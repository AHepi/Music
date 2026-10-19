# What this does: builds the HEADFRAME, the tall riveted steel winding tower that stands in front of the engine house doorway.
# It has four leaning legs on four stone footing blocks, cross-braced steel faces (X braces, with big V braces low down so
# the track can pass underneath), two platforms with handrails, a ladder, a top deck carrying the axle and two big spoked
# wheels, two ropes sloping back to the engine-house roof and two ropes dropping to a small wooden shaft-top platform.
# Everything is placed in world coordinates from the shared plan (mc.LAYOUT['headframe']) and sits on mc.ground_height().
# How to use: import this file and call build(); it returns {'objects': [...], 'notes': '...'}. It makes no camera or lights.
# Plain-word names are used on purpose, so a non-programmer can read it and change a number (all the sizes are at the top).
import math
import os
import sys
import time

import numpy as np
import bpy

LIBRARY_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
if LIBRARY_FOLDER not in sys.path:
    sys.path.insert(0, LIBRARY_FOLDER)
import mine_common as mc

# --------------------------------------------------------------------------------------------------------------------
# Sizes in metres (change these to change the look)
# --------------------------------------------------------------------------------------------------------------------
FOOTING_TOP_HEIGHT = 0.74            # how high the stone footing blocks stand above the ground
LEG_START_HEIGHT = 0.80              # steel legs start here (on the base plate on top of the footing)
LEG_END_HEIGHT = 14.0                # steel legs end here, under the top deck
LEG_HALF_WIDTH_AT_BASE = 0.29        # a leg is a square box beam, 0.58 m across at the bottom ...
LEG_HALF_WIDTH_AT_TOP = 0.21         # ... and 0.42 m across at the top
FRAME_HEIGHTS_ON_FRONT_AND_BACK = [6.5, 10.6, 13.8]            # horizontal beams in the front and back faces
FRAME_HEIGHTS_ON_SIDES = [1.35, 3.9, 6.5, 10.6, 13.8]          # horizontal beams in the two side faces
PLATFORM_HEIGHTS = [6.5, 10.6]       # the two intermediate platforms
V_BRACE_START_HEIGHT = 1.45          # the big V braces in the front and back faces start on the legs here
V_BRACE_TUCK_IN = 0.20               # V braces sit this far behind the face (so the hanging ropes pass in front of them)
DECK_TOP_HEIGHT = 14.5               # top of the girders of the top deck
WHEEL_OUTER_RADIUS = 2.40            # outer edge of the wheel rim flanges
WHEEL_ROPE_RADIUS = 2.335            # where the rope sits on the rim
WHEEL_THICKNESS = 0.30
SPOKE_COUNT = 16
ROPE_THICKNESS_RADIUS = 0.036
LADDER_POSITION_FRACTION = 0.70      # the ladder sits this fraction of the way from the centre to the leg, on the front face

FACES = {'front': ('x', -1), 'back': ('x', +1), 'left': ('y', -1), 'right': ('y', +1)}
# 8-corner box layout used everywhere (same order as MeshBuilder.add_box): index = x_bit + 2*y_bit + 4*z_bit
BOX_FACES = {'bottom': (0, 2, 3, 1), 'top': (4, 5, 7, 6), 'front': (0, 1, 5, 4), 'back': (2, 6, 7, 3), 'left': (0, 4, 6, 2), 'right': (1, 3, 7, 5)}


