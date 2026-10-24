export const meta = {
  name: 'blender-mcp-models',
  description: 'Use the official Blender MCP server (its guidance, bundled manual/API search, scene inspection and thumbnails) to make the film models more detailed: learn, then improve factory, town, desk and props, then judge before/after',
  phases: [
    { title: 'Learn', detail: 'read the Blender MCP guidance and search its bundled manual and API for detail techniques' },
    { title: 'Improve', detail: 'one helper per model: inspect via the MCP, improve the build script, rebuild, preview' },
    { title: 'Judge', detail: 'compare before and after in Blender thumbnails and in the film stage' },
  ],
}

const KIT = '/home/user/work/paper-pop-up-film-kit'
const BL = `${KIT}/paper-film/blender`
const MODELS = `${KIT}/assets/models/inflation-chapter-2`
const BEFORE = '/home/user/work/chapter-2/feedback-20/models-before-mcp'
const NOTES = '/home/user/work/chapter-2/reference/22 Blender MCP notes - detailed models.md'
const OUT = '/home/user/work/chapter-2/stills/mcp'

const MCP_HOWTO = (port) => `HOW TO USE THE OFFICIAL BLENDER MCP SERVER (Blender Lab, v1.0.2) HERE
- Blender 5.2.2 is at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender with the MCP add-on installed. Start your OWN headless Blender on your own port (run it in the background and keep its process id; stop it at the end with kill PID - never pkill -f, which can kill your own shell):
    /home/user/work/blender-app/blender-5.2.2-linux-x64/blender --background --online-mode --command blender_mcp --host 127.0.0.1 --port ${port} > /tmp/blender-${port}.log 2>&1 &
- Call the server's tools through the command-line client (the server is the real 'blender-mcp' package; the client just speaks MCP to it):
    export BLENDER_MCP_SERVER=/home/user/work/blender-mcp/mcp-env/bin/blender-mcp BLENDER_PATH=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender BLENDER_MCP_HOST=127.0.0.1 BLENDER_MCP_PORT=${port}
    C="/home/user/work/blender-mcp/mcp-env/bin/python ${BL}/blender_mcp_call.py"
    $C guide                                  (the server's own instructions to models - read them)
    $C tools                                  (the tool list)
    $C search_manual_docs '{"query": "..."}'  /  $C search_api_docs '{"query": "..."}'  /  $C get_python_api_docs '{"identifier": "bpy.types.BevelModifier"}'
    $C get_objects_summary  /  $C get_object_detail_summary '{"name": "walls"}'
    $C run-file SCRIPT.py                     (execute_blender_code with a file; set a variable named result to return data)
    $C render_thumbnail_to_path '{"output_path": "name.png"}'   (writes into bpy.app.tempdir/blender_mcp/; the reply gives the real path; 320 px)
- Lessons already learned: the server's sandbox refuses bpy.ops.wm.read_factory_settings (use bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)); set scene.render.engine = 'CYCLES' and scene.cycles.device = 'CPU' BEFORE any render (EEVEE needs a GPU here and crashes Blender); set scene.render.resolution_x = 1080, resolution_y = 1920 for the film's tall frame; import a model with bpy.ops.import_scene.gltf(filepath=...); add a camera, a sun or area light and a dark world yourself; Blender's -y is the model's front (three.js +z). If Blender crashes, start it again.`

phase('Learn')
const notes = await agent(`You are preparing modelling guidance for helpers who will improve 3D models for a vertical explainer film (1080x1920, phone). The models are built by Python scripts with Blender's bpy and exported as .glb into a real-time three.js stage (software rendering, warm lamp light from the front left, depth of field, film grain), as miniature model sets: two 1915 brick munitions works, a model industrial town around them, a reviewer's desk, and loose props. The viewer asked for "significantly higher quality" models and said: "Blender has an official MCP to use for this ... It'll teach you how to use it to get good detailed results".

${MCP_HOWTO(9880)}

Do this:
1. Start your Blender, run $C guide and read the server's whole instructions. Note every rule that matters for building models by script.
2. Use the server's search tools (search_manual_docs, search_api_docs, get_python_api_docs) to research, with citations to the manual/API paths it returns, the techniques that make small models look richly detailed and well finished in a real-time glTF viewer, for example: bevel modifier settings (segments, harden normals, limit method, clamp), weighted normal / auto smooth and custom normals, sharp edges and shading, solidify, array and curve modifiers (railings, gutters, chains of bricks), boolean best practice, geometry nodes for repeated detail (instances of bricks, slates, rivets, setts) and whether they export to glTF (realize instances), displacement versus normal maps, texel density and UV scale, baking (ambient occlusion, normal maps from high to low detail, curvature/edge wear) in Cycles on CPU, glTF exporter options that affect quality (normals, tangents, vertex colours, materials, image formats, apply modifiers, instancing), and anything else the manual shows that fits.
3. Look at the current models and how they look in the film: the scripts ${BL}/build_factory.py, build_town.py, build_desk.py, build_props.py and the shared ${BL}/model_kit.py and textures.py; the film stills /home/user/work/chapter-2/stills/r20-p3-f/sheet.jpg, /home/user/work/chapter-2/stills/r20-p3-g/still-43.00.jpg, /home/user/work/chapter-2/stills/r20-p8-b/sheet.jpg (Read them). Load one .glb from ${MODELS} into your Blender via the MCP and render a thumbnail to see it.
4. Write the guidance to ${NOTES}: (a) the Blender MCP server's rules and how to use it here; (b) the techniques, each with the exact bpy settings or code snippet and its source path; (c) concrete, prioritised improvements for each of the four models (what a viewer would notice first on a phone), within budgets: each factory up to 40,000 triangles, the town up to 70,000, the desk up to 20,000, props up to 6,000; textures at most 1024 px each; (d) traps.
Stop your Blender (kill PID) at the end. Do not edit the build scripts. Return a 10-line summary of the guidance.`, { label: 'learn from the Blender MCP', phase: 'Learn', effort: 'medium' })

