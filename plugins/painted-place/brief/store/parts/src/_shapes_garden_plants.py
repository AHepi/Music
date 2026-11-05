"""
What this file is: shape and material helpers shared by the garden's bridge and plant parts (arched_bridge, maple_tree,
garden_pine, fern, bamboo_clump). It is not a part (its name starts with '_', so the store does not list it). It builds
on the chapel helpers (_shapes_chapel.py: Shape, rng_for, smooth_path, part_material and the node helpers).

    tagged(shape, lambda: shape.box(...), piece=0.37, pp_bare=lambda co: 1.0)
        adds one piece to a shape and writes its numbers: 'pp_piece' on its faces (so a photographed material shows
        each piece its own part of the photograph) and any point numbers given as functions of the point's place.
    leaf(shape, centre, frame, size, outline, tone, cup=0.0, curl=0.0)
        one flat leaf as a single face from an outline [(x, y), ...] (base at (0, 0), tip towards +y), set in a frame
        (a 3x3 rotation: its x across the leaf, y along it, z out of its upper side); writes 'tone' on the face and the
        outline itself in the UV map 'leaf' (for the veins).
    maple_outline(), bamboo_outline(), pinna_outline(lobes)
        real leaf outlines: a Japanese maple's seven toothed lobes (broad, cut to about half way, so they do not read as
        stars), a bamboo leaf's narrow blade, a fern pinna's lobed edge.

Materials: leaf_material (made: tone ramp, veins, see-through), culm_material and sheath_material (bamboo), needle and
pad materials (pine), bronze_material (the bridge's caps), plain_material, surface(name, part, what, **dials) (a copy
of a photographed SURFACE material for one job), bark(part, ...) (the shelf's photographed bark), painted_wood(part,
...) (the shelf's photographed planks with old paint laid over them, worn to the wood where the number 'pp_bare' says).
The shelf has no photographed leaves, needles or bamboo, so those are made in code; everything else is photographed.
"""

import math

import bpy
from mathutils import Matrix, Vector

import _shapes_chapel as shapes
import store

UP = Vector((0.0, 0.0, 1.0))


# ---------------------------------------------------------------------------------------------- numbers on pieces

def tagged(shape, make, piece=None, **point_numbers):
    """Add one piece to `shape` with make() and write its numbers: 'pp_piece' (one value on all its faces) and, for each
    name=function given, a point number from each new point's place, function((x, y, z)) -> value."""
    bm = shape.bm
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    v0, f0 = len(bm.verts), len(bm.faces)
    result = make()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    if piece is not None:
        layer = bm.faces.layers.float.get('pp_piece') or bm.faces.layers.float.new('pp_piece')
        for f in bm.faces[f0:]:
            f[layer] = float(piece)
    for name, function in point_numbers.items():
        layer = bm.verts.layers.float.get(name) or bm.verts.layers.float.new(name)
        for v in bm.verts[v0:]:
            v[layer] = float(function(tuple(v.co)))
    return result


def face_number(shape, name, value, first_face):
    """Write one number on every face added since `first_face` (a count of faces taken before adding them)."""
    bm = shape.bm
    bm.faces.ensure_lookup_table()
    layer = bm.faces.layers.float.get(name) or bm.faces.layers.float.new(name)
    for f in bm.faces[first_face:]:
        f[layer] = float(value)


# ---------------------------------------------------------------------------------------------- leaves

def maple_outline(lobes=7, depth=0.6, teeth=True):
    """A Japanese maple leaf's outline, base (where the stalk joins) at (0, 0), the middle lobe towards +y, about 1.0
    long: `lobes` lobes fanned over 300 degrees, the middle ones longest, each broad (widest a little past half way
    out, nearly touching its neighbours there) with a pointed tip, cut `depth` of the way in, the edges toothed. Points
    run anticlockwise seen from the leaf's upper side (+z)."""
    span = 150.0
    spacing = 2 * span / (lobes - 1)
    half = spacing * 0.48
    side = [(0.52, half * 0.95), (0.72, half * 0.68), (0.88, half * 0.3)]
    polar = []
    for k in range(lobes):
        a = -span + spacing * k
        reach = 0.42 + 0.58 * max(0.0, math.cos(math.radians(a) * 0.6)) ** 1.6      # middle lobe 1.0, the two at the base small
        if k > 0:
            polar.append((a - spacing / 2, reach * (1.0 - depth)))
        for j, (f, w) in enumerate(side):
            polar.append((a - w, reach * (f + (0.035 if teeth and j == 1 else 0.0))))
        polar.append((a, reach))
        for j, (f, w) in reversed(list(enumerate(side))):
            polar.append((a + w, reach * (f + (0.035 if teeth and j == 1 else 0.0))))
    pts = [(0.0, -0.05)] + [(r * math.sin(math.radians(a)), r * math.cos(math.radians(a))) for a, r in polar]
    # laid from -150 degrees (lower left) over the top to +150 (lower right): clockwise seen from +z, so turn it round
    pts.reverse()
    return pts


