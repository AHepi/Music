"""What this does: makes ground FINE ENOUGH for real displacement and shaped ruts, in the way that suits its shape (make_fine is the one entry point).
A ground mesh is judged coarse by its real mean square (the square root of its area divided by its face count), not by its box, so a long thin strip of 0.1 m squares is
fine and is left alone. A coarse ground that is a plain RECTANGLE (one outline, no holes, filling its box) gets a GRADED GRID: small squares near the camera (0.12 m) that grow
a step at a time (1.09 times) to large ones far away (5 m), keeping the height of the old ground (read by a ray from above). Any other coarse ground (a curved road, a
ground with a trench or a hole cut in it, a turned rectangle) is SUBDIVIDED IN PLACE: every face is split in four, as often as needed, so its outline and its holes stay exactly
as the builder made them (an earlier version replaced every ground by a grid over its box: a curved road became a rectangle and a trench was filled in). The old mesh is kept with
a fake user so undo can swap it back, and the ground's outline area before the change is written on the object (pk_area_before) so the audit can see if it ever grows.
The grid's squares are laid out in plain numpy (graded_axis, graded_grid, is_coarse: tested without Blender). The numbers come from an earlier test yard
(house numbers place_surfaces.displacement_graded_grid_*). It needs numpy; the rest needs Blender (bpy).
A concrete example: graded_axis(0, 14, near=7, near_cell=0.12, growth=1.09, far_cell=5) gives the x lines of a 14 m ground: 0.12 m apart around x = 7; make_fine(lane_strip, ...)
on a curved 160 square metre road of 20 big faces splits it five times (20480 faces of about 9 cm) and the road is still curved.
"""
import math

import numpy as np

AREA_KEY = 'pk_area_before'               # the ground object's outline area (square metres) before the kit changed its mesh
RECTANGLE_FILL = 0.97                     # a ground is a plain rectangle when its outline fills at least this share of its box


def graded_axis(low, high, near, near_cell=0.12, growth=1.09, far_cell=5.0):
    """The grid lines along one axis from low to high: cells of near_cell around `near`, each next cell `growth` times bigger up to far_cell. The ends land
    exactly on low and high (the last cell on each side is stretched or shrunk to fit)."""
    near = float(np.clip(near, low, high))

    def march(start, stop, direction):
        positions, step, current = [], near_cell, start
        while True:
            current += direction * step
            if (direction > 0 and current >= stop - 1e-9) or (direction < 0 and current <= stop + 1e-9):
                positions.append(stop)
                break
            positions.append(current)
            step = min(step * growth, far_cell)
        return positions

    up = march(near, high, +1) if high - near > 1e-9 else []
    down = march(near, low, -1) if near - low > 1e-9 else []
    lines = sorted(set([near] + up + down + [low, high]))
    # a last cell that came out tiny is merged into its neighbour
    cleaned = [lines[0]]
    for value in lines[1:]:
        if value - cleaned[-1] < near_cell * 0.35 and value != high:
            continue
        cleaned.append(value)
    if cleaned[-1] != high:
        cleaned[-1] = high
    return np.array(cleaned)


def graded_grid(x_range, y_range, near_xy, near_cell=0.12, growth=1.09, far_cell=5.0):
    """Vertices and quad faces of a graded grid over a box: (vertices (n, 2), faces list of 4 vertex numbers)."""
    xs = graded_axis(x_range[0], x_range[1], near_xy[0], near_cell, growth, far_cell)
    ys = graded_axis(y_range[0], y_range[1], near_xy[1], near_cell, growth, far_cell)
    gx, gy = np.meshgrid(xs, ys)
    vertices = np.stack([gx.ravel(), gy.ravel()], axis=1)
    columns = len(xs)
    faces = []
    for row in range(len(ys) - 1):
        for col in range(columns - 1):
            a = row * columns + col
            faces.append((a, a + 1, a + columns + 1, a + columns))
    return vertices, faces


def mean_cell_metres(area_square_metres, face_count):
    """The side of the average face of a mesh: the square root of its area divided by its face count (0 faces: infinitely coarse)."""
    if face_count <= 0:
        return float('inf')
    return math.sqrt(max(area_square_metres, 0.0) / face_count)


def is_coarse(face_count, extent_metres, limit_metres, area_square_metres=None):
    """True when a ground object's mean square is longer than the limit (so it cannot show displacement or ruts). Give the real outline area when it is known: a long thin
    strip is then read by its real squares. Without an area the box (extent times extent) is used, which is only right for a square-ish ground."""
    if face_count <= 0:
        return True
    area = float(extent_metres) ** 2 if area_square_metres is None else area_square_metres
    return mean_cell_metres(area, face_count) > limit_metres


