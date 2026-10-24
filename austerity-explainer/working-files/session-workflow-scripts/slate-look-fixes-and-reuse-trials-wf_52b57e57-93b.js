export const meta = {
  name: 'slate-look-fixes-and-reuse-trials',
  description: 'Apply the look checker fixes to the layered slate, and test how much of the tools carry over to brick, wood, metal, mud and gravel',
  phases: [
    { title: 'Slate fixes', detail: 'apply the tested and relief fixes, re-bake, independent look check (up to 2 rounds)' },
    { title: 'Slate re-bake and check', detail: 'ladder, variations, seeds, area, tests, guides; honesty check; corrections' },
    { title: 'Reuse inventory', detail: 'which tools fit which surface; a trial plan per surface' },
    { title: 'Reuse trials', detail: 'the shared layers on brick, wood, metal, mud and gravel' },
    { title: 'Reuse check and guide', detail: 'independent check of all five trials, then the reuse guide' },
  ],
}

const PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const SL = PROC + '/recipes/slate_layers'
const RT = PROC + '/reuse_trials'

const HOUSE = [
  'HOUSE RULES (all helpers):',
  '* Working folder: ' + PROC + ' (cd there in every command; use absolute paths). Blender 5.2.2 runs headless on the CPU: blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- RECIPE.py OUT --size N [--normal-reference SURFACE] [--params JSON]. Read lib/bake_harness.py once for its options.',
  '* The machine has only 4 processor cores and ANOTHER helper is baking at the same time: run at most ONE Blender process at a time, always with -t 2. Never use pkill -f or killall (a pattern can match your own shell and kill it, and you could kill the other helper\'s Blender); to stop a run of yours, kill it by its PID.',
  '* The Bash tool stops a foreground command after 10 minutes. Keep single runs under about 9 minutes (bake small while tuning: 512-900 dots); for a longer run use run_in_background: true and wait for it in ONE Bash call with an until-loop on its output file (for example: until grep -q "Blender quit" LOG; do sleep 15; done), never chains of sleep calls.',
  '* Disk is tight: check df -h / before each bake; free space must stay above 1.2 GB. Delete your own superseded bakes; save pictures meant for looking at as JPEG. Use python3 -I for Python that reads pictures.',
  '* Do not edit lib/, reference/, or anything outside the folders your task names. No git. Plain Blender only: no film plugin, no Astra add-on, no extensions, no downloads.',
  '* The reference pictures are a GUIDE only: you may look at them and measure their general character once (palette, feature sizes, shares); you must NOT trace them, store per-element lists, or run an automatic optimiser over many settings to minimise a difference. Hand-tuning (look, change one thing, look again) and small sweeps of one or two settings are fine.',
  '* Do NOT start the test described in "LATER - realistic moss and damage over the painted colour and weathering - NOT STARTED.md".',
  '* Names: full plain words for files and code names; a plain note at the top of every file you create saying what it does. Notes and guides are for a person who is not a programmer: plain everyday words, explain any unavoidable technical word in one sentence, one word per thing. Say what you tested, what you did not, and what you are unsure of; record failures. Never claim something works unless you ran it and looked at the result.',
].join('\n')

const TUNER_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string', description: 'plain-language summary of what changed and how it looks now' },
  settings_changes: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, before: { type: 'string' }, after: { type: 'string' }, kept: { type: 'boolean' }, why: { type: 'string' } }, required: ['name', 'before', 'after', 'kept', 'why'] } },
  code_changes: { type: 'array', items: { type: 'string' } },
  measures_table_markdown: { type: 'string', description: 'the look measures: before, after, reference' },
  scores_text: { type: 'string', description: 'same-kind scores (overall, colour, height) before and after, and pixel numbers for transparency' },
  pictures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
  failures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'settings_changes', 'code_changes', 'measures_table_markdown', 'scores_text', 'pictures', 'untested', 'failures'] }

