// What this does: page 5 of chapter 2, "So test it". Two real tests of "new money alone pushes
// prices up", in two painted places:
//   Part A, Japan 2013 (a painted noodle-shop counter at night, lanterns glowing):
//   - "Japan, twenty thirteen": a place-and-year title.
//   - "the bank that creates the yen": a stack of banknote bundles (invented notes) lands on the
//     counter; "sets out to double the money": as many again drop onto it, the stack doubles;
//     ×2 MONEY / IN TWO YEARS. Beside it a bowl of ramen with a price tag (an illustrative ¥800)
//     that never changes.
//   - "If new money on its own pushed prices up, they'd soar": a chart, a dashed line IF MONEY ALONE
//     shooting up; "For eight years, they barely move": the real line drawn almost flat, ABOUT ½% A
//     YEAR.
//   Part B, after the 2008 crash (a quick dip to black on "After", then a painted Bank of England):
//   - "creates hundreds of billions of pounds": two towers of bundles rise on the plaza in front of
//     the bank; HUNDREDS OF BILLIONS OF POUNDS.
//   - "Its own study finds the new money pushed up the prices of shares and other investments": a
//     rising arrow, SHARES / OTHER INVESTMENTS; credit line BANK OF ENGLAND STUDY, 2012.
//   - "the gains went to whoever owned the most": the owners pop up in the foreground, the towers
//     slide over to them and gold coins rain at their feet; GAINS TO THE BIGGEST OWNERS.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, clamp01, smooth, smoother, ramp, lerp, seededRandom } from '../cinema-kit.js';
import { banknoteBundle, priceTag } from '../models.js';
import { Motes, Smoke, CoinRain } from '../effects.js';
import { placeTitle, hook, callout, credit, presence, INK } from '../graphics.js';

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    test: kit.at('test'),
    japan: kit.at('japan'),
    central: kit.at('central'),
    creates: kit.at('creates'),
    yen: kit.at('yen'),
    double: kit.at('double'),
    created: kit.at('created'),
    inTwo: kit.at('two'),
    years: kit.at('years'),
    if: kit.at('if'),
    newMoney: kit.at('new'),
    pushed: kit.at('pushed'),
    soar: kit.at('soar'),
    forEight: kit.at('for'),
    barely: kit.at('barely'),
    about: kit.at('about'),
    after: kit.at('after'),
    bank: kit.at('bank', 3),
    britains: kit.at("britain's"),
    creates2: kit.at('creates', 2),
    hundreds: kit.at('hundreds'),
    billions: kit.at('billions'),
    pounds: kit.at('pounds'),
    study: kit.at('study'),
    pushed2: kit.at('pushed', 2),
    shares: kit.at('shares'),
    investments: kit.at('investments'),
    gains: kit.at('gains'),
    went: kit.at('went'),
    owned: kit.at('owned'),
    last: kit.lastWordEnd,
  };
  // the cut between the two places: hidden by a quick dip to black just before "After"
  const CUT = T.after - 0.08;
  const partA = (t) => t < CUT;

  kit.lightRig({ keyColour: 0xffc98a, keyShare: 0.7, keyFrom: [-3, 6, -6], keyTarget: [-0.6, -1, -14], fillSky: 0x8a96a0, fillGround: 0x2a2018,
    fillShare: 0.22, haze: 0x161a1e, hazeDensity: 0.003, shadowBox: 7, shadowSoftness: 5, background: 0x0e1215, reflections: 0.3 });
  const { key, fill } = kit.lights;

  // ------------------------------------------------------------------ part A: the noodle shop
  const shop = await kit.relief('405-bg-noodle-shop', { near: 6, far: 70, fov: 40 });
  const stackBase = shop.pointAt(0.46, 0.36);
  stackBase.y = -1.15;
  const bowlAt = shop.pointAt(0.24, 0.31);
  bowlAt.y = -1.18;
  const random = seededRandom(51);
  const yenBundles = [];
  for (let i = 0; i < 10; i++) {
    const b = banknoteBundle({ width: 0.8, depth: 0.4, notes: 34 });
    b.group.traverse((o) => { if (o.material) [].concat(o.material).forEach((m) => { m.color.multiplyScalar(0.8); }); }); // notes read as green, not white, in this light
    b.group.rotation.y = 0.35 + (random() - 0.5) * 0.35;
    b.twist = (random() - 0.5) * 0.3;
    b.shift = [(random() - 0.5) * 0.06, (random() - 0.5) * 0.06];
    // the first five land on "creates the yen", the second five on "double the money"
    b.landAt = i < 5 ? T.creates + 0.05 + i * 0.13 : T.double + 0.1 + (i - 5) * 0.2;
    kit.scene.add(b.group);
    yenBundles.push(b);
  }
  const stackTop = (count) => stackBase.y + yenBundles.slice(0, count).reduce((h, b) => h + b.height, 0);

  // the bowl of ramen and its price tag (an illustrative menu price, the same all page long)
  const bowl = await kit.cutout('ramen-bowl', { at: [bowlAt.x, bowlAt.y, bowlAt.z], width: 0.95, yaw: 0.2 });
  const tag = priceTag({ width: 0.5, text: '¥800' });
  tag.group.position.set(bowlAt.x + 0.36, bowlAt.y + 0.5, bowlAt.z + 0.2);
  tag.group.rotation.set(0, 0.2, -0.32);
  kit.scene.add(tag.group);
  const steam = new Smoke(kit.scene, { count: 8, life: 2.8, seed: 12, colour: [222, 214, 200] });
  const shopMotes = new Motes(kit.scene, { count: 140, min: [-2.2, -1.2, -16], max: [1.6, 2.4, -6], size: 0.028, seed: 15, opacity: 0.45, colour: 0xffe2b0 });

  // ------------------------------------------------------------- part B: the Bank of England
  const plaza = await kit.relief('406-bg-london-bank', { near: 6, far: 70, fov: 40 });
  const towerBases = [plaza.pointAt(0.27, 0.29), plaza.pointAt(0.73, 0.29)];
  const towers = towerBases.map((base, side) => {
    const r = seededRandom(70 + side);
    const bundles = [];
    for (let i = 0; i < 18; i++) {
      const b = banknoteBundle({ width: 0.8, depth: 0.4, notes: 44 });
      b.group.traverse((o) => { if (o.material) [].concat(o.material).forEach((m) => { m.color.multiplyScalar(0.8); }); }); // notes read as green, not white, in this light
      b.group.scale.setScalar(1.15);
      b.height *= 1.15;
      b.group.rotation.y = (r() - 0.5) * 0.4;
      b.twist = (r() - 0.5) * 0.3;
      b.shift = [(r() - 0.5) * 0.08, (r() - 0.5) * 0.08];
      b.landAt = T.creates2 - 0.05 + i * 0.095 + side * 0.05;
      kit.scene.add(b.group);
      bundles.push(b);
    }
    return { base, bundles };
  });
  // the owners: invented top-hatted figures, standing big in the foreground
  const ownersAt = plaza.pointAt(0.5, 0.155);
  const owners = await kit.cutout('owners', { at: [ownersAt.x, ownersAt.y, ownersAt.z], width: 3.0 });
  // where the towers end up: either side of the owners, just behind them
  const towerEnds = [new THREE.Vector3(ownersAt.x - 1.25, ownersAt.y, ownersAt.z - 1.6), new THREE.Vector3(ownersAt.x + 1.25, ownersAt.y, ownersAt.z - 1.6)];
  const gold = new CoinRain(kit.scene, { count: 26, centre: [ownersAt.x, ownersAt.y, ownersAt.z + 0.55], radius: 1.1, floorY: ownersAt.y,
    height: 5, start: T.owned - 0.1, spread: 0.9, coinRadius: 0.075, seed: 23 });
  const plazaMotes = new Motes(kit.scene, { count: 120, min: [-2.5, -2.2, -18], max: [2.5, 2.5, -7], size: 0.03, seed: 29, opacity: 0.35, colour: 0xdfe6ee });

  // ------------------------------------------------------------------------------ the camera
  const stackFocus = [stackBase.x, stackBase.y + 0.6, stackBase.z];
  const shotA = kit.shot([
    { t: T.start, position: [0, 0.15, 0.6], target: [0, -0.3, -30], fov: 40, focus: 12 },
    { t: T.creates - 0.3, position: [-0.1, 0.05, -0.2], target: [-0.3, -0.4, -24], fov: 38, focus: stackFocus },
    { t: T.double + 1.2, position: [-0.2, 0.0, -0.7], target: [-0.4, -0.3, -24], fov: 36, focus: stackFocus },
    { t: T.forEight, position: [-0.25, 0.0, -0.9], target: [-0.4, -0.25, -24], fov: 36, focus: [bowlAt.x, bowlAt.y + 0.4, bowlAt.z] },
    { t: CUT + 0.6, position: [-0.3, 0.0, -1.1], target: [-0.4, -0.25, -24], fov: 36, focus: [bowlAt.x, bowlAt.y + 0.4, bowlAt.z] },
  ], { handheld: 0.012, seed: 5 });
  const shotB = kit.shot([
    { t: CUT - 0.5, position: [0, 0.05, 0.8], target: [0, 0.2, -30], fov: 40, focus: 30 },
    { t: T.creates2 - 0.2, position: [0, -0.05, 0.2], target: [0, 0.1, -30], fov: 40, focus: 16 },
    { t: T.pounds + 0.4, position: [0, 0.1, -0.4], target: [0, 0.7, -30], fov: 40, focus: 16 },
    { t: T.gains - 0.1, position: [0, 0.0, -0.5], target: [0, 0.3, -30], fov: 40, focus: 15 },
    { t: T.owned, position: [0, -0.15, 0.2], target: [0, -0.4, -30], fov: 41, focus: [ownersAt.x, ownersAt.y + 1, ownersAt.z] },
    { t: T.last + 1.4, position: [0, -0.2, 0.5], target: [0, -0.5, -30], fov: 41, focus: [ownersAt.x, ownersAt.y + 1, ownersAt.z] },
  ], { handheld: 0.012, seed: 6 });
  kit.shake(T.double + 0.1, 0.008, 0.15);
  kit.shake(T.creates2 + 0.3, 0.01, 0.2);

  // a bundle falling onto a stack at landAt, resting at restY
  function dropBundle(b, t, x, restY, z, fall = 0.4, drop = 3) {
    const k = clamp01((t - (b.landAt - fall)) / fall);
    b.group.visible = t >= b.landAt - fall;
    b.group.position.set(x + b.shift[0], restY + drop * (1 - k * k), z + b.shift[1]);
    const settle = t > b.landAt ? Math.exp(-(t - b.landAt) * 10) * Math.sin((t - b.landAt) * 30) * 0.05 : 0;
    b.group.rotation.z = b.twist * (1 - k) + settle;
  }

  function pose(t) {
    const a = partA(t);
    shop.mesh.visible = a;
    plaza.mesh.visible = !a;
    // the lamp: warm lantern light on the counter, then a cooler evening light on the plaza
    if (a) {
      key.color.set(0xffc98a); key.intensity = Math.PI * 0.7;
      key.position.set(-3, 6, -6); key.target.position.set(-0.6, -1, -14);
      fill.color.set(0x8a96a0); fill.groundColor.set(0x2a2018);
    } else {
      key.color.set(0xffe0b8); key.intensity = Math.PI * 0.75;
      key.position.set(4, 9, -4); key.target.position.set(0, -2, -13);
      fill.color.set(0x9fb0c2); fill.groundColor.set(0x30302c);
    }
    key.target.updateMatrixWorld();

    // part A things
    let height = 0;
    yenBundles.forEach((b) => {
      if (!a) { b.group.visible = false; return; }
      dropBundle(b, t, stackBase.x, stackBase.y + height, stackBase.z, 0.38, 2.4);
      height += b.height;
    });
    bowl.set(a ? { visible: true } : { visible: false });
    tag.group.visible = a;
    tag.group.rotation.z = -0.32 + 0.025 * Math.sin(t * 1.3);
    if (a) steam.set({ t, origin: [bowlAt.x + 0.05, bowlAt.y + 0.35, bowlAt.z], scale: 0.32, wind: 0.15 }); else steam.hide();
    shopMotes.set(t, { visible: a });

    // part B things
    const slide = smoother(ramp(t, T.went - 0.1, T.went + 1.0));
    towers.forEach((tower, side) => {
      let h = 0;
      const base = tower.base.clone().lerp(towerEnds[side], slide);
      // a little hop as the stack sets off and lands
      base.y += 0.12 * Math.sin(Math.PI * slide);
      tower.bundles.forEach((b) => {
        if (a) { b.group.visible = false; return; }
        dropBundle(b, t, base.x, base.y + h, base.z, 0.36, 4);
        b.group.rotation.x = -0.08 * Math.sin(Math.PI * slide) * (side ? 1 : 1);
        h += b.height;
      });
    });
    owners.set(a ? { visible: false } : popUp(t, T.gains - 0.05, { height: 1.7, restZ: 0.2 }));
    gold.pose(t, { visible: !a });
    plazaMotes.set(t, { visible: !a });

    // the dip to black that hides the cut
    const fade = Math.max(0, 1 - Math.abs(t - CUT) / 0.24);
    const look = a
      ? { aperture: 8, maxBlur: 14, exposure: 0.95, glowThreshold: 0.92, glowStrength: 0.7, contrast: 1.06, fade }
      : { aperture: 7, maxBlur: 12, exposure: 0.95, glowThreshold: 0.93, glowStrength: 0.62, contrast: 1.06, fade };
    return { camera: a ? shotA(t) : shotB(t), look };
  }

  // ------------------------------------------------------------------------------ 2D graphics
  // "If new money on its own pushed prices up": a dashed line shooting up; then the real line, flat.
  function pricesChart(ctx, t, { at, until, box }) {
    const a = presence(t, at, until, 0.3, 0.4);
    if (a <= 0) return;
    const [bx, by, bw, bh] = box;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(12,16,18,0.6)';
    ctx.beginPath(); ctx.roundRect(bx - 70, by - 120, bw + 130, bh + 210, 26); ctx.fill();
    ctx.fillStyle = INK.paper; ctx.font = '700 38px Inter'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    ctx.fillText('PRICES IN JAPAN', bx, by - 50);
    ctx.strokeStyle = 'rgba(242,237,227,0.35)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.stroke();
    ctx.fillStyle = INK.muted; ctx.font = '600 30px Inter'; ctx.textBaseline = 'top';
    ctx.textAlign = 'left'; ctx.fillText('2013', bx - 10, by + bh + 14);
    ctx.textAlign = 'right'; ctx.fillText('8 YEARS', bx + bw, by + bh + 14);
    const baseY = by + bh * 0.82;
    // what new money on its own would do: a curve that runs off the top (no numbers: it never happened)
    const ifK = clamp01((t - T.newMoney) / (T.soar + 0.3 - T.newMoney));
    if (ifK > 0) {
      ctx.save();
      ctx.beginPath(); ctx.rect(bx, by - 40, bw + 40, bh + 40); ctx.clip();
      ctx.setLineDash([22, 16]); ctx.strokeStyle = INK.red; ctx.lineWidth = 7; ctx.lineCap = 'round';
      ctx.shadowColor = INK.red; ctx.shadowBlur = 16;
      ctx.beginPath();
      const steps = 40;
      for (let i = 0; i <= steps * ifK; i++) {
        const u = i / steps;
        const x = bx + u * bw * 0.62, y = baseY - (Math.pow(u, 2.2) * (bh * 0.82 + 60));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.restore();
      ctx.globalAlpha = a * clamp01((t - T.pushed) / 0.3);
      ctx.fillStyle = INK.red; ctx.font = '800 40px Inter'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
      ctx.shadowColor = INK.shadow; ctx.shadowBlur = 14;
      ctx.fillText('IF MONEY ALONE', bx + bw * 0.62 - 50, by + 10);
      ctx.globalAlpha = a;
    }
    // the real prices: about half a percent a year, so barely off the line over eight years
    const realK = clamp01((t - T.forEight) / (T.barely + 0.5 - T.forEight));
    if (realK > 0) {
      ctx.strokeStyle = INK.amber; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.setLineDash([]);
      ctx.shadowColor = INK.amber; ctx.shadowBlur = 18;
      const rise = bh * 0.82 * 0.04; // 1.005^8 ≈ 1.04, on a scale where the dashed curve passes ×2
      ctx.beginPath(); ctx.moveTo(bx, baseY);
      const endX = bx + bw * realK;
      ctx.lineTo(endX, baseY - rise * realK);
      ctx.stroke();
      if (realK < 1) { ctx.fillStyle = '#fff6e0'; ctx.beginPath(); ctx.arc(endX, baseY - rise * realK, 12, 0, Math.PI * 2); ctx.fill(); }
      ctx.shadowBlur = 0;
      ctx.globalAlpha = a * clamp01((t - T.barely) / 0.3);
      ctx.fillStyle = INK.amber; ctx.font = '800 40px Inter'; ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
      ctx.shadowColor = INK.shadow; ctx.shadowBlur = 14;
      ctx.fillText('REAL PRICES', bx + bw, baseY - rise - 26);
    }
    ctx.restore();
  }

  // "pushed up the prices of shares and other investments": a climbing arrow, no numbers
  function risingArrow(ctx, t, { at, until, box }) {
    const a = presence(t, at, until, 0.3, 0.4);
    if (a <= 0) return;
    const [bx, by, bw, bh] = box;
    const points = [[0, 0.05], [0.18, 0.2], [0.3, 0.14], [0.48, 0.38], [0.6, 0.32], [0.78, 0.62], [0.88, 0.58], [1, 0.92]];
    const k = clamp01((t - at - 0.15) / 1.3);
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(12,16,18,0.55)';
    ctx.beginPath(); ctx.roundRect(bx - 50, by - 50, bw + 100, bh + 100, 26); ctx.fill();
    const px = (p) => bx + p[0] * bw, py = (p) => by + bh - p[1] * bh;
    const upto = k * (points.length - 1);
    ctx.strokeStyle = INK.amber; ctx.lineWidth = 10; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.shadowColor = INK.amber; ctx.shadowBlur = 18;
    ctx.beginPath(); ctx.moveTo(px(points[0]), py(points[0]));
    let hx = px(points[0]), hy = py(points[0]), dirX = 1, dirY = 0;
    for (let i = 1; i <= Math.ceil(upto) && i < points.length; i++) {
      const f = Math.min(1, upto - (i - 1));
      const x0 = px(points[i - 1]), y0 = py(points[i - 1]), x1 = px(points[i]), y1 = py(points[i]);
      hx = lerp(x0, x1, f); hy = lerp(y0, y1, f); dirX = x1 - x0; dirY = y1 - y0;
      ctx.lineTo(hx, hy);
    }
    ctx.stroke();
    if (k > 0.02) {
      const len = Math.hypot(dirX, dirY) || 1, ux = dirX / len, uy = dirY / len;
      ctx.fillStyle = INK.amber;
      ctx.beginPath(); ctx.moveTo(hx + ux * 30, hy + uy * 30);
      ctx.lineTo(hx - ux * 10 - uy * 22, hy - uy * 10 + ux * 22); ctx.lineTo(hx - ux * 10 + uy * 22, hy - uy * 10 - ux * 22); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    if (partA(t)) {
      placeTitle(ctx, t, { at: T.japan, until: T.double - 0.15, place: 'Japan', year: 2013, y: 260 });
      callout(ctx, t, { at: T.yen, until: T.double - 0.1, point: at([stackBase.x, stackTop(5) + 0.05, stackBase.z]), text: 'YEN', dx: 120, dy: -260, size: 52 });
      hook(ctx, t, { at: T.double, until: T.if - 0.2, text: '×2 MONEY', y: 300, size: 120 });
      hook(ctx, t, { at: T.inTwo, until: T.if - 0.2, text: 'IN TWO YEARS', y: 420, size: 64, colour: INK.amber });
      pricesChart(ctx, t, { at: T.if - 0.1, until: CUT - 0.1, box: [190, 300, 700, 330] });
      hook(ctx, t, { at: T.about, until: CUT - 0.1, text: 'ABOUT ½% A YEAR', y: 790, size: 64, colour: INK.amber });
    } else {
      placeTitle(ctx, t, { at: CUT + 0.2, until: T.creates2 - 0.1, place: 'After the crash', year: 2008, y: 260, size: 44 });
      hook(ctx, t, { at: T.bank, until: T.creates2 - 0.1, text: 'BANK OF ENGLAND', y: 400, size: 76 });
      hook(ctx, t, { at: T.britains + 0.1, until: T.creates2 - 0.1, text: "BRITAIN'S CENTRAL BANK", y: 490, size: 46, colour: INK.muted });
      hook(ctx, t, { at: T.hundreds, until: T.study - 0.2, lines: ['HUNDREDS OF', 'BILLIONS'], y: 330, size: 104 });
      hook(ctx, t, { at: T.pounds, until: T.study - 0.2, text: 'OF POUNDS', y: 500, size: 70, colour: INK.amber });
      credit(ctx, t, { at: T.study, until: T.last + 2, text: 'Bank of England study, 2012', y: 180 });
      risingArrow(ctx, t, { at: T.pushed2 - 0.1, until: T.gains - 0.15, box: [210, 330, 560, 380] });
      hook(ctx, t, { at: T.shares, until: T.gains - 0.15, text: 'SHARES ↑', y: 840, size: 78 });
      hook(ctx, t, { at: T.investments, until: T.gains - 0.15, text: 'OTHER INVESTMENTS ↑', y: 940, size: 58, colour: INK.amber });
      hook(ctx, t, { at: T.gains, until: T.last + 2, text: 'THE GAINS', y: 300, size: 96, colour: INK.amber });
      hook(ctx, t, { at: T.owned - 0.1, until: T.last + 2, lines: ['TO THE BIGGEST', 'OWNERS'], y: 450, size: 82 });
    }
    return true;
  }

  return { pose, draw2D };
}
