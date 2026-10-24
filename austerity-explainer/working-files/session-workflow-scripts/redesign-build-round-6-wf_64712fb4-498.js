export const meta = {
  name: 'redesign-build-round-6',
  description: 'Round 6 of the chapter 2 redesign: fix round 5\'s critics on the Works, pages 3 to 5 and the checkout, apply the people test lessons, film again, fresh critics',
  phases: [
    { title: 'Fix', detail: 'Works W1-W3 set; pages and effects; the checkout' },
    { title: 'Film and W4', detail: 'pages 3 to 5 again; W4 and the plan notes' },
    { title: 'Critique', detail: 'fresh critics for the Works and the checkout' },
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
the paintings are approved, the plates stand in for them (free). THE STANDARD is the notice corner (${R}/experiments/"32 Notice corner -
film frames at 1, 4.5 and 9.5 seconds.jpg" and "32 Notice corner - plate and painting.jpg"; ${K}/07 Composing a shot.md): every strong
thing points at the subject, story props touch as one group, the frame is full top to bottom (the story reaches well into the lower half),
the subject is the brightest thing, nothing reads as a model or a toy, lettering always shows whole words.
THE PLAN: ${PLAN}. EARLIER ROUNDS: ${S}/round1-result.json to round5-result.json. Round 5's result holds every helper's report and two
fresh critics' numbered findings: "critique" (the Works and pages 3 to 5, 15 findings) and "checkoutCritique" (the checkout C1, 12
findings): THE LIST FOR THIS ROUND.
THE PEOPLE TEST (painted on 16 October; ${K}/assets/models/inflation-chapter-2-newcomers/people-test/people-test-paintings.json and
${R}/chapter-2-inflation/"34 Full redesign - working files"/people-test/; lessons 135 to 138 in ${R}/project-notes/Lessons.md) TAUGHT:
painted figures work; dark own-surface silhouettes read as shadow puppets (drop them); asked to remove the people, the painter LEFT THEIR
LONG SHADOWS, so plates must be drawn with the figures casting no long shadows (only a small soft shadow under each figure's feet), which
also keeps the state picture's mask small; the painter painted the men paler, so keep them dark with a little rim light; the painter
lifts a faint glow inside a hollow (the drum's top) into a bright band, so darken such glows in the plate; a time cut where only the
people change reads as them blinking out, so something else must change with them (they appear inside; the fire burns lower).
WHAT EXISTS: the Works ${K}/paper-film/blender/inflation-chapter-2-newcomers/works/ (assemble_works.py, build_factories.py, ...), the
export, plates and works-shot.json in ${K}/assets/models/inflation-chapter-2-newcomers/works/; the pages ${K}/paper-film/scenes/
inflation-chapter-2-newcomers/ (page-3.js, page-4.js, page-5.js, works-effects.js, works-states-test.js), graphics.js; the checkout
${K}/paper-film/blender/inflation-chapter-2-newcomers/checkout/ and ${K}/assets/models/inflation-chapter-2-newcomers/checkout/ and its check
file ${K}/examples/inflation-chapter-2-newcomers/checkout-c1-shot-check.json; tools make_state_picture.py, make_behind_picture.py,
check-shot.sh in ${K}/paper-film/tools; helpers' tools in ${S}/round5-*/tools and ${S}/check-round-5*/tools.
TOOLS: Blender 5.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (-b, DISPLAY=:96; start Xvfb :96 if none runs); the film
stage ${K}/paper-film/tools/render-paper-film.mjs from ${K} (never set PAPER_FILM_BROWSER); film-chapter-parallel.sh (PIECE_FRAMES=240);
find_jumps.py one piece at a time; camera_audit.py. 4 processors shared with other helpers: one render of your own at a time.
HARD RULES: spend no money; never change the kept notice corner's files (${K}/assets/models/pit-village/notice-corner-*, street.blend,
street.glb, camera.json, the pit village props and index.json) and prove its stills unchanged after any shared change; figures never nearer
than 6 m to any camera place (so the painter has no faces to paint); a plain note at the top of every file, full plain-word names, the
existing style; every sign with whole words in view, no digit on set dressing except "No. 1" and "No. 2", no logos, brands, party or chain
colours; words on screen only short forms of the narration; never MMT; cameras never turn. Repository files under 90 MB, no .blend1; keep
above 4 GB free disk (delete your own frame dumps and big scratch once checked). Stop processes only by their own process number. Another
team is building plugin tools in /home/user/Music/plugins: do not touch that folder. Do not commit (the lead commits). Report in plain
everyday words: what you changed, what you measured, what you did not do or are unsure of.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, tested: { type: 'string' },
  not_done_or_unsure: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'files', 'tested', 'not_done_or_unsure', 'pictures'] }

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['where', 'problem', 'fix', 'severity'] } },
}, required: ['summary', 'findings'] }

