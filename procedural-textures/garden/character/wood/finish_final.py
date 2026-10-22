"""finish_final.py - run on the card (inside Blender) after the final proofs: metrics JSON + small JPG previews + 100 percent crops. Pictures stay on the store, only these small files are downloaded.
   blender -b --python finish_final.py -- OUTDIR"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import bpy
import final_metrics as fm

out = sys.argv[sys.argv.index('--') + 1]
fm.BOXES['deck_ver'] = (1450, 700, 2350, 1500)
fm.BOXES.pop('deck_hero', None)

def save_jpg(arr, path, q=86):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp', w, h, alpha=False)
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

crops = {'final_hero': [('bridge', (0, 1050, 1560, 1580)), ('deck', (150, 740, 1100, 960))],
         'final_veranda': [('deck', (1100, 300, 2400, 1560)), ('bridge', (0, 250, 700, 700))]}
for name in ('final_hero', 'final_veranda'):
    p = os.path.join(out, name + '.png')
    if not os.path.exists(p):
        print('missing', p)
        continue
    a = fm.load_rgb(p)
    m = fm.metrics(a)
    json.dump(m, open(os.path.join(out, name + '_metrics.json'), 'w'), indent=1)
    print('FINAL_METRICS', name, json.dumps(m))
    h, w = a.shape[:2]
    small = a.reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))
    save_jpg(small, os.path.join(out, name + '_1200.jpg'), 86)
    for cn, (x0, y0, x1, y1) in crops[name]:
        save_jpg(a[y0:y1, x0:x1], os.path.join(out, '%s_crop_%s.jpg' % (name, cn)), 84)
