// What this does: the shared toolkit for paper pages. It has two parts:
//   1. motions, as plain functions of time: fold up from flat (pop-up), fold down, drop in from
//      above and land, slide in, hop, knock (a jolt from an impact). Each returns a pose that a
//      piece can take: { visible, fold, dx, dy, roll, lift }.
//   2. the page kit, one per page of the chapter. It finds Malina's words on that page ("the second
//      'shells'"), makes the page's pieces (painted cut-outs, plain words, printed cards), and puts
//      every piece away tidily before its page turns: the pieces fold down flat one after another,
//      front first, so nothing is left standing on a page as it peels away.
//
// How it fits: the chapter scene (chapter-1.js) makes one kit per page and hands it to that page's
// file (chapter-1/page-N.js). The page file says when each piece moves, in words, and calls
// kit.place(piece, pose) for every piece on every frame.

import { Piece, makeWordTexture, makeCardTexture, loadTexture } from '../stage/paper-stage.js';

// ------------------------------------------------------------------------------------- motions
export const clamp01 = (v) => Math.min(1, Math.max(0, v));
export const degrees = (d) => d * Math.PI / 180;
export const easeInOut = (x) => (x < 0.5 ? 2 * x * x : 1 - (-2 * x + 2) ** 2 / 2);
export const easeIn = (x) => x * x;
export const easeOut = (x) => 1 - (1 - x) * (1 - x);

// A spring settling from 1 to 0 (time in seconds since it was let go): a little overshoot, no wobble.
export function spring(t, { stiffness = 16, damping = 0.72 } = {}) {
  if (t <= 0) return 1;
  if (damping >= 0.999) return Math.exp(-stiffness * t) * (1 + stiffness * t); // no overshoot at all
  const wd = stiffness * Math.sqrt(1 - damping * damping);
  return Math.exp(-damping * stiffness * t) * (Math.cos(wd * t) + (damping * stiffness / wd) * Math.sin(wd * t));
}

// Fold up from flat at `start`; never leans back far enough to touch the page behind.
export function popUp(t, start, piece, options) {
  if (t < start) return { visible: false };
  const maxLeanBack = Math.asin(Math.min(1, piece.restZ / piece.height)) * 0.7;
  return { visible: true, fold: Math.max(-maxLeanBack, (Math.PI / 2) * spring(t - start, options)) };
}

// Fold down to flat starting at `start`, speeding up like something falling; hidden once flat.
export function foldDown(t, start, duration = 0.22) {
  const x = clamp01((t - start) / duration);
  return x >= 1 ? { visible: false, fold: Math.PI / 2 } : { visible: true, fold: (Math.PI / 2) * x * x };
}

// Shown between `start` and `stop`: pops up at start, folds away at stop.
export function popUpUntil(t, start, stop, piece, options) {
  return t < stop ? popUp(t, start, piece, options) : foldDown(t, stop, 0.2);
}

// Adds a tilt toward the camera (a jolt, a lean) to a pose that is showing.
export const addFold = (pose, extra) => (pose.visible === false ? pose : { ...pose, fold: (pose.fold ?? 0) + extra });

// Slapped flat: folds down very fast with a small bounce, and stays lying flat.
export function slapFlat(t, start, duration = 0.14) {
  const x = clamp01((t - start) / duration);
  const after = t - start - duration;
  const settle = after > 0 ? 0.06 * Math.exp(-after / 0.08) * Math.abs(Math.sin(2 * Math.PI * 5 * after)) : 0;
  return { visible: true, fold: (Math.PI / 2) * x * x - settle };
}

// A knock: a decaying shake, for things jolted by an impact (age = seconds since the impact).
export const knock = (age, amount, rate = 3.2, decay = 0.25) => (age < 0 ? 0 : amount * Math.exp(-age / decay) * Math.sin(2 * Math.PI * rate * age));

