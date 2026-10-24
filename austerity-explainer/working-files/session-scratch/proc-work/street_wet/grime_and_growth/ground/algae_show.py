import os, sys, json
import cv2, numpy as np
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as S
from harness import remote
WG = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(WG, 'runs', 'plan_r7', 'out')
info = json.load(open(os.path.join(PLAN, 'plan_info.json')))
x0, x1 = info['ground_bounds']['x']; y0, y1 = info['ground_bounds']['y']; W, H = info['size']; dx, dy = (x1 - x0) / W, (y1 - y0) / H
def comps(name):
    a = cv2.imread(os.path.join(PLAN, f'plan_{name}.png'), cv2.IMREAD_UNCHANGED)
    a = a[..., 0] if a.ndim == 3 else a
    m = cv2.dilate((a > a.max() * 0.4).astype(np.uint8), np.ones((9, 9), np.uint8)) if a.max() > 0 else a * 0
    n, _, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 40:
            cx, cy = cen[i]; out.append((x0 + (cx + 0.5) * dx, y1 - (cy + 0.5) * dy, int(st[i, cv2.CC_STAT_AREA])))
    return sorted(out, key=lambda t: -t[2])
alg = comps('groundmoss_algae'); liv = comps('groundmoss_liverwort')
print('algae', alg, 'liver', liv)
targets = [('alg0', alg[0])] if alg else []
if len(alg) > 1: targets.append(('alg1', alg[1]))
if liv: targets.append(('liv0', liv[0]))
cams = []
for name, (x, y, _) in targets:
    side = -1.0 if x > 0 else 1.0
    cams.append(dict(name='sc_' + name, location=[x + side * 1.0, y - 1.2, 0.9], look_at=[x, y, 0.1], fov_v=40.0))
jobs = []
for c in cams:
    for lk in ('base', 'solo:groundmoss'):
        jobs.append(dict(name=f'{c["name"]}__{lk.replace(":", "_")}', camera=c['name'], light='A', state='wet', look=lk, view='beauty', size=[960, 720, 16], group='sc'))
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[WG], jobs=jobs, extra_cameras=cams)
out = os.path.join(WG, 'runs', 'alg_r7'); os.makedirs(out, exist_ok=True)
jf = os.path.join(out, 'jobs.json'); json.dump(spec, open(jf, 'w'))
st = S.load_set('pit_village_street')
print(remote.run_batch(st.scene('street')['file'], [jf], '/workspace/wk_out/ground_alg_r7', os.path.join(out, 'out'), runner_script=os.path.join(KIT, 'ground', 'runner_ground.py')))
