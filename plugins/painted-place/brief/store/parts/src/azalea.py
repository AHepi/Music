"""
azalea: a garden azalea (Rhododendron indicum, satsuki) clipped the way Japanese gardens keep it (karikomi): a low,
rounded mound, or several mounds run together into one billowing mass, its skin a dense mat of small glossy leaves in
rosettes at the shoot tips (clipped every year after flowering, so the shoots end at the skin and the inside is dark
twigs), and in late spring covered in five-lobed funnel flowers, singly and in twos and threes at the shoot tips,
standing a little proud of the leaves, more on its top and its sunny upper faces than at its foot. Out of flower it is
a crisply clipped dark green mound with a flush of paler new shoots. Its foot is at z = 0, its middle at the origin;
several mounds run together along X.

Options:
    colour     'pink' (default), 'magenta', 'red', 'white' or 'salmon': the flowers (the colours satsuki come in)
    bloom      how much of it is in flower: 1 the leaves showing only in gaps, 0.5 half, 0.2 a scatter (default 0.85)
    flowering  True (default): in flower; False: out of flower, green, freshly clipped, pale new shoots
    mounds     how many mounds run together along X (default 1)
    size       metres across one mound (default 1.2); the others of a run are a little smaller
    height     metres from the ground to the top of the tallest mound (default 0.7)
    seed       the mounds' places and sizes, the lumps of the clipping, every rosette and flower

Where it came from: the third garden builder's pink azalea in '/home/claude/build-57-garden/closer/render_final.py'
(lines 1726-1739): the hedge tool's clipped bush, most of its leaves turned pink by its material. Rebuilt here the way
the shrub is: clipped mounds (the board's photograph 02 has trees clipped into rounded mounds; 10 low shrubs), small
leaves in rosettes at the skin instead of a field hedge's long sprays, and real flowers (the hedge tool's flower
shapes: a funnel, five notched lobes, the upper one spotted) instead of pink leaves. The shelf has no photographed
leaves, so the leaves, the flowers and the dark inside are made in code.
"""

import math
import os
import sys

import bpy
import numpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402
import store  # noqa: E402
import hedge  # noqa: E402
import _noise  # noqa: E402

PART = 'azalea'
COLOURS = tuple(hedge.FLOWER_COLOURS)
ROSETTES = 6                    # leaf rosette shapes
LEAF_DENSITY = 2300.0           # rosettes to the square metre of skin (two layers: at the skin and just under it)
FLOWER_DENSITY = 950.0          # tips tried to the square metre of skin at bloom 1 (about half flower, one to three each)

CARD = {
    'name': PART,
    'what': 'a garden azalea (satsuki) clipped into a low rounded mound, or several run together: a dense skin of small glossy '
            'leaves in rosettes over a dark inside, in late spring covered in five-lobed funnel flowers (pink, magenta, red, '
            'white or salmon) singly and in twos and threes, more on its top than at its foot; or out of flower, green and '
            'freshly clipped',
    'size_m': (1.24, 1.25, 0.75),
    'options': {
        'colour': "'pink' (default), 'magenta', 'red', 'white' or 'salmon': the flowers",
        'bloom': 'how much of it is in flower: 1 the leaves showing only in gaps, 0.5 half, 0.2 a scatter, more of them buds '
                 '(default 0.85; 0 to 1.3)',
        'flowering': 'True (default): in flower; False: out of flower, green and freshly clipped, with pale new shoots',
        'mounds': 'how many mounds run together along X into one mass (default 1; 1 to 8; each one after the first a little '
                  'smaller and lower, overlapping the last by about a third)',
        'size': 'metres across one mound (default 1.2; 0.4 to 2.5)',
        'height': 'metres from the ground to the top of the tallest mound (default 0.7; 0.2 to 2, at most the size)',
        'seed': "the mounds' places and sizes, the lumps of the clipping, every rosette and flower (default 0)",
    },
    'materials': ['PART • azalea: leaves', 'PART • azalea: inside'] + ['PART • azalea: flowers, %s' % c for c in COLOURS],
    'source': "the pink azalea in '/home/claude/build-57-garden/closer/render_final.py' (lines 1726-1739: the hedge tool's "
              "clipped bush with most of its leaves turned pink); rebuilt as clipped mounds of small leaf rosettes with real "
              "flowers (the hedge tool's flower shapes)",
    'views': 'reads from every side and from above; the flowers face out and up, so it is fullest seen from the front and a '
             'little above, and its foot is the darkest part',
    'trap': 'at dusk its leaves go nearly black and its flowers a dim, dusky pink: a lantern within a metre or two of it, or a '
            'light from the side, brings the pink out (6 m from a 30 W stone lantern it was barely seen); out of flower it reads '
            'only by its outline against a paler or lit ground behind it; the leaves and flowers are live copies on points, '
            'drawn only when the picture is drawn',
}


