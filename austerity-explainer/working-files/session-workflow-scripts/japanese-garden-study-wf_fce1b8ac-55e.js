export const meta = {
  name: 'japanese-garden-study',
  description: 'Gather all available advice for improving the Japanese courtyard (the Astra add-on guidance, our street and kit lessons, the scene itself, real gardens) and turn it into one plan',
  phases: [
    { title: 'Study', detail: 'four readers in parallel' },
    { title: 'Plan', detail: 'one plan with two look directions' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const JC = '/home/user/Music/japanese-courtyard'
const AW = SC + '/astra-work'
const ADDON = SC + '/astra-upload-021'
const OUT = PW + '/garden'
const PICS = PW + '/29 Japanese garden - pictures'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. Their request, verbatim: "Ok. Can you work on the Japanese garden using all the advice available. Then render on runpod. There's an option where you only pay per second used. So you don't pay for seconds or minutes not used."
THE GARDEN: the Japanese courtyard built on 18 October with the person's Astra Painted Workbench add-on (their own upload; version 0.2.1 unpacked read-only at ${ADDON}, 0.2.0 at ${SC}/astra-upload): build script ${JC}/build_courtyard.py and loader ${JC}/astra_loader.py (a small Blender 5.2 workaround), project story ${JC}/Japanese courtyard - project story.md, the golden-hour photo ${JC}/01 Japanese courtyard - golden hour photo.png (2400 x 1600, Cycles, 180 samples, 13 minutes here), saved scenes in ${AW}/out/*.blend, working scripts in ${AW}/. A wooden hall with glowing paper screens under a tiled roof, a pond with a zigzag bridge and lily pads, rocks, a stone lantern, a red maple, a pruned pine, raked gravel, stepping stones, moss and pebbles grown by the add-on, hazy hills.
SINCE THEN we built and learned a lot on a 1926 pit-village street (all in ${PW}/): procedural texture recipes and a cookbook (cookbook/06 Cookbook - start here.md, 07 Reuse...), photo-scanned Poly Haven surfaces in the street (the person said the scanned bricks "look incredible"), a reusable WEATHERING KIT (kits/weathering/: grime, cracks, stains, weeds, moss; recipe "15 Recipe - weathering kit ... how it is made.md"; settings sets/japanese_courtyard.json and a rough "mossy Japanese courtyard" look; it was already tried on this courtyard: pictures "25 Reuse - the same kit on the Japanese courtyard.jpg" and the courtyard study street_wet/grime_and_growth/study/12b*; three blockers: the hall roof's materials hide inside a geometry-nodes modifier, the long garden wall gets no wall sheet, per-material dials only work for soot), the EEVEE-and-Cycles comparison (26 EEVEE and Cycles side by side - pictures/ and street_wet/eevee_vs_cycles/: Cycles wins on lamp light, reflections and wet ground; EEVEE's light threshold 0.01 cuts lamp reach), the person's renderer rule ("Cycles ... only for scenes where the lights are on. When they're off, eeve is fine."), what survives a painter (painted-look study under street_wet/grime_and_growth/study/12*), and seven installed Scenario Blender skills at /home/user/Music/.claude/skills/ (expert with a delivery check for inside-out, floating or overlapping parts; texturing-shading; uv-baking; geometry-nodes; lighting-rendering with value studies; previs; export). The project story ${PW}/Procedural textures - project story.md has the full log.
RULES: read-only everywhere except your own folder ${OUT}/<your part>/ (limit 60 MB) and the pictures folder "${PICS}/" (JPG under 400 KB, names start "29 "); never write in ${JC}, ${ADDON}, ${SC}/astra-upload, ${AW}, the film project or the kit; Blender 5.2.2 at ${BLENDER}, headless (-b --disable-autoexec; xvfb-run -a if anything is drawn); no rendering bigger than small previews on this shared computer (EEVEE or Workbench, under 2 minutes); never read or print anything in ~/.runpod; never put the person's name or email into any request to an outside website; no paid calls. Disk is tight (about 0.8 GB free): delete scratch files.
REPORTING: plain everyday words; say what you read, what you could not, and how sure you are.`

const STUDY = { type: 'object', properties: {
  findings: { type: 'string', description: 'the main report, plain words' },
  advice: { type: 'array', items: { type: 'object', properties: { what: { type: 'string' }, applies_to: { type: 'string' }, why: { type: 'string' }, source: { type: 'string' }, impact: { type: 'string', enum: ['high', 'medium', 'low'] } }, required: ['what', 'applies_to', 'why', 'source', 'impact'] } },
  faults_found: { type: 'array', items: { type: 'string' } },
  files: { type: 'array', items: { type: 'string' } },
}, required: ['findings', 'advice', 'faults_found', 'files'] }

phase('Study')
const [addon, ours, scene, real] = await parallel([
  () => agent(`${COMMON}
YOUR PART: THE ADD-ON'S OWN ADVICE. Read every guidance and lessons document of the Astra add-on in full (${ADDON}/README.md, docs/*.md, and the lessons/recipes registry it ships under data/ or wherever docs say the 83 lessons and recipes live; list each file and whether you read it fully). Distil every piece of advice that applies to this courtyard: how the add-on means painted environments to look (pigment mapping, stone and wood identity, flat colour, edges), its terrain, scatter, plank, roof and stone tools and their limits, multi-scale wear, terrain contact and burial, winding and visibility faults, lighting studies, composition and readability rules, and its traps on Blender 5.1 vs 5.2. Also say which of its recipes or operators the courtyard build did NOT use (the story says it skipped the live scatter tool, "pigment" painting and the "detail" tool) and what they would add. Work in ${OUT}/addon/.`, { ...OPTS, label: 'study: the add-on guidance', phase: 'Study', schema: STUDY }),
  () => agent(`${COMMON}
YOUR PART: OUR OWN ADVICE. Read the procedural textures cookbook and reuse note, the weathering kit's recipe, the courtyard settings and look files, its reuse-proof report and the checkers' notes about it (search ${PW}/street_wet/grime_and_growth/ for reuse_proof and check folders), the EEVEE-and-Cycles comparison results, the painted-look study, the project story's log entries 15-28, and the seven Scenario skills' SKILL.md files (and the references they point to for materials, lighting and composition). Distil what applies to the courtyard: which kit layers suit a Japanese garden and which do not (no coal soot), how to fix the three kit blockers in the kit's code without breaking the street, which Poly Haven scanned surfaces would suit wood, plaster, stone, gravel, roof tiles and bark (name them; check Poly Haven's site for exact names and licence, CC0), which renderer the person's rule asks for here (glowing screens and a lantern count as lights on?), and the Scenario skills' advice that fits (materials, lighting value checks, delivery check). Work in ${OUT}/ours/.`, { ...OPTS, label: 'study: our own advice', phase: 'Study', schema: STUDY }),
  () => agent(`${COMMON}
YOUR PART: THE SCENE ITSELF. Open the newest saved courtyard scene that matches the final photo (say which and why) headless and inspect it: objects, materials (which are the add-on's, which are the build script's simple noise materials), lights, sun angle, world and sky, camera, render settings. Run the Scenario expert skill's delivery check (bx_audit; leave out the sky dome and far hills and set distances to about 1 mm, as the street try-out learned) and report real faults (inside-out, floating, overlapping, missing UVs). Look at the photo at full size and list what looks weakest, ranked by how much a viewer would notice (for example faceted low-detail rocks, the star-shaped maple leaves, flat hills, bare plaster, plain gravel, the roof). Read the courtyard story's next-step ideas (veranda view, blue evening with the lantern lit, morning mist, bamboo water spout, tea house, fish). Make 2-3 small Workbench or EEVEE preview pictures if they help. Work in ${OUT}/scene/.`, { ...OPTS, label: 'study: the scene itself', phase: 'Study', schema: STUDY }),
  () => agent(`${COMMON}
YOUR PART: REAL JAPANESE GARDENS. Research with web searches (WebSearch/WebFetch; load them with ToolSearch if needed) what makes a Japanese temple or garden courtyard read as authentic close up: raked gravel (karesansui) patterns and edges, moss gardens (sugigoke, haircap moss; how moss meets stone and gravel), stone lanterns (tōrō: kinds, lichen and moss on them), tsukubai and bamboo spouts, stepping stones (tobi-ishi), engawa wood and how it weathers, plaster walls with tile caps (tsuiji-bei), roof tiles (kawara) and their moss and drip lines, pond edges and koi, maples and pines (how they are pruned), and the light at golden hour and at dusk with lanterns lit. Note common mistakes in CG Japanese gardens. For each, say where it applies in this courtyard and how sure you are; give sources (links). Work in ${OUT}/real/.`, { ...OPTS, label: 'study: real Japanese gardens', phase: 'Study', schema: STUDY }),
])

phase('Plan')
const PLAN = { type: 'object', properties: {
  plan: { type: 'string', description: 'the plan in plain words, step by step, ranked by what a viewer would notice most' },
  plan_file: { type: 'string' },
  look_question: { type: 'string', description: 'the one choice only the person can make about the look, with what each answer means in one or two sentences each' },
  renderer: { type: 'string' },
  steps_for_builders: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, brief: { type: 'string' } }, required: ['name', 'brief'] } },
  risks: { type: 'array', items: { type: 'string' } },
}, required: ['plan', 'plan_file', 'look_question', 'renderer', 'steps_for_builders', 'risks'] }
const plan = await agent(`${COMMON}
YOUR JOB: THE PLAN. From the four studies below, write one plan for improving the courtyard and rendering it, saved as ${OUT}/30 Plan - Japanese garden - all the advice.md. Rank the improvements by what a viewer would notice most. Keep the add-on in use (it is the person's own tool) and say where its advice and ours disagree and which you would follow. Name the ONE choice only the person can make about the look (for example: keep the add-on's painted look, or go realistic with scanned surfaces and Cycles like the street), with what each answer means. Split the work into 2-4 builder briefs that can run side by side without touching each other's files (for example: materials and surfaces; weathering with the kit, including fixing its three blockers in the kit code; plants, water and details; lighting, camera and render settings), each with its own folder under ${OUT}/, and a final integrate-render-check step. Rendering of anything bigger than a small preview goes to the person's RunPod account through a pay-per-second endpoint that is being set up now (the integrate step will get its instructions); say what pictures the final render should be (the original golden-hour view at least; any second view from the story's ideas).
ADD-ON STUDY: ${JSON.stringify(addon)}
OUR-ADVICE STUDY: ${JSON.stringify(ours)}
SCENE STUDY: ${JSON.stringify(scene)}
REAL-GARDENS STUDY: ${JSON.stringify(real)}`, { ...OPTS, label: 'plan', phase: 'Plan', schema: PLAN })

return { addon, ours, scene, real, plan }
