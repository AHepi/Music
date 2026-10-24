"""What this does: shapes ROADS as real geometry: for a lane driven down by horses and carts, two wheel ruts a gauge apart (each a few centimetres to a hand deep, with a
little wobble in depth and line), a raised bank beside each rut, a trodden centre strip with hoof prints (round dimples about 12 to 14 cm across, one every 0.8 to 1.0 m, left and
right in turn), optionally a low crown of grass between the wheel lines on a lightly used lane, and puddle hollows in the bottoms of some ruts. All of it is a plain numpy HEIGHT
FUNCTION of position (lane_height_offset: tested without Blender); shape_roads moves the vertices of the ground object(s) the road lies on, after making the mesh fine enough
(a ground mesh with squares bigger than the house number is first replaced by a fine grid). It remembers each ground vertex's own height (a vertex attribute), so shaping twice gives the
same ground, not a ground dug twice. audit_roads measures the finished ground (from the real surface by rays, not from what the shaper meant to do) and says whether two ruts a gauge apart
are really there. The numbers are first tries (rut depth 5 to 15 cm, hoof spacing 0.8 to 1.0 m: invented; the coal mine yard used 4 to 9 cm); the cart gauge is a fact to confirm.
It needs numpy (the height function) and Blender (bpy) for the rest.
A concrete example: lane_height_offset(points, road) for a point on a wheel track gives about -0.08 (the rut depth) and for a point on the bank beside it a small positive number.
"""
import json
import math

import numpy as np

from .. import plan2d

RUT_WIDTH_DEFAULT = 0.18
BANK_SHARE = 0.3                  # the bank beside a rut stands about this share of the rut's depth
HOOF_RADIUS = 0.065
HOOF_DEPTH = 0.02
LANE_FADE_METRES = 0.4
CROWN_HEIGHT = 0.02
NEAR_CELL_METRES = 0.12
UNIFORM_FACE_CAP = 150000


def _wobble(distance, seed, scale=1.0):
    """A smooth repeatable number in [-1, 1] along the lane (a few incommensurate waves)."""
    rng = np.random.default_rng(int(seed))
    phases = rng.uniform(0, 2 * math.pi, 4)
    return (np.sin(distance / (7.0 * scale) + phases[0]) * 0.45 + np.sin(distance / (2.9 * scale) + phases[1]) * 0.3
            + np.sin(distance / (1.3 * scale) + phases[2]) * 0.15 + np.sin(distance / (0.55 * scale) + phases[3]) * 0.1)


def lane_height_offset(points, road, seed=1):
    """The change of ground height (metres, negative = lower) at each point (n, 2) from this road's ruts, banks, hoof prints, crown and puddle hollows.
    Also returns the rut mask (0..1, 1 in a wheel rut). Points farther than the lane's width plus a fade get 0."""
    p = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    polyline = road['polyline']
    distance, side, along = plan2d.distance_to_polyline(p, polyline)
    signed = side * distance
    width = float(road.get('width', 3.0))
    gauge = float(road.get('gauge', 1.3))
    depth = float(road.get('rut_depth', 0.08))
    rut_width = float(road.get('rut_width', RUT_WIDTH_DEFAULT))
    wobble_depth = 1.0 + 0.3 * _wobble(along, seed)
    wobble_line = 0.05 * _wobble(along, seed + 11, 1.7)                        # the wheels do not run on a ruler: the line wanders a few centimetres
    s = np.abs(signed + wobble_line * np.sign(signed))
    half = gauge / 2.0
    sigma = max(rut_width / 2.5, 0.02)
    rut = np.exp(-(((s - half) / sigma) ** 2))
    dz = -depth * wobble_depth * rut
    bank_sigma = 0.07
    for offset in (half + rut_width / 2.0 + 0.08, half - rut_width / 2.0 - 0.08):
        dz += BANK_SHARE * depth * wobble_depth * np.exp(-(((s - offset) / bank_sigma) ** 2))
    centre = np.exp(-((signed / max(half - rut_width / 2.0, 0.1)) ** 2))
    if road.get('centre_grass'):
        dz += CROWN_HEIGHT * np.clip(centre, 0.0, 1.0)
    if road.get('hoof', False):
        stride = float(road.get('hoof_stride', 0.9))
        index = np.round(along / stride)
        centre_along = index * stride
        lateral = np.where((index % 2) == 0, -0.1, 0.1)
        radial = np.hypot(along - centre_along, signed - lateral)
        dz -= HOOF_DEPTH * np.exp(-((radial / (HOOF_RADIUS * 0.8)) ** 2)) * (centre > 0.15)
    hollow = np.clip((_wobble(along, seed + 23, 2.5) - 0.35) / 0.3, 0.0, 1.0)
    dz -= 0.03 * hollow * rut
    fade = 1.0 - plan2d.smoothstep(width / 2.0, width / 2.0 + LANE_FADE_METRES, distance)
    return dz * fade, rut * fade


