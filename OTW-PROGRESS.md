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
- Behemoth L1/L3/L6/L7: shellcode source (b1/b3/b7.asm 78-byte privilege-keeping shell, b6.asm 41-byte HelloKitty shell) now typed progressively in vim, `cat -n`'d, assembled locally with nasm and checked byte-for-byte against the recorded `xxd -p` (78/78/41/78 bytes). The exploit scripts (`e_behemothN.py`) were never captured in the recording and the behemothN accounts refuse logins as of 2026-11-03, so those steps are kept as the original capture and marked in the level transcript (not re-run, not faked).
- Utumno L1-L7: each level's shellcode (`l1.asm`, `sc.asm`) is now typed stage by stage into vim in the transcript and `cat -n`'d. The source is derived from that level's own recorded `objdump` listing and assembles, this run, to exactly the `xxd -p` line the original run printed (L1 86 bytes; L2-L7 the 78-byte marker shell for L2 and the 131-byte password-printing shell for L3-L7). The build steps (nasm, xxd, wc -c) carry this run's bytes; the exploit scripts (`e.py`) were not captured being written and their source is not reconstructed - those steps are marked as the original capture.
- Utumno L2 (open): live re-test 2026-11-04 on utumno2. The binary copies from the pointer at argv+0x28 compared against 0, not from argv[0]'s tenth character, so argc==1 with an ordinary path never passes ("Aw.."). Fifteen-plus exec shapes were tried on the live host (empty argv[0] via every ctypes exec path, a NULL-terminated argv, 10 and 31 entries, env strings as the ninth entry, an empty environment, a UTF-8 empty-name variable): all print "Aw.." and exit 1. Shape that passed: argv[0] = NULL (a hole at the base of argv; gdb reports argc=0) - utumno2 then exits by signal 11 once, and even with an unbounded address sweep no run prints PWN!, so the recorded "HIT at 0xffffdcd0" is not reproduced live and the transcript under this row describes what was recorded, not what was re-verified.
- Recorded-only (2026-11-04, user decision): Narnia L1-L8 and Behemoth L1-L7 are not re-verified end-to-end in this session, and will not be. Each level's code files are now typed into vim chunk by chunk in the transcript (Narnia retyped live on 2026-11-04 and byte-compared line for line against the original captures; Behemoth from the recorded sources), but the exploit/run steps keep the outputs of the original recordings. Re-running them against the lab is not possible any more: the post-login passwords of the accounts used below (narnia5-L7's accounts, all behemoth accounts) no longer authenticate, so a re-run would need credentials this repo does not have. The transcripts say so on the affected steps; the levels remain solved as recorded.
- Vortex L1: re-attacked 2026-11-04 at maximum effort. Binary re-derived live (world-readable, md5 a7a17e3c…): the branch checks (p>>24)==0xca BEFORE each byte is stored, so a byte can only fire it if the cursor already holds 0xca - and 0xca000000 is ~770 MB below the buffer, while the getchar hook turns every byte >=0xc0 into EOF. Every emitted byte also executes: ecx=0x8048392+c, eax=GOT[c>>2], ebx=0x804bff8+c, jmp [0x804c2f4+3c] read relative to ebp=0, i.e. the fake frame at 0xffffd000-4d; no store on that path is reachable from emitted bytes, so input cannot change the frame. Structured model in tools/vortex1_model.py finds no firing input. Live evidence (objdump of main, the hook, trap traces) recorded in the level transcript. Remains BLOCKED; write-up in vortex-solutions.md.
- Vortex L1 SOLVED (2026-11-04): 261 backslashes walk the cursor to 0xffffdc04 (8 bytes above the saved frame pointer) and four raw 0xca bytes written over a pipe (the getchar hook filters keyboard-style bytes >=0xc0, not piped ones) make the top byte 0xca and fire the branch; shell as uid=5002, /etc/vortex_pass/vortex2 read live, login as vortex2 verified. The earlier 17.8k prober runs missed it because they typed 0xca (hook) and used wrong backslash counts.
- Vortex L2 (open): live investigation 2026-11-04 under the public-write-up relaxation. vortext statement "Create a special tar file": vortex2 (setuid vortex3) builds /bin/tar argv from a fixed "cf /tmp/ownership.$$.tar" slot plus a copy of our argv[0]; measured live (PATH fake-tar probe, controlled-env execve, argv0 padding sweep 0-7, stdin-fed -T -, --checkpoint-action): tar's argv past the first copy is uninitialised garbage, tar dies 'Cannot stat'/EFAULT, and a fake tar on PATH is called at most once per process. No input reaches the fixed options slot, so no tar option (e.g. checkpoint-action) can be triggered. Public write-ups were then searched (maket000/vortex-writeups, livz/otw-vortex, gggal/over-the-wire; official source overthewire.org/wargames/vortex/vortex2.c) and their technique re-tested live: the published argv (vortex2 --checkpoint=1 '--checkpoint-action=exec=...' /vortex/vortex2) creates the fixed /tmp/ownership.$$.tar (vortex3-owned, readable, holds /vortex/vortex2) and tar reports 'Write checkpoint' when no action is given, but the action never runs (marker file not created), even with excess args, split flag/value, both spellings, -T -, or an action fed on stdin; an emulated exact execv of the published source does run the action, so the difference is in the wrapper's build, which cannot be traced (gdb: 'exited normally' with no exec, ptrace_scope 1). The decoy route gives the same tar archive every time, not a password. Not marked blocked (user decision).
- Vortex L2 (still open, 2026-11-05): new angles tested live - (1) invoking vortex2 through /lib/ld-linux.so.2 so the setuid bit is dropped and the same wrapper executes with real (not garbage) argv: it still exits 0 silently and no checkpoint action fires, so the dead end is in vortex2's own execve, not in privileges; (2) direct invocation with 0/1/2/3 args: 2 args make the wrapper's fixed "cf /tmp/ownership.$$.tar" copy run tar (rc 2, Cannot stat) - i.e. the wrapper copies argv[1], argv[2] into tar's option positions only when they exist, so only a tar OPTION can ever reach a position before the file operand, and a 3rd arg is always the vortex3-faulted tail (strace EFAULT); (3) /tmp is world-writable but not readable by vortex2, and no writable dir is visible, so nothing can be planted ahead of tar's fixed absolute archive path. Evidence transcript in games/vortex.json L2 (6 progressive vim steps for why.py). Not marked blocked.
- Vortex L2 (still open, 2026-11-05, -T route): with TWO arguments the wrapper reaches the real tar and our argv[1]/argv[2] land in two OPTION slots after "cf /tmp/ownership.$$.tar" (`tar cf <archive> <opt1> <opt2>`). Tested live: `-T /vortex/vortex2` (tar reads the list as data, hits "file name read contains nul character" and waits), `-T -` with a list on stdin (archives /vortex/vortex2; stdin lines are never options), `--files-from` same, `-T '--checkpoint=1 --checkpoint-action=...'` (one literal name, Cannot stat), `--use-compress-program=/vortex/vortex2`, `-I`, `--owner` (no file operand -> "refusing to create an empty archive"). No route makes tar invoke a program: options only exist before the file list, and vortex2 is only ever a name inside data. TAR_OPTIONS reaches the real tar but this tar build refuses any value ("non-option arguments in TAR_OPTIONS"), same for plain /bin/tar. Transcript in games/vortex.json L2.
