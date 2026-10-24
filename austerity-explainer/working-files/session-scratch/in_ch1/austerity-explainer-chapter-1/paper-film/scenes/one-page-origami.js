// What this does: one still picture, "a blank page with origami props in lamplight".
// A single blank sheet of paper lies at an angle on a dark desk. Folded-paper props stand on it
// (a cottage, two trees, a crane and a zig-zag fence), built as real folded shapes with flat faces,
// so every fold catches the light differently. One low, warm lamp from the left throws long shadows
// across the page; a faint cool light from behind keeps the dark side from going black.
//
// It uses the paper stage's renderer and camera but switches the stage's own lamp off and brings
// its own lights. Draw it with: node paper-film/tools/draw-one-page-still.mjs one-page-origami OUT.png

import * as THREE from '/paper-film/node_modules/three/build/three.module.js';

// ------------------------------------------------------------------------------- small helpers
function seededRandom(seed) {
  let value = seed;
  return () => { value = (value * 16807) % 2147483647; return (value - 1) / 2147483646; };
}

// A folded-paper surface from a list of triangles. Each triangle keeps its own flat face, so the
// folds show as changes of shade, the way real folded paper looks.
function foldedPaper(triangles, colour, { roughness = 0.88 } = {}) {
  const positions = [];
  for (const triangle of triangles) for (const point of triangle) positions.push(...point);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({ color: colour, roughness, metalness: 0, side: THREE.DoubleSide, flatShading: true, shadowSide: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}

// two triangles for a four-cornered face (corners in order around the edge)
const square = (a, b, c, d) => [[a, b, c], [a, c, d]];

// a sheet of paper texture: warm off-white with faint fibres and a slightly uneven tone
function paperTexture(renderer, { width = 1024, height = 1448, tone = [236, 228, 212], seed = 11 } = {}) {
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const context = canvas.getContext('2d');
  context.fillStyle = `rgb(${tone.join(',')})`;
  context.fillRect(0, 0, width, height);
  const random = seededRandom(seed);
  const image = context.getImageData(0, 0, width, height);
  for (let index = 0; index < image.data.length; index += 4) {
    const grain = (random() - 0.5) * 9;
    image.data[index] += grain; image.data[index + 1] += grain; image.data[index + 2] += grain;
  }
  context.putImageData(image, 0, 0);
  context.globalAlpha = 0.05;
  for (let fibre = 0; fibre < 2600; fibre += 1) {
    const x = random() * width, y = random() * height, angle = random() * Math.PI, length = 6 + random() * 22;
    context.strokeStyle = random() < 0.5 ? '#ffffff' : '#8a7a62';
    context.lineWidth = 0.6 + random() * 0.8;
    context.beginPath();
    context.moveTo(x, y);
    context.lineTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length);
    context.stroke();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}

// a dark wooden desk: long grain lines on deep brown
function deskTexture(renderer, { size = 1024, seed = 23 } = {}) {
  const canvas = document.createElement('canvas');
  canvas.width = size; canvas.height = size;
  const context = canvas.getContext('2d');
  context.fillStyle = '#2a1c13';
  context.fillRect(0, 0, size, size);
  const random = seededRandom(seed);
  for (let line = 0; line < 420; line += 1) {
    const y = random() * size;
    const shade = random() < 0.5 ? `rgba(70,46,30,${0.15 + random() * 0.25})` : `rgba(14,9,6,${0.15 + random() * 0.3})`;
    context.strokeStyle = shade;
    context.lineWidth = 0.6 + random() * 2.6;
    context.beginPath();
    const wave = random() * 6, phase = random() * 6.28;
    for (let x = 0; x <= size; x += 16) context.lineTo(x, y + Math.sin(x / 140 + phase) * wave);
    context.stroke();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(3, 3);
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}

// ------------------------------------------------------------------------------------ the page
// A blank sheet (A4 shape) lying flat, with its bottom-right corner lifting in a soft curl.
const SHEET_WIDTH = 8.0;
const SHEET_LENGTH = SHEET_WIDTH * Math.SQRT2;

function blankSheet(renderer) {
  const geometry = new THREE.PlaneGeometry(SHEET_WIDTH, SHEET_LENGTH, 80, 113);
  geometry.rotateX(-Math.PI / 2); // lie flat: x across, z toward the viewer
  const position = geometry.attributes.position;
  const cornerX = SHEET_WIDTH / 2, cornerZ = SHEET_LENGTH / 2;
  for (let index = 0; index < position.count; index += 1) {
    const x = position.getX(index), z = position.getZ(index);
    // distance past a diagonal line near the corner: paper beyond it rolls gently upward
    const past = ((x - cornerX) + (z - cornerZ)) / Math.SQRT2 + 1.9;
    if (past > 0) {
      const radius = 2.2;
      const angle = past / radius;
      const lift = radius * (1 - Math.cos(angle));
      const pullBack = past - radius * Math.sin(angle);
      position.setY(index, lift);
      position.setX(index, x - pullBack / Math.SQRT2);
      position.setZ(index, z - pullBack / Math.SQRT2);
    }
  }
  geometry.computeVertexNormals();
  const front = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ map: paperTexture(renderer), roughness: 0.95, side: THREE.FrontSide, shadowSide: THREE.DoubleSide }));
  const back = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0xcfc4ae, roughness: 0.95, side: THREE.BackSide, shadowSide: THREE.DoubleSide }));
  const sheet = new THREE.Group();
  for (const mesh of [front, back]) { mesh.castShadow = true; mesh.receiveShadow = true; sheet.add(mesh); }
  sheet.position.y = 0.012; // just above the desk
  return sheet;
}

