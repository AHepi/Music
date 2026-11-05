"""
render_final.py - build 57: a Japanese garden after rain, beside a timber inn, at dusk (the owner's picture, no animals).

    python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png        (defaults 540 960 64 final.png beside this script)

A wet stone path runs from the eye along an inn's veranda (red posts with peeling paint, a lit hanging lantern) to a
pond; stepping stones go on round its bank to a red arched bridge; a stone lantern stands lit on rocks at the water;
a bamboo spout pours into a stone basin behind a bamboo fence; maples, a pine, clipped shrubs and bamboo; the inn of
two storeys with lit paper screens behind the pond, and wooded mountains in the mist. Everything is built here, the
surfaces from the kit's shelf and store.

Second pass (dressing, 5 November 2026; every change is marked "second pass" in the code): the maid's bamboo broom
leant on the fence's top rail, the heap of leaves she swept to the path's edge, her wooden bucket with copper hoops
and a dipper beside the path, damp and mud on the soil where water slops, store litter and pebbles in the bed between
path and fence, the guests' clogs as a neat pair on the step stone; the slabs' outlines knocked about like split stone
with their photographed relief turned up and worn edges, smaller ragged puddles (the one mirroring the hanging lantern
kept long), darker joints, deeper red leaves without the sky's pink sheen, the jar's glaze streaked, the bamboo dark
at its foot; the close view finished a little brighter with more glow round the glint.
Layout, camera and lights as the first builder left them.

    python3 render_final.py 540 960 40 final.png                 the final (drawn in about 3.5 minutes here)
    python3 render_final.py 540 960 40 closeup.png --closeup     the close view of the path
"""
import math
import os
import random
import sys
import time

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = '/home/claude/build-57-garden/kit'
sys.path.insert(0, os.path.join(KIT, 'store', 'tools'))

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector, Matrix, Euler, noise  # noqa: E402

import store  # noqa: E402
import moss  # noqa: E402
import hedge  # noqa: E402
import puddle  # noqa: E402
import sky_and_haze  # noqa: E402
import finish  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
W = int(args[0]) if len(args) > 0 else 540
H = int(args[1]) if len(args) > 1 else 960
S = int(args[2]) if len(args) > 2 else 64
OUT = os.path.abspath(args[3]) if len(args) > 3 else os.path.join(HERE, 'final.png')
NO_TREES = '--no-trees' in sys.argv
NO_HEDGES = '--no-hedges' in sys.argv
CLOSEUP = '--closeup' in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
R = random.Random(57)


def log(*a):
    print('[%6.1fs]' % (time.time() - T0), *a, flush=True)


