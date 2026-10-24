export const meta = {
  name: 'slate-fixes-and-reuse-trials-sonnet',
  description: 'Continue the slate look fixes and the reuse trials (wood, metal, mud, gravel) with Sonnet 5.5 helpers at extra-high effort',
  phases: [
    { title: 'Slate fixes', detail: 'independent look check of round 1, a second round if needed', model: 'sonnet' },
    { title: 'Slate re-bake and check', detail: 'ladder, variations, seeds, area, tests, guides; honesty check; corrections', model: 'sonnet' },
    { title: 'Reuse trials', detail: 'finish wood and metal, build mud and gravel', model: 'sonnet' },
    { title: 'Reuse check and guide', detail: 'independent check of all five trials, then the reuse guide', model: 'sonnet' },
  ],
}

const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const SL = PROC + '/recipes/slate_layers'
const RT = PROC + '/reuse_trials'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const HOUSE = [
  'HOUSE RULES (all helpers):',
  '* Working folder: ' + PROC + ' (cd there in every command; use absolute paths). Blender 5.2.2 is NOT on the search path: use the full path ' + BLENDER + '. Bake with: ' + BLENDER + ' -b --disable-autoexec -t 2 --python lib/bake_harness.py -- RECIPE.py OUT --size N [--normal-reference SURFACE] [--params JSON]. Read lib/bake_harness.py once for its options.',
  '* The machine has only 4 processor cores and ANOTHER helper is baking at the same time: run at most ONE Blender process at a time, always with -t 2. Never use pkill -f or killall (a pattern can match your own shell and kill it, and you could kill the other helper\'s Blender); to stop a run of yours, kill it by its PID.',
  '* The Bash tool stops a foreground command after 10 minutes. Keep single runs under about 9 minutes (bake small while tuning: 512-900 dots); for a longer run use run_in_background: true and wait for it in ONE Bash call with an until-loop on its output file (for example: until grep -q "Blender quit" LOG; do sleep 15; done), never chains of sleep calls.',
  '* Disk is tight: check df -h / before each bake; free space must stay above 1.2 GB. Delete your own superseded bakes; save pictures meant for looking at as JPEG. Use python3 -I for Python that reads pictures.',
  '* Do not edit lib/, reference/, or anything outside the folders your task names. No git. Plain Blender only: no film plugin, no Astra add-on, no extensions, no downloads.',
  '* The reference pictures are a GUIDE only: you may look at them and measure their general character once (palette, feature sizes, shares); you must NOT trace them, store per-element lists, or run an automatic optimiser over many settings to minimise a difference. Hand-tuning (look, change one thing, look again) and small sweeps of one or two settings are fine.',
  '* Do NOT start the test described in "LATER - realistic moss and damage over the painted colour and weathering - NOT STARTED.md".',
  '* Names: full plain words for files and code names; a plain note at the top of every file you create saying what it does. Notes and guides are for a person who is not a programmer: plain everyday words, explain any unavoidable technical word in one sentence, one word per thing. Say what you tested, what you did not, and what you are unsure of; record failures. Never claim something works unless you ran it and looked at the result.',
].join('\n')

const TUNER_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  settings_changes: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, before: { type: 'string' }, after: { type: 'string' }, kept: { type: 'boolean' }, why: { type: 'string' } }, required: ['name', 'before', 'after', 'kept', 'why'] } },
  code_changes: { type: 'array', items: { type: 'string' } },
  measures_table_markdown: { type: 'string' },
  scores_text: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
  failures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'settings_changes', 'code_changes', 'measures_table_markdown', 'scores_text', 'pictures', 'untested', 'failures'] }

const CRITIC_SCHEMA = { type: 'object', properties: {
  problems_status: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, status: { type: 'string', enum: ['fixed', 'better', 'same', 'worse'] }, evidence: { type: 'string' } }, required: ['problem', 'status', 'evidence'] } },
  new_problems: { type: 'array', items: { type: 'string' } },
  reads_as_same_hand: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  overall: { type: 'string' },
  should_iterate: { type: 'boolean' },
  suggested_changes: { type: 'array', items: { type: 'string' } },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['problems_status', 'new_problems', 'reads_as_same_hand', 'overall', 'should_iterate', 'suggested_changes', 'pictures'] }

