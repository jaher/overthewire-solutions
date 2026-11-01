# OverTheWire Krypton — Solutions

Live solves against `krypton.labs.overthewire.org:2231` in this run. Krypton is about classical
cryptography; each level's material is under `/krypton/krypton<n>/`. For each level: goal,
technique and why it works, exact commands, verification. Recordings in `recordings/krypton/L<n>.cast`.

Verification: each password was accepted by logging in as the next level's account.
---
## Level 0 → krypton1
- **Account:** `krypton0`. The level page itself gives the first credential: the string `S1JZUFRPTklTR1JFQVQ=` "encodes the password using Base64".
- **Goal:** Decode the Base64 string to obtain the password for krypton1.
- **Technique and why it works:** Base64 is a reversible encoding of bytes into an ASCII alphabet; `base64 -d` decodes it back. Decoding `S1JZUFRPTklTR1JFQVQ=` yields `KRYPTONISGREAT`. No key or cryptanalysis is involved — this is just an encoding step.
- **Commands:**
  ```
  echo S1JZUFRPTklTR1JFQVQ= | base64 -d
  ssh krypton1@krypton.labs.overthewire.org -p 2231      # password KRYPTONISGREAT
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the challenge statement.** Krypton has no shell on level 0 beyond the level page: the page itself gives the string `S1JZUFRPTklTR1JFQVQ=` and says it is Base64-encoded.
2. **Recognise the format.** A trailing `=` is Base64 padding, and the alphabet used is `A–Z a–z 0–9 + /`. Base64 is an *encoding*, not encryption: every byte maps to 4/3 of a character, and decoding restores the exact bytes.
3. **Decode it with the standard tool.**
   ```
   echo S1JZUFRPTklTR1JFQVQ= | base64 -d
   # KRYPTONISGREAT
   ```
   `echo` supplies the trailing newline the tool expects; `-d` selects decode mode. The output is the password for krypton1, and it is a plain English phrase, which confirms the decode worked.
4. **Verify by logging in.**
   ```
   ssh krypton1@krypton.labs.overthewire.org -p 2231     # password KRYPTONISGREAT
   whoami                                                 # krypton1
   ```
- **Password for krypton1:** `KRYPTONISGREAT`
- **Verification:** logged in as `krypton1` with this password.
- **Recording:** `recordings/krypton/L0.cast`

## Level 1 → krypton2
- **Account:** `krypton1`.
- **Goal:** `/krypton/krypton1/krypton2` holds the password for krypton2, encrypted with ROT13 (per the README).
- **Technique and why it works:** ROT13 shifts each letter by 13 positions, half the alphabet, so applying it twice returns the original text — it is its own inverse. `tr 'A-Za-z' 'N-ZA-Mn-za-m'` performs the shift on both cases. The file `YRIRY GJB CNFFJBEQ EBGGRA` decodes to `LEVEL TWO PASSWORD ROTTEN`.
- **Commands:**
  ```
  cat /krypton/krypton1/krypton2
  cat /krypton/krypton1/krypton2 | tr 'A-Za-z' 'N-ZA-Mn-za-m'
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the README.** `/krypton/krypton1/README` explains that the password for level 2 is in the file `krypton2`, encrypted with ROT13, and warns about the "non-standard ciphertext format" — the file keeps the plaintext's word boundaries, so word shapes survive.
2. **Look at the ciphertext.**
   ```
   cat /krypton/krypton1/krypton2
   YRIRY GJB CNFFJBEQ EBGGRA
   ```
   Three-letter, three-letter, eight-letter, six-letter — the shape of "LEVEL TWO PASSWORD ROTTEN" even before decoding. That shape check is a useful sanity test for a substitution cipher.
3. **Apply ROT13 with `tr`.** ROT13 maps A↔N, B↔O, ..., M↔Z; it is its own inverse because 13 is half of 26. `tr` takes two sets and maps positionally:
   ```
   cat /krypton/krypton1/krypton2 | tr 'A-Za-z' 'N-ZA-Mn-za-m'
   LEVEL TWO PASSWORD ROTTEN
   ```
   The two ranges in the second argument are the alphabet rotated by 13, and handling both cases in one call avoids a second pass.
