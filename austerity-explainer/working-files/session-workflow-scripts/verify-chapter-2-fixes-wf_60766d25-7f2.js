export const meta = {
  name: 'verify-chapter-2-fixes',
  description: 'Independent check that every confirmed critique finding on chapter 2 is fixed, with no new problems, before re-filming',
  phases: [
    { title: 'Check', detail: 'three checkers, one per page group, compare findings with the new stills and code' },
  ],
}
const S = '/home/user/work/chapter-2/stills'
const K = '/home/user/work/paper-pop-up-film-kit/paper-film/scenes/inflation-chapter-2'
const GROUPS = [
  { label: 'pages 1-3', pages: [1, 2, 3], sheets: `${S}/fix-p1-c/sheet.jpg, ${S}/fix-p2-a/sheet.jpg, ${S}/fix-p3-d/sheet.jpg, ${S}/fix-p3-e/sheet.jpg, ${S}/fix-p3-p8-a/sheet.jpg` },
  { label: 'pages 4-6', pages: [4, 5, 6], sheets: `${S}/fix-p4-b/sheet.jpg, ${S}/fix-p4-c/sheet.jpg, ${S}/fix-p5-c/sheet.jpg, ${S}/fix-p5-d (single stills), ${S}/fix-p6-c/sheet.jpg, ${S}/fix-p6-d/sheet.jpg` },
  { label: 'pages 7-10', pages: [7, 8, 9, 10], sheets: `${S}/fix-p7-c/sheet.jpg, ${S}/fix-p8-d/sheet.jpg, ${S}/fix-p8-lead/small.jpg (dollar tag), ${S}/fix-p8-lead3/sheet.jpg (latest flat-out shot), ${S}/fix-p9-d/sheet.jpg, ${S}/fix-p9-e/still-225.60.jpg, ${S}/fix-p10-b/sheet.jpg` },
]
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
const results = await parallel(GROUPS.map((g) => () => agent(`You are an independent checker (you did not make these fixes). A narrated explainer film (chapter 2, "What really causes inflation", 1080 x 1920) was critiqued; the confirmed findings for each page are in /home/user/work/chapter-2/fixes/page-N.md (N = ${g.pages.join(', ')}). Helpers then edited the page files ${K}/page-N.js (page 3 also two-factories-set.js; the shared label function in ../graphics.js gained a 'plate' option; the politician's tie piece was recoloured to charcoal; page 8's house tag now uses $ for New Zealand). The rules for on-screen words are in section 5 of /home/user/Music/austerity-explainer/chapter-2-inflation/19 Guide - building a cinema page.md; word times are in /home/user/work/chapter-2/reference/page-words.txt.

Your pages: ${g.label}. New stills to look at (Read tool; open single stills in the same folders at full size when needed): ${g.sheets}. Page turns from the whole chapter drawn in one run: ${S}/joins-d/sheet.jpg.
For EACH finding in the findings files: is it fixed? Check the stills AND read the code change (cite the line). Then look for NEW problems the fixes may have caused (anything now clipped, overlapping, unreadable, mistimed, inaccurate against the narration, against the rules, or broken between moments). You may draw at most 4 extra stills if essential: cd /home/user/work/paper-pop-up-film-kit && PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages ${S}/verify-${g.pages.join('')} --stills T1 T2 (times separated by spaces). Do not edit any files. Be strict and specific.`, { label: `check ${g.label}`, phase: 'Check', schema: SCHEMA, effort: 'medium' }).then((r) => r && ({ group: g.label, ...r }))))
return results.filter(Boolean)
