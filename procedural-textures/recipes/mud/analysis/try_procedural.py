# What this does (plain words): puts the procedural ground (ruts + clods) under the found puddles and stones, draws it with the quick numpy painter, scores it dot for dot and
# with the "same kind of surface" tool, and saves the picture. Analysis only.
import json, os, sys
import cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import describe_tools as dt
el = dt.load_elements('mud')
lvl = dict(puddle_eps=1.8, puddle_tones=True, tone_eps=3, tone_min_area=40, stone_min_area=14, stone_eps=1.8, max_stones=10**9, max_faces=4, face_eps=2.4, face_min_area=18)
base = dt.make_description(el, lvl)
for clods in (14000,):
    d = dt.add_procedural_ground(base, os.path.join(HERE, 'ground_model_mud.json'), os.path.join(HERE, 'ruts_main_mud.json'), clod_count=clods)
    r, img = dt.score_description(d, f'proc_{clods}', texture=True)
    cv2.imwrite(f'/tmp/mudscratch/try/proc_{clods}.png', img)
    print(clods, 'bytes', dt.byte_size(d), {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
