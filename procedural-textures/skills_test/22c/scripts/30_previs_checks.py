# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22c, part 2: uses the previs skill's own tools (bx_previs.py of scenario-blender-previs-storyboard) on the street COPY's cameras: the film's main
# camera, the lockout plate camera and the notice-corner plate camera. The street has no people, so five stand-in walkers (the skill's own "mannequin",
# 1.7 m) are put at chosen spots to give every shot a subject: one in the open road, one hidden behind a gas lamp post on purpose, one for each of the
# other two cameras, and one outside the main camera's narrow frame on purpose. Then: the skill's shot audit (shot size, lens, is the subject in frame and
# is it blocked, camera height, intent), its contact sheet of stamped thumbnails, and its lens A/B sheet.
# The street's own cameras are never moved: the skill needs a lens in "36 mm wide sensor" terms, so previs-only CLONES of the three cameras are made
# (same place, same angle, same field of view, lens figure converted), and a check shows the clones frame a point exactly as the originals do.
# Nothing is saved back to the street file.
# Run (on the rented machine): /workspace/blender/blender -b --disable-autoexec --factory-startup set_copy/street.blend --python-exit-code 1 \
#        --python scripts/30_previs_checks.py -- out/previs
import json
import math
import os
import sys
import time

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.dont_write_bytecode = True
SK = '/home/user/Music/.claude/skills'
sys.path += [SK + '/scenario-blender-previs-storyboard/scripts', SK + '/scenario-blender-expert/scripts']
import bx_previs as P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import apply_wetness_to_set as aw  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
W, H = 540, 960
sc0 = bpy.context.scene
raw = aw.cameras()                                   # main (the film's own), lockout, notice (+ two test cameras)
RAW = {'main': raw['main'], 'lockout': raw['lockout'], 'notice': raw['notice']}
log = {'blender': bpy.app.version_string, 'skill_version': P.__version__}
log['raw_camera_lens_as_the_street_stores_it'] = {k: {'lens_mm': round(c.data.lens, 2), 'sensor_fit': c.data.sensor_fit, 'sensor_height_mm': c.data.sensor_height, 'vertical_fov_deg': round(math.degrees(c.data.angle_y), 2)} for k, c in RAW.items()}

# ------------------------------------------------------------------ previs scene: a NEW scene that shares the street's collections (nothing copied, nothing changed there)
pv = P.setup_scene('pv22c street', res=(W, H), fps=24, pct=100)
for c in sc0.collection.children:
    pv.collection.children.link(c)
for o in sc0.collection.objects:
    pv.collection.objects.link(o)

# ------------------------------------------------------------------ previs-only clones of the three cameras, in the skill's own lens convention (36 mm wide sensor)
clones = {}
for key, cam in RAW.items():
    vfov = cam.data.angle_y
    hfov = 2 * math.atan(math.tan(vfov / 2) * W / H)
    d = bpy.data.cameras.new(f'CA-{key}')
    d.sensor_fit, d.sensor_width = 'HORIZONTAL', P.SENSOR_W
    d.lens = P.SENSOR_W / (2 * math.tan(hfov / 2))
    d.clip_start, d.clip_end = 0.1, 1500.0
    ob = bpy.data.objects.new(f'CA-{key}', d)
    P.coll(pv, 'CA-cameras').objects.link(ob)
    ob.rotation_mode = 'QUATERNION'
    bpy.context.view_layer.update()
    ob.location = cam.matrix_world.translation
    ob.rotation_quaternion = cam.matrix_world.to_quaternion()
    clones[key] = ob
bpy.context.view_layer.update()
test_pt = Vector((0.5, 14.0, 2.0))
same = {}
for key in RAW:
    a = world_to_camera_view(pv, RAW[key], test_pt)
    b = world_to_camera_view(pv, clones[key], test_pt)
    same[key] = {'raw_xy': [round(a.x, 4), round(a.y, 4)], 'clone_xy': [round(b.x, 4), round(b.y, 4)], 'clone_lens_mm_36wide': round(clones[key].data.lens, 1)}
log['clone_check_same_framing'] = same

# ------------------------------------------------------------------ stand-in walkers on the ground (ray cast down onto the street)
dg = bpy.context.evaluated_depsgraph_get()


def ground_z(x, y):
    hit, loc, _n, _i, _ob, _m = sc0.ray_cast(dg, Vector((x, y, 60.0)), Vector((0, 0, -1)), distance=200.0)
    return loc.z if hit else y * math.tan(math.radians(4.0))


def forward(cam):
    f = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    f.z = 0
    return f.normalized()


def ahead(cam, dist, side=0.0):
    f = forward(cam)
    r = Vector((f.y, -f.x, 0))
    p = cam.matrix_world.translation + f * dist + r * side
    return p.x, p.y


def bbox_centre(name):
    eo = bpy.data.objects[name].evaluated_get(dg)
    pts = [eo.matrix_world @ Vector(c) for c in eo.bound_box]
    return sum(pts, Vector()) / len(pts)


