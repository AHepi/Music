# What this does (inside Blender): takes a baked folder (colour.png, height.png) and writes FOLDER_smooth with the height blurred by sigma pixels (wrapping at the
# edges, so the tile stays seamless) and the normal map made again from that smoothed height with Sobel (strength fitted to the slate reference).
# Use: blender -b --python post_smooth_height.py -- FOLDER SIGMA REFERENCE
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import hp_tools as hp
bh = hp.bh
folder, sigma, reference = sys.argv[sys.argv.index('--') + 1:][:3]
sigma = float(sigma)
def blur_wrap(a, sigma):
    radius = int(np.ceil(sigma * 3)); xs = np.arange(-radius, radius + 1); k = np.exp(-xs ** 2 / (2 * sigma ** 2)); k /= k.sum()
    out = sum(k[i] * np.roll(a, radius - i, axis=1) for i in range(len(k)))
    return sum(k[i] * np.roll(out, radius - i, axis=0) for i in range(len(k)))
h = hp.load(os.path.join(folder, 'height.png'))[..., 0]
hs = blur_wrap(h, sigma)
out = folder + '_smooth'
os.makedirs(out, exist_ok=True)
hp.save(hp.load(os.path.join(folder, 'colour.png')), os.path.join(out, 'colour.png'))
hp.save(hs, os.path.join(out, 'height.png'), sixteen=True)
strength = bh.fit_sobel_strength(hs, bh.reference_normal_slope_spread(reference))
hp.save(bh.sobel_normal(hs, strength) * 0.5 + 0.5, os.path.join(out, 'normal.png'))
print('wrote', out, 'strength', strength)
