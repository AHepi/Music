// What this does: chapter 1, page 3, "Britain after the war" (the approved paper test, now part of
// the whole chapter). Source: Clara E. Mattei, The Capital Order (2022); facts from research
// entries C1-08 to C1-11.
//
// What happens, tied to Malina's words:
//   Glasgow square sheet
//     "workers"            a crowd folds up from flat
//     "doubles"            a second, bigger crowd folds up in front: the crowd doubles
//     "eight million"      8 MILLION pops up in the sky
//     "sixty thousand"     8 MILLION folds away; 60,000 pops up
//     "demanding ... week" the crowd bobs, cheering
//     "troops"             a line of soldiers slides in behind the crowd
//     "tanks"              a First World War tank drops in from above and lands hard: the camera
//                          shakes, dust bursts out, the crowd jolts, 60,000 is knocked flat
//                          (a symbol of power: the research says troops and tanks came after the clash)
//   the pieces fold down flat, then the sheet peels away from its bottom-right corner
//   Pithead sheet
//     "demand"             a miner folds up; his paper jaw moves with Malina's voice
//     "public ownership"   PUBLIC OWNERSHIP pops up
//     "royal commission"   the commission's report folds up beside him
//     "ignores it"         PUBLIC OWNERSHIP folds away, IGNORED pops up, the report is slapped flat

import { DustBurst } from '../../stage/paper-stage.js';
import { popUp, foldDown, spring, knock, degrees, clamp01, loadMouthTrack } from '../paper-kit.js';

export const SHEETS = ['glasgow-square', 'pithead'];

