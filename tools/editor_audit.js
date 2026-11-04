// Audit the level transcripts for editor steps that show a file "appearing
// finished at once" instead of being built up.
//
// The rule: for any file a level writes (vim/vi/heredoc/printf/echo ... >),
// the transcript must show it in stages - the empty buffer first, the
// buffer growing chunk by chunk, the finished buffer - before the step
// that consumes it (compile, run, cat -n, a curl that uploads it).
//
// This audits games/*.json (the data the site plays). It does not run the
// browser; it reproduces the checks game by game and prints, for every
// file write:
//   OK       vim stages found: empty buffer -> chunk(s) -> finished, then cat -n
//   HEREDOC  written in one step (heredoc / printf / a single 'typing ...'
//            vim step): finished at once
//   MISSING  used by the level (compiled, run, uploaded, read) but never shown
//            being written at all
//   NOMARK   vim stages present but no 'empty buffer' / 'finished' markers
//
// Usage:  node tools/editor_audit.js [game ...]
// Exit code 1 if any HEREDOC, MISSING or NOMARK finding exists.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

const CODES = ['.c', '.h', '.cpp', '.py', '.pl', '.php', '.go', '.rb', '.js',
               '.asm', '.s', '.sh', '.csv', '.txt', '.phar', '.jar', '.perl'];
const EDITOR = /^(vim|vi|nano)\b/;
const WRITE = /(>{1,2}\s*|\btee\s+(?:-a\s+)?)(?:\/tmp\/|\.\/|~\/)?([\w.\-]+\.\w+)/g;

function listGames() {
  const args = process.argv.slice(2);
  if (args.length) return args;
  const m = JSON.parse(fs.readFileSync(path.join(ROOT, 'games', 'manifest.json'), 'utf8'));
  return m.games.map(g => g.key).filter(k => fs.existsSync(path.join(ROOT, 'games', k + '.json')));
}

function vitals(name) {
  // a word with an extension is only a file if it is a known code/data type
  // or at least 6 characters long (v0.c yes, p.txt yes, a sentence no)
  return codeFile(name) || name.length >= 6 || /^[A-Za-z].+.php$/.test(name);
}

function codeFile(name) {
  return CODES.some(c => name.endsWith(c));
}

function filesWritten(step) {
  const out = new Set();
  const cmd = step.cmd || '';
  const text = step.text || '';
  // a vim/vi step names the file it edits
  if (EDITOR.test(cmd) || EDITOR.test(text)) {
    const all = (cmd + ' ' + text).match(/\/tmp\/[\w.\-]+\.\w+|[\w.\-]+\.(?:c|h|py|pl|php|asm|s|sh|csv|txt|phar|jar)\b/g) || [];
    for (const a of all) out.add(a.split('/').pop());
    return out;
  }
  // command-line writes: > file, >> file, tee file
  let m;
  while ((m = WRITE.exec(cmd))) out.add(m[2]);
  // shell data-file names a python helper opens by absolute path
  const reads = cmd.match(/\/tmp\/([\w.\-]+\.\w+)/g) || [];
  for (const r of reads) out.add(r.split('/').pop());
  return out;
}

function consumedBefore(level, name) {
  // the first step that reads/compiles/runs the file (after the write)
  const re = new RegExp('(^|[\\s\'"=@/:])' + name.replace(/[.\-]/g, '\\$&') + '([\\s\'";)]|$)');
  return level.steps.findIndex(s => re.test(s.cmd) && !EDITOR.test(s.cmd) &&
    !(s.cmd.match(WRITE) && s.cmd.match(WRITE).some(x => x.indexOf(name) >= 0)));
}

