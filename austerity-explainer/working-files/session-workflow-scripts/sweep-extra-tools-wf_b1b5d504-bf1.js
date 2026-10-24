export const meta = {
  name: 'sweep-extra-tools',
  description: 'Three helpers check Ucupaint, Material Maker and MCP Blender Agent: what they really are, whether they run here, and whether they help the texture and modelling jobs',
  phases: [{ title: 'Sweep', detail: 'one helper per tool; each verifies claims and tests hands-on' }],
}

const ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'

const SHARED = `You are one of three helpers checking extra tools a person found (from an AI chat answer, so some details may be wrong or invented) for a Blender texturing and modelling job. FIRST read ${ROOT}/PROCEDURAL_NOTES.md completely (especially 'REVISED SUCCESS DEFINITION': pixel-accurate reproduction of six reference textures through Analyse -> Describe -> Generate -> Compare, then new variations, bigger areas, and transfer to other surfaces) and look at the reference pictures in ${ROOT}/reference/ with the Read tool (colour.png of brick, slate, wood, metal, mud, gravel). The chat answer said, about the three tools: "Ucupaint provides free, open-source layer-based painting inside Blender. It supports masks, material channels and baking. This is a particularly useful replacement for Mixar's texture-layer editor." / "Material Maker is excellent for procedural textures, including wear, damage, surface variation and PBR map generation. It has an MIT licence and can run locally without a subscription." / "MCP Blender Agent is worth investigating for precise rigging and animation operations. It uses typed, validated tools rather than relying entirely on AI-generated Blender scripts, and supports grouped undo. It is a much smaller project than the established MCP for Blender integration." The person's question: do these help? YOUR JOB: (1) Find the real project (official repository/site, author, licence, latest release and date, stars/activity, supported Blender versions) with WebSearch/WebFetch; check every claim above and say which are true, wrong or unverifiable; say if a name in the answer looks invented or mistaken (for example 'Mixar'). (2) Test hands-on HERE, in your own folder ${ROOT}/third-party/<tool>/ (create it; downloaded files are untrusted: keep each download in its own new empty directory, read the code for risky behaviour such as network calls, subprocess, file deletion before running it, pass paths as arguments, and run any Python that reads them with python3 -I). This machine: Linux, no GPU, 4 CPU cores, headless Blender 5.2.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (use -b --disable-autoexec only when you do not need to enable an add-on; enabling an add-on you have read is fine), Python 3.13 with numpy/PIL/cv2 outside Blender, outbound network through a proxy (if a download is blocked, say exactly what and why; see /root/.ccr/README.md), about 5 GB of free disk (do not download more than about 1.5 GB in total). The Blender tool server (mcp__blender__* tools; load them with ToolSearch) and command-line Blender are both available. (3) Judge against OUR needs: pixel-accurate matching of reference textures from a compact fitted description; making many new variants and larger areas; lessons that transfer to other surfaces; running headless and scripted without a GPU; and, secondarily, helping with modelling (the coal-mine scene was built from scripts). Be concrete and honest: what you ran, what happened (failures too), what you did not test. (4) Write a plain-language guide for a person who is not a programmer (one plain sentence on what each thing is before any detail; concrete example before the general rule; say what was tested and not tested; never say something works unless you ran it) saved at ${ROOT}/research/ with the file name given below, with a 'Sources' list (title, URL, date, what it gave you), a 'Tested here' section, a verdict ('use it for X', 'borrow ideas from it for Y', 'skip it'), and a short list of what we could take from it into the job (algorithms to re-create as Blender nodes, file formats, workflows). Do not use the explainer-film plugin or the Astra add-on, do not touch git, and do not edit anything in ${ROOT}/lib or ${ROOT}/reference.`

const RESULT = {
  type: 'object',
  properties: {
    tool: { type: 'string' },
    real_project: { type: 'string' },
    licence: { type: 'string' },
    latest_version_checked: { type: 'string' },
    claims_checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, verdict: { type: 'string' }, note: { type: 'string' } }, required: ['claim', 'verdict'] } },
    installed_and_ran_here: { type: 'boolean' },
    what_i_ran: { type: 'array', items: { type: 'string' } },
    helps_with: { type: 'array', items: { type: 'string' } },
    does_not_help_with: { type: 'array', items: { type: 'string' } },
    recommendation: { type: 'string', enum: ['use it', 'borrow ideas only', 'skip it', 'not tested enough to say'] },
    what_to_take_into_the_job: { type: 'array', items: { type: 'string' } },
    guide_file: { type: 'string' },
  },
  required: ['tool', 'real_project', 'claims_checked', 'installed_and_ran_here', 'recommendation', 'guide_file'],
}

