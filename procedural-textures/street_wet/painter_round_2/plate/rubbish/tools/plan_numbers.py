# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Measures the RUBBISH MASK ITSELF from a plan picture (the mask seen straight from above, written by the picture runner as plantotal_*.png: grey = how much rubbish, 0 none, 1 most; the street
# from y = -12 to 72 m, 4 cm a dot, 225 dots across for x = -4.5 to 4.5 m). It reports, per ZONE of the street, how much of the ground is rubbish:
#     crown       |x| under 1.3 m (the middle of the road): must be 0 (the rubbish never sits on the crown), except round props
#     road        |x| under 2.2 (all the setts)          gutter   2.2 to 2.5 (the channel stones)          kerb and pavement  2.5 to 3.4          wall strip  over 3.4 (the foot of the walls)
# and for each zone: the mean mask, the share of ground with the mask above 0.1 ("some rubbish") and above 0.3 ("clearly rubbish"). Only y from 0 to 45 m (the part the cameras see) is counted.
# With a second picture (the same street with the props), it also says where the extra rubbish is (the "prop zones") and whether the crown outside them is still clean.
# Use: python3 -I plan_numbers.py PLAN_STREET.png [PLAN_LOCKOUT.png] OUT.json
import json
import sys

import cv2
import numpy as np

X0, DOT, Y1 = -4.5, 0.04, 72.0


def load(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    scale = 65535.0 if image.dtype == np.uint16 else 255.0
    return image[..., 2].astype(np.float32) / scale        # red channel (the three channels are the same in 'total' mode)


def zones(mask):
    h, w = mask.shape
    x = X0 + (np.arange(w) + 0.5) * DOT
    y = Y1 - (np.arange(h) + 0.5) * DOT
    ax = np.abs(x)[None, :] + 0 * y[:, None]
    yy = y[:, None] + 0 * x[None, :]
    in_view = (yy >= 0.0) & (yy <= 45.0)
    spec = {'crown (|x| < 1.3)': ax < 1.3, 'road (|x| < 2.2)': ax < 2.2, 'gutter (2.2 to 2.5)': (ax >= 2.2) & (ax < 2.5), 'kerb and pavement (2.5 to 3.4)': (ax >= 2.5) & (ax < 3.4),
            'wall strip (3.4 to 4.4)': (ax >= 3.4) & (ax <= 4.4)}
    return {name: (sel & in_view) for name, sel in spec.items()}


def stats(mask, selection, exclude=None):
    sel = selection if exclude is None else selection & ~exclude
    v = mask[sel]
    return dict(mean=round(float(v.mean()), 4), share_over_0_1=round(float((v > 0.1).mean()), 4), share_over_0_3=round(float((v > 0.3).mean()), 4), dots=int(sel.sum()))


def main():
    args = sys.argv[1:]
    street = load(args[0])
    result = {'street_copy': {name: stats(street, sel) for name, sel in zones(street).items()}}
    if len(args) == 3:
        lockout = load(args[1])
        props_zone = (lockout - street) > 0.05
        props_zone = cv2.dilate(props_zone.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        result['lockout_file'] = {name: stats(lockout, sel) for name, sel in zones(lockout).items()}
        result['lockout_file_outside_the_prop_zones'] = {name: stats(lockout, sel, exclude=props_zone) for name, sel in zones(lockout).items()}
        h, w = lockout.shape
        xs = X0 + (np.arange(w) + 0.5) * DOT
        ys = Y1 - (np.arange(h) + 0.5) * DOT
        ground = (np.abs(xs)[None, :] <= 4.4) & ((ys >= 0.0) & (ys <= 45.0))[:, None]
        result['prop_zone_share_of_ground_0_to_45m'] = round(float((props_zone & ground).sum() / ground.sum()), 4)
    json.dump(result, open(args[-1], 'w'), indent=1)
    for key, table in result.items():
        if isinstance(table, dict):
            print(key)
            for name, s in table.items():
                print(f"  {name:34s} mean {s['mean']:.3f}  over 0.1: {s['share_over_0_1']:.3f}  over 0.3: {s['share_over_0_3']:.3f}")


main()
