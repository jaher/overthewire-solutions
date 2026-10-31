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

## Level 2 → narnia3
- **Account:** `narnia2`.
- **Goal:** `main` does `char buf[128]; strcpy(buf, argv[1]);` — an unbounded copy into a 128-byte stack buffer.
- **Technique and why it works:** `strcpy` copies until the NUL, so an argv longer than 128 bytes overwrites the saved frame pointer (offset 128) and the return address (offset 132). ASLR is off and the stack is executable, so we put NOP sled + shellcode inside `argv[1]` and return into the sled. The shellcode calls `setreuid(geteuid(), geteuid())` first (the binary is setuid narnia3, so euid is narnia3; without it `execve("/bin/sh")` would drop back to narnia2) and then `execve("/bin/sh")`. Because the environment shifts the stack, the exploit sweeps candidate return addresses, detecting success by a "PWN!" marker the shellcode writes before spawning the shell, then re-execs with the found address.
- **Commands:**
  ```
  ssh narnia2@narnia.labs.overthewire.org -p 2226
  # run the python exploit (base64-transferred to /tmp/e_narnia2.py):
  #   payload = NOP*87 + shellcode + 'B'*4 + <ret addr>;  sweep 0xffffd000..0xffffe800
  id                                  # uid=14003(narnia3)
  cat /etc/narnia_pass/narnia3
  ```
- **Password for narnia3:** `F5AYQwE8PA`
- **Verification:** logged in as `narnia3` with this password.
- **Recording:** `recordings/narnia/L2.cast`

## Level 3 → narnia4
- **Account:** `narnia3`.
- **Goal:** `main` has `char ifile[32]; char ofile[16] = "/dev/null";` then `strcpy(ifile, argv[1])`, opens `ofile` read-write and `ifile` read-only, and copies 31 bytes between them.
- **Technique and why it works:** `strcpy` into the 32-byte `ifile` overflows into the adjacent `ofile` (which sits just above it on the stack, at `ebp-0x18` vs `ebp-0x38`). If `argv[1]` is a path whose first 32 bytes form a real directory prefix and whose remaining bytes are a writable path, then: `ifile` is truncated to those first 32 bytes, while `ofile` becomes the tail. We use `/tmp/` + 27 `A`s + `/tmp/out3` (41 chars): bytes 1–32 are `/tmp/AAAAAAAAAAAAAAAAAAAAAAAAAAA` and bytes 33+ are `/tmp/out3`. That directory holds a symlink `out3 -> /etc/narnia_pass/narnia4`, and `/tmp/out3` is pre-created writable so `open(ofile, O_RDWR)` succeeds. The setuid program then reads the password (via the symlink) and writes it to `/tmp/out3`, which we can read.
- **Commands:**
  ```
  ssh narnia3@narnia.labs.overthewire.org -p 2226
  D=$(python3 -c 'print("A"*27)')
  mkdir -p "/tmp/$D/tmp"
  ln -sf /etc/narnia_pass/narnia4 "/tmp/$D/tmp/out3"
  touch /tmp/out3; chmod 666 /tmp/out3
  /narnia/narnia3 "/tmp/$D/tmp/out3"
  cat /tmp/out3
  ```
- **Password for narnia4:** `CyWyf6uGWQ`
- **Verification:** logged in as `narnia4` with this password.
- **Recording:** `recordings/narnia/L3.cast`

