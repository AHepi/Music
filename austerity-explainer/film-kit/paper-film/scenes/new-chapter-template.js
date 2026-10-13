// What this does: the starting point for a new chapter. Copy this file and the folder
// new-chapter-template/ under a new name (for example enclosures-chapter-1.js and
// enclosures-chapter-1/), then change the three settings below and write one page file per page.
//
// Film it with: bash paper-film/tools/film-chapter.sh enclosures-chapter-1
// Check single moments with: node paper-film/tools/render-paper-film.mjs enclosures-chapter-1 FOLDER --stills 3.5 12.0

import { buildChapter } from './paper-chapter.js';
import * as page1 from './new-chapter-template/page-1.js';
// import * as page2 from './new-chapter-template/page-2.js';   ...one line per page

export function build() {
  return buildChapter({
    // where prepare_paper_pieces.py wrote this chapter's pieces (the cut list's "output_folder")
    piecesFolder: '/paper-film/pieces/new-chapter-template',
    // the chapter timeline made by narration-tools/assemble_chapter_narration.py
    timelineUrl: '/examples/new-chapter-template/timeline.json',
    // the page files, in order
    pageFiles: [page1],
  });
}
