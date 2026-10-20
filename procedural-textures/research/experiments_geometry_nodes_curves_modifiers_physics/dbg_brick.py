import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt, recipe_brick_layout as rb
gt.new_scene(128)
p = {**rb.DEFAULTS, 'subdiv': 1}
tree = rb.build_wall_group(p)
obj, mod = gt.add_geometry_object('wall', tree)
pts = gt.evaluated_vertices(obj)
print('verts', len(pts), 'bbox min', pts.min(0), 'max', pts.max(0))
bpy.context.view_layer.update()
ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
print('polys', len(ev.polygons), 'attrs', [(a.name, a.domain, a.data_type) for a in ev.attributes])
# warnings
for n in tree.nodes:
    pass
print('materials', [m.name for m in obj.data.materials])
inside = (pts[:,0]>=0)&(pts[:,0]<=1)&(pts[:,1]>=0)&(pts[:,1]<=1)
print('verts inside tile', inside.sum(), 'z range inside', pts[inside,2].min(), pts[inside,2].max())
import collections
print('z hist', np.histogram(pts[inside,2], bins=8))
ids = gt.evaluated_attribute(obj, 'piece_id')
hi = pts[:,2] > 0.04
lo = pts[:,2] < -0.03
print('high verts', hi.sum(), 'ids', np.unique(ids[hi]), 'xy range', pts[hi][:,:2].min(0), pts[hi][:,:2].max(0))
print('low verts', lo.sum(), 'ids', np.unique(ids[lo]), 'xy range', pts[lo][:,:2].min(0), pts[lo][:,:2].max(0))
w = gt.evaluated_attribute(obj, 'piece_w'); h = gt.evaluated_attribute(obj, 'piece_h')
for i in np.unique(ids[hi|lo])[:5]:
    sel = ids==i
    print('id', i, 'verts', sel.sum(), 'z', pts[sel,2].min(), pts[sel,2].max(), 'w', w[sel][0], 'h', h[sel][0], 'x', pts[sel,0].min(), pts[sel,0].max())
