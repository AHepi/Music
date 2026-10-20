# What this does (plain words): builds the TRACED classes of the wood ladder and measures them with a quick numpy preview (no Blender): for several patch counts and
# outline looseness it traces the reference into flat patches, writes the description, and scores it dot for dot. Two kinds:
#   "trace": the traced patches only;
#   "hybrid": the traced patches with the cheap layout layers on top (blobs, cracks as ribbons, knots, pebbles), because thin dark lines are expensive as outlines and cheap as ribbons.
# Output: ../description/<name>.json for each, and a table printed + saved to ../scores/trace_ladder_table.json. Plain Python (python3 -I). Analysis only (reads the reference).
# Run: python3 -I build_trace_classes.py
import json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import describe_tools as dt
import make_descriptions as md
import preview as pv
import score_tools as st
import trace_tools as tt
bgr = dt.load_reference()
state = dt.load_merge_state(bgr)
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
cracks = json.load(open(os.path.join(HERE, 'cracks_fitted.json')))
DESC = os.path.join(HERE, '..', 'description'); OUT = os.path.join(HERE, '..', 'outputs'); SCORES = os.path.join(HERE, '..', 'scores')
os.makedirs(SCORES, exist_ok=True)
jobs = [json.loads(a) for a in sys.argv[1:]] or [
    dict(name='T_n150', n=150, eps=1.0), dict(name='T_n400', n=400, eps=1.0), dict(name='T_n800', n=800, eps=1.0), dict(name='T_n1500', n=1500, eps=1.0),
    dict(name='T_n2500', n=2500, eps=1.0), dict(name='T_n3500', n=3500, eps=1.0), dict(name='T_n5000', n=5000, eps=1.0),
    dict(name='H_n150', n=150, eps=1.0, hybrid=True), dict(name='H_n400', n=400, eps=1.0, hybrid=True), dict(name='H_n800', n=800, eps=1.0, hybrid=True), dict(name='H_n1500', n=1500, eps=1.0, hybrid=True),
    dict(name='H_n2500', n=2500, eps=1.0, hybrid=True)]
rows = []
for job in jobs:
    t0 = time.time()
    regions, pal = dt.traced_regions(bgr, state, job['n'], job.get('palette', 64), job['eps'])
    d = dt.traced_description(regions, pal, job['name'])
    if job.get('hybrid'):
        import cv2
        lab = md.lab_to_rgb  # noqa
        pal_lab = np.array([cv2.cvtColor(np.array([[[c[2] / 255.0, c[1] / 255.0, c[0] / 255.0]]], np.float32), cv2.COLOR_BGR2Lab)[0, 0] for c in d['palette']])
        layout = md.layout_layers(fit, cracks, pal_lab, crack_count=40)
        boards = [dict(l, draw=False) for l in layout if l['type'] == 'boards']
        d['layers'] = boards + d['layers'] + [l for l in layout if l['type'] != 'boards']
        d['note'] = job['name'] + ': traced patches with layout layers (blobs, cracks, knots, pebbles) on top'
    path = os.path.join(DESC, job['name'] + '.json')
    size = md.write(d, path)
    r = pv.run(path, os.path.join(OUT, 'preview_' + job['name']), 2, True)
    row = dict(name=job['name'], n=job['n'], eps=job['eps'], hybrid=bool(job.get('hybrid')), bytes=size, kilobytes=round(size / 1024, 1))
    for k in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall'):
        row[k] = r.get(k)
    row['seconds'] = round(time.time() - t0)
    print(json.dumps(row), flush=True)
    rows.append(row)
    json.dump(rows, open(os.path.join(SCORES, 'trace_ladder_table.json'), 'w'), indent=1)
