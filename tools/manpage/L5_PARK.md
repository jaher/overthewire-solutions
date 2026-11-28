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

## Exact blocker (external)
The natural win needs 0xdeadbeef to exist in the ld.so/libc startup residue at
an i-slot. Nothing attacker-controllable lands there on the CURRENT lab stack
(modern kernel + glibc, binaries rebuilt Oct 2025). The intended 2008-era
(intruded.net) mechanism - if it relied on an old libc startup leaving
deadbeef, or on a different loader path - does not reproduce here.
Re-check trigger: any change of the lab image (kernel/libc version, binary
md5), or a found writeup of the original game (search terms used: "manpage5
canyou 0xdeadbeef", intruded.net archives - none indexed).

## Working probes left in place on the server
/tmp/e208.b64+py (LD_PRELOAD filler = mechanism proof, works), /tmp/mp5_nosuid
(chmod -s copy for gdb), fresh-core geometry extraction (e224).
