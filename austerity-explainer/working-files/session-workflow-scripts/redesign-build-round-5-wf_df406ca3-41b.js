export const meta = {
  name: 'redesign-build-round-5',
  description: 'Round 5 of the chapter 2 redesign: fix round 4\'s critic findings on the Works and pages 3 to 5, film again, fix W4; build the checkout (C1) as the next place; fresh critics for both',
  phases: [
    { title: 'Fix and build', detail: 'Works W1-W3 set; pages and effects; the checkout C1' },
    { title: 'Film and W4', detail: 'pages 3 to 5 again; W4 and page 12 state picture' },
    { title: 'Critique', detail: 'fresh critics for the Works film, W4 and the checkout' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign'
const PLAN = `${R}/chapter-2-inflation/34 Plan - chapter 2 full redesign - places, shots and order of work.md`
const R4 = `${S}/round4-result.json`

const CONTEXT = `
THE PROJECT: a narrated explainer film for a phone screen (1080 x 1920) about austerity, from Clara E. Mattei's The Capital Order
(2022). The user is not a programmer. Chapter 2 is being remade in full in the look the user kept in log 32 (the notice corner): real 3D
places built in Blender by script, drawn once (the plate), later repainted by Flux, and shone back onto the set in the film stage. Until
the paintings are approved, the plates stand in for them (free). THE STANDARD to reach is the notice corner (${R}/experiments/
"32 Notice corner - film frames at 1, 4.5 and 9.5 seconds.jpg" and "32 Notice corner - plate and painting.jpg"; ${K}/07 Composing a shot.md):
every strong thing points at the subject, story props touch as one group, the frame is full top to bottom (the story group reaches well
into the lower half: in the notice corner the drum, chair and pail fill 0.45 to 0.8 down), the subject is the brightest thing, nothing reads
as a model or a toy, and lettering always shows whole words.
THE PLAN: ${PLAN}. EARLIER ROUNDS: ${S}/round1-result.json to round4-result.json. Round 4's result holds the set, pages and film reports
and, under "critique", a fresh critic's 15 numbered findings with measured problems and concrete fixes: THE LIST FOR THIS ROUND.
WHAT EXISTS: the Works assembly ${K}/paper-film/blender/inflation-chapter-2-newcomers/works/ (assemble_works.py, build_works.sh,
build_factories.py, build_far_town.py, works_kit.py, paint_works_pictures.py, make_works_continuity_sheet.py); the figures
${K}/paper-film/blender/figures/build_figures.py; the export, plates, state pictures and works-shot.json in
${K}/assets/models/inflation-chapter-2-newcomers/works/; the pages ${K}/paper-film/scenes/inflation-chapter-2-newcomers/page-3.js, page-4.js,
page-5.js and works-effects.js (spots for labels come from works-shot.json through works.screen(name)); graphics.js; works-states-test.js;
make_state_picture.py and make_behind_picture.py in ${K}/paper-film/tools/; the stage ${K}/paper-film/stage/cinema-stage.js; the shot checker
${K}/paper-film/tools/check-shot.sh (check_shot.py, shot_facts.py) with the Works' check files in ${K}/examples/inflation-chapter-2-newcomers/;
the chapter scene ${K}/paper-film/scenes/inflation-chapter-2-newcomers.js on the estimated timeline. Round 4's helpers' tools (smoke_path.py,
diffs.py, words_check.py, camera_facing.py, frame_times.py, changes_at.py) are in ${S}/round4-pages/tools, ${S}/round4-film/tools and
${S}/check-round-4.
TOOLS: Blender 5.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (-b, DISPLAY=:96; start Xvfb :96 if none runs); the film
stage node ${K}/paper-film/tools/render-paper-film.mjs from ${K} (never set PAPER_FILM_BROWSER); film-chapter-parallel.sh (PIECE_FRAMES=240);
find_jumps.py one piece at a time; camera_audit.py. The computer has 4 processors and other helpers render at the same time: one render of
your own at a time.
HARD RULES: spend no money (no fal, no ElevenLabs, no paid service of any kind); never change the kept notice corner's files
(${K}/assets/models/pit-village/notice-corner-*, street.blend, street.glb, camera.json, the pit village props and index.json) and prove its
stills unchanged after any shared change; a plain note at the top of every file, full plain-word names, the existing style; every sign with
real lettering and whole words in view, no digit on set dressing except "No. 1" and "No. 2", no logos, brands, party or chain colours; words
on screen only short forms of the narration; never MMT; cameras never turn. Repository files under 90 MB, no .blend1; keep above 4 GB free
disk (delete your own big scratch videos once checked). Stop processes only by their own process number. Do not commit (the lead commits).
Report in plain everyday words: what you changed, what you measured, what you did not do or are unsure of.`

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

const SET_FIXES = `YOUR TASK: the Works set for W1, W2 and W3 (you own assemble_works.py, build_factories.py and the figures; another helper
owns the page files and works-effects.js at the same time, so coordinate only through works-shot.json names). Fix round 4's critique findings
1, 2, 3, 5, 6, 7, 13 and the handcart half of 12, plus the film helper's problems 5 and 6 (round 4 result, film.summary). In short:
- people WORKING inside both lit doorways (finding 1): 2 or 3 existing figure shapes at the machines, dark work clothes, side-on or from
  behind, as dark shapes against the lit back wall; No. 2 in every No. 2 plate; No. 1 only in the working and men-gone helper plates (so on
  "go" the men leave the gate and appear inside). The state pictures' masks must then cover the doorway too;
- the waiting men as a loose crowd ACROSS No. 1's gateway, two deep, backs to the camera, 0.3 to 0.5 m between shoulders, heads at
  different heights, the stooped man at the brazier, and a thin rim of light on them from the yard light and the gate lamp (finding 2);
  the same arrangement for No. 2's men on page 12 (men_at_no_2). Check W3 at phone size: you must be able to count heads;
- PETROL and DIESEL against the dividing wall right of No. 1's right pier so no man is in front of them from W1 or W3 (finding 2), keep them
  in must_read; check No. 2's drums too; the THIS WAY UP pop-up crates placed and stacked so their whole words show above the drums from W1's
  composed spot (finding 7), added to must_read in the W1 working check file;
- bring W1's and W2's composed spots about 3 m nearer once the crowd stands near the gate (finding 3: the nearest man stays more than 6 m
  away, his feet near 0.72 down, the gate about half the frame's width), update works-shot.json and the camera files, and make the slide
  start and length still land as the pages expect (the pages read the camera files; tell the pages helper's successor in your report what
  changed). ADD to the shot checker a test that some story object reaches below 0.70 down (rule 7, a per-view setting in the check files,
  off by default so the notice corner's check is unchanged);
- W1 light (finding 5): the gate lamp off the pier's front face (hang it from the arch or the pier's inner face, about half as strong) so the
  gate, the chain and the board are lit and the quiet side holds nothing as bright as the gate; the brazier warming the gate's lower bars;
  W2 mirrored; re-run the checker until the gate holds at least 40% of the brightest parts;
- No. 1's looms that read as machines (finding 6): upright side frames, a big pulley wheel, a belt up to the line shaft, a pale roll of cloth,
  chest-high; break up the flat glowing back wall in both rooms (shelves, bobbin racks, a darker lower part);
- the handcart loaded with THIS WAY UP crates and moved nearer on the right pavement in W3, about 0.8 down (finding 12, first half);
- the stooped man (finding 13): look in Blender whether the checker's "rests on brazier" is his hands; note it in the check files or move
  him; make him clearly overlap the brazier (at least 15 pixels);
- WRITE these points into works-shot.json for the pages (Blender coordinates, metres): "machines": {"no-2-flywheel": [x,y,z],
  "no-1-looms": [x,y,z]} (the middle of each), and keep every existing key and object name the pages read; the queue's spot must still be
  right for the crowd (update men_at_no_1 and queue_front).
- then redraw every affected plate (read each render log for shadow faults), remake the state pictures and the behind picture, export, re-run
  the shot checker on W1, W2, W2 slowed and W3, and draw the continuity sheet. Make a before/after sheet of the plates at phone size.
W4 is NOT yours this round (another helper fixes it after you).`

const PAGE_FIXES = `YOUR TASK: the pages and the live effects (you own page-3.js, page-4.js, page-5.js, works-effects.js, graphics.js; another
helper rebuilds the Works set at the same time and will write "machines": {"no-2-flywheel": [x,y,z], "no-1-looms": [x,y,z]} into works-shot.json
and may move the W1 and W2 cameras about 3 m nearer; read the facts from the file, never hard-code positions). Fix round 4's critique findings
4, 8, 9, 11, the BANK half of 12, and 14:
- smoke (finding 4): wind across the view (about (-0.85, 0, -0.5) in the stage's axes, slight sink) so each plume lies as a long trail,
  brownish grey about 90 to 100, small dense puffs for the first 2 seconds so the plume is attached to the chimney's mouth; trace the paths in
  W1, W2 and W3 with smoke_path.py first; in W3 keep it below the lower rule card (which ends about 0.24 down); find and fix why puffs read as
  rings (test the focus blur guess by drawing with and without it);
- callout() in graphics.js: an option for the words to come in WITH the line (default unchanged so nothing else changes); use it for the
  three W3 labels so MACHINES reads about 0.85 s; point MACHINES at the new no-2-flywheel spot (add the spot to works-effects.js, reading
  facts.machines; fall back to the old spot if the key is missing); move WORKERS so its line leaves the crowd sideways and the label sits on
  the empty road, not over the men (finding 8);
- "busy" (finding 9): about three times the flicker for 2 seconds, a slow dark band passing across No. 2's panes, the doorway light pulsing
  with it; at least 15 levels of change over the windows (measure at 79.0 and 79.8 s);
- on "made" (finding 11): start No. 1's working smoke so the rule card's line lands on a smoking chimney;
- BANK dimmed to about 0.15 until page 9 (finding 12, second half);
- the NEW MONEY SPENT arrow ends at the chain between the gate leaves (gates.no-1.chain) (finding 14);
- then wait until the set helper's new export and plates exist (look for the machines key in works-shot.json and fresh plate dates; poll
  every few minutes, do something useful meanwhile, give up waiting after 3 hours and say so), and draw stills of every changed moment on the
  new set; fix what is wrong. Prove the notice corner's stills unchanged after any change to graphics.js or the stage.`

const CHECKOUT = `YOUR TASK: build the next place, B. THE CHECKOUT (view C1), as the plan describes it (part 1 section B; pages 1, 15 and 16 in
part 2; "Traps"; the lettering rules at the top of part 1; "New things to build by script"). This is the film's opening picture.
Learn from the Works first: round 4's critique lists what went wrong there (story small and high in the frame, bare floor in the bottom
third, the subject not the brightest thing, props that read as cut-outs, lettering cut off by other props, flat glowing back walls). Avoid
all of it from the start.
- Work in a new folder ${K}/paper-film/blender/inflation-chapter-2-newcomers/checkout/ (scripts) and ${K}/assets/models/
  inflation-chapter-2-newcomers/checkout/ (export, plate, camera file, shot file), in the Works' style (look at assemble_works.py,
  works_kit.py, the props scripts in ${K}/paper-film/blender/inflation-chapter-2-newcomers/ and set_dressing.py's export_for_film).
- Fetch the Poly Haven models and surfaces the plan names (free, CC0; the catalogue is in ${S}/polyhaven); build the rest by script with
  real lettering (BREAD, MILK, BUTTER, CHEESE, CHECKOUT, PETROL · DIESEL, the bill's words NEW MONEY: PRICES WILL GO UP). The newspaper
  masthead is invented: search the web that no real New Zealand paper or business uses it before you build it, and say what you searched.
  No digits anywhere (the card terminal's keypad turned away, no prices, no lane number). No chain colours (no supermarket green, red,
  yellow) and no large flat areas of a party's colour (red, blue, green, yellow, black, teal): neutral greys and wood. No people.
- Compose C1 with the shot checker until it passes (write its own check file, with the new "story object below 0.70 down" test on if the
  Works helper has added it; otherwise say so): the basket and the bill the brightest things under the warm lamp, the belt's lines meeting
  at the bill's edge, the dark ceiling patch at the top for the typed words, the basket about 0.75 down, the story group touching.
- Draw the plate at 1536 x 2730 (EEVEE, read the render log for shadow faults), and the export and camera file the film stage loads (as the
  Works does). Then show it in the film stage: a small test scene (like ${K}/paper-film/scenes/people-test.js) that projects the plate onto
  the set from the plate camera, and stills at the composed spot and at the end of a 1.3x slide, plus the "weights" check (blue at an edge
  means the camera left the painted area). Do not build page 1's file yet.
- A phone-size sheet: the plate, the stage stills, and the notice corner beside it for comparison.`

const W4 = `YOUR TASK: W4, the view from inside No. 2's yard (page 14), and page 12's second slowed state picture. Round 4's critique finding 10
lists W4's problems and fixes (empty yard in the bottom 30%, the jacket a flat cut-out, the cap a flat disc, the blank back of No. 2's board,
the "AY UP" crate fragment, WAGES a white speck, the yard lit warm like daytime, the top third too bright). Fix them all in assemble_works.py
(the set helper has finished with it; read its report below first and keep everything it did), redraw the W4 plate, re-check it with the
shot checker until it passes, and draw it in the film stage with works-states-test.js. Then make the windows-only slowed state picture for
page 12 (finding 15) with make_state_picture.py from W2's final plates. Re-export only if you changed exported objects, and then prove W1, W2,
W3 plates and names unchanged.`

const FILM = `YOUR TASK: film pages 3 to 5 again on the fixed set, plates and pages, from start to end (estimated timeline), and check: stills at
every event and the first, middle and last frame of each slide; the jump finder piece by piece (every jump planned); the camera audit (no
turn); every word on screen against the narration; the seconds a frame. Move the chunks out of paper-film/out into your scratch folder. Make a
one-frame-a-second contact sheet and phone-size still sheets. Fix nothing yourself; list every problem you see, worst first.`

phase('Fix and build')
const setP = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round5-set (create it).\n\n${SET_FIXES}`, { label: 'fix:works-set', phase: 'Fix and build', schema: REPORT })
const pagesP = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round5-pages (create it).\n\n${PAGE_FIXES}`, { label: 'fix:pages-and-effects', phase: 'Fix and build', schema: REPORT })
const checkoutP = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round5-checkout (create it).\n\n${CHECKOUT}`, { label: 'build:checkout-c1', phase: 'Fix and build', schema: REPORT })

const checkoutChain = checkoutP.then(checkout => agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-5-checkout (create it).\n\nThe builder's report:\n${JSON.stringify(checkout, null, 1)}
YOUR TASK: you are a film designer who has not seen this work before, and a skeptic. Look at the notice corner pictures named above first
(the standard the user loved). Then judge the new checkout view C1 (its plate at full size and phone size, the stage stills, the shot checker
report) against that standard and against the plan's part 1 section B and pages 1, 15 and 16: composition, light, anything that reads as a
toy or a model, lettering (whole words, no digits, no real paper's name: search the masthead yourself), colours (no supermarket chain's or
party's colours), and whether a newcomer would read "a supermarket checkout, a full basket, a newspaper warning that prices will go up" in two
seconds. Verify the builder's claims by measuring. Report every real problem with a concrete fix, worst first.`,
  { label: 'critique:checkout', phase: 'Critique', schema: FINDINGS }).then(critique => ({ checkout, critique })))

