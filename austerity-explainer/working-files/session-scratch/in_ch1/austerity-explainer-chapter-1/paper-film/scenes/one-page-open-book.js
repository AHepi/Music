// What this does: one still picture, "an open pop-up book in lamplight".
// An open book floats in darkness, seen from the chair of someone reading it. Rising from its pages
// is a pop-up countryside, all cut from one ivory paper so only light and shadow make the picture:
// rolling fields divided by hedges with a church on the hill, three cypresses, a great oak made of
// three layers of lacy leaves, a cottage with scalloped shingles and cut windows, a picket fence,
// sheep, and a strip of grass and wildflowers at the front.
//
// Lights: a warm reading lamp from the front left (the main light, long shadows), cool moonlight
// from behind on the right (rims and cool shadows), and a warm light inside the cottage that glows
// out through its windows and door onto the page.
//
// Draw it with: node paper-film/tools/draw-one-page-still.mjs one-page-open-book OUT.png
// then finish with: python3 -I tools/finish_one_page_still.py OUT.png FINISHED.png

import * as THREE from '/paper-film/node_modules/three/build/three.module.js';

const IVORY = '#efe7d6';
const PAGE_IVORY = '#ebe2cd';
const INK_LINE = 'rgba(110, 92, 70, 0.28)';

// ------------------------------------------------------------------------------ small helpers
function seededRandom(seed) {
  let value = seed;
  return () => { value = (value * 16807) % 2147483647; return (value - 1) / 2147483646; };
}
const between = (random, low, high) => low + random() * (high - low);

let paperGrainPattern = null;
function paperGrain(context) {
  if (!paperGrainPattern) {
    const grain = document.createElement('canvas');
    grain.width = grain.height = 256;
    const grainContext = grain.getContext('2d');
    const image = grainContext.createImageData(256, 256);
    const random = seededRandom(99);
    for (let index = 0; index < image.data.length; index += 4) {
      const shade = 128 + (random() - 0.5) * 70;
      image.data[index] = image.data[index + 1] = image.data[index + 2] = shade;
      image.data[index + 3] = 255;
    }
    grainContext.putImageData(image, 0, 0);
    paperGrainPattern = grain;
  }
  return context.createPattern(paperGrainPattern, 'repeat');
}

function finishTexture(canvas, renderer) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}

// A cut-paper picture: draw(context, width, height, random) paints the paper in IVORY and cuts holes
// with cut(); everything left transparent is cut away. A faint grain is laid over the paper only.
function cutPaperTexture(renderer, widthPx, heightPx, seed, draw) {
  const canvas = document.createElement('canvas');
  canvas.width = widthPx; canvas.height = heightPx;
  const context = canvas.getContext('2d');
  context.fillStyle = IVORY;
  context.strokeStyle = IVORY;
  context.lineCap = 'round';
  context.lineJoin = 'round';
  draw(context, widthPx, heightPx, seededRandom(seed));
  context.globalCompositeOperation = 'source-atop';
  context.globalAlpha = 0.06;
  context.fillStyle = paperGrain(context);
  context.fillRect(0, 0, widthPx, heightPx);
  context.globalAlpha = 1;
  context.globalCompositeOperation = 'source-over';
  return finishTexture(canvas, renderer);
}

// cut a hole: whatever is drawn while cutting removes paper
function cutting(context, drawHole) {
  context.save();
  context.globalCompositeOperation = 'destination-out';
  context.fillStyle = '#000'; context.strokeStyle = '#000';
  drawHole();
  context.restore();
}

function paperMaterial(texture, { roughness = 0.92 } = {}) {
  return new THREE.MeshStandardMaterial({ map: texture, alphaTest: 0.5, side: THREE.DoubleSide, roughness, metalness: 0, shadowSide: THREE.DoubleSide });
}

// A flat cut-paper layer standing upright, its bottom edge at height y, facing the reader.
function standingLayer(texture, worldWidth, worldHeight, { x = 0, y = 0, z = 0, turn = 0 }) {
  const geometry = new THREE.PlaneGeometry(worldWidth, worldHeight);
  geometry.translate(0, worldHeight / 2, 0);
  const mesh = new THREE.Mesh(geometry, paperMaterial(texture));
  mesh.position.set(x, y, z);
  mesh.rotation.y = turn;
  mesh.castShadow = true; mesh.receiveShadow = true;
  return mesh;
}

// ------------------------------------------------------------------------------------ the book
// Each page curves up out of the gutter and flattens toward its outer edge, like a real open book.
const PAGE_WIDTH = 6.0;
const PAGE_LENGTH = 9.0;          // from the far (top) edge to the near (bottom) edge
const STACK_BOTTOM = -0.42;       // where the block of pages meets the cover
function pageHeight(x) {
  const softness = 0.05; // rounds the bottom of the fold so there is no hard crease
  const share = Math.min((Math.sqrt(x * x + (softness * PAGE_WIDTH) ** 2) - softness * PAGE_WIDTH) / (PAGE_WIDTH * (1 - softness)), 1);
  return 0.62 * (1 - Math.pow(1 - share, 2.6)) - 0.1 * Math.pow(share, 4);
}

