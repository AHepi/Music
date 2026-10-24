export const meta = {
  name: 'reusable-grime-cracks-stains-weeds-moss',
  description: 'A reusable kit of grime, cracks, stains, weeds and moss layers, tuned on the pit village street (copy only) and proven to carry over to the Japanese courtyard: study, shared masks, three builders, integration, reuse proof, two fresh checks, one fix round, one painter test',
  phases: [
    { title: 'Study', detail: 'period reference, our pipeline, the painted look, the Japanese courtyard' },
    { title: 'Design', detail: 'one build plan with shared masks and interfaces' },
    { title: 'Foundation', detail: 'shared masks module and test harness' },
    { title: 'Build', detail: 'walls, ground, weeds and moss pieces in parallel' },
    { title: 'Integrate', detail: 'one stack with wetness, joints and rubbish; full test set and plates' },
    { title: 'Reuse proof', detail: 'the same kit on the Japanese courtyard with only a new settings file' },
    { title: 'Check', detail: 'two fresh checkers, one fix round, re-check' },
    { title: 'Paint', detail: 'one repaint to see what survives the painter' },
  ],
}

const SC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
const PW = SC + '/proc-work'
const SW = PW + '/street_wet'
const RR = SW + '/relief_and_rubbish'
const R2 = SW + '/painter_round_2'
const PT = SW + '/painter_test'
const G = SW + '/grime_and_growth'
const KIT = PW + '/kits/weathering'
const JC = '/home/user/Music/japanese-courtyard'
const AW = SC + '/astra-work'
const PICS = PW + '/25 Street grime, cracks, stains, weeds and moss - pictures'
const LEDGER = PW + '/SPENDING - paid image generation ledger.md'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
const OPTS = { model: 'sonnet', effort: 'xhigh' }

