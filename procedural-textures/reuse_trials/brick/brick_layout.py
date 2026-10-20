# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# BRICK LAYOUT: the small box that answers "which brick am I on, and where on it?" for every dot, and hands the shared layers the same
# eleven numbers the slate LAYOUT gives them (the "bundle": piece_id, row, local_x, local_y, piece_width, piece_height, edge_distance,
# top_edge_distance, gap_mask, piece_mask, base_height; their meaning is in recipes/slate_layers/interface/interface.md). It paints nothing.
#
# How it is made (shader nodes only, written by Python; nothing is a picture):
#  1. COURSES. The picture is cut into equal courses (12 per tile). Every second course is slid by half a brick (running bond).
#  2. BRICK LENGTHS. Each upright mortar joint of a course is moved left or right of its even place by its own random amount (up to
#     plus or minus half of Length Spread x one brick), so bricks have different lengths. The random number belongs to the JOINT, so the
#     brick on its left and the brick on its right agree where it is, and joint number 4 is joint number 0 again (the tile repeats).
#     A dot finds its brick by checking the joint just left and just right of its even place, and one more on either side.
#  3. MORTAR. Head joints (between two bricks of a course) and bed joints (between two courses) have their own widths in tile units.
#  4. SHAPE. Each brick is a rectangle with rounded corners whose edges are dented by a seamless noise (a different noise for every brick).
#  5. BUNDLE. From the distances to the four edges come edge_distance, the two masks, local_x / local_y, and base_height (mortar low,
#     brick high, a rounded bevel along the edges, a tiny random lift per brick).
# Settings are named 'brick_layout.<name>' (for example 'brick_layout.head_joint'). Courses and bricks per course change the number of
# nodes, so they are read when the box is built; everything else is a socket in the Shader editor.
# Sizes are TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.008 = 10 dots).
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'brick_layout'
GROUP_NAME = 'BRICK LAYOUT'

