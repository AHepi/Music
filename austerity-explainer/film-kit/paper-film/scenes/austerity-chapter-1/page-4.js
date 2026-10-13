// What this does: chapter 1, page 4, "Italy" (a street of factories in Turin). Source: Clara E.
// Mattei, The Capital Order (2022); facts from research entries C1-12 and C1-13.
//
// What happens, tied to Malina's words:
//   "In Italy"                   a factory with a saw-tooth roof folds up
//   "a million workers"          a crowd of striking workers folds up; 1 MILLION pops up
//   "go on strike"               the crowd bobs
//   "half a million"             1 MILLION folds away; 500,000 pops up
//   "take over their factories"  the crowd slides toward the factory and goes in (folds down as it
//                                goes); a plain red flag rises on the factory roof

import { popUp, popUpUntil, spring, clamp01, degrees, easeIn } from '../paper-kit.js';

export const SHEETS = ['turin-street'];

export async function build(kit) {
  const at = kit.at;
  const factory = await kit.piece('factory-small', { width: 5.6, x: 1.0, y: 7.0, z: 0.6 });
  const flag = await kit.piece('red-flag', { width: 1.7, x: -0.6, y: 7.0 + factory.height * 0.5, z: 0.45 });
  const strikers = await kit.piece('italian-strikers', { width: 10.6, x: 0, y: 0.2, z: 2.4 });
  const oneMillion = await kit.word(['1 MILLION'], { size: 1.0, x: 0, y: 12.4, z: 0.55 });
  const halfMillion = await kit.word(['500,000'], { size: 1.0, x: 0, y: 12.4, z: 0.55 });

  const T = {
    factory: at('In', 1) - 0.12,
    strikers: at('million', 1) - 0.12,
    oneMillion: at('million', 1) - 0.04,
    cheerFrom: at('go') - 0.05, cheerTo: kit.end('strike') + 0.5,
    oneMillionAway: at('half') - 0.22,
    halfMillion: at('half') - 0.04,
    marchFrom: at('take') + 0.02, marchLength: 0.75,
    flagFrom: at('factories') - 0.05,
  };

  function pose(t) {
    kit.place(factory, popUp(t, T.factory, factory));

    // the strikers: up on "a million", bobbing on "strike", then off into the factory
    const cheering = t > T.cheerFrom && t < T.cheerTo;
    const envelope = cheering ? Math.sin(Math.PI * clamp01((t - T.cheerFrom) / (T.cheerTo - T.cheerFrom))) ** 0.5 : 0;
    const bob = 0.12 * envelope * Math.max(0, Math.sin(2 * Math.PI * 2.4 * (t - T.cheerFrom)));
    const roll = degrees(1.2) * envelope * Math.sin(2 * Math.PI * 1.2 * (t - T.cheerFrom));
    if (t < T.marchFrom) {
      const up = popUp(t, T.strikers, strikers);
      kit.place(strikers, up.visible ? { ...up, dy: bob, roll } : up);
    } else {
      const x = clamp01((t - T.marchFrom) / T.marchLength);
      const step = 0.1 * Math.abs(Math.sin(Math.PI * 3 * (t - T.marchFrom)));
      if (x >= 1) kit.place(strikers, { visible: false });
      else kit.place(strikers, { visible: true, dx: 4.5 * easeIn(x), dy: step + 2.2 * easeIn(x), fold: (Math.PI / 2) * easeIn(x) });
    }

    kit.place(oneMillion, popUpUntil(t, T.oneMillion, T.oneMillionAway, oneMillion));
    kit.place(halfMillion, popUp(t, T.halfMillion, halfMillion));

    // the red flag rises from behind the roof, with a small sway as it settles
    if (t < T.flagFrom) kit.place(flag, { visible: false });
    else {
      const rise = spring(t - T.flagFrom, { stiffness: 9, damping: 0.7 });
      kit.place(flag, { visible: true, dy: -1.7 * rise, roll: degrees(3) * Math.sin(2 * Math.PI * 0.9 * (t - T.flagFrom)) * Math.exp(-(t - T.flagFrom) / 1.2) });
    }
  }

  return { pose };
}
