---
name: make-3d-models
description: Make detailed 3D models for a film's model sets (buildings, a town, a desk, props) by scripting Blender with its Python module (bpy) - no screen needed - and load them into cinema pages as .glb files with baked corner shading. Use when a page's card models look plain or sparse, or a set needs to fill a tall frame (top and bottom thirds).
---

# Make 3D models in Blender (by script)

Chapter 2's viewer called the old card-box factories "a sudden drop in visual quality" and asked for
"significantly higher quality" models, pointing at Blender's official MCP server. Research found:
Blender Lab's MCP server (projects.blender.org/lab/blender_mcp; Blender 5.1+) and the community
ahujasid/blender-mcp both mostly send Python to a running Blender. An agent that can run code gets
the same result by scripting Blender's `bpy` module directly, headless. Rendering whole frames in
Blender's Cycles on 4 CPU cores takes 35 to 90 s a frame (80 to 200 hours a film), so Blender only
BUILDS the models; the three.js stage still films them.

**Places built in 3D and painted over** (logs 29 to 34: Blender builds a whole place, draws one picture of
it, an image model paints that over, and the page shines the painting back onto the set) have their own
skill: `build-and-paint-a-place`. Its Blender scripts are in `kit/paper-film/blender/pit-village/` (the
street, the props library, set dressing, three shots), `kit/paper-film/blender/figures/` (people) and
`kit/paper-film/blender/inflation-chapter-2-newcomers/props/`.

**Example.** `build_factory.py` makes a 1915 munitions works: brick walls with real arched window
openings (Boolean cuts), stone sills and cornice, a sawtooth roof of corrugated iron with lit glazed
north lights, a tapered chimney, an office with a slate roof, a water tank on a trestle, a cobbled
forecourt. 22,000 triangles, 4 MB. It replaced a 2,000-triangle card box; the viewer's frames went
from a white box on a black table to a lit works in a full town.

## The official Blender MCP server (use it: its guidance and tools)

