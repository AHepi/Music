import sys, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from place_kit import parts
parts.refresh_ground()
scene = bpy.context.scene
gz = parts.ground_height_at
B = {'A': (-40.05, 7.6, -26.45, 12.4, 5.3), 'B': (-9.2, 7.2, -2.8, 11.8, 6.5), 'C': (-29.7, -12.8, -22.3, -8.2, 4.8), 'D': (2.15, -10.2, 5.85, -5.8, 4.1), 'stable': (19.1, 36.0, 28.9, 42.0, 5.0)}
def corners(k):
    x0, y0, x1, y1, h = B[k]
    pts = []
    for x in (x0, x1):
        for y in (y0, y1):
            g = gz(x, y)
            pts += [Vector((x, y, g)), Vector((x, y, g + h))]
    return pts
def frame(camobj, pts):
    res = []
    for p in pts:
        co = world_to_camera_view(scene, camobj, p)
        res.append((round(co.x, 3), round(co.y, 3), round(co.z, 1)))
    return res
def inside(res, margin=0.02):
    return all(margin <= u <= 1 - margin and margin <= v <= 1 - margin and d > 0 for u, v, d in res)
out = {}
cam = bpy.data.objects['View wide']
scene.camera = cam
items = {k: corners(k) for k in B}
items['well'] = [Vector((-17.5, 6.0, gz(-17.5, 6.0) + z)) for z in (0.0, 1.0, 2.2)]
items['junction'] = [Vector((20, 2, gz(20, 2)))]
road = []
high = json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/plan/place-settings.json'))['roads'][0]['polyline']
import math
# 100 m of the road: sample along the polyline between x=-45 and x=52
for x in np.linspace(-45, 52, 12):
    # find y on polyline
    for a, b in zip(high[:-1], high[1:]):
        if a[0] <= x <= b[0]:
            y = a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]); break
    road.append(Vector((x, y, gz(x, y))))
items['road'] = road
rep = {}
for k, pts in items.items():
    r = frame(cam, pts)
    rep[k] = {'inside': inside(r), 'uv': r[:4]}
print('WIDE', json.dumps({k: (v['inside'], v['uv'][:3]) for k, v in rep.items()}))
# length of road inside
inroad = [frame(cam, [p])[0] for p in road]
print('road points inside', sum(1 for u, v, d in inroad if 0 <= u <= 1 and 0 <= v <= 1), 'of', len(road))
for name in ('View road_eye', 'View stable_close', 'View cottage_close'):
    c = bpy.data.objects[name]; scene.camera = c
    r = {}
    for k in ('A', 'B', 'C', 'D', 'stable', 'well'):
        pts = items[k]
        rr = frame(c, pts)
        r[k] = (inside(rr, 0.0), [(u, v) for u, v, d in rr[:2]])
    print(name, json.dumps(r))
