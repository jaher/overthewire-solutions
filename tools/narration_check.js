// Headless check of the narration player, for one level: run index.html's
// script against a tiny DOM stub (same stub as player_check.js, plus a
// drivable fake audio element) and verify that the typed lines appear in
// time with the narration audio, the highlight tracks the spoken segment,
// the visible transcript panel renders the script and tracks the clock,
// and seek / pause / end all behave — through the whole narration.
// Usage: node tools/narration_check.js <game> <level>   (default: vortex 0)
// Exit 0 when every assertion passes, 1 otherwise.
// If a level fails ONLY on lateness (the render typing slower than the
// driven clock, not a real sync bug), re-run with SLOW=1: it drives the
// fake clock slower and widens the late tolerance.
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const GAME = process.argv[2] || 'vortex';
const LEVEL = parseInt(process.argv[3] || '0', 10);
const SLOW = !!process.env.SLOW;
const STEP_SLEEP = SLOW ? 250 : 150;   // real ms per 0.25s of audio
const LATE_TOL = SLOW ? 4.0 : 2.5;     // s a line may lag its spoken time
const EARLY_TOL = 0.6;                 // s a line may appear before its time

function El(tag) {
  this.tag = tag; this.children = []; this.style = {}; this.className = '';
  this._text = ''; this._q = {}; this.parent = null;
  this.scrollTop = 0; this.scrollHeight = 0; this.value = ''; this.innerHTML = '';
  this.dataset = {}; this._listeners = {};
  this.paused = true; this.currentTime = 0; this.duration = NaN; this.src = '';
}
Object.defineProperty(El.prototype, 'innerHTML', {
  get() { return ''; },
  set(v) { this.children = []; this._text = String(v); },
});
Object.defineProperty(El.prototype, 'textContent', {
  get() { return this._text; },
  set(v) { this._text = String(v); },
});
El.prototype.appendChild = function (c) { c.parent = this; this.children.push(c); return c; };
El.prototype.querySelector = function (sel) {
  if (!this._q[sel]) { const e = new El('span'); e.parent = this; this._q[sel] = e; }
  return this._q[sel];
};
El.prototype.remove = function () {
  if (this.parent) this.parent.children = this.parent.children.filter(x => x !== this);
};
El.prototype.addEventListener = function (type, fn) {
  (this._listeners[type] = this._listeners[type] || []).push(fn);
};
El.prototype.fire = function (type) {
  (this._listeners[type] || []).forEach(fn => fn());
};
El.prototype.play = function () { this.paused = false; return Promise.resolve(); };
El.prototype.pause = function () { this.paused = true; };
El.prototype.scrollIntoView = function () {};
Object.defineProperty(El.prototype, 'classList', {
  get() {
    const el = this;
    const has = (c) => el.className.split(/\s+/).includes(c);
    return {
      add(c) { if (!has(c)) el.className = (el.className + ' ' + c).trim(); },
      remove(c) { el.className = el.className.split(/\s+/).filter(x => x && x !== c).join(' '); },
      toggle(c, force) { const on = force === undefined ? !has(c) : force; if (on) this.add(c); else this.remove(c); return on; },
      contains(c) { return has(c); },
    };
  },
});
El.prototype.querySelectorAll = function (sel) {
  const out = [];
  const walk = (e) => { for (const c of e.children) { if (c.dataset && c.dataset.narrSeg) out.push(c); walk(c); } };
  walk(this);
  return out;
};

const byId = {};
let audioEl = null;
const document = {
  getElementById(id) { if (!byId[id]) { byId[id] = new El('div'); if (id === 'term') byId[id].__term = true; } return byId[id]; },
  createElement(tag) { const e = new El(tag); if (tag === 'audio') audioEl = e; return e; },
  title: '',
  activeElement: null,
};
const window = {};
global.document = document;
global.window = window;

const realSetInterval = setInterval;
global.setInterval = (fn, ms) => realSetInterval(fn, 1);

const realFetch = (url) => {
  const p = path.join(ROOT, url.replace(/^\.?\//, ''));
  if (!fs.existsSync(p)) return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
  return Promise.resolve({ ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) });
};
global.fetch = realFetch;

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error('no script found'); process.exit(1); }
const api = new Function(m[1] + "\n;return { GAMES, playLevel, fillLevels, setGame: g => { gameKey = g; }, getCur: () => cur, getRun: () => runId, getNarrMap: () => narrMap, isNarrOn: () => narrOn, getNarrBtn: () => narrBtn, getNarrSeek: () => narrSeek, getNarrAudio: () => narrAudio, getNarrKeySegs: () => narrKeySegs };")();
const { GAMES, playLevel, fillLevels, setGame, getNarrMap, isNarrOn, getNarrBtn, getNarrSeek, getNarrAudio, getNarrKeySegs } = api;

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let failures = 0;
function check(name, ok, detail) {
  console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (detail !== undefined ? '  — ' + detail : ''));
  if (!ok) failures++;
}

