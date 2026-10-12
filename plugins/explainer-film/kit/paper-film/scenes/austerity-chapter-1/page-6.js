// What this does: chapter 1, page 6, "The experts" (a grand 1920 conference hall). Source: Clara E.
// Mattei, The Capital Order (2022); facts from research entries C1-15 to C1-20.
//
// What happens, tied to Malina's words:
//   "the experts get together"   a row of delegates in dark suits folds up behind the long table
//   "Brussels, 1920"             BRUSSELS 1920 pops up
//   "Guess who isn't in the room?"  a worker walks up from the right
//   "Not one trade unionist"     a heavy door slams up in front of him; the camera shakes
//   "Genoa, 1922"                BRUSSELS 1920 folds away; GENOA 1922 pops up
//   "same advice"                the delegates nod (a small jump)
//   the advice: five printed cards drop onto the table one after another, each knocking the last
//   flat: BALANCE THE BUDGET, CUT SPENDING, NO NEW MONEY, RATES TO BANKS, BACK TO GOLD
//   "gold"                       a pile of gold bars crashes down; dust; the camera shakes

import { DustBurst } from '../../stage/paper-stage.js';
import { popUp, popUpUntil, foldDown, dropIn, hop, slideIn, walkBob, knock, degrees, addFold } from '../paper-kit.js';

export const SHEETS = ['conference-hall'];

const CARD_LOOK = { fontPx: 150, minWidth: 1250, aspect: 0.4 };

export async function build(kit) {
  const at = kit.at;
  const delegates = await kit.piece('delegates', { width: 9.2, x: 0, y: 4.0, z: 1.2 });
  const brussels = await kit.word(['BRUSSELS', '1920'], { size: 0.95, x: 0, y: 11.8, z: 0.55 });
  const genoa = await kit.word(['GENOA', '1922'], { size: 0.95, x: 0, y: 11.8, z: 0.55 });
  const worker = await kit.piece('worker-standing', { width: 1.55, x: 2.45, y: 0.45, z: 2.2 });
  const door = await kit.piece('door', { width: 2.95, x: 2.45, y: 0.4, z: 2.8 });
  const cardLines = [['BALANCE', 'THE BUDGET'], ['CUT', 'SPENDING'], ['NO NEW', 'MONEY'], ['RATES', 'TO BANKS'], ['BACK', 'TO GOLD']];
  const cards = [];
  for (const lines of cardLines) cards.push(await kit.card(lines, { look: CARD_LOOK, width: 5.4, x: -0.4, y: 1.3, z: 3.0 }));
  const gold = await kit.piece('gold-bars', { width: 3.4, x: 0.1, y: 3.0, z: 2.0 });
  const dust = kit.effect(new DustBurst({ count: 22, seed: 5 }));

  const T = {
    delegates: at('experts') - 0.16,
    brussels: at('Brussels') - 0.06,
    workerWalks: at('Guess') - 0.10,
    doorSlams: at('Not') - 0.02,
    brusselsAway: at('Genoa') - 0.25, doorAway: at('Genoa') - 0.45,
    genoa: at('Genoa') - 0.04,
    nod: at('same') + 0.02,
    cardsLand: [at('Balance'), at('Cut'), at('Stop'), at('Hand'), at('get', 2)].map((time) => time + 0.03),
    goldLands: at('gold') + 0.03,
  };
  kit.shake(T.doorSlams, 0.07, 0.12);
  for (const time of T.cardsLand) kit.shake(time, 0.035, 0.1);
  kit.shake(T.goldLands, 0.12, 0.16);

  function pose(t) {
    kit.place(delegates, { ...popUp(t, T.delegates, delegates), dy: hop(t, T.nod, 0.12) });
    kit.place(brussels, popUpUntil(t, T.brussels, T.brusselsAway, brussels));
    kit.place(genoa, popUp(t, T.genoa, genoa));

    // the worker walks up; the door slams in his face (it folds up fast in front of him)
    if (t < T.doorAway) {
      const walk = slideIn(t, T.workerWalks, { from: 6, stiffness: 6, damping: 0.9, tilt: 1.5 });
      const shut = t > T.doorSlams ? knock(t - T.doorSlams, degrees(-7), 3, 0.2) : 0;
      kit.place(worker, walk.visible ? { ...walk, dy: walkBob(t, T.workerWalks, T.workerWalks + 1.1, 0.12, 2.6), fold: shut } : walk);
    } else kit.place(worker, foldDown(t, T.doorAway, 0.2));
    if (t < T.doorAway) kit.place(door, popUp(t, T.doorSlams, door, { stiffness: 26, damping: 0.5 }));
    else kit.place(door, foldDown(t, T.doorAway + 0.04, 0.2));

    // the five cards: each drops onto the table and knocks the one before it flat
    cards.forEach((card, i) => {
      const lands = T.cardsLand[i];
      const next = T.cardsLand[i + 1];
      if (next !== undefined && t >= next) kit.place(card, foldDown(t, next, 0.1));
      else kit.place(card, dropIn(t, lands, { fall: 0.22, height: 9, roll: i % 2 ? 5 : -5, bounce: 0.14 }));
    });

    // the gold crashes down; the last card is jolted
    kit.place(gold, dropIn(t, T.goldLands, { fall: 0.3, height: 12, roll: 6, bounce: 0.25 }));
    const lastCard = cards[cards.length - 1];
    if (t > T.goldLands) kit.place(lastCard, addFold(dropIn(t, T.cardsLand[4], { fall: 0.22, height: 9, roll: -5, bounce: 0.14 }), knock(t - T.goldLands, degrees(6), 4, 0.18)));
    const pageTurning = t >= kit.foldAwayAt.get(kit.sheets[0]);
    dust.set({ origin: { x: gold.restX, y: gold.restY + 0.3, z: gold.restZ + 0.2 }, width: gold.width * 0.8, age: pageTurning ? 9 : t - T.goldLands });
  }

  return { pose };
}
