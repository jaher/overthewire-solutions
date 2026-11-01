# OverTheWire — all wargames, solved

Solutions to **every OverTheWire wargame**, solved from a DGX Spark ("DGX 5"). Each game gets a full writeup and a terminal-replay of every level being solved — commands typed out live, with the level's problem statement, the output, and the password it yields.

**Site:** https://jaher.github.io/overthewire-solutions/ — pick a game from the tier dropdown, pick a level, watch it being solved.

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
| Maze | Exploitation & format strings | 0–9 | ⛔ Blocked — ssh password auth refused by the host |
| Vortex | Classic exploitation | 0–26 | ⛔ Blocked — ssh password auth refused by the host |

## How this repo is organized

- `index.html` — the terminal-replay site (dark shell, green type, human typing effect). Published to GitHub Pages by the Action in `.github/workflows/pages.yml` on every push to `main`.
- `games/<game>.json` — per-game replay data (levels, goals, commands, outputs, passwords); `games/manifest.json` lists the games the site offers in its tier dropdown. A game appears on the site as soon as its data lands here.
- `<game>-solutions.md` — the written solution per game. Every level has its goal, the technique and why it works, the exact commands, the verification, and a **step-by-step discovery section** that walks the tooling as it was used: `file`, `strings`, `objdump` with the relevant instructions quoted, `gdb` measurements, `nasm`/`objcopy`/`xxd` for shellcode (the assembly source is shown in full), and the exploit source as it was written.
- `recordings/<game>/L<n>.cast` — the asciinema recording of each live solve; `recordings/index.html` is the player page that lists them all.
- `narration/<game>/L<n>.txt` — the spoken narration script for each level (the `.mp3` audio is delivered separately).
- `solves/` — the exploit sources, assembly files and helpers that the recordings build.
