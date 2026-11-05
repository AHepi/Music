"""
bamboo_broom: a Japanese garden broom (take-boki): a bundle of thin bamboo branches, each with its side twigs, bound
tight to the foot of a bamboo handle and spreading into a broad flat fan, worn straight across its tips where it sweeps;
two bindings of dark cord, one where the branches meet the handle and one lower round the bundle. Leaning back on a
wall or a fence at +Y with its fan on the ground (the fan spread along the wall), or lying flat on the ground.

Options:
    pose   'leaning' (default): leaning back 14 degrees on a wall or fence at +Y, its fan on the ground along X;
           'lying': flat on the ground along X, the fan towards +X
    seed   the branches' spread and bends, the side twigs, each twig's shade, the lean

Where it came from: broom() in '/home/claude/build-57-garden/second pass/render_final.py' (lines 1721-1755: a bamboo
pole with three joint rings, 230 twigs in a fan with side twigs, two bindings, leant on the fence's top rail), rebuilt
with branches that gather into a tight bundle at the binding before they spread, side twigs on each, a fan worn
straight across, and its own lean so it stands on any wall. The store's besom_and_bucket is the English kind (birch
twigs round an ash pole, with a zinc bucket); this is the bamboo one.
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
import _shapes_garden as garden  # noqa: E402

PART = 'bamboo_broom'
POSES = ('leaning', 'lying')
HEAD = 0.55          # the binding's height over the fan's tips
SPREAD = 0.52        # the fan's width at its tips
HANDLE = 1.0         # the handle above the binding

CARD = {
    'name': PART,
    'what': 'a Japanese bamboo garden broom: thin bamboo branches with their side twigs bound to a bamboo handle with dark cord, '
            'spreading into a broad flat fan worn straight across; leaning back on a wall at +Y, or lying flat',
    'size_m': (0.56, 0.42, 1.50),
    'options': {
        'pose': "'leaning' (default): leaning back 14 degrees on a wall or fence at +Y, its fan on the ground along X; 'lying': flat on the ground along X",
        'seed': "the branches' spread and bends, the side twigs, each twig's shade, the lean (default 0)",
    },
    'materials': ['PART • garden: bamboo, weathered', 'PART • garden: dry bamboo twigs', 'PART • garden: dark cord'],
    'source': "broom() in '/home/claude/build-57-garden/second pass/render_final.py' (lines 1721-1755)",
    'views': 'reads from every side; leaning, it needs the wall or fence it leans on at +Y (drawn alone it leans on air); the fan '
             'is broad seen from the front and thin from the side',
    'trap': 'leaning, its handle top rests 0.36 m behind (+Y) its fan, where the wall or the fence rail must be; the twigs are 1 to 3 mm '
            'thick, so from far off the fan reads as a soft brown wedge, and only against something lighter',
}


def build(collection, seed=0, pose='leaning'):
    if pose not in POSES:
        raise ValueError("pose is one of %s, not %r" % (', '.join(repr(k) for k in POSES), pose))
    rng = shapes.rng_for(PART, seed)
    # built standing: the fan's tips on z = 0, spread along X, the handle up the Z axis
    handle = garden.Shape()
    garden.culm(handle, (0.0, 0.0, HEAD - 0.16), (0.0, 0.0, HEAD + HANDLE), 0.0145, rng, node_gap=0.3, taper=0.88)
    twigs = garden.Shape()
    bind = Vector((0.0, 0.0, HEAD))
    count = 230
    for k in range(count):
        u = (k + rng.uniform(-0.4, 0.4)) / (count - 1) * 2 - 1           # -1 .. 1 across the fan
        u = max(-1.0, min(1.0, u))
        v = rng.uniform(-1.0, 1.0)
        twigs.begin()
        root = bind + Vector((u * 0.012, v * 0.01, rng.uniform(0.0, 0.05)))
        tip = Vector((u * SPREAD / 2 + rng.uniform(-0.015, 0.015), v * 0.035 + rng.uniform(-0.01, 0.01), 0.004 + 0.012 * u * u + rng.uniform(0, 0.006)))
        gather = bind + Vector((u * 0.03, v * 0.018, -0.12))             # held in the bundle by the lower binding
        bow = (tip + gather) / 2 + Vector((u * 0.025, v * 0.01, 0.0))
        path = shapes.smooth_path([root, gather, bow, tip], steps=3)
        radii = [0.0026 - 0.0015 * i / (len(path) - 1) for i in range(len(path))]
        twigs.sweep(path, 0.002, sides=4, radii=radii)
        # side twigs off the lower part of each branch, turning outwards and down to the sweeping edge
        for j in range(rng.randint(2, 4)):
            f = rng.uniform(0.45, 0.8)
            i = int(f * (len(path) - 1))
            start = path[i]
            out = Vector((math.copysign(1.0, u + rng.uniform(-0.3, 0.3)) * rng.uniform(0.02, 0.06), rng.uniform(-0.015, 0.015), 0.0))
            end = Vector((start.x + out.x, start.y + out.y, max(0.004, tip.z + rng.uniform(0.0, 0.03))))
            mid = start.lerp(end, 0.5) + out * 0.25
            twigs.sweep([start, mid, end], 0.0014, sides=3, radii=[0.0015, 0.0011, 0.0008])
        twigs.end(rng.random(), 'twig_tone')
    cords = garden.Shape()
    for z in (HEAD - 0.005, HEAD + 0.008, HEAD + 0.021, HEAD + 0.034):
        cords.torus(Vector((0.0, 0.0, z)), 0.019, 0.0035, segments=20, sides=6)
    for z in (HEAD - 0.115, HEAD - 0.127):
        pts = [Vector((0.036 * math.cos(2 * math.pi * j / 24), 0.022 * math.sin(2 * math.pi * j / 24), z)) for j in range(24)]
        cords.sweep(pts, 0.003, sides=6, closed=True)
    # the pose: leaning back on the wall at +Y, the fan on the ground; or lying flat along X
    if pose == 'leaning':
        lean = math.radians(14.0 + rng.uniform(-1.0, 1.0))
        place = Matrix.Rotation(-lean, 4, 'X')
    else:
        place = Matrix.Rotation(math.radians(-90), 4, 'Y') @ Matrix.Rotation(math.radians(90), 4, 'Z')
    for s in (handle, twigs, cords):
        s.transform(place)
    low = min(v.co.z for s in (handle, twigs, cords) for v in s.bm.verts)
    lift = Matrix.Translation((0.0, 0.0, -low))
    if pose == 'lying':
        # flat on the ground: centre it along X
        xs = [v.co.x for v in handle.bm.verts] + [v.co.x for v in twigs.bm.verts]
        lift = Matrix.Translation((-(min(xs) + max(xs)) / 2, 0.0, -low))
    for s in (handle, twigs, cords):
        s.transform(lift)
    made = [handle.finish('%s handle' % PART, collection, garden.bamboo('weathered'), smooth=True, sharp=50.0),
            twigs.finish('%s twigs' % PART, collection, garden.twigs()),
            cords.finish('%s bindings' % PART, collection, garden.cord(), smooth=True)]
    return made
