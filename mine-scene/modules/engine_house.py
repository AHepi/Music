# What this does: builds the ENGINE HOUSE of the coal mine in world coordinates (metres): a long red-brick building with a
# slate roof, standing with its short gable end (the big doorway) facing -Y, exactly where mine_common.LAYOUT['engine_house'] says.
# It makes: brick walls (real displaced bumps on the walls and roof that the camera sees most), a heavy stone doorway with a dark
# timber-framed inside, weathered stone plinth, two glowing windows on the left wall and one on the right wall (arched brick heads,
# stone sills, dark glazing bars), a lean-to plank shed, slate roof with ridge cap, gutters, two downpipes, a small chimney stack
# with lead flashing, a bracket lamp over the door, leaning timber planks and a wooden crate.
# How to use: from another Blender script: sys.path.insert(0, ".../lib"); import mine_common as mc; then
#   import engine_house; result = engine_house.build('Mine')    (it returns {'objects': [names], 'notes': '...'}).
# It makes no camera, sky, lights or render settings. It builds no floor inside: the yard ground must run under the building.
import math
import os
import sys
import time

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import mine_common as mc

# ------------------------------------------------------------------------------------------------------------------
# The plan (all in metres) taken from the shared layout
# ------------------------------------------------------------------------------------------------------------------
PLAN = mc.LAYOUT['engine_house']
LEFT_X = PLAN['x_left']
RIGHT_X = PLAN['x_right']
FRONT_Y = PLAN['y_front']
BACK_Y = PLAN['y_back']
WALL_HEIGHT = PLAN['wall_height']
RIDGE_TOP = PLAN['ridge_height']
OVERHANG = PLAN['roof_overhang']
PLINTH_HEIGHT = PLAN['plinth_height']
DOOR_CENTRE = PLAN['door_centre_x']
DOOR_WIDTH = PLAN['door_width']
DOOR_HEIGHT = PLAN['door_height']

CENTRE_X = 0.5 * (LEFT_X + RIGHT_X)
HALF_WIDTH = 0.5 * (RIGHT_X - LEFT_X)          # 3.9
WALL_THICKNESS = 0.45
PLINTH_PROJECTION = 0.08

SLATE_EAVE_HEIGHT = WALL_HEIGHT + 0.08         # height of the slate surface right above the outer wall face
SLATE_RIDGE_HEIGHT = RIDGE_TOP - 0.10          # slate surface at the ridge; the ridge cap adds the last 10 cm
SLOPE = (SLATE_RIDGE_HEIGHT - SLATE_EAVE_HEIGHT) / HALF_WIDTH   # roof rise per metre sideways
SLAB_THICKNESS = 0.14                          # roof slab thickness measured straight down
GABLE_APEX = SLATE_RIDGE_HEIGHT - 0.08         # the brick gable stops 8 cm below the slate, hidden inside the slab
DEPTH_OF_GLASS = 0.22                          # how far behind the wall face window glass sits

UP = np.array([0.0, 0.0, 1.0])

# Honest list of things that are not perfect yet (also written into out/engine_house_report.json by the preview script).
KNOWN_FLAWS = [
    'The headframe footings (LAYOUT says legs at x=+-3.1, y=-0.7) will probably overlap the crate (x -4.1 to -3.2, y -0.8 to -0.2) and the two '
    'plank piles (x -3.1 to -2.6 and 2.6 to 3.7, feet out to y -0.7); move them with the numbers in add_crate / add_leaning_planks if they clash.',
    'No floor is built inside the doorway or the building: the yard ground (mud) must run under the whole footprint at about z = 0.',
    'From the standard camera the left wall is seen at only about 12 degrees, so the two glowing windows show as narrow slivers and the shed hides '
    'the low part of that wall; they read well from the side and 3/4 views.',
    'The window panes and lamp bulb are one-sided light-giving surfaces facing outward: the inside of the building is dark and is not lit by them. '
    'Their strength (materials Window glow A/B/C and Lamp bulb) was tuned by eye for a bright preview and a dim dusk preview, so tune it in the final light.',
    'Stone (plinth, doorway jambs and lintel, window sills, chimney cap) is a procedural grey stone made inside the module, not one of the uploaded pictures.',
    'Real displacement is only on the front gable wall, the long left wall and the two slate roof slopes; the right wall, back wall and small parts use the normal map only. '
    'The brick picture repeats every 1.5 m so its dark soot blotches show a repeat on the long plain walls.',
    'The interior is only a dark shell with a few timber frames and a plank partition at y=6.4 (no machinery); the design picture shows lighter timbers lit from inside.',
    'The chimney stack shaft passes about 0.3 m below the roof underside near the ridge (visible only from inside the roof space).',
    'Gutters and downpipes are low-polygon (12 and 10 sides): fine at the camera distances of the film, faceted if filmed from under 1 m.',
]


def slate_height(x):
    """Height of the top of the slate at sideways position x."""
    return SLATE_RIDGE_HEIGHT - SLOPE * abs(x - CENTRE_X)


# ------------------------------------------------------------------------------------------------------------------
# Small geometry helpers
# ------------------------------------------------------------------------------------------------------------------
class WallFace:
    """One outside wall seen as a flat sheet. 'along' runs to the right when you stand outside looking at the wall, 'height' is up,
    'depth' is how far INTO the wall (negative = sticking out into the yard)."""

    def __init__(self, origin_x, origin_y, outward_x, outward_y):
        self.outward = np.array([outward_x, outward_y, 0.0])
        self.along = np.cross(UP, self.outward)
        self.origin = np.array([origin_x, origin_y, 0.0])
        self.basis = np.stack([self.along, -self.outward, UP], axis=1)   # box axes: along, inward, up (right handed)

    def point(self, along, height, depth=0.0):
        return self.origin + self.along * along + UP * height - self.outward * depth


FRONT_WALL = WallFace(CENTRE_X, FRONT_Y, 0, -1)       # along = x
LEFT_WALL = WallFace(LEFT_X, FRONT_Y, -1, 0)          # along = -y
BACK_WALL = WallFace(CENTRE_X, BACK_Y, 0, 1)          # along = -x
RIGHT_WALL = WallFace(RIGHT_X, FRONT_Y, 1, 0)         # along = +y


def newell_normal(points):
    points = np.asarray(points, dtype=float)
    following = np.roll(points, -1, axis=0)
    return np.array([
        np.sum((points[:, 1] - following[:, 1]) * (points[:, 2] + following[:, 2])),
        np.sum((points[:, 2] - following[:, 2]) * (points[:, 0] + following[:, 0])),
        np.sum((points[:, 0] - following[:, 0]) * (points[:, 1] + following[:, 1])),
    ])


def add_face(builder, points, slot=0, normal=None, toward=None, away=None, **options):
    """A flat face. Say which way it should look with normal= (a direction), toward= (a point it should face) or away= (a point it
    should face away from); the corner order is flipped if needed so the front side really points that way."""
    points = np.asarray(points, dtype=float).reshape(-1, 3)
    facing = newell_normal(points)
    flip = False
    if normal is not None:
        flip = float(np.dot(facing, normal)) < 0
    elif toward is not None:
        flip = float(np.dot(facing, np.asarray(toward, dtype=float) - points.mean(axis=0))) < 0
    elif away is not None:
        flip = float(np.dot(facing, points.mean(axis=0) - np.asarray(away, dtype=float))) < 0
    if flip:
        points = points[::-1]
    builder.add_polygon(points, slot=slot, **options)


def add_extruded_outline(builder, outline_xz, y_from, y_to, slot=0, uv_axes=None):
    """A flat shape drawn in the x-z plane (list of (x, z) corners, any simple outline) given thickness from y_from to y_to."""
    outline = [(x, z) for x, z in outline_xz]
    area = 0.0
    for (x0, z0), (x1, z1) in zip(outline, outline[1:] + outline[:1]):
        area += x0 * z1 - x1 * z0
    counter_clockwise = area > 0          # seen from -y looking toward +y, x to the right, z up
    front = [(x, y_from, z) for x, z in outline]
    back = [(x, y_to, z) for x, z in outline]
    add_face(builder, front, slot, normal=(0, -1, 0), uv_axes=uv_axes)
    add_face(builder, back, slot, normal=(0, 1, 0), uv_axes=uv_axes)
    for (x0, z0), (x1, z1) in zip(outline, outline[1:] + outline[:1]):
        dx, dz = x1 - x0, z1 - z0
        outward = (dz, 0.0, -dx) if counter_clockwise else (-dz, 0.0, dx)
        add_face(builder, [(x0, y_from, z0), (x1, y_from, z1), (x1, y_to, z1), (x0, y_to, z0)], slot, normal=outward)


def add_prism(builder, loop_a, loop_b, slot=0, skip_a=False, skip_b=False):
    """A solid made from two matching corner loops (front and back). Only for convex shapes."""
    loop_a = np.asarray(loop_a, dtype=float)
    loop_b = np.asarray(loop_b, dtype=float)
    centre = np.concatenate([loop_a, loop_b]).mean(axis=0)
    count = len(loop_a)
    if not skip_a:
        add_face(builder, loop_a, slot, away=centre)
    if not skip_b:
        add_face(builder, loop_b, slot, away=centre)
    for i in range(count):
        j = (i + 1) % count
        add_face(builder, [loop_a[i], loop_a[j], loop_b[j], loop_b[i]], slot, away=centre)