const REST_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' }, ladder_table_markdown: { type: 'string' }, variations_text: { type: 'string' }, seed_spread_text: { type: 'string' },
  area_text: { type: 'string' }, tests_text: { type: 'string' },
  files_updated: { type: 'array', items: { type: 'string' } }, pictures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } }, failures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'ladder_table_markdown', 'variations_text', 'seed_spread_text', 'area_text', 'tests_text', 'files_updated', 'pictures', 'untested', 'failures'] }

const HONESTY_SCHEMA = { type: 'object', properties: {
  claims_hold: { type: 'boolean' }, problems: { type: 'array', items: { type: 'string' } }, checked: { type: 'array', items: { type: 'string' } },
}, required: ['claims_hold', 'problems', 'checked'] }

const TRIAL_SCHEMA = { type: 'object', properties: {
  surface: { type: 'string' },
  layers_used: { type: 'array', items: { type: 'object', properties: { layer: { type: 'string' }, how: { type: 'string' }, why: { type: 'string' } }, required: ['layer', 'how', 'why'] } },
  new_parts: { type: 'array', items: { type: 'string' } },
  node_counts: { type: 'string' },
  scores: { type: 'string' },
  reads_as_surface: { type: 'string', enum: ['yes', 'partly', 'no'] },
  judgement: { type: 'string' }, sheet: { type: 'string' }, folder: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['surface', 'layers_used', 'new_parts', 'node_counts', 'scores', 'reads_as_surface', 'judgement', 'sheet', 'folder', 'failures', 'untested'] }

const VERIFY_REUSE_SCHEMA = { type: 'object', properties: {
  per_surface: { type: 'array', items: { type: 'object', properties: {
    surface: { type: 'string' }, scores_reproduced: { type: 'boolean' }, snapshot_untouched: { type: 'boolean' }, no_fitting: { type: 'boolean' },
    reads_as_surface: { type: 'string', enum: ['yes', 'partly', 'no'] }, corrected_numbers: { type: 'string' }, problems: { type: 'array', items: { type: 'string' } } },
    required: ['surface', 'scores_reproduced', 'snapshot_untouched', 'no_fitting', 'reads_as_surface', 'corrected_numbers', 'problems'] } },
  overall: { type: 'string' },
}, required: ['per_surface', 'overall'] }

const SYNTH_SCHEMA = { type: 'object', properties: {
  guide_path: { type: 'string' }, overview_picture: { type: 'string' }, short_answer: { type: 'string' }, table_markdown: { type: 'string' },
}, required: ['guide_path', 'overview_picture', 'short_answer', 'table_markdown'] }

const ROUND1 = SL + '/look_fixes/round_1_tuner_result.json'

function criticPrompt(round, tuneSource) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes, an art director for hand-painted game textures. The person saw the slate made of separate layers (one Blender recipe: LAYOUT, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW, COMBINE) and asked for the first look checker\'s fixes to be applied. A tuner has done that. Judge whether the result is better. Do not trust the tuner\'s words: look at the pictures at full size and measure for yourself.',
    HOUSE,
    'Write only into ' + SL + '/verify_look_after_fixes/round_' + round + '/ (JPEG pictures, under 15 MB in total). Do not edit any other file.',
    'Inputs: the reference ' + PROC + '/reference/slate/ (colour.png, normal.png, height_as_uploaded.png); the BEFORE tile ' + SL + '/outputs/default_before_look_fixes/; the AFTER tile ' + SL + '/outputs/default/; the 11 problems the first look checker found, in ' + SL + '/verify_look/LOOK_VERDICT.md; the tuner\'s notes, pictures and measuring script in ' + SL + '/look_fixes/. The tuner\'s report (claims to check): ' + tuneSource,
    'Do: (1) for EACH of the 11 problems decide fixed / better / same / worse, with evidence: a crop picture and a number (you may use look_fixes/measure_look.py but check at least two of its numbers with your own code). (2) Look for NEW problems the fixes caused (for example the slates now too plain, the paint too blurry, too little moss, chips invisible, the relief exaggerated, tiling seams). (3) Render the raking-light check with verify_look/lit_preview.py (it may need the full Blender path) for reference, before and after (full tile and a zoom) and judge the relief. (4) Tile the after tile 3 x 3 and look for repeat landmarks. (5) Say plainly whether an art director would now accept it as the same hand as the reference: yes / nearly / no.',
    'Set should_iterate to true only if a second tuning round is clearly worth it (a regression, a new major problem, or a top problem still clearly visible with a settings fix in reach), and then list concrete suggested changes (setting, from, to, why) and test the most important one yourself on a colour-only 900-dot tile if you can (bake into your folder with damage_work/window_render.py or the harness).',
    'Also save your structured result as JSON in your folder (critic_result.json). Return the structured result.',
  ].join('\n')
}

