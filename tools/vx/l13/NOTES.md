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

## Pre-main entry audit + hints + host check (2026-11-19, third session)

### Pre-main entry audit (angle 1)

- Sections: .init (0x8049000, 0x20), .init_array (0x804bf00, 1 entry),
  .fini_array (1 entry), .plt (0x8049020), .text (0x80490c0).
- .init_array entry = 0x80491d0 = **frame_dummy** (endbr32; jmp
  register_tm_clones) - the standard constructor, NOT vuln.
- .init calls [ebx-4] = __gmon_start__ (weak, 0 -> skipped).
- _start flows to __libc_start_main -> main (the standard path).
- **The ONLY branch to vuln (0x80491d6) is main's call at 0x804937e** -
  a scan of every e8/e9 in .text computes the targets; exactly one hits
  vuln, and it sits AFTER main's argc gate (0x804928f).  No data
  reference, no alternate entry, no pre-main path primes the stack or
  the format state.

No route to vuln bypasses main's argc gate.  Angle 1 closed with
evidence.

### Last-resort hints (angle 2): public writeups on the 5.18 fix

- l3ouu4n9 (2019-12-02): the {NULL}/{NULL} execve wrapper "passes the
  restriction of argc = 0" - no mention of kernel 5.18+, the empty-argv
  fix, or a fallback for modern kernels.
