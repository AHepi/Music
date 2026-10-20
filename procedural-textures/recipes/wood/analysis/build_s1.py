# What this does (plain words): builds the S1 description (S0 layout + statistical paint "stamps" drawn from the fitted paint model) of the wood reference, writes it to
# ../description/S1_layout_stamps.json, paints a numpy preview and scores it. Plain Python (python3 -I). Options: --rate A,B,C,... (stamp count scale per size class).
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_descriptions as md
import preview as pv
palette, palette_lab = md.make_s_palette()
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
cracks = json.load(open(os.path.join(HERE, 'cracks_fitted.json')))
model = json.load(open(os.path.join(HERE, 'paint_model.json')))
rate = [float(v) for v in sys.argv[sys.argv.index('--rate') + 1].split(',')] if '--rate' in sys.argv else [1.0] * len(model['classes'])
name = sys.argv[sys.argv.index('--name') + 1] if '--name' in sys.argv else 'S1_layout_stamps'
stamp_model = {k: model[k] for k in ('classes', 'class_group', 'child_classes', 'zone', 'child')}
d = md.base_description(palette, 'S1: layout + statistical paint (stamps); invented paint of the measured kind, not the reference paint')
if os.environ.get('GRAIN'):
    d['maps'] = dict(d['maps'], grain=json.loads(os.environ['GRAIN']))
d['layers'] = md.layout_layers(fit, cracks, palette_lab, crack_count=int(os.environ.get('CRACKS', 25)), with_stamps={'type': 'stamps', 'seed': 21, 'model': stamp_model, 'rate_scale': rate})
size = md.write(d, os.path.join(HERE, '..', 'description', name + '.json'))
r = pv.run(os.path.join(HERE, '..', 'description', name + '.json'), os.path.join(HERE, '..', 'outputs', 'preview_' + name), 2, True)
print('bytes', size, json.dumps({k: r.get(k) for k in ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall']}))
