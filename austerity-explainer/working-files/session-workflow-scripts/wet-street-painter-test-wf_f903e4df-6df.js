export const meta = {
  name: 'wet-street-painter-test',
  description: 'Repaint the wet lockout plate once with fal (Flux 3 edit, hard limit US$0.30) using a painter brief changed to keep wetness; test it in a copy of the film stage; independent look check',
  phases: [
    { title: 'Painter test', detail: 'new wet brief, one repaint, line-up, stage check, measures', model: 'sonnet' },
    { title: 'Check', detail: 'fresh-eyes look check and ledger check', model: 'sonnet' },
  ],
}

const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const SW = PROC + '/street_wet'
const PT = SW + '/painter_test'
const AE = '/home/user/Music/austerity-explainer'
const KIT = AE + '/film-kit'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const HOUSE = [
  'HOUSE RULES:',
  '* The film project ' + AE + ' is the person\'s repository: READ it freely but NEVER change, add or delete anything there; copy what you need into your own folder. No git.',
  '* Blender 5.2.2 is at ' + BLENDER + ' (always -b --disable-autoexec -t 2, one process at a time; never pkill -f or killall). The Bash tool stops a foreground command after 10 minutes: use run_in_background and ONE until-loop wait for longer runs. Use python3 -I for Python that reads pictures. Chromium and Playwright are installed for the stage (PLAYWRIGHT_BROWSERS_PATH is set; do not run playwright install).',
  '* Disk: free space must stay above 1.2 GB (check df -h /). Keep your folder under 120 MB; JPEG for pictures meant for looking.',
  '* Names: full plain words; a plain note at the top of every file you create. Notes are for a person who is not a programmer: plain everyday words, explain any unavoidable technical word in one sentence, one word per thing. Say what you tested, what you did not, and what you are unsure of; record failures. Never claim something works unless you ran it and looked at the result.',
].join('\n')

const CONTEXT = [
  'BACKGROUND: the film shows the pit village street by drawing a "plate" (a picture rendered from the 3D street in Blender EEVEE), having an image model repaint it in the series\' hand-painted style ("the painter": Flux 3 edit on fal, model blackforestlabs/flux-3/edit-image, sent the plate as image 1 and the series\' style picture as image 2), lining the painting up with the plate (' + KIT + '/paper-film/tools/align_painting.py) and shining it back onto the 3D set in the three.js stage (' + KIT + '/paper-film/scenes/projected-set.js). How earlier paintings were made, with their full prompts and settings: ' + KIT + '/assets/models/pit-village/notice-corner-paintings.json (and the lockout painting ' + KIT + '/assets/models/pit-village/lockout-painted.jpg; look in the project story ' + AE + '/project-notes/Austerity explainer - project story.md, log 29 and 32, and in ' + KIT + '/paper-film/blender/pit-village/ for its prompt).',
  'A helper then built a WETNESS layer for the street and drew a full-size WET plate of the lockout shot: ' + SW + '/work/r35/main_wet_plate.png (1536 x 2730, EEVEE, 32 samples; the film\'s lockout shot file with its props). Read ' + SW + '/09 Recipe - wetness layer and specular map for the street - how it is made.md (especially round 2 and the "painter" notes) and the last check ' + SW + '/check_round_2/ to know what the plate shows and its known weak spots (walls barely read wet at plate size; the brazier-lit foreground reads as polished tile with a blown-out glare pool; props stand dry). Its key finding: the .glb maps do not reach the film; the wet look the audience sees is whatever the painter paints from the wet plate. The old painter brief says "matte painted finish" and bans "puddles or reflections" (a wet ground was once repainted dry).',
].join('\n')

const LEDGER_RULE = 'MONEY: the person approved ONE repaint of the wet lockout plate (about 10 US cents). Hard limit: US$0.30 in total for this whole job. Before the paid call, look up the price (load the Fal tools with ToolSearch, for example "+Fal pricing", "+Fal upload", "+Fal run"; use get_pricing or estimate_cost). Make exactly ONE repaint; a second call is allowed only if the first fails for a technical reason (error, timeout, empty or broken result), never just to get a nicer picture. Keep a ledger ' + PT + '/spending.md (model, settings, price, running total, request id).'

