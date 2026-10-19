# What this does: builds the railway track (two rusty I-section rails, brown cast-iron chairs and bolts, wooden sleepers,
# a bed of angular stones), three riveted rusty mine carts heaped with coal (one on the rails in front of the engine house
# doorway, one further along the curve, one tipped over beside the track with its coal spilled), and two coal heaps with
# scattered lumps near the right side of the track.
# Everything is made from the shared toolbox lib/mine_common.py (surfaces from the uploaded pictures and maps), in world
# coordinates, and seated on the yard ground with mc.ground_height(). The track follows the layout curve mc.track_point(t).
# Use: import this file and call build('Mine'); it returns {'objects': [names], 'notes': '...'}.
import math
import os
import sys
import time

import numpy as np

import bpy
import bmesh

LIBRARY_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib')
if LIBRARY_FOLDER not in sys.path:
    sys.path.insert(0, LIBRARY_FOLDER)
import mine_common as mc  # noqa: E402

# ---------------------------------------------------------------------------------------------------------------------
# Sizes (metres). Change these to change the look of the track and carts.
# ---------------------------------------------------------------------------------------------------------------------
RAIL_GAUGE = mc.LAYOUT['track_gauge']          # distance between the two rails' centres
HALF_GAUGE = RAIL_GAUGE / 2.0
DOORWAY_END_Y = 4.0                            # rails run inside the doorway up to this y

RAIL_SCALE = 1.45                              # makes the rails a little chunkier than a real mine rail so they read from far away
# rail cross-section as (sideways, up) points, going round counter-clockwise: foot, web, head
RAIL_PROFILE = np.array([
    (-0.065, 0.000), (0.065, 0.000), (0.065, 0.020), (0.016, 0.034), (0.016, 0.100), (0.040, 0.110), (0.040, 0.130),
    (0.028, 0.142), (-0.028, 0.142), (-0.040, 0.130), (-0.040, 0.110), (-0.016, 0.100), (-0.016, 0.034), (-0.065, 0.020),
]) * RAIL_SCALE
RAIL_HEIGHT = 0.142 * RAIL_SCALE
FOOT_HALF_WIDTH = 0.065 * RAIL_SCALE

SLEEPER_TOP_ABOVE_GROUND = 0.17                # nominal top of a sleeper above the smoothed ground along the track
RAIL_BASE_ABOVE_GROUND = 0.195                  # rail foot sits on the chair plates, a little above the sleeper tops
STONE_BED_TOP_ABOVE_GROUND = 0.075
SLEEPER_SPACING = 0.66
STONE_BED_HALF_WIDTH = 1.6

WHEEL_RADIUS = 0.26
WHEEL_BASE = 1.1                               # distance between the two axles
CART_BODY_BOTTOM, CART_BODY_TOP = 0.44, 1.16   # heights above the rail top
CART_BOTTOM_HALF_LENGTH, CART_TOP_HALF_LENGTH = 0.74, 0.88
CART_BOTTOM_HALF_WIDTH, CART_TOP_HALF_WIDTH = 0.44, 0.60
CART_WALL_THICKNESS = 0.03

# The headframe's four leg footings (square blocks at the corners of its base). Nothing of the track may touch them.
HEADFRAME_FOOTING_HALF_SIZE = 0.65             # assumed footing half size (0.4) plus a margin
HEADFRAME_FOOTING_CENTRES = [
    (mc.LAYOUT['headframe']['centre_x'] + sx * mc.LAYOUT['headframe']['base_half_x'],
     mc.LAYOUT['headframe']['centre_y'] + sy * mc.LAYOUT['headframe']['base_half_y'])
    for sx in (-1, 1) for sy in (-1, 1)]

# Parts of the metal picture that are plain rusty panel (no rivet rows or braces): (start u, start v, width, height) in picture units
METAL_PLAIN_WINDOWS = {'A': (0.15, 0.23, 0.36, 0.26), 'B': (0.66, 0.61, 0.32, 0.30)}


# ---------------------------------------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------------------------------------
def unit(vector):
    vector = np.asarray(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def lerp(a, b, fraction):
    return a + (b - a) * fraction


def rotation_about_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def random_rotation(rng):
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def newell_normal(points):
    points = np.asarray(points, dtype=float)
    following = np.roll(points, -1, axis=0)
    return np.cross(points, following).sum(axis=0)


def smooth_values(values, spacing, sigma):
    radius = max(1, int(3 * sigma / spacing))
    offsets = np.arange(-radius, radius + 1) * spacing
    kernel = np.exp(-0.5 * (offsets / sigma) ** 2)
    kernel /= kernel.sum()
    padded = np.pad(values, (radius, radius), mode='edge')
    return np.convolve(padded, kernel, mode='valid')


def ping_pong(value, low, high):
    """Walks back and forth between low and high, so a long strip can use a small plain part of the picture without seams."""
    width = high - low
    phase = (value / width) % 2.0
    return low + width * (1.0 - abs(phase - 1.0))


def add_polygon_facing(builder, points, slot, hint, texture=None):
    """One flat face that is turned so that it faces the 'hint' direction. texture: None (automatic picture coordinates) or
    {'axes': (u_direction, v_direction), 'window': (u, v), 'scale': metres per picture} to lay a chosen part of the picture on it."""
    points = np.asarray(points, dtype=float)
    if np.dot(newell_normal(points), hint) < 0:
        points = points[::-1]
    if texture is None:
        builder.add_polygon(points, slot=slot)
        return
    tile = float(builder.materials[slot].get('mine_tile_metres', 1.0))
    axis_u, axis_v = texture['axes']
    origin = points[0]
    scale = texture['scale']
    uv = [(float(np.dot(p - origin, axis_u)) * tile / scale, float(np.dot(p - origin, axis_v)) * tile / scale) for p in points]
    builder.add_polygon(points, slot=slot, uv_metres=uv, uv_shift=texture['window'])


def add_oriented_box(builder, centre, axis_x, axis_y, axis_z, half_sizes, slot, texture=None):
    """A box with its own three directions. texture: None, 'natural' (grain along the long direction, uses the material's own
    tile size) or a dict like add_polygon_facing's, which is then used for all six faces."""
    centre = np.asarray(centre, dtype=float)
    ax, ay, az = [np.asarray(a, dtype=float) for a in (axis_x, axis_y, axis_z)]
    hx, hy, hz = half_sizes

    def corner(sx, sy, sz):
        return centre + sx * hx * ax + sy * hy * ay + sz * hz * az

    faces = [
        ('top', [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], az, (ax, ay)),
        ('bottom', [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)], -az, (ax, ay)),
        ('end_plus', [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], ax, (ay, az)),
        ('end_minus', [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], -ax, (ay, az)),
        ('side_plus', [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], ay, (ax, az)),
        ('side_minus', [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], -ay, (ax, az)),
    ]
    for _name, corners, hint, natural_axes in faces:
        points = [corner(*c) for c in corners]
        if texture is None:
            face_texture = None
        elif isinstance(texture, dict) and 'natural_window' in texture:
            face_texture = {'axes': natural_axes, 'window': texture['natural_window'], 'scale': texture['scale']}
        else:
            face_texture = texture
        add_polygon_facing(builder, points, slot, hint, face_texture)


