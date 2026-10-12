// What this does: the air and the movement in a cinema page: dust floating in a beam of light, the
// beam itself, puffs of dust where something heavy lands, smoke from chimneys, and coins raining
// down and settling. Each effect is built once and set for any moment by set(...) or pose(t), so a
// frame can be drawn on its own (nothing remembers earlier frames).

import { THREE, canvasTexture } from '../stage/cinema-stage.js';
import { seededRandom, clamp01, lerp } from './cinema-kit.js';
import { coin } from './models.js';

function softDot(inner = 'rgba(255,240,215,1)', outer = 'rgba(255,240,215,0)') {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 64;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, inner); g.addColorStop(0.35, inner.replace(/[\d.]+\)$/, '0.5)')); g.addColorStop(1, outer);
  ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64);
  return canvasTexture(canvas);
}

// ------------------------------------------------------------------------------- dust motes
// Specks floating in a box (min, max corners), drifting slowly and twinkling; brighter near `glowAt`
// (the beam) if given. size in world units.
export class Motes {
  constructor(scene, { count = 260, min = [-4, 0, -12], max = [4, 8, -2], size = 0.035, colour = 0xfff0d8, seed = 3, opacity = 0.85 } = {}) {
    const random = seededRandom(seed);
    this.base = []; this.phase = [];
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const p = [lerp(min[0], max[0], random()), lerp(min[1], max[1], random()), lerp(min[2], max[2], random())];
      this.base.push(p); this.phase.push([random() * 6.28, random() * 6.28, 0.3 + random() * 0.7]);
      positions.set(p, i * 3);
    }
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.material = new THREE.PointsMaterial({ map: softDot(), size, sizeAttenuation: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, color: colour, opacity });
    this.points = new THREE.Points(this.geometry, this.material);
    this.points.frustumCulled = false;
    this.height = max[1] - min[1];
    this.min = min;
    scene.add(this.points);
  }
  set(t, { visible = true, opacity } = {}) {
    this.points.visible = visible;
    if (!visible) return;
    if (opacity !== undefined) this.material.opacity = opacity;
    const positions = this.geometry.attributes.position.array;
    for (let i = 0; i < this.base.length; i++) {
      const [x, y, z] = this.base[i], [a, b, speed] = this.phase[i];
      positions[i * 3] = x + 0.18 * Math.sin(t * 0.21 * speed + a);
      positions[i * 3 + 1] = this.min[1] + ((y - this.min[1] + t * 0.05 * speed) % this.height);
      positions[i * 3 + 2] = z + 0.18 * Math.sin(t * 0.17 * speed + b);
    }
    this.geometry.attributes.position.needsUpdate = true;
  }
}

