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

