# What this file does (plain words): re-measures the "joint contrast" of the pictures of the lighting test set that were drawn with the final look (JOINTS and the rubbish), with the checker's stricter rule:
# dots under puddles and dots under rubbish are NOT left out (every road dot counts). It uses the job's own measure function (study/tools/b04_measure_joints.py) and the job's own joint masks.
# It is the checker's my_measure_all_dots.py with the folder as an argument and only the look "rubbish" (the other two looks were measured in round 1).
# Use: python3 -I measure_all_dots.py FOLDER [FOLDER_OF_THE_ROUND_1_PICTURES_TO_COMPARE_WITH]
import sys, json, os
HERE = 'proc-work/street_wet/painter_round_2/plate'
sys.path.insert(0, HERE + '/study/tools')
sys.dont_write_bytecode = True
from b04_measure_joints import measure
from b09_lighting_test_set import PASS, FULL, CAMERAS
T = sys.argv[1].rstrip('/') + '/'
OLD = sys.argv[2].rstrip('/') + '/' if len(sys.argv) > 2 else None
def ok(m, label):
    need = PASS[label]
    for band in ('near', 'middle'):
        e = m[band]
        if e['contrast'] is None:
            return False
        n = need[band]
        if e['contrast'] < n['contrast'] or e['delta'] < n['delta'] or e['seen'] < n['seen']:
            return False
    return True
rows, total, total_old = [], 0, 0
print(f"{'picture':24s} | NEW near/mid contrast, seen (all road dots counted)" + ('  | ROUND 1 (rubbish look)' if OLD else ''))
for label, items in FULL.items():
    spec = CAMERAS[label]
    mask = T + f"mask_{spec['camera']}_{spec['w']}x{spec['h']}.png"
    for light, states in items:
        for state in states:
            name = f'{label}_{light}_{state}_rubbish'
            m = measure(T + name + '.jpg', mask)
            flag = ok(m, label)
            total += flag
            n, d = m['near'], m['middle']
            line = f"{label+'_'+light+'_'+state:24s} | {n['contrast']:.2f}/{n['seen']:.2f} {d['contrast']:.2f}/{d['seen']:.2f} {'PASS' if flag else 'FAIL'}"
            if OLD:
                mo = measure(OLD + name + '.jpg', OLD + f"mask_{spec['camera']}_{spec['w']}x{spec['h']}.png")
                fo = ok(mo, label)
                total_old += fo
                line += f" | {mo['near']['contrast']:.2f}/{mo['near']['seen']:.2f} {mo['middle']['contrast']:.2f}/{mo['middle']['seen']:.2f} {'PASS' if fo else 'FAIL'}"
            print(line)
            rows.append((name, m, flag))
print('pass count with every road dot counted (puddles and rubbish included): NEW', total, 'of', len(rows), ('; ROUND 1 ' + str(total_old) + ' of ' + str(len(rows))) if OLD else '')
json.dump({n: dict(m, pass_all_dots=f) for n, m, f in rows}, open(T + 'measure_all_dots.json', 'w'), indent=1)
