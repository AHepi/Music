# What this does (plain words): measures how much the brightness of the SLATE paint (not the black joints) varies SIDEWAYS at different
# sizes (a few dots = fine strokes, tens of dots = streaks, hundreds of dots = whole slates), after removing what is the same along the whole row.
# It tells which size of variation a baked picture has too little or too much of compared with the reference. A measurement for hand-tuning only.
# Use: python3 -I sideways_bands.py PICTURE ...
import sys, cv2, numpy as np
PROC = 'proc-work'
def lightness(path):
    img = cv2.imread(path); img = cv2.resize(img, (1254, 1254), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)[..., 0] * 100 / 255
def blur_x(a, w, s):
    # wrap-around horizontal gaussian blur of a (weighted by w): normalised convolution, done by padding the picture sideways first
    k = int(s * 4) | 1
    pad = k
    def one(x):
        x = np.concatenate([x[:, -pad:], x, x[:, :pad]], axis=1)
        return cv2.GaussianBlur(x, (k, 1), s)[:, pad:-pad]
    return one(a * w) / np.maximum(one(w), 1e-3)
sig = [0.01, 3, 8, 20, 50, 120]
for name, path in [('reference', PROC + '/reference/slate/colour.png')] + [(p, p) for p in sys.argv[1:]]:
    L = lightness(path); w = (L > 14).astype(np.float32)
    levels = [blur_x(L, w, s) for s in sig]
    row_mean = (L * w).sum(1, keepdims=True) / np.maximum(w.sum(1, keepdims=True), 1) * np.ones_like(L)
    out = []
    for i in range(len(sig) - 1):
        d = (levels[i] - levels[i + 1])
        out.append(float((d * d * w).sum() / w.sum()))
    d = levels[-1] - row_mean; out.append(float((d * d * w).sum() / w.sum()))
    print(f'{name.split("/")[-1]:>22}: variance by sideways size  3-8: {out[0]:5.1f}   8-20: {out[1]:5.1f}   20-50: {out[2]:5.1f}   50-120: {out[3]:5.1f}   120+: {out[4]:5.1f}   (fine <3: {out[0]*0:.0f})')
