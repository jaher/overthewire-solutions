#!/usr/bin/env python3
"""Narration coverage + alignment audit for overthewire-solutions.

Usage: python3 tools/narration_audit.py [--md narration/COVERAGE.md]

Denominator: every level the site renders — games/*.json levels plus the
34 Bandit levels inlined in index.html. For each level: does a narration
script exist? an mp3? And a heuristic alignment signal: the distinctive
command/file tokens of the level's transcript vs the words its narration
uses, plus narration-only command names (a command the narration names
that no typed step ever runs — the classic drift signal, e.g. a gdb
confirmation or an ssh verification the transcript never types).
"""
import json, glob, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

STOP = set("""the and for with from into that this then when after before file
level password user host port ssh vim cat cd ls echo test read write open close
run runs running using use used get gets got make makes find found check checks
show shows print prints return returns value values first second next last new
one two three four five six seven eight nine ten""".split())

# Tool names that (almost) never occur as ordinary prose. A hit means the
# narration names a tool no typed step ever runs — hand-review each one.
COMMANDS = """gdb strace ltrace ssh nasm objdump readelf xxd hexdump netcat ncat
socat curl wget openssl nmap john hashcat hydra sqlmap tcpdump radare2 ghidra
msfconsole burpsuite nikto gobuster ffuf sqlmap""".split()


def levels():
    out = {}
    html = open('index.html').read()
    m = re.search(r'const LEVELS = \[(.*?)\n\];', html, re.S)
    bandit = re.findall(r'"lvl":(\d+)', m.group(1))
    out['bandit'] = [int(x) for x in bandit]
    for f in sorted(glob.glob('games/*.json')):
        if 'manifest' in f:
            continue
        d = json.load(open(f))
        out[os.path.basename(f)[:-5]] = [l['lvl'] for l in d['levels']]
    return out


def level_data(game):
    if game == 'bandit':
        html = open('index.html').read()
        m = re.search(r'const LEVELS = \[(.*?)\n\];', html, re.S)
        return [json.loads(x) for x in re.findall(r'\{"lvl".*?\}\s*(?=,\n|\n\])',
                                                    m.group(1) + '\n]')]
    d = json.load(open(f'games/{game}.json'))
    return d['levels']


def distinctive_tokens(level):
    cmds = []
    for s in level.get('steps', []) or []:
        cmds.append(s.get('cmd') or '')
        if s.get('text'):
            cmds.append(s['text'])
    for grp in level.get('cmds', []) or []:
        cmds.extend(grp)
    toks = set()
    for c in cmds:
        for w in re.findall(r'[a-zA-Z][a-zA-Z0-9_.\-/]{2,}', c.lower()):
            base = w.split('/')[-1].split('.')[0]
            if base and base not in STOP and len(base) >= 3:
                toks.add(base)
            if '/' in w or '.' in w:
                toks.add(w)
    return toks, ' '.join(cmds).lower()


