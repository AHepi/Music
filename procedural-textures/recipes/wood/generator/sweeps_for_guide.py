# What this does (plain words): makes the "what does this setting do?" pictures for the wood guide. Inside Blender it bakes the SAME sampled wood description (seed 2) several
# times, changing ONE setting each time, as small 384-dot colour pictures, and writes them (plus a sweep.json of labels) into guide_pictures/sweep_<name>/ so that
# lib/make_strip.py can join them into a labelled strip. Settings swept: dry-brush streak cut level, hair-line thickness, zone colour spread, strip count, crack count,
# plank count. (The normal-map strength strip is made from one bake in numpy by make_normal_strength_strip.py.)
# Use: blender -b --disable-autoexec -t 2 --python sweeps_for_guide.py -- OUT_FOLDER [name ...]
import copy
import json
import os
import shutil
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sampler  # noqa: E402
import wood_generator as wg  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
out_root = arguments[0]
wanted = arguments[1:]


def with_grain(path, key, value):
    def apply(d):
        node = d['maps']['grain']
        for part in path:
            node = node[part]
        node[key] = value
        return d
    return apply


def with_stamp(key, value):
    def apply(d):
        for layer in d['layers']:
            if layer['type'] == 'stamps':
                layer[key] = [value] * 8 if key == 'rate_scale' else value
        return d
    return apply


def with_crack_scale(value):
    def apply(d):
        for layer in d['layers']:
            if layer['type'] == 'crack_field':
                layer['scale'] = value
        return d
    return apply


SWEEPS = {
    'grain_light_cut': ('Dry-brush light streaks: where the noise is cut (lower = more streaks)', [0.50, 0.54, 0.58, 0.62, 0.70], lambda v: with_grain(['hatch'], 'light_cut', v)),
    'grain_hair_thickness': ('Hair-line thickness (distance from the noise level 0.5)', [0.0, 0.004, 0.012, 0.025, 0.05], lambda v: with_grain(['hair'], 'thickness', v)),
    'paint_zone_amp': ('Zone colour spread (how far the big paint zones stray from the average)', [0.0, 0.3, 0.55, 0.9, 1.4], lambda v: with_stamp('zone_amp', v)),
    'paint_rate': ('Strip count scale (how many small paint strips)', [0.0, 0.5, 1.0, 1.6, 2.6], lambda v: with_stamp('rate_scale', v)),
    'cracks_scale': ('Crack count scale', [0.0, 0.5, 1.0, 2.0, 3.5], lambda v: with_crack_scale(v)),
    'plank_count': ('Number of planks in the tile', [3, 4, 5, 7, 9], None),
}
for name, (title, values, make) in SWEEPS.items():
    if wanted and name not in wanted:
        continue
    folder = os.path.join(out_root, 'sweep_' + name)
    os.makedirs(folder, exist_ok=True)
    files, labels = [], []
    for i, value in enumerate(values):
        if name == 'plank_count':
            d = sampler.sample_description(2, boards=value)
        else:
            d = make(value)(sampler.sample_description(2))
        out = os.path.join(folder, f'bake_{i:02d}')
        wg.bake_description(d, out, size=384, samples=4, quiet=True, with_ao=False)
        shutil.copy(os.path.join(out, 'colour.png'), os.path.join(folder, f'tile_{i:02d}.png'))
        shutil.rmtree(out)
        files.append(f'tile_{i:02d}.png')
        labels.append(f'{value}')
    json.dump({'files': files, 'labels': labels, 'title': title}, open(os.path.join(folder, 'sweep.json'), 'w'), indent=1)
    print('sweep done', name, flush=True)
