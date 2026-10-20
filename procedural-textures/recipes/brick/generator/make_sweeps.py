# What this does (plain words): makes the "what does this setting do?" strips for the recipe guide. For each setting it takes ONE base description
# (the same random seed, so only that one setting changes), bakes it at small size once per value of the setting, and saves little pictures in
# guide_pictures/sweeps/<name>/ (tile_00.png ... plus sweep.json) that ../../lib/make_strip.py joins into a labelled strip.
# Use (system python):  python3 -I make_sweeps.py [name ...]   (no names = all sweeps)
import copy, json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RECIPE = os.path.join(PROC, 'recipes', 'brick')
sys.path.insert(0, HERE)
import sample_description as sd
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
SIZE = 384
OUT = os.path.join(RECIPE, 'guide_pictures', 'sweeps')
model = json.load(open(os.path.join(HERE, 'sampler_model_brick.json')))


def base_description(**kw):
    return sd.sample_description(7, model, grain=kw.pop('grain', 0.0), cell_scale=kw.pop('cell_scale', 2.0), **kw)


def layer(desc, kind, index=0):
    return [l for l in desc['layers'] if l['type'] == kind][index]


def bake(desc, folder, name):
    path = os.path.join(folder, name + '.json')
    json.dump(desc, open(path, 'w'), separators=(',', ':'))
    subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(HERE, 'brick_generator.py'), '--', path, os.path.join(folder, name), '--size', str(SIZE), '--samples', '4'],
                   capture_output=True, text=True)
    return os.path.join(folder, name)


def run_sweep(name, values, labels, mutate, channel='colour', base=None, crop=None):
    folder = os.path.join(OUT, name)
    os.makedirs(folder, exist_ok=True)
    files = []
    for i, v in enumerate(values):
        desc = mutate(copy.deepcopy(base() if base else base_description()), v)
        baked = bake(desc, folder, f'work_{i:02d}')
        img = cv2.imread(os.path.join(baked, channel + '.png'))
        if crop:
            s = SIZE / 1254.0
            img = img[int(crop[1] * s):int(crop[3] * s), int(crop[0] * s):int(crop[2] * s)]
        cv2.imwrite(os.path.join(folder, f'tile_{i:02d}.png'), img)
        files.append(f'tile_{i:02d}.png')
        subprocess.run(['rm', '-rf', baked, baked + '.json'])
    json.dump({'files': files, 'labels': labels}, open(os.path.join(folder, 'sweep.json'), 'w'), indent=1)
    print('sweep', name, 'done', flush=True)


def set_grain(d, v):
    d['grain'] = {'amount': v, 'seed': 3}
    return d


def set_radius(d, v):
    for l in d['layers']:
        if l['type'] in ('bricks', 'outlines') or (l['type'] == 'mosaic' and l['target'] == 'bricks'):
            l['corner_radius'] = v
    return d


def set_ring(d, v):
    ring = layer(d, 'outlines')
    ring['inside'] = [v * 0.5, v * 0.5, v * 0.5, v * 0.75]
    ring['outside'] = [v * 0.5, 0.0, v * 0.75, v * 1.5]
    if v == 0:
        d['layers'] = [l for l in d['layers'] if l['type'] != 'outlines']
        layer(d, 'bricks')['outline_width'] = 0.0
    return d


def set_wobble(d, v):
    for l in d['layers']:
        if l['type'] == 'mosaic':
            for sc in l['scales']:
                sc['wobble'] = v
    return d


def set_soot(d, v):
    for l in d['layers']:
        if l['type'] == 'mosaic':
            for acc in l['accents']:
                if acc['name'] == 'soot':
                    acc['count'] = v
    return d


def set_cell_area(d, v):
    for l in d['layers']:
        if l['type'] == 'mosaic' and l['target'] == 'bricks':
            for k, sc in enumerate(l['scales']):
                sc['area'] = v * (320.0 / 1100.0) ** (0 if k == 0 else 1) * (1.0 if k < 2 else 0.28)
            l['scales'][0]['area'] = v
    return d


def set_scales(d, v):
    for l in d['layers']:
        if l['type'] == 'mosaic' and l['target'] == 'bricks':
            l['scales'] = l['scales'][:v]
    return d


def set_jitter(d, v):
    for l in d['layers']:
        if l['type'] == 'mosaic' and l['target'] == 'bricks':
            l['scales'][0]['jitter'] = v
            l['scales'][1]['jitter'] = v
    return d


def set_derive(d, v):
    d['maps']['blur_sigma'] = v
    return d


SWEEPS = {
    'grain_amount': ([0.0, 0.05, 0.10, 0.15, 0.25], ['grain 0', 'grain 0.05', 'grain 0.10', 'grain 0.15', 'grain 0.25'], set_grain, 'colour', (200, 200, 600, 520)),
    'corner_radius': ([0, 5, 9, 16, 26], ['radius 0', '5', '9 (reference)', '16', '26'], set_radius, 'colour', (200, 200, 800, 700)),
    'outline_ring_width': ([0, 1.0, 2.0, 4.0, 7.0], ['no ring', 'x1', 'x2 (about reference)', 'x4', 'x7'], set_ring, 'colour', (200, 200, 800, 700)),
    'edge_wobble': ([0.0, 0.6, 1.3, 2.5, 4.5], ['wobble 0', '0.6', '1.3 (reference)', '2.5', '4.5'], set_wobble, 'colour', (200, 200, 600, 520)),
    'soot_smudges': ([0, 6, 12, 24, 48], ['soot 0', '6', '12', '24', '48'], set_soot, 'colour', None),
    'big_cell_area': ([5000.0, 2500.0, 1100.0, 500.0, 220.0], ['area 5000', '2500', '1100 (reference)', '500', '220'], set_cell_area, 'colour', (200, 200, 700, 560)),
    'number_of_cell_sizes': ([1, 2, 3, 4], ['1 size', '2 sizes', '3 sizes', '4 sizes'], set_scales, 'colour', (200, 200, 700, 560)),
    'height_blur': ([0.0, 0.7, 1.5, 3.0, 6.0], ['blur 0', '0.7 (reference)', '1.5', '3', '6'], set_derive, 'normal', (200, 200, 600, 520)),
    'tone_jitter': ([0.0, 0.08, 0.2, 0.4, 0.8], ['jitter 0', '0.08', '0.2', '0.4', '0.8'], set_jitter, 'colour', None),
}

if __name__ == '__main__':
    names = sys.argv[1:] or list(SWEEPS)
    for n in names:
        values, labels, fn, channel, crop = SWEEPS[n]
        run_sweep(n, values, labels, fn, channel, crop=crop)
