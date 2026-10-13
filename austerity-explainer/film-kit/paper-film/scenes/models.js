// What this does: card and paper models built from shapes, not painted: they are real 3D objects,
// lit by the page's lamp, casting real shadows, seen from any side as the camera moves. Most are
// made of ivory card, like an architect's model, with a few colours where they mean something
// (brass shells, gold coins, a red price tag). Each function returns an object with `group` (put it
// in the world: kit.scene.add(model.group)) and the parts or settings a page moves.
//
// The models: paperGround, paperFactory, paperHouse, shell, coin, banknoteBundle, priceTag,
// splitFlap (a counter whose digits flip over), dial (a meter with a needle), oilBarrel, paperBoat,
// barColumns (a chart whose bars rise), threadChart (a chart drawn as a red thread between pins).

import { THREE, canvasTexture } from '../stage/cinema-stage.js';
import { loadFonts, seededRandom, clamp01, lerp, smooth } from './cinema-kit.js';

// ------------------------------------------------------------------------------- the papers
let grainTexture = null;
function paperGrain() {
  if (!grainTexture) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 256;
    const ctx = canvas.getContext('2d');
    const image = ctx.createImageData(256, 256), random = seededRandom(41);
    for (let i = 0; i < image.data.length; i += 4) { const v = 225 + (random() - 0.5) * 36; image.data[i] = image.data[i + 1] = image.data[i + 2] = v; image.data[i + 3] = 255; }
    ctx.putImageData(image, 0, 0);
    grainTexture = canvasTexture(canvas);
    grainTexture.wrapS = grainTexture.wrapT = THREE.RepeatWrapping;
    grainTexture.repeat.set(3, 3);
  }
  return grainTexture;
}
export const PAPER = {
  ivory: 0xefe6d2, cream: 0xe6dcc3, card: 0xd8cdb3, charcoal: 0x2d3236, slate: 0x55606a,
  brick: 0x9c4a36, red: 0xb23a2a, teal: 0x2f5d62, ochre: 0xc4913c, ink: 0x20262b,
};
export function paper(colour = PAPER.ivory, { roughness = 0.93, emissive = 0x000000, emissiveIntensity = 0, side = THREE.FrontSide } = {}) {
  return new THREE.MeshStandardMaterial({ color: colour, roughness, metalness: 0, map: paperGrain(), emissive, emissiveIntensity, side, envMapIntensity: 0.25 });
}
export function metal(colour, { roughness = 0.32, metalness = 1 } = {}) {
  return new THREE.MeshStandardMaterial({ color: colour, roughness, metalness, envMapIntensity: 1.1 });
}
const shadowing = (object) => { object.traverse((o) => { if (o.isMesh && !o.userData.noShadow) { o.castShadow = true; o.receiveShadow = true; } }); return object; };

// --------------------------------------------------------------------------------- the ground
// A sheet of card lying flat (a table top, a model's base), size x size, centred at `at`.
export function paperGround({ at = [0, 0, 0], width = 30, depth = 30, colour = PAPER.card } = {}) {
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), paper(colour, { roughness: 0.97 }));
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set(...at);
  mesh.receiveShadow = true;
  return { group: mesh };
}

