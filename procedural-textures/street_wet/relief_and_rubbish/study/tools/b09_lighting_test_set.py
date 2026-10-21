# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# THE LIGHTING TEST SET: the fixed list of pictures every later helper must draw and measure before saying "the joints between the setts show in every condition".
# It does three things, chosen by the first word you give it:
#   jobs     writes the job files (what to draw) for a set into a folder:      python3 -I b09_lighting_test_set.py jobs SET OUT_FOLDER
#   report   measures the finished pictures and prints PASS / FAIL per picture: python3 -I b09_lighting_test_set.py report SET OUT_FOLDER
#   list     prints the set as a table
# SET is "full" (every picture, about 40 minutes on this machine) or "quick" (the 9 hardest pictures, about 20 minutes).
# The drawing itself is done by b03_render_jobs.py (the runner) through run_lighting_test_set.sh, which calls this file for the job lists and the report.
# What a PICTURE of the set is: a camera (main = the film's street camera, 540 x 960; lockout = the lockout plate camera in the film's lockout shot file, 540 x 960; close =
# a low view down the road, 640 x 480), a lighting (A dusk lamps, B the lockout brazier's glare, C low side light, D flat overhead light, E light from behind into the glare),
# and a wetness state (dry = 0 / 0, wet = 0.85 / 0.5, heavy = 1.0 / 0.8; the two numbers are Wetness and the Puddles dial of the wetness layer).
# The PASS LINE (section 5 of the study note says how it was chosen, by looking at pictures): for every picture of the set, in the NEAR and MIDDLE bands of the road, the joints
# (dots under a PUDDLE are left out: water seen at a grazing angle hides what lies under it; the report says how much of the road is puddle)
# must be at least PASS['contrast'] darker than the stone beside them (as a share of the stone's brightness), at least PASS['delta'] darker in plain brightness (0 to 1), and at
# least PASS['seen'] of the joint dots must be "seen" (15 % and 0.015 darker). The far band is only reported (at 540 x 960 the far joints are narrower than a dot).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

# (camera label, camera name in the file, width, height, samples, file) -> list of (lighting, [states])
CAMERAS = {
    'main': dict(camera='main', w=540, h=960, samples=16, file='street'),
    'close': dict(camera='close_road', w=640, h=480, samples=24, file='street'),
    'lockout': dict(camera='lockout', w=540, h=960, samples=16, file='lockout'),       # 'lockout' = the lockout plate camera (the same as the lockout file's own main camera; the name keeps its mask apart from the street's main camera mask)
}
FULL = {
    'main': [('A', ['dry', 'wet', 'heavy']), ('C', ['dry', 'wet']), ('D', ['dry', 'wet']), ('E', ['dry', 'wet', 'heavy'])],
    'close': [('A', ['dry', 'wet', 'heavy']), ('C', ['wet']), ('D', ['wet']), ('E', ['wet'])],
    'lockout': [('B', ['dry', 'wet', 'heavy']), ('C', ['wet']), ('D', ['wet']), ('E', ['wet'])],
}
QUICK = {
    'main': [('A', ['wet', 'heavy']), ('C', ['wet']), ('D', ['wet']), ('E', ['wet'])],
    'close': [('A', ['wet']), ('E', ['wet'])],
    'lockout': [('B', ['wet']), ('E', ['wet'])],
}
SETS = {'full': FULL, 'quick': QUICK}
# the pass line (filled in from the study's pictures: see section 5 of the note)
PASS = {
    # near / middle bands of the road in the picture. contrast = share of the stone's brightness that the joint is darker by; delta = the same in plain brightness (0 to 1);
    # seen = share of joint dots at least 15 % and 0.015 darker than the stone beside them. 'max_contrast' stops the other fault: a harsh black grid.
    'main':    dict(near=dict(contrast=0.18, delta=0.020, seen=0.65), middle=dict(contrast=0.12, delta=0.015, seen=0.30), max_contrast=0.75),
    'lockout': dict(near=dict(contrast=0.15, delta=0.020, seen=0.50), middle=dict(contrast=0.07, delta=0.015, seen=0.12), max_contrast=0.75),
    'close':   dict(near=dict(contrast=0.25, delta=0.030, seen=0.70), middle=dict(contrast=0.20, delta=0.025, seen=0.60), max_contrast=0.80),
}


def picture_name(label, light, state):
    return f'{label}_{light}_{state}'