const KEEP = `KEEP EXACTLY (pages depend on these): the output file names; every marker (empty) name and position; material names ending in -glow (the page turns them up and down) and their meaning; the model's footprint and origin. The factory: shed 3.2 wide x 2.0 deep x 1.3 high, origin at the middle of the ground under it, front at Blender y = -1.0, markers chimney_top, door, yard, door_lamp, office_door. Nothing new may stand on the forecourt in front of the facade (Blender y < -1.0) except within 0.25 of the side walls' line: the film places shells, coins, price boards on posts, cut-out workers and a pop-up house there. The town: markers smoke-0..smoke-5 and lamp-0..lamp-5; the factories stand at three.js (-1.4, 2.2) and (1.6, -4.2) with their forecourts about 5.8 x 5.4 around them, and a street across at three.js z -0.25: keep those areas flat and clear; ground top at y -0.02. The desk: origin = the middle of the blotter, on its surface; the printed report (about 1.3 wide, 1.65 deep) lies centred there: keep the blotter's middle 1.5 x 1.9 clear and flat; markers desk_lamp, ink_pad. The props: the groups 'barrels', 'crates', 'lamp-post', 'cart' and the marker lamp-post-light, each group built around its own origin.`

const MODELS_TO_IMPROVE = [
  { key: 'factory', script: 'build_factory.py', port: 9881, files: 'factory-a.glb (--brick red --office left --seed 1) and factory-b.glb (--brick brown --office right --seed 2)', budget: '40,000 triangles each', look: 'pages 3 and 8: /home/user/work/chapter-2/stills/r20-p3-f/sheet.jpg, /home/user/work/chapter-2/stills/r20-p3-g/still-43.00.jpg, /home/user/work/chapter-2/stills/r20-p8-b/sheet.jpg', stage: 'cam=3.6,1.5,7.5&look=0,1.0,0&fov=42 and cam=-3.0,1.3,6.5&look=0,1.1,0&fov=42' },
  { key: 'town', script: 'build_town.py', port: 9882, files: 'town.glb', budget: '70,000 triangles', look: 'pages 3 and 8 backgrounds: /home/user/work/chapter-2/stills/r20-p3-g/still-43.00.jpg, /home/user/work/chapter-2/stills/r20-p3-f/sheet.jpg', stage: 'cam=-2.6,1.25,12.6&look=0.4,1.05,-1.8&fov=44 and cam=4.8,1.3,2.8&look=2.0,0.95,-3.2&fov=41 (ground=0 so the town ground shows)' },
  { key: 'desk', script: 'build_desk.py', port: 9883, files: 'desk.glb', budget: '20,000 triangles', look: 'page 8 desk: /home/user/work/chapter-2/stills/r20-p8-b/sheet.jpg (the last two frames) and /home/user/work/chapter-2/stills/r20-desk-a/sheet.jpg', stage: 'cam=0,4.9,3.4&look=0,0,-0.15&fov=44&ground=0 (the film camera) and cam=0,5.5,5&look=0,0,0&fov=40&ground=0' },
  { key: 'props', script: 'build_props.py', port: 9884, files: 'props.glb', budget: '6,000 triangles', look: 'page 3 near corners: /home/user/work/chapter-2/stills/r20-p3-g/still-43.00.jpg (cart, barrels bottom) and /home/user/work/chapter-2/stills/r20-p3-f/still-74.00.jpg', stage: 'cam=0.9,0.7,1.6&look=0.1,0.25,0&fov=42&sky=none (all four groups overlap at the origin there; inspect them one by one in Blender instead)' },
]

