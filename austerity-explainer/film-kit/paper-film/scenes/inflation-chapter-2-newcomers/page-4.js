// What this does: page 4 of chapter 2 for newcomers, "The flat-out factory, the first guess" (about 75.1 to 95.7 s;
// plan 34, part 2, shot 4a in shots.json). Malina: "In the second factory, every worker and every machine is already
// busy... working as hard as they can. No one waits at the gate. Call it the flat-out factory. The same new money is
// spent on what this factory makes. What happens to prices? Have a guess."
//   4a  W2, the open No. 2 gate with nobody waiting, from where a waiting man would stand (W1's spot, mirrored): flat
//       out, the gate wide open, windows blazing, both chimneys smoking hard, the empty pavement lit by the gateway. On
//       "busy" a burst for 2 seconds: the windows flicker three times as strongly, a slow dark band (the machines'
//       shadows) passes across No. 2's panes and the doorway's light pulses with it; then the brighter flicker stays. One slide of 1.2 m toward the gate from "No" to "factory" (we walk up to
//       the gate with nobody in the way), never turning, stopping on the composed frame. THE FLAT-OUT FACTORY with a
//       small line under it, FLAT OUT = WORKING AS HARD AS THEY CAN; NEW MONEY SPENT (the same words as page 3); WHAT
//       HAPPENS TO PRICES?; HAVE A GUESS with a ring that fills over 4 seconds. Then the 4-second guess hold on the
//       still frame, and page 5 runs on in the same frame with no join you can see.
// The run-on: page 5 opens on this same view and composed frame with the same words and the full ring, and every
// moving thing depends only on the moment (works-effects.js, fixed seeds), so this page hands over with a short
// plain blend between two identical pictures (the stage's 'run-on' join: a dissolve would darken them in the middle),
// well inside the guess hold (after the ring is full, before page 5's first word). Live: heavy smoke from both
// chimneys, window flicker, the gate lamp's glow.
import { smooth } from '../cinema-kit.js';
import { buildWorks, WORKS_IN_USE } from './works-effects.js';
import { buildWords, topShade, guessRing, presence, INK } from '../graphics.js';

// How this page leaves: no join you can see. A plain blend of 0.2 s between two identical pictures, 3.5 s into the
// 4-second guess hold (the ring is full by then; page 5's first word comes at about 4.0 s).
export const join = { kind: 'run-on', after: 3.5, length: 0.2 };

// The pictures shone onto the set. Until the paintings are approved, the PLATE stands in for its painting.
export const PICTURES = {
  w2: 'works-w2-plate.jpg',   // W2, No. 2 flat out: the gate's warm light on the empty pavement
};
export const LOOK = { exposure: 1.0, aperture: 4.0, maxBlur: 2, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3 };

// The question and the guess ring, drawn the same way here and at the start of page 5 (so the run-on can't be seen).
// guessAt: when the ring starts to fill; until: when they go.
export const QUESTION = { line1: 172, line2: 238, size1: 66, size2: 42 };
export function drawQuestion(ctx, t, { questionAt, guessAt, until = Infinity }) {
  buildWords(ctx, t, { parts: [{ text: 'WHAT HAPPENS TO PRICES?', at: questionAt }], until, y: QUESTION.line1, size: QUESTION.size1 });
  const guess = buildWords(ctx, t, { parts: [{ text: 'HAVE A GUESS', at: guessAt }], until, y: QUESTION.line2, size: QUESTION.size2, colour: INK.amber });
  if (guess) guessRing(ctx, t, { at: guessAt, until, length: 4, x: guess.right + 46, y: QUESTION.line2 - QUESTION.size2 * 0.34, radius: 22, width: 7 });
}

export async function build(kit) {
  const works = await buildWorks(kit, { folder: WORKS_IN_USE, views: ['w2'], pictures: PICTURES });
  const T = {
    busy: kit.at('busy'), no: kit.at('No'), flatOut: kit.at('flat-out'), factory: kit.at('factory', 2), spent: kit.at('spent'),
    prices: kit.at('prices'), guess: kit.at('guess'),
  };
  const camera = kit.stillShot(works.cameraAt('w2', 'plate'),
    [{ kind: 'zoom in', from: T.no, to: T.factory, ...works.cameraAt('w2', 'composed') }], { name: '4a the flat-out gate' });

  function pose(t) {
    const still = works.set(t, { view: 'w2', painting: 'w2', no1: { state: 'quiet' }, no2: { state: 'flat out', busy: smooth((t - T.busy) / 0.6), busyAt: T.busy } });
    const sliding = t > T.no && t < T.factory;
    return { camera: camera(t), still: sliding ? false : still, look: LOOK };
  }

  function draw2D(ctx, t) {
    topShade(ctx, presence(t, T.flatOut - 0.2, Infinity, 0.5));
    buildWords(ctx, t, { parts: [{ text: 'THE FLAT-OUT FACTORY', at: T.flatOut }], until: T.prices, y: 172, size: 68 });
    buildWords(ctx, t, { parts: [{ text: 'FLAT OUT = WORKING AS HARD AS THEY CAN', at: T.flatOut + 0.25 }], until: T.prices, y: 234, size: 38 });
    buildWords(ctx, t, { parts: [{ text: 'NEW MONEY SPENT', at: T.spent }], until: T.prices, y: 306, size: 50, colour: INK.amber });
    drawQuestion(ctx, t, { questionAt: T.prices, guessAt: T.guess });
    return true;
  }

  return { pose, draw2D };
}