// Per-line scheduled times, recomputed from the sync map with the same rule
// the page uses (segment start + j/refs * segment length; first ref wins).
function lineTimes(map) {
  const times = new Map();
  map.segments.forEach((sg, si) => {
    const refs = [];
    for (const L of (sg.lines || [])) {
      if (L.role === 'out' && L.from !== undefined) {
        for (let i = L.from; i <= (L.to === undefined ? L.from : L.to); i++) refs.push(L.step + ':out:' + i);
      } else refs.push(L.step + ':' + L.role + ':');
    }
    refs.forEach((k, j) => {
      if (!times.has(k)) times.set(k, { t: sg.start + (refs.length > 1 ? (j / refs.length) * (sg.end - sg.start) : 0), seg: si });
    });
  });
  return times;
}

function vimFileOf(st) {
  const m = /^vim\s+(.+)$/.exec((st.cmd || '').trim());
  if (!m) return null;
  const parts = m[1].trim().split(/\s+/);
  return parts[parts.length - 1] || null;
}

// The sequence of term children playLevel renders, in order, as
// {key} (a narration-gated line) or {key: null} (an untagged line).
// Mirrors playLevel/playVimSession/typeText exactly.
function expectedChildren(L) {
  const seq = [];
  seq.push({ key: null });                 // opening blank line
  seq.push({ key: '-1:goal:' });           // goal div
  seq.push({ key: null });                 // host tag note
  if (L.steps) {
    let si = 0;
    while (si < L.steps.length) {
      const st = L.steps[si];
      const vf = vimFileOf(st);
      if (vf) {
        const firstSi = si;
        const run = [];
        while (si < L.steps.length && vimFileOf(L.steps[si]) === vf) { run.push(si); si++; }
        seq.push({ key: null });           // 'typing X in vim' note
        seq.push({ key: firstSi + ':vimcmd:' });
        // The box is created at the session-start gate, which waits on
        // vimcmd (not vim): when one segment anchors both, the schedule
        // spreads them (vimcmd at the start, vim at the midpoint), so the
        // box appears at the vimcmd time. Key it vimcmd so the early/late
        // checks use the session start; its vim tag lives only in the
        // div's own dataset, which the highlight check reads directly.
        seq.push({ key: firstSi + ':vimcmd:' });
        for (const s of run) if (L.steps[s].note) seq.push({ key: s + ':note:' });
        continue;
      }
      if (st.text) { seq.push({ key: si + ':text:' }); seq.push({ key: si + ':text:' }); }
      else if ((st.cmd || '').startsWith('#')) seq.push({ key: si + ':note:' });
      else seq.push({ key: si + ':cmd:' });
      for (let oi = 0; oi < (st.out || []).length; oi++) seq.push({ key: si + ':out:' + oi });
      if (st.note) seq.push({ key: si + ':note:' });
      si++;
    }
  }
  if (L.pw) seq.push({ key: '-1:pw:' });
  if (L.note) seq.push({ key: null });
  seq.push({ key: null });                 // closing blank line
  return seq;
}

