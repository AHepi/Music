export const meta = {
  name: 'plugin-calculators-build',
  description: 'Build the explainer-film plugin calculators: sync the film kit into the plugin, the geometry core and settings, then six builders with tests against the project\'s recorded numbers',
  phases: [
    { title: 'Core and sync', detail: 'frame geometry, settings, place facts; film kit into the plugin kit' },
    { title: 'Build', detail: 'six builders in parallel, each with tests' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const PL = '/home/user/Music/plugins/explainer-film'
const C = `${PL}/kit/calculators`
const SP = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const D = `${SP}/plugin-calculators/inventory-and-design.json`

const BASE = `
THE USER'S REQUEST (not a programmer): "All the runs and adjustments you've made, can you make them into automatic calculations the plugin
makes automatically so they don't have to be exhaustively searched for every time a new video is made. Along with tips and tricks for LLMs
to follow."
THE DESIGN: ${D} holds the inventory (423 hand-found values, each with evidence and a proposed calculation), the design (17 calculators
with formulas and test cases) and a skeptic's verdicts (what to change in each, and what is missing). READ THE DESIGN ENTRY FOR YOUR
CALCULATORS, THE SKEPTIC'S VERDICT ON THEM, THE SKEPTIC'S "missing" LIST, AND EVERY INVENTORY ITEM YOUR CALCULATORS REPLACE. Where the
skeptic corrects the design, follow the skeptic, and check its numbers against the project's files yourself.
THE PLUGIN: ${PL} (skills, agents, workflows, bin, kit = a copy of the film kit). New calculators go in ${C}/ (Python 3; numpy, opencv,
PIL are installed; pytest is NOT, so tests are plain Python files ${C}/tests/test_NAME.py that exit non-zero on failure, plus one runner
${C}/tests/run_all.py that the core helper writes and every builder's test is picked up by). Small JSON fixtures copied from the project go in
${C}/tests/fixtures/ (never large pictures or models: keep each fixture under 1 MB and the plugin lean; write the source path in a note).
THE PROJECT'S FILES (read only unless your task says otherwise): the film kit ${K}; notes ${R}/project-notes/; experiments ${R}/experiments/;
the redesign scratch ${SP}/redesign/ (round1..round4-result.json, round5-* folders with checkout C1's check files, people-paint/).
HOUSE RULES: a plain note at the top of every file saying what it does and how to use it; full plain-word names (remove_empty_rows, not
rmEmpty); every calculator has a --help, writes JSON and a short plain-words report, and says which film-settings.json values it used.
Mark each house number as measured, judged or invented. Every calculator gets tests that reproduce the project's recorded cases (with the
numbers and where they are recorded) and, where possible, a hold-out case it was NOT derived from (checkout C1, the people test). Do not
claim a test proves something it only repeats (for example a price computed from the same rate). No money; no paid service. Do not change
the film kit, the round 5 Works files or the checkout files (other helpers are working there). Do not commit (the lead commits). Keep above
4 GB free disk; delete your own frame dumps. Stop processes only by their own process number. Report in plain everyday words: what you
built, what each test proves, what failed or is unsure.`

const REPORT = { type: 'object', properties: {
  summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } },
  tests: { type: 'string', description: 'each test, what it reproduces, the numbers, pass or fail' },
  settings_added: { type: 'string', description: 'keys added to film-settings.json, under which section' },
  api: { type: 'string', description: 'how other tools and the preflight call yours: commands, functions, inputs, outputs' },
  not_done_or_unsure: { type: 'string' },
}, required: ['summary', 'files', 'tests', 'settings_added', 'api', 'not_done_or_unsure'] }

const CORE = `YOUR TASK: the core every other calculator builds on (design: "Frame geometry core and shared film settings"; skeptic's verdict;
"missing": the standard place-facts file, shot-kind profiles, the accepted list).
1. ${C}/frame_geometry.py and ${PL}/kit/paper-film/scenes/frame-geometry.js (the same sums for pages) with a parity test (the same points give
   the same answers in both, run with node). Projection to the film frame and the plate, metres per pixel, where the lines meet, reach (how
   far a camera may stand for a thing to land at a given 'down'), eye height, turn and slide effects, slide magnification measured at the
   nearest painted surface using the painting's returned height (the skeptic's correction).
2. ${PL}/kit/film-settings.json: one table of every house number from the inventory (frame, lenses, margins, bands, timing constants, sound
   targets, filming costs per frame updated to round 4's measured 0.9 s held, 4.3 s sliding, about 35 s loading a piece, prices with the
   date they were read, state picture thresholds, and so on), each with {value, unit, kind: measured|judged|invented, source}. And
   ${C}/settings.py to read it (with a clear error for a missing key). Sections by area, so builders can add their own section.
3. The standard PLACE FACTS file: a JSON schema (${C}/place_facts_schema.json) and validator (${C}/place_facts.py) that every place's
   assemble script will write: views (camera place, turn, lens, composed and plate spots, slide, subject, kind of shot), signs (centre, normal,
   letter height, words, must_read), emitters (chimney mouths, fires), figures (feet, facing, height), lights (place, target, watts),
   landmark tops, support surfaces (floor, counter, pavement heights; interiors), and an "accepted" list (rule, view, reason, who, date).
   Write converters that build place facts from the Works' works-shot.json + camera files, the notice corner's files and the people test's
   people-test-shot.json + camera, and put the converted results in fixtures.
4. Shot-kind PROFILES in film-settings.json: still life (the notice corner), crowd, overview, interior, dark subject; each with which
   composing rules apply and their limits, taken from what the project accepted (the skeptic lists where the notice corner limits would
   reject the accepted round 5 Works views).
5. ${C}/tests/run_all.py (runs every tests/test_*.py, prints a plain summary, exits non-zero on any failure) and your own tests: the notice
   corner's meeting point (0.684, 0.4395 per the design), the works-shot.json letter pixel sizes, W1's reach numbers per the skeptic (d_max
   7.30 m for 0.70; man at 7.42 m lands 0.696; DIESEL front 0.723; round 4's spot at y 10.2 gives 0.653), head 63 px at 6 m; and a hold-out
   from checkout C1's files if they exist yet.
Write ${C}/README.md: what each calculator is for (list all 17 from the design, marking yours built and the others "being built").`

const SYNC = `YOUR TASK: bring the plugin's kit up to date with the film kit (design: "sync_to_plugin"; skeptic: "missing"). Copy newer and missing
film kit files into ${PL}/kit/ (paper-film/scenes, stage, tools, blender/pit-village and figures scripts, narration-tools including
estimate_timeline.py, docs such as "07 Composing a shot.md" and "05 Lessons and traps.md", examples and small test fixtures), keeping the
plugin-only improvements the design lists (do not overwrite them; merge by hand if both changed). Leave out: chapter-specific Works and
checkout assembly files that round 5 is still changing (note them for a later sync), large models, pictures and paintings (the plugin must
stay lean: no file over 5 MB, and say the total size before and after), anything with a password or key, and session paths (replace
/tmp/claude-0/... paths in copied text with a plain note). Then fix the plugin skills and docs that are out of date (the design's list, for
example camera-and-framing.md's rule 12 margins; the built-and-painted workflow from Workflows.md logs 29 to 34 as a section of
make-3d-models or a new skill "build-and-paint-a-place"). Do not touch ${C}/ or kit/paper-film/scenes/frame-geometry.js or
kit/film-settings.json (the core helper is writing them). Prove the synced kit still works: run the plugin kit's own checker tests
(kit/paper-film/blender/tests if they run without Blender, or say why not) and load one synced scene file with node --check.`

const BUILDERS = [
  { key: 'shot-planner', task: `Build the SHOT PLANNER (design "Shot planner"; skeptic's changes: shot-kind profiles, accepted list, closed forms,
no silhouette fallback, people limits: backs to the camera at 6 m or more from every camera place along the slide, the crowd's long axis at
least 60 degrees to every view, crowd two deep with 0.3-0.5 m between shoulders) as ${C}/plan_shot.py, pure geometry from place facts and a
shot list (subject, story, kind). It places the camera (x, height, turn), the composed and plate spots, the slide and its longest safe
length, the plate's lens and size, the people and props, then predicts the composition numbers the checker would measure and says what
fails and by how much, in metres. Also teach the plugin kit's check_shot.py to read the check file's "accepted" list and the shot-kind
profile (accepted items reported as known, not as new problems; default behaviour unchanged when absent, prove the notice corner's report
is unchanged). Tests: round 4's W1 spot fails (bottom third bare, 0.653) and round 5's passes, the crowd across the lane, the people test,
the notice corner; hold-out: checkout C1.` },
  { key: 'views-and-models', task: `Build three Blender-side and audit tools: (1) ${C}/view_audit.py, lettering, figure and landmark audit per view
(design "Lettering, figure and landmark audit"; skeptic: letter height from the vertical part of the view ray, width from the horizontal;
must-read words fail under about 20 px and warn at 20-25; unnamed signs compared by letter px times contrast against the named ones,
calibrated on BANK; head size; tall landmarks in the typed-words band; backs of signs that show); (2) ${PL}/kit/paper-film/blender/make_check_file.py
(bpy: writes a view's check file from the scene; story roles come from the shot list, everything else generated, on_ground against declared
support surfaces, light props only when their own materials emit, "band": true when no sky; prove it reproduces the hand-made Works W1 and
notice corner check files except the story roles, and the checkout's ceiling and counter cases); (3) ${PL}/kit/paper-film/blender/model_lint.py
(bpy and .glb: stripes with the real thresholds from ${SP}/redesign/check-round-3/tools/find_stripes.py, tested against round 3's 15, 27,
33 striped parts and round 4's 0; same-plane faces; floors just over ground; '.001' names; glass alpha; glowing bases; front axis). Blender
5.2 is at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (-b, DISPLAY=:96; another helper may be rendering, so keep your runs
short and one at a time); use --disable-autoexec for any .blend you did not make.` },
  { key: 'painting', task: `Build the PAINTING tools: (1) ${C}/paint_request.py with templates/paint-prompt.txt and templates/behind-prompt.txt (design
"Painter's request builder"; skeptic: a paint_as field in the check file for each story prop's description; the plate preflight including
lesson 138's glow inside a hollow (light in the top 30% of a hollow prop's mask means darken it first), figures casting long shadows
(lesson 135: refuse, or warn that the painter will leave them), figure-to-surround brightness; prompt clauses for figures: backs to us, far
walkers flat dark shapes with no pale spots, a facing figure's face lost in deep shadow with no lit cheek, keep the figures as dark as in
image 1; the price from film-settings.json's dated rate times (output + input megapixels), marked as an estimate until fitted to real
charges; reproduce the people test's and the notice corner's prompts' structure from their ledgers); (2) ${C}/after_painting.py (design
"Painting arrival checks"; skeptic's pass logic: always align, fail only if no better than before, if the best shift is at the search's edge,
or if it ends under 0.85; figures pass when within-3-px is no more than 0.05 below that figure's plate baseline; count figure-sized blobs;
figure-to-surround brightness plate against painting (people test: about 15% to about 50%); skin-hue pixels per head (0 to 183); a style
match against the standard painting (brightness 77.4, spread 26.1, colour 45 to 50, ink lines 6.4 to 6.7%); lossless saving; the behind
painting's leftover shadows (people test: dark streaks where the men's shadows fell)) - test it on the people test's real paintings in
${K}/assets/models/inflation-chapter-2-newcomers/people-test/ and the notice corner's in ${K}/assets/models/pit-village/ (read only; use
their facts folders or make plate facts with the plugin kit's shot_facts.py); (3) ${C}/plan_states.py (design "State picture planner";
skeptic: blend default 0.8 s in 3 steps, cut when the change is under about 0.12 of the frame, an error for two sub-changes on one plate,
thresholds from measured noise, the exact make_state_picture.py commands; lesson 136: warn when only people change at a cut and nothing
else shows time passing).` },
  { key: 'pages-and-timing', task: `Build the PAGE TIMING tools: (1) ${PL}/kit/paper-film/tools/page_events.mjs (runs a page or chapter in an events
mode in the stage and dumps every kit.at/kit.end call, slide, draw2D item with box and opacity, still key, effect and join, at 30 frames a
second; instrument the plugin kit's graphics.js and cinema-kit.js only behind an events flag so normal drawing is unchanged, and prove it:
one still before and after, identical); (2) ${C}/plan_page_timing.py (design "Page timing and words-on-screen planner"; skeptic: the pause
after a page = join.after + join.length + about 0.15 s settle plus any hold, clamped to 1.1-1.7 only for plain peels; each element's appear
delay read from graphics.js (buildWords' 0.14 s); reproduce round 4's MACHINES readable only about 0.4 s and the PRICES UP fix with the
corrected numbers; the word-lookup lint for words said more than once; words ending exactly on cuts (fadeOut 0); readable at least 1 s;
margins (0.90 across, letter tops 0.06 down); numbers against the ledger; the still list; the planned cuts for find_jumps); (3) a slim
${PL}/kit/paper-film/tools/check_page_layout.mjs (skeptic: one-frame pops outside planned cuts, effects visible after their page, still keys
changing during a move, holds with no still key, overlaps at events). Test on the film kit's chapter 2 pages 3 to 5 data (copy small fixtures:
timeline-estimated.json, page files read only).` },
  { key: 'script-sound-budget', task: `Build: (1) ${PL}/kit/narration-tools/lint_script.py (design "Script and narration gate"; skeptic: figures
limit about 5-6 a minute calibrated on the two chapter 2 scripts (the newcomer script 4.1 a minute passes, the old 8.8 fails), unfamiliar
words and stakes as lists for a person, a "key": true page mark, the cue, capitals, names, the rule said twice word for word, guess holds,
words a minute per page at the narrator's measured speed, the estimated timeline via estimate_timeline.py, credits and dollars, and the
transcript checks after recording); (2) ${PL}/kit/narration-tools/sound_gates.py (design "Sound calculator and gates"; skeptic: momentary
400 ms loudness or RMS per word span and per pause of 0.5 s or more; the ducking loop to 18 dB under the voice while she speaks and about 12
in pauses; the length after every audio step within 0.05 s; final loudness -15 LUFS +/- 0.5 and true peak under -1 dBTP measured on the
encoded file; alignment within 2 ms) and wire it into the plugin kit's mix scripts and finish_film.sh as gates; (3) ${C}/plan_budget.py
(design "Budget, filming time, memory and disk planner"; skeptic: profile one held and one moving frame per view before filming and plan
from those, table only as fallback (0.9 / 4.3 s, about 35 s loading); reproduce round 4's 53 minutes for pages 3 to 5 from its own frame
mix without circularity; the spend ledger against the user's allowance; stretches under 2 hours with FILM_FROM/FILM_TO commands; workers;
lazy loading; disk). Test on the chapter 2 files (narration scripts, the old timeline, timeline-estimated.json, round 4's frame-times.txt).` },
  { key: 'effects-camera-light', task: `Build: (1) ${C}/plan_effects.py (design "Effects planner"; skeptic: test puff TOP edges (centre minus half
the width where opacity is 0.2 or more), trace both wind signs and keep the one that passes in every view; reproduce round 4's failing wind
(0.044 of the width) and round 5's passing one (0.188) from ${SP}/redesign/round4-pages/tools/smoke_path.py and the round 5 settings in
the film kit's works-effects.js; plume colour and mouth; contact shadows for props the behind painting removes; the window-change check of 15
levels); (2) extend the plugin kit's ${PL}/kit/paper-film/tools/camera_audit.py with a built-set mode (named moves per shot, any turn during a
slide, meeting-point drift, slide magnification at the nearest painted surface, whether the frame leaves the painted plate) and the page
window from the timeline; prove its old behaviour unchanged on chapter 2's old camera log if one exists; (3) ${C}/plan_lights.py (design
"Light planner"; skeptic: start watts by inverse square from a reference light, reach by ray cast to the first non-target surface, cone from
the subject's size, links, the shadow-caster list, EEVEE shadow settings and the render-log check; a 'dark subject' profile for gates and
openings, where the round 5 attempts to make the gate brightest failed at 0.85x). Leave tune_lights for later and say so.` },
]

phase('Core and sync')
const [core, sync] = await parallel([
  () => agent(`${BASE}\n\n${CORE}`, { label: 'build:core', phase: 'Core and sync', schema: REPORT }),
  () => agent(`${BASE}\n\n${SYNC}`, { label: 'build:sync', phase: 'Core and sync', schema: REPORT }),
])

phase('Build')
const builders = await parallel(BUILDERS.map((b) => () => agent(`${BASE}\n\nTHE CORE IS BUILT. Its report:\n${JSON.stringify(core, null, 1)}\n\nTHE KIT SYNC IS DONE. Its report:\n${JSON.stringify(sync, null, 1)}\n\nUse the core's frame_geometry, settings and place facts; never copy their sums. Add new house numbers to ${PL}/kit/film-settings.json only under your own section, re-reading the file right before one single edit.\n\nYOUR TASK (${b.key}): ${b.task}`,
  { label: `build:${b.key}`, phase: 'Build', schema: REPORT })))

return { core, sync, builders: Object.fromEntries(BUILDERS.map((b, i) => [b.key, builders[i]])) }
