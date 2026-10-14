// What this does: the plan 3 test clip (log 29), 12 seconds, no narration: Britain, 1926, a pit
// village street at dusk during the miners' lockout. The street, the cottages, the pithead and the
// props are real 3D (built in Blender: paper-film/blender/pit-village/), drawn once from the main
// camera (the plate), repainted in the series' painted style by Flux, and the painting is shone back
// onto the same 3D shapes (projected-set.js), so the camera can move without anything tearing.
//   0-2 s     fade in on the painted street: BRITAIN 1926
//   2-7.2 s   the camera moves up the street (one move: 1.4 m forward, a little right and up, turning
//             5 degrees right and 1.5 down, narrowing its lens from 40 to 26 degrees), ending with the
//             notice board near the middle, the colliery's sign and the pithead gone off the left.
//             The turn is kept small so the frame never leaves the painted area (the narrower lens
//             is what lets it turn at all), and most of the push in is the lens: a lens change
//             uncovers nothing the plate didn't see.
//   7.3 s     cut to the notice board, close, square to it (one slow push in)
//   8-11 s    LOCKED OUT / FROM 1 MAY 1926 above the notice
//   11-12 s   fade out
// Three paintings are shone onto the set: the painting itself; a "behind" painting of the same view
// with the near props painted out (Flux), for the road and walls those props hid, uncovered as the
// camera moves; and the painted sky alone (paintedSkyOnly) on a far card, so the sky uncovered behind
// the pithead is painted sky. The notice board keeps its own sharp surfaces (the painter garbled the
// small print), matched in colour to the painting where it stands.
// Live on top: flames on the brazier's coals, sparks, smoke from the brazier and some chimneys, and
// the fire's flickering light on the surfaces the painting doesn't cover (the notice board).
// Views (PAPER_FILM_QUERY=view=NAME): move (default), projector (holds the first frame), moved
// (holds the end of the street move), notice (holds the end of the close shot), weights (the end of
// the street move: orange wears the painting, green the behind painting, blue its own surface),
// weights-move (the same colours through the whole clip).
// Use: cd paper-pop-up-film-kit && node paper-film/tools/render-paper-film.mjs lockout-test OUT --stills 1.5 5 7 9
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE, smooth, clamp01, seededRandom } from './cinema-kit.js';
import { loadTexture, canvasTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';
import { loadProjector, projectPaintingOnto, paintedSkyOnly } from './projected-set.js';
import { Smoke } from './effects.js';
import { placeTitle, hook } from './graphics.js';

const SET = '/assets/models/pit-village';
const VIEW = new URLSearchParams(location.search).get('view') ?? 'move';
// the near props painted out of the behind painting (names as exported, before Blender's .001)
const NEAR_PROPS = ['handcart', 'coal-sacks', 'coal-pile', 'wooden-pail', 'hurricane-lantern', 'spade', 'brazier', 'dustbins', 'notice-on-board', 'Cube'];
const NEAR = 16;   // metres from the projector: further copies of the same props stay in the behind painting

// a soft warm glow (fire, lamps), drawn additively
function glow(colour, size, opacity) {
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
// pale yellow heart, each a pointed teardrop inside the last, only the tip fading out
function flamePicture() {
  const canvas = document.createElement('canvas'); canvas.width = 64; canvas.height = 128;
  const ctx = canvas.getContext('2d');
  ctx.filter = 'blur(1px)';
  const tongue = (scale, top, colourTop, colourBottom) => {
    const g = ctx.createLinearGradient(0, 128, 0, top);
    g.addColorStop(0, colourBottom); g.addColorStop(0.65, colourTop); g.addColorStop(1, colourTop.replace(/[\d.]+\)$/, '0)'));
    ctx.fillStyle = g;
    const w = 26 * scale;
    ctx.beginPath();
    ctx.moveTo(32, top);
    ctx.bezierCurveTo(32 + w * 0.3, top + 30, 32 + w, 72, 32 + w * 0.85, 104); ctx.bezierCurveTo(32 + w * 0.6, 124, 32 - w * 0.6, 124, 32 - w * 0.85, 104);
    ctx.bezierCurveTo(32 - w, 72, 32 - w * 0.3, top + 30, 32, top);
    ctx.fill();
  };
  tongue(1.0, 4, 'rgba(214,62,14,1)', 'rgba(255,120,30,1)');
  tongue(0.66, 34, 'rgba(255,150,40,1)', 'rgba(255,200,80,1)');
  tongue(0.36, 66, 'rgba(255,226,140,1)', 'rgba(255,246,200,1)');
  return canvasTexture(canvas);
}

// the brazier's flames: tongues standing on the coals, each flickering in height, leaning and
// swaying, with a brighter core added on top
class Flames {
  constructor(scene, base, { seed = 17 } = {}) {
    const random = seededRandom(seed), picture = flamePicture();
    this.base = base;
    this.tongues = [[0, 0, 0.46, 0.16], [0.1, -0.04, 0.34, 0.12], [-0.09, 0.05, 0.38, 0.13], [0.04, 0.11, 0.3, 0.11],
      [-0.06, -0.1, 0.29, 0.11], [0.14, 0.07, 0.22, 0.09], [-0.14, -0.02, 0.25, 0.1], [0.06, -0.12, 0.2, 0.09], [-0.03, 0.14, 0.24, 0.1]]
      .map(([dx, dz, height, width]) => {
        const body = new THREE.Sprite(new THREE.SpriteMaterial({ map: picture, transparent: true, depthWrite: false, fog: false }));
        const core = new THREE.Sprite(new THREE.SpriteMaterial({ map: picture, transparent: true, depthWrite: false, fog: false, blending: THREE.AdditiveBlending, opacity: 0.35, color: 0xffd090 }));
        body.center.set(0.5, 0.04); core.center.set(0.5, 0.04);
        scene.add(body, core);
        return { body, core, dx, dz, height, width, speed: 7 + random() * 6, phase: random() * 6.28, lean: (random() - 0.5) * 0.2 };
      });
  }
  set(t) {
    for (const f of this.tongues) {
      const flicker = 0.72 + 0.18 * Math.sin(t * f.speed + f.phase) + 0.1 * Math.sin(t * f.speed * 2.3 + f.phase * 1.7);
      const x = this.base.x + f.dx + 0.015 * Math.sin(t * 5.1 + f.phase);
      f.body.position.set(x, this.base.y, this.base.z + f.dz);
      f.body.scale.set(f.width * (0.9 + 0.1 * flicker), f.height * flicker, 1);
      f.body.material.rotation = f.lean + 0.08 * Math.sin(t * 3.3 + f.phase);
      f.core.position.copy(f.body.position);
      f.core.scale.set(f.width * 0.5, f.height * flicker * 0.55, 1);
      f.core.material.rotation = f.body.material.rotation;
    }
  }
}

// sparks rising from the coals: each lives under a second and a half, cooling and fading as it rises;
// each spark's place depends only on the moment t
class Sparks {
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
function paintedSkyColour(texture) {
  const image = texture.image, canvas = new OffscreenCanvas(32, 32), context = canvas.getContext('2d');
  context.drawImage(image, 0, 0, image.width, image.height * 0.2, 0, 0, 32, 32);
  const data = context.getImageData(0, 0, 32, 32).data, sum = [0, 0, 0];
  const toLinear = (value) => { const c = value / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  for (let i = 0; i < data.length; i += 4) for (let c = 0; c < 3; c++) sum[c] += toLinear(data[i + c]);
  return new THREE.Color(sum[0] / 1024, sum[1] / 1024, sum[2] / 1024);
}

// a soft dark patch lying on the ground under a prop: once the camera moves, the road round the near
// props wears the behind painting, which has no shadows of them, so this stands in for the painted one
function contactShadow(width, depth) {
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
function groundUnder(group, x, z, leaveOut) {
  const skip = new Set();
  for (const o of leaveOut) o.traverse((c) => skip.add(c));
  const hits = new THREE.Raycaster(new THREE.Vector3(x, 30, z), new THREE.Vector3(0, -1, 0)).intersectObject(group, true);
  const hit = hits.find((h) => !skip.has(h.object) && h.object.visible);
  return hit ? hit.point.y : 0;
}

// the direction a flat thing faces (the average of its normals that face `towards`)
function facingOf(mesh, towards) {
  mesh.updateMatrixWorld(true);
  const normals = mesh.geometry.attributes.normal, matrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
  const sum = new THREE.Vector3(), n = new THREE.Vector3();
  for (let i = 0; i < normals.count; i++) {
    n.fromBufferAttribute(normals, i).applyMatrix3(matrix).normalize();
    if (n.dot(towards) > 0.5) sum.add(n);
  }
  return sum.normalize();
}

const page = {
  async build(kit) {
    // dusk: cool sky light, warm lamps; the painting carries the light, the lamps only touch the
    // surfaces the plate never saw and the notice board's own surfaces
    kit.lightRig({ keyColour: 0xffc48a, keyShare: 0.45, keyFrom: [1, 2.4, -10.4], keyTarget: [0, 0, -14], fillSky: 0x50637e, fillGround: 0x1c1712,
      fillShare: 0.35, haze: 0x1a2330, hazeDensity: 0.008, shadowBox: 14, shadowSoftness: 6, background: 0x0e141c, reflections: 0.2 });
    kit.lights.key.castShadow = false;

    const set = await loadModel(`${SET}/lockout-set.glb`);
    const signs = await loadModel(`${SET}/lockout-signs.glb`);
    const everything = new THREE.Group();
    everything.add(set, signs);
    kit.scene.add(everything);
    everything.updateMatrixWorld(true);
    const dome = set.getObjectByName('sky_dome');   // past the film camera's reach; the sky card stands in
    if (dome) dome.visible = false;
    const projector = await loadProjector(`${SET}/lockout-camera.json`);
    const [painting, behindPainting] = await Promise.all([loadTexture(`${SET}/lockout-painted.jpg`), loadTexture(`${SET}/lockout-behind.jpg`)]);

    // the near props (painted out of the behind painting) and the notice board's materials
    const nearProps = [];
    const centre = new THREE.Vector3();
    for (const root of [...set.children, ...signs.children]) {
      if (!NEAR_PROPS.some((name) => root.name.startsWith(name))) continue;
      new THREE.Box3().setFromObject(root).getCenter(centre);
      if (centre.distanceTo(projector.position) < NEAR) nearProps.push(root);
    }
    const boardMaterials = new Set();
    for (const root of signs.children) {
      if (!root.name.startsWith('notice-on-board') && !root.name.startsWith('Cube')) continue;
      root.traverse((o) => { if (o.isMesh) for (const m of [o.material].flat()) boardMaterials.add(m.name); });
    }
    boardMaterials.delete('notice-paper');
    let paper = null;
    signs.traverse((o) => { if (o.isMesh && [o.material].flat().some((m) => m.name === 'notice-paper')) paper = o; });
    if (paper?.material.map) paper.material.map.anisotropy = 8;   // the small print stays crisp at a slant

    // the fire's light, made before the paintings are shone on so the colour match includes it: it
    // only shows on surfaces the painting doesn't cover (the notice board, and anything uncovered as
    // the camera moves), so they are warm like the painted firelight round them, and it flickers
    const fireLight = new THREE.PointLight(0xff9a50, 4, 9, 2);
    fireLight.position.set(0.95, 2.08, -10.4);
    kit.scene.add(fireLight);

    const projection = projectPaintingOnto(kit, everything, painting, projector, {
      ownSurface: ['notice-paper', 'colliery-board-paint', ...[...boardMaterials].map((name) => [name, 'notice-paper'])],
      behind: { painting: behindPainting, hide: nearProps },
      stretch: [2.0, 4.0],
    });

    // the sky: a card 300 m out, square to the projector and wider than its frame, wearing the painted
    // sky alone (nothing nearer than 1 km), so the sky uncovered behind the pithead is painted sky
    const skyDistance = 300;
    const skyHeight = 2 * skyDistance * Math.tan(THREE.MathUtils.degToRad(projector.fov / 2)) * 1.6;
    const skyCard = new THREE.Mesh(new THREE.PlaneGeometry(skyHeight * 1.5, skyHeight), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }));
    skyCard.material.name = 'sky card';
    skyCard.position.copy(projector.position).addScaledVector(new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion), skyDistance);
    skyCard.quaternion.copy(projector.quaternion);
    const skyGroup = new THREE.Group();
    skyGroup.add(skyCard);
    kit.scene.add(skyGroup);
    const skyColour = paintedSkyColour(painting);
    const skyProjection = projectPaintingOnto(kit, skyGroup, paintedSkyOnly(projection, painting), projector, { calibrate: false, averageColour: skyColour, darken: 1, tint: 1, matte: false });
    // where the painting doesn't reach, the card shows the painted sky's average colour exactly
    skyProjection.materials[0].color.setRGB(skyColour.r / skyProjection.fallbackTint.x, skyColour.g / skyProjection.fallbackTint.y, skyColour.b / skyProjection.fallbackTint.z);
    kit.scene.background = skyColour.clone();
    if (VIEW === 'weights' || VIEW === 'weights-move') { projection.showWeights(true); skyProjection.showWeights(true); }

    // soft contact shadows under the coal sacks and the handcart (placed in assemble_lockout.py:
    // Blender (x, y, turn) -> three.js (x, -y), turned about y), faded in as the move begins
    const shadows = [[-0.2, 8.4, 18, 1.5, 1.9], [-1.75, 9.6, -70, 1.9, 1.2]].map(([x, y, turn, width, depth]) => {
      const shadow = contactShadow(width, depth);
      shadow.holder.position.set(x, groundUnder(set, x, -y, nearProps) + 0.012, -y);
      shadow.holder.rotation.y = THREE.MathUtils.degToRad(turn);
      kit.scene.add(shadow.holder);
      return shadow;
    });

    // where things are, in three.js space (Blender x, y, z -> x, z, -y)
    const coals = new THREE.Vector3(0.95, 1.62, -10.4);        // the top of the coal bed, where the flames stand
    const brazierTop = new THREE.Vector3(0.95, 1.78, -10.4);   // the middle of the flames
    const notice = new THREE.Box3().setFromObject(paper).getCenter(new THREE.Vector3());
    const noticeFacing = facingOf(paper, projector.position.clone().sub(notice).normalize());
    const chimneyTops = [[-7.65, 11.74, 8.5], [-7.65, 12.37, 17.5], [7.65, 12.05, 17.5], [7.65, 12.68, 26.5], [-7.65, 13.31, 31.0]]
      .map(([x, z, y]) => new THREE.Vector3(x, z + 0.4, -y));

    // the fire: flames on the coals, a flickering glow, sparks, smoke, and its light
    const fireGlow = glow(0xff9a40, 1.5, 0.4); fireGlow.position.copy(brazierTop); kit.scene.add(fireGlow);
    const flames = new Flames(kit.scene, coals);
    const sparks = new Sparks(kit.scene, coals.clone().add(new THREE.Vector3(0, 0.08, 0)));
    // smoke sprites are not lit, so their colour is set dark enough to sit in the dusk
    const brazierSmoke = new Smoke(kit.scene, { count: 14, life: 3.6, seed: 21, colour: [150, 146, 140] });
    for (const puff of brazierSmoke.puffs) puff.sprite.material.color.setRGB(0.5, 0.48, 0.46);
    const chimneySmoke = chimneyTops.map((top, i) => ({ top, effect: new Smoke(kit.scene, { count: 10, life: 4.2, seed: 31 + i, colour: [120, 126, 136] }) }));
    for (const c of chimneySmoke) for (const puff of c.effect.puffs) puff.sprite.material.color.setRGB(0.6, 0.62, 0.66);

    // shot 1: starts exactly where the plate was drawn from (with the film's 40-degree lens the frame
    // is the middle of the painting), then moves up the street
    const ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion).setY(0).normalize();
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(projector.quaternion).setY(0).normalize();
    const start = { position: projector.position.toArray(), target: projector.userData.target.toArray(), fov: 40, focus: 9 };
    const endPosition = projector.position.clone().addScaledVector(ahead, 1.4).addScaledVector(right, 0.3).add(new THREE.Vector3(0, 0.05, 0));
    // turned 5 degrees right (with the 26-degree lens the frame's right edge stays just inside the
    // painting) and 1.5 down: the board near the middle, the fire at the bottom, the coal sacks below
    // the frame, the colliery's sign and the pithead gone off the left
    const endLook = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion).applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(-5));
    endLook.applyAxisAngle(endLook.clone().cross(new THREE.Vector3(0, 1, 0)).normalize(), THREE.MathUtils.degToRad(-1.5));
    const end = { position: endPosition.toArray(), target: endPosition.clone().addScaledVector(endLook, 10).toArray(), fov: 26, focus: endPosition.distanceTo(notice) };
    // shot 2: square to the notice (it faces almost straight at the projector, so little is uncovered),
    // the paper a little below the middle to leave room for the words above it
    const closeAt = (distance) => notice.clone().addScaledVector(noticeFacing, distance).add(new THREE.Vector3(0, -0.1, 0));
    const closeTarget = notice.clone().add(new THREE.Vector3(0, 0.2, 0));
    const close = { position: closeAt(2.7).toArray(), target: closeTarget.toArray(), fov: 34, focus: 2.7 };
    const closer = { position: closeAt(2.25).toArray(), target: closeTarget.toArray(), fov: 34, focus: 2.25 };

    const T = { title: kit.at('title'), move: kit.at('move'), arrive: kit.at('arrive'), cut: kit.at('cut'), locked: kit.at('locked'), end: kit.at('end') };
    const street = VIEW === 'projector' ? kit.stillShot(start, [], { name: 'projector' })
      : VIEW === 'moved' || VIEW === 'weights' ? kit.stillShot(end, [], { name: 'moved' })
        : VIEW === 'weights-move' ? kit.stillShot(start, [{ kind: 'zoom in', from: T.move, to: T.arrive, ...end }], { name: 'up the street, weights' })
        : kit.stillShot(start, [{ kind: 'zoom in', from: T.move, to: T.arrive, ...end }], { name: 'up the street' });
    const board = VIEW === 'notice' ? kit.stillShot(closer, [], { name: 'notice held' })
      : kit.stillShot(close, [{ kind: 'zoom in', from: T.cut, to: T.end + 1, ...closer }], { name: 'the notice' });
    const onBoard = (t) => VIEW === 'notice' || ((VIEW === 'move' || VIEW === 'weights-move') && t >= T.cut);

    function pose(t) {
      const flicker = 0.75 + 0.15 * Math.sin(t * 17.3) + 0.1 * Math.sin(t * 29.1 + 1.3);
      fireGlow.material.opacity = 0.4 * flicker;
      fireGlow.scale.setScalar(1.4 + 0.12 * Math.sin(t * 11.7));
      fireLight.intensity = 4 * (0.75 + 0.25 * flicker);
      flames.set(t);
      sparks.set(t);
      for (const shadow of shadows) shadow.material.opacity = 0.6 * smooth((t - T.move) / 0.7);
      brazierSmoke.set({ t, origin: brazierTop.clone().add(new THREE.Vector3(0, 0.4, 0)).toArray(), scale: 0.55, wind: 0.35 });
      for (const c of chimneySmoke) c.effect.set({ t, origin: c.top.toArray(), scale: 0.9, wind: 0.8 });
      const fade = Math.max(1 - clamp01(t / 1.0), smooth((t - T.end) / 1.0));
      const close = onBoard(t);
      return { camera: close ? board(t) : street(t),
        look: { exposure: 1.0, aperture: close ? 1.6 : 2.5, maxBlur: close ? 10 : 7, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fade } };
    }
    function draw2D(ctx, t) {
      placeTitle(ctx, t, { at: T.title, until: T.move + 3.5, place: 'Britain', year: 1926, y: 300 });
      // a soft dark fade down from the top behind LOCKED OUT, so it reads over the board and the lit window
      const shade = clamp01((t - T.locked + 0.2) / 0.5) * (1 - clamp01((t - T.end - 0.4) / 0.5));
      if (shade > 0) {
        const g = ctx.createLinearGradient(0, 0, 0, 640);
        g.addColorStop(0, `rgba(5,8,12,${0.62 * shade})`); g.addColorStop(1, 'rgba(5,8,12,0)');
        ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 640);
      }
      hook(ctx, t, { at: T.locked, until: T.end + 0.9, text: 'LOCKED OUT', y: 330, size: 104 });
      hook(ctx, t, { at: T.locked + 0.5, until: T.end + 0.9, text: 'FROM 1 MAY 1926', y: 430, size: 48, colour: '#e8a33d' });
      return true;
    }
    return { pose, draw2D };
  },
};

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/lockout-test/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page],
    pageNumbers: [1],
  });
}
