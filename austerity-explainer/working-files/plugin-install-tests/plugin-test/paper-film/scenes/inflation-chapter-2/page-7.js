// What this does: page 7 of chapter 2, "the oil shock, and now". Two places, one cut.
//   Part A, late 1973: we stand on the forecourt of a painted petrol station at night (a painting
//   with depth), cars queueing at the pumps under the canopy lights.
//   - "Late 1973": a place-and-year title. "Prices are already climbing": a label on the pumps.
//   - "the price of oil nearly quadruples": a heavy oil barrel drops onto the forecourt (shake,
//     dust); a split-flap counter rises on its lid at $2.90 and flips up to $11.65 a barrel; ×4,
//     IN ABOUT 3 MONTHS.
//   - "almost everything made or moved with fuel gets dearer": a row of price tags lying on the
//     concrete flips upright one after another like dominoes, each printed with an up arrow; DEARER.
//   - "the cause isn't spending. It's costs.": NOT SPENDING (dimmed, struck through), then COSTS.
//   Part B, "And here?": a quick dip to black and we are on a sunny New Zealand street (a second
//   painting). NEW ZEALAND 2026; two bars: prices rose 4.1% in the year to June, 2.9% without fuel.
//   Small credit: Stats NZ.
// Facts: C2-C14 (oil $2.90 to $11.65 a barrel, nearly quadrupled in about three months, late 1973),
// C2-N05 (NZ CPI 4.1% in the year to the June 2026 quarter; 2.9% without fuel).
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, clamp01, smooth, smoother, ramp, lerp, spring, seededRandom, degrees } from '../cinema-kit.js';
import { oilBarrel, splitFlap, countSchedule, priceTag } from '../models.js';
import { Motes, DustBurst } from '../effects.js';
import { placeTitle, hook, presence, INK } from '../graphics.js';

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    late: kit.at('late'),
    prices: kit.at('prices'),
    climbing: kit.at('climbing'),
    price: kit.at('price'),
    oil: kit.at('oil'),
    nearly: kit.at('nearly'),
    quadruples: kit.at('quadruples'),
    three: kit.at('three'),
    months: kit.at('months'),
    almost: kit.at('almost'),
    made: kit.at('made'),
    moved: kit.at('moved'),
    fuel: kit.at('fuel'),
    dearer: kit.at('dearer'),
    so: kit.at('so'),
    isnt: kit.at("isn't"),
    spending: kit.at('spending'),
    costs: kit.at('costs'),
    and: kit.at('and', 2),
    here: kit.at('here'),
    latest: kit.at('latest'),
    rose: kit.at('rose'),
    four: kit.at('four'),
    june: kit.at('june'),
    leave: kit.at('leave'),
    fuel2: kit.at('fuel', 2),
    two: kit.at('two'),
    nine: kit.at('nine'),
    end: kit.lastWordEnd,
  };
  // the cut to New Zealand, hidden in a quick dip to black on "And"
  const cut = T.and + 0.05;

  // ------------------------------------------------------------------ part A: the petrol station
  kit.lightRig({ keyColour: 0xffd09a, keyShare: 0.75, keyFrom: [2.8, 5.5, -3.5], keyTarget: [0, -2.1, -7.6], fillSky: 0x6f86a0, fillGround: 0x1c1a18,
    fillShare: 0.22, haze: 0x101823, hazeDensity: 0.004, shadowBox: 6, shadowSoftness: 5, background: 0x0b1118, reflections: 0.3 });
  const station = await kit.relief('409-bg-petrol-station-1973', { near: 6, far: 70, fov: 40, margin: 0.22 });
  const floor = (u, v) => station.pointAt(u, v);

  // the oil barrel, on the forecourt a little right of centre, with an OIL card on its side
  const barrelAt = floor(0.57, 0.15);
  const barrel = oilBarrel({ height: 1.05, colour: 0x9a3d1f });
  barrel.group.position.copy(barrelAt);
  barrel.group.rotation.y = 0;
  kit.scene.add(barrel.group);
  const oilCard = await kit.card('OIL', { size: 0.15, at: [0, barrel.height * 0.38, barrel.radius + 0.045], parent: barrel.group });
  const barrelLight = kit.glow([barrelAt.x - 0.6, barrelAt.y + 1.6, barrelAt.z + 1.4], { colour: 0xffc27a, strength: 3.5, reach: 5 });
  const dust = new DustBurst(kit.scene, { count: 22, seed: 7, colour: 'rgba(150,140,124,0.9)' });

  // the split-flap price counter on the barrel's lid: $2.90, flipping up to $11.65
  const flap = splitFlap({ cells: 6, cellWidth: 0.15, gap: 0.03, flipTime: 0.14 });
  const flapBase = barrelAt.clone().add(new THREE.Vector3(0, barrel.height, 0));
  kit.scene.add(flap.group);
  const flapUp = T.oil + 0.35;
  const priceSchedule = [{ t: flapUp - 0.01, text: '$2.90' },
    ...countSchedule({ from: 2.9, to: 11.65, start: T.nearly + 0.05, finish: T.quadruples + 0.75, steps: 12, format: (v) => `$${v.toFixed(2)}` }).slice(1)];

  // a row of price tags lying on the concrete in front, flipping up one after another
  const tags = [];
  const tagCount = 4;
  for (let i = 0; i < tagCount; i++) {
    const u = 0.29 + i * 0.145;
    const at = floor(u, 0.075);
    const tag = priceTag({ width: 0.46, text: '↑', accent: '#b8402c' });
    const pivot = new THREE.Group();
    // the tag hangs from its hole; sit its bottom edge on the pivot (its hinge), centred
    tag.group.position.set(-tag.width / 2 + tag.width * 62 / 512, tag.height / 2, 0);
    pivot.add(tag.group);
    pivot.position.copy(at);
    pivot.rotation.y = (i - 1.5) * -0.06;
    kit.scene.add(pivot);
    tags.push({ pivot, tag, upAt: T.almost + 0.1 + i * ((T.fuel - T.almost) / (tagCount - 1)) });
  }

  // warm specks drifting under the canopy lights
  const motes = new Motes(kit.scene, { count: 140, min: [-1.8, -2.0, -11], max: [2.4, 0.8, -5], size: 0.025, colour: 0xffe2b8, seed: 9, opacity: 0.5 });

  const partA = [station.mesh, barrel.group, flap.group, motes.points, ...tags.map((x) => x.pivot)];

  // ------------------------------------------------------------------ part B: a New Zealand street
  const suburb = await kit.relief('410-bg-nz-suburb', { near: 6, far: 70, fov: 40 });
  suburb.mesh.visible = false;

  // ------------------------------------------------------------------ the camera
  const barrelMid = [barrelAt.x, barrelAt.y + 0.75, barrelAt.z];
  const shotA = kit.shot([
    { t: T.start, position: [0, 0.25, 0.6], target: [0.2, -0.9, -30], fov: 40, focus: 14 },
    { t: T.climbing + 0.4, position: [0.1, 0.05, -0.2], target: [0.4, -1.0, -30], fov: 39, focus: 13 },
    { t: T.oil, position: [0.2, -0.2, -1.0], target: [barrelAt.x + 0.05, barrelAt.y + 0.85, barrelAt.z], fov: 36, focus: barrelMid },
    { t: T.months + 0.3, position: [0.3, -0.3, -1.6], target: [barrelAt.x, barrelAt.y + 0.9, barrelAt.z], fov: 33, focus: barrelMid },
    { t: T.made + 0.3, position: [0.05, -0.1, -0.6], target: [0.15, -1.3, -9], fov: 38, focus: [0, barrelAt.y, barrelAt.z + 0.6] },
    { t: T.dearer + 0.6, position: [0.05, -0.15, -0.9], target: [0.2, -1.25, -9], fov: 37, focus: [0, barrelAt.y, barrelAt.z + 0.5] },
    { t: cut + 0.5, position: [0.15, -0.05, -1.3], target: [0.3, -1.15, -9], fov: 35, focus: barrelMid },
  ], { handheld: 0.012, seed: 7 });
  const shotB = kit.shot([
    { t: cut - 0.5, position: [-0.1, 0.15, 0.4], target: [0.15, -0.55, -30], fov: 41, focus: 16 },
    { t: T.end + 1.4, position: [0.2, 0.0, -1.3], target: [0.35, -0.6, -30], fov: 39, focus: 14 },
  ], { handheld: 0.01, seed: 8 });
  kit.shake(T.oil + 0.05, 0.03, 0.18);

  function pose(t) {
    const inA = t < cut;
    partA.forEach((m) => { m.visible = inA; });
    suburb.mesh.visible = !inA;
    barrelLight.visible = inA;
    const fade = clamp01(1 - Math.abs(t - cut) / 0.24);
    if (!inA) {
      dust.hide();
      return { camera: shotB(t), look: { aperture: 6, maxBlur: 10, exposure: 0.95, glowThreshold: 0.93, glowStrength: 0.6, contrast: 1.05, fade: smooth(fade) } };
    }
    motes.set(t);
    // the barrel: falls from above and lands on "oil" with a thud and a small rock
    const land = T.oil + 0.05, fall = 0.38;
    barrel.group.visible = t >= land - fall;
    const k = clamp01((t - (land - fall)) / fall);
    const after = t - land;
    const rock = after > 0 ? 0.07 * Math.exp(-after * 6) * Math.sin(after * 26) : 0;
    barrel.group.position.set(barrelAt.x, barrelAt.y + 4.5 * (1 - k * k), barrelAt.z);
    barrel.group.rotation.set(rock, 0, degrees(6) * (1 - k) + rock * 0.6);
    dust.set({ origin: [barrelAt.x, barrelAt.y + 0.02, barrelAt.z + 0.1], width: 0.9, age: after, scale: 0.5 });
    // the counter rises out of the lid, then counts
    const rise = t < flapUp ? 0 : 1 - spring(t - flapUp, { stiffness: 14, damping: 0.6 });
    flap.group.visible = t >= flapUp;
    flap.group.position.set(flapBase.x, flapBase.y + 0.26 * rise, flapBase.z + 0.05);
    flap.group.scale.set(1, Math.max(0.01, rise), 1);
    flap.group.rotation.y = 0.12;
    flap.pose(t, priceSchedule);
    // the tags: lying face up, then flipping upright one by one (a little overshoot, a wobble)
    for (const { pivot, upAt } of tags) {
      const age = t - upAt;
      const up = age <= 0 ? 0 : 1 - spring(age, { stiffness: 15, damping: 0.5 });
      pivot.rotation.x = -Math.PI / 2 * (1 - up);
      // hidden until its turn (lying flat, a tag reads as a white sliver), then growing in as it flips
      if (age < 0) pivot.visible = false;
      pivot.scale.setScalar(smooth(clamp01(age / 0.18)) || 0.001);
    }
    return { camera: shotA(t), look: { aperture: 8, maxBlur: 14, exposure: 0.95, glowThreshold: 0.92, glowStrength: 0.72, contrast: 1.07, fade: smooth(fade) } };
  }

  // prices rose 4.1% with fuel, 2.9% without: two bars, the second added on "two point nine"
  function twoBars(ctx, t, { at, until, x = 260, y = 640, width = 560, height = 500 }) {
    const a = presence(t, at, until, 0.3, 0.4);
    if (a <= 0) return;
    const max = 5;
    const items = [
      { value: 4.1, label: 'WITH FUEL', colour: INK.amber, at: T.four + 0.05 },
      { value: 2.9, label: 'WITHOUT FUEL', colour: INK.paper, at: T.two + 0.05, labelAt: T.leave + 0.1 },
    ];
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(12,16,18,0.6)';
    ctx.beginPath(); ctx.roundRect(x - 50, y - 250, width + 100, height + 380, 26); ctx.fill();
    ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
    ctx.fillStyle = INK.amber; ctx.fillRect(x, y - 222, 120 * clamp01((t - at) / 0.5), 4);
    ctx.fillStyle = INK.paper; ctx.font = '800 58px Inter'; ctx.fillText('NEW ZEALAND', x, y - 150);
    ctx.fillStyle = INK.muted; ctx.font = '700 34px Inter'; ctx.fillText('PRICES, YEAR TO JUNE 2026', x, y - 92);
    ctx.font = '600 26px Inter'; ctx.fillText('SOURCE: STATS NZ', x, y + height + 104);
    ctx.strokeStyle = 'rgba(242,237,227,0.35)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x, y + height); ctx.lineTo(x + width, y + height); ctx.stroke();
    const slot = width / items.length, barWidth = slot * 0.6;
    items.forEach((item, i) => {
      const bx = x + i * slot + (slot - barWidth) / 2;
      const la = clamp01((t - (item.labelAt ?? item.at)) / 0.3);
      if (la > 0) {
        ctx.globalAlpha = a * la;
        ctx.fillStyle = INK.muted; ctx.font = '700 32px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
        ctx.fillText(item.label, bx + barWidth / 2, y + height + 18);
        if (t < item.at) {
          ctx.setLineDash([10, 10]); ctx.strokeStyle = 'rgba(242,237,227,0.45)'; ctx.lineWidth = 3;
          ctx.strokeRect(bx, y + height * 0.35, barWidth, height * 0.65); ctx.setLineDash([]);
        }
      }
      const k = 1 - (1 - clamp01((t - item.at) / 0.7)) ** 3;
      if (k <= 0) return;
      const h = height * item.value / max * k;
      ctx.globalAlpha = a;
      ctx.shadowColor = INK.shadow; ctx.shadowBlur = 14; ctx.shadowOffsetY = 3;
      ctx.fillStyle = item.colour; ctx.fillRect(bx, y + height - h, barWidth, h);
      ctx.shadowBlur = 20;
      ctx.fillStyle = INK.paper; ctx.font = '800 64px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
      ctx.globalAlpha = a * clamp01(k * 2 - 1);
      ctx.fillText(`${item.value.toFixed(1)}%`, bx + barWidth / 2, y + height - h - 20);
      ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    });
    ctx.restore();
  }

  // NOT SPENDING, dimmed, then struck through
  function struck(ctx, t, { at, strikeAt, until, text, y, size }) {
    const a = presence(t, at, until, 0.15, 0.3);
    if (a <= 0) return;
    hook(ctx, t, { at, until, text, y, size, colour: INK.muted });
    const k = 1 - (1 - clamp01((t - strikeAt) / 0.3)) ** 3;
    if (k <= 0) return;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.font = `800 ${size}px Inter`;
    const w = ctx.measureText(text).width + 30;
    ctx.strokeStyle = INK.red; ctx.lineWidth = 9; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(540 - w / 2, y + 4); ctx.lineTo(540 - w / 2 + w * k, y - 2); ctx.stroke();
    ctx.restore();
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    if (t < cut) {
      placeTitle(ctx, t, { at: T.late, until: T.price - 0.15, place: 'Late', year: 1973, y: 260 });
      hook(ctx, t, { at: T.prices, until: T.price - 0.15, lines: ['PRICES ALREADY', 'CLIMBING'], y: 420, size: 64 });
      // the counter's caption, just above it
      const flapTop = at([flapBase.x, flapBase.y - 0.02, flapBase.z + barrel.radius]);
      const ca = presence(t, T.oil + 0.6, T.almost - 0.1, 0.3, 0.3);
      if (ca > 0) {
        ctx.save(); ctx.globalAlpha = ca;
        ctx.shadowColor = INK.shadow; ctx.shadowBlur = 16;
        ctx.fillStyle = INK.paper; ctx.font = '800 46px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
        ctx.fillText('A BARREL', flapTop.x, flapTop.y + 34);
        ctx.restore();
      }
      hook(ctx, t, { at: T.quadruples + 0.1, until: T.almost - 0.1, text: '×4', y: 300, size: 170, colour: INK.amber });
      hook(ctx, t, { at: T.three - 0.05, until: T.almost - 0.1, text: 'IN ABOUT 3 MONTHS', y: 440, size: 58 });
      hook(ctx, t, { at: T.dearer, until: T.so - 0.1, text: 'DEARER', y: 330, size: 120, colour: INK.amber });
      struck(ctx, t, { at: T.isnt - 0.05, strikeAt: T.spending + 0.35, until: cut - 0.2, text: 'NOT SPENDING', y: 300, size: 84 });
      hook(ctx, t, { at: T.costs, until: cut - 0.2, text: 'COSTS', y: 440, size: 140, colour: INK.amber });
    } else {
      twoBars(ctx, t, { at: T.here + 0.1, until: T.end + 2 });
    }
    return true;
  }

  return { pose, draw2D };
}
