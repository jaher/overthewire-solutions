# Vortex L12 — blocked (2026-11-16) → SOLVED (2026-11-18)

Solved 2026-11-18 by the approved last-resort hints (HINTS.md, checked in
as a27bc7a): the single 4-byte GOT write of Hint 2 with the W1 insight of
Hint 3.  See RACE.md for the race verdict and the untraced evidence that
corrected the earlier "blocked by the lab" conclusion.

## The solve (2026-11-18)

- **Payload** (`build12.py`): 1032 'A' filler + `saved ebp ← 0x0804c030`
  (bss scratch) + `popal; cld; ret` @0x0804931d + six filler dwords (all
  0x0804c030 — popal fillers need not be zero, which sidesteps the old
  NUL-blocker) + `ecx = system@libc` (0xf7dc0ce0) + `eax = printf@GOT`
  (0x804c004) + `mov [eax], ecx; ret` @0xf7da9aee (libc+0x3caee) +
  return to safecode's loop head @0x8049260.  NUL-free by construction;
  no stack addresses, so no sweep and no env sensitivity.
- **libc base without gdb:** the parking-loop trick — park main with
  `[ebp-0xc] = sleep@GOT (0x804c00c)`; safecode's own loop prints that
  dword each second: the unresolved stub first, then the resolved
  `base + 0x10b680` = 0xf7e78680 → base **0xf7d6d000** (identical for a
  setuid and a non-setuid exec, verified twice).
- **Delivery:** `drv12.c` reads the payload file and execs the level with
  the raw bytes as argv[1].  The planted executable named `%d\n` (the
  thread's own printf format string, which becomes system()'s argument)
  copies `/etc/vortex_pass/vortex13` to a readable file.
- **The race:** winnable with retries over a no-pty (-T) channel — the
  pty timing breaks the process-wide setresuid broadcast (same lesson as
  L8).  The planted script failed at euid 5012 on the first iterations
  (real shell errors live in the cast) and succeeded on a later one as
  vortex13.  3/3 measured wins in 30s windows; the level is killed by
  timeout so no orphan survives.
- **Verification:** password `6iyARs3cY`, login as vortex13
  (`uid=5013`), `cat /etc/vortex_pass/vortex13` matches.  Recording:
  `recordings/vortex/L12.cast`.

## The program (live binary, verified 2026-11-16)

`/vortex/vortex12`, mode 4750, setuid vortex13, group vortex12, 15220
bytes, md5 `0c8384a61f74ffb2d493bd9a6c634ca6`, not stripped, `GNU_STACK
RW` (no shellcode), partial RELRO (the GOT at 0x0804c000+ writable).
Reconstructed from `objdump`:

```c
void fix_perms(unsigned uid, unsigned gid) {   /* 0x080491e6 */
    syscall(170, uid, uid, uid);   /* 0xaa: setresgid(rgid,egid,sgid)=uid */
    syscall(164, gid, gid, gid);   /* 0xa4: setresuid(ruid,euid,suid)=gid */
}
void *safecode(void *arg) {                    /* 0x08049235 — the THREAD */
    unsigned i = 0;
    geteuid(); getgid();
    fix_perms(geteuid(), getgid());
    for (;;) { printf("%d\n", i++); fflush(stdout); sleep(1); }
}
int unsafecode(char *src) {                    /* 0x08049294 */
    char buf[1032];                /* ebp-0x408 */
    strcpy(buf, src);              /* unbounded overflow */
}
int main(int argc, char **argv) {              /* 0x080492b5 */
    pthread_t tid;
    pthread_create(&tid, 0, safecode, 0);
    getuid(); getgid();
    fix_perms(getuid(), getgid()); /* drops MAIN to r=e=s=5012 */
    unsafecode(argv[1]);           /* the overflow runs AFTER the drop */
    return 0;
}
```

## Why the L8 race does not work here

L8's safecode had no fix_perms: the raw syscalls in main were
per-thread, so the other thread kept euid=vortex9 forever.  L12's
safecode CALLS fix_perms(geteuid(), getgid()) itself — and fix_perms
passes its first arg to setresgid and its SECOND to setresuid, so the
thread runs setresgid(5013,5013,5013) (EPERM: gid 5013 not held) then
**setresuid(5012,5012,5012)** — the thread drops ITSELF to 5012.  The
gdb thread dump confirms: **both threads end at `Uid: 5012 5012 5012
5012`** before the loop starts.  `/etc/vortex_pass/vortex13` is
`-r-------- vortex13:vortex13` — euid 5013 is required, and nothing in
the process holds it after the drops.

