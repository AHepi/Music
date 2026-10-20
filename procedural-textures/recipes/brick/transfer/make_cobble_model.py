# What this does (plain words): the TRANSFER test. It builds a "model" file (the numbers the sampler draws from) for a surface the recipe was NOT fitted on:
# grey granite cobblestones / paving setts with sandy joints and a little moss. Nothing in the generator is changed except the numbers below: the layout
# (more, smaller, rounder stones in 13 courses), the palette (16 cool greys, sandy joints, moss greens), which colours stones and joints use, the outline
# settings, the tone curve that turns colour into height. The patch SIZE statistics (how many patches of what size, how stretched, how tilted) are copied
# unchanged from the brick measurement: they are the "hand-painted paint patch" look, which is what is carried over.
# Writes ../generator/sampler_model_cobble.json. No reference picture of cobbles exists here, so nothing is "fitted": the numbers are chosen by eye.
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
brick = json.load(open(os.path.join(HERE, '..', 'generator', 'sampler_model_brick.json')))
palette = [[34, 36, 40], [48, 50, 55], [62, 65, 70], [78, 82, 88], [92, 96, 102], [108, 112, 118], [124, 126, 128], [96, 92, 86],
           [112, 104, 92], [74, 86, 78], [88, 110, 84], [120, 140, 100], [150, 140, 120], [128, 118, 100], [104, 96, 84], [170, 165, 155]]
rough = [0.85, 0.9, 0.7, 0.68, 0.66, 0.64, 0.62, 0.7, 0.75, 0.8, 0.9, 0.9, 0.95, 0.95, 0.95, 0.9]
palette = [c + [r] for c, r in zip(palette, rough)]
stone_colours = [2, 3, 4, 5, 6, 7, 8, 9]
joint_colours = [12, 13, 14]
def table(centre, spread, moss=0.10, dark=0.08, pale=0.06):
    p = np.zeros(16)
    for k in stone_colours:
        p[k] += np.exp(-0.5 * ((k - centre) / spread) ** 2)
    p /= p.sum(); p *= (1 - moss - dark - pale)
    p[10] += moss * 0.6; p[11] += moss * 0.15; p[9] += moss * 0.25
    p[1] += dark * 0.6; p[0] += dark * 0.4
    p[15] += pale * 0.5; p[6] += pale * 0.5
    return [round(float(v), 4) for v in p / p.sum()]
class_of_colour = [0, 0, 0, 0, 1, 2, 3, 2, 2, 1, 0, 0, 4, 4, 4, 4]
class_centres = {0: 3.2, 1: 4.5, 2: 6.0, 3: 6.5, 4: 7.0}
model = {'tile': 1254, 'surface': 'cobblestone', 'palette': palette, 'maps': {'blur_sigma': 0.7, 'curve_x': [30, 60, 90, 120, 150, 180], 'curve_y': [0, 50, 110, 170, 220, 255], 'normal_strength': 5.0},
         'backdrop': 13,
         'layout': {'face_height': [84.0, 3.0], 'row_pitch_mean': 96.5, 'row_pitch_target': 96.5, 'brick_pitch': [150.0, 38.0], 'joint_gap': [13.0, 3.0],
                    'vertical_gap': 12.0, 'corner_radius': 26.0},
         'outline': {'width': 1.5, 'ragged': 1.5, 'ragged_wavelength': 10.0, 'ring_inside': [1.0, 1.0, 1.0, 1.0], 'ring_outside': [1.0, 0.5, 1.0, 2.0],
                     'rgb_rough': [28, 30, 34, 0.9]},
         'brick_base_colour': {'class_of_colour': class_of_colour, 'frequency': [0.0, 0.0, 0.12, 0.2, 0.16, 0.14, 0.08, 0.1, 0.1, 0.1, 0, 0, 0, 0, 0, 0]},
         'brick_patches': {'bins': brick['brick_patches']['bins'], 'colour_probability': {}},
         'mortar_patches': {'bins': brick['mortar_patches']['bins'], 'colour_probability': {}}}
for g in range(5):
    for co in range(3):
        model['brick_patches']['colour_probability'][f'{g}_{co}'] = table(class_centres[g], 1.4 + 0.6 * co)
for co in range(3):
    p = np.zeros(16)
    p[joint_colours] = [0.34, 0.34, 0.2]; p[15] = 0.04; p[1] = 0.04; p[10] = 0.04
    model['mortar_patches']['colour_probability'][str(co)] = [round(float(v), 4) for v in p / p.sum()]
json.dump(model, open(os.path.join(HERE, '..', 'generator', 'sampler_model_cobble.json'), 'w'), separators=(',', ':'))
print('wrote cobble model', len(json.dumps(model)), 'bytes')
