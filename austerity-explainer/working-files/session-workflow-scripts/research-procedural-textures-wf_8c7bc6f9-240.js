export const meta = {
  name: 'research-procedural-textures',
  description: 'Five helpers research and test how people make procedural textures in current Blender, and save plain-language guides',
  phases: [{ title: 'Research', detail: 'five topics in parallel; each claim tested in Blender where possible' }],
}

const ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'

const SHARED = `You are one of five research helpers for a texture job. FIRST read ${ROOT}/PROCEDURAL_NOTES.md completely, and look at the reference pictures in ${ROOT}/reference/ (at least colour.png of brick, slate, wood, metal, mud, gravel, and the matching normal.png and height.png of two of them) with the Read tool so you know what we are trying to make. Your job is RESEARCH THAT GETS TESTED: search the web for how people currently achieve your topic in Blender 4.x/5.x (prefer sources from 2024-2026, the official Blender manual, Blender developer posts, well-known tutorial authors, artist forums; note the date and URL of every source you actually used), search Blender's own bundled manual and Python reference through the Blender MCP tools (mcp__blender__search_manual_docs, mcp__blender__search_api_docs, mcp__blender__get_python_api_docs - load them with ToolSearch), and then TEST the important claims yourself in Blender 5.2.2 (command-line Blender or mcp__blender__execute_blender_code_for_cli with ${ROOT}/empty.blend; small renders; use the helpers in ${ROOT}/lib). Web claims are often wrong or out of date (for example one shop page claims procedural nodes wrap seamlessly at integer UV values, which is false for Blender noise); anything you did not test must be labelled 'not tested'. Write your findings as one plain-language markdown guide (see the notes: plain words, one-sentence meaning first, concrete example before the general rule, say what was tested and not tested) saved in ${ROOT}/research/ with the file name given below, plus any experiment files in ${ROOT}/research/experiments_<your topic>/. Put a 'Sources' list (title, URL, date, and one line on what it gave you) at the end of the guide and a 'Tested here' section with what you ran and what happened (failures too). Keep the guide useful: concrete node chains, exact setting names and values, what each setting does to the picture (with small before/after experiment pictures where it helps), pitfalls, and a short 'recipe card' list at the end.`

