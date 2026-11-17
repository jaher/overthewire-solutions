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