const PAINTER_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  brief_changes: { type: 'string', description: 'what was removed, added and kept in the painter brief, and why' },
  prompt: { type: 'string' },
  settings: { type: 'string' },
  cost_usd: { type: 'number' },
  request_ids: { type: 'array', items: { type: 'string' } },
  wet_survival: { type: 'string', description: 'which wet cues survived the repaint (road sheen, lamp reflections, gutter puddles and their mirrored houses, wet joint lines, darker wall feet) and which were lost, with measures (for example brightness ratios on the road and walls, overlap of bright reflection areas between plate and painting) and crops' },
  other_changes: { type: 'string', description: 'anything the painter added, removed, moved or broke; style match to the series' },
  stage_check: { type: 'string', description: 'the painting projected on a copy of the stage: plate view and a moved view, how the wet look holds when the camera moves' },
  pictures: { type: 'array', items: { type: 'string' } },
  recommendation: { type: 'string', description: 'plain: is this good enough to use, and what would improve it (brief, plate or stage), each with its cost' },
  failures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'brief_changes', 'prompt', 'settings', 'cost_usd', 'request_ids', 'wet_survival', 'other_changes', 'stage_check', 'pictures', 'recommendation', 'failures', 'untested'] }

const LOOK_SCHEMA = { type: 'object', properties: {
  reads_as_wet: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  fits_the_series_style: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  problems: { type: 'array', items: { type: 'string' } },
  claims_checked: { type: 'array', items: { type: 'string' } },
  ledger_ok: { type: 'boolean' },
  overall: { type: 'string' },
  next_step: { type: 'string', description: 'one recommended next step, with its cost' },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['reads_as_wet', 'fits_the_series_style', 'problems', 'claims_checked', 'ledger_ok', 'overall', 'next_step', 'pictures'] }

const painterPrompt = [
  'You are the PAINTER TEST HELPER. The person (not a programmer) said: "Do it" to this proposal: "One painter test of the wet street (about 10 US cents): change the painter\'s brief to keep the wet sheen, lamp reflections and puddles, repaint the wet lockout plate once, and see whether the wet look survives."',
  HOUSE, CONTEXT, LEDGER_RULE,
  'Your folder: ' + PT + '.',
  'STEPS: (1) Find the exact prompt, settings and style picture used for the existing lockout painting (and the notice-corner one as a second example), and the dry lockout plate it was made from if it still exists. (2) Write the new WET brief by changing the old one as little as possible: remove "matte painted finish" and every ban on puddles or reflections; add plainly that the street is wet after rain and that the painter must KEEP, exactly where image 1 has them, the wet sheen on the setts, the lamp and window reflections on the road, the puddles in the gutter and low spots with the houses mirrored in them, the wet dark joint lines and the darker wet foot of the walls, painted in the series\' style (painted reflections, not photographic); keep everything else the old brief protects (camera, shapes, props, no additions). Save old and new brief side by side with the differences marked. (3) Look up the price, upload the wet plate and the style picture, make the ONE repaint with the same settings as before (2k, png) and save the result and the request id. (4) Line the painting up with the plate using a COPY of align_painting.py (record how well it lines up). (5) Compare: wet plate | wet painting | the existing dry lockout painting, full and 100% crops of the road near and far, the gutter, a wall foot, the brazier area; measure which wet cues survived (road brightness and sheen against the dry painting, overlap of the bright reflection areas between plate and painting, puddle places, wall foot darkness) and look for anything added, removed, moved or broken, and how well it matches the series\' style. (6) Stage: in a COPY of the stage files (' + SW + '/stage_test/ exists from the earlier helper; reuse it), project the new painting the way the film does and render the plate view and a moved view (for example 1.4 m forward, 0.3 m right), and say how the wet look holds when the camera moves. (7) Write ' + PT + '/notes - wet street painter test.md and save your structured result as ' + PT + '/result.json.',
  'Return the structured result.',
].join('\n')

function lookPrompt(test) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes (a film art director for a hand-painted explainer series). Judge the wet street painting strictly and check the helper\'s claims. Write only into ' + PT + '/check/.',
    HOUSE, CONTEXT,
    'The helper\'s report: ' + JSON.stringify(test),
    'Judge: does the painting read as a wet street after rain at dusk in 1926; does it fit the series\' painted style (compare with the style picture and the existing paintings); which wet cues survived; did the painter add, remove, move or break anything (compare outlines with the plate); does the wet look hold in the stage\'s moved view; is the glare or anything else distracting. Check that the ledger adds up and stays under US$0.30 and that only the allowed calls were made (Fal request history if you can read it), and re-measure two of the helper\'s numbers. Give ONE recommended next step with its cost.',
    'Return the structured result.',
  ].join('\n')
}

phase('Painter test')
const test = await agent(painterPrompt, { ...SONNET, label: 'wet plate repaint test', phase: 'Painter test', schema: PAINTER_SCHEMA })
phase('Check')
const look = await agent(lookPrompt(test), { ...SONNET, label: 'painting look check', phase: 'Check', schema: LOOK_SCHEMA })
return { test, look }
