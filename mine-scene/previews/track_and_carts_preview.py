# What this does: builds only the track, carts and coal heaps (modules/track_and_carts.py) on a stand-in muddy ground and takes
# preview photos from several angles, then writes out/track_and_carts_report.json.
# Use: blender -b --disable-autoexec -t 2 --python track_and_carts_preview.py -- VIEW [VIEW ...]
#   VIEW is one of: standard (the finished-look camera), wide, topdown, cart_close, rail_close, back_side, heaps, tipped, all
#   Add "fast" to render with fewer samples and smaller pictures.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WORK, 'lib'))
sys.path.insert(0, os.path.join(WORK, 'modules'))

import bpy
import numpy as np
import mine_common as mc
import track_and_carts

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['standard']
fast = 'fast' in arguments
views_wanted = [a for a in arguments if a != 'fast']

# (camera position, looks at, lens, picture size)
VIEWS = {
    'standard': ((-9.5, -21.0, 1.7), (1.0, 2.0, 5.5), 28, (506, 900)),
    'wide': ((-9.5, -21.0, 3.0), (8.0, -10.0, 0.5), 22, (900, 700)),
    'topdown': ((6.0, -9.0, 34.0), (6.0, -8.5, 0.0), 40, (900, 700)),
    'cart_close': ((-3.6, -11.8, 1.5), (1.7, -7.2, 0.7), 34, (900, 700)),
    'cart_end': ((3.6, -11.6, 1.2), (1.7, -7.2, 0.8), 40, (900, 700)),
    'doorway': ((0.0, -1.5, 1.3), (0.0, 4.0, 0.3), 30, (900, 600)),
    'cart2_back': ((6.8, -6.4, 1.5), (3.3, -10.3, 0.9), 40, (900, 700)),
    'cart2_end': ((4.9, -14.3, 1.1), (3.3, -10.3, 0.8), 45, (900, 700)),
    'cracks': ((1.2, -4.0, 3.6), (0.9, -5.6, 0.0), 35, (900, 600)),
    'cart2_far': ((8.6, -6.0, 2.3), (3.4, -10.2, 1.0), 42, (900, 700)),
    'cart1_far': ((7.6, -2.0, 2.4), (1.7, -7.0, 1.0), 42, (900, 700)),
    'sleepers': ((-1.4, -6.6, 0.9), (0.3, -3.6, 0.12), 38, (900, 600)),
    'rail_close': ((-0.8, -9.8, 0.75), (4.2, -11.2, 0.15), 40, (900, 600)),
    'back_side': ((12.0, -2.5, 2.6), (3.5, -9.5, 0.5), 30, (900, 700)),
    'heaps': ((3.0, -20.0, 2.4), (10.5, -12.0, 0.8), 32, (900, 700)),
    'tipped': ((-8.6, -17.0, 1.7), (-5.4, -8.2, 0.6), 34, (900, 700)),
}
if 'all' in views_wanted:
    views_wanted = list(VIEWS)

mc.clear_scene()
mc.preview_stage()
bpy.data.objects.remove(bpy.data.objects['Preview floor'])

# stand-in ground that follows mc.ground_height, so the track can be judged seated on the yard
ground_builder = mc.MeshBuilder('Preview ground', [mc.surface_material('mud', variation=0.2, splash=0.0)])
xs = np.arange(-30.0, 40.1, 1.0)
ys = np.arange(-35.0, 15.1, 1.0)
vertices = np.array([(x, y, mc.ground_height(x, y)) for y in ys for x in xs])
faces = []
for j in range(len(ys) - 1):
    for i in range(len(xs) - 1):
        a = j * len(xs) + i
        faces.append([a, a + 1, a + len(xs) + 1, a + len(xs)])