// ---------------------------------------------------------------------------- the folded props
// Each prop is built standing on the ground (y = 0) around its own middle, then placed on the page.

function cottage() {
  const group = new THREE.Group();
  const halfWidth = 0.85, halfDepth = 0.6, wallHeight = 0.95, peak = 1.62, overhang = 0.14;
  const walls = [
    ...square([-halfWidth, 0, halfDepth], [halfWidth, 0, halfDepth], [halfWidth, wallHeight, halfDepth], [-halfWidth, wallHeight, halfDepth]),
    ...square([halfWidth, 0, -halfDepth], [-halfWidth, 0, -halfDepth], [-halfWidth, wallHeight, -halfDepth], [halfWidth, wallHeight, -halfDepth]),
    // gable ends: a wall with a triangle on top, folded from one piece
    ...square([halfWidth, 0, halfDepth], [halfWidth, 0, -halfDepth], [halfWidth, wallHeight, -halfDepth], [halfWidth, wallHeight, halfDepth]),
    [[halfWidth, wallHeight, halfDepth], [halfWidth, wallHeight, -halfDepth], [halfWidth, peak, 0]],
    ...square([-halfWidth, 0, -halfDepth], [-halfWidth, 0, halfDepth], [-halfWidth, wallHeight, halfDepth], [-halfWidth, wallHeight, -halfDepth]),
    [[-halfWidth, wallHeight, -halfDepth], [-halfWidth, wallHeight, halfDepth], [-halfWidth, peak, 0]],
  ];
  group.add(foldedPaper(walls, 0xf1e9d8));
  // the roof: one sheet folded along the ridge, hanging over the walls a little
  const eaveY = wallHeight - overhang * (peak - wallHeight) / halfDepth;
  const roofEnd = halfWidth + overhang;
  const roof = [
    ...square([-roofEnd, eaveY, halfDepth + overhang], [roofEnd, eaveY, halfDepth + overhang], [roofEnd, peak + 0.01, 0], [-roofEnd, peak + 0.01, 0]),
    ...square([roofEnd, eaveY, -halfDepth - overhang], [-roofEnd, eaveY, -halfDepth - overhang], [-roofEnd, peak + 0.01, 0], [roofEnd, peak + 0.01, 0]),
  ];
  group.add(foldedPaper(roof, 0xa4553f));
  // a door: a small flap of darker paper, folded slightly open
  const door = foldedPaper(square([0, 0, 0], [0.3, 0, 0], [0.3, 0.52, 0], [0, 0.52, 0]), 0x6f3f2a);
  door.position.set(-0.15, 0.002, halfDepth + 0.006);
  group.add(door);
  // a little window: a square of pale paper with a cross fold
  const windowPane = foldedPaper([
    ...square([0, 0, 0], [0.13, 0, 0.01], [0.13, 0.13, 0], [0, 0.13, 0.01]),
    ...square([0.13, 0, 0.01], [0.26, 0, 0], [0.26, 0.13, 0.01], [0.13, 0.13, 0]),
    ...square([0, 0.13, 0.01], [0.13, 0.13, 0], [0.13, 0.26, 0.01], [0, 0.26, 0]),
    ...square([0.13, 0.13, 0], [0.26, 0.13, 0.01], [0.26, 0.26, 0], [0.13, 0.26, 0.01]),
  ], 0xe8c27a);
  windowPane.position.set(0.33, 0.45, halfDepth + 0.008);
  group.add(windowPane);
  return group;
}

