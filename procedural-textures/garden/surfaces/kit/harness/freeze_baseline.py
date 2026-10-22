# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# FREEZES THE BASELINE: takes the pictures of the look `base` drawn several times (folders ROOT/r1, ROOT/r2, ROOT/r3, each holding one folder per scene file, brought back by
# run_testset.py) and writes harness/baseline/:
#     numbers.json      the frozen numbers: joint passes (three counts) with every picture's bands, wet-to-dry ratios, puddle cover, road p95 / highlight / speckle, class brightness
#                       shares of the plates (walls, trims, road, pavement ...), plate drawing times (best of the runs), the first picture's time, run times, the earlier layers' file hashes
#     pictures/<scene>/ the JPG of every picture (the 22, the close views, the plates)
#     plates/           the plate pictures, lossless (PNG), for the dot-by-dot comparisons of P5 and the hue check
#     maps/             class and depth pictures of the plates (small, 8 bit), the joint masks and the puddle / dirt / zones pictures (what a later run measures against)
# Use:   python3 -I harness/freeze_baseline.py SET_ID ROOT [--tags r1,r2,r3]
import glob
import hashlib
import json
import os
import shutil
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402
import measure_joints  # noqa: E402
import measure_mush  # noqa: E402
import measure_time  # noqa: E402
import measure_wet  # noqa: E402

OUT = os.path.join(mc.KIT_ROOT, 'harness', 'baseline')


def scene_folders(root, tag):
    return sorted(p for p in glob.glob(os.path.join(root, tag, '*')) if os.path.isdir(p) and not os.path.basename(p).startswith('_'))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    set_id, root = args[0], args[1]
    tags = (sys.argv[sys.argv.index('--tags') + 1] if '--tags' in sys.argv else 'r1,r2,r3').split(',')
    if '--tags' in sys.argv and tags[0] in args:
        args.remove(tags[0])
    settings = mc.load_set(set_id)
    folders = {t: scene_folders(root, t) for t in tags}
    first = tags[0]
    numbers = dict(schema='weathering-baseline/1', set=set_id, look='base', made=time.strftime('%Y-%m-%d %H:%M'), repeats=tags)
    # ---- joints, on every repeat (they must agree: the draws are deterministic)
    joints = {t: measure_joints.run(settings, folders[t]) for t in tags}
    numbers['joints'] = joints[first]
    agree = {}
    for t in tags[1:]:
        worst = 0.0
        for name, e in joints[first]['pictures'].items():
            if 'official' in e and 'official' in joints[t]['pictures'].get(name, {}):
                for band in ('near', 'middle'):
                    a, b = e['official'][band]['contrast'], joints[t]['pictures'][name]['official'][band]['contrast']
                    if a is not None and b is not None:
                        worst = max(worst, abs(a - b))
        agree[t] = dict(max_contrast_difference_vs_first=round(worst, 4), same_pass_count=joints[t]['summary']['official']['passed'] == joints[first]['summary']['official']['passed'])
    numbers['repeat_agreement'] = agree
    # ---- wet look
    wet = measure_wet.run(settings, folders[first])
    numbers['wet'] = measure_wet.run(settings, folders[first], base=wet)
    # ---- plate class numbers (P5) and the maps
    mush, maps_dir = {}, os.path.join(OUT, 'maps')
    for camera, light, state, scene_id, w, h in mc.plate_list(settings):
        name = f'plate_{camera}_{light}_{state}'
        folder = next((f for f in folders[first] if mc.exists(f, name)), None)
        if folder is None:
            continue
        stats, _ = measure_mush.plate_stats_from_folder(settings, folder, name)
        mush[name] = stats
        measure_mush.save_maps(os.path.join(folder, f'class_{camera}_{w}x{h}.png'), os.path.join(folder, f'depth_{camera}_{w}x{h}.png'), maps_dir, f'{camera}_{w}x{h}')
    numbers['plates'] = mush
    # ---- time
    times = {}
    for index, scene in enumerate(sorted(os.path.basename(f) for f in folders[first])):
        per = [os.path.join(root, t, scene) for t in tags if os.path.isdir(os.path.join(root, t, scene))]
        summary = measure_time.summarise(measure_time.load_runs(per, 'base'))
        runs = []
        for p in per:
            sp = os.path.join(p, 'run_summary.json')
            runs.append(json.load(open(sp)).get('seconds_total') if os.path.exists(sp) else None)
        summary['blender_run_seconds'] = runs
        summary['wall_seconds_incl_send_and_return'] = [json.load(open(os.path.join(root, t, 'run_time.json'))).get(scene, {}).get('wall_seconds') for t in tags if os.path.exists(os.path.join(root, t, 'run_time.json'))]
        summary.pop('best', None)
        summary['plate_best'] = {n: min(json.load(open(os.path.join(p, n + '.json')))['seconds'] for p in per) for n in summary['plates']}
        times[scene] = summary
    numbers['time'] = times
    # ---- the earlier layers' pinned files
    pinned = json.load(open(os.path.join(mc.KIT_ROOT, 'integrate', 'legacy_pinned.json')))
    numbers['legacy_pinned_sha256'] = {k: v['pinned_sha256'] for k, v in pinned['files'].items()}
    # ---- keep the pictures
    if os.path.isdir(OUT):
        for sub in ('pictures', 'plates', 'maps'):
            shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    for folder in folders[first]:
        scene = os.path.basename(folder)
        os.makedirs(os.path.join(OUT, 'pictures', scene), exist_ok=True)
        os.makedirs(os.path.join(OUT, 'plates'), exist_ok=True)
        os.makedirs(maps_dir, exist_ok=True)
        for path in glob.glob(os.path.join(folder, '*.jpg')):
            shutil.copy(path, os.path.join(OUT, 'pictures', scene))
        for path in glob.glob(os.path.join(folder, 'plate_*.png')):
            img = cv2.imread(path)
            cv2.imwrite(os.path.join(OUT, 'plates', os.path.basename(path)), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        for pattern in ('jmask_*.png', 'puddle_*.png', 'dirt_*.png', 'zones_*.png'):
            for path in glob.glob(os.path.join(folder, pattern)):
                shutil.copy(path, maps_dir)
        for path in glob.glob(os.path.join(folder, 'class_*.png')) + glob.glob(os.path.join(folder, 'depth_*.png')):
            if '1536x2730' in path or '1920x1440' in path:
                continue                                                         # the plate maps are stored small by save_maps
            shutil.copy(path, maps_dir)
    mc.jdump(numbers, os.path.join(OUT, 'numbers.json'))
    s = numbers['joints']['summary']
    print('joints official', s['official']['passed'], 'of', s['official']['of'], 'failing', s['official']['failing'])
    print('joints all dots', s['all_dots']['passed'], 'of', s['all_dots']['of'], 'failing', s['all_dots']['failing'])
    print('repeat agreement', agree)
    print('baseline written to', OUT, 'size MB', round(sum(os.path.getsize(os.path.join(b, f)) for b, _, fs in os.walk(OUT) for f in fs) / 1e6, 1))


if __name__ == '__main__':
    main()