const CRITIC_SCHEMA = { type: 'object', properties: {
  problems_status: { type: 'array', items: { type: 'object', properties: { problem: { type: 'string' }, status: { type: 'string', enum: ['fixed', 'better', 'same', 'worse'] }, evidence: { type: 'string' } }, required: ['problem', 'status', 'evidence'] } },
  new_problems: { type: 'array', items: { type: 'string' } },
  reads_as_same_hand: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  overall: { type: 'string' },
  should_iterate: { type: 'boolean', description: 'true only if a second tuning round is clearly worth it (a regression, a new major problem, or a top problem still clearly visible with a settings fix in reach)' },
  suggested_changes: { type: 'array', items: { type: 'string' } },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['problems_status', 'new_problems', 'reads_as_same_hand', 'overall', 'should_iterate', 'suggested_changes', 'pictures'] }

const REST_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  ladder_table_markdown: { type: 'string' },
  variations_text: { type: 'string' },
  seed_spread_text: { type: 'string' },
  area_text: { type: 'string' },
  tests_text: { type: 'string', description: 'half-tile, independence (if any layer code changed), resolution' },
  files_updated: { type: 'array', items: { type: 'string' } },
  pictures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
  failures: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'ladder_table_markdown', 'variations_text', 'seed_spread_text', 'area_text', 'tests_text', 'files_updated', 'pictures', 'untested', 'failures'] }

const HONESTY_SCHEMA = { type: 'object', properties: {
  claims_hold: { type: 'boolean' },
  problems: { type: 'array', items: { type: 'string' } },
  checked: { type: 'array', items: { type: 'string' } },
}, required: ['claims_hold', 'problems', 'checked'] }

const INVENTORY_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  tools: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, kind: { type: 'string' }, what_it_does: { type: 'string' },
    brick: { type: 'string' }, wood: { type: 'string' }, metal: { type: 'string' }, mud: { type: 'string' }, gravel: { type: 'string' }, evidence: { type: 'string' } },
    required: ['name', 'kind', 'what_it_does', 'brick', 'wood', 'metal', 'mud', 'gravel', 'evidence'] } },
  surfaces: { type: 'array', items: { type: 'object', properties: {
    surface: { type: 'string' }, features: { type: 'array', items: { type: 'string' } }, plan: { type: 'string' }, baseline: { type: 'string' } },
    required: ['surface', 'features', 'plan', 'baseline'] } },
  inventory_file: { type: 'string' },
}, required: ['summary', 'tools', 'surfaces', 'inventory_file'] }

const TRIAL_SCHEMA = { type: 'object', properties: {
  surface: { type: 'string' },
  layers_used: { type: 'array', items: { type: 'object', properties: { layer: { type: 'string' }, how: { type: 'string', description: 'unchanged / settings only / changed copy / not used' }, why: { type: 'string' } }, required: ['layer', 'how', 'why'] } },
  new_parts: { type: 'array', items: { type: 'string' } },
  node_counts: { type: 'string', description: 'nodes from the shared layers vs new nodes, and how counted' },
  scores: { type: 'string', description: 'same-kind overall, colour group, height group for the layered tile AND for the surface own earlier recipe new tile, measured the same way' },
  reads_as_surface: { type: 'string', enum: ['yes', 'partly', 'no'] },
  judgement: { type: 'string' },
  sheet: { type: 'string' },
  folder: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
}, required: ['surface', 'layers_used', 'new_parts', 'node_counts', 'scores', 'reads_as_surface', 'judgement', 'sheet', 'folder', 'failures', 'untested'] }

const VERIFY_REUSE_SCHEMA = { type: 'object', properties: {
  per_surface: { type: 'array', items: { type: 'object', properties: {
    surface: { type: 'string' }, scores_reproduced: { type: 'boolean' }, snapshot_untouched: { type: 'boolean' }, no_fitting: { type: 'boolean' },
    reads_as_surface: { type: 'string', enum: ['yes', 'partly', 'no'] }, corrected_numbers: { type: 'string' }, problems: { type: 'array', items: { type: 'string' } } },
    required: ['surface', 'scores_reproduced', 'snapshot_untouched', 'no_fitting', 'reads_as_surface', 'corrected_numbers', 'problems'] } },
  overall: { type: 'string' },
}, required: ['per_surface', 'overall'] }

const SYNTH_SCHEMA = { type: 'object', properties: {
  guide_path: { type: 'string' }, overview_picture: { type: 'string' },
  short_answer: { type: 'string', description: '5-8 plain sentences answering: how much of the tools can be used on the other textures now' },
  table_markdown: { type: 'string' },
}, required: ['guide_path', 'overview_picture', 'short_answer', 'table_markdown'] }

