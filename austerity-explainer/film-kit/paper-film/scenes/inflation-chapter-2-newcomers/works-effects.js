// What this does: the Works on a page of chapter 2 for newcomers (plan 34, part 1 "A. The Works", and "How the two
// factories stay the same", point 8): it loads the Works set (the two factories at the head of one lane, built in
// Blender), shines the view's painting onto it (projected-set.js), and draws the Works' moving things on top: chimney
// smoke from the chimney tops, the brazier's flames, sparks, smoke and glow and the lantern's flicker at No. 1, No. 2's
// window flicker, the gate lamps' glow, the gate leaves (their own sharp surfaces, never in a plate) that can swing,
// the crates that pop up in No. 1's open gateway, the bank's window lighting, and the factories' windows changing in
// steps. Every page that shows the Works uses this one file, so the four states and their settings, the smoke and
// flicker seeds and the wind are the same on every page.
//
// The four states (STATES below; plan 34's states table):
//   No. 1 quiet      windows dark, chimney cold, gate shut and chained, men waiting, brazier and lantern lit
//   No. 1 working    windows lit (in steps, on "start"), chimney smoking, gate open, nobody at the gate, the brazier
//                    still burning, crates popping up in the gateway on "things"
//   No. 2 flat out   windows blazing and flickering, heavy smoke from both chimneys, gate wide open
//   No. 2 slowed     a third of the windows lit, thin smoke from one chimney, gate half shut, men waiting
//
// Held shots stay fast (log 34): everything that changes from frame to frame (smoke, flames, flicker, a gate while it
// swings, crates while they pop up) is marked moving (kit.moving), so a held camera draws the set once and only these
// each frame. works.set(t, state) returns the page's still key, which changes only when the set itself changes (a
// view, a painting, a step of a blend, the men gone, a gate coming to rest, crates landing, the bank's window).
// Nothing in the set depends on t except through that key, and every moving thing depends only on t (fixed seeds), so
// frames can be drawn in any order and pieces of film filmed apart join without a jump.
//
// Use in a page:
//   const works = await buildWorks(kit, { folder, views: ['w3', 'w1'], pictures: { w3: 'works-w3-plate.jpg', ... },
//                                         behind: 'w1 behind', hideInBehind: 'men' });
//   const camera = kit.stillShot(works.cameraAt('w1', 'plate'), [{ kind: 'zoom in', from, to, ...works.cameraAt('w1', 'composed') }]);
//   pose(t): const still = works.set(t, { view: 'w1', painting: 'w1', men: true,
//                                         no1: { state: 'quiet' }, no2: { state: 'flat out' } });
//   draw2D: works.screen('no-1-queue') -> where a thing is on the frame, for labels
//
// The set's files (in `folder`): works-set.glb, or the parts listed in works-shot.json's "files" whose names start
// with works-set (everything the painting is shone onto, with the waiting men),
// works-signs.glb (lettered things keeping their own surfaces), works-gates.glb (the gate leaves, chain and padlock),
// works-pop-up.glb (No. 1's pop-up crates), works-camera-VIEW.json (each view's plate camera, the projector) and
// works-shot.json (where things are, Blender space: views with their plate and composed spots, the brazier, the
// lantern, the gate lamps, the gates, the men's names), all written into WORKS_FOLDER by assemble_works.py.
// What this file looks for in them (so the real export can match, or this list be changed in one place):
//   works-shot.json   film_fov_degrees; views.{w1,w2,w3,w4}.plate and .composed (the camera's two spots) and
//                     .subject (what it is focused on); brazier [x, y], coals_z, fire_light, lantern_light;
//                     gate_lamps.{no-1,no-2}; men (the waiting men's object names); no-1-gateway (where the
//                     pop-up crates stand and the NEW MONEY arrow points); no-2-crates (the crates in No. 2's gateway)
//   works-set.glb     the markers no-1-chimney-top, no-2-chimney-a-top, no-2-chimney-b-top (smoke) and the window
//                     groups no-1-windows-step-1 to 3 and no-2-windows-step-1 to 3 (flicker), as build_factories.py
//                     names them; the bank's glass in a material named bank-window... (page 9)
//   works-gates.glb   no-1-gate and no-2-gate, each holding a left and a right leaf (names containing left_door /
//                     right_door, or left-leaf / right-leaf) and a bolt; no-1-chain (the chain and padlock)
//   works-pop-up.glb  no-1-crate-1, no-1-crate-2 ... (popping up in that order)
// Missing pieces are left out quietly (no gates, no crates, no smoke from a chimney without its marker).
import { THREE, seededRandom, clamp01, spring } from '../cinema-kit.js';
import { loadTexture, canvasTexture, MOVING_LAYER } from '../../stage/cinema-stage.js';
import { loadModel } from '../model-loader.js';
import { loadProjector, projectPaintingOnto, paintedSkyOnly } from '../projected-set.js';
import { glow, Flames, Sparks, paintedSkyColour } from '../pit-village-effects.js';
import { Smoke } from '../effects.js';
import { nameTag } from '../graphics.js';

// where the Works' files are: the real assembly's export (assemble_works.py, build_works.sh)
export const WORKS_FOLDER = '/assets/models/inflation-chapter-2-newcomers/works';
// the one the pages use (the stand-in used while the assembly was being built is no longer needed)
export const WORKS_IN_USE = WORKS_FOLDER;

