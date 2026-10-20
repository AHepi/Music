import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt, recipe_brick_layout as rb
scene = gt.new_scene(64)
p = {**rb.DEFAULTS, 'subdiv': 1}
tree = rb.build_wall_group(p)
obj, mod = gt.add_geometry_object('wall', tree)
mat = gt.height_material(-0.014, 0.028)
obj.data.materials.append(mat)
bpy.context.view_layer.update()
ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
me = ev.to_mesh()
print('evaluated materials', [m.name if m else None for m in me.materials], 'object slots', [s.name for s in obj.material_slots])
ev.to_mesh_clear()
print('obj in scene', obj.name in scene.collection.objects, 'scene is context', scene == bpy.context.scene, 'camera', scene.camera)
print('hide_render', obj.hide_render, 'mod show_render', mod.show_render)
