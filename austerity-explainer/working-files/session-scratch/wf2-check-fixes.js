(async () => {
const meta = {
  name: 'check-fixes',
  description: 'Independent check that every critique finding on a chapter is fixed (stills and code), and that the fixes caused no new problems',
  whenToUse: 'After helpers have fixed the findings from critique-film, before filming. Pass the findings files, the new stills per page group, and the kit and chapter.',
  phases: [{ title: 'Check', detail: 'one checker per page group compares each finding with the new stills and the code, and looks for new problems' }],
}

// args: {
//   kit: '/path/to/film-kit', chapter: 'my-chapter'               (required)
//   guide: '/path/to/guide.md'                                     (required: the on-screen rules)
//   wordTimes: '/path/to/word times or timeline.json'              (required)
//   groups: [{ label: 'pages 1-3', pages: [1, 2, 3],
//              findings: 'where the findings for these pages are (files or a short list)',
//              stills: 'the new contact sheets / stills for these pages' }]   (required, 1-4 groups)
//   joins: '/path/to/sheet of page turns drawn in one run'          (optional)
//   changes: 'shared changes made alongside (e.g. a new label option, a recoloured piece)' (optional)
//   effort: 'medium'                                               (optional)
// }
const A = args ?? {}
for (const k of ['kit', 'chapter', 'guide', 'wordTimes', 'groups']) if (!A[k]) throw new Error(`check-fixes needs args.${k}`)
const EFFORT = A.effort ?? 'medium'
const SCHEMA = { type: 'object', properties: {
  findings: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'string' }, finding: { type: 'string' }, status: { type: 'string', enum: ['fixed', 'partly fixed', 'not fixed'] }, evidence: { type: 'string' }, remaining: { type: 'string' } },
    required: ['page', 'finding', 'status', 'evidence', 'remaining'] } },
  new_problems: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'string' }, time: { type: 'string' }, severity: { type: 'string', enum: ['must fix', 'should fix', 'minor'] }, what: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' } },
    required: ['page', 'time', 'severity', 'what', 'fix', 'evidence'] } },
  verdict: { type: 'string' },
}, required: ['findings', 'new_problems', 'verdict'] }

phase('Check')
const results = await parallel(A.groups.map((g) => () => agent(`You are an independent checker; you did not make these fixes. A narrated explainer film (chapter "${A.chapter}", 1080 x 1920, cinema look) was critiqued and helpers then edited its page files ${A.kit}/paper-film/scenes/${A.chapter}/page-N.js.${A.changes ? ` Shared changes made alongside: ${A.changes}.` : ''} On-screen rules: ${A.guide}. Word times: ${A.wordTimes}.

Your pages: ${g.label}. Findings to check: ${g.findings}. New stills (look with the Read tool; open single stills at full size when needed): ${g.stills}.${A.joins ? ` Page turns drawn in one run: ${A.joins}.` : ''}
1. For EACH finding: fixed, partly fixed or not fixed? Check the stills AND the code change (cite file and line).
2. Look for NEW problems the fixes caused: anything now clipped, off screen, overlapping, unreadable, mistimed, contradicting the narration, breaking the rules, or broken between moments (a camera change can push another label's target off screen).
You may draw at most 4 extra stills if essential: cd ${A.kit} && PAPER_FILM_CHAPTER=${A.chapter} PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages ${A.kit}/paper-film/out/check-fixes/pN --stills T1 T2 (times separated by spaces). Do not edit any files. Be strict and specific.`, { label: `check ${g.label}`, phase: 'Check', schema: SCHEMA, effort: EFFORT }).then((r) => r && ({ group: g.label, ...r }))))
return results.filter(Boolean)

})()