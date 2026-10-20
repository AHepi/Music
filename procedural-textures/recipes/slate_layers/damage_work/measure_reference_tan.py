# What this does (plain words): looks ONCE at the slate reference picture to measure the general character of the pale/tan
# "flaked" patches (how much of the picture they cover, their typical colours, and where along a row of slates they sit).
# It only measures; nothing from it is copied into the recipe except these few numbers, used to choose default settings.
import numpy as np, cv2, json
im = cv2.imread('../../../reference/slate/colour.png')          # BGR
rgb = im[..., ::-1].astype(np.float32)
lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
L = lab[..., 0] * 100 / 255.0
a = lab[..., 1] - 128
b = lab[..., 2] - 128
# 'tan or pale' = warm (b > 4 and a > -1) and fairly light; slate blue-grey has b < 0; olive moss is dark and greenish (a < 0)
warm = (b > 5) & (a > 0) & (L > 30)
pale = (L > 42)
tan = warm | (pale & (b > 0))
share = tan.mean()
print('share of picture that is tan or pale:', round(float(share), 4))
pix = rgb[tan]
# 4 clusters of the tan/pale pixel colours
data = pix.astype(np.float32)
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
_, labels, centres = cv2.kmeans(data, 4, None, crit, 5, cv2.KMEANS_PP_CENTERS)
counts = np.bincount(labels.flatten(), minlength=4)
order = np.argsort(-counts)
out = []
for i in order:
    c = centres[i]
    out.append(('#%02x%02x%02x' % tuple(int(round(x)) for x in c), round(float(counts[i] / counts.sum()), 3)))
print('tan/pale colour clusters (hex, share of tan pixels):', out)
# where along a row of slates? rows are 8 per tile with the picture edge cutting through the middle of a row (phase 0.5)
h = im.shape[0]
y = np.arange(h)
phase = ((y / (h / 8.0)) - 0.5) % 1.0            # 0 = top of the row, 1 = bottom (approx; rows differ by a few percent)
hist = np.zeros(10)
for k in range(10):
    sel = (phase >= k / 10) & (phase < (k + 1) / 10)
    hist[k] = tan[sel].mean()
print('share of tan by tenth of a row, top to bottom:', np.round(hist, 3).tolist())
# size of tan blobs: connected pieces
n, lab_cc, stats, cent = cv2.connectedComponentsWithStats(tan.astype(np.uint8), 8)
areas = stats[1:, cv2.CC_STAT_AREA]
areas = areas[areas >= 4]
print('tan blobs (>=4 dots):', len(areas), 'area percentiles 25/50/75/90/99 (dots):', np.percentile(areas, [25, 50, 75, 90, 99]).round(0).tolist())
eq = np.sqrt(areas / np.pi) * 2
print('equivalent diameter percentiles (dots) 25/50/75/90:', np.percentile(eq, [25, 50, 75, 90]).round(1).tolist())
widths = stats[1:, cv2.CC_STAT_WIDTH][stats[1:, cv2.CC_STAT_AREA] >= 4]
heights = stats[1:, cv2.CC_STAT_HEIGHT][stats[1:, cv2.CC_STAT_AREA] >= 4]
print('median blob height/width:', float(np.median(heights / widths)))
json.dump({'share': float(share), 'clusters': out, 'by_tenth_of_row': hist.tolist()}, open('reference_tan_measure.json', 'w'), indent=1)
