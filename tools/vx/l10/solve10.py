import subprocess, re, time, struct, sys

# run the level, capture the 20-value rand() array it prints
p = subprocess.Popen(["/vortex/vortex10"], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE)
line = p.stdout.readline().decode()
arr = re.findall(r"[0-9a-f]{8}", line)
print("array:", " ".join(arr[:5]), "...", flush=True)

# crack the srand() seed with the C cracker (the target's own libc rand)
args = ["./cracke"] + arr
r = subprocess.run(args, capture_output=True, text=True, timeout=180)
print("cracker:", r.stdout.strip(), flush=True)
m = re.search(r"seed=(-?\d+)", r.stdout)
if not m:
    print("NO SEED", flush=True)
    sys.exit(1)
seed = int(m.group(1))

# the answer is read(0, &target, 4): send the seed as 4 raw bytes
p.stdin.write(struct.pack("<i", seed))
p.stdin.flush()
# the shell spawns: feed the verification commands
time.sleep(1)
p.stdin.write(b"id; cat /etc/vortex_pass/vortex11; exit\n")
p.stdin.flush()
out = p.stdout.read(400)
print("response:", out.decode('latin-1')[:200], flush=True)
