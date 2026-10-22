# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# MEASURES ONE ROUND of the ground layers against the plan's pass lines, using the kit's own measuring scripts (nothing new is invented: this file only feeds them).
#     python3 -I ground/measure_ground.py SET_ID ROUND_FOLDER [--out result.json] [--clean] [--look sooty_1926] [--only p1,p2,p3,p5,p6,p7]
# ROUND_FOLDER holds one folder per scene file (made by ground/run_round.py). What is measured:
#   P1  the sett joints still pass (harness/measure_joints.py): the 22 lighting pictures, with the puddle and rubbish dots left out and the kit's own dots LEFT IN (the official
#       count), with every dot counted, and with the kit's dots left out too; the table per picture; the verdict against the frozen baseline
#   P2  the wet look is kept (harness/measure_wet.py): wet-to-dry ratios, puddle cover, highlights, speckle; the ground part (road, pavement) is listed on its own
#   P3  each element readable at the painter's size (harness/measure_readable.py's check_element on the element's own part pictures, at painter scale 0.45 and 0.40): the elements
#       come from the set's ground section ("readable": layer, parts, design zone, smallest GOOD count)
#   P5  not one dark mush (harness/measure_mush.py) on the ground classes of every plate, against the baseline plate
#   P6  nothing green where nothing may grow (harness/measure_zones.py marks_test on the layers' whole Mask pictures)
#   P7  drawing time (harness/measure_time.py) against the frozen baseline
# --clean deletes the big PNGs of the round afterwards (the numbers and the JPGs stay): disk is tight.
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
import measure_joints, measure_mush, measure_readable, measure_time, measure_wet, measure_zones  # noqa: E402
from ground import ground_names as gc  # noqa: E402

BASELINE = os.path.join(KIT_ROOT, 'harness', 'baseline')


def scene_folders(round_dir):
    return sorted(os.path.join(round_dir, d) for d in os.listdir(round_dir) if os.path.isdir(os.path.join(round_dir, d)) and not d.startswith('_'))


def p1(settings, folders, base):
    result = measure_joints.run(settings, folders)
    verdict = measure_joints.compare_with_base(result, base['joints'])
    rows = {}
    for name, e in result['pictures'].items():
        if 'official' not in e:
            rows[name] = e
            continue
        n_, m_ = e['official']['near'], e['official']['middle']
        rows[name] = dict(near=[n_['contrast'], n_['delta'], n_['seen']], middle=[m_['contrast'], m_['delta'], m_['seen']], kit_share=e['official'].get('kit_share'),
                          puddle_share=e['official'].get('puddle_share'), official=e['official']['passed'], all_dots=e['all_dots']['passed'], without_kit=e['without_kit']['passed'],
                          reasons=e['official']['reasons'][:2], near_without_kit=e['without_kit']['near']['contrast'])
    return dict(summary=result['summary'], verdict=verdict, pictures=rows)


def p2(settings, folders, base):
    result = measure_wet.run(settings, folders, base['wet'])
    ok, fails = measure_wet.judge(result, base['wet'])
    ground = [f for f in fails if ' road ' in f or ' pavement ' in f]
    return dict(ok=ok, failures=fails, ground_failures=ground, wet_to_dry={k: {c: v[c] for c in ('road', 'pavement', 'kerb_gutter') if c in v} for k, v in result['wet_to_dry'].items()},
                puddle_cover=result['puddle_cover'], speckle=result['speckle'], element_wet_dry=result['element_wet_dry'])


def element_mask(folder, row, camera):
    mask = None
    for part in row['parts']:
        path = mc.pic(folder, f'part_{row["layer"]}_{part}_{camera}')
        if path is None:
            return None
        m = mc.read_channel(path, 0) > 0.5
        mask = m if mask is None else (mask | m)
    return mask