def make_jobs(set_name, out_folder, variant='baseline', args=None, after_apply=None):
    """Writes one job file per street file (street.json, lockout.json) into out_folder and returns their paths."""
    os.makedirs(out_folder, exist_ok=True)
    result = {}
    for file_kind in ('street', 'lockout'):
        masks, jobs = [], []
        for label, rows in SETS[set_name].items():
            spec = CAMERAS[label]
            if spec['file'] != file_kind:
                continue
            masks.append([spec['camera'], spec['w'], spec['h']])
            wet_states = []
            for light, states in rows:
                for state in states:
                    jobs.append(dict(name=picture_name(label, light, state), camera=spec['camera'], light=light, state=state, variant=variant, args=args or {},
                                     w=spec['w'], h=spec['h'], samples=spec['samples']))
                    if state != 'dry' and state not in wet_states:
                        wet_states.append(state)
            # the puddle masks (a checking view in plain light; where the puddles lie does not depend on the lighting): one for each camera and wet state
            for state in wet_states:
                jobs.append(dict(name=f'{label}_A_{state}_puddlemask', camera=spec['camera'], light='A', state=state, variant='show_masks', args={},
                                 w=spec['w'], h=spec['h'], samples=4))
        if jobs:
            data = dict(masks=masks, jobs=jobs)
            if after_apply:
                data['after_apply'] = after_apply
            path = os.path.join(out_folder, f'jobs_{file_kind}.json')
            json.dump(data, open(path, 'w'), indent=1)
            result[file_kind] = path
    return result


def judge(measure_result, label):
    """PASS / FAIL for one picture's measurement (near and middle bands), and the list of reasons."""
    reasons = []
    for band in ('near', 'middle'):
        entry = measure_result[band]
        need = PASS[label][band]
        if entry['contrast'] is None:
            reasons.append(f'{band}: too few joint dots to measure')
            continue
        for key in ('contrast', 'delta', 'seen'):
            if entry[key] < need[key]:
                reasons.append(f'{band} {key} {entry[key]:.3f} < {need[key]}')
        if entry['contrast'] > PASS[label]['max_contrast']:
            reasons.append(f"{band} contrast {entry['contrast']:.3f} > {PASS[label]['max_contrast']} (a harsh black grid)")
    return (len(reasons) == 0), reasons


def report(set_name, folder, store_name='measurements.json'):
    from b04_measure_joints import measure
    store_path = os.path.join(folder, store_name)
    store = json.load(open(store_path)) if os.path.exists(store_path) else {}
    print(f"{'picture':22s} {'road':>6s} {'pud':>5s} {'near c / delta / seen':>24s} {'middle c / delta / seen':>26s}  verdict")
    failures = 0
    missing = []
    for label, rows in SETS[set_name].items():
        for light, states in rows:
            for state in states:
                name = picture_name(label, light, state)
                r = store.get(name)
                if r is None:
                    missing.append(name)
                    continue
                ok, reasons = judge(r, label)
                failures += (not ok)
                n, m = r['near'], r['middle']
                fmt = lambda e: 'n/a' if e['contrast'] is None else f"{e['contrast']:5.2f} {e['delta']:6.3f} {e['seen']:5.2f}"
                pud = '-' if r.get('puddle_share') is None else f"{r['puddle_share']:.2f}"
                print(f"{name:22s} {r['road_mean']:6.3f} {pud:>5s} {fmt(n):>24s} {fmt(m):>26s}  {'PASS' if ok else 'FAIL  ' + '; '.join(reasons[:3])}")
    print('\nmissing pictures:', missing if missing else 'none')
    print('RESULT:', 'ALL PASS' if (failures == 0 and not missing) else f'{failures} picture(s) fail, {len(missing)} missing')


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'jobs':
        # python3 -I b09_lighting_test_set.py jobs SET OUT_FOLDER [--variant NAME] [--args JSON] [--after-apply FILE.py]
        rest = sys.argv[4:]
        options = {rest[i]: rest[i + 1] for i in range(0, len(rest) - 1, 2)}
        print(make_jobs(sys.argv[2], sys.argv[3], variant=options.get('--variant', 'baseline'), args=json.loads(options['--args']) if '--args' in options else None,
                        after_apply=options.get('--after-apply')))
    elif command == 'report':
        report(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'measurements.json')
    elif command == 'list':
        for label, rows in SETS[sys.argv[2]].items():
            for light, states in rows:
                print(label, light, states)