// ------------------------------------------------------------------------------- light beam
// A soft shaft of light from `from` to `to` (world points), `width` across at the far end. Glows
// additively, faintly streaked, slowly shimmering.
let beamTexture = null;
function beamGradient() {
  if (!beamTexture) {
    const canvas = document.createElement('canvas'); canvas.width = 128; canvas.height = 256;
    const ctx = canvas.getContext('2d');
    const across = ctx.createLinearGradient(0, 0, 128, 0);
    across.addColorStop(0, 'rgba(255,255,255,0)'); across.addColorStop(0.5, 'rgba(255,255,255,1)'); across.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = across; ctx.fillRect(0, 0, 128, 256);
    ctx.globalCompositeOperation = 'destination-in';
    const along = ctx.createLinearGradient(0, 0, 0, 256);
    along.addColorStop(0, 'rgba(0,0,0,0.9)'); along.addColorStop(0.7, 'rgba(0,0,0,0.5)'); along.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = along; ctx.fillRect(0, 0, 128, 256);
    ctx.globalCompositeOperation = 'source-over';
    const random = seededRandom(17);
    for (let i = 0; i < 22; i++) { ctx.fillStyle = `rgba(0,0,0,${0.08 + random() * 0.12})`; ctx.fillRect(random() * 128, 0, 2 + random() * 6, 256); }
    beamTexture = canvasTexture(canvas);
  }
  return beamTexture;
}
export class LightBeam {
  constructor(scene, { from, to, width = 2.5, startWidth = 0.6, colour = 0xffd9a0, strength = 0.22 } = {}) {
    this.from = new THREE.Vector3(...from); this.to = new THREE.Vector3(...to);
    const length = this.from.distanceTo(this.to);
    const geometry = new THREE.PlaneGeometry(1, length, 1, 1);
    const positions = geometry.attributes.position.array;
    // top edge (y = +length/2) narrow, bottom wide
    for (let i = 0; i < positions.length / 3; i++) positions[i * 3] *= positions[i * 3 + 1] > 0 ? startWidth : width;
    geometry.translate(0, -length / 2, 0);
    this.material = new THREE.MeshBasicMaterial({ map: beamGradient(), color: colour, transparent: true, opacity: strength, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false });
    this.mesh = new THREE.Mesh(geometry, this.material);
    this.mesh.position.copy(this.from);
    const direction = this.to.clone().sub(this.from).normalize();
    this.mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), direction);
    this.strength = strength;
    scene.add(this.mesh);
  }
  // faces the camera around its own axis, and shimmers a little
  set(t, camera, { strength } = {}) {
    const s = strength ?? this.strength;
    this.mesh.visible = s > 0.001;
    this.material.opacity = s * (0.92 + 0.08 * Math.sin(t * 0.7));
    const axis = this.to.clone().sub(this.from).normalize();
    const toCamera = camera.position.clone().sub(this.from);
    const side = new THREE.Vector3().crossVectors(axis, toCamera).normalize();
    const normal = new THREE.Vector3().crossVectors(side, axis).normalize();
    const basis = new THREE.Matrix4().makeBasis(side, axis.clone().negate(), normal);
    this.mesh.quaternion.setFromRotationMatrix(basis);
  }
}

// -------------------------------------------------------------------------------- dust burst
export class DustBurst {
  constructor(scene, { count = 26, seed = 7, colour = 'rgba(120,112,100,0.9)' } = {}) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
    g.addColorStop(0, colour); g.addColorStop(0.5, 'rgba(105,98,88,0.45)'); g.addColorStop(1, 'rgba(90,85,78,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
    const texture = canvasTexture(canvas);
    const random = seededRandom(seed);
    this.puffs = Array.from({ length: count }, () => {
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false, opacity: 0 }));
      sprite.visible = false; scene.add(sprite);
      return { sprite, across: random() * 2 - 1, rise: 0.4 + random() * 0.9, spread: 0.8 + random() * 1.6, size: 0.7 + random() * 0.9, delay: random() * 0.08, depth: random() * 2 - 1 };
    });
  }
  // origin: [x, y, z] of the landing; width: how wide; age: seconds since landing; scale: size
  set({ origin, width = 1, age, scale = 1 }) {
    for (const puff of this.puffs) {
      const a = age - puff.delay;
      if (a < 0 || a > 1.2) { puff.sprite.visible = false; continue; }
      const k = 1 - Math.exp(-a * 4.5);
      puff.sprite.visible = true;
      puff.sprite.position.set(origin[0] + puff.across * width * 0.5 + Math.sign(puff.across) * puff.spread * k * scale,
        origin[1] + puff.rise * k * scale, origin[2] + puff.depth * 0.5 * scale);
      const size = scale * puff.size * (0.5 + 1.6 * k);
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.opacity = 0.5 * (1 - a / 1.2) ** 1.5;
    }
  }
  hide() { for (const puff of this.puffs) puff.sprite.visible = false; }
}