# ===================================================================================================== mesh helpers
class Mesh:
    """Collects many simple pieces into one mesh object."""

    def __init__(self, name):
        self.name, self.v, self.f, self.attrs = name, [], [], {}
        self.luv = None

    def add(self, verts, faces, **attrs):
        base = len(self.v)
        luv = attrs.pop('_luv', None)
        verts = list(verts)
        if luv is not None or self.luv is not None:
            if self.luv is None:
                self.luv = [(0.0, 0.0, 0.0)] * base
            self.luv.extend(luv if luv is not None else [(0.0, 0.0, 0.0)] * len(verts))
        self.v.extend(tuple(p) for p in verts)
        self.f.extend(tuple(i + base for i in face) for face in faces)
        for k, val in attrs.items():
            self.attrs.setdefault(k, {})
        for k in self.attrs:
            self.attrs[k].setdefault('vals', [])
            pad = len(self.f) - len(faces) - len(self.attrs[k]['vals'])
            if pad > 0:
                self.attrs[k]['vals'].extend([0.0] * pad)
            self.attrs[k]['vals'].extend([float(attrs.get(k, 0.0))] * len(faces))

    def box(self, center, size, rot=None, **attrs):
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        pts = [Vector((x, y, z)) for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)]
        m = rot.to_matrix() if rot is not None else Matrix.Identity(3)
        c = Vector(center)
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        self.add([c + m @ p for p in pts], faces, **attrs)

    def beam(self, p0, p1, w, h, up=(0, 0, 1), **attrs):
        """A box from p0 to p1 with cross-section w (sideways) x h (up)."""
        p0, p1 = Vector(p0), Vector(p1)
        t = (p1 - p0)
        length = t.length
        t.normalize()
        upv = Vector(up)
        if abs(t.dot(upv)) > 0.99:
            upv = Vector((1, 0, 0))
        side = t.cross(upv).normalized()
        u = side.cross(t).normalized()
        m = Matrix((side, t, u)).transposed()
        self.box((p0 + p1) / 2, (w, length, h), rot=m.to_quaternion(), **attrs)

    def cyl(self, p0, p1, r0, r1=None, seg=8, caps=True, **attrs):
        p0, p1 = Vector(p0), Vector(p1)
        r1 = r0 if r1 is None else r1
        axis = p1 - p0
        length = axis.length
        q = Vector((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix()
        verts = []
        for z, r in ((0.0, r0), (length, r1)):
            for i in range(seg):
                a = 2 * math.pi * i / seg
                verts.append(p0 + q @ Vector((r * math.cos(a), r * math.sin(a), z)))
        faces = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
        if caps:
            faces.append(tuple(reversed(range(seg))))
            faces.append(tuple(range(seg, 2 * seg)))
        self.add(verts, faces, **attrs)

    def sweep(self, pts, w, h, up=(0, 0, 1), **attrs):
        pts = [Vector(p) for p in pts]
        n = len(pts)
        upv = Vector(up)
        rings = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            side = t.cross(upv).normalized()
            u = side.cross(t).normalized()
            rings.append([p + side * sx * w / 2 + u * sy * h / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        verts = [v for ring in rings for v in ring]
        faces = []
        for i in range(n - 1):
            a, b = 4 * i, 4 * (i + 1)
            for k in range(4):
                faces.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
        faces.append((3, 2, 1, 0))
        faces.append((4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 2, 4 * (n - 1) + 3))
        self.add(verts, faces, **attrs)

    def tube(self, pts, radii, seg=8, **attrs):
        """A round tube along points with a radius per point."""
        pts = [Vector(p) for p in pts]
        n = len(pts)
        verts, faces = [], []
        prev_side = None
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            side = t.cross(ref).normalized() if prev_side is None else (prev_side - t * prev_side.dot(t)).normalized()
            prev_side = side
            u = t.cross(side).normalized()
            for k in range(seg):
                a = 2 * math.pi * k / seg
                verts.append(p + (side * math.cos(a) + u * math.sin(a)) * radii[i])
        for i in range(n - 1):
            for k in range(seg):
                a, b = i * seg, (i + 1) * seg
                faces.append((a + k, a + (k + 1) % seg, b + (k + 1) % seg, b + k))
        faces.append(tuple(reversed(range(seg))))
        faces.append(tuple(range((n - 1) * seg, n * seg)))
        self.add(verts, faces, **attrs)

    def build(self, mat, smooth=False, ground=None):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        for k, d in self.attrs.items():
            vals = d['vals'] + [0.0] * (len(self.f) - len(d['vals']))
            a = me.attributes.new(k, 'FLOAT', 'FACE')
            a.data.foreach_set('value', vals)
        if self.luv is not None:
            vals = self.luv + [(0.0, 0.0, 0.0)] * (len(self.v) - len(self.luv))
            la = me.attributes.new('leafuv', 'FLOAT_VECTOR', 'POINT')
            la.data.foreach_set('vector', [c for t in vals for c in t])
        me.update()
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(self.name, me)
        scene.collection.objects.link(ob)
        if mat is not None:
            store.use_material(ob, mat, ground=ground)
        return ob


def lathe(mesh, profile, center, seg=32, wobble=0.0, seed=0, **attrs):
    """Turn a (radius, height) profile about Z at center; wobble roughens it like a stone."""
    c = Vector(center)
    verts = []
    for r, z in profile:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            rr = r
            if wobble and r > 0.001:
                rr = r + wobble * noise.noise(Vector((math.cos(a) * 1.7 + seed, math.sin(a) * 1.7, z * 3.0)))
            verts.append(c + Vector((rr * math.cos(a), rr * math.sin(a), z)))
    faces = []
    for j in range(len(profile) - 1):
        for i in range(seg):
            a, b = j * seg, (j + 1) * seg
            faces.append((a + i, a + (i + 1) % seg, b + (i + 1) % seg, b + i))
    mesh.add(verts, faces, **attrs)


# ===================================================================================================== material helpers
def new_mat(name):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    return m, nt.nodes, nt.links, bsdf


def put(links, sock, val):
    if isinstance(val, bpy.types.NodeSocket):
        links.new(val, sock)
    else:
        sock.default_value = val


def mix_rgb(nodes, links, fac, a, b, blend='MIX'):
    n = nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    put(links, n.inputs[0], fac)
    put(links, n.inputs[6], a if not isinstance(a, tuple) else (*a, 1.0) if len(a) == 3 else a)
    put(links, n.inputs[7], b if not isinstance(b, tuple) else (*b, 1.0) if len(b) == 3 else b)
    return n.outputs[2]


def ramp(nodes, links, fac, stops):
    r = nodes.new('ShaderNodeValToRGB')
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1.0)
    els[1].position, els[1].color = stops[-1][0], (*stops[-1][1], 1.0)
    for p, c in stops[1:-1]:
        e = els.new(p)
        e.color = (*c, 1.0)
    put(links, r.inputs['Fac'], fac)
    return r.outputs['Color']


def math_node(nodes, links, op, a, b=0.0, clamp=False):
    n = nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    put(links, n.inputs[0], a)
    put(links, n.inputs[1], b)
    return n.outputs[0]


def tex_noise(nodes, links, scale, detail=4.0, rough=0.55, vec=None, out='Fac'):
    t = nodes.new('ShaderNodeTexNoise')
    t.inputs['Scale'].default_value = scale
    t.inputs['Detail'].default_value = detail
    t.inputs['Roughness'].default_value = rough
    if vec is not None:
        links.new(vec, t.inputs['Vector'])
    return t.outputs[out]


def obj_coords(nodes, scale=(1, 1, 1)):
    tc = nodes.new('ShaderNodeTexCoord')
    mp = nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    nodes.id_data.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector'], tc


def bump(nodes, links, bsdf, height, strength=0.3, distance=0.02):
    b = nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = distance
    links.new(height, b.inputs['Height'])
    links.new(b.outputs['Normal'], bsdf.inputs['Normal'])


def store_copy(name, new_name, **dials):
    m = store.material(name).copy()
    m.name = new_name
    w = m.node_tree.nodes.get('Weather')
    names = {'wet': 'Wet', 'grime': 'Grime', 'mud_height': 'Mud height', 'mud_color': 'Mud color',
             'edge_wear': 'Edge wear', 'bump': 'Bump', 'darken': 'Darken'}
    for k, v in dials.items():
        if w is not None and names[k] in w.inputs:
            w.inputs[names[k]].default_value = v
    return m


def add_air(mat, k, colour, strength=1.0):
    """Mix the material towards lit air by its distance from the eye (far things lighter and bluer)."""
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    src = out.inputs['Surface'].links[0].from_socket
    cam = nodes.new('ShaderNodeCameraData')
    e = math_node(nodes, links, 'EXPONENT', math_node(nodes, links, 'MULTIPLY', cam.outputs['View Distance'], -k))
    fac = math_node(nodes, links, 'SUBTRACT', 1.0, e)
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*colour, 1.0)
    em.inputs['Strength'].default_value = strength
    mix = nodes.new('ShaderNodeMixShader')
    links.new(fac, mix.inputs[0])
    links.new(src, mix.inputs[1])
    links.new(em.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs['Surface'])


# ----------------------------------------------------------------------------------------------- made materials
def mat_paint(name, paint=(0.30, 0.045, 0.028), wood=(0.10, 0.085, 0.07), peel=0.5):
    """Old red paint peeling in vertical strips to grey timber, gone at the foot."""
    m, nodes, links, b = new_mat(name)
    vec, tc = obj_coords(nodes, (5.0, 5.0, 0.9))
    n1 = tex_noise(nodes, links, 2.2, 8.0, 0.62, vec)
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tc.outputs['Object'], sep.inputs[0])
    foot = math_node(nodes, links, 'MULTIPLY', math_node(nodes, links, 'SUBTRACT', 1.0,
                     math_node(nodes, links, 'DIVIDE', sep.outputs['Z'], 0.9, clamp=True)), 0.22)
    level = math_node(nodes, links, 'ADD', n1, foot)
    mask = ramp(nodes, links, level, [(peel - 0.03, (1, 1, 1)), (peel + 0.02, (0, 0, 0))])   # 1 = paint
    var = tex_noise(nodes, links, 9.0, 3.0, 0.5, vec)
    paint_col = mix_rgb(nodes, links, var, tuple(c * 0.75 for c in paint), tuple(c * 1.15 for c in paint))
    wood_col = mix_rgb(nodes, links, var, wood, tuple(c * 0.6 for c in wood))
    col = mix_rgb(nodes, links, mask, wood_col, paint_col)
    links.new(col, b.inputs['Base Color'])
    rough = ramp(nodes, links, mask, [(0.0, (0.62, 0.62, 0.62)), (1.0, (0.38, 0.38, 0.38))])
    links.new(rough, b.inputs['Roughness'])
    h = math_node(nodes, links, 'ADD', math_node(nodes, links, 'MULTIPLY', mask, 0.6), math_node(nodes, links, 'MULTIPLY', var, 0.4))
    bump(nodes, links, b, h, 0.25, 0.004)
    return m


def mat_flat(name, colour, rough=0.5, var=0.25, scale=6.0, metal=0.0, spec=0.5, bump_s=0.15):
    m, nodes, links, b = new_mat(name)
    vec, tc = obj_coords(nodes)
    n = tex_noise(nodes, links, scale, 5.0, 0.6, vec)
    col = mix_rgb(nodes, links, n, tuple(c * (1 - var) for c in colour), tuple(min(1.0, c * (1 + var)) for c in colour))
    links.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if bump_s:
        bump(nodes, links, b, n, bump_s, 0.01)
    return m


def mat_glow(name, colour, strength, paper=(0.5, 0.42, 0.3)):
    """Lit paper: glows warm, patchy where the paper is thicker; lets light through and casts no shadow (set on objects)."""
    m, nodes, links, b = new_mat(name)
    vec, tc = obj_coords(nodes)
    n = tex_noise(nodes, links, 7.0, 4.0, 0.6, vec)
    col = mix_rgb(nodes, links, n, tuple(c * 0.75 for c in colour), colour)
    links.new(col, b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = strength
    b.inputs['Base Color'].default_value = (*paper, 1.0)
    b.inputs['Roughness'].default_value = 0.8
    return m


def mat_water(name, ripple=0.05, scale=9.0, rings=None):
    m, nodes, links, b = new_mat(name)
    b.inputs['Base Color'].default_value = (0.006, 0.009, 0.011, 1.0)
    b.inputs['Roughness'].default_value = 0.035
    b.inputs['IOR'].default_value = 1.333
    b.inputs['Specular IOR Level'].default_value = 0.5
    vec, tc = obj_coords(nodes, (1.0, 1.6, 1.0))
    n = tex_noise(nodes, links, scale, 3.0, 0.5, vec)
    h = n
    if rings is not None:
        mp = nodes.new('ShaderNodeMapping')
        mp.inputs['Location'].default_value = (-rings[0], -rings[1], 0.0)
        links.new(tc.outputs['Object'], mp.inputs['Vector'])
        wv = nodes.new('ShaderNodeTexWave')
        wv.wave_type = 'RINGS'
        wv.inputs['Scale'].default_value = 9.0
        wv.inputs['Distortion'].default_value = 1.5
        links.new(mp.outputs['Vector'], wv.inputs['Vector'])
        h = math_node(nodes, links, 'ADD', math_node(nodes, links, 'MULTIPLY', wv.outputs['Fac'], 1.0), math_node(nodes, links, 'MULTIPLY', n, 0.3))
    bump(nodes, links, b, h, ripple, 0.02)
    return m


def mat_leaf(name, stops, translucent=0.35, rough=0.4):
    m, nodes, links, b = new_mat(name)
    at = nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'tone'
    col = ramp(nodes, links, at.outputs['Fac'], stops)
    links.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    if translucent > 0:
        out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        tr = nodes.new('ShaderNodeBsdfTranslucent')
        links.new(col, tr.inputs['Color'])
        mix = nodes.new('ShaderNodeMixShader')
        mix.inputs[0].default_value = translucent
        links.new(b.outputs[0], mix.inputs[1])
        links.new(tr.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def mat_jar(name):
    """White glaze with cobalt flowers and bands, crazed, wet."""
    m, nodes, links, b = new_mat(name)
    tc = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tc.outputs['Object'], sep.inputs[0])
    vec, _ = obj_coords(nodes, (1.0, 1.0, 1.0))
    v = nodes.new('ShaderNodeTexVoronoi')
    v.inputs['Scale'].default_value = 9.0
    links.new(vec, v.inputs['Vector'])
    n = tex_noise(nodes, links, 8.0, 4.0, 0.6, vec)
    petals = math_node(nodes, links, 'ADD', math_node(nodes, links, 'MULTIPLY', v.outputs['Distance'], 1.6), math_node(nodes, links, 'MULTIPLY', n, 0.5))
    swirl = tex_noise(nodes, links, 4.5, 3.0, 0.5, vec)
    line = ramp(nodes, links, swirl, [(0.465, (0, 0, 0)), (0.485, (1, 1, 1)), (0.505, (1, 1, 1)), (0.525, (0, 0, 0))])
    blot = ramp(nodes, links, swirl, [(0.6, (0, 0, 0)), (0.625, (1, 1, 1))])
    flower = math_node(nodes, links, 'MAXIMUM', line, blot)
    z = sep.outputs['Z']
    band1 = ramp(nodes, links, z, [(0.06, (0, 0, 0)), (0.07, (1, 1, 1)), (0.1, (1, 1, 1)), (0.11, (0, 0, 0))])
    band2 = ramp(nodes, links, z, [(0.47, (0, 0, 0)), (0.48, (1, 1, 1)), (0.505, (1, 1, 1)), (0.515, (0, 0, 0))])
    belly = ramp(nodes, links, z, [(0.13, (0, 0, 0)), (0.16, (1, 1, 1)), (0.43, (1, 1, 1)), (0.46, (0, 0, 0))])
    fl = math_node(nodes, links, 'MULTIPLY', nodes.new('ShaderNodeRGBToBW').outputs[0] if False else flower, belly)
    blue_amt = math_node(nodes, links, 'MAXIMUM', fl, math_node(nodes, links, 'MAXIMUM', band1, band2))
    col = mix_rgb(nodes, links, blue_amt, (0.34, 0.34, 0.33), (0.012, 0.03, 0.17))
    _sv, _ = obj_coords(nodes, (14.0, 14.0, 0.8))      # second pass: rain streaks down from the rim, grime in them
    _st = ramp(nodes, links, tex_noise(nodes, links, 3.0, 6.0, 0.6, _sv), [(0.5, (0, 0, 0)), (0.66, (1, 1, 1))])
    col = mix_rgb(nodes, links, math_node(nodes, links, 'MULTIPLY', _st, 0.55), col, (0.075, 0.08, 0.08))
    grime = ramp(nodes, links, z, [(0.0, (1, 1, 1)), (0.09, (0, 0, 0))])
    col = mix_rgb(nodes, links, grime, col, (0.03, 0.035, 0.02))
    links.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.12
    b.inputs['Coat Weight'].default_value = 0.6
    b.inputs['Coat Roughness'].default_value = 0.05
    cr = nodes.new('ShaderNodeTexVoronoi')
    cr.feature = 'DISTANCE_TO_EDGE'
    cr.inputs['Scale'].default_value = 40.0
    links.new(vec, cr.inputs['Vector'])
    bump(nodes, links, b, cr.outputs['Distance'], 0.05, 0.002)
    return m


def mat_bamboo(name, green=(0.11, 0.13, 0.04), old=(0.22, 0.18, 0.08), greyed=0.0, foot_damp=False):
    m, nodes, links, b = new_mat(name)
    info = nodes.new('ShaderNodeObjectInfo')
    vec, tc = obj_coords(nodes, (30.0, 30.0, 1.5))
    streak = tex_noise(nodes, links, 3.0, 4.0, 0.6, vec)
    base = mix_rgb(nodes, links, info.outputs['Random'], green, old)
    grey = tuple(0.6 * (c * 0.4 + 0.12) for c in old)
    base = mix_rgb(nodes, links, greyed, base, grey)
    col = mix_rgb(nodes, links, streak, base, (0.04, 0.035, 0.02), 'MIX')
    if foot_damp:    # second pass: dark and green at the foot, where soil splashes and the damp climbs (world height)
        _geo = nodes.new('ShaderNodeNewGeometry')
        _sz = nodes.new('ShaderNodeSeparateXYZ')
        links.new(_geo.outputs['Position'], _sz.inputs[0])
        _foot = ramp(nodes, links, _sz.outputs['Z'], [(0.0, (1, 1, 1)), (0.22, (0, 0, 0))])
        _ft = math_node(nodes, links, 'MULTIPLY', _foot, math_node(nodes, links, 'ADD', 0.45, math_node(nodes, links, 'MULTIPLY', streak, 0.45)))
        col = mix_rgb(nodes, links, _ft, col, (0.022, 0.03, 0.012))
    fac_mix = nodes.new('ShaderNodeMix')
    links.new(col, b.inputs['Base Color'])
    nodes.remove(fac_mix)
    b.inputs['Roughness'].default_value = 0.32
    b.inputs['Coat Weight'].default_value = 0.3
    return m


# ===================================================================================================== materials
log('materials')
M_red = mat_paint('red paint, peeling', peel=0.44)
M_red_bridge = mat_paint('bridge red paint', paint=(0.36, 0.05, 0.03), peel=0.46)
M_timber = mat_flat('dark timber', (0.04, 0.035, 0.031), rough=0.6, var=0.3, scale=4.0)
M_rafter = mat_flat('rafters, sooted', (0.034, 0.032, 0.03), rough=0.7, var=0.35, scale=5.0)
M_lattice = mat_flat('lattice wood', (0.04, 0.028, 0.018), rough=0.6, var=0.2)
M_soffit = mat_flat('soffit boards, sooted', (0.03, 0.022, 0.016), rough=0.7, var=0.3, scale=3.0)
M_tile = mat_flat('clay roof tiles, wet', (0.042, 0.047, 0.052), rough=0.28, var=0.35, scale=2.5, bump_s=0.2)
M_tile_moss = mat_flat('roof tile ends', (0.05, 0.052, 0.05), rough=0.35, var=0.4, scale=8.0)
M_shoji_lit = mat_glow('lit paper screen', (1.0, 0.56, 0.24), 2.4)
M_shoji_dim = mat_glow('dim paper screen', (0.55, 0.36, 0.2), 0.16, paper=(0.20, 0.18, 0.15))
M_lantern_paper = mat_glow('lantern paper', (1.0, 0.52, 0.2), 9.0)
M_stone_window = mat_glow('stone lantern paper', (1.0, 0.5, 0.18), 10.0)
M_round_lantern = mat_glow('round paper lantern', (1.0, 0.45, 0.16), 6.0)
M_water = mat_water('pond water', ripple=0.04)
_wb = next(n for n in M_water.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
_wb.inputs['IOR'].default_value = 1.7
_wb.inputs['Specular IOR Level'].default_value = 0.8
M_basin_water = mat_water('basin water', ripple=0.25, rings=(1.13, 2.69))
M_stream = mat_flat('falling water', (0.45, 0.5, 0.55), rough=0.08, var=0.1, spec=0.8, bump_s=0.0)
M_iron = mat_flat('black iron', (0.02, 0.018, 0.016), rough=0.45, var=0.2, metal=0.6)
M_cord = mat_flat('black cord', (0.012, 0.01, 0.009), rough=0.8, var=0.1, scale=30.0)
M_geta = mat_flat('paulownia clogs, foot-darkened', (0.2, 0.14, 0.085), rough=0.55, var=0.3)
M_thong = mat_flat('clog thongs', (0.42, 0.025, 0.018), rough=0.7, var=0.2)
M_maple = mat_leaf('maple leaves', [(0.0, (0.30, 0.012, 0.008)), (0.45, (0.42, 0.04, 0.01)), (0.75, (0.55, 0.13, 0.015)), (1.0, (0.20, 0.08, 0.02))])
M_maple_ground = mat_leaf('fallen maple leaves', [(0.0, (0.13, 0.006, 0.003)), (0.35, (0.24, 0.016, 0.005)), (0.65, (0.33, 0.055, 0.006)), (0.85, (0.29, 0.095, 0.01)), (1.0, (0.09, 0.035, 0.01))], translucent=0.1, rough=0.45)   # second pass: deeper reds, no pink
def add_veins(mat, coat=0.0):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    b = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    base = b.inputs['Base Color'].links[0].from_socket
    at = nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'leafuv'
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(at.outputs['Vector'], sep.inputs[0])
    ang = math_node(nodes, links, 'ARCTAN2', sep.outputs['X'], sep.outputs['Y'])
    cosv = math_node(nodes, links, 'COSINE', math_node(nodes, links, 'MULTIPLY', ang, 7.66))
    line = math_node(nodes, links, 'POWER', math_node(nodes, links, 'MAXIMUM', cosv, 0.0), 8.0)
    radius = math_node(nodes, links, 'SQRT', math_node(nodes, links, 'ADD', math_node(nodes, links, 'MULTIPLY', sep.outputs['X'], sep.outputs['X']),
                                                                         math_node(nodes, links, 'MULTIPLY', sep.outputs['Y'], sep.outputs['Y'])))
    fade = math_node(nodes, links, 'SUBTRACT', 1.0, math_node(nodes, links, 'POWER', radius, 4.0), clamp=True)
    amount = math_node(nodes, links, 'MULTIPLY', math_node(nodes, links, 'MULTIPLY', line, fade), 0.9, clamp=True)
    col = mix_rgb(nodes, links, amount, base, (0.07, 0.008, 0.004))
    links.new(col, b.inputs['Base Color'])
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.08


add_veins(M_maple)
add_veins(M_maple_ground, coat=0.05)    # second pass: was 0.6; the gloss mirrored the blue sky and turned the reds pink
next(n for n in M_maple_ground.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value = 0.22
M_lily = mat_leaf('water-lily leaves', [(0.0, (0.018, 0.045, 0.012)), (0.7, (0.035, 0.07, 0.015)), (1.0, (0.12, 0.10, 0.02))], translucent=0.1, rough=0.3)
M_flower = mat_leaf('water-lily flowers', [(0.0, (0.55, 0.18, 0.25)), (1.0, (0.75, 0.42, 0.45))], translucent=0.4, rough=0.5)
M_fern = mat_leaf('fern fronds', [(0.0, (0.012, 0.035, 0.008)), (1.0, (0.04, 0.075, 0.015))], translucent=0.3, rough=0.35)
M_bamboo_leaf = mat_leaf('bamboo leaves', [(0.0, (0.015, 0.035, 0.01)), (1.0, (0.05, 0.075, 0.02))], translucent=0.3, rough=0.35)
M_jar = mat_jar('blue-and-white jar')
M_bamboo = mat_bamboo('bamboo, wet')
M_bamboo_old = mat_bamboo('bamboo fence, greyed', green=(0.17, 0.15, 0.07), old=(0.26, 0.2, 0.1), greyed=0.35, foot_damp=True)
M_mountain = mat_flat('wooded mountains', (0.012, 0.022, 0.02), rough=0.9, var=0.6, scale=0.08, bump_s=0.0)
add_air(M_mountain, 0.011, (0.045, 0.065, 0.085), 1.0)
M_far_trees = mat_flat('far trees', (0.008, 0.016, 0.012), rough=0.9, var=0.5, scale=0.5, bump_s=0.0)
add_air(M_far_trees, 0.02, (0.06, 0.085, 0.105), 1.0)

S_slab = store_copy('SURFACE • dark_rock_02', 'path slabs, wet', wet=0.85, edge_wear=0.35)
S_slab.node_tree.nodes['Weather'].inputs['Darken'].default_value *= 0.93   # second pass
if S_slab.node_tree.nodes.get('Normal picture') is not None:
    S_slab.node_tree.nodes['Normal picture'].inputs['Strength'].default_value = 0.95   # second pass: was 0.55
if S_slab.node_tree.nodes.get('Weather') is not None and 'Bump' in S_slab.node_tree.nodes['Weather'].inputs:
    S_slab.node_tree.nodes['Weather'].inputs['Bump'].default_value *= 1.2   # second pass: was 0.4
if S_slab.node_tree.nodes.get('Pieces') is not None:
    for _k in S_slab.node_tree.nodes['Pieces'].inputs:
        if _k.name == 'Shade':
            log('slab Shade was', _k.default_value)
            _k.default_value = max(_k.default_value, 0.35)
S_rock = moss.add(store_copy('SURFACE • dark_rock_02', 'garden rocks', wet=0.7), amount=1.0, foot=0.15, scale=4.0)
S_lantern = moss.add(store_copy('SURFACE • dark_rock_02', 'lantern granite', wet=0.6), amount=0.9, foot=0.2, scale=6.0)
S_deck = store_copy('SURFACE • old_planks_02', 'veranda boards', wet=0.55)
S_wood = store_copy('SURFACE • rough_wood', 'rafters and bridge deck', wet=0.4)
S_plaster = store_copy('SURFACE • worn_plaster_wall', 'inn plaster', wet=0.2)
S_base = store_copy('SURFACE • old_stone_wall_02', 'inn stone base', wet=0.5)
S_ground = moss.add(store_copy('SURFACE • mud_forest', 'garden soil', wet=0.75), amount=1.15, foot=0.0, facing=(0.2, 0.75), scale=1.6)
S_bark = store.material('MADE • wet bark')
add_air(S_plaster, 0.006, (0.09, 0.12, 0.15), 1.0)


# ===================================================================================================== the ground and the pond
log('ground')
WATER_Z = -0.12


def pond_f(x, y):
    f1 = ((x - 2.45) / 3.0) ** 2 + ((y - 7.4) / 3.9) ** 2
    f2 = ((x - 2.2) / 1.9) ** 2 + ((y - 12.9) / 1.7) ** 2
    return min(f1, f2) * (1.0 + 0.09 * noise.noise(Vector((x * 0.55, y * 0.55, 1.3))))


def ground_z(x, y):
    f = pond_f(x, y)
    t = min(max((1.25 - f) / 0.6, 0.0), 1.0)
    s = t * t * (3 - 2 * t)
    z = -0.62 * s + 0.03 * noise.noise(Vector((x * 1.7, y * 1.7, 0.2))) * (1 - s)
    if -1.0 < x < 0.6 and -1.5 < y < 4.8:          # the path's bed, filled to just under the slabs' tops
        z = max(z, 0.026 + 0.008 * noise.noise(Vector((x * 9.0, y * 9.0, 4.0))))
    for (mx, my, mh, mr) in ((4.9, 5.4, 0.35, 1.6), (-0.4, 15.0, 0.3, 1.8), (5.6, 13.5, 0.45, 2.2), (3.6, 3.4, 0.18, 1.2)):
        d = math.hypot(x - mx, y - my) / mr
        if d < 1:
            z += mh * (1 - d * d) ** 2 * (1 - s)
    return z


gm = Mesh('garden ground')
X0, X1, Y0, Y1, CELL = -7.0, 20.0, -3.0, 34.0, 0.15
nx, ny = int((X1 - X0) / CELL) + 1, int((Y1 - Y0) / CELL) + 1
gverts = []
for j in range(ny):
    y = Y0 + j * CELL
    for i in range(nx):
        x = X0 + i * CELL
        gverts.append((x, y, ground_z(x, y)))
gfaces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(ny - 1) for i in range(nx - 1)]
gm.add(gverts, gfaces)
GROUND = gm.build(S_ground, smooth=True, ground=0.0)

wm = Mesh('pond water')
wm.add([(-1.4, 3.5, WATER_Z), (6.4, 3.5, WATER_Z), (6.4, 15.2, WATER_Z), (-1.4, 15.2, WATER_Z)], [(0, 1, 2, 3)])
wm.build(M_water)


# ===================================================================================================== stones: path, stepping stones, rocks
log('stones')


def slab(mesh, pts2d, ztop, depth=0.3, chamfer=0.022, tilt=(0.0, 0.0), piece=0.5):
    n = len(pts2d)
    cx = sum(p[0] for p in pts2d) / n
    cy = sum(p[1] for p in pts2d) / n

    def zt(x, y):
        return ztop + tilt[0] * (x - cx) + tilt[1] * (y - cy)
    inner = []
    for px, py in pts2d:
        dx, dy = cx - px, cy - py
        d = math.hypot(dx, dy) or 1.0
        qx, qy = px + dx * chamfer / d, py + dy * chamfer / d
        inner.append((qx, qy, zt(qx, qy)))
    outer = [(px, py, zt(px, py) - chamfer * 0.9) for px, py in pts2d]
    bottom = [(px, py, ztop - depth) for px, py in pts2d]
    faces = [tuple(range(n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, n + i, n + j, j))
        faces.append((n + i, 2 * n + i, 2 * n + j, n + j))
    faces.append(tuple(2 * n + i for i in reversed(range(n))))
    mesh.add(inner + outer + bottom, faces, pp_piece=piece)


PUDDLE_AT = (-0.46, 1.82)


def rough_slab(mesh, x0, x1, y0, y1, ztop, seed, dish=0.0, cell=0.02, depth=0.25, round_r=0.035, tilt=(0.0, 0.0), piece=0.5):
    """A split stone slab whose top has real relief: low swells, pits, edges worn round; a dish holds rain."""
    nx = max(4, int(round((x1 - x0) / cell)))
    ny = max(4, int(round((y1 - y0) / cell)))
    cx, cy, hw, hd = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    off = Vector((seed * 13.17, seed * 7.31, seed * 0.77))
    top = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            p = Vector((x * 6.0, y * 6.0, 0.0)) + off
            # second pass: the outline made irregular, corners knocked off and edges wandering, as split stone is
            ex, ey = min(x - x0, x1 - x), min(y - y0, y1 - y)
            near_edge = max(0.0, 1.0 - min(ex, ey) / 0.08)
            wx = 0.011 * noise.noise(Vector((y * 7.0, seed * 1.7, 2.0))) * near_edge
            wy = 0.011 * noise.noise(Vector((x * 7.0, seed * 2.3, 5.0))) * near_edge
            kc = max(0.0, 1.0 - ex / 0.09) * max(0.0, 1.0 - ey / 0.09)
            pull = (0.026 + 0.02 * (0.5 + 0.5 * noise.noise(Vector((seed * 0.9, x0, y0))))) * kc
            x += (wx if ex < ey else 0.0) + (pull if x < cx else -pull)
            y += (wy if ey <= ex else 0.0) + (pull if y < cy else -pull)
            rel = 0.005 * noise.noise(p) + 0.0028 * noise.noise(p * 3.1)
            rel += 0.0032 * noise.noise(p * 4.6 + Vector((1.7, 8.1, 3.3)))     # second pass: finer relief, ragged water edges
            pit = noise.noise(p * 4.3 + Vector((3.3, 1.1, 7.7)))
            if pit > 0.42:
                rel -= (pit - 0.42) * 0.025
            de = min(ex, ey)              # second pass: measured on the stone before its outline was knocked about
            rr = round_r * (0.7 + 0.6 * (0.5 + 0.5 * noise.noise(p * 0.7 + Vector((9.0, 9.0, 9.0)))))
            e = max(0.0, 1.0 - de / rr)
            z = ztop + rel - 0.026 * e * e + tilt[0] * (x - cx) + tilt[1] * (y - cy)
            if dish:
                u = ((x - cx) / hw) ** 2 + ((y - cy) / hd) ** 2
                z -= dish * max(0.0, 1.0 - u)
            top.append((x, y, z))
    w1 = nx + 1
    faces = [(j * w1 + i, j * w1 + i + 1, (j + 1) * w1 + i + 1, (j + 1) * w1 + i) for j in range(ny) for i in range(nx)]
    loop = list(range(nx + 1)) + [j * w1 + nx for j in range(1, ny + 1)] + [ny * w1 + i for i in range(nx - 1, -1, -1)] + [j * w1 for j in range(ny - 1, 0, -1)]
    nt, nl = len(top), len(loop)
    bottom = [(top[k][0], top[k][1], ztop - depth) for k in loop]
    for m in range(nl):
        faces.append((loop[m], loop[(m + 1) % nl], nt + (m + 1) % nl, nt + m))
    faces.append(tuple(nt + m for m in reversed(range(nl))))
    mesh.add(top + bottom, faces, pp_piece=piece)


near = Mesh('path slabs, near')
SLAB_RECTS, DISH_SLABS = [], []
y = 0.15
while y < 4.6:
    d = R.uniform(0.36, 0.6)
    xs = [-0.82]
    while xs[-1] < 0.48 - 0.35:
        xs.append(min(0.48, xs[-1] + R.uniform(0.38, 0.75)))
    xs[-1] = 0.48
    for a, bx in zip(xs[:-1], xs[1:]):
        g = 0.018
        x0, x1, y0, y1 = a + g, bx - g, y + g, y + d - g
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        low = math.hypot((mx - PUDDLE_AT[0]) * 1.2, my - PUDDLE_AT[1]) < 0.62
        zt = 0.042 if low else 0.056 + R.uniform(-0.01, 0.012)
        dish = 0.0
        if not low and mx > -0.32 and 0.8 < my < 4.3 and R.random() < 0.6:
            dish = R.uniform(0.016, 0.022)
            DISH_SLABS.append((x0, x1, y0, y1, zt, dish))
        rough_slab(near, x0, x1, y0, y1, zt, len(SLAB_RECTS), dish=dish, tilt=(R.uniform(-0.012, 0.012), R.uniform(-0.012, 0.012)), piece=R.random())
        SLAB_RECTS.append((x0, x1, y0, y1))
    y += d
NEAR_PATH = near.build(S_slab, smooth=True, ground=0.0)
path = Mesh('path slabs')
# stepping stones round the pond's bank to the bridge
STEPS = [(-0.25, 5.0), (-0.42, 5.75), (-0.5, 6.55), (-0.42, 7.35), (-0.3, 8.15), (-0.2, 8.95), (-0.08, 9.75), (0.05, 10.55), (0.12, 11.35), (0.2, 12.05)]
for k, (sx, sy) in enumerate(STEPS):
    r = R.uniform(0.27, 0.34)
    el = R.uniform(0.8, 1.0)
    turn = R.uniform(0, math.pi)
    pts = []
    for i in range(12):
        a = 2 * math.pi * i / 12
        rr = r * (1 + 0.14 * noise.noise(Vector((math.cos(a) * 1.3 + k * 3.1, math.sin(a) * 1.3, 0.5))))
        lx, ly = rr * math.cos(a), rr * el * math.sin(a)
        pts.append((sx + lx * math.cos(turn) - ly * math.sin(turn), sy + lx * math.sin(turn) + ly * math.cos(turn)))
    gz = max(ground_z(sx, sy), WATER_Z)
    slab(path, pts, max(gz, 0.0) + R.uniform(0.03, 0.06), depth=0.85, chamfer=0.04, tilt=(R.uniform(-0.03, 0.03), R.uniform(-0.03, 0.03)), piece=R.random())
# the stone step at the veranda, where clogs are left
slab(path, [(-0.98, 2.62), (-0.42, 2.6), (-0.36, 2.72), (-0.38, 3.06), (-0.45, 3.12), (-0.96, 3.1), (-1.02, 2.98), (-1.0, 2.7)], 0.24, depth=0.4, chamfer=0.03, piece=0.3)
PATH = path.build(S_slab, ground=0.0)

# rocks: an icosphere roughened, many in one mesh
_bm = bmesh.new()
bmesh.ops.create_icosphere(_bm, subdivisions=3, radius=1.0)
ICO_V = [v.co.copy() for v in _bm.verts]
ICO_F = [tuple(v.index for v in f.verts) for f in _bm.faces]
_bm.free()


def rock(mesh, center, size, seed, flat=0.0, turn=None):
    sx, sy, sz = size
    turn = R.uniform(0, 6.28) if turn is None else turn
    ct, st = math.cos(turn), math.sin(turn)
    verts = []
    for v in ICO_V:
        d = 1.0 + 0.28 * noise.noise(v * 1.1 + Vector((seed * 3.7, seed * 1.3, 0))) + 0.08 * noise.noise(v * 3.5 + Vector((seed, 0, 0)))
        p = v * d
        z = p.z
        if z < -0.35:
            z = -0.35 - (z + 0.35) * 0.2
        if flat and z > 0.45:
            z = 0.45 + (z - 0.45) * (1 - flat)
        lx, ly = p.x * sx, p.y * sy
        verts.append((center[0] + lx * ct - ly * st, center[1] + lx * st + ly * ct, center[2] + z * sz))
    mesh.add(verts, ICO_F, pp_piece=R.random())


rocks = Mesh('garden rocks')
# round the pond's edge
for k in range(46):
    a = 2 * math.pi * k / 46 + R.uniform(-0.05, 0.05)
    px, py = 2.45 + 3.08 * math.cos(a), 7.4 + 4.0 * math.sin(a)
    if pond_f(px, py) < 0.9:
        continue
    if px < 0.5 and 4.6 < py < 12.4:          # the stepping stones make this edge
        continue
    if 11.2 < py < 14.6 and 0.0 < px < 4.4:   # the channel under the bridge
        continue
    sz = R.uniform(0.22, 0.42)
    rock(rocks, (px, py, ground_z(px, py) + 0.02), (R.uniform(0.28, 0.5), R.uniform(0.25, 0.42), sz), k)
for k in range(16):                            # the channel's banks
    a = 2 * math.pi * k / 16
    px, py = 2.2 + 2.0 * math.cos(a), 12.9 + 1.8 * math.sin(a)
    if py < 11.6 or abs(py - 12.85) < 0.75:
        continue
    rock(rocks, (px, py, ground_z(px, py)), (R.uniform(0.3, 0.45), R.uniform(0.25, 0.4), R.uniform(0.2, 0.35)), 100 + k)
# the lantern's mound of rocks in the water
LANTERN_AT = (2.2, 5.3)
rock(rocks, (2.2, 5.3, -0.12), (0.62, 0.5, 0.42), 201, flat=0.85, turn=0.3)
rock(rocks, (2.75, 5.05, -0.15), (0.45, 0.4, 0.35), 202)
rock(rocks, (1.7, 5.5, -0.15), (0.4, 0.35, 0.3), 203)
rock(rocks, (2.5, 5.8, -0.2), (0.5, 0.45, 0.3), 204)
# feature rocks
rock(rocks, (0.85, 4.35, -0.02), (0.55, 0.42, 0.42), 210)
rock(rocks, (4.4, 5.6, 0.1), (0.7, 0.55, 0.55), 211)
rock(rocks, (3.3, 9.7, -0.25), (0.45, 0.4, 0.32), 212)
rock(rocks, (0.3, 12.55, -0.05), (0.42, 0.42, 0.35), 213)
rock(rocks, (4.15, 12.6, -0.05), (0.42, 0.42, 0.35), 214)
rock(rocks, (1.55, 3.6, 0.0), (0.35, 0.3, 0.26), 215)
rock(rocks, (0.75, 2.25, 0.0), (0.42, 0.3, 0.14), 216, flat=0.9)           # the front stone of the basin
rock(rocks, (1.62, 2.35, 0.0), (0.26, 0.24, 0.22), 217)
# pads under the veranda's posts
POST_Y = [2.2 + 1.8 * k for k in range(9)]
for py in POST_Y:
    rock(rocks, (-1.0, py, -0.02), (0.17, 0.17, 0.08), 300 + int(py * 10), flat=0.9)
    rock(rocks, (-2.75, py, -0.02), (0.17, 0.17, 0.08), 400 + int(py * 10), flat=0.9)
ROCKS = rocks.build(S_rock, smooth=True, ground=0.0)

M_puddle = mat_water('puddle water in hollows', ripple=0.12, scale=30.0)   # second pass: was 0.07, 24; a faint ripple breaks the mirror (Traps)
_pb = next(n for n in M_puddle.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
_pb.inputs['IOR'].default_value = 1.9
_pb.inputs['Specular IOR Level'].default_value = 1.0
_pb.inputs['Base Color'].default_value = (0.03, 0.028, 0.024, 1.0)   # second pass: the stone shows through where the water mirrors the dark eave
pw = Mesh('puddles in the slabs\' hollows')
for (x0, x1, y0, y1, zt, dish) in DISH_SLABS:
    lantern_puddle = math.hypot((x0 + x1) / 2 + 0.05, (y0 + y1) / 2 - 2.15) < 0.4
    lvl = zt - dish * (0.36 if lantern_puddle else 0.56)   # second pass: was 0.42 for all; smaller, ragged puddles, the lantern's kept
    # second pass: the water an ellipse inside the stone (a rectangle's corners stood out past the knocked-off corners)
    ecx, ecy, erx, ery = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 - 0.035, (y1 - y0) / 2 - 0.035
    pw.add([(ecx, ecy, lvl)] + [(ecx + erx * math.cos(2 * math.pi * i / 28), ecy + ery * math.sin(2 * math.pi * i / 28), lvl) for i in range(28)],
           [(0, 1 + i, 1 + (i + 1) % 28) for i in range(28)])
pw.build(M_puddle)
S_gravel = moss.add(store_copy('SURFACE • gravel_road', 'path bed gravel, wet', wet=0.9, darken=0.95), amount=0.6, foot=0.0, facing=(0.2, 0.8), scale=11.0, colour=(0.02, 0.03, 0.008))   # second pass: darker joints
bed = Mesh('path bed, gravel and moss')
bvs = []
for j in range(32):
    for i in range(12):
        x, y = -0.9 + 1.48 * i / 11, -0.1 + 4.85 * j / 31
        bvs.append((x, y, ground_z(x, y) + 0.008))
bed.add(bvs, [(j * 12 + i, j * 12 + i + 1, (j + 1) * 12 + i + 1, (j + 1) * 12 + i) for j in range(31) for i in range(11)])
bed.build(S_gravel, smooth=True, ground=0.0)


# ===================================================================================================== the veranda wing
log('veranda')
DECK_Z = 0.45
V_Y0, V_Y1 = -3.0, 17.3
deck = Mesh('veranda deck boards')
xb = -2.86
while xb < -0.93:
    w = 0.152
    yy = V_Y0
    while yy < V_Y1:
        L = min(R.uniform(2.6, 3.9), V_Y1 - yy)
        deck.box((xb + w / 2, yy + L / 2, DECK_Z - 0.0175 + R.uniform(-0.002, 0.002)), (w - 0.007, L - 0.005, 0.035), pp_piece=R.random())
        yy += L
    xb += w
DECK = deck.build(S_deck, ground=0.0)

frame = Mesh('veranda timber')
frame.box((-0.94, (V_Y0 + V_Y1) / 2, DECK_Z - 0.1), (0.09, V_Y1 - V_Y0, 0.17))             # the deck's edge beam
for py in POST_Y:
    for px in (-1.0, -2.75):
        frame.box((px, py, (DECK_Z - 0.035) / 2 + 0.02), (0.1, 0.1, DECK_Z - 0.06))       # short legs on the pads
    frame.box((-1.9, py, DECK_Z - 0.12), (1.9, 0.09, 0.1))                                 # joists
TIMBER = frame.build(M_timber)

posts = Mesh('veranda posts, red')
for py in POST_Y:
    posts.box((-1.0, py, DECK_Z + 1.1), (0.125, 0.125, 2.2))
posts.box((-1.0, (V_Y0 + V_Y1) / 2, 2.62), (0.15, V_Y1 - V_Y0, 0.2))                    # the head beam
posts.box((-1.0, (V_Y0 + V_Y1) / 2, 2.2), (0.06, V_Y1 - V_Y0, 0.08))                     # a tie rail below it
POSTS = posts.build(M_red, ground=DECK_Z)

# the eave: rafters, sooty boards, fascia, tile ends
EAVE_X, EAVE_Z, WALL_X, TOP_Z = -0.22, 2.84, -2.95, 3.32
raft = Mesh('veranda rafters')
yy = V_Y0
while yy < V_Y1:
    raft.beam((WALL_X, yy, TOP_Z - 0.05), (EAVE_X - 0.02, yy, EAVE_Z - 0.03), 0.055, 0.085)
    yy += 0.33
RAFTERS = raft.build(M_rafter)
soff = Mesh('veranda soffit')
soff.add([(WALL_X, V_Y0, TOP_Z + 0.02), (EAVE_X, V_Y0, EAVE_Z + 0.03), (EAVE_X, V_Y1, EAVE_Z + 0.03), (WALL_X, V_Y1, TOP_Z + 0.02)], [(0, 1, 2, 3)])
soff.box((EAVE_X, (V_Y0 + V_Y1) / 2, EAVE_Z + 0.02), (0.045, V_Y1 - V_Y0, 0.2))
soff.build(M_soffit)
tiles = Mesh('veranda roof tiles')
tiles.add([(WALL_X - 0.2, V_Y0, TOP_Z + 0.12), (EAVE_X + 0.1, V_Y0, EAVE_Z + 0.13), (EAVE_X + 0.1, V_Y1, EAVE_Z + 0.13), (WALL_X - 0.2, V_Y1, TOP_Z + 0.12)], [(0, 1, 2, 3)])
yy = V_Y0 + 0.1
while yy < V_Y1:
    tiles.cyl((WALL_X - 0.2, yy, TOP_Z + 0.16), (EAVE_X + 0.12, yy, EAVE_Z + 0.17), 0.05, seg=6)
    tiles.cyl((EAVE_X + 0.05, yy, EAVE_Z + 0.16), (EAVE_X + 0.16, yy, EAVE_Z + 0.155), 0.07, seg=10)
    yy += 0.27
tiles.build(M_tile)

# the wall of paper screens behind the veranda
LIT_BAYS = (1,)   # bays (between wall posts) lit from inside
wall = Mesh('veranda wall timber')
paper_dim, paper_lit = Mesh('veranda screens dim'), Mesh('veranda screens lit')
plaster = Mesh('veranda plaster')
for k in range(-3, 9):
    ya = 2.2 + 1.8 * k - 0.9 + 0.9
    yb = ya + 1.8
    if yb < V_Y0 or ya > V_Y1:
        continue
    wall.box((WALL_X + 0.03, ya, 1.65), (0.11, 0.11, 2.6))                     # wall post
    wall.box((WALL_X + 0.03, (ya + yb) / 2, 2.08), (0.1, 1.8, 0.1))           # lintel
    wall.box((WALL_X + 0.03, (ya + yb) / 2, DECK_Z + 0.03), (0.1, 1.8, 0.06))  # sill
    plaster.add([(WALL_X, ya, 2.13), (WALL_X, yb, 2.13), (WALL_X, yb, TOP_Z), (WALL_X, ya, TOP_Z)], [(0, 1, 2, 3)])
    target = paper_lit if k in LIT_BAYS else paper_dim
    for half in (0, 1):
        y0p = ya + 0.05 + half * 0.875
        y1p = y0p + 0.85
        target.add([(WALL_X - 0.01, y0p, DECK_Z + 0.06), (WALL_X - 0.01, y1p, DECK_Z + 0.06), (WALL_X - 0.01, y1p, 2.03), (WALL_X - 0.01, y0p, 2.03)], [(0, 1, 2, 3)])
        xL = WALL_X + 0.02 + half * 0.02
        for yb2 in (y0p, y1p):
            wall.box((xL, yb2, (DECK_Z + 2.03) / 2), (0.035, 0.035, 2.03 - DECK_Z))
        for i in range(1, 4):
            wall.box((xL, y0p + i * 0.2125, (DECK_Z + 2.03) / 2), (0.018, 0.016, 2.03 - DECK_Z))
        zz = DECK_Z + 0.08
        while zz < 2.03:
            wall.box((xL, (y0p + y1p) / 2, zz), (0.018, 0.85, 0.016))
            zz += 0.26
        wall.box((xL, (y0p + y1p) / 2, DECK_Z + 0.13), (0.035, 0.85, 0.16))   # the screen's bottom rail
wall.build(M_lattice)
plaster.build(S_plaster)
paper_dim.build(M_shoji_dim)
PAPER_LIT = paper_lit.build(M_shoji_lit)
PAPER_LIT.visible_shadow = False


def light(name, kind, location, energy, colour, size=0.1, rot=None, size_y=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = colour
    if kind == 'AREA':
        if size_y:
            ld.shape = 'RECTANGLE'
            ld.size, ld.size_y = size, size_y
        else:
            ld.size = size
    elif kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = location
    if rot is not None:
        ob.rotation_euler = rot
    ob.visible_camera = False
    if kind == 'AREA':
        ob.visible_glossy = False
    return ob


for k in LIT_BAYS:
    yc = 2.2 + 1.8 * k + 0.9
    light('screen spill %d' % k, 'AREA', (WALL_X + 0.25, yc, 1.25), 38.0, (1.0, 0.58, 0.28), 1.6, Euler((0, math.radians(-90), 0)), 1.4)


# hanging lanterns from the eave
def hanging_lantern(x, y, z_top, z_bottom, energy):
    fr = Mesh('hanging lantern frame %.1f' % y)
    pane = Mesh('hanging lantern panes %.1f' % y)
    hw = 0.13
    z0, z1 = z_bottom, z_bottom + 0.34
    for sx in (-1, 1):
        for sy in (-1, 1):
            fr.box((x + sx * hw, y + sy * hw, (z0 + z1) / 2), (0.028, 0.028, z1 - z0))
    for zz in (z0, z1, z0 + 0.17):
        for sx in (-1, 1):
            fr.box((x + sx * hw, y, zz), (0.022, 2 * hw, 0.022))
            fr.box((x, y + sx * hw, zz), (2 * hw, 0.022, 0.022))
    fr.box((x, y, z0 - 0.02), (2 * hw + 0.05, 2 * hw + 0.05, 0.03))
    # roof cap: a low pyramid
    c = 0.21
    fr.add([(x - c, y - c, z1 + 0.01), (x + c, y - c, z1 + 0.01), (x + c, y + c, z1 + 0.01), (x - c, y + c, z1 + 0.01), (x, y, z1 + 0.13)],
           [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)])
    fr.cyl((x, y, z1 + 0.12), (x, y, z1 + 0.19), 0.025, seg=8)
    ch = Mesh('lantern chain %.1f' % y)
    zz = z1 + 0.19
    while zz < z_top:
        ch.cyl((x, y, zz), (x, y, zz + 0.05), 0.008, seg=6)
        zz += 0.06
    ch.build(M_iron)
    fr.build(M_timber)
    for sx in (-1, 1):
        pane.add([(x + sx * (hw - 0.004), y - hw, z0), (x + sx * (hw - 0.004), y + hw, z0), (x + sx * (hw - 0.004), y + hw, z1), (x + sx * (hw - 0.004), y - hw, z1)], [(0, 1, 2, 3)])
        pane.add([(x - hw, y + sx * (hw - 0.004), z0), (x + hw, y + sx * (hw - 0.004), z0), (x + hw, y + sx * (hw - 0.004), z1), (x - hw, y + sx * (hw - 0.004), z1)], [(0, 1, 2, 3)])
    p = pane.build(M_lantern_paper)
    p.visible_shadow = False
    light('lantern light %.1f' % y, 'POINT', (x, y, (z0 + z1) / 2), energy, (1.0, 0.55, 0.22), 0.07)


hanging_lantern(-0.62, 4.95, 2.86, 1.98, 30.0)
hanging_lantern(-0.62, 10.35, 2.86, 1.98, 32.0)
hanging_lantern(-0.62, 15.75, 2.86, 1.98, 28.0)


# ===================================================================================================== things people left
log('jar, clogs, basin, spout, fence')
scene_depsgraph = bpy.context.evaluated_depsgraph_get()


def top_at(x, y, objs=None):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nor, idx, ob, mtx = scene.ray_cast(dg, Vector((x, y, 1.5)), Vector((0, 0, -1)))
    return (loc.z, nor) if hit else (ground_z(x, y), Vector((0, 0, 1)))


jar = Mesh('blue-and-white jar')
JAR_AT = (-0.74, 0.9)
jz, _ = top_at(*JAR_AT)
lathe(jar, [(0.0, 0.0), (0.125, 0.0), (0.15, 0.025), (0.2, 0.11), (0.248, 0.24), (0.255, 0.33), (0.23, 0.42), (0.17, 0.5), (0.11, 0.545),
            (0.096, 0.575), (0.104, 0.61), (0.118, 0.625), (0.11, 0.635), (0.09, 0.63), (0.085, 0.6), (0.0, 0.57)], (0, 0, 0), seg=40)
JAR = jar.build(M_jar, smooth=True)
JAR.location = (JAR_AT[0], JAR_AT[1], jz - 0.004)
JAR.rotation_euler = (0, 0, 0.6)
JAR.scale = (0.78, 0.78, 0.78)

def clog(name, at, turn, tipped=False):
    """A geta: a thin paulownia platform on two teeth, a red thong in a V; built at the origin, then stood where it goes."""
    g, t = Mesh(name), Mesh(name + ' thong')
    # the platform: a rounded slab (an octagon in plan), not a box
    oc = []
    for k in range(16):                       # a rounded rectangle (superellipse) 0.104 x 0.232
        a = 2 * math.pi * k / 16
        ca, sa = math.cos(a), math.sin(a)
        oc.append((0.052 * math.copysign(abs(ca) ** 0.5, ca), 0.116 * math.copysign(abs(sa) ** 0.5, sa)))
    g.add([(x, y, 0.055) for x, y in oc] + [(x, y, 0.081) for x, y in oc],
          [tuple(reversed(range(16))), tuple(range(16, 32))] + [(k, (k + 1) % 16, 16 + (k + 1) % 16, 16 + k) for k in range(16)])
    for ty in (-0.068, 0.07):
        g.box((0, ty, 0.028), (0.098, 0.02, 0.056))
    t.cyl((0, 0.072, 0.082), (-0.042, -0.012, 0.104), 0.0075, seg=6)
    t.cyl((0, 0.072, 0.082), (0.042, -0.012, 0.104), 0.0075, seg=6)
    t.cyl((-0.042, -0.012, 0.104), (-0.047, -0.03, 0.082), 0.006, seg=6)
    t.cyl((0.042, -0.012, 0.104), (0.047, -0.03, 0.082), 0.006, seg=6)
    obs = [g.build(M_geta), t.build(M_thong)]
    for ob in obs:
        if tipped:            # on its side: the long edge down, the sole with its two teeth turned to the eye
            ob.rotation_euler = Euler((0.0, math.radians(90), math.radians(turn)), 'XYZ')
            ob.location = (at[0], at[1], 0.24 + 0.052)
        else:
            ob.rotation_euler = Euler((0.0, 0.0, math.radians(turn)), 'XYZ')
            ob.location = (at[0], at[1], 0.24)
    return obs


clog('clog left', (-0.74, 2.8), -84)          # a neat pair, toes to the garden, as guests leave them on the step stone
clog('clog right', (-0.73, 2.95), -78)

# the stone water basin, with the bamboo spout pouring into it
BASIN_AT = (1.13, 2.69)
basin = Mesh('stone basin')
lathe(basin, [(0.36, -0.08), (0.43, 0.08), (0.455, 0.28), (0.42, 0.45), (0.36, 0.53), (0.28, 0.55), (0.245, 0.52), (0.21, 0.43), (0.12, 0.385), (0.0, 0.38)],
      (BASIN_AT[0], BASIN_AT[1], 0.0), seg=36, wobble=0.035, seed=4)
basin.build(S_rock, smooth=True, ground=0.0)
bw = Mesh('basin water')
seg = 24
bw.add([(BASIN_AT[0], BASIN_AT[1], 0.495)] + [(BASIN_AT[0] + 0.25 * math.cos(2 * math.pi * i / seg), BASIN_AT[1] + 0.25 * math.sin(2 * math.pi * i / seg), 0.495) for i in range(seg)],
       [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)])
bw.build(M_basin_water)

bam = Mesh('bamboo spout and post')
SP_POST = (1.86, 3.06)
bam.cyl((SP_POST[0], SP_POST[1], -0.05), (SP_POST[0], SP_POST[1], 1.02), 0.045, seg=10)
for zz in (0.3, 0.68, 1.0):
    bam.cyl((SP_POST[0], SP_POST[1], zz - 0.012), (SP_POST[0], SP_POST[1], zz + 0.012), 0.05, seg=10)
MOUTH = Vector((1.25, 2.76, 0.8))
start = Vector((SP_POST[0] + 0.02, SP_POST[1] + 0.01, 0.92))
bam.cyl(start, MOUTH, 0.03, seg=10, caps=False)
bam.cyl(start, start + (start - MOUTH).normalized() * 0.03, 0.03, seg=10)
mid = start.lerp(MOUTH, 0.45)
bam.cyl(mid - (MOUTH - start).normalized() * 0.01, mid + (MOUTH - start).normalized() * 0.01, 0.034, seg=10)
bam.build(M_bamboo_old)
# the inside of the pipe, dark
inn = Mesh('spout inside')
inn.cyl(start.lerp(MOUTH, 0.7), MOUTH + (MOUTH - start).normalized() * -0.002, 0.024, seg=10, caps=True)
inn.build(M_cord)
stream = Mesh('falling water')
d = (MOUTH - start).normalized()
pts, radii = [], []
for i in range(9):
    t = i / 8.0
    p = MOUTH + Vector((d.x, d.y, 0)).normalized() * (0.07 * t) + Vector((0, 0, -0.31 * t * t - 0.01 * t))
    pts.append(p)
    radii.append(0.009 - 0.004 * t)
stream.tube(pts, radii, seg=6)
STREAM = stream.build(M_stream, smooth=True)

ladle = Mesh('bamboo ladle')
ladle.cyl((BASIN_AT[0] - 0.3, BASIN_AT[1] - 0.12, 0.555), (BASIN_AT[0] + 0.12, BASIN_AT[1] + 0.05, 0.565), 0.009, seg=6)
ladle.cyl((BASIN_AT[0] + 0.1, BASIN_AT[1] + 0.04, 0.545), (BASIN_AT[0] + 0.1, BASIN_AT[1] + 0.04, 0.62), 0.036, seg=12)
ladle.build(M_bamboo_old)

# the bamboo fence in the near right corner
fence = Mesh('bamboo fence')
ties = Mesh('fence ties')
F0, F1 = Vector((0.53, 0.6, 0)), Vector((1.27, 2.17, 0))
fd = (F1 - F0)
FL = fd.length
fd.normalize()
for t in (0.0, 0.5, 1.0):
    p = F0 + fd * FL * t
    fence.cyl((p.x, p.y, -0.05), (p.x, p.y, 0.78), 0.036, seg=10)
    fence.cyl((p.x, p.y, 0.765), (p.x, p.y, 0.79), 0.04, seg=10)
for zz in (0.2, 0.47, 0.72):
    a = F0 - fd * 0.08
    b2 = F1 + fd * 0.08
    fence.cyl((a.x, a.y, zz), (b2.x, b2.y, zz + R.uniform(-0.01, 0.01)), 0.02, seg=8)
n_up = int(FL / 0.21)
side = Vector((-fd.y, fd.x, 0))
for i in range(1, n_up):
    p = F0 + fd * (FL * i / n_up)
    if abs(i / n_up - 0.5) < 0.04:
        continue
    q = p + side * 0.03
    fence.cyl((q.x, q.y, -0.03), (q.x, q.y, 0.66 + R.uniform(-0.03, 0.03)), 0.016, seg=8)
    for zz in (0.2, 0.47):
        ties.cyl(q + side * -0.014 + Vector((0, 0, zz - 0.012)), q + side * 0.03 + Vector((0, 0, zz + 0.012)), 0.007, seg=5)
        ties.cyl(q + side * -0.014 + Vector((0, 0, zz + 0.012)), q + side * 0.03 + Vector((0, 0, zz - 0.012)), 0.007, seg=5)
fence.build(M_bamboo_old)
ties.build(M_cord)


# ===================================================================================================== the stone lantern
log('stone lantern')
lz, _ = top_at(*LANTERN_AT)
LX, LY = LANTERN_AT
st = Mesh('stone lantern')
glow = Mesh('stone lantern paper')


def hexring(r, z, turn=0.0, cx=LX, cy=LY):
    return [(cx + r * math.cos(turn + i * math.pi / 3), cy + r * math.sin(turn + i * math.pi / 3), z) for i in range(6)]


def hexprism(mesh, r0, r1, z0, z1, turn=0.0):
    a, b = hexring(r0, z0, turn), hexring(r1, z1, turn)
    faces = [(i, (i + 1) % 6, 6 + (i + 1) % 6, 6 + i) for i in range(6)] + [tuple(reversed(range(6))), tuple(range(6, 12))]
    mesh.add(a + b, faces, pp_piece=R.random())


z = lz - 0.02
hexprism(st, 0.27, 0.25, z, z + 0.11)
z += 0.11
hexprism(st, 0.2, 0.17, z, z + 0.06)
z += 0.06
st.cyl((LX, LY, z), (LX, LY, z + 0.5), 0.09, 0.08, seg=10, pp_piece=0.3)
z += 0.5
hexprism(st, 0.13, 0.24, z, z + 0.09)
z += 0.09
hexprism(st, 0.24, 0.24, z, z + 0.04)
z += 0.04
FB0, FB1 = z, z + 0.26
for i in range(6):
    a = i * math.pi / 3
    st.box((LX + 0.17 * math.cos(a), LY + 0.17 * math.sin(a), (FB0 + FB1) / 2), (0.045, 0.045, FB1 - FB0), rot=Euler((0, 0, a)).to_quaternion())
ring_lo, ring_hi = hexring(0.155, FB0 + 0.02), hexring(0.155, FB1 - 0.02)
for i in range(6):
    j = (i + 1) % 6
    glow.add([ring_lo[i], ring_lo[j], ring_hi[j], ring_hi[i]], [(0, 1, 2, 3)])
hexprism(st, 0.2, 0.2, FB0 - 0.005, FB0 + 0.02)
z = FB1
# the cap: wide, thin at its edge, the corners curled up
edge = hexring(0.4, z + 0.05)
edge = [(LX + (p[0] - LX) * 1.06, LY + (p[1] - LY) * 1.06, p[2] + 0.07) for p in edge]
mid_r = []
for i in range(6):
    a0, a1 = i * math.pi / 3, (i + 1) * math.pi / 3
    am = (a0 + a1) / 2
    mid_r.append((LX + 0.36 * math.cos(am), LY + 0.36 * math.sin(am), z + 0.05))
rim = []
for i in range(6):
    rim.append(edge[i])
    rim.append(mid_r[i])
under = [(LX + (p[0] - LX) * 0.55, LY + (p[1] - LY) * 0.55, z) for p in rim]
top_low = [(p[0], p[1], p[2] + 0.04) for p in rim]
nv = 12
verts = under + rim + top_low
faces = [tuple(reversed(range(nv)))]
for i in range(nv):
    j = (i + 1) % nv
    faces.append((i, j, nv + j, nv + i))
    faces.append((nv + i, nv + j, 2 * nv + j, 2 * nv + i))
st.add(verts, faces, pp_piece=0.6)
apex = [(LX + 0.1 * math.cos(k * math.pi / 6), LY + 0.1 * math.sin(k * math.pi / 6), z + 0.25) for k in range(12)]
st.add(top_low + apex, [(i, (i + 1) % 12, 12 + (i + 1) % 12, 12 + i) for i in range(12)] + [tuple(range(12, 24))], pp_piece=0.6)
z += 0.25
st.cyl((LX, LY, z - 0.01), (LX, LY, z + 0.05), 0.075, 0.07, seg=10)
lathe(st, [(0.0, 0.0), (0.06, 0.005), (0.085, 0.05), (0.08, 0.1), (0.05, 0.15), (0.02, 0.185), (0.0, 0.2)], (LX, LY, z + 0.05), seg=12)
STONE_LANTERN = st.build(S_lantern, smooth=False, ground=lz)
SL_GLOW = glow.build(M_stone_window)
SL_GLOW.visible_shadow = False
light('stone lantern light', 'POINT', (LX, LY, (FB0 + FB1) / 2), 26.0, (1.0, 0.52, 0.2), 0.05)


# ===================================================================================================== the arched bridge
log('bridge')
BX0, BX1, BYC, BW = 0.15, 4.25, 12.85, 1.3
XM, HS, RISE, ZEND = (BX0 + BX1) / 2, (BX1 - BX0) / 2, 1.0, 0.06
RAD = (RISE ** 2 + HS ** 2) / (2 * RISE)
ZC = ZEND + RISE - RAD


def arch_z(x):
    return ZC + math.sqrt(max(RAD ** 2 - (x - XM) ** 2, 0.0))


br = Mesh('bridge timber, red')
deckb = Mesh('bridge deck boards')
xs = [BX0 + (BX1 - BX0) * i / 40 for i in range(41)]
for ys in (BYC - BW / 2, BYC + BW / 2):
    br.sweep([(x, ys, arch_z(x) - 0.13) for x in xs], 0.1, 0.22, pp_piece=0.2)              # stringers
    br.sweep([(x, ys, arch_z(x) + 0.8) for x in xs], 0.085, 0.07)                          # top rail
    br.sweep([(x, ys, arch_z(x) + 0.42) for x in xs], 0.05, 0.05)                          # middle rail
    n_posts = 8
    for i in range(n_posts + 1):
        x = BX0 + 0.06 + (BX1 - BX0 - 0.12) * i / n_posts
        top = 0.95 if i in (0, n_posts) else 0.8
        br.box((x, ys, arch_z(x) + top / 2 - 0.05), (0.075, 0.075, top + 0.1))
# deck boards across, following the arch
sarc = 0.0
x = BX0
while x < BX1 - 0.05:
    z0 = arch_z(x)
    slope = (arch_z(x + 0.01) - z0) / 0.01
    ang = math.atan(slope)
    w = 0.14
    deckb.box((x + math.cos(ang) * w / 2, BYC, z0 + 0.015 + math.sin(ang) * w / 2), (w - 0.012, BW + 0.06, 0.035), rot=Euler((0, -ang, 0)).to_quaternion(), pp_piece=R.random())
    x += math.cos(ang) * w
# under the arch: posts standing in the water with cross beams
for px in (1.15, 2.2, 3.25):
    for ys in (BYC - BW / 2 + 0.06, BYC + BW / 2 - 0.06):
        br.box((px, ys, (-0.6 + arch_z(px) - 0.2) / 2), (0.1, 0.1, arch_z(px) - 0.2 + 0.6))
    br.box((px, BYC, arch_z(px) - 0.27), (0.08, BW, 0.1))
    br.box((px, BYC, -0.02), (0.07, BW, 0.08))
BRIDGE = br.build(M_red_bridge, ground=0.0)
deckb.build(S_wood, ground=0.0)
caps = Mesh('bridge post caps')
for ys in (BYC - BW / 2, BYC + BW / 2):
    for x in (BX0 + 0.06, BX1 - 0.06):
        zt = arch_z(x) + 0.9
        lathe(caps, [(0.0, 0.0), (0.05, 0.0), (0.055, 0.03), (0.07, 0.07), (0.06, 0.11), (0.03, 0.15), (0.008, 0.2), (0.0, 0.21)], (x, ys, zt), seg=12)
caps.build(store.material('MADE • old copper'), smooth=True)


# ===================================================================================================== the inn
log('inn')
IX0, IX1 = -5.5, 8.5
FRONT = 17.5
inn_t = Mesh('inn timber')
inn_p = Mesh('inn plaster')
inn_dim = Mesh('inn screens dim')
inn_lit = Mesh('inn screens lit')
inn_tile = Mesh('inn roof tiles')
inn_soff = Mesh('inn soffits')
inn_base = Mesh('inn stone base')
inn_deck = Mesh('inn veranda boards')
inn_base.box(((IX0 + IX1) / 2, FRONT + 3.3, 0.27), (IX1 - IX0 + 0.2, 6.6, 0.56))
inn_base.build(S_base, ground=0.0)
# ground floor veranda
inn_deck.box(((IX0 + IX1) / 2, FRONT + 0.55, 0.585), (IX1 - IX0, 1.2, 0.05))
inn_deck.build(S_deck, ground=0.0)
BAY = (IX1 - IX0) / 8
G_LIT = (2, 5)
U_LIT = (1, 5)
WALL1 = FRONT + 1.1
for k in range(9):
    x = IX0 + k * BAY
    inn_t.box((x, FRONT + 0.05, 1.95), (0.17, 0.17, 2.8))                # veranda posts
    inn_t.box((x, WALL1, 1.95), (0.15, 0.15, 2.8))                       # wall posts
inn_t.box(((IX0 + IX1) / 2, FRONT + 0.05, 3.3), (IX1 - IX0 + 0.3, 0.2, 0.22))   # beam over the veranda posts
inn_t.box(((IX0 + IX1) / 2, WALL1, 2.4), (IX1 - IX0, 0.14, 0.12))               # lintel
for k in range(8):
    xa = IX0 + k * BAY
    lit = k in G_LIT
    tgt = inn_lit if lit else inn_dim
    for half in range(2):
        x0p = xa + 0.08 + half * (BAY / 2 - 0.04)
        x1p = x0p + BAY / 2 - 0.12
        tgt.add([(x0p, WALL1 + 0.02, 0.62), (x1p, WALL1 + 0.02, 0.62), (x1p, WALL1 + 0.02, 2.33), (x0p, WALL1 + 0.02, 2.33)], [(0, 1, 2, 3)])
        for xx in (x0p, x1p):
            inn_t.box((xx, WALL1 - 0.01, 1.47), (0.04, 0.04, 1.71))
        for i in range(1, 3):
            inn_t.box((x0p + (x1p - x0p) * i / 3, WALL1 - 0.01, 1.47), (0.02, 0.02, 1.71))
        zz = 0.75
        while zz < 2.33:
            inn_t.box(((x0p + x1p) / 2, WALL1 - 0.01, zz), (x1p - x0p, 0.02, 0.02))
            zz += 0.3
    # band of lattice and plaster above
    inn_p.add([(xa, WALL1 + 0.03, 2.46), (xa + BAY, WALL1 + 0.03, 2.46), (xa + BAY, WALL1 + 0.03, 3.3), (xa, WALL1 + 0.03, 3.3)], [(0, 1, 2, 3)])
for k in G_LIT:
    xc = IX0 + (k + 0.5) * BAY
    light('inn ground screen spill %d' % k, 'AREA', (xc, WALL1 - 0.35, 1.5), 40.0, (1.0, 0.56, 0.26), 1.5, Euler((math.radians(-90), 0, 0)), 1.4)
# hanging round paper lanterns under the lower eave
for k in (1, 3, 5, 7):
    xc = IX0 + k * BAY
    rl = Mesh('round lantern %d' % k)
    lathe(rl, [(0.0, -0.2), (0.1, -0.19), (0.16, -0.12), (0.18, 0.0), (0.16, 0.12), (0.1, 0.19), (0.0, 0.2)], (xc, FRONT - 0.25, 2.75), seg=14)
    o = rl.build(M_round_lantern, smooth=True)
    o.visible_shadow = False
    light('round lantern light %d' % k, 'POINT', (xc, FRONT - 0.25, 2.75), 9.0, (1.0, 0.5, 0.2), 0.1)


def roof(mesh, soff, x0, x1, y_eave, z_eave, y_top, z_top, upturn=0.3, roll_r=0.065, step=0.3, rafters=True, ridge=False):
    """A tiled roof slope rising from the eave (towards +Y) with a concave profile, corners turned up, rolls of tiles in
    relief, round tile ends on the eave, a fascia, and rafters under the overhang."""
    def zf(x, u):
        z = z_eave + (z_top - z_eave) * (u ** 1.45)
        ends = max(0.0, (abs(x - (x0 + x1) / 2) - ((x1 - x0) / 2 - 1.6)) / 1.6)
        return z + upturn * ends * ends * (1 - u) ** 1.5

    def yf(u):
        return y_eave + (y_top - y_eave) * u
    nxr, nu = 48, 10
    vs, fs = [], []
    for j in range(nu + 1):
        u = j / nu
        for i in range(nxr + 1):
            x = x0 + (x1 - x0) * i / nxr
            vs.append((x, yf(u), zf(x, u)))
    for j in range(nu):
        for i in range(nxr):
            a = j * (nxr + 1) + i
            fs.append((a, a + 1, a + nxr + 2, a + nxr + 1))
    mesh.add(vs, fs)
    x = x0 + step / 2
    while x < x1:
        pts = [(x, yf(u), zf(x, u) + roll_r * 0.6) for u in [i / 10 for i in range(11)]]
        mesh.tube(pts, [roll_r] * len(pts), seg=6)
        p0 = Vector(pts[0])
        dvec = (Vector(pts[1]) - p0).normalized()
        mesh.cyl(p0 - dvec * 0.03, p0 + dvec * 0.06, roll_r * 1.25, seg=10)
        x += step
    # fascia along the eave
    fas = [(x0 + (x1 - x0) * i / 30, yf(0) + 0.02, zf(x0 + (x1 - x0) * i / 30, 0) - 0.1) for i in range(31)]
    soff.sweep(fas, 0.06, 0.2)
    if rafters:
        x = x0 + 0.15
        while x < x1:
            soff.beam((x, yf(0) + 0.05, zf(x, 0) - 0.16), (x, yf(0) + 1.0, zf(x, 0.0) + 0.05), 0.06, 0.09)
            x += 0.36
        soff.add([(x0, yf(0), zf(x0, 0) - 0.06), (x1, yf(0), zf(x1, 0) - 0.06), (x1, yf(0) + 1.1, zf(x1, 0) + 0.12), (x0, yf(0) + 1.1, zf(x0, 0) + 0.12)], [(0, 1, 2, 3)])
    if ridge:
        rp = [(x0 + 0.4 + (x1 - x0 - 0.8) * i / 30, y_top, z_top + 0.2) for i in range(31)]
        mesh.sweep(rp, 0.42, 0.42)
        for xe, sgn in ((x0 + 0.4, -1), (x1 - 0.4, 1)):
            mesh.beam((xe, y_top, z_top), (xe + sgn * 0.35, y_top, z_top + 0.75), 0.42, 0.3)
    return zf


# the lower roof along the front
roof(inn_tile, inn_soff, IX0 - 0.6, IX1 + 0.6, FRONT - 0.85, 3.3, WALL1 + 0.35, 3.95, upturn=0.25)
# upper floor
WALL2 = FRONT + 1.35
for k in range(9):
    x = IX0 + k * BAY
    inn_t.box((x, WALL2, 5.3), (0.15, 0.15, 2.8))
inn_t.box(((IX0 + IX1) / 2, WALL2, 4.0), (IX1 - IX0 + 0.2, 0.16, 0.16))
inn_t.box(((IX0 + IX1) / 2, WALL2, 6.6), (IX1 - IX0 + 0.2, 0.18, 0.2))
for k in range(8):
    xa = IX0 + k * BAY
    tgt = inn_lit if k in U_LIT else inn_dim
    x0p, x1p = xa + 0.1, xa + BAY - 0.1
    tgt.add([(x0p, WALL2 + 0.03, 4.35), (x1p, WALL2 + 0.03, 4.35), (x1p, WALL2 + 0.03, 6.05), (x0p, WALL2 + 0.03, 6.05)], [(0, 1, 2, 3)])
    nb = 6
    for i in range(nb + 1):
        inn_t.box((x0p + (x1p - x0p) * i / nb, WALL2 - 0.0, 5.2), (0.03 if i in (0, nb) else 0.018, 0.03, 1.7))
    zz = 4.35
    while zz <= 6.06:
        inn_t.box(((x0p + x1p) / 2, WALL2 - 0.0, zz), (x1p - x0p, 0.03, 0.022))
        zz += 0.34
    inn_p.add([(xa, WALL2 + 0.04, 4.08), (xa + BAY, WALL2 + 0.04, 4.08), (xa + BAY, WALL2 + 0.04, 4.35), (xa, WALL2 + 0.04, 4.35)], [(0, 1, 2, 3)])
    inn_p.add([(xa, WALL2 + 0.04, 6.05), (xa + BAY, WALL2 + 0.04, 6.05), (xa + BAY, WALL2 + 0.04, 6.55), (xa, WALL2 + 0.04, 6.55)], [(0, 1, 2, 3)])
for k in U_LIT:
    xc = IX0 + (k + 0.5) * BAY
    light('inn upper screen spill %d' % k, 'AREA', (xc, WALL2 - 0.8, 5.2), 30.0, (1.0, 0.56, 0.26), 1.4, Euler((math.radians(-90), 0, 0)), 1.4)
# upper balcony with a railing of thin posts
BAL = FRONT + 0.7
inn_t.box(((IX0 + IX1) / 2, (BAL + WALL2) / 2, 4.08), (IX1 - IX0 + 0.1, WALL2 - BAL + 0.1, 0.08))
inn_t.box(((IX0 + IX1) / 2, BAL, 4.85), (IX1 - IX0 + 0.1, 0.08, 0.07))
inn_t.box(((IX0 + IX1) / 2, BAL, 4.25), (IX1 - IX0 + 0.1, 0.05, 0.05))
x = IX0
while x <= IX1 + 0.01:
    inn_t.box((x, BAL, 4.47), (0.028 if (abs((x - IX0) / BAY - round((x - IX0) / BAY)) > 0.05) else 0.09, 0.028, 0.75))
    x += 0.145
# the main roof, its ridge, the gable ends, and a small gable on the front
zf_main = roof(inn_tile, inn_soff, IX0 - 1.0, IX1 + 1.0, WALL2 - 1.1, 6.85, FRONT + 3.9, 9.45, upturn=0.45, roll_r=0.07, ridge=True)
for xg in (IX0, IX1):
    inn_p.add([(xg, WALL2, 6.6), (xg, FRONT + 3.9, 9.25), (xg, FRONT + 6.5, 6.6)], [(0, 1, 2)])
inn_tile.add([(IX0 - 1.0, FRONT + 3.9, 9.45), (IX1 + 1.0, FRONT + 3.9, 9.45), (IX1 + 1.0, FRONT + 7.6, 6.85), (IX0 - 1.0, FRONT + 7.6, 6.85)], [(0, 1, 2, 3)])
GX, GW = 1.5, 2.1
gy0, gy1 = WALL2 - 0.75, FRONT + 3.2
gz_top = 9.35
gz_eave = 7.55
for sgn in (-1, 1):
    vs = []
    for i in range(9):
        t = i / 8
        yy = gy0 + (gy1 - gy0) * t
        vs.append((GX, yy, gz_top))
        vs.append((GX + sgn * GW, yy, gz_eave))
    fs = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(8)]
    inn_tile.add(vs, fs)
    xr = GX + sgn * 0.15
    while abs(xr - GX) < GW:
        f = abs(xr - GX) / GW
        zr = gz_top + (gz_eave - gz_top) * f + 0.06
        inn_tile.cyl((xr, gy0, zr), (xr, gy1, zr), 0.06, seg=6)
        inn_tile.cyl((xr, gy0 - 0.06, zr), (xr, gy0 + 0.05, zr), 0.08, seg=10)
        xr += sgn * 0.3
    bp = [(GX + sgn * GW * t, gy0 - 0.03, gz_top + (gz_eave - gz_top) * t - 0.02 + 0.12 * math.sin(math.pi * t) * 0) for t in [i / 12 for i in range(13)]]
    inn_soff.sweep(bp, 0.08, 0.26)
inn_tile.sweep([(GX, gy0 - 0.1, gz_top + 0.15), (GX, gy1, gz_top + 0.15)], 0.3, 0.3)
inn_p.add([(GX - GW + 0.15, gy0 + 0.05, gz_eave + 0.05), (GX + GW - 0.15, gy0 + 0.05, gz_eave + 0.05), (GX, gy0 + 0.05, gz_top - 0.12)], [(0, 1, 2)])
for t in (0.33, 0.66):
    inn_t.box((GX + (t - 0.5) * 2 * (GW - 0.4), gy0 + 0.03, gz_eave + 0.6), (0.06, 0.04, 0.9))
inn_t.box((GX, gy0 + 0.03, gz_eave + 0.35), (2 * GW - 0.6, 0.04, 0.07))
INN_T = inn_t.build(M_timber)
inn_p.build(S_plaster)
inn_dim.build(M_shoji_dim)
INN_LIT = inn_lit.build(M_shoji_lit)
INN_LIT.visible_shadow = False
inn_tile.build(M_tile)
inn_soff.build(M_soffit)


# ===================================================================================================== water plants, leaves, ferns
log('leaves and plants')


def maple_outline():
    lobes = [(-102, 0.5), (-50, 0.86), (0, 1.0), (50, 0.86), (102, 0.5)]
    pts = []
    for i, (a, L) in enumerate(lobes):
        prev = lobes[i - 1][0] if i > 0 else -150
        va = (a + prev) / 2
        pts.append((va, 0.3 if i > 0 else 0.16))
        pts.append((a - 11, 0.62 * L))
        pts.append((a - 4, 0.8 * L))
        pts.append((a, L))
        pts.append((a + 4, 0.8 * L))
        pts.append((a + 11, 0.62 * L))
    pts.append((150, 0.16))
    pts.append((180, 0.12))
    return [(r * math.sin(math.radians(a)), r * math.cos(math.radians(a))) for a, r in pts]


MAPLE = maple_outline()


def maple_outline_fine():
    lobes = [(-140, 0.36), (-95, 0.68), (-48, 0.92), (0, 1.0), (48, 0.92), (95, 0.68), (140, 0.36)]
    pts = [(180.0, 0.08)]
    fr = [0.42, 0.55, 0.66, 0.77, 0.87]
    for i, (a, L) in enumerate(lobes):
        if i > 0:
            pa, pL = lobes[i - 1]
            pts.append(((a + pa) / 2.0, 0.38 * min(L, pL) + 0.03))
        for k, f in enumerate(fr):
            pts.append((a - 23.0 * ((1 - f) / 0.58) ** 0.55 - (4.0 if k % 2 else 0.0) * (1 - f), L * f))
        pts.append((a, L))
        for k, f in reversed(list(enumerate(fr))):
            pts.append((a + 23.0 * ((1 - f) / 0.58) ** 0.55 + (4.0 if k % 2 else 0.0) * (1 - f), L * f))
    return [(r * math.sin(math.radians(ang)), r * math.cos(math.radians(ang))) for ang, r in pts]


MAPLE_FINE = maple_outline_fine()


def add_leaf(mesh, center, size, normal, spin, tone, outline=MAPLE, droop=0.0, stem=False):
    nrm = Vector(normal).normalized()
    q = Vector((0, 0, 1)).rotation_difference(nrm).to_matrix() @ Matrix.Rotation(spin, 3, 'Z')
    c = Vector(center)
    verts = [c]
    luv = [(0.0, 0.0, 0.0)]
    for x, y in outline:
        verts.append(c + q @ Vector((x * size, y * size, -droop * (x * x + y * y) * size)))
        luv.append((x, y, 0.0))
    n = len(outline)
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    if stem:
        b = len(verts)
        for sx, sy in ((-0.018, 0.02), (0.018, 0.02), (0.012, -0.6), (-0.012, -0.6)):
            verts.append(c + q @ Vector((sx * size, sy * size, abs(sy) * 0.05 * size)))
            luv.append((0.0, 0.0, 0.0))
        faces.append((b, b + 1, b + 2, b + 3))
    mesh.add(verts, faces, tone=tone, _luv=luv)


# fallen leaves on the path and its edges, gathered at joints, the puddle's edge and the posts' feet
fallen = Mesh('fallen maple leaves')
bpy.context.view_layer.update()
for k in range(260):
    if k < 150:
        x, y = R.uniform(-0.85, 0.55), R.uniform(0.5, 4.8)
        if abs(x - (-0.17)) < 0.35 and R.random() < 0.6:
            continue
    elif k < 210:
        x, y = R.uniform(-0.6, 0.6), R.uniform(4.8, 11.5)
    else:
        x, y = R.uniform(0.5, 2.1), R.uniform(1.0, 4.4)
    if x < -0.88:
        continue
    zt, nor = top_at(x, y)
    if zt > 0.3 and abs(zt - 0.24) > 0.02:
        continue
    add_leaf(fallen, (x, y, zt + 0.004), R.uniform(0.075, 0.105), nor + Vector((R.uniform(-0.15, 0.15), R.uniform(-0.15, 0.15), 0)), R.uniform(0, 6.28), R.random(), outline=MAPLE_FINE, droop=-0.08, stem=True)
# leaves floating on the pond and in the basin
for k in range(40):
    x, y = R.uniform(-0.5, 5.2), R.uniform(4.6, 14.5)
    if pond_f(x, y) < 0.95:
        add_leaf(fallen, (x, y, WATER_Z + 0.004), R.uniform(0.07, 0.1), (0, 0, 1), R.uniform(0, 6.28), R.random(), outline=MAPLE_FINE, droop=-0.05, stem=True)
for k in range(4):
    a = R.uniform(0, 6.28)
    add_leaf(fallen, (BASIN_AT[0] + 0.15 * math.cos(a), BASIN_AT[1] + 0.15 * math.sin(a), 0.498), 0.075, (0, 0, 1), R.uniform(0, 6.28), R.random())
fallen.build(M_maple_ground)

# water-lily leaves: round with a notch, a few yellowed; three flowers
lily = Mesh('water-lily leaves')
flw = Mesh('water-lily flowers')
pads = []
for cx, cy, n, spread in ((2.0, 7.0, 9, 0.8), (3.4, 8.6, 10, 0.9), (1.2, 9.4, 6, 0.6), (3.8, 6.4, 5, 0.5), (2.6, 10.6, 5, 0.6)):
    for i in range(n):
        x, y = cx + R.gauss(0, spread * 0.6), cy + R.gauss(0, spread * 0.6)
        if pond_f(x, y) > 0.9:
            continue
        r = R.uniform(0.11, 0.22)
        notch = R.uniform(0, 6.28)
        outline = []
        for j in range(22):
            a = notch + math.radians(14) + (2 * math.pi - math.radians(28)) * j / 21
            rr = r * (1 + 0.04 * noise.noise(Vector((math.cos(a) * 3 + i, math.sin(a) * 3, 0.0))))
            outline.append((rr * math.cos(a), rr * math.sin(a)))
        outline.append((r * 0.05 * math.cos(notch), r * 0.05 * math.sin(notch)))
        verts = [(x, y, WATER_Z + 0.006)] + [(x + px, y + py, WATER_Z + 0.006 + 0.004 * (px * px + py * py) / (r * r)) for px, py in outline]
        nn = len(outline)
        lily.add(verts, [(0, 1 + j, 1 + (j + 1) % nn) for j in range(nn)], tone=R.random() ** 2)
        pads.append((x, y))
lily.build(M_lily)
for (fx, fy) in ((2.15, 7.25), (3.25, 8.75), (1.35, 9.3)):
    for layer, (n, L, lift) in enumerate(((10, 0.075, 0.55), (8, 0.06, 1.0))):
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * layer) / n
            base = Vector((fx, fy, WATER_Z + 0.02))
            dirv = Vector((math.cos(a), math.sin(a), lift)).normalized()
            sidev = Vector((-math.sin(a), math.cos(a), 0)) * 0.016
            tip = base + dirv * L
            flw.add([base - sidev * 0.3, base + sidev * 0.3, base + dirv * L * 0.55 + sidev, tip, base + dirv * L * 0.55 - sidev],
                    [(0, 1, 2, 3, 4)], tone=0.3 + 0.5 * layer)
flw.build(M_flower)


# ferns: arching fronds in clumps
def fern(mesh, x, y, z, n=7, length=0.6, seed=0):
    rr = random.Random(seed)
    for k in range(n):
        yaw = 2 * math.pi * k / n + rr.uniform(-0.3, 0.3)
        L = length * rr.uniform(0.75, 1.15)
        rise = rr.uniform(0.45, 0.8)
        d = Vector((math.cos(yaw), math.sin(yaw), 0))
        side = Vector((-d.y, d.x, 0))
        pts = []
        for i in range(13):
            s = i / 12
            pts.append(Vector((x, y, z)) + d * (L * s) + Vector((0, 0, L * rise * math.sin(math.pi * s * 0.75) - L * 0.25 * s * s)))
        for i in range(1, 12):
            s = i / 12
            p = pts[i]
            t = (pts[i + 1] - pts[i - 1]).normalized()
            lf = L * 0.22 * math.sin(math.pi * min(1.0, s * 1.1)) * (1 - 0.4 * s)
            for sg in (-1, 1):
                tipp = p + side * sg * lf + t * lf * 0.35 + Vector((0, 0, -lf * 0.25))
                mesh.add([p - t * 0.012, p + t * 0.02, tipp], [(0, 1, 2)], tone=rr.random())
        for i in range(12):
            mesh.add([pts[i] - side * 0.004, pts[i] + side * 0.004, pts[i + 1] + side * 0.003, pts[i + 1] - side * 0.003], [(0, 1, 2, 3)], tone=0.2)


ferns = Mesh('ferns')
for i, (fx, fy, L) in enumerate(((0.42, 3.75, 0.5), (1.72, 2.05, 0.55), (1.6, 3.4, 0.6), (2.75, 3.55, 0.7), (3.4, 4.5, 0.75),
                                 (-0.15, 13.7, 0.7), (4.75, 12.2, 0.7), (0.98, 2.04, 0.42), (2.2, 2.9, 0.55), (4.0, 4.0, 0.7),
                                 (1.25, 1.2, 0.5), (0.95, 0.55, 0.45), (2.1, 1.9, 0.6))):
    fern(ferns, fx, fy, ground_z(fx, fy), n=8, length=L, seed=i)
ferns.build(M_fern)


# ===================================================================================================== bamboo grove at the right edge
log('bamboo')
stems = Mesh('bamboo stems')
bleaves = Mesh('bamboo leaves')
BLADE = [(-0.012, 0.0), (0.012, 0.0), (0.016, 0.05), (0.01, 0.13), (0.0, 0.2), (-0.01, 0.13), (-0.016, 0.05)]
for i, (bx, by) in enumerate(((2.05, 3.3), (2.35, 3.9), (2.75, 4.6), (3.1, 5.4), (3.55, 6.1), (4.15, 6.7), (4.8, 7.3), (1.95, 2.55), (2.85, 3.75), (3.4, 4.65), (4.2, 5.6))):
    rr = random.Random(i + 7)
    h = rr.uniform(6.5, 9.0)
    r0 = rr.uniform(0.035, 0.055)
    lean = Vector((rr.uniform(-0.05, 0.12), rr.uniform(-0.05, 0.05), 1.0)).normalized()
    zz = 0.0
    p_prev = Vector((bx, by, ground_z(bx, by) - 0.1))
    while zz < h:
        segl = rr.uniform(0.28, 0.4) * (1 + zz / h)
        p_next = p_prev + lean * segl + Vector((0.004 * zz, 0, 0))
        rad = r0 * (1 - 0.5 * zz / h)
        stems.cyl(p_prev, p_next, rad, rad * 0.97, seg=8, caps=False)
        stems.cyl(p_next - lean * 0.01, p_next + lean * 0.01, rad * 1.12, seg=8)
        if zz > h * 0.45:
            for k in range(rr.randint(3, 6)):
                d = Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-0.6, 0.1))).normalized()
                c = p_next + d * rr.uniform(0.05, 0.25)
                add_leaf(bleaves, c, rr.uniform(0.9, 1.3), (d.x * 0.4, d.y * 0.4, 1.0), rr.uniform(0, 6.28), rr.random(), outline=BLADE, droop=1.2)
        p_prev = p_next
        zz += segl