function tunerRound2Prompt(critic) {
  return [
    'You are the SLATE TUNER, round 2. The person saw the slate made of separate layers and asked for the look checker\'s fixes and its relief changes, re-baked and checked by eye and by score. Round 1 was done by an earlier helper: its full report is in ' + ROUND1 + ' and its notes, measuring script (measure_look.py) and pictures are in ' + SL + '/look_fixes/. The "before" state is kept in ' + SL + '/recipe/settings_before_look_fixes.json and ' + SL + '/outputs/default_before_look_fixes/ (do not change those).',
    HOUSE,
    'Your folders: ' + SL + ' (recipe/settings.json; layer files in layers/ only if a fix truly needs code, recorded in integration/CHANGES_TO_LAYER_FILES.md with the independence test re-run for that layer; your work in ' + SL + '/look_fixes/). Keep slate_layers under 460 MB.',
    'An independent look checker judged round 1. Its findings: ' + JSON.stringify(critic),
    'Fix what it found (regressions first, then new problems, then problems still visible), using the same method: change one thing, bake small, look, measure with look_fixes/measure_look.py, keep only what helps. Then re-bake the 1254 default (colour, 16-bit height, normal, roughness, metallic) into outputs/default/, make the reference-style normal with integration/make_normal.py (strength 7), re-score with lib/texture_compare.py (and pixel_compare for transparency), re-make the before/after pictures (before_after_colour.jpg, before_after_zoom.jpg, before_after_lit.jpg, maps_after.jpg; before = outputs/default_before_look_fixes), and add a "Round 2" section to look_fixes/notes - look fixes round 15.md. Budget: at most about 12 Blender runs.',
    'Save your structured result as JSON in look_fixes/round_2_tuner_result.json. Return the structured result for the state after round 2 (list ALL settings changes since the start of round 1, not only this round).',
  ].join('\n')
}

function restPrompt(tuneSource, critic) {
  return [
    'You are the SLATE RE-BAKER. The look fixes for the layered slate are finished and accepted. Re-make every result that depends on the default settings so the folder and its guides are consistent again.',
    HOUSE,
    'Folder: ' + SL + ' (keep it under 460 MB: delete or JPEG superseded pictures of yours; keep the "before" copies in outputs/default_before_look_fixes). Tuner report: ' + tuneSource + ' Last look check: ' + JSON.stringify(critic),
    'Do, reading the existing scripts in each folder first and reusing them:',
    '1. LADDER (ladder/): re-bake the rungs (layout and joints only, + colour and fade, + moss, + damage = default, and without outline and shadow) at 1254 with the new settings, score them, rebuild ladder_table.md (keep the old table under a heading "before the look fixes") and ladder_sheet.jpg.',
    '2. VARIATIONS (variations/): re-bake the eight variations on top of the NEW default, applying the first look checker\'s variation advice (problem 10 in verify_look/LOOK_VERDICT.md: v6 dark and wet, v5 fresh and clean, v4 faded, v2 more moss now distinct) where it helps by eye; re-score (same-kind colour group) and rebuild contact_sheet.png; keep the old scores in variations.json under "before the look fixes".',
    '3. SEED SPREAD (variations/seed_spread/): the three extra seed sets plus v1 seeds on the new default; mean, lowest, highest.',
    '4. AREA: re-bake the 2 x 2 area (area/area_2x2, 2508 dots, colour and height) and its seam/repeat measures. Do NOT re-bake the 4 x 4 (mark it "before the look fixes" in the folder map).',
    '5. TESTS: the half-tile shift test at 512 on the finished maps (tests/half_tile_layers.py); if any layer FILE was changed, the independence test for that layer (tests/independence_full.py) and say so; one 512 bake to confirm the same look at a smaller size.',
    '6. DEBUG VIEWS: re-bake debug_views/overview_masks_and_colours.png with the new settings.',
    '7. WRITE: recipe/controls.md (re-run recipe/make_controls_table.py), final_report.json (ADD a section "look fixes (round 15)" with every new number; do not delete the earlier numbers), "README - folder map.md" (new folders, what is before/after), and the two guides: in "05 Recipe - slate in layers - how it is made.md" add a section "Round 15 - the look checker\'s fixes" (what each fix does in plain words, before/after measures, before/after pictures look_fixes/before_after_colour.jpg and before_after_lit.jpg, what did not help) and update the results tables to the new numbers with the old ones in a "before" column; correct the reporting errors listed in ' + SL + '/verify/HONESTY_VERDICT.md; in "05 Lessons ..." add what this round taught that carries over to other surfaces.',
    'Budget: about 25 Blender runs, one after another (never two at once). Save your structured result as JSON in look_fixes/rebake_result.json. Return the structured result.',
  ].join('\n')
}

