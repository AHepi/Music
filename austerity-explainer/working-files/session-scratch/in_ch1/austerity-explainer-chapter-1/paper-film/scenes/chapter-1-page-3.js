// What this does: chapter 1, page 3 ("Britain after the war") as a paper pop-up test.
// Source: Clara E. Mattei, The Capital Order (2022); facts from research entries C1-08 to C1-11.
//
// What happens, tied to Malina's words (times come from the chapter timeline, so nothing is guessed):
//   Glasgow square page
//     "workers"            a crowd folds up from flat
//     "doubles"            a second, bigger crowd folds up in front: the crowd doubles
//     "eight million"      8 MILLION pops up in the sky
//     "sixty thousand"     8 MILLION folds away; 60,000 pops up
//     "demanding ... week" the crowd bobs, cheering
//     "troops"             a line of soldiers slides in behind the crowd
//     "tanks"              a First World War tank drops in from above and lands hard: the camera
//                          shakes, dust bursts out, the crowd jolts, 60,000 is knocked flat
//   the pieces fold down flat, then the page peels away from its bottom-right corner
//   Pithead page
//     "demand"             a miner folds up; his paper jaw moves with Malina's voice
//     "public ownership"   PUBLIC OWNERSHIP pops up
//     "royal commission"   the commission's report folds up beside him
//     "ignores it"         PUBLIC OWNERSHIP folds away, IGNORED pops up, the report is slapped flat

import { Page, Piece, DustBurst, makeWordTexture, placeCamera } from '../stage/paper-stage.js';

const PIECES = '/paper-film/pieces/page3';

// ------------------------------------------------------------------ motion, as plain functions
const clamp01 = (v) => Math.min(1, Math.max(0, v));
const degrees = (d) => d * Math.PI / 180;
// A spring settling from 1 to 0 (time in seconds since it was let go): a little overshoot, no wobble.
function spring(t, { stiffness = 16, damping = 0.72 } = {}) {
  if (t <= 0) return 1;
  const wd = stiffness * Math.sqrt(1 - damping * damping);
  return Math.exp(-damping * stiffness * t) * (Math.cos(wd * t) + (damping * stiffness / wd) * Math.sin(wd * t));
}
// Fold up from flat at `start`; never leans back far enough to touch the page behind.
function popUp(t, start, piece) {
  if (t < start) return { visible: false };
  const maxLeanBack = Math.asin(Math.min(1, piece.restZ / piece.height)) * 0.7;
  return { visible: true, fold: Math.max(-maxLeanBack, (Math.PI / 2) * spring(t - start)) };
}
// Fold down to flat starting at `start`, speeding up like something falling; hidden once flat.
function foldDown(t, start, duration = 0.22) {
  const x = clamp01((t - start) / duration);
  return x >= 1 ? { visible: false, fold: Math.PI / 2 } : { visible: true, fold: (Math.PI / 2) * x * x };
}
// A knock: a decaying shake, for things jolted by an impact.
const knock = (age, amount, rate = 3.2, decay = 0.25) => (age < 0 ? 0 : amount * Math.exp(-age / decay) * Math.sin(2 * Math.PI * rate * age));

