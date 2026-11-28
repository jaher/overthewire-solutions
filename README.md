# Wargames — OverTheWire + SmashTheStack

Solutions to **every OverTheWire wargame** plus the **SmashTheStack** missions, solved live on the lab servers from a DGX Spark. Each game ships a full writeup **and** a terminal replay of every level being solved — commands typed out live, the problem statement, the output, and the password it yields.

**Site:** https://jaher.github.io/overthewire-solutions/ — pick a game from the tier dropdown, pick a level, watch it being solved. (Repo will be renamed `wargames-solutions` to match the scope; the Pages URL moves to `https://jaher.github.io/wargames-solutions/` with the old URL redirecting.)

> **This README is kept in sync with the solves.** Every time a level or game is completed (or a blocker is resolved / re-opened), its status row below is updated in the same commit. The per-game `games/<game>.json` is the source of truth the site renders; this table is the human-facing mirror.

## OverTheWire games

| Game | Type | Levels | Status |
|---|---|---|---|
| Bandit | Linux basics over SSH | 0–33 | ✅ Complete (34/34) — L13 re-recorded 2026-11-28 (client-side key + key-auth ssh; the parked ptyrun2 @waitfor defect cleared) — [solutions](bandit-solutions.md) |
| Natas | Web security | 0–33 | ✅ Complete (34/34) — [solutions](natas-solutions.md) |
| Leviathan | Linux/binary basics | 0–7 | ✅ Complete (8/8) — [solutions](leviathan-solutions.md) |
| Krypton | Classical cryptography | 0–7 | ✅ Complete (8/8) — [solutions](krypton-solutions.md) |
| Manpage | Linux privilege basics | 0–4 done, L5 parked | ✅ L0–L4 complete (5/5), L5 **parked 2026-11-28** (residue frame map: the i-slot band below frame 1 is deterministic ld.so/libc startup data — 102/150 slots nonzero, zero attacker bytes, the only per-run random words miss every i-slot; LD_PRELOAD stripped on the setuid exec; no sibling euid-6 route; blocker = modern kernel+glibc leave nothing winnable — see `tools/manpage/L5_PARK.md`) — [solutions](manpage-solutions.md) |
| Narnia | Buffer overflows & shellcode | 0–9 | ✅ Complete (10/10) — [solutions](narnia-solutions.md) |
| Behemoth | Exploitation vs. mitigations | 0–7 | ✅ Complete (8/8) — [solutions](behemoth-solutions.md) |
| Utumno | Advanced exploitation / reversing | 0–7 | ✅ Complete (8/8) — [solutions](utumno-solutions.md) |
| Maze | Exploitation & format strings | 0–8 | ✅ Complete (9/9) — [solutions](maze-solutions.md) |
| Vortex | Classic exploitation | 0–13 | 🟡 L0–L12 complete (13/14); **L13 blocked** (kernel 7.0.0-1014 ≥5.18 fills the empty-argv hole → `argc==0` unreachable — re-derived 2026-11-28 with a fresh 4-angle investigation cast, all routes closed live); L0/L1/L2 casts re-recorded (standard-v2, replay PASS); L3 verified + replay PASS; L5 re-recorded (Rule-1 heredoc fixed) + replay PASS; L6 verified + replay PASS; L7 verified + replay PASS; **L8 verified + replay PASS** (s24 exploit restructured in-session: the Nov-16 transport was output-only, the uid pattern now sits at ~0xffffd190 — sweep widened to 0xffffd000-0xffffe000); **L9 verified + replay PASS** (mail-delivery level: no vi sessions by design, solve = /var/mail/vortex9 + vortex10 re-login); **L10 verified + replay PASS** (srand-seed reverse: C cracker vs the target's own libc rand, fresh rand window/seed exempted as run-to-run variables); **L11 re-recorded (Rule-1 heredoc fixed: h11.c typed in vim) + replay PASS**; **L12 re-recorded (Rule-1 heredocs fixed: drv12.c + the '%d' script typed in vim; the -T transport race re-proven live — the process-wide setresuid race wins over exec channels and loses in a pty) + Rule-4b PASS**; **L13 cast re-recorded (vi→vim, real park5.bin build, 3 vim sessions) + Rule-4b PASS**; **L4 replay PASS** — the vortex4/5 ssh-password "divergence" resolved 2026-11-28 as a throttle/lockout of the gotcha-(h) class: after a quiet period both chain passwords log in live; operator item withdrawn) — [solutions](vortex-solutions.md) |
| Drifter | New game, single level | 0 | ✅ L0 complete — cast in `recordings/drifter/` |
| FormulaOne | Race-condition / file exploits | 0–3 | ✅ Complete (4/4) — cast in `recordings/formulaone/` |
| Semtex | — | — | ⛔ Offline since 2022-08-16 (OTW-announced; live-verified) — skipped |

## SmashTheStack games

| Game | Type | Levels | Status |
|---|---|---|---|
| Blowfish | Beginner, binary | 0–13 | 🟡 L1–L13 recorded & solved (13/14); **L3 re-opened** (old verdict: level3 exec destroyed by a prior player — re-verifying on the live box); **L0 cast recorded + replay PASS**; **L2 JSON rebuilt cast-verbatim + replay PASS** (full MOTD outs, the 2→4 backdoor chain live in-replay); **L4–L8 JSONs rebuilt cast-verbatim + replay PASS each** (staged-vim editor sessions per gotcha g, buffers byte-verified against cast :wq markers; L4 strcpy ret+sled → yummy_bluntz, L5 VULN-env → ur_so_l33t, L6 jmp-esp → g00d_j0b, L7 ret2libc → w3ll_d0n3!, L8 fmt-string GOT → Ur_t3h_sh1t); **L2/L4–L8 Rule-7 narrations written + validated**; **L9–L12 JSONs rebuilt cast-verbatim + replay PASS each** (L9 race → error:U_sux0rZ, L10 PATH-hijack → phj33r_tuX, L11 strncpy-gate sweep → em_kcuF, L12 0xbf-filter → 0n3_m0r3.); **L13 JSON rebuilt cast-verbatim + replay PASS** (heap unlink, argc==0 execve → 0n3_m0r3.) — `recordings/blowfish/` |
| Logic | Intermediate | 1–3 | ✅ L1–L3 solved (3/3); L4+ unreachable (19 recon rounds as level3, no path; **host down 2026-11-28** — no route to logic.smashthestack.org:2224) |
| Blackbox | Advanced | 1–10 | 🟡 **UNBLOCKED 2026-11-28** (2026-11-26 lockout lifted): L2 solved (pw `PassFor2` = login2's strncmp-4 access code, login-verified) and L4 solved (pw `BashingSh`, from a player's `/dev/shm` artifact, login-verified); L3 attack running (getowner ret2libc brute over ~173 ASLR'd libc bases - an on-box sweep; our IP got kex-reset by the host mid-check, re-check next pass; **port 2225 kex-resetting again 2026-11-28 evening** while blowfish on the same IP works = the 2225 sshd is down/overloaded, not an IP ban); **L5 parked** — shared.cc's path filter proven airtight (exact-port sweep of 3^16 inputs), no other euid-level5 reader; re-check queue-pass items logged — [evidence](OTW-BLACKBOX-PROBE.md) |
| Tux | Intermediate | 0+ | ⏳ L0 parked — rate-limited box, `pfwd=/bin/cat` tunnel-only; re-checked 2026-11-28 (box up, pfwd answers, ircd challenge unchanged); re-check when a route to the ircd challenge appears |
| Amateria | Intermediate | 0+ | ⏳ L0 parked — admins patched the pickle service (re-confirmed 2026-11-28: service answers instantly, plain pickles sum fine, ALL global reduces fail fast; the published :89/level1.py has no filter = the running service differs from the published source) |
| APFEL | Beginner | — | ⛔ Offline — skipped until back online |

## How this repo is organized

- `index.html` — the terminal-replay site (dark shell, green type, human typing effect). Published to GitHub Pages by the Action in `.github/workflows/pages.yml` on every push to `main`.
- `games/<game>.json` — per-game replay data (levels, goals, commands, outputs, passwords); `games/manifest.json` lists the games the site offers in its tier dropdown. A game appears on the site as soon as its data lands here.
- `<game>-solutions.md` — the written solution per game (where one exists). Every level has its goal, the technique and why it works, the exact commands, the verification, and a **step-by-step discovery section** that walks the tooling as it was used: `file`, `strings`, `objdump` with the relevant instructions quoted, `gdb` measurements, `nasm`/`objcopy`/`xxd` for shellcode (the assembly source is shown in full), and the exploit source as it was written.
- `recordings/<game>/L<n>.cast` — the asciinema recording of each live solve; `recordings/index.html` is the player page that lists them all.
- `narration/<game>/L<n>.txt` — the spoken narration script for each level (the `.mp3` audio is delivered separately).
- `solves/` — the exploit sources, assembly files and helpers that the recordings build.
- `OTW-PROGRESS.md` — the running log of every level's technique and any blocker; the authoritative detail behind the table above.
