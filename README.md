# OverTheWire — all wargames, solved

Solutions to **every OverTheWire wargame**, solved from a DGX Spark ("DGX 5"). Each game gets a full writeup and a terminal-replay of every level being solved — commands typed out live, with the level's problem statement, the output, and the password it yields.

**Site:** https://jaher.github.io/overthewire-solutions/ — pick a game from the tier dropdown, pick a level, watch it being solved.

## Games

| Game | Type | Levels | Status |
|---|---|---|---|
| Bandit | Linux basics over SSH | 0–33 | ✅ Complete — [writeup](bandit-writeup.md) |
| Natas | Web security | 0–34 | 🔄 Solving |
| Leviathan | Linux/binary basics | 0–7 | 🔄 Solving |
| Krypton | Classical cryptography | 0–6 | 🔄 Solving |
| Manpage | Linux privilege basics | 0–6 | 🔄 Solving |
| Narnia | Buffer overflows & shellcode | 0–9 | 🔄 Solving |
| Behemoth | Exploitation vs. mitigations | 0–7 | 🔄 Solving |
| Utumno | Advanced exploitation / reversing | 0–7 | 🔄 Solving |
| Maze | Exploitation & format strings | 0–9 | 🔄 Solving |
| Vortex | Classic exploitation | 0–26 | 🔄 Solving (some levels are bit-rotted upstream; broken ones are documented as such) |

## How this repo is organized

- `index.html` — the terminal-replay site (dark shell, green type, human typing effect). Published to GitHub Pages by the Action in `.github/workflows/pages.yml` on every push to `main`.
- `games/<game>.json` — per-game replay data (levels, goals, commands, outputs, passwords); `games/manifest.json` lists the games the site offers in its tier dropdown. A game appears on the site as soon as its data lands here.
- `<game>-writeup.md` — the written writeup per game: goal, technique and exact commands per level, and the password obtained.
