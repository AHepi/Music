"""crop_job.py - runs on the card inside Blender: cuts crops out of full-size PNGs that stay on the store and writes small JPGs.
   blender -b -P crop_job.py -- JOB.json     JOB = {"items": [{"png": "...", "out": ".../name.jpg", "box": [x0,y0,x1,y1] (pixels, top-left origin) | null, "width": 1200 | null, "quality": 86}]}"""
import sys, os, json
import numpy as np
import bpy
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
cache = {}
def load_rgb(path):
    if path in cache:
        return cache[path]
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    a = a.reshape(h, w, 4)[::-1, :, :3].copy()
    cache[path] = a
    return a
def downscale(a, w):
    h0, w0 = a.shape[:2]
    f = max(1, int(w0 // w))
    if f > 1:
        hh, ww = (h0 // f) * f, (w0 // f) * f
        a = a[:hh, :ww].reshape(hh // f, f, ww // f, f, 3).mean(axis=(1, 3))
    h1, w1 = a.shape[:2]
    if w1 != w:
        nh = int(round(h1 * w / w1))
        xs = np.linspace(0, w1 - 1, w); ys = np.linspace(0, h1 - 1, nh)
        x0 = np.floor(xs).astype(int); x1 = np.minimum(x0 + 1, w1 - 1); fx = (xs - x0)[None, :, None]
        y0 = np.floor(ys).astype(int); y1 = np.minimum(y0 + 1, h1 - 1); fy = (ys - y0)[:, None, None]
        top = a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx
        bot = a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx
        a = top * (1 - fy) + bot * fy
    return a.astype(np.float32)
def save_jpg(arr, path, q):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_jpg', w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([arr[::-1], np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(rgba.ravel())
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = q
    img.file_format = 'JPEG'
    img.filepath_raw = path
    img.save()
    bpy.data.images.remove(img)
for it in job['items']:
    if not os.path.exists(it['png']):
        print('missing', it['png']); continue
    a = load_rgb(it['png'])
    if it.get('box'):
        x0, y0, x1, y1 = it['box']
        a = a[y0:y1, x0:x1]
    if it.get('width'):
        a = downscale(a, it['width'])
    os.makedirs(os.path.dirname(it['out']), exist_ok=True)
    save_jpg(a, it['out'], it.get('quality', 86))
    print('CROP_DONE', it['out'], a.shape)
