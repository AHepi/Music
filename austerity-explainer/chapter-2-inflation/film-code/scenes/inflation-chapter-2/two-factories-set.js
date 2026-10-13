// What this does: builds the "two factories" set used on pages 3 and 8 of chapter 2: two detailed
// model munitions works made in Blender (paper-film/blender/build_factory.py: brick, arched lit
// windows, sawtooth roofs with glazed north lights, chimneys, offices, water tanks, cobbled
// forecourts) standing in a model industrial town (blender/build_town.py: terraced streets with lit
// windows, far works and chimneys, a gasholder, a railway viaduct, gas lamps, a low wall and crates
// near the camera), in front of a painted dusk skyline, lit by one warm lamp from the front left and
// the works' own lamps. The left works (A) starts idle; the right one (B) runs flat out. Each has a
// flip counter on a post showing its price, a yard where coins land, and a place where its shells
// stand.
//
// Round 20: the viewer said the old card boxes on a bare table were "a sudden drop in visual
// quality... the model needs to be significantly higher quality" and asked to "fill the frame".
//
// Positions (world units): the ground is y = 0; works A stands at x = -1.4, z = +2.2, works B at
// x = +1.6, z = -4.2, fronts facing the camera (+z). A street runs across between them at z = -0.25.

import { THREE } from '../cinema-kit.js';
import { paper, PAPER, splitFlap, shell } from '../models.js';
import { Smoke, Motes } from '../effects.js';
import { loadModel, modelFactory, markerAt } from '../model-loader.js';

export const FACTORY_A = new THREE.Vector3(-1.4, 0, 2.2);
export const FACTORY_B = new THREE.Vector3(1.6, 0, -4.2);
const MODELS = '/assets/models/inflation-chapter-2';

