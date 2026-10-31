# OverTheWire Bandit — Solutions

Every level below was solved live against `bandit.labs.overthewire.org:2220` in this run.
For each level: what the level asks, the technique and why it works, the exact commands,
and how the result was verified. The recorded terminal session for each level is under
`recordings/bandit/L<n>.cast` (linked in `recordings/index.html`).

Each password was verified by logging in to the next level with it (or, for key-based
levels, by using the returned key to open the next account) before being written down.

Note on the lab: connecting from `localhost` on the game server is blocked by OTW, so
levels that are "ssh to the next account from inside" (13, 16) are solved by bringing
the key/credential to this client machine and connecting directly to the public host.

---
## Level 0 → bandit1
- **Account:** `bandit0`, password `bandit0` (given by the game).
- **Goal:** Read the password for bandit1, stored in the home directory's `readme`.
- **Technique and why it works:** The level is a plain file read. `cat` writes the file's bytes to stdout; the file is group-readable by `bandit0` (`-rw-r----- bandit1 bandit0`), so no privilege trick is needed — the password file is simply handed to this level's account.
- **Commands:**
  ```
  ssh bandit0@bandit.labs.overthewire.org -p 2220
  cat ~/readme
  ```
- **Password for bandit1:** `6y2kwnwK6grgvwvpvLaa2T1cpFEKOhNR`
- **Verification:** logged in as `bandit1` with this password (`whoami` → `bandit1`).
- **Recording:** `recordings/bandit/L0.cast`

## Level 1 → bandit2
- **Account:** `bandit1`.
- **Goal:** Read the password for bandit2, which is stored in a file literally named `-`.
- **Technique and why it works:** A bare `-` is not treated as a filename by most GNU tools: `cat -` means "read standard input". Prefixing the path with `./` makes it an explicit relative path, so it is no longer an option-looking argument; `cat -- -` is an equivalent alternative (`--` ends option parsing).
- **Commands:**
  ```
  ls -la          # shows the file named "-"
  cat ./-
  ```
- **Password for bandit2:** `PK8fYLZg2hnHSz83plBL1iEPKdD3QToB`
- **Verification:** logged in as `bandit2` with this password.
- **Recording:** `recordings/bandit/L1.cast`

## Level 2 → bandit3
- **Account:** `bandit2`.
- **Goal:** Read the password in a file whose name contains spaces: `--spaces in this filename--`.
- **Technique and why it works:** The shell splits unquoted whitespace into separate arguments, so the name must be kept as one word. Either quoting (`cat "./--spaces in this filename--"`) or backslash-escaping each space (`cat ./--spaces\ in\ this\ filename--`) passes a single argument; `./` also stops the leading dashes being parsed as options.
- **Commands:**
  ```
  ls -la
  cat ./--spaces\ in\ this\ filename--
  ```
- **Password for bandit3:** `7ZZ2LFrykP2zEyvBl4m3clcL7tGYJPME`
- **Verification:** logged in as `bandit3` with this password.
- **Recording:** `recordings/bandit/L2.cast`

## Level 3 → bandit4
- **Account:** `bandit3`.
- **Goal:** The password is in a hidden file inside the `inhere` directory.
- **Technique and why it works:** `ls` hides dot-files by default; `ls -la` lists all entries including names beginning with `.`, which reveals `...Hiding-From-You`. It is a normal (non-dot) file here, but the directory listing is what exposes the name.
- **Commands:**
  ```
  ls -la inhere/
  cat inhere/...Hiding-From-You
  ```
- **Password for bandit4:** `xzTXq1rDJQVVAzdv5cHq1TQytTWufAMq`
- **Verification:** logged in as `bandit4` with this password.
- **Recording:** `recordings/bandit/L3.cast`

## Level 4 → bandit5
- **Account:** `bandit4`.
- **Goal:** In `inhere` there are ten files; find the one that is human-readable.
- **Technique and why it works:** `file` classifies content from magic bytes rather than names. Nine files are binary `data`; only `-file07` is reported as `ASCII text`, so it is the human-readable one. Note the leading dash again, so the path is passed as `inhere/-file07` (the directory prefix removes the option ambiguity).
- **Commands:**
  ```
  file inhere/* 2>/dev/null
  cat inhere/-file07
  ```
- **Password for bandit5:** `6C7h9GD8M6ai5nr7wo1RonrzFjj9yIrG`
- **Verification:** logged in as `bandit5` with this password.
- **Recording:** `recordings/bandit/L4.cast`

