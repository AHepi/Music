"""
What this file is: helpers shared by the barn parts (made from the two barn builders' scripts, log 54: plank_door,
ladder, fork, skep, mangold_heap, hay, bare_tree, corrugated_sheet). It is not a part (its name starts with '_', so the
store does not list it). It adds to the chapel helpers (_shapes_chapel.py, imported here as `shapes`):

    mangold(shape, matrix, length, radius, rng)     one mangold root into a Shape: a crown with a small knob, a shoulder,
                                                    a long taper to a bent tail; it writes the point numbers 'tail'
                                                    (0 at the crown, 1 at the tip) and 'root_tone' (one per root)
    mangold_material(part)                          'PART • <part>: mangold, soiled': each root its own dull orange to
                                                    red (from 'root_tone'), a darker shoulder, soil caked on the tail
                                                    (from 'tail') and in patches
    shaded_surface(name, part, **dials)             a copy of a SURFACE material for one part in which every object
                                                    takes its own shade (planks, rails, rungs)
    number_layers(shape, points=(), faces=())       make named number layers on a Shape before any of its points
                                                    (adding a layer later drops the points already made)
    point_numbers(shape, verts, **numbers)          write point numbers on some points of a Shape
    face_numbers(shape, faces, **numbers)           write face numbers on some faces of a Shape
    number(name, value, low, high), clamp(...)      check an option is a number in range, with a plain message
"""

import math

import bpy
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

import _shapes_chapel as shapes

UP = Vector((0.0, 0.0, 1.0))


# ---------------------------------------------------------------------- numbers on points and faces

def number_layers(shape, points=(), faces=()):
    """Make the named point and face number layers of a Shape before any of its points are made (adding a layer to a
    bmesh drops every point and face made before it)."""
    for name in points:
        shape.bm.verts.layers.float.get(name) or shape.bm.verts.layers.float.new(name)
    for name in faces:
        shape.bm.faces.layers.float.get(name) or shape.bm.faces.layers.float.new(name)


def point_numbers(shape, verts, **numbers):
    """Write point numbers (a material reads them through an Attribute node) on the given points of a Shape; make the
    layers first with number_layers()."""
    for name, value in numbers.items():
        layer = shape.bm.verts.layers.float[name]
        for v in verts:
            v[layer] = float(value(v) if callable(value) else value)


def face_numbers(shape, faces, **numbers):
    """Write face numbers on the given faces of a Shape; make the layers first with number_layers()."""
    for name, value in numbers.items():
        layer = shape.bm.faces.layers.float[name]
        for f in faces:
            f[layer] = float(value(f) if callable(value) else value)


# ---------------------------------------------------------------------- a photographed surface, one shade per object

def shaded_surface(name, part, low=0.72, high=1.18, **dials):
    """A copy of a store SURFACE material for one part ('SURFACE • <name> (<part>)', its Weather dials turned), in which
    every object takes its own shade between `low` and `high` times the photograph's (from the object's own random
    number), so planks or rungs that are each their own object never match."""
    material = shapes.surface_copy(name, part, **dials)
    if material.get('pp_shaded'):
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    weather = nodes['Weather']
    principled = nodes.get('Principled BSDF')
    info = nodes.new('ShaderNodeObjectInfo')
    shade = shapes.map_range(nodes, links, info.outputs['Random'], 0.0, 1.0, low, high)
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    links.new(weather.outputs['Base Color'], scale.inputs[0])
    links.new(shade, scale.inputs['Scale'])
    links.new(scale.outputs[0], principled.inputs['Base Color'])
    material['pp_shaded'] = True
    return material


# ---------------------------------------------------------------------- mangold roots

# (z as a share of the length below the crown, radius as a share of the shoulder's): the crown's knob, its flat top,
# the shoulder; the taper below the shoulder is worked out per root
_CROWN = [(-0.022, 0.0), (-0.012, 0.13), (0.0, 0.32), (0.012, 0.62), (0.035, 0.86), (0.07, 0.97)]
# the body: widest a quarter of the way down, narrowing slowly, then a thin whip of a tail (not a sharp horn)
_BODY = [(0.15, 1.0), (0.25, 0.99), (0.37, 0.92), (0.5, 0.79), (0.62, 0.62), (0.72, 0.45), (0.8, 0.3), (0.86, 0.16),
         (0.91, 0.1), (0.955, 0.07), (0.985, 0.045)]


def mangold_rings(length, radius, rng, segments=12):
    """One mangold root in its own frame: the crown at the origin, the root running down -Z for `length` metres, its
    shoulder `radius` metres. Returns (rings, shares): rings of points (the first and last a single point) and each
    ring's share of the length from the crown (the 'tail' number)."""
    stretch = rng.uniform(0.84, 1.04)     # where the body starts to narrow
    tankard = rng.uniform(0.55, 1.0)      # below 1 the body stays fat for longer (a tankard root)
    bend_dir = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0))
    if bend_dir.length < 1e-3:
        bend_dir = Vector((1.0, 0.0, 0.0))
    bend_dir.normalize()
    bend = rng.uniform(0.04, 0.2) * length
    flat = rng.uniform(0.86, 1.0)         # a little oval in section
    phase = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))
    profile = list(_CROWN)
    for (t, r) in _BODY:
        if t < 0.86:
            t = min(0.85, 0.07 + (t - 0.07) * stretch)
            r = r ** tankard
        profile.append((t, r))
    if rng.random() < 0.5:
        # the tail broken off short, as most are when the roots are lifted and carted: a blunt end
        cut = rng.uniform(0.78, 0.9)
        kept = [(t, r) for (t, r) in profile if t < cut]
        last_t, last_r = kept[-1]
        kept.append((cut, last_r * 0.85))
        kept.append((cut + 0.012, 0.0))
        profile = kept
    else:
        profile.append((1.0, 0.0))
    rings, shares = [], []
    for (t, r) in profile:
        z = -t * length
        lean = bend_dir * (bend * max(0.0, (t - 0.35) / 0.65) ** 2)
        if r < 1e-6:
            rings.append([Vector((lean.x, lean.y, z + (0.012 * length if t < 0 else 0.0)))])
            shares.append(max(0.0, t))
            continue
        ring = []
        for j in range(segments):
            a = 2 * math.pi * j / segments
            c, s = math.cos(a), math.sin(a)
            lump = 1.0 + 0.07 * mnoise.noise(Vector((c * 1.6, s * 1.6, t * 7.0)) + phase)
            wrinkle = 1.0 - 0.025 * max(0.0, math.sin(t * 95.0 + phase.x)) ** 6     # faint growth rings
            rr = radius * r * lump * wrinkle
            ring.append(Vector((c * rr + lean.x, s * rr * flat + lean.y, z)))
        rings.append(ring)
        shares.append(max(0.0, t))
    return rings, shares


