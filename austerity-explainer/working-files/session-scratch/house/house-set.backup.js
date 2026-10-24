// What this does: builds "the house" for the house sample (log 27): one tall British building of the
// 1920s, cut open at the front like a doll's house, so every floor of society shows at once:
//   top floor     the Treasury (where it's decided) and the Bank's vault
//   middle floor  what public money builds: council houses going up, and a school
//   ground floor  work and home: a factory floor and a family's kitchen
//   cellar        the mine
// with a pitched slate roof and chimneys above, and a pavement in front where people can stand.
// The rooms are real 3D boxes (floor, ceiling, side walls, back wall), so the camera can move through
// the house without anything tearing. Back walls wear crops of the series' existing paintings; the
// other surfaces are plain painted colours. Each room has a light level (0 dark, 1 lit) that brightens
// its walls, its lamp and the cut-outs standing in it, so lights can go out on a word.
//
// How it fits: house-sample/page-1.js calls buildHouse(kit) once and gets back the rooms, the floor
// heights and helpers; it places the cut-outs and sets the light levels for each moment.
// Units: the house is about 9.2 wide and 16 tall; x across (0 is the middle), y up (the pavement is at
// y 4.3), z toward the camera (the cut-open front is at z 0, back walls at z -3).

import { THREE, canvasTexture, loadTexture } from '../../stage/cinema-stage.js';
import { seededRandom, lerp } from '../cinema-kit.js';

const PAINTINGS = '/paper-film/pieces/austerity-chapter-1';
export const FRONT = 0, DEPTH = 3;
export const LEFT = -4.3, RIGHT = 4.3, WALL = 0.32;
// floors: the bottom (floor) and top (ceiling) of each storey's inside
export const FLOORS = {
  cellar: { bottom: 0.9, top: 3.9 },
  ground: { bottom: 4.3, top: 7.6 },
  middle: { bottom: 7.9, top: 11.1 },
  top: { bottom: 11.4, top: 14.3 },
};
export const STREET = 4.3, EAVES = 14.65, RIDGE = 16.1;
export const DIVIDE = 0.5;   // the wall between the left and right rooms (top and ground floors)

