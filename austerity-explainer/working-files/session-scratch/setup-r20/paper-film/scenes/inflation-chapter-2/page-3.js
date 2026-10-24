// What this does: page 3 of chapter 2, "two factories" (the centre of the chapter). Two ivory card
// model factories stand on a table in front of a painted dusk skyline. The camera cranes down onto
// both, then visits each in turn:
//   - factory A (left) is idle; workers wait at its gate. New money (gold coins) rains into its yard,
//     the workers go in, its windows light up, smoke rises and shells come out one by one. Its price
//     counter stays at £1.00 ("Prices barely move").
//   - factory B (right) is already flat out. The same coins rain in, but its row of shells stays the
//     same; coins pile up beside its price counter as buyers bid, and the counter flips upward
//     ("prices climb").
//   - "Britain at war was close to the second factory... short of workers, materials and machines":
//     the camera settles on B and three painted cut-outs (a worker, materials, a lathe) pop up, each
//     with its word.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, foldDown, clamp01, smooth, ramp, lerp, degrees, spring } from '../cinema-kit.js';
import { CoinRain, DustBurst } from '../effects.js';
import { callout, hook, credit, INK } from '../graphics.js';
import { buildTwoFactories, FACTORY_A, FACTORY_B } from './two-factories-set.js';

export async function build(kit) {
  const set = await buildTwoFactories(kit);
  const { a, b } = set;
  const T = {
    start: kit.firstWordAt - 0.6,
    two: kit.at('factories'),
    first: kit.at('first'),
    idle: kit.at('idle'),
    workers: kit.at('workers'),
    gate: kit.at('gate'),
    money1: kit.at('money'),
    goIn: kit.at('go'),
    shells: kit.at('shells'),
    prices1: kit.at('prices'),
    barely: kit.at('barely'),
    second: kit.at('second'),
    flat: kit.at('flat'),
    money2: kit.at('money', 2),
    noMore: kit.at('no'),
    bid: kit.at('bid'),
    climb: kit.at('climb'),
    britain: kit.at('britain'),
    short: kit.at('short'),
    wordWorkers: kit.at('workers', 3),
    wordMaterials: kit.at('materials'),
    wordMachines: kit.at('machines', 2),
    end: kit.lastWordEnd,
  };

  // the queue of workers waiting at factory A's gate (a painted cut-out, side view, facing left)
  const queue = await kit.cutout('workers-queue', { at: [FACTORY_A.x + 1.05, 0, FACTORY_A.z + 1.2], width: 1.7, yaw: 0 });
  // new money: coins raining into each yard
  const coinsA = new CoinRain(kit.scene, { count: 22, centre: [a.yard.x, 0, a.yard.z], radius: 0.7, start: T.money1 + 0.05, spread: 0.9, coinRadius: 0.06, seed: 5 });
  const coinsB = new CoinRain(kit.scene, { count: 22, centre: [b.yard.x, 0, b.yard.z], radius: 0.7, start: T.money2 + 0.05, spread: 0.9, coinRadius: 0.06, seed: 8 });
  // buyers' bids: a stack of coins growing beside B's price counter
  const bids = new CoinRain(kit.scene, { count: 14, centre: [b.boardAt.x - 0.32, 0, b.boardAt.z + 0.25], height: 2.5, start: T.bid, spread: T.climb - T.bid + 0.6, coinRadius: 0.055, seed: 3, stack: true });
  const dust = new DustBurst(kit.scene, { count: 18, seed: 4 });

  // short of workers, materials and machines: three cut-outs and their words in front of B
  const shortOf = [
    { name: 'worker-standing', width: 0.42, x: FACTORY_B.x - 0.95, word: 'WORKERS', at: T.wordWorkers },
    { name: 'materials', width: 0.8, x: FACTORY_B.x + 0.05, word: 'MATERIALS', at: T.wordMaterials },
    { name: 'lathe', width: 0.8, x: FACTORY_B.x + 1.05, word: 'MACHINES', at: T.wordMachines },
  ];
  for (const item of shortOf) {
    item.piece = await kit.cutout(item.name, { at: [item.x, 0, FACTORY_B.z + 2.55], width: item.width });
    item.label = await kit.word(item.word, { at: [item.x, 0, FACTORY_B.z + 2.95], size: 0.12 });
  }

  // the camera: a crane down onto both factories, then to A, across to B, and back to settle on B
  // (close-ups are framed so each price board sits fully inside x 140..940 of the frame; while the
  // shells come out the camera pulls back so the shells and A's board share the picture)
  const shot = kit.shot([
    { t: T.start, position: [0.2, 8.5, 21], target: [0.1, 1.6, -3.0], fov: 40, focus: [0, 0.6, -1] },
    { t: T.two + 0.5, position: [0.5, 5.6, 14.5], target: [0.1, 1.2, -2.2], fov: 40, focus: [0, 0.6, -1] },
    { t: T.first + 1.5, position: [0.8, 3.9, 10.2], target: [-0.7, 0.75, 2.6], fov: 38, focus: [-1.0, 0.6, 3.2] },
    { t: T.money1, position: [0.8, 3.7, 9.9], target: [-0.8, 0.55, 2.9], fov: 38, focus: [a.yard.x, 0.1, a.yard.z] },
    { t: T.shells + 0.6, position: [0.1, 4.6, 14.2], target: [-1.2, 0.5, 3.2], fov: 38, focus: [-1.3, 0.3, 3.6] },
    { t: T.barely + 0.6, position: [0.4, 3.8, 12.6], target: [-0.9, 0.8, 3.4], fov: 36, focus: [a.boardAt.x, a.boardAt.y, a.boardAt.z] },
    { t: T.second + 1.0, position: [3.9, 4.85, 6.1], target: [1.95, 0.75, -3.8], fov: 38, focus: [1.8, 0.6, -3.0] },
    { t: T.money2, position: [3.85, 4.5, 5.6], target: [1.95, 0.55, -3.5], fov: 38, focus: [b.yard.x, 0.1, b.yard.z] },
    { t: T.noMore + 0.9, position: [3.85, 4.1, 4.9], target: [2.05, 0.6, -3.3], fov: 38, focus: [1.9, 0.3, -2.9] },
    { t: T.bid, position: [3.9, 2.6, 2.4], target: [2.6, 0.85, -2.9], fov: 36, focus: [b.boardAt.x, b.boardAt.y, b.boardAt.z] },
    { t: T.climb + 1.0, position: [3.8, 2.3, 1.8], target: [2.7, 0.95, -2.8], fov: 34, focus: [b.boardAt.x, b.boardAt.y, b.boardAt.z] },
    { t: T.britain + 0.8, position: [2.55, 5.0, 6.5], target: [1.95, 0.9, -3.6], fov: 38, focus: [1.8, 0.8, -3.4] },
    { t: T.end + 1.2, position: [2.05, 3.9, 8.4], target: [1.85, 0.5, -1.8], fov: 38, focus: [1.8, 0.3, -1.6] },
], { handheld: 0.015, seed: 3 });

  // the prices on each counter
  const priceA = [{ t: T.start - 1, text: '£1.00' }];
  const priceB = [{ t: T.start - 1, text: '£1.00' }, { t: T.climb - 0.2, text: '£1.25' }, { t: T.climb + 0.25, text: '£1.60' }, { t: T.climb + 0.7, text: '£2.00' }];
  kit.shake(T.money1 + 0.6, 0.02, 0.2);
  kit.shake(T.money2 + 0.6, 0.02, 0.2);

  function pose(t) {
    // factory A: idle until the workers go in; factory B: always running
    const runA = smooth(ramp(t, T.goIn + 0.3, T.goIn + 1.3));
    a.factory.setRunning(runA);
    b.factory.setRunning(1);
    a.smoke.set({ t, origin: a.chimney.toArray(), from: T.goIn + 0.6, scale: 0.9 });
    b.smoke.set({ t, origin: b.chimney.toArray(), scale: 0.9 });
    a.board.pose(t, priceA);
    b.board.pose(t, priceB);
    // A's shells: none at first, then one by one out of the door after "shells"
    a.shells.forEach((s, i) => {
      if (i >= set.shellsA) { s.group.visible = false; return; }
      const out = T.shells + 0.05 + i * 0.22;
      const k = clamp01((t - out) / 0.35);
      s.group.visible = t >= out;
      const home = a.shellAt(i);
      const from = new THREE.Vector3(FACTORY_A.x, 0, FACTORY_A.z + 1.1);
      s.group.position.lerpVectors(from, home, smooth(k));
      s.group.position.y = 0.12 * Math.sin(Math.PI * k);
    });
    // B's shells: a full row from the start; on "no more shells" one rocks but none are added
    b.shells.forEach((s, i) => {
      s.group.visible = i < set.shellsB;
      s.group.position.copy(b.shellAt(i));
      const age = t - T.noMore;
      s.group.rotation.z = i === set.shellsB - 1 && age > 0 ? 0.12 * Math.exp(-age * 3) * Math.sin(age * 18) : 0;
    });
    coinsA.pose(t);
    coinsB.pose(t);
    bids.pose(t);
    dust.set({ origin: [a.yard.x, 0.02, a.yard.z], width: 1.2, age: t - T.money1 - 0.55, scale: 0.3 });
    // the queue waits, then walks in through the door and folds away
    const walk = clamp01((t - T.goIn) / 1.1);
    if (t < T.workers - 0.15) queue.set({ visible: false });
    else if (walk < 1) {
      const up = popUp(t, T.workers - 0.15, { height: 0.9, restZ: 0.2 });
      queue.set({ fold: (up.fold ?? 0) + walk * walk * Math.PI / 2, dx: -0.9 * smooth(walk), dy: 0.03 * Math.abs(Math.sin(t * 9)) * (walk > 0 ? 1 : 0) });
    } else queue.set({ visible: false });
    // the three things Britain was short of
    for (const item of shortOf) {
      const up = popUp(t, item.at - 0.1, { height: 1, restZ: 0.25 });
      item.piece.set(up);
      item.label.set(popUp(t, item.at - 0.05, { height: 0.3, restZ: 0.1 }));
    }
    set.motes.set(t);
    return { camera: shot(t), look: { aperture: 9, maxBlur: 16, exposure: 0.92, glowThreshold: 0.95, glowStrength: 0.75, contrast: 1.08 } };
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    // labels sit on dark plates (the walls and roofs behind them are pale); board callouts point at
    // the board's top rim, not through its digits
    const rim = (board) => at(board.clone().setY(1.27));
    const label = { plate: true, size: 52, margin: 140 };
    callout(ctx, t, { ...label, at: T.idle, until: T.goIn + 0.2, point: at([FACTORY_A.x + 0.35, 0.95, FACTORY_A.z + 1.05]), text: 'IDLE', dx: 60, dy: -300 });   // a window that stays in frame
    callout(ctx, t, { ...label, at: T.shells + 0.1, until: T.barely - 0.1, point: at(a.shellAt(2).setY(0.3)), text: 'MORE SHELLS', dx: 60, dy: -300 });
    callout(ctx, t, { ...label, at: T.barely, until: T.second - 0.2, point: rim(a.boardAt), text: 'BARELY MOVE', dx: -60, dy: -260 });
    callout(ctx, t, { ...label, at: T.flat, until: T.money2 - 0.1, point: at([FACTORY_B.x - 0.8, 0.95, FACTORY_B.z + 1.05]), text: 'FLAT OUT', dx: 100, dy: -260 });
    callout(ctx, t, { ...label, at: T.noMore + 0.1, until: T.bid - 0.1, point: at(b.shellAt(6).setY(0.3)), text: 'NO MORE SHELLS', dx: -60, dy: -300 });
    callout(ctx, t, { ...label, at: T.climb, until: T.britain - 0.1, point: rim(b.boardAt.clone().setX(b.boardAt.x + 0.3)), text: 'PRICES CLIMB', dx: -140, dy: -260, accent: INK.red });
    hook(ctx, t, { at: T.britain, until: T.short - 0.2, lines: ['BRITAIN', 'AT WAR'], x: 470, y: 290, size: 92 });   // clear of factory B's chimney
    hook(ctx, t, { at: T.short, until: T.end + 1.2, text: 'SHORT OF', x: 470, y: 290, size: 80 });
    credit(ctx, t, { at: T.first, until: T.britain, text: 'Example prices', y: 1460, size: 28 });
    return true;
  }

  return { pose, draw2D };
}