const REPORT = { type: 'object', properties: {
  model: { type: 'string' },
  mcp_use: { type: 'array', items: { type: 'string' }, description: 'each Blender MCP tool call that informed a change, and what it showed' },
  changes: { type: 'array', items: { type: 'string' } },
  triangles_before: { type: 'string' }, triangles_after: { type: 'string' },
  before_after: { type: 'array', items: { type: 'string' }, description: 'paths of before and after pictures (MCP thumbnails and stage stills)' },
  kept: { type: 'string', description: 'how you checked that names, markers, footprint and clear zones are unchanged' },
  unsure: { type: 'array', items: { type: 'string' } },
}, required: ['model', 'mcp_use', 'changes', 'triangles_before', 'triangles_after', 'before_after', 'kept', 'unsure'] }

phase('Improve')
const reports = await parallel(MODELS_TO_IMPROVE.map((m) => () => agent(`You are improving one 3D model of a vertical explainer film so it looks significantly more detailed and finished on a phone, using the official Blender MCP server. Model: ${m.key}, built by ${BL}/${m.script} into ${MODELS}/${m.files}. Budget: ${m.budget}, textures at most 1024 px.

First read the guidance written from the Blender MCP's own instructions and its bundled manual: ${NOTES}. Also read ${m.script}, ${BL}/model_kit.py and ${BL}/textures.py.

${MCP_HOWTO(m.port)}

How the model is used in the film (Read these pictures): ${m.look}.

Work like this:
1. Before: load the current .glb into your Blender via the MCP (run-file with an import script), inspect it (get_objects_summary, get_object_detail_summary on the main parts), and render MCP thumbnails from two or three film-like angles; also make a stage still of it (true film look):
   cd ${KIT} && PAPER_FILM_QUERY="model=/assets/models/inflation-chapter-2/FILE.glb&${m.stage.split(' and ')[0]}" timeout 600 node paper-film/tools/render-paper-film.mjs model-preview ${OUT}/${m.key}-before --stills 1
   Copy MCP thumbnails out of Blender's temp folder into ${OUT}/${m.key}-before/.
2. Decide the most visible improvements (what a viewer notices first on a phone; follow the guidance's list for this model), and implement them in ${m.script} only. You may add helper functions inside your own script; do NOT edit model_kit.py or textures.py (other helpers use them at the same time) - if you need a shared change, write the helper into your script and report it.
3. Build to a candidate file whose name ends in .glb (Blender adds .glb to any other name), e.g. ${MODELS}/${m.key}-candidate.glb (for the factory, build both variants as candidates), with the Blender Python module: /home/user/work/blender-env/bin/python ${m.script} OUT.glb [options]. Check triangles (printed) against the budget.
4. After: load the candidate through the MCP, inspect and render the same thumbnails; make the same stage still with the candidate file (${OUT}/${m.key}-after...). Compare honestly. Iterate (two or three rounds at most; the machine is shared, so one render at a time).
5. ${KEEP}
   Verify markers and material names in the candidate through the MCP (get_objects_summary / a run-file listing empties and materials) against the old file.
6. When the candidate is clearly better and keeps everything, copy it over the real file(s) (${MODELS}/${m.files.split(' ')[0]}${m.key === 'factory' ? ' and factory-b.glb' : ''}); remove candidate files. If it is not clearly better, leave the real files alone and say so.
Stop your Blender (kill PID). Do not edit page files or anything outside ${BL}/${m.script}, ${MODELS} and ${OUT}. Spend no money. Report as asked.`, { label: `improve ${m.key}`, phase: 'Improve', schema: REPORT, effort: 'medium' })))
const done = reports.filter(Boolean)

phase('Judge')
const verdict = await agent(`You are judging whether helpers made the film's 3D models better, as a demanding film director looking at a phone screen. Old models and scripts: ${BEFORE}. New: ${MODELS} and ${BL}. The helpers' reports are below, with before/after pictures; Read those pictures. Then check them in the film itself (one render at a time):
  cd ${KIT} && PAPER_FILM_PAGES=3 timeout 900 node paper-film/tools/render-paper-film.mjs cinema-test-pages ${OUT}/judge-p3 --stills 43.0 50.9 62 74.0
  cd ${KIT} && PAPER_FILM_PAGES=8 timeout 900 node paper-film/tools/render-paper-film.mjs cinema-test-pages ${OUT}/judge-p8 --stills 181.5 189.0 202.0 206.2
and compare with the stills from before (/home/user/work/chapter-2/stills/r20-p3-f, r20-p3-g, r20-p8-b). For each model: better, same, or worse, with the specific evidence; any regression (something moved, clipping with the film's shells, coins, boards, cut-outs, the pop-up house or the report; missing lamps or smoke; much darker or brighter; broken shading; slower drawing). For a model that is worse, name it and say exactly what to restore (the old .glb is in ${BEFORE}). Do not edit files.
Reports:
${JSON.stringify(done, null, 1)}`, { label: 'judge before and after', phase: 'Judge', effort: 'medium' })

return { notes, reports: done, verdict }
