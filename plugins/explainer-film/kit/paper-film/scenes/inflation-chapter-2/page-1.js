// What this does: page 1 of chapter 2, the opening. Two places, joined by a quick dip to black:
//   1. A painted debating chamber (a painting with depth). The film fades up from black and the
//      camera pushes slowly down the aisle toward an invented politician at a lectern; his mouth moves
//      while Malina asks the question he stands for ("won't creating new money just cause
//      inflation?"). NEW MONEY appears, and on "inflation?" a big amber 3D word INFLATION? pops up in
//      the room with a jolt.
//   2. Cut on "You've felt it at the checkout" to a painted supermarket checkout. A basket of shopping
//      sits on the conveyor with a price tag hanging from it: A YEAR AGO $100.00; on "costs more" the
//      tag flips to NOW $104.10 (example prices, labelled as such).
//      "That's inflation... prices in general, going up": INFLATION / PRICES IN GENERAL, GOING UP.
//      "Not one price tag": the basket's tag swings alone. "The whole basket": price tags pop up all
//      across the shelves and flip upward together; THE WHOLE BASKET.
//      "go back to the shell factory": a brass shell drops onto the conveyor with a bounce on
//      "shell" and the camera eases toward it, a bridge into page 2's munitions hall.
// Every time comes from Malina's recorded words (kit.at); pose(t) is computed from t alone.

import { THREE, clamp01, smooth, smoother, ramp, spring, seededRandom } from '../cinema-kit.js';
import { priceTag, shell } from '../models.js';
import { Motes } from '../effects.js';
import { hook, callout, credit, presence, INK } from '../graphics.js';

