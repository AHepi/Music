# Plain note: puts the intermediate pictures of a "probe" export side by side on one sheet (each shrunk to 400 px, with its name),
# so you can see what every part of a Material Maker graph is doing. Run: python3 -I probe_sheet.py RAW_FOLDER STEM OUT.png "label0,label1,..."
# (labels are written under the pictures in this order: albedo, emission, rough, metal, occlusion, displace, sss)
import sys, os
import numpy as np, cv2
raw, stem, out = sys.argv[1:4]
labels = sys.argv[4].split(',') if len(sys.argv) > 4 else []
files = [f'{stem}_albedo.png', f'{stem}_emission.png', f'{stem}_rough.png16.png', f'{stem}_metal.png16.png', f'{stem}_occlusion.png16.png', f'{stem}_displace.png16.png', f'{stem}_sss.png16.png']
tiles = []
for i, f in enumerate(files):
    p = os.path.join(raw, f)
    if not os.path.exists(p):
        continue
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im.dtype == np.uint16:
        im = (im / 257.0).astype(np.uint8)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    im = im[..., :3]
    im = cv2.resize(im, (400, 400), interpolation=cv2.INTER_AREA)
    cv2.putText(im, labels[i] if i < len(labels) else f, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    tiles.append(im)
cols = 4
while len(tiles) % cols:
    tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[r * cols:(r + 1) * cols]) for r in range(len(tiles) // cols)]
cv2.imwrite(out, np.vstack(rows))
print('sheet', out)
