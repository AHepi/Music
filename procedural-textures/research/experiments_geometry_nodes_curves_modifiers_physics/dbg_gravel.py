import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt, recipe_gravel_rigidbody as rg
gt.new_scene(64)
p = {**rg.DEFAULTS, 'big': 10, 'medium': 50, 'small': 120, 'tiny': 0, 'frames': 150, 'ghosts': os.environ.get('GHOSTS','1')=='1', **json.loads(os.environ.get('EXTRA','{}'))}
rng = np.random.default_rng(p['seed'])
shapes = rg.make_stone_shapes(rng, p['variants'])
stones = rg.stone_list(rng, p)
rg.place_without_overlap(rng, stones, p['max_drop_height'])
print('start z range', min(s['start'][2] for s in stones), max(s['start'][2] for s in stones))
log = {}
objs = rg.run_physics(p, rng, shapes, stones, log)
print(log)
bad = [(i, s['kind'], round(float(s['start'][2]),2), round(float(s['final_location'][2]),2), objs[i].rigid_body is not None) for i, s in enumerate(stones) if s['final_location'][2] > 3 or s['final_location'][2] < -0.3]
print('suspicious stones (index, kind, start z, final z, has rigid body):', bad[:20], len(bad))
zs = np.array([s['final_location'][2] for s in stones]); print('final z percentiles', np.percentile(zs, [0, 5, 50, 95, 100]).round(2))
