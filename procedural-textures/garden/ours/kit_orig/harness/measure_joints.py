# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P1 (the sett joints still pass). Measures the earlier joint contrast (pinned copy of the study's b04_measure_joints.py, unchanged) on the 22 lighting pictures of a set and
# judges each with the set file's test_set.joint_pass (the earlier study's pass line). THREE counts, as the plan says:
#   official     dots under a puddle and dots under the earlier rubbish are left out (the way the 21 of 22 were counted)         <- the pass count
#   all_dots     every dot counted (reported; was 18 of 22)
#   without_kit  as official, and the kit's own marks (the layer mask pictures layer_<key>_<label>_<state>) left out too; with no kit layer this equals official
# plus the study's second measure (dark or bright lines, pinned measure_grid_visibility.py) and the 'harsh black grid' test (near-band contrast above joint_pass.max_contrast).
# Inputs in the folder: <label>_<light>_<state>.png (kept by the runner), jmask_<camera>_<W>x<H>.png, puddle_<label>_<state>.png, dirt_<label>_<state>.png, layer_*.png.
# Use:   python3 -I measure_joints.py SET_ID FOLDER [FOLDER ...] [--out result.json]        (several folders: the pictures of each scene file)
#        from measure_joints import run;  run(settings, [folders]) -> dict;  compare_with_base(result, base_result) -> P1's verdict
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402

PINNED = os.path.join(mc.KIT_ROOT, 'integrate', 'legacy_pinned', 'earlier', 'relief_and_rubbish')
for sub in ('study/tools', 'setts/tools'):
    path = os.path.join(PINNED, sub)
    if path not in sys.path:
        sys.path.insert(0, path)
import b04_measure_joints as b04  # noqa: E402
import measure_grid_visibility as grid  # noqa: E402


def judge(result, need):
    """PASS / FAIL and the reasons, from the near and middle bands and joint_pass[label]."""
    reasons = []
    for band in ('near', 'middle'):
        entry = result[band]
        want = dict(zip(('contrast', 'delta', 'seen'), need[band]))
        if entry['contrast'] is None:
            reasons.append(f'{band}: too few joint dots')
            continue
        for key in ('contrast', 'delta', 'seen'):
            if entry[key] < want[key]:
                reasons.append(f'{band} {key} {entry[key]:.3f} < {want[key]}')
        if entry['contrast'] > need['max_contrast']:
            reasons.append(f'{band} contrast {entry["contrast"]:.3f} > {need["max_contrast"]} (a harsh black grid)')
    return not reasons, reasons


def _red_over(path, limit):
    return mc.read_channel(path, 0) > limit


