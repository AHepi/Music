// What this does: a quick check of the cinema stage: one painted room with depth, seen from where it
// was painted and from a camera moved into it. Not part of any film.
import { buildCinemaChapter } from './cinema-chapter.js';
const testPage = {
  async build(kit) {
    kit.lightRig({ hazeDensity: 0.0 });
    const room = await kit.relief('102-bg-munitions-factory', { near: 6, far: 70, fov: 40 });
    const shot = kit.shot([
      { t: 20, position: [0, 0, 0], target: [0, 0, -30], fov: 40, focus: 12 },
      { t: 30, position: [0.4, -0.6, -4], target: [0.3, -0.8, -30], fov: 40, focus: 10 },
    ], { handheld: 0 });
    return { pose: (t) => ({ camera: shot(t), look: { aperture: t > 25 ? 10 : 0 } }) };
  },
};
export async function build() {
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2/timeline.json', piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles: [testPage], pageNumbers: [2] });
}
