import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt, recipe_brick_layout as rb
gt.new_scene(128)
p = {**rb.DEFAULTS, 'subdiv': 1}
tree = rb.build_wall_group(p)
obj, mod = gt.add_geometry_object('wall', tree)
out = [n for n in tree.nodes if n.bl_idname=='NodeGroupOutput'][0]
for stage, sock in [('realize','Geometry'),('bevel','Mesh'),('subdivide','Mesh'),('displace outline','Geometry'),('displace top','Geometry'),('lower bricks','Geometry'),('store piece colour','Geometry')]:
    for l in list(out.inputs[0].links): tree.links.remove(l)
    tree.links.new(tree.nodes[stage].outputs[sock], out.inputs[0])
    pts = gt.evaluated_vertices(obj)
    print(f'{stage:20s} verts {len(pts):7d} z {pts[:,2].min():.4f}..{pts[:,2].max():.4f}  x {pts[:,0].min():.3f}..{pts[:,0].max():.3f}')
