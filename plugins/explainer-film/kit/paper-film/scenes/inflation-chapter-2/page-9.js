// What this does: page 9 of chapter 2, "the usual cure" (Britain, 1920-21). Two painted places:
//   Part A, a wet town street at dusk:
//   - "So what's the usual cure?": the hook THE USUAL CURE? over the empty street.
//   - "Britain, 1920. The Bank of England pushes its interest rate ... up to seven percent": a place
//     and year title; a card bank pops up on the street and a 3D meter on a post beside it shows the
//     interest rate at 6; its needle strains and slams up to 7 on "seven" with a heavy jolt.
//   - "Loans cost more, and people spend less": a stack of coins on the pavement is pulled back to
//     the bank coin by coin, the shop light goes out and the street dims.
//   Part B (after a quick dip to black on "Within a year"), a factory gate:
//   - "unemployment jumps from about two percent to eleven percent": a dole queue grows from the
//     gate toward us; bars 1920 (2%) and 1921 (11%) labelled UNEMPLOYMENT.
//   - "Prices do fall... but people pay with their jobs": PRICES DO FALL, then PAID WITH THEIR JOBS.
//   - "Mattei argues that was part of the point": her book pops up with a source credit and the
//     words MATTEI: PART OF THE POINT.
//   - "workers lose the power to ask for more": an iron weight drops onto a pay packet and crushes
//     it flat (jolt, dust); LESS POWER TO ASK FOR MORE (the credit to her stays on screen).
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, foldDown, slapFlat, dropIn, spring, clamp01, smooth, ramp, lerp, seededRandom } from '../cinema-kit.js';
import { dial, coin, PAPER } from '../models.js';
import { Motes, DustBurst } from '../effects.js';
import { placeTitle, hook, callout, bars, credit, INK } from '../graphics.js';

