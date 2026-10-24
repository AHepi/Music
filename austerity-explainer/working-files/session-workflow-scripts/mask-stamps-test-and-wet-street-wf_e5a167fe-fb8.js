export const meta = {
  name: 'mask-stamps-test-and-wet-street',
  description: 'Test generated mask stamps (fal, under US$1) inside the slate moss and damage layers; then make a wetness layer with a specular map for the pit village street set and test it on the street view',
  phases: [
    { title: 'Mask test', detail: 'fal stamp sheets for moss and chips, plugged into copies of the slate layers, compared with the node-made masks', model: 'sonnet' },
    { title: 'Street study', detail: 'how the street set is built, shown and exported; how people make wet surfaces; plan', model: 'sonnet' },
    { title: 'Street build', detail: 'wetness layer with specular and roughness maps, new ground materials, renders of the street view dry and wet', model: 'sonnet' },
    { title: 'Checks', detail: 'fresh-eyes look checks of the mask test and the wet street; one fix round if needed', model: 'sonnet' },
  ],
}

const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const MT = PROC + '/mask_test'
const SW = PROC + '/street_wet'
const KIT = '/home/user/Music/austerity-explainer/film-kit'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const HOUSE = [
  'HOUSE RULES:',
  '* Working folder for textures: ' + PROC + ' (use absolute paths). Blender 5.2.2 is NOT on the search path: use ' + BLENDER + ' (always -b --disable-autoexec -t 2). The texture bake tool is lib/bake_harness.py (read it once; it photographs a recipe\'s node group from straight above). Do not edit lib/ or reference/ or any other job\'s folder.',
  '* The machine has only 4 processor cores and up to THREE other helpers are baking at the same time: run at most ONE Blender process at a time, always -t 2. Never use pkill -f or killall; stop your own runs by PID only.',
  '* The Bash tool stops a foreground command after 10 minutes: keep single runs under about 9 minutes, or use run_in_background: true and wait in ONE Bash call with an until-loop on the output file (never chains of sleep calls).',
  '* Disk is tight: check df -h / before each bake or render; free space must stay above 1.2 GB. Keep your folder under the size given in your task; delete your own superseded files; JPEG for pictures meant for looking. Use python3 -I for Python that reads pictures.',
  '* The film project in /home/user/Music/austerity-explainer is the person\'s repository: READ it freely but NEVER change, add or delete anything there; work on copies in your own folder. No git.',
  '* Plain Blender only (no film plugin, no Astra add-on, no extensions).',
  '* Do NOT start the test in "LATER - realistic moss and damage over the painted colour and weathering - NOT STARTED.md".',
  '* Names: full plain words; a plain note at the top of every file you create. Notes and guides are for a person who is not a programmer: plain everyday words, explain any unavoidable technical word in one sentence first, one word per thing, a concrete example before any general rule. Say what you tested, what you did not, and what you are unsure of; record failures. Never claim something works unless you ran it and looked at the result.',
].join('\n')

const MASK_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  generations: { type: 'array', items: { type: 'object', properties: { model: { type: 'string' }, prompt: { type: 'string' }, cost_usd: { type: 'number' }, file: { type: 'string' }, usable: { type: 'string' } }, required: ['model', 'prompt', 'cost_usd', 'file', 'usable'] } },
  total_cost_usd: { type: 'number' },
  how_it_plugs_in: { type: 'string' },
  measures_table_markdown: { type: 'string', description: 'look measures and same-kind scores: node-made masks vs generated stamps vs reference' },
  pictures: { type: 'array', items: { type: 'string' } },
  verdict: { type: 'string', description: 'plain: did the generated shapes look better than the node-made ones, where, and why' },
  failures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'generations', 'total_cost_usd', 'how_it_plugs_in', 'measures_table_markdown', 'pictures', 'verdict', 'failures', 'untested'] }

const STUDY_SCHEMA = { type: 'object', properties: {
  street_facts: { type: 'string', description: 'how the street set is built, which materials and textures it wears, which surfaces fill the main camera view and how much of the frame each covers, how it is exported (glb) and shown (three.js stage), what the stage does with roughness, specular, clearcoat and normal maps' },
  wet_methods: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, what_it_does: { type: 'string' }, how: { type: 'string' }, tested: { type: 'string' }, sources: { type: 'string' } }, required: ['name', 'what_it_does', 'how', 'tested', 'sources'] } },
  plan: { type: 'string', description: 'the build plan: the WETNESS layer (inputs, outputs, rules), which street materials get it, which materials are replaced by our own recipes and which keep their photo textures, the maps to produce, how to check them in Blender and in the stage' },
  guide_path: { type: 'string' },
}, required: ['street_facts', 'wet_methods', 'plan', 'guide_path'] }

