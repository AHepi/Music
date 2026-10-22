# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE PIECE LIBRARY (Blender code): the small separate 3D weeds and moss cushions that the scatter (scatter.py) stands on the ground. Sizes, shares, colours and where each kind
# likes to grow are DATA in species.json; this file only knows how to build each SHAPE (a tuft of bent blades, a toothed rosette, a broad-leaved rosette, a stalk with lobed
# leaves, a mat of paired leaves, a leafy rosette with a flower spike, a trailing stem, a star cushion, a string of lumpy moss cushions).
# Every piece has 40 to 200 ragged faces (the first rubbish pieces "looked like gems and matchsticks": too few facets), a random lean, bent blades and its own random shape: each
# kind is built in several VARIANTS spread over the kind's size range, and the scatter picks one at random for every plant.
# Pieces are objects in ONE collection that is NOT linked to the scene (only the scatter's Collection Info node uses it), origin at the foot of the plant, z up, 1 unit = 1 metre.
# Materials (one per colour name of the palette): a Principled BSDF with no coat; the colour is the dry colour times a small per-plant random tint (instance attribute `tint`),
# turned richer and darker by the WET value (a Value node named WET in every material; set_wetness() moves them all) and the `wet_dark` dial; the surface gets a little glossier
# when wet (roughness 0.72 to 0.46), never a coat. A second Value node, GAIN, multiplies the colour (the `colour_gain` dial, for tuning the plate brightness).
# `set_mask_view(True)` turns every piece into plain white light (the checking view `layer:growth` uses it, everything else is blacked out by the caller).
import json
import math
import os
import random

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SPECIES_PATH = os.path.join(HERE, 'species.json')
COLLECTION_NAME = 'WKG pieces'
MATERIAL_PREFIX = 'WKG '
OBJECT_PREFIX = 'WKG_'


def load_species(path=SPECIES_PATH):
    with open(path) as handle:
        return json.load(handle)


# ------------------------------------------------------------------------------------------------------------------------------ colours and materials
def srgb_to_linear(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 5.5e-2) / 1.055) ** 2.4


def lin(rgb):
    return (srgb_to_linear(rgb[0]), srgb_to_linear(rgb[1]), srgb_to_linear(rgb[2]), 1.0)


class Materials:
    """The piece materials of one library (one per palette colour). wet_nodes / gain_nodes / dark_nodes are all the Value nodes the set_* functions move."""

    def __init__(self, species):
        self.species = species
        self.by_colour = {}
        self.wet_nodes, self.gain_nodes, self.dark_nodes = [], [], []

    def get(self, colour_name):
        if colour_name in self.by_colour:
            return self.by_colour[colour_name]
        spec = self.species['material']
        rgb = self.species['palette'][colour_name]
        material = bpy.data.materials.new(MATERIAL_PREFIX + colour_name)
        material.use_nodes = True
        tree = material.node_tree
        for node in list(tree.nodes):
            if node.type != 'OUTPUT_MATERIAL':
                tree.nodes.remove(node)
        output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
        principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
        tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        principled.inputs['Coat Weight'].default_value = 0.0
        principled.inputs['Metallic'].default_value = 0.0

        def value(name, default):
            node = tree.nodes.new('ShaderNodeValue')
            node.name, node.label = name, name
            node.outputs[0].default_value = default
            return node

        wet = value('WET', 0.0)
        gain = value('GAIN', 1.0)
        sat = value('SAT', 1.0)
        dark = value('WET_DARK', 0.7)
        self.wet_nodes.append(wet)
        self.gain_nodes.append(gain)
        self.dark_nodes.append(dark)
        # per-plant values from the instance attributes the scatter stores (a missing attribute reads 0)
        tint = tree.nodes.new('ShaderNodeAttribute')
        tint.attribute_type, tint.attribute_name = 'INSTANCER', 'tint'
        wetmod = tree.nodes.new('ShaderNodeAttribute')
        wetmod.attribute_type, wetmod.attribute_name = 'INSTANCER', 'damp'

        def math(op, a, b=None, clamp=False):
            node = tree.nodes.new('ShaderNodeMath')
            node.operation, node.use_clamp = op, clamp
            for index, item in enumerate((a, b)):
                if item is None:
                    continue
                if isinstance(item, bpy.types.NodeSocket):
                    tree.links.new(item, node.inputs[index])
                else:
                    node.inputs[index].default_value = item
            return node.outputs[0]

        spread = spec.get('tint_spread', 0.14)
        tint_mul = math('ADD', math('MULTIPLY', math('SUBTRACT', tint.outputs['Fac'], 0.5), 2.0 * spread), 1.0)          # 1 +- spread (0.5 when the attribute is missing: x1)
        wet_eff = math('MULTIPLY', wet.outputs[0], math('ADD', 0.75, math('MULTIPLY', wetmod.outputs['Fac'], 0.5)), clamp=True)   # the wetter, damper spots wetter
        value_mul = math('MULTIPLY', math('MULTIPLY', tint_mul, gain.outputs[0]), math('MAXIMUM', 0.25, math('ADD', 1.0, math('MULTIPLY', wet_eff, math('MULTIPLY', math('SUBTRACT', dark.outputs[0], 1.0), spec.get('wet_dark_boost', 1.0))))))
        hsv = tree.nodes.new('ShaderNodeHueSaturation')
        hsv.inputs['Color'].default_value = lin(rgb)
        tree.links.new(value_mul, hsv.inputs['Value'])
        tree.links.new(math('MULTIPLY', sat.outputs[0], math('ADD', 1.0, math('MULTIPLY', wet_eff, spec.get('wet_saturation', 1.18) - 1.0))), hsv.inputs['Saturation'])
        tree.links.new(hsv.outputs['Color'], principled.inputs['Base Color'])
        rough = math('ADD', spec['rough_dry'], math('MULTIPLY', wet_eff, spec['rough_wet'] - spec['rough_dry']))
        tree.links.new(rough, principled.inputs['Roughness'])
        tree.links.new(math('ADD', spec['specular_dry'], math('MULTIPLY', wet_eff, spec['specular_wet'] - spec['specular_dry'])), principled.inputs['Specular IOR Level'])
        material['wk_hsv'] = hsv.name
        self.by_colour[colour_name] = material
        return material


