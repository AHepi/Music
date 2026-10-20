# What this does: one picture with every recipe next to its reference: reference colour | my colour | reference height | my height | reference normal | my normal, 220 px each.
# Run (plain Python): python3 -I make_overview_sheet.py
import os
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.abspath(os.path.join(HERE, '..', '..', 'reference'))
rows = [('brick', 'brick'), ('slate', 'slate'), ('wood', 'wood'), ('metal', 'metal'), ('mud', 'mud'), ('gravel', 'gravel (rigid body)'), ('gravel', 'gravel (nodes only)')]
cell = 220
def load(path, grey=False):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img.dtype == np.uint16:
        img = (img / 257.0).astype(np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return cv2.resize(img[..., :3], (cell, cell), interpolation=cv2.INTER_AREA)
def banner(text):
    b = np.full((22, cell, 3), 245, np.uint8)
    cv2.putText(b, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
    return b
tiles = []
for ref_name, label in rows:
    folder = os.path.join(HERE, 'out', 'full', {'gravel (rigid body)': 'gravel', 'gravel (nodes only)': 'gravel_gn'}.get(label, ref_name))
    if not os.path.exists(os.path.join(folder, 'colour.png')):
        continue
    row = []
    for title, path in ((f'reference {ref_name}', os.path.join(REF, ref_name, 'colour.png')), (f'mine: {label}', os.path.join(folder, 'colour.png')),
                        ('reference height', os.path.join(REF, ref_name, 'height.png')), ('my height', os.path.join(folder, 'height.png')),
                        ('reference normal', os.path.join(REF, ref_name, 'normal.png')), ('my normal (Sobel)', os.path.join(folder, 'normal.png'))):
        row.append(np.vstack([banner(title), load(path)]))
    tiles.append(np.hstack(row))
cv2.imwrite(os.path.join(HERE, 'out', 'overview_all_recipes.png'), np.vstack(tiles))
print('ok', len(tiles))