4. **Read off the password.** The sentence literally states it: `ROTTEN`.
5. **Verify.**
   ```
   ssh krypton2@krypton.labs.overthewire.org -p 2231      # password ROTTEN
   whoami                                                 # krypton2
   ```
- **Password for krypton2:** `ROTTEN`
- **Verification:** logged in as `krypton2` with this password.
- **Recording:** `recordings/krypton/L1.cast`

## Level 2 → krypton3
- **Account:** `krypton2`.
- **Goal:** `/krypton/krypton2/krypton3` holds the password for krypton3, encrypted with a Caesar cipher. The key is in `keyfile.dat` (unreadable), but a setuid-`krypton3` `encrypt` program encrypts any file we give it.
- **Technique and why it works:** A Caesar cipher is a fixed shift over the alphabet. Rather than brute-forcing all 26 shifts, we use the oracle with a chosen plaintext: encrypt the alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ` and read `ciphertext`. The result is `MNOPQRSTUVWXYZABCDEFGHIJKL`, which shows the mapping A→M, i.e. a shift of +12 (not the ROT13 one might assume). Decrypting the target therefore means shifting by −12, which `tr 'A-Z' 'O-ZA-N'` does. `OMQEMDUEQMEK` becomes `CAESARISEASY`. The setuid binary needs to read `keyfile.dat` from our working directory, so we create a directory in `/tmp`, symlink the keyfile into it, make the directory traversable for krypton3, and run the binary there.
- **Commands:**
  ```
  cat /krypton/krypton2/krypton3                 # OMQEMDUEQMEK
  D=$(mktemp -d); cd "$D"
  ln -s /krypton/krypton2/keyfile.dat; chmod 777 .
  printf 'ABCDEFGHIJKLMNOPQRSTUVWXYZ\n' > p.txt
  /krypton/krypton2/encrypt p.txt; cat ciphertext   # MNOPQRSTUVWXYZABCDEFGHIJKL => shift +12
  cat /krypton/krypton2/krypton3 | tr 'A-Z' 'O-ZA-N'   # CAESARISEASY
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the README and list the directory.** The README explains the setup: `encrypt` reads `keyfile.dat` from the *current directory*, runs setuid krypton3, and therefore needs krypton3 to be able to reach our directory. That last sentence tells us exactly how to make the oracle usable:
   ```
   ls -l /krypton/krypton2/
   # -rwsr-x--- 1 krypton3 krypton2  encrypt
   # -rw-r----- 1 krypton2 krypton2  keyfile.dat
   # -rw-r----- 1 krypton3 krypton3  krypton3
   ```
2. **Look at the ciphertext.**
   ```
   cat /krypton/krypton2/krypton3
   OMQEMDUEQMEK
   ```
   Twelve letters, no spaces — consistent with a Caesar shift over a single alphabet.
3. **Build a working directory the setuid binary can use.** `/tmp` is world-writable, but a `mktemp -d` directory is mode 700, so krypton3 could not traverse it. The recipe is: create the directory, symlink the keyfile into it (so the binary finds it in its cwd), and `chmod 777` the directory:
   ```
   D=$(mktemp -d); cd "$D"
   ln -s /krypton/krypton2/keyfile.dat
   chmod 777 .
   ```
4. **Feed it a chosen plaintext.** This is the key idea of a Caesar break with an oracle: instead of trying 26 shifts, encrypt the alphabet once and read the mapping directly.
   ```
   printf 'ABCDEFGHIJKLMNOPQRSTUVWXYZ\n' > p.txt
   /krypton/krypton2/encrypt p.txt
   cat ciphertext
   MNOPQRSTUVWXYZABCDEFGHIJKL
   ```
   A→M is a shift of **+12**, not the ROT13 one might assume. The output also shows the alphabet wraps cleanly, confirming it is a Caesar shift and not a general substitution.