// A small jump: up and down a couple of times, fading (dy in world units).
export const hop = (t, at, height = 0.22, decay = 0.13) => {
  const age = t - at;
  return age < 0 || age > 1 ? 0 : height * Math.exp(-age / decay) * Math.abs(Math.sin(2 * Math.PI * 2.6 * age));
};

// Dropped in from above: falls, speeding up, and lands at `landAt` with a hard bounce.
export function dropIn(t, landAt, { fall = 0.32, height = 13, roll = 7, bounce = 0.3 } = {}) {
  const fallStart = landAt - fall;
  if (t < fallStart) return { visible: false };
  if (t < landAt) {
    const x = (t - fallStart) / fall;
    return { visible: true, dy: height * (1 - x * x), roll: degrees(roll) * (1 - x), fold: degrees(-2) };
  }
  const age = t - landAt;
  return { visible: true, dy: bounce * Math.exp(-age / 0.09) * Math.abs(Math.sin(Math.PI * age / 0.13)),
    roll: knock(age, degrees(roll * 0.5), 3, 0.22), fold: knock(age, degrees(5), 5, 0.2) };
}

// Slid in from the side (from = how far away it starts, in world units; minus is from the left).
export function slideIn(t, start, { from = -12, stiffness = 11, damping = 0.62, tilt = 3 } = {}) {
  if (t < start) return { visible: false };
  const age = t - start;
  const settle = clamp01(age / 0.5);
  return { visible: true, dx: from * spring(age, { stiffness, damping }), roll: degrees(tilt * Math.sign(from)) * Math.sin(Math.PI * settle) * (1 - settle) };
}

// Walking: a gentle bob while moving (paper figures bob, they do not stride).
export const walkBob = (t, from, to, height = 0.12, steps = 2.4) => (t < from || t > to ? 0 : height * Math.abs(Math.sin(Math.PI * steps * (t - from))));

// A side-to-side rock, growing then fading over [from, to] (roll in radians).
export const rock = (t, from, to, amount = degrees(4), rate = 2.2) => {
  if (t < from || t > to) return 0;
  const x = (t - from) / (to - from);
  return amount * Math.sin(Math.PI * x) * Math.sin(2 * Math.PI * rate * (t - from));
};

