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
- **Password for krypton4:** `BRUTE`
- **Verification:** logged in as `krypton4` with this password.
- **Recording:** `recordings/krypton/L3.cast`

