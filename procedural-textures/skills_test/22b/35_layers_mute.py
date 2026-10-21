# Trial 22b: Price's "mute each layer, does each add something?" check for M.add_wear, in Cycles (the only engine where all of it shows), small pictures.
# Run: blender -b --disable-autoexec street_copy/door_addwear.blend --python 35_layers_mute.py -- OUTDIR
import json
import os
import sys

import bpy
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/street_wet/tools')
import apply_wetness_to_set as aw  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
aw.cycles_settings(sc, 360, 640, 64)
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type != 'CPU'
sc.cycles.device = 'GPU'
mat = bpy.data.materials['door_navy_wear']
nt = mat.node_tree
ew = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree.name == 'BX Edge Wear')
gg = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree.name == 'BX Grunge')
full = {'wear': ew.inputs['Wear Amount'].default_value, 'cav': ew.inputs['Dirt Amount'].default_value, 'grunge': gg.inputs['Coverage'].default_value}
configs = {'all': {}, 'no_edge_wear': {'wear': 0.0}, 'no_cavity_dirt': {'cav': 0.0}, 'no_grunge_spots': {'grunge': 0.0}, 'nothing': {'wear': 0.0, 'cav': 0.0, 'grunge': 0.0}}
imgs = {}
for name, ch in configs.items():
    ew.inputs['Wear Amount'].default_value = ch.get('wear', full['wear'])
    ew.inputs['Dirt Amount'].default_value = ch.get('cav', full['cav'])
    gg.inputs['Coverage'].default_value = ch.get('grunge', full['grunge'])
    fn = os.path.join(out, f'layers_{name}.png')
    sc.render.filepath = fn
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fn, check_existing=False)
    imgs[name] = np.array(im.pixels[:]).reshape(640, 360, 4)[..., :3]
    bpy.data.images.remove(im)
leaf = (slice(int(640 * 0.22), int(640 * 0.95)), slice(int(360 * 0.22), int(360 * 0.78)))
res = {}
for name in configs:
    res[name] = {'mean_abs_diff_vs_all': round(float(np.abs(imgs[name][leaf] - imgs['all'][leaf]).mean() * 255), 3),
                 'mean_abs_diff_vs_nothing': round(float(np.abs(imgs[name][leaf] - imgs['nothing'][leaf]).mean() * 255), 3)}
print('LAYERS', json.dumps(res))
json.dump(res, open(os.path.join(out, 'layers.json'), 'w'), indent=1)
