export const meta = {
  name: 'wood-from-displacement-map',
  description: 'Build a wood recipe that uses the uploaded wood displacement and colour maps as its source and procedurally makes large non-repeating areas from it; research, build, independent checks',
  phases: [
    { title: 'Research', detail: 'how people make non-repeating surfaces from an example map in Blender 5.x; small tests', model: 'sonnet' },
    { title: 'Build', detail: 'board layout that samples the displacement and colour maps together; bigger non-repeating areas', model: 'sonnet' },
    { title: 'Check', detail: 'fresh-eyes look check and honesty check; one fix round if needed', model: 'sonnet' },
  ],
}

const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const WD = PROC + '/recipes/wood_from_displacement'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const ASK = [
  'WHAT THE PERSON ASKED (they are not a programmer; they test ideas by having helpers build them): about the wood texture, "Maybe the wood is going to need the displacement map. But then procedurally generate more non repeating surface with it. Because it\'s not good."',
  'Meaning, as decided: the earlier wood recipes (recipes/wood/, made purely from nodes with the picture only as a guide) are not good enough. For WOOD ONLY, the person now allows the uploaded wood displacement map (' + PROC + '/reference/wood/height_as_uploaded.png, 1254 x 1254, 8-bit grey, brighter = higher; it shows 5 horizontal rows of weathered boards with butt joints, cracks, knots and dark round stain splotches) to be used as the SOURCE material. Blender must then procedurally ARRANGE that material into new surfaces: a default tile that repeats without a seam, and bigger areas (2 x 2 and 4 x 4 tiles and more) that never visibly repeat. The arrangement must be made by Blender nodes inside one recipe (no hand-made collage, no image editing outside Blender).',
  'The person then added: "And the material map." Meaning, as decided: the uploaded wood COLOUR map (' + PROC + '/reference/wood/colour.png, the painted material picture of the same boards) is ALSO allowed as source material. The MAIN version samples BOTH the colour map and the displacement map with exactly the same arrangement (same window, same flips, per dot), so colour and relief always match; small per-board tone shifts are allowed and wanted (they break repetition). A COMPARISON version makes colour procedurally FROM the sampled displacement instead (a wood palette mapped from height, plus per-board tone), to show how much the colour map adds. Keep both, label them clearly. The uploaded normal map is NOT sampled directly (a flipped board would have its slopes pointing the wrong way): the normal is made from the sampled height at strength 8 and compared with the uploaded normal as a check. The shared slate layers in reuse_trials/shared_layers_snapshot/layers may be used for extra stains or wear if they help.',
].join('\n')

const HOUSE = [
  'HOUSE RULES:',
  '* Working folder: ' + PROC + ' (cd there in every command; use absolute paths). Blender 5.2.2 is NOT on the search path: use ' + BLENDER + '. Bake with: ' + BLENDER + ' -b --disable-autoexec -t 2 --python lib/bake_harness.py -- RECIPE.py OUT --size N [--normal-reference wood] [--params JSON]. Read lib/bake_harness.py once.',
  '* The machine has only 4 processor cores and TWO other helpers are baking at the same time: run at most ONE Blender process at a time, always with -t 2. Never use pkill -f or killall; to stop a run of yours, kill it by its PID.',
  '* The Bash tool stops a foreground command after 10 minutes. Keep single runs under about 9 minutes; for longer runs use run_in_background: true and wait in ONE Bash call with an until-loop on the output file (never chains of sleep calls).',
  '* Disk is tight: check df -h / before each bake; free space must stay above 1.2 GB. Keep ' + WD + ' under 150 MB; delete your own superseded bakes; JPEG for pictures meant for looking. Use python3 -I for Python that reads pictures.',
  '* Do not edit lib/, reference/, or other recipes\' folders. No git. Plain Blender only (no film plugin, no Astra add-on, no extensions). Web research is allowed for the research step only.',
  '* Do NOT start the test in "LATER - realistic moss and damage over the painted colour and weathering - NOT STARTED.md".',
  '* Names: full plain words; a plain note at the top of every file you create. Notes and guides are for a person who is not a programmer: plain everyday words, explain any unavoidable technical word in one sentence first, one word per thing, a concrete example before any general rule. Say what you tested, what you did not, and what you are unsure of; record failures. Never claim something works unless you ran it and looked at the result.',
].join('\n')