CONTROLS = [
    Control('courses_per_tile', 'Courses Per Tile', 12, 1, 64, 'how many courses (rows of bricks) fit in one base tile; use an even number so the running bond repeats', build_time=True),
    Control('bricks_per_course', 'Bricks Per Course Per Tile', 4, 1, 32, 'how many bricks sit side by side in one course of one base tile', build_time=True),
    Control('seed', 'Seed', 1.0, 0.0, 1000.0, 'random seed of the layout: changes brick lengths and edge dents, nothing else'),
    Control('head_joint', 'Head Joint', 0.0163, 0.0, 0.05, 'width of the upright mortar joint between two bricks of a course, in tile units (0.0163 = 20.4 dots)'),
    Control('bed_joint', 'Bed Joint', 0.0148, 0.0, 0.05, 'height of the mortar band between two courses, in tile units (0.0148 = 18.6 dots)'),
    Control('length_spread', 'Length Spread', 0.3, 0.0, 0.9, 'how far each upright joint may move from its even place, as a share of one brick (0.3 = plus or minus 15 percent; 0 = all bricks equal)'),
    Control('course_offset', 'Course Offset', 0.5, 0.0, 1.0, 'how far every second course is slid sideways, as a share of one brick (0.5 = half a brick, the usual running bond)'),
    Control('corner_radius', 'Corner Radius', 0.007, 0.0, 0.03, 'rounding of the brick corners, in tile units (0.007 = 9 dots)'),
    Control('dent_depth', 'Dent Depth', 0.002, 0.0, 0.01, 'deepest dent pushed into a brick edge by the edge noise, in tile units (0.002 = 2.5 dots)'),
    Control('dent_scale', 'Dent Scale', 90.0, 4.0, 400.0, 'how many dents (noise features) fit across one base tile (90 = a dent about 14 dots long)'),
    Control('edge_softness', 'Edge Softness', 0.0004, 0.0, 0.005, 'width of the soft ramp of the masks at a brick edge, in tile units (0.0004 = half a dot)'),
    Control('mortar_level', 'Mortar Level', 0.08, 0.0, 1.0, 'base relief height in the mortar (0..1)'),
    Control('brick_level', 'Brick Level', 0.50, 0.0, 1.0, 'base relief height on the bricks (0..1)'),
    Control('bevel_width', 'Bevel Width', 0.003, 0.0001, 0.05, 'how wide the rounded slope from mortar up to the brick face is, in tile units'),
    Control('brick_level_jitter', 'Brick Level Jitter', 0.03, 0.0, 0.3, 'how much each brick face is higher or lower than the others (plus and minus this much)'),
]
OUTPUTS = [(name, 'float', li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]


def build_group(parameters):
    """Make the BRICK LAYOUT node group. Reads 'brick_layout.*' settings and 'recipe.tiles_across'."""
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    tiles = int(parameters.get('recipe.tiles_across', 1))
    courses_per_tile, bricks_per_tile = int(values['courses_per_tile']), int(values['bricks_per_course'])
    courses, bricks = courses_per_tile * tiles, bricks_per_tile * tiles          # in the whole picture
    pitch_x, pitch_y = 1.0 / bricks_per_tile, 1.0 / courses_per_tile              # one brick step and one course step, in tile units
    inputs = [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1 left to right, y = 0..1 BOTTOM to top of the picture')]
    for control in CONTROLS:
        if not control.build_time:
            inputs.append((control.label, control.kind, values[control.key], control.low, control.high, control.text))
    tree, b = li.make_plain_group(GROUP_NAME, inputs, OUTPUTS)
    S = b.input
    seed = S('Seed')

    # ---------------------------------------------------------------------------------------------- 1. COURSES
    u, v, _ = b.xyz(S('Vector'))
    y = b.mul(v, float(courses))                                     # course units, counted from the BOTTOM of the picture
    course = b.floor(y)
    up = b.frac(y)                                                   # 0 at the bottom of the course band, 1 at its top
    course_wrapped = b.mod(course, float(courses))
    slide = b.mul(b.mod(course_wrapped, 2.0), S('Course Offset'))
    x = b.sub(b.mul(u, float(bricks)), slide)                        # brick units along the course after the slide

    # ---------------------------------------------------------------------------------------------- 2. BRICK LENGTHS (joints moved at random)
    guess = b.floor(x)

    def joint(index):
        """Where upright joint number `index` of this course really is (its even place plus its own random move)."""
        wrapped = b.mod(index, float(bricks))
        roll = b.hash4(b.vec(wrapped, course_wrapped, seed), 0.37).outputs['Value']
        return b.add(index, b.mul(b.sub(roll, 0.5), S('Length Spread')))

    joint_left2, joint_left, joint_right, joint_right2 = joint(b.add(guess, -1.0)), joint(guess), joint(b.add(guess, 1.0)), joint(b.add(guess, 2.0))
    is_left = b.lt(x, joint_left)                                    # 1 if the dot really lies in the brick one step to the left
    is_right = b.gt(x, joint_right)                                  # 1 if it lies one step to the right
    brick_index = b.add(b.sub(guess, is_left), is_right)
    left_edge = b.math('MULTIPLY_ADD', is_left, b.sub(joint_left2, joint_left), b.math('MULTIPLY_ADD', is_right, b.sub(joint_right, joint_left), joint_left))
    right_edge = b.math('MULTIPLY_ADD', is_left, b.sub(joint_left, joint_right), b.math('MULTIPLY_ADD', is_right, b.sub(joint_right2, joint_right), joint_right))
    brick_wrapped = b.mod(brick_index, float(bricks))
    piece_id = b.hash4(b.vec(brick_wrapped, course_wrapped, b.add(seed, 0.7)), 0.3).outputs['Value']

    # ---------------------------------------------------------------------------------------------- 3. MORTAR and 4. SHAPE
    half_head, half_bed = b.mul(S('Head Joint'), 0.5), b.mul(S('Bed Joint'), 0.5)
    brick_length = b.mul(b.sub(right_edge, left_edge), pitch_x)      # tile units, joint included
    along = b.mul(b.sub(x, left_edge), pitch_x)                      # tile units from the brick's left joint line
    inside_left = b.sub(along, half_head)
    inside_right = b.sub(b.sub(brick_length, along), half_head)
    inside_top = b.sub(b.mul(b.sub(1.0, up), pitch_y), half_bed)
    inside_bottom = b.sub(b.mul(up, pitch_y), half_bed)
    dents = b.power(b.noise01(S('Vector'), b.mul(S('Dent Scale'), float(tiles)), 3.0, 0.5, b.math('MULTIPLY_ADD', piece_id, 500.0, b.mul(seed, 7.0))), 2.0)
    dent = b.mul(dents, S('Dent Depth'))
    inside_left, inside_right = b.sub(inside_left, dent), b.sub(inside_right, dent)
    inside_top, inside_bottom = b.sub(inside_top, dent), b.sub(inside_bottom, dent)
    radius = S('Corner Radius')
    side_nearest = b.mn(inside_left, inside_right)
    updown_nearest = b.mn(inside_top, inside_bottom)
    corner_x = b.mx(b.sub(radius, side_nearest), 0.0)
    corner_y = b.mx(b.sub(radius, updown_nearest), 0.0)
    corner_length = b.sqrt(b.add(b.mul(corner_x, corner_x), b.mul(corner_y, corner_y)))
    inside = b.sub(b.add(b.mn(side_nearest, updown_nearest), b.mx(corner_x, corner_y)), corner_length)   # + on the brick, - in the mortar

    # ---------------------------------------------------------------------------------------------- 5. THE BUNDLE
    piece_mask = b.math('MULTIPLY_ADD', inside, b.div(1.0, b.mx(S('Edge Softness'), 1e-6)), 0.5, clamp=True)
    edge_distance = b.mx(inside, 0.0)
    face_width = b.sub(brick_length, S('Head Joint'))
    face_height = b.sub(pitch_y, S('Bed Joint'))
    local_x = b.maprange(along, half_head, b.add(b.sub(brick_length, half_head), 1e-6), 0.0, 1.0, True)
    local_y = b.maprange(up, b.sub(1.0, b.mul(half_bed, float(courses_per_tile))), b.mul(half_bed, float(courses_per_tile)), 0.0, 1.0, True)   # 0 at the TOP
    profile = b.smoothstep(edge_distance, 0.0, b.mx(S('Bevel Width'), 1e-5))
    face_level = b.add(S('Brick Level'), b.mul(b.sub(b.mul(piece_id, 2.0), 1.0), S('Brick Level Jitter')))
    base_height = b.math('MULTIPLY_ADD', b.sub(face_level, S('Mortar Level')), profile, S('Mortar Level'))
    for name, socket in (('piece_id', piece_id), ('row', b.div(course_wrapped, float(courses))), ('local_x', local_x), ('local_y', local_y),
                         ('piece_width', face_width), ('piece_height', face_height), ('edge_distance', edge_distance),
                         ('top_edge_distance', b.mx(inside_top, 0.0)), ('gap_mask', b.sub(1.0, piece_mask)), ('piece_mask', piece_mask),
                         ('base_height', base_height)):
        b.output(name, socket)
    return tree