const COMMON = `
CONTEXT: The person is not a programmer; they test ideas by having helpers build them. They make a painted explainer film set in a 1926 County Durham pit village: the street is built in Blender, drawn as a "plate", repainted by an image model (the "painter", Flux 3 edit on fal) in the series' style, and the film's three.js "stage" projects the painting back onto the 3D set. What the audience sees is the painting, so anything added must read clearly in the plate at the painter's size (the painter gets the plate at about 0.4 to 0.5 of 1536x2730) and survive the repaint.
THE PERSON'S REQUESTS, verbatim: "The next thing to apply to the streets is things like: grime, cracks, stains, weeds and moss." and then "They should be reusable too. Which is perfect. Because next is the Japanese forecourt again".
REUSE IS A MUST: build this as a reusable WEATHERING KIT, not street-only code. The kit's code lives in ${KIT}/ (layers, masks, scatter, apply, harness), and everything that belongs to one set lives in a small per-set settings file (${KIT}/sets/pit_village_street.json, and later ${KIT}/sets/japanese_courtyard.json): which materials or objects get which layer, which objects count as walls, ground, edges, drips, iron, wood, stone, plaster, gravel, roof; the set's light directions for shade; traffic or footfall areas; scale. The looks (a sooty 1926 coal town; a mossy Japanese courtyard) are PRESETS of the same layers' dials in a settings file, not separate code. Layers must read only generic inputs (position, normal, distance-to-wall and edge pictures made by the kit's own geometry reader from the set's settings, cavity/curvature, shade, wetness masks only if a wetness layer is present) and must work on any material by inserting before its Principled BSDF, whatever is wired into it. No street object names, coordinates or sizes inside the kit code. The next job is the Japanese courtyard (its build script ${JC}/build_courtyard.py; saved scenes in ${AW}/out/*.blend; built with the person's Astra add-on, unpacked read-only at ${SC}/astra-upload; its project story ${JC}/Japanese courtyard - project story.md): a wooden hall with paper screens and a tiled roof, a pond and zigzag bridge, rocks, a stone lantern, raked gravel, stepping stones, moss and pebbles already grown by the add-on. Never write in ${JC} or the add-on folder.
WHAT EXISTS (all on the street COPY; never change the film project):
- ${SW}/set_copy/ : the street copy (read-only for you). ${SW}/tools/ : the WETNESS layer (wetness_layer.py, apply_wetness_to_set.py) and the picture runner 22_render_eevee.py (states must start with "today"). Wetness recipe note: ${SW}/09 Recipe*.md.
- ${RR}/ : the JOINTS layer (dark, dull sett joints that survive wet light; setts/tools/joint_layer.py, apply_joints_to_set.py, setts/maps) and the RUBBISH layer + scattered pieces (rubbish/tools/rubbish_layer.py, rubbish_pieces.py, apply_rubbish_to_set.py, make_places_pictures.py; rubbish/maps/places_street_*.png and places_lockout_*.png = distance-to-wall, gutter, doorstep, prop-ring pictures made from the real geometry). Recipe note: "${RR}/10 Recipe - sett relief and rubbish - how it is made.md". The 22-picture lighting test set, its runner and the joint measuring script (measure_grid_visibility.py) are in ${RR}/setts/tools and ${RR}/rubbish/tools. The fresh checker's notes: ${RR}/check_round_1/.
- A second painter round is running now in ${R2}/ (it is fixing the rubbish pieces: flatter coal lumps, more gutter density, curved straw, joint ticks). Do not write there; read its results if they exist.
- Earlier texture work you may reuse: ${PW}/recipes/slate_layers/layers/ (moss.py, damage.py: node-made moss clumps and chips), the cookbook ${PW}/cookbook/06 Cookbook - start here.md, reuse notes ${PW}/cookbook/07*.md. (The file "LATER - realistic moss and damage ... NOT STARTED.md" is a different, slate-only test: do not start it.)
- Scenario's Blender skills may be installed at /home/user/Music/.claude/skills/ (another job is installing and trying them now; read only, if present: scenario-blender-texturing-shading has wear and grime mask layering, scenario-blender-geometry-nodes has scatter helpers).
RENDERING: Blender 5.2.2 at ${BLENDER}, always -b --disable-autoexec. Draw pictures on the rented RunPod machine (50-100x faster than here): read ${SC}/runpod/HOW TO RENDER ON THE RENTED MACHINE - cached.md and use ONLY ${SC}/runpod/render_client_cached.py (if an old script calls render_client.py or an old rent_run client, use the cached client instead). Upload what a run needs (same absolute paths there; the store already has set_copy, tools and maps, not relief_and_rubbish or your folders; upload only what you need). Other jobs share the machine; that is fine. Batch your renders (one run, many pictures).
HARD RULES: never print, copy, move or read anything in ~/.runpod; never write into the film project (/home/user/Music/austerity-explainer), ${SW}/set_copy, ${SW}/tools, ${RR}, ${R2} or ${PT}: copy what you need into your own folder under ${G}/; do not commit or push; do not stop or end rented machines; disk is tight (about 2 GB free shared by three jobs): keep your own folder under the size your step gives, save working pictures as JPG, delete big scratch files, and stop and report if free space falls under 0.9 GB. No paid image calls except in the Paint step.
REPORTING: plain everyday words in every text field (explain an unavoidable technical word in one sentence). Say what you tested, what you did not, what you are unsure of, and every failure. Pictures worth showing go in "${PICS}/" (JPG under 400 KB; names start "25 " and say what they show).`

const STUDY_SCHEMA = { type: 'object', properties: {
  findings: { type: 'string', description: 'the main report, plain words, organised by element: grime, cracks, stains, weeds, moss (and lichen if relevant)' },
  rules: { type: 'array', items: { type: 'object', properties: { element: { type: 'string' }, where: { type: 'string' }, how_much: { type: 'string' }, size_and_shape: { type: 'string' }, colour_dry_and_wet: { type: 'string' }, why: { type: 'string' }, confidence: { type: 'string' }, source: { type: 'string' } }, required: ['element', 'where', 'how_much', 'size_and_shape', 'colour_dry_and_wet', 'why', 'confidence', 'source'] } },
  risks: { type: 'array', items: { type: 'string' } },
  files: { type: 'array', items: { type: 'string' } },
}, required: ['findings', 'rules', 'risks', 'files'] }

