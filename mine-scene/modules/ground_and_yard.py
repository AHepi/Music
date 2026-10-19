# What this does: builds the ground of the coal-mine yard and the clutter lying on it.
#   1. The terrain: one big mesh of wet, churned mud (the uploaded mud picture, with real bumps pushed out of its height map).
#      It is cut fine near the camera and coarse far away. It follows mc.ground_height() everywhere, then adds deep cart ruts,
#      lumpy mud, a few earth mounds, coal heaps and shallow hollows for the puddles. Right next to the buildings and the track
#      it is left exactly as mc.ground_height() says, so things that sit on that height sit cleanly (one exception: the floor
#      inside the engine house is dug 7 cm lower). Wet places (ruts, puddle edges) are darker and glossier, coal heaps are black.
#   2. The puddles: eight flat sheets of glossy dark-blue water lying in hollows and cart ruts (one object).
#   3. The yard clutter: about two thousand coal lumps and stones (one object), five heaps of coal, a leaning stack of timber props
#      at the far left, a low post-and-rail fence at the right, two barrels, a wooden handcart, a pile of railway sleepers and
#      a tall iron lamp post with a glowing lantern.
# How the assembler uses it:  import ground_and_yard;  ground_and_yard.build('Mine ground and yard')
#   and  ground_and_yard.ground_mesh_object()  hands back the terrain object (it is called GROUND_OBJECT_NAME).
#   ground_and_yard.lamp_light_position() says where the lantern is, if a real light should be placed there.
# Everything is placed in world metres, +X right, +Y away from the camera, +Z up (see LAYOUT in lib/mine_common.py).
import math
import os
import sys
import time

import bpy
import numpy as np

_LIBRARY_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
if _LIBRARY_FOLDER not in sys.path:
    sys.path.insert(0, _LIBRARY_FOLDER)
import mine_common as mc

# ====================================================================================================================
# Names and numbers you may want to change
# ====================================================================================================================
GROUND_OBJECT_NAME = 'Ground terrain'
PUDDLE_OBJECT_NAME = 'Ground puddles'
LUMPS_OBJECT_NAME = 'Yard coal and stones'
PROPS_OBJECT_NAME = 'Yard props (timber, fence, barrels, cart, lamp)'

TERRAIN_X_RANGE = (-45.0, 60.0)          # metres, west to east
TERRAIN_Y_RANGE = (-45.0, 90.0)          # metres, toward the camera to far behind the mine
FINE_X_RANGE = (-14.0, 9.0)              # the foreground yard where the mesh is finest
FINE_Y_RANGE = (-26.0, -5.0)
FINE_CELL = 0.12                         # metres: size of one mesh square in the fine part
CELL_GROWTH = 1.09                       # each square outside the fine part is this much bigger than the one before
LARGEST_CELL = 5.0
MUD_RELIEF_DEPTH = 0.05                  # metres of real bumps pushed out of the mud height picture (the default is 0.06)
TERRAIN_DICING_PIXELS = 2.0              # real displacement is cut to about this many screen pixels per facet (bigger = less memory and time)

WATER_ABOVE_LOWEST = 0.015               # a puddle sheet lies this far above the lowest ground it covers
HOLLOW_DEPTH = 0.04                      # the puddle bed is dug this far below the water sheet
LEVELLING = 0.85                         # how much round pools flatten the ground slope across themselves (0 = none, 1 = fully flat)
RUT_LEVELLING = 0.85                     # the same for puddles lying in a cart rut
LAMP_POSITION = (7.4, -1.0)              # foot of the iron lamp post
LAMP_HEIGHT = 4.4

# ====================================================================================================================
# Where things are (the plan). Changing a number here moves the thing; the ground reshapes itself around it.
# ====================================================================================================================
# Cart roads: each is a curve through these points (x, y); two wheel ruts run along it, 1.24 m apart.
CART_ROADS = {
    'A': [(-3.6, -27.5), (-3.8, -22.5), (-4.0, -18.0), (-4.7, -14.0), (-4.3, -10.4), (-3.9, -8.0)],
    'B': [(3.8, -26.0), (0.6, -22.0), (-1.4, -18.4), (-3.2, -15.2), (-4.6, -12.2)],
    'C': [(-14.5, -9.0), (-11.5, -10.3), (-8.8, -11.2), (-6.0, -10.8), (-4.2, -10.2)],
    'D': [(17.0, -9.0), (12.6, -10.2), (9.2, -9.4), (6.8, -7.6)],
    'E': [(-16.0, -19.8), (-12.0, -17.8), (-8.8, -15.4), (-6.0, -13.4), (-3.4, -12.6)],
}
RUT_GAUGE = 1.24                         # distance between the two wheel ruts of one road
RUT_HALF_WIDTH = 0.25                    # width of the trench (about 0.4 m across at half depth)
RUT_DEPTH = 0.15

# Earth mounds: (x, y, radius, height)
EARTH_MOUNDS = [(-17.0, -16.0, 3.2, 0.26), (12.0, -22.0, 3.0, 0.20), (15.0, -8.0, 2.4, 0.18)]

# Puddles. 'blob' = a rounded irregular pool; 'rut' = water lying in one wheel rut of a cart road between two y values.
PUDDLES = [
    {'name': 'front left pool', 'kind': 'blob', 'centre': (-8.7, -17.9), 'size': (1.8, 1.05), 'turn': 70, 'seed': 1},
    {'name': 'road E flooded', 'kind': 'rut', 'road': 'E', 'side': 1, 'y_range': (-16.3, -13.9), 'half_width': 0.36},
    {'name': 'road A flooded, middle', 'kind': 'rut', 'road': 'A', 'side': -1, 'y_range': (-13.0, -8.9), 'half_width': 0.38},
    {'name': 'middle pool', 'kind': 'blob', 'centre': (-0.8, -10.9), 'size': (1.8, 1.0), 'turn': 25, 'seed': 2},
    {'name': 'far left pool', 'kind': 'blob', 'centre': (-12.0, -6.6), 'size': (2.0, 1.1), 'turn': 60, 'seed': 3},
    {'name': 'back yard pool', 'kind': 'blob', 'centre': (5.8, -18.8), 'size': (2.6, 1.4), 'turn': 160, 'seed': 4},
    {'name': 'right yard pool', 'kind': 'blob', 'centre': (9.0, -6.3), 'size': (1.9, 0.95), 'turn': 20, 'seed': 5},
    {'name': 'road B flooded', 'kind': 'rut', 'road': 'B', 'side': 1, 'y_range': (-21.6, -18.4), 'half_width': 0.30},
]

# Coal heaps: (x, y, radius, height, number of lumps on top). The heap itself is part of the terrain, darkened with coal dust.
COAL_HEAPS = [(-17.5, -11.5, 2.3, 1.0, 330), (11.5, -12.0, 1.9, 0.85, 240), (15.8, -16.0, 1.5, 0.60, 150)]

TIMBER_RACK = {'x': -7.2, 'y_from': -6.0, 'y_to': -3.2, 'bar_height': 2.1}
BARREL_SPOTS = [(-5.3, -1.9), (-4.5, -2.4)]
HANDCART = {'x': -7.6, 'y': -9.0, 'yaw_degrees': 205}
SLEEPER_PILE = {'x': 5.9, 'y': -3.6}
FENCE_LINE = [(10.2, -3.9), (13.4, -3.4), (16.4, -1.6), (18.6, 1.6), (19.8, 5.4)]

# Building footprints the ground must leave alone: (x_min, x_max, y_min, y_max)
BUILDING_FOOTPRINTS = [
    (mc.LAYOUT['engine_house']['x_left'], mc.LAYOUT['engine_house']['x_right'],
     mc.LAYOUT['engine_house']['y_front'], mc.LAYOUT['engine_house']['y_back']),
    (-mc.LAYOUT['headframe']['base_half_x'], mc.LAYOUT['headframe']['base_half_x'],
     mc.LAYOUT['headframe']['centre_y'] - mc.LAYOUT['headframe']['base_half_y'],
     mc.LAYOUT['headframe']['centre_y'] + mc.LAYOUT['headframe']['base_half_y']),
    (mc.LAYOUT['chimney']['centre_x'] - mc.LAYOUT['chimney']['base_width'] / 2,
     mc.LAYOUT['chimney']['centre_x'] + mc.LAYOUT['chimney']['base_width'] / 2,
     mc.LAYOUT['chimney']['centre_y'] - mc.LAYOUT['chimney']['base_width'] / 2,
     mc.LAYOUT['chimney']['centre_y'] + mc.LAYOUT['chimney']['base_width'] / 2),
]

LAST_BUILD_INFO = {}


