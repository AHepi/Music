// What this does: a starting point for one page of a chapter in the cinema look. Copy it to
// paper-film/scenes/YOUR-CHAPTER/page-N.js and change the parts marked CHANGE. As written it shows
// one painted room with depth (the camera creeping in), a title on the first word, a paper
// cut-out that pops up on a word, a stack of 3D banknotes landing on a word, a label pointing at
// them, and a big hook (short words) on a later word.
//
// Rules that keep the film right (see the build-cinema-page skill for all of them):
//   - every time comes from a narration word: kit.at('word') (first time on this page) or
//     kit.at('word', 2) (second time). Never type seconds.
//   - pose(t) and draw2D(ctx, t) must work from t alone: the film is drawn in separate stretches.
//   - words on screen are short forms of what the narrator says at that moment.
//   - phone buttons: anything to be read ends left of 0.90 across (972 pixels, TEXT_RIGHT in graphics.js) and
//     above 0.80 down (keep the bottom 380 pixels clear). The older "right 140 pixels" (0.87 across) is stricter than needed.

import { popUp, clamp01, smooth } from '../cinema-kit.js';
import { banknoteBundle } from '../models.js';
import { Motes } from '../effects.js';
import { placeTitle, hook, callout } from '../graphics.js';

export async function build(kit) {
  // CHANGE: the words this page reacts to (lower case, punctuation ignored)
  const T = {
    start: kit.firstWordAt - 0.6,      // the page appears a little before its first word
    title: kit.firstWordAt,            // e.g. kit.at('britain')
    figure: kit.at(kit.words[Math.min(3, kit.words.length - 1)].text),    // e.g. kit.at('workers')
    money: kit.at(kit.words[Math.min(6, kit.words.length - 1)].text),     // e.g. kit.at('money')
    point: kit.at(kit.words[Math.min(9, kit.words.length - 1)].text),     // e.g. kit.at('doubled')
    end: kit.lastWordEnd,
  };

  // light: a warm lamp for the 3D things; inside a painting keep reflections low (0.3), or paper
  // and banknotes look white
  kit.lightRig({ keyColour: 0xffd6a0, keyShare: 0.7, keyFrom: [6, 8, -8], keyTarget: [0, -3, -10],
    fillShare: 0.2, hazeDensity: 0.004, reflections: 0.3, background: 0x10161b });

  // CHANGE: the painted room (a name in assets/reliefs/YOUR-CHAPTER/, made by prepare_relief.py).
  // The camera starts at the origin looking along -z, exactly where the painting was made from.
  // room.pointAt(u, v) is the 3D spot behind the painting's point u (0 left .. 1 right), v (0 bottom
  // .. 1 top); find good spots with tools/relief_points.py.
  const room = await kit.relief('102-bg-munitions-factory', { near: 6, far: 70, fov: 40 });
  const motes = new Motes(kit.scene, { count: 160, min: [-2, -2.8, -14], max: [2, 2, -4], size: 0.03, opacity: 0.5 });

  // CHANGE: a cut-out (a name in paper-film/pieces/YOUR-CHAPTER/pieces.json). Big and near reads
  // best; its bottom edge may sit below the frame.
  const figure = await kit.cutout('munition-women', { at: [-0.35, -3.5, -8.6], width: 4.0 });

  // 3D banknote bundles that land in a stack on the floor
  const floor = room.pointAt(0.6, 0.07);
  const bundles = [0, 1, 2].map((i) => {
    const b = banknoteBundle({ width: 0.62, depth: 0.31, notes: 34 });
    b.landAt = T.money + 0.1 + i * 0.22;
    kit.scene.add(b.group);
    return b;
  });

  // the camera: small moves only inside a painting (1 to 2 units), keys in time order
  const shot = kit.shot([
    { t: T.start, position: [0, 0.1, 0.4], target: [0, -0.4, -30], fov: 40, focus: 14 },
    { t: T.money - 0.2, position: [0.1, -0.3, -1.0], target: [0.1, -1.6, -30], fov: 40, focus: [floor.x, floor.y, floor.z] },
    { t: T.end + 1.2, position: [0.05, -0.3, -1.6], target: [0, -1.3, -30], fov: 40, focus: 10 },
  ], { handheld: 0.012, seed: 1 });

  function pose(t) {
    motes.set(t);
    figure.set(popUp(t, T.figure - 0.15, { height: 1.4, restZ: 0.15 }));
    let height = 0;
    for (const b of bundles) {
      const k = clamp01((t - (b.landAt - 0.4)) / 0.4);                // falls for 0.4 s
      b.group.visible = k > 0;
      b.group.position.set(floor.x, floor.y + height + 3 * (1 - k * k), floor.z);
      height += b.height;
    }
    // look: exposure 0.9-1.0, aperture 7-9 (focus blur), glow above 0.9 so only bright things glow
    return { camera: shot(t), look: { aperture: 8, exposure: 0.95, glowThreshold: 0.95, glowStrength: 0.6 } };
  }

  function draw2D(ctx, t) {
    placeTitle(ctx, t, { at: T.title, until: T.figure - 0.1, place: 'Britain', year: 1915 });        // CHANGE
    callout(ctx, t, { at: T.money + 0.4, until: T.point - 0.1, point: kit.toScreen([floor.x, floor.y + 0.3, floor.z]), text: 'NEW MONEY', dx: -60, dy: -320 });  // CHANGE
    hook(ctx, t, { at: T.point, until: T.end + 1, text: 'PRICES ×2', y: 330 });                         // CHANGE
    return true;
  }

  // join: how this page hands over to the next (default: a page peel 0.3 s after the last word)
  return { pose, draw2D /*, join: { kind: 'peel', after: 0.3, length: 0.85 } */ };
}
