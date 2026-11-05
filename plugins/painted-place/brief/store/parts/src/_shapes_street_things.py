"""
What this file is: helpers shared by the street things made from the town street builders' code (log 55): ash_bin,
drain, sett_stack, newspaper, chimney_stack, sack_barrow, coster_barrow. It is not a part (its name starts with '_',
so the store does not list it). It adds to the chapel helpers (_shapes_chapel.py, imported here as `shapes`):

    add_soot(material, reach_colour=...)    soot laid over any material (a SURFACE copy, a STONE, the clay), as much
                                            as the point number 'soot' on the object says (0 none, 1 black), broken
                                            into streaks running down
    sooted(name, part, **dials)             a copy of a store material for one part with soot added
    heap(shape, centre, rx, ry, height, rng) a slumped heap with a ragged, lobed foot (ash in a bin, grit)
    bin_material(part)                      galvanised iron gone dull: grey zinc blotched, rust and soot running down
                                            from the rim, rust at the foot (the street builder's bin_mat)
    worn_iron_material(part)                cast iron rusty in the hollows and worn bright on what stands proud
    clinker_material(part), clay_material(part), granite_material(part), newsprint_material(part),
    mortar_material(part)                   the street things' own made materials
"""

import math

import bpy
from mathutils import Vector
from mathutils import noise as mnoise

import _shapes_chapel as shapes

UP = Vector((0.0, 0.0, 1.0))


# ---------------------------------------------------------------------- soot over any material

def _principled(material):
    for n in material.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def add_soot(material, colour=(0.011, 0.010, 0.010), streaks=1.0):
    """Lay soot over a material: its colour goes to near-black and dull as far as the object's point number 'soot'
    says (0 clean, 1 black), the edge of the soot broken into streaks running down (noise stretched along Z). Works on
    any material with a Principled BSDF (a SURFACE copy, a STONE, a made one). Done once per material."""
    if material.get('pp_sooted'):
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = _principled(material)
    attr = nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'soot'
    vec = shapes.own_coordinates(nodes)
    stretch = nodes.new('ShaderNodeMapping')
    stretch.inputs['Scale'].default_value = (16.0, 16.0, 1.1)
    links.new(vec, stretch.inputs['Vector'])
    streak = shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 1.0, detail=5.0, roughness=0.6)
    blot = shapes.noise_fac(nodes, links, vec, 6.0, detail=4.0)
    # the soot number scaled up and down by the streaks and blots (never any where the number is 0), then full black
    # from 0.8 up: so the top is black, and lower down the streaks decide
    wobble = shapes.math_node(nodes, links, 'ADD', shapes.map_range(nodes, links, streak, 0.3, 0.7, 1.0 - 0.45 * streaks, 1.0 + 0.45 * streaks),
                              shapes.map_range(nodes, links, blot, 0.3, 0.7, -0.15, 0.15))
    amount = shapes.math_node(nodes, links, 'MULTIPLY', attr.outputs['Fac'], wobble)
    amount = shapes.map_range(nodes, links, amount, 0.06, 0.55, 0.0, 1.0)
    base = principled.inputs['Base Color']
    source = base.links[0].from_socket if base.is_linked else tuple(base.default_value)[:3]
    links.new(shapes.mix_colour(nodes, links, amount, source, colour), base)
    rough = principled.inputs['Roughness']
    rsource = rough.links[0].from_socket if rough.is_linked else rough.default_value
    links.new(shapes.mix_float(nodes, links, amount, rsource, 0.9), rough)
    material['pp_sooted'] = True
    return material


def sooted(name, part, **dials):
    """A copy of a store material for one part ('<name> (<part>, sooted)'), with soot added (see add_soot); a SURFACE
    material's Weather dials can be turned too."""
    copy_name = '%s (%s, sooted)' % (name, part)
    existing = bpy.data.materials.get(copy_name)
    if existing is not None:
        return existing
    if name.startswith('SURFACE • '):
        m = shapes.surface_copy(name, part, **dials).copy()
    else:
        m = shapes.material(name).copy()
    m.name = copy_name
    return add_soot(m)