def bamboo_outline(points=5):
    """A bamboo leaf: a narrow blade 1.0 long and 0.13 wide, widest a quarter of the way up, a long fine tip, a short
    rounded base; base at (0, 0), tip at (0, 1)."""
    right, left = [], []
    for k in range(1, points + 1):
        t = k / (points + 1)
        w = 0.065 * math.sin(math.pi * min(1.0, t ** 0.75)) * (1.0 - 0.25 * t)
        right.append((w, t))
        left.append((-w, t))
    return [(0.0, 0.0)] + right + [(0.0, 1.0)] + list(reversed(left))


def pinna_outline(lobes=6):
    """A fern pinna: a narrow blade 1.0 long, 0.24 wide, with `lobes` rounded pinnules down each side, base at (0, 0),
    tip at (0, 1)."""
    right, left = [], []
    for k in range(lobes):
        t0 = (k + 0.15) / (lobes + 0.4)
        t1 = (k + 0.65) / (lobes + 0.4)
        width = 0.12 * (1.0 - 0.75 * ((k + 0.5) / lobes) ** 1.3)
        right += [(width * 0.45, t0), (width, t1)]
        left += [(-width * 0.45, t0), (-width, t1)]
    return [(0.0, 0.0)] + right + [(0.0, 1.0)] + list(reversed(left))


def frame_from(along, up_hint):
    """A 3x3 rotation for a leaf: its y along `along`, its z (the upper side) as near `up_hint` as the leaf allows."""
    y = Vector(along).normalized()
    z = Vector(up_hint) - y * Vector(up_hint).dot(y)
    if z.length < 1e-6:
        z = Vector((1.0, 0.0, 0.0)) - y * y.x
    z.normalize()
    x = y.cross(z).normalized()
    return Matrix((x, y, z)).transposed()


def leaf(shape, centre, frame, size, outline, tone, cup=0.0, curl=0.0, width=1.0):
    """One leaf as a single face. `cup` lifts its edges (a fraction of its size: a cupped maple leaf), `curl` bends it
    down along its length (a drooping bamboo leaf); `width` stretches it across. Returns the face."""
    bm = shape.bm
    tone_layer = bm.faces.layers.float.get('tone') or bm.faces.layers.float.new('tone')
    uv_layer = bm.loops.layers.uv.get('leaf') or bm.loops.layers.uv.new('leaf')
    c = Vector(centre)
    verts = []
    for (x, y) in outline:
        r2 = x * x + y * y
        z = cup * r2 - curl * y * y
        verts.append(bm.verts.new(c + frame @ (Vector((x * width, y, z)) * size)))
    try:
        face = bm.faces.new(verts)
    except ValueError:
        return None
    face.material_index = shape.material_index
    face[tone_layer] = float(tone)
    for loop, (x, y) in zip(face.loops, outline):
        loop[uv_layer].uv = (x, y)
    return face


# ---------------------------------------------------------------------------------------------- made materials

def _ramp(nodes, links, fac, stops):
    ramp = nodes.new('ShaderNodeValToRGB')
    elements = ramp.color_ramp.elements
    while len(elements) > len(stops):
        elements.remove(elements[-1])
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, (position, colour) in zip(elements, stops):
        element.position = position
        element.color = tuple(colour) + (1.0,)
    links.new(fac, ramp.inputs['Fac'])
    return ramp.outputs['Color']


def _see_through(m, nodes, links, principled, colour, amount):
    """Mix a translucent BSDF of the same colour into the surface: thin leaves let the light through."""
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    translucent = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(colour, translucent.inputs['Color'])
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = amount
    links.new(principled.outputs[0], mix.inputs[1])
    links.new(translucent.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs['Surface'])


