// What this does: turns a list of cinema page files into one continuous film on the narration
// timeline. Each page is its own small 3D world with its own camera; this file decides which page is
// showing at any moment, and joins each page to the next a moment after its last word: the old page
// peels away like a book page (the series' signature), or the two pictures dissolve.
//
// How it fits: a chapter scene (for example inflation-chapter-2.js) calls buildCinemaChapter() with
// its pages. Each page file exports build(kit) and returns { pose(t), draw2D(context, t), join }.
// pose(t) returns { camera: <state from kit.shot>, look: { exposure, aperture, ... } }. join (optional)
// says how this page leaves: { kind: 'peel' | 'dissolve' | 'dip', after: seconds after the last word,
// length: seconds }. The filming tool asks renderFrame(t) for every frame and gets one finished JPEG.

import { drawPage, drawJoin, pageTargets, grabFrame } from '../stage/cinema-stage.js';
import { CinemaKit, loadFonts } from './cinema-kit.js';

const DEFAULT_JOIN = { kind: 'peel', after: 0.3, length: 0.85 };

export async function buildCinemaChapter({ timelineUrl, piecesFolder, reliefFolder, pageFiles, pageNumbers }) {
  await loadFonts();
  const timeline = await (await fetch(timelineUrl)).json();
  let pieceInfo = {};
  try { pieceInfo = await (await fetch(`${piecesFolder}/pieces.json`)).json(); } catch { /* a chapter may have no cut pieces yet */ }
  // pageNumbers (optional): which timeline page each file is, for testing a few pages on their own
  const kits = pageFiles.map((_, i) => new CinemaKit({ number: pageNumbers?.[i] ?? i + 1, timeline, piecesFolder, pieceInfo, reliefFolder }));
  const pages = [];
  for (const [i, file] of pageFiles.entries()) pages.push(await file.build(kits[i]));

  // when each page hands over to the next
  const joins = pages.map((page, i) => {
    const join = { ...DEFAULT_JOIN, ...(page.join ?? {}) };
    const start = kits[i].lastWordEnd + join.after;
    return { ...join, start, end: start + join.length };
  });
  const end = timeline.chapter_seconds;
  const pageEdges = joins.slice(0, -1).map((j) => j.end);

  const showPage = (i, t, target) => {
    const kit = kits[i];
    kit.t = t;
    const state = pages[i].pose(t) ?? {};
    const focusDistance = state.camera ? kit.aim(state.camera, t) : 10;
    drawPage({
      scene: kit.scene, camera: kit.camera, focusDistance, look: state.look, time: t,
      drawOverlay: pages[i].draw2D ? (context) => pages[i].draw2D(context, t, kit) : null,
    }, target);
  };

  function renderFrame(t) {
    // the page showing: the first whose join has not finished
    let i = 0;
    while (i < pages.length - 1 && t >= joins[i].end) i++;
    const join = joins[i];
    if (i < pages.length - 1 && t >= join.start) {
      showPage(i, t, pageTargets[0]);
      showPage(i + 1, t, pageTargets[1]);
      drawJoin(join.kind, (t - join.start) / join.length, pageTargets[0], pageTargets[1]);
    } else {
      showPage(i, t, null);
    }
    return grabFrame();
  }

  return { start: 0, end, pageEdges, renderFrame, kits, pages, joins };
}