## Level 5 → bandit6
- **Account:** `bandit5`.
- **Goal:** Find a file under `inhere` that is human-readable, 1033 bytes, and not executable.
- **Technique and why it works:** `find` can select by exact byte size (`-size 1033c`), type (`-type f`), and permission (`! -executable`). Combining all three predicates narrows the tree to a single path, `inhere/maybehere07/.file2`.
- **Commands:**
  ```
  find inhere -type f -size 1033c ! -executable
  cat inhere/maybehere07/.file2
  ```
- **Password for bandit6:** `pXa26xhMWaC2SvDotA4r9EgZkulOeSBW`
- **Verification:** logged in as `bandit6` with this password.
- **Recording:** `recordings/bandit/L5.cast`

## Level 6 → bandit7
- **Account:** `bandit6`.
- **Goal:** Find a file anywhere on the filesystem owned by user `bandit7`, group `bandit6`, exactly 33 bytes.
- **Technique and why it works:** `find /` walks the whole tree; `-user`, `-group` and `-size 33c` are exact-match predicates. `2>/dev/null` discards the permission errors from directories `bandit6` cannot read, leaving the single hit `/var/lib/dpkg/info/bandit7.password`.
- **Commands:**
  ```
  find / -user bandit7 -group bandit6 -size 33c 2>/dev/null
  cat /var/lib/dpkg/info/bandit7.password
  ```
- **Password for bandit7:** `Bmnnvf82KzQlfxgAI2d1zYbr1u9pr3E3`
- **Verification:** logged in as `bandit7` with this password.
- **Recording:** `recordings/bandit/L6.cast`

## Level 7 → bandit8
- **Account:** `bandit7`.
- **Goal:** The password is on the line next to the word `millionth` in `data.txt`.
- **Technique and why it works:** `grep` prints the whole matching line; the data file is `word<TAB>value`, so the matching line contains the password after the tab.
- **Commands:**
  ```
  grep millionth data.txt
  ```
- **Password for bandit8:** `VR1ljMayciFxbnUokuQmJFw6QC9VKtub`
- **Verification:** logged in as `bandit8` with this password.
- **Recording:** `recordings/bandit/L7.cast`

## Level 8 → bandit9
- **Account:** `bandit8`.
- **Goal:** `data.txt` contains many repeated lines; exactly one line occurs only once — that line is the password.
- **Technique and why it works:** `uniq` only collapses adjacent duplicates, so the file is sorted first. `uniq -u` prints only lines that occur exactly once in the sorted input, which leaves the unique password line.
- **Commands:**
  ```
  sort data.txt | uniq -u
  ```
- **Password for bandit9:** `EjmOSvuAu7sGAHqHVcBDPirRe9T03kxl`
- **Verification:** logged in as `bandit9` with this password.
- **Recording:** `recordings/bandit/L8.cast`

## Level 9 → bandit10
- **Account:** `bandit9`.
- **Goal:** The password is stored in a binary file (`data.txt`) as human-readable text, preceded by several `=` characters.
- **Technique and why it works:** `strings` extracts printable runs from binary data; filtering with `grep "==="` keeps the marker lines. The last of them is `========== <password>`.
- **Commands:**
  ```
  strings data.txt | grep "==="
  ```
- **Password for bandit10:** `B0s2khmbT9u0geKuOoVGW3JZKhndE3BG`
- **Verification:** logged in as `bandit10` with this password.
- **Recording:** `recordings/bandit/L9.cast`

## Level 10 → bandit11
- **Account:** `bandit10`.
- **Goal:** `data.txt` contains base64-encoded data; the password is the decoded text.
- **Technique and why it works:** base64 is a reversible encoding of bytes into an ASCII alphabet. `base64 -d` decodes it back, yielding `The password is <pw>`.
- **Commands:**
  ```
  base64 -d data.txt
  ```
- **Password for bandit11:** `pYfOY6HwUsDj5rL9UvyhU7MCmv8vN5Ro`
- **Verification:** logged in as `bandit11` with this password.
- **Recording:** `recordings/bandit/L10.cast`

## Level 11 → bandit12
- **Account:** `bandit11`.
- **Goal:** The password in `data.txt` has been rotated 13 positions (ROT13).
- **Technique and why it works:** ROT13 is a Caesar shift by 13 over the 26-letter alphabet; it is its own inverse, so applying it to the ciphertext returns the plaintext. `tr` maps each character range: `A-Z` → `N-ZA-M` and `a-z` → `n-za-m`.
- **Commands:**
  ```
  cat data.txt | tr 'A-Za-z' 'N-ZA-Mn-za-m'
  ```
- **Password for bandit12:** `GROozWPO8QyN0mGrjUkID0WCYkZiQxrN`
- **Verification:** logged in as `bandit12` with this password.
- **Recording:** `recordings/bandit/L11.cast`

