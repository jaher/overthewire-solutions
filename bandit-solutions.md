# OverTheWire Bandit — Solutions

Every level below was solved live against `bandit.labs.overthewire.org:2220` in this run.
For each level: what the level asks, the technique and why it works, the exact commands,
and how the result was verified. The recorded terminal session for each level is under
`recordings/bandit/L<n>.cast` (linked in `recordings/index.html`).

Each password was verified by logging in to the next level with it (or, for key-based
levels, by using the returned key to open the next account) before being written down.

Note on the lab: connecting from `localhost` on the game server is blocked by OTW, so
levels that are "ssh to the next account from inside" (13, 16) are solved by bringing
the key/credential to this client machine and connecting directly to the public host.

---
## Level 0 → bandit1
- **Account:** `bandit0`, password `bandit0` (given by the game).
- **Goal:** Read the password for bandit1, stored in the home directory's `readme`.
- **Technique and why it works:** The level is a plain file read. `cat` writes the file's bytes to stdout; the file is group-readable by `bandit0` (`-rw-r----- bandit1 bandit0`), so no privilege trick is needed — the password file is simply handed to this level's account.
- **Commands:**
  ```
  ssh bandit0@bandit.labs.overthewire.org -p 2220
  cat ~/readme
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Log in as the first account.** `ssh bandit0@bandit.labs.overthewire.org -p 2220` (the password is `bandit0`, given by the game).
2. **Look at the home directory.** `ls -la` shows a single readable file, `readme`, owned by `bandit1:bandit0`.
3. **Read it.** `cat readme` prints the next password. Nothing to exploit: the file is handed to this level's account.
- **Password for bandit1:** `6y2kwnwK6grgvwvpvLaa2T1cpFEKOhNR`
- **Verification:** logged in as `bandit1` with this password (`whoami` → `bandit1`).
- **Recording:** `recordings/bandit/L0.cast`

## Level 1 → bandit2
- **Account:** `bandit1`.
- **Goal:** Read the password for bandit2, which is stored in a file literally named `-`.
- **Technique and why it works:** A bare `-` is not treated as a filename by most GNU tools: `cat -` means "read standard input". Prefixing the path with `./` makes it an explicit relative path, so it is no longer an option-looking argument; `cat -- -` is an equivalent alternative (`--` ends option parsing).
- **Commands:**
  ```
  ls -la          # shows the file named "-"
  cat ./-
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **List the directory.** `ls -la` reveals a file whose name is exactly `-`; the permissions line shows it is readable by `bandit1`'s group.
2. **Notice why the obvious command fails.** `cat -` would read *standard input*, because `-` is an option-like argument that GNU tools interpret specially. The `ls` output makes that trap visible.
3. **Give the shell an unambiguous path.** `cat ./-` forces the argument to be a path (it starts with `./`), so `cat` opens the file instead of stdin. (`cat -- -` works the same way: `--` ends option parsing.)
- **Password for bandit2:** `PK8fYLZg2hnHSz83plBL1iEPKdD3QToB`
- **Verification:** logged in as `bandit2` with this password.
- **Recording:** `recordings/bandit/L1.cast`

## Level 2 → bandit3
- **Account:** `bandit2`.
- **Goal:** Read the password in a file whose name contains spaces: `--spaces in this filename--`.
- **Technique and why it works:** The shell splits unquoted whitespace into separate arguments, so the name must be kept as one word. Either quoting (`cat "./--spaces in this filename--"`) or backslash-escaping each space (`cat ./--spaces\ in\ this\ filename--`) passes a single argument; `./` also stops the leading dashes being parsed as options.
- **Commands:**
  ```
  ls -la
  cat ./--spaces\ in\ this\ filename--
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **List the directory.** `ls -la` shows the file `--spaces in this filename--`. Two traps are visible: the name starts with `--`, and it contains spaces.
2. **Keep it one argument.** Unquoted spaces split into separate words, so the shell would pass `cat` four arguments. Backslash-escaping each space keeps it one word: `cat ./--spaces\ in\ this\ filename--`.
3. **Neutralise the leading dashes.** The `./` prefix (or `--` before the name) stops the string being read as an option.
- **Password for bandit3:** `7ZZ2LFrykP2zEyvBl4m3clcL7tGYJPME`
- **Verification:** logged in as `bandit3` with this password.
- **Recording:** `recordings/bandit/L2.cast`

## Level 3 → bandit4
- **Account:** `bandit3`.
- **Goal:** The password is in a hidden file inside the `inhere` directory.
- **Technique and why it works:** `ls` hides dot-files by default; `ls -la` lists all entries including names beginning with `.`, which reveals `...Hiding-From-You`. It is a normal (non-dot) file here, but the directory listing is what exposes the name.
- **Commands:**
  ```
  ls -la inhere/
  cat inhere/...Hiding-From-You
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Look in the directory.** `ls -la inhere/` lists every entry, including hidden ones. Plain `ls` would not show the dot-file.
2. **Spot the hidden file.** The listing shows `...Hiding-From-You`, a name built from dots so it blends into the `.` and `..` entries at a glance.
3. **Read it by its exact path.** `cat inhere/...Hiding-From-You` prints the password.
- **Password for bandit4:** `xzTXq1rDJQVVAzdv5cHq1TQytTWufAMq`
- **Verification:** logged in as `bandit4` with this password.
- **Recording:** `recordings/bandit/L3.cast`

