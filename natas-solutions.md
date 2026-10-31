# OverTheWire Natas — Solutions

Every level solved live against `*.natas.labs.overthewire.org` in this run. Natas levels are
web challenges behind HTTP Basic auth: each level's password is the credential for the next
(`natas<n>` / password). For each level: the goal, the technique and why it works, the exact
commands (curl/HTTP requests), and how the password was verified. Recordings are in
`recordings/natas/L<n>.cast`.

Verification rule used throughout: a password is accepted only if a request to
`natas<next>.natas.labs.overthewire.org` with it returns that level's page (HTTP 200).
---
## Level 0 → natas1
- **Account:** `natas0`, password `natas0` (given by the game).
- **Goal:** The password for natas1 is somewhere on the level-0 page.
- **Technique and why it works:** HTTP Basic auth protects the page; the game hands us natas0's credential. The password is not in the visible body but in an HTML comment: `<!--The password for natas1 is ... -->`. Comments are sent to the browser like any other markup, so fetching the raw page (rather than viewing rendered text) exposes them. `curl -u user:pass` sends the Basic auth header and prints the raw response; `grep` picks out the comment line.
- **Commands:**
  ```
  curl -s -u natas0:natas0 http://natas0.natas.labs.overthewire.org/ | grep "natas1 is"
  ```
- **Password for natas1:** `scfWG6qNEIdzqVyfRwEGXyNUfFZkZeQ7`
- **Verification:** fetched `http://natas1.natas.labs.overthewire.org/` with `natas1:<password>` and got the level-1 page (HTTP 200 with natas1 content), which also displays the same password in its wechall info.
- **Recording:** `recordings/natas/L0.cast`

## Level 1 → natas2
- **Account:** `natas1`.
- **Goal:** The password for natas2 is on the level-1 page, but right-clicking is blocked by the page's `oncontextmenu` handler.
- **Technique and why it works:** The right-click block is a client-side JavaScript attribute on `<body>` — it only affects a browser's context menu, not the data. The password is in an HTML comment (`<!--The password for natas2 is ... -->`), and comments are part of the raw response, so fetching the page with curl and grepping the comment line retrieves it without needing a browser or defeating any server-side control.
- **Commands:**
  ```
  curl -s -u natas1:<pw> http://natas1.natas.labs.overthewire.org/ | grep "natas2 is"
  ```
- **Password for natas2:** `vsDOxoXyq3wckCP1ZmTZ71ngIA606odB`
- **Verification:** fetched `http://natas2.natas.labs.overthewire.org/` with `natas2:<password>` → HTTP 200 with the level-2 page.
- **Recording:** `recordings/natas/L1.cast`