const BUILD_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  wetness_layer: { type: 'string', description: 'what it is, its controls (what each does, range, default), what maps it writes' },
  materials_changed: { type: 'string' },
  maps_made: { type: 'array', items: { type: 'string' } },
  renders: { type: 'array', items: { type: 'string', description: 'path: what it shows' } },
  stage_check: { type: 'string', description: 'whether the specular/roughness/clearcoat maps survive the glb export and show in the three.js stage, with evidence, or why not tested' },
  timings: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'wetness_layer', 'materials_changed', 'maps_made', 'renders', 'stage_check', 'timings', 'failures', 'untested'] }

const LOOK_SCHEMA = { type: 'object', properties: {
  reads_well: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  problems: { type: 'array', items: { type: 'string', description: 'ranked, most noticeable first, with a crop path and a concrete fix' } },
  claims_checked: { type: 'array', items: { type: 'string', description: 'claim: holds / wrong (with the right number)' } },
  should_iterate: { type: 'boolean' },
  overall: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['reads_well', 'problems', 'claims_checked', 'should_iterate', 'overall', 'pictures'] }

// ---------------- mask test ----------------
const maskPrompt = [
  'You are the MASK TEST BUILDER. The person (not a programmer) suggested: "You can create masking layers with generations. Then use the masks as a layer to engineer into a procedure." They said: "Yeah do it as a test." Read ' + PROC + '/IDEA - masks from image generation as layers - NOT STARTED.md (the idea as written down; it is now STARTED as this test).',
  HOUSE,
  'Your folder: ' + MT + ' (keep it under 120 MB).',
  'MONEY: the person approved paid image generation for THIS TEST ONLY with a hard limit of US$1.00 in total. Before every paid call, look up the price (Fal tools: load them with ToolSearch, for example query "+Fal pricing" and "+Fal run", and use get_pricing or estimate_cost); keep a ledger file ' + MT + '/spending.md (model, prompt, price, running total) and stop before the total could pass US$1.00. Prefer cheap, good text-to-image models; at most about 6 pictures.',
  'GENERATE: stamp sheets in the hand-painted style of the slate reference (' + PROC + '/reference/slate/colour.png; look at it): (a) a sheet of separate MOSS CLUMPS (soft, mottled, irregular, some hanging drip shapes), (b) a sheet of separate PAINT/SLATE CHIPS and flaked-edge fragments; ideally white shapes on plain black (a mask), or coloured shapes on a plain flat background that you turn into a mask by colour. Save the originals in ' + MT + '/stamps/originals/, then clean them into masks (threshold, remove specks, keep soft edges where they help) and cut each sheet into a grid atlas of separate stamps (record the cell size and count). Look at every picture; say which were usable.',
  'PLUG IN: copy the CURRENT slate recipe and layers (' + PROC + '/recipes/slate_layers/recipe/slate_recipe.py, recipe/settings.json and layers/*.py) into ' + MT + '/slate_copy/ (record the time and a checksum of what you copied; another helper may still be finishing the slate, so never write into recipes/slate_layers). In your COPY, give the MOSS and DAMAGE layers a stamp mode: inside each slate (piece_id, local_x, local_y from the layout bundle), place a few stamps from the atlas at random places that follow the layer\'s own rules (moss hanging from the upper edge and along joints, chips along the lower edge and corners), with random stamp choice, turn, size and mirror per piece from the layer\'s seed, and use the stamp image as that layer\'s mask (a setting chooses: node-made mask, stamp mask, or both multiplied). The layer\'s colour, height and roughness stay its own. Keep the tile seamless (stamps that cross the tile edge must wrap; prove with the half-tile shift test at 512).',
  'COMPARE at 1254 dots with the same settings and seeds: (1) node-made masks (the copy unchanged), (2) generated stamps for moss, (3) generated stamps for chips, (4) both. Use the slate look measures (' + PROC + '/recipes/slate_layers/look_fixes/measure_look.py: olive share, tan share, largest moss clump, lightness spread inside moss, gradients) and lib/texture_compare.py against slate; and LOOK at 1:1 crops of moss and lower edges next to the reference. Make ' + MT + '/sheets/masks_compare.jpg (reference | node-made | stamps; full tile and 400 x 400 crops) and a sheet of the stamp atlases.',
  'Write ' + MT + '/notes - generated mask stamps test.md (plain words: what was generated and what it cost, how the stamps plug into a layer, what looked better or worse and why, what it would take to use this on other surfaces, failures, what was not tested). Save your structured result as ' + MT + '/result.json. Budget: about 12 Blender runs. Return the structured result.',
].join('\n')

function maskLookPrompt(build) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes (an art director for hand-painted game textures). Judge the generated-mask-stamps test strictly and check its claims. Write only into ' + MT + '/check/.',
    HOUSE,
    'The builder\'s report: ' + JSON.stringify(build),
    'Do: look at the reference slate, the node-made-mask tile and the stamp tiles at full size and at 1:1 (moss, chips, lower edges); judge whether the generated shapes read more like the reference\'s painted moss and chips; check that the tile is still seamless (re-run the half-tile test on one tile), that stamps are placed by the recipe (not painted into a picture outside Blender), that the spending ledger adds up and stays under US$1.00, and that two of the builder\'s numbers reproduce. Rank problems with crops and fixes. should_iterate is false for this test (it is a one-off test); put any follow-up ideas in problems.',
    'Return the structured result.',
  ].join('\n')
}

