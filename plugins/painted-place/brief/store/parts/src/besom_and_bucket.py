"""
besom_and_bucket: a besom broom (a bundle of birch twigs bound twice with wire to an ash pole left in the round)
leaning back against a wall, its twigs on the ground and splayed with use, and a galvanised zinc bucket standing beside
it with mop-water in it and its wire bail dropped to one side: the two things a keeper leaves together by a door. The
wall is at +Y; the bucket stands at the right (+X). Foot at z = 0.

Options:
    bucket   True (default): the bucket beside the broom; False: the broom alone
    seed     the twigs' spread, the bail's drop, the lean

Where it came from: '/home/claude/build-51-chapel/work/render_final.py', besom() (line 470) and bucket() (line 484):
a pole and a cone of 'twigs', a cone bucket with a bar for a bail; rebuilt here twig by twig, with a real bucket.
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

PART = 'besom_and_bucket'
IRON = 'IRON • soot-black lamp posts'
BARK = 'MADE • wet bark'

CARD = {
    'name': PART,
    'what': 'a besom broom (birch twigs wire-bound to a round ash pole) leaning back on a wall at +Y, and a zinc bucket of mop-water '
            'beside it at +X, its bail dropped',
    'size_m': (0.59, 0.53, 1.31),
    'options': {
        'bucket': 'True (default): the bucket stands beside the broom; False: the broom alone',
        'seed': "the twigs' spread, the bail's drop, the lean (default 0)",
    },
    'materials': [BARK, IRON, 'PART • besom_and_bucket: birch twigs', 'PART • besom_and_bucket: dull galvanised steel',
                  'PART • besom_and_bucket: standing water', 'PART • besom_and_bucket: dark worn ash'],
    'source': "'/home/claude/build-51-chapel/work/render_final.py', besom() (line 470) and bucket() (line 484)",
    'views': 'reads from every side; the broom needs the wall it leans on at +Y (alone it leans on air)',
    'trap': 'the broom leans 14 degrees back: its pole top is 0.33 m behind (+Y) its foot, where the wall must be',
}

POLE = 1.35
HEAD = 0.40


def twig_material():
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        grain = shapes.noise_fac(nodes, links, vec, 30.0, detail=3.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.35, 0.65), (0.045, 0.03, 0.024), (0.09, 0.062, 0.05))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.8
        m.diffuse_color = (0.06, 0.045, 0.035, 1.0)
    return shapes.part_material(PART, 'birch twigs', maker)


def water_material():
    def maker(m, nodes, links, principled):
        principled.inputs['Base Color'].default_value = (0.008, 0.01, 0.012, 1.0)
        principled.inputs['Roughness'].default_value = 0.12
        principled.inputs['Specular IOR Level'].default_value = 0.5
        vec = shapes.own_coordinates(nodes)
        ripple = shapes.noise_fac(nodes, links, vec, 25.0, detail=2.0)
        links.new(shapes.bump(nodes, links, ripple, 0.05, 0.001), principled.inputs['Normal'])
        m.diffuse_color = (0.01, 0.012, 0.015, 1.0)
    return shapes.part_material(PART, 'standing water', maker)


def build(collection, seed=0, bucket=True):
    rng = shapes.rng_for(PART, seed)
    objects = []
    twigs_mat = twig_material()
    broom = []

    # ------------------------------------------------------------------ the besom, built upright then leaned
    bx = -0.14 if bucket else 0.0
    foot = Vector((bx, -0.02, 0.0))
    pole = shapes.Shape()
    pole.lathe([(0.0, 0.14), (0.013, 0.14), (0.015, 0.5), (0.014, 1.0), (0.012, POLE - 0.01), (0.0, POLE)], segments=14, phase=0.0,
               matrix=Matrix.Translation(foot))
    broom.append(pole.finish('besom pole', collection, BARK, smooth=True, sharp=50))
    lean = math.radians(14 + rng.uniform(-1.5, 1.5))
    twigs = shapes.Shape()
    bind_z = HEAD - 0.06                 # where the bindings hold the bundle, above the foot
    count = 170
    for k in range(count):
        a = rng.uniform(0, 2 * math.pi)
        r_bind = rng.uniform(0.012, 0.034)
        spread = rng.uniform(0.03, 0.11)
        bend = rng.uniform(-0.03, 0.03)
        top_z = bind_z + rng.uniform(0.04, 0.12)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((-math.sin(a), math.cos(a), 0.0))
        p_top = foot + d * (r_bind * 0.8) + Vector((0, 0, top_z))
        p_bind = foot + d * r_bind + Vector((0, 0, bind_z))
        p_mid = foot + d * (r_bind + (spread - r_bind) * 0.55) + side * bend * 0.5 + Vector((0, 0, bind_z * 0.45))
        p_end = foot + d * spread + side * bend
        p_end.z = rng.uniform(0.0, 0.02) + (p_end.y - foot.y) * math.tan(lean)     # so every end meets the ground once leaned back
        pts = shapes.smooth_path([p_top, p_bind, p_mid, p_end], steps=3)
        radius = rng.uniform(0.0018, 0.003)
        twigs.sweep(pts, radius, sides=4, radii=[radius * (1.0 - 0.5 * i / (len(pts) - 1)) for i in range(len(pts))])
    broom.append(twigs.finish('besom twigs', collection, twigs_mat, smooth=False))
    wire = shapes.Shape()
    for z, r in ((bind_z + 0.015, 0.036), (bind_z - 0.05, 0.042)):
        for dz in (-0.004, 0.0, 0.004):
            wire.torus(foot + Vector((0, 0, z + dz)), r, 0.0016, segments=24, sides=5)
    broom.append(wire.finish('besom bindings', collection, IRON, smooth=True, sharp=50))
    # lean back on the wall, twig ends staying on the ground
    shapes.tilt_all(broom, rx=-lean, rz=math.radians(rng.uniform(-10, 10)), pivot=foot)
    shapes.bake_placement(broom)
    objects += broom

    # ------------------------------------------------------------------ the bucket
    if bucket:
        steel = shapes.galvanised_material(PART)
        centre = Vector((0.16, -0.05, 0.0))
        pail = shapes.Shape()
        prof = [(0.0, 0.0), (0.125, 0.0), (0.13, 0.004), (0.13, 0.012), (0.136, 0.02), (0.158, 0.27), (0.163, 0.28)]
        pail.lathe(prof, segments=40, matrix=Matrix.Translation(centre))
        inner = [(0.161, 0.28), (0.156, 0.27), (0.134, 0.02), (0.0, 0.016)]
        pail.lathe(inner, segments=40, matrix=Matrix.Translation(centre), open_ends=True)
        pail.torus(centre + Vector((0, 0, 0.283)), 0.161, 0.006, segments=40, sides=8)          # rolled rim
        pail.torus(centre + Vector((0, 0, 0.012)), 0.131, 0.005, segments=40, sides=8)          # the foot bead
        pail.torus(centre + Vector((0, 0, 0.17)), 0.149, 0.004, segments=40, sides=6)           # a swaged bead
        for side in (-1, 1):
            pail.box(centre + Vector((side * 0.163, 0.0, 0.245)), (0.012, 0.03, 0.045))
        pail.number_all('board_tone', 0.0)
        objects.append(pail.finish('bucket', collection, steel, smooth=True, sharp=42))
        water = shapes.Shape()
        water.lathe([(0.0, 0.22), (0.153, 0.22)], segments=40, matrix=Matrix.Translation(centre), open_ends=True)
        water_obj = water.finish('bucket water', collection, water_material(), smooth=True)
        water_obj.visible_shadow = False
        objects.append(water_obj)
        # the bail: a wire half ring from ear to ear, dropped to one side, a wooden grip in its middle
        drop = math.radians(rng.choice((-1, 1)) * rng.uniform(55, 80))
        bail = shapes.Shape()
        pts = []
        for k in range(25):
            a = math.pi * k / 24
            p = Vector((-0.175 * math.cos(a), 0.0, 0.17 * math.sin(a)))
            p = Vector((p.x, -math.sin(drop) * p.z, math.cos(drop) * p.z))
            pts.append(centre + p + Vector((0, 0, 0.245)))
        bail.sweep(pts, 0.004, sides=6)
        for side in (-1, 1):
            bail.sphere(centre + Vector((side * 0.176, 0.0, 0.245)), 0.007, segments=8, rings=4)
        objects.append(bail.finish('bucket bail', collection, IRON, smooth=True, sharp=50))
        grip = shapes.Shape()
        along = (pts[13] - pts[11]).normalized()
        grip.lathe([(0.0, -0.045), (0.008, -0.045), (0.011, -0.03), (0.011, 0.03), (0.008, 0.045), (0.0, 0.045)], segments=12,
                   matrix=shapes.to4(shapes.frame_along(along), pts[12]))
        objects.append(grip.finish('bucket grip', collection, shapes.dark_wood(PART), smooth=True, sharp=50))
    return objects
