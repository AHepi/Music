"""ssim_map.py - card-side: per-pixel blurred-luminance SSIM maps (12 px blur) of a picture against the previous final and against the integrated final,
and a JPG heat map of where THIS picture is worse than the integrated final (red) or better (green). JOB = {"items": [{"name", "png", "base", "integrated", "out_dir"}]}"""
import sys, os, json
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'measure_ground.py')).read().split("res = {}")[0].replace("job = json.load(open(sys.argv[sys.argv.index('--') + 1]))", "job = json.load(open(sys.argv[sys.argv.index('--') + 1]))"))
def save_jpg(arr, path, q=84):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_jpg', w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([arr[::-1], np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(rgba.ravel())
    bpy.context.scene.render.image_settings.file_format = 'JPEG'; bpy.context.scene.render.image_settings.quality = q
    img.file_format = 'JPEG'; img.filepath_raw = path; img.save(); bpy.data.images.remove(img)
def down(a, f):
    h, w = a.shape[:2]; hh, ww = (h // f) * f, (w // f) * f
    return a[:hh, :ww].reshape(hh // f, f, ww // f, f, *a.shape[2:]).mean(axis=(1, 3))
out = {}
for it in job['items']:
    a = load_rgb(it['png']); b = load_rgb(it['base']); c = load_rgb(it['integrated'])
    la, lb, lc = lum_of(a), lum_of(b), lum_of(c)
    s_ab = ssim_blur(la, lb); s_cb = ssim_blur(lc, lb)
    d = s_ab - s_cb
    H, W = d.shape
    print('SSIM_MAP', it['name'], 'mine vs base', round(float(s_ab.mean()), 4), 'integrated vs base', round(float(s_cb.mean()), 4), flush=True)
    # grid of 6 x 4 cells: mean of (mine - integrated) * area share  => contribution to the total
    gy, gx = 4, 6
    rows = []
    for j in range(gy):
        r = []
        for i in range(gx):
            blk = d[j * H // gy:(j + 1) * H // gy, i * W // gx:(i + 1) * W // gx]
            r.append(round(float(blk.mean()), 3))
        rows.append(r)
    print('SSIM_GRID', it['name'], 'mine-minus-integrated per cell (rows top..bottom):', rows, flush=True)
    rows = []
    for j in range(gy):
        r = []
        for i in range(gx):
            blk = s_ab[j * H // gy:(j + 1) * H // gy, i * W // gx:(i + 1) * W // gx]
            r.append(round(float(blk.mean()), 2))
        rows.append(r)
    print('SSIM_GRID_BASE', it['name'], 'mine vs base per cell:', rows, flush=True)
    f = 4
    sm = down(np.clip(0.5 - d * 2.0, 0, 1), f)               # 0.5 = same; <0.5 worse? (d negative -> brighter red)
    img = np.zeros(sm.shape + (3,), np.float32)
    dd = down(d, f)
    img[..., 0] = np.clip(-dd * 4, 0, 1); img[..., 1] = np.clip(dd * 4, 0, 1)
    base_small = down(la, f)
    img = img * 0.8 + base_small[..., None] * 0.35
    os.makedirs(it['out_dir'], exist_ok=True)
    save_jpg(np.clip(img, 0, 1), os.path.join(it['out_dir'], it['name'] + '_ssimmap.jpg'))
print('SSIM_DONE')