class PlacedBuilder:
    """Lets one shape be described in its own frame (a cart's own length / side / up) and lands it in the world.
    origin: where the frame's zero is in the world. rotation: 3x3 matrix whose columns are the frame's three directions."""

    def __init__(self, builder, origin, rotation):
        self.builder = builder
        self.origin = np.asarray(origin, dtype=float)
        self.rotation = np.asarray(rotation, dtype=float)

    def point(self, local):
        return self.origin + self.rotation @ np.asarray(local, dtype=float)

    def direction(self, local):
        return self.rotation @ np.asarray(local, dtype=float)

    def box(self, centre, size, slot=0, local_rotation=None):
        rotation = self.rotation if local_rotation is None else self.rotation @ local_rotation
        self.builder.add_box(self.point(centre), size, slot=slot, rotation=rotation)

    def oriented_box(self, centre, axes, half_sizes, slot, texture=None):
        world_axes = [self.direction(a) for a in axes]
        if isinstance(texture, dict) and 'axes' in texture:
            texture = dict(texture, axes=(self.direction(texture['axes'][0]), self.direction(texture['axes'][1])))
        add_oriented_box(self.builder, self.point(centre), *world_axes, half_sizes, slot, texture)

    def cylinder(self, start, end, radius, sides=10, slot=0, radius_end=None, caps=True):
        self.builder.add_cylinder(self.point(start), self.point(end), radius, sides=sides, slot=slot, radius_end=radius_end, caps=caps)

    def ring(self, centre, axis, outer_radius, inner_radius, thickness, sides=24, slot=0):
        self.builder.add_ring(self.point(centre), self.direction(axis), outer_radius, inner_radius, thickness, sides=sides, slot=slot)

    def beam(self, start, end, width, depth, slot=0, up_hint=(0.0, 0.0, 1.0)):
        self.builder.add_beam(self.point(start), self.point(end), width, depth, slot=slot, up_hint=self.direction(up_hint))

    def facing_polygon(self, local_points, slot, hint, texture=None):
        world_points = [self.point(p) for p in local_points]
        if texture is not None:
            texture = dict(texture, axes=(self.direction(texture['axes'][0]), self.direction(texture['axes'][1])))
        add_polygon_facing(self.builder, world_points, slot, self.direction(hint), texture)

    def chunk(self, centre, radii, local_rotation, template, slot=0):
        add_chunk(self.builder, self.point(centre), radii, self.rotation @ local_rotation, template, slot)

    def polygon_with_picture_coordinates(self, local_points, slot, hint, picture_uv):
        """A flat face with its picture coordinates (u, v in picture units) given point by point."""
        points = np.array([self.point(p) for p in local_points])
        picture_uv = list(picture_uv)
        if np.dot(newell_normal(points), self.direction(hint)) < 0:
            points = points[::-1]
            picture_uv = picture_uv[::-1]
        tile = float(self.builder.materials[slot].get('mine_tile_metres', 1.0))
        self.builder.add_polygon(points, slot=slot, uv_metres=[(u * tile, v * tile) for u, v in picture_uv])


# ---------------------------------------------------------------------------------------------------------------------
# Angular lumps (coal and stones): little convex shapes with flat faces, made once and reused in many sizes
# ---------------------------------------------------------------------------------------------------------------------
def convex_hull_solid(points):
    """The flat-faced solid that wraps a set of points: returns (vertices, faces) with every face turned outward."""
    points = np.asarray(points, dtype=float)
    mesh = bmesh.new()
    vertices = [mesh.verts.new(tuple(p)) for p in points]
    bmesh.ops.convex_hull(mesh, input=vertices)
    mesh.verts.index_update()
    used = sorted({v.index for f in mesh.faces for v in f.verts})
    remap = {old: new for new, old in enumerate(used)}
    hull_vertices = points[used]
    hull_faces = [[remap[v.index] for v in f.verts] for f in mesh.faces]
    mesh.free()
    centre = hull_vertices.mean(axis=0)
    fixed_faces = []
    for face in hull_faces:
        face_points = hull_vertices[face]
        if np.dot(newell_normal(face_points), face_points.mean(axis=0) - centre) < 0:
            face = face[::-1]
        fixed_faces.append(face)
    return hull_vertices, fixed_faces


def add_hull_solid(builder, points, slot=0):
    vertices, faces = convex_hull_solid(points)
    builder.add_indexed_faces(vertices, faces, slot=slot)


def make_chunk_templates(how_many, seed):
    """Angular lumps (coal, stones): each is the flat-faced solid around a squashed, jittered cube with a few extra points."""
    rng = np.random.default_rng(seed)
    templates = []
    for number in range(how_many):
        corners = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], dtype=float)
        if number % 2 == 0:          # blocky lump
            corners = corners * rng.uniform(0.7, 1.0, (8, 3)) + rng.uniform(-0.2, 0.2, (8, 3))
            extra_count = int(rng.integers(1, 4))
            extra_reach = (0.85, 1.1)
        else:                        # rough, irregular lump with a few sharp corners
            corners = corners * rng.uniform(0.5, 1.0, (8, 3)) + rng.uniform(-0.4, 0.4, (8, 3))
            extra_count = int(rng.integers(3, 6))
            extra_reach = (0.9, 1.35)
        extra = rng.normal(size=(extra_count, 3))
        extra = extra / np.linalg.norm(extra, axis=1, keepdims=True) * rng.uniform(extra_reach[0], extra_reach[1], (extra_count, 1))
        vertices, faces = convex_hull_solid(np.vstack([corners, extra]))
        vertices = vertices - vertices.mean(axis=0)
        vertices = vertices / np.abs(vertices).max()
        templates.append((vertices, faces))
    return templates


def add_hull_solid_placed(placed, local_points, slot=0):
    vertices, faces = convex_hull_solid(local_points)
    placed.builder.add_indexed_faces([placed.point(v) for v in vertices], faces, slot=slot)


def add_chunk(builder, centre, radii, rotation, template, slot=0):
    vertices, faces = template
    world = (vertices * np.asarray(radii, dtype=float)) @ np.asarray(rotation).T + np.asarray(centre, dtype=float)
    builder.add_indexed_faces(world, faces, slot=slot)


# ---------------------------------------------------------------------------------------------------------------------
# The track path: the layout curve, extended straight into the doorway, with a smoothed ground height along it
# ---------------------------------------------------------------------------------------------------------------------
class TrackPath:
    def __init__(self):
        samples = 4001
        t_values = np.linspace(0.0, 1.0, samples)
        self.t_values = t_values
        self.curve_x = np.array([mc.track_point(float(t))[0] for t in t_values])
        self.curve_y = np.array([mc.track_point(float(t))[1] for t in t_values])
        steps = np.hypot(np.diff(self.curve_x), np.diff(self.curve_y))
        self.cumulative = np.concatenate([[0.0], np.cumsum(steps)])
        self.length = float(self.cumulative[-1])
        start_x, start_y = mc.track_point(0.0)
        self.start_s = -(DOORWAY_END_Y - start_y)          # s < 0 is the straight bit inside the doorway
        spacing = 0.2
        self.height_spacing = spacing
        self.height_samples_s = np.arange(self.start_s, self.length + spacing, spacing)
        raw = np.array([mc.ground_height(*self.centre_xy(s)) for s in self.height_samples_s])
        self.smooth_height = smooth_values(raw, spacing, 1.3)   # smoothed so the rails never zig-zag

    def t_at(self, s):
        return float(np.interp(s, self.cumulative, self.t_values))

    def frame(self, s):
        """x, y and the unit direction (dx, dy) of the track centre line at distance s along it."""
        if s <= 0.0:
            start_x, start_y = mc.track_point(0.0)
            direction_x, direction_y = mc.track_direction(0.0)
            return start_x + direction_x * s, start_y + direction_y * s, direction_x, direction_y
        t = float(self.t_at(min(s, self.length)))
        x, y = mc.track_point(t)
        dx, dy = mc.track_direction(t)
        return x, y, dx, dy

    def centre_xy(self, s):
        x, y, _dx, _dy = self.frame(s)
        return x, y

    def side_xy(self, s, sideways):
        """Point 'sideways' metres to the left of the centre line (negative = right) at distance s."""
        x, y, dx, dy = self.frame(s)
        return x - dy * sideways, y + dx * sideways

    def inside_headframe_footing(self, x, y):
        return any(max(abs(x - cx), abs(y - cy)) < HEADFRAME_FOOTING_HALF_SIZE for cx, cy in HEADFRAME_FOOTING_CENTRES)

    def reach_limit(self, s, side_sign, wanted):
        """How far sideways (towards side_sign = +1 left or -1 right) things next to the track may reach at distance s
        before touching a headframe leg footing; never less than 0.9 m."""
        reach = wanted
        while reach > 0.9:
            x, y = self.side_xy(s, side_sign * reach)
            if not self.inside_headframe_footing(x, y):
                break
            reach -= 0.02
        return max(reach, 0.9)

    def bed_height(self, s):
        return float(np.interp(s, self.height_samples_s, self.smooth_height))

    def rail_base_height(self, s):
        return self.bed_height(s) + RAIL_BASE_ABOVE_GROUND

    def rail_top_height(self, s):
        return self.rail_base_height(s) + RAIL_HEIGHT


