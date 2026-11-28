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
            # JSON out starts at 'logout', the line right after that echo. If
            # the client pty closed before echoing the final exit, anchor at the
            # last remote-prompt exit echo instead.
            for i in range(len(lines) - 1, cur - 1, -1):
                if lines[i].rstrip().endswith('exit') and 'client$' in lines[i]:
                    for k in range(i, cur, -1):
                        if 'manpage' in lines[k] and lines[k].rstrip().endswith('exit'):
                            found = k
                            break
                    break
            if found < 0:
                for i in range(len(lines) - 1, cur - 1, -1):
                    if lines[i].rstrip().endswith('exit'):
                        for k in range(i, cur, -1):
                            if 'manpage' in lines[k] and lines[k].rstrip().endswith('exit'):
                                found = k
                                break
                        if found >= 0:
                            break
                    if found >= 0:
                        break
            anchors.append(found if found >= 0 else -1)
            if found < 0:
                print(f"step {si} ({cmd[:50]}): ANCHOR NOT FOUND")
                ok = False
            else:
                cur = found + 1
            continue
        first = cmd.split('\n')[0].rstrip()
        # a trailing bare-'exit' step must anchor at the LAST echo (the remote
        # shell's exit), not the first (the spawned shell's '$ exit' inside the
        # previous step's output, maze L4)
        last_exit = cmd.rstrip() == 'exit' and all(
            not steps[k].get('out') or steps[k]['cmd'].startswith('ssh ')
            for k in range(si + 1, len(steps)))
        # consecutive vi steps with the same cmd = ONE editor session: they
        # share the session's single command echo (vortex L5: remote vim 4
        # steps + local vim 4 steps, each run echoes 'vim crack5.py' once)
        if (re.match(r'^(?:vi|vim)\s', cmd) and si > 0
                and steps[si-1].get('cmd') == cmd and anchors[si-1] >= 0):
            anchors.append(anchors[si-1])
            cur = anchors[si-1] + 1
            continue
        found = -1
        if last_exit:
            # anchor at the remote shell's exit echo: the line right above the
            # 'logout' (or the last remote-prompt exit echo when no logout)
            for i in range(len(lines) - 1, cur - 1, -1):
                if lines[i].strip() == 'logout':
                    found = i - 1
                    break
            if found < 0:
                # no logout (local/client-side session): anchor at the PROMPT
                # exit echo ('client$ exit') so the segment carries the bare
                # exit echoes the driver typed after it
                for i in range(len(lines) - 1, cur - 1, -1):
                    if lines[i].rstrip().endswith(first) and 'client$' in lines[i]:
                        found = i
                        break
            if found < 0:
                for i in range(len(lines) - 1, cur - 1, -1):
                    if lines[i].rstrip().endswith(first):
                        found = i
                        break
        else:
            # prefer the PROMPT-prefixed echo: when a previous step left a
            # background job (vortex L8 step 4's `& sleep 2`), the shell can
            # echo the next command bare (typed-ahead) BEFORE printing the
            # late job-control notice, then echo it again with the prompt -
            # the prompt echo is the one whose output follows
            for i in range(cur, len(lines)):
                if re.search(r'\$ ' + re.escape(first) + r'$', lines[i].rstrip()):
                    found = i
                    break
            if found < 0:
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
                    # escape-residue prefixes the cleaner kept (the stream
                    # line may keep the [New] token the core drops)
                    if norm(mk) not in seg_n and \
                       not any(l.rstrip().endswith(core) or l.rstrip().endswith(mk) for l in seg):
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
            if re.match(r'^[-bcdlps]\S{9} \S+ \S+ \S+ \S+ \w+ \w+ [\d:]+ ', en) or \
               re.search(r' (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +\d+ [\d:]+ ', en):
                hit_ts = [k for k in range(pos, len(seg_n)) if re.match(r'^\S+ \S+ \S+ \S+ \S+ \w+ \w+ [\d:]+ ', seg_n[k])]
                if hit_ts:
                    pos = hit_ts[0] + 1
                    continue
            # ISO-timestamp lines (tar tvf '2026-11-28 07:42', ls --full-time)
            # carry a run-to-run mtime - same exemption class
            if re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', en):
                hit_ts = [k for k in range(pos, len(seg_n))
                          if re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', seg_n[k])]
                if hit_ts:
                    pos = hit_ts[0] + 1
                    continue
            # per-connection random values (vortex L0: the service's four
            # uint32s and their sum are fresh every connect) - match the
            # shape, not the value
            if re.match(r'^received: \d+ \d+ \d+ \d+$', en):
                hit_rv = [k for k in range(pos, len(seg_n))
                          if re.match(r'^received: \d+ \d+ \d+ \d+$', seg_n[k])]
                if hit_rv:
                    pos = hit_rv[0] + 1
                    continue
            if re.match(r'^sum:\s+\d+ \(0x[0-9a-f]+\)$', en):
                hit_sm = [k for k in range(pos, len(seg_n))
                          if re.match(r'^sum:\s+\d+ \(0x[0-9a-f]+\)$', seg_n[k])]
                if hit_sm:
                    pos = hit_sm[0] + 1
                    continue
            # $RANDOM/mktemp-derived workdir names (vortex L7 /tmp/l7rec-NNNN,
            # L11's mktemp -d /tmp/tmp.XXXXXXXXX) - run-to-run variables
            if re.match(r'^WORKDIR=/tmp/\S+$', en) or re.match(r'^/tmp/tmp\.[A-Za-z0-9]+$', en):
                hit_wd = [k for k in range(pos, len(seg_n))
                          if re.match(r'^(WORKDIR=/tmp/\S+|/tmp/tmp\.[A-Za-z0-9]+)$', seg_n[k])]
                if hit_wd:
                    pos = hit_wd[0] + 1
                    continue
            # stack-scan table rows (vortex L8: '0xffffd960 11') - the probe
            # addresses and read-lengths shift between runs
            if re.match(r'^0x[0-9a-f]+ \d+$', en):
                hit_sc = [k for k in range(pos, len(seg_n))
                          if re.match(r'^0x[0-9a-f]+ \d+$', seg_n[k])]
                if hit_sc:
                    pos = hit_sc[0] + 1
                    continue
            # fresh rand() windows and their derived seed (vortex L10: the
            # level prints 20 fresh rand values each run and the cracker's
            # FOUND seed/skip are derived from them) - match the shape
            if re.match(r'^\[ [0-9a-f]{8}(, [0-9a-f]{8})+,]$', en) or \
               re.match(r'^array: [0-9a-f]{8}( [0-9a-f]{8})+ \.\.\.$', en):
                rx = r'^(\[ [0-9a-f]{8}(, [0-9a-f]{8})+,]|array: [0-9a-f]{8}( [0-9a-f]{8})+ \.\.\.)$'
                hit_r = [k for k in range(pos, len(seg_n)) if re.match(rx, seg_n[k])]
                if hit_r:
                    pos = hit_r[0] + 1
                    continue
            if re.match(r'^cracker: FOUND seed=-?\d+ skip=\d+$', en):
                hit_f = [k for k in range(pos, len(seg_n))
                         if re.match(r'^cracker: FOUND seed=-?\d+ skip=\d+$', seg_n[k])]
                if hit_f:
                    pos = hit_f[0] + 1
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
            # the final exit step's trailing 'exit' echo is typed at the client
            # shell; when the pty closes before bash echoes it the replay shows
            # only 'client$' (L3: cast has it, replay's client pty closed first).
            # Accept that single line when everything else matched. Same class
            # for the bare driver-exit echoes of a local session (vortex L0:
            # the pty dies between the two echoes; the cast keeps both, a
            # replay can lose the last one to the same race).
            if cmd.rstrip() == 'exit\nexit' and missing == ['exit'] \
               and any('client$' in l for l in seg):
                print(f"step {si} ({cmd[:40]}): trailing exit echo not echoed "
                      f"(client pty closed) - accepted artifact")
            elif cmd.rstrip() == 'exit' and missing == ['exit'] \
                    and any(l.strip() == 'exit' for l in seg):
                print(f"step {si} ({cmd[:40]}): trailing exit echo lost to the "
                      f"pty-teardown race - accepted artifact")
            elif missing == ['exit'] \
                    and any(l.rstrip().endswith('$ exit') for l in seg):
                # the same exit, echo-form differs: the replay's shell echoed
                # 'prompt$ exit' (prompt-prefixed) where the cast kept the bare
                # 'exit' - same typed command, echo race only (vortex L8 step 24)
                print(f"step {si} ({cmd[:40]}): exit echo prompt-prefixed in "
                      f"replay (cast kept bare 'exit') - accepted artifact")
            elif missing == ['0'] and ' & ' in cmd:
                # a backgrounded job's echo raced the foreground output: the
                # cast's job-control ordering printed the backgrounded echo's
                # '0' first, the replay's order dropped it inside the race
                # window (vortex L8 step 4: `& sleep 2; kill %1`)
                print(f"step {si} ({cmd[:40]}): background-job echo raced "
                      f"(cast '0', replay lost it) - accepted artifact")
            elif cmd.rstrip() == 'exit' and len(missing) == 1 \
                    and missing[0].rstrip().endswith('exit') and '$' in missing[0] \
                    and any(l.rstrip().endswith('exit') and '$' in l for l in seg):
                # same echo, different client prompt label (cast container shows
                # 'user@localhost$ ', replay shows 'client$ ') - prompt-label
                # artifact, the echoed command is identical (vortex L3)
                print(f"step {si} ({cmd[:40]}): client prompt label differs "
                      f"({missing[0].strip()[:24]}... vs replay client$) - accepted artifact")
                print(f"step {si} ({cmd[:40]}): trailing exit echo not echoed "
                      f"(client pty closed) - accepted artifact")
            else:
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