export async function build(kit) {
  const at = kit.at;
  const [glasgow, pithead] = kit.sheets;
  const mouthOpen = await loadMouthTrack('/paper-film/scene-data/chapter-1-page-3-mouth.json');

  // Glasgow sheet
  const soldiers = await kit.piece('soldiers', { sheet: glasgow, width: 8.4, x: -0.3, y: 5.0, z: 0.7 });
  const crowdBack = await kit.piece('crowd-back', { sheet: glasgow, width: 10.8, x: 0, y: 1.6, z: 1.25 });
  const tank = await kit.piece('tank', { sheet: glasgow, width: 7.2, x: 0.7, y: 3.5, z: 1.95 });
  const crowdFront = await kit.piece('crowd-front', { sheet: glasgow, width: 11.2, x: 0, y: -1.4, z: 2.7 });
  const eightMillion = await kit.word(['8 MILLION'], { sheet: glasgow, width: 6.3, x: 0, y: 11.3, z: 0.55 });
  const sixtyThousand = await kit.word(['60,000'], { sheet: glasgow, width: 5.2, x: 0, y: 11.3, z: 0.55 });
  const dust = kit.effect(new DustBurst({ count: 28, seed: 11 }));

  // pithead sheet
  const miner = await kit.speaker('miner', { sheet: pithead, width: 7.6, x: 0, y: -1.4, z: 1.6, jawDropShare: 0.022 });
  const report = await kit.piece('report', { sheet: pithead, width: 3.1, x: -2.45, y: 0.3, z: 2.6, yaw: degrees(6) });
  const publicOwnership = await kit.word(['PUBLIC', 'OWNERSHIP'], { sheet: pithead, width: 6.1, x: 0, y: 10.8, z: 0.55 });
  const ignored = await kit.word(['IGNORED'], { sheet: pithead, width: 5.7, x: 0, y: 11.5, z: 0.55 });

  const T = {
    crowdBack: at('workers') - 0.12,
    crowdFront: at('doubles') - 0.10,
    eightMillion: at('eight') - 0.08,
    eightMillionAway: at('sixty') - 0.24,
    sixtyThousand: at('sixty') - 0.04,
    cheerFrom: at('demanding') - 0.05, cheerTo: kit.end('week') + 0.1,
    soldiers: at('troops') - 0.22,
    tankLands: at('tanks') + 0.02,
    tankFall: 0.36,
    glasgowFoldsAway: at('tanks') + 0.48,
    turnFrom: at('tanks') + 0.74, turnLength: 0.82,
    miner: at('demand') - 0.22,
    mouthFrom: at('demand') - 0.02, mouthTo: kit.end('mines') + 0.05,
    publicOwnership: at('public') - 0.08,
    report: at('royal') - 0.10,
    publicOwnershipAway: at('ignores') - 0.16,
    ignored: at('ignores') - 0.03,
    reportSlapped: at('ignores') + 0.06,
  };
  kit.shake(T.tankLands, 0.13, 0.17);
  kit.shake(T.reportSlapped, 0.04, 0.12);

  function pose(t) {
    const age = t - T.tankLands;
    // ------------------------------------------------------------------- Glasgow
    const cheering = t > T.cheerFrom && t < T.cheerTo;
    const cheerEnvelope = cheering ? Math.sin(Math.PI * clamp01((t - T.cheerFrom) / (T.cheerTo - T.cheerFrom))) ** 0.5 : 0;
    const bob = (phase) => 0.11 * cheerEnvelope * Math.max(0, Math.sin(2 * Math.PI * 2.3 * (t - T.cheerFrom) + phase));
    const jolt = (amount) => knock(age, degrees(amount));
    const jump = (amount) => (age < 0 ? 0 : amount * Math.exp(-age / 0.14) * Math.abs(Math.sin(2 * Math.PI * 4 * age)));

    const back = popUp(t, T.crowdBack, crowdBack);
    kit.place(crowdBack, back.visible ? { ...back, fold: back.fold + jolt(7), dy: bob(0) + jump(0.16), roll: degrees(1.2) * cheerEnvelope * Math.sin(2 * Math.PI * 1.15 * (t - T.cheerFrom)) } : back);
    const front = popUp(t, T.crowdFront, crowdFront);
    kit.place(crowdFront, front.visible ? { ...front, fold: front.fold + jolt(5), dy: bob(1.9) + jump(0.12), roll: degrees(-1.0) * cheerEnvelope * Math.sin(2 * Math.PI * 1.15 * (t - T.cheerFrom) + 1) } : front);

    if (t < T.soldiers) kit.place(soldiers, { visible: false });
    else {
      const slide = spring(t - T.soldiers, { stiffness: 11, damping: 0.62 });
      kit.place(soldiers, { fold: jolt(4), dx: -12 * slide, roll: degrees(-3) * Math.sin(Math.PI * clamp01((t - T.soldiers) / 0.5)) * (1 - clamp01((t - T.soldiers) / 0.5)) });
    }

    const fallStart = T.tankLands - T.tankFall;
    if (t < fallStart) kit.place(tank, { visible: false });
    else if (t < T.tankLands) {
      const x = (t - fallStart) / T.tankFall;
      kit.place(tank, { dy: 14 * (1 - x * x), roll: degrees(7) * (1 - x), fold: degrees(-2) });
    } else {
      const bounce = 0.32 * Math.exp(-age / 0.09) * Math.abs(Math.sin(Math.PI * age / 0.13));
      kit.place(tank, { dy: bounce, roll: knock(age, degrees(3.5), 3, 0.22), fold: knock(age, degrees(5), 5, 0.2) });
    }
    dust.set({ origin: { x: tank.restX, y: tank.restY + 0.5, z: tank.restZ + 0.15 }, width: tank.width * 0.85, age: t > T.glasgowFoldsAway ? 9 : age });

    if (t < T.eightMillionAway) kit.place(eightMillion, popUp(t, T.eightMillion, eightMillion));
    else kit.place(eightMillion, foldDown(t, T.eightMillionAway, 0.2));
    if (t < T.tankLands + 0.03) kit.place(sixtyThousand, popUp(t, T.sixtyThousand, sixtyThousand));
    else kit.place(sixtyThousand, foldDown(t, T.tankLands + 0.03, 0.16));

    // ------------------------------------------------------------------- pithead
    kit.place(miner.piece, popUp(t, T.miner, miner.piece));
    miner.setOpen(t >= T.mouthFrom && t <= T.mouthTo ? mouthOpen(t) : 0);

    kit.place(publicOwnership, t < T.publicOwnershipAway ? popUp(t, T.publicOwnership, publicOwnership) : foldDown(t, T.publicOwnershipAway, 0.2));
    kit.place(ignored, popUp(t, T.ignored, ignored));
    if (t < T.reportSlapped) kit.place(report, popUp(t, T.report, report));
    else {
      const x = clamp01((t - T.reportSlapped) / 0.14);
      const settle = x >= 1 ? 0.06 * Math.exp(-(t - T.reportSlapped - 0.14) / 0.08) * Math.abs(Math.sin(2 * Math.PI * 5 * (t - T.reportSlapped - 0.14))) : 0;
      kit.place(report, { fold: Math.PI / 2 * x * x - settle, visible: true });
    }
  }

  return { pose, turns: [{ sheet: glasgow, from: T.turnFrom, length: T.turnLength, foldAwayAt: T.glasgowFoldsAway }] };
}
