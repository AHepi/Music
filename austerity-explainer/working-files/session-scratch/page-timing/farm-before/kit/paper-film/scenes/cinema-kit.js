// What this does: the toolkit every cinema page uses. One CinemaKit is made for each page of a
// chapter (by cinema-chapter.js) and handed to that page's file. It gives the page:
//   - its own small 3D world (kit.scene) with a camera (kit.camera) and a light rig (kit.lights):
//     one warm key lamp that casts soft shadows, a cool fill, haze for depth;
//   - painted rooms with real depth (kit.relief): a painting and its depth map become a 3D surface,
//     so the camera can move into the painting and near things slide past far things;
//   - paper cut-outs (kit.cutout, kit.word): painted figures and plain words, standing in the world
//     on a hinge, folding up like a pop-up book and casting shadows;
//   - card and paper models built here, not painted (in models.js: factories, houses, coins, shells,
//     price tags, counters, dials and more);
//   - camera moves (kit.shot), shakes (kit.shake), dust and haze in the light (in effects.js);
//   - the narrator's word times (kit.at('word'), kit.end('word')) so everything lands on her words;
//   - flat graphics on top of the picture (in graphics.js: place and date titles, labels that point
//     at things, counters and charts), drawn by the page's draw2D().
//
// How it fits: cinema-chapter.js makes the kits and calls each page's build(kit) once, then pose(t)
// for every frame. A page returns { pose(t) -> { camera, look }, draw2D(context, t) }. The full
// reference is "08 Cinema pages - how a page file works.md" in the kit folder.

import { THREE, loadTexture, loadPixels, canvasTexture, renderer, FRAME_WIDTH, FRAME_HEIGHT, MOVING_LAYER } from '../stage/cinema-stage.js';
import { RoomEnvironment } from '/paper-film/node_modules/three/examples/jsm/environments/RoomEnvironment.js';
import { spring, clamp01, easeInOut } from './paper-kit.js';

export { THREE };
export * from './paper-kit.js';

const PAPER_BACK = new THREE.Color(0xd9d2c3);

// ------------------------------------------------------------------------------------- helpers
export const lerp = (a, b, k) => a + (b - a) * k;
export const smooth = (x) => { x = clamp01(x); return x * x * (3 - 2 * x); };
export const smoother = (x) => { x = clamp01(x); return x * x * x * (x * (x * 6 - 15) + 10); };
export const ramp = (t, from, to) => clamp01((t - from) / Math.max(1e-6, to - from));
export function seededRandom(seed) {
  let value = (seed * 9301 + 49297) % 233280 || 1;
  return () => { value = (value * 16807) % 2147483647; return (value - 1) / 2147483646; };
}
const mirror = (x) => (x < 0 ? Math.min(1, -x) : x > 1 ? Math.max(0, 2 - x) : x);
const vector = (v) => (v instanceof THREE.Vector3 ? v.clone() : new THREE.Vector3(...v));

// One shared reflection environment (a soft grey room), so metal and gloss have something to reflect.
let roomEnvironment = null;
function environmentTexture() {
  if (!roomEnvironment) {
    const generator = new THREE.PMREMGenerator(renderer);
    roomEnvironment = generator.fromScene(new RoomEnvironment(), 0.04).texture;
    generator.dispose();
  }
  return roomEnvironment;
}