# ---------------------------------------------------------------------- a slumped heap

def heap(shape, centre, rx, ry, height, rng, segments=28, rings=9, rough=0.012, lobes=0.16):
    """A slumped heap into `shape`: a ragged, lobed foot (rx, ry) round `centre` (its foot's height), rising to
    `height`, its top lumpy. Closed underneath (a flat bottom at the foot)."""
    cx, cy, cz = centre
    phase = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    salt = Vector((rng.uniform(0, 100), rng.uniform(0, 100), 0.0))
    ring_verts = []
    for i in range(rings):
        t = i / rings                     # 0 at the foot, towards 1 at the top
        ring = []
        for j in range(segments):
            a = 2 * math.pi * j / segments
            wob = 1.0 + lobes * math.sin(3 * a + phase[0]) + lobes * 0.55 * math.sin(5 * a + phase[1]) + rng.uniform(-0.04, 0.04)
            spread = (1.0 - t ** 1.15)
            x, y = cx + rx * spread * wob * math.cos(a), cy + ry * spread * wob * math.sin(a)
            z = cz + height * (1.0 - (1.0 - t) ** 1.8)
            n = mnoise.noise(Vector((x * 9.0, y * 9.0, 0.0)) + salt)
            z += rough * n * (0.3 + t)
            if i == 0:
                z = cz
            ring.append(Vector((x, y, z)))
        ring_verts.append(shape._verts(ring))
    top = shape._verts([(cx + rng.uniform(-0.01, 0.01), cy + rng.uniform(-0.01, 0.01), cz + height)])
    bottom = shape._verts([(cx, cy, cz)])
    shape._rings([bottom] + ring_verts + [top], True, False, False)


# ---------------------------------------------------------------------- materials

