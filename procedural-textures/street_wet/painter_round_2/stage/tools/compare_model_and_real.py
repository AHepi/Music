"""What this file does (plain words): lines up, for every case drawn by tools/render_diagnosis.sh, the road brightness that the REAL stage gave (numbers/diagnosis_real_stage.json, plus the film's own look from stills/before) with what the Python copy of the finish
(finish_model.py) predicts for the same settings, so it is clear that the copy is a fair stand-in and that the list of "what costs how much" is true of the real stage too. Writes numbers/diagnosis_real_against_model.json and a printout.
Run: python3 -I tools/compare_model_and_real.py
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import finish_model as fm
from finish_model import lum
from stage_common import central, central_mask, masks, er, load01, TEST1, FILM, P
M = masks(TEST1 + 'alignment/facts_surfaces/'); road = er(central_mask(M['road']))
wet = central(load01(P('../paint/front_painting_final.png'))); pl = lum(wet)
real = json.load(open(P('numbers/diagnosis_real_stage.json')))
before = json.load(open(P('numbers/stage_measurements_before.json')))['plate_view_stage_against_painting']['new_wet_front_painting']
OFF = dict(filmic=0.0, contrast=1.0, lift=0.0, tintAmount=0.0, vignette=0.0, grain=0.0)
cases = [('nothing of the finish left (the painting passed straight through)', 'diagnosis/off_all', OFF),
         ('only the dark frame edge (vignette 0.3)', 'diagnosis/only_edge', {**OFF, 'vignette': 0.3}),
         ('only the filmic curve (ACES)', 'diagnosis/only_curve', {**OFF, 'filmic': 1.0}),
         ('only contrast 1.04 and lift 0.015', 'diagnosis/only_cl', {**OFF, 'contrast': 1.04, 'lift': 0.015}),
         ('only the cool/warm tint', 'diagnosis/only_tint', {**OFF, 'tintAmount': 0.35}),
         ('the film\'s look without the frame edge', 'diagnosis/film_no_edge', {'vignette': 0.0}),
         ('the film\'s look as it is (the lockout look)', None, {}),
         ('FIX candidate: toe only', 'diagnosis/toe1', {'toe': 1.0}),
         ('FIX candidate: toe, contrast 1.0, lift 0', 'diagnosis/toe1_cl', {'toe': 1.0, 'contrast': 1.0, 'lift': 0.0}),
         ('FIX candidate: toe and frame edge 0.25', 'diagnosis/toe1_v25', {'toe': 1.0, 'vignette': 0.25}),
         ('FIX candidate: toe and frame edge 0.20', 'diagnosis/toe1_v20', {'toe': 1.0, 'vignette': 0.20})]
out = []
print(f"{'case':66s} real stage | Python copy")
for label, key, look in cases:
    r = before['road_stage_over_painting'] if key is None else real[key]['road_arrives']
    m = float(lum(fm.finish(wet, look))[road].mean() / pl[road].mean())
    out.append({'case': label, 'real_stage_road_arrives': r, 'python_copy_road_arrives': m})
    print(f"{label:66s} {r:.3f}      | {m:.3f}")
json.dump(out, open(P('numbers/diagnosis_real_against_model.json'), 'w'), indent=1)
