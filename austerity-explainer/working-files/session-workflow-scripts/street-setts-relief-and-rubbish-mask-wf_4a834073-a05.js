export const meta = {
  name: 'street-setts-relief-and-rubbish-mask',
  description: 'Make the road setts keep their 3D look under every lighting and wetness, then add a rubbish mask and rubbish along the gutters and building feet of the pit village street (copy only); fresh-eyes checks and one fix round',
  phases: [
    { title: 'Study', detail: 'why the setts lose their 3D look; where rubbish gathers in a 1926 pit village; how people do both in Blender today; plan and lighting test set', model: 'sonnet' },
    { title: 'Setts', detail: 'real or stronger relief in the joints that survives wetness, glare and any light', model: 'sonnet' },
    { title: 'Rubbish', detail: 'rubbish mask for gutters and building feet; painted muck plus small scattered pieces', model: 'sonnet' },
    { title: 'Check', detail: 'fresh-eyes look check under the lighting test set; one fix round if needed', model: 'sonnet' },
  ],
}

const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const SW = PROC + '/street_wet'
const RS = SW + '/relief_and_rubbish'
const AE = '/home/user/Music/austerity-explainer'
const KIT = AE + '/film-kit'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const ASK = [
  'WHAT THE PERSON ASKED (not a programmer; they test ideas by having helpers build them), after seeing the wet street and its painter test: "Can we do one more thing. Add a rubbish mask for gutters and along buildings. And the normal maps between bricks on the ground needs a little work. The light shouldn\'t be able to wash out the 3d affect so easily. The geometry should still be visible under all conditions."',
  'Meaning, as decided: (1) the joints between the road setts ("bricks on the ground") must read as 3D - grooves between raised stones - in EVERY lighting and wetness condition: dusk with lamps, the brazier glare in the lockout foreground, a low raking light, flat overhead light, light from behind into the glare, and dry / wet / heavy rain. Today the setts wear a Poly Haven colour + normal picture (normal strength 1.4, no height), and when wet the wetness layer flattens the relief (Relief Flatten 0.7, Grain Fill) and the wet sheen and glare fill the joints, so the stones melt into one glossy sheet. (2) A RUBBISH MASK: where rubbish gathers - along the gutters and kerbs, along the foot of the house walls, in corners, at doorsteps and downpipes, round the drum - and rubbish drawn there, fitting a 1926 Durham pit village during the lockout (coal dust and cinders, ash, wet straw, sodden paper, leaves, a few broken bits, mud; nothing modern, no plastic, no readable print).',
].join('\n')

const HOUSE = [
  'HOUSE RULES:',
  '* Work on the COPY of the street in ' + SW + ' (set_copy/, tools/, the WETNESS layer tools/wetness_layer.py and tools/apply_wetness_to_set.py, round 2 settings). Read ' + SW + '/09 Recipe - wetness layer and specular map for the street - how it is made.md first. The film project ' + AE + ' is the person\'s repository: READ it freely but NEVER change, add or delete anything there. No git.',
  '* Blender 5.2.2 is at ' + BLENDER + ' (always -b --disable-autoexec -t 2, at most ONE Blender process at a time; never pkill -f or killall). The film draws its plates in EEVEE (use the round 2 plate settings: shadow rays 4, steps 16, enough samples, xvfb-run as the earlier helper did); Cycles only for checks. The Bash tool stops a foreground command after 10 minutes: use run_in_background and ONE until-loop wait for longer runs. Use python3 -I for Python that reads pictures.',
  '* Disk: free space must stay above 1.2 GB (check df -h /). Keep ' + RS + ' under 300 MB; delete your own superseded renders; JPEG for pictures meant for looking.',
  '* NO paid image generation in this job.',
  '* Names: full plain words; a plain note at the top of every file you create. Notes and guides are for a person who is not a programmer: plain everyday words, explain any unavoidable technical word in one sentence, one word per thing, a concrete example before any general rule. Say what you tested, what you did not, and what you are unsure of; record failures. Never claim something works unless you ran it and looked at the result.',
].join('\n')

