// What this does: page 1 of chapter 2, the opening. Two places, joined by a quick dip to black, each
// one still shot (the camera rule: still unless a move lands a point, three moves at most):
//   1. A painted debating chamber (a painting with depth). The film fades up from black on an
//      invented politician at a lectern; his mouth moves while Malina asks the question he stands for
//      ("won't creating new money just cause inflation?"). NEW MONEY appears; the camera zooms in on
//      him, and on "inflation?" a big amber 3D word INFLATION? pops up in the room with a jolt.
//   2. Cut on "You've felt it at the checkout" to a painted supermarket checkout. A basket of shopping
//      stands on the conveyor (its bottom on the belt) with a price tag hanging from it. The camera
//      zooms in on "the same basket": A YEAR AGO $100.00; on "costs more" the tag flips to NOW $104.10
//      (example prices, labelled as such). It zooms out on "That's inflation... prices in general":
//      INFLATION / PRICES IN GENERAL, GOING UP. "Not one price tag": the basket's tag swings alone.
//      "The whole basket": price tags pop up in clear air in front of the shelves (none touching
//      another, the basket or the terminal) and flip upward together; THE WHOLE BASKET.
//      "drives it": the tags and the basket fold away; "go back to the shell factory": a brass shell
//      drops onto the belt where the basket stood, and the camera zooms in on it, a bridge into
//      page 2's munitions hall.
// Every time comes from Malina's recorded words (kit.at); pose(t) is computed from t alone.

import { THREE, clamp01, smooth, smoother, ramp, spring, seededRandom } from '../cinema-kit.js';

