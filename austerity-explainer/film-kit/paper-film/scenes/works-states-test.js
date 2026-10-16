// What this does: draws the Works' states that later pages of chapter 2 for newcomers will use, on the real Works set,
// before those pages are built (round 4 of log 34), so each can be looked at in stills and fixed first. Not part of the
// film. Each state is drawn on its page's own spoken words (the estimated timeline), with the plates standing in for
// the paintings, as on pages 3 to 5:
//   state=bank    page 9's shot 9b (W3, from "In", 214.0 s): the tags QUIET and FLAT OUT; on "most" (2) the bank's
//                 window lights from inside in 1 s (four steps), the sign brightening with it and a soft pool of light
//                 on the pavement. Until then the bank's sign is dim, as on every page before 9.
//   state=slows   page 12's shot 12b (W2, the composed frame, from "In", 294.8 s): the tag FLAT OUT, which becomes THE
//                 FLAT-OUT FACTORY SLOWS on "slows" as the gate swings half shut, the smoke thins to one chimney (the
//                 heavy puffs drift away) and two thirds of the lit windows dim (a 1.5 s blend in five steps to the
//                 windows-only slowed picture, round 5); on "workers" a time cut to the slowed state picture with No. 2's
//                 eight men waiting (their figures join the set, as No. 1's are on page 3); MORE WORKERS AT THE GATE on
//                 "gate".
//   state=w4      page 14's shot 14a (W4): No. 2's gate half shut from inside its yard, the eight men outside as dark
//                 silhouettes (own surfaces, never painted); one slide of 1.2 m toward the gate from "With" to "says".
//                 Round 5: the jacket's corner in one pool of lamplight, the rest in the dusk; No. 2's gateway crates
//                 are hidden (works-shot.json w4.left_out: they are not in the W4 plate).
// For page 12: the plan dims two thirds of No. 2's windows on "slows" (a 1.5 s blend to the slowed picture) and brings
// the men on "workers". The slowed state picture (works-w2-slowed-state.png) holds both the dark windows and the men,
// so a blend to it on "slows" would fade the men in as ghosts. So "slows" blends to a second state picture with only the
// windows (works-w2-slowed-windows-state.png: make_state_picture.py with a mask of the windows' change alone, round 5),
// and "workers" cuts to the slowed state picture, whose windows are the same.
// Use (from film-kit): PAPER_FILM_QUERY=state=slows node paper-film/tools/render-paper-film.mjs works-states-test OUT --stills 296 298
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { buildWorks, steppedBlend, WORKS_IN_USE } from './inflation-chapter-2-newcomers/works-effects.js';
import { buildWords, topShade, presence, INK } from './graphics.js';

const STATE = new URLSearchParams(location.search).get('state') ?? 'slows';
const LOOK = { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3 };
const PAGE_OF = { bank: 9, slows: 12, w4: 14 };

// page 9, shot 9b: W3 with the bank lighting
async function bankPage(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w3'], pictures: { w3: 'works-w3-plate.jpg' } });
  const T = { cut: kit.at('In'), picture: kit.at('picture'), most: kit.at('most', 2) };
  const both = kit.stillShot(works.cameraAt('w3'), [], { name: '9b both factories, the bank lit' });
  return {
    pose(t) {
      const bank = steppedBlend(t, T.most, { length: 1.0, steps: 4 });
      const still = works.set(t, { view: 'w3', painting: 'w3', no1: { state: 'quiet' }, no2: { state: 'flat out' }, bank });
      return { camera: both(t), still, look: LOOK };
    },
    draw2D(ctx, t) {
      topShade(ctx, 1);
      works.drawTags(ctx, t, { at: T.cut });
      buildWords(ctx, t, { parts: [{ text: 'IN OUR PICTURE', at: T.picture }], y: 150, size: 40 });
      return true;
    },
  };
}