// A tree folded from three star-shaped tiers: each tier's edge goes in and out, so half its faces
// turn toward the lamp and half away, like the pleats of folded paper.
function tree({ height = 2.2, width = 0.75, colour = 0x6f8a5c, points = 6 } = {}) {
  const group = new THREE.Group();
  const trunk = foldedPaper([
    ...square([-0.07, 0, 0.07], [0.07, 0, 0.07], [0.07, 0.42, 0.07], [-0.07, 0.42, 0.07]),
    ...square([0.07, 0, 0.07], [0.07, 0, -0.07], [0.07, 0.42, -0.07], [0.07, 0.42, 0.07]),
    ...square([0.07, 0, -0.07], [-0.07, 0, -0.07], [-0.07, 0.42, -0.07], [0.07, 0.42, -0.07]),
    ...square([-0.07, 0, -0.07], [-0.07, 0, 0.07], [-0.07, 0.42, 0.07], [-0.07, 0.42, -0.07]),
  ], 0x7a5134);
  group.add(trunk);
  const tiers = [[0.32, 1.0, 1.0], [0.78, 0.8, 0.78], [1.2, 0.6, 0.56]];
  for (const [baseShare, sizeShare, tipShare] of tiers) {
    const baseY = height * baseShare * 0.62, tipY = baseY + height * 0.42 * tipShare + 0.25;
    const outer = width * sizeShare, inner = outer * 0.62;
    const triangles = [];
    const corners = [];
    for (let step = 0; step < points * 2; step += 1) {
      const angle = (step / (points * 2)) * Math.PI * 2 + 0.3;
      const radius = step % 2 === 0 ? outer : inner;
      corners.push([Math.cos(angle) * radius, baseY + (step % 2 === 0 ? -0.04 : 0.06), Math.sin(angle) * radius]);
    }
    for (let step = 0; step < corners.length; step += 1) triangles.push([corners[step], corners[(step + 1) % corners.length], [0, tipY, 0]]);
    group.add(foldedPaper(triangles, colour));
  }
  return group;
}

// The classic paper crane, facing along +x and seen from the side: a diamond body, a thin neck
// rising at the front with the head folded down at its tip, a thin tail rising at the back, and two
// wings raised above the body, each folded once along its length.
function crane() {
  const front = [0.36, 0.26, 0], back = [-0.36, 0.26, 0], top = [0, 0.48, 0], keel = [0, 0.02, 0];
  const left = [0, 0.27, 0.15], right = [0, 0.27, -0.15];
  const body = [
    [front, top, left], [top, back, left], [back, keel, left], [keel, front, left],
    [top, front, right], [back, top, right], [keel, back, right], [front, keel, right],
  ];
  // neck and tail: narrow folded points, each two faces meeting along a centre crease
  const point = (baseLow, baseHigh, tip) => [
    [baseLow, [baseHigh[0], baseHigh[1], 0.03], tip], [[baseHigh[0], baseHigh[1], -0.03], baseLow, tip],
    [[baseHigh[0], baseHigh[1], 0.03], [baseHigh[0], baseHigh[1], -0.03], tip],
  ];
  const neckTip = [0.86, 1.3, 0];
  const neck = point([0.14, 0.18, 0], [0.34, 0.28, 0], neckTip);
  const head = [[neckTip, [0.8, 1.26, 0.025], [1.02, 1.16, 0]], [[0.8, 1.26, -0.025], neckTip, [1.02, 1.16, 0]]];
  const tail = point([-0.14, 0.18, 0], [-0.34, 0.28, 0], [-0.9, 1.3, 0]);
  const wing = (side) => {
    const rootFront = [0.22, 0.46, 0.02 * side], rootBack = [-0.24, 0.46, 0.02 * side];
    const tip = [-0.12, 1.42, 0.5 * side], crease = [0.02, 0.92, 0.2 * side];
    return [[rootFront, crease, rootBack], [rootFront, tip, crease], [crease, tip, rootBack]];
  };
  const group = new THREE.Group();
  group.add(foldedPaper([...body, ...neck, ...head, ...tail, ...wing(1), ...wing(-1)], 0xf6f1e6));
  return group;
}

