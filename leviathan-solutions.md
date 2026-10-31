# OverTheWire Leviathan — Solutions

Live solves against `leviathan.labs.overthewire.org:2223` in this run. For each level:
goal, technique and why it works, exact commands, and verification. Recordings in
`recordings/leviathan/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.
---
## Level 0 → leviathan1
- **Account:** `leviathan0`, password `leviathan0` (given by the game).
- **Goal:** The password for leviathan1 is stored somewhere in leviathan0's home directory.
- **Technique and why it works:** `ls -la` shows a hidden `.backup` directory readable by group `leviathan0`. Its only file is `bookmarks.html`, a large Firefox bookmark export. Searching it for the next account name finds an entry whose URL text contains the password. The data is plain text in a backup that was never meant to be hidden from this account.
- **Commands:**
  ```
  ssh leviathan0@leviathan.labs.overthewire.org -p 2223     # password leviathan0
  ls -la .backup
  grep -i "leviathan1" .backup/bookmarks.html
  ```
- **Password for leviathan1:** `PiXaSWQqHq`
- **Verification:** logged in as `leviathan1` with this password (`whoami` → `leviathan1`).
- **Recording:** `recordings/leviathan/L0.cast`

## Level 1 → leviathan2
- **Account:** `leviathan1`.
- **Goal:** The home directory contains `check`, a setuid binary owned by leviathan2. Get leviathan2's password.
- **Technique and why it works:** `check` is a setuid-root-style helper: it is owned by `leviathan2` and has the setuid bit, so it runs with leviathan2's effective UID. The binary asks for a password and compares it; `strings` shows fragments `secr`, `love`, and the prompt. The accepted input is `sex` (the comparison is against that word). When the comparison succeeds the program calls `setreuid()` to switch to leviathan2 and `system("/bin/sh")`, dropping us into a shell as leviathan2. From that shell, `cat /etc/leviathan_pass/leviathan2` works. The level shows a hardcoded-password check plus a setuid shell as the escalation primitive.
- **Commands:**
  ```
  ssh leviathan1@leviathan.labs.overthewire.org -p 2223
  file check; strings check | grep -iE 'secr|love|password'
  ./check        # enter: sex
  id             # uid=leviathan2
  cat /etc/leviathan_pass/leviathan2
  ```
- **Password for leviathan2:** `ERJ9jTYWXE`
- **Verification:** logged in as `leviathan2` with this password.
- **Recording:** `recordings/leviathan/L1.cast`

