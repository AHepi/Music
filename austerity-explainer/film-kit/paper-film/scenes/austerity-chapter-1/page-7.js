// What this does: chapter 1, page 7, "The plan has three parts" (a town street). Source: Clara E.
// Mattei, The Capital Order (2022); the three parts are her summary (research entry C1-21).
//
// Three dark boards fold up one above the other, one for each part, each with its word:
//   SPENDING  "cut public services"        a school folds up, then is cut away
//             "tax everyday purchases"     a basket of food folds up; a TAX tag drops onto it
//             "instead of wealth"          a money bag folds up, untouched
//   MONEY     "make borrowing expensive"   a bank folds up; a padlock crashes onto its door
//             "businesses slow down"       a small factory folds up, smoking; the smoke stops
//             "jobs disappear"             a worker folds up, then folds away
//   WORK      "cut wages"                  a pay packet folds up and is swapped for a smaller one
//             "sell off what the public owns"  a railway engine folds up; a SOLD sign slaps onto it
//             "weaken the unions"          a union banner folds up, then topples

import { Smoke } from '../../stage/paper-stage.js';
import { popUp, popUpUntil, foldDown, dropIn, degrees, clamp01, easeIn } from '../paper-kit.js';

export const SHEETS = ['town-street'];

const BOARD_LOOK = { fontPx: 150, cardColour: '#24323b', borderColour: 'rgba(232,224,204,0.32)', minWidth: 1200, aspect: 0.5 };

export async function build(kit) {
  const at = kit.at;
  const rows = { spending: 10.9, money: 6.2, work: 1.5 };   // where each board's bottom edge sits
  const board = async (y) => kit.card([], { look: BOARD_LOOK, width: 8.6, x: 0, y, z: 0.35 });
  const boards = { spending: await board(rows.spending), money: await board(rows.money), work: await board(rows.work) };
  const label = async (text, y) => kit.word([text], { size: 0.62, x: 0, y: y + 3.25, z: 0.55 });
  const labels = { spending: await label('SPENDING', rows.spending), money: await label('MONEY', rows.money), work: await label('WORK', rows.work) };
  const on = (row, lift = 0.25) => rows[row] + lift;

  const school = await kit.piece('school', { width: 2.3, x: -2.75, y: on('spending'), z: 0.9 });
  const basket = await kit.piece('basket', { width: 2.1, x: 0.1, y: on('spending'), z: 0.9 });
  const taxTag = await kit.piece('tax-tag', { width: 1.35, x: 0.85, y: on('spending', 1.15), z: 1.35, yaw: degrees(-4) });
  const moneyBag = await kit.piece('money-bag', { width: 2.0, x: 2.8, y: on('spending'), z: 0.9 });

  const bank = await kit.piece('bank', { width: 2.4, x: -2.75, y: on('money'), z: 0.9 });
  const padlock = await kit.piece('padlock', { width: 0.85, x: -2.75, y: on('money', 0.35), z: 1.35 });
  const factory = await kit.piece('factory-small', { width: 2.7, x: 0.1, y: on('money'), z: 0.9 });
  const smoke = kit.effect(new Smoke({ count: 8, life: 2.0, seed: 9 }));
  const worker = await kit.piece('worker-standing', { width: 0.95, x: 2.85, y: on('money'), z: 0.9 });

  const payBig = await kit.piece('pay-packet', { width: 2.2, x: -2.8, y: on('work'), z: 0.9 });
  const paySmall = await kit.piece('pay-packet', { width: 1.15, x: -2.8, y: on('work'), z: 0.9 });
  const engine = await kit.piece('locomotive', { width: 3.2, x: 0.3, y: on('work', 0.4), z: 0.9 });
  const sold = await kit.card(['SOLD'], { look: { fontPx: 150, inkColour: '#6e1d18', borderColour: 'rgba(110,29,24,0.6)' }, width: 1.45, x: 0.55, y: on('work', 1.05), z: 1.35 });
  const banner = await kit.piece('banner', { width: 2.1, x: 2.85, y: on('work'), z: 0.9 });

  const T = {
    spending: at('Spending') - 0.22,
    school: at('cut', 1) - 0.14, schoolCut: kit.end('services') + 0.05,
    basket: at('tax') - 0.14, taxTagLands: at('purchases') + 0.05,
    moneyBag: at('wealth') - 0.14,
    money: at('Money') - 0.22,
    bank: at('make') - 0.10, padlockLands: at('expensive') + 0.08,
    factory: at('businesses') - 0.14, smokeStops: at('down') - 0.1,
    worker: at('jobs') - 0.14, workerGone: at('disappear') + 0.2,
    work: at('Work') - 0.22,
    payBig: at('cut', 2) - 0.14, paySwap: at('wages') + 0.22,
    engine: at('sell') - 0.12, soldLands: at('owns') + 0.04,
    banner: at('weaken') - 0.12, bannerFalls: at('unions') + 0.25,
  };
  kit.shake(T.padlockLands, 0.03, 0.1);
  kit.shake(T.soldLands, 0.03, 0.1);

  function pose(t) {
    for (const row of ['spending', 'money', 'work']) {
      kit.place(boards[row], popUp(t, T[row], boards[row], { stiffness: 14, damping: 0.8 }));
      kit.place(labels[row], popUp(t, T[row] + 0.12, labels[row]));
    }

    kit.place(school, popUpUntil(t, T.school, T.schoolCut, school));
    kit.place(basket, popUp(t, T.basket, basket));
    kit.place(taxTag, dropIn(t, T.taxTagLands, { fall: 0.2, height: 4, roll: -10, bounce: 0.1 }));
    kit.place(moneyBag, popUp(t, T.moneyBag, moneyBag));

    kit.place(bank, popUp(t, T.bank, bank));
    kit.place(padlock, dropIn(t, T.padlockLands, { fall: 0.22, height: 5, roll: 6, bounce: 0.12 }));
    kit.place(factory, popUp(t, T.factory, factory));
    const chimney = { x: factory.restX - factory.width / 2 + factory.width * 0.765, y: factory.restY + factory.height * 0.97, z: factory.restZ + 0.05 };
    const smokeOn = t > T.factory + 0.25 && t < kit.foldAwayAt.get(kit.sheets[0]);
    smoke.set({ t, origin: chimney, from: smokeOn ? T.factory + 0.25 : 1e9, until: T.smokeStops, scale: 0.55 });
    kit.place(worker, popUpUntil(t, T.worker, T.workerGone, worker));

    // the pay packet is swapped for a smaller one: the big one folds down as the small one folds up
    kit.place(payBig, popUpUntil(t, T.payBig, T.paySwap, payBig));
    kit.place(paySmall, popUp(t, T.paySwap + 0.1, paySmall));
    kit.place(engine, popUp(t, T.engine, engine));
    kit.place(sold, dropIn(t, T.soldLands, { fall: 0.18, height: 3.5, roll: -12, bounce: 0.1 }));
    // the banner topples over toward the camera, speeding up, and is gone
    if (t < T.bannerFalls) kit.place(banner, popUp(t, T.banner, banner));
    else {
      const x = clamp01((t - T.bannerFalls) / 0.35);
      kit.place(banner, x >= 1 ? { visible: false } : { visible: true, fold: (Math.PI / 2) * easeIn(x), roll: degrees(10) * easeIn(x) });
    }
  }

  return { pose };
}
