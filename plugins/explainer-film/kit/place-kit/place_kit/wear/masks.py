"""What this does: makes the PLAN MASKS: twelve small "where-pictures" of the ground plan that say, for every spot of the place, how low it lies
(where water gathers), where the crown of a road is, how much feet and wheels trample it, where nothing may grow or lie, how far it is from a wall,
from a prop, from litter, how sheltered and how shady it is, how damp (low ground, shade, the foot of a wall and the margin of any water), whether it is above water, and where the wheel tracks run. Materials look
them up by world x and y; the scatter uses them for exact keep-out gates; the audit counts against them. They are made with numpy only: the ground
and the objects are painted into grids from above (plan2d.py), then combined. This is the lighter route of decision D4 of the 1.4.0 design (the
proven weathering masks needed OpenCV and 25 to 80 seconds a scene); it is judged by the tests (isolation, dial zero, keep-out counts) and the time
is written into the audit.
The masks, with the picture (a to e) and channel that holds each (8-bit, so value/255):
  a: lowness, crown, footfall, keepclear     b: wall_dist, prop_dist, sheltered, shade     c: dampness, above_water, litter_dist, track
  d: verge_dist (how far to a road's edge, a grass strip between ruts, or the line where two different ground surfaces meet), joint_dist (how far to a joint
     between two pieces of the same ground surface: separate stones or boards), seam_blend (how much of the OTHER ground surface lies within a metre), grows (1 where
     the top ground is one that grows plants and litter)
  e: seam_r, seam_g, seam_b (the colour of that other ground surface), unpaved (1 where the top ground is unpaved: earth, mud, gravel, grass, sand: stones lie there)
  f: centre_strip (1 on the grass strip between the two ruts of a road whose settings say "centre_grass"), three spare channels (only the growth step and the audit read f)
Distances are stored as a share of a longest distance (wall_dist and prop_dist 4 m, litter_dist 1 m, verge_dist 2 m, joint_dist 1 m). above_water is 1 on dry ground
and 0 in a puddle. The growth step finds its sites with d (weeds along road edges and verges, moss along joints); the wear chain blends two ground surfaces into
each other across their seam with d and e, so grass never meets earth at a ruled line.
Before the plan masks exist, every question about where things may go answers "anywhere" (False for keep_clear_at).
The shade (and so the dampness, moss, soot and fade that follow it) is worked out for the scene's own sun lamp when there is exactly one, else
for a sun at 135 degrees compass and 45 degrees up (light.scene_sun_direction); the record and the audit say which was used, so add your sun
before finish. It needs Blender (bpy) and numpy. A concrete example: after build_plan_masks(...), masks.sample('footfall', [[x, y, 0]]) is 1.0 on a wheel track.
"""
import re
import time

import numpy as np

import bpy

from .. import house_numbers, names, parts, plan2d, roles as roles_module, scene_read, settings_file

PICTURES = ('a', 'b', 'c', 'd', 'e', 'f')
CHANNELS = {
    'lowness': ('a', 0), 'crown': ('a', 1), 'footfall': ('a', 2), 'keepclear': ('a', 3),
    'wall_dist': ('b', 0), 'prop_dist': ('b', 1), 'sheltered': ('b', 2), 'shade': ('b', 3),
    'dampness': ('c', 0), 'above_water': ('c', 1), 'litter_dist': ('c', 2), 'track': ('c', 3),
    'verge_dist': ('d', 0), 'joint_dist': ('d', 1), 'seam_blend': ('d', 2), 'grows': ('d', 3),
    'seam_r': ('e', 0), 'seam_g': ('e', 1), 'seam_b': ('e', 2), 'unpaved': ('e', 3),
    'centre_strip': ('f', 0), 'f_spare_g': ('f', 1), 'f_spare_b': ('f', 2), 'f_spare_a': ('f', 3),
}
DISTANCE_SCALE = {'wall_dist': 4.0, 'prop_dist': 4.0, 'litter_dist': 1.0, 'verge_dist': 2.0, 'joint_dist': 1.0}       # metres a full value stands for
SEAM_BLEND_METRES = 1.0          # two ground surfaces blend into each other over about this far on each side of their seam
LOWNESS_WINDOW_METRES = 1.5
LOWNESS_FULL_METRES = 0.15
PUDDLE_LOWNESS = 0.55
SOLID_MIN_HEIGHT = 0.3
ROOF_MIN_CLEARANCE = 0.8
SUN_AZIMUTH_DEGREES = 135.0        # the fallback only: the shade reads the scene's sun lamp when there is exactly one (light.scene_sun_direction)
SUN_ELEVATION_DEGREES = 45.0
WHEEL_TRACK_WIDTH = 0.18
CENTRE_STRIP_HALF_WIDTH = 0.3


