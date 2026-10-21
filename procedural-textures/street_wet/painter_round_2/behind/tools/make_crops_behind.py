"""What this file does (plain words): makes look-by-eye pictures of the behind painting: for each place where a near prop stood, the plate without props | the front painting | the behind painting as the painter made it (lined up, free sky) | the behind painting after the free colour match, all at 100 percent (1 dot = 1 dot).
Run: python3 -I tools/make_crops_behind.py   (reads work/behind_with_free_sky.png and work/behind_matched.png; writes pictures_look/)"""
import os, json, cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
PAINT = 'proc-work/street_wet/painter_round_2/paint/'
PL = 'proc-work/street_wet/painter_round_2/plate/'
os.makedirs(P('pictures_look'), exist_ok=True)
W, H = 1536, 2730
imgs = [cv2.imread(PL + 'lockout_plate_wet_round2_no_props.png'), cv2.imread(PAINT + 'front_painting_final.png'), cv2.imread(P('work/behind_with_free_sky.png')), cv2.imread(P('work/behind_matched.png'))]
names = ['plate without props', 'front painting', 'behind (as painted)', 'behind (colour matched)']
f = json.load(open(PAINT + 'alignment/facts/facts.json'))
ids = cv2.cvtColor(cv2.imread(PAINT + 'alignment/facts/ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
def mask(g):
    m = (np.abs(ids - np.array(f['groups'][g]['colour'])).sum(axis=2) < 24).astype(np.uint8)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST) > 0
places = {'drum_and_board': ['drum', 'notice', 'board posts', 'pail'], 'sacks': ['sacks'], 'coal_pile': ['coal pile'], 'handcart_and_spade': ['handcart', 'spade'], 'dustbins': ['dustbins']}
for key, groups in places.items():
    m = np.zeros((H, W), bool)
    for g in groups: m |= mask(g)
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    pad = 60
    x0, x1, y0, y1 = max(0, x0 - pad), min(W, x1 + pad), max(0, y0 - pad), min(H, y1 + pad)
    # keep the crop sheet a sensible size: at most 520 wide and 700 tall per picture
    cw, ch = x1 - x0, y1 - y0
    s = min(1.0, 520 / cw, 760 / ch)
    tiles = []
    for im, n in zip(imgs, names):
        t = im[y0:y1, x0:x1].copy()
        if s < 1: t = cv2.resize(t, (int(cw * s), int(ch * s)), interpolation=cv2.INTER_AREA)
        cv2.putText(t, n, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(t, n, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(t)
    sheet = np.hstack(tiles)
    cv2.imwrite(P('pictures_look/crop_%s.jpg' % key), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(key, (x0, y0, x1, y1), 'scale', round(s, 2), sheet.shape)
