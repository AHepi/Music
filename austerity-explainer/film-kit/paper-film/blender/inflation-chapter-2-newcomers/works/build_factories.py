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
#     gate, its doors shut, and behind it a weaving shed's room with two chest-high power looms facing the lane (side
#     frames, a pale roll of cloth across the front, a big spoked driving wheel belted up to a countershaft).
#   No. 2, the flat-out factory: pale buff-grey brick (white_sandstone_bricks, toned); TWO SQUARE chimneys
#     (25 m and 23 m) of a paler buff still, sooted only in a narrow band under the cap, their faces toward
#     the lane and their sides lit warm by No. 2's own blazing yard (so that from the lane, where only their
#     tops show, they stay pale against the dusk and never read as No. 1's: round 2's check); a water tank on a steel trestle standing over its roof; long pitched shed roofs
#     (three spans, gables to the lane) with glazed roof lanterns along their ridges; a two-storey mill
#     front with upper windows; a cart doorway behind the gate with its doors open on a lit works (a lathe,
#     a power press with a big spoked flywheel and a pillar drill, belted to a line shaft), and over it, in
#     the gable above the gate, a row of three tall mill windows in the window groups.
# The machines are modelled (round 3's check: painted on the doorway's back wall as dark slabs in rising
# steps, they read as a bar chart on a phone); the doorway's far wall is lit, broken up by a darker lower part,
# shelves of boxes and tins, and a bobbin rack (No. 1) or a workbench and a rack of bar stock (No. 2) (round 5).
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
# <prefix>-doorway-foot (on the ground 1 m in front of the doorway's middle), no-2-tank-top, no-1-looms-middle and
# no-2-flywheel-middle (the middle of the two looms and of the press's flywheel, round 5). One root each: no-1-quiet-factory,
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
# No. 2's chimneys. Round 2's check: from street level (W1) only their top 8 to 9 m show over the roofs, and that
# part was sooted dark, so they came out dark red-brown against the dusk (about 15 levels of 255 against the sky's
# 75) and seemed to rise out of No. 1's own roof: No. 1 looked as if it had three chimneys. Now their brick is a
# paler buff than the mill's, the soot is a narrow band just under the cap, and each brick and stone face toward
# the lane (-y) wears a warm lit twin that gives off a little light of its own, as if lit from below by No. 2's
# lit windows and open doorway (its sides less, its back none). The dark cap stays: a pale shaft with a dark crown.
NO_2_CHIMNEY_BRICK = (1.0, 0.95, 0.84)          # tint over white_sandstone_bricks (the mill's is 0.92, 0.86, 0.74)
NO_2_CHIMNEY_SOOT = (0.88, 0.96)                # where the soot starts, and where it turns black, as shares of the
                                                # shaft (No. 1's: 0.62 and 0.82)
NO_2_YARD_GLOW = (1.0, 0.72, 0.46)              # the colour of the yard's light on the brick
NO_2_GLOW_STRENGTH = {'lane-side': 0.45, 'sides': 0.22}   # how strongly each face gives off that light
YARD_DEPTH = 42.0
DOORWAY_ROOM_DEPTH = 7.0         # the room seen through each cart doorway, from the front wall's face to its lit far wall
# No. 1's two looms: (centre along the wall from the doorway's middle, front's depth behind the wall's face, width), and
# the radius of each loom's big driving wheel (round 5)
LOOMS = ((0.25, 1.9, 1.8), (-1.2, 3.7, 1.7))
LOOM_WHEEL_RADIUS = 0.45
DADO_HEIGHT = 1.0                # the darker lower part of each doorway room's far wall (round 5)
GABLE_WINDOWS = (4.6, 7.2)       # No. 2's row of windows in the gable over its gate: sill and head heights
GABLE_WINDOW_WIDTH = 0.95
GABLE_WINDOW_CENTRES = (1.75, 2.9, 4.05)
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
    other axis (-1 or +1). Points on it are given as (along, depth, z): along the wall, depth into the wall
    from its face (negative: standing out in front of it), z up."""

    def __init__(self, name, axis, plane, out, start_along, end_along):
        self.name, self.axis, self.plane, self.out, self.start_along, self.end_along = name, axis, plane, out, start_along, end_along

    def point(self, along, depth, z):
        across = self.plane - self.out * depth
        return Vector((along, across, z)) if self.axis == 'x' else Vector((across, along, z))

    def right(self):
        """The direction to a viewer's right as they face the wall from outside."""
        outward = Vector((0, self.out, 0)) if self.axis == 'x' else Vector((self.out, 0, 0))
        return (-outward).cross(Vector((0, 0, 1)))

    def box(self, builder, start_along, end_along, near_depth, far_depth, z0, z1, material):
        one_corner, other_corner = self.point(start_along, near_depth, z0), self.point(end_along, far_depth, z1)
        builder.box(tuple(map(min, one_corner, other_corner)), tuple(map(max, one_corner, other_corner)), material)

    def face_corners(self, start_along, end_along, depth, z0, z1):
        """Corners of a flat piece on the wall (glass), bottom left, bottom right, top right, top left
        as seen from outside."""
        left, right = (start_along, end_along) if self.right().dot(self.point(1, 0, 0) - self.point(0, 0, 0)) > 0 else (end_along, start_along)
        return [self.point(left, depth, z0), self.point(right, depth, z0), self.point(right, depth, z1), self.point(left, depth, z1)]


