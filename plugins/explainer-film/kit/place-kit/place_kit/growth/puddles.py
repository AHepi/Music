"""What this does: lays STANDING WATER in the hollows and ruts of the ground when the place is damp or wet, as the project's earlier yard of carts and lumps did by hand: a flat, dark, mirror-like sheet at
the water's level in each hollow, so the water's edge is exactly where the level meets the ground (the sheet runs a little way under the bank and the ground hides its own
edge). The hollows are the plan masks' puddle cells (low ground: lowness 0.55 or more, which is also where the growth step keeps plants out and the wetness layer darkens)
and the wheel ruts of the roads (a rut holds water by its nature; the water then lies only where the rut's bottom is below the level of its stretch).
A long hollow (a rut) is cut into stretches of about 1.5 m and each stretch fills to a share of its own depth (place_wear.puddle_fill_share_damp, _wet, varied from
stretch to stretch), so water lies in the low parts only; only a share of the stretches hold water (place_wear.puddle_keep_share), chosen by a slow noise so wet
stretches come in short runs with dry ground between (a first try kept stretches at random and the ruts read as two long blue rails); each pool's water draws back
toward its own ends, so a pool is a lens or a rounded patch, not a box; only where a view camera can see it, and the whole is capped
(place_wear.puddle_area_max_square_metres, the nearest first). A dry place gets none. The sheet is one object, "PK puddles", with the role never.puddle: it is not
a water role, so the renderer rule is not changed by a few puddles. Running it twice makes the same again. It needs Blender (bpy) and numpy.
A concrete example: make_puddles(settings) on a damp road with ruts 10 cm deep lays thin strips of water in the bottoms of the ruts, about 3 cm deep at their deepest.
"""
import math

import numpy as np

import bpy

from .. import house_numbers, names
from ..wear import masks
from . import scatter, sites

OBJECT_NAME = 'PK puddles'
MATERIAL_NAME = 'PK puddle water'
SHEET_CELL_METRES = 0.05
TILE_METRES = 1.5              # a hollow longer than this fills stretch by stretch (a rut is never full end to end)
NOISE_METRES = 5.0             # the wavelength of the slow noise that picks which stretches hold water (wet runs and dry gaps of about half this)
FILL_SPREAD = (0.6, 1.4)       # each pool's fill share is the house number times a draw from this range (some pools shallow, some full), never above 0.9
ENDS_START = 0.55              # past this share of a pool's half-length the water draws back toward its ends (a lens, not a box)


def remove_old():
    removed = 0
    for obj in list(bpy.data.objects):
        if obj.get(scatter.PUDDLE_KEY) and obj.get(names.MADE):
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
            removed += 1
    return removed


def water_material():
    """Dark, nearly mirror-smooth water with a faint ripple: the kit's own still-water normal map (the surface water_still of data/surfaces.json) at a low strength,
    on UVs in metres, so a puddle shows the sky and the things round it, slightly broken, and never as a flat grey card."""
    from .. import run_record, settings_file
    from ..surfaces import materials as surface_materials, normals
    material = bpy.data.materials.get(MATERIAL_NAME) or bpy.data.materials.new(MATERIAL_NAME)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    principled.inputs['Base Color'].default_value = (0.022, 0.025, 0.024, 1.0)
    principled.inputs['Roughness'].default_value = 0.04
    principled.inputs['IOR'].default_value = 1.33
    spec = settings_file.surface('water_still')
    size = int(run_record.read().get('map_size_pixels') or house_numbers.value('place_surfaces.map_size_pixels'))
    normal_image, _, _, _ = surface_materials.make_maps('water_still', spec, size)
    tile = float(settings_file.number(spec['tile_metres']))
    normals.add_normal_map_nodes(material, normal_image, 'UVMap', strength=0.15, scale=(1.0 / tile, 1.0 / tile, 1.0), principled=principled)
    material[names.MADE] = 1
    return material