## The exploit chain built (all verified piece by piece)

- The overflow: buf[1032] at ebp-0x408; saved ebp at buf+1032, ret at
  buf+1036.  strcpy copies 1440 bytes — the ret slot is reachable, and
  the payload is NUL-free so nothing truncates it.
- Gadgets (all byte-verified in the copied binary and /usr/lib32/
  libc.so.6, libc base 0xf7d6d000 measured via /proc maps):
  `popal; cld; ret` @0x0804931d, `pop ebx; ret` @0x0804901e,
  `inc [ebx-0x366fef3c]; ret` @0x0804922e (builds small integers in
  the zero-initialized .data at 0x0804c028/2c), `mov [eax], ecx; ret`
  @libc+0x3caee (write-what-where), `mov eax,[eax]; ret` @libc+0xe8354
  (deref), `xchg eax,{ebx,ecx,edx}; ret` @libc+0x36297/0x27deb/
  0x362a4, `pop esp; ret` @libc+0x182130, `int 0x80` @libc+0x3b59c.
- sleep@GOT = 0x0804c00c, getgid@GOT = 0x0804c01c,
  geteuid@plt = 0x08049080 — all outside the read-only RELRO.
- Verified working live: the ROP runs after unsafecode's ret; the
  write-what-where landed (an isolated test patching getgid@GOT with
  0xdeadbeef killed the thread the moment its next GOT call fired);
  the deref chain loaded values from the environment; a 4-byte write
  to stdout printed the dumped stack slot.
- The planned chain: W1 = getgid@GOT ← geteuid@plt (the thread's
  getgid() then returns its euid, so fix_perms(euid,euid) no-ops and
  the thread never drops); W2 = the thread's sleep-return slot
  (0xf7d6c33c, gdb-measured) ← `pop esp; ret`; W3 = the sleep-argument
  slot (0xf7d6c340) ← the address of a ROP chain in the payload; main
  then sleeps forever and the thread — still euid 5013 if W1 won the
  race — pivots into open/read/write/exit via int 0x80.

## Why it is blocked

1. **The race is unwinnable in the required window.**  W1 must land
   before the thread's `getgid@plt`, which executes ~1.5 µs after
   pthread_create; main reaches its ROP ~10 µs later (two syscalls in
   fix_perms plus the strcpy).  The thread always wins.  CPU hogs
   (1–24 tried on the lab's 2 cores) either leave the thread's
   scheduling ahead of main's ROP or starve the thread completely.
2. **The sleep-return pivot is self-defeating.**  The thread pushes
   its own return address into the very slot W2 patches on every sleep
   call; whenever the thread's first sleep call happens after main's
   ROP, the thread overwrites both W2 and W3.  Empirically ~20 % of
   runs pivot (and the chain then runs at euid 5012 — EACCES on the
   pass file), the rest loop normally.
3. **mprotect is unavailable** to make the stack executable for a
   full shellcode stage (not in the GOT; ret2dlresolve would need a
   fake Elf32_Rel/Sym whose own addresses are again run-layout
   dependent), and every syscall value small enough to be useful
   (open=5, O_RDONLY=0, read=3, write=4) contains NUL bytes that
   strcpy cannot carry — each workaround (the .data inc-builder,
   environment derefs) was built and verified, but the assembly of the
   whole chain still needs run-layout addresses that move between the
   gdb measurement and a plain run (gdb's `_=/usr/bin/gdb` vs the
   run's `_=/vortex/vortex12` changes the environment block, shifting
   every stack address).
4. Six ROP variants (sleep-then-pivot, ROP re-apply loop, sleep
   -yielding loop, multi-candidate leaks, .data value builders,
   env-independent stack leaks) were built, run, and instrumented with
   strace; each failed on one of the three blockers above.  Strace of
   the stripped copy shows main dying at 0x41414141 (a filler slot
   popped into eip) or the chain's int 0x80 firing with the wrong eax
   when the register-load order desynced — both fixed, but the race
   and the self-overwriting pivot remain.

Fallback per the standing rule: no password obtained, nothing
invented.  The next level's binary is present
(`-r-sr-x--- 1 vortex13 vortex12 /vortex/vortex12`), so the chain can
continue if the block is lifted.