phase('Study')
const studies = await parallel([
  () => agent(`${COMMON}

YOUR JOB: PERIOD REFERENCE (no Blender work). Find out, with web searches and reading (WebSearch/WebFetch; load them with ToolSearch if needed), what the streets and terraced houses of a 1920s County Durham / Northumberland coal-mining village looked like close up, as to: GRIME (coal soot on brick and stone, black run-off streaks under sills, copings, gutters and downpipes, soot on window heads, dirt splash at wall feet, grime on doors and thresholds), CRACKS (in stone flags, kerbs, setts, render, steps; broken corners; where traffic and frost crack them), STAINS (rust under iron: lamp posts, downpipes, railings, the brazier drum; water marks; tar; ash; lime/whitewash on plinths and steps — donkey-stoned or whitened doorsteps were common in the north), WEEDS (which plants grow in sett joints, wall feet, gutters and cracks in a sooty northern town: annual meadow-grass, dandelion, plantain, groundsel, chickweed, shepherd's purse, mosses, liverworts; how big, how many, when in the year), MOSS and LICHEN (on north-facing or shaded wall feet, roof slates, copings, damp corners near downpipes, between setts away from traffic; colours dry and wet). Good sources: Beamish Museum's 1900s pit village and its photographs, period photographs of Durham colliery rows, accounts of pit-village life, botanical sources on urban street plants and mosses in polluted air (soot pollution killed lichens: say what that means for 1926). For each element give placement rules a builder can turn into masks: where (exact places on our street: road crown, road edges, gutters, kerbs, pavement flags, wall feet, sills, doorsteps, under downpipes, corners), how much (share of that surface), size and shape, colours dry and wet (as sRGB numbers or ranges), why, how sure you are, and the source (link). Note what would be WRONG for 1926 (e.g. graffiti, modern litter, heavy lichen in a sooty town, lush weeds on a busy road). Write your report also as ${G}/study/10 Research - grime, cracks, stains, weeds and moss in a 1926 pit village.md (folder limit 20 MB).`, { ...OPTS, label: 'study: period reference', phase: 'Study', schema: STUDY_SCHEMA }),
  () => agent(`${COMMON}

YOUR JOB: OUR PIPELINE (technical study). Read the wetness, joints and rubbish layers, their apply scripts, the places pictures and the recipe notes, and open the street copy in Blender (headless, list only, nothing saved) to report: every material and object family in the street copy that grime, cracks, stains, weeds or moss could go on (road setts, pavement flags, kerbs, gutter channel stones, house walls by type, sills, door frames, steps, doorsteps, downpipes, lamp posts, roofs, the colliery buildings, props), with their names, how their materials are built and where the new layers could hook in (after which layer, before the Principled BSDF); what each layer already exposes that the new ones can read (Wet Mask, Puddle Mask, joint cavity, rubbish total, places pictures, normal z, object coordinates); what masks are missing and how to make them from the geometry the way make_places_pictures.py does (shade/north-facing walls from the scene's light directions; under-sill and under-downpipe run-off lines; traffic lanes and the road crown; wall corners; edges of flags and kerbs); how the lockout shot file differs from the street copy (props, cameras); the cameras used by the test set and the plates; how long a picture takes on the rented machine; and the traps earlier builders hit (states order, stale pictures on the rented machine, shadow-noise grit in EEVEE, white ticks, the painter crushing darks in the stage). Also read the slate moss.py and damage.py layers and Scenario's texturing skill if installed, and say what can be reused as is. Write ${G}/study/11 Pipeline - where new layers hook into the street.md (folder limit 20 MB).`, { ...OPTS, label: 'study: our pipeline', phase: 'Study', schema: STUDY_SCHEMA }),
  () => agent(`${COMMON}

YOUR JOB: THE PAINTED LOOK (what survives the painter). Look (read-only) at the series' paintings and how the painter treated detail: the film's lockout and notice corner paintings and behind paintings, the style picture the painter test used (see ${PT}/notes - wet street painter test.md, section 3), the first wet painting ${PT}/pictures/wet_painting_lined_up.png against its plate, and, if they exist, the second round's results in ${R2}/paint/. Measure, on matching crops of plate and painting: how small and how faint a feature can be in the plate and still be painted (the round 1 checker said the tiniest rubbish chips may be dropped at 0.4 size; sett joints of 1.6 cm survived as lines); what the painter does to soot streaks, stains, moss patches, weeds and cracks if the earlier paintings show any (the old dry lockout painting has a soot ring round the drum, dark plinths, etc.); how the stage's brightness curve treats darks (painted 0.08 becomes 0.02). Turn this into targets a builder can measure in the plate: minimum size in plate pixels at 1536x2730, minimum contrast against the surface around it, the darkest value that will not be crushed, how much is too much (when grime turns the whole street into one dark mush), and the order of importance for the viewer. Write ${G}/study/12 Painted look - what survives the painter.md with crops (folder limit 30 MB).`, { ...OPTS, label: 'study: the painted look', phase: 'Study', schema: STUDY_SCHEMA }),
  () => agent(`${COMMON}

YOUR JOB: THE SECOND SET, so the kit is designed to carry over. (1) Open the Japanese courtyard's newest saved scene from ${AW}/out/ (pick the one matching the final photo; say which and why; headless, list only, never save over it) or, if none fits, read ${JC}/build_courtyard.py to learn its objects. List every surface family (wood: posts, veranda, bridge, planks; paper screens; ceramic roof tiles; plaster or walls; stone: rocks, lantern, stepping stones; raked gravel; earth and the add-on's moss and pebbles; water edge), how their materials are built (some are simple node materials, some vertex-colour, some the add-on's), and where a kit layer could hook in. (2) Research briefly (web) how grime, cracks, stains, weeds, moss and lichen look in a real Japanese temple or garden courtyard: moss on stones, lanterns and roof edges; lichen; dark water and rot stains at the feet of wooden posts and under roof drips; streaks on plaster; weeds and grass in gravel edges and between stepping stones; cracks and chips in stone; how wet weather changes them. (3) Say what the kit must handle so ONE set of layers covers both this courtyard and a sooty 1926 coal-town street (e.g. wood and plaster, not only brick and setts; gravel, not only setts; no road crown; footfall paths instead of traffic lanes), and what would be wrong to carry over (coal soot, coal-town rubbish). Write ${G}/study/12b Second set - the Japanese courtyard.md (folder limit 20 MB).`, { ...OPTS, label: 'study: the Japanese courtyard', phase: 'Study', schema: STUDY_SCHEMA }),
])
const [refStudy, pipeStudy, lookStudy, courtyardStudy] = studies