class PlanMasks:
    """The twelve masks as 8-bit grids, with the bounds and cell size that tie a grid cell to world x and y."""

    def __init__(self, x0, y0, cell, grids):
        self.x0, self.y0, self.cell = float(x0), float(y0), float(cell)
        self.grids = grids                      # name -> uint8 (rows, cols)
        self.shape = next(iter(grids.values())).shape

    @property
    def bounds(self):
        rows, cols = self.shape
        return (self.x0, self.y0, self.x0 + cols * self.cell, self.y0 + rows * self.cell)

    def sample(self, name, points):
        """The mask value (0..1; for distance masks the share of their longest distance) at world points (n, 2 or 3), nearest cell, edges clamped."""
        p = np.asarray(points, dtype=np.float64).reshape(-1, np.asarray(points).shape[-1])
        cols = np.clip(((p[:, 0] - self.x0) / self.cell).astype(int), 0, self.shape[1] - 1)
        rows = np.clip(((p[:, 1] - self.y0) / self.cell).astype(int), 0, self.shape[0] - 1)
        return self.grids[name][rows, cols].astype(np.float64) / 255.0

    def sample_metres(self, name, points):
        return self.sample(name, points) * DISTANCE_SCALE[name]

    def keep_clear_at(self, x, y):
        gate = house_numbers.value('place_wear.exact_zero_gate_keepclear')
        footfall_gate = house_numbers.value('place_wear.exact_zero_gate_footfall')
        point = [[x, y]]
        return bool(self.sample('keepclear', point)[0] >= gate or self.sample('footfall', point)[0] >= footfall_gate)

    def picture(self, which):
        """The RGBA picture a, b or c as uint8 (rows, cols, 4), rows from y0 up (Blender's own order)."""
        out = np.zeros(self.shape + (4,), dtype=np.uint8)
        for name, (picture, channel) in CHANNELS.items():
            if picture == which:
                out[..., channel] = self.grids[name]
        return out


