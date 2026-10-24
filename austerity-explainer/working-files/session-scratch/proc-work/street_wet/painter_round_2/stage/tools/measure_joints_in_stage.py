"""What this file does (plain words): measures whether the sett joints (the thin lines between the cobbles) survive the stage, with the SAME measure the plate step and the front painting step used (measure_grid_visibility.py: for the dots next to a joint, how much they differ
from the stone beside them, as a share of the stone's brightness, "line"; and the stone's own mottling "texture"; a grid counts as visible when line >= 0.12 and line >= 2 x texture), using Blender's joint mask for the lockout camera.
The stage's plate view shows the middle 90 percent of the plate (a narrower lens), so each stage picture (1080 x 1920) is put back into plate space (1536 x 2730) over that middle part, and the mask is cut to the same part.
Pictures measured: the painting itself (the same part), the stage with NOTHING of its finish left (only the painting passed through: shows what the stage's own sharpness and the narrower lens cost), the stage before the fix and after it.
Writes numbers/joints_in_stage.json. Run: python3 -I tools/measure_joints_in_stage.py
"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from stage_common import k, P, load01
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate/'
sys.path.insert(0, ROOT + 'setts/tools'); sys.path.insert(0, ROOT + 'study/tools')
from measure_grid_visibility import grid_visibility, visible
from b04_measure_joints import load_mask, load_puddles
W0, H0 = 1536, 2730
cw, ch = int(round(W0 * k)), int(round(H0 * k)); x0, y0 = (W0 - cw) // 2, (H0 - ch) // 2
J, S, R = load_mask(ROOT + 'rubbish/work/plates04/mask_lockout_1536x2730.png')
pud = load_puddles(ROOT + 'rubbish/work/plates04/lockout_A_wet_1536x2730_puddlemask.png')
inside = np.zeros((H0, W0), np.float32); inside[y0:y0 + ch, x0:x0 + cw] = 1
Jc, Sc, Rc = J * inside, S * inside, R * inside
def lum(img_bgr):
    b, g, r = [img_bgr[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def into_plate_space(L1080):
    canvas = np.zeros((H0, W0), np.float32)
    canvas[y0:y0 + ch, x0:x0 + cw] = cv2.resize(L1080, (cw, ch), interpolation=cv2.INTER_LINEAR)
    return canvas
paint = lum(cv2.imread(P('../paint/front_painting_final.png')))
pics = {'the painting itself (the same middle part, full sharpness)': paint,
        'stage with nothing of its finish left (painting passed through)': into_plate_space(lum(cv2.imread(P('stills/diagnosis/off_all/still-6.00.jpg')))),
        'stage before the fix': into_plate_space(lum(cv2.imread(P('stills/before/wet_projector/still-6.00.jpg')))),
        'stage after the fix': into_plate_space(lum(cv2.imread(P('stills/after/wet_projector/still-6.00.jpg'))))}
res = {}
print('sett joints on the wet road in the stage (line = how much the dots beside a joint differ from the stone; texture = the stone\'s own mottling; visible if line >= 0.12 and >= 2 x texture)')
for name, L in pics.items():
    g = grid_visibility(L, (Jc, Sc, Rc), pud)
    res[name] = {band: {**e, 'visible': bool(visible(e))} for band, e in g.items()}
    print(f"  {name:66s}" + ' | '.join(f"{b}: line {e['line']:.3f} tex {e['texture']:.3f} {'VISIBLE' if visible(e) else 'not seen'}" for b, e in g.items() if e['line'] is not None))
json.dump(res, open(P('numbers/joints_in_stage.json'), 'w'), indent=1)