// ------------------------------------------------------------------------------- word timing
export function wordClock(timeline, pageNumber) {
  const page = timeline.pages.find((p) => p.page === pageNumber);
  if (!page) throw new Error(`the timeline has no page ${pageNumber}`);
  const key = (w) => w.toLowerCase().replace(/[^a-z0-9'.]/g, '').replace(/\.+$/, '');
  const find = (word, n = 1) => {
    let seen = 0;
    for (const w of page.words) if (key(w.text) === key(word) && ++seen === n) return w;
    throw new Error(`page ${pageNumber}: no word "${word}" (occurrence ${n})`);
  };
  return { at: (word, n) => find(word, n).start, end: (word, n) => find(word, n).end, page };
}

// ----------------------------------------------------------------------------------- the kit
export class CinemaKit {
  constructor({ number, timeline, piecesFolder, pieceInfo, reliefFolder }) {
    this.number = number;
    this.piecesFolder = piecesFolder;
    this.pieceInfo = pieceInfo;
    this.reliefFolder = reliefFolder;
    const clock = wordClock(timeline, number);
    this.at = clock.at;
    this.end = clock.end;
    this.words = clock.page.words;
    this.firstWordAt = clock.page.first_word_at;
    this.lastWordEnd = clock.page.last_word_end_at;
    this.scene = new THREE.Scene();
    this.scene.environment = environmentTexture();
    this.camera = new THREE.PerspectiveCamera(40, FRAME_WIDTH / FRAME_HEIGHT, 0.05, 400);
    this.shakes = [];
    this.cameraPlans = [];   // every stillShot made on this page, for the camera check
    this.lights = null;
    this.t = 0;
    this.lightRig();
  }

  // ---------------------------------------------------------------------------- the lights
  // key: the main lamp (warm), from `keyFrom` toward `keyTarget`; fill: soft light from all around
  // (sky colour above, ground colour below); haze: colour and thickness of the air; reflections: how
  // much the soft grey reflection room lights things (lower it inside dark paintings, so models
  // match the painting's light).
  lightRig({ keyColour = 0xffe2b8, keyShare = 0.42, keyFrom = [-6, 9, 8], keyTarget = [0, 0, -6],
    fillSky = 0x9fb4c0, fillGround = 0x3a3128, fillShare = 0.5, haze = 0x1d2a31, hazeDensity = 0.0,
    shadowBox = 14, shadowSoftness = 6, background = 0x0c1114, reflections = 1 } = {}) {
    this.scene.environmentIntensity = reflections;
    if (this.lights) for (const light of Object.values(this.lights)) if (light?.isObject3D) this.scene.remove(light);
    const key = new THREE.DirectionalLight(keyColour, Math.PI * keyShare);
    key.position.set(...keyFrom);
    key.target.position.set(...keyTarget);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { left: -shadowBox, right: shadowBox, top: shadowBox, bottom: -shadowBox, near: 0.5, far: 120 });
    key.shadow.radius = shadowSoftness;
    key.shadow.bias = -0.0004;
    key.shadow.normalBias = 0.02;
    const fill = new THREE.HemisphereLight(fillSky, fillGround, Math.PI * fillShare);
    this.scene.add(key, key.target, fill);
    this.scene.fog = hazeDensity > 0 ? new THREE.FogExp2(haze, hazeDensity) : null;
    this.scene.background = new THREE.Color(background);
    this.lights = { key, fill };
    return this.lights;
  }

  // a small warm light (a lamp, a glowing window), not casting shadows
  // Marks things that change from frame to frame while the camera holds (flames, smoke, sparks, glows, anything
  // lit by a flickering light that matters), so a held shot redraws only them (cinema-stage.js, MOVING_LAYER).
  // Everything not marked is the set, drawn once per held view. Returns its first argument.
  moving(...objects) {
    for (const object of objects.flat()) object?.traverse?.((o) => o.layers.set(MOVING_LAYER));
    return objects[0];
  }

  // Everything added to the scene by build(), from now until the returned function is called, is marked moving:
  //   const done = kit.movingFromHere(); new Flames(kit.scene, at); ...; done();
  movingFromHere() {
    const before = new Set(this.scene.children);
    return () => this.moving(this.scene.children.filter((o) => !before.has(o)));
  }

  glow(position, { colour = 0xffb25e, strength = 4, reach = 6 } = {}) {
    const light = new THREE.PointLight(colour, strength, reach, 2);
    light.position.copy(vector(position));
    this.scene.add(light);
    return light;
  }

  // ------------------------------------------------------------------------ painted rooms with depth
  // A painting seen from a camera at the origin looking along -z. Each pixel is pushed back to its
  // distance (from the depth map: light = near, dark = far), between `near` and `far` world units.
  // From the origin with the same lens (fov), the picture looks exactly like the painting; move the
  // camera and near things slide past far things. pointAt(u, v) gives the 3D point behind a spot on
  // the painting (u from the left, v from the bottom, 0 to 1), for standing things on its floor.
  async relief(name, { near = 5, far = 60, fov = 40, columns = 150, rows = 266, margin = 0.08, lit = 0.35, depthName } = {}) {
    const painting = await loadTexture(`${this.reliefFolder}/${name}.jpg`);
    painting.wrapS = painting.wrapT = THREE.ClampToEdgeWrapping;
    const depth = await loadPixels(`${this.reliefFolder}/${depthName ?? name}-depth.png`);
    const aspect = painting.image.width / painting.image.height;
    const tanY = Math.tan(THREE.MathUtils.degToRad(fov / 2)), tanX = tanY * aspect;
    const depthAt = (u, v) => {
      const x = Math.min(depth.width - 1, Math.max(0, u * (depth.width - 1)));
      const y = Math.min(depth.height - 1, Math.max(0, (1 - v) * (depth.height - 1)));
      const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(depth.width - 1, x0 + 1), y1 = Math.min(depth.height - 1, y0 + 1);
      const fx = x - x0, fy = y - y0;
      const value = (xx, yy) => depth.data[(yy * depth.width + xx) * 4] / 255;
      return lerp(lerp(value(x0, y0), value(x1, y0), fx), lerp(value(x0, y1), value(x1, y1), fx), fy);
    };
    const distanceAt = (u, v) => { const w = depthAt(u, v); return 1 / (w / near + (1 - w) / far); };
    const pointAt = (u, v, distance) => {
      const d = distance ?? distanceAt(u, v);
      return new THREE.Vector3((u * 2 - 1) * tanX * d, (v * 2 - 1) * tanY * d, -d);
    };
    const geometry = new THREE.PlaneGeometry(1, 1, columns, rows);
    const positions = geometry.attributes.position.array, uvs = geometry.attributes.uv.array, normals = geometry.attributes.normal.array;
    for (let i = 0; i < positions.length / 3; i++) {
      const u = -margin + uvs[i * 2] * (1 + 2 * margin), v = -margin + uvs[i * 2 + 1] * (1 + 2 * margin);
      const p = pointAt(clamp01(u), clamp01(v), distanceAt(u, v));
      // past the painting's edge, keep going in the same direction so the frame never shows a gap
      p.x = (u * 2 - 1) * tanX * -p.z; p.y = (v * 2 - 1) * tanY * -p.z;
      positions[i * 3] = p.x; positions[i * 3 + 1] = p.y; positions[i * 3 + 2] = p.z;
      // past the edge, show the painting mirrored (it reads as more floor or wall), not stretched streaks
      uvs[i * 2] = mirror(u); uvs[i * 2 + 1] = mirror(v);
      normals[i * 3] = 0; normals[i * 3 + 1] = 0; normals[i * 3 + 2] = 1;
    }
    geometry.attributes.position.needsUpdate = true;
    geometry.computeBoundingSphere();
    // the painting keeps its own colours (it glows by itself), and the lamp adds a little, so shadows
    // of things standing in it still show
    const material = new THREE.MeshLambertMaterial({ map: painting, emissiveMap: painting, emissive: 0xffffff, emissiveIntensity: 1 - lit, color: new THREE.Color(lit / 0.45, lit / 0.45, lit / 0.45) });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.receiveShadow = true;
    this.scene.add(mesh);
    // How far a 3D thing stands in front of the painted surface behind it (world units; negative =
    // it pokes into the painting, which shows as clipping). Checks up to `samples` of its corners.
    // Call it while testing, after posing the thing for a moment, e.g.
    //   console.warn('basket clearance', room.clearance(basket.anchor).toFixed(3));
    // It checks each corner and also points spread across each face (a flat card's middle can
    // cross a sloping floor even when its corners are clear).
    const clearance = (object, { samples = 600 } = {}) => {
      object.updateMatrixWorld(true);
      let least = Infinity;
      const p = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
      const test = (point) => {
        if (point.z >= -0.01) return;
        const d = -point.z, u = (point.x / d / tanX + 1) / 2, v = (point.y / d / tanY + 1) / 2;
        if (u < 0 || u > 1 || v < 0 || v > 1) return;
        least = Math.min(least, distanceAt(u, v) - d);
      };
      const visible = (o) => { for (let x = o; x; x = x.parent) if (!x.visible) return false; return true; };
      object.traverse((o) => {
        if (!o.isMesh || !visible(o)) return;
        const position = o.geometry.attributes.position, index = o.geometry.index;
        const triangles = index ? index.count / 3 : position.count / 3;
        const stride = Math.max(1, Math.floor(triangles / samples));
        const corner = (k) => (index ? index.getX(k) : k);
        for (let t = 0; t < triangles; t += stride) {
          a.fromBufferAttribute(position, corner(t * 3)).applyMatrix4(o.matrixWorld);
          b.fromBufferAttribute(position, corner(t * 3 + 1)).applyMatrix4(o.matrixWorld);
          c.fromBufferAttribute(position, corner(t * 3 + 2)).applyMatrix4(o.matrixWorld);
          for (const [wa, wb] of [[1, 0], [0, 1], [0, 0], [1 / 3, 1 / 3], [0.5, 0.5], [0.5, 0], [0, 0.5], [0.2, 0.2], [0.6, 0.2], [0.2, 0.6]]) {
            p.set(0, 0, 0).addScaledVector(a, wa).addScaledVector(b, wb).addScaledVector(c, 1 - wa - wb);
            test(p);
          }
        }
      });
      return least;
    };
    return { mesh, pointAt, distanceAt, clearance, fov, tanX, tanY, near, far };
  }

  // A flat painted backdrop (no depth), as a big card standing far back.
  async backdrop(name, { distance = 40, fov = 40, folder } = {}) {
    const painting = await loadTexture(`${folder ?? this.reliefFolder}/${name}.jpg`);
    const tanY = Math.tan(THREE.MathUtils.degToRad(fov / 2));
    const height = 2 * tanY * distance * 1.12, width = height * painting.image.width / painting.image.height;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, height), new THREE.MeshBasicMaterial({ map: painting, fog: false }));
    mesh.position.set(0, 0, -distance);
    this.scene.add(mesh);
    return mesh;
  }

  // ---------------------------------------------------------------------------- paper cut-outs
  // A painted cut-out (from the chapter's pieces) standing at `at` (the middle of its bottom edge),
  // `width` wide, turned by `yaw`. Use .set({ fold, dx, dy, dz, roll, lift, yaw, scale, visible }).
  // A speaking figure (an invented person): the face piece with a dark mouth just behind it and the
  // jaw just in front, all standing at `at`. set(pose, open) poses all three like one cut-out (pose
  // as for cutout .set) and drops the jaw by `open` (0 shut .. 1 wide).
  async speaker(name, { at = [0, 0, 0], width = 2, yaw = 0 } = {}) {
    const info = this.pieceInfo[`${name}-face`];
    const [x, y, z] = at;
    const face = await this.cutout(`${name}-face`, { at: [x, y, z], width, yaw });
    const mouth = await this.cutout(`${name}-mouth`, { at: [x, y, z - 0.006], width, yaw });
    const jaw = await this.cutout(`${name}-jaw`, { at: [x, y, z + 0.006], width, yaw });
    const dropMax = width * info.height_px / info.width_px * (info.jaw_drop_share ?? 0.014);
    return {
      face, mouth, jaw,
      set(pose = {}, open = 0) {
        face.set(pose);
        mouth.set({ ...pose, visible: (pose.visible ?? true) && open > 0.001 });
        jaw.set({ ...pose, dy: (pose.dy ?? 0) - dropMax * open });
      },
    };
  }

  // How open a speaking mouth is at t while words are said between `from` and `until` (seconds):
  // opens on each word of this page's narration in that span, shut between words.
  mouthOpen(t, from, until) {
    if (t < from || t > until) return 0;
    const word = this.words.find((w) => t >= w.start && t <= w.end);
    if (!word) return 0;
    const k = (t - word.start) / Math.max(0.08, word.end - word.start);
    return Math.sin(Math.PI * Math.min(1, k)) * (0.6 + 0.4 * Math.abs(Math.sin(t * 23)));
  }

  async cutout(name, options) {
    const info = this.pieceInfo[name];
    if (!info) throw new Error(`no piece called ${name}`);
    const texture = await loadTexture(`${this.piecesFolder}/${info.file}`);
    return this.addCutout(texture, options);
  }
  addCutout(texture, { at = [0, 0, 0], width = 2, yaw = 0, thickness = 0, shine = 0.4, parent } = {}) {
    const piece = new CutOut(texture, { at: vector(at), width, yaw, thickness, shine });
    (parent ?? this.scene).add(piece.anchor);
    return piece;
  }

  // Plain words cut from thick off-white card. size = letter height in world units.
  async word(lines, { size = 0.5, colour = '#f2ede3', weight = 800, ...options } = {}) {
    const texture = await wordTexture(Array.isArray(lines) ? lines : [lines], { colour, weight });
    const width = size * texture.image.width / 220;
    return this.addCutout(texture, { width, thickness: options.thickness ?? 0.035, ...options });
  }

  // A printed card (dark ink on card), for notices, signs and labels on things.
  async card(lines, { size = 0.4, look = {}, ...options } = {}) {
    const texture = await cardTexture(Array.isArray(lines) ? lines : [lines], look);
    const width = size * texture.image.width / (look.fontPx ?? 150);
    return this.addCutout(texture, { width, thickness: options.thickness ?? 0.02, ...options });
  }

  // ---------------------------------------------------------------------------- the camera
  // keys: [{ t, position: [x, y, z], target: [x, y, z], fov, focus (a point [x,y,z] or a distance) }]
  // The camera glides through the keys (no stops in between, easing in at the first key and out at the
  // last). handheld: a slight breathing drift (world units; off by default - the camera rule says hold
  // still). New pages should use stillShot below, which holds still between at most three moves.
  shot(keys, { handheld = 0, seed = 1 } = {}) {
    const times = keys.map((k) => k.t);
    const tracks = {
      position: keys.map((k) => vector(k.position)),
      target: keys.map((k) => vector(k.target)),
      fov: keys.map((k) => k.fov ?? keys[0].fov ?? 40),
      roll: keys.map((k) => k.roll ?? 0),
    };
    const focusValues = keys.map((k) => k.focus);
    const random = seededRandom(seed * 13 + 5);
    const phases = Array.from({ length: 6 }, () => random() * Math.PI * 2);
    return (t) => {
      const position = hermite(times, tracks.position, t);
      const target = hermite(times, tracks.target, t);
      const fov = hermite(times, tracks.fov, t);
      const roll = hermite(times, tracks.roll, t);
      // focus: a point in the world (its distance along the view) or a distance
      const index = segmentIndex(times, t);
      const focusAt = (i) => {
        const f = focusValues[i];
        if (f === undefined) return target.distanceTo(position);
        if (typeof f === 'number') return f;
        const point = vector(f), view = target.clone().sub(position).normalize();
        return Math.max(0.2, point.sub(position).dot(view));
      };
      const s = index.k;
      const focus = lerp(focusAt(index.i), focusAt(Math.min(keys.length - 1, index.i + 1)), smoother(s));
      const drift = new THREE.Vector3(
        handheld * (Math.sin(t * 0.53 + phases[0]) + 0.5 * Math.sin(t * 1.31 + phases[1])),
        handheld * (Math.sin(t * 0.61 + phases[2]) + 0.5 * Math.sin(t * 1.17 + phases[3])),
        0);
      return { position: position.add(drift), target, fov, roll, focus };
    };
  }

  // A still camera with a few deliberate moves: the film's camera rule. The camera holds still at
  // `start` and only moves during the listed moves; between moves it holds still again. At most three
  // moves per shot (a shot ends at a cut); a page that needs more needs another shot.
  //   start: { position, target, fov, focus }  (focus: a point [x, y, z] or a distance)
  //   moves: [{ from, to, kind, position?, target?, fov?, focus? }] in time order, not overlapping;
  //          anything a move leaves out stays as it was. Each move eases in and out.
  // kind says why the camera moves (the camera grammar):
  //   'zoom out'  make room for what comes next      'zoom in'   narrow the view onto what matters now
  //   'pan left' / 'pan right'  shift perspective    'pan up'    toward ideals   'pan down'  pressure
  //   'move up'   see the bigger picture             'move down' show the small details
  //   'focus'     only the focus changes (does not count as a move)
  stillShot(start, moves = [], { name = 'shot' } = {}) {
    const KINDS = ['zoom out', 'zoom in', 'pan left', 'pan right', 'pan up', 'pan down', 'move up', 'move down', 'focus'];
    const counted = moves.filter((m) => m.kind !== 'focus');
    const where = `page ${this.number}, ${name}`;
    for (const m of moves) {
      if (!KINDS.includes(m.kind)) throw new Error(`${where}: camera move kind "${m.kind}" is not one of: ${KINDS.join(', ')}`);
      if (!(m.to > m.from)) throw new Error(`${where}: camera move "${m.kind}" must end after it starts (from ${m.from}, to ${m.to})`);
      if (m.kind === 'focus' && (m.position || m.target || m.fov !== undefined)) throw new Error(`${where}: a 'focus' move may only change focus`);
    }
    for (let i = 1; i < moves.length; i++) {
      if (moves[i].from < moves[i - 1].to - 1e-6 && moves[i].kind !== 'focus' && moves[i - 1].kind !== 'focus') {
        throw new Error(`${where}: camera moves overlap ("${moves[i - 1].kind}" until ${moves[i - 1].to.toFixed(2)}, "${moves[i].kind}" from ${moves[i].from.toFixed(2)})`);
      }
    }
    if (counted.length > 3) throw new Error(`${where}: ${counted.length} camera moves; the rule is at most 3 per shot (cut to a new shot instead)`);
    // the pose before and after each move
    const poses = [{ position: vector(start.position), target: vector(start.target), fov: start.fov ?? 40, focus: start.focus }];
    for (const m of moves) {
      const before = poses[poses.length - 1];
      poses.push({
        position: m.position ? vector(m.position) : before.position.clone(),
        target: m.target ? vector(m.target) : before.target.clone(),
        fov: m.fov ?? before.fov,
        focus: m.focus ?? before.focus,
      });
    }
    const focusDistance = (f, position, target) => {
      if (f === undefined) return target.distanceTo(position);
      if (typeof f === 'number') return f;
      const view = target.clone().sub(position).normalize();
      return Math.max(0.2, vector(f).sub(position).dot(view));
    };
    this.cameraPlans.push({ name, start, moves: moves.map(({ from, to, kind }) => ({ from, to, kind })) });
    return (t) => {
      this.shotShowing = name;   // tells the camera check which shot is on screen
      let position = poses[0].position.clone(), target = poses[0].target.clone(), fov = poses[0].fov;
      let focus = focusDistance(poses[0].focus, position, target);
      moves.forEach((m, i) => {
        if (t <= m.from) return;
        const k = smoother(clamp01((t - m.from) / (m.to - m.from)));
        const a = poses[i], b = poses[i + 1];
        if (m.kind !== 'focus') {
          position = a.position.clone().lerp(b.position, k);
          target = a.target.clone().lerp(b.target, k);
          fov = lerp(a.fov, b.fov, k);
        }
        focus = lerp(focusDistance(a.focus, position, target), focusDistance(b.focus, position, target), k);
      });
      return { position, target, fov, roll: 0, focus };
    };
  }

  // a camera shake from something heavy landing (amount in world units)
  shake(time, amount = 0.06, decay = 0.15) { this.shakes.push({ time, amount, decay }); }

  // Puts the camera where the shot says (plus shakes) for moment t; returns the focus distance.
  aim(state, t) {
    let dx = 0, dy = 0;
    for (const s of this.shakes) {
      const age = t - s.time;
      if (age < 0 || age > 1.5) continue;
      const a = s.amount * Math.exp(-age / s.decay);
      dx += a * Math.sin(2 * Math.PI * 17 * age); dy += a * 0.7 * Math.sin(2 * Math.PI * 23 * age + 1);
    }
    const view = state.target.clone().sub(state.position).normalize();
    const side = new THREE.Vector3().crossVectors(view, new THREE.Vector3(0, 1, 0)).normalize();
    const up = new THREE.Vector3().crossVectors(side, view);
    this.camera.position.copy(state.position).addScaledVector(side, dx).addScaledVector(up, dy);
    this.camera.up.set(Math.sin(state.roll ?? 0), Math.cos(state.roll ?? 0), 0);
    this.camera.lookAt(state.target.clone().addScaledVector(side, dx * 0.5).addScaledVector(up, dy * 0.5));
    this.camera.fov = state.fov;
    this.camera.updateProjectionMatrix();
    this.camera.updateMatrixWorld();
    return state.focus;
  }

  // Where a 3D point lands on the frame (in pixels), for labels that point at things.
  toScreen(point) {
    const p = vector(point).project(this.camera);
    return { x: (p.x + 1) / 2 * FRAME_WIDTH, y: (1 - p.y) / 2 * FRAME_HEIGHT, behind: p.z > 1 };
  }
}

