"""
What this file does: lays separate stones on a ground you give, in three sizes: rocks (8 to 20 cm), pebbles (2 to 6 cm)
and grit (under 2 cm). Each stone lies in the soil, not on it: it sits on the ground where it lands, tipped with the
slope, and is sunk into the soil by a share of its own height, so the soil covers its foot; wet ground sinks it deeper.
Within the area you give, the ground's own numbers decide only where stones gather more or less: more in the dips (or
on the crowns, or evenly, as you ask; water carries small stones furthest, so grit gathers in the dips most and rocks
least), more pebbles and grit round the foot of each rock (and grit round the foot of big pebbles), fewer stones where
the ground is wet (wet ground swallows them), more where it is dry and trodden. The area and the amount are yours;
nothing here decides them. Every stone carries the wetness of the ground under it, so its material makes stones in wet
places dark and glossy.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import ground, stones
    yard = ground.make(size=(10, 10), relief=0.08, seed=3)
    ground.wet(yard, 0.6)
    laid = stones.scatter(yard, amount=1.0, where='hollows', seed=2)               # over the whole ground
    stones.scatter(yard, area=(-2, -2, 2, 1), layers=('pebbles', 'grit'), seed=3)  # in a rectangle (x0, y0, x1, y1)
    stones.scatter(yard, area=[(0, 0), (3, 1), (1, 4)], seed=4)                    # in a polygon of (x, y) points
    stones.scatter(yard, area=my_weights, layers=('grit',), seed=5)                # my_weights: (n, 2) points -> 0..1
    print(laid['rocks']['stones'], 'rocks')
    stones.settle(yard, laid)          # after carving tracks under stones already laid: drops them onto the new shape

From the command line:

    python3 stones.py --help
    python3 stones.py --blend IN.blend --ground Ground --out OUT.blend [--amount 1 --where hollows --seed 2]
    python3 stones.py --blend IN.blend --ground Ground --out OUT.blend --area -2 -2 2 1 --layers pebbles grit
    python3 stones.py --blend IN.blend --ground Ground --out OUT.blend --settle "stones rocks" "stones pebbles"

Options of scatter(), with their defaults:
    ground      the ground: a mesh object (the ground tool's, or your own); required
    area        where stones may lie: None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon (a list of (x, y)
                points), or a function that takes an (n, 2) array of points and returns a weight 0 to 1 for each (None)
    layers      which sizes, any of 'rocks', 'pebbles', 'grit' ('rocks', 'pebbles', 'grit')
    amount      how many: 1 is about 0.6 rocks, 30 pebbles and 300 grit per square metre of dry ground (wet ground
                swallows some: a ground wetted to 0.6 holds about two thirds of that); 2 is twice as many, and with the
                same seed a bigger amount keeps the stones of a smaller one and adds more (1.0)
    where       'hollows' (more in the dips), 'even', or 'crowns' (more on the high ground); it moves stones about
                within the area, it does not add or take away ('hollows')
    buried      the share of each stone's height sunk into the soil, on average (each stone a third more or less),
                0 to 0.95; wet ground sinks it deeper, up to 0.25 more where the ground is about to stand under water
                (0.35)
    seed        the same seed lays the same stones (0)
    collection  where the stone objects go (a new collection 'stones')
    material    the stones' material: a store name or a material you hold ('MADE • pebbles, wet')
settle(ground, stones): drops stones already laid (what scatter returned, or a list of its objects) onto the ground as
    it is now, each kept as deep in the soil as it was and tipped with the new slope; each stone takes the wetness of
    the ground under it now. Use it after carving tracks under stones.

What it makes: one object per size, 'stones rocks', 'stones pebbles', 'stones grit': a cloud of points, one per stone,
carrying the stone's size ('stone_scale'), turn ('stone_rotation'), shape ('stone_shape'), the wetness of the ground
under it ('wetness'), and what settle needs ('stone_burial', 'stone_turn', 'stone_tilt'). A Geometry Nodes modifier
puts a live copy of one of a dozen stone shapes on each point; the shapes (1 m across before sizing) are kept in hidden
collections 'stones shapes • <size> • <material>'. obj['stones'] is the count.

The ground's numbers it reads (the ground tool writes them on every point): 'hollow' (0 on the crowns to 1 in the
deepest dips), 'wetness' (0 dry, about 0.2 damp, about 0.5 wet, 0.86 and over standing water) and 'wear' (0 untrodden to
1 trodden hard). A ground without them reads as level, dry and untrodden.
"""

import argparse
import math
import os
import random
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector, noise  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import store  # noqa: E402
import ground as ground_tool  # noqa: E402

MATERIAL = 'MADE • pebbles, wet'
FLOODED = 0.86                 # the ground's wetness at which water stands
WET_SINK = 0.25                # wet ground sinks a stone this much more of its height, in full at FLOODED
REACH = 3.0                    # small stones gather round a bigger one's foot out to this many of its radii
SHAPE_COUNT = 12
ORDER = ('rocks', 'pebbles', 'grit')
WHERE = ('hollows', 'even', 'crowns')

