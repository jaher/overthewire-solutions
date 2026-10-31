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