phase('Design')
const DESIGN_SCHEMA = { type: 'object', properties: {
  plan: { type: 'string', description: 'the build plan in plain words: layers, order, masks, dials, what each builder makes, how they fit, test set, pass lines' },
  plan_file: { type: 'string' },
  builders: { type: 'array', items: { type: 'object', properties: { name: { type: 'string', enum: ['walls', 'ground', 'growth'] }, brief: { type: 'string' } }, required: ['name', 'brief'] } },
  foundation_brief: { type: 'string' },
  pass_lines: { type: 'array', items: { type: 'string' } },
}, required: ['plan', 'plan_file', 'builders', 'foundation_brief', 'pass_lines'] }
const design = await agent(`${COMMON}

YOUR JOB: DESIGN one build plan from the four studies below, for the reusable WEATHERING KIT (code in ${KIT}/, per-set settings files, looks as presets). Write it to ${G}/design/13 Plan - grime, cracks, stains, weeds and moss for the street.md.
Shape of the work (fixed): a FOUNDATION helper first builds one shared masks module (all the new "where" masks, made from the real geometry and the existing places pictures, readable by every layer, plus the test harness: cameras, the lighting test set, the runner on the rented machine, measuring scripts, sheet maker); then THREE BUILDERS work in parallel on separate files that do not touch each other:
- "walls": everything on house walls and their trims (soot grime, run-off streaks, rust and water stains, whitened or worn doorsteps if the period study supports them, wall-foot damp, moss/lichen on walls, cracks in render or stone if justified);
- "ground": everything painted on the road, flags, kerbs and gutter stones (cracks and broken corners, stains: rust under iron, tar, water marks, ash; ground grime and traffic polish; flat moss in joints and at edges away from traffic);
- "growth": 3D weeds and moss cushions as scattered pieces (Geometry Nodes, like the rubbish pieces): grass tufts, dandelion and plantain rosettes, moss cushions in sett joints near the edges, wall feet, flag cracks and gutters, sized and placed by the period rules, wet where the street is wet, never on the road's middle or in heavy traffic lanes, and sensible next to the rubbish (decide: weeds may grow through thin rubbish but not on heaps).
Then an INTEGRATOR chains everything with WETNESS, JOINTS and RUBBISH on the street copy and the lockout shot file, keeps every layer switchable with its own master dial (0 = exactly as before), and draws the full test set and plates.
Decide and write down: the kit's folder layout and the per-set settings file format (with the street's file filled in and a first draft of the courtyard's, so you prove the format covers both); layer order on each material and why; each mask (name, formula in words, from which data); each layer's dials (name, range, default); what each builder must deliver (node group file, apply function, self-test proving dial 0 changes nothing, debug views of masks, a sheet); the test set (reuse the 22-lighting set and add close views of a wall foot, a downpipe, a doorstep, a gutter and a cracked flag); the pass lines, at least: the sett joints still pass as before (21 of 22 with puddle and rubbish dots left out, report all-dots too); the wet look kept; each element visible at the painter's size by the painted-look study's targets; nothing modern or wrong for 1926; the street not turned into one dark mush (give a number); no weeds or moss on the road crown or the traffic lanes; same drawing time within +30 %.
Give each builder a complete brief (what to make, the masks to read from the foundation, file names, their own folder ${G}/<name>/, folder limit 120 MB, time-box about 2.5 hours of work, pictures to save).
PERIOD STUDY: ${JSON.stringify(refStudy)}
PIPELINE STUDY: ${JSON.stringify(pipeStudy)}
PAINTED-LOOK STUDY: ${JSON.stringify(lookStudy)}
SECOND-SET STUDY (Japanese courtyard): ${JSON.stringify(courtyardStudy)}
Every builder's brief must say: code goes in ${KIT}/<part>/ with no set-specific names or numbers; set-specific choices go in the settings files; work pictures and notes for the street go in ${G}/<part>/.`, { ...OPTS, label: 'design the build plan', phase: 'Design', schema: DESIGN_SCHEMA })