// ------------------------------------------------------------------------- painted surfaces
// A canvas painted with soft strokes, so plain colours don't look like flat plastic.
function paintedCanvas(width, height, base, { strokes = 900, spread = 26, seed = 3, draw } = {}) {
  const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = base; ctx.fillRect(0, 0, width, height);
  draw?.(ctx, width, height);
  const random = seededRandom(seed);
  for (let i = 0; i < strokes; i++) {
    const shade = (random() - 0.5) * spread;
    ctx.fillStyle = shade > 0 ? `rgba(255,240,220,${shade / 255})` : `rgba(10,8,6,${-shade / 255})`;
    const x = random() * width, y = random() * height, w = 8 + random() * 40, h = 3 + random() * 10;
    ctx.save(); ctx.translate(x, y); ctx.rotate((random() - 0.5) * 0.6); ctx.fillRect(-w / 2, -h / 2, w, h); ctx.restore();
  }
  return canvas;
}
function bricks(ctx, width, height, { brick = 40, course = 16, mortar = 'rgba(40,30,26,0.75)', seed = 9 } = {}) {
  const random = seededRandom(seed);
  for (let row = 0; row * course < height; row++) {
    const offset = (row % 2) * brick / 2;
    for (let x = -brick; x < width; x += brick) {
      const tone = Math.floor(random() * 40) - 20;
      ctx.fillStyle = `rgba(${tone > 0 ? '255,200,170' : '20,10,8'},${Math.abs(tone) / 160})`;
      ctx.fillRect(x + offset + 1, row * course + 1, brick - 2, course - 2);
    }
    ctx.fillStyle = mortar; ctx.fillRect(0, row * course, width, 2);
    for (let x = -brick; x < width; x += brick) ctx.fillRect(x + offset, row * course, 2, course);
  }
}
function texture(canvas, repeatX = 1, repeatY = 1) {
  const t = canvasTexture(canvas);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeatX, repeatY);
  return t;
}
const surfaces = {};
function surface(name) {
  if (surfaces[name]) return surfaces[name];
  const make = {
    brick: () => paintedCanvas(512, 512, '#6e3b2c', { draw: (c, w, h) => bricks(c, w, h), spread: 30, seed: 4 }),
    plaster: () => paintedCanvas(256, 256, '#cfc2a8', { spread: 22, seed: 5 }),
    planks: () => paintedCanvas(512, 256, '#5b4130', { seed: 6, draw: (c, w, h) => { for (let y = 0; y < h; y += 32) { c.fillStyle = 'rgba(20,12,8,0.6)'; c.fillRect(0, y, w, 2); } } }),
    stone: () => paintedCanvas(512, 512, '#3e4744', { seed: 7, draw: (c, w, h) => bricks(c, w, h, { brick: 128, course: 64, mortar: 'rgba(14,18,18,0.8)', seed: 3 }) }),
    rock: () => paintedCanvas(512, 512, '#54473c', { seed: 8, strokes: 1600, spread: 40, draw: (c, w, h) => {
      const random = seededRandom(21);
      for (let i = 0; i < 5; i++) {   // seams of coal running across the rock
        const y = h * (0.15 + 0.17 * i + random() * 0.05);
        c.fillStyle = 'rgba(6,6,8,0.85)';
        c.beginPath(); c.moveTo(0, y);
        for (let x = 0; x <= w; x += 32) c.lineTo(x, y + Math.sin(x * 0.02 + i) * 6 + random() * 4);
        for (let x = w; x >= 0; x -= 32) c.lineTo(x, y + 10 + random() * 14 + Math.sin(x * 0.02 + i) * 6);
        c.fill();
      }
    } }),
    slate: () => paintedCanvas(512, 512, '#2f3a42', { seed: 10, draw: (c, w, h) => bricks(c, w, h, { brick: 48, course: 22, mortar: 'rgba(10,14,18,0.8)', seed: 8 }) }),
    earth: () => paintedCanvas(256, 256, '#241c16', { seed: 11, strokes: 700, spread: 30 }),
    pavement: () => paintedCanvas(512, 256, '#4a4d50', { seed: 12, draw: (c, w, h) => bricks(c, w, h, { brick: 128, course: 128, mortar: 'rgba(20,22,24,0.7)', seed: 2 }) }),
  }[name];
  surfaces[name] = make();
  return surfaces[name];
}

// ------------------------------------------------------------------------- glows (lamps)
let glowTexture = null;
function glowSprite(colour = 0xffc27a, size = 1, opacity = 1) {
  if (!glowTexture) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.18, 'rgba(255,255,255,0.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
    glowTexture = canvasTexture(canvas);
  }
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture, color: colour, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  sprite.scale.set(size, size, 1);
  sprite.userData.baseOpacity = opacity;
  return sprite;
}
export { glowSprite };

// ------------------------------------------------------------------------- a room
// A material that is dim (moonlight only) when the room is dark and shows its picture by its own
// light when lit: `glow` scales how bright it gets at full light.
function roomMaterial(map, { tint = 0xffe6c4, glow = 1, dark = 0x2a3140 } = {}) {
  const material = new THREE.MeshLambertMaterial({ map, color: dark, emissive: tint, emissiveMap: map, emissiveIntensity: 0 });
  material.userData.glow = glow;
  return material;
}
function plane(width, height, material) {
  return new THREE.Mesh(new THREE.PlaneGeometry(width, height), material);
}

// Crops a painting (pixels from its top) to fit a wall of the given width and height.
async function wallPicture(name, { top, width, height }) {
  const source = await loadTexture(`${PAINTINGS}/${name}.jpg`);
  const picture = source.clone();
  const W = source.image.width, H = source.image.height;
  const cropHeight = W * height / width;
  picture.repeat.set(1, cropHeight / H);
  picture.offset.set(0, 1 - (top + cropHeight) / H);
  picture.needsUpdate = true;
  return picture;
}

