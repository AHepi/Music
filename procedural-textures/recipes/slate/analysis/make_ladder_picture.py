# What this does (plain words): draws the "ladder" picture for the guide: the same 300 x 300 dot patch of the reference and of each description class
# (layout only, layout + stamps, traced coarse, traced medium, traced fine), side by side with the size of each description. Plain Python.
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..')); PROC = os.path.abspath(os.path.join(SLATE, '..', '..'))
names = [('reference', None), ('S0_layout_only', 'S0 layout only'), ('S1_layout_stamps', 'S1 layout + stamps'), ('M_trace_coarse', 'M traced coarse'), ('L_trace_medium', 'L traced medium'), ('L_trace_fine', 'L traced fine')]
x0, y0, w = 330, 520, 300
cells = []
for name, label in names:
    path = os.path.join(PROC, 'reference', 'slate', 'colour.png') if name == 'reference' else os.path.join(SLATE, 'outputs', name, 'colour.png')
    im = cv2.imread(path)[y0:y0 + w, x0:x0 + w]
    im = cv2.resize(im, (w * 2, w * 2), interpolation=cv2.INTER_NEAREST)
    text = 'reference' if name == 'reference' else f"{label} ({os.path.getsize(os.path.join(SLATE, 'description', name + '.json')) / 1024:.1f} KB)"
    cv2.putText(im, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA); cv2.putText(im, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cells.append(im)
sheet = np.vstack([np.hstack(cells[:3]), np.hstack(cells[3:])])
cv2.imwrite(os.path.join(SLATE, 'guide_pictures', 'ladder_crops.png'), sheet)
print('ok', sheet.shape)
