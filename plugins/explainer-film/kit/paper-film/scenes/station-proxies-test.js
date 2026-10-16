// What this does: the first test of plan 23 (log 23), not part of any film. Painting 409's petrol
// station becomes simple 3D stand-ins that wear the painting: the two canopy posts, the kiosk, the
// canopy deck and the pump island are boxes fitted to their painted edges (fit_station_proxies.py),
// each showing the painting shone onto it from where it was painted, and lit exactly as the painted
// room is lit, so the painted light stays as painted. The red car and the three pumps are the SAM 3D
// models of log 22. Everything else (the forecourt, the road, the queued cars, hedges, houses, sky)
// stays the painted room with depth, but with the station painted out of it and flattened back
// (station_plates.py), so nothing near and upright is left in it to tear. The painted-out part is a
// rough smear: hidden from the painting's view and on a straight push, but a sideways step shows some
// of it behind the rear post (log 24).
//
// Which picture each part wears:
//   posts                       the original painting
//   kiosk, canopy, island       plate P: the painting with the posts, pumps and car painted out, so
//                               what the camera newly sees behind a post or pump is wall, not a copy
//                               of the post or pump
//   painted room behind         plate Q: plate P with the kiosk and canopy painted out too
// Light: the painted room and the stand-ins show the painting exactly, with its painted light (no stage
// lamp on them). The car and pumps keep mostly the painting's own light with a small share of the lamp
// on all their sides (it mainly shapes the sides the painting never showed), and their shadows fall on
// a see-through ground that shows only shadows (it sits on the forecourt, so not on the island top).
//
// Views (?view=): painting (from where it was painted: must match the painting), push (a 1.25x push
// toward the pump island: the posts must stay straight and slide in front of the kiosk), push-side
// (the same push with a small step sideways), original and original-push (the plain painted room,
// as the film has it today, from the painting's view and with the same push, for comparison).
// Use: PAPER_FILM_QUERY=view=push node paper-film/tools/render-paper-film.mjs station-proxies-test OUT --stills 190
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { placeSamModels, projectedMaterial, boxMesh, pixelsOf, shadowCatcher } from './painted-projection.js';

const view = new URLSearchParams(location.search).get('view') ?? 'painting';
const PAINTING = '/assets/reliefs/inflation-chapter-2/409-bg-petrol-station-1973.jpg';
const PLATES = '/assets/reliefs/station-test';

const testPage = {
  async build(kit) {
    // the same light as page 7: a warm lamp under the canopy, a cool sky
    kit.lightRig({ keyColour: 0xffd09a, keyShare: 0.75, keyFrom: [2.8, 5.5, -3.5], keyTarget: [0, -2.1, -7.6], fillSky: 0x6f86a0, fillGround: 0x1c1a18,
      fillShare: 0.22, haze: 0x101823, hazeDensity: 0.004, shadowBox: 6, shadowSoftness: 5, background: 0x0b1118, reflections: 0.3 });
    const original = view === 'original' || view === 'original-push';
    const chapterReliefs = kit.reliefFolder;
    if (!original) kit.reliefFolder = PLATES;
    // lit 0: the painted room shows the painting exactly, with its painted light and no stage lamp on it
    const room = await kit.relief(original ? '409-bg-petrol-station-1973' : '409-station-backdrop', { near: 6, far: 70, fov: 40, margin: 0.22, lit: 0 });
    kit.reliefFolder = chapterReliefs;
    const proxies = await (await fetch('/assets/models/station-test/proxies.json')).json();
    // the pushes move toward the pump island's middle; every view looks straight ahead, the painting's way
    const island = proxies.boxes.island.reduce((sum, p) => sum.add(new THREE.Vector3(...p)), new THREE.Vector3()).multiplyScalar(1 / 8);
    if (!original) {
      const painting = await loadTexture(PAINTING), plateP = await loadTexture(`${PLATES}/409-station-plate-p.jpg`);
      const paintPixels = await pixelsOf(PAINTING);
      for (const [name, corners] of Object.entries(proxies.boxes)) {
        // the colour of a face the painting never showed: the box's painted colour, in shade
        const middle = corners.reduce((s, p) => s.add(new THREE.Vector3(...p)), new THREE.Vector3()).multiplyScalar(1 / 8);
        const u = (middle.x / -middle.z / room.tanX + 1) / 2, v = (middle.y / -middle.z / room.tanY + 1) / 2;
        const i = (Math.round((1 - v) * (paintPixels.height - 1)) * paintPixels.width + Math.round(u * (paintPixels.width - 1))) * 4;
        const toLinear = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
        const shade = new THREE.Color(toLinear(paintPixels.data[i]), toLinear(paintPixels.data[i + 1]), toLinear(paintPixels.data[i + 2])).multiplyScalar(0.6);
        const picture = name.startsWith('post') ? painting : plateP;
        const mesh = boxMesh(corners, projectedMaterial(picture, room, { fallback: shade, lit: 0 }));   // the painting exactly, like the room
        mesh.name = name;
        kit.scene.add(mesh);
      }
      // the car and pumps: mostly the painting's own light, a touch of the lamp to shape their hidden sides
      await placeSamModels(kit, room, { models: '/assets/models/sam-3d-test', painting: PAINTING, masks: '/assets/reliefs/sam-3d-test', light: { glow: 0.95, lamp: 0.08 } });
      // their shadows fall on a see-through ground (the painted ground keeps its painted light)
      kit.scene.add(shadowCatcher(proxies.ground, { at: island.clone(), darkness: 0.5 }));
    }
    const target = island;
    const toward = (share, sideways = 0) => new THREE.Vector3(0, 0, 0).lerp(target, share).add(new THREE.Vector3(sideways, 0.0, 0));
    const cameras = {
      painting: { position: new THREE.Vector3(0, 0, 0), target: new THREE.Vector3(0, 0, -30) },
      original: { position: new THREE.Vector3(0, 0, 0), target: new THREE.Vector3(0, 0, -30) },
      // a 1.25x push: the distance to the island shrinks to 80%, still looking the painting's way
      push: { position: toward(0.2), target: new THREE.Vector3(0, 0, -30).add(toward(0.2)) },
      'push-side': { position: toward(0.2, -0.6), target: new THREE.Vector3(0, 0, -30).add(toward(0.2, -0.6)) },
    };
    // the same push on the plain painted room, as the film has it today (for comparison)
    cameras['original-push'] = cameras.push;
    const camera = cameras[view] ?? cameras.painting;
    const focus = camera.position.distanceTo(target);
    return {
      pose: () => ({ camera: { position: camera.position.clone(), target: camera.target.clone(), fov: 40, roll: 0, focus },
        look: { aperture: 4, maxBlur: 8, exposure: 0.95, glowThreshold: 0.92, glowStrength: 0.6, contrast: 1.06, fade: 0 } }),
    };
  },
};

export async function build() {
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2/timeline.json', piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles: [testPage], pageNumbers: [7] });
}
