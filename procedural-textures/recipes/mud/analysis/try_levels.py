# What this does (plain words): builds descriptions at several levels of detail from the found puddles and stones, draws each with the quick numpy painter, and prints
# the size in bytes and the dot-for-dot scores. This is the first look at "what does each layer buy". Analysis only.
import json, os, sys
import cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import describe_tools as dt
el = dt.load_elements('mud')
print('palette kinds', el['kinds'])
earth_ground = 0
LEVELS = {
 'S_a_ground_only':      dict(puddle_eps=99999, puddle_tones=False, stone_min_area=10**9, stone_eps=3),
 'S_b_puddles_coarse':   dict(puddle_eps=4, puddle_tones=False, stone_min_area=10**9, stone_eps=3),
 'S_c_+60_big_stones':   dict(puddle_eps=4, puddle_tones=False, stone_min_area=0, stone_eps=3, max_stones=60, max_faces=0),
 'M_a_puddle_tones':     dict(puddle_eps=2, puddle_tones=True, tone_eps=4, tone_min_area=60, stone_min_area=0, stone_eps=3, max_stones=60, max_faces=0),
 'M_b_300_stones_faces': dict(puddle_eps=2, puddle_tones=True, tone_eps=4, tone_min_area=60, stone_min_area=0, stone_eps=2.2, max_stones=300, max_faces=3, face_eps=3, face_min_area=30),
 'L_a_all_stones_fine':  dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12),
}
os.makedirs('/tmp/mudscratch/try', exist_ok=True)
for name, level in LEVELS.items():
    d = dt.make_description(el, level)
    d['ground']['colour'] = earth_ground
    r, img = dt.score_description(d, name, texture=True)
    cv2.imwrite(f'/tmp/mudscratch/try/{name}.png', img)
    print(f'{name:24s} bytes {dt.byte_size(d):7d}', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
