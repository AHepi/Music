# What this does: a flat "which group is this pixel" picture of the courtyard seen from the photo camera (Workbench, 960x640, no lighting), so the share of the
#   frame taken by each group (maple, rocks, ground, gravel, hills, sky ...) can be counted. Works on the opened copy in memory; saves one small PNG, no .blend.
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup FILE.blend -P id_map.py -- OUT.png
import bpy, sys
sc = bpy.context.scene
GROUPS = [  # (name, rgb, prefixes)
    ('maple', (1, 0, 0), ('Maple',)),
    ('pine', (0, 0.6, 0), ('Pine',)),
    ('rocks', (0.5, 0.5, 0.5), ('Rock', 'Pond edge stone', 'Gravel rock', 'Stepping stone', 'Veranda step', 'Water basin')),
    ('lantern', (1, 1, 0), ('Lantern',)),
    ('bridge', (0.6, 0.3, 0), ('Bridge pier', 'Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007')),
    ('veranda deck', (0.4, 0.2, 0.1), ('Astra / varied planks',)),
    ('ground (moss/earth)', (0, 0.3, 0), ('Astra / Courtyard receiving ground', 'Astra / moss', 'Astra / pebbles')),
    ('raked gravel', (0.9, 0.7, 0.5), ('Raked gravel',)),
    ('water + lily pads', (0, 0, 1), ('Pond water', 'Lily pads', 'Lotus', 'Basin water')),
    ('roof', (0.2, 0.2, 0.2), ('Hall roof',)),
    ('hall (posts, screens, plaster)', (1, 0.5, 0), ('Hall', 'Shoji', 'Open room', 'Eave soffit', 'Stone plinth')),
    ('garden walls', (0.9, 0.9, 0.9), ('Back wall', 'Right wall')),
    ('bamboo (fence, stalks, leaves)', (0.6, 1, 0.2), ('Bamboo',)),
    ('hills (3 ridges)', (0.5, 0, 0.5), ('Hills,',)),
    ('dark plain far back', (0.1, 0.1, 0.1), ('Dark plain',)),
    ('fallen leaves', (1, 0.5, 0.5), ('Fallen leaves',)),
]
for o in bpy.data.objects:
    if o.type not in ('MESH', 'CURVE') or o.hide_render: continue
    for name, rgb, pre in GROUPS:
        if any(o.name.startswith(p) for p in pre):
            o.color = (*rgb, 1); break
    else:
        o.color = (1, 0, 1, 1); print('UNGROUPED', o.name)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_object_outline = False; sh.show_shadows = False; sh.show_cavity = False
sc.display.render_aa = 'OFF'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0
sc.world.use_nodes = False; sc.world.color = (0, 0, 0)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 640, 100
sc.render.filepath = sys.argv[sys.argv.index('--') + 1]
bpy.ops.render.render(write_still=True)
print('IDMAP_DONE')