export async function build(kit) {
  const T = {
    start: 0,
    so: kit.at('so'),
    newMoney: kit.at('new'),
    inflationQ: kit.at('inflation'),
    youve: kit.at("you've"),
    same: kit.at('same'),
    basket: kit.at('basket'),
    costs: kit.at('costs'),
    more: kit.at('more'),
    yearAgo: kit.at('year'),
    thats: kit.at("that's"),
    inflation: kit.at('inflation', 2),
    prices: kit.at('prices'),
    not: kit.at('not'),
    whole: kit.at('whole'),
    basket2: kit.at('basket', 2),
    to: kit.at('to'),
    drives: kit.at('drives'),
    shell: kit.at('shell'),
    last: kit.lastWordEnd,
  };
  // the cut between the two places (hidden by a quick dip to black, fully black at T.cut)
  T.cut = T.youve - 0.02;

  // ------------------------------------------------------------------------------ the lights
  // one rig, re-tuned in pose() for each place (warm lamps in the chamber, cool tubes at the shop)
  kit.lightRig({ keyColour: 0xffd09a, keyShare: 0.7, keyFrom: [3, 6, 3], keyTarget: [0, -2, -10], fillSky: 0x9aa8b0, fillGround: 0x2a2219,
    fillShare: 0.2, haze: 0x161a1d, hazeDensity: 0.0, shadowBox: 10, shadowSoftness: 5, background: 0x0e1113, reflections: 0.3 });
  const { key, fill } = kit.lights;

  // ------------------------------------------------------------------------- 1. the chamber
  const chamber = await kit.relief('101-bg-parliament', { near: 6, far: 70, fov: 40 });
  const aisle = chamber.pointAt(0.5, 0.15);
  // the invented politician at his lectern, standing in the aisle (big, near, bottom on the floor)
  const man = await kit.speaker('politician', { at: [aisle.x - 0.35, aisle.y - 0.05, aisle.z + 0.6], width: 2.0 });
  // the question, as a big amber word standing up in the room behind him and above his head
  const question = await kit.word('INFLATION?', { size: 0.5, colour: '#e8a33d', at: [-0.1, 1.2, -11.5] });
  const chamberMotes = new Motes(kit.scene, { count: 160, min: [-2.2, -2.2, -14], max: [2.2, 2.4, -3], size: 0.025, seed: 11, opacity: 0.5 });

  // ------------------------------------------------------------------------- 2. the checkout
  const shop = await kit.relief('401-bg-checkout', { near: 6, far: 70, fov: 40 });
  const belt = shop.pointAt(0.42, 0.455);
  const basketWidth = 1.7;
  const basket = await kit.cutout('basket', { at: [belt.x - 0.25, belt.y, belt.z], width: basketWidth });
  // the basket's price tag hangs from the right of the rim: before (A YEAR AGO) and after (NOW)
  const tagBefore = priceTag({ width: 1.05, text: '$100.00' });
  const tagAfter = priceTag({ width: 1.05, text: '$104.10', accent: '#b23a2a' });
  const tagHolder = new THREE.Group();
  tagHolder.add(tagBefore.group, tagAfter.group);
  const tagHome = new THREE.Vector3(belt.x - 0.25 + basketWidth * 0.36, belt.y + basketWidth * 0.62, belt.z + 0.35);
  tagHolder.position.copy(tagHome);
  kit.scene.add(tagHolder);
  const tagCentre = () => tagHolder.localToWorld(new THREE.Vector3(tagBefore.width * 0.4, 0, 0));

  // the whole basket: tags all across the shelves (example prices, each up about the same share)
  const shelfSpots = [
    [0.12, 0.62, '$2.50', '$2.60'], [0.21, 0.69, '$4.00', '$4.16'], [0.08, 0.73, '$6.80', '$7.08'], [0.25, 0.58, '$3.20', '$3.33'],
    [0.44, 0.71, '$1.90', '$1.98'], [0.57, 0.67, '$5.40', '$5.62'], [0.33, 0.77, '$8.50', '$8.85'], [0.62, 0.76, '$2.20', '$2.29'],
    [0.86, 0.66, '$3.60', '$3.75'], [0.94, 0.6, '$7.50', '$7.81'], [0.8, 0.73, '$12.00', '$12.49'], [0.76, 0.79, '$4.80', '$5.00'],
  ];
  const random = seededRandom(7);
  const shelfTags = shelfSpots.map(([u, v, before, after], i) => {
    const at = shop.pointAt(u, v).multiplyScalar(0.9); // a little in front of its shelf
    const size = 0.07 * at.length();
    const a = priceTag({ width: size, text: before });
    const b = priceTag({ width: size, text: after, accent: '#b23a2a' });
    const inner = new THREE.Group();
    inner.add(a.group, b.group);
    const group = new THREE.Group();
    group.add(inner);
    group.position.copy(at);
    group.lookAt(0, at.y * 0.6, 0);
    kit.scene.add(group);
    return { group, inner, a, b, home: at, appear: T.whole - 0.05 + i * 0.06 + random() * 0.05, flip: T.basket2 + i * 0.025, phase: random() * 6 };
  });

  // the brass shell that drops onto the conveyor on "shell"
  const shellSpot = shop.pointAt(0.36, 0.395);
  const brass = shell({ height: 1.15 });
  brass.group.position.copy(shellSpot);
  kit.scene.add(brass.group);
  const shopMotes = new Motes(kit.scene, { count: 120, min: [-2, -1.5, -16], max: [2, 2.2, -4], size: 0.02, seed: 5, opacity: 0.35 });

  // ------------------------------------------------------------------------------ the cameras
  const chamberShot = kit.shot([
    { t: T.start, position: [0, 0.25, 0.8], target: [0, -0.2, -30], fov: 40, focus: 9 },
    { t: T.inflationQ - 0.2, position: [0, 0.1, -0.3], target: [0, -0.1, -30], fov: 38, focus: 7.6 },
    { t: T.cut, position: [0, 0.05, -0.8], target: [0, 0.0, -30], fov: 36, focus: 7.2 },
  ], { handheld: 0.01, seed: 1 });
  const tagFocus = [tagHome.x + 0.4, tagHome.y, tagHome.z];
  const shellFocus = [shellSpot.x, shellSpot.y + 0.5, shellSpot.z];
  const shopShot = kit.shot([
    { t: T.cut, position: [0.15, 0.35, 0.6], target: [-0.3, -0.9, -16], fov: 40, focus: 14 },
    { t: T.same + 0.2, position: [0.1, 0.15, -0.6], target: [-0.05, -0.55, -16], fov: 33, focus: tagFocus },
    { t: T.yearAgo, position: [0.12, 0.05, -1.2], target: [0.1, -0.3, -16], fov: 28, focus: tagFocus },
    { t: T.prices, position: [0.05, 0.4, 0.4], target: [0, 0.6, -30], fov: 38, focus: 14 },
    { t: T.not + 0.3, position: [0.1, 0.1, -0.6], target: [0, -0.4, -18], fov: 32, focus: tagFocus },
    { t: T.whole + 0.3, position: [0, 0.35, 0.6], target: [0, 0.9, -30], fov: 40, focus: 30 },
    { t: T.drives, position: [0, 0.4, 0.4], target: [0, 0.4, -30], fov: 40, focus: 20 },
    { t: T.shell + 0.4, position: [-0.1, 0.05, -0.9], target: [shellSpot.x * 0.5, -0.9, -16], fov: 33, focus: shellFocus },
    { t: T.last + 1.4, position: [-0.15, -0.05, -1.6], target: [shellSpot.x * 0.6, -0.9, -16], fov: 30, focus: shellFocus },
  ], { handheld: 0.012, seed: 3 });
  kit.shake(T.inflationQ + 0.05, 0.02, 0.16);
  kit.shake(T.shell + 0.02, 0.025, 0.15);

  // a flip (k 0..1) that turns a card over and back to its face: the before side shows until the
  // edge-on moment, the after side from then on, both facing the camera
  const flipAngle = (k) => (k < 0.5 ? k * Math.PI : (k - 1) * Math.PI);

  function pose(t) {
    const inChamber = t < T.cut;
    chamber.mesh.visible = inChamber;
    shop.mesh.visible = !inChamber;
    chamberMotes.set(t, { visible: inChamber });
    shopMotes.set(t, { visible: !inChamber });

    if (inChamber) {
      key.color.set(0xffd09a); key.intensity = Math.PI * 0.7; key.position.set(3, 6, 3); key.target.position.set(0, -2, -10);
      fill.intensity = Math.PI * 0.2;
      // the politician: a slight sway, mouth moving with her question
      man.set({ roll: 0.012 * Math.sin(t * 1.3) }, kit.mouthOpen(t, T.so - 0.05, T.inflationQ + 0.8));
      // INFLATION? folds up hard on the word, with an overshoot
      const rise = T.inflationQ - 0.05;
      question.set(t >= rise ? { fold: (Math.PI / 2) * spring(t - rise, { stiffness: 18, damping: 0.5 }) } : { visible: false });
      basket.set({ visible: false });
      tagHolder.visible = false; brass.group.visible = false;
      shelfTags.forEach((s) => { s.group.visible = false; });
      // fade up from black, dip to black for the cut
      const fade = Math.max(1 - smooth(ramp(t, 0.05, 0.85)), smooth(ramp(t, T.cut - 0.24, T.cut)));
      return { camera: chamberShot(t), look: { aperture: 7, maxBlur: 12, exposure: 0.95, glowThreshold: 0.93, glowStrength: 0.65, contrast: 1.06, fade } };
    }

    // ---- the checkout
    key.color.set(0xfff1dc); key.intensity = Math.PI * 0.75; key.position.set(-2, 8, 2); key.target.position.set(0, -1, -14);
    fill.intensity = Math.PI * 0.25;
    man.set({ visible: false }); question.set({ visible: false });
    // the basket on the belt; the conveyor carries it back up the belt as the shell comes
    const aside = smooth(ramp(t, T.to, T.shell - 0.4));
    basket.set({ dx: 0.3 * aside, dz: -1.6 * aside });
    // the basket's tag: hangs and breathes, flips on "costs", swings alone on "not one price tag"
    tagHolder.visible = true;
    tagHolder.position.set(tagHome.x + 0.3 * aside, tagHome.y, tagHome.z - 1.6 * aside);
    const flipK = smoother(ramp(t, T.costs, T.costs + 0.5));
    const swingAge = t - T.not;
    const swing = swingAge > 0 ? 0.38 * Math.exp(-swingAge / 1.2) * Math.sin(swingAge * 5.2) : 0;
    tagHolder.rotation.set(0, flipAngle(flipK) - 0.15, -0.32 + swing + 0.02 * Math.sin(t * 1.7));
    tagBefore.group.visible = flipK < 0.5;
    tagAfter.group.visible = flipK >= 0.5;
    // the shelf tags: pop up one after another, flip upward together, fold away as the shell comes
    const away = smooth(ramp(t, T.drives, T.drives + 0.5));
    shelfTags.forEach((s) => {
      const age = t - s.appear;
      s.group.visible = age > 0 && away < 1;
      if (!s.group.visible) return;
      const grow = 1 - spring(age, { stiffness: 14, damping: 0.55 });
      s.group.scale.setScalar(Math.max(0.001, grow * (1 - away)));
      const k = smoother(ramp(t, s.flip, s.flip + 0.45));
      s.group.position.set(s.home.x, s.home.y + 0.006 * s.home.length() * Math.sin(Math.PI * k), s.home.z);
      s.inner.rotation.set(0, flipAngle(k), -0.18 + 0.06 * Math.sin(t * 1.5 + s.phase));
      s.a.group.visible = k < 0.5; s.b.group.visible = k >= 0.5;
    });
    // the brass shell: falls onto the belt and bounces on "shell"
    const fall = 0.4;
    brass.group.visible = t >= T.shell - fall;
    if (brass.group.visible) {
      const x = clamp01((t - (T.shell - fall)) / fall);
      const age = t - T.shell;
      const bounce = age > 0 ? 0.32 * Math.exp(-age / 0.12) * Math.abs(Math.sin(Math.PI * age / 0.16)) : 0;
      brass.group.position.set(shellSpot.x, shellSpot.y + 3.5 * (1 - x * x) + bounce, shellSpot.z);
      const wobble = age > 0 ? 0.12 * Math.exp(-age / 0.25) * Math.sin(age * 26) : 0.25 * (1 - x);
      brass.group.rotation.set(0, t * 0.15, wobble);
    }
    const fade = 1 - smooth(ramp(t, T.cut, T.cut + 0.26));
    return { camera: shopShot(t), look: { aperture: 7.5, maxBlur: 12, exposure: 0.94, glowThreshold: 0.93, glowStrength: 0.6, contrast: 1.05, fade } };
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    // the chamber: NEW MONEY, then the 3D INFLATION? answers it
    hook(ctx, t, { at: T.newMoney, until: T.cut - 0.15, text: 'NEW MONEY', y: 250, size: 76 });
    if (t < T.cut) return true;
    // a soft dark wash at the top of the bright shop, so the hooks read over the shelves
    const wash = Math.min(presence(t, T.same, T.drives + 0.4, 0.4, 0.5) + presence(t, T.drives - 0.2, T.last + 3, 0.4, 0.4), 1) * 0.6;
    if (wash > 0) {
      const g = ctx.createLinearGradient(0, 0, 0, 640);
      g.addColorStop(0, `rgba(8,12,14,${wash})`); g.addColorStop(0.65, `rgba(8,12,14,${wash * 0.55})`); g.addColorStop(1, 'rgba(8,12,14,0)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 640);
    }
    // the same basket, a year apart
    const tagPoint = at(tagCentre());
    callout(ctx, t, { at: T.basket, until: T.costs + 0.2, point: tagPoint, text: 'A YEAR AGO', dx: -150, dy: -260, size: 44 });
    callout(ctx, t, { at: T.costs + 0.3, until: T.thats - 0.1, point: tagPoint, text: 'NOW', dx: -150, dy: -260, size: 52, accent: INK.red });
    hook(ctx, t, { at: T.same, until: T.costs - 0.05, text: 'THE SAME BASKET', y: 300, size: 68 });
    hook(ctx, t, { at: T.more, until: T.thats - 0.1, text: 'COSTS MORE', y: 300, size: 92, colour: INK.amber });
    credit(ctx, t, { at: T.same, until: T.thats - 0.1, text: 'Example prices', y: 1460, size: 28 });
    // what inflation is
    hook(ctx, t, { at: T.inflation, until: T.not - 0.1, text: 'INFLATION', y: 300, size: 124 });
    hook(ctx, t, { at: T.prices, until: T.not - 0.1, lines: ['PRICES IN GENERAL,', 'GOING UP'], y: 440, size: 58, colour: INK.amber });
    // one tag, then the whole basket
    hook(ctx, t, { at: T.not, until: T.whole - 0.1, text: 'NOT ONE PRICE TAG', y: 300, size: 66 });
    hook(ctx, t, { at: T.whole, until: T.to + 0.1, text: 'THE WHOLE BASKET', y: 300, size: 92, colour: INK.amber });
    credit(ctx, t, { at: T.whole, until: T.to + 0.1, text: 'Example prices', y: 1460, size: 28 });
    // what really drives it? the shell factory
    hook(ctx, t, { at: T.drives - 0.2, until: T.shell - 0.1, text: 'WHAT REALLY DRIVES IT?', y: 300, size: 64 });
    hook(ctx, t, { at: T.shell, until: T.last + 3, lines: ['BACK TO', 'THE SHELL FACTORY'], y: 320, size: 66, colour: INK.amber });
    return true;
  }

  return { pose, draw2D };
}
