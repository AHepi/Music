export const meta = {
  name: 'plugin-surfaces-and-wear',
  description: 'Put everything learned about surfaces, wear, weathering and believable construction into the explainer-film plugin (skills, kit code, a preflight check, a place-building workflow), then test that a model uses it without being told',
  phases: [
    { title: 'Inventory', detail: 'four readers: weathering kit and street; garden; procedural cookbook; the plugin and rendering' },
    { title: 'Design', detail: 'one plan for the plugin changes, then a fresh critic' },
    { title: 'Build', detail: 'skill text; kit code, audit and preflight; place-building workflow' },
    { title: 'Verify', detail: 'tests and a small smoke scene; two blind newcomers; code and docs review' },
    { title: 'Fix', detail: 'apply what the checks found, rerun tests' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const P = '/home/user/Music/plugins/explainer-film'
const PT = '/home/user/Music/procedural-textures'
const WORK = SC + '/plugin-work'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const CLIENT = SC + '/runpod/render_client_serverless.py'
const GUIDE = SC + '/runpod/HOW TO RENDER - pay per second.md'
const OPTS = { model: 'sonnet', effort: 'xhigh' }
const WORDS = "Sonnet needs to use normals, displacements, dirt, grime, weeds, weathering, damage.. basically everything. But don't tell it that. These things need to be in the plugin."

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. Over the last days this project learned, by building and checking, how to make 3D places in Blender look believable and full of character: real normal maps and displacement, dirt and grime where things touch and where water runs, weeds and moss where they would grow, weathering, damage, wetness, rubbish, construction that makes sense (every plank on a support, every support on the ground), detail designed into the art style instead of photographic noise, measured checks (value range, detail energy, squint test, normal-map direction), fresh-eyes checkers, and cheap rendering on rented cards paid per second. Almost none of that is in the project's Claude Code plugin yet. The person said, verbatim: "${WORDS}"
THE GOAL: the plugin "explainer-film" (${P}) must carry all of it, so that ANY model (often a smaller one, such as Sonnet) asked with a plain request to build a place, a set or props in Blender, with no mention of surfaces or wear, applies the full treatment by itself. Make it automatic in four ways: (1) routing: the skills a model reads first make the surface-and-wear pass and the construction check required steps, and the skill descriptions mention them so they are picked; (2) kit code a model calls instead of reinventing (one entry point per job, settings per place, presets); (3) a preflight check that fails when a material or the scene lacks them; (4) a workflow that builds a place in parts with fresh checkers. Keep everything generic: it must work for any place (town, harbour, mine, farm, garden, interior), not one place.
SOURCES: this project's saved texture and place work in ${PT} (start with "${PT}/Procedural textures - project story.md": the goal, the word list and logs 1-31 with every lesson and failure); the weathering kit ${PT}/kits/weathering; the street ${PT}/street_wet; the garden ${PT}/garden (the plan "30 Plan - Japanese garden - all the advice.md", its stages, and garden/character with the style note, direction, builder and fixer stages, normal tools, checkers' findings in workflow_result.json and the notes 32-34); the cookbook ${PT}/cookbook; ${PT}/lib; the scratch copies in ${SC}/proc-work (same layout, more files); the rendering guides and code in ${SC}/runpod (pay-per-second client, its job taker in serverless/, set-up notes in "${PT}/RunPod set-up for rendering - findings.md"); seven Scenario Blender skills (MIT licence) in /home/user/Music/.claude/skills and the note "${PT}/23 Scenario Blender skills - what was installed, changed and learned.md".
HARD RULES: write only inside ${P} and your own scratch folder ${WORK}/<your step>/; never commit or push; never print, copy, move or read anything in ~/.runpod, and never put keys, endpoint ids, machine ids or volume ids into the plugin (rendering code must read the user's own settings at run time); never put the person's name, email or any personal detail anywhere or into a request to an outside website; never copy the person's own Astra Blender add-on (${SC}/astra-upload*, ${SC}/astra-work) or its code into the plugin (the summaries in ${PT}/garden/addon may inform rules in your own words); third-party code keeps its licence file and a note of where it came from; never write in /home/user/Music/japanese-courtyard. Disk here: about 2.5 GB free and shared; keep big files (.blend, EXR, big renders) on the rented store.
BLENDER: ${BLENDER} headless (-b --disable-autoexec; xvfb-run -a for anything drawn here; this computer is slow, only tiny tests here). Anything bigger renders on the rented cards: read ${GUIDE} and use only ${CLIENT} (the endpoint is switched on; if jobs wait more than 5 minutes while workers show idle, stop and report it, never purge the queue or change the endpoint).
WRITING: the plugin is read by smaller models and by the person: plain everyday words, one word for each thing, a concrete example before a general rule, say what was measured versus judged. New files: plain-word names. Code: full plain-word names (remove_empty_rows, not rmEmpty) and a plain note at the top of each file saying what it does. Report in plain words: what you did, what you tested, what you did not, every failure.`

const INV = { type: 'object', properties: {
  techniques: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, what_it_is: { type: 'string' }, why_it_matters: { type: 'string' }, how_to_do_it: { type: 'string' },
    measured_results: { type: 'string' }, traps_and_failures: { type: 'string' }, sources: { type: 'array', items: { type: 'string' } },
    reusable_code: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' }, generic_or_place_specific: { type: 'string' }, depends_on: { type: 'string' } }, required: ['path', 'what', 'generic_or_place_specific', 'depends_on'] } },
  }, required: ['name', 'what_it_is', 'why_it_matters', 'how_to_do_it', 'measured_results', 'traps_and_failures', 'sources', 'reusable_code'] } },
  checks_and_measures: { type: 'array', items: { type: 'string' } },
  gaps_or_unproven: { type: 'array', items: { type: 'string' } },
  summary: { type: 'string' },
}, required: ['techniques', 'checks_and_measures', 'gaps_or_unproven', 'summary'] }

const STEP = { type: 'object', properties: {
  summary: { type: 'string' }, files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
  tests_run: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } }, runpod_seconds: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'files_changed', 'tests_run', 'pictures', 'runpod_seconds', 'failures', 'untested'] }

phase('Inventory')
const READERS = [
  { key: 'weathering and street', brief: `the weathering kit (${PT}/kits/weathering, every file: README, HOW TO USE, the recipe note, apply_weathering.py, its parts ground, growth, walls, masks, presets, sets, integrate, harness) and the street work (${PT}/street_wet: tools, the wetness recipe 09, relief_and_rubbish, grime_and_growth, eevee_vs_cycles, check rounds; story logs 18-27). Techniques: grime, cracks, stains, weeds, moss, rust, wetness and puddles, specular maps, sett joints that read under all light, the rubbish mask built from the scene's real shape, settings files per place, presets, the courtyard transfer test.` },
  { key: 'garden', brief: `the Japanese garden (${PT}/garden: "30 Plan - Japanese garden - all the advice.md", the stages shapes, life, surfaces (surf_kit.py), light, final, fix, check; then garden/character: concept/ (style note with section 0, the rule for every builder), direction/ (direction note, briefs, shared/normal_tools.py), wood/ roof/ ground/ pond/ (builder stages and modules), final/ (build_character.py, render_character.py, stage_final.py), fix/ (four fixers' stages), workflow_result.json (every builder, checker and fixer report; read the checkers' problems and which claims did NOT hold), and the notes 32, 33, 34; story logs 30-31). Techniques: scene inspection (floating parts, short posts, buried lights, faces fighting), real-world scale facts, scanned surfaces, real normal maps made and checked for direction, geometry detail (plank shapes, tile variety, chunky tufts), construction logic of a bridge, moss caps and cushions, the style rule "details are designed parts of the style", measures (value range, detail energy, squint test, flat-colour windows, saturation), ownership of stages and the conflict check, fresh checkers and claim checking, the repeated-stamp and bean-bag traps, concept images as targets.` },
  { key: 'procedural making', brief: `the procedural texture research and cookbook (${PT}/cookbook: every guide, especially relief (height, bump, displacement and normal maps), pattern makers, shapers, seamless tiles, the painted look, baking and checking, geometry nodes and modifiers, the new-surface checklist, reuse; ${PT}/lib tools; ${PT}/recipes guides; ${PT}/research; story logs 1-17), and the seven Scenario Blender skills in /home/user/Music/.claude/skills (especially texturing-shading: edge wear, cavity dirt, baking; uv-baking; lighting-rendering) with the note on what was learned from them (log 23). Techniques: making brick, slate, wood, metal, mud and gravel by recipe; layers (colour and fade, damage, moss, outline); seeds; tiling traps; normal-map conventions; displacement versus bump; baking for EEVEE; edge wear and cavity dirt; what failed.` },
  { key: 'plugin and rendering', brief: `the plugin as it is now (${P}: README, every skill, agents, workflows, kit/docs including "LLM tips and tricks.md", kit/paper-film/blender (model_kit.py, model_lint.py, textures.py, build_* scripts), kit/calculators, kit/film-settings.json, bin/explainer-film-preflight and its stages, the tests), and rendering on rented cards (${SC}/runpod: both HOW TO RENDER guides, render_client_serverless.py, serverless/handler.py, start.sh, copy_libraries.sh; "${PT}/RunPod set-up for rendering - findings.md"; story logs 21, 26, 29, 33's note on credit running out in ${PT}/garden/character/"33 Note - RunPod credit ran out.md"), the renderer rule (Cycles where lamps, windows or fires are lit, EEVEE when they are off). Report exactly what the plugin says today about materials, surfaces, wear, normal maps, displacement and construction (quote file and line), where a model following it would skip these, how the preflight stages are built (so a new stage can be added the same way), how the tests run, and what a generic rented-card rendering guide would need (without any key or id).` },
]
const inventories = await parallel(READERS.map(r => () => agent(`${COMMON}
YOUR STEP: INVENTORY, reader "${r.key}". Read, in full, ${r.brief}
Return every technique and lesson that a model building a new place would need, with how to do it, what was measured, the traps and failures, and the code worth carrying into the plugin (say whether each file is generic or tied to one place, and what it depends on). Do not change any file.`, { ...OPTS, label: `inventory: ${r.key}`, phase: 'Inventory', schema: INV }).then(x => ({ reader: r.key, inventory: x }))))

phase('Design')
const DESIGN = { type: 'object', properties: {
  plan: { type: 'string', description: 'the full design in plain words' },
  files: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, contents: { type: 'string' }, owner: { type: 'string', enum: ['skills and docs', 'kit code', 'workflow'] } }, required: ['path', 'action', 'contents', 'owner'] } },
  entry_points: { type: 'string', description: 'the exact names, arguments and outputs of every kit entry point, the audit and the preflight stage, so the three builders agree' },
  how_it_becomes_automatic: { type: 'string' }, tests: { type: 'string' }, risks: { type: 'array', items: { type: 'string' } },
}, required: ['plan', 'files', 'entry_points', 'how_it_becomes_automatic', 'tests', 'risks'] }
const design = await agent(`${COMMON}
YOUR STEP: DESIGN the plugin change (version 1.4.0). Read the four inventories below, then the plugin itself (${P}) where you need detail. Write one design that three builders will follow at the same time without stepping on each other: (a) "skills and docs": a new skill for the surface-and-wear pass and believable construction (with reference files), edits to make-explainer-film, build-and-paint-a-place, make-3d-models, the tips guide, README (and its Changes section), plugin.json and /home/user/Music/.claude-plugin/marketplace.json versions; (b) "kit code": the kit modules carried in and made generic (weathering, normal-map making and checking, displacement, wetness, growth and rubbish masks, picture measures, scene inspection for floating parts and supports, and a MATERIAL AND SCENE AUDIT that lists, per material and per object, which treatments it has and fails when a required one is missing), settings per place and presets, house numbers in film-settings.json, a new preflight stage in bin/explainer-film-preflight, and tests that run here; (c) "workflow": a workflow in ${P}/workflows that builds a place in parts (plan the place and its real-world facts, build parts in parallel with the surface pass and construction check built in, combine with an ownership and conflict check, the audit, render with the renderer rule on rented cards or locally, fresh checkers that verify claims, one fix round, a re-check) plus any agents it needs. Decide exact names and arguments of every entry point so (a), (b) and (c) agree. Say how each of the person's items (normals, displacements, dirt, grime, weeds, weathering, damage, and the rest that "basically everything" covers: moss, wetness, rubbish, stains, cracks, edge wear, construction logic, scale, the style rule, measures, fresh checkers) becomes automatic, and where a smaller model would most likely skip it and how the plugin stops that.
INVENTORIES: ${JSON.stringify(inventories)}`, { ...OPTS, label: 'design', phase: 'Design', schema: DESIGN })

