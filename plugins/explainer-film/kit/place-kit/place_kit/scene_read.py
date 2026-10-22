"""What this does: reads plain facts about a Blender scene for the rest of the kit: which mesh objects are visible, what
collections and materials they have, their custom properties, their size in world metres, how many triangles they really
draw after modifiers, and their world-space points as numpy arrays. Nothing here changes the scene. It needs Blender (bpy)
and numpy; the role matcher and the judge work on the plain dictionaries it returns.

A concrete example: object_facts(obj) for a plank returns {"name": "plank 3", "collections": ["Place: huts"],
"materials": ["oak"], "properties": {"place_role": "timber.plank"}, "size": [1.2, 0.15, 0.04], ...}.
"""
import numpy as np

import bpy
from mathutils import Vector

from . import names

OBJECT_TYPES_WITH_SURFACE = ('MESH',)


def is_visible(obj):
    """Visible in the render and in the view layer (hidden helpers, preview cameras and disabled objects are left out)."""
    if obj.hide_render:
        return False
    try:
        return bool(obj.visible_get())
    except RuntimeError:                       # an object that is in no view layer at all
        return False


def mesh_objects(scene=None, only_visible=True):
    """Every mesh object of the scene (in file order), visible only by default."""
    scene = scene or bpy.context.scene
    found = [o for o in scene.objects if o.type in OBJECT_TYPES_WITH_SURFACE]
    return [o for o in found if is_visible(o)] if only_visible else found


def collection_names(obj):
    return [c.name for c in obj.users_collection]


def material_names(obj):
    return [slot.material.name for slot in obj.material_slots if slot.material is not None]


def custom_properties(obj):
    """The object's own custom properties as plain Python values (the kit's place_*, pk_* ones and anything simple)."""
    props = {}
    for key in obj.keys():
        if key.startswith('_'):
            continue
        value = obj[key]
        if isinstance(value, (int, float, str, bool)):
            props[key] = value
        elif hasattr(value, 'to_list'):
            props[key] = value.to_list()
    return props


def world_points(obj, evaluated=False, depsgraph=None):
    """The object's vertices in world space as an (n, 3) float64 array (after modifiers when evaluated=True)."""
    if evaluated:
        depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
        owner = obj.evaluated_get(depsgraph)
        mesh = owner.to_mesh()
    else:
        owner, mesh = obj, obj.data
    count = len(mesh.vertices)
    flat = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', flat)
    local = flat.reshape(count, 3)
    matrix = np.array(obj.matrix_world, dtype=np.float64)
    points = local @ matrix[:3, :3].T + matrix[:3, 3]
    if evaluated:
        owner.to_mesh_clear()
    return points


def triangle_count(obj, evaluated=True, depsgraph=None):
    """How many triangles the object draws (after modifiers by default)."""
    if evaluated:
        depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
        owner = obj.evaluated_get(depsgraph)
        mesh = owner.to_mesh()
        try:
            mesh.calc_loop_triangles()
            return len(mesh.loop_triangles)
        finally:
            owner.to_mesh_clear()
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def world_bounds(obj):
    """(min, max) corners of the object's bounding box in world space as two numpy arrays."""
    corners = np.array([obj.matrix_world @ Vector(c) for c in obj.bound_box], dtype=np.float64)
    return corners.min(axis=0), corners.max(axis=0)


def object_size(obj):
    low, high = world_bounds(obj)
    return high - low


def object_facts(obj):
    """Plain facts for the role matcher and the audit."""
    low, high = world_bounds(obj)
    return {'name': obj.name, 'collections': collection_names(obj), 'materials': material_names(obj), 'properties': custom_properties(obj),
            'size': [float(v) for v in (high - low)], 'min': [float(v) for v in low], 'max': [float(v) for v in high]}


def scene_facts(scene=None, only_visible=True):
    return [object_facts(o) for o in mesh_objects(scene, only_visible)]


def is_scatter(obj):
    return bool(obj.get(names.SCATTER))