## Level 4 → bandit5
- **Account:** `bandit4`.
- **Goal:** In `inhere` there are ten files; find the one that is human-readable.
- **Technique and why it works:** `file` classifies content from magic bytes rather than names. Nine files are binary `data`; only `-file07` is reported as `ASCII text`, so it is the human-readable one. Note the leading dash again, so the path is passed as `inhere/-file07` (the directory prefix removes the option ambiguity).
- **Commands:**
  ```
  file inhere/* 2>/dev/null
  cat inhere/-file07
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Inspect every candidate's type.** `file inhere/* 2>/dev/null` reports nine files as binary `data` and exactly one as `ASCII text`.
2. **Read the text one.** The hit is `inhere/-file07`; the leading dash is harmless here because the argument is a path (`inhere/-file07`), not a bare `-file07`.
3. **`cat inhere/-file07`** prints the password.
- **Password for bandit5:** `6C7h9GD8M6ai5nr7wo1RonrzFjj9yIrG`
- **Verification:** logged in as `bandit5` with this password.
- **Recording:** `recordings/bandit/L4.cast`

## Level 5 → bandit6
- **Account:** `bandit5`.
- **Goal:** Find a file under `inhere` that is human-readable, 1033 bytes, and not executable.
- **Technique and why it works:** `find` can select by exact byte size (`-size 1033c`), type (`-type f`), and permission (`! -executable`). Combining all three predicates narrows the tree to a single path, `inhere/maybehere07/.file2`.
- **Commands:**
  ```
  find inhere -type f -size 1033c ! -executable
  cat inhere/maybehere07/.file2
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Express the three conditions as `find` predicates.** Size is `-size 1033c` (bytes), type is `-type f`, and "not executable" is `! -executable`.
2. **Run them together.** `find inhere -type f -size 1033c ! -executable` returns exactly one path, `inhere/maybehere07/.file2`.
3. **Read it.** `cat inhere/maybehere07/.file2` prints the password.
- **Password for bandit6:** `pXa26xhMWaC2SvDotA4r9EgZkulOeSBW`
- **Verification:** logged in as `bandit6` with this password.
- **Recording:** `recordings/bandit/L5.cast`

## Level 6 → bandit7
- **Account:** `bandit6`.
- **Goal:** Find a file anywhere on the filesystem owned by user `bandit7`, group `bandit6`, exactly 33 bytes.
- **Technique and why it works:** `find /` walks the whole tree; `-user`, `-group` and `-size 33c` are exact-match predicates. `2>/dev/null` discards the permission errors from directories `bandit6` cannot read, leaving the single hit `/var/lib/dpkg/info/bandit7.password`.
- **Commands:**
  ```
  find / -user bandit7 -group bandit6 -size 33c 2>/dev/null
  cat /var/lib/dpkg/info/bandit7.password
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Search the whole filesystem.** `find / -user bandit7 -group bandit6 -size 33c 2>/dev/null` — the predicates are exact owner, exact group and exact byte size.
2. **Silence the noise.** `2>/dev/null` drops the "Permission denied" errors from directories bandit6 cannot read, so the output is a single path: `/var/lib/dpkg/info/bandit7.password`.
3. **Read it.** `cat /var/lib/dpkg/info/bandit7.password` prints the password.
- **Password for bandit7:** `Bmnnvf82KzQlfxgAI2d1zYbr1u9pr3E3`
- **Verification:** logged in as `bandit7` with this password.
- **Recording:** `recordings/bandit/L6.cast`

## Level 7 → bandit8
- **Account:** `bandit7`.
- **Goal:** The password is on the line next to the word `millionth` in `data.txt`.
- **Technique and why it works:** `grep` prints the whole matching line; the data file is `word<TAB>value`, so the matching line contains the password after the tab.
- **Commands:**
  ```
  grep millionth data.txt
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Search the data file for the marker word.** `grep millionth data.txt` prints the whole matching line.
2. **Read the value.** The file is `word<TAB>password`, so the password follows the tab on the same line.
- **Password for bandit8:** `VR1ljMayciFxbnUokuQmJFw6QC9VKtub`
- **Verification:** logged in as `bandit8` with this password.
- **Recording:** `recordings/bandit/L7.cast`

## Level 8 → bandit9
- **Account:** `bandit8`.
- **Goal:** `data.txt` contains many repeated lines; exactly one line occurs only once — that line is the password.
- **Technique and why it works:** `uniq` only collapses adjacent duplicates, so the file is sorted first. `uniq -u` prints only lines that occur exactly once in the sorted input, which leaves the unique password line.
- **Commands:**
  ```
  sort data.txt | uniq -u
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Sort first.** `uniq` only collapses *adjacent* duplicates, so `sort data.txt` groups equal lines together.
2. **Print only unique lines.** `sort data.txt | uniq -u` keeps the single line that occurs exactly once — the password.
- **Password for bandit9:** `EjmOSvuAu7sGAHqHVcBDPirRe9T03kxl`
- **Verification:** logged in as `bandit9` with this password.
- **Recording:** `recordings/bandit/L8.cast`

## Level 9 → bandit10
- **Account:** `bandit9`.
- **Goal:** The password is stored in a binary file (`data.txt`) as human-readable text, preceded by several `=` characters.
- **Technique and why it works:** `strings` extracts printable runs from binary data; filtering with `grep "==="` keeps the marker lines. The last of them is `========== <password>`.
- **Commands:**
  ```
  strings data.txt | grep "==="
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Check the file type.** `file data.txt` reports binary data, so `cat` would be unreadable.
2. **Pull printable strings.** `strings data.txt` extracts printable runs.
3. **Filter for the marker.** `strings data.txt | grep "==="` keeps the lines that start with `=`; the last one carries the password.
- **Password for bandit10:** `B0s2khmbT9u0geKuOoVGW3JZKhndE3BG`
- **Verification:** logged in as `bandit10` with this password.
- **Recording:** `recordings/bandit/L9.cast`

## Level 10 → bandit11
- **Account:** `bandit10`.
- **Goal:** `data.txt` contains base64-encoded data; the password is the decoded text.
- **Technique and why it works:** base64 is a reversible encoding of bytes into an ASCII alphabet. `base64 -d` decodes it back, yielding `The password is <pw>`.
- **Commands:**
  ```
  base64 -d data.txt
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Recognise the encoding.** `cat data.txt` shows text ending in `=`, the base64 padding character.
2. **Decode it.** `base64 -d data.txt` converts the ASCII alphabet back to the original bytes, which read `The password is <pw>`.
- **Password for bandit11:** `pYfOY6HwUsDj5rL9UvyhU7MCmv8vN5Ro`
- **Verification:** logged in as `bandit11` with this password.
- **Recording:** `recordings/bandit/L10.cast`

## Level 11 → bandit12
- **Account:** `bandit11`.
- **Goal:** The password in `data.txt` has been rotated 13 positions (ROT13).
- **Technique and why it works:** ROT13 is a Caesar shift by 13 over the 26-letter alphabet; it is its own inverse, so applying it to the ciphertext returns the plaintext. `tr` maps each character range: `A-Z` → `N-ZA-M` and `a-z` → `n-za-m`.
- **Commands:**
  ```
  cat data.txt | tr 'A-Za-z' 'N-ZA-Mn-za-m'
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the data.** `cat data.txt` shows the ciphertext.
2. **Apply ROT13.** `cat data.txt | tr 'A-Za-z' 'N-ZA-Mn-za-m'` maps `A-Z` to `N-ZA-M` and `a-z` to `n-za-m`; because the shift is 13, applying it to the ciphertext returns the plaintext.
- **Password for bandit12:** `GROozWPO8QyN0mGrjUkID0WCYkZiQxrN`
- **Verification:** logged in as `bandit12` with this password.
- **Recording:** `recordings/bandit/L11.cast`

## Level 12 → bandit13
- **Account:** `bandit12`.
- **Goal:** `data.txt` is a hexdump of a file that has been repeatedly compressed; recover the password from the innermost layer.
- **Technique and why it works:** Each layer must be identified before it can be peeled. `xxd -r` reverses the hexdump into the first binary; `file -b` names each layer; `gzip -dc` / `bzip2 -dc` decompress; `tar -xf` extracts an archive. The chain here is gzip → bzip2 → gzip → tar → (data5.bin) tar → (data6.bin) bzip2 → tar → (data8.bin) gzip → plaintext. Compression tools key off content, not extensions, but `tar` is happier with an archive-looking name; each step is therefore renamed to its real type before use. Working in `/tmp` (world-writable, unlike the home directory) is needed because the home dir is read-only for this account.
- **Commands:**
  ```
  mkdir -p /tmp/b12live && cd /tmp/b12live
  xxd -r ~/data.txt > d1.bin
  mv d1.bin d1.gz && gzip -dc d1.gz > d2.bin && file -b d2.bin
  mv d2.bin d2.bz2 && bzip2 -dc d2.bz2 > d3.bin && file -b d3.bin
  mv d3.bin d3.gz && gzip -dc d3.gz > d4.tar && file -b d4.tar
  tar -xf d4.tar && tar -tf data5.bin
  tar -xf data5.bin && file -b data6.bin
  mv data6.bin d6.bz2 && bzip2 -dc d6.bz2 > d7.tar && tar -tf d7.tar
  tar -xf d7.tar && file -b data8.bin
  mv data8.bin d8.gz && gzip -dc d8.gz
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Work in a writable directory.** The home directory is read-only for this account, so the session creates `/tmp/b12live` and works there (`mkdir -p /tmp/b12live && cd /tmp/b12live`).
2. **Undo the hexdump.** `xxd -r ~/data.txt > d1.bin` turns the hexdump back into bytes.
3. **Identify the first layer.** `mv d1.bin d1.gz && gzip -dc d1.gz > d2.bin && file -b d2.bin` — the rename matters because the tools key off content, but `file` tells us what we have next.
4. **Peel layer by layer.** `mv d2.bin d2.bz2 && bzip2 -dc d2.bz2 > d3.bin`, then `mv d3.bin d3.gz && gzip -dc d3.gz > d4.tar`, then `tar -xf d4.tar && tar -tf data5.bin` shows the next archive.
5. **Keep going.** `tar -xf data5.bin && file -b data6.bin` → `mv data6.bin d6.bz2 && bzip2 -dc d6.bz2 > d7.tar && tar -tf d7.tar` → `tar -xf d7.tar && file -b data8.bin` → `mv data8.bin d8.gz && gzip -dc d8.gz` prints the plaintext password.
6. **Note the pattern.** Each step is *identify with `file`*, *rename to the real type*, *decompress*. The chain is gzip → bzip2 → gzip → tar → tar → bzip2 → tar → gzip.
- **Password for bandit13:** `qQYQiHOBPR8zR61qxYqX45quvihF2uzk`
- **Verification:** logged in as `bandit13` with this password.
- **Recording:** `recordings/bandit/L12.cast`

## Level 13 → bandit14
- **Account:** `bandit13`.
- **Goal:** The home directory contains `sshkey.private`, a private key that can log in as bandit14; use it to read bandit14's password.
- **Technique and why it works:** SSH public-key auth: the private key proves possession of the identity whose public half is in bandit14's `~/.ssh/authorized_keys`. `ssh -i key` selects it. The official level page suggests `ssh -i sshkey.private bandit14@localhost`, but the OTW backend refuses connections from localhost; so the key is copied to the client machine (fetched by `cat` over an authenticated session) and used to connect to the public host directly. The key must be mode 600 or ssh refuses to use it.
- **Commands:**
  ```
  # on the client: fetch the key out of bandit13's home
  ssh bandit13@bandit.labs.overthewire.org -p 2220 'cat sshkey.private' > key
  chmod 600 key
  ssh -i key bandit14@bandit.labs.overthewire.org -p 2220 'cat /etc/bandit_pass/bandit14'
  ```
  (Inside bandit13, `cat HINT` and `cat sshkey.private` confirm the intended route; the localhost hop is rejected with "Connecting from/to localhost is blocked".)
### Step-by-step discovery and crafting (what the recording shows)
1. **Inspect the key.** The home directory holds `sshkey.private`; `head -1` on the fetched copy shows `-----BEGIN OPENSSH PRIVATE KEY-----`.
2. **Fetch it to this client.** OTW's backend refuses connections from `localhost`, so the key is read over the authenticated session: `ssh bandit13@... -p 2220 "cat sshkey.private" > key` (mode 600, or ssh refuses to use it).
3. **Use it against the public host.** `ssh -i key bandit14@bandit.labs.overthewire.org -p 2220 "cat /etc/bandit_pass/bandit14"` — public-key auth proves possession of the identity whose public half is in bandit14's `authorized_keys`.
- **Password for bandit14:** `aaWecNkG4FhxJQxz07uiwzVP6bJiYS65`
- **Verification:** logged in as `bandit14` with this password.
- **Recording:** `recordings/bandit/L13.cast`

## Level 14 → bandit15
- **Account:** `bandit14`.
- **Goal:** Submit the current level's password to the service on `localhost:30000`; it answers with the next password.
- **Technique and why it works:** The level runs a plain TCP daemon on port 30000 that reads a line and checks it against bandit14's password. `nc` connects, and the shell pipeline feeds the password line on stdin. `-q 2` closes after 2 seconds once stdin ends so the read completes and the connection tears down cleanly.
- **Commands:**
  ```
  echo aaWecNkG4FhxJQxz07uiwzVP6bJiYS65 | nc -q 2 localhost 30000
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Connect and send the password.** `echo aaWecNkG4FhxJQxz07uiwzVP6bJiYS65 | nc -q 2 localhost 30000` — the daemon reads one line and compares it with bandit14's password.
2. **Why `-q 2`.** When stdin ends, `nc` would close immediately; `-q 2` keeps the socket open for two more seconds so the daemon's reply can be read.
- **Password for bandit15:** `pbLYuZtTg4MgaqfJx8jbA9gKKGqM68A7`
- **Verification:** logged in as `bandit15` with this password.
- **Recording:** `recordings/bandit/L14.cast`

## Level 15 → bandit16
- **Account:** `bandit15`.
- **Goal:** Same idea as level 14, but the service on `localhost:30001` speaks TLS.
- **Technique and why it works:** A plain `nc` to 30001 fails because the daemon expects a TLS handshake. `openssl s_client` performs the handshake (and, with `-quiet`, suppresses the certificate chatter); the password is then written over the encrypted channel. `2>/dev/null` drops the handshake diagnostics on stderr so the transcript shows only the daemon's reply.
- **Commands:**
  ```
  echo pbLYuZtTg4MgaqfJx8jbA9gKKGqM68A7 | openssl s_client -connect localhost:30001 -quiet 2>/dev/null
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Try the same idea as level 14.** A plain `nc` to port 30001 fails: the daemon expects a TLS handshake first.
2. **Speak TLS.** `echo pbLYuZtTg4MgaqfJx8jbA9gKKGqM68A7 | openssl s_client -connect localhost:30001 -quiet 2>/dev/null` performs the handshake and writes the password over the encrypted channel.
3. **Why `-quiet` and `2>/dev/null`.** `-quiet` suppresses the certificate chatter; redirecting stderr drops the remaining handshake diagnostics so the transcript shows only the daemon's reply.
- **Password for bandit16:** `kS0Hf0u5HiXFwKMKFqXvPdOTNGGa0X8V`
- **Verification:** logged in as `bandit16` with this password.
- **Recording:** `recordings/bandit/L15.cast`

## Level 16 → bandit17
- **Account:** `bandit16`.
- **Goal:** Credentials for the next level are served by one of the ports in 31000–32000; find the right one and speak its protocol. A correct submission returns an SSH private key for bandit17.
- **Technique and why it works:** `nmap -p 31000-32000 localhost` lists the open ports (31046, 31518, 31691, 31790, 31960). Some are decoys (echo services that just return the input); the real service is TLS on 31790: submitting bandit16's password there yields `Correct!` followed by a PEM private key. The key is saved, mode 600, and used to log in to bandit17 on the public host (the localhost hop is blocked by OTW, same as level 13).
- **Commands:**
  ```
  nmap -p 31000-32000 localhost
  echo kS0Hf0u5HiXFwKMKFqXvPdOTNGGa0X8V | openssl s_client -connect localhost:31790 -quiet
  # save the returned key, chmod 600, then:
  ssh -i key bandit17@bandit.labs.overthewire.org -p 2220 'cat /etc/bandit_pass/bandit17'
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Scan the port range.** `nmap -p 31000-32000 localhost` (run as bandit16) lists 31046, 31518, 31691, 31790 and 31960.
2. **Probe the candidates.** Several are decoy echo services that return the input unchanged; the real service is TLS on 31790.
3. **Submit there.** `echo <bandit16 pw> | openssl s_client -connect localhost:31790 -quiet` answers `Correct!` followed by a PEM private key.
4. **Use the key.** Save it (mode 600) and `ssh -i key bandit17@bandit.labs.overthewire.org -p 2220 "cat /etc/bandit_pass/bandit17"` — the localhost hop is blocked by OTW, so the key is used from this client.
- **Password for bandit17:** `pWXMAZoxGC8JmDMfmT5MGEsobMM3vnj2`
- **Verification:** logged in as `bandit17` with this password (and the returned key authenticated as bandit17 before that).
- **Recording:** `recordings/bandit/L16.cast`

## Level 17 → bandit18
- **Account:** `bandit17`.
- **Goal:** There are two files, `passwords.old` and `passwords.new`; the password for bandit18 is the one line that changed.
- **Technique and why it works:** `diff` reports only differing lines; the single hunk `42c42` shows the old value (`<`) and the new value (`>`). The new side is the password for the next level.
- **Commands:**
  ```
  diff passwords.old passwords.new
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Compare the two files.** `diff passwords.old passwords.new` prints only the differing lines.
2. **Read the hunk.** The single change is `42c42`, with the old value on the `<` side and the new one on the `>` side — the new value is bandit18's password.
- **Password for bandit18:** `OQxXZjELndr90zuhOTDYBEomI0SZITXI`
- **Verification:** logged in as `bandit18` with this password.
- **Recording:** `recordings/bandit/L17.cast`

## Level 18 → bandit19
- **Account:** `bandit18`.
- **Goal:** The password is in `readme`, but logging in interactively is immediately terminated.
- **Technique and why it works:** bandit18's shell startup (`.bashrc`) logs the session out, so an interactive `ssh` dies before you can type anything. Running a command non-interactively makes ssh execute it directly and return its output without ever starting the interactive shell that would exit: `ssh host 'cat readme'`. No PTY is requested, so the logout hook never matters.
- **Commands:**
  ```
  ssh bandit18@bandit.labs.overthewire.org -p 2220 'cat readme'
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Observe the symptom.** An interactive login dies immediately: bandit18's shell startup (`.bashrc`) logs the session out before it can accept input.
2. **Run a command non-interactively.** `ssh bandit18@bandit.labs.overthewire.org -p 2220 "cat readme"` makes ssh execute the command directly and return its output, never starting the interactive shell that would exit.
- **Password for bandit19:** `KpsOfPkcP7i1FlIExk2QEjyt6dw8dxZI`
- **Verification:** logged in as `bandit19` with this password.
- **Recording:** `recordings/bandit/L18.cast`

## Level 19 → bandit20
- **Account:** `bandit19`.
- **Goal:** Use the setuid binary `bandit20-do` to read bandit20's password.
- **Technique and why it works:** `bandit20-do` is mode `-rwsr-x---` owned by bandit20: when executed it runs with bandit20's effective UID. It execs the command given as its arguments with that euid, so `cat /etc/bandit_pass/bandit20` is performed as bandit20 and can read the `0400 bandit20` password file.
- **Commands:**
  ```
  ls -la                 # shows -rwsr-x--- 1 bandit20 bandit19 bandit20-do
  ./bandit20-do cat /etc/bandit_pass/bandit20
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **List the directory.** `ls -la` shows `bandit20-do` with mode `-rwsr-x---` and owner `bandit20` — a setuid binary.
2. **Check what it does.** It execs the command given as its arguments with bandit20's effective UID.
3. **Use it.** `./bandit20-do cat /etc/bandit_pass/bandit20` reads the `0400 bandit20` password file because the `cat` it runs is bandit20.
- **Password for bandit20:** `4pIjcunZ0fK2vmp3IwfG8Vf7VhxD6pOA`
- **Verification:** logged in as `bandit20` with this password.
- **Recording:** `recordings/bandit/L19.cast`

## Level 20 → bandit21
- **Account:** `bandit20`.
- **Goal:** `suconnect` connects to a TCP port on localhost, sends the current password, and if it matches, sends back the next password. Provide a matching listener.
- **Technique and why it works:** The binary is setuid bandit21, so the reply it receives is bandit21's password. We start our own listener on an arbitrary port (4000) with `nc -l -p 4000` and feed it bandit20's password (the value suconnect compares against), then run `./suconnect 4000`. `(echo ...; sleep 3)` keeps the connection open long enough for suconnect to read and reply; the sleep matters because nc would otherwise close stdin immediately.
- **Commands:**
  ```
  (echo 4pIjcunZ0fK2vmp3IwfG8Vf7VhxD6pOA; sleep 3) | nc -l -p 4000 &
  sleep 1
  ./suconnect 4000
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **List the directory.** `ls -la` shows `suconnect`, setuid bandit21.
2. **Understand the protocol.** `suconnect <port>` connects to a TCP port on localhost, sends bandit20's password, and — if it matches — sends back bandit21's password.
3. **Start the listener.** `(echo 4pIjcunZ0fK2vmp3IwfG8Vf7VhxD6pOA; sleep 3) | nc -l -p 4000 &` listens on port 4000 and feeds the password on stdin.
4. **Connect the binary.** `sleep 1` gives the listener time to bind, then `./suconnect 4000` performs the exchange. The `sleep 3` in the pipeline is what keeps stdin open long enough for suconnect to read the reply.
- **Password for bandit21:** `bW9kBv5WC3P4yoDyf12LSdGuNz5ka6hY`
- **Verification:** logged in as `bandit21` with this password.
- **Recording:** `recordings/bandit/L20.cast`

## Level 21 → bandit22
- **Account:** `bandit21`.
- **Goal:** A cron job runs a script as bandit22; find what it does and where the password lands.
- **Technique and why it works:** Cron jobs are defined in `/etc/cron.d/`, and the job runs `/usr/bin/cronjob_bandit22.sh` every minute as user bandit22. The script is world-readable and does two things: `chmod 644` a fixed file in `/tmp`, then copy `/etc/bandit_pass/bandit22` into it. Because the script runs as bandit22 it can read that file, and the `chmod 644` makes the copy readable by us. Reading the output file yields the password.
- **Commands:**
  ```
  cat /etc/cron.d/cronjob_bandit22
  cat /usr/bin/cronjob_bandit22.sh
  cat /tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Find the cron job.** `cat /etc/cron.d/cronjob_bandit22` shows it runs every minute as bandit22.
2. **Read the script.** `cat /usr/bin/cronjob_bandit22.sh` shows it `chmod 644`s a fixed file in `/tmp` and copies `/etc/bandit_pass/bandit22` into it.
3. **Read the copy.** `cat /tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv` prints the password — the script can read it as bandit22, and the `chmod 644` makes the copy readable by us.
- **Password for bandit22:** `RYVux2rHEm9tiXHmLFzuR7Vhx6AZQMEz`
- **Verification:** logged in as `bandit22` with this password.
- **Recording:** `recordings/bandit/L21.cast`

## Level 22 → bandit23
- **Account:** `bandit22`.
- **Goal:** Another cron job copies a password into `/tmp` under a name computed at runtime; work out the name.
- **Technique and why it works:** `/usr/bin/cronjob_bandit23.sh` computes `myname=$(whoami)` — which is `bandit23` when cron runs it — then `mytarget=$(echo I am user $myname | md5sum | cut -d ' ' -f 1)`, and writes `/etc/bandit_pass/$myname` to `/tmp/$mytarget`. Reproducing the exact pipeline on our side gives the same MD5 name, so the file can be read directly.
- **Commands:**
  ```
  cat /etc/cron.d/cronjob_bandit23
  cat /usr/bin/cronjob_bandit23.sh
  echo I am user bandit23 | md5sum | cut -d ' ' -f 1     # 8ca319486bfbbc3663ea0fbe81326349
  cat /tmp/8ca319486bfbbc3663ea0fbe81326349
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Find the cron job.** `cat /etc/cron.d/cronjob_bandit23` points at `/usr/bin/cronjob_bandit23.sh`.
2. **Read the script.** `cat /usr/bin/cronjob_bandit23.sh` computes `myname=$(whoami)` (which is `bandit23` under cron) and `mytarget=$(echo I am user $myname | md5sum | cut -d ' ' -f 1)`, then writes `/etc/bandit_pass/$myname` to `/tmp/$mytarget`.
3. **Reproduce the name.** `echo I am user bandit23 | md5sum | cut -d ' ' -f 1` gives the same MD5, so the output path is predictable.
4. **Read it.** `cat /tmp/8ca319486bfbbc3663ea0fbe81326349` prints the password.
- **Password for bandit23:** `gKXDTAXnIz3OBxiPjRZ2uqutUlPZrBsw`
- **Verification:** logged in as `bandit23` with this password.
- **Recording:** `recordings/bandit/L22.cast`

## Level 23 → bandit24
- **Account:** `bandit23`.
- **Goal:** A cron job runs every script dropped into `/var/spool/bandit24/foo` as bandit24; get it to read bandit24's password.
- **Technique and why it works:** `/var/spool/bandit24/foo` is mode `drwxrwx-wx` with group `bandit24` — bandit23 can create files but cannot list the directory. The cron script (`cronjob_bandit24.sh`) iterates the directory, checks each file's owner is `bandit23`, and if it is a regular file, runs it with `timeout -s 9 60 ./file` **as bandit24**. So a script we write is executed with bandit24's privileges; it can read `/etc/bandit_pass/bandit24` and copy it to a world-readable location. The script must be executable (the cron job invokes it directly). Cron fires every minute, so wait ~70 s and read the output.
- **Commands:**
  ```
  cat /etc/cron.d/cronjob_bandit24
  cat /usr/bin/cronjob_bandit24.sh
  ls -ld /var/spool/bandit24/foo
  echo 'cat /etc/bandit_pass/bandit24 > /tmp/b23out; chmod 644 /tmp/b23out' > /var/spool/bandit24/foo/grab.sh
  chmod +x /var/spool/bandit24/foo/grab.sh
  # wait for the next cron minute, then:
  cat /tmp/b23out
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Find the cron job.** `cat /etc/cron.d/cronjob_bandit24` → `/usr/bin/cronjob_bandit24.sh`.
2. **Read the script.** It iterates `/var/spool/bandit24/foo`, checks each file is owned by `bandit23` and is a regular file, and runs it with `timeout -s 9 60 ./file` **as bandit24**.
3. **Check the directory.** `ls -ld /var/spool/bandit24/foo` shows `drwxrwx-wx` group `bandit24`: we can create files but not list them.
4. **Drop the payload.** `echo 'cat /etc/bandit_pass/bandit24 > /tmp/b23out; chmod 644 /tmp/b23out' > /var/spool/bandit24/foo/grab.sh` writes a script that reads the password and copies it to a world-readable file.
5. **Make it executable.** `chmod +x /var/spool/bandit24/foo/grab.sh` — the cron job invokes the file directly, so the execute bit matters.
6. **Wait for cron.** It fires every minute; after ~70 s, `cat /tmp/b23out` prints the password.
- **Password for bandit24:** `hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv`
- **Verification:** logged in as `bandit24` with this password.
- **Recording:** `recordings/bandit/L23.cast`

## Level 24 → bandit25
- **Account:** `bandit24`.
- **Goal:** A daemon on `localhost:30002` gives out bandit25's password to whoever supplies bandit24's password plus a secret 4-digit PIN on one line.
- **Technique and why it works:** The PIN space is only 10,000 values (`0000`–`9999`), so exhaustive search is trivial. The daemon reads one line per attempt on the same connection, so we generate all candidate lines up front (`seq -w 0 9999` zero-pads to 4 digits) and pipe them through a single `nc`. `grep -v Wrong` drops the rejection messages, leaving the greeting and the success line with the password.
- **Commands:**
  ```
  echo hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv 0000 | nc -q 2 localhost 30002   # shows the protocol
  for i in $(seq -w 0 9999); do echo "hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv $i"; done \
    | nc -q 2 localhost 30002 | grep -v Wrong
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Understand the protocol.** The daemon on port 30002 wants bandit24's password plus a 4-digit PIN on one line.
2. **Test one attempt.** `echo hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv 0000 | nc -q 2 localhost 30002` shows the rejection message.
3. **Generate the whole space.** `for i in $(seq -w 0 9999); do echo "hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv $i"; done` builds 10,000 candidate lines (`seq -w` zero-pads).
4. **Send them in one connection.** Pipe that loop into `nc -q 2 localhost 30002`; the daemon reads one line per attempt.
5. **Drop the failures.** `| grep -v Wrong` leaves the greeting and the success line with the password.
- **Password for bandit25:** `SoHfqMOEqIX2IYKVciZxvgpR9a2Djx4P`
- **Verification:** logged in as `bandit25` with this password.
- **Recording:** `recordings/bandit/L24.cast`

## Level 25 → bandit26
- **Account:** `bandit25`.
- **Goal:** bandit25's home holds `bandit26.sshkey`, the private key for bandit26. Log in as bandit26 and read its password from `/etc/bandit_pass/bandit26`. The catch: bandit26's login shell is `/usr/bin/showtext`, which runs `exec more ~/text.txt` and then exits — so logging in never gives you a shell.
- **Technique and why it works:** `more` has an interactive escape hatch: pressing `v` opens the current file in `vi`. Inside `vi`, `:set shell=/bin/bash` then `:shell` starts a bash under bandit26's identity, and from it `/etc/bandit_pass/bandit26` is readable. The catch is that `~/text.txt` is only 6 lines (258 bytes): on a normal terminal `more` prints it all and exits without ever showing the `--More--` prompt, so there is no chance to press `v`. Shrinking the terminal to ~5 rows forces `more` to paginate and keep the prompt on screen; that is why the recording runs the session on a 60x5 PTY. The localhost hop is blocked on the lab, so the key is fetched over SSH from this client, written to a mode-600 file, and used for a direct connection to the public host.
- **Commands:**
  ```
  ssh bandit25@bandit.labs.overthewire.org -p 2220 'cat bandit26.sshkey'   # save it, chmod 600
  ssh -i bandit26.sshkey bandit26@bandit.labs.overthewire.org -p 2220      # on a ~5-row terminal
  # at the --More--(66%) prompt: press  v
  # in vi:
  :set shell=/bin/bash
  :shell
  cat /etc/bandit_pass/bandit26
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Fetch the key.** `ssh bandit25@… 'ls -la; cat bandit26.sshkey'` shows `bandit26.sshkey` is mode `-r--------` (readable only by bandit25, which is who we are). The recording extracts the PEM block into `bandit26.sshkey` and `chmod 600`s it — ssh refuses a key that is group/other readable.
2. **Find the shell.** `getent passwd bandit26` / the level goal shows the login shell is `/usr/bin/showtext`, which runs `exec more ~/text.txt` and exits. A plain login therefore prints the banner and drops you straight back out.
3. **Find the escape.** `more` lets you press `v` to open the file in `vi`; in `vi`, `:set shell=/bin/bash` then `:shell` starts bash as bandit26. The recording shows the `--More--(66%)` prompt, the `v` press, and the vi status line `"~/text.txt" </text.txt> [readonly] 6L, 258B`.
4. **Force pagination.** `~/text.txt` is 6 lines / 258 bytes, so on a normal terminal `more` prints it and exits before you can press `v`. Running the session on a 60x5 PTY (as the recording does) forces the `--More--` prompt to appear.
5. **Read the password.** In the escaped shell, `cat /etc/bandit_pass/bandit26` prints it. The recording then logs out and the verification step uses that password on a fresh SSH connection.
- **Password for bandit26:** `jHdv2ELQhT22BkprMNDjybZDAkw1zeBJ`
- **Verification:** logged in as `bandit26` with this password (the login runs `showtext`, confirming the account).
- **Recording:** `recordings/bandit/L25.cast`

## Level 26 → bandit27
- **Account:** `bandit26` (reached through the level-25 `more`→`vi`→`:shell` escape; the shell is not the login shell, so we stay in it rather than starting a new SSH session).
- **Goal:** bandit26's home holds `bandit27-do`, a setuid binary owned by bandit27. Use it to read `/etc/bandit_pass/bandit27`.
- **Technique and why it works:** `bandit27-do` is setuid bandit27, so it executes whatever command you give it with bandit27's effective UID. `ls -l bandit27-do` shows the `s` bit in the owner execute position; `./bandit27-do cat /etc/bandit_pass/bandit27` therefore cats a file that bandit26 cannot read directly. This is the same setuid primitive as bandit19's `bandit20-do`.
- **Commands:**
  ```
  ls -l ./bandit27-do
  ./bandit27-do cat /etc/bandit_pass/bandit27
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Reach the shell.** Reuse the level-25 escape (`ssh -i bandit26.sshkey bandit26@…` on a 60x5 PTY, `v`, `:set shell=/bin/bash`, `:shell`). The recording repeats it live rather than assuming a saved session.
2. **Spot the helper.** `ls -l` in `~` shows `bandit27-do` with the setuid bit and owner bandit27. Anything it runs runs as bandit27.
3. **Run it.** `./bandit27-do cat /etc/bandit_pass/bandit27` prints the password — a direct `cat /etc/bandit_pass/bandit27` as bandit26 would be permission denied.
- **Password for bandit27:** `STJLJBRRphMxKB392CT4iOr5CbzPU9ER`
- **Verification:** logged in as `bandit27` with this password.
- **Recording:** `recordings/bandit/L26.cast`

## Level 27 → bandit28
- **Account:** `bandit27`.
- **Goal:** A git repository is served over SSH at `ssh://bandit27-git@bandit.labs.overthewire.org:2220/home/bandit27-git/repo`; clone it and read the password for bandit28.
- **Technique and why it works:** The repo is hosted over git's SSH transport, authenticated with bandit27's password (the account `bandit27-git` shares the credential). `git clone` with the `ssh://` URL pulls the objects and checks out `README`. The README states the next password in plain text. The clone is run from this client with the password supplied through `SSH_ASKPASS`, because the game backend blocks localhost connections.
- **Commands:**
  ```
  git clone ssh://bandit27-git@bandit.labs.overthewire.org:2220/home/bandit27-git/repo
  cat repo/README
  ```
  (The recording shows the same clone, with `GIT_SSH_COMMAND` forcing password auth and `SSH_ASKPASS` supplying the bandit27 password.)
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the goal.** The level page gives the `ssh://…bandit27-git…/home/bandit27-git/repo` URL and states that `bandit27-git` shares bandit27's password.
2. **Clone the repository.** `git clone ssh://bandit27-git@bandit.labs.overthewire.org:2220/home/bandit27-git/repo` — git's SSH transport, authenticated with bandit27's password via `SSH_ASKPASS`.
3. **Read the README.** `cat repo/README` prints `The password to the next level is: …` in plain text.
- **Password for bandit28:** `y8Yd2ssKcpHpud7UvOSOxwamRMzIGIeQ`
- **Verification:** logged in as `bandit28` with this password.
- **Recording:** `recordings/bandit/L27.cast`

## Level 28 → bandit29
- **Account:** `bandit28`.
- **Goal:** Clone the `bandit28-git` repository and obtain bandit29's password.
- **Technique and why it works:** The repository's `README.md` in the current commit (HEAD) shows the password redacted as `xxxxxxxxxx`; the HEAD commit is literally titled "fix info leak". But git keeps every version of every file, and the previous commit (`HEAD~1`) still contains the real password. `git log --oneline` reveals the history, and `git show HEAD~1:README.md` prints the old file version. Removing a secret from the working tree does not remove it from history.
- **Commands:**
  ```
  git clone ssh://bandit28-git@bandit.labs.overthewire.org:2220/home/bandit28-git/repo
  cd repo
  cat README.md               # redacted at HEAD
  git --no-pager log --oneline
  git --no-pager show HEAD~1:README.md
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Clone and read.** `git clone …` then `cat README.md` shows `password: xxxxxxxxxx`, and `git --no-pager log --oneline` shows the tip commit titled "fix info leak" above "add missing data" and "initial commit of README.md".
2. **Look at history.** The redaction is in HEAD only; the parent commit still has the original file.
3. **Print the parent version.** `git --no-pager show HEAD~1:README.md` prints the previous file, which still contains the real password. Removing a secret from the working tree does not remove it from history.
- **Password for bandit29:** `Em7eGtqaMySwNFjCpwzzHhLhospOcdt0`
- **Verification:** logged in as `bandit29` with this password.
- **Recording:** `recordings/bandit/L28.cast`

## Level 29 → bandit30
- **Account:** `bandit29`.
- **Goal:** Clone the `bandit29-git` repository and find bandit30's password.
- **Technique and why it works:** On the default branch (`master`) the README says `<no passwords in production!>`, but `git branch -a` shows remote branches, including `dev`. The password lives in a development branch that was never merged: `git show origin/dev:README.md` prints that branch's version of the file, which contains the real password.
- **Commands:**
  ```
  git clone ssh://bandit29-git@bandit.labs.overthewire.org:2220/home/bandit29-git/repo
  cd repo
  cat README.md
  git --no-pager branch -a
  git --no-pager show origin/dev:README.md
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Clone and read.** `git clone …` then `cat README.md` says `<no passwords in production!>` on `master`.
2. **List all refs.** `git --no-pager branch -a` shows `remotes/origin/dev` and `remotes/origin/sploits-dev` beside `master`.
3. **Read that branch's file.** `git --no-pager show origin/dev:README.md` prints the password — it was committed on a branch that was never merged.
- **Password for bandit30:** `jq9Dfg2rXsfYsWMgFuKlXhphjdH7USgX`
- **Verification:** logged in as `bandit30` with this password.
- **Recording:** `recordings/bandit/L29.cast`

## Level 30 → bandit31
- **Account:** `bandit30`.
- **Goal:** Clone the `bandit30-git` repository and find bandit31's password.
- **Technique and why it works:** The working tree is a decoy — the README says "just an epmty file... muahaha" and there are no branches of interest. But git tags are separate refs that can carry their own objects/messages; `git tag` lists one tag named `secret`, and `git show secret` prints its content, which is the password. Git stores more than files and commits: tags, notes, and stashes can all hold data.
- **Commands:**
  ```
  git clone ssh://bandit30-git@bandit.labs.overthewire.org:2220/home/bandit30-git/repo
  cd repo
  cat README.md
  git --no-pager tag
  git --no-pager show secret
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Clone and read.** `cat README.md` is a decoy ("just an epmty file... muahaha").
2. **List tags.** `git --no-pager tag` shows a tag named `secret`.
3. **Show the tag.** `git --no-pager show secret` prints its content — tags are refs that can carry their own objects and messages.
- **Password for bandit31:** `82NkymblpGBYmIXG6ZQ8YldBYstHpfUf`
- **Verification:** logged in as `bandit31` with this password.
- **Recording:** `recordings/bandit/L30.cast`

## Level 31 → bandit32
- **Account:** `bandit31`.
- **Goal:** The repository's README sets a task: push a file named `key.txt` containing `May I come in?` to branch `master` on the remote.
- **Technique and why it works:** The repo's `.gitignore` contains `*.txt`, so `git add key.txt` silently does nothing; `git add -f` overrides the ignore rule and stages it. After committing, `git push origin master` is deliberately rejected by a remote pre-receive hook — but that hook validates the pushed content and prints the password for bandit32 in its "remote:" output before declining the push. The password appears in the push output, not in the repository.
- **Commands:**
  ```
  git clone ssh://bandit31-git@bandit.labs.overthewire.org:2220/home/bandit31-git/repo
  cd repo
  echo 'May I come in?' > key.txt
  git add -f key.txt
  git commit -m 'key'
  git push origin master        # hook prints the password
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Clone and read the task.** `cat README.md; cat .gitignore` — the README asks for `key.txt` containing `May I come in?`, and `.gitignore` contains `*.txt`.
2. **Create the file.** `echo "May I come in?" > key.txt`.
3. **Defeat the ignore rule.** `git add -f key.txt` (plain `git add` would silently skip it).
4. **Commit and push.** `git commit -m "key"` then `git push origin master`.
5. **Read the hook output.** The remote pre-receive hook prints "Well done! Here is the password for the next level:" in its `remote:` lines, then declines the push.
- **Password for bandit32:** `pWuj5jBQ6IgV0NXwiH6g1pXRF8S1YvbT`
- **Verification:** logged in as `bandit32` with this password (the account presents the uppercase-only shell).
- **Recording:** `recordings/bandit/L31.cast`

## Level 32 → bandit33
- **Account:** `bandit32`.
- **Goal:** bandit32's login shell is a restricted shell ("WELCOME TO THE UPPERCASE SHELL") that uppercases every command before executing it. Break out and read bandit33's password.
- **Technique and why it works:** The wrapper uppercases the input string and then executes it. A command made only of characters with no case — like `$0` — is unchanged by uppercasing, and in a POSIX shell `$0` expands to the shell's own name, so `$0` re-executes the shell. That new shell is a normal `/bin/sh` (or bash) inherited with bandit32's effective UID, i.e. it keeps the privileges of the game account, and from it `cat /etc/bandit_pass/bandit33` works.
- **Commands:**
  ```
  $0
  id                            # uid=11033(bandit33) — we are running as the next level's user
  cat /etc/bandit_pass/bandit33
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Observe the shell.** bandit32's login shell prints "WELCOME TO THE UPPERCASE SHELL" and uppercases every command before executing it.
2. **Find a case-free command.** `$0` contains no letters, so uppercasing leaves it unchanged; in a POSIX shell `$0` expands to the shell's own name, so it re-executes the shell.
3. **Use the new shell.** The re-executed shell is a normal shell; `id` prints `uid=11033(bandit33) gid=11032(bandit32)`, and `cat /etc/bandit_pass/bandit33` prints the final password.
- **Password for bandit33:** `u4P2CyPOwPGLe94RdD9Uo2FxFwvnFswM`
- **Verification:** logged in as `bandit33` with this password; `~/README.txt` confirms it is the last level and `getent passwd bandit34` returns nothing.
- **Recording:** `recordings/bandit/L32.cast`

## Level 33 — final level (no next account)
- **Account:** `bandit33`.
- **Goal:** Confirm the game is complete.
- **Technique and why it works:** bandit33 is the final account. Its home contains `README.txt`, which reads "Congratulations on solving the last level of this game! At this moment, there are no more levels to play." `getent passwd bandit34` returns nothing, so there is no bandit34 account and no further password to find. OTW's own `games.json` reports `lastlevel: 34` and `bandit34.html` says "At this moment, level 34 does not exist yet." Nothing to exploit here; the level is the end marker of the game.
- **Commands:**
  ```
  ssh bandit33@bandit.labs.overthewire.org -p 2220
  cat ~/README.txt
  getent passwd bandit34 || echo "no bandit34"
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the end marker.** `cat ~/README.txt` says "Congratulations on solving the last level of this game! At this moment, there are no more levels to play."
2. **Confirm there is no next account.** `getent passwd bandit34 || echo "no bandit34"` prints `no bandit34`, so the game ends at bandit33.
- **Password for bandit34:** none — the game ends at bandit33.
- **Verification:** login as bandit33 succeeds; the README states the game is complete; no bandit34 user exists on the host.
- **Recording:** `recordings/bandit/L33.cast`
