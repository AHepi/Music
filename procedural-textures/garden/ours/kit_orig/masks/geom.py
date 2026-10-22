# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Geometry helpers for the reader (they run inside Blender): the triangles of every role's objects in world space (modifiers applied, instanced geometry such as a roof of
# many copies of one tile included), BVH search trees (Blender's fast "what is near this point / what does this ray hit" structure), grids, and picture writing helpers.
# Everything is asked of the real 3D shapes; nothing here names an object: roles come from the set file through the kit's role finder.
import math
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .grid import Grid, blur, smoothstep  # noqa: F401  (pure numpy helpers live in grid.py so the pack code can run without Blender)


class Timer:
    def __init__(self):
        self.t0 = time.time()
        self.marks = []

    def mark(self, what):
        now = time.time()
        self.marks.append((what, round(now - self.t0, 2)))
        print(f'[reader] {what}: {now - self.t0:.1f} s', flush=True)
        self.t0 = now


class RoleGeometry:
    """World-space triangles per role, gathered once from the evaluated scene.
        geo = RoleGeometry(role_map)       # role_map: apply.roles.RoleMap
        geo.tree(['wall.masonry', ...])    # a BVH tree of those roles (None if they have no triangles)
        geo.triangles(['ground'])          # (vertices Nx3, triangles Mx3, owner index per triangle, owner names)
    """

    def __init__(self, role_map, include_hidden=False):
        self.role_map = role_map
        self.settings = role_map.settings
        self._tri = {}
        self._trees = {}
        depsgraph = bpy.context.evaluated_depsgraph_get()
        self.depsgraph = depsgraph
        parts = {}
        for inst in depsgraph.object_instances:
            obj = inst.object
            if obj.type not in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT'):
                continue
            host = inst.parent if (inst.is_instance and inst.parent is not None) else obj
            name = host.original.name if hasattr(host, 'original') else host.name
            role = role_map.primary.get(name)
            if role is None:
                continue
            if not include_hidden and host.original.hide_render:
                continue
            try:
                mesh = obj.to_mesh()
            except RuntimeError:
                continue
            if mesh is None or len(mesh.vertices) == 0:
                if mesh is not None:
                    obj.to_mesh_clear()
                continue
            mesh.calc_loop_triangles()
            co = np.empty(len(mesh.vertices) * 3, np.float64)
            mesh.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            matrix = np.array(inst.matrix_world)
            world = co @ matrix[:3, :3].T + matrix[:3, 3]
            tri = np.empty(len(mesh.loop_triangles) * 3, np.int64)
            mesh.loop_triangles.foreach_get('vertices', tri)
            parts.setdefault(role, []).append((name, world, tri.reshape(-1, 3)))
            obj.to_mesh_clear()
        self.parts = parts

    def _roles(self, names):
        return self.settings.expand_roles(names) if names else []

    def triangles(self, names):
        key = tuple(sorted(self._roles(names)))
        if key in self._tri:
            return self._tri[key]
        verts, tris, owner, owners, offset = [], [], [], [], 0
        for role in key:
            for name, world, tri in self.parts.get(role, []):
                verts.append(world)
                tris.append(tri + offset)
                owner.append(np.full(len(tri), len(owners), np.int32))
                owners.append(name)
                offset += len(world)
        result = None if not verts else (np.concatenate(verts), np.concatenate(tris), np.concatenate(owner), owners)
        self._tri[key] = result
        return result

    def tree(self, names):
        key = tuple(sorted(self._roles(names)))
        if key in self._trees:
            return self._trees[key]
        data = self.triangles(names)
        tree = None
        if data is not None:
            v, t = data[0], data[1]
            tree = BVHTree.FromPolygons([tuple(p) for p in v], [tuple(p) for p in t], all_triangles=True)
        self._trees[key] = tree
        return tree

    def owners_tree(self, names):
        """Tree plus the owner object of every triangle (BVH ray_cast returns the triangle index)."""
        data = self.triangles(names)
        return (self.tree(names), data[2], data[3]) if data is not None else (None, None, None)

    def extra_tree(self, patterns):
        """A tree of every object whose name matches one of the patterns, whether or not it has a role (leaf masses that shade but are never weathered)."""
        import re
        key = ('extra',) + tuple(patterns)
        if key in self._trees:
            return self._trees[key]
        verts, tris, offset = [], [], 0
        for inst in self.depsgraph.object_instances:
            obj = inst.object
            if obj.type != 'MESH':
                continue
            host = inst.parent if (inst.is_instance and inst.parent is not None) else obj
            name = host.original.name
            if not any(re.match(p, name) for p in patterns):
                continue
            mesh = obj.to_mesh()
            if mesh is None or len(mesh.vertices) == 0:
                continue
            mesh.calc_loop_triangles()
            co = np.empty(len(mesh.vertices) * 3, np.float64)
            mesh.vertices.foreach_get('co', co)
            matrix = np.array(inst.matrix_world)
            world = co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
            tri = np.empty(len(mesh.loop_triangles) * 3, np.int64)
            mesh.loop_triangles.foreach_get('vertices', tri)
            verts.append(world)
            tris.append(tri.reshape(-1, 3) + offset)
            offset += len(world)
            obj.to_mesh_clear()
        tree = BVHTree.FromPolygons([tuple(p) for p in np.concatenate(verts)], [tuple(p) for p in np.concatenate(tris)], all_triangles=True) if verts else None
        self._trees[key] = tree
        return tree

    def objects_of(self, names):
        return sorted({name for role in self._roles(names) for name, _, _ in self.parts.get(role, [])})

    def bounds(self, names):
        data = self.triangles(names)
        if data is None:
            return None
        return data[0].min(axis=0), data[0].max(axis=0)


