// What this does: chapter 1, page 9, "Why do it?" (a factory gate in a workers' street). Source:
// Clara E. Mattei, The Capital Order (2022); "power" is Mattei's answer (research entries C1-12,
// C1-23 and C1-27), said as hers.
//
// What happens, tied to Malina's words:
//   "Ask Mattei"                  her book folds up
//   "power"                       POWER crashes down from above; dust; the camera shakes
//   "Take away the alternatives"  a row of council houses and a queue at the unemployment office
//                                 fold up, then fold away as each is named ("public housing",
//                                 "help for the unemployed")
//   "whatever job is going"       a worker walks to the factory gate
//   "work more, consume less"     two posters slap onto the wall: WORK MORE, then CONSUME LESS

import { DustBurst } from '../../stage/paper-stage.js';
import { popUp, popUpUntil, foldDown, dropIn, slideIn, walkBob, hop, degrees, clamp01, easeIn } from '../paper-kit.js';

export const SHEETS = ['factory-gate'];

const POSTER_LOOK = { fontPx: 150, cardColour: '#ddd2b6', inkColour: '#26221e', borderColour: 'rgba(38,34,30,0.5)', minWidth: 980, aspect: 0.5 };

export async function build(kit) {
  const at = kit.at;
  const book = await kit.piece('book', { width: 2.3, x: 2.5, y: 7.2, z: 1.0, yaw: degrees(-6) });
  const power = await kit.word(['POWER'], { size: 1.5, x: 0, y: 10.9, z: 0.55 });
  const homes = await kit.piece('council-houses', { width: 3.7, x: -2.0, y: 4.4, z: 1.2 });
  const queue = await kit.piece('dole-queue', { width: 3.0, x: 2.1, y: 4.0, z: 1.6 });
  const worker = await kit.piece('worker-standing', { width: 1.45, x: -0.5, y: 1.0, z: 1.8 });
  const workMore = await kit.card(['WORK', 'MORE'], { look: POSTER_LOOK, width: 2.5, x: -2.85, y: 7.9, z: 0.35, yaw: degrees(2) });
  const consumeLess = await kit.card(['CONSUME', 'LESS'], { look: POSTER_LOOK, width: 2.5, x: -2.85, y: 6.2, z: 0.35, yaw: degrees(-2) });
  const dust = kit.effect(new DustBurst({ count: 20, seed: 23 }));

  const T = {
    book: at('Mattei') - 0.10, bookAway: at('power') - 0.32,
    powerLands: at('power') + 0.03,
    homes: at('Take') - 0.12, queue: at('away') - 0.05,
    homesGone: at('housing') + 0.15, queueGone: at('unemployed') + 0.3,
    workerWalks: at('people') - 0.05,
    workMore: at('work') + 0.02, consumeLess: at('consume') + 0.02,
  };
  kit.shake(T.powerLands, 0.11, 0.16);
  kit.shake(T.workMore, 0.025, 0.08);
  kit.shake(T.consumeLess, 0.025, 0.08);

  // a poster pasted onto the wall: it flies in from near the camera and slaps flat against the bricks
  function slapOn(t, at, poster) {
    if (t < at - 0.2) return { visible: false };
    const x = clamp01((t - (at - 0.2)) / 0.2);
    const settle = t > at ? degrees(2) * Math.exp(-(t - at) / 0.1) * Math.sin(2 * Math.PI * 6 * (t - at)) : 0;
    return { visible: true, lift: 6 * (1 - easeIn(x)), roll: degrees(10) * (1 - x) + settle, dy: 0.6 * (1 - x) };
  }

  function pose(t) {
    kit.place(book, popUpUntil(t, T.book, T.bookAway, book));
    kit.place(power, dropIn(t, T.powerLands, { fall: 0.3, height: 10, roll: -5, bounce: 0.22 }));
    const pageTurning = t >= kit.foldAwayAt.get(kit.sheets[0]);
    dust.set({ origin: { x: 0, y: power.restY - 0.2, z: power.restZ - 0.3 }, width: power.width * 0.8, age: pageTurning ? 9 : t - T.powerLands });

    kit.place(homes, popUpUntil(t, T.homes, T.homesGone, homes));
    kit.place(queue, popUpUntil(t, T.queue, T.queueGone, queue));

    const walk = slideIn(t, T.workerWalks, { from: 5.2, stiffness: 4.2, damping: 0.95, tilt: 1.2 });
    kit.place(worker, walk.visible ? { ...walk, dy: walkBob(t, T.workerWalks, T.workerWalks + 1.4, 0.11, 2.4) } : walk);

    kit.place(workMore, slapOn(t, T.workMore, workMore));
    kit.place(consumeLess, slapOn(t, T.consumeLess, consumeLess));
  }

  return { pose };
}
