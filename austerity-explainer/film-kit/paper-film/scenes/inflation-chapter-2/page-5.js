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
//   - "the gains went to whoever owned the most": no figure; the money itself shows it. Gold coins
//     pour onto ONE of the two towers of notes and more bundles land on it, so it grows clearly
//     taller than the other; THE GAINS / TO THE BIGGEST OWNERS.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, clamp01, smooth, smoother, ramp, lerp, seededRandom } from '../cinema-kit.js';
import { banknoteBundle, priceTag, coin, contactShadow } from '../models.js';
import { Motes, Smoke } from '../effects.js';
import { placeTitle, hook, callout, credit, presence, INK } from '../graphics.js';

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    test: kit.at('test'),
    japan: kit.at('japan'),
    central: kit.at('central'),
    creates: kit.at('creates'),
    yen: kit.at('yen'),
    sets: kit.at('sets'),
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
  stackBase.y = -1.09;   // just on the painted counter top (at -1.15 its bottom bundle sank into it)
  const bowlAt = shop.pointAt(0.24, 0.31);
  bowlAt.y = -1.11;   // on the painted counter top, not into it
  bowlAt.z += 0.4;    // a little forward on the counter: the bigger bowl stays clear of the painted back of the counter
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
  const bowl = await kit.cutout('ramen-bowl', { at: [bowlAt.x, bowlAt.y, bowlAt.z], width: 1.2, yaw: 0.2 });
  const tag = priceTag({ width: 0.44, text: '¥800' });
  tag.group.position.set(bowlAt.x - 0.5, bowlAt.y + 0.5, bowlAt.z + 0.25);   // hung on the bowl's left side, clear of the stack of yen
  tag.group.rotation.set(0, 0.2, -0.5);
  kit.scene.add(tag.group);
  const steam = new Smoke(kit.scene, { count: 8, life: 2.8, seed: 12, colour: [222, 214, 200] });
  const shopMotes = new Motes(kit.scene, { count: 140, min: [-2.2, -1.2, -16], max: [1.6, 2.4, -6], size: 0.028, seed: 15, opacity: 0.45, colour: 0xffe2b0 });

  // ------------------------------------------------------- part B: a City of London bank street
  // a dry painting (no wet reflections the 3D money could not match): the bank at an angle on the
  // left, open flagstones on the right and across the bottom. The towers stand on that pavement.
  const plaza = await kit.relief('406b-bg-london-bank-dry', { near: 6, far: 70, fov: 40 });
  // the floor under a spot: its point and its slope (the angle the flagstones rise toward us)
  const floorAt = (u, v) => {
    const p = plaza.pointAt(u, v), q = plaza.pointAt(u, v + 0.02);
    return { point: p, slope: Math.atan2(p.y - q.y, p.z - q.z) };   // rise per unit toward the camera
  };
  // the painted floor's height at a world spot (x, z): find the spot on the painting whose floor point
  // lies there (z grows toward us as v falls, so a bisection on v)
  const floorHeight = (x, z) => {
    let lo = 0, hi = 0.3, p = null;
    for (let i = 0; i < 30; i++) {
      const v = (lo + hi) / 2;
      p = plaza.pointAt(0.5 + x / (-z) / plaza.tanX / 2, v);
      if (p.z < z) hi = v; else lo = v;
    }
    return p.y;
  };
  // the highest floor point under a disc of radius r (so a thing resting there never sinks in)
  const floorUnder = (x, z, r) => {
    let top = -Infinity;
    for (let i = 0; i <= 12; i++) {
      const a = (i / 12) * Math.PI * 2, rr = i === 12 ? 0 : r;
      top = Math.max(top, floorHeight(x + rr * Math.cos(a), z + rr * Math.sin(a)));
    }
    return top;
  };
  const BUNDLE = 1.15, FIRST = 9, GROW = 6;
  const towers = [floorAt(0.3, 0.12), floorAt(0.7, 0.12)].map((floor, side) => {
    const base = floor.point.clone();
    base.y += 0.03;   // the front edge of a bundle meets the slightly rising flagstones: lift so it never sinks in
    const r = seededRandom(70 + side);
    const bundles = [];
    const count = FIRST + (side === 1 ? GROW : 0);
    for (let i = 0; i < count; i++) {
      const b = banknoteBundle({ width: 0.8, depth: 0.4, notes: 44 });
      b.group.traverse((o) => { if (o.material) [].concat(o.material).forEach((m) => { m.color.multiplyScalar(0.8); }); }); // notes read as green, not white, in this light
      b.group.scale.setScalar(BUNDLE);
      b.height *= BUNDLE;
      b.group.rotation.y = (r() - 0.5) * 0.3;
      b.twist = (r() - 0.5) * 0.3;
      b.shift = [(r() - 0.5) * 0.06, (r() - 0.5) * 0.06];
      // the first ones land on "creates hundreds of billions"; on the right tower, more land on
      // "the gains went", so it grows clearly taller than the left one
      b.landAt = i < FIRST ? T.creates2 - 0.05 + i * 0.13 + side * 0.06 : T.went - 0.1 + (i - FIRST) * 0.14;
      kit.scene.add(b.group);
      bundles.push(b);
    }
    // a soft contact shadow under the tower, lying on the flagstones (tilted with them)
    const shadow = contactShadow(1.5, 0.95, 0.75);
    const shadowHolder = new THREE.Group();
    shadowHolder.add(shadow);
    shadowHolder.position.set(floor.point.x, floor.point.y + 0.012, floor.point.z);
    shadowHolder.rotation.x = -floor.slope;
    kit.scene.add(shadowHolder);
    return { base, bundles, floor, shadowHolder };
  });
  const rich = towers[1];
  const richTop = rich.base.y + rich.bundles.reduce((h, b) => h + b.height, 0);
  const lastBundle = rich.bundles[rich.bundles.length - 1];
  // the gold coins: they pour down by the rich tower. Each one falls straight down onto its own spot
  // and stays there: before the tower has finished growing they land in little stacks on the
  // flagstones at its foot; after, on its top. Every coin rests exactly on the surface or coin below.
  const COIN_R = 0.13, COIN_T = 0.03;
  const pour = [];
  let coinFloorSpots = [];
  {
    const r = seededRandom(23);
    const floorSpots = [];
    // spots in front of and beside the tower's foot, clear of its footprint (a bundle reaches at most
    // about 0.33 forward and 0.5 sideways of its centre; a coin is 0.13 across its radius)
    [[-0.45, 0.6], [-0.15, 0.62], [0.15, 0.6], [0.45, 0.62], [-0.3, 0.9], [0.0, 0.92], [0.3, 0.9], [0.75, 0.3], [0.78, 0.0], [-0.76, 0.3], [0.6, 0.85]]
      .forEach(([dx, dz]) => { const x = rich.floor.point.x + dx, z = rich.floor.point.z + dz; floorSpots.push({ x, y: floorUnder(x, z, COIN_R + 0.02), z, slope: 0, count: 0 }); });
    // spots on the top of the tower (inside the top bundle's face, 0.3 apart so stacks never touch)
    const topSpots = [[-0.3, -0.03], [0, 0.04], [0.3, -0.03]]
      .map(([dx, dz]) => ({ x: rich.base.x + lastBundle.shift[0] + dx, y: richTop + 0.006, z: rich.base.z + lastBundle.shift[1] + dz, slope: 0, count: 0 }));
    const count = 56, from = T.gains + 0.05, to = T.last + 0.6;
    const topFrom = lastBundle.landAt + 0.35;
    for (let i = 0; i < count; i++) {
      const c = coin({ radius: COIN_R, thickness: COIN_T });
      kit.scene.add(c.group);
      const land = from + (i / count) * (to - from) + r() * 0.03;
      const spots = land > topFrom && i % 3 !== 0 ? topSpots : floorSpots;
      const spot = spots[Math.floor(r() * spots.length)];
      const layer = spot.count++;
      pour.push({ group: c.group, mesh: c.group.children[0], land, spot, restY: spot.y + COIN_T * (layer + 0.5) + 0.004 + layer * 0.001,
        drop: 2.2 + r() * 0.8, spin: 6 + r() * 8, tilt0: r() * Math.PI, yaw: r() * Math.PI * 2 });
    }
    // small shadows under the coin stacks on the flagstones
    floorSpots.filter((s) => s.count > 0).forEach((s) => {
      const holder = new THREE.Group(); holder.add(contactShadow(0.42, 0.3, 0.55));
      holder.position.set(s.x, s.y + 0.006, s.z); holder.rotation.x = -s.slope;
      s.shadow = holder; kit.scene.add(holder);
      s.firstLand = Math.min(...pour.filter((c) => c.spot === s).map((c) => c.land));
    });
    coinFloorSpots = floorSpots;
  }
  const plazaMotes = new Motes(kit.scene, { count: 120, min: [-2.5, -2.2, -14], max: [2.5, 2.5, -6], size: 0.03, seed: 29, opacity: 0.35, colour: 0xdfe6ee });

  // ------------------------------------------------------------------------------ the camera
  // The camera rule: still unless a move lands the point; at most three moves per shot.
  // Shot 1, the noodle shop: it holds on the counter (the empty spot where the money will land, the
  // bowl and its price); one zoom in as the bank "sets out to double the money", narrowing onto the
  // stack as it doubles; then it holds. Focus slides to the bowl for "they barely move" (free).
  const stackFocus = [stackBase.x, stackBase.y + 0.6, stackBase.z];
  const bowlFocus = [bowlAt.x, bowlAt.y + 0.4, bowlAt.z];
  const shotA = kit.stillShot({ position: [-0.45, -0.1, -0.6], target: [-0.75, 1.1, -24], fov: 32, focus: stackFocus }, [
    { from: T.sets - 0.1, to: T.double + 0.6, kind: 'zoom in', position: [-0.5, -0.2, -1.4], target: [-0.6, 0.45, -24], fov: 30 },
    { from: T.forEight, to: T.forEight + 0.6, kind: 'focus', focus: bowlFocus },
  ], { name: 'the noodle shop' });
  // Shot 2, the bank street: it holds low on the pavement with the bank behind while both towers
  // rise; on "the gains went to whoever owned the most" one zoom in narrows onto the rich tower as it
  // grows and the coins pour down by it; then it holds to the end.
  const richFocus = [rich.base.x, rich.base.y + 1.4, rich.base.z];
  // It stands 0.7 in from the painting's eye point: from further back (at the origin, a little below
  // the eye line) the frame saw past the painting's bottom edge and a black band ran along the bottom.
  // At z -0.7 that edge (and its mirrored margin) lies below the frame (frame_check: y 1978 of 1920).
  const shotB = kit.stillShot({ position: [0, -0.4, -0.7], target: [0, -0.8, -30], fov: 40, focus: 9.2 }, [
    { from: T.gains - 0.1, to: T.went + 0.8, kind: 'zoom in', position: [0.14, -0.4, -1.5], target: [-0.12, -0.9, -30], fov: 37, focus: richFocus },
  ], { name: 'the bank street' });
  kit.shake(T.double + 0.1, 0.008, 0.15);
  kit.shake(T.creates2 + 0.3, 0.008, 0.2);

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
    tag.group.rotation.z = -0.5 + 0.025 * Math.sin(t * 1.3);
    if (a) steam.set({ t, origin: [bowlAt.x + 0.06, bowlAt.y + 0.44, bowlAt.z], scale: 0.38, wind: 0.15 }); else steam.hide();
    shopMotes.set(t, { visible: a });

    // part B things
    towers.forEach((tower) => {
      let h = 0;
      const base = tower.base;
      tower.shadowHolder.visible = !a && t >= tower.bundles[0].landAt - 0.05;
      tower.bundles.forEach((b) => {
        if (a) { b.group.visible = false; return; }
        dropBundle(b, t, base.x, base.y + h, base.z, 0.36, 2.6);
        h += b.height;
      });
    });
    // the coins: each falls straight down onto its spot (the flagstones, the coin below it, or the
    // top of the rich tower) and stays there, lying with the slope of the surface
    pour.forEach((c) => {
      const fall = Math.sqrt(2 * c.drop / 30), age = t - c.land;
      if (a || age < -fall) { c.group.visible = false; return; }
      c.group.visible = true;
      // its shadow shows only once it has landed (so no shadow ovals on the towers while it falls)
      c.mesh.castShadow = age >= 0;
      if (age < 0) {
        const k = 1 + age / fall;
        c.group.position.set(c.spot.x, c.restY + c.drop * (1 - k * k), c.spot.z);
        // it tumbles as it falls but comes in flat: the tilt fades out over the last quarter second,
        // faster than it drops, so its rim never reaches below the surface
        const tumble = (Math.PI / 2) * Math.sin(c.tilt0 + age * c.spin) * smooth(clamp01(-age / 0.25));
        c.group.rotation.set(-c.spot.slope + tumble, c.yaw, 0, 'XYZ');
      } else {
        // a tiny hop just after landing (always upward from the resting height), then still
        const hop = 0.025 * Math.exp(-age / 0.06) * Math.abs(Math.sin(Math.PI * age / 0.1));
        c.group.position.set(c.spot.x, c.restY + hop, c.spot.z);
        c.group.rotation.set(-c.spot.slope, c.yaw, 0, 'XYZ');
      }
    });
    coinFloorSpots.forEach((s) => { if (s.shadow) s.shadow.visible = !a && t >= s.firstLand; });
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
    ctx.textAlign = 'right'; ctx.fillText('2021', bx + bw, by + bh + 14);
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

  // a dark rounded plate behind words over pale or busy parts of the picture
  function plate(ctx, t, { at, until, x, y, w, h, grow }) {
    const a = presence(t, at, until, 0.12, 0.3);
    if (a <= 0) return;
    // grow: { at, h, y } lets the plate reach down to take a second line when it appears
    if (grow) { const k = smooth(clamp01((t - grow.at) / 0.25)); h = lerp(h, grow.h, k); y = lerp(y, grow.y, k); }
    ctx.save(); ctx.globalAlpha = a * 0.72; ctx.fillStyle = 'rgb(12,16,18)';
    ctx.beginPath(); ctx.roundRect(x - w / 2, y - h / 2, w, h, 28); ctx.fill();
    ctx.restore();
  }
  // the source credit, in paper white so it reads over the sky
  function sourceCredit(ctx, t, { at, until, text, lines, x = 84, y = 180, size = 34, gap = 1.25 }) {
    const a = presence(t, at, until, 0.3, 0.4);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a;
    ctx.shadowColor = INK.shadow; ctx.shadowBlur = 16; ctx.shadowOffsetY = 3;
    ctx.fillStyle = INK.paper; ctx.font = `700 ${size}px Inter`; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    ctx.letterSpacing = '3px';
    (lines ?? [text]).forEach((row, i) => ctx.fillText(row.toUpperCase(), x, y + i * size * gap));
    ctx.restore();
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    if (partA(t)) {
      placeTitle(ctx, t, { at: T.japan, until: T.double - 0.15, place: 'Japan', year: 2013, y: 260 });
      // the line starts early so its label is up by the word "yen"
      callout(ctx, t, { at: T.creates + 0.62, until: T.double - 0.1, point: at([stackBase.x, stackTop(5) + 0.05, stackBase.z]), text: 'YEN', dx: 120, dy: -260, size: 52, plate: true });
      // on the left, clear of the bundles falling onto the stack (on screen x 500-850 all the way up);
      // the plate fits ×2 MONEY, then reaches down for IN TWO YEARS when she says it
      plate(ctx, t, { at: T.double, until: T.if - 0.2, x: 250, y: 335, w: 400, h: 250, grow: { at: T.inTwo, h: 340, y: 380 } });
      hook(ctx, t, { at: T.double, until: T.if - 0.2, text: '×2', x: 250, y: 280, size: 130 });
      hook(ctx, t, { at: T.double + 0.1, until: T.if - 0.2, text: 'MONEY', x: 250, y: 400, size: 84 });
      hook(ctx, t, { at: T.inTwo, until: T.if - 0.2, text: 'IN TWO YEARS', x: 250, y: 492, size: 48 });
      // the ¥800 is invented: say so, as pages 1 and 3 do (above the bowl, left of the stack)
      credit(ctx, t, { at: T.japan, until: CUT - 0.1, text: 'Example price', x: 84, y: 1050, size: 28, plate: true });
      pricesChart(ctx, t, { at: T.if - 0.1, until: CUT - 0.1, box: [190, 300, 700, 330] });
      // just under the chart, above the stack of yen and the bowl
      plate(ctx, t, { at: T.about, until: CUT - 0.1, x: 540, y: 775, w: 700, h: 110 });
      hook(ctx, t, { at: T.about, until: CUT - 0.1, text: 'ABOUT ½% A YEAR', y: 797, size: 64, colour: INK.amber });
    } else {
      placeTitle(ctx, t, { at: CUT + 0.2, until: T.creates2 - 0.1, place: 'After the crash', year: 2008, y: 260, size: 44 });
      hook(ctx, t, { at: T.bank, until: T.creates2 - 0.1, text: 'BANK OF ENGLAND', y: 400, size: 76 });
      plate(ctx, t, { at: T.britains + 0.1, until: T.creates2 - 0.1, x: 540, y: 490, w: 700, h: 76 });
      hook(ctx, t, { at: T.britains + 0.1, until: T.creates2 - 0.1, text: 'BRITAIN’S CENTRAL BANK', y: 490, size: 46 });
      hook(ctx, t, { at: T.hundreds, until: T.study - 0.2, lines: ['HUNDREDS OF', 'BILLIONS'], y: 330, size: 104 });
      hook(ctx, t, { at: T.pounds, until: T.study - 0.2, text: 'OF POUNDS', y: 500, size: 70, colour: INK.amber });
      // two short lines on the left (x 84-470): the bundles that land later all fall onto the right
      // tower (on screen x 530 and right), so none crosses it; its top sits at y ~197
      sourceCredit(ctx, t, { at: T.study, until: T.last + 2, lines: ['Bank of England', 'study, 2012'], y: 220, size: 32, gap: 1.2 });
      risingArrow(ctx, t, { at: T.pushed2 - 0.1, until: T.gains - 0.15, box: [210, 335, 560, 320] });   // kept above the tower tops (the camera now stands closer)
      plate(ctx, t, { at: T.shares, until: T.gains - 0.15, x: 540, y: 828, w: 820, h: 176 });
      hook(ctx, t, { at: T.shares, until: T.gains - 0.15, text: 'SHARES ↑', y: 788, size: 74 });
      hook(ctx, t, { at: T.investments - 0.12, until: T.gains - 0.15, text: 'OTHER INVESTMENTS ↑', y: 873, size: 56 });
      hook(ctx, t, { at: T.gains, until: T.last + 2, text: 'THE GAINS', x: 54, y: 345, size: 88, colour: INK.amber, align: 'left' });
      hook(ctx, t, { at: T.owned - 0.1, until: T.last + 2, lines: ['TO THE BIGGEST', 'OWNERS'], x: 54, y: 480, size: 62, align: 'left' });
    }
    return true;
  }

  return { pose, draw2D };
}