function pageTexture(renderer, side) {
  const width = 1200, height = 1800;
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const context = canvas.getContext('2d');
  context.fillStyle = PAGE_IVORY;
  context.fillRect(0, 0, width, height);
  context.globalAlpha = 0.07;
  context.fillStyle = paperGrain(context);
  context.fillRect(0, 0, width, height);
  context.globalAlpha = 1;
  // a gentle darkening toward the gutter, where the pages curve away
  const gutter = side < 0 ? context.createLinearGradient(width, 0, width - 140, 0) : context.createLinearGradient(0, 0, 140, 0);
  gutter.addColorStop(0, 'rgba(90, 70, 45, 0.12)');
  gutter.addColorStop(1, 'rgba(90, 70, 45, 0)');
  context.fillStyle = gutter;
  context.fillRect(0, 0, width, height);
  // positions on the page in world units: x across the book, z from the far edge (-4.5) to the near one
  const toCanvas = (x, z) => [side < 0 ? (x + PAGE_WIDTH) / PAGE_WIDTH * width : x / PAGE_WIDTH * width, (z + PAGE_LENGTH / 2) / PAGE_LENGTH * height];
  const unitsToPixels = width / PAGE_WIDTH;
  const random = seededRandom(side < 0 ? 31 : 37);

  // printed ground details that read as lying flat: a pond with ripples, garden rows, tiny flowers
  const ink = (alpha) => `rgba(100, 82, 60, ${alpha})`;
  {
    const [cx, cy] = toCanvas(-4.3, 0.2);
    context.strokeStyle = ink(0.4); context.lineWidth = 2.4;
    context.fillStyle = 'rgba(120, 130, 140, 0.12)';
    context.beginPath(); context.ellipse(cx, cy, unitsToPixels * 0.9, unitsToPixels * 0.42, 0.05, 0, Math.PI * 2); context.fill(); context.stroke();
    context.lineWidth = 1.6;
    for (const ring of [0.25, 0.45, 0.65]) { context.beginPath(); context.ellipse(cx - unitsToPixels * 0.1, cy, unitsToPixels * 0.9 * ring, unitsToPixels * 0.42 * ring, 0.05, 0.3, 2.6); context.stroke(); }
    // reeds at the pond's edge, printed
    for (let reed = 0; reed < 9; reed += 1) {
      const angle = between(random, 3.4, 5.9), rx = cx + Math.cos(angle) * unitsToPixels * 0.92, ry = cy + Math.sin(angle) * unitsToPixels * 0.44;
      context.beginPath(); context.moveTo(rx, ry); context.lineTo(rx + between(random, -4, 4), ry - 14); context.stroke();
    }
  }
  context.strokeStyle = ink(0.32); context.lineWidth = 2;
  for (let row = 0; row < 5; row += 1) { // garden rows beside the cottage
    const [x0, y0] = toCanvas(4.15, -0.9 + row * 0.28), [x1] = toCanvas(5.5, 0);
    context.beginPath(); context.moveTo(x0, y0); context.lineTo(x1, y0); context.stroke();
    context.fillStyle = ink(0.35);
    for (let x = x0 + 10; x < x1 - 6; x += 22) { context.beginPath(); context.arc(x, y0 - 6, 4, 0, Math.PI * 2); context.fill(); }
  }
  context.fillStyle = ink(0.3);
  for (let flower = 0; flower < 260; flower += 1) {
    const [cx, cy] = toCanvas(side * between(random, 0.3, PAGE_WIDTH - 0.3), between(random, -2.9, 2.6));
    for (let petal = 0; petal < 5; petal += 1) { const angle = petal * 1.2566; context.beginPath(); context.arc(cx + Math.cos(angle) * 3.5, cy + Math.sin(angle) * 2.2, 1.8, 0, Math.PI * 2); context.fill(); }
  }
  // a printed path of stepping stones from the garden gate toward the reader
  const pathPoints = [];
  for (let step = 0; step <= 14; step += 1) {
    const share = step / 14;
    const x = 1.5 * (1 - share) ** 2 + 2 * (1 - share) * share * 0.2 + share * share * -0.9;
    const z = 1.45 + share * 1.15;
    pathPoints.push([x + (step % 2 === 0 ? 0.12 : -0.12), z]);
  }
  for (const [x, z] of pathPoints) {
    const [cx, cy] = toCanvas(x, z);
    const stoneWidth = unitsToPixels * between(random, 0.07, 0.1), stoneHeight = stoneWidth * between(random, 0.6, 0.8);
    context.fillStyle = 'rgba(105, 88, 66, 0.26)';
    context.beginPath(); context.ellipse(cx, cy, stoneWidth, stoneHeight, between(random, -0.4, 0.4), 0, Math.PI * 2); context.fill();
  }
  // soft shadows where the pop-up pieces meet the page (deepest right at the fold, fading behind it)
  const contactShadow = (xFrom, xTo, z, depth = 0.45, strengthAsked = 0.32) => {
    const strength = Math.min(0.6, strengthAsked * 1.3);
    context.save();
    context.filter = 'blur(10px)';
    const [x0, y0] = toCanvas(xFrom, z), [x1] = toCanvas(xTo, z);
    const [, yBehind] = toCanvas(xFrom, z - depth);
    const behind = context.createLinearGradient(0, y0, 0, yBehind);
    behind.addColorStop(0, `rgba(60, 42, 25, ${strength})`);
    behind.addColorStop(1, 'rgba(60, 42, 25, 0)');
    context.fillStyle = behind;
    context.fillRect(Math.min(x0, x1), yBehind, Math.abs(x1 - x0), y0 - yBehind);
    const [, yFront] = toCanvas(xFrom, z + 0.08);
    const front = context.createLinearGradient(0, y0, 0, yFront);
    front.addColorStop(0, `rgba(60, 42, 25, ${strength * 0.6})`);
    front.addColorStop(1, 'rgba(60, 42, 25, 0)');
    context.fillStyle = front;
    context.fillRect(Math.min(x0, x1), y0, Math.abs(x1 - x0), yFront - y0);
    context.restore();
  };
  for (const [z, depth] of [[-4.15, 0.3], [-3.55, 0.45], [-3.0, 0.45], [1.25, 0.4], [2.75, 0.35]]) contactShadow(-6, 6, z, depth);
  contactShadow(3.0, 5.0, -2.9, 0.5);
  contactShadow(-3.3, -1.7, -1.9, 0.7, 0.4);
  contactShadow(1.0, 3.9, -1.45, 0.6, 0.38);
  contactShadow(1.0, 3.9, 0.35, 0.25, 0.3);
  for (const [x, z, half] of [[-3.7, 2.0, 0.45], [-1.7, 2.35, 0.4], [0.9, 2.15, 0.35]]) contactShadow(x - half, x + half, z, 0.25, 0.26);

  // a few lines of small type near the bottom (shapes of words, not real words), and a page number
  context.fillStyle = 'rgba(60, 48, 36, 0.3)';
  const left = side < 0 ? 200 : 260, right = side < 0 ? width - 260 : width - 200;
  for (let line = 0; line < 8; line += 1) {
    let x = left + (line === 0 ? 40 : 0);
    const y = 1530 + line * 21;
    const end = line === 7 ? left + (right - left) * 0.45 : right;
    while (x < end) {
      const wordLength = between(random, 10, 46);
      if (x + wordLength > end) break;
      context.fillRect(x, y, wordLength, 5);
      x += wordLength + 8;
    }
  }
  context.font = 'italic 26px serif';
  context.fillStyle = 'rgba(60, 48, 36, 0.45)';
  context.textAlign = 'center';
  context.fillText(side < 0 ? '14' : '15', side < 0 ? 170 : width - 170, 1740);
  // a small printed rule and flourish above the type
  context.strokeStyle = 'rgba(60, 48, 36, 0.3)';
  context.lineWidth = 1.6;
  context.beginPath(); context.moveTo(width / 2 - 100, 1500); context.lineTo(width / 2 - 12, 1500); context.moveTo(width / 2 + 12, 1500); context.lineTo(width / 2 + 100, 1500); context.stroke();
  context.beginPath(); context.arc(width / 2, 1500, 6, 0, Math.PI * 2); context.stroke();
  return finishTexture(canvas, renderer);
}

