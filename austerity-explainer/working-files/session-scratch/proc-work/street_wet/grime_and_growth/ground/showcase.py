# work script: finds where the ground elements are on the plan pictures and draws close views of them (extra cameras) with and without the layer.
import os, sys, json, time
import cv2, numpy as np
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as S
from harness import remote
WG = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(WG, 'runs', sys.argv[1], 'out')
tag = sys.argv[2]
info = json.load(open(os.path.join(PLAN, 'plan_info.json')))
x0, x1 = info['ground_bounds']['x']; y0, y1 = info['ground_bounds']['y']
W, H = info['size']; dx, dy = (x1 - x0) / W, (y1 - y0) / H
def load(n):
    a = cv2.imread(os.path.join(PLAN, f'plan_{n}.png'), cv2.IMREAD_UNCHANGED)
    if a.ndim == 3: a = a[..., 0]
    return a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)
def world(cx, cy): return x0 + (cx + 0.5) * dx, y1 - (cy + 0.5) * dy
rows = np.arange(H)[:, None]; ys = y1 - (rows + 0.5) * dy
def window_of(mask, size_px, lo=2.0, hi=14.0):
    m = mask & ((ys >= lo) & (ys <= hi))
    k = cv2.boxFilter(m.astype(np.float32), -1, (size_px, size_px), normalize=False)
    cy, cx = np.unravel_index(np.argmax(k), k.shape)
    return world(cx, cy), float(k.max())
targets = {}
targets['tar'], _ = window_of(load('dirt_tar') > 0.5, 40)
targets['moss'], _ = window_of(load('groundmoss_joint_moss') > 0.5, 60)
targets['halo'], _ = window_of(load('dirt_halo') > 0.3, 30)
targets['algae'], _ = window_of(load('groundmoss_algae') > 0.3, 30)
targets['rust'], _ = window_of(load('iron_foot_rust') > 0.3, 40)
targets['kerb'], _ = window_of(load('groundcracks_kerb_chips') > 0.5, 40)
fr=json.load(open(os.path.join(WG,'feature_report.json')))['strongest_flag_crack']['position']
targets['crack']=(fr[0],fr[1])
print(targets)
cams = []
for name, (x, y) in targets.items():
    side = -1.0 if x > 0 else 1.0                                  # stand on the street side of the thing, look across it
    cams.append(dict(name=f'sc_{name}', location=[x + side * 0.9, y - 1.4, 0.95], look_at=[x, y, 0.1], fov_v=40.0))
def job(name, cam, look): return dict(name=name, camera=cam, light='A', state='wet', look=look, view='beauty', size=[960, 720, 16], group='sc')
jobs = []
for c in cams:
    for lk in ['base', 'solo:dirt', 'solo:groundcracks', 'solo:groundmoss', 'solo:iron']:
        jobs.append(job(f'{c["name"]}__{lk.replace(":", "_")}', c['name'], lk))
spec = dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[WG], jobs=jobs, extra_cameras=cams)
out_local = os.path.join(WG, 'runs', tag); os.makedirs(out_local, exist_ok=True)
jf = os.path.join(out_local, 'jobs.json'); json.dump(spec, open(jf, 'w'), indent=1)
st = S.load_set('pit_village_street')
res = remote.run_batch(st.scene('street')['file'], [jf], f'/workspace/wk_out/ground_{tag}', os.path.join(out_local, 'out'), runner_script=os.path.join(KIT, 'ground', 'runner_ground.py'))
json.dump(targets, open(os.path.join(out_local, 'targets.json'), 'w'))
print(tag, res, flush=True)