# each size: its sizes in metres (across), stones per square metre at amount 1, how finely its shapes are made (the
# icosphere's subdivisions: 4 is 642 points, 3 is 162, 2 is 42), how far a stone tips from lying flat on the slope
# (degrees, a spread), whether it is drawn smooth or faceted, how strongly the dips (or crowns) draw it (water moves
# small stones most), and how many times as thick it lies at the foot of a rock and of a pebble (falling back to the
# ground's own at three radii out)
LAYERS = {
    'rocks': {'sizes': (0.08, 0.20), 'density': 0.6, 'detail': 4, 'tilt': 6.0, 'smooth': True, 'drawn': 0.8,
              'at_rocks': 0.0, 'at_pebbles': 0.0},
    'pebbles': {'sizes': (0.02, 0.06), 'density': 30.0, 'detail': 3, 'tilt': 9.0, 'smooth': True, 'drawn': 1.0,
                'at_rocks': 6.0, 'at_pebbles': 0.0},
    'grit': {'sizes': (0.006, 0.019), 'density': 300.0, 'detail': 2, 'tilt': 18.0, 'smooth': False, 'drawn': 1.5,
             'at_rocks': 9.0, 'at_pebbles': 2.5},
}
SINGULAR = {'rocks': 'rock', 'pebbles': 'pebble', 'grit': 'grit'}

TOOL = {
    'name': 'stones',
    'what': 'separate stones lying in the soil of a ground you give, in three sizes (rocks 8-20 cm, pebbles 2-6 cm, grit '
            'under 2 cm), each sunk into the soil by a share of its height; within the area you give, more gather in the '
            'dips (or on the crowns), round the foot of each rock and where the ground is dry and trodden, fewer in wet mud; '
            'wet stones dark and glossy',
    'call': "laid = stones.scatter(yard, area=(-2, -2, 2, 1), amount=1.0, where='hollows', seed=2);  stones.settle(yard, laid)",
    'options': {
        'ground': 'a mesh object: the ground tool\'s, or your own (required)',
        'area': 'None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or a function of an '
                '(n, 2) array of points giving weights 0 to 1 (None)',
        'layers': "any of 'rocks', 'pebbles', 'grit' (all three)",
        'amount': 'how many: 1 is about 0.6 rocks, 30 pebbles, 300 grit per square metre of dry ground; wet ground holds fewer; a bigger amount keeps the stones of a smaller one (1.0)',
        'where': "'hollows', 'even' or 'crowns': where in the area stones gather, not how many; grit follows it most, rocks least ('hollows')",
        'buried': 'share of each stone\'s height sunk in the soil, on average; up to 0.25 more where the ground is wet (0.35)',
        'seed': 'the same seed, the same stones (0)',
        'collection': "where the objects go (a new collection 'stones')",
        'material': "the stones' material ('%s')" % MATERIAL,
        'settle(ground, stones)': 'drops laid stones onto the ground as it is now (after carving tracks), each as deep in the soil as it was',
    },
    'materials': [MATERIAL],
    'source': 'the research of log 53 (studios lay stones in size layers, small ones gathering in hollows and at the foot of '
              'big ones, each buried by the soil), made for the store; live copies on points as in lay_cobbles',
    'trap': 'stones laid before tracks are carved hang over the grooves: call stones.settle(ground, laid) after carving; '
            'with a low sun ahead of the camera every stone is a dark bead on shining wet ground: light them from the side or '
            'behind the camera to show their faces',
}


# ----------------------------------------------------------------------------------------------- the ground as a surface