def bin_material(part, height):
    """Galvanised iron gone dull (the street builder's bin_mat): grey zinc blotched light and dark; rust and soot run
    down from the rim and the handles in streaks; rust at the foot where it stands in the wet. `height` is the bin's
    height (the streaks are strongest under the rim)."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vec, sep.inputs[0])
        z = shapes.math_node(nodes, links, 'DIVIDE', sep.outputs['Z'], height)
        stretch = nodes.new('ShaderNodeMapping')
        stretch.inputs['Scale'].default_value = (14.0, 14.0, 1.2)
        links.new(vec, stretch.inputs['Vector'])
        streak = shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 2.5, detail=6.0)
        top = shapes.map_range(nodes, links, z, 0.35, 0.95)
        foot = shapes.map_range(nodes, links, z, 0.16, 0.0)
        runs = shapes.math_node(nodes, links, 'MULTIPLY', top, shapes.map_range(nodes, links, streak, 0.42, 0.6))
        rust = shapes.math_node(nodes, links, 'MAXIMUM', runs, foot, clamp=True)
        blot = shapes.noise_fac(nodes, links, vec, 5.0, detail=4.0)
        spangle = nodes.new('ShaderNodeTexVoronoi')
        spangle.inputs['Scale'].default_value = 70.0
        links.new(vec, spangle.inputs['Vector'])
        zinc = shapes.mix_colour(nodes, links, blot, (0.06, 0.062, 0.06), (0.13, 0.135, 0.13))
        zinc = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, spangle.outputs['Distance'], 0.0, 0.5, 0.0, 0.25), zinc, (0.16, 0.165, 0.16))
        # soot in the runs nearest the rim, rust lower down and at the foot
        runs_colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, z, 0.6, 0.95), (0.075, 0.028, 0.010), (0.02, 0.016, 0.013))
        colour = shapes.mix_colour(nodes, links, rust, zinc, runs_colour)
        links.new(colour, principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, rust, 0.0, 1.0, 0.55, 0.0), principled.inputs['Metallic'])
        links.new(shapes.map_range(nodes, links, rust, 0.0, 1.0, 0.5, 0.85), principled.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, blot, 0.2, 0.01), principled.inputs['Normal'])
        m.diffuse_color = (0.1, 0.1, 0.1, 1.0)
    return shapes.part_material(part, 'galvanised iron, dull, rust and soot runs', maker)


def worn_iron_material(part, low=-0.003, high=0.0015):
    """Cast iron in a road: rusty brown-black in the hollows and on every side face; the faces that stand proud
    (above `high` in the object's own height) and face up are worn bright by wheels and boots: dark steel with a
    shine. Between `low` and `high` it goes from one to the other, broken by noise."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vec, sep.inputs[0])
        geo = nodes.new('ShaderNodeNewGeometry')
        nsep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(geo.outputs['Normal'], nsep.inputs[0])
        facing_up = shapes.map_range(nodes, links, nsep.outputs['Z'], 0.75, 0.95)
        proud = shapes.map_range(nodes, links, sep.outputs['Z'], low, high)
        patch = shapes.noise_fac(nodes, links, vec, 14.0, detail=4.0)
        worn = shapes.math_node(nodes, links, 'MULTIPLY', facing_up, proud)
        worn = shapes.math_node(nodes, links, 'MULTIPLY', worn, shapes.map_range(nodes, links, patch, 0.3, 0.5, 0.55, 1.0), clamp=True)
        grain = shapes.noise_fac(nodes, links, vec, 90.0, detail=3.0)
        flake = shapes.noise_fac(nodes, links, vec, 22.0, detail=5.0, roughness=0.65)
        rust = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, flake, 0.35, 0.65), (0.014, 0.008, 0.005), (0.055, 0.022, 0.009))
        rust = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.55, 0.75, 0.0, 0.5), rust, (0.008, 0.007, 0.006))
        # worn iron: a light grey that reads pale in any light, half metal (a full mirror would show only the dark sky)
        steel = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.3, 0.7), (0.26, 0.255, 0.25), (0.42, 0.41, 0.4))
        links.new(shapes.mix_colour(nodes, links, worn, rust, steel), principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, worn, 0.0, 1.0, 0.05, 0.5), principled.inputs['Metallic'])
        links.new(shapes.map_range(nodes, links, worn, 0.0, 1.0, 0.85, 0.36), principled.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, flake, 0.35, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.05, 0.03, 0.02, 1.0)
    return shapes.part_material(part, 'cast iron, rusty in the hollows, worn bright on top', maker)