// ------------------------------------------------------------------------------------------ the fixed settings

// The four states. windows: share of the factory's windows lit (in thirds); flicker: how strongly the lit windows
// flicker (0 none, 1 blazing); smoke: which chimneys smoke and how ('none', 'working', 'heavy', 'thin'); gate: the
// leaves' angle in degrees (0 shut, 90 square to the wall, swung into the yard); men: how many wait at the gate.
export const STATES = {
  'no-1': {
    quiet: { windows: 0, flicker: 0, smoke: 'none', gate: 0, chained: true, men: 7, brazier: true, lantern: true },
    working: { windows: 1, flicker: 0.18, smoke: 'working', gate: 84, chained: false, men: 0, brazier: true, lantern: true },
  },
  'no-2': {
    'flat out': { windows: 1, flicker: 0.55, busy: 1.0, smoke: 'heavy', gate: 96, chained: false, men: 0 },
    slowed: { windows: 1 / 3, flicker: 0.2, smoke: 'thin', gate: 42, chained: false, men: 8 },
  },
};

// Chimney smoke, in metres (the chimneys are about 25 m tall). count: puffs alive at once; life: seconds a puff lives;
// rise and drift: how far it climbs and is blown; size: its width when born and at the end; opacity: its strongest.
// colour: as seen against the dusk (0 to 255, as on screen).
export const SMOKE = {
  heavy: { count: 26, life: 9.0, rise: 16, drift: 12, size: [3.0, 13], opacity: 0.78, colour: [104, 101, 106] },
  // No. 1 working is seen only from W1 (page 3), where its chimney's mouth is about 0.05 down the frame, in the words'
  // dark band, and each puff leaves the frame within about a second: so it is fuller, paler and stronger than the
  // others, or it did not show at all (round 3 of log 34)
  working: { count: 16, life: 8.0, rise: 14, drift: 10, size: [3.2, 10], opacity: 0.8, colour: [150, 146, 148] },
  thin: { count: 9, life: 7.0, rise: 12, drift: 9, size: [1.6, 6.5], opacity: 0.32, colour: [128, 126, 128] },
};
// the wind: the same on every page and in every view, so the smoke always leans the same way (to No. 2's side, +x)
export const WIND = new THREE.Vector3(1, 0.05, 0.25).normalize();
// fixed seeds: the same smoke and flicker on every page
export const SEEDS = { 'no-1-chimney-top': 41, 'no-2-chimney-a-top': 52, 'no-2-chimney-b-top': 63, brazierSmoke: 21, flames: 17, sparks: 11,
  'no-1-windows': 71, 'no-2-windows': 72 };
// which chimneys smoke for each kind of smoke
const CHIMNEYS = { 'no-1': ['no-1-chimney-top'], 'no-2': ['no-2-chimney-a-top', 'no-2-chimney-b-top'] };
const THIN_CHIMNEYS = { 'no-1': ['no-1-chimney-top'], 'no-2': ['no-2-chimney-a-top'] };
// the lettering that keeps its own sharp surface (the painter garbles small print; plan 34, "Own surface")
export const LETTERING = ['gate-board-no-1-lettering', 'gate-board-no-2-lettering', 'bank-sign-lettering', 'bank-brass-plate-lettering',
  'steel-drum-petrol-stencil', 'steel-drum-diesel-stencil', 'crate-stencil', 'wages-envelope-printing'];
// The small name tags (plan 34, "How the two factories stay the same", point 4): QUIET and FLAT OUT on every return to
// W3 from page 5, FLAT OUT on W2 from page 6; No. 2's tag becomes THE FLAT-OUT FACTORY SLOWS on "slows" (page 12,
// finding T16), so a tag never calls a slowing factory flat out.
export const TAGS = { quiet: 'QUIET', flatOut: 'FLAT OUT', slows: 'THE FLAT-OUT FACTORY SLOWS' };
// the bank's window glass, lit from page 9 (a material whose name starts with this)
const BANK_WINDOW = 'bank-window';
// the windows' lit pictures, by glass type (for the flicker; the glass pieces are named in works_kit.py)
const GLASS_TYPES = ['mill-window-narrow', 'mill-window-wide', 'north-light', 'lantern-light', 'doorway-inside'];

// Blender (x, y, z) -> three.js (x, z, -y)
export const fromBlender = ([x, y, z = 0]) => new THREE.Vector3(x, z, -y);

// Marks an object (and everything under it) as moving (drawn every frame over the held set) or as part of the set.
function setMoving(object, moving) {
  object.traverse((o) => o.layers.set(moving ? MOVING_LAYER : 0));
}

// A blend in steps (plan 34, F8: "windows change in steps"): from `at`, over `length` seconds, in `steps` equal
// steps, the first on the word itself. Returns 0 before `at`, then 1/steps, 2/steps ... 1. Each step is one more
// drawing of the held set, not one a frame.
export function steppedBlend(t, at, { length = 0.8, steps = 3 } = {}) {
  if (t < at) return 0;
  return Math.min(steps, 1 + Math.floor((t - at) / (length / steps))) / steps;
}