// ----------------------------------------------------------------------------------- factory
// Printed card for the model factory walls: faint brick courses in a slightly darker ink, a little
// grime toward the bottom, like an architect's model printed on card.
const printedCards = new Map();
function printedCard(kind, base) {
  const key = `${kind}|${base}`;
  if (printedCards.has(key)) return printedCards.get(key);
  const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = base; ctx.fillRect(0, 0, 512, 256);
  const random = seededRandom(kind.length * 31 + 7);
  if (kind === 'brick') {
    ctx.strokeStyle = 'rgba(70,50,35,0.22)'; ctx.lineWidth = 1.2;
    for (let row = 0; row < 32; row++) {
      const y = row * 8; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke();
      for (let x = (row % 2) * 12; x < 512; x += 24) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + 8); ctx.stroke(); }
    }
    for (let i = 0; i < 90; i++) { ctx.fillStyle = `rgba(60,40,25,${0.04 + random() * 0.06})`; ctx.fillRect(random() * 512, random() * 256, 12 + random() * 30, 6 + random() * 10); }
    const grime = ctx.createLinearGradient(0, 160, 0, 256); grime.addColorStop(0, 'rgba(40,30,20,0)'); grime.addColorStop(1, 'rgba(40,30,20,0.28)');
    ctx.fillStyle = grime; ctx.fillRect(0, 0, 512, 256);
  } else if (kind === 'roof') {
    ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 2;
    for (let x = 0; x < 512; x += 10) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 256); ctx.stroke(); }
  } else if (kind === 'weatherboard') {
    // painted horizontal boards: a thin shadow line under each lap, a lighter top edge, a little wear
    for (let y = 0; y < 256; y += 16) {
      ctx.fillStyle = 'rgba(70,58,40,0.20)'; ctx.fillRect(0, y + 13, 512, 3);
      ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(0, y, 512, 2);
    }
    for (let i = 0; i < 60; i++) { ctx.fillStyle = `rgba(90,75,55,${0.03 + random() * 0.04})`; ctx.fillRect(random() * 512, random() * 256, 20 + random() * 60, 3 + random() * 6); }
  } else if (kind === 'iron') {
    // corrugated iron: soft light and dark ridges, a few faint rust streaks
    for (let x = 0; x < 512; x += 8) {
      ctx.fillStyle = 'rgba(255,255,255,0.10)'; ctx.fillRect(x, 0, 3, 256);
      ctx.fillStyle = 'rgba(0,0,0,0.22)'; ctx.fillRect(x + 4, 0, 3, 256);
    }
    for (let i = 0; i < 14; i++) { ctx.fillStyle = `rgba(120,60,30,${0.05 + random() * 0.07})`; ctx.fillRect(random() * 512, random() * 128, 3 + random() * 5, 60 + random() * 140); }
  }
  const texture = canvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  printedCards.set(key, texture);
  return texture;
}
// A window: dark glass divided into small panes by a printed frame; it glows warm when lit.
let windowTexture = null;
function windowPanes() {
  if (!windowTexture) {
    const canvas = document.createElement('canvas'); canvas.width = 128; canvas.height = 192;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 128, 192);
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, 128, 10); ctx.fillRect(0, 182, 128, 10); ctx.fillRect(0, 0, 10, 192); ctx.fillRect(118, 0, 10, 192);
    for (let i = 1; i < 3; i++) ctx.fillRect(i * 128 / 3 - 3, 0, 6, 192);
    for (let j = 1; j < 4; j++) ctx.fillRect(0, j * 192 / 4 - 3, 128, 6);
    windowTexture = canvasTexture(canvas, { colour: false });
  }
  return windowTexture;
}
// A villa sash window: a white border, one meeting rail across the middle (one-over-one), dark glass
// that glows warm when lit.
let sashTexture = null;
function sashPanes() {
  if (!sashTexture) {
    const canvas = document.createElement('canvas'); canvas.width = 96; canvas.height = 192;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 96, 192);
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, 96, 9); ctx.fillRect(0, 183, 96, 9); ctx.fillRect(0, 0, 9, 192); ctx.fillRect(87, 0, 9, 192);
    ctx.fillRect(0, 90, 96, 11);
    sashTexture = canvasTexture(canvas, { colour: false });
  }
  return sashTexture;
}
// A card model of a factory: a long brick body with a saw-tooth roof of `bays` teeth, tall paned
// windows along the front (they glow warm when the factory runs), a door, a sign band and a chimney.
// Front faces +z. setRunning(level 0..1) lights the windows; chimneyTop is where smoke comes out.
export function paperFactory({ width = 3.2, depth = 2.0, height = 1.3, bays = 4, colour = '#d6c6a4', roofColour = '#5b636a' } = {}) {
  const group = new THREE.Group();
  const wallTexture = printedCard('brick', colour).clone(); wallTexture.needsUpdate = true; wallTexture.repeat.set(width / 1.6, height / 0.8);
  const wallMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff, map: wallTexture, roughness: 0.92, envMapIntensity: 0.25 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), wallMaterial);
  body.position.y = height / 2;
  group.add(body);
  const toothWidth = width / bays, toothHeight = height * 0.42;
  const shape = new THREE.Shape();
  shape.moveTo(0, 0); shape.lineTo(toothWidth, 0); shape.lineTo(toothWidth, toothHeight); shape.lineTo(0, 0);
  const toothGeometry = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false });
  const roofTexture = printedCard('roof', roofColour);
  const roofMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff, map: roofTexture, roughness: 0.85, envMapIntensity: 0.3 });
  const glassMaterial = new THREE.MeshStandardMaterial({ color: 0x2a3238, roughness: 0.35, metalness: 0.2, emissive: 0xffb45e, emissiveIntensity: 0, emissiveMap: windowPanes(), map: windowPanes() });
  for (let i = 0; i < bays; i++) {
    const tooth = new THREE.Mesh(toothGeometry, roofMaterial);
    tooth.position.set(-width / 2 + i * toothWidth, height, -depth / 2);
    group.add(tooth);
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(depth * 0.94, toothHeight * 0.78), glassMaterial);
    glass.rotation.y = -Math.PI / 2;
    glass.position.set(-width / 2 + (i + 1) * toothWidth + 0.004, height + toothHeight * 0.46, 0);
    group.add(glass);
  }
  const windows = [];
  const windowMaterial = new THREE.MeshStandardMaterial({ color: 0x323b42, roughness: 0.3, metalness: 0.25, map: windowPanes(), emissive: 0xffa94d, emissiveMap: windowPanes(), emissiveIntensity: 0 });
  const sillMaterial = paper(0x8f7f68);
  const columns = Math.max(3, Math.round(width / 0.5));
  for (let i = 0; i < columns; i++) {
    const x = -width / 2 + (i + 0.5) * width / columns;
    if (Math.abs(x) < width * 0.1) continue;
    const w = width / columns * 0.5, h = height * 0.48;
    const pane = new THREE.Mesh(new THREE.PlaneGeometry(w, h), windowMaterial);
    pane.position.set(x, height * 0.5, depth / 2 + 0.004);
    group.add(pane); windows.push(pane);
    const sill = new THREE.Mesh(new THREE.BoxGeometry(w * 1.15, 0.03, 0.05), sillMaterial);
    sill.position.set(x, height * 0.5 - h / 2 - 0.015, depth / 2 + 0.025);
    group.add(sill);
    const lintel = new THREE.Mesh(new THREE.BoxGeometry(w * 1.15, 0.04, 0.03), sillMaterial);
    lintel.position.set(x, height * 0.5 + h / 2 + 0.02, depth / 2 + 0.015);
    group.add(lintel);
  }
  const door = new THREE.Mesh(new THREE.BoxGeometry(width * 0.15, height * 0.6, 0.04), paper(0x2b2420, { roughness: 0.8 }));
  door.position.set(0, height * 0.3, depth / 2 + 0.02);
  group.add(door);
  const doorGlow = new THREE.Mesh(new THREE.PlaneGeometry(width * 0.13, height * 0.57), new THREE.MeshBasicMaterial({ color: 0xffb060, transparent: true, opacity: 0, fog: false }));
  doorGlow.position.set(0, height * 0.29, depth / 2 + 0.045);
  group.add(doorGlow);
  const band = new THREE.Mesh(new THREE.BoxGeometry(width * 0.46, height * 0.1, 0.035), paper(0x3d4246));
  band.position.set(0, height * 0.82, depth / 2 + 0.02);
  group.add(band);
  const chimneyHeight = height * 2.3, chimneyRadius = width * 0.045;
  const chimneyTexture = printedCard('brick', '#9c5a43').clone(); chimneyTexture.needsUpdate = true; chimneyTexture.repeat.set(1, 4);
  const chimney = new THREE.Mesh(new THREE.CylinderGeometry(chimneyRadius * 0.8, chimneyRadius, chimneyHeight, 24), new THREE.MeshStandardMaterial({ map: chimneyTexture, roughness: 0.9 }));
  chimney.position.set(width * 0.36, chimneyHeight / 2, -depth * 0.25);
  group.add(chimney);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(chimneyRadius * 0.85, chimneyRadius * 0.2, 8, 20), paper(PAPER.charcoal));
  rim.rotation.x = Math.PI / 2; rim.position.set(width * 0.36, chimneyHeight, -depth * 0.25);
  group.add(rim);
  // a soft dark patch on the table under the model, so it sits on the table rather than floats
  group.add(contactShadow(width * 1.25, depth * 1.4, 0.55));
  shadowing(group);
  for (const w of windows) w.castShadow = false;
  doorGlow.castShadow = false;
  return {
    group, windows, door, width, depth, height,
    chimneyTop: new THREE.Vector3(width * 0.36, chimneyHeight + 0.05, -depth * 0.25),
    doorAt: new THREE.Vector3(0, 0, depth / 2 + 0.05),
    setRunning(level) {
      windowMaterial.emissiveIntensity = 2.2 * level;
      glassMaterial.emissiveIntensity = 1.4 * level;
      doorGlow.material.opacity = 0.42 * level;
    },
  };
}

// A soft shadow patch lying on the ground (contact shadow), width x depth, darkness 0..1.
let contactTexture = null;
export function contactShadow(width, depth, darkness = 0.5) {
  if (!contactTexture) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(64, 64, 10, 64, 64, 64);
    g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(0.6, 'rgba(0,0,0,0.6)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
    contactTexture = canvasTexture(canvas, { colour: false });
  }
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), new THREE.MeshBasicMaterial({ map: contactTexture, transparent: true, opacity: darkness, depthWrite: false, color: 0x000000 }));
  mesh.rotation.x = -Math.PI / 2; mesh.position.y = 0.004;
  mesh.renderOrder = 1;
  mesh.userData.noShadow = true;
  return mesh;
}