function tunerPrompt(round, critic, previous) {
  const common = [
    'You are the SLATE TUNER. The person saw the slate made of separate layers (one Blender recipe: LAYOUT, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW, COMBINE) and said: apply the look checker\'s fixes and its relief changes, re-bake all the maps and check them by eye and by score.',
    HOUSE,
    'Your folders: ' + SL + ' (you may change recipe/settings.json, and layer files in layers/ only if a fix truly needs code; put your work in ' + SL + '/look_fixes/). Keep the whole slate_layers folder under 460 MB.',
    'Read first: ' + SL + '/README - folder map.md, ' + SL + '/verify_look/LOOK_VERDICT.md (the 11 problems with suggested settings; t1-t4 in verify_look/tests were colour-only 900-dot tests), ' + SL + '/recipe/settings.json, ' + SL + '/recipe/controls.md (all 176 controls with ranges; settings not in settings.json keep the layer file starting value), ' + SL + '/integration/CHANGES_TO_LAYER_FILES.md, and the results and dead-ends parts of ' + SL + '/05 Recipe - slate in layers - how it is made.md.',
  ]
  if (round === 1) {
    return common.concat([
      'STEPS:',
      '1. Save the starting point so before/after is fair: copy recipe/settings.json to recipe/settings_before_look_fixes.json, and outputs/default (colour, height, normal, roughness, metallic, scores) to outputs/default_before_look_fixes/. Do not change those copies afterwards.',
      '2. Write ONE measuring script look_fixes/measure_look.py that reproduces the look checker\'s numbers at 900 dots: median colour gradient, side-to-side over up-down gradient energy, olive share, tan share, largest moss clump and lightness spread inside moss, brightest slate mean lightness (reference max 34.6), and on the normal/height maps the 99th-percentile tilt and average up-down vs side-to-side slope. Calibrate it first: on the old default it must give about 10.0 / 1.18 / 10.7% / 2.1%, on the reference about 5.5 / 0.83 / 6.4% / 1.0% (the existing helpers integration/share_olive.py and damage_work/measure_share.py may help). Write down any number you cannot reproduce.',
      '3. Apply the fixes in this order, baking at 640-900 dots and LOOKING at the result (side by side with the reference and the old default) after each step: (a) the tested combined set t4_all (problems 1, 2, 3, 4 (corner_bottom_factor, ragged_bottom), 6 (black_drips, shadow_drip), 8 (crack_amount 0 for the default), 9 (lichen_amount)); (b) the relief changes of problem 5 (combine.tone_blend 0.7 to 0.45, outline_and_shadow.lip_height 0.04 to 0.1, damage.sink_depth 1 to 1.6, moss.raise 1 to 2.5) judged on height and normal maps AND under a low raking light with verify_look/lit_preview.py; (c) the untested ones: shadow_tiers 4 to 2, the pale outlier slates (outlier_size or outlier_share), damage side_share 0.12 to 0.05, layout bottom_tilt 0.02 to 0.035, a wider moss palette (a darker and a lighter moss tone, about #23241c and #63614a), and problem 11 (moss cut off with straight edges at side joints; only if a small change does it). Keep a change only if it helps by eye and does not spoil something else; write down every change you tried, kept or dropped, and why.',
      '4. Bake the finished default tile at 1254 dots (colour, 16-bit height, normal, roughness, metallic) into outputs/default/, make the reference-style normal with integration/make_normal.py (strength 7), score it with lib/texture_compare.py against slate (overall, colour group, height group; save the JSON) and lib/pixel_compare.py (for transparency only), and run measure_look.py on before / after / reference.',
      '5. Make pictures in look_fixes/: before_after_colour.jpg (reference | before | after, full tile), before_after_zoom.jpg (the same 0.4-tile crop of each at full size), before_after_lit.jpg (raking light, reference | before | after) and maps_after.jpg (the five maps).',
      '6. If you changed a layer file: record every change in integration/CHANGES_TO_LAYER_FILES.md and re-run that layer\'s independence test (tests/independence_full.py for that layer only, 384 dots) and the half-tile test at 512 (tests/half_tile_layers.py); report the result.',
      '7. Write look_fixes/notes - look fixes round 15.md: plain-language list of what changed, the measures table (before, after, reference), scores before and after, what you did not test, failures.',
      'Budget: at most about 18 Blender runs. Do NOT re-bake the ladder, variations, seed spread, areas or guides: a later helper does that once the look is accepted.',
      'Return the structured result (paths absolute).',
    ]).join('\n')
  }
  return common.concat([
    'This is ROUND 2. Round 1 result (your earlier work): ' + JSON.stringify(previous),
    'An independent look checker then judged round 1. Its findings: ' + JSON.stringify(critic),
    'Fix what it found (regressions first, then new problems, then problems still visible), using the same method: change, bake small, look, measure with look_fixes/measure_look.py, keep only what helps. Then re-bake the 1254 default and all five maps and the normal, re-score, re-make the four before/after pictures (before = outputs/default_before_look_fixes), and add a "Round 2" section to look_fixes/notes - look fixes round 15.md. Budget: at most about 12 Blender runs.',
    'Return the structured result for the state after round 2 (list ALL settings changes since the start, not only this round).',
  ]).join('\n')
}

