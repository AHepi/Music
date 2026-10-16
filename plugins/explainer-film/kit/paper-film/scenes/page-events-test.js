// What this does: a small made-up cinema chapter (three pages of plain boxes in a yard, no paintings or models to
// load) for testing the page timing tools: paper-film/tools/page_events.mjs, tools/check_page_layout.mjs and
// calculators/plan_page_timing.py. It uses every kind of flat graphic in graphics.js (words that build, labels,
// pointers, a price arrow, a counter, a rule card, a guess ring, a name tag, the top shade), a held shot with live
// effects (dust and a flickering lamp), a cut, a slide between two words, and the page joins.
// Its timeline is made up: calculators/tests/fixtures/page-timing/page-events-test-timeline.json.
//
// ?variant=faults (PAPER_FILM_QUERY=variant=faults, or page_events.mjs --query variant=faults) plants the faults the
// project found by hand, so the tools can be tested on them. On page 2: a word said three times looked up without
// saying which time (lessons 28, 46); a new line drawn over a fading one (round 3, NO SPARE); a heading whose letters
// start 0.047 down (round 3) and a line past 0.90 across; an arrow shown for one frame and a tag that jumps across the
// frame (log 27); a held-shot key kept during a slide; a hold with no held-shot key; a spark whose showing depends on
// what was drawn before (lesson 29); words that fade a frame before a cut (round 3); a label readable for under a
// second before a cut (round 4, MACHINES); and a run-on join into a different view. On page 1: a count that lands
// after its spoken number and drops the ledger's "about" (lesson 53, decision 21). Without it the pages are clean.
// Not part of any film.
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { buildWords, callout, pointer, priceArrow, counter, ruleCard, guessRing, nameTag, topShade, INK } from './graphics.js';
import { Motes } from './effects.js';

const VARIANT = new URLSearchParams(location.search).get('variant') ?? 'clean';
const FAULTS = VARIANT === 'faults';

// a plain yard: ground, a back wall and three boxes; boxes[i].top is the middle of its top face
function yard(kit) {
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshLambertMaterial({ color: 0x4a4038 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  const wall = new THREE.Mesh(new THREE.BoxGeometry(30, 8, 0.4), new THREE.MeshLambertMaterial({ color: 0x6b5a4c }));
  wall.position.set(0, 4, -12);
  kit.scene.add(ground, wall);
  // (the frame is tall and narrow: at 10 m it shows only about 2 m either side of the middle)
  const boxes = [[-1.25, 1.6, 0xb08a5a], [0.1, 2.2, 0x8a9aa6], [1.3, 1.2, 0x9c6b4e]].map(([x, height, colour]) => {
    const box = new THREE.Mesh(new THREE.BoxGeometry(1.0, height, 1.0), new THREE.MeshLambertMaterial({ color: colour }));
    box.position.set(x, height / 2, -4);
    box.castShadow = true; box.receiveShadow = true;
    kit.scene.add(box);
    return { mesh: box, top: [x, height, -4] };
  });
  return boxes;
}

// a lamp that flickers (live: drawn every frame over the held set)
function lamp(kit, at) {
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffd9a0 }));
  bulb.position.set(...at);
  const light = kit.glow(at, { strength: 3, reach: 7 });
  kit.moving(bulb, light);
  kit.scene.add(bulb);
  return { bulb, light, set(t) { const k = 0.8 + 0.2 * Math.sin(t * 17) * Math.sin(t * 5.3); light.intensity = 3 * k; bulb.material.color.setScalar(0.7 + 0.3 * k); } };
}

const WIDE = { position: [0, 2.2, 6], target: [0, 1.4, -4], fov: 40 };
const GATE = { position: [-1.2, 1.7, 2.6], target: [-1.6, 1.2, -4], fov: 40 };
const GATE_NEAR = { position: [-1.4, 1.65, 1.2], target: [-1.7, 1.2, -4], fov: 40 };