def total_offset(points, roads, seed=1):
    """Added up over every road in the settings: (dz, rut mask)."""
    p = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    dz = np.zeros(len(p))
    rut = np.zeros(len(p))
    for index, road in enumerate(roads):
        d, r = lane_height_offset(p, road, seed + 101 * index)
        dz += d
        rut = np.maximum(rut, r)
    return dz, rut


# ------------------------------------------------------------------ Blender side
def _road_box(roads):
    pts = np.vstack([np.asarray(r['polyline'], dtype=float) for r in roads])
    margin = max(float(r.get('width', 3.0)) for r in roads) / 2.0 + LANE_FADE_METRES + 1.0
    return pts.min(axis=0) - margin, pts.max(axis=0) + margin


def ground_objects_for(roads, objects):
    """The ground objects whose box meets the roads' box (a road lies on them)."""
    from .. import scene_read
    low, high = _road_box(roads)
    found = []
    for obj in objects:
        a, b = scene_read.world_bounds(obj)
        if a[0] <= high[0] and b[0] >= low[0] and a[1] <= high[1] and b[1] >= low[1]:
            found.append(obj)
    return found


def make_fine(obj, roads):
    """Makes the ground object's mesh fine enough for ruts: a uniform grid of 0.12 m squares when that is not too many faces, else a graded grid around the road. Returns a sentence or None."""
    import bpy
    import numpy as np_
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from .. import house_numbers, parts, scene_read
    from . import ground_mesh
    limit = house_numbers.value('place_surfaces.displacement_mesh_edge_metres_max')
    low, high = scene_read.world_bounds(obj)
    extent = float(max(high[0] - low[0], high[1] - low[1]))
    if not ground_mesh.is_coarse(len(obj.data.polygons), extent, min(limit, 0.25)):
        return None
    near_cell = house_numbers.value('place_surfaces.displacement_graded_grid_near_metres')
    faces_needed = ((high[0] - low[0]) / near_cell) * ((high[1] - low[1]) / near_cell)
    box_low, box_high = _road_box(roads)
    near = ((box_low[0] + box_high[0]) / 2.0, (box_low[1] + box_high[1]) / 2.0)
    if faces_needed <= UNIFORM_FACE_CAP:
        xs = np.linspace(low[0], high[0], int(math.ceil((high[0] - low[0]) / near_cell)) + 1)
        ys = np.linspace(low[1], high[1], int(math.ceil((high[1] - low[1]) / near_cell)) + 1)
        gx, gy = np.meshgrid(xs, ys)
        vertices2d = np.stack([gx.ravel(), gy.ravel()], axis=1)
        columns = len(xs)
        faces = [(r * columns + c, r * columns + c + 1, (r + 1) * columns + c + 1, (r + 1) * columns + c) for r in range(len(ys) - 1) for c in range(columns - 1)]
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
        mesh = bpy.data.meshes.new(obj.data.name + ' fine')
        mesh.from_pydata([tuple(v) for v in local], [], faces)
        mesh.update()
        for material in obj.data.materials:
            mesh.materials.append(material)
        old = obj.data
        obj.data = mesh
        if 'pk_original_mesh' not in obj.keys():
            old.use_fake_user = True              # kept, so undo can swap it back
            obj['pk_original_mesh'] = old.name
        obj['pk_regraded'] = 1
        return f'{obj.name}: a uniform grid of {len(faces)} squares of {near_cell} m'
    report = ground_mesh.regrade_object(obj, near)
    return f'{obj.name}: graded to {report["faces"]} faces around the lane' if report else None


