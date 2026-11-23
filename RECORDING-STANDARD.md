# Recording Standard (OTW) — MANDATORY for every level cast

User rule (2026-11-23, repeated 3×): **every** level recording must be a *fully
legit, genuine, step-by-step interactive SSH session*. No scripted batch dumps,
no "mystery" files, no garbled output. A cast is acceptable ONLY if it meets ALL
of the following. Apply this to every new level AND to any re-record of an older cast.

## 1. The session MUST start with the SSH login, visible
- First thing in the cast: type the real login and let it succeed.
  `ssh <user>@<host> -p <port>` (or `-p` first), then the password prompt + password.
- We must see the MOTD / welcome banner, then the level's shell prompt.
- Do NOT open the cast already sitting at the level prompt.
- (For the very first level of a game where you log in from the client, show the
  client-side `ssh` too, then the hop.)

## 2. EVERY file you compile/run must be SHOWN being written in that session
- Before you `gcc x.c`, `python3 x.py`, `./exploit`, etc., the cast must show the
  file being created **in the same session, at the terminal**.
- Write it in **vim** (open, type the content, save) OR via a clearly-labeled
  heredoc: `cat > x.c <<'EOF'` … `EOF`. Either is fine; the code must be visible
  being entered, not appear from nowhere.
- Never run a script/binary whose source was never shown. If a prior level already
  wrote the file, re-create it in this session (or `cat` it and re-save) so the
  write is on record.
- The cast must show the file's content (the code), not just `python3 solve.py`.

## 3. Only real, terminal-legitimate commands
- Every line that looks like a command must be a command a person could actually
  type and run at that prompt. No pasted blocks of C/Python that render as if they
  were terminal output.
- Explanatory commentary = shell comments (`# …`) or `echo '…'` narration. A `#`
  line is fine and expected; it is a comment, not a command.
- No fake/placeholder tokens that aren't real commands.

## 4. Clean, readable exploit output — NO raw binary dumps
- If the exploit emits the password as plain text, show that.
- If the exploit emits binary (e.g. a 256-byte fwrite, a leaked struct), DO NOT
  dump raw bytes to the terminal. Pipe it to a clean reader:
  `… | xxd`, `… | strings`, `… | od -c`, or capture to a file then `cat`/`xxd` it,
  so the cast shows *readable* data (and the password is clearly visible).
- The target password must be unmissable in the cast (printed in clean text).

## 5. Verification is real
- Show the `id` / login-as-next-user / `cat /etc/<game>_pass/<next>` that proves
  the level was actually solved, with the password in clean text.

## Acceptance (re-audit before commit)
Before committing a cast, re-open it and confirm:
  [ ] opens with a typed ssh login + MOTD,
  [ ] every compiled/run file is shown being written (vim or heredoc),
  [ ] no raw-binary terminal dumps,
  [ ] only real commands + `#`/echo commentary,
  [ ] the next level's password is shown in clean text and login-verified.
If any box fails, re-record. Do not commit a cast that fails this standard.
