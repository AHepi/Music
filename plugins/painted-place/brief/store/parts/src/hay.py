"""
hay: hay in a barn, of two kinds. Stacked to fill a bay: a block of hay against the bay's back wall (+Y) and its sides,
its face (-Y) bulging and layered where the loads went in, its top slumped and sagging, its front edge rounded over and
straggling, loose hay spilled over the floor at its foot. Or a loose heap, as forked down onto a barn floor: a lumpy
mound, straggling at its foot. The surface is stalks over a fibrous mass, buff to pale gold with grey-green and
brown in it, dark in its hollows, so it reads as hay and not as a smooth glowing block. Foot at z = 0; the origin is the
middle of its footprint.

Options:
    kind     'bay' (default): a block filling a bay, its back flat for the wall at +Y; 'heap': a loose heap
    width    along X, metres (default 3.0; a heap's own is 1.6)
    depth    along Y, metres (default 2.0; a heap's own is 1.4)
    height   metres (default 2.4; a heap's own is 0.9)
    seed     the lumps, the layers, the slump, every stalk

Where it came from: '/home/claude/build-54-barn/first pass/render_final.py', hay_stack() (line 461) and hay_heap()
(line 489): a subdivided box and a sphere pushed about by a cloud texture, in one plain hay colour that glowed flat
under the barn's lamps and read as fog through its haze. Rebuilt here as a shaped block or heap with layers, slump and
lumps, covered in stalks with straggling edges, over a fibrous hay material kept dark enough for the look.
"""

import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402

PART = 'hay'
KINDS = ('bay', 'heap')
OWN = {'bay': (3.0, 2.0, 2.4), 'heap': (1.6, 1.4, 0.9)}

CARD = {
    'name': PART,
    'what': 'hay: stacked to fill a bay (a block with a bulging, layered face, a slumped top, straggling edges, hay spilled up to 0.75 m in '
            'front of its foot) or a loose heap; stalks over a fibrous mass, buff to pale gold, dark in its hollows',
    'size_m': (3.15, 2.75, 2.62),
    'options': {
        'kind': "'bay' (default): a block filling a bay, its back flat for the wall at +Y and its sides flat for the posts; 'heap': a loose heap",
        'width': "along X, metres (default 3.0; a heap's own is 1.6)",
        'depth': "along Y, metres (default 2.0; a heap's own is 1.4)",
        'height': "metres (default 2.4; a heap's own is 0.9)",
        'seed': 'the lumps, the layers, the slump, every stalk (default 0)',
    },
    'materials': ['PART • hay: hay', 'PART • hay: stalks'],
    'source': "'/home/claude/build-54-barn/first pass/render_final.py', hay_stack() (line 461) and hay_heap() (line 489)",
    'views': 'a bay reads from the front and from above (its back and sides are flat, for the walls); a heap from every side',
    'trap': 'light hay from one side so its lumps and loose ends throw shadows: under a lamp straight on, or through haze inside the barn, '
            'it goes flat and reads as fog (as the first barn builder found)',
}


