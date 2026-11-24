# Wargames — OverTheWire + SmashTheStack, all solved

Solutions to **every OverTheWire wargame** plus **all SmashTheStack missions**, solved from a DGX Spark ("DGX 5"). Each game gets a full writeup and a terminal-replay of every level being solved — commands typed out live, with the level's problem statement, the output, and the password it yields.

**Site:** https://jaher.github.io/overthewire-solutions/ — pick a game from the tier dropdown, pick a level, watch it being solved. (Repo will be renamed `wargames-solutions` to match the scope; the Pages URL moves to `https://jaher.github.io/wargames-solutions/` with the old URL redirecting.)

**Scope extension (2026-11-24):** all [smashthestack.org](https://www.smashthestack.org/) wargames are now in scope — Tux, Logic, Blackbox, Blowfish, Amateria (APFEL is offline; CTF excluded). They are in `games/` and the site dropdown as stubs with live-verified connection details, and are being solved/recorded alongside the OverTheWire games.

## Games

| Game | Type | Levels | Status |
|---|---|---|---|
| Bandit | Linux basics over SSH | 0–33 | ✅ Complete — [solutions](bandit-solutions.md) |
| Natas | Web security | 0–34 | ✅ Complete — [solutions](natas-solutions.md) |
| Leviathan | Linux/binary basics | 0–7 | ✅ Complete — [solutions](leviathan-solutions.md) |
| Krypton | Classical cryptography | 0–6 | ✅ Complete — [solutions](krypton-solutions.md) |
| Manpage | Linux privilege basics | 0–6 | ⛔ Blocked — setuid bit not honoured on the lab host; documented in OTW-PROGRESS.md |
| Narnia | Buffer overflows & shellcode | 0–9 | ✅ Complete — [solutions](narnia-solutions.md) |
| Behemoth | Exploitation vs. mitigations | 0–7 | ✅ Complete — [solutions](behemoth-solutions.md) |
| Utumno | Advanced exploitation / reversing | 0–7 | ✅ Complete — [solutions](utumno-solutions.md) |
| Maze | Exploitation & format strings | 0–8 | ✅ Complete (L0–L8 + final) — [solutions](maze-solutions.md) |
| Vortex | Classic exploitation | 0–25 | ⛔ Partial — L0–L12 solved; L13 kernel-blocked (see OTW-PROGRESS.md) |

## SmashTheStack wargames

| Game | Type | Levels | Access (live-verified 2026-11-24) | Status |
|---|---|---|---|---|
| Blowfish | Beginner, binary | 1–13 | `ssh levelN@blowfish.smashthestack.org` (port 22, OpenSSH 5.3); entry pw via telnet :6666 (encrypted) | In scope — not yet started |
| Tux | Intermediate | 0–7+ | `ssh levelN@tux.smashthestack.org -p 2226`; entry: `ssh -L 6667:0:6667 -p 2226 pfwd@…` (pw `pfwd`) then `nc localhost 6667` | In scope — not yet started |
| Amateria | Intermediate | 0–7+ | `ssh -p 2229 levelX@amateria.smashthestack.org`; L0 remote (source on web, no outbound) | In scope — not yet started |
| Logic | Intermediate | 1–11+ | L1 is web (port 8181); then `ssh -l levelN logic.smashthestack.org -p 2227` | In scope — not yet started |
| Blackbox | Advanced | unknown | `ssh -l levelN blackbox.smashthestack.org -p 2225` (legacy OpenSSH 4.3); web page (:85) is down | In scope — not yet started |
| APFEL | Beginner | — | offline | Skipped until back online |

## How this repo is organized

- `index.html` — the terminal-replay site (dark shell, green type, human typing effect). Published to GitHub Pages by the Action in `.github/workflows/pages.yml` on every push to `main`.
- `games/<game>.json` — per-game replay data (levels, goals, commands, outputs, passwords); `games/manifest.json` lists the games the site offers in its tier dropdown. A game appears on the site as soon as its data lands here.
- `<game>-solutions.md` — the written solution per game. Every level has its goal, the technique and why it works, the exact commands, the verification, and a **step-by-step discovery section** that walks the tooling as it was used: `file`, `strings`, `objdump` with the relevant instructions quoted, `gdb` measurements, `nasm`/`objcopy`/`xxd` for shellcode (the assembly source is shown in full), and the exploit source as it was written.
- `recordings/<game>/L<n>.cast` — the asciinema recording of each live solve; `recordings/index.html` is the player page that lists them all.
- `narration/<game>/L<n>.txt` — the spoken narration script for each level (the `.mp3` audio is delivered separately).
- `solves/` — the exploit sources, assembly files and helpers that the recordings build.
