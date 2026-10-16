// What this does: page 3 of chapter 2 for newcomers, "The quiet factory" (about 47.7 to 75.1 s; plan 34, part 2,
// shots 3a and 3b in shots.json). Malina: "Picture two factories. Think of each one as a whole country... all its
// workers, materials and machines. In the first, the machines stand still. Workers wait at the gate, hoping for a
// job. Call it the quiet factory. Now the government spends new money on what the factory makes. The workers go in.
// The machines start. More money... and more things to buy. So prices barely move."
//   3a  W3, both gates from the upstairs window across the cross street, held: PICTURE TWO FACTORIES, EACH ONE = A
//       WHOLE COUNTRY (to the cut), and labels WORKERS (No. 1's waiting men: its line one hook, sideways from the men
//       past the brazier, down onto the empty lane and on to its words), MATERIALS (the crates at No. 2's gate, its words
//       lower on the lane) and MACHINES (over No. 2's own column, its line dropping straight to the flywheel in No. 2's
//       lit doorway), each label's words coming in with its line (MACHINES is up only about 0.9 s before the cut). The
//       labels are placed from where their things are on the frame, and a check in the stage's log says how far each
//       keeps clear of the others. Live: No. 2's smoke and window flicker, No. 1's brazier and lantern.
//   3b  W1, the shut No. 1 gate at the head of the queue. Cut in on "In"; one slide of 1.2 m along the queue toward
//       the gate, from "Workers" to "Call" (we join the line), never turning, stopping on the composed frame. THE
//       QUIET FACTORY; NEW MONEY SPENT with a small arrow to the chain between the gate leaves; on "go" a time cut: the gate open, the men
//       gone, the brazier still burning by the empty pier but lower (smaller flames, less glow: time has passed; the
//       people test, lesson 136), the lantern and lunch tin still there; on "start" No. 1's
//       windows light in three steps and its chimney starts to smoke; MORE MONEY, + MORE THINGS TO BUY as crates
//       stencilled THIS WAY UP pop up in the open gateway; → PRICES BARELY MOVE with a level price arrow across No. 1's
//       upper windows, under its gate board (at least 24 pixels clear of it, checked), with a dark edge so it shows on
//       the lit windows. No. 1's gate lamp glows low in W1, so the gate, not the lamp, is the brightest thing.
// A state changes only while the camera holds. The one Works set serves both views: at the cut the projector moves
// from W3's plate camera to W1's (works-effects.js, projected-set.js setView).
// ?go=swing (PAPER_FILM_QUERY=go=swing) shows the plan's fallback for "go": the gate swings open in 0.8 s and the men
// fade in 1.2 s inside the swing (a blend in six steps), instead of the time cut.
import { THREE } from '../cinema-kit.js';
import { buildWorks, steppedBlend, WORKS_IN_USE, FIRE_AFTER_A_WHILE } from './works-effects.js';
import { callout, buildWords, topShade, pointer, priceArrow, presence, gapToBox, pointsRound, reportGap, INK, TEXT_RIGHT } from '../graphics.js';

// How this page leaves: the series' page peel, 0.3 s after the last word.
export const join = { kind: 'peel', after: 0.3, length: 0.85 };