const REMOTE = [
  'RENDERING ON THE RENTED MACHINE (new since the job started): a rented RunPod machine with an RTX 4090 renders EEVEE about 100 times faster than this machine. Read ' + PROC.replace('/proc-work', '') + '/runpod/HOW TO RENDER ON THE RENTED MACHINE.md and render there with its render_client.py (upload changed scripts and files first; render in batches; download pictures to look at and measure here). Cycles there runs on 25 processor cores (the card cannot run Cycles on that machine). If the machine does not answer for 5 minutes, render here and say so. Never print or touch the files in ~/.runpod; do not stop the machine.',
  'Because rendering is now cheap, render the WHOLE lighting test set at every step that matters and look at it, and give the full-size lockout plates their full quality.',
].join('\n')

const STUDY_SCHEMA = { type: 'object', properties: {
  setts_diagnosis: { type: 'string', description: 'why the joints wash out: measured in the current plates (joint-to-stone contrast in each condition), which settings or maps cause it' },
  setts_methods: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, how: { type: 'string' }, tested: { type: 'string' }, cost: { type: 'string' } }, required: ['name', 'how', 'tested', 'cost'] } },
  rubbish_facts: { type: 'string', description: 'what rubbish lay where in a 1926 pit village street, with sources' },
  rubbish_methods: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, how: { type: 'string' }, tested: { type: 'string' }, cost: { type: 'string' } }, required: ['name', 'how', 'tested', 'cost'] } },
  lighting_test_set: { type: 'string', description: 'the fixed set of lighting and wetness conditions and cameras every later helper must render, how to switch them, and the joint-visibility measure with its pass line' },
  plan: { type: 'string' },
  guide_path: { type: 'string' },
}, required: ['setts_diagnosis', 'setts_methods', 'rubbish_facts', 'rubbish_methods', 'lighting_test_set', 'plan', 'guide_path'] }

const BUILD_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' },
  what_changed: { type: 'string', description: 'every change to the set copy, the layers and the materials, with settings' },
  controls: { type: 'string', description: 'the new controls: what each does, range, default' },
  measures: { type: 'string', description: 'the joint-visibility measure (and rubbish measures) in every condition of the lighting test set, before and after' },
  renders: { type: 'array', items: { type: 'string', description: 'path: what it shows' } },
  timings: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } },
  untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'what_changed', 'controls', 'measures', 'renders', 'timings', 'failures', 'untested'] }

