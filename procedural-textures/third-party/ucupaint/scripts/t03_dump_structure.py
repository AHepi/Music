"""Plain note: our own test. Builds a small layer stack with Ucupaint and writes out (as text) every node and link it generated,
so we can see what Ucupaint really makes (the main group, the per-layer groups, their nodes and settings)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from ucu_common import *
obj, mat = fresh_scene()
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Cells', type='VORONOI', uv_map='UVMap', add_mask=True, mask_type='IMAGE', mask_color='WHITE', mask_uv_name='UVMap')
yp, grp = get_yp(mat)
def dump(tree, indent=0, seen=None):
    seen = seen if seen is not None else set()
    pad = '  '*indent
    print(f'{pad}TREE {tree.name!r} nodes={len(tree.nodes)} links={len(tree.links)}')
    for n in tree.nodes:
        extra = ''
        if n.type == 'GROUP' and n.node_tree: extra = ' -> ' + n.node_tree.name
        if n.type in ('TEX_BRICK','TEX_NOISE','TEX_VORONOI','TEX_IMAGE'): extra += ' settings:' + str({k: getattr(n,k) for k in ('noise_dimensions','voronoi_dimensions','feature') if hasattr(n,k)})
        print(f'{pad}  {n.name!r} [{n.bl_idname}]{extra}')
    for n in tree.nodes:
        if n.type=='GROUP' and n.node_tree and n.node_tree.name not in seen:
            seen.add(n.node_tree.name); dump(n.node_tree, indent+1, seen)
dump(grp.node_tree)
print('MASKS of top layer:', [(m.name, m.type) for m in yp.layers[0].masks])
print('layer0 props:', [k for k in dir(yp.layers[0]) if not k.startswith('_')][:80])