// ----------------------------------------------------------------- a smooth path through keys
function segmentIndex(times, t) {
  if (t <= times[0]) return { i: 0, k: 0 };
  for (let i = 0; i < times.length - 1; i++) if (t < times[i + 1]) return { i, k: (t - times[i]) / (times[i + 1] - times[i]) };
  return { i: times.length - 1, k: 0 };
}
function hermite(times, values, t) {
  const isVector = values[0] instanceof THREE.Vector3;
  const n = values.length;
  if (n === 1 || t <= times[0]) return isVector ? values[0].clone() : values[0];
  if (t >= times[n - 1]) return isVector ? values[n - 1].clone() : values[n - 1];
  const { i, k } = segmentIndex(times, t);
  if (values[i + 1] === undefined) throw new Error(`camera keys out of order at t=${t}: ${times.map((x) => x.toFixed(2)).join(', ')}`);
  const dt = times[i + 1] - times[i];
  const tangent = (j) => {
    if (j === 0 || j === n - 1) return isVector ? new THREE.Vector3() : 0;
    const span = times[j + 1] - times[j - 1];
    return isVector ? values[j + 1].clone().sub(values[j - 1]).multiplyScalar(1 / span) : (values[j + 1] - values[j - 1]) / span;
  };
  const h00 = 2 * k ** 3 - 3 * k ** 2 + 1, h10 = k ** 3 - 2 * k ** 2 + k, h01 = -2 * k ** 3 + 3 * k ** 2, h11 = k ** 3 - k ** 2;
  if (!isVector) return h00 * values[i] + h10 * dt * tangent(i) + h01 * values[i + 1] + h11 * dt * tangent(i + 1);
  return values[i].clone().multiplyScalar(h00).addScaledVector(tangent(i), h10 * dt)
    .addScaledVector(values[i + 1], h01).addScaledVector(tangent(i + 1), h11 * dt);
}