def leaf_material(part, what, stops, veins='palmate', spacing=50.0, translucent=0.3, rough=0.45, coat=0.3,
                  vein_light=0.3, specular=0.15):
    """A made leaf material ('PART • <part>: <what>'): each leaf's colour from the ramp `stops` by its face number
    'tone'; veins drawn from the UV map 'leaf' (palmate: from the base out to each lobe, `spacing` degrees apart;
    pinnate: a midrib), a little lighter than the blade; see-through by `translucent`; a wet sheen (`coat`)."""
    def maker(m, nodes, links, p):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_name = 'tone'
        colour = _ramp(nodes, links, tone.outputs['Fac'], stops)
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'leaf'
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(uv.outputs['UV'], sep.inputs[0])
        x, y = sep.outputs['X'], sep.outputs['Y']
        if veins == 'palmate':
            angle = shapes.math_node(nodes, links, 'ARCTAN2', x, y)
            wave = shapes.math_node(nodes, links, 'COSINE', shapes.math_node(nodes, links, 'MULTIPLY', angle, 360.0 / spacing))
            line = shapes.math_node(nodes, links, 'POWER', shapes.math_node(nodes, links, 'MAXIMUM', wave, 0.0), 60.0)
            radius = shapes.math_node(nodes, links, 'SQRT', shapes.math_node(
                nodes, links, 'ADD', shapes.math_node(nodes, links, 'MULTIPLY', x, x), shapes.math_node(nodes, links, 'MULTIPLY', y, y)))
            fade = shapes.math_node(nodes, links, 'SUBTRACT', 1.0, shapes.math_node(nodes, links, 'POWER', radius, 2.5), clamp=True)
            amount = shapes.math_node(nodes, links, 'MULTIPLY', line, fade, clamp=True)
            # the leaf's middle, where the veins meet, a little paler; its edge a little darker
            heart = shapes.math_node(nodes, links, 'SUBTRACT', 1.0, shapes.math_node(nodes, links, 'MULTIPLY', radius, 3.0), clamp=True)
            amount = shapes.math_node(nodes, links, 'MAXIMUM', amount, shapes.math_node(nodes, links, 'MULTIPLY', heart, 0.5))
            edge = shapes.map_range(nodes, links, radius, 0.55, 1.0, 0.0, 0.35)
        else:
            ax = shapes.math_node(nodes, links, 'ABSOLUTE', x)
            amount = shapes.map_range(nodes, links, ax, 0.004, 0.0, 0.0, 1.0)
            edge = shapes.map_range(nodes, links, ax, 0.03, 0.09, 0.0, 0.25)
        light = shapes.mix_colour(nodes, links, 0.45, colour, (0.75, 0.62, 0.25), 'MIX')
        colour = shapes.mix_colour(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', amount, vein_light), colour, light)
        colour = shapes.mix_colour(nodes, links, edge, colour, (0.0, 0.0, 0.0))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = rough
        p.inputs['Specular IOR Level'].default_value = specular       # low: a leaf's sheen at a grazing light read as white flowers
        p.inputs['Coat Weight'].default_value = coat
        p.inputs['Coat Roughness'].default_value = 0.15
        if translucent > 0:
            _see_through(m, nodes, links, p, colour, translucent)
    return shapes.part_material(part, what, maker)


def culm_material(part):
    """Bamboo culm: green when young, yellowing with age (the point number 'age', 0 young to 1 old), a pale waxy band
    under each node on the young ones ('band'), a dark line at each node ('ring'), fine streaks along the culm, darker
    and greyer at its damp foot; glossy and wet."""
    def maker(m, nodes, links, p):
        age = nodes.new('ShaderNodeAttribute')
        age.attribute_name = 'age'
        band = nodes.new('ShaderNodeAttribute')
        band.attribute_name = 'band'
        ring = nodes.new('ShaderNodeAttribute')
        ring.attribute_name = 'ring'
        tc = nodes.new('ShaderNodeTexCoord')
        stretch = nodes.new('ShaderNodeVectorMath')
        stretch.operation = 'MULTIPLY'
        stretch.inputs[1].default_value = (60.0, 60.0, 1.2)
        links.new(tc.outputs['Object'], stretch.inputs[0])
        streak = shapes.noise_fac(nodes, links, stretch.outputs[0], 1.0, detail=6.0, roughness=0.6)
        blotch = shapes.noise_fac(nodes, links, tc.outputs['Object'], 9.0, detail=3.0, roughness=0.5)
        green = _ramp(nodes, links, age.outputs['Fac'], [(0.0, (0.032, 0.082, 0.028)), (0.45, (0.07, 0.11, 0.03)),
                                                         (0.8, (0.20, 0.17, 0.045)), (1.0, (0.26, 0.20, 0.07))])
        # old culms: dark mottling
        mottle = shapes.math_node(nodes, links, 'MULTIPLY', shapes.map_range(nodes, links, blotch, 0.55, 0.68, 0.0, 0.7), age.outputs['Fac'])
        colour = shapes.mix_colour(nodes, links, mottle, green, (0.03, 0.03, 0.02))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, streak, 0.35, 0.65, 0.0, 0.25), colour, (0.02, 0.03, 0.01))
        young = shapes.math_node(nodes, links, 'SUBTRACT', 1.0, age.outputs['Fac'], clamp=True)
        bloom = shapes.math_node(nodes, links, 'MULTIPLY', band.outputs['Fac'], shapes.math_node(nodes, links, 'MULTIPLY', young, 0.55))
        colour = shapes.mix_colour(nodes, links, bloom, colour, (0.20, 0.24, 0.23))
        colour = shapes.mix_colour(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', ring.outputs['Fac'], 0.75), colour, (0.03, 0.025, 0.012))
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(tc.outputs['Object'], sep.inputs[0])
        foot = shapes.map_range(nodes, links, sep.outputs['Z'], 0.45, 0.0, 0.0, 0.7)
        colour = shapes.mix_colour(nodes, links, foot, colour, (0.035, 0.035, 0.025))
        links.new(colour, p.inputs['Base Color'])
        rough = shapes.mix_float(nodes, links, band.outputs['Fac'], 0.3, 0.55)
        links.new(rough, p.inputs['Roughness'])
        p.inputs['Coat Weight'].default_value = 0.25
        p.inputs['Coat Roughness'].default_value = 0.15
        normal = shapes.bump(nodes, links, streak, strength=0.15, distance=0.002)
        links.new(normal, p.inputs['Normal'])
    return shapes.part_material(part, 'culms', maker)


def sheath_material(part):
    """A bamboo culm sheath: papery straw-brown, blotched dark, matte; damp darker at its foot."""
    def maker(m, nodes, links, p):
        tc = nodes.new('ShaderNodeTexCoord')
        stretch = nodes.new('ShaderNodeVectorMath')
        stretch.operation = 'MULTIPLY'
        stretch.inputs[1].default_value = (40.0, 40.0, 3.0)
        links.new(tc.outputs['Object'], stretch.inputs[0])
        fibre = shapes.noise_fac(nodes, links, stretch.outputs[0], 1.0, detail=6.0)
        blotch = shapes.noise_fac(nodes, links, tc.outputs['Object'], 30.0, detail=3.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fibre, 0.35, 0.65), (0.17, 0.12, 0.06), (0.30, 0.22, 0.11))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, blotch, 0.55, 0.65, 0.0, 0.8), colour, (0.04, 0.03, 0.02))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.7
        _see_through(m, nodes, links, p, colour, 0.15)
    return shapes.part_material(part, 'culm sheaths', maker)