def hay_material():
    """Hay in the mass: crossing fibres (three stretched noises), buff to pale gold with grey-green and brown patches, dark
    in the hollows between the stalks."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        fibres = []
        # three layers of fibres, each stretched along a slanted way (fibres along the axes read as woven sacking)
        for scale, turn in (((7.0, 45.0, 45.0), (0.5, 1.1, 0.2)), ((45.0, 7.0, 45.0), (-0.7, 0.3, 1.3)), ((45.0, 45.0, 7.0), (1.2, -0.5, -0.9))):
            stretch = nodes.new('ShaderNodeMapping')
            stretch.inputs['Rotation'].default_value = turn
            stretch.inputs['Scale'].default_value = scale
            links.new(vec, stretch.inputs['Vector'])
            fibres.append(shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 1.0, detail=4.0, roughness=0.6))
        fib = shapes.math_node(nodes, links, 'MAXIMUM', shapes.math_node(nodes, links, 'MAXIMUM', fibres[0], fibres[1]), fibres[2])
        lit = shapes.map_range(nodes, links, fib, 0.5, 0.72)
        patch = shapes.noise_fac(nodes, links, vec, 1.6, detail=3.0)
        straw = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, patch, 0.35, 0.65), (0.2, 0.15, 0.065), (0.26, 0.2, 0.09))
        straw = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, patch, 0.64, 0.78, 0.0, 0.4), straw, (0.16, 0.145, 0.075))
        dark = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, patch, 0.3, 0.6), (0.025, 0.017, 0.008), (0.05, 0.036, 0.016))
        colour = shapes.mix_colour(nodes, links, lit, dark, straw)
        occlusion = nodes.new('ShaderNodeAmbientOcclusion')
        occlusion.samples = 6
        occlusion.inputs['Distance'].default_value = 0.12
        shade = shapes.map_range(nodes, links, occlusion.outputs['AO'], 0.3, 1.0, 0.35, 1.0)
        darkened = nodes.new('ShaderNodeVectorMath')
        darkened.operation = 'SCALE'
        links.new(colour, darkened.inputs[0])
        links.new(shade, darkened.inputs['Scale'])
        links.new(darkened.outputs[0], principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.8
        principled.inputs['Specular IOR Level'].default_value = 0.3
        links.new(shapes.bump(nodes, links, fib, 0.9, 0.01), principled.inputs['Normal'])
        m.diffuse_color = (0.16, 0.12, 0.055, 1.0)
    return shapes.part_material(PART, 'hay', maker)


def stalk_material():
    """Hay stalks, each its own shade (the face number 'straw_tone'): brown, buff, pale gold, a few grey-green; a dull
    sheen along them."""
    def maker(m, nodes, links, principled):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_name = 'straw_tone'
        t = tone.outputs['Fac']
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, t, 0.0, 0.35), (0.06, 0.042, 0.02), (0.2, 0.15, 0.065))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, t, 0.35, 0.85), colour, (0.3, 0.235, 0.11))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, t, 0.85, 1.0), colour, (0.17, 0.17, 0.09))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.55
        principled.inputs['Specular IOR Level'].default_value = 0.4
        m.diffuse_color = (0.22, 0.17, 0.08, 1.0)
    return shapes.part_material(PART, 'stalks', maker)


def _noise(p, scale, seed_at):
    return mnoise.noise(p * scale + seed_at)


def build(collection, seed=0, kind='bay', width=None, depth=None, height=None):
    if kind not in KINDS:
        raise ValueError("hay kind is 'bay' or 'heap', not %r" % (kind,))
    own = OWN[kind]
    width = barn.number('hay width', own[0] if width is None else width, 0.4, 12.0)
    depth = barn.number('hay depth', own[1] if depth is None else depth, 0.4, 12.0)
    height = barn.number('hay height', own[2] if height is None else height, 0.2, 8.0)
    rng = shapes.rng_for(PART, seed)
    seed_at = Vector((rng.uniform(0, 90), rng.uniform(0, 90), rng.uniform(0, 90)))
    mass = shapes.Shape()
    if kind == 'bay':
        faces_weight = _bay(mass, width, depth, height, rng, seed_at)
    else:
        faces_weight = _heap(mass, width, depth, height, rng, seed_at)
    stalks = shapes.Shape()
    barn.number_layers(stalks, faces=('straw_tone',))
    _cover(stalks, mass, faces_weight, kind, width, depth, height, rng)
    _spill(stalks, mass, kind, width, depth, height, rng, seed_at)
    objects = [mass.finish('hay', collection, hay_material(), smooth=True, sharp=None)]
    objects.append(stalks.finish('hay stalks', collection, stalk_material(), smooth=False))
    return objects


def _bay(mass, width, depth, height, rng, seed_at):
    """A block of hay filling a bay: back (+Y) and sides flat for the walls; front bulging and layered; top slumped;
    the front top edge rounded over. Returns a weight per face for the stalks (how much of it shows)."""
    bm = mass.bm
    cuts = max(12, int(max(width, depth, height) / 0.09))
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    half_w, half_d = width / 2.0, depth / 2.0
    rs, rf, rt = min(0.12, half_w * 0.3), min(0.4, depth * 0.3), min(0.4, height * 0.25)
    inner_lo = Vector((-half_w + rs, -half_d + rf, 0.0))
    inner_hi = Vector((half_w - rs, half_d, height - rt))
    for v in bm.verts:
        p = Vector(((v.co.x) * width, (v.co.y) * depth, (v.co.z + 0.5) * height))
        c = Vector(tuple(max(lo, min(hi, x)) for x, lo, hi in zip(p, inner_lo, inner_hi)))
        o = p - c
        if o.length > 1e-9:
            scaled = Vector((o.x / rs, o.y / rf, o.z / rt)).normalized()
            p = c + Vector((scaled.x * rs, scaled.y * rf, scaled.z * rt))
        v.co = p
    bm.normal_update()
    layer_phase = rng.uniform(0, 6.3)
    for v in bm.verts:
        p = v.co.copy()
        n = v.normal.copy()
        if p.z < 1e-4:
            continue                                       # the floor stays the floor
        front = max(0.0, -n.y)
        top = max(0.0, n.z)
        side_or_back = max(0.0, abs(n.x), n.y) * (1.0 - front) * (1.0 - top)
        lumps = (0.1 * _noise(p, 0.6, seed_at) + 0.09 * _noise(p, 1.7, seed_at) + 0.035 * _noise(p, 5.0, seed_at)
                 + 0.012 * _noise(p, 14.0, seed_at))
        layers = 0.016 * math.sin(2 * math.pi * p.z / 0.45 + layer_phase + 3.0 * _noise(p, 0.6, seed_at)) * front
        push = (lumps + layers) * (1.0 - 0.85 * side_or_back)
        v.co += n * push
        # the top sags in the middle and slumps towards the front; the foot of the face bulges out under the weight
        if top > 0.2:
            across = max(0.0, 1.0 - (2.0 * p.x / width) ** 2)
            towards_front = max(0.0, (half_d - p.y) / depth)
            v.co.z -= ((0.17 * across + 0.14 * towards_front * across) * min(1.0, height / 2.0) * top
                       * (0.65 + 0.35 * _noise(p, 0.9, seed_at)))
        if front > 0.3 and p.z < 0.45:
            v.co.y -= 0.09 * (1.0 - p.z / 0.45) ** 2 * front
        # it fills the bay: never past the posts at the sides or the wall at the back
        v.co.x = max(-half_w, min(half_w, v.co.x))
        v.co.y = min(half_d, v.co.y)
        v.co.z = max(0.0, min(height + 0.04, v.co.z))
    bm.normal_update()
    bm.faces.index_update()
    weights = {}
    for f in bm.faces:
        n = f.normal
        c = f.calc_center_median()
        w = 0.0
        if n.y < -0.35 or n.z > 0.35:
            w = 1.0
        elif abs(n.x) > 0.5:
            w = 0.6 if c.y < -half_d + 0.5 else 0.4        # the sides show past the posts at the front, and wherever a bay is open
        elif n.y > 0.5:
            w = 0.3                                        # the back, against the wall
        if c.z < 0.002:
            w = 0.0
        weights[f.index] = w * f.calc_area()
    return weights


def _heap(mass, width, depth, height, rng, seed_at):
    """A loose heap: a lumpy mound on an elliptic footprint, slumped on top, its foot spreading."""
    a, b = width / 2.0, depth / 2.0
    rings = max(10, int(max(a, b) / 0.06))
    segs = max(24, int(2 * math.pi * max(a, b) / 0.07))
    top = mass.bm.verts.new((0.0, 0.0, height))
    grid = []
    for i in range(1, rings + 1):
        u = i / rings
        ring = []
        for j in range(segs):
            phi = 2 * math.pi * j / segs
            ragged = 1.0 + 0.13 * _noise(Vector((math.cos(phi), math.sin(phi), 0.0)), 2.0, seed_at)
            x, y = a * u * ragged * math.cos(phi), b * u * ragged * math.sin(phi)
            z = height * max(0.0, 1.0 - u ** 1.8)
            ring.append(mass.bm.verts.new((x, y, z)))
        grid.append(ring)
    for j in range(segs):
        mass._face([top, grid[0][j], grid[0][(j + 1) % segs]])
    for i in range(rings - 1):
        for j in range(segs):
            k = (j + 1) % segs
            mass._face([grid[i][j], grid[i + 1][j], grid[i + 1][k], grid[i][k]])
    mass.bm.normal_update()
    for v in mass.bm.verts:
        p = v.co.copy()
        if p.z < 1e-4:
            continue
        lumps = 0.17 * height * _noise(p, 1.6, seed_at) + 0.06 * height * _noise(p, 4.5, seed_at) + 0.014 * _noise(p, 14.0, seed_at)
        v.co += v.normal * lumps * min(1.0, p.z / (0.15 * height))
        u = math.sqrt((p.x / a) ** 2 + (p.y / b) ** 2)
        v.co.z -= 0.16 * height * max(0.0, 1.0 - u) ** 2 * (0.5 + 0.5 * _noise(p, 1.1, seed_at))
        v.co.z = max(0.0, v.co.z)
    mass.bm.normal_update()
    mass.bm.faces.index_update()
    return {f.index: f.calc_area() for f in mass.bm.faces}


def _stalk(shape, points, radius, tone, rng):
    """One hay stalk: a thin three-sided tube along the points, thinning to its end."""
    before = len(shape.bm.faces)
    n = len(points)
    shape.sweep(points, radius, sides=3, radii=[radius * (1.0 - 0.55 * k / (n - 1)) for k in range(n)], caps=False)
    shape.bm.faces.ensure_lookup_table()
    layer = shape.bm.faces.layers.float['straw_tone']
    for f in shape.bm.faces[before:]:
        f[layer] = tone


def _tone(rng, trodden=0.0):
    r = rng.random()
    if r < 0.12 + trodden:
        return rng.uniform(0.0, 0.3)       # brown, old or trodden
    if r > 0.93:
        return rng.uniform(0.86, 1.0)      # grey-green
    return rng.uniform(0.35, 0.85)          # buff to pale gold


def _cover(stalks, mass, weights, kind, width, depth, height, rng):
    """Stalks over the hay: lying along its surface every way, some curling off it; at the edges they straggle out and
    droop."""
    bm = mass.bm
    bm.faces.ensure_lookup_table()
    faces = [f for f in bm.faces if weights.get(f.index, 0.0) > 0.0]
    if not faces:
        return
    cumulative = []
    total = 0.0
    for f in faces:
        total += weights[f.index]
        cumulative.append(total)
    count = int(total * (420 if kind == 'bay' else 520))
    import bisect
    for _ in range(count):
        f = faces[min(len(faces) - 1, bisect.bisect_left(cumulative, rng.uniform(0.0, total)))]
        vs = [v.co for v in f.verts]
        w = [rng.random() for _ in vs]
        s = sum(w)
        p = sum((c * (wi / s) for c, wi in zip(vs, w)), Vector((0.0, 0.0, 0.0)))
        n = f.normal.copy()
        t1 = n.cross(Vector((0.0, 0.0, 1.0)))
        if t1.length < 0.1:
            t1 = n.cross(Vector((1.0, 0.0, 0.0)))
        t1.normalize()
        t2 = n.cross(t1).normalized()
        a = rng.uniform(0, 2 * math.pi)
        d = t1 * math.cos(a) + t2 * math.sin(a)
        if n.z < 0.5:
            d = (d + Vector((0.0, 0.0, -0.7))).normalized()           # on a face, stalks hang downwards
            d = (d - n * d.dot(n)).normalized()
        edge = n.z > 0.2 and n.z < 0.85 and n.y < -0.2                 # the rounded front edge of a bay
        length = rng.uniform(0.07, 0.24) * (1.5 if edge else 1.0)
        curl = rng.uniform(-0.25, 0.9) if rng.random() < 0.3 else rng.uniform(-0.1, 0.2)
        pts = []
        steps = 4
        sway = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.25
        for k in range(steps + 1):
            t = k / steps
            q = p - n * 0.006 + (d + sway * t) * (length * t) + n * (curl * length * t * t * 0.6)
            if edge:
                q += Vector((0.0, 0.0, -0.5 * length * t * t)) - n * 0.0       # straggling over the edge, drooping
            q.z = max(0.003, q.z)
            if kind == 'bay':
                q.x = max(-width / 2 - 0.04, min(width / 2 + 0.04, q.x))
                q.y = min(depth / 2, q.y)
            pts.append(q)
        _stalk(stalks, pts, rng.uniform(0.0011, 0.0019), _tone(rng), rng)


def _spill(stalks, mass, kind, width, depth, height, rng, seed_at):
    """Loose hay on the floor round the foot: clumps of stalks laid side by side (never spread from one middle point,
    which reads as stars), and for a bay a low drift of hay along the foot of its face."""
    if kind == 'bay':
        half_w, half_d = width / 2.0, depth / 2.0
        nx, ny = max(8, int(width / 0.08)), 6
        reach = 0.42
        grid = {}
        for i in range(nx + 1):
            for j in range(ny + 1):
                x = -half_w + 0.03 + (width - 0.06) * i / nx
                v = j / ny
                ragged = reach * (0.7 + 0.3 * mnoise.noise(Vector((x * 2.0, 0.0, 0.5)) + seed_at))
                y = -half_d + 0.25 - (0.25 + ragged) * v
                z = max(0.003, 0.16 * (1.0 - v) ** 1.7 * (0.7 + 0.3 * mnoise.noise(Vector((x * 3.0, y * 3.0, 0.0)) + seed_at)))
                grid[i, j] = mass.bm.verts.new((x, y, z))       # a low drift of hay along the foot, in the hay's own mesh
        for i in range(nx):
            for j in range(ny):
                mass._face([grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]])
        area_lo = (-half_w, -half_d - reach - 0.1, half_w, -half_d + 0.05)
        clumps = int(width * 9)
    else:
        a, b = width / 2.0, depth / 2.0
        area_lo = None
        clumps = int((a + b) * 10)
    for _ in range(clumps):
        if area_lo is not None:
            cx = rng.uniform(area_lo[0], area_lo[2])
            cy = rng.uniform(area_lo[1], area_lo[3])
        else:
            phi = rng.uniform(0, 2 * math.pi)
            u = rng.uniform(0.92, 1.25)
            cx, cy = a * u * math.cos(phi), b * u * math.sin(phi)
        turn = rng.uniform(0, math.pi)
        along = Vector((math.cos(turn), math.sin(turn), 0.0))
        across = Vector((-along.y, along.x, 0.0))
        trodden = rng.uniform(0.0, 0.35)
        for k in range(rng.randint(10, 22)):
            off = across * rng.gauss(0.0, 0.035) + along * rng.gauss(0.0, 0.04)
            d = (along + across * rng.uniform(-0.3, 0.3)).normalized()
            length = rng.uniform(0.1, 0.28)
            z0 = rng.uniform(0.003, 0.025)
            start = Vector((cx, cy, z0)) + off - d * (length / 2)
            pts = []
            bow = rng.uniform(-0.03, 0.03)
            for j in range(4):
                t = j / 3
                q = start + d * (length * t) + across * (bow * 4 * t * (1 - t))
                q.z = max(0.003, z0 + 0.012 * math.sin(math.pi * t) * rng.uniform(0.0, 1.0))
                pts.append(q)
            _stalk(stalks, pts, rng.uniform(0.0011, 0.0018), _tone(rng, trodden), rng)