function pageEdgeTexture(renderer) {
  // the edges of hundreds of pages: fine lines
  const canvas = document.createElement('canvas');
  canvas.width = 64; canvas.height = 512;
  const context = canvas.getContext('2d');
  context.fillStyle = '#ddd2ba';
  context.fillRect(0, 0, 64, 512);
  const random = seededRandom(5);
  for (let y = 0; y < 512; y += 3) {
    context.fillStyle = `rgba(120, 100, 75, ${between(random, 0.08, 0.3)})`;
    context.fillRect(0, y, 64, 1);
  }
  const texture = finishTexture(canvas, renderer);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function openBook(renderer) {
  const book = new THREE.Group();
  const columns = 90, rows = 6;
  for (const side of [-1, 1]) {
    // the top page, curved
    const geometry = new THREE.PlaneGeometry(PAGE_WIDTH, PAGE_LENGTH, columns, rows);
    geometry.rotateX(-Math.PI / 2);
    geometry.translate(side * PAGE_WIDTH / 2, 0, 0);
    const position = geometry.attributes.position;
    for (let index = 0; index < position.count; index += 1) position.setY(index, pageHeight(position.getX(index)));
    geometry.computeVertexNormals();
    const page = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ map: pageTexture(renderer, side), roughness: 0.95, side: THREE.DoubleSide, shadowSide: THREE.DoubleSide }));
    page.castShadow = true; page.receiveShadow = true;
    book.add(page);

    // the block of pages under it: the near and far edges follow the curve; the outer edge is straight
    const edgeMaterial = new THREE.MeshStandardMaterial({ map: pageEdgeTexture(renderer), roughness: 0.95, side: THREE.DoubleSide });
    for (const end of [-1, 1]) {
      const shape = [];
      for (let step = 0; step <= columns; step += 1) {
        const x = side * (step / columns) * PAGE_WIDTH;
        shape.push([x, pageHeight(x)]);
      }
      const triangles = [];
      for (let step = 0; step < columns; step += 1) {
        const [x0, y0] = shape[step], [x1, y1] = shape[step + 1];
        const bottom0 = STACK_BOTTOM + 0.25 * (1 - Math.min(Math.abs(x0) / 0.6, 1));
        const bottom1 = STACK_BOTTOM + 0.25 * (1 - Math.min(Math.abs(x1) / 0.6, 1));
        const z = end * PAGE_LENGTH / 2;
        triangles.push(x0, bottom0, z, x1, bottom1, z, x1, y1, z, x0, bottom0, z, x1, y1, z, x0, y0, z);
      }
      const edgeGeometry = new THREE.BufferGeometry();
      edgeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(triangles, 3));
      const uv = [];
      for (let index = 0; index < triangles.length; index += 3) uv.push(triangles[index] * 0.5, (triangles[index + 1] - STACK_BOTTOM) * 6);
      edgeGeometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      edgeGeometry.computeVertexNormals();
      const edge = new THREE.Mesh(edgeGeometry, edgeMaterial);
      edge.castShadow = true; edge.receiveShadow = true;
      book.add(edge);
    }
    const outerHeight = pageHeight(PAGE_WIDTH) - STACK_BOTTOM;
    const outer = new THREE.Mesh(new THREE.PlaneGeometry(PAGE_LENGTH, outerHeight), edgeMaterial);
    outer.rotation.y = side * Math.PI / 2;
    outer.position.set(side * PAGE_WIDTH, STACK_BOTTOM + outerHeight / 2, 0);
    outer.receiveShadow = true;
    book.add(outer);
  }
  // the cover boards: deep red cloth, a little bigger than the pages
  const clothCanvas = document.createElement('canvas');
  clothCanvas.width = clothCanvas.height = 512;
  const clothContext = clothCanvas.getContext('2d');
  clothContext.fillStyle = '#4b1d1a';
  clothContext.fillRect(0, 0, 512, 512);
  const random = seededRandom(8);
  for (let line = 0; line < 512; line += 2) {
    clothContext.fillStyle = `rgba(0,0,0,${between(random, 0.02, 0.12)})`; clothContext.fillRect(0, line, 512, 1);
    clothContext.fillStyle = `rgba(255,200,170,${between(random, 0.0, 0.05)})`; clothContext.fillRect(line, 0, 1, 512);
  }
  const clothTexture = finishTexture(clothCanvas, renderer);
  clothTexture.wrapS = clothTexture.wrapT = THREE.RepeatWrapping;
  clothTexture.repeat.set(4, 3);
  const cloth = new THREE.MeshStandardMaterial({ map: clothTexture, roughness: 0.85 });
  for (const side of [-1, 1]) {
    const board = new THREE.Mesh(new THREE.BoxGeometry(PAGE_WIDTH + 0.28, 0.1, PAGE_LENGTH + 0.4), cloth);
    board.position.set(side * (PAGE_WIDTH + 0.28) / 2 + side * 0.06, STACK_BOTTOM - 0.05, 0);
    board.rotation.z = side * -0.012;
    board.castShadow = true; board.receiveShadow = true;
    book.add(board);
  }
  const spine = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, PAGE_LENGTH + 0.4, 24, 1, true, Math.PI / 2, Math.PI), cloth);
  spine.rotation.x = Math.PI / 2;
  spine.position.set(0, STACK_BOTTOM - 0.05, 0);
  book.add(spine);
  return book;
}

// --------------------------------------------------------------------------- the cut-paper art
// Every drawer paints on a canvas whose bottom edge is the ground line.

function drawFieldsAndChurch({ crest = 0.42, swell = 0.13, phase = 0.6, waves = 1.6, church = true, birds = true, trees = true } = {}) { return (context, width, height, random) => {
  const ground = height;
  const hillTop = (x) => height * crest + Math.sin(x / width * Math.PI * waves + phase) * height * swell + Math.sin(x / width * Math.PI * 4.2 + phase) * height * 0.04;
  context.beginPath();
  context.moveTo(0, ground);
  for (let x = 0; x <= width; x += 8) context.lineTo(x, hillTop(x));
  context.lineTo(width, ground);
  context.closePath();
  context.fill();
  // little round trees along the crest
  if (trees) for (let x = 40; x < width - 40; x += between(random, 50, 140)) {
    if (church && x > width * 0.62 && x < width * 0.78) continue; // room for the church
    const y = hillTop(x), size = between(random, 14, 26);
    context.fillRect(x - 2.5, y - size * 1.2, 5, size * 1.3);
    context.beginPath(); context.arc(x, y - size * 1.5, size, 0, Math.PI * 2); context.fill();
  }
  // the church on the right hill: nave, tower, spire, with arched windows cut out
  if (church) {
  const churchX = width * 0.7, churchBase = hillTop(churchX) + 6;
  context.fillRect(churchX - 70, churchBase - 70, 120, 72);
  context.beginPath(); context.moveTo(churchX - 78, churchBase - 68); context.lineTo(churchX - 10, churchBase - 110); context.lineTo(churchX + 58, churchBase - 68); context.fill();
  context.fillRect(churchX + 40, churchBase - 150, 46, 152);
  context.beginPath(); context.moveTo(churchX + 36, churchBase - 148); context.lineTo(churchX + 63, churchBase - 250); context.lineTo(churchX + 90, churchBase - 148); context.fill();
  context.fillRect(churchX + 61, churchBase - 275, 4, 30);
  context.fillRect(churchX + 53, churchBase - 266, 20, 4);
  cutting(context, () => {
    for (const windowX of [churchX - 52, churchX - 22, churchX + 8]) {
      context.beginPath(); context.moveTo(windowX, churchBase - 22); context.lineTo(windowX, churchBase - 44);
      context.arc(windowX + 7, churchBase - 44, 7, Math.PI, 0); context.lineTo(windowX + 14, churchBase - 22); context.fill();
    }
    context.beginPath(); context.arc(churchX + 63, churchBase - 118, 11, 0, Math.PI * 2); context.fill();
  });
  }
  // hedges dividing the fields: wavy cut lines across the hills and down them
  cutting(context, () => {
    context.lineWidth = 3.2;
    for (let band = 2; band <= 4; band += 2) {
      context.beginPath();
      const share = band / 6 + between(random, -0.05, 0.05), wobble = between(random, 0, 6.28);
      for (let x = 0; x <= width; x += 10) {
        const top = hillTop(x) + 20;
        const y = top + (ground - top) * share + Math.sin(x / 90 + wobble) * 6;
        if (x === 0) context.moveTo(x, y); else context.lineTo(x, y);
      }
      context.stroke();
    }
    // furrows in some fields: rows of short slits
    context.lineWidth = 2;
    for (let field = 0; field < 9; field += 1) {
      const x0 = between(random, 60, width - 260), band = Math.floor(between(random, 1, 5));
      const slant = between(random, -0.5, 0.5);
      for (let row = 0; row < 7; row += 1) {
        const x = x0 + row * 18;
        const top = hillTop(x) + 20;
        const y = top + (ground - top) * ((band + 0.5) / 6);
        context.beginPath(); context.moveTo(x, y - 9); context.lineTo(x + slant * 10, y + 9); context.stroke();
      }
    }
  });
  // birds in the sky above the hills, joined to the paper by a fine stalk of thread
  context.lineWidth = 3;
  if (birds) for (const [bx, by, size] of [[width * 0.38, height * 0.12, 18], [width * 0.44, height * 0.07, 13], [width * 0.47, height * 0.16, 11]]) {
    context.beginPath(); context.moveTo(bx - size, by - size * 0.3); context.quadraticCurveTo(bx - size * 0.4, by - size * 0.7, bx, by); context.quadraticCurveTo(bx + size * 0.4, by - size * 0.7, bx + size, by - size * 0.3); context.stroke();
  }
}; }