# ---------------------------------------------------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------------------------------------------------
def make_materials():
    m = {}
    m['sleeper_woods'] = [
        mc.surface_material('wood', tint=(0.95, 0.85, 0.75), true_displacement=True, splash=0.2),
        mc.surface_material('wood', tint=(0.72, 0.66, 0.62), true_displacement=True, splash=0.2),
        mc.surface_material('wood', tint=(1.15, 0.95, 0.78), true_displacement=True, splash=0.2),
    ]
    m['stone_bed'] = mc.surface_material('gravel', tint=(0.92, 0.88, 0.85), true_displacement=True, splash=0.12, variation=0.3)
    m['rail_metal'] = mc.surface_material('metal', tint=(2.1, 1.3, 0.85), splash=0.35, variation=0.25)
    m['rail_top'] = mc.plain_material('Rail top worn steel', (0.32, 0.20, 0.13), roughness=0.32, metallic=0.75)
    m['iron_brown'] = mc.plain_material('Cast iron chair brown', (0.17, 0.075, 0.04), roughness=0.55, metallic=0.35)
    m['iron_dark'] = mc.plain_material('Dark iron', (0.045, 0.036, 0.034), roughness=0.55, metallic=0.4)
    m['rivet_rust'] = mc.plain_material('Rivet rust', (0.22, 0.095, 0.045), roughness=0.5, metallic=0.4)
    m['stones'] = [
        mc.plain_material('Stone dark slate', (0.035, 0.04, 0.05), roughness=0.6),
        mc.plain_material('Stone blue grey', (0.075, 0.085, 0.105), roughness=0.55),
        mc.plain_material('Stone rusty ochre', (0.14, 0.062, 0.034), roughness=0.7),
        mc.plain_material('Stone warm grey', (0.10, 0.085, 0.072), roughness=0.65),
        mc.plain_material('Stone coal black', (0.014, 0.015, 0.019), roughness=0.4),
    ]
    m['cart_steels'] = [
        mc.surface_material('metal', tint=(1.9, 1.2, 0.85), variation=0.2),
        mc.surface_material('metal', tint=(1.55, 1.25, 1.05), variation=0.2),
        mc.surface_material('metal', tint=(2.2, 1.2, 0.75), variation=0.2),
        mc.surface_material('metal', tint=(2.8, 1.3, 0.65), variation=0.15),       # rim, straps: bright orange rust
        mc.surface_material('metal', tint=(2.3, 2.25, 1.95), variation=0.15),      # end plate: greyer, scratched
        mc.surface_material('metal', tint=(2.3, 1.15, 0.7), variation=0.15),       # wheels: rusty cast iron
    ]
    m['coals'] = [
        mc.plain_material('Coal black', (0.011, 0.012, 0.016), roughness=0.30),
        mc.plain_material('Coal blue sheen', (0.022, 0.026, 0.036), roughness=0.26),
        mc.plain_material('Coal grey worn', (0.036, 0.040, 0.050), roughness=0.38),
        mc.plain_material('Coal dust black', (0.008, 0.008, 0.010), roughness=0.9),
    ]
    return m


# ---------------------------------------------------------------------------------------------------------------------
# Sleepers
# ---------------------------------------------------------------------------------------------------------------------
def plan_sleepers(path, rng):
    """Positions along the track, with random size, small yaw and sink; some missing, some cracked."""
    positions = np.arange(path.start_s + 0.25, path.length - 0.1, SLEEPER_SPACING)
    count = len(positions)
    missing = {int(i) for i in (11, 19, 27, 36, 44) if i < count - 2}
    cracked = {int(i) for i in (6, 14, 22, 31, 40, 48) if i < count - 1 and i not in missing}
    plan = []
    for index, s in enumerate(positions):
        if index in missing:
            plan.append({'s': float(s), 'missing': True})
            continue
        plan.append({
            's': float(s + rng.uniform(-0.025, 0.025)),
            'missing': False,
            'cracked': index in cracked,
            'length': float(rng.uniform(1.62, 1.86)),
            'width': float(rng.uniform(0.26, 0.33)),
            'thickness': float(rng.uniform(0.15, 0.20)),
            'yaw': float(rng.uniform(-0.045, 0.045)),
            'shift': float(rng.uniform(-0.06, 0.06)),
            'sink': float(rng.uniform(0.0, 0.03)),
            'material_slot': int(rng.choice(3, p=[0.45, 0.3, 0.25])),
            'wood_offset': (float(rng.uniform(0, 1)), float(rng.uniform(0, 1))),
        })
        info = plan[-1]
        # keep the sleeper ends off the headframe leg footings
        left_end = min(info['shift'] + info['length'] / 2.0, path.reach_limit(info['s'], 1.0, 0.95) - 0.03)
        right_end = max(info['shift'] - info['length'] / 2.0, -(path.reach_limit(info['s'], -1.0, 0.95) - 0.03))
        info['length'] = float(left_end - right_end)
        info['shift'] = float((left_end + right_end) / 2.0)
    return plan


def add_one_sleeper_piece(builder, path, info, centre_across, length, rotate_extra, sink_extra, texture_offset):
    """A single wooden box lying across the track; centre_across = sideways position of the piece's middle."""
    s = info['s']
    x, y, dx, dy = path.frame(s)
    angle = math.atan2(dy, dx) + math.pi / 2.0 + info['yaw'] + rotate_extra     # direction across the track
    across = np.array([math.cos(angle), math.sin(angle), 0.0])
    along = np.array([-across[1], across[0], 0.0])          # Z x across
    up = np.array([0.0, 0.0, 1.0])
    top = path.bed_height(s) + SLEEPER_TOP_ABOVE_GROUND - info['sink'] - sink_extra
    centre = np.array([x, y, top - info['thickness'] / 2.0]) + across * (info['shift'] + centre_across)
    tile = float(builder.materials[info['material_slot']].get('mine_tile_metres', 1.2))
    add_oriented_box(builder, centre, across, along, up, (length / 2.0, info['width'] / 2.0, info['thickness'] / 2.0),
                     info['material_slot'], texture={'natural_window': texture_offset, 'scale': tile})


def build_sleepers(path, plan, materials, rng):
    builder = mc.MeshBuilder('Track sleepers', materials['sleeper_woods'])
    for info in plan:
        if info['missing']:
            continue
        if info['cracked']:
            gap = 0.035
            split = rng.uniform(-0.25, 0.25)       # where along the sleeper the crack falls (0 = middle)
            left_length = info['length'] / 2.0 + split - gap / 2.0
            right_length = info['length'] - left_length - gap
            left_centre = -info['length'] / 2.0 + left_length / 2.0
            right_centre = info['length'] / 2.0 - right_length / 2.0
            add_one_sleeper_piece(builder, path, info, left_centre, left_length, 0.0, 0.0, info['wood_offset'])
            add_one_sleeper_piece(builder, path, info, right_centre, right_length, rng.uniform(-0.05, 0.05), rng.uniform(0.0, 0.025),
                                  (info['wood_offset'][0] + 0.37, info['wood_offset'][1]))
        else:
            add_one_sleeper_piece(builder, path, info, 0.0, info['length'], 0.0, 0.0, info['wood_offset'])
    obj = builder.finish('Mine')
    mc.use_real_displacement(obj, 1.0)
    return obj


