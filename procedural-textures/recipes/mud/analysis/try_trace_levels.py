# What this does (plain words): paints the traced ground patches (2000 ... 70000 of them) under the found puddles and stones with the quick numpy painter and prints
# description size against every dot-for-dot score: the "tracing" part of the rate-distortion table. Analysis only.
import json, os, sys, glob
import cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import describe_tools as dt
el = dt.load_elements('mud')
level = dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
base = dt.make_description(el, level)
rows = []
for target in (2000, 5000, 10000, 20000, 40000, 70000):
    p = os.path.join(HERE, 'ground_trace_mud', f'patches_{target}.pkl')
    d = dt.add_patches(base, p)
    r, img = dt.score_description(d, f'trace_{target}', texture=True)
    cv2.imwrite(f'/tmp/mudscratch/try/trace_{target}.png', img)
    row = dict(target=target, bytes=dt.byte_size(d), **r)
    rows.append(row)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
json.dump(rows, open(os.path.join(HERE, 'trace_levels.json'), 'w'), indent=1)