The owner asked for it ("use blender MCP as well. It'll teach you how to use it to get good detailed
results"). Blender Lab's server runs without a screen:
```
# Blender itself (the full program, ~400 MB; check the published checksum)
curl -O https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz && tar -xf blender-5.2.2-linux-x64.tar.xz
B=$PWD/blender-5.2.2-linux-x64/blender
# the server's add-on, built and installed into Blender
git clone https://projects.blender.org/lab/blender_mcp.git
$B --factory-startup --command extension build --source-dir blender_mcp/addon/blender_mcp_addon --output-dir .
$B --command extension install-file -r user_default -e mcp-1.0.0.zip
# the server itself
python3 -m venv mcp-env && mcp-env/bin/pip install ./blender_mcp/mcp
# run Blender headless, listening only on this machine (--online-mode allows the add-on's local socket)
$B --background --online-mode --command blender_mcp --host 127.0.0.1 --port 9876 &
```
Connect it to Claude Code for the next session: `claude mcp add blender -e BLENDER_MCP_HOST=127.0.0.1
-e BLENDER_MCP_PORT=9876 -e BLENDER_PATH=$B -- $PWD/mcp-env/bin/blender-mcp` (a running session does
not pick up new servers). In the meantime, or for helpers, call its tools with the bundled client:
`BLENDER_MCP_SERVER=$PWD/mcp-env/bin/blender-mcp mcp-env/bin/python ${CLAUDE_PLUGIN_ROOT}/kit/paper-film/blender/blender_mcp_call.py guide | tools | TOOL '{json}' | run-file SCRIPT.py`.

What it gives: its own instructions to models (`guide`: inspect before changing, operators versus
the data API, modes, selection, coordinate spaces), full-text search of Blender's bundled manual and
Python API (`search_manual_docs`, `search_api_docs`, `get_python_api_docs`), scene inspection
(`get_objects_summary`, `get_object_detail_summary`), code execution in Blender
(`execute_blender_code`) and quick Cycles thumbnails (`render_thumbnail_to_path`).
Traps found here: its sandbox refuses `bpy.ops.wm.read_factory_settings` (use
`bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)`); set the render engine to
Cycles before any render in a Blender with no screen (EEVEE crashed there without a GPU; with a virtual
screen it works, see "Set up"); thumbnails are written
into Blender's temp folder (the reply gives the path). One headless Blender per helper (own port).

Modelling guidance learned through the server (its rules, tested bpy settings with manual
sources, sizes that show on a phone, traps): `${CLAUDE_PLUGIN_ROOT}/skills/make-3d-models/blender-mcp-notes.md`.
Most visible first: bevels with `harden_normals=True` plus a Weighted Normal modifier and smooth
shading (plain bevels show as hard facets); bevel walls after cutting their openings; join parts by
material (232 parts to 19) to draw faster.

## Set up (once)

```
python3 -m venv /path/blender-env && /path/blender-env/bin/pip install bpy pillow
```
(`bpy` 5.x needs Python 3.13; 5.2.2 worked.) With only this module EEVEE did not start without a GPU
(no libEGL); Cycles on the CPU does, and bakes.

EEVEE without a GPU (logs 29 to 34): use the full Blender program (5.2.2) under a virtual screen:
```
Xvfb :96 -screen 0 1920x1080x24 &
DISPLAY=:96 /path/blender-5.2.2-linux-x64/blender -b SCENE.blend --python SCRIPT.py -- ...
```
A plate of 1536 x 2730 took about 10 minutes, a 540 x 960 preview about a minute. Give EEVEE enough shadow
memory: `set_dressing.render()` in `kit/paper-film/blender/pit-village/` sets it, and a render log with
"Shadow buffer full" (false hard shadows) or "Could not allocate shadow atlas" (no shadows) is a failed
picture. `explainer-film-setup` looks for Blender and Xvfb and writes them into the kit's
`machine-settings.env`.

## Make a model

1. Copy a script from `${CLAUDE_PLUGIN_ROOT}/kit/paper-film/blender/` as a pattern:
   `build_factory.py` (a building), `build_town.py` (a whole set: ground, streets, terraces, far
   chimneys, a gasholder, a viaduct; linked copies), `build_desk.py` (an interior table top),
   `build_props.py` (named groups to copy: barrels, crates, a lamp post, a cart).
2. Use the tools in `model_kit.py`: `box`, `cylinder`, `prism` (an outline pushed out: gables,
   arched openings), `plane` (a picture once over a face: windows, signs), `corrugated_sheet`,
   `array`, `cut` (Boolean openings), `marker` (a named spot the page can find), `group`,
   `material(kind)` with tiling textures from `textures.py` (brick red/brown/yellow, stone,
   corrugated, slate, setts, cinders, planks, riveted, wood, leather) at true world size, lit
   materials named `...-glow` (the page turns them up and down).
3. Rules learned:
   - Blender's -y is the front (three.js +z, towards the camera); z is up.
   - The output name must end in `.glb` (Blender adds `.glb` to any other name).
   - Detail that reads on a phone: real openings and recesses, bevelled edges (they catch the lamp),
     many small parts (sills, copings, gutters, downpipes on brackets, ridge flashing), lit windows.
   - Baked shading (`finish(path, bake=True)`): 1024 px, 32 samples, reach 0.6 units, about 2
     minutes. (2048 px, 48 samples and Blender's default reach of 10 took 12 minutes and darkened
     everything.) A part left out of the bake gets its own material copies automatically.
   - Budget by filming time, not by triangles. On card-model pages (chapter 2, log 20) a model of about
     25,000 triangles and a whole set (town + 2 works) of about 70,000 filmed at a normal speed in the
     software renderer. In a painted set whose camera holds, the stage draws the set once and only the
     moving things each frame (the Works: about 0.9 s a frame held, 4.3 s sliding, round 4, one worker),
     so the size of the set matters mostly while the camera moves. Measure a page before filming with
     `node paper-film/tools/profile_frame.mjs PAGE TIME` (it times the frame, then without each kind of
     thing, so the slow part shows).
4. Run: `/path/blender-env/bin/python build_X.py /kit/assets/models/<chapter>/X.glb`.
5. Look at it in the stage before using it:
   `PAPER_FILM_QUERY="model=/assets/models/<chapter>/X.glb&cam=3.6,2.4,7.5&look=0,1,0&fov=42" node paper-film/tools/render-paper-film.mjs model-preview OUT --stills 1`

## Chapter 2's models

The worked example (`kit/paper-film/scenes/inflation-chapter-2/`) loads four models that are not
shipped as files; make them once (about 5 minutes):
```
cd <kit>/paper-film/blender && B=$BLENDER_PYTHON; M=<kit>/assets/models/inflation-chapter-2
$B build_factory.py $M/factory-a.glb --brick red --office left --seed 1
$B build_factory.py $M/factory-b.glb --brick brown --office right --seed 2
$B build_town.py $M/town.glb && $B build_desk.py $M/desk.glb && $B build_props.py $M/props.glb
```

## Use it in a page

```js
import { loadModel, modelFactory, markerAt } from '../model-loader.js';
const town = await loadModel('/assets/models/<chapter>/town.glb'); kit.scene.add(town);
const works = await modelFactory('/assets/models/<chapter>/factory-a.glb');   // same handles as paperFactory
works.group.position.set(-1.4, 0, 2.2); kit.scene.add(works.group); works.setRunning(1);
const smokeFrom = works.chimneyTop.clone().add(works.group.position);
```
Copy a prop group: `props.getObjectByName('barrels').clone(true)`. Chapter 2's
`two-factories-set.js` shows the full set (town, two works, door lamps, far smoke, props).

## Fill the tall frame (with the models)

- A low camera at the model's eye height, a fairly wide lens, close in. Stack subjects in depth
  (near works left, far works right; three cut-outs staggered front to back), not side by side.
- Top third: chimneys, smoke, a painted sky. Bottom third: soft out-of-focus props (barrels, crates,
  a cart, a lamp post) in the near corners, never bare dark ground.
- Frame with numbers first: `python3 -I paper-film/tools/frame_check.py CAM TARGET FOV name=x,y,z ...`
  says where each thing lands in the 1080 x 1920 frame, in a second, before any still is made.

## Or: lift things out of a painting with SAM 3D (tested once, log 22 of the austerity project)

Turns things in one painting (a car, pumps) into 3D models that stand where they were and still look
painted. About 12 US cents a painting on fal (confirm spending first). Worked example:
`paper-film/scenes/sam-3d-petrol-station-test.js` in the austerity project's film kit.

1. Mark a box round each thing in the painting (pixels). Send the painting and the boxes to
   `fal-ai/sam-3/3d-objects` in ONE run (`box_prompts`, `export_textured_glb: true`): one model per box
   plus each model's size, turn and position in SAM's own camera (`metadata`).
2. `blender-env/bin/python paper-film/tools/sam3d_fit_layout.py metadata.json GLB_FOLDER boxes.json`
   finds how SAM's layout maps onto the painting (for the first painting: model files a quarter-turn
   about x, turn given w first and applied inverted, x pointing left, lens tanX 0.300).
