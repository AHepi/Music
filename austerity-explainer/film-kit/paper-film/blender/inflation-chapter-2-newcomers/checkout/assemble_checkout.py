# What this does: builds "the checkout", chapter 2's opening picture ("34 Plan - chapter 2 full redesign - places, shots
# and order of work", part 1 "B. The checkout"; pages 1, 15 and 16 in part 2; findings T4, T12, T18, T21 and F13), in
# Blender by script, from an empty scene, and draws its plate and writes its files for the film.
#
# One checkout lane of a small suburban New Zealand supermarket in the evening, near closing time:
#   - the shop: a big grey-tiled floor, plastered walls, a suspended ceiling of tiles with fluorescent fittings in rows
#     (the rows near the queue switched off for closing time, which leaves the dark patch of ceiling at the top of the
#     frame for the typed words), the shop front's big window onto the car park, blue-black outside
#   - our lane (checkout_props.py): the counter with its black belt between steel rails, the scanner glass, the till on
#     the operator's side with an empty stool, the card terminal on its stand at the shoppers' side (its keypad turned
#     away from the queue), the rack of plain reusable bags along the shoppers' side, grey crates stacked at the end, and
#     the hanging CHECKOUT sign (no lane number); a lane on each side beyond
#   - the story group, touching: a full grey wire basket on the belt (a loaf in a paper bag printed BREAD, a milk bottle
#     with its MILK sleeve, BUTTER, CHEESE, kiwifruit, apples, a lemon, avocados and a bunch of bananas over the rim), the
#     divider bar against the basket's front, the newspaper bill in its wire stand at the end of the belt, its bottom edge
#     behind the basket's far side (THE EVENING LAMP, an invented paper; NEW MONEY: PRICES WILL GO UP in letters 0.1 m
#     tall), and the card terminal beyond, just behind the bill's right edge
#   - the warm lamp over the belt (out of the frame, above it) that makes the basket and the bill the brightest things
#   - the ends of two aisles beyond the left lane (Poly Haven's steel frame shelves with boxes)
#   - outside, through the window: the car park, the road and, across it, small and dim, a petrol station's canopy with
#     its fascia PETROL · DIESEL (no brand; its price board edge-on), and a few houses' lit windows beyond
# No people, no digits anywhere, no prices, no brands or chain colours: neutral greys and wood.
#
# The view C1 (the camera level, never turning, facing straight along the belt): where the next shopper in the queue
# stands, in line with the bill's right edge (x = CAMERA_X), eye 1.6 m above the floor; 3.1 m from the basket at the
# plate's spot and 2.4 m at the composed spot (page 1 slides in 0.7 m, 1.29 times nearer; page 16 slides back out).
# The belt's lines meet at the bill's right edge at eye height (on its first line, NEW MONEY:), just above the basket;
# the basket sits about 0.72 down the frame at the composed spot.
#
# Layout (metres, Blender, z up): x across the lane (the shoppers' side at plus x); y along the belt, away from the
# queue (0 at the counter's loading end); z up from the shop's floor. In three.js a point (x, y, z) is (x, z, -y).
#
# Run (a virtual screen is needed for EEVEE: Xvfb :96 -screen 0 1920x1080x24 &):
#   DISPLAY=:96 blender -b --python assemble_checkout.py -- [things to do]
# Things to do (any of):
#   --preview FILE        a small picture (540 x 960) with the film's lens at the composed spot (--spot plate for the
#                         plate's spot)
#   --plates FOLDER       the plates (PLATES below, 1536 x 2730, the plate's lens at the plate spot) as PNG; read Blender's
#                         log for "Shadow buffer full" and "Could not allocate shadow atlas"; --only NAME draws only that
#   --export              the film's files into the checkout folder (or --out FOLDER): checkout-set.glb, checkout-signs.glb,
#                         checkout-camera-c1.json and checkout-shot.json
#   --save FILE           the built scene as a .blend (no .blend1 backup)
#   --samples N           EEVEE samples (previews 16, plates 48)
#   --preview-width N     the preview's width (default 540)
#   --spot plate|composed where --preview stands (default composed)
#   --state NAME          main (default) or behind (the basket, its groceries and the divider left out: what they hide)
# Then the shot checker measures the composed spot:
#   BLEND= paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/checkout/assemble_checkout.py \
#       examples/inflation-chapter-2-newcomers/checkout-c1-shot-check.json OUT [PICTURE]
#   (check-shot.sh opens a .blend first: build_checkout.sh gives it an empty one, checkout-empty.blend)

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'works')))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'pit-village')))
import works_kit as kit            # noqa: E402
import checkout_props as props     # noqa: E402
import set_dressing as dressing    # noqa: E402

SCRIPT_NAME = 'assemble_checkout.py'
CHECKOUT_FOLDER = props.CHECKOUT_FOLDER
given = kit.arguments()
SAMPLES = kit.option('--samples')
PREVIEW_WIDTH = int(kit.option('--preview-width', '540'))
OUT_FOLDER = os.path.abspath(kit.option('--out', CHECKOUT_FOLDER))
STATE = kit.option('--state', 'main')

# ------------------------------------------------------------------------------------------ the layout

