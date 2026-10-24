# What this does: prints the bill's colour band by band (the checker's "lit from below" measure) for a preview and a check folder.
import sys
import numpy as np
from PIL import Image
pic = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(float)
ids = np.asarray(Image.open(sys.argv[2] + '/facts/ids.png').convert('RGB')).astype(int)
m = (np.abs(ids - np.array([245, 130, 48])).sum(axis=2) < 6)
ys, xs = np.nonzero(m); span = ys.max() - ys.min()
rows = np.arange(m.shape[0])[:, None]
r, g, b = pic[..., 0], pic[..., 1], pic[..., 2]
hue = (r - b) / np.maximum(r + b, 1)
grey = pic.mean(axis=2) / 255
for k in range(0, 20, 2):
    band = m & (rows >= ys.min() + k * 0.05 * span) & (rows < ys.min() + (k + 2) * 0.05 * span)
    if band.sum():
        print(k, round(hue[band].mean(), 3), pic[band].mean(axis=0).round(0), 'burnt', round(float((pic[band].max(axis=1) >= 254).mean()), 2))
top = m & (rows < ys.min() + 0.15 * span); bot = m & (rows > ys.max() - 0.15 * span)
print('lift', round(hue[bot].mean() - hue[top].mean(), 3), 'median grey', round(float(np.median(grey[m])), 3))
