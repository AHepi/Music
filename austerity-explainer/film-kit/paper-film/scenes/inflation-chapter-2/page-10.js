// What this does: page 10 of chapter 2, the last page of the film. Two places:
//   A. A New Zealand street at dusk (the suburb painting, its light sinking warmer and lower as the
//      page goes on). A card interest-rate dial stands on a post at the kerb.
//      - "the Reserve Bank, pushed its interest rate from a quarter of a percent to five and a half
//        percent by twenty twenty-three": the needle swings from 0.25 to 5.5; the figure counts up;
//        a small 2023 under it.
//      - "unemployment has climbed from three point two percent to five point six": a figure counts
//        3.2% to 5.6% over a panel of a hundred dots, 3 then 6 of them empty (as on page 2).
//      - "this year, the Reserve Bank is raising its interest rate again": back to the dial, which
//        ticks up again (2.25% to 2.75%, 2026); RISING AGAIN.
//   B. A quick dip to black on "So", into the debating chamber. An invented politician at a lectern
//      mouths "new money causes inflation". The camera pushes in and the two questions land:
//      SPENT ON WHAT? and WHO PAYS TO STOP IT? They hold, then the whole picture fades to black.
// Narration words used are listed in T below; every time comes from Malina's recording.

import { THREE, popUp, clamp01, smooth, smoother, ramp, lerp, spring } from '../cinema-kit.js';
import { dial, PAPER, paper } from '../models.js';
import { Motes } from '../effects.js';
import { placeTitle, hook, counter, credit, presence, INK } from '../graphics.js';

const FACE_TURN = Math.PI / 2;

