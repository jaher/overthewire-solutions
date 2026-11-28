# CLAUDE.md — standing rules for this repo (read before ANY level work)

You are recording OverTheWire / SmashTheStack wargame solves as live, verbatim
terminal sessions. The user's non-negotiable standard: **a replay of the
recording must reproduce the real session character-for-character — same
typed commands, same editor sessions, same output, same final state.**

**Vortex (L0–L13) is the standing quality benchmark.** Every game, every
level, every re-record must meet that bar: the full step-by-step process of
developing the exploit, real in-session vi/vim editing on the machine,
verbatim outputs, and an educational narration that teaches the solve. A
level that shows only the final exploit running — without the development
process that produced it — does not meet the standard.

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
- **Every single character of input and output must actually solve the real
  level on the machine.** No decorative commands, no pre-built artifacts
  carried in, no steps that exist only for the transcript: the whole
  character stream, replayed verbatim on the server, is what solves the
  level.

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

## Rule 4 — Verification before commit (POST-SOLVE, verbatim, against the real server)
- After recording a level: (a) the cast ends in a live solve; (b) the
  `games/<game>.json` steps for that level are replayed AGAINST THE REAL
  SERVER in a fresh live pty session, and **every character of input and
  output must match the real session verbatim — including the vi/vim
  editing done on the machine**: the replay's editor session is driven
  character-by-character exactly as the cast typed it, must land on the same
  buffer (byte-identical to the cast's buffer, confirmed by the same `:wq`
  `N L, M C` marker), and the run must reach the same solved state. There is
  no byte-check-only escape hatch: a level whose steps cannot be verified
  verbatim against a live session on the server is re-recorded, not patched
  around; (c) narration sync/segments step indices
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

## Rule 9 — Step-by-step process, vortex quality (user rule 2026-11-26)
- A level must SHOW THE WHOLE PROCESS OF DEVELOPING THE EXPLOIT, step by
  step — not jump from login to the final exploit firing. The standard
  shape (the vortex L0–L13 reference): login → recon (the real discovery
  steps, in the order taken) → vulnerability analysis (disassembly,
  offsets, what the bytes mean) → exploit design (including the probes and
  iterations that were actually run, with their real outputs) → code
  written in vi on the machine → build → run → verification (real `id`,
  real password, real next-level login).
- Every phase must be present in the cast, in the JSON replay, and in the
  narration (Rule 7), in the same order, at the same quality as vortex.
  Short levels compress phases; they do not delete them (a level whose
  "recon" is one `ls` still shows that `ls` and its full output, and the
  narration explains why it is the whole recon).
- Educational is the point: after the level, a reader who saw ONLY the
  cast + narration can reproduce the exploit development from scratch —
  they know what each step found, why the next step was chosen, and what
  the bytes on screen mean.


## Standing rule — log corrections (user 2026-11-26)
- When a defect in a cast, JSON, or narration is found and fixed, ask: is
  the lesson generalizable? If yes, add it to this file (new rule or a note
  on the rule it extends) in the SAME commit, so the next recording follows
  it without being told again. If it is a one-off or a site/tooling defect
  (e.g. the `vimFileOf` regex only matching `vim`, the OSC-greedy ESCRE bug),
  fix it where it lives and leave a one-line note here only if it can bite
  again. Do not pad this file with trivia; a rule earns its place by being
  violated once.
- Recorded-run debugging discipline (added 2026-11-26, from maze L2): when
  a recorded run's behavior contradicts the intended script, DO NOT
  re-record blind — first diff the actual on-machine file (`cat f`) against
  the intended buffer inside the failed cast itself. The two recurring
  causes are both silent: (a) editor corruption of the typed buffer (vim's
  auto comment-leader/indent; now neutralized in ptyrun2's @vi setup with
  `formatoptions=`), and (b) the shell stripping NUL bytes from a binary
  payload passed through command substitution (`$(cat sc.bin)`) or shell
  variables — assemble NUL-free encodings at the SOURCE (asm imm8 forms,
  printable path dwords) instead of filtering after the fact. A payload
  that must survive a shell round-trip is NUL-free by construction, not
  by filtering. The same diff-first rule catches driver bugs: a
  `@waitfor` directive with only two fields, or a stage window that missed
  because the payload size changed, shows up as stage1-miss lines in the
  failed cast — read them before touching the recorder.
