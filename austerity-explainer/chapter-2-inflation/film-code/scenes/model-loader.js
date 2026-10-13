// What this does: brings models made in Blender (.glb files, see paper-film/blender/) into a cinema
// page. Each model gets its own copy of its materials (so two factories can be lit differently), casts
// and catches shadows, keeps its baked corner shading (glTF "occlusion", used by three.js as the
// aoMap), and lets the page find named spots on it (empties called "markers" in Blender, such as
// chimney_top or door) and turn its lit parts (materials named "...-glow") up and down.
//
// Use in a page:
//   import { loadModel, modelFactory } from '../model-loader.js';
//   const works = await modelFactory('/assets/models/inflation-chapter-2/factory-a.glb');
//   works.group.position.set(-1.4, 0, 2.2); kit.scene.add(works.group);
//   works.setRunning(1);                       // windows, roof lights and the open door glow
//   const smokeFrom = works.chimneyTop.clone().add(works.group.position);

import { THREE } from './cinema-kit.js';
import { GLTFLoader } from '/paper-film/node_modules/three/examples/jsm/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const cache = new Map();

// Load a .glb and return a fresh copy of it, ready to add to a page's scene.
// matte: true swaps the realistic (Standard) materials for matte (Lambert) ones with the same
// pictures, bumps, baked shading and glow: about half the drawing time in the software renderer
// (chapter 2, page 3: the detailed works and town took 4 times as long as other pages to film),
// at the cost of the soft reflections on metal and glass. Use it for big or distant models.
// matteFill: matte materials get no soft light from the surroundings (the realistic ones do, and it
// lifts their shadowed sides), so each surface also glows faintly with its own colour by this
// much, standing in for that light.
export async function loadModel(url, { reflections = 0.3, shadows = true, matte = false, matteFill = 0.3 } = {}) {
  if (!cache.has(url)) cache.set(url, loader.loadAsync(url));
  const gltf = await cache.get(url);
  const root = gltf.scene.clone(true);
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.material = o.material.clone();
    if (matte && o.material.isMeshStandardMaterial) {
      const m = o.material;
      const lambert = new THREE.MeshLambertMaterial({
        map: m.map, color: m.color, emissive: m.emissive, emissiveMap: m.emissiveMap, emissiveIntensity: m.emissiveIntensity,
        aoMap: m.aoMap, aoMapIntensity: m.aoMapIntensity, normalMap: m.normalMap, normalScale: m.normalScale,
        transparent: m.transparent, opacity: m.opacity, side: m.side, alphaTest: m.alphaTest, vertexColors: m.vertexColors,
      });
      lambert.name = m.name;
      if (!/-glow$/.test(m.name) && matteFill > 0) {
        lambert.emissiveMap = m.map;
        lambert.emissive = m.color.clone().multiplyScalar(matteFill);
        lambert.emissiveIntensity = 1;
      }
      o.material = lambert;
    }
    const glowing = /-glow$/.test(o.material.name);
    o.castShadow = shadows && !glowing;
    o.receiveShadow = shadows;
    o.material.envMapIntensity = reflections;
    if (o.material.aoMap) o.material.aoMapIntensity = 1.0;
  });
  return root;
}

// Every material on a model whose name starts with `prefix` (e.g. 'window-glow').
export function materialsNamed(root, prefix) {
  const found = new Set();
  root.traverse((o) => { if (o.isMesh && o.material.name.startsWith(prefix)) found.add(o.material); });
  return [...found];
}

// Where a marker sits on the model, relative to the model's own origin.
export function markerAt(root, name) {
  const marker = root.getObjectByName(name);
  if (!marker) return null;
  root.updateMatrixWorld(true);
  const inverse = root.matrixWorld.clone().invert();
  return marker.getWorldPosition(new THREE.Vector3()).applyMatrix4(inverse);
}

// A works made by blender/build_factory.py, with the same handles the old card factory had
// (models.js paperFactory): group, chimneyTop, doorAt, width, depth, height, setRunning(level).
export async function modelFactory(url, options = {}) {
  const group = await loadModel(url, options);
  const glow = {
    windows: materialsNamed(group, 'window-glow'), roof: materialsNamed(group, 'roof-glow'),
    door: materialsNamed(group, 'door-glow'), office: materialsNamed(group, 'office-glow'), lamp: materialsNamed(group, 'lamp-glow'),
  };
  const setRunning = (level) => {
    for (const m of glow.windows) m.emissiveIntensity = 0.12 + 1.5 * level;
    for (const m of glow.roof) m.emissiveIntensity = 0.08 + 1.1 * level;
    for (const m of glow.door) m.emissiveIntensity = 0.2 + 1.3 * level;
    for (const m of glow.office) m.emissiveIntensity = 0.75;
    for (const m of glow.lamp) m.emissiveIntensity = 2.4;
  };
  setRunning(0);
  return {
    group, width: 3.2, depth: 2.0, height: 1.3, setRunning, glow,
    chimneyTop: markerAt(group, 'chimney_top') ?? new THREE.Vector3(1.15, 3.25, -1.3),
    doorAt: markerAt(group, 'door') ?? new THREE.Vector3(0, 0, 1.05),
    yardAt: markerAt(group, 'yard') ?? new THREE.Vector3(-0.1, 0, 2.1),
    lampAt: markerAt(group, 'door_lamp'),
  };
}