// ------------------------------------------------------------------------------------- house
// A card model of a New Zealand villa: a box with a gabled roof, a front bay and a verandah.
export function paperHouse({ width = 1.6, depth = 1.6, height = 0.8, colour = PAPER.ivory, roofColour = PAPER.slate, glow = 0, garden = false } = {}) {
  // A card model of a small New Zealand villa (front faces +z): painted weatherboards over a painted
  // skirting with vents, white corner boards, a hipped corrugated-iron roof with ridge caps, deep eaves,
  // a fascia, gutter and downpipe, a brick chimney with a corbel and pots, a front bay with a
  // weatherboarded gable (barge boards, apex fretwork, a finial) and three tall sash windows under a
  // small hood, a lean-to verandah with posts, fretwork brackets, a frieze rail, a balustrade, a deck
  // and steps up to a panelled door with a glowing fanlight, and tall one-over-one sash windows with
  // facings, heads and sills. garden: true adds a lawn plinth, a picket fence with a gate, a path and
  // a hedge. setGlow(level) lights the windows. Same footprint as before (plus the garden if asked).
  const w = width, d = depth, h = height;
  const group = new THREE.Group();
  const add = (geometry, material, x, y, z, ry = 0) => { const m = new THREE.Mesh(geometry, material); m.position.set(x, y, z); m.rotation.y = ry; group.add(m); return m; };
  const beam = (from, to, thickness, material) => {   // a thin strip from one point to another
    const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to);
    const m = new THREE.Mesh(new THREE.BoxGeometry(thickness, thickness, a.distanceTo(b)), material);
    m.position.copy(a).add(b).multiplyScalar(0.5); m.lookAt(b); group.add(m); return m;
  };
  const boardTexture = (repeatX, repeatY) => { const t = printedCard('weatherboard', '#' + new THREE.Color(colour).getHexString()).clone(); t.needsUpdate = true; t.repeat.set(repeatX, repeatY); return t; };
  const wallMaterial = (rx, ry) => new THREE.MeshStandardMaterial({ color: 0xffffff, map: boardTexture(rx, ry), roughness: 0.9, envMapIntensity: 0.25, side: THREE.DoubleSide });
  const ironTexture = printedCard('iron', '#' + new THREE.Color(roofColour).getHexString()).clone(); ironTexture.needsUpdate = true; ironTexture.repeat.set(3, 2);
  const iron = new THREE.MeshStandardMaterial({ color: 0xffffff, map: ironTexture, roughness: 0.7, metalness: 0.15, envMapIntensity: 0.35, side: THREE.DoubleSide });
  const trim = paper(0xeae4d6, { side: THREE.DoubleSide }), dark = paper(0x3a3631), sillColour = paper(0xe2dbcb);
  const skirtPaint = paper(0x8f8676), ridge = paper(0x7d858c);
  const glass = new THREE.MeshStandardMaterial({ color: 0x2a3034, roughness: 0.3, metalness: 0.2, map: sashPanes(), emissive: 0xffb25e, emissiveMap: sashPanes(), emissiveIntensity: glow });
  const skirt = h * 0.12, wallH = h - skirt;

  // body on a painted skirting with dark vents, white corner boards
  add(new THREE.BoxGeometry(w + 0.03, skirt, d + 0.03), skirtPaint, 0, skirt / 2, 0);
  for (let i = 0; i < 4; i++) add(new THREE.PlaneGeometry(0.05, skirt * 0.35), dark, -w * 0.38 + i * w * 0.25, skirt * 0.5, d / 2 + 0.017);
  add(new THREE.BoxGeometry(w, wallH, d), wallMaterial(w / 0.5, wallH / 0.25), 0, skirt + wallH / 2, 0);
  for (const [x, z] of [[-w / 2, -d / 2], [w / 2, -d / 2], [-w / 2, d / 2], [w / 2, d / 2]]) add(new THREE.BoxGeometry(0.035, wallH, 0.035), trim, x, skirt + wallH / 2, z);

  // hipped roof (a four-sided pyramid stretched to the eaves), ridge caps on the hips, fascia, gutter
  const eave = Math.min(w, d) * 0.1, roofRise = h * 0.62, apex = [0, h + roofRise, 0];
  const hip = new THREE.ConeGeometry(Math.SQRT2, roofRise, 4, 1, true);
  hip.rotateY(Math.PI / 4);
  add(hip, iron, 0, h + roofRise / 2, 0).scale.set(w / 2 + eave, 1, d / 2 + eave);
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) beam(apex, [sx * (w / 2 + eave), h, sz * (d / 2 + eave)], 0.022, ridge);
  add(new THREE.BoxGeometry(w + 2 * eave, 0.035, d + 2 * eave), trim, 0, h + 0.005, 0);
  add(new THREE.BoxGeometry(w + 2 * eave, 0.03, 0.035), dark, 0, h - 0.01, d / 2 + eave);
  add(new THREE.CylinderGeometry(0.012, 0.012, wallH, 8), dark, w / 2 + eave * 0.6, skirt + wallH / 2, d / 2 + eave * 0.6);

  // brick chimney with a corbel band, a cap and two pots
  const chimneyTexture = printedCard('brick', '#9c5a43').clone(); chimneyTexture.needsUpdate = true; chimneyTexture.repeat.set(0.4, 1.2);
  const brick = new THREE.MeshStandardMaterial({ map: chimneyTexture, roughness: 0.9 });
  const cw = w * 0.11, chimneyHeight = h + roofRise * 1.05, cx = -w * 0.26, cz = -d * 0.12;
  add(new THREE.BoxGeometry(cw, chimneyHeight, cw), brick, cx, chimneyHeight / 2, cz);
  add(new THREE.BoxGeometry(cw * 1.3, 0.03, cw * 1.3), brick, cx, chimneyHeight - 0.06, cz);
  add(new THREE.BoxGeometry(cw * 1.35, 0.03, cw * 1.35), dark, cx, chimneyHeight + 0.015, cz);
  for (const k of [-1, 1]) add(new THREE.CylinderGeometry(0.016, 0.02, 0.06, 10), paper(0xa8573c), cx + k * cw * 0.25, chimneyHeight + 0.06, cz);

  // front bay with its own weatherboarded gable, barge boards, apex fretwork and a finial
  const bayW = w * 0.44, bayD = Math.min(0.4, d * 0.42), bayX = -w * 0.22;
  add(new THREE.BoxGeometry(bayW + 0.03, skirt, bayD), skirtPaint, bayX, skirt / 2, d / 2 + bayD / 2);
  add(new THREE.BoxGeometry(bayW, wallH, bayD), wallMaterial(bayW / 0.5, wallH / 0.25), bayX, skirt + wallH / 2, d / 2 + bayD / 2);
  const gableRise = h * 0.5, gableOver = 0.05, faceZ = d / 2 + bayD + eave * 0.5 + 0.082;
  const gable = new THREE.Shape();
  gable.moveTo(-bayW / 2 - gableOver, 0); gable.lineTo(0, gableRise); gable.lineTo(bayW / 2 + gableOver, 0); gable.lineTo(-bayW / 2 - gableOver, 0);
  add(new THREE.ExtrudeGeometry(gable, { depth: bayD + 0.08 + eave * 0.5, bevelEnabled: false }), iron, bayX, h, d / 2);
  const face = new THREE.Shape(); face.moveTo(-bayW / 2, 0); face.lineTo(0, gableRise * 0.92); face.lineTo(bayW / 2, 0); face.lineTo(-bayW / 2, 0);
  const faceGeometry = new THREE.ShapeGeometry(face);
  { const uv = faceGeometry.attributes.uv, pos = faceGeometry.attributes.position; for (let i = 0; i < uv.count; i++) uv.setXY(i, pos.getX(i) / 0.5, pos.getY(i) / 0.25); }
  add(faceGeometry, wallMaterial(1, 1), bayX, h + 0.004, faceZ);
  add(new THREE.BoxGeometry(bayW + 0.04, 0.025, 0.02), trim, bayX, h + 0.012, faceZ + 0.006);                 // band at the base of the gable
  const slope = Math.atan2(gableRise, bayW / 2 + gableOver), rafter = Math.hypot(gableRise, bayW / 2 + gableOver);
  for (const side of [-1, 1]) {
    const barge = add(new THREE.BoxGeometry(rafter, 0.045, 0.02), trim, bayX + side * (bayW / 2 + gableOver) / 2, h + gableRise / 2 - 0.01, faceZ + 0.008);
    barge.rotation.z = -side * slope;
  }
  const fretwork = new THREE.Shape();                                                                        // a pierced fan at the apex
  const fanR = bayW * 0.16, fanY = h + gableRise * 0.62;
  fretwork.moveTo(-fanR, 0); fretwork.lineTo(0, fanR * 0.9); fretwork.lineTo(fanR, 0); fretwork.lineTo(-fanR, 0);
  for (let i = 0; i < 4; i++) { const hole = new THREE.Path(); const hx = -fanR * 0.6 + i * fanR * 0.4; hole.moveTo(hx, 0.012); hole.lineTo(hx + fanR * 0.12, 0.012); hole.lineTo(hx + fanR * 0.06, fanR * 0.35); hole.lineTo(hx, 0.012); fretwork.holes.push(hole); }
  add(new THREE.ShapeGeometry(fretwork), trim, bayX, fanY, faceZ + 0.012);
  add(new THREE.ConeGeometry(0.018, 0.1, 8), trim, bayX, h + gableRise + 0.045, faceZ + 0.008);

  // windows: tall one-over-one sashes with wide white facings, a head and a sill
  const sash = (x, y, z, ry, sw, sh) => {
    add(new THREE.PlaneGeometry(sw, sh), glass, x, y + sh / 2, z, ry);
    const back = (amount) => [Math.sin(ry) * amount, Math.cos(ry) * amount];
    const [bx, bz] = back(-0.008);
    add(new THREE.BoxGeometry(sw + 0.05, sh + 0.05, 0.01), trim, x + bx, y + sh / 2, z + bz, ry);              // facings, just behind the glass
    const [hx, hz] = back(0.012);
    add(new THREE.BoxGeometry(sw + 0.08, 0.022, 0.03), trim, x + hx, y + sh + 0.035, z + hz, ry);            // head
    const [sx, sz] = back(0.02);
    add(new THREE.BoxGeometry(sw + 0.07, 0.022, 0.045), sillColour, x + sx, y - 0.022, z + sz, ry);           // sill
  };
  const bayZ = d / 2 + bayD + 0.004, lightW = bayW * 0.24, lightH = wallH * 0.62, bayY = skirt + wallH * 0.16;
  for (const k of [-1, 0, 1]) sash(bayX + k * lightW * 1.22, bayY, bayZ, 0, lightW, lightH);
  const hood = add(new THREE.BoxGeometry(bayW + 0.06, 0.018, 0.09), iron, bayX, bayY + lightH + 0.07, bayZ + 0.04);   // a small iron hood over the bay window
  hood.rotation.x = 0.35;
  const sashW = w * 0.09, sashH = wallH * 0.6, sashY = skirt + wallH * 0.18;
  sash(w * 0.12, sashY, d / 2 + 0.004, 0, sashW, sashH);
  sash(-w / 2 - 0.004, sashY, -d * 0.16, -Math.PI / 2, d * 0.14, sashH);
  sash(-w / 2 - 0.004, sashY, d * 0.2, -Math.PI / 2, d * 0.14, sashH);
  sash(w / 2 + 0.004, sashY, -d * 0.12, Math.PI / 2, d * 0.15, sashH);

  // panelled door with facings and a glowing fanlight
  const doorX = w * 0.36, doorW = w * 0.12, doorH = wallH * 0.66, front = d / 2 + 0.004;
  add(new THREE.BoxGeometry(doorW + 0.05, doorH + doorH * 0.22, 0.012), trim, doorX, skirt + (doorH * 1.22) / 2, front);
  add(new THREE.BoxGeometry(doorW, doorH, 0.016), paper(0x6e2f2a), doorX, skirt + doorH / 2, front + 0.006);
  for (const k of [0.3, 0.72]) add(new THREE.BoxGeometry(doorW * 0.6, doorH * 0.22, 0.008), paper(0x5a2622), doorX, skirt + doorH * k, front + 0.016);
  add(new THREE.CylinderGeometry(0.008, 0.008, 0.012, 8), paper(PAPER.ochre), doorX + doorW * 0.32, skirt + doorH * 0.5, front + 0.02).rotation.x = Math.PI / 2;
  add(new THREE.PlaneGeometry(doorW, doorH * 0.16), glass, doorX, skirt + doorH + doorH * 0.1, front + 0.007);

  // verandah: deck with an edge board, steps up to the door, posts, brackets, frieze rail, balustrade,
  // and a lean-to iron roof from under the main eaves down to the beam
  const verX = w * 0.24, verW = w * 0.5, verD = bayD * 0.95, verH = h * 0.8, deckY = skirt * 0.7;
  add(new THREE.BoxGeometry(verW, deckY, verD), paper(0x8b7b66), verX, deckY / 2, d / 2 + verD / 2);
  add(new THREE.BoxGeometry(verW + 0.01, 0.02, 0.012), trim, verX, deckY - 0.01, d / 2 + verD + 0.006);
  for (let i = 0; i < 2; i++) add(new THREE.BoxGeometry(doorW * 1.6, deckY * 0.5 * (2 - i), 0.07), paper(0x9c8b74), doorX, deckY * 0.25 * (2 - i), d / 2 + verD + 0.035 + i * 0.07);
  const roofTop = [verX, h - 0.012, d / 2], roofLow = [verX, verH + 0.03, d / 2 + verD + 0.05];
  const rise = roofTop[1] - roofLow[1], run = roofLow[2] - roofTop[2];
  const lean = add(new THREE.BoxGeometry(verW + 0.06, 0.018, Math.hypot(rise, run)), iron, verX, (roofTop[1] + roofLow[1]) / 2, (roofTop[2] + roofLow[2]) / 2);
  lean.rotation.x = Math.atan2(rise, run);
  add(new THREE.BoxGeometry(verW + 0.06, 0.03, 0.018), trim, verX, verH + 0.02, d / 2 + verD + 0.055);         // fascia on the verandah edge
  const postZ = d / 2 + verD - 0.03, posts = [verX - verW / 2 + 0.02, verX - verW * 0.06, verX + verW / 2 - 0.02];
  for (const x of posts) {
    add(new THREE.BoxGeometry(0.03, verH - deckY, 0.03), trim, x, deckY + (verH - deckY) / 2, postZ);
    for (const side of [-1, 1]) {
      const bracket = new THREE.Shape(); bracket.moveTo(0, 0); bracket.lineTo(side * 0.11, 0); bracket.quadraticCurveTo(side * 0.02, -0.02, 0, -0.11); bracket.lineTo(0, 0);
      const hole = new THREE.Path(); hole.moveTo(side * 0.015, -0.015); hole.lineTo(side * 0.05, -0.015); hole.lineTo(side * 0.015, -0.05); hole.lineTo(side * 0.015, -0.015); bracket.holes.push(hole);
      add(new THREE.ShapeGeometry(bracket), trim, x, verH - 0.012, postZ + 0.017);
    }
  }
  add(new THREE.BoxGeometry(verW, 0.025, 0.02), trim, verX, verH - 0.012, postZ + 0.012);                      // the beam
  add(new THREE.BoxGeometry(verW, 0.012, 0.012), trim, verX, verH - 0.07, postZ + 0.012);                      // frieze rail
  for (let x = verX - verW / 2 + 0.03; x < verX + verW / 2 - 0.02; x += 0.035) add(new THREE.BoxGeometry(0.006, 0.05, 0.006), trim, x, verH - 0.042, postZ + 0.012);
  const railY = deckY + 0.12, gapFrom = doorX - doorW * 0.9, gapTo = doorX + doorW * 0.9;                      // balustrade, open at the steps
  for (const [x0, x1] of [[verX - verW / 2 + 0.02, gapFrom], [gapTo, verX + verW / 2 - 0.02]]) {
    if (x1 - x0 < 0.03) continue;
    add(new THREE.BoxGeometry(x1 - x0, 0.015, 0.02), trim, (x0 + x1) / 2, railY, postZ);
    for (let x = x0 + 0.02; x < x1 - 0.01; x += 0.04) add(new THREE.BoxGeometry(0.008, railY - deckY, 0.008), trim, x, deckY + (railY - deckY) / 2, postZ);
  }

  // an optional garden: lawn plinth, path, picket fence with a gate gap, a rounded hedge
  if (garden) {
    const gw = w * 1.55, gd = d + bayD + 0.55, gz = (d / 2 + bayD + 0.55) - gd / 2;
    add(new THREE.BoxGeometry(gw, 0.03, gd), paper(0x6f7a46), 0, -0.012, gz);
    add(new THREE.BoxGeometry(doorW * 1.6, 0.034, 0.55 - 0.07), paper(0xc9c1b0), doorX, -0.008, d / 2 + verD + 0.14 + (0.55 - 0.14) / 2);
    const fenceZ = d / 2 + bayD + 0.5, picket = paper(0xf2ede2);
    for (let x = -gw / 2 + 0.02; x < gw / 2; x += 0.045) {
      if (Math.abs(x - doorX) < doorW * 0.9) continue;
      add(new THREE.BoxGeometry(0.018, 0.13, 0.008), picket, x, 0.065, fenceZ);
      add(new THREE.ConeGeometry(0.011, 0.02, 4), picket, x, 0.14, fenceZ).rotation.y = Math.PI / 4;
    }
    for (const y of [0.04, 0.1]) {
      for (const [x0, x1] of [[-gw / 2, doorX - doorW * 0.9], [doorX + doorW * 0.9, gw / 2]]) add(new THREE.BoxGeometry(x1 - x0, 0.012, 0.008), picket, (x0 + x1) / 2, y, fenceZ - 0.008);
    }
    const hedge = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 12), paper(0x3f5a33));
    hedge.scale.set(1.4, 0.8, 1); hedge.position.set(-gw / 2 + 0.2, 0.08, fenceZ - 0.2); group.add(hedge);
  }

  shadowing(group);
  group.traverse((o) => { if (o.isMesh && o.material === glass) o.castShadow = false; });
  return { group, setGlow(level) { glass.emissiveIntensity = level; } };
}

