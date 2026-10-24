export const meta = {
  name: 'critique-chapter-2',
  description: 'Independent critique of chapter 2 (pictures, on-screen content, code), then adversarial verification and ranking of findings',
  phases: [
    { title: 'Critique', detail: 'three picture critics, two content critics, one code critic' },
    { title: 'Verify', detail: 'one skeptic re-checks every finding against the files and pictures, dedupes and ranks' },
  ],
}

const K = '/home/user/work/paper-pop-up-film-kit'
const S = '/home/user/work/chapter-2/stills'
const CH = '/home/user/Music/austerity-explainer/chapter-2-inflation'
const COMMON = `Context: you are reviewing chapter 2 ("What really causes inflation") of a narrated explainer film for a phone screen (1080 x 1920, 30 frames a second, 4 min 30 s), made for a non-programmer in New Zealand. The owner asked for visuals that are "cinematic, yet still carry the informational quality", mixing 2D motion graphics with 3D. Each of the ten pages is a 3D scene (painted rooms with depth, card models, paper cut-outs, lamp light, dust, focus blur, film grain) with flat documentary graphics on top; pages are joined by a page peel.
Key files (read what you need):
- Script with research ids: ${CH}/19 Script - chapter 2 - what really causes inflation.md
- Every word's time: /home/user/work/chapter-2/reference/page-words.txt
- Rules and the guide the page builders followed: ${CH}/19 Guide - building a cinema page.md (section 5 = strict on-screen rules)
- Research ledger (facts, sources; the end has a second fact check done today): ${CH}/18 Research - chapter 2 - what really causes inflation.md
- Page files: ${K}/paper-film/scenes/inflation-chapter-2/page-1.js ... page-10.js (and two-factories-set.js); shared code in ${K}/paper-film/scenes/ (cinema-kit.js, models.js, effects.js, graphics.js, cinema-chapter.js) and ${K}/paper-film/stage/cinema-stage.js
The film is being filmed right now in the background (do not stop it, do not edit any file). Finished stretches are in ${K}/paper-film/out/inflation-chapter-2-chunks/chunk-FROM-to-TO.mp4 (frame numbers; 30 frames a second from t = 0); you can pull a frame with: ffmpeg -hide_banner -loglevel error -y -ss SECONDS_INTO_CHUNK -i CHUNK.mp4 -frames:v 1 OUT.jpg (write only into /home/user/work/chapter-2/stills/critique/). Rendering new stills is possible but slows the filming: do it only if essential, at most 4 stills, with: cd ${K} && PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages /home/user/work/chapter-2/stills/critique/pN --stills T1 T2 (times separated by spaces).
Be a demanding, specific critic: name the page, the moment (seconds), what is wrong, why it matters to a viewer, and the smallest concrete fix. Do not pad with praise; but do not invent problems either — every finding needs evidence you actually saw or read. Do not edit any files.`

const SHEETS = {
  'pages 1-3': `Page 1 (0-20 s): ${S}/p1-c/sheet.jpg. Page 2 (20-42 s): ${S}/p2b/sheet.jpg and ${S}/p2d/sheet.jpg (after these, the last of the hundred dots was made nearly empty). Page 3 (42-74 s): ${S}/p3c/sheet.jpg and ${S}/p3d/sheet.jpg. Page turns: ${S}/joins-c/sheet.jpg. Already-filmed frames of page 1 and the start of page 2 are in the chunks folder.`,
  'pages 4-6': `Page 4 (74-95 s): ${S}/p4-j/sheet.jpg. Page 5 (95-128 s): ${S}/p5-d/sheet.jpg and ${S}/p5-r/sheet.jpg (banknotes were darkened to read as green after p5-d). Page 6 (128-155 s): ${S}/p6-d/sheet.jpg, ${S}/p6-e/still-151.90.jpg, ${S}/p6-r/still-148.40.jpg (a stray mark beside commas on the flip counter was fixed in p6-r).`,
  'pages 7-10': `Page 7 (155-180 s): ${S}/p7-c/sheet.jpg and ${S}/p7-r/sheet.jpg (price tags now hidden until they flip up). Page 8 (180-208 s): ${S}/p8-d/sheet.jpg, ${S}/p8-e/sheet.jpg, ${S}/p8-r/still-193.80.jpg (caption now LOWEST SINCE 1986). Page 9 (208-238 s): ${S}/p9-d/sheet.jpg, ${S}/p9-e/sheet.jpg, ${S}/p9-s/small.jpg (BANK OF ENGLAND label moved). Page 10 (238-270 s): ${S}/p10-d/sheet.jpg, ${S}/p10-r/sheet.jpg, ${S}/p10-s/small.jpg (the 1920s queue was replaced by a hundred-dot panel).`,
}