def p3(settings, folders, ground, scales=(0.45, 0.40)):
    classes = mc.classes(settings)
    ts = settings.get('test_set') or {}
    out = {}
    for row in ground.get('readable', []):
        for index, camera in enumerate(row.get('plates', ['main'])):
            plate_entry = next((p for p in mc.plate_list(settings) if p[0] == camera), None)
            if plate_entry is None:
                continue
            _, light, state, scene_id, w, h = plate_entry
            folder = next((f for f in folders if os.path.basename(f) == scene_id), None)
            tag = f'{row["element"]}@{camera}'
            if folder is None:
                out[tag] = dict(skipped='no folder')
                continue
            plate_png = mc.pic(folder, f'plate_{camera}_{light}_{state}')
            mask = element_mask(folder, row, camera)
            if not plate_png or mask is None:
                out[tag] = dict(skipped='plate or part picture missing')
                continue
            zone = row.get('zone') or {}
            cp, dp = mc.pic(folder, f'class_{camera}_{w}x{h}'), mc.pic(folder, f'depth_{camera}_{w}x{h}')
            cmap = mc.read_class(cp) if cp else None
            if zone.get('class') and cmap is not None:
                mask = mask & mc.class_mask(cmap, classes[zone['class']])
            if zone.get('max_m') and dp:
                mask = mask & (mc.read_depth(dp) <= zone['max_m'])
            entry = {}
            for scale in scales:
                summary, rows_ = measure_readable.check_element(plate_png, mask, scale)
                need = row.get('min_good', 0) if index == 0 else row.get('min_good_second_plate', row.get('min_good', 0) / 2.0)
                fails = []
                if summary['marks'] == 0 or summary['good'] < need:
                    fails.append(f'{summary["good"]} GOOD marks, need {need:g}')
                if summary['marks']:
                    if summary['share_good'] < 0.60:
                        fails.append(f'GOOD share {summary["share_good"]:.0%} below 60 %')
                    if summary['share_lost'] > 0.15:
                        fails.append(f'LOST share {summary["share_lost"]:.0%} above 15 %')
                    if summary['share_crushed'] > 0.15:
                        fails.append(f'crushed share {summary["share_crushed"]:.0%} above 15 %')
                summary.update(passed=not fails, failures=fails, need=need)
                entry[f'scale_{scale}'] = summary
            entry['mask_dots'] = int(mask.sum())
            out[tag] = entry
    return out


def p5(settings, folders, ground_classes=('road', 'pavement', 'kerb_gutter', 'iron')):
    out = {}
    for camera, light, state, scene_id, w, h in mc.plate_list(settings):
        folder = next((f for f in folders if os.path.basename(f) == scene_id), None)
        name = f'plate_{camera}_{light}_{state}'
        base_png = os.path.join(BASELINE, 'plates', name + '.png')
        if folder is None or not os.path.exists(base_png) or mc.pic(folder, name) is None:
            continue
        cp, dp = mc.pic(folder, f'class_{camera}_{w}x{h}'), mc.pic(folder, f'depth_{camera}_{w}x{h}')
        if not (cp and dp):
            continue
        res = measure_mush.compare(mc.read_lum(mc.pic(folder, name)), mc.read_lum(base_png), mc.read_class(cp), mc.read_depth(dp), mc.classes(settings))
        out[name] = dict(plate_mean_ratio=res['plate_mean_ratio'], classes={c: {k: v for k, v in e.items() if k not in ('base', 'kit')} for c, e in res['classes'].items() if c in ground_classes},
                         failures=[f for f in res['failures'] if any(f' {c}:' in f for c in ground_classes) or 'whole plate' in f])
    return out


def p6(settings, folders, look):
    out = {}
    for folder in folders:
        if os.path.basename(folder) in {s['id'] for s in settings.scenes}:
            r = measure_zones.marks_test(settings, folder, look)
            out[os.path.basename(folder)] = r
    return out