- Driver-script gotchas (added 2026-11-26, from maze L5's five attempts):
  (a) `@waitfor <token> <rest>` splits on SPACES — a token containing
  spaces ("Yeh, here's your shell") makes ptyrun2 treat the token's tail
  as the rest field and TYPE it into the freshly spawned shell (the cast
  showed `$ here's your shell` and a `>` continuation prompt). Tokens must
  be a single word; pick a distinctive single word from the expected output.
  (b) After a solve spawns an interactive shell, exiting needs one exit per
  layer PLUS a second exit when bash prints "There are stopped jobs." (the
  level binary sits behind as a stopped job; the first exit only warns).
  Count the layers before typing: spawned shell → remote shell (warning →
  second exit) → client shell. One exit too many types the next command
  into a dead pty — its echo appears with no output, which is the signature.
  (c) A `@waitfor` token must not appear in any SOURCE TEXT typed before the
  awaited event: the typed buffer is part of the same stream, so waiting for
  "HIT" fired on the exploit's own print("HIT buf", ...) line while it was
  being typed into vi, and the follow-up commands landed inside the editor.
  Pick a token that exists only in the awaited output (e.g. the password the
  run prints), never one that occurs in code, comments, or prompts.
  (d) After a LARGE-buffer `:wq` (65+ lines), settle before typing the next
  command: put `@sleep 4` between `@viend` and the following `@line`. The
  drain can return on prompt-lookalike output while vim is still tearing
  down (restoring the terminal, releasing the tty), and vim then eats the
  typed-ahead line - the driver logs the directive as sent, the cast shows
  no echo, and the remote shell never sees it (formulaone L3 replays 1-2:
  gcc vanished after the 66-line f1l3.c save; attempt 3 with the sleep
  passed). Small buffers race less because vim exits faster; the sleep is
  cheap insurance for any vi session over ~50 lines.
  (e) An exploit's address sweep is calibrated to the environment it was
  measured in and does NOT transfer: the landing address shifts by hundreds
  of bytes between an ssh-exec env and the ptyrun2 session env (manpage L4:
  0xffffd940 via ssh exec, 0xffffd0b8 under ptyrun2 - the first recording's
  sweep range missed entirely and the cast ran the sweep silently to no
  result). Sweep wide (or re-measure the landing IN the recording
  environment) before recording.
  (f) The tty line discipline changes what an exploit can do: manpage L4's
  sprintf overflow reaches the return slot only when stdin is a PIPE (a pty
  run exits cleanly, the ret slot untouched). If a recorded run behaves
  differently from a manual run, test the pipe-vs-tty delivery path too -
  and note that a pipe run loses the interactive echo, so the JSON `out`
  comes from the subprocess's captured stdout, not the pty.
  (g) The site only renders a staged vim screen when the JSON step cmd
  matches /^vim\s+(.+)$/ (index.html vimFileOf): type `vim <file>` in the
  recording, never `vi <file>` - `vi` steps render as plain commands with
  fragmented partial output instead of ONE continuous editor session
  (vortex L4's vim sc.asm/ex6.py/gen.py is the reference appearance;
  maze L4's four `vi tinel.py` steps had to be re-recorded as a single
  `vim tinel.py` session, 2026-11-28 user correction).
  (h) The lab throttles ssh auth by source after several failures: a failed
  recording (wrong password, driver bug typing garbage at the login prompt)
  locks out the NEXT attempts for minutes - and the lockout looks like a
  password rotation (maze4/maze3/maze2 all "Permission denied" right after a
  botched run, then the same passwords work again after a quiet period).
  Before re-deriving passwords or assuming a lab reset, STOP connecting for
  ~10 minutes and retry once; never fire rapid retry probes - each denied
  attempt extends the lockout. Also: a failed session that dumps the whole
  vi buffer into the CLIENT shell is the signature of ptyrun2 never entering
  the editor (login failed), not a driver-file defect.
  (i) ptyrun2 @line types through the REMOTE shell: anything the remote bash
  would expand at a prompt gets expanded in the typed command - an unquoted
  `$$.tar` became `<pid>.tar` on the wire (vortex L2 cast 1: "ownership.3.tar").
  Quote literal dollar/backslash/asterisk payloads in @line strings exactly as
  you would at a real prompt, and verify the archive/file names in the cast
  before accepting the run.
  (j) On chain levels the LOGIN password and the LEVEL-OUTPUT password are
  different: account N's login password is level N-1's output (vortex3 logs
  in with L2's xRMRVus8g, NOT L3's output TlI5kxGd1 = vortex4's password).
  A replay that auth-fails with "Permission denied" on the FIRST password
  prompt is a wrong LOGIN password until proven otherwise - probe the login
  alone (`ptyrun2 ... 'id'`) before suspecting lab rotation or the driver;
  the pre-auth MOTD banner prints regardless of auth outcome, so a banner in
  the output is NOT a successful login.
  (k) A program that reads a prompt interactively (getpass etc.) will EAT the
  next @line's bytes as its input if nothing is fed at the prompt: the
  symptom is a garbled first-read echo (vortex L5: getpass read the following
  'exit' as the password; the binary's '<lastchar>:<hex>' debug print decoded
  it). Every prompt-consuming step needs a "feed" (waitfor token + typed
  answer + anchored follow-ups) in the JSON so gen_ptyrun2 emits the waitfor
  BEFORE the next command.
  (l) A long-running step (crack, sweep) also eats the next @line: type-ahead
  lands in the running process's stdin and executes when it exits, killing
  the session plan. ptyrun2's @line now WAITS FOR THE PROMPT after each
  command (fixed at the driver level, vortex L6) - do not reintroduce blind
  sleeps. A waitafter cascade that waits for the NEXT command's output
  deadlocks (waitfor blocks BEFORE typing that command); waitafter tokens
  must come from the CURRENT step's own output only.
  (m) Replays leave artifacts in the LAB workdir (v6, ex.py, /tmp/l6rec/*) -
  a killed run's leftovers break re-runs (cp 'Permission denied' on the
  stale file in the sticky /tmp). Clean the lab workdir (a one-shot
  ptyrun2 rm pass) before every replay launch, and make the first JSON
  step idempotent (rm -f) where the cast shows it.

## Standing rule — never stop until all levels are solved (user 2026-11-27)
- The mission is ALL levels, ALL games, solved and shipped. A parked line, a
  blocked line, or a 6h timebox is a pause, never an ending: keep working.
- When a level is stuck, work it in this order:
  1. Re-derive the facts on the machine first - the binary, kernel, or lab
     config may have changed; re-measure before re-using any old verdict
     (e.g. re-check the lab kernel before re-asserting an L13-style block).
  2. Research the internet: public write-ups, level hints, CVEs, kernel
     behavior changes, forum threads. **Internet hint research is explicitly
     authorized** - use it whenever a level is stuck or a technique is
     unclear.
  3. Try genuinely new angles (new primitives, new entry points, timing,
     races, the environment, the wrapper programs around the level binary).
  4. Only then park - and a park must name the EXACT external blocker (lab
     offline, operator credentials needed, a lab-host-side change) plus when
     to re-check it.
- Park re-checks are part of the work, not optional: on every pass through
  the queue, re-probe each parked level with a cheap live check; any change
  in conditions (kernel, DNS, auth, rate limit, binary md5) immediately
  reopens the level.
- **"Unreachable" is a hypothesis, never a verdict (user 2026-11-28).**
  Levels the user considers solvable — "unreachable" ones included. When a
  level was marked unreachable (no path from the current account, no
  entry point, dead end), that claim must be re-derived from scratch, not
  inherited: (a) re-read the level's own page/write-up for hints the
  previous pass missed; (b) re-audit the *entire* attack surface, not just
  the level binary — sibling accounts, cron, other games' binaries on the
  host, web interfaces, file permissions, environment, the wrapper around
  the level, and every account you can already read as a foothold; (c)
  search the internet for that exact level (write-ups, forums, GitHub) —
  techniques for the same level often exist that the prior pass never
  considered; (d) try a different *entry account* if the game allows
  multi-account access. A level stays "unreachable" only with current,
  dated, per-route evidence that the specific route is closed *today* —
  and even then it is re-probed on every queue pass.

## Standing rule — parallel subagents for independent levels (user 2026-11-28)
- If it is possible to solve two levels in parallel, do it: when the
  current level is waiting on a long background task (sweep, replay,
  rate-limit cooldown) and another level is INDEPENDENT — different game
  and/or different lab host, no shared files — delegate it to a subagent
  (Task tool) while the main turn keeps working its own level.
- Discipline for parallel work:
  - One level per agent, end-to-end: record -> JSON -> Rule-4b verbatim
    replay -> audit -> commit. A subagent does not hand back a half-cast.
  - **Never `git add -A` while another agent may be mid-work.** Stage only
    this level's paths (`recordings/<game>/L<n>.*`, `games/<game>.json`,
    `narration/<game>/L<n>.*`, plus the README/OTW-PROGRESS rows for this
    level). Before committing, `git status`; if the index lock is busy,
    wait and retry.
  - Re-read `README.md` / `OTW-PROGRESS.md` from disk immediately before
    editing them (never from cached context), so a parallel agent's row
    update in the same file is not clobbered.
  - Never run two live lab sessions on the SAME lab host in parallel
    (rate-limit / auth lockout — already seen once with maze2). One live
    pty per host, always.
  - The parent verifies each subagent's commit against the normal gates
    (Rule 4 post-solve verbatim replay, audit, README sync) on its next
    turn before treating that level as done.

## Standing rule — keep README.md in sync with solved levels (user 2026-11-28)
- Every level (or game) that is completed, or whose blocker state changes
  (solved, parked, re-opened, unblocked), updates the status row in
  `README.md` in the SAME commit as the work. The per-game JSON is the
  source of truth; the README table is the human-facing mirror and must
  never lag it.
- When resuming a session or finishing a queue pass, diff the README
  against the actual per-game JSON state (solved level counts, missing
  passwords, cast coverage) and fix any drift in the same commit.

See RECORDING-STANDARD.md for the full v2 standard; this file adds the
character-exact fidelity and vi-everywhere rules (user, 2026-11-25) and the
vortex-quality step-by-step + post-solve verbatim rules (user, 2026-11-26).
