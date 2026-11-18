# Vortex L12 — hints only (last-resort exception, L12 only)

Scope: hints for the OTW session's blocked L12 attempt. Fresh re-solve rule
still stands for all other levels. No complete exploit, no copy-paste
commands, no passwords.

## What the level is

`/vortex/vortex12`, setuid vortex13, 32-bit, NX stack, partial RELRO
(writable GOT), not stripped. `main` spawns a thread running `safecode`,
then calls `fix_perms(getuid(), getgid())` (drops main to 5012), then
`unsafecode(argv[1])` — an unbounded `strcpy` into a 1032-byte buffer
(ret at buf+1036). The thread runs `fix_perms(...)` itself, then loops
forever: `printf("%d\n", i); fflush(stdout); sleep(1);`.
`fix_perms(a, b)` does `setresgid(a,a,a)` then `setresuid(b,b,b)` (raw
syscalls, return values ignored). `setresuid` is process-wide. The pass
file needs euid 5013.

## The session's blocker (from its own notes, tools/vx/l12/NOTES.md, RACE.md)

- Its L8-style race doesn't transfer: in L8 the thread never called
  fix_perms, so it kept euid forever. Here the thread calls fix_perms
  itself. The session built a full ROP chain (W1 = getgid@GOT ← geteuid@plt
  so the thread's fix_perms no-ops; W2/W3 = pivot the thread's sleep-return
  slot into an open/read/write chain) plus six variants, CPU hogs (1–24),
  and a saved-set-uid regain attempt. All dead-ended on three blockers:
  (1) W1 must land before the thread's getgid call — measured as
  unwinnable; (2) the thread re-pushes its own return address into the
  W2 slot on every sleep, overwriting the pivot; (3) mprotect is not
  imported and every useful syscall number has NUL bytes strcpy can't
  carry. 85/85 natural runs end at Uid 5012.
- RACE.md additionally concludes "blocked by the lab, not by the race":
  under gdb the process shows Uid 5012 before any program code runs.

## Hint 1 — The gdb/strace evidence is an artifact; the lab premise is fine

