"""
What this file does: grows a ragged field hedge along a line you give: a strip of leafy sprays (live copies of a dozen
leafy twigs, each spray its own size, turn and shade), thick at the hedge's skin and thin inside, its top uneven (higher
and lower along its length, sprigs standing up out of it), its faces bulging and falling back, thin patches and holes
where the dark inside shows, a thin foot where the woody stems come down to the ground, bare twigs sticking out of the
top and faces, and a dark core deep inside so it never looks hollow. Where you ask for a gap (a gateway) the hedge
stops, cut back square-ish. On a ground you give, its foot follows the ground's height (ground.height_at); without one
it stands on the line's own heights. It is not a row of balloons: no smooth blobs anywhere. Nothing here chooses where
a hedge goes: the line, the gaps and the sizes are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import hedge
    made = hedge.lay([(-20, 30, 0), (5, 31, 0), (25, 28, 0)], height=1.7, width=1.2, gaps=[(12, 15.5)], ground=yard, seed=4)
    made['sprays'], made['twigs'], made['core']

The line may be a list of points (x, y, z), a curve object (it follows the curve whichever way it goes), a mesh object
made of a line of edges, or the path of a JSON file of points; by default a few points give a smooth curve through them.
Round a bend the sprays are spread by the hedge's own length on each side, as thick on the outside as on the inside.
Gaps are (from, to) in metres along the line (smoothed, as grown) from its first point, as seen from above.

From the command line:

    python3 hedge.py --help
    python3 hedge.py --points "-20,30,0 5,31,0 25,28,0" --gap 12 15.5 --out hedge.blend

Options, with their defaults:
    height          1.6 m    about how tall the hedge stands (its top rises and falls round this)
    width           1.1 m    about how wide it is at its fullest
    gaps            none     (from, to) metres along the line where the hedge is left out (gateways)
    ground          none     a mesh object whose height the hedge's foot follows; none: the line's own heights
    smooth          True     a smooth curve through your points (a curve object keeps its own shape); False: straight
                             between them (the hedge still rounds its corners a little)
    raggedness      1.0      0 a clipped, even hedge; 1 an old field hedge; 2 overgrown and gappy
    amount          1.0      how thick the leaves are: 0.5 thin (winter), 1.5 dense
    twigs           1.0      how many bare twigs stick out (0 none)
    dry             0.25     how much of it has turned brown, 0 green to 1 all russet
    seed            0        the same seed grows the same hedge
    leaves_material 'MADE • hedge leaves'          the leaves (reads the numbers this tool writes)
    twig_material   'MADE • wet bark'              stems and twigs
    core_material   'MADE • hedge leaves'          the dark core (the leaves' darkest green, as deep inside a hedge)
    collection      none     where the objects go (a new collection 'hedge')

What it makes: 'hedge sprays' (a cloud of points, one per spray, carrying 'hedge_scale', 'hedge_rotation',
'hedge_shape', 'hedge_tone', 'hedge_dry' and 'hedge_inner'; a Geometry Nodes modifier puts a live copy of a leafy spray
on each; obj['sprays'] is the count), 'hedge twigs' (the stems at its foot and the bare twigs; obj['twigs']) and 'hedge
core'. The spray shapes are kept in a hidden collection 'hedge shapes • <material>'.
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
import numpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import dry_wall  # noqa: E402
import stones  # noqa: E402
import _noise  # noqa: E402

LEAVES = 'MADE • hedge leaves'
BARK = 'MADE • wet bark'
CORE = LEAVES                  # without the numbers the tool writes on sprays, the leaves are their darkest green
SHAPE_COUNT = 12
SPRAYS_PER_SQUARE_METRE = 62.0      # of the hedge's outside, at amount 1
UP = Vector((0.0, 0.0, 1.0))

TOOL = {
    'name': 'hedge',
    'what': 'a ragged field hedge along a line or curve you give: leafy sprays thick at its skin, a rounded uneven top, faces '
            'that bulge and fall back, thin patches and holes, woody stems at its foot, bare twigs sticking out, a dark core; '
            'gaps where you say (gateways)',
    'call': "hedge.lay([(-20, 30, 0), (5, 31, 0), (25, 28, 0)], height=1.7, width=1.2, gaps=[(12, 15.5)], ground=yard, seed=4)",
    'options': {
        'height, width': 'about how tall and how wide at its fullest (1.6 m, 1.1 m); its top and faces wander round these',
        'gaps': '(from, to) metres along the line where it is left out: gateways (none)',
        'ground': "a mesh object whose height its foot follows (none: the line's own heights)",
        'smooth': 'a smooth curve through your points; a curve object keeps its own shape (True)',
        'raggedness': '0 clipped and even, 1 an old field hedge, 2 overgrown and gappy (1.0)',
        'amount': 'how thick the leaves are: 0.5 thin, 1.5 dense (1.0)',
        'twigs': 'how many bare twigs stick out, 0 none (1.0)',
        'dry': 'how much has turned brown, 0 to 1 (0.25)',
        'seed': 'the same seed grows the same hedge (0)',
        'leaves_material, twig_material, core_material': "('%s', '%s', '%s')" % (LEAVES, BARK, CORE),
        'collection': "where the objects go (a new collection 'hedge')",
    },
    'materials': [LEAVES, BARK],
    'source': "the hedge in the barn builder's '54 barn first pass - render_final.py' (section 5, line 746) rebuilt: the "
              "builder's strip of noise read as 'a row of balloons', then as a flat dark band",
    'trap': 'a hedge is thousands of leaves: far away it is a dark ragged band, so give a long distant hedge amount=0.6 '
            'and keep amount 1 or more for the near one',
}


# ------------------------------------------------------------------------------------------------ the spray shapes

def _spray_mesh(name, index):
    """One leafy spray 1 m long along +X: a bending stem with two or three side shoots, small folded leaves along them
    (each leaf its own 'leaf_random'), a bark stem (material slot 1)."""
    pick = random.Random(6300 + index)
    bm = bmesh.new()
    leaf_number = bm.verts.layers.float.new('leaf_random')
    leaves, stems = [], []

    def shoot(start, heading, length, radius, depth):
        points = []
        position = Vector(start)
        heading = Vector(heading).normalized()
        steps = 6
        for step in range(steps + 1):
            points.append(position.copy())
            heading = (heading + Vector((pick.gauss(0, 0.1), pick.gauss(0, 0.14), pick.gauss(0, 0.1)))).normalized()
            position = position + heading * (length / steps)
        rings = []
        for k, centre in enumerate(points):
            r = radius * (1.0 - 0.7 * k / steps)
            ahead = (points[min(k + 1, steps)] - points[max(k - 1, 0)]).normalized()
            side = ahead.cross(UP).normalized() if abs(ahead.z) < 0.95 else Vector((1.0, 0.0, 0.0))
            lift = side.cross(ahead).normalized()
            ring = [bm.verts.new(centre + (side * math.cos(a) + lift * math.sin(a)) * r) for a in (0.0, 2.1, 4.2)]
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for k in range(3):
                stems.append(bm.faces.new((a[k], a[(k + 1) % 3], b[(k + 1) % 3], b[k])))
        # leaves along the shoot, from a quarter of the way out to its tip
        count = int(length * pick.uniform(42, 60))
        for _ in range(count):
            k = pick.uniform(0.25, 1.0) * steps
            i = min(int(k), steps - 1)
            base = points[i].lerp(points[i + 1], k - i)
            ahead = (points[i + 1] - points[i]).normalized()
            around = pick.uniform(0.0, 2.0 * math.pi)
            side = ahead.cross(UP).normalized() if abs(ahead.z) < 0.95 else Vector((1.0, 0.0, 0.0))
            lift = side.cross(ahead).normalized()
            radial = side * math.cos(around) + lift * math.sin(around)
            out = (ahead * pick.uniform(0.4, 0.9) + radial).normalized()
            out = (out - UP * pick.uniform(0.0, 0.25)).normalized()            # leaves droop a little
            size = pick.uniform(0.075, 0.12)
            across = out.cross(radial).normalized()
            if across.length < 1e-6:
                across = side
            fold = out.cross(across).normalized() * size * 0.12
            tip = base + out * size
            middle = base + out * size * 0.45
            value = pick.random()
            verts = [bm.verts.new(base), bm.verts.new(middle + across * size * 0.27 + fold), bm.verts.new(tip),
                     bm.verts.new(middle - across * size * 0.27 + fold)]
            for vertex in verts:
                vertex[leaf_number] = value
            leaves.append(bm.faces.new((verts[0], verts[1], verts[2])))
            leaves.append(bm.faces.new((verts[0], verts[2], verts[3])))
        if depth < 1:
            for _ in range(pick.randint(2, 3)):
                at = pick.randint(1, 4)
                heading2 = (Vector((pick.uniform(0.3, 0.9), pick.choice((-1, 1)) * pick.uniform(0.4, 1.0), pick.uniform(-0.3, 0.5))))
                shoot(points[at], heading2, length * pick.uniform(0.35, 0.55), radius * 0.6, depth + 1)

    shoot((0.0, 0.0, 0.0), (1.0, 0.0, 0.05), 1.0, 0.011, 0)
    for face in stems:
        face.material_index = 1
        face.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _shapes(leaves, bark, collection):
    name = 'hedge shapes • %s' % leaves.name
    shapes = bpy.data.collections.get(name)
    if shapes is None:
        shapes = bpy.data.collections.new(name)
    if shapes.name not in collection.children:
        collection.children.link(shapes)
    shapes.hide_render = True
    shapes.hide_viewport = True
    for index in range(len(shapes.objects), SHAPE_COUNT):
        shape_name = 'hedge spray %02d' % index
        mesh = _spray_mesh(shape_name, index)
        mesh.materials.append(leaves)
        mesh.materials.append(bark)
        shapes.objects.link(bpy.data.objects.new(shape_name, mesh))
    return shapes


def _live_copies(obj, shapes):
    group = bpy.data.node_groups.new(obj.name + ' • live copies', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in, group_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    info = nodes.new('GeometryNodeCollectionInfo')
    info.inputs['Collection'].default_value = shapes
    info.inputs['Separate Children'].default_value = True
    info.inputs['Reset Children'].default_value = True
    instance.inputs['Pick Instance'].default_value = True
    links.new(group_in.outputs['Geometry'], instance.inputs['Points'])
    links.new(info.outputs['Instances'], instance.inputs['Instance'])
    for attribute, socket, kind in (('hedge_scale', 'Scale', 'FLOAT_VECTOR'), ('hedge_rotation', 'Rotation', 'FLOAT_VECTOR'),
                                    ('hedge_shape', 'Instance Index', 'INT')):
        named = nodes.new('GeometryNodeInputNamedAttribute')
        named.data_type = kind
        named.inputs['Name'].default_value = attribute
        links.new(named.outputs['Attribute'], instance.inputs[socket])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('live sprays', 'NODES')
    modifier.node_group = group
    return modifier


# ------------------------------------------------------------------------------------------------ the hedge's shape

def _smoothstep(low, high, value):
    t = numpy.clip((numpy.asarray(value, dtype=numpy.float64) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class _Shape:
    """The hedge's outline along one run: its height and width wandering along it, rounded at the top, thin at the
    foot, and its ends cut back."""

    def __init__(self, run, height, width, raggedness, seed):
        self.run, self.height, self.width, self.rag, self.seed = run, height, width, raggedness, seed

    def size(self, u):
        rag, seed = self.rag, self.seed
        h = self.height * (1.0 + rag * (0.11 * _noise.wander(u, 0.0, scale=2.6, seed=seed + 11) + 0.06 * _noise.wander(u, 3.0, scale=0.7, seed=seed + 12)))
        w = self.width * (1.0 + rag * 0.12 * _noise.wander(u, 7.0, scale=3.1, seed=seed + 13))
        to_end = numpy.minimum(u - self.run['start'], self.run['end'] - u)
        h = h * (0.82 + 0.18 * _smoothstep(0.0, 0.5, to_end))
        w = w * (0.7 + 0.3 * _smoothstep(0.0, 0.45, to_end))
        return h, w

    def half(self, u, z):
        """Half the width at height z (the section: narrow at the foot, fullest at 0.6 of the height, rounded over the
        top), with the face's lumps added."""
        h, w = self.size(u)
        t = numpy.clip(z / numpy.maximum(h, 1e-6), 0.0, 1.2)
        lower = 0.55 + 0.45 * numpy.sin(0.5 * numpy.pi * numpy.clip(t / 0.6, 0.0, 1.0))
        upper = numpy.clip(1.0 - numpy.clip((t - 0.6) / 0.4, 0.0, 1.0) ** 2.4, 0.0, 1.0) ** (1.0 / 2.4)
        shape = numpy.where(t <= 0.6, lower, upper)
        lumps = 0.085 * self.rag * _noise.wander(u, z, scale=(0.9, 0.55), seed=self.seed + 21)
        return numpy.maximum(w / 2.0 * shape + lumps * (shape > 0.05), 0.0), h


