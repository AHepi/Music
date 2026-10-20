# What this does (plain words): finds the best mix of "how many traced patches" and "how loose their outlines are" (and how detailed the stone and puddle outlines are) for a
# fixed description size, so that the biggest class (L, 512 KB) gets the most accuracy. Prints size against the dot-for-dot scores for each mix. Analysis only.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import describe_tools as dt
el = dt.load_elements('mud')
rows = []
fine = dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
mid = dict(puddle_eps=1.8, puddle_tones=True, tone_eps=3, tone_min_area=40, stone_min_area=14, stone_eps=1.8, max_stones=10**9, max_faces=4, face_eps=2.4, face_min_area=18)
for ename, lvl in (('fine', fine), ('mid', mid)):
    base = dt.make_description(el, lvl)
    for target in (5000, 10000, 20000):
        for eps in (1.0, 1.8, 2.6):
            d = dt.add_patches(base, os.path.join(HERE, 'ground_trace_mud', f'patches_{target}.pkl'), epsilon_keep=eps)
            r, img = dt.score_description(d, 'bs', texture=False)
            row = dict(elements=ename, target=target, eps=eps, bytes=dt.byte_size(d), **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != 'texture_compare_overall'})
            rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open(os.path.join(HERE, 'budget_search.json'), 'w'), indent=1)
