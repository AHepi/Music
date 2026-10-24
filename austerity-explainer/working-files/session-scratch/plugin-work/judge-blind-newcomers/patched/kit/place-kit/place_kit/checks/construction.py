"""What this does: the CONSTRUCTION CHECK. It asks of every visible part of a place: what carries you? A part counts as carried when
a chain of resting contacts leads from it down to the ground (a plank on stringers, stringers on posts, posts on footings, footings on the
bed), or when it is joined into a carried part by overlapping it (a peg through a beam, a hinge). It reports parts that float, hang from
nothing, stop short of what they should meet, span too far, are turned inside out, have flickering twin faces, stand on nothing, or
(for lights) sit inside a solid; and doorways with no floor behind them. Scattered pieces (plants, leaves, litter) are left out on purpose
and the report says so.
It is written in our own words from earlier bridge checks (a bridge that "made no sense" was rebuilt from the ground up and then proved:
59 planks, none on fewer than 2 supports, 18 posts on footings). It reads the mesh as built (before modifiers), part by part (a loose piece
of a mesh is its own part), and needs Blender (bpy), mathutils and numpy.

A concrete example: a plank lying on two stringers that lie on two posts that stand on the ground passes; the same plank lifted 2 cm fails
with "floats" and the gap in millimetres; a post 4 cm short of its beam is reported short by 40 mm.
The numbers (touch 5 mm, rest patch 16 square centimetres within 8 mm, overlap 4 cm, span 1.38 m, floating over 5 mm, z-fight 1 mm) are the
place_construction house numbers in kit/film-settings.json.
"""
import json
import math
import os

import numpy as np

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .. import house_numbers, names, parts, roles as roles_module, scene_read, settings_file

GROUND_NAME = '<ground>'
CARRIER_ROLES = ('timber.post', 'stone.footing', 'timber.beam')       # parts whose job is to carry something above them
SHORT_REACH_METRES = 0.15                                            # a carrier this close under a part it does not touch is "short"


class Part:
    """One loose piece of one object: its world-space points and triangles, box and role."""

    def __init__(self, obj_name, index, vertices, triangles, role, may_hang, needs_support, max_span):
        self.obj_name = obj_name
        self.index = index
        self.V = vertices
        self.T = triangles
        self.role = role
        self.may_hang = may_hang
        self.needs_support = needs_support
        self.max_span = max_span
        self.bmin = vertices.min(axis=0)
        self.bmax = vertices.max(axis=0)
        self._bvh = None
        self._down = {}
        self.name = obj_name if index == 0 else f'{obj_name}:{index}'

    @property
    def bvh(self):
        if self._bvh is None:
            self._bvh = BVHTree.FromPolygons([tuple(v) for v in self.V], [tuple(t) for t in self.T], epsilon=0.0)
        return self._bvh

    def face_samples(self, spacing, down_only=False, max_count=2500, up_only=False):
        """Points on the part's triangles about `spacing` apart (the corners, edge midpoints and a grid inside bigger triangles). down_only keeps
        triangles that face down (the underside, where a part rests); up_only keeps triangles that face up (the top, where something may rest on it)."""
        key = (round(spacing, 4), down_only, up_only)
        if key in self._down:
            return self._down[key]
        tri = self.V[self.T]                                      # (n, 3, 3)
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        lengths = np.linalg.norm(normals, axis=1)
        valid = lengths > 1e-12
        normals[valid] /= lengths[valid][:, None]
        keep = (normals[:, 2] < -0.5) & valid if down_only else (normals[:, 2] > 0.5) & valid if up_only else valid
        if down_only and not keep.any():
            lowest = tri[:, :, 2].mean(axis=1)
            keep = lowest <= np.percentile(lowest, 20)
        tri = tri[keep]
        out = []
        if len(tri):
            edge = np.maximum.reduce([np.linalg.norm(tri[:, 1] - tri[:, 0], axis=1), np.linalg.norm(tri[:, 2] - tri[:, 1], axis=1), np.linalg.norm(tri[:, 0] - tri[:, 2], axis=1)])
            steps = np.clip(np.ceil(edge / spacing).astype(int), 1, 40)
            for k in np.unique(steps):
                members = tri[steps == k]
                a, b = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
                inside = (a + b) <= k
                u, v = (a[inside] / k), (b[inside] / k)
                weights = np.stack([1 - u - v, u, v], axis=1)                         # (m, 3)
                out.append(np.einsum('mj,tjc->tmc', weights, members).reshape(-1, 3))
        samples = np.vstack(out) if out else np.zeros((0, 3))
        if len(samples) > max_count:
            samples = samples[np.random.default_rng(1).choice(len(samples), max_count, replace=False)]
        self._down[key] = samples
        return samples


