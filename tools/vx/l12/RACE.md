# Vortex L12: the privilege race, measured (2026-11-17)

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

## Measured

- 85/85 natural runs: the process ends at Uid 5012 (sleep-payload keeps main
  alive; /proc/pid/status read).  The thread NEVER wins.
- Timestamped strace: only main's setresuid appears; the thread exits without
  calling setresuid at all (it is still in glibc's thread startup when main
  has already finished fix_perms and unsafecode).
- Why: main's path after pthread_create is 2 PLT calls + fix_perms (~2us).
  The thread must first be created by the kernel (clone, TLS setup, ~10us).
  The window is not close; it is structurally lost.

## Consequence

The L8-style race (thread keeps euid=vortex9) does not exist here because
safecode CALLS fix_perms itself.  Every route that needs a privileged thread
is dead: the thread is always 5012 by the time it runs user code.

## Saved-set-uid regain attempt (2026-11-17)

The unprivileged setresuid rule allows e=saved-set-uid.  On the real binary
the saved uid is rewritten: main's setresuid(5012,5012,5012) sets
r=e=s=5012 (/proc/pid/status Uid line while the sleep-payload keeps the
process alive: 5012 5012 5012 5012).  No 5013 remains anywhere in the
credentials after main's fix_perms, so the regain route is dead.

## Final state (2026-11-17, fresh attempt)

- The race (thread wins 5013) is structurally lost: 85/85 natural runs end at
  Uid 5012; the timestamped strace shows the thread exits without ever
  calling setresuid.  main's path after pthread_create is ~2us of PLT calls;
  the thread needs ~10us of kernel thread startup first.
- The saved-set-uid regain fails: main's setresuid(5012,5012,5012) rewrites
  the saved uid too; no 5013 remains in r/e/s.
- main makes no file syscalls at all (pthread_create; getuid; getgid;
  fix_perms; unsafecode=strcpy; return 0), so nothing in the pre-drop window
  can be aimed at /etc/vortex_pass/vortex13.
- The overflow runs strictly after main's fix_perms (at euid 5012), so no
  ROP chain can reach a privileged state; mprotect is not imported and every
  useful syscall number has NUL bytes strcpy cannot carry (previous session).
- The password file is a single hard link (1), owner vortex13 mode 400, no
  NFS/alternate path.

Outcome: fresh attempt dead-ends with evidence.  Not solved; the standing
blocked note stays.
