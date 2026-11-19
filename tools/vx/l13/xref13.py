#!/usr/bin/env python3
# xref13 - scan every e8/e9 branch in .text of /vortex/vortex13 and
# compute its target: find every path to vuln (0x80491d6).
from elftools.elf.elffile import ELFFile
import struct
f = open('/vortex/vortex13', 'rb')
elf = ELFFile(f)
text = elf.get_section_by_name('.text')
code = text.data()
base = text['sh_addr']
hits = []
for i in range(len(code) - 5):
    if code[i] in (0xe8, 0xe9):
        rel = struct.unpack('<i', code[i+1:i+5])[0]
        tgt = base + i + 5 + rel
        kind = 'call' if code[i] == 0xe8 else 'jmp'
        if tgt == 0x80491d6:
            hits.append((base + i, kind))
print("branches to vuln (0x80491d6):")
for a, k in hits:
    print("  0x%08x %s" % (a, k))
# the init_array entry
ia = elf.get_section_by_name('.init_array')
val = struct.unpack('<I', ia.data())[0]
print(".init_array entry: 0x%08x" % val)
for sym in elf.get_section_by_name('.symtab').iter_symbols():
    if sym['st_value'] == val:
        print("  = %s" % sym.name)
