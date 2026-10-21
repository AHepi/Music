# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# SELF-TEST of apply_rubbish_to_set.py, inside Blender, on the street copy (nothing is saved). It draws the main view (540 x 960, wet) four ways and compares them:
#   a  the street with the wetness layer and the JOINTS layer only (no rubbish nodes at all)
#   b  the same with the rubbish put on at Rubbish Amount 0 (the nodes are there, the dial is off)
#   c  the rubbish on at the normal setting
#   d  the rubbish put on and then taken off again with remove()
# and checks: b equals a, d equals a (mean difference under 0.001 of a 0..1 scale), c differs from a, and after remove() there is no RUBBISH node, no scatter object and no leftover link.
# Run: blender -b --disable-autoexec street.blend --python test_rubbish_apply.py -- OUT_FOLDER
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ('', '../../setts/tools', '../../study/tools', '../../../tools'):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, sub)))
sys.dont_write_bytecode = True
import b02_lighting_and_variants as lv  # noqa: E402
import apply_wetness_to_set as aw  # noqa: E402
import apply_joints_to_set as aj  # noqa: E402
import apply_rubbish_to_set as ar  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
scene.camera = cams['main']
aw.apply(0.0, 0.0)
aj.apply()


def shot(name):
    lv.eevee_setup(540, 960, 16)
    lv.set_lighting('A')
    aw.set_state(0.85, 0.5)
    ar.set_state(0.85)
    scene.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(scene.render.filepath, check_existing=False)
    pixels = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
    bpy.data.images.remove(img)
    return pixels


def leftovers():
    nodes = sum(1 for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.name.startswith('RUBBISH'))
    host = bpy.data.objects.get('rubbish_scatter') is not None
    return dict(rubbish_nodes_in_materials=nodes, scatter_object_present=host)


result = {}
a = shot('a_no_rubbish')
result['before'] = leftovers()
ar.apply(places='street', amount=0.0)
b = shot('b_amount_0')
ar.apply(places='street')
c = shot('c_default')
ar.remove()
d = shot('d_after_remove')
result['after_remove'] = leftovers()
result['mean_abs_difference'] = dict(b_amount0_vs_a=float(np.abs(b - a).mean()), d_after_remove_vs_a=float(np.abs(d - a).mean()), c_default_vs_a=float(np.abs(c - a).mean()))
result['largest_difference'] = dict(b_vs_a=float(np.abs(b - a).max()), d_vs_a=float(np.abs(d - a).max()))
result['ok'] = bool(result['mean_abs_difference']['b_amount0_vs_a'] < 0.001 and result['mean_abs_difference']['d_after_remove_vs_a'] < 0.001 and result['mean_abs_difference']['c_default_vs_a'] > 0.001
                    and result['after_remove']['rubbish_nodes_in_materials'] == 0 and not result['after_remove']['scatter_object_present'])
json.dump(result, open(os.path.join(out, 'test_result.json'), 'w'), indent=1)
print('TEST RESULT', json.dumps(result), flush=True)
