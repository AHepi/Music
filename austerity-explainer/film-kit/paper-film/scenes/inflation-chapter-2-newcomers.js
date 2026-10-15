// What this does: chapter 2 of the austerity explainer for newcomers ("What really causes inflation", about 7
// minutes, log 34), in the look kept in log 32: each place a 3D set built in Blender, painted over, and the painting
// shone back onto the set. Pages not built yet are stand-ins (inflation-chapter-2-newcomers/placeholder.js), so the
// chapter can be timed and filmed end to end at any stage. Built lazily: a piece of film loads only the pages it shows.
// Real pages so far: 3, 4 and 5 (the Works: the quiet factory, the flat-out factory and the first guess, the rule), in
// inflation-chapter-2-newcomers/page-3.js to page-5.js, sharing works-effects.js.
// Source for the history and the argument about who pays: Clara E. Mattei, The Capital Order (2022).
//
// The timeline: examples/inflation-chapter-2-newcomers/timeline.json once the narration is recorded; until then the
// estimated one (timeline-estimated.json, made by narration-tools/estimate_timeline.py from the script).
import { buildCinemaChapter } from './cinema-chapter.js';
import * as standIn from './inflation-chapter-2-newcomers/placeholder.js';
import * as page3 from './inflation-chapter-2-newcomers/page-3.js';
import * as page4 from './inflation-chapter-2-newcomers/page-4.js';
import * as page5 from './inflation-chapter-2-newcomers/page-5.js';

const TIMELINE = new URLSearchParams(location.search).get('timeline') ?? 'timeline-estimated';
// one module per page, in order; replace a stand-in with its real page file as each is built
// (built so far: pages 3, 4 and 5, the Works; their plates stand in for the paintings until those are approved)
const pageFiles = [standIn, standIn, page3, page4, page5, standIn, standIn, standIn,
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
