# What this does: builds the Works' two factories at true size in Blender by script ("34 Plan - chapter 2
# full redesign", part 1 A, finding F4), each into its own .glb (for the film) and .blend (for drawing
# plates), in assets/models/inflation-chapter-2-newcomers/works/:
#   no-1-quiet-factory.glb / .blend      No. 1, always on the left of the lane
#   no-2-flat-out-factory.glb / .blend   No. 2, always on the right
# It replaces, for the redesign, the small old model of build_factory.py (a 3.2 m shed, one tapering square
# chimney and a tank on every factory, one merged glowing window, a blank sign board, a shading bake),
# which is left as it is, with the old models in assets/models/inflation-chapter-2/.
#
# The fixed looks (plan, part 1 A), so the two are told apart by shape first:
#   No. 1, the quiet factory: dark red-brown brick (castle_brick_02_red, darkened); ONE tall ROUND
#     chimney (26 m) at the back of its yard; a four-bay sawtooth roof whose teeth show along the mill
#     front's top; no water tank; a two-storey mill front with upper windows; a cart doorway behind the
#     gate, its doors shut.
#   No. 2, the flat-out factory: pale buff-grey brick (white_sandstone_bricks, toned); TWO SQUARE chimneys
#     (25 m and 23 m); a water tank on a steel trestle standing over its roof; long pitched shed roofs
#     (three spans, gables to the lane) with glazed roof lanterns along their ridges; a two-storey mill
#     front with upper windows; a cart doorway behind the gate with its doors open on a lit works, and a
#     taking-in door with a hoist beam above it.
# No sign boards, no lettering, no figures anywhere (the gate boards "No. 1" and "No. 2" are props from
# chapter 2's prop library). No shading bake: Blender draws the plates itself.
#
# Where things stand (metres; the Works' layout in works_kit.py: x across the lane, 0 on its centre line;
# y away from the lane, 0 at the works wall's face on the lane side; z up from the ground). The works
# wall, its gates and the dividing wall are not in these files; they are built with the lane.
#   mill fronts: 8 m behind the wall's face (y 8 to 30, 22 m deep); each mill 22 m wide, from 0.5 m
#     beside the lane's centre line outwards (No. 1 x -22.5 to -0.5; No. 2 x 0.5 to 22.5), so each mill
#     front stands behind its own gate and fills the view from that gate's pavement
#   two storeys: ground floor 4.2 m, eaves 7.8 m; No. 1's sawtooth peaks 10.2 m; No. 2's ridges 8.85 and
#     9.84 m, lanterns 10.9 m, tank top 14.8 m
#   chimneys 35 m behind the wall, in line with each gate's outer pier: No. 1's round one at x -5.3;
#     No. 2's square ones at x 5.3 and (3.5 m further back) x 8.6
#   the sawtooth's low ends and No. 2's span joints are placed so the gate views (eye 1.7 m, 13 m from
#     the wall, in line with the outer pier) look over the low part of the roof at their own chimney
#   each yard is paved with setts (top 2 cm above the ground) from the wall to 42 m back
#
# Windows: every pane of glass is its own piece (front, back and outer end walls, the sawtooth's north
# lights, the lanterns' glazing), in three named groups of a third each, <prefix>-windows-step-1, -2 and
# -3, spread over every wall and floor. Each piece wears <prefix>-<type>-lit or <prefix>-<type>-dark;
# works_kit.set_windows(prefix, {1, 2, 3}) lights them all, {1} a third, set() none. The loading
# doorway's inside is lit or dark on its own (works_kit.set_doorway). Each piece carries its factory,
# glass type and step as custom properties (glTF extras in the .glb). Saved as built: No. 1 all dark,
# doors shut; No. 2 all lit, doors open, doorway lit.
#
# Named parts the film can find: <prefix>-loading-door-left / -right (each turns about its hinge, its own
# centre), the markers no-1-chimney-top, no-2-chimney-a-top, no-2-chimney-b-top (where smoke starts),
# <prefix>-doorway-foot (on the ground 1 m in front of the doorway's middle), no-2-tank-top. One root each: no-1-quiet-factory,
# no-2-flat-out-factory.
#
# Run (paint_works_pictures.py first):
#   blender -b --python build_factories.py -- [--factory 1|2] [--out FOLDER] [--replace]
#       [--chimney-1 X,Y,HEIGHT] [--chimneys-2 X,Y,HEIGHT;X,Y,HEIGHT] [--wall-to-mill METRES]
# With no --factory it builds both. It stops rather than write over files that are there, unless
# --replace is given.

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import works_kit as kit  # noqa: E402

OUT_FOLDER = os.path.abspath(kit.option('--out', kit.WORKS_FOLDER))
REPLACE = kit.flag('--replace')
WHICH = [kit.option('--factory')] if kit.option('--factory') else ['1', '2']

WALL_TO_MILL = float(kit.option('--wall-to-mill', '8.0'))   # the works wall's face to the mill fronts
MILL_DEPTH = 22.0
MILL_WIDTH = 22.0
INNER_EDGE = 0.5                 # the mills' inner ends stand this far from the lane's centre line
WALL = 0.5                       # wall thickness
FIRST_FLOOR = 4.2
EAVES = 7.8
PLINTH = 0.6
GROUND_WINDOWS = (1.0, 3.4)      # sill and head heights
UPPER_WINDOWS = (5.0, 7.2)
GLASS_SET_BACK = 0.22            # how far the glass stands back from the wall's face
PILASTER = 0.6                   # pilaster width; they stand out 0.14 m
TOOTH = 2.4                      # No. 1's sawtooth: how far each tooth rises above the eaves
PITCH = math.radians(25)         # No. 2's roof pitch
YARD_DEPTH = 42.0
FRONT = WALL_TO_MILL
BACK = WALL_TO_MILL + MILL_DEPTH


def numbers(text):
    return [float(part) for part in text.split(',')]


CHIMNEY_1 = numbers(kit.option('--chimney-1', '-5.3,35,26'))
CHIMNEYS_2 = [numbers(part) for part in kit.option('--chimneys-2', '5.3,35,25;8.6,38.5,23').split(';')]


# ------------------------------------------------------------------------------------------ walls

class Wall:
    """One straight wall of a mill, described from outside. axis 'x': the wall runs along x with its face
    at y = plane; axis 'y': along y with its face at x = plane. out: which way its face looks along the
    other axis (-1 or +1). Points on it are given as (u, depth, z): u along the wall, depth into the wall
    from its face (negative: standing out in front of it), z up."""

    def __init__(self, name, axis, plane, out, u0, u1):
        self.name, self.axis, self.plane, self.out, self.u0, self.u1 = name, axis, plane, out, u0, u1

    def point(self, u, depth, z):
        across = self.plane - self.out * depth
        return Vector((u, across, z)) if self.axis == 'x' else Vector((across, u, z))

    def right(self):
        """The direction to a viewer's right as they face the wall from outside."""
        outward = Vector((0, self.out, 0)) if self.axis == 'x' else Vector((self.out, 0, 0))
        return (-outward).cross(Vector((0, 0, 1)))

    def box(self, builder, u0, u1, d0, d1, z0, z1, material):
        a, b = self.point(u0, d0, z0), self.point(u1, d1, z1)
        builder.box(tuple(map(min, a, b)), tuple(map(max, a, b)), material)

    def face_corners(self, u0, u1, depth, z0, z1):
        """Corners of a flat piece on the wall (glass), bottom left, bottom right, top right, top left
        as seen from outside."""
        left, right = (u0, u1) if self.right().dot(self.point(1, 0, 0) - self.point(0, 0, 0)) > 0 else (u1, u0)
        return [self.point(left, depth, z0), self.point(right, depth, z0), self.point(right, depth, z1), self.point(left, depth, z1)]


