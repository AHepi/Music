// What this does: chapter 1, page 2, "The war" (a 1915 shell factory). Source: Clara E. Mattei,
// The Capital Order (2022); facts from research entries C1-04 and C1-05.
//
// What happens, tied to Malina's words:
//   "Picture Britain in 1915"         women munition workers fold up; 1915 pops up
//   "shells"                          a row of artillery shells folds up, one after another
//   "the government"                  a full money bag folds up, and stays put ("doesn't run out of money")
//   "runs out of shells"              the shells fold away one by one; OUT OF SHELLS pops up
//   "takes charge"                    an official rubber stamp crashes down
//   "what factories make / what things cost / what workers are paid"
//                                     a factory, a price tag and a pay packet fold up in turn, and the
//                                     stamp crashes onto each
//   "Italy does the same"             a map of Italy folds up; the stamp crashes onto it
//   "people notice"                   the women jump
//   "organised for war"               the shells come back
//   "why not for what people need"    the shells go; a basket of food, homes and a school fold up;
//                                     WHY NOT FOR PEOPLE? pops up

import { popUp, popUpUntil, foldDown, hop, knock, degrees, easeIn, clamp01, addFold } from '../paper-kit.js';

export const SHEETS = ['munitions-factory'];

export async function build(kit) {
  const at = kit.at;
  const women = await kit.piece('munition-women', { width: 9.4, x: 0, y: -0.3, z: 2.2 });
  const year = await kit.word(['1915'], { size: 1.1, x: 0, y: 12.6, z: 0.55 });
  const shells = [];
  for (let i = 0; i < 7; i++) shells.push(await kit.piece(`shell-${i + 1}`, { width: 0.72, x: -3.0 + i, y: 6.0, z: 1.0 }));
  const moneyBag = await kit.piece('money-bag', { width: 2.4, x: 2.7, y: 9.0, z: 1.3 });
  const outOfShells = await kit.word(['OUT OF SHELLS'], { size: 0.9, x: 0, y: 12.6, z: 0.55 });
  const factory = await kit.piece('factory-small', { width: 2.9, x: -2.75, y: 6.2, z: 1.0 });
  const priceTag = await kit.piece('price-tag', { width: 2.3, x: 0, y: 6.2, z: 1.0 });
  const payPacket = await kit.piece('pay-packet', { width: 2.5, x: 2.75, y: 6.2, z: 1.0 });
  const italy = await kit.piece('italy-map', { width: 3.0, x: 0, y: 6.6, z: 1.0 });
  const stamp = await kit.piece('rubber-stamp', { width: 1.7, x: 0, y: 6.4, z: 1.6 });
  const basket = await kit.piece('basket', { width: 2.6, x: -2.75, y: 6.0, z: 1.0 });
  const homes = await kit.piece('council-houses', { width: 3.0, x: 0.05, y: 6.1, z: 1.0 });
  const school = await kit.piece('school', { width: 2.6, x: 2.8, y: 6.0, z: 1.0 });
  const whyNot = await kit.word(['WHY NOT', 'FOR PEOPLE?'], { size: 0.9, x: 0, y: 11.6, z: 0.55 });

  const T = {
    women: at('Picture') - 0.15,
    year: at('1915') - 0.06, yearAway: at('shells', 2) - 0.45,
    shellsIn: at('shells', 1) - 0.12,
    moneyBag: at('government') - 0.10, moneyHop: at('money') + 0.05,
    shellsOut: at('runs') - 0.05,
    outOfShells: at('shells', 2) - 0.06,
    clearAway: at('So') - 0.30,
    factory: at('factories', 2) - 0.20, priceTag: at('things') - 0.20, payPacket: at('workers') - 0.20,
    italy: at('Italy') - 0.12, italyAway: at('If') - 0.25,
    notice: at('notice') + 0.02,
    shellsBack: at('war', 2) - 0.32, shellsGo: at('why') - 0.12,
    basket: at('what', 4) - 0.10, homes: at('people', 2) - 0.10, school: at('need') - 0.10,
    whyNot: at('why') - 0.04,
  };
  // the stamp crashes four times: on "charge" (nothing under it yet), then on the factory, the price
  // tag and the pay packet as each is named, then on Italy on "same"
  const stampHits = [
    { at: at('charge') + 0.05, x: 0, y: 6.4 },
    { at: at('factories', 2) + 0.22, x: -2.75, y: 6.2 + factory.height - 0.35 },
    { at: at('things') + 0.30, x: 0, y: 6.2 + priceTag.height - 0.45 },
    { at: at('paid') + 0.02, x: 2.75, y: 6.2 + payPacket.height - 0.3 },
    { at: at('same') + 0.05, x: 0, y: 6.6 + italy.height - 0.5 },
  ];
  for (const hit of stampHits) kit.shake(hit.at, 0.045, 0.1);

  function stampPose(t) {
    const FALL = 0.2, HOLD = 0.18, LIFT = 0.25, HIGH = 10;
    for (const hit of stampHits) {
      const from = hit.at - FALL, to = hit.at + HOLD + LIFT;
      if (t < from || t > to) continue;
      let dy;
      if (t < hit.at) dy = HIGH * (1 - easeIn((t - from) / FALL));
      else if (t < hit.at + HOLD) dy = 0.12 * Math.exp(-(t - hit.at) / 0.05) * Math.abs(Math.sin(Math.PI * (t - hit.at) / 0.08));
      else dy = HIGH * easeIn((t - hit.at - HOLD) / LIFT);
      return { visible: true, dx: hit.x - stamp.restX, dy: hit.y - stamp.restY + dy, roll: degrees(-4) * clamp01((hit.at - t) / FALL) };
    }
    return { visible: false };
  }
  // what the stamp is hitting jolts
  const jolt = (t, hitIndex) => knock(t - stampHits[hitIndex].at, degrees(6), 4, 0.15);

  function pose(t) {
    // the women jump when "people notice", leaning back a little as they land
    const leanBack = t > T.notice ? degrees(4) * Math.exp(-(t - T.notice) / 0.3) : 0;
    kit.place(women, addFold({ ...popUp(t, T.women, women), dy: hop(t, T.notice, 0.3) }, -leanBack));
    kit.place(year, popUpUntil(t, T.year, T.yearAway, year));

    // the shells: made one after another, then used up one by one, then back for "organised for war"
    shells.forEach((shell, i) => {
      let p;
      if (t < T.shellsOut + 0.6) p = popUpUntil(t, T.shellsIn + i * 0.12, T.shellsOut + i * 0.08, shell);
      else if (t < T.shellsGo) p = popUp(t, T.shellsBack + i * 0.05, shell);
      else p = foldDown(t, T.shellsGo + i * 0.03, 0.18);
      kit.place(shell, p);
    });
    kit.place(moneyBag, { ...popUpUntil(t, T.moneyBag, T.clearAway, moneyBag), dy: hop(t, T.moneyHop, 0.14) });
    kit.place(outOfShells, popUpUntil(t, T.outOfShells, T.clearAway + 0.05, outOfShells));

    // the government takes charge
    const away = T.italy - 0.25;
    kit.place(factory, addFold(popUpUntil(t, T.factory, away, factory), jolt(t, 1)));
    kit.place(priceTag, addFold(popUpUntil(t, T.priceTag, away + 0.04, priceTag), jolt(t, 2)));
    kit.place(payPacket, addFold(popUpUntil(t, T.payPacket, away + 0.08, payPacket), jolt(t, 3)));
    kit.place(italy, addFold(popUpUntil(t, T.italy, T.italyAway, italy), jolt(t, 4)));
    kit.place(stamp, stampPose(t));

    // what people need
    kit.place(basket, popUp(t, T.basket, basket));
    kit.place(homes, popUp(t, T.homes, homes));
    kit.place(school, popUp(t, T.school, school));
    kit.place(whyNot, popUp(t, T.whyNot, whyNot));
  }

  return { pose };
}