const FACE_TURN = Math.PI / 2;

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    cure: kit.at('cure'),
    britain: kit.at('britain'),
    bank: kit.at('bank'),
    pushes: kit.at('pushes'),
    interest: kit.at('interest'),
    price: kit.at('price'),
    up: kit.at('up'),
    seven: kit.at('seven'),
    loans: kit.at('loans'),
    spend: kit.at('spend'),
    less: kit.at('less'),
    within: kit.at('within'),
    unemployment: kit.at('unemployment'),
    jumps: kit.at('jumps'),
    two: kit.at('two'),
    eleven: kit.at('eleven'),
    prices: kit.at('prices'),
    but: kit.at('but'),
    pay: kit.at('pay'),
    mattei: kit.at('mattei'),
    part: kit.at('part'),
    with: kit.at('with', 2),
    fewer: kit.at('fewer'),
    workers: kit.at('workers'),
    lose: kit.at('lose'),
    power: kit.at('power'),
    last: kit.lastWordEnd,
  };
  const CUT = T.within - 0.05; // the dip to black is darkest here; the second place starts

  kit.lightRig({ keyColour: 0xffd2a0, keyShare: 0.7, keyFrom: [5, 7, 2], keyTarget: [0, -2, -9], fillSky: 0x7f95a4, fillGround: 0x26221e,
    fillShare: 0.22, haze: 0x18212a, hazeDensity: 0.004, shadowBox: 8, shadowSoftness: 5, background: 0x10161b, reflections: 0.3 });

  // ------------------------------------------------------------------ part A: the town street
  const street = await kit.relief('107-bg-town-street', { near: 6, far: 70, fov: 40 });
  const bankAt = street.pointAt(0.35, 0.13);
  const bank = await kit.cutout('bank', { at: [bankAt.x, bankAt.y, bankAt.z], width: 1.8, yaw: 0.12 });
  // the interest-rate meter on a post, on the pavement right of the bank
  const postAt = street.pointAt(0.69, 0.15);
  const meter = dial({ radius: 0.62, min: 0, max: 8, step: 1, label: 'INTEREST', unit: '%' });
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 1.8, 12), new THREE.MeshStandardMaterial({ color: 0x2d3236, roughness: 0.6 }));
  post.castShadow = true;
  const meterRig = new THREE.Group();
  meterRig.add(post); post.position.y = 0.9;
  meterRig.add(meter.group); meter.group.position.y = 1.8 + 0.55;
  meterRig.position.copy(postAt);
  meterRig.rotation.y = -0.18;
  // work-around: the shared dial prints its face a quarter turn off from its needle; turn the face
  // about its own axis so the printed scale lines up with the needle (the needle is right)
  meter.group.children[0].rotation.y = FACE_TURN;
  kit.scene.add(meterRig);
  const meterCentre = postAt.clone().add(new THREE.Vector3(0, 2.35, 0));
  // a stack of coins on the pavement (people's spending money), pulled back to the bank coin by coin
  const stackAt = street.pointAt(0.6, 0.06);
  const coins = [];
  const random = seededRandom(9);
  for (let i = 0; i < 9; i++) {
    const c = coin({ radius: 0.19, thickness: 0.04 });
    c.shift = [(random() - 0.5) * 0.03, (random() - 0.5) * 0.03];
    c.leaveAt = T.loans + 0.25 + (8 - i) * 0.3; // the top coin leaves first
    kit.scene.add(c.group);
    coins.push(c);
  }
  const shopLight = kit.glow(street.pointAt(0.86, 0.3).add(new THREE.Vector3(-0.6, 0.6, 1.5)), { colour: 0xffb25e, strength: 6, reach: 7 });
  const streetMotes = new Motes(kit.scene, { count: 140, min: [-2, -2.4, -12], max: [2, 1.5, -4], size: 0.025, seed: 19, opacity: 0.45 });
  const partA = [street.mesh, bank.anchor, meterRig, ...coins.map((c) => c.group), shopLight, streetMotes.points];

  // ------------------------------------------------------------------ part B: the factory gate
  const gate = await kit.relief('109-bg-factory-gate', { near: 6, far: 70, fov: 40 });
  // the dole queue grows from the gate toward us: four copies, the far one first
  const queueSpots = [[0.44, 0.31], [0.36, 0.25], [0.27, 0.18], [0.15, 0.1]];
  const queueTimes = [T.unemployment - 0.1, T.jumps, T.two + 0.1, T.eleven];
  const queue = [];
  for (const [i, [u, v]] of queueSpots.entries()) {
    const p = gate.pointAt(u, v);
    queue.push(await kit.cutout('dole-queue', { at: [p.x, p.y, p.z], width: 1.8, yaw: 0.35 }));
  }
  const bookAt = gate.pointAt(0.76, 0.15);
  const book = await kit.cutout('book', { at: [bookAt.x, bookAt.y, bookAt.z], width: 1.0, yaw: -0.25 });
  const packetAt = gate.pointAt(0.52, 0.15);
  const packet = await kit.cutout('pay-packet', { at: [packetAt.x, packetAt.y, packetAt.z], width: 1.2 });
  const weight = await kit.cutout('iron-weight', { at: [packetAt.x, packetAt.y + 0.02, packetAt.z + 0.45], width: 0.95 });
  const dust = new DustBurst(kit.scene, { count: 22, seed: 12 });
  const gateMotes = new Motes(kit.scene, { count: 160, min: [-2, -2.2, -14], max: [2, 1.5, -4], size: 0.025, seed: 23, opacity: 0.45 });
  const partB = [gate.mesh, ...queue.map((q) => q.anchor), book.anchor, packet.anchor, weight.anchor, gateMotes.points];

  // ------------------------------------------------------------------ cameras
  const meterFocus = [meterCentre.x, meterCentre.y, meterCentre.z];
  const shotA = kit.shot([
    { t: T.start, position: [0, 0.2, 0.3], target: [0, -0.3, -30], fov: 40, focus: 14 },
    { t: T.bank - 0.2, position: [0, 0.05, -0.2], target: [0, -0.9, -30], fov: 40, focus: [bankAt.x, bankAt.y + 1, bankAt.z] },
    { t: T.price, position: [0.15, -0.05, -0.8], target: [0.15, -0.6, -30], fov: 39, focus: meterFocus },
    { t: T.seven + 0.3, position: [0.3, -0.1, -1.3], target: [0.35, -0.4, -30], fov: 38, focus: meterFocus },
    { t: T.loans + 0.5, position: [0.1, -0.05, -0.9], target: [0.05, -1.0, -30], fov: 39, focus: [stackAt.x, stackAt.y, stackAt.z] },
    { t: CUT, position: [0.05, 0.0, -0.7], target: [0.0, -0.95, -30], fov: 40, focus: [stackAt.x, stackAt.y, stackAt.z] },
  ], { handheld: 0.012, seed: 9 });
  const qMid = queue[1].rest;
  const shotB = kit.shot([
    { t: CUT, position: [0, 0.15, 0.4], target: [-0.4, -0.4, -30], fov: 40, focus: [qMid.x, qMid.y + 0.8, qMid.z] },
    { t: T.eleven + 0.5, position: [-0.1, 0.0, -0.5], target: [-0.5, -0.8, -30], fov: 40, focus: [qMid.x, qMid.y + 0.8, qMid.z] },
    { t: T.pay + 0.4, position: [0.0, -0.05, -0.9], target: [-0.2, -0.9, -30], fov: 39, focus: queue[2].rest.toArray() },
    { t: T.part, position: [0.35, -0.2, -1.1], target: [0.6, -1.0, -30], fov: 39, focus: [bookAt.x, bookAt.y + 0.8, bookAt.z] },
    { t: T.lose - 0.3, position: [0.15, -0.3, -1.4], target: [0.2, -1.3, -30], fov: 39, focus: [packetAt.x, packetAt.y + 0.3, packetAt.z] },
    { t: T.last + 1.3, position: [0.15, -0.35, -1.8], target: [0.2, -1.4, -30], fov: 39, focus: [packetAt.x, packetAt.y + 0.3, packetAt.z] },
  ], { handheld: 0.012, seed: 10 });
  kit.shake(T.seven + 0.08, 0.05, 0.2);
  kit.shake(T.lose + 0.2, 0.045, 0.2);
  const WEIGHT_LANDS = T.lose + 0.2;

  // the needle: sits at 6, strains on "up to", slams to 7 on "seven" with an overshoot
  function rate(t) {
    if (t < T.seven) {
      const strain = smooth(ramp(t, T.up - 0.1, T.seven));
      return 6 + 0.18 * strain + 0.03 * strain * Math.sin(t * 60);
    }
    return 7 - (1 - 0.18) * spring(t - T.seven, { stiffness: 18, damping: 0.45 });
  }

  function pose(t) {
    const inA = t < CUT;
    partA.forEach((o) => { o.visible = inA; });
    partB.forEach((o) => { o.visible = !inA; });
    const fade = clamp01(1 - Math.abs(t - CUT) / 0.24);
    let exposure = 0.95, vignette;
    if (inA) {
      streetMotes.set(t);
      bank.set(popUp(t, T.bank - 0.1, { height: 2.2, restZ: 0.2 }));
      // the meter rises out of the pavement on "pushes"
      const rise = clamp01((t - T.pushes + 0.2) / 0.45);
      meterRig.visible = rise > 0;
      meterRig.position.set(postAt.x, postAt.y - 2.6 * (1 - smooth(rise)) * (1 - smooth(rise)), postAt.z);
      meterRig.rotation.z = rise > 0 ? 0.08 * Math.exp(-(t - T.pushes) * 4) * Math.sin((t - T.pushes) * 14) : 0;
      meter.setValue(rate(t));
      // the coins appear on "loans", then fly back to the bank one by one
      const bankDoor = bankAt.clone().add(new THREE.Vector3(0.1, 0.45, 0.1));
      coins.forEach((c, i) => {
        const appear = clamp01((t - T.loans + 0.25 - i * 0.03) / 0.2);
        const rest = new THREE.Vector3(stackAt.x + c.shift[0], stackAt.y + 0.04 * (i + 0.5), stackAt.z + c.shift[1]);
        const k = smooth(clamp01((t - c.leaveAt) / 0.55));
        c.group.visible = appear > 0 && k < 1;
        c.group.position.lerpVectors(rest, bankDoor, k);
        c.group.position.y += Math.sin(Math.PI * k) * 0.9 + (1 - appear) * 0.4;
        c.group.rotation.set(k * 9, 0, k * 4);
        c.group.scale.setScalar(lerp(1, 0.5, k));
      });
      // people spend less: the shop light goes out and the street dims
      const dim = smooth(ramp(t, T.spend, T.less + 0.5));
      shopLight.intensity = 6 * (1 - dim);
      exposure = lerp(0.95, 0.7, dim);
      vignette = lerp(0.35, 0.6, dim);
    } else {
      gateMotes.set(t);
      queue.forEach((q, i) => q.set(popUp(t, queueTimes[i] - 0.1, { height: 1.4, restZ: 0.25 })));
      book.set(popUp(t, T.mattei - 0.1, { height: 1.6, restZ: 0.2 }));
      packet.set(t < WEIGHT_LANDS ? popUp(t, T.workers - 0.2, { height: 0.9, restZ: 0.25 }) : slapFlat(t, WEIGHT_LANDS - 0.04, 0.08));
      const drop = dropIn(t, WEIGHT_LANDS, { fall: 0.38, height: 5, roll: 6, bounce: 0.12 });
      weight.set(drop.visible ? { ...drop, dy: (drop.dy ?? 0) + 0.04 } : drop);
      if (t >= WEIGHT_LANDS) dust.set({ origin: [packetAt.x, packetAt.y + 0.05, packetAt.z], width: 1.2, age: t - WEIGHT_LANDS, scale: 0.55 });
      else dust.hide();
      exposure = 0.93;
    }
    if (inA) dust.hide();
    return {
      camera: inA ? shotA(t) : shotB(t),
      look: { aperture: 8, maxBlur: 14, exposure, glowThreshold: 0.93, glowStrength: 0.65, contrast: 1.06, fade, ...(vignette !== undefined ? { vignette } : {}) },
    };
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    // part A
    hook(ctx, t, { at: T.cure - 0.05, until: T.britain - 0.15, lines: ['THE USUAL', 'CURE?'], y: 360, size: 104 });
    placeTitle(ctx, t, { at: T.britain, until: T.interest - 0.15, place: 'Britain', year: 1920, y: 290 });
    callout(ctx, t, { at: T.bank + 0.15, until: T.interest - 0.15, point: at(bankAt.clone().add(new THREE.Vector3(0, 1.8, 0))), text: 'BANK OF ENGLAND', dx: -120, dy: -640, size: 38 });
    hook(ctx, t, { at: T.interest, until: T.seven - 0.1, lines: ['INTEREST RATE'], y: 300, size: 76 });
    hook(ctx, t, { at: T.price, until: T.seven - 0.1, lines: ['THE PRICE OF BORROWING'], y: 390, size: 42, colour: INK.amber });
    hook(ctx, t, { at: T.seven, until: T.loans - 0.15, text: '7%', y: 350, size: 200, colour: INK.red });
    hook(ctx, t, { at: T.loans, until: CUT - 0.1, text: 'LOANS COST MORE', y: 300, size: 76 });
    hook(ctx, t, { at: T.spend, until: CUT - 0.1, text: 'SPEND LESS', y: 400, size: 76, colour: INK.amber });
    // part B
    hook(ctx, t, { at: CUT + 0.1, until: T.two - 0.35, text: 'WITHIN A YEAR', y: 300, size: 64, colour: INK.muted });
    bars(ctx, t, { at: T.two - 0.25, until: T.prices - 0.1, box: [300, 360, 480, 360], values: [2, 11], maxValue: 13, labels: ['1920', '1921'], title: 'Unemployment',
      valueText: (v) => `${v}%`, colours: [INK.paper, INK.red], stagger: T.eleven - T.two, rise: 0.6 });
    hook(ctx, t, { at: T.prices, until: T.pay - 0.15, text: 'PRICES DO FALL...', y: 330, size: 72 });
    hook(ctx, t, { at: T.pay, until: T.mattei - 0.15, lines: ['PAID WITH', 'THEIR JOBS'], y: 350, size: 96, colour: INK.amber });
    credit(ctx, t, { at: T.mattei, until: T.last + 2, text: 'Clara E. Mattei, The Capital Order (2022)', y: 560, size: 28 });
    hook(ctx, t, { at: T.mattei + 0.1, until: T.with - 0.15, text: 'MATTEI:', y: 270, size: 52, colour: INK.amber });
    hook(ctx, t, { at: T.part, until: T.with - 0.15, lines: ['PART OF', 'THE POINT'], y: 400, size: 96 });
    hook(ctx, t, { at: T.fewer, until: T.workers - 0.1, text: 'FEWER JOBS', y: 340, size: 88 });
    hook(ctx, t, { at: T.power - 0.1, until: T.last + 2, text: 'MATTEI:', y: 250, size: 44, colour: INK.amber });
    hook(ctx, t, { at: T.power, until: T.last + 2, lines: ['LESS POWER', 'TO ASK FOR MORE'], y: 370, size: 84 });
    return true;
  }

  return { pose, draw2D };
}
