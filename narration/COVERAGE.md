# Narration coverage audit

Generated against origin/main. Site-rendered levels: **119** — scripts **110** (9 missing), mp3 **67** (52 missing).

| Game | Levels | Scripts | MP3s | Missing scripts | Missing mp3s |
|---|---|---|---|---|---|
| bandit | 34 | 34 | 33 | — | L33 |
| behemoth | 8 | 8 | 0 | — | L0, L1, L2, L3, L4, L5, L6, L7 |
| krypton | 8 | 8 | 8 | — | — |
| leviathan | 8 | 8 | 8 | — | — |
| manpage | 5 | 0 | 0 | L0, L1, L2, L3, L4 | L0, L1, L2, L3, L4 |
| maze | 1 | 0 | 0 | L0 | L0 |
| narnia | 10 | 9 | 0 | L9 | L0, L1, L2, L3, L4, L5, L6, L7, L8, L9 |
| natas | 34 | 34 | 18 | — | L18, L19, L20, L21, L22, L23, L24, L25, L26, L27, L28, L29, L30, L31, L32, L33 |
| utumno | 8 | 8 | 0 | — | L0, L1, L2, L3, L4, L5, L6, L7 |
| vortex | 3 | 1 | 0 | L1, L2 | L0, L1, L2 |

## Alignment flags

`narr-only` = a tool the narration names that no typed step ever runs. Each one was hand-checked against the level's transcript and writeup; the ones below are real gaps (a verification or inspection the script describes but the site never types), not prose false positives.

### Narration-only tools (named in the script, never typed)

- behemoth L0: objdump — narration disassembles main; transcript has no objdump step
- behemoth L1: gdb — narration confirms the layout in gdb; transcript has no gdb step
- narnia L1: nasm, objdump — narration assembles with nasm, checks with objdump, extracts with objcopy; transcript has none of the three
- narnia L2: gdb — narration confirms the layout in gdb; transcript has no gdb step
- narnia L4: strace — narration cites strace output; transcript has gdb but no strace
- utumno L2: gdb — narration confirms offsets in gdb; transcript has no gdb step
- utumno L3: gdb — narration confirms the arithmetic in gdb; transcript has no gdb step
- utumno L5: gdb — narration confirms the layout in gdb; transcript has no gdb step
- utumno L6: gdb — narration confirms the slot in gdb; transcript has no gdb step
- utumno L7: gdb — narration cites gdb output; transcript has no gdb step
- vortex L0: ssh — narration verifies by logging in over SSH on port 2228; transcript has no ssh step (fixed in the pilot: sentence rewritten to the service reply)

### Reviewed and cleared (not gaps)

- bandit L12: hexdump names the file; xxd -r is typed
- bandit L14: netcat = nc, typed
- bandit L15: negative mention — "plain netcat will not work"
- bandit L20: netcat = nc, typed in a compound command
- bandit L24: netcat = nc, typed inside the for loop
- utumno L0: negative mention — "nm and readelf and ltrace all refuse"
- utumno L4: gdb IS in the transcript (false positive)

## Notes

- Vortex L3 is solved (recordings/vortex/L3.cast, writeup) but not yet in games/vortex.json, so it is outside this table; it needs a script + mp3 + a site entry.
- Vortex L4 is in progress (no solution yet).
- manpage (5 levels) and maze (L0) are blocked games; their site entries are stubs, so no narration is expected until they are solved.