# ---------------------------------------------------------------------------------------------------------------------
# Stone bed
# ---------------------------------------------------------------------------------------------------------------------
def build_stone_bed(path, materials):
    spacing = 0.4
    s_values = np.arange(path.start_s, path.length + spacing * 0.5, spacing)
    sideways_values = [-STONE_BED_HALF_WIDTH, -1.3, -0.95, 0.0, 0.95, 1.3, STONE_BED_HALF_WIDTH]
    vertices = np.zeros((len(s_values), len(sideways_values), 3))
    squeeze = np.ones((len(s_values), 2))               # how much each side of each row is pulled in (1 = not at all)
    for i, s in enumerate(s_values):
        for side_index, side_sign in enumerate((-1.0, 1.0)):
            squeeze[i, side_index] = max(0.6, path.reach_limit(s, side_sign, STONE_BED_HALF_WIDTH) / STONE_BED_HALF_WIDTH)
    for column in range(2):                             # smooth the pull-in over neighbouring rows
        padded = np.pad(squeeze[:, column], 1, mode='edge')
        squeeze[:, column] = np.minimum(squeeze[:, column], np.minimum(padded[:-2], padded[2:]) + 0.08)
    for i, s in enumerate(s_values):
        bed = path.bed_height(s)
        for j, sideways in enumerate(sideways_values):
            if sideways != 0.0:
                sideways = sideways * squeeze[i, 0 if sideways < 0 else 1]
            x, y = path.side_xy(s, sideways)
            ground = mc.ground_height(x, y)
            distance = abs(sideways_values[j])
            if distance <= 0.95:
                z = bed + STONE_BED_TOP_ABOVE_GROUND
            elif distance < STONE_BED_HALF_WIDTH - 0.01:
                z = max(bed + STONE_BED_TOP_ABOVE_GROUND - 0.03, ground + 0.045)
            else:
                z = ground - 0.05
            vertices[i, j] = (x, y, z)
    columns = len(sideways_values)
    faces = []
    for i in range(len(s_values) - 1):
        for j in range(columns - 1):
            a = i * columns + j
            faces.append([a, a + columns, a + columns + 1, a + 1])
    builder = mc.MeshBuilder('Track stone bed', [materials['stone_bed']])
    builder.add_indexed_faces(vertices.reshape(-1, 3), faces, slot=0, uv_axes=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    obj = builder.finish('Mine')
    mc.use_real_displacement(obj, 1.0)
    return obj


# ---------------------------------------------------------------------------------------------------------------------
# Rails, fishplates, chairs and bolts
# ---------------------------------------------------------------------------------------------------------------------
def build_rails(path, materials):
    builder = mc.MeshBuilder('Track rails', [materials['rail_metal'], materials['rail_top']])
    tile = float(materials['rail_metal'].get('mine_tile_metres', 2.0))
    picture_scale = 3.0                                         # metres of rail per picture: shows a coarse rusty patch
    window_u_low, window_u_high = 0.66, 0.97
    window_v_low = 0.62
    edge_lengths = np.hypot(*(np.roll(RAIL_PROFILE, -1, axis=0) - RAIL_PROFILE).T)
    perimeter = np.concatenate([[0.0], np.cumsum(edge_lengths)])
    s_values = list(np.arange(path.start_s, path.length, 0.25)) + [path.length]
    corner_count = len(RAIL_PROFILE)
    for side_index, side in enumerate((-1.0, 1.0)):
        rings = []
        for s in s_values:
            x, y, dx, dy = path.frame(s)
            centre = np.array(path.side_xy(s, side * HALF_GAUGE) + (path.rail_base_height(s),))
            left = np.array([-dy, dx, 0.0])
            ring = np.array([centre + left * q + np.array([0.0, 0.0, h]) for q, h in RAIL_PROFILE])
            rings.append(ring)
        for i in range(len(s_values) - 1):
            u_a = ping_pong(s_values[i] / picture_scale + side_index * 0.11, window_u_low, window_u_high)
            u_b = ping_pong(s_values[i + 1] / picture_scale + side_index * 0.11, window_u_low, window_u_high)
            for k in range(corner_count):
                k2 = (k + 1) % corner_count
                v_a = window_v_low + perimeter[k] / picture_scale
                v_b = window_v_low + perimeter[k + 1] / picture_scale
                points = [rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]]
                uv = [(u_a * tile, v_a * tile), (u_a * tile, v_b * tile), (u_b * tile, v_b * tile), (u_b * tile, v_a * tile)]
                builder.add_polygon(points, slot=1 if k in (6, 7, 8) else 0, uv_metres=uv)
        end_uv = [((window_u_low + 0.05) * tile + p[0] * 2.0, (window_v_low + 0.05) * tile + p[1] * 2.0) for p in RAIL_PROFILE]
        builder.add_polygon(rings[-1], slot=0, uv_metres=end_uv)
        builder.add_polygon(rings[0][::-1], slot=0, uv_metres=end_uv[::-1])
    return builder.finish('Mine')


def build_chairs_and_fishplates(path, plan, materials, rng):
    builder = mc.MeshBuilder('Track chairs and bolts', [materials['iron_brown'], materials['iron_dark'], materials['rivet_rust']])
    up = np.array([0.0, 0.0, 1.0])
    hex_sides = 6
    for info in plan:
        if info['missing']:
            continue
        s = info['s']
        x, y, dx, dy = path.frame(s)
        tangent = np.array([dx, dy, 0.0])
        left = np.array([-dy, dx, 0.0])
        sleeper_top = path.bed_height(s) + SLEEPER_TOP_ABOVE_GROUND - info['sink']
        base_z = path.rail_base_height(s)
        plate_thickness = base_z - sleeper_top + 0.004
        for side in (-1.0, 1.0):
            rail_x, rail_y = path.side_xy(s, side * HALF_GAUGE)
            rail_foot = np.array([rail_x, rail_y, base_z])
            outside = left * side                          # pointing away from the track centre

            def on_chair(t, o, h):
                return rail_foot + tangent * t + outside * o + up * h

            # base plate under the rail foot
            plate_centre = np.array([rail_x, rail_y, sleeper_top + plate_thickness / 2.0])
            add_oriented_box(builder, plate_centre, tangent, outside, up, (0.15, FOOT_HALF_WIDTH + 0.04, plate_thickness / 2.0), 0)
            # wedge-shaped jaw on the outside of the foot, with two bolt heads
            near, far = FOOT_HALF_WIDTH + 0.012, FOOT_HALF_WIDTH + 0.08
            jaw = [on_chair(t, o, h) for t, o, h in (
                (-0.08, near, 0.0), (0.08, near, 0.0), (-0.08, far, 0.0), (0.08, far, 0.0),
                (-0.06, near, 0.085), (0.06, near, 0.085), (-0.06, near + 0.04, 0.07), (0.06, near + 0.04, 0.07))]
            add_hull_solid(builder, jaw, 0)
            for along in (-0.032, 0.032):
                bolt_start = on_chair(along, near + 0.02, 0.082)
                builder.add_cylinder(bolt_start, bolt_start + up * 0.022, 0.019, sides=hex_sides, slot=2)
            # hook clip lying over the outer edge of the foot, and a smaller clip and jaw on the inside
            add_oriented_box(builder, on_chair(0.0, FOOT_HALF_WIDTH - 0.02, 0.02 * RAIL_SCALE + 0.014), tangent, outside, up, (0.045, 0.035, 0.014), 0)
            add_oriented_box(builder, on_chair(0.0, -FOOT_HALF_WIDTH + 0.02, 0.02 * RAIL_SCALE + 0.014), tangent, outside, up, (0.045, 0.035, 0.014), 0)
            add_oriented_box(builder, on_chair(0.0, -(FOOT_HALF_WIDTH + 0.035), 0.03), tangent, outside, up, (0.055, 0.02, 0.03), 0)
    # fishplates (bolted joint plates) every few metres, on both sides of each rail's web
    for index in range(5, len(plan) - 3, 8):
        info = plan[index]
        for side in (-1.0, 1.0):
            s = info['s'] + SLEEPER_SPACING / 2.0 + (0.0 if side < 0 else 2 * SLEEPER_SPACING)
            x, y, dx, dy = path.frame(s)
            tangent = np.array([dx, dy, 0.0])
            left = np.array([-dy, dx, 0.0])
            rail_x, rail_y = path.side_xy(s, side * HALF_GAUGE)
            plate_height_centre = path.rail_base_height(s) + 0.067 * RAIL_SCALE
            for face in (-1.0, 1.0):
                offset = face * (0.016 * RAIL_SCALE + 0.007)
                centre = np.array([rail_x, rail_y, plate_height_centre]) + left * offset
                add_oriented_box(builder, centre, tangent, left, up, (0.26, 0.008, 0.033 * RAIL_SCALE), 1)
                if face > 0:
                    for bolt_along, bolt_up in ((-0.15, 0.015), (-0.05, -0.015), (0.05, 0.015), (0.15, -0.015)):
                        start = centre + tangent * bolt_along + up * bolt_up + left * 0.008
                        builder.add_cylinder(start, start + left * 0.022, 0.018, sides=hex_sides, slot=2)
    return builder.finish('Mine')


