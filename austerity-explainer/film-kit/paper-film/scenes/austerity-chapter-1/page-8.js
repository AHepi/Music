// What this does: chapter 1, page 8, "The official story" (a family kitchen, then the shell factory
// again). Source: Clara E. Mattei, The Capital Order (2022); facts from research entries C1-22 to
// C1-26. The money view is said as "economists who study how modern money works".
//
// What happens, tied to Malina's words:
//   kitchen sheet
//     "Prices are rising"            a price tag folds up and rises
//     "war debts are huge"           a thick stack of banknotes folds up
//     "a government, like a household"  a kitchen table with an account book folds up;
//                                    LIKE A HOUSEHOLD? pops up
//     "balance its books"            the table rocks from side to side
//     "issues its own money"         the banknotes jump
//     "isn't a household"            the table is slapped flat; NOT A HOUSEHOLD replaces the question
//     "its own money"                the banknotes jump again
//   the kitchen sheet turns over, uncovering the shell factory from page 2
//     "workers, materials and machines"  the women workers, steel and timber, and a lathe fold up
//     "as the war just showed"       the shells from page 2 drop back in
//     "And gold?"                    a pile of gold bars folds up
//     "a limit they chose"           a padlock crashes onto the gold
//     "forcing wages and prices down"  a pay packet and a price tag fold up; the gold rises and
//                                    slams down on them, flattening them; dust; the camera shakes

import { DustBurst } from '../../stage/paper-stage.js';
import { popUp, popUpUntil, foldDown, dropIn, slapFlat, hop, rock, degrees, clamp01, easeIn, easeInOut } from '../paper-kit.js';

export const SHEETS = ['kitchen', 'munitions-factory'];