function honestyPrompt(tuneSource, rest) {
  return [
    'You are an INDEPENDENT HONESTY CHECKER. Check that what the slate tuner and re-baker report is true and fairly shown. Do not edit their files; write your notes only into ' + SL + '/verify/after_look_fixes/.',
    HOUSE,
    'Claims to check: tuner ' + tuneSource + ' re-baker ' + JSON.stringify(rest),
    'Check at least: (1) re-score outputs/default with lib/texture_compare.py and compare with every place the numbers are written (final_report.json, the 05 guides, ladder table, notes); (2) re-bake the default ONCE at 1254 from recipe/settings.json and confirm it matches outputs/default (allow 1-2 step dither differences; say so); (3) the before/after pictures are fair: same seeds, same size, same crop, before really is outputs/default_before_look_fixes; (4) python3 -I lib/description_audit.py recipe/settings.json --limit-kilobytes 8 passes and the settings named in the guides match settings.json; (5) any layer-file change is listed in integration/CHANGES_TO_LAYER_FILES.md and its independence test was re-run; (6) the earlier honesty problems in verify/HONESTY_VERDICT.md were really corrected in the guides; (7) the variation and seed-spread scores reproduce (re-score at least three); (8) every link and picture named in the two 05 guides and the folder map exists.',
    'Return claims_hold (true only if no claim is wrong in substance), a list of concrete problems (file, what is wrong, what it should say), and what you checked.',
  ].join('\n')
}

function fixPrompt(honesty) {
  return [
    'You are the SLATE CORRECTOR. An independent honesty checker found these problems in the slate-in-layers reports and guides: ' + JSON.stringify(honesty),
    HOUSE,
    'Correct every problem in the text files of ' + SL + ' (guides, folder map, final_report.json, notes). Re-run a score or bake only if a number must be re-measured. Do not change settings or layer files. Add a short "Corrections after the honesty check" list at the end of look_fixes/notes - look fixes round 15.md. Reply with a plain list of what you corrected.',
  ].join('\n')
}

