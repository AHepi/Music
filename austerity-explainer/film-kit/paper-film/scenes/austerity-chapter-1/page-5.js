// What this does: chapter 1, page 5, "The capital order" (a company boardroom). Source: Clara E.
// Mattei, The Capital Order (2022); "the capital order" is Mattei's term (research entry C1-14).
//
// What happens, tied to Malina's words:
//   "the owners' side"        three factory owners in top hats fold up
//   "the capital order"       THE CAPITAL ORDER pops up
//   "a few people own"        the owners jump
//   "land / factories / mines"  a farm, a factory and a pithead fold up in front of them, in turn
//   "work for a wage"         a long queue of workers slides in along the bottom
//   "run things themselves"   the queue jumps
//   "that order could fall"   THE CAPITAL ORDER rocks, then topples flat; the owners rock nervously

import { popUp, hop, rock, slideIn, degrees, clamp01, easeIn } from '../paper-kit.js';

export const SHEETS = ['boardroom'];

export async function build(kit) {
  const at = kit.at;
  const owners = await kit.piece('owners', { width: 7.8, x: 0, y: 6.8, z: 1.0 });
  const capitalOrder = await kit.word(['THE CAPITAL', 'ORDER'], { size: 0.95, x: 0, y: 12.4, z: 0.55 });
  const farm = await kit.piece('farmland', { width: 2.9, x: -2.7, y: 4.0, z: 1.6 });
  const factory = await kit.piece('factory-small', { width: 3.0, x: 0, y: 4.1, z: 1.6 });
  const mine = await kit.piece('mine-small', { width: 2.3, x: 2.8, y: 4.0, z: 1.6 });
  const queue = await kit.piece('workers-queue', { width: 10.2, x: 0, y: -0.4, z: 2.4 });

  const T = {
    owners: at("owners'") - 0.16,
    capitalOrder: at('capital') - 0.06,
    ownersHop: at('own') + 0.02,
    farm: at('land') - 0.10, factory: at('factories') - 0.10, mine: at('mines') - 0.10,
    queue: at('work') - 0.35,
    queueHop: at('run') + 0.02, queueHop2: at('themselves') + 0.05,
    rockFrom: at('order', 2) - 0.05, fall: at('fall') + 0.02,
  };

  function pose(t) {
    const nervous = rock(t, T.rockFrom, T.fall + 0.9, degrees(2.5), 2.6);
    const ownersPose = popUp(t, T.owners, owners);
    kit.place(owners, ownersPose.visible ? { ...ownersPose, dy: hop(t, T.ownersHop, 0.16), roll: nervous } : ownersPose);

    // THE CAPITAL ORDER rocks harder and harder, then topples over and is gone
    if (t < T.fall) {
      const words = popUp(t, T.capitalOrder, capitalOrder);
      const shaking = t > T.rockFrom ? degrees(5) * clamp01((t - T.rockFrom) / (T.fall - T.rockFrom)) * Math.sin(2 * Math.PI * 3.2 * (t - T.rockFrom)) : 0;
      kit.place(capitalOrder, words.visible ? { ...words, roll: shaking } : words);
    } else {
      const x = clamp01((t - T.fall) / 0.38);
      kit.place(capitalOrder, x >= 1 ? { visible: false } : { visible: true, fold: (Math.PI / 2) * easeIn(x), roll: degrees(-9) * easeIn(x), dy: -0.4 * easeIn(x) });
    }

    kit.place(farm, popUp(t, T.farm, farm));
    kit.place(factory, popUp(t, T.factory, factory));
    kit.place(mine, popUp(t, T.mine, mine));

    const slid = slideIn(t, T.queue, { from: 12, stiffness: 7, damping: 0.85, tilt: 2 });
    kit.place(queue, slid.visible ? { ...slid, dy: hop(t, T.queueHop, 0.2) + hop(t, T.queueHop2, 0.16) } : slid);
  }

  return { pose };
}