def wall_with_openings(builder, wall, z0, z1, openings, material, thickness=WALL):
    """The wall's brickwork from z0 to z1 with rectangular openings [(u0, u1, z0, z1)] left open: built of
    boxes round the openings, so each opening's sides (the reveals) are brick too."""
    us = sorted({wall.u0, wall.u1} | {o[0] for o in openings} | {o[1] for o in openings})
    zs = sorted({z0, z1} | {o[2] for o in openings if z0 < o[2] < z1} | {o[3] for o in openings if z0 < o[3] < z1})
    for za, zb in zip(zs, zs[1:]):
        run_start = None
        for ua, ub in zip(us, us[1:]):
            middle_u, middle_z = (ua + ub) / 2, (za + zb) / 2
            open_here = any(o[0] < middle_u < o[1] and o[2] < middle_z < o[3] for o in openings)
            if not open_here and run_start is None:
                run_start = ua
            if open_here and run_start is not None:
                wall.box(builder, run_start, ua, 0, thickness, za, zb, material)
                run_start = None
        if run_start is not None:
            wall.box(builder, run_start, us[-1], 0, thickness, za, zb, material)


def spread(clear_start, clear_end, count, width):
    """Centres of count openings of the given width spread evenly over a clear stretch of wall."""
    room = clear_end - clear_start
    return [clear_start + room * (k + 0.5) / count for k in range(count)]


# ---------------------------------------------------------------------------------------- factories

class Factory:
    """Everything one factory needs while it is built: its name, materials, groups and glass."""

    def __init__(self, number):
        self.number = number
        self.prefix = f'no-{number}'
        self.side = -1 if number == 1 else 1
        self.root = kit.empty('no-1-quiet-factory' if number == 1 else 'no-2-flat-out-factory', size=2.0, collection_name='roots')
        self.groups = {}
        self.glass_rows = {}            # (wall, row) -> list of glass pieces, for spreading the steps
        if number == 1:
            self.brick = kit.surface_material('no-1-brick', 'castle_brick_02_red', tint=(0.42, 0.27, 0.22))
            self.stone = kit.surface_material('no-1-stone', 'large_sandstone_blocks', tint=(0.74, 0.7, 0.62), tile_metres=1.5)
            self.chimney_bricks = [self.brick,
                                   kit.surface_material('no-1-brick-sooted', 'castle_brick_02_red', tint=(0.3, 0.2, 0.17)),
                                   kit.surface_material('no-1-brick-black', 'castle_brick_02_red', tint=(0.13, 0.1, 0.09))]
            self.window_type = 'mill-window-narrow'
            self.roof_glass_type = 'north-light'
            self.door_paint = kit.surface_material('no-1-door-timber', 'distressed_painted_planks', tint=(0.3, 0.21, 0.15), roughness=0.7)
        else:
            self.brick = kit.surface_material('no-2-brick', 'white_sandstone_bricks', tint=(0.92, 0.86, 0.74))
            self.stone = kit.surface_material('no-2-stone', 'large_sandstone_blocks', tint=(0.6, 0.58, 0.54), tile_metres=1.5)
            self.chimney_bricks = [self.brick,
                                   kit.surface_material('no-2-brick-sooted', 'white_sandstone_bricks', tint=(0.5, 0.46, 0.4)),
                                   kit.surface_material('no-2-brick-black', 'white_sandstone_bricks', tint=(0.16, 0.15, 0.14))]
            self.window_type = 'mill-window-wide'
            self.roof_glass_type = 'lantern-light'
            self.door_paint = kit.surface_material('no-2-door-timber', 'distressed_painted_planks', tint=(0.27, 0.22, 0.17), roughness=0.7)
            self.tank_steel = kit.surface_material('no-2-tank-steel', 'rusty_metal_02', tint=(0.16, 0.17, 0.18), roughness=0.6, metallic=0.5)
        self.slate = kit.surface_material(f'{self.prefix}-slate', 'roof_slates_03', tint=(0.4, 0.43, 0.5), roughness=0.5, normal_strength=1.2)
        self.iron = kit.surface_material(f'{self.prefix}-iron', 'rusty_metal_02', tint=(0.14, 0.14, 0.14), roughness=0.55, metallic=0.6)
        self.flashing = kit.surface_material(f'{self.prefix}-lead', 'grey_plaster_02', tint=(0.16, 0.17, 0.18), roughness=0.5)
        self.setts = kit.surface_material(f'{self.prefix}-setts', 'square_cobblestone', tint=(0.48, 0.48, 0.5), roughness=0.75, normal_strength=1.4)
        self.inside_dark = kit.surface_material(f'{self.prefix}-inside', 'grey_plaster_02', tint=(0.06, 0.05, 0.045), roughness=1.0)
        self.cap_stone = kit.surface_material(f'{self.prefix}-chimney-cap', 'large_sandstone_blocks', tint=(0.2, 0.19, 0.18), tile_metres=1.5)
        self.default_state = 'dark' if number == 1 else 'lit'

    def group(self, name, parent=None):
        """A named group (an empty) under the root, or under another group."""
        full = f'{self.prefix}-{name}'
        if full not in self.groups:
            self.groups[full] = kit.empty(full, parent=parent or self.root, size=1.0)
        return self.groups[full]

    def glass(self, name, corners, glass_type, row_key):
        """A pane of glass for this factory, in its built state; its step (1, 2 or 3) and which of the
        four windows in its picture it wears are given later, spread over its row (spread_steps)."""
        piece = kit.glass_piece(f'{self.prefix}-{name}', corners, self.prefix, glass_type, self.default_state,
                                variant=0, step=1, parent=self.root)
        self.glass_rows.setdefault(row_key, []).append(piece)
        return piece

    def spread_steps(self):
        """Give every pane a step (1, 2 or 3) so each third is spread over every wall and floor, and one
        of the four windows in its picture, so neighbours differ."""
        chooser = random.Random(self.number * 101)
        for row_key in sorted(self.glass_rows):
            pieces = self.glass_rows[row_key]
            order = list(range(len(pieces)))
            chooser.shuffle(order)
            start = chooser.randrange(3)
            for rank, index in enumerate(order):
                piece = pieces[index]
                step = 1 + (rank + start) % 3
                piece['window_step'] = step
                piece.parent = self.group(f'windows-step-{step}', self.group('windows'))
                variant = (index * 3 + chooser.randrange(4)) % 4
                for loop in piece.data.uv_layers[0].data:
                    loop.uv = (0.25 * variant + (0.25 if loop.uv[0] > 0.125 else 0.0), loop.uv[1])


# --------------------------------------------------------------------------------------- the mill

def window_openings(wall, centres, width, floors, skip=()):
    """Openings for windows: [(u0, u1, sill, head)] at each centre on each floor, leaving out the
    (centre index, floor index) pairs in skip."""
    found = []
    for floor_index, (sill, head) in enumerate(floors):
        for index, centre in enumerate(centres):
            if (index, floor_index) not in skip:
                found.append((centre - width / 2, centre + width / 2, sill, head))
    return found


