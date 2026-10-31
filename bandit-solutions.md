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
- **Password for bandit25:** `SoHfqMOEqIX2IYKVciZxvgpR9a2Djx4P`
- **Verification:** logged in as `bandit25` with this password.
- **Recording:** `recordings/bandit/L24.cast`

