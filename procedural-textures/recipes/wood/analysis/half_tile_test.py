# What this does (plain words): the HALF-TILE SHIFT TEST for seamless tiles. Compares a picture baked with the whole pattern slid by half a tile (--shift 0.5 0.5) with the
# normal bake rolled by half a tile. If the tile repeats exactly, they are the same picture (small differences only where hard edges fall on different dots). A
# deliberately WRONG roll (a third of a tile) is measured as a control: it must differ a lot. Also reports the jump across the wrap-around edge against a normal jump.
# Use: python3 -I half_tile_test.py NORMAL_FOLDER SHIFTED_FOLDER [--json out.json]. Plain Python.
import json, os, sys
import cv2
import numpy as np
a = cv2.imread(os.path.join(sys.argv[1], 'colour.png')).astype(np.float64)
b = cv2.imread(os.path.join(sys.argv[2], 'colour.png')).astype(np.float64)
h, w = a.shape[:2]
def stats(x, y):
    d = np.abs(x - y).mean(axis=-1)
    return {'mean_difference_levels': round(float(d.mean()), 3), 'share_over_40_levels': round(float((d > 40).mean()), 5)}
right = stats(np.roll(a, (h // 2, w // 2), axis=(0, 1)), b)
wrong = stats(np.roll(a, (h // 3, w // 3), axis=(0, 1)), b)
def edge_jump(x):
    g = x.mean(axis=-1)
    inner = np.abs(np.diff(g, axis=1)).mean()
    across = np.abs(g[:, 0] - g[:, -1]).mean()
    inner_v = np.abs(np.diff(g, axis=0)).mean(); across_v = np.abs(g[0] - g[-1]).mean()
    return round(float(across / inner), 2), round(float(across_v / inner_v), 2)
result = {'half_tile_roll': right, 'wrong_roll_control': wrong, 'edge_jump_over_normal_jump_left_right_and_top_bottom': edge_jump(a)}
print(json.dumps(result))
if '--json' in sys.argv:
    json.dump(result, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
