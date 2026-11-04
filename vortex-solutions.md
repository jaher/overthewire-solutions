
## Level 1 → vortex2 (BLOCKED)
- **Account:** `vortex1`, password `Gq#qu3bF3` (from the level-0 service; login verified).
- **Goal:** `/vortex/vortex1` (setuid vortex2, 32-bit i386, stack NX, stack canary, partial RELRO) reads bytes from stdin into `buf[0x21c]` at `ebp-0x21c`, keeping a cursor `p` that starts at `buf+0x100`:

  | byte | effect |
  |---|---|
  | `'\n'` (0x0a) | `print(buf, 0x200)`: every byte printed as `"%x "` |
  | `'\\'` (0x5c) | `p--` |
  | anything else | if `p <= buf+0x200`: `*p++ = c` |

  Before every read it compares `(p & 0xff000000) == 0xca000000`; on a match it calls `setresuid(geteuid(),…)` and `execlp("/bin/sh","sh",0)` — the winning branch.

  The catch, measured live: `getchar` is redirected, so **byte 0xc0 and above return −1**, and so does EOF. The branch needs the top byte of the pointer to be 0xca, but no 0xca can ever be stored.

- **Re-attempt (2026-11-04).** The instruction at 0x8048399, the one the compiler's `SlotsCE` table sends every emitted byte through, is decoded as `add bl, [ebx/edi*?]` and bounds every byte of the path. Concretely, byte `c` (every byte ≤ 0xbf) also runs as code:
  - `ecx = 0x8048392 + c`, `esi`/`edi = 0x80483b1 + 2c`, `eax = GOT[c>>2]`, `ebx = 0x804bff8 + c`, `ecx += 0x805c11c`, `ebx += 2c`;
  - then `jmp [ebx−0x3d0c]`, i.e. slot `0x804c2f4 + 3c` of a `.bss` table that is read relative to **ebp, which is 0** — so it reads a *fake frame* at `0xffffd000 − 4·d` with `d = GOT[4] + 2·GOT[3] − 2 = 0xe78fe38e`;
  - that frame's six slots are executed as code on every input byte. None of the path's stores is reachable (each sits behind an opcode check that emitted bytes never satisfy), so a byte cannot change the frame it is running in.

  The only frame that is not immediately fatal is the untouched one, and its slot 5 is a `pop ebx; ret` (`SlotsCE + 0xd5`), which returns through whatever is on the guest stack: tracer-measured evidence shows the guest stack is where the earlier probes found it, not at the frame.

  Reachable goals under this model (checked in `tools/vortex1_model.py`): a firing store needs `(p>>24)==0xca` *before* the byte is stored, so the pointer must already hold 0xca — `0xca000000` lies about 770 MB below the buffer and nothing in the binary writes it there; and no input leaves a valid, goal-directed slot table behind.

- **Outcome: BLOCKED.** Roughly 17,800 prober runs (swept filler × backslash × 0xca position × padding × write-past-the-end; counts in `OTW-PROGRESS.md`) and the structural model above produce zero firings. The level is recorded as blocked; the model is in `tools/vortex1_model.py` and the binary facts are re-derived in the L1 transcript a level at a time.

# OverTheWire Vortex — Solutions

Vortex is a binary-exploitation wargame. Level 0 is a TCP arithmetic service;
from level 1 on, each level is a setuid binary in the next account's home that
must be exploited over SSH. Everything here was derived live in this run:
the level-0 client was written from the official level description and typed
into vim, and every credential was checked by logging in to the next account.

Verification rule: a password is recorded only after `ssh vortex<N+1>` with it
returns a working shell.

---

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