const LOOK_SCHEMA = { type: 'object', properties: {
  setts_read_3d_everywhere: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  rubbish_reads_right: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  problems: { type: 'array', items: { type: 'string', description: 'ranked, most noticeable first, with a crop path and a concrete fix' } },
  claims_checked: { type: 'array', items: { type: 'string' } },
  should_iterate: { type: 'boolean' },
  overall: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['setts_read_3d_everywhere', 'rubbish_reads_right', 'problems', 'claims_checked', 'should_iterate', 'overall', 'pictures'] }

const studyPrompt = [
  'You are the STUDY HELPER for this job.',
  ASK, HOUSE,
  'Your folder: ' + RS + '/study/ (under 60 MB). Web research is allowed for this step.',
  'Do: (1) DIAGNOSE the setts: render the current wet set (round 2 settings) and the dry set from the main camera and the lockout plate camera, plus a close road view, and MEASURE how visible the joints are: build a joint mask for the setts from their texture coordinates and the Poly Haven sett layout (or from the height picture), and measure the brightness difference between joint lines and stone faces (and its share of the local brightness) in each condition. Find which settings or maps flatten them (normal strength, Relief Flatten, Grain Fill, the water film coat, puddles over joints, missing height/shadow, the colour picture\'s own joint darkness) by switching one at a time. (2) Research how people today (2024-2026) make cobbles and setts keep their relief in Blender 4.x/5.x: real geometry (displacement with a subdivided road, a Displace modifier from a height picture, geometry-nodes stones), parallax, stronger normal maps, cavity / ambient-occlusion darkening baked into colour, wet joints that stay dark and rough while stone tops shine, and the painted-style answer (dark joint lines that survive the repaint). Test the two or three most promising quickly. (3) Research where rubbish lay in a 1926 Durham pit village street (photographs and accounts: coal dust, cinders and ash from fires and ash middens, wet straw, paper, leaves, mud, broken crockery; where it gathered) and how people make rubbish masks and litter in Blender today (masks from the gutter and the wall foot - the wetness layer already knows both -, from distance to walls with geometry nodes Proximity, ambient occlusion and cavity; then a painted muck layer in the ground materials, and/or small scattered pieces with geometry nodes Distribute Points on Faces with density from the mask, kept small and few). (4) Define the LIGHTING TEST SET every later helper must render: the main camera and the lockout plate camera at 540 x 960, plus one close road view, under: A dusk lamps (the plate lighting), B lockout brazier glare, C low raking light from the side, D flat overhead light, E light from behind into the glare; each dry, wet (0.85/0.5) and heavy (1.0/0.8) where it matters; how to switch each (a script), and the joint-visibility measure with a pass line ("visible under all conditions" in numbers, chosen by looking).',
  'Write ' + RS + '/study/10 Research - sett relief and rubbish for the street.md (plain words, with the measured pictures) and return the structured result with a concrete plan: first the setts, then the rubbish mask on top.',
].join('\n')

function settsPrompt(study, critique, round) {
  const lines = [
    'You are the SETTS BUILDER' + (round > 1 ? ' (round ' + round + ', fixing what the checker found)' : '') + '.',
    ASK, HOUSE,
    'Your folder: ' + RS + ' (work in setts/, change the set copy only through scripts you save there). Study findings and plan: ' + JSON.stringify(study),
    REMOTE,
    round === 1 ? 'IMPORTANT - YOU ARE CONTINUING: an earlier setts builder worked for about 30 minutes and was stopped only so the rendering could move to the rented machine. Its files are in ' + RS + '/setts/ (tools, maps, work, logs): read them first, keep what is sound, and finish the job.' : '',
  ]
  if (round === 1) lines.push('Make the joints between the setts read as 3D grooves in every condition of the lighting test set, by the plan (for example real relief from the height picture on a subdivided road, darker and rougher joints that the water film does not fill, a cavity darkening in the colour, the wetness layer changed so it flattens only the stone tops and never the joints). Keep the wet look of round 2 (sheen, reflections, puddles in low spots). Render the whole lighting test set before and after, measure joint visibility in every condition, and make sheets: ' + RS + '/sheets/setts_before_after_all_lights.jpg and close-ups. Budget: about 20 Blender runs.')
  else lines.push('The checker\'s findings: ' + JSON.stringify(critique), 'Fix the setts problems it found, re-render the affected conditions and sheets. Budget: about 10 Blender runs.')
  lines.push('Write or update ' + RS + '/10 Recipe - sett relief and rubbish - how it is made.md (setts part). Save your structured result as ' + RS + '/setts_result_round_' + round + '.json and return it.')
  return lines.filter(Boolean).join('\n')
}

function rubbishPrompt(study, setts, critique, round) {
  const lines = [
    'You are the RUBBISH BUILDER' + (round > 1 ? ' (round ' + round + ', fixing what the checker found)' : '') + '.',
    ASK, HOUSE,
    'Your folder: ' + RS + ' (work in rubbish/). Study findings and plan: ' + JSON.stringify(study) + ' The setts are done (build on top of them, do not undo them): ' + JSON.stringify(setts),
    REMOTE,
  ]
  if (round === 1) lines.push('Build a RUBBISH MASK (a node group or geometry-nodes field, like the wetness layer, with controls: amount, gutter, wall foot, corners and doorsteps, around props, seed) that is strongest along the gutters and kerbs and at the foot of the house walls, breaks up naturally, and never sits on the crown of the road. Draw the rubbish with it: a painted muck layer in the ground materials (coal dust, cinders, ash, mud, wet straw, sodden paper and leaves as colour, height and roughness; wet where the street is wet) and, if the plan says, a few small scattered 3D pieces (cinders, paper scraps, straw, leaves, a broken pot) with density from the mask, nothing modern, no readable print. It must keep the setts\' 3D look and the wet look. Render the lighting test set (dry, wet, heavy) with and without rubbish, show the mask itself, and make sheets: ' + RS + '/sheets/rubbish_mask.jpg, ' + RS + '/sheets/rubbish_all_lights.jpg and 100 percent close-ups of a gutter, a wall foot and a doorstep. Finally draw ONE full-size lockout plate (1536 x 2730, EEVEE, plate settings) with setts and rubbish, wet. Budget: about 20 Blender runs.')
  else lines.push('The checker\'s findings: ' + JSON.stringify(critique), 'Fix the rubbish problems it found, re-render the affected conditions, the sheets and the full-size plate. Budget: about 10 Blender runs.')
  lines.push('Update ' + RS + '/10 Recipe - sett relief and rubbish - how it is made.md (rubbish part; every control and what changing it does). Save your structured result as ' + RS + '/rubbish_result_round_' + round + '.json and return it.')
  return lines.filter(Boolean).join('\n')
}

function lookPrompt(setts, rubbish, round) {
  return [
    'You are an INDEPENDENT LOOK CHECKER with fresh eyes (a film art director for a hand-painted explainer series set in 1926). Judge strictly and check the builders\' claims. Write only into ' + RS + '/check_round_' + round + '/ (JPEG, under 15 MB).',
    ASK, HOUSE,
    'Builders\' reports: setts ' + JSON.stringify(setts) + ' rubbish ' + JSON.stringify(rubbish),
    REMOTE,
    'Judge: (1) do the setts read as separate raised stones with grooves in EVERY condition of the lighting test set (look at each, and re-render at least two hard ones yourself: the brazier glare and the flat overhead light, wet); (2) does the rubbish sit where rubbish gathers (gutters, kerbs, wall feet, corners, doorsteps) and read as 1926 pit village muck and litter, not as noise, stains or modern litter; is it too much or too little; (3) did anything else get worse (the wet look, the walls, seams, tiling of the sett picture, shimmering, render time); (4) would the painter keep it (look at the full-size plate as the painter will). Re-measure two of the builders\' numbers. Rank problems with crops and concrete fixes; should_iterate true only if a fix round is clearly worth it.',
    'Return the structured result.',
  ].join('\n')
}

phase('Study')
const study = await agent(studyPrompt, { ...SONNET, label: 'study: sett relief and rubbish', phase: 'Study', schema: STUDY_SCHEMA })
phase('Setts')
let setts = await agent(settsPrompt(study, null, 1), { ...SONNET, label: 'setts builder, round 1', phase: 'Setts', schema: BUILD_SCHEMA })
phase('Rubbish')
let rubbish = await agent(rubbishPrompt(study, setts, null, 1), { ...SONNET, label: 'rubbish builder, round 1', phase: 'Rubbish', schema: BUILD_SCHEMA })
phase('Check')
let look = await agent(lookPrompt(setts, rubbish, 1), { ...SONNET, label: 'look check, round 1', phase: 'Check', schema: LOOK_SCHEMA })
const rounds = [{ setts, rubbish, look }]
if (look && look.should_iterate) {
  log('Look check asked for a fix round')
  setts = await agent(settsPrompt(study, look, 2), { ...SONNET, label: 'setts builder, round 2', phase: 'Setts', schema: BUILD_SCHEMA })
  rubbish = await agent(rubbishPrompt(study, setts, look, 2), { ...SONNET, label: 'rubbish builder, round 2', phase: 'Rubbish', schema: BUILD_SCHEMA })
  look = await agent(lookPrompt(setts, rubbish, 2), { ...SONNET, label: 'look check, round 2', phase: 'Check', schema: LOOK_SCHEMA })
  rounds.push({ setts, rubbish, look })
}
const stopped = await agent('Run this one command and report its output line, nothing else: bash ~/.runpod/stop_pod.sh  (it stops the rented RunPod machine now that the job is done; do not read or print any file in ~/.runpod).', { ...SONNET, effort: 'low', label: 'stop the rented machine', phase: 'Check' })
return { study, rounds, stopped }
