# What this does: builds the checkout's own things in Blender by script, for assemble_checkout.py ("34 Plan - chapter 2
# full redesign", part 1 "B. The checkout", and part 3 "New things to build by script"): the checkout counter with its
# belt, rails, end rollers and scanner glass; the grey wire basket; the groceries that no free model covers (a loaf in a
# paper bag printed BREAD, a plastic milk bottle with its MILK sleeve, a block of butter in a BUTTER wrapper, a block of
# cheese with a CHEESE label); the divider bar; the newspaper bill in its wire stand with a tray of folded papers; the
# card terminal on its stand (its keypad turned away, no figures on it anyway); the till; the rack of reusable bags;
# the hanging CHECKOUT sign; and, across the road, the petrol station's canopy with its PETROL · DIESEL fascia, pumps and
# a price board turned edge-on. Run inside Blender; it does nothing by itself.
#
# Every lettered face is its own object in the "signs" collection, wearing a material whose name ends in "-lettering"
# (the film keeps it as its own sharp surface: the painter garbles small print). The lettering's pictures come from
# paint_checkout_pictures.py (assets/models/inflation-chapter-2-newcomers/checkout/textures). No figure (digit),
# brand, logo or chain colour anywhere: greys, wood, white, cream and brown.
#
# Layout (metres, Blender, z up): x across the lane (the belt's middle at x = BELT_MIDDLE, the shoppers' side at plus
# x), y along the belt, away from the queue (0 at the counter's loading end), z up from the shop's floor.

import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'works')))
import works_kit as kit   # noqa: E402   (MeshBuilder, collections, empties)

KIT_FOLDER = kit.KIT_FOLDER
CHECKOUT_FOLDER = os.path.join(KIT_FOLDER, 'assets', 'models', 'inflation-chapter-2-newcomers', 'checkout')
TEXTURES = os.path.join(CHECKOUT_FOLDER, 'textures')
PROPS = os.path.join(CHECKOUT_FOLDER, 'props')

# ---------------------------------------------------------------------------------------------- the counter's sizes
COUNTER_TOP = 0.90            # the counter's top
COUNTER_LEFT = -0.50          # the operator's side face
COUNTER_RIGHT = 0.36          # the shoppers' side face
COUNTER_END = 4.30            # the far end of the bagging area
BELT_LEFT, BELT_RIGHT = -0.22, 0.28
BELT_MIDDLE = (BELT_LEFT + BELT_RIGHT) / 2
BELT_START, BELT_END = 0.10, 2.42
BELT_TOP = 0.885              # the rubber's top, a little below the rails
RAIL_TOP = 0.915
SCANNER_Y = (2.86, 3.16)      # the scanner's glass in the counter top

# ---------------------------------------------------------------------------------------------- materials

MATERIALS = {}


def _shader(material):
    return material.node_tree.nodes['Principled BSDF']


