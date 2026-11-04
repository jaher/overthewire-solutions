// Headless check of the site player: run index.html's script against a tiny
// DOM stub and report the order of lines it renders for one level.
// Usage: node player_check.js GAME LVL
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');

function El(tag) {
  this.tag = tag; this.children = []; this.style = {}; this.className = '';
  this._text = ''; this._q = {}; this.parent = null;
  this.scrollTop = 0; this.scrollHeight = 0; this.value = ''; this.innerHTML = '';
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
// the player sets row text through innerHTML; keep it visible to textContent
// for rows that are not split into prompt/cmd spans
El.prototype.querySelector = function (sel) {
  if (!this._q[sel]) { const e = new El('span'); e.parent = this; this._q[sel] = e; }
  return this._q[sel];
};
El.prototype.remove = function () {
  if (this.parent) this.parent.children = this.parent.children.filter(x => x !== this);
};

const byId = {};
const document = {
  getElementById(id) { if (!byId[id]) { byId[id] = new El('div'); if (id === 'term') byId[id].__term = true; } return byId[id]; },
  createElement(tag) { return new El(tag); },
  title: '',
};
const window = {};
global.document = document;
global.window = window;

// The real script uses setInterval for its delay()/sleep(); tick 50x faster.
const realSetInterval = setInterval;
global.setInterval = (fn, ms) => realSetInterval(fn, 1);

const realFetch = (url) => {
  const p = path.join(ROOT, url.replace(/^\.?\//, ''));
  return Promise.resolve({ json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) });
};
global.fetch = realFetch;

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error('no script found'); process.exit(1); }
// expose the script's top-level bindings (const/let stay inside the eval)
const api = new Function(m[1] + "\n;return { GAMES, playLevel, fillLevels, setGame: g => { gameKey = g; }, getCur: () => cur, getRun: () => runId };")();
const GAMES = api.GAMES, playLevel = api.playLevel, fillLevels = api.fillLevels, setGame = api.setGame, getCur = api.getCur, getRun = api.getRun;
const DEBUG = process.env.DEBUG_PLAYER === "1";

// The player memoises the terminal rows it draws; record every new row so the
// check can print the exact order even after the terminal is cleared for the
// next level.


const game = process.argv[2] || 'narnia';
const lvl = parseInt(process.argv[3] || '2', 10);
byId['speed'].value = '0.15';

// every row the player draws, in order, with the level it belongs to
const LOG = [];
const _appendChild = El.prototype.appendChild;
El.prototype.appendChild = function (c) {
  if (this.__term) LOG.push(c);
  return _appendChild.call(this, c);
};

function rendered(rows) {
  return (rows || LOG).map(c => {
    if (c.className === '') return { kind: 'cmd', text: (c._q['.prompt'] ? c._q['.prompt'].textContent : '') + (c._q['.cmd'] ? c._q['.cmd'].textContent : '') };
    return { kind: c.className, text: c.textContent || c.innerHTML || '' };
  });
}
if (process.env.DEBUG_PLAYER) {
  const _lvl = parseInt(process.argv[3]||'0',10);
}

(async () => {
  // wait for the manifest-driven games to load
  for (let i = 0; i < 200 && !GAMES[game]; i++) await new Promise(r => setTimeout(r, 20));
  if (!GAMES[game]) { console.error('game not loaded:', game); process.exit(1); }
  if (process.env.DEBUG_PLAYER) {
    const L0 = GAMES[game].levels.find(x => x.lvl === lvl);
    console.error('DEBUG level keys:', Object.keys(L0).join(','), 'step1 text:', JSON.stringify(L0.steps && L0.steps[1].text));
  }
  // let the manifest's own auto-play settle first, so its runId bump does not
  // cancel the level we are about to play
  await new Promise(r => setTimeout(r, 300));
  window.__userPickedGame = true;
  setGame(game); byId["gameSel"].value = game;
  fillLevels();
  const idx = GAMES[game].levels.findIndex(x => x.lvl === lvl);
  // terminal rows are an internal binding of the player script; the
  // harness only gets the exported functions, so count rows via document
  playLevel(idx);
  await new Promise(r => setImmediate(r));
  const runFor = getRun();
  // stop as soon as the password line of this level is rendered
  // the player auto-advances to the next level, so keep the fullest snapshot
  // taken while this level was on screen
  // the player auto-advances to the next level, so watch the terminal until
  // the password line of this level has been printed, then snapshot
  // runLevel stops typing when the level advances, so start counting from
  // this level's goal row in LOG; end when the run for THIS level is over
  // (runId moved on) and the level advanced
  let snap = null, idle = 0, lastLen = 0;
  const termEl = byId['term'];
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    const all = LOG.map(c => ({ kind: c.className || 'cmd', text: c.textContent || c.innerHTML || '' }));
    const gi = all.map(r => r.text).findIndex(t => t.startsWith(GAMES[game].title.toUpperCase() + ' LEVEL ' + lvl + ' '));
    if (gi >= 0) {
      snap = all.slice(gi);
      // the level's ending note (if any) is the last row it draws; the
      // trailing blank line is drawn after it
      if (snap.some(r => r.text === 'The password is <span class="pw">' + GAMES[game].levels[idx].pw + '</span>') &&
          LOG.length > 0 && all.length >= 2 && all[all.length - 1].text === '' && all[all.length - 2].text !== '') break;
    }
    // idle = drawn rows unchanged; when the level moved on and drawing has
    // stalled, the run of this level is over
    idle = (termEl.children.length === lastLen) ? idle + 1 : 0;
    lastLen = termEl.children.length;
    if (getCur() !== idx && idle > 2) break;
    await new Promise(r => setTimeout(r, 0));
  }
  const rows = snap || rendered();
  const start = 0;
  for (const r of rows.slice(start)) {
    const t = r.text.length > 100 ? r.text.slice(0, 97) + '...' : r.text;
    console.log(r.kind.padEnd(5) + ' | ' + t.replace(/\n/g, '\\n'));
  }
  process.exit(0);
})();