class Room {
  constructor(scene, { name, x0, x1, storey, back, floor = 'planks', sides = 'plaster', sideTint = 0xd9c6a4, lamp = [0.5, 0.8], lampColour = 0xffc27a, warmth = 0xffe6c4 }) {
    this.name = name;
    const { bottom: y0, top: y1 } = FLOORS[storey];
    Object.assign(this, { x0, x1, y0, y1, storey });
    this.group = new THREE.Group();
    scene.add(this.group);
    this.materials = [];
    this.pieces = [];
    this.lamps = [];
    this.level = 1;
    const width = x1 - x0, height = y1 - y0, middle = (x0 + x1) / 2;
    const add = (mesh) => { this.group.add(mesh); return mesh; };
    const keep = (material) => { this.materials.push(material); return material; };
    // back wall: a crop of a painting, or a painted surface
    const backMaterial = keep(roomMaterial(back.picture ?? texture(surface(back.surface ?? 'plaster'), width / 3, height / 3), { tint: back.tint ?? warmth, glow: back.glow ?? 1 }));
    const wall = add(plane(width, height, backMaterial));
    wall.position.set(middle, (y0 + y1) / 2, FRONT - DEPTH);
    // floor and ceiling
    const floorMaterial = keep(roomMaterial(texture(surface(floor), width / 3, 1), { tint: warmth, glow: 0.8 }));
    const ground = add(plane(width, DEPTH, floorMaterial));
    ground.rotation.x = -Math.PI / 2; ground.position.set(middle, y0, FRONT - DEPTH / 2);
    const ceilingMaterial = keep(roomMaterial(texture(surface(sides), width / 2, 1), { tint: sideTint, glow: 0.45 }));
    const ceiling = add(plane(width, DEPTH, ceilingMaterial));
    ceiling.rotation.x = Math.PI / 2; ceiling.position.set(middle, y1, FRONT - DEPTH / 2);
    this.ceiling = ceiling;
    // side walls
    const sideMaterial = keep(roomMaterial(texture(surface(sides), 1, height / 3), { tint: sideTint, glow: 0.45 }));
    const left = add(plane(DEPTH, height, sideMaterial));
    left.rotation.y = Math.PI / 2; left.position.set(x0, (y0 + y1) / 2, FRONT - DEPTH / 2);
    const right = add(plane(DEPTH, height, sideMaterial));
    right.rotation.y = -Math.PI / 2; right.position.set(x1, (y0 + y1) / 2, FRONT - DEPTH / 2);
    // a hanging lamp and the pool of light it throws on the back wall
    if (lamp) {
      const at = new THREE.Vector3(lerp(x0, x1, lamp[0]), lerp(y0, y1, lamp[1]), FRONT - DEPTH * 0.45);
      const flex = add(new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, y1 - at.y, 5), new THREE.MeshBasicMaterial({ color: 0x15110e })));
      flex.position.set(at.x, (y1 + at.y) / 2, at.z);
      const bulb = glowSprite(lampColour, 0.55, 1);
      bulb.position.copy(at); add(bulb);
      const halo = glowSprite(lampColour, 2.6, 0.32);
      halo.position.copy(at); add(halo);
      const pool = glowSprite(lampColour, Math.min(width, height) * 1.25, 0.16);
      pool.position.set(at.x, at.y - 0.4, FRONT - DEPTH + 0.05); add(pool);
      this.lamps.push(bulb, halo, pool);
    }
  }
  // a cut-out standing in this room: its brightness follows the room's light
  holds(piece) {
    const material = piece.front.material;
    material.userData.baseGlow ??= material.emissiveIntensity;
    material.userData.baseColour ??= material.color.clone();
    this.pieces.push(piece);
    return piece;
  }
  setLevel(level) {
    this.level = level;
    for (const m of this.materials) m.emissiveIntensity = m.userData.glow * level;
    for (const lamp of this.lamps) { lamp.visible = level > 0.02; lamp.material.opacity = lamp.userData.baseOpacity * level; }
    // in a dark room a cut-out goes dark too, paper edge and all (no moonlight indoors)
    const keep = 0.02 + 0.98 * level;
    for (const piece of this.pieces) {
      const m = piece.front.material;
      m.emissiveIntensity = m.userData.baseGlow * keep;
      m.color.copy(m.userData.baseColour).multiplyScalar(0.05 + 0.95 * level);
    }
  }
}