FILM_FOV, PLATE_FOV = 60.4, 64.4          # the film's lens and the plate's (a little wider, so a slide stays inside it)
FILM_ASPECT = 1080 / 1920
EYE = 1.60                                # the camera's eye above the floor
BASKET_AT = (props.BELT_MIDDLE, 2.00)     # the basket's middle on the belt
PLATE_DISTANCE, COMPOSED_DISTANCE = 3.1, 2.4     # the camera's distance from the basket (plan 34: 3.1 m and 2.4 m)
BILL_FACE_Y = 2.60                        # the bill's face, 0.44 m beyond the basket's far rim, at the end of the belt
CAMERA_X = -0.16                          # in line with the bill's left edge
BILL_LEFT = CAMERA_X                      # the bill's left edge (the bill reaches 0.62 m to the right of it)
LEDGE = (2.45, 3.40, 0.78)                # the counter's packing ledge on the shoppers' side: y from, y to, x
TERMINAL_AT = (0.43, 3.08)                # the card terminal's post, on the ledge, just past the bill's right edge
TILL_AT = (-0.40, 3.10)                   # the till's post, on the counter's operator edge
STOOL_AT = (-0.95, 4.00)
BAG_RACK = (1.35, 2.60, 1.80)             # x, the near end's y, its length (along the shoppers' side of the lane)
SIGN_AT = (0.25, 4.40)                    # the hanging CHECKOUT sign, over the end of the counter, above the bill
FLOOR_EDGES = (-8.0, 6.0, -4.0)           # the room: left wall, right wall, back wall (behind the queue)
FRONT_WALL_Y = 7.80                       # the shop front with its window
CEILING = 3.40
WINDOW = (-5.6, 4.6, 0.45, 2.75)          # the window: left, right, bottom, top
# the window's mullions: none between x -2.3 and -0.4, where PETROL · DIESEL shows through it from the plate spot to the
# composed spot (the ones at 0.0 and 1.4 stand behind the bill)
MULLIONS = (-5.6, -4.0, -2.5, 0.0, 1.4, 3.0, 4.6)
LIGHT_ROWS_Y = (-2.8, -0.4, 2.0, 4.4, 6.4)
LIGHT_ROWS_X = (-4.2, -1.8, 0.6, 3.0)
LIT_FROM_Y = 6.0                          # the ceiling rows nearer than this are switched off (closing time)
NEIGHBOUR_LANES = (-1.55, 1.90)           # how far the lanes on each side are moved across (their counters, no belts)
AISLE_ENDS = ((-2.0, 6.6), (-3.3, 6.6))    # the two aisles' ends beyond the left lane (x middle, y of their faces)
PETROL_AT = (-4.5, 31.0)                  # the petrol station's canopy: the middle of its front edge (on the quiet side)
ROAD = (21.0, 28.5)                       # the road across the car park (its near and far kerbs)
SHOP_FLOOR_STEP = 0.15                    # the car park lies this far below the shop's floor


def view_spots():
    """The view C1: plate spot and composed spot (x, y) and what it is about."""
    return {'c1': {'plate': (CAMERA_X, BASKET_AT[1] - PLATE_DISTANCE), 'composed': (CAMERA_X, BASKET_AT[1] - COMPOSED_DISTANCE),
                   'eye': EYE, 'subject': (BILL_LEFT + props.BILL_WIDTH / 2, BILL_FACE_Y, props.COUNTER_TOP + props.BILL_BOTTOM + props.BILL_HEIGHT / 2),
                   'about': 'the basket on the belt and the newspaper bill beyond it, from the next place in the queue'}}


# ------------------------------------------------------------------------------------------ helpers

bpy.context.preferences.filepaths.save_version = 0      # no .blend1 backups