def wall_with_openings(builder, wall, z0, z1, openings, material, thickness=WALL):
    """The wall's brickwork from z0 to z1 with rectangular openings [(start_along, end_along, z0, z1)] left open: built of
    boxes round the openings, so each opening's sides (the reveals) are brick too."""
    cuts_along = sorted({wall.start_along, wall.end_along} | {opening[0] for opening in openings} | {opening[1] for opening in openings})
    cuts_up = sorted({z0, z1} | {opening[2] for opening in openings if z0 < opening[2] < z1} | {opening[3] for opening in openings if z0 < opening[3] < z1})
    for lower, upper in zip(cuts_up, cuts_up[1:]):
        run_start = None
        for run_from, run_to in zip(cuts_along, cuts_along[1:]):
            middle_along, middle_z = (run_from + run_to) / 2, (lower + upper) / 2
            open_here = any(opening[0] < middle_along < opening[1] and opening[2] < middle_z < opening[3] for opening in openings)
            if not open_here and run_start is None:
                run_start = run_from
            if open_here and run_start is not None:
                wall.box(builder, run_start, run_from, 0, thickness, lower, upper, material)
                run_start = None
        if run_start is not None:
            wall.box(builder, run_start, cuts_along[-1], 0, thickness, lower, upper, material)


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
            # weathered, paler timber (round 5; round 4: dark brown): No. 1's shut cart doors stand behind its shut gate in
            # W1, and in the yard's faint cool light the gate's bars and the waiting men's heads now show dark against them
            self.door_paint = kit.surface_material('no-1-door-timber', 'distressed_painted_planks', tint=(0.52, 0.45, 0.37), roughness=0.7)
        else:
            self.brick = kit.surface_material('no-2-brick', 'white_sandstone_bricks', tint=(0.92, 0.86, 0.74))
            self.stone = kit.surface_material('no-2-stone', 'large_sandstone_blocks', tint=(0.6, 0.58, 0.54), tile_metres=1.5)
            # the chimneys' own paler brick, and for each brick and the stone bands a warm lit twin for the faces toward
            # the lane and the sides (lit_from_the_yard); the black under the cap has no twin, it stays dark
            shades = [('no-2-chimney-brick', 'white_sandstone_bricks', NO_2_CHIMNEY_BRICK, None, 1.0),
                      ('no-2-chimney-brick-sooted', 'white_sandstone_bricks', (0.56, 0.52, 0.46), None, 0.7),
                      ('no-2-stone', 'large_sandstone_blocks', (0.6, 0.58, 0.54), 1.5, 0.7)]
            self.chimney_lit_twins = {}
            for name, surface, tint, tile, share in shades:
                self.chimney_lit_twins[name] = {
                    facing: kit.surface_material(f'{name}-lit-{facing}', surface, tint=tint, tile_metres=tile,
                                                 glow=(NO_2_YARD_GLOW, NO_2_GLOW_STRENGTH[facing] * share))
                    for facing in NO_2_GLOW_STRENGTH}
            self.chimney_bricks = [kit.surface_material('no-2-chimney-brick', 'white_sandstone_bricks', tint=NO_2_CHIMNEY_BRICK),
                                   kit.surface_material('no-2-chimney-brick-sooted', 'white_sandstone_bricks', tint=(0.56, 0.52, 0.46)),
                                   kit.surface_material('no-2-chimney-brick-black', 'white_sandstone_bricks', tint=(0.16, 0.15, 0.14))]
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
    """Openings for windows: [(start_along, end_along, sill, head)] at each centre on each floor, leaving out the
    (centre index, floor index) pairs in skip."""
    found = []
    for floor_index, (sill, head) in enumerate(floors):
        for index, centre in enumerate(centres):
            if (index, floor_index) not in skip:
                found.append((centre - width / 2, centre + width / 2, sill, head))
    return found


def dress_wall(factory, wall, walls, dressings, iron, pilasters, openings, glass_type, eaves=True, doorways=(), other_glass=None):
    """Everything on one wall's face: pilasters, the plinth (broken at doorways), a string course at the
    first floor, a band under the eaves, stone sills and lintels at every window, and the glass. other_glass:
    {opening: glass type} for openings that wear another window picture (No. 2's narrow gable windows)."""
    for centre in pilasters:
        start_along, end_along = max(wall.start_along, centre - PILASTER / 2), min(wall.end_along, centre + PILASTER / 2)
        if centre <= wall.start_along + 0.01:
            start_along, end_along = wall.start_along, wall.start_along + PILASTER
        if centre >= wall.end_along - 0.01:
            start_along, end_along = wall.end_along - PILASTER, wall.end_along
        wall.box(walls, start_along, end_along, -0.14, 0.02, PLINTH, EAVES - 0.3, factory.brick)
    cuts = sorted(doorways)
    start = wall.start_along - 0.2
    for door_start, door_end in cuts + [(wall.end_along + 0.2, wall.end_along + 0.2)]:
        if door_start > start:
            wall.box(dressings, start, door_start, -0.2, 0.05, 0.0, PLINTH, factory.stone)
        start = door_end
    wall.box(dressings, wall.start_along - 0.05, wall.end_along + 0.05, -0.07, 0.02, FIRST_FLOOR, FIRST_FLOOR + 0.25, factory.stone)
    if eaves:
        wall.box(dressings, wall.start_along - 0.2, wall.end_along + 0.2, -0.2, 0.02, EAVES - 0.35, EAVES, factory.stone)
    for start_along, end_along, sill, head in openings:
        wall.box(dressings, start_along - 0.1, end_along + 0.1, -0.08, GLASS_SET_BACK, sill - 0.14, sill + 0.02, factory.stone)
        wall.box(dressings, start_along - 0.15, end_along + 0.15, -0.03, 0.03, head, head + 0.32, factory.stone)
        row = 'ground' if sill < FIRST_FLOOR else 'upper'
        number = len(factory.glass_rows.get((wall.name, row), [])) + 1
        factory.glass(f'window-{wall.name}-{row}-{number:02d}', wall.face_corners(start_along, end_along, GLASS_SET_BACK, sill + 0.02, head),
                      (other_glass or {}).get((start_along, end_along, sill, head), glass_type), (wall.name, row))


