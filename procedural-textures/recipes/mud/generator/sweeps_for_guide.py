# What this does (plain words): makes the "what does this setting do?" pictures for the mud guide. It bakes the SAME sampled mud description (seed 2) several times, changing ONE setting
# each time, as small 384-dot colour pictures, and writes them into guide_pictures/sweep_<name>/ with a sweep.json of labels so that lib/make_strip.py can join them into a labelled strip.
# Settings swept: number of crumbly ground clods, how strongly clods clump into zones of one tone, number of wheel ruts, rut band width, number of stones, number of puddles.
# Two steps because the sampler needs OpenCV (plain Python) and the baking needs Blender:
#   python3 -I sweeps_for_guide.py prepare OUT_FOLDER          (writes the description files)
#   blender -b --disable-autoexec -t 2 --python sweeps_for_guide.py -- bake OUT_FOLDER [name ...]     (bakes them)
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
MODE = sys.argv[1] if 'bpy' not in sys.modules and len(sys.argv) > 1 and sys.argv[1] in ('prepare',) else 'bake'
if MODE == 'prepare':
    import sampler  # noqa: E402
    out_root, wanted = sys.argv[2], sys.argv[3:]
else:
    import bpy  # noqa: E402
    import mud_generator as mg  # noqa: E402
    arguments = sys.argv[sys.argv.index('--') + 1:]
    assert arguments[0] == 'bake'
    out_root, wanted = arguments[1], arguments[2:]


def rut_width_scale(d, factor):
    for layer in d['layers']:
        if layer['type'] == 'ruts':
            for item in layer['items']:
                item['w'] = item['w'] * factor
                item['bw'] = item['bw'] * factor
    return d


SWEEPS = {} if MODE != 'prepare' else {
    'clod_count': ('Crumbly ground: number of clods', [0, 4000, 9000, 14000, 28000], lambda v: sampler.sample_description(2, clod_count=v)),
    'zone_weight': ('Clods clumping into zones of one tone (0 = every clod independent)', [0.0, 0.3, 0.6, 0.85, 0.97], lambda v: sampler.sample_description(2, zone_weight=v)),
    'rut_scale': ('Number of wheel ruts', [0.0, 0.5, 1.0, 1.6, 2.4], lambda v: sampler.sample_description(2, rut_scale=v)),
    'rut_width': ('Rut band width (x normal)', [0.4, 0.7, 1.0, 1.5, 2.2], lambda v: rut_width_scale(sampler.sample_description(2), v)),
    'stone_scale': ('Number of stones', [0.0, 0.4, 1.0, 1.8, 3.0], lambda v: sampler.sample_description(2, stone_scale=v)),
    'puddle_scale': ('Number of puddles', [0.0, 0.5, 1.0, 1.6, 2.4], lambda v: sampler.sample_description(2, puddle_scale=v)),
}
if MODE == 'prepare':
    for name, (title, values, make) in SWEEPS.items():
        if wanted and name not in wanted:
            continue
        folder = os.path.join(out_root, 'sweep_' + name)
        os.makedirs(folder, exist_ok=True)
        for i, value in enumerate(values):
            json.dump(make(value), open(os.path.join(folder, f'desc_{i:02d}.json'), 'w'), separators=(',', ':'))
        json.dump({'files': [f'tile_{i:02d}.png' for i in range(len(values))], 'labels': [f'{v}' for v in values], 'title': title}, open(os.path.join(folder, 'sweep.json'), 'w'), indent=1)
        print('prepared', name, flush=True)
else:
    for name in sorted(os.listdir(out_root)):
        if not name.startswith('sweep_') or (wanted and name[6:] not in wanted):
            continue
        folder = os.path.join(out_root, name)
        info = json.load(open(os.path.join(folder, 'sweep.json')))
        for i, file_name in enumerate(info['files']):
            d = json.load(open(os.path.join(folder, f'desc_{i:02d}.json')))
            out = os.path.join(folder, f'bake_{i:02d}')
            mg.bake_description(d, out, size=384, samples=4, quiet=True, with_ao=False)
            shutil.copy(os.path.join(out, 'colour.png'), os.path.join(folder, file_name))
            shutil.rmtree(out)
        print('sweep done', name, flush=True)
