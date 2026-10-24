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

// lazy (for long chapters of heavy sets): no page is built until a moment that shows it is prepared
// (window.prepareFrame(t), which the filming tool calls before every frame), so a short piece of film loads only
// the one or two pages it shows, not all of them (log 34: one painted set takes 20 to 30 seconds and over 2 GB to
// load). Each page file must then export its join (export const join = {...}) rather than return it from build(),
// because the joins decide which page shows when, before any page is built.
export async function buildCinemaChapter({ timelineUrl, piecesFolder, reliefFolder, pageFiles, pageNumbers, lazy = false }) {
  await loadFonts();
  const timeline = await (await fetch(timelineUrl)).json();
  let pieceInfo = {};
  try { pieceInfo = await (await fetch(`${piecesFolder}/pieces.json`)).json(); } catch { /* a chapter may have no cut pieces yet */ }
  // pageNumbers (optional): which timeline page each file is, for testing a few pages on their own
  const kits = pageFiles.map((_, i) => new CinemaKit({ number: pageNumbers?.[i] ?? i + 1, timeline, piecesFolder, pieceInfo, reliefFolder }));
  const pages = pageFiles.map(() => null);
  const building = new Map();
  const buildPage = (i) => {
    if (!building.has(i)) building.set(i, pageFiles[i].build(kits[i]).then((page) => { pages[i] = page; return page; }));
    return building.get(i);
  };
  if (!lazy) for (let i = 0; i < pageFiles.length; i++) await buildPage(i);   // one after another, as always

  // when each page hands over to the next
  const joins = pageFiles.map((file, i) => {
    const join = { ...DEFAULT_JOIN, ...(lazy ? file.join ?? {} : pages[i].join ?? file.join ?? {}) };
    const start = kits[i].lastWordEnd + join.after;
    return { ...join, start, end: start + join.length };
  });
  // the pages showing at moment t: one, or two during a join
  const pagesAt = (t) => {
    let i = 0;
    while (i < pageFiles.length - 1 && t >= joins[i].end) i++;
    return i < pageFiles.length - 1 && t >= joins[i].start ? [i, i + 1] : [i];
  };
  async function prepare(t) {
    for (const i of pagesAt(t)) if (!pages[i]) await buildPage(i);
  }
  const ready = (i) => {
    if (!pages[i]) throw new Error(`page ${kits[i].number} is not built yet: call prepare(t) (window.prepareFrame) before drawing it`);
    return pages[i];
  };
  const end = timeline.chapter_seconds;
  const pageEdges = joins.slice(0, -1).map((j) => j.end);

  const showPage = (i, t, target) => {
    const kit = kits[i];
    kit.t = t;
    const state = ready(i).pose(t) ?? {};
    const focusDistance = state.camera ? kit.aim(state.camera, t) : 10;
    // a held shot (the page returns still: true, or a value that changes when its set changes): its set is drawn
    // once and only its moving things each frame (cinema-stage.js); the camera's place is part of the key, so the
    // set is drawn again whenever the camera moves
    let still = null;
    if (state.still) {
      const c = kit.camera, r = (x) => x.toFixed(5);
      still = [i, state.still === true ? '' : state.still, ...c.position.toArray().map(r), ...c.quaternion.toArray().map(r), r(c.fov)].join('|');
    }
    drawPage({
      scene: kit.scene, camera: kit.camera, focusDistance, look: state.look, time: t, still,
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

  // Where the camera is at moment t, without drawing (for the camera check): the page showing (the
  // outgoing one during a join), its camera position, aim and lens, and the page's still-shot plans.
  function cameraAt(t) {
    let i = 0;
    while (i < pages.length - 1 && t >= joins[i].end) i++;
    const kit = kits[i];
    kit.t = t;
    kit.shotShowing = null;
    const camera = (ready(i).pose(t) ?? {}).camera;
    if (!camera) return { page: kit.number, t };
    return { page: kit.number, t, shot: kit.shotShowing, position: camera.position.toArray(), target: camera.target.toArray(), fov: camera.fov, focus: camera.focus };
  }
  const cameraPlans = () => kits.map((kit) => ({ page: kit.number, plans: kit.cameraPlans }));

  return { start: 0, end, pageEdges, renderFrame, cameraAt, cameraPlans, kits, pages, joins, prepare, pagesAt, lazy };
}
