"""
Plain note: this is the look checker's own repeat finder (written by the independent checker, not the builder).
What it does: it cuts small picture pieces (a bit smaller than one board) out of the big 4 x 4 wood area,
and looks everywhere else in the same area for the best match, also with the match turned left-right and
upside-down (because the recipe flips its pieces). The score is 1.0 for an exact copy and about 0.3 or
less for two unrelated pieces of wood. It writes a JSON list and a picture sheet of the closest matches.
"""
import sys, json
import numpy as np
from PIL import Image

BASE = 'proc-work/'
OUT = BASE + 'recipes/wood_from_displacement/check_look_round_1/'


def ncc_map(img, patch):
    """normalised cross correlation of patch against every position of img (valid positions only)."""
    H, W = img.shape
    ph, pw = patch.shape
    p = patch - patch.mean()
    pn = np.sqrt((p * p).sum()) + 1e-9
    # FFT size
    fh, fw = H + ph, W + pw
    F = np.fft.rfft2(img, (fh, fw))
    P = np.fft.rfft2(p[::-1, ::-1], (fh, fw))
    cc = np.fft.irfft2(F * P, (fh, fw))[ph - 1:H, pw - 1:W]
    # local sums by integral images
    I = np.pad(img, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    I2 = np.pad(img * img, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    def box(M):
        return M[ph:, pw:] - M[:-ph, pw:] - M[ph:, :-pw] + M[:-ph, :-pw]
    s = box(I)
    s2 = box(I2)
    n = ph * pw
    var = s2 - s * s / n
    var[var < 1e-9] = 1e-9
    return cc / (pn * np.sqrt(var))


def main(path, tag, ph=100, pw=190, n=60, seed=3, is_rgb=False):
    im = Image.open(path)
    if is_rgb:
        a = np.asarray(im.convert('L'), dtype=np.float64)
    else:
        a = np.asarray(im.convert('L'), dtype=np.float64)
    H, W = a.shape
    rng = np.random.default_rng(seed)
    res = []
    for k in range(n):
        y = int(rng.integers(20, H - ph - 20))
        x = int(rng.integers(20, W - pw - 20))
        patch = a[y:y + ph, x:x + pw]
        if patch.std() < 8:
            continue
        best = (-1, None)
        for flip in ['none', 'lr', 'ud', 'both']:
            pp = patch
            if flip in ('lr', 'both'):
                pp = pp[:, ::-1]
            if flip in ('ud', 'both'):
                pp = pp[::-1, :]
            m = ncc_map(a, np.ascontiguousarray(pp))
            # blank out own neighbourhood (self match and shifted overlap)
            y0, y1 = max(0, y - ph), min(m.shape[0], y + ph)
            x0, x1 = max(0, x - pw), min(m.shape[1], x + pw)
            m[y0:y1, x0:x1] = -1
            idx = np.unravel_index(np.argmax(m), m.shape)
            v = float(m[idx])
            if v > best[0]:
                best = (v, (flip, int(idx[0]), int(idx[1])))
        res.append({'y': y, 'x': x, 'score': round(best[0], 3), 'flip': best[1][0], 'my': best[1][1], 'mx': best[1][2]})
        print(k, res[-1], flush=True)
    json.dump(res, open(OUT + f'repeats_{tag}.json', 'w'), indent=1)
    sc = np.array([r['score'] for r in res])
    print(tag, 'patches', len(sc), 'median', np.median(sc), 'p90', np.percentile(sc, 90),
          'share>0.6', (sc > 0.6).mean(), 'share>0.7', (sc > 0.7).mean(), 'share>0.8', (sc > 0.8).mean())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