def set_wetness(wet, materials=None):
    for material in (materials or [m for m in bpy.data.materials if m.name.startswith(MATERIAL_PREFIX)]):
        node = material.node_tree.nodes.get('WET') if material.node_tree else None
        if node is not None:
            node.outputs[0].default_value = float(wet)


def set_value_node(name, value):
    count = 0
    for material in bpy.data.materials:
        if material.name.startswith(MATERIAL_PREFIX) and material.node_tree is not None:
            node = material.node_tree.nodes.get(name)
            if node is not None:
                node.outputs[0].default_value = float(value)
                count += 1
    return count


def set_mask_view(on):
    """Every piece material shows plain white light (on) or its own surface (off). Used by the checking view; the caller blacks out everything else."""
    for material in bpy.data.materials:
        if not material.name.startswith(MATERIAL_PREFIX) or material.node_tree is None:
            continue
        tree = material.node_tree
        output = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        principled = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if output is None or principled is None:
            continue
        existing = tree.nodes.get('WKG VIEW')
        if on and existing is None:
            emission = tree.nodes.new('ShaderNodeEmission')
            emission.name = 'WKG VIEW'
            emission.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            emission.inputs['Strength'].default_value = 1.0
            tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        elif not on and existing is not None:
            tree.nodes.remove(existing)
            tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])


# ------------------------------------------------------------------------------------------------------------------------------ a tiny mesh maker
class Mesher:
    def __init__(self):
        self.v, self.f, self.m = [], [], []

    def vert(self, p):
        self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.v) - 1

    def face(self, idx, mat=0):
        self.f.append(tuple(idx))
        self.m.append(mat)

    def extent(self):
        xs, ys, zs = zip(*self.v)
        return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def _dir(phi, theta):
    """A unit direction at azimuth phi, angle theta from straight up."""
    return Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))


def _lift(p, floor=0.0006):
    return Vector((p.x, p.y, max(p.z, floor)))