const RESEARCH_SCHEMA = { type: 'object', properties: {
  methods: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, what_it_does: { type: 'string' }, how_in_blender: { type: 'string' }, tested: { type: 'string', description: 'what you ran in Blender 5.2 and what happened, or "not tested"' },
    good_for_this_wood: { type: 'string' }, sources: { type: 'string' } }, required: ['name', 'what_it_does', 'how_in_blender', 'tested', 'good_for_this_wood', 'sources'] } },
  source_map_facts: { type: 'string', description: 'measured facts about the wood displacement map: row bands, joint positions, seam behaviour, what features are where' },
  recommendation: { type: 'string' },
  guide_path: { type: 'string' },
}, required: ['methods', 'source_map_facts', 'recommendation', 'guide_path'] }

const BUILD_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  method: { type: 'string' },
  controls: { type: 'string', description: 'every setting of the recipe: what it does, range, default' },
  scores: { type: 'string', description: 'same-kind scores (overall, colour, height, normal) for the main and comparison versions on three seeds, against reference wood; the earlier wood recipe new tile scored the same way; pixel numbers for transparency' },
  repetition_evidence: { type: 'string', description: 'how you showed bigger areas do not repeat: measures and pictures' },
  seam_evidence: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' } },
  failures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'method', 'controls', 'scores', 'repetition_evidence', 'seam_evidence', 'pictures', 'failures', 'untested'] }

