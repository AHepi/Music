"""
umbrella: a black gentleman's umbrella of about 1900: black cloth over eight steel ribs, a steel shaft, a brass-tipped
ferrule, a bent wooden crook handle. Either furled and leant against a wall (ferrule on the ground, crook up, leaning
back towards +Y where the wall is), or open and dropped on the ground, lying on its rim with the crook on the ground,
wet. Foot at z = 0.

Options:
    pose     'furled standing' (default): furled, leaning back 12 degrees (the wall is at +Y); 'lying open': open,
             lying on its side on the ground, the canopy's top towards -Y
    seed     the furled folds' twist, the lying umbrella's turn

Where it came from: '/home/claude/build-51-chapel/work/render_final.py', umbrella() (line 491): a cone, a shaft and
a crook, and '/home/claude/build-51-chapel/dress/dress_block.py', umbrella_lying() (line 258): the gathered cloth
and crook of beams; rebuilt here with fluted furled cloth, and an open canopy of sagging panels over ribs.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402

PART = 'umbrella'
IRON = 'IRON • soot-black lamp posts'
BRASS = 'MADE • old brass'
POSES = ('furled standing', 'lying open')

CARD = {
    'name': PART,
    'what': 'a black umbrella: furled and leant against a wall (default), or open and dropped on the ground, wet; '
            'black cloth over eight ribs, a wooden crook handle, a brass ferrule',
    'size_m': (0.09, 0.25, 0.96),
    'options': {
        'pose': "'furled standing' (default): furled, leaning back 12 degrees on a wall at +Y; 'lying open': open, lying on the ground, "
                "its top towards -Y",
        'seed': "the folds' twist, the lying umbrella's turn (default 0)",
    },
    'materials': ['PART • umbrella: wet black cloth', 'PART • umbrella: dark worn ash', IRON, BRASS],
    'source': "'/home/claude/build-51-chapel/work/render_final.py', umbrella() (line 491); '/home/claude/build-51-chapel/dress/dress_block.py', "
              "umbrella_lying() (line 258)",
    'views': "reads from every side; furled, it needs the wall it leans on at +Y (drawn alone it leans on air)",
    'trap': "furled, it leans 12 degrees back: its crook is 0.19 m behind (+Y) its foot, where the wall must be; lying open it is 1.3 m across",
}

LENGTH = 0.90          # ferrule tip to the top of the crook's bend
CANOPY_R = 0.50
CANOPY_H = 0.16
RIBS = 8


def crook(shape, top, along, wood):
    """The crook handle: a bent rod from the shaft's top, curving over and back down (an open hook) towards -Y."""
    pts = []
    r = 0.045
    for k in range(13):
        a = math.pi * k / 12
        pts.append(Vector((0.0, -r + r * math.cos(a), r * math.sin(a))))
    pts = [Vector((0.0, -2 * r, -0.025))] + list(reversed(pts)) + [Vector((0.0, 0.0, -0.12))]
    pts = list(reversed(pts))
    frame = shapes.frame_along(along).to_4x4()
    pts = [frame @ p + Vector(top) for p in pts]
    pts = shapes.smooth_path(pts, steps=3)
    shape.sweep(pts, 0.0115, sides=10)
    return pts


