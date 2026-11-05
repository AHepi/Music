"""
sack_barrow: a grocer's two-wheeled sack truck of about 1900, left leaning back against his shop front: two ash side
rails that are the handles at the top (rubbed pale where they are held), round cross stays, an iron nose plate at the
foot for sliding under a sack, iron straps and a stay to the axle, and two small spoked wheels with iron tyres
behind the rails. It stands on its wheels and its nose plate, leaning back on a wall at +Y.

Options:
    sack     False (default): empty; True: a sack of potatoes stands on its nose plate against the rails
    seed     the lean, the wood's shades, the wheels' turn, the sack's slump

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the grocer's sack barrow (lines 1699-1719):
two leaning cylinders, three rungs, a flat box for the nose plate, two solid discs for wheels, an axle. Rebuilt here
with squared ash rails rounded into grips, mortised stays, a turned-up nose plate with its straps, a stay from each
rail to the axle, and spoked wooden wheels on iron tyres.
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

PART = 'sack_barrow'
IRON = 'IRON • soot-black lamp posts'
RUST = 'RUST • rain-aged iron'
SACKING = 'SURFACE • hessian_380'

CARD = {
    'name': PART,
    'what': "a grocer's sack truck: two ash rails ending in grips, round stays, an iron nose plate, two small iron-tyred spoked "
            'wheels behind; leaning back on a wall at +Y on its wheels and nose plate',
    'size_m': (0.62, 0.62, 1.22),
    'options': {
        'sack': 'False (default): empty; True: a sack of potatoes stands on the nose plate against the rails',
        'seed': "the lean, the wood's shades, the wheels' turn, the sack's slump (default 0)",
    },
    'materials': ['SURFACE • rough_wood (sack_barrow)', 'PART • sack_barrow: ash, rubbed pale where held', IRON, RUST, SACKING + ' (sack_barrow)'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the grocer's sack barrow (lines 1699-1719)",
    'views': 'reads from every side; it needs the wall it leans on at +Y (drawn alone it leans on air)',
    'trap': 'it leans 17 degrees back: its grips touch the wall about 0.42 m behind (+Y) the origin (the nose plate\'s back edge); '
            'put that plane on your wall face',
}

LEAN = math.radians(17.0)
RAIL = 1.22                 # rail length, nose plate to grip
WHEEL_R = 0.14


def grip_material():
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        stretch = nodes.new('ShaderNodeMapping')
        stretch.inputs['Scale'].default_value = (40.0, 40.0, 1.6)
        links.new(vec, stretch.inputs['Vector'])
        grain = shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 1.0, detail=5.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.35, 0.65), (0.15, 0.115, 0.075), (0.23, 0.18, 0.12))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.42
        links.new(shapes.bump(nodes, links, grain, 0.2, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.18, 0.14, 0.09, 1.0)
    return shapes.part_material(PART, 'ash, rubbed pale where held', maker)


def build(collection, seed=0, sack=False):
    if not isinstance(sack, bool):
        raise ValueError('sack_barrow sack is True or False, not %r' % (sack,))
    rng = shapes.rng_for(PART, seed)
    lean = LEAN + rng.uniform(-0.015, 0.015)
    up = Vector((0.0, math.sin(lean), math.cos(lean)))             # along the rails, up and back
    out = Vector((0.0, -math.cos(lean), math.sin(lean)))           # square to the rails, towards the front
    wood = shapes.surface_copy('rough_wood', PART, Grime=0.5, Darken=0.45)
    objects = []
    foot = Vector((0.0, 0.0, 0.035))                                # the rails' foot, just over the nose plate

    def timber(name, a, b, w, h, material=None, **kw):
        obj = shapes.timber(collection, 'sack_barrow %s' % name, a, b, w, h, material or wood, rng=rng, shift=0.3, up=out, **kw)
        objects.append(obj)
        return obj

    # ------------------------------------------------------------------ rails, stays
    tops = {}
    for side in (-1, 1):
        a = foot + Vector((side * 0.19, 0.0, 0.0))
        b = foot + Vector((side * 0.165, 0.0, 0.0)) + up * (RAIL - 0.16)
        timber('rail %s' % ('left' if side < 0 else 'right'), a, b, 0.038, 0.048, chamfer=0.006)
        # the grip: the rail's end turned round, bent a little back
        grip = shapes.Shape()
        g0 = b + up * 0.0
        g1 = b + up * 0.17 + out * -0.02
        grip.lathe([(0.0, 0.0), (0.02, 0.0), (0.019, 0.03), (0.017, 0.13), (0.019, 0.16), (0.0, 0.17)], segments=12,
                   matrix=shapes.to4(shapes.frame_along(g1 - g0), g0))
        objects.append(grip.finish('sack_barrow grip %s' % ('left' if side < 0 else 'right'), collection, grip_material(), smooth=True, sharp=50))
        tops[side] = b
    for t in (0.3, 0.52, 0.74, 0.94):
        z_off = up * (RAIL - 0.16) * t
        half = 0.19 - 0.025 * t
        stay = shapes.Shape()
        stay.cylinder(foot + z_off + Vector((-half - 0.012, 0, 0)), foot + z_off + Vector((half + 0.012, 0, 0)), 0.014, segments=10)
        objects.append(stay.finish('sack_barrow stay %.2f' % t, collection, wood, smooth=True, sharp=50))

    # ------------------------------------------------------------------ the nose plate and its straps
    iron = shapes.Shape()
    iron.box((0.0, -0.085, 0.004), (0.44, 0.19, 0.008))                       # the plate, on the ground in front of the rails
    iron.box((0.0, -0.178, 0.008), (0.44, 0.008, 0.012))                      # its front edge turned down a little
    for side in (-1, 1):
        a = foot + Vector((side * 0.19, 0.0, 0.0)) + out * 0.026
        iron.beam(Vector((side * 0.19, 0.0, 0.006)), a + up * 0.32, 0.042, 0.006, up=out)   # strap up the rail's front
        for k in (0.08, 0.2, 0.3):
            iron.sphere(a + up * k + out * 0.005, 0.006, segments=8, rings=4)
    objects.append(iron.finish('sack_barrow nose plate', collection, RUST, smooth=False))

    # ------------------------------------------------------------------ axle, stays to it, wheels
    axle_y = foot.y + 0.13
    axle = Vector((0.0, axle_y + (WHEEL_R - foot.z) * math.tan(lean) * 0.0, WHEEL_R))
    bar = shapes.Shape()
    bar.cylinder(axle + Vector((-0.30, 0, 0)), axle + Vector((0.30, 0, 0)), 0.012, segments=10)
    for side in (-1, 1):
        on_rail = foot + Vector((side * 0.188, 0.0, 0.0)) + up * 0.36 + out * -0.024
        bar.beam(on_rail, axle + Vector((side * 0.188, 0.0, 0.0)), 0.012, 0.03, up=Vector((1, 0, 0)))
        low_rail = foot + Vector((side * 0.19, 0.0, 0.0)) + up * 0.08 + out * -0.024
        bar.beam(low_rail, axle + Vector((side * 0.19, 0.0, 0.0)), 0.012, 0.03, up=Vector((1, 0, 0)))
    objects.append(bar.finish('sack_barrow axle and stays', collection, IRON, smooth=False))
    for side in (-1, 1):
        objects += shapes.spoked_wheel(collection, 'sack_barrow wheel %s' % ('left' if side < 0 else 'right'),
                                       axle + Vector((side * 0.265, 0.0, 0.0)), (1.0, 0.0, 0.0), WHEEL_R, 8, wood, IRON, rng,
                                       hub_radius=0.03, hub_length=0.07, spoke_width=0.017, felloe_depth=0.026, felloe_width=0.03, tyre=0.006)

    # ------------------------------------------------------------------ the sack
    if sack:
        bag = shapes.Shape()
        h = 0.62
        prof = []
        for k in range(11):
            t = k / 10
            r = 0.17 * (1.0 + 0.18 * math.sin(math.pi * t * 0.9)) * (1.0 - 0.55 * max(0.0, t - 0.8) / 0.2)
            prof.append((r, 0.008 + h * t))
        prof = [(0.0, 0.008)] + prof + [(0.0, h + 0.02)]
        bag.lathe(prof, segments=18)
        from mathutils import noise as mnoise
        salt = Vector((rng.uniform(0, 50), rng.uniform(0, 50), 0.0))
        for v in bag.bm.verts:
            n = mnoise.noise(v.co * 8.0 + salt)
            v.co.x *= 1.0 + 0.08 * n
            v.co.y *= 1.0 + 0.08 * n
        # stood on the plate, leaning back on the rails
        bag.transform(Matrix.Translation((0.0, -0.215, 0.0)) @ Matrix.Rotation(-lean * 0.8, 4, 'X'))
        for v in bag.bm.verts:
            if v.co.z < 0.008:
                v.co.z = 0.008                        # its foot slumped flat on the plate
        objects.append(bag.finish('sack_barrow sack', collection, shapes.surface_copy(SACKING, PART, Grime=0.5), smooth=True, sharp=None))
    return objects
