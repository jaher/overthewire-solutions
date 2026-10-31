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