def place(file_name, location, turn=0.0, scale=1.0, name=None, collection_name='props', keep=None):
    """Imports a prop from the checkout's library (assets/.../checkout/props) at location, turned about z (degrees);
    keep: only the parts whose names are listed stay (the others are removed)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(props.PROPS, f'{file_name}.glb'))
    imported = [o for o in bpy.data.objects if o not in before]
    if keep:
        for o in [o for o in imported if o.type == 'MESH' and o.name.split('.')[0] not in keep]:
            imported.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
    holder = bpy.data.objects.new(name or file_name, None)
    kit.collection(collection_name).objects.link(holder)
    for o in imported:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        kit.collection(collection_name).objects.link(o)
        if o.parent is None:
            o.parent = holder
    holder.location = location
    holder.rotation_euler = Euler((0, 0, math.radians(turn)))
    holder.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    return holder


def tint_imported(holder, colour, strength=1.0):
    """Multiplies an imported prop's base colour by colour (a plastic crate's orange made grey)."""
    for o in holder.children_recursive:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            material = slot.material
            if not material or material.get('checkout_tinted'):
                continue
            material = material.copy()
            material['checkout_tinted'] = True
            slot.material = material
            nodes, links = material.node_tree.nodes, material.node_tree.links
            shader = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if shader is None:
                continue
            base = shader.inputs['Base Color']
            multiply = nodes.new('ShaderNodeMix')
            multiply.data_type = 'RGBA'
            multiply.blend_type = 'MULTIPLY'
            multiply.inputs['Factor'].default_value = strength
            multiply.inputs[7].default_value = (*colour, 1)
            if base.links:
                links.new(base.links[0].from_socket, multiply.inputs[6])
            else:
                multiply.inputs[6].default_value = base.default_value
            grey = nodes.new('ShaderNodeHueSaturation')
            grey.inputs['Saturation'].default_value = 0.08
            links.new(multiply.outputs[2], grey.inputs['Color'])
            links.new(grey.outputs['Color'], base)


def light(name, kind, location, energy, colour, target=None, size=None, spot=None, shadow=False, soft=0.1, collection_name='checkout-lights'):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, colour
    data.use_shadow = shadow
    if kind in ('POINT', 'SPOT'):
        data.shadow_soft_size = soft
    if kind == 'AREA' and size:
        data.shape = 'RECTANGLE'
        data.size, data.size_y = size
    if kind == 'SPOT' and spot:
        data.spot_size, data.spot_blend = math.radians(spot[0]), spot[1]
    made = bpy.data.objects.new(name, data)
    made.location = location
    if target is not None:
        direction = Vector(target) - Vector(location)
        made.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    kit.collection(collection_name).objects.link(made)
    return made


def box(name, minimum, maximum, material, collection_name='room'):
    builder = kit.MeshBuilder()
    builder.box(minimum, maximum, material)
    return builder.finish(name, collection_name=collection_name)


# ------------------------------------------------------------------------------------------ the shop

def room():
    """The floor, walls, window, ceiling with its grid and its rows of fittings (lit only far from the queue)."""
    left, right, back = FLOOR_EDGES
    floor = props.surface('shop-floor', 'large_floor_tiles_02', 3.0, tint=(0.62, 0.62, 0.61), roughness=0.5, normal_strength=0.6)
    walls = props.surface('shop-walls', 'painted_plaster_wall', 2.0, tint=(0.62, 0.62, 0.61), roughness=0.85, normal_strength=0.5)
    ceiling = props.surface('shop-ceiling', 'ceiling_interior', 0.6, tint=(0.16, 0.16, 0.17), roughness=0.9, normal_strength=0.5)
    frame = props.plain('window-frame', (0.10, 0.10, 0.11), roughness=0.45, metallic=0.6)
    b = kit.MeshBuilder()
    b.quad([(left, back, 0), (right, back, 0), (right, FRONT_WALL_Y, 0), (left, FRONT_WALL_Y, 0)], floor)
    b.box((left - 0.2, back, 0), (left, FRONT_WALL_Y, CEILING), walls)
    b.box((right, back, 0), (right + 0.2, FRONT_WALL_Y, CEILING), walls)
    b.box((left, back - 0.2, 0), (right, back, CEILING), walls)
    # the shop front: a low wall under the window, a bulkhead over it, piers at its ends, mullions and a transom
    wl, wr, wb, wt = WINDOW
    # the shop front's inside: a dark charcoal bulkhead over the window and dark piers (a light wall there, lit by the
    # far row of fittings, was a bright band right across the frame)
    front = props.surface('shop-front', 'painted_plaster_wall', 2.0, tint=(0.24, 0.24, 0.25), roughness=0.85, normal_strength=0.5)
    b.box((left, FRONT_WALL_Y, 0), (right, FRONT_WALL_Y + 0.25, wb), front)
    b.box((left, FRONT_WALL_Y, wt), (right, FRONT_WALL_Y + 0.25, CEILING), front)
    b.box((left, FRONT_WALL_Y, wb), (wl, FRONT_WALL_Y + 0.25, wt), front)
    b.box((wr, FRONT_WALL_Y, wb), (right, FRONT_WALL_Y + 0.25, wt), front)
    for x in MULLIONS:
        b.box((x - 0.04, FRONT_WALL_Y + 0.05, wb), (x + 0.04, FRONT_WALL_Y + 0.17, wt), frame)
    b.box((wl, FRONT_WALL_Y + 0.05, wb - 0.02), (wr, FRONT_WALL_Y + 0.17, wb + 0.05), frame)
    b.box((wl, FRONT_WALL_Y + 0.05, wt - 0.05), (wr, FRONT_WALL_Y + 0.17, wt + 0.02), frame)
    # a dark skirting round the floor
    skirting = props.plain('skirting', (0.06, 0.06, 0.065), roughness=0.5)
    b.box((left, FRONT_WALL_Y - 0.012, 0), (right, FRONT_WALL_Y, 0.10), skirting)
    shop = b.finish('shop', collection_name='room')
    # the ceiling, its own object (the shot checker's check file counts it as the top band's dim "sky")
    top = kit.MeshBuilder()
    top.quad([(left, FRONT_WALL_Y, CEILING), (right, FRONT_WALL_Y, CEILING), (right, back, CEILING), (left, back, CEILING)], ceiling)
    top.finish('ceiling', collection_name='room')
    # the ceiling's structure, painted as dark as the ceiling: steel beams across the shop every 3 m (dark and quiet over the queue, where the typed words go; a light grid of ceiling tiles drew the eye)
    structure = kit.MeshBuilder()
    dark_paint = props.plain('ceiling-structure', (0.045, 0.045, 0.05), roughness=0.7, metallic=0.2)
    y = back + 1.0
    while y <= FRONT_WALL_Y:
        structure.box((left, y - 0.08, CEILING - 0.35), (right, y + 0.08, CEILING - 0.02), dark_paint)
        y += 3.0
    structure.finish('ceiling-structure', collection_name='room')
    return shop


FITTING_HEIGHT = 3.15                      # the fittings hang this high, under the open ceiling


def ceiling_lights():
    """The fluorescent fittings in rows, hung on two thin cables under the open ceiling: a shallow white batten with two
    of Poly Haven's tubes (mounted_fluorescent_lights) under it. The rows nearer the queue than LIT_FROM_Y are switched off
    for closing time (their tubes grey); the far ones are lit, each with a soft area light under it (no shadows)."""
    batten = props.plain('light-batten', (0.55, 0.55, 0.54), roughness=0.5, metallic=0.3)
    fittings = []
    for y in LIGHT_ROWS_Y:
        lit = y >= LIT_FROM_Y
        for x in LIGHT_ROWS_X:
            b = kit.MeshBuilder()
            b.box((x - 0.50, y - 0.11, FITTING_HEIGHT), (x + 0.50, y + 0.11, FITTING_HEIGHT + 0.05), batten)
            for dx in (-0.4, 0.4):
                b.rod((x + dx, y, FITTING_HEIGHT + 0.05), (x + dx, y, CEILING), 0.002, props.steel(), sides=4)
            made = b.finish(f'ceiling-fitting-{len(fittings) + 1}', collection_name='room')
            tubes = place('mounted-fluorescent-lights', (x, y + 0.253, FITTING_HEIGHT - 0.036), name=f'ceiling-fitting-{len(fittings) + 1}-tubes',
                          collection_name='room', keep={'mounted_fluorescent_lights_a', 'mounted_fluorescent_lights_b'})
            for o in tubes.children_recursive:
                if o.type != 'MESH':
                    continue
                for slot in o.material_slots:
                    if slot.material and slot.material.name.startswith('mounted_fluorescent_lights_glass'):
                        slot.material = tube_glass(lit)
            fittings.append(made)
            if lit:
                light(f'ceiling-light-{len(fittings)}', 'AREA', (x, y, FITTING_HEIGHT - 0.06), 40.0, (0.88, 0.93, 1.0), target=(x, y, 0), size=(1.0, 0.25))
    return fittings


def tube_glass(lit):
    """The tubes' glass: glowing cool white when lit, a dull grey when off."""
    if lit:
        return props.plain('tube-lit', (0.95, 0.97, 1.0), roughness=0.3, glow=((0.90, 0.95, 1.0), 3.5))
    return props.plain('tube-off', (0.40, 0.41, 0.42), roughness=0.3)


