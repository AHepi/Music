# What this does: four small Workbench pictures (flat colour, outlines, no real lighting) of the spots the delivery check flagged, drawn on an in-memory copy
#   (saves only PNGs): (1) bridge seen from the side, (2) veranda step seen from the side, (3) lantern from the front with its parts in different colours,
#   (4) the wall cap seen from low down, like a viewer sitting on the veranda. Nothing is saved to any .blend.
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup FILE.blend -P audit_closeups.py -- OUT_FOLDER
import bpy, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'OBJECT'; sh.show_object_outline = True; sh.object_outline_color = (0, 0, 0); sh.show_cavity = False; sh.show_shadows = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0
sc.world.use_nodes = False; sc.world.color = (0.80, 0.90, 1.0)
sc.render.resolution_x, sc.render.resolution_y = 640, 427
cam = sc.camera; cd = cam.data; cd.dof.use_dof = False
all_objs = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE')]
def show_only(prefixes):
    for o in all_objs:
        o.hide_render = not any(o.name.startswith(p) for p in prefixes)
def colour(prefix_colour):
    for o in all_objs:
        o.color = (0.75, 0.75, 0.75, 1)
    for pre, c in prefix_colour:
        for o in all_objs:
            if o.name.startswith(pre): o.color = (*c, 1)
def aim(loc, target, ortho=None, lens=35):
    cam.location = loc; cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.type = 'PERSP'; cd.lens = lens
def shot(name): sc.render.filepath = f'{out}/{name}.png'; bpy.ops.render.render(write_still=True)

# 1 bridge from the side: only piers and bridge planks
show_only(('Bridge pier', 'Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007', 'Pond water'))
colour([('Bridge pier', (0.25, 0.45, 0.9)), ('Astra / varied planks', (0.9, 0.55, 0.25)), ('Pond water', (0.2, 0.7, 0.8))])
aim((-3.9, -8.0, 0.08), (-3.9, 0.0, 0.08), ortho=1.7); shot('p1_bridge_side')

# 2 veranda step from the side, with the ground
show_only(('Veranda step', 'Stone plinth', 'Astra / varied planks'))
# a thin stand-in for the ground (the real ground is at z = 0.00 under both steps, measured by ray)
bpy.ops.mesh.primitive_cube_add(size=1, location=(3.0, 4.25, -0.03)); gp = bpy.context.object; gp.scale = (6.0, 3.0, 0.06); gp.name = 'GROUND_STANDIN'; all_objs.append(gp)
for o in all_objs:
    if o.name.startswith('Astra / varied planks.00') and o.name[-1] in '34567': o.hide_render = True
colour([('Veranda step, lower', (0.9, 0.3, 0.3)), ('Veranda step', (0.9, 0.8, 0.2)), ('Stone plinth', (0.55, 0.55, 0.6)), ('Astra / varied planks', (0.9, 0.55, 0.25)), ('GROUND_STANDIN', (0.3, 0.6, 0.3))])
aim((12.0, 4.25, 0.3), (2.2, 4.25, 0.3), ortho=1.9); shot('p2_step_side')

# 3 lantern from the front, parts in different colours, the glow box in red
show_only(('Lantern',))
colour([('Lantern base', (0.4, 0.5, 0.9)), ('Lantern post', (0.4, 0.8, 0.4)), ('Lantern gallery', (0.9, 0.85, 0.3)), ('Lantern firebox', (0.7, 0.7, 0.7)), ('Lantern cap', (0.7, 0.4, 0.8)), ('Lantern finial', (0.3, 0.3, 0.3)), ('Lantern window glow', (1.0, 0.15, 0.05))])
aim((0.95, -6.0, 1.0), (0.95, 1.1, 1.0), ortho=3.3); shot('p3_lantern_front')

# 4 wall cap from low down (like sitting on the veranda), the cap in dark red
show_only(('Back wall', 'Right wall'))
colour([('Back wall, right cap', (0.7, 0.15, 0.15)), ('Back wall, left cap', (0.7, 0.15, 0.15)), ('Right wall behind hall cap', (0.7, 0.15, 0.15)), ('Back wall', (0.85, 0.82, 0.7)), ('Right wall', (0.85, 0.82, 0.7))])
for o in all_objs:
    if o.name.endswith(' cap'): o.color = (0.7, 0.15, 0.15, 1)
aim((8.2, 6.4, 1.85), (8.2, 10.5, 2.2), lens=60); shot('p4_wallcap_low')
print('CLOSEUPS_DONE')
