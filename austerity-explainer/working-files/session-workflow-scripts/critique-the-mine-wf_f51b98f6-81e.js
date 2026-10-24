export const meta = {
  name: 'critique-the-mine',
  description: 'Three critics inspect the assembled mine scene (look, materials, clashes) and each finding is independently re-checked',
  phases: [{ title: 'Critique', detail: 'three lenses, read-only' }, { title: 'Verify', detail: 'each finding re-checked with fresh renders' }],
}

const ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
const BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'

const CONTEXT = `CONTEXT. A coal-mine scene (engine house, steel headframe with two big wheels, tall brick chimney with smoke, railway with carts and coal, muddy yard, village, hills, dusk sky) was built in Blender 5.2 from a person's uploaded textures (brick, slate, wood, rusted metal, mud, gravel colour pictures + normal + displacement maps, prepared in ${ROOT}/textures_ready) by six helpers, then assembled. The target look is the painted dusk pit-village in ${ROOT}/pictures/reference_scene_screenshot.jpg (tall portrait frame). Design pictures of the props are in ${ROOT}/pictures/ (pithead_building_with_headframe.png, headframe_tower.png, chimney_with_smoke.png, mine_cart_with_coal.png, curved_rail_track.png). The current candidate photo (720x1280, quick render) is ${ROOT}/out/candidate_01_quick.png. Read ${ROOT}/lib/mine_common.py for the shared toolbox and LAYOUT (metres; +X right, +Y away from camera, +Z up). The parts are modules/*.py (ground_and_yard, engine_house, headframe, chimney_and_smoke, track_and_carts, village_and_sky) and the assembler is assemble_mine.py. YOU ARE READ-ONLY: do not edit any file except your own outputs named out/critic_<yourlens>_*. To take your own look from any camera run:
  ${BLENDER} -b --disable-autoexec -t 2 --python ${ROOT}/assemble_mine.py -- ${ROOT}/out/critic_<yourlens>_<name> --quick --camera X,Y,Z,TX,TY,TZ --lens L --width 720 --samples 24 [--only ground_and_yard,engine_house,...] 
(camera = location then look-at target, comma-separated, no spaces; a render takes about 1-3 minutes; keep to a few dozen renders at most; wide/overview shots can use --width 900 --height 900 with --lens 20). View images with the Read tool. Do not use the explainer-film plugin or the Astra add-on. Known state: the engine house has a floor added by the assembler; the track curve was bent toward the camera; the smoke path and heaps were already moved once; a warm front fill light was added. Be concrete, specific and honest; prefer a few real, high-impact findings over many nitpicks; never report something you have not actually seen in an image you looked at. For each finding give where it is (image + approximate position, and the 3D place if known), why it matters, and a concrete proposed fix naming the file and the parameter/function to change.`

const FINDINGS = {
  type: 'object',
  properties: {
    overall: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          title: { type: 'string' },
          evidence: { type: 'string' },
          proposed_fix: { type: 'string' },
          how_to_verify: { type: 'string' },
        },
        required: ['id', 'severity', 'title', 'evidence', 'proposed_fix', 'how_to_verify'],
      },
    },
  },
  required: ['overall', 'findings'],
}

const VERDICT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['confirmed', 'partly', 'refuted'] },
    what_i_saw: { type: 'string' },
    refined_fix: { type: 'string' },
  },
  required: ['verdict', 'what_i_saw', 'refined_fix'],
}

const LENSES = [
  {
    key: 'look',
    prompt: `YOUR LENS: LOOK AND MOOD versus the reference. Compare the candidate photo with the reference screenshot and the design pictures: framing and proportions (tower, chimney, engine house, village, hills), what the reference has that ours lacks, value structure and colour (too dark / too blue / flat?), light direction and warmth (windows, lamp, horizon glow, rim light), the smoke's shape, size and colour, the sky, the foreground (ruts, puddles and reflections, clutter, carts and rails), depth and atmosphere, anything that looks obviously CG or unfinished. Think like a painter's art director: what 5-8 changes would most improve how close it feels to the reference while staying a believable 3D render? Include lighting/exposure/camera suggestions with numbers.`,
  },
  {
    key: 'materials',
    prompt: `YOUR LENS: MATERIALS AND MAP FIDELITY. The person's brick, slate, wood, rusted-metal, mud and gravel pictures with their normal and displacement maps must read clearly and correctly. Take close and medium views (and the candidate) of: engine-house brick walls and slate roof, chimney shaft, headframe steel, wood planks/sleepers/shed, track ballast, the mud ground and puddles, carts. Look for: texture stretching or smearing, wrong tile scale (bricks/slates too big or small), visible tiling repetition, seams where surfaces meet, mirrored or wrongly oriented textures, displacement artifacts (spikes, cracks or gaps at displaced corners/edges, needle-like relief, noise at distance), missing or flat-looking relief where relief was intended, shine/roughness that looks wrong (everything wet? mirror puddles absent? metal too dark), tint inconsistencies between parts, plain-colour parts that clash with the textured ones. Check that the maps are actually used (relief catches light).`,
  },
  {
    key: 'clashes',
    prompt: `YOUR LENS: ASSEMBLY AND GEOMETRY CLASHES. Six helpers built parts separately; check how they fit. Use overview and deliberately awkward cameras (high overview, close at the doorway, at the headframe footings, at rope ends, at the planks/crate by the door, along the rails, behind the buildings, at the edges of the terrain, the horizon and hills, the sky seam, under the roof eaves). Look for: parts interpenetrating or overlapping (headframe footings vs crate/plank piles/rails; rope ends vs rails; chimney flue stub vs wall; carts vs rails/footings; clutter on the track), floating or sunk objects, gaps or black voids (doorway, interior, floor, terrain edges, village hillside seam, hills not covering the horizon, the terrain rim), faces pointing the wrong way, z-fighting flicker, things that are far too big/small for each other, stray objects, anything visible in the candidate frame or in plausible nearby camera positions that looks broken.`,
  },
]

phase('Critique')
const reviews = await pipeline(
  LENSES,
  lens => agent(`${CONTEXT}\n\n${lens.prompt}\n\nReturn at most 8 findings, highest impact first, as the structured result.`, { label: `critic:${lens.key}`, phase: 'Critique', schema: FINDINGS }),
  (review, lens) => {
    const top = (review && review.findings ? review.findings : []).filter(f => f.severity !== 'low').slice(0, 6)
    return parallel(top.map(f => () =>
      agent(`${CONTEXT}\n\nYOU ARE AN INDEPENDENT VERIFIER. Another critic (lens: ${lens.key}) reported this finding. Try to REFUTE it: take your own renders (different cameras than they probably used) and look at the evidence yourself. Default to 'refuted' if you cannot see the problem; say 'partly' if it is real but smaller, different, or the proposed fix is wrong, and give a better fix.\n\nFINDING ${f.id} [${f.severity}]: ${f.title}\nEvidence: ${f.evidence}\nProposed fix: ${f.proposed_fix}\nHow to verify: ${f.how_to_verify}`,
        { label: `verify:${lens.key}:${f.id}`, phase: 'Verify', schema: VERDICT }).then(v => ({ ...f, lens: lens.key, verdict: v }))))
  },
)
const out = reviews.map((r, i) => ({ lens: LENSES[i].key, items: (r || []).filter(Boolean) }))
log(out.map(o => `${o.lens}: ${o.items.length} findings checked`).join('; '))
return out
