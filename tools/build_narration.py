#!/usr/bin/env python3
"""Build one level's narration audio + sync map from its segment file.

Source of truth: narration/<game>/L<n>.segments.json — a list of segments,
each with the spoken text and the exact typed lines it anchors to:
    {"segments": [{"text": "...", "lines": [{"step": -1, "role": "goal"}]}, ...]}
Line refs use the site's own rendered lines: step index + role
(goal/vim/vimcmd/cmd/out/pw/text/note); out lines take an inclusive
index range into the step's `out` array, 0-based.

Outputs (same method as the Vortex L0 pilot):
  - narration/<game>/L<n>.txt       — " ".join(segment texts); if a .txt
    already exists it must match exactly, or the build fails (the script
    is the source text; edit the segments file, not the other way round).
  - narration/<game>/L<n>.mp3       — one Helio TTS synthesis per segment
    (/opt/hatch/bin/tts, voice avocado_v2:MAI_03), durations measured
    with ffprobe, segments concatenated in order (24 kHz mono 64 kb/s).
  - narration/<game>/L<n>.sync.json — segments with measured start/end
    (cumulative sums, never guesswork) plus the line refs.

Validation: every line ref must point at a real rendered line of the
level (loaded from games/<game>.json, or from the inline LEVELS array
in index.html for bandit). Steps whose command is never referenced are
reported as warnings — review them; a command the narration never
anchors to types ungated, i.e. possibly before its spoken time.

Usage: python3 tools/build_narration.py <game> <level>
Run from the repo root.
"""
import json, os, re, subprocess, sys

VOICE = "avocado_v2:MAI_03"  # Helio — user-confirmed 2026-11-15
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLES = {"goal", "vim", "vimcmd", "cmd", "out", "pw", "text", "note"}

