# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Measures the pictures of the EEVEE / Cycles pairs (plain Python with numpy and OpenCV; no Blender). For every picture:
#   mean_L / median_L   brightness of the finished 8-bit picture, L = 0.2126 R + 0.7152 G + 0.0722 B (0 black, 1 white), the same L the sett measures use
#   blown / crushed     share of dots with L over 0.97 / under 0.02
#   road_L, puddle_L    mean brightness of the road dots (mask picture) and of the road dots under puddles (puddle mask picture)   [where masks exist]
#   the sett joint measures of the job, unchanged: the study's "joint contrast" (b04_measure_joints.measure, with the pass line of b09) and the rubbish job's second measure
#   (measure_grid_visibility.grid_visibility). Dots under puddles (grown by two dots) and dots on rubbish (rubbish mask over 0.3, grown by two dots) are left out, as the rubbish job does.
# Use: python3 -I measure_pairs.py WORK_OUT_FOLDER LABEL:w:h:name[,name...] ...      e.g.  measure_pairs.py runA/out main:1080:1920:main_today_eevee,main_today_cycles
# Writes WORK_OUT_FOLDER/pair_measurements.json and prints a table.
import json
import os
import sys

import cv2
import numpy as np

BASE = 'proc-work/street_wet/relief_and_rubbish'
sys.path.insert(0, BASE + '/study/tools')
sys.path.insert(0, BASE + '/setts/tools')
sys.dont_write_bytecode = True
from b04_measure_joints import luminance, measure, load_mask  # noqa: E402
from b09_lighting_test_set import PASS, judge  # noqa: E402
from measure_grid_visibility import grid_visibility, visible  # noqa: E402


def read_raw_red(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    scale = 65535.0 if image.dtype == np.uint16 else 255.0
    return image[..., 2].astype(np.float32) / scale        # OpenCV reads BGR: index 2 is red


def read_puddles(path):
    wet = (read_raw_red(path) > 0.5).astype(np.uint8)
    return cv2.dilate(wet, np.ones((5, 5), np.uint8)) > 0


def analyse(folder, label, w, h, name, puddle_name=None, dirt_name=None):
    png = os.path.join(folder, name + '.png')
    L = luminance(png)
    out = dict(name=name, w=w, h=h, mean_L=round(float(L.mean()), 4), median_L=round(float(np.median(L)), 4), blown=round(float((L > 0.97).mean()), 5), crushed=round(float((L < 0.02).mean()), 5),
               blown_dots=int((L > 0.97).sum()), crushed_dots=int((L < 0.02).sum()), dots=int(L.size))
    rgb = cv2.imread(png)[..., ::-1].astype(np.float32).reshape(-1, 3).mean(0) / 255
    out['mean_rgb'] = [round(float(v), 4) for v in rgb]
    mask = os.path.join(folder, f'mask_{label}_{w}x{h}.png')
    if os.path.exists(mask) and label in PASS:
        J, S, R = load_mask(mask)
        road = R > 0.99
        out['road_L'] = round(float(L[road].mean()), 4)
        puddles = None
        if puddle_name and os.path.exists(os.path.join(folder, puddle_name + '.png')):
            puddles = read_puddles(os.path.join(folder, puddle_name + '.png'))
            out['puddle_share_of_road'] = round(float((puddles & road).sum() / max(1, road.sum())), 3)
            under = (read_raw_red(os.path.join(folder, puddle_name + '.png')) > 0.5) & road
            out['puddle_L'] = round(float(L[under].mean()), 4) if under.any() else None
            out['road_dry_part_L'] = round(float(L[road & ~puddles].mean()), 4)
        exclude = puddles if puddles is not None else np.zeros(road.shape, bool)
        dirt = None
        if dirt_name and os.path.exists(os.path.join(folder, dirt_name + '.png')):
            on = read_raw_red(os.path.join(folder, dirt_name + '.png')) > 0.3
            ground = os.path.join(folder, f'ground_{label}_{w}x{h}.png')
            if os.path.exists(ground):
                on &= read_raw_red(ground) > 0.5
            dirt = cv2.dilate(on.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            exclude = exclude | dirt
            out['dirt_share_of_road'] = round(float((dirt & road).sum() / max(1, road.sum())), 3)
        joint = measure(png, mask, puddles=exclude)
        out['joint'] = {b: joint[b] for b in ('near', 'middle', 'far') if b in joint}
        ok, reasons = judge(joint, label)
        out['joint_pass_line'] = 'pass' if ok else 'FAIL: ' + '; '.join(reasons)
        grid = grid_visibility(png, mask, exclude)
        out['grid'] = grid
        out['grid_visible'] = {b: bool(visible(grid[b])) for b in ('near', 'middle')}
    return out


def main():
    folder = sys.argv[1]
    result = {}
    for spec in sys.argv[2:]:
        label, w, h, names = spec.split(':')
        puddle_name = f'{label}_wet_puddlemask'
        dirt_name = f'{label}_wet_dirt'
        for name in names.split(','):
            result[name] = analyse(folder, label, int(w), int(h), name, puddle_name, dirt_name)
    json.dump(result, open(os.path.join(folder, 'pair_measurements.json'), 'w'), indent=1)
    print(f"{'picture':34s} {'meanL':>6s} {'blown%':>7s} {'crush%':>7s} {'roadL':>6s} {'pudL':>6s} | near c/delta/seen/grid | middle c/delta/seen/grid | pass-line")
    for name, r in result.items():
        j = r.get('joint')
        if j:
            def cell(b):
                e = j[b]
                g = r['grid'][b]
                return 'n/a' if e['contrast'] is None else f"{e['contrast']:.2f}/{e['delta']:.3f}/{e['seen']:.2f}/{g['line']}"
            print(f"{name:34s} {r['mean_L']:6.3f} {100 * r['blown']:7.3f} {100 * r['crushed']:7.3f} {r.get('road_L', 0):6.3f} {str(r.get('puddle_L')):>6s} | {cell('near'):>22s} | {cell('middle'):>22s} | {r['joint_pass_line'][:60]}")
        else:
            print(f"{name:34s} {r['mean_L']:6.3f} {100 * r['blown']:7.3f} {100 * r['crushed']:7.3f}")


if __name__ == '__main__':
    main()