# ---------------------------------------------------------------------------------------------------------------------
# Loose stones on and beside the stone bed
# ---------------------------------------------------------------------------------------------------------------------
def build_loose_stones(path, plan, materials, templates, rng, count=2600):
    """Loose angular stones lying between and beside the sleepers and along the edges of the stone bed."""
    builder = mc.MeshBuilder('Track loose stones', materials['stones'])
    sleeper_s = np.array([info['s'] for info in plan if not info['missing']])
    slot_weights = np.array([0.3, 0.28, 0.17, 0.15, 0.10])
    placed = 0
    attempts = 0
    while placed < count and attempts < count * 8:
        attempts += 1
        s = rng.uniform(path.start_s + 0.3, path.length - 0.2)
        zone = rng.random()
        if zone < 0.45:
            sideways = rng.uniform(-0.5, 0.5)
            size = rng.uniform(0.014, 0.042)
        elif zone < 0.8:
            sideways = rng.choice([-1, 1]) * rng.uniform(0.62, 1.2)
            size = rng.uniform(0.016, 0.05)
        else:
            sideways = rng.choice([-1, 1]) * rng.uniform(1.15, 1.58)
            size = rng.uniform(0.024, 0.07)
        if abs(abs(sideways) - HALF_GAUGE) < 0.1:      # keep the rail feet clear
            continue
        if (np.abs(sleeper_s - s) < (0.15 + size)).any() and abs(sideways) < 0.95:
            continue
        x, y = path.side_xy(s, sideways)
        if path.inside_headframe_footing(x, y):
            continue
        bed = path.bed_height(s)
        if abs(sideways) <= 0.95:
            surface = bed + STONE_BED_TOP_ABOVE_GROUND
        elif abs(sideways) < 1.4:
            surface = max(bed + STONE_BED_TOP_ABOVE_GROUND - 0.03 * min(1.0, (abs(sideways) - 0.95) / 0.35), mc.ground_height(x, y) + 0.045)
        else:
            surface = mc.ground_height(x, y) + 0.01
        radii = np.array([size * rng.uniform(0.8, 1.4), size * rng.uniform(0.8, 1.4), size * rng.uniform(0.45, 0.8)])
        add_chunk(builder, (x, y, surface + radii[2] * 0.3), radii, random_rotation(rng), templates[int(rng.integers(len(templates)))],
                  slot=int(rng.choice(5, p=slot_weights)))
        placed += 1
    return builder.finish('Mine')


# ---------------------------------------------------------------------------------------------------------------------
# The mine cart
# ---------------------------------------------------------------------------------------------------------------------
def cart_half_length(z):
    return lerp(CART_BOTTOM_HALF_LENGTH, CART_TOP_HALF_LENGTH, (z - CART_BODY_BOTTOM) / (CART_BODY_TOP - CART_BODY_BOTTOM))


def cart_half_width(z):
    return lerp(CART_BOTTOM_HALF_WIDTH, CART_TOP_HALF_WIDTH, (z - CART_BODY_BOTTOM) / (CART_BODY_TOP - CART_BODY_BOTTOM))


def cart_surface_point(sign_x, sign_y, z, push=0.0):
    """A point on the cart's outer wall (push moves it out from the wall)."""
    return np.array([sign_x * (cart_half_length(z) + push), sign_y * (cart_half_width(z) + push), z])


