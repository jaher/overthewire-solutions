# OTW solve progress

Live solves, recorded with asciinema. Format: game | level | technique | recording.
Bandit | L0 | read ~/readme with cat | recordings/bandit/L0.cast
Bandit | L1 | cat ./- (dash-prefixed filename) | recordings/bandit/L1.cast
Bandit | L2 | quote the filename containing spaces | recordings/bandit/L2.cast
Bandit | L3 | ls -la to reveal the hidden file in inhere/ | recordings/bandit/L3.cast
Bandit | L4 | file inhere/* to find the only ASCII text file | recordings/bandit/L4.cast
Bandit | L5 | find -size 1033c ! -executable under inhere | recordings/bandit/L5.cast
Bandit | L6 | find / -user bandit7 -group bandit6 -size 33c 2>/dev/null | recordings/bandit/L6.cast
Bandit | L7 | grep millionth data.txt | recordings/bandit/L7.cast
Bandit | L8 | sort data.txt | uniq -u | recordings/bandit/L8.cast
Bandit | L9 | strings data.txt | grep "===" | recordings/bandit/L9.cast
Bandit | L10 | base64 -d data.txt | recordings/bandit/L10.cast
Bandit | L11 | ROT13 via tr | recordings/bandit/L11.cast
Bandit | L12 | peel xxd/gzip/bzip2/tar layers with file | recordings/bandit/L12.cast
Bandit | L13 | ssh private key, log in to bandit14 from client (localhost hop blocked) | recordings/bandit/L13.cast
Bandit | L14 | pipe current password into nc localhost:30000 | recordings/bandit/L14.cast
Bandit | L15 | SSL submission with openssl s_client to localhost:30001 | recordings/bandit/L15.cast
Bandit | L16 | nmap port scan + SSL key exchange on 31790, login as bandit17 | recordings/bandit/L16.cast
Bandit | L17 | diff passwords.old passwords.new | recordings/bandit/L17.cast
Bandit | L18 | non-interactive ssh command (bashrc logs out interactive) | recordings/bandit/L18.cast
Bandit | L19 | setuid bandit20-do runs command as bandit20 | recordings/bandit/L19.cast
Bandit | L20 | nc listener + setuid suconnect password handshake | recordings/bandit/L20.cast
Bandit | L21 | read cron job script, grab password it writes to /tmp | recordings/bandit/L21.cast
Bandit | L22 | reproduce md5 filename computed by cron script | recordings/bandit/L22.cast
Bandit | L23 | drop executable script in bandit24 cron spool | recordings/bandit/L23.cast
Bandit | L24 | brute-force 10,000 pincodes against nc daemon | recordings/bandit/L24.cast
Bandit | L25 | escape showtext/more via vi on a tiny PTY, read bandit26 password | recordings/bandit/L25.cast
Bandit | L26 | setuid bandit27-do from the escaped bandit26 shell | recordings/bandit/L26.cast
Bandit | L27 | clone git repo over ssh, read README | recordings/bandit/L27.cast
Bandit | L28 | git history leaks redacted password (HEAD~1) | recordings/bandit/L28.cast
Bandit | L29 | git branch -a, password on origin/dev | recordings/bandit/L29.cast
Bandit | L30 | git tag "secret" holds the password | recordings/bandit/L30.cast
Bandit | L31 | force-add ignored key.txt, push; hook prints password | recordings/bandit/L31.cast
Bandit | L32 | $0 breaks the uppercase restricted shell | recordings/bandit/L32.cast
Bandit | L33 | final level: README confirms game complete, no bandit34 | recordings/bandit/L33.cast
Natas | L0 | password in HTML comment | recordings/natas/L0.cast
Natas | L1 | raw HTTP fetch bypasses client-side right-click block | recordings/natas/L1.cast
Natas | L2 | open directory index + users.txt | recordings/natas/L2.cast
Natas | L3 | robots.txt leaks /s3cr3t/, open index, users.txt | recordings/natas/L3.cast
Natas | L4 | spoof Referer header | recordings/natas/L4.cast
Natas | L5 | forge loggedin=1 cookie | recordings/natas/L5.cast
Natas | L6 | fetch included secret.inc | recordings/natas/L6.cast
Natas | L7 | page= path traversal / LFI to /etc/natas_webpass | recordings/natas/L7.cast
Natas | L8 | reverse encodeSecret: hex->rev->base64 | recordings/natas/L8.cast
Natas | L9 | command injection via passthru | recordings/natas/L9.cast
Natas | L10 | argument injection: grep extra file, blocks ;|& | recordings/natas/L10.cast
Natas | L11 | recover XOR key from known plaintext, forge cookie | recordings/natas/L11.cast
Natas | L12 | unrestricted upload with filename=shell.php | recordings/natas/L12.cast
Natas | L13 | GIF89a polyglot bypasses exif_imagetype | recordings/natas/L13.cast
Natas | L14 | SQL injection OR 1=1 | recordings/natas/L14.cast
Natas | L15 | blind SQLi: binary search on ORD(SUBSTR(password)) | recordings/natas/L15.cast
Leviathan | L0 | grep backup bookmarks.html for password | recordings/leviathan/L0.cast
Leviathan | L1 | setuid check accepts sex, spawns leviathan2 shell | recordings/leviathan/L1.cast
Leviathan | L2 | printfile access()/cat split: symlink + space in name | recordings/leviathan/L2.cast
Natas | L16 | $(...) substitution oracle (13 B match vs 460891 B dump) + binary search | recordings/natas/L16.cast
Leviathan | L3 | setuid level3 accepts snlprintf, spawns shell | recordings/leviathan/L3.cast
Leviathan | L4 | decode binary output of .trash/bin | recordings/leviathan/L4.cast
Leviathan | L5 | symlink /tmp/file.log to leviathan6 password | recordings/leviathan/L5.cast
Leviathan | L6 | read hardcoded code 7123 from disassembly | recordings/leviathan/L6.cast
Leviathan | L7 | final level: CONGRATULATIONS, no leviathan8 | recordings/leviathan/L7.cast
Krypton | L0 | Base64 decode of the level-page string | recordings/krypton/L0.cast
Krypton | L1 | ROT13 via tr | recordings/krypton/L1.cast
Krypton | L2 | Caesar chosen-plaintext oracle -> shift +12 | recordings/krypton/L2.cast
Krypton | L3 | BLOCKED: re-derived live 2026-11-03. found1..3 are a stepping-variant substitution over ONE stream (found1+found2+found3+krypton4, 4272 bytes; target = last 7 words = 35 letters K S V V W ...). Live frequencies S 12.9% Q 9.6% J 8.5% U 7.3% B 7.0% N 6.8% C/G 6.4% D 6.0%. ~12 letters of the alphabet recovered (S=E Q=T J=O U=A B=N N=I C=D G=H, C/G tie questionable); quadgram/trigram hill climbs and a +7 step test all failed to decode the target to readable English, no password derived. Old transcript's L3 row was reconstructed, not captured; superseded. Neighbouring levels re-verified live: L4 key FREKEY -> CLEARTEXT (login uid=8004); L5 keylength 9, key KEYLENGTH -> RANDOM (login uid=8006). | (no recording)
Krypton | L4 | Vigenere keylen 6: per-column chi-squared -> SERXRL, then ROT13 | recordings/krypton/L4.cast
Krypton | L5 | Vigenere unknown keylen: IC->9, per-column chi-squared->XRLYRATGU, then ROT13 | recordings/krypton/L5.cast
Krypton | L6 | chosen-plaintext recovers periodic LFSR keystream (period 30) | recordings/krypton/L6.cast
Krypton | L7 | final level: README confirms game complete | recordings/krypton/L7.cast
Manpage | L0 | BLOCKED: no account reachable — manpage.labs.overthewire.org:2224 refuses password auth for manpage0 and manpage1 ('Permission denied (publickey,password)'), so the levels cannot be replayed live from this host. Earlier attempts also found the setuid bit not honoured (euid stays manpage0 at main entry), so the level appears bit-rotted upstream. | (no recording)
Narnia | L0 | overwrite val via 24-byte scanf into 20-byte buf | recordings/narnia/L0.cast
Narnia | L1 | EGG env var shellcode (setreuid euid + execve), bytes env | recordings/narnia/L1.cast
Narnia | L2 | strcpy overflow: NOP sled + shellcode, swept return address | recordings/narnia/L2.cast
Narnia | L3 | ifile strcpy overflow rewrites ofile path to writable file | recordings/narnia/L3.cast
Narnia | L4 | buffer[256] strcpy overflow; setuid(euid) shellcode so the privilege survives execve; shellcode placed at buffer offset 0 to avoid its own execve pushes | recordings/narnia/L4.cast
Narnia | L5 | format string: snprintf dest overlaps varargs; 56 filler + &i + %440c%15$n writes 500 into i | recordings/narnia/L5.cast
Narnia | L6 | overflow b1[8] into function pointer fp (b1+8==fp); point fp at libc system; "sh;#AAAA"+addr comments out the address bytes | recordings/narnia/L6.cast
Narnia | L7 | format string writes hackedfunction into ptrf via %152$hn/%153$hn (arg index found by sweep) | recordings/narnia/L7.cast
Narnia | L8 | bok[20] copy-loop overflow: loop overwrites its own blah pointer; argv[20..23]=argv addr keeps it valid; ret into argv sled; final level (CONGRATULATIONS) | recordings/narnia/L8.cast
Behemoth | L0 | memfrob (XOR 42) obfuscated secret read from movl immediates -> "eatmyshorts" | recordings/behemoth/L0.cast
Behemoth | L1 | gets() overflow into buf[67]; RWE stack + ASLR off -> stack shellcode (nasm), swept ret 0xffffde20 | recordings/behemoth/L1.cast
Natas | L17 | time-based blind SQLi: scalar-subquery IF(cond,SLEEP(5)) for one sleep per query; binary search ORD(SUBSTR(password,pos,1)); len 32 | recordings/natas/L17.cast
Natas | L18 | brute-force PHPSESSID 1..640 (session_id=rand(1,640)); sid 119 is admin | recordings/natas/L18.cast
Natas | L19 | session id = bin2hex("<n>-admin"); brute-force n 1..640, found n=281 | recordings/natas/L19.cast
Natas | L20 | session-file injection: name="x\nadmin 1" adds an admin=1 line to the session | recordings/natas/L20.cast
Natas | L21 | colocated experimenter sets $_SESSION[key]=val; POST admin=1 then reuse PHPSESSID on main host | recordings/natas/L21.cast
Natas | L22 | ?revelio GET parameter alone prints credentials (no auth check) | recordings/natas/L22.cast
Natas | L23 | PHP loose comparison: "10111iloveyou" contains iloveyou and converts to 10111 > 10 | recordings/natas/L23.cast
Natas | L24 | passwd[]=x makes strcmp() receive an array -> NULL -> !NULL passes | recordings/natas/L24.cast
Natas | L25 | log poisoning via UA + ....// bypass of str_replace("../","") -> include the log | recordings/natas/L25.cast
Natas | L26 | PHP object injection: Logger __destruct writes PHP into img/natas26_<sid>.php | recordings/natas/L26.cast
Natas | L27 | truncation + MySQL trailing-space match: register padded natas28 row, login, dumpData(trim) prints the real row | recordings/natas/L27.cast
Natas | L28 | ECB cut-and-paste: splice ciphertext blocks to inject UNION SELECT password | recordings/natas/L28.cast
Natas | L29 | Perl two-arg open("$f.txt") pipe injection + glob n?tas bypass of /natas/ filter | recordings/natas/L29.cast
Natas | L30 | DBI quote() second arg is the SQL type: repeated password=1 OR 1=1 & password=4 -> SQL_INTEGER, unquoted | recordings/natas/L30.cast
Natas | L31 | CGI param/ARGV injection: plain file=ARGV field -> open("ARGV") reads @ARGV from the query string | recordings/natas/L31.cast
Natas | L32 | ARGV injection with " #" to defuse CGI quoting; run setuid getpassword in the webroot | recordings/natas/L32.cast
Natas | L33 | phar deserialization: md5_file(phar://...) unserializes metadata -> Executor __destruct passthru | recordings/natas/L33.cast
Behemoth | L2 | pid-file race: replace the touched <pid> file with a symlink to the password; program cats it as behemoth3 after sleep(2000) | recordings/behemoth/L2.cast
Behemoth | L3 | printf(buf) format string:  rewrites the saved return address; shellcode in vim+nasm, raw pty | recordings/behemoth/L3.cast
Behemoth | L4 | /tmp/<pid> symlink race with a predicted child pid (fork before exec) | recordings/behemoth/L4.cast
Behemoth | L5 | bind UDP 127.0.0.1:1337 before running; the program sendto()s the password to us | recordings/behemoth/L5.cast
Behemoth | L6 | shellcode.txt must write "HelloKitty" (nasm shellcode); behemoth6 then execs a shell | recordings/behemoth/L6.cast
Behemoth | L7 | alphanumeric filter checks only the first 512 chars; strcpy overflow carries nasm shellcode -> behemoth8 (CONGRATULATIONS) | recordings/behemoth/L7.cast
Utumno | L0 | execute-only binary dumped from inside the process with a 32-bit LD_PRELOAD constructor reading /proc/self/maps | recordings/utumno/L0.cast
Utumno | L1 | RWX mmap + strncpy shellcode runner: filename "sh_" + slash-free/NUL-free shellcode that builds /bin/sh byte by byte | recordings/utumno/L1.cast
Utumno | L2 | strcpy(argv[10]) aliases envp[8]: empty argv[0] via libc.execve, stack shellcode in the env value | recordings/utumno/L2.cast
Utumno | L3 | signed-char byte-write primitive: return address -> shellcode in argv[0]; shellcode reads the password file itself | recordings/utumno/L3.cast
Utumno | L4 | the length guard checks only 16 bits: 65599 passes and copies 65599 bytes, overwriting the return address at offset 65286 | recordings/utumno/L4.cast
Utumno | L5 | strncpy caps long strings at 20 bytes: ret is overwritten, shellcode stays in envp[8] | recordings/utumno/L5.cast
Utumno | L6 | signed table index -1 rewrites the strcpy destination pointer; argv[2] is parsed as hex | recordings/utumno/L6.cast
Maze | L0 | BLOCKED: maze0 login refused — maze.labs.overthewire.org answers ssh with 'Permission denied (publickey)', so password auth is not available for this game from this host. | (no recording)
Vortex | L0 | TCP service on vortex.labs.overthewire.org:5842: client written in vim (gcc) reads four little-endian uint32s, returns their sum, reply carries the vortex1 credentials; login verified | recordings/vortex/L0.cast
Vortex | L1 | BLOCKED (re-attempted 2026-11-03 with a systematic live prober, /vortex/vortex1 on port 2228). Swept on the live binary: A) filler 0..255 x backslash 0..260 x 0xca in each of the 4 word slots (3930 runs: 3923 ok, 7 SIGABRT); B) 0xca as 1st..4th word byte, backslash 0..299 (3000 runs: 2991 ok, 8 SIGSEGV, 1 rc1); C) NUL padding 0/1..12 before 0xca, filler 0/200/255 x backslash 0..278 (10080 runs: 10014 ok, 24 SIGSEGV, 42 SIGABRT); D) >512-byte writes after a walk (780 runs: 780 SIGABRT, stack canary); E) filler 0..510 x backslash 0..269 with a fresh baseline per filler (sweep in /tmp/vxfinal/n.py), 0 firings of the (p>>24)==0xca branch. Measured behaviour: a walk leaves buf unchanged when no byte is written between backslashes (buf[0..5] keep their initial 00 00 00 00 12 00), while 0xca typed after a walk and followed by a write IS stored (at buf[k]); so the check reads pointer state that survives untouched while writes accumulate. The typed 0xca can therefore only become the pointer's top byte if it lands on the pointer's own storage, and every construction tried (walk to each slot 0..16, NUL-shifted 0xca, null-word overwrite, EOF right after) left the run 'ok'. No shell, no password derived; old L1 row (never solved) stands as blocked. | (no recording)
Utumno | L7 | longjmp restores an attacker-controlled ebp inside the overflowed buffer; 144-byte payload keeps esp/eip intact | recordings/utumno/L7.cast