export async function buildTwoFactories(kit, { shellsA = 6, shellsB = 8 } = {}) {
  kit.lightRig({ keyColour: 0xffc98a, keyShare: 0.8, keyFrom: [-12, 6.5, 7], keyTarget: [0, 0, -1], fillSky: 0x6f8796, fillGround: 0x241e18,
    fillShare: 0.24, haze: 0x1a2228, hazeDensity: 0.022, shadowBox: 10, shadowSoftness: 6, background: 0x10161b, reflections: 0.3 });
  const backdrop = await kit.backdrop('402-bg-dusk-skyline', { distance: 52, fov: 40 });
  backdrop.position.set(0, 13, -52);
  backdrop.scale.setScalar(4.6);   // wide enough for the side-on close shots of each works
  // a soft band of dusk haze at the far edge of the town, so the ground melts into the painting
  const hazeCanvas = document.createElement('canvas'); hazeCanvas.width = 4; hazeCanvas.height = 256;
  const hazeInk = hazeCanvas.getContext('2d'), fall = hazeInk.createLinearGradient(0, 0, 0, 256);
  fall.addColorStop(0, 'rgba(44,36,27,0)'); fall.addColorStop(0.6, 'rgba(44,36,27,0.6)'); fall.addColorStop(1, 'rgba(44,36,27,1)');
  hazeInk.fillStyle = fall; hazeInk.fillRect(0, 0, 4, 256);
  const hazeTexture = new THREE.CanvasTexture(hazeCanvas); hazeTexture.colorSpace = THREE.SRGBColorSpace;
  const haze = new THREE.Mesh(new THREE.PlaneGeometry(140, 6), new THREE.MeshBasicMaterial({ map: hazeTexture, transparent: true, depthWrite: false, fog: false }));
  haze.position.set(0, 2.5, -37.6);
  kit.scene.add(haze);

  // the town (ground, streets, terraces, far works, gasholder, viaduct, lamps, near wall and crates)
  const town = await loadModel(`${MODELS}/town.glb`);
  kit.scene.add(town);
  const farSmoke = [];
  for (let k = 0; k < 6; k++) {
    const top = markerAt(town, `smoke-${k}`);
    if (top) farSmoke.push({ top, smoke: new Smoke(kit.scene, { count: 7, life: 4.2, seed: 60 + k }) });
  }

  const make = async (file, at, seed) => {
    const factory = await modelFactory(`${MODELS}/${file}`);
    factory.group.position.copy(at);
    kit.scene.add(factory.group);
    const smoke = new Smoke(kit.scene, { count: 12, life: 3.4, seed });
    const chimney = factory.chimneyTop.clone().add(at);
    // a warm pool of light from the lamp over the loading door
    if (factory.lampAt) {
      const doorLight = new THREE.PointLight(0xffb066, 1.6, 2.6, 2);
      doorLight.position.copy(factory.lampAt).add(at).add(new THREE.Vector3(0, -0.05, 0.12));
      kit.scene.add(doorLight);
      factory.doorLight = doorLight;
    }
    // a flip counter on a post to the right of the door, showing the price of a shell
    const board = splitFlap({ cells: 5, cellWidth: 0.13, gap: 0.018 });
    const boardAt = new THREE.Vector3(at.x + 1.25, 1.05, at.z + 1.55);
    board.group.position.copy(boardAt);
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.9, 10), paper(PAPER.charcoal));
    post.position.set(boardAt.x, 0.45, boardAt.z - 0.05);
    post.castShadow = true;
    kit.scene.add(board.group, post);
    const shells = [];
    for (let i = 0; i < 10; i++) {
      const s = shell({ height: 0.28 });
      s.group.position.set(at.x - 0.95 + i * 0.15, 0, at.z + 1.35);
      kit.scene.add(s.group);
      shells.push(s);
    }
    return { factory, smoke, chimney, board, boardAt, post, shells,
      shellAt: (i) => new THREE.Vector3(at.x - 0.95 + i * 0.15, 0, at.z + 1.35),   // close left of the door, so shells, door and board share a frame
      yard: new THREE.Vector3(at.x + 0.15, 0, at.z + 1.95), door: factory.doorAt.clone().add(at) };
  };
  const a = await make('factory-a.glb', FACTORY_A, 31), b = await make('factory-b.glb', FACTORY_B, 47);
  // works B must not look like works A (round 20 critique; pages 3 and 8 both): an oxblood door (B's own copies of the 'door-planks'
  // material, the plank texture turned grey and tinted) and heavier, darker, denser smoke
  const OXBLOOD = new THREE.Color(0x8a2a22);
  let oxbloodMap = null;
  b.factory.group.traverse((o) => {
    if (!o.isMesh || !o.material.name.startsWith('door-planks')) return;
    const m = o.material;
    if (m.map && m.map.image && !oxbloodMap) {
      const img = m.map.image, canvas = document.createElement('canvas');
      canvas.width = img.width; canvas.height = img.height;
      const ink = canvas.getContext('2d');
      ink.drawImage(img, 0, 0);
      const px = ink.getImageData(0, 0, canvas.width, canvas.height), d = px.data;
      for (let i = 0; i < d.length; i += 4) {
        const grey = 0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2];
        const v = Math.min(255, 70 + grey * 0.9);
        d[i] = d[i + 1] = d[i + 2] = v;
      }
      ink.putImageData(px, 0, 0);
      oxbloodMap = new THREE.CanvasTexture(canvas);
      for (const key of ['flipY', 'wrapS', 'wrapT', 'colorSpace', 'channel', 'magFilter', 'minFilter', 'anisotropy']) oxbloodMap[key] = m.map[key];
      oxbloodMap.repeat.copy(m.map.repeat); oxbloodMap.offset.copy(m.map.offset); oxbloodMap.rotation = m.map.rotation; oxbloodMap.center.copy(m.map.center);
      oxbloodMap.needsUpdate = true;
    }
    if (oxbloodMap) m.map = oxbloodMap;
    m.color.copy(OXBLOOD);
    m.needsUpdate = true;
  });

  const heavySmoke = new Smoke(kit.scene, { count: 30, life: 4.2, seed: 93, colour: [74, 70, 68] });
  // B's coal smoke: a thick, dark, slow column that stays over its chimney (rise squashed, puffs
  // more opaque than the kit's light wisps). Call from pose while the set shows.
  const heavySmokeB = (t) => {
    heavySmoke.set({ t: t + 7, origin: b.chimney.toArray(), scale: 1.3, wind: 0.45 });
    for (const puff of heavySmoke.puffs) {
      if (!puff.sprite.visible) continue;
      puff.sprite.position.y = b.chimney.y + 0.05 + (puff.sprite.position.y - b.chimney.y) * 0.5;
      puff.sprite.material.opacity = Math.min(0.85, puff.sprite.material.opacity * 1.8);
    }
  };
  const hideHeavySmokeB = () => heavySmoke.hide();
  const motes = new Motes(kit.scene, { count: 200, min: [-5, 0.2, -8], max: [5, 4, 5], size: 0.025, seed: 11, opacity: 0.55 });
  // loose things for the near foreground (blender/build_props.py): 'barrels', 'crates', 'lamp-post', 'cart'
  const props = await loadModel(`${MODELS}/props.glb`);
  const prop = (name, at, turn = 0) => {
    const copy = props.getObjectByName(name).clone(true);
    copy.position.set(...at); copy.rotation.y = turn;
    kit.scene.add(copy);
    return copy;
  };
  // the far chimneys smoke all the time (call from pose)
  const townSmoke = (t) => { for (const s of farSmoke) s.smoke.set({ t: t + 20, origin: s.top.toArray(), scale: 1.6 }); };
  const hideTownSmoke = () => { for (const s of farSmoke) s.smoke.hide(); };
  return { a, b, motes, shellsA, shellsB, town, townSmoke, hideTownSmoke, prop, heavySmokeB, hideHeavySmokeB };
}
