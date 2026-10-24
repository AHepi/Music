export const meta = {
  name: 'redesign-build-round-1',
  description: 'Free building, round 1 of the chapter 2 redesign: reusable script settings, the prop library and Works props; the figure shapes and the people test scene (no paid steps)',
  phases: [
    { title: 'Build', detail: 'scripts and props; figures and the people test' },
    { title: 'Check', detail: 'a fresh skeptic checks both' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign'
const PLAN = `${R}/chapter-2-inflation/34 Plan - chapter 2 full redesign - places, shots and order of work.md`

const CONTEXT = `
THE PROJECT: a narrated explainer film for a phone screen (1080 x 1920) about austerity, from Clara E. Mattei's The Capital Order
(2022). The user is not a programmer. Chapter 2 is being remade in full in the look the user kept in log 32: real 3D places built
in Blender by script, drawn once (the plate), repainted by Flux on fal, and the painting shone back onto the set in the film stage.
THE PRODUCTION PLAN (read the parts named in your task): ${PLAN}. The shot list: ${R}/chapter-2-inflation/34 Full redesign - working files/design/shots.json.
HOW THE KEPT SHOT WAS MADE (your pattern): ${R}/project-notes/Workflows.md section "A built place, painted over"; ${K}/07 Composing a shot.md;
${K}/paper-film/blender/pit-village/ (build_street.py, set_dressing.py, assemble_notice_corner.py, props/); ${K}/paper-film/scenes/notice-corner.js,
projected-set.js, pit-village-effects.js; the shot checker ${K}/paper-film/tools/check-shot.sh, check_shot.py, ${K}/paper-film/blender/shot_facts.py.
TOOLS: Blender 5.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender, run in the background (-b) with a virtual screen for
EEVEE: start one if none is running (pgrep Xvfb || (Xvfb :96 -screen 0 1920x1080x24 &)) and use DISPLAY=:96. Poly Haven (CC0) is
reachable (api.polyhaven.com, dl.polyhaven.org); its saved lists are in ${S}/polyhaven/. The film stage: node ${K}/paper-film/tools/render-paper-film.mjs
(from ${K}); never set PAPER_FILM_BROWSER. Python with numpy, opencv and Pillow; run Python that reads downloaded files with -I.
HARD RULES:
- Spend no money: never call fal, ElevenLabs or any paid service. Paintings and narration wait for the user's approval.
- NEVER overwrite or change the kept notice corner's files: ${K}/assets/models/pit-village/notice-corner-*, street.blend, street.glb,
  camera.json, the props folder's existing .glb files and index.json entries. Do not run build_street.py or set_dressing.py's export
  until they write to a folder you choose.
- Every new file: a plain note at the top saying what it does; full plain-word names in code (remove_empty_rows, not rmEmpty); match
  the style of the existing scripts. Every sign carries real lettering; no figure (digit) on any set dressing except "No. 1" and
  "No. 2"; no logos, brands, flags, party or chain colours.
- Keep work in the repository's film kit (${K}) so it is saved; keep downloads, big test pictures and scratch in ${S}/<your folder>.
  No single file in the repository over 90 MB; turn off Blender's .blend1 backups. Check free disk (df -h /) before big steps; keep
  above 4 GB free.
- Another helper works at the same time and may run Blender too: keep previews small (540 x 960) and render one at a time.
- Do not commit to git; the coordinator commits. Write in plain everyday words in your report.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string', description: 'what was built and what was found, in plain words' },
  files: { type: 'array', items: { type: 'string' } },
  tested: { type: 'string', description: 'what was run and checked, with numbers' },
  not_done_or_unsure: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' }, description: 'paths of preview pictures worth looking at' },
}, required: ['summary', 'files', 'tested', 'not_done_or_unsure', 'pictures'] }

const JOBS = [
  { key: 'scripts-and-props', ask: `YOUR TASK: the reusable scripts, the prop library and the Works' small props (plan part 1, "Reused files,
and the changes they need", and part 3 "New things to build by script", the Works list; findings F5 and F11 in part 5).
1. build_street.py: give it settings (command-line options after "--") for an output folder and base name, the colliery on or off, the
   lane's width (carriageway and pavements), its length, and the slope (4 degrees as now, or level); defaults must reproduce today's
   street exactly. set_dressing.py: export_for_film gets an output folder; its ground fallback (the 4-degree slope) becomes a setting.
   Prove the kept shot is unchanged: before changing anything, draw a small preview of the notice corner's composed frame
   (assemble_notice_corner.py --preview, see its notes) and after; compare them (they must match to within a few levels) and build
   the default street into your scratch folder and compare its object list and sizes with the existing street.glb.
2. The prop library: give convert_poly_haven.py, download_poly_haven.py and prop_library.py a choices list and an output folder, so
   chapter 2's props go to ${K}/assets/models/inflation-chapter-2-newcomers/props/ with their own index.json; the pit village library
   stays as it is. Fetch and convert the Works' Poly Haven choices from the plan (model hand_truck; surfaces white_sandstone_bricks and
   large_red_bricks into ${K}/assets/models/inflation-chapter-2-newcomers/textures/), checking each name in the saved lists.
3. Build by script, into the new library (a new scripted-props file for chapter 2, reusing scripted_kit.py and the notice-paper and
   colliery-board builders): the two gate boards "No. 1" and "No. 2" (cream sign-writer's lettering on near-black); the bank's hanging
   sign and brass plate "BANK"; two steel drums stencilled "PETROL" and "DIESEL" (dull grey-black; the stencil lettering readable); a
   crate stencilled "THIS WAY UP" (reuse wooden-chest if it fits); a chain and padlock; a lunch tin; a jacket and cap hanging on a nail;
   a tin mug; a pay envelope lettered "WAGES". Real sizes in metres; each prop stands on the ground (lowest point 0), with one root
   named after the prop, like the pit village props. Draw a contact sheet of them (render_contact_sheet.py or similar) and look at
   it: lettering legible, sizes believable, nothing blank.` },
  { key: 'figures-and-people-test', ask: `YOUR TASK: the people (plan section "People: how 'workers wait at the gate' and crowds are shown",
and order of work step 3, the free part only).
1. A figure builder by script (${K}/paper-film/blender/figures/build_figures.py or similar): simple but well-shaped working men of the
   early twentieth century in long work coats and flat caps, dull browns and greys, in five poses: hands in pockets, arms folded, one
   hand raised as if on a gate bar, one stooped toward a brazier, one leaning on a wall; plus walking figures (men and women, some with
   a bundle) for far-off crowds. Real height (about 1.65 to 1.8 m). They must read as people from behind and in silhouette at 6 to 9 m
   (heads, shoulders, caps, coat hems, legs apart), not as mannequins or capsules: build heads, necks, shoulders, arms with elbows,
   hands as simple mitts, coat skirts, trouser legs, boots. No faces are needed (they are seen from behind or as silhouettes). Save
   each as a .glb with one root, in ${K}/assets/models/inflation-chapter-2-newcomers/figures/.
2. The people test scene: a NEW assemble script (do not change assemble_notice_corner.py) that opens the pit village street.blend
   read-only and stands, near the notice corner (its kept files untouched; write everything under a new name such as people-test-*):
   four figures from behind at 6 to 9 m from the camera by the brazier, one facing the camera against the lit street at about 7 m, and
   six small walkers 40 to 60 m up the street. Draw the plate (1536 x 2730, EEVEE, as the notice corner's) and a helper plate without
   the figures, and export the set for the film (to a new output name; make sure set_dressing's export does not overwrite the notice
   corner, writing your own export step if needed).
3. A small test page (paper-film/scenes/people-test.js) that shines the PLATE (standing in for a painting: free) onto the set and holds
   still: first with the figures in it; then, on a time cut, the helper plate (the men gone) - use the stage's held-shot drawing
   (pose returns still: <a value that changes at the cut>, kit.moving for anything that moves, see cinema-stage.js and cinema-kit.js);
   and a second version where the figures are not in the plate but stand as dark own surfaces (near-black, a rim of light) over the
   helper plate. Draw stills before and after the cut, and of the silhouettes, and film 4 seconds of each to check nothing jumps.
4. Look at the stills at full size and judge honestly: do the figures read as people from behind and as silhouettes, at phone size?
   What would the painter likely get wrong? Report with the picture paths.` },
]

phase('Build')
const built = await parallel(JOBS.map((j) => () =>
  agent(`${CONTEXT}\n\nYour scratch folder: ${S}/${j.key} (create it).\n\n${j.ask}`, { label: `build:${j.key}`, phase: 'Build', schema: REPORT })))

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['where', 'problem', 'fix', 'severity'] } },
}, required: ['summary', 'findings'] }

phase('Check')
const checked = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-1 (create it).\n\nTwo helpers just built things:
${JOBS.map((j, i) => `### ${j.key}\nTask: ${j.ask}\nTheir report: ${JSON.stringify(built[i], null, 1)}`).join('\n\n')}

YOUR TASK: be a skeptic. Verify each report against the files and pictures: open every picture they name at full size; re-run the
notice corner preview comparison yourself; check the kept notice corner's files have not changed (compare modification times and
sizes with git: cd ${R}/.. && git status --short and git diff --stat); check the new props' lettering is legible and carries no stray
digits, brands or colours; check the figures read as people (not mannequins) from behind and in silhouette at phone size; check the
test page's cut does not leave ghosts or painted shadows behind; check file sizes (none over 90 MB) and that nothing was written
outside the agreed folders. Report every real problem with its fix.`, { label: 'check:skeptic', phase: 'Check', schema: FINDINGS })

return { built: JOBS.map((j, i) => ({ key: j.key, ...(built[i] || {}) })), checked }