def add_strip(M, rng, centre, phi, theta0, bend, length, width_at, segs, mat=0, fold=0.25, teeth=0.0, tooth_flip=False, jag=0.0):
    """A ragged leaf or blade: a strip of `segs` stations along a curved centreline; width_at(t) is the full width at t 0..1; across the strip a fold along the middle (V) gives it
    two faces per station; `teeth` pulls alternate stations of the two edges in (a toothed leaf); jag randomly moves edge points. The tip is one point. Returns the vertex rows."""
    side = Vector((-math.sin(phi), math.cos(phi), 0.0))
    p = Vector(centre)
    rows = []
    for i in range(segs + 1):
        t = i / segs
        th = theta0 + bend * t
        d = _dir(phi, th)
        w = width_at(t)
        if i == segs:
            rows.append((M.vert(_lift(p)),))
            break
        nrm = side.cross(d)
        nrm = nrm.normalized() if nrm.length > 1e-6 else Vector((0, 0, 1))
        wl = wr = w * 0.5
        if teeth > 0.0:
            odd = (i % 2 == 1) != tooth_flip
            wl *= (1.0 - teeth) if odd else 1.0
            wr *= 1.0 if odd else (1.0 - teeth)
        if jag > 0.0:
            wl *= 1.0 + rng.uniform(-jag, jag)
            wr *= 1.0 + rng.uniform(-jag, jag)
        rows.append((M.vert(_lift(p - side * wl)), M.vert(_lift(p + nrm * (w * fold))), M.vert(_lift(p + side * wr))))
        p = p + d * (length / segs)
    for i in range(segs - 1):
        a, b = rows[i], rows[i + 1]
        M.face((a[0], a[1], b[1], b[0]), mat)
        M.face((a[1], a[2], b[2], b[1]), mat)
    a, tip = rows[segs - 1], rows[segs][0]
    M.face((a[0], a[1], tip), mat)
    M.face((a[1], a[2], tip), mat)
    return rows


def add_tube(M, pts, radii, sides=3, mat=0, cap=True):
    """A thin stalk: rings of `sides` points round a polyline (the stalk leans, so rings are flat in z), quads between rings, a point at the top."""
    rings = []
    for k, (p, r) in enumerate(zip(pts, radii)):
        rings.append([M.vert(Vector((p.x + r * math.cos(2 * math.pi * s / sides), p.y + r * math.sin(2 * math.pi * s / sides), p.z))) for s in range(sides)])
    for a, b in zip(rings[:-1], rings[1:]):
        for s in range(sides):
            M.face((a[s], a[(s + 1) % sides], b[(s + 1) % sides], b[s]), mat)
    if cap:
        top = M.vert(pts[-1] + Vector((0, 0, radii[-1] * 1.5)))
        for s in range(sides):
            M.face((rings[-1][s], rings[-1][(s + 1) % sides], top), mat)


def add_disc(M, centre, radius, n, rng, mat=0, rise=0.0, jag=0.25, spikes=False):
    """A flat or slightly conical disc of n triangles (a flower head, a seed-clock when spikes=True: thin radial spikes)."""
    c = M.vert(centre + Vector((0, 0, rise)))
    ring = []
    for s in range(n):
        a = 2 * math.pi * s / n + rng.uniform(-0.1, 0.1)
        r = radius * (1.0 + rng.uniform(-jag, jag))
        ring.append(M.vert(centre + Vector((r * math.cos(a), r * math.sin(a), -0.2 * rise if not spikes else rise * rng.uniform(-0.6, 0.6)))))
    for s in range(n):
        M.face((c, ring[s], ring[(s + 1) % n]), mat)


def add_leaf_fan(M, base, phi, length, width, lift, rng, mat=0, droop=0.0):
    """A small roundish leaf (4 corners and a tip): 2 triangles; lies nearly flat, tipped up by `lift` radians."""
    d = Vector((math.cos(phi), math.sin(phi), math.sin(lift)))
    d = d.normalized()
    side = Vector((-math.sin(phi), math.cos(phi), 0.0))
    b = M.vert(_lift(base))
    ml = M.vert(_lift(base + d * (length * 0.5) - side * (width * 0.5)))
    mr = M.vert(_lift(base + d * (length * 0.5) + side * (width * 0.5)))
    tip = M.vert(_lift(base + d * length + Vector((0, 0, -droop))))
    M.face((b, ml, tip), mat)
    M.face((b, tip, mr), mat)


def add_pentagon_leaf(M, base, phi, radius, lift, rng, mat=0):
    """A round, ivy-shaped leaf (5 points round a centre) as 5 triangles, tilted by `lift`."""
    c = Vector(base)
    n = Vector((math.sin(lift) * math.cos(phi), math.sin(lift) * math.sin(phi), math.cos(lift)))
    ax = Vector((-math.sin(phi), math.cos(phi), 0.0))
    ay = n.cross(ax)
    cv = M.vert(_lift(c + n * radius * 0.25))
    ring = [M.vert(_lift(c + ax * math.cos(2 * math.pi * s / 5) * radius * (1 + rng.uniform(-0.2, 0.2)) + ay * math.sin(2 * math.pi * s / 5) * radius * (1 + rng.uniform(-0.2, 0.2)))) for s in range(5)]
    for s in range(5):
        M.face((cv, ring[s], ring[(s + 1) % 5]), mat)


