// What this does: the stage side of the wet street test (plain words). It is a small page script in a COPY of the film kit's stage files. It can:
//   describe(glb)            load a .glb with three.js's own loader and list, for every material, which maps and extensions arrived (roughness map, clear coat, clear coat roughness,
//                            specular strength map, colour, normal) and the plain numbers.
//   still({glb, variant})    draw the street from the film's main camera with the .glb's own materials (no painting) in a dusk setting: warm lamp lights, a cool sky light, and an
//                            "environment" (what shiny surfaces reflect) made of a dusk sky gradient with bright lamp and window patches. variant switches the maps of the
//                            baked surfaces on one at a time: 'no_maps' (colour and normal only: roughness 0.8, no coat, normal shine), 'roughness' (+ the roughness map),
//                            'coat' (+ the clear coat maps), 'full' (+ the specularity map = everything the .glb carries).
//   projected({glb, painting, matte, view})  draw the street through the film's real projection code (projected-set.js projectPaintingOnto), the same way the lockout test does,
//                            with a stand-in painting (the wet picture Blender drew), matte true (what the film does today) or false. view: 'projector' (the plate's own camera),
//                            'moved' (1.4 m forward, a little right and up, the lockout clip's move), 'weights' (moved; orange = wears the painting, blue = wears the .glb's own surface).
import { THREE, renderer, loadTexture } from '../stage/cinema-stage.js';
import { GLTFLoader } from '/paper-film/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from '/paper-film/node_modules/three/examples/jsm/environments/RoomEnvironment.js';
import { loadModel } from './model-loader.js';
import { projectorCamera, projectPaintingOnto } from './projected-set.js';

const SET = '/assets/models/pit-village';
const MAIN = { position: [0, 1.88978, -3.0], quaternion: [0.056693, 0, 0, 0.998392], fov: 40, aspect: 0.5625, near: 0.1, far: 400 };
const LAMPS = [[3.03, 11.0, 3.98], [-3.03, 25.0, 4.96], [3.03, 39.0, 5.94], [-3.03, 53.0, 6.92], [3.03, 64.5, 7.72]];   // Blender x, y, z of the five gas lamps
const loader = new GLTFLoader();
const cameraFrom = (settings) => projectorCamera(settings);

