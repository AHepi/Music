# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A self-test of apply_joints_to_set.py (the script that puts the JOINTS layer on the street copy's road), run inside Blender on the street copy:
#   a  the road as it is (wetness layer only)                      -> a.png
#   b  aj.apply()                  the JOINTS layer on              -> b.png   (must DIFFER from a)
#   c  aj.set_dials(strength=0)    the layer's master dial at 0     -> c.png   (must equal a)
#   d  aj.remove()                 the layer taken off again        -> d.png   (must equal a)
#   e  aj.apply(shadow=0.4) + aj.apply_real_grooves()  the layer with the optional shade and real grooves -> e.png (must differ from a and b)
#   f  aj.remove()                 everything off again             -> f.png   (must equal a)
# Small pictures (270 x 480, 8 samples) of the main camera, wet 0.85 / puddles 0.5, dusk lamps. Writes pictures and test_result.json into the folder given after "--".
# Run: blender -b --disable-autoexec street.blend --python test_apply_script.py -- OUT_FOLDER
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools'))
sys.path.insert(0, HERE)
sys.path.insert(0, STUDY)
sys.dont_write_bytecode = True
import apply_joints_to_set as aj  # noqa: E402
import apply_wetness_to_set as aw  # noqa: E402
import b02_lighting_and_variants as lv  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
aw.apply(wetness=0.85, puddles=0.5)
scene.camera = aw.cameras()['main']
lv.eevee_setup(270, 480, 8)
lv.set_lighting('A')


def draw(name):
    scene.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)


draw('a')
aj.apply()
draw('b')
aj.set_dials(strength=0.0)
draw('c')
aj.remove()
draw('d')
aj.apply(shadow=0.4)
aj.apply_real_grooves()
draw('e')
aj.remove()
draw('f')
nodes_left = [n.name for n in bpy.data.materials['street_setts'].node_tree.nodes if n.name.startswith('JOINTS') or n.type == 'MIX_SHADER']
modifiers_left = [m.name for m in bpy.data.objects['street_setts'].modifiers]
json.dump(dict(nodes_left=nodes_left, modifiers_left=modifiers_left), open(os.path.join(out, 'test_result.json'), 'w'))
print('TEST DONE', flush=True)
