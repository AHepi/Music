"""
What this file is: helpers shared by the garden things made from the Japanese garden builders' code (log 57):
stone_lantern, water_basin, jar, clogs, hanging_lantern, wooden_bucket, bamboo_broom. It is not a part (its name starts
with '_', so the store does not list it). It adds to the chapel helpers (_shapes_chapel.py, imported here as `shapes`):

    shape = Shape()                       the chapel Shape, and two more things:
    shape.begin(); ...; shape.end(0.37)   every face made between the two carries the number 'pp_piece' = 0.37, so a
                                          photographed (SURFACE) material shows that piece its own part of the picture
                                          (one stone of a lantern, one stave of a bucket); end(value, name) writes
                                          another face number instead
    culm(shape, a, b, radius, rng)        a bamboo stem from a to b: swollen rings at its joints, the point numbers
                                          'culm' (round and along it) and 'culm_node' (1 at a joint) the bamboo
                                          materials read, an open or slanted end if asked
    roughen(shape, verts, amount, scale)  pushes points in and out along their normals by a noise (rough stone)
    hex_ring(r, z, turn)                  six corners of a hexagon

Materials (each made once per file):
    garden_stone(wet)                     'SURFACE • dark_rock_02 (garden stone ...)': the photographed dark rock as
                                          weathered granite: rain streaks run down it (weathering.stone) and moss sits
                                          on what faces up and round the foot (moss.add); the stone pieces carry
                                          'pp_piece' so each shows its own part of the photograph
    wood(part, darken)                    'SURFACE • rough_wood (<part>)', the photographed weathered wood; its grain
                                          runs along the object's own Z on the sides
    tinted(name, part, colour)            a SURFACE copy turned to one colour, its picture's light and dark kept (the
                                          clogs' red cloth thongs)
    bamboo('green' | 'weathered')         bamboo stems made in code (no bamboo photograph on the shelf): streaks along
                                          the stem, darker joints, a waxy pale band under each joint
    twigs()                               dry bamboo twigs for a broom
    paper(lit)                            lantern paper: lit, glowing warm and patchy where thicker; unlit, a dirty
                                          off-white that lets some light through
    still_water(part, centre)             dark still water, glossy, rings spreading from `centre` where a stream lands
    falling_water()                       a thin clear stream
    moss_cushion()                        cushions of dark green moss on the ground, fuzzy and matte
    cord(colour)                          a dark twisted cord (bindings, a lantern's cord)
"""

import math
import random

import bpy
import bmesh  # noqa: F401  (bpy first, then bmesh)
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

import _shapes_chapel as shapes
import store

UP = Vector((0.0, 0.0, 1.0))


class Shape(shapes.Shape):
    """The chapel Shape with piece numbers: faces made between begin() and end(value) carry 'pp_piece' (or another
    face number)."""

    def begin(self):
        self._before = set(self.bm.faces)
        self._vbefore = set(self.bm.verts)

    def end(self, value, name='pp_piece'):
        layer = self.bm.faces.layers.float.get(name) or self.bm.faces.layers.float.new(name)
        for face in self.bm.faces:
            if face not in self._before:
                face[layer] = float(value)

    def new_verts(self):
        return [v for v in self.bm.verts if v not in self._vbefore]


def hex_ring(r, z, turn=0.0, centre=(0.0, 0.0)):
    return [Vector((centre[0] + r * math.cos(turn + i * math.pi / 3), centre[1] + r * math.sin(turn + i * math.pi / 3), z)) for i in range(6)]


def roughen(shape, verts, amount, scale, seed=0, up_only=False):
    """Push each point in or out along its normal by a smooth noise (amount metres at most, patches about 1/scale m)."""
    shape.bm.normal_update()
    salt = Vector((seed * 7.31, seed * 3.17, seed * 1.93))
    moves = []
    for v in verts:
        n = v.normal.copy()
        if n.length < 1e-6:
            continue
        p = v.co * scale + salt
        d = mnoise.noise(p) * 0.7 + mnoise.noise(p * 2.7) * 0.3
        if up_only and n.z < 0.3:
            d *= 0.3
        moves.append((v, n * (d * amount)))
    for v, m in moves:
        v.co += m


