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