stems.build(M_bamboo, smooth=True)
bleaves.build(M_bamboo_leaf)


# ===================================================================================================== trees, shrubs, mountains
def leaf_the_tree(root, n_points, size, seed, tone_lo=0.0, tone_hi=0.8, min_r=0.6, min_z=0.4, name='maple crown'):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    base = root.matrix_world.translation
    height = 0.0
    for ob in bpy.data.objects:
        if ob.type not in ('MESH', 'CURVE'):
            continue
        p = ob
        inside = False
        while p is not None:
            if p == root:
                inside = True
                break
            p = p.parent
        if not inside:
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ob.matrix_world
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        co = (np.array(mw)[:3, :3] @ co.T).T + np.array(mw.translation)
        pts.append(co)
        ev.to_mesh_clear()
    if not pts:
        return None
    co = np.concatenate(pts)
    height = co[:, 2].max() - base.z
    rxy = np.hypot(co[:, 0] - base.x, co[:, 1] - base.y)
    keep = co[(rxy > min_r) & (co[:, 2] - base.z > min_z * height)]
    rr = random.Random(seed)
    if len(keep) == 0:
        return None
    idx = [rr.randrange(len(keep)) for _ in range(n_points)]
    crown = Mesh(name)
    for i in idx:
        c = Vector(keep[i].tolist())
        for k in range(5):
            off = Vector((rr.gauss(0, 0.12), rr.gauss(0, 0.12), rr.gauss(-0.04, 0.08)))
            nrm = Vector((rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), 1.0))
            add_leaf(crown, c + off, size * rr.uniform(0.8, 1.2), nrm, rr.uniform(0, 6.28), rr.uniform(tone_lo, tone_hi), droop=0.3)
    return crown.build(M_maple)