def lanes():
    """Our lane's counter and belt, and the counters of the lanes on each side (no belts: their far halves only show)."""
    ours, belt = props.counter('counter', props.COUNTER_LEFT, props.COUNTER_RIGHT, 0.0, props.COUNTER_END, ledge=LEDGE)
    for i, shift in enumerate(NEIGHBOUR_LANES):
        part, _ = props.counter(f'neighbour-counter-{i + 1}', props.COUNTER_LEFT + shift, props.COUNTER_RIGHT + shift, 0.6, props.COUNTER_END,
                                with_belt=False)
    return ours, belt


def aisle_ends():
    """Two aisles' ends beyond the left lane: Poly Haven's steel frame shelves (built ten times too big: shrunk), two
    side by side at each end, with boxes and plain packs on their shelves."""
    placed = []
    pack_colours = [(1.0, 0.95, 0.88), (0.80, 0.84, 0.90), (0.95, 0.93, 0.90), (0.70, 0.66, 0.62), (0.88, 0.82, 0.76)]
    for k, (x, y) in enumerate(AISLE_ENDS):
        for j, dx in enumerate((-0.56, 0.56)):
            shelf = place('steel-frame-shelves', (x + dx, y, 0.0), turn=0.0, scale=0.1, name=f'aisle-end-{k + 1}-shelf-{j + 1}', collection_name='aisles')
            placed.append(shelf)
            # packs on the shelves (the boards are at about 0.06, 0.55, 1.05, 1.55 and 2.05 m)
            b = kit.MeshBuilder()
            for level, board in enumerate((0.55, 1.05, 1.55)):
                px = x + dx - 0.48
                while px < x + dx + 0.44:
                    w = 0.07 + 0.05 * ((level * 7 + int(px * 31)) % 3)
                    h = 0.18 + 0.08 * ((level * 5 + int(px * 17)) % 3)
                    colour = pack_colours[(level * 3 + int(px * 23)) % len(pack_colours)]
                    b.box((px, y - 0.20, board + 0.02), (px + w, y + 0.05, board + 0.02 + h),
                          props.picture(f'packs-{colour[0]:.2f}', 'packs.jpg', tile=0.6, tint=colour, roughness=0.6))
                    px += w + 0.01
            b.finish(f'aisle-end-{k + 1}-packs-{j + 1}', collection_name='aisles')
        box_ = place('cardboard-box', (x - 0.3, y - 0.05, 0.06), turn=90, name=f'aisle-end-{k + 1}-box', collection_name='aisles')
        placed.append(box_)
    return placed


