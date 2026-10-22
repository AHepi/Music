"""What this does: makes the PLAN MASKS: twelve small "where-pictures" of the ground plan that say, for every spot of the place, how low it lies
(where water gathers), where the crown of a lane is, how much feet and wheels trample it, where nothing may grow or lie, how far it is from a wall,
from a prop, from litter, how sheltered and how shady it is, how damp, whether it is above water, and where the wheel tracks run. Materials look
them up by world x and y; the scatter uses them for exact keep-out gates; the audit counts against them. They are made with numpy only: the ground
and the objects are painted into grids from above (plan2d.py), then combined. This is the lighter route of decision D4 of the 1.4.0 design (the
proven weathering masks needed OpenCV and 25 to 80 seconds a scene); it is judged by the tests (isolation, dial zero, keep-out counts) and the time
is written into the audit.
The twelve masks, with the picture (a, b or c) and channel that holds each (8-bit, so value/255):
  a: lowness, crown, footfall, keepclear     b: wall_dist, prop_dist, sheltered, shade     c: dampness, above_water, litter_dist, track
Distances are stored as a share of a longest distance (wall_dist and prop_dist 4 m, litter_dist 1 m). above_water is 1 on dry ground and 0 in a puddle.
Before the plan masks exist, every question about where things may go answers "anywhere" (False for keep_clear_at).
It needs Blender (bpy) and numpy. A concrete example: after build_plan_masks(...), masks.sample('footfall', [[x, y, 0]]) is 1.0 on a wheel track.
"""
import re
import time

import numpy as np

import bpy

from .. import house_numbers, names, parts, plan2d, roles as roles_module, scene_read, settings_file

PICTURES = ('a', 'b', 'c')
CHANNELS = {
    'lowness': ('a', 0), 'crown': ('a', 1), 'footfall': ('a', 2), 'keepclear': ('a', 3),
    'wall_dist': ('b', 0), 'prop_dist': ('b', 1), 'sheltered': ('b', 2), 'shade': ('b', 3),
    'dampness': ('c', 0), 'above_water': ('c', 1), 'litter_dist': ('c', 2), 'track': ('c', 3),
}
DISTANCE_SCALE = {'wall_dist': 4.0, 'prop_dist': 4.0, 'litter_dist': 1.0}       # metres a full value stands for
LOWNESS_WINDOW_METRES = 1.5
LOWNESS_FULL_METRES = 0.15
PUDDLE_LOWNESS = 0.55
SOLID_MIN_HEIGHT = 0.3
ROOF_MIN_CLEARANCE = 0.8
SUN_AZIMUTH_DEGREES = 135.0
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
    ground, walls, props, roofs, doors_boxes = [], [], [], [], []
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

    ground_top = plan2d.fill_nan(raster(ground, 'max'), 0.0)
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
    shadow = plan2d.shadow_map(above, cell, SUN_AZIMUTH_DEGREES, SUN_ELEVATION_DEGREES)
    shade = np.clip(np.maximum(0.7 * sheltered, 0.9 * plan2d.box_blur(shadow, 0.3 / cell)), 0.0, 1.0)
    foot_of_wall = 1.0 - plan2d.smoothstep(0.0, 0.6, wall_dist)
    dampness = np.clip(0.5 * lowness + 0.4 * shade + 0.2 * foot_of_wall, 0.0, 1.0)
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
        wheels = np.abs(centre_offset - gauge / 2.0) <= rut_width / 2.0
        centre = centre_offset <= max(CENTRE_STRIP_HALF_WIDTH, gauge / 2.0 - rut_width)
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

    grids = {'lowness': quantise(lowness), 'crown': quantise(crown), 'footfall': quantise(footfall), 'keepclear': quantise(keepclear),
             'wall_dist': quantise(wall_dist / DISTANCE_SCALE['wall_dist']), 'prop_dist': quantise(prop_dist / DISTANCE_SCALE['prop_dist']),
             'sheltered': quantise(sheltered), 'shade': quantise(shade), 'dampness': quantise(dampness), 'above_water': quantise(np.where(puddle, 0.0, 1.0)),
             'litter_dist': quantise(np.ones(shape)), 'track': quantise(track)}
    masks = PlanMasks(x0, y0, cell, grids)
    record = {'cell_metres': cell, 'cells': [cols, rows], 'seconds': round(time.time() - started, 2), 'source': 'part_only' if only_owner else 'whole_scene',
              'bounds': [x0, y0, x0 + cols * cell, y0 + rows * cell]}
    return masks, record


# ---------------------------------------------------------------- in the Blender file
def write_plan_images(masks):
    """Puts the three pictures into Blender as packed Non-Color images with their bounds written on them. Returns the images."""
    from ..surfaces import normals
    images = []
    for which in PICTURES:
        array = masks.picture(which).astype(np.float32) / 255.0                 # rows from y0 up: Blender's own order
        name = names.plan_image_name(which)
        old = bpy.data.images.get(name)
        if old is not None:
            bpy.data.images.remove(old)
        rows, cols = array.shape[:2]
        image = bpy.data.images.new(name, cols, rows, alpha=True, float_buffer=False)
        image.colorspace_settings.name = 'Non-Color'
        image.pixels.foreach_set(array.ravel())
        image.update()
        image['pk_made'] = 1
        image['pk_bounds'] = list(masks.bounds)
        image['pk_cell'] = masks.cell
        normals.pack(image)
        images.append(image)
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