if not NO_TREES:
    log('maples')
    try:
        m1 = store.add_part('bare_tree', location=(-0.4, 15.4, ground_z(-0.4, 15.4)), turn=20, seed=3, height=7.5)
        leaf_the_tree(m1, 2200, 0.13, 1, 0.0, 0.85, min_r=0.9, min_z=0.42)
        m2 = store.add_part('bare_tree', location=(3.9, 2.6, 0.0), turn=150, seed=8, height=6.2)
        leaf_the_tree(m2, 1500, 0.12, 2, 0.05, 0.9, min_r=0.8, min_z=0.5, name='near maple crown')
        m3 = store.add_part('bare_tree', location=(6.2, 12.6, ground_z(6.2, 12.6)), turn=-40, seed=5, height=5.0)
        leaf_the_tree(m3, 900, 0.12, 3, 0.0, 0.6, min_r=0.6, min_z=0.4, name='bridge maple crown')
    except Exception as e:  # keep the place drawable if the tree fails
        log('maple failed:', repr(e))

if not NO_HEDGES:
    log('shrubs and pine')
    try:
        for i, (line, h, w) in enumerate((
                ([(3.7, 4.75, 0.05), (4.7, 5.15, 0.15)], 0.8, 1.0),
                ([(-0.3, 13.95, 0.1), (0.55, 14.35, 0.1)], 0.75, 0.95),
                ([(4.5, 11.9, 0.05), (5.5, 12.3, 0.1)], 0.9, 1.0),
                ([(5.0, 8.6, 0.0), (5.6, 9.6, 0.0)], 0.8, 1.0),
                ([(-0.4, 16.2, 0.2), (1.2, 16.4, 0.2)], 1.0, 1.0))):
            hedge.lay(line, height=h, width=w, raggedness=0.35, amount=1.3, twigs=0.2, dry=0.08, seed=10 + i)
        # the pine: a twisting trunk and flat pads of needles
        trunk = Mesh('pine trunk')
        tp = [Vector(p) for p in ((5.3, 15.3, 0.0), (5.05, 15.35, 1.1), (5.5, 15.2, 2.1), (5.0, 15.15, 3.0), (5.3, 15.25, 3.9), (5.15, 15.3, 4.6))]
        trunk.tube(tp, [0.2, 0.16, 0.13, 0.1, 0.08, 0.05], seg=10)
        pads_at = [((5.3, 15.2, 1.9), (6.6, 15.0, 2.2)), ((5.1, 15.2, 2.8), (3.9, 15.0, 3.0)), ((5.4, 15.2, 3.6), (6.5, 15.4, 3.85)),
                   ((5.2, 15.3, 4.4), (4.4, 15.2, 4.6)), ((5.15, 15.3, 4.6), (5.4, 15.3, 5.0))]
        for i, (a, b2) in enumerate(pads_at):
            trunk.tube([Vector(a), Vector(a).lerp(Vector(b2), 0.5) + Vector((0, 0, 0.1)), Vector(b2)], [0.06, 0.045, 0.03], seg=6)
            bv = Vector(b2)
            hedge.lay([(bv.x - 0.55, bv.y - 0.1, bv.z - 0.2), (bv.x + 0.55, bv.y + 0.1, bv.z - 0.2)], height=0.5, width=1.1,
                      raggedness=0.3, amount=1.4, twigs=0.0, dry=0.05, seed=40 + i)
        trunk.build(S_bark, smooth=True)
        # a ragged dark tree line behind the inn
        hedge.lay([(-14.0, 30.0, 0.0), (-4.0, 31.5, 0.0), (6.0, 30.5, 0.0), (16.0, 31.5, 0.0)], height=6.0, width=4.0, raggedness=1.4, amount=0.6, twigs=0.3, dry=0.15, seed=77)
    except Exception as e:
        log('hedges failed:', repr(e))

