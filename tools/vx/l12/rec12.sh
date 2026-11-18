#!/bin/bash
# rec12 - record the full L12 solve: the exploit session as vortex12
# (discovery, vim writing) over -tt; the exploit run transported over -T
# (the pty timing breaks the process-wide setresuid race, like L8);
# then the verification session as vortex13.
cd /workspace/tools/vx/l12
python3 /home/claude/tools/ptyrun.py vortex.labs.overthewire.org 2228 vortex12 YufVIb8Mo l12.cmds 100x32
echo
echo "=== the exploit run, transported over -T (the pty timing breaks the setresuid race) ==="
bash /workspace/tools/vx/l12/fireT.sh
echo
echo "=== second session: login as vortex13 ==="
python3 /home/claude/tools/ptyrun.py vortex.labs.overthewire.org 2228 vortex13 6iyARs3cY l13.cmds 100x32