def outside():
    """The car park, the road, the petrol station across it and a few houses beyond, at night."""
    asphalt = props.surface('asphalt', 'asphalt_02', 3.0, tint=(0.30, 0.30, 0.31), roughness=0.85)
    road = props.surface('road', 'asphalt_02', 3.0, tint=(0.20, 0.20, 0.21), roughness=0.8)
    line = props.plain('road-line', (0.55, 0.55, 0.53), roughness=0.7)
    concrete = props.plain('footpath', (0.30, 0.30, 0.29), roughness=0.9, tile=2.0)
    ground = -SHOP_FLOOR_STEP
    b = kit.MeshBuilder()
    b.quad([(-60, FRONT_WALL_Y + 0.25, ground), (60, FRONT_WALL_Y + 0.25, ground), (60, ROAD[0] - 1.5, ground), (-60, ROAD[0] - 1.5, ground)], asphalt)
    b.box((-60, ROAD[0] - 1.5, ground), (60, ROAD[0], ground + 0.12), concrete)
    b.quad([(-60, ROAD[0], ground), (60, ROAD[0], ground), (60, ROAD[1], ground), (-60, ROAD[1], ground)], road)
    b.box((-60, ROAD[1], ground), (60, ROAD[1] + 1.5, ground + 0.12), concrete)
    b.quad([(-60, ROAD[1] + 1.5, ground + 0.01), (60, ROAD[1] + 1.5, ground + 0.01), (60, 90, ground + 0.01), (-60, 90, ground + 0.01)], asphalt)
    # the car park's bays (white lines) and the road's dashed middle line
    for i in range(-6, 7):
        x = i * 2.6
        b.box((x - 0.05, FRONT_WALL_Y + 4.0, ground), (x + 0.05, FRONT_WALL_Y + 9.0, ground + 0.006), line)
    for i in range(-12, 13):
        b.box((i * 5.0 - 1.5, (ROAD[0] + ROAD[1]) / 2 - 0.06, ground), (i * 5.0 + 1.5, (ROAD[0] + ROAD[1]) / 2 + 0.06, ground + 0.006), line)
    b.finish('outside-ground', collection_name='outside')
    station = props.petrol_station('petrol-station')
    station.location = (PETROL_AT[0], PETROL_AT[1], ground)
    # houses beyond: dark gabled shapes with a few warm windows
    houses = kit.MeshBuilder()
    wall = props.plain('house-wall', (0.10, 0.10, 0.11), roughness=0.9, tile=2.0)
    roof = props.plain('house-roof', (0.05, 0.05, 0.06), roughness=0.9, tile=2.0)
    window_lit = props.plain('house-window', (0.6, 0.45, 0.3), glow=((1.0, 0.72, 0.45), 1.2))
    for i, (x, y) in enumerate(((-14, 58), (-4, 60), (6, 62), (16, 59), (26, 61))):
        houses.box((x - 4, y, ground), (x + 4, y + 8, ground + 3.0), wall)
        houses.prism([(x - 4.3, 3.0), (x + 4.3, 3.0), (x, 5.2)], y - 0.3, y + 8.3, roof, axis='y')
        if i % 2 == 0:
            houses.box((x - 1.4, y - 0.02, ground + 1.0), (x - 0.4, y, ground + 2.0), window_lit)
    houses.finish('houses-beyond', collection_name='outside')
    # the car park's light pole and the street lights
    poles = kit.MeshBuilder()
    pole = props.plain('light-pole', (0.18, 0.18, 0.19), roughness=0.6, metallic=0.5)
    for x, y, h in ((-4.5, FRONT_WALL_Y + 7.0, 7.0), (-12.0, ROAD[0] - 0.8, 7.5), (13.0, ROAD[0] - 0.8, 7.5)):
        poles.rod((x, y, ground), (x, y, ground + h), 0.07, pole)
        poles.box((x - 0.3, y - 0.12, ground + h), (x + 0.3, y + 0.12, ground + h + 0.12), pole)
        light(f'street-light-{len(poles.materials)}-{x:g}', 'POINT', (x, y, ground + h - 0.2), 900.0, (1.0, 0.86, 0.68), soft=0.3)
    poles.finish('light-poles', collection_name='outside')
    return station


# ------------------------------------------------------------------------------------------ the story

def basket_and_groceries():
    """The full basket on the belt, its groceries heaped above the rim so every word shows whole, the bananas over its
    right-hand rim; and the divider bar against its front. Returns {name: object}."""
    x0, y0 = BASKET_AT
    base_z = props.BELT_TOP
    basket = props.wire_basket('basket')
    basket.location = (x0, y0, base_z)
    made = {'basket': basket}

    def put(part, local, tilt=(0, 0, 0), turn=0.0):
        part.parent = basket
        part.location = local
        rotation = Euler(tuple(math.radians(v) for v in tilt))
        rotation.rotate(Euler((0, 0, math.radians(turn))))
        part.rotation_euler = rotation
        return part

    # Three layers, so the basket reads full and nothing floats: fruit on its floor (the apples' red shows through the
    # front wires), a second layer of fruit, and on top at the front the butter and the cheese lying flat, their lettered
    # fronts just above the rim; at the back the loaf standing up and the milk bottle on the fruit, its sleeve above the
    # rim; the bananas over the right-hand rim.
    floor_z = 0.014
    made['bread'] = put(props.bread_loaf('basket-bread'), (-0.135, 0.062, floor_z), turn=7)
    made['milk'] = put(props.milk_bottle('basket-milk'), (0.045, 0.068, floor_z + 0.092), tilt=(-4, 0, 0), turn=-3)
    made['butter'] = put(props.butter_block('basket-butter'), (-0.095, -0.072, 0.205), tilt=(0, 2, 0), turn=6)
    made['cheese'] = put(props.cheese_block('basket-cheese'), (0.062, -0.072, 0.204), tilt=(0, -2, 0), turn=-5)
    fruit = [
        # the floor: four apples along the front, kiwifruit and an avocado behind them
        ('apple', (-0.150, -0.080, floor_z), 0), ('apple', (-0.050, -0.088, floor_z), 50), ('apple', (0.050, -0.082, floor_z), 100),
        ('apple', (0.150, -0.086, floor_z), 150), ('kiwifruit', (-0.060, 0.000, floor_z), 20), ('kiwifruit', (0.020, -0.004, floor_z), 70),
        ('avocado', (0.120, 0.000, floor_z), 10), ('kiwifruit', (0.045, 0.068, floor_z), 30),
        # the second layer, under the butter and cheese and round the milk
        ('kiwifruit', (-0.130, -0.075, 0.100), 40), ('apple', (-0.050, -0.070, 0.100), 20), ('apple', (0.030, -0.075, 0.100), 200),
        ('kiwifruit', (0.110, -0.075, 0.100), 90), ('avocado', (-0.040, 0.010, 0.090), 120), ('lemon-fruit', (0.130, 0.040, 0.090), 15),
        # a few on top, between the things with words
        ('kiwifruit', (-0.025, 0.020, 0.185), 60), ('avocado', (0.135, 0.050, 0.170), 250), ('apple', (-0.180, -0.010, 0.120), 300),
    ]
    for i, (file_name, local, turn) in enumerate(fruit):
        holder = place(file_name, (0, 0, 0), turn=turn, name=f'basket-fruit-{i + 1}-{file_name}', collection_name='checkout')
        put(holder, local, turn=turn)
    bananas = place('bananas', (0, 0, 0), name='basket-bananas', collection_name='checkout', keep={'bananas_bunch'})
    for o in bananas.children:
        o.location.x -= 0.233        # the bunch's own middle onto the holder (Poly Haven lays it 0.23 m from the model's middle)
    put(bananas, (0.205, 0.035, 0.150), tilt=(0, -24, 0), turn=90)
    made['bananas'] = bananas
    divider = props.divider_bar('divider-bar')
    divider.location = (x0, y0 - props.BASKET['base'][1] / 2 - 0.025, base_z)
    made['divider'] = divider
    return made


