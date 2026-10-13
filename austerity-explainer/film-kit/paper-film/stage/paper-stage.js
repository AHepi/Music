// What this does: the paper stage. Every picture in the film is a piece of paper in a small 3D
// world, lit by one soft lamp from the upper left, filmed by one camera. Nothing is drawn by hand
// and no hand ever appears: pieces fold up from flat like a pop-up book, slide in, drop in from
// above, fold back down, and whole pages turn like the pages of a book.
//
// How the pieces fit:
//   - a Page is one painting printed on a sheet the size of the screen (a bit bigger, so the
//     camera can drift). It can turn over to the left, bending as it goes, like a book page.
//   - a Piece is a cut-out (figure, object or word) that stands a little in front of its page,
//     hinged along its bottom edge. Its "fold" is how far it has folded down toward the camera:
//     0 = standing up, a quarter turn (Math.PI / 2) = lying flat.
//   - words, printed cards, signs and posters are made here from text (no painting needed); dust
//     bursts where heavy things land, and smoke rises from chimneys.
//   - each picture file is loaded once, however many pieces or pages use it.
//   - the scene file (scenes/...) creates pages and pieces and says, for any moment, where each
//     one is. This file only builds the world and draws a frame for a given moment.
//
// The page calls window.renderFrame(seconds) and gets back one finished frame as a JPEG.

import * as THREE from '/paper-film/node_modules/three/build/three.module.js';

export const FRAME_WIDTH = 1080;
export const FRAME_HEIGHT = 1920;
export const PAGE_WIDTH = 10.4;
export const PAGE_HEIGHT = 18.5;
export const PAGE_CENTRE_Y = 8.0;
const PAPER_BACK_COLOUR = new THREE.Color(0xd9d2c3);

export const renderer = new THREE.WebGLRenderer({
  canvas: document.getElementById('stage'), antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance',
});
renderer.setPixelRatio(1);
renderer.setSize(FRAME_WIDTH, FRAME_HEIGHT, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap; // soft edges come from shadow.radius below
renderer.setClearColor(0x101418, 1);

export const scene = new THREE.Scene();
export const camera = new THREE.PerspectiveCamera(2 * Math.atan(8 / 26) * 180 / Math.PI, FRAME_WIDTH / FRAME_HEIGHT, 0.5, 200);

// One soft lamp, upper left and in front; a broad fill so the paintings keep their own colours.
const ambient = new THREE.AmbientLight(0xffffff, 1.0);
scene.add(ambient);
const lamp = new THREE.DirectionalLight(0xfff4e6, 1.0);
lamp.castShadow = true;
lamp.shadow.mapSize.set(1536, 1536);
lamp.shadow.camera.left = -14; lamp.shadow.camera.right = 14;
lamp.shadow.camera.top = 14; lamp.shadow.camera.bottom = -14;
lamp.shadow.camera.near = 1; lamp.shadow.camera.far = 90;
lamp.shadow.radius = 5;
lamp.shadow.bias = -0.0006;
lamp.shadow.normalBias = 0.01;
const lampTarget = new THREE.Object3D();
lampTarget.position.set(0, PAGE_CENTRE_Y, 0);
scene.add(lampTarget);
lamp.target = lampTarget;
const LAMP_DIRECTION = new THREE.Vector3(-0.42, 0.52, 0.74).normalize();
lamp.position.copy(lampTarget.position).addScaledVector(LAMP_DIRECTION, 40);
scene.add(lamp);

// Light levels: chosen so a piece facing the camera shows its painting at its own brightness
// (ambient + lamp = 1), and tilting a piece away from the lamp darkens it, as paper does.
export function setLightLevels({ ambientShare = 0.52, lampShare = 0.48 } = {}) {
  const facing = LAMP_DIRECTION.z; // how directly the lamp hits a piece that faces the camera
  ambient.intensity = Math.PI * ambientShare;
  lamp.intensity = Math.PI * lampShare / facing;
}
setLightLevels();

const loader = new THREE.TextureLoader();
const loadedTextures = new Map(); // one copy of each picture, however many pieces use it
export function loadTexture(url) {
  if (!loadedTextures.has(url)) {
    loadedTextures.set(url, loader.loadAsync(url).then((texture) => {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
      texture.generateMipmaps = true;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      return texture;
    }));
  }
  return loadedTextures.get(url);
}

function canvasTexture(canvas) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}

function paperBackMaterial(map) {
  // the plain back of a cut-out: paper colour, the same outline as the front
  const material = new THREE.MeshLambertMaterial({ map, alphaTest: 0.5, alphaToCoverage: true, side: THREE.BackSide, shadowSide: THREE.DoubleSide });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.paperBack = { value: PAPER_BACK_COLOUR };
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 paperBack;')
      .replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb = paperBack;');
  };
  return material;
}

