# Recording Standard (OTW) — MANDATORY for every level cast

User rule (2026-11-23/24, stated repeatedly): **every** level recording must be a *fully
legit, genuine, step-by-step LIVE interactive SSH session* against the real server.
No scripted batch dumps, no "mystery" files, no garbled output, no offline
reconstruction. A cast is acceptable ONLY if it meets ALL of the following. Apply
this to every new level AND to any re-record of an older cast.

## 0. LIVE + VERBATIM (user rule 2026-11-24)
- Every cast is recorded **against the live server, in real time** — the pty/
  asciinema session IS the attack session. Do NOT re-type or reconstruct a past
  session offline.
- The terminal must **mirror exactly what happens on the level**: the exact
  commands that actually solve the mission, in the order they actually run, with
  real output.
- The code written in vi must be **verbatim** — the exact source that was verified
  to solve the level. No paraphrasing, no "cleaned-up" rewrites, no placeholders.
  If the exploit changed during development, the cast shows the final working
  version and the cast's own run proves it (the level is actually solved inside
  the cast).
- Lab quirk: home dirs are read-only ("Write-access to homedirectories is
  disabled"). `gcc` from `$HOME` aborts (can't create temp files). Always
  `mktemp -d` / `cd` into /tmp first, then compile there.

## 1. The session MUST start with the SSH login, visible
- First thing in the cast: type the real login and let it succeed.
  `ssh <user>@<host> -p <port>` (or `-p` first), then the password prompt + password.
- We must see the MOTD / welcome banner, then the level's shell prompt.
- Do NOT open the cast already sitting at the level prompt.
- (For the very first level of a game where you log in from the client, show the
  client-side `ssh` too, then the hop.)

## 2. EVERY file you compile/run must be SHOWN being written in **vi**, in that session
- Before you `gcc x.c`, `python3 x.py`, `./exploit`, etc., the cast must show the
  file being created **in the same session, in vi**.
- Write it with **vi/vim**: `vi file.c` → press `i` → the full code (with any
  comments) is typed into the editor → `Esc` → `:wq`. The editor session must be
  visible: the vi startup, the buffer with the code being entered, the save.
  (Driver: ptyrun2.py `@vi FILE` … code lines … `@viend`; verified live
  2026-11-24 — writes the file byte-exact, rendered session matches the vortex-
  cast style. Reference: `recordings/vortex/L3.cast`, a real `vim sc.asm` session.)
- The code must be REAL and SOLVE THE LEVEL: the exact commands/source that were
  verified to work on the live level — not placeholders, not rewrites that differ
  from what actually solved it (§0 verbatim). Re-run the final solve step in the
  cast to prove it (the cast's own run must produce the password / next shell).
- Never run a script/binary whose source was never shown. If a prior level already
  wrote the file, re-create it in this session's vi so the write is on record.
- The cast must show the file's content (the code), not just `python3 solve.py`.
- **Heredocs (`cat > f <<'EOF'`) are NO LONGER acceptable for exploit code — vi only.**

## 3. Only real, terminal-legitimate commands — no terminal-side commentary
- Every line typed at the shell prompt must be a real command a person could run.
  No pasted blocks of C/Python that render as terminal output, no bare lines.
- **Comments belong INSIDE the file** (in the vi buffer — `//`, `#`, `/* */` as
  appropriate to the language), shown being typed in the editor.
- **Do NOT put explanatory comments in the terminal** as bare `#` lines or
  `echo '# …'` narration (user rule 2026-11-24: terminal comments that are not
  executable commands are not legitimate). Keep the shell transcript clean:
  login → read/analyze (real commands) → vi write (code+comments in the editor)
  → compile/run → verify. If a short label is truly needed, `echo 'text'`
  WITHOUT a leading `#` and without pretense of commentary is acceptable, but
  prefer zero terminal commentary.

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

## 6. REPLAYABLE TRANSCRIPT (user rule 2026-11-24) — games/*.json steps
- The `steps` array in `games/<game>.json` (what the site player renders and
  replays with narration highlighting) is a **script**: it must be a full,
  complete solution on the remote machine. Someone typing EXACTLY those steps,
  verbatim, in that order, on the live lab, must reach the solved state — every
  keystroke must work, no placeholders, no elided commands (no `printf 'AAAA...'`,
  no `cp ... `, no `# (see notes)` steps standing in for the real work).
- **All code is written in vi in the transcript too**: file creation steps use the
  staged `vim file` + `vim <keystroke>` lines (vortex L4 cast style: empty buffer
  first, buffer growing chunk by chunk, finished buffer, then the compile/run).
  The staged-vim convention (empty buffer → chunks → finished, `tools/editor_audit.js`)
  must hold for every level.
- **Every level is REPLAYED against the live server to prove it**: a harness takes
  the steps, drives a real pty session on the lab (ssh login + each typed line,
  verbatim), and checks the final output/password. A level is only "done" when its
  own transcript replays to a solve. Revisit ALL levels (old and new) for this —
  any step that doesn't verbatim-work on the live server must be fixed in the JSON,
  the cast, and the docs until the replay passes.
**Every `.py` executed, `.c`/`.cc` compiled, `.asm` assembled has a vim-writing session** (user rule 2026-11-25, all levels, all games): the replay (games/*.json) must show the code being written in vi — never just `python3 x.py` / `gcc x.c` for a file whose source was never shown. Audit 2026-11-25 (repo-wide): utumno L1-L7 e.py fixed in 59d7ac9 (L7 also had a duplicated nasm/objdump/objcopy build — a replay must NOT repeat a build step verbatim; the JSON mirrors the cast 1:1). Known remaining defects — fix as each level is revisited (cast has the session, JSON omits it: behemoth L1-L7 e_behemothN.py, formulaone L0 solve.py + L2 attack.c, krypton L2 k2crypt.py, maze L4 tinel.py + L6 sc.py; krypton L4/L5/L6 vim steps are PLACEHOLDERS, no screen; cast has NO writing session: drifter L0 exploit.py, maze L7 gen.py/fire.py, natas L26 n26jar.py, utumno L0 dump.c, vortex L11 h11.c + L12 drv12.c/build12.py (heredocs — vi re-record needed), vortex L13 (in-scope per L13 work); manpage L0-L4 have no casts at all).
- Vi sessions in the transcript must look as good as the vortex levels (esp. L4):
  real editor chrome (line numbers / `~` rows where the player renders them), the
  keystrokes shown (i, Esc, :wq), the buffer content visible as it is typed.

## Acceptance (re-audit before commit)
Before committing a cast, re-open it and confirm:
  [ ] opens with a typed ssh login + MOTD,
  [ ] LIVE + verbatim: recorded in real time against the live level; the cast's
        own run solves it; code is the exact verified source (§0),
  [ ] every compiled/run file is shown being written IN VI (vi open → i → code
        visible being typed → :wq) — no heredocs,
  [ ] no raw-binary terminal dumps,
  [ ] the shell transcript is clean: only real commands; NO bare `#` comment
        lines and NO `echo '# …'` terminal commentary (comments are in the file),
  [ ] the next level's password is shown in clean text and login-verified.
If any box fails, re-record. Do not commit a cast that fails this standard.