// ------------------------------------------------------------------------------------- shells
// An artillery shell of the First World War: brass case body with a copper driving band and a
// darker nose. Stands on its base. height in world units.
let shellGeometry = null;
export function shell({ height = 0.6 } = {}) {
  if (!shellGeometry) {
    const profile = [[0, 0], [0.16, 0], [0.165, 0.02], [0.165, 0.58], [0.17, 0.6], [0.17, 0.66], [0.165, 0.68], [0.16, 0.74], [0.14, 0.84], [0.1, 0.93], [0.05, 0.99], [0.0, 1.0]];
    shellGeometry = new THREE.LatheGeometry(profile.map(([r, y]) => new THREE.Vector2(r, y)), 28);
  }
  const group = new THREE.Group();
  const body = new THREE.Mesh(shellGeometry, metal(0xc8a24a, { roughness: 0.28 }));
  const band = new THREE.Mesh(new THREE.CylinderGeometry(0.172, 0.172, 0.05, 28), metal(0xb0643a, { roughness: 0.35 }));
  band.position.y = 0.63;
  group.add(body, band);
  group.scale.setScalar(height);
  shadowing(group);
  return { group };
}

// -------------------------------------------------------------------------------------- coins
let coinFace = null;
function coinFaceTexture() {
  if (!coinFace) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#c9a54a'; ctx.fillRect(0, 0, 256, 256);
    ctx.strokeStyle = 'rgba(80,55,10,0.55)'; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.arc(128, 128, 112, 0, Math.PI * 2); ctx.stroke();
    ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(128, 128, 92, 0, Math.PI * 2); ctx.stroke();
    for (let i = 0; i < 48; i++) { const a = i / 48 * Math.PI * 2; ctx.beginPath(); ctx.moveTo(128 + Math.cos(a) * 98, 128 + Math.sin(a) * 98); ctx.lineTo(128 + Math.cos(a) * 106, 128 + Math.sin(a) * 106); ctx.stroke(); }
    ctx.fillStyle = 'rgba(90,62,12,0.5)'; ctx.beginPath(); ctx.arc(128, 128, 40, 0, Math.PI * 2); ctx.fill();
    coinFace = canvasTexture(canvas);
  }
  return coinFace;
}
// A gold coin, `radius` wide, lying flat (rotate the group to stand it).
export function coin({ radius = 0.16, thickness = 0.03 } = {}) {
  const face = new THREE.MeshStandardMaterial({ map: coinFaceTexture(), color: 0xffffff, metalness: 1, roughness: 0.3, envMapIntensity: 1.2 });
  const edge = metal(0xc9a54a, { roughness: 0.34 });
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, thickness, 32), [edge, face, face]);
  const group = new THREE.Group(); group.add(mesh);
  shadowing(group);
  return { group };
}