def loose_part_labels(mesh):
    """For each vertex, the number of the connected piece it belongs to (union-find over the edges), as an int array, and the piece count."""
    count = len(mesh.vertices)
    if count == 0:
        return np.zeros(0, dtype=np.int64), 0
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', edges)
    edges = edges.reshape(-1, 2)
    parent = np.arange(count)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in edges.tolist():
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    roots = np.array([find(i) for i in range(count)], dtype=np.int64)
    _, labels = np.unique(roots, return_inverse=True)
    return labels, int(labels.max()) + 1


def is_plain_box(obj):
    """True for a bare six-sided box (8 corners, 6 four-sided faces) with no bevel modifier: the shape a model has before any shaping."""
    if obj.type != 'MESH':
        return False
    mesh = obj.data
    if len(mesh.vertices) != 8 or len(mesh.polygons) != 6:
        return False
    if any(len(p.vertices) != 4 for p in mesh.polygons):
        return False
    return not any(m.type == 'BEVEL' for m in obj.modifiers)


def has_bevel(obj):
    return any(m.type == 'BEVEL' for m in obj.modifiers) or bool(obj.get('pk_bevelled'))


def has_shape_damage(obj):
    return any(m.name == names.DAMAGE_MODIFIER for m in obj.modifiers) or bool(obj.get(names.SHAPE_DAMAGE))


def uv_facts(obj):
    """{'has': bool, 'layer': name or None, 'mirrored_share': share of faces whose UV winding is clockwise (the map would read backwards)}."""
    mesh = obj.data
    if not mesh.uv_layers:
        return {'has': False, 'layer': None, 'mirrored_share': 0.0}
    layer = mesh.uv_layers.active or mesh.uv_layers[0]
    polygons = len(mesh.polygons)
    if polygons == 0:
        return {'has': True, 'layer': layer.name, 'mirrored_share': 0.0}
    loops = len(mesh.loops)
    uv = np.empty(loops * 2, dtype=np.float32)
    layer.uv.foreach_get('vector', uv)
    uv = uv.reshape(loops, 2)
    starts = np.empty(polygons, dtype=np.int64)
    mesh.polygons.foreach_get('loop_start', starts)
    first, second, third = uv[starts], uv[starts + 1], uv[starts + 2]
    area = (second[:, 0] - first[:, 0]) * (third[:, 1] - first[:, 1]) - (second[:, 1] - first[:, 1]) * (third[:, 0] - first[:, 0])
    return {'has': True, 'layer': layer.name, 'mirrored_share': float(np.mean(area < -1e-12))}


def mean_edge_length(obj):
    """The average edge length of the mesh in world metres (0 for a mesh with no edges)."""
    mesh = obj.data
    if len(mesh.edges) == 0:
        return 0.0
    points = world_points(obj)
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', edges)
    edges = edges.reshape(-1, 2)
    return float(np.linalg.norm(points[edges[:, 0]] - points[edges[:, 1]], axis=1).mean())


def relief_metres(obj):
    """How uneven a roughly flat object is: the spread (95th minus 5th percentile) of its vertex heights after a plane is fitted and removed."""
    points = world_points(obj, evaluated=True)
    if len(points) < 4:
        return 0.0
    design = np.c_[points[:, 0], points[:, 1], np.ones(len(points))]
    coefficients, *_ = np.linalg.lstsq(design, points[:, 2], rcond=None)
    residual = points[:, 2] - design @ coefficients
    return float(np.percentile(residual, 95) - np.percentile(residual, 5))


def has_subdivision(obj):
    return any(m.type in ('SUBSURF', 'MULTIRES') for m in obj.modifiers)


def facing_slope_degrees(obj):
    """The typical slope (degrees from flat) of the up-facing faces of an object: a roof's pitch. None when no face looks up."""
    mesh = obj.data
    polygons = len(mesh.polygons)
    if polygons == 0:
        return None
    normals = np.empty(polygons * 3, dtype=np.float32)
    mesh.polygons.foreach_get('normal', normals)
    normals = normals.reshape(-1, 3).astype(np.float64)
    matrix = np.array(obj.matrix_world.to_3x3(), dtype=np.float64)
    world = normals @ matrix.T
    length = np.linalg.norm(world, axis=1)
    length[length == 0] = 1.0
    world = world / length[:, None]
    up = world[:, 2] > 0.2
    if not up.any():
        return None
    slopes = np.degrees(np.arccos(np.clip(world[up, 2], -1, 1)))
    return float(np.median(slopes))