post = bbox_centre('gas_lamp_1_post')
cam_xy = RAW['main'].matrix_world.translation
bx, by = cam_xy.x + (post.x - cam_xy.x) * 1.08, cam_xy.y + (post.y - cam_xy.y) * 1.08     # same line of sight as the post, 8 % further away (first try, 30 %, put him inside the house row: on a roof)
SPOTS = {
    'walkerA': ahead(RAW['main'], 6.0, -0.3),         # open road, main camera
    'walkerB': (bx, by),                              # hidden behind lamp post 1 on purpose, main camera
    'walkerC': ahead(RAW['lockout'], 4.5, 0.0),       # lockout camera
    'walkerD': ahead(RAW['notice'], 7.0, 0.6),        # notice-corner camera
    'walkerE': ahead(RAW['main'], 5.0, 3.5),          # beside the road, outside the main camera's 23-degree-wide frame on purpose
}
chars = {}
for n, (x, y) in SPOTS.items():
    chars[n] = P.mannequin(pv, n, 1.7, (x, y, ground_z(x, y)), facing=0.0, color=P.BLUE_GREY)
bpy.context.view_layer.update()
log['walker_spots_xyz'] = {n: [round(v, 2) for v in chars[n].location] for n in chars}
assert all(chars[n].location.z < 3.0 for n in chars), 'a walker landed on a roof: ' + str({n: chars[n].location.z for n in chars})

# ------------------------------------------------------------------ the shot list: one fact per beat, one shot per beat
BEATS = ['A walker is small in the open road under the colliery (main camera)',
         'A second walker stands behind the first gas lamp on the left (main camera)',
         'One person is close to the lockout camera',
         'One person stands up the street beside the notice-corner camera',
         'A walker stands beside the road, outside the main frame (main camera)']
SHOTS = [dict(id='sh010', beats=[1], subjects=['walkerA'], cam='main', lens_planned='main', size='wide', dur=2.0, intent='the street seen from its foot, standing height, the colliery at the end'),
         dict(id='sh020', beats=[2], subjects=['walkerB'], cam='main', size='ews', dur=2.0, intent='the same camera on the walker behind the lamp post'),
         dict(id='sh030', beats=[3], subjects=['walkerC'], cam='lockout', size='medium', dur=2.0, intent='lockout plate camera'),
         dict(id='sh040', beats=[4], subjects=['walkerD'], cam='notice', size='full', dur=2.0),           # no intent written on purpose
         dict(id='sh050', beats=[5], subjects=['walkerE'], cam='main', size='wide', dur=2.0, intent='the same camera on a walker outside its frame')]
table = P.shot_list(BEATS, SHOTS, start=10)
for t in table:
    cam = clones[t['cam']]
    m = pv.timeline_markers.new(t['id'], frame=t['frame'])
    m.camera = cam
    t['camera'] = cam.name
pv.camera = clones['main']
pv.frame_end = max(t['frame'] + t['block'] for t in table)
P.passepartout(list(clones.values()))
for t in table:
    cam = clones[t['cam']]
    cam['aim'] = list(Vector((*chars[t['subjects'][0]].matrix_world.translation.xy, P.eye_z(chars[t['subjects'][0]]))))

# ------------------------------------------------------------------ the skill's shot audit
t0 = time.time()
rep = P.audit(pv, table, chars)
log['audit_seconds'] = round(time.time() - t0, 2)
log['audit'] = rep
log['table_after_audit'] = [{k: t.get(k) for k in ('id', 'camera', 'subjects', 'size', 'size_measured', 'lens_measured', 'height_measured', 'intent')} for t in table]
print('AUDIT problems:', len(rep['problems']), flush=True)
for p in rep['problems']:
    print('  PROBLEM', p, flush=True)

# ------------------------------------------------------------------ contact sheet (stamped Workbench thumbnails) and lens A/B
try:
    t0 = time.time()
    sheet = P.contact_sheet(pv, table, os.path.join(out, 'sheet'), cols=5, chars=chars)
    log['contact_sheet'] = {'path': sheet, 'seconds': round(time.time() - t0, 2)}
except Exception as error:
    log['contact_sheet'] = {'error': repr(error)}
try:
    t0 = time.time()
    t1 = table[0]
    # the three shots on the main camera share one camera object, so its 'aim' was left on the LAST of them (walker E); the A/B needs shot sh010's own subject (walker A).
    # (first try forgot this: the A/B moved the camera along the line to walker E and showed an unfair picture)
    clones['main']['aim'] = list(Vector((*chars['walkerA'].matrix_world.translation.xy, P.eye_z(chars['walkerA']))))
    ab = P.ab_lens(pv, t1, [50, 88, 135], os.path.join(out, 'ab'), keep_size=True, chars=chars)
    log['ab_lens'] = {'path': ab, 'seconds': round(time.time() - t0, 2), 'note': 'lenses in the skill 36 mm-wide-sensor terms; 88 mm is the main camera as it is'}
except Exception as error:
    log['ab_lens'] = {'error': repr(error)}
try:
    far = [o for o in pv.objects if o.type == 'MESH' and (o.name in ('ground', 'sky_dome') or o.name.startswith(('moorland', 'spoil', 'headframe', 'heapstead', 'winding', 'engine_house', 'second_winding', 'colliery'))
           or bbox_centre(o.name).y > 45.0 or abs(bbox_centre(o.name).x) > 12.0)]
    fp = P.floor_plan(pv, table, chars, os.path.join(out, 'floor_plan.png'), hide=far, res=1000)
    log['floor_plan'] = {'path': str(fp)}
except Exception as error:
    log['floor_plan'] = {'error': repr(error)}


def plain(x):
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    return str(x)


json.dump(plain(log), open(os.path.join(out, 'previs_checks.json'), 'w'), indent=1)
print('DONE previs checks')