// ---------------- street ----------------
const ASK_STREET = 'WHAT THE PERSON ASKED: after the texture work, "move on to another set. Say, the street view test. Because it\'s going to need a specularity map to mimick wetness." The street view test is the pit village street set of the film project (log 29 of ' + KIT + '/../project-notes/Austerity explainer - project story.md and the "Plan 3 test clip" part of ' + KIT + '/../project-notes/Status.md): a 1926 pit village street at dusk built in Blender (scripts in ' + KIT + '/paper-film/blender/pit-village/, models and textures in ' + KIT + '/assets/models/pit-village/, main camera in camera.json), exported as a .glb, repainted by an image model in the series\' painted style and shone back onto the 3D set in the three.js stage (' + KIT + '/paper-film/scenes/projected-set.js). Today its materials wear downloaded Poly Haven photo textures (colour and normal only) with one fixed roughness each, so nothing looks wet.'

const studyPrompt = [
  'You are the STREET STUDY HELPER.',
  ASK_STREET, HOUSE,
  'Your folder: ' + SW + '/study/ (under 60 MB). Read only; small test renders allowed.',
  'Find out and write down: (1) how the street is built (build_street.py: parts, materials, texture sizes, tile_metres), which surfaces fill the main camera view and roughly what share of the frame each covers (make a quick false-colour material render from the main camera at a small size to measure it); (2) how the set is exported and shown: what the glb keeps (base colour, normal, metallic-roughness, KHR_materials_specular, clearcoat, emissive), and what the three.js stage and the repaint step actually use (read projected-set.js and the scene files); (3) how people make wet surfaces today in Blender 4.x/5.x and in three.js/glTF (darker and more saturated colour, lower roughness, higher specular, a clear wet film, puddles in low spots that flatten the relief and mirror the sky and lamps, wet bands at wall bottoms and under drips, wet setts with dry tops), with sources and a small Blender test of the most important ones; (4) which street materials should get a WETNESS layer, which (if any) should be replaced by our own texture recipes (' + PROC + ': the slate layers for roofs, brick, mud for the yard, a new sett/cobble layout from the stone tools) and which keep their photo textures with only the wetness layer added on top - remember the repaint step: what matters most is what the camera sees.',
  'Then write the BUILD PLAN: a WETNESS layer as a node group that can sit on top of ANY material (photo-textured or our recipes): inputs (colour, roughness, height or normal, a wetness amount, a puddle amount, a seed, world position or texture coordinate), rules (puddles in low spots, wet bands at wall bottoms, streaks under sills and eaves, drier tops of setts), outputs (wet colour, roughness, specular level, clearcoat, adjusted normal/height) and the MAPS to bake for the glb (roughness and a specularity map at least); how to check it in Blender (renders from the main camera: dry, wet; a close look at the setts) and, if possible, in the three.js stage. Keep the plan doable in about 20 Blender runs.',
  'Write ' + SW + '/study/09 Research - wet surfaces for the street set.md (plain words, pictures of your tests) and return the structured result.',
].join('\n')

