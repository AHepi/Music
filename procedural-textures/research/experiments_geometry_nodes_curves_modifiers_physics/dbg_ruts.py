import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt, recipe_curve_ruts as rr
gt.new_scene(64)
p = {**rr.DEFAULTS, 'grid': 128}
tree = rr.build_mud_group(p)
obj, mod = gt.add_geometry_object('mud', tree)
out = [n for n in tree.nodes if n.bl_idname=='NodeGroupOutput'][0]
for stage, sock in [('ground','Geometry'),('ruts and copies','Geometry'),('stone points all','Geometry'),('stones on ground','Geometry'),('stones real','Geometry'),('join','Geometry')]:
    for l in list(out.inputs[0].links): tree.links.remove(l)
    tree.links.new(tree.nodes[stage].outputs[sock], out.inputs[0])
    try:
        pts = gt.evaluated_vertices(obj)
        print(f'{stage:22s} verts {len(pts):7d} z {pts[:,2].min():.4f}..{pts[:,2].max():.4f}  x {pts[:,0].min():.3f}..{pts[:,0].max():.3f}')
    except Exception as e:
        print(stage, 'ERR', e)
