# What this does (plain words): TUNES the gravel sampler's numbers (how many stones in each size class, how tightly they are packed) so that the
# generated picture has the same stone-versus-soil size distribution as the reference (the "survives opening" curves measured by measure_gravel.py).
# It makes a picture with plain OpenCV (no Blender), measures it the same way as the reference, and nudges one number at a time (coordinate search),
# keeping a change only if the match gets better. Writes the best description to description/S_calibrated.json and a log.
# Run: python3 -I analysis/calibrate_sampler.py [start.json] [rounds]
import copy, json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, '..', 'generator')
sys.path.insert(0, GEN)
import preview_tools as pt

ref = json.load(open(os.path.join(HERE, '..', 'scores', 'measurements.json')))
ref_stone, ref_soil = np.array(ref['granulometry']['stone']), np.array(ref['granulometry']['soil'])
start = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'description', 'S_first_guess.json')))
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
out_name = sys.argv[3] if len(sys.argv) > 3 else 'S_calibrated.json'
REF_EDGE = 0.229

def cost(desc):
    picture, n, _, _ = pt.make_preview(desc, scale=1)
    m = pt.measure(picture)
    c = float(np.abs(np.array(m['stone_gran']) - ref_stone).mean() + np.abs(np.array(m['soil_gran']) - ref_soil).mean())
    edge = pt.edge_density(picture)
    c += 0.5 * abs(edge - REF_EDGE)
    return c, m, edge, n

def apply(desc, params):
    d = copy.deepcopy(desc)
    for i, cls in enumerate(d['stones']['classes']):
        cls['count'] = int(round(start['stones']['classes'][i]['count'] * params['mult'][i]))
        cls['spacing'] = params['spacing'][i]
    d['soil']['layers'][0]['count'] = int(round(start['soil']['layers'][0]['count'] * params['soil_small']))
    d['soil']['layers'][1]['count'] = int(round(start['soil']['layers'][1]['count'] * params['soil_big']))
    return d

params = {'mult': [1.0] * len(start['stones']['classes']), 'spacing': [c.get('spacing', 0.8) for c in start['stones']['classes']], 'soil_small': 1.0, 'soil_big': 1.0}
best, m, edge, n = cost(apply(start, params))
print('start cost', round(best, 4), 'edge', round(edge, 3), 'shapes', n, flush=True)
steps = [('mult', i, f) for i in range(len(params['mult'])) for f in (1.5, 0.7)] + [('spacing', i, f) for i in range(len(params['spacing'])) for f in (0.9, 1.08)] \
        + [('soil_small', None, 1.0)]
for r in range(rounds):
    improved = False
    for kind, i, f in steps:
        trial = copy.deepcopy(params)
        if i is None:
            trial[kind] = trial[kind] * f
        else:
            trial[kind][i] = trial[kind][i] * f
            if kind == 'spacing':
                trial[kind][i] = float(np.clip(trial[kind][i], 0.45, 1.0))
        c, m2, e2, n2 = cost(apply(start, trial))
        if c < best - 1e-4:
            best, params, improved = c, trial, True
            print(f'round {r} {kind} {i} x{f}: cost {c:.4f} edge {e2:.3f} stone share {m2["stone_share"]:.3f} shapes {n2}', flush=True)
    if not improved:
        break
final = apply(start, params)
json.dump(final, open(os.path.join(HERE, '..', 'description', out_name), 'w'), indent=1)
json.dump(params, open(os.path.join(HERE, '..', 'scores', 'calibration_' + out_name), 'w'), indent=1)
print('done; best cost', round(best, 4), params)
