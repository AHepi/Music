# Checker's own comparison pictures (inside Blender, numpy only). First phase: composites from the finals. Second phase: one small render of the bridge cramps.
import bpy, json, os, sys, math
import numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'
OUT = G + 'character/checker3/out/pics/'
os.makedirs(OUT, exist_ok=True)
NEW = {'hero': G + 'character/fix/final/out/finals/final_hero.png', 'veranda': G + 'character/fix/final/out/finals/final_veranda.png'}
FIRST = {'hero': G + 'character/final/out/finals/final_hero.png', 'veranda': G + 'character/final/out/finals/final_veranda.png'}
OLD = {'hero': G + 'fix/out/final/real_hero.png', 'veranda': G + 'fix/out/final/real_veranda.png'}
def load(path):
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()
def save_jpg(arr, path, q=78):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('t', w, h, alpha=False); img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.concatenate([np.clip(arr[::-1], 0, 1), np.ones((h, w, 1), np.float32)], axis=2).ravel())
    bpy.context.scene.render.image_settings.file_format = 'JPEG'; bpy.context.scene.render.image_settings.quality = q
    img.file_format = 'JPEG'; img.filepath_raw = path; img.save(); bpy.data.images.remove(img)
def pair(a, b, box):
    x0, y0, x1, y1 = box
    sep = np.ones((y1 - y0, 8, 3), np.float32)
    return np.concatenate([a[y0:y1, x0:x1], sep, b[y0:y1, x0:x1]], axis=1)
def stack(rows):
    W = max(r.shape[1] for r in rows)
    out = []
    for r in rows:
        if r.shape[1] < W: r = np.concatenate([r, np.ones((r.shape[0], W - r.shape[1], 3), np.float32) * 0.1], axis=1)
        out.append(r); out.append(np.ones((8, W, 3), np.float32))
    return np.concatenate(out[:-1], axis=0)
hN, hF, vN, vF = load(NEW['hero']), load(FIRST['hero']), load(NEW['veranda']), load(FIRST['veranda'])
# 1 bridge: first (left) and fix round (right)
save_jpg(stack([pair(hF, hN, (0, 1100, 800, 1600)), pair(hF, hN, (700, 1000, 1500, 1450))]), OUT + 'pic_bridge.jpg')
# 2 pond and moss cushions
save_jpg(stack([pair(hF, hN, (250, 850, 1100, 1250)), pair(vF, vN, (1150, 950, 1800, 1350))]), OUT + 'pic_pond_moss.jpg')
# 3 lawn and worn path
save_jpg(stack([pair(hF, hN, (1500, 1250, 2400, 1600)), pair(vF, vN, (0, 1000, 800, 1600))]), OUT + 'pic_lawn_path.jpg')
# 4 roof and wall cracks and veranda maple (new only for the maple, first next to it)
save_jpg(stack([pair(hF, hN, (700, 300, 1450, 620)), pair(vF, vN, (1250, 80, 1850, 600))]), OUT + 'pic_roof_maple.jpg')
# 5 deck
save_jpg(pair(vF, vN, (1500, 800, 2100, 1400)), OUT + 'pic_deck.jpg')
print('COMPOSITES DONE', flush=True)
# phase 2: the cramps
bpy.ops.wm.open_mainfile(filepath=G + 'character/fix/final/garden_character_fix.blend')
from mathutils import Vector
sc = bpy.context.scene
cam = bpy.data.objects.new('chk_cam', bpy.data.cameras.new('chk_cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 55
tg = Vector((-3.845, -0.178, 0.226))
for name, pos in (('cramp_A', Vector((-3.845, -0.52, 0.34))), ):
    cam.location = pos
    cam.rotation_euler = (tg - pos).to_track_quat('-Z', 'Y').to_euler()
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.resolution_x = 1000; sc.render.resolution_y = 625; sc.render.resolution_percentage = 100
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'; prefs.get_devices()
        for d in prefs.devices: d.use = (d.type == 'OPTIX')
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('gpu setup', e)
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = OUT + name + '.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name, flush=True)
print('PICS4 DONE')
