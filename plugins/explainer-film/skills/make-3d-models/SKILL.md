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

**Example.** `build_factory.py` makes a 1915 munitions works: brick walls with real arched window
openings (Boolean cuts), stone sills and cornice, a sawtooth roof of corrugated iron with lit glazed
north lights, a tapered chimney, an office with a slate roof, a water tank on a trestle, a cobbled
forecourt. 22,000 triangles, 4 MB. It replaced a 2,000-triangle card box; the viewer's frames went
from a white box on a black table to a lit works in a full town.

## Set up (once)

```
python3 -m venv /path/blender-env && /path/blender-env/bin/pip install bpy pillow
```
(`bpy` 5.x needs Python 3.13; 5.2.2 worked.) EEVEE does not start without a GPU (no libEGL); Cycles
on the CPU does, and bakes.

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
   - Keep each model under about 25,000 triangles; a whole set (town + 2 works) about 70,000 films at
     a normal speed in the software renderer.
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
