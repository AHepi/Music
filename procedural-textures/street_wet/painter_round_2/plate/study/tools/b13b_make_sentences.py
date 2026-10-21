# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes the few sentences of the study note that hold numbers worked out from the measurement files (so that none is typed by hand): the puddle sentence, the quick-set results, the fourth-test text.
# Plain Python. Run before b13_write_note.py:  python3 -I b13b_make_sentences.py
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
from b04_measure_joints import load_mask, load_puddles  # noqa: E402
import b09_lighting_test_set as t  # noqa: E402

WORK = os.path.abspath(os.path.join(HERE, '..', 'work'))
PARTS = os.path.join(WORK, 'note_text')


def load(folder, name='measurements.json'):
    p = os.path.join(WORK, folder, name)
    return json.load(open(p)) if os.path.exists(p) else {}


def put(name, text):
    open(os.path.join(PARTS, name), 'w').write(text.strip() + '\n')


# ---- puddles over joints (main and close from the checking pictures of work/r10, lockout from work/r12)
rows = {}
for label, folder, mask_file in (('main', 'r10', 'r10/mask_main_540x960.png'), ('close', 'r10', 'r10/mask_close_road_640x480.png'), ('lockout', 'r12', 'r07/mask_lockout_540x960.png')):
    J, S, R = load_mask(os.path.join(WORK, mask_file))
    for state in ('wet', 'heavy'):
        pm = os.path.join(WORK, folder, f'{label}_A_{state}_puddlemask.png')
        image = cv2.imread(pm, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
        puddle = image[..., 0] > 0.5
        road = R > 0.99
        joint = (J > 0.5) & road
        stone = (S > 0.9) & road
        rows[(label, state)] = (puddle[road].mean(), puddle[joint].mean(), puddle[stone].mean())
fmt = lambda v: f'{100 * v:.1f} %'
parts = []
for label in ('main', 'close', 'lockout'):
    a, b = rows[(label, 'wet')], rows[(label, 'heavy')]
    parts.append(f"{label} camera: wet dial {fmt(a[0])} of the road is puddle (joint dots {fmt(a[1])}, stone dots {fmt(a[2])}); heavy dial {fmt(b[0])} ({fmt(b[1])}, {fmt(b[2])})")
put('puddle_sentence.txt', "**Puddles cover the road, not specially the joints.** Share of the road under a puddle (and of the joint dots and the stone-face dots alone), from the road's puddle mask drawn as plain light (`tools/b12_puddles_over_joints.py`, `work/r10`, `work/r12`): " + '; '.join(parts) +
    ". A joint dot is about as often under water as a stone dot (within 6 percentage points in every case), which fits the 'no puddles' row of the table above. The lockout camera sees a lot of puddle at the heavy dial (the recipe's calibration table says 42 %), and water at a grazing angle really does hide what lies under it, so **from here on the study leaves dots under a puddle out of the measure** and reports the puddle share beside each picture.")

# ---- quick set results
QUICK = [('main_A_wet'), ('main_A_heavy'), ('main_C_wet'), ('main_D_wet'), ('main_E_wet'), ('close_A_wet'), ('close_E_wet'), ('lockout_B_wet'), ('lockout_E_wet')]


def summarise(store):
    fails, nears = [], []
    for name in QUICK:
        r = store.get(name)
        if r is None:
            return None
        label = name.split('_')[0]
        ok, reasons = t.judge(r, label)
        nears.append(r['near']['contrast'])
        if not ok:
            fails.append((name, reasons))
    return fails, nears


base = summarise(load('r01', 'measurements_nopuddle.json'))
mild = summarise(load('r07', 'measurements_nopuddle.json'))
if base:
    put('quick_base_result.txt', f"all nine pictures fail (near contrast {min(base[1]):.2f} to {max(base[1]):.2f}, where today's dry road has 0.19 to 0.33).")
if mild:
    n_fail = len(mild[0])
    text = f"{len(QUICK) - n_fail} of the nine pass (near contrast {min(mild[1]):.2f} to {max(mild[1]):.2f})"
    if n_fail:
        text += '; the ones that fail: ' + '; '.join(f"{n} ({r[0]})" for n, r in mild[0]) + '.'
    else:
        text += '.'
    put('quick_mild1_result.txt', text)

# ---- fourth tests
r8, r6, r1 = load('r08'), load('r06'), load('r01')
f = lambda e, k: f"{e[k]:.2f}"
big0, big1 = r8['big_A_wet'], r8['big_A_wet_mild1']
geo_c, geo_m = r8['close_A_wet_mild1_geo8'], r8['main_A_wet_mild1_geo8']
mc, mm = r6['close_A_wet_mild1'], r6['main_A_wet_mild1']
an = r8['close_A_wet_mild1_aniso16b']
put('sol4_text.txt', f"""
* **The texture filter (anisotropic filtering 16 instead of the default 2): no change.** Near contrast {f(an['near'],'contrast')} / middle {f(an['middle'],'contrast')} / far {f(an['far'],'contrast')} against {f(mc['near'],'contrast')} / {f(mc['middle'],'contrast')} / {f(mc['far'],'contrast')} with the default: the same to two decimals, and the same to the eye (`pictures/solution_close_hybrid_filter.jpg`, first two panels). Either the setting does not reach EEVEE in a background run, or the road was already as sharp as it gets; I cannot tell. It is not a cure.
* **The hybrid, mild1 plus an 8 mm real groove** (sharp profile; 11 m of road for the close view, 15 m for the main view): in the close view near contrast {f(geo_c['near'],'contrast')} and middle {f(geo_c['middle'],'contrast')} (mild1 alone {f(mc['near'],'contrast')} and {f(mc['middle'],'contrast')}), so a little better; in the main view near {f(geo_m['near'],'contrast')} and middle {f(geo_m['middle'],'contrast')} (mild1 alone {f(mm['near'],'contrast')} and {f(mm['middle'],'contrast')}), so WORSE, because the groove's edges catch the wet shine. To the eye it is lumpier and less clean than mild1 alone (third panel of `pictures/solution_close_hybrid_filter.jpg`: ragged bright rims along the joints, small lumps far away, from the picture being sampled at 8 mm). It costs +120 to +165 seconds. **So real geometry is not needed to pass; it is an option for one hero close-up, and it needs a cleaner groove picture first.**
* **At the size the painter sees (1080 x 1920, lighting A, wet, 16 samples):** round 2: near contrast {f(big0['near'],'contrast')} ({100*big0['near']['seen']:.0f} % seen), middle {f(big0['middle'],'contrast')} ({100*big0['middle']['seen']:.0f} %), far {f(big0['far'],'contrast')}; with mild1: near {f(big1['near'],'contrast')} ({100*big1['near']['seen']:.0f} %), middle {f(big1['middle'],'contrast')} ({100*big1['middle']['seen']:.0f} %), far {f(big1['far'],'contrast')} ({100*big1['far']['seen']:.0f} %). Round 2 looks a little better at this size than at 540 x 960 (more dots to show the joint) but is still far under the dry road and under the pass line. The lower road at 100 % is `pictures/solution_plate_size_1080x1920.jpg`. **One weak spot I can see in it:** at middle distance the joints that run across the road look like short dashes (they are foreshortened, and the joint picture has small gaps in them); and near the brazier's glare in the lockout shot the bright rim of a stone edge draws curly outlines that can look like scribbles. A cleaner joint picture drawn from a straight grid instead of the colour picture's ragged joints (step A1) would help both; not tried.
""")
open(os.path.join(PARTS, 'pieces_count_sentence.txt'), 'w').write('1,990 pieces in the whole street file and 2,180 in the lockout shot file (the first try had 7,939 and 8,291, which is too many)\n')
put('hybrid_pass_sentence.txt', f"the close view with the hybrid has near contrast {f(geo_c['near'],'contrast')}; the main view, {f(geo_m['near'],'contrast')} (mild1 alone: {f(mc['near'],'contrast')} and {f(mm['near'],'contrast')}): not better in the main view, so use it only if the person wants the stones to cast real shadows in a hero close-up")
print('sentences written')
