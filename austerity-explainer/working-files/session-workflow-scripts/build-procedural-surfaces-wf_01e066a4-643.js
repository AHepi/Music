export const meta = {
  name: 'build-procedural-surfaces',
  description: 'Six builders reproduce the six reference surfaces with Blender procedural recipes (pixel-accurate first), then scale and transfer them; an independent verifier re-checks each result',
  phases: [{ title: 'Build', detail: 'analyse -> describe -> generate -> compare, then variation, area, resolution, transfer, guides' }, { title: 'Verify', detail: 'independent re-run of scores, audit and no-cheating check' }],
}

const ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const SHARED = `You are one of six builders. Each builder takes ONE reference surface and works it end to end. FIRST read ${ROOT}/PROCEDURAL_NOTES.md completely (the job, the REVISED SUCCESS DEFINITION, the tools in lib/ and lib/contrib, what the five research guides found, the house rules). Then read the 'short version' of each research guide and every section about your surface in ${ROOT}/research/ ('02 Research - ...' files; they are long: read what you need, not everything), then look at your reference (colour.png, normal.png, height_as_uploaded.png in ${ROOT}/reference/<surface>/) with the Read tool, zoomed crops included (make crops with cv2 and save them in your folder). Blender: ${BLENDER} -b --disable-autoexec -t 2 --python SCRIPT.py -- ARGS (CPU only; several builders run at once, so keep exploration renders at 384-512 px and bake 1254 px only for real checks). The person is not a programmer: plain everyday language in everything you write for them, code with full plain-word names and a plain note at the top of each file, say what you tested and did not, never say something works unless you ran it, and record failures and dead ends (they are part of the guide).

THE JOB IN ONE PARAGRAPH: the first step is pixel-accurate reproduction of your reference (colour, height, normal) with a procedural Blender recipe driven by a compact fitted description (audit it with lib/description_audit.py; no picture data, no masks, no pixel arrays, no embedded images; the generator never reads the reference, only the description; analysis scripts may read the reference). The end goal is a METHOD: a generic generator that, given different descriptions, makes unlimited new good tiles and bigger areas, plus written lessons that transfer to surfaces nobody gave us. Measure with lib/pixel_compare.py (dot for dot, tiers none/layout/close/exact, difference sheet) and lib/texture_compare.py (same kind of surface). LOOK at every sheet yourself. Fix the biggest visible error first.

Work in this order and keep your folder tidy (${ROOT}/recipes/<surface>/ with sub-folders analysis/, generator/, outputs/, scores/, variations/, area/, resolution/, transfer/, guide_pictures/):
 A. DERIVATION CEILING: fit the small tone-curve + blur + strength that turns the REFERENCE colour into the REFERENCE height and normal; report how exact it is. (Tools: numpy/cv2.)
 B. ANALYSE the colour picture: layout, elements, palette, outlines, patches, grain; write analysis/analysis_findings.md in plain words with measured numbers.
 C. DESCRIBE: description.json in classes S (<=8 KB), M (<=64 KB), L (<=512 KB) where you can (a layered description is fine: layout -> per-element colour -> patches/wear -> outlines -> fine grain); audit each.
 D. GENERATE: the Blender generator (shader nodes, geometry nodes, curves, modifiers, physics - whatever fits; you may combine, and you should try at least one real-geometry route where it could help, comparing honestly) that reads a description and bakes colour.png, height.png (16-bit), normal.png (OpenGL), roughness.png, metallic.png (plus ao.png if you make one) for a 1254 px tile, seamless (prove it with the half-tile-shift test and a 2 x 2 look). Use lib/bake_harness.py / lib/contrib tools where they fit.
 E. COMPARE and ITERATE with both comparison tools per layer and class; record the rate-distortion table (what each layer adds, at what description size) in scores/ and show the difference sheets.
 F. SCALE: (1) VARIATION: write sample_description(seed) from distributions fitted to your reference's own elements and bake 8 new tiles through the same generator: each should score well on texture_compare (same kind of surface) and differ from each other and from the reference (pixel_compare must be poor against the reference; also measure how different the variants are from each other); contact sheet in variations/. (2) AREA: one bigger picture (2 x 2 tiles of NEW unique content, 2508 px, or tiles that differ from each other) with no visible repeats or seams: show it and measure the seams. (3) RESOLUTION: bake 512, 1254 and 2508 px of the same description; table of time and what changes.
 G. TRANSFER: take the recipe to ONE new surface you were not given (suggested: brick -> paving stones or cobbles; slate -> roof shingles or fish-scale tiles; wood -> parquet or deck boards; metal -> hull plates or corrugated sheet; mud -> snow, sand or wet clay; gravel -> pebbles or crushed rock; for the mud builder ALSO re-fit the golden-puddle mud reference/mud_golden (colour only) with the same generator): change only the description / few settings, record exactly what you changed and how long it took, show the pictures.
 H. DOCUMENT for the person (plain language): (1) "04 Recipe - <surface> - how it is made.md": the recipe step by step: for every Blender tool you used say in one plain sentence what it is, which settings matter, what changing each does to the picture (make 3-6 small parameter-sweep strips with lib/sweep_tools.py + make_strip.py in guide_pictures/ and embed/link them), the analysis method, the description format, the results tables (every measure, every layer and class), the dead ends; (2) "04 Lessons - <surface> - what carries over to other surfaces.md": a how-to-start-a-new-surface checklist in order, what each layer buys, what to measure first, traps, what is specific to this surface and what is general.
 Finish by writing recipes/<surface>/final_report.json (numbers per class: bytes, tier, SSIM, Delta E, edge skill, height/normal errors, texture_compare overall, seam, bake seconds) and answer with the structured result. Be honest about gaps. Soft limit: stop polishing when two further rounds each gain less than 0.01 SSIM or you have used about 350 tool calls; say what you would do next. Do not use the explainer-film plugin or the Astra add-on, do not touch git, do not edit lib/ or reference/ (copy and adapt into your own folder; say in your answer what you would change in lib/). Disk is tight (about 4 GB free for everyone): keep your folder under 400 MB and delete scratch pictures you no longer need.`