const CRITIC = { type: 'object', properties: {
  missing: { type: 'array', items: { type: 'string' } }, not_automatic: { type: 'array', items: { type: 'string' } },
  wrong_or_risky: { type: 'array', items: { type: 'string' } }, required_changes: { type: 'string' }, verdict: { type: 'string' },
}, required: ['missing', 'not_automatic', 'wrong_or_risky', 'required_changes', 'verdict'] }
const critic = await agent(`${COMMON}
YOUR STEP: DESIGN CRITIC (fresh eyes; you did not write the design). Compare the design with the inventories and the sources. List every learned technique or lesson that the design leaves out, every item that would still depend on the requester asking for it (not automatic), anything wrong, risky, place-specific or unlicensed, and the exact changes the builders must make. Pretend you are a smaller model given only the plugin and a plain request "build me a place": where would you still skip normal maps, displacement, dirt, grime, weeds, weathering or damage?
DESIGN: ${JSON.stringify(design)}
INVENTORIES: ${JSON.stringify(inventories)}`, { ...OPTS, label: 'design critic', phase: 'Design', schema: CRITIC })

phase('Build')
const OWNERS = [
  { owner: 'skills and docs', job: `write and edit the skill text and docs owned by "skills and docs" in the design (new skill folder, edits to the existing skills, the tips guide, README with a 1.4.0 Changes entry, plugin.json and marketplace.json versions). Name the kit entry points exactly as the design's entry_points say. Make the surface-and-wear pass and the construction check REQUIRED numbered steps in build-and-paint-a-place and make-3d-models (not "consider"), and make every skill description that a model reads when asked to build a place, a set or props mention them so they are picked.` },
  { owner: 'kit code', job: `write the kit code owned by "kit code" in the design: carry the weathering kit and the other tools into the kit, made generic (settings per place, presets, roles of objects), the material and scene audit, the new preflight stage, the house numbers, and tests that run here (python3 and headless Blender on tiny scenes). Prove each entry point on a small generic test scene (a few boxes and planes standing for a wall, a floor, a post and a beam) and save one small JPG per check in ${WORK}/kit/. Run the existing tests too (python3 ${P}/kit/calculators/tests/run_all.py) and keep them passing.` },
  { owner: 'workflow', job: `write the workflow (and any agents) owned by "workflow" in the design, in ${P}/workflows (plain JavaScript in the Workflow tool's format: export const meta first, agent()/parallel()/pipeline()/phase(), args for the request and the environment notes; no Date.now or Math.random). It must take the requester's plain words as they are and add the plugin's own steps (surface pass, construction check, audit, measures, fresh checkers, one fix round) itself; the environment (where to render, disk limits, paths, money rules) comes in through args. Check it parses (node --check on a copy wrapped as a module, or another way).` },
]
const builds = await parallel(OWNERS.map(o => () => agent(`${COMMON}
YOUR STEP: BUILD, owner "${o.owner}". Change only the files the design gives to your owner (other builders work at the same time on the rest). Your job: ${o.job}
DESIGN: ${JSON.stringify(design)}
CRITIC'S REQUIRED CHANGES (follow them): ${JSON.stringify(critic)}`, { ...OPTS, label: `build: ${o.owner}`, phase: 'Build', schema: STEP }).then(x => ({ owner: o.owner, report: x }))))

