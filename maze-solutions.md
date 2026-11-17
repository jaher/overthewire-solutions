# Maze — solutions

Transcripts: `games/maze.json` (per-level `cmds`/`out`/`pw`). Casts: not yet
recorded (see OTW-PROGRESS.md).

## Level 0 → maze1 (SOLVED)
- **Password for maze1:** `Sp5VmLGFC0`, read live in a winning run of the race.
- **The program:** `/maze/maze0`: `main()` does `access(PATH, R_OK)` → `setresuid(euid)` → `open(PATH)` → read/print. `PATH` is `/tmp/128ecf542a35ac5270a87dc740918404` — a classic check-then-open TOCTOU race.
- **Method:** place a readable file (`/tmp/real_f` full of `AAAA...`) and a symlink (`/tmp/link_s` → `/etc/maze_pass/maze1`), then a C loop `rename()`s the path back and forth between the two. `for i in $(seq 15000); do /maze/maze0; done | sort | uniq -c`: most runs print the `AAAA...` filler, **132 winning runs print `Sp5VmLGFC0`**.
- **Verification:** the password was confirmed by logging in as `maze1` when the level was solved.
- **Note (2026-11-17):** the `maze0` login works again on the current lab (uid=15000 live, initial password `maze0`); the recorded solve stands.