def add_dome(M, centre, radius, height, rng, segs=10, rings=3, mat=0, lumpy=0.22):
    """A lumpy dome (a moss cushion or a star cushion's body): `rings` rings of `segs` points, a top point, ragged outline."""
    ring_ids = []
    for k in range(rings):
        t = k / float(rings)
        rr = radius * math.cos(t * math.pi / 2.3)
        zz = height * math.sin(t * math.pi / 2.0) ** 0.8
        ids = []
        for s in range(segs):
            a = 2 * math.pi * (s + 0.5 * (k % 2)) / segs
            r = rr * (1.0 + rng.uniform(-lumpy, lumpy))
            ids.append(M.vert(Vector((centre.x + r * math.cos(a), centre.y + r * math.sin(a), centre.z + zz * (1.0 + rng.uniform(-lumpy, lumpy) * 0.6) + (0.0004 if k == 0 else 0.0)))))
        ring_ids.append(ids)
    top = M.vert(Vector((centre.x + rng.uniform(-0.15, 0.15) * radius, centre.y + rng.uniform(-0.15, 0.15) * radius, centre.z + height * (1.0 + rng.uniform(-0.1, 0.1)))))
    for a, b in zip(ring_ids[:-1], ring_ids[1:]):
        for s in range(segs):
            M.face((a[s], a[(s + 1) % segs], b[(s + 1) % segs], b[s]), mat)
    for s in range(segs):
        M.face((ring_ids[-1][s], ring_ids[-1][(s + 1) % segs], top), mat)


# ------------------------------------------------------------------------------------------------------------------------------ the shapes
def _between(rng, pair):
    lo, hi = pair
    return rng.uniform(lo, hi)


def _int_between(rng, pair):
    return rng.randint(int(pair[0]), int(pair[1]))


def build_tuft(spec, size_m, rng, variant, with_flowers=True):
    """Meadow-grass tuft: 10 to 16 bent blades from one base; some tufts also send up 1 to 3 thin flowering stems with a feathery head; a dead tuft droops more and is straw-coloured."""
    p = spec['params']
    M = Mesher()
    blades = _int_between(rng, p['blades'])
    for k in range(blades):
        phi = rng.uniform(0, 2 * math.pi)
        theta0 = rng.uniform(0.05, 0.55)
        length = size_m * rng.uniform(0.55, 1.0)
        width = size_m * rng.uniform(0.10, 0.17)
        bend = _between(rng, p['droop']) * rng.uniform(0.6, 1.2)
        base = Vector((rng.uniform(-0.1, 0.1) * size_m * 0.4, rng.uniform(-0.1, 0.1) * size_m * 0.4, 0.0))
        add_strip(M, rng, base, phi, theta0, bend, length, lambda t, w=width: w * (1.0 - t ** 1.6), 4, mat=0, fold=0.3, jag=0.12)
    if with_flowers and rng.random() < p.get('flower_share', 0.0) * 2.0 and not p.get('dead'):
        for k in range(rng.randint(1, 3)):
            phi = rng.uniform(0, 2 * math.pi)
            h = size_m * rng.uniform(1.0, 1.5)
            lean = rng.uniform(0.05, 0.3)
            pts = [Vector((math.sin(lean) * math.cos(phi) * h * t, math.sin(lean) * math.sin(phi) * h * t, h * t)) for t in (0.0, 0.3, 0.6, 0.85)]
            add_tube(M, pts, [size_m * 0.012, size_m * 0.010, size_m * 0.008, size_m * 0.006], sides=3, mat=1, cap=False)
            top = pts[-1]
            for s in range(5):                                      # a feathery head: small spikelets drooping off the top of the stem
                a = phi + rng.uniform(-1.2, 1.2)
                tip = top + Vector((math.cos(a) * size_m * 0.25, math.sin(a) * size_m * 0.25, size_m * rng.uniform(0.05, 0.3)))
                v0, v1, v2 = M.vert(top), M.vert(top + Vector((0.0, 0.0, size_m * 0.05)) + Vector((-math.sin(a), math.cos(a), 0)) * size_m * 3.5e-2), M.vert(tip)
                M.face((v0, v1, v2), 1)
    return M


