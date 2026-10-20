# What this does: calibrates the outline methods on STRAIGHT edges (a regular grid of square cells: Randomness 0, no warp) with no anti-aliasing,
# so the line width in pixels can be counted exactly: setting -> measured width. Prints a table and saves it.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c05_outlines_in_shader.py')).read().split('results = {}')[0]
exec(compile(src, 'c05head', 'exec'))
hp.SAMPLES = 1
SIZE = 384
table = {}
BASEDIR = os.path.join(hp.OUT, 'data', 'c05e'); os.makedirs(BASEDIR, exist_ok=True)
kw = dict(scale=6.0, warp_amount=0.0, randomness=0.0)
for method in ('edge_distance', 'offset2', 'offset4', 'bump'):
    for width in (1, 2, 3, 4, 6, 8):
        label = f'{method}_{width}'
        path = os.path.join(BASEDIR, label + '.png')
        hp.photograph_group(lambda: outlined('cells', method, width, size=SIZE, name='cal_' + label, field_kwargs=kw), 'Mask', path, SIZE)
        a = hp.load(path)[..., 0] > 0.5
        # runs of white along the middle rows (cross vertical lines); ignore rows that lie on a horizontal line (long runs)
        runs = []
        for y in range(10, SIZE - 10, 7):
            row = a[y]
            if row.mean() > 0.5: continue
            edges = np.flatnonzero(np.diff(np.r_[0, row.astype(int), 0]))
            for s, e in zip(edges[::2], edges[1::2]):
                runs.append(e - s)
        table[label] = {'requested_px': width, 'median_run_px': float(np.median(runs)) if runs else 0.0, 'runs_seen': sorted(set(int(r) for r in runs))[:8]}
        print(label, table[label], flush=True)
json.dump(table, open(os.path.join(hp.OUT, 'data', 'c05e_width_calibration.json'), 'w'), indent=1)