const BUILD_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' }, what_changed: { type: 'string' }, controls: { type: 'string' }, measures: { type: 'string' },
  deliverables: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, what: { type: 'string' } }, required: ['path', 'what'] } },
  renders: { type: 'array', items: { type: 'string' } }, timings: { type: 'string' },
  failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'what_changed', 'controls', 'measures', 'deliverables', 'renders', 'timings', 'failures', 'untested'] }

phase('Foundation')
const foundation = await agent(`${COMMON}

YOUR JOB: THE FOUNDATION for three builders who will start right after you. Read the plan ${design && design.plan_file} and build exactly what it asks of the foundation: kit code in ${KIT}/ (the geometry reader that makes the "where" pictures from any set's settings file, the shared masks, the apply skeleton, the harness), the street's settings file in ${KIT}/sets/, and street work pictures in ${G}/foundation/ (folder limit 80 MB in all). Prove the geometry reader is generic by also running it, untuned, on the Japanese courtyard's saved scene with the draft courtyard settings file and saving its mask pictures ("${PICS}/25 Masks - the same reader on the Japanese courtyard.jpg"):
${design && design.foundation_brief}
Deliver: the shared masks module (each mask as a function/node output the builders can call, plus any new "places" pictures made from the real geometry for BOTH the street copy and the lockout shot file), debug pictures of every mask from the main, lockout and close cameras (a sheet in "${PICS}/25 Masks - where each thing may go.jpg"), the test harness (job writer + runner on the rented machine with the stale-picture trap handled, the measuring scripts including the joint measure, the sheet maker), a short "HOW TO USE.md" for the builders, and a self-test showing the module changes nothing in the pictures by itself. Measure and report how long one test-set run takes on the rented machine.`, { ...OPTS, label: 'foundation: shared masks and harness', phase: 'Foundation', schema: BUILD_SCHEMA })

