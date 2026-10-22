"""What this does: writes UV maps FIRST, because a tangent-space normal map cannot sit on an object that has none. The UVs are in real METRES (one UV unit is one
metre, from the object's own scale), so every surface's material can scale them to its own tile size, and they are never mirrored (a mirrored island makes a
normal map read backwards). Methods: box (each face is projected along the axis its normal mostly points along, with a right-handed frame so nothing is
mirrored and side faces stay upright), planar (looking down from above: ground and water), plank (u runs along the object's longest side, v across it).
An object that already has UVs with few mirrored faces keeps them (a downloaded prop's own UVs are better than ours); the kit only writes when UVs are
missing or too mirrored.
It needs Blender (bpy) and numpy. A concrete example: write_uvs(obj, 'box') adds the UV layer "UVMap" to a wall box so a brick normal map sits on it at
real size; uv_facts(obj)['mirrored_share'] is then 0.0.
"""
import numpy as np

import bpy

from .. import house_numbers, scene_read

UV_LAYER = 'UVMap'


def _frame_for_normal(normal):
    """A right-handed (tangent, bitangent) pair for an outward normal (t x b = n), with the bitangent up (+z) on side faces."""
    n = np.asarray(normal, dtype=np.float64)
    axis = int(np.argmax(np.abs(n)))
    sign = 1.0 if n[axis] >= 0 else -1.0
    if axis == 2:
        return (np.array([1.0, 0, 0]), np.array([0, sign, 0.0]))
    if axis == 0:
        return (np.array([0, sign, 0.0]), np.array([0, 0, 1.0]))
    return (np.array([-sign, 0, 0.0]), np.array([0, 0, 1.0]))


def _axes_by_extent(extent):
    order = np.argsort(-np.asarray(extent))          # longest first
    unit = np.eye(3)
    return unit[order[0]], unit[order[1]], unit[order[2]]


def write_uvs(obj, method='box', layer_name=UV_LAYER):
    """Writes the UV layer for the object's mesh in metres by the method (box, planar or plank). Returns the layer name."""
    mesh = obj.data
    if layer_name in mesh.uv_layers:
        layer = mesh.uv_layers[layer_name]
    else:
        layer = mesh.uv_layers.new(name=layer_name)
    mesh.uv_layers.active = layer
    count = len(mesh.loops)
    if count == 0:
        return layer.name
    scale = np.abs(np.array(obj.scale, dtype=np.float64))
    flat = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', flat)
    points = flat.reshape(-1, 3) * scale
    loop_vertex = np.empty(count, dtype=np.int64)
    mesh.loops.foreach_get('vertex_index', loop_vertex)
    polygons = len(mesh.polygons)
    starts = np.empty(polygons, dtype=np.int64)
    totals = np.empty(polygons, dtype=np.int64)
    mesh.polygons.foreach_get('loop_start', starts)
    mesh.polygons.foreach_get('loop_total', totals)
    normals = np.empty(polygons * 3, dtype=np.float64)
    mesh.polygons.foreach_get('normal', normals)
    normals = normals.reshape(-1, 3) * (1.0 / np.where(scale == 0, 1, scale))
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0] = 1.0
    normals = normals / lengths[:, None]
    extent = points.max(axis=0) - points.min(axis=0) if len(points) else np.ones(3)
    longest, middle, thinnest = _axes_by_extent(extent)
    uv = np.zeros((count, 2), dtype=np.float32)
    for polygon in range(polygons):
        loops = np.arange(starts[polygon], starts[polygon] + totals[polygon])
        p = points[loop_vertex[loops]]
        n = normals[polygon]
        if method == 'planar':
            tangent, bitangent = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
        elif method == 'plank':
            axis = int(np.argmax(np.abs(n)))
            thin_axis, mid_axis, long_axis = int(np.argmax(thinnest)), int(np.argmax(middle)), int(np.argmax(longest))
            if axis == thin_axis:
                tangent, bitangent = longest, middle
            elif axis == mid_axis:
                tangent, bitangent = longest, thinnest
            else:
                tangent, bitangent = middle, thinnest
        else:
            tangent, bitangent = _frame_for_normal(n)
        u, v = p @ tangent, p @ bitangent
        # make sure the island is not mirrored: its winding in UV must match the face's winding
        if len(u) >= 3:
            area = (u[1] - u[0]) * (v[2] - v[0]) - (v[1] - v[0]) * (u[2] - u[0])
            if area < 0:
                u = -u
        uv[loops, 0], uv[loops, 1] = u, v
    layer.uv.foreach_set('vector', uv.ravel())
    mesh.update()
    return layer.name


def needs_uvs(obj):
    """True when the object has no UV layer, or more mirrored faces than the house number allows."""
    facts = scene_read.uv_facts(obj)
    return (not facts['has']) or facts['mirrored_share'] > house_numbers.value('place_surfaces.uv_mirrored_face_share_max')


def ensure_uvs(obj, method='box'):
    """Writes UVs only when they are missing or mirrored; returns (layer name, whether it wrote them)."""
    if needs_uvs(obj):
        return write_uvs(obj, method), True
    return (obj.data.uv_layers.active or obj.data.uv_layers[0]).name, False
