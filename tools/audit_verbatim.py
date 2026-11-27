#!/usr/bin/env python3
"""audit_verbatim.py — detect step outputs in games/*.json that do not match
the cast verbatim (elided, fabricated, or annotated).

Matching model:
  * Commands are matched LOOSELY: the JSON cmd's leading token + first quoted
    path/word must appear in the cast near the JSON out text. JSON cmds are
    often shorthand (e.g. `ssh -p 2222 level5@...` vs the cast's full ssh
    with options); that is fine — the OUT is what must be verbatim.
  * For a matched command, the segment = cast stream from cmd to the next
    shell prompt (user@host$ / client$ / bash-...$).
  * A step's `out` passes when:
      - every out-line (normalized, 80-col wraps joined) is a substring of
        the normalized segment, in order; AND
      - the out text covers the segment (segment is not substantially
        longer than out -> truncation/omission) — except for vi/vim where
        staged screen snapshots are the norm.
  * Defect kinds:
      ELISION   out has a literal ' ... ' the cast segment does not
      ABSENT    out line not present in segment/stream (fabricated/edited)
      OMITTED   segment has content out does not (partial output recorded)
      NOCAST    level has steps but no cast file

Usage: tools/audit_verbatim.py [game ...]
Exit 0 clean / 1 defects.
"""
import json, glob, os, re, sys

ESCRE = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][0-9A-B]|\x1b[78MmDE]')
# NOTE: some captures terminate OSC with ST (ESC \\) not BEL — the old
# greedy-to-BEL pattern swallowed whole screen regions (e.g. narnia L1 cat).
# Also normalize \r-runs (this capture family separates lines with \r\r\r\n,
# not \r\n) BEFORE unwrapping, and collapse ALL whitespace when matching.

def raw_stream(path):
    lines = open(path).read().splitlines()
    data = []
    for l in lines[1:]:
        try:
            o = json.loads(l)
        except Exception:
            continue
        if isinstance(o, list) and len(o) == 3 and o[1] == 'o':
            data.append(o[2])
    return ESCRE.sub('', ''.join(data))

def detect_prompt(stream):
    """Return one alternation regex covering ALL user@host prompt tokens
    seen in the stream (multi-level sessions switch users mid-cast)."""
    toks = re.findall(r'\b[\w.-]+@[\w.-]+\b', stream)
    best = {}
    for t in toks:
        best[t] = best.get(t, 0) + 1
    # keep tokens that sit in a prompt-looking position: shortly before a '$'
    # on some line (command/password/MOTD lines don't have that)
    live = [t for t in best
            if best[t] >= 2
            and re.search(r'\n[^\n]*' + re.escape(t) + r'[^\n]{0,20}\$', stream)]
    if live:
        alt = '|'.join(re.escape(t) for t in sorted(live, key=lambda t: -best[t]))
        return re.compile(r'\n[^\n]*(?:' + alt + r')[^\n]*\$')
    # a bare '$' anywhere matches PHP/Perl output lines ($var); require '$ ' (dollar
    # SPACE - the prompt shape 'user@host$ cmd') so '$var' output lines don't truncate
    # segments (natas L26: 'private $logFile;' cut the segment to 13 chars)
    return re.compile(r'\n[^\n]*\$ ')

def unwrap(s):
    """Join 80-col soft wraps: a line not ending in space, followed by a line
    not starting in space, is one logical line split by the terminal."""
    s = re.sub(r'\r+', '\n', s)
    lines = s.split('\n')
    res = []
    for ln in lines:
        if res and len(res[-1]) >= 70 and not res[-1].endswith(' ') \
           and not ln.startswith(' '):
            res[-1] = res[-1] + ln
        else:
            res.append(ln)
    return '\n'.join(res)

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()

def find_cmd(stream, cmd, after=0):
    """Find the command line in the cast. Tries the full cmd first, then
    'leading token + path', then bare leading token (shorthand cmds).
    Matches are anchored to a line start so 'id' doesn't hit inside
    arbitrary text; falls back to substring only if no line-start hit."""
    cands = [cmd]
    m = re.match(r'^(\S+)(\s+(\S+))?', cmd)
    if m:
        lead, arg = m.group(1), m.group(3)
        if lead and arg:
            cands.append(lead + ' ' + arg)
        cands.append(lead)
    for c in cands:
        j = after
        while True:
            j = stream.find(c, j)
            if j < 0:
                break
            # accept a match whose line has a short prompt-like prefix
            # ([user@host ~]$ id, client$ cmd) and reject mid-text hits
            # (zoidberg, setresuid); the char before must be a boundary
            prev = stream[j - 1] if j else '\n'
            ls = stream.rfind('\n', 0, j) + 1
            if (j == 0 or (not (prev.isalnum() or prev in '_-')
                           and len(stream[ls:j]) <= 40)):
                return j, len(c)
            j += 1
    for c in cands:
        j = stream.find(c, after)
        if j >= 0:
            return j, len(c)
    return -1, 0