phase('Build')
const builders = (design && design.builders && design.builders.length) ? design.builders : [{ name: 'walls', brief: 'see plan' }, { name: 'ground', brief: 'see plan' }, { name: 'growth', brief: 'see plan' }]
const built = await parallel(builders.map(b => () => agent(`${COMMON}

YOUR JOB: BUILDER "${b.name}". Kit code goes only in ${KIT}/${b.name}/ (no set-specific names or numbers in it; set-specific choices go in the settings files' "${b.name}" section); street work pictures and notes in ${G}/${b.name}/ (folder limit 120 MB in all; time-box about 2.5 hours). Read the plan ${design && design.plan_file} and the foundation's HOW TO USE.md first; use the foundation's masks and harness, do not change the foundation's files (copy and extend in your folder if you must, and say so). Two other builders work at the same time on the other parts; do not touch their folders.
YOUR BRIEF:
${b.brief}
FOUNDATION REPORT: ${JSON.stringify(foundation)}
Work in rounds: build, draw small pictures on the rented machine, look at them yourself at 100 % and at painter size, measure against the plan's pass lines, adjust. Prove your master dial at 0 changes nothing. Make a sheet for the person ("${PICS}/25 ${b.name} - before and after.jpg") and one showing what each main dial does. Write your part of the recipe note as ${G}/${b.name}/14 Recipe - ${b.name} - how it is made.md.`, { ...OPTS, label: `build: ${b.name}`, phase: 'Build', schema: BUILD_SCHEMA }).then(r => ({ name: b.name, report: r }))))

phase('Integrate')
const integrate = await agent(`${COMMON}

YOUR JOB: THE INTEGRATOR. Work in ${G}/integrated/ (folder limit 150 MB). Builders' reports: ${JSON.stringify(built)}. Foundation: ${JSON.stringify(foundation)}. Plan: ${design && design.plan_file}.
1. Make ONE kit apply entry point (${KIT}/apply_weathering.py: apply(set_settings_file, look_preset, **dials), remove()) that puts on the three new parts by the settings file, plus a small street wrapper that puts on, in order, WETNESS, JOINTS, RUBBISH and then the kit, on the street copy and on the lockout shot file (both opened in memory, never saved over), with every layer's master dial and a remove(). If the second painter round has finished its plate step (${R2}/plate/ has its fixed rubbish tools and a report), use its fixed rubbish tools (copied); otherwise round 1's, and say which.
2. Resolve overlaps the builders could not see (e.g. moss under rubbish heaps, stains under weeds, grime darkening the joints): fix the order or masks, and write each decision down.
3. Draw on the rented machine: the whole 22-lighting test set (dry, wet, heavy) with everything on, and with the new parts off (the before), plus the close views the plan names; measure the joints exactly as before (left-out dots and all dots), the darkness of the whole street (the plan's mush number), each element's visibility at the painter's size, drawing time.
4. Draw the full-size lockout plate wet AND dry (1536x2730, the plate settings of the final plate: EEVEE, shadow rays 4 / steps 16, 64 samples, wet 0.85 / puddles 0.5, lighting B) and the main street camera full size wet: save PNGs in ${G}/integrated/plates/ and half-size JPGs for the person.
5. Sheets for the person in "${PICS}/": "25 Before and after - lockout plate wet.jpg", "25 Before and after - street view wet and dry.jpg", "25 Close-ups at 100 percent.jpg", "25 All lightings - joints still pass.jpg".
6. The combined recipe note ${KIT}/15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made.md (every dial, what it does, the order, how to switch each off, how to add a new set: the settings file fields, step by step).`, { ...OPTS, label: 'integrate and draw plates', phase: 'Integrate', schema: BUILD_SCHEMA })