def dress_wall(factory, wall, walls, dressings, iron, pilasters, openings, glass_type, eaves=True, doorways=()):
    """Everything on one wall's face: pilasters, the plinth (broken at doorways), a string course at the
    first floor, a band under the eaves, stone sills and lintels at every window, and the glass."""
    for centre in pilasters:
        u0, u1 = max(wall.u0, centre - PILASTER / 2), min(wall.u1, centre + PILASTER / 2)
        if centre <= wall.u0 + 0.01:
            u0, u1 = wall.u0, wall.u0 + PILASTER
        if centre >= wall.u1 - 0.01:
            u0, u1 = wall.u1 - PILASTER, wall.u1
        wall.box(walls, u0, u1, -0.14, 0.02, PLINTH, EAVES - 0.3, factory.brick)
    cuts = sorted(doorways)
    start = wall.u0 - 0.2
    for door_u0, door_u1 in cuts + [(wall.u1 + 0.2, wall.u1 + 0.2)]:
        if door_u0 > start:
            wall.box(dressings, start, door_u0, -0.2, 0.05, 0.0, PLINTH, factory.stone)
        start = door_u1
    wall.box(dressings, wall.u0 - 0.05, wall.u1 + 0.05, -0.07, 0.02, FIRST_FLOOR, FIRST_FLOOR + 0.25, factory.stone)
    if eaves:
        wall.box(dressings, wall.u0 - 0.2, wall.u1 + 0.2, -0.2, 0.02, EAVES - 0.35, EAVES, factory.stone)
    for u0, u1, sill, head in openings:
        wall.box(dressings, u0 - 0.1, u1 + 0.1, -0.08, GLASS_SET_BACK, sill - 0.14, sill + 0.02, factory.stone)
        wall.box(dressings, u0 - 0.15, u1 + 0.15, -0.03, 0.03, head, head + 0.32, factory.stone)
        row = 'ground' if sill < FIRST_FLOOR else 'upper'
        number = len(factory.glass_rows.get((wall.name, row), [])) + 1
        factory.glass(f'window-{wall.name}-{row}-{number:02d}', wall.face_corners(u0, u1, GLASS_SET_BACK, sill + 0.02, head),
                      glass_type, (wall.name, row))


def doorway(factory, wall, walls, dressings, centre, width, height, open_doors):
    """A cart doorway: an opening with a stone lintel and kerbs, a dark room behind it with the lit (or
    dark) inside of the works on its back wall, and two plank door leaves, each turning about its hinge."""
    u0, u1 = centre - width / 2, centre + width / 2
    wall.box(dressings, u0 - 0.25, u1 + 0.25, -0.05, 0.05, height, height + 0.4, factory.stone)
    for u in (u0 - 0.12, u1 + 0.12):        # guard stones at the jambs' feet, against cart wheels
        wall.box(dressings, u - 0.12, u + 0.12, -0.25, 0.0, 0.0, 0.7, factory.stone)
    room = kit.MeshBuilder()
    depth = 3.0
    wall.box(room, u0 - 0.3, u1 + 0.3, WALL, depth, -0.02, 0.0, factory.inside_dark)                  # floor
    wall.box(room, u0 - 0.3, u1 + 0.3, WALL, depth, height + 0.6, height + 0.7, factory.inside_dark)  # ceiling
    for u in (u0 - 0.4, u1 + 0.3):
        wall.box(room, u, u + 0.1, WALL, depth, 0.0, height + 0.6, factory.inside_dark)               # sides
    doorway_group = factory.group('doorway')
    room.finish(f'{factory.prefix}-doorway-room', parent=doorway_group)
    inside = kit.glass_piece(f'{factory.prefix}-doorway-inside', wall.face_corners(u0 - 0.3, u1 + 0.3, depth - 0.05, 0.0, height + 0.6),
                             factory.prefix, 'doorway-inside', 'lit' if open_doors else 'dark', variant=0, step=0, parent=doorway_group)
    inside['window_step'] = 0
    # the two leaves: vertical planks with ledges and braces behind and strap hinges in front
    leaf_width, leaf_height, thickness = width / 2 - 0.01, height - 0.05, 0.08
    for side, hinge_u in (('left', u0), ('right', u1)):
        toward = 1 if hinge_u == u0 else -1
        leaf = kit.MeshBuilder()
        planks = 7
        plank = (leaf_width - 0.01 * (planks - 1)) / planks
        for k in range(planks):
            a = hinge_u + toward * (k * (plank + 0.01))
            wall.box(leaf, min(a, a + toward * plank), max(a, a + toward * plank), 0.04, 0.04 + thickness, 0.03, leaf_height, factory.door_paint)
        for z in (0.4, leaf_height / 2, leaf_height - 0.4):
            wall.box(leaf, min(hinge_u, hinge_u + toward * leaf_width), max(hinge_u, hinge_u + toward * leaf_width),
                     0.04 + thickness, 0.04 + thickness + 0.05, z - 0.11, z + 0.11, factory.door_paint)
        for z in (0.55, leaf_height - 0.55):
            wall.box(leaf, min(hinge_u, hinge_u + toward * leaf_width * 0.75), max(hinge_u, hinge_u + toward * leaf_width * 0.75),
                     0.02, 0.04, z - 0.04, z + 0.04, factory.iron)
        hinge = wall.point(hinge_u, 0.04, 0.0)
        part = leaf.finish(f'{factory.prefix}-loading-door-{side}', parent=doorway_group, origin=hinge)
        if open_doors:
            # swung outwards (towards the lane) about 100 degrees, standing out from the wall like open
            # gates; doorways are only on the fronts, which face minus y
            part.rotation_euler.z = math.radians(-100 * toward)
    kit.empty(f'{factory.prefix}-doorway-foot', wall.point(centre, -1.0, 0.0), parent=factory.root)


def gable_coping(builder, factory, x_low, z_low, x_high, z_high, y0, y1):
    """A stone coping along a gable's sloping edge from (x_low, z_low) up to (x_high, z_high), standing a
    little proud of both faces of the wall."""
    run = Vector((x_high - x_low, z_high - z_low)).normalized()
    lift = Vector((-run.y, run.x)) * 0.18
    if lift.y < 0:
        lift = -lift                     # always above the sloping edge
    a, b = Vector((x_low, z_low)) - run * 0.15, Vector((x_high, z_high))
    outline = [tuple(a), tuple(b), tuple(b + lift), tuple(a + lift)]
    builder.prism(outline, y0 - 0.08, y1 + 0.08, factory.stone, axis='y')


