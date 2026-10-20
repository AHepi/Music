# Plain note: measures the brick reference picture: finds the mortar lines (the pale gaps between bricks) and prints the row
# height, number of rows, brick lengths and the typical colours of brick and mortar. Run: python3 -I analyse_brick_layout.py REFERENCE_FOLDER
import sys, numpy as np, cv2, json
ref = sys.argv[1]
col = cv2.imread(ref + '/colour.png')[..., ::-1].astype(float)
hei = cv2.imread(ref + '/height_as_uploaded.png', cv2.IMREAD_UNCHANGED).astype(float)
if hei.ndim == 3: hei = hei[..., 0]
hsv = cv2.cvtColor(col.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(float)
sat = hsv[..., 1]; val = hsv[..., 2]
H, W = hei.shape
# mortar = low-saturation or very low height
mortar = (hei < np.percentile(hei, 22))
print('height pct', [int(np.percentile(hei, p)) for p in (5, 22, 50, 80, 95)])
# horizontal mortar lines: row profile of mortar fraction
rowfrac = mortar.mean(axis=1)
# smooth and find peaks
k = 9
rf = np.convolve(np.r_[rowfrac[-k:], rowfrac, rowfrac[:k]], np.ones(k) / k, 'same')[k:-k]
peaks = [y for y in range(H) if rf[y] > 0.55 and rf[y] >= rf[max(0, y - 20):y + 20].max()]
print('row-mortar peaks', peaks, 'pitches', np.diff(peaks))
# autocorrelation of row profile
ac = np.fft.irfft(np.abs(np.fft.rfft(rowfrac - rowfrac.mean())) ** 2)
ac /= ac[0]
cand = [(i, round(ac[i], 2)) for i in range(40, 400) if ac[i] > ac[i - 1] and ac[i] > ac[i + 1] and ac[i] > 0.2]
print('row autocorr peaks', cand[:8])
# mean colours
brick = ~mortar
for name, m in (('brick', brick), ('mortar', mortar)):
    print(name, 'mean RGB', col[m].mean(axis=0).round(0), 'std', col[m].std(axis=0).round(0), 'fraction', round(m.mean(), 3))
