"""sat_mask.py - card-side: JPG showing pixels with saturation above 0.70 (red) over a dimmed copy, with shares per image band. JOB = {"items": [{"png","out"}]}"""
import sys, os, json
import numpy as np
import bpy
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'measure_ground.py')).read().split("res = {}")[0])
def down(a, f):
    h, w = a.shape[:2]; hh, ww = (h // f) * f, (w // f) * f
    return a[:hh, :ww].reshape(hh // f, f, ww // f, f, *a.shape[2:]).mean(axis=(1, 3))
def save_jpg(arr, path, q=84):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_jpg', w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([arr[::-1], np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(rgba.ravel())
    bpy.context.scene.render.image_settings.file_format = 'JPEG'; bpy.context.scene.render.image_settings.quality = q
    img.file_format = 'JPEG'; img.filepath_raw = path; img.save(); bpy.data.images.remove(img)
for it in job['items']:
    a = load_rgb(it['png']); sat = sat_of(a); H, W = sat.shape
    m = sat > 0.70
    mask = np.ones((H, W), bool); mask[:int(0.55 * H), :int(0.40 * W)] = False
    print('SATMASK', it['png'].split('/')[-1], 'share outside maple', round(float((m & mask).mean() / mask.mean()), 4), flush=True)
    for name, (x0, y0, x1, y1) in {'lower_right_lawn': (1300, 1000, 2400, 1600), 'left_lower': (0, 1000, 1300, 1600), 'mid_pond_bank': (700, 700, 1700, 1100), 'roof': (500, 250, 1700, 600), 'right_upper': (1700, 0, 2400, 900)}.items():
        sub = m[y0:y1, x0:x1]
        print('   ', name, round(float(sub.mean()), 4), 'pixels', int(sub.sum()), flush=True)
    img = a * 0.35
    img[m] = np.array([1.0, 0.0, 0.8])
    save_jpg(np.clip(down(img, 3), 0, 1), it['out'])
print('SAT_DONE')