def build_sawtooth_mill(factory):
    """No. 1's mill: a two-storey mill front with upper windows under a four-bay sawtooth roof whose
    teeth rise towards the lane's centre line, each with a glazed north light on its upright face."""
    mill = factory.group('mill')
    walls, dressings, roof, ironwork = kit.MeshBuilder(), kit.MeshBuilder(), kit.MeshBuilder(), kit.MeshBuilder()
    outer, inner = -INNER_EDGE - MILL_WIDTH, -INNER_EDGE
    bay = MILL_WIDTH / 4
    bay_lines = [outer + bay * k for k in range(5)]
    floors = (GROUND_WINDOWS, UPPER_WINDOWS)
    front = Wall('front', 'x', FRONT, -1, outer, inner)
    back = Wall('back', 'x', BACK, 1, outer, inner)
    outer_end = Wall('outer-end', 'y', outer, -1, FRONT + WALL, BACK - WALL)
    inner_end = Wall('inner-end', 'y', inner, 1, FRONT + WALL, BACK - WALL)
    width = 1.3
    centres = []
    for a, b in zip(bay_lines, bay_lines[1:]):
        centres += spread(a + PILASTER / 2, b - PILASTER / 2, 2, width)
    door_centre, door_width, door_height = -3.4, 3.0, 3.8
    for wall in (front, back):
        skip = {(len(centres) - 2, 0), (len(centres) - 1, 0)} if wall is front else set()
        openings = window_openings(wall, centres, width, floors, skip)
        doors = [(door_centre - door_width / 2, door_centre + door_width / 2, 0.0, door_height)] if wall is front else []
        wall_with_openings(walls, wall, 0.0, EAVES, openings + doors, factory.brick)
        dress_wall(factory, wall, walls, dressings, ironwork, bay_lines, openings, factory.window_type,
                   doorways=[(d[0], d[1]) for d in doors])
        if wall is front:
            doorway(factory, wall, walls, dressings, door_centre, door_width, door_height, open_doors=False)
    side_lines = [FRONT + bay * k for k in range(5)]
    side_centres = []
    for a, b in zip(side_lines, side_lines[1:]):
        side_centres += spread(a + PILASTER / 2, b - PILASTER / 2, 2, width)
    openings = window_openings(outer_end, side_centres, width, floors)
    wall_with_openings(walls, outer_end, 0.0, EAVES, openings, factory.brick)
    dress_wall(factory, outer_end, walls, dressings, ironwork, side_lines, openings, factory.window_type)
    wall_with_openings(walls, inner_end, 0.0, EAVES, [], factory.brick)          # the blank party end
    inner_end.box(dressings, inner_end.u0, inner_end.u1, -0.05, 0.02, EAVES - 0.35, EAVES, factory.stone)
    # the teeth: a gable triangle on the front and back walls for each bay, a slate slope rising towards
    # the centre line, and the north light glazing on each tooth's upright face (facing the centre line)
    for index, (low, high) in enumerate(zip(bay_lines, bay_lines[1:])):
        for y0, y1 in ((FRONT, FRONT + WALL), (BACK - WALL, BACK)):
            walls.prism([(low, EAVES), (high, EAVES), (high, EAVES + TOOTH)], y0, y1, factory.brick, axis='y')
            gable_coping(dressings, factory, low, EAVES, high - 0.02, EAVES + TOOTH, y0, y1)
            dressings.box((high - 0.45, y0 - 0.1, EAVES + TOOTH - 0.05), (high + 0.05, y1 + 0.1, EAVES + TOOTH + 0.3), factory.stone)  # apex block
            dressings.box((low - 0.3, y0 - 0.1, EAVES - 0.25), (low + 0.4, y1 + 0.1, EAVES + 0.25), factory.stone)                    # kneeler
        y_from, y_to = FRONT + WALL - 0.02, BACK - WALL + 0.02
        roof.roof_slope((low + 0.25, y_from, EAVES + 0.12), (low + 0.25, y_to, EAVES + 0.12),
                        (high - 0.12, y_to, EAVES + TOOTH - 0.02), (high - 0.12, y_from, EAVES + TOOTH - 0.02), factory.slate)
        ironwork.box((low - 0.3, y_from, EAVES - 0.05), (low + 0.3, y_to, EAVES + 0.16), factory.iron)                 # valley (eaves) gutter
        roof.box((high - 0.2, y_from, EAVES + TOOTH - 0.1), (high + 0.04, y_to, EAVES + TOOTH + 0.08), factory.flashing)   # ridge flashing
        roof.box((high - 0.14, y_from, EAVES - 0.02), (high + 0.02, y_to, EAVES + 0.28), factory.flashing)           # upstand under the glass
        panels = 7
        panel = (y_to - y_from) / panels
        for k in range(panels):
            a, b = y_from + k * panel + 0.06, y_from + (k + 1) * panel - 0.06
            corners = [Vector((high, a, EAVES + 0.3)), Vector((high, b, EAVES + 0.3)), Vector((high, b, EAVES + TOOTH - 0.14)), Vector((high, a, EAVES + TOOTH - 0.14))]
            factory.glass(f'north-light-{index + 1}-panel-{k + 1}', corners, factory.roof_glass_type, ('north-light', index))
            ironwork.box((high - 0.03, b - 0.0, EAVES + 0.28), (high + 0.06, b + 0.12, EAVES + TOOTH - 0.1), factory.iron)  # mullion
        ironwork.box((high - 0.03, y_from, EAVES + TOOTH - 0.16), (high + 0.06, y_to, EAVES + TOOTH - 0.08), factory.iron)  # head rail
        # downpipes from the valley gutters, down the front and back
        if index > 0:
            for wall, depth in ((front, -0.12), (back, -0.12)):
                top = wall.point(low + 0.5, depth, EAVES - 0.4)
                ironwork.rod(wall.point(low + 0.5, depth, 0.15), top, 0.06, factory.iron)
                ironwork.centred_box(tuple(top + Vector((0, 0, 0.18))), (0.3, 0.3, 0.32), factory.iron)                  # hopper head
    for y in (FRONT + 1.2, BACK - 1.2):      # downpipes from the eaves gutter on the outer end wall
        ironwork.rod(outer_end.point(y, -0.12, 0.15), outer_end.point(y, -0.12, EAVES), 0.06, factory.iron)
    for builder, name in ((walls, 'walls'), (dressings, 'stonework'), (roof, 'roof'), (ironwork, 'ironwork')):
        builder.finish(f'{factory.prefix}-mill-{name}', parent=mill)


