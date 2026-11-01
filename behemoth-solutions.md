# OverTheWire Behemoth — Solutions

Live solves against `behemoth.labs.overthewire.org:2221` in this run. Behemoth is
a setuid binary-exploitation wargame; sources are not provided, so every level is
solved by reading the binaries (`strings`, `objdump`, `gdb`, `nm`, `readelf`).
For each level: goal, technique and why it works, exact commands, verification.
Recordings in `recordings/behemoth/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.
---
## Level 0 → behemoth1
- **Account:** `behemoth0`, password `behemoth0` (given by the game).
- **Goal:** `main` builds a secret on the stack, memfrobs it, reads up to 64
  characters into another stack buffer, and `strcmp`s the two. On a match it
  prints "Access granted..", does `setreuid(geteuid(),geteuid())` and runs
  `system("/bin/sh")`.
- **Technique and why it works:** the secret is stored in plain sight as
  immediates in the disassembly, but obfuscated with glibc's `memfrob`, which
  XORs every byte with 42 (`0x2A`). We read the three `movl` immediates that
  initialise the secret and XOR them with 42 to recover the plaintext password.
  Nothing has to be guessed or brute-forced: the comparison string is fully
  recoverable from the binary.

### Step-by-step discovery and crafting (what the recording shows)
1. **List the game and the binaries.** `ls -la /behemoth/` shows `behemoth0`
   is setuid `behemoth1`, and each later binary is setuid to the next user.
2. **Look at the strings.** `strings -a /behemoth/behemoth0` shows the program
   text plus three suspicious blobs — `OK^G`, `SYBE`, `X^Y` — and the symbol
   `memfrob`. Those are not random: they are ASCII XOR-ed with 42.
3. **Read the disassembly of `main`.**
   ```
   objdump -d --no-show-raw-insn /behemoth/behemoth0 | sed -n '/<main>:/,/strcmp/p'
   ```
   The secret is built from three immediates at `-0x55(%ebp)`:
   ```
   movl $0x475e4b4f,-0x55(%ebp)   # 4f 4b 5e 47  = "OK^G"
   movl $0x45425953,-0x51(%ebp)   # 53 59 42 45  = "SYBE"
   movl $0x00595e58,-0x4d(%ebp)   # 58 5e 59 00  = "X^Y\0"
   ```
   so the stored string is `OK^GSYBEX^Y` (little-endian byte order within each
   dword). Then the program calls `memfrob(secret, strlen(secret))` and
   `strcmp(secret, input)`.
4. **Decode the secret.** `memfrob` XORs each byte with 42:
   ```
   python3 -c 'print(bytes(c ^ 42 for c in bytes.fromhex("4f4b5e4753594245585e59")))'
   # b'eatmyshorts'
   ```
5. **Feed the password.** The binary reads our input with `scanf("%64s")` and,
   on success, runs `system("/bin/sh")`. Because the shell inherits the same
   stdin, we send the password first and then the commands after a short delay
   (so `scanf` does not consume them):
   ```
   { printf "eatmyshorts\n"; sleep 1; printf "id\ncat /etc/behemoth_pass/behemoth1\nexit\n"; } | /behemoth/behemoth0
   # Password: Access granted..
   # uid=13001(behemoth1) ...
   # paAotdjMCj
   ```
- **Password for behemoth1:** `paAotdjMCj`
- **Verification:** logged in as `behemoth1` with this password (`whoami` → `behemoth1`).
- **Recording:** `recordings/behemoth/L0.cast`
