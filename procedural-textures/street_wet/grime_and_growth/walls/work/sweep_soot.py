import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from jobs import J, PL
import mround
OUT = os.path.join(HERE, '..', 'out')
V = json.loads(sys.argv[2])   # {name: {dial: value}}
tag = sys.argv[1]
def jobs_for(cam, light):
    return [J(f's_{n}_{cam}', 'solo:soot', cam=cam, light=light, size=PL, keep_png=True, plate_height=2730, dials={'soot': d}) for n, d in V.items()]
specs = {'street': jobs_for('main', 'A') + jobs_for('notice', 'A'), 'lockout': jobs_for('lockout', 'B')}
import shutil
for scene, jobs in specs.items():
    p = os.path.join(HERE, f'jobs_sweep_{scene}.json'); json.dump(jobs, open(p, 'w'))
    sub = subprocess.run(['python3', os.path.join(HERE, 'drive.py'), tag + '_' + scene, p, scene], capture_output=True, text=True)
    d = os.path.join(OUT, tag + '_' + scene)
    for f in os.listdir(os.path.join(OUT, 'maps')): shutil.copy(os.path.join(OUT, 'maps', f), d)
for cam, scene, base in (('main', 'street', 'plate_main_A_wet'), ('notice', 'street', 'plate_notice_A_wet'), ('lockout', 'lockout', 'plate_lockout_B_wet')):
    d = os.path.join(OUT, tag + '_' + scene)
    for n in V:
        res, *_ = mround.mush(d, f's_{n}_{cam}', cam=cam, base=mround.BASE_PLATES + base + '.png')
        sh = mround.short(res, classes=('walls', 'trims'))
        w, t = sh['walls'], sh['trims']
        print(f'{n:6s} {cam:8s} walls m1 {w["m1"]:.3f} m2 {w["m2"]:+.3f} m3 {w["m3"]:.3f} m4 {w["m4"]:.2f} m5 {[v for v in w["m5"].values() if v]} | trims m1 {t["m1"]:.3f} m2 {t["m2"]:+.3f} m3 {t["m3"]:.3f} m5 {[v for v in t["m5"].values() if v]}')
for f in os.listdir(OUT):
    if f.startswith(tag + '_'):
        for g in os.listdir(os.path.join(OUT, f)):
            if g.endswith('.png') and not g.startswith(('class', 'depth')): os.remove(os.path.join(OUT, f, g))