def build_pitched_mill(factory):
    """No. 2's mill: a two-storey mill front with upper windows under three long pitched spans (gables
    to the lane) with glazed lanterns along their ridges; a taking-in door with a hoist beam in the
    narrow first span; the steel trestle and water tank standing over the second span."""
    mill = factory.group('mill')
    walls, dressings, roof, ironwork, timber = (kit.MeshBuilder() for _ in range(5))
    inner, outer = INNER_EDGE, INNER_EDGE + MILL_WIDTH
    spans = [(inner, 5.0), (5.0, 13.75), (13.75, outer)]
    span_lines = [inner, 5.0, 13.75, outer]
    floors = (GROUND_WINDOWS, UPPER_WINDOWS)
    front = Wall('front', 'x', FRONT, -1, inner, outer)
    back = Wall('back', 'x', BACK, 1, inner, outer)
    outer_end = Wall('outer-end', 'y', outer, 1, FRONT + WALL, BACK - WALL)
    inner_end = Wall('inner-end', 'y', inner, -1, FRONT + WALL, BACK - WALL)
    width = 1.7
    door_centre, door_width, door_height = 2.9, 2.8, 3.8
    loft_door = (2.2, 3.6, FIRST_FLOOR + 0.25, EAVES - 0.8)
    for wall in (front, back):
        openings, centres = [], []
        for index, (a, b) in enumerate(spans):
            count = 1 if index == 0 else 3
            these = spread(a + PILASTER / 2 + 0.05, b - PILASTER / 2 - 0.05, count, width)
            if wall is front and index == 0:
                continue                     # the doorway and the taking-in door instead
            centres += these
        openings = window_openings(wall, centres, width, floors)
        extra = [(door_centre - door_width / 2, door_centre + door_width / 2, 0.0, door_height), loft_door] if wall is front else []
        wall_with_openings(walls, wall, 0.0, EAVES, openings + extra, factory.brick)
        dress_wall(factory, wall, walls, dressings, ironwork, span_lines, openings, factory.window_type,
                   doorways=[(door_centre - door_width / 2, door_centre + door_width / 2)] if wall is front else [])
        if wall is front:
            doorway(factory, wall, walls, dressings, door_centre, door_width, door_height, open_doors=True)
            # the taking-in door: two plank leaves, shut, a stone sill, a hoist beam from the gable's apex
            u0, u1, z0, z1 = loft_door
            wall.box(dressings, u0 - 0.1, u1 + 0.1, -0.1, 0.3, z0 - 0.12, z0 + 0.02, factory.stone)
            wall.box(dressings, u0 - 0.15, u1 + 0.15, -0.03, 0.03, z1, z1 + 0.3, factory.stone)
            for k in range(6):
                a = u0 + k * (u1 - u0) / 6
                wall.box(timber, a + 0.005, a + (u1 - u0) / 6 - 0.005, 0.12, 0.2, z0 + 0.02, z1, factory.door_paint)
            for z in (z0 + 0.4, z1 - 0.4):
                wall.box(ironwork, u0 + 0.1, u0 + 0.6, 0.1, 0.12, z - 0.04, z + 0.04, factory.iron)
                wall.box(ironwork, u1 - 0.6, u1 - 0.1, 0.1, 0.12, z - 0.04, z + 0.04, factory.iron)
            apex = EAVES + (5.0 - inner) / 2 * math.tan(PITCH)
            beam_u = (inner + 5.0) / 2
            wall.box(timber, beam_u - 0.14, beam_u + 0.14, -1.4, 0.4, apex - 0.75, apex - 0.47, factory.door_paint)
            ironwork.centred_box(tuple(wall.point(beam_u, -1.25, apex - 0.9)), (0.12, 0.2, 0.3), factory.iron)          # pulley block
            ironwork.rod(wall.point(beam_u, -1.25, apex - 1.05), wall.point(beam_u, -1.25, apex - 2.6), 0.025, factory.iron)  # chain
            ironwork.centred_box(tuple(wall.point(beam_u, -1.25, apex - 2.7)), (0.08, 0.06, 0.18), factory.iron)         # hook
    side_lines = [FRONT + MILL_DEPTH / 4 * k for k in range(5)]
    side_centres = []
    for a, b in zip(side_lines, side_lines[1:]):
        side_centres += spread(a + PILASTER / 2, b - PILASTER / 2, 2, width)
    openings = window_openings(outer_end, side_centres, width, floors)
    wall_with_openings(walls, outer_end, 0.0, EAVES, openings, factory.brick)
    dress_wall(factory, outer_end, walls, dressings, ironwork, side_lines, openings, factory.window_type)
    wall_with_openings(walls, inner_end, 0.0, EAVES, [], factory.brick)
    inner_end.box(dressings, inner_end.u0, inner_end.u1, -0.2, 0.02, EAVES - 0.35, EAVES, factory.stone)
    # the spans: gables with copings on the front and back walls, two slate slopes, a ridge roll,
    # gutters in the valleys and along the two eaves, downpipes; a lantern along each ridge
    tan = math.tan(PITCH)
    y_from, y_to = FRONT + WALL - 0.02, BACK - WALL + 0.02
    for index, (a, b) in enumerate(spans):
        middle, half = (a + b) / 2, (b - a) / 2
        ridge = EAVES + half * tan
        for y0, y1 in ((FRONT, FRONT + WALL), (BACK - WALL, BACK)):
            walls.prism([(a, EAVES), (b, EAVES), (middle, ridge)], y0, y1, factory.brick, axis='y')
            gable_coping(dressings, factory, a, EAVES, middle + 0.01, ridge, y0, y1)
            gable_coping(dressings, factory, b, EAVES, middle - 0.01, ridge, y0, y1)
            dressings.box((middle - 0.3, y0 - 0.1, ridge - 0.05), (middle + 0.3, y1 + 0.1, ridge + 0.35), factory.stone)   # apex
            for x in (a, b):
                dressings.box((x - 0.35, y0 - 0.1, EAVES - 0.25), (x + 0.35, y1 + 0.1, EAVES + 0.22), factory.stone)       # kneelers
        roof.roof_slope((a + 0.25 if a != inner else a - 0.35, y_from, EAVES + 0.12 + (0.25 if a != inner else -0.35) * tan),
                        (a + 0.25 if a != inner else a - 0.35, y_to, EAVES + 0.12 + (0.25 if a != inner else -0.35) * tan),
                        (middle, y_to, ridge + 0.12), (middle, y_from, ridge + 0.12), factory.slate)
        roof.roof_slope((b - 0.25 if b != outer else b + 0.35, y_to, EAVES + 0.12 + (0.25 if b != outer else -0.35) * tan),
                        (b - 0.25 if b != outer else b + 0.35, y_from, EAVES + 0.12 + (0.25 if b != outer else -0.35) * tan),
                        (middle, y_from, ridge + 0.12), (middle, y_to, ridge + 0.12), factory.slate)
        roof.rod((middle, y_from, ridge + 0.14), (middle, y_to, ridge + 0.14), 0.11, factory.flashing, sides=10)       # ridge roll
        # the lantern: a raised glazed louvre along the ridge with its own little roof
        lantern_width = 1.4 if index == 0 else 2.4
        lantern_height = 0.7 if index == 0 else 1.0
        start, end = (FRONT + 2.5, BACK - 2.5) if index != 1 else (FRONT + 6.0, BACK - 2.0)
        side_low = ridge - lantern_width / 2 * tan
        top = ridge + lantern_height
        for x in (middle - lantern_width / 2, middle + lantern_width / 2):
            timber.box((x - 0.06, start, side_low), (x + 0.06, end, ridge + 0.05), factory.door_paint)                   # cheek boarding
            ironwork.box((x - 0.07, start, top - 0.1), (x + 0.07, end, top), factory.iron)                                # head rail
        for y in (start, end):
            timber.prism([(middle - lantern_width / 2, side_low), (middle + lantern_width / 2, side_low),
                          (middle + lantern_width / 2, top), (middle, top + lantern_width / 2 * tan + 0.1), (middle - lantern_width / 2, top)],
                         y - 0.06, y + 0.06, factory.door_paint, axis='y')
        cover = lantern_width / 2 + 0.25
        roof.roof_slope((middle - cover, start - 0.2, top - 0.25 * tan), (middle - cover, end + 0.2, top - 0.25 * tan),
                        (middle, end + 0.2, top + lantern_width / 2 * tan + 0.06), (middle, start - 0.2, top + lantern_width / 2 * tan + 0.06), factory.slate, thickness=0.08)
        roof.roof_slope((middle + cover, end + 0.2, top - 0.25 * tan), (middle + cover, start - 0.2, top - 0.25 * tan),
                        (middle, start - 0.2, top + lantern_width / 2 * tan + 0.06), (middle, end + 0.2, top + lantern_width / 2 * tan + 0.06), factory.slate, thickness=0.08)
        panels = max(2, round((end - start) / 2.6))
        panel = (end - start) / panels
        for k in range(panels):
            y_a, y_b = start + k * panel + 0.05, start + (k + 1) * panel - 0.05
            for facing, x in ((-1, middle - lantern_width / 2 - 0.07), (1, middle + lantern_width / 2 + 0.07)):
                ends = (y_b, y_a) if facing < 0 else (y_a, y_b)
                corners = [Vector((x, ends[0], ridge + 0.08)), Vector((x, ends[1], ridge + 0.08)), Vector((x, ends[1], top - 0.12)), Vector((x, ends[0], top - 0.12))]
                factory.glass(f'lantern-{index + 1}-{"left" if facing < 0 else "right"}-panel-{k + 1}', corners, factory.roof_glass_type, ('lantern', index, facing))
                ironwork.box((x - 0.05, y_b, ridge + 0.05), (x + 0.05, y_b + 0.1, top - 0.08), factory.iron)
    for x in (5.0, 13.75):                                       # valley gutters and their downpipes
        ironwork.box((x - 0.3, y_from, EAVES - 0.05), (x + 0.3, y_to, EAVES + 0.16), factory.iron)
        for wall in (front, back):
            top = wall.point(x + 0.55, -0.12, EAVES - 0.4)
            ironwork.rod(wall.point(x + 0.55, -0.12, 0.15), top, 0.06, factory.iron)
            ironwork.centred_box(tuple(top + Vector((0, 0, 0.18))), (0.3, 0.3, 0.32), factory.iron)
    for x, out in ((inner, -1), (outer, 1)):                     # eaves gutters along both side walls
        gutter_x = x + out * 0.42
        ironwork.rod((gutter_x, FRONT - 0.2, EAVES - 0.02), (gutter_x, BACK + 0.2, EAVES - 0.02), 0.13, factory.iron, sides=10)
        for y in (FRONT + 0.9, BACK - 0.9):
            ironwork.rod((x + out * 0.14, y, 0.15), (x + out * 0.14, y, EAVES - 0.1), 0.06, factory.iron)
    for builder, name in ((walls, 'walls'), (dressings, 'stonework'), (roof, 'roof'), (ironwork, 'ironwork'), (timber, 'timber')):
        builder.finish(f'{factory.prefix}-mill-{name}', parent=mill)
    build_tank(factory, spans[1])