// ------------------------------------------------------------------------------------ banknotes
let noteTexture = null;
function banknoteTexture() {
  if (!noteTexture) {
    // an invented note: no real design, no real words, just the look of an engraved note
    const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#9fb296'; ctx.fillRect(0, 0, 512, 256);
    ctx.strokeStyle = 'rgba(52,78,64,0.6)'; ctx.lineWidth = 6; ctx.strokeRect(14, 14, 484, 228);
    ctx.lineWidth = 1.2;
    for (let i = 0; i < 60; i++) { ctx.beginPath(); ctx.ellipse(380, 128, 30 + i * 1.6, 50 + i * 1.2, 0, 0, Math.PI * 2); ctx.globalAlpha = 0.08; ctx.stroke(); }
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgba(52,78,64,0.75)'; ctx.font = '700 64px Inter'; ctx.fillText('100', 40, 90);
    ctx.fillStyle = 'rgba(52,78,64,0.35)'; for (let i = 0; i < 6; i++) ctx.fillRect(40, 130 + i * 14, 200 - i * 18, 5);
    noteTexture = canvasTexture(canvas);
  }
  return noteTexture;
}
// the edges of a stack of notes: fine pale and dark lines, one per note
let edgeTexture = null;
function noteEdgeTexture() {
  if (!edgeTexture) {
    const canvas = document.createElement('canvas'); canvas.width = 16; canvas.height = 128;
    const ctx = canvas.getContext('2d');
    for (let y = 0; y < 128; y += 4) { ctx.fillStyle = '#a9b99f'; ctx.fillRect(0, y, 16, 3); ctx.fillStyle = '#5f7259'; ctx.fillRect(0, y + 3, 16, 1); }
    edgeTexture = canvasTexture(canvas);
  }
  return edgeTexture;
}
// A bundle of banknotes with a paper band, lying flat. `notes` sets its thickness.
export function banknoteBundle({ width = 0.9, depth = 0.45, notes = 40 } = {}) {
  const height = notes * 0.004;
  const top = new THREE.MeshStandardMaterial({ map: banknoteTexture(), roughness: 0.85 });
  const side = new THREE.MeshStandardMaterial({ map: noteEdgeTexture(), roughness: 0.9 });
  const group = new THREE.Group();
  const block = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), [side, side, top, side, side, side]);
  block.position.y = height / 2; group.add(block);
  const band = new THREE.Mesh(new THREE.BoxGeometry(width * 0.16, height + 0.008, depth + 0.008), paper(0xb08a3e));
  band.position.y = height / 2; group.add(band);
  shadowing(group);
  return { group, height };
}