// ------------------------------------------------------------------------- the whole house
function box(width, height, depth, material) {
  return new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
}
// an outside surface: lit by the moon, with a little warm spill from the lit rooms
function solid(map, colour = 0xffffff, { spill = 0x2a1c14, spillShare = 0.5 } = {}) {
  return new THREE.MeshLambertMaterial({ map, color: colour, emissive: spill, emissiveMap: map, emissiveIntensity: spillShare });
}

export async function buildHouse(kit) {
  const scene = kit.scene;
  const brick = texture(surface('brick'), 2, 2);
  const brickMaterial = solid(brick, 0xe6cfc0, { spill: 0x6a4434, spillShare: 0.55 });
  const slabMaterial = solid(texture(surface('plaster'), 6, 0.3), 0xc4b8a8, { spill: 0x5a4a3a, spillShare: 0.45 });
  const slateMaterial = solid(texture(surface('slate'), 3, 2), 0xb4c2d0, { spill: 0x3a4652, spillShare: 0.5 });
  const earthMaterial = new THREE.MeshLambertMaterial({ map: texture(surface('earth'), 4, 3), color: 0xa89484, emissive: 0x3a2c22, emissiveIntensity: 0.35 });

  // the sky and the town behind: a cloudy painting, darkened to night
  const sky = await wallPicture('glasgow-square', { top: 0, width: 1, height: 0.92 });
  const skyPlane = plane(44, 40, new THREE.MeshBasicMaterial({ map: sky, color: 0x6c7c9c, fog: false }));
  skyPlane.position.set(0, 13, -26);
  scene.add(skyPlane);

  // the earth the cellar is dug into, and the ground either side of the house
  const earthBack = plane(40, 10, earthMaterial);
  earthBack.position.set(0, STREET - 5.01, FRONT - DEPTH - 0.4);
  scene.add(earthBack);
  for (const side of [-1, 1]) {
    const bank = box(10, 10, DEPTH + 0.8, earthMaterial);
    bank.position.set(side * (RIGHT + WALL + 5), STREET - 5, FRONT - DEPTH / 2 + 0.1);
    scene.add(bank);
  }
  const groundBeyond = box(40, 0.3, 12, new THREE.MeshLambertMaterial({ map: texture(surface('pavement'), 8, 3), color: 0x6c6f74 }));
  groundBeyond.position.set(0, STREET - 0.15, FRONT - DEPTH - 6.4);
  scene.add(groundBeyond);
  const below = box(9.4, 1.2, DEPTH + 0.8, earthMaterial);
  below.position.set(0, FLOORS.cellar.bottom - 0.6, FRONT - DEPTH / 2 + 0.1);
  scene.add(below);

  // outer walls and the slabs between storeys (their cut edges face the camera)
  for (const side of [-1, 1]) {
    const wall = box(WALL, EAVES - FLOORS.cellar.bottom + 0.3, DEPTH + 0.2, brickMaterial);
    wall.position.set(side * (RIGHT + WALL / 2), (EAVES + FLOORS.cellar.bottom - 0.3) / 2, FRONT - DEPTH / 2 - 0.1);
    scene.add(wall);
  }
  const slab = (yBottom, yTop, material = slabMaterial) => {
    const s = box(RIGHT - LEFT, yTop - yBottom, DEPTH + 0.2, material);   // between the outer walls (no overlapping faces)
    s.position.set(0, (yBottom + yTop) / 2, FRONT - DEPTH / 2 - 0.1);
    scene.add(s);
    return s;
  };
  slab(FLOORS.cellar.top, FLOORS.ground.bottom, brickMaterial);
  slab(FLOORS.ground.top, FLOORS.middle.bottom);
  slab(FLOORS.middle.top, FLOORS.top.bottom);
  slab(FLOORS.top.top, EAVES);
  for (const storey of ['top', 'ground']) {
    const f = FLOORS[storey];
    const divide = box(0.3, f.top - f.bottom, DEPTH, brickMaterial);
    divide.position.set(DIVIDE, (f.top + f.bottom) / 2, FRONT - DEPTH / 2);
    scene.add(divide);
  }

  // the roof: a slate pitch with two chimney stacks
  const roofShape = new THREE.Shape();
  const half = RIGHT + WALL + 0.35;
  roofShape.moveTo(-half, 0); roofShape.lineTo(half, 0); roofShape.lineTo(0, RIDGE - EAVES); roofShape.lineTo(-half, 0);
  const roof = new THREE.Mesh(new THREE.ExtrudeGeometry(roofShape, { depth: DEPTH + 0.6, bevelEnabled: false }), slateMaterial);
  roof.position.set(0, EAVES, FRONT - DEPTH - 0.4);
  scene.add(roof);
  const chimneys = [];
  for (const x of [-2.7, 2.9]) {
    const height = 1.15;
    const stack = box(0.75, height, 0.75, brickMaterial);
    const roofAt = EAVES + (RIDGE - EAVES) * (1 - Math.abs(x) / half);
    stack.position.set(x, roofAt + height / 2 - 0.3, FRONT - DEPTH / 2 - 0.2);
    scene.add(stack);
    for (const dx of [-0.17, 0.17]) {
      const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.11, 0.35, 10), new THREE.MeshLambertMaterial({ color: 0x8a4e36 }));
      pot.position.set(x + dx, roofAt + height - 0.13, FRONT - DEPTH / 2 - 0.2);
      scene.add(pot);
    }
    chimneys.push([x, roofAt + height + 0.1, FRONT - DEPTH / 2 - 0.2]);
  }

  // the rooms
  const treasuryWall = await wallPicture('boardroom', { top: 1150, width: DIVIDE - 0.15 - LEFT, height: FLOORS.top.top - FLOORS.top.bottom });
  const factoryWall = await wallPicture('munitions-factory', { top: 300, width: DIVIDE - 0.15 - LEFT, height: FLOORS.ground.top - FLOORS.ground.bottom });
  const kitchenWall = await wallPicture('kitchen', { top: 520, width: RIGHT - DIVIDE - 0.15, height: FLOORS.ground.top - FLOORS.ground.bottom });
  const streetWall = await wallPicture('town-street', { top: 900, width: RIGHT - LEFT, height: FLOORS.middle.top - FLOORS.middle.bottom });
  const rooms = {
    treasury: new Room(scene, { name: 'treasury', x0: LEFT, x1: DIVIDE - 0.15, storey: 'top', back: { picture: treasuryWall }, sides: 'planks', sideTint: 0xb8946a, lamp: [0.3, 0.86] }),
    vault: new Room(scene, { name: 'vault', x0: DIVIDE + 0.15, x1: RIGHT, storey: 'top', back: { surface: 'stone', tint: 0xcfd8c8, glow: 0.7 }, floor: 'stone', sides: 'stone', sideTint: 0xb8c4b4, lamp: [0.5, 0.86], lampColour: 0xd8e2c0 }),
    site: new Room(scene, { name: 'site', x0: LEFT, x1: RIGHT, storey: 'middle', back: { picture: streetWall, glow: 0.8 }, floor: 'planks', sides: 'brick', sideTint: 0xc89a80, lamp: [0.36, 0.88] }),
    factory: new Room(scene, { name: 'factory', x0: LEFT, x1: DIVIDE - 0.15, storey: 'ground', back: { picture: factoryWall, glow: 0.9 }, floor: 'pavement', sides: 'brick', sideTint: 0xc0a090, lamp: [0.62, 0.88] }),
    kitchen: new Room(scene, { name: 'kitchen', x0: DIVIDE + 0.15, x1: RIGHT, storey: 'ground', back: { picture: kitchenWall }, sides: 'plaster', lamp: [0.42, 0.88], lampColour: 0xffb560 }),
    mine: new Room(scene, { name: 'mine', x0: LEFT, x1: RIGHT, storey: 'cellar', back: { surface: 'rock', tint: 0xffc890, glow: 0.95 }, floor: 'earth', sides: 'rock', sideTint: 0xffc890, lamp: null }),
  };
  // the school's own lamp (it keeps half its light after the cuts)
  rooms.site.schoolLamp = glowSprite(0xffd28a, 2.2, 0.35);
  rooms.site.schoolLamp.position.set(2.6, FLOORS.middle.top - 0.5, FRONT - 1.6);
  scene.add(rooms.site.schoolLamp);

  // the mine's ceiling can come down (the pressure): a block of rock whose underside moves down, with
  // timber props under it; both brighten and darken with the mine's light
  const rockMaterial = new THREE.MeshLambertMaterial({ map: texture(surface('rock'), 3, 0.5), color: 0x8a786a, emissive: 0xd8a070, emissiveMap: texture(surface('rock'), 3, 0.5), emissiveIntensity: 0.8 });
  rockMaterial.userData.glow = 0.8;
  const mineCeiling = box(RIGHT - LEFT - 0.01, 1, DEPTH - 0.01, rockMaterial);
  scene.add(mineCeiling);
  const timber = new THREE.MeshLambertMaterial({ color: 0x6b4a2e, emissive: 0x3a2412, emissiveIntensity: 0.7 });
  timber.userData.glow = 0.7;
  const props = [-3.4, -1.1, 1.2, 3.5].map((x) => {
    const post = box(0.16, 1, 0.16, timber);
    post.userData.x = x;
    scene.add(post);
    const cap = box(0.9, 0.12, 0.2, timber);
    scene.add(cap);
    return { post, cap, x };
  });
  const setMineCeiling = (top) => {
    const underside = top - 0.3, above = FLOORS.cellar.top;
    mineCeiling.scale.y = above - underside; mineCeiling.position.set(0, (above + underside) / 2, FRONT - DEPTH / 2);
    const height = underside - FLOORS.cellar.bottom;
    for (const p of props) {
      p.post.scale.y = height; p.post.position.set(p.x, FLOORS.cellar.bottom + height / 2, FRONT - 0.7);
      p.cap.position.set(p.x, underside - 0.06, FRONT - 0.7);
    }
  };
  setMineCeiling(FLOORS.cellar.top);
  rooms.mine.materials.push(rockMaterial, timber);

  // the pavement in front (where people stand when they walk out), with a gas lamp and its pool of light
  const pavementMap = texture(surface('pavement'), 6, 1.1);
  const pavement = box(14, 0.15, 2.6, new THREE.MeshLambertMaterial({ map: pavementMap, color: 0xb4b8be, emissive: 0x6a5238, emissiveMap: pavementMap, emissiveIntensity: 0.45 }));
  pavement.position.set(0, STREET - 0.075, FRONT + 1.3);
  scene.add(pavement);
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 3.0, 8), new THREE.MeshLambertMaterial({ color: 0x1e2428 }));
  post.position.set(-3.9, STREET + 1.5, FRONT + 2.1);
  scene.add(post);
  const lantern = glowSprite(0xffcf8a, 0.7, 1); lantern.position.set(-3.9, STREET + 3.05, FRONT + 2.1); scene.add(lantern);
  const lanternHalo = glowSprite(0xffb867, 3.2, 0.35); lanternHalo.position.copy(lantern.position); scene.add(lanternHalo);
  const pool = new THREE.Mesh(new THREE.PlaneGeometry(6, 2.6), new THREE.MeshBasicMaterial({ map: glowSprite().material.map, color: 0xffb867, transparent: true, opacity: 0.4, blending: THREE.AdditiveBlending, depthWrite: false }));
  pool.rotation.x = -Math.PI / 2; pool.position.set(-2.6, STREET + 0.01, FRONT + 1.4);
  scene.add(pool);

  return { rooms, chimneys, setMineCeiling, lantern: [lantern, lanternHalo] };
}

