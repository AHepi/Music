# What this does (plain words): a small automatic tuning loop for the S1 wood description (invented paint). For every candidate setting it writes the description,
# bakes it with Blender (4 samples, quick) and scores it with the "same kind of surface" tool; it prints one line per candidate and keeps the best settings in
# ../description/S1_tuned_settings.json. Settings tuned: how far the zone colours and strip colours may stray (zone_amp, child_amp), the strip count scale, and the
# grain brightness steps. Run in the background: python3 -I tune_s1.py     (takes about 25 minutes)
import itertools, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import make_descriptions as md
import score_tools as st
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
palette, palette_lab = md.make_s_palette()
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
cracks = json.load(open(os.path.join(HERE, 'cracks_fitted.json')))
model = json.load(open(os.path.join(HERE, 'paint_model.json')))
stamp_model = {k: model[k] for k in ('classes', 'class_group', 'child_classes', 'zone', 'child')}

def build(settings, path):
    stamps = {'type': 'stamps', 'seed': 21, 'model': stamp_model, 'rate_scale': [settings['rate']] * 8, 'zone_amp': settings['zone_amp'], 'child_amp': settings['child_amp'], 'paint_min_l': 16.0}
    d = md.base_description(palette, 'S1 tuning candidate')
    d['maps'] = dict(d['maps'], grain={'hatch': {'u': 45, 'v': 420, 'detail': 1.5, 'seed': 3, 'light_cut': settings['light_cut'], 'dark_cut': settings['dark_cut'], 'light_gain': settings['light_gain'], 'dark_gain': settings['dark_gain']},
                                       'hair': {'u': 5, 'v': 150, 'seed': 5, 'thickness': settings['hair_thickness'], 'gain': 0.45}})
    d['layers'] = md.layout_layers(fit, cracks, palette_lab, crack_count=40, with_stamps=stamps)
    md.write(d, path)

candidates = []
base = dict(rate=1.0, zone_amp=0.8, child_amp=0.8, light_cut=0.60, dark_cut=0.40, light_gain=1.5, dark_gain=0.6, hair_thickness=0.012)
candidates.append(dict(base))
for key, values in (('zone_amp', [0.55, 1.0]), ('child_amp', [0.5, 1.1]), ('rate', [0.6, 1.6]), ('light_cut', [0.57, 0.64]), ('light_gain', [1.25, 1.8]), ('hair_thickness', [0.006, 0.025])):
    for v in values:
        c = dict(base); c[key] = v; candidates.append(c)
results = []
for i, c in enumerate(candidates):
    t0 = time.time()
    path = os.path.join(WOOD, 'description', 'tune_tmp.json'); out = os.path.join(WOOD, 'outputs', 'tune_tmp')
    build(c, path)
    subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(WOOD, 'generator', 'wood_generator.py'), '--', path, out, '--size', '1254', '--samples', '4'], capture_output=True)
    r = st.tc.score_set('wood', out)
    row = dict(c, overall=r['overall'], colour=r['groups']['colour'], height=r['groups']['height'], normal=r['groups']['normal'], seconds=round(time.time() - t0))
    results.append(row)
    print(json.dumps(row), flush=True)
    json.dump(results, open(os.path.join(HERE, 'tune_s1_results.json'), 'w'), indent=1)