def _roles_for_scene(settings_data):
    return roles_module.tag_objects(scene_read.scene_facts(only_visible=True), settings_data, settings_file.roles_table())


def _loose_parts(obj, role_info, roles_table):
    mesh = obj.data
    if len(mesh.vertices) == 0 or len(mesh.polygons) == 0:
        return []
    count = len(mesh.vertices)
    flat = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', flat)
    matrix = np.array(obj.matrix_world, dtype=np.float64)
    world = flat.reshape(count, 3) @ matrix[:3, :3].T + matrix[:3, 3]
    mesh.calc_loop_triangles()
    tri = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get('vertices', tri)
    tri = tri.reshape(-1, 3)
    labels, number = scene_read.loose_part_labels(mesh)
    role = role_info.get('role') or ''
    spec = roles_table['roles'].get(role, {})
    found = []
    triangle_label = labels[tri[:, 0]]
    for k in range(number):
        mask = labels == k
        if not mask.any():
            continue
        index_map = -np.ones(count, dtype=np.int64)
        index_map[mask] = np.arange(mask.sum())
        member_triangles = tri[triangle_label == k]
        if len(member_triangles) == 0:
            continue
        found.append(Part(obj.name, k, world[mask], index_map[member_triangles], role, bool(spec.get('may_hang')), spec.get('needs_support', 'ground'), spec.get('max_span_metres')))
    return found


def _boxes_overlap_matrix(parts_list, margin):
    low = np.array([p.bmin for p in parts_list]) - margin
    high = np.array([p.bmax for p in parts_list]) + margin
    count = len(parts_list)
    pairs = []
    chunk = 400
    for start in range(0, count, chunk):
        stop = min(count, start + chunk)
        overlap = np.all((low[start:stop, None, :] <= high[None, :, :]) & (high[start:stop, None, :] >= low[None, :, :]), axis=2)
        rows, cols = np.nonzero(overlap)
        for r, c in zip(rows + start, cols):
            if r < c:
                pairs.append((int(r), int(c)))
    return pairs


def rest_patch(upper, lower_bvh, spacing, reach, lower_box=None):
    """How much of `upper`'s underside lies within `reach` of an up-facing face of the other tree and not below it: (area in square metres,
    smallest gap in metres)."""
    samples = upper.face_samples(spacing, down_only=True)
    if lower_box is not None:
        lo, hi = lower_box
        samples = samples[np.all((samples >= lo - reach) & (samples <= hi + reach), axis=1)]
    count, gap = 0, None
    for p in samples:
        hit = lower_bvh.find_nearest(Vector(p), reach)
        if hit[0] is None:
            continue
        location, normal = hit[0], hit[1]
        if normal.z > 0.6 and p[2] >= location.z - 0.003:
            count += 1
            gap = (p[2] - location.z) if gap is None else min(gap, p[2] - location.z)
    return count * spacing * spacing, gap