// ----------------------------------------------------------------------------------- price tag
// A manila card tag with a reinforced hole and a loop of string, its price printed in dark ink.
// setText(text) reprints it (only when it changes). The tag hangs from its hole (the group's origin).
export function priceTag({ width = 0.9, text = '', colour = '#d9c79a', ink = '#22282c', accent = null } = {}) {
  const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 300;
  const texture = canvasTexture(canvas);
  let printed = null;
  const print = (value) => {
    if (value === printed) return;
    printed = value;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, 512, 300);
    ctx.fillStyle = colour;
    ctx.beginPath(); ctx.moveTo(0, 150); ctx.lineTo(80, 10); ctx.lineTo(500, 10); ctx.lineTo(500, 290); ctx.lineTo(80, 290); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.12)'; ctx.beginPath(); ctx.arc(62, 150, 30, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#efe6d2'; ctx.beginPath(); ctx.arc(62, 150, 22, 0, Math.PI * 2); ctx.fill();
    ctx.globalCompositeOperation = 'destination-out'; ctx.beginPath(); ctx.arc(62, 150, 12, 0, Math.PI * 2); ctx.fill();
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = accent ?? ink; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    let size = 150; ctx.font = `800 ${size}px Inter`;
    while (ctx.measureText(value).width > 370 && size > 40) { size -= 6; ctx.font = `800 ${size}px Inter`; }
    ctx.fillText(value, 300, 158);
    texture.needsUpdate = true;
  };
  const height = width * 300 / 512;
  const geometry = new THREE.PlaneGeometry(width, height);
  geometry.translate(width / 2 - width * 62 / 512, 0, 0); // origin at the hole
  const material = new THREE.MeshStandardMaterial({ map: texture, transparent: false, alphaTest: 0.5, roughness: 0.9, side: THREE.DoubleSide });
  const card = new THREE.Mesh(geometry, material);
  card.castShadow = true; card.receiveShadow = true;
  card.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: texture, alphaTest: 0.5 });
  const string = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 0), new THREE.Vector3(-0.12 * width, 0.12 * width, 0.02), new THREE.Vector3(-0.3 * width, 0.08 * width, 0.0), new THREE.Vector3(-0.42 * width, 0.22 * width, -0.02)]), 20, 0.008 * width / 0.9, 6), paper(0xe8dcc0));
  const group = new THREE.Group(); group.add(card, string);
  loadFonts().then(() => { const p = printed; printed = null; print(p ?? text); });
  print(text);
  return { group, card, setText: print, width, height };
}