const RESULT = {
  type: 'object',
  properties: {
    guide_file: { type: 'string' },
    key_findings: { type: 'array', items: { type: 'string' } },
    verified_by_test: { type: 'array', items: { type: 'string' } },
    wrong_or_outdated_claims_found: { type: 'array', items: { type: 'string' } },
    recommended_for_the_builders: { type: 'array', items: { type: 'string' } },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['guide_file', 'key_findings', 'recommended_for_the_builders'],
}

const TOPICS = [
  {
    key: 'toolbox',
    file: '02 Research - the shader node toolbox.md',
    brief: `TOPIC: the procedural shader-node toolbox of Blender 5.2. Enumerate by introspection (Python in Blender: every ShaderNode type, its settings and its input/output sockets; also the texture/converter nodes available in the Geometry Nodes editor) and group them by what they are FOR: pattern makers (Brick, Checker, Gradient, Magic, Noise incl. its fractal types and 1D-4D, Voronoi incl. features/distance metrics/4D, Wave, White Noise, Gabor, anything new), shapers (Color Ramp and its interpolation modes, Map Range, Math, Float Curve, RGB Curves, Clamp, Mix and its blend modes, Invert, Hue/Saturation, Bright/Contrast, Gamma, Vector Math, Mapping, Vector Rotate, Separate/Combine), surface-effect nodes (Bump, Displacement, Vector Displacement, Normal Map, Bevel, Ambient Occlusion, Wireframe, Geometry/pointiness/curvature-like inputs, Layer Weight, Fresnel), and shader nodes (Principled BSDF inputs that matter for these materials: base colour, roughness, metallic, coat, specular, subsurface, emission; and how puddles/wetness are usually done). For EACH node: one plain sentence on what it does, its key settings and what turning each up or down does, and which of our six surfaces (brick, slate, wood, rusted metal, mud with puddles, gravel) it helps with and how. Mark what changed from Blender 3.x to 5.x (e.g. Musgrave merged into Noise). Test several nodes by rendering small pictures with ${ROOT}/lib/sweep_tools.py. In your final answer include a list of the nodes that deserve their own parameter-sweep picture in the guides.`,
  },
  {
    key: 'seamless_and_baking',
    file: '02 Research - seamless tiles and baking maps.md',
    brief: `TOPIC: making a procedural material into SEAMLESS tileable texture pictures, and baking the maps (colour, height/displacement, normal, roughness, metallic, ambient occlusion). Cover and TEST: (1) how to make each kind of pattern tile exactly (integer scales on the Brick Texture, the 4D 'donut' trick for Noise and Voronoi already in ${ROOT}/lib/recipe_tools.py, how Wave/Gradient/Magic/Gabor behave at tile edges, offset-and-blend repair, mirror tiling and why people avoid it); measure seams with the seam measure in ${ROOT}/lib/texture_compare.py. (2) baking routes: Cycles Bake (Diffuse colour only, Normal, Emit, AO, Roughness) vs 'photograph a flat square with an emission shader' (what ${ROOT}/lib/bake_harness.py does) vs Geometry Nodes Bake node vs compositor; pitfalls (colour space, 8 vs 16 bit, anti-aliasing, margin/bleed, UV scaling, tangent space, bake from high to low poly). (3) height -> normal conversion: Bump node vs Sobel in numpy vs compositor; OpenGL vs DirectX green channel and how to tell which a map is; displacement vs bump vs 'both' in Cycles (material displacement settings, adaptive subdivision in 5.2, why 8-bit height bands, dicing); what 'midlevel' and 'scale' mean. (4) how real studios and Blender artists export PBR sets (naming, channel packing, ORM, resolution, bit depth), and which add-ons people use (SimpleBake, The Bakery, Node Wrangler, etc.) - say what they do, not whether to buy them. (5) a checklist for 'is my texture really seamless and correct' that a non-programmer can follow, backed by a small test script saved in your experiments folder.`,
  },
  {
    key: 'geometry_curves_modifiers',
    file: '02 Research - geometry nodes, curves, modifiers and physics for surface detail.md',
    brief: `TOPIC: building surface detail from REAL GEOMETRY and then photographing it from straight above to get height, colour and normal maps (so the maps come from geometry, not just from shader noise). Cover and TEST in Blender 5.2: Geometry Nodes recipes for tile layouts (brick courses with random size/offset/gaps, roof slates with overlap, wood planks with gaps, riveted metal plates with bolts, stone/gravel scatter with Distribute Points on Faces + Instance on Points + Relax/Poisson spacing + random rotation/scale, realize instances, capture/store attributes for per-piece colour and height), curves for cracks, mortar lines, wood grain, ruts and wheel tracks (Curve to Mesh, Resample, Set Position with noise, curve-based displacement), modifiers that help (Displace with textures, Subdivision, Bevel, Boolean, Remesh, Weld, Solidify, Array, Wave, Cast, Simple Deform), physics to make piles look natural (Rigid Body drop-and-settle for gravel and rubble; mention particles, cloth, dynamic paint, fluids only if useful and tested), Blender 5.x's Bake node and Repeat/Simulation zones for iterative relaxation, and 'draw height with an orthographic camera and an emission Z-depth shader'. Also how to make the geometry WRAP so its tile is seamless (copies across the edges). Save at least four small working example .py recipes (brick layout, slate layout, gravel scatter + rigid-body settle, curve-based ruts) in your experiments folder, each producing a height picture and a colour picture of a 1 x 1 tile through ${ROOT}/lib/bake_harness.py building blocks, and say how long each took. Report honestly what is slow or fragile here (CPU only).`,
  },
  {
    key: 'per_material_recipes',
    file: '02 Research - how people make each surface.md',
    brief: `TOPIC: surface by surface, how Blender artists currently build procedural BRICK WALL, ROOF SLATE tiles, AGED WOOD planks, RUSTED RIVETED METAL, WET MUD with ruts, stones and puddles, and GRAVEL / ballast / rubble, in shader nodes and with geometry where people do. For each of the six: (a) 3-5 distinct approaches found, with sources, and the node chain each one uses (node names, key settings and numbers, how they are connected), (b) which pattern/mask layers make it look right (large-scale variation, per-piece colour variation, edge wear, grime in crevices, moss/stains, scratches, gloss differences, puddle masks, depth cues), (c) typical pitfalls and tricks, (d) how to make it look HAND-PAINTED / stylised instead of photo-real (posterise, constant colour ramps, outlines, flat patches) when the sources mention it, (e) an honest assessment of which approach is closest to the person's reference picture of that surface (look at the reference in ${ROOT}/reference/<surface>/colour.png) and why. Test at least the most promising one chain per surface by actually building it in Blender at 512 px and comparing it with the reference by eye (save the node chain as a small recipe file and its picture in your experiments folder). Finish with a table: surface x approach x expected closeness x difficulty.`,
  },
  {
    key: 'painterly_look',
    file: '02 Research - getting a hand-painted stylised look.md',
    brief: `TOPIC: the person's reference textures look HAND-PAINTED and stylised (flat painted colour patches, hard-edged shapes, dark outlines, chunky features, limited palettes, subtle brush streaks) rather than photo-real. Research and TEST how to get that look procedurally in Blender 5.2: constant-interpolation Color Ramps and posterising (Math 'Floor'/'Snap', Map Range with steps), Voronoi cells as paint patches, domain warping (Noise 'Distortion', warping a coordinate by noise before another noise), streaky / anisotropic noise for brush strokes (scaled vector noise, Wave, Gabor), edge darkening and outlines (Bevel node, Ambient Occlusion node, height-gradient edge detection built from offsetting the same pattern, Geometry pointiness), colour palette control (colour ramps from an extracted palette, Hue/Saturation variation per cell), the compositor's Kuwahara filter (classic and anisotropic) and other compositor stylising nodes (Pixelate, Posterize, Filter, Dilate/Erode, Blur) applied to baked maps, and ways to keep stylising consistent between colour, height and normal. Also analyse the six references yourself by numbers (run python on the reference pictures: dominant palette by k-means in Lab, how many distinct flat levels, outline darkness and width in pixels, typical patch size) and give the builders a measured 'look specification' per surface (palette, outline width, patch scale, contrast) they can aim at. Save sweep strips showing what each stylising control does.`,
  },
]

phase('Research')
const results = await parallel(TOPICS.map(t => () =>
  agent(`${SHARED}\n\nYOUR GUIDE FILE (save exactly here): ${ROOT}/research/${t.file}\n\n${t.brief}\n\nWhen finished, answer with the structured result.`, {
    label: `research:${t.key}`, phase: 'Research', schema: RESULT,
  })
))
log(`research done: ${results.filter(Boolean).length} of ${TOPICS.length}`)
return TOPICS.map((t, i) => ({ topic: t.key, result: results[i] }))