def signed_volume_and_closed(part):
    tri = part.V[part.T]
    volume = float(np.einsum('ij,ij->i', tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)
    edges = np.sort(np.concatenate([part.T[:, [0, 1]], part.T[:, [1, 2]], part.T[:, [2, 0]]]), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    return volume, bool((counts % 2 == 0).all() and len(counts) > 0)


def long_axis(part):
    centre = part.V.mean(axis=0)
    _, _, vt = np.linalg.svd(part.V[:, :2] - centre[:2], full_matrices=False)
    axis2 = vt[0]
    return centre, np.array([axis2[0], axis2[1], 0.0])


def unsupported_span(part, support_trees, step, reach):
    """The longest stretch (metres) along the part's long axis where nothing holds it up from below, between two supported stretches. A spot is held up when an up-facing
    surface of one of `support_trees` (the parts around it and the ground) lies within `reach` under its underside there (the same test as the rest patch)."""
    centre, axis = long_axis(part)
    if np.linalg.norm(axis) < 1e-9:
        return 0.0
    along = (part.V[:, :2] - centre[:2]) @ axis[:2]
    low, high = float(along.min()), float(along.max())
    own = part.bvh
    stations = np.arange(low + step / 2, high, step)
    supported = []
    for t in stations:
        x, y = centre[0] + axis[0] * t, centre[1] + axis[1] * t
        bottom = own.ray_cast(Vector((x, y, part.bmin[2] - 1.0)), Vector((0, 0, 1)))
        if bottom[0] is None:
            supported.append(None)                      # the long axis leaves the part here (a bent or diagonal part)
            continue
        point = Vector((x, y, bottom[0].z))
        held = False
        for tree in support_trees:
            hit = tree.find_nearest(point, reach)
            if hit[0] is not None and hit[1].z > 0.6 and point.z >= hit[0].z - 0.003:
                held = True
                break
        supported.append(held)
    longest, run, seen_support = 0.0, 0, False
    for state in supported:
        if state is None:
            continue
        if state:
            if seen_support:
                longest = max(longest, run * step)
            seen_support, run = True, 0
        else:
            run += 1
    return float(longest)


def _build_tree(vertex_blocks, triangle_blocks):
    """One BVH tree from blocks of world vertices and their local triangle lists."""
    vertices, triangles, offset = [], [], 0
    for v, t in zip(vertex_blocks, triangle_blocks):
        vertices.append(v)
        triangles.append(t + offset)
        offset += len(v)
    if not triangles:
        return None
    return BVHTree.FromPolygons([tuple(v) for v in np.vstack(vertices)], [tuple(t) for t in np.vstack(triangles)], epsilon=0.0)


def _triangle_centres_and_normals(part):
    tri = part.V[part.T]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0] = 1.0
    return tri.mean(axis=1), normals / lengths[:, None]


def check_construction(settings=None, owner=None, out_path=None):
    """Runs the check on every visible part (or only the parts of one owner, still using every other part as a possible carrier). Returns a
    dict: {'objects': {name: construction facts}, 'summary': {...}, 'exempt': [...]} and writes it to out_path when given."""
    number = house_numbers.value
    touch = number('place_construction.touch_metres')
    overlap_cm = number('place_construction.overlap_centimetres_min')
    rest_cm2 = number('place_construction.rest_patch_square_centimetres_min')
    reach = number('place_construction.rest_patch_reach_millimetres') / 1000.0
    float_gap = number('place_construction.float_gap_millimetres_fail') / 1000.0
    z_fight = number('place_construction.z_fight_gap_millimetres') / 1000.0
    span_step = number('place_construction.walk_ray_step_metres')
    spacing = number('place_construction.sample_spacing_metres')
    max_parts = number('place_construction.parts_checked_max')
    rules = settings.rules_dict() if hasattr(settings, 'rules_dict') else (settings or {})
    roles_table = settings_file.roles_table()
    bpy.context.view_layer.update()
    objects = scene_read.mesh_objects(only_visible=True)
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, roles_table)['by_object']
    parts.refresh_ground()
    exempt, ground_objects, all_parts = [], [], []
    for obj in objects:
        info = tagged.get(obj.name, {})
        role = info.get('role') or ''
        if scene_read.is_scatter(obj) or roles_module.is_never(role):
            exempt.append(obj.name)
        elif role.startswith('ground.'):
            ground_objects.append(obj)
        else:
            all_parts.extend(_loose_parts(obj, info, roles_table))
    ground_blocks = [parts.world_triangles(obj) for obj in ground_objects]
    ground_bvh = _build_tree([v for v, _ in ground_blocks], [t for _, t in ground_blocks])
    sampled_coarser = len(all_parts) > max_parts
    if sampled_coarser:
        spacing = min(0.04, spacing * math.sqrt(len(all_parts) / max_parts))
    combined_bvh = _build_tree([p.V for p in all_parts] + [v for v, _ in ground_blocks], [p.T for p in all_parts] + [t for _, t in ground_blocks])
    count = len(all_parts)

    # ---- contacts: who rests on whom, who is joined into whom, who touches whom (touching only matters for parts that may hang)
    rest_on = {i: set() for i in range(count)}
    embedded = {i: set() for i in range(count)}
    touching = {i: set() for i in range(count)}
    grounded, ground_gap = set(), {}
    for i, part in enumerate(all_parts):
        if part.needs_support == 'none':
            grounded.add(i)
            continue
        centre_xy = (part.bmin[:2] + part.bmax[:2]) / 2
        ground_z = max(parts.ground_height_at(*point) for point in [tuple(centre_xy), (part.bmin[0], part.bmin[1]), (part.bmax[0], part.bmax[1])])
        lowest = float(part.bmin[2])
        patch = rest_patch(part, ground_bvh, spacing, reach)[0] if ground_bvh is not None else 0.0
        if patch * 1e4 >= rest_cm2 or (ground_z - 1.0 <= lowest <= ground_z + reach and part.bmax[2] > ground_z):
            grounded.add(i)
        ground_gap[i] = lowest - ground_z
    pairs = _boxes_overlap_matrix(all_parts, max(reach, touch))
    neighbours = {i: set() for i in range(count)}
    for i, j in pairs:
        neighbours[i].add(j)
        neighbours[j].add(i)
    for i, j in pairs:
        a, b = all_parts[i], all_parts[j]
        for upper, lower, u, l in ((a, b, i, j), (b, a, j, i)):
            area, _ = rest_patch(upper, lower.bvh, spacing, reach, lower_box=(lower.bmin, lower.bmax))
            if area * 1e4 >= rest_cm2:
                rest_on[u].add(l)
        try:
            crossings = a.bvh.overlap(b.bvh)
        except Exception:   # noqa: BLE001 - a degenerate tree counts as no overlap
            crossings = []
        if crossings:
            extent = np.minimum(a.bmax, b.bmax) - np.maximum(a.bmin, b.bmin)
            if float(extent.min()) * 100.0 >= overlap_cm:             # the shallowest way through the overlap is how deep one part really sits in the other
                embedded[i].add(j)
                embedded[j].add(i)
        if a.may_hang or b.may_hang:
            for first, second, f, s in ((a, b, i, j), (b, a, j, i)):
                if any(second.bvh.find_nearest(Vector(v), touch)[0] is not None for v in first.V[:200]):
                    touching[f].add(s)
                    touching[s].add(f)

    # ---- who is carried: by resting chains from the ground (carried); else by being joined or touching a carried part (hung)
    carried = set(grounded)
    changed = True
    while changed:
        changed = False
        for i in range(count):
            if i not in carried and any(j in carried for j in rest_on[i]):
                carried.add(i)
                changed = True
    joined, hung = set(carried), set()
    changed = True
    while changed:
        changed = False
        for i in range(count):
            if i in joined:
                continue
            via = set(embedded[i]) | (set(touching[i]) if all_parts[i].may_hang else set())
            if any(j in joined for j in via) or any(j in joined for j in rest_on[i]):
                joined.add(i)
                if i not in carried:
                    hung.add(i)
                changed = True

    # ---- facts per part
    facts = {}
    for i, part in enumerate(all_parts):
        facts[i] = {'carried': i in joined, 'via': ([all_parts[j].name for j in sorted(rest_on[i])][:3] + (['ground'] if i in grounded else [])),
                    'hung': i in hung, 'hang_allowed': bool(part.may_hang), 'gap_mm': 0.0, 'floating': i not in joined, 'short_by_mm': 0, 'span_max_m': 0.0,
                    'max_span_m': part.max_span, 'inside_out': False, 'coplanar_faces': 0, 'buried_light': False, 'opening_floor_gap_m': None,
                    'seat_error_m': None, 'needs_ground': part.needs_support == 'ground'}
        if i not in joined and combined_bvh is not None:
            best = None
            for p in part.face_samples(spacing * 2, down_only=True)[:200]:
                hit = combined_bvh.ray_cast(Vector((p[0], p[1], p[2] - 0.0005)), Vector((0, 0, -1)), 5.0)
                if hit[0] is not None:
                    best = (p[2] - hit[0].z) if best is None else min(best, p[2] - hit[0].z)
            facts[i]['gap_mm'] = round((best if best is not None else 99.0) * 1000.0, 1)
        volume, closed = signed_volume_and_closed(part)
        facts[i]['inside_out'] = bool(closed and volume < 0)
        if part.max_span:
            around = [all_parts[j].bvh for j in sorted(neighbours[i])] + ([ground_bvh] if ground_bvh is not None else [])
            facts[i]['span_max_m'] = round(unsupported_span(part, around, span_step, reach), 3)
        if part.needs_support == 'ground' and i in grounded and not rest_on[i]:
            facts[i]['seat_error_m'] = round(float(ground_gap.get(i, 0.0)), 4)

    # ---- a post or footing a few centimetres under something it does not touch is "short"
    for i, part in enumerate(all_parts):
        if part.role not in CARRIER_ROLES or combined_bvh is None:
            continue
        best = None
        for p in part.face_samples(spacing * 2, up_only=True)[:300]:
            if p[2] < part.bmax[2] - 0.01:
                continue
            hit = combined_bvh.ray_cast(Vector((p[0], p[1], p[2] + 0.0005)), Vector((0, 0, 1)), SHORT_REACH_METRES)
            if hit[0] is not None and (hit[0].z - p[2]) > float_gap:
                best = (hit[0].z - p[2]) if best is None else min(best, hit[0].z - p[2])
        if best is not None and not any(i in rest_on[j] for j in range(count) if j != i):
            facts[i]['short_by_mm'] = round(best * 1000.0, 1)

    # ---- faces of two parts that face the same way and lie within a millimetre of each other flicker (z-fighting)
    if count:
        centres_normals = [_triangle_centres_and_normals(p) for p in all_parts]
        for i, j in _boxes_overlap_matrix(all_parts, z_fight):
            a, b = all_parts[i], all_parts[j]
            centres, normals = centres_normals[i]
            other_centres, other_normals = centres_normals[j]
            flicker = 0
            for k in range(min(len(centres), 300)):
                hit = b.bvh.find_nearest(Vector(centres[k]), z_fight)
                if hit[0] is not None and hit[3] <= z_fight and float(np.dot(normals[k], np.array(hit[1]))) > 0.99:
                    flicker += 1
            if flicker >= 2:
                facts[i]['coplanar_faces'] += flicker
                facts[j]['coplanar_faces'] += flicker

    # ---- doorways: a door's sill needs a floor close below it
    if combined_bvh is not None:
        for i, part in enumerate(all_parts):
            if part.role == 'timber.door':
                centre = (part.bmin + part.bmax) / 2
                # the floor under the sill: the ground there, or the top of whatever lies just below the sill (a ray from the sill downward, started 0.5 mm under the door's own underside)
                floor = parts.ground_height_at(float(centre[0]), float(centre[1]))
                hit = combined_bvh.ray_cast(Vector((centre[0], centre[1], part.bmin[2] - 0.0005)), Vector((0, 0, -1)), 50.0)
                if hit[0] is not None and hit[1].z > 0.6:
                    floor = max(floor, hit[0].z)
                facts[i]['opening_floor_gap_m'] = round(max(float(part.bmin[2] - floor), 0.0), 3)

    # ---- lights inside a solid: a ray up from the lamp crosses an odd number of surfaces
    lamps_buried = []
    if combined_bvh is not None:
        for lamp in [o for o in bpy.context.scene.objects if o.type == 'LIGHT' and not o.hide_render]:
            origin, crossings = lamp.matrix_world.translation.copy(), 0
            direction = Vector((0.0001, 0.0002, 1.0)).normalized()
            for _ in range(40):
                hit = combined_bvh.ray_cast(origin, direction, 1000.0)
                if hit[0] is None:
                    break
                crossings += 1
                origin = hit[0] + direction * 1e-5
            if crossings % 2 == 1:
                lamps_buried.append(lamp.name)

    # ---- fold the parts back into their objects
    folded = {}
    for i, part in enumerate(all_parts):
        fact = facts[i]
        now = folded.get(part.obj_name)
        if now is None:
            folded[part.obj_name] = dict(fact, parts=1)
            continue
        now['parts'] += 1
        for key in ('floating', 'hung', 'inside_out'):
            now[key] = now[key] or fact[key]
        now['carried'] = now['carried'] and fact['carried']
        for key in ('gap_mm', 'short_by_mm', 'span_max_m'):
            now[key] = max(now[key], fact[key])
        now['coplanar_faces'] += fact['coplanar_faces']
        if fact['opening_floor_gap_m'] is not None:
            now['opening_floor_gap_m'] = max(now['opening_floor_gap_m'] or 0.0, fact['opening_floor_gap_m'])
        if fact['seat_error_m'] is not None and (now['seat_error_m'] is None or abs(fact['seat_error_m']) > abs(now['seat_error_m'])):
            now['seat_error_m'] = fact['seat_error_m']
    for obj in objects:
        if obj.name in folded:
            sink = float(obj.get(names.SEAT_SINK, 0.0))
            if folded[obj.name]['seat_error_m'] is not None:
                folded[obj.name]['seat_error_m'] = round(folded[obj.name]['seat_error_m'] + sink, 4)
    for lamp in lamps_buried:
        folded[lamp] = {'carried': True, 'buried_light': True, 'parts': 0, 'floating': False, 'hung': False}
    if owner is not None:
        owned = {o.name for o in objects if o.get(names.OWNER) == owner}
        folded = {k: v for k, v in folded.items() if k in owned or k in lamps_buried}
    summary = {'parts_checked': count, 'objects_checked': len(folded), 'carried': sum(1 for f in folded.values() if f.get('carried')),
               'floating': sorted(k for k, f in folded.items() if f.get('floating')), 'hung': sorted(k for k, f in folded.items() if f.get('hung')),
               'sample_spacing_metres': spacing, 'sampled_coarser': sampled_coarser, 'scatter_exempt': len(exempt),
               'note': 'scattered pieces (plants, leaves, litter) and never-roles are exempt on purpose: they stand on the ground by their own roots'}
    result = {'objects': folded, 'summary': summary, 'exempt': exempt}
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, 'w') as handle:
            json.dump(result, handle, indent=1)
    return result