# ------------------------------------------------------------------------------------------------ growing it

def _frames(line, run, u):
    """Points on the line and its way ahead, the way taken over 0.4 m either side (within this piece of hedge) so a
    corner is rounded and a cut end stays square."""
    us = numpy.asarray(u, dtype=numpy.float64)
    points = numpy.array([tuple(line.path.at(float(v)))[:2] for v in us])
    before = numpy.array([tuple(line.path.at(max(float(v) - 0.4, run['start'])))[:2] for v in us])
    after = numpy.array([tuple(line.path.at(min(float(v) + 0.4, run['end'])))[:2] for v in us])
    ahead = after - before
    ahead /= numpy.maximum(numpy.linalg.norm(ahead, axis=1, keepdims=True), 1e-9)
    return points, ahead


def lay(line, height=1.6, width=1.1, gaps=(), ground=None, smooth=True, raggedness=1.0, amount=1.0, twigs=1.0, dry=0.25, seed=0,
        leaves_material=LEAVES, twig_material=BARK, core_material=CORE, collection=None):
    """Grow the hedge along the line; returns {'sprays': object, 'twigs': object, 'core': object} (see the note at the
    top)."""
    height, width, raggedness, amount, twigs, dry = (float(v) for v in (height, width, raggedness, amount, twigs, dry))
    if not 0.3 <= height <= 6.0:
        raise ValueError('height is 0.3 to 6 m, not %r' % (height,))
    if not 0.3 <= width <= 4.0:
        raise ValueError('width is 0.3 to 4 m, not %r' % (width,))
    if not 0.0 <= raggedness <= 2.0:
        raise ValueError('raggedness is 0 (clipped) to 2 (overgrown), not %r' % (raggedness,))
    if not 0.05 <= amount <= 3.0:
        raise ValueError('amount is 0.05 to 3 (1 an ordinary hedge), not %r' % (amount,))
    if not 0.0 <= twigs <= 4.0:
        raise ValueError('twigs is 0 to 4, not %r' % (twigs,))
    if not 0.0 <= dry <= 1.0:
        raise ValueError('dry is 0 (green) to 1 (all brown), not %r' % (dry,))
    path = dry_wall.Line(line, smooth=smooth)
    gap_list = dry_wall.read_gaps(gaps, path.total)
    pieces = dry_wall.runs(path, gap_list, corner=180.0)            # a hedge rounds its corners: only gaps break it
    if not pieces:
        raise ValueError('nothing left to grow: the gaps take the whole line')
    foot = dry_wall.ground_heights(path, ground)
    rng = numpy.random.default_rng([int(seed) % (2 ** 32), 61])
    pick = random.Random(seed)
    positions, scales, rotations, shapes_used, tones, dries, inners = [], [], [], [], [], [], []
    twig_mesh = bmesh.new()
    core_points, core_faces = [], []
    for number, run in enumerate(pieces):
        shape = _Shape(run, height, width, raggedness, int(seed) * 7 + number)
        length = run['end'] - run['start']
        skin = (2.0 * height + width) * length
        wanted = int(SPRAYS_PER_SQUARE_METRE * amount * skin)
        found = 0
        tries = 0
        # how sharply the line bends along this piece (1 / radius, left positive): round a bend the outside is longer
        # than the inside, so sprays are kept by each side's own length to be as thick on both
        grid = numpy.linspace(run['start'], run['end'], max(3, int(math.ceil(length / 0.2)) + 1))
        _, grid_ahead = _frames(path, run, grid)
        bends = numpy.gradient(numpy.unwrap(numpy.arctan2(grid_ahead[:, 1], grid_ahead[:, 0])), grid)
        while found < wanted and tries < 40:
            tries += 1
            n = max(256, (wanted - found) * 4)
            u = rng.uniform(run['start'] + 0.04, run['end'] - 0.04, n)
            z = rng.uniform(-0.05, 1.12, n) * shape.size(u)[0]
            across = rng.uniform(-0.62, 0.62, n) * shape.size(u)[1]
            half, h = shape.half(u, z)
            inside = half - numpy.abs(across)                          # metres in from the skin, sideways
            below_top = h * numpy.clip(1.0 - z / numpy.maximum(h, 1e-6), -1.0, 1.0)
            depth = numpy.minimum(inside, below_top + 0.25)
            near_skin = numpy.where(depth < -0.07, 0.0, numpy.exp(-numpy.maximum(depth, 0.0) / 0.12) + 0.06)
            holes = _smoothstep(-0.42, -0.12, _noise.wander(u, z, scale=(1.1, 0.8), seed=int(seed) + 31 + number) + 0.25 * (1.0 - raggedness))
            thin_foot = 0.2 + 0.8 * _smoothstep(0.12, 0.5, z)
            bend = numpy.interp(u, grid, bends)
            by_length = numpy.clip(1.0 - bend * across, 0.2, 2.0) / (1.0 + numpy.abs(bend) * 0.7 * width)
            keep = rng.random(n) < near_skin * (0.12 + 0.88 * holes) * thin_foot * by_length
            u, z, across, depth, half, h = u[keep], z[keep], across[keep], depth[keep], half[keep], h[keep]
            take = min(len(u), wanted - found)
            u, z, across, depth, half, h = u[:take], z[:take], across[:take], depth[:take], half[:take], h[:take]
            found += take
            if not take:
                continue
            points, ahead = _frames(path, run, u)
            left = numpy.column_stack([-ahead[:, 1], ahead[:, 0]])
            ground_here = numpy.array([foot(float(v)) for v in u])
            xy = points + left * across[:, None]
            positions.append(numpy.column_stack([xy, ground_here + z]))
            # each spray grows out of the hedge: sideways from its faces, up out of its top, a little this way and that
            sideways = numpy.clip(numpy.abs(across) / numpy.maximum(half, 1e-3), 0.0, 1.0) ** 2
            upward = 0.3 + numpy.clip((z / numpy.maximum(h, 1e-6) - 0.55) / 0.45, 0.0, 1.0) * 1.2
            grow = numpy.column_stack([left * (numpy.sign(across) * sideways)[:, None], upward])
            grow += rng.normal(0.0, 0.45, grow.shape)
            to_end = numpy.minimum(u - run['start'], run['end'] - u)
            along = numpy.sum(grow[:, :2] * ahead, axis=1)
            flip = ((u - run['start'] < 0.35) & (along < 0)) | ((run['end'] - u < 0.35) & (along > 0))
            grow[flip, :2] -= 2.0 * along[flip, None] * ahead[flip]
            grow /= numpy.maximum(numpy.linalg.norm(grow, axis=1, keepdims=True), 1e-9)
            side = numpy.cross(numpy.tile([0.0, 0.0, 1.0], (len(grow), 1)), grow)
            side_length = numpy.linalg.norm(side, axis=1, keepdims=True)
            side = numpy.where(side_length > 1e-6, side / numpy.maximum(side_length, 1e-9), numpy.tile([0.0, 1.0, 0.0], (len(grow), 1)))
            top = numpy.cross(grow, side)
            roll = rng.uniform(0.0, 2.0 * numpy.pi, len(grow))
            side, top = side * numpy.cos(roll)[:, None] + top * numpy.sin(roll)[:, None], top * numpy.cos(roll)[:, None] - side * numpy.sin(roll)[:, None]
            turn = numpy.stack([grow, side, top], axis=-1)              # columns: the spray's x, y, z in the world
            rotations.append(stones._euler(turn))
            size = rng.uniform(0.28, 0.58, len(u)) * (0.75 + 0.25 * _smoothstep(0.0, 0.4, to_end))
            scales.append(numpy.repeat(size[:, None], 3, axis=1))
            shapes_used.append(rng.integers(0, SHAPE_COUNT, len(u)))
            tones.append(rng.random(len(u)))
            patches = 0.5 + 0.5 * _noise.wander(u, z, scale=(2.0, 1.0), seed=int(seed) + 41)
            dries.append(numpy.clip(dry + 0.45 * (patches - 0.5) + rng.normal(0.0, 0.12, len(u)), 0.0, 1.0))
            inners.append(numpy.clip(numpy.maximum(depth, 0.0) / numpy.maximum(0.5 * half, 0.1), 0.0, 1.0))
        # the dark core: a lumpy body well inside the leaves, from a third of the way up (the foot shows its stems)
        sections = max(2, int(math.ceil(length / 0.3)) + 1)
        ring = 14
        start_index = len(core_points)
        for i in range(sections):
            inset = min(0.6, length * 0.3)
            u = run['start'] + inset + (length - 2.0 * inset) * i / (sections - 1)
            ending = 0.45 if i in (0, sections - 1) else 1.0                # the core tapers at its ends, deep in the leaves
            point, ahead = _frames(path, run, [u])
            left = numpy.array([-ahead[0, 1], ahead[0, 0]])
            h, _ = shape.size(numpy.array([u]))
            g = foot(u)
            for k in range(ring):
                angle = numpy.pi * k / (ring - 1)                       # from one side's foot over the top to the other's
                lump = (1.0 + 0.3 * raggedness * float(_noise.wander(u, angle, scale=(0.45, 0.7), seed=int(seed) + 51))) * ending
                z = 0.3 * h[0] + 0.5 * h[0] * numpy.sin(angle) * lump
                half, _ = shape.half(numpy.array([u]), numpy.array([z]))
                x = -numpy.cos(angle) * half[0] * 0.5 * lump
                core_points.append((point[0, 0] + left[0] * x, point[0, 1] + left[1] * x, g + z))
            if i:
                a, b = start_index + ring * (i - 1), start_index + ring * i
                for k in range(ring - 1):
                    core_faces.append((a + k, a + k + 1, b + k + 1, b + k))
                core_faces.append((a + ring - 1, a, b, b + ring - 1))          # underneath
        core_faces.append(tuple(start_index + k for k in range(ring)))
        last = start_index + ring * (sections - 1)
        core_faces.append(tuple(last + k for k in reversed(range(ring))))
        # woody stems at the foot, and bare twigs out of the top and faces
        stems = int(length * pick.uniform(2.5, 4.0))
        for _ in range(stems):
            u = pick.uniform(run['start'] + 0.1, run['end'] - 0.1)
            point, ahead = _frames(path, run, [u])
            left = Vector((-ahead[0, 1], ahead[0, 0], 0.0))
            g = foot(u)
            half, _ = shape.half(numpy.array([u]), numpy.array([0.1]))
            base = Vector((point[0, 0], point[0, 1], g - 0.05)) + left * pick.uniform(-0.6, 0.6) * half[0]
            heading = (UP + left * pick.uniform(-0.35, 0.35) + Vector((ahead[0, 0], ahead[0, 1], 0.0)) * pick.uniform(-0.3, 0.3)).normalized()
            _branch(twig_mesh, base, heading, pick.uniform(0.5, 0.9) * height * 0.6, pick.uniform(0.014, 0.028), pick, forks=1)
        count = int(length * 6.0 * twigs * (0.5 + 0.5 * raggedness))
        for _ in range(count):
            u = pick.uniform(run['start'] + 0.15, run['end'] - 0.15)
            point, ahead = _frames(path, run, [u])
            left = Vector((-ahead[0, 1], ahead[0, 0], 0.0))
            h, _ = shape.size(numpy.array([u]))
            g = foot(u)
            if pick.random() < 0.55:
                # out of the top: arching over, short and forked, so the top's outline is broken softly, never in spikes
                z = h[0] * pick.uniform(0.8, 0.93)
                half, _ = shape.half(numpy.array([u]), numpy.array([z]))
                base = Vector((point[0, 0], point[0, 1], g + z)) + left * pick.uniform(-0.6, 0.6) * half[0]
                spread = left * pick.uniform(-1.0, 1.0) + Vector((ahead[0, 0], ahead[0, 1], 0.0)) * pick.uniform(-0.8, 0.8)
                heading = (UP * pick.uniform(0.5, 0.9) + spread.normalized() * pick.uniform(0.6, 1.0)).normalized()
                length = pick.uniform(0.22, 0.5)
            else:                                                       # out of a face
                z = h[0] * pick.uniform(0.3, 0.8)
                half, _ = shape.half(numpy.array([u]), numpy.array([z]))
                sign = pick.choice((-1.0, 1.0))
                base = Vector((point[0, 0], point[0, 1], g + z)) + left * sign * max(half[0] - 0.15, 0.05)
                heading = (left * sign + UP * pick.uniform(0.1, 0.6)).normalized()
                length = pick.uniform(0.3, 0.65)
            _branch(twig_mesh, base, heading, length, pick.uniform(0.004, 0.007), pick, forks=2, droop=0.12)
    if collection is None:
        collection = bpy.data.collections.new('hedge')
        bpy.context.scene.collection.children.link(collection)
    material = lambda value: store.material(value) if isinstance(value, str) else value
    leaves, bark, core_mat = material(leaves_material), material(twig_material), material(core_material)
    origin = numpy.array([path.points[0].x, path.points[0].y, foot(0.0)])
    joined = lambda parts, width_: numpy.concatenate(parts) if parts else numpy.zeros((0, width_) if width_ else 0)
    position = joined(positions, 3)
    sprays_mesh = bpy.data.meshes.new('hedge sprays')
    sprays_mesh.vertices.add(len(position))
    if len(position):
        sprays_mesh.vertices.foreach_set('co', (position - origin).astype(numpy.float32).ravel())
    sprays_mesh.update()
    for name, kind, values in (('hedge_scale', 'FLOAT_VECTOR', joined(scales, 3)), ('hedge_rotation', 'FLOAT_VECTOR', joined(rotations, 3)),
                               ('hedge_shape', 'INT', joined(shapes_used, 0)), ('hedge_tone', 'FLOAT', joined(tones, 0)),
                               ('hedge_dry', 'FLOAT', joined(dries, 0)), ('hedge_inner', 'FLOAT', joined(inners, 0))):
        stones._write(sprays_mesh, name, kind, values)
    sprays = bpy.data.objects.new('hedge sprays', sprays_mesh)
    sprays.location = tuple(origin)
    collection.objects.link(sprays)
    _live_copies(sprays, _shapes(leaves, bark, collection))
    sprays['sprays'] = len(position)
    twig_data = bpy.data.meshes.new('hedge twigs')
    twig_mesh.to_mesh(twig_data)
    twig_mesh.free()
    for vertex in twig_data.vertices:
        vertex.co -= Vector(origin)
    twig_object = bpy.data.objects.new('hedge twigs', twig_data)
    twig_object.location = tuple(origin)
    collection.objects.link(twig_object)
    twig_data.materials.append(bark)
    twig_data.shade_smooth()
    twig_object['twigs'] = len(twig_data.polygons) // 18
    core_data = bpy.data.meshes.new('hedge core')
    core_data.from_pydata([tuple(numpy.array(p) - origin) for p in core_points], [], core_faces)
    core_data.update()
    core = bpy.data.objects.new('hedge core', core_data)
    core.location = tuple(origin)
    collection.objects.link(core)
    core_data.materials.append(core_mat)
    lowest = min(foot(u) for u in numpy.linspace(0.0, path.total, 20))
    for obj in (sprays, twig_object, core):
        store.mark(obj, ground=lowest)
    sprays['length'] = sum(r['end'] - r['start'] for r in pieces)
    bpy.context.view_layer.update()
    return {'sprays': sprays, 'twigs': twig_object, 'core': core}