log('mountains')
mt = Mesh('mountains')
for layer, (yb, depth, hmax, xoff) in enumerate(((80.0, 40.0, 60.0, 0.0), (150.0, 60.0, 160.0, 30.0), (240.0, 80.0, 260.0, -20.0))):
    nxm, nym = 90, 12
    vs = []
    for j in range(nym + 1):
        v = j / nym
        for i in range(nxm + 1):
            x = -160 + 320 * i / nxm
            ridge = 0.55 + 0.45 * noise.noise(Vector(((x + xoff) * 0.012, layer * 3.1, 0.0))) + 0.18 * noise.noise(Vector((x * 0.05, layer * 1.7, 2.0))) + 0.07 * noise.noise(Vector((x * 0.16, v * 3.0, layer + 5.0))) + 0.03 * noise.noise(Vector((x * 0.5, v * 8.0, layer + 9.0)))
            z = hmax * ridge * math.sin(math.pi * v) ** 0.8 - 2.0
            vs.append((x, yb + depth * v, z))
    fs = [(j * (nxm + 1) + i, j * (nxm + 1) + i + 1, (j + 1) * (nxm + 1) + i + 1, (j + 1) * (nxm + 1) + i) for j in range(nym) for i in range(nxm)]
    mt.add(vs, fs)
