# What this does (plain words): writes a first by-hand gravel description (soil recipe + stone recipe with size classes) so the painter can be tried.
# The colour tables are the measured palettes of the reference's stones and soil (analysis/measure_gravel.py); the counts and sizes are first guesses
# that analysis/calibrate_sampler.py later tunes against the measured size distribution.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, '..', 'scores', 'measurements.json')))
stone_tones = m['stone_palette_rgb']
soil_tones = m['soil_palette_rgb']
mix = m['stone_colour_mix_by_size_class']
soil_weights = [round(float(w) ** 0.6, 3) for w in m['soil_palette_share']]
def avg(rows): 
    import numpy as np
    return np.mean(rows, axis=0).round(3).tolist()
description = {
    'format': 'gravel_painter_1', 'tile': 1254, 'ground': soil_tones[2], 'light': [0.0, -1.0],
    'maps': {'height': {'mix': [267.15, 91.48, 210.5], 'offset': -17.7, 'blur': 0.5}, 'normal': {'strength': 10}},
    'soil': {'seed': 1, 'tones': soil_tones, 'layers': [
        {'count': 6000, 'radius': [2.2, 6.0], 'shape': 1.0, 'sides': [5, 8], 'jitter': 0.3, 'top_share': 0.5, 'weights': soil_weights},
        {'count': 2200, 'radius': [5.0, 11.0], 'shape': 1.0, 'sides': [5, 8], 'jitter': 0.3, 'weights': soil_weights},
        {'count': 500, 'radius': [10.0, 20.0], 'shape': 1.0, 'sides': [5, 8], 'jitter': 0.3, 'weights': soil_weights}],
        'specks': [{'count': 2800, 'radius': [1.0, 2.6], 'tones': [[16, 15, 15], [25, 25, 27], [33, 34, 38]], 'weights': [3, 2, 1]},
                   {'count': 1800, 'radius': [0.9, 2.2], 'tones': [[149, 115, 87], [114, 96, 80], [111, 117, 116]], 'weights': [2, 1, 1]}]},
    'stones': {'seed': 1, 'tones': stone_tones, 'rim': 0.8, 'shadow': 6.0, 'shadow_rgb': [30, 22, 17], 'chip': 0.12, 'chip_step': 0.28, 'facets': 2, 'mottle_per_radius': 0.7, 'mottle_size': [0.07, 0.24], 'mottle_min_radius': 8.0,
               'classes': [
                   {'count': 80, 'radius': [30, 48], 'aspect': [0.55, 0.95], 'sides': [4, 6], 'jitter': 0.14, 'spacing': 0.65, 'rust': 0.12, 'weights': avg(mix[10:12])},
                   {'count': 126, 'radius': [17, 30], 'aspect': [0.55, 1.0], 'sides': [4, 6], 'jitter': 0.16, 'spacing': 0.65, 'rust': 0.1, 'weights': avg(mix[8:10])},
                   {'count': 500, 'radius': [9, 17], 'aspect': [0.6, 1.0], 'sides': [4, 7], 'jitter': 0.18, 'spacing': 0.65, 'rust': 0.1, 'weights': avg(mix[6:8])},
                   {'count': 1050, 'radius': [4.5, 9], 'aspect': [0.65, 1.0], 'sides': [4, 7], 'jitter': 0.2, 'spacing': 0.65, 'rust': 0.1, 'weights': avg(mix[4:6])},
                   {'count': 1800, 'radius': [2.5, 4.5], 'aspect': [0.7, 1.0], 'sides': [4, 6], 'jitter': 0.2, 'spacing': 0.65, 'rust': 0.1, 'weights': avg(mix[1:4])}]},
}
os.makedirs(os.path.join(HERE, '..', 'description'), exist_ok=True)
json.dump(description, open(os.path.join(HERE, '..', 'description', 'S_first_guess.json'), 'w'), indent=1)
print('written', len(json.dumps(description)), 'bytes')
