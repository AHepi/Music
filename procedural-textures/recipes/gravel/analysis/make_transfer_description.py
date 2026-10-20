# What this does (plain words): the TRANSFER test. It takes the finished gravel description (S_v1) and turns it into a description for a surface nobody gave us:
# ROUNDED PEBBLES ON SAND (a pebble beach / river-bed look) by changing ONLY numbers in the description (no generator code is touched):
#   more sides per stone and no chips (round pebbles), a grey/beige/ochre stone palette, a sand palette instead of brown soil, a softer light shadow,
#   fewer and bigger pebbles, looser packing, no extra facets, and a new height stretch (the one number that must be found again for every new surface:
#   the sand is bright, so the gravel's height stretch would turn all of it white). The change list is printed and saved in transfer/pebbles_changes.json.
# Run: python3 -I make_transfer_description.py   (writes description/transfer_pebbles.json)
import copy, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import preview_tools as pt

base = json.load(open(os.path.join(HERE, '..', 'description', 'S_v4.json')))
d = copy.deepcopy(base)
changes = []
def set_(path, value):
    changes.append(path)
    node = d
    keys = path.split('/')
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = keys[-1]
    if isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value

pebble_tones = [[92, 90, 88], [118, 112, 104], [150, 142, 128], [176, 168, 152], [128, 116, 98], [70, 68, 66], [200, 194, 180], [108, 96, 84]]
sand_tones = [[120, 100, 72], [144, 122, 88], [160, 136, 98], [170, 150, 118], [176, 152, 112], [190, 168, 128], [200, 180, 140], [214, 196, 160]]
set_('stones/tones', pebble_tones)
set_('soil/tones', sand_tones)
set_('ground', sand_tones[2])
set_('stones/rim', 0.6); set_('stones/rim_rgb', [70, 60, 48])
set_('stones/shadow', 3.0); set_('stones/shadow_rgb', [104, 88, 62])
set_('stones/chip', 0.015)
set_('stones/facets', 0)
set_('stones/mottle_per_radius', 0.25); set_('stones/mottle_shift', [5, 12]); set_('stones/lit_shift', [6, 14]); set_('stones/shade_shift', [4, 9])
set_('light', [-0.5, -0.85])
classes = [
    {'count': 230, 'radius': [15, 28], 'aspect': [0.65, 1.0], 'sides': [9, 12], 'jitter': 0.07, 'spacing': 0.9, 'rust': 0.0, 'weights': [1, 2, 2, 1, 2, 1, 1, 1]},
    {'count': 620, 'radius': [8, 15], 'aspect': [0.7, 1.0], 'sides': [8, 11], 'jitter': 0.07, 'spacing': 0.9, 'rust': 0.0, 'weights': [1, 2, 2, 1, 2, 1, 1, 1]},
    {'count': 1300, 'radius': [4, 8], 'aspect': [0.75, 1.0], 'sides': [7, 10], 'jitter': 0.08, 'spacing': 0.9, 'rust': 0.0, 'weights': [1, 2, 2, 1, 2, 1, 1, 1]},
    {'count': 1700, 'radius': [2.5, 4], 'aspect': [0.8, 1.0], 'sides': [6, 9], 'jitter': 0.08, 'spacing': 0.9, 'rust': 0.0, 'weights': [1, 2, 2, 1, 2, 1, 1, 1]}]
set_('stones/classes', classes)
set_('soil/layers/0/count', 2500); set_('soil/layers/1/count', 900); set_('soil/layers/2/count', 200)
for layer in d['soil']['layers']:
    layer['top_share'] = 0.2
d['soil']['specks'] = [{'count': 1500, 'radius': [0.8, 1.8], 'tones': [[96, 80, 58], [230, 222, 200]], 'weights': [1, 1]}]
changes.append('soil/specks')
set_('soil/weights_note', 'sand')
for layer in d['soil']['layers']:
    layer['weights'] = [1, 1, 2, 2, 2, 2, 1, 1]
# the one number to find again: the height stretch. Draw the tile (plain preview), find its 1st and 99th percentile of the same red/green/blue mix, stretch those to 10 and 245.
picture, n, _, _ = pt.make_preview(d, scale=1)
rgb = picture[..., ::-1].astype(np.float64)
mix = np.array([267.15, 91.48, 210.5]) / 255.0
g = rgb @ mix
lo, hi = np.percentile(g, [1, 99])
gain = (245 - 10) / (hi - lo)
d['maps']['height']['mix'] = (mix * 255.0 * gain).round(2).tolist()
d['maps']['height']['offset'] = round(float(10 - lo * gain), 2)
changes.append('maps/height/mix and offset (new height stretch from the tile itself, percentiles 1 and 99)')
d['seed_note'] = 'transfer: pebbles on sand'
d['stones']['seed'] = 7; d['soil']['seed'] = 7
json.dump(d, open(os.path.join(HERE, '..', 'description', 'transfer_pebbles.json'), 'w'), separators=(',', ':'))
json.dump({'what_was_changed': changes, 'height_stretch': {'percentile_1': float(lo), 'percentile_99': float(hi), 'gain': float(gain)}}, open(os.path.join(HERE, '..', 'transfer', 'pebbles_changes.json'), 'w'), indent=1)
print('changed:', changes)
print('size', len(json.dumps(d, separators=(',', ':'))), 'bytes; height stretch', d['maps']['height'])
