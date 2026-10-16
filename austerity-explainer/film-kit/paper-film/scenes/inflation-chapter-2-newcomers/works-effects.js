// What this does: the Works on a page of chapter 2 for newcomers (plan 34, part 1 "A. The Works", and "How the two
// factories stay the same", point 8): it loads the Works set (the two factories at the head of one lane, built in
// Blender), shines the view's painting onto it (projected-set.js), and draws the Works' moving things on top: chimney
// smoke from the chimney tops (blown across the view), the brazier's flames, sparks, smoke and glow (burning lower
// after a time cut) and the lantern's flicker at No. 1, the windows' flicker (with page 4's burst on "busy": No. 2's
// doorway and the stone round its windows brightening in three warm pulses, with sparks at the lathe), the gate lamps'
// glow, the gate leaves (their own sharp surfaces, never in a plate) that can swing,
// the crates that pop up in No. 1's open gateway, the bank's window lighting (with its sign kept dim until then), No.
// 2's eight waiting men (painted in W2's slowed picture, dark silhouettes in W4), and the factories' windows changing
// in steps. Every page that shows the Works uses this one file, so the four states and their settings, the smoke and
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
// works-pop-up.glb (No. 1's pop-up crates), works-no-2-men.glb (No. 2's eight waiting men, pages 12 and 14),
// works-camera-VIEW.json (each view's plate camera, the projector) and
// works-shot.json (where things are, Blender space: views with their plate and composed spots, the brazier, the
// lantern, the gate lamps, the gates, the men's names), all written into WORKS_FOLDER by assemble_works.py.
// What this file looks for in them (so the real export can match, or this list be changed in one place):
//   works-shot.json   film_fov_degrees; views.{w1,w2,w3,w4}.plate and .composed (the camera's two spots) and
//                     .subject (what it is focused on); brazier [x, y], coals_z, fire_light, lantern_light;
//                     gate_lamps.{no-1,no-2}; men (the waiting men's object names) and men_at_no_1 (each with its
//                     figure); no-1-gateway (where the pop-up crates stand); gates.no-1.chain (where the NEW MONEY
//                     arrow points); no-2-crates (the crates in No. 2's gateway); machines.no-2-flywheel and
//                     machines.no-1-looms (the machines in the lit doorways; MACHINES points at No. 2's flywheel)
//   works-set.glb     the markers no-1-chimney-top, no-2-chimney-a-top, no-2-chimney-b-top (smoke) and the window
//                     groups no-1-windows-step-1 to 3 and no-2-windows-step-1 to 3 (flicker), as build_factories.py
//                     names them, and each factory's lit doorway room (no-2-doorway-inside, no-2-doorway-room; the
//                     burst's pulse); the bank's glass in a material named bank-window... (page 9)
//   works-gates.glb   no-1-gate and no-2-gate, each holding a left and a right leaf (names containing left_door /
//                     right_door, or left-leaf / right-leaf) and a bolt; no-1-chain (the chain and padlock)
//   works-pop-up.glb  no-1-crate-1, no-1-crate-2 ... (popping up in that order)
//   works-signs.glb   bank-sign-board (the bank's hanging sign: its board and the lettering bank-sign-lettering)
//   works-no-2-men.glb no-2-man-1 to no-2-man-8, each with a ...-foot-shadow patch
// Missing pieces are left out quietly (no gates, no crates, no smoke from a chimney without its marker).
import { THREE, seededRandom, clamp01, spring } from '../cinema-kit.js';
import { loadTexture, canvasTexture, MOVING_LAYER } from '../../stage/cinema-stage.js';
import { loadModel } from '../model-loader.js';
import { loadProjector, projectPaintingOnto, paintedSkyOnly } from '../projected-set.js';
import { glow, Flames, Sparks, paintedSkyColour, groundUnder } from '../pit-village-effects.js';
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
// rise and drift: how far it climbs and is blown; mouth: for its first `seconds` a puff is small (from `size` metres,
// about the chimney's mouth, to size[0]) and stays close to the mouth, so the plume leaves the chimney as one body;
// size: its width after that and at the end; opacity: its strongest; fade: how soon a puff thins as it ages (the power
// of what is left of its life: lower keeps it thick for longer). colour: a brownish coal smoke, as seen against the
// dusk (0 to 255, about as on screen).
// The wind blows across the views (round 5 of log 34): toward No. 1's side and a little away up the works, sinking a
// little, so each plume lies on its side as a long trail. Measured with round5-pages/tools/smoke_trace.py: in W3 No.
// 2's plumes run left from their chimneys at about 0.24 to 0.29 down, under the lower rule card (it ends 0.236 down),
// fading out by about 0.45 across, before they reach No. 1's chimney (0.375 across; longer plumes ran on behind it and
// read as its smoke); No. 1's (from "made" on page 5) runs left toward the bank; in W1 and W2 the plumes run left
// along the top of the frame, under the words, for about a quarter of the frame's width. The smoke hardly climbs and
// sinks a little as it goes, so in W3 No. 1's plume comes out under the lower rule card, which hides the chimney's
// mouth from "nothing" on (the card's line lands on No. 1's lit windows). (Blown away from the cameras, as in round 4, the puffs
// piled up one behind another in a small patch, and their slightly different shades showed as rings: a pale doughnut
// and a hook over No. 2's chimneys. Drawn with and without the focus blur, the rings were the same.)
// No. 2's heavy smoke is a shorter plume from round 6 (its puffs live 4.6 s and are blown 9.5 m, so they move as fast as
// before but fade out sooner): in W3 it fades out by about 0.50 across, well before No. 1's chimney (0.375), where its
// last faint part had seemed to hang round No. 1's quiet chimney (round 5's critique, finding 13).
export const SMOKE = {
  heavy: { count: 30, life: 4.6, rise: 0.45, drift: 9.5, mouth: { seconds: 1.6, size: 1.9 }, size: [3.4, 7.5], opacity: 0.95, fade: 2.2, colour: [100, 92, 84] },
  // No. 1 working: seen from W1 (page 3, from "start") and W3 (page 5, from "made")
  working: { count: 36, life: 7.0, rise: 0.6, drift: 15, mouth: { seconds: 2, size: 1.7 }, size: [3.0, 8], opacity: 0.93, fade: 1.8, colour: [104, 96, 88] },
  thin: { count: 14, life: 7.0, rise: 0.5, drift: 14, mouth: { seconds: 2, size: 1.3 }, size: [1.8, 6], opacity: 0.5, fade: 1.9, colour: [100, 94, 88] },
};
// the wind: the same on every page and in every view, so the smoke always leans the same way: across the views toward
// No. 1's side (-x), a little away up the works (three.js axes: -z is away from the lane's cameras) and sinking a little
export const WIND = new THREE.Vector3(-0.85, -0.12, -0.5).normalize();
// across the wind, level: puffs spread to either side of the plume's line (so it reads as a broad plume, not a string)
const ACROSS_WIND = new THREE.Vector3(-WIND.z, 0, WIND.x).normalize();
// fixed seeds: the same smoke and flicker on every page
export const SEEDS = { 'no-1-chimney-top': 41, 'no-2-chimney-a-top': 52, 'no-2-chimney-b-top': 63, brazierSmoke: 21, flames: 17, sparks: 11,
  'no-1-windows': 71, 'no-2-windows': 72, latheSparks: 31 };
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
// a gate view's name tag stands on the gable over its gate, this high up the works' front (metres)
const TAG_HEIGHT = 5.6;
// the bank's window glass, lit from page 9 (a material whose name starts with this)
const BANK_WINDOW = 'bank-window';
// The bank's hanging sign (plan 34: the bank stays dim until page 9). Lit by the gas lamp beside it in the plate, its
// BANK was the largest, clearest lettering in W3 (about 29-pixel letters against about 14 on the No. 1 and No. 2
// boards), read before the factories' names on pages that never mention a bank (round 3 of log 34). Its board and
// lettering are own surfaces, dimmed to this share of their lit brightness until the bank's window lights (page 9),
// then brightened with the window. The board gets its own copy of the board paint (shared with the gate boards).
// Dimmed to 0.3 (round 4) its letters were still twice the size of the factories' and easy to read on a phone; at
// 0.15 (round 5) BANK was still a whole word you could read in W3, on pages that never mention a bank; 0.07 from round 6.
export const BANK_SIGN = { board: 'bank-sign-board', lettering: 'bank-sign-lettering', boardPaint: 'board-black-paint', ownBoardPaint: 'bank-sign-board-paint', dim: 0.07 };
// The drums' stencilled PETROL and DIESEL (own surfaces, lit by the fire and the gate lamps) kept below the gate
// board's letters, so the subject stays the brightest thing (round 5's critique, finding 5: the white letters reached
// 219 to 224 levels on screen in W1 and 202 in W2, against 153 and 110 for the boards' letters, and pulled the eye into
// the bottom-left corner). Their paint is darkened to this share of its own brightness, by view (own surfaces are
// matched to the painting once, in the page's first view, and W1 is drawn brighter: page 3's LOOK_W1).
export const DRUM_LETTERS = { materials: ['steel-drum-petrol-stencil', 'steel-drum-diesel-stencil'], dim: { w1: 0.12, w2: 0.18, w3: 0.5, w4: 0.5 } };
// The brazier after a time cut (the people test, lesson 136 of log 34: when only the people change at a cut, they seem to
// blink out; the fire burning lower says time has passed). fire: 1 burning as when the men stood round it; lower
// shares give shorter, narrower flames, a smaller and dimmer glow, fewer sparks and a dimmer fire light.
// FIRE_AFTER_A_WHILE is the share the pages use after "go" (page 3) and "made" (page 5).
export const FIRE_AFTER_A_WHILE = 0.4;
// the pool of light the lit bank window throws on the pavement in front of it (page 9), in metres
const BANK_POOL = { width: 3.4, depth: 2.4, out: 1.3, strength: 0.55 };
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
// The picture is white all over and the blobs are only in how see-through it is: a canvas keeps no colour where it is
// fully see-through, so its own picture would fade toward black at the puff's soft edge when shrunk.
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
  const drawn = ctx.getImageData(0, 0, 128, 128).data;
  const pixels = new Uint8Array(128 * 128 * 4).fill(255);
  for (let i = 0; i < 128 * 128; i++) pixels[i * 4 + 3] = drawn[i * 4 + 3];
  const texture = new THREE.DataTexture(pixels, 128, 128, THREE.RGBAFormat);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.magFilter = THREE.LinearFilter; texture.minFilter = THREE.LinearMipmapLinearFilter; texture.generateMipmaps = true;
  texture.needsUpdate = true;
  return texture;
}
const PUFF_PICTURES = [];
const puffPictures = () => {
  if (!PUFF_PICTURES.length) for (const seed of [3, 7, 12, 19]) PUFF_PICTURES.push(puffPicture(seed));
  return PUFF_PICTURES;
};