// ------------------------------------------------------------------------------------- smoke
export class Smoke {
  constructor(scene, { count = 10, life = 2.6, seed = 5, colour = [176, 174, 168] } = {}) {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
    const ctx = canvas.getContext('2d');
    const g = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
    g.addColorStop(0, `rgba(${colour},0.9)`); g.addColorStop(0.55, `rgba(${colour},0.45)`); g.addColorStop(1, `rgba(${colour},0)`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
    const texture = canvasTexture(canvas);
    const random = seededRandom(seed);
    this.life = life;
    this.puffs = Array.from({ length: count }, (_, i) => {
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false, opacity: 0 }));
      sprite.visible = false; scene.add(sprite);
      return { sprite, offset: (i / count) * life, sway: random() * Math.PI * 2, size: 0.8 + random() * 0.5 };
    });
  }
  // origin [x,y,z]: chimney top; puffs are born between `from` and `until`
  set({ t, origin, from = -Infinity, until = Infinity, scale = 1, wind = 0.5 }) {
    for (const puff of this.puffs) {
      const born = puff.offset + Math.floor((t - puff.offset) / this.life) * this.life;
      const age = t - born;
      if (born < from || born > until || age < 0 || age > this.life) { puff.sprite.visible = false; continue; }
      const k = age / this.life;
      puff.sprite.visible = true;
      puff.sprite.position.set(origin[0] + scale * (wind * k + 0.12 * Math.sin(puff.sway + age * 2.2)), origin[1] + scale * 1.7 * k, origin[2]);
      const size = scale * puff.size * (0.35 + 1.1 * k);
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.opacity = 0.5 * Math.min(1, age / 0.25) * (1 - k);
    }
  }
  hide() { for (const puff of this.puffs) puff.sprite.visible = false; }
}

// --------------------------------------------------------------------------------- coin rain
// Coins dropped from above onto a floor (y = floorY) around `centre`, spread over `radius`; each
// lands at its own time between `start` and `start + spread`, bounces, spins down and lies flat.
// pose(t) puts them where they are at moment t.
export class CoinRain {
  constructor(scene, { count = 18, centre = [0, 0, 0], radius = 0.8, floorY = 0, height = 6, start = 0, spread = 0.9, coinRadius = 0.13, seed = 9, stack = false } = {}) {
    const random = seededRandom(seed);
    this.coins = Array.from({ length: count }, (_, i) => {
      const c = coin({ radius: coinRadius, thickness: coinRadius * 0.18 });
      scene.add(c.group);
      const angle = random() * Math.PI * 2, distance = Math.sqrt(random()) * radius;
      const restY = stack ? floorY + coinRadius * 0.18 * (i + 0.5) : floorY + coinRadius * 0.09 + random() * 0.002;
      return {
        group: c.group, land: start + (stack ? i / count : random()) * spread,
        x: centre[0] + (stack ? (random() - 0.5) * 0.04 : Math.cos(angle) * distance), z: centre[2] + (stack ? (random() - 0.5) * 0.04 : Math.sin(angle) * distance),
        restY, height: height * (0.8 + random() * 0.4), spin: 6 + random() * 8, tilt0: random() * Math.PI, yaw: random() * Math.PI * 2,
      };
    });
  }
  pose(t, { visible = true } = {}) {
    for (const c of this.coins) {
      const fall = Math.sqrt(2 * c.height / 30); // falling under a strong "gravity" so it reads fast
      const age = t - c.land;
      if (!visible || age < -fall) { c.group.visible = false; continue; }
      c.group.visible = true;
      if (age < 0) {
        const k = 1 + age / fall;
        c.group.position.set(c.x, c.restY + c.height * (1 - k * k), c.z);
        c.group.rotation.set(c.tilt0 + age * c.spin, c.yaw, 0);
        continue;
      }
      const bounce = 0.12 * Math.exp(-age / 0.08) * Math.abs(Math.sin(Math.PI * age / 0.11));
      const wobble = 0.5 * Math.exp(-age / 0.18) * Math.cos(age * 40);
      c.group.position.set(c.x, c.restY + bounce, c.z);
      c.group.rotation.set(wobble * 0.6, c.yaw + age * 0.5 * Math.exp(-age * 3), wobble * 0.4);
    }
  }
}