const FINDINGS = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'object', properties: {
      page: { type: 'string' }, time: { type: 'string' },
      category: { type: 'string', enum: ['clarity', 'legibility', 'composition', 'cinematic quality', 'consistency', 'accuracy', 'rules', 'timing', 'bug', 'other'] },
      severity: { type: 'string', enum: ['must fix', 'should fix', 'nice to have'] },
      what: { type: 'string' }, why: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string', description: 'which file/still/line you looked at' },
    }, required: ['page', 'time', 'category', 'severity', 'what', 'why', 'fix', 'evidence'] } },
    overall: { type: 'string', description: 'a short honest overall critique of your area' },
  },
  required: ['findings', 'overall'],
}

const CRITICS = [
  ...Object.entries(SHEETS).map(([pages, sheets]) => ({
    key: `pictures ${pages}`,
    prompt: `${COMMON}

Your area: the PICTURES of ${pages}, as a film director and an information designer. Look at every still (use the Read tool on the images; open single stills at full size when a detail matters). Pictures: ${sheets}
Judge: does each moment clearly show what Malina is saying at that moment (read the script and word times)? Is it cinematic (composition, light, depth, camera framing, focus) while staying informative? Are words readable, not clipped, not overlapping things, and out of the phone-button zones (bottom 380 px and right 140 px of 1080 x 1920)? Is anything confusing, cluttered, empty, ugly, anachronistic, or inconsistent with the rest of the chapter? Are there rendering faults (tearing, streaks, white blocks, stray marks, things floating or sinking wrongly)?`,
  })),
  { key: 'content pages 1-5', prompt: `${COMMON}

Your area: the ON-SCREEN CONTENT of pages 1 to 5. Read page-1.js to page-5.js and list every word, number and label they put on screen (draw2D strings, 3D words and cards via kit.word/kit.card, price tags, flip counters, dial scales) with its timing word. For each, check: (1) it is a short form of what Malina says at that moment (the script and word times), or plainly illustrative (example prices); (2) any number matches the research ledger and today's second fact check at the end of the ledger, and adds no claim she does not make; (3) the strict rules in the guide's section 5 (no MMT, no party, Mattei's views attributed to her, no portraits of real people, no capitals for emphasis inside sentences); (4) it appears while the matching words are said (not long before or after). Also check spelling and typography (quotes, % signs, ×, currency symbols, dates).` },
  { key: 'content pages 6-10', prompt: `${COMMON}

Your area: the ON-SCREEN CONTENT of pages 6 to 10. Read page-6.js to page-10.js (and two-factories-set.js) and list every word, number and label they put on screen (draw2D strings, 3D words and cards via kit.word/kit.card, price tags, flip counters, dial scales) with its timing word. For each, check: (1) it is a short form of what Malina says at that moment (the script and word times), or plainly illustrative; (2) any number matches the research ledger and today's second fact check at the end of the ledger, and adds no claim she does not make (watch page 10's interest-rate dial path 0.25 -> 5.5 -> 2.25 -> 2.75 and page 8's 3.2%); (3) the strict rules in the guide's section 5 (no MMT, no party, Mattei's views attributed to her, no portraits of real people, no capitals for emphasis inside sentences); (4) it appears while the matching words are said. Also check spelling and typography.` },
  { key: 'code', prompt: `${COMMON}

Your area: the CODE, looking for faults that would show in the filmed chapter. The film is drawn in separate stretches (each stretch starts in a fresh browser at its first frame, after drawing 3 warm-up frames just before it), so every page's pose(t) and draw2D(ctx, t) must give the same picture for a given t no matter what was drawn before. Check all ten page files, two-factories-set.js, cinema-kit.js, models.js, effects.js, graphics.js, cinema-chapter.js and cinema-stage.js for: state carried between frames (variables changed in pose and read later, caches that depend on order, Math.random or Date use, things that accumulate), camera keys out of time order, word lookups that hit the wrong occurrence of a repeated word (check each kit.at against page-words.txt), events timed outside the page's window (each page shows from about the previous page's last word + 0.3 s until its own last word + about 1.2 s), objects left visible after a cut within a page, canvas state leaking between pages (save/restore, transforms; note the stage now resets the overlay canvas for every page), and anything else that would make a stretch look different from the same moment drawn in one go. Cite file and line for each finding.` },
]