function drawCypresses(context, width, height, random) {
  const trees = [[width * 0.25, 0.62], [width * 0.5, 0.98], [width * 0.76, 0.74]];
  for (const [cx, share] of trees) {
    const top = height * (1 - share), treeWidth = width * 0.17;
    context.beginPath();
    context.moveTo(cx, top);
    context.bezierCurveTo(cx + treeWidth * 0.9, top + (height - top) * 0.35, cx + treeWidth * 0.75, height - 60, cx + 8, height - 40);
    context.lineTo(cx + 8, height); context.lineTo(cx - 8, height); context.lineTo(cx - 8, height - 40);
    context.bezierCurveTo(cx - treeWidth * 0.75, height - 60, cx - treeWidth * 0.9, top + (height - top) * 0.35, cx, top);
    context.fill();
    cutting(context, () => {
      context.lineWidth = 3.4;
      for (let y = top + 40; y < height - 70; y += 26) {
        const spread = treeWidth * 0.55 * Math.sin(Math.min(1, (y - top) / ((height - top) * 0.45)) * Math.PI / 2);
        for (let k = -1; k <= 1; k += 2) {
          const offset = between(random, -4, 4);
          context.beginPath(); context.moveTo(cx + offset, y); context.lineTo(cx + k * spread * between(random, 0.55, 0.9), y + 16); context.stroke();
        }
      }
    });
  }
}

// The oak's shape, shared by its three layers so their branches line up.
function oakSkeleton(width, height) {
  const random = seededRandom(404);
  const centre = width / 2;
  width = height * 0.652; // the tree's own proportions, whatever the sheet's width
  const branches = [];
  const tips = [];
  const grow = (x, y, angle, length, thickness, depth) => {
    const endX = x + Math.cos(angle) * length, endY = y + Math.sin(angle) * length;
    branches.push([x, y, endX, endY, thickness, thickness * 0.66]);
    if (depth === 0) { tips.push([endX, endY]); return; }
    const children = depth > 3 ? 2 : (random() < 0.5 ? 2 : 3);
    for (let child = 0; child < children; child += 1) {
      const spread = (child - (children - 1) / 2) * between(random, 0.45, 0.75) + between(random, -0.15, 0.15);
      grow(endX, endY, angle + spread, length * between(random, 0.66, 0.8), thickness * 0.66, depth - 1);
    }
    if (depth < 3) tips.push([endX, endY]);
  };
  const trunkTop = [centre, height * 0.6];
  for (const angle of [-Math.PI / 2 - 0.95, -Math.PI / 2 - 0.35, -Math.PI / 2 + 0.25, -Math.PI / 2 + 0.85]) {
    grow(trunkTop[0], trunkTop[1], angle, height * 0.15, width * 0.034, 5);
  }
  return { branches, tips, trunkTop };
}

function drawOak(layer) {
  return (context, sheetWidth, height, random) => {
    const { branches, tips, trunkTop } = oakSkeleton(sheetWidth, height);
    const width = height * 0.652;
    // trunk with flared roots
    const baseHalf = width * 0.07;
    context.beginPath();
    context.moveTo(trunkTop[0] - width * 0.045, trunkTop[1]);
    context.bezierCurveTo(trunkTop[0] - width * 0.05, height * 0.82, trunkTop[0] - baseHalf * 0.8, height * 0.93, trunkTop[0] - baseHalf * 1.9, height);
    context.lineTo(trunkTop[0] + baseHalf * 1.8, height);
    context.bezierCurveTo(trunkTop[0] + baseHalf * 0.8, height * 0.94, trunkTop[0] + width * 0.05, height * 0.8, trunkTop[0] + width * 0.04, trunkTop[1]);
    context.closePath();
    context.fill();
    if (layer === 2) cutting(context, () => { // bark: fine vertical slits on the front layer only
      context.lineWidth = 2;
      for (let slit = 0; slit < 14; slit += 1) {
        const x = trunkTop[0] + between(random, -width * 0.03, width * 0.03), y = between(random, height * 0.64, height * 0.95);
        context.beginPath(); context.moveTo(x, y); context.lineTo(x + between(random, -3, 3), y + between(random, 30, 70)); context.stroke();
      }
    });
    for (const [x0, y0, x1, y1, w0, w1] of branches) {
      const angle = Math.atan2(y1 - y0, x1 - x0) + Math.PI / 2;
      context.beginPath();
      context.moveTo(x0 + Math.cos(angle) * w0 / 2, y0 + Math.sin(angle) * w0 / 2);
      context.lineTo(x1 + Math.cos(angle) * w1 / 2, y1 + Math.sin(angle) * w1 / 2);
      context.lineTo(x1 - Math.cos(angle) * w1 / 2, y1 - Math.sin(angle) * w1 / 2);
      context.lineTo(x0 - Math.cos(angle) * w0 / 2, y0 - Math.sin(angle) * w0 / 2);
      context.fill();
    }
    // leaves: clusters around the branch tips; the back layer is dense, the front one sparse
    const clusterRadius = [width * 0.1, width * 0.085, width * 0.065][layer];
    const leavesPerCluster = [90, 55, 30][layer];
    const leafSize = [17, 15, 14][layer];
    const leafRandom = seededRandom(1000 + layer * 77);
    for (const [tipX, tipY] of tips) {
      if (layer === 2 && leafRandom() < 0.45) continue;
      for (let leaf = 0; leaf < leavesPerCluster; leaf += 1) {
        const angle = leafRandom() * Math.PI * 2, distance = Math.sqrt(leafRandom()) * clusterRadius;
        const x = tipX + Math.cos(angle) * distance, y = tipY + Math.sin(angle) * distance * 0.8 - clusterRadius * 0.2;
        const size = leafSize * between(leafRandom, 0.7, 1.3);
        context.save();
        context.translate(x, y);
        context.rotate(leafRandom() * Math.PI * 2);
        context.beginPath();
        context.moveTo(-size, 0);
        context.quadraticCurveTo(0, -size * 0.55, size, 0);
        context.quadraticCurveTo(0, size * 0.55, -size, 0);
        context.fill();
        context.restore();
      }
    }
    // the leaves' veins: a fine cut through the middle of some leaves on the front layers
    if (layer > 0) cutting(context, () => {
      context.lineWidth = 1.6;
      const veinRandom = seededRandom(2000 + layer);
      for (const [tipX, tipY] of tips) {
        for (let vein = 0; vein < 6; vein += 1) {
          const x = tipX + between(veinRandom, -clusterRadius, clusterRadius) * 0.7, y = tipY + between(veinRandom, -clusterRadius, clusterRadius) * 0.6;
          const angle = veinRandom() * Math.PI;
          context.beginPath(); context.moveTo(x - Math.cos(angle) * 8, y - Math.sin(angle) * 8); context.lineTo(x + Math.cos(angle) * 8, y + Math.sin(angle) * 8); context.stroke();
        }
      }
    });
  };
}

