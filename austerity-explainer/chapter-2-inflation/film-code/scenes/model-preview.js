// What this does: shows one Blender model (.glb) on its own in the cinema stage, under the dusk
// lamp light of the two-factories set, so it can be photographed and judged before it goes into a
// page. Not part of any film.
//
// Use (from the kit folder):
//   PAPER_FILM_QUERY="model=/assets/models/inflation-chapter-2/factory-a.glb&cam=1.5,1.2,6&look=0,0.8,0&fov=42" \
//   node paper-film/tools/render-paper-film.mjs model-preview OUT_FOLDER --stills 1 2 3
// cam: camera position; look: the point it looks at; fov: lens angle; running: 0 to 1 (lit windows);
// ground: 0 for no ground; sky: a painted room's name for the far sky. Each still time t turns the model by t * spin degrees (spin=0 by default),
// so several stills can show several sides.

import { THREE } from './cinema-kit.js';
import { buildCinemaChapter } from './cinema-chapter.js';
import { paperGround } from './models.js';
import { modelFactory } from './model-loader.js';
import { Smoke } from './effects.js';

export async function build() {
  const query = new URLSearchParams(location.search);
  const numbers = (name, fallback) => (query.get(name) ?? fallback).split(',').map(Number);
  const page = {
    async build(kit) {
      kit.lightRig({ keyColour: 0xffc98a, keyShare: 0.8, keyFrom: [-12, 6.5, 7], keyTarget: [0, 0, -1], fillSky: 0x6f8796, fillGround: 0x241e18,
        fillShare: 0.24, haze: 0x1a2228, hazeDensity: 0.012, shadowBox: 8, shadowSoftness: 6, background: 0x10161b, reflections: 0.3 });
      // chapter 2's painted dusk sky, when this kit has it (a plain dark sky otherwise)
      try {
        const backdrop = await kit.backdrop(query.get('sky') ?? '402-bg-dusk-skyline', { distance: 52, fov: 40 });
        backdrop.position.set(0, 13, -52); backdrop.scale.setScalar(4.6);
      } catch { /* no painting: the background colour shows */ }
      if (query.get('ground') !== '0') kit.scene.add(paperGround({ at: [0, -0.02, -8], width: 70, depth: 60, colour: 0x2e2c28 }).group);
      const model = await modelFactory(query.get('model'));
      kit.scene.add(model.group);
      const running = Number(query.get('running') ?? 1);
      model.setRunning(running);
      const smoke = new Smoke(kit.scene, { count: 12, life: 3.4, seed: 3 });
      const spin = Number(query.get('spin') ?? 0);
      const shot = kit.stillShot({ position: numbers('cam', '1.5,1.4,6.5'), target: numbers('look', '0,0.9,0'), fov: Number(query.get('fov') ?? 42) }, [], { name: 'preview' });
      return {
        pose(t) {
          model.group.rotation.y = THREE.MathUtils.degToRad(spin * t);
          const top = model.chimneyTop.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), model.group.rotation.y);
          smoke.set({ t: t + 5, origin: top.toArray(), scale: 0.9 });
          return { camera: shot(t), look: { aperture: Number(query.get('aperture') ?? 4), maxBlur: 10, exposure: 0.95, glowThreshold: 0.95, glowStrength: 0.7, contrast: 1.08 } };
        },
      };
    },
  };
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2/timeline.json', piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles: [page], pageNumbers: [3] });
}