def mangold(shape, matrix, length, radius, rng, tone=None, segments=12, adjust=None):
    """One mangold root into `shape`: built in its own frame (crown at the origin, root down -Z) and placed by `matrix`.
    `adjust(points)` may return a Vector to move the whole root by (to keep it off a wall or out of the ground).
    Writes the point numbers 'tail' and 'root_tone'. Returns the root's placed points."""
    rings, shares = mangold_rings(length, radius, rng, segments)
    placed = [[matrix @ p for p in ring] for ring in rings]
    if adjust is not None:
        shift = adjust([p for ring in placed for p in ring])
        if shift is not None and shift.length > 0:
            placed = [[p + shift for p in ring] for ring in placed]
    # the layers first: adding a layer to a bmesh drops every point made before it
    tail_layer = shape.bm.verts.layers.float.get('tail') or shape.bm.verts.layers.float.new('tail')
    tone_layer = shape.bm.verts.layers.float.get('root_tone') or shape.bm.verts.layers.float.new('root_tone')
    verts = [shape._verts(ring) for ring in placed]
    shape._rings(verts, True, False, False)
    tone = rng.random() if tone is None else tone
    for ring, share in zip(verts, shares):
        for v in ring:
            v[tail_layer] = share
            v[tone_layer] = tone
    return [p for ring in placed for p in ring]


def root_frame(axis, roll=0.0):
    """A rotation that turns a root built down -Z so it runs along `axis` (crown to tail), rolled `roll` radians."""
    r = shapes.frame_along(-Vector(axis))
    return r @ Matrix.Rotation(roll, 3, 'Z')


def mangold_material(part):
    """Mangolds lifted a week ago: each root its own dull orange-yellow to red, darker and browner on the shoulder that
    grew above the soil, faint dark growth rings, soil caked on the tail and in patches (dull where soiled, a little
    sheen where clean). Reads the point numbers 'tail' and 'root_tone'. 'PART • <part>: mangold, soiled'."""
    def maker(m, nodes, links, principled):
        tail = nodes.new('ShaderNodeAttribute')
        tail.attribute_name = 'tail'
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_name = 'root_tone'
        vec = shapes.own_coordinates(nodes)
        t = tone.outputs['Fac']
        skin = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, t, 0.0, 0.45), (0.165, 0.08, 0.019), (0.135, 0.038, 0.013))
        skin = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, t, 0.45, 1.0), skin, (0.085, 0.015, 0.013))
        mottle = shapes.noise_fac(nodes, links, vec, 22.0, detail=3.0)
        skin = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, mottle, 0.35, 0.7, 0.0, 0.5), skin,
                                 (0.055, 0.02, 0.01))
        crown = shapes.map_range(nodes, links, tail.outputs['Fac'], 0.04, 0.17, 0.85, 0.0)
        colour = shapes.mix_colour(nodes, links, crown, skin, (0.045, 0.036, 0.017))
        patch = shapes.noise_fac(nodes, links, vec, 11.0, detail=5.0, roughness=0.6)
        soil = shapes.math_node(nodes, links, 'ADD', shapes.map_range(nodes, links, tail.outputs['Fac'], 0.38, 0.72),
                                shapes.map_range(nodes, links, patch, 0.58, 0.74, 0.0, 0.8), clamp=True)
        colour = shapes.mix_colour(nodes, links, soil, colour, (0.03, 0.021, 0.013))
        links.new(colour, principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, soil, 0.0, 1.0, 0.62, 0.95), principled.inputs['Roughness'])
        principled.inputs['Specular IOR Level'].default_value = 0.35
        grit = shapes.noise_fac(nodes, links, vec, 70.0, detail=3.0)
        lumps = shapes.bump(nodes, links, patch, 0.35, 0.006)
        links.new(shapes.bump(nodes, links, grit, 0.25, 0.002, normal=lumps), principled.inputs['Normal'])
        m.diffuse_color = (0.12, 0.045, 0.02, 1.0)
    return shapes.part_material(part, 'mangold, soiled', maker)


# ---------------------------------------------------------------------- small things

def clamp(value, low, high):
    return max(low, min(high, value))


def number(name, value, low=None, high=None):
    """An option that must be a number (within low..high if given): stops with a plain message otherwise."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError('%s must be a number, not %r' % (name, value))
    if (low is not None and v < low) or (high is not None and v > high):
        raise ValueError('%s must be between %s and %s, not %r' % (name, low, high, value))
    return v
