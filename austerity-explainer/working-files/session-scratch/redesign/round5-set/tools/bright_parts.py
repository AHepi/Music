# What this does: shows where the brightest 3% of a picture lie (as the shot checker counts them: a slight blur first),
# and how many of them fall on each measured group (scratch look, round 5).
# Use: python3 bright_parts.py PICTURE FACTS_FOLDER OUT.jpg
import sys, json, os
import cv2, numpy as np
picture, facts, out = sys.argv[1:4]
img = cv2.imread(picture)
h, w = img.shape[:2]
grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
blur = cv2.GaussianBlur(grey, (0, 0), w * 0.01)
limit = np.quantile(blur, 0.97)
bright = blur >= limit
f = json.load(open(os.path.join(facts, 'facts.json')))
ids = cv2.cvtColor(cv2.imread(os.path.join(facts, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
total = bright.sum()
print(f'threshold {limit:.3f}, {total} pixels')
shares = {}
for g, info in f['groups'].items():
    m = np.abs(ids - np.array(info['colour'])).sum(axis=2) < 24
    shares[g] = (bright & m).sum() / total
setmask = np.abs(ids - np.array([64, 64, 64])).sum(axis=2) < 24
shares['(the set)'] = (bright & setmask).sum() / total
shares['(sky)'] = (bright & (ids.sum(axis=2) < 24)).sum() / total
for g, v in sorted(shares.items(), key=lambda kv: -kv[1]):
    if v > 0.005:
        print(f'  {g}: {v:.0%}')
n, labels, stats, cents = cv2.connectedComponentsWithStats(bright.astype(np.uint8))
order = np.argsort(-stats[1:, cv2.CC_STAT_AREA])[:8] + 1
for k in order:
    print(f'  patch at {cents[k][0] / w:.2f} across, {cents[k][1] / h:.2f} down: {stats[k, cv2.CC_STAT_AREA] / total:.0%}')
show = img.copy()
show[bright] = (0.5 * show[bright] + np.array([0, 0, 127])).astype(np.uint8)
cv2.imwrite(out, cv2.resize(show, (w // 2, h // 2)), [cv2.IMWRITE_JPEG_QUALITY, 85])
