# Vortex L12: the privilege race, measured (2026-11-17) — SOLVED (2026-11-18)

## The structural fact the old notes missed

`fix_perms(gid, euid)` maps arg1 -> setresgid, arg2 -> setresuid
(`mov 0x8(%ebp),%edx` -> the setresgid word; `mov 0xc(%ebp),%eax` -> the
setresuid word).  safecode pushes ebx (euid) then eax (gid), so:

- main: fix_perms(uid=5012, gid=5012) -> setresgid(5012..) OK, setresuid(5012,5012,5012) = 0
- thread: fix_perms(euid, gid) -> setresgid(5012..), setresuid(5013,5013,5013)

setresuid is process-wide.  If the thread's 5013 call lands FIRST, main's
later setresuid(5012,5012,5012) must EPERM (5012 not in {5013}) and main
ignores the return value — the whole process (including unsafecode's
overflow) would run at euid 5013 with full read on /etc/vortex_pass/vortex13.
So the race IS the privilege; no W1/W2/W3 chain is needed if it can be won.

## Measured (2026-11-17, with tracers — superseded, see below)

- 85/85 natural runs: the process ends at Uid 5012 (sleep-payload keeps main
  alive; /proc/pid/status read).  The thread NEVER wins.
- Timestamped strace: only main's setresuid appears; the thread exits without
  calling setresuid at all (it is still in glibc's thread startup when main
  has already finished fix_perms and unsafecode).
- Why: main's path after pthread_create is 2 PLT calls + fix_perms (~2us).
  The thread must first be created by the kernel (clone, TLS setup, ~10us).
  The window is not close; it is structurally lost.

## Saved-set-uid regain attempt (2026-11-17)

The unprivileged setresuid rule allows e=saved-set-uid.  On the real binary
the saved uid is rewritten: main's setresuid(5012,5012,5012) sets
r=e=s=5012 (/proc/pid/status Uid line while the sleep-payload keeps the
process alive: 5012 5012 5012 5012).  No 5013 remains anywhere in the
credentials after main's fix_perms, so the regain route is dead.

## gdb control attempt (2026-11-17) — CORRECTED (2026-11-18): a ptrace artifact

The gdb measurement "Uid 5012 before any program code" is EXPECTED under
ptrace: the kernel ignores setuid on exec when the execing thread is traced
(Linux-kernel mailing list, 2003 — see HINTS.md Sources).  It proves nothing
about the lab.  Untraced evidence below overturns it.

## Untraced evidence (2026-11-18) — the race is real, and it was WON

- A tight task-level poller (grep -h Uid /proc/[0-9]*/task/*/status in a
  loop from the same ssh session, NO tracer attached) caught the exec-time
  state: Uid: 5013 5013 5013 5013 in 3/3 runs.  The lab HONOURS setuid on
  exec; the gdb finding was the ptrace artifact HINTS.md predicted.
- The same poller never sees 5013 after the first instants: main's
  fix_perms lands within the first poll window, so the transient is narrow.
- The parked-process Uid reads (with the W1 write in place) showed 5012:
  in those runs the thread's fix_perms ran after main's — the race was
  lost, not absent.

## Final state (2026-11-18): SOLVED

The single 4-byte GOT write of HINTS.md Hint 2 works: from main's overflow,
one ROP patches printf@GOT (0x804c004) <- system@libc (0xf7dc0ce0, base
0xf7d6d000 leaked live by the parking-loop trick), then returns main into
safecode's loop head (0x8049260) so the process never exits.  The thread's
loop calls the patched printf once a second, forever: system("%d\n") with
the thread's own format-string argument.  An executable named '%d\n' on
PATH (the planted script copies /etc/vortex_pass/vortex13 to a readable
file) is the delivery mechanism.  Retries: the script ran at euid 5012 on
the first iterations (real shell errors "Permission denied" printed live)
and succeeded on a later iteration with euid 5013 — the thread's own
fix_perms(setresuid 5013) won the process-wide race by then.  Password
6iyARs3cY read from the dropped file and verified by logging in as
vortex13 (uid=5013, cat matches).  Recording: recordings/vortex/L12.cast.
