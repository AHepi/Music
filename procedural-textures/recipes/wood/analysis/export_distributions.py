# What this does (plain words): gathers every distribution the sampler needs (palette, board tone, gap/crack/knot/splatter/pebble statistics, the fitted paint model, the
# tuned paint and grain settings) into ONE small file, generator/fitted_distributions.json. The sampler reads only that file. It contains numbers measured on the
# reference picture (no picture data). Run after fit_paint_model.py, fit_sampler_stats.py and tuning. Plain Python (python3 -I).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
load = lambda name: json.load(open(os.path.join(HERE, name)))
pal = load('palette16.json'); fit = load('layout_fit.json'); stats = load('sampler_stats.json'); model = load('paint_model.json'); tuned = load('tuned_settings.json')
board_lab = [sum(b[i] for b in fit['board_mean_lab']) / len(fit['board_mean_lab']) for i in range(3)]
stats['rust_palette_lab'] = fit['blob_stats']['rust_palette_lab']
out = {'palette_rgb': pal['palette_rgb'], 'palette_lab': pal['palette_lab'], 'board_lab': [round(v, 2) for v in board_lab], 'sampler': stats,
       'paint_model': {k: model[k] for k in ('classes', 'class_group', 'child_classes', 'zone', 'child')}, 'tuned': tuned}
path = os.path.join(HERE, '..', 'generator', 'fitted_distributions.json')
text = json.dumps(out, separators=(',', ':'))
open(path, 'w').write(text)
print('wrote', os.path.abspath(path), len(text.encode()), 'bytes')
