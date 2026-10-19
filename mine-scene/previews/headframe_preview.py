# What this does: builds ONLY the headframe (plus a plain stand-in box for the engine house, so the sloping ropes have a roof to
# land on) and takes quick preview photos of it from several viewpoints, saved in the "out" folder.
# Use:  blender -b --disable-autoexec -t 2 --python headframe_preview.py -- VIEW_NAME [VIEW_NAME ...]
# View names: reference (the standard tall camera), detail_top (wheels and deck), back_side, base_detail, all.
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, 'lib'))
sys.path.insert(0, os.path.join(WORK, 'modules'))
import bpy
import mine_common as mc
import headframe

views_asked = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['all']
if 'all' in views_asked:
    views_asked = ['reference', 'detail_top', 'back_side', 'base_detail']
extra_samples = 32
for item in list(views_asked):
    if item.startswith('samples='):
        extra_samples = int(item.split('=')[1])
        views_asked.remove(item)

mc.clear_scene()
mc.preview_stage()

# ---- stand-in engine house (NOT part of the headframe; only so the ropes have something to land on) ----
house = mc.LAYOUT['engine_house']
brick = mc.plain_material('stand-in brick', (0.30, 0.10, 0.06), roughness=0.9)
slate = mc.plain_material('stand-in slate', (0.07, 0.08, 0.10), roughness=0.6)
dark = mc.plain_material('stand-in doorway', (0.01, 0.01, 0.01), roughness=1.0)
stand_in = mc.MeshBuilder('Stand-in engine house', [brick, slate, dark])
x0, x1, y0, y1 = house['x_left'], house['x_right'], house['y_front'], house['y_back']
wall, ridge = house['wall_height'], house['ridge_height']
stand_in.add_box(((x0 + x1) / 2, (y0 + y1) / 2, wall / 2), (x1 - x0, y1 - y0, wall), slot=0)
# roof as two sloping quads plus two triangular gables
stand_in.add_polygon([(x0 - 0.35, y0 - 0.3, wall - 0.3), (0, y0 - 0.3, ridge), (0, y1 + 0.3, ridge), (x0 - 0.35, y1 + 0.3, wall - 0.3)][::-1], slot=1)
stand_in.add_polygon([(x1 + 0.35, y0 - 0.3, wall - 0.3), (x1 + 0.35, y1 + 0.3, wall - 0.3), (0, y1 + 0.3, ridge), (0, y0 - 0.3, ridge)][::-1], slot=1)
stand_in.add_polygon([(x0, y0 - 0.02, wall), (x1, y0 - 0.02, wall), (0, y0 - 0.02, ridge)], slot=0)
stand_in.add_polygon([(-1.7, y0 - 0.03, 0.01), (1.7, y0 - 0.03, 0.01), (1.7, y0 - 0.03, 4.0), (-1.7, y0 - 0.03, 4.0)], slot=2)
stand_in.finish('Stand-in')
# a stand-in pair of rails, so we can see the headframe really leaves the track clear
rail_material = mc.plain_material('stand-in rail', (0.12, 0.10, 0.09), roughness=0.5, metallic=0.5)
rails = mc.MeshBuilder('Stand-in rails', [rail_material])
for k in range(0, 40):
    t0, t1 = k / 40.0, (k + 1) / 40.0
    (ax, ay), (bx, by) = mc.track_point(t0), mc.track_point(t1)
    for side in (-0.55, 0.55):
        rails.add_beam((ax + side, ay, 0.16), (bx + side, by, 0.16), 0.07, 0.1, slot=0)
rails.finish('Stand-in')

started = time.time()
build_started = time.time()
result = headframe.build('Headframe')
build_seconds = time.time() - build_started
mc.say(f'build() returned {result["objects"]}')
mc.say(result['notes'])

views = {
    'reference': dict(location=(-9.5, -21, 1.7), target=(1, 2, 5.5), lens=28, size=(540, 960)),
    'detail_top': dict(location=(-6.0, -13.0, 12.5), target=(0.3, -3.4, 16.0), lens=42, size=(900, 800)),
    'back_side': dict(location=(13.5, 9.0, 7.5), target=(0.0, -2.5, 8.5), lens=24, size=(720, 900)),
    'base_detail': dict(location=(-6.5, -11.5, 2.2), target=(1.0, -3.4, 3.0), lens=30, size=(900, 800)),
    'reference_full': dict(location=(-9.5, -21, 1.7), target=(1, 2, 9.0), lens=24, size=(540, 960)),
    'rope_vbrace': dict(location=(-2.5, -9.5, 3.4), target=(1.55, -5.7, 3.6), lens=50, size=(900, 700)),
    'platform': dict(location=(-4.5, -9.5, 7.8), target=(1.0, -4.0, 7.2), lens=32, size=(900, 700)),
    'deck_close': dict(location=(-4.8, -7.5, 15.4), target=(0.6, -3.4, 15.4), lens=40, size=(900, 700)),
    'above': dict(location=(0.5, -8.0, 30.0), target=(0.0, -3.4, 13.5), lens=50, size=(900, 700)),
    'front_straight': dict(location=(0.0, -26.0, 8.0), target=(0.0, -3.4, 8.0), lens=35, size=(720, 900)),
}
for name in views_asked:
    spec = views[name]
    for obj in list(bpy.data.objects):
        if obj.type == 'CAMERA':
            bpy.data.objects.remove(obj)
    path = os.path.join(WORK, 'out', f'headframe_{name}.png')
    t = time.time()
    mc.render_preview(path, spec['location'], spec['target'], lens=spec['lens'], size=spec['size'], samples=extra_samples)
    mc.say(f'{name} rendered in {time.time() - t:.0f} s -> {path}')

# triangle count and object count for the report
total_triangles = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.name.startswith('Headframe'):
        mesh = obj.data
        mesh.calc_loop_triangles()
        total_triangles += len(mesh.loop_triangles)
mc.say(f'headframe triangles: {total_triangles}, build time (with previews) {time.time() - started:.0f} s')

import json
headframe_objects = [o for o in bpy.data.objects if o.name.startswith('Headframe')]
report = {
    'object_count': len(headframe_objects),
    'triangle_count': total_triangles,
    'uses_real_displacement': [],
    'build_seconds': round(build_seconds, 2),
    'known_flaws': [
        'The two hanging ropes drop from the FRONT TANGENT of the wheels, so they land at y = centre_y - 2.335 (about -5.73), not exactly at y = centre_y; the timber landing is centred under them.',
        'The back ropes end on small steel posts standing on the roof slope at x = +-1.55, y = 6 (rope end at 7.65 m); the roof height there is taken from mc.LAYOUT (6.41 m), so the posts only seat exactly if the engine-house roof follows the plan.',
        'The top deck is wider than the plan (deck 4.4 x 3.2 m, wheel pits between girders) so the wheels have somewhere to dip; legs still end at the planned 3.0 x 2.5 m top.',
        'No real displacement on the steel (normal map only); footing stone is a procedural noise material, not a supplied picture.',
        'The track curve passes x = 0.6 to 1.4 at the headframe front (y -5 to -6.7), so its right rail runs right where the right rope lands; the landing is flat and 0.10 m high so rails can cross it.',
        'Previews were lit by the neutral test sun, so the dusk look and exact tint of the steel are not judged yet.',
        'The ladder has no safety cage, ropes do not sag, and the wheel spokes are plain tapered timbers with iron shoes and bands, not carved.',
    ],
}
with open(os.path.join(WORK, 'out', 'headframe_report.json'), 'w') as handle:
    json.dump(report, handle, indent=2)
mc.say('report written')
