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
Bandit | L11 | ROT13 via tr | recordings/bandit/L11.cast
Bandit | L12 | peel xxd/gzip/bzip2/tar layers with file | recordings/bandit/L12.cast
Bandit | L13 | ssh private key, log in to bandit14 from client (localhost hop blocked) | recordings/bandit/L13.cast
Bandit | L14 | pipe current password into nc localhost:30000 | recordings/bandit/L14.cast
Bandit | L15 | SSL submission with openssl s_client to localhost:30001 | recordings/bandit/L15.cast
