"""GROUND builder: picture measures. usage: python3 -I metrics.py lr before.jpg after.jpg ...   (lr = the lower-right crop 1080x448 at 2400 res)
                                              python3 -I metrics.py full a.png b.png ...        (2400x1600 pictures: boxes of the hf script + guard numbers)"""
import sys, colorsys
import numpy as np
from PIL import Image, ImageFilter

BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700),
         "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050)}


def energy(a_lum, box):
    g = Image.fromarray((a_lum * 255).astype(np.uint8))
    blur = np.asarray(g.filter(ImageFilter.GaussianBlur(2))).astype(np.float32)
    hf = np.abs(np.asarray(g).astype(np.float32) - blur)
    x0, y0, x1, y1 = box
    return float(hf[y0:y1, x0:x1].mean())


def hue_deg(rgb):
    h, s, v = colorsys.rgb_to_hsv(*[float(x) for x in rgb])
    return h * 360.0


def run(mode, files):
    for f in files:
        im = Image.open(f).convert('RGB')
        a = np.asarray(im).astype(np.float32) / 255
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        mx, mn = a.max(-1), a.min(-1)
        sat = (mx - mn) / np.maximum(mx, 1e-4)
        if mode == 'lr':
            box = (180, 198, 1080, 448)
            e = energy(lum, box)
            x0, y0, x1, y1 = box
            m = a[y0:y1, x0:x1].reshape(-1, 3)
            # lawn only: leave out pixels that are very bright (kerb, gravel) 
            sel = lum[y0:y1, x0:x1].reshape(-1) < 0.55
            print('%-28s energy(grass box) %.2f  mean lum %.3f  lawn mean lum %.3f  lawn hue %.1f  lawn sat %.3f' % (f.split('/')[-1], e, lum[y0:y1, x0:x1].mean(), lum[y0:y1, x0:x1].reshape(-1)[sel].mean(), hue_deg(m[sel].mean(0)), sat[y0:y1, x0:x1].mean()))
        else:
            if im.size != (2400, 1600):
                im = im.resize((2400, 1600), Image.LANCZOS)
                a = np.asarray(im).astype(np.float32) / 255
                lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
                mx, mn = a.max(-1), a.min(-1)
                sat = (mx - mn) / np.maximum(mx, 1e-4)
            es = {k: energy(lum, b) for k, b in BOXES.items()}
            p = np.percentile(lum, [1, 5, 25, 50, 75, 95, 99])
            x0, y0, x1, y1 = BOXES['grass fg']
            m = a[y0:y1, x0:x1].reshape(-1, 3)
            sel = lum[y0:y1, x0:x1].reshape(-1) < 0.55
            print(f.split('/')[-1])
            print('   energy ' + ' '.join('%s %.2f' % (k, v) for k, v in es.items()))
            print('   lum pct 1/5/25/50/75/95/99: ' + ' '.join('%.3f' % v for v in p) + '   mean sat %.3f' % sat.mean())
            print('   grass box: lawn lum %.3f  hue %.1f' % (lum[y0:y1, x0:x1].reshape(-1)[sel].mean(), hue_deg(m[sel].mean(0))))


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2:])