// A fence folded like a paper fan: a long strip pleated back and forth, standing on its edge.
function zigzagFence({ pleats = 14, pleatWidth = 0.2, height = 0.36, depth = 0.07, colour = 0xc89a55 } = {}) {
  const triangles = [];
  for (let pleat = 0; pleat < pleats; pleat += 1) {
    const x0 = pleat * pleatWidth, x1 = x0 + pleatWidth;
    const z0 = pleat % 2 === 0 ? 0 : depth, z1 = pleat % 2 === 0 ? depth : 0;
    triangles.push(...square([x0, 0, z0], [x1, 0, z1], [x1, height, z1], [x0, height, z0]));
  }
  const fence = foldedPaper(triangles, colour);
  fence.position.x = -pleats * pleatWidth / 2;
  const group = new THREE.Group();
  group.add(fence);
  return group;
}

// ---------------------------------------------------------------------------------- the scene
export async function build(stage) {
  const { renderer, scene, camera } = stage;

  // switch off the stage's own lamp and fill; this picture brings its own lights
  scene.traverse((object) => { if (object.isLight) object.visible = false; });
  renderer.setPixelRatio(2); // drawn at twice the size, then shrunk, for smooth edges
  renderer.setSize(stage.FRAME_WIDTH, stage.FRAME_HEIGHT, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.setClearColor(0x0c0907, 1);

  const world = new THREE.Group();
  scene.add(world);

  const desk = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ map: deskTexture(renderer), roughness: 0.7 }));
  desk.rotation.x = -Math.PI / 2;
  desk.receiveShadow = true;
  world.add(desk);

  // the page, turned at an angle on the desk; the props stand on it and turn with it
  const page = new THREE.Group();
  page.rotation.y = 0.28;
  world.add(page);
  page.add(blankSheet(renderer));

  const place = (prop, x, z, turn = 0, scale = 1) => {
    prop.position.set(x, 0.014, z);
    prop.rotation.y = turn;
    prop.scale.setScalar(scale);
    page.add(prop);
    return prop;
  };
  place(cottage(), 0.9, -1.9, -0.35);
  place(tree({ height: 2.5, width: 0.8, colour: 0x87a26f }), -1.55, -3.1, 0.2);
  place(tree({ height: 1.8, width: 0.6, colour: 0x7c9866 }), 2.75, -3.5, 0.9);
  place(tree({ height: 1.4, width: 0.5, colour: 0x93ad78 }), -2.6, -1.4, 0.5);
  place(crane(), -0.8, 2.9, -0.36, 1.85);
  place(zigzagFence(), 0.7, -0.05, -0.12);

  // lights: one low warm lamp from the left (long shadows), a faint cool sky fill, a cool rim
  const sky = new THREE.HemisphereLight(0x5d6f92, 0x2a1c12, 0.4);
  scene.add(sky);
  const lamp = new THREE.SpotLight(0xffc48a, 4.2, 0, 0.47, 0.9, 0);
  lamp.position.set(-11.5, 6.0, 4.8);
  lamp.target.position.set(0.6, 0, 0.3);
  lamp.castShadow = true;
  lamp.shadow.mapSize.set(4096, 4096);
  lamp.shadow.camera.near = 4; lamp.shadow.camera.far = 30;
  lamp.shadow.radius = 3;
  lamp.shadow.bias = -0.0012;
  lamp.shadow.normalBias = 0; // folded faces point either way, so no push along the face (it pushed trees into their own shadow)
  scene.add(lamp, lamp.target);
  const rim = new THREE.DirectionalLight(0x8fb0ff, 0.45);
  rim.position.set(7, 6, -10);
  scene.add(rim);

  camera.fov = 32;
  camera.aspect = stage.FRAME_WIDTH / stage.FRAME_HEIGHT;
  camera.near = 0.5; camera.far = 120;
  camera.updateProjectionMatrix();

  return {
    start: 0,
    end: 1,
    pose() {
      camera.position.set(1.0, 18.0, 21.0);
      camera.lookAt(-0.25, 0, 0.55);
    },
  };
}