// The pictures shone onto the set. Until the paintings are approved, each view's PLATE stands in for its painting.
// When a painting is approved, put its file here; the state pictures are then made again from the paintings with
// paper-film/tools/make_state_picture.py (main painting, working painting, plate, helper plate).
export const PICTURES = {
  w3: 'works-w3-plate.jpg',                       // W3, both gates: No. 1 quiet, No. 2 flat out
  w1: 'works-w1-plate.jpg',                       // W1, quiet: the men waiting, windows dark
  'w1 men gone': 'works-w1-men-gone-state.png',   // state picture: the men gone (and No. 1's cart doors open), windows dark
  'w1 working': 'works-w1-working-state.png',     // state picture: the men gone and every window lit
  // the behind picture for the slide (what the men hide, for the ring round them that the stage gives to the behind
  // picture as soon as the camera moves): the main painting everywhere but inside the men's outlines, where it is
  // the helper plate drawn without them and with all else quiet (works-w1-behind-plate.jpg; make_state_picture.py
  // with the men's outlines). The working painting (the plan's first choice) and the "men gone" state picture both
  // show No. 1's doorway lit there, and the doorway came on behind the waiting men from "Workers" on (round 3 of
  // log 34). Once the paintings come: a painting of that helper plate, or, free, make_behind_picture.py on the main
  // painting (a plain fill inside the outlines).
  'w1 behind': 'works-w1-behind.png',
};
const GO = new URLSearchParams(location.search).get('go') ?? 'cut';
// fringe: the lens's colour fringe kept small (the stage's 0.006 showed rainbow edges on the lane's gutter in W1 and
// W2; round 5's critique, finding 12)
const LOOK = { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fringe: 0.002 };
// W1 (3b) a little brighter, the whole shot alike (it changes only at the cut): W1's plate is the darkest of the Works
// (a frame's average 35 levels, against 49 for W2 and 59 for W3), and the stage's filmic curve roughly halves so dark
// a picture, so at 1.0 the waiting men were near-black shapes on a near-black gate (18 on screen, against 37 to 43 for
// W2 and W3). At 1.6 they stand out against the lit pavement and pier (28 quiet, 50 once the windows are lit). Judge
// it again when the painting comes: the notice corner's painting came out brighter than its plate (57 to 77).
// Its glow is softer (0.4) and No. 1's gate lamp's own glow kept low (LAMP_GLOW_W1), so the lamp no longer outshines the
// gate (round 5's critique, finding 5: the lamp glass was the brightest thing in W1).
const LOOK_W1 = { ...LOOK, exposure: 1.6, glowStrength: 0.4 };
const LAMP_GLOW_W1 = { 'no-1': 0.2 };
// the labels over W3: their size, the rows (pixels down the frame) their words stand on, how far apart (pixels) the
// labels must keep, and the things in the picture their words must not cover (all checked)
const LABELS = { size: 42, machinesRow: 0.40 * 1920, workersRow: 0.69 * 1920, materialsBelow: 125, apart: 12,
  keepClearOf: ['gate-board-no-1', 'gate-board-no-2', 'handcart'] };
// the level price arrow: its row at least this far down (0.31 of the frame) and this far clear of No. 1's gate board
const PRICE_ARROW = { row: 0.31 * 1920, clear: 24, width: 10, size: 30 };

