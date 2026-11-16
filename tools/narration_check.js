// Headless check of the narration player: run index.html's script against a
// tiny DOM stub (same stub as player_check.js, plus a drivable fake audio
// element) and verify that, for Vortex L0, the typed lines appear in time
// with the narration audio and the highlight tracks the spoken segment —
// through the first minute and across a seek — and that the visible
// transcript panel renders all 17 segments, tracks the audio clock, jumps
// on seek, freezes on pause, and clears at the end.
// Usage: node narration_check.js
// Exit 0 when every assertion passes, 1 otherwise.
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

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
const api = new Function(m[1] + "\n;return { GAMES, playLevel, fillLevels, setGame: g => { gameKey = g; }, getCur: () => cur, getRun: () => runId, getNarrMap: () => narrMap, isNarrOn: () => narrOn, getNarrBtn: () => narrBtn, getNarrSeek: () => narrSeek, getNarrAudio: () => narrAudio };")();
const { GAMES, playLevel, fillLevels, setGame, getNarrMap, isNarrOn, getNarrBtn, getNarrSeek, getNarrAudio } = api;

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let failures = 0;
function check(name, ok, detail) {
  console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (detail !== undefined ? '  — ' + detail : ''));
  if (!ok) failures++;
}

// Per-line scheduled times, recomputed from the sync map with the same rule
// the page uses (segment start + j/refs * segment length).
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