// ------------------------------------------------------------------------------------------ chimney smoke

// A soft, lumpy puff of smoke (a few overlapping soft blobs), drawn once; `seed` makes each of a few shapes its own.
function puffPicture(seed) {
  const random = seededRandom(seed);
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  for (let i = 0; i < 7; i++) {
    const angle = random() * Math.PI * 2, reach = 18 * Math.sqrt(random());
    const x = 64 + Math.cos(angle) * reach, y = 64 + Math.sin(angle) * reach, radius = 26 + random() * 18;
    const g = ctx.createRadialGradient(x, y, 0, x, y, radius);
    g.addColorStop(0, 'rgba(255,255,255,0.55)'); g.addColorStop(0.6, 'rgba(255,255,255,0.22)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
  }
  return canvasTexture(canvas);
}
const PUFF_PICTURES = [];
const puffPictures = () => {
  if (!PUFF_PICTURES.length) for (const seed of [3, 7, 12, 19]) PUFF_PICTURES.push(puffPicture(seed));
  return PUFF_PICTURES;
};

// Smoke rising from a chimney top and blown by the wind. Each puff's place depends only on t: puffs are born one
// after another for ever; set(t, { kind, from }) shows those born after `from` (so smoke can start on a word and build
// up from the chimney's mouth) with the kind's settings.
export class ChimneySmoke {
  constructor(scene, top, seed) {
    this.top = top;
    const random = seededRandom(seed);
    const pictures = puffPictures();
    const most = Math.max(...Object.values(SMOKE).map((s) => s.count));
    this.puffs = Array.from({ length: most }, (_, i) => {
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: pictures[i % pictures.length], transparent: true, depthWrite: false, opacity: 0 }));
      sprite.visible = false;
      scene.add(sprite);
      return { sprite, order: i, jitter: random() * 0.6, sway: random() * Math.PI * 2, spin: (random() - 0.5) * 0.25, turn: random() * Math.PI * 2,
        size: 0.8 + random() * 0.45, shade: 0.85 + random() * 0.25, side: (random() - 0.5) * 0.5 };
    });
  }
  set(t, { kind = 'none', from = -Infinity } = {}) {
    const settings = SMOKE[kind];
    for (const puff of this.puffs) {
      if (!settings || puff.order >= settings.count) { puff.sprite.visible = false; continue; }
      const { life, count } = settings;
      const offset = (puff.order + puff.jitter) / count * life;
      const born = offset + Math.floor((t - offset) / life) * life;
      const age = t - born;
      if (born < from || age < 0 || age > life) { puff.sprite.visible = false; continue; }
      const k = age / life;
      const climb = settings.rise * Math.pow(k, 0.75), blown = settings.drift * Math.pow(k, 1.25);
      const sway = 0.9 * Math.sin(puff.sway + age * 0.9) * k;
      puff.sprite.visible = true;
      puff.sprite.position.set(this.top.x + WIND.x * blown + sway, this.top.y + 0.3 + climb + WIND.y * blown, this.top.z + WIND.z * blown + puff.side * k * 3);
      const size = (settings.size[0] + (settings.size[1] - settings.size[0]) * Math.pow(k, 0.8)) * puff.size;
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.rotation = puff.turn + puff.spin * age;
      const [r, g, b] = settings.colour.map((c) => Math.min(255, c * puff.shade) / 255);
      puff.sprite.material.color.setRGB(r, g, b, THREE.SRGBColorSpace);
      puff.sprite.material.opacity = settings.opacity * Math.min(1, age / 0.25) * Math.pow(1 - k, 1.3);
    }
  }
}

// ------------------------------------------------------------------------------------------ window flicker

