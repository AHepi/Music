// What this does: the live effects and helpers shared by the pit village clips (lockout-test.js, log 29;
// notice-corner.js, log 31): a soft additive glow, the brazier's flames and sparks, the painting's sky
// colour, soft contact shadows under props, the ground height under a spot, and which way a flat thing
// faces. Everything here depends only on the moment t, so frames can be drawn in any order.
import { THREE, seededRandom } from './cinema-kit.js';
import { canvasTexture } from '../stage/cinema-stage.js';

// a soft warm glow (fire, lamps), drawn additively
export function glow(colour, size, opacity) {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.25, 'rgba(255,255,255,0.45)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: canvasTexture(canvas), color: colour, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  sprite.scale.set(size, size, 1);
  return sprite;
}

// a flame tongue, solid like the painting's shapes: a red-orange body, an orange-yellow middle and a
// pale yellow heart, each inside the last, with ragged, licking edges and a bent tip that fades out.
// `seed` gives each of a few shapes its own wobble and bend, so no two tongues match.
export function flamePicture(seed) {
  const random = seededRandom(seed);
  const canvas = document.createElement('canvas'); canvas.width = 64; canvas.height = 128;
  const ctx = canvas.getContext('2d');
  ctx.filter = 'blur(1.2px)';
  const bend = (random() - 0.5) * 22, wobble = Array.from({ length: 12 }, () => random() - 0.5);
  const tongue = (scale, top, colourTop, colourBottom) => {
    const g = ctx.createLinearGradient(0, 128, 0, top);
    g.addColorStop(0, colourBottom); g.addColorStop(0.55, colourTop); g.addColorStop(1, colourTop.replace(/[\d.]+\)$/, '0)'));
    ctx.fillStyle = g;
    const w = 26 * scale, rows = 24, left = [], right = [];
    for (let i = 0; i <= rows; i++) {
      const k = i / rows, y = top + (124 - top) * k;                       // tip (k = 0) to root
      const half = w * Math.sin(Math.PI * Math.min(1, k * 0.95 + 0.05) * 0.62) * (0.75 + 0.25 * k);
      const lick = 3.5 * scale * wobble[Math.floor(k * 11)] * (1 - k);     // ragged edges, most near the tip
      const x = 32 + bend * (1 - k) * (1 - k);
      left.push([x - half + lick, y]); right.push([x + half + lick * 0.6, y]);
    }
    ctx.beginPath();
    ctx.moveTo(...left[0]);
    for (const p of right) ctx.lineTo(...p);
    for (const p of left.reverse()) ctx.lineTo(...p);
    ctx.fill();
  };
  tongue(1.0, 4, 'rgba(214,62,14,1)', 'rgba(255,120,30,1)');
  tongue(0.66, 34, 'rgba(255,150,40,1)', 'rgba(255,200,80,1)');
  tongue(0.36, 66, 'rgba(255,226,140,1)', 'rgba(255,246,200,1)');
  return canvasTexture(canvas);
}

// the brazier's flames: tongues standing on the coals, each flickering in height, leaning and
// swaying, with a brighter core added on top
export class Flames {
  constructor(scene, base, { seed = 17 } = {}) {
    const random = seededRandom(seed), pictures = [flamePicture(3), flamePicture(8), flamePicture(14)];
    this.base = base;
    this.tongues = [[0, 0, 0.46, 0.16], [0.1, -0.04, 0.34, 0.12], [-0.09, 0.05, 0.38, 0.13], [0.04, 0.11, 0.3, 0.11],
      [-0.06, -0.1, 0.29, 0.11], [0.14, 0.07, 0.22, 0.09], [-0.14, -0.02, 0.25, 0.1], [0.06, -0.12, 0.2, 0.09], [-0.03, 0.14, 0.24, 0.1]]
      .map(([dx, dz, height, width], i) => {
        const picture = pictures[i % pictures.length];
        const body = new THREE.Sprite(new THREE.SpriteMaterial({ map: picture, transparent: true, depthWrite: false, fog: false }));
        const core = new THREE.Sprite(new THREE.SpriteMaterial({ map: picture, transparent: true, depthWrite: false, fog: false, blending: THREE.AdditiveBlending, opacity: 0.35, color: 0xffd090 }));
        body.center.set(0.5, 0.04); core.center.set(0.5, 0.04);
        scene.add(body, core);
        // sizes, leans and how deep in the coals each stands all differ, so they don't form a row
        const size = 0.7 + random() * 0.6;
        return { body, core, dx, dz, height: height * size, width: width * (0.8 + random() * 0.4), sink: random() * 0.05,
          speed: 6 + random() * 8, phase: random() * 6.28, lean: (random() - 0.5) * 0.5 };
      });
  }
  set(t) {
    for (const f of this.tongues) {
      const flicker = 0.72 + 0.18 * Math.sin(t * f.speed + f.phase) + 0.1 * Math.sin(t * f.speed * 2.3 + f.phase * 1.7);
      const x = this.base.x + f.dx + 0.015 * Math.sin(t * 5.1 + f.phase);
      f.body.position.set(x, this.base.y - f.sink, this.base.z + f.dz);
      f.body.scale.set(f.width * (0.9 + 0.1 * flicker), f.height * flicker, 1);
      f.body.material.rotation = f.lean + 0.12 * Math.sin(t * 3.3 + f.phase) + 0.05 * Math.sin(t * 7.9 + f.phase * 2);
      f.core.position.copy(f.body.position);
      f.core.scale.set(f.width * 0.5, f.height * flicker * 0.55, 1);
      f.core.material.rotation = f.body.material.rotation;
    }
  }
}

