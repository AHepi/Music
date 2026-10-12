// What this does: draws chosen pages of a cinema chapter on their own, for checking single moments
// while a page is being made. Not part of any film. The address says which chapter and pages
// (?chapter=my-chapter&pages=3,4), set from the PAPER_FILM_CHAPTER and PAPER_FILM_PAGES settings of
// render-paper-film.mjs. The chapter's files are found by its name:
//   pages      paper-film/scenes/CHAPTER/page-N.js
//   pieces     paper-film/pieces/CHAPTER/        (cut-outs and pieces.json)
//   reliefs    assets/reliefs/CHAPTER/           (painted rooms with depth)
//   timeline   examples/CHAPTER/timeline.json    (every word's time)
import { buildCinemaChapter } from './cinema-chapter.js';
export async function build() {
  const query = new URLSearchParams(location.search);
  const chapter = query.get('chapter') ?? 'inflation-chapter-2';
  const numbers = (query.get('pages') ?? '1').split(',').map(Number);
  const pageFiles = [];
  for (const n of numbers) pageFiles.push(await import(`./${chapter}/page-${n}.js`));
  return buildCinemaChapter({ timelineUrl: `/examples/${chapter}/timeline.json`, piecesFolder: `/paper-film/pieces/${chapter}`,
    reliefFolder: `/assets/reliefs/${chapter}`, pageFiles, pageNumbers: numbers });
}