phase('Verify')
const VERDICT = { type: 'object', properties: {
  passed: { type: 'boolean' }, findings: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, where: { type: 'string' }, fix: { type: 'string' }, severity: { type: 'string', enum: ['blocking', 'should fix', 'minor'] } }, required: ['problem', 'where', 'fix', 'severity'] } },
  evidence: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
}, required: ['passed', 'findings', 'evidence', 'pictures', 'summary'] }
const NEWCOMER = { type: 'object', properties: { plan: { type: 'string' }, plugin_parts_used: { type: 'array', items: { type: 'string' } } }, required: ['plan', 'plugin_parts_used'] }
const verifySmoke = () => agent(`${COMMON}
YOUR STEP: VERIFY BY USING IT (fresh; you built none of it). Using ONLY the plugin (${P}: its skills, kit and preflight), build a small test scene in Blender: a short stretch of brick canal wall with a wooden lock gate, stone steps and a towpath, about 12 m long. Follow the plugin's steps as a newcomer would. Render one EEVEE picture (1200 x 800) and one close-up on the rented cards, run the plugin's audit and its new preflight stage, and run all the plugin's tests. Report what worked, what broke, where the instructions were unclear, and whether the picture shows normal maps, displacement, dirt, grime, weeds, weathering and damage. Save the pictures as JPGs under 400 KB in ${WORK}/verify/.
BUILDERS' REPORTS: ${JSON.stringify(builds)}`, { ...OPTS, label: 'verify: use it on a small scene', phase: 'Verify', schema: VERDICT })
const newcomer = (place, n) => agent(`You have a Claude Code plugin for making films installed at ${P} (read its README first, then whatever it tells you to read). A person asks you, in these words: "Build ${place} in Blender for a film." Do not build anything. Write the step-by-step plan you would follow, as concretely as you can (what you would make, in what order, with which plugin parts and kit commands, how you would check it), and list the plugin parts you would use. Read only the plugin folder; do not read any other folder.`, { ...OPTS, label: `newcomer ${n}`, phase: 'Verify', schema: NEWCOMER })
const verifyCode = () => agent(`${COMMON}
YOUR STEP: CODE AND DOCS REVIEW (fresh). Review every file the builders changed: bugs, paths that only work on this computer, anything place-specific, keys or ids or personal details (grep for them), licences of carried-in code, links and names that do not match between skills, kit, preflight and workflow, and whether the old tests still pass (run them). Do not change files; report findings with the fix.
BUILDERS' REPORTS: ${JSON.stringify(builds)}`, { ...OPTS, label: 'verify: code and docs', phase: 'Verify', schema: VERDICT })