# ====================================================================================================================
# Small maths helpers
# ====================================================================================================================
def smooth_step(low, high, values):
    """Like mc.smoothstep but for whole arrays at once."""
    t = np.clip((np.asarray(values, dtype=float) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class SoftNoise:
    """Smooth random bumps (value noise). Call it with arrays of x and y already divided by the bump size; gives -1..1."""

    def __init__(self, seed):
        self.table = np.random.default_rng(seed).uniform(-1.0, 1.0, (256, 256))

    def __call__(self, x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        x0 = np.floor(x)
        y0 = np.floor(y)
        fx = x - x0
        fy = y - y0
        u = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
        v = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
        i0 = x0.astype(np.int64) & 255
        j0 = y0.astype(np.int64) & 255
        i1 = (i0 + 1) & 255
        j1 = (j0 + 1) & 255
        a = self.table[i0, j0]
        b = self.table[i1, j0]
        c = self.table[i0, j1]
        d = self.table[i1, j1]
        return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def graded_axis(low, high, fine_low, fine_high, fine_step, growth, largest_step):
    """Mesh lines along one direction: even and fine inside [fine_low, fine_high], growing coarser toward low and high."""
    count = int(round((fine_high - fine_low) / fine_step))
    inner = np.linspace(fine_low, fine_high, count + 1)
    step = (fine_high - fine_low) / count

    def run(start, limit, direction):
        points = []
        position, size = start, step
        while True:
            size = min(size * growth, largest_step)
            position += direction * size
            if (direction > 0 and position >= limit - 0.4 * size) or (direction < 0 and position <= limit + 0.4 * size):
                points.append(limit)
                return points
            points.append(position)

    below = run(fine_low, low, -1)[::-1]
    above = run(fine_high, high, +1)
    return np.concatenate([below, inner, above])


def smooth_curve_through(points, spacing):
    """A smooth curve through the given (x, y) points, as evenly spaced samples. Returns (samples n x 2, distance along n, total)."""
    p = np.array(points, dtype=float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    dense = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        pieces = max(4, int(np.linalg.norm(p2 - p1) / 0.05))
        for t in np.linspace(0.0, 1.0, pieces, endpoint=False):
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(p[-2])
    dense = np.array(dense)
    run = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))])
    total = run[-1]
    along = np.arange(0.0, total, spacing)
    return np.stack([np.interp(along, run, dense[:, 0]), np.interp(along, run, dense[:, 1])], axis=1), along, total


def nearest_sample(px, py, samples, chunk=2500):
    """For every point (px, py) the distance to the closest of the sample points and which sample it was."""
    count = len(px)
    distance = np.empty(count)
    index = np.empty(count, dtype=np.int64)
    sx = samples[:, 0][None, :]
    sy = samples[:, 1][None, :]
    for a in range(0, count, chunk):
        b = min(count, a + chunk)
        dx = px[a:b, None] - sx
        dy = py[a:b, None] - sy
        d2 = dx * dx + dy * dy
        best = np.argmin(d2, axis=1)
        index[a:b] = best
        distance[a:b] = np.sqrt(d2[np.arange(b - a), best])
    return distance, index


def random_rotation(rng):
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def rotation_about_z(angle):
    return mc.rotation_from_yaw(angle)


def distance_to_rectangle(x, y, rectangle):
    x_min, x_max, y_min, y_max = rectangle
    dx = np.maximum(np.maximum(x_min - x, x - x_max), 0.0)
    dy = np.maximum(np.maximum(y_min - y, y - y_max), 0.0)
    return np.hypot(dx, dy)


# ====================================================================================================================
# The ground plan: every feature of the ground in one place, so the terrain, the puddles and the clutter all agree
# ====================================================================================================================
class GroundPlan:
    def __init__(self):
        self.noise_wide = SoftNoise(101)
        self.noise_middle = SoftNoise(102)
        self.noise_small = SoftNoise(103)
        self.noise_patches = SoftNoise(104)
        self.noise_along = SoftNoise(105)
        self._plain_ground_height = np.vectorize(mc.ground_height, otypes=[float])

        # the track: samples along its curve, so we can keep ruts and puddles off it
        track = np.array([mc.track_point(float(t)) for t in np.linspace(0.0, 1.0, 700)])
        self.track_samples = track

        # cart ruts
        self.rut_lines = []
        rut_xy, rut_depth, rut_half = [], [], []
        for road_name, points in CART_ROADS.items():
            centre, along, total = smooth_curve_through(points, 0.1)
            tangent = np.gradient(centre, axis=0)
            tangent /= np.maximum(np.linalg.norm(tangent, axis=1, keepdims=True), 1e-9)
            normal = np.stack([-tangent[:, 1], tangent[:, 0]], axis=1)
            for side in (-1, +1):
                seed_shift = 7.0 * (len(self.rut_lines) + 1)
                wobble = 0.09 * self.noise_along(along / 3.0 + seed_shift, np.full_like(along, 0.5))
                line = centre + normal * ((side * RUT_GAUGE / 2.0) + wobble)[:, None]
                depth_along = RUT_DEPTH * (0.85 + 0.40 * self.noise_along(along / 2.4 + seed_shift, np.full_like(along, 3.5)))
                depth_along = depth_along * smooth_step(0.0, 3.0, along) * smooth_step(0.0, 3.0, total - along)
                half_along = RUT_HALF_WIDTH * (0.9 + 0.3 * self.noise_along(along / 1.7 + seed_shift, np.full_like(along, 7.5)))
                self.rut_lines.append({'road': road_name, 'side': side, 'xy': line, 'along': along, 'total': total})
                rut_xy.append(line)
                rut_depth.append(depth_along)
                rut_half.append(half_along)
        self.rut_xy = np.vstack(rut_xy)
        self.rut_depth = np.concatenate(rut_depth)
        self.rut_half_width = np.concatenate(rut_half)

        self.puddles = []
        self._build_puddle_shapes()
        for puddle in self.puddles:
            self._set_water_level(puddle)

    # ---- feature masks ----
    def distance_to_track(self, x, y):
        flat_x, flat_y = x.ravel(), y.ravel()
        distance, _ = nearest_sample(flat_x, flat_y, self.track_samples)
        return distance.reshape(x.shape)

    def distance_to_buildings(self, x, y):
        distance = np.full(x.shape, 1e9)
        for rectangle in BUILDING_FOOTPRINTS:
            distance = np.minimum(distance, distance_to_rectangle(x, y, rectangle))
        return distance

    def clear_factor(self, x, y):
        """0 right next to buildings and the track (ground left exactly as mc.ground_height), 1 out in the open yard."""
        away_from_buildings = smooth_step(1.3, 4.2, self.distance_to_buildings(x, y))
        away_from_track = smooth_step(1.7, 3.4, self.distance_to_track(x, y))
        return away_from_buildings * away_from_track

    # ---- the ground without puddles ----
    def ground_without_puddles(self, x, y):
        """Returns (height, wetness, coal_dust, slow_part), each a 1-D array. x and y are 1-D arrays of the same length.
        slow_part is the broad swell of the ground (its slope), which the puddles may flatten out."""
        base = self._plain_ground_height(x, y)
        clear = self.clear_factor(x, y)
        distance_to_rut, which = nearest_sample(x, y, self.rut_xy)
        half = self.rut_half_width[which]
        depth = self.rut_depth[which]
        core = np.exp(-(distance_to_rut / half) ** 2)
        raised_edge = 0.30 * np.exp(-((distance_to_rut - 1.9 * half) / (0.8 * half)) ** 2)
        rut_change = (-depth * core + depth * raised_edge) * clear

        # lumpy churned mud: broad swells everywhere, finer clods that get rougher beside the ruts
        near_rut = np.exp(-(distance_to_rut / 1.7) ** 2)
        yard_weight = smooth_step(80.0, 38.0, np.hypot(x - 2.0, y + 8.0))
        broad = 0.10 * self.noise_wide(x / 10.0, y / 10.0)
        finer = 0.040 * self.noise_middle(x / 3.6, y / 3.6) + 0.016 * self.noise_small(x / 1.45, y / 1.45)
        smooth_in_rut = 1.0 - 0.8 * np.exp(-(distance_to_rut / (1.6 * half)) ** 2)        # the bottom of a rut is smoothed by running water
        lumpy = (broad + finer * (1.0 + 1.0 * near_rut) * smooth_in_rut) * yard_weight * clear

        earth_mounds = np.zeros_like(x)
        for mound_x, mound_y, radius, height in EARTH_MOUNDS:
            r = np.hypot(x - mound_x, y - mound_y) / radius
            earth_mounds += height * smooth_step(1.0, 0.0, r) ** 1.5 * (0.8 + 0.4 * self.noise_middle(x / 2.2 + 5, y / 2.2))
        earth_mounds *= clear
        mounds = np.zeros_like(x)

        # coal heaps are heaps of the ground itself (cone with a rounded top), darkened with coal dust; lumps are laid on top later
        coal_dust = np.zeros_like(x)
        for heap_x, heap_y, radius, height, _ in COAL_HEAPS:
            r = np.hypot(x - heap_x, y - heap_y) / radius
            ragged = 0.85 + 0.30 * self.noise_middle(x / 1.3 + 17.0, y / 1.3)
            mounds += height * smooth_step(1.0, 0.0, r) ** 1.15 * ragged
            coal_dust = np.maximum(coal_dust, smooth_step(1.55, 0.7, r))
        mounds *= clear
        coal_dust = coal_dust * clear

        # the floor inside the engine house is dug 7 cm lower, so a floor built at ground level never fights with the mud
        inside_x = smooth_step(-3.80, -3.55, x) * smooth_step(3.80, 3.55, x)
        inside_y = smooth_step(0.10, 0.50, y) * smooth_step(10.95, 10.55, y)
        floor_dip = 0.07 * inside_x * inside_y

        slow_part = base + broad * yard_weight * clear + earth_mounds
        height = base + rut_change + lumpy + earth_mounds + mounds - floor_dip
        wetness = np.exp(-(distance_to_rut / (2.1 * half)) ** 2) * 0.9 * clear
        patches = 0.5 + 0.5 * self.noise_patches(x / 2.6 + 11.0, y / 2.6)
        wet_patches = 0.45 * np.clip(patches - 0.42, 0.0, 1.0) * smooth_step(30.0, 12.0, np.hypot(x + 3.0, y + 14.0))
        wetness = np.clip(wetness + wet_patches * clear, 0.0, 1.0) * (1.0 - 0.85 * coal_dust)
        return height, wetness, coal_dust, slow_part

    # ---- puddles ----
    def _build_puddle_shapes(self):
        rng = np.random.default_rng(55)
        for spec in PUDDLES:
            puddle = {'spec': spec, 'name': spec['name'], 'kind': spec['kind']}
            if spec['kind'] == 'blob':
                puddle['phases'] = rng.uniform(0, 2 * math.pi, 4)
            else:
                line = next(l for l in self.rut_lines if l['road'] == spec['road'] and l['side'] == spec['side'])
                keep = (line['xy'][:, 1] >= spec['y_range'][0]) & (line['xy'][:, 1] <= spec['y_range'][1])
                if 'x_range' in spec:
                    keep &= (line['xy'][:, 0] >= spec['x_range'][0]) & (line['xy'][:, 0] <= spec['x_range'][1])
                samples = line['xy'][keep]
                puddle['samples'] = samples
                puddle['progress'] = np.linspace(0.0, 1.0, len(samples))
                puddle['half_width_along'] = spec['half_width'] * np.sin(math.pi * puddle['progress']) ** 0.45 * (
                    0.85 + 0.3 * self.noise_along(puddle['progress'] * 5.0 + 20.0 + spec['y_range'][0], np.full(len(samples), 2.5)))
            self.puddles.append(puddle)

    def puddle_inside_depth(self, puddle, x, y):
        """Positive inside the puddle outline, negative outside, roughly in metres from the edge."""
        if puddle['kind'] == 'blob':
            return self._blob_inside_depth(puddle, x, y)
        distance, which = nearest_sample(x, y, puddle['samples'])
        return puddle['half_width_along'][which] - distance

    def _blob_boundary(self, puddle, angle):
        a2, a3, a5, a7 = puddle['phases']
        return 1.0 + 0.17 * np.cos(2 * angle + a2) + 0.12 * np.cos(3 * angle + a3) + 0.07 * np.cos(5 * angle + a5) + 0.05 * np.cos(7 * angle + a7)

    def _blob_inside_depth(self, puddle, x, y):
        spec = puddle['spec']
        cx, cy = spec['centre']
        a, b = spec['size']
        turn = math.radians(spec['turn'])
        dx, dy = x - cx, y - cy
        local_x = (dx * math.cos(turn) + dy * math.sin(turn)) / a
        local_y = (-dx * math.sin(turn) + dy * math.cos(turn)) / b
        radius = np.hypot(local_x, local_y)
        angle = np.arctan2(local_y, local_x)
        return (self._blob_boundary(puddle, angle) - radius) * math.sqrt(a * b)

    def _levelled(self, puddle, inside, height, slow_part):
        """The slope of the ground across a puddle is softened, so the puddle is not dug deep on its uphill side. Only the broad swell
        is flattened: ruts, clods and lumps stay as they are."""
        strength = LEVELLING if puddle['kind'] == 'blob' else RUT_LEVELLING
        weight = strength * smooth_step(-1.6, -0.2, inside)
        return height + weight * (puddle['plane_height'] - slow_part)

    def _set_water_level(self, puddle):
        """Look over the ground the puddle covers and set the water just above its lowest point."""
        if puddle['kind'] == 'blob':
            cx, cy = puddle['spec']['centre']
            reach = max(puddle['spec']['size']) * 1.5 + 1.6
            x0, x1, y0, y1 = cx - reach, cx + reach, cy - reach, cy + reach
        else:
            xs, ys = puddle['samples'][:, 0], puddle['samples'][:, 1]
            x0, x1, y0, y1 = xs.min() - 2.0, xs.max() + 2.0, ys.min() - 2.0, ys.max() + 2.0
        gx, gy = np.meshgrid(np.arange(x0, x1, 0.1), np.arange(y0, y1, 0.1))
        gx, gy = gx.ravel(), gy.ravel()
        inside = self.puddle_inside_depth(puddle, gx, gy)
        height, _, _, slow = self.ground_without_puddles(gx, gy)
        puddle['plane_height'] = float(slow[inside > 0].mean())
        height = self._levelled(puddle, inside, height, slow)
        covered = inside > -0.3
        puddle['lowest_ground'] = float(height[covered].min())
        puddle['water_level'] = puddle['lowest_ground'] + WATER_ABOVE_LOWEST

    def _dig_puddle(self, puddle, x, y, height, slow):
        level = puddle['water_level']
        inside = self.puddle_inside_depth(puddle, x, y)
        height = self._levelled(puddle, inside, height, slow)
        rim = level + 0.035
        lifted = height + smooth_step(-0.9, -0.2, inside) * np.maximum(0.0, rim - height)
        bed = level - HOLLOW_DEPTH + 0.006 * self.noise_small(x / 0.6, y / 0.6)
        digging = smooth_step(-0.25, 0.10, inside)
        return lifted - digging * np.maximum(0.0, lifted - bed), inside

    # ---- everything together ----
    def ground(self, x, y):
        """Final height and wetness of the ground at the given points (1-D arrays)."""
        height, wetness, _ = self.ground_with_dust(x, y)
        return height, wetness

    def ground_with_dust(self, x, y):
        """Final height, wetness and coal dust (how black the ground is from coal) at the given points."""
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        height, wetness, coal_dust, slow = self.ground_without_puddles(x, y)
        for puddle in self.puddles:
            height, inside = self._dig_puddle(puddle, x, y, height, slow)
            wetness = np.maximum(wetness, smooth_step(-1.0, 0.1, inside))
        return height, wetness, coal_dust

    def inside_any_puddle(self, x, y, margin=0.0):
        deepest = np.full(np.shape(x), -1e9)
        for puddle in self.puddles:
            deepest = np.maximum(deepest, self.puddle_inside_depth(puddle, np.asarray(x, dtype=float), np.asarray(y, dtype=float)))
        return deepest > -margin