function wordClock(timeline, pageNumber) {
  const page = timeline.pages.find((p) => p.page === pageNumber);
  const key = (w) => w.toLowerCase().replace(/[^a-z0-9']/g, '');
  const find = (word, n = 1) => {
    let seen = 0;
    for (const w of page.words) if (key(w.text) === key(word) && ++seen === n) return w;
    throw new Error(`page ${pageNumber}: no word "${word}" (occurrence ${n})`);
  };
  return { at: (word, n) => find(word, n).start, end: (word, n) => find(word, n).end, page };
}

export async function build() {
  const timeline = await (await fetch('/narration/chapter-1-timeline-steady-accent.json')).json();
  const mouthTrack = await (await fetch('/paper-film/scene-data/chapter-1-page-3-mouth.json')).json();
  const pieceInfo = await (await fetch(`${PIECES}/pieces.json`)).json();
  const words = wordClock(timeline, 3);
  const at = words.at;

  // ---------------------------------------------------------------------------- the pages
  // The pithead page waits underneath the Glasgow page and is revealed when Glasgow turns over.
  const pithead = await Page.create(`${PIECES}/pithead.jpg`, { z: -0.06 });
  const glasgow = await Page.create(`${PIECES}/glasgow-square.jpg`, { z: 0 });

  // ------------------------------------------------------------------- Glasgow page pieces
  const soldiers = await Piece.create(`${PIECES}/soldiers.png`, { page: glasgow, width: 8.4, x: -0.3, y: 5.0, z: 0.7 });
  const crowdBack = await Piece.create(`${PIECES}/crowd-back.png`, { page: glasgow, width: 10.8, x: 0, y: 1.6, z: 1.25 });
  const tank = await Piece.create(`${PIECES}/tank.png`, { page: glasgow, width: 7.2, x: 0.7, y: 3.5, z: 1.95 });
  const crowdFront = await Piece.create(`${PIECES}/crowd-front.png`, { page: glasgow, width: 11.2, x: 0, y: -1.4, z: 2.7 });
  const eightMillion = new Piece(await makeWordTexture(['8 MILLION']), { page: glasgow, width: 6.3, x: 0, y: 11.3, z: 0.55 });
  const sixtyThousand = new Piece(await makeWordTexture(['60,000']), { page: glasgow, width: 5.2, x: 0, y: 11.3, z: 0.55 });
  const dust = new DustBurst({ count: 28, seed: 11 });

  // ------------------------------------------------------------------- pithead page pieces
  const miner = await Piece.create(`${PIECES}/miner-face.png`, { page: pithead, width: 7.6, x: 0, y: -1.4, z: 1.6 });
  const mouth = await miner.addLayer(`${PIECES}/miner-mouth.png`, -0.004);
  const jaw = await miner.addLayer(`${PIECES}/miner-jaw.png`, 0.004);
  const jawDropMax = miner.height * 0.022;
  const report = await Piece.create(`${PIECES}/report.png`, { page: pithead, width: 3.1, x: -2.45, y: 0.3, z: 2.6, yaw: degrees(6) });
  const publicOwnership = new Piece(await makeWordTexture(['PUBLIC', 'OWNERSHIP']), { page: pithead, width: 6.1, x: 0, y: 10.8, z: 0.55 });
  const ignored = new Piece(await makeWordTexture(['IGNORED']), { page: pithead, width: 5.7, x: 0, y: 11.5, z: 0.55 });

  // ------------------------------------------------------------------------------- times
  const T = {
    crowdBack: at('workers') - 0.12,
    crowdFront: at('doubles') - 0.10,
    eightMillion: at('eight') - 0.08,
    eightMillionAway: at('sixty') - 0.24,
    sixtyThousand: at('sixty') - 0.04,
    cheerFrom: at('demanding') - 0.05, cheerTo: words.end('week') + 0.1,
    soldiers: at('troops') - 0.22,
    tankLands: at('tanks') + 0.02,
    tankFall: 0.36,
    glasgowFoldsAway: at('tanks') + 0.48,
    turnFrom: at('tanks') + 0.74, turnLength: 0.82,
    miner: at('demand') - 0.22,
    mouthFrom: at('demand') - 0.02, mouthTo: words.end('mines') + 0.05,
    publicOwnership: at('public') - 0.08,
    report: at('royal') - 0.10,
    publicOwnershipAway: at('ignores') - 0.16,
    ignored: at('ignores') - 0.03,
    reportSlapped: at('ignores') + 0.06,
  };
  const start = at('when') - 0.45;
  const end = timeline.pages.find((p) => p.page === 4).first_word_at - 0.22;

  const mouthOpen = (t) => {
    if (t < T.mouthFrom || t > T.mouthTo) return 0;
    const i = Math.round((t - mouthTrack.start) * mouthTrack.frames_per_second);
    return mouthTrack.open[Math.min(mouthTrack.open.length - 1, Math.max(0, i))] ?? 0;
  };

  function pose(t) {
    // the camera drifts in slowly; it shakes when the tank lands and, a little, when the report is slapped down
    const age = t - T.tankLands, slapAge = t - T.reportSlapped;
    const shake = (age >= 0 ? 0.13 * Math.exp(-age / 0.17) : 0) + (slapAge >= 0 ? 0.04 * Math.exp(-slapAge / 0.12) : 0);
    const shakeAge = age >= 0 && (slapAge < 0) ? age : Math.max(0, slapAge);
    const progress = (t - start) / (end - start);
    const drift = 0.10 * Math.sin(progress * Math.PI * 1.3);
    placeCamera({ x: drift + shake * Math.sin(2 * Math.PI * 17 * shakeAge), y: 8.25 + shake * 0.7 * Math.sin(2 * Math.PI * 23 * shakeAge + 1),
      z: 26.2 - 0.9 * progress, lookX: drift * 0.6, lookY: 8.0 });

    // ------------------------------------------------------------------- page turn
    const turn = clamp01((t - T.turnFrom) / T.turnLength);
    glasgow.setTurn(turn);
    glasgow.setVisible(turn < 1);
    // before the page turns, its pieces fold down flat one after another (front first) and are put away
    const foldOrder = [crowdFront, tank, sixtyThousand, crowdBack, soldiers];
    const onGlasgow = (p, piece) => {
      const order = foldOrder.indexOf(piece);
      const startFold = T.glasgowFoldsAway + 0.05 * Math.max(0, order);
      if (t < startFold || p.visible === false) return p;
      const away = foldDown(t, startFold, 0.2);
      return away.visible ? { ...p, fold: Math.max(p.fold ?? 0, away.fold) } : { visible: false };
    };

    // ------------------------------------------------------------------- Glasgow
    const cheering = t > T.cheerFrom && t < T.cheerTo;
    const cheerEnvelope = cheering ? Math.sin(Math.PI * clamp01((t - T.cheerFrom) / (T.cheerTo - T.cheerFrom))) ** 0.5 : 0;
    const bob = (phase) => 0.11 * cheerEnvelope * Math.max(0, Math.sin(2 * Math.PI * 2.3 * (t - T.cheerFrom) + phase));
    const jolt = (amount) => knock(age, degrees(amount));
    const jump = (amount) => (age < 0 ? 0 : amount * Math.exp(-age / 0.14) * Math.abs(Math.sin(2 * Math.PI * 4 * age)));

    const back = popUp(t, T.crowdBack, crowdBack);
    crowdBack.set(onGlasgow({ ...back, fold: (back.fold ?? 0) + jolt(7), dy: bob(0) + jump(0.16), roll: degrees(1.2) * cheerEnvelope * Math.sin(2 * Math.PI * 1.15 * (t - T.cheerFrom)) }, crowdBack));
    const front = popUp(t, T.crowdFront, crowdFront);
    crowdFront.set(onGlasgow({ ...front, fold: (front.fold ?? 0) + jolt(5), dy: bob(1.9) + jump(0.12), roll: degrees(-1.0) * cheerEnvelope * Math.sin(2 * Math.PI * 1.15 * (t - T.cheerFrom) + 1) }, crowdFront));

    if (t < T.soldiers) soldiers.set({ visible: false });
    else {
      const slide = spring(t - T.soldiers, { stiffness: 11, damping: 0.62 });
      soldiers.set(onGlasgow({ fold: jolt(4), dx: -12 * slide, roll: degrees(-3) * Math.sin(Math.PI * clamp01((t - T.soldiers) / 0.5)) * (1 - clamp01((t - T.soldiers) / 0.5)) }, soldiers));
    }

    const fallStart = T.tankLands - T.tankFall;
    if (t < fallStart) tank.set({ visible: false });
    else if (t < T.tankLands) {
      const x = (t - fallStart) / T.tankFall;
      tank.set(onGlasgow({ dy: 14 * (1 - x * x), roll: degrees(7) * (1 - x), fold: degrees(-2) }, tank));
    } else {
      const bounce = 0.32 * Math.exp(-age / 0.09) * Math.abs(Math.sin(Math.PI * age / 0.13));
      tank.set(onGlasgow({ dy: bounce, roll: knock(age, degrees(3.5), 3, 0.22), fold: knock(age, degrees(5), 5, 0.2) }, tank));
    }
    dust.set({ origin: { x: tank.restX, y: tank.restY + 0.5, z: tank.restZ + 0.15 }, width: tank.width * 0.85, age: t > T.glasgowFoldsAway ? 9 : age });

    if (t < T.eightMillionAway) eightMillion.set(popUp(t, T.eightMillion, eightMillion));
    else eightMillion.set(foldDown(t, T.eightMillionAway, 0.2));
    if (t < T.tankLands + 0.03) sixtyThousand.set(popUp(t, T.sixtyThousand, sixtyThousand));
    else sixtyThousand.set(foldDown(t, T.tankLands + 0.03, 0.16));

    // ------------------------------------------------------------------- pithead
    const minerPose = popUp(t, T.miner, miner);
    miner.set(minerPose);
    const open = mouthOpen(t);
    jaw.position.y = -jawDropMax * open;
    mouth.visible = open > 0.001;

    publicOwnership.set(t < T.publicOwnershipAway ? popUp(t, T.publicOwnership, publicOwnership) : foldDown(t, T.publicOwnershipAway, 0.2));
    ignored.set(popUp(t, T.ignored, ignored));
    if (t < T.reportSlapped) report.set(popUp(t, T.report, report));
    else {
      const x = clamp01((t - T.reportSlapped) / 0.14);
      const settle = x >= 1 ? 0.06 * Math.exp(-(t - T.reportSlapped - 0.14) / 0.08) * Math.abs(Math.sin(2 * Math.PI * 5 * (t - T.reportSlapped - 0.14))) : 0;
      report.set({ fold: Math.PI / 2 * x * x - settle, visible: true });
    }
  }

  return { start, end, pose };
}
