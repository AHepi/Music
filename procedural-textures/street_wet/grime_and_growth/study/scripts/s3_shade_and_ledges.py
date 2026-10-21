# What this does (plain words): a STUDY PROTOTYPE (it saves nothing in the street file). It tries, on the street copy, three of the masks the weathering kit will need and does not
# have yet, the same way make_places_pictures.py makes its pictures (ask Blender's own geometry, no guessing):
#   1. SKY OPENNESS: from a point on the ground or on a wall face, shoot rays over the sky hemisphere; the share that escapes is how open to the sky the spot is (low = shaded and damp:
#      where moss, algae and green stains gather). Reported across the street at y = 10, along the wall foot, up a facade.
#   2. SUN SHADOW: for each sun lamp in the file, the share of sampled spots whose ray toward that lamp is blocked.
#   3. LEDGES (drip sources): faces that face up and stand out from a wall (sills, steps, plinth tops, string courses, eaves) found from the geometry, to compare with the numbers the
#      wetness layer was given by hand from the street builder (window sills at 0.85 and 3.55 m, eaves at 6.0 m above the cottage floor).
# Also writes a small coarse top-down picture of the openness for the look sheet (grayscale PNG, 0.1 m a dot).
# Run: blender -b --disable-autoexec street.blend --python s3_shade_and_ledges.py -- OUT_FOLDER
import json
import math
import os
import re
import sys
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
T0 = time.time()
result = {}