phase('Reuse proof')
const reuse = await agent(`${COMMON}

YOUR JOB: THE REUSE PROOF. Apply the finished kit (${KIT}/, entry point apply_weathering.py; integrator's report: ${JSON.stringify(integrate)}) to the Japanese courtyard's saved scene (from ${AW}/out/; opened in memory, never saved over) using ONLY a settings file (${KIT}/sets/japanese_courtyard.json, finish the designer's draft) and a first rough "mossy Japanese courtyard" look preset (no coal soot, no coal-town rubbish): moss on stones, lantern and roof edges, lichen, water and rot stains at post feet and under roof drips, streaks on plaster, weeds in gravel edges and between stepping stones, cracks and chips in stone. Do NOT change any kit code; if something cannot be done by settings alone, write down exactly what and why (that is a finding, not a failure to hide). Draw on the rented machine, at small size, the courtyard's camera before and after, and two close views (lantern and rocks; hall posts and veranda), dry only. Time-box about 1.5 hours; folder ${G}/reuse_proof/ limit 60 MB. Sheet for the person: "${PICS}/25 Reuse - the same kit on the Japanese courtyard.jpg". This is a first rough pass to prove reuse, not the finished courtyard look (that is the next job).`, { ...OPTS, label: 'reuse proof: Japanese courtyard', phase: 'Reuse proof', schema: BUILD_SCHEMA })

phase('Check')
const CHECK_SCHEMA = { type: 'object', properties: {
  reads_as_1926_pit_village: { type: 'string', enum: ['yes', 'nearly', 'no'] },
  each_element: { type: 'array', items: { type: 'object', properties: { element: { type: 'string' }, verdict: { type: 'string', enum: ['yes', 'nearly', 'no'] }, why: { type: 'string' } }, required: ['element', 'verdict', 'why'] } },
  joints_still_pass: { type: 'string' },
  claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, holds: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['claim', 'holds', 'evidence'] } },
  problems: { type: 'array', items: { type: 'string', description: 'what, where (picture path and crop), why a viewer would notice, the cheapest fix' } },
  should_fix_now: { type: 'boolean' }, fixes_for_one_round: { type: 'string' }, overall: { type: 'string' },
  pictures: { type: 'array', items: { type: 'string' } },
}, required: ['reads_as_1926_pit_village', 'each_element', 'joints_still_pass', 'claims_checked', 'problems', 'should_fix_now', 'fixes_for_one_round', 'overall', 'pictures'] }
const checkPrompt = (lens, reports) => `${COMMON}

YOU ARE A FRESH-EYES CHECKER (you did none of this work). Lens: ${lens}
Open the plates and sheets yourself at full size and 100 % crops (make your own crops; save the telling ones in ${G}/check/ and the key ones in "${PICS}/" named "25 Checker - ..."). Re-run at least three measurements yourself from the saved files. Judge each element (grime, cracks, stains, weeds, moss) yes / nearly / no. List problems with the cheapest fix, and say whether one fix round is worth it now (only for faults a viewer would notice at film size).
REPORTS: ${JSON.stringify(reports)}`
const LENS_ART = 'ART DIRECTOR AND PERIOD: does the street read as a lived-in 1926 Durham pit village at film size, dry and wet; is anything too much, too even, too clean, wrong for the period, repeated or tiled; do the elements sit where water, soot, feet and shade would put them; will the painter keep them (compare with the painted-look study\'s targets).'
const LENS_MEASURE = 'MEASUREMENT, CLAIMS AND REUSE: re-measure the joints (left-out and all dots), the darkness of the street, drawing time, visibility at painter size; check every master dial at 0 gives the old picture; check no weeds or moss on the crown or traffic lanes; check the builders\' and integrator\'s claims against the files; regressions in the wet look or rubbish; and REUSE: grep the kit code for street object names, coordinates or sizes, check the courtyard ran from settings alone, and list anything that would block the next job on the courtyard.'
const reports1 = { plan_file: design && design.plan_file, foundation, built, integrate, reuse }
const checks = await parallel([
  () => agent(checkPrompt(LENS_ART, reports1), { ...OPTS, label: 'check: art director and period', phase: 'Check', schema: CHECK_SCHEMA }),
  () => agent(checkPrompt(LENS_MEASURE, reports1), { ...OPTS, label: 'check: measurement and claims', phase: 'Check', schema: CHECK_SCHEMA }),
])
let fix = null, recheck = null
if (checks.filter(Boolean).some(c => c.should_fix_now)) {
  fix = await agent(`${COMMON}

YOUR JOB: ONE FIX ROUND on the integrated street (${G}/integrated/; copy, never overwrite the builders' folders; folder limit for ${G}/fix/ 100 MB). The two checkers found: ${JSON.stringify(checks.filter(Boolean).map(c => ({ problems: c.problems, fixes: c.fixes_for_one_round })))}
Earlier reports: ${JSON.stringify(reports1)}
Make the fixes a viewer would notice first; redraw what they affect (test set, close views, both full-size lockout plates and the street view) with the same settings; re-measure; save before/after sheets in "${PICS}/" named "25 Fix - ...". Update the combined recipe note.`, { ...OPTS, label: 'fix round', phase: 'Check', schema: BUILD_SCHEMA })
  recheck = await agent(checkPrompt(LENS_ART + ' ALSO: ' + LENS_MEASURE, { ...reports1, first_checks: checks, fix }), { ...OPTS, label: 're-check after fixes', phase: 'Check', schema: CHECK_SCHEMA })
}