# which way each of the four walls faces: (corner signs at one end, corner signs at the other, outward direction, direction along the wall)
CART_WALLS = [
    ('front end', (1, -1), (1, 1), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ('left side', (1, 1), (-1, 1), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    ('back end', (-1, 1), (-1, -1), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ('right side', (-1, -1), (1, -1), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
]


def metal_window_texture(axis_along, up_along_wall, length, height, window_name, rng):
    u0, v0, width, window_height = METAL_PLAIN_WINDOWS[window_name]
    scale = max(length / (width * 0.92), height / (window_height * 0.92))
    return {'axes': (axis_along, up_along_wall), 'window': (u0 + rng.uniform(0, 0.02), v0 + rng.uniform(0, 0.02)), 'scale': scale}


def wall_band(placed_steel, slot, z_low, z_high, push_low, push_high, rng, window_name='A'):
    """Outer faces of a ring-shaped band around the cart's walls between two heights."""
    for _name, corner_a, corner_b, outward, along in CART_WALLS:
        points = [cart_surface_point(*corner_a, z_low, push_low), cart_surface_point(*corner_b, z_low, push_low),
                  cart_surface_point(*corner_b, z_high, push_high), cart_surface_point(*corner_a, z_high, push_high)]
        length = float(np.linalg.norm(points[1] - points[0]))
        height = float(np.linalg.norm(points[3] - points[0]))
        up_along_wall = unit(0.5 * (points[2] + points[3]) - 0.5 * (points[0] + points[1]))
        texture = metal_window_texture(np.array(along), up_along_wall, length, height, window_name, rng)
        placed_steel.facing_polygon(points, slot, outward, texture)


def flat_ring(placed, slot, z, push_outer, push_inner, hint, rng, window_name='B'):
    """A flat horizontal ring (like the top lip of the rim) at height z between two distances from the wall."""
    for _name, corner_a, corner_b, outward, along in CART_WALLS:
        points = [cart_surface_point(*corner_a, z, push_outer), cart_surface_point(*corner_b, z, push_outer),
                  cart_surface_point(*corner_b, z, push_inner), cart_surface_point(*corner_a, z, push_inner)]
        texture = metal_window_texture(np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), 1.8, 1.2, window_name, rng)
        placed.facing_polygon(points, slot, hint, texture)


def build_cart_shell(steel, iron, body_slot, rng):
    z0, z1 = CART_BODY_BOTTOM, CART_BODY_TOP
    # outer walls (rusty riveted steel)
    wall_band(steel, body_slot, z0, z1 - 0.1, 0.0, 0.0, rng, 'A')
    # inner walls, floor and underside (dark iron, mostly hidden by coal)
    thickness = CART_WALL_THICKNESS
    for _name, corner_a, corner_b, outward, along in CART_WALLS:
        points = [cart_surface_point(*corner_a, z0 + thickness, -thickness), cart_surface_point(*corner_b, z0 + thickness, -thickness),
                  cart_surface_point(*corner_b, z1 - 0.06, -thickness), cart_surface_point(*corner_a, z1 - 0.06, -thickness)]
        iron.facing_polygon(points, 1, tuple(-np.array(outward)))
    floor = [cart_surface_point(sx, sy, z0 + thickness, -thickness) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    iron.facing_polygon(floor, 1, (0.0, 0.0, 1.0))
    underside = [cart_surface_point(sx, sy, z0, 0.0) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    iron.facing_polygon(underside, 1, (0.0, 0.0, -1.0))
    # flared top rim: a band that leans outward, a flat lip on top, and the underside of the overhang
    rim_low, rim_high = z1 - 0.15, z1
    wall_band(steel, 3, rim_low, rim_high, 0.02, 0.075, rng, 'B')
    flat_ring(steel, 3, rim_high, 0.075, -0.05, (0.0, 0.0, 1.0), rng, 'B')
    flat_ring(steel, 3, rim_low, 0.02, 0.0, (0.0, 0.0, -1.0), rng, 'B')
    for _name, corner_a, corner_b, outward, along in CART_WALLS:
        points = [cart_surface_point(*corner_a, rim_high, -0.05), cart_surface_point(*corner_b, rim_high, -0.05),
                  cart_surface_point(*corner_b, rim_high - 0.06, -0.05), cart_surface_point(*corner_a, rim_high - 0.06, -0.05)]
        iron.facing_polygon(points, 1, tuple(-np.array(outward)))
    # bottom angle band
    wall_band(steel, 3, z0, z0 + 0.1, 0.022, 0.022, rng, 'B')
    flat_ring(steel, 3, z0 + 0.1, 0.022, 0.0, (0.0, 0.0, 1.0), rng, 'B')
    flat_ring(steel, 3, z0, 0.022, 0.0, (0.0, 0.0, -1.0), rng, 'B')


def add_rivet_row(iron, start, end, direction_out, spacing, radius=0.021, height=0.02):
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    count = max(1, int(round(np.linalg.norm(end - start) / spacing)))
    out = unit(direction_out)
    for k in range(count + 1):
        point = start + (end - start) * (k / count)
        iron.cylinder(point - out * 0.002, point + out * height, radius, sides=6, slot=2)


def build_cart_details(steel, iron, rng):
    z1 = CART_BODY_TOP
    # rivet rows along the rim band and the bottom angle
    for _name, corner_a, corner_b, outward, along in CART_WALLS:
        out = unit(np.array(outward) + np.array([0, 0, -0.35]))
        a = cart_surface_point(*corner_a, z1 - 0.075, 0.05)
        b = cart_surface_point(*corner_b, z1 - 0.075, 0.05)
        inset = unit(b - a) * 0.09
        add_rivet_row(iron, a + inset, b - inset, np.array(outward) * 0.9 + np.array([0, 0, 0.1]), 0.2)
        a2 = cart_surface_point(*corner_a, CART_BODY_BOTTOM + 0.05, 0.022)
        b2 = cart_surface_point(*corner_b, CART_BODY_BOTTOM + 0.05, 0.022)
        inset2 = unit(b2 - a2) * 0.09
        add_rivet_row(iron, a2 + inset2, b2 - inset2, outward, 0.26, radius=0.019, height=0.017)
    # end plates with a frame and four rivets, and a vertical strap at each edge of the end panels
    for sign_x in (1.0, -1.0):
        z_mid = 0.78
        slope = (CART_TOP_HALF_LENGTH - CART_BOTTOM_HALF_LENGTH) / (CART_BODY_TOP - CART_BODY_BOTTOM)
        normal = unit((sign_x, 0.0, -slope))
        along_panel = unit((sign_x * slope, 0.0, 1.0))
        sideways = np.array([0.0, 1.0, 0.0])
        panel_centre = cart_surface_point(sign_x, 0.0, z_mid, 0.012)
        plate_texture = {'axes': (sideways, along_panel), 'window': (METAL_PLAIN_WINDOWS['B'][0] + 0.02, METAL_PLAIN_WINDOWS['B'][1] + 0.01), 'scale': 3.0}
        steel.oriented_box(panel_centre, (sideways, normal, along_panel), (0.37, 0.012, 0.17), 4, plate_texture)
        frame_texture = {'axes': (sideways, along_panel), 'window': (METAL_PLAIN_WINDOWS['A'][0], METAL_PLAIN_WINDOWS['A'][1]), 'scale': 3.0}
        for offset_up, size in ((0.19, (0.41, 0.018, 0.022)), (-0.19, (0.41, 0.018, 0.022))):
            steel.oriented_box(panel_centre + along_panel * offset_up + normal * 0.006, (sideways, normal, along_panel), size, 3, frame_texture)
        for offset_side in (0.405, -0.405):
            steel.oriented_box(panel_centre + sideways * offset_side + normal * 0.006, (sideways, normal, along_panel), (0.022, 0.018, 0.19), 3, frame_texture)
        for corner_y in (0.34, -0.34):
            for corner_up in (0.13, -0.13):
                point = panel_centre + sideways * corner_y + along_panel * corner_up + normal * 0.018
                iron.cylinder(point, point + normal * 0.022, 0.022, sides=6, slot=2)
        # straps along the two vertical edges of the end panel
        for sign_y in (1.0, -1.0):
            strap_centre = cart_surface_point(sign_x, sign_y, 0.74, 0.014) - sideways * sign_y * 0.075
            strap_texture = {'axes': (sideways, along_panel), 'window': (METAL_PLAIN_WINDOWS['B'][0], METAL_PLAIN_WINDOWS['B'][1] + 0.1), 'scale': 3.0}
            steel.oriented_box(strap_centre, (sideways, normal, along_panel), (0.052, 0.015, 0.26), 3, strap_texture)
            for rivet_up in (-0.2, -0.07, 0.07, 0.2):
                point = strap_centre + along_panel * rivet_up + normal * 0.012
                iron.cylinder(point, point + normal * 0.022, 0.021, sides=6, slot=2)
    # triangular corner brackets (gussets) low on the side walls near the corners, like the ones in the picture
    for sign_y in (1.0, -1.0):
        for sign_x in (1.0, -1.0):
            z_corner = CART_BODY_BOTTOM + 0.2
            x_corner = sign_x * (cart_half_length(z_corner) - 0.02)
            outward_y = np.array([0.0, sign_y, 0.0])
            triangle = []
            for inward, z in ((0.0, z_corner + 0.12), (0.0, z_corner - 0.17), (0.27, z_corner - 0.17)):
                triangle.append(np.array([x_corner - sign_x * inward, sign_y * (cart_half_width(z) + 0.004), z]))
            add_hull_solid_placed(iron, triangle + [p + outward_y * 0.028 for p in triangle], 0)


def build_cart_undercarriage(steel, iron, wheel_phase, rng):
    # axles, chassis beams, axle boxes, drawbar and couplings (cast iron / dark iron)
    for axle_x in (WHEEL_BASE / 2.0, -WHEEL_BASE / 2.0):
        iron.cylinder((axle_x, -HALF_GAUGE - 0.1, WHEEL_RADIUS), (axle_x, HALF_GAUGE + 0.1, WHEEL_RADIUS), 0.034, sides=10, slot=1)
        for side in (1.0, -1.0):
            iron.box((axle_x, side * 0.40, 0.355), (0.24, 0.07, 0.10), slot=1)      # axle box on the chassis beam
    for side in (1.0, -1.0):
        iron.box((0.0, side * 0.38, 0.415), (1.7, 0.08, 0.075), slot=1)              # chassis beam under the floor
    iron.box((0.0, 0.0, 0.40), (1.9, 0.12, 0.07), slot=1)                            # drawbar
    for sign_x in (1.0, -1.0):
        x = sign_x * 0.86
        z = 0.31
        iron.box((x - sign_x * 0.01, 0.0, z + 0.07), (0.1, 0.14, 0.1), slot=0)
        iron.box((x, 0.0, z + 0.085), (0.08, 0.24, 0.035), slot=0)
        iron.box((x, 0.0, z - 0.085), (0.08, 0.24, 0.035), slot=0)
        for side in (1.0, -1.0):
            iron.box((x, side * 0.1025, z), (0.08, 0.035, 0.2), slot=0)
        iron.cylinder((x - sign_x * 0.03, 0.0, z), (x + sign_x * 0.06, 0.0, z), 0.048, sides=10, slot=1)
    # wheels
    for axle_index, axle_x in enumerate((WHEEL_BASE / 2.0, -WHEEL_BASE / 2.0)):
        for side in (1.0, -1.0):
            add_wheel(steel, iron, axle_x, side, wheel_phase + 0.3 * axle_index + (0.2 if side > 0 else 0.0), rng)


def add_textured_wheel_ring(placed, centre, outer_radius, inner_radius, y_low, y_high, slot, window, scale, sides=28):
    """A ring (tread or flange of a wheel, axle along the cart's side-to-side direction) that shows a rusty part of the metal picture."""
    u0, v0 = window
    step = 2.0 * math.pi / sides

    def point(radius, angle, y):
        return np.array([centre[0] + radius * math.cos(angle), y, centre[2] + radius * math.sin(angle)])

    for i in range(sides):
        a0, a1 = i * step, (i + 1) * step
        middle = 0.5 * (a0 + a1)
        radial = (math.cos(middle), 0.0, math.sin(middle))
        for radius, hint in ((outer_radius, radial), (inner_radius, tuple(-np.array(radial)))):
            points = [point(radius, a0, y_low), point(radius, a1, y_low), point(radius, a1, y_high), point(radius, a0, y_high)]
            uv = [(u0 + a0 * radius / scale, v0), (u0 + a1 * radius / scale, v0), (u0 + a1 * radius / scale, v0 + (y_high - y_low) / scale),
                  (u0 + a0 * radius / scale, v0 + (y_high - y_low) / scale)]
            placed.polygon_with_picture_coordinates(points, slot, hint, uv)
        for y, hint in ((y_high, (0.0, 1.0, 0.0)), (y_low, (0.0, -1.0, 0.0))):
            points = [point(outer_radius, a0, y), point(outer_radius, a1, y), point(inner_radius, a1, y), point(inner_radius, a0, y)]
            uv = [(u0 + (p[0] - centre[0]) / scale, v0 + (p[2] - centre[2]) / scale) for p in points]
            placed.polygon_with_picture_coordinates(points, slot, hint, uv)


def add_wheel(steel, iron, axle_x, side, phase, rng):
    centre = np.array([axle_x, side * HALF_GAUGE, WHEEL_RADIUS])
    axis = np.array([0.0, 1.0, 0.0])
    window_name = 'A' if rng.random() < 0.5 else 'B'
    u0, v0, width, height = METAL_PLAIN_WINDOWS[window_name]
    window = (u0 + rng.uniform(0.0, 0.02), v0 + rng.uniform(0.0, 0.02))
    scale = 2.0 * math.pi * WHEEL_RADIUS / (width * 0.9)
    yc = centre[1]
    add_textured_wheel_ring(steel, centre, WHEEL_RADIUS, WHEEL_RADIUS - 0.055, yc - 0.06, yc + 0.06, 5, window, scale)       # tread
    flange_y = yc - side * 0.07
    add_textured_wheel_ring(steel, centre, WHEEL_RADIUS + 0.04, WHEEL_RADIUS - 0.03, flange_y - 0.01, flange_y + 0.01, 5, window, scale)  # flange on the inside
    iron.ring(centre - axis * side * 0.045, axis, WHEEL_RADIUS - 0.03, 0.06, 0.02, sides=24, slot=1)          # dark back disc (rim to hub)
    iron.cylinder(centre - axis * side * 0.06, centre + axis * side * 0.075, 0.058, sides=12, slot=0)        # hub
    iron.cylinder(centre + axis * side * 0.075, centre + axis * side * 0.105, 0.042, sides=12, slot=1)       # hub cap
    for spoke in range(8):
        angle = phase + spoke * math.pi / 4.0
        direction = np.array([math.cos(angle), 0.0, math.sin(angle)])
        iron.beam(centre + direction * 0.05 + axis * side * 0.02, centre + direction * (WHEEL_RADIUS - 0.05) + axis * side * 0.02,
                  0.032, 0.05, slot=0, up_hint=(0.0, 1.0, 0.0))


def random_lump_size(rng):
    """Coal comes in many sizes: mostly medium lumps, some small bits and a few big blocks."""
    pick = rng.random()
    if pick < 0.12:
        return rng.uniform(0.04, 0.065)
    if pick < 0.62:
        return rng.uniform(0.07, 0.12)
    if pick < 0.9:
        return rng.uniform(0.12, 0.19)
    return rng.uniform(0.19, 0.28)


def chunk_radii(rng, size, flatten=1.0):
    """Radii of a lump (length, width, height). flatten < 1 makes lumps that lie on the ground flatter."""
    radii = size * rng.uniform(0.7, 1.25, 3)
    radii[2] *= flatten
    return radii


def fill_cart_with_heaped_coal(coal, templates, rng):
    """Coal heaped above the rim: a black filler under a top layer and a deeper layer of angular lumps."""
    coal.box((0.0, 0.0, 0.76), (1.4, 0.86, 0.55), slot=3)
    hl, hw = 0.80, 0.50
    for layer, drop in ((0, 0.0), (1, 0.2)):
        x_values = np.arange(-hl + 0.1, hl - 0.05, 0.19)
        y_values = np.arange(-hw + 0.1, hw - 0.05, 0.19)
        for x0 in x_values:
            for y0 in y_values:
                x = x0 + rng.uniform(-0.06, 0.06)
                y = y0 + rng.uniform(-0.06, 0.06)
                dome = max(0.0, 1.0 - (x / (hl + 0.1)) ** 2) ** 0.75 * max(0.0, 1.0 - (y / (hw + 0.1)) ** 2) ** 0.75
                top = 1.04 + 0.36 * dome + rng.uniform(-0.05, 0.07) - drop
                size = min(random_lump_size(rng), 0.2) * 1.15
                radii = chunk_radii(rng, size)
                z_here = top - radii[2] * 0.55
                limit_x = cart_half_length(min(z_here, CART_BODY_TOP)) - CART_WALL_THICKNESS - radii.max() * 1.3
                limit_y = cart_half_width(min(z_here, CART_BODY_TOP)) - CART_WALL_THICKNESS - radii.max() * 1.3
                x, y = float(np.clip(x, -limit_x, limit_x)), float(np.clip(y, -limit_y, limit_y))
                coal.chunk((x, y, z_here), radii, random_rotation(rng), templates[int(rng.integers(len(templates)))],
                           slot=int(rng.choice(3, p=[0.45, 0.3, 0.25])))


def fill_cart_with_tipped_coal(coal, templates, rng, gravity_local):
    """A thin pile resting against the cart's lowest wall (the cart is tipped over, most of its coal is out)."""
    down = unit(gravity_local)
    lowest = -1e9
    corners = np.array([[sx * 0.8, sy * 0.5, z] for sx in (-1, 1) for sy in (-1, 1) for z in (0.5, 1.08)])
    low_value = (corners @ down).max()                         # how far "down" the lowest corner is
    placed = 0
    attempts = 0
    while placed < 60 and attempts < 4000:
        attempts += 1
        p = np.array([rng.uniform(-0.78, 0.78), rng.uniform(-0.5, 0.5), rng.uniform(0.52, 1.08)])
        depth_above_floor = low_value - float(p @ down)
        if depth_above_floor > 0.16 + rng.uniform(0.0, 0.14):
            continue
        size = rng.uniform(0.07, 0.14)
        radii = chunk_radii(rng, size)
        coal.chunk(p, radii, random_rotation(rng), templates[int(rng.integers(len(templates)))], slot=int(rng.choice(3, p=[0.45, 0.3, 0.25])))
        placed += 1


def build_one_cart(parts, origin, rotation, body_slot, templates, rng, coal_mode, gravity_local=None):
    steel = PlacedBuilder(parts['steel'], origin, rotation)
    iron = PlacedBuilder(parts['iron'], origin, rotation)
    coal = PlacedBuilder(parts['coal'], origin, rotation)
    build_cart_shell(steel, iron, body_slot, rng)
    build_cart_details(steel, iron, rng)
    build_cart_undercarriage(steel, iron, rng.uniform(0, math.pi / 4.0), rng)
    if coal_mode == 'heaped':
        fill_cart_with_heaped_coal(coal, templates, rng)
    elif coal_mode == 'tipped':
        fill_cart_with_tipped_coal(coal, templates, rng, gravity_local)


def cart_frame_on_track(path, centre_s):
    """Where a cart centred at distance centre_s along the track stands: origin on the rail tops, orientation along the rails."""
    back = path.centre_xy(centre_s - WHEEL_BASE / 2.0) + (path.rail_top_height(centre_s - WHEEL_BASE / 2.0),)
    front = path.centre_xy(centre_s + WHEEL_BASE / 2.0) + (path.rail_top_height(centre_s + WHEEL_BASE / 2.0),)
    back, front = np.array(back), np.array(front)
    forward = unit(front - back)
    left = unit(np.cross([0.0, 0.0, 1.0], forward))
    up = np.cross(forward, left)
    return (back + front) / 2.0, np.stack([forward, left, up], axis=1)


def find_s_for_y(path, target_y):
    s_values = np.linspace(0.0, path.length, 2000)
    ys = np.array([path.centre_xy(s)[1] for s in s_values])
    return float(s_values[np.argmin(np.abs(ys - target_y))])


def tipped_cart_pose(x, y, yaw, roll):
    """Orientation of a cart lying tipped over (rolled about its length) and the height that makes its lowest point touch the ground."""
    rotation = mc.rotation_from_yaw(yaw) @ rotation_about_x(roll)
    support_points = []
    for sign_x in (1, -1):
        for sign_y in (1, -1):
            support_points.append((sign_x * (CART_TOP_HALF_LENGTH + 0.075), sign_y * (CART_TOP_HALF_WIDTH + 0.075), CART_BODY_TOP))
    for axle_x in (WHEEL_BASE / 2.0, -WHEEL_BASE / 2.0):
        for side in (1.0, -1.0):
            for angle in np.linspace(0, 2 * math.pi, 24, endpoint=False):
                for lateral in (side * HALF_GAUGE - side * 0.05, side * HALF_GAUGE + side * 0.095):
                    support_points.append((axle_x + (WHEEL_RADIUS + 0.04) * math.cos(angle), lateral, WHEEL_RADIUS + (WHEEL_RADIUS + 0.04) * math.sin(angle)))
    lowest = min((rotation @ np.array(p))[2] for p in support_points)
    origin = np.array([x, y, mc.ground_height(x, y) - lowest - 0.03])
    return origin, rotation


def add_spilled_coal(coal_builder, templates, rng, origin, rotation, count=130):
    """Coal that has slid out of the tipped cart's mouth and fans out over the ground."""
    mouth_direction = rotation @ np.array([0.0, 0.0, 1.0])
    mouth_centre = origin + rotation @ np.array([0.0, 0.0, 1.1])
    flat = np.array([mouth_direction[0], mouth_direction[1]])
    flat /= np.linalg.norm(flat)
    for _ in range(count):
        distance = 0.35 + 2.4 * rng.random() ** 1.1
        spread = rng.normal(0.0, 0.3 + 0.12 * distance)
        direction = np.array([flat[0] * math.cos(spread) - flat[1] * math.sin(spread), flat[0] * math.sin(spread) + flat[1] * math.cos(spread)])
        x, y = mouth_centre[0] + direction[0] * distance, mouth_centre[1] + direction[1] * distance
        size = random_lump_size(rng) * (1.2 - 0.3 * min(distance, 2.5) / 2.5)
        radii = chunk_radii(rng, size, 0.75)
        add_chunk(coal_builder, (x, y, mc.ground_height(x, y) + radii[2] * 0.45), radii, random_rotation(rng),
                  templates[int(rng.integers(len(templates)))], slot=int(rng.choice(3, p=[0.45, 0.3, 0.25])))


# ---------------------------------------------------------------------------------------------------------------------
# Coal heaps and scattered lumps
# ---------------------------------------------------------------------------------------------------------------------
def add_coal_heap(coal_builder, templates, rng, centre_x, centre_y, radius_x, radius_y, height, lump_count, yaw):
    cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
    phases = rng.uniform(0, 2 * math.pi, 3)
    ground_centre = mc.ground_height(centre_x, centre_y)
    # a smooth dark core so no gaps show between lumps
    core_rotation = mc.rotation_from_yaw(yaw)
    coal_builder.add_blob((centre_x, centre_y, ground_centre - 0.05), (radius_x * 0.8, radius_y * 0.8, height * 0.88), slot=3, subdivisions=2,
                          rotation=core_rotation, jitter=0.06, seed=int(rng.integers(1 << 30)))
    for _ in range(lump_count):
        angle = rng.uniform(0, 2 * math.pi)
        edge = 1.0 + 0.16 * math.sin(2 * angle + phases[0]) + 0.1 * math.sin(3 * angle + phases[1])
        unit_radius = math.sqrt(rng.random()) * 1.05
        local_x = math.cos(angle) * unit_radius * radius_x * edge
        local_y = math.sin(angle) * unit_radius * radius_y * edge
        x = centre_x + local_x * cos_yaw - local_y * sin_yaw
        y = centre_y + local_x * sin_yaw + local_y * cos_yaw
        relative = min(1.0, unit_radius)
        surface = height * max(0.0, 1.0 - relative ** 1.7) * (1.0 + 0.08 * math.sin(5 * angle + phases[2]))
        size = random_lump_size(rng) * 1.05
        radii = chunk_radii(rng, size)
        z = mc.ground_height(x, y) + surface + rng.uniform(-0.03, 0.04) - radii[2] * 0.35
        add_chunk(coal_builder, (x, y, z), radii, random_rotation(rng), templates[int(rng.integers(len(templates)))],
                  slot=int(rng.choice(3, p=[0.45, 0.3, 0.25])))


def add_scattered_lumps(coal_builder, templates, rng, path, centres, count):
    """Single lumps lying around the heaps, thinning out with distance, and never on the track bed."""
    sample_s = np.arange(0.0, path.length, 0.25)
    track_points = np.array([path.centre_xy(s) for s in sample_s])
    placed = 0
    attempts = 0
    while placed < count and attempts < count * 20:
        attempts += 1
        cx, cy, spread = centres[int(rng.integers(len(centres)))]
        x = cx + rng.normal(0.0, spread)
        y = cy + rng.normal(0.0, spread * 0.8)
        nearest = np.min(np.hypot(track_points[:, 0] - x, track_points[:, 1] - y))
        if nearest < 1.8:
            continue
        size = min(random_lump_size(rng) * 0.8, 0.12)
        radii = chunk_radii(rng, size, 0.65)
        add_chunk(coal_builder, (x, y, mc.ground_height(x, y) + radii[2] * 0.4), radii, random_rotation(rng),
                  templates[int(rng.integers(len(templates)))], slot=int(rng.choice(3, p=[0.45, 0.3, 0.25])))
        placed += 1


# ---------------------------------------------------------------------------------------------------------------------
# The whole part
# ---------------------------------------------------------------------------------------------------------------------
def count_triangles(objects):
    total = 0
    for obj in objects:
        mesh = obj.data
        sizes = np.zeros(len(mesh.polygons), dtype=np.int32)
        mesh.polygons.foreach_get('loop_total', sizes)
        total += int((sizes - 2).sum())
    return total


def build(collection_name='Mine'):
    started = time.time()
    rng = np.random.default_rng(20250519)
    path = TrackPath()
    materials = make_materials()
    templates = make_chunk_templates(24, 77)
    created = []

    plan = plan_sleepers(path, rng)
    created.append(build_stone_bed(path, materials))
    created.append(build_sleepers(path, plan, materials, rng))
    created.append(build_rails(path, materials))
    created.append(build_chairs_and_fishplates(path, plan, materials, rng))
    created.append(build_loose_stones(path, plan, materials, templates, rng))

    # carts
    parts = {
        'steel': mc.MeshBuilder('Cart steel', materials['cart_steels']),
        'iron': mc.MeshBuilder('Cart iron parts', [materials['iron_brown'], materials['iron_dark'], materials['rivet_rust']]),
        'coal': mc.MeshBuilder('Coal in carts', materials['coals']),
    }
    cart_one_s = find_s_for_y(path, -7.0)
    origin, rotation = cart_frame_on_track(path, cart_one_s)
    build_one_cart(parts, origin, rotation, 0, templates, rng, 'heaped')
    cart_two_s = cart_one_s + 4.3
    origin, rotation = cart_frame_on_track(path, cart_two_s)
    build_one_cart(parts, origin, rotation, 1, templates, rng, 'heaped')
    tipped_x, tipped_y = -5.4, -8.2
    origin, rotation = tipped_cart_pose(tipped_x, tipped_y, math.radians(30), math.radians(74))
    gravity_local = rotation.T @ np.array([0.0, 0.0, -1.0])
    build_one_cart(parts, origin, rotation, 2, templates, rng, 'tipped', gravity_local)
    spill = mc.MeshBuilder('Coal heaps and spill', materials['coals'])
    add_spilled_coal(spill, templates, rng, origin, rotation)
    for key in ('steel', 'iron', 'coal'):
        created.append(parts[key].finish(collection_name))

    # heaps beside the track (to its left, the side away from the camera) and scattered lumps
    def heap_centre(t, distance):
        s = float(np.interp(t, path.t_values, path.cumulative))
        x, y, dx, dy = path.frame(s)
        return x - dy * distance, y + dx * distance
    heap_a = heap_centre(0.6, 3.9)
    heap_b = heap_centre(0.85, 3.7)
    add_coal_heap(spill, templates, rng, heap_a[0], heap_a[1], 2.1, 1.55, 1.15, 1100, 0.5)
    add_coal_heap(spill, templates, rng, heap_b[0], heap_b[1], 1.8, 1.35, 0.9, 800, -0.3)
    add_scattered_lumps(spill, templates, rng, path, [(heap_a[0], heap_a[1], 2.6), (heap_b[0], heap_b[1], 2.4),
                                                   (heap_a[0] + 2.0, heap_a[1] - 3.5, 1.8), (heap_b[0] - 1.0, heap_b[1] - 4.0, 1.8)], 300)
    # a little coal dropped around the carts' stretch of track (in front of the carts, between the camera and the doorway)
    cart_yard = [path.side_xy(cart_one_s, -3.0), path.side_xy(cart_two_s, -3.2), path.side_xy(cart_one_s - 1.0, 2.8)]
    add_scattered_lumps(spill, templates, rng, path, [(x, y, 1.7) for x, y in cart_yard], 90)
    created.append(spill.finish(collection_name))

    names = [obj.name for obj in created]
    return {'objects': names, 'notes': 'Track, three carts and two coal heaps built in %.1f s; heaps at (%.1f, %.1f) and (%.1f, %.1f); '
            'cart 1 centre s=%.2f m, cart 2 s=%.2f m, tipped cart at (%.1f, %.1f). %d triangles.' % (
                time.time() - started, heap_a[0], heap_a[1], heap_b[0], heap_b[1], cart_one_s, cart_two_s, tipped_x, tipped_y, count_triangles(created)),
            'triangle_count': count_triangles(created), 'build_seconds': time.time() - started}