def doorway(factory, wall, walls, dressings, centre, width, height, open_doors, room_reach=(1.6, 1.6)):
    """A cart doorway: an opening with a stone lintel and kerbs, a room behind it with real machines in it
    (doorway_machines) and the lit (or dark) far wall of the works at its back, and two plank door leaves,
    each turning about its hinge. room_reach: how far the room runs past each jamb (it stays inside the mill's
    end walls). Round 3's check: the machines were painted on the back wall as flat dark slabs in rising steps,
    and through the doorway they read as a bar chart on a phone; now they are modelled, each its own outline."""
    start_along, end_along = centre - width / 2, centre + width / 2
    wall.box(dressings, start_along - 0.25, end_along + 0.25, -0.05, 0.05, height, height + 0.4, factory.stone)
    for along in (start_along - 0.12, end_along + 0.12):        # guard stones at the jambs' feet, against cart wheels
        wall.box(dressings, along - 0.12, along + 0.12, -0.25, 0.0, 0.0, 0.7, factory.stone)
    room = kit.MeshBuilder()
    depth = DOORWAY_ROOM_DEPTH
    room_start, room_end = start_along - room_reach[0], end_along + room_reach[1]
    ceiling = height + 0.9
    wall.box(room, room_start, room_end, WALL, depth, -0.02, 0.0, factory.inside_dark)                  # floor
    wall.box(room, room_start, room_end, WALL, depth, ceiling, ceiling + 0.1, factory.inside_dark)      # ceiling
    for along in (room_start - 0.1, room_end):
        wall.box(room, along, along + 0.1, WALL, depth, 0.0, ceiling, factory.inside_dark)              # sides
    doorway_group = factory.group('doorway')
    room.finish(f'{factory.prefix}-doorway-room', parent=doorway_group)
    doorway_machines(factory, wall, centre, room_start, room_end, ceiling, depth, doorway_group)
    inside = kit.glass_piece(f'{factory.prefix}-doorway-inside', wall.face_corners(room_start, room_end, depth - 0.05, 0.0, ceiling),
                             factory.prefix, 'doorway-inside', 'lit' if open_doors else 'dark', variant=0, step=0, parent=doorway_group)
    inside['window_step'] = 0
    # the two leaves: vertical planks with ledges and braces behind and strap hinges in front
    leaf_width, leaf_height, thickness = width / 2 - 0.01, height - 0.05, 0.08
    for side, hinge_along in (('left', start_along), ('right', end_along)):
        toward = 1 if hinge_along == start_along else -1
        leaf = kit.MeshBuilder()
        planks = 7
        plank = (leaf_width - 0.01 * (planks - 1)) / planks
        for k in range(planks):
            plank_start = hinge_along + toward * (k * (plank + 0.01))
            wall.box(leaf, min(plank_start, plank_start + toward * plank), max(plank_start, plank_start + toward * plank), 0.04, 0.04 + thickness, 0.03, leaf_height, factory.door_paint)
        for z in (0.4, leaf_height / 2, leaf_height - 0.4):
            wall.box(leaf, min(hinge_along, hinge_along + toward * leaf_width), max(hinge_along, hinge_along + toward * leaf_width),
                     0.04 + thickness, 0.04 + thickness + 0.05, z - 0.11, z + 0.11, factory.door_paint)
        for z in (0.55, leaf_height - 0.55):
            wall.box(leaf, min(hinge_along, hinge_along + toward * leaf_width * 0.75), max(hinge_along, hinge_along + toward * leaf_width * 0.75),
                     0.02, 0.04, z - 0.04, z + 0.04, factory.iron)
        hinge = wall.point(hinge_along, 0.04, 0.0)
        part = leaf.finish(f'{factory.prefix}-loading-door-{side}', parent=doorway_group, origin=hinge)
        if open_doors:
            # swung outwards (towards the lane) about 100 degrees, standing out from the wall like open
            # gates; doorways are only on the fronts, which face minus y
            part.rotation_euler.z = math.radians(-100 * toward)
    kit.empty(f'{factory.prefix}-doorway-foot', wall.point(centre, -1.0, 0.0), parent=factory.root)


