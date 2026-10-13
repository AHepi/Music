// What this does: the house sample (log 27), about 37 seconds with no narration, showing how plan 2
// ("the house", experiments/26 Plans) would carry chapter 3 (Britain in the 1920s). One tall building
// of society, cut open at the front (house-set.js), seen whole at night:
//   0-7 s    Britain, 1922: the floors light up from the top down, each named: where it's decided
//            (the Treasury and the Bank's vault), what public money builds (council houses, a school),
//            work and home (a factory floor, a kitchen), the mine.
//   8-11 s   THE CUTS: scissors appear on the committee's table, then land in the middle floor below;
//            the scaffolding falls, the bricklayers and
//            the half-built houses fold away, the floor goes dark; the school keeps half its light.
//   12-16 s  the camera moves in to the vault (move 1): BACK ON GOLD, AT THE PRE-WAR PRICE (1925): a
//            padlock lands on the gold that was there all along, with a jolt.
//   16-20 s  the camera moves down the house to the mine (move 2): the weight travels down, and dust is
//            shaken from the lit rooms' ceilings as the camera passes.
//   20-23 s  the mine's ceiling comes down, the miners bow and their pay packet shrinks: COAL OWNERS WANT
//            LOWER PAY, LONGER HOURS.
//   23-26 s  the camera pulls back to the whole house and the street (move 3).
//   26-32 s  1926, THE GENERAL STRIKE: the factory and the mine go dark, the chimneys stop smoking and a
//            crowd with placards fills the lit pavement; then the crowd fades, the miners stay in the
//            street and snow falls: LOCKED OUT, THE MINERS HELD OUT TILL NOVEMBER, THEN LOST.
//   32-37 s  everything dims but the committee room and the miners outside: ONE HOUSE / WHO DECIDES,
//            WHO PAYS, labelled DECIDES and PAYS, with a note that this is a sample after Clara E.
//            Mattei's argument whose history is not yet researched; fade to black.
// Checked by two independent helpers before filming (log 27); the facts on screen were confirmed for
// Britain (the 1922 cuts, gold at the pre-war parity in April 1925, the owners' demands, the General
// Strike of May 1926, the lockout until November).
// The camera rule holds: one shot, still except for three moves. No drawn portraits of real people;
// the figures are the series' invented cut-outs. Beat times come from examples/house-sample/timeline.json.

import { THREE, popUp, foldDown, dropIn, spring, clamp01, smooth, ramp, lerp } from '../cinema-kit.js';
import { contactShadow } from '../models.js';
import { Smoke } from '../effects.js';
import { placeTitle, hook, presence, INK } from '../graphics.js';
import { buildHouse, Snow, FallingDust, glowSprite, FLOORS, LEFT, RIGHT, DIVIDE, STREET, FRONT } from './house-set.js';

