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

## Level 2 → leviathan3
- **Account:** `leviathan2`.
- **Goal:** The setuid binary `printfile` (owned by leviathan3) prints a file. Read leviathan3's password.
- **Technique and why it works:** `printfile` first calls `access()` on the path we give it — an access check performed with *our* real UID, so it only passes for files we can already read — and then builds a shell command `"/bin/cat %s"` with that path. Two bugs combine. First, `access()` and the later `cat` disagree about the path: we can make `access()` succeed on a path whose *prefix* is a symlink to the password file. We create `/tmp/l2/a` as a symlink to `/etc/leviathan_pass/leviathan3`, and a real, readable file named `/tmp/l2/a b` (with a space). `access("/tmp/l2/a b")` succeeds because that real file exists and we can read it. But `/bin/cat %s` is word-split by the shell, so cat receives two arguments: `/tmp/l2/a` (the symlink, now resolved with the setuid binary's privileges) and `b`. Cat prints the symlinked password file. The classic TOCTOU/argument-splitting flaw.
- **Commands:**
  ```
  ssh leviathan2@leviathan.labs.overthewire.org -p 2223
  rm -rf /tmp/l2; mkdir -p /tmp/l2
  ln -s /etc/leviathan_pass/leviathan3 /tmp/l2/a
  touch "/tmp/l2/a b"
  ./printfile "/tmp/l2/a b"
  ```
- **Password for leviathan3:** `PiEpxxknZH`
- **Verification:** logged in as `leviathan3` with this password.
- **Recording:** `recordings/leviathan/L2.cast`

## Level 3 → leviathan4
- **Account:** `leviathan3`.
- **Goal:** The setuid binary `level3` (owned by leviathan4) asks for a password; supply it to get leviathan4's password.
- **Technique and why it works:** `strings` shows the comparison target `snlprintf` and a `/bin/sh` string. Disassembly of `do_stuff` confirms the flow: `fgets` reads a line, `strcmp` compares it with `snlprintf`; on a match it prints a success line, calls `setreuid(geteuid(), geteuid())` to become leviathan4, and runs `system("/bin/sh")`. Entering `snlprintf` therefore drops us into a shell as leviathan4, from which we read `/etc/leviathan_pass/leviathan4`. This is the same hardcoded-password + setuid-shell pattern as level 1, but with a longer, non-dictionary password found by reading the binary.
- **Commands:**
  ```
  ssh leviathan3@leviathan.labs.overthewire.org -p 2223
  strings level3 | grep -E 'snlp|bin/sh'
  ./level3        # enter: snlprintf
  id              # uid=leviathan4
  cat /etc/leviathan_pass/leviathan4
  ```
- **Password for leviathan4:** `XIyBbRwAPt`
- **Verification:** logged in as `leviathan4` with this password.
- **Recording:** `recordings/leviathan/L3.cast`

## Level 4 → leviathan5
- **Account:** `leviathan4`.
- **Goal:** There is a setuid binary in the hidden `.trash` directory; run it to get leviathan5's password.
- **Technique and why it works:** `ls -la .trash` shows `bin`, mode `-r-sr-x---`, owned by leviathan5. Running it prints a sequence of 8-bit binary numbers separated by spaces, one per character of the password, ending with `00001010` (a newline). Converting each group of eight bits to its ASCII character reconstructs the password, `Bub9gZ3BGU`. No exploit is needed beyond decoding the binary's output format.
- **Commands:**
  ```
  ssh leviathan4@leviathan.labs.overthewire.org -p 2223
  ls -la .trash
  ./.trash/bin
  python3 -c "print(''.join(chr(int(b,2)) for b in '01000010 01110101 ...'.split()))"
  ```
- **Password for leviathan5:** `Bub9gZ3BGU`
- **Verification:** logged in as `leviathan5` with this password.
- **Recording:** `recordings/leviathan/L4.cast`