// Smoke rising from a chimney top and blown by the wind. Each puff's place depends only on t: puffs are born one
// after another for ever; set(t, { kind, from }) shows those born after `from` (so smoke can start on a word and build
// up from the chimney's mouth) with the kind's settings. A change of kind on a word (No. 2 slowing on page 12: heavy
// to thin, or none): set(t, { kind, earlier: { kind, until } }) lets the puffs of the earlier kind born before `until`
// live out their lives and drift away, while the new kind's puffs are born from `until` on (a second set of puffs),
// so the smoke thins rather than jumping.
export class ChimneySmoke {
  constructor(scene, top, seed) {
    this.top = top;
    const random = seededRandom(seed);
    const pictures = puffPictures();
    const most = Math.max(...Object.values(SMOKE).map((s) => s.count));
    const pool = () => Array.from({ length: most }, (_, i) => {
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: pictures[i % pictures.length], transparent: true, depthWrite: false, opacity: 0 }));
      sprite.visible = false;
      scene.add(sprite);
      // shade: each puff a little lighter or darker than the kind's colour (kept close: puffs seen one over another
      // showed their outlines as rings when the shades were 0.72 to 1.14 apart)
      return { sprite, order: i, jitter: random() * 0.6, sway: random() * Math.PI * 2, spin: (random() - 0.5) * 0.25, turn: random() * Math.PI * 2,
        size: 0.8 + random() * 0.45, shade: 0.93 + random() * 0.14, side: (random() - 0.5) * 0.5, lift: random() - 0.5 };
    });
    this.puffs = pool();
    this.earlierPuffs = pool();
  }
  set(t, { kind = 'none', from = -Infinity, earlier = null } = {}) {
    const changeAt = earlier ? earlier.until : -Infinity;
    this.place(this.puffs, t, SMOKE[kind], Math.max(from, changeAt), Infinity);
    this.place(this.earlierPuffs, t, earlier ? SMOKE[earlier.kind] : null, from, changeAt);
  }
  // shows the puffs of one kind (settings) born from bornFrom until bornUntil
  place(puffs, t, settings, bornFrom, bornUntil) {
    for (const puff of puffs) {
      if (!settings || puff.order >= settings.count) { puff.sprite.visible = false; continue; }
      const { life, count } = settings;
      const offset = (puff.order + puff.jitter) / count * life;
      const born = offset + Math.floor((t - offset) / life) * life;
      const age = t - born;
      if (born < bornFrom || born >= bornUntil || age < 0 || age > life) { puff.sprite.visible = false; continue; }
      const k = age / life;
      const climb = settings.rise * Math.pow(k, 0.75), blown = settings.drift * Math.pow(k, 1.25);
      // the plume widens as it goes: to either side of its line, and a little up and down
      const across = (0.9 * Math.sin(puff.sway + age * 0.9) + puff.side * 6) * k;
      puff.sprite.visible = true;
      puff.sprite.position.set(this.top.x + WIND.x * blown + ACROSS_WIND.x * across, this.top.y + 0.3 + climb + WIND.y * blown + puff.lift * 3 * k,
        this.top.z + WIND.z * blown + ACROSS_WIND.z * across);
      // small and close at the mouth for its first seconds (the plume attached to the chimney), then widening
      const { seconds: mouthFor, size: mouthSize } = settings.mouth;
      const opened = Math.min(1, age / mouthFor);
      const width = age < mouthFor ? mouthSize + (settings.size[0] - mouthSize) * opened
        : settings.size[0] + (settings.size[1] - settings.size[0]) * Math.pow((age - mouthFor) / (life - mouthFor), 0.8);
      const size = width * (1 + (puff.size - 1) * opened);
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.rotation = puff.turn + puff.spin * age;
      const [r, g, b] = settings.colour.map((c) => Math.min(255, c * puff.shade) / 255);
      puff.sprite.material.color.setRGB(r, g, b, THREE.SRGBColorSpace);
      puff.sprite.material.opacity = settings.opacity * Math.min(1, age / 0.2) * Math.pow(1 - k, settings.fade ?? 1.3);
    }
  }
}

