# 22 Blender MCP notes: detailed models

These notes are for the helpers who will rebuild the chapter 2 models: the two 1915 munitions works,
the model town, the reviewer's desk and the loose props. The viewer asked for "significantly higher
quality" and said: "Blender has an official MCP to use for this ... It'll teach you how to use it to
get good detailed results". Everything below was checked against the official Blender MCP server
(Blender Lab `blender-mcp` v1.0.2, Blender 5.2.2). The server was run headless on this machine, the
current `.glb` files were loaded into it and rendered, and every code snippet in section B was run
through `execute_blender_code` unless it is marked otherwise.

Read it with `20 Guide - building a cinema page.md` and `21 Guide - camera rule, filling the frame, no clipping.md`.

Sources are given as paths inside the server's bundled docs
(`<blender_mcp clone>/mcp/blmcp/data/`), in the form the search tools return them
(`manual/...rst`, `api/...rst`), or as the identifier passed to `get_python_api_docs`.

---

## A. The Blender MCP server: its rules and how to use it here

### A1. Starting and stopping your own Blender

```bash
<blender> --background --online-mode \
  --command blender_mcp --host 127.0.0.1 --port 9880 > /tmp/blender-9880.log 2>&1 &
echo $!          # keep this process id. Stop it at the end with: kill <PID>
                 # (never use pkill -f, which can kill your own shell)

export BLENDER_MCP_SERVER=<mcp-env>/bin/blender-mcp \
       BLENDER_PATH=<blender> \
       BLENDER_MCP_HOST=127.0.0.1 BLENDER_MCP_PORT=9880
C="<mcp-env>/bin/python <kit>/paper-film/blender/blender_mcp_call.py"
```

Each helper uses their own port (9880, 9881, ...). If Blender crashes (an EEVEE render or running out
of memory will do it), start it again. Scene state does not survive a restart.

### A2. The server's own instructions (`$C guide`), and what each means for building models by script

| Server rule | What it means here |
|---|---|
| "Respect existing structure and naming conventions." "NEVER assume missing values - inspect the scene first." | Keep the names the pages depend on. Materials ending in `-glow` (`window-glow`, `roof-glow`, `door-glow`, `office-glow`, `lamp-glow`, `house-window-glow`) are found by name in `model-loader.js`. The empties are found by name too: `chimney_top`, `door`, `yard`, `door_lamp`, `office_door`, `desk_lamp`, `ink_pad`, `smoke-N`, `lamp-N`, `lamp-post-light`. So are the prop groups `barrels`, `crates`, `lamp-post` and `cart` (`two-factories-set.js` clones them with `getObjectByName`). Before you change a model, run `get_objects_summary` and `get_object_detail_summary`. |
| "Do not destructively modify objects without confirmation." | Do not edit the build scripts in place unless that is your task. Try ideas in your own Blender session first. |
| "`execute_blender_code` is a last resort, if there are other tools ... use those instead." | Use `get_objects_summary`, `get_object_detail_summary` and `render_thumbnail_to_path` to inspect. Use `run-file` for the modelling itself, because no other tool builds geometry. |
| "Prefer operators (`bpy.ops`) for standard actions ... Use the data API (`bpy.data`) for precise control or to avoid side effects." | `model_kit.py` already uses bmesh and the data API for its primitives, which is right. Use operators for apply, join, smart project, bake and export. |
| "Many operators depend on the current mode ... wrong mode either fails or silently does nothing." | Before `bpy.ops.uv.*`, enter `mode_set(mode='EDIT')`. Before `modifier_apply`, `join` and `bake`, go back to OBJECT mode. |
| "The active object and selection are distinct ... re-set both between sequential operator calls on different objects." | Do as `model_kit.apply_modifiers` does: `select_all(action='DESELECT')`, then `select_set(True)`, then set `view_layer.objects.active` before every apply, join or bake. |
| "Update the dependency graph after changes before reading computed properties." | Count triangles with `bpy.context.evaluated_depsgraph_get()` (as `mk.count_triangles` does), and call `view_layer.update()` after you move things. |
| "In edit mode, access mesh geometry through the bmesh API ... Flush bmesh changes back ... forgetting this silently loses all edits." | Always end with `bm.to_mesh(mesh); bm.free()`, or with `bmesh.update_edit_mesh` in Edit mode. |
| "Return structured data (dicts, lists) from executed code, not print output." | In `run-file` scripts, set `result = {...}`: triangle counts, names, timings. Printed output gets buried in importer logs. |
| "Objects created via the data API must be linked to a collection." "Names auto-append .001 ... capture references immediately." | Keep the object a call returns. Never look an object up later by the name you expect it to have. |
| "Shared data: check user count before modifying a datablock." | The town's terraces are linked copies that share one mesh. Editing one edits all 17 of them. Call `.copy()` on the mesh first if you want a single row to differ. |
| "Apply transforms (especially scale) before geometry-dependent operations (booleans ...)." | Before you bevel or cut a part made by scaling, call `transform_apply(scale=True)`. Otherwise bevel widths come out stretched. |
| "Blender defaults to meters. Check scene unit settings." | 1 Blender unit = 1 three.js unit. The factory is 3.2 wide. Detail sizes in section B are given in these units. |
| Bundled manuals: "`data/api/` ... Consult when writing or debugging bpy code"; "`data/manual/` ... for conceptual explanations" | Call `search_manual_docs`, `search_api_docs` and `get_python_api_docs '{"identifier": "bpy.types.BevelModifier"}'`, or grep the `.rst` files directly. The bundled docs match Blender 5.2, so trust them over memory. Several things moved in 4.1 to 5.x (see section D). |

