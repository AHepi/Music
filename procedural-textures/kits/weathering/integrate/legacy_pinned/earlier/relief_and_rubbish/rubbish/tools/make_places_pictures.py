# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# It measures WHERE THINGS STAND on the street's ground, so that the rubbish mask knows where rubbish gathers: along the foot of the house walls, round the doorsteps,
# at the foot of the rain pipes and the lamp posts, in the corners, and round the props of the lockout shot (the fire drum, sacks, handcart, dustbins ...).
# It reads the real 3D street (the street copy, or the film's lockout shot file opened read-only; nothing is ever saved) and writes TWO small flat pictures seen from above
# ("places pictures"), one dot = 4 cm of street, covering across the street x = -4.5 to 4.5 m and along it y = -12 to 72 m (225 x 2100 dots):
#   picture A   red   = how far the ground is from the nearest HOUSE WALL, STEP or PLINTH (0 = touching, 255 = 1.275 m or more)
#               green = how far the ground is from the nearest PROP (drum, sacks, cart, bins, pails, barrel, ladder ... only in the lockout file)
#               blue  = the "catch points" in one picture: doorsteps, rain-pipe feet, lamp-post feet and inside corners (0 none, 255 strongest)
#   picture B   red   = inside corners only (where two solid things meet: a step and its wall, a bin and the wall)  0..255
#               green = doorsteps only (the foot of every front step)                                              0..255
#               blue  = rain-pipe feet and lamp-post feet only                                                      0..255
# Why measure instead of listing: every wall, step, pipe and prop that stands in the file is found by itself, and a prop moved in the file gives a new picture by running this again.
# How (all by asking Blender's own geometry): for every dot of the ground, find the ground height by a ray from above, then ask "how far is the nearest wall / step / pipe / post /
# prop" from a point 3 cm above the ground; doorsteps come from the door frames' empty objects; an inside corner is a dot where many of 12 short sideways rays (45 cm long, 25 cm above
# the ground) hit something although the nearest wall is far away: more blocked rays than a straight wall would give.
# Run (street copy):   blender -b --disable-autoexec FILE --python make_places_pictures.py -- OUT_PREFIX [street|lockout]
#   writes OUT_PREFIX_a.png, OUT_PREFIX_b.png, OUT_PREFIX_numbers.json and OUT_PREFIX_check.jpg (a look at the pictures). It changes nothing in the file.
import json
import math
import os
import re
import struct
import sys
import time
import zlib

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

X0, X1, Y0, Y1, DOT = -4.5, 4.5, -12.0, 72.0, 0.04
WIDTH, HEIGHT = int(round((X1 - X0) / DOT)), int(round((Y1 - Y0) / DOT))
DIST_SCALE = 1.275               # picture value 255 = this many metres
GROUND_NAMES = ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements')
BUILDING_RE = re.compile(r'^(left|right)_row_[ab]_cottage_\d+_(walls|trim)$')
PIPE_RE = re.compile(r'^(left|right)_row_[ab]_cottage_\d+_rainwater$')
POST_RE = re.compile(r'^gas_lamp_\d+_post$')
DOORWAY_RE = re.compile(r'^(left|right)_row_[ab]_cottage_\d+_doorway$')
args = sys.argv[sys.argv.index('--') + 1:]
out_prefix = args[0]
kind = args[1] if len(args) > 1 else 'street'
started = time.time()
depsgraph = bpy.context.evaluated_depsgraph_get()
STREET_NAMES = set(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'objects_street.txt')).read().split('\n'))
STREET_NAMES = set(line.split()[0] for line in STREET_NAMES if line.strip())


