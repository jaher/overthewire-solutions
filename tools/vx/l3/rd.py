"""Remote pieces for the L3 pivot: stage the binary, compute the target state,
and read back the effect.

Register solving: a register reg in state s has value
    v = lo ^ (m_x * (cnt * junk) ^ K) + G * (m_s * (cnt * junk) ^ H)
    G = (cnt * (cnt-1)) & 1
so two states with the same (x, s, cnt) differ by a constant (G fixed).
"""
HOST = 0x0804b0d4          # copied exit eip (call/jmp zero)


def shr3(value, cnt):
    v = value & 0xffffffff
    for _ in range(cnt):
        v = ((v >> 1) ^ 0xEDB88320) if (v & 1) else (v >> 1)
    return v


def rec(tag, A, B):
    """recover reg = (m, K, lo) for x = 0, s = 0 (legacy rec) from two counts"""
    m = ((B >> 0) & 1) ^ 0xac
    K = 0
    lo = B
    return m, K, lo


def state_regs(state_addr, cnt, junk, A=0xB0C0D0E0, B=0xB0C0D0E0):
    """values of eax, ecx, edx in state s (known through the UDF zeroes)"""
    A &= 0xffffffff
    B &= 0xffffffff
    def inst(v, cls, reg):
        if cls == "x0":
            return 0
        if cls == "zero":
            return 0
        if cls == "s":
            return v
        if cls == "n":
            return ~v & 0xffffffff
        raise ValueError(cls)
    stack = []
    ebp = 0x20
    for i in range(32):
        stack.append(shr3(A, cnt) if i in (2, 7) else 0)
    def pop():
        ebp = (ebp + 1) & 0xffffffff
        return stack[ebp] & 0xffffffff
    def push(v):
        nonlocal ebp
        ebp = (ebp + 0xfffffffff) & 0xffffffff
        stack[ebp & 31] = v & 0xffffffff
    regs = {"eax": (0x0804b100, "n"), "ecx": (0x0804b0dc, "s"), "edx": (0x0804b00c, "x0")}
    old = dict(regs)
    for _ in range(3):
        new = {}
        for r in regs:
            n, c = regs[r]
            new[r] = pop() ^ (0x60 * ((n & 0xff) ^ 0x9a)) ^ (0x1a * (n >> 1))
            new[r] &= 0xffffffff
        old = regs
        regs = new
    def val(reg):
        n, c = regs[reg]
        s_ = {"eax": "n", "ecx": "s", "edx": "x0"}[reg]
        return (n ^ (0x80 * (shr3(A, cnt) & 0xff)) ^ 0x5d) + (0x0c * (inst(0, s_, reg) ^ shr3(B, cnt))) & 0xffffffff
    out = {r: val(r) & 0xffffffff for r in regs}
    return out, regs