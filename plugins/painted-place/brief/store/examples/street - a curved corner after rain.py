"""
What this file does: the store's worked example for its street tools: a wet street corner on a curve at dusk, after
rain. A sett road climbs gently and bends to the right; kerbs and flagged pavements follow both its edges round the
bend. Along the outside of the bend runs a wall that follows it in straight stretches, each stretch one flat plane
filled by the wall tool: old red brick, one stretch in Flemish bond of dark sooty brick, then a stretch of dressed stone
blocks; it ends at a house front of photographed ashlar with a door and windows and a slate roof. A lit gas lamp stands
on the far pavement, away from the eye, its light on the wet setts and in the puddles standing on them in the low
places by the kerbs; a second lamp stands out of the frame on the near pavement, so only its light is seen on the
near setts. Two lit windows, each with a small warm light outside it. An ash bin by the door, a sodden newspaper in the
gutter and a few weeds in the joints, out of the wheel lines. (A low wall of dark brick in English bond also runs round
the inside of the bend; the tall frame never shows it.) It is drawn from eye height in the road, 540 x 960, and finished.

    python3 "street - a curved corner after rain.py" [WIDTH HEIGHT SAMPLES OUT.png]     (defaults 540 960 64, in the folder you run it from)

Full size takes about six minutes on two processors (the building about half a minute of it); try 270 480 16 first.
Never run it from inside the brief folder without OUT: the picture goes where you run it.

The order of the steps is the point of the example:
    1. the road's middle line (a few points; the road climbs and bends with it), lay_cobbles.lay_setts_along
    2. lay_cobbles.road_edges: the kerbs' lines (lay_kerb), the pavements' middles (lay_cobbles.lay_flags_along) and
       the line the walls stand on, all from the same line, so everything follows the bend exactly
    3. the walls: one flat plane per straight stretch along the outside of the bend, each filled by lay_wall
    4. the house: a box, lay_stone (door, windows in timber frames, two lit), then lay_eaves (the roof), the parts
    5. the puddles: puddle.make with level=lay_cobbles.top_at(setts, x, y) + 0.002, the water flat over the setts
    6. joint_weeds in the joints by the kerbs, out of the wheel lines; the materials made wet
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import store  # noqa: E402
import lay_cobbles  # noqa: E402
import lay_kerb  # noqa: E402
import lay_wall  # noqa: E402
import lay_stone  # noqa: E402
import lay_eaves  # noqa: E402
import puddle  # noqa: E402
import joint_weeds  # noqa: E402
import sky_and_haze  # noqa: E402
import finish  # noqa: E402

WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 540
HEIGHT = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 64
OUT = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else os.path.join(os.getcwd(), 'street - a curved corner after rain.png')

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def new_materials(before):
    return [m for m in bpy.data.materials if m.name not in before]


def dials(materials, shade=None, bump=None, normal=None, grime=None):
    """Turn other dials on the copies a tool made: each stone's shade, the relief, the grime in the hollows."""
    for m in materials:
        nodes = m.node_tree.nodes if m.node_tree else {}
        if shade is not None and 'Pieces' in nodes:
            nodes['Pieces'].inputs['Shade'].default_value = shade
        if 'Weather' in nodes:
            if bump is not None:
                nodes['Weather'].inputs['Bump'].default_value = bump
            if grime is not None:
                nodes['Weather'].inputs['Grime'].default_value = grime
        if normal is not None and 'Normal picture' in nodes:
            nodes['Normal picture'].inputs['Strength'].default_value = normal


def wet(materials, amount):
    """Turn up the Wet dial on the copies a tool made (never the store's own materials)."""
    for m in materials:
        if m.node_tree and 'Weather' in m.node_tree.nodes and 'Wet' in m.node_tree.nodes['Weather'].inputs:
            m.node_tree.nodes['Weather'].inputs['Wet'].default_value = amount


# ----------------------------------------------------------------------------------------------- 1. the road
ROAD = 5.0                                      # the road's width
KERB_W, KERB_H = 0.30, 0.13
PAVE = 2.1                                      # the pavements' width
R, CX, CY = 9.0, 9.0, 3.0                       # the bend: a circle's radius and middle


