# What this does (plain words): tests a CORRECTION layer of traced patches painted last (only where the drawing is still clearly wrong) on top of the traced-ground description, at
# several settings, and prints size against dot-for-dot scores. Analysis only (reads the reference).
import json, os, sys
import cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import describe_tools as dt
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ref = cv2.imread(PROC + '/reference/mud/colour.png')
el = dt.load_elements('mud')
fine = dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
rows = []
for target, eps in ((5000, 2.6), (5000, 3.2), (10000, 3.6)):
    p = os.path.join(HERE, 'ground_trace_mud', f'patches_{target}.pkl') if os.path.exists(os.path.join(HERE, 'ground_trace_mud', f'patches_{target}.pkl')) else None
    if p is None:
        continue
    base = dt.add_patches(dt.make_description(el, fine), p, epsilon_keep=eps)
    for thr, minarea, e in ((8, 14, 1.8), (6, 10, 1.6)):
        d, n = dt.add_residual_patches(base, ref, threshold=thr, min_area=minarea, epsilon=e)
        r, img = dt.score_description(d, 'res', texture=False)
        row = dict(ground_patches=target, ground_eps=eps, residual_thr=thr, residual_min_area=minarea, residual_eps=e, residual_patches=n, bytes=dt.byte_size(d),
                   **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != 'texture_compare_overall'})
        rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open(os.path.join(HERE, 'residual_trials.json'), 'w'), indent=1)
