# What this does (plain python): draws the 8-colour k-means palette of every reference as a coloured bar (bar width = share of the picture) with the hex codes,
# from ../data/reference_measurements.json. One row per surface.
import json, os, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.abspath(os.path.join(HERE, '..'))
d = json.load(open(os.path.join(BASE, 'data', 'reference_measurements.json')))
rows = []
W, H = 1400, 70
for name in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel', 'mud_golden']:
    img = np.full((H + 18, W + 130, 3), 255, np.uint8)
    cv2.putText(img, name, (4, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
    x = 130
    for p in d[name]['palette_8']:
        w = int(round(W * p['share_percent'] / 100.0))
        hexc = p['hex'].lstrip('#'); bgr = tuple(int(hexc[i:i + 2], 16) for i in (4, 2, 0))
        img[0:H, x:x + w] = bgr
        lum = 0.114 * bgr[0] + 0.587 * bgr[1] + 0.299 * bgr[2]
        col = (255, 255, 255) if lum < 110 else (0, 0, 0)
        cv2.putText(img, p['hex'], (x + 4, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 1, cv2.LINE_AA)
        cv2.putText(img, f"{p['share_percent']:.0f}%", (x + 4, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.42, col, 1, cv2.LINE_AA)
        x += w
    rows.append(img)
out = np.vstack(rows)
cv2.imwrite(os.path.join(BASE, 'pictures', 'a03_reference_palettes.png'), out)
print(out.shape)