def triangles_of(objects):
    """All the triangles of the objects (modifiers applied) in world space: (vertices Nx3, triangles Mx3)."""
    verts, tris, offset = [], [], 0
    for obj in objects:
        ev = obj.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        if len(mesh.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mesh.calc_loop_triangles()
        co = np.empty(len(mesh.vertices) * 3, np.float64)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        matrix = np.array(obj.matrix_world)
        world = co @ matrix[:3, :3].T + matrix[:3, 3]
        tri = np.empty(len(mesh.loop_triangles) * 3, np.int64)
        mesh.loop_triangles.foreach_get('vertices', tri)
        verts.append(world)
        tris.append(tri.reshape(-1, 3) + offset)
        offset += len(world)
        ev.to_mesh_clear()
    if not verts:
        return None
    return np.concatenate(verts), np.concatenate(tris)


def make_tree(objects):
    data = triangles_of(objects)
    if data is None:
        return None
    v, t = data
    return BVHTree.FromPolygons([tuple(p) for p in v], [tuple(p) for p in t], all_triangles=True)


def bbox(obj):
    ev = obj.evaluated_get(depsgraph)
    corners = np.array([obj.matrix_world @ Vector(c) for c in ev.bound_box])
    return corners.min(axis=0), corners.max(axis=0)


objects = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render]
ground_objects = [o for o in objects if o.name in GROUND_NAMES]
building_objects = [o for o in objects if BUILDING_RE.match(o.name)]
pipe_objects = [o for o in objects if PIPE_RE.match(o.name)]
post_objects = [o for o in objects if POST_RE.match(o.name)]
ground_tree = make_tree(ground_objects)
# the props: meshes of this file that are not in the street copy (lockout file only), standing on the ground (not floating above it, not far up the street)
prop_objects, skipped = [], []
if kind == 'lockout':
    for o in objects:
        if o.name in STREET_NAMES or o.name in GROUND_NAMES:
            continue
        lo, hi = bbox(o)
        cx, cy = 0.5 * (lo[0] + hi[0]), 0.5 * (lo[1] + hi[1])
        hit = ground_tree.ray_cast(Vector((cx, cy, 60.0)), Vector((0, 0, -1)), 120.0)
        ground_z = hit[0].z if hit[0] is not None else None
        if ground_z is None or cy > 70.0 or abs(cx) > 4.4:
            skipped.append((o.name, 'off the street'))
            continue
        if lo[2] - ground_z > 0.35 or hi[2] - ground_z > 2.6:
            skipped.append((o.name, 'floating or too high'))
            continue
        prop_objects.append(o)
building_tree = make_tree(building_objects)
pipe_tree = make_tree(pipe_objects)
post_tree = make_tree(post_objects)
prop_tree = make_tree(prop_objects)
all_tree = make_tree(building_objects + pipe_objects + post_objects + prop_objects)
print('TREES built in', round(time.time() - started, 1), 's: ground', len(ground_objects), 'buildings', len(building_objects), 'pipes', len(pipe_objects), 'posts', len(post_objects),
      'props', len(prop_objects), flush=True)
print('PROPS', sorted(o.name for o in prop_objects), flush=True)
doorways = [(o.matrix_world.translation.x, o.matrix_world.translation.y) for o in bpy.context.scene.objects if DOORWAY_RE.match(o.name)]
print('DOORWAYS', len(doorways), flush=True)

# ------------------------------------------------------------------------------------------------------------------------------- the grid
xs = X0 + DOT * (np.arange(WIDTH) + 0.5)
ys = Y0 + DOT * (np.arange(HEIGHT) + 0.5)
FAR = DIST_SCALE
d_build = np.full((HEIGHT, WIDTH), FAR, np.float32)
d_prop = np.full((HEIGHT, WIDTH), FAR, np.float32)
d_pipe = np.full((HEIGHT, WIDTH), FAR, np.float32)
d_post = np.full((HEIGHT, WIDTH), FAR, np.float32)
has_ground = np.zeros((HEIGHT, WIDTH), bool)
ground_z = np.zeros((HEIGHT, WIDTH), np.float32)
down = Vector((0, 0, -1))
T_ground = time.time()
for j, y in enumerate(ys):
    for i, x in enumerate(xs):
        hit = ground_tree.ray_cast(Vector((x, y, 40.0)), down, 80.0)
        if hit[0] is None:
            continue
        ground_z[j, i] = hit[0].z
        has_ground[j, i] = True
print('GROUND heights found in', round(time.time() - T_ground, 1), 's', flush=True)
T_dist = time.time()
for j, y in enumerate(ys):
    for i, x in enumerate(xs):
        if not has_ground[j, i]:
            continue
        origin = Vector((x, y, ground_z[j, i] + 0.03))
        ax = abs(x)
        if building_tree is not None and ax > 2.7:
            r = building_tree.find_nearest(origin, FAR)
            if r[0] is not None:
                d_build[j, i] = r[3]
        if prop_tree is not None:
            r = prop_tree.find_nearest(origin, FAR)
            if r[0] is not None:
                d_prop[j, i] = r[3]
        if pipe_tree is not None and ax > 2.7:
            r = pipe_tree.find_nearest(origin, 0.6)
            if r[0] is not None:
                d_pipe[j, i] = r[3]
        if post_tree is not None and ax > 1.6:
            r = post_tree.find_nearest(origin, 0.6)
            if r[0] is not None:
                d_post[j, i] = r[3]