mt.build(M_mountain, smooth=True)


# ===================================================================================================== the puddle on the path
log('puddle')
try:
    water, film = puddle.make((-0.47, 1.6, 0.048), size=(0.5, 0.3), turn=86, ground=None, seed=3, shallow_band=0.04, raggedness=1.0)
    film.hide_render = True      # second pass: its rim drew a pale ring round the water under the lamp (Traps); the wet slabs carry the wet
except Exception as e:
    log('puddle failed:', repr(e))


# ===================================================================================================== SECOND PASS: the things people left
# (second pass, build 57 dress) the maid's bamboo broom leant on the garden fence beside the path, her wooden bucket with a
# dipper set down by the fence near the basin, the ground wet and muddy where water slops, leaves, twigs and pebbles
# in the bed between the path and the fence. Nothing on the path itself.
log('second pass: broom, bucket, stains, litter')
import stain as stain_tool      # noqa: E402
import litter as litter_tool    # noqa: E402
import stones as stones_tool    # noqa: E402
DR = random.Random(5701)
FD = (F1 - F0).normalized()                     # along the fence
N_PATH = Vector((-FD.y, FD.x, 0.0))             # from the fence towards the path
RAIL_Z = 0.72


def fence_point(p):
    t = (Vector((p[0], p[1], 0.0)) - F0).dot(FD)
    return F0 + FD * t


