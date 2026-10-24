# gathers the walls results into walls_results.json (work folder) and selftest_walls.json (kit walls folder)
import json, os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'out')
KITW = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/walls'
res = {}
# self-tests
st = {}
for name, tag in (('street_with_earlier_layers', 'fs_street'), ('street_steps_all_doors_whitened', 'fs_steps'), ('lockout_file', 'fs_lockout'), ('courtyard_courtyard_look', 'fs_court')):
    p = os.path.join(OUT, tag, 'selftest_walls.json')
    if os.path.exists(p): st[name] = json.load(open(p))
json.dump(st, open(os.path.join(KITW, 'selftest_walls.json'), 'w'), indent=1)
json.dump(st, open(os.path.join(HERE, '..', 'selftest_walls.json'), 'w'), indent=1)
# plate measures from final_eval.txt
txt = open(os.path.join(HERE, 'final_eval_f8.txt')).read()
cam = None; meas = {}
for line in txt.splitlines():
    m = re.match(r'== (\w+): plate ratio ([\d.]+)', line)
    if m: cam = m.group(1); meas[cam] = dict(plate_ratio=float(m.group(2)), classes={}, p3={}); continue
    m = re.match(r'\s+(walls|trims|roofs|colliery|chimneys)\s+m1 ([\d.]+) m2 ([+-][\d.]+) m3 ([\d.]+) m4 ([\d.]+) m5 (.*)', line)
    if m and cam: meas[cam]['classes'][m.group(1)] = dict(m1=float(m.group(2)), m2=float(m.group(3)), m3=float(m.group(4)), m4=float(m.group(5)), m5=m.group(6)); continue
    m = re.match(r'\s+P3 (\w+)\s+marks\s+(\d+) good\s+(\d+) risky\s+(\d+) lost\s+(\d+) crushed\s+(\d+)', line)
    if m and cam: meas[cam]['p3'][m.group(1)] = dict(marks=int(m.group(2)), good=int(m.group(3)), risky=int(m.group(4)), lost=int(m.group(5)), crushed=int(m.group(6))); continue
res['plates'] = meas
# P7 drawing time and P2 wet look (wall part)
import sys
sys.path.insert(0, HERE)
import mround
mc = mround.mc
timing, p2 = {}, {}
for cam, tag in (('main', 'tm_s'), ('lockout', 'tm_l')):
    d = os.path.join(OUT, tag)
    try:
        tb = [json.load(open(os.path.join(d, f'tb{i}_{cam}.json'))) for i in (1, 2, 3)]; tk = [json.load(open(os.path.join(d, f'tk{i}_{cam}.json'))) for i in (1, 2, 3)]
    except Exception as e:
        timing[cam] = dict(error=str(e)); continue
    bmin = min(x['seconds'] for x in tb); kmin = min(x['seconds'] for x in tk)
    timing[cam] = dict(base_seconds=[x['seconds'] for x in tb], kit_seconds=[x['seconds'] for x in tk], best_base=bmin, best_kit=kmin, ratio=round(kmin / bmin, 3), first_picture_after_applying=tk[0]['seconds_job'], first_base_job=tb[0]['seconds_job'])
    cmap = mc.read_class(os.path.join(d, f'class_{cam}_540x960.png')); cls = mc.classes(mround.settings)
    p2[cam] = {}
    for c in ('walls', 'trims'):
        m = mc.class_mask(cmap, cls[c]); r = {}
        for who in ('base', 'kit'):
            dry = mc.read_lum(os.path.join(d, f'w_{who}_{cam}_dry.png'))[m].mean(); wet = mc.read_lum(os.path.join(d, f'w_{who}_{cam}_wet.png'))[m].mean()
            r[who] = round(float(wet / dry), 4)
        p2[cam][c] = dict(base=r['base'], kit=r['kit'], difference=round(r['kit'] - r['base'], 4))
res['time_P7'] = timing
res['wet_look_P2_walls'] = p2
json.dump(res, open(os.path.join(HERE, '..', 'walls_results.json'), 'w'), indent=1)
print('ok', list(st), list(meas))
