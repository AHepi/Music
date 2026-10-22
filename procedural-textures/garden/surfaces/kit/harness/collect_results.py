# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# COLLECTS EVERY TEST RESULT of the foundation into ONE JSON next to the notes: the self-tests on each scene and picture size (hook, remove, do-nothing, dial zero, isolation,
# determinism, reuse, lighting), the bus tests, the Attribute-node test, the lint, the made-up-picture tests of the measures, each pack's acceptance checks and sizes, the places
# regression, the baseline's headline numbers. It only reads files the other scripts wrote.
#     python3 -I harness/collect_results.py WORK_DIR OUT.json
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))


def load(path):
    return json.load(open(path)) if os.path.exists(path) else None


def brief(result):
    """A test result without its bulky numbers: passed, plus the short facts."""
    if not isinstance(result, dict):
        return result
    keep = {k: v for k, v in result.items() if isinstance(v, (bool, int, float, str)) or k in ('layers', 'rigs')}
    return keep


def main(work, out):
    results = dict(made=time.strftime('%Y-%m-%d %H:%M'), kit=KIT_ROOT)
    selftests = {}
    for path in sorted(glob.glob(os.path.join(work, 'out_self_*', 'selftests_*.json'))):
        d = load(path)
        key = f"{d['scene']}@{'x'.join(str(v) for v in d.get('size', []))}"
        selftests[key] = {name: brief(r) for name, r in d['results'].items()}
        selftests[key]['_seconds'] = d.get('seconds')
    results['selftests'] = selftests
    bus = {}
    for path in sorted(glob.glob(os.path.join(work, 'out_bus_*', 'bus_tests_*.json'))):
        d = load(path)
        bus[d['scene']] = {name: brief(r) for name, r in d['results'].items()}
    results['bus_tests'] = bus
    results['attribute_node'] = dict(result=load(os.path.join(work, 'attr_out', 'attr_result.json')),
                                     meaning='[picture value in EEVEE, in Cycles] for an object whose custom property is 0.5552: both engines read an object custom property through an Attribute node equally (difference 0.0002); a missing property reads 0.0')
    lint = subprocess.run(['python3', '-I', os.path.join(HERE, 'lint_no_set_names.py')], capture_output=True, text=True, cwd=KIT_ROOT)
    results['lint'] = dict(returncode=lint.returncode, output_tail=lint.stdout[-600:])
    tm = subprocess.run(['python3', '-I', os.path.join(HERE, 'test_measures.py')], capture_output=True, text=True, cwd=KIT_ROOT)
    results['measure_tests'] = dict(returncode=tm.returncode, summary=tm.stdout.strip().splitlines()[-1])
    packs = {}
    for path in sorted(glob.glob(os.path.join(KIT_ROOT, 'masks', 'packs', '*', '*', 'manifest.json'))):
        m = load(path)
        folder = os.path.dirname(path)
        size = sum(os.path.getsize(os.path.join(folder, f)) for f in os.listdir(folder))
        failed = {k: v for k, v in (m.get('checks') or {}).items() if isinstance(v, dict) and v.get('passed') is False}
        passed = [k for k, v in (m.get('checks') or {}).items() if isinstance(v, dict) and v.get('passed')]
        packs[f"{m['set']}/{m['scene']}"] = dict(bytes=size, megabytes=round(size / 1e6, 2), checks_passed=len(passed), checks_failed=failed, reader_seconds=round(sum(t[1] for t in (m.get('timings') or [])), 1), sheets=len(m['frames']['sheets']), sheet_errors=(m.get('stats') or {}).get('sheet_errors'))
    results['packs'] = packs
    sys.path.insert(0, KIT_ROOT)
    from masks import check_pack
    results['shade_side'] = {}
    for key in packs:
        set_id, scene_id = key.split('/')
        try:
            results['shade_side'][key] = check_pack.shade_side(set_id, scene_id)
            results.setdefault('pack_acceptance', {})[key] = check_pack.acceptance(set_id, scene_id)
        except Exception as error:               # reported, never hidden
            results['shade_side'][key] = dict(passed=False, error=repr(error))
    for path in sorted(glob.glob(os.path.join(work, 'places_regression_*.json'))):
        results.setdefault('places_regression', {})[os.path.basename(path)[len('places_regression_'):-5]] = load(path)
    baseline = load(os.path.join(KIT_ROOT, 'harness', 'baseline', 'numbers.json'))
    if baseline:
        s = baseline['joints']['summary']
        results['baseline'] = dict(joints_official=s['official'], joints_all_dots=s['all_dots'], joints_without_kit=s['without_kit'], grid_visible=s['grid_visible_near_and_middle'],
                                   repeat_agreement=baseline.get('repeat_agreement'), time=baseline['time'])
    json.dump(results, open(out, 'w'), indent=1, default=str)
    print('written', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
