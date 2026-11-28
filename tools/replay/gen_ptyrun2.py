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
            editor = cmd.split()[0]
            # collect the whole vi run; the LAST staged step holds the full buffer
            j = i
            buf = []
            rows = {}
            while j < len(steps) and steps[j]['cmd'] in (f'vi {fname}', f'vim {fname}'):
                cand = steps[j]['out']
                if isinstance(cand, list):
                    # drop only vim's status/save line ("file" [New] N L, M C
                    # written) - NOT every line starting with '"': a source
                    # buffer's own """docstring""" lines start with '"' too and
                    # are SOURCE TEXT; stripping them corrupts the saved file
                    # (the L6 replay's sc.py/w6.py SyntaxError was exactly
                    # this). Match the full status shape including [New].
                    # the cast stream strips the ESC before the save marker's
                    # opening quote, so the marker can start with '="' too
                    body = [l for l in cand if l != '~'
                            and not re.match(r'^.{0,2}"[^"]*"\s+(\[New\]\s+)?\d+L,\s*\d+[BC]', l)]
                    # staged screens (site convention, parseVimScreen): buffer
                    # rows carry a right-aligned line number prefix; chrome rows
                    # (status line, -- INSERT --, bare '  1' of an empty buffer)
                    # don't map to buffer text. Strip the numbers, drop chrome.
                    if body and re.match(r'^\s*\d+(?: |$)', body[0]):
                        clean = []
                        for l in body:
                            nm = re.match(r'^\s*(\d+) (.*)$', l)
                            if nm:
                                clean.append(nm.group(2))
                        body = clean
                    # union the staged screens: each carries a window of the
                    # buffer keyed by absolute line number; later screens
                    # overwrite earlier rows (retyped lines) - the union at the
                    # end of the run = the final buffer
                    if body and re.match(r'^\s*\d+(?: |$)', steps[j]['out'][0] if steps[j]['out'] else ''):
                        for l in steps[j]['out']:
                            nm = re.match(r'^\s*(\d+) (.*)$', l)
                            if nm:
                                rows[int(nm.group(1))] = nm.group(2)
                j += 1
            if rows:
                buf = [rows[k] for k in sorted(rows)]
            out.append(f'@{editor} {fname}')
            out.extend(buf)
            out.append('@viend')
            i = j
            continue
        # an 'ssh -i key ...' line is a typed command from the current
        # shell (key auth), NOT a ptyrun2 login - only password-logins with a
        # user@host but no -i are ptyrun2's own (bandit L13's client-side
        # key-auth ssh must be typed, not re-login'd)
        if cmd.startswith('ssh ') and ' -i ' not in cmd:
            if i == 0:
                pass  # ptyrun2 performs the typed login itself
            else:
                # the preceding step is usually the logout 'exit' already
                # emitted - a second one would close the CLIENT shell and
                # strand the re-login in a dead pty (vortex L3 replay)
                if not (out and out[-1] == '@line exit'):
                    out.append('@line exit')
                out.append('@sleep 2')
                out.append('@login2')
            i += 1
            continue
        if cmd == 'exit' and i + 1 >= len(steps):
            out.append('@line exit')
            i += 1
            continue
        # a step's cmd may carry several real commands (e.g. the manpage L0 gdb
        # session: gdb -> set debuginfod enabled off -> disassemble -> run -> info ->
        # quit -> y). Each line is a real typed command - emit one @line per line.
        for cl in cmd.split('\n'):
            out.append(f'@line {cl}')
        if cmd.startswith('ssh ') and ' -i ' in cmd:
            # a typed key-auth ssh opens a NEW remote session: pause so the
            # MOTD finishes before the next command is typed (typing during
            # the banner echoes ahead into the client and the remote never
            # sees it - bandit L13's replay)
            out.append('@sleep 8')
        i += 1
    print('\n'.join(out))

if __name__ == '__main__':
    main()
