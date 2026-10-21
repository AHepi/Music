# What this does (plain words): puts a "before" and an "after" picture side by side (optionally the same crop of both, optionally scaled) with a small label above each, and writes a JPEG.
# Use: python3 -I side_by_side.py BEFORE AFTER OUT [x0 y0 w h [scale]] [--labels "left text|right text"]
import sys, cv2, numpy as np
args = [a for a in sys.argv[1:] if not a.startswith('--labels')]
labels = ('before', 'after')
if '--labels' in sys.argv:
    labels = sys.argv[sys.argv.index('--labels') + 1].split('|')
    args = [a for a in args if a != sys.argv[sys.argv.index('--labels') + 1]]
before, after, out = args[:3]
box = list(map(int, args[3:7])) if len(args) >= 7 else None
scale = float(args[7]) if len(args) > 7 else 1.0
pics = []
for path, label in ((before, labels[0]), (after, labels[1])):
    im = cv2.imread(path)
    if box:
        x0, y0, w, h = box
        im = im[y0:y0 + h, x0:x0 + w]
    if scale != 1.0:
        im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
    bar = np.full((26, im.shape[1], 3), 24, np.uint8)
    cv2.putText(bar, label, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)
    pics.append(np.vstack([bar, im]))
gap = np.full((pics[0].shape[0], 6, 3), 24, np.uint8)
cv2.imwrite(out, np.hstack([pics[0], gap, pics[1]]), [cv2.IMWRITE_JPEG_QUALITY, 86])