def build_tank(factory, span):
    """No. 2's water tank: a pressed-steel sectional tank (panels bolted through flanges that stand out in
    a grid) on a steel trestle whose four legs rise out of the roof of the second span, braced crosswise,
    with a ladder, a hand rail round the top and an outlet pipe down into the roof."""
    group = factory.group('tank')
    trestle, tank = kit.MeshBuilder(), kit.MeshBuilder()
    x0, x1 = 6.9, 9.9
    y0, y1 = FRONT + 1.6, FRONT + 4.6
    bottom, height = 12.0, 2.8
    tan = math.tan(PITCH)
    middle, half = (span[0] + span[1]) / 2, (span[1] - span[0]) / 2
    roof_at = lambda x: EAVES + (half - abs(x - middle)) * tan
    legs = [(x0 + 0.2, y0 + 0.2), (x1 - 0.2, y0 + 0.2), (x1 - 0.2, y1 - 0.2), (x0 + 0.2, y1 - 0.2)]
    for x, y in legs:
        trestle.box((x - 0.13, y - 0.13, roof_at(x) - 0.3), (x + 0.13, y + 0.13, bottom - 0.4), factory.iron)
        trestle.box((x - 0.25, y - 0.25, roof_at(x) - 0.05), (x + 0.25, y + 0.25, roof_at(x) + 0.12), factory.iron)   # base plate
    for y in (y0 + 0.2, y1 - 0.2):                               # bearers under the tank, and joists across
        trestle.box((x0 - 0.1, y - 0.15, bottom - 0.4), (x1 + 0.1, y + 0.15, bottom - 0.05), factory.iron)
    for x in (x0 + 0.9, x0 + 1.5, x1 - 0.9):
        trestle.box((x - 0.08, y0, bottom - 0.2), (x + 0.08, y1, bottom - 0.02), factory.iron)
    for (xa, ya), (xb, yb) in zip(legs, legs[1:] + legs[:1]):    # bracing on each face: a tie and a cross
        za, zb = roof_at(xa) + 0.3, roof_at(xb) + 0.3
        middle_z = (max(za, zb) + bottom - 0.4) / 2
        trestle.beam((xa, ya, middle_z), (xb, yb, middle_z), 0.1, 0.14, factory.iron)
        trestle.beam((xa, ya, za), (xb, yb, bottom - 0.45), 0.03, 0.12, factory.iron)
        trestle.beam((xb, yb, zb), (xa, ya, bottom - 0.45), 0.03, 0.12, factory.iron)
    tank.box((x0, y0, bottom), (x1, y1, bottom + height), factory.tank_steel)
    flange = 0.05
    for k in range(5):                                            # flanges: upright, then across, on every side
        x = x0 + (x1 - x0) * k / 4
        y = y0 + (y1 - y0) * k / 4
        for yy in (y0, y1):
            tank.box((x - 0.03, yy - flange if yy == y0 else yy, bottom), (x + 0.03, yy if yy == y0 else yy + flange, bottom + height), factory.tank_steel)
        for xx in (x0, x1):
            tank.box((xx - flange if xx == x0 else xx, y - 0.03, bottom), (xx if xx == x0 else xx + flange, y + 0.03, bottom + height), factory.tank_steel)
    for k in range(1, 4):
        z = bottom + height * k / 4
        tank.box((x0 - flange, y0 - flange, z - 0.03), (x1 + flange, y1 + flange, z + 0.03), factory.tank_steel)
    tank.box((x0 - 0.08, y0 - 0.08, bottom + height - 0.02), (x1 + 0.08, y1 + 0.08, bottom + height + 0.06), factory.tank_steel)   # lid
    tank.box((x0 + 0.6, y0 + 0.6, bottom + height + 0.06), (x0 + 1.3, y0 + 1.3, bottom + height + 0.22), factory.tank_steel)        # hatch
    rail_top = bottom + height + 1.0
    posts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)]
    for x, y in posts:
        trestle.rod((x, y, bottom + height), (x, y, rail_top), 0.025, factory.iron, sides=6)
    for (xa, ya), (xb, yb) in zip(posts[:4], posts[1:4] + posts[:1]):
        trestle.rod((xa, ya, rail_top), (xb, yb, rail_top), 0.025, factory.iron, sides=6)
    ladder_x = x0 - 0.35                                          # a ladder up the trestle's side
    for y in (y0 + 1.1, y0 + 1.6):
        trestle.rod((ladder_x, y, roof_at(x0) + 0.2), (ladder_x, y, rail_top), 0.025, factory.iron, sides=6)
    rung = roof_at(x0) + 0.5
    while rung < rail_top - 0.1:
        trestle.rod((ladder_x, y0 + 1.1, rung), (ladder_x, y0 + 1.6, rung), 0.018, factory.iron, sides=6)
        rung += 0.3
    trestle.rod((x0 + 0.6, y1 - 0.6, roof_at(x0 + 0.6) - 0.2), (x0 + 0.6, y1 - 0.6, bottom), 0.1, factory.iron, sides=10)  # outlet pipe
    trestle.finish('no-2-tank-trestle', parent=group)
    tank.finish('no-2-water-tank', parent=group)
    kit.empty('no-2-tank-top', ((x0 + x1) / 2, (y0 + y1) / 2, bottom + height), parent=factory.root)