function drawFence(context, width, height, random) {
  const railY = [height * 0.42, height * 0.72];
  for (const y of railY) context.fillRect(0, y, width, height * 0.07);
  let x = 6;
  while (x < width - 20) {
    const gate = x > width * 0.6 && x < width * 0.6 + 160;
    const paleWidth = 14, top = height * between(random, 0.08, 0.14);
    if (!gate) {
      context.beginPath();
      context.moveTo(x, height); context.lineTo(x, top + 12); context.lineTo(x + paleWidth / 2, top); context.lineTo(x + paleWidth, top + 12); context.lineTo(x + paleWidth, height);
      context.fill();
    }
    x += paleWidth + 11;
  }
  // the gate: a frame with a diagonal brace and a curl on top
  const gateX = width * 0.6 + 8;
  context.lineWidth = 9; context.lineCap = 'butt';
  context.strokeRect(gateX, height * 0.2, 140, height * 0.8);
  context.beginPath(); context.moveTo(gateX, height); context.lineTo(gateX + 140, height * 0.2); context.stroke();
  context.beginPath(); context.moveTo(gateX + 70, height * 0.2); context.lineTo(gateX + 70, height); context.stroke();
  context.lineWidth = 6;
  context.beginPath(); context.arc(gateX + 70, height * 0.14, 18, Math.PI * 0.1, Math.PI * 1.9); context.stroke();
  // climbing roses on some posts: round flowers with their petals cut
  for (let rose = 0; rose < 9; rose += 1) {
    const roseX = between(random, 20, width - 20), roseY = height * between(random, 0.25, 0.6), size = between(random, 9, 14);
    if (Math.abs(roseX - gateX - 70) < 90) continue;
    context.beginPath(); context.arc(roseX, roseY, size, 0, Math.PI * 2); context.fill();
    for (let leaf = 0; leaf < 3; leaf += 1) {
      const angle = between(random, 0, Math.PI * 2);
      context.beginPath(); context.ellipse(roseX + Math.cos(angle) * size * 1.5, roseY + Math.sin(angle) * size * 1.5, size * 0.75, size * 0.35, angle, 0, Math.PI * 2); context.fill();
    }
    cutting(context, () => {
      context.lineWidth = 1.6;
      for (let ring = 1; ring <= 2; ring += 1) { context.beginPath(); context.arc(roseX, roseY, size * ring / 3, ring, ring + Math.PI * 1.4); context.stroke(); }
    });
  }
}

function drawSheep(facing) {
  return (context, width, height, random) => {
    context.save();
    if (facing < 0) { context.translate(width, 0); context.scale(-1, 1); }
    const bodyX = width * 0.42, bodyY = height * 0.45, bodyWidth = width * 0.28, bodyHeight = height * 0.22;
    // legs, a little apart, with small hooves
    for (const legX of [bodyX - bodyWidth * 0.62, bodyX - bodyWidth * 0.3, bodyX + bodyWidth * 0.32, bodyX + bodyWidth * 0.64]) {
      context.fillRect(legX - 7, bodyY, 14, height - bodyY - 4);
      context.fillRect(legX - 9, height - 12, 18, 12);
    }
    // woolly body: a scalloped outline of overlapping circles
    context.beginPath(); context.ellipse(bodyX, bodyY, bodyWidth, bodyHeight, 0, 0, Math.PI * 2); context.fill();
    for (let bump = 0; bump < 22; bump += 1) {
      const angle = (bump / 22) * Math.PI * 2;
      context.beginPath(); context.arc(bodyX + Math.cos(angle) * bodyWidth, bodyY + Math.sin(angle) * bodyHeight, between(random, 15, 21), 0, Math.PI * 2); context.fill();
    }
    // head and ears
    const headX = bodyX + bodyWidth * 1.32, headY = bodyY - bodyHeight * 0.75;
    context.beginPath(); context.moveTo(bodyX + bodyWidth * 0.8, bodyY - bodyHeight * 0.6); context.lineTo(headX - 10, headY - 18); context.lineTo(headX, headY + 20); context.lineTo(bodyX + bodyWidth * 0.9, bodyY + 4); context.fill();
    context.beginPath(); context.ellipse(headX + 8, headY + 4, 40, 24, 0.55, 0, Math.PI * 2); context.fill();
    context.beginPath(); context.ellipse(headX - 22, headY - 14, 22, 8, -0.4, 0, Math.PI * 2); context.fill();
    // a tuft of tail
    context.beginPath(); context.arc(bodyX - bodyWidth * 1.08, bodyY - bodyHeight * 0.3, 16, 0, Math.PI * 2); context.fill();
    cutting(context, () => {
      // curls of wool
      context.lineWidth = 2.4;
      for (let curl = 0; curl < 12; curl += 1) {
        const angle = random() * Math.PI * 2, distance = Math.sqrt(random()) * 0.8;
        const x = bodyX + Math.cos(angle) * bodyWidth * distance, y = bodyY + Math.sin(angle) * bodyHeight * distance;
        context.beginPath(); context.arc(x, y, between(random, 5, 8), random() * 6, random() * 6 + Math.PI * 1.2); context.stroke();
      }
      context.beginPath(); context.ellipse(headX + 10, headY - 4, 6, 3.5, 0.5, 0, Math.PI * 2); context.fill();
      context.lineWidth = 2; context.beginPath(); context.arc(headX + 34, headY + 18, 7, 0.2, 1.6); context.stroke();
    });
    context.restore();
  };
}

function drawGrass(context, width, height, random) {
  context.fillRect(0, height - 14, width, 14);
  for (let blade = 0; blade < 520; blade += 1) {
    const x = between(random, 0, width), bladeHeight = height * between(random, 0.25, 0.8), lean = between(random, -22, 22), bladeWidth = between(random, 3.5, 7);
    context.beginPath();
    context.moveTo(x - bladeWidth, height);
    context.quadraticCurveTo(x + lean * 0.3, height - bladeHeight * 0.6, x + lean, height - bladeHeight);
    context.quadraticCurveTo(x + lean * 0.3 + bladeWidth, height - bladeHeight * 0.5, x + bladeWidth, height);
    context.fill();
  }
  // daisies on tall stems: petals with gaps cut between them, a ring cut round the middle
  for (let daisy = 0; daisy < 34; daisy += 1) {
    const x = between(random, 20, width - 20), y = height * between(random, 0.06, 0.35), size = between(random, 9, 15);
    context.lineWidth = 3.2;
    context.beginPath(); context.moveTo(x, y); context.quadraticCurveTo(x + between(random, -12, 12), (y + height) / 2, x + between(random, -6, 6), height); context.stroke();
    for (let petal = 0; petal < 10; petal += 1) {
      const angle = (petal / 10) * Math.PI * 2;
      context.beginPath(); context.ellipse(x + Math.cos(angle) * size * 0.7, y + Math.sin(angle) * size * 0.7, size * 0.55, size * 0.2, angle, 0, Math.PI * 2); context.fill();
    }
    context.beginPath(); context.arc(x, y, size * 0.32, 0, Math.PI * 2); context.fill();
    cutting(context, () => { context.lineWidth = 1.4; context.beginPath(); context.arc(x, y, size * 0.42, 0, Math.PI * 2); context.stroke(); });
  }
  // seed heads: a stem with a fan of fine strokes
  for (let head = 0; head < 16; head += 1) {
    const x = between(random, 20, width - 20), y = height * between(random, 0.04, 0.2);
    context.lineWidth = 2.4;
    context.beginPath(); context.moveTo(x, height); context.quadraticCurveTo(x + 10, (y + height) / 2, x, y); context.stroke();
    context.lineWidth = 1.8;
    for (let seed = 0; seed < 9; seed += 1) {
      const angle = -Math.PI / 2 + (seed - 4) * 0.28;
      context.beginPath(); context.moveTo(x, y); context.lineTo(x + Math.cos(angle) * 16, y + Math.sin(angle) * 16); context.stroke();
    }
  }
}

