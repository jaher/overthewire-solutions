# Vortex L9 — solution notes (solved 2026-11-16)

## The level: the BlackBox

The official level page (overthewire.org/wargames/vortex/vortex9.html)
is titled **"BlackBox"** and says only: *"There is no information
available for this level. Login to vortex.labs.overthewire.org and
check it out."*  No hints, no source, no description.

## Measured live (the full discovery arc)

- **The level-9 binary is missing.**  Every other level N has
  `/vortex/vortexN` (mode 4550, owner vortex(N+1), group vortexN — the
  current level's user runs it).  Level 9's binary does not exist:
  `stat /vortex/vortex9` → `No such file or directory`.  The listing
  jumps from `vortex8` (4550 vortex9:vortex8) to `vortex10`
  (4550 vortex11:vortex10).
- **The next binary is unreachable from vortex9.**  `/vortex/vortex10`
  is `4550 vortex11:vortex10`: only euid=vortex11 or gid=vortex10 can
  read/execute it.  vortex9 has gid 5009 only (`groups` → `vortex9`),
  `setgid(5010)` is refused (EPERM), `/etc/security/group.conf` has no
  active pam_group rules, the sshd PAM chain has no pam_group, and
  `vortex10:x:5010:` has no members.  `/etc/vortex_pass/vortex10` is
  `400 vortex10:vortex10` — needs euid 5010.  Circular: no route to run
  the level-10 binary from vortex9.
- **The password arrives by mail.**  `/var/mail/vortex9` — owned by
  vortex9, mode 640 — contains the 9-char password in plain text:
  `95KsP1i3K`.

## Verification

- `cat /var/mail/vortex9` → `95KsP1i3K`.
- Login as vortex10 with `95KsP1i3K` verified (`uid=5010(vortex10)`,
  `cat /etc/vortex_pass/vortex10` matches).

## Password for vortex10

`95KsP1i3K`

## Files

- No driver or exploit source is needed — the level is solved by
  reading `/var/mail/vortex9` as vortex9.
- The recording: `recordings/vortex/L9.cast`.
