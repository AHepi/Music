export const meta = {
  name: 'build-pages',
  description: 'Build several cinema-look page files in parallel (one helper per page, each checking its own stills), then check the pages for consistency',
  whenToUse: 'When a chapter has its narration timeline, painted rooms and cut-out pieces, and one or two pattern pages are finished. Pass the kit, chapter, guide and a brief per page.',
  phases: [
    { title: 'Build', detail: 'one helper per page builds page-N.js and checks its stills' },
    { title: 'Consistency', detail: 'one reviewer compares all pages for look, wording and timing' },
  ],
}

// args: {
//   kit: '/path/to/film-kit'                     (required)
//   chapter: 'my-chapter'                        (required)
//   guide: '/path/to/guide.md'                   (required: the build-cinema-page skill's guide, adapted to this chapter)
//   patterns: 'paper-film/scenes/my-chapter/page-2.js and page-3.js'  (optional: finished pages to copy)
//   stills: '/path/to/stills-folder'             (optional, default <kit>/paper-film/out/stills-<chapter>)
//   pages: [{ number: 4, brief: 'narration, window, research ids and a beat-by-beat plan' }]  (required, at most 9)
//   effort: 'medium'                             (optional)
// }
const A = args ?? {}
for (const k of ['kit', 'chapter', 'guide', 'pages']) if (!A[k]) throw new Error(`build-pages needs args.${k}`)
const EFFORT = A.effort ?? 'medium'
const STILLS = A.stills ?? `${A.kit}/paper-film/out/stills-${A.chapter}`
if (A.pages.length > 9) log(`Note: ${A.pages.length} pages; consider running in two batches`)

const REPORT = { type: 'object', properties: {
  page: { type: 'number' }, file: { type: 'string' }, sheet: { type: 'string' },
  beats: { type: 'array', items: { type: 'object', properties: { time: { type: 'string' }, word: { type: 'string' }, seen: { type: 'string' } }, required: ['time', 'word', 'seen'] } },
  on_screen: { type: 'array', items: { type: 'object', properties: { shown: { type: 'string' }, source: { type: 'string' } }, required: ['shown', 'source'] } },
  unsure: { type: 'array', items: { type: 'string' } },
  shared_problems: { type: 'array', items: { type: 'string' }, description: 'faults found in shared files (worked around, not edited)' },
}, required: ['page', 'file', 'sheet', 'beats', 'on_screen', 'unsure', 'shared_problems'] }

const buildPrompt = (p) => `You are building page ${p.number} of a cinematic explainer film. First read the guide ${A.guide} completely and follow it.${A.patterns ? ` Finished pattern pages to copy the structure of: ${A.patterns}.` : ''} Then build ${A.kit}/paper-film/scenes/${A.chapter}/page-${p.number}.js.

Brief:
${p.brief}

Test often: cd ${A.kit} && PAPER_FILM_CHAPTER=${A.chapter} PAPER_FILM_PAGES=${p.number} node paper-film/tools/render-paper-film.mjs cinema-test-pages ${STILLS}/p${p.number}-a --stills T1 T2 T3 (times separated by spaces; a new folder letter each round), then python3 -I paper-film/tools/contact_sheet.py ${STILLS}/p${p.number}-a/sheet.jpg 4 ${STILLS}/p${p.number}-a and look at the sheet with the Read tool. Other pages are being built at the same time on the same machine: keep rounds to 4-8 stills.
Only create or edit page-${p.number}.js (or page-${p.number}-something.js); never edit shared files or other pages; spend no money; do not commit. Finish with a final round covering every beat (including the first and last moments of the page window) and report as asked.`

phase('Build')
const reports = await parallel(A.pages.map((p) => () => agent(buildPrompt(p), { label: `page ${p.number}`, phase: 'Build', schema: REPORT, effort: EFFORT })))
const built = reports.filter(Boolean)
const missing = A.pages.filter((p, i) => !reports[i]).map((p) => p.number)
if (missing.length) log(`No report from page(s): ${missing.join(', ')}`)

phase('Consistency')
const review = await agent(`You are checking that several pages of one film, built in parallel by different helpers, fit together. Their reports are below (each names its final contact sheet; look at every sheet with the Read tool, and at the pattern pages${A.patterns ? ` ${A.patterns}` : ''}). Read the guide ${A.guide}. List inconsistencies a viewer would notice (different title styles or positions, different colours for the same meaning, words in the phone-button zones, clashing camera styles, a page much busier or emptier than the rest, the same idea drawn two ways), anything that breaks the guide's on-screen rules, and every "shared_problems" item. For each: page, what, smallest fix. Then a short plain-language verdict. Do not edit files.
Reports:
${JSON.stringify(built, null, 1)}`, { label: 'consistency', phase: 'Consistency', effort: EFFORT })

return { reports: built, missing, review }