# ====================================================================================================================
# 1. The terrain
# ====================================================================================================================
def break_up_repeating_tiles(material):
    """The mud picture repeats every 5 m. To hide that, every picture lookup is done twice, the second time at a slightly different
    size and position, and big slow patches decide which of the two shows. Nothing is rotated, so the bumps still light correctly."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    image_nodes = [n for n in nodes if n.type == 'TEX_IMAGE']
    coords = next(n for n in nodes if n.type == 'TEX_COORD')
    position = next(n for n in nodes if n.type == 'NEW_GEOMETRY')
    patch_noise = nodes.new('ShaderNodeTexNoise')
    patch_noise.inputs['Scale'].default_value = 0.17
    patch_noise.inputs['Detail'].default_value = 1.0
    links.new(position.outputs['Position'], patch_noise.inputs['Vector'])
    choice = nodes.new('ShaderNodeMapRange')
    choice.inputs['From Min'].default_value = 0.40
    choice.inputs['From Max'].default_value = 0.60
    links.new(patch_noise.outputs['Fac'], choice.inputs['Value'])
    shifted = nodes.new('ShaderNodeMapping')
    shifted.inputs['Scale'].default_value = (0.79, 0.79, 1.0)
    shifted.inputs['Location'].default_value = (0.37, 0.58, 0.0)
    links.new(coords.outputs['UV'], shifted.inputs['Vector'])
    for node in image_nodes:
        targets = [link.to_socket for link in node.outputs['Color'].links]
        for link in list(node.outputs['Color'].links):
            links.remove(link)
        second = nodes.new('ShaderNodeTexImage')
        second.image = node.image
        second.extension = node.extension
        second.interpolation = node.interpolation
        links.new(shifted.outputs['Vector'], second.inputs['Vector'])
        blend = nodes.new('ShaderNodeMix')
        blend.data_type = 'RGBA'
        links.new(choice.outputs['Result'], next(s for s in blend.inputs if s.name == 'Factor' and s.type == 'VALUE'))
        links.new(node.outputs['Color'], next(s for s in blend.inputs if s.name == 'A' and s.type == 'RGBA'))
        links.new(second.outputs['Color'], next(s for s in blend.inputs if s.name == 'B' and s.type == 'RGBA'))
        for target in targets:
            links.new(next(s for s in blend.outputs if s.type == 'RGBA'), target)


def build_wet_mud_material():
    """The uploaded mud picture + normal map + height map, then darkened and made glossier where the ground is wet
    (in the ruts and around puddles), blacker where coal dust lies, and flatter, greyer and duller far away.
    Wetness, farness and coal dust are stored in the mesh (colour layer 'ground_marks': red, green, blue)."""
    material = mc.surface_material('mud', tint=(0.95, 0.93, 0.95), true_displacement=True, variation=0.27, depth=MUD_RELIEF_DEPTH)
    break_up_repeating_tiles(material)
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')

    def new_mix(data_type, blend='MIX'):
        node = nodes.new('ShaderNodeMix')
        node.data_type = data_type
        node.blend_type = blend
        return node

    def socket(node, name, kind):
        return next(s for s in node.inputs if s.name == name and s.type == kind)

    def output(node, kind):
        return next(s for s in node.outputs if s.type == kind)

    marks = nodes.new('ShaderNodeAttribute')
    marks.attribute_name = 'ground_marks'
    marks.attribute_type = 'GEOMETRY'
    split = nodes.new('ShaderNodeSeparateColor')
    links.new(marks.outputs['Color'], split.inputs['Color'])
    wetness, farness, coal_dust = split.outputs['Red'], split.outputs['Green'], split.outputs['Blue']

    # colour: multiply by a wet tint, then by a far-away tint
    base_link = bsdf.inputs['Base Color'].links[0]
    base_source = base_link.from_socket
    wet_tint = new_mix('RGBA')
    socket(wet_tint, 'A', 'RGBA').default_value = (1.0, 1.0, 1.0, 1.0)
    socket(wet_tint, 'B', 'RGBA').default_value = (0.50, 0.46, 0.48, 1.0)
    links.new(wetness, socket(wet_tint, 'Factor', 'VALUE'))
    far_tint = new_mix('RGBA')
    socket(far_tint, 'A', 'RGBA').default_value = (1.0, 1.0, 1.0, 1.0)
    socket(far_tint, 'B', 'RGBA').default_value = (0.62, 0.66, 0.60, 1.0)
    links.new(farness, socket(far_tint, 'Factor', 'VALUE'))
    # far away the painted puddle flecks fade out toward the average mud colour, so the distance does not look like a regular pattern
    far_share = nodes.new('ShaderNodeMath')
    far_share.operation = 'MULTIPLY'
    far_share.inputs[1].default_value = 0.8
    links.new(farness, far_share.inputs[0])
    plain_far = new_mix('RGBA')
    links.new(far_share.outputs['Value'], socket(plain_far, 'Factor', 'VALUE'))
    links.new(base_source, socket(plain_far, 'A', 'RGBA'))
    socket(plain_far, 'B', 'RGBA').default_value = (0.115, 0.062, 0.042, 1.0)
    times_wet = new_mix('RGBA', 'MULTIPLY')
    socket(times_wet, 'Factor', 'VALUE').default_value = 1.0
    links.new(output(plain_far, 'RGBA'), socket(times_wet, 'A', 'RGBA'))
    links.new(output(wet_tint, 'RGBA'), socket(times_wet, 'B', 'RGBA'))
    times_far = new_mix('RGBA', 'MULTIPLY')
    socket(times_far, 'Factor', 'VALUE').default_value = 1.0
    links.new(output(times_wet, 'RGBA'), socket(times_far, 'A', 'RGBA'))
    links.new(output(far_tint, 'RGBA'), socket(times_far, 'B', 'RGBA'))
    coal_tint = new_mix('RGBA')
    socket(coal_tint, 'A', 'RGBA').default_value = (1.0, 1.0, 1.0, 1.0)
    socket(coal_tint, 'B', 'RGBA').default_value = (0.11, 0.115, 0.14, 1.0)
    links.new(coal_dust, socket(coal_tint, 'Factor', 'VALUE'))
    times_coal = new_mix('RGBA', 'MULTIPLY')
    socket(times_coal, 'Factor', 'VALUE').default_value = 1.0
    links.new(output(times_far, 'RGBA'), socket(times_coal, 'A', 'RGBA'))
    links.new(output(coal_tint, 'RGBA'), socket(times_coal, 'B', 'RGBA'))
    links.new(output(times_coal, 'RGBA'), bsdf.inputs['Base Color'])

    # shine: wet ground is glossier
    rough_link = bsdf.inputs['Roughness'].links[0]
    rough_source = rough_link.from_socket
    wet_gloss = new_mix('FLOAT')
    scaled_wet = nodes.new('ShaderNodeMath')
    scaled_wet.operation = 'MULTIPLY'
    scaled_wet.inputs[1].default_value = 0.62
    links.new(wetness, scaled_wet.inputs[0])
    links.new(scaled_wet.outputs['Value'], socket(wet_gloss, 'Factor', 'VALUE'))
    links.new(rough_source, socket(wet_gloss, 'A', 'VALUE'))
    socket(wet_gloss, 'B', 'VALUE').default_value = 0.17
    far_dull = new_mix('FLOAT')
    links.new(farness, socket(far_dull, 'Factor', 'VALUE'))
    links.new(output(wet_gloss, 'VALUE'), socket(far_dull, 'A', 'VALUE'))
    socket(far_dull, 'B', 'VALUE').default_value = 0.92
    links.new(output(far_dull, 'VALUE'), bsdf.inputs['Roughness'])

    # far away the small bumps shrink, so the distant ground does not shimmer like water
    normal_node = next(n for n in nodes if n.type == 'NORMAL_MAP')
    full_strength = normal_node.inputs['Strength'].default_value
    weaker_far = nodes.new('ShaderNodeMapRange')
    weaker_far.inputs['To Min'].default_value = full_strength
    weaker_far.inputs['To Max'].default_value = full_strength * 0.25
    links.new(farness, weaker_far.inputs['Value'])
    links.new(weaker_far.outputs['Result'], normal_node.inputs['Strength'])
    return material


def build_terrain(plan, collection_name):
    x_lines = graded_axis(*TERRAIN_X_RANGE, *FINE_X_RANGE, FINE_CELL, CELL_GROWTH, LARGEST_CELL)
    y_lines = graded_axis(*TERRAIN_Y_RANGE, *FINE_Y_RANGE, FINE_CELL, CELL_GROWTH, LARGEST_CELL)
    columns, rows = len(x_lines), len(y_lines)
    grid_x, grid_y = np.meshgrid(x_lines, y_lines)
    flat_x, flat_y = grid_x.ravel(), grid_y.ravel()
    mc.say(f'terrain mesh: {columns} x {rows} points = {(columns - 1) * (rows - 1)} squares')
    started = time.time()
    height, wetness, coal_dust = plan.ground_with_dust(flat_x, flat_y)
    mc.say(f'terrain heights worked out in {time.time() - started:.1f} s')
    far = smooth_step(30.0, 58.0, np.hypot(flat_x - 2.0, flat_y + 4.0))

    vertices = np.stack([flat_x, flat_y, height], axis=1)
    index = np.arange(columns * rows).reshape(rows, columns)
    squares = np.stack([index[:-1, :-1], index[:-1, 1:], index[1:, 1:], index[1:, :-1]], axis=-1).reshape(-1, 4)

    mesh = bpy.data.meshes.new(GROUND_OBJECT_NAME)
    mesh.vertices.add(len(vertices))
    mesh.vertices.foreach_set('co', vertices.astype(np.float64).ravel())
    mesh.loops.add(squares.size)
    mesh.loops.foreach_set('vertex_index', squares.ravel())
    mesh.polygons.add(len(squares))
    mesh.polygons.foreach_set('loop_start', np.arange(len(squares), dtype=np.int32) * 4)
    mesh.polygons.foreach_set('use_smooth', np.ones(len(squares), dtype=bool))
    mesh.polygons.foreach_set('material_index', np.zeros(len(squares), dtype=np.int32))
    mesh.update(calc_edges=True)

    tile = mc.SURFACES['mud']['tile']
    layer = mesh.uv_layers.new(name='UVMap')
    corner_points = vertices[squares.ravel()]
    layer.data.foreach_set('uv', np.stack([corner_points[:, 0] / tile, corner_points[:, 1] / tile], axis=1).ravel())

    marks = mesh.color_attributes.new(name='ground_marks', type='FLOAT_COLOR', domain='POINT')
    marks.data.foreach_set('color', np.stack([wetness, far, coal_dust, np.ones_like(far)], axis=1).ravel())

    material = build_wet_mud_material()
    mesh.materials.append(material)
    terrain = bpy.data.objects.new(GROUND_OBJECT_NAME, mesh)
    collection = _collection(collection_name)
    collection.objects.link(terrain)
    mc.use_real_displacement(terrain, TERRAIN_DICING_PIXELS)
    return terrain, (columns - 1) * (rows - 1)


def _collection(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


# ====================================================================================================================
# 2. The puddles
# ====================================================================================================================
def build_water_material():
    material = mc.plain_material('Puddle water', (0.018, 0.030, 0.042), roughness=0.02)
    bsdf = material.node_tree.nodes['Principled BSDF']
    bsdf.inputs['IOR'].default_value = 1.33
    bsdf.inputs['Alpha'].default_value = 0.88
    # a faint ripple so the mirror is not perfectly flat and CG-clean
    nodes, links = material.node_tree.nodes, material.node_tree.links
    coords = nodes.new('ShaderNodeTexCoord')
    ripples = nodes.new('ShaderNodeTexNoise')
    ripples.inputs['Scale'].default_value = 18.0
    ripples.inputs['Detail'].default_value = 2.0
    links.new(coords.outputs['Object'], ripples.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.06
    bump.inputs['Distance'].default_value = 0.01
    links.new(ripples.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return material


def build_puddles(plan, collection_name):
    builder = mc.MeshBuilder(PUDDLE_OBJECT_NAME, [build_water_material()])
    report = []
    for puddle in plan.puddles:
        level = puddle['water_level']
        spec = puddle['spec']
        edge_margin = -0.20      # the sheet reaches 20 cm past the nominal edge, hidden under the raised rim
        if puddle['kind'] == 'blob':
            cx, cy = spec['centre']
            a, b = spec['size']
            turn = math.radians(spec['turn'])
            angles = np.linspace(0.0, 2 * math.pi, 56, endpoint=False)
            boundary = plan._blob_boundary(puddle, angles) + (-edge_margin) / math.sqrt(a * b)
            local_x, local_y = a * boundary * np.cos(angles), b * boundary * np.sin(angles)
            world_x = cx + local_x * math.cos(turn) - local_y * math.sin(turn)
            world_y = cy + local_x * math.sin(turn) + local_y * math.cos(turn)
            outline = np.stack([world_x, world_y], axis=1)
            ring = np.column_stack([outline, np.full(len(outline), level)])
            for i in range(len(ring)):
                j = (i + 1) % len(ring)
                builder.add_polygon([(cx, cy, level), ring[i], ring[j]])
        else:
            samples = puddle['samples'][::3]
            half_width = (puddle['half_width_along'][::3]) + (-edge_margin)
            tangent = np.gradient(samples, axis=0)
            tangent /= np.maximum(np.linalg.norm(tangent, axis=1, keepdims=True), 1e-9)
            normal = np.stack([-tangent[:, 1], tangent[:, 0]], axis=1)
            left = samples + normal * half_width[:, None]
            right = samples - normal * half_width[:, None]
            outline = np.vstack([left, right[::-1]])
            for i in range(len(samples) - 1):
                builder.add_polygon([(right[i][0], right[i][1], level), (right[i + 1][0], right[i + 1][1], level),
                                     (left[i + 1][0], left[i + 1][1], level), (left[i][0], left[i][1], level)])
        distance_to_track = plan.distance_to_track(outline[:, 0], outline[:, 1]).min()
        report.append({'name': puddle['name'], 'water_level': round(level, 3), 'lowest_ground': round(puddle['lowest_ground'], 3),
                       'nearest_track_distance': round(float(distance_to_track), 2)})
    obj = builder.finish(collection_name)
    return obj, report


# ====================================================================================================================
# 3. Shapes for the clutter (timber, logs, barrels, wheels...)
# ====================================================================================================================
def add_timber(builder, start, end, sideways_size, up_size, slot, up_hint=(0.0, 0.0, 1.0), grain_shift=0.0):
    """A straight sawn beam or plank from start to end. The wood grain runs along its length."""
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    basis = mc.basis_from_direction(end - start, up_hint)
    forward, side, up = basis[:, 0], basis[:, 1], basis[:, 2]
    half_side, half_up = sideways_size / 2.0, up_size / 2.0

    def corner(at_end, s, u):
        return (end if at_end else start) + side * s * half_side + up * u * half_up

    def face(points, axes):
        builder.add_polygon(points, slot=slot, uv_axes=axes, uv_shift=(grain_shift, grain_shift * 0.37))

    face([corner(0, -1, 1), corner(1, -1, 1), corner(1, 1, 1), corner(0, 1, 1)], (forward, side))        # top
    face([corner(0, -1, -1), corner(0, 1, -1), corner(1, 1, -1), corner(1, -1, -1)], (forward, side))    # bottom
    face([corner(0, 1, -1), corner(0, 1, 1), corner(1, 1, 1), corner(1, 1, -1)], (forward, up))          # one side
    face([corner(0, -1, -1), corner(1, -1, -1), corner(1, -1, 1), corner(0, -1, 1)], (forward, up))      # other side
    face([corner(1, -1, -1), corner(1, 1, -1), corner(1, 1, 1), corner(1, -1, 1)], (side, up))           # far end
    face([corner(0, -1, -1), corner(0, -1, 1), corner(0, 1, 1), corner(0, 1, -1)], (side, up))           # near end


def add_log(builder, start, end, radius, slot, sides=9, grain_shift=0.0, radius_end=None):
    """A round pit prop. The wood grain runs along its length."""
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    radius_end = radius if radius_end is None else radius_end
    basis = mc.basis_from_direction(end - start)
    side, up = basis[:, 1], basis[:, 2]
    angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    ring = np.outer(np.cos(angles), side) + np.outer(np.sin(angles), up)
    low, high = start + ring * radius, end + ring * radius_end
    length = float(np.linalg.norm(end - start))
    for i in range(sides):
        j = (i + 1) % sides
        around_i, around_j = angles[i] * radius, (angles[i] + 2 * np.pi / sides) * radius
        # picture coordinates: grain runs along the log (u = length), around the log is v
        builder.add_polygon([low[i], low[j], high[j], high[i]], slot=slot, smooth=True,
                            uv_metres=[(grain_shift, around_i), (grain_shift, around_j), (length + grain_shift, around_j), (length + grain_shift, around_i)])
    builder.add_polygon(low[::-1], slot=slot, uv_axes=(side, up))
    builder.add_polygon(high, slot=slot, uv_axes=(side, up))


def add_barrel(builder, x, y, ground, radius, height, body_slot, hoop_slot, water_slot=None):
    """An oil or water barrel standing on the ground. If water_slot is given the top is open with dark water inside."""
    profile = [0.90, 0.985, 1.0, 0.985, 0.90]
    heights = np.linspace(0.0, height, len(profile))
    for k in range(len(profile) - 1):
        builder.add_cylinder((x, y, ground + heights[k]), (x, y, ground + heights[k + 1]), radius * profile[k], sides=16, slot=body_slot,
                             radius_end=radius * profile[k + 1], caps=(k in (0, len(profile) - 2) and water_slot is None))
    for fraction, thickness in ((0.06, 0.05), (0.30, 0.04), (0.70, 0.04), (0.94, 0.05)):
        z = ground + height * fraction
        ring_radius = radius * float(np.interp(fraction, np.linspace(0, 1, len(profile)), profile)) + 0.012
        builder.add_ring((x, y, z), (0, 0, 1), ring_radius, ring_radius - 0.03, thickness, sides=16, slot=hoop_slot, smooth=False)
    if water_slot is not None:
        top_radius = radius * profile[-1]
        builder.add_ring((x, y, ground + height), (0, 0, 1), top_radius + 0.012, top_radius - 0.03, 0.03, sides=16, slot=hoop_slot, smooth=False)
        angles = np.linspace(0, 2 * math.pi, 16, endpoint=False)
        disc = [(x + (top_radius - 0.02) * math.cos(a), y + (top_radius - 0.02) * math.sin(a), ground + height - 0.11) for a in angles]
        builder.add_polygon(disc, slot=water_slot)


def add_spoked_wheel(builder, centre, axis_along_y_rotation, radius, rim_slot, spoke_slot, spokes=10, thickness=0.07):
    """A cart wheel standing in the plane given by the rotation (its own y axis is the axle)."""
    centre = np.asarray(centre, dtype=float)
    rotation = np.asarray(axis_along_y_rotation)
    axle = rotation @ np.array([0.0, 1.0, 0.0])
    builder.add_ring(centre, axle, radius, radius - 0.06, thickness, sides=20, slot=rim_slot, smooth=False)
    hub_half = rotation @ np.array([0.0, 0.07, 0.0])
    builder.add_cylinder(centre - hub_half, centre + hub_half, 0.075, sides=10, slot=spoke_slot)
    for k in range(spokes):
        angle = 2 * math.pi * k / spokes
        direction = rotation @ np.array([math.cos(angle), 0.0, math.sin(angle)])
        add_timber(builder, centre + direction * 0.05, centre + direction * (radius - 0.04), 0.035, 0.035, spoke_slot,
                   up_hint=tuple(axle), grain_shift=k * 0.13)


# ====================================================================================================================
# 4. Yard clutter
# ====================================================================================================================
def rough_rock_material(name, dark_colour, light_colour, roughness, bumpiness=0.6, speckle_scale=22.0):
    """A plain rock colour made rough and speckled with world-space noise (no picture needed; it works on any lump shape)."""
    material = mc.plain_material(name, dark_colour, roughness=roughness)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes['Principled BSDF']
    coords = nodes.new('ShaderNodeTexCoord')
    speckle = nodes.new('ShaderNodeTexNoise')
    speckle.inputs['Scale'].default_value = speckle_scale
    speckle.inputs['Detail'].default_value = 6.0
    speckle.inputs['Roughness'].default_value = 0.65
    links.new(coords.outputs['Object'], speckle.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*dark_colour, 1.0)
    ramp.color_ramp.elements[1].color = (*light_colour, 1.0)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[1].position = 0.72
    links.new(speckle.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 140.0
    grain.inputs['Detail'].default_value = 3.0
    links.new(coords.outputs['Object'], grain.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = bumpiness
    bump.inputs['Distance'].default_value = 0.01
    links.new(grain.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return material


def clutter_materials():
    coal = rough_rock_material('Coal lump', (0.010, 0.012, 0.018), (0.050, 0.056, 0.072), roughness=0.46, bumpiness=0.35, speckle_scale=40.0)
    grey_stone = rough_rock_material('Grey stone', (0.060, 0.066, 0.078), (0.20, 0.21, 0.23), roughness=0.72)
    rust_stone = rough_rock_material('Rust-brown stone', (0.085, 0.045, 0.028), (0.26, 0.135, 0.07), roughness=0.78)
    return [coal, grey_stone, rust_stone]


# A cube whose corners are pushed about gives a chunky, angular lump of coal, like the lumps in the cart picture.
_CUBE_CORNERS = np.array([[x, y, z] for z in (-1.0, 1.0) for y in (-1.0, 1.0) for x in (-1.0, 1.0)])
_CUBE_FACES = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]


def add_chunk(builder, rng, centre, radii, rotation, slot, roughness=0.28):
    """An angular lump: a cube with its corners pushed about."""
    corners = _CUBE_CORNERS * (1.0 + rng.uniform(-roughness, roughness, (8, 3)))
    vertices = (corners * np.asarray(radii)) @ np.asarray(rotation).T + np.asarray(centre)
    builder.add_indexed_faces(vertices, _CUBE_FACES, slot=slot)


def add_lump(builder, rng, x, y, ground, radius, slot, sink=0.22):
    """One coal lump or stone sunk part way into the ground."""
    radii = radius * np.array([rng.uniform(0.95, 1.4), rng.uniform(0.7, 1.1), rng.uniform(0.5, 0.85)])
    rotation = rotation_about_z(rng.uniform(0, 2 * math.pi))
    if rng.random() < 0.35:
        rotation = rotation @ random_rotation(rng)
    centre = (x, y, ground + sink * radii[2])
    shape = rng.random()
    if radius < 0.03:
        builder.add_blob(centre, radii, slot=slot, subdivisions=0, rotation=rotation, jitter=0.28, seed=int(rng.integers(1_000_000)))
    elif shape < 0.40 and slot == 0:
        add_chunk(builder, rng, centre, radii * 0.85, rotation, slot, roughness=0.32)       # angular coal chunks; stones are rounder
    else:
        builder.add_blob(centre, radii, slot=slot, subdivisions=1, rotation=rotation,
                         jitter=0.22, seed=int(rng.integers(1_000_000)))


def scatter_lumps(plan, builder, rng, keep_clear):
    """Hundreds of coal lumps and stones lying around the yard, more of them in spilled clusters."""
    xs, ys, sizes = [], [], []

    def add_points(x, y, size):
        xs.append(x)
        ys.append(y)
        sizes.append(size)

    # a loose scatter all over the foreground yard
    count = 760
    add_points(rng.uniform(-15.0, 11.0, count), rng.uniform(-27.0, -3.0, count), 0.024 * np.exp(rng.normal(0, 0.55, count)))
    # a thinner scatter across the whole yard
    count = 260
    angle = rng.uniform(0, 2 * math.pi, count)
    reach = 30.0 * np.sqrt(rng.uniform(0.1, 1.0, count))
    add_points(3.0 + reach * np.cos(angle), -6.0 + reach * np.sin(angle) * 0.9, 0.028 * np.exp(rng.normal(0, 0.55, count)))
    # spilled clusters
    for _ in range(54):
        centre_x, centre_y = rng.uniform(-14.0, 10.0), rng.uniform(-25.0, -4.0)
        number = int(rng.integers(8, 46))
        spread = rng.uniform(0.35, 1.3)
        add_points(centre_x + rng.normal(0, spread, number), centre_y + rng.normal(0, spread, number), 0.04 * np.exp(rng.normal(0, 0.45, number)))
    # lumps beside the cart roads, shaken off the carts
    for line in plan.rut_lines:
        picks = rng.integers(0, len(line['xy']), 30)
        side = rng.choice([-1.0, 1.0], 30) * rng.uniform(0.35, 1.1, 30)
        add_points(line['xy'][picks, 0] + side, line['xy'][picks, 1] + rng.normal(0, 0.2, 30), 0.036 * np.exp(rng.normal(0, 0.5, 30)))
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    size = np.clip(np.concatenate(sizes), 0.014, 0.14)

    allowed = (plan.distance_to_track(x, y) > 1.9) & (plan.distance_to_buildings(x, y) > 0.9)
    allowed &= ~plan.inside_any_puddle(x, y, margin=0.0)
    for centre_x, centre_y, reach in keep_clear:
        allowed &= np.hypot(x - centre_x, y - centre_y) > reach
    x, y, size = x[allowed], y[allowed], size[allowed]
    ground, _ = plan.ground(x, y)
    kind = rng.random(len(x))
    slots = np.where(kind < 0.62, 0, np.where(kind < 0.88, 1, 2))
    for i in range(len(x)):
        add_lump(builder, rng, x[i], y[i], ground[i], size[i], int(slots[i]))
    return len(x)


def scatter_boulders(plan, builder, rng, keep_clear):
    """Bigger stones and coal blocks lying about, mostly near the cart roads and at the edges of the yard."""
    count = 150
    xs, ys = [], []
    for line in plan.rut_lines:
        picks = rng.integers(0, len(line['xy']), 9)
        side = rng.choice([-1.0, 1.0], 9) * rng.uniform(0.8, 2.2, 9)
        xs.append(line['xy'][picks, 0] + side)
        ys.append(line['xy'][picks, 1] + rng.normal(0, 0.3, 9))
    xs.append(rng.uniform(-16.0, 12.0, 60))
    ys.append(rng.uniform(-27.0, -3.0, 60))
    x, y = np.concatenate(xs), np.concatenate(ys)
    allowed = (plan.distance_to_track(x, y) > 2.0) & (plan.distance_to_buildings(x, y) > 1.2) & ~plan.inside_any_puddle(x, y, margin=0.3)
    for centre_x, centre_y, reach in keep_clear:
        allowed &= np.hypot(x - centre_x, y - centre_y) > reach
    x, y = x[allowed], y[allowed]
    ground, _ = plan.ground(x, y)
    for i in range(len(x)):
        size = 0.07 + 0.15 * rng.random() ** 2.2
        kind = rng.random()
        slot = 0 if kind < 0.55 else (1 if kind < 0.85 else 2)
        radii = size * np.array([rng.uniform(0.95, 1.35), rng.uniform(0.75, 1.1), rng.uniform(0.6, 0.95)])
        rotation = rotation_about_z(rng.uniform(0, 2 * math.pi)) @ random_rotation(rng)
        centre = (x[i], y[i], ground[i] + 0.2 * radii[2])
        builder.add_blob(centre, radii, slot=slot, subdivisions=2, rotation=rotation, jitter=0.12, seed=int(rng.integers(1_000_000)))
    return len(x)


def add_coal_heap(plan, builder, rng, heap):
    """Lumps of coal laid over a heap that is already part of the terrain (cone-shaped, darkened with coal dust)."""
    centre_x, centre_y, radius, height, _ = heap
    number = int(130 * radius * radius)
    angle = rng.uniform(0, 2 * math.pi, number)
    near = np.sqrt(rng.uniform(0.0, 1.0, number)) * radius * 1.12
    x = centre_x + near * np.cos(angle)
    y = centre_y + near * np.sin(angle)
    ground, _ = plan.ground(x, y)
    for i in range(number):
        size = (0.026 + 0.05 * rng.random() ** 2.0) * (1.2 - 0.35 * min(near[i] / radius, 1.2))      # half-size of the lump, metres
        kind = rng.random()
        slot = 0 if kind < 0.88 else (1 if kind < 0.96 else 2)
        radii = size * np.array([rng.uniform(0.95, 1.4), rng.uniform(0.7, 1.1), rng.uniform(0.55, 0.95)])
        rotation = rotation_about_z(rng.uniform(0, 2 * math.pi)) @ random_rotation(rng)
        centre = (x[i], y[i], ground[i] + 0.25 * size)
        if slot == 0 and rng.random() < 0.45:
            add_chunk(builder, rng, centre, radii, rotation, slot, roughness=0.32)
        else:
            builder.add_blob(centre, radii, slot=slot, subdivisions=0 if rng.random() < 0.6 else 1, rotation=rotation,
                             jitter=0.26, seed=int(rng.integers(1_000_000)))


# ---- props: timber stack, fence, barrels, handcart, sleepers, lamp post ----
class PropSlots:
    wood, old_wood, rusty_iron, dark_iron, lamp_glass, barrel_water = range(6)


def prop_materials():
    return [
        mc.surface_material('wood', tint=(1.15, 1.0, 0.88), variation=0.3),
        mc.surface_material('wood', tint=(0.66, 0.60, 0.56), variation=0.3),
        mc.surface_material('metal', tint=(1.15, 0.72, 0.52), variation=0.3),
        mc.surface_material('metal', tint=(0.36, 0.40, 0.44), variation=0.2),
        mc.glow_material('Lamp glass', (1.0, 0.64, 0.26), 34.0),
        mc.plain_material('Barrel water', (0.010, 0.016, 0.022), roughness=0.05),
    ]


def ground_at(plan, x, y):
    height, _ = plan.ground(np.array([x], dtype=float), np.array([y], dtype=float))
    return float(height[0])


def add_timber_rack(plan, builder, rng):
    """A leaning stack of planks and pit props against a crossbar held up by two posts, plus a few props lying in front."""
    rack = TIMBER_RACK
    bar_x, bar_z = rack['x'], rack['bar_height']
    ground_a, ground_b = ground_at(plan, bar_x, rack['y_from']), ground_at(plan, bar_x, rack['y_to'])
    S = PropSlots
    for y, ground in ((rack['y_from'] + 0.12, ground_a), (rack['y_to'] - 0.12, ground_b)):
        add_timber(builder, (bar_x + 0.10, y, ground - 0.2), (bar_x + 0.10, y, ground + bar_z + 0.22), 0.16, 0.16, S.old_wood, grain_shift=y)
    add_timber(builder, (bar_x + 0.06, rack['y_from'] - 0.12, ground_a + bar_z), (bar_x + 0.06, rack['y_to'] + 0.12, ground_b + bar_z), 0.12, 0.14,
               S.old_wood, up_hint=(1, 0, 0))
    count = 15
    for k in range(count):
        y = rack['y_from'] + 0.08 + (rack['y_to'] - rack['y_from'] - 0.16) * k / (count - 1) + rng.uniform(-0.03, 0.03)
        ground = ground_a + (ground_b - ground_a) * k / (count - 1)
        foot_x = bar_x - rng.uniform(0.55, 0.85)
        length = rng.uniform(2.7, 3.5)
        # a plank that rests on the bar: its top end lies above the bar, its foot on the ground
        run = (bar_x - 0.05) - foot_x
        rise = bar_z
        along = np.array([run, 0.0, rise]) / math.hypot(run, rise)
        foot = np.array([foot_x, y, ground + 0.03])
        top = foot + along * length
        sideways = rng.uniform(-0.05, 0.05)
        if k % 5 == 3:
            add_log(builder, foot + np.array([0, 0, 0.0]), top, rng.uniform(0.055, 0.075), S.wood, grain_shift=rng.random() * 3,
                    radius_end=rng.uniform(0.05, 0.065))
        else:
            add_timber(builder, foot, top + np.array([0.0, sideways, 0.0]), rng.uniform(0.17, 0.26), rng.uniform(0.04, 0.055),
                       S.wood if rng.random() < 0.6 else S.old_wood, grain_shift=rng.random() * 5)
    # props lying on the ground in front of the rack
    base_x = rack['x'] - 1.9
    for k, (offset_y, layer) in enumerate([(-0.5, 0), (0.0, 0), (0.5, 0), (-0.25, 1), (0.25, 1), (0.0, 2)]):
        y_mid = 0.5 * (rack['y_from'] + rack['y_to']) + offset_y * 1.5
        ground = ground_at(plan, base_x, y_mid)
        z = ground + 0.09 + layer * 0.15
        add_log(builder, (base_x + rng.uniform(-0.1, 0.1), y_mid - 1.3, z), (base_x + rng.uniform(-0.1, 0.1), y_mid + 1.3, z), 0.085, S.wood,
                grain_shift=rng.random() * 4)


def add_fence(plan, builder, rng):
    S = PropSlots
    samples, _, total = smooth_curve_through(FENCE_LINE, 0.05)
    post_count = int(total // 1.75) + 1
    spacing = total / (post_count - 1)
    posts = []
    for k in range(post_count):
        index = min(int(k * spacing / 0.05), len(samples) - 1)
        x, y = samples[index]
        ground = ground_at(plan, x, y)
        lean_x, lean_y = rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)
        top_height = rng.uniform(1.05, 1.2)
        add_timber(builder, (x, y, ground - 0.25), (x + lean_x, y + lean_y, ground + top_height), 0.13, 0.13, S.old_wood, grain_shift=k * 0.7)
        posts.append((x, y, ground))
    for k in range(post_count - 1):
        for height, missing_chance in ((0.55, 0.12), (0.95, 0.22)):
            if rng.random() < missing_chance:
                continue
            (x0, y0, g0), (x1, y1, g1) = posts[k], posts[k + 1]
            sag = rng.uniform(-0.03, 0.03)
            direction = np.array([x1 - x0, y1 - y0, 0.0])
            side = np.array([-direction[1], direction[0], 0.0])
            side /= np.linalg.norm(side)
            offset = side * 0.085
            add_timber(builder, (x0 + offset[0], y0 + offset[1], g0 + height), (x1 + offset[0], y1 + offset[1], g1 + height + sag), 0.045, 0.12,
                       S.wood, grain_shift=rng.random() * 5)


def add_barrels(plan, builder, rng):
    S = PropSlots
    for number, (x, y) in enumerate(BARREL_SPOTS):
        ground = ground_at(plan, x, y)
        if number == 0:
            add_barrel(builder, x, y, ground - 0.02, 0.30, 0.90, S.rusty_iron, S.dark_iron)
        else:
            add_barrel(builder, x, y, ground - 0.02, 0.30, 0.88, S.dark_iron, S.rusty_iron, water_slot=S.barrel_water)


def add_handcart(plan, builder, rng):
    """A wooden two-wheeled handcart parked with its shafts resting on the ground."""
    S = PropSlots
    cart = HANDCART
    yaw = math.radians(cart['yaw_degrees'])
    ground = ground_at(plan, cart['x'], cart['y'])
    wheel_radius = 0.50
    axle_height = wheel_radius - 0.02
    shaft_pitch = math.atan2(axle_height + 0.12 - 0.05, 2.1)      # the front of the shafts rests on the ground
    turn = rotation_about_z(yaw)
    pitch = np.array([[math.cos(-shaft_pitch), 0, math.sin(-shaft_pitch)], [0, 1, 0], [-math.sin(-shaft_pitch), 0, math.cos(-shaft_pitch)]])
    origin = np.array([cart['x'], cart['y'], ground])

    def place(point, pitched=False):
        local = np.asarray(point, dtype=float)
        if pitched:
            local = pitch @ (local - np.array([0, 0, axle_height + 0.12])) + np.array([0, 0, axle_height + 0.12])
        return origin + turn @ local

    def fixed_basis(pitched):
        return turn @ (pitch if pitched else np.eye(3))

    # wheels and axle
    for side in (-1, 1):
        add_spoked_wheel(builder, place((0.0, side * 0.52, axle_height)), turn, wheel_radius, S.old_wood, S.wood)
    add_timber(builder, place((0, -0.56, axle_height)), place((0, 0.56, axle_height)), 0.07, 0.07, S.dark_iron)
    # shafts and bed (tilted together)
    for side in (-1, 1):
        add_timber(builder, place((-0.95, side * 0.40, axle_height + 0.12), True), place((2.1, side * 0.40, axle_height + 0.12), True), 0.07, 0.07,
                   S.old_wood, up_hint=tuple(fixed_basis(True) @ np.array([0, 0, 1])))
        add_timber(builder, place((-0.55, side * 0.40, axle_height + 0.07), True), place((0.55, side * 0.40, axle_height + 0.07), True), 0.06, 0.06,
                   S.old_wood)
    bed_centre = place((0.0, 0.0, axle_height + 0.17), True)
    builder.add_box(bed_centre, (1.15, 0.84, 0.035), slot=S.wood, rotation=fixed_basis(True))
    for side in (-1, 1):
        builder.add_box(place((0.0, side * 0.42, axle_height + 0.32), True), (1.15, 0.04, 0.30), slot=S.old_wood, rotation=fixed_basis(True))
    for end in (-1, 1):
        builder.add_box(place((end * 0.575, 0.0, axle_height + 0.32), True), (0.04, 0.84, 0.30), slot=S.wood, rotation=fixed_basis(True))
    # a few lumps of coal in the bed
    for _ in range(9):
        local = (rng.uniform(-0.45, 0.45), rng.uniform(-0.3, 0.3), axle_height + 0.25 + rng.uniform(0.0, 0.1))
        add_blob_at(builder, rng, place(local, True), 0.07)


def add_blob_at(builder, rng, centre, size):
    radii = size * np.array([rng.uniform(0.9, 1.3), rng.uniform(0.8, 1.1), rng.uniform(0.6, 0.9)])
    builder.add_blob(tuple(centre), radii, slot=0, subdivisions=0, rotation=rotation_about_z(rng.uniform(0, 6.28)) @ random_rotation(rng), jitter=0.26,
                     seed=int(rng.integers(1_000_000)))


def add_sleeper_pile(plan, builder, rng):
    """A rough pile of old railway sleepers: layers laid crosswise but shifted, turned and sagging, with a few lying beside it."""
    S = PropSlots
    pile = SLEEPER_PILE
    length, width, thick = 2.4, 0.26, 0.15
    pile_turn = math.radians(rng.uniform(-8, 8))
    along = np.array([math.cos(pile_turn), math.sin(pile_turn)])          # direction of the sleepers in even layers
    across = np.array([-along[1], along[0]])
    for layer in range(6):
        crosswise = layer % 2 == 1
        shift = rng.uniform(-0.08, 0.08, 2)
        layer_turn = math.radians(rng.uniform(-3.5, 3.5))
        number = 8 if crosswise else 4
        for k in range(number):
            if rng.random() < 0.08 and layer > 3:
                continue
            spacing = (width + 0.03) if not crosswise else 0.275
            offset = (k - (number - 1) / 2.0) * spacing + rng.uniform(-0.03, 0.03)
            if crosswise:
                direction, side_direction = across, along
                half_length = length / 2 - 0.65 + rng.uniform(-0.12, 0.12)
            else:
                direction, side_direction = along, across
                half_length = length / 2 + rng.uniform(-0.12, 0.1)
            direction = np.array([direction[0] * math.cos(layer_turn) - direction[1] * math.sin(layer_turn),
                                  direction[0] * math.sin(layer_turn) + direction[1] * math.cos(layer_turn)])
            centre = np.array([pile['x'], pile['y']]) + side_direction * offset + shift
            ends = (centre - direction * half_length, centre + direction * half_length)
            z = [ground_at(plan, ends[0][0], ends[0][1]), ground_at(plan, ends[1][0], ends[1][1])]
            base = min(z) - 0.03 if layer == 0 else None
            if layer == 0:
                heights = (base + thick * 0.5, base + thick * 0.5)
            else:
                lift = 0.045 * (layer % 3) * rng.uniform(0.5, 1.0)
                heights = (ground_at(plan, centre[0], centre[1]) + thick * (layer + 0.5) - 0.03 + lift * 0.3,) * 2
            add_timber(builder, (ends[0][0], ends[0][1], heights[0]), (ends[1][0], ends[1][1], heights[1] + rng.uniform(-0.02, 0.03)),
                       width * rng.uniform(0.92, 1.05), thick * rng.uniform(0.9, 1.08), S.old_wood if rng.random() < 0.7 else S.wood,
                       grain_shift=rng.random() * 9)
    # spare sleepers on the ground next to the pile, one propped on the corner
    for k, (dx, dy, turn) in enumerate(((2.0, -0.9, 15), (2.2, 0.9, -12), (-0.4, -2.0, 80))):
        x, y = pile['x'] + dx, pile['y'] + dy
        a_turn = math.radians(turn)
        start = (x - math.cos(a_turn) * 1.2, y - math.sin(a_turn) * 1.2)
        end = (x + math.cos(a_turn) * 1.2, y + math.sin(a_turn) * 1.2)
        add_timber(builder, (start[0], start[1], ground_at(plan, *start) + 0.06), (end[0], end[1], ground_at(plan, *end) + 0.06), width, thick,
                   S.old_wood, grain_shift=k * 3.1)


def add_lamp_post(plan, builder):
    S = PropSlots
    x, y = LAMP_POSITION
    ground = ground_at(plan, x, y)
    # stepped foot
    builder.add_box((x, y, ground + 0.08), (0.55, 0.55, 0.20), slot=S.dark_iron)
    builder.add_box((x, y, ground + 0.24), (0.42, 0.42, 0.14), slot=S.dark_iron)
    builder.add_cylinder((x, y, ground + 0.30), (x, y, ground + 1.15), 0.16, sides=10, slot=S.dark_iron, radius_end=0.095)
    builder.add_ring((x, y, ground + 1.15), (0, 0, 1), 0.125, 0.06, 0.07, sides=12, slot=S.dark_iron, smooth=False)
    shaft_top = ground + LAMP_HEIGHT - 0.55
    builder.add_cylinder((x, y, ground + 1.15), (x, y, shaft_top), 0.075, sides=10, slot=S.dark_iron, radius_end=0.05)
    for fraction in (0.35, 0.7):
        z = ground + 1.15 + (shaft_top - ground - 1.15) * fraction
        builder.add_ring((x, y, z), (0, 0, 1), 0.085, 0.04, 0.05, sides=12, slot=S.dark_iron, smooth=False)
    # crossbar for the lamp lighter's ladder
    builder.add_cylinder((x - 0.32, y, shaft_top - 0.45), (x + 0.32, y, shaft_top - 0.45), 0.022, sides=6, slot=S.dark_iron)
    # lantern: tray, four corner bars, glowing glass, cap and knob
    z0 = shaft_top
    builder.add_box((x, y, z0 + 0.025), (0.38, 0.38, 0.05), slot=S.dark_iron, yaw=math.radians(45))
    for corner_x, corner_y in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        add_timber(builder, (x + corner_x * 0.13, y + corner_y * 0.13, z0 + 0.05), (x + corner_x * 0.15, y + corner_y * 0.15, z0 + 0.50), 0.025, 0.025, S.dark_iron)
    builder.add_box((x, y, z0 + 0.28), (0.25, 0.25, 0.42), slot=S.lamp_glass, yaw=math.radians(45))
    builder.add_cylinder((x, y, z0 + 0.50), (x, y, z0 + 0.72), 0.27, sides=4, slot=S.dark_iron, radius_end=0.04, caps=True)
    builder.add_cylinder((x, y, z0 + 0.72), (x, y, z0 + 0.80), 0.03, sides=6, slot=S.dark_iron)
    return (x, y, z0 + 0.28)


def lamp_light_position():
    """Where the lantern's glowing glass is (x, y, z) in metres, in case the assembler wants to put a real light there."""
    if 'lamp_glass' in LAST_BUILD_INFO:
        return tuple(LAST_BUILD_INFO['lamp_glass'])
    x, y = LAMP_POSITION
    return (x, y, mc.ground_height(x, y) + LAMP_HEIGHT - 0.55 + 0.28)


