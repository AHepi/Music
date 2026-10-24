# What this does: writes the JOBS json files the RunPod picture jobs read (preview round). Run locally: python3 -I make_jobs.py
import json, os
F = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final'
VIEWS = {
 'v_lantern': {'loc': [3.2, -1.6, 1.3], 'target': [0.95, 1.1, 0.9], 'fov_v': 32},
 'v_rocks': {'loc': [-5.5, -1.0, 1.0], 'target': [-3.5, 3.7, 0.7], 'fov_v': 40},
 'v_gravel': {'loc': [0.5, -6.5, 1.4], 'target': [5.0, -1.0, 0.0], 'fov_v': 35},
 'v_bridge': {'loc': [-0.5, -3.0, 1.6], 'target': [-2.5, 0.8, 0.2], 'fov_v': 40},
 'v_wall': {'loc': [5.11, 4.95, 1.5], 'target': [10.4, 5.95, 1.2], 'fov_v': 40},
 'v_roof': {'loc': [-2.4, -0.2, 2.5], 'target': [0.4, 5.0, 3.6], 'fov_v': 40},
 'v_posts': {'loc': [3.9, 1.3, 1.25], 'target': [0.3, 5.0, 1.1], 'fov_v': 42},
 'v_ground': {'loc': [-6.0, -4.5, 1.6], 'target': [-5.0, 1.0, 0.0], 'fov_v': 38},
 'v_maple': {'loc': [-3.0, -3.2, 1.8], 'target': [-5.9, 1.2, 3.6], 'fov_v': 45},
 'v_pond': {'loc': [-0.2, -2.6, 1.4], 'target': [-2.8, 1.0, -0.1], 'fov_v': 40},
}
def preview(look, tag, samples=64):
    R = f'{F}/renders/{tag}'
    pics = [{'out': f'{R}/{look}_hero', 'camera': 'photo', 'size': '960x640', 'samples': samples},
            {'out': f'{R}/{look}_veranda', 'camera': 'veranda', 'size': '960x640', 'samples': samples}]
    for v in VIEWS:
        pics.append({'out': f'{R}/{look}_{v}', 'camera': v, 'size': '960x640', 'samples': samples})
    return {'look': look, 'views': VIEWS, 'pictures': pics}
os.makedirs(F + '/work/jobs', exist_ok=True)
import sys
tag = sys.argv[1] if len(sys.argv) > 1 else 'prev1'
for look in ('real', 'painted'):
    json.dump(preview(look, tag), open(f'{F}/work/jobs/{tag}_{look}.json', 'w'), indent=1)
print('written', tag)
