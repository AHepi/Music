// What this does: chapter 1, page 10, "Sound familiar?" (back in the parliament from page 1), and
// the ending. Source: Clara E. Mattei, The Capital Order (2022); the argument is said as hers.
//
// What happens, tied to Malina's words:
//   "That's the argument"       the politician from page 1 folds up again
//   "Austerity"                 AUSTERITY pops up again
//   "about the books"           an account book folds up beside him
//   "about power"               POWER crashes down; the account book is knocked flat
//   "Sound familiar?"           his paper jaw flaps silently, as if he is starting the speech again
//   "But wait."                 AUSTERITY and POWER fold away
//   "its own money"             a stack of banknotes folds up
//   "creating it ... inflation" a price tag folds up and is swapped for bigger and bigger ones;
//                               INFLATION? pops up
//   "That's next."              the politician folds away and the page corner lifts, teasing the
//                               next chapter; then the page turns over to a plain dark page

import { DustBurst } from '../../stage/paper-stage.js';
import { popUp, popUpUntil, foldDown, dropIn, slapFlat, spring, clamp01, degrees } from '../paper-kit.js';

export const SHEETS = ['parliament', 'blank'];

export async function build(kit) {
  const at = kit.at;
  const [parliament, blank] = kit.sheets;
  const politician = await kit.speaker('politician', { sheet: parliament, width: 7.6, x: 0, y: 0.0, z: 1.4, jawDropShare: 0.018 });
  const austerity = await kit.word(['AUSTERITY'], { sheet: parliament, size: 1.0, x: 0, y: 12.6, z: 0.55 });
  const ledger = await kit.piece('ledger', { sheet: parliament, width: 1.8, x: -3.0, y: 8.4, z: 1.9, yaw: degrees(8) });
  const power = await kit.word(['POWER'], { sheet: parliament, size: 1.25, x: 0, y: 10.3, z: 0.55 });
  const banknotes = await kit.piece('banknotes', { sheet: parliament, width: 2.6, x: -2.5, y: 10.0, z: 1.0 });
  const tags = [];
  for (const width of [1.2, 1.75, 2.4]) tags.push(await kit.piece('price-tag', { sheet: parliament, width, x: 2.5, y: 9.9, z: 1.0 }));
  const inflation = await kit.word(['INFLATION?'], { sheet: parliament, size: 1.0, x: 0, y: 12.9, z: 0.55 });
  const dust = kit.effect(new DustBurst({ count: 18, seed: 31 }));

  const T = {
    politician: at("That's", 1) - 0.18, politicianAway: at("That's", 2) - 0.12,
    austerity: at('Austerity') - 0.06,
    ledger: at('books') - 0.12,
    powerLands: at('power') + 0.03,
    flapFrom: kit.end('familiar') + 0.08, flapLength: 0.62,
    wordsAway: at('But') - 0.05,
    banknotes: at('money') - 0.18,
    tags: [at('creating') - 0.10, at('cause') - 0.02, at('inflation') + 0.18],
    inflation: at('inflation') - 0.05,
    cornerLifts: at("That's", 2) + 0.15,
    lastTurn: kit.lastWordEnd + 1.75, lastTurnLength: 1.2,
  };
  kit.shake(T.powerLands, 0.1, 0.15);

  // the page corner lifts a little on "That's next.", waits, then the page turns over
  const CORNER_LIFT = 0.34;
  const lastTurnCurve = (t) => {
    if (t < T.cornerLifts) return 0;
    if (t < T.lastTurn) return CORNER_LIFT * (1 - spring(t - T.cornerLifts, { stiffness: 9, damping: 0.6 }));
    return CORNER_LIFT + (1 - CORNER_LIFT) * clamp01((t - T.lastTurn) / T.lastTurnLength);
  };

  function pose(t) {
    kit.place(politician.piece, popUpUntil(t, T.politician, T.politicianAway, politician.piece));
    // a silent, mechanical flap of the jaw: three quick opens
    const flap = t > T.flapFrom && t < T.flapFrom + T.flapLength ? 0.85 * Math.max(0, Math.sin(2 * Math.PI * (3 / T.flapLength) * (t - T.flapFrom))) : 0;
    politician.setOpen(flap);

    kit.place(austerity, popUpUntil(t, T.austerity, T.wordsAway, austerity));
    kit.place(ledger, t < T.powerLands ? popUp(t, T.ledger, ledger) : foldDown(t, T.powerLands, 0.12));
    kit.place(power, t < T.wordsAway + 0.05 ? dropIn(t, T.powerLands, { fall: 0.3, height: 9, roll: 5, bounce: 0.2 }) : foldDown(t, T.wordsAway + 0.05, 0.2));
    dust.set({ origin: { x: 0, y: power.restY - 0.2, z: power.restZ - 0.3 }, width: power.width * 0.8, age: t > T.wordsAway ? 9 : t - T.powerLands });

    kit.place(banknotes, popUp(t, T.banknotes, banknotes));
    // the price tag grows: each one is swapped for a bigger one
    tags.forEach((tag, i) => {
      const next = T.tags[i + 1];
      kit.place(tag, next !== undefined ? popUpUntil(t, T.tags[i], next - 0.06, tag) : popUp(t, T.tags[i], tag));
    });
    kit.place(inflation, popUp(t, T.inflation, inflation));
  }

  return {
    pose,
    turns: [
      { sheet: parliament, from: T.lastTurn, length: T.lastTurnLength, curve: lastTurnCurve },
      { sheet: blank, from: Infinity, length: 1 },
    ],
  };
}
