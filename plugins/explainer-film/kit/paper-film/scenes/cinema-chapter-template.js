// What this does: a starting point for a whole chapter in the cinema look. Copy it to
// paper-film/scenes/YOUR-CHAPTER.js, change the chapter name, and list every page file. Film it with
// tools/film-chapter-parallel.sh YOUR-CHAPTER.
import { buildCinemaChapter } from './cinema-chapter.js';
import * as page1 from './cinema-chapter-template/page-1.js';   // CHANGE: one line per page

const CHAPTER = 'inflation-chapter-2';                            // CHANGE: your chapter's folder name

export function build() {
  return buildCinemaChapter({
    timelineUrl: `/examples/${CHAPTER}/timeline.json`,
    piecesFolder: `/paper-film/pieces/${CHAPTER}`,
    reliefFolder: `/assets/reliefs/${CHAPTER}`,
    pageFiles: [page1],                                           // CHANGE: [page1, page2, ...]
    pageNumbers: [2],                                             // CHANGE: [1, 2, ...] (the timeline's page numbers)
  });
}
