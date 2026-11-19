# Vortex L13 — blocked by the kernel's empty-argv fix (2026-11-19)

## The program (live binary, md5 5c9efbdf32e1d3473cb75511ccbf8fbd)

`/vortex/vortex13`, mode 4750, setuid vortex14, group vortex13, 15200
bytes, not stripped, `GNU_STACK RW` (NX stack), partial RELRO.
Reconstructed from objdump (capstone, offsets re-derived live):

```c
void vuln(void) {                    /* 0x80491d6 */
    unsigned n = 20;
    char *buf = malloc(n);
    if (!fgets(buf, n, stdin)) exit(1);   /* stdin copy at .bss 0x804c060 */
    for (i = 0; i < 20; i++)
        if (!strchr(ALLOW, (signed char)buf[i])) exit(1);
    printf(buf);                     /* format string, allowlisted */
    free(buf);
}
int main(...) {                      /* 0x804927b */
    if (argc != 0) exit(1);          /* cmp [argc],0; je skip-exit */
    /* zero every envp string byte via the .bss array at 0x804c040,
       then every argv string byte via the ecx-thunk's [eax+4] */
    setreuid(geteuid(), geteuid());
    vuln();
}
```

ALLOW (rodata 0x0804a008) =
`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%.$\n`.

## The published technique (l3ouu4n9, re-derived)

- An execve with NULL argv/envp gives argc==0 (on pre-5.18 kernels), so
  main's argc gate passes and the zeroing loops see no strings.
- The kernel puts the exec path's basename at the bottom of the stack
  (AT_EXECFN); main's zeroing never touches it.  A symlink whose
  basename holds the payload bytes plants attacker bytes on the stack.
- The fmt write (`%57316x%112$hn` in the writeup) repoints a stack slot
  into the crafted name; vuln's leave/ret pivots into it; the crafted
  bytes hold system@libc and "sh" - a shell.

## Why it is blocked here (untraced evidence, 2026-11-19)

- Kernel 7.0.0-1014-aws (>= 5.18): the kernel forces a single empty
  string for an empty argv ("exec: Force single empty string when argv
  is empty"), so **argc==0 is unreachable**: printargc via execve with
  argv={NULL} and argv={NULL,NULL} both report argc=1; argv=NULL
  (glibc-normalized) also argc=1.
- The real binary under an empty-argv exec: execve("/vortex/vortex13",
  [], []) -> **exit_group(1) with no read(0) at all** (strace, untraced):
  main's argc gate exits before vuln().
- The AT_EXECFN angle is downstream of the gate: vuln never runs, so no
  fmt write, no pivot, no shell.

Outcome: the level's argc==0 premise does not exist on this kernel.
Blocked with untraced evidence.  Files: probe13.c (the execve probe),
printargc.c (the argc printer), argcprobe.c (the self-re-exec probe),
vortex13 (the live binary copy, md5 above).

## Exhaustive re-check (2026-11-19): both remaining angles closed

### Angle 1 — every exec path for argc==0 (exec13.c, all straced)

A 32-bit raw-syscall launcher tried execve (argv=NULL), execven
(argv={NULL}), execven1 (argv={NULL,NULL}), execveat (dirfd+empty),
fexecve (execveat with AT_EMPTY_PATH on an open fd) and posix_spawn
(argv={NULL}) against the live /vortex/vortex13, each straced:

- All six: the level execs with NULL/empty argv and **exits 1 with zero
  stdin reads** (0 read(0)/read(3...AAAA) in every trace): main's argc
  gate exits before vuln() on every path.
- Fresh `uname -r` on a new login: 7.0.0-1014-aws (#14-Ubuntu SMP PREEMPT
  Thu Sep 17 19:08:36 UTC 2026 x86_64) — unchanged; the 5.18+ empty-argv
  fix applies to every path.

argc==0 is unreachable on this host.  Angle 1 is closed with evidence.

### Angle 2 — host enumeration for an alternate route to vortex14

As vortex13 (uid=5013, groups=5013 only):

- `ls -la /vortex/`: vortex13 (the level, 4750 vortex14:vortex13),
  **vortex14.txt is -r-------- vortex14:vortex14, 323 bytes** (mode 400:
  only euid vortex14 can read; `cat` -> Permission denied), vortex15
  (r-x group vortex15 — not our group), vortex15.tar.Z.enc (400
  vortex15).  No world-readable vortex14 artifact.
- `find / -perm -4000 -o -perm -2000`: the wargame binaries, bandit26's
  bandit27-do, leviathan helpers, krypton encrypt tools — nothing
  vortex14-related, nothing that yields euid 5014.
- `grep -r "vortex14" /etc /home /opt /srv /usr/local`: nothing
  world-readable.
- `/var/mail/`: only vortex9's mailbox (the L9 precedent); no
  /var/mail/vortex13 or vortex14.
- cron: only the shared lab cleanup jobs (/etc/cron.d/clean_tmp,
  behemoth4_cleanup, bandit cronjobs); crontab -l unreadable (root
  spool).  No systemd unit touching vortex14.
- `sudo`: not usable ("sudo must be owned by uid 0 and have the setuid
  bit set").
- Group hop: setgid(5014) and setreuid(5014) both EPERM from uid 5013
  (the L9 precedent holds: the vortexN groups have no members).

Angle 2 is closed: no alternate route to the vortex14 password exists
from vortex13 on this host.

## Final verdict (2026-11-19)

L13 is blocked by the kernel's empty-argv normalization (7.0.0, >= 5.18)
on every exec path, and no alternate route to /etc/vortex_pass/vortex14
exists from vortex13.  The level's argc==0 premise is structurally dead
on this lab.  Both angles documented with untraced evidence.
