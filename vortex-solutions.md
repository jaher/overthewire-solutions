
## Level 2 → vortex3 (open)
- **Where it comes from:** this level is `0xbadc0ded.org` challenge #02 (2003-07-08, Joel Eriksson), the same origin as L3.
- **The shipped source** (overthewire.org/wargames/vortex/vortex2.c):
  ```c
  int main(int argc, char **argv) {
      char *args[] = { "/bin/tar", "cf", "/tmp/ownership.$$.tar", argv[1], argv[2], argv[3] };
      execv(args[0], args);
  }
  ```
  A tar **argument-injection** wrapper: everything after `tar cf <fixed archive>` would come from our arguments.
- **What the live binary really does** (measured as vortex2, 32-bit i386 build):
  - 0 arguments: `execv` fails and the program exits 0 silently.
  - **2 arguments:** the real tar runs as `tar cf /tmp/ownership.$$.tar <arg1> <arg2>`. I could not reconcile this with the three-slot source; a simulator of the source would reach the `argv[3]` slot at argc=2, and the shipped 32-bit build shows 6 pointer slots. That is recorded as measured, with the cause unknown.
  - **3 or more:** every call fails on argument 3 with EFAULT (strace) and the program exits 0. Launching it through `/lib/ld-linux.so.2` (dropping setuid) makes no difference, so these failures are in the wrapper, not in privileges.
- **Routes tried live, none fired:**
  - Published `--checkpoint=1 --checkpoint-action=exec=…` form, and variations (extra arguments, split flag/value, both spellings, both placements, `-T -`, action on stdin, `env -i`).
  - `-T /vortex/vortex2`, `--files-from …`: tar reads its file list as data only, so nothing is ever executed.
  - `-T '--checkpoint=1 --checkpoint-action=…'`: that becomes one filename, "Cannot stat".
  - `--use-compress-program=/vortex/vortex2`, `-I`, `--owner`: no file operand remains, so tar refuses to create an empty archive.
  - `TAR_OPTIONS=…`: the wrapper passes the environment to tar, but this tar build rejects any `TAR_OPTIONS` value.
- **Why the two-argument form can't carry the attack:** tar options only exist before the file list, and the fixed archive name takes the `f` slot. Our two arguments therefore sit after the list has started, where tar treats them as names. A name is never executed.
- **Not marked blocked** (user decision). Transcript of all of the above in `games/vortex.json` L2.

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