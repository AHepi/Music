// What this does: chapter 1 ("Where austerity came from") as one continuous paper film, 3 minutes
// 41 seconds, on Malina's narration. Source: Clara E. Mattei, The Capital Order (2022).
//
// How the pieces fit:
//   - Every page of the chapter is a file in scenes/chapter-1/ (page-1.js ... page-10.js). Each
//     names the painted sheets it needs (most need one; pages 3 and 8 need two) and says, in
//     Malina's words, when each of its pieces moves.
//   - This file stacks all the sheets like the pages of a book, top page first, each a little
//     behind the one before. A page's pieces fold down flat and its sheet peels away from the
//     bottom-right corner 0.3 seconds after its last word, uncovering the next sheet. Only the
//     sheet on top and the one being uncovered are drawn.
//   - It also moves the camera: a slow push in on each sheet, a slight drift from side to side,
//     an easing back as a page turns, and a shake whenever something heavy lands.

import { Page, placeCamera, makePlainTexture, loadTexture } from '../stage/paper-stage.js';
import { PageKit, clamp01, easeInOut } from './paper-kit.js';
import * as page1 from './chapter-1/page-1.js';
import * as page2 from './chapter-1/page-2.js';
import * as page3 from './chapter-1/page-3.js';
import * as page4 from './chapter-1/page-4.js';
import * as page5 from './chapter-1/page-5.js';
import * as page6 from './chapter-1/page-6.js';
import * as page7 from './chapter-1/page-7.js';
import * as page8 from './chapter-1/page-8.js';
import * as page9 from './chapter-1/page-9.js';
import * as page10 from './chapter-1/page-10.js';

const PIECES = '/paper-film/pieces/chapter-1';
const PAGE_FILES = [page1, page2, page3, page4, page5, page6, page7, page8, page9, page10];
const SHEET_GAP = 0.06;               // how far each sheet lies behind the one above it
const TURN_AFTER_LAST_WORD = 0.30;    // seconds after a page's last word before its sheet peels
const TURN_LENGTH = 0.8;              // seconds a page turn takes
const CAMERA_FAR = 26.2, CAMERA_NEAR = 25.4;

export async function build() {
  const timeline = await (await fetch('/narration/chapter-1-timeline-steady-accent.json')).json();
  const pieceInfo = await (await fetch(`${PIECES}/pieces.json`)).json();
  const shakes = [];

  // ------------------------------------------------------------------ the sheets, top first
  const allSheets = [];
  const kits = [];
  for (const [index, pageFile] of PAGE_FILES.entries()) {
    const sheets = [];
    for (const name of pageFile.SHEETS) {
      const texture = name === 'blank' ? makePlainTexture('#1e282e') : await loadTexture(`${PIECES}/${pieceInfo[name].file}`);
      const sheet = new Page(texture, { z: -SHEET_GAP * allSheets.length });
      sheet.setVisible(false);
      sheets.push(sheet);
      allSheets.push(sheet);
    }
    kits.push(new PageKit({ number: index + 1, timeline, sheets, piecesFolder: PIECES, pieceInfo, shakes }));
  }

  // ------------------------------------------------------- every page makes its pieces
  const pages = [];
  for (const [index, pageFile] of PAGE_FILES.entries()) pages.push(await pageFile.build(kits[index]));

  // ------------------------------------------------------------- when each sheet turns
  // A page may set its own turns (a turn inside the page, or a special last turn); otherwise its
  // last sheet turns a moment after its last word.
  const turns = new Map();
  for (const [index, page] of pages.entries()) {
    const kit = kits[index];
    for (const turn of page.turns ?? []) turns.set(turn.sheet, { ...turn });
    const last = kit.sheets[kit.sheets.length - 1];
    if (!turns.has(last)) turns.set(last, { sheet: last, from: kit.lastWordEnd + TURN_AFTER_LAST_WORD, length: TURN_LENGTH });
  }
  for (const [index, kit] of kits.entries()) {
    for (const sheet of kit.sheets) {
      const turn = turns.get(sheet);
      if (!turn) throw new Error(`page ${index + 1}: a sheet has no turn`);
      turn.foldAwayAt ??= turn.from - 0.26;
      turn.doneAt ??= turn.from + turn.length;
      kit.setFoldAway(sheet, turn.foldAwayAt);
    }
  }
  const turnOf = (sheet) => turns.get(sheet);
  // a sheet is uncovered when the one above it starts to turn
  const uncoveredAt = allSheets.map((sheet, i) => (i === 0 ? -Infinity : turnOf(allSheets[i - 1]).from));
  const settledAt = allSheets.map((sheet, i) => (i === 0 ? 0 : turnOf(allSheets[i - 1]).doneAt));

  // each page is posed only around its own stretch of time
  const pageWindows = kits.map((kit) => {
    const first = allSheets.indexOf(kit.sheets[0]);
    return { from: uncoveredAt[first] - 0.1, to: turnOf(kit.sheets[kit.sheets.length - 1]).doneAt };
  });

  const start = 0;
  const end = timeline.chapter_seconds;

  function placeTheCamera(t) {
    // which sheet is on top, and how far through its time we are
    let current = 0;
    while (current + 1 < allSheets.length && t >= settledAt[current + 1]) current++;
    const turn = turnOf(allSheets[current]);
    let z;
    if (t < turn.from) {
      const span = Math.max(1, turn.from - settledAt[current]);
      z = CAMERA_FAR - (CAMERA_FAR - CAMERA_NEAR) * clamp01((t - settledAt[current]) / span);
    } else {
      z = CAMERA_NEAR + (CAMERA_FAR - CAMERA_NEAR) * easeInOut(clamp01((t - turn.from) / (turn.doneAt - turn.from)));
    }
    if (!Number.isFinite(z)) z = CAMERA_FAR;
    // shakes from things landing
    let shake = 0, latestAge = 0;
    for (const s of shakes) {
      const age = t - s.time;
      if (age < 0 || age > 1.5) continue;
      shake += s.amount * Math.exp(-age / s.decay);
      latestAge = age;
    }
    const drift = 0.10 * Math.sin(2 * Math.PI * t / 19);
    placeCamera({
      x: drift + shake * Math.sin(2 * Math.PI * 17 * latestAge),
      y: 8.25 + shake * 0.7 * Math.sin(2 * Math.PI * 23 * latestAge + 1),
      z, lookX: drift * 0.6, lookY: 8.0,
    });
  }

  function pose(t) {
    for (let i = 0; i < allSheets.length; i++) {
      const sheet = allSheets[i];
      const turn = turnOf(sheet);
      const shown = t >= uncoveredAt[i] - 0.05 && t < turn.doneAt;
      sheet.setVisible(shown);
      if (shown) sheet.setTurn(turn.curve ? turn.curve(t) : clamp01((t - turn.from) / turn.length));
    }
    for (const [index, page] of pages.entries()) {
      const kit = kits[index];
      if (t < pageWindows[index].from || t > pageWindows[index].to) { kit.hideAll(); continue; }
      kit.t = t;
      page.pose(t);
    }
    placeTheCamera(t);
  }

  return { start, end, pose };
}