def build(collection, seed=0, pose='furled standing'):
    if pose not in POSES:
        raise ValueError("umbrella pose is one of %s, not %r" % (', '.join(repr(s) for s in POSES), pose))
    rng = shapes.rng_for(PART, seed)
    objects = []
    cloth = shapes.black_cloth(PART)
    wood = shapes.dark_wood(PART)

    if pose == 'furled standing':
        twist = rng.uniform(0, 2 * math.pi)
        # the furled cloth: a fluted taper up the shaft, bulging near its top
        furl = shapes.Shape()
        profile = [(0.009, 0.035, 0.0), (0.016, 0.08, 0.2), (0.026, 0.25, 0.3), (0.036, 0.45, 0.32), (0.042, 0.60, 0.3),
                   (0.040, 0.68, 0.25), (0.030, 0.725, 0.15), (0.014, 0.745, 0.0), (0.0, 0.75)]
        furl.lathe(profile, segments=48, flutes=RIBS, phase=twist)
        # the strap round the middle with its button
        furl.torus((0.0, 0.0, 0.52), 0.040, 0.004, segments=32, sides=6)
        furl.box((0.0, -0.045, 0.52), (0.022, 0.006, 0.03))
        furl.number_all('board_tone', 0.0)
        objects.append(furl.finish('umbrella furled cloth', collection, cloth, smooth=True, sharp=70))
        # ferrule, shaft, rib tips showing at the bottom
        metal = shapes.Shape()
        metal.lathe([(0.0, 0.0), (0.0035, 0.0), (0.0055, 0.025), (0.0065, 0.04)], segments=12)
        metal.cylinder((0.0, 0.0, 0.74), (0.0, 0.0, 0.80), 0.0055, segments=10)
        objects.append(metal.finish('umbrella ferrule and shaft', collection, BRASS, smooth=True, sharp=50))
        tips = shapes.Shape()
        for k in range(RIBS):
            a = twist + 2 * math.pi * (k + 0.5) / RIBS
            d = Vector((math.cos(a), math.sin(a), 0.0))
            tips.cylinder(d * 0.006 + Vector((0, 0, 0.03)), d * 0.012 + Vector((0, 0, 0.055)), 0.0018, segments=6)
        objects.append(tips.finish('umbrella rib tips', collection, IRON, smooth=True, sharp=50))
        handle = shapes.Shape()
        crook(handle, (0.0, 0.0, 0.80 + 0.10), (0.0, 0.0, 1.0), wood)
        handle.cylinder((0.0, 0.0, 0.79), (0.0, 0.0, 0.80 + 0.10 - 0.12), 0.0115, segments=10)
        objects.append(handle.finish('umbrella crook', collection, wood, smooth=True, sharp=50))
        # lean back on the wall, the ferrule tip staying on the ground
        shapes.tilt_all(objects, rx=-math.radians(12))
        for obj in objects:
            obj.matrix_world = Matrix.Translation((0.0, 0.0, 0.002)) @ obj.matrix_world
        return objects

    # ------------------------------------------------------------------ open, lying on the ground
    canopy = shapes.Shape()
    rings_out = 10
    segs = RIBS * 8
    rings = []
    for i in range(rings_out + 1):
        f = i / rings_out
        ring = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            sag = math.sin(RIBS / 2 * a) ** 2
            r = f * CANOPY_R * (1.0 - 0.045 * f * sag)
            z = CANOPY_H * (1.0 - f * f) - 0.03 * f * f * sag
            ring.append(Vector((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    verts = [canopy._verts(r) for r in rings[1:]]
    tip = canopy._verts([Vector((0.0, 0.0, CANOPY_H))])
    canopy._rings([tip] + verts, True, False, False)
    canopy_obj = canopy.finish('umbrella canopy', collection, cloth, smooth=True, sharp=None)
    objects.append(canopy_obj)
    frame_parts = shapes.Shape()
    # ribs under the cloth, stretchers from the runner to each rib, the shaft down through the middle
    runner_z = CANOPY_H - 0.30
    for k in range(RIBS):
        a = 2 * math.pi * k / RIBS
        d = Vector((math.cos(a), math.sin(a), 0.0))
        pts = []
        for i in range(rings_out + 1):
            f = i / rings_out
            pts.append(d * (f * CANOPY_R) + Vector((0, 0, CANOPY_H * (1.0 - f * f) - 0.004)))
        pts.append(d * (CANOPY_R + 0.02) + Vector((0, 0, -0.01)))
        frame_parts.sweep(pts, 0.002, sides=5)
        f = 0.5
        frame_parts.cylinder((0.0, 0.0, runner_z), d * (f * CANOPY_R) + Vector((0, 0, CANOPY_H * (1.0 - f * f) - 0.006)), 0.0018, segments=5)
    frame_parts.cylinder((0.0, 0.0, CANOPY_H + 0.03), (0.0, 0.0, CANOPY_H - LENGTH + 0.12 + 0.2), 0.0055, segments=10)
    frame_parts.cylinder((0.0, 0.0, runner_z - 0.025), (0.0, 0.0, runner_z + 0.025), 0.009, segments=10)
    objects.append(frame_parts.finish('umbrella ribs and shaft', collection, IRON, smooth=True, sharp=50))
    ferrule = shapes.Shape()
    ferrule.lathe([(0.0, CANOPY_H + 0.09), (0.0035, CANOPY_H + 0.09), (0.0065, CANOPY_H + 0.04), (0.0065, CANOPY_H + 0.02)], segments=12)
    objects.append(ferrule.finish('umbrella ferrule', collection, BRASS, smooth=True, sharp=50))
    handle = shapes.Shape()
    handle_top = CANOPY_H - LENGTH + 0.12 + 0.2
    crook(handle, (0.0, 0.0, handle_top), (0.0, 0.0, -1.0), wood)
    objects.append(handle.finish('umbrella crook', collection, wood, smooth=True, sharp=50))
    # lay it over: the canopy's top towards -Y, tipped so the rim and the crook meet the ground; a turn about Z
    tip_over = Matrix.Rotation(math.radians(56), 4, 'X')      # the rim and the crook both reach the ground
    turn = Matrix.Rotation(math.radians(rng.uniform(-20, 20)), 4, 'Z')
    for obj in objects:
        obj.matrix_world = turn @ tip_over @ obj.matrix_world
    bpy.context.view_layer.update()
    low = min((obj.matrix_world @ v.co).z for obj in objects for v in obj.data.vertices)
    for obj in objects:
        obj.matrix_world = Matrix.Translation((0.0, 0.0, -low)) @ obj.matrix_world
    shapes.bake_placement(objects)
    return objects
