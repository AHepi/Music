"""
What this file does: clears the ground under a thing you set down. It takes away the grass tufts, stones, litter
(leaves, twigs, straw) or hedge sprays that the store's tools laid inside a footprint you give, so nothing pokes up
through a heap, a basket, a crate or a sack set down on them, and keeps every other one exactly as it was. It acts only
on the scatterings you pass it (what grass.grow, stones.scatter, litter.scatter or hedge.lay returned, or their point
objects): nothing here looks round the scene for things to clear, and nothing chooses where your thing stands.

From your own script, after the thing is in its place:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import clear_under
    turf = grass.grow(yard, area=verge, seed=2); laid = stones.scatter(yard, area=verge, seed=3)
    basket = store.add_part('skep', location=(x, y, ground.height_at(yard, x, y)))
    clear_under.clear([turf, laid], basket, margin=0.04)                        # under the basket's outline
    clear_under.clear([turf, laid], lambda x, y: (x - 1) ** 2 + (y - 2) ** 2 < 0.3 ** 2)     # under a circle
    clear_under.clear(turf, (0.5, 1.0, 1.7, 2.2))                               # under a rectangle (x0, y0, x1, y1)

The footprint may be:
    an object         its outline seen from above: under any of its faces (an empty with a part under it is read
                      as all the meshes under it), plus `margin`
    a function        f(x, y) of two arrays of points giving True (or more than 0.5) where the ground is covered
    a rectangle       (x0, y0, x1, y1), plus `margin`
    a polygon         [(x, y), ...] seen from above, plus `margin`

    python3 clear_under.py --help
    python3 clear_under.py --blend IN.blend --scattering "grass turf" --scattering "stones pebbles" --under "skep" --margin 0.04 --out OUT.blend

Options:
    margin      0.0 m    how far past the footprint's edge the ground is also cleared (a heap's skirt, a tuft's
                         spread); for a function footprint, put the margin in the function itself

It returns {point object's name: how many points it took away}. The points are taken away from the point objects
(the numbers on the others are kept with them, so stones.settle still works), and each object's count ('tufts',
'stones', 'pieces' or 'sprays') is brought down to match. The same tool call with the same seed lays them again.
"""

import argparse
import os
import sys

import bpy
import bmesh
import numpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import stones  # noqa: E402

COUNTS = ('tufts', 'stones', 'pieces', 'sprays')

TOOL = {
    'name': 'clear_under',
    'what': 'takes away the grass tufts, stones, litter and hedge sprays the store laid inside a footprint you give, so '
            'nothing pokes through a heap or a basket set down on them; acts only on the scatterings you pass it',
    'call': "clear_under.clear([turf, laid_stones, litter_made], basket, margin=0.04)",
    'options': {
        'scatterings': 'what grass.grow, stones.scatter, litter.scatter or hedge.lay returned, their point objects, or a list of them (required)',
        'footprint': 'an object (its outline from above), a function f(x, y) -> True where covered, a rectangle (x0, y0, x1, y1) or a polygon [(x, y), ...] (required)',
        'margin': "how far past the footprint's edge is also cleared, metres (0.0)",
    },
    'materials': [],
    'source': "`clear_points` in the barn dresser's '54 barn dress - render_final.py' (line 946), made into a tool: it no "
              'longer walks every object in the scene or sinks points 60 m under the ground; it takes away only the points '
              'of the scatterings it is given and keeps the counts true',
    'trap': 'clear after the thing is in its final place, and after the last scatter call: a scatter called later lays '
            'its tufts and stones under the thing again',
}


def _objects(scatterings):
    """The point objects in what was passed: a dict a tool returned, an object, or a list or tuple of either."""
    if isinstance(scatterings, bpy.types.Object):
        found = [scatterings]
    elif isinstance(scatterings, dict):
        found = list(scatterings.values())
    elif isinstance(scatterings, (list, tuple)):
        found = []
        for item in scatterings:
            found.extend(_objects(item))
    else:
        raise ValueError('scatterings are what grass.grow, stones.scatter, litter.scatter or hedge.lay returned (a dict), '
                         'their point objects, or a list of them; not %r' % (scatterings,))
    for obj in found:
        if not isinstance(obj, bpy.types.Object) or obj.type != 'MESH' or len(obj.data.polygons) or len(obj.data.edges):
            name = getattr(obj, 'name', repr(obj))
            raise ValueError('%s is not a scattering: a scattering is a cloud of points (the grass, stones, litter and hedge '
                             'tools make them), not a mesh with faces' % name)
    return found


