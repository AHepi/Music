export const meta = {
  name: 'redesign-build-round-2',
  description: 'Free building, round 2 of the chapter 2 redesign: fix round 1\'s findings, build the two factories and the far town at true scale, and the state-picture step (no paid steps)',
  phases: [
    { title: 'Build', detail: 'prop fixes then the factories; figure fixes and state pictures' },
    { title: 'Check', detail: 'a fresh skeptic' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign'
const PLAN = `${R}/chapter-2-inflation/34 Plan - chapter 2 full redesign - places, shots and order of work.md`
const ROUND1 = `${S}/round1-result.json`

const CONTEXT = `
THE PROJECT: a narrated explainer film for a phone screen (1080 x 1920) about austerity, from Clara E. Mattei's The Capital Order
(2022). The user is not a programmer. Chapter 2 is being remade in full in the look the user kept in log 32: real 3D places built
in Blender by script, drawn once (the plate), repainted by Flux on fal, and the painting shone back onto the set in the film stage.
THE PRODUCTION PLAN: ${PLAN} (read "People", part 1 "A. The Works", part 3 "New things to build" and "Disk", and the Traps).
ROUND 1's results (what was built, and a skeptic's findings with fixes): ${ROUND1} (JSON: built[].summary/files/tested, checked.findings).
HOW THE KEPT SHOT WAS MADE: ${R}/project-notes/Workflows.md "A built place, painted over"; ${K}/07 Composing a shot.md;
${K}/paper-film/blender/pit-village/ (build_street.py, set_dressing.py, assemble_notice_corner.py, assemble_people_test.py, props/);
${K}/paper-film/blender/figures/; ${K}/paper-film/blender/inflation-chapter-2-newcomers/props/; ${K}/paper-film/scenes/people-test.js,
notice-corner.js, projected-set.js (it now has setPainting, blendTo and setView for state changes on a held shot), cinema-stage.js
(held shots: pose returns still: KEY; kit.moving(...) marks moving things).
TOOLS: Blender 5.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (-b, with DISPLAY=:96; start Xvfb :96 if none runs).
Poly Haven is reachable; its lists are in ${S}/polyhaven/. The film stage: node ${K}/paper-film/tools/render-paper-film.mjs (from ${K});
never set PAPER_FILM_BROWSER. Python with numpy, opencv, Pillow; run Python that reads downloaded files with -I.
HARD RULES:
- Spend no money: never call fal, ElevenLabs or any paid service.
- NEVER change the kept notice corner's files (${K}/assets/models/pit-village/notice-corner-*, street.blend, street.glb, camera.json,
  the pit village props and index.json). If you change a shared script, prove the notice corner's preview is unchanged (round 1 did:
  assemble_notice_corner.py --preview, compare pixel by pixel).
- Every new or changed file: a plain note at the top saying what it does; full plain-word names (no r, h, hz); the existing style.
  Every sign carries real lettering; no digit on any set dressing except "No. 1" and "No. 2"; no logos, brands, maker's labels, flags,
  party or chain colours.
- Keep work in the repository's film kit (${K}); scratch, downloads and big test pictures in ${S}/<your folder>. No file in the
  repository over 90 MB; Blender's .blend1 backups off; keep pictures outside .blend files where you can. Keep above 4 GB free disk.
- Another helper works at the same time and may run Blender: previews small (540 x 960), one render at a time.
- Do not commit to git. Report in plain everyday words.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, tested: { type: 'string' },
  not_done_or_unsure: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'files', 'tested', 'not_done_or_unsure', 'pictures'] }

const PROPS_FIXES = `YOUR TASK (short, do it first): fix round 1's prop findings (in ${ROUND1}, checked.findings):
the eight props whose root is named "<prop>.001" (rename joined parts, rebuild, check every .glb has exactly one root named after the
prop); the jacket and cap reading as a headless man (cap on its own nail beside the jacket, or on the crate, nothing round above the
collar); the hand truck's maker's sticker (paint it out in the converter step with a nearby patch of the same paint, re-save, note it
in index.json); index.json measurements taken from the saved models; the lunch tin, mug and envelope looking modern or wrong (dull
dented tinplate or dark enamel; a thin paper envelope with a faint fold); the gate boards' plank joints striking through the letters;
export_for_film's folder made a required setting (pass folder=SET_FOLDER explicitly in assemble_notice_corner.py and
assemble_lockout.py, then prove the notice corner's preview unchanged); short names renamed. Redraw the contact sheet and look at it.`

const FACTORIES = `YOUR TASK: the two factories and the far town of "The Works" (plan part 1 "A. The Works": layout, fixed looks,
states, and "Reused files, and the changes they need"; finding F4 in part 5). Read ${K}/paper-film/blender/build_factory.py and
build_town.py first, and the old models in ${K}/assets/models/inflation-chapter-2/ (leave them as they are).
Build, by script, into ${K}/assets/models/inflation-chapter-2-newcomers/works/ (new scripts in ${K}/paper-film/blender/inflation-chapter-2-newcomers/works/
or new options on the old scripts that keep their old default output byte-for-byte):
- No. 1, the quiet factory: dark red-brown brick, ONE tall ROUND chimney (about 25 m) at the back of its yard, a four-bay sawtooth
  roof, no water tank, a mill front with upper windows.
- No. 2, the flat-out factory: pale buff-grey brick (white_sandstone_bricks, toned), TWO SQUARE chimneys, a water tank on a steel
  trestle, long pitched shed roofs with a roof lantern, a mill front with upper windows.
- True scale (mill fronts about 8 m back behind a 4 m works wall; chimneys about 35 m behind the wall); surfaces mapped at true scale
  (no giant bricks); no shading bake (Blender draws the plates).
- Windows as separate pieces in named groups (so a plate can be drawn with all, a third, or none lit; the film can light them in steps),
  with lit and dark glass materials.
- No blank sign boards (remove the old one or letter it; the gate boards "No. 1" and "No. 2" come from the prop library).
- The far town (build_town.py at true scale, or a new script): chimneys, a gasholder, a spire, rooftops, seen far beyond the works.
Export each factory and the town as separate .glb files (each under 90 MB) with one root each, plus a .blend of each if useful (no
.blend1). Draw a contact sheet: each factory from the front at about 40 m and from a lane-level view, and the two side by side as the
plan's W3 (upstairs window across the lane, about 30 m from the wall, 4.6 m up) would roughly see them, with the town behind. Check by
eye at phone size: are the two told apart at a glance by shape (round vs two square chimneys, the tank)? Report sizes in metres.`

const FIGURES_STATES = `YOUR TASK: the figure fixes and the state-picture step.
1. Figures (round 1's findings, in ${ROUND1}): dark hair covering the back and sides of every head from under the cap to the collar;
   collars turned up or mufflers on men seen from behind so little pale neck shows; caps seated a little lower; the stooped man's hands
   lifted 10 to 15 cm off the drum's rim; walkers turned 20 to 40 degrees so their stride shows; most women bare-headed or with the
   shawl on the shoulders (never nun-like); the cloth pictures seeded with zlib.crc32 (repeatable) and their cache keyed by colour.
   Rebuild all 11 and redraw the contact sheets (back, side, front, silhouettes); look at them at full size.
2. The state-picture step (plan "How the men come and go"; ${K}/paper-film/tools/composite_fill.py may help): a tool, for example
   ${K}/paper-film/tools/make_state_picture.py, that takes the main painting, the second painting of the same view (or, for the free
   test, the plate and the helper plate), the two plates, and the outlines of what changes (the shot checker's per-prop outline
   pictures from shot_facts.py, or a mask), and writes the state picture: the main painting everywhere EXCEPT inside a mask made from
   (a) where the two plates really differ (the men and the shadows and light they change), joined with (b) the men's outlines, widened
   a little and softened; inside the mask, the second painting. Also write the mask as a picture to look at. Explain in its note how
   the mask threshold was chosen.
3. Rebuild the people test with the fixed figures (assemble_people_test.py: also move the hand-on-bar man out of the brazier's smoke
   column), redraw the plate and helper plate, make the state picture with the new tool, and change people-test.js so its time cut
   swaps to the STATE picture (not the whole helper plate). Draw stills before and after the cut and the mask, film 4 seconds, and run
   the jump finder (${K}/paper-film/tools/find_jumps.py) to show the cut is the only jump. Judge honestly at full size whether any
   ghost or shadow stays where the men stood.`

phase('Build')
const [propsAndFactories, figures] = await parallel([
  async () => {
    const fixes = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round2-props (create it).\n\n${PROPS_FIXES}`, { label: 'build:prop-fixes', phase: 'Build', schema: REPORT })
    const factories = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round2-factories (create it).\n\n${FACTORIES}`, { label: 'build:factories', phase: 'Build', schema: REPORT })
    return { fixes, factories }
  },
  () => agent(`${CONTEXT}\n\nYour scratch folder: ${S}/round2-figures (create it).\n\n${FIGURES_STATES}`, { label: 'build:figures-and-states', phase: 'Build', schema: REPORT }),
])

const FINDINGS = { type: 'object', properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: {
    where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' },
    severity: { type: 'string', enum: ['must-fix', 'should-fix', 'minor'] } }, required: ['where', 'problem', 'fix', 'severity'] } },
}, required: ['summary', 'findings'] }