// sparks rising from the coals: each lives under a second and a half, cooling and fading as it rises;
// each spark's place depends only on the moment t
export class Sparks {
  constructor(scene, origin, { count = 28, seed = 11 } = {}) {
    const random = seededRandom(seed);
    this.origin = origin;
    this.sparks = Array.from({ length: count }, () => ({ offset: random() * 2, life: 0.6 + random() * 0.9, rise: 0.35 + random() * 0.4,
      drift: (random() - 0.5) * 0.3, phase: random() * 6.28, spread: [(random() - 0.5) * 0.3, (random() - 0.5) * 0.3] }));
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    this.geometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 32;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(255,255,255,0.6)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 32, 32);
    // additive, so a spark faded to black is gone
    this.material = new THREE.PointsMaterial({ map: canvasTexture(canvas), size: 0.035, sizeAttenuation: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true, fog: false });
    this.points = new THREE.Points(this.geometry, this.material);
    this.points.frustumCulled = false;
    scene.add(this.points);
  }
  set(t) {
    const positions = this.geometry.attributes.position.array, colours = this.geometry.attributes.color.array;
    this.sparks.forEach((s, i) => {
      const age = (t + s.offset) % s.life, k = age / s.life;
      positions[i * 3] = this.origin.x + s.spread[0] + s.drift * k + 0.04 * Math.sin(t * 6 + s.phase) * k;
      positions[i * 3 + 1] = this.origin.y + s.rise * Math.sqrt(k);
      positions[i * 3 + 2] = this.origin.z + s.spread[1] + 0.03 * Math.cos(t * 5 + s.phase) * k;
      const bright = Math.pow(1 - k, 1.5) * Math.min(1, age / 0.06);
      colours[i * 3] = bright; colours[i * 3 + 1] = bright * (0.75 - 0.35 * k); colours[i * 3 + 2] = bright * (0.35 - 0.3 * k);
    });
    this.geometry.attributes.position.needsUpdate = true;
    this.geometry.attributes.color.needsUpdate = true;
  }
}

// the painting's sky colour (linear light): the average of its top fifth
export function paintedSkyColour(texture) {
  const image = texture.image, canvas = new OffscreenCanvas(32, 32), context = canvas.getContext('2d');
  context.drawImage(image, 0, 0, image.width, image.height * 0.2, 0, 0, 32, 32);
  const data = context.getImageData(0, 0, 32, 32).data, sum = [0, 0, 0];
  const toLinear = (value) => { const c = value / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  for (let i = 0; i < data.length; i += 4) for (let c = 0; c < 3; c++) sum[c] += toLinear(data[i + c]);
  return new THREE.Color(sum[0] / 1024, sum[1] / 1024, sum[2] / 1024);
}

// a soft dark patch lying on the ground under a prop: once the camera moves, the road round the near
// props wears the behind painting, which has no shadows of them, so this stands in for the painted one
export function contactShadow(width, depth) {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,0.85)'); g.addColorStop(0.55, 'rgba(0,0,0,0.55)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
  const patch = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), new THREE.MeshBasicMaterial({
    map: canvasTexture(canvas), color: 0x0b0806, transparent: true, opacity: 0, depthWrite: false, fog: false,
    polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  patch.rotation.x = -Math.PI / 2;
  const holder = new THREE.Group();
  holder.add(patch);
  return { holder, material: patch.material };
}

// the height of the set's surface under (x, z), leaving out some objects (the props standing there)
export function groundUnder(group, x, z, leaveOut) {
  const skip = new Set();
  for (const o of leaveOut) o.traverse((c) => skip.add(c));
  const hits = new THREE.Raycaster(new THREE.Vector3(x, 30, z), new THREE.Vector3(0, -1, 0)).intersectObject(group, true);
  const hit = hits.find((h) => !skip.has(h.object) && h.object.visible);
  return hit ? hit.point.y : 0;
}

// the direction a flat thing faces (the average of its normals that face `towards`)
export function facingOf(mesh, towards) {
  mesh.updateMatrixWorld(true);
  const normals = mesh.geometry.attributes.normal, matrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
  const sum = new THREE.Vector3(), n = new THREE.Vector3();
  for (let i = 0; i < normals.count; i++) {
    n.fromBufferAttribute(normals, i).applyMatrix3(matrix).normalize();
    if (n.dot(towards) > 0.5) sum.add(n);
  }
  return sum.normalize();
}