def p7(folders, base):
    out = {}
    for folder in folders:
        sid = os.path.basename(folder)
        if sid not in base['time']:
            continue
        runs = measure_time.load_runs([folder])
        now = measure_time.summarise(runs)
        ok, fails = measure_time.judge(now, base['time'][sid])
        out[sid] = dict(plate_best_total=now['plate_best_total'], base_plate_total=base['time'][sid]['plate_best_total'], first_picture_seconds=now['first_picture_seconds'],
                        base_first=base['time'][sid]['first_picture_seconds'], pieces_max=now['pieces_max'], ok=ok, failures=fails, plate_best=now.get('best', {}) and
                        {k: v for k, v in now['best'].items() if k.startswith('plate_')})
    return out


def clean(round_dir):
    freed = 0
    for folder in scene_folders(round_dir):
        for name in os.listdir(folder):
            if name.endswith('.png'):
                path = os.path.join(folder, name)
                freed += os.path.getsize(path)
                os.remove(path)
    return freed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    set_id, round_dir = args[0], args[1]
    settings = mc.load_set(set_id)
    look = json.load(open(os.path.join(KIT_ROOT, 'presets', opts.get('--look', settings.default_look() or 'sooty_1926') + '.json')))
    base = json.load(open(os.path.join(BASELINE, 'numbers.json')))
    ground = gc.ground_section(settings)
    only = set(opts['--only'].split(',')) if '--only' in opts else {'p1', 'p2', 'p3', 'p5', 'p6', 'p7'}
    folders = scene_folders(round_dir)
    with_maps = folders + [os.path.join(BASELINE, 'maps')]
    result = {}
    if 'p1' in only:
        result['p1'] = p1(settings, with_maps, base)
    if 'p2' in only:
        result['p2'] = p2(settings, with_maps, base)
    if 'p3' in only:
        result['p3'] = p3(settings, folders, ground)
    if 'p5' in only:
        result['p5'] = p5(settings, folders)
    if 'p6' in only:
        result['p6'] = p6(settings, with_maps, look)
    if 'p7' in only:
        result['p7'] = p7(folders, base)
    out_path = opts.get('--out') or os.path.join(round_dir, 'ground_measures.json')
    mc.jdump(result, out_path)
    if '--clean' in sys.argv:
        print('freed', round(clean(round_dir) / 1e6, 1), 'MB')
    summarise(result)


def summarise(result):
    if 'p1' in result:
        s = result['p1']['summary']
        print('P1 official (kit dots in)', s['official']['passed'], 'of', s['official']['of'], 'failing', s['official']['failing'])
        print('   all dots', s['all_dots']['passed'], '| kit dots out', s['without_kit']['passed'], '| max near contrast', s['max_near_contrast'], '| harsh', s['harsh_grid'])
        print('   verdict', result['p1']['verdict'])
    if 'p2' in result:
        print('P2 ok', result['p2']['ok'], 'ground failures', result['p2']['ground_failures'][:6], '| all failures', len(result['p2']['failures']))
    if 'p3' in result:
        for tag, e in result['p3'].items():
            if 'skipped' in e:
                print('P3', tag, 'SKIPPED', e['skipped'])
                continue
            a, b = e['scale_0.45'], e['scale_0.4']
            print(f'P3 {tag:62s} marks {a["marks"]:4d} good {a["good"]:3d} lost {a["lost"]:3d} crushed {a["crushed"]:3d} | {"PASS" if a["passed"] else "FAIL " + "; ".join(a["failures"][:2])} | 0.40: good {b["good"]} {"PASS" if b["passed"] else "fail"}')
    if 'p5' in result:
        for name, e in result['p5'].items():
            print('P5', name, 'plate mean ratio', e['plate_mean_ratio'], 'failures', e['failures'])
    if 'p6' in result:
        for sid, e in result['p6'].items():
            print('P6', sid, 'ok', e['ok'], e['shares'])
    if 'p7' in result:
        for sid, e in result['p7'].items():
            print('P7', sid, e)


if __name__ == '__main__':
    main()