// a name for a floor: a small amber rule and white words on a dark plate, at the left edge
function floorLabel(ctx, t, { at, until, y, text, size = 30 }) {
  const a = presence(t, at, until, 0.3, 0.4);
  if (a <= 0) return false;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.font = `800 ${size}px Inter`; ctx.textBaseline = 'middle';
  const w = ctx.measureText(text).width, x = 54 + 14 * (1 - smooth((t - at) / 0.4));
  ctx.fillStyle = 'rgba(10,12,16,0.72)';
  ctx.beginPath(); ctx.roundRect(x - 16, y - size * 0.85, w + 32, size * 1.7, 10); ctx.fill();
  ctx.fillStyle = INK.amber; ctx.fillRect(x - 16, y - size * 0.85, 5, size * 1.7);
  ctx.fillStyle = INK.paper; ctx.fillText(text, x, y + 1);
  ctx.restore();
  return true;
}
// a small note on a dark plate (the sample's honesty line), one or more lines
function note(ctx, t, { at, until, y, lines, size = 32 }) {
  const a = presence(t, at, until, 0.4, 0.4);
  if (a <= 0) return false;
  ctx.save(); ctx.globalAlpha = a * 0.95;
  ctx.font = `600 ${size}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const w = Math.max(...lines.map((line) => ctx.measureText(line).width)) + 48, gap = size * 1.3;
  const h = gap * lines.length + size * 0.7;
  ctx.fillStyle = 'rgba(10,12,16,0.78)';
  ctx.beginPath(); ctx.roundRect(540 - w / 2, y - h / 2, w, h, 12); ctx.fill();
  ctx.fillStyle = 'rgba(242,237,227,0.88)';
  lines.forEach((line, i) => ctx.fillText(line, 540, y + (i - (lines.length - 1) / 2) * gap + 1));
  ctx.restore();
  return true;
}
// a hook on a dark plate, for words over busy or pale parts of the picture
function platedHook(ctx, t, { at, until, lines, y, size, colour = INK.paper }) {
  const a = presence(t, at, until, 0.12, 0.3);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a * 0.8;
    ctx.font = `800 ${size}px Inter`;
    const w = Math.max(...lines.map((line) => ctx.measureText(line).width)) + size * 1.1;
    const h = lines.length * size * 1.02 + size * 0.75;
    ctx.fillStyle = 'rgba(10,12,16,0.72)';
    ctx.beginPath(); ctx.roundRect(540 - w / 2, y - h / 2, w, h, 16); ctx.fill();
    ctx.restore();
  }
  return hook(ctx, t, { at, until, lines, y, size, colour });
}

// Sets a cut-out's pose so that it can fade smoothly. Two things stop a plain cut-out from fading:
// it is drawn only where it is at least half solid (so a fade snaps off half way), and a piece first
// drawn as solid keeps a drawing recipe that ignores see-through until the recipe is rebuilt. So a
// fading piece is always drawn as see-through-capable (its recipe built once), and while it fades it
// is drawn down to nearly see-through.
function setFading(piece, pose) {
  piece.set(pose);
  for (const mesh of [piece.front, piece.back]) {
    mesh.material.transparent = true;
    if (!mesh.material.userData.fadeReady) { mesh.material.needsUpdate = true; mesh.material.userData.fadeReady = true; }
  }
  const fading = pose.opacity !== undefined && pose.opacity < 0.999;
  piece.front.material.alphaTest = fading ? 0.02 : 0.5;
}

export async function build(kit) {
  // night: a cool moon from the upper left, a dark sky; the rooms are lit by their own lamps
  kit.lightRig({ keyColour: 0xa9bde0, keyShare: 0.8, keyFrom: [-9, 22, 20], keyTarget: [0, 7, 0], fillSky: 0x4a5a7a, fillGround: 0x1a1612,
    fillShare: 0.5, haze: 0x0a0f18, hazeDensity: 0.004, background: 0x06090f, reflections: 0.08 });
  kit.lights.key.castShadow = false;

  const T = {
    title: kit.at('britain'), decided: kit.at('decided'), builds: kit.at('builds'), home: kit.at('home'), mine: kit.at('mine'),
    cuts: kit.at('cuts'), gold: kit.at('gold'), owners: kit.at('owners'), strike: kit.at('strike'), months: kit.at('months'),
    house: kit.at('house'), end: kit.at('end'),
  };
  T.scissorsUp = T.cuts - 0.05;          // the scissors appear on the committee's table...
  T.scissorsLeave = T.cuts + 0.35;        // ...leave it, passing in front of the floor below...
  T.scissorsLand = T.cuts + 0.85;         // ...and land in the building site
  T.zoomIn = [T.cuts + 3.8, T.cuts + 5.8];
  T.padlock = T.gold + 0.55;              // the pound locked to gold
  T.down = [T.gold + 2.6, T.gold + 6.6];
  T.squeeze = [T.owners - 0.4, T.owners + 0.8];
  T.zoomOut = [T.owners + 2.4, T.owners + 5.0];
  T.walkOut = T.strike + 0.1;

  const house = await buildHouse(kit);
  const { rooms } = house;
  const F = FLOORS;
  const shadowUnder = (x, y, z, width, depth = 0.5, darkness = 0.5) => {
    const s = contactShadow(width, depth, darkness); s.position.set(x, y + 0.006, z); kit.scene.add(s); return s;
  };

  // ---- the Treasury and the vault
  const delegates = rooms.treasury.holds(await kit.cutout('delegates', { at: [-1.95, F.top.bottom, -1.25], width: 3.7 }));
  shadowUnder(-1.95, F.top.bottom, -1.2, 3.6, 0.6);
  // the gold is in the vault from the start; going back on gold locks the pound to it
  const goldBars = [];
  for (const [i, x] of [1.55, 2.6, 3.6].entries()) {
    const bars = rooms.vault.holds(await kit.cutout('gold-bars', { at: [x, F.top.bottom, -1.5 + 0.25 * (i % 2)], width: 1.15 }));
    const glint = glowSprite(0xffd46a, 1.4, 0.0);
    glint.position.set(x, F.top.bottom + 0.45, -1.2 + 0.25 * (i % 2));
    kit.scene.add(glint);
    goldBars.push({ bars, glint, x });
  }
  const padlock = rooms.vault.holds(await kit.cutout('padlock', { at: [2.6, F.top.bottom, -0.75], width: 0.95 }));
  const shelfMaterial = new THREE.MeshLambertMaterial({ color: 0x3a3a34, emissive: 0x1a1a14, emissiveIntensity: 0.5 });
  shelfMaterial.userData.glow = 0.5;
  rooms.vault.materials.push(shelfMaterial);
  for (const y of [12.5, 13.4]) {
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.08, 0.45), shelfMaterial);
    shelf.position.set((DIVIDE + RIGHT) / 2 + 0.07, y, FRONT - 2.75);
    kit.scene.add(shelf);
  }

  // ---- the building site and the school
  const houses = rooms.site.holds(await kit.cutout('council-houses', { at: [-1.75, F.middle.bottom, -2.0], width: 4.3 }));
  const school = await kit.cutout('school', { at: [2.65, F.middle.bottom, -1.7], width: 2.25 });
  school.front.material.userData.baseGlow = school.front.material.emissiveIntensity;
  school.front.material.userData.baseColour = school.front.material.color.clone();
  const scaffoldMaterial = new THREE.MeshLambertMaterial({ color: 0x7a6248, emissive: 0x3a2a18, emissiveIntensity: 0.9 });
  scaffoldMaterial.userData.glow = 0.9;
  rooms.site.materials.push(scaffoldMaterial);
  const scaffold = new THREE.Group();
  scaffold.position.set(-1.75, F.middle.bottom, -1.1);
  kit.scene.add(scaffold);
  for (const x of [-1.9, -0.65, 0.6, 1.85]) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 2.7, 6), scaffoldMaterial);
    pole.position.set(x, 1.35, 0); scaffold.add(pole);
  }
  for (const y of [1.0, 2.0]) {
    const ledger = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 4.0, 6), scaffoldMaterial);
    ledger.rotation.z = Math.PI / 2; ledger.position.set(0, y, 0.02); scaffold.add(ledger);
    const plank = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.05, 0.32), scaffoldMaterial);
    plank.position.set(0, y + 0.03, 0.12); scaffold.add(plank);
  }
  const bricklayerUp = rooms.site.holds(await kit.cutout('worker-standing', { at: [-2.95, F.middle.bottom + 1.06, -0.9], width: 0.56 }));
  const bricklayerDown = rooms.site.holds(await kit.cutout('worker-standing', { at: [-0.25, F.middle.bottom, -0.55], width: 0.6, yaw: -0.2 }));
  const materials = rooms.site.holds(await kit.cutout('materials', { at: [0.95, F.middle.bottom, -0.7], width: 1.35 }));
  shadowUnder(-0.25, F.middle.bottom, -0.5, 0.7, 0.3); shadowUnder(0.95, F.middle.bottom, -0.65, 1.3, 0.4); shadowUnder(2.65, F.middle.bottom, -1.65, 2.2, 0.5);
  // one pair of scissors: it stands on the committee's table, then travels down to the building site
  const scissorsRest = [0.95, F.middle.bottom + 0.05, -0.35];
  const scissors = await kit.cutout('scissors-chain', { at: scissorsRest, width: 2.0 });
  const onTable = { dx: -1.25 - scissorsRest[0], dy: F.top.bottom - scissorsRest[1], dz: -0.45 - scissorsRest[2], scale: 0.525 };

  // ---- the factory floor and the kitchen
  const lathe = rooms.factory.holds(await kit.cutout('lathe', { at: [-2.45, F.ground.bottom, -1.35], width: 2.05 }));
  const machinist = rooms.factory.holds(await kit.cutout('worker-standing', { at: [-0.85, F.ground.bottom, -0.95], width: 0.62, yaw: -0.15 }));
  const table = rooms.kitchen.holds(await kit.cutout('kitchen-table', { at: [2.45, F.ground.bottom, -1.05], width: 1.95 }));
  const kitchenPacket = rooms.kitchen.holds(await kit.cutout('pay-packet', { at: [2.2, F.ground.bottom + 0.9, -0.92], width: 0.62 }));
  shadowUnder(-2.45, F.ground.bottom, -1.3, 2.0, 0.5); shadowUnder(-0.85, F.ground.bottom, -0.9, 0.7, 0.3); shadowUnder(2.45, F.ground.bottom, -1.0, 1.9, 0.5);

  // ---- the mine: three miners with lamps
  const miners = [];
  for (const [i, x] of [-1.45, 0.25, 1.85].entries()) {
    const miner = rooms.mine.holds(await kit.cutout('worker-standing', { at: [x, F.cellar.bottom, -1.25 + 0.12 * i], width: 0.5, yaw: (i - 1) * 0.12 }));
    const lamp = glowSprite(0xffd890, 0.12, 0.6);
    lamp.position.set(x - 0.02, F.cellar.bottom + 1.3, -1.17 + 0.12 * i);
    kit.scene.add(lamp);
    const halo = glowSprite(0xffb050, 0.6, 0.1);
    halo.position.set(x - 0.02, F.cellar.bottom + 1.4, -1.17 + 0.12 * i); kit.scene.add(halo);
    shadowUnder(x, F.cellar.bottom, -1.2 + 0.12 * i, 0.6, 0.3);
    miners.push({ miner, lamp, halo, x });
  }

  // the miners' pay packet, standing on the mine floor: it shrinks when the owners want lower pay
  const packet = rooms.mine.holds(await kit.cutout('pay-packet', { at: [1.05, F.cellar.bottom, -0.55], width: 0.8 }));
  rooms.mine.holds(await kit.card(['WAGES'], { size: 0.13, thickness: 0, at: [0, 0.2, 0.006], parent: packet.hinge, look: { cardColour: '#efe7d2' } }));
  shadowUnder(1.05, F.cellar.bottom, -0.5, 0.8, 0.25);

  // ---- the street: a crowd with placards, then the miners who stay out (on the lit pavement)
  const crowd = await kit.cutout('crowd-back', { at: [0.3, STREET, 3.6], width: 5.6 });
  const streetMiners = [];
  for (const [i, [x, width, yaw]] of [[-2.6, 0.66, 0.18], [-0.6, 0.72, -0.06], [1.2, 0.68, -0.2]].entries()) {
    streetMiners.push(await kit.cutout('worker-standing', { at: [x, STREET, 3.7 + 0.1 * i], width, yaw }));
  }

  // ---- air: chimney smoke, dust falling from ceilings, snow
  const smoke = house.chimneys.map((origin, i) => ({ origin, effect: new Smoke(kit.scene, { count: 12, life: 3.2, seed: 5 + i, colour: [168, 170, 178] }) }));
  // dust shaken down from the ceilings of the lit rooms as the weight travels down
  const dust = [
    { effect: new FallingDust(kit.scene, { x0: LEFT + 0.2, x1: DIVIDE - 0.3, y: F.ground.top - 0.05, seed: 51 }), at: T.down[0] + 1.7, floor: F.ground.bottom },
    { effect: new FallingDust(kit.scene, { x0: DIVIDE + 0.3, x1: RIGHT - 0.2, y: F.ground.top - 0.05, seed: 52 }), at: T.down[0] + 1.95, floor: F.ground.bottom },
    { effect: new FallingDust(kit.scene, { x0: LEFT + 0.2, x1: RIGHT - 0.2, y: F.cellar.top - 0.75, seed: 53, count: 220 }), at: T.squeeze[0] + 0.1, floor: F.cellar.bottom },
  ];
  const snow = new Snow(kit.scene, { count: 380, min: [-5.5, 0, 2.0], max: [5.5, 17.5, 7.5], size: 0.12 });

  // jolts: the scissors landing, each gold bar, the mine's ceiling coming down
  kit.shake(T.scissorsLand, 0.05, 0.16);
  kit.shake(T.padlock, 0.06, 0.16);
  kit.shake(T.down[0] + 1.7, 0.02, 0.2);
  kit.shake(T.squeeze[0] + 0.3, 0.025, 0.25);

  // ---- the camera: one still shot with three moves
  const whole = { position: [0, 8.35, 23.6], target: [0, 8.35, 0], fov: 40, focus: 24.8 };
  const shot = kit.stillShot(whole, [
    { kind: 'zoom in', from: T.zoomIn[0], to: T.zoomIn[1], position: [2.35, 12.85, 9.4], target: [2.35, 12.7, -1.5], focus: 10.7 },
    { kind: 'pan down', from: T.down[0], to: T.down[1], position: [0.25, 4.25, 9.4], target: [0.25, 4.1, -1.5], focus: 10.6 },
    { kind: 'zoom out', from: T.zoomOut[0], to: T.zoomOut[1], position: [0, 8.1, 25.4], target: [0, 8.1, 0], focus: 25.6 },
  ], { name: 'the house' });

  function pose(t) {
    // rooms light up from the top down, then go dark as the story says
    const on = (at) => smooth((t - at) / 0.6);
    // the end: everything dims except the committee room (who decides) and the miners outside (who pay)
    const ending = smooth((t - T.house) / 1.2);
    const dimAtEnd = (level, to) => lerp(level, to, ending);
    const top = on(T.decided);
    rooms.treasury.setLevel(top);
    rooms.vault.setLevel(dimAtEnd(top, 0.45));
    const siteLevel = on(T.builds) * lerp(1, 0.1, smooth((t - (T.scissorsLand + 0.3)) / 1.0));
    rooms.site.setLevel(dimAtEnd(siteLevel, 0.04));
    const schoolLevel = dimAtEnd(on(T.builds) * lerp(1, 0.4, smooth((t - (T.scissorsLand + 0.5)) / 1.0)), 0.15);
    school.front.material.emissiveIntensity = school.front.material.userData.baseGlow * (0.02 + 0.98 * schoolLevel);
    school.front.material.color.copy(school.front.material.userData.baseColour).multiplyScalar(0.05 + 0.95 * schoolLevel);
    rooms.site.schoolLamp.material.opacity = 0.35 * schoolLevel;
    const struck = smooth((t - (T.walkOut + 0.2)) / 0.9);
    rooms.factory.setLevel(dimAtEnd(on(T.home) * lerp(1, 0.25, struck), 0.06));
    rooms.kitchen.setLevel(dimAtEnd(on(T.home), 0.15));
    const mineLevel = on(T.mine) * lerp(1, 0.8, smooth((t - T.squeeze[0]) / 1.2)) * lerp(1, 0.22, struck);   // left empty, faintly lit
    rooms.mine.setLevel(dimAtEnd(mineLevel, 0.08));

    // the cuts
    // the scissors: fade in on the committee's table, travel down in front of the floor below, land and
    // snip in the building site, then fade away
    if (t < T.scissorsUp) scissors.set({ visible: false });
    else if (t < T.scissorsLeave) {
      const k = smooth((t - T.scissorsUp) / 0.2);
      setFading(scissors, { ...onTable, dy: onTable.dy + 0.15 * (1 - k), opacity: k });
    } else if (t < T.scissorsLand) {
      const u = (t - T.scissorsLeave) / (T.scissorsLand - T.scissorsLeave);
      setFading(scissors, { dx: lerp(onTable.dx, 0, smooth(u)), dy: onTable.dy * (1 - u * u), dz: lerp(onTable.dz, 0, u) + 1.4 * Math.sin(Math.PI * u),
        scale: lerp(onTable.scale, 1, smooth(u)), roll: 0.35 * Math.sin(Math.PI * u), opacity: 1 });
    } else if (t < T.scissorsLand + 2.2) {
      const landed = dropIn(t, T.scissorsLand, { bounce: 0.2, roll: 0.3 });
      const snip = 0.18 * Math.sin((t - T.scissorsLand) * 14) * Math.exp(-(t - T.scissorsLand) * 1.4);
      setFading(scissors, { ...landed, fold: 0, roll: (landed.roll ?? 0) + snip, opacity: 1 });
    } else {
      const k = smooth((t - (T.scissorsLand + 2.2)) / 0.5);
      setFading(scissors, k >= 1 ? { visible: false } : { opacity: 1 - k });
    }
    const fall = smooth((t - (T.scissorsLand + 0.2)) / 0.9);
    scaffold.rotation.z = -1.25 * fall * fall;
    scaffold.position.y = F.middle.bottom - 0.15 * fall;
    scaffold.visible = fall < 0.999 || t < T.scissorsLand + 3;
    const stand = (piece, at, extra = {}) => piece.set(t < at ? { ...extra } : foldDown(t, at, 0.55));
    stand(houses, T.scissorsLand + 0.6);
    stand(bricklayerUp, T.scissorsLand + 0.35);
    stand(bricklayerDown, T.scissorsLand + 0.5);
    stand(materials, T.scissorsLand + 0.75);
    school.set({});
    delegates.set({});
    lathe.set({});
    table.set({});

    // the gold glints; a padlock lands on it (the pound locked to gold at the pre-war price)
    const padlockAge = t - T.padlock;
    const flash = padlockAge < 0 ? 0 : 0.6 * smooth(padlockAge / 0.12) * Math.exp(-padlockAge * 3);
    for (const g of goldBars) {
      g.bars.set({});
      g.glint.material.opacity = top * (0.12 + flash);
    }
    // the padlock fades in as it starts to fall from just under the vault's ceiling
    const padlockPose = dropIn(t, T.padlock, { fall: 0.45, height: 1.45, roll: 0.2, bounce: 0.22 });
    setFading(padlock, padlockPose.visible ? { ...padlockPose, opacity: smooth((t - (T.padlock - 0.45)) / 0.15) } : padlockPose);
    kitchenPacket.set({});
    // the miners' pay packet shrinks when the owners want lower pay
    const shrink = smooth((t - (T.owners + 0.15)) / 0.8);
    const gone = (start, length = 0.45) => { const k = smooth((t - start) / length); return k >= 1 ? { visible: false } : { opacity: 1 - k }; };
    setFading(packet, t < T.walkOut + 0.3 ? { scale: lerp(1, 0.45, shrink), opacity: 1 } : { ...gone(T.walkOut + 0.3), scale: 0.45 });
    // the mine's ceiling comes down; the miners bow
    const squeeze = smooth((t - T.squeeze[0]) / (T.squeeze[1] - T.squeeze[0]));
    house.setMineCeiling(lerp(F.cellar.top, F.cellar.top - 0.95, squeeze));
    for (const [i, m] of miners.entries()) {
      const leave = T.walkOut + 0.1 * i;
      if (t < leave) setFading(m.miner, { fold: 0.22 * squeeze, dy: -0.04 * squeeze, opacity: 1 });
      else setFading(m.miner, { ...gone(leave, 0.4), fold: 0.22 });
      const lit = t < leave ? 1 : 1 - smooth((t - leave) / 0.4);
      m.lamp.material.opacity = 0.6 * lit; m.halo.material.opacity = 0.1 * lit;
      m.lamp.position.y = F.cellar.bottom + 1.3 - 0.1 * squeeze; m.halo.position.y = m.lamp.position.y + 0.1;
    }
    // the machinist walks out with the strike
    setFading(machinist, t < T.walkOut ? { opacity: 1 } : gone(T.walkOut, 0.45));

    // the street: the crowd pops up on "strike", folds away on "months", the miners stay
    // (they fade in and out standing up: a cut-out folded flat low in the frame shows its pale back)
    const arrive = (start, length = 0.5) => {
      if (t < start) return { visible: false };
      const k = smooth((t - start) / length);
      return { opacity: k, dy: -0.25 * (1 - k) };
    };
    setFading(crowd, t < T.months ? arrive(T.walkOut + 0.25, 0.6) : gone(T.months, 0.7));
    for (const [i, m] of streetMiners.entries()) setFading(m, arrive(T.months + 0.35 + 0.15 * i, 0.45));

    // air
    for (const s of smoke) s.effect.set({ t, origin: s.origin, until: T.walkOut + 0.4, scale: 0.9, wind: 0.6 });
    for (const d of dust) d.effect.set(t, d.at, d.floor);
    snow.set(t, 0.85 * smooth((t - (T.months - 0.3)) / 1.2) * (1 - smooth((t - (T.end + 0.3)) / 0.8)));

    const fade = Math.max(1 - clamp01(t / 1.0), smooth((t - (T.end + 0.1)) / 1.0));
    const close = ramp(t, T.zoomIn[0], T.zoomIn[1]) * (1 - ramp(t, T.zoomOut[0], T.zoomOut[1]));
    return {
      camera: shot(t),
      look: { exposure: 1.02, aperture: lerp(2.5, 5, close), maxBlur: 9, glowThreshold: 0.84, glowStrength: 0.72, contrast: 1.06, vignette: 0.38, fade },
    };
  }

  function draw2D(ctx, t) {
    const screenY = (x, y) => kit.toScreen(new THREE.Vector3(x, y, 0)).y;
    placeTitle(ctx, t, { at: T.title, until: T.cuts - 0.2, place: 'Britain', year: 1922, y: 200 });
    floorLabel(ctx, t, { at: T.decided + 0.2, until: T.cuts - 0.3, y: screenY(LEFT, FLOORS.top.top - 0.4), text: "WHERE IT'S DECIDED" });
    floorLabel(ctx, t, { at: T.builds + 0.2, until: T.cuts - 0.3, y: screenY(LEFT, FLOORS.middle.top - 0.4), text: 'WHAT PUBLIC MONEY BUILDS' });
    floorLabel(ctx, t, { at: T.home + 0.2, until: T.cuts - 0.3, y: screenY(LEFT, FLOORS.ground.top - 0.4), text: 'WORK AND HOME' });
    floorLabel(ctx, t, { at: T.mine + 0.2, until: T.cuts - 0.3, y: screenY(LEFT, FLOORS.cellar.top - 0.45), text: 'THE MINE' });
    hook(ctx, t, { at: T.cuts, until: T.zoomIn[0] - 0.2, text: 'THE CUTS', y: 215, size: 88 });
    placeTitle(ctx, t, { at: T.gold - 0.5, until: T.down[1], place: 'Britain', year: 1925, y: 180 });
    hook(ctx, t, { at: T.gold, until: T.down[0] + 1.0, text: 'BACK ON GOLD', y: 300, size: 80, colour: INK.amber });
    hook(ctx, t, { at: T.gold + 0.35, until: T.down[0] + 1.0, text: 'AT THE PRE-WAR PRICE', y: 375, size: 40 });
    // over the band of rock between the ground floor and the mine, where the beat happens
    platedHook(ctx, t, { at: T.owners, until: T.zoomOut[0] + 0.4, lines: ['COAL OWNERS WANT', 'LOWER PAY,', 'LONGER HOURS'], y: Math.min(1250, Math.max(700, screenY(0, FLOORS.cellar.top + 0.2))), size: 54 });
    placeTitle(ctx, t, { at: T.strike - 0.3, until: T.house - 0.2, place: 'Britain', year: 1926, y: 200 });
    platedHook(ctx, t, { at: T.strike, until: T.months - 0.2, lines: ['THE GENERAL', 'STRIKE'], y: 330, size: 80 });
    platedHook(ctx, t, { at: T.months + 0.2, until: T.house - 0.2, lines: ['LOCKED OUT, THE MINERS', 'HELD OUT TILL NOVEMBER,', 'THEN LOST'], y: 345, size: 50 });
    platedHook(ctx, t, { at: T.house, until: T.end + 0.9, lines: ['ONE HOUSE'], y: 250, size: 92 });
    hook(ctx, t, { at: T.house + 0.5, until: T.end + 0.9, text: 'WHO DECIDES, WHO PAYS', y: 345, size: 54, colour: INK.amber });
    floorLabel(ctx, t, { at: T.house + 0.9, until: T.end + 0.9, y: screenY(LEFT, FLOORS.top.top - 1.3), text: 'DECIDES' });
    floorLabel(ctx, t, { at: T.house + 1.3, until: T.end + 0.9, y: kit.toScreen(new THREE.Vector3(LEFT, STREET + 1.75, 3.8)).y, text: 'PAYS' });
    note(ctx, t, { at: T.house + 1.6, until: T.end + 0.9, y: 1440, lines: ["A sample of the look for chapter 3, after Clara E. Mattei's", 'argument. History not yet researched.'] });
    return true;
  }

  return { pose, draw2D };
}