export async function build(kit) {
  const T = {
    start: kit.firstWordAt - 0.8,
    here: kit.at('here'),
    pushed: kit.at('pushed'),
    interest: kit.at('interest'),
    from: kit.at('from'),
    quarter: kit.at('quarter'),
    to: kit.at('to'),
    five: kit.at('five'),
    half: kit.at('half'),
    by: kit.at('by'),
    bring: kit.at('bring'),
    since: kit.at('since'),
    unemployment: kit.at('unemployment'),
    climbed: kit.at('climbed'),
    three: kit.at('three'),
    to2: kit.at('to', 3),
    five2: kit.at('five', 2),
    six: kit.at('six'),
    sixEnd: kit.end('six'),
    and: kit.at('and', 2),
    thisYear: kit.at('this'),
    raising: kit.at('raising'),
    again: kit.at('again'),
    so: kit.at('so'),
    someone: kit.at('someone'),
    newMoney: kit.at('new'),
    inflationEnd: kit.end('inflation'),
    ask: kit.at('ask'),
    spent: kit.at('spent'),
    who: kit.at('who'),
    last: kit.lastWordEnd,
  };
  T.cut = T.so - 0.02; // the switch, hidden at the bottom of the dip
  T.fadeEnd = 270.2; // the film ends at 270.33; black by here
  T.fadeStart = T.fadeEnd - 2.0;

  kit.lightRig({ keyColour: 0xffc68e, keyShare: 0.7, keyFrom: [7, 5, 2], keyTarget: [-1, -2, -9], fillSky: 0x8b9cb0, fillGround: 0x3a2c22,
    fillShare: 0.2, haze: 0x2a2a30, hazeDensity: 0.003, shadowBox: 9, shadowSoftness: 5, background: 0x14161a, reflections: 0.3 });

  // ------------------------------------------------------------------ A: the street at dusk
  const street = await kit.relief('410-bg-nz-suburb', { near: 6, far: 70, fov: 40 });
  const streetMaterial = street.mesh.material;
  const daylight = new THREE.Color(0xffffff), dusk = new THREE.Color(0xe2ae90);

  // the interest-rate dial on a post at the kerb, right of frame
  const dialFoot = street.pointAt(0.69, 0.27);   // a little left, clear of the right-hand phone buttons
  const rate = dial({ radius: 0.62, min: 0, max: 6, step: 1, label: 'INTEREST', unit: '%' });
  const dialCentre = new THREE.Vector3(dialFoot.x, dialFoot.y + 1.6, dialFoot.z);
  rate.group.position.copy(dialCentre);
  rate.group.rotation.y = -0.12;
  // models.js draws the dial's face turned a quarter turn (its numbers read sideways); turn the
  // face back here so the numbers stand upright and the needle still matches them
  rate.group.children[0].rotation.y = FACE_TURN;
  kit.scene.add(rate.group);
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 1.6, 16), paper(0x6a6f70));
  // behind the dial's face; its foot sits just on the kerb (the painted ground rises steeply behind
  // the foot point, so it is lifted a hair to stay clear of it)
  post.position.set(dialFoot.x, dialFoot.y + 0.8 + 0.055, dialFoot.z - 0.06);
  post.castShadow = true;
  kit.scene.add(post);

  const motes = new Motes(kit.scene, { count: 140, min: [-2.2, -2.2, -12], max: [2.2, 2.0, -4], size: 0.028, seed: 10, opacity: 0.45 });

  // -------------------------------------------------------------------- B: the chamber
  const chamber = await kit.relief('101-bg-parliament', { near: 6, far: 70, fov: 40 });
  // the politician stands exactly where he stood on page 1 (the film ends where it began), his foot
  // on the painted floor
  const manFloor = chamber.pointAt(0.47, 0.14);
  const politician = await kit.speaker('politician', { at: [manFloor.x, manFloor.y + 0.01, manFloor.z], width: 2.0 });
  const faceAt = new THREE.Vector3(manFloor.x, manFloor.y + 2.0, manFloor.z);

  // ------------------------------------------------------------------------- the cameras
  // The camera rule: each shot holds still and moves only to land a point (at most 3 moves a shot).
  // Street shot: the street with the dial at the kerb; zoom in on the dial as she names the interest
  // rate; zoom out on "since" to make room for the hundred dots; zoom in on the dial again on "this
  // year ... raising".
  const dialPoint = [dialCentre.x, dialCentre.y, dialCentre.z];
  // the opening: closer and lower than the wide framing, the dial big at the kerb (the street's road
  // no longer an empty band across the bottom)
  const STREET_OPEN = { position: [0.3, -0.35, -1.3], target: [1.15, 1.6, -30], fov: 29, focus: dialPoint };
  // the wide framing that makes room for the hundred dots (the dial kept clear of the right-hand buttons)
  const STREET_WIDE = { position: [0.15, -0.2, -0.6], target: [0.4, 1.8, -30], fov: 34 };
  const STREET_DIAL = { position: [0.35, -0.05, -2.0], target: [1.95, 0.95, -30], fov: 26.5 };
  const streetShot = kit.stillShot(STREET_OPEN, [
    { from: T.pushed - 0.3, to: T.pushed + 0.9, kind: 'zoom in', ...STREET_DIAL },
    { from: T.since - 0.35, to: T.since + 0.75, kind: 'zoom out', position: STREET_WIDE.position, target: STREET_WIDE.target, fov: STREET_WIDE.fov },
    { from: T.thisYear - 0.15, to: T.thisYear + 1.0, kind: 'zoom in', ...STREET_DIAL },
  ], { name: 'the street and the dial' });
  // Chamber shot: page 1's picture again. It holds on the politician while he says it; one short zoom
  // in on "ask them", onto him (to page 1's close framing), as the two questions land; then still.
  const faceFocus = [faceAt.x, faceAt.y, faceAt.z];
  const chamberShot = kit.stillShot({ position: [0, 0.1, -0.3], target: [0, -0.35, -30], fov: 35, focus: faceFocus }, [
    { from: T.ask - 0.1, to: T.ask + 1.0, kind: 'zoom in', position: [0, 0.05, -0.8], target: [-0.05, -0.1, -30], fov: 30 },
  ], { name: 'the chamber and the question' });

  // the needle: 0.25 at the start, swings to 5.5 on "five and a half" (capped: it never passes the
  // 5.5 she says) and holds there through the unemployment beat; it only resets to the 2026 level
  // on "this year", then ticks up twice on "raising ... again"
  function rateAt(t) {
    let v = 0.25;
    if (t > T.to) v = Math.min(5.5, lerp(0.25, 5.5, 1 - spring((t - T.to) * 0.9, { stiffness: 9, damping: 0.6 })));
    // the jump back to 2.25 (the cuts of 2024-25, not narrated) happens inside a quick pop of the dial on
    // "this year", while it is small, so the needle is never seen falling while she says "raising"
    const ease = smoother(ramp(t, T.thisYear + 0.05, T.thisYear + 0.3));
    v = lerp(v, 2.25, ease);
    v += 0.25 * smooth(ramp(t, T.raising, T.raising + 0.35)) + 0.25 * smooth(ramp(t, T.again - 0.25, T.again + 0.1));
    return v;
  }

  function pose(t) {
    const inStreet = t < T.cut;
    street.mesh.visible = inStreet;
    rate.group.visible = post.visible = inStreet;
    chamber.mesh.visible = !inStreet;

    // dusk: the painting's own light warms and lowers as the page goes on
    const k = smooth(ramp(t, T.start, T.cut));
    streetMaterial.emissive.copy(daylight).lerp(dusk, 0.25 + 0.5 * k);

    rate.setValue(rateAt(t));
    const pop = Math.sin(Math.PI * clamp01((t - (T.thisYear - 0.05)) / 0.45));
    rate.group.scale.setScalar(1 - 0.85 * pop);
    // small knock of the dial as the needle hits 5.5
    const knockAge = t - (T.half + 0.1);
    rate.group.rotation.z = knockAge > 0 && knockAge < 1.2 ? 0.02 * Math.exp(-knockAge * 5) * Math.sin(knockAge * 30) : 0;

    if (inStreet) {
      motes.set(t, { visible: true });
      politician.set({ visible: false });
    } else {
      motes.set(t, { visible: false });
      politician.set({}, kit.mouthOpen(t, T.newMoney - 0.02, T.inflationEnd + 0.05));
    }

    // the dip at the cut, and the final fade to black
    const dip = 1 - clamp01(Math.abs(t - T.cut) / 0.24);
    const end = smooth(ramp(t, T.fadeStart, T.fadeEnd));
    const fade = Math.max(smooth(dip), end);

    const look = inStreet
      ? { aperture: 8, maxBlur: 14, exposure: lerp(0.93, 0.84, k), glowThreshold: 0.92, glowStrength: 0.7, contrast: 1.08, saturation: 1.05,
        highlightTint: [0.62, 0.48, 0.36], shadowTint: [0.42, 0.46, 0.56], tintAmount: 0.38, vignette: 0.42, fade }
      : { aperture: 7, maxBlur: 14, exposure: 0.92, glowThreshold: 0.94, glowStrength: 0.6, contrast: 1.08, vignette: lerp(0.38, 0.55, smooth(ramp(t, T.spent, T.who + 1))), fade };
    return { camera: inStreet ? streetShot(t) : chamberShot(t), look };
  }

  // a figure that just shows a value (the value comes from the needle or a ramp), with a caption
  // quarter steps for the interest rate (0.25, 0.5 ... 5.5), one decimal for unemployment
  const quarters = (v) => `${(Math.round(v * 4) / 4).toFixed(2).replace(/0$/, '').replace(/\.0$/, '')}%`;
  const tenths = (v) => `${v.toFixed(1)}%`;
  function figure(ctx, t, { at, until, value, caption, y, size = 150, colour = INK.paper, format = quarters }) {
    counter(ctx, t, { at, until, from: value, to: value, format, x: 540, y, size, colour, caption, captionColour: INK.paper });
  }
  // a soft dark wash behind the words at the top of the street shots (the dusk sky is bright)
  function topWash(ctx, a) {
    if (a <= 0) return;
    const g = ctx.createLinearGradient(0, 0, 0, 900);
    g.addColorStop(0, `rgba(10,12,16,${0.55 * a})`); g.addColorStop(0.6, `rgba(10,12,16,${0.3 * a})`); g.addColorStop(1, 'rgba(10,12,16,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 900);
  }

  // a hundred dots, one per hundred workers: the ones out of work (rounded) are filled solid red. A small
  // key on its own dark plate beside them says what a dot and a red dot mean.
  function hundredDots(ctx, t, { at, until, x, y, gap = 40, radius = 15, empty }) {
    const a = presence(t, at, until, 0.3, 0.35);
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(12,16,18,0.62)';
    ctx.beginPath(); ctx.roundRect(x - 36, y - 36, gap * 9 + 72, gap * 9 + 72, 22); ctx.fill();
    for (let i = 0; i < 100; i++) {
      const cx = x + (i % 10) * gap, cy = y + Math.floor(i / 10) * gap;
      const k = clamp01((t - at - 0.1 - i * 0.01) / 0.25);
      if (k <= 0) continue;
      ctx.beginPath(); ctx.arc(cx, cy, radius * k, 0, Math.PI * 2);
      ctx.fillStyle = 99 - i < empty ? INK.red : INK.amber;
      ctx.fill();
    }
    ctx.restore();
  }
  function dotsKey(ctx, t, { at, until, x, y }) {
    const a = presence(t, at, until, 0.3, 0.35);
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(12,16,18,0.62)';
    ctx.beginPath(); ctx.roundRect(x, y, 400, 262, 22); ctx.fill();
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    const row = (cy, colour, label) => {
      ctx.fillStyle = colour; ctx.beginPath(); ctx.arc(x + 46, cy, 16, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = INK.paper; ctx.font = '800 36px Inter'; ctx.fillText(label, x + 80, cy + 2);
    };
    row(y + 50, INK.red, 'OUT OF WORK');
    row(y + 106, INK.amber, 'IN WORK');
    ctx.fillStyle = INK.paper; ctx.font = '700 31px Inter';
    ctx.fillText('EACH DOT =', x + 30, y + 168);
    ctx.fillText('1 IN 100 WORKERS', x + 30, y + 210);
    ctx.restore();
  }

  function draw2D(ctx, t) {
    // ---- A
    topWash(ctx, presence(t, T.start, T.cut, 0.3, 0.1));
    placeTitle(ctx, t, { at: T.here, until: T.since - 0.2, place: 'New Zealand', x: 84, y: 250 });
    const shownRate = t < T.to ? 0.25 : Math.min(5.5, Math.max(0.25, rateAt(t)));
    figure(ctx, t, { at: T.from, until: T.since - 0.2, value: Math.round(shownRate * 100) / 100, caption: 'Interest rate', y: 500 });
    hook(ctx, t, { at: T.by, until: T.since - 0.2, text: '2023', y: 625, size: 54, colour: INK.paper });
    hook(ctx, t, { at: T.bring, until: T.since - 0.2, text: 'TO BRING PRICES DOWN', y: 700, size: 48, colour: INK.paper });

    // the count lands on 5.6 as she says "five", then holds still until "this year"
    const jobless = lerp(3.2, 5.6, smooth(ramp(t, T.to2 - 0.1, T.five2 + 0.25)));
    const joblessUntil = T.thisYear + 0.2;
    hook(ctx, t, { at: T.since, until: T.thisYear - 0.05, text: 'SINCE THE END OF 2021', y: 260, size: 44, colour: INK.paper });
    figure(ctx, t, { at: T.three, until: joblessUntil, value: jobless, caption: 'Unemployment', y: 470, format: tenths });
    hundredDots(ctx, t, { at: T.unemployment, until: joblessUntil, x: 100, y: 650, empty: Math.round(jobless) });
    dotsKey(ctx, t, { at: T.unemployment + 0.4, until: joblessUntil, x: 520, y: 614 });
    credit(ctx, t, { at: T.from, until: T.cut - 0.15, text: 'Stats NZ; Reserve Bank of New Zealand', y: 1505, plate: true });

    const later = 2.25 + 0.25 * smooth(ramp(t, T.raising, T.raising + 0.35)) + 0.25 * smooth(ramp(t, T.again - 0.25, T.again + 0.1));
    hook(ctx, t, { at: T.thisYear, until: T.cut - 0.15, text: '2026', y: 260, size: 54, colour: INK.paper });
    hook(ctx, t, { at: T.raising, until: T.cut - 0.15, text: 'RISING AGAIN', y: 360, size: 96 });
    figure(ctx, t, { at: T.raising, until: T.cut - 0.15, value: later, caption: 'Interest rate', y: 540, size: 110, colour: INK.amber });

    // ---- B
    if (t >= T.cut) {
      // what 'someone' says, as an upright hook
      hook(ctx, t, { at: T.newMoney, until: T.ask - 0.1, lines: ['“New money causes', 'inflation.”'], y: 330, size: 72 });
      hook(ctx, t, { at: T.spent, until: T.fadeEnd + 1, text: 'SPENT ON WHAT?', y: 290, size: 88 });
      hook(ctx, t, { at: T.who, until: T.fadeEnd + 1, lines: ['WHO PAYS', 'TO STOP IT?'], y: 440, size: 88, colour: INK.amber });
    }
    // the overlay fades with the picture at the end
    return true;
  }

  return { pose, draw2D, join: { kind: 'dip', after: 99, length: 1 } };
}