def shape_roads(settings):
    """Shapes every road of the settings into the ground it lies on (see the note at the top). Returns a report with a plain summary."""
    import bpy
    from .. import names, parts, scene_read
    roads = settings.roads
    if not roads:
        return {'summary': 'no roads in the settings (nothing to shape)', 'roads': 0, 'objects': []}
    ground = [o for o in scene_read.mesh_objects(only_visible=True) if (o.get(names.ROLE) or '').startswith('ground.')]
    targets = ground_objects_for(roads, ground)
    if not targets:
        return {'summary': 'the roads lie on no ground object (give the ground a ground.* role)', 'roads': len(roads), 'objects': []}
    notes = []
    for obj in targets:
        said = make_fine(obj, roads)
        if said:
            notes.append(said)
    done = []
    for obj in targets:
        mesh = obj.data
        count = len(mesh.vertices)
        flat = np.empty(count * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', flat)
        local = flat.reshape(count, 3)
        matrix = np.array(obj.matrix_world, dtype=np.float64)
        inverse = np.linalg.inv(matrix)
        if 'pk_base_z' not in mesh.attributes:
            attribute = mesh.attributes.new('pk_base_z', 'FLOAT', 'POINT')
            attribute.data.foreach_set('value', local[:, 2].astype(np.float32))
        base = np.empty(count, dtype=np.float32)
        mesh.attributes['pk_base_z'].data.foreach_get('value', base)
        local[:, 2] = base
        world = local @ matrix[:3, :3].T + matrix[:3, 3]
        dz, rut = total_offset(world[:, :2], roads, seed=settings.seed)
        world[:, 2] += dz
        new_local = (np.c_[world, np.ones(count)] @ inverse.T)[:, :3]
        mesh.vertices.foreach_set('co', new_local.ravel())
        if 'pk_rut' not in mesh.attributes:
            mesh.attributes.new('pk_rut', 'FLOAT', 'POINT')
        mesh.attributes['pk_rut'].data.foreach_set('value', rut.astype(np.float32))
        mesh.update()
        done.append(obj.name)
        obj['pk_roads_shaped'] = json.dumps(roads, sort_keys=True)[:60000]
    parts.refresh_ground()
    bpy.context.view_layer.update()
    summary = f'{len(roads)} road(s) shaped into {len(done)} ground object(s)' + (': ' + '; '.join(notes) if notes else '')
    return {'summary': summary, 'roads': len(roads), 'objects': done, 'notes': notes}


def measure_ruts(road, ground_height, stations=9):
    """From the real ground (ground_height(x, y) by rays): across the lane at several stations along the road, where the two lowest points lie and how deep they are below the
    banks. Returns {'ruts_found': bool, 'depth_m': median depth, 'gauge_m': median distance between the two ruts}."""
    polyline = np.asarray(road['polyline'], dtype=float)
    distance, _, _ = plan2d.distance_to_polyline(polyline[:1], polyline)
    lengths = np.hypot(*np.diff(polyline, axis=0).T)
    total = float(lengths.sum())
    if total <= 0:
        return {'ruts_found': False, 'depth_m': 0.0, 'gauge_m': 0.0}
    width = float(road.get('width', 3.0))
    gauge = float(road.get('gauge', 1.3))
    depths, gauges = [], []
    for k in range(stations):
        t = total * (k + 0.5) / stations
        travelled, point, direction = 0.0, polyline[0], np.array([1.0, 0.0])
        for a, b, length in zip(polyline[:-1], polyline[1:], lengths):
            if travelled + length >= t:
                direction = (b - a) / max(length, 1e-9)
                point = a + direction * (t - travelled)
                break
            travelled += length
        normal = np.array([-direction[1], direction[0]])
        offsets = np.linspace(-width / 2.0, width / 2.0, 61)
        heights = np.array([ground_height(*(point + normal * o)) for o in offsets])
        left = offsets < -0.1
        right = offsets > 0.1
        if left.sum() < 3 or right.sum() < 3:
            continue
        li = np.argmin(np.where(left, heights, np.inf))
        ri = np.argmin(np.where(right, heights, np.inf))
        shoulder = float(np.median(heights))
        depths.append(shoulder - min(heights[li], heights[ri]))
        gauges.append(abs(offsets[ri] - offsets[li]))
    if not depths:
        return {'ruts_found': False, 'depth_m': 0.0, 'gauge_m': 0.0}
    depth, found_gauge = float(np.median(depths)), float(np.median(gauges))
    return {'ruts_found': bool(depth > 0.015 and abs(found_gauge - gauge) <= 0.25 * gauge), 'depth_m': round(depth, 4), 'gauge_m': round(found_gauge, 3)}


def audit_roads(settings, ground_objects):
    """The roads section of the audit: for each road in the settings, the ground objects it lies on, the relief and whether two ruts are really there."""
    from .. import names, parts, scene_read
    roads = settings.roads
    result = []
    if not roads:
        return result
    parts.refresh_ground()
    carriers = ground_objects_for(roads, [o for o in ground_objects])
    for road in roads:
        measured = measure_ruts(road, parts.ground_height_at)
        relief = max([scene_read.relief_metres(o) for o in carriers] + [measured['depth_m']]) if carriers else 0.0
        result.append({'name': road.get('name'), 'ground_objects': [o.name for o in carriers], 'relief_m': round(relief, 4), 'ruts_found': measured['ruts_found'],
                       'rut_depth_m': measured['depth_m'], 'gauge_m': measured['gauge_m'], 'gauge_in_settings_m': road.get('gauge')})
    return result