(async () => {
  const sync = JSON.parse(fs.readFileSync(path.join(ROOT, 'narration/vortex/L0.sync.json'), 'utf8'));
  const sched = lineTimes(sync);
  check('sync map: 17 segments, continuous 0 -> 74.98',
    sync.segments.length === 17 && Math.abs(sync.duration - 74.98) < 0.01,
    `segments=${sync.segments.length} duration=${sync.duration}`);
  const mp3 = path.join(ROOT, 'narration/vortex/L0.mp3');
  check('mp3 exists next to the script', fs.existsSync(mp3), fs.existsSync(mp3) ? (fs.statSync(mp3).size + ' bytes') : 'missing');

  for (let i = 0; i < 200 && !GAMES.vortex; i++) await sleep(20);
  if (!GAMES.vortex) { console.error('vortex not loaded'); process.exit(1); }
  await sleep(300);
  window.__userPickedGame = true;
  setGame('vortex'); byId['gameSel'].value = 'vortex';
  fillLevels();
  const idx = GAMES.vortex.levels.findIndex(x => x.lvl === 0);
  byId['speed'].value = '0.15';
  playLevel(idx);
  // wait for the sync map to load (Narrate button appears)
  for (let i = 0; i < 100 && !getNarrMap(); i++) await sleep(20);
  check('sync map loads for Vortex L0; Narrate button shown',
    !!getNarrMap() && getNarrBtn().style.display !== 'none',
    getNarrMap() ? `duration ${getNarrMap().duration}s` : 'no map');

  const transcript = byId['narrTranscript'];
  const panelActive = () => {
    let a = -1;
    for (const d of transcript.children) if (d.classList.contains('active')) a = parseInt(d.dataset.seg, 10);
    return a;
  };
  check('transcript panel renders all 17 segments with the script text',
    transcript.children.length === 17 &&
    transcript.children.every((d, i) => d.textContent === sync.segments[i].text) &&
    transcript.classList.contains('on'),
    `segments=${transcript.children.length} shown=${transcript.classList.contains('on')}`);

  const audio = getNarrAudio();
  audio.duration = sync.duration;
  audio.fire('loadedmetadata');
  const term = byId['term'];

  // --- start narration ---
  getNarrBtn().onclick();
  await sleep(50);
  check('narration is on after pressing Narrate', isNarrOn() === true);

  const outRows = () => term.children.filter(c => c.className === 'out' || c.className.startsWith('out '));
  const catOut = () => {
    // step 3 (cat -n) out lines: the 67-row block before the gcc cmd;
    // step 5 out lines: the 3-row block after the ./v0 cmd. Identify by
    // position: cat block = first 67 out rows, run block = next 3.
    const rows = outRows();
    return { cat: rows.slice(0, 67), run: rows.slice(67, 70) };
  };
  const highlighted = () => term.querySelectorAll('[data-narr-seg]')
    .filter(d => d.classList.contains('narr-hl'))
    .map(d => d.dataset.narrSeg);
  const hasVimBox = () => term.children.some(c => c.className === 'vimscreen' || (c.className || '').includes('vimscreen'));

  // --- drive the fake clock: 0.25s of audio per 40ms of real time ---
  const early = [], late = [];
  let sawVimAt10 = null, hlAtSeg5 = null, hlAtSeg12 = null, hlAtSeg15 = null;
  let panelAt10 = null, panelAtSeg5 = null, panelAtSeg12 = null;
  let t = 0;
  const DT = 0.25;
  while (t < 62) {
    t += DT;
    if (!audio.paused) { audio.currentTime = t; audio.fire('timeupdate'); }
    await sleep(100);
    const now = audio.currentTime;
    // (a) no out line may appear before its scheduled time (0.6s tolerance)
    const { cat, run } = catOut();
    cat.forEach((d, i) => {
      const e = sched.get('3:out:' + i);
      if (e && e.t > now + 0.6) early.push(`cat out[${i}] at ${now.toFixed(2)} (scheduled ${e.t.toFixed(2)})`);
    });
    run.forEach((d, i) => {
      const e = sched.get('5:out:' + i);
      if (e && e.t > now + 0.6) early.push(`run out[${i}] at ${now.toFixed(2)} (scheduled ${e.t.toFixed(2)})`);
    });
    // (b) every out line scheduled <= now - 1.5 must exist by now
    for (let i = 0; i < 67; i++) {
      const e = sched.get('3:out:' + i);
      if (e && e.t <= now - 1.5 && !cat[i]) late.push(`cat out[${i}] missing at ${now.toFixed(2)} (scheduled ${e.t.toFixed(2)})`);
    }
    for (let i = 0; i < 3; i++) {
      const e = sched.get('5:out:' + i);
      if (e && e.t <= now - 1.5 && !run[i]) late.push(`run out[${i}] missing at ${now.toFixed(2)} (scheduled ${e.t.toFixed(2)})`);
    }
    if (Math.abs(now - 10) < DT / 2) sawVimAt10 = hasVimBox();
    if (Math.abs(now - 10) < DT / 2 && panelAt10 === null) panelAt10 = panelActive();
    // seg 5's six lines are spread across [29.42, 31.30]; sample near its end
    // so all six have appeared and are highlighted together
    if (now >= 31.1 && now < 31.3 && hlAtSeg5 === null) hlAtSeg5 = highlighted();
    if (now >= 31.1 && now < 31.3 && panelAtSeg5 === null) panelAtSeg5 = panelActive();
    if (now >= 46 && now < 46.5 && hlAtSeg12 === null) hlAtSeg12 = highlighted();
    if (now >= 46 && now < 46.5 && panelAtSeg12 === null) panelAtSeg12 = panelActive();
    if (now >= 62.5 && hlAtSeg15 === null) hlAtSeg15 = highlighted();
  }
  check('no typed line appears before its spoken time', early.length === 0,
    early.length ? early.slice(0, 3).join(' | ') : '0 early lines');
  check('no typed line lags its spoken time by >1.5s', late.length === 0,
    late.length ? late.slice(0, 3).join(' | ') : '0 late lines');
  check('at t=10s (still in the goal preamble) the vim session has not started', sawVimAt10 === false,
    sawVimAt10 === null ? 'no sample at t=10' : (sawVimAt10 ? 'vim box already present' : 'no vim box yet'));
  check('seg 5 ("create a TCP socket") highlights exactly out lines 17-22',
    hlAtSeg5 !== null && hlAtSeg5.length === 6 && hlAtSeg5.every(s => s.split(' ').includes('5')),
    hlAtSeg5 === null ? 'no sample' : `highlighted segs: [${hlAtSeg5.join(', ')}]`);
  check('seg 12 (inet_pton story) highlights exactly out lines 23-28, no new lines',
    hlAtSeg12 !== null && hlAtSeg12.length === 6 && hlAtSeg12.every(s => s.split(' ').includes('12')),
    hlAtSeg12 === null ? 'no sample' : `highlighted segs: [${hlAtSeg12.join(', ')}]`);
  check('transcript panel active segment tracks the audio clock (seg 1 at t=10, seg 5 at t=31, seg 12 at t=46)',
    panelAt10 === 1 && panelAtSeg5 === 5 && panelAtSeg12 === 12,
    `t10=${panelAt10} t31=${panelAtSeg5} t46=${panelAtSeg12}`);
  // --- seek to 60s (seg 14: the reply-buffer story) and re-render fast-forwarded ---
  // Only lines scheduled <= 60s may appear: all 67 cat lines, but NOT the
  // gcc/run lines (scheduled 65.1s+) — the seek fast-forwards up to the seek
  // point, never past it.
  audio.currentTime = 60; audio.fire('seeked');
  getNarrSeek().value = '60';
  getNarrSeek().fire('input');
  getNarrSeek().fire('change');
  await sleep(1500);
  const afterSeek = catOut();
  check('after seek to 60s, all 67 cat lines present, run lines not yet (fast-forward stops at seek point)',
    afterSeek.cat.length === 67 && afterSeek.run.length === 0,
    `cat=${afterSeek.cat.length} run=${afterSeek.run.length}`);
  check('after seek to 60s, transcript panel jumps to segment 14', panelActive() === 14,
    `panel=${panelActive()}`);
  // resume the clock from 60 to past the end
  while (t < 75.2) {
    t += DT;
    if (!audio.paused) { audio.currentTime = t; audio.fire('timeupdate'); }
    await sleep(100);
    if (t >= 67 && t < 67.25 && hlAtSeg15 === null) hlAtSeg15 = highlighted();
  }
  check('seg 15 highlights the gcc/run lines', hlAtSeg15 !== null && hlAtSeg15.length >= 2 && hlAtSeg15.every(s => s.split(' ').includes('15')),
    hlAtSeg15 === null ? 'no sample' : `highlighted segs: [${hlAtSeg15.join(', ')}]`);
  const atEnd = catOut();
  const pwShown = term.children.some(c => (c.textContent || '').includes('The password is'));
  check('by the end (t=75s) the 3 run lines and the password line are shown',
    atEnd.run.length === 3 && pwShown, `run=${atEnd.run.length} pw=${pwShown}`);
  audio.currentTime = 75.2; audio.fire('ended');
  await sleep(100);
  check('audio end clears narration state + highlight + transcript panel', isNarrOn() === false && highlighted().length === 0 && panelActive() === -1,
    `narrOn=${isNarrOn()} highlighted=${highlighted().length} panel=${panelActive()}`);

  // --- pause / resume lockstep ---
  getNarrBtn().onclick(); // start again
  await sleep(50);
  // drive a few seconds so a segment is active, then pause
  for (let k = 0; k < 20; k++){ audio.currentTime = (k + 1) * 0.25; audio.fire('timeupdate'); await sleep(40); }
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