def story():
    made = basket_and_groceries()
    stand, poster = props.bill_stand('bill-stand')
    stand.location = (BILL_LEFT + props.BILL_WIDTH / 2, BILL_FACE_Y - 0.019, props.COUNTER_TOP)
    made['bill-stand'], made['bill'] = stand, poster
    terminal = props.card_terminal('card-terminal')
    terminal.location = (TERMINAL_AT[0], TERMINAL_AT[1], props.COUNTER_TOP)
    made['card-terminal'] = terminal
    till_ = props.till('till')
    till_.location = (TILL_AT[0], TILL_AT[1], props.COUNTER_TOP)
    made['till'] = till_
    stool = props.operator_stool('operator-stool')
    stool.location = (STOOL_AT[0], STOOL_AT[1], 0.0)
    rack = props.bag_rack('bag-rack', length=BAG_RACK[2])
    rack.location = (BAG_RACK[0], BAG_RACK[1], 0.0)
    made['bag-rack'] = rack
    for i, (x, y, z, turn) in enumerate(((2.05, 4.70, 0.0, 3), (2.05, 4.70, 0.254, -2))):
        crate = place('plastic-crate', (x, y, z), turn=turn, name=f'crate-{i + 1}', collection_name='checkout')
        tint_imported(crate, (0.42, 0.44, 0.46))
    sign_material = props.picture('checkout-sign-lettering', 'checkout-sign.png', roughness=0.6)
    sign, cables = props.hanging_sign('checkout-sign', sign_material, drop=CEILING - 2.85)
    sign.location = cables.location = (SIGN_AT[0], SIGN_AT[1], 2.85)
    made['checkout-sign'] = sign
    return made


# ------------------------------------------------------------------------------------------ light

# The bill's own light, reaching only it (light linking, as the notice corner's warm light reaches only the notice): a cool
# white from the shop's lights above on its top, and warm from the lamp's pool on the counter below it (rule 6: lit from
# below, cool at the top and warm at the bottom)
BILL_LIGHTS = {'cool': 90.0, 'warm': 30.0}
WARM_LAMP = {'at': (0.30, 1.45, CEILING - 0.05), 'aim': (0.35, 2.00, 0.90), 'energy': 290.0, 'colour': (1.0, 0.50, 0.22), 'cone': (110, 0.9)}


def lights():
    """The evening's light: the warm lamp over the belt (out of the frame, above it), the far rows' fittings
    (ceiling_lights), a faint cool fill from the whole ceiling, the night outside, the petrol station's canopy."""
    world = bpy.data.worlds.new('night')
    world.use_nodes = True
    background = world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (0.010, 0.014, 0.026, 1)
    background.inputs['Strength'].default_value = 1.0
    bpy.context.scene.world = world
    made = {}
    made['warm-lamp'] = light('warm-lamp', 'SPOT', WARM_LAMP['at'], WARM_LAMP['energy'], WARM_LAMP['colour'], target=WARM_LAMP['aim'],
                              spot=WARM_LAMP['cone'], shadow=True, soft=0.06)
    # the bill takes its light from its own two lights below, not from the lamp over the belt (from above, the lamp lit the
    # bill's top more than its bottom, and the tops of the groceries more than the bill)
    dressing.light_reaches(made['warm-lamp'], [bpy.data.objects['bill-stand-bill-lettering']], only=False)
    bill = bpy.data.objects['bill-stand-bill-lettering']
    made['bill-cool'] = light('bill-cool', 'SPOT', (BILL_LEFT + 0.31, 0.9, CEILING - 0.3), BILL_LIGHTS['cool'], (0.80, 0.87, 1.0),
                              target=(BILL_LEFT + 0.31, BILL_FACE_Y, 2.15), spot=(20, 1.0), soft=0.3)
    dressing.light_reaches(made['bill-cool'], [bill])
    made['bill-warm'] = light('bill-warm-bounce', 'AREA', (BILL_LEFT + 0.31, BILL_FACE_Y - 0.30, props.COUNTER_TOP + 0.08), BILL_LIGHTS['warm'],
                              (1.0, 0.45, 0.18), target=(BILL_LEFT + 0.31, BILL_FACE_Y, 1.20), size=(0.7, 0.15))
    dressing.light_reaches(made['bill-warm'], [bill])
    made['fill'] = light('ceiling-fill', 'AREA', (-1.0, 2.0, CEILING - 0.1), 50.0, (0.80, 0.86, 0.95), target=(-1.0, 2.0, 0.0), size=(11.0, 11.0))
    made['bounce'] = light('bounce-to-ceiling', 'AREA', (0.0, 1.5, 1.0), 18.0, (0.95, 0.90, 0.85), target=(0.0, 1.5, 5.0), size=(6.0, 8.0))
    made['canopy'] = light('canopy-light', 'AREA', (PETROL_AT[0], PETROL_AT[1] + 4.0, -SHOP_FLOOR_STEP + 4.5), 300.0, (0.92, 0.95, 1.0),
                           target=(PETROL_AT[0], PETROL_AT[1] + 4.0, 0.0), size=(11.5, 7.5))
    return made


def picture_settings():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    try:
        scene.eevee.use_shadows = True
        scene.eevee.use_raytracing = False
    except AttributeError:
        pass
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.3