(async () => {
  const syncPath = path.join(ROOT, 'narration', GAME, `L${LEVEL}.sync.json`);
  if (!fs.existsSync(syncPath)) { console.error('no sync map: ' + syncPath); process.exit(1); }
  const sync = JSON.parse(fs.readFileSync(syncPath, 'utf8'));
  const sched = lineTimes(sync);
  const cont = sync.segments.every((sg, i) =>
    (i === 0 ? Math.abs(sg.start) < 0.02 : Math.abs(sg.start - sync.segments[i - 1].end) < 0.02));
  check('sync map continuous 0 -> duration',
    cont && Math.abs(sync.segments[sync.segments.length - 1].end - sync.duration) < 0.05,
    `${sync.segments.length} segments, duration=${sync.duration}s`);
  const mp3 = path.join(ROOT, 'narration', GAME, `L${LEVEL}.mp3`);
  check('mp3 exists next to the script', fs.existsSync(mp3) && fs.statSync(mp3).size > 0,
    fs.existsSync(mp3) ? (fs.statSync(mp3).size + ' bytes') : 'missing');

  for (let i = 0; i < 200 && !GAMES[GAME]; i++) await sleep(20);
  if (!GAMES[GAME]) { console.error(GAME + ' not loaded'); process.exit(1); }
  await sleep(300);
  window.__userPickedGame = true;
  setGame(GAME); byId['gameSel'].value = GAME;
  fillLevels();
  const idx = GAMES[GAME].levels.findIndex(x => x.lvl === LEVEL);
  if (idx < 0) { console.error('level ' + LEVEL + ' not in ' + GAME); process.exit(1); }
  const L = GAMES[GAME].levels[idx];
  if (!L.steps) { console.error('level has no steps (legacy cmds) — cannot check'); process.exit(1); }
  const expected = expectedChildren(L);
  // scheduled times must be non-decreasing in render order, else the
  // narration walks the solution out of order and seek fast-forward stalls
  const ordered = expected.filter(e => e.key && sched.has(e.key)).map(e => sched.get(e.key).t);
  const mono = ordered.every((t, i) => i === 0 || t >= ordered[i - 1] - 0.01);
  check('scheduled times non-decreasing in render order', mono,
    mono ? `${ordered.length} gated lines` : 'narration references lines out of order');
  const firstPos = new Map();
  expected.forEach((e, i) => { if (e.key && !firstPos.has(e.key)) firstPos.set(e.key, i); });

  byId['speed'].value = '0.15';
  playLevel(idx);
  for (let i = 0; i < 100 && !getNarrMap(); i++) await sleep(20);
  check('sync map loads; Narrate button shown',
    !!getNarrMap() && getNarrBtn().style.display !== 'none',
    getNarrMap() ? `duration ${getNarrMap().duration}s` : 'no map');

  const audio = getNarrAudio();
  audio.duration = sync.duration;
  audio.fire('loadedmetadata');
  const term = byId['term'];
  const transcript = byId['narrTranscript'];
  const panelActive = () => {
    let a = -1;
    for (const d of transcript.children) if (d.classList.contains('active')) a = parseInt(d.dataset.seg, 10);
    return a;
  };
  check('transcript panel renders every segment with the script text',
    transcript.children.length === sync.segments.length &&
    transcript.children.every((d, i) => d.textContent === sync.segments[i].text) &&
    transcript.classList.contains('on'),
    `segments=${transcript.children.length} shown=${transcript.classList.contains('on')}`);

  getNarrBtn().onclick();
  await sleep(50);
  check('narration is on after pressing Narrate', isNarrOn() === true);

  const highlightedIdx = () => term.querySelectorAll('[data-narr-seg]')
    .filter(d => d.classList.contains('narr-hl'))
    .map(d => term.children.indexOf(d));
  const activeSegAt = (t) => {
    let active = -1;
    sync.segments.forEach((sg, i) => { if (t >= sg.start) active = i; });
    return active;
  };

  // --- drive the fake clock through the whole narration ---
  const early = [], late = [], hlBad = [], panelBad = [];
  let t = 0;
  const DT = 0.25;
  while (t < sync.duration) {
    t += DT;
    if (!audio.paused) { audio.currentTime = t; audio.fire('timeupdate'); }
    // The highlight is applied synchronously by the timeupdate handler to
    // the divs present NOW; divs the render creates afterwards catch up at
    // the next tick, so snapshot the expected highlight set here, before
    // the sleep, and compare against it after. Read the player's own
    // tagging off each div: the vim box carries the merged segment list
    // of its whole run, so it highlights through every chunk.
    const active = activeSegAt(audio.currentTime);
    const wantNow = [];
    for (let i = 0; i < term.children.length; i++) {
      const d = term.children[i];
      if (d.dataset && d.dataset.narrSeg && d.dataset.narrSeg.split(' ').indexOf(String(active)) >= 0) wantNow.push(i);
    }
    const panelNow = panelActive();
    await sleep(STEP_SLEEP);
    const now = audio.currentTime;
    const n = term.children.length;
    // (a) no gated line may appear before its spoken time
    for (let i = 0; i < n; i++) {
      const k = expected[i] && expected[i].key;
      const e = k && sched.get(k);
      if (e && e.t > now + EARLY_TOL) early.push(`child[${i}] ${k} at ${now.toFixed(2)} (scheduled ${e.t.toFixed(2)})`);
    }
    // (b) every gated line scheduled <= now - LATE_TOL must exist by now
    for (const [k, e] of sched) {
      if (e.t <= now - LATE_TOL && firstPos.has(k) && firstPos.get(k) >= n) {
        late.push(`${k} missing at ${now.toFixed(2)} (scheduled ${e.t.toFixed(2)})`);
      }
    }
    // (c) highlighted divs == present divs tagged with the active segment
    // (as snapshotted at the timeupdate, before the sleep). Read the
    // player's own tagging off each div: the vim box carries the merged
    // segment list of its whole run, so it highlights through every chunk.
    const got = highlightedIdx();
    if (wantNow.sort().join(',') !== got.sort().join(',')) {
      hlBad.push(`t=${now.toFixed(2)} seg=${active} want=[${wantNow.join(',')}] got=[${got.join(',')}]`);
    }
    // (d) transcript panel tracks the clock
    if (panelNow !== active) panelBad.push(`t=${now.toFixed(2)} panel=${panelNow} active=${active}`);
    if (early.length > 5 || late.length > 5 || hlBad.length > 5 || panelBad.length > 5) break;
  }
  check('no typed line appears before its spoken time', early.length === 0,
    early.length ? early.slice(0, 3).join(' | ') : '0 early lines');
  check(`no typed line lags its spoken time by >${LATE_TOL}s`, late.length === 0,
    late.length ? late.slice(0, 3).join(' | ') : '0 late lines');
  check('highlighted lines == lines tagged with the active segment (every tick)', hlBad.length === 0,
    hlBad.length ? hlBad.slice(0, 3).join(' | ') : '0 mismatches');
  check('transcript panel active segment tracks the audio clock (every tick)', panelBad.length === 0,
    panelBad.length ? panelBad.slice(0, 3).join(' | ') : '0 mismatches');

  // --- seek to ~60% and re-render fast-forwarded ---
  const seekSeg = sync.segments.reduce((best, sg, i) =>
    Math.abs(sg.start - sync.duration * 0.6) < Math.abs(sync.segments[best].start - sync.duration * 0.6) ? i : best, 0);
  const seekT = sync.segments[seekSeg].start;
  audio.currentTime = seekT; audio.fire('seeked');
  getNarrSeek().value = String(seekT);
  getNarrSeek().fire('input');
  getNarrSeek().fire('change');
  await sleep(SLOW ? 3000 : 2000);
  const nAfter = term.children.length;
  const missingPast = [], presentFuture = [];
  for (const [k, e] of sched) {
    if (!firstPos.has(k)) continue;
    if (e.t <= seekT && firstPos.get(k) >= nAfter) missingPast.push(k);
    if (e.t > seekT + EARLY_TOL && firstPos.get(k) < nAfter) presentFuture.push(k);
  }
  check(`after seek to ${seekT.toFixed(1)}s (seg ${seekSeg}), fast-forward stops at the seek point`,
    missingPast.length === 0 && presentFuture.length === 0,
    missingPast.length ? `missing past lines: ${missingPast.slice(0, 3).join(', ')}`
      : presentFuture.length ? `future lines present: ${presentFuture.slice(0, 3).join(', ')}`
      : `${nAfter} lines present`);
  check('after seek, transcript panel jumps to the seek segment', panelActive() === seekSeg,
    `panel=${panelActive()} seekSeg=${seekSeg}`);

  // --- drive to the end ---
  while (t < sync.duration + 0.2) {
    t += DT;
    if (!audio.paused) { audio.currentTime = t; audio.fire('timeupdate'); }
    await sleep(STEP_SLEEP);
  }
  audio.currentTime = sync.duration + 0.2; audio.fire('ended');
  await sleep(100);
  check('audio end clears narration state + highlight + transcript panel',
    isNarrOn() === false && highlightedIdx().length === 0 && panelActive() === -1,
    `narrOn=${isNarrOn()} highlighted=${highlightedIdx().length} panel=${panelActive()}`);

  // --- pause / resume lockstep ---
  getNarrBtn().onclick(); // start again
  await sleep(50);
  for (let k = 0; k < 20; k++) { audio.currentTime = (k + 1) * 0.25; audio.fire('timeupdate'); await sleep(40); }
  getNarrBtn().onclick(); // pause
  await sleep(50);
  check('pause button pauses the audio', audio.paused === true, `paused=${audio.paused}`);
  const frozenAt = panelActive();
  await sleep(300);
  check('transcript highlight freezes while paused', panelActive() === frozenAt && frozenAt >= 0,
    `panel=${panelActive()} was=${frozenAt}`);
  getNarrBtn().onclick(); // resume
  await sleep(50);
  check('resume button resumes the audio', audio.paused === false, `paused=${audio.paused}`);
  audio.pause();

  console.log(failures === 0 ? '\nALL NARRATION CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
  process.exit(failures === 0 ? 0 : 1);
})();