// ------------------------------------------------------------------------- snow
// Flakes falling in front of the house; where each flake is depends only on the moment t.
export class Snow {
  constructor(scene, { count = 520, min = [-5.5, 0, 0.3], max = [5.5, 17.5, 7], size = 0.13, seed = 31 } = {}) {
    const random = seededRandom(seed);
    this.flakes = Array.from({ length: count }, () => [lerp(min[0], max[0], random()), random(), lerp(min[2], max[2], random()), 0.5 + random() * 0.6, random() * 6.28]);
    this.min = min; this.max = max;
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 32;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.5, 'rgba(255,255,255,0.6)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 32, 32);
    this.material = new THREE.PointsMaterial({ map: canvasTexture(canvas), size, sizeAttenuation: true, transparent: true, depthWrite: false, color: 0xe8eef6, opacity: 0 });
    this.points = new THREE.Points(this.geometry, this.material);
    this.points.frustumCulled = false;
    scene.add(this.points);
  }
  set(t, opacity) {
    this.points.visible = opacity > 0.01;
    if (!this.points.visible) return;
    this.material.opacity = opacity;
    const span = this.max[1] - this.min[1];
    const positions = this.geometry.attributes.position.array;
    this.flakes.forEach(([x, start, z, speed, phase], i) => {
      const fallen = (start * span + t * 0.9 * speed) % span;
      positions[i * 3] = x + 0.25 * Math.sin(t * 0.8 * speed + phase);
      positions[i * 3 + 1] = this.max[1] - fallen;
      positions[i * 3 + 2] = z;
    });
    this.geometry.attributes.position.needsUpdate = true;
  }
}

