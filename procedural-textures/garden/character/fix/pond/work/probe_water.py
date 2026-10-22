import bpy, sys, math
import numpy as np
pw = bpy.data.objects['Pond water']
me = pw.data
print('water verts', len(me.vertices), 'polys', len(me.polygons), 'attrs', [(a.name, a.domain, a.data_type) for a in me.attributes])
co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); V = co.reshape(-1,3)
print('bbox', V.min(0), V.max(0), 'z unique', np.unique(np.round(V[:,2],3))[:5])
d = np.empty(len(me.vertices), np.float32)
me.attributes['depth'].data.foreach_get('value', d)
print('depth min/max', d.min(), d.max(), 'hist', np.histogram(d, bins=[0,0.02,0.05,0.1,0.15,0.2,0.25,0.3,0.4,0.5])[0])
# relation to ground / bed: sample bed
bed = bpy.data.objects['Life / pond bed']
print('bed verts', len(bed.data.vertices), bed.name, [a.name for a in bed.data.attributes])
bc = np.empty(len(bed.data.vertices)*3, np.float32); bed.data.vertices.foreach_get('co', bc); B = bc.reshape(-1,3)
print('bed z range', B[:,2].min(), B[:,2].max(), 'bbox', B.min(0), B.max(0))
# grid spacing
xs = np.unique(np.round(V[:,0],2)); print('unique x', len(xs), xs[:10])
# print depth along a few lines
from mathutils.bvhtree import BVHTree
g = bpy.data.objects['Astra / Courtyard receiving ground']
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(g, dg)
def gz(x,y):
    r = bvh.ray_cast((x,y,6.0),(0,0,-1))
    return r[0].z if r[0] else None
# nearest-vertex depth vs ground z at those points
for (x,y) in [(-4.5,0.5),(-4.0,-0.5),(-3.0,-0.9),(-2.0,-0.5),(-3.0,2.0),(-3.0,2.8),(-1.0,2.0),(-2.5,0.0),(-1.5,0.2),(-4.8,2.2),(-5.2,0.5)]:
    i = np.argmin((V[:,0]-x)**2+(V[:,1]-y)**2)
    print((x,y), 'nearest vert', V[i].round(2), 'depth', round(float(d[i]),3), 'ground z', gz(x,y))