def segment_of(stream, cmd, prompt_re, after=0):
    j, clen = find_cmd(stream, cmd, after)
    if j < 0:
        return None, -1
    j2 = j + clen
    # skip the echoed command line itself
    nl = stream.find('\n', j2)
    if nl < 0 or nl - j2 > 200:
        nl = j2
    else:
        j2 = nl + 1
    m = prompt_re.search(stream, j2)
    end = m.start() if m else min(j2 + 50000, len(stream))
    return stream[j2:end], j

def audit_game(game):
    d = json.load(open(f'games/{game}.json'))
    defects = []
    for li, lv in enumerate(d.get('levels', [])):
        castpath = None
        for cand in (f'recordings/{game}/L{lv.get("lvl")}.cast',
                     f'recordings/{game}/L{li}.cast'):
            if os.path.exists(cand):
                castpath = cand
                break
        if not castpath:
            if lv.get('steps'):
                defects.append((lv.get('lvl'), -1, 'NOCAST', '', ''))
            continue
        stream = raw_stream(castpath)
        stream_n = norm(unwrap(stream))
        prompt_re = detect_prompt(stream)
        cursor = 0
        for si, st in enumerate(lv.get('steps', [])):
            cmd, out = st.get('cmd', ''), st.get('out')
            if out is None:
                continue
            outs = out if isinstance(out, list) else [out]
            texts = [str(o) for o in outs if isinstance(o, str) and o.strip()]
            if not texts:
                continue
            is_vi = cmd.strip().startswith(('vi ', 'vim ', 'nano '))
            seg, j = segment_of(stream, cmd, prompt_re, cursor)
            if seg is None:
                # cmd not found at all: check if the out text exists anywhere
                ok_any = all(norm(t) in stream_n for t in texts)
                if not ok_any:
                    defects.append((lv.get('lvl'), si, 'NOCMD', cmd[:60], texts[0][:60]))
                continue
            cursor = max(cursor, j)
            seg_n = norm(unwrap(seg))
            pos = 0
            for k, t in enumerate(texts):
                tn = norm(t)
                idx = seg_n.find(tn, pos)
                if idx < 0:
                    idx = seg_n.find(tn)
                if idx < 0:
                    if is_vi and tn in stream_n:
                        pos = stream_n.find(tn, pos)
                        continue
                    defects.append((lv.get('lvl'), si, 'ABSENT', cmd[:55], t[:70]))
                    continue
                pos = idx + len(tn)
                if ' ... ' in t:
                    defects.append((lv.get('lvl'), si, 'ELISION', cmd[:55], t[:70]))
            # omission check (non-vi): segment has a lot of content out lacks
            if not is_vi and seg_n:
                covered = ''
                pos = 0
                for t in texts:
                    tn = norm(t)
                    idx = seg_n.find(tn, pos)
                    if idx >= 0:
                        covered += seg_n[pos:idx + len(tn)] if pos < idx else tn
                        pos = idx + len(tn)
                missing_ratio = 1 - (len(covered) / len(seg_n)) if seg_n else 0
                if missing_ratio > 0.25 and len(seg_n) > 60:
                    defects.append((lv.get('lvl'), si, 'OMITTED', cmd[:55],
                                    f'seg {len(seg_n)}B, out covers {len(covered)}B ({missing_ratio:.0%} missing)'))
    return defects

def main():
    args = sys.argv[1:]
    if not args:
        args = sorted(os.path.basename(p)[:-5] for p in glob.glob('games/*.json'))
    total = 0
    for game in args:
        if game == 'manifest' or not os.path.exists(f'games/{game}.json'):
            continue
        if not glob.glob(f'recordings/{game}/*.cast'):
            continue
        defects = audit_game(game)
        if defects:
            total += len(defects)
            by = {}
            for lvl, si, kind, cmd, out in defects:
                by.setdefault(f'L{lvl}', []).append((si, kind, cmd, out))
            print(f'== {game}: {len(defects)} defect(s) ==')
            for lvl, items in by.items():
                print(f'  {lvl}: {len(items)}')
                for si, kind, cmd, out in items[:10]:
                    print(f'    s{si} {kind:8s} {cmd!r} :: {out!r}')
                if len(items) > 10:
                    print(f'    ... +{len(items)-10} more')
    print(f'\nTOTAL defects: {total}')
    sys.exit(1 if total else 0)

if __name__ == '__main__':
    main()
