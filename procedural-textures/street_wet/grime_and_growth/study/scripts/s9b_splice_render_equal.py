# What this does (plain words): STUDY ONLY. Draws the street twice at 135 x 240 dots, 4 samples (EEVEE): as it is, and with the do-nothing group spliced into every material (s9_splice_test.py's
# method, run here in the same Blender session). Counts the dots that differ. It saves two small PNGs into the out folder and nothing else.
import os, sys, time
import bpy
import numpy as np
out_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_folder, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 135, 240, 100
scene.eevee.taa_render_samples = 4
scene.render.image_settings.file_format = 'PNG'


def draw(name):
    path = os.path.join(out_folder, name + '.png')
    scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path, check_existing=False)
    arr = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
    bpy.data.images.remove(img)
    return arr, round(time.time() - t, 1)


a, ta = draw('before')
exec(open(os.path.join(HERE, 's9_splice_test.py')).read().replace("args = sys.argv[sys.argv.index('--') + 1:]\nout_folder = args[0]\nos.makedirs(out_folder, exist_ok=True)\n", ''))
b, tb = draw('after')
d = np.abs(a - b)
print('RENDER_EQUAL', 'before s', ta, 'after s', tb, 'max diff', float(d.max()), 'mean diff', float(d.mean()), 'dots differing by more than 1/255:', int((d.max(axis=1) > 1 / 255).sum()), 'of', len(d))