def quantise(grid):
    return np.clip(np.rint(np.asarray(grid, dtype=np.float64) * 255.0), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- shapes
def road_by_name(settings, name):
    for road in settings.roads:
        if road.get('name') == name:
            return road
    return None


def stamp_shape(shape, settings, x0, y0, cell, shape_grid, object_boxes):
    """Paints one footfall or keep-clear shape of the settings into a float grid (values 0..1, max-combined)."""
    kind = shape.get('shape')
    value = float(shape.get('value', 1.0))
    rows, cols = shape_grid.shape
    if kind == 'rect':
        c0, c1 = int((shape['x0'] - x0) / cell), int((shape['x1'] - x0) / cell)
        r0, r1 = int((shape['y0'] - y0) / cell), int((shape['y1'] - y0) / cell)
        window = shape_grid[max(r0, 0):max(r1 + 1, 0), max(c0, 0):max(c1 + 1, 0)]
        if window.size:
            window[:] = np.maximum(window, value)
    elif kind in ('polyline', 'band_along', 'lines_along'):
        if kind == 'polyline':
            line, offsets, width = shape.get('points') or shape.get('polyline') or [], [0.0], float(shape.get('width', 1.0))
        else:
            road = road_by_name(settings, shape.get('road'))
            if road is None:
                return
            line = road['polyline']
            offsets = [float(shape.get('offset', 0.0))] if kind == 'band_along' else [float(o) for o in shape.get('offsets', [])]
            width = float(shape.get('width', 0.5))
        if len(line) < 2:
            return
        distance, sign, _ = plan2d.polyline_field(x0, y0, cell, shape_grid.shape, line, max(abs(o) for o in offsets) + width)
        for offset in offsets:
            band = np.abs(sign * distance - offset) <= width / 2.0
            shape_grid[band] = np.maximum(shape_grid[band], value)
    elif kind in ('around_role', 'auto_door_strip'):
        pattern = shape.get('role') or ('timber.door' if kind == 'auto_door_strip' else '*')
        regex = '^' + re.escape(pattern).replace('\\*', '.*') + '$'
        depth = float(shape.get('depth', shape.get('radius', 1.0)))
        width_extra = float(shape.get('width', 0.0))
        for role, box in object_boxes:
            if not re.match(regex, role or ''):
                continue
            (bx0, by0), (bx1, by1) = box
            if kind == 'around_role':
                lo = (bx0 - depth, by0 - depth)
                hi = (bx1 + depth, by1 + depth)
            else:
                # a strip in front of and behind the door, along its thin side
                if (bx1 - bx0) >= (by1 - by0):          # the door's face runs along x: people stand at +y and -y
                    lo, hi = (bx0 - width_extra / 2 + 0.0, by0 - depth), (bx1 + width_extra / 2, by1 + depth)
                else:
                    lo, hi = (bx0 - depth, by0 - width_extra / 2), (bx1 + depth, by1 + width_extra / 2)
            c0, c1 = int((lo[0] - x0) / cell), int((hi[0] - x0) / cell)
            r0, r1 = int((lo[1] - y0) / cell), int((hi[1] - y0) / cell)
            window = shape_grid[max(r0, 0):max(r1 + 1, 0), max(c0, 0):max(c1 + 1, 0)]
            if window.size:
                window[:] = np.maximum(window, value)


# ---------------------------------------------------------------- building the masks
def plan_extent(objects):
    low = np.array([np.inf, np.inf])
    high = np.array([-np.inf, -np.inf])
    for obj in objects:
        a, b = scene_read.world_bounds(obj)
        low = np.minimum(low, a[:2])
        high = np.maximum(high, b[:2])
    return low, high


def build_plan_masks(settings, quick=False, cell=None, only_owner=None):
    """Makes the twelve masks from the open scene and the settings. Returns (PlanMasks, record) where the record has the cell size, the grid size,
    the seconds taken and where the masks came from. cell: metres (default from the house numbers; larger when the place is large)."""
    started = time.time()
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    objects = scene_read.mesh_objects(only_visible=True)
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, table)['by_object']
    ground, walls, props, roofs, doors_boxes, waters = [], [], [], [], [], []
    for obj in objects:
        role = tagged[obj.name]['role'] or ''
        if scene_read.is_scatter(obj) or roles_module.is_never(role):
            continue
        if only_owner is not None and obj.get(names.OWNER) != only_owner and not role.startswith('ground.'):
            continue
        klass = roles_module.role_class(role)
        if klass == 'ground':
            ground.append(obj)
        elif klass == 'roof':
            roofs.append(obj)
        elif klass == 'water':
            waters.append(obj)                 # water is not a solid prop (a sea box is not a 2.4 m tall wall that shades the seabed); it wets what lies beside it (below)
        elif klass in ('wall', 'stone'):
            walls.append(obj)
        else:
            props.append(obj)
    extent_objects = ground or (walls + props + roofs)
    if not extent_objects:
        extent_objects = objects
    low, high = plan_extent(extent_objects)
    pad = 1.0
    low, high = low - pad, high + pad
    base_cell = house_numbers.value('place_wear.plan_mask_cell_metres_quick' if quick else 'place_wear.plan_mask_cell_metres')
    across_max = house_numbers.value('place_wear.plan_mask_cells_across_max')
    cell = float(cell or max(base_cell, float(max(high - low)) / across_max))
    cols = max(8, int(np.ceil((high[0] - low[0]) / cell)))
    rows = max(8, int(np.ceil((high[1] - low[1]) / cell)))
    shape = (rows, cols)
    x0, y0 = float(low[0]), float(low[1])

    def raster(objs, mode):
        grid = np.full(shape, np.nan)
        for obj in objs:
            vertices, triangles = parts.world_triangles(obj)
            if len(triangles) == 0:
                continue
            painted = plan2d.rasterize_triangles(vertices, triangles, x0, y0, cell, shape, mode)
            both = ~np.isnan(painted)
            if mode == 'max':
                grid = np.where(both, np.where(np.isnan(grid), painted, np.maximum(grid, painted)), grid)
            else:
                grid = np.where(both, np.where(np.isnan(grid), painted, np.minimum(grid, painted)), grid)
        return grid

    ground_top, ground_id = np.full(shape, np.nan), np.full(shape, -1, dtype=np.int64)
    for index, obj in enumerate(ground):                         # the top ground surface in every cell, and which object it is
        vertices, triangles = parts.world_triangles(obj)
        if len(triangles) == 0:
            continue
        painted = plan2d.rasterize_triangles(vertices, triangles, x0, y0, cell, shape, 'max')
        better = ~np.isnan(painted) & (np.isnan(ground_top) | (painted > ground_top))
        ground_top[better] = painted[better]
        ground_id[better] = index
    ground_top = plan2d.fill_nan(ground_top, 0.0)
    wall_top = raster(walls, 'max')
    prop_top = raster(props, 'max')
    roof_top = raster(roofs, 'max')
    roof_bottom = raster(roofs, 'min')
    above = np.nan_to_num(np.fmax.reduce([wall_top, prop_top, roof_top]) - ground_top, nan=0.0)
    above = np.maximum(above, 0.0)
    wall_solid = np.nan_to_num(wall_top - ground_top, nan=0.0) > SOLID_MIN_HEIGHT
    prop_solid = np.nan_to_num(prop_top - ground_top, nan=0.0) > SOLID_MIN_HEIGHT
    roofed = (~np.isnan(roof_bottom)) & ((roof_bottom - ground_top) > ROOF_MIN_CLEARANCE)

    lowness = np.clip((plan2d.box_blur(ground_top, LOWNESS_WINDOW_METRES / cell) - ground_top) / LOWNESS_FULL_METRES, 0.0, 1.0)
    wall_dist = plan2d.distance_to_marked(wall_solid, cell, DISTANCE_SCALE['wall_dist'])
    prop_dist = plan2d.distance_to_marked(prop_solid, cell, DISTANCE_SCALE['prop_dist'])
    sheltered = np.clip(plan2d.box_blur(roofed.astype(np.float64), 0.5 / cell), 0.0, 1.0)
    from .. import light
    sun = light.scene_sun_direction()
    shadow = plan2d.shadow_map(above, cell, sun['compass_degrees'], sun['height_degrees'])
    shade = np.clip(np.maximum(0.7 * sheltered, 0.9 * plan2d.box_blur(shadow, 0.3 / cell)), 0.0, 1.0)
    foot_of_wall = 1.0 - plan2d.smoothstep(0.0, 0.6, wall_dist)
    # ground within 1.5 m of water, where the water stands above the ground, is wet: full at the waterline, fading to nothing 1.5 m away (a quay edge, a bank, a wheel pit)
    water_top = raster(waters, 'max')
    water_here = np.nan_to_num(water_top - ground_top, nan=-1.0) > 0.0
    near_water = 1.0 - plan2d.smoothstep(0.0, 1.5, plan2d.distance_to_marked(water_here, cell, 3.0)) if water_here.any() else np.zeros(shape)
    dampness = np.clip(0.5 * lowness + 0.4 * shade + 0.2 * foot_of_wall + 0.6 * near_water, 0.0, 1.0)
    state_is_dry = (settings.state == 'dry')
    puddle = (lowness >= PUDDLE_LOWNESS) & (not state_is_dry)

    # ---- footfall, crown, keep-clear and wheel tracks from the roads and the shapes in the settings
    footfall = np.zeros(shape)
    crown = np.zeros(shape)
    keepclear = np.zeros(shape)
    track = np.zeros(shape)
    for road in settings.roads:
        width = float(road.get('width', 3.0))
        gauge = float(road.get('gauge', 1.3))
        rut_width = float(road.get('rut_width', WHEEL_TRACK_WIDTH))
        distance, sign, _ = plan2d.polyline_field(x0, y0, cell, shape, road['polyline'], width)
        centre_offset = np.abs(sign * distance)
        reach = 0.71 * cell                          # half the diagonal of a cell: a cell that the rut touches anywhere is blocked, so the gates are exact-zero on the whole nominal rut
        wheels = np.abs(centre_offset - gauge / 2.0) <= rut_width / 2.0 + reach
        centre = centre_offset <= max(CENTRE_STRIP_HALF_WIDTH, gauge / 2.0 - rut_width) + reach
        centre_grass = bool(road.get('centre_grass', False))
        track[wheels] = 1.0
        footfall[wheels] = 1.0
        footfall[centre & ~wheels] = np.maximum(footfall[centre & ~wheels], 0.45 if centre_grass else 0.8)
        if not centre_grass:
            crown[centre & ~wheels] = 1.0
        keepclear[wheels] = 1.0
    boxes = []
    for obj in objects:
        role = tagged[obj.name]['role'] or ''
        a, b = scene_read.world_bounds(obj)
        boxes.append((role, ((float(a[0]), float(a[1])), (float(b[0]), float(b[1])))))
    for shape_spec in settings.get('footfall') or []:
        stamp_shape(shape_spec, settings, x0, y0, cell, footfall, boxes)
    for shape_spec in settings.get('keep_clear') or []:
        stamp_shape(shape_spec, settings, x0, y0, cell, keepclear, boxes)
    keepclear = np.maximum(keepclear, (footfall >= house_numbers.value('place_wear.exact_zero_gate_footfall')).astype(np.float64))

    # ---- verges, joints and seams: where weeds gather along edges, and where two ground surfaces blend into each other
    surfaces_of = [ground_surface_key(obj) for obj in ground]
    verge_marked, joint_marked = ground_seams(ground_id, surfaces_of)
    centre_strip = np.zeros(shape, dtype=bool)
    for road in settings.roads:
        width = float(road.get('width', 3.0))
        distance, _, _ = plan2d.polyline_field(x0, y0, cell, shape, road['polyline'], width / 2.0 + 1.0)
        verge_marked |= np.abs(distance - width / 2.0) <= max(0.5 * cell, 0.05)
        if road.get('centre_grass'):
            gauge = float(road.get('gauge', 1.3))
            rut_width = float(road.get('rut_width', WHEEL_TRACK_WIDTH))
            centre_strip |= distance <= max(gauge / 2.0 - rut_width, 0.5 * cell)
    verge_dist = plan2d.distance_to_marked(verge_marked, cell, DISTANCE_SCALE['verge_dist'])
    joint_dist = plan2d.distance_to_marked(joint_marked, cell, DISTANCE_SCALE['joint_dist'])
    tones = [ground_tone(obj) for obj in ground]
    seam_blend, seam_tone = seam_blend_grids(ground_id, tones, SEAM_BLEND_METRES / cell)
    grows_of = np.array([ground_grows(obj, tagged[obj.name]['role'] or '', rules, table) for obj in ground] + [False], dtype=bool)
    unpaved_of = np.array([ground_unpaved(key) for key in surfaces_of] + [False], dtype=bool)
    grows = grows_of[np.where(ground_id >= 0, ground_id, len(ground))]
    unpaved = unpaved_of[np.where(ground_id >= 0, ground_id, len(ground))]

    grids = {'lowness': quantise(lowness), 'crown': quantise(crown), 'footfall': quantise(footfall), 'keepclear': quantise(keepclear),
             'wall_dist': quantise(wall_dist / DISTANCE_SCALE['wall_dist']), 'prop_dist': quantise(prop_dist / DISTANCE_SCALE['prop_dist']),
             'sheltered': quantise(sheltered), 'shade': quantise(shade), 'dampness': quantise(dampness), 'above_water': quantise(np.where(puddle, 0.0, 1.0)),
             'litter_dist': quantise(np.ones(shape)), 'track': quantise(track),
             'verge_dist': quantise(verge_dist / DISTANCE_SCALE['verge_dist']), 'joint_dist': quantise(joint_dist / DISTANCE_SCALE['joint_dist']),
             'seam_blend': quantise(seam_blend), 'grows': quantise(grows.astype(np.float64)),
             'seam_r': quantise(seam_tone[..., 0]), 'seam_g': quantise(seam_tone[..., 1]), 'seam_b': quantise(seam_tone[..., 2]), 'unpaved': quantise(unpaved.astype(np.float64)),
             'centre_strip': quantise((centre_strip & (track < 0.5)).astype(np.float64)), 'f_spare_g': quantise(np.zeros(shape)), 'f_spare_b': quantise(np.zeros(shape)),
             'f_spare_a': quantise(np.zeros(shape))}
    masks = PlanMasks(x0, y0, cell, grids)
    record = {'cell_metres': cell, 'cells': [cols, rows], 'seconds': round(time.time() - started, 2), 'source': 'part_only' if only_owner else 'whole_scene',
              'bounds': [x0, y0, x0 + cols * cell, y0 + rows * cell], 'sun': sun}
    return masks, record