def outline_facts(obj):
    """The ground object's real outline from its evaluated mesh: {'area': square metres seen from above, 'box_area': its box's, 'faces': face count, 'boundary_loops': how many
    separate outlines it has (a hole or a trench cut through it adds one), 'pieces': loose pieces, 'plain_rectangle': one piece, one outline, filling its box}."""
    from .. import parts, scene_read
    vertices, triangles = parts.world_triangles(obj)
    area = 0.0
    if len(triangles):
        a, b, c = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]
        area = float(np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])).sum() / 2.0)
    low, high = scene_read.world_bounds(obj)
    box_area = float((high[0] - low[0]) * (high[1] - low[1]))
    mesh = obj.data
    loop_edges = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get('edge_index', loop_edges)
    uses = np.bincount(loop_edges, minlength=len(mesh.edges))
    edge_vertices = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', edge_vertices)
    boundary = edge_vertices.reshape(-1, 2)[uses == 1]
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for first, second in boundary.tolist():
        parent[find(first)] = find(second)
    loops = len({find(v) for v in parent})
    _, pieces = scene_read.loose_part_labels(mesh)
    plain = bool(pieces == 1 and loops == 1 and box_area > 0 and area >= RECTANGLE_FILL * box_area)
    return {'area': area, 'box_area': box_area, 'faces': len(mesh.polygons), 'boundary_loops': loops, 'pieces': pieces, 'plain_rectangle': plain}


def _swap_mesh(obj, new_mesh, area_before):
    """Gives the object the new mesh (materials copied), keeps the old one with a fake user so undo can swap it back, and writes what the audit needs."""
    for slot_material in obj.data.materials:
        new_mesh.materials.append(slot_material)
    old = obj.data
    obj.data = new_mesh
    if 'pk_original_mesh' not in obj.keys():
        old.use_fake_user = True              # kept, so undo can swap it back (a mesh nothing uses is dropped when the file is saved)
        obj['pk_original_mesh'] = old.name
    for polygon in new_mesh.polygons:
        polygon.use_smooth = True
    obj['pk_regraded'] = 1
    if AREA_KEY not in obj.keys():
        obj[AREA_KEY] = float(area_before)


def regrade_object(obj, near_xy=None, settings_numbers=None):
    """Replaces the object's mesh with a graded grid over the same box, keeping the old surface height. Only for a plain rectangle (see make_fine, which decides). Returns a report
    dict, or None when the object is already fine. The object keeps its name, role, materials and place in the scene."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from .. import house_numbers, parts, scene_read
    limit = house_numbers.value('place_surfaces.displacement_mesh_edge_metres_max')
    if obj.get('pk_regraded'):
        return None                                      # already fine (a second finish must not change it again)
    facts = outline_facts(obj)
    if not is_coarse(facts['faces'], 0.0, limit, facts['area']):
        return None
    low, high = scene_read.world_bounds(obj)
    near_cell = house_numbers.value('place_surfaces.displacement_graded_grid_near_metres')
    growth = house_numbers.value('place_surfaces.displacement_graded_grid_growth')
    far_cell = house_numbers.value('place_surfaces.displacement_graded_grid_far_metres')
    if near_xy is None:
        camera = bpy.context.scene.camera
        near_xy = (camera.matrix_world.translation.x, camera.matrix_world.translation.y) if camera is not None else ((low[0] + high[0]) / 2, (low[1] + high[1]) / 2)
    vertices2d, faces = graded_grid((low[0], high[0]), (low[1], high[1]), near_xy, near_cell, growth, far_cell)
    return _regrid(obj, vertices2d, faces, facts['area'], 'graded', {'near_cell': near_cell, 'near_xy': [float(near_xy[0]), float(near_xy[1])]})


def _regrid(obj, vertices2d, faces, area_before, label, extra):
    """Builds a new mesh from 2D grid points and quads, with each point's height read from the old ground by a ray from above, and swaps it in."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from .. import parts, scene_read
    low, high = scene_read.world_bounds(obj)
    old_vertices, old_triangles = parts.world_triangles(obj)
    tree = BVHTree.FromPolygons([tuple(v) for v in old_vertices], [tuple(t) for t in old_triangles], epsilon=0.0)
    mean_z = float(old_vertices[:, 2].mean())
    heights = np.empty(len(vertices2d))
    for index, (x, y) in enumerate(vertices2d):
        hit = tree.ray_cast(Vector((float(x), float(y), float(high[2]) + 10.0)), Vector((0, 0, -1)))
        heights[index] = hit[0].z if hit[0] is not None else mean_z
    world = np.column_stack([vertices2d, heights])
    inverse = np.array(obj.matrix_world.inverted())
    local = (np.c_[world, np.ones(len(world))] @ inverse.T)[:, :3]
    mesh = bpy.data.meshes.new(obj.data.name + ' ' + label)
    mesh.from_pydata([tuple(v) for v in local], [], faces)
    mesh.update()
    _swap_mesh(obj, mesh, area_before)
    return dict({'object': obj.name, 'faces': len(faces)}, **extra)


