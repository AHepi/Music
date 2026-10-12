// What this does: page 8 of chapter 2, "so yes... and here, 2021". Three places, joined by quick dips:
//   A. The two-factories model set from page 3 (round 20: detailed Blender works in a model town).
//      "So yes": YES, IT CAN, held on works B (flat out): coins rain into its yard and its price
//      counter flips up at "flat out". At "things we can't make more of in a hurry" the camera zooms
//      out to make room as a card house pops up in front of works B and its tag climbs (arrows, plainly
//      illustrative, no figures).
//   B. "In twenty twenty-one": a painted New Zealand street (a painting with depth). Title NEW ZEALAND
//      2021; at "lowest" the figure 3.2% with UNEMPLOYMENT, LOWEST ON RECORD and a small line "Records
//      began in 1986". "House prices rose about thirty percent in twelve months": a card house pops up
//      on the pavement while its tag climbs a post ($, $$, $$$, plainly illustrative); +30% / IN 12
//      MONTHS as words only. Credit STATS NZ; REINZ.
//   C. "An independent review of the Reserve Bank": a reviewer's desk (Blender: wood, a leather
//      blotter, a banker's lamp, folders, typed papers, an ink pad, a pen, glasses, tea, bookshelves);
//      a printed report drops onto the blotter and lies flat (INDEPENDENT REVIEW / RESERVE BANK; credit INDEPENDENT REVIEW, SEPTEMBER 2026). The
//      rubber stamp comes down twice: RIGHT AT FIRST (teal) and TOO STRONG, FOR TOO LONG (red), each
//      also as a word hook under THE REVIEW: (it is the review's judgement).
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, clamp01, smooth, ramp, lerp, spring } from '../cinema-kit.js';
import { loadModel, markerAt } from '../model-loader.js';
import { paperHouse, priceTag, paper, PAPER, contactShadow } from '../models.js';
import { CoinRain, DustBurst, Motes } from '../effects.js';
import { placeTitle, hook, counter, callout, credit, presence, INK } from '../graphics.js';
import { buildTwoFactories, FACTORY_B } from './two-factories-set.js';

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    yes: kit.at('yes'),
    newMoney: kit.at('new'),
    when: kit.at('when'),
    spent: kit.at('spent'),
    workers: kit.at('workers'),
    flat: kit.at('flat'),
    or: kit.at('or'),
    things: kit.at('things'),
    cant: kit.at("can't"),
    make: kit.at('make'),
    of: kit.at('of'),
    hurry: kit.at('hurry'),
    inWord: kit.at('in', 2),
    twenty: kit.at('twenty'),
    unemployment: kit.at('unemployment'),
    lowest: kit.at('lowest'),
    began: kit.at('began'),
    house: kit.at('house'),
    rose: kit.at('rose'),
    thirty: kit.at('thirty'),
    percent: kit.at('percent'),
    twelve: kit.at('twelve'),
    an: kit.at('an'),
    review: kit.at('review'),
    reserve: kit.at('reserve'),
    says: kit.at('says'),
    support: kit.at('support'),
    was: kit.at('was'),
    right: kit.at('right'),
    first: kit.at('first'),
    but: kit.at('but'),
    too: kit.at('too'),
    strong: kit.at('strong'),
    long: kit.at('long'),
    end: kit.lastWordEnd,
  };
  // the two cuts (each hidden in a short dip to black)
  const CUT_B = T.inWord - 0.05;
  const CUT_C = T.an - 0.1;
  const DIP = 0.22;
  const phaseOf = (t) => (t < CUT_B ? 'A' : t < CUT_C ? 'B' : 'C');

  // ------------------------------------------------------------------ A and C: the model set
  const before = new Set(kit.scene.children);
  const set = await buildTwoFactories(kit);
  const { a, b } = set;
  const tableThings = kit.scene.children.filter((o) => !before.has(o) && !o.isLight && o !== kit.lights.key.target);
  const key = kit.lights.key, fill = kit.lights.fill;
  const setLight = { keyPos: key.position.clone(), keyTarget: key.target.position.clone(), key: key.intensity, fill: fill.intensity, fog: kit.scene.fog?.density ?? 0 };
  const own = []; // things of this page that belong to the table set (hidden in the street)
  const track = (o) => { own.push(o); return o; };

  // coins raining into factory B's yard, as the money is spent where it is flat out
  const beforeCoins = new Set(kit.scene.children);
  const coinsB = new CoinRain(kit.scene, { count: 22, centre: [b.yard.x + 0.2, 0, b.yard.z - 0.3], radius: 0.45, start: T.spent + 0.1, spread: 1.4, coinRadius: 0.06, seed: 12 });
  const dust = new DustBurst(kit.scene, { count: 16, seed: 9 });
  kit.scene.children.filter((o) => !beforeCoins.has(o)).forEach(track);
  const priceA = [{ t: T.start - 1, text: '£1.00' }];
  const priceB = [{ t: T.start - 1, text: '£1.00' }, { t: T.flat - 0.05, text: '£1.30' }, { t: T.flat + 0.3, text: '£1.70' }, { t: T.flat + 0.65, text: '£2.00' }];

  // a card house on the table, for "things we can't make more of in a hurry", with its tag on a post
  const HOUSE_A = new THREE.Vector3(1.6, 0.012, -1.4);   // in front of works B, its board behind it
  const houseA = paperHouse({ width: 1.0, depth: 0.95, height: 0.5, glow: 0.9, garden: true });
  houseA.group.position.copy(HOUSE_A);
  houseA.group.rotation.y = 0.5;
  houseA.group.add(contactShadow(1.5, 1.4, 0.5));
  kit.scene.add(track(houseA.group));
  const postA = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1, 10), paper(PAPER.charcoal));
  postA.castShadow = true;
  kit.scene.add(track(postA));
  const tagA = priceTag({ width: 0.55, text: '↑' });
  kit.scene.add(track(tagA.group));
  const POST_A = new THREE.Vector3(2.45, 0, -0.65);   // at the garden's front right corner, clear of the roof
  // arrows, not a currency: this is the general idea on the model table, before the New Zealand street
  const tagTextA = [{ t: -1e9, text: '↑' }, { t: T.cant, text: '↑↑' }, { t: T.of, text: '↑↑↑' }];

  // C: the review on a reviewer's desk (its own place: the town and works are hidden then)
  const R = new THREE.Vector3(0.35, 0, 7.6); // centre of the bottom edge of the report (nearest the camera)
  const desk = await loadModel('/assets/models/inflation-chapter-2/desk.glb');
  desk.position.set(R.x, 0, R.z - 0.85);         // the blotter's middle, under the report's middle
  kit.scene.add(desk);
  const deskLamp = new THREE.PointLight(0xffc27a, 2.2, 4.5, 2);
  deskLamp.position.copy(markerAt(desk, 'desk_lamp')).add(desk.position);
  kit.scene.add(deskLamp);
  const deskThings = [desk, deskLamp];
  const report = await kit.card(['INDEPENDENT REVIEW', 'OF THE', 'RESERVE BANK', '', '', '', '', '', ''],
    { size: 0.1, at: [R.x, 0.026, R.z], look: { aspect: 1.25, cardColour: '#ece4cf', inkColour: '#1f2a33' } });
  own.push(report.anchor);
  const stampLook = (ink) => ({ cardColour: 'rgba(0,0,0,0)', inkColour: ink, borderColour: ink, padX: 0.4, padY: 0.38 });
  const markRight = await kit.card(['RIGHT AT FIRST'], { size: 0.085, thickness: 0, at: [R.x - 0.02, 0.034, R.z - 0.66], yaw: 0.07, look: stampLook('#2b6f69') });
  const markLong = await kit.card(['TOO STRONG,', 'FOR TOO LONG'], { size: 0.095, thickness: 0, at: [R.x + 0.03, 0.036, R.z - 0.22], yaw: -0.12, look: stampLook('#b8321f') });
  const stamp = await kit.cutout('rubber-stamp', { at: [R.x, 0.04, R.z - 0.6], width: 0.5 });
  own.push(markRight.anchor, markLong.anchor, stamp.anchor);
  const stampHits = [
    { at: T.right + 0.02, z: R.z - 0.76, x: R.x - 0.02, mark: markRight },
    { at: T.strong - 0.05, z: R.z - 0.36, x: R.x + 0.03, mark: markLong },
  ];
  const reportLands = T.review + 0.05;

  // ------------------------------------------------------------------ B: the New Zealand street
  const street = await kit.relief('410-bg-nz-suburb', { near: 5, far: 70, fov: 40 });
  const streetThings = [street.mesh];
  const floor = street.pointAt(0.52, 0.3);
  const HOUSE_B = new THREE.Vector3(floor.x - 0.35, floor.y, floor.z);
  const houseB = paperHouse({ width: 1.45, depth: 1.15, height: 0.68, glow: 1.2, garden: true });
  const HOUSE_B_TURN = 0.6;    // turned so its side, roof and verandah show, like the painted villas
  const postB = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 1, 10), paper(PAPER.charcoal));
  postB.castShadow = true;
  const tagB = priceTag({ width: 0.62, text: '$' });   // New Zealand: dollars
  const groundShadow = contactShadow(2.6, 2.4, 0.55);
  groundShadow.position.set(HOUSE_B.x, HOUSE_B.y + 0.02, HOUSE_B.z);
  kit.scene.add(houseB.group, postB, tagB.group, groundShadow);
  streetThings.push(houseB.group, postB, tagB.group, groundShadow);
  const streetMotes = new Motes(kit.scene, { count: 120, min: [-1.6, -1.6, -10], max: [1.6, 1.2, -3], size: 0.02, seed: 31, opacity: 0.5 });
  streetThings.push(streetMotes.points);
  // the tag says only "dearer" ($ to $$$, New Zealand dollars); the figure itself is the +30% word hook, not repeated in 3D
  const tagTextB = [{ t: -1e9, text: '$' }, { t: T.rose, text: '$$' }, { t: T.thirty, text: '$$$' }];

  // ------------------------------------------------------------------ cameras
  // round 20: still unless a move lands a point, at most 3 moves per shot (one each here)
  const houseFocus = [HOUSE_B.x, HOUSE_B.y + 0.5, HOUSE_B.z];
  // A: held on works B, its board readable; zooms out to make room as the house pops up
  const shotA = kit.stillShot({ position: [4.3, 1.25, 1.9], target: [2.2, 0.95, -3.0], fov: 40, focus: [b.boardAt.x, b.boardAt.y, b.boardAt.z] }, [
    { from: T.spent - 0.2, to: T.spent + 0.3, kind: 'focus', focus: [b.yard.x + 0.2, 0.1, b.yard.z - 0.3] },
    { from: T.flat - 0.3, to: T.flat + 0.1, kind: 'focus', focus: [b.boardAt.x, b.boardAt.y, b.boardAt.z] },
    { from: T.things - 0.25, to: T.things + 0.8, kind: 'zoom out', position: [2.5, 1.4, 3.6], target: [2.05, 0.8, -1.9], fov: 44, focus: [HOUSE_A.x, 0.4, HOUSE_A.z] },
  ], { name: 'works B' });
  // B: the New Zealand street, from where it was painted; moves down to the house as prices rise
  const shotB = kit.stillShot({ position: [0, 0.1, 0.2], target: [0, -0.4, -30], fov: 40, focus: 14 }, [
    { from: T.house - 0.45, to: T.house + 0.6, kind: 'move down', position: [0.06, -0.4, -1.5], target: [0.05, -1.75, -30], focus: houseFocus },
  ], { name: 'New Zealand street' });
  // C: the whole desk around the report; zooms in on the report as the review gives its verdict
  const cardMid = [R.x, 0.03, R.z - 0.85];
  const shotC = kit.stillShot({ position: [0.35, 4.9, 10.0], target: [0.35, 0.0, 6.6], fov: 44, focus: cardMid }, [
    { from: T.says - 0.2, to: T.says + 0.9, kind: 'zoom in', position: [0.35, 4.4, 9.4], target: [0.35, 0.0, 6.75], fov: 40 },
  ], { name: 'the review desk' });
  kit.shake(reportLands, 0.012, 0.15);
  for (const hit of stampHits) kit.shake(hit.at, 0.02, 0.14);

  function pose(t) {
    const phase = phaseOf(t);
    const onTable = phase !== 'B';
    // A: the works and town; B: the New Zealand street; C: the desk (with the report and stamp)
    for (const o of [...tableThings, ...own]) o.visible = phase === 'A';
    for (const o of [report.anchor, markRight.anchor, markLong.anchor, stamp.anchor]) o.visible = phase === 'C';
    for (const o of deskThings) o.visible = phase === 'C';
    for (const o of streetThings) o.visible = phase === 'B';
    for (const f of [a.factory, b.factory]) if (f.doorLight) f.doorLight.visible = phase === 'A';

    // the light: the set's lamp on the table; a low sun from the left in the street
    if (onTable) {
      const toCard = phase === 'C' ? new THREE.Vector3(0.35, 0, 6.75).sub(setLight.keyTarget) : new THREE.Vector3();
      key.position.copy(setLight.keyPos).add(toCard); key.target.position.copy(setLight.keyTarget).add(toCard);
      key.intensity = setLight.key; fill.intensity = setLight.fill;
      if (kit.scene.fog) kit.scene.fog.density = setLight.fog;
      kit.scene.environmentIntensity = 1;
    } else {
      key.position.set(HOUSE_B.x - 9, HOUSE_B.y + 5.5, HOUSE_B.z - 3); key.target.position.copy(HOUSE_B);
      key.intensity = Math.PI * 0.75; fill.intensity = Math.PI * 0.2;
      if (kit.scene.fog) kit.scene.fog.density = 0.003;
      kit.scene.environmentIntensity = 0.3;
    }
    key.target.updateMatrixWorld();

    if (phase === 'A') set.townSmoke(t); else set.hideTownSmoke();
    if (onTable) {
      a.factory.setRunning(1);
      b.factory.setRunning(1);
      a.smoke.set({ t, origin: a.chimney.toArray(), scale: 0.9 });
      b.smoke.set({ t, origin: b.chimney.toArray(), scale: 0.9 });
      a.board.pose(t, priceA);
      b.board.pose(t, priceB);
      a.shells.forEach((s, i) => { s.group.visible = i < set.shellsA; s.group.position.copy(a.shellAt(i)); });
      b.shells.forEach((s, i) => { s.group.visible = i < set.shellsB; s.group.position.copy(b.shellAt(i)); });
      coinsB.pose(t);
      dust.set({ origin: [b.yard.x + 0.2, 0.02, b.yard.z - 0.3], width: 1.0, age: t - T.spent - 0.6, scale: 0.3 });
      set.motes.set(t);

      // the house pops up on "things", and its tag climbs the post
      const up = t < T.things - 0.1 ? 0 : 1 - spring(t - (T.things - 0.1), { stiffness: 14, damping: 0.6 });
      houseA.group.visible = up > 0.001;
      houseA.group.scale.set(1, Math.max(0.001, up), 1);
      const climb = tagTextA.filter((s) => t >= s.t).length - 1; // 0, 1, 2
      const tagLift = 0.55 + 0.17 * climb - 0.17 * Math.max(0, climb) * spring(t - tagTextA[climb].t, { stiffness: 18, damping: 0.55 }) * (climb > 0 ? 1 : 0);
      const postHeight = 1.25;
      postA.visible = tagA.group.visible = up > 0.001;
      postA.scale.y = postHeight * Math.max(0.001, up);
      postA.position.set(POST_A.x, postHeight * up / 2, POST_A.z);
      tagA.setText(tagTextA[climb].text);
      tagA.group.position.set(POST_A.x + 0.03, tagLift * up, POST_A.z + 0.03);
      tagA.group.rotation.set(0, -0.35, 0.05 * Math.sin(t * 2.1));

      // C: the report drops and lies flat; the stamp comes down twice
      if (t < reportLands - 0.4) report.set({ visible: false });
      else {
        const k = clamp01((t - (reportLands - 0.4)) / 0.4);
        const settle = t > reportLands ? 0.035 * Math.exp(-(t - reportLands) / 0.08) * Math.abs(Math.sin((t - reportLands) * 40)) : 0;
        report.set({ fold: -Math.PI / 2 + 0.35 * (1 - k), dy: 1.4 * (1 - k * k) + settle, yaw: 0.05 * (1 - k) });
      }
      let stampPose = { visible: false };
      for (const hit of stampHits) {
        const age = t - hit.at;
        if (age > -0.4 && age < 0.65) {
          const dyDown = age < 0 ? 1.6 * (age / -0.4) ** 2 : 0;
          const dyUp = age > 0.22 ? 2.2 * smooth((age - 0.22) / 0.43) : 0;
          const squash = age >= 0 && age < 0.22 ? 0.025 * Math.exp(-age / 0.05) : 0;
          stampPose = { visible: true, dx: hit.x - R.x, dz: hit.z - (R.z - 0.6), dy: dyDown + dyUp - squash };
        }
        const shown = t >= hit.at;
        const pop = shown ? 1 + 0.12 * Math.exp(-(t - hit.at) / 0.07) : 1;
        hit.mark.set(shown ? { fold: -Math.PI / 2, scale: pop } : { visible: false });
      }
      stamp.set(stampPose);
    } else {
      a.smoke.hide(); b.smoke.hide(); dust.hide();
      for (const o of [...tableThings, ...own]) o.visible = false;
      // B: the house pops up on the pavement; as prices rise its tag climbs the post
      const appear = t < T.house - 0.15 ? 0 : 1 - spring(t - (T.house - 0.15), { stiffness: 13, damping: 0.6 });
      const rise = smooth(ramp(t, T.rose, T.percent + 0.4));
      houseB.group.visible = postB.visible = tagB.group.visible = groundShadow.visible = appear > 0.001;
      houseB.group.position.set(HOUSE_B.x, HOUSE_B.y, HOUSE_B.z);
      houseB.group.rotation.y = HOUSE_B_TURN;
      houseB.group.scale.set(1, Math.max(0.001, appear), 1);
      const postX = HOUSE_B.x + 0.9, postZ = HOUSE_B.z + 1.05, postHeight = 1.7;
      postB.scale.y = postHeight * Math.max(0.001, appear);
      postB.position.set(postX, HOUSE_B.y + postHeight * appear / 2, postZ);
      let current = 0;
      while (current + 1 < tagTextB.length && tagTextB[current + 1].t <= t) current++;
      tagB.setText(tagTextB[current].text);
      const bump = current > 0 ? 0.06 * Math.exp(-(t - tagTextB[current].t) / 0.12) : 0;
      tagB.group.position.set(postX + 0.03, HOUSE_B.y + (0.45 + 0.95 * rise + bump) * appear, postZ + 0.03);
      tagB.group.rotation.set(0, -0.1, 0.05 * Math.sin(t * 2.3));
      streetMotes.set(t);
    }

    // the dips at the two cuts
    const fade = Math.max(0, 1 - Math.abs(t - CUT_B) / DIP, 1 - Math.abs(t - CUT_C) / DIP);
    const camera = phase === 'A' ? shotA(t) : phase === 'B' ? shotB(t) : shotC(t);
    const look = phase === 'B'
      ? { aperture: 8, maxBlur: 14, exposure: 0.95, glowThreshold: 0.93, glowStrength: 0.6, contrast: 1.05, fade }
      : { aperture: 9, maxBlur: 16, exposure: 0.93, glowThreshold: 0.95, glowStrength: 0.7, contrast: 1.08, fade };
    return { camera, look };
  }

  function draw2D(ctx, t) {
    const at = (p) => kit.toScreen(p);
    const phase = phaseOf(t);
    // a soft dark band at the top, so the words read over the busy set (chimneys; the desk's papers)
    if (phase !== 'B') {
      const band = ctx.createLinearGradient(0, 0, 0, 760);
      const strength = phase === 'C' ? 0.62 : 0.5;
      band.addColorStop(0, `rgba(10,14,16,${strength})`); band.addColorStop(0.65, `rgba(10,14,16,${strength * 0.55})`); band.addColorStop(1, 'rgba(10,14,16,0)');
      ctx.save(); ctx.fillStyle = band; ctx.fillRect(0, 0, 1080, 760); ctx.restore();
    }
    if (phase === 'A') {
      hook(ctx, t, { at: T.yes, until: T.spent - 0.1, lines: ['YES,', 'IT CAN'], y: 340, size: 104 });
      callout(ctx, t, { at: T.flat, until: T.things + 0.2, point: at([FACTORY_B.x + 0.2, 1.1, FACTORY_B.z + 1.0]), text: 'FLAT OUT', dx: -120, dy: -330, size: 52, plate: true, margin: 140 });   // a spot on the front wall that stays in frame
      callout(ctx, t, { at: T.flat + 0.35, until: T.things + 0.2, point: at(b.boardAt.clone().setY(1.27)), text: 'PRICES UP', dx: -140, dy: -220, accent: INK.red, size: 52, plate: true, margin: 140 });  // points at the board's top rim, not through the digits
      hook(ctx, t, { at: T.things, until: CUT_B - 0.05, lines: ["CAN'T MAKE MORE", 'IN A HURRY'], y: 320, size: 70 });
    } else if (phase === 'B') {
      // a soft dark band at the top, so the words read over the bright painting
      const band = ctx.createLinearGradient(0, 0, 0, 900);
      band.addColorStop(0, 'rgba(10,14,16,0.6)'); band.addColorStop(0.6, 'rgba(10,14,16,0.35)'); band.addColorStop(1, 'rgba(10,14,16,0)');
      ctx.save(); ctx.fillStyle = band; ctx.fillRect(0, 0, 1080, 900); ctx.restore();
      placeTitle(ctx, t, { at: T.twenty, until: T.house - 0.2, place: 'New Zealand', year: 2021, y: 260 });
      hook(ctx, t, { at: T.unemployment, until: T.house - 0.2, text: 'UNEMPLOYMENT', y: 470, size: 56, colour: INK.muted });
      counter(ctx, t, { at: T.lowest - 0.05, until: T.house - 0.2, duration: 0.01, from: 3.2, to: 3.2, format: (v) => `${v.toFixed(1)}%`, y: 700, size: 190, caption: 'Lowest on record', captionColour: INK.paper });
      // so the caption isn't misread: 1986 is when the survey began (C2-N09)
      const note = presence(t, T.lowest + 0.25, T.house - 0.2, 0.3, 0.35);
      if (note > 0) {
        ctx.save(); ctx.globalAlpha = note;
        ctx.font = '600 30px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        const w = ctx.measureText('Records began in 1986').width + 40;
        ctx.fillStyle = 'rgba(12,16,18,0.55)'; ctx.beginPath(); ctx.roundRect(540 - w / 2, 815, w, 50, 12); ctx.fill();
        ctx.fillStyle = INK.paper; ctx.globalAlpha = note * 0.85;
        ctx.fillText('Records began in 1986', 540, 841);
        ctx.restore();
      }
      hook(ctx, t, { at: T.house, until: CUT_C - 0.05, text: 'HOUSE PRICES', y: 260, size: 58, colour: INK.muted });
      hook(ctx, t, { at: T.thirty, until: CUT_C - 0.05, text: '+30%', y: 390, size: 150, colour: INK.amber });
      hook(ctx, t, { at: T.twelve, until: CUT_C - 0.05, text: 'IN 12 MONTHS', y: 520, size: 70 });
      credit(ctx, t, { at: T.unemployment, until: T.house - 0.2, text: 'Source: Stats NZ', y: 1460 });
      credit(ctx, t, { at: T.house, until: CUT_C - 0.05, text: 'Source: REINZ', y: 1460 });
    } else {
      credit(ctx, t, { at: T.review + 0.3, until: T.end + 2, text: 'Independent review, September 2026', y: 1460 });
      hook(ctx, t, { at: T.support, until: T.was - 0.05, lines: ['SUPPORT FROM', 'BANK + GOVERNMENT'], y: 330, size: 66 });
      hook(ctx, t, { at: T.right - 0.15, until: T.end + 2, text: 'THE REVIEW:', y: 230, size: 48, colour: INK.muted });
      hook(ctx, t, { at: T.right, until: T.too - 0.1, text: 'RIGHT AT FIRST', y: 340, size: 84, colour: INK.teal });
      hook(ctx, t, { at: T.too, until: T.end + 2, lines: ['TOO STRONG,', 'FOR TOO LONG'], y: 380, size: 92, colour: INK.red });
    }
    return true;
  }

  return { pose, draw2D };
}