def plain(name, colour, roughness=0.6, metallic=0.0, glow=None, tile=1.0, alpha=None):
    """A material of one colour. glow (colour, strength): it gives off light of its own."""
    if name in MATERIALS:
        return MATERIALS[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = _shader(material)
    shader.inputs['Base Color'].default_value = (*colour, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    if glow:
        shader.inputs['Emission Color'].default_value = (*glow[0], 1)
        shader.inputs['Emission Strength'].default_value = glow[1]
    if alpha is not None:
        shader.inputs['Alpha'].default_value = alpha
        material.surface_render_method = 'BLENDED'
    material['tile_metres'] = tile
    MATERIALS[name] = material
    return material


def picture(name, file_name, tile=0.0, tint=None, roughness=0.6, metallic=0.0, normal=None, normal_strength=1.0, glow=None, colour_data=True):
    """A material wearing a picture from the checkout's textures folder. tile: metres one picture covers (0: the faces
    give their own picture coordinates, as a label does). tint: a colour the picture is multiplied by. normal: a relief
    picture (Poly Haven's) beside it. glow: the picture also gives off light, at this strength."""
    if name in MATERIALS:
        return MATERIALS[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = _shader(material)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(os.path.join(TEXTURES, file_name), check_existing=True)
    texture.image.colorspace_settings.name = 'sRGB'
    texture.location = (-700, 300)
    colour_out = texture.outputs['Color']
    if tint is not None:
        multiply = nodes.new('ShaderNodeMix')
        multiply.data_type = 'RGBA'
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs['Factor'].default_value = 1.0
        multiply.inputs[7].default_value = (*tint, 1)
        multiply.location = (-350, 300)
        links.new(texture.outputs['Color'], multiply.inputs[6])
        colour_out = multiply.outputs[2]
    links.new(colour_out, shader.inputs['Base Color'])
    if glow:
        links.new(colour_out, shader.inputs['Emission Color'])
        shader.inputs['Emission Strength'].default_value = glow
    if normal:
        relief = nodes.new('ShaderNodeTexImage')
        relief.image = bpy.data.images.load(os.path.join(TEXTURES, normal), check_existing=True)
        relief.image.colorspace_settings.name = 'Non-Color'
        relief.location = (-700, -100)
        normal_map = nodes.new('ShaderNodeNormalMap')
        normal_map.inputs['Strength'].default_value = normal_strength
        links.new(relief.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    material['tile_metres'] = tile
    MATERIALS[name] = material
    return material


def surface(name, poly_haven_id, tile, tint=None, roughness=0.7, metallic=0.0, normal_strength=1.0):
    """A material wearing a Poly Haven surface (NAME_colour.jpg, NAME_normal.jpg in the textures folder) at its real size."""
    return picture(name, f'{poly_haven_id}_colour.jpg', tile=tile, tint=tint, roughness=roughness, metallic=metallic,
                   normal=f'{poly_haven_id}_normal.jpg', normal_strength=normal_strength)


def steel():
    """Brushed stainless steel (plain: Poly Haven's metal_plate is a diamond tread plate, which read as a floor plate on
    the belt's rails)."""
    return plain('brushed-steel', (0.52, 0.53, 0.54), roughness=0.36, metallic=0.9)


def dark_steel():
    return plain('dark-steel', (0.10, 0.10, 0.11), roughness=0.5, metallic=0.7)


def wire_grey():
    """The basket's wire: zinc-grey coated steel."""
    return plain('basket-wire', (0.40, 0.41, 0.42), roughness=0.34, metallic=0.75)


def laminate():
    return picture('counter-laminate', 'counter-laminate.jpg', tile=1.0, roughness=0.55)


def wood():
    return surface('ash-wood', 'ash_veneer', 0.9, tint=(0.80, 0.72, 0.62), roughness=0.5)


def kick_plate():
    return plain('kick-plate', (0.05, 0.05, 0.055), roughness=0.6, metallic=0.3)


def dark_plastic():
    return plain('dark-plastic', (0.035, 0.036, 0.04), roughness=0.45)


def grey_plastic():
    return plain('grey-plastic', (0.30, 0.31, 0.32), roughness=0.5)


# ---------------------------------------------------------------------------------------------- small geometry helpers

def finish(builder, name, collection_name='checkout', parent=None, location=None, turn=0.0, tilt=None):
    """Make the builder's object; place it at location (its own origin is where its points' (0, 0, 0) is), turned
    `turn` degrees about z (and tilted by an Euler in degrees, applied before the turn)."""
    part = builder.finish(name, parent=parent, collection_name=collection_name)
    if location is not None:
        part.location = location
    rotation = Euler((0, 0, 0))
    if tilt is not None:
        rotation = Euler(tuple(math.radians(v) for v in tilt))
    rotation.rotate(Euler((0, 0, math.radians(turn))))
    part.rotation_euler = rotation
    return part


def loop(builder, points, radius, material, sides=6):
    """A closed loop of wire through the points."""
    for a, b in zip(points, points[1:] + points[:1]):
        builder.rod(a, b, radius, material, sides=sides)


def rounded_rectangle(half_x, half_y, z, corner, steps=3):
    """Points round a rectangle with rounded corners, at height z."""
    points = []
    for cx, cy, start in ((half_x - corner, half_y - corner, 0), (-half_x + corner, half_y - corner, 90),
                          (-half_x + corner, -half_y + corner, 180), (half_x - corner, -half_y + corner, 270)):
        for k in range(steps + 1):
            angle = math.radians(start + 90 * k / steps)
            points.append((cx + corner * math.cos(angle), cy + corner * math.sin(angle), z))
    return points


def triangle(builder, points, material):
    """One three-cornered face."""
    face = builder.bm.faces.new([builder.bm.verts.new(p) for p in points])
    builder._tag([face], material)
    return face


def point_along(points, fraction):
    """The point a fraction of the way along a line through the points (by length)."""
    points = [Vector(p) for p in points]
    lengths = [(c - a).length for a, c in zip(points, points[1:])]
    goal = max(0.0, min(1.0, fraction)) * sum(lengths)
    for a, c, step in zip(points, points[1:], lengths):
        if goal <= step:
            return a + (c - a) * (goal / max(step, 1e-9))
        goal -= step
    return points[-1]


LETTERING_SIZES = {}


def ink_box(picture_file):
    """Where a lettered picture's words are (left, top, right, bottom, fractions from its top left): lettering-sizes.json,
    written by paint_checkout_pictures.py."""
    if not LETTERING_SIZES:
        import json
        with open(os.path.join(TEXTURES, 'lettering-sizes.json')) as handle:
            LETTERING_SIZES.update(json.load(handle)['pictures'])
    return LETTERING_SIZES[picture_file]['ink_box']


def face_grid(name, rows, material, u_range, v_range, collection_name, offset=0.0, columns=16, lines=6):
    """A curved face through rows of points (bottom to top, each row left to right as seen from the front), cut to the part
    of the picture between u_range and v_range (u across by length, v up by the rows' spacing), wearing that part of the
    picture; moved `offset` metres toward the front (-y side of the face)."""
    middles = [sum((Vector(p) for p in row), Vector()) / len(row) for row in rows]
    spacing = [0.0]
    for a, c in zip(middles, middles[1:]):
        spacing.append(spacing[-1] + (c - a).length)

    def point(u, v):
        goal = v * spacing[-1]
        for k in range(len(rows) - 1):
            if goal <= spacing[k + 1] or k == len(rows) - 2:
                t = (goal - spacing[k]) / max(spacing[k + 1] - spacing[k], 1e-9)
                low, high = point_along(rows[k], u), point_along(rows[k + 1], u)
                return low + (high - low) * t
        return point_along(rows[-1], u)

    (u0, u1), (v0, v1) = u_range, v_range
    grid = [[point(u0 + (u1 - u0) * i / columns, v0 + (v1 - v0) * j / lines) for i in range(columns + 1)] for j in range(lines + 1)]
    across = grid[lines // 2][-1] - grid[lines // 2][0]
    up = grid[-1][columns // 2] - grid[0][columns // 2]
    normal = across.cross(up).normalized()
    if normal.y > 0:
        normal = -normal
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    verts = [[bm.verts.new(p + normal * offset) for p in row] for row in grid]
    for j in range(lines):
        for i in range(columns):
            face = bm.faces.new([verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]])
            face.smooth = True
            for loop_, (jj, ii) in zip(face.loops, ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i))):
                loop_[uv_layer].uv = (u0 + (u1 - u0) * ii / columns, v0 + (v1 - v0) * jj / lines)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    part = bpy.data.objects.new(name, mesh)
    kit.collection(collection_name).objects.link(part)
    return part


def printed_face(name, rows, picture_file, parent, roughness=0.7, margin=0.03, collection_name='checkout'):
    """A printed face (a label, a wrapper, a bag's front) through rows of points: the whole picture as an ordinary
    surface ('NAME-print', painted like the rest of the set), and over it, a hair in front, just the words with a small
    margin round them as their own lettered surface ('NAME-lettering' in the signs collection, material
    'PICTURE-lettering'), so the shot checker and the film treat exactly the words as the lettering."""
    stem = picture_file.rsplit('.', 1)[0]
    whole = face_grid(f'{name}-print', rows, picture(f'{stem}-print', picture_file, roughness=roughness), (0.0, 1.0), (0.0, 1.0), collection_name,
                      offset=0.0)
    whole.parent = parent
    left, top, right, bottom = ink_box(picture_file)
    words = face_grid(f'{name}-lettering', rows, picture(f'{stem}-lettering', picture_file, roughness=roughness),
                      (max(0.0, left - margin), min(1.0, right + margin)), (max(0.0, 1 - bottom - margin * 2), min(1.0, 1 - top + margin * 2)),
                      'signs', offset=0.0006)
    words.parent = parent
    return whole, words


def ring_points(half_x, half_y, roundness, z, count, start_degrees, end_degrees):
    """Points on a rounded square (a superellipse) at height z, from one angle to another (degrees, counterclockwise
    seen from above; 0 is +x, 90 is +y, 270 is -y, the front)."""
    points = []
    for i in range(count + 1):
        angle = math.radians(start_degrees + (end_degrees - start_degrees) * i / count)
        c, s_ = math.cos(angle), math.sin(angle)
        points.append((half_x * math.copysign(abs(c) ** (2 / roundness), c), half_y * math.copysign(abs(s_) ** (2 / roundness), s_), z))
    return points


def label_quad(name, corners, material, collection_name='signs', parent=None):
    """One lettered face as its own object: corners bottom left, bottom right, top right, top left as seen from the
    front, wearing the whole picture."""
    builder = kit.MeshBuilder()
    builder.quad(corners, material, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    part = builder.finish(name, collection_name=collection_name)
    if parent is not None:
        part.parent = parent
    return part


def rounded_square_ring(half, roundness, z, count=32):
    """Points round a rounded square (a superellipse |x|^n + |y|^n = 1, n = roundness), half its width across."""
    points = []
    for i in range(count):
        angle = 2 * math.pi * i / count - math.pi / 2          # the first point faces -y (the front)
        c, s = math.cos(angle), math.sin(angle)
        x = half * math.copysign(abs(c) ** (2 / roundness), c)
        y = half * math.copysign(abs(s) ** (2 / roundness), s)
        points.append((x, y, z))
    return points


def rings_mesh(name, rings, material, collection_name='checkout', cap_bottom=True, cap_top=True, uv_from_arc=False, smooth=True):
    """A shape from rings of points (bottom to top), each ring the same number of points. uv_from_arc: picture
    coordinates run round the rings by length (u, 0 at the ring's first point minus half the round) and up by ring
    (v 0 at the first ring, 1 at the last), for a label wrapped round a bottle."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    count = len(rings[0])
    verts = [[bm.verts.new(p) for p in ring] for ring in rings]
    faces = []
    perimeter = sum((Vector(rings[0][(i + 1) % count]) - Vector(rings[0][i])).length for i in range(count))
    arc = [0.0]
    for i in range(count):
        arc.append(arc[-1] + (Vector(rings[0][(i + 1) % count]) - Vector(rings[0][i])).length)
    for k in range(len(rings) - 1):
        for i in range(count):
            j = (i + 1) % count
            face = bm.faces.new([verts[k][i], verts[k][j], verts[k + 1][j], verts[k + 1][i]])
            face.smooth = smooth
            for loop_, (ring_index, point_index, wrap) in zip(face.loops, ((k, i, 0), (k, j, 1 if j == 0 else 0), (k + 1, j, 1 if j == 0 else 0), (k + 1, i, 0))):
                if uv_from_arc:
                    u = (arc[point_index] + (perimeter if wrap else 0)) / perimeter + 0.5
                    v = ring_index / (len(rings) - 1)
                else:
                    p = rings[ring_index][point_index]
                    u, v = (p[0] + p[1]) * 4, p[2] * 4
                loop_[uv_layer].uv = (u, v)
            faces.append(face)
    if cap_bottom:
        bm.faces.new(list(reversed(verts[0])))
    if cap_top:
        bm.faces.new(verts[-1])
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    part = bpy.data.objects.new(name, mesh)
    kit.collection(collection_name).objects.link(part)
    return part


# ---------------------------------------------------------------------------------------------- the counter

def counter(name, x_left, x_right, y_start, y_end, with_belt=True, ledge=None, collection_name='checkout'):
    """A checkout counter: laminate panels on a dark kick plate, a wooden nosing along the shoppers' side, a dark grey
    top; with_belt: the black belt sunk in its top between steel rails, a steel roller at each end, and the scanner's dark
    glass. ledge (y from, y to, x): the counter is wider on the shoppers' side there, out to x (the packing ledge past the
    belt's end, where the newspaper stand and the card terminal stand). Returns the counter object (and the belt's)."""
    b = kit.MeshBuilder()
    top_material = picture('counter-top', 'counter-laminate.jpg', tile=0.8, tint=(0.30, 0.30, 0.30), roughness=0.7)
    if ledge:
        ledge_from, ledge_to, ledge_x = ledge
        b.box((x_right - 0.02, ledge_from + 0.02, 0.0), (ledge_x - 0.02, ledge_to - 0.02, 0.10), kick_plate())
        b.box((x_right, ledge_from, 0.10), (ledge_x, ledge_to, COUNTER_TOP - 0.03), laminate())
        b.box((x_right, ledge_from, COUNTER_TOP - 0.03), (ledge_x, ledge_to, COUNTER_TOP), top_material)
        b.box((ledge_x - 0.005, ledge_from, COUNTER_TOP - 0.05), (ledge_x + 0.02, ledge_to, COUNTER_TOP + 0.004), wood())
        for y in (ledge_from, ledge_to):
            b.box((x_right, y - 0.012, COUNTER_TOP - 0.05), (ledge_x + 0.02, y + 0.012, COUNTER_TOP + 0.004), wood())
    b.box((x_left + 0.02, y_start + 0.02, 0.0), (x_right - 0.02, y_end - 0.02, 0.10), kick_plate())
    b.box((x_left, y_start, 0.10), (x_right, y_end, COUNTER_TOP - 0.03), laminate())
    # the top, in pieces round the belt's well
    if with_belt:
        b.box((x_left, y_start, COUNTER_TOP - 0.03), (BELT_LEFT - 0.04, y_end, COUNTER_TOP), top_material)
        b.box((BELT_RIGHT + 0.04, y_start, COUNTER_TOP - 0.03), (x_right, y_end, COUNTER_TOP), top_material)
        b.box((BELT_LEFT - 0.04, y_start, COUNTER_TOP - 0.03), (BELT_RIGHT + 0.04, BELT_START - 0.03, COUNTER_TOP), top_material)
        b.box((BELT_LEFT - 0.04, BELT_END + 0.05, COUNTER_TOP - 0.03), (BELT_RIGHT + 0.04, SCANNER_Y[0], COUNTER_TOP), top_material)
        b.box((BELT_LEFT - 0.04, SCANNER_Y[1], COUNTER_TOP - 0.03), (BELT_RIGHT + 0.04, y_end, COUNTER_TOP), top_material)
        # the belt's well floor, under the rubber
        b.box((BELT_LEFT - 0.04, BELT_START - 0.03, COUNTER_TOP - 0.08), (BELT_RIGHT + 0.04, BELT_END + 0.05, COUNTER_TOP - 0.06), kick_plate())
    else:
        b.box((x_left, y_start, COUNTER_TOP - 0.03), (x_right, y_end, COUNTER_TOP), top_material)
    # the wooden nosing along the shoppers' side and round the loading end
    b.box((x_right - 0.005, y_start, COUNTER_TOP - 0.05), (x_right + 0.02, y_end, COUNTER_TOP + 0.004), wood())
    b.box((x_left, y_start - 0.02, COUNTER_TOP - 0.05), (x_right + 0.02, y_start + 0.005, COUNTER_TOP + 0.004), wood())
    # a steel strip along the panels' foot, where trolleys knock
    b.box((x_right, y_start + 0.05, 0.10), (x_right + 0.006, y_end - 0.05, 0.16), steel())
    part = finish(b, name, collection_name)
    if not with_belt:
        return part, None
    # the belt: black ribbed rubber (its picture runs along the belt), sunk between two steel rails
    belt = kit.MeshBuilder()
    rubber = picture('belt-rubber', 'belt-rubber.jpg', tile=0.0, roughness=0.32)
    length = BELT_END - BELT_START
    belt.quad([(BELT_LEFT, BELT_START, BELT_TOP), (BELT_RIGHT, BELT_START, BELT_TOP), (BELT_RIGHT, BELT_END, BELT_TOP), (BELT_LEFT, BELT_END, BELT_TOP)],
              rubber, uvs=[(0, 0), (1, 0), (1, length), (0, length)])
    # its ends wrap round the rollers
    for y, sign_ in ((BELT_START, -1), (BELT_END, 1)):
        belt.rod((BELT_LEFT, y + sign_ * 0.012, BELT_TOP - 0.012), (BELT_RIGHT, y + sign_ * 0.012, BELT_TOP - 0.012), 0.013, rubber, sides=10)
        belt.rod((BELT_LEFT - 0.03, y + sign_ * 0.035, COUNTER_TOP - 0.004), (BELT_RIGHT + 0.03, y + sign_ * 0.035, COUNTER_TOP - 0.004), 0.008, steel(), sides=10)
    for x0, x1 in ((BELT_LEFT - 0.04, BELT_LEFT), (BELT_RIGHT, BELT_RIGHT + 0.04)):
        belt.box((x0, BELT_START - 0.03, COUNTER_TOP - 0.06), (x1, BELT_END + 0.05, RAIL_TOP), steel())
        belt.box((x0 - 0.002, BELT_START - 0.03, RAIL_TOP), (x1 + 0.002, BELT_END + 0.05, RAIL_TOP + 0.004), steel())
    belt_part = finish(belt, f'{name}-belt', collection_name)
    # the scanner's glass, dark, flush in the top
    glass = kit.MeshBuilder()
    glass.box((BELT_LEFT - 0.04, SCANNER_Y[0], COUNTER_TOP - 0.03), (BELT_RIGHT + 0.04, SCANNER_Y[1], COUNTER_TOP - 0.002),
              plain('scanner-glass', (0.02, 0.022, 0.025), roughness=0.08, metallic=0.0))
    glass.box((BELT_LEFT - 0.04, SCANNER_Y[0] - 0.01, COUNTER_TOP - 0.002), (BELT_RIGHT + 0.04, SCANNER_Y[0], COUNTER_TOP + 0.002), steel())
    glass.box((BELT_LEFT - 0.04, SCANNER_Y[1], COUNTER_TOP - 0.002), (BELT_RIGHT + 0.04, SCANNER_Y[1] + 0.01, COUNTER_TOP + 0.002), steel())
    finish(glass, f'{name}-scanner', collection_name)
    return part, belt_part


# ---------------------------------------------------------------------------------------------- the basket and what is in it

BASKET = {'top': (0.46, 0.32), 'base': (0.40, 0.26), 'height': 0.22}


def wire_basket(name, collection_name='checkout'):
    """A grey wire shopping basket, its base centred on its origin: a thick rim, four rounds of wire, upright wires every
    22 mm, a base grid, two runners under it, and two handles folded down outside its long sides with grey plastic
    grips."""
    b = kit.MeshBuilder()
    wire = wire_grey()
    (top_x, top_y), (base_x, base_y), height = BASKET['top'], BASKET['base'], BASKET['height']

    def size_at(z):
        f = z / height
        return (base_x + (top_x - base_x) * f) / 2, (base_y + (top_y - base_y) * f) / 2

    lift = 0.012                       # the base grid sits on the runners
    for z, radius in ((lift, 0.0032), (0.06, 0.0017), (0.11, 0.0017), (0.16, 0.0017), (height - 0.012, 0.0019), (height, 0.0042)):
        hx, hy = size_at(z)
        loop(b, rounded_rectangle(hx, hy, z, 0.03, steps=3), radius, wire)
    # the upright wires, every 22 mm round the sides
    bottom = rounded_rectangle(*size_at(lift), lift, 0.03, steps=3)
    top = rounded_rectangle(*size_at(height), height, 0.03, steps=3)

    def along(points, fraction):
        lengths = [(Vector(points[(i + 1) % len(points)]) - Vector(points[i])).length for i in range(len(points))]
        total = sum(lengths)
        goal = fraction * total
        for i, step in enumerate(lengths):
            if goal <= step:
                a, c = Vector(points[i]), Vector(points[(i + 1) % len(points)])
                return a + (c - a) * (goal / max(step, 1e-9))
            goal -= step
        return Vector(points[0])

    perimeter = sum((Vector(bottom[(i + 1) % len(bottom)]) - Vector(bottom[i])).length for i in range(len(bottom)))
    count = int(perimeter / 0.022)
    for k in range(count):
        f = k / count
        b.rod(tuple(along(bottom, f)), tuple(along(top, f)), 0.0015, wire, sides=5)
    # the base grid
    hx, hy = size_at(lift)
    for i in range(1, int(2 * hx / 0.025)):
        x = -hx + i * 0.025
        b.rod((x, -hy, lift), (x, hy, lift), 0.0015, wire, sides=5)
    for i in range(1, int(2 * hy / 0.025)):
        y = -hy + i * 0.025
        b.rod((-hx, y, lift), (hx, y, lift), 0.0015, wire, sides=5)
    # two runners under the base
    for y in (-hy + 0.04, hy - 0.04):
        b.rod((-hx + 0.03, y, 0.004), (hx - 0.03, y, 0.004), 0.004, wire, sides=6)
        for x in (-hx + 0.03, hx - 0.03):
            b.rod((x, y, 0.004), (x * 1.04, y, lift), 0.004, wire, sides=6)
    # the handles, folded down outside each long side: pivots near the short ends at the rim, a grip in the middle
    rim_x, rim_y = size_at(height)
    grip = plain('basket-grip', (0.22, 0.225, 0.23), roughness=0.55)
    for side in (-1, 1):
        y_out = side * (rim_y + 0.018)
        pivot_l, pivot_r = (-rim_x + 0.06, side * rim_y, height - 0.01), (rim_x - 0.06, side * rim_y, height - 0.01)
        low_l, low_r = (-0.075, y_out, height - 0.075), (0.075, y_out, height - 0.075)
        b.rod(pivot_l, (-rim_x + 0.06, y_out, height - 0.03), 0.0032, wire, sides=6)
        b.rod((-rim_x + 0.06, y_out, height - 0.03), low_l, 0.0032, wire, sides=6)
        b.rod(low_l, low_r, 0.0032, wire, sides=6)
        b.rod(low_r, (rim_x - 0.06, y_out, height - 0.03), 0.0032, wire, sides=6)
        b.rod((rim_x - 0.06, y_out, height - 0.03), pivot_r, 0.0032, wire, sides=6)
        b.rod((-0.06, y_out, height - 0.075), (0.06, y_out, height - 0.075), 0.011, grip, sides=10)
    return finish(b, name, collection_name)


def bread_loaf(name, collection_name='checkout'):
    """A loaf in a white paper bag standing on its end: a soft rounded body (the loaf's shape under the paper, a little
    uneven), the bag's open end above it gathered and folded over into a ridge; BREAD printed on its front (its own
    lettered face, facing -y, following the bag's curve), above the basket's rim."""
    paper_ = plain('bread-bag-paper', (0.34, 0.33, 0.31), roughness=0.85, tile=0.3)
    half_w, half_d, loaf = 0.062, 0.058, 0.34
    # (height, across, depth, roundness): the bag's body round the loaf, then the gathered neck and the fold
    profile = [(0.0, 0.90, 0.90, 3.0), (0.012, 1.0, 1.0, 3.2), (0.10, 1.03, 1.02, 3.4), (0.20, 1.02, 1.0, 3.4), (loaf, 0.97, 0.95, 3.2),
               (loaf + 0.025, 0.86, 0.62, 2.6), (loaf + 0.05, 0.82, 0.32, 2.2), (loaf + 0.07, 0.78, 0.10, 2.0)]
    rings = []
    for k, (z, across, depth, roundness) in enumerate(profile):
        ring = rounded_square_ring(1.0, roundness, z, count=40)
        wobble = 0.004 * math.sin(k * 2.1)
        rings.append([(x * half_w * across + wobble, y * half_d * depth, z + (0.006 * math.sin(3 * x) if k == len(profile) - 1 else 0.0))
                      for x, y, _ in ring])
    part = rings_mesh(name, rings, paper_, collection_name, cap_bottom=True, cap_top=True)
    # the printed front, following the bag's front curve from 0.015 m up to the top of the loaf (BREAD near its top)
    rows = [ring_points(half_w * 1.035, half_d * 1.025, 3.4, z, 24, 205, 335) for z in (0.015, 0.10, 0.20, 0.27, loaf - 0.004)]
    printed_face(name, rows, 'bread-bag.png', part, roughness=0.85)
    return part


def milk_bottle(name, collection_name='checkout'):
    """A two-litre plastic milk bottle: a rounded square body, shoulders, a neck and a dark cap, a moulded handle at
    one back corner, and its printed sleeve (MILK, its own lettered surface) high on the body, centred on its front
    (-y)."""
    body_material = plain('milk-bottle-plastic', (0.56, 0.57, 0.56), roughness=0.4, tile=0.3)
    half = 0.056
    profile = [(0.0, 0.70, 4.0), (0.004, 0.97, 4.0), (0.012, 1.0, 4.5), (0.245, 1.0, 4.5), (0.272, 0.86, 3.6), (0.292, 0.52, 2.6),
               (0.302, 0.30, 2.0), (0.315, 0.29, 2.0)]
    rings = [rounded_square_ring(half * scale, roundness, z, count=32) for z, scale, roundness in profile]
    body = rings_mesh(name, rings, body_material, collection_name)
    cap_rings = [rounded_square_ring(0.019, 2.0, z, count=20) for z in (0.312, 0.332)]
    cap = rings_mesh(f'{name}-cap', cap_rings, plain('milk-cap', (0.10, 0.13, 0.20), roughness=0.4), collection_name)
    cap.parent = body
    # the handle: a moulded loop at the back right corner
    b = kit.MeshBuilder()
    for a, c in (((0.04, 0.045, 0.27), (0.058, 0.062, 0.25)), ((0.058, 0.062, 0.25), (0.062, 0.066, 0.18)), ((0.062, 0.066, 0.18), (0.045, 0.05, 0.16))):
        b.rod(a, c, 0.009, body_material, sides=8)
    handle = finish(b, f'{name}-handle', collection_name)
    handle.parent = body
    # the sleeve, a hair outside the body, from 0.15 to 0.24 m up (high, so it shows over the basket's rim), wrapped from the front
    rows = [ring_points(half * 1.012, half * 1.012, 4.5, z, 64, 90, 450) for z in (0.15, 0.18, 0.21, 0.24)]
    printed_face(name, rows, 'milk-label.png', body, roughness=0.4)
    return body


def butter_block(name, collection_name='checkout'):
    """A block of butter in a parchment wrapper with folded ends, lying flat; BUTTER printed on its long front face (-y,
    its own lettered face)."""
    b = kit.MeshBuilder()
    wrapper = plain('butter-wrapper-paper', (0.74, 0.70, 0.58), roughness=0.7, tile=0.2)
    length, width, height = 0.125, 0.064, 0.052
    b.box((-length / 2, -width / 2, 0), (length / 2, width / 2, height), wrapper)
    # the wrapper's folded ends: a flap a little proud of each end
    for side in (-1, 1):
        x0, x1 = sorted((side * length / 2, side * (length / 2 + 0.0015)))
        b.box((x0, -width / 2 + 0.004, 0.006), (x1, width / 2 - 0.004, height - 0.006), wrapper)
    part = finish(b, name, collection_name)
    y = -width / 2 - 0.0008
    printed_face(name, [[(-length / 2 + 0.001, y, 0.001), (length / 2 - 0.001, y, 0.001)], [(-length / 2 + 0.001, y, height - 0.001), (length / 2 - 0.001, y, height - 0.001)]],
                 'butter-wrapper.png', part)
    return part


def cheese_block(name, collection_name='checkout'):
    """A block of mild cheese (pale, waxy) lying flat, its cream label CHEESE on its long front face (-y, its own lettered
    face)."""
    b = kit.MeshBuilder()
    cheese = plain('cheese', (0.78, 0.58, 0.30), roughness=0.4, tile=0.2)
    length, width, height = 0.20, 0.095, 0.05
    b.box((-length / 2, -width / 2, 0), (length / 2, width / 2, height), cheese)
    part = finish(b, name, collection_name)
    lx = 0.06
    y = -width / 2 - 0.0008
    printed_face(name, [[(-lx, y, 0.0), (lx, y, 0.0)], [(-lx, y, height), (lx, y, height)]], 'cheese-label.png', part, roughness=0.6)
    return part


def divider_bar(name, length=0.46, collection_name='checkout'):
    """The grey plastic divider bar that lies across the belt between one shopper's things and the next: a long
    three-sided bar."""
    b = kit.MeshBuilder()
    outline = [(-0.02, 0.0), (0.02, 0.0), (0.003, 0.036), (-0.003, 0.036)]
    b.prism(outline, -length / 2, length / 2, plain('divider-plastic', (0.13, 0.135, 0.14), roughness=0.45), axis='x')
    return finish(b, name, collection_name)


# ---------------------------------------------------------------------------------------------- the newspaper bill

BILL_WIDTH, BILL_HEIGHT = 0.62, 0.72


def bill_stand(name, collection_name='checkout'):
    """A wire stand for newspapers that stands on the counter: a wire tray with a stack of folded papers, two upright
    wires, and above them a wire frame holding the day's bill (the poster: its own lettered surface, facing -y). Its
    origin is the middle of its foot on the counter top; the bill's bottom edge is BILL_BOTTOM above it."""
    b = kit.MeshBuilder()
    wire = plain('stand-wire', (0.32, 0.33, 0.34), roughness=0.35, metallic=0.8)
    half_w = BILL_WIDTH / 2 + 0.012
    bottom, top = BILL_BOTTOM, BILL_BOTTOM + BILL_HEIGHT
    # the foot: a wire tray 0.26 deep, its front lip low
    tray = [(-half_w, -0.12, 0.004), (half_w, -0.12, 0.004), (half_w, 0.12, 0.004), (-half_w, 0.12, 0.004)]
    loop(b, tray, 0.004, wire)
    loop(b, [(x, y, 0.05) for x, y, _ in tray], 0.003, wire)
    for x, y, _ in tray:
        b.rod((x, y, 0.004), (x, y, 0.05), 0.003, wire)
    for i in range(1, 8):
        x = -half_w + i * 2 * half_w / 8
        b.rod((x, -0.12, 0.004), (x, 0.12, 0.004), 0.0022, wire, sides=5)
    # the uprights behind the papers, up to the frame's top, and the frame round the bill
    for x in (-half_w, half_w):
        b.rod((x, 0.10, 0.004), (x, 0.02, top + 0.012), 0.0045, wire)
    frame = [(-half_w, 0.02 - 0.003, bottom - 0.012), (half_w, 0.02 - 0.003, bottom - 0.012), (half_w, 0.02 - 0.003, top + 0.012), (-half_w, 0.02 - 0.003, top + 0.012)]
    loop(b, frame, 0.0035, wire)
    b.rod((-half_w, 0.032, (bottom + top) / 2), (half_w, 0.032, (bottom + top) / 2), 0.0025, wire)     # behind the backing board
    # the backing board behind the bill
    b.box((-BILL_WIDTH / 2, 0.022, bottom), (BILL_WIDTH / 2, 0.028, top), plain('bill-backing', (0.18, 0.18, 0.19), roughness=0.7))
    # two clips on the top bar
    for x in (-0.18, 0.18):
        b.box((x - 0.012, 0.010, top - 0.02), (x + 0.012, 0.024, top + 0.016), wire)
    part = finish(b, name, collection_name)
    # the papers: a stack of folded papers in the tray, the top one's front page up, leaning back a little
    papers = kit.MeshBuilder()
    newsprint_edge = plain('newsprint-edge', (0.70, 0.69, 0.66), roughness=0.9, tile=0.3)
    papers.box((-0.15, -0.10, 0.006), (0.15, 0.10, 0.045), newsprint_edge)
    papers.quad([(-0.15, -0.10, 0.0455), (0.15, -0.10, 0.0455), (0.15, 0.10, 0.0455), (-0.15, 0.10, 0.0455)],
                picture('newsprint', 'newsprint.jpg', roughness=0.9), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    stack = finish(papers, f'{name}-papers', collection_name)
    stack.parent = part
    # the bill: the poster, just in front of the backing board
    poster = label_quad(f'{name}-bill-lettering', [(-BILL_WIDTH / 2, 0.019, bottom), (BILL_WIDTH / 2, 0.019, bottom), (BILL_WIDTH / 2, 0.019, top),
                                                   (-BILL_WIDTH / 2, 0.019, top)], picture('bill-lettering', 'bill.png', roughness=0.8))
    poster.parent = part
    return part, poster


BILL_BOTTOM = 0.24         # the bill's bottom edge above the counter top (the tray of papers below it)


# ---------------------------------------------------------------------------------------------- the card terminal and the till

def card_terminal(name, collection_name='checkout'):
    """The card terminal on its stand: a steel post from a clamp on the counter's edge, a swivel, and the terminal (a dark
    grey plastic body with a dark screen and blank keys) tilted up toward the shopper who stands beside it (+x), so from
    the queue its keypad is turned away. Origin: the post's foot on the counter top."""
    b = kit.MeshBuilder()
    b.box((-0.03, -0.04, -0.004), (0.03, 0.04, 0.012), dark_steel())
    b.rod((0, 0, 0.012), (0, 0, 0.21), 0.012, dark_steel(), sides=10)
    b.rod((0, 0, 0.21), (0.02, 0, 0.235), 0.015, dark_steel(), sides=10)
    post = finish(b, name, collection_name)
    head = kit.MeshBuilder()
    body = plain('terminal-plastic', (0.07, 0.072, 0.078), roughness=0.5)
    head.box((-0.022, -0.042, -0.095), (0.0, 0.042, 0.095), body)
    head.box((0.0, -0.034, 0.005), (0.002, 0.034, 0.075), plain('terminal-screen', (0.012, 0.014, 0.018), roughness=0.1))
    for row in range(4):
        for column in range(3):
            y = -0.024 + column * 0.024
            z = -0.08 + row * 0.019
            head.box((0.0, y - 0.009, z - 0.007), (0.004, y + 0.009, z + 0.007), plain('terminal-key', (0.16, 0.165, 0.17), roughness=0.6))
    terminal = finish(head, f'{name}-head', collection_name)
    terminal.parent = post
    terminal.location = (0.035, 0, 0.27)
    terminal.rotation_euler = Euler((0, math.radians(-35), 0))     # its face tipped up toward +x
    return post


def till(name, collection_name='checkout'):
    """The operator's till on the counter's operator edge: a dark screen on a short post turned to the operator (-x, away
    from the queue), a small shoppers' screen on the post's other side, both dark. Origin: the post's foot on the counter
    top. (The cash drawer is in the counter, on the operator's side, out of sight.)"""
    b = kit.MeshBuilder()
    b.box((-0.06, -0.08, 0.0), (0.06, 0.08, 0.02), dark_steel())
    b.rod((0.0, 0.0, 0.02), (0.0, 0.0, 0.30), 0.018, dark_steel(), sides=10)
    b.box((-0.05, -0.19, 0.24), (-0.01, 0.19, 0.52), dark_plastic())          # the operator's screen, facing -x
    b.box((-0.052, -0.17, 0.26), (-0.05, 0.17, 0.50), plain('till-screen', (0.010, 0.012, 0.016), roughness=0.08))
    b.box((0.02, -0.08, 0.20), (0.05, 0.08, 0.32), dark_plastic())            # the shoppers' small screen, facing +x
    b.box((0.05, -0.07, 0.21), (0.052, 0.07, 0.31), plain('till-screen', (0.010, 0.012, 0.016), roughness=0.08))
    return finish(b, name, collection_name)


def operator_stool(name, collection_name='checkout'):
    """The operator's empty stool, pushed back from the till."""
    b = kit.MeshBuilder()
    b.lathe([(0.20, 0.0), (0.20, 0.02), (0.03, 0.04), (0.025, 0.60), (0.17, 0.62), (0.17, 0.68), (0.0, 0.69)], dark_steel(), sides=16)
    b.lathe([(0.175, 0.64), (0.18, 0.70), (0.0, 0.715)], plain('stool-seat', (0.10, 0.10, 0.11), roughness=0.6), sides=16)
    return finish(b, name, collection_name)


# ---------------------------------------------------------------------------------------------- the bags, the sign

def pillow(name, width, height, fullness, material, collection_name='checkout', seed=0):
    """A soft cloth bag hanging flat: two panels (front -x, back +x) sewn at the edges, fuller toward the bottom, its
    top edge drawn in a little where the handles pull, with a slight sag; origin at the middle of its top edge."""
    import random
    rng = random.Random(seed)
    columns, rows = 9, 9
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    panels = []
    for side in (-1, 1):
        grid = []
        for r in range(rows + 1):
            v = r / rows                                   # 0 at the top, 1 at the bottom
            row = []
            for c in range(columns + 1):
                u = c / columns                            # 0 at -y, 1 at +y
                puff = math.sin(math.pi * u) * (math.sin(math.pi * min(1.0, v * 1.15)) ** 0.7) * (0.45 + 0.55 * v)
                x = side * fullness * puff + rng.uniform(-0.002, 0.002) * puff
                y = (u - 0.5) * width * (1 - 0.06 * (1 - v) * math.sin(math.pi * u) ** 0.5)
                z = -v * height - 0.012 * math.sin(math.pi * u) * v
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        panels.append(grid)
    for k, grid in enumerate(panels):
        for r in range(rows):
            for c in range(columns):
                quad = [grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]]
                face = bm.faces.new(quad if k == 1 else list(reversed(quad)))
                face.smooth = True
                for loop_ in face.loops:
                    p = loop_.vert.co
                    loop_[uv_layer].uv = (p.y / 0.25, p.z / 0.25)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    part = bpy.data.objects.new(name, mesh)
    kit.collection(collection_name).objects.link(part)
    return part


def bag_rack(name, length=1.8, bags=6, collection_name='checkout'):
    """A rack of reusable bags for sale along the shoppers' side of the lane: two steel uprights on feet, a top rail with
    hooks, and plain woven bags (no print) hanging from it by their handles, soft and a little full at the bottom, their
    fronts facing -x. Origin: the rack's near foot on the floor; it runs along +y."""
    b = kit.MeshBuilder()
    rail = 1.42
    for y in (0.0, length):
        b.box((-0.16, y - 0.02, 0.0), (0.16, y + 0.02, 0.025), dark_steel())
        b.rod((0, y, 0.025), (0, y, rail + 0.02), 0.014, dark_steel(), sides=8)
    b.rod((0, 0, rail), (0, length, rail), 0.011, steel(), sides=8)
    rack = finish(b, name, collection_name)
    shades = [(0.42, 0.40, 0.36), (0.30, 0.30, 0.30), (0.40, 0.37, 0.32), (0.24, 0.25, 0.26), (0.44, 0.42, 0.39), (0.34, 0.31, 0.28)]
    step = length / bags
    for i in range(bags):
        y = step * (i + 0.5)
        cloth = picture(f'bag-cloth-{i % len(shades)}', 'bag-canvas.jpg', tile=0.25, tint=shades[i % len(shades)], roughness=0.95)
        width, height = 0.37, 0.40
        top_z = rail - 0.17
        bag = pillow(f'{name}-bag-{i + 1}', width, height, 0.022 + 0.006 * (i % 2), cloth, collection_name, seed=i)
        bag.parent = rack
        bag.location = (-0.03, y, top_z)
        bag.rotation_euler = Euler((math.radians((i % 3 - 1) * 2.5), 0, math.radians((i % 3 - 1) * 5)))
        # its two handles: flat cloth straps from the bag's top corners up over the hook
        straps = kit.MeshBuilder()
        for side in (-1, 1):
            for face_x in (-0.006, 0.006):
                a = Vector((face_x, side * 0.10, 0.0))
                c = Vector((face_x * 0.3, side * 0.012, 0.165))
                widthwise = (c - a).normalized().cross(Vector((1, 0, 0))).normalized() * 0.013
                straps.quad([tuple(a - widthwise), tuple(a + widthwise), tuple(c + widthwise), tuple(c - widthwise)], cloth)
        handle = finish(straps, f'{name}-bag-{i + 1}-handles', collection_name)
        handle.parent = bag
        hook = kit.MeshBuilder()
        hook.rod((0, y, rail), (-0.04, y, rail - 0.01), 0.003, steel(), sides=5)
        hook.rod((-0.04, y, rail - 0.01), (-0.04, y, rail + 0.01), 0.003, steel(), sides=5)
        finish(hook, f'{name}-hook-{i + 1}', collection_name).parent = rack
    return rack


def hanging_sign(name, words_material, width=1.10, height=0.26, drop=0.55, collection_name='signs'):
    """A sign panel hung from the ceiling on two thin cables: the picture on both faces (front -y, back +y). Origin: the
    middle of the panel's top edge; the cables rise `drop` metres to the ceiling. Returns the panel and its cables (a
    separate object: place both at the same spot)."""
    b = kit.MeshBuilder()
    edge = plain('sign-edge', (0.18, 0.18, 0.19), roughness=0.5)
    b.box((-width / 2, -0.012, -height), (width / 2, 0.012, 0.0), edge)
    # a thin brushed aluminium trim round the panel's edge, both faces
    trim = plain('sign-trim', (0.62, 0.63, 0.64), roughness=0.35, metallic=0.85)
    for y0, y1 in ((-0.016, -0.012), (0.012, 0.016)):
        b.box((-width / 2, y0, -height), (width / 2, y1, -height + 0.012), trim)
        b.box((-width / 2, y0, -0.012), (width / 2, y1, 0.0), trim)
        b.box((-width / 2, y0, -height), (-width / 2 + 0.012, y1, 0.0), trim)
        b.box((width / 2 - 0.012, y0, -height), (width / 2, y1, 0.0), trim)
    panel = finish(b, name, 'checkout')
    # its two cables up to the ceiling: their own object, not hung under the panel (so the sign's outline, as the shot
    # checker measures it, is the panel alone); place it where the panel is
    cables = kit.MeshBuilder()
    for x in (-width / 2 + 0.08, width / 2 - 0.08):
        cables.rod((x, 0, 0.0), (x, 0, drop), 0.0015, steel(), sides=4)
    hangers = finish(cables, f'cables-of-{name}', 'checkout')
    front = label_quad(f'{name}-lettering', [(-width / 2 + 0.012, -0.0125, -height + 0.012), (width / 2 - 0.012, -0.0125, -height + 0.012),
                                             (width / 2 - 0.012, -0.0125, -0.012), (-width / 2 + 0.012, -0.0125, -0.012)], words_material, collection_name)
    front.parent = panel
    back = label_quad(f'{name}-back-lettering', [(width / 2 - 0.012, 0.0125, -height + 0.012), (-width / 2 + 0.012, 0.0125, -height + 0.012),
                                                 (-width / 2 + 0.012, 0.0125, -0.012), (width / 2 - 0.012, 0.0125, -0.012)], words_material, collection_name)
    back.parent = panel
    return panel, hangers


# ---------------------------------------------------------------------------------------------- across the road

def petrol_station(name, collection_name='outside'):
    """A small petrol station seen across the road at night: a flat canopy on four posts with a grey fascia lettered
    PETROL · DIESEL on its front (no brand), two islands of plain pumps (no figures), a low kiosk behind, and its tall
    price board turned edge-on to the shop (so no figures can show). Origin: the middle of the canopy's front edge on
    the ground; the canopy runs +x across and +y away."""
    b = kit.MeshBuilder()
    canopy_w, canopy_d, under, fascia = 10.0, 8.0, 4.6, 0.9
    white = plain('canopy-white', (0.26, 0.27, 0.28), roughness=0.6, tile=2.0)
    grey = plain('canopy-grey', (0.22, 0.225, 0.23), roughness=0.6, tile=2.0)
    b.box((-canopy_w / 2, 0.0, under), (canopy_w / 2, canopy_d, under + fascia), grey)
    for x in (-canopy_w / 2 + 2.0, canopy_w / 2 - 2.0):
        for y in (2.0, canopy_d - 2.0):
            b.box((x - 0.18, y - 0.18, 0.0), (x + 0.18, y + 0.18, under), white)
    # the islands and pumps
    for x in (-2.5, 2.5):
        b.box((x - 0.5, 1.8, 0.0), (x + 0.5, canopy_d - 1.8, 0.15), white)
        for y in (3.0, 5.0):
            b.box((x - 0.30, y - 0.20, 0.15), (x + 0.30, y + 0.20, 1.85), white)
            b.box((x - 0.31, y - 0.12, 1.0), (x + 0.31, y + 0.12, 1.5), grey)
    # the kiosk behind
    b.box((-4.0, canopy_d + 3.0, 0.0), (4.0, canopy_d + 8.0, 3.2), plain('kiosk-wall', (0.30, 0.30, 0.31), roughness=0.8, tile=2.0))
    b.box((-3.0, canopy_d + 2.98, 0.4), (3.0, canopy_d + 3.0, 2.4), plain('kiosk-window', (0.20, 0.18, 0.15), glow=((1.0, 0.80, 0.58), 0.10)))
    station = finish(b, name, collection_name)
    # the canopy's lit underside (a panel glowing a little)
    under_side = kit.MeshBuilder()
    under_side.quad([(-canopy_w / 2, canopy_d, under - 0.01), (canopy_w / 2, canopy_d, under - 0.01), (canopy_w / 2, 0.0, under - 0.01), (-canopy_w / 2, 0.0, under - 0.01)],
                    plain('canopy-lights', (0.4, 0.42, 0.45), glow=((0.92, 0.95, 1.0), 0.22)))
    lit = finish(under_side, f'{name}-underside', collection_name)
    lit.parent = station
    # the fascia's lettering on the front face (-y)
    fascia_material = picture('petrol-fascia-lettering', 'petrol-fascia.png', roughness=0.6, glow=0.12)
    front = label_quad(f'{name}-fascia-lettering', [(-4.5, -0.012, under + 0.0), (4.5, -0.012, under + 0.0), (4.5, -0.012, under + fascia), (-4.5, -0.012, under + fascia)],
                       fascia_material, 'signs')
    front.parent = station
    # the price board on its pylon, turned edge-on to the shop: its faces look along x
    pylon = kit.MeshBuilder()
    pylon.box((-0.12, -0.9, 0.0), (0.12, 0.9, 6.0), grey)
    pylon.box((-0.13, -0.8, 2.6), (0.13, 0.8, 5.6), plain('price-board-edge', (0.12, 0.12, 0.13), roughness=0.6))
    board = finish(pylon, f'{name}-price-board', collection_name)
    board.parent = station
    board.location = (canopy_w / 2 + 3.5, -1.5, 0.0)
    return station
