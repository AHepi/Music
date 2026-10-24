"""What this file does (plain words): draws two grey pictures of the weathering kit's marks, so the number "the painting follows the kit" can be checked by eye:
left = what the kit added to the plate (kit plate minus no-kit plate, fine-to-medium brightness pattern, mid-grey = nothing, lighter = the kit brightened, darker = the kit darkened);
right = what the painting has that the no-kit plate's own pattern does not explain (same scale). Sky left out. Writes work/marks_kit_vs_painting.jpg.
Run: python3 -I tools/make_marks_pictures.py"""
import numpy as np, cv2, os, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B_ = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
W, H = 1536, 2730
def load(p): return cv2.resize(cv2.imread(p), (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)
K = load(B_ + 'grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png'); Bp = load(B_ + 'grime_and_growth/integrated/plates/lockout/final_lockout_B_wet_base.png'); P = load(os.path.join(HERE, 'pictures/kit_painting_lined_up.png'))
lum = lambda im: (0.2126 * im[:, :, 2] + 0.7152 * im[:, :, 1] + 0.0722 * im[:, :, 0]) / 255
G = lambda x, s: cv2.GaussianBlur(x, (0, 0), s)
LK, LB, LP = lum(K), lum(Bp), lum(P)
s1, s2 = 4, 30
hb, hp, hk = G(LB, s1) - G(LB, s2), G(LP, s1) - G(LP, s2), G(LK, s1) - G(LK, s2)
ids = cv2.imread(B_ + 'painter_test/alignment/facts/ids.png').astype(np.int32)
sky = cv2.resize((ids.sum(axis=2) < 24).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
sky = cv2.dilate(sky.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
ns = ~sky
a = float(np.cov(hb[ns], hp[ns])[0, 1] / hb[ns].var())
delta, resid = hk - hb, hp - a * hb
gain = 6.0
def pic(x): 
    v = np.clip(0.5 + gain * x, 0, 1); v[sky] = 0.5
    return (cv2.resize(v, (576, 1024), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)
sheet = np.concatenate([pic(delta), np.full((1024, 6), 255, np.uint8), pic(resid)], axis=1)
cv2.imwrite(os.path.join(HERE, 'work/marks_kit_vs_painting.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
print('fit a =', round(a, 3), 'std of kit marks', round(float(delta[ns].std()), 4), 'std of painting leftover', round(float(resid[ns].std()), 4))