// ----------------------------------------------------------------------------------- the words
// Finds Malina's words on one page of the timeline. Words spoken twice are asked for by which time.
export function wordClock(timeline, pageNumber) {
  const page = timeline.pages.find((p) => p.page === pageNumber);
  const key = (w) => w.toLowerCase().replace(/[^a-z0-9']/g, '');
  const find = (word, n = 1) => {
    let seen = 0;
    for (const w of page.words) if (key(w.text) === key(word) && ++seen === n) return w;
    throw new Error(`page ${pageNumber}: no word "${word}" (occurrence ${n})`);
  };
  return { at: (word, n) => find(word, n).start, end: (word, n) => find(word, n).end, page };
}

// ------------------------------------------------------------------------------------ the kit
export class PageKit {
  constructor({ number, timeline, sheets, piecesFolder, pieceInfo, shakes }) {
    this.number = number;
    this.sheets = sheets;
    this.piecesFolder = piecesFolder;
    this.pieceInfo = pieceInfo;
    this.shakes = shakes;
    const clock = wordClock(timeline, number);
    this.at = clock.at;
    this.end = clock.end;
    this.firstWordAt = clock.page.first_word_at;
    this.lastWordEnd = clock.page.last_word_end_at;
    this.pieces = [];
    this.effects = [];             // dust and smoke, hidden with the pieces when the page is not showing
    this.foldAwayAt = new Map();   // sheet -> when its pieces start folding away
    this.foldOrder = null;
    this.t = 0;
  }

  // a painted cut-out from the chapter's pieces folder
  async piece(name, { sheet, ...options }) {
    const info = this.pieceInfo[name];
    if (!info) throw new Error(`no piece called ${name}`);
    const texture = await loadTexture(`${this.piecesFolder}/${info.file}`);
    return this.register(new Piece(texture, { page: sheet ?? this.sheets[0], ...options }));
  }

  // plain words, cut out of off-white card; size = letter size in world units (1 = the page-3 words)
  async word(lines, { sheet, size = 1.0, width, ...options }) {
    const texture = await makeWordTexture(lines);
    return this.register(new Piece(texture, { page: sheet ?? this.sheets[0], width: width ?? size * texture.image.width / 220, ...options }));
  }

  // a printed card, sign or poster (or, with no lines, a plain board)
  async card(lines, { sheet, look = {}, size, width, ...options }) {
    const texture = await makeCardTexture(lines, look);
    const fontPx = look.fontPx ?? 150;
    return this.register(new Piece(texture, { page: sheet ?? this.sheets[0], width: width ?? size * texture.image.width / fontPx, ...options }));
  }

  // a speaking figure: the face piece with a dark mouth behind and a jaw in front, all on one hinge
  async speaker(name, { sheet, jawDropShare, ...options }) {
    const face = await this.piece(`${name}-face`, { sheet, ...options });
    const mouth = await face.addLayer(`${this.piecesFolder}/${this.pieceInfo[`${name}-mouth`].file}`, -0.004);
    const jaw = await face.addLayer(`${this.piecesFolder}/${this.pieceInfo[`${name}-jaw`].file}`, 0.004);
    const dropMax = face.height * (jawDropShare ?? this.pieceInfo[`${name}-face`].jaw_drop_share);
    return { piece: face, setOpen: (open) => { jaw.position.y = -dropMax * open; mouth.visible = open > 0.001; } };
  }

  register(piece) { this.pieces.push(piece); return piece; }

  // dust or smoke that belongs to this page
  effect(effect) { this.effects.push(effect); return effect; }

  // a camera shake starting at `time` (amount in world units, fading over `decay` seconds)
  shake(time, amount, decay = 0.15) { this.shakes.push({ time, amount, decay }); }

  // set by the chapter once it knows when each sheet turns
  setFoldAway(sheet, time) { this.foldAwayAt.set(sheet, time); this.foldOrder = null; }

  foldAwayStart(piece) {
    if (!this.foldOrder) {
      // front pieces fold first; all are flat before the page starts to turn
      this.foldOrder = new Map();
      for (const sheet of this.sheets) {
        const onSheet = this.pieces.filter((p) => p.page === sheet).sort((a, b) => b.restZ - a.restZ);
        const gap = onSheet.length > 1 ? Math.min(0.05, 0.2 / (onSheet.length - 1)) : 0;
        onSheet.forEach((p, i) => this.foldOrder.set(p, i * gap));
      }
    }
    const sheetTime = this.foldAwayAt.get(piece.page);
    return sheetTime === undefined ? Infinity : sheetTime + this.foldOrder.get(piece);
  }

  // Puts a piece in its pose for this moment, folding it away if its page is about to turn.
  place(piece, pose) {
    if (!pose || pose.visible === false) { piece.set({ visible: false }); return; }
    const away = this.foldAwayStart(piece);
    if (this.t >= away) {
      const folding = foldDown(this.t, away, 0.2);
      if (!folding.visible) { piece.set({ visible: false }); return; }
      pose = { ...pose, fold: Math.max(pose.fold ?? 0, folding.fold) };
    }
    piece.set(pose);
  }

  hideAll() {
    for (const piece of this.pieces) piece.set({ visible: false });
    for (const effect of this.effects) effect.hide();
  }
}

// A mouth track (how open the jaw is on each frame, from Malina's loudness), as a function of time.
export async function loadMouthTrack(url) {
  const track = await (await fetch(url)).json();
  return (t) => {
    const i = Math.round((t - track.start) * track.frames_per_second);
    if (i < 0 || i >= track.open.length) return 0;
    return track.open[i];
  };
}
