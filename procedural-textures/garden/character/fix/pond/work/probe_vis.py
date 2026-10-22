# local probe: where is the pond water visible in the hero and veranda cameras? (reads the starting scene only, never saves)
import bpy, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
want = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.hide_render: continue
    n = ob.name
    if n.startswith(('Rock', 'Pond edge stone', 'Astra / varied planks', 'Astra / Planked', 'Bridge', 'Astra / Courtyard receiving', 'Hall', 'Shore', 'Stone plinth', 'Veranda', 'Right wall', 'Back wall')):
        want.append(ob)
print('blockers', [o.name for o in want])
verts, polys = [], []
off = 0
for ob in want:
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    me.calc_loop_triangles()
    mw = ob.matrix_world
    for v in me.vertices:
        verts.append(mw @ v.co)
    for t in me.loop_triangles:
        polys.append(tuple(off + i for i in t.vertices))
    off += len(me.vertices)
    eo.to_mesh_clear()
bvh = BVHTree.FromPolygons(verts, polys)
out = {}
for camname, W, H in (('photo', 1200, 800), ('veranda', 1200, 800)):
    cam = bpy.data.objects[camname]
    sc.render.resolution_x, sc.render.resolution_y = W, H
    loc = cam.matrix_world.translation
    print(camname, 'loc', tuple(round(x, 2) for x in loc), 'lens', cam.data.lens, 'sensor', cam.data.sensor_width, cam.data.sensor_fit)
    pts = []
    for x in np.arange(-5.6, 0.2, 0.2):
        for y in np.arange(-1.2, 3.1, 0.2):
            p = Vector((x, y, -0.12))
            c = world_to_camera_view(sc, cam, p)
            if not (0 < c.x < 1 and 0 < c.y < 1 and c.z > 0): continue
            d = p - loc
            hit = bvh.ray_cast(loc, d.normalized(), d.length - 0.02)
            vis = hit[0] is None
            pts.append((round(float(x), 2), round(float(y), 2), round(c.x * W), round((1 - c.y) * H), bool(vis)))
    out[camname] = pts
    print(camname, 'points in frame', len(pts), 'visible', sum(1 for p in pts if p[4]))
json.dump(out, open(sys.argv[sys.argv.index('--') + 1], 'w'))