# --------------------------------------------------------------------------------------------------------------------
# Small geometry helpers
# --------------------------------------------------------------------------------------------------------------------
def unit(vector):
    vector = np.asarray(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def polygon_normal(points):
    """Direction a flat polygon faces (Newell's method). Points go counter-clockwise when seen from the front."""
    points = np.asarray(points, dtype=float)
    following = np.roll(points, -1, axis=0)
    return np.array([
        np.sum((points[:, 1] - following[:, 1]) * (points[:, 2] + following[:, 2])),
        np.sum((points[:, 2] - following[:, 2]) * (points[:, 0] + following[:, 0])),
        np.sum((points[:, 0] - following[:, 0]) * (points[:, 1] + following[:, 1]))])


def add_solid_from_eight_corners(builder, corners, slot, skip=(), uv_axes_by_face=None):
    """A box-like solid from 8 corners (bottom four then top four, as in add_box). Each face is turned to face outward
    automatically, so slanted or tapered boxes can never come out inside-out."""
    corners = np.asarray(corners, dtype=float).reshape(8, 3)
    middle = corners.mean(axis=0)
    for face_name, ids in BOX_FACES.items():
        if face_name in skip:
            continue
        points = corners[list(ids)]
        if np.dot(polygon_normal(points), points.mean(axis=0) - middle) < 0:
            points = points[::-1]
        axes = None if uv_axes_by_face is None else uv_axes_by_face.get(face_name)
        builder.add_polygon(points, slot=slot, uv_axes=axes)


def add_flat_plate(builder, polygon_points, outward_direction, thickness, slot):
    """A thin plate (gusset, cover plate) with the given outline, thickness measured along outward_direction."""
    direction = unit(outward_direction)
    outline = np.asarray(polygon_points, dtype=float)
    if np.dot(polygon_normal(outline), direction) < 0:
        outline = outline[::-1]
    front = outline + direction * thickness / 2.0
    back = outline - direction * thickness / 2.0
    builder.add_polygon(front, slot=slot)
    builder.add_polygon(back[::-1], slot=slot)
    count = len(outline)
    for i in range(count):
        j = (i + 1) % count
        builder.add_polygon([back[i], back[j], front[j], front[i]], slot=slot)


def add_timber(builder, centre, basis, size, slot, grain_along_first_axis=True):
    """A wooden box whose wood grain runs along its first axis (so planks and spokes look right).
    basis: 3x3 matrix whose columns are the box's length, width and height directions; size: the three lengths."""
    basis = np.asarray(basis, dtype=float)
    centre = np.asarray(centre, dtype=float)
    half = np.asarray(size, dtype=float) / 2.0
    corners = np.array([[x, y, z] for z in (-half[2], half[2]) for y in (-half[1], half[1]) for x in (-half[0], half[0])]) @ basis.T + centre
    length_axis, width_axis, height_axis = basis[:, 0], basis[:, 1], basis[:, 2]
    axes = {'left': (width_axis, height_axis), 'right': (width_axis, height_axis),
            'front': (length_axis, height_axis), 'back': (length_axis, height_axis),
            'top': (length_axis, width_axis), 'bottom': (length_axis, width_axis)}
    add_solid_from_eight_corners(builder, corners, slot, uv_axes_by_face=axes)


def timber_basis(length_direction, width_hint=(0.0, 0.0, 1.0)):
    return mc.basis_from_direction(length_direction, width_hint)


class RivetCollector:
    """Collects thousands of small rivet heads and turns them into one mesh at the end (fast)."""

    def __init__(self):
        self.positions = []
        self.normals = []

    def add(self, position, normal):
        self.positions.append(np.asarray(position, dtype=float))
        self.normals.append(unit(normal))

    def add_line(self, start, end, normal, spacing, margin=0.0):
        start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
        length = np.linalg.norm(end - start)
        usable = length - 2 * margin
        if usable <= 0:
            return
        count = max(int(round(usable / spacing)), 1)
        for k in range(count + 1):
            fraction = (margin + usable * k / count) / length
            self.add(start + (end - start) * fraction, normal)

    def finish_into(self, builder, slot, radius=0.042, height=0.034):
        if not self.positions:
            return
        positions = np.array(self.positions)
        normals = np.array(self.normals)
        count = len(positions)
        helper = np.where(np.abs(normals[:, 2:3]) < 0.9, np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]]))
        side_a = np.cross(helper, normals)
        side_a /= np.linalg.norm(side_a, axis=1, keepdims=True)
        side_b = np.cross(normals, side_a)
        angles = np.linspace(0, 2 * np.pi, 6, endpoint=False)
        ring = np.cos(angles)[:, None, None] * side_a[None] + np.sin(angles)[:, None, None] * side_b[None]    # (6, count, 3)
        base_ring = positions[None] - normals[None] * 0.006 + ring * radius
        middle_ring = positions[None] + normals[None] * height * 0.62 + ring * radius * 0.78
        apex = positions + normals * height
        # vertex order per rivet: 6 base, 6 middle, 1 apex
        vertices = np.concatenate([base_ring.transpose(1, 0, 2), middle_ring.transpose(1, 0, 2), apex[:, None, :]], axis=1).reshape(-1, 3)
        faces = []
        for r in range(count):
            o = r * 13
            for i in range(6):
                j = (i + 1) % 6
                faces.append([o + i, o + j, o + 6 + j, o + 6 + i])
                faces.append([o + 6 + i, o + 6 + j, o + 12])
        builder.add_indexed_faces(vertices, faces, slot=slot)


# --------------------------------------------------------------------------------------------------------------------
# The shape of the tower: where the leaning legs and the four faces are at any height
# --------------------------------------------------------------------------------------------------------------------
class TowerShape:
    def __init__(self):
        spec = mc.LAYOUT['headframe']
        self.cx, self.cy = spec['centre_x'], spec['centre_y']
        self.base_half_x, self.base_half_y = spec['base_half_x'], spec['base_half_y']
        self.top_half_x, self.top_half_y = spec['top_half_x'], spec['top_half_y']
        self.z_bottom, self.z_top = LEG_START_HEIGHT, LEG_END_HEIGHT
        span = self.z_top - self.z_bottom
        self.lean_x = (self.base_half_x - self.top_half_x) / span      # metres each leg moves inward per metre of height
        self.lean_y = (self.base_half_y - self.top_half_y) / span

    def half_x(self, z):
        return self.base_half_x - self.lean_x * (z - self.z_bottom)

    def half_y(self, z):
        return self.base_half_y - self.lean_y * (z - self.z_bottom)

    def leg_centre(self, side_x, side_y, z):
        return np.array([self.cx + side_x * self.half_x(z), self.cy + side_y * self.half_y(z), z])

    def leg_half_width(self, z):
        t = (z - self.z_bottom) / (self.z_top - self.z_bottom)
        return LEG_HALF_WIDTH_AT_BASE + (LEG_HALF_WIDTH_AT_TOP - LEG_HALF_WIDTH_AT_BASE) * t

    def face_normal(self, face):
        axis, sign = FACES[face]
        if axis == 'x':
            return unit([0.0, sign, self.lean_y])
        return unit([sign, 0.0, self.lean_x])

    def face_half_width(self, face, z):
        return self.half_x(z) if FACES[face][0] == 'x' else self.half_y(z)

    def face_point(self, face, across, z, offset=0.0):
        """A point in the flat face of the tower. across = metres sideways from the face centre; offset = metres outward."""
        axis, sign = FACES[face]
        if axis == 'x':
            point = np.array([self.cx + across, self.cy + sign * self.half_y(z), z])
        else:
            point = np.array([self.cx + sign * self.half_x(z), self.cy + across, z])
        return point + offset * self.face_normal(face)


