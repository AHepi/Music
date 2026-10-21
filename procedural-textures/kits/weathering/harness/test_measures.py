# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# TESTS OF THE MEASURING SCRIPTS with made-up pictures (no Blender, no machine): each measure must give the number the construction says it must. Run:
#     python3 -I harness/test_measures.py [--out results.json]
# A measure that is never tested against a known answer is a guess; these are the known answers (a darkened plate, a painted line, an orange blob, a piece standing on the crown ...).
import json
import os
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage  # noqa: E402
import measure_common as mc  # noqa: E402
import measure_mush  # noqa: E402
import measure_period  # noqa: E402
import measure_readable  # noqa: E402
import measure_time  # noqa: E402
import measure_zones  # noqa: E402

results = {}


def check(name, passed, detail=''):
    results[name] = dict(passed=bool(passed), detail=str(detail))
    print(('PASS ' if passed else 'FAIL ') + name, detail)


def test_mush():
    rng = np.random.default_rng(1)
    H, W = 200, 100
    base = 0.2 + 0.3 * rng.random((H, W)).astype(np.float32)
    cmap = np.ones((H, W), np.int16)
    cmap[:, 50:] = 2
    depth = np.tile(np.linspace(0, 60, H)[:, None], (1, W)).astype(np.float32)
    classes = {'a': [1], 'b': [2]}
    same = measure_mush.compare(base, base, cmap, depth, classes)
    check('mush_identical_passes', same['ok'] and same['classes']['a']['m1_darkened_third'] == 0.0, same['failures'])
    dark = base.copy()
    dark[:, :50] *= 0.5
    r = measure_mush.compare(dark, base, cmap, depth, classes)
    check('mush_half_brightness_fails_M1_M3', any(f.startswith('M1 a') for f in r['failures']) and any(f.startswith('M3 a') for f in r['failures']) and not any(' b:' in f for f in r['failures']), r['failures'][:3])
    mild = base * 0.95
    r = measure_mush.compare(mild, base, cmap, depth, classes)
    check('mush_five_percent_passes', r['ok'], r['failures'][:3])
    far = base.copy()
    far[depth > 20] *= 0.7
    r = measure_mush.compare(far, base, cmap, depth, classes)
    check('mush_far_band_darkening_caught_by_M5', any(f.startswith('M5') for f in r['failures']), r['failures'][:2])


def test_time():
    fake = lambda secs, first_extra=0.0, pieces=0: {'plate_main': dict(name='plate_main', seconds=secs, index=2, seconds_look_change=0.0, pieces=pieces), 'a': dict(name='a', seconds=1.0, index=1, seconds_look_change=first_extra, pieces=pieces)}   # noqa: E731
    base = measure_time.summarise([fake(10.0, 2.0), fake(11.0, 2.5), fake(10.5, 2.2)])
    check('time_best_of_three', base['best']['plate_main'] == 10.0 and base['first_picture_seconds'] == 3.0, base['best'])
    ok, f = measure_time.judge(measure_time.summarise([fake(12.5, 2.0)]), base)
    check('time_plus_25_percent_passes', ok, f)
    ok, f = measure_time.judge(measure_time.summarise([fake(14.0, 2.0)]), base)
    check('time_plus_40_percent_fails', not ok, f)
    ok, f = measure_time.judge(measure_time.summarise([fake(10.0, 2.0, pieces=3000)]), base)
    check('time_pieces_over_2500_fails', not ok, f)
    base_p = measure_time.summarise([fake(10.0, 2.0, pieces=6000)])
    ok, f = measure_time.judge(measure_time.summarise([fake(10.0, 2.0, pieces=8000)]), base_p)
    check('time_pieces_counted_on_top_of_baseline', ok, f)


def test_period():
    kit = np.full((50, 50, 3), 0.3, np.float32)
    base = kit.copy()
    r = measure_period.hue_check(kit, base)
    check('hue_nothing_changed', r['ok'] and r['changed'] == 0, r)
    kit2 = kit.copy()
    kit2[10:20, 10:20] = (0.9, 0.6, 0.1)           # orange
    r = measure_period.hue_check(kit2, base)
    check('hue_orange_blob_caught', not r['ok'] and r['orange_yellow_share'] > 0.9, r)
    allowed = np.zeros((50, 50), bool)
    allowed[10:20, 10:20] = True
    r = measure_period.hue_check(kit2, base, allowed)
    check('hue_orange_inside_rust_mask_allowed', r['ok'], r)
    kit3 = kit.copy()
    kit3[5:15, 5:15] = (0.1, 0.9, 0.1)
    r = measure_period.hue_check(kit3, base)
    check('hue_bright_green_caught', not r['ok'] and r['bright_green_share'] > 0.9, r)
    ok, bad = measure_period.forbidden_check(dict(layers={'soot': {'amount': 1}, 'graffiti': {}}, forbidden=['graffiti']))
    check('forbidden_layer_caught', not ok, bad)
    ok, bad = measure_period.forbidden_check(dict(layers={'wallgrowth': {'lichen_amount': 0.0}}, must_be_zero=['lichen_amount']))
    check('lichen_zero_passes', ok, bad)
    ok, bad = measure_period.forbidden_check(dict(layers={'wallgrowth': {'lichen_amount': 0.2}}, must_be_zero=['lichen_amount']))
    check('lichen_not_zero_fails', not ok, bad)