# ---------------------------------------------------------------- verges, joints and seams between ground surfaces (plain numpy, tested without Blender)
def ground_seams(ground_id, surface_keys):
    """Two boolean grids from the grid of which ground object is on top in each cell: (verge, joint). A cell is on a VERGE when a neighbouring cell holds another ground
    object of a different surface (grass meeting earth); on a JOINT when the neighbour is another object of the same surface (two stones or boards of one paving).
    Cells with no ground (-1) and the outer edge of the ground are neither."""
    ids = np.asarray(ground_id)
    keys = np.array([str(k) for k in surface_keys] + ['(none)'], dtype=object)
    verge = np.zeros(ids.shape, dtype=bool)
    joint = np.zeros(ids.shape, dtype=bool)
    for axis in (0, 1):
        for step in (1, -1):
            other = np.roll(ids, step, axis=axis)
            valid = np.ones(ids.shape, dtype=bool)
            edge = [slice(None)] * 2
            edge[axis] = slice(0, 1) if step == 1 else slice(-1, None)
            valid[tuple(edge)] = False                                  # np.roll wraps round: the far row is not a neighbour
            different = valid & (ids >= 0) & (other >= 0) & (other != ids)
            same_surface = keys[np.where(ids >= 0, ids, len(keys) - 1)] == keys[np.where(other >= 0, other, len(keys) - 1)]
            verge |= different & ~same_surface
            joint |= different & same_surface
    return verge, joint