// ------------------------------------------------------------------------------------------ pages
// A page turns by peeling: its bottom-right corner lifts toward the camera and rolls over a
// cylinder of paper that sweeps up and to the left, the turned part lying back over the page
// (showing the plain back) until it has left the frame, uncovering the next page underneath.
const CURL_DIRECTION = new THREE.Vector2(0.93, -0.36).normalize(); // from the fold toward the lifting corner
const CURL_RADIUS = 0.75;
const PAGE_COLUMNS = 60, PAGE_ROWS = 106;

export class Page {
  constructor(texture, { z = 0 }) {
    this.z = z;
    this.spineX = -PAGE_WIDTH / 2;
    this.geometry = new THREE.PlaneGeometry(PAGE_WIDTH, PAGE_HEIGHT, PAGE_COLUMNS, PAGE_ROWS);
    this.restPositions = this.geometry.attributes.position.array.slice();
    this.front = new THREE.Mesh(this.geometry, new THREE.MeshLambertMaterial({ map: texture, side: THREE.FrontSide, shadowSide: THREE.DoubleSide }));
    this.back = new THREE.Mesh(this.geometry, new THREE.MeshLambertMaterial({ color: PAPER_BACK_COLOUR, side: THREE.BackSide, shadowSide: THREE.DoubleSide }));
    for (const mesh of [this.front, this.back]) { mesh.receiveShadow = true; mesh.castShadow = true; scene.add(mesh); }
    this.pieces = [];
    const corners = [[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([a, b]) => CURL_DIRECTION.x * a * PAGE_WIDTH / 2 + CURL_DIRECTION.y * b * PAGE_HEIGHT / 2);
    this.foldStart = Math.max(...corners) + 0.02;
    this.foldEnd = Math.min(...corners) - 0.3;
    this.turn = -1;
    this.setTurn(0);
  }
  static async create(url, options = {}) { return new Page(await loadTexture(url), options); }

  // Pieces only stand on a page while it lies open, so they always use the flat page.
  frameAt(s) { return { x: this.spineX + s, z: this.z, angle: 0 }; }

  // turn: 0 = lying open, 1 = turned away completely
  setTurn(turn) {
    turn = Math.min(1, Math.max(0, turn));
    if (turn === this.turn) return;
    this.turn = turn;
    const eased = turn < 0.5 ? 2 * turn * turn : 1 - (-2 * turn + 2) ** 2 / 2;
    const fold = this.foldStart + (this.foldEnd - this.foldStart) * eased;
    const positions = this.geometry.attributes.position.array;
    const nx = CURL_DIRECTION.x, ny = CURL_DIRECTION.y, r = CURL_RADIUS;
    for (let i = 0; i < positions.length / 3; i++) {
      const x = this.restPositions[i * 3], y = this.restPositions[i * 3 + 1];
      const u = x * nx + y * ny - fold;      // how far past the fold line this point is
      let along = 0, height = 0;
      if (u > 0 && u < Math.PI * r) { const a = u / r; along = r * Math.sin(a) - u; height = r * (1 - Math.cos(a)); }
      else if (u >= Math.PI * r) { along = -(u - Math.PI * r) - u; height = 2 * r; }
      positions[i * 3] = x + along * nx;
      positions[i * 3 + 1] = y + along * ny + PAGE_CENTRE_Y;
      positions[i * 3 + 2] = this.z + height;
    }
    this.geometry.attributes.position.needsUpdate = true;
    this.geometry.computeVertexNormals();
    this.geometry.computeBoundingSphere();
  }
  setVisible(visible) { this.front.visible = visible; this.back.visible = visible; }
}

// ----------------------------------------------------------------------------------------- pieces
export class Piece {
  // width in world units; x, y = where the middle of its bottom edge (the hinge) sits on the page;
  // z = how far in front of the page it stands.
  constructor(texture, { page, width, x = 0, y = 0, z = 0.5, yaw = 0, aspect = null }) {
    this.page = page; this.restX = x; this.restY = y; this.restZ = z; this.yaw = yaw;
    const imageAspect = aspect ?? (texture.image.height / texture.image.width);
    this.width = width; this.height = width * imageAspect;
    this.anchor = new THREE.Group();     // follows the page (and its turn)
    this.mover = new THREE.Group();      // slides, drops and bounces
    this.hinge = new THREE.Group();      // folds about the bottom edge
    this.anchor.add(this.mover); this.mover.add(this.hinge);
    const geometry = new THREE.PlaneGeometry(this.width, this.height);
    geometry.translate(0, this.height / 2, 0);
    this.front = new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({ map: texture, alphaTest: 0.5, alphaToCoverage: true, side: THREE.FrontSide, shadowSide: THREE.DoubleSide }));
    this.back = new THREE.Mesh(geometry, paperBackMaterial(texture));
    this.front.castShadow = true; this.front.receiveShadow = true;
    this.back.castShadow = false; this.back.receiveShadow = true;
    this.hinge.add(this.front, this.back);
    scene.add(this.anchor);
    page.pieces.push(this);
    this.layers = [];
  }
  static async create(url, options) { return new Piece(await loadTexture(url), options); }