# ---------------------------------------------------------------------- bamboo

def culm(shape, a, b, radius, rng, node_gap=0.26, sides=10, caps=True, slant=0.0, taper=1.0, offset=None):
    """A bamboo stem from a to b, radius metres (tapering to radius * taper at b), swollen a little at its joints every
    `node_gap` metres or so; writes the point numbers 'culm' (cos, sin round the stem, metres along it) and 'culm_node'
    (1 on a joint ring). `slant` cuts the end at b on a slope (the lower lip reaching slant * radius further)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    length = d.length
    if length < 1e-5:
        return []
    t = d / length
    joints = []
    s = rng.uniform(0.25, 0.8) * node_gap
    while s < length - 0.03:
        joints.append(s)
        s += node_gap * rng.uniform(0.85, 1.15)
    stations = {0.0, length}
    for j in joints:
        for x in (j - 0.012, j - 0.004, j + 0.004, j + 0.012):
            if 0.002 < x < length - 0.002:
                stations.add(x)
    if length > 0.2:
        for k in range(1, int(length / 0.2)):
            stations.add(length * k / int(length / 0.2))
    stations = sorted(stations)
    radii = []
    for x in stations:
        r = radius * (1.0 + (taper - 1.0) * x / length)
        if any(abs(x - j) < 0.005 for j in joints):
            r *= 1.07
        radii.append(r)
    before = set(shape.bm.verts)
    shape.sweep([a + t * x for x in stations], radius, sides=sides, radii=radii, caps=caps)
    frame = shapes.frame_along(d)
    inverse = frame.transposed()
    vec = shape.bm.verts.layers.float_vector.get('culm') or shape.bm.verts.layers.float_vector.new('culm')
    knot = shape.bm.verts.layers.float.get('culm_node') or shape.bm.verts.layers.float.new('culm_node')
    shift = rng.uniform(0, 50) if offset is None else offset
    made = [v for v in shape.bm.verts if v not in before]
    for v in made:
        local = inverse @ (v.co - a)
        if slant and local.z > length - 1e-4:
            v.co += t * (-slant * local.y)
            local = inverse @ (v.co - a)
        angle = math.atan2(local.y, local.x)
        v[vec] = (math.cos(angle), math.sin(angle), local.z + shift)
        near = min((abs(local.z - j) for j in joints), default=1.0)
        v[knot] = max(0.0, 1.0 - near / 0.009)
    return made


# ---------------------------------------------------------------------- materials

def _principled(material):
    for n in material.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def garden_stone(wet=0.45, moss_amount=1.0, foot=0.3):
    """The photographed dark rock as weathered granite: a SURFACE copy, rain streaks run down it, moss on what faces up
    and round the foot. Made once per file (by its settings)."""
    name = 'SURFACE • dark_rock_02 (garden stone, wet %.2f, moss %.2f)' % (wet, moss_amount)
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    import moss
    import weathering
    base = shapes.surface_copy('SURFACE • dark_rock_02', 'garden stone %.2f' % wet, Wet=wet, Darken=1.15, Grime=0.45, Bump=0.35)
    streaked = weathering.stone(base, dark=0.5, overall=1.0, streak_width=0.05, streak_length=0.7, blotch=0.35, wet=0.0, seed=3)
    mossy = moss.add(streaked, amount=moss_amount, foot=foot, facing=(0.35, 0.8), scale=7.0) if moss_amount > 0 else streaked
    mossy.name = name
    return mossy


def wood(part, darken=0.72, wet=0.0, grime=0.4, edge=0.4):
    """The photographed weathered wood for one part ('SURFACE • rough_wood (<part>)'): its grain runs along the
    object's own Z on its sides, so build a wooden piece with its Z along the grain."""
    return shapes.surface_copy('SURFACE • rough_wood', part, Darken=darken, Wet=wet, Grime=grime)