export async function build(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w3', 'w1'], pictures: PICTURES, behind: 'w1 behind', hideInBehind: 'men' });
  const T = {
    picture: kit.at('Picture'), country: kit.at('country'), workers: kit.at('workers'), materials: kit.at('materials'), machines: kit.at('machines'),
    cut: kit.at('In'), slideFrom: kit.at('Workers', 2), slideTo: kit.at('Call'), quiet: kit.at('quiet'), spends: kit.at('spends'),
    go: kit.at('go'), start: kit.at('start'), more: kit.at('More'), things: kit.at('things'), barely: kit.at('barely'),
  };
  const pageEnd = kit.lastWordEnd + join.after + join.length;
  const checked = new Set();   // the checks already reported (reportGap)
  const both = kit.stillShot(works.cameraAt('w3'), [], { name: '3a both gates' });
  const quietGate = kit.stillShot(works.cameraAt('w1', 'plate'),
    [{ kind: 'zoom in', from: T.slideFrom, to: T.slideTo, ...works.cameraAt('w1', 'composed') }], { name: '3b the quiet gate' });

  function pose(t) {
    const inW1 = t >= T.cut;
    let painting = inW1 ? 'w1' : 'w3', blendTo = null, blend = 0, men = true, gate, gateMoving = false;
    let no1 = 'quiet';
    if (inW1 && t >= T.go) {
      no1 = 'working';
      if (GO === 'swing') {
        // the fallback: the gate swings open in 0.8 s and the men fade in 1.2 s inside the swing
        const swing = THREE.MathUtils.clamp((t - T.go) / 0.8, 0, 1);
        gate = 84 * (1 - (1 - swing) ** 3);
        gateMoving = swing < 1;
        const fade = steppedBlend(t, T.go, { length: 1.2, steps: 6 });
        if (fade < 1) { blendTo = 'w1 men gone'; blend = fade; } else { painting = 'w1 men gone'; men = false; }
      } else {
        painting = 'w1 men gone';   // the time cut: the men simply gone, the gate open
        men = false;
      }
    }
    if (inW1 && t >= T.start) {
      // No. 1's windows light in three steps over 0.8 s (each step one more drawing of the held set)
      const lit = steppedBlend(t, T.start, { length: 0.8, steps: 3 });
      if (lit < 1) { painting = 'w1 men gone'; blendTo = 'w1 working'; blend = lit; } else { painting = 'w1 working'; blendTo = null; blend = 0; }
      men = false;
    }
    // after "go" the brazier burns lower, so the time cut reads as time passing (with the swing, as the men fade)
    const fire = inW1 && t >= T.go ? (GO === 'swing' ? 1 - (1 - FIRE_AFTER_A_WHILE) * steppedBlend(t, T.go, { length: 1.2, steps: 6 }) : FIRE_AFTER_A_WHILE) : 1;
    const still = works.set(t, {
      view: inW1 ? 'w1' : 'w3', painting, behind: inW1 ? 'w1 behind' : null, blendTo, blend, men, fire, lampGlow: inW1 ? LAMP_GLOW_W1 : undefined,
      no1: { state: no1, gate, gateMoving, smokeFrom: T.start, litSteps: t >= T.start + 0.8 ? [1, 2, 3] : [], crates: T.things },
      no2: { state: 'flat out' },
    });
    const camera = inW1 ? quietGate(t) : both(t);
    const sliding = inW1 && t > T.slideFrom && t < T.slideTo;
    return { camera, still: sliding ? false : still, look: inW1 ? LOOK_W1 : LOOK };
  }

  // the words' places (pixels): the top band, left-aligned from 0.06 across, never past 0.90
  const LINE_1 = 172, LINE_2 = 250;
  function draw2D(ctx, t) {
    const inW1 = t >= T.cut;
    // everything over W3 ends exactly on the cut to W1 (fadeOut 0): a fade a frame early made the cut two steps
    const shade = inW1 ? presence(t, T.quiet - 0.2, Infinity, 0.5) : presence(t, T.picture - 0.2, T.cut, 0.5, 0);
    topShade(ctx, shade);
    if (!inW1) {
      buildWords(ctx, t, { parts: [{ text: 'PICTURE TWO FACTORIES', at: T.picture }], until: T.cut, y: LINE_1, size: 66, fadeOut: 0 });
      buildWords(ctx, t, { parts: [{ text: 'EACH ONE = A WHOLE COUNTRY', at: T.country }], until: T.cut, y: LINE_2, size: 46, colour: INK.amber, fadeOut: 0 });
      // the words come in with their lines (wordsWithLine): MACHINES comes on "machines", under a second before the cut
      const label = { plate: true, size: LABELS.size, until: T.cut, fadeOut: 0, wordsWithLine: true };
      const drawn = {};
      for (const [name, options] of Object.entries(labelsW3(ctx))) if (options) drawn[name] = callout(ctx, t, { ...label, ...options });
      checkLabels(drawn);
      return true;
    }
    buildWords(ctx, t, { parts: [{ text: 'THE QUIET FACTORY', at: T.quiet }], until: pageEnd, y: LINE_1, size: 72 });
    const spent = buildWords(ctx, t, { parts: [{ text: 'NEW MONEY SPENT', at: T.spends }], until: T.more, y: LINE_2, size: 50, colour: INK.amber });
    const chain = works.screen('no-1-chain');
    if (spent && chain) {
      // a small arrow into the gate: the last stretch of the way from the words to the chain between the gate leaves
      const from = { x: chain.x + ((spent.left + spent.right) / 2 - chain.x) * 0.3, y: chain.y + (spent.bottom + 18 - chain.y) * 0.3 };
      pointer(ctx, t, { at: T.spends + 0.25, until: T.more, from, to: chain, width: 6 });
    }
    buildWords(ctx, t, {
      parts: [{ text: 'MORE MONEY', at: T.more }, { text: '+ MORE THINGS TO BUY', at: T.things }, { text: '→ PRICES BARELY MOVE', at: T.barely, colour: INK.amber }],
      until: pageEnd, y: LINE_2, size: 50,
    });
    // the price arrow across No. 1's upper windows, under its gate board: level (prices barely move). Its row comes from
    // the board's place on the frame: at least PRICE_ARROW.clear pixels below the board for the word PRICES over its tail
    // (round 5's critique, finding 2: drawn at a fixed y 545, it ran along the board's bottom edge)
    // It starts right of the gate lamp (which hangs at that height) and ends as far right of the column's middle.
    const column = works.screen('no-1-gate'), board = works.screenBox('gate-board-no-1'), lamp = works.screenBox('no-1-gate-lamp');
    if (column && board) {
      const row = Math.max(PRICE_ARROW.row, board.bottom + PRICE_ARROW.clear + PRICE_ARROW.size * 0.76 + PRICE_ARROW.width + 6 + 4);
      const fromX = Math.max(110, column.x - 230, lamp ? lamp.right + PRICE_ARROW.clear + PRICE_ARROW.width : -Infinity);
      const arrow = priceArrow(ctx, t, { at: T.barely + 0.15, from: { x: fromX, y: row }, length: column.x + 230 - fromX, angle: 0, word: 'PRICES',
        width: PRICE_ARROW.width, size: PRICE_ARROW.size, edge: true });
      if (arrow) reportGap(checked, 'page 3: the level PRICES arrow and No. 1\'s gate board', gapToBox(board, arrow.outline), PRICE_ARROW.clear);
      if (arrow && lamp) reportGap(checked, 'page 3: the level PRICES arrow and No. 1\'s gate lamp', gapToBox(lamp, arrow.outline), PRICE_ARROW.clear);
    }
    return true;
  }

  // The three labels over W3, placed from where their things are on the frame (round 6 of log 34; round 5's critique,
  // finding 10). MACHINES: over No. 2's own column on LABELS.machinesRow, its line dropping straight from the flywheel,
  // its plate's right edge inside 0.90 across. WORKERS: its line leaves the right-hand man sideways at head height, past
  // the brazier, drops to LABELS.workersRow and runs on to its words on the right (one hook, not a bracket enclosing
  // nothing). MATERIALS: from the crates down and to the right, past the end of WORKERS' words, its words to the left
  // of its line's end, LABELS.materialsBelow pixels lower.
  function labelsW3(ctx) {
    const men = works.screen('no-1-crowd-side'), fire = works.screen('brazier'), crates = works.screen('no-2-crates'), flywheel = works.screen('no-2-flywheel');
    ctx.save(); ctx.font = `800 ${LABELS.size}px Inter`;
    const width = (text) => ctx.measureText(text).width;
    const plateWidth = (text) => width(text) + 2 * LABELS.size * 0.45;
    const workersWidth = width('WORKERS'), machinesWidth = plateWidth('MACHINES');
    ctx.restore();
    const labels = {};
    if (flywheel) {
      // the line's end stands so that the plate (52 pixels on from it) ends inside TEXT_RIGHT
      const endX = Math.min(flywheel.x, TEXT_RIGHT - 52 - machinesWidth + LABELS.size * 0.45);
      labels.machines = { at: T.machines, point: flywheel, text: 'MACHINES', dx: endX - flywheel.x, dy: LABELS.machinesRow - flywheel.y, side: 'right' };
    }
    let workersRight = null;
    if (men) {
      // sideways at head height, at least 60 pixels and 40 past the brazier's flames
      const across = Math.max(60, (fire ? fire.x + 40 : men.x + 60) - men.x);
      labels.workers = { at: T.workers, point: men, text: 'WORKERS', corner: { dx: across, dy: -8 }, dx: across, dy: LABELS.workersRow - men.y, side: 'right' };
      workersRight = men.x + across + 52 + workersWidth + LABELS.size * 0.45;
    }
    if (crates) {
      // the line passes the right end of WORKERS' plate (LABELS.apart clear) where it crosses WORKERS' row
      const rowY = LABELS.workersRow - LABELS.size * 0.82, down = LABELS.workersRow + LABELS.materialsBelow - crates.y;
      const share = Math.max(0.05, (rowY - crates.y) / down);
      const pass = workersRight === null ? 0 : (workersRight + LABELS.apart + 6 - crates.x) / share;
      labels.materials = { at: T.materials, point: crates, text: 'MATERIALS', dx: Math.max(30, pass), dy: down, side: 'left' };
    }
    return labels;
  }
  // the labels keep LABELS.apart pixels clear of each other (each one's words against the others' lines and words),
  // and MACHINES' words stand over No. 2's column (right of the middle between the gates)
  function checkLabels(drawn) {
    const names = Object.keys(drawn).filter((name) => drawn[name]);
    for (const a of names) {
      for (const b of names) {
        if (a !== b) reportGap(checked, `page 3: the words of ${a.toUpperCase()} and the label ${b.toUpperCase()}`, gapToBox(drawn[a].words, drawn[b].outline), LABELS.apart);
      }
    }
    for (const name of names) {
      for (const thing of LABELS.keepClearOf) {
        const box = works.screenBox(thing);
        if (box) reportGap(checked, `page 3: the words of ${name.toUpperCase()} and the ${thing}`, gapToBox(box, pointsRound(drawn[name].words)), LABELS.apart);
      }
    }
    const one = works.screen('no-1-gate'), two = works.screen('no-2-gate');
    if (drawn.machines && one && two) reportGap(checked, 'page 3: the words of MACHINES right of the middle between the gates', drawn.machines.words.left - (one.x + two.x) / 2, 0);
    if (drawn.machines) reportGap(checked, 'page 3: the words of MACHINES inside 0.90 across', TEXT_RIGHT - drawn.machines.words.right, 0);
  }

  return { pose, draw2D };
}
