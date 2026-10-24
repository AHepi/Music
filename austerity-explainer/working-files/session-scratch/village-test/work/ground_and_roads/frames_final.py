import sys, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from place_kit import parts
parts.refresh_ground()
scene = bpy.context.scene
gz = parts.ground_height_at
road = json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/plan/place-settings.json'))['roads'][0]['polyline']
def road_pt(x):
    for a, b in zip(road[:-1], road[1:]):
        if a[0] <= x <= b[0]:
            y = a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]); return Vector((x, y, gz(x, y)))
items = {'cottage A centre (-32,10)': Vector((-32, 10, gz(-32, 10) + 1.5)), 'cottage B centre (-6,9.5)': Vector((-6, 9.5, gz(-6, 9.5) + 1.5)), 'cottage C centre (-26,-10.5)': Vector((-26, -10.5, gz(-26, -10.5) + 1.5)),
         'cottage D centre (4,-8)': Vector((4, -8, gz(4, -8) + 1.5)), 'well (-17.5,6)': Vector((-17.5, 6, gz(-17.5, 6) + 0.6)), 'lane junction (20,2)': Vector((20, 2, gz(20, 2))),
         'stable centre (24,39)': Vector((24, 39, gz(24, 39) + 2.0)), 'lean-to west end of A (-40.05,10)': Vector((-40.05, 10, gz(-40.05, 10) + 1.0)),
         'stable doorway (24,36)': Vector((24, 36, gz(24, 36) + 1.0))}
out = {}
cam = bpy.data.objects['View wide']; scene.camera = cam
out['wide'] = {k: [round(c, 3) for c in world_to_camera_view(scene, cam, v)[:2]] for k, v in items.items()}
xs = [-45, -20, 0, 20, 52]
out['wide_road'] = {str(x): [round(c, 3) for c in world_to_camera_view(scene, cam, road_pt(x))[:2]] for x in xs}
# length of the high road inside the frame (sampled every 1 m along its x range)
inside = [x for x in np.arange(-140, 140, 1.0) if (lambda c: 0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0 and c.z > 0)(world_to_camera_view(scene, cam, road_pt(float(x))))]
out['wide_road_inside_x_range'] = [min(inside), max(inside)] if inside else None
if inside:
    pts = [road_pt(float(x)) for x in (min(inside), max(inside))]
    out['wide_road_inside_length_m_approx'] = round(float(sum(np.hypot(*np.diff(np.array([[road_pt(float(x)).x, road_pt(float(x)).y] for x in inside]), axis=0).T))), 1)
for name in ('View road_eye', 'View stable_close', 'View cottage_close'):
    c = bpy.data.objects[name]; scene.camera = c
    out[name] = {k: [round(v, 3) for v in world_to_camera_view(scene, c, p)[:2]] for k, p in items.items()}
for name in ('View wide', 'View road_eye', 'View stable_close', 'View cottage_close'):
    c = bpy.data.objects[name]
    out.setdefault('cameras', {})[name] = {'location': [round(v, 3) for v in c.location], 'rotation_deg': [round(np.degrees(v), 2) for v in c.rotation_euler], 'lens': c.data.lens, 'clip': [c.data.clip_start, c.data.clip_end],
                                           'ground_below': round(gz(c.location.x, c.location.y), 3)}
json.dump(out, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/ground_and_roads/frames_final.json', 'w'), indent=1)
print('FRAMES', json.dumps(out)[:3000])
