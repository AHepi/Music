import sys, json, math
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from place_kit import parts
parts.refresh_ground()
scene = bpy.context.scene
gz = parts.ground_height_at
def look(cam, pos, aim):
    cam.location = pos
    cam.rotation_euler = (aim - pos).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
def margin(cam, pts):
    m = 9.0
    for p in pts:
        co = world_to_camera_view(scene, cam, p)
        if co.z <= 0: return -9.0
        m = min(m, co.x, 1 - co.x, co.y, 1 - co.y)
    return m
B = {'A': (-40.05, 7.6, -26.45, 12.4, 5.3), 'B': (-9.2, 7.2, -2.8, 11.8, 6.5), 'C': (-29.7, -12.8, -22.3, -8.2, 4.8), 'D': (2.15, -10.2, 5.85, -5.8, 4.1), 'stable': (19.1, 36.0, 28.9, 42.0, 5.0)}
def box_pts(k, zs=(0.0, 1.0)):
    x0, y0, x1, y1, h = B[k]
    pts = []
    for x in (x0, x1):
        for y in (y0, y1):
            g = gz(x, y)
            pts += [Vector((x, y, g)), Vector((x, y, g + h))]
    return pts
well = [Vector((-17.5 + dx, 6.0 + dy, gz(-17.5 + dx, 6.0 + dy) + z)) for dx in (-1.5, 0, 1.5) for dy in (-1.5, 0, 1.5) for z in (0.0, 1.0)]
# --- wide
cam = bpy.data.objects['View wide']
aim = Vector((-5.0, 14.0, 2.0))
d = Vector((43.0, 44.0, 0.0)).normalized(); left = Vector((-d.y, d.x, 0.0))
route = []
for z in (14.0, 15.0):
    for s in (0.0, 1.0, 2.0, 3.0):
        pos = Vector((-48.0, -30.0, z)) + left * s
        look(cam, pos, aim)
        pts = []
        for k in B: pts += box_pts(k)
        pts += [Vector((-17.5, 6.0, gz(-17.5, 6.0) + 1.0)), Vector((20, 2, gz(20, 2)))]
        for x in (-45, -20, 20, 52):
            for a, b in zip(json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/plan/place-settings.json'))['roads'][0]['polyline'][:-1], json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/plan/place-settings.json'))['roads'][0]['polyline'][1:]):
                if a[0] <= x <= b[0]:
                    y = a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]); pts.append(Vector((x, y, gz(x, y)))); break
        route.append((round(margin(cam, pts), 3), z, s, tuple(round(v, 2) for v in pos)))
print('WIDE', sorted(route, reverse=True)[:6])
# --- cottage_close
cam = bpy.data.objects['View cottage_close']
aim = Vector((-31.0, 8.0, gz(-31, 8) + 1.6))
d = Vector((-17.0, 7.7, 0.0)).normalized(); right = Vector((d.y, -d.x, 0.0))
res = []
for s in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0):
    for dz in (0.0, 1.0):
        pos0 = Vector((-14.0, 0.3, 0.0)) + right * s
        pos = Vector((pos0.x, pos0.y, gz(pos0.x, pos0.y) + 1.7 + dz))
        look(cam, pos, aim)
        res.append((round(min(margin(cam, box_pts('A')), margin(cam, well)), 3), round(margin(cam, box_pts('A')), 3), round(margin(cam, well), 3), s, dz, tuple(round(v, 2) for v in pos)))
print('COTTAGE', sorted(res, reverse=True)[:8])
