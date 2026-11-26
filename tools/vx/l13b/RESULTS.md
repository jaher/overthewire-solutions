# Vortex L13 attempt 7 (2026-11-26) — fresh measurements, block PERSISTS

Host: vortex.labs.overthewire.org:2228, vortex13 / 6iyARs3cY (still valid).
- uname -r: 7.0.0-1014-aws (#14-Ubuntu SMP PREEMPT Thu Sep 17 19:08:36 UTC 2026, gibson-0) — UNCHANGED, >= 5.18.
- /vortex/vortex13 md5 5c9efbdf32e1d3473cb75511ccbf8fbd — UNCHANGED. -r-sr-x--- vortex14:vortex13.
- glibc: Ubuntu GLIBC 2.43-2ubuntu2.4 (ldd 2.43).

argc probe (printargc via raw-syscall execve/execveat, all built fresh in /tmp/vx13b on the lab):
| exec shape                          | reported argc |
|-------------------------------------|---------------|
| execve argv={NULL}                  | 1             |
| execve argv=NULL (no vector)        | 1             |
| execve argv={"",NULL}               | 1             |
| execveat(AT_EMPTY_PATH) {NULL}      | 1             |
| execveat(AT_EMPTY_PATH) {NULL,NULL} | 1             |

The 5.18+ kernel forces a single empty string in every empty/NULL-argv exec; argc==0 is unreachable.

Real binary under empty-argv exec (strace trreal.txt):
execve("/vortex/vortex13", [], /* 0 vars */) = 0 -> exit_group(1), read(0) count = 0.
main's argc gate exits before vuln(); the rk700/l3ouu4n9 technique stays gated behind argc==0.

Directive step (2) build NOT attempted — gate condition unmet. L13 stays blocked pending a
lab-host kernel change. (Attempt 7; attempts 1-6 closed every route class 2026-11-19..22.)