phase('Critique')
const results = await parallel(CRITICS.map((c) => () => agent(c.prompt, { label: `critique:${c.key}`, phase: 'Critique', schema: FINDINGS, effort: 'medium' }).then((r) => r && ({ area: c.key, ...r }))))
const done = results.filter(Boolean)
const missing = CRITICS.filter((c, i) => !results[i]).map((c) => c.key)
if (missing.length) log(`No result from: ${missing.join(', ')}`)
const total = done.reduce((n, r) => n + r.findings.length, 0)
log(`${total} findings from ${done.length} critics`)

const VERIFIED = {
  type: 'object',
  properties: {
    confirmed: { type: 'array', items: { type: 'object', properties: {
      page: { type: 'string' }, time: { type: 'string' }, severity: { type: 'string', enum: ['must fix', 'should fix', 'nice to have'] },
      what: { type: 'string' }, fix: { type: 'string' }, evidence: { type: 'string' }, from: { type: 'string', description: 'which critic(s)' },
    }, required: ['page', 'time', 'severity', 'what', 'fix', 'evidence', 'from'] } },
    rejected: { type: 'array', items: { type: 'object', properties: { what: { type: 'string' }, reason: { type: 'string' } }, required: ['what', 'reason'] } },
    summary: { type: 'string', description: 'plain-language overall verdict for a non-programmer: what is strong, what is weak, what should change before release' },
  },
  required: ['confirmed', 'rejected', 'summary'],
}

phase('Verify')
const verdict = await agent(`${COMMON}

You are the skeptical final checker. Six critics reviewed the chapter; their findings are below as JSON. For EACH finding, check it yourself against the evidence (open the still or frame, read the file and line, check the word times). Reject findings that are wrong, already fixed (see the notes about later fixes in the critics' brief: hundred dots, darkened banknotes, comma mark, hidden price tags, LOWEST SINCE 1986, moved bank label, page 10's dots panel, and the page-turn overlay fix), purely a matter of taste with no cost to the viewer, or not worth their risk this late. Merge duplicates. Re-rank severity honestly: "must fix" only for something wrong, misleading, broken, or unreadable that a viewer would notice; "should fix" for a clear improvement worth a small change; "nice to have" for the rest. For each confirmed finding keep the smallest concrete fix (which file, what to change). Then write a plain-language summary.
${missing.length ? `No findings came back from: ${missing.join(', ')}.` : ''}

Findings:
${JSON.stringify(done, null, 1)}`, { label: 'verify', phase: 'Verify', schema: VERIFIED, effort: 'medium' })

return { critics: done, verdict }
