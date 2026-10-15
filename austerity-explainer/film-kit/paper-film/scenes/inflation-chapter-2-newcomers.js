// What this does: chapter 2 of the austerity explainer for newcomers ("What really causes inflation", about 7
// minutes, log 34), in the look kept in log 32: each place a 3D set built in Blender, painted over, and the painting
// shone back onto the set. Pages not built yet are stand-ins (inflation-chapter-2-newcomers/placeholder.js), so the
// chapter can be timed and filmed end to end at any stage. Built lazily: a piece of film loads only the pages it shows.
// Source for the history and the argument about who pays: Clara E. Mattei, The Capital Order (2022).
//
// The timeline: examples/inflation-chapter-2-newcomers/timeline.json once the narration is recorded; until then the
// estimated one (timeline-estimated.json, made by narration-tools/estimate_timeline.py from the script).
import { buildCinemaChapter } from './cinema-chapter.js';
import * as standIn from './inflation-chapter-2-newcomers/placeholder.js';

const TIMELINE = new URLSearchParams(location.search).get('timeline') ?? 'timeline-estimated';
// one module per page, in order; replace a stand-in with its real page file as each is built
const pageFiles = [standIn, standIn, standIn, standIn, standIn, standIn, standIn, standIn,
  standIn, standIn, standIn, standIn, standIn, standIn, standIn, standIn];

export function build() {
  return buildCinemaChapter({
    timelineUrl: `/examples/inflation-chapter-2-newcomers/${TIMELINE}.json`,
    piecesFolder: '/paper-film/pieces/austerity-chapter-1',
    reliefFolder: '/assets/reliefs/inflation-chapter-2',
    pageFiles,
    pageNumbers: pageFiles.map((_, i) => i + 1),
    lazy: true,
  });
}