// ----------------------------------------------------------------------------------- cut-outs
// A paper cut-out standing in the world, hinged along its bottom edge. Thickness, if given, is shown
// as a few stacked copies of the outline in a darker paper colour behind the front (card edge).
export class CutOut {
  constructor(texture, { at, width, yaw, thickness, shine }) {
    this.rest = at.clone(); this.yaw = yaw;
    this.width = width; this.height = width * texture.image.height / texture.image.width;
    this.anchor = new THREE.Group();
    this.mover = new THREE.Group();
    this.hinge = new THREE.Group();
    this.anchor.add(this.mover); this.mover.add(this.hinge);
    const geometry = new THREE.PlaneGeometry(this.width, this.height);
    geometry.translate(0, this.height / 2, 0);
    const front = new THREE.MeshLambertMaterial({ map: texture, emissiveMap: texture, emissive: 0xffffff, emissiveIntensity: 1 - shine, color: new THREE.Color(shine / 0.45, shine / 0.45, shine / 0.45), alphaTest: 0.5, side: THREE.FrontSide });
    this.front = new THREE.Mesh(geometry, front);
    this.front.castShadow = true; this.front.receiveShadow = true;
    this.front.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: texture, alphaTest: 0.5 });
    const backMaterial = new THREE.MeshLambertMaterial({ map: texture, alphaTest: 0.5, side: THREE.BackSide });
    backMaterial.onBeforeCompile = (shader) => {
      shader.uniforms.paperBack = { value: PAPER_BACK };
      shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 paperBack;')
        .replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb = paperBack;');
    };
    this.back = new THREE.Mesh(geometry, backMaterial);
    this.hinge.add(this.front, this.back);
    if (thickness > 0) {
      const edgeMaterial = new THREE.MeshLambertMaterial({ map: texture, alphaTest: 0.5, side: THREE.DoubleSide });
      edgeMaterial.onBeforeCompile = (shader) => {
        shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n diffuseColor.rgb = vec3(0.62, 0.58, 0.52);');
      };
      const layers = 4;
      for (let i = 1; i <= layers; i++) {
        const edge = new THREE.Mesh(geometry, edgeMaterial);
        edge.position.z = -thickness * i / layers;
        this.hinge.add(edge);
      }
      this.back.position.z = -thickness;
    }
    this.anchor.position.copy(this.rest);
    this.anchor.rotation.y = yaw;
  }
  // fold: 0 standing, PI/2 lying flat toward the camera; dx, dy, dz: moves; roll: turn in its own
  // plane; lift: forward along its facing; yaw: extra turn; scale: size.
  set({ visible = true, fold = 0, dx = 0, dy = 0, dz = 0, roll = 0, lift = 0, yaw = 0, scale = 1, opacity } = {}) {
    this.anchor.visible = visible;
    if (!visible) return;
    const facing = this.yaw + yaw;
    this.anchor.position.set(this.rest.x + dx + Math.sin(facing) * lift, this.rest.y + dy, this.rest.z + dz + Math.cos(facing) * lift);
    this.anchor.rotation.set(0, facing, 0);
    this.mover.rotation.set(0, 0, roll);
    this.mover.scale.setScalar(scale);
    this.hinge.rotation.set(fold, 0, 0);
    if (opacity !== undefined) {
      this.hinge.traverse((o) => {
        if (!o.isMesh) return;
        o.material.transparent = opacity < 1;
        o.material.opacity = opacity;
      });
    }
  }
}

