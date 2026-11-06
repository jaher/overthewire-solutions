"""Model of the vortex3 walk: p starts at lpp (= 0x804b200 to pass the check).
At each step: t = *p; s = *t; *t = s; p = t  -- no exec, the value is copied.
So p follows the chain t = *p.  The only value on the stack that passes the
check after the store is 0x804b200 itself, so the walk cycles there.

This script searches: for every stack dword the walk could read (the argv
itself and the untouched stack below), is there a combination that makes p
leave 0x804b200..0x804b218 for something with the high word 0x0804?

Run: python3 walk.py
"""
import struct

U = (1 << 32) - 1
SLOT = 0x0804B200


def run(chain, got_page, arg, top):
    """Compute the chain of reads for a given argv (bytes) and stack top."""
    # build a sparse memory: argv bytes + zeros + the GOT page
    mem = dict(got_page)
    base = top - len(arg) - 1
    for i, b in enumerate(arg):
        mem[base + i] = b
    def rd(a):
        return mem.get(a, 0)
    p = SLOT
    seen = []
    for _ in range(64):
        if not (0x08040000 <= p < 0x08050000):
            return {"end": "left", "p": p, "seen": seen}
        if not (0x804b000 <= p < 0x804c000):
            return {"end": "unmapped-image", "p": p, "seen": seen}
        t = rd(p) | rd(p + 1) << 8 | rd(p + 2) << 16 | rd(p + 3) << 24
        seen.append((p, t))
        if t == 0:
            return {"end": "zero", "seen": seen}
        if t & 1:
            return {"end": "odd-target", "t": t, "seen": seen}
        s = rd(t) | rd(t + 1) << 8 | rd(t + 2) << 16 | rd(t + 3) << 24
        mem[t] = s & 0xFF            # the store (one byte, s known odd/even)
        if not (0x08040000 <= t < 0x08050000):
            return {"end": "left-by-target", "t": t, "seen": seen}
        p = t
        if len(seen) > 2 and seen[-1] == seen[0]:
            return {"end": "loop", "seen": seen}
    return {"end": "steps", "seen": seen}


if __name__ == "__main__":
    got = {0x804B200: 0x56, 0x804B201: 0x90, 0x804B202: 0x04, 0x804B203: 0x08}
    top = 0x7ffffffff000
    # baseline: the smallest overflow that reaches lpp
    arg = b"A" * 128 + struct.pack("<I", SLOT)
    print("baseline", run(None, got, arg, top))
    # the argv dwords that sit ABOVE lpp (the walk could read them)
    for off in range(132, 132 + 24):
        a2 = bytearray(b"A" * 128 + struct.pack("<I", SLOT) + b"B" * 40)
        a2[off] = 0xD0
        print(off, run(None, got, bytes(a2), top)["end"])