def build_cushion_star(spec, size_m, rng, variant):
    """Pearlwort: a low dome of tiny leaves (a lumpy dome) with a ring of thin needle leaves spreading from the top."""
    p = spec['params']
    M = Mesher()
    radius = size_m * 0.5
    add_dome(M, Vector((0, 0, 0)), radius, radius * 0.5, rng, segs=12, rings=3, mat=0, lumpy=0.18)
    for k in range(_int_between(rng, p['needles'])):
        a = rng.uniform(0, 2 * math.pi)
        r0 = radius * rng.uniform(0.15, 0.6)
        base = Vector((r0 * math.cos(a), r0 * math.sin(a), radius * rng.uniform(0.3, 0.5)))
        out = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((-math.sin(a), math.cos(a), 0.0))
        tip = base + out * radius * rng.uniform(0.5, 0.9) + Vector((0, 0, radius * rng.uniform(-0.1, 0.35)))
        w = radius * 0.16
        M.face((M.vert(base - side * w), M.vert(base + side * w), M.vert(_lift(tip))), 0)
    return M


def _toothed_leaf(M, rng, centre, phi, elevation, length, width, mat, bend, teeth=0.5, segs=7, profile=None, flip=False):
    theta0 = math.pi / 2 - elevation                  # elevation above horizontal -> angle from straight up
    prof = profile or (lambda t: math.sin(math.pi * min(1.0, t ** 0.75)) * (0.25 + 0.75 * t) ** 0.5)
    return add_strip(M, rng, centre, phi, theta0, bend, length, lambda t: width * prof(t), segs, mat=mat, fold=0.18, teeth=teeth, tooth_flip=flip, jag=0.08)


def build_rosette_toothed(spec, size_m, rng, variant, flower=None):
    """Dandelion: 9 to 13 long, deeply toothed leaves lying out from a centre; a few variants carry a flower (yellow disc on a stalk) or a seed-clock (pale ball of spikes)."""
    p = spec['params']
    M = Mesher()
    n = _int_between(rng, p['leaves'])
    for k in range(n):
        phi = 2 * math.pi * k / n + rng.uniform(-0.25, 0.25)
        elev = rng.uniform(0.12, 0.6)
        length = size_m * 0.62 * rng.uniform(0.75, 1.0)
        width = length * rng.uniform(0.28, 0.4)
        _toothed_leaf(M, rng, Vector((0, 0, 0.002)), phi, elev, length, width, 0, bend=-rng.uniform(0.2, 0.9), teeth=0.5, flip=bool(k % 2))
    if flower:
        h = size_m * rng.uniform(0.45, 0.9)
        lean = rng.uniform(0.05, 0.35)
        phi = rng.uniform(0, 2 * math.pi)
        pts = [Vector((math.sin(lean) * math.cos(phi) * h * t, math.sin(lean) * math.sin(phi) * h * t, h * t)) for t in (0.0, 0.33, 0.66, 1.0)]
        add_tube(M, pts, [size_m * 0.018] * 3 + [size_m * 0.014], sides=3, mat=1, cap=False)
        if flower == 'flower':
            add_disc(M, pts[-1], size_m * 0.17, 14, rng, mat=1, rise=size_m * 0.06)
        else:
            add_disc(M, pts[-1] + Vector((0, 0, size_m * 0.08)), size_m * 0.2, 26, rng, mat=2, rise=size_m * 0.1, spikes=True)
    return M


def build_rosette_broad(spec, size_m, rng, variant):
    """Greater plantain: 6 to 9 broad ribbed oval leaves standing up and out from a centre (five points across a leaf give the ribs)."""
    p = spec['params']
    M = Mesher()
    n = _int_between(rng, p['leaves'])
    for k in range(n):
        phi = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        elev = rng.uniform(0.35, 1.05)
        length = size_m * 0.8 * rng.uniform(0.75, 1.0)
        width = length * rng.uniform(0.42, 0.6)
        theta0 = math.pi / 2 - elev
        bend = -rng.uniform(0.3, 0.9)
        side = Vector((-math.sin(phi), math.cos(phi), 0.0))
        centre = Vector((0, 0, 0.002))
        segs = 5
        rows = []
        pcur = Vector(centre)
        for i in range(segs + 1):
            t = i / segs
            th = theta0 + bend * t
            d = _dir(phi, th)
            if i == segs:
                rows.append([M.vert(_lift(pcur))])
                break
            w = width * (math.sin(math.pi * min(1.0, 0.12 + 0.88 * t ** 0.8)) ** 0.8) * (0.3 if t < 0.12 else 1.0)
            nrm = side.cross(d)
            nrm = nrm.normalized() if nrm.length > 1e-6 else Vector((0, 0, 1))
            row = []
            for u, lift in ((-1.0, 0.0), (-0.5, 0.10), (0.0, -0.03), (0.5, 0.10), (1.0, 0.0)):
                row.append(M.vert(_lift(pcur + side * (u * w * 0.5 * (1.0 + rng.uniform(-0.05, 0.05))) + nrm * (lift * w))))
            rows.append(row)
            pcur = pcur + d * (length / segs)
        for i in range(segs - 1):
            for c in range(4):
                M.face((rows[i][c], rows[i][c + 1], rows[i + 1][c + 1], rows[i + 1][c]), 0)
        last, tip = rows[segs - 1], rows[segs][0]
        for c in range(4):
            M.face((last[c], last[c + 1], tip), 0)
    return M