// ---------------------------------------------------------------------------------------------------- page 1 (clean)
const page1 = {
  join: { kind: 'peel', after: 0.3, length: 0.85 },
  async build(kit) {
    kit.lightRig({ background: 0x10161a });
    const boxes = yard(kit);
    const done = kit.movingFromHere();
    const dust = new Motes(kit.scene, { count: 120, min: [-2.5, 0, -8], max: [2.5, 4, -1], seed: 5 });
    done();
    const light = lamp(kit, [-1.6, 2.8, -3]);
    const T = {
      picture: kit.at('Picture'), country: kit.at('country'), workers: kit.at('workers', 1), materials: kit.at('materials'),
      cut: kit.at('Workers', 2), wait: kit.at('wait'), spends: kit.at('spends'), so: kit.at('So'), prices: kit.at('prices'),
      up: kit.at('up'), four: kit.at('four'), government: kit.at('government'),
    };
    const pageEnd = kit.lastWordEnd + 0.3 + 0.85;
    const wide = kit.stillShot(WIDE, [], { name: '1a the yard' });
    const gate = kit.stillShot(GATE, [{ kind: 'zoom in', from: T.wait, to: T.spends, ...GATE_NEAR }], { name: '1b the gate' });
    function pose(t) {
      dust.set(t);
      light.set(t);
      const inGate = t >= T.cut;
      const sliding = inGate && t > T.wait && t < T.spends;
      return { camera: inGate ? gate(t) : wide(t), still: sliding ? false : (inGate ? 'gate' : 'yard'), look: { exposure: 1.1 } };
    }
    function draw2D(ctx, t, pageKit) {
      const inGate = t >= T.cut;
      topShade(ctx, 1);
      if (!inGate) {
        buildWords(ctx, t, { parts: [{ text: 'PICTURE TWO BOXES', at: T.picture }], until: T.cut, y: 172, size: 66, fadeOut: 0 });
        buildWords(ctx, t, { parts: [{ text: 'EACH ONE = A WHOLE COUNTRY', at: T.country }], until: T.cut, y: 250, size: 46, colour: INK.amber, fadeOut: 0 });
        const label = { plate: true, size: 42, until: T.cut, fadeOut: 0, wordsWithLine: true };
        callout(ctx, t, { ...label, at: T.workers, point: pageKit.toScreen(boxes[0].top), text: 'WORKERS', dx: 60, dy: 260 });
        callout(ctx, t, { ...label, at: T.materials, point: pageKit.toScreen(boxes[2].top), text: 'MATERIALS', dx: -60, dy: 330 });
        return true;
      }
      buildWords(ctx, t, { parts: [{ text: 'THE GATE', at: T.cut }], until: pageEnd, y: 172, size: 72 });
      const spent = buildWords(ctx, t, { parts: [{ text: 'NEW MONEY SPENT', at: T.spends }], until: T.so, y: 250, size: 50, colour: INK.amber });
      if (spent) pointer(ctx, t, { at: T.spends + 0.25, until: T.so, from: { x: spent.right - 60, y: spent.bottom + 20 }, to: pageKit.toScreen(boxes[0].top) });
      buildWords(ctx, t, { parts: [{ text: '→ PRICES GO UP', at: T.prices, colour: INK.amber }], until: pageEnd, y: 250, size: 50 });
      priceArrow(ctx, t, { at: T.prices, drawFor: T.up - T.prices, from: { x: 140, y: 760 }, length: 420, angle: 28, word: 'PRICES' });
      nameTag(ctx, t, { at: T.cut + 0.5, text: 'WORKERS', x: pageKit.toScreen(boxes[0].top).x, y: 640 });
      ruleCard(ctx, t, { at: T.government, until: T.so, box: [65, 300, 907, 110], size: 40, parts: [{ text: 'THE GOVERNMENT SPENDS', at: T.government }] });
      // the figure counts up and lands on "four" (lesson 53). With the faults it lands late and drops the ledger's "about"
      counter(ctx, t, { at: T.four - 0.35, duration: FAULTS ? 0.95 : 0.4, until: pageEnd, from: 0, to: 4, x: 540, y: 1180, size: 110,
        format: FAULTS ? (v) => `${v.toFixed(0)}%` : (v) => `ABOUT ${v.toFixed(0)}%` });
      return true;
    }
    return { pose, draw2D };
  },
};

