import sys, json, math
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import numpy as np, bpy
import place_kit as pk
from place_kit import parts
from place_kit.wear import masks
parts.refresh_ground()
m = masks.load_plan_masks()
out = {'masks_in_file': m is not None}
if m is not None:
    out['cell'] = m.cell; out['shape'] = list(m.shape)
    road = [[-140, -34], [-110, -18], [-80, -6], [-45, -1.5], [-12, 0.5], [20, 2], [52, -2.5], [85, -10], [115, -19], [140, -33]]
    # points on a wheel track: x=-30 centre y plus 0.7 normal
    def road_y(x):
        for a, b in zip(road[:-1], road[1:]):
            if a[0] <= x <= b[0]: return a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
    cy = road_y(-30.0)
    tests = {'wheel track (x -30, +0.7 from the centre)': (-30.0, cy + 0.7), 'wheel track (other rut)': (-30.0, cy - 0.7), 'crown centre': (-30.0, cy), 'verge 3.3 m from the centre': (-30.0, cy + 3.3),
             'meadow, 12 m north of the road': (-30.0, cy + 12), 'doorway zone': (24.0, 35.5), 'yard middle': (24.5, 28.0), 'forest, 60 m out': (-100.0, 80.0)}
    out['is_keep_clear'] = {k: bool(pk.is_keep_clear(x, y)) for k, (x, y) in tests.items()}
    out['track_mask'] = {k: round(float(m.sample('track', [[x, y]])[0]), 2) for k, (x, y) in tests.items()}
print('KEEPCLEAR', json.dumps(out))