def _branch(bm, start, heading, length, radius, pick, forks=1, depth=0, droop=0.0):
    """A thin tapering twig (three sided, six lengths) bending as it goes and drooping by `droop` each length (so it
    arches over instead of standing up like a spike), forking once or twice."""
    points = []
    position = Vector(start)
    heading = Vector(heading).normalized()
    steps = 6
    for step in range(steps + 1):
        points.append(position.copy())
        heading = (heading + Vector((pick.gauss(0, 0.12), pick.gauss(0, 0.12), pick.gauss(0, 0.08) - droop))).normalized()
        position = position + heading * (length / steps)
    rings = []
    for k, centre in enumerate(points):
        r = max(radius * (1.0 - 0.8 * k / steps), 0.0008)
        ahead = (points[min(k + 1, steps)] - points[max(k - 1, 0)]).normalized()
        side = ahead.cross(UP).normalized() if abs(ahead.z) < 0.95 else Vector((1.0, 0.0, 0.0))
        lift = side.cross(ahead).normalized()
        rings.append([bm.verts.new(centre + (side * math.cos(a) + lift * math.sin(a)) * r) for a in (0.0, 2.1, 4.2)])
    for a, b in zip(rings, rings[1:]):
        for k in range(3):
            bm.faces.new((a[k], a[(k + 1) % 3], b[(k + 1) % 3], b[k]))
    if depth < forks:
        for _ in range(pick.randint(1, 2)):
            at = pick.randint(2, 4)
            turn = Vector((pick.gauss(0, 0.6), pick.gauss(0, 0.6), pick.uniform(0.0, 0.5)))
            _branch(bm, points[at], (heading + turn).normalized(), length * pick.uniform(0.35, 0.55), radius * 0.55, pick, forks, depth + 1, droop)


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of hedge.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--points', help='the line as "x,y,z x,y,z ..." (makes a new file unless --blend is given)')
    parser.add_argument('--points-json', help='a JSON file holding {"points": [[x, y, z], ...]}')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--ground', help='the name of the ground object in the --blend file (the hedge follows its height)')
    parser.add_argument('--gap', type=float, nargs=2, action='append', default=[], metavar=('FROM', 'TO'), help='metres along the line left out (repeat for more)')
    for name, default, text in (('height', 1.6, 'about how tall'), ('width', 1.1, 'about how wide at its fullest'),
                                ('raggedness', 1.0, '0 clipped to 2 overgrown'), ('amount', 1.0, 'how thick the leaves are'),
                                ('twigs', 1.0, 'how many bare twigs stick out'), ('dry', 0.25, 'how much has turned brown, 0 to 1')):
        parser.add_argument('--' + name, type=float, default=default, help='%s; default %s' % (text, default))
    parser.add_argument('--no-smooth', action='store_true', help='straight between the points')
    parser.add_argument('--seed', type=int, default=0, help='the same seed grows the same hedge; default 0')
    parser.add_argument('--out', help='save the result here (.blend)')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    line = None
    if args.line:
        if args.line not in bpy.data.objects:
            parser.error('no object %r in the file' % args.line)
        line = bpy.data.objects[args.line]
    elif args.points_json:
        line = args.points_json
    elif args.points:
        line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()]
    if line is None:
        parser.error('give the line: --points, --points-json or --line')
    ground = None
    if args.ground:
        if args.ground not in bpy.data.objects:
            parser.error('no object %r in the file' % args.ground)
        ground = bpy.data.objects[args.ground]
    made = lay(line, height=args.height, width=args.width, gaps=[tuple(g) for g in args.gap], ground=ground, smooth=not args.no_smooth, raggedness=args.raggedness,
               amount=args.amount, twigs=args.twigs, dry=args.dry, seed=args.seed)
    print('grew %d sprays and %d twigs along %.2f m of hedge' % (made['sprays']['sprays'], made['twigs']['twigs'], made['sprays']['length']))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