print('DISTANCES found in', round(time.time() - T_dist, 1), 's', flush=True)

# ------------------------------------------------------------------------------------------------------------------------------- inside corners (sideways rays)
d_any = np.minimum.reduce([d_build, d_prop, d_pipe + 0.0, d_post + 0.0])
RAY_R, RAYS, RAY_H = 0.45, 12, 0.25
directions = [Vector((math.cos(2 * math.pi * k / RAYS), math.sin(2 * math.pi * k / RAYS), 0.0)) for k in range(RAYS)]
blocked = np.zeros((HEIGHT, WIDTH), np.float32)
T_corner = time.time()
candidates = np.argwhere(has_ground & (d_any < RAY_R) & (d_any > 0.015))
for j, i in candidates:
    origin = Vector((xs[i], ys[j], ground_z[j, i] + RAY_H))
    n = 0
    for d in directions:
        if all_tree.ray_cast(origin, d, RAY_R)[0] is not None:
            n += 1
    blocked[j, i] = n / RAYS
print('CORNER rays for', len(candidates), 'dots in', round(time.time() - T_corner, 1), 's', flush=True)
# what a straight wall at distance d would block: acos(d / r) / pi (the share of directions that reach the wall within r)
planar = np.where(d_any < RAY_R, np.arccos(np.clip(d_any / RAY_R, 0, 1)) / math.pi, 0.0)
corner = np.clip((blocked - planar - 0.08) / 0.30, 0, 1) * (d_any < RAY_R)
corner = corner.astype(np.float32)

# ------------------------------------------------------------------------------------------------------------------------------- doorsteps, pipe feet, post feet
X, Y = np.meshgrid(xs, ys)
door = np.zeros((HEIGHT, WIDTH), np.float32)
for dx, dy in doorways:
    door = np.maximum(door, np.exp(-(((X - dx) / 0.55) ** 2 + ((Y - dy) / 0.65) ** 2)))
pipe_foot = np.exp(-(d_pipe / 0.20) ** 2) * (d_pipe < 0.6)
post_foot = np.exp(-(d_post / 0.18) ** 2) * (d_post < 0.6)
feet = np.maximum(pipe_foot, post_foot).astype(np.float32)
catch = np.maximum.reduce([door, feet, 0.9 * corner]).astype(np.float32)
# where there is no ground (beyond the pavement edge) nothing
for arr in (door, feet, catch, corner):
    arr[~has_ground] = 0.0


def to8(arr):
    return np.clip(np.round(arr * 255), 0, 255).astype(np.uint8)


a = np.stack([to8(np.clip(d_build / DIST_SCALE, 0, 1)), to8(np.clip(d_prop / DIST_SCALE, 0, 1)), to8(catch)], axis=-1)
b = np.stack([to8(corner), to8(door), to8(feet)], axis=-1)


def write_png(path, rgb):
    """A plain 8-bit RGB PNG; the first row of the file is the TOP of the picture, so the array (row 0 = y = Y0, the low end of the street) is flipped first."""
    rgb = np.ascontiguousarray(np.flipud(rgb))
    h, w, _ = rgb.shape
    raw = b''.join(b'\x00' + rgb[r].tobytes() for r in range(h))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)


os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
write_png(out_prefix + '_a.png', a)
write_png(out_prefix + '_b.png', b)
near_wall = (d_build < 0.5) & has_ground
numbers = dict(kind=kind, size=[WIDTH, HEIGHT], dot_m=DOT, x_range=[X0, X1], y_range=[Y0, Y1], dist_scale_m=DIST_SCALE, doorways=len(doorways), props=sorted(o.name for o in prop_objects),
               props_skipped=skipped, share_ground_within_50cm_of_a_wall=float(near_wall.sum() / max(1, has_ground.sum())),
               share_corner_over_half=float(((corner > 0.5) & has_ground).sum() / max(1, has_ground.sum())), share_prop_within_80cm=float(((d_prop < 0.8) & has_ground).sum() / max(1, has_ground.sum())),
               seconds=round(time.time() - started, 1), objects_used=dict(buildings=len(building_objects), pipes=len(pipe_objects), posts=len(post_objects), props=len(prop_objects)))
json.dump(numbers, open(out_prefix + '_numbers.json', 'w'), indent=1)
print(json.dumps(numbers, indent=1), flush=True)
print('PLACES DONE', kind, round(time.time() - started, 1), 's', flush=True)