phase('Paint')
const PAINT_SCHEMA = { type: 'object', properties: {
  summary: { type: 'string' }, what_survived: { type: 'array', items: { type: 'object', properties: { element: { type: 'string' }, survived: { type: 'string', enum: ['yes', 'partly', 'no'] }, evidence: { type: 'string' } }, required: ['element', 'survived', 'evidence'] } },
  paid_calls: { type: 'array', items: { type: 'object', properties: { request_id: { type: 'string' }, price: { type: 'string' } }, required: ['request_id', 'price'] } },
  pictures: { type: 'array', items: { type: 'string' } }, failures: { type: 'array', items: { type: 'string' } }, untested: { type: 'array', items: { type: 'string' } },
}, required: ['summary', 'what_survived', 'paid_calls', 'pictures', 'failures', 'untested'] }
const paint = await agent(`${COMMON}

YOUR JOB: ONE PAINTER TEST (paid; work in ${G}/paint/, folder limit 60 MB). The person's money rule: "Just do it. $20 budget, ask free. Over that, start asking". This step may spend at most US$1.00. Before the call, look up the price with the Fal connector's price tool; record the call as a row in ${LEDGER} under "Against the US$20 budget" (time UTC, job, model and settings, price, request id, running total — add to the running total the other rows already there). Fal tools load with ToolSearch (e.g. "select:mcp__Fal__get_pricing,mcp__Fal__upload_file,mcp__Fal__submit_job,mcp__Fal__check_job,mcp__Fal__run_model"); on every Fal call pass user_intent with the person's request: "The next thing to apply to the streets is things like: grime, cracks, stains, weeds and moss."
Take the final full-size WET lockout plate with everything on (from the fix round if there was one: ${JSON.stringify(fix ? fix.deliverables : (integrate && integrate.deliverables))}). Repaint it ONCE with the same painter, settings and way of sending as the second painter round, if it has finished (${R2}/paint/briefs/ and its request file), otherwise as the first painter test (${PT}/briefs/brief_new_wet.txt, ${PT}/painter_request_and_result.json), adding to the brief only: "keep the soot grime, run-off streaks, stains, cracks, weeds and moss where image 1 has them, at the same size and strength, painted in image 2's hand". Line it up with the lining-up tool copy (${PT}/alignment/), then judge, element by element, what survived (crops of plate and painting side by side at the same size), and whether the painting still reads as the series' style. At most one call (a second only if the first failed outright; write down why). Sheet for the person: "${PICS}/25 Painter test - plate and painting.jpg" and "25 Painter test - close-ups.jpg".`, { ...OPTS, label: 'paint: one repaint', phase: 'Paint', schema: PAINT_SCHEMA })

return { studies: { refStudy, pipeStudy, lookStudy, courtyardStudy }, design, foundation, built, integrate, reuse, checks, fix, recheck, paint }