def test_coverage():
    cmap = np.zeros((100, 100), np.int16)
    cmap[:, :50] = 3
    mask = np.zeros((100, 100), np.float32)
    mask[:, :10] = 1.0
    share, n = coverage.shares(mask, cmap, [3])
    check('coverage_share_is_a_fifth', abs(share - 0.2) < 1e-6 and n == 5000, (share, n))
    depth = np.tile(np.arange(100, dtype=np.float32)[:, None], (1, 100))
    share, n = coverage.shares(mask, cmap, [3], depth, 10)
    check('coverage_inside_distance', n == 11 * 50 and abs(share - 0.2) < 1e-6, (share, n))


def test_zones():
    gp = {k: np.zeros((50, 50), np.float32) for k in ('footfall', 'crown', 'keepclear', 'moss_site', 'weed_site', 'lichen_site', 'algae_site', 'step_foot')}
    gp['footfall'][:, 20:30] = 1.0
    gp['moss_site'][:, :15] = 0.5
    check('zones_fields_zero_passes', measure_zones.fields_test(gp)['ok'])
    gp['moss_site'][:, 22] = 0.1
    check('zones_field_leak_caught', not measure_zones.fields_test(gp)['ok'], measure_zones.fields_test(gp)['worst'])
    manifest = dict(ground=dict(x=[0.0, 2.0], y=[0.0, 2.0], dot_m=0.04))
    pieces = [dict(x=0.1, y=1.0, kind='weed'), dict(x=0.9, y=1.0, kind='weed')]                      # the second one is at x 0.9 = column 22: inside the lane
    r = measure_zones.pieces_test(gp, manifest, pieces)
    check('zones_piece_in_lane_caught', not r['ok'] and r['counts']['footfall'] == 1, r['counts'])
    r = measure_zones.pieces_test(gp, manifest, pieces[:1], fire_points=[(0.5, 1.0)])
    check('zones_piece_near_fire_caught', not r['ok'] and r['counts']['fire_1m'] == 1, r['counts'])
    r = measure_zones.pieces_test(gp, manifest, pieces[:1], rubbish=[dict(x=0.12, y=1.0)])
    check('zones_weed_on_rubbish_caught', not r['ok'] and r['weeds_near_rubbish'] == 1, r)


def test_readable():
    plate = np.full((300, 300, 3), 0.45, np.float32)
    plate[100:104, 40:200] = 0.30                    # a 4 dot wide, 160 long dark line (contrast 0.15)
    plate[200:225, 100:125] = 0.20                   # a 25 dot blob
    path = os.path.join(tempfile.mkdtemp(), 'plate.png')
    cv2.imwrite(path, (plate[..., ::-1] * 255).astype(np.uint8))
    mask = np.zeros((300, 300), bool)
    mask[100:104, 40:200] = True
    mask[200:225, 100:125] = True
    summary, rows = measure_readable.check_element(path, mask, 0.45)
    check('readable_finds_both_marks', summary['marks'] == 2, summary)
    check('readable_wide_blob_is_good', any(r['verdict'] == 'GOOD' and r['width_px'] > 20 for r in rows), [(r['width_px'], r['verdict']) for r in rows])


def test_joints_compare():
    import measure_joints
    mk = lambda passed, failing: {'summary': dict(official=dict(passed=passed, of=22, failing=failing), without_kit=dict(passed=passed, of=22, failing=failing), all_dots=dict(passed=18, of=22, failing=[]), max_near_contrast=0.6, harsh_grid=[])}   # noqa: E731
    base = mk(21, ['x'])
    check('joints_same_as_base_ok', measure_joints.compare_with_base(mk(21, ['x']), base)['ok'])
    check('joints_new_failure_caught', not measure_joints.compare_with_base(mk(21, ['y']), base)['ok'])
    check('joints_below_21_caught', not measure_joints.compare_with_base(mk(20, ['x', 'z']), base)['ok'])


if __name__ == '__main__':
    for t in (test_mush, test_time, test_period, test_coverage, test_zones, test_readable, test_joints_compare):
        try:
            t()
        except Exception as exc:       # a test that crashes is a failure with its message
            import traceback
            check(t.__name__ + '_crashed', False, traceback.format_exc()[-400:])
    if '--out' in sys.argv:
        mc.jdump(results, sys.argv[sys.argv.index('--out') + 1])
    failed = [k for k, v in results.items() if not v['passed']]
    print(f'{len(results) - len(failed)} of {len(results)} passed', failed)
    sys.exit(1 if failed else 0)
