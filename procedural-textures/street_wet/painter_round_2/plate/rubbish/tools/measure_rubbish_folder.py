# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Measures the pictures a run of rubbish_runner.py drew (plain Python with numpy and OpenCV; no Blender), and turns the PNG pictures into smaller JPEG files for looking.
# It measures TWO things:
#  1. THE SETTS' 3D LOOK (the study's "joint contrast", unchanged, see study/tools/b04_measure_joints.py): how much darker a joint between the setts is than the stone beside it, in the near
#     and middle bands of the road, with the study's PASS LINE. New here: the dots where there is rubbish (the rubbish mask above 0.3, grown by two dots, on the ground) are left out, together
#     with the dots under puddles, because rubbish lies over joints on purpose; the table says how much of the road that was ("dirt_share").
#  2. THE RUBBISH ITSELF, for every picture of the look "rubbish" that has a twin of the look "joints" (same name with _joints instead of _rubbish):
#       diff_in_dirt     average brightness change (0..1) on road dots where the rubbish mask is above 0.3
#       changed_in_dirt  the share of those dots that changed by more than 0.02 (the rubbish can be SEEN there)
#       diff_outside     average change on road dots farther than 15 dots from any rubbish: it should be about 0 (the clean road is untouched; only the small shadows and reflections of pieces)
#       crown_clean      nothing here by itself (see the plan measure)
#     and, for plan pictures (view "plan", mask drawn from above), the share of the ground that is rubbish by zone (see plan_numbers()).
# Run: python3 -I measure_rubbish_folder.py FOLDER JOB_FILE [JOB_FILE ...] [--convert]
# Writes FOLDER/measurements.json (joint numbers), FOLDER/rubbish_numbers.json, prints two tables, and with --convert makes JPEGs (92) from the big PNG pictures and deletes the PNG
# (masks and the checking pictures *_dirt.png, *_puddlemask.png stay as PNG).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY_TOOLS = os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools'))
sys.path.insert(0, STUDY_TOOLS)
sys.dont_write_bytecode = True
from b04_measure_joints import luminance, measure, load_mask  # noqa: E402
from b09_lighting_test_set import PASS, judge  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
convert = '--convert' in sys.argv
folder, job_files = args[0], args[1:]
jobs = {}
for jf in job_files:
    for j in json.load(open(jf))['jobs']:
        jobs[j['name']] = j
LABEL = {'main': 'main', 'close_road': 'close', 'lockout': 'lockout'}


def exists(name):
    return os.path.exists(os.path.join(folder, name))