def _outline(obj, margin):
    """f(x, y) for the object's outline seen from above: under any of its faces (or its meshes', for an empty with a
    part under it), or within `margin` of them."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    meshes = [obj] + ([child for child in obj.children_recursive] if obj.type == 'EMPTY' else [])
    points, triangles = [], []
    for item in meshes:
        if item.type not in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT'):
            continue
        evaluated = item.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            matrix = item.matrix_world
            start = len(points)
            points.extend(tuple(matrix @ v.co) for v in mesh.vertices)
            triangles.extend(tuple(start + i for i in t.vertices) for t in mesh.loop_triangles)
        finally:
            evaluated.to_mesh_clear()
    if not triangles:
        raise ValueError('%r has no faces to make a footprint from' % obj.name)
    flat = numpy.array(points, dtype=numpy.float64)
    low, high = flat[:, :2].min(axis=0) - margin, flat[:, :2].max(axis=0) + margin
    flat[:, 2] = 0.0
    tree = BVHTree.FromPolygons(flat.tolist(), triangles, all_triangles=True)
    reach = max(float(margin), 0.0) + 1e-5

    def inside(x, y):
        x, y = numpy.asarray(x, dtype=numpy.float64), numpy.asarray(y, dtype=numpy.float64)
        found = numpy.zeros(len(x), dtype=bool)
        near = numpy.flatnonzero((x >= low[0]) & (x <= high[0]) & (y >= low[1]) & (y <= high[1]))
        for i in near.tolist():
            hit = tree.find_nearest(Vector((x[i], y[i], 0.0)), reach)
            found[i] = hit[0] is not None
        return found
    return inside


def _edges_near(polygon, x, y, margin):
    """Which points lie within `margin` of the polygon's edges."""
    near = numpy.zeros(len(x), dtype=bool)
    points = numpy.column_stack([x, y])
    for a, b in zip(polygon, numpy.roll(polygon, -1, axis=0)):
        edge = b - a
        length = max(float(edge @ edge), 1e-12)
        t = numpy.clip((points - a) @ edge / length, 0.0, 1.0)
        closest = a + t[:, None] * edge
        near |= numpy.linalg.norm(points - closest, axis=1) <= margin
    return near


def footprint_test(footprint, margin=0.0):
    """The footprint as f(x, y) -> a True/False array (see the note at the top)."""
    margin = float(margin)
    if margin < 0:
        raise ValueError('margin is 0 or more metres, not %r' % (margin,))
    if isinstance(footprint, bpy.types.Object):
        return _outline(footprint, margin)
    if callable(footprint):
        def inside(x, y):
            result = numpy.asarray(footprint(numpy.asarray(x), numpy.asarray(y)))
            if result.shape != numpy.shape(x):
                raise ValueError('the footprint function gave %s answers for %d points (one True or False each)' % (result.shape, len(x)))
            return result > 0.5 if result.dtype != bool else result
        return inside
    try:
        values = list(footprint)
    except TypeError:
        raise ValueError('the footprint is an object, a function f(x, y), a rectangle (x0, y0, x1, y1) or a polygon [(x, y), ...]; not %r' % (footprint,))
    if len(values) == 4 and all(isinstance(v, (int, float, numpy.number)) for v in values):
        x0, x1 = sorted((float(values[0]), float(values[2])))
        y0, y1 = sorted((float(values[1]), float(values[3])))
        return lambda x, y: (numpy.asarray(x) >= x0 - margin) & (numpy.asarray(x) <= x1 + margin) & (numpy.asarray(y) >= y0 - margin) & (numpy.asarray(y) <= y1 + margin)
    weigh, _box = stones._area(values)
    polygon = numpy.array([(float(p[0]), float(p[1])) for p in values], dtype=numpy.float64)

    def inside_polygon(x, y):
        x, y = numpy.asarray(x, dtype=numpy.float64), numpy.asarray(y, dtype=numpy.float64)
        found = weigh(numpy.column_stack([x, y])) > 0.5
        if margin > 0:
            found |= _edges_near(polygon, x, y, margin)
        return found
    return inside_polygon


def clear(scatterings, footprint, margin=0.0):
    """Take away the points of the scatterings that lie inside the footprint (seen from above). Returns {point object's
    name: how many points it took away} (see the note at the top)."""
    objects = _objects(scatterings)
    inside = footprint_test(footprint, margin)
    bpy.context.view_layer.update()
    taken = {}
    for obj in objects:
        mesh = obj.data
        count = len(mesh.vertices)
        if not count:
            taken[obj.name] = 0
            continue
        local = numpy.zeros(count * 3, dtype=numpy.float64)
        mesh.vertices.foreach_get('co', local)
        matrix = numpy.array(obj.matrix_world)
        world = local.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
        covered = numpy.asarray(inside(world[:, 0], world[:, 1]), dtype=bool)
        removed = int(covered.sum())
        taken[obj.name] = removed
        if not removed:
            continue
        tool = bmesh.new()
        tool.from_mesh(mesh)
        tool.verts.ensure_lookup_table()
        bmesh.ops.delete(tool, geom=[tool.verts[i] for i in numpy.flatnonzero(covered).tolist()], context='VERTS')
        tool.to_mesh(mesh)
        tool.free()
        mesh.update()
        for key in COUNTS:
            if key in obj:
                obj[key] = count - removed
    return taken


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--scattering', action='append', default=[], help='a point object the grass, stones, litter or hedge tool made (repeat for more)')
    parser.add_argument('--under', help='the object whose outline seen from above is cleared under')
    parser.add_argument('--rectangle', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='or a rectangle to clear')
    parser.add_argument('--margin', type=float, default=0.0, help="how far past the footprint's edge is also cleared, metres; default 0")
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not (args.blend and args.scattering and (args.under or args.rectangle) and args.out):
        parser.error('--blend, at least one --scattering, --under or --rectangle, and --out are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    named = []
    for name in args.scattering + ([args.under] if args.under else []):
        if name not in bpy.data.objects:
            parser.error('no object %r in %s' % (name, args.blend))
        named.append(bpy.data.objects[name])
    footprint = named[-1] if args.under else tuple(args.rectangle)
    scatterings = named[:-1] if args.under else named
    for name, count in clear(scatterings, footprint, margin=args.margin).items():
        print('%s: took away %d' % (name, count))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))


if __name__ == '__main__':
    main()
