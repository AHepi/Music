# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Prints ONE TABLE of how well the joints between the setts show, for every picture of the lighting test set and every variant drawn in a folder (plain Python, no Blender).
# For each picture and variant it prints the NEAR band's "joint contrast" (how much darker a joint is than the stone beside it, as a share of the stone's brightness; 0 = not
# at all, 0.3 = a clear dark line) and "seen" (the share of joint dots that are clearly darker), then the MIDDLE band's, then PASS or FAIL against the study's pass line
# (study/tools/b09_lighting_test_set.py, unchanged). The last lines count the passes for each variant.
# Use:  python3 -I sweep_report.py FOLDER_WITH_MEASUREMENTS [FOLDER2 ...] [--variants before,after] [--set full|quick] [--json OUT.json]
#   FOLDER: a folder with measurements.json made by the runner; pictures are named <camera>_<light>_<state>_<variant tag>. With several folders (the street run and the lockout run),
#   the measurements are put together.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools')))
sys.dont_write_bytecode = True
from b09_lighting_test_set import SETS, judge  # noqa: E402


def load(folders):
    store = {}
    for folder in folders:
        path = os.path.join(folder, 'measurements.json')
        if os.path.exists(path):
            store.update(json.load(open(path)))
    return store


def table(store, variants, set_name='full', out=print):
    summary = {v: [0, 0] for v in variants}
    rows = {}
    out(f"{'picture':16s} " + ' '.join(f'{v:^34s}' for v in variants))
    out(f"{'':16s} " + ' '.join(f"{'near c/seen | mid c/seen':^34s}" for v in variants))
    for label, rest in SETS[set_name].items():
        for light, states in rest:
            for state in states:
                cells = []
                for v in variants:
                    r = store.get(f'{label}_{light}_{state}_{v}')
                    if r is None:
                        cells.append(f"{'-':^34s}")
                        continue
                    ok, reasons = judge(r, label)
                    summary[v][0] += ok
                    summary[v][1] += 1
                    f = lambda e: ' n/a ' if e['contrast'] is None else f"{e['contrast']:.2f}/{e['seen']:.2f}"   # noqa: E731
                    cells.append(f"{f(r['near'])} | {f(r['middle'])} {'PASS' if ok else 'FAIL'}".center(34))
                    rows[f'{label}_{light}_{state}_{v}'] = dict(near=r['near'], middle=r['middle'], far=r['far'], ok=ok, reasons=reasons, puddle=r.get('puddle_share'))
                out(f'{label + " " + light + " " + state:16s} ' + ' '.join(cells))
    out('')
    for v in variants:
        out(f'{v}: {summary[v][0]} of {summary[v][1]} pictures pass')
    return summary, rows


if __name__ == '__main__':
    args = sys.argv[1:]
    options = {}
    folders = []
    i = 0
    while i < len(args):
        if args[i].startswith('--'):
            options[args[i]] = args[i + 1]
            i += 2
        else:
            folders.append(args[i])
            i += 1
    store = load(folders)
    tags = sorted({k.rsplit('_', 1)[1] for k in store if k.count('_') >= 3})
    variants = options['--variants'].split(',') if '--variants' in options else tags
    summary, rows = table(store, variants, options.get('--set', 'full'))
    if '--json' in options:
        json.dump(dict(summary=summary, rows=rows), open(options['--json'], 'w'), indent=1)