def doorway_machines(factory, wall, centre, room_start, room_end, ceiling, depth, parent):
    """The machines seen through a cart doorway, each with its own outline so it reads as a machine and not as a
    block: a line shaft along the ceiling on hangers, with a pulley over each machine and a flat leather belt down to
    it, and hanging lamp shades. No. 1 (a weaving shed under its sawtooth roof): two power looms, one behind the
    other, each a cast-iron side frame with its rollers and warp. No. 2 (an engineering works): a lathe on cabinet
    legs with its stepped cone pulley, a power press with a big spoked flywheel facing the lane (driven from a short
    countershaft), and a pillar drill. Points are (along the wall, depth behind its face, height)."""
    iron = kit.surface_material(f'{factory.prefix}-machine-iron', 'rusty_metal_02', tint=(0.1, 0.1, 0.105), roughness=0.5, metallic=0.5)
    belt = kit.plain_material(f'{factory.prefix}-machine-belt', (0.05, 0.035, 0.025), roughness=0.75)
    warp = kit.plain_material(f'{factory.prefix}-loom-warp', (0.32, 0.29, 0.24), roughness=0.9)
    machines = kit.MeshBuilder()
    at = lambda along, behind, z: wall.point(along, behind, z)

    def box(a0, a1, d0, d1, z0, z1, material=iron):
        wall.box(machines, a0, a1, d0, d1, z0, z1, material)

    def rod_along(a0, a1, behind, z, radius, material=iron, sides=12):
        """A round bar or a pulley with its axis along the wall."""
        machines.rod(at(a0, behind, z), at(a1, behind, z), radius, material, sides=sides)

    def rod_back(along, d0, d1, z, radius, material=iron, sides=12):
        """A round bar or a hub with its axis running away from the lane."""
        machines.rod(at(along, d0, z), at(along, d1, z), radius, material, sides=sides)

    def strap(first, second, width=0.07):
        """A flat belt's straight run: wide across, thin toward the lane (the belts run up and down, across or back)."""
        machines.beam(first, second, width, 0.01, belt, up=(0, 1, 0))

    def belt_between(along, small, small_radius, big, big_radius):
        """A flat belt round a pulley with its axis along the wall (small: (depth, z)) and one on the shaft (big), as
        its two straight runs."""
        u = Vector((big[0] - small[0], big[1] - small[1])).normalized()
        n = Vector((-u.y, u.x))
        for sign in (1, -1):
            strap(at(along, small[0] + sign * n.x * small_radius, small[1] + sign * n.y * small_radius),
                  at(along, big[0] + sign * n.x * big_radius, big[1] + sign * n.y * big_radius))

    def wheel(along, behind, z, radius, spokes=6, rim=0.05):
        """A spoked wheel facing the lane (its axis running away from it): rim, spokes and hub."""
        segments = 28
        ring = [at(along + radius * math.cos(2 * math.pi * k / segments), behind, z + radius * math.sin(2 * math.pi * k / segments)) for k in range(segments)]
        for first, second in zip(ring, ring[1:] + ring[:1]):
            machines.rod(first, second, rim, iron, sides=6)
        for k in range(spokes):
            angle = 2 * math.pi * k / spokes + 0.3
            machines.rod(at(along, behind, z), at(along + (radius - rim) * math.cos(angle), behind, z + (radius - rim) * math.sin(angle)), 0.028, iron, sides=6)
        rod_back(along, behind - 0.12, behind + 0.12, z, 0.1)

    # the line shaft under the ceiling, on hangers, the full width of the room (in No. 1 it runs near the back wall,
    # where the looms' countershafts end at it)
    shaft_depth, shaft_z = (depth - 0.9 if factory.number == 1 else depth - 2.6), ceiling - 0.38
    rod_along(room_start + 0.15, room_end - 0.15, shaft_depth, shaft_z, 0.045, sides=10)
    along = room_start + 0.5
    while along < room_end - 0.3:
        machines.rod(at(along, shaft_depth, shaft_z), at(along, shaft_depth, ceiling), 0.03, iron, sides=6)
        box(along - 0.09, along + 0.09, shaft_depth - 0.09, shaft_depth + 0.09, shaft_z - 0.08, shaft_z + 0.1)   # bearing
        along += 1.7
    shaft_pulleys = []
    if factory.number == 1:
        # two power looms facing the lane, chest-high (round 5; round 4's check: low dark bars, "two church benches",
        # with no wheel, belt or cloth). The second stands further back and to the left, so both show through the
        # doorway. Each: two upright cast-iron side frames (a short front post, a tall back post, an arched top rail and
        # a cross rail), the breast beam with a pale roll of woven cloth across the front under it, the warp's pale sheet
        # rising to the back rest, the sley, and on its right end a big spoked driving wheel facing the lane, belted
        # straight up to a pulley on a short countershaft hung from the ceiling (its axis away from the lane, like No.
        # 2's press). The loom's own colour is a little lighter than No. 2's machines so its outline shows in the room's
        # light.
        cloth = kit.plain_material(f'{factory.prefix}-loom-cloth', (0.78, 0.74, 0.64), roughness=0.95)
        for loom_centre, front, width in LOOMS:
            loom_centre += centre
            left, right = loom_centre - width / 2, loom_centre + width / 2
            back = front + 1.2
            for side in (left, right):
                box(side - 0.05, side + 0.05, front, front + 0.1, 0.0, 1.22)               # the front post
                box(side - 0.05, side + 0.05, back - 0.1, back, 0.0, 1.42)                 # the back post
                machines.beam(at(side, front + 0.05, 1.22), at(side, (front + back) / 2, 1.5), 0.1, 0.1, iron)   # the arched top rail
                machines.beam(at(side, (front + back) / 2, 1.5), at(side, back - 0.05, 1.42), 0.1, 0.1, iron)
                machines.beam(at(side, front + 0.05, 0.55), at(side, back - 0.05, 0.55), 0.07, 0.08, iron)       # the cross rail
                box(side - 0.07, side + 0.07, front - 0.05, back + 0.05, 0.0, 0.1)         # the cross foot
            rod_along(left, right, front + 0.02, 1.12, 0.055)                              # the breast beam
            rod_along(left + 0.08, right - 0.08, front + 0.12, 0.72, 0.15, material=cloth, sides=16)   # the roll of cloth
            machines.quad([at(left + 0.1, front + 0.03, 1.1), at(right - 0.1, front + 0.03, 1.1), at(right - 0.1, front + 0.1, 0.86),
                           at(left + 0.1, front + 0.1, 0.86)], cloth)                       # the cloth running down to it
            rod_along(left + 0.05, right - 0.05, back - 0.15, 0.62, 0.17)                  # the warp beam
            rod_along(left + 0.05, right - 0.05, back - 0.08, 1.3, 0.04)                   # the back rest
            box(left + 0.05, right - 0.05, front + 0.3, front + 0.42, 1.0, 1.2)            # the sley
            rod_along(left - 0.05, right + 0.2, front + 0.55, 0.62, 0.045)                 # the crank shaft
            # the warp: a sheet of threads from the warp beam over the back rest to the cloth at the breast beam
            machines.quad([at(left + 0.1, back - 0.1, 1.3), at(right - 0.1, back - 0.1, 1.3), at(right - 0.1, front + 0.12, 1.14),
                           at(left + 0.1, front + 0.12, 1.14)], warp)
            # the big driving wheel on the crank shaft's right end, facing the lane, belted up to its countershaft
            wheel_along, wheel_z, wheel_radius = right + 0.16, 0.62, LOOM_WHEEL_RADIUS
            wheel(wheel_along, front + 0.55, wheel_z, wheel_radius, spokes=6, rim=0.04)
            jack_z = ceiling - 0.4
            rod_back(wheel_along, front + 0.35, front + 0.75, jack_z, 0.15, sides=14)       # the countershaft's pulley
            rod_back(wheel_along, front - 0.2, shaft_depth, jack_z, 0.04, sides=8)          # the countershaft
            for hanger in (front - 0.1, shaft_depth - 0.3):
                machines.rod(at(wheel_along, hanger, jack_z), at(wheel_along, hanger, ceiling), 0.03, iron, sides=6)
            for sign in (1, -1):        # the belt's two runs, flat toward the lane
                strap(at(wheel_along + sign * wheel_radius * 0.97, front + 0.51, wheel_z), at(wheel_along + sign * 0.15, front + 0.51, jack_z))
        # a marker in the middle of the two looms (round 5: the pages' label points at it)
        middle_along = centre + sum(loom[0] for loom in LOOMS) / len(LOOMS)
        middle_depth = sum(loom[1] for loom in LOOMS) / len(LOOMS) + 0.6
        kit.empty(f'{factory.prefix}-looms-middle', at(middle_along, middle_depth, 0.9), parent=factory.root)
    else:
        # a lathe on cabinet legs, its bed across the room, the headstock with its stepped cone pulley on the left
        lathe = centre - 0.75
        front = 2.2
        for a0, a1 in ((lathe - 0.95, lathe - 0.62), (lathe + 0.55, lathe + 0.88)):
            box(a0, a1, front - 0.05, front + 0.33, 0.0, 0.86)
        box(lathe - 1.0, lathe + 0.92, front, front + 0.26, 0.86, 1.0)                  # the bed
        box(lathe - 0.97, lathe - 0.52, front - 0.04, front + 0.3, 1.0, 1.36)          # the headstock
        for k, radius in enumerate((0.21, 0.165, 0.12)):                               # the cone pulley
            rod_along(lathe - 0.98 + k * 0.08, lathe - 0.9 + k * 0.08, front + 0.13, 1.56, radius, sides=16)
        rod_along(lathe - 0.52, lathe - 0.38, front + 0.13, 1.18, 0.09, sides=12)      # the chuck
        box(lathe + 0.55, lathe + 0.82, front, front + 0.26, 1.0, 1.3)                 # the tailstock
        rod_along(lathe + 0.38, lathe + 0.55, front + 0.13, 1.18, 0.035)               # its quill
        box(lathe - 0.08, lathe + 0.22, front - 0.06, front + 0.32, 1.0, 1.14)         # the saddle
        box(lathe + 0.02, lathe + 0.12, front + 0.04, front + 0.16, 1.14, 1.26)        # the tool post
        shaft_pulleys.append((lathe - 0.86, 0.3))
        belt_between(lathe - 0.86, (front + 0.13, 1.56), 0.165, (shaft_depth, shaft_z), 0.3)
        # a power press: a C-frame column, crown, ram and bolster, with a big spoked flywheel facing the lane on its
        # right, belted up to a short countershaft hung from the ceiling
        press = centre + 0.15
        back = depth - 1.9
        box(press - 0.28, press + 0.12, back, back + 0.5, 0.0, 2.15)                   # the column
        box(press - 0.34, press + 0.18, back - 0.45, back + 0.5, 0.0, 0.14)            # its foot
        box(press - 0.32, press + 0.16, back - 0.42, back + 0.1, 0.78, 0.94)           # the bolster
        box(press - 0.34, press + 0.2, back - 0.42, back + 0.5, 2.15, 2.5)             # the crown
        box(press - 0.16, press, back - 0.34, back - 0.18, 1.2, 2.15)                  # the ram
        flywheel_along, flywheel_z, flywheel_radius = press + 0.62, 2.0, 0.72
        wheel(flywheel_along, back - 0.2, flywheel_z, flywheel_radius)
        kit.empty(f'{factory.prefix}-flywheel-middle', at(flywheel_along, back - 0.2, flywheel_z), parent=factory.root)   # for the pages' label
        rod_back(flywheel_along, back - 0.2, back + 0.4, flywheel_z, 0.05)            # its shaft into the crown
        jack_z = ceiling - 0.35
        rod_back(flywheel_along, back - 0.32, back - 0.08, jack_z, 0.18, sides=14)    # the countershaft's pulley
        machines.rod(at(flywheel_along, back - 0.2, jack_z), at(flywheel_along, back - 0.2, ceiling), 0.03, iron, sides=6)
        for sign in (1, -1):        # the belt's two runs, flat toward the lane
            strap(at(flywheel_along + sign * flywheel_radius * 0.98, back - 0.24, flywheel_z), at(flywheel_along + sign * 0.18, back - 0.24, jack_z))
        # a pillar drill on the right, in front
        drill, front = centre + 1.05, 1.9
        box(drill - 0.28, drill + 0.28, front - 0.2, front + 0.38, 0.0, 0.12)          # the base
        machines.rod(at(drill, front + 0.22, 0.12), at(drill, front + 0.22, 2.0), 0.06, iron, sides=10)   # the column
        box(drill - 0.22, drill + 0.22, front - 0.12, front + 0.18, 0.86, 0.92)        # the table
        box(drill - 0.14, drill + 0.14, front - 0.08, front + 0.34, 1.55, 1.95)        # the head
        machines.rod(at(drill, front + 0.02, 1.55), at(drill, front + 0.02, 1.08), 0.025, iron, sides=6)   # the spindle
        for k, radius in enumerate((0.15, 0.11)):
            rod_along(drill - 0.1 + k * 0.08, drill - 0.02 + k * 0.08, front + 0.14, 2.12, radius, sides=14)
        shaft_pulleys.append((drill - 0.02, 0.26))
        belt_between(drill - 0.02, (front + 0.14, 2.12), 0.13, (shaft_depth, shaft_z), 0.26)
    for pulley_along, radius in shaft_pulleys:
        rod_along(pulley_along - 0.08, pulley_along + 0.08, shaft_depth, shaft_z, radius, sides=16)
    # the far wall broken up (round 5; round 4's check: a flat glowing panel, an empty hall lit like a lightbox): a
    # darker lower part (a painted dado up to DADO_HEIGHT), two long shelves of boxes and tins high up, and in No. 1 a
    # bobbin rack (rows of upright bobbins on pegs) against the wall's left part, in No. 2 a workbench with a vice and
    # a rack of bar stock. They stand in front of the lit wall, so they show as dark shapes against it, and the room's
    # own light gives them a little form. The middle band, where the machines and the people at them stand, stays lit,
    # so they show against it; No. 2's shelves are higher, above its flywheel.
    chooser = random.Random(factory.number * 37)
    far = depth - 0.05
    dado = kit.plain_material(f'{factory.prefix}-room-dado', (0.1, 0.075, 0.055) if factory.number == 1 else (0.085, 0.09, 0.08), roughness=0.9)
    timber = kit.plain_material(f'{factory.prefix}-room-shelf', (0.15, 0.1, 0.065), roughness=0.85)
    tins = kit.plain_material(f'{factory.prefix}-room-tins', (0.12, 0.12, 0.13), roughness=0.6)
    box(room_start + 0.12, room_end - 0.12, far - 0.07, far - 0.01, 0.0, DADO_HEIGHT, dado)
    box(room_start + 0.12, room_end - 0.12, far - 0.1, far - 0.01, DADO_HEIGHT, DADO_HEIGHT + 0.06, timber)       # its rail
    for shelf_z in ((2.3, 2.9) if factory.number == 1 else (3.0, 3.5)):
        box(room_start + 0.15, room_end - 0.15, far - 0.36, far - 0.01, shelf_z - 0.04, shelf_z, timber)
        along = room_start + 0.4
        while along < room_end - 0.3:
            box(along - 0.025, along + 0.025, far - 0.3, far - 0.01, shelf_z - 0.3, shelf_z - 0.04, iron)          # a bracket
            along += 1.2
        along = room_start + 0.25 + 0.2 * chooser.random()
        while along < room_end - 0.5:
            wide, high = 0.18 + 0.3 * chooser.random(), 0.1 + 0.2 * chooser.random()
            if chooser.random() < 0.35:
                rod_back(along + 0.1, far - 0.3, far - 0.06, shelf_z + 0.1, 0.09, material=tins, sides=10)          # a tin
                along += 0.22
            else:
                box(along, along + wide, far - 0.32, far - 0.05, shelf_z, shelf_z + high, timber if chooser.random() < 0.5 else tins)
                along += wide
            along += 0.04 + 0.25 * chooser.random()
    if factory.number == 1:
        # the bobbin rack: an upright frame with five rows of pale bobbins standing on pegs, on the wall's left part
        bobbins = kit.plain_material(f'{factory.prefix}-bobbins', (0.6, 0.52, 0.4), roughness=0.9)
        a0, a1 = centre - 2.15, centre - 0.85
        for a in (a0, a1):
            box(a - 0.03, a + 0.03, far - 0.4, far - 0.34, 0.0, 2.15)
        for row in range(5):
            z = 1.12 + row * 0.2
            box(a0, a1, far - 0.42, far - 0.32, z - 0.03, z)
            for k in range(9):
                spot = a0 + (k + 0.5) * (a1 - a0) / 9
                machines.rod(at(spot, far - 0.37, z), at(spot, far - 0.37, z + 0.15), 0.035, bobbins, sides=8)
    else:
        # the workbench along the far wall, a vice on it, and a rack of bar stock leaning on the wall on the right
        bench = (centre - 1.6, centre - 0.1)
        box(bench[0], bench[1], far - 0.7, far - 0.08, 0.86, 0.94, timber)
        for a in (bench[0] + 0.08, bench[1] - 0.08):
            box(a - 0.04, a + 0.04, far - 0.66, far - 0.12, 0.0, 0.86)
        box(bench[0] + 0.3, bench[0] + 0.48, far - 0.68, far - 0.5, 0.94, 1.12)                                    # the vice
        rack = centre + 1.1
        for k in range(7):
            lean = rack + 0.06 * k
            machines.rod(at(lean, far - 0.5, 0.0), at(lean + 0.12, far - 0.12, 2.5), 0.025, iron, sides=6)
        box(rack - 0.05, rack + 0.55, far - 0.2, far - 0.05, 2.1, 2.16)
    # lamp shades hanging on cords (their light is the lit far wall's and the room's light)
    for lamp_along, lamp_depth in ((centre - 0.9, 2.9), (centre + 0.7, 3.5), (centre - 0.1, 5.2)):
        low = ceiling - 1.0
        x, y, _ = at(lamp_along, lamp_depth, 0.0)
        machines.lathe([(0.03, low + 0.22), (0.22, low)], iron, centre=(x, y, 0), sides=14, smooth=False)
        machines.rod(at(lamp_along, lamp_depth, low + 0.22), at(lamp_along, lamp_depth, ceiling), 0.01, iron, sides=4)
    return machines.finish(f'{factory.prefix}-doorway-machines', parent=parent)