const SET = `YOUR TASK: the Works set for W1, W2 and W3 (you own assemble_works.py, build_factories.py and the figures; the pages helper owns
the page files, works-effects.js and graphics.js at the same time, so coordinate only through works-shot.json names). Fix round 5's Works
critique findings 1 (the plate and state picture half: a W3 "No. 1 working" plate - men gone, gate and cart doors open, windows lit, its
chimney's smoke is the pages helper's - and its state picture with a mask kept small; write its file names into works-shot.json under
states), 3 (No. 2's workers visible in W3), 4 (a near layer so the story reaches lower: props such as the drums and lantern may come nearer,
figures stay at least 6 m from every camera place; aim for the story to fill to about 0.80 down in W1 and W2 and a fuller bottom third in
W3), 6 (the men's rim light visible: behind them at shoulder height, grazing their outlines, a 2 to 4 pixel edge), 7 ("start" must not
floodlight the empty paving: shorten the gateway lights' reach; keep the working state's mask as small as you can), 11 (No. 2's crate
stencils readable or turned; the handcart's crate), 12 (the gutter's stepped ridges smoothed for the Works' lane only; close the pop-up
crates' gap), 14 (No. 1's cart doors mid-brown timber). AND THE PEOPLE TEST'S LESSONS in every plate: the figures (waiting men, workers
inside, No. 2's men) cast no long shadows, only a small soft shadow under each figure's feet; the men stay dark with the rim light; the
drum's and brazier's inner glow darkened so no bright band can be painted. Then redraw every affected plate (read each render log for shadow
faults), remake the state pictures (measure each mask's share of the frame: report them) and the behind picture, export, re-run the shot
checker on W1, W1 working, W2, W2 slowed and W3, draw the continuity sheet and a before/after sheet at phone size. Keep every key and object
name the pages read; list in your report everything that moved for the pages helper. W4 is NOT yours (another helper fixes it after you).`

const PAGES = `YOUR TASK: the pages and live effects (you own page-3.js, page-4.js, page-5.js, works-effects.js, graphics.js; the set helper is
redrawing the plates at the same time and will add a W3 "No. 1 working" state picture to works-shot.json under states; read facts from the
file, never hard-code positions). Fix round 5's Works critique findings 1 (the pages half: on "made" in page 5, cut W3 to the No. 1
working state picture and start No. 1's working smoke where the rule cards don't hide it, so the line lands on a factory at work; use the
plate when the set helper's file is not there yet, and switch when it appears), 2 (both PRICES arrows placed from the boards' places on
screen, kept at least 24 pixels clear of the boards; add a check), 5 (the drum stencils dimmed so the letters sit below the gate board's;
the gate lamp's glow cut in W1), 8 ("busy" must read as busier: a warm pulse brightening 15 to 25 levels three times in 2 s, no dark
band, a few sparks at the lathe), 10 (MACHINES over No. 2's own column, WORKERS' line not a bracket), the BANK half of 11 (dim to about
0.07 until page 9), 12 (fringe about 0.002 in the pages' LOOK; not a shared change), 13 (the brazier smoke on the same WIND as the
chimneys; No. 2's plume fades out by about 0.50 across in W3; W2's "flat out" carried by the busy burst and the workers). AND THE PEOPLE
TEST'S LESSON for the time cut on "go": the fire burns lower after the cut (smaller flames, less glow), so the change reads as time
passing; check it in stills either side of the cut. Then wait until the set helper's new plates and export exist (look at works-shot.json
and the plate dates; poll every few minutes and do useful work meanwhile; give up after 3 hours and say so) and draw stills of every
changed moment on the new set. Prove the notice corner's stills unchanged after any change to graphics.js or the stage.`

const CHECKOUT = `YOUR TASK: fix the checkout view C1 (you own the checkout's folders and its check file). Fix every finding in round 5's
"checkoutCritique" (12 findings, worst first: the top 40% a black void - a dim ceiling with structure leading to the vanishing point;
the bright empty belt - light the basket, not the counter, belt rubber near-black; the story reaching too little of the lower frame - the
eye at 1.70 m and the critic's worked-out spots; the divider tray out of view and named in the check file; the petrol canopy far, small
and dim with glass cues, and one plain supermarket cue on the quiet side; the groceries modelled so they don't read as toys - bread in a
kraft paper bag, butter and cheese different sizes and wrappers, a grey divider; no grey slab in the title band; the slide's start frame
passing (it is also the chapter's last held picture); the masthead letters bigger; the shelf packs plain; the card terminal and till;
the props index sizes and the crate's export colour). Fill the basket so a hundred dollars is believable (plan section B). Then redraw the
plate and the behind plate, export, re-run the shot checker at the composed spot and the slide's start until both pass or every remaining
problem is explained, draw the stage stills (start, middle, end, weights), and a phone-size sheet beside the notice corner.`