M_twig = mat_flat('broom twigs, weathered', (0.2, 0.17, 0.125), rough=0.55, var=0.4, scale=60.0, bump_s=0.0)
M_pole = M_bamboo_old      # the same greyed bamboo as the fence: it reads pale against the dark bed


def broom(foot, rest_at=None, length=1.42, head=0.5, spread=0.44, seed=0):
    """A garden broom of bamboo twigs bound to a bamboo pole, its head on the ground, the pole leant on the fence's top rail."""
    rr = random.Random(seed)
    f = Vector(foot)
    P = fence_point(rest_at if rest_at is not None else f)
    rest = Vector((P.x, P.y, RAIL_Z + 0.02)) + N_PATH * 0.036
    d = (rest - f).normalized()
    side = FD.copy()                                    # the head's fan opens along the fence
    side = (side - d * side.dot(d)).normalized()
    nrm = side.cross(d).normalized()
    pole, tw, cord = Mesh('broom pole'), Mesh('broom twigs'), Mesh('broom binding')
    bind = f + d * head
    pole.cyl(bind - d * 0.12, f + d * length, 0.0135, 0.0125, seg=8)
    for s_ in (0.8, 1.08, 1.33):
        q = f + d * s_
        pole.cyl(q - d * 0.007, q + d * 0.007, 0.0158, seg=8)
    cord.cyl(bind - d * 0.02, bind + d * 0.045, 0.026, 0.022, seg=10)
    cord.cyl(bind - d * 0.2, bind - d * 0.165, 0.042, seg=10)
    for i in range(230):
        u = rr.uniform(-1.0, 1.0)
        v = rr.uniform(-1.0, 1.0)
        tip = f + side * (u * spread / 2) + nrm * (v * 0.05) - d * 0.02
        tip.z = f.z + rr.uniform(0.0, 0.05) * (1 - abs(u))
        start = bind + side * (u * 0.018) + nrm * (v * 0.016)
        mid = start.lerp(tip, 0.45) + side * (u * 0.035) + nrm * (v * 0.02)
        tw.tube([start, mid, tip], [0.0035, 0.0028, 0.0016], seg=4)
        if rr.random() < 0.35:                          # side twigs off the main ones
            br = mid.lerp(tip, rr.uniform(0.2, 0.6))
            end = br + side * rr.uniform(-0.06, 0.06) - d * rr.uniform(0.04, 0.1) + nrm * rr.uniform(-0.03, 0.03)
            end.z = max(end.z, f.z + 0.005)
            tw.tube([br, end], [0.0018, 0.001], seg=3)
    pole.build(M_pole, smooth=True)
    tw.build(M_twig)
    cord.build(M_cord, smooth=True)
    return rest


