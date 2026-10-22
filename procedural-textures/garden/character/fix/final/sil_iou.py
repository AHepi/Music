"""sil_iou.py - overlap of before/after silhouette PNGs (alpha above 0.5). blender -b --factory-startup --python sil_iou.py -- JOB.json
JOB.json = {"dir": "...", "groups": [...], "cameras": [...], "json": "/abs/out.json"}"""
import sys, json, os
import numpy as np, bpy
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
def load(p):
    img = bpy.data.images.load(p); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a); bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[..., 3] > 0.5
res = {}
for g in job['groups']:
    for c in job['cameras']:
        A = load(os.path.join(job['dir'], 'before_%s_%s.png' % (g, c))); B = load(os.path.join(job['dir'], 'after_%s_%s.png' % (g, c)))
        inter, uni = int((A & B).sum()), int((A | B).sum())
        res['%s_%s' % (g, c)] = dict(area_before=int(A.sum()), area_after=int(B.sum()), area_ratio=round(float(B.sum() / max(A.sum(), 1)), 3),
                                    iou=round(inter / max(uni, 1), 4), share_of_before_covered=round(inter / max(int(A.sum()), 1), 4))
        print('SIL', g, c, json.dumps(res['%s_%s' % (g, c)]), flush=True)
json.dump(res, open(job['json'], 'w'), indent=1)