def needle_material(part):
    """Pine needles: near-black green to a fresher green at the shoots' tips ('tone' per tuft; the UV map 'leaf' y runs
    from a needle's base, 0, to its tip, 1), a few gone brown, glossy and wet."""
    def maker(m, nodes, links, p):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_name = 'tone'
        colour = _ramp(nodes, links, tone.outputs['Fac'], [(0.0, (0.012, 0.03, 0.012)), (0.55, (0.025, 0.055, 0.018)),
                                                           (0.9, (0.06, 0.085, 0.025)), (0.97, (0.16, 0.10, 0.04)), (1.0, (0.16, 0.10, 0.04))])
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'leaf'
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(uv.outputs['UV'], sep.inputs[0])
        tip = shapes.map_range(nodes, links, sep.outputs['Y'], 0.5, 1.0, 0.0, 0.35)
        colour = shapes.mix_colour(nodes, links, tip, colour, (0.10, 0.12, 0.04))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.45
        p.inputs['Specular IOR Level'].default_value = 0.3
        p.inputs['Coat Weight'].default_value = 0.1
        _see_through(m, nodes, links, p, colour, 0.15)
    return shapes.part_material(part, 'needles', maker)


def pad_material(part):
    """The dense heart of a pine's needle pad, seen between the tufts: dark green, broken up, with fine needle streaks."""
    def maker(m, nodes, links, p):
        tc = nodes.new('ShaderNodeTexCoord')
        fine = shapes.noise_fac(nodes, links, tc.outputs['Object'], 60.0, detail=4.0, roughness=0.7)
        broad = shapes.noise_fac(nodes, links, tc.outputs['Object'], 5.0, detail=3.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fine, 0.3, 0.7), (0.004, 0.009, 0.004), (0.014, 0.03, 0.01))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, broad, 0.4, 0.62, 0.0, 0.6), colour, (0.003, 0.006, 0.003))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.9
        p.inputs['Specular IOR Level'].default_value = 0.1
        links.new(shapes.bump(nodes, links, fine, strength=0.6, distance=0.01), p.inputs['Normal'])
    return shapes.part_material(part, 'needle pad', maker)


