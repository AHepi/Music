export const meta = {
  name: 'japanese-garden-character',
  description: 'Give the realistic garden character in its own art style: concept images (US$15 cap), a direction from them, four builders (wood and bridge, roof and stone, ground and grass, pond and trees) with normal maps, Cycles finals on the pay-per-second endpoint, two checks and a fix round',
  phases: [
    { title: 'Concept', detail: 'style note and concept images in the art style (paid, capped)' },
    { title: 'Direction', detail: 'pick from the concepts, write four builder briefs' },
    { title: 'Build', detail: 'wood and bridge; roof, walls and stone; ground and grass; pond and trees' },
    { title: 'Integrate and render', detail: 'chain, finals and close-ups on RunPod per second' },
    { title: 'Check', detail: 'art direction against the concepts; construction, normal maps, claims, cost' },
    { title: 'Fix', detail: 'four fixers (wood, roof and stone, ground, pond and trees), put together and draw finals, re-check' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const G = PW + '/garden'
const C = G + '/character'
const BASE = G + '/fix/garden_real_fixed.blend'
const NOW_HERO = G + '/fix/out/final/real_hero.png'
const NOW_VERANDA = G + '/fix/out/final/real_veranda.png'
const PICS = PW + '/31 Japanese garden character - pictures'
const LEDGER = PW + '/SPENDING - paid image generation ledger.md'
const RUNPOD_GUIDE = SC + '/runpod/HOW TO RENDER - pay per second.md'
const CLIENT = SC + '/runpod/render_client_serverless.py'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPTS = { model: 'sonnet', effort: 'xhigh' }
const REQUEST = "The realistic one. But don't make it more realistic. I still want the art style. What's missing now is the details in grass, pond, roof, wood and so on. They have textures, but they're bland and have no character. The geometry of the wood planks is also very basic. No wear, no mold or moss, the logic behind how the bridge is constructed makes no sense. Even for an artistic style. Are there any normal maps used? Generate an image of trees and so on in the art style and work from that. The image gen budget is $15."

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. The Japanese courtyard garden was just rebuilt in two looks; they chose the realistic one and said, verbatim: "${REQUEST}"
WHAT THAT MEANS: keep the CURRENT art style of the realistic garden (its simplified, slightly chunky stylised forms, its colour palette, the graded dusk light, the saturated maple) and do NOT push it toward photo-realism. Add CHARACTER: hand-crafted, readable detail in wood, the bridge, roof, grass, pond, trees, stone. Answer to their normal-map question (checked): the garden has NO normal maps; the scanned surfaces carry only colour, roughness and a height picture fed to Blender's Bump node at strength 0.3-0.6, plants and water get bump from noise, and the planks are plain boxes with a 3 mm bevel. Normal maps and real geometry detail are wanted now.
THE GARDEN NOW: starting scene ${BASE} (read-only; open it, never save over it); its current pictures ${NOW_HERO} and ${NOW_VERANDA} (2400 x 1600, Cycles); the earlier plan ${G}/30 Plan - Japanese garden - all the advice.md (sections 6 and 7: rendering, shared rules such as garden_owner / garden_role labels on new objects and keeping existing names); the stages that built it: ${G}/shapes, ${G}/life, ${G}/surfaces (incl. surf_kit.py, the weathering kit copy and the scans in surfaces/maps), ${G}/light, ${G}/final, ${G}/fix (stage_fix.py). The person's Astra add-on (read-only): ${SC}/astra-upload-021; its painted-environment rules are summarised in ${G}/addon and the plan.
RENDERING: Blender 5.2.2 at ${BLENDER}, headless (-b --disable-autoexec; xvfb-run -a for anything drawn here; this computer is too slow for real pictures). Draw on RunPod paying per second: read ${RUNPOD_GUIDE}, use ONLY ${CLIENT}; batch pictures into one job per round; up to 3 jobs can run account-wide at once (others share them). Cycles for finals (the screens and lantern are lit), EEVEE or low-sample Cycles for previews.
DISK IS VERY TIGHT (about 0.65 GB free, shared): keep .blend files, EXR and full-size PNG renders ON THE RUNPOD STORE ONLY (any path under your folder is in the store once you upload or a job writes there); download only JPG previews (under 400 KB) and the small files you need; stop and report if free space here falls under 0.4 GB.
HARD RULES: never write in /home/user/Music/japanese-courtyard, ${SC}/astra-upload*, ${SC}/astra-work, ${BASE} or other stages' folders (copy what you need into your own folder under ${C}/); never print, copy, move or read anything in ~/.runpod; never put the person's name, email or any personal detail into a request to an outside website; do not commit or push.
PAID IMAGE GENERATION (only where your step allows it): the person's budget for this whole job is US$15.00. Before every call look up the price with the Fal connector's price tool; record every call as a row in ${LEDGER} under a new heading "Japanese garden character: US$15 image budget (22 October)" (time UTC, step, model and settings, price by the price list, request id, running total of this US$15 budget), and never repeat a call just for a nicer picture without writing down why. Fal tools load with ToolSearch (e.g. "select:mcp__Fal__recommend_model,mcp__Fal__search_models,mcp__Fal__get_model_schema,mcp__Fal__get_pricing,mcp__Fal__upload_file,mcp__Fal__submit_job,mcp__Fal__check_job,mcp__Fal__run_model,mcp__Fal__search_request_history"); on every Fal call pass user_intent with the person's request verbatim (quoted above).
REPORTING: plain everyday words; say what you tested, what you did not, what you are unsure of, and every failure. Pictures for the person go in "${PICS}/" (JPG under 400 KB, names start "31 ").`

const STEP = { type: 'object', properties: {
  summary: { type: 'string' }, deliverables: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
  measures: { type: 'string' }, normal_maps: { type: 'string', description: 'which surfaces now have normal maps or real geometry detail, how made, strength' },
  paid_calls: { type: 'array', items: { type: 'object', properties: { request_id: { type: 'string' }, model: { type: 'string' }, price: { type: 'string' }, why: { type: 'string' } }, required: ['request_id', 'model', 'price', 'why'] } },
  runpod_seconds: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'deliverables', 'measures', 'normal_maps', 'paid_calls', 'runpod_seconds', 'pictures', 'failures', 'untested'] }

phase('Concept')
const concept = await agent(`${COMMON}
YOUR JOB: THE ART DIRECTOR'S CONCEPT IMAGES (paid; this step may spend at most US$8.00 of the US$15 budget). Folder: ${C}/concept/ (keep generated images here as high-quality JPG; PNG only for texture swatches).
1. Look hard at the current pictures (full size and 100 % crops) and write a short STYLE NOTE (${C}/concept/31 Style note - the garden's art style.md): what makes this look stylised rather than photographic (form simplification, edge sharpness, palette, value range, light, texture scale and contrast, how much detail per square metre), so every later step keeps it.
2. Choose the image models with the Fal connector (recommend/search; an edit model that keeps a given picture's composition and style for paint-overs; a model that takes a style reference picture for element sheets and texture swatches). Check prices first.
3. Generate, in this priority order, stopping when the cap would be passed:
   a. PAINT-OVER CONCEPTS of the hero view: send the current hero picture to the edit model and ask for the SAME composition, SAME art style (explicitly: not photographic, not more realistic), with character added: a zigzag plank bridge whose construction makes sense (posts or stones in the pond carrying cross beams, planks or plank pairs laid across them, visible joints, pegs or iron cramps), weathered planks with worn rounded edges, cracks, darker mould and moss at the ends and near the water, a roof whose tiles vary, with moss and lichen in the valleys and drip stains, grass with tufts, colour variety and a few small flowers, moss cushions, a pond with clear water, a stone bed, reeds and iris at the edge, algae at the waterline, ripples, lily pads with flowers, maple and pine with strong characterful silhouettes. Two or three variants. Then one or two of the veranda view.
   b. ELEMENT SHEETS in the same art style (use crops of the current picture as the style reference): "Generate an image of trees and so on in the art style": the maple, the pine; the bridge construction from the side and from above; a close-up of plank wood with wear, mould and moss; roof tiles close-up; the pond edge; grass and moss ground; the stone lantern.
   c. TILEABLE TEXTURE SWATCHES in the same style (flat, top-down, evenly lit, seamless, no perspective): weathered plank wood (along the grain), roof tile field, grass-and-moss ground, moss cushion surface, pond bed stones, plaster. Check each for seams (shift by half and look) and say which are usable as colour pictures.
4. Make an index sheet "${PICS}/31 Concepts - the targets we work from.jpg" and smaller sheets per group. Record every call in the ledger as the rules say.`, { ...OPTS, label: 'concept images (art director)', phase: 'Concept', schema: STEP })

phase('Direction')
const DIRECTION = { type: 'object', properties: {
  direction: { type: 'string', description: 'plain words: what we will build from the concepts, element by element, and what we will not copy' },
  direction_file: { type: 'string' },
  briefs: { type: 'array', items: { type: 'object', properties: { name: { type: 'string', enum: ['wood', 'roof', 'ground', 'pond'] }, brief: { type: 'string' } }, required: ['name', 'brief'] } },
  acceptance: { type: 'array', items: { type: 'string' } },
}, required: ['direction', 'direction_file', 'briefs', 'acceptance'] }
const direction = await agent(`${COMMON}
YOUR JOB: THE DIRECTION, as a fresh pair of eyes. Look at every concept image and the style note (concept step's report below), compare them with the current pictures, and decide element by element which concept to follow and what NOT to copy (anything that pushes toward photo-realism, or that would not hold up in 3D from the hero and veranda cameras). Write ${C}/direction/31 Direction - from the concepts to the build.md and four builder briefs that run side by side without touching each other's objects or materials:
- "wood": the bridge rebuilt with construction that makes sense (supports in the water, cross beams, planks laid across, joints, fixings; walkable heights), every plank with real geometry character (varied width and thickness, slight warp and twist, worn rounded edges, chipped corners, end checks and splits, gaps), plus wear on the walking line, mould and moss where water and shade put them; the veranda deck, steps, posts and beams get the same treatment. Textures from the concept swatches where they work, with NORMAL MAPS (derived from height, or baked from the detailed geometry) and roughness.
- "roof": tile variety (slight colour, chips, a few slipped or broken tiles), moss and lichen in the valleys and along the eaves, drip stains, ridge and eave details; the plaster walls and caps, the stones and the lantern get character in the same style; normal maps.
- "ground": grass with character (clumps of several shapes and heights, colour variety, seed heads, a few small flowers), moss cushions with texture, worn path lines, fallen leaves, how ground meets gravel, stones and wood; normal maps on ground and moss.
- "pond" (and trees): water with clear shallow edges and deeper middle, stone and silt bed, reeds and iris, algae at the waterline, ripples (normal map), lily pads with flowers, and the maple and pine reshaped toward the concept silhouettes.
Each brief must name: the concept images to follow, the objects and materials the builder owns (by name from the starting scene), how to make normal maps (and to connect them through a Normal Map node, OpenGL convention, checked for the right direction with a test light), the guard against realism (palette and value range to keep, the style note's rules), preview views to draw, a folder ${C}/<name>/, a time-box of about 2.5 hours, and that each builder may spend at most US$1.00 of the image budget on extra swatches (with a reason).
List acceptance tests the checkers will use (for example: every plank rests on a support; no surface in the picture is flat colour at 100 %; the style note's value range is kept; the concepts' character reads at normal viewing size).
CONCEPT STEP REPORT: ${JSON.stringify(concept)}`, { ...OPTS, label: 'direction from the concepts', phase: 'Direction', schema: DIRECTION })

phase('Build')
const briefs = (direction && direction.briefs && direction.briefs.length) ? direction.briefs : ['wood', 'roof', 'ground', 'pond'].map(n => ({ name: n, brief: 'see the direction file' }))
const built = await parallel(briefs.map(b => () => agent(`${COMMON}
YOUR JOB: BUILDER "${b.name}". Read the direction file ${direction && direction.direction_file} and the style note first. Your brief:
${b.brief}
Deliver ${C}/${b.name}/stage_${b.name}.py with apply(options) that works on the open starting scene and touches only what you own (list object and material names before and after to prove it), a short test report, and 2-3 sheets for the person in "${PICS}/" named "31 ${b.name} - ...": before and after at the hero and veranda cameras and close-ups, next to the concept you followed. Draw previews on RunPod (keep .blend files and full PNGs on the store). Check every normal map's direction (a raised ridge must be lit on the side facing the light).`, { ...OPTS, label: `build: ${b.name}`, phase: 'Build', schema: STEP }).then(r => ({ name: b.name, report: r }))))

phase('Integrate and render')
const integrate = await agent(`${COMMON}
YOUR JOB: INTEGRATE AND RENDER. Folder ${C}/final/ (local copy under 40 MB; .blend and full renders on the store). Builders: ${JSON.stringify(built)}.
1. Chain the four stages on the starting scene (order: wood, roof, ground, pond unless the direction says otherwise); conflict check (each stage touched only its own things; names the weathering kit and the earlier stages rely on still exist); save garden_character.blend on the store.
2. RunPod per second: one cheap preview round (hero and veranda, 960 x 640), fix only what is clearly broken, then the finals in Cycles exactly as the earlier finals were drawn (2400 x 1600, 512 adaptive samples, denoiser, same camera, light, exposure and seed; light groups and EXR as before): hero and veranda; plus four close-ups at 1600 x 1067: the bridge from the bank, the roof eave, the pond edge, the grass and moss by the lantern.
3. Sheets in "${PICS}/": "31 Before and after - hero view.jpg" (previous final | new), "31 Before and after - veranda view.jpg", "31 Close-ups - bridge, roof, pond edge, grass.jpg", "31 New next to the concept - hero view.jpg" (concept | new).
4. List which surfaces now have normal maps and real geometry detail. Report RunPod seconds per job and the total.`, { ...OPTS, label: 'integrate and render on RunPod', phase: 'Integrate and render', schema: STEP })

phase('Check')
const CHECK = { type: 'object', properties: {
  art_style_kept: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  more_character_than_before: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  bridge_construction_makes_sense: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  each_element: { type: 'array', items: { type: 'object', properties: { element: { type: 'string' }, verdict: { type: 'string', enum: ['yes', 'nearly', 'no'] }, why: { type: 'string' } }, required: ['element', 'verdict', 'why'] } },
  claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['claim', 'holds', 'evidence'] } },
  budget_checked: { type: 'string' },
  problems: { type: 'array', items: { type: 'string' } },
  should_fix_now: { type: 'boolean' }, fixes_for_one_round: { type: 'string' }, overall: { type: 'string' }, pictures: { type: 'array', items: { type: 'string' } },
}, required: ['art_style_kept', 'more_character_than_before', 'bridge_construction_makes_sense', 'each_element', 'claims_checked', 'budget_checked', 'problems', 'should_fix_now', 'fixes_for_one_round', 'overall', 'pictures'] }
const checkPrompt = (lens, reports) => `${COMMON}
YOU ARE A FRESH-EYES CHECKER (you did none of this work). Lens: ${lens}
Open the new finals and close-ups at full size (download what you need to a scratch folder and delete it afterwards), the previous finals, the concepts, the style note and the direction's acceptance tests; make your own 100 % crops (key ones in "${PICS}/" named "31 Checker - ..."). Re-check at least three claims yourself. List problems with the cheapest fix and say whether one fix round is worth it now.
REPORTS: ${JSON.stringify(reports)}`
const LENS_ART = "ART DIRECTION: is the art style kept (not pushed toward photo-realism, per the style note), does each element (wood, bridge, roof, grass, moss, pond, trees, stone, lantern) now have the character the concepts show, read at normal viewing size, and is anything too busy, repeated, tiled or out of style."
const LENS_BUILD = "CONSTRUCTION, NORMAL MAPS, CLAIMS AND MONEY: open garden_character.blend on the store (a RunPod job) or locally if it fits, check every bridge plank rests on a support and the supports stand on the pond bed, check each claimed normal map exists, is connected through a Normal Map node and points the right way, check stages touched only their own things, re-add the image-budget ledger rows against the Fal request history (the US$15 cap) and the RunPod seconds, and grep new code for personal details or ~/.runpod."
const reports1 = { concept, direction, built, integrate }
const checks = await parallel([
  () => agent(checkPrompt(LENS_ART, reports1), { ...OPTS, label: 'check: art direction', phase: 'Check', schema: CHECK }),
  () => agent(checkPrompt(LENS_BUILD, reports1), { ...OPTS, label: 'check: construction, normal maps, money', phase: 'Check', schema: CHECK }),
])

// Fix round, rewritten after the container restart at about 09:40: one fixer per owner (parallel), then one integration and the finals, then a re-check.
phase('Fix')
const MINE = `${C}/32 Fix list - my own read of the builder previews.md`
const STYLE_NOTE = `${C}/concept/31 Style note - the garden's art style.md`
const FIX_NOTE = `
NOTE FROM THE MAIN SESSION (read first): the container restarted after the art check, so the fix round was restarted with this brief. The combined scene ${C}/final/garden_character.blend and the finals in ${C}/final/out/finals/ are on the RunPod store (see the integrate report). The RunPod stall from 07:37 to 08:30 was the account's credit running out; the person has topped it up. If your jobs wait in line for more than 5 minutes while the workers show idle, stop sending jobs, say so in your report and carry on with checks that need no card; never purge the queue or change the endpoint. Disk here: about 0.5 GB free, shared; download only JPGs under 400 KB and delete scratch downloads when done. No paid image calls in this round (the concepts already exist). The person's rule, verbatim: "These things need to be integrated into the style. So it's just part of design." Read the style note ${STYLE_NOTE} (section 0 first) and the direction's acceptance tests before changing anything. Every fix must read at normal viewing size (1200 px wide) and stay in the style: bigger, simpler, designed shapes, not more realistic texture. Keep the value range, saturation and detail-energy limits from the direction step; the squint test (blurred-luminance similarity to the previous final) should reach at least 0.92. The main session's own list of what still misses the concepts is ${MINE}; it is part of your brief.`
const CHECK_FINDINGS = checks.filter(Boolean).map(c => ({ problems: c.problems, fixes: c.fixes_for_one_round, elements: c.each_element }))
const FIXERS = [
  { name: 'wood', owns: `the bridge and the veranda deck (stage ${C}/wood/stage_wood.py and its modules)`, items: `(1) moss and mould on the walking surface, which the person asked for and which barely exists (0.6 percent olive on the left run; the claimed 9.8 percent did not hold): designed soft olive and dark-green patches at plank ends, along the gaps, on the shaded side and near the water, plus a few darker damp stains, readable at 1200 px; a greyer, weathered base on the bridge (the deck may stay warmer). (2) The same spiral knot stamped on most planks: per plank, mirror and rotate the plank pattern, vary the knot's place and size, and leave about half the planks without a knot. (3) The open outer corner at each elbow and the dark triangle under the diagonal board: close them. (4) Pegs 30 to 50 percent bigger so they read. (5) Footing stones should read where a post meets the water, without clutter. (6) Moss at the foot of the veranda steps if your stage owns that wood. Do not lose what works: the construction logic, the varied planks and the deck.` },
  { name: 'roof', owns: `the roof, the walls and caps, the rocks and stone, and the lantern (stage ${C}/roof/stage_roof.py and its modules)`, items: `(1) Rocks: the old agate-like stripes and neon-green lines in the stone colour (visible in the close-ups and in the old finals) are out of style; calm them to the style's painted stone (lines at about a third of their strength or removed, soft value blocks, a few chips and cracks). Keep the moss caps on the big rocks; they are the best match to the concept. (2) The lantern cap moss reads as a bright yellow-green sticker: darker olive, smaller, following the cap's shape with a little in the crevices (if another stage made it, say which and leave it). (3) Roof moss as soft cushions in the concept's style at the eaves and the ridge foot instead of small speckles; drip stains and slipped tiles readable at normal size (30 to 50 percent stronger, not more of them); calm the crumpled, faceted look of the glaze. (4) Wall cracks: fewer but bolder, one clean dark line each, wide enough to read at 1200 px. The integration step's ${C}/final/stage_final.py already softens the plaster-loss patches; leave that file alone.` },
  { name: 'ground', owns: `the lawn, tufts, flowers, fallen leaves on land, the worn path, the gravel kerb and the moss cushions (stage ${C}/ground/stage_ground.py and its modules)`, items: `(1) Tufts are thin and spiky, which looks more realistic, the opposite of what the person asked: make them the concept's chunky tufts (fewer, broader blades with rounded tips, plump seed heads), keeping the clumps and the variety of shapes. (2) Moss cushions repeat like bean bags (same size, same pinched crease, row after row): vary the size 0.6 to 1.5 times, cut about a third in the veranda bank, give some a round dome, and let them merge into soft carpets. (3) The worn path: the green moss blotches read as camouflage patches; make it soft bare earth with gentle value change and a few pebbles, as in the concept; the veranda path is a flat terracotta patch, give it the same soft modelling. (4) Flowers (0.02 percent of the picture) and fallen maple leaves cannot be seen: fewer but larger, readable white flower clusters and red star-shaped leaves in the concept's style. (5) The lawn between the tufts looks smeared and smoother than before: bring back gentle mottling and a little litter.` },
  { name: 'pond', owns: `the water, the pond bed and plants, the maple, the pine and the bamboo (stage ${C}/pond/stage_pond.py and its modules)`, items: `(1) The pond does not read at 1200 px (dark water, small dark pads): bigger, brighter notched lily pads (25 to 40 cm), a few pink lily flowers, a wider clear shallow band with brighter pebbles at the bank, ripple rings 1.5 times larger, a few red maple leaves floating, a dark middle. (2) The maple became darker and heavier and is the main cause of the squint miss (maple area 0.76): lift the leaf colour back toward the previous final (mean red channel was 0.48, now 0.43) while keeping the hue mix, soften the two hard-edged slabs in the veranda view, and open gaps so branches read in the hero; bring its detail energy back under the limit (+8 percent). (3) Pine: the needle fringe is long loose strands (hairy, photographic); shorten it by about a quarter and widen the strokes into chunky brush-stroke clumps as in the concept; the plated bark should read a little.` },
]
const fixers = await parallel(FIXERS.map(f => () => agent(`${COMMON}
${FIX_NOTE}
YOUR JOB: FIX ROUND, OWNER "${f.name}". You own ${f.owns}. Copy that stage and the modules it imports into ${C}/fix/${f.name}/ and change only those copies (the builder's originals stay as the record). Work through these, most noticeable at normal viewing size first:
${f.items}
Also take any problem the checkers listed below that belongs to objects or materials your stage creates (find the owner by the name prefix your stage gives them). If an item belongs to another stage, leave it and say so. Three other fixers work at the same time, each on their own stage.
TEST ON RUNPOD (per second): build the combined garden with your fixed stage in place of the original and the other three stages and ${C}/final/stage_final.py unchanged. Copy ${C}/final/build_character.py and a job file into your folder and point them at your copy; never write in ${C}/final/ or another owner's folder, and never save over ${C}/final/garden_character.blend. Conflict-check that your stage still touches only its own things. Draw previews at the hero and veranda cameras (1200 x 800, Cycles, enough samples to judge) and at the close-up cameras that show your elements. Measure value range, saturation, detail energy in your elements' boxes, and the squint test against the previous final.
DELIVER: the fixed stage in ${C}/fix/${f.name}/ (apply(options), idempotent, same name as the original); a sheet "${PICS}/31 Fix - ${f.name} - before and after.jpg" (integrated final now | after your fix | the concept you followed, same views); and a report of every item (fixed, partly or not, with evidence).
CHECKERS' FINDINGS: ${JSON.stringify(CHECK_FINDINGS)}
YOUR BUILDER'S REPORT: ${JSON.stringify((built.find(b => b.name === f.name) || {}).report || null)}
INTEGRATE REPORT: ${JSON.stringify(integrate)}`, { ...OPTS, label: `fix: ${f.name}`, phase: 'Fix', schema: STEP }).then(r => ({ name: f.name, report: r }))))

const final2 = await agent(`${COMMON}
${FIX_NOTE}
YOUR JOB: PUT THE FIXES TOGETHER AND DRAW THE FINALS. Folder ${C}/fix/final/ (small local files only; .blend and full renders on the store).
1. Chain the stages in the same order as the first integration (wood, roof, ground, pond, then ${C}/final/stage_final.py), using each fixed stage from ${C}/fix/<owner>/ where it exists; fall back to the builder's original and say so where it does not. Conflict check as before (each stage touched only its own things; nothing the weathering kit or the earlier stages rely on vanished). Save garden_character_fix.blend on the store; never save over ${C}/final/garden_character.blend.
2. Draw on RunPod per second, exactly as the first finals were drawn (2400 x 1600, 512 adaptive samples, denoiser, same cameras, light, exposure and seed, light groups and EXR): hero and veranda, plus the same four close-ups at 1600 x 1067 (bridge from the bank, roof eave, pond edge, grass and moss by the lantern).
3. Measure as the first integration did: value range and saturation against the previous final, the squint test (target 0.92), detail energy per box, flat-colour windows, and the light groups adding up to the picture. Re-check every normal map in the saved scene.
4. Sheets in "${PICS}/" (JPG under 400 KB): "31 Final - hero view.jpg" and "31 Final - veranda view.jpg" (the new finals alone, 1600 px wide), "31 Before and after - hero view.jpg" and "31 Before and after - veranda view.jpg" (previous final | first integration | after the fixes), "31 Final - close-ups.jpg", "31 Final - next to the concept - hero view.jpg".
5. Report RunPod seconds per job and the total.
FIXERS' REPORTS: ${JSON.stringify(fixers)}
FIRST INTEGRATION REPORT: ${JSON.stringify(integrate)}`, { ...OPTS, label: 'fix: put together and draw finals', phase: 'Fix', schema: STEP })

const recheck = await agent(checkPrompt(LENS_ART + ' ALSO: ' + LENS_BUILD + ' THIS IS THE RE-CHECK AFTER THE FIX ROUND: judge the new finals in ' + C + '/fix/final/ against the first integration and the concepts, and say for each first-check problem whether it is now fixed.', { integrate, first_checks: checks, fixers, final2 }), { ...OPTS, label: 're-check', phase: 'Fix', schema: CHECK })
return { concept, direction, built, integrate, checks, fixers, final2, recheck }
