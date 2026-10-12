// What this does: page 4 of chapter 2, "Glasgow, 1915" (the rent strikes, research C2-H04). We stand
// in a painted Glasgow tenement street at dusk (a painting with depth: wet cobbles, gas lamps), with a
// light rain falling and haze in the air.
//   - "Homes work the same way": the empty street; the word HOMES.
//   - "In 1915": a place-and-year title, GLASGOW 1915.
//   - "workers poured into Glasgow for war work": three long files of workers stream in from the
//     right and walk away up the street, one after another.
//   - "landlords pushed rents up... by as much as a quarter": the camera closes in on a notice board
//     standing in the street; a printed notice (RENT RAISED) slaps onto it, then UP TO +25% / AS MUCH AS A QUARTER.
//   - "By November, about twenty thousand households were refusing to pay the rise": a row of
//     rent strikers with placards pops up on the pavement under the notice; 20,000 counts up,
//     HOUSEHOLDS REFUSING TO PAY.
//   - "Within weeks, Parliament froze rents": a rubber stamp slams down on the notice (shake, dust)
//     and lifts away, leaving a red RENTS FROZEN stamp on it.
//   - "Homes can't be built in a hurry": a quick dip to black on "homes" cuts to a small card house
//     on the cobbles, its walls going up one slow course at a time beside the faint outline of the
//     finished house; HOMES CAN'T BE BUILT / IN A HURRY.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, foldDown, clamp01, smooth, ramp, lerp, seededRandom, spring, walkBob, knock } from '../cinema-kit.js';
import { paper, PAPER, contactShadow } from '../models.js';
import { Motes, DustBurst } from '../effects.js';
import { placeTitle, hook, counter, presence, INK } from '../graphics.js';

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    homes: kit.at('homes'),
    y1915: kit.at('1915'),
    workers: kit.at('workers'),
    poured: kit.at('poured'),
    glasgow: kit.at('glasgow'),
    landlords: kit.at('landlords'),
    pushed: kit.at('pushed'),
    by: kit.at('by'),
    quarter: kit.at('quarter'),
    november: kit.at('november'),
    about: kit.at('about'),
    twenty: kit.at('twenty'),
    households: kit.at('households'),
    refusing: kit.at('refusing'),
    rise: kit.at('rise'),
    within: kit.at('within'),
    parliament: kit.at('parliament'),
    froze: kit.at('froze'),
    homes2: kit.at('homes', 2),
    hurry: kit.at('hurry'),
    last: kit.lastWordEnd,
  };
  T.slam = T.froze + 0.12;
  // "Homes can't be built": a quick dip to black that bottoms out on "homes"; under the black the
  // wall scene (board, notice, stamp, strikers) is hidden and the camera cuts to the building site,
  // so the foundation shot starts clean
  T.cut = T.homes2;
  T.dipIn = 0.22; T.dipOut = 0.26;

  kit.lightRig({ keyColour: 0xffc887, keyShare: 0.72, keyFrom: [4, 6, -4], keyTarget: [-1.5, -2, -15], fillSky: 0x5f7a92, fillGround: 0x2a241e,
    fillShare: 0.22, haze: 0x182230, hazeDensity: 0.005, shadowBox: 12, shadowSoftness: 5, background: 0x0f1720, reflections: 0.3 });
  const street = await kit.relief('403-bg-glasgow-tenements', { near: 6, far: 70, fov: 40 });
  const P = (u, v, k = 1) => street.pointAt(u, v).multiplyScalar(k);

  // ------------------------------------------------------------------ nothing passes into the street
  // gapAt: how far a world point stands in front of the painted surface behind it (negative = inside
  // the painting). objectGap samples every vertex of an object's meshes (plus extra points along the
  // bottom of flat cut-outs and the slab, since a box or card has corners only). liftFor finds the
  // smallest raise that keeps an object clear in every pose it will take; all of it runs once, here
  // in build, so pose(t) stays a function of t alone.
  const gapAt = (p) => {
    const d = -p.z;
    if (d < 0.05) return Infinity;
    return street.distanceAt((p.x / d / street.tanX + 1) / 2, (p.y / d / street.tanY + 1) / 2) - d;
  };
  const objectGap = (object, extra = []) => {
    object.updateMatrixWorld(true);
    let least = Infinity;
    const p = new THREE.Vector3();
    object.traverse((o) => {
      if (!o.isMesh) return;
      const position = o.geometry.attributes.position;
      for (let i = 0; i < position.count; i++) least = Math.min(least, gapAt(p.fromBufferAttribute(position, i).applyMatrix4(o.matrixWorld)));
    });
    for (const [o, local] of extra) least = Math.min(least, gapAt(o.localToWorld(local.clone())));
    return least;
  };
  const cardEdge = (piece) => Array.from({ length: 13 }, (_, i) => [piece.hinge, new THREE.Vector3((i / 12 - 0.5) * piece.width, 0, 0)]);
  // the smallest raise (world units, upward) at which `measure(raise)` (posing the object every way it
  // will be posed, returning the least gap) reaches `wanted`
  const liftFor = (measure, wanted) => {
    let lo = -0.6, hi = 1.2;
    for (let i = 0; i < 30; i++) { const mid = (lo + hi) / 2; if (measure(mid) >= wanted) hi = mid; else lo = mid; }
    return hi;
  };

  // ------------------------------------------------------------------ rain and haze
  const motes = new Motes(kit.scene, { count: 160, min: [-3, -2.2, -20], max: [3, 2.5, -5], size: 0.035, colour: 0xcfe0ff, seed: 41, opacity: 0.45 });
  const RAIN = 520, rainTop = 3.5, rainHeight = 6.2, dropLength = 0.32;
  const rainRandom = seededRandom(404);
  const drops = Array.from({ length: RAIN }, () => ({ x: lerp(-4, 4, rainRandom()), z: lerp(-22, -4, rainRandom()), phase: rainRandom(), speed: 0.85 + rainRandom() * 0.3 }));
  const rainGeometry = new THREE.BufferGeometry();
  rainGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(RAIN * 6), 3));
  const rainMaterial = new THREE.LineBasicMaterial({ color: 0xb8cce0, transparent: true, opacity: 0.22, depthWrite: false, blending: THREE.AdditiveBlending });
  const rain = new THREE.LineSegments(rainGeometry, rainMaterial);
  rain.frustumCulled = false;
  kit.scene.add(rain);
  function setRain(t) {
    const a = rainGeometry.attributes.position.array;
    drops.forEach((d, i) => {
      const fall = ((t * 7.5 * d.speed) / rainHeight + d.phase) % 1;
      const y = rainTop - fall * rainHeight;
      a.set([d.x + 0.04 * (1 - fall), y, d.z, d.x + 0.04 * (1 - fall) + 0.03, y + dropLength, d.z], i * 6);
    });
    rainGeometry.attributes.position.needsUpdate = true;
  }

  // ------------------------------------------------------------------ workers pouring in
  // three files of workers (painted side-view, facing left), turned so each file heads away up the
  // street; they walk in from the right along their own line.
  const yaw = -0.45;
  const along = new THREE.Vector3(-Math.cos(yaw), 0, Math.sin(yaw)); // the way they face and walk
  const files = [];
  const fileSpecs = [
    // the first file walks in from beyond the right edge under "1915", so the street is never empty
    // for long; each starts out of frame (pushed back along its line by `back`) and ends about where it did
    { start: [1.0, -2.13, -8.0], back: 2.1, width: 3.0, at: T.y1915 - 0.7, speed: 1.15 },
    { start: [2.0, -2.08, -11.0], back: 1.6, width: 3.2, at: T.workers - 1.2, speed: 1.1 },
    { start: [2.9, -2.03, -14.5], back: 1.6, width: 3.4, at: T.workers - 0.4, speed: 1.21 },
  ];
  for (const spec of fileSpecs) {
    spec.start = new THREE.Vector3(...spec.start).addScaledVector(along, -spec.back).toArray();
    const piece = await kit.cutout('workers-queue', { at: spec.start, width: spec.width, yaw });
    files.push({ piece, ...spec });
  }
  // they walk until the camera has panned away to the notice board (by then they are out of frame),
  // then go; along their walk the cobbles rise and fall, so each file gets a raise for every 0.1 s
  // that keeps its feet on (never in) the street, bob included
  T.workersFold = T.landlords - 0.42; T.workersGone = T.workersFold + 0.25; // gone before the board rises where they stood
  for (const f of files) {
    const steps = Math.ceil((T.workersFold - f.at) / 0.1) + 1;
    const raw = Array.from({ length: steps + 1 }, (_, i) => {
      const move = along.clone().multiplyScalar(f.speed * i * 0.1);
      return liftFor((dy) => { f.piece.set({ dx: move.x, dz: move.z, dy }); return objectGap(f.piece.anchor, cardEdge(f.piece)); }, 0.06);
    });
    // never dip between samples: each step keeps the larger of itself and its neighbours
    f.lift = raw.map((v, i) => Math.max(v, raw[i - 1] ?? v, raw[i + 1] ?? v));
    f.liftAt = (t) => { const x = clamp01((t - f.at) / ((steps) * 0.1)) * steps, i = Math.min(steps - 1, Math.floor(x)); return lerp(f.lift[i], f.lift[i + 1], x - i); };
    // folding away: a raise for each fold angle, at the spot where the fold happens
    const at = along.clone().multiplyScalar(f.speed * (T.workersFold - f.at));
    f.foldLift = [0, 0.3, 0.6, 0.9, 1.2, Math.PI / 2].map((fold) => [fold, liftFor((dy) => {
      f.piece.set({ fold, dx: at.x, dz: at.z, dy }); return objectGap(f.piece.anchor, cardEdge(f.piece)); }, 0.06)]);
    f.piece.set({ visible: false });
  }
  const foldLiftAt = (f, fold) => {
    const L = f.foldLift;
    for (let i = 1; i < L.length; i++) if (fold <= L[i][0]) return Math.max(L[i - 1][1], L[i][1]);
    return L[L.length - 1][1];
  };

  // ------------------------------------------------------------------ the notice on the wall
  // a wooden notice board on two posts, standing on the left-hand pavement; the landlords' notice
  // is slapped onto it
  // it stands in the roadway on flat cobbles (u about 0.37-0.63, v 0.24), right of and in front of
  // the painted puddle that read as a pit under the posts when the board stood at u 0.13-0.36
  const boardFoot = P(0.5, 0.25, 1.0);
  boardFoot.x = 0.22; boardFoot.z = -11.0;
  const noticeYaw = 0.22;
  const boardW = 1.55, boardH = 0.78, postH = 1.25;
  const boardGroup = new THREE.Group();
  boardGroup.position.set(boardFoot.x, boardFoot.y, boardFoot.z);
  boardGroup.rotation.y = noticeYaw;
  const wood = paper(0x6b4e36, { roughness: 0.85 });
  const panel = new THREE.Mesh(new THREE.BoxGeometry(boardW, boardH, 0.05), wood);
  panel.position.set(0, postH + boardH / 2, 0);
  const posts = [-1, 1].map((side) => { const m = new THREE.Mesh(new THREE.BoxGeometry(0.07, postH + boardH * 0.9, 0.07), wood); m.position.set(side * boardW * 0.4, (postH + boardH * 0.9) / 2, -0.06); return m; });
  // a foot plate under each post and a soft contact shadow, so the board stands on the street
  const feet = [-1, 1].map((side) => { const m = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.05, 0.3), paper(0x4a3524, { roughness: 0.9 })); m.position.set(side * boardW * 0.4, 0.025, -0.06); return m; });
  boardGroup.add(panel, ...posts, ...feet);
  boardGroup.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  kit.scene.add(boardGroup);
  // stand the board on the pavement: the least raise that keeps its posts clear of the painted
  // street (it grows up from its feet, so it never lies on the cobbles)
  const boardLift = liftFor((dy) => { boardGroup.position.y = boardFoot.y + dy; return objectGap(boardGroup); }, 0.05);
  boardGroup.position.y = boardFoot.y + boardLift;
  boardFoot.y += boardLift;
  // the contact shadow: a soft dark patch just above the cobbles under the foot plates
  const boardShadow = contactShadow(boardW * 1.2, 0.6, 0.75);
  boardGroup.add(boardShadow);
  const shadowLift = liftFor((dy) => { boardShadow.position.set(0, dy, -0.06); return street.clearance(boardShadow); }, 0.006);
  boardShadow.position.set(0, shadowLift, -0.06);
  const facing = new THREE.Vector3(Math.sin(noticeYaw), 0, Math.cos(noticeYaw));
  const onBoard = (y, out = 0.03) => new THREE.Vector3(boardFoot.x, boardFoot.y + y, boardFoot.z).addScaledVector(facing, out);
  const noticeBase = onBoard(postH + 0.12, 0.05); // its back 0.005 in front of the board face
  const notice = await kit.card(['NOTICE', 'RENT RAISED'], { size: 0.15, at: noticeBase.toArray(), yaw: noticeYaw });
  const noticeCentre = noticeBase.clone().add(new THREE.Vector3(0, notice.height * 0.5, 0));
  const frozen = await kit.card(['RENTS', 'FROZEN'], { size: 0.145, at: onBoard(postH + 0.2, 0.06).toArray(), yaw: noticeYaw,
    look: { cardColour: '#b23a2a', inkColour: '#f2ede3', borderColour: 'rgba(242,237,227,0.7)' } });
  const stamp = await kit.cutout('rubber-stamp', { at: onBoard(postH + 0.28, 0.14).toArray(), width: 0.7, yaw: noticeYaw });
  const dust = new DustBurst(kit.scene, { count: 20, seed: 9, colour: 'rgba(150,140,128,0.9)' });

  // ------------------------------------------------------------------ the rent strikers
  const strikersAt = [boardFoot.x + 0.45, boardFoot.y - 0.08, -9.6];
  const strikers = await kit.cutout('rent-strikers', { at: strikersAt, width: 2.55, yaw: 0.15 });
  // their bottom edge on the cobbles in every fold of the pop-up (lying flat to standing)
  const strikersPop = { height: 1.18, restZ: 0.3 };
  const strikersLift = liftFor((dy) => Math.min(...[Math.PI / 2, 1.2, 0.8, 0.4, 0, -0.2].map((fold) => {
    strikers.set({ fold, dy }); return objectGap(strikers.anchor, cardEdge(strikers));
  })), 0.06);
  strikers.set({ visible: false });

  // ------------------------------------------------------------------ the house going up slowly
  const site = P(0.56, 0.205, 1.0);
  const house = new THREE.Group();
  house.position.copy(site);
  house.rotation.y = -0.5;
  kit.scene.add(house);
  const W = 1.3, D = 0.95, H = 0.9, COURSES = 10, courseH = H / COURSES, wallT = 0.07;
  const brickA = paper(PAPER.cream), brickB = paper(PAPER.card);
  const courses = [];
  for (let i = 0; i < COURSES; i++) {
    const course = new THREE.Group();
    const m = i % 2 ? brickA : brickB;
    for (const [w, d, x, z] of [[W, wallT, 0, D / 2 - wallT / 2], [W, wallT, 0, -D / 2 + wallT / 2], [wallT, D - 2 * wallT, W / 2 - wallT / 2, 0], [wallT, D - 2 * wallT, -W / 2 + wallT / 2, 0]]) {
      // a gap for the door in the front wall's lower courses
      if (z > 0 && i < 6) {
        for (const [ww, xx] of [[W * 0.38, -W * 0.31], [W * 0.38, W * 0.31]]) {
          const b = new THREE.Mesh(new THREE.BoxGeometry(ww, courseH * 0.94, d), m);
          b.position.set(xx, 0, z); b.castShadow = b.receiveShadow = true; course.add(b);
        }
        continue;
      }
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, courseH * 0.94, d), m);
      b.position.set(x, 0, z); b.castShadow = b.receiveShadow = true; course.add(b);
    }
    course.userData.y = 0.034 + courseH * (i + 0.5); // on the slab (top 0.03), never in it
    house.add(course);
    courses.push(course);
  }
  const slab = new THREE.Mesh(new THREE.BoxGeometry(W + 0.16, 0.03, D + 0.16), paper(PAPER.card));
  slab.position.y = 0.015; slab.receiveShadow = true; house.add(slab);
  // the faint outline of the finished house (walls and a pitched roof), drawn as thin glowing rods
  const outline = new THREE.Group();
  const lineMaterial = new THREE.MeshBasicMaterial({ color: 0xe8a33d, transparent: true, opacity: 0, depthWrite: false, fog: false });
  const corners = [];
  for (const y of [0, H]) for (const [x, z] of [[-W / 2, -D / 2], [W / 2, -D / 2], [W / 2, D / 2], [-W / 2, D / 2]]) corners.push(new THREE.Vector3(x, y, z));
  const ridgeF = new THREE.Vector3(0, H + 0.5, D / 2), ridgeB = new THREE.Vector3(0, H + 0.5, -D / 2);
  const edges = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]].map(([i, j]) => [corners[i], corners[j]]);
  edges.push([corners[7], ridgeF], [corners[6], ridgeF], [corners[4], ridgeB], [corners[5], ridgeB], [ridgeF, ridgeB]);
  for (const [p, q] of edges) {
    const length = p.distanceTo(q);
    // dashed: short rods along the edge
    const dashes = Math.max(2, Math.round(length / 0.09));
    for (let i = 0; i < dashes; i++) {
      const a0 = p.clone().lerp(q, i / dashes), a1 = p.clone().lerp(q, (i + 0.6) / dashes);
      const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.009, a0.distanceTo(a1), 5), lineMaterial);
      rod.position.copy(a0).add(a1).multiplyScalar(0.5);
      rod.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), a1.clone().sub(a0).normalize());
      outline.add(rod);
    }
  }
  outline.position.y = 0.034;
  house.add(outline);
  // the slab sits on the cobbles: raise the house until the slab's whole underside clears the street
  const slabUnder = [];
  for (let i = 0; i <= 8; i++) for (let j = 0; j <= 6; j++) slabUnder.push([slab, new THREE.Vector3((i / 8 - 0.5) * (W + 0.16), -0.015, (j / 6 - 0.5) * (D + 0.16))]);
  courses.forEach((course) => { course.position.y = course.userData.y; });
  const houseLift = liftFor((dy) => { house.position.y = site.y + dy; return objectGap(house, slabUnder); }, 0.05);
  house.position.y = site.y + houseLift;
  // one course every 0.75 s, from just after the cut: only a few are up by the end
  const courseAt = (i) => T.cut + 0.45 + i * 0.75;

  // ------------------------------------------------------------------ the camera
  const noticeFocus = [noticeCentre.x, noticeCentre.y, noticeCentre.z];
  const wallTarget2 = [noticeCentre.x + 0.3, noticeCentre.y - 0.22, noticeCentre.z]; // board sits a little right of the left edge
  // shot 1, the street: it holds still while the workers pour in; on "landlords" it zooms in onto
  // the notice board standing in the roadway and holds there through the
  // notice, the strikers and the count; on "within weeks" it narrows onto the notice for the stamp.
  const wallShot = kit.stillShot({ position: [0.1, -0.05, -0.5], target: [0.05, -1.0, -30], fov: 39, focus: 12 }, [
    { from: T.landlords - 0.15, to: T.pushed + 0.45, kind: 'zoom in', position: [0.4, -0.25, -1.3], target: [wallTarget2[0], wallTarget2[1] - 0.1, wallTarget2[2]], fov: 27.5, focus: noticeFocus },
    { from: T.rise - 0.2, to: T.rise + 0.3, kind: 'focus', focus: [strikersAt[0], strikersAt[1] + 0.7, strikersAt[2]] },
    { from: T.within, to: T.parliament + 0.4, kind: 'zoom in', position: [0.45, -0.3, -1.6], target: wallTarget2, fov: 24.5, focus: noticeFocus },
  ], { name: 'the street and the notice' });
  // shot 2, after the dip: the building site, held still while the walls creep up
  const siteFocus = [site.x, site.y + 0.4, site.z];
  const siteShot = kit.stillShot({ position: [0.25, -0.65, -2.4], target: [site.x, site.y + 0.8, site.z], fov: 25, focus: siteFocus }, [],
    { name: 'the building site' });
  const shot = (t) => (t < T.cut ? wallShot(t) : siteShot(t));
  kit.shake(T.slam, 0.02, 0.16);

  function pose(t) {
    motes.set(t);
    setRain(t);
    // workers stream in and fold away as the camera turns to the wall
    for (const f of files) {
      if (t < f.at || t > T.workersGone) { f.piece.set({ visible: false }); continue; }
      const move = along.clone().multiplyScalar(f.speed * (Math.min(t, T.workersFold) - f.at));
      if (t < T.workersFold) f.piece.set({ dx: move.x, dz: move.z, dy: f.liftAt(t) + walkBob(t, f.at, Infinity, 0.025, 2.2) });
      else {
        // they fold away (flat toward the camera) just before the camera turns, raised enough at every
        // angle that no part of them dips into the cobbles
        const folding = foldDown(t, T.workersFold, 0.25);
        f.piece.set({ ...folding, dx: move.x, dz: move.z, dy: Math.max(f.liftAt(T.workersFold), foldLiftAt(f, folding.fold)) });
      }
    }
    // the board pops up on "landlords"
    const boardUp = t < T.landlords - 0.1 ? 0 : 1 - spring(t - (T.landlords - 0.1), { stiffness: 14, damping: 0.6 });
    const wall = t < T.cut; // everything at the wall is hidden under the dip, never lowered or tipped
    boardGroup.visible = t > T.landlords - 0.1 && wall;
    boardGroup.scale.set(1, Math.max(0.001, boardUp), 1);
    // the notice slaps onto the board
    if (t < T.pushed) notice.set({ visible: false });
    else if (!wall) notice.set({ visible: false });
    else {
      const age = t - T.pushed;
      const k = spring(age, { stiffness: 18, damping: 0.6 });
      notice.set({ lift: 0.5 * Math.max(0, k), scale: 1 + 0.25 * Math.max(0, k), roll: -0.05 + 0.25 * k + knock(age - 0.15, 0.02) });
    }
    // the stamp: fades in hovering just above the notice (below the PARLIAMENT words), slams down on
    // "froze", then lifts a little and fades away within half a second, so RENTS FROZEN reads clear
    const stampDown = T.slam, stampFall = 0.2, hover = 0.42;
    if (t < T.within + 0.3 || t > stampDown + 0.5) stamp.set({ visible: false });
    else {
      let dy, opacity = 1;
      if (t < stampDown - stampFall) {
        dy = hover + 0.04 * Math.sin((t - T.within) * 5);
        opacity = smooth(ramp(t, T.within + 0.3, T.within + 0.6));
      } else if (t < stampDown) { const x = ramp(t, stampDown - stampFall, stampDown); dy = (hover + 0.04 * Math.sin((stampDown - stampFall - T.within) * 5)) * (1 - x * x); }
      else {
        dy = 0.02 * Math.exp(-(t - stampDown) / 0.06) + 0.35 * smooth(ramp(t, stampDown + 0.1, stampDown + 0.45));
        opacity = 1 - smooth(ramp(t, stampDown + 0.12, stampDown + 0.42));
      }
      const squash = t >= stampDown && t < stampDown + 0.3 ? 1 - 0.04 * Math.exp(-(t - stampDown) / 0.08) : 1;
      stamp.set({ visible: true, dy, lift: 0.12, scale: squash, opacity, roll: t < stampDown ? 0.05 * (1 - ramp(t, stampDown - 0.6, stampDown)) : 0 });
    }
    if (t < T.slam || !wall) frozen.set({ visible: false });
    else frozen.set({ lift: 0.03, roll: -0.13, scale: 1 + 0.12 * Math.exp(-(t - T.slam) / 0.07) });
    if (t > T.slam - 0.05 && t < Math.min(T.slam + 1.3, T.cut)) dust.set({ origin: [noticeCentre.x + 0.1, noticeCentre.y - 0.25, noticeCentre.z + 0.3], width: 1.0, age: t - T.slam, scale: 0.35 });
    else dust.hide();
    // the strikers pop up on "about" and stay until the camera leaves
    strikers.set(wall ? { ...popUp(t, T.about - 0.15, strikersPop), dy: strikersLift } : { visible: false });
    // the house: courses drop into place one by one; the outline fades in
    house.visible = !wall;
    lineMaterial.opacity = 0.75 * smooth(ramp(t, T.cut + 0.3, T.cut + 0.9));
    courses.forEach((course, i) => {
      const at = courseAt(i);
      const k = clamp01((t - (at - 0.25)) / 0.25);
      course.visible = t > at - 0.25;
      course.position.y = course.userData.y + 0.35 * (1 - k * k) + Math.max(0, knock(t - at, 0.004, 6, 0.1));
    });
    // the dip: black exactly on the cut, picture back about a quarter second later
    const fade = t < T.cut ? smooth(ramp(t, T.cut - T.dipIn, T.cut)) : 1 - smooth(ramp(t, T.cut, T.cut + T.dipOut));
    return { camera: shot(t), look: { aperture: 8, maxBlur: 14, exposure: 0.95, glowThreshold: 0.93, glowStrength: 0.68, contrast: 1.06, fade } };
  }

  function draw2D(ctx, t) {
    hook(ctx, t, { at: T.homes, until: T.y1915 - 0.1, text: 'HOMES', y: 330, size: 78, colour: INK.paper });
    placeTitle(ctx, t, { at: T.y1915, until: T.landlords - 0.2, place: 'Glasgow', year: 1915, y: 280 });
    hook(ctx, t, { at: T.workers + 0.2, until: T.landlords - 0.1, lines: ['WORKERS POUR IN'], y: 420, size: 62, colour: INK.muted });
    hook(ctx, t, { at: T.quarter - 0.1, until: T.november - 0.1, text: 'UP TO +25%', y: 330, size: 112, colour: INK.amber });
    // on a dark plate, so it reads over the lit building
    const plate = presence(t, T.quarter, T.november - 0.1, 0.12, 0.3);
    if (plate > 0) {
      ctx.save(); ctx.globalAlpha = 0.62 * plate; ctx.fillStyle = '#0b0f14';
      ctx.beginPath(); ctx.roundRect(150, 455 - 46, 780, 92, 18); ctx.fill(); ctx.restore();
    }
    hook(ctx, t, { at: T.quarter, until: T.november - 0.1, text: 'AS MUCH AS A QUARTER', y: 455, size: 52, colour: INK.paper });
    hook(ctx, t, { at: T.november, until: T.within - 0.2, text: 'BY NOVEMBER', y: 165, size: 38, colour: INK.paper });
    counter(ctx, t, { at: T.twenty - 0.05, until: T.within - 0.2, duration: 0.9, from: 0, to: 20000, y: 350, size: 150,
      format: (v) => (Math.round(v / 100) * 100).toLocaleString('en-GB') });
    hook(ctx, t, { at: T.about, until: T.within - 0.2, text: 'ABOUT', y: 220, size: 44, colour: INK.paper });
    hook(ctx, t, { at: T.refusing, until: T.within - 0.2, lines: ['HOUSEHOLDS', 'REFUSING TO PAY'], y: 480, size: 54, colour: INK.amber });
    hook(ctx, t, { at: T.parliament, until: T.homes2 - 0.2, text: 'PARLIAMENT', y: 200, size: 56, colour: INK.paper });
    hook(ctx, t, { at: T.homes2, until: T.last + 2, lines: ['HOMES CAN\u2019T', 'BE BUILT'], y: 330, size: 74 });
    hook(ctx, t, { at: T.hurry - 0.05, until: T.last + 2, text: 'IN A HURRY', y: 470, size: 74, colour: INK.amber });
    return true;
  }

  return { pose, draw2D };
}