3. `sam3d_make_clean_plate.py masks` (Blender's Python) then `plate` (system Python) draws each
   model's outline as a mask and makes a rough clean plate; repaint the plate properly with an image
   edit model (Flux 3 edit, about 10 US cents: "remove the ... keep everything else") and blend it in
   only inside the outlines with `composite_fill.py`.
4. `ground_under_objects.py` fits the ground around each thing's base and puts a flat floor in the
   clean depth picture where it stood (without this the models float or sink).
5. In the page: place each model on its line of sight, standing on that ground; let it wear the
   painting projected from where it was painted on every surface the painting showed, and SAM's own
   surface only on hidden sides; give it only a touch of the lamp (see the worked example).

Traps found in the test:
- SAM's model files carry no surface directions: call `geometry.computeVertexNormals()` or they
  draw as black blocks.
- Keep the stage's standard colour handling for both the painting and the models' surfaces.
- Far or small things are better left painted (SAM placed the far car 30-40 px off with pink trim).
- The painted room still tears beyond a short push (canopy posts, building edges): keep moves small,
  or split such buildings into their own layers.

## Or: make a painting's near, upright parts solid with stand-ins (tested once, log 24)

When a push bends posts, a canopy or a building front, replace just those with simple boxes that
wear the painting (shared code `paper-film/scenes/painted-projection.js`; worked example in the
austerity project's film kit, `station-proxies-test.js`, `fit_station_proxies.py`, `station_plates.py`):
1. Fit a box to each thing's painted edges in the painted room's space; if the painting's perspective
   doesn't add up (AI paintings rarely do), fit to the painted corners instead of a true rectangle.
   Check on a wireframe over the painting first.
2. Paint those things out of the background and push that part of its depth back, so they aren't
   shown twice. Repaint that part properly (an image edit model): a free smear is hidden on a straight
   push but shows on any sideways step.
3. Dress each box with `projectedMaterial(picture, room, { fallback, lit: 0 })` and give the painted
   room `lit: 0` too: both show the painting exactly, with its painted light and no lamp, so their
   edges don't jump in brightness. Put shadows of 3D models on `shadowCatcher(...)`.
4. Check: the painting's view must match the painting; on a 1.25 times push the posts must stay
   straight and slide in front of what's behind them.