function criticPrompt(round, tune) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes, an art director for hand-painted game textures. Judge whether the look fixes made the layered slate better. Do not trust the tuner\'s words: look at the pictures at full size and measure for yourself.',
    HOUSE,
    'Write only into ' + SL + '/verify_look_after_fixes/round_' + round + '/ (JPEG pictures, under 15 MB in total). Do not edit any other file.',
    'Inputs: the reference ' + PROC + '/reference/slate/ (colour.png, normal.png, height_as_uploaded.png); the BEFORE tile ' + SL + '/outputs/default_before_look_fixes/; the AFTER tile ' + SL + '/outputs/default/; the 11 problems the first look checker found, in ' + SL + '/verify_look/LOOK_VERDICT.md; the tuner\'s notes and measuring script in ' + SL + '/look_fixes/. The tuner reported (treat as claims to check): ' + JSON.stringify(tune),
    'Do: (1) for EACH of the 11 problems decide fixed / better / same / worse, with evidence: a crop picture and a number (you may use look_fixes/measure_look.py but check at least two of its numbers with your own code). (2) Look for NEW problems the fixes caused (for example the slates now too plain, the paint too blurry, too little moss, chips invisible, the relief exaggerated, tiling seams). (3) Render the raking-light check with verify_look/lit_preview.py for reference, before and after (full tile and a zoom) and judge the relief. (4) Tile the after tile 3 x 3 and look for repeat landmarks. (5) Say plainly whether an art director would now accept it as the same hand as the reference: yes / nearly / no.',
    'Set should_iterate to true only if a second tuning round is clearly worth it (a regression, a new major problem, or a top problem still clearly visible with a settings fix in reach), and then list concrete suggested changes (setting, from, to, why) and test the most important one yourself on a colour-only 900-dot tile if you can (bake into your folder with damage_work/window_render.py or the harness).',
    'Return the structured result.',
  ].join('\n')
}

