export const meta = {
  name: 'street-eevee-vs-cycles',
  description: 'Draw the wet street (main camera and lockout plate) with EEVEE and Cycles side by side on the rented machine, same layers and light, then a fresh-eyes comparison',
  phases: [
    { title: 'Draw', detail: 'same street, same layers, two renderers, timed' },
    { title: 'Compare', detail: 'fresh eyes: realism, wet look, joints, noise, time' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const SW = PW + '/street_wet'
const RR = SW + '/relief_and_rubbish'
const OUT = SW + '/eevee_vs_cycles'
const PICS = PW + '/26 EEVEE and Cycles side by side - pictures'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. Looking at a door drawn with Blender's Cycles renderer (${PW}/23 Scenario Blender skills test - pictures/23b-1 door before and after wear - add_wear shows in Cycles only, the bake carries it to EEVEE.jpg, third door), they said it looked photorealistic and the photo-scanned bricks "look incredible". Our street plates are drawn with EEVEE (faster, flatter). They asked, verbatim: "Yeah do it!" to: draw the wet street from the main camera with both renderers side by side, so they can see whether the whole street gets the same jump.
WHERE THINGS ARE: the street copy ${SW}/set_copy/street.blend (read-only); the wetness layer and the EEVEE picture runner ${SW}/tools/ (wetness_layer.py, apply_wetness_to_set.py, 22_render_eevee.py: states must start with "today"); the JOINTS and RUBBISH layers and their apply scripts ${RR}/setts/tools and ${RR}/rubbish/tools (recipe note ${RR}/10 Recipe*.md; the final lockout plate's exact settings are in that note and in ${RR}/rubbish/final/); the lockout shot file is in the film project (read-only; find it from the rubbish tools, which open it). The Cycles door try-out's own render script: ${PW}/skills_test/22b/21_render_cycles.py.
RENDERING: only on the rented RunPod machine: read ${SC}/runpod/HOW TO RENDER ON THE RENTED MACHINE - cached.md and use ONLY ${SC}/runpod/render_client_cached.py. Upload what you need (relief_and_rubbish tool and map folders are not on the machine's store). Two other jobs share the machine; that is fine. Blender 5.2.2 headless with --disable-autoexec.
HARD RULES: never print, copy, move or read anything in ~/.runpod; never write into the film project, ${SW}/set_copy, ${SW}/tools, ${RR}, or other jobs' folders (${SW}/painter_round_2, ${SW}/grime_and_growth, ${PW}/kits); work in ${OUT}/ (limit 150 MB; keep only the final PNGs and JPGs); do not commit or push; do not stop or end rented machines; no paid image calls.
REPORTING: plain everyday words; say what you tested, what you did not, what you are unsure of.`

const DRAW_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' }, settings: { type: 'string', description: 'both renderers: samples, denoiser, light paths, resolution, anything changed to make Cycles match' },
  timings: { type: 'string' }, outputs: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
  measures: { type: 'string' }, layer_differences: { type: 'string', description: 'anything in the wetness, joints or rubbish layers that behaves differently in Cycles' },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'settings', 'timings', 'outputs', 'measures', 'layer_differences', 'failures', 'untested'] }

phase('Draw')
const draw = await agent(`${COMMON}

YOUR JOB: draw the same pictures with EEVEE and with Cycles, everything else identical (same file, camera, lighting, wetness, JOINTS and RUBBISH layers at their final defaults, same resolution).
1. MAIN STREET CAMERA, 1080 x 1920: "today" (dry) and "wet". EEVEE exactly as the plates are drawn now (the plate settings in the recipe note: ray tracing, shadow rays 4 / steps 16, 64 samples). Cycles on the card (OptiX), with the OptiX denoiser, adaptive sampling, enough samples that noise is not visible at 100 % (start at 256; say what you settled on and why), light paths sensible for a street at dusk (say which).
2. LOCKOUT PLATE, full size 1536 x 2730, "wet", lighting B, exactly as the final plate (${RR}/rubbish/final/final_lockout_plate_wet_setts_and_rubbish.png) but in both renderers.
3. One CLOSE VIEW at 1600 x 1200 of a cottage front (door, stone walls, a window, the pavement and gutter in front), wet, both renderers, so the person can see the stone and brick up close.
Time every picture. If Cycles shows something different because a layer was built for EEVEE (for example shadow settings, the wet film, emission, transparency, the rubbish pieces), say exactly what and do NOT tune the layers; only renderer settings may differ.
Measure for each pair: overall brightness, how many dots are blown out (over 0.97) or crushed (under 0.02), the sett joint visibility with the job's own measuring script (${RR}/setts/tools/measure_grid_visibility.py or the one the rubbish job used) on the lockout plate, and the time.
Make side-by-side sheets for the person in "${PICS}/" (JPG under 400 KB each; EEVEE on the left, Cycles on the right, labelled, with time per picture): "26 Main street - wet - EEVEE and Cycles.jpg", "26 Main street - dry - EEVEE and Cycles.jpg", "26 Lockout plate - wet - EEVEE and Cycles (half size).jpg", "26 Close-ups at 100 percent - walls, door, setts, gutter.jpg", "26 Cottage front close view - EEVEE and Cycles.jpg". Keep the full-size PNGs in ${OUT}/.`, { ...OPTS, label: 'draw both renderers', phase: 'Draw', schema: DRAW_SCHEMA })

phase('Compare')
const CMP_SCHEMA = { type: 'object', properties: {
  verdict: { type: 'string', description: 'plain words: does the whole street get the jump the door got? where does Cycles look better, where worse?' },
  per_picture: { type: 'array', items: { type: 'object', properties: { picture: { type: 'string' }, better: { type: 'string', enum: ['EEVEE', 'Cycles', 'about the same'] }, why: { type: 'string' } }, required: ['picture', 'better', 'why'] } },
  for_the_film: { type: 'string', description: 'what it would mean for the painted film: does the painter need the extra realism, would the wet look and joints survive, cost in time per plate' },
  claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['claim', 'holds', 'evidence'] } },
  problems: { type: 'array', items: { type: 'string' } }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['verdict', 'per_picture', 'for_the_film', 'claims_checked', 'problems', 'pictures'] }
const compare = await agent(`${COMMON}

YOU ARE A FRESH-EYES COMPARER (you did not draw these). Open every full-size PNG in ${OUT}/ and the sheets in "${PICS}/", make your own 100 % crops of the same places in both renderers (stone walls, a door, setts and joints, gutter puddles, lamp glow and reflections, the sky, dark corners, the rubbish), and re-run two of the drawer's measurements yourself. Judge as the person would: realism of stone and brick, wet look, light from lamps and windows, darkness and noise, and whether the joints and rubbish still read. Say plainly where Cycles is better, where EEVEE is better or equal, and what each costs in time. Add a sheet of your best crops: "${PICS}/26 Checker - the clearest differences.jpg".
DRAWER'S REPORT: ${JSON.stringify(draw)}`, { ...OPTS, label: 'fresh-eyes comparison', phase: 'Compare', schema: CMP_SCHEMA })

return { draw, compare }