def tinted(name, part, colour, lift=2.6):
    """A SURFACE copy turned to one colour: the picture's light and dark kept, its own colour taken out."""
    copy_name = '%s (%s, %s)' % (name, part, 'tinted %.2f %.2f %.2f' % tuple(colour))
    existing = bpy.data.materials.get(copy_name)
    if existing is not None:
        return existing
    m = store.material(name).copy()
    m.name = copy_name
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = _principled(m)
    base = p.inputs['Base Color']
    if base.is_linked:
        source = base.links[0].from_socket
        grey = nodes.new('ShaderNodeRGBToBW')
        links.new(source, grey.inputs[0])
        scaled = shapes.math_node(nodes, links, 'MULTIPLY', grey.outputs[0], lift)
        mult = nodes.new('ShaderNodeMix')
        mult.data_type = 'RGBA'
        mult.blend_type = 'MULTIPLY'
        mult.inputs[0].default_value = 1.0
        mult.inputs[6].default_value = tuple(colour) + (1.0,)
        links.new(scaled, mult.inputs[7])
        links.new(mult.outputs[2], base)
    else:
        base.default_value = tuple(colour) + (1.0,)
    return m


def bamboo(kind='weathered'):
    """Bamboo stems made in code: streaks along the stem (from the point number 'culm' that culm() writes), each stem
    a little different, darker joints with a pale waxy band under them; 'green' fresh and glossy, 'weathered' greyed
    straw, duller, with dark specks of mould."""
    green = kind == 'green'

    def maker(m, nodes, links, p):
        attr = nodes.new('ShaderNodeAttribute')
        attr.attribute_name = 'culm'
        joint = nodes.new('ShaderNodeAttribute')
        joint.attribute_name = 'culm_node'
        info = nodes.new('ShaderNodeObjectInfo')
        stretch = nodes.new('ShaderNodeMapping')
        stretch.inputs['Scale'].default_value = (7.0, 7.0, 0.45)
        links.new(attr.outputs['Vector'], stretch.inputs['Vector'])
        streak = shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 3.0, detail=6.0, roughness=0.62)
        blot = shapes.noise_fac(nodes, links, attr.outputs['Vector'], 2.2, detail=3.0)
        if green:
            a, b, knot, wax = (0.055, 0.085, 0.022), (0.16, 0.15, 0.045), (0.07, 0.065, 0.025), (0.17, 0.18, 0.12)
        else:
            a, b, knot, wax = (0.15, 0.11, 0.055), (0.075, 0.066, 0.05), (0.04, 0.03, 0.018), (0.2, 0.18, 0.13)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, streak, 0.32, 0.68), a, b)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, blot, 0.45, 0.7, 0.0, 0.5), colour, b)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, info.outputs['Random'], 0.0, 1.0, 0.0, 0.35), colour, tuple(c * 0.75 for c in a))
        # the pale waxy band just under a joint, then the dark joint ring itself
        band = shapes.map_range(nodes, links, joint.outputs['Fac'], 0.05, 0.3, 0.0, 0.45)
        colour = shapes.mix_colour(nodes, links, band, colour, wax)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, joint.outputs['Fac'], 0.55, 0.95), colour, knot)
        if not green:
            specks = shapes.noise_fac(nodes, links, attr.outputs['Vector'], 14.0, detail=2.0)
            colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, specks, 0.66, 0.74, 0.0, 0.8), colour, (0.025, 0.022, 0.018))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.3 if green else 0.5
        p.inputs['Coat Weight'].default_value = 0.35 if green else 0.12
        p.inputs['Coat Roughness'].default_value = 0.15
        links.new(shapes.bump(nodes, links, streak, 0.08, 0.002), p.inputs['Normal'])
        m.diffuse_color = tuple(b) + (1.0,)
    return shapes.part_material('garden', 'bamboo, %s' % ('green' if green else 'weathered'), maker)