// Fades a cut-out smoothly: use setFading(piece, pose) instead of piece.set(pose) for a piece that fades (pose with
// opacity). Two things stop a plain cut-out from fading: it is drawn only where it is at least half solid (so a fade
// snaps off half way), and a piece first drawn solid keeps a drawing recipe that ignores see-through until the recipe
// is rebuilt. So a fading piece is drawn see-through-capable from its first call (its recipe rebuilt once), and while
// it fades it is drawn down to nearly see-through. soft: true keeps the low cut-off even when solid (feathered edges).
// Call it on every frame the piece shows, so each frame is drawn the same whatever came before (lesson 87 of the
// austerity project; the film kit keeps this inside house-sample/page-1.js). piece.set({ opacity }) is unchanged, so
// pages that already fade their own way (chapter 2's pages 1, 4, 6 and 9) draw as before.
export function setFading(piece, pose, { soft = false } = {}) {
  piece.set(pose);
  for (const mesh of [piece.front, piece.back]) {
    mesh.material.transparent = true;
    if (!mesh.material.userData.fadeReady) { mesh.material.needsUpdate = true; mesh.material.userData.fadeReady = true; }
  }
  const fading = pose.opacity !== undefined && pose.opacity < 0.999;
  piece.front.material.alphaTest = fading || soft ? 0.02 : 0.5;
}