const [set, pages] = await Promise.all([setP, pagesP])

phase('Film and W4')
const w4P = agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round5-w4 (create it).\n\nThe set helper's report:\n${JSON.stringify(set, null, 1)}\n\n${W4}`, { label: 'fix:w4', phase: 'Film and W4', schema: REPORT })
const film = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round5-film (create it).\n\nWhat the two fixers reported:\n${JSON.stringify({ set, pages }, null, 1)}\n\n${FILM}`,
  { label: 'film:pages-3-to-5', phase: 'Film and W4', schema: REPORT })
const w4 = await w4P

phase('Critique')
const critique = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-5 (create it).\n\nThe reports:\n${JSON.stringify({ set, pages, film, w4 }, null, 1)}

YOUR TASK: you are a film designer who has not seen this work before, and a skeptic. First look at the notice corner pictures named above
(the standard the user loved). Then watch the new film of pages 3 to 5 (and its contact sheet) and open the plates of W1, W2, W3, W4 at full
size and at phone size. Judge honestly against that standard: composition (does everything strong point at the subject? is the frame full
top to bottom? do story props touch as one group?), light, whether anything reads as a toy or a model, whether a newcomer understands each
page from the pictures (two different factories; men waiting, then gone and seen working inside; the flat-out factory busy with nobody
waiting; the rule). Go through round 4's 15 findings one by one and say for each whether it is now fixed (measure it). Verify the fixers'
claims and that the kept notice corner is unchanged. Report every real problem left with a concrete fix, worst first.`, { label: 'critique:works', phase: 'Critique', schema: FINDINGS })

const checkoutResult = await checkoutChain
return { set, pages, film, w4, critique, checkout: checkoutResult.checkout, checkoutCritique: checkoutResult.critique }
