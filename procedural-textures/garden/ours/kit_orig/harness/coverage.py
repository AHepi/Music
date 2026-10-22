# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P4 (b) the SHARES: how much of each surface class each element covers, from the layers' own mask pictures (layer_<key>_<label>_<state>.png from the three cameras; the pictures are
# plain light, raw numbers) cut up by the class picture of the same camera. The look's `period` table lists the caps:
#   {"element": name, "layer": key, "class": "walls", "measure": "area_share", "cap": [lo, hi], "note": "..."}   area share of the class's dots with mask above 0.5 (inside max_m if given)
#   {"element": name, "measure": "not_automated", "note": "how a person checks it"}                                counted by eye or by a builder's own feature report
# shares(...) is the plain function; run(...) goes through the table. The number reported is the mean of the cameras that see the class (at least 2000 dots of it), each camera also
# listed; a number outside its cap fails (the cameras are listed so one can see which).
# Use:   python3 -I coverage.py SET_ID FOLDER [--look sooty_1926] [--out result.json]
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402


def shares(mask, class_map, class_ids, depth=None, max_m=None, threshold=0.5):
    """Share of the class's dots (optionally nearer than max_m) whose mask value is above threshold; returns (share, dots of the class)."""
    zone = mc.class_mask(class_map, class_ids)
    if max_m is not None and depth is not None:
        zone &= depth <= max_m
    n = int(zone.sum())
    return (float((mask[zone] > threshold).mean()) if n else None), n


def run(settings, folder, look):
    classes = mc.classes(settings)
    out = {'elements': {}, 'passed': True}
    cams = []
    for label, light, state, scene_id in mc.t22_list(settings):
        if state == 'wet' and (label, state) not in [(c[0], c[1]) for c in cams]:
            cams.append((label, state))
    for row in look.get('period', []):
        if row.get('measure') != 'area_share':
            out['elements'][row['element']] = {'skipped': row.get('note', 'not automated')}
            continue
        per_camera, values = {}, []
        for label, state in cams:
            w, h = mc.size_of(settings, label)
            camera = mc.camera_of(settings, label)
            mp = mc.pic(folder, f'layer_{row["layer"]}_{label}_{state}')
            cp = mc.pic(folder, f'class_{camera}_{w}x{h}')
            dp = mc.pic(folder, f'depth_{camera}_{w}x{h}')
            if not (mp and cp):
                continue
            share, n = shares(mc.read_channel(mp, 0), mc.read_class(cp), classes[row['class']], mc.read_depth(dp) if dp else None, row.get('max_m'))
            if share is not None and n >= 2000:
                per_camera[label] = round(share, 4)
                values.append(share)
        if not values:
            out['elements'][row['element']] = {'skipped': 'no mask pictures for this layer yet'}
            continue
        mean = float(np.mean(values))
        lo, hi = row['cap']
        ok = lo <= mean <= hi
        out['elements'][row['element']] = dict(share=round(mean, 4), cap=[lo, hi], passed=ok, per_camera=per_camera)
        out['passed'] &= ok
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    settings = mc.load_set(args[0])
    look = json.load(open(os.path.join(mc.KIT_ROOT, 'presets', opts.get('--look', 'sooty_1926') + '.json')))
    result = run(settings, args[1], look)
    if '--out' in opts:
        mc.jdump(result, opts['--out'])
    print(json.dumps(result, indent=1))
