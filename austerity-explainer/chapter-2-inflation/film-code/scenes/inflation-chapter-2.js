// What this does: chapter 2 of the austerity explainer ("What really causes inflation", 4 minutes
// 30 seconds), in the cinema look: each of its ten pages is a 3D scene (painted rooms with depth,
// card models, paper cut-outs, light and dust) with documentary graphics on top, built from the page
// files in scenes/inflation-chapter-2/ and joined by page peels. Source for the history and the
// argument about who pays: Clara E. Mattei, The Capital Order (2022).
//
// It needs: the pieces in pieces/inflation-chapter-2, the painted rooms in
// assets/reliefs/inflation-chapter-2 and the narration timeline examples/inflation-chapter-2/timeline.json.

import { buildCinemaChapter } from './cinema-chapter.js';
import * as page1 from './inflation-chapter-2/page-1.js';
import * as page2 from './inflation-chapter-2/page-2.js';
import * as page3 from './inflation-chapter-2/page-3.js';
import * as page4 from './inflation-chapter-2/page-4.js';
import * as page5 from './inflation-chapter-2/page-5.js';
import * as page6 from './inflation-chapter-2/page-6.js';
import * as page7 from './inflation-chapter-2/page-7.js';
import * as page8 from './inflation-chapter-2/page-8.js';
import * as page9 from './inflation-chapter-2/page-9.js';
import * as page10 from './inflation-chapter-2/page-10.js';

export function build() {
  return buildCinemaChapter({
    timelineUrl: '/examples/inflation-chapter-2/timeline.json',
    piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles: [page1, page2, page3, page4, page5, page6, page7, page8, page9, page10],
    pageNumbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  });
}
