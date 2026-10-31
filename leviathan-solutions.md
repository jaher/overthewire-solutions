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

