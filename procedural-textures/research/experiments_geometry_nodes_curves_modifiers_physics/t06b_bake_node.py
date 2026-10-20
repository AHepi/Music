# What this does: tests the Bake node (Geometry Nodes, 4.1+) in headless Blender 5.2.2: put a Bake node after an expensive-looking step, bake it from Python,
# and check that afterwards the result is frozen (changing the setting in front of the Bake node no longer changes the result) until the bake is deleted.
# Also records the time to compute vs to read back, and which Python calls are needed (the .blend must be saved first).
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt
import t06_relax_repeat_zone as t6
OUT = os.path.join(HERE, 'out', 't06_relax'); os.makedirs(OUT, exist_ok=True)
gt.new_scene(64)
relax = t6.relax_group()
tree, g = gt.make_geometry_group('bake test', [('Geometry', 'NodeSocketGeometry', None), ('Iterations', 'NodeSocketInt', 40)])
node, socket = t6.starting_points_node(g, 'c', 220, 3)
g.group('relax', relax, {'Points': (node, socket), 'Iterations': ('in', 'Iterations')})
g.node('GeometryNodeBake', 'bake')
g.nodes['bake'].bake_items.new('GEOMETRY', 'Geometry')
g.link('relax', 'Points', 'bake', 'Geometry')
g.node('GeometryNodePointsToVertices', 'to vertices', {'Points': ('bake', 'Geometry')})
g.link('to vertices', 'Mesh', 'out', 'Geometry')
obj, mod = gt.add_geometry_object('bake test', tree)
res = {}
def iterations(n):
    gt.modifier_inputs(bpy.data.objects['bake test'].modifiers['recipe'], Iterations=n)   # (re-fetch: Python handles go stale after saving the file)
t = time.time(); p40 = gt.evaluated_vertices(obj)[:, :2]; res['evaluate_before_bake_s'] = round(time.time() - t, 3)
res['bakes_listed_on_modifier'] = [(b.bake_id, b.bake_mode if hasattr(b, 'bake_mode') else None, b.bake_target if hasattr(b, 'bake_target') else None) for b in mod.bakes]
def sorted_x():
    return np.sort(gt.evaluated_vertices(bpy.data.objects['bake test'])[:, 0])
def changed(a, b):
    return float(np.abs(a - b).max())
x40 = sorted_x()
iterations(2)
res['control_before_baking:_changing_iterations_40_to_2_changes_the_points_by'] = changed(sorted_x(), x40)
iterations(40)
path = os.path.join(OUT, 'bake_test.blend')
bpy.ops.wm.save_as_mainfile(filepath=path)          # a Bake needs a saved file
obj = bpy.data.objects['bake test']; mod = obj.modifiers['recipe']
for other in bpy.context.view_layer.objects: other.select_set(False)
obj.select_set(True); bpy.context.view_layer.objects.active = obj
try:
    r = bpy.ops.object.geometry_node_bake_single(session_uid=obj.session_uid, modifier_name=mod.name, bake_id=mod.bakes[0].bake_id)
    res['bake_operator_result'] = list(r)
except Exception as e:
    res['bake_operator_error'] = repr(e)
obj = bpy.data.objects['bake test']
res['after_bake_modifier_bake_target_and_mode'] = [(str(b.bake_target), str(b.bake_mode)) for b in obj.modifiers['recipe'].bakes]
x_baked = sorted_x()
iterations(2)
t = time.time(); x2 = sorted_x(); res['evaluate_after_bake_s'] = round(time.time() - t, 3)
res['FROZEN_after_bake:_changing_iterations_to_2_changes_the_points_by'] = changed(x2, x_baked)
try:
    obj = bpy.data.objects['bake test']
    r = bpy.ops.object.geometry_node_bake_delete_single(session_uid=obj.session_uid, modifier_name=obj.modifiers['recipe'].name, bake_id=obj.modifiers['recipe'].bakes[0].bake_id)
    res['delete_bake_result'] = list(r)
    x_after_delete = sorted_x()
    res['after_deleting_the_bake_the_points_change_again_by'] = changed(x_after_delete, x_baked)
except Exception as e:
    res['delete_error'] = repr(e)
res['modifier_execution_time_seconds_(modifier.execution_time)'] = bpy.data.objects['bake test'].modifiers['recipe'].execution_time
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(OUT, 'bake_node_results.json'), 'w'), indent=1)
