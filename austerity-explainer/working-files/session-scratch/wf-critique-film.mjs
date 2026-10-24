export const meta = {
  name: 'critique-film',
  description: 'Independent critique of a cinema-look chapter (pictures, on-screen content, code), then a skeptic verifies, merges and ranks every finding',
  whenToUse: 'When all pages of a chapter are built (before or while filming). Pass the kit folder, chapter name, script, word times, guide, and where the stills of each page group are.',
  phases: [
    { title: 'Critique', detail: 'picture critics per page group, content critics, one code critic' },
    { title: 'Verify', detail: 'one skeptic re-checks every finding, dedupes and ranks' },
  ],
}

// args: {
//   kit: '/path/to/film-kit'                     (required: the folder holding paper-film/, assets/, examples/)
//   chapter: 'my-chapter'                        (required: paper-film/scenes/<chapter>/page-N.js)
//   script: '/path/to/script.md'                 (required: narration page by page)
//   wordTimes: '/path/to/page-words.txt or examples/<chapter>/timeline.json' (required)
//   guide: '/path/to/guide or the build-cinema-page skill file' (required: the on-screen rules)
//   ledger: '/path/to/research-ledger.md'        (optional)
//   brief: 'what the owner asked for, in their words' (optional)
//   pictureGroups: [{ label: 'pages 1-3', stills: 'which contact sheets / stills to look at, and fixes made since' }]  (required, 1-4 groups)
//   contentGroups: [{ label: 'pages 1-5', pages: '1-5' }]  (optional, default two halves of 10 pages)
//   notes: 'fixes already made that critics should not report again' (optional)
//   effort: 'medium'                             (optional)
// }
const A = args ?? {}
for (const k of ['kit', 'chapter', 'script', 'wordTimes', 'guide', 'pictureGroups']) if (!A[k]) throw new Error(`critique-film needs args.${k}`)
const EFFORT = A.effort ?? 'medium'
const PAGES = `${A.kit}/paper-film/scenes/${A.chapter}`
const STILLS = `${A.kit}/paper-film/out/critique-${A.chapter}`
const COMMON = `Context: you are reviewing a chapter of a narrated explainer film for a phone screen (1080 x 1920, 30 frames a second) in the cinema look: each page is a 3D scene (painted rooms with depth, card models, paper cut-outs, lamp light, dust, focus blur, film grain) with flat documentary graphics on top, joined by page peels.${A.brief ? ` The owner asked: "${A.brief}".` : ' It must be cinematic yet still carry the information.'}
Files: script ${A.script}; word times ${A.wordTimes}; on-screen rules ${A.guide}${A.ledger ? `; research ledger ${A.ledger}` : ''}; page files ${PAGES}/page-N.js; shared code ${A.kit}/paper-film/scenes/ (cinema-kit.js, models.js, effects.js, graphics.js, cinema-chapter.js) and ${A.kit}/paper-film/stage/cinema-stage.js.
If you must draw a still, write only into ${STILLS}/ and draw at most 4: cd ${A.kit} && PAPER_FILM_CHAPTER=${A.chapter} PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages ${STILLS}/pN --stills T1 T2 (times separated by spaces).
${A.notes ? `Already fixed (do not report again): ${A.notes}\n` : ''}Be a demanding, specific critic: page, moment (seconds), what is wrong, why it matters to a viewer, the smallest concrete fix, and the evidence you actually looked at. No padding, no invented problems. Do not edit any files.`

const FINDINGS = { type: 'object', properties: {
  findings: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'string' }, time: { type: 'string' },
    category: { type: 'string', enum: ['clarity', 'legibility', 'composition', 'cinematic quality', 'consistency', 'accuracy', 'rules', 'timing', 'bug', 'other'] },
    severity: { type: 'string', enum: ['must fix', 'should fix', 'nice to have'] },
    what: { type: 'string' }, why: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' },
  }, required: ['page', 'time', 'category', 'severity', 'what', 'why', 'fix', 'evidence'] } },
  overall: { type: 'string' },
}, required: ['findings', 'overall'] }