// page 12, shot 12b: W2 slows and the queue returns
async function slowsPage(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w2'], no2Men: 'painted',
    pictures: { w2: 'works-w2-plate.jpg', 'w2 slowed': 'works-w2-slowed-state.png', 'w2 windows dim': 'works-w2-slowed-windows-state.png' } });
  const T = { cut: kit.at('In'), picture: kit.at('picture'), slows: kit.at('slows'), workers: kit.at('workers'), gate: kit.at('gate') };
  const flatOutGate = kit.stillShot(works.cameraAt('w2', 'composed'), [], { name: '12b the flat-out factory slows' });
  const swingFor = 1.2;
  return {
    pose(t) {
      const slowing = t >= T.slows;
      const swing = THREE.MathUtils.clamp((t - T.slows) / swingFor, 0, 1);
      const gate = slowing ? 96 - 54 * (1 - (1 - swing) ** 3) : 96;
      const queue = t >= T.workers;
      // two thirds of the windows dim on "slows" (1.5 s, in five steps: each step one drawing of the held set)
      const dim = queue ? 0 : steppedBlend(t, T.slows, { length: 1.5, steps: 5 });
      const still = works.set(t, {
        view: 'w2', painting: queue ? 'w2 slowed' : 'w2', men2: queue, blendTo: dim > 0 ? 'w2 windows dim' : null, blend: dim,
        no1: { state: 'quiet' },
        no2: slowing ? { state: 'slowed', gate, gateMoving: swing > 0 && swing < 1, was: { state: 'flat out', until: T.slows } } : { state: 'flat out' },
      });
      return { camera: flatOutGate(t), still, look: LOOK };
    },
    draw2D(ctx, t) {
      topShade(ctx, presence(t, T.cut - 0.2, Infinity, 0.5));
      buildWords(ctx, t, { parts: [{ text: 'IN OUR PICTURE', at: T.picture }], y: 150, size: 40 });
      works.drawTags(ctx, t, { at: T.cut, view: 'w2', slowsAt: T.slows });
      buildWords(ctx, t, { parts: [{ text: 'MORE WORKERS AT THE GATE', at: T.gate }], y: 226, size: 54, colour: INK.amber });
      return true;
    },
  };
}

// page 14, shot 14a: W4 from inside No. 2's yard, the men outside as silhouettes
async function w4Page(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w4'], no2Men: 'silhouettes', pictures: { w4: 'works-w4-plate.jpg' } });
  // No. 2's gateway crates are left out of the W4 plate (round 5: from inside the yard they stood big in the frame's
  // bottom-left corner, cut by its edge); works-shot.json's w4.left_out names them, so page 14 hides them too
  for (const name of works.facts.w4?.left_out ?? []) {
    const thing = kit.scene.getObjectByName(name);
    if (thing) thing.visible = false;
  }
  works.projection.refresh();
  const T = { with: kit.at('With'), says: kit.at('says') };
  const yard = kit.stillShot(works.cameraAt('w4', 'plate'), [{ kind: 'zoom in', from: T.with, to: T.says, ...works.cameraAt('w4', 'composed') }], { name: '14a from inside the yard' });
  return {
    pose(t) {
      const still = works.set(t, { view: 'w4', painting: 'w4', men: false, men2: true, no1: { state: 'quiet' }, no2: { state: 'slowed' } });
      const sliding = t > T.with && t < T.says;
      return { camera: yard(t), still: sliding ? false : still, look: LOOK };
    },
    draw2D(ctx) { topShade(ctx, 1); return true; },
  };
}

const BUILDERS = { bank: bankPage, slows: slowsPage, w4: w4Page };

export function build() {
  if (!BUILDERS[STATE]) throw new Error(`works-states-test: no state "${STATE}" (bank, slows or w4)`);
  return buildCinemaChapter({
    timelineUrl: '/examples/inflation-chapter-2-newcomers/timeline-estimated.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [{ build: BUILDERS[STATE] }],
    pageNumbers: [PAGE_OF[STATE]],
  });
}
