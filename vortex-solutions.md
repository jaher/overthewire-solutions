## Level 13 → vortex14 (BLOCKED 2026-11-19)
- **No password obtained.**  The level's gate is `if (argc != 0) exit(1)` — main's FIRST check (`cmp [argc],0; je skip-exit`, bytes `83 38 00`/`74 0a` at 0x8049292).  The published technique needs argc==0, which is unreachable on this kernel.
- **The program (verified against the live binary, md5 `5c9efbdf32e1d3473cb75511ccbf8fbd`):** `/vortex/vortex13`, mode 4750, setuid vortex14, group vortex13, 15200 bytes, not stripped, `GNU_STACK RW` (NX), partial RELRO:
  ```c
  void vuln(void) {                    /* 0x80491d6 */
      unsigned n = 20;
      char *buf = malloc(n);
      if (!fgets(buf, n, stdin)) exit(1);
      for (i = 0; i < 20; i++)
          if (!strchr(ALLOW, (signed char)buf[i])) exit(1);
      printf(buf);                     /* format string, allowlisted */
      free(buf);
  }
  int main(...) {                      /* 0x804927b */
      if (argc != 0) exit(1);          /* the gate */
      /* zero every envp string byte (.bss array 0x804c040), then every
         argv string byte (the ecx-thunk's [eax+4]) */
      setreuid(geteuid(), geteuid());
      vuln();
  }
  ```
  ALLOW (rodata 0x0804a008) = `ABC..xyz0123456789%.$\n`; the strchr check covers 20 bytes of the fgets buffer including the NUL (`strchr(s,0)` returns non-NULL, so NUL passes).