const W4 = `YOUR TASK: W4 (page 14) and the plan's notes. Fix round 5's Works critique finding 9 (the jacket hung by its collar loop with sloping
shoulders and free sleeves, one over the crate's edge; the cap's peak toward the camera; WAGES a brown pay envelope in dark ink, tucked in the
pocket or leaning, not a placard; the crate not a plinth) in assemble_works.py (the set helper has finished with it: read its report below
and keep everything it did), apply the people test's lessons (no long shadows from the men; W4's men are painted figures now, not
own-surface silhouettes, since silhouettes read as shadow puppets: update the export and works-effects.js's W4 handling only if the set
helper's report shows the pages helper is done with that file, otherwise list exactly what the pages must change), redraw W4's plate, check
it, and draw it in the stage. Then add to the plan ${PLAN} a short plain section "Changes since the plan (rounds 3 to 6)" recording the
camera spots, the crowd, the drums, the workers inside, the handcart, W4's spot, the people test's lessons and the checkout's changes, so
the plan matches what is built.`

const FILM = `YOUR TASK: film pages 3 to 5 again on the fixed set, plates and pages, from start to end (estimated timeline), and check: stills at
every event and the first, middle and last frame of each slide; the jump finder piece by piece (every jump planned); the camera audit (no
turn); every word on screen against the narration; the seconds a frame. Move the chunks out of paper-film/out into your scratch folder,
make a one-frame-a-second contact sheet and phone-size still sheets, delete the chunks once joined and checked. Fix nothing yourself; list
every problem you see, worst first.`

phase('Fix')
const setP = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round6-set (create it).\n\n${SET}`, { label: 'fix:works-set', phase: 'Fix', schema: REPORT })
const pagesP = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round6-pages (create it).\n\n${PAGES}`, { label: 'fix:pages-and-effects', phase: 'Fix', schema: REPORT })
const checkoutP = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round6-checkout (create it).\n\n${CHECKOUT}`, { label: 'fix:checkout', phase: 'Fix', schema: REPORT })

const checkoutChain = checkoutP.then(checkout => agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-6-checkout (create it).\n\nThe fixer's report:\n${JSON.stringify(checkout, null, 1)}
YOUR TASK: you are a film designer who has not seen this work before, and a skeptic. Look at the notice corner pictures first. Then judge
the checkout view C1 (the plate at full size and phone size, the stage stills, the checker reports) against that standard and the plan's
part 1 section B and pages 1, 15 and 16. Go through round 5's 12 checkout findings one by one and say whether each is fixed (measure it).
Would a newcomer read "a supermarket checkout, a full basket, a newspaper warning that prices will go up" in two seconds? Report every real
problem left with a concrete fix, worst first.`, { label: 'critique:checkout', phase: 'Critique', schema: FINDINGS }).then(critique => ({ checkout, critique })))

const [set, pages] = await Promise.all([setP, pagesP])

phase('Film and W4')
const w4P = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round6-w4 (create it).\n\nThe set helper's report:\n${JSON.stringify(set, null, 1)}\n\nThe pages helper's report:\n${JSON.stringify(pages, null, 1)}\n\n${W4}`, { label: 'fix:w4-and-plan', phase: 'Film and W4', schema: REPORT })
const film = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round6-film (create it).\n\nWhat the two fixers reported:\n${JSON.stringify({ set, pages }, null, 1)}\n\n${FILM}`,
  { label: 'film:pages-3-to-5', phase: 'Film and W4', schema: REPORT })
const w4 = await w4P

phase('Critique')
const critique = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-6 (create it).\n\nThe reports:\n${JSON.stringify({ set, pages, film, w4 }, null, 1)}

YOUR TASK: you are a film designer who has not seen this work before, and a skeptic. First look at the notice corner pictures (the standard
the user loved). Then watch the new film of pages 3 to 5 (and its contact sheet) and open the plates of W1, W2, W3, W4 at full size and at
phone size. Judge honestly against that standard: composition, light, anything that reads as a toy or a model, and whether a newcomer
understands each page from the pictures (two different factories; men waiting, then gone and seen working inside; the flat-out factory busy
with nobody waiting; the rule landing on a factory at work). Go through round 5's 15 Works findings one by one and say whether each is now
fixed (measure it). Check the people test's lessons are in the plates (no long shadows from figures; the glow in the drum; the fire lower
after "go"). Verify the fixers' claims and that the kept notice corner is unchanged. Report every real problem left with a concrete fix, worst
first.`, { label: 'critique:works', phase: 'Critique', schema: FINDINGS })

const checkoutResult = await checkoutChain
return { set, pages, film, w4, critique, checkout: checkoutResult.checkout, checkoutCritique: checkoutResult.critique }
