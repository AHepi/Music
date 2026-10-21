# Trial 22b: numbers from the finished pictures (plain Python with PIL and numpy; it only reads pictures).
import json
import numpy as np
from PIL import Image

def load(p):
    return np.asarray(Image.open(p).convert('RGB')).astype(float)

R = 'r3/'
pics = {
    'before_eevee': R + 'main_today_before_eevee.png',
    'addwear_eevee': R + 'main_today_addwear_eevee.png',
    'curv_eevee': R + 'main_today_curv_eevee.png',
    'curv2_eevee': 'r4/main_today_curv2_eevee.png',
    'baked512_a60_eevee': R + 'main_today_baked512_eevee.png',
    'baked1024_a60_eevee': R + 'main_today_baked1024_eevee.png',
    'baked512_sharp30_eevee': 'r4/main_today_baked512_sharp30_eevee.png',
    'before_cycles': R + 'main_before_cycles.png',
    'addwear_cycles': R + 'main_addwear_cycles.png',
}
P = {k: load(v) for k, v in pics.items()}
# door leaf, navy paint only: x 125..405, y 195..910, pixels that are blue-ish in the BEFORE picture of the same engine (so brass and bare stone are left out)
box = np.zeros(P['before_eevee'].shape[:2], bool)
box[195:910, 125:405] = True
navy = box & (P['before_eevee'][..., 2] >= P['before_eevee'][..., 0] - 2) & (P['before_cycles'][..., 2] >= P['before_cycles'][..., 0] - 2)
# stay off the pixels that are far from navy in either picture (frame shadows): keep it simple
def chips(a):
    return float(((a[..., 0] - a[..., 2]) > 8)[navy].mean())
out = {'door_leaf_pixels': int(navy.sum()), 'warm_chip_pixel_share': {k: round(chips(v), 4) for k, v in P.items()}}
d_cyc = (P['addwear_cycles'] - P['before_cycles']).mean(-1)
out['effect_vs_own_before'] = {}
for k in ('addwear_eevee', 'curv_eevee', 'curv2_eevee', 'baked512_a60_eevee', 'baked1024_a60_eevee', 'baked512_sharp30_eevee'):
    d = (P[k] - P['before_eevee']).mean(-1)
    out['effect_vs_own_before'][k] = {'mean_abs_change_0_255': round(float(np.abs(d)[navy].mean()), 2),
                                      'correlation_with_cycles_wear_change': round(float(np.corrcoef(d[navy], d_cyc[navy])[0, 1]), 3)}
out['effect_vs_own_before']['addwear_cycles'] = {'mean_abs_change_0_255': round(float(np.abs(d_cyc)[navy].mean()), 2)}
print(json.dumps(out, indent=1))
json.dump(out, open('numbers.json', 'w'), indent=1)