// The brazier's smoke, on the same WIND as the chimneys (round 5's critique, finding 13: it drifted right while the
// chimneys' trails blew left): the shared Smoke's puffs (effects.js), each rising from the coals and blown along the
// wind's level direction, swaying a little across it. set({ t, origin, scale, drift }): origin [x, y, z] above the
// coals; scale: the puffs' size and climb (as Smoke's); drift: how far (in `scale`s) a puff is blown in its life.
class BrazierSmoke extends Smoke {
  set({ t, origin, scale = 1, drift = 0.9 }) {
    const along = new THREE.Vector3(WIND.x, 0, WIND.z).normalize();
    for (const puff of this.puffs) {
      const born = puff.offset + Math.floor((t - puff.offset) / this.life) * this.life;
      const age = t - born;
      if (age < 0 || age > this.life) { puff.sprite.visible = false; continue; }
      const k = age / this.life;
      const blown = scale * drift * k, sway = scale * 0.12 * Math.sin(puff.sway + age * 2.2);
      puff.sprite.visible = true;
      puff.sprite.position.set(origin[0] + along.x * blown + ACROSS_WIND.x * sway, origin[1] + scale * 1.7 * k, origin[2] + along.z * blown + ACROSS_WIND.z * sway);
      const size = scale * puff.size * (0.35 + 1.1 * k);
      puff.sprite.scale.set(size, size, 1);
      puff.sprite.material.opacity = 0.5 * Math.min(1, age / 0.25) * (1 - k);
    }
  }
}

// ------------------------------------------------------------------------------------------ window flicker

// A warm light over a factory's lit windows that flickers (machines moving in front of the gas light): a copy of each
// glass piece wearing its lit picture, drawn additively just in front of it. set(t, { amount, steps }) shows the panes
// of the lit steps (1, 2, 3) with a flicker of strength `amount` (0 none, 1 blazing); fading: { steps, amount } shows
// other steps going dark (a state change: No. 2's windows dimming as it slows).
// burst: { at } (page 4's "busy", plan 34 F8: "the windows flicker brighter"; round 6 of log 34): for BUSY.length
// seconds from `at` the factory works harder: its doorway and the stone round its windows brighten in BUSY.pulses warm
// pulses (each a soft patch that multiplies what is under it, so lit stone and the lit room brighten while the dark
// people at work stay dark), its panes flicker brighter with each pulse, and a few sparks fly at the lathe. Before the
// burst the panes carry a light shade (BUSY.headroom: the painted panes are near white, so this leaves them room to
// brighten); it lifts on the first pulse and stays off, so the brighter windows stay. (Round 5's burst passed a dark
// band across the panes and dimmed the doorway, and "busy" read as the lights dipping; round 4's could not be seen.)
//   pulses, floor: the pulses' number in BUSY.length seconds, and how bright the burst stays between them (share)
//   rise, fall: seconds the burst takes to come and to go; boost: how much brighter the panes flicker at a pulse's top
//   doorway, front: the warm brightening's colour at a pulse's top, over the doorway and over the windows' stone
//   (each colour's share added to what is there: 0.5 makes it half as bright again)
//   sparks: how many sparks at the lathe; sparkSize: their size, metres; sparkRise: how high they fly (share of the
//   shared Sparks' rise: kept low, so they show against the lathe's dark bed beside the man, not over his head)
export const BUSY = { length: 2.0, rise: 0.15, fall: 0.45, pulses: 3, floor: 0.45, boost: 3.0, headroom: 0.12,
  doorway: [1.3, 0.9, 0.48], front: [1.1, 0.76, 0.4], sparks: 16, sparkSize: 0.07, sparkRise: 0.3 };
