# Manpage L5 park note (2026-11-28)

Level: /manpage/manpage5 (setuid manpage6), login manpage5/v2ltdizZfm.
Win: canyou()'s uninitialized `int i` (ebp-0xc) must read 0xdeadbeef -> setreuid+system("sh").

## What is PROVEN
- Mechanism confirmed by injection: an LD_PRELOAD constructor filling the stack
  below its own frame with 0xdeadbeef wins at ANY fill size (even 64 dwords).
  Winning i-slots = ctor-relative offsets -260..-100 (addresses ~368..1040 bytes
  below the ctor frame) = the ld.so/_dl_init startup residue region, i-slots
  hit every 20 bytes (frame stride measured 0x14 from the core; i at ebp-12).
- Frame geometry: stride 20B, frame layout [ebp-16 stray][ebp-12 i][ebp-8 canary]
  [ebp-4 ebx][ebp saved-eip... wait saved-ebp][ebp+4 ret]. Recursion crashes
  (SIGSEGV reading i below the 8MB map bottom) at ~416k frames, all i=0.
- The residue (8-16KB below the first canyou frame) = ld.so/libc startup frames:
  deterministic content, deadbeef-free, alignment-invariant across env sizes.

## What is RULED OUT (all on the real setuid binary + nosuid gdb dumps)
- env content injection: 19 candidate vars (TZ/LANG/LC_*/GLIBC_TUNABLES/LD_*)
  + deadbeef-valued PAD vars at 30-60KB: zero marker words in residue.
  200KB deadbeef env = E2BIG; 60KB x60 runs on the real binary: no win.
- argv injection: argv[0]/argv[1] deadbeef strings (12 shape combos, real
  binary): no win. argv/env/exec-path/cwd markers never appear in residue
  (gdb dumps: 0 hits for ZqYxWvUt / ../ZqYxWvUt/../ relative exec).
- env SIZE / alignment shifts: residue is relative to the loader frames which
  shift together with ebp1 - nz-count and i-slot values invariant
  (def/bigenv/dbenv/bigargv dumps differ only in pointer values + the two
  per-run random guard words at ebp-680/ebp+12, which never sit on i-slots).
- ulimit -s unlimited: OOM SIGKILL; suid core dumps: not produced (suid_dumpable=2
  writes nothing readable); LD_DEBUG/LD_SHOW_AUXV/LD_TRACE: no content injection.
- ptrace of the setuid binary: silently dropped at exec.

## Second pass (2026-11-28, this session) - blocker CONFIRMED with a frame map
- Residue frame map (gdb x/756xw band $ebp-3000..$ebp+64 on /tmp/mp5g): the band
  below the first canyou frame is owned by ld.so (_dl_start/_dl_main/_dl_init
  frames: ret ptrs f7fd7b39/f7fd012f/f7fd2af2/f7fd0d7e/f7fc99b4/f7fd02cb into
  ld-linux r-x 0xf7fc7000..0xf7fec000) and libc __libc_start_main frames
  (f7d8d7e7 into libc 0xf7d91000..). 102/150 i-slots at depths 2..92 hold
  non-zero startup dwords (link_map ptrs f7ffda60/f7ffcfd4, auxv values
  0x40/0x100/0x24c0000, stack ptrs) - deterministic, deadbeef-free, zero
  attacker-influenced bytes (env/argv/exec-path markers never land; prior pass).
- Per-run randomness: only TWO dwords vary between runs (0xffffd930, 0xffffdbe4
  = AT_RANDOM-derived guard words); a two-run diff confirms NEITHER lands on an
  i-slot (i-slots every 20B from ebp1-12 never coincide with them).
- Invocation-shape sweep on the REAL setuid binary, all SIGSEGV: env -i, 2000
  argv entries, 120KB single argv, ulimit -s 1MB/16MB/32MB, LC_ALL x3, via
  /lib/ld-linux.so.2, setarch -R, MALLOC_PERTURB_, GLIBC_TUNABLES hwcaps.
- LD_PRELOAD on the real setuid exec: silently stripped (constructor never
  runs; same .so preloads fine on the chmod -s copy and prints
  "PRELOAD uid=17005 euid=17005"; on the copy the fill then wins "I CAN!
  17005" via system sh - mechanism re-proven live this session).
- Sibling-account audit: NO setuid/setgid manpage6 binary except manpage5
  itself; earlier sources (0-3.c) read via their own accounts contain no
  euid-6 path; manpage4.diff = the already-solved wumpus; no manpage6 cron,
  no manpage6 mail, /home/manpage6 stock dotfiles. glibc 2.3.6 source grep:
  0xdeadbeef appears only in test code, never in startup/loader paths - the
  2008-era residue would have been ordinary libc startup garbage, not a
  planted constant; modern glibc 2.43's startup leaves nothing attacker-shaped.
- Web research exhausted available channels: Wayback holds ONE snapshot of
  intruded.net/manpage.html (level list only, no writeups; the "famous work of
  Ilja" link = Ilja's blog, dead); no public writeup of manpage5 exists on
  GitHub/bing/DDG/Google (all queries; search engines mostly bot-blocked).

## Exact blocker (external)
The natural win needs 0xdeadbeef to exist in the ld.so/libc startup residue at
an i-slot. Nothing attacker-controllable lands there on the CURRENT lab stack
(modern kernel 7.0.0-1014-aws + glibc 2.43, binaries rebuilt Oct 2025): the
residue is deterministic loader/libc startup data, the only per-run random
words miss every i-slot, and every injection lever is closed by AT_SECURE
(LD_PRELOAD stripped on the setuid exec).
Re-check trigger: any change of the lab image (kernel/libc version, binary
md5), or a found writeup of the original game (search terms used: "manpage5",
"canyou deadbeef wargame", "manpage wargame intruded writeup", intruded.net +
smashthestack forum archives - none indexed).

## Working probes left in place on the server
/tmp/e208.b64+py (LD_PRELOAD filler = mechanism proof, works), /tmp/mp5_nosuid
(chmod -s copy for gdb), fresh-core geometry extraction (e224).