# ------------------------------------------------------------------------------------------ cameras, pictures, export

def camera():
    data = bpy.data.cameras.new('camera-c1')
    data.sensor_fit = 'VERTICAL'
    data.clip_start, data.clip_end = 0.05, 400.0
    made = bpy.data.objects.new('camera-c1', data)
    made.rotation_mode = 'XYZ'
    made.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')       # level, facing +y along the belt, never turned
    kit.collection('cameras').objects.link(made)
    return made


def camera_spot(spot):
    x, y = view_spots()['c1'][spot]
    return Vector((x, y, EYE))


def put_camera(spot, fov):
    made = bpy.data.objects['camera-c1']
    made.location = camera_spot(spot)
    made.data.angle_y = math.radians(fov)
    bpy.context.scene.camera = made
    bpy.context.view_layer.update()
    return made


STATES = {'main': 'everything', 'behind': 'the basket, its groceries and the divider bar left out: what they hide, for the behind picture'}
PLATES = {'checkout-c1-plate': ('main', 'C1: the basket on the belt, the bill beyond, from the plate\'s spot (3.1 m from the basket)'),
          'checkout-c1-behind-plate': ('behind', 'C1 helper: the same with the basket, its groceries and the divider left out (for the behind picture)')}


def set_state(name):
    hidden = name == 'behind'
    basket = bpy.data.objects['basket']
    for o in [basket] + list(basket.children_recursive) + [bpy.data.objects['divider-bar']]:
        o.hide_render = hidden
        o.hide_viewport = hidden


def render(path, width, height, samples):
    picture_settings()
    dressing.render(path, width, height, samples)


def draw_plates(folder, only):
    os.makedirs(folder, exist_ok=True)
    for name, (state, what) in PLATES.items():
        if only and name not in only:
            continue
        set_state(state)
        put_camera('plate', PLATE_FOV)
        print(f'assemble_checkout: drawing {name} ({what})', flush=True)
        render(os.path.join(folder, f'{name}.png'), 1536, 2730, int(SAMPLES or 48))
    set_state('main')


def projector_json():
    made = put_camera('plate', PLATE_FOV)
    q_blender = made.matrix_world.to_quaternion()
    q_three = Quaternion((1, 0, 0), math.radians(-90)) @ q_blender
    location = made.matrix_world.translation
    return {
        'about': f'The plate camera of the checkout\'s view C1 ({SCRIPT_NAME}), as the projector for projected-set.js. three.js space (y-up): '
                 'position (x, z, -y) of Blender; quaternion = rotation(-90 deg about x) * Blender quaternion.',
        'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
        'quaternion': [round(q_three.x, 6), round(q_three.y, 6), round(q_three.z, 6), round(q_three.w, 6)],
        'fov': PLATE_FOV, 'aspect': FILM_ASPECT, 'near': 0.05, 'far': 400,
        'blender': {'location': [round(v, 5) for v in location], 'rotation_quaternion_wxyz': [round(v, 6) for v in q_blender]},
    }


# the film's files: name: (collections, what it holds)
PARTS = {
    'checkout-set.glb': (('room', 'checkout', 'aisles', 'outside', 'props'), 'the shop, the three lanes, the story group, the aisles\' ends and the outside '
                                                                           '(the painting is shone onto it)'),
    'checkout-signs.glb': (('signs',), 'own surfaces: every lettered face (the bill, BREAD, MILK, BUTTER, CHEESE, CHECKOUT, PETROL · DIESEL)'),
}


def export_for_film(folder, facts):
    os.makedirs(folder, exist_ok=True)
    set_state('main')
    written = {}
    for file_name, (collections, what) in PARTS.items():
        bpy.ops.object.select_all(action='DESELECT')
        chosen = 0
        for o in bpy.context.scene.objects:
            if o.type in ('MESH', 'EMPTY') and any(c.name in collections for c in o.users_collection):
                o.select_set(True)
                chosen += 1
        path = os.path.join(folder, file_name)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_cameras=False,
                                  export_lights=False, export_apply=True, export_extras=True)
        written[file_name] = {'holds': what, 'objects': chosen, 'megabytes': round(os.path.getsize(path) / 1e6, 1)}
        print(f'assemble_checkout: wrote {file_name} ({written[file_name]["megabytes"]} MB, {chosen} objects)', flush=True)
    with open(os.path.join(folder, 'checkout-camera-c1.json'), 'w') as handle:
        json.dump(projector_json(), handle, indent=1)
    facts['files'] = written
    with open(os.path.join(folder, 'checkout-shot.json'), 'w') as handle:
        json.dump(facts, handle, indent=1)
    print('assemble_checkout: wrote checkout-camera-c1.json and checkout-shot.json into', folder)


def top_of(o, lift=0.0):
    """The middle of the top of an object and everything under it (Blender x, y, z)."""
    low, high = kit.bounds([o] + list(o.children_recursive))
    return [round((low.x + high.x) / 2, 3), round((low.y + high.y) / 2, 3), round(high.z + lift, 3)]


def middle_of(o):
    low, high = kit.bounds([o] + list(o.children_recursive))
    return [round(v, 3) for v in (low + high) / 2]


def letter_pixels(point_y, letter_metres, spot='composed'):
    depth = point_y - camera_spot(spot).y
    return round(1920 * letter_metres / (2 * depth * math.tan(math.radians(FILM_FOV / 2))), 1)


# ------------------------------------------------------------------------------------------ main