// ------------------------------------------------------------------------- dust shaken from a ceiling
// Specks that fall from a ceiling (a strip from x0 to x1 at height y, between z0 and z1) after a jolt
// at time `at`, speeding up as they fall and fading; where each speck is depends only on t.
export class FallingDust {
  constructor(scene, { x0, x1, y, z0 = -2.2, z1 = -0.4, count = 140, size = 0.06, seed = 51 } = {}) {
    const random = seededRandom(seed);
    this.specks = Array.from({ length: count }, () => [lerp(x0, x1, random()), lerp(z0, z1, random()), random() * 0.5, 0.7 + random() * 0.6]);
    this.y = y;
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 32;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.6, 'rgba(255,255,255,0.4)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 32, 32);
    this.material = new THREE.PointsMaterial({ map: canvasTexture(canvas), size, sizeAttenuation: true, transparent: true, depthWrite: false, color: 0xd8c8a8, opacity: 0 });
    this.points = new THREE.Points(this.geometry, this.material);
    this.points.frustumCulled = false;
    scene.add(this.points);
  }
  set(t, at, floorBelow) {
    const age = t - at;
    this.points.visible = age > 0 && age < 2.4;
    if (!this.points.visible) return;
    this.material.opacity = 0.85 * Math.min(1, age / 0.15) * (1 - Math.max(0, (age - 1.4) / 1.0));
    const positions = this.geometry.attributes.position.array;
    this.specks.forEach(([x, z, delay, weight], i) => {
      const a = Math.max(0, age - delay);
      positions[i * 3] = x + 0.04 * Math.sin(a * 5 + i);
      positions[i * 3 + 1] = Math.max(floorBelow, this.y - 0.5 * 2.2 * weight * a * a);
      positions[i * 3 + 2] = z;
    });
    this.geometry.attributes.position.needsUpdate = true;
  }
}