def clinker_material(part):
    """Clinker: burnt-out coal, grey-black and pitted, duller than coal, each lump its own shade."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        pits = shapes.noise_fac(nodes, links, vec, 60.0, detail=3.0, roughness=0.7)
        geo = nodes.new('ShaderNodeNewGeometry')
        tint = shapes.map_range(nodes, links, geo.outputs['Random Per Island'], 0.0, 1.0, 0.0, 1.0)
        dark = shapes.mix_colour(nodes, links, tint, (0.028, 0.027, 0.026), (0.06, 0.05, 0.045))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, pits, 0.4, 0.6), dark, (0.085, 0.08, 0.075))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.8
        links.new(shapes.bump(nodes, links, pits, 0.5, 0.004), principled.inputs['Normal'])
        m.diffuse_color = (0.05, 0.05, 0.05, 1.0)
    return shapes.part_material(part, 'clinker', maker)


def clay_material(part):
    """Fired clay (chimney pots): a dull red-brown, a little blotched, each pot its own shade; soot comes on top
    through add_soot."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        blot = shapes.noise_fac(nodes, links, vec, 7.0, detail=5.0)
        fine = shapes.noise_fac(nodes, links, vec, 70.0, detail=3.0)
        geo = nodes.new('ShaderNodeNewGeometry')
        tone = geo.outputs['Random Per Island']
        base = shapes.mix_colour(nodes, links, tone, (0.16, 0.06, 0.03), (0.24, 0.10, 0.05))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, blot, 0.35, 0.7, 0.0, 0.6), base, (0.09, 0.05, 0.035))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fine, 0.4, 0.7, 0.0, 0.3), colour, (0.12, 0.08, 0.06))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.85
        links.new(shapes.bump(nodes, links, fine, 0.15, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.2, 0.08, 0.04, 1.0)
    return add_soot(shapes.part_material(part, 'fired clay, sooted', maker))


def mortar_material(part, what='lime mortar, sooted'):
    """Old lime mortar (flaunching round chimney pots, joints): grey, gritty, sooted through add_soot."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        grit = shapes.noise_fac(nodes, links, vec, 80.0, detail=3.0)
        blot = shapes.noise_fac(nodes, links, vec, 6.0, detail=4.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, blot, 0.3, 0.7), (0.06, 0.058, 0.054), (0.12, 0.115, 0.105))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grit, 0.5, 0.7, 0.0, 0.4), colour, (0.04, 0.038, 0.035))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.92
        links.new(shapes.bump(nodes, links, grit, 0.3, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.09, 0.09, 0.085, 1.0)
    return add_soot(shapes.part_material(part, what, maker))


def granite_material(part):
    """New granite setts, wet: a dark grey speckled with black mica and pale quartz grains, each sett its own shade
    (one per island), a wet shine (the street builder's 'new granite setts', with the grain)."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        grains = nodes.new('ShaderNodeTexVoronoi')
        grains.inputs['Scale'].default_value = 260.0
        grains.inputs['Randomness'].default_value = 1.0
        links.new(vec, grains.inputs['Vector'])
        cloud = shapes.noise_fac(nodes, links, vec, 9.0, detail=4.0)
        geo = nodes.new('ShaderNodeNewGeometry')
        tone = geo.outputs['Random Per Island']
        base = shapes.mix_colour(nodes, links, tone, (0.050, 0.048, 0.047), (0.095, 0.088, 0.082))
        base = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, cloud, 0.3, 0.7, 0.0, 0.35), base, (0.075, 0.06, 0.05))
        speck = grains.outputs['Color']
        sep = nodes.new('ShaderNodeSeparateColor')
        links.new(speck, sep.inputs[0])
        black = shapes.map_range(nodes, links, sep.outputs[0], 0.0, 0.18, 1.0, 0.0)
        pale = shapes.map_range(nodes, links, sep.outputs[1], 0.86, 1.0, 0.0, 1.0)
        colour = shapes.mix_colour(nodes, links, black, base, (0.012, 0.012, 0.013))
        colour = shapes.mix_colour(nodes, links, pale, colour, (0.2, 0.195, 0.19))
        links.new(colour, principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, cloud, 0.3, 0.7, 0.18, 0.4), principled.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, grains.outputs['Distance'], 0.15, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.07, 0.066, 0.063, 1.0)
    return shapes.part_material(part, 'new granite, wet', maker)


def newsprint_material(part):
    """Newsprint gone sodden: a grey-buff paper, darker and a little glossy where the water stands in it, the fibres
    in the bump; no print (at a distance print reads as noise, and the look asks for none)."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        wet = shapes.noise_fac(nodes, links, vec, 7.0, detail=5.0, roughness=0.6)
        fibre = shapes.noise_fac(nodes, links, vec, 160.0, detail=3.0)
        dirt = shapes.noise_fac(nodes, links, vec, 3.0, detail=3.0)
        soaked = shapes.map_range(nodes, links, wet, 0.38, 0.58)
        dry = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, dirt, 0.3, 0.7), (0.15, 0.142, 0.12), (0.11, 0.1, 0.082))
        colour = shapes.mix_colour(nodes, links, soaked, dry, (0.058, 0.054, 0.046))
        links.new(colour, principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, soaked, 0.0, 1.0, 0.62, 0.28), principled.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, fibre, 0.12, 0.001), principled.inputs['Normal'])
        principled.inputs['Subsurface Weight'].default_value = 0.0
        m.diffuse_color = (0.12, 0.11, 0.095, 1.0)
    return shapes.part_material(part, 'sodden newsprint', maker)
