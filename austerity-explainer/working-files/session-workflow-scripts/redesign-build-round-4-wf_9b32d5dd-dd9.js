export const meta = {
  name: 'redesign-build-round-4',
  description: 'Free building, round 4 of the chapter 2 redesign: fix round 3\'s findings on the Works (models, composition, plates) and pages 3 to 5, film again, and a fresh design critic',
  phases: [
    { title: 'Fix', detail: 'the Works set and plates; the pages and stage' },
    { title: 'Film', detail: 'pages 3 to 5 again' },
    { title: 'Critique', detail: 'a fresh design critic and skeptic' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign'
const PLAN = `${R}/chapter-2-inflation/34 Plan - chapter 2 full redesign - places, shots and order of work.md`

const CONTEXT = `
THE PROJECT: a narrated explainer film for a phone screen (1080 x 1920) about austerity, from Clara E. Mattei's The Capital Order
(2022). The user is not a programmer. Chapter 2 is being remade in full in the look the user kept in log 32 (the notice corner): real 3D
places built in Blender by script, drawn once (the plate), later repainted by Flux, and shone back onto the set in the film stage. Until
the paintings are approved, the plates stand in for them (free). THE STANDARD to reach is the notice corner (${R}/experiments/
"32 Notice corner - film frames at 1, 4.5 and 9.5 seconds.jpg" and "32 Notice corner - plate and painting.jpg"; ${K}/07 Composing a shot.md):
every strong thing points at the subject, story props touch as one group, the frame is full top to bottom, nothing reads as a model.
THE PLAN: ${PLAN} (part 1 "A. The Works", "People", part 2 pages 3 to 5, Traps). EARLIER ROUNDS: ${S}/round1-result.json, round2-result.json,
round3-result.json (round 3's reports: fixes, works, effects, pages; and checked.findings - THE LIST TO FIX THIS ROUND).
WHAT EXISTS: the Works assembly ${K}/paper-film/blender/inflation-chapter-2-newcomers/works/ (assemble_works.py, build_works.sh,
build_factories.py, build_far_town.py, works_kit.py with the stripe fix, make_works_continuity_sheet.py); the export and plates in
${K}/assets/models/inflation-chapter-2-newcomers/works/; the pages ${K}/paper-film/scenes/inflation-chapter-2-newcomers/page-3.js, page-4.js,
page-5.js and works-effects.js; make_state_picture.py and make_behind_picture.py in ${K}/paper-film/tools/; the stage ${K}/paper-film/stage/
cinema-stage.js; the shot checker ${K}/paper-film/tools/check-shot.sh with the Works' check files; the chapter scene
${K}/paper-film/scenes/inflation-chapter-2-newcomers.js on the estimated timeline.
TOOLS: Blender 5.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (-b, DISPLAY=:96; start Xvfb :96 if none runs); the film
stage node ${K}/paper-film/tools/render-paper-film.mjs from ${K} (never set PAPER_FILM_BROWSER); film-chapter-parallel.sh (PIECE_FRAMES=240);
find_jumps.py one piece at a time; camera_audit.py.
HARD RULES: spend no money (no fal, no ElevenLabs); never change the kept notice corner's files (${K}/assets/models/pit-village/
notice-corner-*, street.blend, street.glb, camera.json, the pit village props and index.json) and prove its stills unchanged after any shared
change; a plain note at the top of every file, full plain-word names, the existing style; every sign with real lettering, no digit on set
dressing except "No. 1" and "No. 2", no logos, brands, party or chain colours; words on screen only short forms of the narration; never MMT;
cameras never turn. Repository files under 90 MB, no .blend1; keep above 4 GB free disk. One render at a time; the other helper may be
rendering too. Do not commit. Report in plain everyday words.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, tested: { type: 'string' },
  not_done_or_unsure: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'files', 'tested', 'not_done_or_unsure', 'pictures'] }

const SET_FIXES = `YOUR TASK: the Works set, its composition and its plates (round 3's findings about models and views):
- rebuild both factories and the far town with the stripe fix (build_factories.py, build_far_town.py), and measure that no brick surface is
  striped any more;
- the "machines" in both lit doorways read as a bar chart: model real machines (for example a lathe or loom with a flywheel, belts up to a
  line shaft, different outlines), or a plain lit room with hanging belts and the crates in front;
- No. 2's gable over its gate: a row of lit mill windows (a window group) instead of the blank loft door, so "flat out" and the flicker show in W2;
- the gasholder: never a "tank" on No. 1's side; push it far back, paler and hazier, or out of W3, so No. 1's round chimney is the biggest
  thing on the left;
- W3's queue: the 7 men in single file down the left pavement toward the camera with clear gaps (about 1.1 to 1.3 m) so each shows on his
  own, the tail reaching about 0.70 to 0.75 down; the handcart onto the right pavement nearer the camera, into the bottom third (rule 7);
- the PETROL and DIESEL drums: clear of the house fronts' line, both whole words facing the camera in W1 and W2 (add them to must_read);
- No. 1's shut, chained gate visible in W1: a faint cool light in No. 1's yard behind it so the bars show as a silhouette (the doorway stays
  dark until "go"), the chain where it shows;
- W4: the dividing wall's No. 2 face in No. 2's buff brick; look at the cap;
- the stooped man's head turned or lowered into shadow, and him about 0.1 m off the drum;
- also look hard at W1 and W2 against the standard: the near house walls fill much of each side and the bottom half is bare paving. Use the
  composing rules (quiet side not empty, story group touching, columns top to bottom, nothing big and dark bottom left) and the shot checker
  to make each frame fuller and more composed without turning the camera or breaking the plan;
- then redraw all plates (read each render log), re-run the shot checker on every view (W1, W2, W3, W4), remake the state pictures and the
  behind picture, export, and draw the continuity sheet. Keep the file and object names the pages read.`

const PAGE_FIXES = `YOUR TASK: the pages and the stage (round 3's findings about words, timing and the stage):
- page 5: NO SPARE must not overlap the fading question (end the question before it starts); "→ PRICES UP" in on "prices" with the arrow so it
  is up about 1.2 s or more; the rule-card heading (MOST ECONOMISTS AGREE) down to about 0.06 or lower;
- words that fade one frame before a cut: end them exactly on the cut;
- the BANK sign's lettering and board dim until page 9 (works-effects.js; its own surface bank-sign-lettering), then brighten with the bank window;
- No. 2's smoke must show under the words in W2 (a plume that lies lower and thicker, crossing about 0.10 to 0.25 down) and No. 1's smoke
  after "start" in W1;
- the page peel's first frame darkening the old page about 11% (cinema-stage.js): bring the sheet's shading in over the first frames; then
  prove the notice corner's stills unchanged and an old chapter 2 page turn otherwise unchanged;
- draw stills of the states not yet tried on the real set (the go=swing fallback, the W2 tag changing to THE FLAT-OUT FACTORY SLOWS and its
  right edge, the slowed state with 8 men, the W4 silhouettes, the bank window lit) and fix what is wrong.
Coordinate with the set helper only through file names: do not edit assemble_works.py or the Blender scripts.`

const FILM = `YOUR TASK: film pages 3 to 5 again on the fixed set, plates and pages (switch any file names that changed), from start to end
(estimated timeline), and check: stills at every event and the first, middle and last frame of each slide; the jump finder piece by piece
(every jump planned); the camera audit (no turn); every word on screen against the narration; the seconds a frame. Make a one-frame-a-second
contact sheet of the film and put it with the film in your scratch folder.
NOTE: a first filming helper started this (its notes are in ${S}/round4-film: moments.json, words-check.txt, camera/, smoke/, tools/) and was
cut off when the computer restarted: no programs from before are running now (start Xvfb :96 again; nothing else is waiting). Reuse what it
left that is still right, check it rather than trust it, and film the whole of pages 3 to 5 again from the start.`

phase('Fix')
const [set, pageFixes] = await parallel([
  () => agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round4-set (create it).\n\n${SET_FIXES}`, { label: 'fix:set-and-plates', phase: 'Fix', schema: REPORT }),
  () => agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round4-pages (create it).\n\n${PAGE_FIXES}`, { label: 'fix:pages-and-stage', phase: 'Fix', schema: REPORT }),
])

phase('Film')
const film = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round4-film (create it).\n\nWhat the two fixers reported:\n${JSON.stringify({ set, pageFixes }, null, 1)}\n\n${FILM}`,
  { label: 'film:pages-3-to-5', phase: 'Film', schema: REPORT })

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['where', 'problem', 'fix', 'severity'] } },
}, required: ['summary', 'findings'] }

phase('Critique')
const critique = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-4 (create it).\n\nThe reports:\n${JSON.stringify({ set, pageFixes, film }, null, 1)}

YOUR TASK: you are a film designer who has not seen this work before, and a skeptic. First look at the notice corner pictures named above
(the standard the user loved). Then watch the new film of pages 3 to 5 (and its contact sheet) and open the plates of W1, W2, W3, W4 at full
size and at phone size. Judge honestly against that standard: composition (does everything strong point at the subject? is the frame full
top to bottom? do story props touch as one group?), light, whether anything reads as a toy or a model, whether a newcomer understands each
page from the pictures (two different factories; men waiting, then gone; the flat-out factory with nobody waiting; the rule). Also verify
the fixers' claims (stripes gone, machines read as machines, words timing, no overlaps, the bank dim, smoke visible, the peel pop gone, the
kept notice corner unchanged). Report every real problem with a concrete fix, worst first.`, { label: 'critique:design-and-skeptic', phase: 'Critique', schema: FINDINGS })

return { set, pageFixes, film, critique }
