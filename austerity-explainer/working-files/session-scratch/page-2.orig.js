// What this does: page 2 of chapter 2, "Britain, 1915". We stand inside a painted munitions hall
// (a painting with depth, so the camera can creep down its aisle and the hall shifts like a real
// room). Sunlight falls through the high windows and dust drifts in it.
//   - "Britain, 1915": a place-and-year title.
//   - "Unemployment ... under one percent": a row of munition women rises up in the foreground; a
//     panel of a hundred dots fills in, all but one, under the words UNDER 1%.
//   - "paid for partly with new money": bundles of banknotes drop onto the floor and stack up.
//   - "Submarines are sinking supply ships": three paper boats pop up, tip over and fade away.
//   - "factories are turned over to war work": the camera turns to the benches of shells.
//   - "more money is chasing fewer things to buy": more bundles land and the stack grows, while a
//     basket of shopping shrinks; MORE MONEY / FEWER THINGS.
//   - "prices have roughly doubled": two bars, 1914 and 1918, the second twice the first.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, foldDown, clamp01, smooth, ramp, lerp, seededRandom } from '../cinema-kit.js';
import { banknoteBundle, paperBoat } from '../models.js';
import { Motes, LightBeam } from '../effects.js';
import { placeTitle, hook, callout, bars, presence, INK } from '../graphics.js';

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.6,
    britain: kit.at('britain'),
    unemployment: kit.at('unemployment'),
    under: kit.at('under'),
    percent: kit.at('percent'),
    newMoney: kit.at('new'),
    submarines: kit.at('submarines'),
    factories: kit.at('factories'),
    warWork: kit.at('war', 2),
    more: kit.at('more'),
    chasing: kit.at('chasing'),
    fewer: kit.at('fewer'),
    end: kit.at('end'),
    doubled: kit.at('doubled'),
    last: kit.lastWordEnd,
  };

  kit.lightRig({ keyColour: 0xffd6a0, keyShare: 0.75, keyFrom: [7, 9, -16], keyTarget: [0, -3, -10], fillSky: 0x8aa0ac, fillGround: 0x2a241e,
    fillShare: 0.2, haze: 0x1c2328, hazeDensity: 0.004, shadowBox: 9, shadowSoftness: 5, background: 0x10161b, reflections: 0.3 });
  // the hall: the painting pushed back by its depth (camera starts where it was painted from)
  const hall = await kit.relief('102-bg-munitions-factory', { near: 6, far: 70, fov: 40 });
  const floorAt = (u, v) => hall.pointAt(u, v);

  // sunlight through the high windows on the right, and dust in the aisle
  const beams = [
    new LightBeam(kit.scene, { from: [4.4, 7.5, -30], to: [-0.6, -2.8, -17], width: 3.2, startWidth: 1.0, strength: 0.16 }),
    new LightBeam(kit.scene, { from: [3.6, 6.5, -21], to: [-0.4, -2.9, -12], width: 2.4, startWidth: 0.8, strength: 0.12 }),
  ];
  const motes = new Motes(kit.scene, { count: 220, min: [-2.2, -2.9, -16], max: [2.2, 2.5, -4], size: 0.03, seed: 21, opacity: 0.6 });

  // munition women, waist up, rising in the foreground (their bottom edge sits below the frame)
  const women = await kit.cutout('munition-women', { at: [-0.35, -3.5, -8.6], width: 4.0 });

  // bundles of new banknotes, landing in a stack on the floor, right of the aisle
  const stackBase = floorAt(0.6, 0.07);
  const random = seededRandom(17);
  const bundles = [];
  for (let i = 0; i < 9; i++) {
    const b = banknoteBundle({ width: 0.62, depth: 0.31, notes: 34 });
    b.group.rotation.y = (random() - 0.5) * 0.5;
    b.twist = (random() - 0.5) * 0.25;
    b.shift = [(random() - 0.5) * 0.06, (random() - 0.5) * 0.06];
    // the first three land on "new money", the rest on "more money is chasing"
    b.landAt = i < 3 ? T.newMoney + 0.1 + i * 0.22 : T.more + 0.05 + (i - 3) * 0.2;
    kit.scene.add(b.group);
    bundles.push(b);
  }

  // three paper boats on a puddle, left of the aisle, sinking one after another
  const boats = [0, 1, 2].map((i) => {
    const boat = paperBoat({ length: 0.55, colour: 0xcfc6b4 });
    const at = floorAt(0.3 + i * 0.07, 0.11 + (i % 2) * 0.02);
    boat.group.position.copy(at);
    boat.home = at;
    boat.group.rotation.y = 0.3 - i * 0.25;
    boat.sinkAt = T.submarines + 0.45 + i * 0.55;
    boat.mesh = boat.group.children[0];
    boat.mesh.material.transparent = true;
    kit.scene.add(boat.group);
    return boat;
  });

  // the basket of things to buy, shrinking as the money stack grows
  const basketAt = floorAt(0.36, 0.1);
  const basket = await kit.cutout('basket', { at: [basketAt.x, basketAt.y, basketAt.z], width: 0.9 });

  // the camera (still unless a move is essential, three moves at most): it holds on the hall from
  // where it was painted; moves down to the floor for the small details as the new money lands; then
  // pans a little right as the factories turn to war work, and holds there (the money stack, the
  // basket and the benches all in view) to the end
  const stackPoint = [stackBase.x, stackBase.y, stackBase.z];
  const shot = kit.stillShot({ position: [0, 0.1, 0.2], target: [0, -0.5, -30], fov: 40, focus: 12 }, [
    { from: T.unemployment + 0.2, to: T.unemployment + 0.8, kind: 'focus', focus: 9.0 },
    { from: T.newMoney - 0.9, to: T.newMoney + 0.3, kind: 'move down', position: [0.05, -0.35, -1.2], target: [0, -1.8, -30], focus: stackPoint },
    { from: T.submarines - 0.1, to: T.submarines + 0.4, kind: 'focus', focus: [boats[1].home.x, boats[1].home.y, boats[1].home.z] },
    { from: T.factories - 0.1, to: T.warWork + 0.5, kind: 'pan right', target: [0.9, -1.6, -26], focus: stackPoint },
  ], { name: 'the munitions hall' });
  kit.shake(T.newMoney + 0.3, 0.012, 0.18);

  function pose(t) {
    beams.forEach((b) => b.set(t, kit.camera));
    motes.set(t);
    // the women rise on "unemployment" and fold away as the money comes
    women.set(t < T.newMoney - 0.3 ? popUp(t, T.unemployment - 0.2, { height: 1.4, restZ: 0.15 }) : foldDown(t, T.newMoney - 0.3, 0.3));
    // the banknote stack
    let height = 0;
    bundles.forEach((b) => {
      const fall = 0.42;
      const k = clamp01((t - (b.landAt - fall)) / fall);
      b.group.visible = t >= b.landAt - fall;
      const restY = stackBase.y + height;
      b.group.position.set(stackBase.x + b.shift[0], restY + 3.2 * (1 - k * k), stackBase.z + b.shift[1]);
      const settle = t > b.landAt ? Math.exp(-(t - b.landAt) * 10) * Math.sin((t - b.landAt) * 30) * 0.05 : 0;
      b.group.rotation.z = b.twist * (1 - k) + settle;
      height += b.height;
    });
    // the boats pop up on "submarines", bob, then tip over and fade away (they never sink through the floor)
    boats.forEach((boat) => {
      const age = t - boat.sinkAt;
      const gone = smooth(clamp01((age - 0.25) / 1.0));
      const appear = clamp01((t - T.submarines) / 0.35);
      boat.group.visible = gone < 1 && appear > 0;
      boat.group.scale.setScalar(smooth(appear));
      boat.group.position.set(boat.home.x, boat.home.y + 0.01 * Math.sin(t * 2.6 + boat.home.x * 5), boat.home.z);
      boat.group.rotation.z = 0.55 * smooth(clamp01(age / 0.5)) + 0.04 * Math.sin(t * 1.9 + boat.home.z);
      boat.mesh.material.opacity = 1 - gone;
      boat.mesh.castShadow = gone < 0.5;
    });
    // the basket appears with the boats gone, then shrinks
    const basketUp = popUp(t, T.more - 0.1, { height: 0.9, restZ: 0.1 });
    basket.set({ ...basketUp, scale: lerp(1, 0.55, smooth(ramp(t, T.fewer, T.fewer + 1.2))) });
    return { camera: shot(t), look: { aperture: 8, maxBlur: 14, exposure: 0.95, glowThreshold: 0.95, glowStrength: 0.6, contrast: 1.06 } };
  }

  // a hundred dots, all but one filled: under one in a hundred out of work
  function hundredDots(ctx, t, { at, until, x, y, gap = 44, radius = 13 }) {
    const a = presence(t, at, until, 0.3, 0.35);
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(12,16,18,0.55)';
    ctx.beginPath(); ctx.roundRect(x - 40, y - 40, gap * 9 + 80, gap * 9 + 80, 24); ctx.fill();
    for (let i = 0; i < 100; i++) {
      const col = i % 10, row = Math.floor(i / 10);
      const cx = x + col * gap, cy = y + row * gap;
      const k = clamp01((t - at - 0.15 - i * 0.012) / 0.25);
      if (k <= 0) continue;
      ctx.beginPath(); ctx.arc(cx, cy, radius * k, 0, Math.PI * 2);
      // the last dot is nearly empty: 0.95% of workers were out of work in 1915, just under one in a hundred
      if (i === 99) { ctx.strokeStyle = INK.paper; ctx.lineWidth = 3; ctx.stroke(); ctx.globalAlpha = a * 0.18; ctx.fillStyle = INK.amber; ctx.fill(); ctx.globalAlpha = a; }
      else { ctx.fillStyle = INK.amber; ctx.fill(); }
    }
    ctx.restore();
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    placeTitle(ctx, t, { at: T.britain, until: T.unemployment - 0.1, place: 'Britain', year: 1915, y: 260 });
    hook(ctx, t, { at: T.unemployment, until: T.newMoney - 0.3, text: '100 WORKERS', y: 250, size: 54, colour: INK.muted });
    hundredDots(ctx, t, { at: T.unemployment + 0.4, until: T.newMoney - 0.3, x: 342, y: 360 });
    // the one empty dot (bottom right, x 342 + 9 * 44, y 360 + 9 * 44) is the one out of work: label it,
    // pointing at the ring's lower-left edge so the leader's dot does not fill it
    callout(ctx, t, { at: T.under, until: T.newMoney - 0.3, point: { x: 342 + 9 * 44 - 12, y: 360 + 9 * 44 + 14 }, text: 'OUT OF WORK',
      dx: -70, dy: 96, size: 40, accent: INK.paper, plate: true });
    hook(ctx, t, { at: T.under, until: T.newMoney - 0.3, text: 'UNDER 1%', y: 990, size: 120 });
    hook(ctx, t, { at: T.newMoney, until: T.submarines + 0.2, text: 'NEW MONEY', y: 330, size: 92 });
    const top = stackBase.clone(); top.y += 0.5;
    callout(ctx, t, { at: T.submarines + 0.3, until: T.factories - 0.1, point: at(boats[1].home), text: 'SUPPLY SHIPS SUNK', dx: -40, dy: -330 });
    callout(ctx, t, { at: T.warWork - 0.1, until: T.more - 0.2, point: at(hall.pointAt(0.86, 0.36)), text: 'WAR WORK', dx: -220, dy: -300 });
    hook(ctx, t, { at: T.more, until: T.end - 0.2, lines: ['MORE MONEY'], y: 300, size: 84 });
    hook(ctx, t, { at: T.fewer, until: T.end - 0.2, lines: ['FEWER THINGS'], y: 400, size: 84, colour: INK.amber });
    bars(ctx, t, { at: T.end - 0.1, until: T.last + 2, box: [270, 330, 540, 420], values: [1, 2], labels: ['1914', '1918'], title: 'Prices',
      valueText: (v) => (v === 1 ? '×1' : '×2'), colours: [INK.paper, INK.red], stagger: T.doubled - T.end - 0.2, rise: 0.7 });
    return true;
  }

  return { pose, draw2D };
}
