// What this does: page 6 of chapter 2, "Germany, 1923". We stand in the snow before the gate of a
// painted Ruhr coal and steel works (a painting with depth: winding tower, chimneys, brick sheds, the
// gate). Snow drifts down; the chimneys smoke.
//   - "Germany, 1923": a place-and-year title.
//   - "Prices are already racing": a flip counter drops in already spinning, its digits never settling.
//   - "French and Belgian soldiers march into the Ruhr": a column of soldiers (a painted cut-out)
//     marches in from the right along the near tracks, bobbing as it walks; THE RUHR, then COAL AND
//     STEEL as a stack of girders and timber stands up by the sheds.
//   - "tells workers to stop work in protest": the smoke stops; a padlock pops onto the gate; STOP WORK.
//   - "keeps paying them, with new money": banknotes tumble down out of the sky and bundles of notes
//     land and stack up in the snow.
//   - "one American dollar costs more than four trillion German marks": the flip counter returns and
//     counts up to 4,200,000,000,000 (research C2-C03: about 4.2 trillion marks per dollar in
//     November 1923); MARKS (from the start of the count), FOR ONE US DOLLAR, on dark plates.
//   - "new money really did push prices up... while less and less was being made": the counter lifts
//     away, the money keeps landing, the chimneys stay cold and the stack of steel shrinks; PRICES UP,
//     LESS AND LESS MADE.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, clamp01, smooth, ramp, lerp, seededRandom, spring, popUp } from '../cinema-kit.js';
import { banknoteBundle, splitFlap } from '../models.js';
import { Smoke } from '../effects.js';
import { placeTitle, hook, presence, INK } from '../graphics.js';

