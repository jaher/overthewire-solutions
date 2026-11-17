# Narration coverage audit

Generated against local main. Site-rendered levels = casts present.

| Game | Levels (casts) | Scripts | MP3s | Missing scripts | Missing mp3s |
|---|---|---|---|---|---|
| bandit | 34 | 34 | 34 | — | — |
| natas | 34 | 34 | 34 | — | — |
| leviathan | 8 | 8 | 8 | — | — |
| krypton | 8 | 8 | 8 | — | — |
| manpage | 0 | 5 | 0 | — | — |
| narnia | 9 | 10 | 10 | — | — |
| behemoth | 8 | 8 | 8 | — | — |
| utumno | 8 | 8 | 8 | — | — |
| maze | 0 | 1 | 0 | — | — |
| vortex | 10 | 12 | 5 | — | L5, L6, L7, L8, L9 |

Site-rendered levels: **119** — scripts **128** (all), mp3 **115** (4 missing).

The mp3 synthesis needs the Helio TTS binary (/opt/hatch/bin/tts) and ffprobe,
neither of which is on this container; the sync host makes the audio.
