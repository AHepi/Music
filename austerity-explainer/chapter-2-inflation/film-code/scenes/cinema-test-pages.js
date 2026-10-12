// What this does: draws chosen pages of chapter 2 on their own, for checking single moments while a
// page is being made. Not part of the film. The page numbers come from the address (?pages=3,4).
import { buildCinemaChapter } from './cinema-chapter.js';
export async function build() {
  const numbers = (new URLSearchParams(location.search).get('pages') ?? '3').split(',').map(Number);
  const pageFiles = [];
  for (const n of numbers) pageFiles.push(await import(`./inflation-chapter-2/page-${n}.js`));
  return buildCinemaChapter({ timelineUrl: '/examples/inflation-chapter-2/timeline.json', piecesFolder: '/paper-film/pieces/inflation-chapter-2',
    reliefFolder: '/assets/reliefs/inflation-chapter-2', pageFiles, pageNumbers: numbers });
}
