# What this file does (plain words): the checker's own re-measure of the builders' "joint contrast" for all 22 pictures of the lighting test set, drawn three ways each (round 2, JOINTS, JOINTS + rubbish),
# but with the stricter rule: dots under puddles and dots under rubbish are NOT left out. It uses the builders' own measure function (study/tools/b04_measure_joints.py) and their joint masks.
# Use: python3 -I my_measure_all_dots.py
import sys, json, os
sys.path.insert(0, 'proc-work/street_wet/relief_and_rubbish/study/tools')
sys.dont_write_bytecode = True
from b04_measure_joints import measure
from b09_lighting_test_set import PASS, FULL, CAMERAS
T = 'proc-work/street_wet/relief_and_rubbish/rubbish/work/testset02/'
rows = []
for label, items in FULL.items():
    spec = CAMERAS[label]
    mask = T + f"mask_{spec['camera']}_{spec['w']}x{spec['h']}.png" if os.path.exists(T + f"mask_{spec['camera']}_{spec['w']}x{spec['h']}.png") else None
    if mask is None:
        print('no mask for', label); continue
    for light, states in items:
        for state in states:
            out = {}
            for look in ('round2', 'joints', 'rubbish'):
                p = T + f'{label}_{light}_{state}_{look}.jpg'
                m = measure(p, mask)            # no puddles argument: every road dot counts
                out[look] = m
            rows.append((f'{label}_{light}_{state}', out))
def ok(m, label):
    need = PASS[label]
    for band in ('near', 'middle'):
        e = m[band]
        if e['contrast'] is None: return False
        n = need[band]
        if e['contrast'] < n['contrast'] or e['delta'] < n['delta'] or e['seen'] < n['seen']:
            return False
    return True
tot = {'round2': 0, 'joints': 0, 'rubbish': 0}
print(f"{'picture':24s} | round2 near/mid contrast, seen | JOINTS | JOINTS+rubbish  (all road dots counted)")
for name, out in rows:
    label = name.split('_')[0]
    cells = []
    for look in ('round2', 'joints', 'rubbish'):
        m = out[look]
        flag = ok(m, label)
        tot[look] += flag
        n, d = m['near'], m['middle']
        cells.append(f"{n['contrast']:.2f}/{n['seen']:.2f} {d['contrast']:.2f}/{d['seen']:.2f} {'PASS' if flag else 'FAIL'}")
    print(f'{name:24s} | ' + ' | '.join(cells))
print('pass counts with every road dot counted (puddles and rubbish included):', tot, 'of', len(rows))
json.dump({n: o for n, o in rows}, open('proc-work/street_wet/relief_and_rubbish/check_round_1/my_measure_all_dots.json', 'w'), indent=1)
