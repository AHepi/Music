"""iou.py - inside Blender: overlap (intersection over union) of two silhouette PNGs (alpha > 0.5): usage: blender -b --python iou.py -- OUT.json A.png B.png"""
import sys, json
import numpy as np, bpy
a_, b_ = sys.argv[sys.argv.index('--') + 2: sys.argv.index('--') + 4]
out = sys.argv[sys.argv.index('--') + 1]
def load(p):
    img = bpy.data.images.load(p); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a); bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[..., 3] > 0.5
A, B = load(a_), load(b_)
res = dict(area_a=int(A.sum()), area_b=int(B.sum()), iou=round(float((A & B).sum() / max((A | B).sum(), 1)), 4), overlap_of_a=round(float((A & B).sum() / max(A.sum(), 1)), 4))
json.dump(res, open(out, 'w')); print('IOU', json.dumps(res))
