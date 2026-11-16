import hashlib, itertools, string, os, time
TARGET = bytes.fromhex('155fb95d04287b757c996d77b5ea51f7')
ALNUM = string.ascii_letters + string.digits

def crack_chunk(letters, wfd):
    for L in range(1, 5):
        for first in letters:
            for t in itertools.product(ALNUM, repeat=L-1):
                s = first + ''.join(t)
                if hashlib.md5(s.encode()).digest() == TARGET:
                    os.write(wfd, s.encode() + b'\n'); return
    for first in letters:
        for t in itertools.product(ALNUM, repeat=4):
            s = first + ''.join(t)
            if hashlib.md5(s.encode()).digest() == TARGET:
                os.write(wfd, s.encode() + b'\n'); return
    try:
        os.write(wfd, b'-\n')
    except OSError:
        pass

if __name__ == '__main__':
    t0 = time.time()
    chunks = [list(ALNUM[i::8]) for i in range(8)]
    rfd, wfd = os.pipe()
    pids = []
    for ch in chunks:
        pid = os.fork()
        if pid == 0:
            os.close(rfd)
            crack_chunk(ch, wfd)
            os._exit(0)
        pids.append(pid)
    os.close(wfd)
    found = None
    with os.fdopen(rfd, 'rb') as f:
        for line in f:
            v = line.strip()
            if v and v != b'-':
                found = v.decode(); break
    for pid in pids:
        os.waitpid(pid, 0)
    print('FOUND:', found, 'in %.1fs' % (time.time()-t0))