  // An extra layer on the same hinge (used for the miner's jaw and mouth), at a small depth offset.
  async addLayer(url, depthOffset) {
    const texture = await loadTexture(url);
    const geometry = new THREE.PlaneGeometry(this.width, this.height);
    geometry.translate(0, this.height / 2, 0);
    const holder = new THREE.Group();
    const mesh = new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({ map: texture, alphaTest: 0.5, alphaToCoverage: true, side: THREE.FrontSide, shadowSide: THREE.DoubleSide }));
    mesh.receiveShadow = true;
    holder.position.z = depthOffset;
    holder.add(mesh);
    this.hinge.add(holder);
    this.layers.push(holder);
    return holder;
  }

  // Pose for one moment. fold: 0 standing, PI/2 flat toward the camera. dx, dy: offsets on the page.
  // roll: a turn in the page's plane (radians). lift: extra distance from the page.
  set({ visible = true, fold = 0, dx = 0, dy = 0, roll = 0, lift = 0 } = {}) {
    this.anchor.visible = visible;
    if (!visible) return;
    const s = this.restX + dx - this.page.spineX;
    const frame = this.page.frameAt(s);
    const depth = this.restZ + lift;
    // the page's front faces (-sin a, 0, cos a) at angle a
    this.anchor.position.set(frame.x - Math.sin(frame.angle) * depth, this.restY + dy, frame.z + Math.cos(frame.angle) * depth);
    this.anchor.rotation.set(0, -frame.angle + this.yaw, 0);
    this.mover.rotation.set(0, 0, roll);
    this.hinge.rotation.set(fold, 0, 0);
  }
}

// A word: plain letters cut out of card, no decoration, made from a text string.
export async function makeWordTexture(lines, { fontPx = 220, colour = '#f2ede3', lineGap = 0.98 } = {}) {
  const font = `800 ${fontPx}px Inter`;
  await document.fonts.load(font);
  const measure = document.createElement('canvas').getContext('2d');
  measure.font = font;
  const widths = lines.map((line) => measure.measureText(line).width);
  const pad = Math.round(fontPx * 0.12);
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(Math.max(...widths) + pad * 2);
  canvas.height = Math.ceil(fontPx * lineGap * lines.length + pad * 2 + fontPx * 0.12);
  const ctx = canvas.getContext('2d');
  ctx.font = font; ctx.fillStyle = colour; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'center';
  lines.forEach((line, i) => ctx.fillText(line, canvas.width / 2, pad + fontPx * 0.8 + i * fontPx * lineGap));
  return canvasTexture(canvas);
}

// A printed card or poster: plain words in dark ink on a card with slightly rounded corners and a
// thin ruled border just inside its edge. Used for the experts' advice cards, the SOLD sign and the
// wall posters. With no lines it is a plain board (the panels on page 7).
export async function makeCardTexture(lines, { fontPx = 150, cardColour = '#e8e0cc', inkColour = '#20262b', borderColour = 'rgba(32,38,43,0.55)',
  lineGap = 1.08, padX = 0.55, padY = 0.42, minWidth = 0, aspect = null } = {}) {
  const font = `800 ${fontPx}px Inter`;
  await document.fonts.load(font);
  const measure = document.createElement('canvas').getContext('2d');
  measure.font = font;
  const widest = lines.length ? Math.max(...lines.map((line) => measure.measureText(line).width)) : 0;
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(Math.max(minWidth, widest + fontPx * padX * 2));
  canvas.height = aspect ? Math.ceil(canvas.width * aspect) : Math.ceil(fontPx * lineGap * lines.length + fontPx * padY * 2);
  const ctx = canvas.getContext('2d');
  const corner = Math.min(canvas.width, canvas.height) * 0.06;
  ctx.fillStyle = cardColour;
  ctx.beginPath(); ctx.roundRect(0, 0, canvas.width, canvas.height, corner); ctx.fill();
  const inset = Math.min(canvas.width, canvas.height) * 0.05;
  ctx.strokeStyle = borderColour; ctx.lineWidth = Math.max(3, fontPx * 0.035);
  ctx.beginPath(); ctx.roundRect(inset, inset, canvas.width - 2 * inset, canvas.height - 2 * inset, corner * 0.6); ctx.stroke();
  ctx.font = font; ctx.fillStyle = inkColour; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  const blockHeight = fontPx * lineGap * (lines.length - 1) + fontPx * 0.72;
  const firstBaseline = (canvas.height - blockHeight) / 2 + fontPx * 0.72;
  lines.forEach((line, i) => ctx.fillText(line, canvas.width / 2, firstBaseline + i * fontPx * lineGap));
  return canvasTexture(canvas);
}