// how strong the burst is at moment t (0 outside it): rising, three pulses over a floor, falling
export function burstStrength(t, at) {
  if (at === undefined || t < at || t >= at + BUSY.length) return 0;
  const age = t - at;
  const surge = Math.min(1, age / BUSY.rise, (BUSY.length - age) / BUSY.fall);
  const beat = Math.sin(Math.PI * BUSY.pulses * age / BUSY.length) ** 2;
  return surge * (BUSY.floor + (1 - BUSY.floor) * beat);
}
// a soft round picture for the warm brightening: white in the middle fading to black at the edge, solid (its colour
// is what it multiplies by, so it must carry the fall-off itself). holes: [{ u, v, width, height }] (shares of the
// picture, v up) left dark with soft edges: where the people at work stand, so they stay dark
function softBrightPicture(holes = []) {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, '#ffffff'); g.addColorStop(0.45, '#9a9a9a'); g.addColorStop(1, '#000000');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
  ctx.filter = 'blur(3px)';
  ctx.fillStyle = '#000000';
  for (const { u, v, width, height } of holes) {
    ctx.beginPath(); ctx.ellipse(u * 128, (1 - v) * 128, width * 64, height * 64, 0, 0, Math.PI * 2); ctx.fill();
  }
  return canvasTexture(canvas);
}
// a flat soft patch facing the lane's cameras that brightens what lies behind it (the result is what is there times
// one plus the patch's colour): see-through where its picture is black
function brighteningPatch(width, height, holes = []) {
  const material = new THREE.MeshBasicMaterial({ map: softBrightPicture(holes), color: 0x000000, transparent: true, depthWrite: false, fog: false,
    blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.DstColorFactor, blendDst: THREE.OneFactor });
  material.name = 'busy brightening';
  const patch = new THREE.Mesh(new THREE.PlaneGeometry(width, height), material);
  patch.visible = false;
  return patch;
}
class WindowFlicker {
  // keepDark: { camera (where the burst is seen from, three.js), people: [{ feet (three.js), height }] }: the people at
  // work in the doorway, left out of the doorway's brightening as that camera sees them
  constructor(scene, set, prefix, seed, litPictures, keepDark = null) {
    const random = seededRandom(seed);
    this.group = new THREE.Group();
    this.panes = [];
    set.updateMatrixWorld(true);
    const addPane = (o, step, picture, colour) => {
      const material = new THREE.MeshBasicMaterial({ map: picture ?? null, color: colour, transparent: true, opacity: 0,
        blending: THREE.AdditiveBlending, depthWrite: false, fog: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
      const pane = new THREE.Mesh(o.geometry, material);
      const shade = new THREE.Mesh(o.geometry, new THREE.MeshBasicMaterial({ color: 0x150d06, transparent: true, opacity: 0, depthWrite: false, fog: false,
        polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      shade.renderOrder = 1; pane.renderOrder = 2;   // the shade first, the light over it
      for (const mesh of [pane, shade]) { mesh.matrixAutoUpdate = false; mesh.matrix.copy(o.matrixWorld); this.group.add(mesh); }
      this.panes.push({ pane, shade, step, speeds: [2.1 + random() * 3.5, 5.3 + random() * 6], phases: [random() * 6.28, random() * 6.28], dip: random() });
    };
    const front = new THREE.Box3();
    for (const step of [1, 2, 3]) {
      const holder = set.getObjectByName(`${prefix}-windows-step-${step}`);
      if (!holder) continue;
      holder.traverse((o) => {
        if (!o.isMesh) return;
        const name = [o.material].flat()[0]?.name ?? '';
        const glassType = GLASS_TYPES.find((type) => name.includes(type));
        addPane(o, step, litPictures[glassType], 0xffb468);
        if (o.name.includes('window-front')) front.expandByObject(o);
      });
    }
    // the burst's warm brightening: one patch over the mill front's windows and the stone round them, one over the lit
    // doorway (its mouth and the stone round it), each just in front of the wall, toward the lane
    this.patches = [];
    if (!front.isEmpty()) {
      const size = front.getSize(new THREE.Vector3()), centre = front.getCenter(new THREE.Vector3());
      const patch = brighteningPatch(size.x * 1.5 + 2, size.y * 1.5 + 1);
      patch.position.set(centre.x, centre.y, front.max.z + 0.3);
      this.patches.push({ patch, colour: BUSY.front });
    }
    const doorway = new THREE.Box3();
    set.getObjectByName(`${prefix}-doorway-inside`)?.traverse((o) => { if (o.isMesh) doorway.expandByObject(o); });
    set.getObjectByName(`${prefix}-doorway-room`)?.traverse((o) => { if (o.isMesh) doorway.expandByObject(o); });
    if (!doorway.isEmpty()) {
      const size = doorway.getSize(new THREE.Vector3()), centre = doorway.getCenter(new THREE.Vector3());
      const width = size.x * 1.6 + 1.5, height = size.y * 1.5 + 1.2, planeZ = doorway.max.z + 0.4;
      // each person at work as the camera sees him on the patch's plane (a figure about 0.6 m wide), as a hole
      const holes = [];
      for (const { feet, height: tall } of keepDark?.people ?? []) {
        const along = (planeZ - keepDark.camera.z) / (feet.z - keepDark.camera.z);
        if (!(along > 0 && along < 1)) continue;
        const onPlane = (point) => keepDark.camera.clone().lerp(point, along);
        const low = onPlane(feet), high = onPlane(feet.clone().add(new THREE.Vector3(0, tall, 0)));
        holes.push({ u: (low.x - (centre.x - width / 2)) / width, v: ((low.y + high.y) / 2 - (centre.y - height / 2)) / height,
          width: (0.6 * along + 0.25) / width, height: ((high.y - low.y) / 2 + 0.2) / height });
      }
      const patch = brighteningPatch(width, height, holes);
      // at the room's open front (its largest z, nearest the lane), a little out from the wall
      patch.position.set(centre.x, centre.y, planeZ);
      this.patches.push({ patch, colour: BUSY.doorway });
    }
    for (const { patch } of this.patches) this.group.add(patch);
    scene.add(this.group);
  }
  set(t, { amount = 0, steps = [], fading = null, burst = null } = {}) {
    const pulse = burst ? burstStrength(t, burst.at) : 0;
    // the light shade before the burst (only on a page with a burst), lifting as the first pulse rises
    const headroom = burst && t < burst.at + BUSY.rise ? BUSY.headroom * (1 - clamp01((t - burst.at) / BUSY.rise)) : 0;
    for (const p of this.panes) {
      const strength = steps.includes(p.step) ? amount : fading && fading.steps.includes(p.step) ? fading.amount : 0;
      const on = strength > 0;
      p.pane.visible = on;
      p.shade.visible = on && headroom > 0;
      if (!on) continue;
      const wave = 0.5 + 0.3 * Math.sin(t * p.speeds[0] + p.phases[0]) + 0.2 * Math.sin(t * p.speeds[1] + p.phases[1]);
      // now and then a machine's shadow passes the window: a short dip
      const passing = Math.max(0, Math.sin(t * 0.7 + p.dip * 20)) ** 12;
      const boost = 1 + (BUSY.boost - 1) * pulse;
      p.pane.material.opacity = Math.min(1, strength * boost * (0.12 + 0.3 * wave) * (1 - 0.7 * passing));
      p.shade.material.opacity = headroom;
    }
    for (const { patch, colour } of this.patches) {
      patch.visible = pulse > 0 && steps.length > 0;
      if (patch.visible) patch.material.color.setRGB(colour[0] * pulse, colour[1] * pulse, colour[2] * pulse);
    }
    return pulse;
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

// ------------------------------------------------------------------------------------------ No. 2's men in W4

// The dark own surface of a waiting man seen from inside No. 2's yard (W4, page 14; plan 34, "People": dark
// silhouettes kept as their own surfaces, never painted, so the painter paints no faces): near-black wool with a rim
// of light from the lamp-lit lane behind them, strongest on the shoulders and cap, fading toward the feet; unlit by the
// page's lamps, so it stays a silhouette. The same look as the people test's silhouettes (people-test.js).
function silhouetteMaterial({ base = 0x050504, rim = 0xd9b98c, strength = 0.55, behind = [0.0, 0.45, -1.0] } = {}) {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      baseColour: { value: new THREE.Color(base) }, rimColour: { value: new THREE.Color(rim) },
      rimStrength: { value: strength }, lightBehind: { value: new THREE.Vector3(...behind).normalize() },
    },
    vertexShader: `
      varying vec3 vNormal; varying vec3 vToCamera; varying float vHeight;
      void main() {
        vec4 world = modelMatrix * vec4(position, 1.0);
        vHeight = world.y;   // height above the ground (the lane is level at about 0.1 m)
        vec4 viewPosition = viewMatrix * world;
        vToCamera = -viewPosition.xyz;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * viewPosition;
      }`,
    fragmentShader: `
      uniform vec3 baseColour; uniform vec3 rimColour; uniform float rimStrength; uniform vec3 lightBehind;
      varying vec3 vNormal; varying vec3 vToCamera; varying float vHeight;
      void main() {
        vec3 normal = normalize(vNormal);
        float edge = pow(1.0 - abs(dot(normal, normalize(vToCamera))), 3.0);   // 1 at the outline, 0 face-on
        float towardLight = clamp(dot(normal, lightBehind) + 0.35, 0.0, 1.0);   // the side the lane's light reaches
        float aboveFeet = smoothstep(0.2, 0.6, vHeight);
        gl_FragColor = vec4(baseColour + rimColour * rimStrength * edge * towardLight * aboveFeet, 1.0);
      }`,
  });
  material.name = 'figure silhouette';
  return material;
}

// A copy of a flat patch whose picture spans it once, edge to edge (the exported foot patches carry surface
// co-ordinates in metres, which would show only one edge of the soft picture).
function acrossItsSpan(geometry) {
  const copy = geometry.clone();
  copy.computeBoundingBox();
  const { min, max } = copy.boundingBox;
  const size = max.clone().sub(min);
  // the patch lies in its two longest directions
  const axes = ['x', 'y', 'z'].sort((a, b) => size[b] - size[a]).slice(0, 2);
  const position = copy.attributes.position, uv = new Float32Array(position.count * 2);
  for (let i = 0; i < position.count; i++) {
    const point = { x: position.getX(i), y: position.getY(i), z: position.getZ(i) };
    uv[i * 2] = (point[axes[0]] - min[axes[0]]) / Math.max(1e-6, size[axes[0]]);
    uv[i * 2 + 1] = (point[axes[1]] - min[axes[1]]) / Math.max(1e-6, size[axes[1]]);
  }
  copy.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return copy;
}

// A soft dark round picture for a contact shadow: darkest in the middle, fading to nothing at the edge of its square.
function softShadowPicture() {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,0.85)'); g.addColorStop(0.5, 'rgba(0,0,0,0.5)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
  return canvasTexture(canvas);
}

// A soft round patch drawn on the ground (a pool of light, additive): `colour` at its middle fading to nothing.
function groundPatch(width, depth, colour) {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.45, 'rgba(255,255,255,0.5)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 128);
  const patch = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), new THREE.MeshBasicMaterial({
    map: canvasTexture(canvas), color: colour, transparent: true, opacity: 0, depthWrite: false, fog: false, blending: THREE.AdditiveBlending,
    polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  patch.rotation.x = -Math.PI / 2;
  patch.material.name = 'bank light pool';
  return patch;
}

// ------------------------------------------------------------------------------------------ a picture the set may have

// Looks in the Works' export for a picture of a view in a state that the set helper may not have made yet (round 6: W3
// with No. 1 at work, for page 5's "made"): a file named in works-shot.json (anywhere in it, by name, such as
// "works-w3-working-state.png") that matches `pattern` and is really in the folder. A state picture (…-state.png) comes
// first; failing that, the helper plate it is made from (…-plate.jpg; until the paintings come, a plate and its state
// picture differ only where the state differs). Returns the file's name, or null (the page then keeps its main
// picture). Use before buildWorks, to put the picture in the page's PICTURES.
export async function findPicture(folder, pattern) {
  const facts = await fetch(`${folder}/works-shot.json`).then((r) => r.json()).catch(() => null);
  if (!facts) return null;
  const names = new Set();
  const gather = (value) => {
    if (typeof value === 'string') { if (pattern.test(value)) names.add(value); return; }
    if (Array.isArray(value)) { value.forEach(gather); return; }
    if (value && typeof value === 'object') for (const [key, inner] of Object.entries(value)) { if (pattern.test(key)) names.add(key); gather(inner); }
  };
  gather(facts);
  const files = [...names].map((name) => (/\.(png|jpg)$/.test(name) ? name : `${name}.jpg`));
  const order = (file) => (file.endsWith('-state.png') ? 0 : file.endsWith('-plate.jpg') ? 1 : 2);
  for (const file of [...new Set(files)].sort((a, b) => order(a) - order(b))) {
    const found = await fetch(`${folder}/${file}`, { method: 'HEAD' }).then((r) => r.ok).catch(() => false);
    if (found) return file;
  }
  return null;
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
//   no2Men        No. 2's eight waiting men (works-no-2-men.glb), for the slowed state: 'painted' (part of the set,
//                 wearing a painting that shows them, W2 page 12; shown by the state's men2), 'silhouettes' (dark own
//                 surfaces outside the projection, the W4 painting has none, page 14) or null (not loaded)
export async function buildWorks(kit, { folder = WORKS_FOLDER, views, pictures, behind = null, hideInBehind = 'men', no2Men = null }) {
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
  const [setParts, signs, gates, popUp, menAtNo2, projectors, textures] = await Promise.all([
    Promise.all(setFiles.map((file) => loadModel(url(file)))), optional('works-signs.glb'), optional('works-gates.glb'), optional('works-pop-up.glb'),
    no2Men ? optional('works-no-2-men.glb') : null,
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
  // No. 2's men, painted: part of the set (hidden until the state shows them, as No. 1's men are hidden when they go in)
  if (menAtNo2 && no2Men === 'painted') { menAtNo2.visible = false; everything.add(menAtNo2); }
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
  // the bank's hanging sign: its board gets its own copy of the board paint, so board and lettering can be dimmed
  // together (both own surfaces, the board with the lettering's tint)
  const bankSign = named(BANK_SIGN.board);
  let ownBoard = null;
  bankSign?.traverse((o) => {
    if (!o.isMesh) return;
    const swap = (m) => {
      if (m.name !== BANK_SIGN.boardPaint) return m;
      if (!ownBoard) { ownBoard = m.clone(); ownBoard.name = BANK_SIGN.ownBoardPaint; }
      return ownBoard;
    };
    o.material = Array.isArray(o.material) ? o.material.map(swap) : swap(o.material);
  });

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
    ownSurface: [...LETTERING, ...bankGlassNames, ...(ownBoard ? [[BANK_SIGN.ownBoardPaint, BANK_SIGN.lettering]] : [])],
    behind: behind ? { painting: picture(behind), hide: hidden } : null,
    stretch: [2.0, 4.0],
  });
  // the drums' stencils as projected (their colours, kept to scale from; DRUM_LETTERS): darkened by view in showView
  const drumLetters = new Map();
  everything.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of [o.material].flat()) {
      if (DRUM_LETTERS.materials.includes(m.name) && !drumLetters.has(m)) drumLetters.set(m, { colour: m.color?.clone() ?? null, emissive: m.emissive?.clone() ?? null });
    }
  });
  const dimDrumLetters = (view) => {
    const share = DRUM_LETTERS.dim[view] ?? 1;
    for (const [m, base] of drumLetters) {
      if (base.colour) m.color.copy(base.colour).multiplyScalar(share);
      if (base.emissive) m.emissive.copy(base.emissive).multiplyScalar(share);
    }
  };
  dimDrumLetters(firstView);

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
  // No. 2's men as silhouettes (W4): outside the projection, like the gates (the W4 painting has no men, so the yard
  // and lane behind them stay painted); the patch at each man's feet becomes a soft contact shadow (exported as a flat
  // disc of even darkness, it showed as a hard dark ring round each man's boots: round 4 of log 34)
  if (menAtNo2 && no2Men === 'silhouettes') {
    const dark = silhouetteMaterial();
    const softShadow = new THREE.MeshBasicMaterial({ map: softShadowPicture(), color: 0xffffff, transparent: true, opacity: 0.75, depthWrite: false, fog: false,
      polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 });
    menAtNo2.traverse((o) => {
      if (!o.isMesh) return;
      if (o.name.includes('foot-shadow') || [o.material].flat().some((m) => m.name.includes('foot-shadow'))) {
        o.geometry = acrossItsSpan(o.geometry);
        o.material = softShadow;
      } else {
        o.material = dark;
      }
      o.castShadow = false; o.receiveShadow = false;
    });
    menAtNo2.visible = false;
    kit.scene.add(menAtNo2);
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
  const brazierSmoke = new BrazierSmoke(kit.scene, { count: 14, life: 3.6, seed: SEEDS.brazierSmoke, colour: [150, 146, 140] });
  for (const puff of brazierSmoke.puffs) puff.sprite.material.color.setRGB(0.5, 0.48, 0.46);
  const lanternGlow = lanternAt ? glow(0xffb060, 0.34, 0.5) : null;
  if (lanternGlow) { lanternGlow.position.copy(lanternAt); kit.scene.add(lanternGlow); }
  const gateLampGlows = Object.fromEntries(Object.entries(facts.gate_lamps ?? {}).map(([prefix, at]) => {
    const lamp = glow(0xffc888, 0.9, 0.42);
    lamp.position.copy(fromBlender(at));
    kit.scene.add(lamp);
    return [prefix, lamp];
  }));
  // the people at work in each doorway (painted in the plates), kept dark in the burst's brightening as the first view
  // showing their factory's gate sees them (W2 for No. 2: page 4's burst)
  const keepDark = (prefix) => {
    const view = views.find((v) => v === (prefix === 'no-1' ? 'w1' : 'w2')) ?? firstView;
    return { camera: projectorOf[view].position.clone(), people: (facts.workers?.[prefix] ?? []).map((w) => ({ feet: fromBlender(w.feet), height: w.figure?.includes('stooped') ? 1.55 : 1.8 })) };
  };
  const flicker = { 'no-1': new WindowFlicker(kit.scene, set, 'no-1', SEEDS['no-1-windows'], litPictures, keepDark('no-1')),
    'no-2': new WindowFlicker(kit.scene, set, 'no-2', SEEDS['no-2-windows'], litPictures, keepDark('no-2')) };
  // sparks at No. 2's lathe during the burst on "busy": where works-shot.json's machines name the lathe ("no-2-lathe"),
  // or on the lathe's bed by the hands of No. 2's man bent over it (the stooped figure among its people at work): 0.7 m
  // up the room from his feet, 0.25 m to his right as the lane sees him, at the bed's height, kept low (drawn round his
  // head, the sparks read as a face)
  const latheAt = (() => {
    if (facts.machines?.['no-2-lathe']) return fromBlender(facts.machines['no-2-lathe']);
    const man = (facts.workers?.['no-2'] ?? []).find((w) => w.figure?.includes('stooped'));
    return man ? fromBlender([man.feet[0] + 0.25, man.feet[1] + 0.7, (man.feet[2] ?? 0) + 0.95]) : null;
  })();
  const latheSparks = latheAt ? new Sparks(kit.scene, latheAt, { count: BUSY.sparks, seed: SEEDS.latheSparks }) : null;
  if (latheSparks) { latheSparks.material.size = BUSY.sparkSize; latheSparks.points.visible = false; }
  effectsDone();

  // the bank's window (page 9): its glass glows when lit, its sign brightens, and a soft pool of light lies on the
  // pavement in front of it; a set change (part of the still key)
  const bankGlass = [];
  set.traverse((o) => { if (o.isMesh && [o.material].flat().some((m) => m.name.startsWith(BANK_WINDOW))) bankGlass.push(o); });
  // the sign's own surfaces as projected (their colours, kept to scale from)
  const bankSignMaterials = new Map();
  bankSign?.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of [o.material].flat()) {
      if ((m.name === BANK_SIGN.lettering || m.name === BANK_SIGN.ownBoardPaint) && !bankSignMaterials.has(m)) {
        bankSignMaterials.set(m, { colour: m.color?.clone() ?? null, emissive: m.emissive?.clone() ?? null });
      }
    }
  });
  let bankPool = null;
  const bankWindow = facts.bank?.window;
  if (bankWindow) {
    const centre = fromBlender(bankWindow.centre);
    const frontX = facts.bank.front_x ?? bankWindow.centre[0];
    // on the pavement, out from the bank's front (the lane is on the bank's +x side)
    const x = frontX + BANK_POOL.out, z = centre.z;
    bankPool = groundPatch(BANK_POOL.width, BANK_POOL.depth, 0xffb46a);
    bankPool.rotation.z = Math.PI / 2;   // long along the bank's front
    bankPool.position.set(x, groundUnder(set, x, z, []) + 0.015, z);
    bankPool.visible = false;
    kit.scene.add(bankPool);
  }