function trialPrompt(surface) {
  const continuing = (surface === 'wood' || surface === 'metal')
  return [
    'You are the REUSE TRIAL BUILDER for ' + surface.toUpperCase() + '. Question from the person: "How much of the tools can be used on the other textures now?" Your job: show, by building it, how much of the shared layered slate recipe (layers COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW, COMBINE, and the layout-bundle interface) can make a convincing ' + surface + ' texture, and what had to be new.',
    HOUSE,
    continuing ? ('IMPORTANT - YOU ARE CONTINUING: an earlier helper started this trial and was stopped part-way (only because the person switched the helpers to another model). Read "' + RT + '/' + surface + '/STOPPED PART-WAY - read first.md" and everything in the folder first (blender_runs.log, the newest rounds, settings.json, the layout, recipe and any new layer files); check that it is sound, keep what works, and finish. Blender runs already used count towards the budget.') : '',
    'Your folder: ' + RT + '/' + surface + '/ (keep it under 80 MB). Import the shared layers ONLY from ' + RT + '/shared_layers_snapshot/layers (put it first on sys.path; never edit it; its checksums are checked afterwards). The pattern to copy is ' + SL + '/reuse/brick_layers_recipe.py; the bundle and the layer sockets are explained in ' + SL + '/interface/interface.md and the snapshot layer_interface.py. A finished trial to learn from (same task, brick): ' + RT + '/brick/ (notes - brick reuse trial.md, trial_result.json, brick_recipe.py, grime.py, height_rule.py, checks_run.py, final_scores.py, make_brick_sheet.py) - reuse its tools where they fit, and note its lessons (COMBINE\'s height-from-colour rule is slate-only; 640-dot views scored with texture_compare are not like for like, so every reported score must come from 1254-dot bakes; seed choice moves scores a lot, so report three seed sets).',
    'The surveyor\'s inventory and plan for every surface: ' + RT + '/00 Inventory - which tools fit which surface.md and ' + RT + '/inventory_result.json (read the ' + surface + ' part).',
    'Rules: (a) write a small ' + surface + ' LAYOUT that makes the eleven-number bundle (or use the shared slate LAYOUT by settings if that fits better, and say so); (b) use as many shared layers as you can UNCHANGED, changing only their settings; (c) if a shared layer cannot make a needed feature, first try a different meaning with settings (for example MOSS as rust), then a SMALL NEW layer in your folder with the same sockets (layer_interface); only as a last resort copy a shared layer into your folder as <layer>_changed_for_' + surface + '.py and list every change and why; (d) the reference ' + PROC + '/reference/' + surface + '/ is a guide only (measure palette and sizes once; no tracing, no per-element lists, no optimiser; if you take any number from the reference maps, say exactly which and why); (e) at most 12 Blender runs in total, most at 512-640 dots for looking, then the default tile at 1254 with colour, 16-bit height, roughness, metallic, and a normal made from the height with ' + SL + '/integration/make_normal.py at the reference strength (brick 6, wood 8, metal 5, mud 9, gravel 10), for three seed sets; (f) settings in settings.json must pass python3 -I lib/description_audit.py settings.json --limit-kilobytes 8.',
    'Measure: lib/texture_compare.py same-kind scores (overall, colour group, height group) of your 1254 tiles against reference ' + surface + '; and score the surface\'s own earlier small recipe new tile THE SAME WAY (same tool, same size) so the comparison is like for like. A half-tile shift test at 512 (the tile must repeat without a seam). Count nodes: how many come from the shared layers and how many are new (see brick\'s checks_run.py), and lines of code new versus reused.',
    'Pictures: sheet_' + surface + '.jpg = reference | the surface\'s own earlier recipe (new tile) | your layered tile, a 400 x 400 enlarged crop row of the same three, plus a row with each layer\'s mask on this surface; final_seed_sets.jpg; and a 2 x 2 repeat of your tile.',
    'Write "notes - ' + surface + ' reuse trial.md" in your folder: plain words; what was reused unchanged, what only needed settings, what was new and why, scores like for like, does it read as ' + surface + ' (be honest), what is missing to make it better, failures, what you did not test.',
    'Save your structured result as JSON in your folder as trial_result.json. Return the structured result.',
  ].filter(Boolean).join('\n')
}

function verifyReusePrompt(trials) {
  return [
    'You are the INDEPENDENT REUSE CHECKER. Five helpers each tried to make brick, wood, metal, mud and gravel from the shared layers of the layered slate recipe. Check their claims strictly. Write only into ' + RT + '/verify/.',
    HOUSE,
    'Their reports: brick is in ' + RT + '/brick/trial_result.json; the other four: ' + JSON.stringify(trials) + ' (each folder also has trial_result.json and a notes file).',
    'For EACH surface: (1) re-run lib/texture_compare.py on its 1254 colour/height/normal against the reference and on the surface\'s own earlier new tile, and compare with the claimed numbers (give corrected numbers if different); (2) cd ' + RT + '/shared_layers_snapshot && sha256sum -c checksums.txt (snapshot untouched?) and check the trial recipe really imports the shared layers from the snapshot, and that every changed copy and new layer is declared; (3) description_audit on its settings.json (8 KB); (4) no fitting or tracing (look at the code and settings: no per-element lists, no optimiser); judge in particular whether numbers taken from the reference maps (for example brick\'s height box: a straight line fitted once to the reference height curve) stay within "measure the general character once" or cross into fitting, and say so plainly; (5) re-run the node count; (6) look at its sheet and its tile at full size and judge strictly whether it reads as that surface: yes / partly / no, with reasons; (7) check the half-tile test claim on at least two surfaces by re-running it.',
    'Save your structured result as JSON in ' + RT + '/verify/verify_result.json. Return the structured result.',
  ].join('\n')
}