// Falling snow: points drifting down through a box, placed from t alone.
class Snow {
  constructor(scene, { count = 520, min = [-3, -2.4, -12], max = [3, 3.5, -1.5], size = 0.07, seed = 6, opacity = 0.75 } = {}) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 64;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const random = seededRandom(seed);
    this.flakes = Array.from({ length: count }, () => ({
      x: lerp(min[0], max[0], random()), y: random(), z: lerp(min[2], max[2], random()),
      speed: 0.25 + random() * 0.25, sway: random() * 6.28, swayRate: 0.6 + random() * 0.8 }));
    this.min = min; this.max = max;
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    this.points = new THREE.Points(this.geometry, new THREE.PointsMaterial({ map: texture, size, transparent: true, depthWrite: false, opacity, color: 0xe8eef4 }));
    this.points.frustumCulled = false;
    scene.add(this.points);
  }
  set(t) {
    const p = this.geometry.attributes.position.array, height = this.max[1] - this.min[1];
    this.flakes.forEach((f, i) => {
      const fall = (f.y * height + t * f.speed) % height;
      p[i * 3] = f.x + 0.15 * Math.sin(t * f.swayRate + f.sway);
      p[i * 3 + 1] = this.max[1] - fall;
      p[i * 3 + 2] = f.z;
    });
    this.geometry.attributes.position.needsUpdate = true;
  }
}

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    germany: kit.at('germany'),
    prices: kit.at('prices'),
    racing: kit.at('racing'),
    then: kit.at('then'),
    french: kit.at('french'),
    ruhr: kit.at('ruhr'),
    coal: kit.at('coal'),
    heartland: kit.at('heartland'),
    government: kit.at('government'),
    stop: kit.at('stop'),
    protest: kit.at('protest'),
    keeps: kit.at('keeps'),
    paying: kit.at('paying'),
    newMoney: kit.at('new'),
    money: kit.at('money'),
    november: kit.at('november'),
    american: kit.at('american'),
    four: kit.at('four'),
    trillion: kit.at('trillion'),
    marks: kit.at('marks'),
    thisTime: kit.at('this'),
    push: kit.at('push'),
    less: kit.at('less'),
    made: kit.at('made'),
    last: kit.lastWordEnd,
  };
  T.end = T.last + 1.3;

  kit.lightRig({ keyColour: 0xffd2a0, keyShare: 0.55, keyFrom: [-5, 8, 4], keyTarget: [0, -2, -10], fillSky: 0x93a8bc, fillGround: 0x2a2826,
    fillShare: 0.22, haze: 0x1c242c, hazeDensity: 0.003, shadowBox: 9, shadowSoftness: 5, background: 0x0e1318, reflections: 0.3 });
  const works = await kit.relief('407-bg-ruhr-works', { near: 6, far: 70, fov: 40 });

  // chimney smoke from the two tall chimneys and a blast-furnace stack (stops on "stop work")
  const chimneys = [
    { at: works.pointAt(0.195, 0.83).toArray(), scale: 2.4, seed: 41 },
    { at: works.pointAt(0.89, 0.83).toArray(), scale: 3.4, seed: 43 },
    { at: works.pointAt(0.78, 0.69).toArray(), scale: 4.2, seed: 47 },
  ].map((c) => ({ ...c, smoke: new Smoke(kit.scene, { count: 22, life: 4.2, seed: c.seed, colour: [48, 45, 43] }) }));
  const snow = new Snow(kit.scene, {});

  // the column of soldiers on the near tracks, marching in from the right (the cut-out faces left)
  const soldiers = await kit.cutout('french-soldiers', { at: [0, -2.085, -6.5], width: 3.4 });
  const marchFrom = T.french - 0.35, marchSpeed = 1.1;

  // coal and steel: a stack of girders, bricks and timber standing by the sheds on the right
  // (placed centre-right in the snow just behind the money stacks, so its shrinking reads clearly and
  // stacks and steel together fit the tight gate framing, clear of the phone-button zones)
  const STEEL = { x: 0.48, z: -9.3 };
  const steel = await kit.cutout('materials', { at: [STEEL.x, -2.14, STEEL.z], width: 1.4 });

  // the padlock on the gate
  const lockAt = works.pointAt(0.624, 0.3);
  const padlock = await kit.cutout('padlock', { at: [lockAt.x, lockAt.y + 0.04, lockAt.z + 0.25], width: 0.5 });

  // where the two stacks of bundles stand (drawn in a little so stacks and steel fit the tight gate framing)
  const stacks = [{ x: -0.8, z: -8.5 }, { x: -0.15, z: -8.9 }];

  // new money: flat notes tumbling down, and bundles stacking up in the snow before the gate
  const random = seededRandom(23);
  const notes = [];
  for (let i = 0; i < 26; i++) {
    let x = lerp(-1.6, 1.0, random()), z = lerp(-7.6, -9.8, random());
    // keep the notes that lie in the snow clear of the two bundle stacks and the steel (no clipping)
    for (const s of stacks) {
      if (Math.abs(x - s.x) < 0.62 && Math.abs(z - s.z) < 0.5) z = s.z + (z < s.z ? -0.75 : 0.75);
    }
    const piece = await kit.cutout('banknotes', { at: [x, -2.2, z], width: 0.42 + random() * 0.1, yaw: (random() - 0.5) * 0.8 });
    const fall = 1.3 + random() * 0.5;
    const from = i < 18 ? T.keeps - 0.1 + (i / 18) * (T.november - T.keeps) : T.november + 0.3 + ((i - 18) / 8) * (T.push - T.november);
    const note = { piece, rest: 0.03 + i * 0.003, land: from + fall, fall, spin: (random() - 0.5) * 9, tumble: 4 + random() * 4, phase: random() * 6.28, drift: (random() - 0.5) * 0.8 };
    // the whole fall (drift and sway) must stay clear of the stacks too: if its path passes over one,
    // it falls in front of or behind it instead
    // (and the same for the standing steel)
    const obstacles = [...stacks.map((s) => ({ ...s, half: 0.62, depth: 0.75 })), { ...STEEL, half: 0.95, depth: 0.45 }];
    for (let pass = 0; pass < 3; pass++) for (const s of obstacles) {
      const near = Math.min(Math.abs(x - s.x), Math.abs(x + note.drift - s.x)) - 0.12;
      const between = (x - s.x) * (x + note.drift - s.x) < 0;
      if ((near < s.half || between) && Math.abs(piece.rest.z - s.z) < s.depth) piece.rest.z = s.z + (piece.rest.z < s.z ? -s.depth : s.depth);
    }
    notes.push(note);
  }
  const bundles = [];
  for (let i = 0; i < 16; i++) {
    const b = banknoteBundle({ width: 0.6, depth: 0.3, notes: 32 });
    const s = stacks[i % 2];
    b.stack = s; b.level = Math.floor(i / 2);
    // tone the notes down to the painting's dusk light (they read near-white otherwise)
    b.group.traverse((o) => { if (o.material) [].concat(o.material).forEach((m) => { m.color.multiplyScalar(0.72); }); });
    b.group.rotation.y = (random() - 0.5) * 0.4;
    b.twist = (random() - 0.5) * 0.3;
    b.shift = [(random() - 0.5) * 0.05, (random() - 0.5) * 0.05];
    // most land while she says "keeps paying them, with new money"; the rest keep coming afterwards
    b.landAt = i < 8 ? T.paying + 0.05 + i * 0.16 : T.money + 0.6 + (i - 8) * ((T.made - T.money - 0.6) / 8);
    kit.scene.add(b.group);
    bundles.push(b);
  }

  // the flip counter: spinning at "prices are already racing", counting marks for a dollar in November
  const board = splitFlap({ cells: 17, cellWidth: 0.088, gap: 0.008, flipTime: 0.14 });
  const boardHome = new THREE.Vector3(-0.08, 1.0, -6.2);
  kit.scene.add(board.group);
  const glow = kit.glow([-0.08, 1.2, -5.2], { colour: 0xffd8a8, strength: 1.6, reach: 3 });
  // while prices race, every cell is its own one-cell counter flipping on its own beat, so the digits
  // are always mid-flip and the board never rests on a readable number
  const spin = seededRandom(5);
  const racing = [{ t: 0, text: '' }];
  const raceCells = [];
  for (let n = 0; n < 17; n++) {   // one layer only: a doubled ghost layer read as a rendering fault
    const i = n % 17, ghost = n >= 17;
    const cell = splitFlap({ cells: 1, cellWidth: 0.088, gap: 0.008, flipTime: 0.075, housing: false });
    cell.group.position.set((i - 8) * 0.096, ghost ? 0.012 : 0, ghost ? 0.03 : 0.012);
    if (ghost) cell.group.traverse((o) => { if (o.material) { o.material.transparent = true; o.material.opacity = 0.5; o.material.depthWrite = false; } });
    board.group.add(cell.group);
    const fromRight = 16 - i, schedule = [];
    for (let t = T.prices - 0.25 + spin() * 0.08; t < T.then + 0.8; t += 0.08) {
      const length = Math.min(13, 4 + Math.floor(Math.max(0, t - T.prices) * 3));
      const width = length + Math.floor((length - 1) / 3);
      const text = fromRight >= width ? '' : (fromRight + 1) % 4 === 0 ? ',' : String(Math.floor(spin() * 10));
      schedule.push({ t, text });
    }
    raceCells.push({ cell, schedule });
  }
  const FINAL = 4.2e12;
  const count = [{ t: T.november - 0.4, text: '' }];
  const countFrom = T.november + 0.15, countTo = T.trillion;
  for (let i = 0; i <= 34; i++) {
    const k = i / 34;
    const value = i === 34 ? FINAL : 10 ** lerp(3, Math.log10(FINAL), smooth(k) * 0.4 + k * 0.6);
    const shown = i === 34 ? FINAL : Number(value.toPrecision(2));
    count.push({ t: lerp(countFrom, countTo, 1 - (1 - k) ** 1.6), text: shown.toLocaleString('en-US') });
  }

  // the camera, by the camera rule: two still shots with a cut on "By November".
  // Shot 1 (the works gate): holds wide on the works and the racing counter; zooms in a little (tilting
  // down) onto the soldiers as they march in; zooms in onto the gate as it is locked, and holds there
  // while the money lands.
  // Shot 2 (November): holds on the counter with the money below; zooms in onto the stacks of money
  // and the shrinking steel as new money pushes prices up while less and less is made, then holds.
  const boardFocus = boardHome.toArray();
  const stackFocus = [-0.6, -1.8, -8.7];
  const CUT = T.november - 0.5, DIP = 0.2;
  // the locked gate, framed tight (2 degrees tighter than the soldiers' framing) with the padlock and
  // the steel low in the frame, so the snow in front does not take the bottom quarter
  const GATE_FOV = 35, GATE_AIM = [0.3, -0.6, -30];
  const gateShot = kit.stillShot({ position: [0, 0.3, 0.35], target: [0, -0.1, -30], fov: 40, focus: 14 }, [
    { from: T.prices - 0.3, to: T.prices + 0.2, kind: 'focus', focus: boardFocus },
    { from: T.french - 0.45, to: T.french + 0.75, kind: 'zoom in', position: [0, -0.02, -0.25], target: [0, -1.2, -30], fov: 37, focus: 8 },
    { from: T.heartland - 0.2, to: T.heartland + 0.3, kind: 'focus', focus: 7.2 },
    { from: T.government - 0.15, to: T.stop + 0.3, kind: 'zoom in', position: [-0.05, -0.3, -1.2], target: GATE_AIM, fov: GATE_FOV, focus: [lockAt.x, lockAt.y, lockAt.z] },
    { from: T.paying - 0.1, to: T.paying + 0.4, kind: 'focus', focus: stackFocus },
  ], { name: 'the works gate' });
  const novemberShot = kit.stillShot({ position: [0, 0.1, -0.55], target: [0, -0.1, -30], fov: 40, focus: boardFocus }, [
    { from: T.push - 0.35, to: T.push + 0.85, kind: 'zoom in', position: [-0.05, -0.3, -1.6], target: [0, -1.1, -30], focus: [-0.3, -1.9, -8.8] },
  ], { name: 'November' });
  const shot = (t) => (t < CUT ? gateShot(t) : novemberShot(t));

  // Keep every fall path (notes and bundles) clear of the words on screen: for each faller, find the
  // highest start that keeps its whole path, as the camera sees it at each moment, out of the boxes
  // the words fill at that moment. A note that has to start lower fades in out of the snowy air; a bundle pops into being.
  const lens = new THREE.PerspectiveCamera(40, 1080 / 1920, 0.1, 200);
  const onScreen = (point, t) => {
    const c = shot(t);
    lens.position.copy(c.position); lens.up.set(0, 1, 0); lens.lookAt(c.target);
    lens.fov = c.fov; lens.updateProjectionMatrix(); lens.updateMatrixWorld();
    const p = new THREE.Vector3(...point).project(lens);
    return { x: (p.x + 1) / 2 * 1080, y: (1 - p.y) / 2 * 1920 };
  };
  const wordBoxes = (t) => {
    const boxes = [];   // [left, top, right, bottom] in pixels, with a margin
    if (t > T.stop - 0.1 && t < T.keeps) boxes.push([200, 215, 880, 455]);
    if (t > T.paying - 0.1 && t < T.november - 0.25) boxes.push([200, 215, 880, 455]);
    if (t > T.november - 0.1 && t < T.thisTime + 0.2) {
      const top = onScreen([boardHome.x, boardHome.y + 0.2, boardHome.z], t), bottom = onScreen([boardHome.x, boardHome.y - 0.2, boardHome.z], t);
      boxes.push([100, top.y - 120, 920, bottom.y + 215]);
    }
    if (t > T.push - 0.1) boxes.push([190, 155, 890, 455]);
    return boxes;
  };
  const pathClear = (from, length, at) => {
    for (let k = 0; k <= 1.0001; k += 0.04) {
      const t = from + k * length, [x, y, z, rx, ry] = at(k, t);
      const a = onScreen([x - rx, y + ry, z], t), b = onScreen([x + rx, y - ry, z], t);   // its box on screen
      for (const [l, top, right, bottom] of wordBoxes(t)) {
        if (b.x > l && a.x < right && b.y > top && a.y < bottom) return false;
      }
    }
    return true;
  };
  for (const n of notes) {
    const from = n.land - n.fall, { x, z } = n.piece.rest;
    n.drop = 4.4;
    while (n.drop > 0.4 && !pathClear(from, n.fall, (k, t) => [x + n.drift * (1 - k) + 0.12 * Math.sin((t - from) * 3 + n.phase), -2.2 + n.drop * (1 - k) + n.rest + 0.12, z, 0.3, 0.3])) n.drop -= 0.05;
    for (const m of [n.piece.front.material, n.piece.back.material]) m.alphaTest = 0.5;
  }
  {
    const levels = new Map(stacks.map((st) => [st, 0]));
    for (const b of bundles) {
      const base = levels.get(b.stack); levels.set(b.stack, base + b.height + 0.009);
      b.drop = 3.6;
      while (b.drop > 0.3 && !pathClear(b.landAt - 0.45, 0.45, (k) => [b.stack.x, -2.2 + base + b.drop * (1 - k * k) + b.height / 2, b.stack.z, 0.36, 0.16])) b.drop -= 0.05;
    }
  }
  kit.shake(T.stop + 0.15, 0.01, 0.15);
  kit.shake(T.trillion + 0.05, 0.012, 0.18);

  // the board drops in from above and lifts away again
  const boardDrop = (t) => {
    const inRace = t >= T.prices - 0.35 && t < T.then + 0.9;
    const inCount = t >= T.november - 0.45 && t < T.thisTime + 0.9;
    if (!inRace && !inCount) return null;
    const [from, leave] = inRace ? [T.prices - 0.35, T.then + 0.2] : [T.november - 0.45, T.thisTime + 0.15];
    const arrive = 2.2 * spring(t - from, { stiffness: 11, damping: 0.6 });
    const go = 3.2 * smooth(ramp(t, leave, leave + 0.7)) ** 1.5;
    return arrive + go;
  };

  function pose(t) {
    snow.set(t);
    for (const c of chimneys) c.smoke.set({ t, origin: c.at, until: T.stop + 0.05, scale: c.scale, wind: 0.6 });

    // soldiers: marching from the right, with a walking bob, gone off the left by "stop work"
    const dx = 3.5 - marchSpeed * (t - marchFrom);
    const stepping = Math.sin((t - marchFrom) * Math.PI * 2 * 1.7);
    soldiers.set({ visible: t > marchFrom && dx > -3.6, dx, dy: 0.04 * Math.abs(stepping), roll: 0.012 * stepping });

    // the stack of steel stands up on "heartland" and shrinks as less and less is made
    const steelUp = popUp(t, T.heartland - 0.05, { height: 0.7, restZ: 0.15 });
    // (it shrinks toward its right end, so it stays in view beside the growing money)
    const steelScale = lerp(1, 0.6, smooth(ramp(t, T.less - 0.1, T.made + 0.4)));
    steel.set({ ...steelUp, scale: steelScale, dx: (1 - steelScale) * 0.7 });

    // the padlock pops onto the gate
    const lockAge = t - T.stop;
    padlock.set({ visible: lockAge > 0, scale: lockAge > 0 ? 1 - spring(lockAge, { stiffness: 15, damping: 0.45 }) : 0, dz: 0 });

    // notes tumbling out of the sky, then lying flat in the snow face-up (negative fold = printed side up)
    for (const n of notes) {
      const age = t - (n.land - n.fall);
      if (age < 0) { n.piece.set({ visible: false }); continue; }
      const k = Math.min(1, age / n.fall);
      // a note that starts low (to keep clear of the words) fades in out of the snowy air
      const opacity = n.drop < 4.35 ? smooth(clamp01(age / 0.3)) : 1;
      for (const m of [n.piece.front.material, n.piece.back.material]) m.alphaTest = opacity < 1 ? 0.02 : 0.5;
      if (k < 1) {
        n.piece.set({ opacity, dy: n.drop * (1 - k) + n.rest, dx: n.drift * (1 - k) + 0.12 * Math.sin(age * 3 + n.phase), roll: n.spin * (1 - k),
          fold: -0.6 + 0.9 * Math.sin(age * n.tumble + n.phase) * (1 - k) - 0.95 * k, yaw: 0.8 * Math.sin(age * 2 + n.phase) });
      } else n.piece.set({ opacity: 1, fold: -(Math.PI / 2 - 0.02), dy: n.rest });
    }

    // bundles land and stack up
    const heights = new Map(stacks.map((s) => [s, 0]));
    bundles.forEach((b) => {
      const fall = 0.45;
      const k = clamp01((t - (b.landAt - fall)) / fall);
      b.group.visible = t >= b.landAt - fall;
      const base = heights.get(b.stack);
      const settle = t > b.landAt ? Math.exp(-(t - b.landAt) * 10) * Math.sin((t - b.landAt) * 30) * 0.05 : 0;
      const tilt = b.twist * (1 - k) + settle;
      b.group.rotation.z = tilt;
      b.group.position.set(b.stack.x + b.shift[0], -2.2 + 0.004 + base + b.drop * (1 - k * k) + Math.abs(Math.sin(tilt)) * 0.32, b.stack.z + b.shift[1]);
      // a bundle that starts low (to keep clear of the words) pops into being as it drops, paper-style
      b.group.scale.setScalar(b.drop < 3.55 ? 0.3 + 0.7 * smooth(clamp01(k / 0.3)) : 1);
      heights.set(b.stack, base + b.height + 0.009);   // the paper band stands 0.004 proud top and bottom
    });

    // the flip counter
    const drop = boardDrop(t);
    board.group.visible = drop !== null;
    glow.intensity = drop !== null ? 1.6 : 0;
    if (drop !== null) {
      board.group.position.set(boardHome.x, boardHome.y + drop, boardHome.z);
      board.group.rotation.x = -0.05 * drop;
      const inRace = t < T.november - 0.5;
      board.pose(t, inRace ? racing : count);
      for (const r of raceCells) { r.cell.group.visible = inRace; if (inRace) r.cell.pose(t, r.schedule); }
    }

    const dim = smooth(ramp(t, T.less - 0.2, T.made + 0.6));
    return { camera: shot(t), look: { aperture: 8, maxBlur: 14, exposure: lerp(0.95, 0.86, dim), saturation: lerp(1, 0.85, dim),
      glowThreshold: 0.93, glowStrength: 0.62, contrast: 1.06, fade: Math.max(0, 1 - Math.abs(t - CUT) / DIP) } };
  }

  function draw2D(ctx, t) {
    placeTitle(ctx, t, { at: T.germany, until: T.prices - 0.15, place: 'Germany', year: 1923, y: 260 });
    hook(ctx, t, { at: T.prices, until: T.then - 0.1, text: 'PRICES RACING', y: 280, size: 84 });
    hook(ctx, t, { at: T.ruhr, until: T.government - 0.2, text: 'THE RUHR', y: 290, size: 100 });
    hook(ctx, t, { at: T.coal, until: T.government - 0.2, text: 'COAL AND STEEL', y: 400, size: 66, colour: INK.amber });
    hook(ctx, t, { at: T.stop, until: T.keeps - 0.15, text: 'STOP WORK', y: 290, size: 100 });
    hook(ctx, t, { at: T.protest, until: T.keeps - 0.15, text: 'IN PROTEST', y: 400, size: 58, colour: INK.amber });
    hook(ctx, t, { at: T.paying, until: T.november - 0.3, text: 'STILL PAID', y: 290, size: 96 });
    hook(ctx, t, { at: T.newMoney, until: T.november - 0.3, text: 'WITH NEW MONEY', y: 400, size: 66, colour: INK.amber });

    // the November counter's captions, placed around the board on screen, each on a dark plate in
    // paper white so they read over the grey headframe and the amber sky. MARKS stands under the
    // counter from the moment it starts racing (the unit is there while the number climbs);
    // FOR ONE US DOLLAR comes in as she says "one American dollar" (US, so a New Zealand viewer
    // does not read it as NZ$).
    const top = kit.toScreen([boardHome.x, boardHome.y + 0.2, boardHome.z]);
    const bottom = kit.toScreen([boardHome.x, boardHome.y - 0.2, boardHome.z]);
    const plated = (alpha, text, size, weight, y) => {
      if (alpha <= 0) return;
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.font = `${weight} ${size}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const w = ctx.measureText(text).width;
      ctx.fillStyle = 'rgba(12,16,18,0.78)';
      ctx.beginPath(); ctx.roundRect(500 - w / 2 - 26, y - size * 0.72, w + 52, size * 1.44, 12); ctx.fill();
      ctx.fillStyle = INK.paper;
      ctx.fillText(text, 500, y + size * 0.04);
      ctx.restore();
    };
    // the unit under the racing counter too ("prices are already racing"), following the board as it
    // drops in
    const raceUnit = presence(t, T.prices + 0.1, T.then + 0.1, 0.3, 0.3);
    if (raceUnit > 0) {
      const under = kit.toScreen([boardHome.x, boardHome.y - 0.2 + (boardDrop(t) ?? 0), boardHome.z]);
      plated(raceUnit, 'MARKS', 56, 800, under.y + 62);
    }
    plated(presence(t, T.november, T.thisTime + 0.1, 0.3, 0.3), 'NOVEMBER 1923', 50, 700, top.y - 62);
    plated(presence(t, T.november + 0.1, T.thisTime + 0.1, 0.3, 0.3), 'MARKS', 64, 800, bottom.y + 72);
    plated(presence(t, T.american - 0.1, T.thisTime + 0.1, 0.3, 0.3), 'FOR ONE US DOLLAR', 50, 700, bottom.y + 168);

    hook(ctx, t, { at: T.push, until: T.end, text: 'PRICES UP', y: 230, size: 100, colour: INK.red });
    hook(ctx, t, { at: T.less, until: T.end, lines: ['LESS AND LESS', 'MADE'], y: 350, size: 66, colour: INK.paper });   // paper white: amber was lost on the amber sky
    return true;
  }

  return { pose, draw2D, join: { kind: 'peel', after: 0.3, length: 0.85 } };
}
