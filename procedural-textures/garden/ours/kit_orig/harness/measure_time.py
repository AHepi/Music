# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P7 (the same drawing time within +30 %). Reads the <picture>.json files the runner writes (seconds to draw; seconds spent changing the look; the order in the run) from one
# or more folders (the same batch drawn several times) and reports, per picture, the BEST of the runs; the plates' total (every plate_* picture, from the set file's
# test_set.time_plates or every plate_* picture); the FIRST picture after the look was put on (look-change seconds plus draw seconds of the first picture of that look in the run);
# and the number of 3D pieces (the earlier rubbish pieces are in the baseline's count). judge() applies the plan's lines: plates at most 1.30 x base, first picture at most 1.5 x base and never over 40 s, at most 2,500 pieces on top of the baseline's.
# Use:   python3 -I measure_time.py FOLDER [FOLDER ...] [--look base] [--out times.json]
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402


def load_runs(folders, look=None):
    """[{picture name: info}] one dict per folder (pictures of the given look only)."""
    runs = []
    for folder in mc.folders_for(folders):
        run = {}
        for path in glob.glob(os.path.join(folder, '*.json')):
            if os.path.basename(path) in ('run_summary.json',) or os.path.basename(path).startswith(('jobs_', 'times', 'selftests', 'bus_tests')):
                continue
            try:
                data = json.load(open(path))
            except ValueError:
                continue
            if 'seconds' not in data or (look and data.get('look') != look):
                continue
            run[data['name']] = data
        runs.append(run)
    return runs


def summarise(runs, plate_prefix='plate_', exclude=('_behind',)):
    names = sorted(set().union(*[set(r) for r in runs])) if runs else []
    best = {n: min(r[n]['seconds'] for r in runs if n in r) for n in names}
    plates = [n for n in names if n.startswith(plate_prefix) and not any(x in n for x in exclude)]
    # first picture of the look in each run = the one with the smallest index; its draw time plus the look change
    firsts = []
    for r in runs:
        if not r:
            continue
        first = min(r.values(), key=lambda d: d.get('index', 1e9))
        firsts.append(dict(name=first['name'], seconds=round(first['seconds'] + first.get('seconds_look_change', 0.0), 2), draw=first['seconds'], look_change=first.get('seconds_look_change')))
    pieces = max((d.get('pieces') or 0 for r in runs for d in r.values()), default=0)
    per_run_plate_total = [round(sum(r[n]['seconds'] for n in plates if n in r), 2) for r in runs]
    return dict(best=best, plates=plates, plate_best_total=round(sum(best[n] for n in plates), 2), plate_totals_per_run=per_run_plate_total,
                first_picture_seconds=min((f['seconds'] for f in firsts), default=None), first_pictures=firsts, pieces_max=pieces,
                run_seconds=[round(sum(d['seconds_job'] if 'seconds_job' in d else d['seconds'] for d in r.values()), 1) for r in runs], pictures=len(names))


def judge(now, base):
    fails = []
    if base['plate_best_total'] and now['plate_best_total'] > 1.30 * base['plate_best_total']:
        fails.append(f'plates {now["plate_best_total"]:.1f} s over 1.30 x base {base["plate_best_total"]:.1f} s')
    if base['first_picture_seconds'] and now['first_picture_seconds'] is not None:
        if now['first_picture_seconds'] > 1.5 * base['first_picture_seconds']:
            fails.append(f'first picture {now["first_picture_seconds"]:.1f} s over 1.5 x base {base["first_picture_seconds"]:.1f} s')
        if now['first_picture_seconds'] > 40:
            fails.append(f'first picture {now["first_picture_seconds"]:.1f} s over 40 s')
    growth = now['pieces_max'] - base.get('pieces_max', 0)         # the earlier rubbish pieces are in the baseline's count; only the kit's own pieces are limited
    if growth > 2500:
        fails.append(f'{growth} growth pieces on top of the baseline\'s {base.get("pieces_max", 0)} (limit 2,500)')
    return not fails, fails


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    result = summarise(load_runs(args, opts.get('--look')))
    if '--out' in opts:
        mc.jdump(result, opts['--out'])
    print(json.dumps({k: v for k, v in result.items() if k not in ('best',)}, indent=1))