def run(settings, folders, scene_ids=None):
    ts = settings.get('test_set') or {}
    joint_pass = ts['joint_pass']
    folders = mc.folders_for(folders)
    out = {'pictures': {}, 'summary': {}}
    for label, light, state, scene_id in mc.t22_list(settings):
        name = f'{label}_{light}_{state}'
        folder = next((f for f in folders if mc.exists(f, name)), None)
        if folder is None:
            out['pictures'][name] = {'missing': True}
            continue
        w, h = mc.size_of(settings, label)
        camera = mc.camera_of(settings, label)
        mask = os.path.join(folder, f'jmask_{camera}_{w}x{h}.png')
        if not os.path.exists(mask):
            mask = next((os.path.join(f, f'jmask_{camera}_{w}x{h}.png') for f in folders if os.path.exists(os.path.join(f, f'jmask_{camera}_{w}x{h}.png'))), None)
        if mask is None:
            out['pictures'][name] = {'missing': 'joint mask'}
            continue
        picture = os.path.join(folder, name + '.png')
        road = b04.load_mask(mask)[2] > 0.99
        puddles = np.zeros(road.shape, bool)
        dirt = np.zeros(road.shape, bool)
        kit = np.zeros(road.shape, bool)
        pf = next((f for f in folders if mc.exists(f, f'puddle_{label}_{state}')), None)
        if pf and state != 'dry':
            puddles = mc.dilate(_red_over(os.path.join(pf, f'puddle_{label}_{state}.png'), 0.5), 5)
        df = next((f for f in folders if mc.exists(f, f'dirt_{label}_{state}')), None)
        if df and state != 'dry':
            dirt = mc.dilate(_red_over(os.path.join(df, f'dirt_{label}_{state}.png'), 0.3), 5)
        for f in folders:
            for fn in os.listdir(f):
                if fn.startswith('layer_') and fn.endswith(f'_{label}_{state}.png'):
                    kit |= mc.dilate(_red_over(os.path.join(f, fn), 0.3), 5)
        L = b04.luminance(picture)
        official = b04.measure(L, mask, puddles=puddles | dirt)
        all_dots = b04.measure(L, mask)
        without_kit = b04.measure(L, mask, puddles=puddles | dirt | kit)
        for r, ex in ((official, puddles | dirt), (all_dots, np.zeros_like(road)), (without_kit, puddles | dirt | kit)):
            r['puddle_share'] = round(float((puddles & road).sum() / max(1, road.sum())), 3)
            r['dirt_share'] = round(float((dirt & road).sum() / max(1, road.sum())), 3)
            r['kit_share'] = round(float((kit & road).sum() / max(1, road.sum())), 3)
        need = joint_pass[label]
        entry = {}
        for key, r in (('official', official), ('all_dots', all_dots), ('without_kit', without_kit)):
            ok, reasons = judge(r, need)
            entry[key] = dict(r, passed=ok, reasons=reasons)
        gv = grid.grid_visibility(L, mask, puddles | dirt)
        entry['grid'] = {band: dict(v, visible=grid.visible(v)) for band, v in gv.items()}
        out['pictures'][name] = entry
    for key in ('official', 'all_dots', 'without_kit'):
        pics = {n: e for n, e in out['pictures'].items() if key in e}
        out['summary'][key] = dict(passed=sum(e[key]['passed'] for e in pics.values()), of=len(pics), failing=sorted(n for n, e in pics.items() if not e[key]['passed']))
    pics = {n: e for n, e in out['pictures'].items() if 'official' in e}
    out['summary']['grid_visible_near_and_middle'] = dict(count=sum(1 for e in pics.values() if e['grid']['near']['visible'] and e['grid']['middle']['visible']), of=len(pics))
    out['summary']['max_near_contrast'] = max((e['official']['near']['contrast'] or 0) for e in pics.values()) if pics else None
    out['summary']['harsh_grid'] = sorted(n for n, e in pics.items() if (e['official']['near']['contrast'] or 0) > joint_pass[n.split('_')[0]]['max_contrast'])
    out['summary']['missing'] = sorted(n for n, e in out['pictures'].items() if 'missing' in e)
    return out


def compare_with_base(result, base):
    """P1's verdict against the frozen base result: pass count >= 21, nothing that passed in base fails now, without_kit count equals base's, no harsh grid."""
    now, then = result['summary'], base['summary']
    broke = sorted(set(now['official']['failing']) - set(then['official']['failing']))
    checks = dict(
        official_count_at_least_21=now['official']['passed'] >= 21,
        nothing_that_passed_now_fails=not broke,
        without_kit_equals_base=now['without_kit']['passed'] == then['official']['passed'],
        no_harsh_grid=not now['harsh_grid'],
        all_dots_reported=now['all_dots']['passed'])
    checks['broke'] = broke
    checks['ok'] = bool(checks['official_count_at_least_21'] and checks['nothing_that_passed_now_fails'] and checks['without_kit_equals_base'] and checks['no_harsh_grid'])
    return checks


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_path = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    if out_path and out_path in args:
        args.remove(out_path)
    settings = mc.load_set(args[0])
    result = run(settings, args[1:])
    if out_path:
        mc.jdump(result, out_path)
    print(mc.json.dumps(result['summary'], indent=1))
    for name, e in result['pictures'].items():
        if 'official' in e:
            n, m = e['official']['near'], e['official']['middle']
            f = lambda b: 'n/a' if b['contrast'] is None else f"{b['contrast']:.2f}/{b['delta']:.3f}/{b['seen']:.2f}"   # noqa: E731
            print(f"{name:22s} puddle {e['official']['puddle_share']:.2f} dirt {e['official']['dirt_share']:.2f} near {f(n)} middle {f(m)} "
                  f"{'PASS' if e['official']['passed'] else 'FAIL ' + '; '.join(e['official']['reasons'][:2])} | all dots {'PASS' if e['all_dots']['passed'] else 'fail'}")