def build_groundsel(spec, size_m, rng, variant):
    """Groundsel: an upright stem with alternate lobed leaves and a little crowd of yellow-green flower buds on top."""
    p = spec['params']
    M = Mesher()
    h = size_m
    lean = rng.uniform(0.0, 0.18)
    phi0 = rng.uniform(0, 2 * math.pi)
    pts = [Vector((math.sin(lean) * math.cos(phi0) * h * t, math.sin(lean) * math.sin(phi0) * h * t, h * t)) for t in (0.0, 0.2, 0.4, 0.6, 0.8, 0.95)]
    add_tube(M, pts, [h * 2.2e-2, h * 0.02, h * 0.018, h * 1.6e-2, h * 1.3e-2, h * 0.01], sides=4, mat=0, cap=False)
    pairs = _int_between(rng, p['pairs'])
    for k in range(pairs):
        t = 0.08 + 0.8 * k / max(1, pairs - 1)
        node = Vector((math.sin(lean) * math.cos(phi0) * h * t, math.sin(lean) * math.sin(phi0) * h * t, h * t))
        for sign in (0, 1):
            phi = phi0 + k * 1.9 + sign * math.pi + rng.uniform(-0.3, 0.3)
            length = h * 0.32 * (1.0 - 0.6 * t) * rng.uniform(0.8, 1.15)
            _toothed_leaf(M, rng, node, phi, rng.uniform(0.1, 0.7), length, length * 0.5, 0, bend=-rng.uniform(0.2, 0.8), teeth=0.45, segs=3, flip=bool(sign))
    top = pts[-1]
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        c = top + Vector((math.cos(a) * h * 0.06, math.sin(a) * h * 0.06, h * rng.uniform(0.0, 0.07)))
        add_disc(M, c, h * 0.05, 5, rng, mat=1, rise=h * 0.06, jag=0.2)
    return M


def build_mat_leaves(spec, size_m, rng, variant):
    """Chickweed: a loose spreading mat of 5 to 8 trailing stems, each with 3 to 5 pairs of small oval leaves lying nearly flat."""
    p = spec['params']
    M = Mesher()
    stems = _int_between(rng, p['stems'])
    for k in range(stems):
        phi = 2 * math.pi * k / stems + rng.uniform(-0.4, 0.4)
        reach = size_m * 0.5 * rng.uniform(0.5, 1.0)
        pairs = _int_between(rng, p['pairs'])
        for q in range(pairs):
            t = (q + 1.0) / pairs
            wob = rng.uniform(-0.25, 0.25)
            base = Vector((math.cos(phi + wob * t) * reach * t, math.sin(phi + wob * t) * reach * t, 4e-3 + 0.006 * rng.random()))
            leaf_len = size_m * rng.uniform(8.5e-2, 0.13)
            for side in (-1, 1):
                add_leaf_fan(M, base, phi + side * rng.uniform(0.9, 1.5), leaf_len, leaf_len * rng.uniform(0.55, 0.8), rng.uniform(0.05, 0.5), rng, mat=0, droop=0.002)
    for k in range(rng.randint(5, 9)):                          # a crowd of leaves at the centre
        add_leaf_fan(M, Vector((0, 0, 4e-3)), rng.uniform(0, 2 * math.pi), size_m * rng.uniform(0.09, 0.13), size_m * 0.07, rng.uniform(0.2, 0.9), rng, mat=0)
    return M


