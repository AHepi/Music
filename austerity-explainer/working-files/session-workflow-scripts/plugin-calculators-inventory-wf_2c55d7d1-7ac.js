export const meta = {
  name: 'plugin-calculators-inventory',
  description: 'Inventory every setting and fix found by trial across the project, then design automatic calculators and an LLM tips guide for the explainer-film plugin',
  phases: [
    { title: 'Inventory', detail: 'five readers over notes, rounds, notice corner, tools, plugin' },
    { title: 'Design', detail: 'a designer, then a skeptic' },
  ],
}

const R = '/home/user/Music/austerity-explainer'
const K = `${R}/film-kit`
const PL = '/home/user/Music/plugins/explainer-film'
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign'
const OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators'

const GOAL = `
THE USER'S REQUEST (not a programmer): "All the runs and adjustments you've made, can you make them into automatic calculations the plugin
makes automatically so they don't have to be exhaustively searched for every time a new video is made. Along with tips and tricks for LLMs
to follow."
THE PROJECT: narrated explainer films for phone screens (1080 x 1920). Over many logs we found, by trial and repeated critique rounds, the
numbers and rules that make a shot work: camera places, distances, sizes of figures and lettering, light, composition rules, painting
prompts and alignment, state pictures, smoke and wind, page timing, filming speed, costs, and so on. The plugin
${PL} (skills, agents, workflows, kit = a copy of the film kit) is meant to let another model make the next film. We now want every value
that was searched for by hand turned into a calculation the plugin does automatically from the inputs a new film has (the script, the
narration timings, the 3D scene and its camera, the check file, prices), plus a guide of tips for LLMs.
PLACES TO READ: project notes ${R}/project-notes/ (Lessons.md, Workflows.md, Decisions.md, Status.md, "Austerity explainer - project
story.md" log), the film kit ${K} (its "07 Composing a shot.md", paper-film/tools, paper-film/blender, paper-film/scenes, narration-tools,
examples), experiments ${R}/experiments/ (logs 29 to 32 working files and reports), the chapter 2 redesign plan
${R}/chapter-2-inflation/"34 Plan - chapter 2 full redesign - places, shots and order of work.md", the redesign rounds' reports
${S}/round1-result.json to round4-result.json (round 4 has a critic's 15 findings with measured fixes), the people test ledger
${K}/assets/models/inflation-chapter-2-newcomers/people-test/people-test-paintings.json, and the plugin ${PL}.
RULES: read only; change no file; spend no money. Write any notes in ${OUT} (create it). Plain everyday words in descriptions, but exact
numbers, file paths and code names where they matter.`

const ITEMS = { type: 'object', properties: {
  items: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string', description: 'short plain name of the setting or fix' },
    area: { type: 'string', enum: ['camera and composition', 'people and figures', 'lettering and signs', 'light', 'painting and alignment', 'state pictures and changes', 'effects (smoke, fire, weather)', 'timing and words on screen', 'filming speed and memory', 'money and pricing', 'checking and critique', 'script and narration', 'models and Blender', 'other'] },
    how_found: { type: 'string', description: 'how it was searched for: which log, round or lesson, how many tries, what went wrong first' },
    final_value_or_rule: { type: 'string', description: 'the number or rule that worked, with units' },
    evidence: { type: 'string', description: 'file and line or log number that shows it' },
    computable_from: { type: 'string', description: 'which inputs a new film has that it could be computed from (or "judgement only" if it cannot be computed)' },
    proposed_calculation: { type: 'string', description: 'the formula or algorithm that would compute it automatically, concretely' },
    already_automatic: { type: 'string', description: 'is any tool already computing it? which, and is that tool in the plugin kit?' },
    llm_tip: { type: 'string', description: 'a one or two sentence tip for an LLM making the next film' },
  }, required: ['name', 'area', 'how_found', 'final_value_or_rule', 'evidence', 'computable_from', 'proposed_calculation', 'already_automatic', 'llm_tip'] } },
  notes: { type: 'string' },
}, required: ['items', 'notes'] }

const READERS = [
  { key: 'lessons-and-notes', task: `Read Lessons.md in full (every numbered lesson), Workflows.md and Decisions.md "Claude's calls". List every lesson that
records a value or rule found by trial (a failure, then a fix with a number or a rule), and every workflow step that a tool could do
for the reader.` },
  { key: 'story-log', task: `Read the project story's log (all numbered entries, 1 to 34) and Status.md. List every adjustment, tuning or
repeated fix it records (camera moves, lens, sizes, timings, voice speed, music loudness, captions, costs, filming time, memory,
compression to fit 30 MB, page-turn timing, etc.) that a later film would otherwise have to search for again.` },
  { key: 'redesign-rounds', task: `Read the chapter 2 redesign plan (all of it, especially People, the places, The numbers, Traps and part 5),
the round 1 to 4 reports in ${S} (every helper's report and every critic's findings), and the people test ledger. List every measured
fix and value (for example: figures never nearer than 6 m so heads stay under about 24 pixels; the crowd across the line of sight, not
along it; the camera about 3 m nearer so the nearest man's feet land near 0.72 down; smoke wind across the view; the gate lamp off the
pier's face; words ending exactly on a cut; the peel shading brought in over 0.3 of the peel; state picture thresholds 6 and 3; lettering
pixel heights; the gasholder pushed out of view; drums in must_read; and so on).` },
  { key: 'notice-corner-and-checker', task: `Read the film kit's "07 Composing a shot.md", paper-film/tools/check_shot.py, measure_composition.py,
shot_facts.py, align_painting.py, keep_painted_shadows.py, make_state_picture.py, make_behind_picture.py, and the logs 29 to 32 working
files and reports in ${R}/experiments/. List every threshold and rule in the checker and the painting steps, how each number was chosen,
and which of the checker's "fixes" could instead be computed BEFORE building (for example a camera placement solver that satisfies the
main rule, rule 1 and rule 7 at once), and which painting prompt parts could be generated from the check file automatically.` },
  { key: 'tools-and-plugin-gap', task: `Read the film kit's tools and scenes (paper-film/tools, paper-film/stage/cinema-stage.js, paper-film/scenes/cinema-kit.js,
cinema-chapter.js, projected-set.js, graphics.js, effects files, narration-tools/estimate_timeline.py, film-chapter-parallel.sh,
camera_audit.py, find_jumps.py, profile_frame.mjs) and the plugin ${PL} (README, every skill, agent and workflow, its kit). List the
tuned constants in the tools and how they were found, and the GAP: which film kit tools, rules and lessons from logs 29 to 34 are missing
from the plugin or out of date in it (compare files; the plugin is version 1.2.0).` },
]