const TOOLS = [
  {
    key: 'ucupaint',
    file: '03 Research - Ucupaint.md',
    brief: `TOOL: Ucupaint (an open-source Blender add-on for layer-based texturing, formerly known by another name; find out). Test: install it into a copy of Blender's add-on setup for 5.2.2 (a user folder inside your sandbox; Blender 5 prefers 'extensions' but legacy add-on zips may still load; find what works), enable it in background mode, and check: does it load on 5.2.2 at all; can you create its layer setup and add layers by Python (procedural texture layers such as noise/voronoi/brick, solid colour layers, masks, a layer stack with blend modes) without a screen; what node groups does it generate and could our recipes' node groups be used as layers; does it bake colour/normal/height/roughness/AO to images headlessly and are those pixel-exact compared with our photograph route (${ROOT}/lib/bake_harness.py); could it help build a 'stack of layers' structure for our wear/outline/blotch layers; does it have anything for seamless tiles; does it need a GPU or the interface. Also check the 'replacement for Mixar's texture-layer editor' claim (what could 'Mixar' be? Mixer/MixAR/Mixer add-on? Substance? say what you find).`,
  },
  {
    key: 'material_maker',
    file: '03 Research - Material Maker.md',
    brief: `TOOL: Material Maker (a free open-source node-based procedural texture program built on the Godot engine, MIT licence per the chat; verify). Test: download the official Linux release into your sandbox (check the size first), find out whether it can run on this machine without a GPU (try a virtual display such as Xvfb with software OpenGL, or its command-line export options), and if it runs, (a) list its node library (patterns, bricks/tiles, noise, voronoi, warp, blur, colorize/gradient, normal-map-from-height, edge detect/outline nodes, tile samplers/splatter, etc.), (b) work out its file format (.ptex JSON) and whether graphs can be written by a script and exported to PBR maps (albedo, height, normal, roughness, metallic, AO) at 1254 px headlessly, (c) build or adapt a brick graph from its own library, export 1254 px maps, and score them with ${ROOT}/lib/texture_compare.py and ${ROOT}/lib/pixel_compare.py against the brick reference to see whether it reaches closer than Blender nodes did (early Blender node attempts scored about 0.41 overall on texture_compare and 'none' on pixel_compare), (d) read how its key nodes (bricks, tiler, noise, voronoi, directional blur, edge detect, 'colorize') are built (their GLSL/graph code) so we can re-create the useful ones as Blender node groups, (e) check whether it exports anything Blender can use directly (material export, .mmpp, Blender add-on 'Material Maker for Blender'/'Import'), and how tileable its outputs are (measure seam ratio). Also list the other free procedural-texture programs you come across that are similar (name, licence, one line) without testing them.`,
  },
  {
    key: 'mcp_blender_agent',
    file: '03 Research - MCP Blender Agent.md',
    brief: `TOOL: 'MCP Blender Agent' (the chat says: typed, validated tools instead of AI-written scripts, grouped undo, much smaller than the established Blender MCP). Find the real project(s) with that or a similar name (there are several Blender MCP servers: Blender Lab's official blender_mcp which this job already uses, ahujasid/blender-mcp, others; identify which one 'MCP Blender Agent' refers to, licence, maintainers, last commit). Test: if installable here, install it in your sandbox, run its Blender add-on/server headless, and try its typed tools on a small job (create material with nodes, set a node input, bake or render a flat tile, group an undo step, query the scene); compare honestly with what we already do: the official Blender Lab MCP (tools you can load with ToolSearch: mcp__blender__execute_blender_code, search_manual_docs, search_api_docs, get_python_api_docs, the *_for_cli variants) plus plain command-line Blender scripts. Judge: does typed/validated editing help a texture job built from Python recipes and many parallel helpers (shared state, safety, reproducibility, speed), does grouped undo matter in headless runs, does it add any texture/material-specific tools, does it need a GUI or GPU, and security: what can the server do to the machine (arbitrary code execution, network listening, file access) and what you would want before trusting it. It is described as being for rigging and animation: say what it offers for modelling and materials.`,
  },
]

phase('Sweep')
const results = await parallel(TOOLS.map(t => () =>
  agent(`${SHARED}\n\nYOUR GUIDE FILE (save exactly here): ${ROOT}/research/${t.file}\n\n${t.brief}\n\nWhen finished, answer with the structured result.`, {
    label: `sweep:${t.key}`, phase: 'Sweep', schema: RESULT,
  })
))
log(`sweep done: ${results.filter(Boolean).length} of ${TOOLS.length}`)
return TOOLS.map((t, i) => ({ tool: t.key, result: results[i] }))
