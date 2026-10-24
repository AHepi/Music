export const meta = {
  name: 'redesign-build-round-3',
  description: 'Free building, round 3 of the chapter 2 redesign: round 2 fixes; assemble the Works and compose its four views with plates; the Works effects and pages 3 to 5 filmed with the plates standing in for paintings',
  phases: [
    { title: 'Build', detail: 'fixes then the Works assembled and composed; the Works effects and page code' },
    { title: 'Pages', detail: 'pages 3 to 5 on the plates, filmed' },
    { title: 'Check', detail: 'a fresh skeptic' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign'
const PLAN = `${R}/chapter-2-inflation/34 Plan - chapter 2 full redesign - places, shots and order of work.md`
const SHOTS = `${R}/chapter-2-inflation/34 Full redesign - working files/design/shots.json`

const CONTEXT = `
THE PROJECT: a narrated explainer film for a phone screen (1080 x 1920) about austerity, from Clara E. Mattei's The Capital Order
(2022). The user is not a programmer. Chapter 2 is being remade in full in the look the user kept in log 32: real 3D places built
in Blender by script, drawn once (the plate), repainted by Flux on fal, and the painting shone back onto the set in the film stage.
Until the paintings are approved, every plate STANDS IN for its painting (free), so everything can be built, filmed and checked now.
THE PRODUCTION PLAN: ${PLAN} - read "People", part 1 "A. The Works" (layout, fixed looks, states, views W1 to W4, props), part 2 for
pages 3, 4 and 5, "How the two factories stay the same", the Traps. The shot list: ${SHOTS}.
EARLIER ROUNDS (what exists, and skeptics' findings): ${S}/round1-result.json and ${S}/round2-result.json (JSON: built/props_fixes/
factories/figures reports with files and pictures; checked.findings).
WHAT EXISTS: factories and far town in ${K}/assets/models/inflation-chapter-2-newcomers/works/ (index.json with markers: chimney tops,
tank, doorways, window groups; scripts in ${K}/paper-film/blender/inflation-chapter-2-newcomers/works/, works_kit.set_windows/set_doorway);
props in .../inflation-chapter-2-newcomers/props/ (gate boards No. 1 and No. 2, BANK sign and plate, PETROL and DIESEL drums, crates,
chain and padlock, lunch tin, jacket and cap, mug, WAGES envelope, hand truck); figures in .../figures/ (five waiting poses, six walkers);
the pit village props (iron gates pair, brazier drum, hurricane lantern, gas lamps, handcart, dustbins...) in ${K}/assets/models/pit-village/props/;
the street builder build_street.py (now with --out --name --colliery --carriageway --pavement --length --slope --behind --cottages
--replace) and set_dressing.py (place_prop(..., folder=), export_for_film(..., folder=REQUIRED)); the people test
(${K}/paper-film/blender/pit-village/assemble_people_test.py, ${K}/paper-film/scenes/people-test.js) as the pattern for figures, plates,
helper plates and state pictures (${K}/paper-film/tools/make_state_picture.py); the kept shot's pattern
(assemble_notice_corner.py, notice-corner.js, projected-set.js with setPainting/blendTo/setView, pit-village-effects.js, cinema-kit.js
kit.moving and held shots, graphics.js with titles, labels, counters, bars, line charts and dotPanel); the shot checker
(${K}/paper-film/tools/check-shot.sh, ${K}/07 Composing a shot.md); the chapter scene ${K}/paper-film/scenes/inflation-chapter-2-newcomers.js
(lazy; stand-in pages in inflation-chapter-2-newcomers/placeholder.js; each real page module must EXPORT its join) on the estimated timeline
${K}/examples/inflation-chapter-2-newcomers/timeline-estimated.json (page 4 is followed by a 4-second guess pause, page 5 by a 3.5-second rule
pause in that timeline). The narration words: ${R}/chapter-2-inflation/33 Narration script - chapter 2 for newcomers.json.
TOOLS: Blender 5.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (-b, DISPLAY=:96; start Xvfb :96 if none runs). The
film stage: node ${K}/paper-film/tools/render-paper-film.mjs from ${K} (never set PAPER_FILM_BROWSER); filming whole stretches:
${K}/paper-film/tools/film-chapter-parallel.sh (PIECE_FRAMES=240 for lazy chapters). The jump finder ${K}/paper-film/tools/find_jumps.py
(run it on one piece at a time). Python with numpy, opencv, Pillow; -I for Python reading downloaded files.
HARD RULES:
- Spend no money: never call fal, ElevenLabs or any paid service.
- NEVER change the kept notice corner's files (${K}/assets/models/pit-village/notice-corner-*, street.blend, street.glb, camera.json, the pit
  village props and index.json). If you change a shared script, prove the notice corner's preview unchanged (assemble_notice_corner.py --preview).
- Every new or changed file: a plain note at the top; full plain-word names; the existing style. Every sign carries real lettering; no
  digit on any set dressing except "No. 1" and "No. 2"; no logos, brands, flags, party or chain colours. Words on screen are short forms of
  the narration, never a figure Malina doesn't say. Never write MMT. A camera never turns during a move; held shots stay still.
- Keep work in the repository's film kit; scratch and big test pictures in ${S}/<your folder>. No file in the repository over 90 MB; no
  .blend1. Keep above 4 GB free disk (df -h /).
- Another helper works at the same time and may run Blender or the stage: keep previews small, one render at a time.
- Do not commit to git. Report in plain everyday words.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, tested: { type: 'string' },
  not_done_or_unsure: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'files', 'tested', 'not_done_or_unsure', 'pictures'] }

const FIXES = `YOUR TASK (do it first, briefly): round 2's should-fix and minor findings (${S}/round2-result.json, checked.findings), except
the W1/W2 camera places (the next helper settles those with the shot checker). Specifically: No. 2's chimneys paler buff, with a warm lit
side, so from street level they stay pale against the dusk and never read as No. 1's; the two right-hand men's coats a dull grey-brown or
olive-brown that stays brown (not red) after the film's grade (film one still and sample the colour); the figures less toy-like (deeper coat
folds and elbow and back creases, a broken hem line, smaller boots, hands bent round the bar or cuff, the two profile heads turned 15 to 20
degrees away from the light); the WAGES envelope as a prop standing up against the mug, facing forward; the jacket with a collar and
slumped shoulders and the cap tilted with its peak in profile; the lunch tin with real dents, a rolled lid rim, a wire hinge, worn edges;
the BANK hanging sign's letters about 0.3 m; make_state_picture.py writing lossless pictures and printing the largest difference from the
main painting outside the mask; the far town raised or moved so the gasholder and spire show clear of the roofs in W3; short names
renamed. Rebuild what changes, redraw the contact sheets, look at them at full size.`

const WORKS = `YOUR TASK: assemble "The Works" and compose its four views (plan part 1 "A. The Works", "People", findings T1, T2, T8,
T15; round 2's findings on the W1/W2 camera places, the yard setts showing the ground through, the bank sign's size). A new assemble
script (for example ${K}/paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py) that builds into its own folder
(${K}/assets/models/inflation-chapter-2-newcomers/works/): the short cobbled lane with terraces and gas lamps (build_street.py with
settings), the cross street and the end house whose upstairs window is W3's camera, the works wall with two gate arches and copings, the
piers, the dividing wall, the two iron gates (OWN SURFACES, never in a plate: their leaves are separate objects the film can swing), the
gate boards, the bank with its barred window (own glass, a shallow lit room) and hanging sign, the PETROL and DIESEL drums at both piers,
crates, the handcart, the brazier and lantern at No. 1, the queue of seven men at No. 1 (figures, backs to the camera, at least 6 m away),
the eight men for No. 2's slowed state, the inside-the-yard props for W4 (jacket and cap, crate, mug, WAGES envelope), the factories and
the far town, with the yard ground level under the setts. Four named cameras: W3 (upstairs window, both gates), W1 (No. 1's gate), W2
(No. 2's gate, the mirror of W1), W4 (inside No. 2's yard looking out). For each view: a check file for the shot checker, then compose
until it passes the main rule (where the lines meet, the brightest parts, the warm light and the story group on the subject) or say why
not; settle W1 and W2's camera places by comparing the checker's results (mid-pavement against gates moved toward the lane, as round 2
suggested). Then draw the plates (1536 x 2730 EEVEE, read each render log for shadow faults): W3; W1 main (quiet: men, windows dark) and
W1's working helper plate (men gone, windows lit); W2 flat out and W2's slowed helper plate (8 men, two thirds of the windows dark); W4
(no men, no gate leaves). Export the set for the film (split into parts under 90 MB each: lane and terraces; factories; town; props and
figures; own surfaces) with each view's camera json and a shot json of where things are (gate hinge positions, chimney tops, brazier,
lantern, drums, bank window, the men). Draw a continuity sheet: one preview of each view side by side; check No. 1 is always left, the
chimneys and boards consistent, the men's count right.`

const EFFECTS = `YOUR TASK: the Works' moving things and the page code for pages 3, 4 and 5 (plan part 2, pages 3 to 5; "How the two
factories stay the same" point 8; findings T9, T13, T16; the shot list ${SHOTS} shots 3a, 3b, 4a, 5a, 5b).
1. A shared module ${K}/paper-film/scenes/inflation-chapter-2-newcomers/works-effects.js: the four states (No. 1 quiet, No. 1 working,
   No. 2 flat out, No. 2 slowed) and their settings in one place, with fixed seeds: chimney smoke from the chimney-top markers (heavy from
   both of No. 2's, thin from one when slowed, none from No. 1 until "start"), the brazier's flames and glow and the lantern's flicker at
   No. 1, No. 2's window flicker, the gate leaves as own surfaces that can swing (moving things during a swing, part of the set when still),
   the bank window lighting, windows changing in steps (a held-set redraw per step, not per frame). Mark moving things with kit.moving so
   held shots stay fast; give each page's pose a still key that changes only when the set changes.
2. Page files ${K}/paper-film/scenes/inflation-chapter-2-newcomers/page-3.js, page-4.js, page-5.js, exactly following the plan's shots,
   events on spoken words (kit.at('word', n)), words on screen (graphics.js: plain heavy type in the top band, left of 0.90 across; the rule
   cards stacked over a soft dark band; the guess ring; tags QUIET and FLAT OUT), the one slide per page that never turns and stops on the
   composed frame, the time cut on "go" to the state picture (men gone; made with make_state_picture.py from the plates), the windows
   lighting on "start", crates popping up on "things", the 4-second guess hold on page 4 and the run-on into page 5 with no join, the
   2-second hold on the rule cards. Each page exports its join. Use the PLATES as stand-ins for the paintings (a setting at the top of each
   page names the picture used, so the paintings drop in later), and setView for two views of one place on a page.
   Until the Works assembly exists (the other helper builds it at the same time), develop against the factories and a stand-in wall; switch
   to the real export as soon as it appears (look for it in ${K}/assets/models/inflation-chapter-2-newcomers/works/ and its camera json files).
3. Wire pages 3 to 5 into ${K}/paper-film/scenes/inflation-chapter-2-newcomers.js (the rest stay stand-ins).`

const PAGES = `YOUR TASK: finish and film pages 3, 4 and 5 on the real Works export with the plates standing in, and check them.
Make sure pages 3 to 5 use the final assembled set, cameras and plates (switch from any stand-in), make the state pictures, then draw
stills at every event on those pages (read the page files for the moments) and the first, middle and last frames of each slide, and film
pages 3 to 5 (about 75 seconds of the estimated timeline: use render-paper-film.mjs --frames on the stretch, or film-chapter-parallel.sh
with FILM_FROM/FILM_TO). Measure the seconds a frame on held, effect and sliding frames. Run the jump finder piece by piece; every jump
must be a planned cut. Check the camera never turns (paper-film/tools/camera_audit.py). Check every word on screen against the narration.
Look at the stills at phone size and judge honestly: does a newcomer see two factories, the quiet one with men waiting, the men going in,
the flat-out one with nobody waiting? Fix what you can; report the rest.`

phase('Build')
const [fixesAndWorks, effects] = await parallel([
  async () => {
    const fixes = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round3-fixes (create it).\n\n${FIXES}`, { label: 'build:round-2-fixes', phase: 'Build', schema: REPORT })
    const works = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round3-works (create it).\n\n${WORKS}`, { label: 'build:the-works', phase: 'Build', schema: REPORT })
    return { fixes, works }
  },
  () => agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round3-effects (create it).\n\n${EFFECTS}`, { label: 'build:effects-and-pages', phase: 'Build', schema: REPORT }),
])

phase('Pages')
const pages = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round3-pages (create it).\n\nWhat the builders reported:
### the Works\n${JSON.stringify(fixesAndWorks?.works, null, 1)}\n### effects and page code\n${JSON.stringify(effects, null, 1)}\n\n${PAGES}`,
  { label: 'pages:3-to-5', phase: 'Pages', schema: REPORT })

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['where', 'problem', 'fix', 'severity'] } },
}, required: ['summary', 'findings'] }

phase('Check')
const checked = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-3 (create it).\n\nThe helpers' reports:
${JSON.stringify({ fixes: fixesAndWorks?.fixes, works: fixesAndWorks?.works, effects, pages }, null, 1)}

YOUR TASK: be a skeptic, as a first-time viewer and as a careful checker. Watch the filmed pages 3 to 5 frame by frame where it matters and
open every still at full size and at phone size. Check: a newcomer sees two different factories and which is which; the men read as people
waiting, then gone, with no ghost or shadow left; the flat-out factory has nobody waiting; the words on screen match the narration and sit
in the top band, readable, left of 0.90; no figure on screen Malina doesn't say; the slides never turn and stop on the composed frames;
every jump is planned; the four views are consistent (No. 1 always left; chimneys, boards, men's count); the shot checker's main rule holds
on each view; the kept notice corner's files are unchanged (git status under assets/models/pit-village); file sizes under 90 MB; the speed of
each kind of frame. Report every real problem with its fix.`, { label: 'check:skeptic', phase: 'Check', schema: FINDINGS })

return { fixes: fixesAndWorks?.fixes, works: fixesAndWorks?.works, effects, pages, checked }