def build():
    kit.empty_scene()
    props.MATERIALS.clear()
    scene = bpy.context.scene
    room()
    ceiling_lights()
    lanes()
    aisle_ends()
    station = outside()
    made = story()
    made_lights = lights()
    camera()
    picture_settings()
    bpy.context.view_layer.update()
    sizes = json.load(open(os.path.join(props.TEXTURES, 'lettering-sizes.json')))['pictures']
    bill = sizes['bill.png']
    bill_top = props.COUNTER_TOP + props.BILL_BOTTOM + props.BILL_HEIGHT
    spots = {
        'bill': middle_of(made['bill']),
        'bill-left-edge': [round(BILL_LEFT, 3), BILL_FACE_Y, EYE],
        'bill-words': [round(BILL_LEFT + props.BILL_WIDTH / 2, 3), BILL_FACE_Y, round(bill_top - 0.35, 3)],
        'basket': top_of(made['basket']),
        'bread': top_of(made['bread']), 'milk': top_of(made['milk']), 'butter': top_of(made['butter']), 'cheese': top_of(made['cheese']),
        'bananas': top_of(made['bananas']),
        'apples': top_of(bpy.data.objects['basket-fruit-3-apple']), 'kiwifruit': top_of(bpy.data.objects['basket-fruit-15-kiwifruit']),
        'card-terminal': top_of(made['card-terminal']), 'checkout-sign': middle_of(made['checkout-sign']),
        'petrol-fascia': [PETROL_AT[0], PETROL_AT[1], round(-SHOP_FLOOR_STEP + 4.6 + 0.45, 3)],
        'divider': top_of(made['divider']),
    }
    facts = {
        'about': 'The checkout (assemble_checkout.py; plan 34 part 1 "B. The checkout"): where things are, Blender space (x, y, z), metres; three.js '
                 'is (x, z, -y). x across the lane (the shoppers\' side at plus x), y along the belt away from the queue, z up from the shop\'s floor.',
        'film_fov_degrees': FILM_FOV, 'plate_fov_degrees': PLATE_FOV,
        'views': {'c1': {'plate': [round(v, 3) for v in camera_spot('plate')], 'composed': [round(v, 3) for v in camera_spot('composed')],
                         'subject': [round(v, 3) for v in view_spots()['c1']['subject']], 'faces': '+y (along the belt)', 'eye_height_metres': EYE,
                         'stands_on': 'the shop\'s floor, the next place in the queue', 'about': view_spots()['c1']['about'],
                         'camera_file': 'checkout-camera-c1.json', 'slide': {'from': 'plate', 'to': 'composed', 'metres': PLATE_DISTANCE - COMPOSED_DISTANCE,
                                                                             'nearer_times': round(PLATE_DISTANCE / COMPOSED_DISTANCE, 3)}}},
        'spots': spots,
        'lettering': {'materials': sorted({m.name for o in bpy.data.collections['signs'].objects if o.type == 'MESH' for m in o.data.materials}),
                      'about': 'own surfaces: every lettered face keeps its own picture in the film (the painter garbles small print)'},
        'letter_pixels': {
            'about': 'capital letters\' height on the film\'s 1080 x 1920 frame at the composed spot (and at the plate spot)',
            'bill big words': letter_pixels(BILL_FACE_Y, 0.10), 'bill big words, plate spot': letter_pixels(BILL_FACE_Y, 0.10, 'plate'),
            'bill paper name': letter_pixels(BILL_FACE_Y, bill['lines'][-1]['caps_metres']),
            'CHECKOUT': letter_pixels(SIGN_AT[1], 0.11), 'PETROL · DIESEL': letter_pixels(PETROL_AT[1], 0.42),
        },
        'warm_lamp': {'at': list(WARM_LAMP['at']), 'aim': list(WARM_LAMP['aim'])},
        'states': STATES,
        'plates': {name: {'state': state, 'what': what} for name, (state, what) in PLATES.items()},
        'decisions': {
            'camera': 'in line with the bill\'s left edge (x -0.16), facing straight along the belt, so the belt\'s lines meet on that edge at eye '
                      'height, just under the bill\'s first line; the next shopper waits at the counter\'s loading end. The story group then stands '
                      'right of the frame\'s middle and the quiet side (the operator\'s side, the aisles\' ends, the petrol station through the '
                      'window) is on the left, as at the notice corner; with the bill on the left (round 5\'s first try) the bill and the basket '
                      'filled the bottom-left quarter where the eye enters, the black belt lay across it and the right half was bare floor',
            'bill': 'on a wire stand on the counter at the end of the belt, 0.44 m beyond the basket\'s far rim: its letters 0.1 m tall come out '
                    'about 55 pixels tall at the composed spot; its lowest line stays above everything in the basket',
            'groceries': 'heaped above the rim, every lettered face turned to the queue and above the rim, so each word shows whole',
            'top band': 'the ceiling rows nearer the queue than y 6.0 are off for closing time: the top band is dark ceiling',
            'warm lamp': 'a spot in the dark ceiling over the belt, just above the frame, aimed between the basket and the bill',
        },
    }
    return facts


facts = build()
if '--plates' in given:
    only = [name for name in (kit.option('--only') or '').split(',') if name]
    draw_plates(os.path.abspath(kit.option('--plates')), only)
if '--export' in given:
    export_for_film(OUT_FOLDER, facts)
set_state(STATE)
if kit.option('--preview'):
    put_camera(kit.option('--spot', 'composed'), FILM_FOV)
    render(kit.option('--preview'), PREVIEW_WIDTH, round(PREVIEW_WIDTH * 16 / 9), int(SAMPLES or 16))
if kit.option('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(kit.option('--save')), relative_remap=True)
put_camera('composed', FILM_FOV)       # left on the film's view, for a script run after this one (shot_facts.py)
print(f'assemble_checkout: done (state {STATE})', flush=True)