def run(cmd, inp=None):
    r = subprocess.run(cmd, input=inp, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAILED:", " ".join(cmd), "\n", r.stdout, r.stderr)
        sys.exit(1)
    return r

def duration(path):
    r = run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", path])
    return float(r.stdout.strip())

def load_level(game, level):
    """Return the level dict {lvl, user, pw, steps} for game/level."""
    if game == "bandit":
        html = open(os.path.join(ROOT, "index.html")).read()
        m = re.search(r"const LEVELS = (\[.*?\n\]);", html, re.S)
        if not m:
            sys.exit("could not find inline LEVELS in index.html")
        levels = json.loads(m.group(1))
    else:
        data = json.load(open(os.path.join(ROOT, "games", game + ".json")))
        levels = data["levels"]
    for lv in levels:
        if lv["lvl"] == level:
            return lv
    sys.exit(f"no level {level} in game {game}")

def vim_file_of(step):
    m = re.match(r"^vim\s+(.+)$", (step.get("cmd") or "").strip())
    if not m:
        return None
    parts = m.group(1).strip().split()
    return parts[-1] if parts else None

def vim_runs(steps):
    """Map step index -> first step index of its consecutive vim run."""
    first_of = {}
    si = 0
    while si < len(steps):
        vf = vim_file_of(steps[si])
        if vf:
            run = []
            while si < len(steps) and vim_file_of(steps[si]) == vf:
                run.append(si)
                si += 1
            for s in run:
                first_of[s] = run[0]
        else:
            si += 1
    return first_of

def validate(game, level, segments):
    lv = load_level(game, level)
    steps = lv.get("steps")
    if not steps:
        sys.exit(f"level {game} L{level} has no steps (legacy cmds) — cannot sync")
    first_of = vim_runs(steps)
    covered_cmds = set()
    errors = []
    for i, seg in enumerate(segments):
        for L in seg.get("lines", []):
            step, role = L.get("step"), L.get("role")
            if role not in ROLES:
                errors.append(f"seg {i}: unknown role {role!r}")
                continue
            if step == -1:
                if role not in ("goal", "pw"):
                    errors.append(f"seg {i}: step -1 with role {role!r}")
                elif role == "pw" and not lv.get("pw"):
                    errors.append(f"seg {i}: pw ref but level has no pw")
                continue
            if not isinstance(step, int) or not (0 <= step < len(steps)):
                errors.append(f"seg {i}: step {step!r} out of range (0..{len(steps)-1})")
                continue
            st = steps[step]
            if role == "cmd":
                if st.get("text"):
                    errors.append(f"seg {i}: step {step} is a text step, use role 'text'")
                elif (st.get("cmd") or "").startswith("#"):
                    errors.append(f"seg {i}: step {step} is a comment, use role 'note'")
                else:
                    covered_cmds.add(step)
            elif role == "text":
                if not st.get("text"):
                    errors.append(f"seg {i}: step {step} has no text field")
                else:
                    covered_cmds.add(step)
            elif role == "note":
                if not ((st.get("cmd") or "").startswith("#") or st.get("note")):
                    errors.append(f"seg {i}: step {step} is neither a # comment nor a noted step")
            elif role in ("vim", "vimcmd"):
                if step not in first_of:
                    errors.append(f"seg {i}: step {step} is not a vim step")
                elif first_of[step] != step:
                    errors.append(f"seg {i}: {role} must anchor the FIRST step of the vim run "
                                  f"(step {first_of[step]}, not {step})")
                else:
                    covered_cmds.add(step)
            elif role == "out":
                out = st.get("out") or []
                frm, to = L.get("from"), L.get("to")
                if frm is None:
                    errors.append(f"seg {i}: out ref needs 'from'")
                elif not (0 <= frm < len(out)):
                    errors.append(f"seg {i}: out from={frm} out of range (0..{len(out)-1})")
                elif to is not None and not (frm <= to < len(out)):
                    errors.append(f"seg {i}: out to={to} out of range ({frm}..{len(out)-1})")
            elif role == "goal":
                errors.append(f"seg {i}: goal must use step -1")
            elif role == "pw":
                errors.append(f"seg {i}: pw must use step -1")
    if errors:
        print(f"INVALID line refs in {game} L{level}:")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    # warnings: commands the narration never anchors to (they type ungated)
    uncovered = [s for s, st in enumerate(steps)
                 if s not in covered_cmds and (st.get("cmd") or "").strip()]
    if uncovered:
        print(f"WARNING {game} L{level}: {len(uncovered)} command(s) never anchored: "
              + ", ".join(f"step {s} ({steps[s].get('cmd','')[:40]!r})" for s in uncovered))

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    game, level = sys.argv[1], int(sys.argv[2])
    seg_path = os.path.join(ROOT, "narration", game, f"L{level}.segments.json")
    segs = json.load(open(seg_path))["segments"]
    if not segs:
        sys.exit(f"{seg_path}: no segments")
    validate(game, level, segs)

    txt_path = os.path.join(ROOT, "narration", game, f"L{level}.txt")
    script = " ".join(s["text"] for s in segs)
    if os.path.exists(txt_path):
        existing = open(txt_path).read().strip()
        if existing != script:
            print(f"segments do not reconstruct {txt_path}:\n--- file ---\n{existing}\n"
                  f"--- joined ---\n{script}")
            sys.exit(1)
    else:
        open(txt_path, "w").write(script + "\n")
        print(f"wrote {txt_path}")
    print(f"{len(segs)} segments, script {len(script)} chars — matches L{level}.txt")

    outdir = f"/tmp/narr-{game}-L{level}-segs"
    os.makedirs(outdir, exist_ok=True)
    files, durs = [], []
    for i, seg in enumerate(segs):
        out = f"{outdir}/seg{i:02d}.mp3"
        run(["/opt/hatch/bin/tts", "speak", "--voice", VOICE,
             "--output", out, "--text-stdin"], inp=seg["text"])
        d = duration(out)
        files.append(out)
        durs.append(d)
        print(f"seg {i:02d} {d:6.2f}s  {seg['text'][:60]}")

    mp3_path = os.path.join(ROOT, "narration", game, f"L{level}.mp3")
    with open(f"{outdir}/list.txt", "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", f"{outdir}/list.txt", "-c", "copy", mp3_path])
    total = duration(mp3_path)
    print(f"sum of segments: {sum(durs):.2f}s; shipped mp3: {total:.2f}s "
          f"(diff {total - sum(durs):+.2f}s)")
    # format must match the existing mp3s: 24 kHz mono 64 kb/s
    r = run(["ffprobe", "-v", "quiet", "-show_entries",
             "stream=sample_rate,channels,codec_name",
             "-show_entries", "format=bit_rate",
             "-of", "csv=p=0", mp3_path])
    print("mp3 format:", " ".join(r.stdout.split()))

    sync_segs, t = [], 0.0
    for i, (seg, d) in enumerate(zip(segs, durs)):
        sync_segs.append({"id": i, "start": round(t, 2), "end": round(t + d, 2),
                          "text": seg["text"], "lines": seg["lines"]})
        t += d
    sync = {"game": game, "level": level,
            "audio": f"narration/{game}/L{level}.mp3",
            "voice": VOICE, "duration": round(total, 2), "segments": sync_segs}
    sync_path = os.path.join(ROOT, "narration", game, f"L{level}.sync.json")
    json.dump(sync, open(sync_path, "w"), indent=1)
    print(f"wrote {sync_path}, duration {round(total, 2)}s")

if __name__ == "__main__":
    main()
