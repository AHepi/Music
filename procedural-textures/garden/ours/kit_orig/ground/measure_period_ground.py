# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P4 SHARES OF THE GROUND LAYERS' OWN ELEMENTS against the period caps, counted on the plan pictures (straight from above, ground/plan_views.py), so they do not depend on a camera.
#     python3 -I ground/measure_period_ground.py SET_ID PLAN_FOLDER [--out result.json]
# The rows are the set's ground section ("period": [...]) and copy the caps of the look's `period` table (presets/<look>.json). A row says what to count:
#   {"element", "kind": "share",        "part": "layer:part", "over": [class names], "minus": "layer:part" (optional: left out of the class area), "zone_y": [lo, hi], "cap": [lo, hi]}
#         share of the class's dots (minus the `minus` part) whose part picture is above 0.5
#   {"element", "kind": "length_share", "part": "layer:part", "over": [class names], "cap": [lo, hi]}
#         share of the class's length along the plan picture (2 cm rows) that holds at least one dot of the part, each side of the picture on its own and the mean
#   {"element", "kind": "count",        "part": "layer:part", "zone_y": [lo, hi], "over": [class names], "cap": [lo, hi]}      number of separate patches of the part
# The plan pictures are 8 bit, so a mark thinner than one plan dot (2 cm) is counted at its covered share (the threshold 0.5 is applied to the picture as drawn).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.path.insert(0, os.path.join(KIT_ROOT, 'harness'))
sys.dont_write_bytecode = True

import measure_common as mc  # noqa: E402
from ground import ground_names as gc  # noqa: E402


def load(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a is None:
        return None
    if a.ndim == 3:
        a = a[..., 0]
    return a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)


def part_picture(plan, spec):
    return load(os.path.join(plan, 'plan_' + spec.replace(':', '_') + '.png'))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_path = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    if out_path and out_path in args:
        args.remove(out_path)
    set_id, plan = args[0], args[1]
    settings = mc.load_set(set_id)
    section = gc.ground_section(settings)
    info = json.load(open(os.path.join(plan, 'plan_info.json')))
    y0, y1 = info['ground_bounds']['y']
    h = info['size'][1]
    dot = (y1 - y0) / h
    y_of_row = y1 - (np.arange(h) + 0.5) * dot
    classes = mc.classes(settings)
    cmap = np.round(load(os.path.join(plan, 'plan_class.png')) * 64.0).astype(int)
    xs = np.arange(info['size'][0])
    results = []
    for row in section.get('period', []):
        picture = part_picture(plan, row['part'])
        entry = dict(element=row['element'], cap=row.get('cap'), kind=row['kind'], part=row['part'])
        if picture is None:
            entry.update(skipped='plan picture missing')
            results.append(entry)
            continue
        ids = sorted({i for c in row.get('over', []) for i in classes.get(c, [])})
        zone = np.isin(cmap, ids)
        lo, hi = row.get('zone_y', [y0, y1])
        zone &= ((y_of_row >= lo) & (y_of_row <= hi))[:, None]
        mark = picture > 0.5
        if row['kind'] == 'share':
            area = zone.copy()
            if row.get('of'):
                area &= part_picture(plan, row['of']) > 0.5
            if row.get('minus'):
                other = part_picture(plan, row['minus'])
                area &= ~(other > 0.5)
            value = float((mark & area).sum() / max(area.sum(), 1))
        elif row['kind'] == 'length_share':
            sides = []
            for side in (xs < info['size'][0] // 2, xs >= info['size'][0] // 2):
                z = zone & side[None, :]
                rows_with = z.any(axis=1)
                got = (mark & z).any(axis=1)
                sides.append(float(got.sum() / max(rows_with.sum(), 1)))
            value = float(np.mean(sides))
            entry['sides'] = [round(s, 4) for s in sides]
        elif row['kind'] == 'count':
            m = (mark & zone) if ids else (mark & ((y_of_row >= lo) & (y_of_row <= hi))[:, None])
            m = cv2.dilate(m.astype(np.uint8), np.ones((9, 9), np.uint8))
            n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
            value = int(sum(1 for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 40))
        else:
            continue
        entry['value'] = round(value, 4) if isinstance(value, float) else value
        if row.get('cap'):
            entry['inside_cap'] = bool(row['cap'][0] <= value <= row['cap'][1])
        results.append(entry)
    out = dict(rows=results, all_inside=all(r.get('inside_cap', True) for r in results))
    if out_path:
        json.dump(out, open(out_path, 'w'), indent=1)
    for r in results:
        print(f'{r["element"]:58s} {r.get("value", r.get("skipped")):>8}  cap {r["cap"]}  {"OK" if r.get("inside_cap") else "OUTSIDE" if "inside_cap" in r else ""}')


if __name__ == '__main__':
    main()
