# What this does (plain words): the TRANSFER test. It takes the slate recipe to a roof covering nobody gave us and changes ONLY the numbers in
# the fitted description: the palette (weathered wooden shingles / clay roof tiles instead of blue-grey slate), how many rows and tiles per tile,
# how wide and tall they are, how thick the joints are, how the paint stamps are sized and coloured. No generator code is changed except where
# said. It writes the new "fitted numbers" files and a sampled description for each, ready for slate_generator.py. Plain Python.
# Use: python3 -I make_transfer_descriptions.py
import copy, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(SLATE, 'generator'))
import sampler
base = json.load(open(os.path.join(SLATE, 'generator', 'fitted_distributions.json')))


def hexrgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def make_fitted(kind):
    f = copy.deepcopy(base)
    if kind == 'cedar_shingles':
        # palette: [0] black joint, then 7 weathered wood tones (dark to light), 2 mossy greens, 2 pale bleached, 1 dark knot colour, 1 silver
        palette = ['#0e0c0a', '#2a211b', '#3a2d24', '#4c3a2d', '#5f4a38', '#75604b', '#8c7660', '#a28f78', '#4a5230', '#5d6a3b', '#b8a98f', '#cdbfa6', '#1d1612', '#8d8a80']
        f['palette'] = [hexrgb(c) for c in palette]
        f['roughness'] = [0.95] + [0.85] * 7 + [0.95, 0.95, 0.8, 0.8, 0.9, 0.7]
        f['rows_per_tile'], f['slates_per_row'] = 14, 12
        f['row_height'] = [83.0, 3.0]
        f['row_gap'] = [6.0, 0.4]
        f['width_log'] = [float(np.log(104.0)), 0.28]            # shingles of very different widths
        f['joint_lean'] = [0.0, 0.02]
        f['joint_gap'] = [3.0, 1.0]
        f['corner'] = 3.0
        f['rough'] = {'top': 1.5, 'bottom': 2.2, 'side': 1.2, 'scale': 10.0}
        f['top_shift_std'], f['bottom_shift_std'] = 1.5, 3.0
        pm = f['paint_model']
        pm['family_colours'] = {'blue': [1, 2, 3, 4, 5, 6, 7], 'olive': [8, 9], 'tan': [10, 11], 'black': [12]}
        pm['slate_spread'] = {'tone': [100.0, 6.0], 'olive': [0.04, 0.05], 'tan': [0.05, 0.03]}
        pm['tone_by_y'] = [-9.0, -3.0, 0.0, 2.0, 4.0, 8.0]
        for band in pm['band']:
            band['tone_residual_std'] = round(band['tone_residual_std'] * 0.55, 2)
            band['log_w'][0] -= 0.45                                # narrower patches: long thin grain streaks
            band['log_h'][0] += 0.15
        f['slate_pool'] = [[100.0, 0.02, 0.05], [96.0, 0.0, 0.07], [104.0, 0.06, 0.03], [99.0, 0.1, 0.04], [101.0, 0.0, 0.1], [93.0, 0.03, 0.02]]
        f['gap'] = 0
        f['phase_mode'] = 'random'
    if kind == 'fish_scale_clay':
        # palette: [0] joint shadow, 7 terracotta/clay tones dark to light, 2 mossy greens, 2 pale lime-wash chips, 1 soot, 1 grey
        palette = ['#120c0a', '#4a2418', '#5e2f1e', '#74391f', '#8a4626', '#a1562e', '#b86a3a', '#cc8450', '#4f5a30', '#67743c', '#d3bb98', '#e1cdae', '#241410', '#8f8478']
        f['palette'] = [hexrgb(c) for c in palette]
        f['roughness'] = [0.95] + [0.9] * 7 + [0.95, 0.95, 0.85, 0.85, 0.95, 0.8]
        f['rows_per_tile'], f['slates_per_row'] = 17, 12
        f['row_height'] = [66.0, 1.0]
        f['row_gap'] = [7.0, 0.3]
        f['width_log'] = [float(np.log(104.5)), 0.02]
        f['joint_lean'] = [0.0, 0.01]
        f['joint_gap'] = [2.5, 0.4]
        f['corner'] = 4.0
        f['bottom_round'] = 1.0                                    # the one new generator setting: lower corners rounded all the way (a half circle)
        f['rough'] = {'top': 0.8, 'bottom': 1.0, 'side': 0.8, 'scale': 12.0}
        f['top_shift_std'], f['bottom_shift_std'] = 0.8, 1.0
        pm = f['paint_model']
        pm['family_colours'] = {'blue': [1, 2, 3, 4, 5, 6, 7], 'olive': [8, 9], 'tan': [10, 11], 'black': [12]}
        pm['slate_spread'] = {'tone': [95.0, 7.0], 'olive': [0.03, 0.04], 'tan': [0.04, 0.03]}
        pm['tone_by_y'] = [-10.0, -4.0, 0.0, 2.0, 5.0, 9.0]
        for band in pm['band']:
            band['tone_residual_std'] = round(band['tone_residual_std'] * 0.5, 2)
            band['log_w'][0] -= 0.5
        f['slate_pool'] = [[95.0, 0.02, 0.04], [92.0, 0.0, 0.06], [99.0, 0.05, 0.03], [96.0, 0.08, 0.04], [94.0, 0.0, 0.08]]
        f['gap'] = 0
        f['phase_mode'] = 'half'
    return f


if __name__ == '__main__':
    for kind in ('cedar_shingles', 'fish_scale_clay'):
        f = make_fitted(kind)
        json.dump(f, open(os.path.join(HERE, f'fitted_{kind}.json'), 'w'), separators=(',', ':'))
        for seed in (1, 2):
            d = sampler.sample_description(seed, fitted=f)
            # the height stretch is surface-specific. A rule that reproduces the slate fit (9.5 and 111.5) from the slate's own picture: the 1st and 99th
            # percentile of the brightness of the picture (slate: 8.8 and 114). Used here because there is no reference height for a new surface.
            sys.path.insert(0, os.path.join(SLATE, 'analysis'))
            import cv2, preview_tools as pt
            grey = cv2.cvtColor(pt.draw(d, size=627), cv2.COLOR_BGR2GRAY)
            d['maps'] = json.loads(json.dumps(d['maps']))
            d['maps']['height']['grey_low'], d['maps']['height']['grey_high'] = round(float(np.percentile(grey, 1)), 1), round(float(np.percentile(grey, 99)), 1)
            print(kind, seed, 'height stretch from the picture:', d['maps']['height']['grey_low'], d['maps']['height']['grey_high'])
            path = os.path.join(HERE, f'{kind}_{seed}.json')
            json.dump(d, open(path, 'w'), separators=(',', ':'))
            print(path, os.path.getsize(path), 'bytes')