def main():
    lvls = levels()
    rows = []
    for game in sorted(lvls):
        data = {l['lvl']: l for l in level_data(game)}
        for lv in lvls[game]:
            txt_p = f'narration/{game}/L{lv}.txt'
            mp3_p = f'narration/{game}/L{lv}.mp3'
            txt = open(txt_p).read() if os.path.exists(txt_p) else None
            mp3 = os.path.exists(mp3_p)
            toks, cmdtext = distinctive_tokens(data[lv])
            narr_only = sorted(c for c in COMMANDS
                               if txt and re.search(r'\b' + re.escape(c) + r'\b', txt.lower())
                               and not re.search(r'\b' + re.escape(c) + r'\b', cmdtext))
            rows.append(dict(game=game, lv=lv, txt=txt is not None, mp3=mp3,
                             narr_only=narr_only))
    tot = len(rows)
    ntxt = sum(1 for r in rows if r['txt'])
    nmp3 = sum(1 for r in rows if r['mp3'])
    flagged = [r for r in rows if r['txt'] and r['narr_only']]
    # Hand-verified (2026-11-15) against the full level JSON (cmds, text, out)
    # and the writeup: a flag is a REAL gap only if the tool is absent from
    # the entire site transcript. Aliases (nc = netcat, xxd = hexdump) and
    # negative mentions ("plain netcat will not work", "nm/readelf/ltrace
    # all refuse") are not gaps. Every real gap below IS in the writeup's
    # step-by-step section — the narration follows the writeup, the site
    # transcript trimmed the step out.
    VERIFIED = {
        ('behemoth', 0): 'objdump — narration disassembles main; transcript has no objdump step',
        ('behemoth', 1): 'gdb — narration confirms the layout in gdb; transcript has no gdb step',
        ('narnia', 1): 'nasm, objdump — narration assembles with nasm, checks with objdump, extracts with objcopy; transcript has none of the three',
        ('narnia', 2): 'gdb — narration confirms the layout in gdb; transcript has no gdb step',
        ('narnia', 4): 'strace — narration cites strace output; transcript has gdb but no strace',
        ('utumno', 2): 'gdb — narration confirms offsets in gdb; transcript has no gdb step',
        ('utumno', 3): 'gdb — narration confirms the arithmetic in gdb; transcript has no gdb step',
        ('utumno', 5): 'gdb — narration confirms the layout in gdb; transcript has no gdb step',
        ('utumno', 6): 'gdb — narration confirms the slot in gdb; transcript has no gdb step',
        ('utumno', 7): 'gdb — narration cites gdb output; transcript has no gdb step',
        ('vortex', 0): 'ssh — narration verifies by logging in over SSH on port 2228; transcript has no ssh step (fixed in the pilot: sentence rewritten to the service reply)',
    }
    NOT_GAPS = {
        ('bandit', 12): 'hexdump names the file; xxd -r is typed',
        ('bandit', 14): 'netcat = nc, typed',
        ('bandit', 15): 'negative mention — "plain netcat will not work"',
        ('bandit', 20): 'netcat = nc, typed in a compound command',
        ('bandit', 24): 'netcat = nc, typed inside the for loop',
        ('utumno', 0): 'negative mention — "nm and readelf and ltrace all refuse"',
        ('utumno', 4): 'gdb IS in the transcript (false positive)',
    }
    lines = []
    lines.append('# Narration coverage audit')
    lines.append('')
    lines.append(f'Generated against origin/main. Site-rendered levels: **{tot}** '
                 f'— scripts **{ntxt}** ({tot - ntxt} missing), '
                 f'mp3 **{nmp3}** ({tot - nmp3} missing).')
    lines.append('')
    lines.append('| Game | Levels | Scripts | MP3s | Missing scripts | Missing mp3s |')
    lines.append('|---|---|---|---|---|---|')
    for game in sorted(lvls):
        gr = [r for r in rows if r['game'] == game]
        ms = ', '.join(f"L{r['lv']}" for r in gr if not r['txt']) or '—'
        mm = ', '.join(f"L{r['lv']}" for r in gr if not r['mp3']) or '—'
        lines.append(f"| {game} | {len(gr)} | {sum(1 for r in gr if r['txt'])} | "
                     f"{sum(1 for r in gr if r['mp3'])} | {ms} | {mm} |")
    lines.append('')
    lines.append('## Alignment flags')
    lines.append('')
    lines.append('`narr-only` = a tool the narration names that no typed step '
                 'ever runs. Each one was hand-checked against the level\'s '
                 'transcript and writeup; the ones below are real gaps (a '
                 'verification or inspection the script describes but the '
                 'site never types), not prose false positives.')
    lines.append('')
    lines.append('### Narration-only tools (named in the script, never typed)')
    lines.append('')
    if VERIFIED:
        for (g, lv), why in sorted(VERIFIED.items()):
            lines.append(f"- {g} L{lv}: {why}")
    else:
        lines.append('None.')
    lines.append('')
    lines.append('### Reviewed and cleared (not gaps)')
    lines.append('')
    for (g, lv), why in sorted(NOT_GAPS.items()):
        lines.append(f"- {g} L{lv}: {why}")
    lines.append('')
    lines.append('## Notes')
    lines.append('')
    lines.append('- Vortex L3 is solved (recordings/vortex/L3.cast, writeup) but '
                 'not yet in games/vortex.json, so it is outside this table; '
                 'it needs a script + mp3 + a site entry.')
    lines.append('- Vortex L4 is in progress (no solution yet).')
    lines.append('- manpage (5 levels) and maze (L0) are blocked games; their '
                 'site entries are stubs, so no narration is expected until '
                 'they are solved.')
    md = '\n'.join(lines) + '\n'
    if '--md' in sys.argv:
        path = sys.argv[sys.argv.index('--md') + 1]
        open(path, 'w').write(md)
        print(f'wrote {path}')
    print(f'TOTAL levels={tot} txt={ntxt} mp3={nmp3}')
    print(f'narr-only flags: {len(flagged)}')
    for r in flagged:
        print(f"FLAG {r['game']} L{r['lv']}: {','.join(r['narr_only'])}")


if __name__ == '__main__':
    main()