def build_props(plan, collection_name, rng):
    builder = mc.MeshBuilder(PROPS_OBJECT_NAME, prop_materials())
    add_timber_rack(plan, builder, rng)
    add_fence(plan, builder, rng)
    add_barrels(plan, builder, rng)
    add_handcart(plan, builder, rng)
    add_sleeper_pile(plan, builder, rng)
    LAST_BUILD_INFO['lamp_glass'] = tuple(float(v) for v in add_lamp_post(plan, builder))
    return builder.finish(collection_name)


def build_lumps(plan, collection_name, rng):
    builder = mc.MeshBuilder(LUMPS_OBJECT_NAME, clutter_materials())
    keep_clear = [(TIMBER_RACK['x'] - 1.0, 0.5 * (TIMBER_RACK['y_from'] + TIMBER_RACK['y_to']), 2.6),
                  (HANDCART['x'], HANDCART['y'], 1.9), (SLEEPER_PILE['x'], SLEEPER_PILE['y'], 2.0),
                  (LAMP_POSITION[0], LAMP_POSITION[1], 0.6)]
    keep_clear += [(bx, by, 0.6) for bx, by in BARREL_SPOTS]
    for heap in COAL_HEAPS:
        keep_clear.append((heap[0], heap[1], heap[2] * 1.15))
    scattered = scatter_lumps(plan, builder, rng, keep_clear)
    scattered += scatter_boulders(plan, builder, rng, keep_clear)
    for heap in COAL_HEAPS:
        add_coal_heap(plan, builder, rng, heap)
    return builder.finish(collection_name), scattered


