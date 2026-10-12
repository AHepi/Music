// What this does: the worked example. Chapter 1 of the austerity explainer ("Where austerity came
// from", 3 minutes 41 seconds), exactly as it was filmed, built from its ten page files in
// scenes/austerity-chapter-1/. Source for the story: Clara E. Mattei, The Capital Order (2022).
//
// It needs: the pieces made from examples/austerity-chapter-1/cut-list.json (run
// prepare_paper_pieces.py first) and the narration timeline examples/austerity-chapter-1/timeline.json.

import { buildChapter } from './paper-chapter.js';
import * as page1 from './austerity-chapter-1/page-1.js';
import * as page2 from './austerity-chapter-1/page-2.js';
import * as page3 from './austerity-chapter-1/page-3.js';
import * as page4 from './austerity-chapter-1/page-4.js';
import * as page5 from './austerity-chapter-1/page-5.js';
import * as page6 from './austerity-chapter-1/page-6.js';
import * as page7 from './austerity-chapter-1/page-7.js';
import * as page8 from './austerity-chapter-1/page-8.js';
import * as page9 from './austerity-chapter-1/page-9.js';
import * as page10 from './austerity-chapter-1/page-10.js';

export function build() {
  return buildChapter({
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    timelineUrl: '/examples/austerity-chapter-1/timeline.json',
    pageFiles: [page1, page2, page3, page4, page5, page6, page7, page8, page9, page10],
  });
}