def read_raw_red(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    scale = 65535.0 if image.dtype == np.uint16 else 255.0
    return image[..., 2].astype(np.float32) / scale        # OpenCV reads BGR: index 2 is red


def read_puddles(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    scale = 65535.0 if image.dtype == np.uint16 else 255.0
    wet = (image[..., 2].astype(np.float32) / scale > 0.5).astype(np.uint8)
    return cv2.dilate(wet, np.ones((5, 5), np.uint8)) > 0


def dirt_of(name, job):
    """The rubbish mask as a True/False picture on the ground (mask above 0.3, grown by two dots), or None when the picture has none."""
    dirt_path = os.path.join(folder, name + '_dirt.png')
    ground_path = os.path.join(folder, f"ground_{job['camera']}_{job['w']}x{job['h']}.png")
    if not os.path.exists(dirt_path):
        return None
    red = read_raw_red(dirt_path)
    on = red > 0.3
    if os.path.exists(ground_path):
        on &= read_raw_red(ground_path) > 0.5
    return cv2.dilate(on.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0


store_path = os.path.join(folder, 'measurements.json')
store = json.load(open(store_path)) if os.path.exists(store_path) else {}
rub_path = os.path.join(folder, 'rubbish_numbers.json')
rub_store = json.load(open(rub_path)) if os.path.exists(rub_path) else {}
rows = []
for name, job in jobs.items():
    if job.get('view', 'beauty') != 'beauty':
        continue
    png = os.path.join(folder, name + '.png')
    if not os.path.exists(png):
        continue
    mask = os.path.join(folder, f"mask_{job['camera']}_{job['w']}x{job['h']}.png")
    if os.path.exists(mask):
        label = LABEL.get(job['camera'])
        puddle_file = os.path.join(folder, f"{label}_A_{job['state']}_{job['w']}x{job['h']}_puddlemask.png")
        old_style = os.path.join(folder, f"{label}_A_{job['state']}_puddlemask.png")
        puddles = read_puddles(puddle_file) if os.path.exists(puddle_file) else (read_puddles(old_style) if os.path.exists(old_style) else None)
        dirt = dirt_of(name, job)
        road = load_mask(mask)[2] > 0.99
        exclude = puddles if puddles is not None else np.zeros(road.shape, bool)
        puddle_share = float((exclude & road).sum() / max(1, road.sum()))
        if dirt is not None:
            exclude = exclude | dirt
        result = measure(png, mask, puddles=exclude)
        result['puddle_share'] = round(puddle_share, 3)
        result['dirt_share'] = round(float((dirt & road).sum() / max(1, road.sum())), 3) if dirt is not None else 0.0
        result['job'] = {k: job.get(k) for k in ('camera', 'light', 'state', 'look', 'dials', 'w', 'h', 'samples')}
        if label in PASS:
            ok, reasons = judge(result, label)
            result['pass'], result['reasons'] = ok, reasons
        store[name] = result
        rows.append((name, result))
        # the rubbish itself: against the twin picture with the look "joints"
        twin = name[:-len('_rubbish')] + '_joints' if name.endswith('_rubbish') else None
        if dirt is not None and twin and os.path.exists(os.path.join(folder, twin + '.png')):
            a, b = luminance(png), luminance(os.path.join(folder, twin + '.png'))
            diff = np.abs(a - b)
            raw_dirt = read_raw_red(os.path.join(folder, name + '_dirt.png')) > 0.3
            ground_path = os.path.join(folder, f"ground_{job['camera']}_{job['w']}x{job['h']}.png")
            if os.path.exists(ground_path):
                raw_dirt &= read_raw_red(ground_path) > 0.5
            near_dirt = cv2.dilate(raw_dirt.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
            inside = raw_dirt & road
            outside = road & ~near_dirt & ~(puddles if puddles is not None else np.zeros(road.shape, bool))
            rub_store[name] = dict(dirt_share_road=round(float(inside.sum() / max(1, road.sum())), 3), diff_in_dirt=round(float(diff[inside].mean()), 4) if inside.any() else None,
                                   changed_in_dirt=round(float((diff[inside] > 0.02).mean()), 3) if inside.any() else None,
                                   diff_outside=round(float(diff[outside].mean()), 5) if outside.any() else None, road_dots=int(road.sum()))
json.dump(store, open(store_path, 'w'), indent=1)
json.dump(rub_store, open(rub_path, 'w'), indent=1)
print(f"{'picture':36s} {'puddle':>6s} {'dirt':>5s} | {'near c/delta/seen':>20s} | {'middle':>20s} | verdict")
for name, r in rows:
    cell = lambda e: 'n/a'.rjust(20) if e['contrast'] is None else f"{e['contrast']:6.2f} {e['delta']:6.3f} {e['seen']:5.2f}".rjust(20)   # noqa: E731
    print(f"{name:36s} {r['puddle_share']:6.2f} {r['dirt_share']:5.2f} | {cell(r['near'])} | {cell(r['middle'])} | {'PASS' if r.get('pass') else 'FAIL ' + '; '.join(r.get('reasons', [])[:2])}")
print()
print(f"{'rubbish picture':36s} {'dirt share of road':>18s} {'diff in dirt':>13s} {'changed':>8s} {'diff outside':>13s}")
for name, r in rub_store.items():
    print(f"{name:36s} {r['dirt_share_road']:18.3f} {str(r['diff_in_dirt']):>13s} {str(r['changed_in_dirt']):>8s} {str(r['diff_outside']):>13s}")
if convert:
    for name in jobs:
        png = os.path.join(folder, name + '.png')
        if not os.path.exists(png) or name.endswith('_dirt') or name.endswith('_puddlemask') or 'plantotal' in name or name.startswith('final_'):
            continue
        image = cv2.imread(png)
        cv2.imwrite(os.path.join(folder, name + '.jpg'), image, [cv2.IMWRITE_JPEG_QUALITY, 92])
        os.remove(png)
