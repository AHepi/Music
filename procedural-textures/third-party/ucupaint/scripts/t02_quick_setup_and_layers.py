"""Plain note: our own test. Makes a plane, turns on Ucupaint's layer setup (Principled material) and adds layers by Python:
a solid colour layer, a brick layer, a noise layer, a voronoi layer, each with blend modes; prints what came out."""
import sys, traceback
sys.path.insert(0, __import__('os').path.dirname(__file__))
import bpy
from ucu_common import *
obj, mat = fresh_scene()
def tryrun(label, fn):
    try:
        r = fn(); print('OK  ', label, r if r is not None else ''); return True
    except Exception as e:
        print('FAIL', label, repr(e)[:300]); traceback.print_exc(limit=3); return False
tryrun('quick setup', lambda: bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED'))
yp, grp = get_yp(mat)
print('yp found:', yp is not None, 'group node:', grp.name if grp else None, 'tree:', grp.node_tree.name if grp else None)
if yp:
    print('channels:', [(c.name, c.type) for c in yp.channels])
tryrun('layer COLOR', lambda: bpy.ops.wm.y_new_layer(name='Solid', type='COLOR', solid_color=(0.6,0.2,0.1,1.0), uv_map='UVMap'))
tryrun('layer BRICK', lambda: bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap'))
tryrun('layer NOISE', lambda: bpy.ops.wm.y_new_layer(name='Noisy', type='NOISE', uv_map='UVMap'))
tryrun('layer VORONOI', lambda: bpy.ops.wm.y_new_layer(name='Cells', type='VORONOI', uv_map='UVMap'))
yp, grp = get_yp(mat)
print('num layers', len(yp.layers))
for i,l in enumerate(yp.layers):
    print(i, l.name, l.type, 'channels:', [(c.enable, c.blend_type) for c in l.channels][:6])
nt = grp.node_tree
print('top-level material nodes:', [(n.name, n.type) for n in mat.node_tree.nodes])
print('ucupaint group inner nodes:', len(nt.nodes))
sub = [n.node_tree.name for n in nt.nodes if n.type=='GROUP' and n.node_tree]
print('inner groups:', sub)
print('bpy.data.node_groups:', [g.name for g in bpy.data.node_groups])