// ---------------------------------------------------------------------------- page 2 (clean, or with planted faults)
const page2 = {
  join: FAULTS ? { kind: 'run-on', after: 0.3, length: 0.2 } : { kind: 'peel', after: 0.3, length: 0.85 },
  async build(kit) {
    kit.lightRig({ background: 0x10161a });
    const boxes = yard(kit);
    const light = lamp(kit, [1.5, 2.6, -3]);
    // a spark on the middle box (live). With the faults: once on it is never put out again, so a moment drawn out of
    // order shows it too early (lesson 29)
    const spark = new THREE.Mesh(new THREE.SphereGeometry(0.1, 10, 8), new THREE.MeshBasicMaterial({ color: 0xfff2c0 }));
    spark.position.set(0.1, 2.4, -4);
    kit.moving(spark);
    kit.scene.add(spark);
    const T = {
      no: kit.at('No'), spare: kit.at('spare'), boxes: kit.at('boxes'), what: kit.at('What'), happens: kit.at('happens'), have: kit.at('Have'), guess: kit.at('guess'),
      most: kit.at('Most'), agree: kit.at('agree'), this: kit.at('this'), the2: kit.at('The', 1), prices2: kit.at('prices', 2), stay: kit.at('stay'),
      up2: kit.at('up', 2), that: kit.at('That'),
      // with the faults, a word said three times on the page asked for without saying which time (lessons 28, 46)
      prices: FAULTS ? kit.at('prices') : kit.at('prices', 1),
    };
    const pageEnd = kit.lastWordEnd + 0.3 + (FAULTS ? 0.2 : 0.85);
    const held = kit.stillShot(WIDE, FAULTS ? [{ kind: 'zoom in', from: T.the2, to: T.stay, ...GATE_NEAR }] : [], { name: '2a the boxes' });
    const close = kit.stillShot(GATE, [], { name: '2b the gate' });
    function pose(t) {
      light.set(t);
      if (FAULTS) { if (t > T.most) spark.visible = true; } else spark.visible = t > T.most;
      if (!FAULTS) return { camera: held(t), still: 'boxes' };
      // faults: the held-shot key is kept while the camera slides; then a hold with no key at all; a cut on "That"
      if (t >= T.that) return { camera: close(t), still: 'gate' };
      return { camera: held(t), still: t < T.stay ? 'boxes' : false };
    }
    if (FAULTS) spark.visible = false;
    function draw2D(ctx, t, pageKit) {
      topShade(ctx, 1);
      if (FAULTS) {
        // a new line in the same place while the old one fades out (round 3: "NO SPAREPENS TO PRICES?")
        buildWords(ctx, t, { parts: [{ text: 'NO SPARE', at: T.no }], until: T.what, y: 172, size: 72 });
        buildWords(ctx, t, { parts: [{ text: 'WHAT HAPPENS TO PRICES?', at: T.what - 0.15 }], until: T.agree, y: 172, size: 60 });
        // a heading whose letters start 0.047 down (round 3), and a line that runs past 0.90 across; both fade a frame
        // before the cut on "That" (round 3: the cut took two steps)
        buildWords(ctx, t, { parts: [{ text: 'MOST PEOPLE AGREE', at: T.agree }], y: 116, size: 34, until: T.that });
        buildWords(ctx, t, { parts: [{ text: '→ PRICES GO UP AND THE PRICES STAY UP', at: T.prices2, colour: INK.amber }], until: T.that, y: 250, size: 50, right: 1060 });
        // something shown for one frame only (log 27's one-frame faults): an arrow drawn at once and gone at once
        priceArrow(ctx, t, { at: T.this, until: T.this + 0.04, drawFor: 0.001, fadeOut: 0, from: { x: 200, y: 1000 }, length: 300, angle: 0, word: 'PRICES' });
        // a name tag that jumps across the frame in one frame while it shows (log 27: the scissors' jump)
        nameTag(ctx, t, { at: T.spare, until: T.agree, text: 'SPARE', x: t < T.happens ? 300 : 700, y: 900 });
        // a label that comes in only about 0.7 s before the cut, with the usual wait for its words (round 4, MACHINES)
        callout(ctx, t, { at: T.up2, until: T.that, fadeOut: 0, point: pageKit.toScreen(boxes[0].top), text: 'PRICES', dx: 80, dy: 300, plate: true });
      } else {
        buildWords(ctx, t, { parts: [{ text: 'NO SPARE', at: T.no }], until: T.what + 0.12, y: 172, size: 72 });
        buildWords(ctx, t, { parts: [{ text: 'WHAT HAPPENS TO PRICES?', at: T.what + 0.15 }], until: T.agree, y: 172, size: 60 });
        buildWords(ctx, t, { parts: [{ text: 'MOST PEOPLE AGREE', at: T.agree }], y: 142, size: 34, until: pageEnd });
        buildWords(ctx, t, { parts: [{ text: '→ PRICES GO UP', at: T.prices2, colour: INK.amber }, { text: '+ STAY UP', at: T.stay }], until: pageEnd, y: 250, size: 50 });
        callout(ctx, t, { at: T.boxes, until: T.most, point: pageKit.toScreen(boxes[1].top), text: 'SPARE BOXES', dx: 80, dy: 300, plate: true });
      }
      const guess = buildWords(ctx, t, { parts: [{ text: 'HAVE A GUESS', at: T.have }], until: T.agree, y: 238, size: 42, colour: INK.amber });
      if (guess) guessRing(ctx, t, { at: T.guess, until: T.agree, length: 0.8, x: guess.right + 46, y: 224, radius: 22 });
      return true;
    }
    return { pose, draw2D };
  },
};

// ------------------------------------------------------------------------------------------------------------ page 3
const page3 = {
  join: { kind: 'peel', after: 0.3, length: 0.85 },
  async build(kit) {
    kit.lightRig({ background: 0x10161a });
    yard(kit);
    const T = { rule: kit.at('rule') };
    const shot = kit.stillShot(GATE_NEAR, [], { name: '3a near the gate' });
    return {
      pose: (t) => ({ camera: shot(t), still: 'rule' }),
      draw2D(ctx, t) { topShade(ctx, 1); buildWords(ctx, t, { parts: [{ text: 'THE RULE', at: T.rule }], y: 172, size: 72 }); return true; },
    };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/calculators/tests/fixtures/page-timing/page-events-test-timeline.json',
    piecesFolder: '/paper-film/pieces/none', reliefFolder: '/assets/reliefs/none',
    pageFiles: [page1, page2, page3],
  });
}