def on_bend(degrees, z):
    a = math.radians(degrees)
    return (CX + R * math.cos(a), CY + R * math.sin(a), z)


CLIMB = 0.012                                   # the road climbs 1.2 cm a metre


def build_line():
    """The road's middle: straight, a quarter circle to the right, straight again; points about 2.4 m apart."""
    points = []
    for y in numpy.linspace(-14.0, CY, 8)[:-1]:
        points.append((0.0, float(y), (y + 14.0) * CLIMB))
    arc0 = (CY + 14.0)
    for degrees in numpy.linspace(180.0, 90.0, 7):
        x, y, _ = on_bend(degrees, 0.0)
        points.append((x, y, (arc0 + R * math.radians(180.0 - degrees)) * CLIMB))
    end0 = arc0 + R * math.pi / 2
    for d in numpy.linspace(0.0, 18.0, 8)[1:]:
        points.append((CX + float(d), CY + R, (end0 + d) * CLIMB))
    return points


LINE = build_line()

before = set(m.name for m in bpy.data.materials)
# near the eye more setts are rocked loose (sunk and tipped), so each catches the light its own way and the near road
# does not read as a flat picture of setts
setts = lay_cobbles.lay_setts_along(LINE, ROAD, seed=3, shades=0.3, quarries=True, rocked=0.16,
                                    rocked_area=(-3.0, -14.0, 3.0, 7.0), grit=True, moss='all', missing=0.004)
wet(new_materials(before), 0.8)                 # after rain: dark and glossy

# ----------------------------------------------------------------------------------------------- 2. kerbs and pavements
left, right = lay_cobbles.road_edges(LINE, ROAD)                       # the road's edges, at the setts' tops there
before = set(m.name for m in bpy.data.materials)
lay_kerb.lay(left, road='right', height=KERB_H, width=KERB_W, seed=1)
lay_kerb.lay(right, road='left', height=KERB_H, width=KERB_W, seed=2)
wet(new_materials(before), 0.6)
dials(new_materials(before), shade=0.2, bump=0.35, grime=0.45)

outer_mid, inner_mid = lay_cobbles.road_edges(LINE, ROAD, beyond=KERB_W + PAVE / 2, rise=KERB_H)
before = set(m.name for m in bpy.data.materials)
outer_flags = lay_cobbles.lay_flags_along(outer_mid, PAVE, seed=4, shades=0.35)
inner_flags = lay_cobbles.lay_flags_along(inner_mid, PAVE, seed=5, shades=0.35)
wet(new_materials(before), 0.7)
dials(new_materials(before), shade=0.25, bump=0.4, normal=1.5, grime=0.5)     # each flag its own, worn, a little relief

# the line the outer walls stand on: just inside the pavement's back edge (each straight stretch cuts a little in)
WALL_AT = KERB_W + PAVE - 0.08
wall_line, _ = lay_cobbles.road_edges(LINE, ROAD, beyond=WALL_AT, rise=KERB_H)
wall_line = numpy.array(wall_line)
along = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(wall_line[:, :2], axis=0), axis=1))])


def wall_point(s):
    """The point on the walls' line `s` metres along it, at the flags' tops there."""
    return numpy.array([numpy.interp(s, along, wall_line[:, k]) for k in range(3)])


_, inner_line = lay_cobbles.road_edges(LINE, ROAD, beyond=WALL_AT + 0.05, rise=KERB_H)
inner_line = numpy.array(inner_line)
inner_along = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(inner_line[:, :2], axis=0), axis=1))])


def inner_point(s):
    return numpy.array([numpy.interp(s, inner_along, inner_line[:, k]) for k in range(3)])