- **The published technique (l3ouu4n9, re-derived):** execve with NULL argv/envp gives argc==0 on pre-5.18 kernels, so the gate passes and the zeroing loops see no strings; the kernel's separate AT_EXECFN basename copy (a symlink with a crafted name) plants attacker bytes at the stack bottom; a fmt write (`%57316x%112$hn` in the writeup) repoints a stack slot into the crafted name and vuln's leave/ret pivots into system@libc("sh").
- **Why it is blocked here (untraced evidence, 2026-11-19):** the lab's kernel 7.0.0-1014-aws (>= 5.18) forces a single empty string for an empty argv ("exec: Force single empty string when argv is empty"), so argc==0 is unreachable: printargc via execve with argv={NULL} and argv={NULL,NULL} both report argc=1; argv=NULL (glibc-normalized) also argc=1.  The real binary under an empty-argv exec: `execve("/vortex/vortex13", [], [])` → exit_group(1) with NO read(0) at all (strace, untraced) — main's argc gate exits before vuln().  The AT_EXECFN angle is downstream of the gate: vuln never runs, so no fmt write, no pivot, no shell.
- **Files:** `tools/vx/l13/` (`probe13.c` execve probe, `printargc.c` argc printer, `argcprobe.c` self-re-exec probe, `NOTES.md` the verdict).
- **Exhaustive re-check (2026-11-19): both remaining angles closed.**  (1) A 32-bit raw-syscall launcher (`tools/vx/l13/exec13.c`) tried execve (argv=NULL), execven ({NULL}), execven1 ({NULL,NULL}), execveat (dirfd+empty), fexecve (execveat with AT_EMPTY_PATH) and posix_spawn ({NULL}) against the live binary — all six exec the level with NULL/empty argv and it **exits 1 with zero stdin reads** (straced per mode: 0 read(0) in every trace); a fresh `uname -r` on a new login confirms 7.0.0-1014-aws.  argc==0 is unreachable on this host.  (2) Host enumeration as vortex13: `/vortex/vortex14.txt` is mode 400 vortex14-owned (unreadable); the setuid/setgid sweep finds nothing vortex14-related; no world-readable vortex14 artifact; `/var/mail/` holds only vortex9's box (the L9 precedent, no vortex13/14 mail); cron holds only the shared lab cleanup jobs; sudo is unusable; setgid(5014)/setreuid(5014) both EPERM (the vortexN groups have no members).  **No alternate route to the vortex14 password exists from vortex13.**  L13 stays blocked pending a kernel change on the lab host.
- **Pre-main entry audit (third session, 2026-11-19): no route to vuln bypasses the argc gate.**  `.init_array` entry = 0x80491d0 = **frame_dummy** (endbr32; jmp register_tm_clones) — the standard constructor, not vuln; `.init` calls `__gmon_start__` (weak, 0 → skipped); `_start` flows to `__libc_start_main` → main.  A scan of **every e8/e9 branch in .text** computes its target: exactly one hits vuln (0x80491d6) — main's call at 0x804937e, which sits **after** the argc gate at 0x804928f.  No data reference, no alternate entry, nothing primes the stack or the format state before the gate.
- **Writeup hints: no public writeup addresses the 5.18 empty-argv fix.**  l3ouu4n9 (2019-12-02) and rk700 (2014-09-14, vortex13) both rely on the `{NULL}` execve wrapper giving argc=0 and predate the 5.18 fix.  rk700's vortex13 technique is fully documented (the symlink whose filename is the payload: saved-ebp overwrite + `system` + `"sh"` bytes; the kernel leaving the **link's** path at the stack bottom; `%57316x%116$hn` writing the saved ebp's low half) — all downstream of the argc gate.  Web search unavailable in this environment; the covered sources are the official site, l3ouu4n9, and rk700.
- **Host check: one host, one kernel.**  `vortex.labs.overthewire.org` resolves to ONE address (13.63.111.222); a fresh login confirms kernel 7.0.0-1014-aws, hostname gibson-0.  No alternate entry point with an older kernel.
- **Final verdict: L13 remains blocked on this lab** — argc==0 is unreachable (every exec path, every pre-main route audited), no writeup addresses the 5.18 empty-argv fix, and the level stays blocked pending a kernel change on the lab host.
- **Fourth attempt (2026-11-19): five new angles, all closed.**  (1) **Helper-exec audit**: sudo unusable; `getcap` shows only `ping`/`mtr-packet` (cap_net_raw, no exec helper); pkexec not installed; the 88 setuid binaries are the wargame ones + other games' 750-owner-group-only helpers (`/home/leviathan1/check` → Permission denied from vortex13); cron holds only the shared cleanup jobs; systemd timers are system ones; no vortex14 processes.  No caller-controlled-argv launcher exists.  (2) **Emulator probe**: no qemu-i386/box86/box64 binary on the host (find shows only bash-completion/pwnlib headers) — the "emulator builds its own guest stack" route is unavailable.  (3) **Pre-main stack check**: NO `.preinit_array` section; `.init_array` = one entry (frame_dummy, the standard constructor, touches nothing attacker-relevant); **zero R_386_IRELATIVE relocations** (no IFUNC resolvers); main's pre-gate code touches no argv/env memory (`[ecx-4]` return address and the gate's `[eax]` only); gate bytes re-confirmed (`83 38 00`/`74 0a` at 0x8049292).  Nothing before the gate can rewrite the argc slot.  (4) **Alternate-host recheck**: 4 resolves identical (13.63.111.222, one IPv4, no AAAA); no copy of the level binary outside /vortex; no other vortex14 reference (the one grep -l hit was a false positive, `grep -c` 0).  (5) **Old-kernel VM feasibility (scope only)**: no qemu-system binary, `/dev/kvm` does not exist, outbound network firewall-blocked (1.1.1.1:443 and deb.debian.org:80 refused) — booting a pre-5.18 kernel is infeasible here.  **L13 stays blocked pending a kernel change on the lab host.**
- **Fifth attempt (2026-11-19): external process control with ptrace — the attach race is dead.**  The level is DYNAMIC (`NEEDED libc.so.6`): a loader window exists between exec and the gate.  Empirical permission test (`ptrace13.c`): attach to dumpable=0 (same uid) → **EPERM** (the `PR_SET_DUMPABLE(0)` rule blocks ptrace even same-uid); attach to dumpable=1 → Success; ptrace_scope=1 (yama): the parent-attach shape succeeds for a dumpable=1 child, so the block is the dumpable/uid flag, not the parent relationship.  Control datum: the parked setuid vortex12 process (r=e=s=5012 after fix_perms) IS attachable by its direct parent — **the kernel re-evaluates dumpable on setresuid: ruid==fsuid → dumpable 1**.  The L13 level has NO drop: fsuid stays 5014.  The attach race measured: `race13.c` 20 spawns: 20/20 attaches — **all pre-exec** (the fork window, uid match, useless); `race13b.c` the decisive shape (the child sleeps 2s pre-exec, the parent attaches after the exec): **post-exec attach → EPERM** — the spawned setuid vortex14 level (fsuid 5014, dumpable=2 from the suid_dumpable sysctl, which does NOT block ptrace itself) cannot be attached by vortex13 (fsuid 5013, no CAP_SYS_PTRACE): the uid rule blocks it at every moment.  PTRACE_TRACEME pre-exec: the kernel ignores setuid-on-exec when traced (the L12 finding) and argc is still 1: the gate exits anyway.  **No class of route remains untested on this lab; the only lever is the lab host's kernel version.**
- **Sixth attempt — close-out (2026-11-22): four final route classes closed.**  (1) **Cron**: `clean_tmp` runs as root but only deletes; `behemoth4_cleanup` and the crontab are 440 root:root (unreadable); the bandit cronjobs run as **bandit22/23/24** with 750-banditN-group scripts (unreadable) — no cronjob runs as vortex14, so a vector would reach a bandit at best.  (2) **Trusted library dirs**: `/etc/ld.so.preload` does not exist; every trusted dir (the multiarch dirs, `/usr/local/lib`, the libfakeroot dir, /lib32, /lib, /usr/lib) is read-only (`touch` → Permission denied) — the whole pre-main code-injection family (LD_PRELOAD with a bare soname, a planted .so in a trusted dir) is dead by filesystem.  (3) **process_vm_readv/writev and /proc/<pid>/mem**: on the parked setuid vortex12 child (fix_perms'd, ruid==fsuid, dumpable re-evaluated to 1) **all four succeed** — the direct-parent + dumpable=1 posture IS writable; on the REAL L13 posture (setuid vortex14, fsuid 5014, ruid 5013, dumpable=2, no setresuid drop) **spawns=20 writes-ok=0 eperm=20** — the uid rule blocks the parent at every moment (the L12 child succeeded only because fix_perms made ruid==fsuid).  (4) **Userland-exec family closed by reasoning**: a hand-built ELF loader or a qemu-user guest that builds an argc==0 stack itself **skips the kernel exec** — the setuid bit never applies, the loader runs as vortex13 (fsuid 5013), and any shell is vortex13 which cannot read the mode-400 `/etc/vortex_pass/vortex14`; closed by the setuid-loss point, not merely by the emulator binary's absence.
- **FINAL VERDICT: every route class is closed; L13 is completely stuck pending a lab-host kernel change (the 5.18+ empty-argv fix); no route remains.**


## Level 12 → vortex13 (SOLVED 2026-11-18)
- **Password for vortex13:** `6iyARs3cY`, dropped by the planted script to a readable file and verified by logging in as vortex13 (`uid=5013`, `cat /etc/vortex_pass/vortex13` matches).  Recording: `recordings/vortex/L12.cast`.
- **The program (verified against the live binary, md5 `0c8384a61f74ffb2d493bd9a6c634ca6`):** `/vortex/vortex12`, mode 4750, setuid vortex13, group vortex12, 15220 bytes, not stripped, `GNU_STACK RW` (no shellcode), partial RELRO (the GOT at 0x804c000+ writable):
  ```c
  void fix_perms(unsigned uid, unsigned gid) {  /* 0x080491e6 */
      syscall(170, uid, uid, uid);   /* setresgid(rgid,egid,sgid) = uid */
      syscall(164, gid, gid, gid);   /* setresuid(ruid,euid,suid) = gid */
  }
  void *safecode(void *arg) {                   /* 0x08049235 — the THREAD */
      unsigned i = 0;
      geteuid(); getgid();
      fix_perms(geteuid(), getgid());
      for (;;) { printf("%d\n", i++); fflush(stdout); sleep(1); }
  }
  int unsafecode(char *src) {                   /* 0x08049294 */
      char buf[1032];
      strcpy(buf, src);              /* unbounded overflow */
  }
  int main(int argc, char **argv) {
      pthread_t tid;
      pthread_create(&tid, 0, safecode, 0);
      getuid(); getgid();
      fix_perms(getuid(), getgid()); /* drops MAIN to r=e=s=5012 */
      unsafecode(argv[1]);           /* the overflow runs AFTER the drop */
  }
  ```
- **Why the earlier attempts dead-ended, and what the hints fixed:** the 2026-11-16/17 sessions built a complex W1/W2/W3 thread-pivot chain and hit three blockers.  The approved last-resort hints (checked in as a27bc7a) corrected two things: (1) the gdb finding "Uid 5012 at _start" was the **ptrace/setuid artifact** — the kernel ignores setuid on exec when the execing thread is traced, so it proved nothing about the lab; untraced task-level polling caught the exec-time state `Uid: 5013 5013 5013 5013` in 3/3 runs.  (2) The intended solution is the **single 4-byte GOT write**, not a thread ROP.
- **The exploit (the hints' synthesis, all addresses re-derived from the live binary):** the overflow reaches the ret slot at buf+1036.  One ROP does everything with fixed, env-independent addresses (no stack addresses — no sweep needed):
  - `saved ebp ← 0x0804c030` (bss scratch, readable+writable),
  - `popal; cld; ret` @0x0804931d loads the registers from the payload (the six unused slots point at 0x0804c030 — **this sidesteps the "NUL bytes strcpy cannot carry" blocker**: popal fillers need not be zero),
  - `ecx = system@libc` (0xf7dc0ce0), `eax = printf@GOT` (0x804c004),
  - `mov [eax], ecx; ret` @0xf7da9aee (libc+0x3caee) performs the write,
  - return into safecode's loop head @0x8049260 — main never exits, and the thread's loop calls the patched function once a second, forever.  No pivot to maintain, no sleep-return slot to defend, no syscall numbers to smuggle.
  - The command string is whatever the thread already passes: `printf("%d\n", i++)` → `system("%d\n")`.  An executable named `%d\n` on PATH (the planted script: `cp /etc/vortex_pass/vortex13 ./leak13.txt; chmod 644`) delivers the password.
- **The libc base without gdb:** ASLR is off, so the parking-loop trick leaks it live — a payload parks main in safecode's loop with `[ebp-0xc] = sleep@GOT (0x804c00c)`; the loop prints that dword each iteration: first the unresolved PLT address, then the resolved `libc_base + 0x10b680` = `0xf7e78680` → base `0xf7d6d000`, identical for a setuid and a non-setuid exec (verified twice with different env sizes).
- **The privilege race, resolved:** the race IS the privilege (RACE.md derivation), and **retries win it**: the planted script ran at euid 5012 on the first loop iterations (real shell errors `Permission denied` printed live in the cast) and on a later iteration ran as vortex13 — the thread's own `fix_perms` (`setresuid(5013,5013,5013)`, process-wide) had won the race by then.  Over -T transports the win lands within a 30s window in 3/3 measured trials; the level is killed by `timeout` afterwards so no orphan survives.
- **Files:** `tools/vx/l12/` (`build12.py` payload builder, `drv12.c` raw-bytes argv driver, `rec12.sh` + `l12.cmds` recording drivers, `vortex12` + `libc32.so` re-derived from the lab, `RACE.md` the race verdict, `HINTS.md` the approved hints).

## Level 11 → vortex12 (SOLVED 2026-11-16)
- **Password for vortex12:** `YufVIb8Mo`, dumped by the shellcode from `/etc/vortex_pass/vortex12` and verified by logging in as vortex12 (`uid=5012`, `cat /etc/vortex_pass/vortex12` matches). Recording: `recordings/vortex/L11.cast`.
- **The program (reconstructed from objdump):** `/vortex/vortex11`, mode 4550, setuid vortex12, 20660 bytes, md5 `c6b84d4cebbd082a3c852c83305443b2`, not stripped, **embeds its own phkmalloc** (the FreeBSD allocator — `malloc`/`malloc_bytes` compiled in; GOT shows `mmap/munmap/madvise/brk/sbrk`, no `malloc@GLIBC`), `GNU_STACK RWE` (executable stack, ASLR off):
  ```c
  int main(int argc, char **argv) {
      if (argc <= 2) exit(0);
      char *a = malloc(0x800);
      char *b = malloc(0x10);
      char *c = malloc(0x800);
      strcpy(c, argv[1]);            /* UNBOUNDED heap overflow */
      char *d = malloc(0x10);
      strncpy(d, argv[2], 0xf);      /* the write primitive */
      exit(0);
  }
  ```
  Heap layout (gdb-verified): `a=0x804f000`, `b=0x8050030`, `c=0x804f800`, `d=0x8050040`; the second page's phkmalloc **page header** (`prev/next/info/bits/bitmap`) sits at `0x8050000`.
- **The exploit: overflow c's 2048 bytes into the next page header.**  `argv[1] = 'A'*2048 + prev(0x11111111) + next(0x0804cfdc) + info byte(0x11)` — the copy then **stops at the NUL** after the info byte, so the header's `bits`/`bitmap` stay pristine (a junked `bits` would make malloc_junk's `memset(0xd0)` wipe the read-only RELRO page and crash).  The corrupt `next` makes `malloc(0x10)` walk a fake chunk whose bit_index shift returns `chunk->base + 64 = 0x804d01c` = **exit@GOT**; `strncpy(d, argv[2], 0xf)` then writes 15 bytes there, and main's final `call exit@plt` jumps into the EGG env var: a 1500-byte NOP sled + shellcode.
- **The shellcode (73 bytes, NUL-free, int 0x80):** builds `/etc/vortex_pass/vortex1` on the stack with 7 push-immediates, patches byte 24 `'1'→'2'` (`mov byte [ebx+24], 0x32`), then `open/read/write/exit` via `int 0x80` — the level is setuid **vortex12**, so the 400-mode pass file is readable by euid with no setreuid first.  Two lessons: `push 0x31786574` puts `"tex1"` in memory (an early draft pushed the bytes backwards and built `vor1tex2` → ENOENT); and the first "syscall filter" evidence was a **64-bit harness artifact** — `seccomptest`/`wt.c` were compiled with plain `gcc` (64-bit) and `memcpy(o+7, &path, 4)` copied only the low 4 bytes of an 8-byte pointer, so `int 0x80 open → -14 (EFAULT)` was literally "bad address", not interception.  A `gcc -m32` probe on the lab showed open/read/write all succeed (getpid had already returned 12 — int 0x80 worked all along).
- **Pinning the EGG address (no gdb sweep):** with ASLR off, the kernel places env strings identically for any execve with the same total argv+envp byte lengths; a helper `h11.c` (`printf("%p", getenv("EGG"))`, invoked with the same two argv strings) reports the exact address the level will see (`0xffffd7d7` live).  Target = `EGG + 1024` mid-sled; argv[2] cannot contain NULs, so a 0 low byte would shift the target by 1.
- **Files:** `tools/vx/l11/` (`build11.py` payload builder, `h11.c` address pin, `solve11.sh` end-to-end driver, `NOTES.md`).

## Level 10 → vortex11 (SOLVED 2026-11-16)
- **Password for vortex11:** `xb4DVZ2av`, read from `/etc/vortex_pass/vortex11` in the shell the level spawns and verified by logging in as vortex11 (`uid=5011`, `cat /etc/vortex_pass/vortex11` matches). Recording: `recordings/vortex/L10.cast`.
- **The program (reconstructed from objdump):** `/vortex/vortex10`, mode 4550, setuid vortex11, 15352 bytes, md5 `49dcf2fee434ab1eb8f0b5bdc4104729`, not stripped, `GNU_STACK RW` (no shellcode possible), full RELRO-ish GOT (but not needed):
  ```c
  int main(void) {
      struct tms t;
      unsigned base = times(&t) + t.tms_utime + t.tms_stime
                    + t.tms_cutime + t.tms_cstime + clock() + time(0);
      int N = 128 - (base % 256);
      unsigned seed = N + time(0);      /* the srand argument */
      srand(seed);
      setvbuf(stdout, 0, _IONBF, 0);
      for (int i = 0; i < N; i++) rand();          /* N skipped draws */
      putchar('[');
      unsigned arr[20];
      for (int i = 0; i <= 19; i++) { arr[i] = rand(); printf(" %08x,", arr[i]); }
      puts("]");
      alarm(30);
      unsigned target;
      read(0, &target, 4);
      if (target == seed) {           /* must echo the exact srand seed */
          setresuid(geteuid(), geteuid(), geteuid());
          execlp("/bin/sh", "sh", "-i", 0);
      } else
          puts("Nope, try again");
  }
  ```
  The gate: `read(0, &target, 4)` must equal **the exact `srand()` seed** — `N + time(0)` where `N = 128 - ((times()+clock()+time()) % 256)`. The seed is not printed, but the 20-value `rand()` window is — and glibc's `rand()` is fully deterministic given the seed.
- **The solve: reverse the seed from the printed rand() window.** Emulating glibc's TYPE_3 rand in python failed (my warmup/output indexing was off for this build), so the cracker uses **the target's own libc**: a C program that, for every candidate seed (time ±600 s) and every skip count (0–500), calls `srand(candidate)`, skips that many draws, and compares the next 20 against the printed array. A 20-value match is ~2⁻¹⁶⁰, so the found `(seed, skip)` is exact.
- **The gotchas (each measured live):**
  - The loop count `N` is a *signed* mod (`sar/shr/movzbl/sub` idiom): `128 - (base % 256)` can be negative, in which case zero draws are skipped and the printed window starts at draw #1 — the cracker must therefore cover both positive and negative-seed ranges (`N` as large as ~366 was observed, since the `times()/clock()` jitter shifts `base`).
  - The two `time()` calls differ by the loop's runtime, so `seed − now` can be a few hundred seconds — the ±600 s window covers it.
  - The answer is `read(0,&target,4)`: the seed is sent as 4 raw little-endian bytes. On a match the level `setresuid`s to euid and spawns `sh -i` — my driver feeds it `id; cat /etc/vortex_pass/vortex11; exit` on stdin.
  - The cast driver's prompt regex used `vortex[0-9]` (single digit) — `vortex10`+ needs `vortex[0-9]+`; that's why the first two recording takes timed out.
- **Files:** `tools/vx/l10/cracke.c` (the libc-based seed cracker), `tools/vx/l10/solve10.py` (run the level, parse the window, crack, answer, verify the spawned shell).
- **Recording:** `recordings/vortex/L10.cast` — local shell, ssh vortex10, workdir `/tmp/l10rec-25004`, the binary's md5/main disassembly and relocation table, `GNU_STACK RW`, the live gate shown (`Nope, try again`), `cracke.c` and `solve10.py` typed in vim from empty buffers, `cracke` compiled, the crack printing `FOUND seed=1794839484 skip=366`, the spawned shell's `uid=5011(vortex11)` and `xb4DVZ2av`, then login as vortex11 from the local shell (`uid=5011(vortex11)`, password file read).

## Level 9 → vortex10 (SOLVED 2026-11-16)
- **Password for vortex10:** `95KsP1i3K`, read from `/var/mail/vortex9` and verified by logging in as vortex10 (`uid=5010`, `cat /etc/vortex_pass/vortex10` matches). Recording: `recordings/vortex/L9.cast`.
- **This level is the BlackBox.** The official page (overthewire.org vortex9.html) is titled "BlackBox" and says only *"There is no information available for this level. Login to vortex.labs.overthewire.org and check it out."* — no hints, no source.
- **The level-9 binary is missing.** Every other level N has `/vortex/vortexN` (mode 4550, owner vortex(N+1), group vortexN — the current level's user runs it by gid). Level 9's binary does not exist: `stat /vortex/vortex9` → `No such file or directory`; the listing jumps from `vortex8` (4550 vortex9:vortex8) straight to `vortex10` (4550 vortex11:vortex10).
- **The next binary is unreachable from vortex9 (measured live).** `/vortex/vortex10` is `4550 vortex11:vortex10`: only euid=vortex11 or gid=vortex10 can read/execute it. vortex9 has gid 5009 only, `setgid(5010)` is refused (EPERM), `/etc/security/group.conf` has no active pam_group rules, the sshd PAM chain contains no pam_group, and the `vortex10` group has no members to inherit from. `/etc/vortex_pass/vortex10` is `400 vortex10:vortex10`. So there is no route to run the level-10 binary from vortex9 at all — and none is needed.
- **The solution: the password arrives by mail.** `/var/mail/vortex9` (mode 640, owned by vortex9) contains the 9-char password in plain text: `95KsP1i3K`.
- **Recording:** `recordings/vortex/L9.cast` — local shell, ssh vortex9, workdir `/tmp/l9rec-10419`, the missing-binary stat, the next binary's mode and the group dead-ends, the mail file found and read, then login as vortex10 from the local shell (`uid=5010(vortex10)`, password file read).

## Level 8 → vortex9 (SOLVED 2026-11-16)
- **Password for vortex9:** `XdTW4yCeq`, read by the hijacked *thread* (euid=vortex9) from `/etc/vortex_pass/vortex9` and verified by logging in as vortex9 (`uid=5009`, `cat /etc/vortex_pass/vortex9` matches). Recording: `recordings/vortex/L8.cast`.
- **The program (reconstructed from objdump, no published source — the level page says "Disassemble this dynamically linked executable"):** `/vortex/vortex8`, mode 4750, setuid vortex9, 15152 bytes, md5 `a2cae4e765bc58316b34dbe7f64af120`, not stripped:
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
      syscall(164, getuid(), getuid(), getuid());  /* setresuid — drops euid 5009→5008 */
      unsafecode(argv[1]);             /* the overflow runs AFTER the drop */
  }
  ```
  So the overflow gives code execution as plain vortex8, while `/etc/vortex_pass/vortex9` is `-r-------- vortex9:vortex9` — only euid=vortex9 can read it.
- **The key measurement (a clean-run poller, then a geteuid()-in-the-thread shellcode):** the thread is created *before* the drops, and the raw `syscall()` calls in this glibc do **per-thread** credentials — the thread **keeps euid=vortex9** while main drops to 5008. Measured live two ways: a fork+exec poller that snapshots `/proc/<pid>/task/*/status` in a tight loop caught one task at `Uid: 5008 5009 5009 5009` while the other was all-5008 (the transient broadcast state), and a uid-printing shellcode executed *inside the hijacked thread* reported `geteuid()=5009` seconds later — the thread still runs as vortex9 for its whole life. (First gdb /proc snapshots showed both tasks at 5008 — gdb holds threads in signals and perturbs the setxid broadcast; the clean-run poller settles it.)
- **The exploit chain:** 1100-byte argv[1] (raw bytes via a fread/execv driver, NUL-free):
  1. `strcpy` copies all 1100 bytes into unsafecode's 1024-byte buffer — offset 1036 = unsafecode's saved eip.
  2. Bytes 8..25: a GOT-patcher shellcode (`mov eax,&sc2; mov [0x804c00c],eax; push 0x80491e3; ret`) that overwrites **`sleep@GOT`** (0x804c00c, writable — outside the 0x804bf00–0x804c000 RELRO region) with the address of the password shellcode, then returns main into `safecode`'s loop head so the process never exits.
  3. Bytes 48..112: the password shellcode (`open("/etc/vortex_pass/vortex9",0); read; write(1,…)`) — called by **the thread** via the hijacked `sleep@GOT` every loop iteration, with euid=5009.
  4. Bytes 1032..1035: a readable address (0x0804a008) over unsafecode's saved ebp so the loop's `push -0xc(%ebp)` doesn't fault.
- **The gotchas (each measured live):**
  - The race window is thread-vs-broadcast: a naive poller shows the thread dragged to 5008 within ~20 µs in a gdb-attached run, but in a clean no-pty session the thread keeps 5009 for its whole life.
  - **The session type matters (measured live):** over `ssh -T` (no pty) the thread keeps euid=5009 and the exploit works; over `ssh -tt` (pty) the setxid broadcast drags the thread to 5008 and the exploit fails. The recorded exploit run is therefore transported over `ssh -T` while the `-tt` session displays it — stated plainly in the cast as a comment.
  - The stack buffer address drifts with the session's environment: measured 0xffffd310 (gdb exec-follow), 0xffffd998 (the working fork/exec shape). The solve script sweeps candidate addresses and detects the hit by a uid-signature shellcode that prints `getuid()/geteuid()` from inside the hijacked thread (looking for 5009) before running the password shellcode.
  - My first password shellcode pushed the path chunk `9pss` instead of `tex9` — the open() returned ENOENT (fd −2, printed live by a debug shellcode) instead of EACCES; the fixed chunking is `push 0; push 'tex9'; push '/vor'; push 'pass'; push 'tex_'; push '/vor'; push '/etc'` = `/etc/vortex_pass/vortex9\0`.
- **Files:** `tools/vx/l8/drv8.c` (raw-bytes argv driver: fread a file, execv `/vortex/vortex8`), `tools/vx/l8/solve8.py` (payload builder + sweep + uid-signature hit detection + password run).
- **Recording:** `recordings/vortex/L8.cast` — local shell, ssh vortex8 (`-tt`), workdir `/tmp/l8rec-9319`, the binary's md5/safecode/unsafecode/main disassembly, `sleep@GOT` in the relocation table, `GNU_STACK RWE`, the pass file's mode, `drv8.c` and `solve8.py` typed in vim from empty buffers, `drv8` compiled, the sweep + uid hit + password run (its output appearing from the `ssh -T` transport, shown as a comment in the terminal), then login as vortex9 from the local shell (`uid=5009(vortex9)`, password file read).

## Level 7 → vortex8 (SOLVED 2026-11-16)
- **Password for vortex8:** `X2cOOCYnT`, printed by the exploit shellcode from `/etc/vortex_pass/vortex8` and verified by logging in as vortex8 (`uid=5008`, `cat /etc/vortex_pass/vortex8` matches). Recording: `recordings/vortex/L7.cast`.
- **The program (reconstructed from objdump, no published source — the level page says "Generic Binary Exploitation"):** `/vortex/vortex7`, mode 4750, setuid vortex8, 14956 bytes, md5 `c4f614fe053e5e2f3d4c34e0d34fd878`, not stripped:
  ```c
  int main(int argc, char **argv) {
      unsigned crc = crc32(0, argv[1], strlen(argv[1]));
      if (crc == 0xe1ca95ee)
          strcpy(buf, argv[1]);   /* buf = ebp-0x46: 70 bytes to the saved regs */
      else
          printf("0x%08x\n", crc);
  }
  ```
  The gate: `crc32(0, argv[1], strlen(argv[1]))` must equal **`0xe1ca95ee`** — and CRC32 is a linear function over GF(2) on the message, so any payload can be patched to any target CRC by solving a 32-variable linear system over 4 free bytes.
- **The epilogue (measured in objdump, the key to the ret placement):** main ends
  `lea -0x8(%ebp),%esp; pop %ecx; pop %ebx; pop %ebp; lea -0x4(%ecx),%esp; ret`
  — the final `ret` does NOT pop the address after the saved registers; it pops it from **`ecx-4`**, where `ecx` is loaded from payload bytes 62..65. So the control flow is: bytes 62..65 → ecx; `esp = ecx-4`; `ret` pops bytes at ecx-4 as the return address. With ecx = buf+78, the ret address is read from bytes 74..77 and execution lands at the address stored there.
- **The exploit chain:** 350-byte argv[1]:
  1. `crc32(0, payload)` == 0xe1ca95ee — achieved by appending a 4-byte CRC patch solved over GF(2) (`crcpatch.py`): the CRC of base+patch is linear in the 32 bits of the patch, so build the 32 deltas (one per bit), row-reduce to a basis, and solve for the selection vector. No guessing, deterministic.
  2. `strcpy` copies all 350 bytes into buf@ebp-0x46 — bytes 62..65 set ecx = buf+78; bytes 74..77 hold ret = buf+160 (mid-sled).
  3. `ret` lands in a 187-byte NOP sled leading into an 81-byte shellcode on the RWE stack (`GNU_STACK RWE`, ASLR off).
  4. The shellcode does **`setreuid(5008,5008)`** first (`xor ebx,ebx; mov bh,0x13; mov bl,0x90` = 5008 without NUL bytes — the literal would end the strcpy), then open/read/write `/etc/vortex_pass/vortex8` to stdout and exit(0).
- **The gotchas (each measured live):**
  - The buffer address shifts with argv length and the ssh session's environment: 0xffffda22 in the probe sessions, 0xffffd212 in the recorded one. It must be measured under gdb in the *same* session shape (`break *0x804920e` at the crc compare, `p/x $ebp-0x46` with a 350-char dummy) — a 187-byte NOP sled absorbs the remainder.
  - The vortex8 arg to setuid() is 5008 = 0x1390 — little-endian `90 13 00 00` contains NUL bytes, which terminate strcpy. Built the value with register arithmetic instead (two `mov bh/bl` halfwords).
  - A ret2libc `system("/bin/sh")` chain spawns a shell whose `id` shows only `uid=5007` — the dynamic loader drops the effective uid for the non-setuid child; the shell then reads the pass file as vortex7 and fails. `setreuid` inside the payload's own shellcode fixes this at the source.
- **Files:** `tools/vx/l7/crcpatch.py` (GF(2) linear CRC patch solver), `tools/vx/l7/ex7.py` (payload builder), `tools/vx/l7/drv.c` (raw-bytes argv driver: fread a file into a NUL-free buffer, execv `/vortex/vortex7` with it as argv[1]).
- **Recording:** `recordings/vortex/L7.cast` — local shell, ssh vortex7, unique workdir `/tmp/l7rec-10314`, the binary's md5/PLT/GNU_STACK disassembly (`RWE` stack confirmed), the live CRC gate shown (`/vortex/vortex7 test` → `0xf93ba110`), `crcpatch.py` typed in vim from an empty buffer and self-checked (`crc7(full): 0xe1ca95ee target: 0xe1ca95ee`), the buffer address measured with gdb in the same session (`$1 = 0xffffd212`), `ex7.py` and `drv.c` typed in vim from empty buffers, `drv7` compiled, the payload built (`buf=0xffffd212 sc=81 sled=187 len=350`), `./drv7 pay7.bin` printing `X2cOOCYnT` (RC=0), then login as vortex8 from the local shell (`uid=5008(vortex8)`, password file read).

## Level 6 → vortex7 (SOLVED 2026-11-16)
- **Password for vortex7:** `kZ90cmNy9`, read from `/etc/vortex_pass/vortex7` in the shell the restart() execs and verified by logging in as vortex7 (`uid=5007`, `cat /etc/vortex_pass/vortex7` matches). Recording: `recordings/vortex/L6.cast`.
- **The program (reconstructed from objdump, no published source — the level page says "Generic Binary Exploitation"):** `/vortex/vortex6`, mode 4750, setuid vortex7, 14984 bytes, md5 `db0119220e93bde3024e6f5d1bf185f0`. The binary is not stripped:
  ```c
  void restart(char *arg) {
      setreuid(geteuid(), geteuid());   /* real uid = euid = vortex7 */
      execlp(arg, arg, 0);              /* re-exec arg */
  }
  int main(int argc, char **argv) {
      if (argv[0] != NULL) restart(argv[0]);   /* argv[0], not argv[1]! */
      printf(argv[3]);                          /* a format-string bug */
      _exit(0x7325);
  }
  ```
- **Measured live:** running `/vortex/vortex6` with no argument HANGS — `argv[0]` is the binary path (non-NULL), so `restart(argv[0])` re-execs the binary itself, whose `argv[0]` is the same path again: an infinite exec loop (the ssh channel blocks even under `timeout 3`; a detached `nohup` run produces a 0-byte output file). `GNU_STACK` is **RW** (not RWE like vortex4/5), so the format-string hole (`printf(argv[3])`, reachable with an argv[0]-NULL exec) cannot run shellcode on the stack.
- **The exploit — argv[0] is the program restart() re-execs:** `restart` calls `execlp(arg, arg, 0)` where `arg` is `argv[0]` of the current process. The setuid binary elevates to euid=vortex7 and `setreuid(geteuid(), geteuid())` pins the real uid to vortex7 before exec'ing whatever `argv[0]` names. So `execve("/vortex/vortex6", ["/bin/sh"], env)`: main sees `argv[0] = "/bin/sh"` ≠ NULL → `restart("/bin/sh")` → `setreuid(v7, v7)` → `execlp("/bin/sh", "/bin/sh", 0)` → a shell with real uid vortex7.
- **Gotcha (measured):** a *copy* of the binary does NOT work — `cp` drops the setuid bit and the shell runs as vortex6; the original `/vortex/vortex6` path is required.
- **Recording:** `recordings/vortex/L6.cast` — local shell, ssh vortex6, the hang shown via a detached run (0-byte output), the copy's md5, the full `restart`/`main`/PLT/GNU_STACK disassembly, `ex.py` typed in vim from an empty buffer (`[New] 12L, 440B written`), the exploit printing `uid=5007(vortex7)` and `kZ90cmNy9`, then login as vortex7 from the local shell (`uid=5007`, password file read).

## Level 5 → vortex6 (SOLVED 2026-11-16)
- **Password for vortex6:** `o5kBPzSFM`, read from `/etc/vortex_pass/vortex6` in the shell the level spawns and verified by logging in as vortex6 (`uid=5006`, `cat /etc/vortex_pass/vortex6` matches). Recording: `recordings/vortex/L5.cast`.
- **The program (verified against the live binary):** `/vortex/vortex5`, mode 4750, setuid vortex6, 15428 bytes. It is the published source (overthewire.org vortex5.c, "A tribute to arc :)"): glibc's MD5 (Colin Plumb) plus `x = getpass("Password: ")`, then `MD5Update(&a, x, strlen(x))`, then a 16-byte memcmp against `155fb95d04287b757c996d77b5ea51f7`; on a match it `setresuid`s to euid and runs `/bin/sh`.
- **Measured live:** the empty password prints `:00` (`strlen(x)==0`, `x[-1]` is the byte before getpass's static buffer; `MD5("")` is not the target); the printf leaks the input's last char and its code (`t:74` for "test"); getpass truncates long input (the echoed last char stays `'A'` from length 8 to 50000), so the buffer-overflow angles all die.
- **The solution is the MD5 preimage crack:** the target hash is the MD5 of the password itself (no newline — getpass strips it). rockyou (14M words), with/without a newline, with mangling rules: not found. Brute force over the alphanumeric space finds it at length 5: **`rlTf6`** (`MD5("rlTf6") = 155fb95d...`).
- **The cracker** (`tools/vx/l5/crack5.py`) forks 8 children over the 62^5 space, each checking one chunk of first letters via `os.fork` + `os.pipe` — multiprocessing's Pool needs POSIX semaphores, which the target's /dev/shm does not provide (measured: `FileNotFoundError` from `_multiprocessing.SemLock`), so the crack runs locally.
- **Recording:** `recordings/vortex/L5.cast` — local shell, ssh vortex5, `crack5.py` typed in vim from an empty buffer on the target (`[New] 29L, 924B written`, paste mode set first so the python indentation lands exactly), `cat -n` of the file, then the same file recreated locally via heredoc and run (`FOUND: rlTf6`), `md5sum` verification, ssh again, `/vortex/vortex5` with the password (`You got the right password, congrats!`), the spawned shell as vortex6 (`uid=5006`), the password file read, then login as vortex6 from the local shell (`uid=5006`, password file read).

## Level 4 → vortex5 (SOLVED 2026-11-16)
- **Password for vortex5:** `uwaRhgNq1`, printed by the exploit shellcode from `/etc/vortex_pass/vortex5` and verified by logging in as vortex5 (`uid=5005`, `cat /etc/vortex_pass/vortex5` matches). Recording: `recordings/vortex/L4.cast`.
- **The program (verified against the live binary):** `/vortex/vortex4`, mode 4750, setuid vortex5, 14844 bytes, md5 `c77d90d5aefe8dc716e341bb518798b4`. It is the published source (overthewire.org vortex4.c, "andrewg, original author was zen-parse"): `if (argc) exit(0); printf(argv[3]);`. The live build adds the 2013 fix — `argc==1` with `argv[0][0]==0` also passes — so `argc==1, argv[0]=""` reaches `printf(*(argv+12))`, which with a one-entry argv is `envp[1]`: the format string is the second environment variable (confirmed live).
- **Why the usual routes die (all measured live):** `.got.plt` (0x804c000) is writable but no vararg points into it; the GNU_RELRO segment 0x804bf00..0x804c000 makes `.init_array`/`.fini_array`/`.dynamic`/`.got` read-only (a `%n` through slot 6/27 → 0x804bf04, or slot 19 → 0x0804908d, segfaults); the stack-pointer slots (9/13/18 = `&argc`, 14 = `&envp[0]`) write to cells nothing reads after printf (`%9$n`, `%13$hn`, `%14$hn`, `%18$hn` all change nothing); no vararg points into the env strings.
- **The route that works:** printf's varargs walk *up* the stack past the initial block (argc, argv, envp, auxv) into the strings area — into the format string's own bytes. Verified with marker probes: a dword embedded in `fmt` is read back as a vararg (the slot shifts with the format length; swept 110..130 with a same-length skeleton). The exploit embeds the two raw addresses of exit's GOT slot (`0x0804c008`) and its high half (`0x0804c00a`) at `fmt+6`/`fmt+10` (a 6-byte `X` prefix puts them on the vararg boundary), then:
  1. `%057229c%125$hn` — cumulative 57246 = `0xDF9E` written into `0x0804c008` (exit's GOT low half = the shellcode address's low half);
  2. `%073825c%126$hn` — cumulative 131071 = `0x1FFFF`; `0xFFFF` written into `0x0804c00a` (the high half);
  3. exit's GOT slot now holds `0xFFFFDF9E` = the shellcode address (fmt_addr `0xFFFFDF6A` measured via an envp-pointer probe, + 52);
  4. `exit(0)` → `jmp *0x804c008` → the 69-byte shellcode on the **RWE stack** (`readelf -l`: `GNU_STACK ... RWE`) with euid vortex5 reads `/etc/vortex_pass/vortex5` and prints it.
- **Determinism:** ASLR is off (the OTW MOTD says so) and the env layout is fixed, so the shellcode address is exact. Widths are zero-padded to 5 digits so any count change keeps the 121-byte format length fixed.
- **Recording:** `recordings/vortex/L4.cast` — local shell, ssh vortex4, `sc.asm`/`ex6.py`/`gen.py` typed in vim from empty buffers, `cat -n` of all three, nasm (69 bytes), xxd hexdump + NUL check, `fmt 121` built, the exploit printing `uwaRhgNq1`, then login as vortex5 (`uid=5005`, password file read).

## Level 3 → vortex4 (SOLVED 2026-11-16)
- **Password for vortex4:** `TlI5kxGd1`, read live from `/etc/vortex_pass/vortex4` by the exploit shellcode and verified by logging in as vortex4 (`uid=5004`, `cat /etc/vortex_pass/vortex4` matches). Recording: `recordings/vortex/L3.cast`.
- **The program (verified against the live binary):** `/vortex/vortex3`, mode 4750, 11300 bytes, md5 `17b12585fd1a15df97d13e84364744cf`. It is the 0xbadc0ded #02 source: `strcpy(buf, argv[1])` with `buf[128]`, then a check on `lpp`, then `tmp = *lpp; **lpp = &buf; exit(0)`. The check is `mov $0,%ax; cmp $0x8040000`, so only the high half of `lpp` matters and any `lpp` of the form `0x080Xxxxx` passes. `buf` is at `ebp-0x90`, so the saved `ebp` is at `buf+148`.
- **Correction:** an earlier version of this file (and of `tools/vx/l3/main.dis`) described a bytecode-VM `main` with a stack walk and a two-trap pivot. That text does not match the binary. Re-reading the same addresses from several sessions, including a fresh copy of `/vortex/vortex3`, shows the code above. The VM description is withdrawn; the corrected disassembly is `tools/vx/l3/main.dis`.
- **The key that the earlier notes missed:** the live binary's `GNU_STACK` is **RWE** (`readelf -l` → `GNU_STACK ... RWE`). The 2026-11-08 probe only proved the GOT *page* is non-executable; it never tested the stack. With an executable stack, the store `**lpp = &buf` is a one-gadget write of a stack address into any GOT slot the final `exit(0)` consults.
- **The exploit:** `lpp = 0x08049052` — the immediate of exit@plt's own `jmp *0x804b200` (PLT entry at `0x8049050`, bytes `ff 25 00 b2 04 08`). It is in `.text` (readable, NUL-free, passes the `0x0804xxxx` check). `**lpp = &buf` then writes the stack address of `buf` straight into **exit's GOT slot** `0x804b200` (`.got.plt` is writable — no RELRO segment on this binary). The very next instruction `call exit@plt` jumps through `0x804b200` and lands on `buf`: the shellcode on the RWE stack executes with euid 0 (setuid root binary).
- **Payload:** 69-byte NUL-free shellcode (open/read/write `/etc/vortex_pass/vortex4`, exit 0), 'A' filler to offset 128, 'AAAA' filler for `lp` (128..131), then `52 90 04 08` at offset 132 (the `lpp` slot) — 136 bytes, delivered as `argv[1]` by the raw-bytes driver `drv` (shell substitution mangles the argument, see the 2026-11-07 method note).
- **Earlier notes' open routes are all closed by this:** the GOT-slot candidates in `tools/vx/l3/NOTES.md` were only `0x804b1xx` entries that `exit` faults on or never consults; the slot that works is the *caller's own immediate*, which `exit@plt` dereferences on the next instruction. The notes' finalizer test (fini array) and the exit-reached probe are superseded by the RWE-stack observation.
- **Recording:** `recordings/vortex/L3.cast` — local shell, ssh vortex3, `sc.asm` and `drv.c` typed in vim from empty buffers (`[New] 28L, 433B` / `[New] 6L, 247B`), `cat -n` of both, nasm (69 bytes), xxd hexdump + NUL check, `drv` payload build (136 bytes), `./drv pay` printing `TlI5kxGd1`, then login as vortex4 (`uid=5004`, password file read).

## Level 2 → vortex3 (SOLVED 2026-11-06 — password verified 2026-11-17)
- **Where it comes from:** `0xbadc0ded.org` challenge #02. The shipped source is a tar wrapper:
  ```c
  int main(int argc, char **argv) {
      char *args[] = { "/bin/tar", "cf", "/tmp/ownership.$$.tar", argv[1], argv[2], argv[3] };
      execv(args[0], args);
  }
  ```
- **The idea (Klaus' approach):** `vortex2` is setuid vortex3, so the tar it runs can read `/etc/vortex_pass/vortex3`, and it writes that file into `/tmp/ownership.$$.tar`, which is vortex3-owned but readable by us (mode 664). Copy the archive and extract it. The `$$` is literal: no shell expands it, so the path never changes.
- **Measured on the live build (32-bit, GCC 15.2):**
  - One argument: `/bin/tar cf /tmp/ownership.$$.tar <arg1>`. Give it `/etc/vortex_pass/vortex3` and tar reports "Removing leading `/'" and writes a 10 KB archive with member `etc/vortex_pass/vortex3` (10 bytes, uid 5003), owner uid 5003 on disk.
  - Two arguments: the same, with two file names after the archive name.
  - Three or more: a bad-address (EFAULT) fault after the third argument, exit 0, no tar.
  - So the option slots are fixed and our arguments are always file names. That rules out `--checkpoint-action` (`-T` lists are data only; `TAR_OPTIONS` is rejected by tar 1.35), but it is exactly what is needed to have tar read the password file.
- **Live run (2026-11-06), from vortex1:**
  ```
  $ ls -l /vortex/vortex2 /etc/vortex_pass/vortex3
  -r-sr-x--- 1 vortex3 vortex2 14856 ... /vortex/vortex2
  -r-------- 1 vortex3 vortex3    10 ... /etc/vortex_pass/vortex3
  $ python3 /tmp/drop.py /tmp/job.sh     # drop.py = level-1 exploit -> shell as vortex2
                                         # job.sh  = the commands that shell runs
  ... /bin/tar: Removing leading `/' from member names
  $ python3 /tmp/tinspect.py
  archive /tmp/ownership.$$.tar exists True
  owner uid 5003 size 10240
  etc/vortex_pass/vortex3 10 uid 5003 mode 0o400   # tar tvf
  xRMRVus8g                                         # cat of the extracted file
  ```
- **Password for vortex3:** `xRMRVus8g`, read from the archive in an interactive session at 04:41-04:50 (extracted twice and once re-verified from a fresh vortex3 session). It is not on the MOTD. The `dev/null` member in `tar tvf` belongs to the interface, not the archive.
- **Status:** the password is read and verified. The transcript carries: the level-1 setup, the `drop.py`/`job.sh` files typed in vim, the vortex2 shell running `job.sh` (its line `/vortex/vortex2 /etc/vortex_pass/vortex3` is the step that makes tar run as vortex3, and tar's own "Removing leading `/'" is the confirmation), and the password's use. The archive listing/copy and the extraction are recorded as the commands run (copy of `/tmp/ownership.$$.tar` under a name we choose, extract, read) and in the interactive session above.
- **One caveat found along the way:** in this environment the wrapper could not be started from the typed/pipe-fed channel (line `<vortex2 path>` treated as a name: "Permission denied"), so the capture above comes from the interactive session; the transcript's typed run shows the next line tar prints. Several commands issued after the wrapper in the same scripted run made the second archive member unreadable for me; the transcript stops after the wrapper's own output.
- **Files:** `drop.py` starts the level-1 exploit and feeds `job.sh` to the vortex2 shell. `job.sh` runs `/vortex/vortex2 /etc/vortex_pass/vortex3`, copies `/tmp/ownership.$$.tar` into a private scratch directory and records the directory in `lastdir`. `tinspect.py` copies the archive to a scratch file and lists its members.

## Level 1 → vortex2
- **Account:** `vortex1`, password `Gq#qu3bF3` (from the level-0 service; login verified).
- **Goal:** `/vortex/vortex1` (setuid vortex2, 32-bit i386, NX stack, stack canary) reads stdin byte by byte into `buf[0x21c]` at `ebp-0x21c`, keeping a cursor `p` that starts at `buf+0x100`:

  | byte | effect |
  |---|---|
  | `\n` (0x0a) | `print(buf, 0x200)`: every byte shown as `"%x "` |
  | `\` (0x5c) | `p--` |
  | anything else | if `p <= buf+0x200`: `*p++ = c` |

  Before every read it checks `(p & 0xff000000) == 0xca000000`; on a match it calls `setresuid(geteuid(),…)` and `execlp("/bin/sh","sh",0)`.

- **The two obstacles, measured live:**
  1. `getchar` is redirected: a typed byte ≥ 0xc0 returns −1, so the 0xca the branch needs cannot be typed.
  2. The check runs before the byte is read, so the pointer must already read 0xca when a byte arrives.

- **What carries 0xca into the program.** On this build the `getchar` hook only filters keyboard-style input: bytes written into a **pipe** arrive intact, 0xc0 and above included. So the exploit writes two things to the program's stdin from a Python pipe:
  - 261 single backslashes, which walk the cursor from `buf+0x100` (0xffffdc00) down to **0xffffdc04** (each one is `p--`, regardless of where it points);
  - four raw **0xca** bytes, which are then stored as ordinary bytes and make the cursor's top byte 0xca at the next check, so `(p >> 24) == 0xca` fires the branch.

  The 261 count comes from the stack layout: `p` starts at `bp-0x11c` and the check reads `4·p + 12`, i.e. the word 8 bytes above the cursor (the saved frame pointer, then the return address). `(0xffff + 0xca·2^24) >> 24 == 0xca` with the frame pointer at 0xffffdbfc — one backslash more or less misses it, which is why **260 prints the buffer back** (`[ 0 0 0 …]`) and **261 gives the shell**. Stdin stays open so the shell is interactive.

  Things that do not work on this build: `printf '\357\202\212'`-style escapes and `echo '\134'`-style padding (they only crash the program with a stack-smash message); the raw bytes over a pipe are what work.

- **Live run (2026-11-04):**
  ```
  python3 /tmp/l1_exploit.py 261
    id                            # uid=5002(vortex2) gid=5001(vortex1)
    cat /etc/vortex_pass/vortex2  # qjUFVcpKl
  ```
- **Password for vortex2:** `qjUFVcpKl` (read from that shell; `ssh vortex2` verified).
- **Transcript:** `games/vortex.json` L1: disassembly, the hook measurement, the exploit typed into vim, and both backslash counts.
- **Earlier record:** the first attempt concluded 0xca was unreachable; it missed that backslashes walk the cursor out of the written region toward the frame. `tools/vortex1_model.py` keeps that model and the correction.

## Level 0 → vortex1
- **Account:** none needed — level 0 is a network service. The service runs on
  `vortex.labs.overthewire.org` port `5842`.
- **Goal (official description):** connect to port 5842, read four unsigned
  integers in host byte order, add them, send the sum back, and the reply is
  the username and password for vortex1. The machine is 32-bit x86, so "host
  byte order" is little-endian.
- **Technique and why it works:** a plain TCP client. The service writes
  exactly 16 bytes — four `uint32` values — and waits for a 4-byte reply. The
  values are in the machine's own byte order, so `memcpy` into `unsigned int`
  is the correct decode on a little-endian host; summing with 32-bit unsigned
  overflow wraps naturally, which is what the service expects. The service then
  sends back a short text line `Username: vortex1 Password: <password>` and
  closes the connection.

### Step-by-step discovery and crafting (what the recording shows)

1. **Probe the service before writing any code.** The official page says four
   unsigned integers; connecting and dumping the first bytes confirms it:
   ```
   python3 - <<'PY'
   import socket, struct
   s = socket.create_connection(("vortex.labs.overthewire.org", 5842), timeout=10)
   data = b""
   while len(data) < 16:
       data += s.recv(16 - len(data))
   print("raw bytes:", data.hex())
   print("4 uint32 little-endian:", struct.unpack("<4I", data))
   PY
   ```
   The reply is exactly 16 bytes, so the wire format is four little-endian
   `uint32`s.

2. **Write the client in vim, line by line.** The recording opens vim on a new
   file and types the program in insert mode; nothing is pre-written on disk.
   ```
   vim v0.c
   ```
   The program:
   - creates an `AF_INET`/`SOCK_STREAM` socket;
   - resolves `vortex.labs.overthewire.org` with `gethostbyname` (`inet_pton`
     only accepts a literal address — the first draft failed with
     `inet_pton: Success`, which is its "invalid input" return);
   - connects to port 5842;
   - reads until it has 16 bytes, `memcpy`s each 4-byte group into
     `unsigned int v[i]`, and sums;
   - writes the 32-bit sum back;
   - reads the reply **until the peer closes** into a 256-byte buffer — the
     reply can arrive split across several reads, and the 16-byte input buffer
     is far too small for it.

3. **Save and check the file.**
   ```
   :wq
   cat -n v0.c
   ```

4. **Compile.**
   ```
   gcc -Wall -O2 -o v0 v0.c
   ```
   `-Wall` matters here: the first compile caught the missing `<netdb.h>`
   (`struct hostent` undefined) before anything ran.

5. **Run it against the live service.**
   ```
   ./v0
   received: 928768003 738568258 532716586 1402472015
   sum:      3602524862 (0xd6ba2abe)
   Username: vortex1 Password: <password>
   ```
   The four values and the sum change on every run — the service randomises
   them — but the reply is always the same credentials.

6. **Verify by logging in.**
   ```
   ssh -p 2228 vortex1@vortex.labs.overthewire.org
   # id -> uid=5001(vortex1) gid=5001(vortex1) groups=5001(vortex1)
   ```
- **Password for vortex1:** taken from the live service reply and verified by
  an SSH login (not printed here; it is in the recording and in the game JSON).
- **Recording:** `recordings/vortex/L0.cast`