def twigs():
    """Dry bamboo twigs: straw to grey-brown, each twig its own shade (face number 'twig_tone'), dull."""
    def maker(m, nodes, links, p):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_name = 'twig_tone'
        vec = shapes.own_coordinates(nodes)
        grain = shapes.noise_fac(nodes, links, vec, 60.0, detail=2.0)
        colour = shapes.mix_colour(nodes, links, tone.outputs['Fac'], (0.21, 0.16, 0.085), (0.085, 0.07, 0.05))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.35, 0.65, 0.0, 0.3), colour, (0.05, 0.04, 0.03))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.6
        m.diffuse_color = (0.16, 0.12, 0.07, 1.0)
    return shapes.part_material('garden', 'dry bamboo twigs', maker)


def paper(lit, colour=(1.0, 0.5, 0.2), strength=3.5):
    """Lantern paper. Lit: glowing warm, patchy where the paper is thicker or patched (give its objects
    visible_shadow = False, so the light inside gets out). Unlit: a dirty off-white letting a little light through."""
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        fibre = shapes.noise_fac(nodes, links, vec, 38.0, detail=6.0, roughness=0.7)
        patch = shapes.noise_fac(nodes, links, vec, 5.0, detail=3.0)
        dirt = shapes.map_range(nodes, links, patch, 0.5, 0.75, 0.0, 0.6)
        paper_colour = shapes.mix_colour(nodes, links, dirt, (0.5, 0.46, 0.37), (0.24, 0.2, 0.14))
        links.new(paper_colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.85
        if lit:
            glow = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fibre, 0.3, 0.7), tuple(c * 0.7 for c in colour), colour)
            glow = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, patch, 0.45, 0.8, 0.0, 0.5), glow, tuple(c * 0.45 for c in colour))
            links.new(glow, p.inputs['Emission Color'])
            p.inputs['Emission Strength'].default_value = strength
            m.diffuse_color = tuple(colour) + (1.0,)
        else:
            out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
            through = nodes.new('ShaderNodeBsdfTranslucent')
            through.inputs['Color'].default_value = (0.35, 0.3, 0.22, 1.0)
            mix = nodes.new('ShaderNodeMixShader')
            mix.inputs[0].default_value = 0.3
            links.new(p.outputs[0], mix.inputs[1])
            links.new(through.outputs[0], mix.inputs[2])
            links.new(mix.outputs[0], out.inputs['Surface'])
            m.diffuse_color = (0.45, 0.42, 0.34, 1.0)
        links.new(shapes.bump(nodes, links, fibre, 0.05, 0.001), p.inputs['Normal'])
    return shapes.part_material('garden', 'lantern paper, lit' if lit else 'lantern paper', maker)


def still_water(part, centre=None):
    """Dark still water in a basin or a bucket: near-black, glossy, a faint ripple, and rings spreading from `centre`
    (x, y in the part's own metres) where a stream lands."""
    def maker(m, nodes, links, p):
        p.inputs['Base Color'].default_value = (0.006, 0.009, 0.011, 1.0)
        p.inputs['Roughness'].default_value = 0.03
        p.inputs['IOR'].default_value = 1.333
        vec = shapes.own_coordinates(nodes)
        ripple = shapes.noise_fac(nodes, links, vec, 14.0, detail=3.0)
        height = shapes.math_node(nodes, links, 'MULTIPLY', ripple, 0.2)
        if centre is not None:
            move = nodes.new('ShaderNodeMapping')
            move.inputs['Location'].default_value = (-centre[0], -centre[1], 0.0)
            links.new(vec, move.inputs['Vector'])
            flat = nodes.new('ShaderNodeVectorMath')
            flat.operation = 'MULTIPLY'
            flat.inputs[1].default_value = (1.0, 1.0, 0.0)
            links.new(move.outputs['Vector'], flat.inputs[0])
            length = nodes.new('ShaderNodeVectorMath')
            length.operation = 'LENGTH'
            links.new(flat.outputs[0], length.inputs[0])
            wave = shapes.math_node(nodes, links, 'SINE', shapes.math_node(nodes, links, 'MULTIPLY', length.outputs['Value'], 160.0))
            fade = shapes.map_range(nodes, links, length.outputs['Value'], 0.02, 0.22, 1.0, 0.0)
            rings = shapes.math_node(nodes, links, 'MULTIPLY', wave, fade)
            height = shapes.math_node(nodes, links, 'ADD', height, shapes.math_node(nodes, links, 'MULTIPLY', rings, 0.6))
        links.new(shapes.bump(nodes, links, height, 0.25, 0.004), p.inputs['Normal'])
        m.diffuse_color = (0.01, 0.012, 0.014, 1.0)
    return shapes.part_material(part, 'still water', maker)


