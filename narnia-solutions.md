# OverTheWire Narnia — Solutions

Live solves against `narnia.labs.overthewire.org:2226` in this run. Narnia is about
buffer overflows and shellcode; sources are in `/narnia/`. For each level: goal,
technique and why it works, exact commands, verification. Recordings in
`recordings/narnia/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.
---
## Level 0 → narnia1
- **Account:** `narnia0`, password `narnia0` (given by the game).
- **Goal:** The program initialises `long val = 0x41414141` and reads up to 24 characters into `char buf[20]` with `scanf("%24s")`; if `val` becomes `0xdeadbeef` it `setreuid`s to narnia1 and runs `/bin/sh`.
- **Technique and why it works:** `scanf("%24s")` writes up to 24 bytes into a 20-byte buffer, so bytes 21–24 overwrite the adjacent `long val` (stack layout places `val` immediately after `buf`). Sending 20 filler bytes plus the little-endian encoding of `0xdeadbeef` (`\xef\xbe\xad\xde`) makes the comparison true, and the program hands us a shell as narnia1. The payload must be raw bytes (not the literal text), so it is written with `printf`/Python and piped or typed over a PTY.
- **Commands:**
  ```
  ssh narnia0@narnia.labs.overthewire.org -p 2226
  /narnia/narnia0
  # at the prompt send: 20 'A' bytes followed by \xef\xbe\xad\xde
  # then in the shell it spawns:
  id                                   # uid=14001(narnia1)
  cat /etc/narnia_pass/narnia1
  ```
- **Password for narnia1:** `O8dJypubLr`
- **Verification:** logged in as `narnia1` with this password.
- **Recording:** `recordings/narnia/L0.cast`