// A crescent moon on a slim paper stalk, with stars hanging from it on fine threads.
function drawMoon(context, width, height, random) {
  const cx = width * 0.55, cy = height * 0.2, radius = width * 0.3;
  // the stalk: a slim strip that bends gently up from the hills to the moon
  context.lineWidth = 9;
  context.beginPath(); context.moveTo(width * 0.42, height); context.bezierCurveTo(width * 0.4, height * 0.7, width * 0.62, height * 0.5, cx - radius * 0.2, cy + radius * 0.95); context.stroke();
  context.beginPath(); context.arc(cx, cy, radius, 0, Math.PI * 2); context.fill();
  cutting(context, () => {
    context.beginPath(); context.arc(cx + radius * 0.42, cy - radius * 0.22, radius * 0.86, 0, Math.PI * 2); context.fill();
    for (let crater = 0; crater < 7; crater += 1) {
      const angle = between(random, 2.0, 4.4), distance = between(random, 0.45, 0.8) * radius;
      context.beginPath(); context.arc(cx + Math.cos(angle) * distance, cy + Math.sin(angle) * distance, between(random, 5, 11), 0, Math.PI * 2); context.fill();
    }
  });
  // stars on threads, each star cut with a small hole in the middle
  const star = (x, y, size) => {
    context.beginPath();
    for (let point = 0; point < 10; point += 1) {
      const angle = -Math.PI / 2 + point * Math.PI / 5, reach = point % 2 === 0 ? size : size * 0.45;
      context.lineTo(x + Math.cos(angle) * reach, y + Math.sin(angle) * reach);
    }
    context.closePath(); context.fill();
    cutting(context, () => { context.beginPath(); context.arc(x, y, size * 0.14, 0, Math.PI * 2); context.fill(); });
  };
  context.lineWidth = 2;
  for (const [x, drop, size] of [[cx - radius * 0.75, 0.42, 30], [cx - radius * 0.35, 0.62, 22], [cx + radius * 0.05, 0.5, 26]]) {
    const topY = cy + Math.sqrt(Math.max(0, radius * radius - (x - cx) ** 2)) * 0.9;
    const y = topY + height * drop * 0.32;
    context.beginPath(); context.moveTo(x, topY); context.lineTo(x, y - size); context.stroke();
    star(x, y, size);
  }
  for (const [x, y, size] of [[width * 0.12, height * 0.08, 20], [width * 0.9, height * 0.42, 16], [width * 0.18, height * 0.34, 14]]) {
    context.beginPath(); context.moveTo(x, y); context.lineTo(cx + (x < cx ? -radius : radius) * 0.6, cy + (y - cy) * 0.3); context.stroke();
    star(x, y, size);
  }
}

function drawSmokeCurl(context, width, height, random) {
  // puffs of smoke rising from the chimney (bottom middle), each with a cut curl inside
  let x = width * 0.45, y = height * 0.92, size = width * 0.13;
  for (let puff = 0; puff < 7; puff += 1) {
    context.beginPath(); context.arc(x, y, size, 0, Math.PI * 2); context.fill();
    cutting(context, () => { context.lineWidth = 2.6; context.beginPath(); context.arc(x, y, size * 0.55, puff, puff + Math.PI * 1.3); context.stroke(); });
    x += width * between(random, 0.04, 0.09) * (puff % 2 === 0 ? 1 : 0.4);
    y -= size * 1.35;
    size *= 1.08;
  }
}