def bronze_material(part):
    """Old cast bronze out of doors (a bridge's post caps): dark brown metal, rubbed brighter on its swellings where
    hands touch it, blue-green verdigris in streaks and in its hollows and lower parts where rain runs and lies."""
    def maker(m, nodes, links, p):
        tc = nodes.new('ShaderNodeTexCoord')
        stretch = nodes.new('ShaderNodeVectorMath')
        stretch.operation = 'MULTIPLY'
        stretch.inputs[1].default_value = (14.0, 14.0, 3.0)
        links.new(tc.outputs['Object'], stretch.inputs[0])
        streaks = shapes.noise_fac(nodes, links, stretch.outputs[0], 1.0, detail=5.0, roughness=0.6)
        blotch = shapes.noise_fac(nodes, links, tc.outputs['Object'], 40.0, detail=4.0)
        pointiness = nodes.new('ShaderNodeNewGeometry').outputs['Pointiness']
        hollow = shapes.map_range(nodes, links, pointiness, 0.5, 0.42, 0.0, 1.0)
        green = shapes.math_node(nodes, links, 'ADD', shapes.map_range(nodes, links, streaks, 0.48, 0.62, 0.0, 0.8), hollow)
        green = shapes.math_node(nodes, links, 'MULTIPLY', green, shapes.map_range(nodes, links, blotch, 0.3, 0.6, 0.6, 1.0), clamp=True)
        metal = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, pointiness, 0.5, 0.56, 0.0, 1.0), (0.10, 0.06, 0.03), (0.30, 0.19, 0.08))
        colour = shapes.mix_colour(nodes, links, green, metal, (0.07, 0.15, 0.11))
        links.new(colour, p.inputs['Base Color'])
        links.new(shapes.mix_float(nodes, links, green, 0.85, 0.0), p.inputs['Metallic'])
        links.new(shapes.mix_float(nodes, links, green, 0.38, 0.75), p.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, blotch, strength=0.15, distance=0.002), p.inputs['Normal'])
    return shapes.part_material(part, 'old bronze', maker)