export async function build(kit) {
  const at = kit.at;
  const [kitchen, factory] = kit.sheets;

  const priceTag = await kit.piece('price-tag', { sheet: kitchen, width: 2.0, x: 2.6, y: 9.3, z: 1.0 });
  const banknotes = await kit.piece('banknotes', { sheet: kitchen, width: 2.8, x: -2.5, y: 9.6, z: 1.0 });
  const table = await kit.piece('kitchen-table', { sheet: kitchen, width: 6.4, x: 0, y: 1.2, z: 1.8 });
  const likeHousehold = await kit.word(['LIKE A', 'HOUSEHOLD?'], { sheet: kitchen, size: 0.9, x: 0, y: 12.0, z: 0.55 });
  const notHousehold = await kit.word(['NOT A', 'HOUSEHOLD'], { sheet: kitchen, size: 0.9, x: 0, y: 12.0, z: 0.55 });

  const women = await kit.piece('munition-women', { sheet: factory, width: 9.4, x: 0, y: -0.3, z: 2.2 });
  const materials = await kit.piece('materials', { sheet: factory, width: 3.6, x: -2.3, y: 6.6, z: 1.0 });
  const lathe = await kit.piece('lathe', { sheet: factory, width: 3.4, x: 2.3, y: 6.6, z: 1.0 });
  const shells = [];
  for (let i = 0; i < 7; i++) shells.push(await kit.piece(`shell-${i + 1}`, { sheet: factory, width: 0.66, x: -3.0 + i, y: 10.0, z: 0.8 }));
  const gold = await kit.piece('gold-bars', { sheet: factory, width: 4.0, x: 0, y: 6.3, z: 1.4 });
  const padlock = await kit.piece('padlock', { sheet: factory, width: 1.45, x: 0.1, y: 6.3 + 1.35, z: 1.9 });
  const payPacket = await kit.piece('pay-packet', { sheet: factory, width: 2.2, x: -1.9, y: 1.3, z: 2.3 });
  const priceTag2 = await kit.piece('price-tag', { sheet: factory, width: 2.0, x: 1.9, y: 1.3, z: 2.3 });
  const dust = kit.effect(new DustBurst({ count: 26, seed: 17 }));

  const T = {
    priceTag: at('Prices') - 0.12, priceRises: at('rising') + 0.02,
    banknotes: at('debts') - 0.12,
    table: at('government') - 0.10,
    likeHousehold: at('household', 1) - 0.05,
    balanceFrom: at('balance') - 0.05, balanceTo: kit.end('books') + 0.3,
    issuesHop: at('issues') + 0.02,
    slap: at('household', 2) + 0.04,
    ownMoneyHop: at('money', 3) + 0.02,
    kitchenTurns: kit.end('money', 3) + 0.14,
    women: at('workers') - 0.12, materials: at('materials') - 0.12, lathe: at('machines') - 0.12,
    shellsLand: at('showed') - 0.15,
    clearFactory: at('And', 3) - 0.3,
    gold: at('gold', 1) - 0.12,
    padlockLands: at('chose') + 0.04,
    payPacket: at('wages') - 0.12, priceTag2: at('prices', 2) - 0.12,
    goldRises: at('forcing') - 0.05, slam: at('down') + 0.03,
  };
  kit.shake(T.slap, 0.06, 0.12);
  for (let i = 0; i < 7; i++) kit.shake(T.shellsLand + i * 0.06, 0.012, 0.08);
  kit.shake(T.padlockLands, 0.06, 0.12);
  kit.shake(T.slam, 0.14, 0.17);

  function pose(t) {
    // ---------------------------------------------------------------- kitchen
    const rise = t > T.priceRises ? 0.7 * easeInOut(clamp01((t - T.priceRises) / 0.6)) : 0;
    const tag = popUp(t, T.priceTag, priceTag);
    kit.place(priceTag, tag.visible ? { ...tag, dy: rise } : tag);
    const notes = popUp(t, T.banknotes, banknotes);
    kit.place(banknotes, notes.visible ? { ...notes, dy: hop(t, T.issuesHop, 0.2) + hop(t, T.ownMoneyHop, 0.2) } : notes);
    if (t < T.slap) {
      const up = popUp(t, T.table, table);
      kit.place(table, up.visible ? { ...up, roll: rock(t, T.balanceFrom, T.balanceTo, degrees(3.5), 1.8) } : up);
    } else kit.place(table, foldDown(t, T.slap, 0.12));
    kit.place(likeHousehold, popUpUntil(t, T.likeHousehold, T.slap - 0.12, likeHousehold));
    kit.place(notHousehold, popUp(t, T.slap + 0.06, notHousehold));

    // ---------------------------------------------------------------- the factory again
    const away = (i) => T.clearFactory + i * 0.05;
    kit.place(women, popUpUntil(t, T.women, away(0), women));
    kit.place(materials, popUpUntil(t, T.materials, away(1), materials));
    kit.place(lathe, popUpUntil(t, T.lathe, away(2), lathe));
    shells.forEach((shell, i) => {
      const lands = T.shellsLand + i * 0.06;
      kit.place(shell, t < away(3) ? dropIn(t, lands, { fall: 0.24, height: 8, roll: i % 2 ? 6 : -6, bounce: 0.12 }) : foldDown(t, away(3) + i * 0.02, 0.18));
    });

    // the gold: up on "gold", locked on "chose", then lifted and slammed down on wages and prices
    let lift = { dy: 0, lift: 0 };
    if (t > T.goldRises && t < T.slam - 0.22) {
      const x = easeInOut(clamp01((t - T.goldRises) / 0.8));
      lift = { dy: 3.2 * x, lift: 1.3 * x };
    } else if (t >= T.slam - 0.22 && t < T.slam) {
      const x = easeIn((t - (T.slam - 0.22)) / 0.22);
      lift = { dy: 3.2 + (payPacket.restY - gold.restY - 3.2) * x, lift: 1.3 };
    } else if (t >= T.slam) {
      const age = t - T.slam;
      lift = { dy: payPacket.restY - gold.restY + 0.25 * Math.exp(-age / 0.08) * Math.abs(Math.sin(Math.PI * age / 0.12)), lift: 1.3 };
    }
    const goldUp = popUp(t, T.gold, gold);
    kit.place(gold, goldUp.visible ? { ...goldUp, ...lift } : goldUp);
    const lockPose = dropIn(t, T.padlockLands, { fall: 0.25, height: 9, roll: 7, bounce: 0.18 });
    kit.place(padlock, lockPose.visible ? { ...lockPose, dy: lockPose.dy + lift.dy, lift: lift.lift } : lockPose);
    kit.place(payPacket, t < T.slam ? popUp(t, T.payPacket, payPacket) : foldDown(t, T.slam, 0.08));
    kit.place(priceTag2, t < T.slam ? popUp(t, T.priceTag2, priceTag2) : foldDown(t, T.slam, 0.08));
    const pageTurning = t >= kit.foldAwayAt.get(factory);
    dust.set({ origin: { x: gold.restX, y: payPacket.restY + 0.3, z: gold.restZ + 1.5 }, width: gold.width * 0.9, age: pageTurning ? 9 : t - T.slam });
  }

  return { pose, turns: [{ sheet: kitchen, from: T.kitchenTurns, length: 0.75 }] };
}
