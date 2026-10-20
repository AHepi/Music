# What this does (plain words): draws the outlines of the found puddles (cyan) and stones (green) on top of the reference colour picture so I can judge whether
# the finder is right. Writes /tmp/mudscratch/overlay_<name>.png (whole picture at 1254) and a zoomed crop. Analysis only.
import os, pickle, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
name = sys.argv[1] if len(sys.argv) > 1 else 'mud'
d = pickle.load(open(f'/tmp/mudscratch/elements_{name}.pkl', 'rb'))
img = cv2.imread(f'{PROC}/reference/{name}/colour.png')
h, w = img.shape[:2]
out = img.copy()
for p in d['puddles']:
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            cv2.polylines(out, [(np.asarray(p['p']) + [ox, oy]).astype(np.int32)], True, (255, 255, 0), 1)
for s in d['stones']:
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            cv2.polylines(out, [(np.asarray(s['outline']) + [ox, oy]).astype(np.int32)], True, (0, 255, 0), 1)
cv2.imwrite(f'/tmp/mudscratch/overlay_{name}.png', out)
cv2.imwrite(f'/tmp/mudscratch/overlay_{name}_crop.png', cv2.resize(out[900:1254, 250:700], None, fx=2.5, fy=2.5, interpolation=cv2.INTER_NEAREST))