// ---------------------------------------------------------------------------- split-flap counter
// A railway-station style counter: a row of cells, each a dark card flap printing one character.
// A cell flips over when its character changes (top half falls, showing the new one). Give it a
// schedule of [{ t, text }] (text is right-aligned to the cells) and call pose(t). Stateless.
const FLAP_CHARACTERS = ' 0123456789.,%$x+-:/£¥ABCDEFGHIJKLMNOPQRSTUVWXYZ';
let flapAtlas = null;
function flapAtlasTexture() {
  if (!flapAtlas) {
    const cell = 128, columns = 16, rows = Math.ceil(FLAP_CHARACTERS.length / columns);
    const canvas = document.createElement('canvas'); canvas.width = cell * columns; canvas.height = cell * 2 * rows;
    const ctx = canvas.getContext('2d');
    for (let i = 0; i < FLAP_CHARACTERS.length; i++) {
      const x = (i % columns) * cell, y = Math.floor(i / columns) * cell * 2;
      const gradient = ctx.createLinearGradient(0, y, 0, y + cell * 2);
      gradient.addColorStop(0, '#2b3034'); gradient.addColorStop(0.5, '#1f2326'); gradient.addColorStop(1, '#2a2f33');
      ctx.fillStyle = gradient; ctx.fillRect(x + 2, y + 2, cell - 4, cell * 2 - 4);
      // each letter is clipped to its own tile, so wide ones (%) don't spill into their neighbours
      ctx.save(); ctx.beginPath(); ctx.rect(x + 2, y + 2, cell - 4, cell * 2 - 4); ctx.clip();
      ctx.fillStyle = '#f1e9d6'; ctx.font = '700 176px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(FLAP_CHARACTERS[i], x + cell / 2, y + cell + 10);
      ctx.restore();
      ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(x, y + cell - 2, cell, 4);
    }
    flapAtlas = canvasTexture(canvas);
    flapAtlas.userData = { cell, columns, rows };
  }
  return flapAtlas;
}
function flapUV(geometry, character, half) {
  const atlas = flapAtlasTexture(), { columns, rows } = atlas.userData;
  const index = Math.max(0, FLAP_CHARACTERS.indexOf(character));
  const u0 = (index % columns) / columns, u1 = u0 + 1 / columns;
  const row = Math.floor(index / columns);
  const vTop = 1 - row / rows, vMid = vTop - 0.5 / rows, vBottom = vTop - 1 / rows;
  const [v0, v1] = half === 'top' ? [vMid, vTop] : [vBottom, vMid];
  const uv = geometry.attributes.uv;
  // PlaneGeometry corners: (0,1) (1,1) (0,0) (1,0)
  uv.setXY(0, u0, v1); uv.setXY(1, u1, v1); uv.setXY(2, u0, v0); uv.setXY(3, u1, v0);
  uv.needsUpdate = true;
}
export function splitFlap({ cells = 6, cellWidth = 0.42, gap = 0.04, flipTime = 0.16, housing = true } = {}) {
  const cellHeight = cellWidth * 2;
  const group = new THREE.Group();
  const material = new THREE.MeshStandardMaterial({ map: flapAtlasTexture(), roughness: 0.55, metalness: 0.1 });
  const halves = [];
  for (let i = 0; i < cells; i++) {
    const x = (i - (cells - 1) / 2) * (cellWidth + gap);
    const make = (half, y) => {
      const geometry = new THREE.PlaneGeometry(cellWidth, cellHeight / 2);
      if (half === 'top') geometry.translate(0, cellHeight / 4, 0); else geometry.translate(0, -cellHeight / 4, 0);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(x, y, 0);
      mesh.castShadow = true;
      group.add(mesh);
      return mesh;
    };
    const cell = { top: make('top', 0), bottom: make('bottom', 0), flapTop: make('top', 0.002), flapBottom: make('bottom', 0.002) };
    cell.flapTop.position.z = 0.004; cell.flapBottom.position.z = 0.004;
    halves.push(cell);
  }
  if (housing) {
    const width = cells * (cellWidth + gap) + gap * 3, height = cellHeight + gap * 4;
    const box = new THREE.Mesh(new THREE.BoxGeometry(width, height, 0.18), paper(0x1a1d20, { roughness: 0.7 }));
    box.position.z = -0.1; box.castShadow = true; box.receiveShadow = true;
    group.add(box);
  }
  const shown = halves.map(() => ({ top: null, bottom: null, flapTop: null, flapBottom: null }));
  const setHalf = (i, part, character, half) => {
    if (shown[i][part] === character) return;
    shown[i][part] = character;
    flapUV(halves[i][part].geometry, character, half);
  };
  const align = (text) => String(text).toUpperCase().padStart(cells, ' ').slice(-cells);
  return {
    group, width: cells * (cellWidth + gap), height: cellHeight,
    // schedule: [{ t, text }] in time order
    pose(t, schedule) {
      let current = 0;
      while (current + 1 < schedule.length && schedule[current + 1].t <= t) current++;
      if (t < schedule[0].t) current = -1;
      const now = current >= 0 ? align(schedule[current].text) : align('');
      const before = current >= 1 ? align(schedule[current - 1].text) : align('');
      const age = current >= 0 ? t - schedule[current].t : Infinity;
      for (let i = 0; i < cells; i++) {
        const stagger = i * 0.025;
        const k = clamp01((age - stagger) / flipTime);
        const from = before[i], to = now[i];
        if (from === to || k >= 1) {
          setHalf(i, 'top', to, 'top'); setHalf(i, 'bottom', to, 'bottom');
          halves[i].flapTop.visible = false; halves[i].flapBottom.visible = false;
          continue;
        }
        // behind: new top, old bottom; the old top falls (k < 0.5), then the new bottom lands
        setHalf(i, 'top', to, 'top'); setHalf(i, 'bottom', from, 'bottom');
        setHalf(i, 'flapTop', from, 'top'); setHalf(i, 'flapBottom', to, 'bottom');
        const angle = Math.PI * k;
        halves[i].flapTop.visible = angle < Math.PI / 2;
        halves[i].flapTop.rotation.x = angle;
        halves[i].flapBottom.visible = angle >= Math.PI / 2;
        halves[i].flapBottom.rotation.x = angle - Math.PI;
      }
    },
  };
}
// A schedule that counts from one number to another between two times (for a counter that runs up).
export function countSchedule({ from, to, start, finish, steps = 24, format = (v) => String(Math.round(v)), ease = smooth }) {
  const schedule = [];
  for (let i = 0; i <= steps; i++) schedule.push({ t: lerp(start, finish, i / steps), text: format(lerp(from, to, ease(i / steps))) });
  return schedule;
}

