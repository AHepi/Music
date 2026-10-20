# What this does: draws "what does this setting do?" strips for the brick wall recipe (small 384 px pictures): Bevel offset, Subdivision level, layout Width jitter, layout Row shift
# randomness, colour with Ambient Occlusion strength 0 / 0.5 / 1, and edge wear off / on. Each strip is a folder of little pictures + sweep.json; join them with
# lib/make_strip.py (the shell lines at the end of this file's note do that).
# Run: blender -b --disable-autoexec -t 2 --python fig_settings_strips.py ; then  for d in out/strips/*/; do python3 -I ../../lib/make_strip.py $d out/strips/$(basename $d).png; done
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import gn_tools as gt  # noqa: E402
import recipe_brick_layout as rb  # noqa: E402

SIZE = 384
ROOT = os.path.join(HERE, 'out', 'strips')


def strip(name, variants, channel, **photo):
    """variants: list of (label, parameter overrides). channel: 'normal_geometry' | 'colour' | 'height'."""
    folder = os.path.join(ROOT, name)
    os.makedirs(folder, exist_ok=True)
    files, labels = [], []
    for index, (label, overrides) in enumerate(variants):
        gt.new_scene(SIZE)
        params = {**rb.DEFAULTS, 'subdiv': 2, **overrides}
        tree = rb.build_wall_group(params)
        obj, _ = gt.add_geometry_object('wall', tree)
        scene = bpy.context.scene
        low, high, _ = gt.z_range(obj)
        path = os.path.join(folder, f'tile_{index:02d}.png')
        if channel == 'normal_geometry':
            gt.render_with(scene, obj, gt.normal_material(), path, True, False, samples=8)
        elif channel == 'height':
            gt.render_with(scene, obj, gt.height_material(low, high), path, True, False)
        else:
            gt.render_with(scene, obj, gt.colour_material('piece_colour', **photo), path, False, False, samples=16)
        files.append(os.path.basename(path))
        labels.append(label)
    with open(os.path.join(folder, 'sweep.json'), 'w') as handle:
        json.dump({'files': files, 'labels': labels}, handle)


strip('bevel_offset_normals', [('bevel 0.0003', {'bevel': 0.0003}), ('bevel 0.0035', {'bevel': 0.0035}), ('bevel 0.008', {'bevel': 0.008})], 'normal_geometry')
strip('subdivide_level_normals', [('subdivide 0', {'subdiv': 0}), ('subdivide 2', {'subdiv': 2}), ('subdivide 4', {'subdiv': 4})], 'normal_geometry')
strip('width_jitter_colour', [('width jitter 0', {'width_jitter': 0.0}), ('width jitter 0.2', {'width_jitter': 0.2}), ('width jitter 0.5', {'width_jitter': 0.5})], 'colour')
strip('row_shift_colour', [('row shift random 0 (plain bond)', {'row_shift': 0.0}), ('row shift random 0.8', {'row_shift': 0.8}), ('row shift random 1.0', {'row_shift': 1.0})], 'colour')
# AO and edge wear need different colour settings, so render them separately
for name, settings in (('ambient_occlusion_colour', [('no AO', dict(ambient_occlusion=0.0)), ('AO 0.5', dict(ambient_occlusion=0.5, occlusion_distance=0.03)), ('AO 1.0', dict(ambient_occlusion=1.0, occlusion_distance=0.03))]),
                       ('edge_wear_colour', [('no wear', dict(ambient_occlusion=0.8, occlusion_distance=0.03)), ('edge wear 0.5', dict(ambient_occlusion=0.8, occlusion_distance=0.03, edge_wear=0.5, edge_colour=(0.45, 0.4, 0.34, 1.0))),
                                             ('edge wear 1.0', dict(ambient_occlusion=0.8, occlusion_distance=0.03, edge_wear=1.0, edge_colour=(0.45, 0.4, 0.34, 1.0)))])):
    folder = os.path.join(ROOT, name)
    os.makedirs(folder, exist_ok=True)
    files, labels = [], []
    for index, (label, photo) in enumerate(settings):
        gt.new_scene(SIZE)
        tree = rb.build_wall_group({**rb.DEFAULTS, 'subdiv': 3})
        obj, _ = gt.add_geometry_object('wall', tree)
        path = os.path.join(folder, f'tile_{index:02d}.png')
        gt.render_with(bpy.context.scene, obj, gt.colour_material('piece_colour', **photo), path, False, False, samples=16)
        files.append(os.path.basename(path))
        labels.append(label)
    with open(os.path.join(folder, 'sweep.json'), 'w') as handle:
        json.dump({'files': files, 'labels': labels}, handle)
print('done')