function restPrompt(tune, critic) {
  return [
    'You are the SLATE RE-BAKER. The look fixes for the layered slate are finished and accepted. Re-make every result that depends on the default settings so the folder and its guides are consistent again.',
    HOUSE,
    'Folder: ' + SL + ' (keep it under 460 MB: delete or JPEG superseded pictures of yours; keep the "before" copies in outputs/default_before_look_fixes). Tuner result: ' + JSON.stringify(tune) + ' Last look check: ' + JSON.stringify(critic),
    'Do, reading the existing scripts in each folder first and reusing them:',
    '1. LADDER (ladder/): re-bake the rungs (layout and joints only, + colour and fade, + moss, + damage = default, and without outline and shadow) at 1254 with the new settings, score them, rebuild ladder_table.md (keep the old table under a heading "before the look fixes") and ladder_sheet.jpg.',
    '2. VARIATIONS (variations/): re-bake the eight variations on top of the NEW default, applying the first look checker\'s variation advice (problem 10 in verify_look/LOOK_VERDICT.md: v6 dark and wet, v5 fresh and clean, v4 faded, v2 more moss now distinct) where it helps by eye; re-score (same-kind colour group) and rebuild contact_sheet.png; keep the old scores in variations.json under "before the look fixes".',
    '3. SEED SPREAD (variations/seed_spread/): the three extra seed sets plus v1 seeds on the new default; mean, lowest, highest.',
    '4. AREA: re-bake the 2 x 2 area (area/area_2x2, 2508 dots, colour and height) and its seam/repeat measures. Do NOT re-bake the 4 x 4 (mark it "before the look fixes" in the folder map).',
    '5. TESTS: the half-tile shift test at 512 on the finished maps (tests/half_tile_layers.py); if the tuner changed any layer FILE, the independence test for that layer (tests/independence_full.py) and say so; one 512 bake to confirm the same look at a smaller size.',
    '6. DEBUG VIEWS: re-bake debug_views/overview_masks_and_colours.png with the new settings.',
    '7. WRITE: recipe/controls.md (re-run recipe/make_controls_table.py), final_report.json (ADD a section "look fixes (round 15)" with every new number; do not delete the earlier numbers), "README - folder map.md" (new folders, what is before/after), and the two guides: in "05 Recipe - slate in layers - how it is made.md" add a section "Round 15 - the look checker\'s fixes" (what each fix does in plain words, before/after measures, before/after pictures look_fixes/before_after_colour.jpg and before_after_lit.jpg, what did not help) and update the results tables to the new numbers with the old ones in a "before" column; correct the reporting errors listed in ' + SL + '/verify/HONESTY_VERDICT.md; in "05 Lessons ..." add what this round taught that carries over to other surfaces.',
    'Budget: about 25 Blender runs; run them one after another (never two at once).',
    'Return the structured result.',
  ].join('\n')
}

