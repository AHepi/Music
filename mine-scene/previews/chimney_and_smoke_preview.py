# What this does: takes quick preview photos of the chimney and its smoke on their own (with grey stand-in shapes for the
# engine house and the headframe wheels, only so you can judge where the smoke goes), and writes out/chimney_and_smoke_report.json.
# Photos: the standard tall camera, a close view of the stone base and flue opening, a close view of the top of the chimney,
# a close wall view with low light (to check the real brick bumps), a back/right view, and a side view of the whole smoke plume.
# Use: blender -b --disable-autoexec -t 2 --python chimney_and_smoke_preview.py -- [view names ...]
#      view names: standard base top wall back plume stub corner mouth   (default: all of them)
import json
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
sys.path.insert(0, os.path.join(ROOT, 'modules'))
import mine_common as mc  # noqa: E402
import chimney_and_smoke  # noqa: E402

OUT = os.path.join(ROOT, 'out')
wanted = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not wanted:
    wanted = ['standard', 'base', 'top', 'wall', 'back', 'plume']

mc.clear_scene()
mc.preview_stage()
for light in list(bpy.data.objects):
    if light.type == 'LIGHT':
        bpy.data.objects.remove(light)
mc.set_sun(30, 25, strength=3.4, colour=(1.0, 0.86, 0.68), name='Preview key sun')          # from the front-left
mc.set_sun(12, 200, strength=1.2, colour=(1.0, 0.55, 0.30), name='Preview low back sun')    # warm dusk glow from behind
mc.set_flat_world((0.16, 0.25, 0.29), 0.9)

# grey stand-ins, only for judging the smoke and the surroundings (not part of the real parts)
stand_in = mc.plain_material('Stand-in grey', (0.30, 0.28, 0.26), roughness=0.9)
builder = mc.MeshBuilder('Stand-in engine house and wheels', [stand_in])
house = mc.LAYOUT['engine_house']
builder.add_box(((house['x_left'] + house['x_right']) / 2, (house['y_front'] + house['y_back']) / 2, house['wall_height'] / 2),
                (house['x_right'] - house['x_left'], house['y_back'] - house['y_front'], house['wall_height']), slot=0)
builder.add_box((0, 5.5, house['wall_height'] + 1.5), (7.8, 11.0, 3.0), slot=0)
frame = mc.LAYOUT['headframe']
for wheel_x in (-frame['wheel_spacing_x'] / 2, frame['wheel_spacing_x'] / 2):
    builder.add_ring((wheel_x, frame['centre_y'], frame['wheel_centre_height']), (1, 0, 0), frame['wheel_radius'], frame['wheel_radius'] - 0.25, 0.3, sides=40, slot=0)
for dx in (-frame['base_half_x'], frame['base_half_x']):
    for dy in (-frame['base_half_y'], frame['base_half_y']):
        builder.add_beam((dx, frame['centre_y'] + dy, 0), (dx * 0.5, frame['centre_y'] + dy * 0.5, frame['top_deck_height']), 0.35, 0.35, slot=0)
builder.finish('Stand-ins')

start = time.time()
result = chimney_and_smoke.build('Mine')
build_seconds = round(time.time() - start, 2)
print(result['notes'])

# ---- report ----
triangles = 0
for name in result['objects']:
    mesh = bpy.data.objects[name].data
    triangles += sum(len(p.vertices) - 2 for p in mesh.polygons)
report = {
    'object_count': len(result['objects']),
    'triangle_count': triangles,
    'uses_real_displacement': ['Chimney brick shaft (four tall faces, brick height map, adaptive, 2 px)'],
    'build_seconds': build_seconds,
    'known_flaws': [
        'The smoke is smooth-shaded lumps (about 500 blobs, 160k triangles with the chimney): it reads as soft cauliflower-like painted clumps, not wispy or textured; the far puffs are still rather round.',
        'Smoke greys (linear 0.035 charcoal to 0.27 mid grey) were judged only under the neutral preview sun; they may need to be scaled once the dusk lighting exists.',
        'In the standard tall camera the plume crosses BEHIND the headframe wheels on screen and runs off the top and right edges; in space it never touches them (smallest gap 8 m, plume 12 m further back and 6 m above the wheel tops).',
        'Only the four big shaft faces have real displacement; the corbel, flue stub and stone are normal-map or plain materials. The four faces are separate quads, so brick joints do not interlock round the corners (no cracks seen in close views).',
        'The stone plinth is a plain procedural stone material (not a supplied picture); the flue opening is rectangular with a flat lintel, not arched; the soot stain above it is a see-through sheet 3 cm off the wall, not painted into the brick.',
        'The flue stub sinks 8 cm into the engine-house left wall at x = -3.9 and sits at y 6.45 to 7.55: it depends on that wall being where the plan says.',
        'Previews use grey stand-ins for the engine house and headframe; nothing was checked against the real parts or the real dusk light.',
    ],
    'objects': result['objects'],
    'notes': result['notes'],
}
with open(os.path.join(OUT, 'chimney_and_smoke_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)

views = {
    # name: (camera location, target, lens, size)
    'standard': ((-9.5, -21.0, 1.7), (1.0, 2.0, 5.5), 28, (506, 900)),
    'base': ((-9.0, 0.6, 1.9), (-5.6, 6.3, 1.4), 30, (700, 800)),
    'top': ((-12.0, -4.0, 9.0), (-6.0, 7.0, 15.5), 70, (700, 900)),
    'wall': ((-8.0, 3.2, 3.6), (-6.0, 6.0, 4.4), 40, (800, 800)),
    'back': ((9.0, 22.0, 6.0), (-4.5, 8.0, 12.0), 26, (600, 900)),
    'plume': ((2.0, -45.0, 20.0), (4.0, 8.0, 22.0), 32, (900, 560)),
    'stub': ((-4.5, -1.5, 2.4), (-4.9, 7.0, 0.9), 35, (700, 700)),
    'corner': ((-7.6, 2.6, 2.0), (-6.4, 6.2, 1.8), 45, (800, 800)),
    'mouth': ((-9.0, 1.0, 24.0), (-6.0, 7.0, 17.0), 40, (800, 700)),     # smoke hidden for this one
}
# the wall view uses a very low sun so brick bumps show up
for name in wanted:
    location, target, lens, size = views[name]
    for camera in [o for o in bpy.data.objects if o.type == 'CAMERA']:
        bpy.data.objects.remove(camera)
    bpy.data.objects['Chimney smoke'].hide_render = (name == 'mouth')
    mc.render_preview(os.path.join(OUT, f'chimney_and_smoke_{name}.png'), location, target, lens=lens, size=size, samples=36)
    print('rendered', name, flush=True)