# ----------------------------------------------------------------------------------------------- 3. the walls
def wall_plane(name, s0, s1, height, sink=0.06, inside=False):
    """One flat plane from s0 to s1 along the walls' line (inside: the inside wall's line), its face looking towards
    the road."""
    a, b = (inner_point(s0), inner_point(s1)) if inside else (wall_point(s0), wall_point(s1))
    za, zb = a[2] - sink, b[2] - sink
    verts = [(a[0], a[1], za), (b[0], b[1], zb), (b[0], b[1], zb + height), (a[0], a[1], za + height)]
    mid = (a + b) / 2
    normal = (Vector(verts[1]) - Vector(verts[0])).cross(Vector(verts[3]) - Vector(verts[0]))
    towards_road = Vector((CX - mid[0], CY - mid[1], 0.0))          # the bend's middle is always on the road's side
    if inside:
        towards_road = -towards_road
    if normal.dot(towards_road) < 0:
        verts = [verts[1], verts[0], verts[3], verts[2]]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return obj, a, b, za, zb


def coping(name, a, b, za, zb, height):
    """A stone coping along a stretch's top."""
    d = Vector((b[0] - a[0], b[1] - a[1], zb - za))
    mid = Vector(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (za + zb) / 2 + height + 0.05))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mid)
    cap = bpy.context.object
    cap.name = name
    cap.scale = (d.length + 0.06, 0.36, 0.10)
    cap.rotation_euler = (0.0, -math.atan2(d.z, Vector((d.x, d.y)).length), math.atan2(d.y, d.x))
    store.use_material(cap, 'SURFACE • worn_rock_natural_01')
    return cap


STRETCHES = [                                    # (from, to along the walls' line, kind, bond, atlas, seed, height)
    (12.0, 17.5, 'brick', 'stretcher', None, 7, 2.7),
    (17.5, 22.5, 'brick', 'stretcher', None, 8, 2.7),
    (22.5, 25.5, 'brick', 'stretcher', None, 1, 2.7),
    (25.5, 28.5, 'brick', 'stretcher', None, 2, 2.7),
    (28.5, 31.5, 'brick', 'flemish', 'brick_wall_10', 3, 2.7),
    (31.5, 34.5, 'brick', 'stretcher', None, 4, 2.7),
    (34.5, 37.0, 'stone', None, None, 5, 2.5),
    (37.0, 39.5, 'stone', None, None, 6, 2.5),
]
before = set(m.name for m in bpy.data.materials)
for i, (s0, s1, kind, bond, atlas, seed, height) in enumerate(STRETCHES):
    plane, a, b, za, zb = wall_plane('wall stretch %d' % (i + 1), s0, s1, height)
    if kind == 'brick':
        lay_wall.lay(plane, kind='brick', bond=bond, atlas=atlas, seed=seed)
    else:
        lay_wall.lay(plane, kind='stone', course=0.32, seed=seed)
    coping('coping %d' % (i + 1), a, b, za, zb, height)
WALL_END = STRETCHES[-1][1]
# round the inside of the bend, a low yard wall of the dark brick in short stretches (a tight curve: short chords)
inner_s = [12.0, 15.0, 17.0, 18.2, 19.4, 20.6, 21.8, 23.0, 24.6, 28.0, 33.0]
for i, (s0, s1) in enumerate(zip(inner_s[:-1], inner_s[1:])):
    plane, a, b, za, zb = wall_plane('inside wall %d' % (i + 1), s0, s1, 1.25, inside=True)
    lay_wall.lay(plane, kind='brick', bond='english', atlas='brick_wall_10', seed=20 + i)
    coping('inside coping %d' % (i + 1), a, b, za, zb, 1.25)

