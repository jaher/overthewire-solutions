# Narration coverage audit

Generated against local main. Casts = site-rendered levels (manpage, maze and
vortex L1/L2 have transcripts but no .cast yet).

| Game | Levels (casts) | Scripts | Segments | MP3s | Missing mp3s |
|---|---|---|---|---|---|
| bandit | 34 | 34 | 34 | 34 | — |
| natas | 34 | 34 | 34 | 34 | — |
| leviathan | 8 | 8 | 8 | 8 | — |
| krypton | 8 | 8 | 8 | 8 | — |
| manpage | 0 | 5 | 5 | 0 | — (no casts) |
| narnia | 9 | 10 | 10 | 10 | — |
| behemoth | 8 | 8 | 8 | 8 | — |
| utumno | 8 | 8 | 8 | 8 | — |
| maze | 0 | 1 | 1 | 0 | — (no casts) |
| vortex | 10 | 12 | 12 | 5 | L0, L3, L4 |

Site-rendered levels: **119** — scripts **128**, segments **128** (every level has both), mp3 **115**.

Missing mp3s: vortex L5-L11, manpage L0-L4, maze L0. The mp3 synthesis needs
the Helio TTS binary (/opt/hatch/bin/tts) and ffprobe, neither of which is on
this container; the sync host makes the audio from the segments files.
