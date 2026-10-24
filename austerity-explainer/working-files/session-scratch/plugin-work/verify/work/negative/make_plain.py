"""Negative test: from the FINISHED scene, give the near wall panels and the gate boards a plain flat-colour material (what a lazy builder would leave), then save."""
import sys, bpy
out = sys.argv[sys.argv.index('--') + 1]
mat = bpy.data.materials.new('plain red'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.5, 0.2, 0.15, 1)
n = 0
for o in bpy.data.objects:
    if o.name.startswith(('Wall near', 'Gate near board')):
        o.data.materials.clear(); o.data.materials.append(mat); n += 1
print('PLAINED', n)
bpy.ops.wm.save_as_mainfile(filepath=out)