const [smoke, newcomers, codeReview] = await parallel([
  verifySmoke,
  () => parallel([() => newcomer('a small fishing harbour with a fish market', 1), () => newcomer('a water mill by a river with its miller\'s yard', 2)]),
  verifyCode,
])
const judged = await agent(`${COMMON}
YOUR STEP: JUDGE THE BLIND NEWCOMERS. Two fresh models were given only the plugin and a plain request with no word about surfaces or wear. Their plans are below. For each plan, say whether it applies, without being asked: normal maps, displacement, dirt, grime (where things touch and where water runs), weeds, moss, weathering, damage (chips, cracks, missing pieces), wetness or rubbish where they belong, construction that makes sense, real-world scale, the style rule, the measures, the audit and preflight, fresh checkers. For each item a plan misses, find why in the plugin text (quote it) and say the smallest change that would make a model pick it.
PLANS: ${JSON.stringify(newcomers)}`, { ...OPTS, label: 'verify: judge the newcomers', phase: 'Verify', schema: VERDICT })

phase('Fix')
const fix = await agent(`${COMMON}
YOUR STEP: FIX. Apply every "blocking" and "should fix" finding below (and the minor ones that are cheap), in the plugin only. Rerun all the plugin's tests and the new preflight stage on the small test scene from the smoke check if it exists. Report each finding as fixed or not, with why.
SMOKE CHECK: ${JSON.stringify(smoke)}
CODE AND DOCS REVIEW: ${JSON.stringify(codeReview)}
NEWCOMER JUDGE: ${JSON.stringify(judged)}
BUILDERS' REPORTS: ${JSON.stringify(builds)}`, { ...OPTS, label: 'fix', phase: 'Fix', schema: STEP })

return { inventories, design, critic, builds, smoke, newcomers, codeReview, judged, fix }