def _number(name, value, low, high):
    return barn.number(name, value, low, high)


# ---------------------------------------------------------------------------------------------- the leaf rosettes

def _rosette_mesh(name, index):
    """A shoot tip, real size, facing +Z: four to seven small glossy leaves (2 to 3 cm, narrow ovals, folded a little
    along the midrib) spreading from the tip and lifted 20 to 50 degrees, each with its own 'leaf_random'."""
    pick = shapes.rng_for(PART, index, 'rosette')
    count = pick.randint(4, 7)
    points, faces, values = [], [], []
    start = pick.uniform(0.0, 2.0 * math.pi)
    for k in range(count):
        azimuth = start + 2.0 * math.pi * k / count + pick.uniform(-0.3, 0.3)
        lift = math.radians(pick.uniform(20.0, 50.0))
        length = pick.uniform(0.024, 0.036)
        width = length * pick.uniform(0.34, 0.44)
        along = numpy.array([math.cos(azimuth) * math.cos(lift), math.sin(azimuth) * math.cos(lift), math.sin(lift)])
        across = numpy.array([-math.sin(azimuth), math.cos(azimuth), 0.0])
        up = numpy.cross(along, across)
        if up[2] < 0:
            up = -up
        outline = [(0.0, 0.0, 0.0), (0.42, 0.3, 0.12), (0.36, 0.72, 0.1), (0.0, 1.0, 0.0), (-0.36, 0.72, 0.1), (-0.42, 0.3, 0.12)]
        first = len(points)
        value = pick.random()
        for (x, y, fold) in outline:
            p = along * y * length + across * x * width + up * fold * width
            points.append(tuple(p))
            values.append(value)
        faces += [(first, first + 1, first + 5), (first + 1, first + 2, first + 4, first + 5), (first + 2, first + 3, first + 4)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    mesh.update()
    layer = mesh.attributes.new('leaf_random', 'FLOAT', 'POINT')
    layer.data.foreach_set('value', numpy.asarray(values, dtype=numpy.float32))
    return mesh


def _rosette_shapes(material, collection):
    name = 'azalea rosettes • %s' % material.name
    found = bpy.data.collections.get(name)
    if found is None:
        found = bpy.data.collections.new(name)
    if found.name not in collection.children:
        collection.children.link(found)
    found.hide_render = True
    found.hide_viewport = True
    for index in range(len(found.objects), ROSETTES):
        shape_name = 'azalea rosette %02d' % index
        mesh = _rosette_mesh(shape_name, index)
        mesh.materials.append(material)
        found.objects.link(bpy.data.objects.new(shape_name, mesh))
    return found


def leaf_material():
    """Small glossy evergreen leaves: near-black to deep green, each leaf its own shade ('leaf_random' on the rosette
    shapes) and each rosette its own ('leaf_tone' on the points: the highest tones are pale new shoots); wet and glossy,
    lit through a little from behind."""
    def maker(m, nodes, links, p):
        leaf = nodes.new('ShaderNodeAttribute')
        leaf.attribute_name = 'leaf_random'
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'INSTANCER'
        tone.attribute_name = 'leaf_tone'
        both = shapes.math_node(nodes, links, 'ADD', shapes.math_node(nodes, links, 'MULTIPLY', tone.outputs['Fac'], 0.85),
                                shapes.math_node(nodes, links, 'MULTIPLY', leaf.outputs['Fac'], 0.15))
        ramp = nodes.new('ShaderNodeValToRGB')
        elements = ramp.color_ramp.elements
        stops = [(0.0, (0.010, 0.024, 0.007)), (0.45, (0.022, 0.045, 0.011)), (0.8, (0.040, 0.070, 0.016)),
                 (0.88, (0.06, 0.095, 0.02)), (1.0, (0.09, 0.13, 0.026))]
        while len(elements) < len(stops):
            elements.new(0.5)
        for element, (position, colour) in zip(elements, stops):
            element.position = position
            element.color = colour + (1.0,)
        links.new(both, ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.4
        p.inputs['Specular IOR Level'].default_value = 0.2
        p.inputs['Coat Weight'].default_value = 0.12          # more, and the small leaves' highlights read as white specks
        p.inputs['Coat Roughness'].default_value = 0.25
        out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        through = nodes.new('ShaderNodeBsdfTranslucent')
        links.new(ramp.outputs['Color'], through.inputs['Color'])
        mix = nodes.new('ShaderNodeMixShader')
        mix.inputs[0].default_value = 0.15
        links.new(p.outputs[0], mix.inputs[1])
        links.new(through.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs['Surface'])
        m.diffuse_color = (0.02, 0.045, 0.012, 1.0)
    return shapes.part_material(PART, 'leaves', maker)


def inside_material():
    """The dark inside of a clipped bush, seen between the leaves: twigs and old leaves in shadow, flecked, darkest at
    the foot."""
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        cells = nodes.new('ShaderNodeTexVoronoi')
        cells.inputs['Scale'].default_value = 60.0
        links.new(vec, cells.inputs['Vector'])
        fleck = shapes.map_range(nodes, links, cells.outputs['Distance'], 0.1, 0.5)
        colour = shapes.mix_colour(nodes, links, fleck, (0.009, 0.022, 0.005), (0.002, 0.005, 0.0015))
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vec, sep.inputs[0])
        foot = shapes.map_range(nodes, links, sep.outputs['Z'], 0.0, 0.25, 0.75, 0.0)
        colour = shapes.mix_colour(nodes, links, foot, colour, (0.004, 0.004, 0.003))
        links.new(colour, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.9
        p.inputs['Specular IOR Level'].default_value = 0.1       # a sheen on the smooth skin read as grey-blue stone between the leaves
        m.diffuse_color = (0.012, 0.02, 0.006, 1.0)
    return shapes.part_material(PART, 'inside', maker)


# ---------------------------------------------------------------------------------------------- the clipped mounds

def _mounds(rng, count, size, height):
    """(x, y, radius across x, radius across y, turn, height) of each mound, the run centred on the origin."""
    found = []
    x = 0.0
    for i in range(count):
        r = size / 2.0 * (1.0 if i == 0 else rng.uniform(0.68, 0.95))
        h = height * (1.0 if i == 0 else rng.uniform(0.66, 0.95))
        if i:
            x += (found[-1][2] + r) * rng.uniform(0.6, 0.72)
        oval = rng.uniform(0.86, 1.0)
        found.append([x, rng.uniform(-0.12, 0.12) * size * (i > 0), r, r * oval, rng.uniform(0.0, math.pi), h])
    if count > 1:
        rng.shuffle(found)                   # the tallest, full-size mound somewhere in the run, not always at its end
        xs = sorted(m[0] for m in found)
        for m, x in zip(found, xs):
            m[0] = x
        middle = (min(m[0] - m[2] for m in found) + max(m[0] + m[2] for m in found)) / 2.0
        for m in found:
            m[0] -= middle
    return found


def _skin(mounds, height, lumps, seed):
    """The clipped skin as a height field over the ground: each mound a cushion (flat-topped, its sides falling steeply
    to the ground), run together where they meet (their heights joined smoothly, so the valleys between fill a
    little), roughened by the clipping. Returns (points (n, 3), quads (m, 4), normals (n, 3))."""
    reach = max(max(m[2], m[3]) for m in mounds)
    step = min(0.035, max(0.012, reach / 26.0))
    x0 = min(m[0] - max(m[2], m[3]) for m in mounds) - step
    x1 = max(m[0] + max(m[2], m[3]) for m in mounds) + step
    y0 = min(m[1] - max(m[2], m[3]) for m in mounds) - step
    y1 = max(m[1] + max(m[2], m[3]) for m in mounds) + step
    xs = numpy.arange(x0, x1 + step * 0.5, step)
    ys = numpy.arange(y0, y1 + step * 0.5, step)
    gx, gy = numpy.meshgrid(xs, ys, indexing='ij')
    joined = numpy.zeros_like(gx)
    for (cx, cy, rx, ry, turn, h) in mounds:
        dx, dy = gx - cx, gy - cy
        u = (dx * math.cos(turn) + dy * math.sin(turn)) / rx
        v = (-dx * math.sin(turn) + dy * math.cos(turn)) / ry
        # the outline wanders a little: a clipped bush is never a perfect circle
        wobble = 1.0 + 0.05 * _noise.wander(numpy.arctan2(v, u) * 0.8, numpy.full_like(u, cx), scale=0.6, seed=seed + 5)
        t = numpy.sqrt(u * u + v * v) / wobble
        dome = h * numpy.clip(1.0 - t ** 2.8, 0.0, 1.0) ** 0.38
        joined += dome ** 4
    z = joined ** 0.25
    inside = z > 1e-4
    # the clipping's lumps, fading out at the foot so the outline stays on the ground
    rough = lumps * (0.45 * _noise.wander(gx, gy, scale=0.42, seed=seed + 10) + 0.4 * _noise.wander(gx, gy, scale=0.16, seed=seed + 11)
                     + 0.15 * _noise.wander(gx, gy, scale=0.06, seed=seed + 12))
    z = numpy.where(inside, numpy.maximum(z + rough * numpy.clip(z / 0.12, 0.0, 1.0), 0.0), 0.0)
    nx, ny = z.shape
    index = -numpy.ones((nx, ny), dtype=numpy.int64)
    keep = numpy.zeros((nx, ny), dtype=bool)
    occupied = (z[:-1, :-1] > 1e-4) | (z[1:, :-1] > 1e-4) | (z[1:, 1:] > 1e-4) | (z[:-1, 1:] > 1e-4)
    keep[:-1, :-1] |= occupied
    keep[1:, :-1] |= occupied
    keep[1:, 1:] |= occupied
    keep[:-1, 1:] |= occupied
    index[keep] = numpy.arange(int(keep.sum()))
    points = numpy.column_stack([gx[keep], gy[keep], z[keep]])
    qi, qj = numpy.nonzero(occupied)
    quads = numpy.column_stack([index[qi, qj], index[qi + 1, qj], index[qi + 1, qj + 1], index[qi, qj + 1]])
    # normals from the height field's slope: steep sides face out
    dzdx = numpy.gradient(z, step, axis=0)
    dzdy = numpy.gradient(z, step, axis=1)
    normals = numpy.column_stack([-dzdx[keep], -dzdy[keep], numpy.ones(int(keep.sum()))])
    normals /= numpy.linalg.norm(normals, axis=1, keepdims=True)
    return points, quads, normals


def _scatter(points, quads, normals, count, rng):
    """`count` places spread evenly over the skin's faces (by area), with the skin's normal there."""
    tris = numpy.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]])
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    area = 0.5 * numpy.linalg.norm(numpy.cross(b - a, c - a), axis=1)
    # faces lying flat on the ground (outside the mounds' foot) carry nothing
    area = numpy.where(numpy.maximum(numpy.maximum(a[:, 2], b[:, 2]), c[:, 2]) < 0.01, 0.0, area)
    if count <= 0 or area.sum() <= 0:
        return numpy.zeros((0, 3)), numpy.zeros((0, 3)), 0.0
    pick = rng.choice(len(tris), size=count, p=area / area.sum())
    r1, r2 = rng.random(count), rng.random(count)
    s = numpy.sqrt(r1)
    wa, wb, wc = 1.0 - s, s * (1.0 - r2), s * r2
    where = a[pick] * wa[:, None] + b[pick] * wb[:, None] + c[pick] * wc[:, None]
    n = (normals[tris[pick, 0]] * wa[:, None] + normals[tris[pick, 1]] * wb[:, None] + normals[tris[pick, 2]] * wc[:, None])
    n /= numpy.maximum(numpy.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    return where, n, float(area.sum())


def _skin_area(points, quads):
    tris = numpy.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]])
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    high = numpy.maximum(numpy.maximum(a[:, 2], b[:, 2]), c[:, 2]) >= 0.01
    return float((0.5 * numpy.linalg.norm(numpy.cross(b - a, c - a), axis=1) * high).sum())