// ------------------------------------------------------------------------------------ the cottage
function cottage(renderer) {
  const group = new THREE.Group();
  const halfWidth = 1.3, halfDepth = 0.85, wallTop = 1.95, ridge = 3.05, overhang = 0.2;

  // long walls: stone courses printed faintly, two mullioned windows cut out, and a doorway on the front
  const longWall = (withDoor) => cutPaperTexture(renderer, 900, 675, withDoor ? 61 : 62, (context, width, height, random) => {
    context.fillRect(0, 0, width, height);
    context.strokeStyle = INK_LINE; context.lineWidth = 2;
    for (let course = 0; course < 16; course += 1) {
      const y = height - course * 26;
      context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke();
      for (let joint = (course % 2) * 30; joint < width; joint += 60 + between(random, -8, 8)) { context.beginPath(); context.moveTo(joint, y); context.lineTo(joint, y - 26); context.stroke(); }
    }
    const windows = withDoor ? [width * 0.2, width * 0.8] : []; // the back wall is solid, so no light leaks out behind
    const windowTop = height * 0.18, windowHeight = height * 0.25, windowWidth = width * 0.15;
    cutting(context, () => {
      for (const centre of windows) {
        const left = centre - windowWidth / 2, bar = 7;
        for (let row = 0; row < 3; row += 1) for (let column = 0; column < 2; column += 1) {
          const paneWidth = (windowWidth - bar * 3) / 2, paneHeight = (windowHeight - bar * 4) / 3;
          context.fillRect(left + bar + column * (paneWidth + bar), windowTop + bar + row * (paneHeight + bar), paneWidth, paneHeight);
        }
      }
      if (withDoor) {
        context.beginPath();
        context.moveTo(width * 0.43, height * 0.76); context.lineTo(width * 0.43, height * 0.3);
        context.arc(width * 0.5, height * 0.3, width * 0.07, Math.PI, 0);
        context.lineTo(width * 0.57, height * 0.76); context.fill();
      }
    });
    // printed lintels and sills
    context.strokeStyle = 'rgba(110, 92, 70, 0.4)'; context.lineWidth = 3;
    for (const centre of windows) {
      context.strokeRect(centre - windowWidth / 2 - 10, windowTop - 10, windowWidth + 20, windowHeight + 20);
    }
  });
  const gableWall = (seed) => cutPaperTexture(renderer, 700, 820, seed, (context, width, height, random) => {
    const wallShare = wallTop / ridge;
    context.beginPath();
    context.moveTo(0, height); context.lineTo(0, height * (1 - wallShare)); context.lineTo(width / 2, 0); context.lineTo(width, height * (1 - wallShare)); context.lineTo(width, height);
    context.fill();
    context.strokeStyle = INK_LINE; context.lineWidth = 2;
    for (let course = 0; course < 15; course += 1) { const y = height - course * 26; context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke(); }
    cutting(context, () => {
      // round window in the gable, with four spokes left in
      const cx = width / 2, cy = height * 0.28, radius = width * 0.07;
      for (let quarter = 0; quarter < 4; quarter += 1) {
        context.beginPath(); context.moveTo(cx, cy); context.arc(cx, cy, radius, quarter * Math.PI / 2 + 0.12, (quarter + 1) * Math.PI / 2 - 0.12); context.closePath(); context.fill();
      }
      // a small window lower down
      context.fillRect(width * 0.42, height * 0.52, width * 0.07, width * 0.1);
      context.fillRect(width * 0.51, height * 0.52, width * 0.07, width * 0.1);
    });
  });

  const wallMesh = (texture, wallWidth, wallHeight, x, z, turn) => {
    const mesh = standingLayer(texture, wallWidth, wallHeight, { x, z, turn });
    group.add(mesh);
    return mesh;
  };
  const frontTexture = longWall(true), backTexture = longWall(false);
  wallMesh(frontTexture, halfWidth * 2, wallTop, 0, halfDepth, 0);
  wallMesh(backTexture, halfWidth * 2, wallTop, 0, -halfDepth, Math.PI);
  wallMesh(gableWall(63), halfDepth * 2, ridge, halfWidth, 0, Math.PI / 2);
  wallMesh(gableWall(64), halfDepth * 2, ridge, -halfWidth, 0, -Math.PI / 2);

  // the door, standing a little open
  const doorTexture = cutPaperTexture(renderer, 140, 300, 65, (context, width, height) => {
    context.beginPath(); context.moveTo(0, height); context.lineTo(0, 70); context.arc(width / 2, 70, width / 2, Math.PI, 0); context.lineTo(width, height); context.fill();
    context.strokeStyle = INK_LINE; context.lineWidth = 3;
    for (const x of [width * 0.33, width * 0.66]) { context.beginPath(); context.moveTo(x, 40); context.lineTo(x, height); context.stroke(); }
    cutting(context, () => { context.beginPath(); context.arc(width / 2, 75, 14, 0, Math.PI * 2); context.fill(); });
  });
  const doorWidth = halfWidth * 2 * 0.14, doorHeight = wallTop * 0.71;
  const doorGeometry = new THREE.PlaneGeometry(doorWidth, doorHeight);
  doorGeometry.translate(doorWidth / 2, doorHeight / 2, 0);
  const door = new THREE.Mesh(doorGeometry, paperMaterial(doorTexture));
  door.position.set(-halfWidth * 2 * 0.07, wallTop * 0.24 - 0.0, halfDepth + 0.005);
  door.rotation.y = -1.0;
  door.castShadow = true; door.receiveShadow = true;
  group.add(door);

  // the roof: rows of scalloped shingles, each row's lower edge lifted by the row beneath
  const shingleTexture = cutPaperTexture(renderer, 1320, 200, 66, (context, width, height) => {
    const scallop = 60;
    context.fillRect(0, 0, width, height * 0.62);
    for (let x = 0; x < width + scallop; x += scallop) { context.beginPath(); context.arc(x + scallop / 2, height * 0.62, scallop / 2, 0, Math.PI); context.fill(); }
    context.strokeStyle = INK_LINE; context.lineWidth = 2;
    for (let x = 0; x < width + scallop; x += scallop) { context.beginPath(); context.moveTo(x, height * 0.3); context.lineTo(x, height * 0.64); context.stroke(); }
  });
  const slopeRun = halfDepth + overhang, slopeRise = (ridge - wallTop) * (slopeRun / halfDepth);
  const slopeLength = Math.hypot(slopeRun, slopeRise);
  const rows = 7, rowLength = slopeLength / rows * 1.75, roofLength = halfWidth * 2 + overhang * 2;
  for (const side of [-1, 1]) {
    const eave = new THREE.Vector3(0, ridge - slopeRise, side * slopeRun);
    const peak = new THREE.Vector3(0, ridge + 0.02, 0);
    const down = new THREE.Vector3().subVectors(eave, peak).normalize();
    const outward = new THREE.Vector3(0, slopeRun, side * slopeRise).normalize();
    for (let row = 0; row < rows; row += 1) {
      const bottomDistance = slopeLength * (1 - row / rows);
      const bottom = peak.clone().addScaledVector(down, bottomDistance).addScaledVector(outward, 0.085 + (rows - row) * 0.006);
      const top = peak.clone().addScaledVector(down, Math.max(0, bottomDistance - rowLength)).addScaledVector(outward, 0.015 + (rows - row) * 0.006);
      const geometry = new THREE.PlaneGeometry(roofLength, 1);
      const shingles = new THREE.Mesh(geometry, paperMaterial(shingleTexture));
      // place the strip between its top and bottom lines, scalloped edge at the bottom
      const middle = bottom.clone().add(top).multiplyScalar(0.5);
      const along = new THREE.Vector3().subVectors(top, bottom);
      shingles.scale.y = along.length();
      shingles.position.copy(middle);
      shingles.lookAt(middle.clone().add(outward));
      const upInPlane = along.clone().normalize();
      const currentUp = new THREE.Vector3(0, 1, 0).applyQuaternion(shingles.quaternion);
      const spin = Math.atan2(new THREE.Vector3().crossVectors(currentUp, upInPlane).dot(outward), currentUp.dot(upInPlane));
      shingles.rotateZ(spin);
      shingles.castShadow = true; shingles.receiveShadow = true;
      group.add(shingles);
    }
  }
  // ridge cap: a folded strip along the top
  const capTexture = cutPaperTexture(renderer, 64, 64, 67, (context, width, height) => context.fillRect(0, 0, width, height));
  for (const side of [-1, 1]) {
    const cap = new THREE.Mesh(new THREE.PlaneGeometry(roofLength + 0.04, 0.2), paperMaterial(capTexture));
    cap.position.set(0, ridge + 0.06, side * 0.06);
    cap.rotation.x = -side * (Math.PI / 2 - Math.atan2(slopeRise, slopeRun)) - (side > 0 ? 0 : Math.PI);
    cap.castShadow = true; cap.receiveShadow = true;
    group.add(cap);
  }
  // chimney with brick lines and a cap, on the right of the ridge
  const brickTexture = cutPaperTexture(renderer, 128, 256, 68, (context, width, height) => {
    context.fillRect(0, 0, width, height);
    context.strokeStyle = INK_LINE; context.lineWidth = 2;
    for (let y = 0; y < height; y += 16) { context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke(); }
  });
  const chimney = new THREE.Mesh(new THREE.BoxGeometry(0.32, 1.0, 0.32), paperMaterial(brickTexture));
  chimney.position.set(halfWidth * 0.55, ridge + 0.05, -0.25);
  chimney.castShadow = true; chimney.receiveShadow = true;
  group.add(chimney);
  const chimneyCap = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.06, 0.42), paperMaterial(capTexture));
  chimneyCap.position.set(halfWidth * 0.55, ridge + 0.58, -0.25);
  chimneyCap.castShadow = true;
  group.add(chimneyCap);
  const smoke = standingLayer(cutPaperTexture(renderer, 300, 700, 69, drawSmokeCurl), 0.75, 1.75, { x: halfWidth * 0.55 + 0.05, y: ridge + 0.55, z: -0.25 });
  group.add(smoke);

  // the warm light inside, glowing out through the windows and door
  const hearth = new THREE.PointLight(0xffa04a, 9, 0, 2);
  hearth.position.set(0.1, 1.05, 0.0);
  hearth.castShadow = true;
  hearth.shadow.mapSize.set(1024, 1024);
  hearth.shadow.bias = -0.003;
  hearth.shadow.normalBias = 0;
  hearth.shadow.camera.near = 0.05;
  group.add(hearth);
  return group;
}