def seam_blend_grids(ground_id, tones, radius_cells):
    """(blend, tone): for every cell, how much of the OTHER ground surfaces lies within the radius (0 far from any seam, 0.5 on the seam itself, at most 0.5), and the
    mean colour of those other surfaces (linear RGB). A material mixes its own colour toward that tone by the blend, so on the seam both sides meet half way."""
    ids = np.asarray(ground_id)
    shape = ids.shape
    if not len(tones):
        return np.zeros(shape), np.zeros(shape + (3,))
    tone_array = np.asarray(tones, dtype=np.float64).reshape(-1, 3)
    total = np.zeros(shape + (3,))
    own_share = np.zeros(shape)
    coverage = np.zeros(shape)
    for index in range(len(tone_array)):
        share = plan2d.box_blur((ids == index).astype(np.float64), radius_cells)
        total += share[..., None] * tone_array[index][None, None, :]
        coverage += share
        own_share = np.where(ids == index, share, own_share)
    own_tone = np.where((ids >= 0)[..., None], tone_array[np.clip(ids, 0, None)], 0.0)
    other_share = np.clip(coverage - own_share, 0.0, None)
    other = np.where(other_share[..., None] > 1e-3, (total - own_share[..., None] * own_tone) / np.maximum(other_share, 1e-3)[..., None], own_tone)
    blend = np.where(ids >= 0, np.clip(other_share / np.maximum(coverage, 1e-6), 0.0, 0.5), 0.0)
    return blend, np.clip(other, 0.0, 1.0)