function streetBuildPrompt(study, critique, round) {
  const lines = [
    'You are the WET STREET BUILDER' + (round > 1 ? ' (round ' + round + ', fixing what the checker found)' : '') + '.',
    ASK_STREET, HOUSE,
    'Your folder: ' + SW + ' (under 250 MB). Work on a COPY of the street: copy street.blend (or rebuild it with a copy of build_street.py writing into your folder) and the textures you need into ' + SW + '/set_copy/; never write into the film project.',
    'The study helper\'s findings and plan: ' + JSON.stringify(study) + ' (its guide and tests are in ' + SW + '/study/).',
  ]
  if (round === 1) {
    lines.push(
      'BUILD: (1) the WETNESS layer as a node group (Python that builds it, like the other recipes) with its controls; (2) put it on the street materials the plan names, and replace the materials the plan says to replace with our own recipes (re-use the shared layer files from ' + PROC + '/reuse_trials/shared_layers_snapshot/layers and the finished trials, never edit them); (3) bake the maps each changed material needs for the glb (colour, normal, roughness, specularity, and clearcoat if the plan says) into ' + SW + '/maps/ at a sensible size, and show them on one sheet; (4) render the main camera view at about 540 x 960 (Cycles CPU, -t 2, enough samples plus denoising, under about 9 minutes per render): A = the street as it is today, B = with the new materials dry, C = wet, D = wet and heavier rain; plus close-ups of the setts and a wall bottom near a lamp; (5) if possible, export a glb copy with the new maps and check in the three.js stage (Chromium and Playwright are installed; read how the film kit renders a frame) that the roughness and specular maps arrive and change the picture; if not possible, say exactly why; (6) record timings.',
      'Budget: about 20 Blender runs. Make ' + SW + '/sheets/street_dry_wet.jpg (A | B | C | D) and ' + SW + '/sheets/wet_closeups.jpg.'
    )
  } else {
    lines.push('The checker\'s findings: ' + JSON.stringify(critique), 'Fix what it found (most noticeable first), re-render what changed and re-make the sheets; add a "Round ' + round + '" section to the guide. Budget: about 10 Blender runs.')
  }
  lines.push(
    'Write (or update) ' + SW + '/09 Recipe - wetness layer and specular map for the street - how it is made.md (plain words: what wetness changes in a material and why, every control with what changing it does, the maps and what each is for, how to put it on another set, results, dead ends). Save your structured result as ' + SW + '/build_result_round_' + round + '.json and return it.'
  )
  return lines.join('\n')
}

function streetLookPrompt(build, round) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes (a film art director). Judge the wet street strictly and check the builder\'s claims. Write only into ' + SW + '/check_round_' + round + '/ (JPEG, under 15 MB).',
    ASK_STREET, HOUSE,
    'The builder\'s report: ' + JSON.stringify(build),
    'Judge: does the street read as wet after rain at dusk in 1926 (sheen on the setts, puddles mirroring the sky and lamps, darker wet walls at the bottom, believable not glassy or plastic), does the wetness sit right (puddles in low spots, not on raised setts or vertical walls), do new materials fit the rest of the set, does it suit the repaint step (would an image model keep the wet look), and do the maps in the glb carry the wetness (check the stage evidence; re-run one check if you can). Re-render one close-up yourself to confirm. Rank problems with crops and concrete fixes; set should_iterate true only if a fix round is clearly worth it.',
    'Return the structured result.',
  ].join('\n')
}

async function maskChain() {
  const build = await agent(maskPrompt, { ...SONNET, label: 'mask stamps test', phase: 'Mask test', schema: MASK_SCHEMA })
  const look = await agent(maskLookPrompt(build), { ...SONNET, label: 'mask test look check', phase: 'Checks', schema: LOOK_SCHEMA })
  return { build, look }
}

async function streetChain() {
  const study = await agent(studyPrompt, { ...SONNET, label: 'street study and plan', phase: 'Street study', schema: STUDY_SCHEMA })
  let build = await agent(streetBuildPrompt(study, null, 1), { ...SONNET, label: 'wet street build, round 1', phase: 'Street build', schema: BUILD_SCHEMA })
  let look = await agent(streetLookPrompt(build, 1), { ...SONNET, label: 'wet street look check, round 1', phase: 'Checks', schema: LOOK_SCHEMA })
  const rounds = [{ build, look }]
  if (look && look.should_iterate) {
    log('Street look check asked for a fix round')
    build = await agent(streetBuildPrompt(study, look, 2), { ...SONNET, label: 'wet street build, round 2', phase: 'Street build', schema: BUILD_SCHEMA })
    look = await agent(streetLookPrompt(build, 2), { ...SONNET, label: 'wet street look check, round 2', phase: 'Checks', schema: LOOK_SCHEMA })
    rounds.push({ build, look })
  }
  return { study, rounds }
}

const [mask, street] = await parallel([() => maskChain(), () => streetChain()])
return { mask, street }
