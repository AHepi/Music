// What this does: a test page for the flat graphics (graphics.js) on a plain dark background, so a new graphic
// can be looked at on its own: the 100-dot panel (log 34) in its three uses in chapter 2 for newcomers.
// Use: node paper-film/tools/render-paper-film.mjs graphics-test OUT --stills 3
import { buildCinemaChapter } from './cinema-chapter.js';
import { dotPanel } from './graphics.js';

const page = {
  join: { kind: 'dissolve', after: 0.3, length: 0.5 },
  async build(kit) {
    const camera = kit.stillShot({ position: [0, 1.6, 6], target: [0, 1.6, 0], fov: 40 }, [], { name: 'empty' });
    return {
      pose: (t) => ({ camera: camera(t), look: { exposure: 1, aperture: 0 } }),
      draw2D(ctx, t) {
        dotPanel(ctx, t, { at: 0.2, x: 80, y: 160, empty: 0.6, emptyAt: 0.8, heading: 'Britain, the war years', caption: 'Fewer than 1 in 100 out of work' });
        dotPanel(ctx, t, { at: 0.2, x: 80, y: 760, empty: 3, emptyAt: 0.8, heading: 'End of 2021', caption: 'About 3 in 100 out of work' });
        dotPanel(ctx, t, { at: 0.2, x: 80, y: 1360, empty: 5.6, ghost: 3, emptyAt: 0.8, ghostAt: 2.2, heading: 'Middle of 2026', caption: 'Nearly 6 in 100 out of work' });
        return true;
      },
    };
  },
};
export function build() {
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2-newcomers/timeline-estimated.json', piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles: [page], pageNumbers: [1], lazy: true });
}