const LOOK_SCHEMA = { type: 'object', properties: {
  reads_as_the_same_wood: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  big_area_repeats: { type: 'string', enum: ['no visible repeat', 'some repeat landmarks', 'clearly repeats'] },
  problems: { type: 'array', items: { type: 'string', description: 'ranked, most noticeable first, with a picture crop path and a concrete suggested fix' } },
  better_than_earlier_wood: { type: 'string' },
  should_iterate: { type: 'boolean' },
  overall: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['reads_as_the_same_wood', 'big_area_repeats', 'problems', 'better_than_earlier_wood', 'should_iterate', 'overall', 'pictures'] }

const HONESTY_SCHEMA = { type: 'object', properties: {
  claims_hold: { type: 'boolean' }, problems: { type: 'array', items: { type: 'string' } }, checked: { type: 'array', items: { type: 'string' } },
}, required: ['claims_hold', 'problems', 'checked'] }

const researchPrompt = [
  'You are the RESEARCHER for this job.',
  ASK, HOUSE,
  'Write into ' + WD + '/research/ only.',
  'Find out how people currently (2024-2026) make large non-repeating surfaces from ONE example texture or displacement map, especially in Blender 4.x/5.x, and test the promising ones in Blender 5.2 here with small node setups (512 dots). Cover at least: (1) per-piece random sampling: a board/brick layout where each piece reads the example at its own random offset, flip or rotation (texture bombing by pieces); (2) "stochastic" or hex tiling (Heitz and Neyret 2018 histogram-preserving blending, and the simpler 3-sample hex blend people build in Blender nodes or add-ons); (3) Wang tiles / random tile picking; (4) texture bombing of stamps (for knots, stains); (5) breaking repetition with large-scale masks (per-board tone, stains, wear); (6) anything new in Blender 4.x-5.x that helps (for example new nodes, repeat zones in shaders or geometry nodes, the Image Texture node\'s options), and whether a geometry-nodes route (real board meshes with random UV offsets) is worth it. For each: what it is in one plain sentence, how it is done in Blender, what you ran and saw, and whether it suits THIS wood map.',
  'Also measure the source map once (this is allowed now): where the 5 board rows run (top and bottom of each band), where the butt joints are in each row, whether the map wraps seamlessly left-right and top-bottom, how wide the dark gaps are, where knots and stains sit, and how the colour map relates to it (the notes say colour brightness predicts height with correlation about 0.94-0.985 on these maps; check for wood). Save the measurements as a small JSON file.',
  'Write the guide ' + WD + '/research/08 Research - making big non-repeating surfaces from one map.md (plain words, with your test pictures) and return the structured result with a clear recommendation for the builder.',
].join('\n')

function buildPrompt(research, critique, round) {
  const lines = [
    'You are the WOOD BUILDER' + (round > 1 ? ' (round ' + round + ': fixing what the checkers found)' : '') + '.',
    ASK, HOUSE,
    'Your folder: ' + WD + ' (recipe/, outputs/, area/, tests/, variations/, sheets/). Research done for you: ' + JSON.stringify(research) + ' (guide and test files in ' + WD + '/research/).',
    'Useful earlier work: the earlier wood recipes and their guides in ' + PROC + '/recipes/wood/ (read "04 Lessons - wood ..." for what went wrong); the shared layered slate recipe pattern in ' + PROC + '/recipes/slate_layers/ (recipe/slate_recipe.py, interface/interface.md) and the frozen shared layers in ' + PROC + '/reuse_trials/shared_layers_snapshot/ (import from there only, never edit; set sys.dont_write_bytecode = True before importing); the seamless noise helpers in lib/recipe_tools.py; make_normal.py in recipes/slate_layers/integration/ (strength 8 for wood); lib/texture_compare.py and lib/pixel_compare.py.',
  ]
  if (round === 1) {
    lines.push(
      'BUILD: one Blender recipe (build_node_group(parameters) for lib/bake_harness.py: input "Vector" = tile coordinate; outputs Colour, Roughness, Metallic, Height) that: (a) lays out rows of boards with random lengths and joints (settings: rows per tile, board length range, joint gap); (b) gives every board its own random window of the displacement map AND the colour map together (random offset along the grain, chosen so a board takes material from inside one source row band, optional left-right flip, optional upside-down flip, small tone and height shifts per board), so no two neighbouring boards look alike and a bigger area does not repeat; (c) hides or makes natural the edges where one window meets the next (a board joint, a gap, or a short blend), and keeps the tile seamless at its own edges; (d) height = the sampled displacement (plus small per-board changes); normal from height at strength 8; (e) MAIN colour sampled from the colour map with the same arrangement as the height (plus small per-board tone shifts); COMPARISON colour made procedurally from the sampled height and per-board tone; (f) roughness from height and stains; metallic 0; (g) a setting tiles_across (1, 2, 4, 8) that makes a bigger area of NEW boards with the same look per dot; (h) a seed setting: a new seed gives a new arrangement.',
      'Show and measure: the default tile at 1254 (all maps, both colour versions); three seeds; a 2 x 2 area at 2508 and a 4 x 4 area (colour at 2508 for the whole area is fine, plus full-size crops); the half-tile shift test at 512 (the default tile must repeat without a seam); a REPEAT test for the big areas: correlation at shifts of one source-map width and one tile, against the background at other shifts, and how often the same piece of the source map is reused and how far apart; a look at every board joint at full size for visible cuts. Score with lib/texture_compare.py against reference wood (overall, colour, height, normal; main and comparison; three seeds) and score the earlier wood recipe\'s best new tile THE SAME WAY (1254 dots) so the comparison is like for like; pixel numbers for transparency only.',
      'Pictures (in sheets/): wood_sheet.jpg = reference | earlier wood recipe new tile | new MAIN | new COMPARISON, with a row of 400 x 400 crops; seeds.jpg; area_4x4.jpg (shrunk) plus area_crops.jpg (full size, including across tile lines); maps.jpg; a lit preview under a low raking light (reuse or adapt recipes/slate_layers/verify_look/lit_preview.py) of reference vs new.',
      'Budget: at most about 25 Blender runs, most at 512-900 while building.'
    )
  } else {
    lines.push(
      'ROUND ' + round + ': the checkers judged your first build. Their findings: ' + JSON.stringify(critique),
      'Fix what they found (most noticeable first), re-bake what changed, re-run the affected tests and scores, re-make the affected sheets, and add a "Round ' + round + '" section to the notes. Budget: about 15 Blender runs.'
    )
  }
  lines.push(
    'Write (or update): ' + WD + '/08 Recipe - wood from your displacement and colour maps - how it is made.md (plain words: what the recipe does with the map, every control with what changing it does and sweep pictures of the two or three most important, results tables, dead ends) and ' + WD + '/08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces.md (when to use a map as source vs pure nodes, how to cut any map into pieces, traps). Save the settings as recipe/settings.json and check it with python3 -I lib/description_audit.py recipe/settings.json --limit-kilobytes 8.',
    'Save your structured result as JSON in ' + WD + '/build_result_round_' + round + '.json and return it.'
  )
  return lines.join('\n')
}

function lookPrompt(build, round) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes, an art director for hand-painted game textures. Judge the new wood strictly. Do not trust the builder\'s words: look at the pictures at full size and measure for yourself.',
    ASK, HOUSE,
    'Write only into ' + WD + '/check_look_round_' + round + '/ (JPEG, under 15 MB). The builder\'s report: ' + JSON.stringify(build),
    'Judge: (1) does the default tile read as the same wood as the reference (yes / nearly / no), main and comparison versions; (2) in the 4 x 4 area, do you see repeats (the same knot, crack, stain or board coming back), cuts where one window of the source meets another, or rows that look stamped; tile it yourself 3 x 3 too and compare; (3) board joints at full size; (4) under a low raking light (bake one yourself if needed), does the relief read as weathered wood; (5) is it clearly better than the earlier wood recipe (recipes/wood/); (6) does the main colour (made from height) look right, or does it need the colour map. Rank the problems, most noticeable first, each with a crop and a concrete fix. Set should_iterate true only if a fix round is clearly worth it.',
    'Return the structured result.',
  ].join('\n')
}

