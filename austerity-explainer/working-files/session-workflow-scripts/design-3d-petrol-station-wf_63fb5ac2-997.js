export const meta = {
  name: 'design-3d-petrol-station',
  description: 'Three competing designs for turning the painted petrol station and road into lit 3D objects, scored by two judges',
  phases: [
    { title: 'Design', detail: 'three approaches from different angles' },
    { title: 'Judge', detail: 'lighting-and-look judge, feasibility judge' },
  ],
}
const S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/sam3d'
const K = '/home/user/work/paper-pop-up-film-kit'
const CONTEXT = `The user's request: "the petrol station itself, the road it's on need to also be 3d objects. The rest of the cars and everything else remains part of the background. How would you do this because lighting is important here."
The project: narrated explainer films for phones (1080x1920, 30 fps), made of paintings brought to life in a three.js "cinema stage" drawn in headless Chromium with software graphics (SwiftShader) on a 4-processor cloud machine with NO graphics card (detailed pages draw at 3 to 16 seconds a frame; a 4.5-minute chapter films in ~6 hours). Paintings come from fal (Flux 3; the US$10 picture allowance has about US$3 left after all work so far, spending must be confirmed with the user). Blender 5.2.2 runs headless here (Python module at /home/user/work/blender-env/bin/python, and the official Blender MCP server), used to build models by script and bake soft shading; Blender's own renderer is far too slow to film with.
The camera rule from the user: still unless a move is essential, at most 3 moves per shot (zoom, pan, move up/down), so moves are short.
The painting: ${K}/assets/reliefs/inflation-chapter-2/409-bg-petrol-station-1973.jpg (1536x2736, a 1973 petrol station at night: a canopy with three warm ceiling lamps over a pump island, two canopy posts, a lit kiosk/shop with warm windows, a wet concrete forecourt with warm light pools and the red car's headlight beams, a road behind with queued cars, hedges, houses, a night sky) and its depth picture 409-bg-petrol-station-1973-depth.png. How the stage shows a painting today: "painted room with depth" = the painting pushed back by its depth picture (relief() in ${K}/paper-film/scenes/cinema-kit.js, lines ~123-205; lightRig() ~93-120); it tears on camera moves at near upright things (canopy posts, kiosk edges).
The previous test (log 22): ${K}/paper-film/scenes/sam-3d-petrol-station-test.js, snapshot "${S}/22 Snapshot - SAM 3D petrol station.jpg". SAM 3D (fal-ai/sam-3/3d-objects, 2 US cents) rebuilt the red car and three pumps; each model wears the painting projected from where it was painted (camera projection mapping) on surfaces the painting showed and SAM's own texture on hidden sides; a Flux 3 edit made a clean plate behind them; the ground under them was fitted from the depth around their bases. Worked from the painting's view and on a short push; still wrong: background tearing at canopy posts and kiosk, ghost edges where models and painting don't line up exactly, lifted rear wheels on moves, headlight pool broken.
Lighting facts that matter: everything in the painting has its light painted in (lamp pools, kiosk glow, headlight beams, wet reflections). Real 3D lights in the stage add shading and shadows on top. Painted light that stays put is fine while only the camera moves; it is wrong if objects move through it (a car driving under the canopy) or if a new object needs to be lit by it.
Look at the painting and the snapshot with the Read tool; read the code you need. Spend nothing, render nothing heavy (at most two quick stills if essential, from ${K} with node paper-film/tools/render-paper-film.mjs ... --stills), change no project files (scratch work only under ${S}/design/).`
const DESIGN = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    one_line: { type: 'string' },
    concrete_example: { type: 'string' },
    geometry: { type: 'string' },
    look_and_style: { type: 'string' },
    lighting: { type: 'string' },
    what_stays_painted: { type: 'string' },
    camera_moves_it_allows: { type: 'string' },
    steps: { type: 'array', items: { type: 'string' } },
    cost_usd: { type: 'string' },
    effort_hours: { type: 'string' },
    drawing_speed_per_frame: { type: 'string' },
    risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['name', 'one_line', 'concrete_example', 'geometry', 'look_and_style', 'lighting', 'what_stays_painted', 'camera_moves_it_allows', 'steps', 'cost_usd', 'effort_hours', 'drawing_speed_per_frame', 'risks'],
}
const ANGLES = [
  { key: 'matte-painter', brief: 'You are a film matte painter. Design the approach a 2.5D matte-painting team would use: camera projection of the painting onto simple proxy geometry (ground plane and kerb, canopy slab, posts as cylinders/boxes, kiosk as boxes, pump island), built by script and fitted to the painting and its depth; clean plates painted for what the camera newly sees behind posts and canopy; and how to handle light so the painted light is kept but 3D objects still get proper contact shadows, occlusion and light from the painted lamps (e.g. shadow-only passes, light-only multipliers, emissive lamp cards, matching real lights placed at the painted lamp positions).' },
  { key: 'modeller-lighter', brief: 'You are a 3D modeller and lighting artist. Design the approach of rebuilding the station and road properly in Blender by script (canopy with lamps, posts, kiosk with interior and windows, pump island, forecourt and road with kerbs and wet surface), lit to match the painting (lamp positions and colours estimated from the painting), with painterly textures (from the painting itself or generated), baked lighting where it saves drawing time, and real lights in the stage for anything that moves. Say how it would keep the painted look rather than looking like a clean 3D render.' },
  { key: 'ai-pipeline', brief: 'You are a pipeline engineer who uses AI 3D tools. Design the approach using generative tools available today: e.g. SAM 3D (fal) on the station parts, single-image-to-3D (Hunyuan3D, TRELLIS on fal), whole-scene world generators (World Labs Marble, Hunyuan World), depth-to-mesh with segmentation, or AI relighting of the painting into separate light layers (lamp light, kiosk light, headlights, ambient) so light can be recombined in 3D. Check current fal prices with WebSearch/WebFetch if you name a paid tool (load them via ToolSearch "select:WebFetch,WebSearch"). Be honest about what still breaks.' },
]
const JUDGE = {
  type: 'object',
  properties: {
    scores: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, score_out_of_10: { type: 'number' }, why: { type: 'string' } }, required: ['name', 'score_out_of_10', 'why'] } },
    best: { type: 'string' },
    best_ideas_to_combine: { type: 'array', items: { type: 'string' } },
    biggest_risk_of_best: { type: 'string' },
    first_small_test: { type: 'string' },
  },
  required: ['scores', 'best', 'best_ideas_to_combine', 'biggest_risk_of_best', 'first_small_test'],
}
phase('Design')
const designs = (await parallel(ANGLES.map((a) => () => agent(`${CONTEXT}\n\n${a.brief}\nWrite one complete, concrete design for THIS painting. Lighting must be the centre of it: name each light in the painting (where it is in the picture, its colour), what becomes a real 3D light, what stays painted, how shadows of the 3D car and pumps fall on the 3D forecourt, how the wet reflections are handled, and what happens to the light when the camera pushes in. Be specific and plain; give honest costs, effort and drawing speed on this CPU-only machine.`, { label: `design: ${a.key}`, phase: 'Design', schema: DESIGN, effort: 'medium' })))).filter(Boolean)
phase('Judge')
const listing = JSON.stringify(designs, null, 1)
const judges = (await parallel([
  () => agent(`${CONTEXT}\n\nYou are a film director with a cinematographer's eye for light. Score these designs for how good the petrol station shot would LOOK in the film: painted style kept, light that feels right (lamp pools, kiosk glow, headlights, wet ground), shadows and contact, and how well it survives short camera moves. Name the best, the ideas from the others worth grafting on, its biggest risk, and the first small test that would prove or kill it.\n\nDESIGNS:\n${listing}`, { label: 'judge: look and light', phase: 'Judge', schema: JUDGE, effort: 'medium' }),
  () => agent(`${CONTEXT}\n\nYou are a skeptical technical lead. Score these designs for whether they can actually be built and filmed HERE (CPU-only software rendering at 1080x1920, three.js stage, headless Blender, about US$3 of picture allowance left, smaller models must be able to repeat it via the plugin), how long they take, how they fail, and how reusable the method is for other paintings. Check claims against the code where you can (${K}/paper-film/scenes/cinema-kit.js, model-loader.js, the test scene). Name the best, the ideas to graft, its biggest risk, and the first small test.\n\nDESIGNS:\n${listing}`, { label: 'judge: feasibility', phase: 'Judge', schema: JUDGE, effort: 'medium' }),
])).filter(Boolean)
return { designs, judges }