phase('Check')
const checked = await agent(`${CONTEXT}\n\nYour scratch folder: ${S}/check-round-2 (create it).\n\nThree helpers just worked:
### prop fixes\nTask: ${PROPS_FIXES}\nReport: ${JSON.stringify(propsAndFactories?.fixes, null, 1)}
### factories\nTask: ${FACTORIES}\nReport: ${JSON.stringify(propsAndFactories?.factories, null, 1)}
### figures and state pictures\nTask: ${FIGURES_STATES}\nReport: ${JSON.stringify(figures, null, 1)}

YOUR TASK: be a skeptic. Verify each report against the files and pictures (open every picture at full size). Check: the kept notice
corner unchanged (git status and diff under assets/; redraw its preview and compare); every prop .glb has one root named after it; no
stray digits, brands or labels anywhere; the factories are true scale, told apart at phone size by shape, with separate window groups,
no blank boards, no giant bricks; file sizes under 90 MB; the state picture leaves no ghost or shadow at the cut and changes nothing
outside its mask (measure the difference outside the mask); the figures no longer look bald or like mannequins at the plate's size.
Report every real problem with its fix.`, { label: 'check:skeptic', phase: 'Check', schema: FINDINGS })

return { props_fixes: propsAndFactories?.fixes, factories: propsAndFactories?.factories, figures, checked }