# ====================================================================================================================
# The one function the assembler calls
# ====================================================================================================================
def ground_mesh_object():
    """The terrain object (so the assembler can find it, e.g. to set up displacement quality or to raycast onto it)."""
    return bpy.data.objects.get(GROUND_OBJECT_NAME)


def count_triangles(obj):
    return int(sum(len(p.vertices) - 2 for p in obj.data.polygons))


KNOWN_FLAWS = [
    'The mud picture repeats every 5 m; it is hidden by a second, shifted lookup mixed in by big noise patches, but a faint repeat of the painted puddle patches can still be seen from high above.',
    'The terrain is a rectangle (x -45..60, y -45..90) with hard edges: the hills / village / sky part must cover the rim, and the back bank is 8 m high at y = 90.',
    'Real displacement of the terrain is heavy: measured peak memory was about 1.8 GB at 540x960 and 4.7 GB at 1080x1920 (8 samples) with TERRAIN_DICING_PIXELS = 2; raise that number (3 or 4) if memory is short.',
    'Water sheets are perfectly flat and only faintly rippled; what they reflect depends entirely on the sky the assembler builds.',
    'The lamp post only has a glowing lantern (emission); it does not cast real light, put a point light at lamp_light_position() if a pool of light is wanted.',
    'The engine-house floor area is dug 7 cm below mc.ground_height (inside x -3.8..3.8, y 0.1..10.9) so a floor at ground level does not fight the mud; the engine house should have its own floor or it will see mud below the sleepers.',
    'Barrels, fence, handcart and sleepers are plain boxes and cylinders (chunky, no nails or bands); close up they are simpler than the headframe or engine house.',
    'Small pebbles are 20-80 triangle low-poly lumps; seen from closer than about 3 m the faceting shows.',
]


