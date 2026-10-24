import sys
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import place_kit as pk
from place_kit import parts
trees = []
for ob in bpy.data.objects:
    if ob.get('place_owner') == 'cottages_south' and ob.type == 'MESH':
        V, T = parts.world_triangles(ob)
        trees.append((ob.name, BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], epsilon=0.0)))
yc = -10.5
for y in np.linspace(yc - 0.8, yc + 0.8, 17):
    for x in (-26.0,):
        o = Vector((x, y, 3.4885))
        for name, tr in trees:
            hit = tr.ray_cast(o, Vector((0, 0, 1)), 0.15)
            if hit[0] is not None:
                print('RAY', round(y, 2), name, round(hit[0].z - o.z, 4), tuple(round(v, 2) for v in hit[1]))
