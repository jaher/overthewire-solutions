# Vortex L10 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex10`, mode 4550, setuid vortex11, group vortex10, 15352
bytes, md5 `49dcf2fee434ab1eb8f0b5bdc4104729`.  Reconstructed from
`objdump` (the binary is not stripped; `GNU_STACK RW` — no shellcode):

```c
int main(void) {
    struct tms t;
    unsigned base = times(&t) + t.tms_utime + t.tms_stime
                  + t.tms_cutime + t.tms_cstime + clock() + time(0);
    int N = 128 - (base % 256);        /* a SIGNED mod: can be <= 0 */
    unsigned seed = N + time(0);       /* the srand argument */
    srand(seed);
    setvbuf(stdout, 0, _IONBF, 0);
    for (int i = 0; i < N; i++) rand();        /* N skipped draws */
    putchar('[');
    unsigned arr[20];
    for (int i = 0; i <= 19; i++) { arr[i] = rand(); printf(" %08x,", arr[i]); }
    puts("]");
    alarm(30);
    unsigned target;
    read(0, &target, 4);
    if (target == seed) {              /* must echo the exact seed */
        setresuid(geteuid(), geteuid(), geteuid());
        execlp("/bin/sh", "sh", "-i", 0);
    } else
        puts("Nope, try again");
}
```

## Measured live

- The gate: the 4 bytes read from stdin must equal the exact `srand()`
  seed (`N + time(0)`).  The seed is never printed, but the 20-value
  `rand()` window is — and glibc's `rand()` is deterministic given the
  seed.
- The loop count `N` is a signed mod (`sar $0x1f / shr $0x18 / movzbl /
  sub` idiom): `128 - (base % 256)` can be negative, in which case zero
  draws are skipped and the window starts at draw #1.  The
  `times()/clock()` jitter shifts `base`, so observed skips ranged up
  to ~366.
- The two `time()` calls differ by the loop's runtime: `seed - now` can
  be a few hundred seconds.
- Emulating glibc's TYPE_3 rand in python failed for this build (my
  warmup/output indexing was off — the standard model reproduced seed 1
  but not seed 12345), so the cracker uses the target's own libc: a C
  program that calls `srand(candidate)`, skips `s` draws, and compares
  the next 20 against the printed array.  Candidates: seed `time ±600
  s`, skip `0..500`.  A 20-value match is ~2^-160: the found
  `(seed, skip)` is exact.  Runtime: ~0.7 s.
- The answer is `read(0, &target, 4)`: the seed as 4 raw little-endian
  bytes.  On a match the level `setresuid`s to euid and spawns
  `execlp("/bin/sh", "sh", "-i", 0)`.

## Verification

- The cracker: `FOUND seed=1794839484 skip=366` (live).
- The spawned shell: `uid=5011(vortex11)`, `xb4DVZ2av` from
  `/etc/vortex_pass/vortex11`.
- Login as vortex11 with `xb4DVZ2av` verified (`uid=5011`).

## Password for vortex11

`xb4DVZ2av`

## Files

- `cracke.c` — the libc-based seed cracker (compiled to `cracke`):
  `cracke <20 hex values>`.
- `solve10.py` — run the level, parse the window, crack, answer, verify
  the spawned shell.
- The recording: `recordings/vortex/L10.cast`.
