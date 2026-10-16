// What this does: the house sample (log 27): about 37 seconds, no narration, showing how plan 2 of
// experiments/26 Plans ("the house": each chapter staged in one cut-away building of society, where
// it's decided at the top and who pays at the bottom) would carry chapter 3, Britain in the 1920s.
// One page: house-sample/page-1.js, built by house-sample/house-set.js, from chapter 1's paintings and
// cut-outs. Beat times are in examples/house-sample/timeline.json.
// Use: node paper-film/tools/render-paper-film.mjs house-sample OUT --stills 6 9.5 14
import { buildCinemaChapter } from './cinema-chapter.js';
import * as page1 from './house-sample/page-1.js';

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/house-sample/timeline.json',
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page1],
    pageNumbers: [1],
  });
}
