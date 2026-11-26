#!/usr/bin/env python3
"""gen_ptyrun2.py GAME LVL — generate a ptyrun2 cmdfile from games/<game>.json.

Rule 4 (post-solve verbatim): the level's steps[] are replayed against the
real server in a fresh live pty session, with the vi/vim editing driven
character-by-character exactly as the cast typed it. This generator turns the
JSON steps into a ptyrun2 driver:
  - every command step  -> "@line <cmd>" (typed verbatim)
  - a run of vi steps   -> "@vi <file>" + the final staged buffer typed into
    insert mode (the cast's own mechanism) + "@viend"
  - a second ssh step   -> "@exit" marker (ptyrun2 exits the remote shell and
    the driver logs in again with the next level's user; pass passwords via
    --login)
The generated script is written to stdout; run it with ptyrun2.py and diff
with diff_replay.py.
"""
import json, re, sys

ROOT = __file__.rsplit('/', 3)[0]

def main():
    game, lvl = sys.argv[1], int(sys.argv[2])
    levels = json.load(open(f'{ROOT}/games/{game}.json'))['levels']
    lv = next(l for l in levels if l['lvl'] == lvl)
    steps = lv['steps']
    out = []
    i = 0
    while i < len(steps):
        st = steps[i]
        cmd = st['cmd']
        m = re.match(r'^(?:vi|vim)\s+(\S+)$', cmd)
        if m:
            fname = m.group(1)
            # collect the whole vi run; the LAST staged step holds the full buffer
            j = i
            buf = []
            while j < len(steps) and steps[j]['cmd'] in (f'vi {fname}', f'vim {fname}'):
                cand = steps[j]['out']
                if isinstance(cand, list):
                    body = [l for l in cand if l != '~' and not l.startswith('"')]
                    if len(body) > len(buf):
                        buf = body
                j += 1
            out.append(f'@vi {fname}')
            out.extend(buf)
            out.append('@viend')
            i = j
            continue
        if cmd.startswith('ssh '):
            if i == 0:
                pass  # ptyrun2 performs the typed login itself
            else:
                out.append('@line exit')
                out.append('@sleep 2')
                out.append('@login2')
            i += 1
            continue
        if cmd == 'exit' and i + 1 >= len(steps):
            out.append('@line exit')
            i += 1
            continue
        out.append(f'@line {cmd}')
        i += 1
    print('\n'.join(out))

if __name__ == '__main__':
    main()