// ---------------------------------------------------------------------------- printed textures
let fontsLoaded = null;
export function loadFonts() {
  fontsLoaded ??= Promise.all(['400', '500', '600', '700', '800'].map((w) => document.fonts.load(`${w} 64px Inter`)));
  return fontsLoaded;
}
export async function wordTexture(lines, { fontPx = 220, colour = '#f2ede3', lineGap = 0.98, weight = 800 } = {}) {
  await loadFonts();
  const font = `${weight} ${fontPx}px Inter`;
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
export async function cardTexture(lines, { fontPx = 150, cardColour = '#e8e0cc', inkColour = '#20262b', borderColour = 'rgba(32,38,43,0.55)',
  lineGap = 1.08, padX = 0.55, padY = 0.42, minWidth = 0, aspect = null, weight = 800 } = {}) {
  await loadFonts();
  const font = `${weight} ${fontPx}px Inter`;
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

export { spring, clamp01, easeInOut };

// Whether two 3D things' boxes overlap (true = they may clip into each other), and by how much (the
// overlap's smallest side, world units). Rough: a box is bigger than a slanted card, so a small
// overlap can be fine; look at a still to be sure. Use while testing, e.g.
//   console.warn('envelope vs workers', JSON.stringify(boxesOverlap(envelope.anchor, workers.anchor)));
export function boxesOverlap(a, b) {
  a.updateMatrixWorld(true); b.updateMatrixWorld(true);
  // only the parts that are showing count
  const shownBox = (root) => {
    const box = new THREE.Box3();
    root.traverse((o) => {
      if (!o.isMesh) return;
      for (let x = o; x; x = x.parent) if (!x.visible) return;
      box.union(new THREE.Box3().setFromObject(o, true));
    });
    return box;
  };
  const boxA = shownBox(a), boxB = shownBox(b);
  if (boxA.isEmpty() || boxB.isEmpty()) return { overlap: false, by: 0 };
  if (!boxA.intersectsBox(boxB)) return { overlap: false, by: 0 };
  const both = boxA.clone().intersect(boxB), size = both.getSize(new THREE.Vector3());
  return { overlap: true, by: Math.min(size.x, size.y, size.z) };
}