const contentGroups = A.contentGroups ?? [{ label: 'pages 1-5', pages: '1-5' }, { label: 'pages 6-10', pages: '6-10' }]
const CRITICS = [
  ...A.pictureGroups.map((g) => ({ key: `pictures ${g.label}`, prompt: `${COMMON}

Your area: the PICTURES of ${g.label}, as a film director and an information designer. Look at every still with the Read tool (open single stills at full size when a detail matters): ${g.stills}
Judge: does each moment clearly show what the narrator says then (check the script and word times)? Is it cinematic (composition, light, depth, framing, focus) while staying informative? Are words readable, not clipped or overlapping, and out of the phone-button zones (bottom 380 px, right 140 px)? Anything confusing, cluttered, empty, ugly, anachronistic or inconsistent with the other pages? Rendering faults (tearing, streaks, white blocks, stray marks, things floating or sinking wrongly)?` })),
  ...contentGroups.map((g) => ({ key: `content ${g.label}`, prompt: `${COMMON}

Your area: the ON-SCREEN CONTENT of pages ${g.pages}. Read those page files and list every word, number and label they put on screen (draw2D strings, kit.word / kit.card, price tags, flip counters, dial scales) with its timing word. For each check: (1) it is a short form of what the narrator says at that moment, or plainly illustrative; (2) every number matches the research and adds no claim the narration does not make; (3) the strict on-screen rules in the guide; (4) it appears while the matching words are said. Also spelling and typography (quotes, %, ×, currency, dates).` })),
  { key: 'code', prompt: `${COMMON}

Your area: the CODE, looking for faults that would show in the filmed chapter. The film is drawn in separate stretches (each starts in a fresh browser at its first frame after 3 warm-up frames), so every page's pose(t) and draw2D(ctx, t) must give the same picture for a given t whatever was drawn before. Check every page file and the shared code for: state carried between frames, Math.random or Date, camera keys out of time order, kit.at lookups hitting the wrong occurrence of a repeated word (check against the word times), events outside the page's window (about the previous page's last word + 0.3 s to its own last word + 1.2 s), objects left visible after a cut inside a page, and canvas state leaking between pages. Cite file and line.` },
]

phase('Critique')
const results = await parallel(CRITICS.map((c) => () => agent(c.prompt, { label: `critique:${c.key}`, phase: 'Critique', schema: FINDINGS, effort: EFFORT }).then((r) => r && ({ area: c.key, ...r }))))
const done = results.filter(Boolean)
const missing = CRITICS.filter((c, i) => !results[i]).map((c) => c.key)
if (missing.length) log(`No result from: ${missing.join(', ')}`)
log(`${done.reduce((n, r) => n + r.findings.length, 0)} findings from ${done.length} critics`)

const VERIFIED = { type: 'object', properties: {
  confirmed: { type: 'array', items: { type: 'object', properties: {
    page: { type: 'string' }, time: { type: 'string' }, severity: { type: 'string', enum: ['must fix', 'should fix', 'nice to have'] },
    what: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' }, from: { type: 'string' },
  }, required: ['page', 'time', 'severity', 'what', 'fix', 'evidence', 'from'] } },
  rejected: { type: 'array', items: { type: 'object', properties: { what: { type: 'string' }, reason: { type: 'string' } }, required: ['what', 'reason'] } },
  summary: { type: 'string' },
}, required: ['confirmed', 'rejected', 'summary'] }

phase('Verify')
const verdict = await agent(`${COMMON}

You are the skeptical final checker. Critics reviewed the chapter; their findings are below. For EACH finding, check it yourself (open the still, read the file and line, check the word times). Reject findings that are wrong, already fixed, pure taste with no cost to the viewer, or not worth their risk. Merge duplicates. Rank honestly: "must fix" only for something wrong, misleading, broken or unreadable that a viewer would notice; "should fix" for a clear improvement worth a small change; "nice to have" for the rest. Keep the smallest concrete fix (file and change). Then a plain-language summary.
${missing.length ? `No findings came back from: ${missing.join(', ')}.` : ''}
Findings:
${JSON.stringify(done, null, 1)}`, { label: 'verify', phase: 'Verify', schema: VERIFIED, effort: EFFORT })

return { critics: done, verdict }