def moss_cushion():
    """Cushions of moss on the ground: dark green, yellower in patches where the light catches its tips, fuzzy (a
    fine bump), matte; darker and glossier at its foot where it is wettest."""
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        fuzz = shapes.noise_fac(nodes, links, vec, 260.0, detail=3.0, roughness=0.7)
        patch = shapes.noise_fac(nodes, links, vec, 18.0, detail=4.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, patch, 0.35, 0.7), (0.012, 0.026, 0.006), (0.035, 0.06, 0.01))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fuzz, 0.55, 0.8, 0.0, 0.5), colour, (0.06, 0.085, 0.015))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.85
        links.new(shapes.bump(nodes, links, fuzz, 0.6, 0.002), p.inputs['Normal'])
        m.diffuse_color = (0.03, 0.05, 0.01, 1.0)
    return shapes.part_material('garden', 'moss cushions', maker)


def falling_water():
    """A thin stream of clear water: glassy, catching the light along its length."""
    def maker(m, nodes, links, p):
        p.inputs['Base Color'].default_value = (0.7, 0.75, 0.78, 1.0)
        p.inputs['Roughness'].default_value = 0.04
        p.inputs['Transmission Weight'].default_value = 0.85
        p.inputs['IOR'].default_value = 1.333
        p.inputs['Coat Weight'].default_value = 0.5
        m.diffuse_color = (0.6, 0.65, 0.7, 1.0)
    return shapes.part_material('garden', 'falling water', maker)


def cord(colour=(0.025, 0.02, 0.016), what='dark cord'):
    """A twisted cord or binding: a dull dark colour with a fine twist in its bump."""
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        twist = shapes.noise_fac(nodes, links, vec, 120.0, detail=2.0)
        links.new(shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, twist, 0.3, 0.7), tuple(c * 0.6 for c in colour), colour), p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.8
        links.new(shapes.bump(nodes, links, twist, 0.3, 0.001), p.inputs['Normal'])
        m.diffuse_color = tuple(colour) + (1.0,)
    return shapes.part_material('garden', what, maker)


def hidden_light(collection, name, location, power, colour=(1.0, 0.55, 0.22), radius=0.03):
    """A small warm point light that lights what is round it but is never seen itself (the builders found lights
    show to the eye unless hidden)."""
    obj = shapes.point_light(collection, name, location, power, colour, radius)
    obj.visible_camera = False
    return obj


def mark_all(shape, name, function):
    """A point number from each point's place: function(Vector) -> number."""
    layer = shape.bm.verts.layers.float.get(name) or shape.bm.verts.layers.float.new(name)
    for v in shape.bm.verts:
        v[layer] = float(function(v.co))


def rng_for(part, seed, salt=''):
    return random.Random('%s|%s|%s' % (part, seed, salt))


def matrix_z_along(direction, origin=(0.0, 0.0, 0.0)):
    """A frame whose Z runs along `direction` (for a wooden piece whose grain runs that way)."""
    return shapes.to4(shapes.frame_along(Vector(direction)), origin)