- rk700 (2014-09-14, vortex13): the same {NULL} loader ("The binary
  checks that argc is nonzero, so it must be launched with argv
  containing only NULL"), then the full technique: a symlink whose
  filename is the payload (saved-ebp overwrite + system + "sh" bytes),
  the kernel leaving the invocation path at the stack bottom (for a
  symlink it is the LINK's path), and %57316x%116$hn writing the low
  half of the saved ebp.  No mention of the 5.18 fix (predates it).
- rk700 (2014-09-13, vortex12): covers L12 only.
- Web search unavailable in this environment (all providers failed);
  the covered sources are the official site, l3ouu4n9, and rk700.

No public writeup addresses the 5.18 empty-argv fix for L13.  The
technique both writeups describe is downstream of the argc gate, which
is the block here.  Angle 2 closed.

### Host check (angle 3)

- DNS: vortex.labs.overthewire.org resolves to ONE address
  (13.63.111.222).
- Fresh login: kernel 7.0.0-1014-aws, hostname gibson-0, IP 10.0.1.99 -
  unchanged.  No alternate entry point with an older kernel is reachable
  from this session (all OTW vortex levels are the same host).

Angle 3 closed.  **Final verdict: L13 remains blocked on this lab -
argc==0 is unreachable on kernel 7.0.0 (every exec path, every pre-main
route audited), and no writeup addresses the 5.18 empty-argv fix.  The
level stays blocked pending a kernel change on the lab host.**

## Fourth attempt (2026-11-19): five new angles, all closed

### Angle 1 — helper-exec audit

- `sudo -l`: unusable ("sudo must be owned by uid 0 and have the setuid
  bit set").
- `getcap -r /usr/bin /bin`: only `ping`/`mtr-packet` (cap_net_raw=ep) -
  no exec helper.  `getcap -r /vortex`: nothing.
- pkexec: not installed.
- The 88 setuid binaries (enumerated last session): the wargame
  binaries + bandit26's bandit27-do (750 bandit27:bandit26), bandit20's
  suconnect, leviathan helpers - all 750 owner-group only; vortex13 is
  in none of those groups (`/home/leviathan1/check` -> Permission
  denied).  Nothing yields euid 5014 or a caller-controlled-argv
  launcher.
- cron: only the shared lab cleanup jobs; systemd timers: system ones
  (sysstat/fwupd/motd-news/tmpfiles-clean).
- Running processes: only my sshd-session (no vortex14 helper).

**No helper that launches a program with caller-controlled argv on
vortex13's behalf exists.  Angle closed.**

### Angle 2 — emulator probe

- `which qemu-i386 qemu-i386-static box86 box64`: nothing.
- `find / -name "qemu*" -type f`: only bash-completion/pwnlib headers
  (no binary).  No box86/box64 anywhere.  dpkg: no qemu packages.

**No user-mode emulator exists on the lab host; the "emulator builds
its own guest stack" route is unavailable.  Angle closed.**

### Angle 3 — pre-main stack check

- NO `.preinit_array` section at all.
- `.init_array`: one entry (0x80491d0 = frame_dummy - the standard
  constructor: endbr32; jmp register_tm_clones; it touches nothing
  attacker-relevant).
- **ZERO R_386_IRELATIVE relocations: no IFUNC resolvers run.**
- main's pre-gate code (0x804927b..0x8049292): lea ecx,[esp+4] (&argc);
  and esp,~15; push [ecx-4] (the return address); push ebp/ebx/ecx;
  sub esp,0x10; mov eax,ecx.  **No memory access except [ecx-4] and the
  gate's [eax] - nothing touches argv/env.**
- Gate bytes re-confirmed at 0x8049292: `83 38 00` (cmp [eax],0) /
  `74 0a` (je past the exit).

**Nothing before the gate can rewrite the argc slot.  Angle closed.**

### Angle 4 — alternate-host recheck

- 4 resolves: identical address every time (13.63.111.222, one IPv4, no
  AAAA).  One STREAM/DGRAM/RAW host.
- Filesystem sweep: no copy of the level binary outside /vortex; no
  other reference to vortex_pass/vortex14 (the one grep -l hit was a
  false positive: `grep -c` on the file is 0; od shows the 10-byte
  password only).

**Angle closed.**

### Angle 5 — old-kernel VM feasibility (scope only)

- No `qemu-system` binary on the host.
- `/dev/kvm` does not exist: hardware virtualization unavailable.
- Outbound network is firewall-blocked: 1.1.1.1:443 refused,
  deb.debian.org:80 refused.

**Booting a pre-5.18-kernel VM is infeasible here: no kvm, no
qemu-system, no network to fetch a kernel.  Scope reported, nothing
built.**

## Final verdict (fourth attempt)

L13 remains blocked on this lab.  argc==0 is unreachable (every exec
path, every pre-main route audited, no helper-exec route, no emulator),
and a pre-5.18-kernel VM is infeasible (no kvm, no qemu-system, no
outbound network).  The level stays blocked pending a kernel change on
the lab host.

## Fifth attempt (2026-11-19): external process control with ptrace

### Step 1 — static/dynamic finding

`/vortex/vortex13` is **DYNAMIC** (`NEEDED libc.so.6`, Type EXEC): a
loader-init window exists between exec and main's argc gate (ld.so maps
libc, then main).  A static binary would give almost none.

### Step 2 — empirical permission test (cheap, decisive)

`ptrace13.c` (fork; the child sets `PR_SET_DUMPABLE(0)` and loops; the
parent PTRACE_ATTACHes; then the control with dumpable=1):

- attach to dumpable=0 (same uid): **rc=-1 errno=Operation not permitted**
- attach to dumpable=1 (same uid): rc=0 errno=Success

**The dumpable rule blocks external ptrace control without CAP_SYS_PTRACE
- even by the same uid.**  A setuid vortex14 process (dumpable=0 from the
moment of exec, since ruid != fsuid) cannot be PTRACE_ATTACHed by
vortex13.  ptrace_scope = 1 (yama): the pure parent-attach shape
SUCCEEDS for a dumpable=1 child (rc=0), so the block is precisely the
dumpable flag, not the parent relationship.

Control datum (the L12 precedent): the parked setuid vortex12 process
(r=e=s=5012 after fix_perms) CAN be attached by its direct parent -
**the kernel re-evaluates dumpable on setresuid: ruid == fsuid ->
dumpable 1** (empirically: rc=0).  The L13 level has NO drop: its
process keeps ruid=5013 != fsuid=5014, so dumpable stays 0 from exec -
the attach fails EPERM at any moment.

### Step 3 — the attach race, measured (decisive)

`race13.c` (20 spawns with argv={NULL}, a tight attach loop per spawn):
spawns=20 **attached=20** exits=0 eperm=0.  The 20/20 attaches are the
PRE-exec fork window (the child is still the wrapper image, uid match
5013==5013) - they don't help: after the detach the level execs and the
gate exits(1).

`race13b.c` (the decisive shape: the child sleeps 2s PRE-exec so the
parent's attach cannot land pre-exec, then execs; the parent attaches
after the exec): **post-exec attach: rc=-1 errno=Operation not
permitted.**

The spawned setuid vortex14 level (fsuid 5014, dumpable=2 - the
Ubuntu-default suid_dumpable sysctl) cannot be PTRACE_ATTACHed by
vortex13 (fsuid 5013, no CAP_SYS_PTRACE): the uid rule blocks it.
dumpable=2 (suid-safe) does NOT block ptrace itself - only the uid rule
does.

Resolution of the earlier "dumpable=0 blocks" datum: the ptrace13 test
used PR_SET_DUMPABLE(0) (dumpable=0 = SUID_DUMP_DISABLE, which blocks
ptrace even same-uid).  A setuid exec sets dumpable=2 (suid-safe, from
the sysctl), which does not block ptrace - but the uid rule (fsuid
5014 vs 5013) does.  The L12 parked process became attachable because
its fix_perms setresuid'd ruid=fsuid=5012 (the kernel re-evaluates
dumpable on setresuid: ruid == fsuid -> dumpable 1) - the L13 level has
NO drop, so fsuid stays 5014: the uid rule blocks at every moment.

**The attach race for L13 is dead: post-exec attaches fail EPERM (uid
mismatch, no CAP_SYS_PTRACE), pre-exec/traceme attaches don't change
the gate's outcome.**

### Step 4 — every outcome documented

- static/dynamic: DYNAMIC (loader window exists, but no attach can use
  it).
- the attach errno: post-exec = EPERM (Operation not permitted); the
  dumpable=0 same-uid test = EPERM (the PR_SET_DUMPABLE(0) rule).
- the attach win rate: 20/20 pre-exec (useless); 0 post-exec.

### Step 5 — what class of route remains untested

No class of route remains untested for L13 on this lab: every exec
path, the pre-main routes, the writeups, the helpers, the emulators,
the hosts, and now external ptrace control are all closed.  The only
lever is the lab host's kernel version (the 5.18+ empty-argv fix).