def build(collection_name='Mine'):
    """Builds the whole ground and yard part in world coordinates and returns {'objects': [names], 'notes': text}."""
    started = time.time()
    LAST_BUILD_INFO.clear()
    rng = np.random.default_rng(2024)
    plan = GroundPlan()
    mc.say(f'ground plan ready in {time.time() - started:.1f} s')
    terrain, squares = build_terrain(plan, collection_name)
    puddles, puddle_report = build_puddles(plan, collection_name)
    lumps, scattered = build_lumps(plan, collection_name, rng)
    props = build_props(plan, collection_name, rng)
    objects = [terrain, puddles, lumps, props]
    LAST_BUILD_INFO.update({
        'object_names': [o.name for o in objects],
        'triangles': {o.name: count_triangles(o) for o in objects},
        'puddles': puddle_report,
        'scattered_lumps': scattered,
        'terrain_squares': squares,
        'build_seconds': round(time.time() - started, 1),
    })
    notes = (f'Terrain object "{GROUND_OBJECT_NAME}" (mud, real displacement at {TERRAIN_DICING_PIXELS:g} px; ground_mesh_object() returns it), '
             f'"{PUDDLE_OBJECT_NAME}" ({len(puddle_report)} water sheets), "{LUMPS_OBJECT_NAME}" (coal and stones: {scattered} scattered + {len(COAL_HEAPS)} heaps), '
             f'"{PROPS_OBJECT_NAME}" (timber rack at x -9..-7 y -6..-3, fence x 10..20 y -4..6, 2 barrels, handcart, sleeper pile, lamp post). '
             f'Lantern glass is at {tuple(round(v, 2) for v in lamp_light_position())}.')
    return {'objects': [o.name for o in objects], 'notes': notes}