def plain_material(part, what, colour, rough=0.6, noise=0.3, scale=20.0):
    """A plain made material: a colour broken up a little by noise (a fern's crown, a frond's stalk)."""
    def maker(m, nodes, links, p):
        tc = nodes.new('ShaderNodeTexCoord')
        n = shapes.noise_fac(nodes, links, tc.outputs['Object'], scale, detail=4.0)
        dark = tuple(c * (1.0 - noise) for c in colour)
        light = tuple(min(1.0, c * (1.0 + noise)) for c in colour)
        links.new(shapes.mix_colour(nodes, links, n, dark, light), p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = rough
    return shapes.part_material(part, what, maker)


# ---------------------------------------------------------------------------------------------- photographed materials

def surface(name, part, what, **dials):
    """A copy of a store SURFACE material for one part and job ('SURFACE • <name> (<part>: <what>)'), its dials turned:
    Weather's (Darken, Wet, Grime, Mud height, Mud color, Edge wear, Bump), 'Scale' (the picture's size: 0.5 shows it at
    half size), 'Normal' (the normal picture's strength), 'Turn' and 'Shade' (the Pieces node)."""
    base = name if name.startswith('SURFACE • ') else 'SURFACE • ' + name
    copy_name = '%s (%s: %s)' % (base, part, what)
    existing = bpy.data.materials.get(copy_name)
    if existing is not None:
        return existing
    m = store.material(base).copy()
    m.name = copy_name
    nodes = m.node_tree.nodes
    for key, value in dials.items():
        if key == 'Scale':
            nodes['Picture size'].inputs['Scale'].default_value = value
        elif key == 'Normal':
            nodes['Normal picture'].inputs['Strength'].default_value = value
        elif key in ('Turn', 'Shade'):
            nodes['Pieces'].inputs[key].default_value = value
        elif key == 'Mud color':
            nodes['Weather'].inputs[key].default_value = tuple(value) + ((1.0,) if len(value) == 3 else ())
        else:
            nodes['Weather'].inputs[key].default_value = value
    return m


def bark(part, what='bark', **dials):
    """The shelf's photographed furrowed bark (bark_willow_02), wet, for one part's trunk and branches."""
    settings = {'Wet': 0.45, 'Grime': 0.4}
    settings.update(dials)
    return surface('bark_willow_02', part, what, **settings)


def painted_wood(part, what, paint=(0.30, 0.04, 0.022), wood='old_planks_02', peel=0.42, **dials):
    """Old paint over the shelf's photographed planks: the photograph's grain, relief and roughness under it, the paint
    a little uneven and chalky, flaked off in patches to the grey wood (more of it where the point number 'pp_bare' is
    1: where hands and feet wear it), and the Weather dials as given (Mud height and Mud color darken and green it up
    from the foot). `peel`: how much has flaked off, 0.3 little, 0.5 a lot."""
    settings = {'Wet': 0.35}
    settings.update(dials)
    m = surface(wood, part, what, **settings)
    if m.get('pp_painted'):
        return m
    m['pp_painted'] = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    weather = nodes['Weather']
    photo_link = weather.inputs['Color'].links[0]
    photo = photo_link.from_socket
    rough_link = weather.inputs['Roughness'].links[0]
    photo_rough = rough_link.from_socket
    tc = nodes.new('ShaderNodeTexCoord')
    flakes = shapes.noise_fac(nodes, links, tc.outputs['Object'], 5.5, detail=8.0, roughness=0.62)
    patches = shapes.noise_fac(nodes, links, tc.outputs['Object'], 1.2, detail=2.0)
    bare = nodes.new('ShaderNodeAttribute')
    bare.attribute_name = 'pp_bare'
    # the paint holds where the flakes' noise is over the line; worn places and big patches lower it
    level = shapes.math_node(nodes, links, 'SUBTRACT', flakes, shapes.math_node(nodes, links, 'MULTIPLY', bare.outputs['Fac'], 0.32))
    level = shapes.math_node(nodes, links, 'ADD', level, shapes.math_node(nodes, links, 'MULTIPLY', shapes.math_node(nodes, links, 'SUBTRACT', patches, 0.5), 0.25))
    held = shapes.map_range(nodes, links, level, peel - 0.015, peel + 0.015, 0.0, 1.0)
    shade = shapes.noise_fac(nodes, links, tc.outputs['Object'], 3.0, detail=3.0)
    tint = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, shade, 0.35, 0.65), tuple(c * 0.78 for c in paint),
                             (min(1.0, paint[0] * 1.2), paint[1] * 1.6, paint[2] * 1.2))
    grain = shapes.mix_colour(nodes, links, 0.35, tint, photo, 'MULTIPLY')
    grain = shapes.mix_colour(nodes, links, 0.25, grain, tint, 'MIX')
    # the bare wood greys where paint has gone
    wood_grey = shapes.mix_colour(nodes, links, 0.35, photo, (0.06, 0.058, 0.052), 'MIX')
    colour = shapes.mix_colour(nodes, links, held, wood_grey, grain)
    links.remove(photo_link)
    links.new(colour, weather.inputs['Color'])
    rough = shapes.mix_float(nodes, links, held, photo_rough, 0.5)
    links.remove(rough_link)
    links.new(rough, weather.inputs['Roughness'])
    return m