// sx, sy (0..1 of the wide frame, from the top left), price a year ago, price now, card reaches left
const SHELF_SPOTS = [
  [0.08, 0.25, '$2.50', '$2.60'], [0.39, 0.24, '$4.00', '$4.16'], [0.845, 0.255, '$3.60', '$3.75', true],
  [0.10, 0.34, '$6.80', '$7.08'], [0.41, 0.335, '$1.90', '$1.98'], [0.835, 0.35, '$7.50', '$7.81', true],
  [0.08, 0.425, '$3.20', '$3.33'], [0.38, 0.425, '$5.40', '$5.62'],
];
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
  // the invented politician at his lectern, standing in the aisle (big, near, bottom ON the floor)
  const manFloor = chamber.pointAt(0.47, 0.14);
  const man = await kit.speaker('politician', { at: [manFloor.x, manFloor.y + 0.01, manFloor.z], width: 2.0 });
  // the question, as a big amber word standing up in the room behind him and above his head
  const question = await kit.word('INFLATION?', { size: 0.34, colour: '#e8a33d', at: [-0.1, 1.2, -11.5] });
  const chamberMotes = new Motes(kit.scene, { count: 160, min: [-2.2, -2.2, -14], max: [2.2, 2.4, -3], size: 0.025, seed: 11, opacity: 0.5 });

  // ------------------------------------------------------------------------- 2. the checkout
  const shop = await kit.relief('401-bg-checkout', { near: 6, far: 70, fov: 40 });
  // the basket stands ON the belt: its bottom edge on the belt surface (room.pointAt), a hair above
  // it so the card never sinks into the painting. On "drives" it folds down flat toward us and is
  // gone, and the shell drops onto the belt where it stood.
  const basketWidth = 1.9;
  const basketHome = shop.pointAt(0.395, 0.40);
  basketHome.y += 0.012;
  const basket = await kit.cutout('basket', { at: [basketHome.x, basketHome.y, basketHome.z], width: basketWidth });
  // the painted belt tilts a little from side to side: raise the card just until its lowest corner
  // clears the belt (measured once; a few millimetres)
  let basketLift = 0;
  for (let i = 0; i < 40 && shop.clearance(basket.anchor) < 0.035; i++) { basketLift += 0.002; basket.set({ dy: basketLift }); }
  basketHome.y += basketLift;
  // the basket's price tag hangs from the right of the rim, a little in front of the basket so it can
  // flip over (about its own middle line, upward) without touching it: A YEAR AGO $100.00, NOW $104.10
  const tagBefore = priceTag({ width: 1.0, text: '$100.00' });
  const tagAfter = priceTag({ width: 1.0, text: '$104.10', accent: '#b23a2a' });
  const tagFlip = new THREE.Group();
  tagFlip.add(tagBefore.group, tagAfter.group);
  const tagHolder = new THREE.Group();
  tagHolder.add(tagFlip);
  const tagOffset = new THREE.Vector3(basketWidth * 0.3 - 0.05, basketWidth * 0.66, 0.6);   // its card clear of the right 140 px
  kit.scene.add(tagHolder);
  // the callouts point at the tag's top rim (above the digits), so the leader line never crosses the price
  const tagRim = () => tagFlip.localToWorld(new THREE.Vector3(tagBefore.width * 0.5, tagBefore.height * 0.47, 0));

  // the brass shell that drops onto the conveyor on "shell", where the basket stood. The painted belt
  // slopes up away from us, so the shell's round foot is raised just enough that its back edge stays
  // on (not in) the belt: found by measuring, once.
  const shellSpot = shop.pointAt(0.40, 0.40);
  const brass = shell({ height: 1.5 });
  kit.scene.add(brass.group);
  brass.group.position.copy(shellSpot);
  for (let i = 0; i < 60 && shop.clearance(brass.group) < 0.04; i++) brass.group.position.y += 0.005;
  shellSpot.y = brass.group.position.y;
  const shopMotes = new Motes(kit.scene, { count: 120, min: [-2, -1.5, -16], max: [2, 2.2, -4], size: 0.02, seed: 5, opacity: 0.35 });

  // ------------------------------------------------------------------------------ the cameras
  // The camera rule: each place is one still shot with at most three meaningful moves.
  // Shot 1, the chamber: it holds on the politician; on "new money ... inflation?" it zooms in on him
  // and the question (narrowing onto what matters now), then holds to the cut.
  const manHead = [manFloor.x, manFloor.y + 2.0, manFloor.z];
  const chamberShot = kit.stillShot({ position: [0, 0.1, -0.3], target: [0, -0.35, -30], fov: 35, focus: manHead }, [
    { from: T.newMoney - 0.15, to: T.inflationQ + 0.1, kind: 'zoom in', position: [0, 0.05, -0.8], target: [-0.05, -0.1, -30], fov: 30 },
  ], { name: 'the chamber' });
  // Shot 2, the checkout: it opens on the basket on the belt; zooms in on the basket and its tag for
  // "the same basket ... costs more"; zooms out on "that's inflation, prices in general" to make room
  // for the whole basket (the tags all across the shelves); zooms in on the shell as she sends us back
  // to the shell factory.
  const basketMid = [basketHome.x, basketHome.y + basketWidth * 0.45, basketHome.z];
  const tagFocus = [basketHome.x + tagOffset.x + 0.45, basketHome.y + tagOffset.y, basketHome.z + tagOffset.z];
  const shellFocus = [shellSpot.x, shellSpot.y + 0.6, shellSpot.z];
  // the checkout's hold poses are aimed a few degrees up (and the camera raised a touch) so the empty
  // steel counter in front of the belt mostly drops out of the bottom of the frame
  const aimUp = (position, target, degrees) => {
    const flat = Math.hypot(target[0] - position[0], target[2] - position[2]);
    return [target[0], target[1] + flat * Math.tan((degrees * Math.PI) / 180), target[2]];
  };
  const OPEN = { position: [0, 0.05, -0.6] };
  OPEN.target = aimUp(OPEN.position, [basketMid[0] * 0.9, -0.2, -30], 3.5);
  const CLOSE = { position: [0, 0.0, -1.4] };
  CLOSE.target = aimUp(CLOSE.position, [basketMid[0] + 0.37, basketMid[1] + 0.15, basketMid[2]], 3.5);
  const WIDE = { position: [0, 0.2, 0] };
  WIDE.target = aimUp(WIDE.position, [0, 1.6, -30], 2.8);
  WIDE.fov = 33;
  const shopShot = kit.stillShot({ position: OPEN.position, target: OPEN.target, fov: 30, focus: basketMid }, [
    { from: T.same - 0.2, to: T.basket + 0.55, kind: 'zoom in', position: CLOSE.position, target: CLOSE.target, fov: 27, focus: tagFocus },
    { from: T.thats - 0.05, to: T.inflation + 0.85, kind: 'zoom out', position: WIDE.position, target: WIDE.target, fov: WIDE.fov, focus: 15 },
    { from: T.whole + 0.1, to: T.whole + 0.5, kind: 'focus', focus: 18 },
    { from: T.drives + 0.3, to: T.shell + 0.3, kind: 'zoom in', position: [0, -0.25, -1.8], target: [shellFocus[0], shellFocus[1] + 0.55, shellFocus[2]], fov: 21, focus: shellFocus },
  ], { name: 'the checkout' });
  kit.shake(T.inflationQ + 0.05, 0.02, 0.16);
  kit.shake(T.shell + 0.02, 0.012, 0.15);

  // the whole basket: tags all across the shelves (example prices, each up about the same share).
  // Each is placed by where it shows in the wide shot (sx, sy: 0..1 across the 1080 x 1920 frame from
  // the top left), floating in clear air in front of the painted shelves; none overlaps another, the
  // basket, its tag or the payment terminal. `left`: the card reaches left from its string.
  const wideCam = new THREE.PerspectiveCamera(WIDE.fov, 1080 / 1920, 0.1, 200);
  wideCam.position.set(...WIDE.position); wideCam.lookAt(new THREE.Vector3(...WIDE.target)); wideCam.updateMatrixWorld();
  const surfaceAlong = (origin, dir) => {
    // walk along the ray until it meets the painted surface; returns that distance
    for (let s = 2; s < 80; s += 0.05) {
      const p = origin.clone().addScaledVector(dir, s);
      const d = -p.z, u = (p.x / d / shop.tanX + 1) / 2, v = (p.y / d / shop.tanY + 1) / 2;
      if (d >= shop.distanceAt(Math.min(1, Math.max(0, u)), Math.min(1, Math.max(0, v)))) return s;
    }
    return 80;
  };
  const shelfSpots = SHELF_SPOTS;
  const random = seededRandom(7);
  const shelfTags = shelfSpots.map(([sx, sy, before, after, left], i) => {
    const dir = new THREE.Vector3(sx * 2 - 1, 1 - sy * 2, 0.5).unproject(wideCam).sub(wideCam.position).normalize();
    const wall = surfaceAlong(wideCam.position, dir);
    const reach = Math.min(wall - 2.5, 15);
    const at = wideCam.position.clone().addScaledVector(dir, reach);
    const size = 0.056 * reach;
    const a = priceTag({ width: size, text: before });
    const b = priceTag({ width: size, text: after, accent: '#b23a2a' });
    const inner = new THREE.Group();
    inner.add(a.group, b.group);
    if (left) inner.position.x = -0.8 * size;
    const group = new THREE.Group();
    group.add(inner);
    group.position.copy(at);
    group.lookAt(wideCam.position);
    kit.scene.add(group);
    return { group, inner, a, b, home: at, size, wall, appear: T.whole - 0.05 + i * 0.06 + random() * 0.05, flip: T.basket2 + i * 0.025, phase: random() * 6 };
  });

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
      // the politician: mouth moving with her question (he stands still; the camera holds)
      man.set({}, kit.mouthOpen(t, T.so - 0.05, T.inflationQ + 0.8));
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
    // the basket on the belt; it folds down flat toward us on "drives", making room for the shell
    const aside = smoother(ramp(t, T.drives - 0.1, T.drives + 0.45));
    // it fades as it folds and is gone by about 70% of the fold, so it never shows as a thin card above the belt
    basket.set({ visible: aside < 0.7, fold: (Math.PI / 2) * aside, dy: basketLift, opacity: 1 - smooth(ramp(aside, 0.25, 0.7)) });
    // the basket's tag: hangs, flips on "costs", swings alone on "not one price tag", shrinks away with the basket
    const tagGone = smooth(ramp(t, T.drives - 0.45, T.drives - 0.12));
    tagHolder.visible = tagGone < 1;
    tagHolder.position.set(basketHome.x + tagOffset.x, basketHome.y + tagOffset.y, basketHome.z + tagOffset.z);
    tagHolder.scale.setScalar(Math.max(0.001, 1 - tagGone));
    const flipK = smoother(ramp(t, T.costs, T.costs + 0.5));
    const swingAge = t - T.not;
    const swing = swingAge > 0 ? 0.3 * Math.exp(-swingAge / 1.2) * Math.sin(swingAge * 5.2) : 0;
    tagHolder.rotation.set(0, 0, -0.26 + swing);
    tagFlip.rotation.set(flipAngle(flipK), 0, 0);
    tagBefore.group.visible = flipK < 0.5;
    tagAfter.group.visible = flipK >= 0.5;
    // the shelf tags: pop up one after another, flip upward together, fold away as the shell comes
    const away = smooth(ramp(t, T.drives - 0.4, T.drives + 0.1));
    shelfTags.forEach((s) => {
      const age = t - s.appear;
      s.group.visible = age > 0 && away < 1;
      if (!s.group.visible) return;
      const grow = 1 - spring(age, { stiffness: 14, damping: 0.55 });
      s.group.scale.setScalar(Math.max(0.001, grow * (1 - away)));
      const k = smoother(ramp(t, s.flip, s.flip + 0.45));
      s.group.position.set(s.home.x, s.home.y + 0.08 * s.size * Math.sin(Math.PI * k), s.home.z);
      s.inner.rotation.set(flipAngle(k), 0, -0.12 + 0.04 * Math.sin(t * 1.5 + s.phase));
      s.a.group.visible = k < 0.5; s.b.group.visible = k >= 0.5;
    });
    // the brass shell: falls onto the belt and bounces on "shell" (it never goes below the belt)
    const fall = 0.4;
    brass.group.visible = t >= T.shell - fall;
    if (brass.group.visible) {
      const x = clamp01((t - (T.shell - fall)) / fall);
      const age = t - T.shell;
      const bounce = age > 0 ? 0.25 * Math.exp(-age / 0.12) * Math.abs(Math.sin(Math.PI * age / 0.16)) : 0;
      brass.group.position.set(shellSpot.x, shellSpot.y + 3.5 * (1 - x * x) + bounce, shellSpot.z);
      brass.group.rotation.set(0, t * 0.15, 0);
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
    const tagPoint = at(tagRim());
    callout(ctx, t, { at: T.basket, until: T.costs + 0.2, point: tagPoint, text: 'A YEAR AGO', dx: -150, dy: -260, size: 44 });
    callout(ctx, t, { at: T.costs + 0.3, until: T.thats - 0.1, point: tagPoint, text: 'NOW', dx: -150, dy: -260, size: 52, accent: INK.red });
    hook(ctx, t, { at: T.same, until: T.costs - 0.05, text: 'THE SAME BASKET', y: 300, size: 68 });
    hook(ctx, t, { at: T.more, until: T.thats - 0.1, text: 'COSTS MORE', y: 300, size: 92, colour: INK.amber });
    credit(ctx, t, { at: T.same, until: T.thats - 0.1, text: 'Example prices', y: 400, size: 30, plate: true });
    // what inflation is
    hook(ctx, t, { at: T.inflation, until: T.not - 0.1, text: 'INFLATION', y: 300, size: 124 });
    hook(ctx, t, { at: T.prices, until: T.not - 0.1, lines: ['PRICES IN GENERAL,', 'GOING UP'], y: 440, size: 58, colour: INK.amber });
    // one tag, then the whole basket
    hook(ctx, t, { at: T.not, until: T.whole - 0.1, text: 'NOT ONE PRICE TAG', y: 300, size: 66 });
    hook(ctx, t, { at: T.whole, until: T.to + 0.1, text: 'THE WHOLE BASKET', y: 300, size: 78, colour: INK.amber });
    credit(ctx, t, { at: T.whole, until: T.to + 0.1, text: 'Example prices', y: 400, size: 30, plate: true });
    // what really drives it? the shell factory
    hook(ctx, t, { at: T.drives - 0.2, until: T.shell - 0.1, text: 'WHAT REALLY DRIVES IT?', y: 300, size: 64 });
    hook(ctx, t, { at: T.shell, until: T.last + 3, lines: ['BACK TO', 'THE SHELL FACTORY'], y: 320, size: 66, colour: INK.amber });
    return true;
  }

  return { pose, draw2D };
}
