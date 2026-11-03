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