def add_timber(builder, start, end, width, thickness, slot, width_hint=(1.0, 0.0, 0.0), extend=0.0, grain_shift=(0.0, 0.0)):
    """A straight board or beam from start to end. The wood grain runs along its length. width_hint says roughly which way the wide
    side points. Faces get their own picture coordinates so the grain is never stretched."""
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    forward = end - start
    length = float(np.linalg.norm(forward))
    forward = forward / length
    hint = np.asarray(width_hint, dtype=float)
    wide = hint - np.dot(hint, forward) * forward
    if np.linalg.norm(wide) < 1e-6:
        wide = np.cross(forward, np.array([0.0, 1.0, 0.0]))
    wide = wide / np.linalg.norm(wide)
    thick = np.cross(forward, wide)
    centre = (start + end) / 2.0
    half_length, half_wide, half_thick = length / 2.0 + extend, width / 2.0, thickness / 2.0

    def corner(sf, sw, st):
        return centre + sf * half_length * forward + sw * half_wide * wide + st * half_thick * thick

    for st in (-1, 1):   # the two broad faces
        add_face(builder, [corner(-1, -1, st), corner(1, -1, st), corner(1, 1, st), corner(-1, 1, st)], slot, away=centre,
                 uv_axes=(forward, wide), uv_shift=grain_shift)
    for sw in (-1, 1):   # the two narrow edges
        add_face(builder, [corner(-1, sw, -1), corner(1, sw, -1), corner(1, sw, 1), corner(-1, sw, 1)], slot, away=centre,
                 uv_axes=(forward, thick), uv_shift=grain_shift)
    for sf in (-1, 1):   # the two ends
        add_face(builder, [corner(sf, -1, -1), corner(sf, 1, -1), corner(sf, 1, 1), corner(sf, -1, 1)], slot, away=centre,
                 uv_axes=(wide, thick), uv_shift=grain_shift)


def add_wall_box(builder, face, along_from, along_to, height_from, height_to, depth_from, depth_to, slot=0, skip=(), slots=None):
    """A box described in wall terms. depth_from < depth_to; negative depth is outside the wall face."""
    centre = face.point((along_from + along_to) / 2.0, (height_from + height_to) / 2.0, (depth_from + depth_to) / 2.0)
    builder.add_box(centre, (along_to - along_from, depth_to - depth_from, height_to - height_from), slot=slot,
                    rotation=face.basis, slots=slots, skip=skip)


def break_points(low, high, biggest_step, forced):
    marks = sorted(set([low, high] + [p for p in forced if low + 1e-6 < p < high - 1e-6]))
    result = [marks[0]]
    for start, stop in zip(marks[:-1], marks[1:]):
        pieces = max(1, int(math.ceil((stop - start) / biggest_step - 1e-9)))
        for k in range(1, pieces + 1):
            result.append(start + (stop - start) * k / pieces)
    return result


def add_wall_cells(builder, face, along_range, height_range, holes, slot, biggest_cell=(1.6, 1.5), depth=0.0, inside=False):
    """Fills a rectangle of wall with a grid of flat quads (so the displacement can cut each one finely), leaving the 'holes'
    (along_from, along_to, height_from, height_to) empty. Picture coordinates come from world position, so bricks line up."""
    along_marks = break_points(along_range[0], along_range[1], biggest_cell[0], [h[0] for h in holes] + [h[1] for h in holes])
    height_marks = break_points(height_range[0], height_range[1], biggest_cell[1], [h[2] for h in holes] + [h[3] for h in holes])
    for i in range(len(along_marks) - 1):
        for j in range(len(height_marks) - 1):
            a0, a1, z0, z1 = along_marks[i], along_marks[i + 1], height_marks[j], height_marks[j + 1]
            centre_a, centre_z = (a0 + a1) / 2.0, (z0 + z1) / 2.0
            if any(h[0] < centre_a < h[1] and h[2] < centre_z < h[3] for h in holes):
                continue
            corners = [face.point(a0, z0, depth), face.point(a1, z0, depth), face.point(a1, z1, depth), face.point(a0, z1, depth)]
            builder.add_polygon(corners[::-1] if inside else corners, slot=slot)


def add_gable_cells(builder, face, slot, half_width, depth=0.0, inside=False, columns=4, band_height=1.0):
    """The triangle of brick above the eaves on a gable end, cut into bands so it can be displaced finely."""
    base_height = GABLE_APEX - SLOPE * half_width
    bands = max(1, int(round((GABLE_APEX - base_height) / band_height)))
    levels = [base_height + (GABLE_APEX - base_height) * k / bands for k in range(bands + 1)]
    for k in range(bands):
        z0, z1 = levels[k], levels[k + 1]
        half0, half1 = (GABLE_APEX - z0) / SLOPE, (GABLE_APEX - z1) / SLOPE
        for c in range(columns):
            f0, f1 = c / columns, (c + 1) / columns
            low_left, low_right = -half0 + 2 * half0 * f0, -half0 + 2 * half0 * f1
            if half1 < 1e-6:
                corners = [face.point(low_left, z0, depth), face.point(low_right, z0, depth), face.point(0.0, z1, depth)]
            else:
                high_left, high_right = -half1 + 2 * half1 * f0, -half1 + 2 * half1 * f1
                corners = [face.point(low_left, z0, depth), face.point(low_right, z0, depth),
                           face.point(high_right, z1, depth), face.point(high_left, z1, depth)]
            builder.add_polygon(corners[::-1] if inside else corners, slot=slot)