def gable_coping(builder, factory, x_low, z_low, x_high, z_high, y0, y1):
    """A stone coping along a gable's sloping edge from (x_low, z_low) up to (x_high, z_high), standing a
    little proud of both faces of the wall."""
    run = Vector((x_high - x_low, z_high - z_low)).normalized()
    lift = Vector((-run.y, run.x)) * 0.18
    if lift.y < 0:
        lift = -lift                     # always above the sloping edge
    low_end, high_end = Vector((x_low, z_low)) - run * 0.15, Vector((x_high, z_high))
    outline = [tuple(low_end), tuple(high_end), tuple(high_end + lift), tuple(low_end + lift)]
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
    for bay_start, bay_end in zip(bay_lines, bay_lines[1:]):
        centres += spread(bay_start + PILASTER / 2, bay_end - PILASTER / 2, 2, width)
    door_centre, door_width, door_height = -3.4, 3.0, 3.8
    for wall in (front, back):
        skip = {(len(centres) - 2, 0), (len(centres) - 1, 0)} if wall is front else set()
        openings = window_openings(wall, centres, width, floors, skip)
        doors = [(door_centre - door_width / 2, door_centre + door_width / 2, 0.0, door_height)] if wall is front else []
        wall_with_openings(walls, wall, 0.0, EAVES, openings + doors, factory.brick)
        dress_wall(factory, wall, walls, dressings, ironwork, bay_lines, openings, factory.window_type,
                   doorways=[(door[0], door[1]) for door in doors])
        if wall is front:
            doorway(factory, wall, walls, dressings, door_centre, door_width, door_height, open_doors=False, room_reach=(1.6, 0.8))
    side_lines = [FRONT + bay * k for k in range(5)]
    side_centres = []
    for bay_start, bay_end in zip(side_lines, side_lines[1:]):
        side_centres += spread(bay_start + PILASTER / 2, bay_end - PILASTER / 2, 2, width)
    openings = window_openings(outer_end, side_centres, width, floors)
    wall_with_openings(walls, outer_end, 0.0, EAVES, openings, factory.brick)
    dress_wall(factory, outer_end, walls, dressings, ironwork, side_lines, openings, factory.window_type)
    wall_with_openings(walls, inner_end, 0.0, EAVES, [], factory.brick)          # the blank party end
    inner_end.box(dressings, inner_end.start_along, inner_end.end_along, -0.05, 0.02, EAVES - 0.35, EAVES, factory.stone)
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
            panel_start, panel_end = y_from + k * panel + 0.06, y_from + (k + 1) * panel - 0.06
            corners = [Vector((high, panel_start, EAVES + 0.3)), Vector((high, panel_end, EAVES + 0.3)), Vector((high, panel_end, EAVES + TOOTH - 0.14)), Vector((high, panel_start, EAVES + TOOTH - 0.14))]
            factory.glass(f'north-light-{index + 1}-panel-{k + 1}', corners, factory.roof_glass_type, ('north-light', index))
            ironwork.box((high - 0.03, panel_end, EAVES + 0.28), (high + 0.06, panel_end + 0.12, EAVES + TOOTH - 0.1), factory.iron)  # mullion
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
    to the lane) with glazed lanterns along their ridges; the cart doorway and a row of three windows over it in
    the narrow first span; the steel trestle and water tank standing over the second span."""
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
    for wall in (front, back):
        openings, centres = [], []
        for index, (span_start, span_end) in enumerate(spans):
            count = 1 if index == 0 else 3
            these = spread(span_start + PILASTER / 2 + 0.05, span_end - PILASTER / 2 - 0.05, count, width)
            if wall is front and index == 0:
                continue                     # the doorway and the gable's window group instead
            centres += these
        openings = window_openings(wall, centres, width, floors)
        gable = []
        if wall is front:
            # the gable over the gate: a row of three tall mill windows over the cart doorway, sills just above its
            # lintel (in place of round 3's blank timber loft door), lit with the rest in the window groups. From W2
            # the gate board hides their upper half, so they start low: their lower part shows between the board and
            # the doorway, and "flat out" and the flicker show there (round 3's check: No. 2's windows were not in
            # the W2 frame at all). They are narrower than the mill's other windows, so they wear the narrow picture
            # (4 x 6 panes) and their panes stay about square.
            gable = [(centre - GABLE_WINDOW_WIDTH / 2, centre + GABLE_WINDOW_WIDTH / 2, GABLE_WINDOWS[0], GABLE_WINDOWS[1])
                     for centre in GABLE_WINDOW_CENTRES]
            openings += gable
        extra = [(door_centre - door_width / 2, door_centre + door_width / 2, 0.0, door_height)] if wall is front else []
        wall_with_openings(walls, wall, 0.0, EAVES, openings + extra, factory.brick)
        dress_wall(factory, wall, walls, dressings, ironwork, span_lines, openings, factory.window_type,
                   doorways=[(door_centre - door_width / 2, door_centre + door_width / 2)] if wall is front else [],
                   other_glass={opening: 'mill-window-narrow' for opening in gable})
        if wall is front:
            doorway(factory, wall, walls, dressings, door_centre, door_width, door_height, open_doors=True, room_reach=(0.4, 1.6))
    side_lines = [FRONT + MILL_DEPTH / 4 * k for k in range(5)]
    side_centres = []
    for bay_start, bay_end in zip(side_lines, side_lines[1:]):
        side_centres += spread(bay_start + PILASTER / 2, bay_end - PILASTER / 2, 2, width)
    openings = window_openings(outer_end, side_centres, width, floors)
    wall_with_openings(walls, outer_end, 0.0, EAVES, openings, factory.brick)
    dress_wall(factory, outer_end, walls, dressings, ironwork, side_lines, openings, factory.window_type)
    wall_with_openings(walls, inner_end, 0.0, EAVES, [], factory.brick)
    inner_end.box(dressings, inner_end.start_along, inner_end.end_along, -0.2, 0.02, EAVES - 0.35, EAVES, factory.stone)
    # the spans: gables with copings on the front and back walls, two slate slopes, a ridge roll,
    # gutters in the valleys and along the two eaves, downpipes; a lantern along each ridge
    tan = math.tan(PITCH)
    y_from, y_to = FRONT + WALL - 0.02, BACK - WALL + 0.02
    for index, (span_start, span_end) in enumerate(spans):
        middle, half = (span_start + span_end) / 2, (span_end - span_start) / 2
        ridge = EAVES + half * tan
        for y0, y1 in ((FRONT, FRONT + WALL), (BACK - WALL, BACK)):
            walls.prism([(span_start, EAVES), (span_end, EAVES), (middle, ridge)], y0, y1, factory.brick, axis='y')
            gable_coping(dressings, factory, span_start, EAVES, middle + 0.01, ridge, y0, y1)
            gable_coping(dressings, factory, span_end, EAVES, middle - 0.01, ridge, y0, y1)
            dressings.box((middle - 0.3, y0 - 0.1, ridge - 0.05), (middle + 0.3, y1 + 0.1, ridge + 0.35), factory.stone)   # apex
            for x in (span_start, span_end):
                dressings.box((x - 0.35, y0 - 0.1, EAVES - 0.25), (x + 0.35, y1 + 0.1, EAVES + 0.22), factory.stone)       # kneelers
        roof.roof_slope((span_start + 0.25 if span_start != inner else span_start - 0.35, y_from, EAVES + 0.12 + (0.25 if span_start != inner else -0.35) * tan),
                        (span_start + 0.25 if span_start != inner else span_start - 0.35, y_to, EAVES + 0.12 + (0.25 if span_start != inner else -0.35) * tan),
                        (middle, y_to, ridge + 0.12), (middle, y_from, ridge + 0.12), factory.slate)
        roof.roof_slope((span_end - 0.25 if span_end != outer else span_end + 0.35, y_to, EAVES + 0.12 + (0.25 if span_end != outer else -0.35) * tan),
                        (span_end - 0.25 if span_end != outer else span_end + 0.35, y_from, EAVES + 0.12 + (0.25 if span_end != outer else -0.35) * tan),
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
    for (from_x, from_y), (to_x, to_y) in zip(legs, legs[1:] + legs[:1]):    # bracing on each face: a tie and a cross
        from_z, to_z = roof_at(from_x) + 0.3, roof_at(to_x) + 0.3
        middle_z = (max(from_z, to_z) + bottom - 0.4) / 2
        trestle.beam((from_x, from_y, middle_z), (to_x, to_y, middle_z), 0.1, 0.14, factory.iron)
        trestle.beam((from_x, from_y, from_z), (to_x, to_y, bottom - 0.45), 0.03, 0.12, factory.iron)
        trestle.beam((to_x, to_y, to_z), (from_x, from_y, bottom - 0.45), 0.03, 0.12, factory.iron)
    tank.box((x0, y0, bottom), (x1, y1, bottom + height), factory.tank_steel)
    flange = 0.05
    for k in range(5):                                            # flanges: upright, then across, on every side
        x = x0 + (x1 - x0) * k / 4
        y = y0 + (y1 - y0) * k / 4
        for side_y in (y0, y1):
            tank.box((x - 0.03, side_y - flange if side_y == y0 else side_y, bottom), (x + 0.03, side_y if side_y == y0 else side_y + flange, bottom + height), factory.tank_steel)
        for side_x in (x0, x1):
            tank.box((side_x - flange if side_x == x0 else side_x, y - 0.03, bottom), (side_x if side_x == x0 else side_x + flange, y + 0.03, bottom + height), factory.tank_steel)
    for k in range(1, 4):
        z = bottom + height * k / 4
        tank.box((x0 - flange, y0 - flange, z - 0.03), (x1 + flange, y1 + flange, z + 0.03), factory.tank_steel)
    tank.box((x0 - 0.08, y0 - 0.08, bottom + height - 0.02), (x1 + 0.08, y1 + 0.08, bottom + height + 0.06), factory.tank_steel)   # lid
    tank.box((x0 + 0.6, y0 + 0.6, bottom + height + 0.06), (x0 + 1.3, y0 + 1.3, bottom + height + 0.22), factory.tank_steel)        # hatch
    rail_top = bottom + height + 1.0
    posts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)]
    for x, y in posts:
        trestle.rod((x, y, bottom + height), (x, y, rail_top), 0.025, factory.iron, sides=6)
    for (from_x, from_y), (to_x, to_y) in zip(posts[:4], posts[1:4] + posts[:1]):
        trestle.rod((from_x, from_y, rail_top), (to_x, to_y, rail_top), 0.025, factory.iron, sides=6)
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

def soot_segments(z0, z1, soot=(0.62, 0.82)):
    """Where a chimney's brick turns sooted and then black towards its top: [(from, to, shade)]. soot: where
    the soot starts and where it turns black, as shares of the shaft's height."""
    span = z1 - z0
    sooted, black = soot
    return [(z0, z0 + span * sooted, 0), (z0 + span * sooted, z0 + span * black, 1), (z0 + span * black, z1, 2)]


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
    for start, end in zip(conductor, conductor[1:]):
        builder.rod(start, end, 0.025, factory.iron, sides=6)
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
    for z0, z1, shade in soot_segments(plinth_top, shaft_top, NO_2_CHIMNEY_SOOT):
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
    part = builder.finish(f'{factory.prefix}-{name}', parent=factory.group('chimneys'))
    lit_from_the_yard(factory, part)
    return part