// ---------------------------------------------------------------------------------- the scene
export async function build(stage) {
  const { renderer, scene, camera } = stage;
  scene.traverse((object) => { if (object.isLight) object.visible = false; });
  renderer.setPixelRatio(2);
  renderer.setSize(stage.FRAME_WIDTH, stage.FRAME_HEIGHT, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.92;

  // the darkness around the book: deep blue-black, a little lighter behind the pop-up
  const backgroundCanvas = document.createElement('canvas');
  backgroundCanvas.width = 540; backgroundCanvas.height = 960;
  const backgroundContext = backgroundCanvas.getContext('2d');
  const glow = backgroundContext.createRadialGradient(270, 330, 20, 270, 400, 700);
  glow.addColorStop(0, '#1d2433');
  glow.addColorStop(0.45, '#0d1119');
  glow.addColorStop(1, '#040507');
  backgroundContext.fillStyle = glow;
  backgroundContext.fillRect(0, 0, 540, 960);
  const backgroundTexture = new THREE.CanvasTexture(backgroundCanvas);
  backgroundTexture.colorSpace = THREE.SRGBColorSpace;
  scene.background = backgroundTexture;

  const world = new THREE.Group();
  scene.add(world);
  world.add(openBook(renderer));

  // the pop-up, back to front
  world.add(standingLayer(cutPaperTexture(renderer, 2600, 900, 21, drawFieldsAndChurch({ crest: 0.5, swell: 0.16, phase: 0.6 })), 11.2, 3.9, { z: -4.15 }));
  world.add(standingLayer(cutPaperTexture(renderer, 2600, 700, 32, drawFieldsAndChurch({ crest: 0.5, swell: 0.2, phase: 2.3, waves: 2.2, church: false, birds: false })), 11.0, 2.7, { z: -3.55 }));
  world.add(standingLayer(cutPaperTexture(renderer, 2600, 520, 33, drawFieldsAndChurch({ crest: 0.45, swell: 0.22, phase: 4.1, waves: 1.3, church: false, birds: false, trees: false })), 10.8, 1.7, { z: -3.0 }));
  world.add(standingLayer(cutPaperTexture(renderer, 1000, 2600, 34, drawMoon), 3.4, 8.8, { x: 2.7, y: 0.6, z: -4.35 }));
  world.add(standingLayer(cutPaperTexture(renderer, 700, 1800, 22, drawCypresses), 2.1, 5.4, { x: 4.0, z: -2.9 }));
  for (const layer of [0, 1, 2]) {
    world.add(standingLayer(cutPaperTexture(renderer, 2200, 2300, 23 + layer, drawOak(layer)), 9.09, 9.5, { x: -2.5, z: -2.45 + layer * 0.28 }));
  }
  const house = cottage(renderer);
  house.position.set(2.45, 0, -0.55);
  house.rotation.y = -0.12;
  world.add(house);
  world.add(standingLayer(cutPaperTexture(renderer, 2600, 260, 27, drawFence), 11.0, 1.1, { z: 1.25 }));
  for (const [x, z, size, facing, seed, turn] of [[-3.7, 2.0, 1.5, 1, 28, -0.22], [-1.7, 2.35, 1.3, -1, 29, -0.28], [0.9, 2.15, 1.2, 1, 30, -0.2]]) {
    world.add(standingLayer(cutPaperTexture(renderer, 560, 400, seed, drawSheep(facing)), size, size * 400 / 560, { x, y: pageHeight(x) - 0.03, z, turn }));
  }
  world.add(standingLayer(cutPaperTexture(renderer, 2600, 200, 31, drawGrass), 11.2, 0.86, { z: 2.75 }));

  // lights
  scene.add(new THREE.HemisphereLight(0x5a6075, 0x14100c, 0.55));
  const lamp = new THREE.SpotLight(0xffd9b0, 5.4, 0, 0.48, 1.0, 0);
  lamp.position.set(-13.5, 7.6, 8.5);
  lamp.target.position.set(-0.4, 2.4, -0.9);
  lamp.castShadow = true;
  lamp.shadow.mapSize.set(4096, 4096);
  lamp.shadow.camera.near = 6; lamp.shadow.camera.far = 40;
  lamp.shadow.radius = 5;
  lamp.shadow.bias = -0.0016;
  lamp.shadow.normalBias = 0;
  scene.add(lamp, lamp.target);
  const moon = new THREE.DirectionalLight(0x9eb0e6, 0.75);
  moon.position.set(9, 11, -12);
  moon.target.position.set(0, 1, 0);
  moon.castShadow = false; // its shadows criss-crossed the lamp's and made the page hard to read
  moon.shadow.mapSize.set(2048, 2048);
  Object.assign(moon.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 40 });
  moon.shadow.radius = 3;
  moon.shadow.bias = -0.002;
  moon.shadow.normalBias = 0;
  scene.add(moon, moon.target);
  // a faint cool light on the paper moon only, so it glows pale against the dark
  const moonGlow = new THREE.SpotLight(0xb8c8ff, 2.2, 0, 0.13, 0.9, 0);
  moonGlow.position.set(9, 12, 14);
  moonGlow.target.position.set(3.1, 7.6, -4.35);
  scene.add(moonGlow, moonGlow.target);

  camera.fov = 40;
  camera.aspect = stage.FRAME_WIDTH / stage.FRAME_HEIGHT;
  camera.near = 0.5; camera.far = 150;
  camera.updateProjectionMatrix();

  // A picture of distance from the camera (near = dark, far = light), used afterwards to blur what is
  // far from the cottage the way a camera lens would. Cut-outs keep their holes.
  const DISTANCE_NEAR = 12, DISTANCE_FAR = 40;
  window.drawDistancePicture = () => {
    const swapped = [];
    scene.traverse((object) => {
      if (!object.isMesh) return;
      const original = object.material;
      object.material = new THREE.ShaderMaterial({
        side: THREE.DoubleSide,
        uniforms: { map: { value: original.map ?? null }, useMap: { value: original.map && original.alphaTest ? 1 : 0 }, alphaTest: { value: original.alphaTest || 0 }, near: { value: DISTANCE_NEAR }, far: { value: DISTANCE_FAR } },
        vertexShader: 'varying vec2 vUv; varying float vDistance; void main() { vUv = uv; vec4 viewPosition = modelViewMatrix * vec4(position, 1.0); vDistance = -viewPosition.z; gl_Position = projectionMatrix * viewPosition; }',
        fragmentShader: 'uniform sampler2D map; uniform float useMap; uniform float alphaTest; uniform float near; uniform float far; varying vec2 vUv; varying float vDistance; void main() { if (useMap > 0.5 && texture2D(map, vUv).a < alphaTest) discard; float share = clamp((vDistance - near) / (far - near), 0.0, 1.0); gl_FragColor = vec4(vec3(share), 1.0); }',
      });
      swapped.push([object, original]);
    });
    const background = scene.background, toneMapping = renderer.toneMapping, colourSpace = renderer.outputColorSpace;
    scene.background = new THREE.Color(1, 1, 1);
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
    renderer.render(scene, camera);
    const picture = renderer.domElement.toDataURL('image/png');
    scene.background = background; renderer.toneMapping = toneMapping; renderer.outputColorSpace = colourSpace;
    for (const [object, original] of swapped) { object.material.dispose(); object.material = original; }
    return { picture, near: DISTANCE_NEAR, far: DISTANCE_FAR };
  };

  return {
    start: 0,
    end: 1,
    pose() {
      camera.position.set(0.3, 21.5, 13.5);
      camera.lookAt(0.0, 2.4, -1.4);
    },
  };
}