def cast_down_grid(tree, grid, z_top, depth, progress=None):
    """Ground height at every dot of the grid by a ray from above; returns (height array (rows, cols) float32, has array bool)."""
    height = np.zeros(grid.shape(), np.float32)
    has = np.zeros(grid.shape(), bool)
    down = Vector((0, 0, -1))
    ray = tree.ray_cast
    for j, y in enumerate(grid.ys):
        for i, x in enumerate(grid.xs):
            hit = ray(Vector((x, y, z_top)), down, depth)
            if hit[0] is not None:
                height[j, i] = hit[0].z
                has[j, i] = True
    return height, has


def nearest_distances(tree, grid, z, reach, mask=None):
    """Distance from (x, y, z[j, i]) to the nearest surface of the tree, up to reach (reach where nothing is nearer)."""
    out = np.full(grid.shape(), reach, np.float32)
    find = tree.find_nearest
    for j, y in enumerate(grid.ys):
        for i, x in enumerate(grid.xs):
            if mask is not None and not mask[j, i]:
                continue
            r = find(Vector((x, y, float(z[j, i]))), reach)
            if r[0] is not None:
                out[j, i] = r[3]
    return out


def cone_directions(count, max_angle_deg, axis=(0.0, 0.0, 1.0)):
    """`count` fixed directions spread evenly (golden spiral) inside a cone of max_angle_deg round the axis (default straight up)."""
    directions = []
    golden = math.pi * (3 - math.sqrt(5))
    cos_max = math.cos(math.radians(max_angle_deg))
    for k in range(count):
        z = 1 - (1 - cos_max) * (k + 0.5) / count
        r = math.sqrt(max(0.0, 1 - z * z))
        phi = golden * k
        directions.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
    if tuple(axis) != (0.0, 0.0, 1.0):
        rot = Vector((0, 0, 1)).rotation_difference(Vector(axis))
        directions = [rot @ d for d in directions]
    return directions


def hemisphere_directions(count):
    """Cosine-weighted fixed directions over the upper hemisphere (golden spiral)."""
    directions = []
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(count):
        u = (k + 0.5) / count
        r = math.sqrt(u)
        z = math.sqrt(max(0.0, 1 - u))
        phi = golden * k
        directions.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
    return directions