function honestyPrompt(tune, rest) {
  return [
    'You are an INDEPENDENT HONESTY CHECKER. Check that what the slate tuner and re-baker report is true and fairly shown. Do not edit their files; write your notes only into ' + SL + '/verify/after_look_fixes/.',
    HOUSE,
    'Claims to check: tuner ' + JSON.stringify(tune) + ' re-baker ' + JSON.stringify(rest),
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

const INVENTORY_PROMPT = [
  'You are the REUSE SURVEYOR. The person asked: "How much of the tools can be used on the other textures now?" The tools are everything built so far in ' + PROC + ': the shared tools in lib/ and lib/contrib/, the cookbook (cookbook/: eight 06 tool guides and the new-surface checklist), the per-surface recipes (recipes/<brick|slate|wood|metal|mud|gravel>/ with their 04 guides, analysis, generators, scores), and the slate made of separate layers (recipes/slate_layers/: the layout bundle interface in interface/interface.md, the layer files in layers/, the tests, and reuse/ where the layers already ran on a quick brick layout).',
  HOUSE,
  'Write only into ' + RT + '/ (except the snapshot folder, which you must not edit). A frozen copy of the shared layer files is in ' + RT + '/shared_layers_snapshot/ (read its README); the trials will import the layers from there.',
  'Do (reading, plus small checks; no long bakes): (1) list every tool with what it does in one plain sentence and, for each of brick, wood, metal, mud, gravel, whether it works "as is", "settings only", "needs a new layout", "needs a new layer", "needs code changes" or "not useful", with evidence (for example: which earlier builds already used it; a two-minute check). (2) For each of the five surfaces read its 04 Recipe and 04 Lessons guides and analysis, list the visible features a layered recipe would need (for example metal: plate seams, rivets, rust blooms and streaks, flaking paint), map each feature to a shared layer (and whether the layer\'s meaning can be re-used, for example the MOSS layer as rust with rust colours) or to a missing layer, and write a concrete TRIAL PLAN: how to make the eleven-number layout bundle for that surface (pieces = bricks, boards, plates, stones, or for mud whatever makes sense, and what to do if a surface has no pieces), which shared layers to run and with which kind of settings, what small new layer (if any) is truly needed, the palette and sizes to measure once from the reference as a guide, and the BASELINE: the surface\'s own earlier small recipe and its new-tile same-kind score, with the path to that new-tile colour picture, so the trial can be compared like for like. For brick, start from recipes/slate_layers/reuse/ (brick_layers_recipe.py and settings_round_2).',
  'Save it as ' + RT + '/00 Inventory - which tools fit which surface.md (plain words; tables) and return the structured result.',
].join('\n')

function trialPrompt(surface, inv) {
  const plan = inv && inv.surfaces ? inv.surfaces.find(s => (s.surface || '').toLowerCase().includes(surface)) : null
  return [
    'You are the REUSE TRIAL BUILDER for ' + surface.toUpperCase() + '. Question from the person: "How much of the tools can be used on the other textures now?" Your job: show, by building it, how much of the shared layered slate recipe (layers COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW, COMBINE, and the layout-bundle interface) can make a convincing ' + surface + ' texture, and what had to be new.',
    HOUSE,
    'Your folder: ' + RT + '/' + surface + '/ (keep it under 80 MB). Import the shared layers ONLY from ' + RT + '/shared_layers_snapshot/layers (put it first on sys.path; never edit it; its checksums are checked afterwards). The pattern to copy is ' + SL + '/reuse/brick_layers_recipe.py (it builds a small brick layout that hands the eleven layout numbers to the unchanged layers, and the bake harness loads it); the bundle and the layer sockets are explained in ' + SL + '/interface/interface.md and the snapshot layer_interface.py.',
    'The surveyor\'s plan for ' + surface + ': ' + JSON.stringify(plan),
    'The whole inventory is in ' + RT + '/00 Inventory - which tools fit which surface.md.',
    'Rules: (a) write a small ' + surface + ' LAYOUT that makes the eleven-number bundle; (b) use as many shared layers as you can UNCHANGED, changing only their settings; (c) if a shared layer cannot make a needed feature, first try a different meaning with settings (for example MOSS as rust), then a SMALL NEW layer in your folder with the same sockets (layer_interface); only as a last resort copy a shared layer into your folder as <layer>_changed_for_' + surface + '.py and list every change and why; (d) the reference ' + PROC + '/reference/' + surface + '/ is a guide only (measure palette and sizes once; no tracing, no per-element lists, no optimiser); (e) at most 12 Blender runs, most at 512-640 dots, then the default tile at 1254 with colour, 16-bit height, roughness, metallic, and a normal made from the height with ' + SL + '/integration/make_normal.py at the reference strength (brick 6, wood 8, metal 5, mud 9, gravel 10); (f) settings in settings.json must pass python3 -I lib/description_audit.py settings.json --limit-kilobytes 8.',
    'Measure: lib/texture_compare.py same-kind scores (overall, colour group, height group) of your 1254 tile against reference ' + surface + '; and score the surface\'s own earlier small recipe new tile THE SAME WAY (same tool, same size) so the comparison is like for like. A half-tile shift test at 512 (the tile must repeat without a seam). Count nodes: how many come from the shared layers and how many are new (start from ' + SL + '/damage_work/count_nodes.py or ' + SL + '/integration/count_tools.py), and lines of code new versus reused.',
    'Pictures: sheet_' + surface + '.jpg = reference | the surface\'s own earlier recipe (new tile) | your layered tile, plus a row with each layer\'s mask on this surface; and a 2 x 2 repeat of your tile.',
    'Write "notes - ' + surface + ' reuse trial.md" in your folder: plain words; what was reused unchanged, what only needed settings, what was new and why, scores like for like, does it read as ' + surface + ' (be honest), what is missing to make it better, failures, what you did not test.',
    'Return the structured result.',
  ].join('\n')
}

function verifyReusePrompt(trials) {
  return [
    'You are the INDEPENDENT REUSE CHECKER. Five helpers each tried to make brick, wood, metal, mud and gravel from the shared layers of the layered slate recipe. Check their claims strictly. Write only into ' + RT + '/verify/.',
    HOUSE,
    'Their reports: ' + JSON.stringify(trials),
    'For EACH surface: (1) re-run lib/texture_compare.py on its 1254 colour/height/normal against the reference and on the surface\'s own earlier new tile, and compare with the claimed numbers (give corrected numbers if different); (2) cd ' + RT + '/shared_layers_snapshot && sha256sum -c checksums.txt (snapshot untouched?) and check the trial recipe really imports the shared layers from the snapshot, and that every changed copy and new layer is declared; (3) description_audit on its settings.json (8 KB); (4) no fitting or tracing (look at the code and settings: no per-element lists, no optimiser); (5) re-run the node count; (6) look at its sheet and its tile at full size and judge strictly whether it reads as that surface: yes / partly / no, with reasons; (7) check the half-tile test claim on one surface by re-running it.',
    'Return the structured result.',
  ].join('\n')
}

function synthPrompt(inv, trials, verified) {
  return [
    'You are the REUSE GUIDE WRITER. Answer the person\'s question "How much of the tools can be used on the other textures now?" with a plain-language guide, using only checked evidence.',
    HOUSE,
    'Inventory: ' + JSON.stringify(inv),
    'Trials: ' + JSON.stringify(trials),
    'Independent check (wins wherever it differs from the trials): ' + JSON.stringify(verified),
    'Write ' + PROC + '/cookbook/07 Reuse - which tools work on which surfaces.md: start with the answer in a few sentences and one table (surface | share of the recipe that came from shared parts (nodes) | what had to be new | reads as the surface? | same-kind score layered vs own earlier recipe, like for like); then a table of EVERY tool (measuring, baking, seamless noise, sweeps, description checker, cookbook guides, each shared layer, the layout bundle, the tests) with works on brick / wood / metal / mud / gravel (as is / settings only / needs new layout / needs a new layer / not useful); then "what is missing to make the toolkit general", ranked by how many surfaces need it; then one short section per surface with its sheet. Make the overview picture ' + PROC + '/cookbook/pictures/07 Reuse - five surfaces.jpg (one row per surface: reference | own earlier recipe | layered; labelled; at most 1800 dots wide). Add one line linking the new guide to ' + PROC + '/cookbook/06 Cookbook - start here.md.',
    'Return the structured result.',
  ].join('\n')
}

async function slateChain() {
  phase('Slate fixes')
  let tune = await agent(tunerPrompt(1, null, null), { label: 'slate tuner, round 1', phase: 'Slate fixes', schema: TUNER_SCHEMA })
  let critic = await agent(criticPrompt(1, tune), { label: 'slate look check, round 1', phase: 'Slate fixes', schema: CRITIC_SCHEMA })
  const rounds = [{ tune, critic }]
  if (critic && critic.should_iterate) {
    log('Look check asked for a second tuning round')
    tune = await agent(tunerPrompt(2, critic, tune), { label: 'slate tuner, round 2', phase: 'Slate fixes', schema: TUNER_SCHEMA })
    critic = await agent(criticPrompt(2, tune), { label: 'slate look check, round 2', phase: 'Slate fixes', schema: CRITIC_SCHEMA })
    rounds.push({ tune, critic })
  }
  const rest = await agent(restPrompt(tune, critic), { label: 'slate re-bake the rest and guides', phase: 'Slate re-bake and check', schema: REST_SCHEMA })
  const honesty = await agent(honestyPrompt(tune, rest), { label: 'slate honesty check', phase: 'Slate re-bake and check', schema: HONESTY_SCHEMA })
  let corrections = null
  if (honesty && (!honesty.claims_hold || (honesty.problems && honesty.problems.length))) {
    corrections = await agent(fixPrompt(honesty), { label: 'slate corrections', phase: 'Slate re-bake and check' })
  }
  return { rounds, rest, honesty, corrections }
}

async function reuseChain() {
  const inv = await agent(INVENTORY_PROMPT, { label: 'reuse inventory', phase: 'Reuse inventory', schema: INVENTORY_SCHEMA })
  const surfaces = ['brick', 'wood', 'metal', 'mud', 'gravel']
  const trials = (await parallel(surfaces.map(s => () => agent(trialPrompt(s, inv), { label: 'reuse trial: ' + s, phase: 'Reuse trials', schema: TRIAL_SCHEMA })))).filter(Boolean)
  log('Reuse trials finished: ' + trials.length + ' of 5')
  const verified = await agent(verifyReusePrompt(trials), { label: 'reuse check (all five)', phase: 'Reuse check and guide', schema: VERIFY_REUSE_SCHEMA })
  const guide = await agent(synthPrompt(inv, trials, verified), { label: 'reuse guide', phase: 'Reuse check and guide', schema: SYNTH_SCHEMA })
  return { inv, trials, verified, guide }
}

const [slate, reuse] = await parallel([() => slateChain(), () => reuseChain()])
return { slate, reuse }
