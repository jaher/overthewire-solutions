# CLAUDE.md — standing rules for this repo (read before ANY level work)

You are recording OverTheWire / SmashTheStack wargame solves as live, verbatim
terminal sessions. The user's non-negotiable standard: **a replay of the
recording must reproduce the real session character-for-character — same
typed commands, same editor sessions, same output, same final state.**

## Rule 1 — Every code file is typed in vi, in the session
- ANY file whose contents matter to the solve — `.py`, `.c`, `.cc`, `.asm`,
  `.s`, shell scripts, exploit text — is created **in vi within the same
  live session**: `vi <file>` → `i` → the full source (comments included)
  typed into the buffer → Esc → `:wq` → the `:wq` "N L, M C written" marker
  visible.
- No heredocs (`cat > f <<EOF`), no `cp` from a pre-existing file, no file
  that appears without its vi session. If a helper file was developed
  earlier, its **final working version** is re-typed in vi in this cast.
- The vi session is visible end-to-end: editor chrome, buffer growing as
  lines are typed (ptyrun2 `@vi`/`@viend` blocks), the save marker.
- Applies to every game, every level, every re-record — including files
  that look trivial (a 5-line probe still gets a real vi session).

## Rule 2 — Character-exact fidelity to the live session
- The cast is recorded live against the real server. It must show **exactly
  what happened**: every character typed at the prompt, every line of
  output, in the real order. No elision, no "…", no paraphrased output,
  no hand-edited post-processing of the raw stream.
- If output is long (objdump disassembly, file listings), show the real
  output. You may pipe the real command through `grep`/`sed`/`head`/`tail`
  (that is a legitimate part of the session and must be shown as typed),
  but you may not invent, shorten, or "clean up" what the server returned.
- The cast's own run must SOLVE the level inside the cast (real `id`,
  real `cat /pass/…` with the real password visible). A cast that doesn't
  end in a verified solve is discarded and re-recorded.

## Rule 3 — The replay (games/*.json) mirrors the cast 1:1
- `steps[]` is a replayable script: typing every step, verbatim, in order,
  in a fresh live pty session on the real server must reproduce the same
  terminal behavior and reach the same solved state (same prompt, same
  euid, same password shown).
- JSON editor steps use the **real editor command the cast typed** — the
  casts use `vi`, so JSON steps say `vi <file>` (the site's `vimFileOf`
  accepts both `vi` and `vim`). Staged-screen convention: empty buffer,
  buffer growing in chunks (≤ ~26 lines of visible buffer each), finished
  buffer, then the build/run.
- One vi session per file = one contiguous run of staged steps in the JSON.
  Never repeat a build step the cast only shows once; never omit a vi
  session the cast contains. The JSON is a 1:1 mirror of the cast —
  including placeholder-free: every editor step carries a real screen
  (numbered lines + `~` rows), never a prose summary in `out`.
- Command strings in the JSON must be the real command (full ssh options,
  real flags) — but they may be the *session* form, not the client's
  pre-ssh `export PS1` lines, which belong to the recording harness, not
  the replay.

