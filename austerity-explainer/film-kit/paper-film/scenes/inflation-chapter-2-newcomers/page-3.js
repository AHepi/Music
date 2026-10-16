// What this does: page 3 of chapter 2 for newcomers, "The quiet factory" (about 47.7 to 75.1 s; plan 34, part 2,
// shots 3a and 3b in shots.json). Malina: "Picture two factories. Think of each one as a whole country... all its
// workers, materials and machines. In the first, the machines stand still. Workers wait at the gate, hoping for a
// job. Call it the quiet factory. Now the government spends new money on what the factory makes. The workers go in.
// The machines start. More money... and more things to buy. So prices barely move."
//   3a  W3, both gates from the upstairs window across the cross street, held: PICTURE TWO FACTORIES, EACH ONE = A
//       WHOLE COUNTRY (to the cut), and labels WORKERS (No. 1's waiting men, its line leaving them sideways onto the
//       empty lane), MATERIALS (the crates at No. 2's gate) and MACHINES (the flywheel in No. 2's lit doorway), each
//       label's words coming in with its line (MACHINES is up only about 0.9 s before the cut). Live: No. 2's smoke and
//       window flicker, No. 1's brazier and lantern.
//   3b  W1, the shut No. 1 gate at the head of the queue. Cut in on "In"; one slide of 1.2 m along the queue toward
//       the gate, from "Workers" to "Call" (we join the line), never turning, stopping on the composed frame. THE
//       QUIET FACTORY; NEW MONEY SPENT with a small arrow to the chain between the gate leaves; on "go" a time cut: the gate open, the men
//       gone, the brazier still burning by the empty pier, the lantern and lunch tin still there; on "start" No. 1's
//       windows light in three steps and its chimney starts to smoke; MORE MONEY, + MORE THINGS TO BUY as crates
//       stencilled THIS WAY UP pop up in the open gateway; → PRICES BARELY MOVE with a level price arrow over No. 1.
// A state changes only while the camera holds. The one Works set serves both views: at the cut the projector moves
// from W3's plate camera to W1's (works-effects.js, projected-set.js setView).
// ?go=swing (PAPER_FILM_QUERY=go=swing) shows the plan's fallback for "go": the gate swings open in 0.8 s and the men
// fade in 1.2 s inside the swing (a blend in six steps), instead of the time cut.
import { THREE } from '../cinema-kit.js';
import { buildWorks, steppedBlend, WORKS_IN_USE } from './works-effects.js';
import { callout, buildWords, topShade, pointer, priceArrow, presence, INK } from '../graphics.js';

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
const LOOK = { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3 };
// W1 (3b) a little brighter, the whole shot alike (it changes only at the cut): W1's plate is the darkest of the Works
// (a frame's average 35 levels, against 49 for W2 and 59 for W3), and the stage's filmic curve roughly halves so dark
// a picture, so at 1.0 the waiting men were near-black shapes on a near-black gate (18 on screen, against 37 to 43 for
// W2 and W3). At 1.6 they stand out against the lit pavement and pier (28 quiet, 50 once the windows are lit). Judge
// it again when the painting comes: the notice corner's painting came out brighter than its plate (57 to 77).
const LOOK_W1 = { ...LOOK, exposure: 1.6 };

export async function build(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w3', 'w1'], pictures: PICTURES, behind: 'w1 behind', hideInBehind: 'men' });
  const T = {
    picture: kit.at('Picture'), country: kit.at('country'), workers: kit.at('workers'), materials: kit.at('materials'), machines: kit.at('machines'),
    cut: kit.at('In'), slideFrom: kit.at('Workers', 2), slideTo: kit.at('Call'), quiet: kit.at('quiet'), spends: kit.at('spends'),
    go: kit.at('go'), start: kit.at('start'), more: kit.at('More'), things: kit.at('things'), barely: kit.at('barely'),
  };
  const pageEnd = kit.lastWordEnd + join.after + join.length;
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
    const still = works.set(t, {
      view: inW1 ? 'w1' : 'w3', painting, behind: inW1 ? 'w1 behind' : null, blendTo, blend, men,
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
      const label = { plate: true, size: 42, until: T.cut, fadeOut: 0, wordsWithLine: true };
      // the labels over the lane's empty cobbles (the lower middle), each line from its thing; WORKERS' line leaves the
      // men sideways (it ran straight down over them in round 4 of log 34)
      callout(ctx, t, { ...label, at: T.workers, point: works.screen('no-1-crowd-side'), text: 'WORKERS', dx: 120, dy: 90 });
      callout(ctx, t, { ...label, at: T.materials, point: works.screen('no-2-crates'), text: 'MATERIALS', dx: -30, dy: 160 });
      callout(ctx, t, { ...label, at: T.machines, point: works.screen('no-2-flywheel'), text: 'MACHINES', dx: -70, dy: -190 });
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
    // the price arrow over No. 1's column, just under the words: level (prices barely move)
    const column = works.screen('no-1-gate');
    if (column) priceArrow(ctx, t, { at: T.barely + 0.15, from: { x: Math.max(110, column.x - 230), y: 545 }, length: 460, angle: 0, word: 'PRICES' });
    return true;
  }

  return { pose, draw2D };
}