# ------------------------------------------------------------------------------------------------------------------
# Materials
# ------------------------------------------------------------------------------------------------------------------
def make_stone_material(name, base_colour, contrast=0.3):
    """Weathered grey stone made from soft noise (stone is not one of the uploaded pictures): blotchy light and dark patches, fine
    grain bumps, and mud splashed on the lowest 60 cm."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material['mine_tile_metres'] = 1.0
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    position = nodes.new('ShaderNodeNewGeometry')

    blotches = nodes.new('ShaderNodeTexNoise')
    blotches.inputs['Scale'].default_value = 2.6
    blotches.inputs['Detail'].default_value = 6.0
    blotches.inputs['Roughness'].default_value = 0.65
    links.new(position.outputs['Position'], blotches.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    dark = [c * (1.0 - contrast) for c in base_colour]
    light = [min(1.0, c * (1.0 + contrast)) for c in base_colour]
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (dark[0], dark[1], dark[2], 1.0)
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = (light[0], light[1], light[2], 1.0)
    links.new(blotches.outputs['Fac'], ramp.inputs['Fac'])

    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 55.0
    grain.inputs['Detail'].default_value = 3.0
    links.new(position.outputs['Position'], grain.inputs['Vector'])
    grain_range = nodes.new('ShaderNodeMapRange')
    grain_range.inputs['To Min'].default_value = 0.78
    grain_range.inputs['To Max'].default_value = 1.18
    links.new(grain.outputs['Fac'], grain_range.inputs['Value'])
    grained = nodes.new('ShaderNodeMix')
    grained.data_type = 'RGBA'
    grained.blend_type = 'MULTIPLY'
    grained.inputs['Factor'].default_value = 1.0
    links.new(ramp.outputs['Color'], grained.inputs['A'])
    links.new(grain_range.outputs['Result'], grained.inputs['B'])

    # long dark rain streaks running down the stone (noise stretched up and down)
    stretch = nodes.new('ShaderNodeMapping')
    stretch.inputs['Scale'].default_value = (9.0, 9.0, 1.4)
    links.new(position.outputs['Position'], stretch.inputs['Vector'])
    streaks = nodes.new('ShaderNodeTexNoise')
    streaks.inputs['Scale'].default_value = 1.0
    streaks.inputs['Detail'].default_value = 2.0
    links.new(stretch.outputs['Vector'], streaks.inputs['Vector'])
    streak_range = nodes.new('ShaderNodeMapRange')
    streak_range.inputs['From Min'].default_value = 0.35
    streak_range.inputs['From Max'].default_value = 0.65
    streak_range.inputs['To Min'].default_value = 0.55
    streak_range.inputs['To Max'].default_value = 1.05
    streak_range.clamp = True
    links.new(streaks.outputs['Fac'], streak_range.inputs['Value'])
    streaked = nodes.new('ShaderNodeMix')
    streaked.data_type = 'RGBA'
    streaked.blend_type = 'MULTIPLY'
    streaked.inputs['Factor'].default_value = 1.0
    links.new(grained.outputs['Result'], streaked.inputs['A'])
    links.new(streak_range.outputs['Result'], streaked.inputs['B'])

    split = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position.outputs['Position'], split.inputs['Vector'])
    wetness = nodes.new('ShaderNodeMapRange')
    wetness.clamp = True
    wetness.inputs['From Min'].default_value = 0.0
    wetness.inputs['From Max'].default_value = 0.6
    wetness.inputs['To Min'].default_value = 0.65
    wetness.inputs['To Max'].default_value = 0.0
    links.new(split.outputs['Z'], wetness.inputs['Value'])
    splashed = nodes.new('ShaderNodeMix')
    splashed.data_type = 'RGBA'
    splashed.blend_type = 'MIX'
    links.new(wetness.outputs['Result'], splashed.inputs['Factor'])
    links.new(streaked.outputs['Result'], splashed.inputs['A'])
    splashed.inputs['B'].default_value = mc.MUD_SPLASH_COLOUR
    links.new(splashed.outputs['Result'], bsdf.inputs['Base Color'])

    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.8
    bump.inputs['Distance'].default_value = 0.03
    links.new(grain.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.88
    return material


def make_materials():
    surface = mc.surface_material
    plain = mc.plain_material
    return {
        'brick_displaced': surface('brick', tint=(1.0, 0.94, 0.9), true_displacement=True, variation=0.25),
        'brick_plain': surface('brick', tint=(1.0, 0.94, 0.9), variation=0.4),
        'brick_dark': surface('brick', tint=(0.55, 0.48, 0.45), variation=0.1, splash=0.0),
        'brick_arch': surface('brick', tint=(0.86, 0.72, 0.64), variation=0.3, splash=0.0),
        'brick_stack': surface('brick', tint=(0.95, 0.85, 0.8), variation=0.3, splash=0.0),
        'inside_dark': plain('Engine house inside', (0.025, 0.02, 0.017), roughness=0.9),
        'mortar_dark': plain('Engine house mortar', (0.035, 0.03, 0.026), roughness=0.95),
        'corner_fill': plain('Engine house corner fill', (0.16, 0.06, 0.04), roughness=0.9),
        'slate_displaced': surface('slate', true_displacement=True, variation=0.25),
        'slate_ridge': surface('slate', tint=(0.7, 0.7, 0.72), variation=0.2),
        'wood_dark': surface('wood', tint=(0.75, 0.66, 0.58), variation=0.15),
        'wood_barge': surface('wood', tint=(0.75, 0.68, 0.62), variation=0.15),
        'wood_plank': surface('wood', tint=(1.5, 1.12, 0.8), variation=0.2),
        'wood_shed': surface('wood', tint=(0.85, 0.8, 0.75), variation=0.2),
        'wood_crate': surface('wood', tint=(1.3, 1.02, 0.78), variation=0.2),
        'wood_bar': surface('wood', tint=(0.3, 0.27, 0.25), variation=0.05, splash=0.0),
        'wood_door': surface('wood', tint=(0.7, 0.66, 0.62), variation=0.2),
        'stone_light': make_stone_material('Engine house stone light', (0.38, 0.36, 0.32), 0.38),
        'stone_mid': make_stone_material('Engine house stone mid', (0.30, 0.29, 0.26), 0.38),
        'stone_dark': make_stone_material('Engine house stone dark', (0.24, 0.23, 0.21), 0.38),
        'iron': surface('metal', tint=(0.55, 0.55, 0.58), variation=0.1),
        'sheet_metal': surface('metal', tint=(0.8, 0.76, 0.72), variation=0.2),
        'lamp_black': plain('Lamp black metal', (0.02, 0.02, 0.022), roughness=0.5, metallic=0.6),
        'lead': plain('Lead flashing', (0.09, 0.095, 0.10), roughness=0.55, metallic=0.5),
        'glow_a': mc.glow_material('Window glow A', (1.0, 0.36, 0.05), 2.4),
        'glow_b': mc.glow_material('Window glow B', (1.0, 0.50, 0.10), 2.8),
        'glow_c': mc.glow_material('Window glow C', (0.95, 0.28, 0.04), 1.7),
        'lamp_bulb': mc.glow_material('Lamp bulb', (1.0, 0.72, 0.34), 120.0),
    }


# ------------------------------------------------------------------------------------------------------------------
# The groups of shapes, one Blender object each
# ------------------------------------------------------------------------------------------------------------------
BRICK_FLAT, BRICK_DARK, BRICK_ARCH, BRICK_STACK = 0, 1, 2, 3
INSIDE_DARK, MORTAR_DARK, CORNER_FILL = 0, 1, 2
RIDGE_SLATE, UNDER_WOOD, BARGE_WOOD = 0, 1, 2
STONE_LIGHT, STONE_MID, STONE_DARK = 0, 1, 2
IRON, SHEET_METAL, LAMP_BLACK, LEAD = 0, 1, 2, 3
LAMP_BULB = 3
TIMBER_DARK, TIMBER_PLANK, TIMBER_SHED, TIMBER_CRATE, TIMBER_BAR, TIMBER_DOOR = 0, 1, 2, 3, 4, 5


class Kit:
    """All the builders of the engine house in one place."""

    def __init__(self, materials):
        m = materials
        self.materials = m
        self.brick_displaced = mc.MeshBuilder('Engine house brick walls (displaced)', [m['brick_displaced']])
        self.brick_plain = mc.MeshBuilder('Engine house brick (plain)', [m['brick_plain'], m['brick_dark'], m['brick_arch'], m['brick_stack']])
        self.inside = mc.MeshBuilder('Engine house inside and fillers', [m['inside_dark'], m['mortar_dark'], m['corner_fill']])
        self.slate_displaced = mc.MeshBuilder('Engine house slate roof (displaced)', [m['slate_displaced']])
        self.roof_trim = mc.MeshBuilder('Engine house roof trim', [m['slate_ridge'], m['wood_dark'], m['wood_barge']])
        self.stone = mc.MeshBuilder('Engine house stone', [m['stone_light'], m['stone_mid'], m['stone_dark']])
        self.metal = mc.MeshBuilder('Engine house metal', [m['iron'], m['sheet_metal'], m['lamp_black'], m['lead']])
        self.glow = mc.MeshBuilder('Engine house glow', [m['glow_a'], m['glow_b'], m['glow_c'], m['lamp_bulb']])
        self.timber = mc.MeshBuilder('Engine house timber', [m['wood_dark'], m['wood_plank'], m['wood_shed'], m['wood_crate'],
                                                             m['wood_bar'], m['wood_door']])
        self.random = np.random.default_rng(20260519)


# ------------------------------------------------------------------------------------------------------------------
# Walls
# ------------------------------------------------------------------------------------------------------------------
def add_walls(kit, hole_lists):
    """Outside brick faces (front and left displaced; right and back plain), inside dark faces, corner fillers.
    hole_lists: dict of wall name -> list of holes already decided for windows and the door."""
    door_hole = (DOOR_CENTRE - DOOR_WIDTH / 2, DOOR_CENTRE + DOOR_WIDTH / 2, 0.0, DOOR_HEIGHT)
    low = 0.2   # brick starts 20 cm up, the stone plinth hides the rest
    # front gable end (displaced)
    add_wall_cells(kit.brick_displaced, FRONT_WALL, (-HALF_WIDTH, HALF_WIDTH), (low, WALL_HEIGHT), [door_hole], 0)
    add_gable_cells(kit.brick_displaced, FRONT_WALL, 0, HALF_WIDTH)
    # long left wall (displaced)
    add_wall_cells(kit.brick_displaced, LEFT_WALL, (-(BACK_Y - FRONT_Y), 0.0), (low, WALL_HEIGHT), hole_lists['left'], 0)
    # right wall and back gable end (plain, normal-mapped)
    add_wall_cells(kit.brick_plain, RIGHT_WALL, (0.0, BACK_Y - FRONT_Y), (low, WALL_HEIGHT), hole_lists['right'], BRICK_FLAT, biggest_cell=(2.6, 2.3))
    add_wall_cells(kit.brick_plain, BACK_WALL, (-HALF_WIDTH, HALF_WIDTH), (low, WALL_HEIGHT), [], BRICK_FLAT, biggest_cell=(2.6, 2.3))
    add_gable_cells(kit.brick_plain, BACK_WALL, BRICK_FLAT, HALF_WIDTH, columns=2, band_height=1.5)

    # inside faces (dark, plain): the long walls and gable ends, up to just inside the roof slab
    inner_half = HALF_WIDTH - WALL_THICKNESS
    inner_top = GABLE_APEX - SLOPE * inner_half + 0.0
    inside = kit.inside
    add_wall_cells(inside, FRONT_WALL, (-inner_half, inner_half), (0.0, inner_top), [door_hole], INSIDE_DARK, biggest_cell=(4.0, 5.0),
                   depth=WALL_THICKNESS, inside=True)
    add_gable_cells(inside, FRONT_WALL, INSIDE_DARK, inner_half, depth=WALL_THICKNESS, inside=True, columns=1, band_height=9.0)
    add_wall_cells(inside, BACK_WALL, (-inner_half, inner_half), (0.0, inner_top), [], INSIDE_DARK, biggest_cell=(8.0, 6.0),
                   depth=WALL_THICKNESS, inside=True)
    add_gable_cells(inside, BACK_WALL, INSIDE_DARK, inner_half, depth=WALL_THICKNESS, inside=True, columns=1, band_height=9.0)
    long_range = (WALL_THICKNESS, BACK_Y - FRONT_Y - WALL_THICKNESS)
    add_wall_cells(inside, LEFT_WALL, (-long_range[1], -long_range[0]), (0.0, inner_top), hole_lists['left_inside'], INSIDE_DARK,
                   biggest_cell=(4.0, 5.0), depth=WALL_THICKNESS, inside=True)
    add_wall_cells(inside, RIGHT_WALL, long_range, (0.0, inner_top), hole_lists['right_inside'], INSIDE_DARK,
                   biggest_cell=(4.0, 5.0), depth=WALL_THICKNESS, inside=True)

    # corner fillers: plain red-brown blocks set 2 cm inside every outer corner so no gap shows through a displaced corner
    for corner_x, corner_y, sx, sy in [(LEFT_X, FRONT_Y, 1, 1), (RIGHT_X, FRONT_Y, -1, 1), (LEFT_X, BACK_Y, 1, -1), (RIGHT_X, BACK_Y, -1, -1)]:
        x0, x1 = sorted([corner_x + sx * 0.03, corner_x + sx * 0.40])
        y0, y1 = sorted([corner_y + sy * 0.03, corner_y + sy * 0.40])
        inside.add_box(((x0 + x1) / 2, (y0 + y1) / 2, 2.3), (x1 - x0, y1 - y0, 4.6), slot=CORNER_FILL)


# ------------------------------------------------------------------------------------------------------------------
# Plinth and the stone doorway
# ------------------------------------------------------------------------------------------------------------------
def add_stone_blocks(kit, face, along_from, along_to, height_from, height_to, depth_out, depth_in, longest=1.5, shortest=0.8):
    """A row of dressed stone blocks along a wall with thin dark gaps between them."""
    random = kit.random
    cursor = along_from
    while cursor < along_to - 1e-6:
        length = float(random.uniform(shortest, longest))
        block_end = min(along_to, cursor + length)
        if along_to - block_end < shortest * 0.6:
            block_end = along_to
        slot = int(random.integers(0, 3))
        add_wall_box(kit.stone, face, cursor + 0.006, block_end - 0.006, height_from, height_to - 0.006, -depth_out, depth_in, slot=slot)
        cursor = block_end
    # dark mortar behind the joints
    add_wall_box(kit.inside, face, along_from + 0.02, along_to - 0.02, height_from, height_to - 0.02, -depth_out + 0.03, depth_in - 0.02, slot=MORTAR_DARK)


def add_plinth(kit):
    """A weathered stone plinth all round the base: a lower band of blocks and a thicker capping course on top."""
    out, into = PLINTH_PROJECTION, 0.15
    cap_out = out + 0.04
    cap_from = PLINTH_HEIGHT - 0.09
    door_edge = DOOR_WIDTH / 2 + 0.8          # the doorway stone starts here
    corner = HALF_WIDTH - into                # where the front/back plinth stops, so it meets the side plinths without overlap
    length = BACK_Y - FRONT_Y
    for face, along_from, along_to in ((FRONT_WALL, -corner, -door_edge), (FRONT_WALL, door_edge, corner), (BACK_WALL, -corner, corner)):
        add_stone_blocks(kit, face, along_from, along_to, -0.12, cap_from, out, into)
        add_stone_blocks(kit, face, along_from, along_to, cap_from, PLINTH_HEIGHT, cap_out, into, longest=2.2, shortest=1.2)
    for face, along_from, along_to in ((LEFT_WALL, -length, 0.0), (RIGHT_WALL, 0.0, length)):
        add_stone_blocks(kit, face, along_from - out, along_to + out, -0.12, cap_from, out, into, longest=1.8)
        add_stone_blocks(kit, face, along_from - cap_out, along_to + cap_out, cap_from, PLINTH_HEIGHT, cap_out, into, longest=2.2, shortest=1.2)


def add_door_surround(kit):
    """Heavy stone jambs (long-and-short blocks with dark joints) and a thick lintel round the big doorway."""
    half_door = DOOR_WIDTH / 2
    courses = 7
    course_height = DOOR_HEIGHT / courses
    for side in (-1, 1):
        for course in range(courses):
            width = 0.8 if course % 2 == 0 else 0.55
            near, far = sorted([DOOR_CENTRE + side * half_door, DOOR_CENTRE + side * (half_door + width)])
            low, high = course * course_height - (0.12 if course == 0 else 0.0), (course + 1) * course_height
            slot = int(kit.random.integers(0, 3))
            add_wall_box(kit.stone, FRONT_WALL, near, far, low + 0.006, high - 0.006, -0.12, WALL_THICKNESS, slot=slot, skip=('back',))
            add_wall_box(kit.inside, FRONT_WALL, near + 0.035, far - 0.035, low, high, -0.06, WALL_THICKNESS - 0.02, slot=MORTAR_DARK, skip=('back',))
    lintel_half = half_door + 0.85
    add_wall_box(kit.stone, FRONT_WALL, DOOR_CENTRE - lintel_half, DOOR_CENTRE + lintel_half, DOOR_HEIGHT, DOOR_HEIGHT + 0.52,
                 -0.14, WALL_THICKNESS, slot=STONE_MID, skip=('back',))
    add_wall_box(kit.stone, FRONT_WALL, DOOR_CENTRE - lintel_half - 0.08, DOOR_CENTRE + lintel_half + 0.08, DOOR_HEIGHT + 0.52,
                 WALL_HEIGHT, -0.22, WALL_THICKNESS, slot=STONE_LIGHT, skip=('back',))


# ------------------------------------------------------------------------------------------------------------------
# Windows
# ------------------------------------------------------------------------------------------------------------------
def add_voussoirs(kit, face, centre_along, centre_height, inner_radius, outer_radius, angle_from, angle_to, blocks, slot, depth_front=-0.045,
                  depth_back=DEPTH_OF_GLASS):
    """A ring of wedge-shaped arch bricks (an arch head) with thin gaps, and a dark backing plane behind the gaps."""
    gap = 0.012
    for b in range(blocks):
        t0 = angle_from + (angle_to - angle_from) * b / blocks
        t1 = angle_from + (angle_to - angle_from) * (b + 1) / blocks
        pad_in, pad_out = gap / (2 * inner_radius), gap / (2 * outer_radius)

        def ring_point(radius, angle, depth):
            return face.point(centre_along + radius * math.cos(angle), centre_height + radius * math.sin(angle), depth)

        front = [ring_point(inner_radius, t0 + pad_in, depth_front), ring_point(inner_radius, t1 - pad_in, depth_front),
                 ring_point(outer_radius, t1 - pad_out, depth_front), ring_point(outer_radius, t0 + pad_out, depth_front)]
        back = [ring_point(inner_radius, t0 + pad_in, depth_back), ring_point(inner_radius, t1 - pad_in, depth_back),
                ring_point(outer_radius, t1 - pad_out, depth_back), ring_point(outer_radius, t0 + pad_out, depth_back)]
        add_prism(kit.brick_plain, front, back, slot=slot, skip_b=True)
        backing = [ring_point(inner_radius, t0, depth_front + 0.07), ring_point(inner_radius, t1, depth_front + 0.07),
                   ring_point(outer_radius, t1, depth_front + 0.07), ring_point(outer_radius, t0, depth_front + 0.07)]
        add_face(kit.inside, backing, MORTAR_DARK, normal=face.outward)


def add_window(kit, face, centre_along, sill_height, width, rectangle_height, arched, pane_seed, silhouettes=()):
    """One window with a stone sill, a brick arch head, a dark wooden frame with glazing bars, and warm glowing panes.
    Returns the hole (along_from, along_to, height_from, height_to) that the wall must leave open."""
    random = np.random.default_rng(pane_seed)
    half = width / 2.0
    a_left, a_right = centre_along - half, centre_along + half
    spring = sill_height + rectangle_height                     # where an arch starts
    top = spring + half if arched else spring
    glass = DEPTH_OF_GLASS
    bar_front, bar_back = 0.15, glass + 0.005
    frame_width, bar_width = 0.07, 0.05
    centre_point = face.point(centre_along, (sill_height + top) / 2, glass / 2)

    # reveals (the thick of the wall seen at each side of the glass)
    for a_side in (a_left, a_right):
        add_face(kit.brick_plain, [face.point(a_side, sill_height, 0.0), face.point(a_side, spring, 0.0),
                                   face.point(a_side, spring, glass), face.point(a_side, sill_height, glass)], BRICK_DARK, toward=centre_point)
    # stone sill (its top is the bottom reveal)
    add_wall_box(kit.stone, face, a_left - 0.14, a_right + 0.14, sill_height - 0.10, sill_height, -0.12, glass, slot=STONE_LIGHT)
    add_wall_box(kit.stone, face, a_left - 0.10, a_right + 0.10, sill_height - 0.22, sill_height - 0.10, -0.04, 0.1, slot=STONE_MID)

    # arch head
    if arched:
        add_voussoirs(kit, face, centre_along, spring, half, half + 0.30, 0.0, math.pi, 11, BRICK_ARCH)
    else:
        rise = 0.05
        radius = (half ** 2 + rise ** 2) / (2 * rise)
        circle_height = top + rise - radius
        reach = half + 0.12
        angle_limit = math.asin(reach / radius)
        add_voussoirs(kit, face, centre_along, circle_height, radius, radius + 0.30, math.pi / 2 - angle_limit, math.pi / 2 + angle_limit, 9, BRICK_ARCH)

    # frame bars (dark wood) in front of the glass
    def bar(a0, a1, z0, z1, front=bar_front):
        add_wall_box(kit.timber, face, a0, a1, z0, z1, front, bar_back, slot=TIMBER_BAR, skip=('back',))

    bar(a_left, a_left + frame_width, sill_height, spring if arched else top)
    bar(a_right - frame_width, a_right, sill_height, spring if arched else top)
    bar(a_left, a_right, sill_height, sill_height + frame_width)
    if not arched:
        bar(a_left, a_right, top - frame_width, top)
    columns = 2
    rows = max(2, int(round(rectangle_height / 0.42)))
    column_edges = [a_left + frame_width + (width - 2 * frame_width) * c / columns for c in range(columns + 1)]
    inner_bottom = sill_height + frame_width
    inner_top = spring - (0.03 if arched else frame_width)
    row_edges = [inner_bottom + (inner_top - inner_bottom) * r / rows for r in range(rows + 1)]
    for edge in column_edges[1:-1]:
        bar(edge - bar_width / 2, edge + bar_width / 2, sill_height, top - (0.0 if arched else frame_width), front=bar_front - 0.012)
    for edge in row_edges[1:-1]:
        bar(a_left, a_right, edge - bar_width / 2, edge + bar_width / 2, front=bar_front - 0.024)

    # glowing panes, one flat face each, with different brightness so the window looks lived-in
    def pane(a0, a1, z0, z1):
        slot = int(random.integers(0, 3))
        add_face(kit.glow, [face.point(a0, z0, glass), face.point(a1, z0, glass), face.point(a1, z1, glass), face.point(a0, z1, glass)],
                 slot, normal=face.outward)

    for c in range(columns):
        for r in range(rows):
            a0 = column_edges[c] + (bar_width / 2 if c > 0 else 0.0)
            a1 = column_edges[c + 1] - (bar_width / 2 if c < columns - 1 else 0.0)
            z0 = row_edges[r] + (bar_width / 2 if r > 0 else 0.0)
            z1 = row_edges[r + 1] - (bar_width / 2 if r < rows - 1 else 0.0)
            pane(a0, a1, z0, z1)

    if arched:
        # transom bar across the springing line, then the curved top: a rim of short bars and two fan panes
        bar(a_left, a_right, spring - 0.03, spring + 0.03, front=bar_front - 0.036)
        inner_radius = half - frame_width
        segments = 12
        rim_points = [(centre_along + (half - frame_width / 2) * math.cos(math.pi * s / segments),
                       spring + (half - frame_width / 2) * math.sin(math.pi * s / segments)) for s in range(segments + 1)]
        for (a0, z0), (a1, z1) in zip(rim_points[:-1], rim_points[1:]):
            add_timber(kit.timber, face.point(a0, z0, (bar_front + bar_back) / 2), face.point(a1, z1, (bar_front + bar_back) / 2),
                       frame_width, bar_back - bar_front, TIMBER_BAR, width_hint=np.cross(face.outward, face.point(a1, z1) - face.point(a0, z0)),
                       extend=0.012)
        middle_depth = (bar_front + bar_back) / 2
        for angle in (math.pi / 4, 3 * math.pi / 4):   # two radial bars
            start = face.point(centre_along, spring, middle_depth)
            end = face.point(centre_along + (half - frame_width / 2) * math.cos(angle), spring + (half - frame_width / 2) * math.sin(angle), middle_depth)
            add_timber(kit.timber, start, end, bar_width, bar_back - bar_front, TIMBER_BAR, width_hint=np.cross(face.outward, end - start))
        for side in (-1, 1):
            start_angle = math.asin(0.03 / inner_radius)
            samples = 10
            arc = []
            for s in range(samples + 1):
                angle = start_angle + (math.pi / 2 - bar_width / 2 / inner_radius - start_angle) * s / samples
                arc.append((centre_along + side * inner_radius * math.cos(angle), spring + inner_radius * math.sin(angle)))
            outline = arc + [(centre_along + side * bar_width / 2, spring + 0.03)]
            add_face(kit.glow, [face.point(a, z, glass) for a, z in outline], int(random.integers(0, 3)), normal=face.outward)

    # dark shapes just inside the glass (a pillar, a blind, a curtain) so the glow does not look like a flat lamp
    for a0, a1, z0, z1 in silhouettes:
        add_face(kit.inside, [face.point(a0, z0, glass - 0.012), face.point(a1, z0, glass - 0.012), face.point(a1, z1, glass - 0.012),
                              face.point(a0, z1, glass - 0.012)], INSIDE_DARK, normal=face.outward)
    return (a_left, a_right, sill_height, top)


# ------------------------------------------------------------------------------------------------------------------
# Roof
# ------------------------------------------------------------------------------------------------------------------
def add_roof(kit):
    slate_material = kit.materials['slate_displaced']
    tile = float(slate_material['mine_tile_metres'])
    y_front, y_back = FRONT_Y - OVERHANG, BACK_Y + OVERHANG
    edge_across = HALF_WIDTH + OVERHANG
    for side in (-1, 1):
        normal = np.array([side * SLOPE, 0.0, 1.0])
        normal /= np.linalg.norm(normal)
        uphill = UP - np.dot(UP, normal) * normal
        uphill /= np.linalg.norm(uphill)
        eave_point = np.array([side * edge_across, 0.0, slate_height(side * edge_across)])
        raw_row = float(np.dot(eave_point, uphill)) / tile
        row_shift = (0.0628 - raw_row) % 0.125         # lines the lowest slate row up with the roof edge
        across_marks = break_points(0.0, edge_across, 1.5, [])
        along_marks = break_points(y_front, y_back, 2.4, [])
        for i in range(len(across_marks) - 1):
            for j in range(len(along_marks) - 1):
                a0, a1, y0, y1 = across_marks[i], across_marks[i + 1], along_marks[j], along_marks[j + 1]
                corners = [(side * a0, y0, slate_height(side * a0)), (side * a1, y0, slate_height(side * a1)),
                           (side * a1, y1, slate_height(side * a1)), (side * a0, y1, slate_height(side * a0))]
                add_face(kit.slate_displaced, corners, 0, normal=normal, uv_shift=(0.0, row_shift))
        # underside, eave edge and the two verge edges (dark wood)
        ridge_under, eave_under = SLATE_RIDGE_HEIGHT - SLAB_THICKNESS, slate_height(side * edge_across) - SLAB_THICKNESS
        add_face(kit.roof_trim, [(0, y_front, ridge_under), (side * edge_across, y_front, eave_under), (side * edge_across, y_back, eave_under),
                                 (0, y_back, ridge_under)], UNDER_WOOD, normal=(0, 0, -1))
        add_face(kit.roof_trim, [(side * edge_across, y_front, eave_under), (side * edge_across, y_front, slate_height(side * edge_across)),
                                 (side * edge_across, y_back, slate_height(side * edge_across)), (side * edge_across, y_back, eave_under)],
                 UNDER_WOOD, normal=(side, 0, 0))
        for y, direction in ((y_front, -1), (y_back, 1)):
            add_face(kit.roof_trim, [(0, y, SLATE_RIDGE_HEIGHT), (side * edge_across, y, slate_height(side * edge_across)),
                                     (side * edge_across, y, eave_under), (0, y, ridge_under)], UNDER_WOOD, normal=(0, direction, 0))
    # barge board along the sloping edges of the roof at each gable end: one chevron-shaped board, mitred at the ridge
    for y, direction in ((y_front, -1), (y_back, 1)):
        reach = edge_across + 0.02

        def top_line(x):
            return slate_height(x) + 0.035

        board = [(-reach, top_line(-reach)), (0.0, top_line(0.0)), (reach, top_line(reach)),
                 (reach, top_line(reach) - 0.32), (0.0, top_line(0.0) - 0.32), (-reach, top_line(-reach) - 0.32)]
        if direction < 0:
            add_extruded_outline(kit.roof_trim, board, y - 0.047, y - 0.002, BARGE_WOOD)
        else:
            add_extruded_outline(kit.roof_trim, board, y + 0.002, y + 0.047, BARGE_WOOD)
    # ridge cap: an inverted V of slate-coloured boards laid over the ridge, with a rolled lead edge
    cap_half, cap_drop = 0.5, SLOPE * 0.5
    low_height = SLATE_RIDGE_HEIGHT - cap_drop
    outline = [(-cap_half, low_height), (-cap_half, low_height + 0.10), (0.0, RIDGE_TOP), (cap_half, low_height + 0.10), (cap_half, low_height),
               (0.0, SLATE_RIDGE_HEIGHT)]
    ridge_front, ridge_back = y_front - 0.02, y_back + 0.02
    for k in range(len(outline)):
        (x0, z0), (x1, z1) = outline[k], outline[(k + 1) % len(outline)]
        if k == 4 or k == 5:
            continue   # the lower edges sit on the slate, nobody sees them
        add_face(kit.roof_trim, [(x0, ridge_front, z0), (x1, ridge_front, z1), (x1, ridge_back, z1), (x0, ridge_back, z0)],
                 RIDGE_SLATE, away=(0.0, 0.5 * (ridge_front + ridge_back), SLATE_RIDGE_HEIGHT - 0.1))
    for y, direction in ((ridge_front, -1), (ridge_back, 1)):
        add_face(kit.roof_trim, [(x, y, z) for x, z in outline], RIDGE_SLATE, normal=(0, direction, 0))


def add_rafter_tails_and_tie_plates(kit):
    """Rafter ends showing under the overhanging eaves, and round iron tie-bar plates high on the long walls."""
    edge_across = HALF_WIDTH + OVERHANG
    for side in (-1, 1):
        for y in np.arange(0.2, BACK_Y - 0.1, 0.75):
            def tail_point(x):
                return (side * x, y, slate_height(side * x) - SLAB_THICKNESS - 0.06)
            add_timber(kit.roof_trim, tail_point(HALF_WIDTH - 0.05), tail_point(edge_across - 0.03), 0.09, 0.12, BARGE_WOOD, width_hint=(0, 1, 0),
                       grain_shift=(float(kit.random.random()), float(kit.random.random())))
    plate_height = 4.0
    for y in (2.3, 9.5):
        kit.metal.add_cylinder((LEFT_X - 0.002, y, plate_height), (LEFT_X - 0.04, y, plate_height), 0.17, sides=16, slot=IRON)
        kit.metal.add_cylinder((LEFT_X - 0.04, y, plate_height), (LEFT_X - 0.075, y, plate_height), 0.05, sides=10, slot=IRON)
    for y in (2.0, 5.6, 9.0):
        kit.metal.add_cylinder((RIGHT_X + 0.002, y, plate_height), (RIGHT_X + 0.04, y, plate_height), 0.17, sides=16, slot=IRON)
        kit.metal.add_cylinder((RIGHT_X + 0.04, y, plate_height), (RIGHT_X + 0.075, y, plate_height), 0.05, sides=10, slot=IRON)


# ------------------------------------------------------------------------------------------------------------------
# Gutters and downpipes
# ------------------------------------------------------------------------------------------------------------------
def add_smooth_strip(builder, loop_a, loop_b, slot, normal_hint):
    """A curved surface made of quads joining two matching polylines, shaded smoothly."""
    loop_a = np.asarray(loop_a, dtype=float)
    loop_b = np.asarray(loop_b, dtype=float)
    count = len(loop_a)
    vertices = np.concatenate([loop_a, loop_b])
    faces = [[i, i + 1, count + i + 1, count + i] for i in range(count - 1)]
    middle = count // 2
    test = newell_normal(vertices[faces[middle]])
    if float(np.dot(test, normal_hint(vertices[faces[middle]].mean(axis=0)))) < 0:
        faces = [f[::-1] for f in faces]
    builder.add_indexed_faces(vertices, faces, slot=slot, smooth=True)


def add_gutter_and_pipes(kit):
    edge_across = HALF_WIDTH + OVERHANG
    y_start, y_end = FRONT_Y - OVERHANG + 0.02, BACK_Y + OVERHANG - 0.02
    outer_radius, inner_radius = 0.098, 0.086
    for side in (-1, 1):
        centre_x = side * (edge_across + 0.12)
        centre_z = slate_height(side * edge_across) - 0.06
        steps = 12
        angles = [math.pi + math.pi * s / steps for s in range(steps + 1)]

        def ring(radius, y):
            return [(centre_x + radius * math.cos(t), y, centre_z + radius * math.sin(t)) for t in angles]

        centre = np.array([centre_x, 0.0, centre_z])
        add_smooth_strip(kit.metal, ring(outer_radius, y_start), ring(outer_radius, y_end), IRON,
                         lambda p: p - np.array([centre_x, p[1], centre_z]))
        add_smooth_strip(kit.metal, ring(inner_radius, y_start), ring(inner_radius, y_end), IRON,
                         lambda p: np.array([centre_x, p[1], centre_z]) - p)
        for t_index in (0, steps):    # rims
            outer, inner = ring(outer_radius, 0)[t_index], ring(inner_radius, 0)[t_index]
            add_face(kit.metal, [(outer[0], y_start, outer[2]), (inner[0], y_start, inner[2]), (inner[0], y_end, inner[2]), (outer[0], y_end, outer[2])],
                     IRON, normal=(0, 0, 1))
        for y, direction in ((y_start, -1), (y_end, 1)):
            loop = ring(outer_radius, y) + ring(inner_radius, y)[::-1]
            add_face(kit.metal, loop, IRON, normal=(0, direction, 0))
        # brackets that hold the gutter to the roof edge
        for y in np.linspace(y_start + 0.4, y_end - 0.4, 11):
            kit.metal.add_box((side * (edge_across + 0.04), y, centre_z - 0.03), (0.09, 0.035, 0.07), slot=IRON)
            kit.metal.add_box((centre_x, y, centre_z - outer_radius - 0.004), (0.05, 0.035, 0.012), slot=IRON)
    # downpipes on the left wall (the camera side) with a rain-water head under the gutter
    for y_position in (0.26, 6.25):
        add_downpipe(kit, -1, y_position)


def add_downpipe(kit, side, y_position):
    metal = kit.metal
    gutter_x = side * (HALF_WIDTH + OVERHANG + 0.12)
    pipe_x = side * (HALF_WIDTH + 0.16)
    radius = 0.052
    gutter_bottom = slate_height(side * (HALF_WIDTH + OVERHANG)) - 0.06 - 0.098
    ground = mc.ground_height(pipe_x, y_position)
    # rain-water head
    metal.add_box((gutter_x, y_position, gutter_bottom + 0.02), (0.2, 0.22, 0.26), slot=IRON)
    metal.add_box((gutter_x, y_position, gutter_bottom + 0.16), (0.24, 0.26, 0.04), slot=IRON)
    # swan neck
    top_of_neck = gutter_bottom - 0.12
    metal.add_cylinder((gutter_x, y_position, top_of_neck + 0.01), (gutter_x, y_position, top_of_neck - 0.22), radius, sides=10, slot=IRON, caps=False)
    metal.add_cylinder((gutter_x, y_position, top_of_neck - 0.22), (pipe_x, y_position, top_of_neck - 0.52), radius, sides=10, slot=IRON, caps=False)
    metal.add_cylinder((pipe_x, y_position, top_of_neck - 0.5), (pipe_x, y_position, ground + 0.34), radius, sides=10, slot=IRON, caps=False)
    # shoe at the bottom kicking out into the yard
    metal.add_cylinder((pipe_x, y_position, ground + 0.36), (pipe_x + side * 0.12, y_position, ground + 0.17), radius, sides=10, slot=IRON, caps=False)
    metal.add_cylinder((pipe_x + side * 0.12, y_position, ground + 0.17), (pipe_x + side * 0.30, y_position, ground + 0.12), radius, sides=10, slot=IRON)
    # collars and wall brackets
    wall_x = side * HALF_WIDTH
    for height in (0.85, 1.9, 2.95, top_of_neck - 0.75):
        metal.add_cylinder((pipe_x, y_position, height - 0.025), (pipe_x, y_position, height + 0.025), radius + 0.014, sides=10, slot=IRON)
        arm_middle = (wall_x + pipe_x) / 2
        metal.add_box((arm_middle, y_position, height), (abs(pipe_x - wall_x), 0.035, 0.035), slot=IRON)


# ------------------------------------------------------------------------------------------------------------------
# Chimney stack on the ridge
# ------------------------------------------------------------------------------------------------------------------
def add_chimney_stack(kit):
    centre_y, half_x, half_y = 4.75, 0.5, 0.5
    bottom = SLATE_RIDGE_HEIGHT - SLOPE * half_x - 0.09
    top = 8.75
    brick = kit.brick_plain
    brick.add_box((0.0, centre_y, (bottom + top) / 2), (2 * half_x, 2 * half_y, top - bottom), slot=BRICK_STACK)
    brick.add_box((0.0, centre_y, top + 0.06), (2 * half_x + 0.1, 2 * half_y + 0.1, 0.12), slot=BRICK_STACK)
    brick.add_box((0.0, centre_y, top + 0.18), (2 * half_x + 0.2, 2 * half_y + 0.2, 0.12), slot=BRICK_STACK)
    cap_bottom, cap_top = top + 0.24, top + 0.36
    stone = kit.stone
    for sx in (-1, 1):
        stone.add_box((sx * 0.43, centre_y, (cap_bottom + cap_top) / 2), (0.34, 1.26, 0.12), slot=STONE_LIGHT)
        stone.add_box((0.0, centre_y + sx * 0.43, (cap_bottom + cap_top) / 2), (0.52, 0.34, 0.12), slot=STONE_LIGHT)
    kit.inside.add_polygon([(-0.26, centre_y - 0.26, cap_bottom + 0.005), (0.26, centre_y - 0.26, cap_bottom + 0.005),
                            (0.26, centre_y + 0.26, cap_bottom + 0.005), (-0.26, centre_y + 0.26, cap_bottom + 0.005)], slot=INSIDE_DARK)
    # lead flashing: a stepped strip up each side face, plus an apron lying on the slates
    lead = kit.metal
    lift = 0.26
    for sign, y_face in ((-1, centre_y - half_y - 0.012), (1, centre_y + half_y + 0.012)):
        for side in (-1, 1):
            x_near, x_far = 0.0, side * half_x
            add_face(lead, [(x_near, y_face, slate_height(x_near)), (x_far, y_face, slate_height(x_far)),
                            (x_far, y_face, slate_height(x_far) + lift), (x_near, y_face, slate_height(x_near) + lift)], LEAD, normal=(0, sign, 0))
            apron_y = y_face + sign * 0.22
            normal = np.array([side * SLOPE, 0.0, 1.0])
            lifted = 0.012
            add_face(lead, [(x_near, y_face, slate_height(x_near) + lifted), (x_far, y_face, slate_height(x_far) + lifted),
                            (x_far, apron_y, slate_height(x_far) + lifted), (x_near, apron_y, slate_height(x_near) + lifted)], LEAD, normal=normal)
    for side in (-1, 1):
        x_face = side * (half_x + 0.012)
        low = slate_height(x_face)
        add_face(lead, [(x_face, centre_y - half_y, low), (x_face, centre_y + half_y, low), (x_face, centre_y + half_y, low + lift),
                        (x_face, centre_y - half_y, low + lift)], LEAD, normal=(side, 0, 0))
        apron_x = side * (half_x + 0.32)
        add_face(lead, [(x_face, centre_y - half_y - 0.22, low + 0.012), (apron_x, centre_y - half_y - 0.22, slate_height(apron_x) + 0.012),
                        (apron_x, centre_y + half_y + 0.22, slate_height(apron_x) + 0.012), (x_face, centre_y + half_y + 0.22, low + 0.012)],
                 LEAD, normal=(side * SLOPE, 0, 1))


# ------------------------------------------------------------------------------------------------------------------
# Lean-to shed against the left wall
# ------------------------------------------------------------------------------------------------------------------
def add_shed(kit):
    """A small lean-to plank shed against the left wall near the front corner: vertical planks, sloping sheet-metal roof,
    a plank door (ledges, brace, hinges, latch) on the side that faces the camera, and a step."""
    wall_x = LEFT_X                           # the shed leans on the brick face
    far_x = LEFT_X - 1.8
    y_front, y_back = 0.62, 2.95
    high_side, low_side = 2.52, 2.02          # wall height next to the house and at the outer edge
    timber = kit.timber
    random = kit.random

    def board_top(x):
        return low_side + (high_side - low_side) * (x - far_x) / (wall_x - far_x)

    def grain():
        return (float(random.random()), float(random.random()))

    target_width = 0.142
    count = int(round((wall_x - far_x) / target_width))
    step = (wall_x - far_x) / count
    for y in (y_front, y_back):
        for k in range(count):
            x = far_x + step * (k + 0.5)
            add_timber(timber, (x, y, mc.ground_height(x, y)), (x, y, board_top(x)), step - 0.012, 0.03, TIMBER_SHED, width_hint=(1, 0, 0),
                       grain_shift=grain())
    count_side = int(round((y_back - y_front) / target_width))
    step_side = (y_back - y_front) / count_side
    for k in range(count_side):
        y = y_front + step_side * (k + 0.5)
        add_timber(timber, (far_x, y, mc.ground_height(far_x, y)), (far_x, y, low_side), step_side - 0.012, 0.03, TIMBER_SHED,
                   width_hint=(0, 1, 0), grain_shift=grain())
    for x, y in ((far_x, y_front), (far_x, y_back), (wall_x - 0.05, y_front), (wall_x - 0.05, y_back)):
        add_timber(timber, (x, y, mc.ground_height(x, y)), (x, y, board_top(x)), 0.1, 0.1, TIMBER_DOOR, width_hint=(1, 0, 0))

    # sloping sheet-metal roof that falls away from the house, overhanging the three open sides
    slope_wall = (high_side - low_side) / (wall_x - far_x)
    roof_wall_x, roof_far_x = wall_x + 0.03, far_x - 0.14
    roof_y0, roof_y1 = y_front - 0.13, y_back + 0.13
    lift_wall = high_side + 0.03
    lift_far = lift_wall - slope_wall * (roof_wall_x - roof_far_x)
    top_loop = [(roof_wall_x, roof_y0, lift_wall), (roof_far_x, roof_y0, lift_far), (roof_far_x, roof_y1, lift_far), (roof_wall_x, roof_y1, lift_wall)]
    add_prism(kit.metal, top_loop, [(x, y, z - 0.04) for x, y, z in top_loop], slot=SHEET_METAL)
    for k in range(1, 9):
        y = roof_y0 + (roof_y1 - roof_y0) * k / 9
        add_timber(kit.metal, (roof_wall_x, y, lift_wall + 0.018), (roof_far_x, y, lift_far + 0.018), 0.05, 0.03, SHEET_METAL, width_hint=(0, 1, 0))
    add_face(kit.metal, [(LEFT_X - 0.012, roof_y0, lift_wall), (LEFT_X - 0.012, roof_y1, lift_wall), (LEFT_X - 0.012, roof_y1, lift_wall + 0.26),
                         (LEFT_X - 0.012, roof_y0, lift_wall + 0.26)], LEAD, normal=(-1, 0, 0))

    # the plank door, with its front face about 3.4 cm proud of the shed planks
    door_width, door_height = 0.94, 1.86
    door_centre_x = (far_x + wall_x) / 2 + 0.05
    plank_centre_y = y_front - 0.015 - 0.017
    front_of_planks = plank_centre_y - 0.017
    plank_count = 8
    plank_step = door_width / plank_count
    for k in range(plank_count):
        x = door_centre_x - door_width / 2 + plank_step * (k + 0.5)
        floor = mc.ground_height(x, y_front) + 0.04
        add_timber(timber, (x, plank_centre_y, floor), (x, plank_centre_y, floor + door_height), plank_step - 0.01, 0.034, TIMBER_DOOR,
                   width_hint=(1, 0, 0), grain_shift=grain())
    floor = mc.ground_height(door_centre_x, y_front) + 0.04
    ledge_y = front_of_planks - 0.011
    ledge_heights = (floor + 0.34, floor + door_height - 0.3)
    for height in ledge_heights:
        add_timber(timber, (door_centre_x - door_width / 2, ledge_y, height), (door_centre_x + door_width / 2, ledge_y, height), 0.13, 0.03, TIMBER_DOOR,
                   width_hint=(0, 0, 1))
    add_timber(timber, (door_centre_x - door_width / 2 + 0.08, ledge_y - 0.012, ledge_heights[0]), (door_centre_x + door_width / 2 - 0.08, ledge_y - 0.012, ledge_heights[1]),
               0.11, 0.024, TIMBER_DOOR, width_hint=(0, 0, 1))
    strap_y = ledge_y - 0.015 - 0.006
    for height in ledge_heights:
        kit.metal.add_box((door_centre_x - door_width / 2 + 0.24, strap_y, height), (0.48, 0.012, 0.045), slot=LAMP_BLACK)
        kit.metal.add_box((door_centre_x - door_width / 2 + 0.03, strap_y, height), (0.06, 0.016, 0.1), slot=LAMP_BLACK)
    handle_x = door_centre_x + door_width / 2 - 0.12
    kit.metal.add_box((handle_x, front_of_planks - 0.008, floor + 0.93), (0.05, 0.016, 0.22), slot=LAMP_BLACK)
    kit.metal.add_ring((handle_x, front_of_planks - 0.026, floor + 0.86), (0, 1, 0), 0.05, 0.036, 0.014, sides=16, slot=LAMP_BLACK)
    # a plank step in front of the door
    step_height = mc.ground_height(door_centre_x, y_front) + 0.05
    add_timber(timber, (door_centre_x - 0.5, y_front - 0.24, step_height), (door_centre_x + 0.5, y_front - 0.24, step_height), 0.3, 0.08, TIMBER_SHED,
               width_hint=(0, 1, 0))


# ------------------------------------------------------------------------------------------------------------------
# Lamp over the doorway
# ------------------------------------------------------------------------------------------------------------------
def add_lamp(kit):
    along = -1.2
    face = FRONT_WALL
    black = kit.metal
    height = 5.3
    add_wall_box(black, face, along - 0.07, along + 0.07, height - 0.2, height + 0.22, -0.035, 0.0, slot=LAMP_BLACK)
    black.add_cylinder(face.point(along, height + 0.12, -0.03), face.point(along, height + 0.17, -0.50), 0.018, sides=8, slot=LAMP_BLACK)
    black.add_cylinder(face.point(along, height - 0.14, -0.03), face.point(along, height + 0.15, -0.30), 0.012, sides=8, slot=LAMP_BLACK)
    black.add_cylinder(face.point(along, height + 0.17, -0.50), face.point(along, height + 0.17, -0.58), 0.022, sides=8, slot=LAMP_BLACK)
    shade_centre = face.point(along, 0.0, -0.58)
    top_point = np.array([shade_centre[0], shade_centre[1], height + 0.19])
    bottom_point = np.array([shade_centre[0], shade_centre[1], height - 0.06])
    black.add_cylinder(top_point, bottom_point, 0.045, radius_end=0.20, sides=16, slot=LAMP_BLACK, caps=False)
    black.add_cylinder(top_point, top_point + np.array([0, 0, 0.03]), 0.045, sides=10, slot=LAMP_BLACK)
    kit.glow.add_blob(bottom_point + np.array([0, 0, 0.07]), (0.055, 0.055, 0.065), slot=LAMP_BULB, subdivisions=2, smooth=True)


# ------------------------------------------------------------------------------------------------------------------
# Leaning planks and the crate
# ------------------------------------------------------------------------------------------------------------------
def add_leaning_planks(kit):
    """Two piles of rough timber planks leaning against the gable wall, one each side of the doorway."""
    face = FRONT_WALL
    random = kit.random
    # (along position at the top, how far the foot stands from the wall, plank length, sideways lean at the foot)
    piles = [
        [(-2.70, 0.46, 3.1, 0.10), (-2.86, 0.62, 2.6, -0.08), (-3.02, 0.44, 2.2, 0.06)],
        [(2.70, 0.44, 3.5, -0.08), (2.88, 0.58, 3.1, 0.14), (3.06, 0.66, 2.7, -0.12), (3.24, 0.50, 2.3, 0.10), (3.42, 0.70, 1.9, -0.10),
         (3.58, 0.52, 1.4, 0.05)],
    ]
    for pile in piles:
        for along_top, foot_out, length, sideways in pile:
            foot = face.point(along_top + sideways, 0.0, -foot_out)
            foot[2] = mc.ground_height(foot[0], foot[1]) + 0.01
            drop = math.sqrt(max(length ** 2 - foot_out ** 2 - sideways ** 2, 0.5))
            top = face.point(along_top, foot[2] + drop, -0.06)
            add_timber(kit.timber, foot, top, 0.215, 0.05, TIMBER_PLANK, width_hint=face.along,
                       grain_shift=(float(random.random()), float(random.random())))
    # two short offcuts lying on the ground beside the right pile
    for along, out, yaw in ((3.1, 1.25, 0.4), (3.5, 1.45, -0.25)):
        centre = face.point(along, 0.0, -out)
        centre[2] = mc.ground_height(centre[0], centre[1]) + 0.04
        direction = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        add_timber(kit.timber, centre - direction * 0.5, centre + direction * 0.5, 0.2, 0.06, TIMBER_PLANK, width_hint=UP)


def add_crate(kit):
    """A slatted wooden crate standing against the front wall near the left corner, with cross braces and a lid."""
    face = FRONT_WALL
    along_centre, depth_centre = -3.68, -0.50
    width, depth, height = 0.92, 0.62, 0.64
    ground = mc.ground_height(*face.point(along_centre, 0.0, depth_centre)[:2])
    base = ground + 0.04
    wood = kit.timber
    random = kit.random

    def point(a, z, d):
        return face.point(along_centre + a, base + z, depth_centre + d)

    def grain():
        return (float(random.random()), float(random.random()))

    # dark box inside so it never looks hollow
    kit.inside.add_box(point(0, height / 2, 0), (width - 0.1, depth - 0.1, height - 0.1), slot=INSIDE_DARK, rotation=face.basis)
    # corner posts
    for da in (-width / 2 + 0.035, width / 2 - 0.035):
        for dd in (-depth / 2 + 0.035, depth / 2 - 0.035):
            wood.add_box(point(da, height / 2, dd), (0.07, 0.07, height), slot=TIMBER_CRATE, rotation=face.basis)
    # slats on all four sides
    slat_height, gap = 0.1, 0.035
    rows = int((height - 0.02) // (slat_height + gap))
    for row in range(rows):
        z = 0.03 + slat_height / 2 + row * (slat_height + gap)
        for dd in (-depth / 2, depth / 2):
            add_timber(wood, point(-width / 2, z, dd), point(width / 2, z, dd), slat_height, 0.022, TIMBER_CRATE, width_hint=UP, grain_shift=grain())
        for da in (-width / 2, width / 2):
            add_timber(wood, point(da, z, -depth / 2), point(da, z, depth / 2), slat_height, 0.022, TIMBER_CRATE, width_hint=UP, grain_shift=grain())
    # crossed braces on the front face
    front = -depth / 2 - 0.019
    add_timber(wood, point(-width / 2 + 0.08, 0.07, front), point(width / 2 - 0.08, height - 0.07, front), 0.075, 0.02, TIMBER_CRATE, width_hint=UP)
    add_timber(wood, point(-width / 2 + 0.08, height - 0.07, front), point(width / 2 - 0.08, 0.07, front - 0.018), 0.075, 0.02, TIMBER_CRATE, width_hint=UP)
    # lid boards
    for k in range(4):
        d = -depth / 2 + 0.09 + k * 0.145
        add_timber(wood, point(-width / 2 - 0.02, height + 0.012, d), point(width / 2 + 0.02, height + 0.012, d), 0.135, 0.024, TIMBER_CRATE,
                   width_hint=(0, 1, 0), grain_shift=grain())


# ------------------------------------------------------------------------------------------------------------------
# Inside: dark timber frames behind the doorway
# ------------------------------------------------------------------------------------------------------------------
def add_interior_timbers(kit):
    wood = kit.timber
    inner = HALF_WIDTH - WALL_THICKNESS
    partition_y = 6.4
    underside = SLATE_RIDGE_HEIGHT - SLAB_THICKNESS
    # plank lining on both side walls and a partition wall across the room
    for side in (-1, 1):
        add_face(wood, [(side * (inner - 0.015), WALL_THICKNESS + 0.01, 0.0), (side * (inner - 0.015), partition_y, 0.0),
                        (side * (inner - 0.015), partition_y, 3.0), (side * (inner - 0.015), WALL_THICKNESS + 0.01, 3.0)], TIMBER_DARK,
                 normal=(-side, 0, 0), uv_axes=((0, 0, 1), (0, 1, 0)))
    shoulder = GABLE_APEX - SLOPE * inner - 0.1
    add_face(wood, [(-inner + 0.01, partition_y, 0.0), (inner - 0.01, partition_y, 0.0), (inner - 0.01, partition_y, shoulder),
                    (0.0, partition_y, underside - 0.06), (-inner + 0.01, partition_y, shoulder)], TIMBER_DARK, normal=(0, -1, 0),
             uv_axes=((0, 0, 1), (1, 0, 0)))
    # three open frames: two posts and a tie beam, with diagonal braces
    for y in (1.35, 3.3, 5.25):
        for side in (-1, 1):
            add_timber(wood, (side * (inner - 0.16), y, 0.0), (side * (inner - 0.16), y, 4.15), 0.26, 0.26, TIMBER_DARK, width_hint=(1, 0, 0))
            add_timber(wood, (side * (inner - 0.3), y, 2.15), (side * (inner - 1.25), y, 3.3), 0.15, 0.15, TIMBER_DARK, width_hint=(0, 1, 0))
        add_timber(wood, (-inner, y, 3.4), (inner, y, 3.4), 0.3, 0.24, TIMBER_DARK, width_hint=(0, 0, 1))
        add_timber(wood, (0.0, y, 3.55), (0.0, y, underside - 0.1), 0.18, 0.18, TIMBER_DARK, width_hint=(1, 0, 0))
    # braces across the partition wall
    for side in (-1, 1):
        add_timber(wood, (side * 2.9, partition_y - 0.05, 0.1), (side * 0.5, partition_y - 0.05, 3.6), 0.16, 0.08, TIMBER_DARK, width_hint=(1, 0, 0))
    add_timber(wood, (-inner, partition_y - 0.05, 3.3), (inner, partition_y - 0.05, 3.3), 0.2, 0.08, TIMBER_DARK, width_hint=(0, 0, 1))
    add_timber(wood, (-inner, partition_y - 0.05, 1.1), (inner, partition_y - 0.05, 1.1), 0.2, 0.08, TIMBER_DARK, width_hint=(0, 0, 1))


# ------------------------------------------------------------------------------------------------------------------
# Putting it together
# ------------------------------------------------------------------------------------------------------------------
def build(collection_name='Mine'):
    started = time.time()
    materials = make_materials()
    kit = Kit(materials)

    # windows first, because the walls must leave holes for them
    left_holes, right_holes = [], []
    arched_hole = add_window(kit, LEFT_WALL, -4.7, 1.05, 1.3, 1.55, True, 11,
                             silhouettes=[(-4.7 + 0.10, -4.7 + 0.34, 1.12, 2.25), (-4.7 - 0.58, -4.7 + 0.10, 1.95, 2.02)])
    small_hole = add_window(kit, LEFT_WALL, -7.55, 1.85, 0.95, 1.25, False, 12, silhouettes=[(-7.55 - 0.41, -7.55 + 0.41, 1.92, 2.28)])
    right_hole = add_window(kit, RIGHT_WALL, 5.6, 1.6, 0.95, 1.25, False, 13, silhouettes=[(5.6 - 0.41, 5.6 - 0.05, 1.67, 2.78)])
    left_holes += [arched_hole, small_hole]
    right_holes += [right_hole]
    hole_lists = {'left': left_holes, 'right': right_holes, 'left_inside': left_holes, 'right_inside': right_holes}
    add_walls(kit, hole_lists)
    add_plinth(kit)
    add_door_surround(kit)
    add_roof(kit)
    add_rafter_tails_and_tie_plates(kit)
    add_gutter_and_pipes(kit)
    add_chimney_stack(kit)
    add_shed(kit)
    add_lamp(kit)
    add_leaning_planks(kit)
    add_crate(kit)
    add_interior_timbers(kit)

    names, triangles, displaced = [], 0, []
    for builder, is_displaced in [(kit.brick_displaced, True), (kit.slate_displaced, True), (kit.brick_plain, False), (kit.inside, False),
                                  (kit.roof_trim, False), (kit.stone, False), (kit.metal, False), (kit.glow, False), (kit.timber, False)]:
        obj = builder.finish(collection_name)
        if is_displaced:
            mc.use_real_displacement(obj)
            displaced.append(obj.name)
        names.append(obj.name)
        triangles += sum(len(p.vertices) - 2 for p in obj.data.polygons)
    elapsed = time.time() - started
    mc.say(f'engine house built: {len(names)} objects, {triangles} triangles before displacement, {elapsed:.1f} s')
    return {'objects': names, 'notes': f'engine house; {triangles} triangles before displacement; displaced objects: {displaced}',
            'triangle_count': triangles, 'displaced': displaced, 'seconds': elapsed}
