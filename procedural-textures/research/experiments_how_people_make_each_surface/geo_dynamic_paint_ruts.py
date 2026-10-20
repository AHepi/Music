# What this does: TEST of the "wheel leaves ruts through Dynamic Paint" way of making mud tracks that tutorials describe (Dikko's tracks tutorial, Sardi Pax's wet tyre
# tracks, Lester Banks posts): a finely divided plane is a Dynamic Paint CANVAS of type Displace, a cylinder 'wheel' is a BRUSH that rolls across it, the
# simulation is baked, and the canvas then holds the grooves. The result is photographed from straight above as height.
# It reports whether this works headless in Blender 5.2.2, how long it takes, and what the groove looks like. Not seamless (one track, ends inside the tile).
# Run: blender -b --disable-autoexec -t 2 --python geo_dynamic_paint_ruts.py -- OUT_FOLDER [--size 512] [--grid 220]
import json
import math
import os
import sys
import time

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_helpers as gh  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
size = int(args[args.index('--size') + 1]) if '--size' in args else 512
grid = int(args[args.index('--grid') + 1]) if '--grid' in args else 220
os.makedirs(out, exist_ok=True)
scene = gh.new_overhead_scene(size)
scene.frame_start, scene.frame_end = 1, 50
log = {}

bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=grid, y_segments=grid, size=0.5)
bmesh.ops.translate(bm, vec=(0.5, 0.5, 0.0), verts=bm.verts)
mesh = bpy.data.meshes.new('canvas')
bm.to_mesh(mesh)
bm.free()
canvas = bpy.data.objects.new('canvas', mesh)
scene.collection.objects.link(canvas)
bpy.context.view_layer.objects.active = canvas
canvas.select_set(True)
bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
canvas_modifier = canvas.modifiers[-1]
bpy.ops.dpaint.type_toggle(type='CANVAS')          # the same as the 'Canvas' button in the Physics tab
log['canvas_settings_after_toggle'] = canvas_modifier.canvas_settings is not None
surfaces = canvas_modifier.canvas_settings.canvas_surfaces
log['surfaces_after_setup'] = len(surfaces)
surface = surfaces[0]
log['surface_types_before'] = [x.surface_type for x in surfaces]
surface.surface_type = 'DISPLACE'
surface.displace_factor = 0.05
surface.use_incremental_displace = False
surface.displace_type = 'DISPLACE'
surface.depth_clamp = 1.0
surface.use_dissolve = False
surface.surface_format = 'VERTEX'
surface.frame_start, surface.frame_end = 1, 50
log['surface_properties'] = [p.identifier for p in surface.bl_rna.properties if 'disp' in p.identifier or 'wave' in p.identifier or 'depth' in p.identifier or 'dissolve' in p.identifier or 'output' in p.identifier]
for name, value in (('use_dissolve', False),):
    try:
        setattr(surface, name, value)
    except Exception as error:
        log['set_' + name] = str(error)
canvas.select_set(False)

# the wheel: a cylinder whose axis points along y, rolling along +x, its lowest point 0.012 below the canvas
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.07, location=(-0.1, 0.5, 0.048))
wheel = bpy.context.active_object
wheel.rotation_euler = (math.pi / 2, 0, 0)
bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
brush_modifier = wheel.modifiers[-1]
bpy.ops.dpaint.type_toggle(type='BRUSH')
try:
    brush_modifier.ui_type = 'BRUSH'
except Exception as error:
    log['ui_type_error'] = str(error)
log['brush_settings_exists'] = brush_modifier.brush_settings is not None
log['canvas_settings_on_wheel'] = brush_modifier.canvas_settings is not None
brush = brush_modifier.brush_settings
log['brush_properties'] = [p.identifier for p in brush.bl_rna.properties][:40]
brush.paint_source = 'VOLUME'
brush.paint_alpha = 1.0
brush.use_absolute_alpha = False
log['brush_paint_source'] = brush.paint_source
log['brush_modifier_type'] = brush_modifier.ui_type if hasattr(brush_modifier, 'ui_type') else None
for frame, x in ((1, -0.1), (50, 1.1)):
    wheel.location.x = x
    wheel.keyframe_insert('location', frame=frame)
wheel.hide_render = True

start = time.time()
zs_by_frame = {}
for frame in range(1, 51):
    scene.frame_set(frame)
    if frame in (10, 25, 50):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = canvas.evaluated_get(dg)
        m = ev.to_mesh()
        zs_by_frame[frame] = (round(min(v.co.z for v in m.vertices), 5), round(max(v.co.z for v in m.vertices), 5))
        ev.to_mesh_clear()
log['z_range_by_frame'] = zs_by_frame
log['canvas_modifiers'] = [(m.name, m.type, m.show_viewport) for m in canvas.modifiers]
log['wheel_x_at_frame_50'] = wheel.matrix_world.translation.x
log['surface_type_now'] = surface.surface_type
log['point_cache_frames'] = (surface.point_cache.frame_start, surface.point_cache.frame_end, surface.point_cache.is_baked)
log['seconds'] = round(time.time() - start, 1)
scene.frame_set(50)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = canvas.evaluated_get(depsgraph)
eval_mesh = evaluated.to_mesh()
zs = [v.co.z for v in eval_mesh.vertices]
log['canvas_vertex_z_min'] = min(zs)
log['canvas_vertex_z_max'] = max(zs)
log['vertices'] = len(zs)
evaluated.to_mesh_clear()
gh.set_material(canvas, gh.height_material(-0.05, 0.01))
gh.render_picture(scene, os.path.join(out, 'height.png'), True, True)
json.dump(log, open(os.path.join(out, 'facts.json'), 'w'), indent=1, default=str)
print('FACTS', json.dumps(log, default=str)[:1500])