A setuid binary executed under ptrace runs WITHOUT the setuid elevation:
the kernel ignores setuid on exec when the execing thread is being
traced ("If the thread which calls execve() is being traced, execve
ignores setuid" — Linux-kernel mailing list, 2003, see Sources).
So the gdb finding "Uid 5012 before any program code" is EXPECTED under
gdb and proves nothing about the lab. The same applies to strace
(it is also ptrace). Both also distort the race timing, so neither can
settle whether the thread can win.

Cross-check from the session's own L8 solve: L8's binary is mode 4750,
setuid vortex9, and its solution relied on the thread KEEPING euid
vortex9 ("syscall() calls are per-thread: the thread keeps
euid=vortex9", tools/vx/l8/NOTES.md). That is only possible if the
process started with euid vortex9 via setuid. Setuid IS honoured in
this lab. Drop the "blocked by the lab" conclusion; the race is the
issue, not the lab. Any timing measurement used to judge the race must
come from untraced runs.

## Hint 2 — The intended solution is far simpler than the W1/W2/W3 chain

Both published writeups (rk700 2014, l3ouu4n9 2019 — see Sources) solve
L12 with the SAME idea as L8, and neither builds a ROP chain in the
thread at all:

- From main's overflow, do ONE 4-byte GOT write: replace a GOT entry
  for a function the thread calls every loop iteration (`printf` or
  `fflush`) with `system@libc`. The thread then executes `system()`
  with whatever argument it was already passing.
- The thread's loop is the delivery mechanism: it calls the patched
  function once a second, forever, so there is no rush, no stack pivot
  to maintain, no sleep-return slot to defend, and no syscall numbers
  to smuggle past strcpy. This sidesteps blockers (2) and (3) entirely.
- The "command string" is whatever the thread passes: if the target is
  `printf`, the thread passes its format string, so the command name is
  that format string — plant an executable of exactly that name in a
  directory on PATH. If the target is `fflush`, the thread passes the
  stdout pointer, so the command string is the raw bytes at that
  address — dump those bytes first; they are the filename to plant.
  The planted script just needs to copy the password file somewhere
  the vortex12 user can read it.

The session never tried this single-write approach; its six variants all
kept the complex thread-pivot design. The writeups' approach is strictly
less machinery than anything in tools/vx/l12.

## Hint 3 — The race, reframed: it is winnable in principle, and W1 may make it moot

The session's own RACE.md derives the key fact: if the thread's
fix_perms lands BEFORE main's fix_perms, the thread's setresuid(5013)
succeeds (5013 is still in the credential set), main's later
setresuid(5012) then fails with EPERM and is ignored, and the whole
process stays at 5013. The race IS the privilege — no W1/W2/W3 chain
is needed if it can be won. The published writeups never mention
fighting the race at all, which suggests that on the OTW server the
thread wins it often enough for a plain GOT-patch attempt to land —
or that their runs simply retried until it did.

Two decisive experiments the session has not cleanly run (both must be
untraced — see Hint 1):

1. W1-only probe: patch ONLY getgid@GOT ← geteuid@plt, keep main alive,
   and read /proc/<pid>/status Uid from another shell. 5013 means W1
   won and the thread kept privilege; 5012 means the thread's getgid
   already ran. Note the session's own contradictory measurements here:
   NOTES.md blocker (1) says the thread's getgid runs ~1.5 µs after
   pthread_create, but RACE.md's strace says main finishes fix_perms
   AND unsafecode while the thread is still in glibc startup. If the
   latter ordering holds in natural runs, main's ROP lands BEFORE the
   thread's first geteuid/getgid — and the session's own isolated test
   already supports this: patching getgid@GOT with a bad value killed
   the thread at its next GOT call, i.e. the patch landed BEFORE the
   thread's getgid. Settle it with the W1-only probe; do not trust the
   1.5 µs figure.
2. Retry loop on the plain GOT patch: run the single-write exploit in a
   loop and count outcomes. A race the thread wins even a fraction of
   the time is a solved level with retries. The session's 85/85 figure
   was measured with a sleep-payload that keeps main alive — re-measure
   with the plain patch, untraced.

Synthesis (strongest lead): combine the session's own verified W1 (it
lands before the thread's getgid — proven by the bad-value kill test)
with the writeups' single GOT write to `system`, and drop W2/W3
entirely. One ROP does both GOT writes (or the ebp-preserving loop
re-applies them), the thread keeps 5013 via W1, and its next loop
iteration calls the patched function. No pivot, no sleep-slot fight.

## Hint 4 — Mechanics the writeups use that the session's chain didn't

- Return to the `call strcpy` site INSIDE unsafecode rather than to a
  strcpy PLT entry: it lets the overflow itself perform the GOT write
  with attacker-controlled destination/source, using the payload bytes
  already on the stack.
- Preserve ebp across the first strcpy (rk700): main then effectively
  loops, re-applying the GOT patch forever. That keeps main (and the
  process) alive with no sleep-pivot and no plan for main's post-ROP
  behaviour — the thread gets unlimited loop iterations to hit the
  patched function.
- Preserve sleep@GOT: strcpy appends a NUL terminator one byte past the
  copied data, which lands on the first byte of the NEXT GOT entry.
  Write the copy so that NUL lands harmlessly (e.g. cover the target
  entry plus the neighbour's original bytes) — if sleep@GOT is
  destroyed, the thread dies at its first sleep call before it ever
  reaches the patched function. A neighbouring entry that is never
  called again may be sacrificed.
- printf vs fflush as the patch target: rk700 could not patch printf
  because that GOT address ends in a NUL byte, which would truncate
  the strcpy'd payload; l3ouu4n9 patched printf with no trouble.
  The two writeups' binaries differ from each other and from the
  session's current binary (GOT at 0x0804a000 in the writeups vs
  0x0804c000+ in the session's notes; libc base also differs). Do NOT
  reuse the writeups' literal addresses — re-derive every address
  (GOT entries, system@libc, the stdout bytes) from the session's own
  binary and its measured libc base, and check each candidate GOT
  address for NUL bytes in the payload path.
- mprotect is a dead end for the same NUL reason the session already
  found (rk700 tried it first and abandoned it); the GOT-to-system
  route is the way around it.

## What the session already tried (do not repeat)

Six ROP variants (sleep-pivot, patch re-apply loop, sleep-yielding loop,
multi-candidate leaks, .data value builders, env-independent leaks),
CPU hogs 1–24, saved-set-uid regain, W1/W2/W3 chain with a pop-esp
pivot and int 0x80 open/read/write. The write-what-where primitive and
the gadget set are already verified piece by piece. What is new here:
the single GOT write to `system` (no thread ROP at all), the
ebp-preserving main loop, the sleep@GOT preservation detail, the
gdb/setuid artifact correction, and the W1 + system-patch synthesis.

## Sources

- rk700, "vortex12" (2014) — the fflush→system writeup, with the
  ebp-preserving loop and sleep@GOT preservation detail:
  http://rk700.github.io/2014/09/13/vortex12/
- l3ouu4n9, "Overthewire Vortex Wargame", Level 12 → Level 13 (2019) —
  the printf→system writeup ("pseudocode is exactly the same as Level
  8, but this time the stack is not executable"):
  https://l3ouu4n9.github.io/post/wargames/overthewire/2019-12-02-overthewire-vortex/
- OverTheWire, Vortex level 12 (official): "Exploit this level knowing
  that the stack is not executable":
  https://overTheWire.org/wargames/vortex/vortex12.html
- Linux-kernel mailing list (2003), ptrace/setuid behaviour: "If the
  thread which calls execve() is being traced, execve ignores setuid":
  https://www.cs.helsinki.fi/linux/linux-kernel/2003-18/1586.html
- Session's own notes (read-only, DGX 1):
  ~/overthewire-solutions-work/tools/vx/l12/NOTES.md and RACE.md,
  vortex-solutions.md L12 section, tools/vx/l8/NOTES.md (setuid premise).