5. **Invert the shift.** Encryption added 12, so decryption subtracts 12 — which is `tr 'A-Z' 'O-ZA-N'` (the alphabet starting at O):
   ```
   cat /krypton/krypton2/krypton3 | tr 'A-Z' 'O-ZA-N'
   CAESARISEASY
   ```
   The plaintext is a phrase that names the cipher and states the password: `CAESARISEASY`.
6. **Verify.**
   ```
   ssh krypton3@krypton.labs.overthewire.org -p 2231      # password CAESARISEASY
   whoami                                                 # krypton3
   ```
- **Password for krypton3:** `CAESARISEASY`
- **Verification:** logged in as `krypton3` with this password.
- **Recording:** `recordings/krypton/L2.cast`

## Level 3 → krypton4
- **Account:** `krypton3`.
- **Goal:** `/krypton/krypton3/krypton4` holds the password for krypton4, encrypted with a simple (monoalphabetic) substitution cipher. We also have `found1`, `found2`, `found3` — intercepted English messages encrypted with the same key.
- **Technique and why it works:** A monoalphabetic substitution maps each plaintext letter to one ciphertext letter, so letter frequencies are preserved. Counting letters across all the intercepted text gives S≈13%, Q≈9.6%, J≈8.5%, U≈7.3%, B≈7.0% — the shape of English (E,T,A,O,I,N,...). A frequency-based initial mapping plus a hill-climb that swaps plaintext assignments to maximise the quadgram log-likelihood of the decrypted corpus recovers the full key. The recovered plaintext of `krypton4` reads "WELL DONE THE LEVEL FOUR PASSWORD IS BRUTE", giving the password `BRUTE`. (The same hill-climb also recovers the found-texts' plaintext, an Alice-in-Wonderland passage.)
- **Commands:**
  ```
  cat /krypton/krypton3/found1 /krypton/krypton3/found2 /krypton/krypton3/found3 /krypton/krypton3/krypton4
  # frequency count, then hill-climb substitution with quadgram scoring (script in the recording)
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the README.** It states the crucial facts: the plaintexts are **English**, and all the messages were produced with the **same key**. For a monoalphabetic substitution those two facts are enough to break the cipher without any oracle.
2. **Collect the material.** Four files: three intercepted messages and the target.
   ```
   cat /krypton/krypton3/found1 /krypton/krypton3/found2 /krypton/krypton3/found3 /krypton/krypton3/krypton4
   ```
   The recording saves this to `/tmp/k3.txt` on the solving machine so the Python tools can read it repeatedly.
3. **Count the letters.** Because a monoalphabetic substitution maps each plaintext letter to exactly one ciphertext letter, the *frequency profile* of the ciphertext is the English profile, just with the names changed:
   ```
   python3 - <<'PY'
   import collections
   t = open('/tmp/k3.txt').read()
   letters = ''.join(c for c in t if c.isupper())
   freq = collections.Counter(letters)
   print(' '.join(f'{c}:{100*n/len(letters):.1f}%' for c, n in freq.most_common(10)))
   PY
   # S:13.0% Q:9.6% J:8.5% U:7.3% B:7.0% N:6.8% C:6.4% G:6.4% D:5.9% V:3.8%
   ```
   Compare with English (`E 12.7, T 9.1, A 8.2, O 7.5, I 7.0, N 6.7, S 6.3, H 6.1, ...`): the ranking matches almost one-for-one. That gives an initial guess S→E, Q→T, J→A, U→O, B→I, N→N, ...
4. **Score candidate plaintexts with quadgrams.** Letter frequencies alone get you close but leave ambiguities. A better objective is how *English-like* the decrypted text is: split it into 4-letter groups and sum the log-probabilities of those groups from a reference corpus.
   ```
   quad = collections.Counter(corpus[i:i+4] for i in range(len(corpus)-3))
   def qscore(s): return sum(math.log((quad[s[i:i+4]]+1)/tot) for i in range(len(s)-3))
   ```
   Real English text scores far higher than random letter assignments, so maximising this score is equivalent to finding the key.
5. **Hill-climb the mapping.** Start from the frequency guess, then repeatedly swap two plaintext assignments and keep the swap if the score improves. Restarting from the best result a few times avoids local maxima:
   ```
   for r in range(20):
       cur = dict(best); cs = bs
       for it in range(3000):
           a, b = random.sample(abc, 2); nm = dict(cur); nm[a], nm[b] = nm[b], nm[a]
           sc = qscore(dec(nm))
           if sc > cs: cur, cs = nm, sc
       if cs > bs: best, bs = cur, cs
   ```
   (`random.seed(3)` makes the run reproducible; the recording prints the same answer every time.)
6. **Read the target's plaintext.** Decoding `krypton4` with the recovered mapping gives
   ```
   K4 plaintext: WELLD ONETH ELEVE LFOUR PASSW ORDIS BRUTE
   ```
   — i.e. "WELL DONE THE LEVEL FOUR PASSWORD IS BRUTE". The same mapping also decrypts the found texts (an Alice-in-Wonderland passage), which is the cross-check that the key is right and not just locally plausible.
7. **Take the password.** `BRUTE`.
8. **Verify.** `ssh krypton4@... -p 2231` with `BRUTE` → `whoami` prints `krypton4`.
- **Password for krypton4:** `BRUTE`
- **Verification:** logged in as `krypton4` with this password.
- **Recording:** `recordings/krypton/L3.cast`

## Level 4 → krypton5
- **Account:** `krypton4`.
- **Goal:** A Vigenère cipher with a 6-letter key; `found1` and `found2` are two long intercepted English messages, and `krypton5` holds the next password encrypted with the same key.
- **Technique and why it works:** In a Vigenère cipher each plaintext letter is shifted by the key letter at that position, cycling every 6 characters. So the ciphertext splits into 6 interleaved Caesar ciphers — one per key position — each of which can be attacked by frequency analysis. We take each found text separately (each message restarts at key offset 0), split it into 6 columns, and pick the shift per column that best matches English letter frequencies (chi-squared). Both texts independently give the key `SERXRL`, confirming it. The README's example uses the convention C = P + K (mod 26), so decryption is C − K. Decrypting `HCIKV RJOX` with `SERXRL` yields `PYRNEGRKG`, which is itself ROT13 — applying ROT13 gives `CLEARTEXT`.
- **Commands:**
  ```
  cat /krypton/krypton4/found1; cat /krypton/krypton4/found2
  # per-position chi-squared key recovery -> SERXRL; Vigenere-decrypt krypton5, then ROT13
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the README and the worked example.** The README shows a Vigenère encryption step by step (plaintext numbers + key numbers mod 26 = ciphertext numbers) and states two gifts: the key length is **6**, and the password is in `krypton5`.
2. **Collect the two messages.** Each is a long English text, and — importantly — each message restarts at key offset 0:
   ```
   cat /krypton/krypton4/found1; echo; echo ---; cat /krypton/krypton4/found2
   ```
3. **See why a Vigenère falls to frequency analysis.** With key length 6, position `i` is shifted by key letter `i mod 6`. Taking every 6th character (`text[k::6]`) yields a *single* Caesar cipher per column. Six Caesar ciphers can each be broken independently.
4. **Break each column with chi-squared against English frequencies.** For each column, try all 26 shifts, decrypt, and pick the shift whose letter distribution is closest to English:
   ```
   def dec_col(col, sh): return ''.join(chr((ord(c)-sh) % 26 + 65) for c in col)
   key = [min(range(26), key=lambda sh: chi(dec_col(L[k::K], sh))) for k in range(K)]
   ```
   where `chi` compares the observed percentages with `{'E':12.7, 'T':9.1, 'A':8.2, ...}`.
5. **Check the result against both texts.** The recording prints
   ```
   keys: ['SERXRL', 'SERXRL']
   ```
   Two independently-derived messages agreeing on the same six letters is strong evidence the key is right.
6. **Decrypt the target.** The README's convention is `C = P + K (mod 26)`, so decryption is `C − K`:
   ```
   def dec(s, k): return ''.join(chr((ord(c)-ord(k[i % len(k)])) % 26 + 65) for i, c in enumerate(s))
   ```
   Applying it to the letters of `krypton5` (`HCIKV RJOX`) gives
   ```
   vig  : PYRNEGRKG
   ```
   That is not readable English — a second layer. `PYRNEGRKG` is `CLEARTEXT` under ROT13, so the level's text is ROT13-encoded *after* the Vigenère. Applying ROT13:
   ```
   rot13: CLEARTEXT
   ```
   The layered encoding is the lesson: decrypt in the reverse order of encryption, and check each layer for readability.
7. **Verify.** `ssh krypton5@... -p 2231` with `CLEARTEXT` → `whoami` prints `krypton5`.
- **Password for krypton5:** `CLEARTEXT`
- **Verification:** logged in as `krypton5` with this password.
- **Recording:** `recordings/krypton/L4.cast`

## Level 5 → krypton6
- **Account:** `krypton5`.
- **Goal:** A Vigenère cipher with an *unknown* key length; `found1`–`found3` are English messages encrypted with the same key, and `krypton6` holds the next password.
- **Technique and why it works:** First determine the key length. The index of coincidence (IC) of a text shifted by the key length measures how close each column's letter distribution is to English; computing the average column IC for each candidate length 1–30 peaks at 9 (with multiples 18 and 27), so the key is 9 letters. Then treat each of the 9 columns as a Caesar cipher and pick, per column, the shift whose decrypted column best matches English letter frequencies (chi-squared). All three found texts independently give `XRLYRATGU`, confirming the key. Decrypting `krypton6` with that key gives `ENAQBZ`, which is ROT13; ROT13 gives `RANDOM`.
- **Commands:**
  ```
  cat /krypton/krypton5/found1 /krypton/krypton5/found2 /krypton/krypton5/found3
  # IC over key lengths 1..30 -> 9; per-column chi-squared -> key XRLYRATGU
  # Vigenere-decrypt krypton6, then ROT13
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the README.** It says the key length is now **unknown** and points at frequency analysis; the level's only extra material is `found1`–`found3` plus the target `krypton6`.
2. **Collect all four texts.**
   ```
   cat /krypton/krypton5/found1 /krypton/krypton5/found2 /krypton/krypton5/found3 /krypton/krypton5/krypton6
   ```
3. **Find the key length before anything else.** The index of coincidence measures how uneven the letter distribution is. For a text of English letters it is about 0.066; for random letters about 0.038. Averaging the IC of the 6 (or k) interleaved columns and scanning k = 1..30 gives a spike exactly at the true key length (and at its multiples, because every multiple also aligns the columns):
   ```
   def ic(s):
       f = collections.Counter(s); n = len(s)
       return sum(v*(v-1) for v in f.values()) / (n*(n-1))
   print(sorted(((round(sum(ic(L[k::K]) for k in range(K))/K, 4), K) for K in range(1, 31)), reverse=True)[:5])
   # [(0.0479, 9), (0.0478, 18), (0.0475, 27), (0.0445, 30), (0.0445, 24)]
   ```
   The top three are 9, 18 and 27 — multiples of 9 — so the key is **9** letters.
4. **Break each of the 9 columns as a Caesar cipher.** Same chi-squared approach as level 4, but now applied to each found text separately:
   ```
   keys = [''.join(chr(65+min(range(26), key=lambda sh: chi(dc(t[k::9], sh)))) for k in range(9)) for t in texts]
   # ['XRLYRATGU', 'XRLYRATGU', 'XRLYRATGU']
   ```
   All three texts agree independently — that is the confirmation step.
5. **Decrypt the target and check for a second layer.** Vigenère-decrypting `krypton6` (`BELOSZ`) with `XRLYRATGU` gives `ENAQBZ`, which is not English but is valid ROT13; ROT13 gives
   ```
   vig: ENAQBZ   rot13: RANDOM
   ```
6. **Verify.** `ssh krypton6@... -p 2231` with `RANDOM` → `whoami` prints `krypton6`.
- **Password for krypton6:** `RANDOM`
- **Verification:** logged in as `krypton6` with this password.
- **Recording:** `recordings/krypton/L5.cast`

## Level 6 → krypton7
- **Account:** `krypton6`.
- **Goal:** The setuid `encrypt6` binary encrypts a file using a secret `keyfile.dat` plus a weak "random" keystream (HINT2: an 8-bit LFSR). Recover `krypton7`'s password.
- **Technique and why it works:** Disassembly of `encrypt6` shows the cipher per letter: it uppercases, maps to 0–25, and outputs `(lfsr + key[i % 10] + (P − 0x41) − 0x41) mod 26` — i.e. a Vigenère-style addition of a 10-byte key plus an LFSR byte, with the LFSR advanced once per output letter. Because the LFSR is deterministic and periodic, a chosen-plaintext attack recovers the combined offset: encrypt 600 `A`s, subtract `A` from each output, and the resulting sequence has period 30. Decrypting `krypton7` with that periodic offset gives `LFSRISNOTRANDOM`. (The period is 30 because the 8-bit LFSR's maximal cycle is 255, and combined with the 10-letter key cycling the effective pattern repeats; empirically the period observed is 30 for this keyfile.)
- **Commands:**
  ```
  D=$(mktemp -d); cd "$D"; chmod 777 .
  ln -s /krypton/krypton6/keyfile.dat
  python3 -c 'open("p.txt","wb").write(b"A"*600)'
  /krypton/krypton6/encrypt6 p.txt o.bin
  # offset[i] = (o.bin[i]-65) mod 26 ; find period (30); decrypt krypton7 with it
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Read the material.** The README says the encryption uses `keyfile.dat` **and a "random" number**, and that the generator is weak. The hints narrow it down:
   ```
   cat /krypton/krypton6/HINT1     # "The 'random' generator has a limited number of bits, and is periodic."
   cat /krypton/krypton6/HINT2     # "8 bit LFSR"
   ```
   `ls -l` also shows `keyfile.dat` is owned by krypton7 and unreadable to us, while `encrypt6` is setuid krypton7.
2. **Disassemble the encryption loop.** This is what turns the hints into an exact formula:
   ```
   objdump -d -M intel /krypton/krypton6/encrypt6 | sed -n '/<main>:/,/ret/p'
   ```
   Reading the loop (`1471`–`153c`):
   ```
   146c: call lfsr                          ; first keystream byte, before the loop
   1487: call fgetc                          ; read one plaintext byte
   1495: call toupper                        ; uppercase it
   149d: cmp BYTE PTR [rbp-0x41],0x20        ; spaces are skipped
   14c0: and eax,0x400                       ; isalnum-style check (alpha class)
   14cd: sub eax,0x41                        ; letter -> 0..25
   14e3: add edx,eax                         ; key[i % len] + (P - 0x41)
   14e8: add eax,edx                         ; + lfsr
   14ea: sub eax,0x41                        ; - 0x41  (i.e. mod 26 arithmetic)
   14f2: sub eax,0x1a                        ; wrap into 0..25
   1506: add eax,0x41                        ; back to 'A'..'Z'
   1519: call fputc                          ; write the ciphertext byte
   1534: call lfsr                           ; advance the LFSR once per letter
   ```
   So `C = (key[i % 10] + (P − 'A') + lfsr) mod 26`, and the LFSR advances once per emitted letter. The key is 10 bytes (`cmp DWORD PTR [rbp-0x38],0x9` limits the keyfile read to 10 bytes).
3. **Look at the LFSR itself.** `objdump` of `lfsr` shows a 16-bit shift register with a feedback bit formed by XORing bit 0 with bit 1, shifted in at bit 3, and the *full register value* returned each time:
   ```
   12b7: movzx eax,WORD PTR [rip+...]  # reg
   12c1: sar eax,1                     # reg >> 1
   12c5: movzx eax,WORD PTR [rip+...]  # reg
   12cc: xor eax,edx ; and eax,1       # feedback = (reg ^ (reg>>1)) & 1
   12d5: movzx eax,WORD PTR ... ; shr ax,1 ; or eax,(fb<<3)  # shift in at bit 3
   ```
   The state space is small, so the sequence must repeat — which is why a chosen-plaintext attack works.
4. **Do a chosen-plaintext attack.** Set up a working directory the setuid binary can use (same recipe as level 2 — symlink the keyfile, `chmod 777 .`), then encrypt 600 `A`s:
   ```
   D=$(mktemp -d); cd "$D"; chmod 777 .
   ln -s /krypton/krypton6/keyfile.dat
   python3 -c 'open("p.txt","wb").write(b"A"*600)'
   /krypton/krypton6/encrypt6 p.txt o.bin
   ```
   Because `P − 'A'` is 0 for every byte, each ciphertext byte is exactly `(key[i % 10] + lfsr) mod 26` — the combined keystream, with no plaintext mixed in.
5. **Extract the keystream and find its period.**
   ```
   off = bytes((b - 65) % 26 for b in open("o.bin","rb").read())
   for P in range(1, 300):
       if all(off[i] == off[i % P] for i in range(len(off))):
           print("period", P); break
   ```
   The recording prints
   ```
   period 30 K: [4, 8, 2, 19, 3, 6, 24, 8, 24, 25, 10, 19, 7, 13, 18, 8, 17, 5, 23, 24, 2, 15, 5, 20, 4, 14, 2, 10, 17, 13]
   ```
   30 is `lcm(10, 6)`: the 10-byte key cycles every 10, and the LFSR's 8-bit-derived state cycles every 6 in this configuration, so the combined pattern repeats every 30.
6. **Decrypt the target with the recovered keystream.**
   ```
   ct = [b for b in open("/krypton/krypton6/krypton7","rb").read() if 65 <= b <= 90]
   pt = bytes(65 + ((ct[i]-65-off[i % P]) % 26) for i in range(len(ct)))
   print("krypton7 plaintext:", pt)
   # b'LFSRISNOTRANDOM'
   ```
   The plaintext is the phrase that names the flaw — an LFSR is not a random source.
7. **Verify.** `ssh krypton7@... -p 2231` with `LFSRISNOTRANDOM` → `whoami` prints `krypton7`.
- **Password for krypton7:** `LFSRISNOTRANDOM`
- **Verification:** logged in as `krypton7` with this password.
- **Recording:** `recordings/krypton/L6.cast`

## Level 7 — final level
- **Account:** `krypton7`.
- **Goal:** Confirm the game is complete.
- **Technique and why it works:** krypton7 is the final account. `/krypton/krypton7/README` reads "Congratulations on beating Krypton!" and there is no krypton8 account, so the game ends here. Nothing to exploit; this is the end marker.
- **Commands:**
  ```
  ssh krypton7@krypton.labs.overthewire.org -p 2231
  cat /krypton/krypton7/README
  ```
### Step-by-step discovery and crafting (what the recording shows)
1. **Log in as krypton7** with the password recovered at level 6 (`LFSRISNOTRANDOM`).
2. **List the level directory.**
   ```
   ls -la /krypton/krypton7
   # -r--r----- 1 krypton7 krypton7 36 README
   ```
   There is only a README — no further binary and no further password file.
3. **Read it.**
   ```
   cat /krypton/krypton7/README
   Congratulations on beating Krypton!
   ```
4. **Confirm the chain ends.** There is no krypton8 account to log in as, so the game is complete.
- **Password for krypton8:** none — the game ends at krypton7.
- **Verification:** login as krypton7 succeeds; the README confirms completion.
- **Recording:** `recordings/krypton/L7.cast`

