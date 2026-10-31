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

## Level 2 → natas3
- **Account:** `natas2`.
- **Goal:** The page only shows a 1-pixel image; the password is elsewhere on the site.
- **Technique and why it works:** The `<img src="files/pixel.png">` reveals a `files/` directory. The web server has directory indexing enabled for that directory, so requesting `files/` returns an Apache index listing, which shows `users.txt` next to `pixel.png`. That file is a plain credentials list and includes the line `natas3:<password>`. The bug is a combination of an unlinked-but-guessable directory and an open index, not a code flaw.
- **Commands:**
  ```
  curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/ | grep img
  curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/files/
  curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/files/users.txt
  ```
- **Password for natas3:** `K30JrSRHzjxq3paUQuwozY4MNvmNFyhI`
- **Verification:** fetched `http://natas3.natas.labs.overthewire.org/` with `natas3:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L2.cast`

## Level 3 → natas4
- **Account:** `natas3`.
- **Goal:** The page says "There is nothing on this page" and the comment says not even Google will find it. Find the password for natas4.
- **Technique and why it works:** The hint points at search-engine indexing, so we read `robots.txt`, which lists `Disallow: /s3cr3t/`. robots.txt is a public file that *reveals* paths rather than hiding them; it only asks well-behaved crawlers to stay out. That directory has Apache directory indexing enabled, so `s3cr3t/` lists `users.txt`, which contains `natas4:<password>`.
- **Commands:**
  ```
  curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/robots.txt
  curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/s3cr3t/
  curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/s3cr3t/users.txt
  ```
- **Password for natas4:** `JDrPnuZAKyl6MkiqQGFIddrqpvgOASth`
- **Verification:** `http://natas4.natas.labs.overthewire.org/` with `natas4:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L3.cast`

## Level 4 → natas5
- **Account:** `natas4`.
- **Goal:** The page refuses access unless you arrive from `http://natas5.natas.labs.overthewire.org/`.
- **Technique and why it works:** The check is on the HTTP `Referer` header, which the *client* supplies. It is not a security boundary — it is trivially spoofed with `curl -H 'Referer: ...'`. We send the header claiming we came from natas5, and the server grants access and prints natas5's password. The lesson: client-controlled headers cannot be trusted for access control.
- **Commands:**
  ```
  curl -s -u natas4:<pw> -H 'Referer: http://natas5.natas.labs.overthewire.org/' http://natas4.natas.labs.overthewire.org/
  ```
- **Password for natas5:** `e4z2Noy3oqwPJUWzJH0dseN67Cn1sy2M`
- **Verification:** `http://natas5.natas.labs.overthewire.org/` with `natas5:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L4.cast`