class _Surface:
    """The ground as triangles in the world: its height, slope and numbers anywhere on it."""

    def __init__(self, obj):
        if obj is None or obj.type != 'MESH':
            raise ValueError('stones need a ground: a mesh object (the ground tool makes one)')
        mesh = obj.data
        if not len(mesh.polygons):
            raise ValueError('the ground %r has no faces to lay stones on' % obj.name)
        mesh.calc_loop_triangles()
        corners = numpy.zeros(len(mesh.loop_triangles) * 3, dtype=numpy.int32)
        mesh.loop_triangles.foreach_get('vertices', corners)
        self.tris = corners.reshape(-1, 3).astype(numpy.int64)
        self.points = ground_tool.world_points(obj)
        normals = numpy.zeros(len(mesh.vertices) * 3, dtype=numpy.float32)
        mesh.vertex_normals.foreach_get('vector', normals)
        matrix = numpy.array(obj.matrix_world)[:3, :3]
        normals = normals.reshape(-1, 3).astype(numpy.float64) @ numpy.linalg.inv(matrix)
        normals[normals[:, 2] < 0] *= -1.0                       # a sheet whose faces look down still lays stones on top
        self.normals = normals / numpy.maximum(numpy.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
        a, b, c = (self.points[self.tris[:, k]] for k in range(3))
        self.areas = 0.5 * numpy.linalg.norm(numpy.cross(b - a, c - a), axis=1)
        self.point_areas = numpy.bincount(self.tris.ravel(), weights=numpy.repeat(self.areas / 3.0, 3), minlength=len(self.points))
        edges = numpy.concatenate([numpy.linalg.norm(b - a, axis=1), numpy.linalg.norm(c - b, axis=1), numpy.linalg.norm(a - c, axis=1)])
        self.cell = float(numpy.percentile(edges, 95)) if len(edges) else 0.1
        self.top = float(self.points[:, 2].max()) + 1.0
        self.tree = BVHTree.FromPolygons(self.points.tolist(), self.tris.tolist(), all_triangles=True)
        self.numbers = {name: numpy.clip(numpy.nan_to_num(ground_tool.numbers(mesh, name)), 0.0, 1.0)
                        for name in ('hollow', 'wetness', 'wear')}
        self._point_tree = None

    def at(self, values, tri, bary):
        """Values given on the ground's points, at places given as (triangle, barycentric weights)."""
        corners = values[self.tris[tri]]
        if corners.ndim == 3:
            return (corners * bary[:, :, None]).sum(axis=1)
        return (corners * bary).sum(axis=1)

    def sample(self, density, amount, generator, weigh, box=None):
        """Stones scattered over the ground with `density` stones per square metre at amount 1 (given on its points,
        varying straight across each triangle) times `amount`, within the area's weights. They are laid in blocks of
        one amount each (block j from generator(j)), every stone with its own random choices, so a bigger amount keeps
        every stone of a smaller one and adds more. Returns (triangle, barycentric weights, choices)."""
        corner_density = density[self.tris]
        most = corner_density.max(axis=1)
        expected = most * self.areas
        if box is not None:
            xs, ys = self.points[self.tris, 0], self.points[self.tris, 1]
            outside = (xs.max(axis=1) < box[0]) | (xs.min(axis=1) > box[2]) | (ys.max(axis=1) < box[1]) | (ys.min(axis=1) > box[3])
            expected = numpy.where(outside, 0.0, expected)
        found = []
        for block in range(int(math.ceil(amount))):
            rng = generator(block)
            counts = rng.poisson(expected)
            tri = numpy.repeat(numpy.arange(len(counts)), counts)
            root = numpy.sqrt(rng.random(len(tri)))
            share = rng.random(len(tri))
            bary = numpy.column_stack([1.0 - root, root * (1.0 - share), root * share])
            choices = _choices(rng, len(tri))
            here = (corner_density[tri] * bary).sum(axis=1)
            keep = (choices['thin'] * most[tri] < here) & (block + choices['share'] < amount)
            keep &= choices['inside'] < weigh(self.at(self.points, tri, bary)[:, :2])
            found.append((tri[keep], bary[keep], {k: v[keep] for k, v in choices.items()}))
        return _joined(found)

    def locate(self, xy):
        """For places seen from above (an (n, 2) array): the triangle straight under each, its barycentric weights, and
        whether the ground is there at all."""
        xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
        tri = numpy.full(len(xy), -1, dtype=numpy.int64)
        down = Vector((0.0, 0.0, -1.0))
        cast = self.tree.ray_cast
        top = self.top
        for i, (x, y) in enumerate(xy.tolist()):
            hit = cast(Vector((x, y, top)), down)
            if hit[2] is not None:
                tri[i] = hit[2]
        found = tri >= 0
        bary = numpy.zeros((len(xy), 3))
        if found.any():
            bary[found] = self._barycentric(xy[found], tri[found])
        return tri, bary, found

    def _barycentric(self, xy, tri):
        a = self.points[self.tris[tri, 0], :2]
        v0 = self.points[self.tris[tri, 1], :2] - a
        v1 = self.points[self.tris[tri, 2], :2] - a
        v2 = xy - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
        d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        denominator = d00 * d11 - d01 * d01
        denominator = numpy.where(numpy.abs(denominator) < 1e-18, 1e-18, denominator)
        v = (d11 * d20 - d01 * d21) / denominator
        w = (d00 * d21 - d01 * d20) / denominator
        bary = numpy.clip(numpy.column_stack([1.0 - v - w, v, w]), 0.0, 1.0)
        return bary / numpy.maximum(bary.sum(axis=1, keepdims=True), 1e-12)

    def most_near(self, values, centres, reach):
        """The largest of `values` (given on the ground's points) within `reach` of each centre, seen from above."""
        from scipy.spatial import cKDTree
        if self._point_tree is None:
            self._point_tree = cKDTree(self.points[:, :2])
        result = numpy.zeros(len(centres))
        for i, near in enumerate(self._point_tree.query_ball_point(centres, reach)):
            if near:
                result[i] = values[near].max()
        return result


# ----------------------------------------------------------------------------------------------- the area the caller gives

def _area(area):
    """The area as (weights for an (n, 2) array of points, bounding box (x0, y0, x1, y1) or None)."""
    if area is None:
        return (lambda xy: numpy.ones(len(xy))), None
    if callable(area):
        def weigh(xy):
            xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
            weights = numpy.asarray(area(xy), dtype=numpy.float64).reshape(-1)
            if len(weights) != len(xy):
                raise ValueError('the area function gave %d weights for %d points (one each, 0 to 1)' % (len(weights), len(xy)))
            return numpy.clip(numpy.nan_to_num(weights), 0.0, 1.0)
        return weigh, None
    values = list(area)
    if len(values) == 4 and all(isinstance(v, (int, float, numpy.number)) for v in values):
        x0, x1 = sorted((float(values[0]), float(values[2])))
        y0, y1 = sorted((float(values[1]), float(values[3])))

        def inside_rectangle(xy):
            xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
            return ((xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)).astype(numpy.float64)
        return inside_rectangle, (x0, y0, x1, y1)
    try:
        polygon = numpy.array([(float(p[0]), float(p[1])) for p in values], dtype=numpy.float64)
    except (TypeError, IndexError, ValueError):
        raise ValueError('area is None, a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or a function; not %r' % (area,))
    if len(polygon) < 3:
        raise ValueError('a polygon area needs at least three (x, y) points')

    def inside_polygon(xy):
        xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
        x, y = xy[:, 0], xy[:, 1]
        inside = numpy.zeros(len(xy), dtype=bool)
        previous = polygon[-1]
        for point in polygon:
            (xi, yi), (xj, yj) = point, previous
            if yi != yj:
                crosses = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
                inside ^= crosses
            previous = point
        return inside.astype(numpy.float64)
    low, high = polygon.min(axis=0), polygon.max(axis=0)
    return inside_polygon, (low[0], low[1], high[0], high[1])


# ----------------------------------------------------------------------------------------------- the stone shapes

def _stone_mesh(name, index, detail, smooth):
    """One stone, 1 m across: an icosphere roughed with noise and flattened a little; every other one broken, with one
    to three flat faces where it split. The same index gives the same stone at every detail, whatever the seed of the
    scatter."""
    pick = random.Random(4100 + index)
    offset = Vector((pick.uniform(-90, 90), pick.uniform(-90, 90), pick.uniform(-90, 90)))
    lumps, rough, knobs = pick.uniform(1.0, 1.9), pick.uniform(0.2, 0.34), pick.uniform(0.05, 0.1)
    flat, narrow = pick.uniform(0.45, 0.78), pick.uniform(0.6, 0.95)
    cuts = []
    angle = pick.uniform(0.0, 2.0 * math.pi)
    for number in range(1 + index % 3 if index % 2 else 0):
        lift = pick.uniform(0.25, 0.8) if number == 0 and pick.random() < 0.5 else pick.uniform(-0.25, 0.35)
        cuts.append((Vector((math.cos(angle), math.sin(angle), lift)).normalized(), pick.uniform(0.35, 0.68), pick.uniform(0.004, 0.014)))
        angle += 2.0 * math.pi / 3.0 + pick.uniform(-0.6, 0.6)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=detail, radius=0.5)
    for vertex in bm.verts:
        direction = vertex.co.normalized()
        bulge = (noise.noise(direction * lumps + offset) * rough + noise.noise(direction * 3.3 + offset * 1.7) * knobs
                 + noise.noise(direction * 8.0 + offset * 0.3) * 0.025)
        vertex.co = direction * 0.5 * (1.0 + bulge)
        vertex.co.y *= narrow
        vertex.co.z *= flat
    broken = set()
    for normal, depth, dent in cuts:
        reach = max(v.co.dot(normal) for v in bm.verts)
        result = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6,
                                        plane_co=normal * reach * depth, plane_no=normal, clear_outer=True)
        rim = [e for e in result['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        filled = bmesh.ops.holes_fill(bm, edges=rim, sides=0)['faces']
        if not filled:
            continue
        poked = bmesh.ops.poke(bm, faces=filled)
        for vertex in poked['verts']:
            vertex.co -= normal * dent * (0.5 + 0.5 * pick.random())       # a fresh break is a little hollow
        broken.update(f for f in poked['faces'])
        for edge in rim:
            if edge.is_valid:
                edge.smooth = False
    bm.verts.ensure_lookup_table()
    low = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    high = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
    middle, across = (low + high) / 2.0, max(high.x - low.x, high.y - low.y)
    for vertex in bm.verts:
        vertex.co = (vertex.co - middle) / across
    for face in bm.faces:
        face.smooth = smooth and face not in broken
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _shapes(layer, material, collection):
    """The hidden collection of a dozen stone shapes for one size and material (made once, then shared)."""
    name = 'stones shapes • %s • %s' % (layer, material.name)
    shapes = bpy.data.collections.get(name)
    if shapes is None:
        shapes = bpy.data.collections.new(name)
    if shapes.name not in collection.children:
        collection.children.link(shapes)
    shapes.hide_render = True
    shapes.hide_viewport = True
    if len(shapes.objects) < SHAPE_COUNT:
        spec = LAYERS[layer]
        for index in range(len(shapes.objects), SHAPE_COUNT):
            shape_name = '%s shape %02d' % (SINGULAR[layer], index)
            mesh = _stone_mesh(shape_name, index, spec['detail'], spec['smooth'])
            mesh.materials.append(material)
            shapes.objects.link(bpy.data.objects.new(shape_name, mesh))
    return shapes


def _shape_points(shapes):
    """Each shape's points (in the order Geometry Nodes picks them: by name), as (n, 3) arrays."""
    found = []
    for obj in sorted(shapes.objects, key=lambda o: o.name):
        co = numpy.zeros(len(obj.data.vertices) * 3, dtype=numpy.float64)
        obj.data.vertices.foreach_get('co', co)
        found.append(co.reshape(-1, 3))
    return found


# ----------------------------------------------------------------------------------------------- turning and sinking

def _turns(axis, angles):
    cos, sin = numpy.cos(angles), numpy.sin(angles)
    one, nought = numpy.ones_like(angles), numpy.zeros_like(angles)
    if axis == 'x':
        rows = [[one, nought, nought], [nought, cos, -sin], [nought, sin, cos]]
    elif axis == 'y':
        rows = [[cos, nought, sin], [nought, one, nought], [-sin, nought, cos]]
    else:
        rows = [[cos, -sin, nought], [sin, cos, nought], [nought, nought, one]]
    return numpy.stack([numpy.stack(row, axis=-1) for row in rows], axis=-2)


def _upright_to(normals):
    """The turn that takes straight up to each normal (the shortest way)."""
    nx, ny, nz = normals[:, 0], normals[:, 1], normals[:, 2]
    k = 1.0 / numpy.maximum(1.0 + nz, 1e-9)
    turn = numpy.zeros((len(normals), 3, 3))
    turn[:, 0, 0] = 1.0 - nx * nx * k
    turn[:, 0, 1] = -nx * ny * k
    turn[:, 0, 2] = nx
    turn[:, 1, 0] = -nx * ny * k
    turn[:, 1, 1] = 1.0 - ny * ny * k
    turn[:, 1, 2] = ny
    turn[:, 2, 0] = -nx
    turn[:, 2, 1] = -ny
    turn[:, 2, 2] = 1.0 - (nx * nx + ny * ny) * k
    return turn


def _euler(turn):
    """Blender's XYZ angles of each turn (the turn is Rz @ Ry @ Rx)."""
    y = numpy.arcsin(numpy.clip(-turn[:, 2, 0], -1.0, 1.0))
    x = numpy.arctan2(turn[:, 2, 1], turn[:, 2, 2])
    z = numpy.arctan2(turn[:, 1, 0], turn[:, 0, 0])
    return numpy.column_stack([x, y, z])


def _pose(surface, tri, bary, scale, shape, turn, tilt, burial, shape_points):
    """Where each stone's middle goes and how it is turned so it lies tipped with the slope under it and sunk into the
    soil by `burial` of its height: (positions (n, 3), XYZ angles (n, 3))."""
    normals = surface.at(surface.normals, tri, bary)
    normals /= numpy.maximum(numpy.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    turned = _upright_to(normals) @ _turns('x', tilt[:, 0]) @ _turns('y', tilt[:, 1]) @ _turns('z', turn)
    sized = turned * scale[:, None, :]                       # turned @ diag(scale)
    low = numpy.zeros(len(tri))
    high = numpy.zeros(len(tri))
    for index, points in enumerate(shape_points):
        chosen = numpy.flatnonzero(shape == index)
        if len(chosen):
            heights = sized[chosen, 2, :] @ points.T
            low[chosen] = heights.min(axis=1)
            high[chosen] = heights.max(axis=1)
    positions = surface.at(surface.points, tri, bary)
    positions[:, 2] += -burial * (high - low) - low
    return positions, _euler(turned)


# ----------------------------------------------------------------------------------------------- where the stones gather

def _where(where, hollow, drawn):
    """How strongly each point of the ground draws stones of one size: the dips (or the crowns) by `drawn`."""
    if where == 'hollows':
        return (0.3 + 1.7 * hollow ** 0.75) ** drawn
    if where == 'crowns':
        return (0.3 + 1.7 * (1.0 - hollow) ** 0.75) ** drawn
    return numpy.ones_like(hollow)


def _sizes(u, low, high, power=2.0):
    """Sizes between low and high for picks u (0 to 1), many small and few big (as broken stone comes)."""
    a = 1.0 - power
    return (low ** a + u * (high ** a - low ** a)) ** (1.0 / a)


def _choices(rng, count):
    """Every random choice a stone needs, drawn together, so each stone keeps its own whatever else is laid."""
    return {'size': rng.random(count), 'shape': rng.integers(0, SHAPE_COUNT, count),
            'narrow': rng.uniform(0.78, 1.0, count), 'thick': rng.uniform(0.85, 1.15, count),
            'turn': rng.uniform(0.0, 2.0 * math.pi, count), 'tilt': rng.normal(0.0, 1.0, (count, 2)),
            'sink': rng.uniform(0.65, 1.35, count),          # some stones show only their tops, some sit high
            'thin': rng.random(count), 'share': rng.random(count), 'inside': rng.random(count),
            'key': rng.integers(0, 2 ** 62, count)}


def _joined(parts):
    """(triangle, barycentric weights, choices) parts joined into one."""
    parts = [p for p in parts if len(p[0])] or parts[:1]
    if not parts:
        return numpy.zeros(0, dtype=numpy.int64), numpy.zeros((0, 3)), _choices(numpy.random.default_rng(0), 0)
    return (numpy.concatenate([p[0] for p in parts]), numpy.concatenate([p[1] for p in parts]),
            {k: numpy.concatenate([p[2][k] for p in parts]) for k in parts[0][2]})


def _at_feet(surface, bigger, density, gain, amount, stream, weigh):
    """Extra small stones round the foot of each bigger stone ((centres, radii, keys)): the ground's own density
    times 1 + gain at the foot, falling back to the ground's own at REACH radii out. Each bigger stone lays its own
    from its own key, in blocks of one amount, so its ring stays the same whatever else is laid.
    (triangle, barycentric weights, choices)."""
    centres, radii, keys = bigger
    if not len(centres) or gain <= 0:
        return _joined([])
    inner, outer = 0.85 * radii, REACH * radii
    bound = gain * surface.most_near(density, centres, outer.max() + 2.0 * surface.cell)
    places, owners, picks = [], [], []
    for index in range(len(centres)):
        for block in range(int(math.ceil(amount))):
            rng = numpy.random.default_rng([*stream, int(keys[index]), block])
            count = rng.poisson(bound[index] * math.pi * (outer[index] ** 2 - inner[index] ** 2))
            distance = numpy.sqrt(rng.uniform(inner[index] ** 2, outer[index] ** 2, count))
            angle = rng.uniform(0.0, 2.0 * math.pi, count)
            falloff = rng.random(count)
            choices = _choices(rng, count)
            out = numpy.clip((distance - radii[index]) / ((REACH - 1.0) * radii[index]), 0.0, 1.0)
            keep = (falloff < (1.0 - out) ** 1.6) & (block + choices['share'] < amount)
            places.append(centres[index] + distance[keep, None] * numpy.column_stack([numpy.cos(angle[keep]), numpy.sin(angle[keep])]))
            owners.append(numpy.full(int(keep.sum()), index))
            picks.append({k: v[keep] for k, v in choices.items()})
    xy, owner = numpy.concatenate(places), numpy.concatenate(owners)
    choices = {k: numpy.concatenate([p[k] for p in picks]) for k in picks[0]}
    tri, bary, found = surface.locate(xy)
    here = numpy.zeros(len(xy))
    here[found] = surface.at(density, tri[found], bary[found]) * gain
    keep = found & (choices['thin'] * numpy.maximum(bound[owner], 1e-12) < here) & (choices['inside'] < weigh(xy))
    return tri[keep], bary[keep], {k: v[keep] for k, v in choices.items()}


def _clear_of(xy, radii, bigger):
    """Which stones lie clear of the bigger stones already laid (each (centres, radii)): a small stone may tuck under a
    big one's edge, not lie inside it."""
    from scipy.spatial import cKDTree
    clear = numpy.ones(len(xy), dtype=bool)
    for centres, big_radii in bigger:
        if not len(centres) or not len(xy):
            continue
        k = min(6, len(centres))
        distance, index = cKDTree(centres).query(xy, k=k)
        distance, index = distance.reshape(len(xy), k), index.reshape(len(xy), k)
        clear &= ~(distance < 0.8 * big_radii[index] + 0.5 * radii[:, None]).any(axis=1)
    return clear


def _apart(xy, radii):
    """Which stones of one size do not lie through each other (of two that would, the smaller goes)."""
    from scipy.spatial import cKDTree
    keep = numpy.ones(len(xy), dtype=bool)
    if len(xy) < 2:
        return keep
    pairs = cKDTree(xy).query_pairs(1.5 * radii.max(), output_type='ndarray')
    if not len(pairs):
        return keep
    i, j = pairs[:, 0], pairs[:, 1]
    through = numpy.linalg.norm(xy[i] - xy[j], axis=1) < 0.75 * (radii[i] + radii[j])
    i, j = i[through], j[through]
    keep[numpy.where(radii[i] < radii[j], i, j)] = False
    return keep


# ----------------------------------------------------------------------------------------------- the stones' objects

def _live_copies(obj, shapes):
    """Geometry Nodes put a live copy of the stone shape each point names on the point, sized and turned by it."""
    group = bpy.data.node_groups.new(obj.name + ' • live copies', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    info = nodes.new('GeometryNodeCollectionInfo')
    info.inputs['Collection'].default_value = shapes
    info.inputs['Separate Children'].default_value = True
    info.inputs['Reset Children'].default_value = True
    instance.inputs['Pick Instance'].default_value = True
    links.new(group_in.outputs['Geometry'], instance.inputs['Points'])
    links.new(info.outputs['Instances'], instance.inputs['Instance'])
    for attribute, socket, kind in (('stone_scale', 'Scale', 'FLOAT_VECTOR'), ('stone_rotation', 'Rotation', 'FLOAT_VECTOR'),
                                    ('stone_shape', 'Instance Index', 'INT')):
        named = nodes.new('GeometryNodeInputNamedAttribute')
        named.data_type = kind
        named.inputs['Name'].default_value = attribute
        links.new(named.outputs['Attribute'], instance.inputs[socket])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('live stones', 'NODES')
    modifier.node_group = group
    return modifier


def _write(mesh, name, kind, values):
    attribute = mesh.attributes.get(name)
    if attribute is None:
        attribute = mesh.attributes.new(name, kind, 'POINT')
    if kind == 'FLOAT_VECTOR':
        attribute.data.foreach_set('vector', numpy.asarray(values, dtype=numpy.float32).ravel())
    elif kind == 'INT':
        attribute.data.foreach_set('value', numpy.asarray(values, dtype=numpy.int32).ravel())
    else:
        attribute.data.foreach_set('value', numpy.asarray(values, dtype=numpy.float32).ravel())


def _read(mesh, name, kind):
    attribute = mesh.attributes.get(name)
    if attribute is None:
        raise ValueError('%s carries no %r: it is not a stones object made by stones.scatter' % (mesh.name, name))
    if kind == 'FLOAT_VECTOR':
        values = numpy.zeros(len(attribute.data) * 3, dtype=numpy.float32)
        attribute.data.foreach_get('vector', values)
        return values.reshape(-1, 3).astype(numpy.float64)
    values = numpy.zeros(len(attribute.data), dtype=numpy.int32 if kind == 'INT' else numpy.float32)
    attribute.data.foreach_get('value', values)
    return values.astype(numpy.int64 if kind == 'INT' else numpy.float64)


def _stones_object(name, positions, columns, shapes, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(positions))
    if len(positions):
        mesh.vertices.foreach_set('co', numpy.asarray(positions, dtype=numpy.float32).ravel())
    mesh.update()
    for column, (kind, values) in columns.items():
        _write(mesh, column, kind, values)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    _live_copies(obj, shapes)
    obj['stones'] = len(positions)
    obj['stone_shapes'] = shapes
    store.mark(obj)
    return obj


def _material(name_or_material):
    return store.material(name_or_material) if isinstance(name_or_material, str) else name_or_material


# ----------------------------------------------------------------------------------------------- scatter and settle

def scatter(ground, area=None, layers=ORDER, amount=1.0, where='hollows', buried=0.35, seed=0, collection=None, material=MATERIAL):
    """Lay stones on the ground within the area (see the note at the top). Returns {'rocks': obj, 'pebbles': obj,
    'grit': obj}, only the layers asked for; each object's obj['stones'] is its count."""
    layers = (layers,) if isinstance(layers, str) else tuple(layers)
    unknown = [layer for layer in layers if layer not in LAYERS]
    if unknown:
        raise ValueError('no stone layer %s; the layers are %s' % (', '.join(repr(u) for u in unknown), ', '.join(ORDER)))
    if where not in WHERE:
        raise ValueError("where is 'hollows', 'even' or 'crowns', not %r" % (where,))
    amount = max(0.0, float(amount))
    buried = float(numpy.clip(buried, 0.0, 0.95))
    bpy.context.view_layer.update()
    surface = _Surface(ground)
    weigh, box = _area(area)
    hollow, wetness, wear = (surface.numbers[name] for name in ('hollow', 'wetness', 'wear'))
    inside = weigh(surface.points[:, :2]) * surface.point_areas
    # wet ground swallows stones; dry trodden ground shows them (its fines blown and washed away)
    showing = (1.0 - 0.7 * wetness) * (1.0 + wear * (1.0 - wetness))
    target = collection
    if target is None:
        target = bpy.data.collections.new('stones')
        bpy.context.scene.collection.children.link(target)
    stone_material = _material(material)
    seed = int(seed) % (2 ** 63)
    made, bigger, laid_by_size = {}, [], {}
    for number, layer in enumerate(ORDER):
        if layer not in layers:
            continue
        spec = LAYERS[layer]
        shapes = _shapes(layer, stone_material, target)
        shape_points = _shape_points(shapes)
        extents = numpy.array([[p[:, 0].max() - p[:, 0].min(), p[:, 1].max() - p[:, 1].min()] for p in shape_points])
        # where: more stones in the dips (or on the crowns), small ones drawn most; the same number in the area, only
        # moved about in it
        gather = _where(where, hollow, spec['drawn'])
        gather = gather / (float((gather * inside).sum() / inside.sum()) if inside.sum() > 0 else float(gather.mean()))
        density = gather * showing * spec['density']                 # per square metre at amount 1
        parts = [surface.sample(density, amount, lambda block: numpy.random.default_rng([seed, number, 0, block]), weigh, box)]
        for bigger_layer, gain, minimum in (('rocks', spec['at_rocks'], 0.0), ('pebbles', spec['at_pebbles'], 0.03)):
            if gain > 0 and bigger_layer in laid_by_size:
                centres, radii, sizes, keys = laid_by_size[bigger_layer]
                big = sizes >= minimum
                parts.append(_at_feet(surface, (centres[big], radii[big], keys[big]), density, gain, amount, (seed, number), weigh))
        tri, bary, choices = _joined(parts)
        count = len(tri)
        size = _sizes(choices['size'], *spec['sizes'])
        shape = choices['shape']
        scale = numpy.column_stack([size, size * choices['narrow'], size * choices['thick']])
        radii = 0.25 * (scale[:, 0] * extents[shape, 0] + scale[:, 1] * extents[shape, 1])
        turn = choices['turn']
        spread = math.radians(spec['tilt'])
        tilt = numpy.clip(choices['tilt'] * spread, -2.5 * spread, 2.5 * spread)
        jitter, keys = choices['sink'], choices['key']
        xy = surface.at(surface.points, tri, bary)[:, :2]
        keep = _clear_of(xy, radii, bigger)
        keep &= _apart(xy, numpy.where(keep, radii, 0.0)) if count else keep
        tri, bary, size, shape, scale, radii, turn, tilt, jitter, keys, xy = (
            v[keep] for v in (tri, bary, size, shape, scale, radii, turn, tilt, jitter, keys, xy))
        wet_here = surface.at(wetness, tri, bary)
        burial = numpy.clip((buried + WET_SINK * numpy.clip(wet_here / FLOODED, 0.0, 1.0)) * jitter, 0.0, 0.95)
        positions, angles = _pose(surface, tri, bary, scale, shape, turn, tilt, burial, shape_points)
        obj = _stones_object('stones ' + layer, positions, {
            'stone_scale': ('FLOAT_VECTOR', scale),
            'stone_rotation': ('FLOAT_VECTOR', angles),
            'stone_shape': ('INT', shape),
            'wetness': ('FLOAT', wet_here),
            'stone_burial': ('FLOAT', burial),
            'stone_turn': ('FLOAT', turn),
            'stone_tilt': ('FLOAT_VECTOR', numpy.column_stack([tilt, numpy.zeros(len(tilt))])),
        }, shapes, target)
        obj['stones_layer'] = layer
        made[layer] = obj
        bigger.append((xy, radii))
        laid_by_size[layer] = (xy, radii, size, keys)
    return made


def _shapes_of(obj):
    shapes = obj.get('stone_shapes')
    if isinstance(shapes, bpy.types.Collection):
        return shapes
    for modifier in obj.modifiers:
        if modifier.type == 'NODES' and modifier.node_group is not None:
            for node in modifier.node_group.nodes:
                if node.bl_idname == 'GeometryNodeCollectionInfo' and node.inputs['Collection'].default_value is not None:
                    return node.inputs['Collection'].default_value
    raise ValueError('%s is not a stones object made by stones.scatter (no stone shapes)' % obj.name)


def settle(ground, stones):
    """Drop stones already laid onto the ground as it is now: each stays where it is seen from above, sinks or rises
    with the ground under it, tips with the new slope and stays as deep in the soil as it was; it takes the wetness of
    the ground under it now. `stones` is what scatter returned, a list of its objects, or one of them. Returns how many
    stones were moved."""
    if isinstance(stones, dict):
        objects = list(stones.values())
    elif isinstance(stones, bpy.types.Object):
        objects = [stones]
    else:
        objects = list(stones)
    bpy.context.view_layer.update()
    surface = _Surface(ground)
    moved = 0
    for obj in objects:
        mesh = obj.data
        count = len(mesh.vertices)
        if not count:
            continue
        positions = numpy.zeros(count * 3, dtype=numpy.float64)
        mesh.vertices.foreach_get('co', positions)
        matrix = numpy.array(obj.matrix_world)
        positions = positions.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
        scale = _read(mesh, 'stone_scale', 'FLOAT_VECTOR')
        angles = _read(mesh, 'stone_rotation', 'FLOAT_VECTOR')
        shape = _read(mesh, 'stone_shape', 'INT')
        burial = _read(mesh, 'stone_burial', 'FLOAT')
        turn = _read(mesh, 'stone_turn', 'FLOAT')
        tilt = _read(mesh, 'stone_tilt', 'FLOAT_VECTOR')[:, :2]
        wet = _read(mesh, 'wetness', 'FLOAT')
        tri, bary, found = surface.locate(positions[:, :2])
        if found.any():
            new_positions, new_angles = _pose(surface, tri[found], bary[found], scale[found], shape[found], turn[found],
                                              tilt[found], burial[found], _shape_points(_shapes_of(obj)))
            positions[found] = new_positions
            angles[found] = new_angles
            wet[found] = surface.at(surface.numbers['wetness'], tri[found], bary[found])
            moved += int(found.sum())
        local = (positions - matrix[:3, 3]) @ numpy.linalg.inv(matrix[:3, :3]).T
        mesh.vertices.foreach_set('co', local.astype(numpy.float32).ravel())
        _write(mesh, 'stone_rotation', 'FLOAT_VECTOR', angles)
        _write(mesh, 'wetness', 'FLOAT', wet)
        mesh.update()
    return moved


# ----------------------------------------------------------------------------------------------- command line

def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description='Lay separate stones in the soil of a ground (see the note at the top of '
                                                 'stones.py). ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--ground', help='the ground object, by name')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--area', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='a rectangle to lay stones in; default the whole ground')
    parser.add_argument('--layers', nargs='+', choices=ORDER, default=list(ORDER), help='which sizes; default all three')
    parser.add_argument('--amount', type=float, default=1.0, help='1 is about 0.6 rocks, 30 pebbles, 300 grit per square metre of dry ground; default 1')
    parser.add_argument('--where', choices=WHERE, default='hollows', help='where in the area stones gather; default hollows')
    parser.add_argument('--buried', type=float, default=0.35, help="share of each stone's height in the soil; default 0.35")
    parser.add_argument('--seed', type=int, default=0, help='the same seed, the same stones; default 0')
    parser.add_argument('--material', default=MATERIAL, help="the stones' material; default '%s'" % MATERIAL)
    parser.add_argument('--settle', nargs='+', metavar='OBJECT', help='instead of laying new stones, drop these stones objects onto the ground as it is now')
    args = parser.parse_args(argv)
    if not (args.blend and args.ground and args.out):
        parser.error('--blend, --ground and --out are needed to lay stones')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    yard = bpy.data.objects.get(args.ground)
    if yard is None:
        parser.error('no object %r in %s' % (args.ground, args.blend))
    if args.settle:
        laid = []
        for name in args.settle:
            obj = bpy.data.objects.get(name)
            if obj is None:
                parser.error('no object %r in %s' % (name, args.blend))
            laid.append(obj)
        print('settled %d stones' % settle(yard, laid))
    else:
        made = scatter(yard, area=tuple(args.area) if args.area else None, layers=args.layers, amount=args.amount,
                       where=args.where, buried=args.buried, seed=args.seed, material=args.material)
        for layer, obj in made.items():
            print('%s: %d stones' % (obj.name, obj['stones']))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('saved', args.out)


if __name__ == '__main__':
    main()