def build(collection, seed=0, colour='pink', bloom=0.85, flowering=True, mounds=1, size=1.2, height=0.7):
    if colour not in COLOURS:
        raise ValueError('azalea colour is one of %s, not %r' % (', '.join(repr(c) for c in COLOURS), colour))
    bloom = _number('azalea bloom', bloom, 0.0, 1.3)
    size = _number('azalea size', size, 0.4, 2.5)
    height = _number('azalea height', height, 0.2, 2.0)
    if height > size:
        raise ValueError('azalea height %.2f m is more than its size %.2f m: a clipped azalea is wider than it is tall' % (height, size))
    try:
        mounds = int(mounds)
    except (TypeError, ValueError):
        raise ValueError('azalea mounds is a whole number, 1 to 8, not %r' % (mounds,))
    if not 1 <= mounds <= 8:
        raise ValueError('azalea mounds is 1 to 8, not %r' % (mounds,))
    flowering = bool(flowering)
    rng = shapes.rng_for(PART, seed)
    nrng = numpy.random.default_rng([int(seed) % (2 ** 32), 59])
    noise_seed = int(seed) * 13 + 7
    placed = _mounds(rng, mounds, size, height)
    # in flower the skin is softer (the flowers' shoots stand past the last clipping); out of flower crisply clipped
    points, quads, normals = _skin(placed, height, 0.04 if flowering else 0.022, noise_seed)
    area = _skin_area(points, quads)
    made = []
    mesh = bpy.data.meshes.new('azalea inside')
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set('co', points.astype(numpy.float32).ravel())
    mesh.loops.add(len(quads) * 4)
    mesh.loops.foreach_set('vertex_index', quads.astype(numpy.int32).ravel())
    mesh.polygons.add(len(quads))
    mesh.polygons.foreach_set('loop_start', numpy.arange(0, len(quads) * 4, 4, dtype=numpy.int32))
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    mesh.materials.append(inside_material())
    inside = bpy.data.objects.new('azalea inside', mesh)
    collection.objects.link(inside)
    made.append(inside)
    # the leaf rosettes over the whole skin, a little in and out of it
    leaves = leaf_material()
    # out of flower nothing hides the gaps: the clipped skin is denser (the shoots cut back to it branch again)
    where, out, _ = _scatter(points, quads, normals, int(LEAF_DENSITY * area * (1.0 if flowering else 1.5)), nrng)
    deeper = nrng.random(len(where)) < 0.4                                       # a second layer just under the skin
    where = where + out * numpy.where(deeper, nrng.uniform(-0.03, -0.01, len(where)), nrng.uniform(-0.008, 0.008, len(where)))[:, None]
    turn = hedge.facing(out, (0.0, 0.0, 1.0), nrng, tilt=0.5, roll=math.pi)
    if flowering:
        tone = nrng.uniform(0.0, 0.8, len(where))
    else:                                    # freshly clipped: a flush of new shoots, pale and yellow-green, on the top
        new = nrng.random(len(where)) < 0.04 + 0.1 * numpy.clip(out[:, 2], 0.0, 1.0)
        tone = numpy.where(new, nrng.uniform(0.86, 1.0, len(where)), nrng.uniform(0.0, 0.8, len(where)))
    leaf_mesh = bpy.data.meshes.new('azalea leaves')
    leaf_mesh.vertices.add(len(where))
    leaf_mesh.vertices.foreach_set('co', where.astype(numpy.float32).ravel())
    leaf_mesh.update()
    import stones
    stones._write(leaf_mesh, 'leaf_scale', 'FLOAT_VECTOR', numpy.repeat(nrng.uniform(0.8, 1.2, len(where))[:, None], 3, axis=1))
    stones._write(leaf_mesh, 'leaf_rotation', 'FLOAT_VECTOR', stones._euler(turn))
    stones._write(leaf_mesh, 'leaf_shape', 'INT', nrng.integers(0, ROSETTES, len(where)))
    stones._write(leaf_mesh, 'leaf_tone', 'FLOAT', tone)
    leaf_mesh.materials.append(leaves)
    leaf_obj = bpy.data.objects.new('azalea leaves', leaf_mesh)
    collection.objects.link(leaf_obj)
    hedge.copies(leaf_obj, _rosette_shapes(leaves, collection), 'leaf')
    leaf_obj['rosettes'] = len(where)
    made.append(leaf_obj)
    # the flowers: in clusters of one to three at shoot tips, in patches, more on the top and upper faces than at the foot
    if flowering and bloom > 0:
        tips, tip_out, _ = _scatter(points, quads, normals, int(FLOWER_DENSITY * bloom * area / 1.9 * 1.6), nrng)
        patch = 0.5 + 0.5 * _noise.wander(tips[:, 0] + 0.4 * tips[:, 2], tips[:, 1] - 0.3 * tips[:, 2], scale=0.25, seed=noise_seed + 21)
        up = numpy.clip(tips[:, 2] / max(height, 1e-6), 0.0, 1.0)
        chance = numpy.clip((0.3 + 1.1 * patch) * (0.25 + 0.75 * up ** 0.7) / 1.6, 0.0, 1.0)
        chance = numpy.clip(chance * min(1.0, 0.45 + 0.55 * bloom) * 1.25, 0.0, 1.0)
        keep = nrng.random(len(tips)) < chance
        tips, tip_out = tips[keep], tip_out[keep]
        per = nrng.choice([1, 1, 2, 2, 3], size=len(tips))
        which = numpy.repeat(numpy.arange(len(tips)), per)
        spread = nrng.normal(0.0, 0.022, (len(which), 3))
        normal = tip_out[which]
        spread -= normal * numpy.sum(spread * normal, axis=1, keepdims=True)        # spread along the skin, not out of it
        flower_at = tips[which] + spread + normal * nrng.uniform(0.006, 0.024, len(which))[:, None]
        petals = hedge.flower_material(colour, name='PART • azalea: flowers, %s' % colour)
        buds = 0.06 + 0.3 * max(0.0, 0.6 - bloom)
        flowers = hedge.flower_points('azalea flowers', collection, flower_at, normal, nrng.uniform(0.85, 1.12, len(which)),
                                      seed=seed, material=petals, buds=buds, origin=(0.0, 0.0, 0.0))
        made.append(flowers)
    return made