def triangles_of(objects):
    verts, tris, offset = [], [], 0
    for obj in objects:
        ev = obj.evaluated_get(deps)
        mesh = ev.to_mesh()
        if len(mesh.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mesh.calc_loop_triangles()
        co = np.empty(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        m = np.array(obj.matrix_world)
        verts.append(co @ m[:3, :3].T + m[:3, 3])
        tri = np.empty(len(mesh.loop_triangles) * 3, np.int64)
        mesh.loop_triangles.foreach_get('vertices', tri)
        tris.append(tri.reshape(-1, 3) + offset)
        offset += len(co)
        ev.to_mesh_clear()
    return np.concatenate(verts), np.concatenate(tris)


SOLID_RE = re.compile(r'^(right|left)_row_[ab]_cottage_\d+_(walls|trim|roof|chimney|end_chimney|rainwater|door|window_ground|window_upper_\d)$|^street_|^gas_lamp_\d+_post$|^engine_house_(walls|trim)$|^heapstead_(walls|trim)$|^colliery_chimney$|^headframe_lattice$|^second_winding_house_(walls|trim)$')
solids = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render and SOLID_RE.match(o.name)]
v, t = triangles_of(solids)
bvh = BVHTree.FromPolygons([tuple(p) for p in v], [tuple(p) for p in t], all_triangles=True)
ground_only = [o for o in scene.objects if o.type == 'MESH' and o.name in ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements')]
gv, gt = triangles_of(ground_only)
ground_bvh = BVHTree.FromPolygons([tuple(p) for p in gv], [tuple(p) for p in gt], all_triangles=True)      # the ground alone: a ray from above must not stop on an eave or a roof
result['blockers'] = len(solids)
result['build_seconds'] = round(time.time() - T0, 1)

# --------------------------------------------------------------------------- hemisphere directions (cosine weighted, 48 of them, fixed)
rng = np.random.default_rng(5)
N_DIR = 48
u1 = (np.arange(N_DIR) + rng.random(N_DIR)) / N_DIR
u2 = rng.random(N_DIR)
r = np.sqrt(u1)
phi = 2 * math.pi * u2
HEMI = np.stack([r * np.cos(phi), r * np.sin(phi), np.sqrt(1 - u1)], axis=1)       # z = up in the local frame of the surface
MAXD = 40.0


def frame_from_normal(n):
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    a = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    tx = np.cross(a, n)
    tx /= np.linalg.norm(tx)
    ty = np.cross(n, tx)
    return tx, ty, n


def openness(point, normal, lift=0.03):
    tx, ty, n = frame_from_normal(normal)
    origin = Vector(point) + Vector(n) * lift
    free = 0
    for d in HEMI:
        w = tx * d[0] + ty * d[1] + n * d[2]
        hit = bvh.ray_cast(origin, Vector(w), MAXD)
        if hit[0] is None:
            free += 1
    return free / N_DIR


def ground_z(x, y):
    hit = ground_bvh.ray_cast(Vector((x, y, 40.0)), Vector((0, 0, -1)), 80.0)
    return hit[0].z if hit[0] is not None else None


# --------------------------------------------------------------------------- 1. across the street at several y: openness of the ground (normal = up)
across = {}
timer = time.time()
count = 0
for y in (4.0, 10.0, 24.0, 45.0):
    row = {}
    for x in (-4.3, -3.8, -3.0, -2.45, -1.5, 0.0, 1.5, 2.45, 3.0, 3.8, 4.3):          # (the ground is the four street objects only)
        z = ground_z(x, y)
        if z is None:
            continue
        row[str(x)] = round(openness((x, y, z), (0, 0, 1)), 2)
        count += 1
    across[str(y)] = row
result['ground_openness_across'] = across
result['seconds_per_1000_openness_points'] = round((time.time() - timer) / max(count, 1) * 1000, 1)

# --------------------------------------------------------------------------- facade: openness up the wall (front faces), right row (normal -x) and left row (+x), at y = 10
facade = {}
for side, x, nx in (('right_row_wall_front', 4.14, -1.0), ('left_row_wall_front', -4.14, 1.0)):
    col = {}
    for y in (4.5, 10.0, 24.0):
        for h in (0.4, 1.0, 2.2, 3.5, 5.0):
            z = ground_z(x * 0.0 + (3.3 if nx < 0 else -3.3), y) + 0.13 + h
            col[f'y{y}_h{h}'] = round(openness((x, y, z), (nx, 0, 0), lift=0.02), 2)
    facade[side] = col
result['facade_openness'] = facade

# --------------------------------------------------------------------------- 2. the suns: share blocked
suns = [(o.name, np.array(o.matrix_world.to_quaternion() @ Vector((0, 0, 1)))) for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN']      # direction TOWARD the sun
result['suns_toward'] = {n: [round(float(c), 3) for c in d] for n, d in suns}
sun_blocked = {}
for name, d in suns:
    blocked_g = total_g = 0
    for y in np.arange(2.0, 60.0, 3.0):
        for x in np.arange(-4.3, 4.31, 0.4):
            z = ground_z(x, y)
            if z is None:
                continue
            total_g += 1
            origin = Vector((x, y, z + 0.05))
            hit = bvh.ray_cast(origin, Vector(d), 200.0)
            blocked_g += hit[0] is not None
    sun_blocked[name] = dict(ground_samples=total_g, ground_blocked_share=round(blocked_g / max(total_g, 1), 3))
    # facade faces: normal -x (right row front) and +x (left row front)
    for label, nx in (('right_row_front_normal_-x', -1.0), ('left_row_front_normal_+x', 1.0)):
        ndotl = float(np.dot(np.array([nx, 0, 0]), d))
        sun_blocked[name][label + '_n_dot_L'] = round(ndotl, 3)
result['sun_shadow'] = sun_blocked

# --------------------------------------------------------------------------- 3. ledges from geometry (cottage right_row_a_01: its trim, windows)
def collect_ledges(obj, wall_x=4.15, floor_z=None, min_area=0.01):
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    m = np.array(obj.matrix_world)
    out = []
    for p in me.polygons:
        n = np.array(p.normal) @ m[:3, :3].T
        n /= max(np.linalg.norm(n), 1e-9)
        if n[2] < 0.9 or p.area < min_area:
            continue
        pts = np.array([np.append(np.array(me.vertices[i].co), 1.0) @ m.T for i in p.vertices])[:, :3]
        c = pts.mean(0)
        out.append((c, pts.min(0), pts.max(0), p.area))
    ev.to_mesh_clear()
    return out


floor = bpy.data.objects['right_row_a_cottage_01_walls'].location.z      # cottage floor height (local z = 0)
y0 = bpy.data.objects['right_row_a_cottage_01_walls'].location.y         # centre of the cottage along y (local y = 0)
ledges = []
for name in ('right_row_a_cottage_01_trim', 'right_row_a_cottage_01_window_ground', 'right_row_a_cottage_01_window_upper_0', 'right_row_a_cottage_01_window_upper_1', 'right_row_a_cottage_01_door'):
    for c, lo, hi, area in collect_ledges(bpy.data.objects[name]):
        # in the cottage's own frame: x_out = how far in FRONT of the wall face (4.15 - world x), y across, z above the floor
        ledges.append(dict(src=name.split('cottage_01_')[1], x_out=round(4.15 - float(c[0]), 3), y=round(float(c[1] - y0), 2), z=round(float(c[2] - floor), 2), width_y=round(float(hi[1] - lo[1]), 2),
                           depth_x=round(float(hi[0] - lo[0]), 2), area=round(float(area), 3)))
ledges = [e for e in ledges if -0.2 < e['z'] < 7.0 and e['x_out'] > 0.0]       # in front of the wall face
ledges.sort(key=lambda e: (e['z'], e['y']))
result['ledges_cottage_01'] = ledges
# the builder's numbers the wetness layer uses by hand (apply_wetness_to_set.py): ground sill 0.85 m, upper sill 3.55 m, eaves 6.0 m (cottage floor = 0)
result['builder_numbers'] = dict(ground_window_sill=0.85, upper_window_sill=3.55, eaves=6.0, door_y=-1.15, ground_window_y=0.95, upper_y=[-1.15, 0.95])
# rain pipe: where it runs and its hopper
pipe = bpy.data.objects['right_row_a_cottage_01_rainwater']
ev = pipe.evaluated_get(deps)
me = ev.to_mesh()
co = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get('co', co)
co = co.reshape(-1, 3)
m = np.array(pipe.matrix_world)
w = co @ m[:3, :3].T + m[:3, 3]
result['rainwater_cottage_01'] = dict(world_min=[round(float(a), 2) for a in w.min(0)], world_max=[round(float(a), 2) for a in w.max(0)], y_rel_cottage_centre=[round(float(w[:, 1].min() - y0), 2), round(float(w[:, 1].max() - y0), 2)])
ev.to_mesh_clear()

# --------------------------------------------------------------------------- coarse openness picture, top-down, 0.1 m a dot, x -4.5..4.5, y 0..30 (90 x 300 dots)
timer = time.time()
W, H, DOT = 90, 300, 0.1
pic = np.zeros((H, W), np.float32)
for j in range(H):
    y = 0.0 + DOT * (j + 0.5)
    for i in range(W):
        x = -4.5 + DOT * (i + 0.5)
        z = ground_z(x, y)
        pic[j, i] = openness((x, y, z), (0, 0, 1)) if z is not None else 0.0
secs = time.time() - timer
np.save(os.path.join(out_folder, 'openness_top_down_0p1m.npy'), pic)
result['openness_picture'] = dict(size=[W, H], seconds=round(secs, 1), dots=W * H, seconds_per_1000_dots=round(secs / (W * H) * 1000, 2),
                                  mean_road=round(float(pic[:, 25:65].mean()), 3), mean_pavement=round(float(np.concatenate([pic[:, 5:18], pic[:, 72:85]], axis=1).mean()), 3))
json.dump(result, open(os.path.join(out_folder, 'shade_and_ledges.json'), 'w'), indent=1)
print('DONE', round(time.time() - T0, 1), 's')
