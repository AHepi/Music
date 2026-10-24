"""What this does: the helpers a part builder uses so that its objects are tagged (owner and role), kept in their own
collection, seated on the real ground and easy to rebuild without leaving old copies behind. A part is one piece of the place
built by one owner (for example the lanes, or the huts); every visible object of it gets exactly one role.

A concrete example, as in a stage file:
    pk.forget_part('huts')                       # idempotent: remove what an earlier run made
    pk.begin_part('huts')                        # make the collection "Place: huts"
    wall = pk.new_part_object('huts', 'wall.plaster', 'hut 1 wall', mesh)
    pk.seat_on_ground(wall)                          # its lowest point rests on the ground under it
    pk.ground_height_at(3.0, 4.0)                    # how high the ground is there (0.0 when there is no ground yet)
It needs Blender (bpy) and numpy.
"""
import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import names, scene_read

_ground_cache = {'trees': None}


def begin_part(owner):
    """The collection 'Place: <owner>', made and linked to the scene when it is not there yet."""
    name = names.part_collection_name(owner)
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if collection.name not in bpy.context.scene.collection.children:
        try:
            bpy.context.scene.collection.children.link(collection)
        except RuntimeError:
            pass                                  # it is linked inside another collection already
    return collection


def new_part_object(owner, role, name, mesh_or_object, collection=None):
    """Makes (or takes) an object, links it only to the part's collection and tags it with place_owner and place_role.
    mesh_or_object: a bpy Mesh (a new object is made from it) or an existing Object (it is moved into the part's collection)."""
    target = collection or begin_part(owner)
    if isinstance(mesh_or_object, bpy.types.Object):
        obj = mesh_or_object
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        target.objects.link(obj)
        if name:
            obj.name = name
    else:
        obj = bpy.data.objects.new(name, mesh_or_object)
        target.objects.link(obj)
    obj[names.OWNER] = owner
    obj[names.ROLE] = role
    return obj


def objects_of(owner):
    return [o for o in bpy.data.objects if o.get(names.OWNER) == owner]


def forget_part(owner):
    """Removes everything an earlier run of this owner's stage made: its objects (and their meshes when nothing else uses them) and its collection.
    Idempotent: calling it for an owner with nothing does nothing."""
    removed = 0
    for obj in objects_of(owner):
        mesh = obj.data if obj.type == 'MESH' else None
        bpy.data.objects.remove(obj, do_unlink=True)
        removed += 1
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    collection = bpy.data.collections.get(names.part_collection_name(owner))
    if collection is not None and not collection.objects and not collection.children:
        bpy.data.collections.remove(collection)
    _ground_cache['trees'] = None
    return removed


# ------------------------------------------------------------------ the ground
def is_ground_object(obj):
    role = obj.get(names.ROLE) or ''
    return role.startswith('ground.')


def world_triangles(obj, depsgraph=None):
    """(vertices in world space, triangles) of the object after its modifiers, for a BVH tree."""
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    owner = obj.evaluated_get(depsgraph)
    mesh = owner.to_mesh()
    try:
        count = len(mesh.vertices)
        flat = np.empty(count * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', flat)
        matrix = np.array(obj.matrix_world, dtype=np.float64)
        vertices = flat.reshape(count, 3) @ matrix[:3, :3].T + matrix[:3, 3]
        mesh.calc_loop_triangles()
        triangles = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
        mesh.loop_triangles.foreach_get('vertices', triangles)
        return vertices, triangles.reshape(-1, 3)
    finally:
        owner.to_mesh_clear()


def refresh_ground():
    """Builds the ray-casting trees of every ground object again (call it after the ground changes)."""
    bpy.context.view_layer.update()
    trees = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and is_ground_object(obj) and not obj.hide_render:
            vertices, triangles = world_triangles(obj)
            if len(triangles):
                trees.append(BVHTree.FromPolygons([tuple(v) for v in vertices], [tuple(t) for t in triangles], epsilon=0.0))
    _ground_cache['trees'] = trees
    return len(trees)


def ground_height_at(x, y):
    """The height of the highest ground surface under (x, y), by a ray from above; 0.0 when there is no ground there (or no ground object)."""
    if _ground_cache['trees'] is None:
        refresh_ground()
    best = None
    for tree in _ground_cache['trees']:
        hit = tree.ray_cast(Vector((float(x), float(y), 1.0e4)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is not None and (best is None or hit[0].z > best):
            best = hit[0].z
    return 0.0 if best is None else float(best)


def footprint_points(obj, inside=0.9):
    """Sample points (x, y) under an object: the centre and the four corners of its bounding box pulled toward the centre."""
    low, high = scene_read.world_bounds(obj)
    centre = (low + high) / 2
    half = (high - low) / 2 * inside
    points = [(centre[0], centre[1])]
    for sx in (-1, 1):
        for sy in (-1, 1):
            points.append((centre[0] + sx * half[0], centre[1] + sy * half[1]))
    return points


def ground_under(obj):
    """The highest ground height under the object's footprint."""
    return max(ground_height_at(x, y) for x, y in footprint_points(obj))


def seat_on_ground(obj, sink=0.0):
    """Moves the object up or down so its lowest point is `sink` metres below the ground under its footprint, and remembers the ground height
    it used (so it can be seated again when the ground changes). Returns how far it moved."""
    bpy.context.view_layer.update()
    low, _ = scene_read.world_bounds(obj)
    ground = ground_under(obj)
    shift = (ground - sink) - float(low[2])
    obj.location.z += shift
    bpy.context.view_layer.update()
    obj[names.SEAT_GROUND_Z] = float(ground)
    obj[names.SEAT_SINK] = float(sink)
    return shift


def reseat_on_ground(objects=None):
    """After the ground changed (ruts, regrading): moves every object that was seated by the amount the ground under it moved.
    Returns {object name: metres moved} for the ones that moved."""
    refresh_ground()
    moved = {}
    for obj in objects or [o for o in bpy.context.scene.objects if names.SEAT_GROUND_Z in o.keys()]:
        old = float(obj[names.SEAT_GROUND_Z])
        new = ground_under(obj)
        if abs(new - old) > 1e-6:
            obj.location.z += new - old
            obj[names.SEAT_GROUND_Z] = float(new)
            moved[obj.name] = float(new - old)
    if moved:
        bpy.context.view_layer.update()
    return moved


def is_keep_clear(x, y):
    """True when the plan masks say nothing may be put at (x, y) (a wheel track, a doorstep, a worn path). False when no plan masks are made yet."""
    from .wear import masks
    return masks.keep_clear_at(x, y)
