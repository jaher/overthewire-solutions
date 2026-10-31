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

## Level 1 → narnia2
- **Account:** `narnia1`.
- **Goal:** The program takes the environment variable `EGG`, casts it to a function pointer, and calls it: `ret = (int (*)())getenv("EGG"); ret();`. Put shellcode there.
- **Technique and why it works:** Any string in the environment can be executed if we place valid machine code in it. We set `EGG` to a NOP sled followed by shellcode. The binary is setuid narnia2, so at the call its effective UID is narnia2. Two details matter: (1) the shellcode must first call `setreuid(geteuid(), geteuid())` — otherwise `execve("/bin/sh")` drops the effective UID back to narnia1 (the binary itself does exactly this); (2) the environment must be passed as *bytes* (`os.execve` with a bytes dict) because Python's `os.environ` UTF-8-encodes `\x90` into `\xc2\x90`, corrupting the code. The shellcode: `geteuid` (201), `setreuid(ebx,ebx)` (70), then `execve("/bin/sh")` (11).
- **Commands:**
  ```
  ssh narnia1@narnia.labs.overthewire.org -p 2226
  # set EGG to NOP*200 + [geteuid; setreuid(euid,euid); execve("/bin/sh")] and exec the binary
  id                                  # uid=14002(narnia2)
  cat /etc/narnia_pass/narnia2
  ```
- **Password for narnia2:** `0h8Tj5fxbv`
- **Verification:** logged in as `narnia2` with this password.
- **Recording:** `recordings/narnia/L1.cast`

