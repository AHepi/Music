"""What this does: makes a GRADED GRID for ground: small squares near the camera (0.12 m) that grow a step at a time (1.09 times) to large ones far away (5 m),
so real displacement and shaped ruts have vertices to move where the viewer looks, without a million faces for the distant ground. The grid's squares are
laid out in plain numpy (graded_axis, graded_grid: tested without Blender); regrade_object replaces a coarse ground object's mesh with such a grid over the
same box, keeping the height of the old ground (read by a ray from above) and writing UVs in metres. A ground mesh that is already fine is left alone.
The numbers come from the coal mine yard (house numbers place_surfaces.displacement_graded_grid_*). It needs numpy; regrade_object needs Blender (bpy).
A concrete example: graded_axis(0, 14, near=7, near_cell=0.12, growth=1.09, far_cell=5) gives the x lines of a 14 m ground: 0.12 m apart around x = 7.
"""
import numpy as np


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


def is_coarse(face_count, extent_metres, limit_metres):
    """True when a ground object's mean square is longer than the limit (so it cannot show displacement or ruts)."""
    if face_count <= 0:
        return True
    return (extent_metres / max(np.sqrt(face_count), 1.0)) > limit_metres


def regrade_object(obj, near_xy=None, settings_numbers=None):
    """Replaces the object's mesh with a graded grid over the same box, keeping the old surface height. Returns a report dict, or None when the object is
    already fine. The object keeps its name, role, materials and place in the scene."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from .. import house_numbers, names, parts, scene_read
    limit = house_numbers.value('place_surfaces.displacement_mesh_edge_metres_max')
    if obj.get('pk_regraded'):
        return None                                      # already a graded grid (a second finish must not grade it again)
    low, high = scene_read.world_bounds(obj)
    extent = float(max(high[0] - low[0], high[1] - low[1]))
    if not is_coarse(len(obj.data.polygons), extent, limit):
        return None
    near_cell = house_numbers.value('place_surfaces.displacement_graded_grid_near_metres')
    growth = house_numbers.value('place_surfaces.displacement_graded_grid_growth')
    far_cell = house_numbers.value('place_surfaces.displacement_graded_grid_far_metres')
    if near_xy is None:
        camera = bpy.context.scene.camera
        near_xy = (camera.matrix_world.translation.x, camera.matrix_world.translation.y) if camera is not None else ((low[0] + high[0]) / 2, (low[1] + high[1]) / 2)
    vertices2d, faces = graded_grid((low[0], high[0]), (low[1], high[1]), near_xy, near_cell, growth, far_cell)
    # the old surface's height under each new vertex (a ray from above against the old mesh)
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
    mesh = bpy.data.meshes.new(obj.data.name + ' graded')
    mesh.from_pydata([tuple(v) for v in local], [], faces)
    mesh.update()
    for slot_material in obj.data.materials:
        mesh.materials.append(slot_material)
    old = obj.data
    obj.data = mesh
    if 'pk_original_mesh' not in obj.keys():
        old.use_fake_user = True              # kept, so undo can swap it back (a mesh nothing uses is dropped when the file is saved)
        obj['pk_original_mesh'] = old.name
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj['pk_regraded'] = 1
    return {'object': obj.name, 'faces': len(faces), 'near_cell': near_cell, 'near_xy': [float(near_xy[0]), float(near_xy[1])]}