// A warm light over a factory's lit windows that flickers (machines moving in front of the gas light): a copy of each
// glass piece wearing its lit picture, drawn additively just in front of it. set(t, { amount, steps }) shows the panes
// of the lit steps (1, 2, 3) with a flicker of strength `amount` (0 none, 1 blazing).
class WindowFlicker {
  constructor(scene, set, prefix, seed, litPictures) {
    const random = seededRandom(seed);
    this.group = new THREE.Group();
    this.panes = [];
    set.updateMatrixWorld(true);
    for (const step of [1, 2, 3]) {
      const holder = set.getObjectByName(`${prefix}-windows-step-${step}`);
      if (!holder) continue;
      holder.traverse((o) => {
        if (!o.isMesh) return;
        const name = [o.material].flat()[0]?.name ?? '';
        const glassType = GLASS_TYPES.find((type) => name.includes(type));
        const material = new THREE.MeshBasicMaterial({ map: litPictures[glassType] ?? null, color: 0xffb468, transparent: true, opacity: 0,
          blending: THREE.AdditiveBlending, depthWrite: false, fog: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
        const pane = new THREE.Mesh(o.geometry, material);
        pane.matrixAutoUpdate = false;
        pane.matrix.copy(o.matrixWorld);
        this.group.add(pane);
        this.panes.push({ pane, step, speeds: [2.1 + random() * 3.5, 5.3 + random() * 6], phases: [random() * 6.28, random() * 6.28], dip: random() });
      });
    }
    scene.add(this.group);
  }
  set(t, { amount = 0, steps = [] } = {}) {
    for (const p of this.panes) {
      const on = amount > 0 && steps.includes(p.step);
      p.pane.visible = on;
      if (!on) continue;
      const wave = 0.5 + 0.3 * Math.sin(t * p.speeds[0] + p.phases[0]) + 0.2 * Math.sin(t * p.speeds[1] + p.phases[1]);
      // now and then a machine's shadow passes the window: a short dip
      const passing = Math.max(0, Math.sin(t * 0.7 + p.dip * 20)) ** 12;
      p.pane.material.opacity = amount * (0.12 + 0.3 * wave) * (1 - 0.7 * passing);
    }
  }
}

// ------------------------------------------------------------------------------------------ the gates

// A pair of gate leaves (own surfaces, never in a plate: plan 34, "The gates are never in a plate"), each turning on
// its hinge at its outer edge, swinging into the yard. set(angle, moving): the leaves' angle in degrees (0 shut) and
// whether they are swinging now (then they are drawn every frame; at rest they are part of the held set).
class Gate {
  constructor(root, chain) {
    this.root = root;
    this.chain = chain;
    this.leaves = [];
    root.updateMatrixWorld(true);
    const parts = [];
    root.traverse((o) => { if (o.isMesh) parts.push(o); });
    const box = new THREE.Box3().setFromObject(root);
    const middle = box.getCenter(new THREE.Vector3()).x;
    for (const side of ['left', 'right']) {
      const leaf = parts.find((o) => o.name.includes(`${side}_door`) || o.name.includes(`${side}-leaf`));
      if (!leaf) continue;
      const leafBox = new THREE.Box3().setFromObject(leaf);
      const hinge = new THREE.Vector3(side === 'left' ? leafBox.min.x : leafBox.max.x, 0, (leafBox.min.z + leafBox.max.z) / 2);
      const pivot = new THREE.Group();
      pivot.position.copy(root.worldToLocal(hinge.clone()));
      root.add(pivot);
      pivot.attach(leaf);
      this.leaves.push({ side, pivot });
    }
    // a bolt between the leaves goes with the left one
    const bolt = parts.find((o) => o.name.includes('bolt'));
    const left = this.leaves.find((l) => l.side === 'left');
    if (bolt && left) left.pivot.attach(bolt);
    this.middle = middle;
    this.angle = null;
    this.moving = null;
  }
  set(angle, moving = false) {
    if (angle !== this.angle) {
      for (const { side, pivot } of this.leaves) pivot.rotation.y = THREE.MathUtils.degToRad(side === 'left' ? angle : -angle);
      this.angle = angle;
    }
    if (moving !== this.moving) {
      for (const { pivot } of this.leaves) setMoving(pivot, moving);
      this.moving = moving;
    }
  }
}

// ------------------------------------------------------------------------------------------ the Works on a page

// Loads the Works and gives the page its controls. Options:
//   folder        where the Works' files are (WORKS_FOLDER)
//   views         the views this page shows, in order ('w1', 'w2', 'w3', 'w4'); two views of one place on a page
//                 share one set, and the projector moves between them at the cut (projected-set.js setView)
//   pictures      { name: file in folder } every picture this page shines onto the set (paintings, or the plates
//                 standing in for them, state pictures and behind paintings); each page names its own at its top
//   behind        the name of the behind painting (or null): it shows where the near things (hideInBehind) hid the set
//                 from the projector once the camera moves
//   hideInBehind  'men' (the waiting men) or a list of object names
export async function buildWorks(kit, { folder = WORKS_FOLDER, views, pictures, behind = null, hideInBehind = 'men' }) {
  // the blue dusk (as at the notice corner): the painting carries the light; the page's lamps only touch surfaces the
  // plate never saw and the own surfaces (gates, crates, lettering)
  kit.lightRig({ keyColour: 0xffc48a, keyShare: 0.35, keyFrom: [-3, 6, -14], keyTarget: [-3, 1.5, -22], fillSky: 0x50637e, fillGround: 0x1c1712,
    fillShare: 0.4, haze: 0x1a2330, hazeDensity: 0.004, shadowBox: 14, shadowSoftness: 6, background: 0x0e141c, reflections: 0.2 });
  kit.lights.key.castShadow = false;
  kit.camera.near = 0.1;
  kit.camera.far = 1700;   // the far town reaches about 900 m beyond the camera; the sky card stands at 1200 m

  const url = (file) => `${folder}/${file}`;
  const optional = (file) => loadModel(url(file)).catch(() => null);
  const facts = await fetch(url('works-shot.json')).then((r) => r.json());
  // the set: one file (works-set.glb) or the parts the Works assembly lists in works-shot.json's
  // "files" (works-set-lane.glb, works-set-factories.glb, works-set-town.glb, works-set-props.glb); all wear the painting
  const listed = Object.keys(facts.files ?? {}).filter((file) => file.startsWith('works-set')).sort();
  const setFiles = listed.length ? listed : ['works-set.glb'];
  // each picture file is loaded once, even when two names use it (page 3's state picture is also its behind painting)
  const pictureFiles = [...new Set(Object.values(pictures))];
  const [setParts, signs, gates, popUp, projectors, textures] = await Promise.all([
    Promise.all(setFiles.map((file) => loadModel(url(file)))), optional('works-signs.glb'), optional('works-gates.glb'), optional('works-pop-up.glb'),
    Promise.all(views.map((view) => loadProjector(url(`works-camera-${view}.json`)))),
    Promise.all(pictureFiles.map((file) => loadTexture(url(file)))),
  ]);
  const set = new THREE.Group();
  set.name = 'works-set';
  set.add(...setParts);
  const projectorOf = Object.fromEntries(views.map((view, i) => [view, projectors[i]]));
  const textureOf = new Map(pictureFiles.map((file, i) => [file, textures[i]]));
  const pictureOf = Object.fromEntries(Object.entries(pictures).map(([name, file]) => [name, textureOf.get(file)]));
  const picture = (name) => {
    if (!pictureOf[name]) throw new Error(`works-effects: no picture called "${name}" (the page's PICTURES name: ${Object.keys(pictureOf).join(', ')})`);
    return pictureOf[name];
  };
  const litPictures = Object.fromEntries(await Promise.all(GLASS_TYPES.map(async (type) => [type, await loadTexture(`${WORKS_FOLDER}/textures/${type}-lit.jpg`).catch(() => null)])));

  // the set: everything the painting is shone onto (with the men), the lettering keeping its own surfaces
  const everything = new THREE.Group();
  everything.add(set);
  if (signs) everything.add(signs);
  kit.scene.add(everything);
  everything.updateMatrixWorld(true);
  for (const name of ['sky_dome', 'sky-dome']) { const dome = set.getObjectByName(name); if (dome) dome.visible = false; }
  const named = (name) => everything.getObjectByName(name);
  const men = (facts.men ?? []).map(named).filter(Boolean);
  const hidden = hideInBehind === 'men' ? men : (hideInBehind ?? []).map(named).filter(Boolean);
  const firstView = views[0];
  // the bank's window glass keeps its own surface (so it can light on page 9: plan 34, "its own glass, dark until page 9")
  const bankGlassNames = new Set();
  set.traverse((o) => { if (o.isMesh) for (const m of [o.material].flat()) if (m.name.startsWith(BANK_WINDOW)) bankGlassNames.add(m.name); });

  // the people's own lights, steady (a light that flickered would change the held set between frames): they light
  // only the own surfaces and what the plate never saw; the flicker is drawn by the glows on top
  const coals = fromBlender([facts.brazier[0], facts.brazier[1], facts.coals_z]);
  const fireLight = new THREE.PointLight(0xff9a50, 3.2, 9, 2);
  fireLight.position.copy(facts.fire_light ? fromBlender(facts.fire_light) : coals.clone().add(new THREE.Vector3(0, 0.6, 0)));
  const lanternAt = facts.lantern_light ? fromBlender(facts.lantern_light) : null;
  kit.scene.add(fireLight);
  for (const at of Object.values(facts.gate_lamps ?? {})) {
    const lampLight = new THREE.PointLight(0xffc080, 1.6, 7, 2);
    lampLight.position.copy(fromBlender(at));
    kit.scene.add(lampLight);
  }

  const projection = projectPaintingOnto(kit, everything, picture(firstView), projectorOf[firstView], {
    ownSurface: [...LETTERING, ...bankGlassNames],
    behind: behind ? { painting: picture(behind), hide: hidden } : null,
    stretch: [2.0, 4.0],
  });

  // the sky: a card far beyond the far town, square to the projector and wider than its frame, wearing the painting's
  // sky alone (so sky uncovered when the camera moves is painted sky); made again for each view
  const skyGroup = new THREE.Group();
  const skyCard = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff, fog: false }));
  skyCard.material.name = 'sky card';
  skyGroup.add(skyCard);
  kit.scene.add(skyGroup);
  const skyDistance = 1200;
  const placeSkyCard = (projector) => {
    const height = 2 * skyDistance * Math.tan(THREE.MathUtils.degToRad(projector.fov / 2)) * 1.6;
    skyCard.scale.set(height * 1.5, height, 1);
    skyCard.position.copy(projector.position).addScaledVector(new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion), skyDistance);
    skyCard.quaternion.copy(projector.quaternion);
    skyGroup.updateMatrixWorld(true);
  };
  placeSkyCard(projectorOf[firstView]);
  const skies = new Map();   // view|painting -> { texture, colour }
  const skyFor = (view, paintingName) => {
    const key = `${view}|${paintingName}`;
    if (!skies.has(key)) {
      const painting = picture(paintingName);
      skies.set(key, { texture: paintedSkyOnly(projection, painting), colour: paintedSkyColour(painting) });
    }
    return skies.get(key);
  };
  const firstSky = skyFor(firstView, firstView);
  const skyProjection = projectPaintingOnto(kit, skyGroup, firstSky.texture, projectorOf[firstView], { calibrate: false, averageColour: firstSky.colour, darken: 1, tint: 1, matte: false });
  const showSky = (sky) => {
    skyProjection.materials[0].color.setRGB(sky.colour.r / skyProjection.fallbackTint.x, sky.colour.g / skyProjection.fallbackTint.y, sky.colour.b / skyProjection.fallbackTint.z);
    kit.scene.background = sky.colour.clone();
  };
  showSky(firstSky);

  // own surfaces outside the projection (never in a plate, so they must not hide the painted yard behind them from
  // the projector): the gate leaves, the chain and padlock, the pop-up crates
  const gate = {};
  if (gates) {
    kit.scene.add(gates);
    gates.updateMatrixWorld(true);
    for (const prefix of ['no-1', 'no-2']) {
      const root = gates.getObjectByName(`${prefix}-gate`);
      if (root) gate[prefix] = new Gate(root, gates.getObjectByName(`${prefix}-chain`));
    }
    gates.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });
  }
  const crates = [];
  if (popUp) {
    kit.scene.add(popUp);
    popUp.updateMatrixWorld(true);
    for (let k = 1; k <= 6; k++) {
      const crate = popUp.getObjectByName(`no-1-crate-${k}`);
      if (crate) crates.push({ crate, rest: crate.position.clone(), order: k - 1 });
    }
  }

  // the moving things: marked moving as they are made
  const effectsDone = kit.movingFromHere();
  const smokes = {};
  for (const name of ['no-1-chimney-top', 'no-2-chimney-a-top', 'no-2-chimney-b-top']) {
    const marker = named(name);
    if (marker) smokes[name] = new ChimneySmoke(kit.scene, marker.getWorldPosition(new THREE.Vector3()), SEEDS[name]);
  }
  const brazierTop = coals.clone().add(new THREE.Vector3(0, 0.12, 0));
  const fireGlow = glow(0xff9a40, 1.4, 0.38); fireGlow.position.copy(brazierTop); kit.scene.add(fireGlow);
  const flames = new Flames(kit.scene, coals, { seed: SEEDS.flames });
  const sparks = new Sparks(kit.scene, coals.clone().add(new THREE.Vector3(0, 0.08, 0)), { seed: SEEDS.sparks });
  const brazierSmoke = new Smoke(kit.scene, { count: 14, life: 3.6, seed: SEEDS.brazierSmoke, colour: [150, 146, 140] });
  for (const puff of brazierSmoke.puffs) puff.sprite.material.color.setRGB(0.5, 0.48, 0.46);
  const lanternGlow = lanternAt ? glow(0xffb060, 0.34, 0.5) : null;
  if (lanternGlow) { lanternGlow.position.copy(lanternAt); kit.scene.add(lanternGlow); }
  const gateLampGlows = Object.fromEntries(Object.entries(facts.gate_lamps ?? {}).map(([prefix, at]) => {
    const lamp = glow(0xffc888, 0.9, 0.42);
    lamp.position.copy(fromBlender(at));
    kit.scene.add(lamp);
    return [prefix, lamp];
  }));
  const flicker = { 'no-1': new WindowFlicker(kit.scene, set, 'no-1', SEEDS['no-1-windows'], litPictures),
    'no-2': new WindowFlicker(kit.scene, set, 'no-2', SEEDS['no-2-windows'], litPictures) };
  effectsDone();

  // the bank's window (page 9): its glass glows when lit; a set change (part of the still key)
  const bankGlass = [];
  set.traverse((o) => { if (o.isMesh && [o.material].flat().some((m) => m.name.startsWith(BANK_WINDOW))) bankGlass.push(o); });

  // -------------------------------------------------------------------------------- applying a moment's state
  const now = { view: firstView, painting: firstView, behind, blendTo: null, blend: 0, men: true, bank: false };
  const showMen = (shown) => {
    if (shown === now.men) return;
    for (const man of men) man.visible = shown;
    now.men = shown;
    projection.refresh();   // the distance map again, with or without them
  };
  const showView = (view, paintingName, behindName) => {
    if (view === now.view && paintingName === now.painting && behindName === now.behind) return;
    if (view !== now.view) {
      projection.setView(projectorOf[view], picture(paintingName), behindName ? picture(behindName) : undefined);
      now.blendTo = null; now.blend = 0;   // a new view starts with no blend
      placeSkyCard(projectorOf[view]);
      // the sky from the view's own main painting when the page has it (every state picture has the same sky)
      const sky = skyFor(view, pictureOf[view] ? view : paintingName);
      skyProjection.setView(projectorOf[view], sky.texture);
      showSky(sky);
    } else {
      projection.setPainting(picture(paintingName), behindName ? picture(behindName) : undefined);
    }
    now.view = view; now.painting = paintingName; now.behind = behindName;
  };
  const showBlend = (toName, amount) => {
    if (toName === now.blendTo && amount === now.blend) return;
    if (toName && amount > 0) projection.blendTo(picture(toName), amount);
    else projection.blendTo(picture(now.painting), 0);
    now.blendTo = amount > 0 ? toName : null; now.blend = amount > 0 ? amount : 0;
  };
  const showBank = (lit) => {
    if (lit === now.bank) return;
    for (const mesh of bankGlass) for (const m of [mesh.material].flat()) { m.emissive?.setRGB(lit ? 1.0 : 0, lit ? 0.62 : 0, lit ? 0.3 : 0); m.emissiveIntensity = lit ? 1.4 : 1; }
    now.bank = lit;
  };
  // crates popping up: progress from 0 (hidden) to 1 (landed); each crate springs up in turn
  let cratesKey = 'none';
  const showCrates = (t, at) => {
    let key = 'none';
    if (at !== undefined && t >= at) key = t - at > 0.35 + 0.15 * crates.length ? 'landed' : 'popping';
    for (const { crate, rest, order } of crates) {
      const age = at === undefined ? -1 : t - at - order * 0.15;
      crate.visible = age >= 0;
      if (age < 0) continue;
      const grow = 1 - spring(age, { stiffness: 14, damping: 0.55 });
      crate.scale.setScalar(Math.max(0.001, grow));
      crate.position.set(rest.x, rest.y - 0.25 * (1 - Math.min(1, grow)), rest.z);
    }
    if (key !== cratesKey) { if (popUp) setMoving(popUp, key === 'popping'); cratesKey = key; }
    return key;
  };

  // set(t, state): puts the Works as they are at moment t and returns the still key. state:
  //   view, painting (names), behind (name of the behind painting for this view, or null)
  //   blendTo, blend: a second picture and how far toward it (0 to 1; use steppedBlend so it changes in steps)
  //   men: the waiting men shown (they are in the painting; hiding them redraws the distance map)
  //   no1, no2: { state (a STATES name), gate (degrees, or leave out for the state's own), gateMoving, busy (0 to 1:
  //              the windows flicker brighter), litSteps ([1, 2, 3]: which windows flicker), smokeFrom (seconds: smoke
  //              starts here and builds up), crates (no1 only: the moment the crates pop up) }
  //   bank: the bank's window lit
  function setWorks(t, state) {
    showView(state.view, state.painting ?? state.view, state.behind ?? null);
    showBlend(state.blendTo ?? null, state.blend ?? 0);
    showMen(state.men ?? true);
    showBank(state.bank ?? false);
    const keys = [];
    for (const prefix of ['no-1', 'no-2']) {
      const given = state[prefix === 'no-1' ? 'no1' : 'no2'] ?? {};
      const settings = STATES[prefix][given.state ?? (prefix === 'no-1' ? 'quiet' : 'flat out')];
      const angle = given.gate ?? settings.gate;
      const moving = !!given.gateMoving;
      const chained = settings.chained && angle < 1;
      if (gate[prefix]) {
        gate[prefix].set(angle, moving);
        if (gate[prefix].chain) gate[prefix].chain.visible = chained;
      }
      keys.push(`${prefix}:${moving ? 'swinging' : angle.toFixed(1)}${chained ? ' chained' : ''}`);
      // smoke
      const smokeKind = settings.smoke;
      const smoking = smokeKind === 'thin' ? THIN_CHIMNEYS[prefix] : smokeKind === 'none' ? [] : CHIMNEYS[prefix];
      for (const name of CHIMNEYS[prefix]) smokes[name]?.set(t, { kind: smoking.includes(name) ? smokeKind : 'none', from: given.smokeFrom ?? -Infinity });
      // window flicker: the lit steps (a third lit = step 1), brighter when busy
      const litSteps = given.litSteps ?? (settings.windows >= 1 ? [1, 2, 3] : settings.windows > 0 ? [1] : []);
      const amount = settings.flicker + (settings.busy ? (settings.busy - settings.flicker) * clamp01(given.busy ?? 0) : 0);
      flicker[prefix].set(t, { amount, steps: litSteps });
    }
    keys.push(`crates:${showCrates(t, state.no1?.crates)}`);
    // the fire, the lantern and the gate lamps (always lit at No. 1; the gate lamps on both piers)
    const fireFlicker = 0.75 + 0.15 * Math.sin(t * 17.3) + 0.1 * Math.sin(t * 29.1 + 1.3);
    fireGlow.material.opacity = 0.38 * fireFlicker;
    fireGlow.scale.setScalar(1.35 + 0.02 * Math.sin(t * 11.7));
    flames.set(t);
    sparks.set(t);
    brazierSmoke.set({ t, origin: brazierTop.clone().add(new THREE.Vector3(0, 0.35, 0)).toArray(), scale: 0.75, wind: 0.9 });
    if (lanternGlow) lanternGlow.material.opacity = 0.5 * (0.9 + 0.06 * Math.sin(t * 9.1) + 0.04 * Math.sin(t * 23.7 + 0.6));
    for (const [prefix, lamp] of Object.entries(gateLampGlows)) {
      const seed = prefix === 'no-1' ? 0 : 2.1;
      lamp.material.opacity = 0.42 * (0.95 + 0.03 * Math.sin(t * 4.3 + seed) + 0.02 * Math.sin(t * 13.1 + seed));
    }
    return [now.view, now.painting, now.behind ?? '-', now.blendTo ? `${now.blendTo}@${now.blend.toFixed(3)}` : '-', now.men ? 'men' : 'no men',
      now.bank ? 'bank lit' : 'bank dark', ...keys].join('|');
  }

  // where a view's camera stands: its plate spot or its composed frame, level, facing as its projector faces, with the
  // film's lens (a little narrower than the plate's), focused on the gate's distance
  const cameraAt = (view, spot = 'plate') => {
    const projector = projectorOf[view];
    const place = facts.views?.[view]?.[spot] ? fromBlender(facts.views[view][spot]) : projector.position.clone();
    const ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(projector.quaternion);
    const subject = facts.views?.[view]?.subject ? fromBlender(facts.views[view].subject) : null;
    const focus = subject ? subject.clone().sub(place).dot(ahead) : 13;
    return { position: place.toArray(), target: place.clone().addScaledVector(ahead, 10).toArray(), fov: facts.film_fov_degrees ?? 60.4, focus };
  };

  // named spots, for labels and arrows (three.js points)
  const boxCentre = (objects, lift = 0.5) => {
    const box = new THREE.Box3();
    for (const o of objects) if (o) box.expandByObject(o);
    if (box.isEmpty()) return null;
    const centre = box.getCenter(new THREE.Vector3());
    centre.y = box.min.y + (box.max.y - box.min.y) * lift;
    return centre;
  };
  const marker = (name) => named(name)?.getWorldPosition(new THREE.Vector3()) ?? null;
  // a factory's lit sheds as the lane sees them: the upper window of its mill front nearest the lane's middle (the
  // window groups also hold the back walls and the roof lanterns, so the middle of a whole group lies deep inside the
  // mill, behind the terraces in W3)
  const frontWindow = (prefix) => {
    let best = null;
    for (const step of [1, 2, 3]) {
      named(`${prefix}-windows-step-${step}`)?.traverse((o) => {
        if (!o.isMesh || !o.name.includes('window-front-upper')) return;
        const centre = new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());
        if (!best || Math.abs(centre.x) < Math.abs(best.x)) best = centre;
      });
    }
    return best;
  };
  const spots = {
    'no-1-queue': () => boxCentre(men.slice(2, 5), 0.85),
    'no-1-gate': () => (gate['no-1'] ? boxCentre([gate['no-1'].root], 0.45) : null),
    'no-2-gate': () => (gate['no-2'] ? boxCentre([gate['no-2'].root], 0.45) : null),
    'no-1-gateway': () => (facts['no-1-gateway'] ? fromBlender(facts['no-1-gateway']).add(new THREE.Vector3(0, 1.2, 0)) : null),
    'no-2-crates': () => (facts['no-2-crates'] ? fromBlender(facts['no-2-crates']).add(new THREE.Vector3(0, 0.3, 0)) : null),
    'no-2-sheds': () => frontWindow('no-2') ?? boxCentre([named('no-2-windows-step-1'), named('no-2-windows-step-2'), named('no-2-windows-step-3')], 0.5),
    'no-1-sheds': () => frontWindow('no-1') ?? boxCentre([named('no-1-windows-step-1'), named('no-1-windows-step-2'), named('no-1-windows-step-3')], 0.5),
    'no-1-chimney': () => marker('no-1-chimney-top'),
    'no-2-chimneys': () => { const a = marker('no-2-chimney-a-top'), b = marker('no-2-chimney-b-top'); return a && b ? a.clone().lerp(b, 0.5) : a ?? b; },
    'no-2-chimney-a': () => marker('no-2-chimney-a-top'),
    'no-2-chimney-b': () => marker('no-2-chimney-b-top'),
  };
  const spotAt = (name, { down = 0 } = {}) => {
    const point = spots[name]?.();
    if (!point) return null;
    point.y -= down;
    return point;
  };
  // where a spot is on the frame now (call from draw2D, after the camera is placed); down: metres below the spot
  const screen = (name, options) => {
    const point = spotAt(name, options);
    return point ? kit.toScreen(point) : null;
  };

  // the name tags (TAGS), drawn the same way on every page (call from draw2D). In W3: each on its own factory's
  // chimneys, QUIET on No. 1's round one and FLAT OUT between No. 2's two square ones, low on the shafts (y, the tags'
  // bottom), below the rule cards and the ends of their lines (page 5). (Placed in the sky to the left of each
  // factory's chimneys, as first drawn, QUIET stood over the far town's gasholder and FLAT OUT between the two
  // factories.) In W2: No. 2's tag over its gate (a first place, to be checked when pages 6, 11 and 12 are built).
  // slowsAt: from this moment No. 2's tag reads THE FLAT-OUT FACTORY SLOWS (the old words fade out as the new come in).
  const drawTags = (ctx, t, { at, until = Infinity, view = 'w3', slowsAt = Infinity, y = 700 }) => {
    let no1Place = null, no2Place = null;
    if (view === 'w3') {
      const no1 = screen('no-1-chimney'), a = screen('no-2-chimney-a'), b = screen('no-2-chimney-b');
      if (no1) no1Place = { x: no1.x, y };
      if (a) no2Place = { x: b ? (a.x + b.x) / 2 : a.x, y };
    } else {
      const gate2 = screen('no-2-gate');
      if (gate2) no2Place = { x: gate2.x, y: Math.max(560, gate2.y - 330) };
    }
    if (no1Place) nameTag(ctx, t, { at, until, text: TAGS.quiet, ...no1Place });
    if (no2Place) {
      nameTag(ctx, t, { at: at + (view === 'w3' ? 0.15 : 0), until: Math.min(until, slowsAt), text: TAGS.flatOut, ...no2Place });
      if (slowsAt < until) nameTag(ctx, t, { at: slowsAt, until, text: TAGS.slows, ...no2Place });
    }
  };

  return { set: setWorks, cameraAt, screen, spotAt, drawTags, facts, projection, men, gate, crates, smokes, views: projectorOf };
}
