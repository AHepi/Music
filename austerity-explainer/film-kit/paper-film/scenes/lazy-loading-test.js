// What this does: a stand-in chapter for testing memory and loading time (log 34): 16 pages on the estimated
// timeline of chapter 2 for newcomers, each loading its own copy of the heaviest painted set there is (the notice
// corner: the street, its props and signs, two paintings, projected), held on the projector's view. Built lazily
// (cinema-chapter.js), so a piece of film loads only the pages it shows. ?lazy=0 builds all 16 first, as before.
// Use: node paper-film/tools/render-paper-film.mjs lazy-loading-test OUT.mp4 --frames 1500 1560
import { buildCinemaChapter } from './cinema-chapter.js';
import { THREE } from './cinema-kit.js';
import { loadTexture } from '../stage/cinema-stage.js';
import { loadModel } from './model-loader.js';
import { loadProjector, projectPaintingOnto } from './projected-set.js';

const SET = '/assets/models/pit-village';
const LAZY = new URLSearchParams(location.search).get('lazy') !== '0';

function standIn() {
  return {
    join: { kind: 'peel', after: 0.3, length: 0.85 },
    async build(kit) {
      const [set, signs, projector, painting, behind] = await Promise.all([loadModel(`${SET}/notice-corner-set.glb`),
        loadModel(`${SET}/notice-corner-signs.glb`), loadProjector(`${SET}/notice-corner-camera.json`),
        loadTexture(`${SET}/notice-corner-painted.jpg`), loadTexture(`${SET}/notice-corner-behind.jpg`)]);
      const everything = new THREE.Group();
      everything.add(set, signs);
      kit.scene.add(everything);
      everything.updateMatrixWorld(true);
      projectPaintingOnto(kit, everything, painting, projector, { behind: { painting: behind, hide: [] } });
      const view = { position: projector.position.toArray(), target: projector.userData.target.toArray(), fov: projector.fov };
      const camera = kit.stillShot(view, [], { name: 'projector' });
      return { pose: (t) => ({ camera: camera(t), still: true, look: { exposure: 1, aperture: 0 } }) };
    },
  };
}

const pageFiles = Array.from({ length: 16 }, standIn);
export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/inflation-chapter-2-newcomers/timeline-estimated.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles,
    pageNumbers: pageFiles.map((_, i) => i + 1),
    lazy: LAZY,
  });
}