function honestyPrompt(build) {
  return [
    'You are an INDEPENDENT HONESTY CHECKER. Check the wood builder\'s claims. Do not edit its files; write only into ' + WD + '/check_honesty/.',
    ASK, HOUSE,
    'Claims: ' + JSON.stringify(build),
    'Check at least: (1) re-score the default tile (main and comparison) and the earlier wood tile with lib/texture_compare.py and compare with the claims and the guide; (2) re-bake the default ONCE at 1254 from recipe/settings.json and confirm it matches outputs; (3) the big areas are really new arrangements made by the recipe (look at the recipe: per-board random windows from a seed), not the tile repeated or an image made outside Blender; (4) re-run the half-tile test and the repeat measure on the 4 x 4 area; (5) the settings pass description_audit at 8 KB; (6) only the wood displacement map and the wood colour map are read from reference/ (both sampled with the same arrangement in the main version), and the guide says so; (7) every picture and link named in the two 08 guides exists; (8) the guides\' plain-language claims match what the pictures show.',
    'Return claims_hold, concrete problems (file, what is wrong, what it should say) and what you checked.',
  ].join('\n')
}

phase('Research')
const research = await agent(researchPrompt, { ...SONNET, label: 'research: non-repeating surfaces from one map', phase: 'Research', schema: RESEARCH_SCHEMA })

phase('Build')
let build = await agent(buildPrompt(research, null, 1), { ...SONNET, label: 'wood builder, round 1', phase: 'Build', schema: BUILD_SCHEMA })

phase('Check')
let look = await agent(lookPrompt(build, 1), { ...SONNET, label: 'wood look check, round 1', phase: 'Check', schema: LOOK_SCHEMA })
let honesty = await agent(honestyPrompt(build), { ...SONNET, label: 'wood honesty check, round 1', phase: 'Check', schema: HONESTY_SCHEMA })
const history = [{ build, look, honesty }]

const needsFix = (look && look.should_iterate) || (honesty && !honesty.claims_hold)
if (needsFix) {
  log('Checkers asked for a fix round')
  build = await agent(buildPrompt(research, { look, honesty }, 2), { ...SONNET, label: 'wood builder, round 2', phase: 'Build', schema: BUILD_SCHEMA })
  look = await agent(lookPrompt(build, 2), { ...SONNET, label: 'wood look check, round 2', phase: 'Check', schema: LOOK_SCHEMA })
  honesty = await agent(honestyPrompt(build), { ...SONNET, label: 'wood honesty check, round 2', phase: 'Check', schema: HONESTY_SCHEMA })
  history.push({ build, look, honesty })
} else if (honesty && honesty.problems && honesty.problems.length) {
  const fixed = await agent([
    'You are the WOOD CORRECTOR. An honesty checker found these problems in the wood-from-displacement reports and guides: ' + JSON.stringify(honesty),
    HOUSE,
    'Correct every problem in the text files of ' + WD + ' (guides, notes, build_result JSON). Re-run a score only if a number must be re-measured. Do not change the recipe. Reply with a plain list of what you corrected.',
  ].join('\n'), { ...SONNET, label: 'wood corrections', phase: 'Check' })
  history.push({ corrections: fixed })
}
return { research, history }