// --------------------------------------------------------------------------------------- dial
// A meter: a round card face with a printed scale from `min` to `max`, a label, and a needle.
// setValue(v) turns the needle. The face looks along +z.
export function dial({ radius = 1, min = 0, max = 8, step = 1, label = '', unit = '%', sweep = 240, accent = '#b23a2a' } = {}) {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 1024;
  const ctx = canvas.getContext('2d');
  const angleOf = (v) => THREE.MathUtils.degToRad(90 + sweep / 2 - (v - min) / (max - min) * sweep);
  const draw = () => {
    ctx.clearRect(0, 0, 1024, 1024);
    ctx.fillStyle = '#ece3cf'; ctx.beginPath(); ctx.arc(512, 512, 500, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#2b3135'; ctx.lineWidth = 14; ctx.beginPath(); ctx.arc(512, 512, 470, 0, Math.PI * 2); ctx.stroke();
    ctx.lineCap = 'round';
    for (let v = min; v <= max + 1e-6; v += step / 2) {
      const a = angleOf(v), major = Math.abs((v - min) / step - Math.round((v - min) / step)) < 1e-6;
      ctx.lineWidth = major ? 10 : 5; ctx.strokeStyle = '#2b3135';
      ctx.beginPath(); ctx.moveTo(512 + Math.cos(a) * (major ? 370 : 395), 512 - Math.sin(a) * (major ? 370 : 395)); ctx.lineTo(512 + Math.cos(a) * 430, 512 - Math.sin(a) * 430); ctx.stroke();
      if (major) { ctx.fillStyle = '#2b3135'; ctx.font = '700 70px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(`${+v.toFixed(2)}`, 512 + Math.cos(a) * 300, 512 - Math.sin(a) * 300); }
    }
    ctx.strokeStyle = accent; ctx.lineWidth = 16; ctx.beginPath(); ctx.arc(512, 512, 450, -angleOf(min), -angleOf(max)); ctx.stroke();
    ctx.fillStyle = '#2b3135'; ctx.font = '800 64px Inter'; ctx.textAlign = 'center'; ctx.fillText(label, 512, 700);
    ctx.font = '600 52px Inter'; ctx.fillText(unit, 512, 770);
  };
  const texture = canvasTexture(canvas);
  draw(); loadFonts().then(() => { draw(); texture.needsUpdate = true; });
  const group = new THREE.Group();
  const face = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 0.08, 64), [paper(PAPER.charcoal), new THREE.MeshStandardMaterial({ map: texture, roughness: 0.85 }), paper(PAPER.charcoal)]);
  face.rotation.x = Math.PI / 2; group.add(face);
  const needleShape = new THREE.Shape();
  needleShape.moveTo(-0.05 * radius, 0); needleShape.lineTo(0, 0.82 * radius); needleShape.lineTo(0.05 * radius, 0); needleShape.lineTo(0, -0.14 * radius); needleShape.lineTo(-0.05 * radius, 0);
  const needle = new THREE.Mesh(new THREE.ExtrudeGeometry(needleShape, { depth: 0.03, bevelEnabled: false }), paper(0xa83324, { roughness: 0.6 }));
  const needleHolder = new THREE.Group(); needleHolder.position.z = 0.06; needleHolder.add(needle); group.add(needleHolder);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.07 * radius, 0.07 * radius, 0.06, 24), metal(0x8c8f8f, { roughness: 0.4 }));
  cap.rotation.x = Math.PI / 2; cap.position.z = 0.1; group.add(cap);
  shadowing(group);
  return { group, setValue(v) { needleHolder.rotation.z = angleOf(v) - Math.PI / 2; } };
}

// ----------------------------------------------------------------------------------- oil barrel
export function oilBarrel({ height = 1.2, colour = 0x2c4a5a } = {}) {
  const radius = height * 0.34;
  const group = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, height, 40, 1, false), metal(colour, { roughness: 0.55, metalness: 0.6 }));
  body.position.y = height / 2; group.add(body);
  for (const y of [0.04, 0.33, 0.67, 0.96]) {
    const rib = new THREE.Mesh(new THREE.TorusGeometry(radius * 1.01, height * 0.012, 8, 40), metal(colour, { roughness: 0.5, metalness: 0.6 }));
    rib.rotation.x = Math.PI / 2; rib.position.y = height * y; group.add(rib);
  }
  shadowing(group);
  return { group, radius, height };
}

// ------------------------------------------------------------------------------------ paper boat
// A folded paper boat (a cargo ship in miniature), length along x.
export function paperBoat({ length = 1.6, colour = PAPER.ivory } = {}) {
  const h = length * 0.22, w = length * 0.22;
  const geometry = new THREE.BufferGeometry();
  const L = length / 2;
  // hull: two sloped sides and a sail-like centre fin, as folded paper
  const v = [
    -L, h, 0, -L * 0.62, 0, -w, L * 0.62, 0, -w,   L * 0.62, 0, -w, L, h, 0, -L, h, 0,
    -L, h, 0, L, h, 0, L * 0.62, 0, w,   L * 0.62, 0, w, -L * 0.62, 0, w, -L, h, 0,
    -L * 0.5, h * 0.6, 0, L * 0.5, h * 0.6, 0, 0, h * 2.6, 0,
  ];
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, paper(colour, { side: THREE.DoubleSide }));
  mesh.castShadow = true; mesh.receiveShadow = true;
  const group = new THREE.Group(); group.add(mesh);
  return { group };
}

// --------------------------------------------------------------------------------- bar columns
// A chart whose bars are card columns rising from a base, each with a printed value on top.
// values: numbers; setProgress(i, k) raises bar i to share k of its height.
export function barColumns({ values, maxValue, height = 3, barWidth = 0.6, gap = 0.3, colours = [PAPER.ivory], labels = [] } = {}) {
  const group = new THREE.Group();
  const bars = values.map((value, i) => {
    const holder = new THREE.Group();
    holder.position.x = (i - (values.length - 1) / 2) * (barWidth + gap);
    const full = height * value / (maxValue ?? Math.max(...values));
    const bar = new THREE.Mesh(new THREE.BoxGeometry(barWidth, 1, barWidth * 0.5), paper(colours[i % colours.length]));
    bar.geometry.translate(0, 0.5, 0);
    bar.castShadow = true; bar.receiveShadow = true;
    holder.add(bar); group.add(holder);
    return { holder, bar, full };
  });
  return { group, bars, setProgress(i, k) { const b = bars[i]; b.bar.scale.y = Math.max(0.001, b.full * k); b.bar.visible = k > 0.001; }, topOf(i) { const b = bars[i]; return new THREE.Vector3(b.holder.position.x, b.full * b.bar.scale.y / Math.max(1e-6, b.full), 0); } };
}

// --------------------------------------------------------------------------------- thread chart
// A line chart made of a red thread stretched between brass pins on a card board. points: [[x, y]]
// in board units (0..1 across, 0..1 up). setProgress(k) draws the thread from the first pin to share
// k of the way. The board looks along +z.
export function threadChart({ points, width = 4, height = 3, colour = 0xb23a2a, board = true, boardColour = PAPER.cream } = {}) {
  const group = new THREE.Group();
  if (board) {
    const card = new THREE.Mesh(new THREE.BoxGeometry(width * 1.12, height * 1.18, 0.04), paper(boardColour));
    card.position.set(width / 2, height / 2, -0.03); card.castShadow = true; card.receiveShadow = true;
    group.add(card);
  }
  const world = points.map(([x, y]) => new THREE.Vector3(x * width, y * height, 0.05));
  const pins = world.map((p) => {
    const pin = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 10), metal(0xc9a54a, { roughness: 0.3 }));
    pin.position.copy(p).setZ(0.08); pin.castShadow = true; group.add(pin); return pin;
  });
  const curve = new THREE.CurvePath();
  for (let i = 0; i < world.length - 1; i++) curve.add(new THREE.LineCurve3(world[i], world[i + 1]));
  const segments = Math.max(8, (world.length - 1) * 12);
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, segments, 0.022, 6, false), paper(colour, { roughness: 0.7 }));
  tube.castShadow = true; group.add(tube);
  const indexCount = tube.geometry.index.count;
  return {
    group, pins, pointAt: (i) => world[i].clone(),
    setProgress(k) {
      const shown = Math.floor(clamp01(k) * segments) * 6 * 6;
      tube.geometry.setDrawRange(0, Math.min(indexCount, shown));
      tube.visible = k > 0.001;
      pins.forEach((pin, i) => { pin.visible = i / Math.max(1, world.length - 1) <= k + 1e-6; });
    },
  };
}