def blobs(mask):
    """The connected pieces (four neighbours) of a boolean grid: a list of (rows, cols) arrays, biggest first. Plain numpy and a queue: no SciPy."""
    rows, cols = mask.shape
    label = np.full(mask.shape, -1, dtype=np.int64)
    found = []
    for start_r, start_c in zip(*np.nonzero(mask)):
        if label[start_r, start_c] >= 0:
            continue
        index = len(found)
        stack = [(start_r, start_c)]
        label[start_r, start_c] = index
        members = []
        while stack:
            r, c = stack.pop()
            members.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and mask[nr, nc] and label[nr, nc] < 0:
                    label[nr, nc] = index
                    stack.append((nr, nc))
        found.append(np.array(members, dtype=np.int64))
    found.sort(key=len, reverse=True)
    return [(m[:, 0], m[:, 1]) for m in found]


def tiles(pieces, tile_cells):
    """Splits each hollow into pieces at most tile_cells across: a long rut does not fill end to end; each stretch of it fills its own lowest part."""
    result = []
    for rows, cols in pieces:
        keys = (rows // tile_cells) * 100003 + (cols // tile_cells)
        for key in np.unique(keys):
            chosen = keys == key
            result.append((rows[chosen], cols[chosen]))
    return result


def ring_cells(rows, cols, plan, width=2):
    """The (x, y) of the plan cells in a ring round a hollow (up to `width` cells out, not in it): its rim, whose height says how deep the hollow is."""
    inside = set(zip(rows.tolist(), cols.tolist()))
    ring = set()
    for r, c in inside:
        for dr in range(-width, width + 1):
            for dc in range(-width, width + 1):
                key = (r + dr, c + dc)
                if key not in inside and 0 <= key[0] < plan.shape[0] and 0 <= key[1] < plan.shape[1]:
                    ring.add(key)
    if not ring:
        return np.zeros(0), np.zeros(0)
    ring = np.array(sorted(ring))
    return plan.x0 + (ring[:, 1] + 0.5) * plan.cell, plan.y0 + (ring[:, 0] + 0.5) * plan.cell


def slow_noise(xs, ys, seed, wavelength=NOISE_METRES):
    """A smooth noise of position (three waves at random angles and phases, from the seed), about -1 to 1: neighbouring stretches get nearly the same value, so the
    stretches chosen by it come in runs."""
    rng = np.random.default_rng(seed)
    xs, ys = np.asarray(xs, dtype=np.float64), np.asarray(ys, dtype=np.float64)
    total = np.zeros_like(xs)
    for _ in range(3):
        angle, phase = rng.uniform(0, math.pi), rng.uniform(0, 2 * math.pi)
        length = wavelength * rng.uniform(0.7, 1.3)
        total += np.sin((xs * math.cos(angle) + ys * math.sin(angle)) * 2 * math.pi / length + phase)
    return total / 3.0


def keep_runs(centres, keep_share, seed):
    """Which stretches hold water: the keep_share of them where the slow noise is highest (so wet stretches come in short runs with dry ones between)."""
    if not len(centres):
        return np.zeros(0, dtype=bool)
    values = slow_noise(centres[:, 0], centres[:, 1], seed)
    count = int(round(keep_share * len(values)))
    keep = np.zeros(len(values), dtype=bool)
    if count:
        keep[np.argsort(-values)[:count]] = True
    return keep


def draw_back(px, py, cell_x, cell_y, cell):
    """For points (px, py) round one pool: 0 in its middle, rising to 1 and past at its ends, along the pool's own long and short axes (its cells' spread), so the
    water draws back toward the ends and a pool in a rut is a lens, not a box."""
    centre_x, centre_y = float(cell_x.mean()), float(cell_y.mean())
    dx, dy = cell_x - centre_x, cell_y - centre_y
    if len(cell_x) > 2:
        values, vectors = np.linalg.eigh(np.cov(np.stack([dx, dy])))
        axes = vectors.T
    else:
        axes = np.eye(2)
    reach = []
    for axis in axes:
        along = dx * axis[0] + dy * axis[1]
        reach.append(max(float(np.abs(along).max()) + cell, cell))
    u = ((px - centre_x) * axes[0][0] + (py - centre_y) * axes[0][1]) / reach[0]
    v = ((px - centre_x) * axes[1][0] + (py - centre_y) * axes[1][1]) / reach[1]
    return np.sqrt(u * u + v * v)


def water_level(heights, fill_share, rim=None):
    """The water's level in one hollow: its lowest ground plus a share of its depth, the depth being from the lowest ground to the rim round it (or, with no rim, to the
    90th percentile of the ground it covers)."""
    heights = np.asarray(heights, dtype=np.float64)
    low = float(heights.min())
    top = float(rim) if rim is not None else float(np.percentile(heights, 90))
    return low + fill_share * max(top - low, 0.0)


def make_puddles(settings, plan=None):
    """Lays the puddles (see the note at the top). Returns {'summary', 'puddles', 'area_m2', 'objects'}."""
    removed = remove_old()
    state = settings.state
    if state not in ('damp', 'wet'):
        return {'summary': f'the place is {state}: no standing water', 'puddles': 0, 'area_m2': 0.0, 'objects': [], 'removed': removed}
    plan = plan or masks.load_plan_masks()
    if plan is None:
        return {'summary': 'no plan masks yet: no puddles', 'puddles': 0, 'area_m2': 0.0, 'objects': [], 'removed': removed}
    wet = (sites.grid(plan.grids, 'above_water') < 0.5) | (sites.grid(plan.grids, 'track') >= 0.5)      # the low ground, and every wheel rut (a rut holds water by its nature)
    cameras = scatter.view_cameras()
    weight = sites.seen_weight(plan.shape, plan.x0, plan.y0, plan.cell, cameras, house_numbers.value('place_wear.scatter_full_metres'), house_numbers.value('place_wear.scatter_reach_metres'))
    wet &= weight > 0.05
    if not wet.any():
        return {'summary': 'no hollow holds water where a view can see it', 'puddles': 0, 'area_m2': 0.0, 'objects': [], 'removed': removed}
    from .. import scene_read
    ground = [o for o in scene_read.mesh_objects(only_visible=True) if (o.get(names.ROLE) or '').startswith('ground.') and not scene_read.is_scatter(o)]
    tree, top = scatter.ground_tree(ground)
    if tree is None:
        return {'summary': 'no ground faces: no puddles', 'puddles': 0, 'area_m2': 0.0, 'objects': [], 'removed': removed}
    fill = float(house_numbers.value('place_wear.puddle_fill_share_wet' if state == 'wet' else 'place_wear.puddle_fill_share_damp'))
    area_cap = float(house_numbers.value('place_wear.puddle_area_max_square_metres'))
    pieces = tiles(blobs(wet), max(1, int(round(TILE_METRES / plan.cell))))
    piece_centres = np.array([[plan.x0 + (cols.mean() + 0.5) * plan.cell, plan.y0 + (rows.mean() + 0.5) * plan.cell] for rows, cols in pieces]).reshape(-1, 2)
    keep = keep_runs(piece_centres, float(house_numbers.value('place_wear.puddle_keep_share')), int(settings.seed) * 13 + 5)
    pieces = [piece for piece, kept in zip(pieces, keep) if kept]
    fills = np.minimum(fill * np.random.default_rng(int(settings.seed) * 13 + 6).uniform(*FILL_SPREAD, size=len(pieces)), 0.9)
    centres = []
    for rows, cols in pieces:
        x = plan.x0 + (cols.mean() + 0.5) * plan.cell
        y = plan.y0 + (rows.mean() + 0.5) * plan.cell
        nearest = min((math.hypot(x - cx, y - cy) for cx, cy in cameras), default=0.0)
        centres.append(nearest)
    order = np.argsort(centres)
    vertices, faces, area, count = [], [], 0.0, 0
    step = SHEET_CELL_METRES
    for index in order:
        rows, cols = pieces[index]
        cell_x = plan.x0 + (cols + 0.5) * plan.cell
        cell_y = plan.y0 + (rows + 0.5) * plan.cell
        points, found = scatter.drop_to_ground(tree, top, np.stack([cell_x, cell_y], axis=1))
        if found.sum() < 1:
            continue
        ring_x, ring_y = ring_cells(rows, cols, plan)
        rim_points, rim_found = scatter.drop_to_ground(tree, top, np.stack([ring_x, ring_y], axis=1)) if len(ring_x) else (np.zeros((0, 3)), np.zeros(0, dtype=bool))
        rim = float(np.median(rim_points[rim_found][:, 2])) if rim_found.any() else None
        level = water_level(points[found][:, 2], float(fills[index]), rim)
        depth = max(level - float(points[found][:, 2].min()), 1e-4)
        # a fine sheet over the hollow and one plan cell round it: a little square is kept where the ground under it lies below the water, and one more ring of squares
        # runs under the bank, so the ground hides the sheet's edge and the shore is where the level meets the ground
        x0, x1 = cell_x.min() - plan.cell, cell_x.max() + plan.cell
        y0, y1 = cell_y.min() - plan.cell, cell_y.max() + plan.cell
        nx, ny = max(1, int(math.ceil((x1 - x0) / step))), max(1, int(math.ceil((y1 - y0) / step)))
        if nx * ny > 400000:
            continue
        gx, gy = np.meshgrid(x0 + (np.arange(nx) + 0.5) * step, y0 + (np.arange(ny) + 0.5) * step)
        ground_points, ground_found = scatter.drop_to_ground(tree, top, np.stack([gx.ravel(), gy.ravel()], axis=1))
        ends = draw_back(gx.ravel(), gy.ravel(), cell_x, cell_y, plan.cell)
        lift = depth * 1.5 * np.clip((ends - ENDS_START) / (1.0 - ENDS_START), 0.0, None) ** 1.5      # the ground seems to rise toward the pool's ends
        under = (ground_found & (ground_points[:, 2] + lift < level)).reshape(ny, nx)
        if not under.any():
            continue
        grown = under.copy()
        grown[1:, :] |= under[:-1, :]
        grown[:-1, :] |= under[1:, :]
        grown[:, 1:] |= under[:, :-1]
        grown[:, :-1] |= under[:, 1:]
        piece_area = float(under.sum() * step * step)
        if area + piece_area > area_cap:
            break
        area += piece_area
        count += 1
        corner_index = {}
        for r, c in zip(*np.nonzero(grown)):
            quad = []
            for dr, dc in ((0, 0), (0, 1), (1, 1), (1, 0)):
                key = (r + dr, c + dc)
                if key not in corner_index:
                    corner_index[key] = len(vertices)
                    vertices.append((x0 + (c + dc) * step, y0 + (r + dr) * step, level))
                quad.append(corner_index[key])
            faces.append(tuple(quad))
    if not faces:
        return {'summary': 'the hollows hold no water deep enough to show', 'puddles': 0, 'area_m2': 0.0, 'objects': [], 'removed': removed}
    mesh = bpy.data.meshes.new(OBJECT_NAME)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(water_material())
    obj = bpy.data.objects.new(OBJECT_NAME, mesh)
    scatter.made_collection().objects.link(obj)
    from ..surfaces import uvs
    uvs.write_uvs(obj, 'planar')
    obj[names.MADE] = 1
    obj[names.ROLE] = 'never.puddle'
    obj[scatter.PUDDLE_KEY] = 1
    obj['pk_puddle_count'] = count
    obj['pk_puddle_area'] = round(area, 3)
    obj.visible_shadow = False
    return {'summary': f'{count} puddle(s), {area:.1f} square metres of standing water in hollows and ruts ({state}: each filled to about {fill:.0%} of its depth)',
            'puddles': count, 'area_m2': round(area, 3), 'objects': [obj.name], 'removed': removed}