# ------------------------------------------------------------------------------------- chimneys

def soot_segments(z0, z1):
    """Where a chimney's brick turns sooted and then black towards its top: [(from, to, shade)]."""
    span = z1 - z0
    return [(z0, z0 + span * 0.62, 0), (z0 + span * 0.62, z0 + span * 0.82, 1), (z0 + span * 0.82, z1, 2)]


def build_round_chimney(factory, x, y, height, name):
    """A tall round brick chimney: a square stone-capped plinth, a tapering round shaft with iron bands,
    darkening with soot towards a corbelled cap and a stone coping round its dark flue, and a lightning
    conductor up its side."""
    builder = kit.MeshBuilder()
    plinth_half, plinth_top = 1.8, 4.0
    builder.box((x - 1.9, y - 1.9, 0.0), (x + 1.9, y + 1.9, 0.6), factory.stone)
    builder.box((x - plinth_half, y - plinth_half, 0.6), (x + plinth_half, y + plinth_half, plinth_top - 0.3), factory.brick)
    builder.box((x - 1.95, y - 1.95, plinth_top - 0.3), (x + 1.95, y + 1.95, plinth_top), factory.stone)
    builder.lathe([(1.95, plinth_top), (1.5, plinth_top + 0.35)], factory.stone, centre=(x, y, 0), square=True)
    shaft_top = height - 1.6
    bottom_radius, top_radius = 1.45, 0.92
    radius_at = lambda z: bottom_radius + (top_radius - bottom_radius) * (z - plinth_top) / (shaft_top - plinth_top)
    for z0, z1, shade in soot_segments(plinth_top, shaft_top):
        builder.lathe([(radius_at(z0), z0), (radius_at(z1), z1)], factory.chimney_bricks[shade], centre=(x, y, 0), sides=32)
    band = plinth_top + 3.0
    while band < shaft_top - 1.0:
        hoop = radius_at(band) + 0.035
        builder.lathe([(hoop, band - 0.07), (hoop, band + 0.07)], factory.iron, centre=(x, y, 0), sides=32)
        band += 3.0
    top = top_radius
    builder.lathe([(top, shaft_top), (top + 0.1, shaft_top), (top + 0.1, shaft_top + 0.25), (top + 0.18, shaft_top + 0.25),
                   (top + 0.18, shaft_top + 0.5), (top + 0.26, shaft_top + 0.5), (top + 0.26, shaft_top + 0.75)],
                  factory.chimney_bricks[2], centre=(x, y, 0), sides=32, smooth=False)
    builder.lathe([(top + 0.3, shaft_top + 0.75), (top + 0.3, height - 0.45), (top + 0.2, height - 0.2), (top + 0.1, height),
                   (top - 0.14, height), (top - 0.14, height - 0.7), (0.001, height - 0.7)],
                  factory.cap_stone, centre=(x, y, 0), sides=32, smooth=False)
    conductor = [Vector((x + bottom_radius + 0.04, y, plinth_top + 0.35)), Vector((x + top_radius + 0.04, y, shaft_top)),
                 Vector((x + top_radius + 0.34, y, shaft_top + 0.75)), Vector((x + top_radius + 0.34, y, height + 1.0))]
    builder.rod((x + 1.95, y, 0.0), (x + 1.95, y, plinth_top), 0.02, factory.iron, sides=6)
    for a, b in zip(conductor, conductor[1:]):
        builder.rod(a, b, 0.025, factory.iron, sides=6)
    part = builder.finish(f'{factory.prefix}-{name}', parent=factory.group('chimneys'))
    return part


def build_square_chimney(factory, x, y, height, name):
    """A square brick chimney: a square plinth, a tapering square shaft with two stone bands, darkening
    towards an oversailing square cap with a stone coping round its dark flue."""
    builder = kit.MeshBuilder()
    plinth_top = 3.5
    builder.box((x - 1.6, y - 1.6, 0.0), (x + 1.6, y + 1.6, 0.6), factory.stone)
    builder.box((x - 1.5, y - 1.5, 0.6), (x + 1.5, y + 1.5, plinth_top - 0.3), factory.brick)
    builder.box((x - 1.6, y - 1.6, plinth_top - 0.3), (x + 1.6, y + 1.6, plinth_top), factory.stone)
    builder.lathe([(1.6, plinth_top), (1.15, plinth_top + 0.3)], factory.stone, centre=(x, y, 0), square=True)
    shaft_top = height - 1.5
    bottom_half, top_half = 1.0, 0.68
    half_at = lambda z: bottom_half + (top_half - bottom_half) * (z - plinth_top) / (shaft_top - plinth_top)
    for z0, z1, shade in soot_segments(plinth_top, shaft_top):
        builder.lathe([(half_at(z0), z0), (half_at(z1), z1)], factory.chimney_bricks[shade], centre=(x, y, 0), square=True)
    for fraction in (0.36, 0.68):
        z = plinth_top + (shaft_top - plinth_top) * fraction
        band = half_at(z) + 0.08
        builder.lathe([(band, z), (band, z + 0.35)], factory.stone, centre=(x, y, 0), square=True)
    top = top_half
    builder.lathe([(top, shaft_top), (top + 0.1, shaft_top), (top + 0.1, shaft_top + 0.3), (top + 0.2, shaft_top + 0.3),
                   (top + 0.2, shaft_top + 0.6), (top + 0.3, shaft_top + 0.6), (top + 0.3, shaft_top + 0.95)],
                  factory.chimney_bricks[2], centre=(x, y, 0), square=True)
    builder.lathe([(top + 0.36, shaft_top + 0.95), (top + 0.36, height - 0.25), (top + 0.22, height), (top - 0.18, height),
                   (top - 0.18, height - 0.7), (0.001, height - 0.7)], factory.cap_stone, centre=(x, y, 0), square=True)
    return builder.finish(f'{factory.prefix}-{name}', parent=factory.group('chimneys'))


