#!/usr/bin/env python3
"""Build Vortex L0 narration audio + sync map from the (aligned) script.

Each segment is synthesized separately with /opt/hatch/bin/tts (voice Helio,
the documented default — the voice of the existing 67 mp3s is not recorded
anywhere in the repo or in their tags, so it is not determinable). Each
segment mp3's duration is measured with ffprobe; the shipped mp3 is the
segments concatenated in order, so every sync-map start time is a measured
cumulative sum, not a guess. Line anchors use the site's own rendered lines:
step index + role (goal/vim/vimcmd/cmd/out/pw), out indices are 0-based into
the step's `out` array.
"""
import json, subprocess, sys

VOICE = "avocado_v2:MAI_03"  # Helio
SEGMENTS = [
    ("Vortex, level zero.",
     [{"step": -1, "role": "goal"}]),
    ("This one never gives you a shell at all: it is a network service listening on port 5842 of vortex.labs.overthewire.org.",
     [{"step": -1, "role": "goal"}]),
    ("The official description says the service sends four unsigned integers in host byte order, you add them up and send the sum back, and the reply contains the username and password for vortex one.",
     [{"step": -1, "role": "goal"}]),
    ("The machine is 32 bit x86, so host byte order means little endian.",
     [{"step": -1, "role": "goal"}]),
    ("I open vim and write a small C client:",
     [{"step": 0, "role": "vimcmd"}, {"step": 0, "role": "vim"},
      {"step": 3, "role": "out", "from": 0, "to": 16}]),
    ("create a TCP socket,",
     [{"step": 3, "role": "out", "from": 17, "to": 22}]),
    ("resolve the host name,",
     [{"step": 3, "role": "out", "from": 23, "to": 28}]),
    ("connect to port 5842,",
     [{"step": 3, "role": "out", "from": 30, "to": 33}]),
    ("read sixteen bytes,",
     [{"step": 3, "role": "out", "from": 34, "to": 40}]),
    ("copy them into four unsigned integers, add them,",
     [{"step": 3, "role": "out", "from": 41, "to": 45}]),
    ("write the four byte sum back,",
     [{"step": 3, "role": "out", "from": 46, "to": 50}]),
    ("then read until the service closes and print the reply.",
     [{"step": 3, "role": "out", "from": 51, "to": 66}]),
    ("The first bug I hit was using inet_pton on a host name, which only accepts a literal address, so I switched to gethostbyname;",
     [{"step": 3, "role": "out", "from": 23, "to": 28}]),
    ("the compiler also caught a missing netdb header.",
     [{"step": 3, "role": "out", "from": 6, "to": 6}]),
    ("The reply arrives split across reads, and my input buffer was only sixteen bytes, so I read into a separate two hundred and fifty six byte buffer until the peer closes.",
     [{"step": 3, "role": "out", "from": 12, "to": 13},
      {"step": 3, "role": "out", "from": 52, "to": 60}]),
    ("Then I compile with gcc, run it, and the service answers with the vortex one credentials.",
     [{"step": 4, "role": "cmd"}, {"step": 5, "role": "cmd"},
      {"step": 5, "role": "out", "from": 0, "to": 2}]),
    ("The service prints the vortex one username and password, and the level is solved.",
     [{"step": 5, "role": "out", "from": 2, "to": 2},
      {"step": -1, "role": "pw"}]),
]

OUTDIR = "/tmp/narr-l0-segs"
import os
os.makedirs(OUTDIR, exist_ok=True)

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

def main():
    # sanity: segments joined must equal the script (modulo the final period
    # handling: the script is one paragraph; segments are its sentences, with
    # the long code-walk sentence split on its commas).
    script = open("narration/vortex/L0.txt").read().strip()
    joined = " ".join(t for t, _ in SEGMENTS)
    assert joined == script, (
        "segments do not reconstruct the script:\n--- script ---\n" + script +
        "\n--- joined ---\n" + joined)
    print(f"{len(SEGMENTS)} segments, script {len(script)} chars — matches L0.txt")

    files, durs = [], []
    for i, (text, _) in enumerate(SEGMENTS):
        out = f"{OUTDIR}/seg{i:02d}.mp3"
        run(["/opt/hatch/bin/tts", "speak", "--voice", VOICE,
             "--output", out, "--text-stdin"], inp=text)
        d = duration(out)
        files.append(out)
        durs.append(d)
        print(f"seg {i:02d} {d:6.2f}s  {text[:60]}")

    # concat (same voice/settings, so same codec params — stream copy)
    with open(f"{OUTDIR}/list.txt", "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", f"{OUTDIR}/list.txt", "-c", "copy", "narration/vortex/L0.mp3"])
    total = duration("narration/vortex/L0.mp3")
    print(f"sum of segments: {sum(durs):.2f}s; shipped mp3: {total:.2f}s "
          f"(diff {total - sum(durs):+.2f}s)")

    segs, t = [], 0.0
    for i, ((text, lines), d) in enumerate(zip(SEGMENTS, durs)):
        segs.append({"id": i, "start": round(t, 2), "end": round(t + d, 2),
                     "text": text, "lines": lines})
        t += d
    sync = {"game": "vortex", "level": 0, "audio": "narration/vortex/L0.mp3",
            "voice": VOICE, "duration": round(total, 2), "segments": segs}
    json.dump(sync, open("narration/vortex/L0.sync.json", "w"), indent=1)
    print("wrote narration/vortex/L0.sync.json, duration",
          round(total, 2), "s")

if __name__ == "__main__":
    main()
