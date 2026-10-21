# What this file does (plain words): numbers that say how each layer (WETNESS, JOINTS, RUBBISH) shows up in EEVEE and in Cycles, from the pictures of runs A and B (plain Python, no Blender).
# Use: python3 -I layer_numbers.py   -> prints a table and writes work/layer_numbers.json
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, '..', 'work'))
sys.path.insert(0, 'proc-work/street_wet/relief_and_rubbish/study/tools')
from b04_measure_joints import luminance, load_mask
sys.dont_write_bytecode = True

def red(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED); s = 65535.0 if im.dtype == np.uint16 else 255.0
    return im[..., 2].astype(np.float32) / s

out = {}
# 1. wetness: dry -> wet on the main street, road dots, per engine
A = W + '/runA/out/'
J, S, R = load_mask(A + 'mask_main_1080x1920.png'); road = R > 0.99
pud = cv2.dilate((red(A + 'main_wet_puddlemask.png') > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
for eng in ('eevee', 'cycles'):
    d, w, t = (luminance(A + f'main_{s}_{eng}.png') for s in ('dry', 'wet', 'today'))
    out[f'wetness_main_{eng}'] = dict(road_today=round(float(t[road].mean()), 4), road_dry=round(float(d[road].mean()), 4), road_wet=round(float(w[road].mean()), 4), wet_over_dry=round(float(w[road].mean() / d[road].mean()), 2),
                                      road_wet_outside_puddles=round(float(w[road & ~pud].mean()), 4), road_dry_same_dots=round(float(d[road & ~pud].mean()), 4), puddle_dots_wet=round(float(w[road & pud].mean()), 4), puddle_dots_dry_same_dots=round(float(d[road & pud].mean()), 4),
                                      whole_today=round(float(t.mean()), 4), whole_dry=round(float(d.mean()), 4), whole_wet=round(float(w.mean()), 4))
# 2. rubbish: joints-only -> rubbish, lockout wet, per engine
B = W + '/runB/out/'
J, S, R = load_mask(B + 'mask_lockout_1536x2730.png'); road = R > 0.99
ground = red(B + 'ground_lockout_1536x2730.png') > 0.5
dirt_raw = (red(B + 'lockout_wet_dirt.png') > 0.3) & ground
near_dirt = cv2.dilate(dirt_raw.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
pud = cv2.dilate((red(B + 'lockout_wet_puddlemask.png') > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
inside = dirt_raw & road
outside = road & ~near_dirt & ~pud
for eng in ('eevee', 'cycles'):
    a, b, c = luminance(B + f'lockout_wet_{eng}.png'), luminance(B + f'lockout_wet_joints_{eng}.png'), luminance(B + f'lockout_wet_round2_{eng}.png')
    d = np.abs(a - b)
    out[f'rubbish_lockout_{eng}'] = dict(dirt_share_of_road=round(float(inside.sum() / road.sum()), 3), diff_in_dirt=round(float(d[inside].mean()), 4), changed_in_dirt_over_0_02=round(float((d[inside] > 0.02).mean()), 3),
                                          diff_outside_dirt=round(float(d[outside].mean()), 5), mean_L_rubbish=round(float(a.mean()), 4), mean_L_joints_only=round(float(b.mean()), 4), mean_L_round2=round(float(c.mean()), 4),
                                          road_L_round2=round(float(c[road].mean()), 4), road_L_joints=round(float(b[road].mean()), 4), road_L_rubbish=round(float(a[road].mean()), 4))
json.dump(out, open(W + '/layer_numbers.json', 'w'), indent=1)
for k, v in out.items():
    print(k, json.dumps(v))