def ground_surface_key(obj):
    """Which surface a ground object wears (its first kit material's surface id, else the first material's name): ground objects of one surface meet at a joint, of two at a verge."""
    for slot in obj.material_slots:
        if slot.material is not None:
            return slot.material.get('pk_surface') or slot.material.name
    return obj.get(names.ROLE) or obj.name


def ground_grows(obj, role, rules, table):
    """True when this ground object grows plants and litter (its role requires or wants them and no off entry switches them off)."""
    req = roles_module.requirements(role, table, rules) if role else {'required': [], 'wanted': []}
    return ('plants' in set(req['required']) | set(req['wanted'])) and not roles_module.off_entries_for(role, 'plants', rules)


def ground_unpaved(surface_key):
    """True when the surface is unpaved (data/surfaces.json "unpaved": earth, mud, gravel, grass, sand): loose stones and pebbles lie on it."""
    try:
        return bool(settings_file.surface(surface_key).get('unpaved'))
    except (KeyError, ValueError, TypeError):
        return False


def ground_tone(obj):
    """The mean colour (linear RGB) of a ground object's surface: written on kit materials (pk_mean_colour), else the Principled colour, else a neutral earth."""
    for slot in obj.material_slots:
        material = slot.material
        if material is None:
            continue
        if material.get('pk_mean_colour'):
            return [float(v) for v in material['pk_mean_colour']][:3]
        if material.node_tree is not None:
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    return [float(v) for v in node.inputs['Base Color'].default_value[:3]]
    return [0.12, 0.1, 0.08]