  // -------------------------------------------------------------------------------- applying a moment's state
  const now = { view: firstView, painting: firstView, behind, blendTo: null, blend: 0, men: true, bank: null, men2: false };
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
      dimDrumLetters(view);
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
  // amount: 0 dark (the sign dim), 1 lit (the sign at its full, lamp-lit brightness); give it in steps (steppedBlend)
  const showBank = (amount) => {
    if (amount === now.bank) return;
    for (const mesh of bankGlass) {
      for (const m of [mesh.material].flat()) {
        if (!m.name.startsWith(BANK_WINDOW)) continue;
        m.emissive?.setRGB(1.0 * amount, 0.62 * amount, 0.3 * amount);
        m.emissiveIntensity = 1 + 0.4 * amount;
      }
    }
    const signShare = BANK_SIGN.dim + (1 - BANK_SIGN.dim) * amount;
    for (const [m, base] of bankSignMaterials) {
      if (base.colour) m.color.copy(base.colour).multiplyScalar(signShare);
      if (base.emissive) m.emissive.copy(base.emissive).multiplyScalar(signShare);
    }
    if (bankPool) { bankPool.visible = amount > 0; bankPool.material.opacity = BANK_POOL.strength * amount; }
    now.bank = amount;
  };
  // No. 2's eight men (no2Men): painted ones are part of the set (the distance map is drawn again with or without them)
  const showMen2 = (shown) => {
    if (!menAtNo2 || shown === now.men2) return;
    menAtNo2.visible = shown;
    now.men2 = shown;
    if (no2Men === 'painted') projection.refresh();
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
  //              the windows flicker brighter), busyAt (seconds: the word "busy"; for BUSY.length seconds the doorway
  //              and the stone round the windows brighten in warm pulses, the panes flicker brighter and sparks fly at
  //              the lathe), litSteps ([1, 2, 3]: which
  //              windows flicker), smoke (a SMOKE kind in place of the state's own: No. 1's working smoke on page 5's
  //              "made" while it still shows quiet), smokeFrom (seconds: smoke starts here and builds up from the
  //              chimney's mouth), crates (no1 only: the moment the crates pop up), was: { state, until, fade } (a
  //              change of state on a word, at `until`: the earlier state's smoke drifts away and its extra lit
  //              windows fade out over `fade` seconds, 1.5 by default, instead of jumping) }
  //   bank: the bank's window lit (true, or how far lit 0 to 1, in steps), its sign brightening with it; until then the
  //         sign is dim
  //   men2: No. 2's eight men shown (needs no2Men; painted ones only where the painting shows them)
  //   fire: how high the brazier burns (1, the default, as when the men stood round it; FIRE_AFTER_A_WHILE after a time
  //         cut, so the cut reads as time passing); a set change (its light reaches the own surfaces)
  //   lampGlow: { 'no-1': share, 'no-2': share } of each gate lamp's glow (1 by default; W1 keeps No. 1's lamp low so the
  //         gate, not the lamp, is the brightest thing)
  function setWorks(t, state) {
    showView(state.view, state.painting ?? state.view, state.behind ?? null);
    showBlend(state.blendTo ?? null, state.blend ?? 0);
    showMen(state.men ?? true);
    showBank(typeof state.bank === 'number' ? clamp01(state.bank) : state.bank ? 1 : 0);
    showMen2(!!state.men2);
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
      // smoke (each chimney's kind in a state; on a change, the earlier state's puffs drift away)
      const kindAt = (kind, name) => {
        const smoking = kind === 'thin' ? THIN_CHIMNEYS[prefix] : kind === 'none' ? [] : CHIMNEYS[prefix];
        return smoking.includes(name) ? kind : 'none';
      };
      const was = given.was && t >= given.was.until ? { settings: STATES[prefix][given.was.state], until: given.was.until, fade: given.was.fade ?? 1.5 } : null;
      for (const name of CHIMNEYS[prefix]) {
        smokes[name]?.set(t, { kind: kindAt(given.smoke ?? settings.smoke, name), from: given.smokeFrom ?? -Infinity,
          earlier: was ? { kind: kindAt(was.settings.smoke, name), until: was.until } : null });
      }
      // window flicker: the lit steps (a third lit = step 1), brighter when busy
      const stepsOf = (stateSettings) => (stateSettings.windows >= 1 ? [1, 2, 3] : stateSettings.windows > 0 ? [1] : []);
      const litSteps = given.litSteps ?? stepsOf(settings);
      const amount = settings.flicker + (settings.busy ? (settings.busy - settings.flicker) * clamp01(given.busy ?? 0) : 0);
      const fading = was ? { steps: stepsOf(was.settings).filter((step) => !litSteps.includes(step)), amount: was.settings.flicker * (1 - clamp01((t - was.until) / was.fade)) } : null;
      const burst = given.busyAt !== undefined ? { at: given.busyAt } : null;
      const pulse = flicker[prefix].set(t, { amount, steps: litSteps, fading, burst });
      if (prefix === 'no-2' && latheSparks) {
        latheSparks.points.visible = pulse > 0;
        if (pulse > 0) {
          latheSparks.set(t);
          // kept low over the bed (the shared sparks fly up to 0.75 m)
          const places = latheSparks.geometry.attributes.position.array;
          for (let i = 1; i < places.length; i += 3) places[i] = latheAt.y + (places[i] - latheAt.y) * BUSY.sparkRise;
        }
      }
    }
    keys.push(`crates:${showCrates(t, state.no1?.crates)}`);
    // the fire (lower after a time cut), the lantern and the gate lamps (always lit at No. 1; the gate lamps on both piers)
    const fire = clamp01(state.fire ?? 1);
    fireLight.intensity = 3.2 * (0.45 + 0.55 * fire);
    keys.push(`fire:${fire.toFixed(2)}`);
    const fireFlicker = 0.75 + 0.15 * Math.sin(t * 17.3) + 0.1 * Math.sin(t * 29.1 + 1.3);
    fireGlow.material.opacity = 0.38 * fireFlicker * (0.2 + 0.8 * fire);
    fireGlow.scale.setScalar((1.35 + 0.02 * Math.sin(t * 11.7)) * (0.55 + 0.45 * fire));
    flames.set(t);
    // lower flames: shorter and a little narrower tongues on the same coals
    const tall = 0.3 + 0.7 * fire, wide = 0.75 + 0.25 * fire;
    if (fire < 1) {
      for (const f of flames.tongues) {
        f.body.scale.set(f.body.scale.x * wide, f.body.scale.y * tall, 1);
        f.core.scale.set(f.core.scale.x * wide, f.core.scale.y * tall, 1);
      }
    }
    sparks.set(t);
    if (fire < 1) {
      // fewer sparks: the later ones put out
      const colours = sparks.geometry.attributes.color.array, alive = Math.round(sparks.sparks.length * fire);
      colours.fill(0, alive * 3);
      sparks.geometry.attributes.color.needsUpdate = true;
    }
    brazierSmoke.set({ t, origin: brazierTop.clone().add(new THREE.Vector3(0, 0.35 * tall, 0)).toArray(), scale: 0.75, drift: 0.9 });
    if (lanternGlow) lanternGlow.material.opacity = 0.5 * (0.9 + 0.06 * Math.sin(t * 9.1) + 0.04 * Math.sin(t * 23.7 + 0.6));
    for (const [prefix, lamp] of Object.entries(gateLampGlows)) {
      const seed = prefix === 'no-1' ? 0 : 2.1;
      lamp.material.opacity = 0.42 * (state.lampGlow?.[prefix] ?? 1) * (0.95 + 0.03 * Math.sin(t * 4.3 + seed) + 0.02 * Math.sin(t * 13.1 + seed));
    }
    return [now.view, now.painting, now.behind ?? '-', now.blendTo ? `${now.blendTo}@${now.blend.toFixed(3)}` : '-', now.men ? 'men' : 'no men',
      now.men2 ? 'no. 2 men' : 'no no. 2 men', now.bank > 0 ? `bank lit ${now.bank.toFixed(3)}` : 'bank dark', ...keys].join('|');
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
  // a point given in works-shot.json (Blender), raised by `lift` metres, or null when the export has none
  const fact = (point, lift = 0) => (point ? fromBlender(point).add(new THREE.Vector3(0, lift, 0)) : null);
  // No. 1's waiting men standing at the gate (the stooped man at the brazier left out)
  const waitingMen = () => (facts.men_at_no_1 ?? []).filter((m) => !m.figure?.includes('stooped')).map((m) => named(m.name)).filter(Boolean);
  const spots = {
    'no-1-queue': () => boxCentre(men.slice(2, 5), 0.85),
    // the right-hand man of No. 1's waiting men, at his head: a label's line leaves the crowd sideways from here
    // (round 5 of log 34: drawn from the middle of the queue, WORKERS' line ran down over the men)
    'no-1-crowd-side': () => {
      const crowd = waitingMen();
      if (!crowd.length) return spots['no-1-queue']();
      const right = (man) => new THREE.Box3().setFromObject(man).max.x;
      return boxCentre([crowd.reduce((a, b) => (right(a) >= right(b) ? a : b))], 0.93);
    },
    // the chain between No. 1's gate leaves (the NEW MONEY SPENT arrow ends here; round 4 of log 34 ended it on a drum's lantern)
    'no-1-chain': () => fact(facts.gates?.['no-1']?.chain) ?? spots['no-1-gateway'](),
    // the machines in each factory's lit doorway (works-shot.json "machines", from round 5): No. 2's flywheel is the
    // machine W3 shows (MACHINES points at it); without them, the lit sheds as before
    'no-2-flywheel': () => fact(facts.machines?.['no-2-flywheel']) ?? spots['no-2-sheds'](),
    'no-1-looms': () => fact(facts.machines?.['no-1-looms']) ?? spots['no-1-sheds'](),
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
    // the brazier's fire, at the top of its flames (labels keep their lines clear of it)
    brazier: () => coals.clone().add(new THREE.Vector3(0, 0.45, 0)),
    // over each gate, on the gable above it (about 5.6 m up the works' front): where a gate view's tag stands
    'no-1-gate-top': () => (facts.gates?.['no-1'] ? fromBlender([facts.gates['no-1'].centre[0], facts.gates['no-1'].centre[1], TAG_HEIGHT]) : null),
    'no-2-gate-top': () => (facts.gates?.['no-2'] ? fromBlender([facts.gates['no-2'].centre[0], facts.gates['no-2'].centre[1], TAG_HEIGHT]) : null),
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
  // where a thing (an object by name, such as the gate boards 'gate-board-no-1' and 'gate-board-no-2') is on the frame
  // now: the box round its outline's corners { left, top, right, bottom } in pixels, or null (for checks that words and
  // arrows keep clear of it; round 6 of log 34)
  const screenBox = (name) => {
    const thing = named(name) ?? gates?.getObjectByName(name);
    if (!thing) return null;
    const box = new THREE.Box3().setFromObject(thing);
    if (box.isEmpty()) return null;
    const xs = [], ys = [];
    for (let k = 0; k < 8; k++) {
      const p = kit.toScreen(new THREE.Vector3(k & 1 ? box.max.x : box.min.x, k & 2 ? box.max.y : box.min.y, k & 4 ? box.max.z : box.min.z));
      if (p.behind) return null;
      xs.push(p.x); ys.push(p.y);
    }
    return { left: Math.min(...xs), top: Math.min(...ys), right: Math.max(...xs), bottom: Math.max(...ys) };
  };

  // the name tags (TAGS), drawn the same way on every page (call from draw2D). In W3: each on its own factory's
  // chimneys, QUIET on No. 1's round one and FLAT OUT between No. 2's two square ones, low on the shafts (y, the tags'
  // bottom), below the rule cards and the ends of their lines (page 5). (Placed in the sky to the left of each
  // factory's chimneys, as first drawn, QUIET stood over the far town's gasholder and FLAT OUT between the two
  // factories.) In W2 (and W1): the factory's own tag on the gable over its gate, its tick pointing down at the gate,
  // under the top band's words (about 0.20 to 0.23 down in W2's composed frame). Placed first just under the gate's
  // middle, it sat on the No. 2 board and the gate's arch, and THE FLAT-OUT FACTORY SLOWS covered the top of the lit
  // gateway (round 4 of log 34). The longest tag keeps its right edge left of 0.90 across (nameTag).
  // slowsAt: from this moment No. 2's tag reads THE FLAT-OUT FACTORY SLOWS (the old words fade out as the new come in).
  // quietUntil: QUIET fades out here (page 5: on "made", when No. 1 goes to work; round 6 of log 34).
  const drawTags = (ctx, t, { at, until = Infinity, view = 'w3', slowsAt = Infinity, quietUntil = Infinity, y = 700 }) => {
    let no1Place = null, no2Place = null;
    if (view === 'w3') {
      const no1 = screen('no-1-chimney'), a = screen('no-2-chimney-a'), b = screen('no-2-chimney-b');
      if (no1) no1Place = { x: no1.x, y };
      if (a) no2Place = { x: b ? (a.x + b.x) / 2 : a.x, y };
    } else {
      const top = screen(view === 'w1' ? 'no-1-gate-top' : 'no-2-gate-top');
      const place = top && !top.behind ? { x: top.x, y: Math.max(330, top.y) } : null;
      if (view === 'w1') no1Place = place; else no2Place = place;
    }
    if (no1Place) nameTag(ctx, t, { at, until: Math.min(until, quietUntil), text: TAGS.quiet, ...no1Place });
    if (no2Place) {
      nameTag(ctx, t, { at: at + (view === 'w3' ? 0.15 : 0), until: Math.min(until, slowsAt), text: TAGS.flatOut, ...no2Place });
      if (slowsAt < until) nameTag(ctx, t, { at: slowsAt, until, text: TAGS.slows, ...no2Place });
    }
  };

  return { set: setWorks, cameraAt, screen, screenBox, spotAt, drawTags, facts, projection, men, menAtNo2, gate, crates, smokes, views: projectorOf };
}