// A plain sheet of one colour, softly darker at the edges (the blank page at the very end).
export function makePlainTexture(colour, { width = 512, height = 910, edge = 'rgba(0,0,0,0.35)' } = {}) {
  const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = colour; ctx.fillRect(0, 0, width, height);
  const gradient = ctx.createRadialGradient(width / 2, height / 2, height * 0.25, width / 2, height / 2, height * 0.75);
  gradient.addColorStop(0, 'rgba(0,0,0,0)'); gradient.addColorStop(1, edge);
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, width, height);
  return canvasTexture(canvas);
}

// ------------------------------------------------------------------------------------------- dust
// Soft puffs that burst out where something heavy lands.
function dustTexture() {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
  gradient.addColorStop(0, 'rgba(120,112,100,0.9)'); gradient.addColorStop(0.5, 'rgba(105,98,88,0.45)'); gradient.addColorStop(1, 'rgba(90,85,78,0)');
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
  const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace; return texture;
}
export class DustBurst {
  constructor({ count = 26, seed = 7 }) {
    const texture = dustTexture();
    let state = seed;
    const random = () => { state = (state * 1664525 + 1013904223) % 4294967296; return state / 4294967296; };
    this.puffs = Array.from({ length: count }, () => {
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false, opacity: 0 }));
      sprite.visible = false; scene.add(sprite);
      return { sprite, across: random() * 2 - 1, rise: 0.4 + random() * 0.9, spread: 0.8 + random() * 1.6, size: 0.7 + random() * 0.9, delay: random() * 0.08, depth: random() };
    });
  }
  hide() { for (const puff of this.puffs) puff.sprite.visible = false; }
  // origin: centre of the landing line; width: how wide the landing line is; age: seconds since landing
  set({ origin, width, age }) {
    for (const puff of this.puffs) {
      const a = age - puff.delay;
      if (a < 0 || a > 1.1) { puff.sprite.visible = false; continue; }
      const k = 1 - Math.exp(-a * 4.5);
      puff.sprite.visible = true;
      puff.sprite.position.set(origin.x + puff.across * width * 0.5 + Math.sign(puff.across) * puff.spread * k,
        origin.y + puff.rise * k, origin.z + 0.1 + puff.depth * 0.5);
      const size = puff.size * (0.5 + 1.6 * k);
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.opacity = 0.55 * (1 - a / 1.1) ** 1.5;
    }
  }
}

// Smoke from a chimney: soft puffs that rise, drift and fade. Puffs are born only between `from`
// and `until`; when the smoke stops, the last puffs rise away and fade.
function smokeTexture() {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
  gradient.addColorStop(0, 'rgba(176,174,168,0.9)'); gradient.addColorStop(0.55, 'rgba(160,158,152,0.45)'); gradient.addColorStop(1, 'rgba(150,148,142,0)');
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
  return canvasTexture(canvas);
}
export class Smoke {
  constructor({ count = 9, life = 2.2, seed = 5 } = {}) {
    const texture = smokeTexture();
    let state = seed;
    const random = () => { state = (state * 1664525 + 1013904223) % 4294967296; return state / 4294967296; };
    this.life = life;
    this.puffs = Array.from({ length: count }, (_, i) => {
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false, opacity: 0 }));
      sprite.visible = false; scene.add(sprite);
      return { sprite, offset: (i / count) * life, sway: random() * Math.PI * 2, size: 0.8 + random() * 0.5 };
    });
  }
  hide() { for (const puff of this.puffs) puff.sprite.visible = false; }
  set({ t, origin, from, until, scale = 1 }) {
    for (const puff of this.puffs) {
      const born = puff.offset + Math.floor((t - puff.offset) / this.life) * this.life;
      const age = t - born;
      if (born < from || born > until || age < 0 || age > this.life) { puff.sprite.visible = false; continue; }
      const k = age / this.life;
      puff.sprite.visible = true;
      puff.sprite.position.set(origin.x + scale * (0.55 * k + 0.12 * Math.sin(puff.sway + age * 2.2)), origin.y + scale * 1.7 * k, origin.z + 0.05);
      const size = scale * puff.size * (0.35 + 1.1 * k);
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.opacity = 0.5 * Math.min(1, age / 0.25) * (1 - k);
    }
  }
}

// --------------------------------------------------------------------------------------- the frame
export function placeCamera({ x = 0, y = PAGE_CENTRE_Y, z = 26, lookX = 0, lookY = PAGE_CENTRE_Y }) {
  camera.position.set(x, y, z);
  camera.lookAt(lookX, lookY, 0);
}

export function drawFrame() {
  renderer.render(scene, camera);
  return renderer.domElement.toDataURL('image/jpeg', 0.95);
}