# ---------------------------------------------------------------- in the Blender file
def write_plan_images(masks):
    """Puts the three pictures into Blender as packed Non-Color images with their bounds written on them. A picture of the same size is rewritten in place (so the Plan group
    that reads it keeps working); otherwise it is made again and the Plan group is rebuilt. Returns the images."""
    from ..surfaces import normals
    images, remade = [], False
    for which in PICTURES:
        array = masks.picture(which).astype(np.float32) / 255.0                 # rows from y0 up: Blender's own order
        name = names.plan_image_name(which)
        rows, cols = array.shape[:2]
        image = bpy.data.images.get(name)
        if image is not None and tuple(image.size) == (cols, rows):
            image.pixels.foreach_set(array.ravel())
            image.update()
        else:
            if image is not None:
                bpy.data.images.remove(image)
            image = bpy.data.images.new(name, cols, rows, alpha=True, float_buffer=False)
            image.colorspace_settings.name = 'Non-Color'
            image.alpha_mode = 'CHANNEL_PACKED'
            image.pixels.foreach_set(array.ravel())
            image.update()
            remade = True
        image['pk_made'] = 1
        image.use_fake_user = True          # picture f is read by the growth step and the audit only, never by a material: without a fake user Blender drops it on save
        image['pk_bounds'] = list(masks.bounds)
        image['pk_cell'] = masks.cell
        normals.pack(image)
        images.append(image)
    if remade and bpy.data.node_groups.get(names.PLAN_GROUP) is not None:
        from . import plan_group
        plan_group.build_plan_group()
    return images


def load_plan_masks():
    """The masks from the pictures in the open file, or None when the kit has not made them yet."""
    grids = {}
    first = None
    for which in PICTURES:
        image = bpy.data.images.get(names.plan_image_name(which))
        if image is None:
            return None
        first = first or image
        cols, rows = image.size
        flat = np.empty(cols * rows * image.channels, dtype=np.float32)
        image.pixels.foreach_get(flat)
        array = np.rint(flat.reshape(rows, cols, image.channels) * 255.0).astype(np.uint8)
        for name, (picture, channel) in CHANNELS.items():
            if picture == which:
                grids[name] = array[..., channel]
    bounds = list(first['pk_bounds'])
    return PlanMasks(bounds[0], bounds[1], float(first['pk_cell']), grids)


_loaded = {'masks': None}


def keep_clear_at(x, y):
    """True when the plan masks in the open file say nothing may be at (x, y); False when there are no masks."""
    if _loaded['masks'] is None:
        _loaded['masks'] = load_plan_masks()
    return _loaded['masks'].keep_clear_at(x, y) if _loaded['masks'] is not None else False


def forget_loaded():
    _loaded['masks'] = None


def stamp_litter(points):
    """After litter is scattered: updates the litter_dist channel (distance to the nearest litter piece) in the pictures. Returns the masks."""
    masks = load_plan_masks()
    if masks is None:
        return None
    marked = np.zeros(masks.shape, dtype=bool)
    p = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    if len(p):
        cols = np.clip(((p[:, 0] - masks.x0) / masks.cell).astype(int), 0, masks.shape[1] - 1)
        rows = np.clip(((p[:, 1] - masks.y0) / masks.cell).astype(int), 0, masks.shape[0] - 1)
        marked[rows, cols] = True
    distance = plan2d.distance_to_marked(marked, masks.cell, DISTANCE_SCALE['litter_dist'])
    masks.grids['litter_dist'] = quantise(distance / DISTANCE_SCALE['litter_dist'])
    write_plan_images(masks)
    forget_loaded()
    return masks
