export const meta = {
  name: 'japanese-garden-build-and-render',
  description: 'Build the Japanese garden in both looks (realistic and painted) from the plan, render on the pay-per-second RunPod endpoint, two fresh checks, one fix round, final pictures',
  phases: [
    { title: 'Build', detail: 'shapes, life, surfaces and weathering, light (four builders)' },
    { title: 'Integrate and render', detail: 'chain the stages, preview, final Cycles pictures on RunPod per second' },
    { title: 'Check', detail: 'art and period eye; measurement, claims and cost' },
    { title: 'Fix', detail: 'one fix round, redraw, re-check' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const G = PW + '/garden'
const PLAN = G + '/30 Plan - Japanese garden - all the advice.md'
const JC = '/home/user/Music/japanese-courtyard'
const AW = SC + '/astra-work'
const PICS = PW + '/30 Japanese garden - pictures'
const RUNPOD_GUIDE = SC + '/runpod/HOW TO RENDER - pay per second.md'
const CLIENT = SC + '/runpod/render_client_serverless.py'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. Their request, verbatim: "Ok. Can you work on the Japanese garden using all the advice available. Then render on runpod. There's an option where you only pay per second used. So you don't pay for seconds or minutes not used." Asked which look they want (realistic like the Cycles street, or the hand-painted look their Astra add-on is made for), they answered: "Both, side by side". So every stage supports options['look'] in ('real', 'painted') and the final pictures show both, side by side. Their own recorded words about the painted look (from the add-on's lessons): "No rounded smooth curves. Just edges and flat surfaces that approximate a curve" (and the planes must not be uniform quads or triangles). Their renderer rule: "Cycles ... only for scenes where the lights are on. When they're off, eeve is fine." (this garden has glowing paper screens and a lantern: Cycles for finals).
THE PLAN: read ${PLAN} first: section 7 (shared rules for all builders) and your own section. The four studies behind it are in ${G}/addon, ${G}/ours (including the weathering-kit fixes fix1-fix4 in ours/kit_patched and ours/patches, and polyhaven_shortlist_CC0.json), ${G}/scene, ${G}/real.
STARTING FILE: ${AW}/out/courtyard_final.blend (read-only: open it, never save over it). The person's add-on (read-only): ${SC}/astra-upload-021 (live scatter needs the 3-line Blender 5.2 patch the add-on study saved under ${G}/addon/tests/: apply it only to a COPY of the add-on in your own folder).
RENDERING: Blender 5.2.2 at ${BLENDER}, headless (-b --disable-autoexec; xvfb-run -a for anything drawn here). This shared computer is very slow (over 3 minutes for one small EEVEE picture of this scene): draw anything beyond a tiny Workbench check on RunPod, PAYING PER SECOND: read ${RUNPOD_GUIDE} and use ONLY ${CLIENT} (upload what a job needs first: the stage scripts, the starting file, scans, the add-on copy; the store keeps them; outputs go under your own folder, which is in the store too). Batch pictures into one run per round; up to 3 jobs can run at once account-wide (other builders share them), so keep jobs short and do not leave many queued.
HARD RULES: never write in ${JC}, ${SC}/astra-upload*, ${AW}, the film project or the street work; work only in your own folder under ${G}/ (limit 60 MB unless your brief says otherwise; delete scratch) and the pictures folder "${PICS}/" (JPG under 400 KB, names start "30 "); never print, copy, move or read anything in ~/.runpod (the client reads it itself); never put the person's name, email or any personal detail into a request to an outside website (use a neutral User-Agent such as "garden-study/1.0"); no paid image calls; do not commit or push; free disk is under 1 GB: stop and report if it falls under 0.6 GB.
REPORTING: plain everyday words; say what you tested, what you did not, what you are unsure of, and every failure.`

const STEP = { type: 'object', properties: {
  summary: { type: 'string' }, deliverables: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
  real_vs_painted: { type: 'string', description: 'what your stage does differently for each look' },
  measures: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
  runpod_seconds: { type: 'string', description: 'jobs sent and seconds billed (the wait output shows billed_work_ms)' },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'deliverables', 'real_vs_painted', 'measures', 'pictures', 'runpod_seconds', 'failures', 'untested'] }

const BUILDERS = [
  { name: 'shapes', section: '8', label: 'build: shapes (repairs, lantern, rocks, gravel, walls)' },
  { name: 'life', section: '9', label: 'build: life (maple, ground cover, pond, pine, bamboo)' },
  { name: 'surfaces', section: '10', label: 'build: surfaces and weathering' },
  { name: 'light', section: '11', label: 'build: light, backdrop, camera, render job' },
]

phase('Build')
const built = await parallel(BUILDERS.map(b => () => agent(`${COMMON}
YOUR JOB: BUILDER "${b.name}". Your brief is section ${b.section} of the plan; follow it in its priority order (stopping early must still leave a usable stage). Your folder: ${G}/${b.name}/. Deliver what the brief names (stage script(s) with apply(options), a short test report, 1-3 small pictures for the person). Prove your stage on its own: open the starting file, apply your stage with look='real' and with look='painted', check the objects you own changed as intended and nothing else did (list object and material names before and after), and draw ONE small preview per look on RunPod (EEVEE is fine for previews; 960 x 640). Time-box: about 2.5 hours.`, { ...OPTS, label: b.label, phase: 'Build', schema: STEP }).then(r => ({ name: b.name, report: r }))))

phase('Integrate and render')
const integrate = await agent(`${COMMON}
YOUR JOB: STEP 5, INTEGRATE AND RENDER (plan section 12, with the plan's sections 6 and 7). Folder: ${G}/final/ (limit 120 MB; keep the two .blend files compressed). Builders' reports: ${JSON.stringify(built)}.
1. Chain the stages on the starting file in the plan's order (shapes, life, surfaces, weathering, light) for look='real' and again for look='painted'; save garden_real.blend and garden_painted.blend (compressed, pictures packed). Conflict check as the plan says; if a stage breaks the scene, skip it, run the rest and report which.
2. Rerun the Scenario delivery check on the groups the plan names.
3. RunPod, per second: one tiny Cycles picture first to prove the card works for Cycles (OptiX); then a cheap preview round (both looks, hero view, 960 x 640, about 64 samples); look at them yourself and fix only what is clearly broken.
4. The finals in Cycles on RunPod as the plan's section 6 says (2400 x 1600, adaptive 384-512 samples, denoiser, light groups and an EXR beside each PNG): (1) the original golden-hour view, realistic; (2) the same view, painted; (3) the veranda view over the pond, both looks if time allows; (4) stretch: blue evening with the lantern lit (realistic). Split any job that could pass 50 minutes.
5. Sheets for the person in "${PICS}/": "30 Before and after - the original photo and the realistic garden.jpg", "30 Side by side - realistic and painted.jpg", "30 Veranda view.jpg" (if made), "30 Close-ups at 100 percent - both looks.jpg". Keep the full-size PNGs in ${G}/final/renders/.
6. Report the RunPod seconds used per job (billed_work_ms from the client's wait output) and the total.`, { ...OPTS, label: 'integrate and render on RunPod', phase: 'Integrate and render', schema: STEP })

phase('Check')
const CHECK = { type: 'object', properties: {
  realistic_reads_as_a_real_garden: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  painted_follows_the_add_on_and_the_person: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  better_than_the_original_photo: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['claim', 'holds', 'evidence'] } },
  problems: { type: 'array', items: { type: 'string', description: 'what, where (picture and crop), why a viewer would notice, the cheapest fix' } },
  runpod_cost_checked: { type: 'string' },
  should_fix_now: { type: 'boolean' }, fixes_for_one_round: { type: 'string' }, overall: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['realistic_reads_as_a_real_garden', 'painted_follows_the_add_on_and_the_person', 'better_than_the_original_photo', 'claims_checked', 'problems', 'runpod_cost_checked', 'should_fix_now', 'fixes_for_one_round', 'overall', 'pictures'] }
const checkPrompt = (lens, reports) => `${COMMON}
YOU ARE A FRESH-EYES CHECKER (you did none of this work). Lens: ${lens}
Open the final PNGs at full size and make your own 100 % crops (save the telling ones in ${G}/check/ and the key ones in "${PICS}/" named "30 Checker - ..."); compare with the original photo ${JC}/01 Japanese courtyard - golden hour photo.png. Re-check at least three claims yourself from the files. List problems with the cheapest fix, and say whether one fix round is worth it now (only for faults a viewer would notice at normal viewing size).
REPORTS: ${JSON.stringify(reports)}`
const LENS_ART = 'ART AND GARDEN: does the realistic version read as a real Japanese temple garden at golden hour (gravel, moss, rocks, lantern, maple, pine, water, wood, plaster, roof, sky); does the painted version follow the add-on\'s painted rules (broad unequal colour passages, material-specific marks, chiselled unequal planes, a broad connected glow) and the person\'s own words; is anything floating, tiled, repeated, too clean or too busy; is each clearly better than the original photo.'
const LENS_MEASURE = 'MEASUREMENT, CLAIMS AND COST: re-check the repair claims (floating step, bridge piers, wall caps, lantern opening) in the saved .blend files with Blender (no drawing needed), the conflict check, the light groups adding up to the picture, render settings and engine per picture; check the RunPod seconds and the per-second rule (no machine left running: the client status of the endpoint health shows workers; idle should be 0 shortly after the last job); grep all new code for the person\'s email or name and for anything in ~/.runpod.'
const reports1 = { built, integrate }
const checks = await parallel([
  () => agent(checkPrompt(LENS_ART, reports1), { ...OPTS, label: 'check: art and garden', phase: 'Check', schema: CHECK }),
  () => agent(checkPrompt(LENS_MEASURE, reports1), { ...OPTS, label: 'check: measurement, claims, cost', phase: 'Check', schema: CHECK }),
])

let fix = null, recheck = null
if (checks.filter(Boolean).some(c => c.should_fix_now)) {
  phase('Fix')
  fix = await agent(`${COMMON}
YOUR JOB: ONE FIX ROUND on the integrated garden (${G}/final/; work in ${G}/fix/, limit 100 MB; never overwrite the builders' folders; copy what you change). The checkers found: ${JSON.stringify(checks.filter(Boolean).map(c => ({ problems: c.problems, fixes: c.fixes_for_one_round })))}
Earlier reports: ${JSON.stringify(reports1)}
Fix what a viewer would notice first, in both looks; redraw the finals that change on RunPod per second (same settings), remake the sheets in "${PICS}/" with names starting "30 Fix - " plus updated "30 Side by side - realistic and painted.jpg", and report RunPod seconds.`, { ...OPTS, label: 'fix round', phase: 'Fix', schema: STEP })
  recheck = await agent(checkPrompt(LENS_ART + ' ALSO: ' + LENS_MEASURE, { ...reports1, first_checks: checks, fix }), { ...OPTS, label: 're-check', phase: 'Fix', schema: CHECK })
}
return { built, integrate, checks, fix, recheck }
