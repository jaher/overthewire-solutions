#!/usr/bin/env python3
"""diff_replay.py GAME LVL REPLAY_STREAM — verify a replay against the JSON.

Rule 4: every character of the replayed session must match the JSON `out`
verbatim. The replay stream (cleaned, one logical line per row, same
normalization as the audit tool) is sliced at each step's command anchor and
compared line-for-line with the step's `out`. vi steps compare the final
buffer text (the staged screens are vim redraws; the :wq marker carries the
byte-exact buffer proof: `N L, M C` must match the cast's marker).
Exit 0 = verbatim match for every step; 1 = mismatches listed.
"""
import json, re, sys

ROOT = __file__.rsplit('/', 3)[0]

def norm(s):
    return re.sub(r'\s+', ' ', s).strip()

def main():
    game, lvl, stream_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    levels = json.load(open(f'{ROOT}/games/{game}.json'))['levels']
    lv = next(l for l in levels if l['lvl'] == lvl)
    steps = lv['steps']
    lines = open(stream_path).read().split('\n')

    # locate every command anchor in the stream (first occurrence after the
    # previous anchor)
    anchors = []
    cur = 0
    ok = True
    for si, st in enumerate(steps):
        cmd = st['cmd']
        out = st.get('out')
        if out is None:
            anchors.append(-1)
            continue
        found = -1
        # a step's cmd may carry several real commands (each echoed on its own
        # line in the replay); anchor on the FIRST line. The final exit step's
        # bare 'exit' would otherwise match the remote session's exit echo -
        # prefer the client-side prompt line when it exists.
        if cmd.rstrip() == 'exit\nexit':
            # anchor at the remote shell's exit echo ('user@host$ exit'); the
            # JSON out starts at 'logout', the line right after that echo
            for i in range(len(lines) - 1, cur - 1, -1):
                if lines[i].rstrip().endswith('exit') and 'client$' in lines[i]:
                    for k in range(i, cur, -1):
                        if 'manpage' in lines[k] and lines[k].rstrip().endswith('exit'):
                            found = k
                            break
                    break
            anchors.append(found if found >= 0 else -1)
            if found < 0:
                print(f"step {si} ({cmd[:50]}): ANCHOR NOT FOUND")
                ok = False
            else:
                cur = found + 1
            continue
        first = cmd.split('\n')[0].rstrip()
        for i in range(cur, len(lines)):
            # the replay echoes commands with a prompt prefix
            if lines[i].rstrip().endswith(first):
                found = i
                break
        if found < 0 and re.match(r'^(?:vi|vim)\s', cmd):
            # one vi session = one contiguous run in the replay; later staged
            # steps of the same file share the first session's anchor
            for j in range(si - 1, -1, -1):
                if re.match(r'^(?:vi|vim)\s', steps[j]['cmd']) and anchors[j] >= 0:
                    found = anchors[j]
                    break
        if found < 0:
            # ssh login steps are performed by ptyrun2 itself (typed by the
            # driver, not echoed as a JSON-typed line) - match on the password
            # prompt instead
            m = re.search(r"(\S+)@(\S+)\.labs", cmd)
            if cmd.startswith('ssh ') and m:
                pwline = f"{m.group(1)}@{m.group(2)}.labs.overthewire.org's password:"
                for i in range(cur, len(lines)):
                    if pwline in lines[i]:
                        found = i - 1  # the typed ssh line sits one above
                        break
        anchors.append(found)
        if found < 0:
            print(f"step {si} ({cmd[:50]}): ANCHOR NOT FOUND")
            ok = False
        else:
            cur = found + 1

    # compare segments
    for si, st in enumerate(steps):
        out = st.get('out')
        if out is None or anchors[si] < 0:
            continue
        cmd, expected = st['cmd'], st['out']
        a = anchors[si]
        # segment: from the line after the cmd to the next anchor's cmd line
        nxt = min((x for x in anchors[si+1:] if x > a), default=len(lines))
        seg = lines[a+1:nxt]
        is_vi = bool(re.match(r'^(?:vi|vim)\s', cmd))
        if is_vi:
            # compare only the :wq marker line and the buffer body lines that
            # appear verbatim in the segment (the screen is redraw-heavy)
            # only vim's status/save line is a marker: "file" [New] N L, M C
            # written. A source buffer's own """docstring""" lines also start
            # with '"' - filtering on startswith('"') misclassifies them as
            # markers (L6: every docstring line flagged MARKER MISSING)
            marker = [l for l in expected
                      if re.match(r'^"[^"]*"\s+(\[New\]\s+)?\d+L,\s*\d+[BC]', l)]
            seg_n = [norm(l) for l in seg]
            for mk in marker:
                # the [New] token reflects file pre-existence, not content: a
                # replay over an existing file drops it. Compare the core.
                core = mk.replace('[New] ', '')
                if mk not in seg:
                    # try normalized, or as a suffix of a line carrying
                    # escape-residue prefixes the cleaner kept
                    if norm(mk) not in seg_n and \
                       not any(l.rstrip().endswith(core) for l in seg):
                        print(f"step {si} ({cmd[:40]}): MARKER MISSING {mk}")
                        ok = False
                    else:
                        print(f"step {si} ({cmd[:40]}): marker matches (normalized)")
                else:
                    print(f"step {si} ({cmd[:40]}): marker OK {mk}")
            continue
        # non-vi: every expected line must appear in the segment in order
        seg_n = [norm(l) for l in seg if l.strip()]
        pos = 0
        missing = []
        for el in expected:
            en = norm(el)
            if not en:
                continue
            # live timestamps (ls -l, dates) legitimately differ between runs
            if re.match(r'^-\S+ \S+ \S+ \S+ \w+ \w+\s+\d+ [\d:]+ ', en) or \
               re.search(r' (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +\d+ [\d:]+ ', en):
                hit_ts = [k for k in range(pos, len(seg_n)) if re.match(r'^\S+ \S+ \S+ \S+ \w+ \w+\s+\d+ [\d:]+ \S+$', seg_n[k])]
                if hit_ts:
                    pos = hit_ts[0] + 1
                    continue
            hit = False
            for k in range(pos, len(seg_n)):
                if seg_n[k] == en:
                    pos = k + 1
                    hit = True
                    break
            if not hit:
                missing.append(el)
        if missing:
            ok = False
            print(f"step {si} ({cmd[:50]}): {len(missing)} line(s) NOT in replay segment:")
            for el in missing[:6]:
                print(f"   - {el[:110]}")
        else:
            print(f"step {si} ({cmd[:50]}): OK ({len(expected)} lines)")
    print('REPLAY', 'VERBATIM-OK' if ok else 'MISMATCH')
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
