# python3 evalall.py TAG [layers comma, default soot,runoff,foot,steps]  -> draws the three plates + layer masks, prints P5 and P3 numbers
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from jobs import J, PL
import mround
OUT = os.path.join(HERE, '..', 'out')
tag = sys.argv[1]
layers = (sys.argv[2] if len(sys.argv) > 2 else 'soot,runoff,foot,steps').split(',')
kitlook = 'kit:' + ','.join(layers)
def jobs_for(cam, light):
    j = [J(f't_all_{cam}', kitlook, cam=cam, light=light, size=PL, keep_png=True, plate_height=2730)]
    for l in layers:
        j.append(J(f'tm_{l}_{cam}', f'solo:{l}', cam=cam, light=light, view=f'layer:{l}', size=(1536, 2730, 1), plate_height=2730))
    return j
specs = {'street': jobs_for('main', 'A') + jobs_for('notice', 'A'), 'lockout': jobs_for('lockout', 'B')}
for scene, jobs in specs.items():
    p = os.path.join(HERE, f'jobs_eval_{scene}.json'); json.dump(jobs, open(p, 'w'))
    sub = subprocess.run(['python3', os.path.join(HERE, 'drive.py'), tag + '_' + scene, p, scene], capture_output=True, text=True)
    print(scene, sub.stdout[-200:].strip().splitlines()[-1] if sub.stdout.strip() else sub.stderr[-300:])
    d = os.path.join(OUT, tag + '_' + scene)
    for f in os.listdir(os.path.join(OUT, 'maps')):
        import shutil; shutil.copy(os.path.join(OUT, 'maps', f), d)
for cam, light, scene, base in (('main', 'A', 'street', 'plate_main_A_wet'), ('notice', 'A', 'street', 'plate_notice_A_wet'), ('lockout', 'B', 'lockout', 'plate_lockout_B_wet')):
    d = os.path.join(OUT, tag + '_' + scene)
    res, *_ = mround.mush(d, f't_all_{cam}', cam=cam, base=mround.BASE_PLATES + base + '.png')
    sh = mround.short(res, classes=('walls', 'trims', 'roofs', 'colliery', 'chimneys', 'iron'))
    print(f'== {cam}: plate ratio {sh["plate_ratio"]}')
    for c in ('walls', 'trims', 'roofs', 'colliery', 'chimneys'):
        e = sh.get(c)
        if e: print(f'   {c:9s} m1 {e["m1"]:.3f} m2 {e["m2"]:+.3f} m3 {e["m3_"] if False else e["m3"]:.3f} m4 {e["m4"]:.2f} m5 {e["m5"]}')
    for l in layers:
        zone = {'soot': ('walls', None), 'runoff': ('walls', 20), 'foot': ('walls', 30), 'steps': (None, 15)}.get(l, ('walls', None))
        try:
            r = mround.readable(d, f't_all_{cam}', os.path.join(d, f'tm_{l}_{cam}.png'), zone[0], zone[1], cam=cam)
            print(f'   P3 {l:7s} marks {r["marks"]:4d} good {r["good"]:3d} risky {r["risky"]:3d} lost {r["lost"]:3d} crushed {r["crushed"]:3d}  good-share {r["share_good"]} lost-share {r["share_lost"]} crushed-share {r["share_crushed"]}')
        except Exception as e:
            print('   P3', l, 'ERR', e)