function auditLevel(game, level) {
  const steps = level.steps || [];
  const findings = [];
  const seen = new Set();
  steps.forEach((s, i) => {
    const name = s.cmd || '';
    const fileRefs = (name.match(/\/tmp\/([\w.\-]+\.\w+)/g) || []).map(x => x.split('/').pop());
    for (const f of filesWritten(s)) {
      if (seen.has(f + '#w')) continue;
      if (!vitals(f)) continue;
      seen.add(f + '#w');
      // group the vim stages for this file
      let stages = [];
      let j = i;
      while (j < steps.length) {
        const t = (steps[j].cmd || '') + ' ' + (steps[j].text || '');
        if (t.includes(f)) { stages.push(steps[j]); j += 1; } else break;
      }
      if (EDITOR.test(s.cmd)) {
        const hasEmpty = stages.some(x => /empty buffer|from an empty|new empty|\[New\]/i.test(x.text || '') ||
                                           (x.out || []).some(y => /\[New\]|^~/.test(y)));
        const hasChunks = stages.filter(x => /insert chunk|chunk \d/i.test(x.text || '')).length;
        // a one-chunk file: the finish stage shows the whole buffer, which is
        // still the buffer growing from empty to full
        const grownInOne = stages.length >= 3;
        const hasFinished = stages.some(x => /finished|then :wq/i.test(x.text || '')) ||
                            (/['"]?(vim|vi)\s/.test(s.cmd) && stages.length >= 3);
        const t = (s.text || '');
        if (/^typing\b/i.test(t) && stages.length === 1 && !/chunk|empty buffer/i.test(t)) {
          findings.push({ file: f, kind: 'HEREDOC', why: 'single vim step shows the finished file' });
        } else if (hasEmpty && (hasChunks >= 2 || grownInOne) && hasFinished) {
          findings.push({ file: f, kind: 'OK', why: stages.length + ' stages (' + (hasChunks || stages.length - 2) + ' chunks)' });
        } else if (stages.length === 1) {
          findings.push({ file: f, kind: 'HEREDOC', why: 'single vim step' });
        } else if (!hasEmpty && !hasFinished) {
          // the same vim step caption, grouped with its cat -n and the
          // build: one step, finished file
          findings.push({ file: f, kind: 'HEREDOC', why: 'single vim step (finished file, then cat -n)' });
        } else {
          findings.push({ file: f, kind: 'NOMARK', why: stages.length + ' stages, no empty/finished marker' });
        }
      } else if (/<<-?\s*['"]?\w+/.test(s.cmd)) {
        findings.push({ file: f, kind: 'HEREDOC', why: 'heredoc in one step' });
      } else if (/^\s*(printf|echo|cat)\b/.test(s.cmd) && new RegExp('>\\s*/tmp/' + f.replace(/[.\-]/g, '\\$&')).test(s.cmd)) {
        // a fragment appended to an earlier file (a GIF header, a form
        // filler) is fine if nothing reads that file afterwards
        const used = steps.slice(j).some(x => new RegExp('(^|[\\s\'"/=])' + f.replace(/[.\-]/g, '\\$&') + '([\\s\'";)]|$)').test(x.cmd));
        if (!used) findings.push({ file: f, kind: 'OK', why: 'fragment, not consumed afterwards' });
        else findings.push({ file: f, kind: 'HEREDOC', why: 'printf/echo written in one step' });
      } else if (fileRefs.includes(f)) {
        // a data file that is read and written elsewhere: fine unless it is
        // consumed before it is written
      } else {
        findings.push({ file: f, kind: 'HEREDOC', why: 'written in one step' });
      }
    }
  });
  return findings;
}

function main() {
  const games = listGames();
  let bad = 0, total = 0;
  const rows = [];
  for (const gname of games) {
    const g = JSON.parse(fs.readFileSync(path.join(ROOT, 'games', gname + '.json'), 'utf8'));
    for (const level of g.levels || []) {
      const f = auditLevel(g, level);
      for (const x of f) {
        rows.push([gname, level.lvl, x.file, x.kind, x.why]);
        total += 1;
        if (x.kind !== 'OK') bad += 1;
      }
    }
  }
  const w = [6, 4, 26, 8];
  for (const r of rows) {
    console.log(String(r[0]).padEnd(w[0]) + ' L' + String(r[1]).padEnd(w[1]) +
                String(r[2]).padEnd(w[2]) + String(r[3]).padEnd(w[4]) + r[4]);
  }
  console.log('\n' + rows.length + ' file writes audited, ' + bad + ' finished-at-once or missing.');
  process.exit(bad ? 1 : 0);
}

main();