// What this does: a test scene, not part of any film (log 22). The 1973 petrol station painting
// (chapter 2, page 7) as a painted room with depth, with the red car and the three pumps rebuilt as
// real 3D models by SAM 3D (fal-ai/sam-3/3d-objects) and stood exactly where they are in the painting.
// The teal car further back stays painted (a painted room is enough that far away). The painting
// behind is a "clean plate" (assets/reliefs/sam-3d-test/): the same painting with those four things
// painted out by Flux 3 edit (used only inside their outlines) and a flat floor in the depth picture
// where they stood (paper-film/tools/ground_under_objects.py).
//
// How the models are placed: SAM 3D gives each model a size, a turn and a position in its own guess of
// the camera (assets/models/sam-3d-test/layout.json, mapped by paper-film/tools/sam3d_fit_layout.py).
// Its lens is wider than the film's, so each model keeps its turn and its spot in the picture, is slid
// along its line of sight until its lowest points touch the ground fitted around its base, and is
// sized so it covers the same part of the picture.
//
// How they look painted: each model wears the painting itself, projected from where it was painted,
// on every surface the painting showed (the real brushwork, the glowing headlights, the windscreen's
// interior). Only surfaces the painting never showed use SAM 3D's own surface, tinted to match by
// comparing the two where both exist. They take only a touch of the lamp (the painting already has its
// light painted in) and cast shadows on the painted ground.
//
// Views (?view= in the address, set with PAPER_FILM_QUERY):
//   painting     from where the painting was painted (should look like the painting)
//   small-push   a short straight push towards the car (the snapshot's third picture)
//   original     the original painting as a painted room, without models (for comparison)
//   also: gentle-push, push-in, small-push-2, moved, side, step-right, low-left (bigger moves tear the
//   painted room: its canopy post and kiosk bend)
// Use: PAPER_FILM_QUERY=view=small-push node paper-film/tools/render-paper-film.mjs sam-3d-petrol-station-test OUT --stills 190
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';
import { placeSamModels } from './painted-projection.js';

const view = new URLSearchParams(location.search).get('view') ?? 'painting';
const MODELS = '/assets/models/sam-3d-test';

const testPage = {
  async build(kit) {
    // the same light as page 7: a warm lamp under the canopy, a cool sky
    kit.lightRig({ keyColour: 0xffd09a, keyShare: 0.75, keyFrom: [2.8, 5.5, -3.5], keyTarget: [0, -2.1, -7.6], fillSky: 0x6f86a0, fillGround: 0x1c1a18,
      fillShare: 0.22, haze: 0x101823, hazeDensity: 0.004, shadowBox: 6, shadowSoftness: 5, background: 0x0b1118, reflections: 0.3 });
    const original = view === 'original';
    // the clean plate lives in its own folder; borrow it for this one painted room
    const chapterReliefs = kit.reliefFolder;
    if (!original) kit.reliefFolder = '/assets/reliefs/sam-3d-test';
    const room = await kit.relief(original ? '409-bg-petrol-station-1973' : '409-petrol-station-clean', { near: 6, far: 70, fov: 40, margin: 0.22 });
    kit.reliefFolder = chapterReliefs;
    const placed = original ? [] : await placeSamModels(kit, room, { models: MODELS,
      painting: '/assets/reliefs/inflation-chapter-2/409-bg-petrol-station-1973.jpg', masks: '/assets/reliefs/sam-3d-test' });
    const car = placed.find((p) => p.name.includes('red-car'))?.model.position.clone() ?? room.pointAt(0.22, 0.38);
    const pump = placed.find((p) => p.name.includes('pump-middle'))?.model.position.clone() ?? room.pointAt(0.62, 0.45);
    const pivot = car.clone().lerp(pump, 0.45);
    const around = (yaw, closer, lift) => {
      const offset = new THREE.Vector3(0, 0, 0).sub(pivot).applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(yaw)).multiplyScalar(1 - closer);
      return pivot.clone().add(offset).add(new THREE.Vector3(0, lift, 0));
    };
    const cameras = {
      painting: { position: [0, 0, 0], target: [0, 0, -30], fov: 40 },
      original: { position: [0, 0, 0], target: [0, 0, -30], fov: 40 },
      // a painted room only holds together for small moves, so these stay modest
      moved: { position: around(-7, 0.2, 0.25).toArray(), target: pivot.clone().add(new THREE.Vector3(0, 0.9, 0)).toArray(), fov: 40 },
      side: { position: around(-15, 0.32, 0.45).toArray(), target: pivot.clone().add(new THREE.Vector3(0.2, 0.6, 0)).toArray(), fov: 40 },
    };
    // candidate gentle moves, to find which shows the models best with the least tearing
    const toward = (point, share) => new THREE.Vector3(0, 0, 0).lerp(point, share);
    cameras['push-in'] = { position: toward(car, 0.3).add(new THREE.Vector3(0, 0.1, 0)).toArray(), target: car.clone().add(new THREE.Vector3(0.6, 0.3, 0)).toArray(), fov: 40 };
    cameras['gentle-push'] = { position: toward(car, 0.16).add(new THREE.Vector3(0, 0.05, 0)).toArray(), target: car.clone().lerp(new THREE.Vector3(0, -2, -30), 0.5).toArray(), fov: 40 };
    cameras['step-right'] = { position: [0.9, 0.15, -2.2], target: car.clone().add(new THREE.Vector3(0.9, 0.5, 0)).toArray(), fov: 40 };
    cameras['low-left'] = { position: [-0.7, -0.35, -2.6], target: car.clone().add(new THREE.Vector3(1.0, 0.4, 0)).toArray(), fov: 40 };
    // a short straight push towards the car, looking the same way as the painting: the smallest move
    // that still shows the models are solid, and the least tearing of the painted room
    cameras['small-push'] = { position: [-0.45, -0.05, -1.6], target: [-0.45, -0.6, -31.6], fov: 40 };
    cameras['small-push-2'] = { position: [-0.7, 0.05, -2.4], target: [-0.9, -0.7, -32.4], fov: 40 };
    const camera = cameras[view] ?? cameras.painting;
    const focus = new THREE.Vector3(...camera.position).distanceTo(car);
    return {
      pose: () => ({ camera: { position: new THREE.Vector3(...camera.position), target: new THREE.Vector3(...camera.target), fov: camera.fov, roll: 0, focus },
        look: { aperture: 6, maxBlur: 10, exposure: 0.95, glowThreshold: 0.92, glowStrength: 0.6, contrast: 1.06, fade: 0 } }),
    };
  },
};


export async function build() {
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2/timeline.json', piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles: [testPage], pageNumbers: [7] });
}