def uniform_grid_object(obj, cell, area_before):
    """A plain rectangle gets a uniform grid of squares of `cell` metres over its box (kept when that is not too many faces; the roads use it)."""
    from .. import scene_read
    low, high = scene_read.world_bounds(obj)
    xs = np.linspace(low[0], high[0], int(math.ceil((high[0] - low[0]) / cell)) + 1)
    ys = np.linspace(low[1], high[1], int(math.ceil((high[1] - low[1]) / cell)) + 1)
    gx, gy = np.meshgrid(xs, ys)
    vertices2d = np.stack([gx.ravel(), gy.ravel()], axis=1)
    columns = len(xs)
    faces = [(r * columns + c, r * columns + c + 1, (r + 1) * columns + c + 1, (r + 1) * columns + c) for r in range(len(ys) - 1) for c in range(columns - 1)]
    return _regrid(obj, vertices2d, faces, area_before, 'fine', {'cell': cell})


def subdivide_in_place(obj, target_cell, face_cap, area_before):
    """Splits every face in four, as many times as it takes to bring the mean square down to target_cell (but never past face_cap faces). The outline and the holes are untouched.
    Returns {'object', 'faces', 'levels', 'cell'} or None when not even one level fits under the cap."""
    import bmesh
    import bpy
    faces_now = len(obj.data.polygons)
    cell_now = mean_cell_metres(area_before, faces_now)
    levels = max(0, int(math.ceil(math.log2(cell_now / target_cell)))) if cell_now > target_cell else 0
    while levels > 0 and faces_now * (4 ** levels) > face_cap:
        levels -= 1
    if levels == 0:
        return None
    work = bmesh.new()
    work.from_mesh(obj.data)
    for _ in range(levels):
        bmesh.ops.subdivide_edges(work, edges=list(work.edges), cuts=1, use_grid_fill=True)
    mesh = bpy.data.meshes.new(obj.data.name + ' fine')
    work.to_mesh(mesh)
    work.free()
    mesh.update()
    _swap_mesh(obj, mesh, area_before)
    return {'object': obj.name, 'faces': len(mesh.polygons), 'levels': levels, 'cell': round(mean_cell_metres(area_before, len(mesh.polygons)), 3)}


def make_fine(obj, near_xy, limit, uniform_cell=None, face_cap=150000):
    """The one way to make a ground object fine enough (see the note at the top). Returns a plain sentence saying what was done, or None when the ground was already fine or was
    already changed by an earlier run. near_xy: where the camera looks (the graded grid is finest there). uniform_cell: for a plain rectangle, a uniform grid of this cell size
    when it fits under face_cap (the roads want that), else a graded grid."""
    from .. import house_numbers
    if obj.get('pk_regraded'):
        return None
    facts = outline_facts(obj)
    if not is_coarse(facts['faces'], 0.0, limit, facts['area']):
        return None
    if facts['plain_rectangle']:
        if uniform_cell and facts['box_area'] / (uniform_cell ** 2) <= face_cap:
            report = uniform_grid_object(obj, uniform_cell, facts['area'])
            return f'{obj.name}: a uniform grid of {report["faces"]} squares of {uniform_cell} m'
        report = regrade_object(obj, near_xy)
        return f'{obj.name}: regraded to {report["faces"]} faces (squares of {report["near_cell"]} m near the camera)' if report else None
    near_cell = house_numbers.value('place_surfaces.displacement_graded_grid_near_metres')
    report = subdivide_in_place(obj, uniform_cell or near_cell, face_cap, facts['area'])
    shape = f'{facts["boundary_loops"]} outline(s)' + (f', {facts["pieces"]} pieces' if facts['pieces'] > 1 else '')
    if report is None:
        return (f'LOOK {obj.name}: not a plain rectangle ({shape}) and too coarse (squares of {mean_cell_metres(facts["area"], facts["faces"]):.2f} m, over the {limit} m limit), '
                f'but splitting it would pass {face_cap} faces: make its mesh finer yourself near the road, or cut it into smaller ground objects')
    return f'{obj.name}: split in place {report["levels"]} time(s) to {report["faces"]} faces of about {report["cell"]} m; its outline ({shape}) is unchanged'