// ------------------------------------------------------------------------------------------------ a dusk to reflect (a stand-in for the Blender world and lights)
function duskEnvironment() {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(new THREE.SphereGeometry(90, 48, 24), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vDir; void main() { vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vDir; void main() {
      float h = clamp(vDir.y, 0.0, 1.0);
      vec3 horizon = vec3(0.95, 0.52, 0.30) * 0.55, zenith = vec3(0.05, 0.09, 0.17);
      vec3 colour = mix(horizon, zenith, pow(h, 0.45));
      if (vDir.y < 0.0) colour = vec3(0.03, 0.03, 0.035);
      gl_FragColor = vec4(colour, 1.0); }`,
  }));
  scene.add(sky);
  const patch = (x, y, z, width, height, rgb) => {     // a bright patch: a lamp or a lit window, seen from the street (directions are what count)
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, height), new THREE.MeshBasicMaterial({ color: new THREE.Color(...rgb), side: THREE.DoubleSide }));
    mesh.position.set(x, y, z); mesh.lookAt(0, 1.9, 0); scene.add(mesh);
  };
  for (const [x, y, z] of LAMPS) patch(x * 3, z * 3, -y * 3 * 0.9, 6, 6, [14, 9, 4]);                      // the five lamps, pushed out so they surround the street
  for (let k = 0; k < 14; k++) patch((k % 2 ? 1 : -1) * 12, 6 + (k % 3) * 4, -10 - k * 5.5, 3, 4.2, [7, 4.4, 2]);   // lit windows both sides
  patch(0, 14, -85, 60, 22, [1.6, 0.9, 0.5]);                                                             // the afterglow over the colliery
  const generator = new THREE.PMREMGenerator(renderer);
  const texture = generator.fromScene(scene, 0.02).texture;
  generator.dispose();
  return texture;
}

function lighting(scene, environment) {
  scene.add(new THREE.HemisphereLight(0x50637e, 0x1c1712, 0.55));
  const key = new THREE.DirectionalLight(0xffc48a, 0.5);
  key.position.set(1, 2.4, -10.4); key.target.position.set(0, 0, -14); scene.add(key, key.target);
  for (const [x, y, z] of LAMPS) {
    const lamp = new THREE.PointLight(0xffa860, 55, 24, 2);
    lamp.position.set(x, z, -y); scene.add(lamp);
  }
  scene.environment = environment;
  scene.background = new THREE.Color(0x0e141c);
}

const loadScene = async (glb) => {
  const gltf = await loader.loadAsync(`${SET}/${glb}`);
  return gltf.scene;
};

// every material of a loaded set, once each
const materialsOf = (root) => {
  const found = new Map();
  root.traverse((o) => { if (o.isMesh) for (const m of [o.material].flat()) found.set(m.uuid, m); });
  return [...found.values()];
};

function describeMaterial(m) {
  const picture = (t) => (t ? { width: t.image?.width ?? null, height: t.image?.height ?? null, channel: t.channel } : null);
  return {
    name: m.name, kind: m.type, roughness: m.roughness, metalness: m.metalness, colour: m.color ? m.color.getHexString() : null,
    roughnessMap: picture(m.roughnessMap), normalMap: picture(m.normalMap), map: picture(m.map),
    clearcoat: m.clearcoat ?? null, clearcoatMap: picture(m.clearcoatMap), clearcoatRoughness: m.clearcoatRoughness ?? null, clearcoatRoughnessMap: picture(m.clearcoatRoughnessMap),
    specularIntensity: m.specularIntensity ?? null, specularIntensityMap: picture(m.specularIntensityMap), specularColor: m.specularColor ? m.specularColor.toArray() : null,
    ior: m.ior ?? null,
  };
}

// which maps of the baked surfaces are switched on
function setVariant(root, variant) {
  const level = { no_maps: 0, roughness: 1, coat: 2, full: 3 }[variant] ?? 3;
  for (const m of materialsOf(root)) {
    if (!m.roughnessMap) continue;      // only the baked surfaces carry maps; every other material keeps its flat numbers
    m.userData.saved ??= { roughnessMap: m.roughnessMap, roughness: m.roughness, clearcoat: m.clearcoat, clearcoatMap: m.clearcoatMap, clearcoatRoughnessMap: m.clearcoatRoughnessMap,
      clearcoatRoughness: m.clearcoatRoughness, specularIntensityMap: m.specularIntensityMap, specularIntensity: m.specularIntensity, specularColor: m.specularColor?.clone() };
    const s = m.userData.saved;
    if (level >= 1) { m.roughnessMap = s.roughnessMap; m.roughness = s.roughness; } else { m.roughnessMap = null; m.roughness = 0.8; }
    if (level >= 2) { m.clearcoat = s.clearcoat; m.clearcoatMap = s.clearcoatMap; m.clearcoatRoughness = s.clearcoatRoughness; m.clearcoatRoughnessMap = s.clearcoatRoughnessMap; }
    else { m.clearcoat = 0; m.clearcoatMap = null; m.clearcoatRoughnessMap = null; }
    if (level >= 3) { m.specularIntensityMap = s.specularIntensityMap; m.specularIntensity = s.specularIntensity; m.specularColor?.copy(s.specularColor); }
    else { m.specularIntensityMap = null; m.specularIntensity = 1; m.specularColor?.setRGB(1, 1, 1); }
    m.needsUpdate = true;
  }
}

const bytesOf = (size) => { renderer.setSize(size[0], size[1], false); };
const grab = () => renderer.domElement.toDataURL('image/png');

export async function setup() {
  const environment = duskEnvironment();
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  return {
    async describe(glb) {
      const root = await loadScene(glb);
      const materials = materialsOf(root).map(describeMaterial);
      const meshes = []; root.traverse((o) => { if (o.isMesh) meshes.push(o); });
      const uv1 = meshes.filter((o) => o.geometry.attributes.uv1).length;
      const engine = meshes.filter((o) => /engine_house/.test(o.name) || /engine_house/.test(o.parent?.name ?? '')).map((o) => [o.name, [o.material].flat().map((m) => m.name)]);
      return { glb, materials, meshes: meshes.length, meshesWithSecondTextureCoordinates: uv1, engine };
    },
    async still({ glb, variant = 'full', size = [540, 960], camera = MAIN, envIntensity = 1.0 }) {
      const root = await loadScene(glb);
      const scene = new THREE.Scene();
      lighting(scene, environment);
      scene.add(root);
      const dome = root.getObjectByName('sky_dome'); if (dome) dome.visible = false;
      scene.environmentIntensity = envIntensity;
      setVariant(root, variant);
      bytesOf(size);
      renderer.setRenderTarget(null);
      renderer.render(scene, cameraFrom({ ...camera, aspect: size[0] / size[1] }));
      const url = grab();
      scene.traverse((o) => { o.geometry?.dispose?.(); });
      return url;
    },
    async projected({ glb, painting, matte = true, view = 'projector', size = [540, 960] }) {
      const scene = new THREE.Scene();
      const room = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;   // the film stage's own reflections: a grey room
      scene.environment = room;
      scene.add(new THREE.HemisphereLight(0x50637e, 0x1c1712, 0.55));
      const key = new THREE.DirectionalLight(0xffc48a, 0.5); key.position.set(1, 2.4, -10.4); key.target.position.set(0, 0, -14); scene.add(key, key.target);
      for (const [x, y, z] of LAMPS) { const lamp = new THREE.PointLight(0xffa860, 25, 20, 2); lamp.position.set(x, z, -y); scene.add(lamp); }
      scene.background = new THREE.Color(0x0e141c);
      const kit = { scene };
      const set = await loadModel(`${SET}/${glb}`, { reflections: 0.3 });
      scene.add(set); set.updateMatrixWorld(true);
      const dome = set.getObjectByName('sky_dome'); if (dome) dome.visible = false;
      const projector = cameraFrom(MAIN);
      const projection = projectPaintingOnto(kit, set, await loadTexture(`${SET}/${painting}`), projector, { matte });
      if (view === 'weights') projection.showWeights(true);
      const camera = cameraFrom({ ...MAIN, aspect: size[0] / size[1] });
      if (view !== 'projector') {      // the lockout clip's move: 1.4 m forward, 0.3 m right, a little up
        camera.position.add(new THREE.Vector3(0.3, 0.05, -1.4)); camera.updateMatrixWorld(true);
      }
      bytesOf(size);
      renderer.setRenderTarget(null);
      renderer.toneMapping = THREE.NoToneMapping;      // the painting must come out as painted: no film look on top
      renderer.outputColorSpace = THREE.LinearSRGBColorSpace;   // as in the film: the painting is written after the colour encoding step, so the stage writes plain linear light and its finishing pass encodes it (the runner's picture is encoded afterwards, in Python)
      renderer.render(scene, camera);
      const url = grab();
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      return url;
    },
  };
}