ground_builder.add_indexed_faces(vertices, faces, slot=0, uv_axes=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
ground_builder.finish('Preview')

result = track_and_carts.build('Mine')
print('[track_and_carts]', result['notes'], flush=True)

out_folder = os.path.join(WORK, 'out')
os.makedirs(out_folder, exist_ok=True)
for name in views_wanted:
    location, target, lens, size = VIEWS[name]
    if fast:
        size = (size[0] // 2, size[1] // 2)
    for old in [o for o in bpy.data.objects if o.type == 'CAMERA']:
        bpy.data.objects.remove(old)
    path = os.path.join(out_folder, 'track_and_carts_%s.png' % name)
    mc.render_preview(path, location, target, lens=lens, size=size, samples=16 if fast else 36)
    print('[track_and_carts] wrote', path, flush=True)

mine_objects = [bpy.data.objects[n] for n in result['objects']]

# how closely the rails follow the yard ground (the centre line is smoothed so the rails never zig-zag)
path = track_and_carts.TrackPath()
sample_s = np.arange(path.start_s, path.length, 0.25)
ground_under_track = np.array([mc.ground_height(*path.centre_xy(s)) for s in sample_s])
rail_base_heights = np.array([path.rail_base_height(s) for s in sample_s]) - track_and_carts.RAIL_BASE_ABOVE_GROUND
largest_difference = float(np.abs(ground_under_track - rail_base_heights).max())
largest_step = float(np.abs(np.diff(rail_base_heights)).max())

KNOWN_FLAWS = [
    'In the standard camera frame (-9.5,-21,1.7 -> 1,2,5.5, lens 28, 9:16) only the cart on the track (right third) and the tipped cart (lower left) can be seen; '
    'the second cart (about 4.3 m further along the curve), both coal heaps (x 6..14) and the track beyond about y=-9 lie outside the right edge of that frame. '
    'They sit where the layout puts them; a wider or shifted camera is needed to show them.',
    'Beside the headframe front-right leg (track distance about 7.3 to 8.9 m from the doorway, y about -6.3 to -7.4) the stone bed is pulled in and the sleeper ends are shortened, '
    'because the track centre line passes only about 1.7 m from that footing centre. I assumed the footing is at most 0.4 m half-size (kept 0.65 m clear). A bigger footing would touch the track.',
    'Rails inside the doorway (y 1 to 4) sit at mc.ground_height (0 m). If the engine house builds a raised floor or a sill there, the rails and stone bed will need to be lifted or trimmed to match.',
    'The tipped cart rests on its wheels and rim as a plausible pose, not a physics result; from the front (the standard camera side) its wheels are hidden behind the body, so it reads as an overturned open box with rim, rivets and coupling.',
    'Coal and loose stones are flat-shaded convex lumps in plain materials; up close their faces look a little CG-sharp and the bright highlights can glint. There is no coal dust or rust staining on the ground around the heaps.',
    'Rails are 1.45 times a real mine rail and the carts are large (1.9 m long, about 1.6 m tall with coal) so everything reads from far away; this is a stylised choice and the gauge follows the layout (1.1 m).',
    'Metal walls of the carts show an enlarged (about 2.4 times) plain rusty patch of the metal picture on purpose, so the rivet rows of the picture do not double up with the modelled rivets; rivets are modelled six-sided and small.',
    'Wheels are 28-sided; spokes, hubs and back discs use plain dark cast-iron colour, only tread and flange use the rusty metal picture.',
    'Real displacement (stone bed, sleepers) makes renders slower: a 900 px preview at 36 samples took about 1 to 2 minutes with -t 2. Sleeper boxes have separate corners, so no cracks showed at the edges in the previews but extreme close-ups were not checked.',
    'Previews were taken on a stand-in ground with neutral light, not in the final dusk lighting or with the other parts. The track ends abruptly at t=1 (no buffer stop or tapering).',
]
report = {
    'object_count': len(mine_objects),
    'triangle_count': result['triangle_count'],
    'uses_real_displacement': [o.name for o in mine_objects if any(m.type == 'SUBSURF' for m in o.modifiers)],
    'build_seconds': round(result['build_seconds'], 1),
    'objects': result['objects'],
    'largest_difference_between_rail_foot_height_and_ground_under_centre_line_m': round(largest_difference, 3),
    'largest_height_step_between_neighbouring_rail_samples_m': round(largest_step, 4),
    'known_flaws': KNOWN_FLAWS,
}
with open(os.path.join(out_folder, 'track_and_carts_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('[track_and_carts] report written', flush=True)
