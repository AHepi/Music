# What this does (plain words): checks the big 2508 x 2508 gravel picture (2 x 2 tiles of NEW content from one description) for seams and repeats.
# (1) Seam jump: how much the picture changes between two neighbouring dot columns/rows exactly at the middle lines (x = 1254, y = 1254) and at the wrap-around edge,
#     compared with the same measure on ordinary columns/rows (ratio about 1.0 = no seam). (2) Repeats: the four 1254 x 1254 quadrants are compared with each other
#     (SSIM and best shifted overlap): a copied tile would give SSIM 1.0, different content gives about the "two different tiles" level.
# (3) Writes a preview (area_preview.png, 1254 dots) and the numbers (area_report.json). Use: python3 -I area_report.py AREA_FOLDER OUT_FOLDER
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(G, '..', '..', 'lib'))
import pixel_compare as pc
folder, out = sys.argv[1], sys.argv[2]
img = cv2.imread(os.path.join(folder, 'colour.png')).astype(np.float64)
n = img.shape[0]; half = n // 2
col_jump = np.abs(np.diff(img, axis=1, append=img[:, :1])).mean(axis=(0, 2))          # change between column i and i+1 (wrapping)
row_jump = np.abs(np.diff(img, axis=0, append=img[:1])).mean(axis=(1, 2))
typical_c, typical_r = float(np.median(col_jump)), float(np.median(row_jump))
report = {'size': n, 'middle_vertical_seam_ratio': round(float(col_jump[half - 1] / typical_c), 3), 'middle_horizontal_seam_ratio': round(float(row_jump[half - 1] / typical_r), 3),
          'wrap_vertical_seam_ratio': round(float(col_jump[n - 1] / typical_c), 3), 'wrap_horizontal_seam_ratio': round(float(row_jump[n - 1] / typical_r), 3)}
grey = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float64)
q = [grey[:half, :half], grey[:half, half:], grey[half:, :half], grey[half:, half:]]
sims = []
for i in range(4):
    for j in range(i + 1, 4):
        sims.append(round(pc.ssim(q[i], q[j]), 3))
report['quadrant_pair_ssim'] = sims
report['quadrant_pair_ssim_max'] = max(sims)
# contrast: a copy of one tile repeated 2 x 2 would give 1.0 for every pair
# best shifted overlap: does any quadrant contain a shifted copy of another? normalised cross-correlation by FFT
def ncc_peak(a, b):
    a = (a - a.mean()) / (a.std() + 1e-9); b = (b - b.mean()) / (b.std() + 1e-9)
    f = np.fft.ifft2(np.fft.fft2(a) * np.conj(np.fft.fft2(b))).real / a.size
    return float(f.max())
report['quadrant_best_shift_correlation_max'] = round(max(ncc_peak(q[i], q[j]) for i in range(4) for j in range(i + 1, 4)), 3)
# for contrast: the same measure for one tile against itself shifted by 600 dots (a repeat): the peak would be 1.0
report['quadrant_self_shift_correlation_for_contrast'] = round(ncc_peak(q[0], np.roll(q[0], (600, 300), axis=(0, 1))), 3)
os.makedirs(out, exist_ok=True)
json.dump(report, open(os.path.join(out, 'area_report.json'), 'w'), indent=1)
cv2.imwrite(os.path.join(out, 'area_preview_1254.png'), cv2.resize(img.astype(np.uint8), (1254, 1254), interpolation=cv2.INTER_AREA))
print(json.dumps(report, indent=1))
