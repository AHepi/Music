"""mask_stats.py - runs inside Blender (card or local): coverage numbers of the debug mask pictures (moss red, mould green, walking-line wear blue,
transparent where there is no bridge plank). Usage: blender -b --python mask_stats.py -- OUTJSON IN1.png [IN2.png ...]"""
import sys, json, os
import numpy as np
import bpy
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
res = {}
for path in args[1:]:
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1]
    bpy.data.images.remove(img)
    vis = a[..., 3] > 0.5
    n = max(int(vis.sum()), 1)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    moss = (R > 0.6) & vis
    mould = (G > 0.55) & vis
    walk = (B > 0.5) & vis
    off = vis & ~walk
    res[os.path.basename(path)] = dict(visible_px=int(vis.sum()), moss=round(moss.sum() / n, 4), mould=round(mould.sum() / n, 4), moss_or_mould=round((moss | mould).sum() / n, 4),
                                      walk_share_of_plank=round(walk.sum() / n, 4), moss_on_walk=round((moss & walk).sum() / max(walk.sum(), 1), 4),
                                      moss_off_walk=round((moss & off).sum() / max(off.sum(), 1), 4),
                                      both_on_walk=round(((moss | mould) & walk).sum() / max(walk.sum(), 1), 4), both_off_walk=round(((moss | mould) & off).sum() / max(off.sum(), 1), 4))
    # a small picture to look at: moss olive, mould dark, plank mid grey
    vis3 = np.where(vis[..., None], np.array([0.62, 0.55, 0.48]), np.array([0.12, 0.16, 0.2]))
    vis3 = np.where(moss[..., None], np.array([0.35, 0.5, 0.1]), vis3)
    vis3 = np.where((mould & ~moss)[..., None], np.array([0.1, 0.14, 0.12]), vis3)
    vis3 = np.where((walk & vis & ~moss & ~mould)[..., None], np.array([0.78, 0.7, 0.58]), vis3)
    im = bpy.data.images.new('_mv', w, h, alpha=False)
    rgba = np.concatenate([vis3, np.ones((h, w, 1))], -1)[::-1].astype(np.float32)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = path.replace('.png', '_view.jpg')
    im.file_format = 'JPEG'
    im.save()
    bpy.data.images.remove(im)
json.dump(res, open(out, 'w'), indent=1)
print('MASK_STATS', json.dumps(res))
