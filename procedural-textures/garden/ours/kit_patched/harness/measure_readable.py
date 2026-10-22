# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P3 (each element is readable at the painter's size). For each element in the look's `readable` table (presets/<look>.json -> "readable": [...]) it takes the plate picture and the
# element's own mask picture (layer_<key>_plate_<camera>.png, drawn by the runner), keeps only the part of the mask inside the element's design zone (a surface class and/or the
# first N metres by the depth picture), and runs the painted-look study's plate_detail_check.py (copied here with its fit, unchanged) on every separate mark: width, contrast, surround
# brightness and GOOD / RISKY / LOST at the painter scale (0.45; 0.40 also reported). Then: share GOOD at least 60 %, LOST at most 15 %, crushed (a dark mark on a surround under 0.12)
# at most 15 %, and at least the minimum count of GOOD marks (half on the second plate).
# A table row: {"element": name, "layer": key, "plates": [camera names of the set's plates], "zone": {"class": "walls", "max_m": 20}, "min_good": 15, "min_good_second_plate": 7,
#               "smallest": [width_dots, contrast]}     ("smallest" is documentation of the design size; the pass test is the three shares and the count)
# Use:   python3 -I measure_readable.py SET_ID FOLDER [--look sooty_1926] [--scale 0.45] [--out result.json]
import importlib.util
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('plate_detail_check', os.path.join(HERE, 'plate_detail_check.py'))
pdc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pdc)


def check_element(plate_png, mask_array, scale=0.45):
    """The study's per-mark measure on one mask (a bool array the size of the plate picture). Returns the summary dict (same numbers as plate_detail_check.py's report)."""
    rgb, k = pdc.load_plate(plate_png)
    A = pdc.lum(rgb)
    import cv2
    mask = cv2.resize(mask_array.astype(np.uint8), (A.shape[1], A.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    lab, items, m = pdc.find_marks(A, mask=mask)
    rows = pdc.measure(A, lab, items, mask)
    for r in rows:
        r['p_back'] = round(pdc.p_back(r['kind'], r['width_px'], r['contrast'], scale), 2)
        r['verdict'] = pdc.verdict(r['p_back'])
        r['dark_surround'] = bool(r['surround'] < 0.12 and r['sign'] == 'dark')
    n = len(rows)
    out = dict(marks=n, good=sum(r['verdict'] == 'GOOD' for r in rows), risky=sum(r['verdict'] == 'RISKY' for r in rows), lost=sum(r['verdict'] == 'LOST' for r in rows),
               crushed=sum(r['dark_surround'] for r in rows))
    out['share_good'] = round(out['good'] / n, 3) if n else None
    out['share_lost'] = round(out['lost'] / n, 3) if n else None
    out['share_crushed'] = round(out['crushed'] / n, 3) if n else None
    return out, rows


def run(settings, folder, look, scale=0.45, plates=None):
    table = look.get('readable', []) if isinstance(look, dict) else []
    classes = mc.classes(settings)
    ts = settings.get('test_set') or {}
    out = {'elements': {}, 'scale': scale}
    for row in table:
        plate_names = row.get('plates', ['main'])
        for index, camera in enumerate(plate_names):
            tag = f'{row["element"]}@{camera}'
            plate_entry = next((p for p in mc.plate_list(settings) if p[0] == camera), None)
            if plate_entry is None:
                out['elements'][tag] = {'skipped': 'no such plate'}
                continue
            _, light, state, scene_id, w, h = plate_entry
            plate_png = mc.pic(folder, f'plate_{camera}_{light}_{state}')
            mask_png = mc.pic(folder, f'layer_{row["layer"]}_plate_{camera}')
            if not (plate_png and mask_png):
                out['elements'][tag] = {'skipped': 'plate or mask picture missing'}
                continue
            mask = mc.read_channel(mask_png, 0) > 0.5
            zone = row.get('zone') or {}
            cp, dp = mc.pic(folder, f'class_{camera}_{w}x{h}'), mc.pic(folder, f'depth_{camera}_{w}x{h}')
            if zone.get('class') and cp:
                mask &= mc.class_mask(mc.read_class(cp), classes[zone['class']])
            if zone.get('max_m') and dp:
                mask &= mc.read_depth(dp) <= zone['max_m']
            summary, rows = check_element(plate_png, mask, scale)
            need_good = row.get('min_good', 0) if index == 0 else row.get('min_good_second_plate', row.get('min_good', 0) / 2)
            fails = []
            if summary['marks'] == 0 or summary['good'] < need_good:
                fails.append(f'{summary["good"]} GOOD marks, need {need_good:g}')
            if summary['marks']:
                if summary['share_good'] < 0.60:
                    fails.append(f'GOOD share {summary["share_good"]:.0%} below 60 %')
                if summary['share_lost'] > 0.15:
                    fails.append(f'LOST share {summary["share_lost"]:.0%} above 15 %')
                if summary['share_crushed'] > 0.15:
                    fails.append(f'crushed share {summary["share_crushed"]:.0%} above 15 %')
            summary.update(passed=not fails, failures=fails)
            out['elements'][tag] = summary
    out['passed'] = all(e.get('passed', True) for e in out['elements'].values() if 'skipped' not in e)
    out['skipped'] = sorted(t for t, e in out['elements'].items() if 'skipped' in e)
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    settings = mc.load_set(args[0])
    look = json.load(open(os.path.join(mc.KIT_ROOT, 'presets', opts.get('--look', 'sooty_1926') + '.json')))
    result = run(settings, args[1], look, float(opts.get('--scale', 0.45)))
    if '--out' in opts:
        mc.jdump(result, opts['--out'])
    print(json.dumps(result, indent=1))