# ----------------------------------------------------------------------------------------------- 4. the house and parts
HOUSE_L, HOUSE_D, HOUSE_H = 8.4, 6.0, 7.0
h0 = wall_point(WALL_END)
h1 = wall_point(WALL_END + HOUSE_L)
run = Vector((h1[0] - h0[0], h1[1] - h0[1], 0.0)).normalized()
towards_road = Vector((run.y, -run.x, 0.0))                # the road lies to the right of the run (the bend's inside)
foot = min(h0[2], h1[2]) - 0.12
corner = Vector((h0[0], h0[1], foot)) - towards_road * 0.30            # the front's face stands 0.30 m behind the line
mesh = bpy.data.meshes.new('house')
L, D, H = HOUSE_L, HOUSE_D, HOUSE_H
mesh.from_pydata([(0, 0, 0), (L, 0, 0), (L, D, 0), (0, D, 0), (0, 0, H), (L, 0, H), (L, D, H), (0, D, H)], [],
                 [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
house = bpy.data.objects.new('house', mesh)
scene.collection.objects.link(house)
house.location = corner
house.rotation_euler = (0.0, 0.0, math.atan2(run.y, run.x))
bpy.context.view_layer.update()
stonework = lay_stone.lay(house, openings=[
    ('front', 'door', 1.1, 0.12, 1.0, 2.2),
    ('front', 'window', 3.2, 1.0, 1.1, 1.5),
    ('front', 'window', 5.6, 1.0, 1.1, 1.5),
    ('front', 'window', 1.05, 4.0, 1.1, 1.5),
    ('front', 'window', 3.2, 4.0, 1.1, 1.5),
    ('front', 'window', 5.6, 4.0, 1.1, 1.5),
    ('left', 'window', 2.4, 4.0, 1.0, 1.5),
], sides=['front', 'left'], lit=[1, 3], seed=4)      # timber frames by default; openings 1 and 3 glow
lay_eaves.lay(house, kind='pitched', ridge='front', overhang={'front': 0.42, 'back': 0.42, 'left': 0.3, 'right': 0.3},
              outlets={'front': [0.35]}, seed=2)


def light_window(left_end, bottom, width, height, watts):
    """A small warm light just outside a window lay_stone lit (lit glass glows but lights nothing)."""
    spot = house.matrix_world @ Vector((left_end + width / 2, -0.45, bottom + 0.4))      # low: it lights the sill and the bin
    lamp_obj = bpy.data.objects.new('window light', bpy.data.lights.new('window light', 'POINT'))
    lamp_obj.data.energy = watts
    lamp_obj.data.color = (1.0, 0.62, 0.3)
    lamp_obj.data.shadow_soft_size = 0.4
    lamp_obj.location = spot
    scene.collection.objects.link(lamp_obj)


light_window(3.2, 1.0, 1.1, 1.5, 40.0)
light_window(1.05, 4.0, 1.1, 1.5, 15.0)
ridge = house.matrix_world @ Vector((L - 1.4, D / 2, H + 0.25 + (D / 2 + 0.42) * math.tan(math.radians(36.0)) - 0.3))
store.add_part('chimney_stack', location=ridge, turn=math.degrees(math.atan2(run.y, run.x)), pots=3, stone='brick', seed=2)
# the walls' bricks and blocks a little wet after rain (the BRICK and ASHLAR materials are on these walls only)
since_walls = set(m.name for m in bpy.data.materials) - before
wet([bpy.data.materials[n] for n in since_walls if 'BRICK' in n or 'ASHLAR' in n], 0.25)

# the gas lamp: on the far pavement at the bend, well away from the eye
lamp_s = 30.8                                    # in front of the dark Flemish stretch, so the light falls on both bricks
lp = wall_point(lamp_s)
toward = Vector((CX - lp[0], CY - lp[1], 0.0)).normalized()
lamp_at = Vector((lp[0], lp[1], lp[2])) + toward * (PAVE - 0.55)
gas = store.add_part('gas_lamp', location=lamp_at, turn=math.degrees(math.atan2(toward.y, toward.x)) + 90.0, lit=True, seed=1)


def part_lights(root):
    return [o for o in root.children_recursive if o.type == 'LIGHT']


for light in part_lights(gas):
    light.data.energy = 400.0
# a second lamp out of the frame, on the near inside pavement: its light falls on the near setts (Traps: a lit lamp
# near the eye steals the picture, so this one is never seen, only its light)
near_lamp = store.add_part('gas_lamp', location=(3.95, 0.6, lay_cobbles.top_at(setts, 2.5, 0.6) + KERB_H), turn=90.0, lit=True, seed=2)
for light in part_lights(near_lamp):
    light.data.energy = 200.0

# an ash bin by the house door, a sodden newspaper in the gutter
door_pt = Vector(corner) + run * (1.1 + 0.5 + 1.6) + towards_road * 0.75
bin_z = float(wall_point(WALL_END + 3.2)[2])
store.add_part('ash_bin', location=(door_pt.x, door_pt.y, bin_z), turn=math.degrees(math.atan2(run.y, run.x)) + 8.0, lid='leaning', seed=2)

# ----------------------------------------------------------------------------------------------- 5. the puddles
EYE_XY = (-0.9, 0.2)                             # where the eye (the camera) stands: the puddles are placed from it
lamp_xy = (lamp_at.x, lamp_at.y)


def towards_lamp(f, sideways=0.0):
    """A point a share f of the way from the eye to the lamp, on the ground: where the wet ground mirrors it."""
    dx, dy = lamp_xy[0] - EYE_XY[0], lamp_xy[1] - EYE_XY[1]
    n = math.hypot(dx, dy)
    return EYE_XY[0] + dx * f - dy / n * sideways, EYE_XY[1] + dy * f + dx / n * sideways, math.degrees(math.atan2(dy, dx))


PUDDLES = []      # (x, y, length, width, turn, seed, level below the setts' tops at its middle)
# the long one that mirrors the lamp (Traps: one light, one long puddle). The lamp's head is mirrored a third of the way
# from the eye to the lamp; water nearer the eye than that mirrors the dark sky above the lamp and reads as a hole, so
# the puddle starts there and runs on towards the lamp, mirroring the post and the lit wall behind it.
x, y, heading = towards_lamp(0.30 + 1.6 / math.hypot(lamp_xy[0] - EYE_XY[0], lamp_xy[1] - EYE_XY[1]))
PUDDLES.append((x, y, 3.2, 0.55, heading, 1, 0.001))
x, y, heading = towards_lamp(0.56, 0.3)
PUDDLES.append((x, y, 1.5, 0.45, heading + 8.0, 3, 0.0))
PUDDLES += [(0.5, 10.1, 2.2, 0.45, 50.0, 2, -0.002),    # along the far kerb at the bend, where the crown sheds the water
            (2.1, 3.6, 1.7, 0.5, 86.0, 4, 0.0)]         # by the near kerb on the right
for x, y, length, width_, turn, seed, below in PUDDLES:
    # the water lies flat; a puddle whose level is a little under the setts' tops at its middle leaves the highest
    # stones standing out of it, so it reads as water among setts and not as a hole. A narrow clear rim: a wide one
    # catches the lamp's glow and draws a pale outline round the water
    puddle.make((x, y, 0.0), size=(length, width_), turn=turn, level=lay_cobbles.top_at(setts, x, y) + 0.002 - below,
                seed=seed, raggedness=1.3, shallow_band=0.04)

# a puddle on the inside flags where they mirror the lit window: the same rule, on the pavement (its level from the
# pavement's own middle line, the flags' tops; lay_cobbles.top_at is for the road)
window = house.matrix_world @ Vector((3.2 + 0.55, 0.0, 1.0 + 0.75))
pave = numpy.array(inner_mid)
eye_z = lay_cobbles.top_at(setts, EYE_XY[0], EYE_XY[1]) + 1.62
for _ in range(2):                                   # where the eye's line to the window's mirror image meets the water
    guess = Vector((EYE_XY[0], EYE_XY[1], 0.0)).lerp(Vector((window.x, window.y, 0.0)), 0.45 if _ == 0 else f)
    near = pave[numpy.argmin(numpy.hypot(pave[:, 0] - guess.x, pave[:, 1] - guess.y))]
    level = float(near[2]) + 0.002
    f = (eye_z - level) / ((eye_z - level) + (window.z - level))
mirror = Vector((EYE_XY[0], EYE_XY[1], 0.0)).lerp(Vector((window.x, window.y, 0.0)), f)
sight = (Vector((window.x, window.y, 0.0)) - Vector((EYE_XY[0], EYE_XY[1], 0.0))).normalized()
away_from_kerb = (mirror - Vector((CX, CY, 0.0))).normalized() * -1.0       # towards the bend's middle: off the kerb
centre = mirror + sight * 0.45 + away_from_kerb * 0.2
puddle.make((centre.x, centre.y, 0.0), size=(1.4, 0.5), turn=math.degrees(math.atan2(sight.y, sight.x)), level=level,
            seed=6, raggedness=1.3)

# the newspaper: in the gutter by the kerb, lifted to the setts' tops
# (on the buff flags the grey-buff paper vanished; on the dark setts in the gutter it reads)
paper_at = on_bend(130, 0.0)
paper_dir = Vector((CX - paper_at[0], CY - paper_at[1], 0.0)).normalized()
paper_xy = Vector((paper_at[0], paper_at[1], 0.0)) + paper_dir * (ROAD / 2 - 0.32)       # in the gutter by the inside kerb
store.add_part('newspaper', location=(paper_xy.x, paper_xy.y, lay_cobbles.top_at(setts, paper_xy.x, paper_xy.y) + 0.012),
               turn=70.0, seed=3, kind='sheet')

# ----------------------------------------------------------------------------------------------- 6. weeds in the joints
wheels = lay_cobbles.road_edges(LINE, ROAD, beyond=-(ROAD / 2 - 0.8))


def by_the_kerbs(xy):
    from _lines import Path
    path = Path([Vector(p) for p in LINE])
    _a, across, _ = path.project(xy)
    return (numpy.abs(across) > ROAD / 2 - 0.6).astype(float)


joint_weeds.grow(setts, area=by_the_kerbs, amount=1.2, wheel_lines=[[(p[0], p[1]) for p in w] for w in wheels], seed=4)
joint_weeds.grow([outer_flags, inner_flags], area=None, amount=0.25, kinds=('grass',), seed=6)

# ----------------------------------------------------------------------------------------------- the ground under all
bpy.ops.mesh.primitive_plane_add(size=120.0, location=(10.0, 20.0, -0.35))
under = bpy.context.object
under.name = 'ground under'
store.use_material(under, 'SURFACE • gravel_road')

# ----------------------------------------------------------------------------------------------- sky, lamps, camera
sky_and_haze.sky(scene, strength=0.75, clouds=1.0, low_band=(0.24, 0.15, 0.11), high_band=(0.045, 0.1, 0.12), top=(0.01, 0.03, 0.05))
sky_and_haze.haze(low=(-40, -16, -0.5), high=(60, 80, 26), density=0.003)


def lamp(name, kind, location, energy, colour, size=0.1):
    light = bpy.data.lights.new(name, kind)
    light.energy = energy
    light.color = colour
    if kind == 'AREA':
        light.size = size
    else:
        light.shadow_soft_size = size
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    return obj


lamp('sky fill', 'AREA', (2.0, 8.0, 9.0), 420.0, (0.5, 0.64, 1.0), 12.0)
moon = bpy.data.objects.new('moon fill', bpy.data.lights.new('moon fill', 'SUN'))
moon.data.energy = 0.5
moon.data.color = (0.45, 0.6, 1.0)
moon.rotation_euler = (math.radians(58), 0.0, math.radians(-25))
scene.collection.objects.link(moon)

camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
camera.data.lens = 28
camera.data.shift_y = -0.05
eye = Vector((EYE_XY[0], EYE_XY[1], lay_cobbles.top_at(setts, EYE_XY[0], EYE_XY[1]) + 1.62))   # eye height, in the road
camera.location = eye
camera.rotation_euler = (Vector((7.0, 16.0, 1.6)) - eye).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ----------------------------------------------------------------------------------------------- draw and finish
store.prepare_for_render(scene)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.sample_clamp_indirect = 8
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
if os.environ.get('WHERE'):                      # where each part falls in the frame (0..1 from the bottom left)
    from bpy_extras.object_utils import world_to_camera_view
    for o in scene.objects:
        if o.parent is None and o.type == 'EMPTY':
            v = world_to_camera_view(scene, camera, o.matrix_world.translation)
            print('frame', o.name, round(v.x, 3), round(v.y, 3), round(v.z, 1))
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
raw = os.path.join(os.path.dirname(OUT), 'raw - ' + os.path.splitext(os.path.basename(OUT))[0] + '.exr')
scene.render.filepath = raw
bpy.ops.render.render(write_still=True)
finish.finish(raw, OUT, bloom=1.0, veil=0.3, soften=0.5)
print('drew', OUT)
