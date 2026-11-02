"""
What this file does:
Builds the plain shapes of "a tea house": a short wet lane running along Y that ends at a tea house (stone ground
floor with two bay windows and a door, a jettied half-timbered upper floor, a steep gable, a chimney), with a stone
terrace on each side, gas lamps, little tea tables and chairs on the pavements and in front of the door, tea chests,
a teapot-shaped lantern hanging over the door, and a standing-person camera. Every object is named with role words.
Nothing is textured or lit here.

    python3 build_tea_house.py --out /home/claude/blind-test-2/plugin-build/PLACE.blend
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

FACE = 4.6          # the lane's facades stand at x = -FACE and x = +FACE
Y_FRONT = 22.0      # the tea house's ground-floor front face
Y_JETTY = 21.6      # the upper floor stands 0.4 m proud of the ground floor


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def smooth(obj):
    """Round parts (spheres, cylinders, rings) shade smooth; the flat caps and edges stay crisp."""
    try:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except Exception:
        pass
    return obj


def box(name, centre, size, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(scale=True)
    return obj


def cylinder(name, centre, radius, height, vertices=16, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=height, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = rotation
    return smooth(obj)


def plane(name, centre, size):
    bpy.ops.mesh.primitive_plane_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(scale=True)
    return obj


def sphere(name, centre, radius, squash=(1, 1, 1), segments=24, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = squash
    bpy.ops.object.transform_apply(scale=True)
    return smooth(obj)


def torus(name, centre, major, minor, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=20, minor_segments=8, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = rotation
    return smooth(obj)


def compound(name, parts, location=(0, 0, 0), yaw=0.0):
    """One object made of several cuboids [((cx, cy, cz), (sx, sy, sz)), ...], turned by yaw about Z."""
    bm = bmesh.new()
    for (cx, cy, cz), (sx, sy, sz) in parts:
        verts = bmesh.ops.create_cube(bm, size=1.0)['verts']
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=verts)
        bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (0, 0, yaw)
    return obj


def gable(name, x0, x1, y_front, depth, z0, z_apex):
    """A triangular wall (a prism): base from x0 to x1 at height z0, apex in the middle at z_apex."""
    xm = (x0 + x1) / 2
    yb = y_front + depth
    verts = [(x0, y_front, z0), (x1, y_front, z0), (xm, y_front, z_apex),
             (x0, yb, z0), (x1, yb, z0), (xm, yb, z_apex)]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def sash_parts(w, h):
    """The bars of a sash window (frame, centre bar, meeting rail, two more rails if tall) as cuboids about its centre."""
    t = 0.06
    parts = [((-(w - t) / 2, 0, 0), (t, 0.05, h)), (((w - t) / 2, 0, 0), (t, 0.05, h)),
             ((0, 0, (h - t) / 2), (w, 0.05, t)), ((0, 0, -(h - t) / 2), (w, 0.05, t)),
             ((0, 0, 0), (0.045, 0.05, h)), ((0, 0, h * 0.04), (w, 0.05, 0.05))]
    if h > 1.3:
        parts += [((0, 0, h * 0.30), (w, 0.05, 0.035)), ((0, 0, -h * 0.28), (w, 0.05, 0.035))]
    return parts


# ---------------------------------------------------------------- the ground

def ground():
    plane('road setts', (0, 1.5, 0), (5.0, 31.0))                      # y -14 to 17
    for side, word in ((-1, 'left'), (1, 'right')):
        box('pavement flags %s' % word, (side * 3.65, 4.0, 0.07), (1.9, 36.0, 0.14))
        box('kerb stone %s' % word, (side * 2.6, 1.5, 0.08), (0.2, 31.0, 0.16))
    box('apron pavement flags', (0, 19.5, 0.07), (5.4, 5.0, 0.14))     # the flagged floor in front of the tea house
    box('kerb stone front', (0, 16.9, 0.08), (5.0, 0.2, 0.16))


# ---------------------------------------------------------------- the two terraces

def terrace(side, y0, y1, height, tag, rng):
    word = 'left' if side < 0 else 'right'
    label = '%s terrace %s' % (word, tag)
    width = y1 - y0
    mid = (y0 + y1) / 2
    face_x = side * FACE
    box(label + ' wall', (face_x + side * 2.5, mid, height / 2), (5.0, width - 0.05, height))
    ridge = height + 1.8
    for pitch in (-1, 1):
        box(label + ' roof slate', (face_x + side * 2.5 + pitch * 1.25, mid, (height + ridge) / 2),
            (3.1, width + 0.2, 0.12), rotation=(0, pitch * math.radians(36), 0))
    box(label + ' chimney stack wall', (face_x + side * 3.6, mid + rng.uniform(-width * 0.25, width * 0.25), ridge + 0.6), (1.1, 0.8, 2.0))
    columns = max(2, int(width / 2.0))
    spacing = width / (columns + 0.4)
    floors = int((height - 2.4) / 2.9)
    for floor in range(1, floors + 1):
        z = 1.6 + floor * 2.9
        for column in range(columns):
            wy = mid + (column - (columns - 1) / 2) * spacing
            roll = rng.random()
            kind = 'window lit' if roll < 0.06 else ('window dim' if roll < 0.20 else 'window dark')
            box(label + ' window surround stone', (face_x - side * 0.04, wy, z), (0.08, 1.3, 1.9))
            box(label + ' ' + kind, (face_x - side * 0.08, wy, z), (0.06, 1.0, 1.6))
    door_y = mid - (columns - 1) / 2 * spacing
    box(label + ' door surround stone', (face_x - side * 0.05, door_y, 1.35), (0.10, 1.5, 2.7))
    box(label + ' door wood', (face_x - side * 0.09, door_y, 1.25), (0.06, 1.1, 2.4))
    box(label + ' door step', (face_x - side * 0.25, door_y, 0.18), (0.45, 1.4, 0.08))
    for column in range(1, columns):
        wy = mid + (column - (columns - 1) / 2) * spacing
        box(label + ' window surround stone', (face_x - side * 0.04, wy, 1.7), (0.08, 1.3, 2.1))
        box(label + ' window dim', (face_x - side * 0.08, wy, 1.7), (0.06, 1.0, 1.8))
    box(label + ' downpipe iron', (face_x - side * 0.12, y0 + 0.3, height / 2), (0.1, 0.1, height - 0.3))


# ---------------------------------------------------------------- the tea house

def tea_house():
    xs = 5.4                                  # half-width of the ground floor
    xu = 5.8                                  # half-width of the jettied upper floor
    z_ground, z_beam, z_upper_bottom, z_upper_top = 3.4, 3.4, 3.75, 7.15
    apex = 7.15 + 4.3                         # the gable's tip

    # ground floor: a stone wall with a door in the middle and a bay window on each side
    box('tea house ground wall stone', (0, 26.0, z_ground / 2), (2 * xs, 8.0, z_ground))
    y = Y_FRONT
    box('tea house door surround stone', (0, y - 0.05, 1.5), (1.7, 0.10, 3.0))
    box('tea house door wood', (0, y - 0.09, 1.15), (1.2, 0.06, 2.3))
    box('tea house door fanlight', (0, y - 0.08, 2.62), (1.0, 0.06, 0.38))
    box('tea house door step', (0, y - 0.28, 0.18), (1.9, 0.5, 0.08))
    for side in (-1, 1):
        c = side * 2.95
        box('tea house bay surround stone', (c, y - 0.05, 1.75), (3.1, 0.10, 2.1))
        for k in (-1, 0, 1):
            kind = 'lit' if (side < 0 or k == 0) else 'dim'
            box('tea house bay window ' + kind, (c + k * 0.93, y - 0.08, 1.75), (0.82, 0.06, 1.7))
        for k in (-0.5, 0.5):
            box('tea house bay mullion frame wood', (c + k * 0.93 * 2 * 0.5 * 1.0, y - 0.10, 1.75), (0.10, 0.10, 1.75))
        box('tea house bay transom frame wood', (c, y - 0.10, 2.35), (2.85, 0.10, 0.08))
        # a lamp on a bracket either side of the door
        lx = side * 1.12
        box('tea house door lamp bracket iron', (lx, y - 0.22, 2.5), (0.05, 0.4, 0.05))
        box('tea house door lamp glass %s' % ('left' if side < 0 else 'right'), (lx, y - 0.45, 2.72), (0.22, 0.22, 0.38))
        box('tea house door lamp cap iron', (lx, y - 0.45, 2.96), (0.30, 0.30, 0.07))
    box('tea house sign fascia frame wood', (0, y - 0.07, 3.1), (2 * xs - 0.2, 0.14, 0.42))

    # the jetty: the upper floor stands proud on a heavy beam
    box('tea house jetty frame wood', (0, (Y_JETTY + y + 0.35) / 2, (z_beam + z_upper_bottom) / 2), (2 * xu, y + 0.35 - Y_JETTY, z_upper_bottom - z_beam))

    # upper floor: plaster between dark timbers
    height_up = z_upper_top - z_upper_bottom
    box('tea house upper wall plaster', (0, (Y_JETTY + 30.0) / 2, (z_upper_bottom + z_upper_top) / 2), (2 * xu, 30.0 - Y_JETTY, height_up))
    yu = Y_JETTY
    stud_x = (-5.72, -4.3, -2.85, -1.4, 1.4, 2.85, 4.3, 5.72)
    for x in stud_x:
        box('tea house upper stud frame wood', (x, yu - 0.05, (z_upper_bottom + z_upper_top) / 2), (0.16, 0.12, height_up))
    for z, thickness in ((z_upper_bottom + 0.12, 0.22), (6.62, 0.14), (z_upper_top - 0.1, 0.2)):
        box('tea house upper rail frame wood', (0, yu - 0.06, z), (2 * xu, 0.12, thickness))
    kinds = {-5.0: 'dark', -3.575: 'dim', -2.125: 'dark', 2.125: 'lit', 3.575: 'dark', 5.0: 'dim'}
    for x, kind in kinds.items():
        box('tea house upper window surround stone', (x, yu - 0.04, 5.5), (1.15, 0.08, 1.75))
        box('tea house upper window ' + kind, (x, yu - 0.08, 5.5), (0.9, 0.06, 1.5))
        compound('tea house upper sash bar frame wood', sash_parts(0.9, 1.5), (x, yu - 0.14, 5.5))
    # the centre bay above the door has no window: two crossed braces, and the teapot lantern hangs in front of it
    for sign in (-1, 1):
        box('tea house centre brace frame wood', (0, yu - 0.05, 5.45), (3.35, 0.10, 0.13),
            rotation=(0, sign * math.radians(50), 0))
    # a diagonal in each of the two plain panels next to the windows
    # (the outer panels hold windows; the braces go in the corner panels beside the centre)

    # the gable, its timbers and its round-topped window
    gable('tea house gable wall plaster', -xu, xu, yu, 0.5, z_upper_top, apex)
    box('tea house gable king post frame wood', (0, yu - 0.05, (z_upper_top + apex) / 2), (0.2, 0.12, apex - z_upper_top))
    for z, half in ((8.1, 4.7), (9.9, 2.9)):
        box('tea house gable collar frame wood', (0, yu - 0.06, z), (2 * half, 0.12, 0.2))
    box('tea house gable window surround stone', (0, yu - 0.04, 8.95), (1.2, 0.08, 1.45))
    box('tea house gable window lit', (0, yu - 0.08, 8.95), (0.95, 0.06, 1.2))
    compound('tea house gable sash bar frame wood', sash_parts(0.95, 1.2), (0, yu - 0.14, 8.95))
    # the roof: two steep slates meeting at a ridge, boards on the front edges
    slope = math.atan2(apex - z_upper_top, xu)
    length = math.hypot(xu, apex - z_upper_top) + 0.55
    for pitch in (-1, 1):
        cx = pitch * (xu * 0.5 + 0.12)
        cz = z_upper_top + (apex - z_upper_top) * 0.5 + 0.1
        box('tea house roof slate', (cx, 25.8, cz), (length, 9.2, 0.14), rotation=(0, pitch * slope, 0))
        box('tea house bargeboard frame wood', (cx, 21.2 - 0.04, cz - 0.1), (length, 0.07, 0.3), rotation=(0, pitch * slope, 0))
    box('tea house ridge roof slate', (0, 25.8, apex + 0.1), (0.32, 9.2, 0.18))
    # the chimney, with two pots, and the smoke above it
    box('tea house chimney stack wall', (3.1, 27.4, 11.4), (1.15, 1.15, 5.0))
    for dx in (-0.25, 0.25):
        cylinder('tea house chimney pot trim', (3.1 + dx, 27.4, 14.15), 0.17, 0.55, vertices=12)
    for k, (sx, sz, w, h) in enumerate(((3.1, 15.7, 1.5, 3.0), (3.9, 18.1, 2.3, 3.2), (5.0, 20.6, 3.2, 3.4))):
        box('tea house chimney smoke %d' % (k + 1), (sx, 27.4, sz), (w, w * 0.85, h))

    # the teapot lantern: a big glowing body on an iron bracket; foot, lid with a knob, a long rising spout and a loop handle
    # are iron, dark against the plaster. About 1.7 times life size, as a trade sign is.
    ty, tz, radius = 20.9, 4.95, 0.58
    arm_z = 6.5
    lid_z = tz + radius * 0.80
    box('tea house teapot sign bracket iron', (0, (ty + yu) / 2, arm_z), (0.09, yu - ty + 0.05, 0.09))
    box('tea house teapot sign crossbar iron', (0, ty, arm_z), (0.62, 0.09, 0.09))
    for dx in (-0.22, 0.22):
        box('tea house teapot sign chain iron', (dx, ty, (arm_z + lid_z) / 2), (0.035, 0.035, arm_z - lid_z))
    sphere('tea house teapot lamp glass body', (0, ty, tz), radius, squash=(1, 1, 0.80), segments=32, rings=18)
    cylinder('tea house teapot foot iron', (0, ty, tz - radius * 0.80 - 0.02), 0.34, 0.10, vertices=20)
    cylinder('tea house teapot lid collar iron', (0, ty, lid_z), 0.30, 0.09, vertices=20)
    sphere('tea house teapot lid dome iron', (0, ty, lid_z + 0.03), 0.27, squash=(1, 1, 0.5), segments=20, rings=10)
    sphere('tea house teapot knob iron', (0, ty, lid_z + 0.20), 0.07, segments=10, rings=6)
    cylinder('tea house teapot spout iron', (0.64, ty, tz - 0.05), 0.12, 0.40, vertices=12, rotation=(0, math.radians(68), 0))
    cylinder('tea house teapot spout tip iron', (0.97, ty, tz + 0.21), 0.085, 0.52, vertices=12, rotation=(0, math.radians(40), 0))
    torus('tea house teapot handle iron', (-0.78, ty, tz + 0.02), 0.30, 0.055, rotation=(math.radians(90), 0, 0))

    # tea chests stacked beside the door, a barrel of tea leaf scraps by the other
    box('tea chest crate wood 1', (-1.75, 21.55, 0.14 + 0.30), (0.52, 0.52, 0.60), rotation=(0, 0, math.radians(8)))
    box('tea chest crate wood 2', (-1.72, 21.50, 0.14 + 0.90), (0.50, 0.50, 0.60), rotation=(0, 0, math.radians(-14)))
    box('tea chest crate wood 3', (-2.35, 21.45, 0.14 + 0.30), (0.52, 0.52, 0.60), rotation=(0, 0, math.radians(-5)))
    box('tea chest crate wood 4', (1.8, 21.5, 0.14 + 0.30), (0.52, 0.52, 0.60), rotation=(0, 0, math.radians(12)))
    cylinder('tea barrel wood', (2.45, 21.5, 0.14 + 0.45), 0.30, 0.90, vertices=18)


# ---------------------------------------------------------------- lamps, tables, puddles

def street_lamp(x, y):
    cylinder('lamp post iron %d' % round(y * 10), (x, y, 1.9), 0.06, 3.6)
    box('lamp glass %d' % round(y * 10), (x, y, 3.95), (0.26, 0.26, 0.42))
    box('lamp cap iron %d' % round(y * 10), (x, y, 4.2), (0.38, 0.38, 0.10))


def tea_table(x, y, z0, yaw, tag, chairs=2):
    """A round tea table (iron base, wooden top), a teapot and two cups on it, and chairs around it."""
    compound('tea table base iron %s' % tag, [((0, 0, 0.36), (0.07, 0.07, 0.72)), ((0, 0, 0.02), (0.44, 0.44, 0.04))], (x, y, z0), yaw)
    cylinder('tea table top wood %s' % tag, (x, y, z0 + 0.74), 0.40, 0.04, vertices=20)
    big = 1.5                                   # tea sets are drawn 1.5 times life size so they read from the lane
    top = z0 + 0.76
    sphere('teapot plaster %s' % tag, (x - 0.06, y, top + 0.09 * big), 0.09 * big, squash=(1, 1, 0.9), segments=14, rings=8)
    cylinder('teapot lid plaster %s' % tag, (x - 0.06, y, top + 0.17 * big), 0.045 * big, 0.03 * big, vertices=10)
    cylinder('teapot spout plaster %s' % tag, (x - 0.06 + 0.13 * big, y, top + 0.12 * big), 0.016 * big, 0.14 * big, vertices=8, rotation=(0, math.radians(50), 0))
    torus('teapot handle plaster %s' % tag, (x - 0.06 - 0.10 * big, y, top + 0.09 * big), 0.05 * big, 0.012 * big, rotation=(math.radians(90), 0, 0))
    for k, (dx, dy) in enumerate(((0.18, 0.13), (0.10, -0.15))):
        cylinder('teacup plaster %s %d' % (tag, k), (x + dx, y + dy, top + 0.03 * 1.4), 0.04 * 1.4, 0.06 * 1.4, vertices=12)
    for k in range(chairs):
        angle = yaw + math.radians(100 + 160 * k)
        cx, cy = x + 0.62 * math.cos(angle), y + 0.62 * math.sin(angle)
        turn = angle - math.pi / 2
        parts = [((0, 0, 0.46), (0.40, 0.40, 0.04)),
                 ((0, 0.19, 0.69), (0.40, 0.04, 0.42)),
                 ((0.17, 0.17, 0.22), (0.035, 0.035, 0.44)), ((-0.17, 0.17, 0.22), (0.035, 0.035, 0.44)),
                 ((0.17, -0.17, 0.22), (0.035, 0.035, 0.44)), ((-0.17, -0.17, 0.22), (0.035, 0.035, 0.44))]
        compound('tea chair wood %s %d' % (tag, k), parts, (cx, cy, z0), turn)


def puddles():
    for i, (x, y, w, l) in enumerate(((0.3, 8.0, 1.5, 3.0), (-1.2, 12.5, 1.8, 2.4), (1.3, 14.5, 1.4, 2.0), (-0.4, 4.5, 1.7, 2.2),
                                       (0.1, 16.1, 2.2, 0.9), (-1.3, 1.5, 1.4, 1.6))):
        plane('puddle water %d' % i, (x, y, 0.012), (w, l))
    plane('puddle water apron', (0.0, 20.2, 0.152), (2.2, 1.0))


def camera():
    data = bpy.data.cameras.new('tea house camera')
    data.lens = 32
    data.sensor_width = 36
    cam = bpy.data.objects.new('tea house camera', data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.25, -2.0, 1.65)
    target = Vector((0.0, 22.0, 3.3))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920


def build(seed=11):
    rng = random.Random(seed)
    clear()
    ground()
    terrace(-1, 7.0, 14.0, 8.4, '00', rng)
    terrace(-1, 14.0, 21.0, 11.3, '01', rng)
    terrace(1, 7.0, 13.5, 11.3, '00', rng)
    terrace(1, 13.5, 21.0, 8.4, '01', rng)
    tea_house()
    for x, y in ((-2.9, 10.0), (2.9, 13.5), (-2.9, 17.5), (2.9, 19.8)):
        street_lamp(x, y)
    # tea tables: two in front of the bays, one on each pavement
    tea_table(-1.9, 19.0, 0.14, 0.4, 'a')
    tea_table(1.7, 18.6, 0.14, -0.3, 'b')
    tea_table(-3.65, 15.5, 0.14, 0.2, 'c')
    tea_table(3.65, 11.5, 0.14, 1.0, 'd', chairs=1)
    puddles()
    camera()


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    build()
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print('saved', out, 'objects:', len(bpy.data.objects))


if __name__ == '__main__':
    main()