const RESULT = {
  type: 'object',
  properties: {
    surface: { type: 'string' },
    folder: { type: 'string' },
    derivation_ceiling: { type: 'string' },
    classes: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          class_name: { type: 'string' }, description_bytes: { type: 'number' }, tier: { type: 'string' }, colour_ssim: { type: 'number' },
          colour_mean_delta_e: { type: 'number' }, edge_skill: { type: 'number' }, height_mae_best_fit: { type: 'number' }, normal_mean_angle: { type: 'number' },
          texture_compare_overall: { type: 'number' },
        },
        required: ['class_name', 'description_bytes', 'tier'],
      },
    },
    what_each_layer_bought: { type: 'array', items: { type: 'string' } },
    variation_result: { type: 'string' },
    area_result: { type: 'string' },
    resolution_result: { type: 'string' },
    transfer_result: { type: 'string' },
    blender_tools_used: { type: 'array', items: { type: 'string' } },
    geometry_route_verdict: { type: 'string' },
    lessons_that_transfer: { type: 'array', items: { type: 'string' } },
    dead_ends: { type: 'array', items: { type: 'string' } },
    known_gaps: { type: 'array', items: { type: 'string' } },
    changes_wanted_in_lib: { type: 'array', items: { type: 'string' } },
    guide_files: { type: 'array', items: { type: 'string' } },
  },
  required: ['surface', 'folder', 'classes', 'variation_result', 'area_result', 'transfer_result', 'lessons_that_transfer', 'known_gaps', 'guide_files'],
}

const VERDICT = {
  type: 'object',
  properties: {
    surface: { type: 'string' },
    claims_hold: { type: 'boolean' },
    rescored: { type: 'array', items: { type: 'object', properties: { class_name: { type: 'string' }, tier: { type: 'string' }, colour_ssim: { type: 'number' }, colour_mean_delta_e: { type: 'number' }, texture_compare_overall: { type: 'number' } }, required: ['class_name', 'tier'] } },
    audit_ok: { type: 'boolean' },
    generator_reads_reference: { type: 'boolean' },
    discrepancies: { type: 'array', items: { type: 'string' } },
    variation_really_different: { type: 'string' },
    area_really_unique: { type: 'string' },
    guide_problems: { type: 'array', items: { type: 'string' } },
    overall: { type: 'string' },
  },
  required: ['surface', 'claims_hold', 'audit_ok', 'generator_reads_reference', 'discrepancies', 'overall'],
}