def lit_from_the_yard(factory, part):
    """No. 2's chimneys: each brick or stone face toward the lane (-y) takes its warm lit twin ('lane-side'),
    each face toward the sides (+x or -x) its half-lit twin ('sides'); the back, the tops and the black under the
    cap stay as they are. The shaft is square to the lane, so its faces look straight along x or y."""
    mesh = part.data
    names = [material.name for material in mesh.materials]
    for polygon in mesh.polygons:
        twins = factory.chimney_lit_twins.get(names[polygon.material_index])
        if twins is None:
            continue
        normal = polygon.normal
        facing = 'lane-side' if normal.y < -0.6 else 'sides' if abs(normal.x) > 0.6 else None
        if facing is None:
            continue
        twin = twins[facing]
        if twin.name not in names:
            mesh.materials.append(twin)
            names.append(twin.name)
        polygon.material_index = names.index(twin.name)


def build_boiler_house(factory, x0, x1, chimney):
    """A single-storey brick boiler house at the back of the yard beside the chimney, with a slate roof,
    a timber door on its yard side and a low brick flue running into the chimney's plinth."""
    builder = kit.MeshBuilder()
    y0, y1, walls_top = BACK + 1.0, BACK + 10.0, 4.8
    front = Wall('boiler-front', 'x', y0, -1, x0, x1)
    door_along = (x0 + x1) / 2
    wall_with_openings(builder, front, 0.0, walls_top, [(door_along - 1.2, door_along + 1.2, 0.0, 3.2)], factory.brick)
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
    front.box(builder, door_along - 1.3, door_along + 1.3, -0.04, 0.04, 3.2, 3.5, factory.stone)
    for k in range(6):
        plank_start = door_along - 1.2 + k * 0.4
        front.box(builder, plank_start + 0.005, plank_start + 0.395, 0.1, 0.18, 0.02, 3.18, factory.door_paint)
    chimney_x, chimney_y = chimney[0], chimney[1]
    near_x = x0 if abs(x0 - chimney_x) < abs(x1 - chimney_x) else x1
    builder.box((min(near_x, chimney_x), chimney_y - 0.8, 0.0), (max(near_x, chimney_x), chimney_y + 0.8, 1.6), factory.brick)        # the flue
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
    for glass_type in sorted({factory.window_type, factory.roof_glass_type, 'doorway-inside', 'mill-window-narrow'}):
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
        'sawtooth roof, no water tank, a two-storey mill front with upper windows, cart doors shut on a room of power '
        'looms. Saved with every window dark.'),
    2: ('No. 2, the flat-out factory (always on the right): pale buff-grey brick, two square chimneys of a paler buff '
        '(sooted only just under the cap, their faces toward the lane and their sides lit warm by the yard), a water tank '
        'on a steel trestle, long pitched shed roofs with glazed lanterns, a two-storey mill front with upper windows, '
        'cart doors open on a lit works with a lathe, a power press with a spoked flywheel and a pillar drill, a row of three '
        'tall windows in the gable over the gate. Saved with every window lit.'),
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
                'cart_doorway': {'centre_x': -3.4, 'width': 3.0, 'height': 3.8, 'room_depth': DOORWAY_ROOM_DEPTH,
                                 'machines': 'two chest-high power looms, each with a big driving wheel belted up to a countershaft, a roll of cloth across its front (no-1-doorway-machines)'}}
    spans = [(INNER_EDGE, 5.0), (5.0, 13.75), (13.75, INNER_EDGE + MILL_WIDTH)]
    mill['roof'] = ('three pitched spans, gables to the lane, ridges ' +
                    ', '.join(f'{EAVES + (b - a) / 2 * math.tan(PITCH):.2f} m' for a, b in spans) + ', lanterns on each ridge')
    return {'mill': mill,
            'square_chimneys': [{'x': x, 'y': y, 'height': height, 'shaft_side': [2.0, 1.36]} for x, y, height in CHIMNEYS_2],
            'water_tank': {'x': [6.9, 9.9], 'y': [FRONT + 1.6, FRONT + 4.6], 'bottom': 12.0, 'top': 14.8},
            'cart_doorway': {'centre_x': 2.9, 'width': 2.8, 'height': 3.8, 'room_depth': DOORWAY_ROOM_DEPTH,
                             'machines': 'a lathe, a power press with a spoked flywheel, a pillar drill, belted to a line shaft (no-2-doorway-machines)'},
            'gable_windows': {'x': [round(c - GABLE_WINDOW_WIDTH / 2, 3) for c in GABLE_WINDOW_CENTRES][:1] + [round(GABLE_WINDOW_CENTRES[-1] + GABLE_WINDOW_WIDTH / 2, 3)],
                              'z': list(GABLE_WINDOWS), 'count': len(GABLE_WINDOW_CENTRES)}}


def main():
    names = {'1': 'no-1-quiet-factory', '2': 'no-2-flat-out-factory'}
    paths = [os.path.join(OUT_FOLDER, f'{names[n]}.{ending}') for n in WHICH for ending in ('glb', 'blend')]
    kit.stop_if_files_exist(paths, REPLACE)
    os.makedirs(OUT_FOLDER, exist_ok=True)
    for number in WHICH:
        build(int(number))


main()