BROOM_FOOT = (0.62, 1.12)
broom((BROOM_FOOT[0], BROOM_FOOT[1], ground_z(*BROOM_FOOT) + 0.005), rest_at=(0.62, 0.86), seed=3)

# the heap she swept off the path, at its edge beside the broom
heapm = Mesh('swept leaves')
HEAP_AT = (0.63, 1.42)
for k in range(110):
    a = DR.uniform(0, 2 * math.pi)
    r = 0.17 * math.sqrt(DR.random())
    hx, hy = HEAP_AT[0] + r * math.cos(a) * 1.15, HEAP_AT[1] + r * math.sin(a) * 0.85
    hz = ground_z(hx, hy) + 0.07 * (1 - (r / 0.17) ** 2) + 0.004
    add_leaf(heapm, (hx, hy, hz), DR.uniform(0.07, 0.1), (DR.uniform(-0.5, 0.5), DR.uniform(-0.5, 0.5), 1.0), DR.uniform(0, 6.28), DR.random(), outline=MAPLE_FINE, droop=-0.1, stem=True)
heapm.build(M_maple_ground)

# the wooden bucket (oke): cedar staves (the facets), two split-bamboo hoops, water, a dipper laid across
S_oke = store_copy('SURFACE • old_planks_02', 'bucket staves, greyed cedar', wet=0.5, grime=0.3)
_w = S_oke.node_tree.nodes.get('Weather')
if _w is not None:
    log('bucket Weather dials:', [(i.name, round(i.default_value, 3)) for i in _w.inputs if i.type == 'VALUE'])
    if 'Darken' in _w.inputs:
        _w.inputs['Darken'].default_value *= 0.45
BUCKET_AT = (0.68, 1.8)
bz = ground_z(*BUCKET_AT) - 0.01
oke = Mesh('wooden bucket')
lathe(oke, [(0.0, 0.012), (0.148, 0.012), (0.152, 0.0), (0.158, 0.0), (0.172, 0.27), (0.158, 0.27), (0.145, 0.03), (0.0, 0.03)],
      (BUCKET_AT[0], BUCKET_AT[1], bz), seg=18, pp_piece=0.4)
OKE = oke.build(S_oke)
hoops = Mesh('bucket hoops')
for hz, hr in ((0.055, 0.163), (0.215, 0.1715)):
    hoops.cyl((BUCKET_AT[0], BUCKET_AT[1], bz + hz - 0.013), (BUCKET_AT[0], BUCKET_AT[1], bz + hz + 0.013), hr, seg=24)
hoops.build(store.material('MADE • old copper'), smooth=True)
bwat = Mesh('bucket water')
bwat.add([(BUCKET_AT[0], BUCKET_AT[1], bz + 0.2)] + [(BUCKET_AT[0] + 0.162 * math.cos(2 * math.pi * i / 24), BUCKET_AT[1] + 0.162 * math.sin(2 * math.pi * i / 24), bz + 0.2) for i in range(24)],
         [(0, 1 + i, 1 + (i + 1) % 24) for i in range(24)])
bwat.build(M_basin_water)
dip = Mesh('bucket dipper')
a0 = Vector((BUCKET_AT[0] - 0.2, BUCKET_AT[1] - 0.05, bz + 0.282))
a1 = Vector((BUCKET_AT[0] + 0.12, BUCKET_AT[1] + 0.04, bz + 0.282))
dip.cyl(a0, a1, 0.008, seg=6)
dip.cyl((a1.x, a1.y, bz + 0.21), (a1.x, a1.y, bz + 0.29), 0.034, seg=12)
dip.build(M_bamboo_old)

# wet and mud on the soil where water slops: round the bucket, in front of the basin (never on the glossy path)
try:
    stain_tool.on_ground((BUCKET_AT[0] - 0.02, BUCKET_AT[1] - 0.03, 0.0), size=(0.3, 0.24), kind='damp', turn=20, ground=GROUND, strength=0.4, seed=2)
    stain_tool.on_ground((BASIN_AT[0] - 0.12, BASIN_AT[1] - 0.42, 0.0), size=(0.42, 0.2), kind='mud', turn=-10, ground=GROUND, strength=0.35, seed=4)
except Exception as e:
    log('ground stains failed:', repr(e))

# leaves, twigs and pebbles in the bed between the path's edge and the fence (swept off the path to its edge)
WEDGE = [(0.5, 0.55), (0.58, 0.55), (F1.x - 0.08, F1.y - 0.05), (0.98, 2.3), (0.5, 2.3)]
try:
    litter_tool.scatter(GROUND, area=WEDGE, kinds=('leaves', 'twigs'), amount=2.5, seed=7)
except Exception as e:
    log('litter failed:', repr(e))
try:
    stones_tool.scatter(GROUND, area=WEDGE, layers=('pebbles',), amount=0.8, where='hollows', seed=8)
except Exception as e:
    log('stones failed:', repr(e))


# ===================================================================================================== sky, light, camera
log('sky, lights, camera')
sky_and_haze.sky(scene, strength=1.5, clouds=0.9)
sky_and_haze.haze(low=(-25.0, 6.0, -1.0), high=(35.0, 90.0, 22.0), density=0.014)
scene.cycles.volume_step_rate = 4.0
scene.cycles.volume_max_steps = 256
M_cloud, nodes, links, _b = new_mat('high cloud')
nodes.remove(_b)
_out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
_vec, _tc = obj_coords(nodes, (1 / 260.0, 1 / 170.0, 1.0))
_dens = ramp(nodes, links, tex_noise(nodes, links, 1.0, 7.0, 0.62, _vec), [(0.47, (0, 0, 0)), (0.63, (1, 1, 1))])
_sep = nodes.new('ShaderNodeSeparateXYZ')
links.new(_tc.outputs['Object'], _sep.inputs[0])
_warm = math_node(nodes, links, 'DIVIDE', math_node(nodes, links, 'SUBTRACT', _sep.outputs['Y'], 200.0), 2200.0, clamp=True)
_lit = math_node(nodes, links, 'MULTIPLY', _warm, tex_noise(nodes, links, 3.0, 4.0, 0.6, _vec), clamp=True)
_col = mix_rgb(nodes, links, _lit, (0.15, 0.15, 0.17), (0.5, 0.28, 0.15))
_em = nodes.new('ShaderNodeEmission')
links.new(_col, _em.inputs['Color'])
_tr = nodes.new('ShaderNodeBsdfTransparent')
_mx = nodes.new('ShaderNodeMixShader')
links.new(_dens, _mx.inputs[0])
links.new(_tr.outputs[0], _mx.inputs[1])
links.new(_em.outputs[0], _mx.inputs[2])
links.new(_mx.outputs[0], _out.inputs['Surface'])
cloud = Mesh('high cloud deck')
cloud.add([(-3000.0, -1500.0, 420.0), (3000.0, -1500.0, 420.0), (3000.0, 4000.0, 420.0), (-3000.0, 4000.0, 420.0)], [(0, 1, 2, 3)])
CLOUD = cloud.build(M_cloud)
for flag in ('visible_shadow', 'visible_diffuse', 'visible_volume_scatter', 'visible_transmission'):
    setattr(CLOUD, flag, False)
sun = bpy.data.objects.new('low sun', bpy.data.lights.new('low sun', 'SUN'))
sun.data.energy = 4.2
sun.data.color = (1.0, 0.55, 0.26)
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(-82), 0.0, math.radians(6))
scene.collection.objects.link(sun)
light('sky fill', 'AREA', (1.0, 7.0, 9.0), 1300.0, (0.33, 0.55, 1.0), 14.0)

cam = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
cam.data.lens = 24
cam.data.shift_y = -0.1
cam.data.clip_end = 1000.0
cam.location = (-0.35, -1.0, 1.6)
cam.rotation_euler = (math.radians(90), 0.0, math.radians(-9))
scene.collection.objects.link(cam)
scene.camera = cam
if CLOSEUP:      # looking down at the wet slabs, their puddles and leaves (the owner's second picture)
    cam.data.lens = 30
    cam.data.shift_y = 0.0
    cam.location = (0.1, 0.55, 1.4)
    cam.rotation_euler = (math.radians(90 - 50), 0.0, math.radians(-3))

# ===================================================================================================== draw and finish
log('prepare and draw', W, H, S)
store.prepare_for_render(scene)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = S
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transmission_bounces = 4
scene.cycles.transparent_max_bounces = 8
scene.cycles.sample_clamp_indirect = 6
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
raw = os.path.join(os.path.dirname(OUT), 'raw - ' + os.path.splitext(os.path.basename(OUT))[0] + '.exr')
scene.render.filepath = raw
t_draw = time.time()
bpy.ops.render.render(write_still=True)
log('drawn in %.1f s' % (time.time() - t_draw))
finish.finish(raw, OUT, exposure=4.5 if CLOSEUP else 1.3, bloom=1.8 if CLOSEUP else 1.0, veil=0.0, soften=0.5, shadows_blue=2.0)   # second pass: the close view 4.2 -> 4.5 and more glow round the lantern's glint (its warm light was under the band)
log('finished', OUT)
