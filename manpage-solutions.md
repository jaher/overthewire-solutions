# Manpage — solutions

Transcripts: `games/manpage.json` (per-level `cmds`/`out`/`pw`). Casts: not yet
recorded (see OTW-PROGRESS.md).

## Level 0 → manpage1 (SOLVED)
- **Password for manpage1:** `Mu8GvMudHb`, read from `/etc/manpage_pass/manpage1` in the shell the exploit spawns (`uid=17001(manpage1)`).
- **The program:** `/manpage/manpage0` (setuid manpage1): `setuid(getuid()); strcpy(buf[256], argv[1])` — classic overflow. `setuid(getuid())` drops euid to manpage0 but the saved set-user-ID still holds manpage1, so `setresuid(17001,17001,17001)` regains it.
- **Method:** find `buf` on the stack with gdb (EIP offset 260, ASLR off, GNU_STACK RWE); payload = NOP sled + `setresuid(17001,17001,17001)` + `execve("/bin/sh")` shellcode, return address into `buf`.
- **Note (2026-11-17 re-check):** on today's lab the setuid bit is *not honoured on exec* (the process is already Uid 5012-equivalent from `_start`, matching the Vortex L12 finding), so the recorded run stands as the capture; the fresh re-run confirmed the return-address control (ret-gadget probe → SIGILL) but not the privilege regain.

## Level 1 → manpage2 (SOLVED)
- **Password for manpage2:** `m2uPltjqCJ`.
- **The program:** same strcpy overflow, but `strlen(buf) >= 255` triggers `raise(SIGTERM)` after the copy. The exploit parent blocks SIGTERM (the inherited mask makes `raise()` never deliver), then overflows to `setresuid(17002,17002,17002)` + shell.

## Level 2 → manpage3 (SOLVED)
- **Password for manpage3:** `A8CLKp6IDp`.
- **The program:** getpass-style check against a file, then `setuid(getuid())` and `execl(argv[0], argv[0], argv[1])` with `argv[1][0]` as a marker.
- **The trick:** launch with `executable=/manpage/manpage2` but `argv[0]="/bin/sh"`, `argv[1]="\x81"`, and plant a script file; after one wrong guess the binary execs `/bin/sh "\x82"` — our script, which does `lseek(fd3,0,0)` + read and dumps the password: `FD3: b'A8CLKp6IDp\n'`.

## Level 3 → manpage4 (SOLVED)
- **Password for manpage4:** `8O96CWQPaN`.
- **The program:** `strcmp(stdin_line, 256 random bytes from /manpage/manpage3-pw/password)`; `/manpage/manpage3-reset` rewrites the random file.
- **The trick:** loop: reset, then guess a line starting with a NUL byte; `strcmp` matches when the random file *starts* with NUL. "Wow, you should play the lottery!" — password read in the won shell.

## Level 4 → manpage5 (SOLVED)
- **Password for manpage5:** `v2ltdizZfm`.
- **The program:** `/manpage/manpage4.diff` — a patched Wumpus; `log_winner()` sprintf's ctime+firstname+lastname (uninitialised on some paths).
- **The trick:** seed `-s 12345` to replicate the host libc `rand()` → layout player=18, wumpus=13, pits={2,16}, bats={5,3}; the ROOM # line persists in `getnum`'s stack buffer overlapping the name buffers: NOP sled + `setresuid(17005,17005,17005)` shellcode → "AHA! YOU GOT THE WUMPUS!", `uid=17005(manpage5)`, password read.