def build_rosette_spike(spec, size_m, rng, variant, spike=None):
    """Shepherd's purse: 6 to 8 deeply lobed leaves lying out, and (on some plants) a thin flower spike 20 to 30 cm tall carrying small flat heart-shaped seed pods."""
    p = spec['params']
    M = Mesher()
    n = _int_between(rng, p['leaves'])
    for k in range(n):
        phi = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        length = size_m * 0.5 * rng.uniform(0.7, 1.0)
        _toothed_leaf(M, rng, Vector((0, 0, 0.002)), phi, rng.uniform(0.1, 0.5), length, length * 0.3, 0, bend=-rng.uniform(0.1, 0.6), teeth=0.6, segs=9, flip=bool(k % 2))
    if spike:
        h = spike
        lean = rng.uniform(0.02, 0.15)
        phi = rng.uniform(0, 2 * math.pi)
        pts = [Vector((math.sin(lean) * math.cos(phi) * h * t, math.sin(lean) * math.sin(phi) * h * t, h * t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        add_tube(M, pts, [h * 0.011, h * 0.010, h * 0.008, h * 7e-3, h * 0.005], sides=3, mat=1, cap=True)
        for k in range(8):
            t = 0.35 + 0.6 * k / 7.0
            c = Vector((math.sin(lean) * math.cos(phi) * h * t, math.sin(lean) * math.sin(phi) * h * t, h * t))
            a = phi + k * 2.2
            out = Vector((math.cos(a), math.sin(a), 0.0))
            w = h * 3.5e-2
            v0 = M.vert(c)
            v1 = M.vert(c + out * h * 0.05 + Vector((0, 0, w)))
            v2 = M.vert(c + out * h * 0.05 + Vector((0, 0, -w)))
            M.face((v0, v1, v2), 1)
    return M


def build_trail(spec, size_m, rng, variant, flowers=True):
    """Ivy-leaved toadflax: 3 to 5 trailing stems along a damp wall foot, each with 5 to 7 small round lobed leaves and a few lilac flower specks."""
    p = spec['params']
    M = Mesher()
    stems = _int_between(rng, p['stems'])
    base_phi = rng.uniform(0, 2 * math.pi)
    for k in range(stems):
        phi = base_phi + rng.uniform(-0.9, 0.9)
        reach = size_m * rng.uniform(0.5, 1.0)
        n = _int_between(rng, p['leaves_per_stem'])
        for q in range(n):
            t = (q + 0.6) / n
            c = Vector((math.cos(phi + 0.25 * math.sin(3 * t)) * reach * t, math.sin(phi + 0.25 * math.sin(3 * t)) * reach * t, 4e-3 + 0.01 * t))
            add_pentagon_leaf(M, c, rng.uniform(0, 2 * math.pi), size_m * rng.uniform(0.04, 0.06), rng.uniform(0.0, 0.6), rng, mat=0)
            if flowers and rng.random() < 0.3:
                add_disc(M, c + Vector((0, 0, 0.006)), size_m * 0.018, 4, rng, mat=1, rise=0.003)
    return M


def build_cushion_string(spec, size_m, rng, variant):
    """Moss: 2 to 4 lumpy domed cushions (1 to 3 cm across, 0.5 to 1 cm high) in a short line along a joint, touching or nearly, slightly different in size, with a few tiny lumps between."""
    p = spec['params']
    M = Mesher()
    count = _int_between(rng, p['cushions'])
    x = 0.0
    sizes = []
    for k in range(count):
        r = _between(rng, p['radius_cm']) * 0.01 * (0.8 + 0.4 * size_m / 0.02)
        sizes.append(r)
    total = sum(2.0 * r * 0.85 for r in sizes)
    x = -total / 2.0
    for k, r in enumerate(sizes):
        x += r * 0.85
        c = Vector((x, rng.uniform(-0.3, 0.3) * r, 0.0))
        h = min(_between(rng, p['height_cm']) * 0.01, r * 0.9)
        add_dome(M, c, r, h, rng, segs=10, rings=3, mat=0, lumpy=0.22)
        if rng.random() < 0.7:                                      # a small lump riding on the cushion's shoulder
            add_dome(M, c + Vector((rng.uniform(-0.5, 0.5) * r, rng.uniform(-0.5, 0.5) * r, h * 0.35)), r * 0.4, h * 0.5, rng, segs=6, rings=2, mat=0, lumpy=0.2)
        x += r * 0.85
    return M


# ------------------------------------------------------------------------------------------------------------------------------ the library
BUILDERS = {'tuft': build_tuft, 'cushion_star': build_cushion_star, 'rosette_toothed': build_rosette_toothed, 'rosette_broad': build_rosette_broad, 'groundsel': build_groundsel,
            'mat_leaves': build_mat_leaves, 'rosette_spike': build_rosette_spike, 'trail': build_trail, 'cushion_string': build_cushion_string}


def _size_of(spec, index, count, rng):
    lo, hi = spec['size_cm']
    t = (index + rng.uniform(0.15, 0.85)) / float(count)
    return (lo + (hi - lo) * t) * 0.01


def build_variant(name, spec, index, rng):
    """The Mesher of one variant of one kind (not yet an object)."""
    size = _size_of(spec, index, spec['variants'], rng)
    builder = spec['builder']
    if builder == 'rosette_toothed':
        flower = None
        if index == spec['variants'] - 2:
            flower = 'flower'
        elif index == spec['variants'] - 1:
            flower = 'seed'
        return BUILDERS[builder](spec, size, rng, index, flower=flower), size, flower
    if builder == 'rosette_spike':
        spike = None
        if rng.random() < spec['params'].get('spike_share', 0.5) and index >= 1:
            spike = _between(rng, spec['spike_cm']) * 0.01
        return BUILDERS[builder](spec, size, rng, index, spike=spike), size, spike
    return BUILDERS[builder](spec, size, rng, index), size, None


def material_names_of(spec, extra):
    """The palette colour of each material slot of a variant: slot 0 the leaf (or cushion), slot 1 the stem, head, flower or pod, slot 2 the seed-clock."""
    slots = [spec['colour']]
    second = spec.get('head') or spec.get('flower') or spec.get('pod') or spec.get('stem') or spec.get('colour_light') or spec['colour']
    slots.append(second)
    slots.append(spec.get('seed') or second)
    return slots


class Library:
    """Everything built for one kit: the materials, the collection and a table of the kinds {name: dict(collection objects, mean width, mean footprint, faces)}."""

    def __init__(self, species=None, seed=7):
        self.species = species or load_species()
        self.seed = seed
        self.materials = Materials(self.species)
        self.collection = None
        self.kinds = {}
        self.objects = []
        self.meshes = []

    def build(self, kinds=None):
        names = kinds or list(self.species['kinds'])
        self.collection = None
        self.kind_collections = {}
        for name in names:
            spec = self.species['kinds'][name]
            rng = random.Random(self.seed * 1000 + sum(ord(c) for c in name))
            col = bpy.data.collections.new(f'{COLLECTION_NAME} {name}')
            self.kind_collections[name] = col
            info = dict(collection=col, objects=[], faces=[], widths=[], heights=[], footprints=[], spec=spec)
            for index in range(spec['variants']):
                mesher, size, extra = build_variant(name, spec, index, rng)
                w, d, h, lo, hi = mesher.extent()
                mesh = bpy.data.meshes.new(f'{OBJECT_PREFIX}{name}_{index:02d}')
                mesh.from_pydata(mesher.v, [], mesher.f)
                mesh.update()
                slots = material_names_of(spec, extra)
                used = sorted(set(mesher.m))
                remap = {slot: i for i, slot in enumerate(used)}
                for slot in used:
                    mesh.materials.append(self.materials.get(slots[slot]))
                for poly, slot in zip(mesh.polygons, mesher.m):
                    poly.material_index = remap[slot]
                    poly.use_smooth = False
                obj = bpy.data.objects.new(mesh.name, mesh)
                obj['wk_kind'] = name
                obj['wk_variant'] = index
                obj['wk_size_m'] = size
                obj['wk_width_m'] = max(w, d)
                obj['wk_height_m'] = h
                col.objects.link(obj)
                info['objects'].append(obj)
                info['faces'].append(len(mesh.polygons))
                info['widths'].append(max(w, d))
                info['heights'].append(h)
                info['footprints'].append(math.pi / 4.0 * w * d)
                self.objects.append(obj)
                self.meshes.append(mesh)
            info['mean_width'] = sum(info['widths']) / len(info['widths'])
            info['mean_footprint'] = sum(info['footprints']) / len(info['footprints'])
            self.kinds[name] = info
        return self.kinds

    def face_counts(self):
        return {k: (min(v['faces']), max(v['faces'])) for k, v in self.kinds.items()}

    def remove(self):
        for obj in self.objects:
            if bpy.data.objects.get(obj.name) is obj:
                bpy.data.objects.remove(obj)
        for mesh in self.meshes:
            if bpy.data.meshes.get(mesh.name) is mesh:
                bpy.data.meshes.remove(mesh)
        for col in list(getattr(self, 'kind_collections', {}).values()):
            if bpy.data.collections.get(col.name) is col:
                bpy.data.collections.remove(col)
        for material in list(self.materials.by_colour.values()):
            if bpy.data.materials.get(material.name) is material:
                bpy.data.materials.remove(material)
        self.objects, self.meshes, self.kinds = [], [], {}
        self.materials = Materials(self.species)
