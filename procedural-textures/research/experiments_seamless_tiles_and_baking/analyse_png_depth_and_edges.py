# What this does: reads the pictures made by exp2a_colour_space_and_bit_depth.py and answers: is the "16-bit" PNG really 16-bit (file type), how many
# different grey levels does the gentle 0.40..0.60 ramp hold in 8 and 16 bit, and how close is a hard diagonal edge (u + v > 1) to the exact
# answer (the true fraction of each pixel that lies past the line) for each pixel filter and sample count.
# Run (plain Python):  python3 -I analyse_png_depth_and_edges.py out/colour_space
import glob
import json
import os
import sys

import cv2
import numpy as np

folder = sys.argv[1]
report = {}
for depth in ('8', '16'):
    image = cv2.imread(os.path.join(folder, f'q3_gentle_ramp_{depth}bit.png'), cv2.IMREAD_UNCHANGED)
    values = image[..., 0] if image.ndim == 3 else image
    report[f'ramp_{depth}bit'] = {'file_dtype': str(image.dtype), 'different_grey_levels': int(len(np.unique(values))),
                                  'ideal_for_0.2_of_the_range': int(round(0.2 * (255 if depth == '8' else 65535)))}

# exact coverage of the half plane u + v > 1 for a 64 x 64 picture (rows run top to bottom: v goes up the picture)
n = 64
sub = 32
coordinate = (np.arange(n * sub) + 0.5) / (n * sub)
u = coordinate[None, :]
v = coordinate[::-1][:, None]
exact = ((u + v) > 1.0).astype(np.float64).reshape(n, sub, n, sub).mean(axis=(1, 3))
edge_pixels = (exact > 0) & (exact < 1)
report['edge'] = {}
for path in sorted(glob.glob(os.path.join(folder, 'q4_edge_*.png'))):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
    grey = image[..., 0] if image.ndim == 3 else image
    error = np.abs(grey - exact)
    report['edge'][os.path.basename(path)[8:-4]] = {
        'mean_error_on_edge_pixels': round(float(error[edge_pixels].mean()), 4),
        'worst_error': round(float(error.max()), 3),
        'pixels_touched_by_blur_away_from_the_edge': int(((error > 0.01) & ~edge_pixels).sum()),
        'edge_pixels': int(edge_pixels.sum()),
    }
json.dump(report, open(os.path.join(folder, 'analysis.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))
