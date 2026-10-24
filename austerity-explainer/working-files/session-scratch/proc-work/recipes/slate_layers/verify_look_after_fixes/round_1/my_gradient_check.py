# What this does (plain words): checks the paint "busy-ness" two other ways than the tuner did, to see whether the tuner's gradient
# improvement (9.4 -> 7.5, reference 5.5) holds: plain grey vs Lab lightness, at 1254 or 900 dots, over the whole picture or only
# inside the slates, and it measures the fine grain (tiny speckle) separately.
import cv2
import numpy as np
P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
S = {'reference': P + 'reference/slate/colour.png', 'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png', 'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
print('%-10s %-34s %8s %8s %8s' % ('picture', 'measure', 'median', 'mean', 'p90'))
for name, path in S.items():
    bgr = cv2.imread(path)
    for size in (1254, 900):
        im = bgr if size == 1254 else cv2.resize(bgr, (size, size), interpolation=cv2.INTER_AREA)
        lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(float)
        light = lab[..., 0] * 100 / 255
        grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
        slate = cv2.erode((light > 12).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
        for label, plane in (('Lab-L Sobel', light), ('grey Scharr/16', grey)):
            if 'Sobel' in label:
                gx, gy = cv2.Sobel(plane, cv2.CV_64F, 1, 0, ksize=3), cv2.Sobel(plane, cv2.CV_64F, 0, 1, ksize=3)
            else:
                gx, gy = cv2.Scharr(plane, cv2.CV_64F, 1, 0) / 16, cv2.Scharr(plane, cv2.CV_64F, 0, 1) / 16
            g = np.hypot(gx, gy)
            for where, mask in (('whole', np.ones_like(slate)), ('inside slates', slate)):
                v = g[mask]
                print('%-10s %-34s %8.2f %8.2f %8.2f' % (name, '%d dots, %s, %s' % (size, label, where), np.median(v), v.mean(), np.percentile(v, 90)))
    # fine grain: inside flat patches only, std of grey minus its 5x5 box mean, at 1254
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(float)
    box = cv2.blur(grey, (5, 5))
    rng = cv2.dilate(grey, np.ones((7, 7))) - cv2.erode(grey, np.ones((7, 7)))
    flat = (rng <= 6) & (grey > 30)
    print('%-10s %-34s %8.3f   (flat dots: %.1f%%)' % (name, 'fine grain std in flat patches', (grey - box)[flat].std(), flat.mean() * 100))
    print()