const SURFACES = [
  { key: 'brick', hint: 'Brick wall: running-bond courses, per-brick tone, mortar, soot streaks and chips, ~5 px dark outlines. Research best start: the home-made floor/fract layout with one random number per brick (research guide section on brick; lib/contrib/layout_tools.py for the geometry route).' },
  { key: 'slate', hint: 'Roof slate: rows of slates of varying width with a row slide, thick dark gaps and a shadow band (~12 px outline), grey-green moss streaks. Best research start: per-row slate counts with a sine wave varying widths (statistical score 0.50 so far).' },
  { key: 'wood', hint: 'Aged wood planks: horizontal boards of different heights, knots, splinter strips, cracks, rust-coloured blotches. Research best start: boards + long splinter strips from stretched Voronoi (W5).' },
  { key: 'metal', hint: 'Rusted riveted steel: plates with straps, K/N braces, rivet rows, rust mottling and scratches. Research best start: layout by numbers and signed distances (M4); geometry route with Curve Line + Instance on Points for rivets.' },
  { key: 'mud', hint: 'Mud: criss-crossing wheel ruts, blue-grey puddles, clusters of dark angular stones, crumbly ground. Research best start: a diagonal coordinate bent by noise where the bands are the ruts, polygon stones (D5); curve-based ruts in the geometry guide. ALSO re-fit reference/mud_golden (colour only; the warm sunset-puddle mud) with the same generator as your transfer test.' },
  { key: 'gravel', hint: 'Gravel: very dense angular blue-grey/black stones (5-60 px) in orange-brown earth, light and dark faces. Research best start: one random convex polygon per grid cell (G4) and the nodes-only relaxed Poisson scatter (2,150 stones in a Repeat zone); rigid-body drop only for a few big stones.' },
]

phase('Build')
const outcomes = await pipeline(
  SURFACES,
  s => agent(`${SHARED}\n\nYOUR SURFACE: ${s.key} (reference folder ${ROOT}/reference/${s.key}/). Your folder: ${ROOT}/recipes/${s.key}/. Hint: ${s.hint}\nYour guide files are numbered 04, e.g. "04 Recipe - ${s.key} - how it is made.md" saved inside your folder.\n\nWhen finished, answer with the structured result.`,
    { label: `build:${s.key}`, phase: 'Build', schema: RESULT }),
  (built, s) => agent(`You are an independent VERIFIER for the ${s.key} builder. Read ${ROOT}/PROCEDURAL_NOTES.md (skim; focus on the revised success definition, the rules and the tools). The builder worked in ${ROOT}/recipes/${s.key}/ and reported this result:\n${JSON.stringify(built || {}).slice(0, 6000)}\n\nYour job is to try to REFUTE it, with your own runs, not by reading their claims: (1) re-run lib/description_audit.py on every description file with the class limit they claim; (2) read the GENERATOR code and grep it and everything it imports for anything that reads the reference or any picture as an input to the generated textures (bpy.data.images.load, cv2.imread, PIL Image.open, .png/.jpg paths, np.load of pictures, embedded base64, arrays of thousands of numbers that are really per-dot data); say whether the generator is honest; (3) regenerate the colour/height/normal from the description in a fresh Blender process into a NEW folder (${ROOT}/recipes/${s.key}/verify/) and re-score with lib/pixel_compare.py and lib/texture_compare.py; compare with their numbers; (4) check the variations really come from the same generator with different sampled descriptions and look different (compute pixel differences between variants and between a variant and the reference), check the area picture is not a repeated tile (compare its quadrants), check the half-tile-shift test yourself on one bake, check the transfer claim by looking at the pictures; (5) read their two guides: are they plain language, accurate, with settings and sweep pictures that match what was run? List every problem. Use -t 2 and small sizes where you can. Do not change their files (write only into the verify/ folder). Answer with the structured verdict.`,
    { label: `verify:${s.key}`, phase: 'Verify', schema: VERDICT }).then(v => ({ surface: s.key, built, verdict: v })),
)
log('build and verify finished: ' + outcomes.filter(Boolean).length + ' of ' + SURFACES.length)
return outcomes
