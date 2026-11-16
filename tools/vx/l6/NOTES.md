# Vortex L6 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex6`, mode 4750, setuid vortex7, group vortex6, 14984 bytes,
md5 `db0119220e93bde3024e6f5d1bf185f0`.  No published source — the level
page says "Generic Binary Exploitation: disassemble it".  Reconstructed
from `objdump` (the binary is not stripped):

```c
void restart(char *arg) {
    setreuid(geteuid(), geteuid());   /* real uid = euid = vortex7 */
    execlp(arg, arg, 0);              /* re-exec arg */
}

int main(int argc, char **argv) {
    if (argv[0] != NULL)              /* 0x80491f0-0x80491f7 */
        restart(argv[0]);             /* note: argv[0], not argv[1] */
    printf(argv[3]);                  /* a format-string bug */
    _exit(0x7325);                    /* the "%s" pushed as the exit code */
}
```

## Measured live

- Running `/vortex/vortex6` with no argument HANGS: `argv[0]` is the binary
  path (non-NULL), so `restart(argv[0])` re-execs the binary itself, whose
  `argv[0]` is the same path again — an **infinite exec loop** (measured:
  no output, the ssh channel blocks even under `timeout 3`; a detached
  `nohup` run produces a 0-byte output file).
- `GNU_STACK` is **RW** (not RWE like vortex4/5) and GNU_RELRO covers
  `0x804bf00..0x804c000` — so the format-string hole (`printf(argv[3])`,
  reachable with an argv[0]-NULL exec) cannot run shellcode on the stack.

## The solution: argv[0] is the program restart() re-execs

`restart` calls `execlp(arg, arg, 0)` where `arg` is **`argv[0]`** of the
current process — not a fixed path.  The setuid binary elevates to
euid=vortex7, and `setreuid(geteuid(), geteuid())` pins the real uid to
vortex7 too, before exec'ing whatever `argv[0]` names:

- `execve("/vortex/vortex6", ["/bin/sh"], env)` — the program to run is the
  setuid binary, but its `argv[0]` is `/bin/sh`.
- main: `argv[0] = "/bin/sh"` ≠ NULL → `restart("/bin/sh")` →
  `setreuid(v7, v7)` → `execlp("/bin/sh", "/bin/sh", 0)`.
- The result: a shell with real uid vortex7.

(A copy of the binary does NOT work: `cp` drops the setuid bit, so the
shell runs as vortex6 — the original path is required.)

## Verification

- The exploit prints `uid=5007(vortex7) gid=5006(vortex6)` and
  `kZ90cmNy9` from `cat /etc/vortex_pass/vortex7`.
- Login as vortex7 with `kZ90cmNy9` verified (`uid=5007`).

## Password for vortex7

`kZ90cmNy9`

## Files

- `ex.py` — the ctypes execve runner (argv[0] = `/bin/sh`, prog =
  `/vortex/vortex6`).
- The recording: `recordings/vortex/L6.cast`.