def build_boiler_house(factory, x0, x1, chimney):
    """A single-storey brick boiler house at the back of the yard beside the chimney, with a slate roof,
    a timber door on its yard side and a low brick flue running into the chimney's plinth."""
    builder = kit.MeshBuilder()
    y0, y1, walls_top = BACK + 1.0, BACK + 10.0, 4.8
    front = Wall('boiler-front', 'x', y0, -1, x0, x1)
    door_u = (x0 + x1) / 2
    wall_with_openings(builder, front, 0.0, walls_top, [(door_u - 1.2, door_u + 1.2, 0.0, 3.2)], factory.brick)
    builder.box((x0, y1 - WALL, 0.0), (x1, y1, walls_top), factory.brick)
    builder.box((x0, y0 + WALL, 0.0), (x0 + WALL, y1 - WALL, walls_top), factory.brick)
    builder.box((x1 - WALL, y0 + WALL, 0.0), (x1, y1 - WALL, walls_top), factory.brick)
    middle, rise = (x0 + x1) / 2, (x1 - x0) / 2 * math.tan(math.radians(22))
    for y in (y0, y1 - WALL):
        builder.prism([(x0, walls_top), (x1, walls_top), (middle, walls_top + rise)], y, y + WALL, factory.brick, axis='y')
    builder.roof_slope((x0 - 0.3, y0 - 0.3, walls_top - 0.05), (x0 - 0.3, y1 + 0.3, walls_top - 0.05),
                       (middle, y1 + 0.3, walls_top + rise + 0.25), (middle, y0 - 0.3, walls_top + rise + 0.25), factory.slate)
    builder.roof_slope((x1 + 0.3, y1 + 0.3, walls_top - 0.05), (x1 + 0.3, y0 - 0.3, walls_top - 0.05),
                       (middle, y0 - 0.3, walls_top + rise + 0.25), (middle, y1 + 0.3, walls_top + rise + 0.25), factory.slate)
    front.box(builder, door_u - 1.3, door_u + 1.3, -0.04, 0.04, 3.2, 3.5, factory.stone)
    for k in range(6):
        a = door_u - 1.2 + k * 0.4
        front.box(builder, a + 0.005, a + 0.395, 0.1, 0.18, 0.02, 3.18, factory.door_paint)
    cx, cy = chimney[0], chimney[1]
    near_x = x0 if abs(x0 - cx) < abs(x1 - cx) else x1
    builder.box((min(near_x, cx), cy - 0.8, 0.0), (max(near_x, cx), cy + 0.8, 1.6), factory.brick)        # the flue
    return builder.finish(f'{factory.prefix}-boiler-house-building', parent=factory.group('boiler-house'))


def build_yard(factory):
    """The yard's setts, from the works wall back past the chimney, top 2 cm above the ground."""
    builder = kit.MeshBuilder()
    inner, outer = 0.3 * factory.side, (INNER_EDGE + MILL_WIDTH + 2.5) * factory.side
    builder.box((min(inner, outer), 0.6, -0.1), (max(inner, outer), YARD_DEPTH, 0.02), factory.setts)
    return builder.finish(f'{factory.prefix}-yard-setts', parent=factory.group('yard'))


# ------------------------------------------------------------------------------------------ build

def build(number):
    kit.empty_scene()
    factory = Factory(number)
    if number == 1:
        build_sawtooth_mill(factory)
        x, y, height = CHIMNEY_1
        build_round_chimney(factory, x, y, height, 'chimney')
        kit.empty('no-1-chimney-top', (x, y, height + 0.3), parent=factory.root)
        build_boiler_house(factory, -14.0, -7.4, CHIMNEY_1)
    else:
        build_pitched_mill(factory)
        for letter, (x, y, height) in zip('ab', CHIMNEYS_2):
            build_square_chimney(factory, x, y, height, f'chimney-{letter}')
            kit.empty(f'no-2-chimney-{letter}-top', (x, y, height + 0.3), parent=factory.root)
        build_boiler_house(factory, 11.0, 19.0, CHIMNEYS_2[1])
    build_yard(factory)
    factory.spread_steps()
    # both the lit and the dark material of every glass type are kept in the .blend (marked so Blender
    # keeps the unused ones), so a plate script can switch windows without the picture files
    for glass_type in (factory.window_type, factory.roof_glass_type, 'doorway-inside'):
        for state in ('lit', 'dark'):
            kit.glass_material(factory.prefix, glass_type, state).use_fake_user = True
    bpy.context.view_layer.update()
    parts = kit.descendants(factory.root)
    low, high = kit.bounds(parts)
    glass = kit.glass_pieces(factory.prefix)
    steps = {step: sum(1 for piece in glass if int(piece['window_step']) == step) for step in (0, 1, 2, 3)}
    print(f'{factory.root.name}: {len(parts)} objects, {kit.count_triangles(parts)} triangles, '
          f'{len(glass)} glass pieces (by step {steps}), from {tuple(round(v, 2) for v in low)} to {tuple(round(v, 2) for v in high)}')
    name = factory.root.name
    glb = os.path.join(OUT_FOLDER, f'{name}.glb')
    kit.export_glb(factory.root, glb)
    entry = kit.describe(factory.root, glb, DESCRIPTIONS[number], facts(factory))
    kit.save_blend(os.path.join(OUT_FOLDER, f'{name}.blend'))
    kit.record(OUT_FOLDER, entry)


DESCRIPTIONS = {
    1: ('No. 1, the quiet factory (always on the left): dark red-brown brick, one tall round chimney, a four-bay '
        'sawtooth roof, no water tank, a two-storey mill front with upper windows, cart doors shut. Saved with every '
        'window dark.'),
    2: ('No. 2, the flat-out factory (always on the right): pale buff-grey brick, two square chimneys, a water tank '
        'on a steel trestle, long pitched shed roofs with glazed lanterns, a two-storey mill front with upper windows, '
        'cart doors open on a lit works, a taking-in door with a hoist beam. Saved with every window lit.'),
}


def facts(factory):
    """The sizes that matter for composing the Works' views, from the layout used to build it."""
    side = factory.side
    mill = {'x': sorted([side * INNER_EDGE, side * (INNER_EDGE + MILL_WIDTH)]), 'y': [FRONT, BACK],
            'eaves': EAVES, 'first_floor': FIRST_FLOOR, 'ground_floor_windows': list(GROUND_WINDOWS),
            'upper_windows': list(UPPER_WINDOWS)}
    if factory.number == 1:
        x, y, height = CHIMNEY_1
        mill['roof'] = f'four-bay sawtooth, bays of {MILL_WIDTH / 4:g} m rising towards the centre line, peaks {EAVES + TOOTH:g} m'
        return {'mill': mill, 'round_chimney': {'x': x, 'y': y, 'height': height, 'shaft_diameter': [2.9, 1.84]},
                'cart_doorway': {'centre_x': -3.4, 'width': 3.0, 'height': 3.8}}
    spans = [(INNER_EDGE, 5.0), (5.0, 13.75), (13.75, INNER_EDGE + MILL_WIDTH)]
    mill['roof'] = ('three pitched spans, gables to the lane, ridges ' +
                    ', '.join(f'{EAVES + (b - a) / 2 * math.tan(PITCH):.2f} m' for a, b in spans) + ', lanterns on each ridge')
    return {'mill': mill,
            'square_chimneys': [{'x': x, 'y': y, 'height': height, 'shaft_side': [2.0, 1.36]} for x, y, height in CHIMNEYS_2],
            'water_tank': {'x': [6.9, 9.9], 'y': [FRONT + 1.6, FRONT + 4.6], 'bottom': 12.0, 'top': 14.8},
            'cart_doorway': {'centre_x': 2.9, 'width': 2.8, 'height': 3.8}, 'taking_in_door': {'x': [2.2, 3.6], 'z': [4.45, 7.0]}}


def main():
    names = {'1': 'no-1-quiet-factory', '2': 'no-2-flat-out-factory'}
    paths = [os.path.join(OUT_FOLDER, f'{names[n]}.{ending}') for n in WHICH for ending in ('glb', 'blend')]
    kit.stop_if_files_exist(paths, REPLACE)
    os.makedirs(OUT_FOLDER, exist_ok=True)
    for number in WHICH:
        build(int(number))


main()