## Rule 4 — Verification before commit
- After recording a level: (a) the cast ends in a live solve; (b) the
  `games/<game>.json` steps for that level replay against the live server
  (or are byte-checked with the site's own parseVimScreen/buildVimScript
  when a full live replay is impractical: 0 clears, 0 edits, final buffer
  == the cast's `:wq` byte count); (c) narration sync/segments step indices
  re-keyed if steps were inserted/removed; (d) `python3 tools/audit_verbatim.py <game>`
  is run and every finding is resolved: rebuild the `out` verbatim from the
  cast (or re-record the level) — or, if it is a tool false positive
  (client-side content, 80-col wrap, staged vi screen), mark it as such in
  the commit message.
- Then commit (one commit per level, message naming the level + technique +
  password source). Do NOT `git push` — the operator pushes from the host.

## Rule 5 — No gaps: every level, contiguous, all solved
- Every level of a game gets its own entry in `games/<game>.json`, numbered
  contiguously over the GAME's own level sequence (L0, L1, L2, … Lmax) —
  no missing numbers, no silent skips. Client-side levels (telnet, decrypt,
  any pre-ssh work) are real levels too: record them as client-side casts
  (asciinema of the local terminal) and give them their own entries.
- If a level appears unreachable on the live server, STOP and report to the
  operator with the evidence — never skip a number quietly, and never mark
  an unsolved level solved.

## Rule 6 — The replay mirrors the cast EXACTLY: no more, no less, nothing different
The one test for any JSON step's `out`: **every line in it must be a line
the terminal actually displayed during that step** (whitespace-normalized;
80-column soft wraps joined back into one line). If a line was not on the
terminal screen, it does not belong in `out` — no matter how useful it is.
- **No redundant commands (no MORE):** each command is typed exactly as often
  as the real session typed it. A build/analysis shown ONCE in the cast
  appears ONCE in the JSON — no repeated objdump/objcopy/nasm blocks, no
  duplicate probe commands, no filler re-runs. One vi session per file = one
  contiguous run of staged steps. A JSON step that adds no new information
  relative to the cast is a defect. The replay is the cast, not a superset of
  it.
- **No elisions (no LESS):** the step's output must be the FULL
  cast-verbatim output — every line the terminal printed, in order. No `...`
  elisions, no abridged snippets (e.g. `char buf[256]; ... strcpy(buf,
  argv[1]);` is a defect), no "(N more lines)" summaries, no dropped tail
  lines. Long outputs (objdump, file listings, full MOTD/banner) are shown in
  full. (user rule, 2026-11-25)
- **No annotation (nothing DIFFERENT):** no author commentary in `out` — no
  parentheticals explaining the step (e.g. `(ASLR off -> fixed libc base)`,
  `(55-byte NUL-free shellcode)`), no paraphrased or "cleaned-up" output, no
  abbreviated editor state. Editor steps carry the real staged screens
  (numbered lines + `~` rows + status line, per Rule 3) and the session's
  last step ends with the `:wq` save marker EXACTLY as the terminal printed
  it — `"/dev/shm/e_bf6.py" [New] 37L, 1132C written`, never a shorthand
  `[New] written`. If a step needs a description, it goes in the level's
  `note` field or the narration transcript (Rule 7) — never in `out`.
- **Enforcement:** run `python3 tools/audit_verbatim.py <game>` before
  committing (Rule 4d). It cross-checks every `out` line against the cast
  stream (ABSENT / ELISION / OMITTED findings). No level commits with
  unresolved findings.

## Rule 7 — Educational transcript: every level gets a step-by-step explanation
- Every level ships a narration transcript — `narration/<game>/L<n>.segments.json`
  (the source of truth) plus the built `L<n>.mp3` + `L<n>.sync.json` from
  `python3 tools/build_narration.py <game> <n>` — and it must read as a
  **teaching explanation of the solve**, not a caption track.
- Structure: (a) a goal segment naming the level and what it requires;
  (b) one spoken segment per phase in the order the session runs — login,
  recon, vulnerability analysis, exploit design, code written in vi, build,
  run, verification; (c) a closing segment with the flag/password.
- The explanation must answer WHY: what each command is for, what the
  output reveals (e.g. "buf sits at ebp-0x108, so the saved return address
  is 268 bytes into the payload"), and how the pieces connect into the
  exploit. A reader listening ONLY to the transcript should understand how
  the level was solved, without reading the terminal.
- Every segment's `lines` refs anchor it to the real typed lines (step
  index + role, out-lines by index range) so the site highlights each line
  as it is spoken — no segment floats free of the transcript, and the
  builder's warnings (commands never anchored) must be reviewed and cleared.
- Tone: conversational, first-person, concrete numbers/addresses/offsets
  as they appear on screen. No "as we can see here" filler, no terminal-
  side commentary duplicated as text — the narration explains, the terminal
  shows.
- Levels added or re-recorded get their transcript in the SAME commit.
  A level without an educational transcript is not done.

## Rule 8 — Repo hygiene
- Casts: `recordings/<game>/L<n>.cast`; driver scripts stay in the
  recording container (`/tmp/<game>_scripts/`); sources extracted from a
  cast must byte-match its `:wq` marker (N L, M C) before use.
- Keep `solves/` in sync only when a level's final source changes.
- Do not touch the model endpoint or the CCR bridge; no `git push`;
  commit after each level.

See RECORDING-STANDARD.md for the full v2 standard; this file adds the
character-exact fidelity and vi-everywhere rules (user, 2026-11-25).
