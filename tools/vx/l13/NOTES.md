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