phase('Inventory')
const inventories = await parallel(READERS.map((r) => () => agent(`${GOAL}\n\nYOUR PART (${r.key}): ${r.task}\nBe exhaustive: a missed item will be searched for again by hand in the next film.`,
  { label: `inventory:${r.key}`, phase: 'Inventory', schema: ITEMS })))
const all = inventories.filter(Boolean).flatMap((x, i) => x.items.map((it) => ({ ...it, from: READERS[i].key })))
log(`${all.length} items found by ${inventories.filter(Boolean).length} readers`)

const DESIGN = { type: 'object', properties: {
  calculators: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, file: { type: 'string', description: 'proposed path inside the plugin kit' },
    what_it_computes: { type: 'string' }, inputs: { type: 'string' }, outputs: { type: 'string' },
    method: { type: 'string', description: 'the formulas or algorithm, concretely enough to build' },
    replaces_items: { type: 'array', items: { type: 'string' } },
    test_cases: { type: 'string', description: 'known cases from this project the calculator must reproduce, with expected numbers and where they are recorded' },
    priority: { type: 'string', enum: ['first', 'second', 'later'] },
    effort: { type: 'string', enum: ['small', 'medium', 'large'] },
  }, required: ['name', 'file', 'what_it_computes', 'inputs', 'outputs', 'method', 'replaces_items', 'test_cases', 'priority', 'effort'] } },
  sync_to_plugin: { type: 'array', items: { type: 'string' }, description: 'film kit files and docs to copy or update in the plugin kit' },
  tips_guide_outline: { type: 'string', description: 'the outline of the LLM tips and tricks guide: sections and the tips under each' },
  judgement_only: { type: 'array', items: { type: 'string' }, description: 'items that cannot be computed and must stay as tips or critic checks' },
  summary: { type: 'string' },
}, required: ['calculators', 'sync_to_plugin', 'tips_guide_outline', 'judgement_only', 'summary'] }

phase('Design')
const design = await agent(`${GOAL}\n\nTHE INVENTORY (${all.length} items from five readers):\n${JSON.stringify(all, null, 1)}\n\nYOUR TASK: design the set of automatic
calculators for the plugin. Merge duplicates. Group items into a small number of well-made tools (for example: a shot planner that places
the camera and the people from the rules before anything is drawn; a lettering and figure size calculator; a light plan checker; a
painter's prompt builder from the check file; a state picture planner; an effects planner for smoke and wind relative to the camera; a
page timing and words planner; a budget, time and memory planner; a plugin "preflight" that runs them all and writes one report). Each
must state exact formulas and the known cases from this project it must reproduce (with the numbers), so a builder can write it and a
tester can prove it. Python 3 with numpy/opencv where needed; Blender-side parts as bpy scripts; prefer pure geometry from the camera and
the check file over rendering. Say what must stay judgement (tips and critic checks). Also list what in the film kit must be synced into
the plugin kit, and outline the tips guide for LLMs.`, { label: 'design:calculators', phase: 'Design', schema: DESIGN })

const SKEPTIC = { type: 'object', properties: {
  verdicts: { type: 'array', items: { type: 'object', properties: {
    calculator: { type: 'string' }, keep: { type: 'boolean' }, problems: { type: 'string' }, changes: { type: 'string' } }, required: ['calculator', 'keep', 'problems', 'changes'] } },
  missing: { type: 'array', items: { type: 'string' }, description: 'inventory items or known adjustments the design leaves out' },
  summary: { type: 'string' },
}, required: ['verdicts', 'missing', 'summary'] }

const skeptic = await agent(`${GOAL}\n\nTHE INVENTORY:\n${JSON.stringify(all, null, 1)}\n\nTHE DESIGN:\n${JSON.stringify(design, null, 1)}\n\nYOUR TASK: you are a skeptic.
For each calculator: would it really have computed what the rounds found by hand (check its formula against the recorded numbers yourself,
for example the W1 camera move, the figure head pixels at 6 m, the lettering sizes, the people test alignment), is it buildable from inputs
a new film actually has, is it over-built? Say keep or drop and what to change. Then list what the design misses from the inventory or from
the sources (read them yourself where needed).`, { label: 'design:skeptic', phase: 'Design', schema: SKEPTIC })

return { count: all.length, inventory: all, design, skeptic }
