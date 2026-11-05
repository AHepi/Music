"""
hanging_lantern: a lantern that hangs from an eave or a bracket on an iron chain from a hook. Three kinds: a square
lantern framed in dark timber with a lattice over paper panes, a flared copper roof and a ring on top (the inn's
veranda lantern); the same frame glazed, a candle burning inside; or a round paper lantern (chochin) of paper on
bamboo ribs between black lacquered rims, hung by a wire bail. Lit, it glows warm and a small hidden light inside
lights the eave, the posts and the ground under it.

Its origin is the lantern's foot, and the hook is 0.8 m above it whichever kind it is: to hang it from an eave or a
bracket whose underside is at height H, put the origin at H - 0.8.

Options:
    kind   'box' (default): the square timber-framed lantern with paper panes behind a lattice and a copper roof;
           'glass': the same frame glazed, a candle inside; 'round': a round paper lantern on bamboo ribs
    lit    (default True) glowing warm with a hidden 22 W light inside; False: cold paper or dark glass, no light
    glow   (default 1.0) how brightly it glows, lit: its light is 22 W times glow, and its paper (or the glazed kind's
           candle) glows glow times the square root of glow as brightly, so turned down it dims faster than the light it
           throws; 0.25 (a 5.5 W light, the paper at an eighth) for a lantern near the eye, as the third garden builder
           found; 0.05 to 3
    seed   the chain's twist, a slight swing, the paper's stains

Where it came from: hanging_lantern() in '/home/claude/build-57-garden/first pass/render_final.py' (line 886), kept in
'/home/claude/build-57-garden/second pass/render_final.py' (lines 929-966: four corner posts, three rings of rails,
a pyramid cap, a chain of short rods, glowing paper panes with no shadow, a point light inside), and the round paper
lanterns of the board's photograph 11. Rebuilt with a real chain of links, a lattice over the paper, a flared roof
with a ring, a bottom tray, and the glazed and round kinds.
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

PART = 'hanging_lantern'
KINDS = ('box', 'glass', 'round')
DROP = 0.8              # hook to foot, every kind
IRON = 'IRON • soot-black lamp posts'
COPPER = 'MADE • old copper'

CARD = {
    'name': PART,
    'what': 'a hanging lantern on an iron chain from a hook: a square timber-framed lantern with a lattice over paper panes and a '
            'flared copper roof, the same frame glazed with a candle, or a round paper lantern on bamboo ribs; lit warm or dark',
    'size_m': (0.36, 0.36, 0.80),
    'options': {
        'kind': "'box' (default): timber frame, lattice, paper panes, copper roof; 'glass': the same frame glazed, a candle inside; "
                "'round': a round paper lantern on bamboo ribs between black rims",
        'lit': 'True (default): glowing warm, a hidden 22 W light inside; False: cold paper or dark glass, no light',
        'glow': 'how brightly it glows, lit: its light is 22 W times glow, and its paper dims faster than its light (default 1.0; '
                '0.25 for a lantern near the eye, whose full glow draws its panes white and blows out the warm light: a quarter of the '
                'light, the paper at an eighth; 0.05 to 3)',
        'seed': "the chain's twist, a slight swing, the paper's stains (default 0)",
    },
    'materials': [IRON, COPPER, 'SURFACE • rough_wood (hanging_lantern)', 'PART • garden: lantern paper, lit', 'PART • garden: lantern paper',
                  'PART • hanging_lantern: glass', 'PART • hanging_lantern: black lacquer', 'PART • hanging_lantern: candle flame'],
    'source': "hanging_lantern() in '/home/claude/build-57-garden/first pass/render_final.py' (line 886), kept in "
              "'/home/claude/build-57-garden/second pass/render_final.py' (lines 929-966); the round paper lanterns of the board's photograph 11; "
              "the glow option from '/home/claude/build-57-garden/closer/render_final.py' (lines 987-1019), where the builder turned a near "
              "lantern's light to a quarter and its paper to an eighth by hand",
    'views': 'reads from every side; drawn alone it hangs in the air, as it needs an eave or a bracket above it',
    'trap': "the hook is 0.8 m above the origin (the lantern's foot): to hang it from an eave whose underside is at height H, put the origin at H - 0.8. "
            "Lit, the light is the part's own (the object 'hanging_lantern light'): a row of them adds up, so give each glow=0.5 or less; "
            "near the eye (a few metres) its full glow passes the look's warm-light band: give glow=0.25",
}


def glass():
    def maker(m, nodes, links, p):
        p.inputs['Base Color'].default_value = (0.8, 0.62, 0.4, 1.0)
        p.inputs['Roughness'].default_value = 0.12
        p.inputs['Transmission Weight'].default_value = 0.92
        p.inputs['IOR'].default_value = 1.5
        vec = shapes.own_coordinates(nodes)
        links.new(shapes.bump(nodes, links, shapes.noise_fac(nodes, links, vec, 30.0, detail=2.0), 0.15, 0.001), p.inputs['Normal'])
        m.diffuse_color = (0.6, 0.5, 0.35, 1.0)
    return shapes.part_material(PART, 'glass', maker)


def lacquer():
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        wear = shapes.noise_fac(nodes, links, vec, 25.0, detail=4.0)
        links.new(shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, wear, 0.62, 0.7), (0.012, 0.01, 0.01), (0.08, 0.035, 0.02)), p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.25
        p.inputs['Coat Weight'].default_value = 0.4
        m.diffuse_color = (0.015, 0.012, 0.012, 1.0)
    return shapes.part_material(PART, 'black lacquer', maker)


def flame(glow=1.0):
    def maker(m, nodes, links, p):
        p.inputs['Base Color'].default_value = (1.0, 0.7, 0.35, 1.0)
        p.inputs['Emission Color'].default_value = (1.0, 0.6, 0.25, 1.0)
        p.inputs['Emission Strength'].default_value = 25.0
        m.diffuse_color = (1.0, 0.7, 0.35, 1.0)
    return _dimmed(shapes.part_material(PART, 'candle flame', maker), glow)


def _dimmed(material, glow):
    """The material itself at glow 1; otherwise its own copy ('<name>, glow 0.25'), every glowing strength in it
    times glow ** 1.5 (the third garden builder's near lantern: light at a quarter, paper at an eighth)."""
    if abs(glow - 1.0) < 1e-6:
        return material
    name = '%s, glow %s' % (material.name, ('%.3f' % glow).rstrip('0').rstrip('.'))
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    copy = material.copy()
    copy.name = name
    factor = glow ** 1.5
    for n in copy.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Emission Strength'].default_value *= factor
        elif n.type == 'EMISSION':
            n.inputs['Strength'].default_value *= factor
    return copy


def chain(shape, top, bottom, rng):
    """Oval iron links from top down to bottom, each turned a quarter to the last."""
    length, width, wire = 0.034, 0.017, 0.0028
    z = top - wire
    k = 0
    twist = rng.uniform(0, math.pi)
    while z - length > bottom - 0.004:
        c = Vector((0.0, 0.0, z - length / 2))
        a = twist + (math.pi / 2) * (k % 2)
        pts = []
        for j in range(16):
            t = 2 * math.pi * j / 16
            pts.append(c + Vector((math.cos(a) * (width / 2 - wire) * math.cos(t), math.sin(a) * (width / 2 - wire) * math.cos(t), (length / 2 - wire) * math.sin(t))))
        shape.sweep(pts, wire, sides=6, closed=True)
        z -= length - 2.2 * wire
        k += 1
    return z


def hook(shape):
    """A plate screwed under the eave and an iron eye from it."""
    shape.box((0.0, 0.0, -0.004), (0.05, 0.05, 0.008))
    shape.torus(Vector((0.0, 0.0, -0.022)), 0.011, 0.0035, axis=Vector((1.0, 0.0, 0.0)), segments=16, sides=6)
    shape.cylinder((0.0, 0.0, -0.008), (0.0, 0.0, -0.012), 0.004, segments=6)


def box_lantern(collection, rng, kind, lit, made, glow=1.0):
    w, h = 0.11, 0.32                          # half width, body height
    z0 = -DROP + 0.025                         # the body's foot, over the tray
    z1 = z0 + h
    wood = shapes.surface_copy('SURFACE • rough_wood', PART, Darken=0.38, Grime=0.6)
    frame = garden.Shape()
    post = 0.018
    for sx in (-1, 1):
        for sy in (-1, 1):
            frame.box((sx * (w - post / 2), sy * (w - post / 2), (z0 + z1) / 2), (post, post, h))
    for zz, t in ((z0 + 0.012, 0.024), (z1 - 0.012, 0.024), (z0 + h * 0.58, 0.012)):
        for s in (-1, 1):
            frame.box((s * (w - post / 2), 0.0, zz), (post, 2 * w, t))
            frame.box((0.0, s * (w - post / 2), zz), (2 * w, post, t))
    # the lattice over the panes: two uprights and three bars a side, thin, just outside the panes
    bar = 0.006
    for s in (-1, 1):
        for u in (-w / 3, w / 3):
            frame.box((u, s * (w - 0.006), (z0 + z1) / 2), (bar, bar, h - 0.03))
            frame.box((s * (w - 0.006), u, (z0 + z1) / 2), (bar, bar, h - 0.03))
        for f in (0.24, 0.42, 0.78):
            zz = z0 + h * f
            frame.box((0.0, s * (w - 0.006), zz), (2 * w - 0.02, bar, bar))
            frame.box((s * (w - 0.006), 0.0, zz), (bar, 2 * w - 0.02, bar))
    # the tray under it, a little wider, on four short feet
    frame.box((0.0, 0.0, z0 - 0.008), (2 * w + 0.04, 2 * w + 0.04, 0.016))
    for sx in (-1, 1):
        for sy in (-1, 1):
            frame.box((sx * (w + 0.004), sy * (w + 0.004), -DROP + 0.0045), (0.022, 0.022, 0.009))
    made.append(frame.finish('%s frame' % PART, collection, wood, chamfer=0.0015))
    # the panes: paper or glass, all four sides, just inside the frame
    panes = garden.Shape()
    for s in (-1, 1):
        y = s * (w - 0.012)
        panes.poly([(-w + 0.012, y, z0 + 0.02), (w - 0.012, y, z0 + 0.02), (w - 0.012, y, z1 - 0.02), (-w + 0.012, y, z1 - 0.02)])
        panes.poly([(y, -w + 0.012, z0 + 0.02), (y, w - 0.012, z0 + 0.02), (y, w - 0.012, z1 - 0.02), (y, -w + 0.012, z1 - 0.02)])
    pane_mat = _dimmed(garden.paper(lit), glow) if kind == 'box' else glass()
    obj = panes.finish('%s panes' % PART, collection, pane_mat)
    obj.visible_shadow = False
    made.append(obj)
    if kind == 'glass':
        candle = garden.Shape()
        candle.cylinder((0.0, 0.0, z0), (0.0, 0.0, z0 + 0.09), 0.018, segments=14)
        made.append(candle.finish('%s candle' % PART, collection, garden.paper(False), smooth=True))
        if lit:
            fl = garden.Shape()
            fl.lathe([(0.0, z0 + 0.093), (0.006, z0 + 0.1), (0.0045, z0 + 0.115), (0.0, z0 + 0.128)], segments=10)
            f = fl.finish('%s flame' % PART, collection, flame(glow), smooth=True)
            f.visible_shadow = False
            made.append(f)
    # the roof: four flared slopes in copper, the eave turned up a little, a ring on top
    roof = garden.Shape()
    r_edge, r_top, rise = 0.155, 0.03, 0.085
    rings = []
    for u in (0.0, 0.08, 0.2, 0.36, 0.55, 0.75, 1.0):
        half = r_edge * (1 - u) + r_top * u
        zz = z1 + 0.012 + rise * (u ** 1.8) + 0.012 * (1 - u) ** 3
        rings.append([Vector((x * half, y * half, zz)) for (x, y) in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    under = [Vector((x * (w + 0.005), y * (w + 0.005), z1)) for (x, y) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    lip = [p - Vector((0, 0, 0.012)) for p in rings[0]]
    roof._rings([roof._verts(under), roof._verts(lip)] + [roof._verts(r) for r in rings], True, True, True)
    top = z1 + 0.012 + rise
    roof.cylinder((0.0, 0.0, top - 0.004), (0.0, 0.0, top + 0.012), 0.016, segments=12)
    made.append(roof.finish('%s roof' % PART, collection, COPPER, smooth=True, sharp=40.0))
    ring_top = top + 0.012 + 0.03
    irons = garden.Shape()
    irons.torus(Vector((0.0, 0.0, top + 0.012 + 0.014)), 0.012, 0.0035, axis=Vector((0.0, 1.0, 0.0)), segments=16, sides=6)
    return irons, ring_top, (0.0, 0.0, (z0 + z1) / 2 + (0.03 if kind == 'glass' else 0.0))


def round_lantern(collection, rng, lit, made, glow=1.0):
    """A chochin: paper on bamboo ribs (the ridges every 2 cm), black lacquered rims, a wire bail."""
    bottom = -DROP
    rim = 0.03
    body0, body1 = bottom + rim, bottom + rim + 0.34
    centre = (body0 + body1) / 2
    half = (body1 - body0) / 2
    profile = []
    n = 34
    for k in range(n + 1):
        t = -1.0 + 2.0 * k / n
        r = 0.135 * math.sqrt(max(0.0, 1.0 - (t * 0.93) ** 2))
        r = max(r, 0.072)
        r *= 1.0 if k % 2 else 0.975              # the ribs stand out, the paper sinks a little between them
        profile.append((r, centre + half * t))
    paper = garden.Shape()
    paper.lathe(profile, segments=40, open_ends=True)
    obj = paper.finish('%s paper' % PART, collection, _dimmed(garden.paper(lit), glow), smooth=True)
    obj.visible_shadow = False
    made.append(obj)
    caps = garden.Shape()
    caps.lathe([(0.0, bottom), (0.07, bottom), (0.078, bottom + 0.006), (0.078, body0 + 0.006), (0.0, body0 + 0.006)], segments=32)
    caps.lathe([(0.0, body1 - 0.006), (0.078, body1 - 0.006), (0.078, body1 + rim - 0.006), (0.07, body1 + rim), (0.0, body1 + rim)], segments=32)
    made.append(caps.finish('%s rims' % PART, collection, lacquer(), smooth=True, sharp=40.0))
    irons = garden.Shape()
    top = body1 + rim
    # the bail: a wire loop from the rim's two sides up to a small eye
    pts = [Vector((-0.06, 0.0, top - 0.004)), Vector((-0.045, 0.0, top + 0.03)), Vector((-0.012, 0.0, top + 0.055)), Vector((0.0, 0.0, top + 0.058)),
           Vector((0.012, 0.0, top + 0.055)), Vector((0.045, 0.0, top + 0.03)), Vector((0.06, 0.0, top - 0.004))]
    irons.sweep(shapes.smooth_path(pts, steps=4), 0.0025, sides=6)
    irons.torus(Vector((0.0, 0.0, top + 0.068)), 0.009, 0.0028, axis=Vector((0.0, 1.0, 0.0)), segments=14, sides=6)
    return irons, top + 0.077, (0.0, 0.0, centre)


def build(collection, seed=0, kind='box', lit=True, glow=1.0):
    if kind not in KINDS:
        raise ValueError("kind is one of %s, not %r" % (', '.join(repr(k) for k in KINDS), kind))
    try:
        glow = float(glow)
    except (TypeError, ValueError):
        raise ValueError('hanging_lantern glow is a number, not %r' % (glow,))
    if not 0.05 <= glow <= 3.0:
        raise ValueError('hanging_lantern glow is 0.05 to 3 (1 its own, 0.25 near the eye), not %r' % (glow,))
    rng = shapes.rng_for(PART, seed)
    made = []
    shine = glow if lit else 1.0                # unlit, nothing glows to turn down
    if kind == 'round':
        irons, ring_top, light_at = round_lantern(collection, rng, lit, made, shine)
    else:
        irons, ring_top, light_at = box_lantern(collection, rng, kind, lit, made, shine)
    hook(irons)
    chain(irons, -0.026, ring_top - 0.004, rng)
    made.append(irons.finish('%s chain' % PART, collection, IRON, smooth=True))
    # a slight swing about the hook, the same for every piece
    swing = Matrix.Rotation(rng.uniform(-0.02, 0.02), 4, 'X') @ Matrix.Rotation(rng.uniform(-0.02, 0.02), 4, 'Y') @ Matrix.Rotation(rng.uniform(-0.3, 0.3), 4, 'Z')
    # everything was built hanging below the hook at z = 0: lift it so the foot is on z = 0
    place = Matrix.Translation((0.0, 0.0, DROP)) @ swing
    for obj in made:
        obj.data.transform(place)
    if lit:
        made.append(garden.hidden_light(collection, '%s light' % PART, place @ Vector(light_at), 22.0 * glow, (1.0, 0.55, 0.22), 0.04))
    return made
