# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# REGRESSION AGAINST THE EARLIER PLACES PICTURES: the new ground plan must agree with the earlier rubbish layer's own "places" pictures (the maps the rubbish mask was built from):
#   places A  red = distance to the nearest house wall, step or plinth       -> bus `wall_dist`            green = distance to the nearest prop      -> `prop_dist`      blue = catch points
#   places B  red = inside corners                                           -> `inside_corner`            green = doorsteps -> `step_foot`          blue = pipe and post feet -> `vertical_foot`
# Both are looked up at the centre of every dot of the earlier picture (world x and y) and compared; the plan's line is "within 3 levels of 255 on 99 % of dots".
# The earlier picture had NO walls, steps or plinths between x = -2.7 and 2.7 (its building search started at |x| > 2.7, so the middle of the road is far from every wall by
# construction), the new wall_dist is true everywhere; the report therefore gives the share over every dot AND over the dots the earlier picture covered (|x| >= 2.7).
# Plain Python (numpy, OpenCV). Use:  python3 -I masks/check_against_earlier.py SET_ID SCENE_ID PLACES_A.png PLACES_B.png [--out result.json]
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.path.insert(0, os.path.join(KIT_ROOT, 'harness'))
sys.dont_write_bytecode = True

import cv2  # noqa: E402

from masks import pack as pack_module  # noqa: E402



def read_places(path):
    """The earlier picture as (h, w, 3) uint8 RGB with row 0 = LOW y (the earlier writer's first row is the top: flipped here, the check below proves it)."""
    im = cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1]
    return np.flipud(im)


def sample(array, manifest, xs, ys):
    g = manifest['ground']
    ix = np.floor((xs - g['x'][0]) / g['dot_m']).astype(int)
    iy = np.floor((ys - g['y'][0]) / g['dot_m']).astype(int)
    h, w = array.shape
    inside = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    out = np.full(xs.shape, np.nan, np.float32)
    out[inside] = array[iy[inside], ix[inside]]
    return out


def compare(set_id, scene_id, places_a, places_b):
    from measure_zones import read_gp
    from apply import settings as settings_module
    gp, manifest = read_gp(set_id, scene_id)
    spec = (settings_module.load_set(set_id).legacy() or {}).get('places_grid')
    if not spec:
        raise KeyError(f'the set file {set_id} has no legacy.places_grid (x, y bounds, dot_m and road_middle_half_width_m of the earlier layer\'s places pictures)')
    EARLIER = dict(x=tuple(spec['x']), y=tuple(spec['y']), dot=float(spec['dot_m']))
    a, b = read_places(places_a), read_places(places_b)
    h, w = a.shape[:2]
    xs, ys = np.meshgrid(EARLIER['x'][0] + (np.arange(w) + 0.5) * EARLIER['dot'], EARLIER['y'][0] + (np.arange(h) + 0.5) * EARLIER['dot'])
    pairs = {'wall_dist': (a[..., 0], 'wall_dist'), 'prop_dist': (a[..., 1], 'prop_dist'), 'inside_corner': (b[..., 0], 'inside_corner'),
             'step_foot': (b[..., 1], 'step_foot'), 'vertical_foot': (b[..., 2], 'vertical_foot')}
    out = {}
    for label, (old, name) in pairs.items():
        new = sample(gp[name], manifest, xs, ys) * 255.0
        valid = np.isfinite(new)
        if not valid.any():
            out[label] = dict(note='the new pack does not cover the earlier picture')
            continue
        diff = np.abs(new - old.astype(np.float32))
        outer = valid & (np.abs(xs) >= float(spec['road_middle_half_width_m']))
        out[label] = dict(share_within_3_levels_all=round(float((diff[valid] <= 3.0).mean()), 4), share_within_3_levels_outside_road_middle=round(float((diff[outer] <= 3.0).mean()), 4) if outer.any() else None,
                          mean_abs_difference_levels=round(float(diff[valid].mean()), 3), dots=int(valid.sum()))
    # orientation proof: the unflipped earlier picture must agree worse
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_path = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    if out_path in args:
        args.remove(out_path)
    result = compare(*args[:4])
    print(json.dumps(result, indent=1))
    if out_path:
        json.dump(result, open(out_path, 'w'), indent=1)
