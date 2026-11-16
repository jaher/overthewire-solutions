#!/usr/bin/env python3
"""Real-playback (1x) margin check for narrated vim levels.

For every vim chunk, does the spoken cover (from the chunk's scheduled
time to the next gated line's scheduled time) exceed the nominal typing
time (chars x 21ms + overhead)? Lines over 200 chars are pastes (0.3s),
not typed. Scheduled times replicate buildNarrSchedule: multi-ref
segments spread refs evenly across the segment.

The headless narration check drives a mock clock faster than real time,
so it does NOT prove 1x sync — this check does. Acceptance bar: margins
>= -0.5s are noise (absorbed by the next chunk's slack); worse is a real
defect (the typed lines lag the spoken words at real playback) and the
gating segment must be lengthened. Precedent: narnia L2 step 7 was -2.01s
and was fixed by lengthening its segment (commit d59612a).

Usage: python3 tools/narration_margins.py <game> <lvl> [<lvl> ...]
Exit code 1 if any chunk's margin is worse than -0.5s.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAR = -0.5

def parse_vim_screen(out):
    buf = {}
    for ln in out or []:
        m = re.match(r"^\s*(\d+)\s?(.*)$", ln)
        if m:
            buf[int(m.group(1))] = m.group(2)
    return buf

def vim_runs(steps):
    runs, cur = [], []
    for i, st in enumerate(steps):
        if (st.get("cmd") or "").startswith("vim "):
            cur.append((i, st))
        else:
            if cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    return runs

def chunk_typing(run):
    """per step: nominal typing seconds to produce that step's snapshot."""
    snaps = [parse_vim_screen(st.get("out")) for _, st in run]
    buf, out = {}, {}
    for k, (si, st) in enumerate(run):
        snap = snaps[k]
        secs = 0.0
        for n, text in snap.items():
            if n not in buf:
                secs += 0.3 if len(text) > 200 else len(text) * 0.021 + 0.06
            elif buf[n] != text:
                secs += 0.3 if len(text) > 200 else len(text) * 0.021 + 0.12
        buf = dict(snap)
        out[si] = secs
    return out

def schedule(segments):
    """ordered [(time, key)] replicating buildNarrSchedule (first occurrence)."""
    times, seen = [], {}
    for si, sg in enumerate(segments):
        refs = []
        for L in sg.get("lines", []):
            if L["role"] == "out" and L.get("from") is not None:
                for i in range(L["from"], (L["to"] if L.get("to") is not None else L["from"]) + 1):
                    refs.append((L["step"], "out", i))
            else:
                refs.append((L["step"], L["role"], None))
        for j, k in enumerate(refs):
            t = sg["start"] + ((j / len(refs)) * (sg["end"] - sg["start"]) if len(refs) > 1 else 0)
            if k not in seen:
                seen[k] = t
                times.append((t, k))
    return sorted(times)

def check(game, lv):
    """Returns the worst margin (None if the level has no vim chunks)."""
    d = json.load(open(f"{ROOT}/games/{game}.json"))
    levels = d["levels"] if "levels" in d else d
    steps = [l for l in levels if l["lvl"] == lv][0]["steps"]
    segs = json.load(open(f"{ROOT}/narration/{game}/L{lv}.segments.json"))["segments"]
    sm = json.load(open(f"{ROOT}/narration/{game}/L{lv}.sync.json"))
    for i, s in enumerate(sm["segments"]):
        segs[i]["start"], segs[i]["end"] = s["start"], s["end"]
    times = schedule(segs)
    typing = {}
    for run in vim_runs(steps):
        typing.update(chunk_typing(run))
    worst = None
    for idx, (t, k) in enumerate(times):
        step, role, _ = k
        if role != "vim" or step not in typing:
            continue
        nxt = times[idx + 1][0] if idx + 1 < len(times) else sm["duration"]
        cover = nxt - t
        need = typing[step]
        margin = cover - need
        flag = "OK " if margin >= BAR else "NEG"
        if worst is None or margin < worst[0]:
            worst = (margin, step, cover, need)
        print(f"  {game} L{lv} vim step {step:2d}: cover {cover:6.2f}s need {need:6.2f}s margin {margin:+6.2f}s [{flag}]")
    if worst:
        print(f"  => {game} L{lv} worst margin {worst[0]:+.2f}s (step {worst[1]})")
    else:
        print(f"  {game} L{lv}: no vim chunks")
    return worst[0] if worst else None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: narration_margins.py <game> <lvl> [<lvl> ...]", file=sys.stderr)
        sys.exit(2)
    game = sys.argv[1]
    bad = False
    for lv in [int(x) for x in sys.argv[2:]]:
        w = check(game, lv)
        if w is not None and w < BAR:
            bad = True
    sys.exit(1 if bad else 0)