function synthPrompt(trials, verified) {
  return [
    'You are the REUSE GUIDE WRITER. Answer the person\'s question "How much of the tools can be used on the other textures now?" with a plain-language guide, using only checked evidence.',
    HOUSE,
    'Inventory: ' + RT + '/00 Inventory - which tools fit which surface.md and ' + RT + '/inventory_result.json. Trials: brick in ' + RT + '/brick/trial_result.json; others: ' + JSON.stringify(trials),
    'Independent check (wins wherever it differs from the trials): ' + JSON.stringify(verified),
    'Write ' + PROC + '/cookbook/07 Reuse - which tools work on which surfaces.md: start with the answer in a few sentences and one table (surface | share of the recipe that came from shared parts (nodes) | what had to be new | reads as the surface? | same-kind score layered vs own earlier recipe, like for like); then a table of EVERY tool (measuring, baking, seamless noise, sweeps, description checker, cookbook guides, each shared layer, the layout bundle, the tests) with works on brick / wood / metal / mud / gravel (as is / settings only / needs new layout / needs a new layer / not useful); then "what is missing to make the toolkit general", ranked by how many surfaces need it (for example a height rule per surface instead of COMBINE\'s slate-only rule); then one short section per surface with its sheet. Make the overview picture ' + PROC + '/cookbook/pictures/07 Reuse - five surfaces.jpg (one row per surface: reference | own earlier recipe | layered; labelled; at most 1800 dots wide). Add one line linking the new guide to ' + PROC + '/cookbook/06 Cookbook - start here.md.',
    'Return the structured result.',
  ].join('\n')
}

async function slateChain() {
  const round1 = 'the full round-1 report is in the file ' + ROUND1 + ' (read it).'
  let critic = await agent(criticPrompt(1, round1), { ...SONNET, label: 'slate look check, round 1', phase: 'Slate fixes', schema: CRITIC_SCHEMA })
  let tuneSource = round1
  if (critic && critic.should_iterate) {
    log('Look check asked for a second tuning round')
    const tune2 = await agent(tunerRound2Prompt(critic), { ...SONNET, label: 'slate tuner, round 2', phase: 'Slate fixes', schema: TUNER_SCHEMA })
    tuneSource = 'round 1 report in ' + ROUND1 + '; round 2 report: ' + JSON.stringify(tune2)
    critic = await agent(criticPrompt(2, tuneSource), { ...SONNET, label: 'slate look check, round 2', phase: 'Slate fixes', schema: CRITIC_SCHEMA })
  }
  const rest = await agent(restPrompt(tuneSource, critic), { ...SONNET, label: 'slate re-bake the rest and guides', phase: 'Slate re-bake and check', schema: REST_SCHEMA })
  const honesty = await agent(honestyPrompt(tuneSource, rest), { ...SONNET, label: 'slate honesty check', phase: 'Slate re-bake and check', schema: HONESTY_SCHEMA })
  let corrections = null
  if (honesty && (!honesty.claims_hold || (honesty.problems && honesty.problems.length))) {
    corrections = await agent(fixPrompt(honesty), { ...SONNET, label: 'slate corrections', phase: 'Slate re-bake and check' })
  }
  return { critic, tuneSource, rest, honesty, corrections }
}

async function reuseChain() {
  const surfaces = ['metal', 'wood', 'mud', 'gravel']
  const trials = (await parallel(surfaces.map(s => () => agent(trialPrompt(s), { ...SONNET, label: 'reuse trial: ' + s, phase: 'Reuse trials', schema: TRIAL_SCHEMA })))).filter(Boolean)
  log('Reuse trials finished: ' + trials.length + ' of 4 (brick was finished earlier)')
  const verified = await agent(verifyReusePrompt(trials), { ...SONNET, label: 'reuse check (all five)', phase: 'Reuse check and guide', schema: VERIFY_REUSE_SCHEMA })
  const guide = await agent(synthPrompt(trials, verified), { ...SONNET, label: 'reuse guide', phase: 'Reuse check and guide', schema: SYNTH_SCHEMA })
  return { trials, verified, guide }
}

const [slate, reuse] = await parallel([() => slateChain(), () => reuseChain()])
return { slate, reuse }
