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
Bandit | L25 | more->vi :shell escape on a tiny PTY | recordings/bandit/L25.cast
Bandit | L26 | clone git repo over ssh, read README | recordings/bandit/L26.cast
Bandit | L27 | git history leaks redacted password (HEAD~1) | recordings/bandit/L27.cast
Bandit | L28 | git branch -a, password on origin/dev | recordings/bandit/L28.cast
Bandit | L29 | git tag "secret" holds the password | recordings/bandit/L29.cast
Bandit | L30 | force-add ignored key.txt, push; hook prints password | recordings/bandit/L30.cast
Bandit | L31 | $0 breaks the uppercase restricted shell | recordings/bandit/L31.cast
Bandit | L32 | final level: README confirms game complete, no bandit34 | recordings/bandit/L32.cast
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
Natas | L16 | $(...) substitution oracle + binary search | recordings/natas/L16.cast
Leviathan | L3 | setuid level3 accepts snlprintf, spawns shell | recordings/leviathan/L3.cast
Leviathan | L4 | decode binary output of .trash/bin | recordings/leviathan/L4.cast
Leviathan | L5 | symlink /tmp/file.log to leviathan6 password | recordings/leviathan/L5.cast
Leviathan | L6 | read hardcoded code 7123 from disassembly | recordings/leviathan/L6.cast
Leviathan | L7 | final level: CONGRATULATIONS, no leviathan8 | recordings/leviathan/L7.cast
Krypton | L0 | Base64 decode of the level-page string | recordings/krypton/L0.cast
Krypton | L1 | ROT13 via tr | recordings/krypton/L1.cast
Krypton | L2 | Caesar chosen-plaintext oracle -> shift +12 | recordings/krypton/L2.cast
Krypton | L3 | monoalphabetic substitution: frequency + quadgram hill-climb | recordings/krypton/L3.cast
Krypton | L4 | Vigenere keylen 6: per-column chi-squared -> SERXRL, then ROT13 | recordings/krypton/L4.cast
Krypton | L5 | Vigenere unknown keylen: IC->9, per-column chi-squared->XRLYRATGU, then ROT13 | recordings/krypton/L5.cast
Krypton | L6 | chosen-plaintext recovers periodic LFSR keystream (period 30) | recordings/krypton/L6.cast
Krypton | L7 | final level: README confirms game complete | recordings/krypton/L7.cast
Manpage | L0 | BLOCKED: setuid bit not honored on lab host (euid stays manpage0 at main entry; /manpage/manpage0 is -r-sr-x--- manpage1:manpage0); the setuid(getuid()) drop makes the saved UID 17000, so the strcpy overflow cannot regain manpage1. Level appears bit-rotted upstream. | (no recording)
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
Natas | L17 | time-based blind SQLi: OR IF(cond,SLEEP(5)) fires per row (~20s true vs <1s false); binary search ORD(SUBSTR(password,pos,1)); len 32 | recordings/natas/L17.cast
Natas | L18 | brute-force PHPSESSID 1..640 (session_id=rand(1,640)); sid 119 is admin | recordings/natas/L18.cast
Natas | L19 | session id = bin2hex("<n>-admin"); brute-force n 1..640, found n=281 | recordings/natas/L19.cast
Natas | L20 | session-file injection: name="x\nadmin 1" adds an admin=1 line to the session | recordings/natas/L20.cast
Natas | L21 | colocated experimenter sets $_SESSION[key]=val; POST admin=1 then reuse PHPSESSID on main host | recordings/natas/L21.cast
Natas | L22 | ?revelio GET parameter alone prints credentials (no auth check) | recordings/natas/L22.cast
Natas | L23 | PHP loose comparison: "10111iloveyou" contains iloveyou and converts to 10111 > 10 | recordings/natas/L23.cast
Natas | L24 | passwd[]=x makes strcmp() receive an array -> NULL -> !NULL passes | recordings/natas/L24.cast