# --------------------------------------------------------------------------------------------------------------------
# Materials made in this file
# --------------------------------------------------------------------------------------------------------------------
def make_weathered_stone_material():
    """Grey stone with blotchy light and dark patches and a rough bump, made from noise (no picture needed)."""
    material = bpy.data.materials.new('Headframe footing stone')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    position = nodes.new('ShaderNodeNewGeometry')
    big_patches = nodes.new('ShaderNodeTexNoise')
    big_patches.inputs['Scale'].default_value = 2.2
    big_patches.inputs['Detail'].default_value = 6.0
    big_patches.inputs['Roughness'].default_value = 0.65
    links.new(position.outputs['Position'], big_patches.inputs['Vector'])
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 30.0
    grain.inputs['Detail'].default_value = 8.0
    links.new(position.outputs['Position'], grain.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.085, 0.082, 0.075, 1.0)
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = (0.30, 0.285, 0.255, 1.0)
    middle = ramp.color_ramp.elements.new(0.5)
    middle.color = (0.16, 0.15, 0.135, 1.0)
    links.new(big_patches.outputs['Fac'], ramp.inputs['Fac'])
    grain_mix = nodes.new('ShaderNodeMix')
    grain_mix.data_type = 'RGBA'
    grain_mix.blend_type = 'MULTIPLY'
    grain_mix.inputs['Factor'].default_value = 0.55
    links.new(ramp.outputs['Color'], grain_mix.inputs['A'])
    grain_light = nodes.new('ShaderNodeMapRange')
    grain_light.inputs['To Min'].default_value = 0.6
    grain_light.inputs['To Max'].default_value = 1.25
    links.new(grain.outputs['Fac'], grain_light.inputs['Value'])
    links.new(grain_light.outputs['Result'], grain_mix.inputs['B'])
    # rust stains running down from the steel base plate: strongest near the top of the block, broken up by noise
    split = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position.outputs['Position'], split.inputs['Vector'])
    near_top = nodes.new('ShaderNodeMapRange')
    near_top.clamp = True
    near_top.inputs['From Min'].default_value = 0.30
    near_top.inputs['From Max'].default_value = 0.78
    near_top.inputs['To Min'].default_value = 0.0
    near_top.inputs['To Max'].default_value = 1.0
    links.new(split.outputs['Z'], near_top.inputs['Value'])
    streaks = nodes.new('ShaderNodeTexNoise')
    streaks.inputs['Scale'].default_value = 7.0
    streaks.inputs['Detail'].default_value = 5.0
    links.new(position.outputs['Position'], streaks.inputs['Vector'])
    streak_strength = nodes.new('ShaderNodeMapRange')
    streak_strength.clamp = True
    streak_strength.inputs['From Min'].default_value = 0.42
    streak_strength.inputs['From Max'].default_value = 0.62
    links.new(streaks.outputs['Fac'], streak_strength.inputs['Value'])
    rust_amount = nodes.new('ShaderNodeMath')
    rust_amount.operation = 'MULTIPLY'
    links.new(near_top.outputs['Result'], rust_amount.inputs[0])
    links.new(streak_strength.outputs['Result'], rust_amount.inputs[1])
    rusted = nodes.new('ShaderNodeMix')
    rusted.data_type = 'RGBA'
    rusted.blend_type = 'MIX'
    rusted.inputs['B'].default_value = (0.20, 0.075, 0.032, 1.0)
    links.new(rust_amount.outputs['Value'], rusted.inputs['Factor'])
    links.new(grain_mix.outputs['Result'], rusted.inputs['A'])
    links.new(rusted.outputs['Result'], bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.05
    links.new(grain.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.92
    material['mine_tile_metres'] = 1.0
    return material


# --------------------------------------------------------------------------------------------------------------------
# The parts
# --------------------------------------------------------------------------------------------------------------------
def build_footings(tower, stone, steel, rivets, footing_positions):
    """Four stone footing blocks with a steel base plate, anchor bolts and corner ribs. footing_positions: list of (sx, sy, ground)."""
    generator = np.random.default_rng(7)
    for sx, sy, ground in footing_positions:
        centre = tower.leg_centre(sx, sy, tower.z_bottom)
        x, y = centre[0], centre[1]
        # lower block: wide at the bottom, narrower at the top (a stout pyramid trunk), sunk a little into the ground
        low, high = ground - 0.30, ground + FOOTING_TOP_HEIGHT - 0.12
        wide, narrow = 0.58, 0.49
        corners = []
        for z, half in ((low, wide), (high, narrow)):
            for dy in (-1, 1):
                for dx in (-1, 1):
                    jitter = generator.uniform(-0.02, 0.02, 2)
                    corners.append([x + dx * half + jitter[0], y + dy * half + jitter[1], z])
        add_solid_from_eight_corners(stone, corners, 0)
        # capping slab, a little proud of the block
        cap_half = 0.53
        stone.add_box((x, y, ground + FOOTING_TOP_HEIGHT - 0.06), (cap_half * 2, cap_half * 2, 0.12), slot=0)
        # steel base plate with four anchor bolts and four triangular ribs against the leg
        plate_top = ground + FOOTING_TOP_HEIGHT + 0.06
        steel.add_box((x, y, ground + FOOTING_TOP_HEIGHT + 0.03), (0.90, 0.90, 0.06), slot=1)
        for dx in (-1, 1):
            for dy in (-1, 1):
                bolt_x, bolt_y = x + dx * 0.38, y + dy * 0.38
                steel.add_cylinder((bolt_x, bolt_y, plate_top - 0.01), (bolt_x, bolt_y, plate_top + 0.11), 0.05, sides=6, slot=1)
                rivets.add((bolt_x, bolt_y, plate_top + 0.11), (0, 0, 1))
        base = tower.leg_centre(sx, sy, ground + LEG_START_HEIGHT)
        direction_out = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for ox, oy in direction_out:
            half = LEG_HALF_WIDTH_AT_BASE
            rib_foot = np.array([base[0] + ox * (half + 0.30), base[1] + oy * (half + 0.30), plate_top])
            rib_top = np.array([base[0] + ox * half, base[1] + oy * half, plate_top + 0.62])
            rib_inner = np.array([base[0] + ox * half, base[1] + oy * half, plate_top])
            side = np.array([-oy, ox, 0.0])
            outline = [rib_foot, rib_inner, rib_top]
            add_flat_plate(steel, outline, side, 0.05, 1)
    return


def build_legs(tower, steel, rivets, footing_ground):
    """Four leaning box-beam legs, with strap collars where the frames meet them and rivet columns down every face."""
    for sx, sy, ground in footing_ground:
        z_start = ground + LEG_START_HEIGHT
        z_end = tower.z_top
        bottom = tower.leg_centre(sx, sy, z_start)
        top = tower.leg_centre(sx, sy, z_end)
        half_bottom, half_top = tower.leg_half_width(z_start), tower.leg_half_width(z_end)
        corners = []
        for centre, half in ((bottom, half_bottom), (top, half_top)):
            for dy in (-1, 1):
                for dx in (-1, 1):
                    corners.append([centre[0] + dx * half, centre[1] + dy * half, centre[2]])
        add_solid_from_eight_corners(steel, corners, 0)
        # four angle-iron strips running up the corner edges of the leg (they catch the light and make the leg read as a built beam)
        for corner_x in (-1, 1):
            for corner_y in (-1, 1):
                strip_bottom = bottom + np.array([corner_x * half_bottom, corner_y * half_bottom, 0.0])
                strip_top = top + np.array([corner_x * half_top, corner_y * half_top, 0.0])
                steel.add_beam(strip_bottom, strip_top, 0.075, 0.075, slot=1, up_hint=(1.0, 0.0, 0.0))
        # collar straps where the horizontal frames and platforms are
        for z in sorted(set(FRAME_HEIGHTS_ON_FRONT_AND_BACK + FRAME_HEIGHTS_ON_SIDES + [V_BRACE_START_HEIGHT])):
            z0, z1 = z - 0.42, z + 0.42
            if z0 < z_start + 0.05:
                continue
            collar = []
            for zz in (z0, z1):
                centre = tower.leg_centre(sx, sy, zz)
                half = tower.leg_half_width(zz) + 0.035
                for dy in (-1, 1):
                    for dx in (-1, 1):
                        collar.append([centre[0] + dx * half, centre[1] + dy * half, zz])
            add_solid_from_eight_corners(steel, collar, 1)
        # rivet columns on the four faces
        leg_direction = unit(top - bottom)
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            face_direction = np.array([ox, oy, 0.0])
            normal = unit(face_direction - np.dot(face_direction, leg_direction) * leg_direction)
            lateral = np.array([-oy, ox, 0.0])
            z = z_start + 0.30
            while z < z_end - 0.2:
                centre = tower.leg_centre(sx, sy, z)
                half = tower.leg_half_width(z)
                for lateral_fraction in (-0.5, 0.5):
                    rivets.add(centre + face_direction * half + lateral * half * lateral_fraction, normal)
                z += 0.46


def add_face_beam(builder, tower, face, across_start, z_start, across_end, z_end, width, depth, slot, offset=0.0):
    start = tower.face_point(face, across_start, z_start, offset)
    end = tower.face_point(face, across_end, z_end, offset)
    builder.add_beam(start, end, width, depth, slot=slot, up_hint=tower.face_normal(face))


def add_gusset_triangle(steel, rivets, tower, face, corner, toward_a, toward_b, size_a, size_b, offset, thickness=0.032, slot=1):
    """A corner plate lying in a face. corner = (across, z); toward_a / toward_b = directions (across, z) of the two edges."""
    corner = np.asarray(corner, dtype=float)
    a = corner + unit(toward_a) * size_a
    b = corner + unit(toward_b) * size_b
    outline = [tower.face_point(face, p[0], p[1], offset) for p in (corner, a, b)]
    add_flat_plate(steel, outline, tower.face_normal(face), thickness, slot)
    outward = offset + thickness / 2.0
    for weights in ((0.16, 0.18, 0.66), (0.16, 0.66, 0.18), (0.50, 0.20, 0.30), (0.50, 0.30, 0.20), (0.22, 0.38, 0.40), (0.1, 0.35, 0.55)):
        p = weights[0] * corner + weights[1] * a + weights[2] * b
        rivets.add(tower.face_point(face, p[0], p[1], outward), tower.face_normal(face))


def add_crossing_plate(steel, rivets, tower, face, centre, direction_a, direction_b, half_length, offset, thickness=0.032):
    centre = np.asarray(centre, dtype=float)
    da, db = unit(direction_a), unit(direction_b)
    points = [centre + da * half_length, centre + db * half_length, centre - da * half_length, centre - db * half_length]
    outline = [tower.face_point(face, p[0], p[1], offset) for p in points]
    add_flat_plate(steel, outline, tower.face_normal(face), thickness, 1)
    outward = offset + thickness / 2.0
    for p in (centre, centre + da * half_length * 0.62, centre - da * half_length * 0.62, centre + db * half_length * 0.62, centre - db * half_length * 0.62):
        rivets.add(tower.face_point(face, p[0], p[1], outward), tower.face_normal(face))


def build_faces(tower, steel, rivets, ground_levels):
    """Horizontal frames and the X and V bracing in the four faces of the tower."""
    for face in FACES:
        axis, sign = FACES[face]
        is_front_or_back = axis == 'x'
        normal = tower.face_normal(face)
        frame_heights = FRAME_HEIGHTS_ON_FRONT_AND_BACK if is_front_or_back else FRAME_HEIGHTS_ON_SIDES
        half = lambda z: tower.face_half_width(face, z)
        # horizontal beams
        for z in frame_heights:
            add_face_beam(steel, tower, face, -half(z), z, half(z), z, 0.34, 0.26, 0, offset=0.0)
            start = tower.face_point(face, -half(z) + 0.55, z, 0.13)
            end = tower.face_point(face, half(z) - 0.55, z, 0.13)
            rivets.add_line(start + [0, 0, 0.08], end + [0, 0, 0.08], normal, 0.42)
            rivets.add_line(start - [0, 0, 0.08], end - [0, 0, 0.08], normal, 0.42)
        # the bays between horizontal beams that get an X
        bays = list(zip(frame_heights[:-1], frame_heights[1:]))
        for z0, z1 in bays:
            # first diagonal rises to the right, second to the left
            width = 0.26 if (z1 - z0) < 3.5 else 0.30
            add_face_beam(steel, tower, face, -half(z0), z0, half(z1), z1, width, 0.25, 1, offset=0.0)
            add_face_beam(steel, tower, face, half(z0), z0, -half(z1), z1, width, 0.22, 1, offset=0.0)
            for start_across, end_across, depth_half in ((-half(z0), half(z1), 0.125), (half(z0), -half(z1), 0.11)):
                start = tower.face_point(face, start_across, z0, depth_half)
                end = tower.face_point(face, end_across, z1, depth_half)
                rivets.add_line(start, end, normal, 0.5, margin=0.75)
            # plates in the four corners and where the diagonals cross
            for side in (-1, 1):
                for is_top in (False, True):
                    z_corner = z1 if is_top else z0
                    z_other = z0 if is_top else z1
                    corner = (side * half(z_corner), z_corner)
                    opposite = (-side * half(z_other), z_other)
                    toward_diagonal = (opposite[0] - corner[0], opposite[1] - corner[1])
                    add_gusset_triangle(steel, rivets, tower, face, corner, (-side, 0.0), toward_diagonal, 0.95, 1.05, 0.15)
            crossing_z = 0.5 * (z0 + z1)
            diag_a = (half(z0) + half(z1), z1 - z0)
            diag_b = (-(half(z0) + half(z1)), z1 - z0)
            add_crossing_plate(steel, rivets, tower, face, (0.0, crossing_z), diag_a, diag_b, 0.42, 0.15)
        if is_front_or_back:
            # big inverted-V braces low down: the track runs underneath, between the legs
            z_apex = frame_heights[0]
            z_foot = V_BRACE_START_HEIGHT
            inward = -V_BRACE_TUCK_IN
            for side, depth in ((-1, 0.22), (1, 0.20)):
                add_face_beam(steel, tower, face, side * half(z_foot), z_foot, 0.0, z_apex - 0.05, 0.36, depth, 1, offset=inward)
                start = tower.face_point(face, side * half(z_foot), z_foot, inward + depth / 2)
                end = tower.face_point(face, 0.0, z_apex, inward + depth / 2)
                rivets.add_line(start, end, normal, 0.55, margin=0.9)
                corner = (side * half(z_foot), z_foot)
                toward_apex = (-side * half(z_foot), z_apex - z_foot)
                add_gusset_triangle(steel, rivets, tower, face, corner, (-side, 0.0), toward_apex, 0.95, 1.2, inward + depth / 2 + 0.01)
                if True:
                    # a second, higher plate where the V meets the frame beam
                    corner_top = (side * 0.0, z_apex)
            # one plate covering the point of the V
            plate_centre_z = z_apex - 0.55
            outline_across_z = [(-0.62, z_apex - 0.17), (0.62, z_apex - 0.17), (0.40, z_apex - 1.15), (-0.40, z_apex - 1.15)]
            outline = [tower.face_point(face, a, z, inward + 0.095) for a, z in outline_across_z]
            add_flat_plate(steel, outline, normal, 0.03, 1)
            for a, z in ((-0.40, z_apex - 0.40), (0.40, z_apex - 0.40), (-0.22, z_apex - 0.85), (0.22, z_apex - 0.85), (0.0, z_apex - 0.62)):
                rivets.add(tower.face_point(face, a, z, inward + 0.11), normal)
        # little knee plates where horizontal beams meet the legs (rivets in a block)
    return


def build_platforms_and_ladder(tower, steel, wood, rivets):
    ladder_across_top = None
    for platform_z in PLATFORM_HEIGHTS:
        hx, hy = tower.half_x(platform_z), tower.half_y(platform_z)
        deck_bottom = platform_z + 0.17
        plank_thickness = 0.06
        # planks run front to back, resting on the front and back frame beams
        x = -(hx - 0.05)
        plank_width = 0.235
        index = 0
        while x + plank_width <= hx - 0.05 + 1e-6:
            centre = (tower.cx + x + plank_width / 2.0, tower.cy, deck_bottom + plank_thickness / 2.0)
            add_timber(wood, centre, np.eye(3)[:, [1, 0, 2]], (2 * (hy - 0.05), plank_width - 0.025, plank_thickness), 1)
            x += plank_width
            index += 1
        # joists under the planks (steel, along x) so the deck reads as built, not floating
        for y_fraction in (-0.5, 0.5):
            steel.add_box((tower.cx, tower.cy + y_fraction * (hy - 0.2) * 1.0, platform_z + 0.08), (2 * (hx - 0.2), 0.12, 0.18), slot=0)
        # handrails inside the frame, with a gap in front of the ladder
        rail_x, rail_y = hx - 0.42, hy - 0.42
        ladder_x = tower.cx + LADDER_POSITION_FRACTION * hx
        gap_a, gap_b = ladder_x - 0.50 - tower.cx, ladder_x + 0.50 - tower.cx
        deck_top = deck_bottom + plank_thickness
        path = [(gap_b, -rail_y), (rail_x, -rail_y), (rail_x, rail_y), (-rail_x, rail_y), (-rail_x, -rail_y), (gap_a, -rail_y)]
        add_handrail_run(steel, [(tower.cx + p[0], tower.cy + p[1]) for p in path], deck_top)
    # the ladder: up the front face, near the right-hand leg, standing 0.4 m out from the face
    front = 'front'
    normal = tower.face_normal(front)
    z_low, z_high = LEG_START_HEIGHT + 0.5, 14.9
    def ladder_axis_point(z, offset):
        across = LADDER_POSITION_FRACTION * tower.half_x(z)
        return tower.face_point(front, across, z, offset)
    stand_off = 0.42
    side_vector = np.array([1.0, 0.0, 0.0])
    rail_gap = 0.27
    for sign in (-1, 1):
        start = ladder_axis_point(z_low, stand_off) + side_vector * sign * rail_gap
        end = ladder_axis_point(z_high, stand_off) + side_vector * sign * rail_gap
        # the two side rails follow the leaning face; the lean makes them converge slightly, which is fine for a ladder
        steel.add_beam(start, end, 0.07, 0.05, slot=1, up_hint=normal)
    rung_z = z_low + 0.25
    while rung_z < z_high - 0.1:
        a = ladder_axis_point(rung_z, stand_off) - side_vector * rail_gap
        b = ladder_axis_point(rung_z, stand_off) + side_vector * rail_gap
        steel.add_cylinder(a, b, 0.022, sides=6, slot=1, caps=False)
        rung_z += 0.31
    # stand-off brackets from the ladder rails to the face frames
    bracket_z = z_low + 0.4
    while bracket_z < z_high - 0.3:
        for sign in (-1, 1):
            inner = tower.face_point(front, LADDER_POSITION_FRACTION * tower.half_x(bracket_z), bracket_z, 0.0) + side_vector * sign * rail_gap
            outer = ladder_axis_point(bracket_z, stand_off) + side_vector * sign * rail_gap
            steel.add_beam(inner, outer, 0.05, 0.05, slot=1, up_hint=(1, 0, 0))
        bracket_z += 1.9


def add_handrail_run(steel, path_xy, deck_top, post_spacing=1.15, top_height=1.05, middle_height=0.55):
    """Posts and two rails following a polyline of (x, y) points on a deck."""
    for (x0, y0), (x1, y1) in zip(path_xy[:-1], path_xy[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        pieces = max(int(math.ceil(length / post_spacing)), 1)
        for k in range(pieces + 1):
            t = k / pieces
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            steel.add_box((x, y, deck_top + top_height / 2.0), (0.07, 0.07, top_height), slot=1)
        for height, thickness in ((top_height, 0.06), (middle_height, 0.045)):
            steel.add_beam((x0, y0, deck_top + height), (x1, y1, deck_top + height), thickness, thickness, slot=1)
        steel.add_beam((x0, y0, deck_top + 0.06), (x1, y1, deck_top + 0.06), 0.02, 0.12, slot=1)


def build_top_deck_and_axle(tower, steel, wood, rivets, wheel_centres):
    cx, cy = tower.cx, tower.cy
    deck_bottom = 14.0
    # girders across front and back (long), girders front-to-back on either side of each wheel pit, and a cross tie
    for side in (-1, 1):
        steel.add_box((cx, cy + side * 1.35, deck_bottom + 0.23), (4.40, 0.32, 0.46), slot=0)
        rivets.add_line((cx - 1.9, cy + side * 1.35 + (-0.16 if side < 0 else 0.16), deck_bottom + 0.23),
                        (cx + 1.9, cy + side * 1.35 + (-0.16 if side < 0 else 0.16), deck_bottom + 0.23), (0, side, 0), 0.4)
    for x in (-2.05, -1.05, 1.05, 2.05):
        steel.add_box((cx + x, cy, deck_bottom + 0.25), (0.30, 3.04, 0.50), slot=0)
    steel.add_box((cx, cy, deck_bottom - 0.17), (4.40, 0.28, 0.34), slot=0)
    # planks between the two inner girders
    y = -1.5
    plank_width = 0.25
    while y + plank_width <= 1.5 + 1e-6:
        add_timber(wood, (cx, cy + y + plank_width / 2.0, deck_bottom + 0.46), np.eye(3), (1.84, plank_width - 0.025, 0.12), 1)
        y += plank_width
    # corner plates on the deck frame
    for sx in (-1, 1):
        for sy in (-1, 1):
            corner = np.array([cx + sx * 2.05, cy + sy * 1.35, deck_bottom + 0.505])
            steel.add_box(corner + [0, 0, 0.0125], (0.62, 0.62, 0.025), slot=1)
            for dx in (-0.2, 0.2):
                for dy in (-0.2, 0.2):
                    rivets.add(corner + [dx, dy, 0.025], (0, 0, 1))
    # handrails along the front and back edges of the middle deck
    for side in (-1, 1):
        add_handrail_run(steel, [(cx - 0.85, cy + side * 1.45), (cx + 0.85, cy + side * 1.45)], deck_bottom + 0.52, post_spacing=0.9, top_height=0.95)
    # four pedestals (two per wheel): A-frames holding the bearing blocks that carry the axle
    axle_height = mc.LAYOUT['headframe']['wheel_centre_height']
    for x in (-2.05, -1.05, 1.05, 2.05):
        for side in (-1, 1):
            foot = np.array([cx + x, cy + side * 1.02, deck_bottom + 0.50])
            head = np.array([cx + x, cy + side * 0.26, axle_height - 0.45])
            steel.add_beam(foot, head, 0.24, 0.26, slot=1, up_hint=(1, 0, 0))
            rivets.add_line(foot + [0.13, 0, 0] + (head - foot) * 0.15, foot + [0.13, 0, 0] + (head - foot) * 0.85, (1, 0, 0), 0.4)
            rivets.add_line(foot + [-0.13, 0, 0] + (head - foot) * 0.15, foot + [-0.13, 0, 0] + (head - foot) * 0.85, (-1, 0, 0), 0.4)
        # cross tie between the two pedestal legs
        tie_z = deck_bottom + 0.50 + 0.45 * (axle_height - 0.45 - deck_bottom - 0.50)
        t = (tie_z - (deck_bottom + 0.50)) / (axle_height - 0.45 - deck_bottom - 0.50)
        tie_y = 1.02 + (0.26 - 1.02) * t
        steel.add_beam((cx + x, cy - tie_y, tie_z), (cx + x, cy + tie_y, tie_z), 0.16, 0.22, slot=1, up_hint=(1, 0, 0))
        # bearing block and its cap, with four bolts
        steel.add_box((cx + x, cy, axle_height - 0.30), (0.46, 0.84, 0.30), slot=0)
        steel.add_box((cx + x, cy, axle_height + 0.12), (0.40, 0.46, 0.34), slot=1)
        for dy in (-0.32, 0.32):
            rivets.add((cx + x, cy + dy, axle_height - 0.15), (0, 0, 1))
        for dx in (-0.14, 0.14):
            rivets.add((cx + x + dx, cy, axle_height + 0.29), (0, 0, 1))
    # the axle and its end caps
    steel.add_cylinder((cx - 2.45, cy, axle_height), (cx + 2.45, cy, axle_height), 0.19, sides=20, slot=0)
    for sign in (-1, 1):
        steel.add_cylinder((cx + sign * 2.28, cy, axle_height), (cx + sign * 2.52, cy, axle_height), 0.26, sides=20, slot=1)
    # a thick central collar on the axle between the wheels
    steel.add_cylinder((cx - 0.35, cy, axle_height), (cx + 0.35, cy, axle_height), 0.27, sides=20, slot=1)


def build_wheel(tower, steel, wood, rivets, wheel_x, phase):
    cy = tower.cy
    height = mc.LAYOUT['headframe']['wheel_centre_height']
    centre = np.array([wheel_x, cy, height])
    axis = (1.0, 0.0, 0.0)
    # rim: a steel ring plus a thin raised flange ring on each side (so the rope sits in a groove)
    steel.add_ring(centre, axis, WHEEL_ROPE_RADIUS - 0.035, 2.02, WHEEL_THICKNESS, sides=72, slot=1)
    for sign in (-1, 1):
        flange_centre = centre + np.array([sign * (WHEEL_THICKNESS / 2.0 - 0.03), 0.0, 0.0])
        steel.add_ring(flange_centre, axis, WHEEL_OUTER_RADIUS, 2.10, 0.06, sides=72, slot=1)
        # rivets round the flanges
        face_x = wheel_x + sign * (WHEEL_THICKNESS / 2.0)
        for k in range(44):
            a = 2 * math.pi * k / 44 + phase
            rivets.add((face_x, cy + 2.29 * math.cos(a), height + 2.29 * math.sin(a)), (sign, 0, 0))
    # hub: a fat cylinder with a bigger bolted cap on the outside
    steel.add_cylinder(centre - np.array([0.23, 0, 0]), centre + np.array([0.23, 0, 0]), 0.42, sides=24, slot=1)
    for sign in (-1, 1):
        steel.add_cylinder(centre + np.array([sign * 0.23, 0, 0]), centre + np.array([sign * 0.30, 0, 0]), 0.30, sides=20, slot=0)
        for k in range(8):
            a = 2 * math.pi * k / 8
            rivets.add(centre + np.array([sign * 0.23, 0.35 * math.cos(a), 0.35 * math.sin(a)]), (sign, 0, 0))
    # spokes: tapered timbers, thick at the hub and slimmer at the rim, held to the rim by little iron shoes
    for k in range(SPOKE_COUNT):
        a = phase + 2 * math.pi * k / SPOKE_COUNT
        radial = np.array([0.0, math.cos(a), math.sin(a)])
        tangent = np.array([0.0, -math.sin(a), math.cos(a)])
        axial = np.array([1.0, 0.0, 0.0])
        start = centre + radial * 0.34
        end = centre + radial * 2.06
        half_start = np.array([0.0, 0.0, 0.0])
        corners = []
        for axial_sign in (-1, 1):
            for tangent_sign in (-1, 1):
                for radius_point, width, thick in ((start, 0.085, 0.085), (end, 0.055, 0.065)):
                    corners.append(radius_point + tangent * tangent_sign * width + axial * axial_sign * thick)
        # corners above are ordered (axial, tangent, start/end); reorder into the 8-corner box order (x=start/end, y=tangent, z=axial)
        ordered = [None] * 8
        index = 0
        for axial_bit in (0, 1):
            for tangent_bit in (0, 1):
                for end_bit in (0, 1):
                    ordered[end_bit + 2 * tangent_bit + 4 * axial_bit] = corners[index]
                    index += 1
        axes = {'left': (tangent, axial), 'right': (tangent, axial), 'front': (radial, axial), 'back': (radial, axial),
                'top': (radial, tangent), 'bottom': (radial, tangent)}
        add_solid_from_eight_corners(wood, ordered, 0, uv_axes_by_face=axes)
        # iron shoe at the rim end of each spoke
        shoe_centre = centre + radial * 2.06
        basis = np.stack([radial, tangent, axial], axis=1)
        steel.add_box(shoe_centre, (0.22, 0.20, 0.20), slot=0, rotation=basis)
        rivets.add(shoe_centre + axial * 0.10, (1, 0, 0))
        rivets.add(shoe_centre - axial * 0.10, (-1, 0, 0))
        # iron band round the spoke near the hub
        band_centre = centre + radial * 0.62
        steel.add_box(band_centre, (0.13, 0.20, 0.20), slot=0, rotation=basis)


def rope_cylinders(rope, start, end, radius=ROPE_THICKNESS_RADIUS, sides=7):
    rope.add_cylinder(start, end, radius, sides=sides, slot=0, caps=False)


def build_ropes(tower, rope_builder, steel, rivets, wheel_xs, rope_end_height):
    cy = tower.cy
    wheel_height = mc.LAYOUT['headframe']['wheel_centre_height']
    house = mc.LAYOUT['engine_house']
    ridge_x = 0.5 * (house['x_left'] + house['x_right'])
    half_width = 0.5 * (house['x_right'] - house['x_left'])
    anchor_y = 6.0
    notes = {}
    for wheel_x in wheel_xs:
        # --- rope sloping from the back of the wheel down to the engine-house roof ---
        roof_height = house['ridge_height'] - (house['ridge_height'] - house['wall_height']) * abs(wheel_x - ridge_x) / half_width
        post_top = house['ridge_height'] + 0.05
        anchor = np.array([wheel_x, anchor_y, post_top])
        wheel_centre = np.array([wheel_x, cy, wheel_height])
        to_anchor = np.array([anchor[1] - cy, anchor[2] - wheel_height])           # (y, z) relative to the wheel centre
        distance = np.linalg.norm(to_anchor)
        base_angle = math.atan2(to_anchor[1], to_anchor[0])
        touch_angle = base_angle + math.acos(WHEEL_ROPE_RADIUS / distance)             # tangent point on the upper back of the wheel
        touch = wheel_centre + np.array([0.0, WHEEL_ROPE_RADIUS * math.cos(touch_angle), WHEEL_ROPE_RADIUS * math.sin(touch_angle)])
        rope_cylinders(rope_builder, touch, anchor)
        # --- the rope wraps over the top of the wheel and leaves the front, dropping straight down ---
        steps = 18
        previous = touch
        for k in range(1, steps + 1):
            angle = touch_angle + (math.pi - touch_angle) * k / steps
            point = wheel_centre + np.array([0.0, WHEEL_ROPE_RADIUS * math.cos(angle), WHEEL_ROPE_RADIUS * math.sin(angle)])
            rope_cylinders(rope_builder, previous, point, sides=7)
            previous = point
        bottom = np.array([wheel_x, cy - WHEEL_ROPE_RADIUS, rope_end_height])
        rope_cylinders(rope_builder, previous, bottom)
        # --- a steel post on the roof that holds the sloping rope ---
        base_point = np.array([wheel_x, anchor_y, roof_height - 0.35])
        steel.add_box((wheel_x, anchor_y, 0.5 * (base_point[2] + post_top)), (0.22, 0.22, post_top - base_point[2]), slot=0)
        steel.add_box((wheel_x, anchor_y, post_top - 0.05), (0.40, 0.30, 0.10), slot=1)
        steel.add_cylinder((wheel_x - 0.17, anchor_y, post_top + 0.03), (wheel_x + 0.17, anchor_y, post_top + 0.03), 0.045, sides=6, slot=1)
        notes[wheel_x] = {'anchor': tuple(round(float(v), 2) for v in anchor), 'roof_height_there': round(roof_height, 2)}
    return notes


def build_shaft_platform(tower, wood, steel, rivets, ground_height_at):
    """A low, flat timber landing at the foot of the two hanging ropes (the shaft top). It is kept flat and only 0.10 m high so
    the track can simply run across it; each rope ends in an iron ring bolted to a small steel plate."""
    cx, cy = tower.cx, tower.cy
    rope_y = cy - WHEEL_ROPE_RADIUS
    ground = ground_height_at(cx, rope_y)
    top = ground + 0.10
    front_edge, back_edge = rope_y - 0.62, rope_y + 0.62
    half_length = 2.30
    plank = 0.205
    y = front_edge
    while y + plank <= back_edge + 1e-6:
        add_timber(wood, (cx, y + plank / 2.0, top - 0.06), np.eye(3), (2 * half_length, plank - 0.02, 0.12), 0)
        y += plank
    # two heavy timber sleepers under the planks, sticking out a little at the ends
    for sign in (-1, 1):
        add_timber(wood, (cx + sign * 1.95, rope_y, top - 0.10), np.eye(3)[:, [1, 0, 2]], (1.34, 0.22, 0.16), 1)
    ring_height = top + 0.035
    for sign in (-1, 1):
        x = cx + sign * 1.55
        steel.add_box((x, rope_y, top + 0.0175), (0.56, 0.56, 0.035), slot=1)
        steel.add_ring((x, rope_y, ring_height + 0.03), (0.0, 0.0, 1.0), 0.13, 0.075, 0.04, sides=14, slot=0)
        for dx in (-0.2, 0.2):
            for dy in (-0.2, 0.2):
                rivets.add((x + dx, rope_y + dy, top + 0.035), (0, 0, 1))
    return {'top': top, 'rope_y': rope_y, 'rope_end_height': ring_height + 0.03}


# --------------------------------------------------------------------------------------------------------------------
# build(): the one function the scene assembly calls
# --------------------------------------------------------------------------------------------------------------------
def build(collection_name='Mine'):
    started = time.time()
    tower = TowerShape()
    spec = mc.LAYOUT['headframe']

    steel_dark_blue = mc.surface_material('metal', tint=(0.80, 0.88, 1.02))        # painted steel, a little darker and bluer
    steel_rusty = mc.surface_material('metal', tint=(1.08, 0.92, 0.82))            # bare rusting steel for braces and plates
    old_wood = mc.surface_material('wood', tint=(0.78, 0.66, 0.56))
    dark_old_wood = mc.surface_material('wood', tint=(0.55, 0.47, 0.40))
    stone = make_weathered_stone_material()
    rivet_metal = mc.plain_material('Headframe rivet iron', (0.075, 0.058, 0.048), roughness=0.55, metallic=0.6)
    rope_brown = mc.plain_material('Headframe rope', (0.17, 0.105, 0.06), roughness=0.9)

    steel = mc.MeshBuilder('Headframe steel', [steel_dark_blue, steel_rusty])
    wood = mc.MeshBuilder('Headframe timber', [old_wood, dark_old_wood])
    # note: the wood builder above is reused under another name inside functions
    stone_builder = mc.MeshBuilder('Headframe footings', [stone])
    rivet_builder = mc.MeshBuilder('Headframe rivets', [rivet_metal])
    rope_builder = mc.MeshBuilder('Headframe ropes', [rope_brown])
    rivets = RivetCollector()

    footing_corners = []
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        c = tower.leg_centre(sx, sy, tower.z_bottom)
        footing_corners.append((sx, sy, mc.ground_height(c[0], c[1])))

    build_footings(tower, stone_builder, steel, rivets, footing_corners)
    build_legs(tower, steel, rivets, footing_corners)
    build_faces(tower, steel, rivets, None)
    build_platforms_and_ladder(tower, steel, wood, rivets)
    wheel_xs = [tower.cx - spec['wheel_spacing_x'], tower.cx + spec['wheel_spacing_x']]
    build_top_deck_and_axle(tower, steel, wood, rivets, wheel_xs)
    build_wheel(tower, steel, wood, rivets, wheel_xs[0], 0.10)
    build_wheel(tower, steel, wood, rivets, wheel_xs[1], 0.31)
    platform_info = build_shaft_platform(tower, wood, steel, rivets, mc.ground_height)
    rope_notes = build_ropes(tower, rope_builder, steel, rivets, wheel_xs, platform_info['rope_end_height'])
    rivets.finish_into(rivet_builder, 0)

    objects = []
    for builder in (steel, wood, stone_builder, rivet_builder, rope_builder):
        obj = builder.finish(collection_name)
        objects.append(obj.name)
    mc.say(f'headframe built in {time.time() - started:.1f} s, {len(rivets.positions)} rivets')
    return {'objects': objects,
            'notes': ('Headframe: four legs on footings at (+-3.1, -3.4 +-2.7), horizontal frames at 6.5 / 10.6 / 13.8 m, top deck 14.5 m, '
                      f'wheel centres at x = {wheel_xs[0]:.2f} and {wheel_xs[1]:.2f}, 16.6 m high, radius 2.4. Back ropes run to small steel '
                      f'posts on the engine-house roof at y = 6 (x = +-1.55, top 7.65 m). The front ropes hang vertically from the front of the '
                      f'wheels at y = {platform_info["rope_y"]:.2f} onto a flat timber landing (top {platform_info["top"]:.2f} m) across the track '
                      'route. Low V braces leave the middle 3 m clear to 3.7 m high.')}