### A3. Tools that proved useful

- `$C tools` lists them all. The useful ones: `get_objects_summary`, `get_object_detail_summary '{"name":"walls"}'`,
  `execute_blender_code` (through `$C run-file script.py`), `render_thumbnail_to_path '{"output_path":"x.png"}'`
  (320 px, quick), `render_viewport_to_path '{"output_path":"x.png"}'` (uses your scene's render
  settings, which gives a 432 x 768 look at the film's frame), `search_manual_docs`, `search_api_docs`,
  `get_python_api_docs`, `get_blendfile_summary_datablocks`.
- The `*_for_cli` variants run a separate background Blender on a `.blend` file. That is handy for
  checking a saved file without disturbing your live scene.
- `get_screenshot_*` and `jump_to_*` need a UI, so they are of no use headless.

### A4. A look-at-it stage (tested)

```python
import bpy, math
from mathutils import Vector
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)   # NOT read_factory_settings (refused)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 24   # before ANY render; EEVEE crashes
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1080, 1920, 40
bpy.ops.import_scene.gltf(filepath='<kit>/assets/models/inflation-chapter-2/factory-a.glb')
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.025, 0.035, 1)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera = cam
cam.location = (-1.2, -5.2, 1.6)                       # front left; Blender -y is the model's front
cam.rotation_euler = (Vector((0.2, 0, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); s.collection.objects.link(sun)
sun.data.energy = 3.5; sun.data.color = (1.0, 0.82, 0.62); sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
result = {'objects': len(s.objects)}
```
Then run `$C render_viewport_to_path '{"output_path": "look.png"}'`. The reply gives the real path
(under `bpy.app.tempdir/blender_mcp/`). Read the PNG to see the render. One render takes about
30 to 60 s on the CPU.

---

## B. Techniques, with exact settings and sources

### Sizes to work to: what shows on a phone

The film frame is 1080 px wide and shows about 4.5 units across at the factory. That is about
**240 px per unit**, so:
- **0.004 units ≈ 1 px.** Anything smaller is invisible in focus, and the depth of field and grain
  make it worse.
- **0.008 to 0.015 units** is a bevel that catches a 2 to 4 px highlight from the warm lamp at front
  left. This is the "well finished" look.
- **Real geometry is worth it at 0.01 units of depth or more**: window reveals, glazing bars,
  copings, voussoirs, door ledges, sill drips. Below that, use a normal map.
- The background (town, far chimneys) is soft with focus. Spend triangles where the focus falls
  (each page's subject) and in the silhouettes against the sky (chimney caps, roof ridges, lamps).

### B1. Bevel modifier: soft edges that catch the light
Source: `manual/modeling/modifiers/generate/bevel.rst` (Options > Shading: "Harden Normals ... the
per-vertex face normals of the bevel faces are adjusted to match the surrounding faces ... keep the
surrounding faces flat ... with the bevel faces shading smoothly into them"). API: `bpy.types.BevelModifier`
(`width`, `segments` default 1, `limit_method` 'NONE'|'ANGLE'|'WEIGHT'|'VGROUP', `angle_limit` default
0.5236, `harden_normals`, `use_clamp_overlap` default True, `miter_outer` 'MITER_SHARP'|'MITER_PATCH'|'MITER_ARC',
`face_strength_mode` 'FSTR_NONE'|'FSTR_NEW'|'FSTR_AFFECTED'|'FSTR_ALL', `profile` 0.5 = round).

```python
b = obj.modifiers.new('bevel', 'BEVEL')
b.width = 0.010                      # 0.006 small trims, 0.010-0.015 walls/copings/sills, 0.02 desk top
b.segments = 2                       # 1 for small or far parts (box 12 -> 44 tris); 2-3 for hero parts (box -> 108 tris)
b.limit_method = 'ANGLE'; b.angle_limit = math.radians(30)
b.use_clamp_overlap = True           # stops thin parts from turning inside out
b.miter_outer = 'MITER_ARC'          # rounder corners where 3 edges meet
b.harden_normals = True              # KEY: flat faces stay flat, only the bevel shades round
b.face_strength_mode = 'FSTR_AFFECTED'   # feeds the Weighted Normal modifier below
obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))   # or bpy.ops.object.shade_smooth()
```
**What is wrong now:** `model_kit._finish_part` uses `segments=2, harden_normals=False` on
flat-shaded boxes, so every bevel shows as two hard facets instead of a soft highlight. The big boolean-cut
walls (`walls`, `office`, `terrace-walls`) get no bevel at all, which gives razor corners. Tested:
a box with this setup plus B2 exports and re-imports with custom normals intact (108 tris).

### B2. Weighted Normal modifier and smooth by angle: clean shading on low-poly parts
Sources: `manual/modeling/modifiers/normals/weighted_normal.rst` ("can be useful to make some faces
appear very flat during shading"; Face Influence "Use face weights ... as assigned by ... the Set
Strength mode of a Bevel modifier"); `manual/modeling/modifiers/normals/smooth_by_angle.rst`;
`manual/scene_layout/object/editing/shading.rst` (Shade Auto Smooth "Adds a Smooth by Angle modifier ...
pinned to be the last modifier"). API: `bpy.types.WeightedNormalModifier` (`mode` 'FACE_AREA',
`weight` 50, `keep_sharp`, `use_face_influence`); `bpy.ops.object.shade_auto_smooth(angle=0.5236)`;
`bpy.types.Mesh.set_sharp_from_angle(angle=...)` ("Reset and fill the 'sharp_edge' attribute").

```python
wn = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL')     # add AFTER the bevel
wn.mode = 'FACE_AREA'; wn.keep_sharp = True; wn.use_face_influence = True
# for cylinders (pipes, barrels, chimney pots, lamp columns): smooth sides, sharp caps
obj.data.set_sharp_from_angle(angle=math.radians(40)); obj.data.polygons.foreach_set('use_smooth', [True]*len(obj.data.polygons))
```
Since Blender 4.1 there is no `mesh.use_auto_smooth`. Use the Smooth by Angle modifier,
`shade_auto_smooth`, or `set_sharp_from_angle` instead.

### B3. Sharp edges and how glTF exports them
Source: `manual/addons/scene_gltf2.rst` (Meshes: "Discontinuous UVs and flat-shaded edges may result in
moderately higher vertex counts in glTF ... such vertices are separated for export"; "quads and n-gons
are automatically converted to triangles"). Normals export with `export_normals=True` (the default).
Custom normals from B1 and B2 export as they are, because the exporter writes split normals.
Every hard edge splits vertices, so prefer smooth shading with harden normals over flat shading.

### B4. Solidify: thickness for sheets
Source: `manual/modeling/modifiers/generate/solidify.rst`. API: `bpy.types.SolidifyModifier` (`thickness`,
`offset` default -1, `use_even_offset`, `use_rim` default True).
```python
sd = obj.modifiers.new('thick', 'SOLIDIFY'); sd.thickness = 0.006; sd.offset = -1; sd.use_even_offset = True
```
Use it for door leaves built as planks, shade glass, paper sheets (0.002), canopy sheets, sack
cloth and gutter shells. A plane seen edge-on from front left vanishes. A 2 to 6 mm rim reads as a
real object.

### B5. Arrays, and following a curve (railings, gutters, coping stones, chains of bricks)
Sources: `manual/modeling/modifiers/generate/array_legacy.rst` ("Fit Curve: Generates enough copies to
fit within the length of the curve object"; "Applying the scale can be useful for both"; merge
vertices); `manual/modeling/modifiers/deform/curve.rst` ("the mesh will traverse along the curve, as if it
was a train following and deforming along rails"). API: `bpy.types.ArrayModifier` (`fit_type`
'FIXED_COUNT'|'FIT_LENGTH'|'FIT_CURVE', `curve`, `use_merge_vertices`, `merge_threshold`, `start_cap`,
`end_cap`, `use_relative_offset`, `use_constant_offset`); `bpy.types.CurveModifier` (`object`,
`deform_axis` 'POS_X'...).
```python
# a run of coping stones with real joints, then bent along a gable slope or round an arch
stone = mk.box('coping', (0.118, 0.09, 0.03), material=stone_mat, bevel=0.006)   # one stone, 2 mm short of its pitch
arr = stone.modifiers.new('run', 'ARRAY'); arr.use_relative_offset = False
arr.use_constant_offset = True; arr.constant_offset_displace = (0.12, 0, 0)
arr.fit_type = 'FIT_CURVE'; arr.curve = path_curve
cm = stone.modifiers.new('follow', 'CURVE'); cm.object = path_curve; cm.deform_axis = 'POS_X'
```
`obj.modifiers.new(type='ARRAY')` gives the **legacy** Array modifier, which is the documented
`bpy.types.ArrayModifier`. The new 5.x "Array", "Curve to Tube" and "Scatter on Surface" modifiers
(`manual/modeling/modifiers/generate/array.rst`, `curve_to_tube.rst`, `scatter_on_surface.rst`) are
node-group assets from the Essentials library. Do not rely on them in a headless script.

### B6. Curves for pipes, rails and rods
API: `bpy.types.Curve` (`bevel_depth`, `bevel_resolution`, `resolution_u`, `use_fill_caps`, `bevel_object`).
```python
cu = bpy.data.curves.new('downpipe', 'CURVE'); cu.dimensions = '3D'
cu.bevel_depth = 0.011; cu.bevel_resolution = 2; cu.resolution_u = 6; cu.use_fill_caps = True
sp = cu.splines.new('POLY'); sp.points.add(3)   # set sp.points[i].co = (x, y, z, 1)
ob = bpy.data.objects.new('downpipe', cu); bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.convert(target='MESH')
```
Curves must be turned into meshes before export (`manual/addons/scene_gltf2.rst`: "curves and other
non-mesh data are not preserved, and must be converted to meshes"). Use them for downpipes with
offsets (swan-neck) round the cornice, valley gutters with stop-ends, railing tops, the lamp's pull
chain, the pen clip, the cart's handles and the wire spectacle temples.

### B7. Screw (lathe) modifier for turned objects
Source: `manual/modeling/modifiers/generate/screw.rst` ("takes a profile object, a mesh or a curve ...
Steps Viewport / Render"). API: `bpy.types.ScrewModifier` (`angle`, `axis`, `steps`, `render_steps`,
`use_merge_vertices`, `use_smooth_shade`, `use_normal_calculate`).
```python
# draw half a profile as an edge chain in x-z (radius, height), then spin it round z
sc = prof.modifiers.new('lathe', 'SCREW'); sc.axis = 'Z'; sc.steps = sc.render_steps = 24
sc.use_merge_vertices = True; sc.use_smooth_shade = True; sc.use_normal_calculate = True
```
Use it for barrels with a bulge (belly 1.08 x the ends), tea cup with lip and foot ring, saucer with
a well, chimney pots with a rolled rim, gas-lamp column with base mouldings, lamp finial, pen barrel
and cap, brass lamp base with steps, and the gasholder crown. 16 to 24 steps is enough at film size.

### B8. Booleans
Source: `manual/modeling/modifiers/generate/booleans.rst` ("Only Manifold meshes are guaranteed to give
proper results"; solvers: Float "good performance but lacks support for overlapping geometry", Exact
"best results ... full support for overlapping geometry, but is much slower", Manifold "usually fastest
but only works on Manifold meshes"; Exact options: Self Intersection, Hole Tolerant). API:
`bpy.types.BooleanModifier` (`solver` 'FLOAT'|'EXACT'|'MANIFOLD', `operand_type` 'OBJECT'|'COLLECTION',
`use_self`, `use_hole_tolerant`, `material_mode` 'INDEX'|'TRANSFER').
Best practice for this kit:
- Make cutters closed boxes or prisms that **stick out past the face they cut by 0.01 or more** (and
  right through thin parts), so no cutter face lies on the same plane as a wall face. The walls are one solid box, so a `mk.prism` cutter 0.12 deep
  centred on the front face sinks a 0.06-deep reveal. To deepen a reveal (C1), make the cutter deeper.
- Cut with many joined cutters at once (as `mk.cut` does), and use `operand_type='COLLECTION'` with
  `solver='EXACT'` when cutters overlap.
- **Order: cut, then bevel (B1), then weighted normals (B2), then box_map.** A bevel before the cut
  breaks the opening edges. Booleans leave long thin triangles, which look fine only when shading is
  hardened.
- Use `material_mode='TRANSFER'` when a cutter should paint the reveal faces with a different material
  (for example stone reveals in brick). Otherwise reveals take the wall's brick (index 0).

### B9. Geometry nodes for repeated detail (bricks, slates, rivets, setts, voussoirs)
Sources: `manual/modeling/geometry_nodes/instances/instance_on_points.rst` ("Instances are a fast way to
add the same geometry to a scene many times"); `manual/modeling/geometry_nodes/instances/realize_instances.rst`
("makes any instances ... into real geometry data"); `manual/modeling/modifiers/geometry_nodes.rst`.
glTF: `manual/addons/scene_gltf2.rst` (Data - Scene Graph: "Geometry Nodes Instances: Export Geometry
nodes instances. This feature is experimental"; API `export_gn_mesh`).
Tested snippet (a grid of jittered blocks, realized, exported and re-imported with the same 768 tris):
```python
tree = bpy.data.node_groups.new('blocks', 'GeometryNodeTree')
tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, L = tree.nodes, tree.links
go = N.new('NodeGroupOutput')
grid = N.new('GeometryNodeMeshGrid'); grid.inputs['Size X'].default_value = 1.0; grid.inputs['Size Y'].default_value = 0.5
grid.inputs['Vertices X'].default_value = 8; grid.inputs['Vertices Y'].default_value = 8
cube = N.new('GeometryNodeMeshCube'); cube.inputs['Size'].default_value = (0.11, 0.05, 0.02)
iop = N.new('GeometryNodeInstanceOnPoints')
rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT_VECTOR'
rnd.inputs['Min'].default_value = (-0.03, -0.03, -0.1); rnd.inputs['Max'].default_value = (0.03, 0.03, 0.1)
real = N.new('GeometryNodeRealizeInstances')
L.new(grid.outputs['Mesh'], iop.inputs['Points']); L.new(cube.outputs['Mesh'], iop.inputs['Instance'])
L.new(rnd.outputs['Value'], iop.inputs['Rotation'])
L.new(iop.outputs['Instances'], real.inputs['Geometry']); L.new(real.outputs['Geometry'], go.inputs['Geometry'])
obj.modifiers.new('blocks', 'NODES').node_group = tree
```
**Always end with Realize Instances.** Tested: applying a GN modifier whose output is still instances
fails with "Evaluated geometry from modifier does not contain a mesh", and `model_kit.apply_modifiers`
would stop there. Plain Python loops with bmesh are just as good for a few hundred pieces and easier
to debug. Use GN when you want jitter (rotation and scale per stone) with no extra code.
**Where real geometry pays off** (it must be 0.01 or more proud to show): voussoirs over arches,
coping stones, quoins, setts only in the 1 to 2 units nearest the camera (raised 0.004 with bevel
segments 1), slate courses on the office roof as stepped strips (one strip per course, not per slate),
and rivet heads on the tank only if the tank is in focus. Bricks in a wall stay **texture plus normal
map**: 24 courses per 0.5 units is 5 px per course on screen.

### B10. Displacement or normal maps
Sources: `manual/render/materials/components/displacement.rst` ("Bump Only ... does not actually alter
the mesh surface, but merely changes the shading"); `manual/render/shader_nodes/displacement/normal_map.rst`
(Strength); `manual/addons/scene_gltf2.rst` (Normal Map: "Image Texture ... Normal Map node ... Normal
input ... Color Space ... Non-Color ... must remain on ... Tangent Space ... will copy the strength
setting into the glTF").
- glTF and three.js have **no displacement**. Displacement must be real geometry (B9) or nothing.
- Normal maps: keep the `Image Texture (Non-Color) → Normal Map (Tangent) → Principled Normal` chain
  (which `model_kit.material` already uses). Raise `normal_strength` to 1.5 to 2.5 for brick and setts:
  under the low warm lamp, mortar lines are what make brick read as brick. Export
  `export_tangents=True` so three.js does not derive tangents itself (B13).

### B11. Texel density and UV scale
Sources: `manual/modeling/meshes/editing/uv.rst` (Smart UV Project: "Angle Limit ... A low limit will
create lots of small UV islands with little distortion"; Lightmap Pack: "Share Texture Space ... maps
won't overlap"); `manual/modeling/meshes/uv/editing.rst` (Average Island Scale, Pack Islands shape
methods). API: `bpy.ops.uv.pack_islands(rotate=True, margin_method='SCALED', margin=0.001, shape_method='CONCAVE')`.
- Tiling textures: `mk.box_map` projects in world units, so a brick is the same size everywhere.
  This is right, so keep it. Brick at 0.5 units per 1024 px tile is 2048 px per unit on 240 screen
  px per unit: plenty. Do not exceed 1024 px textures (the budget). Make **tile sizes realistic for a
  1:~40 model**: setts at 0.6 are fine, cinders at 2.0 repeat visibly over a 70-unit ground (see C3).
- Baked maps (AO, B12): one 1024 atlas for a whole factory means about 300 px per unit at best.
  Give hero parts more: scale the front-wall islands up before `pack_islands`, or bake the forecourt
  and the far parts to a separate 512 map (they are already skipped).
- Rotate box-mapped UVs so that the long grain runs along the long side for wood (desk top, crates,
  door planks). Today the desk grain runs the wrong way on some faces.

### B12. Baking in Cycles on CPU (AO, rounded edges, normals from high to low, curvature)
Sources: `manual/render/cycles/baking.rst` (Setup: "requires a mesh to have a UV map, and ... an Image
Texture node ... The Active Image Texture node ... is used as the baking target"; Bake Types: Ambient
Occlusion "as specified in the World panels. Ignores all lights", Normal; Selected to Active, Cage,
Cage Extrusion, Max Ray Distance; Margin: "important to avoid discontinuities at UV seams, due to
texture filtering and mip-mapping", Type Extend or Adjacent Faces); `manual/render/shader_nodes/input/bevel.rst`
("rendering rounded corners ... does not modify the actual geometry ... we suggest to mainly use this for
baking"); `manual/render/shader_nodes/input/ao.rst` ("using Pointiness ... or baking Ambient Occlusion will
result in faster renders"; Only Local); `manual/render/shader_nodes/input/geometry.rst` (Pointiness, Cycles
only). API: `bpy.ops.object.bake(type='AO'|'NORMAL'|..., margin=16, margin_type='EXTEND',
use_selected_to_active=False, max_ray_distance=0.0, cage_extrusion=0.0, normal_space='TANGENT',
normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', use_clear=False, uv_layer="")`; `bpy.types.WorldLighting.distance`
("Length of rays, defines how far away other faces give occlusion effect", default 10).

Tested on CPU (a 512 px map, 16 samples): **a Bevel-node normal bake takes 1.8 s and an AO bake 2.0 s.**
```python
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 16
# (a) rounded edges without geometry, for small plain-colour parts (iron, stone trim, props)
bev = nodes.new('ShaderNodeBevel'); bev.samples = 8; bev.inputs['Radius'].default_value = 0.01
links.new(bev.outputs['Normal'], bsdf.inputs['Normal'])
img = bpy.data.images.new('edges_n', 512, 512); img.colorspace_settings.name = 'Non-Color'
t = nodes.new('ShaderNodeTexImage'); t.image = img; nodes.active = t
bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=8, use_clear=True)
# then rewire: Image(Non-Color) -> Normal Map node -> BSDF Normal, and remove the Bevel node
# (b) AO: keep the world reach short, as model_kit does (0.6); 0.3 for props and desk items
s.world.light_settings.distance = 0.3
bpy.ops.object.bake(type='AO', margin=8, use_clear=True)
# (c) high-to-low: put the detailed copy and the low copy in place, select high, then make low active
bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, cage_extrusion=0.02, max_ray_distance=0.05)
```
**Curvature and edge wear:** Pointiness is Cycles-only and not baked by a bake type of its own. Bake
it as `type='EMIT'` with Geometry > Pointiness → ColorRamp (0.5 to 0.55) → Emission. Then multiply it
into the base-colour picture in Pillow (lighter worn edges on stone and painted iron, darker dirt in
recesses from the AO map). This is untested here and costs one extra bake per part.
**Bake order:** apply all modifiers first (`mk.bake_shading` does), then add a second UV layer.
**One normal map per material:** see trap D7.

### B13. glTF exporter options that affect quality
Sources: `manual/addons/scene_gltf2.rst` (Data - Mesh, Data - Mesh - Vertex Color, Data - Material,
Data - Scene Graph, GPU Instances, Baked Ambient Occlusion, Metallic and Roughness, Emissive, UV Mapping);
API: `bpy.ops.export_scene.gltf`.
```python
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
    export_apply=True,               # "Apply Modifiers" (blocks shape keys; we have none)
    export_normals=True,             # default; keeps hardened/weighted custom normals
    export_tangents=True,            # default False! turn on when normal maps matter (brick, setts, baked edges)
    export_texcoords=True,
    export_vertex_color='ACTIVE',    # only if you use colour attributes for grime (B14); default 'MATERIAL'
    export_materials='EXPORT', export_image_format='AUTO',   # AUTO keeps .jpg as JPEG and .png as PNG
    export_image_quality=90,         # applies when the exporter re-encodes; default 75
    export_extras=True, export_yup=True,
    export_gpu_instances=False,      # three.js GLTFLoader turns EXT_mesh_gpu_instancing into InstancedMesh, but
                                     # model-loader.js clones materials per mesh: test before enabling
    export_gn_mesh=False)            # experimental; realize instances instead (B9)
```
- glTF "Emissive": "If any component of emissiveFactor is > 1.0, `KHR_materials_emissive_strength`
  extension will be used". The `-glow` materials depend on it, and three r169 supports it.
- Metallic and roughness pictures: glTF wants roughness in **G** and metal in **B** of one Non-Color
  image ("Separate RGB ... connect the green (G) channel to Roughness, and blue (B) to Metallic").
  A roughness map is the cheapest big upgrade for iron, slate, wet setts and the desk's polish (see C).
  AO can share the same image in **R** ("glTF stores occlusion in the red channel").
- `KHR_texture_transform`: a Mapping node exports location, rotation (Z) and scale. "Not all glTF
  readers support multiple UV maps or texture transforms", though three r169 does. Prefer baking the
  scale into UVs (box_map), as now.
- Draco and meshopt compression would save file size but need decoder set-up in `model-loader.js`.
  Not needed: the files are 0.4 to 4.3 MB.

### B14. Colour attributes for cheap large-scale variation
Source: `manual/addons/scene_gltf2.rst` (Vertex Color: "A fully compliant glTF viewer should display
this VC as Base Color multiplier"). glTF allows only one base-colour picture per material. Colour
attributes (vertex colours, multiplied in) are how to darken the foot of walls, add soot under
eaves, dirty the paths across the cinder yard and break up tiling **without another texture**.
```python
ca = mesh.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')   # values 0.6-1.0, multiplied into base colour
# write per-corner colours, e.g. darker near z=0 and under the cornice
```
For three.js to apply them, export them (`export_vertex_color='ACTIVE'`). GLTFLoader turns on
`vertexColors` whenever COLOR_0 is present, so **give every mesh that shares the material colours
(white = 1.0)**, or the meshes without them render black or uncoloured. The ground needs subdividing
(about 1 vertex per 0.5 units) for vertex colours to have anywhere to live.

### B15. Fewer parts, cheaper drawing (software rendering)
The factory has 232 mesh objects, the town 185 and the desk 54 (measured through the MCP).
Each object is a draw call and a shadow-map draw. Under software rendering, draw calls cost as much
as triangles. In `finish()`, after the bake, **join parts that share a material and will never move**
(`bpy.ops.object.join()` with the parts selected). Keep `-glow` materials as separate meshes (they
are found by material name, so joining them per material is fine) and keep the prop groups and
markers. Expect about 20 to 30 draws per factory instead of 232.

---

## C. Prioritised improvements per model (what a viewer notices first on a phone)

Measured today through the MCP (imported `.glb`):

| Model | Triangles now | Budget | Objects | Notes |
|---|---|---|---|---|
| factory-a / factory-b | 22,374 each | 40,000 | 232 | 8 textures at 1024; 1024 AO atlas |
| town | 21,882 | 70,000 | 185 | 13 textures at 1024; no AO bake |
| desk | 3,812 | 20,000 | 54 | |
| props | 2,112 | 6,000 | 26 | colour-only barrels, wheels, sacks |

There is a lot of headroom. Spend it on silhouettes and on edges that catch light in the focus plane.

### C1. The two munitions works (`build_factory.py`, budget 40,000 each; aim for about 34,000 to leave margin)
Seen in `r20-p3-f`, `r20-p3-g` and `r20-p8-b`: front elevation, low warm light from the left, sunset sky behind.
1. **Edges (about +3,000 tris).** Walls, office, pilasters, plinth, cornice, copings and chimney need
   B1 and B2: bevel 0.010 to 0.012 with `harden_normals=True`, smooth shading, then weighted normals.
   Bevel the walls *after* `mk.cut`. Right now every wall corner and every coping is a razor edge with
   faceted bevels, which is what makes it read as "CG boxes".
2. **Windows (about +4,000).** Today the glass is a flat plane with painted bars, 5 cm back. Replace it
   with real cast-iron glazing bars (boxes 0.008 x 0.01) in front of the glass, an outer frame 0.015,
   and a reveal deepened to 0.07. Set the glass back a further 0.02 so the bars cast tiny shadows.
   Keep the material name `window-glow` on the glass. Replace the smooth stone `arch_band` with **brick
   voussoirs** (12 to 15 wedge blocks, alternating headers proud by 0.006, bevel segments 1). Add a
   sill with a drip groove and a projecting nose.
3. **Roof (about +3,000).** The corrugated sheets read flat grey from the front. Add eaves gutters
   (B6 half-round 0.02) on brackets along the front of each bay, barge boards on the gable slopes,
   a lead ridge roll (cylinder r 0.012) and a stepped edge where sheets overlap (two sheets per slope,
   a 0.004 lap). Add a roughness map so the rust runs are matte and the paint has a sheen (B13). Give
   the north lights the same real glazing bars as the windows (now `glazing-bar` boxes exist; add
   horizontal bars and a frame).
4. **Copings and gables (about +2,500).** Split each coping into stones with 2 mm joints (B5) and add
   **kneeler stones** at the foot of each gable and a finial block at the apex. These pieces are on
   the skyline against the bright sky, where they are seen first.
5. **The loading door (about +1,500).** Build the leaves as 7 planks (thin boxes with 1.5 mm gaps), plus
   ledges and a Z-brace on the inside face (seen because the leaves are open 110°), and strap hinges with
   a round end. Behind the opening, add a **shallow interior box**: a dark floor, side walls going back 0.6,
   and two or three simple machine blocks and belt rods in silhouette in front of the `door-glow`
   picture. That gives parallax when the camera moves, and the flat picture gives none.
6. **Sign board and lamp (about +600).** Add a raised moulded frame around `sign` (four bevelled boxes),
   a lantern with four glass panes, a frame and a finial instead of the white box, and a curved iron
   bracket (B6).
7. **Plinth, quoins and pilasters (about +1,500).** Stone plinth blocks with joints; quoin stones at the
   wall corners, alternating long and short, 0.006 proud; stone pilaster bases.
8. **Chimney (about +800).** A real corbelled cap (4 to 5 stepped courses, each bevelled), two iron
   straps, a soot-dark top third by vertex colour (B14), and the lightning rod with a tip.
9. **Forecourt (about +2,000).** Real setts only in the strip nearest the camera (B9), a cast-iron drain
   grate, kerb stones with joints, and a roughness map with damp patches (low roughness picks up the
   lamp).
10. **Grime pass (0 tris).** Vertex-colour darkening at wall feet and under the cornice, and soot
    streaks below window sills (B14), plus AO reach kept at 0.6.

### C2. The model town (`build_town.py`, budget 70,000; aim for about 60,000)
Mostly soft with focus; its job is the skyline and the lit windows.
1. **Skyline silhouettes (about +4,000).** The far chimneys (now plain 16-sided cones with a slab cap)
   need corbelled caps (2 to 3 flared rings), a lathe profile with a base plinth (B7), and iron bands.
   The far works need sawtooth roofs with north-light glazing, not prisms. Add water towers and a
   church spire or two for scale.
2. **Terraces (about +12,000; shared mesh, so cost is per module).** Today the windows and doors are
   planes and boxes 3 mm proud of the wall. Cut real reveals (B8), add sash bars and a lintel and sill
   in stone, recess the doors with fanlights, give the chimney stacks oversailing courses and pots with
   rolled rims, and add a gable end with a parapet and kneelers. Bevel the walls (B1). Keep the rows
   as linked copies (this saves memory, and the export writes the mesh once).
3. **Viaduct (about +3,000).** Today it is piers under a slab with no arches. Cut real semicircular
   arches, add a string course and parapet copings, and put a short train or wagons on it for
   silhouette.
4. **Gasholder (about +2,500).** Lattice girders as crossed thin boxes between the columns (not just
   rings), and column caps.
5. **Ground (about +3,000).** The 70 x 60 cinder ground repeats its 2-unit tile visibly. Subdivide it,
   add vertex-colour macro variation (paths, puddles, darker by walls) (B14), and add a second street
   material. Put kerbs and gutters along every street.
6. **Near things (about +1,500).** The front wall needs coping stones and railings with spear heads
   (B5) and a gate pier. The crates need battens.
7. **Bake AO** for the terrace module only (it is shared, so one bake covers all copies). Today the
   town has no corner shading at all.

### C3. The reviewer's desk (`build_desk.py`, budget 20,000; aim for about 16,000)
Seen top-down in `r20-p8-b`, with the report in the middle. What shows first is the things around
the report.
1. **The reading glasses (about +800).** The lenses render as **solid white or grey discs**, which is
   the first thing that reads as wrong. Make thin dark-tinted lenses (`colour` about 0.05,
   `roughness` 0.05, `metallic` 0.0) that read as glass by reflection, with real wire rims (torus or
   B6 curve, r 0.006), a bridge arch and folded temples with hinges.
2. **The desk-top wood (0 to +200).** At this scale the grain reads as speckle or carpet. Use
   wider rings, planks about 0.6 wide with seams, the grain running along the long side (B11), a
   roughness map for polish and wear, and a moulded front edge (bevel `profile_type='CUSTOM'`, or
   two bevel segments with `profile=0.7`).
3. **The tea cup and saucer (about +1,500).** Lathe them (B7): a lip, a foot ring and a saucer well. Give
   the handle a real D-shaped loop (B6 curve with bevel). Add a tea surface with a lower roughness
   and a soft meniscus ring.
4. **The banker's lamp (about +1,500).** Give the shade thickness (B4) with an emissive white inside
   (`lamp-glow` stays on the bulb), brass end caps with a rolled edge, a stepped lathed base (B7), the
   arm as a curved tube, and a pull chain of small beads (B5 array).
5. **The folder stack and tape (about +1,500).** The red tape is a 0.2-tall solid block. Make it a
   0.003-thin band that follows the stack (B5 curve or bmesh), with a bow knot. Show page edges (thin
   offset sheets, 2 to 3 per folder) and bend the folder covers slightly.
6. **The pen, ink pad and papers (about +1,500).** A lathed pen with a nib and a clip. An ink tin with
   rolled rims and a hinged lid. Papers with a slight curl (a subdivided plane bent a few mm, B4
   thickness 0.002).
7. **The blotter (about +400).** Triangular leather corner pockets instead of end bars, and the tooled
   border as a normal-map groove.
8. **Bake AO** (already done) at reach 0.3, so that the cup, lamp and folders sit on the desk.

### C4. The loose props (`build_props.py`, budget 6,000; aim for about 5,000)
Out of focus in the foreground, so **silhouette is everything**.
1. **The cart (about +1,200).** The wheels are solid discs. Give them a rim (lathed), 8 to 10 spokes, a
   hub and an axle. Add a slatted bed with side rails and the handles as one bent piece with grips.
2. **The barrels (about +900).** Lathe them with a bulge (B7), add hoops as bevelled bands, and give the
   staves a normal or colour map (vertical lines). Recess the top head with a lip. Today they are
   straight cylinders.
3. **The lamp-post (about +800).** Today the lamp head is a white box. Make a 4-pane lantern with an iron
   frame, a pyramid roof with a finial, a ladder bar with ball ends, and a lathed fluted column base.
   Keep `lamp-post-light` and `lamp-glow`.
4. **Crates and sacks (about +800).** The crates need frame battens and corner boards, and stencil
   marks as texture. The sacks should be lumpy: subdivided boxes with random push-pull and a tied neck,
   smooth shaded.

---

## D. Traps (each one found or confirmed in this session)

1. **`read_factory_settings` is refused by the MCP sandbox.** Use
   `bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)`. `model_kit.reset()` uses the
   refused call. That is fine when the build scripts run in their own Python, but they fail if you run
   them through `execute_blender_code`. Patch `reset()` only in your own copy.
2. **Set CYCLES and CPU before any render or bake.** EEVEE needs a GPU here and takes Blender down.
   The MCP thumbnail tool "temporarily overrides settings", but `render_viewport_to_path` uses yours.
3. **The front is -y.** Blender -y becomes three.js +z (towards the camera). The town script converts
   with `at(x, z, y)`: keep using it.
4. **Bevel before the boolean breaks the cut.** Cut first, bevel second (B8). Booleans with faces on the
   same plane give holes: make cutters overshoot.
5. **Bevel without `harden_normals` on flat-shaded parts gives facets, not highlights.** Turn on smooth
   shading as well (B1). With shading smooth and no harden normals or weighted normals, big flat faces
   go blotchy instead.
6. **A geometry-nodes modifier must end in Realize Instances**, or applying it fails with "does not
   contain a mesh" (tested). `export_gn_mesh` is experimental: do not use it.
7. **One normal map and one AO map per material.** glTF allows a single `normalTexture`. A
   brick-tiling normal map (UV 0) and a baked bevel normal map (UV 1, unique) cannot both be on one
   material. Use baked bevel normals only on plain-colour parts, and use real bevels (B1) on textured
   ones. AO is on UV 1 (`shading`): every mesh in the material must have that layer (`finish()`
   already copies materials for skipped parts; keep that).
8. **Shared meshes.** The terraces are linked copies: an edit to one edits all of them. For AO on linked
   copies, bake once, because the copies cannot each have their own occlusion.
9. **Material names and markers are an interface.** Renaming `window-glow` or `chimney_top`, or
   joining away the `barrels` group, silently breaks the pages. After a rebuild, check with
   `get_objects_summary` and `grep` the page code (`model-loader.js`, `two-factories-set.js`, `page-8.js`).
10. **`modifiers.new(type='ARRAY')` is the legacy Array.** The new 5.x Array, Curve to Tube and
    Scatter modifiers are Essentials node-group assets and are not available from a bare script (B5).
11. **No `use_auto_smooth`** since Blender 4.1. Use `shade_auto_smooth`, the Smooth by Angle
    modifier, or `mesh.set_sharp_from_angle`.
12. **Vertex colours are all-or-nothing per material** in three.js. If one mesh has COLOR_0 and another
    with the same material does not, results differ (B14).
13. **Texture size cap is 1024**, and JPEG suits colour. Normal maps are JPEG today (q 94) to save
    size. That is acceptable under film grain, but **baked bevel-edge normals and AO should be PNG**,
    because JPEG blocks show up on smooth gradients.
14. **`box_map` uses `obj.location` and `obj.scale` but not rotation.** For rotated parts (copings
    on the slope, door leaves, the tape) brick and plank textures smear. Map before rotating (as
    the door leaves do) or map in local coordinates.
15. **Triangle counts.** Bevel segments multiply fast: a box goes from 12 to 44 triangles with 1
    segment and to 108 with 2 (measured). Use 2 or more segments only on parts in focus and larger
    than 0.1 units. Count with `mk.count_triangles()` (evaluated) and print it in `result`.
16. **Background `--command blender_mcp` sessions keep running.** Stop each with `kill PID` when done.
    Never use `pkill -f blender`, which can match your own shell's command line.
17. **Do not trust memory for API names.** Look them up with `get_python_api_docs`. Examples from this
    session: Instance on Points takes `Rotation` (a rotation socket; a vector is converted), the bake
    margin type is `margin_type='EXTEND'|'ADJACENT_FACES'` (the scene's `render.bake.margin_type` defaults to
    ADJACENT_FACES, while the operator's own argument defaults to EXTEND), and the Boolean solver
    enum is `'FLOAT'|'EXACT'|'MANIFOLD'` (not 'FAST').
