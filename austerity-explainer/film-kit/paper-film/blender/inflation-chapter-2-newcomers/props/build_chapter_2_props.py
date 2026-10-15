# What this does: builds chapter 2's props that no free model covers, in Blender by script, and writes
# each as its own .glb with its line in its own library's index.json
# (assets/models/inflation-chapter-2-newcomers/props). So far the Works' small props ("34 Plan - chapter 2
# full redesign", part 1 A and part 3):
#   gate-board-no-1, gate-board-no-2   the works' gate boards, "No. 1" and "No. 2" in cream sign-writer's
#                                      lettering on near-black planks, with a painted moulding
#   bank-hanging-sign                  "BANK" in gilt on both faces of a board hung from a wrought-iron
#                                      wall bracket
#   bank-brass-plate                   "BANK" engraved on a brass door plate with four screws
#   steel-drum-petrol, steel-drum-diesel   dull grey-black steel drums with rolling hoops, stencilled
#                                      "PETROL" and "DIESEL" in off-white
#   crate-this-way-up                  a nailed packing crate of deal boards and battens, stencilled
#                                      "THIS WAY UP" under two arrows on both long sides
#   chain-and-padlock                  a loop of iron chain (to go round the two gates' meeting bars),
#                                      a short hanging end, and an old iron padlock
#   lunch-tin                          a tinplate lunch tin with its lid on
#   jacket-and-cap-on-nail             a wool work jacket hung by its collar on a nail, a tweed cap over it
#   tin-mug                            a plain tin mug with a rolled rim and a handle
#   wages-envelope                     a brown pay envelope printed "WAGES", lying flat
# The wooden-chest model in the pit village library was not reused for the crate: it is a lidded chest
# with iron handles, not a nailed packing crate.
#
# Every prop is built in real metres, stands on the ground (its lowest point at height 0, centred over
# the origin) and has one root empty named after the prop, like the pit village's. Lettering is on its
# own materials (listed in each index line as "lettering_materials"), so the film can keep it as its own
# surface: the painter garbles small print. Lettered faces face Blender -y (three.js +z), except the
# envelope's, which faces up. The only figures (digits) are the gate boards' "1" and "2".
#
# It reuses the pit village's prop kit (pit-village/props: prop_library.py, scripted_kit.py) and the
# colliery-board builder's plank board (build_scripted_props.py).
#
# Run (after download_poly_haven.py --choices chapter_2_choices.py and paint_chapter_2_pictures.py, which
# write into the scratch folder's downloads/ and pictures/):
#   blender -b --python build_chapter_2_props.py -- --scratch SCRATCH                 (all)
#   blender -b --python build_chapter_2_props.py -- --scratch SCRATCH tin-mug lunch-tin  (some)
#   (--library NAME_OR_FOLDER writes somewhere else; the default is chapter 2's own library)

import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'pit-village', 'props'))
import prop_library as library  # noqa: E402
import scripted_kit as kit  # noqa: E402
import build_scripted_props as pit_village  # noqa: E402   (its builders run only when it is run itself)

SCRIPTED = 'Built by script (paper-film/blender/inflation-chapter-2-newcomers/props/build_chapter_2_props.py) with Poly Haven CC0 surface textures'
LICENCE = ('Own work; textures CC0 1.0 (Poly Haven); lettering fonts: Ultra (Apache 2.0), Abril Fatface and Old Standard TT '
           '(SIL Open Font Licence), DejaVu Sans Bold (Bitstream Vera licence, free)')


# ------------------------------------------------------------------------------------ materials

def board_paint():
    """Near-black paint on the boards' mouldings and edges."""
    return kit.surface_material('board-black-paint', 'weathered_planks', 1.6, tint=(0.085, 0.082, 0.078), tint_strength=0.92, metallic=0.0)


def drum_steel():
    """Dull grey-black painted steel, worn, for the drums."""
    return kit.surface_material('drum-steel', 'rusty_metal_02', 0.8, tint=(0.085, 0.085, 0.09), tint_strength=0.9, metallic=0.45, roughness=0.62)


def deal_boards():
    """Sawn deal (pine) boards for the packing crate."""
    return kit.surface_material('crate-deal', 'raw_plank_wall', 1.2, metallic=0.0, roughness=0.8)


def tinplate():
    """Plain, even tinplate. (Poly Haven's metal_plate is a chequer plate, and its scratched steel came out
    blotchy at a mug's size, so this one is a single colour.)"""
    return kit.plain_material('tinplate', (0.5, 0.5, 0.51), roughness=0.42, metallic=0.85)


def jacket_wool():
    """Dark grey-brown wool cloth (the caban texture with its orange taken out)."""
    return kit.surface_material('jacket-wool', 'caban', 0.27, tint=(0.2, 0.18, 0.16), tint_strength=1.0, metallic=0.0, roughness=0.95)


def cap_tweed():
    return kit.surface_material('cap-tweed', 'poly_wool_herringbone', 0.27, tint=(0.27, 0.25, 0.22), tint_strength=0.9, metallic=0.0, roughness=0.95)


# ---------------------------------------------------------------------------------- shape helpers

def turned(name, profile, material, sides=40, at=(0, 0, 0)):
    """A turned shape (drum, mug): profile [(radius, height), ...] spun round the upright axis. A point
    with radius 0 becomes the centre of a flat end."""
    bm = bmesh.new()
    rings = []
    for radius, height in profile:
        if radius < 1e-6:
            rings.append([bm.verts.new((0, 0, height))])
        else:
            rings.append([bm.verts.new((radius * math.cos(2 * math.pi * i / sides), radius * math.sin(2 * math.pi * i / sides), height))
                          for i in range(sides)])
    for lower, upper in zip(rings, rings[1:]):
        if len(lower) == 1 and len(upper) == 1:
            continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(lower) == 1:
                bm.faces.new([lower[0], upper[i], upper[j]][::-1])
            elif len(upper) == 1:
                bm.faces.new([lower[i], lower[j], upper[0]])
            else:
                bm.faces.new([lower[i], lower[j], upper[j], upper[i]])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    part = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(part)
    part.location = at
    part.data.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    bpy.context.view_layer.update()
    kit.project_by_facing(part)
    return part


def wrapped_strip(name, radius, half_angle_degrees, bottom, top, material, segments=32):
    """A picture laid round a cylinder (a drum's stencil): a curved strip facing -y, centred on the
    front, its picture running left to right as seen from the front."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    columns = []
    for k in range(segments + 1):
        angle = math.radians(-half_angle_degrees + 2 * half_angle_degrees * k / segments)
        x, y = radius * math.sin(angle), -radius * math.cos(angle)
        columns.append((bm.verts.new((x, y, bottom)), bm.verts.new((x, y, top)), k / segments))
    for (low_a, high_a, u_a), (low_b, high_b, u_b) in zip(columns, columns[1:]):
        face = bm.faces.new([low_a, low_b, high_b, high_a])
        for loop, uv in zip(face.loops, [(u_a, 0), (u_b, 0), (u_b, 1), (u_a, 1)]):
            loop[uv_layer].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        if face.normal.y > 0: face.normal_flip()
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    part = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(part)
    part.data.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    return part


def flat_picture(name, width, height, centre, material, facing=-1):
    """A flat picture (a stencil), width along x and height along z, facing -y (facing=-1) or +y
    (facing=+1); seen from its own side it reads the right way round."""
    x, y, z = centre
    left, right = (x - width / 2, x + width / 2) if facing < 0 else (x + width / 2, x - width / 2)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    corners = [bm.verts.new((left, y, z - height / 2)), bm.verts.new((right, y, z - height / 2)),
               bm.verts.new((right, y, z + height / 2)), bm.verts.new((left, y, z + height / 2))]
    face = bm.faces.new(corners)
    for loop, uv in zip(face.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop[uv_layer].uv = uv
    face.normal_update()
    if face.normal.y * facing < 0: face.normal_flip()
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    part = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(part)
    part.data.materials.append(material)
    return part


def picture_on_faces(part, material, width, height, centre, both_sides=False):
    """Puts a picture material on a box's front face (and, with both_sides, its back face, laid the other
    way round so it reads from behind): the picture covers width (x) by height (z) about centre."""
    part.data.materials.append(material)
    index = len(part.data.materials) - 1
    bm = bmesh.new(); bm.from_mesh(part.data)
    uv_layer = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for face in bm.faces:
        front, back = face.normal.y < -0.9, face.normal.y > 0.9 and both_sides
        if not (front or back):
            continue
        face.material_index = index
        for loop in face.loops:
            point = part.matrix_world @ loop.vert.co
            u = (point.x - centre[0]) / width + 0.5
            loop[uv_layer].uv = (u if front else 1 - u, (point.z - centre[2]) / height + 0.5)
    bm.to_mesh(part.data); bm.free()


def ball(name, radius, at, material):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=radius)
    part = kit._object(name, bm, material, at, (0, 0, 0), 0, smooth=True)
    kit.project_by_facing(part, 0.2)
    return part


def bent_bar(name, points, radius, material, sides=10, radius_end=None, flatten=1.0, bend_plane=(0, 1, 0)):
    """One unbroken bar or tube bent through the given points (a scroll, a mug's handle, a shackle, a
    sleeve), its radius changing evenly to radius_end. flatten < 1 squashes it into a strap (thin across
    the bend). bend_plane: the direction square to the plane the bar bends in."""
    points = [Vector(p) for p in points]
    radius_end = radius if radius_end is None else radius_end
    across = Vector(bend_plane).normalized()
    bm = bmesh.new()
    rings = []
    for index, point in enumerate(points):
        tangent = (points[min(index + 1, len(points) - 1)] - points[max(index - 1, 0)]).normalized()
        side = across - tangent * across.dot(tangent)
        side = side.normalized() if side.length > 1e-6 else tangent.orthogonal().normalized()
        normal = tangent.cross(side).normalized()
        r = radius + (radius_end - radius) * index / (len(points) - 1)
        rings.append([bm.verts.new(point + normal * math.cos(2 * math.pi * k / sides) * r * flatten + side * math.sin(2 * math.pi * k / sides) * r)
                      for k in range(sides)])
    for lower, upper in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new([lower[k], lower[(k + 1) % sides], upper[(k + 1) % sides], upper[k]])
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    part = kit._object(name, bm, material, (0, 0, 0), (0, 0, 0), 0, smooth=True)
    kit.project_by_facing(part)
    return part


def rounded_slab(name, length, width, height, corner, bottom, material, corner_steps=6):
    """A box with rounded upright corners (a tin, its lid): length along x, width along y."""
    outline = []
    for cx, cy, start in ((length / 2 - corner, width / 2 - corner, 0), (-length / 2 + corner, width / 2 - corner, 90),
                          (-length / 2 + corner, -width / 2 + corner, 180), (length / 2 - corner, -width / 2 + corner, 270)):
        for step in range(corner_steps + 1):
            angle = math.radians(start + 90 * step / corner_steps)
            outline.append((cx + corner * math.cos(angle), cy + corner * math.sin(angle)))
    bm = bmesh.new()
    low = [bm.verts.new((x, y, bottom)) for x, y in outline]
    high = [bm.verts.new((x, y, bottom + height)) for x, y in outline]
    bm.faces.new(list(reversed(low))); bm.faces.new(high)
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new([low[i], low[j], high[j], high[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    part = kit._object(name, bm, material, (0, 0, 0), (0, 0, 0), 0.0015)
    kit.project_by_facing(part)
    return part


def loft(name, rings, material, close_top=True, close_bottom=True):
    """A surface through rings of points, each ring the same number of points, top ring first (the
    jacket's body): closed at the ends with a fan."""
    bm = bmesh.new()
    vertex_rings = [[bm.verts.new(point) for point in ring] for ring in rings]
    count = len(rings[0])
    for upper, lower in zip(vertex_rings, vertex_rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new([upper[i], upper[j], lower[j], lower[i]])
    for ring, close in ((vertex_rings[0], close_top), (vertex_rings[-1], close_bottom)):
        if close:
            centre = bm.verts.new(sum((v.co for v in ring), Vector()) / count)
            for i in range(count):
                bm.faces.new([ring[i], ring[(i + 1) % count], centre])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    part = kit._object(name, bm, material, (0, 0, 0), (0, 0, 0), 0, smooth=True)
    kit.project_by_facing(part)
    return part


def save(prop_name, description, extra):
    library.stand_on_ground(prop_name)
    return library.save_prop(prop_name, description, SCRIPTED, LICENCE, extra)


# ------------------------------------------------------------------------------- the gate boards

GATE_BOARD_WIDTH, GATE_BOARD_HEIGHT = 1.4, 0.6


def gate_board(words, prop_name, picture):
    """A works' gate board: four planks wearing the painted picture, a near-black moulding round the
    edge with coach bolts through its sides, two battens behind. Faces -y; hang it on the pier or wall."""
    kit.reset()
    lettering = kit.picture_material(f'{prop_name}-lettering', picture, roughness=0.7)
    wood, paint, iron = pit_village.grey_wood(), board_paint(), pit_village.black_iron()
    width, height = GATE_BOARD_WIDTH, GATE_BOARD_HEIGHT
    parts = pit_village.plank_board('board', width, height, 4, 0.035, (0, 0, height / 2), lettering, wood)
    for z in (-0.02, height + 0.02):
        parts.append(kit.box('moulding', (width + 0.08, 0.05, 0.04), (0, -0.004, z), paint, bevel=0.008))
    for x in (-width / 2 - 0.02, width / 2 + 0.02):
        parts.append(kit.box('moulding', (0.04, 0.05, height), (x, -0.004, height / 2), paint, bevel=0.008))
    for x in (-0.42, 0.42):
        parts.append(kit.box('batten', (0.08, 0.03, height - 0.02), (x, 0.033, height / 2), wood, bevel=0.004))
    bolts = [(side * (width / 2 + 0.02), -0.03, z) for side in (-1, 1) for z in (0.12, height - 0.12)]
    parts.append(kit.hex_bolts('coach-bolts', bolts, 0.011, iron))
    kit.join(prop_name, parts)
    save(prop_name, f'the works\' gate board "{words}" in cream sign-writer\'s lettering with a dark drop shade inside a cream lined border, '
         f'on near-black paint over four planks (lightly chipped, dark joints), a painted moulding with coach bolts, two battens behind; '
         f'board {width} x {height} m, letters about 0.27 m high; faces -y (three.js +z); hang it on the gate pier or the wall over the gate',
         {'lettering': [words], 'lettering_materials': [f'{prop_name}-lettering'], 'texture': f'{picture} 2048x878'})


def gate_board_no_1():
    gate_board('No. 1', 'gate-board-no-1', 'gate-board-no-1.jpg')


def gate_board_no_2():
    gate_board('No. 2', 'gate-board-no-2', 'gate-board-no-2.jpg')


# -------------------------------------------------------------------------------------- the bank

def bank_hanging_sign():
    """A board 1.2 x 0.6 m painted "BANK" in gilt on both faces, framed, hung on two eye rods from a
    wrought-iron bracket: a wall plate at the left end, a square top bar, a stay and a scroll, a ball
    finial. The board faces -y and +y, so a camera looking along the lane sees it face-on."""
    kit.reset()
    lettering = kit.picture_material('bank-sign-lettering', 'bank-sign.jpg', roughness=0.5)
    paint, iron = board_paint(), pit_village.black_iron()
    width, height, thickness = 1.2, 0.6, 0.045
    board = kit.box('sign-board', (width, thickness, height), (0, 0, height / 2), paint, bevel=0.004)
    picture_on_faces(board, lettering, width, height, (0, 0, height / 2), both_sides=True)
    frame = []
    for side in (-1, 1):
        y = side * (thickness / 2 + 0.007)
        for z in (0.012, height - 0.012):
            frame.append(kit.box('frame', (width, 0.014, 0.024), (0, y, z), paint, bevel=0.004))
        for x in (-width / 2 + 0.012, width / 2 - 0.012):
            frame.append(kit.box('frame', (0.024, 0.014, height), (x, y, height / 2), paint, bevel=0.004))
    kit.join('bank-sign-board', [board] + frame)
    # the bracket
    wall_x = -width / 2 - 0.2
    bar_z = height + 0.3      # high enough that the stay clears the board's top corner by about 4 cm
    bracket = [kit.box('wall-plate', (0.014, 0.075, 0.64), (wall_x, 0, bar_z - 0.2), iron, bevel=0.003),
               kit.box('top-bar', (width + 0.36, 0.024, 0.03), ((wall_x + width / 2 + 0.16) / 2, 0, bar_z), iron, bevel=0.003),
               kit.rod('stay', (wall_x, 0, bar_z - 0.32), (0.05, 0, bar_z - 0.016), 0.011, iron, sides=8)]
    bracket.append(ball('finial', 0.03, (width / 2 + 0.16 + 0.02, 0, bar_z), iron))
    bracket.append(kit.hex_bolts('wall-bolts', [(wall_x + 0.007, 0, bar_z - 0.43), (wall_x + 0.007, 0, bar_z + 0.06)], 0.012, iron, normal=(1, 0, 0)))
    # a scroll in the corner between the wall plate, the bar and the stay
    centre = Vector((wall_x + 0.2, 0, bar_z - 0.13))
    spiral = [centre + Vector((math.cos(angle), 0, math.sin(angle))) * (0.11 * (1 - 0.75 * t))
              for t, angle in ((k / 40, math.radians(170 - 600 * k / 40)) for k in range(41))]
    bracket.append(bent_bar('scroll', [Vector((wall_x + 0.005, 0, centre.z + 0.02))] + spiral, 0.0075, iron, flatten=0.6))
    # two eye rods from the bar to the board's top, with an eye at each end
    for x in (-0.42, 0.42):
        bracket.append(kit.rod('hanger', (x, 0, height + 0.02), (x, 0, bar_z - 0.03), 0.006, iron, sides=8))
        for z in (height + 0.02, bar_z - 0.03):
            bracket.append(kit.ring('eye', 0.012, 0.019, 0.008, at=(x, 0, z), material=iron, segments=20, rotate=(math.pi / 2, 0, 0)))
    kit.join('bank-sign-bracket', bracket)
    save('bank-hanging-sign', 'the bank\'s hanging sign: "BANK" in gilt (dark-shaded, inside a gilt lined border with corner diamonds) on both faces '
         'of a near-black framed board 1.2 x 0.6 m, letters about 0.29 m high, hung on two eye rods from a wrought-iron bracket (wall plate, '
         'square top bar, stay, scroll and ball finial). The bracket\'s wall plate is the prop\'s left end (lowest x): set it against the '
         'wall, so the board sticks out from the wall and faces along the lane (-y and +y); the bar is 0.9 m above the board\'s bottom',
         {'lettering': ['BANK', 'BANK (back face)'], 'lettering_materials': ['bank-sign-lettering'], 'texture': 'bank-sign 2048x1024'})


def bank_brass_plate():
    """A brass door plate 0.45 x 0.2 m with "BANK" engraved and blacked in, four round-headed brass
    screws. Faces -y; fix it beside the door."""
    kit.reset()
    lettering = kit.picture_material('bank-brass-plate-lettering', 'brass-plate.jpg', roughness=0.3, metallic=0.85)
    brass = pit_village.brass()
    width, height = 0.45, 0.2
    plate = kit.box('plate', (width, 0.005, height), (0, 0, height / 2), brass, bevel=0.0015)
    picture_on_faces(plate, lettering, width, height, (0, 0, height / 2))
    screws = kit.studs('screws', [(side_x * (width / 2 - 0.014), -0.0026, height / 2 + side_z * (height / 2 - 0.014))
                                  for side_x in (-1, 1) for side_z in (-1, 1)], 0.0055, brass, height_ratio=0.45)
    kit.join('bank-brass-plate', [plate, screws])
    save('bank-brass-plate', 'the bank\'s brass door plate: "BANK" engraved in a serif and filled with black wax inside an engraved border, '
         'brushed brass polished in the middle and tarnished toward the edges, four round-headed screws; 0.45 x 0.2 m, letters about 0.066 m '
         'high; faces -y (three.js +z); fix it on the wall beside the bank\'s door',
         {'lettering': ['BANK'], 'lettering_materials': ['bank-brass-plate-lettering'], 'texture': 'brass-plate 1024x455'})


# -------------------------------------------------------------------------------------- the drums

DRUM_RADIUS, DRUM_HEIGHT = 0.2925, 0.88    # a 45-gallon (205-litre) steel drum


def steel_drum(words, prop_name, picture):
    """A steel drum: rolled chimes top and bottom, two rolling hoops, a recessed lid with two bungs,
    dull grey-black paint; the stencilled word laid round the front between the hoops."""
    kit.reset()
    steel = drum_steel()
    r, h = DRUM_RADIUS, DRUM_HEIGHT
    profile = [(0.0, 0.008), (r - 0.012, 0.008), (r - 0.012, 0.0), (r + 0.004, 0.0), (r + 0.004, 0.018), (r, 0.026)]
    for hoop in (0.293, 0.587):
        profile += [(r, hoop - 0.016), (r + 0.006, hoop - 0.009), (r + 0.011, hoop), (r + 0.006, hoop + 0.009), (r, hoop + 0.016)]
    profile += [(r, h - 0.026), (r + 0.004, h - 0.018), (r + 0.004, h), (r - 0.012, h), (r - 0.012, h - 0.014), (0.0, h - 0.014)]
    body = turned('drum-body', profile, steel, sides=48)
    bungs = [kit.cylinder('bung-large', 0.032, 0.014, at=(-0.19, 0, h - 0.007), material=steel, sides=6, bevel=0.002),
             kit.cylinder('bung-small', 0.017, 0.012, at=(0.19, 0, h - 0.008), material=steel, sides=6, bevel=0.0015)]
    stencil = wrapped_strip('stencil', r + 0.0012, 60, 0.336, 0.536,
                            kit.picture_material(f'{prop_name}-stencil', picture, see_through=True, roughness=0.8))
    kit.join(prop_name, [body] + bungs)
    save(prop_name, f'steel drum (0.585 m across, 0.88 m tall) in dull grey-black worn paint, rolled chimes, two rolling hoops, a recessed lid '
         f'with two bungs; "{words}" stencilled in off-white block capitals (stencil bridges, sprayed edges) about 0.1 m high round the front '
         f'between the hoops (its own see-through object "stencil", facing -y, within 45 degrees of the front)',
         {'lettering': [words], 'lettering_materials': [f'{prop_name}-stencil'], 'texture': f'{picture} 2048x668 with transparency'})


def steel_drum_petrol():
    steel_drum('PETROL', 'steel-drum-petrol', 'drum-stencil-petrol.png')


def steel_drum_diesel():
    steel_drum('DIESEL', 'steel-drum-diesel', 'drum-stencil-diesel.png')


# ------------------------------------------------------------------------------------- the crate

CRATE_LENGTH, CRATE_DEPTH, CRATE_HEIGHT, BOARD = 0.8, 0.5, 0.5, 0.022


def crate_this_way_up():
    """A nailed packing crate: three deal boards on each side, four on the top and bottom, upright
    battens at the ends of the long sides and battens top and bottom on the short ends, nail heads;
    "THIS WAY UP" under two arrows stencilled on both long sides (upside down when the crate is turned
    over, as on page 14's upturned crate)."""
    kit.reset()
    deal, battens, iron = deal_boards(), pit_village.rough_wood(), pit_village.iron()
    length, depth, height, t = CRATE_LENGTH, CRATE_DEPTH, CRATE_HEIGHT, BOARD
    parts, nails = [], []
    side_height = height - 2 * t
    board_height = (side_height - 2 * 0.008) / 3
    for k in range(3):
        z = t + board_height / 2 + k * (board_height + 0.008)
        for side in (-1, 1):
            parts.append(kit.box('side-board', (length, t, board_height), (0, side * (depth / 2 - t / 2), z), deal, bevel=0.002))
            parts.append(kit.box('end-board', (t, depth - 2 * t, board_height), (side * (length / 2 - t / 2), 0, z), deal, bevel=0.002))
    top_width = (depth - 3 * 0.006) / 4
    for k in range(4):
        y = -depth / 2 + top_width / 2 + k * (top_width + 0.006)
        for z in (t / 2, height - t / 2):
            parts.append(kit.box('top-board', (length, top_width, t), (0, y, z), deal, bevel=0.002))
    for side in (-1, 1):
        y = side * (depth / 2 + t / 2)
        for x in (-length / 2 + 0.045, length / 2 - 0.045):
            parts.append(kit.box('batten', (0.07, t, height - 0.01), (x, y, height / 2), battens, bevel=0.003))
            nails += [(x, y + side * (t / 2 + 0.0005), t + board_height / 2 + k * (board_height + 0.008)) for k in range(3)]
        x = side * (length / 2 + t / 2)
        for z in (0.045, height - 0.045):
            parts.append(kit.box('end-batten', (t, depth, 0.07), (x, 0, z), battens, bevel=0.003))
    front_nails = [n for n in nails if n[1] < 0]
    back_nails = [n for n in nails if n[1] > 0]
    parts.append(kit.studs('nails-front', front_nails, 0.005, iron, normal=(0, -1, 0), height_ratio=0.3))
    parts.append(kit.studs('nails-back', back_nails, 0.005, iron, normal=(0, 1, 0), height_ratio=0.3))
    kit.join('crate', parts)
    stencil = kit.picture_material('crate-stencil', 'crate-stencil.png', see_through=True, roughness=0.85)
    for side in (-1, 1):
        flat_picture(f'stencil-{"front" if side < 0 else "back"}', 0.62, 0.25, (0, side * (depth / 2 + 0.0008), height / 2), stencil, facing=side)
    save('crate-this-way-up', 'nailed packing crate 0.8 x 0.5 x 0.5 m of sawn deal boards (three on each side, four on top and bottom) with '
         'battens and nail heads; "THIS WAY UP" under two upward arrows stencilled in black on both long sides (objects "stencil-front" '
         'facing -y and "stencil-back" facing +y, letters about 0.085 m high); turned over, the words read upside down',
         {'lettering': ['THIS WAY UP', 'THIS WAY UP (back)'], 'lettering_materials': ['crate-stencil'], 'texture': 'crate-stencil 1600x645 with transparency'})


# ---------------------------------------------------------------------------- chain and padlock

LOOP_STILE_GAP, LOOP_RADIUS, LOOP_HEIGHT = 0.03, 0.045, 0.30


def chain_and_padlock():
    """A loop of iron chain lying round two upright gate bars (centred 0.06 m apart, each up to about
    0.06 m thick), its two ends joined at the front by an old iron lever padlock that hangs below, and a
    short loose end hanging beside it."""
    kit.reset()
    iron, black = pit_village.iron(), pit_village.black_iron()
    links = []
    # the loop's path: a stadium shape round the two bars, starting at the front middle
    a, r = LOOP_STILE_GAP + 0.01, LOOP_RADIUS
    path = []
    steps = 200
    perimeter = 4 * a + 2 * math.pi * r
    for k in range(steps):
        s = perimeter * k / steps
        if s < a:                                   # front, middle to right
            point, tangent = (s, -r), (1, 0)
        elif s < a + math.pi * r:                   # round the right end
            angle = -math.pi / 2 + (s - a) / r
            point, tangent = (a + r * math.cos(angle), r * math.sin(angle)), (-math.sin(angle), math.cos(angle))
        elif s < 3 * a + math.pi * r:               # along the back, right to left
            point, tangent = (a - (s - a - math.pi * r), r), (-1, 0)
        elif s < 3 * a + 2 * math.pi * r:           # round the left end
            angle = math.pi / 2 + (s - 3 * a - math.pi * r) / r
            point, tangent = (-a + r * math.cos(angle), r * math.sin(angle)), (-math.sin(angle), math.cos(angle))
        else:                                       # front, left back to the middle
            point, tangent = (-a + (s - 3 * a - 2 * math.pi * r), -r), (1, 0)
        path.append((s, point, tangent))
    link_length, link_width, wire = 0.05, 0.03, 0.0065
    pitch = link_length - 2 * wire - 0.004
    count = int(perimeter / pitch)
    for index in range(count):
        s = perimeter * (index + 0.5) / count
        _, (x, y), (tx, ty) = min(path, key=lambda item: abs(item[0] - s))
        front_sag = max(0.0, -y / r) ** 4 * 0.02 * (1 - min(1.0, abs(x) / a))   # the front middle sags toward the lock
        turn = math.atan2(ty, tx)
        standing = index % 2 == 1
        links.append(kit.chain_link(f'link-{index}', (x, y, LOOP_HEIGHT - front_sag), (math.pi / 2 if standing else 0, 0, turn), iron,
                                    length=link_length, width=link_width, thickness=wire))
    # the loose end, hanging from the loop's front left
    for index in range(5):
        z = LOOP_HEIGHT - 0.03 - index * pitch
        links.append(kit.chain_link(f'loose-{index}', (-a - 0.012, -r - 0.004, z), (0, math.pi / 2, math.pi / 2 if index % 2 else 0), iron,
                                    length=link_length, width=link_width, thickness=wire))
    kit.join('chain', links)
    # the padlock: a body with a rounded bottom, a shackle through the loop's front, a keyhole cover
    shackle_top = LOOP_HEIGHT - 0.012
    body_top = shackle_top - 0.055
    lock = [kit.box('padlock-body', (0.07, 0.026, 0.05), (0, -r, body_top - 0.025), black, bevel=0.006),
            kit.cylinder('padlock-bottom', 0.035, 0.026, at=(0, -r, body_top - 0.05), material=black, sides=28, rotate=(math.pi / 2, 0, 0), bevel=0.004)]
    shackle = [Vector((-0.022, -r, body_top - 0.002))] + [Vector((-0.022 * math.cos(math.radians(angle)), -r, shackle_top - 0.022 + 0.022 * math.sin(math.radians(angle))))
                                                        for angle in range(0, 181, 15)] + [Vector((0.022, -r, body_top - 0.002))]
    shackle[1:-1] = [Vector((p.x, p.y, max(p.z, body_top + 0.008))) for p in shackle[1:-1]]
    lock.append(bent_bar('shackle', shackle, 0.0055, iron))
    lock.append(kit.cylinder('keyhole-cover', 0.009, 0.003, at=(0, -r - 0.0145, body_top - 0.04), material=pit_village.brass(), sides=16, rotate=(math.pi / 2, 0, 0)))
    lock.append(kit.box('keyhole', (0.003, 0.002, 0.008), (0, -r - 0.0165, body_top - 0.042), kit.plain_material('keyhole-dark', (0.01, 0.01, 0.01), roughness=0.9)))
    kit.join('padlock', lock)
    root = library.stand_on_ground('chain-and-padlock')
    loop_height = round(LOOP_HEIGHT + root.children[0].location.z, 3) if root.children else None
    library.save_prop('chain-and-padlock', 'a loop of heavy iron chain (links 5 cm long) to lie round the two gate leaves\' meeting bars, its ends '
                      'joined at the front by an old black iron lever padlock hanging below (brass keyhole cover), and a short loose end '
                      'hanging beside it; the bars pass through the loop at x = -0.04 and +0.04 m (up to about 0.06 m thick each)',
                      SCRIPTED, LICENCE, {'loop_height_above_base_metres': loop_height})


# ------------------------------------------------------------------------ lunch tin, mug, envelope

def lunch_tin():
    """A tinplate lunch tin 0.19 x 0.12 m with rounded corners, its lid on (overlapping 2.5 cm), a hinge
    along the back and a small clasp at the front."""
    kit.reset()
    tin = tinplate()
    parts = [rounded_slab('tin', 0.19, 0.12, 0.058, 0.016, 0.0, tin),
             rounded_slab('lid', 0.194, 0.124, 0.026, 0.017, 0.05, tin),
             kit.rod('hinge', (-0.075, 0.063, 0.062), (0.075, 0.063, 0.062), 0.0028, tin, sides=8),
             kit.box('clasp', (0.024, 0.004, 0.022), (0, -0.0635, 0.05), tin, bevel=0.001)]
    kit.join('lunch-tin', parts)
    save('lunch-tin', 'a tinplate lunch tin with rounded corners, its lid on, a hinge along the back and a clasp at the front; 0.194 x 0.124 x '
         '0.076 m; no lettering', {})


def tin_mug():
    """A plain tin mug (0.085 m across, 0.09 m tall) with a rolled rim, a strap handle and a dark tea
    stain inside."""
    kit.reset()
    tin = tinplate()
    profile = [(0.0, 0.004), (0.0395, 0.004), (0.0395, 0.087), (0.0405, 0.0905), (0.0428, 0.0912), (0.0438, 0.0885),
               (0.042, 0.0845), (0.042, 0.004), (0.0408, 0.0), (0.0, 0.0)]
    mug = turned('mug', profile, tin, sides=36)
    handle_points = [Vector((0.041 + 0.03 * math.cos(math.radians(angle)), 0, 0.05 + 0.03 * math.sin(math.radians(angle))))
                     for angle in range(-80, 81, 10)]
    handle = bent_bar('handle', [Vector((0.038, 0, handle_points[0].z))] + handle_points + [Vector((0.038, 0, handle_points[-1].z))], 0.006, tin,
                      flatten=0.3)   # a flat strap of tin, 12 mm wide
    stain = kit.cylinder('tea-stain', 0.0392, 0.001, at=(0, 0, 0.0047), material=kit.plain_material('tea-stain', (0.13, 0.08, 0.045), roughness=0.4))
    kit.join('tin-mug', [mug, handle, stain])
    save('tin-mug', 'a plain tin mug with a rolled rim, a strap handle on its +x side and a tea stain inside; 0.085 m across, 0.091 m tall; '
         'no lettering', {})


def wages_envelope():
    """A brown pay envelope (0.114 x 0.076 m, a little filled out in the middle), lying flat: "WAGES"
    printed on top, the gummed flap underneath."""
    kit.reset()
    length, width, thickness = 0.114, 0.076, 0.0036
    front = kit.picture_material('wages-envelope-printing', 'wages-envelope-front.jpg', roughness=0.85)
    back = kit.picture_material('wages-envelope-back', 'wages-envelope-back.jpg', roughness=0.85)
    columns, rows = 16, 11
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    grid_top, grid_bottom = {}, {}
    for i in range(columns):
        for j in range(rows):
            u, v = i / (columns - 1), j / (rows - 1)
            fullness = (1 - abs(2 * u - 1) ** 4) * (1 - abs(2 * v - 1) ** 4)
            x, y = (u - 0.5) * length, (v - 0.5) * width
            grid_top[i, j] = bm.verts.new((x, y, thickness / 2 * (1 + fullness)))
            edge = i in (0, columns - 1) or j in (0, rows - 1)
            grid_bottom[i, j] = grid_top[i, j] if edge else bm.verts.new((x, y, thickness / 2 * (1 - fullness)))
    for i in range(columns - 1):
        for j in range(rows - 1):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            top = bm.faces.new([grid_top[c] for c in corners])
            top.material_index = 0
            for loop, (ci, cj) in zip(top.loops, corners):
                loop[uv_layer].uv = (ci / (columns - 1), cj / (rows - 1))
            bottom = bm.faces.new([grid_bottom[c] for c in reversed(corners)])
            bottom.material_index = 1
            for loop, (ci, cj) in zip(bottom.loops, reversed(corners)):
                loop[uv_layer].uv = (1 - ci / (columns - 1), cj / (rows - 1))
    mesh = bpy.data.meshes.new('envelope'); bm.to_mesh(mesh); bm.free()
    envelope = bpy.data.objects.new('wages-envelope', mesh); bpy.context.scene.collection.objects.link(envelope)
    envelope.data.materials.append(front); envelope.data.materials.append(back)
    for polygon in mesh.polygons: polygon.use_smooth = True
    save('wages-envelope', 'a brown manila pay envelope lying flat, "WAGES" printed large in heavy black letters inside a printed rule on its top '
         'face (faces up, +z in Blender, +y in three.js), the gummed flap underneath; 0.114 x 0.076 m, a little filled out; letters about '
         '0.018 m high, so at real size the word can be read only within about 3 m of the camera',
         {'lettering': ['WAGES'], 'lettering_materials': ['wages-envelope-printing'], 'texture': 'wages-envelope-front and -back 1024x683'})


# --------------------------------------------------------------------------- jacket and cap on a nail

NAIL_HEIGHT = 0.84      # the nail above the jacket's hem, before standing the prop on the ground


def jacket_and_cap_on_nail():
    """A wool work jacket hung by its collar on a nail (the wall or post is the plane y = 0 behind it),
    so its shoulders droop from the nail and drape folds fan out below; sleeves hanging at the sides,
    three buttons, two pocket flaps. A tweed flat cap hangs over the collar on the same nail, crown
    out, peak down."""
    kit.reset()
    wool, tweed = jacket_wool(), cap_tweed()
    nail_z = NAIL_HEIGHT
    # the body: rings from the nail down to the hem; (drop below the nail, half width, thickness)
    shape = [(0.0, 0.02, 0.025), (0.035, 0.07, 0.045), (0.08, 0.14, 0.07), (0.14, 0.205, 0.085), (0.21, 0.232, 0.095),
             (0.33, 0.243, 0.095), (0.48, 0.25, 0.09), (0.64, 0.255, 0.08), (0.78, 0.258, 0.07)]

    def size_at(drop):
        """The body's half width and thickness at this drop below the nail."""
        for (drop_a, width_a, thickness_a), (drop_b, width_b, thickness_b) in zip(shape, shape[1:]):
            if drop <= drop_b:
                f = (drop - drop_a) / (drop_b - drop_a)
                return width_a + (width_b - width_a) * f, thickness_a + (thickness_b - thickness_a) * f
        return shape[-1][1], shape[-1][2]

    def body_y(x, sine, drop, thickness):
        """How far out from the wall the cloth is (as y) at x on the ring, sine being the ring angle's sine:
        a flattened tube, with drape folds fanning out from the nail (deeper lower down) and the button
        line a little sunk."""
        front = max(0.0, -sine)                       # 1 at the front middle, 0 at the sides and back
        y = -0.012 - thickness * (1 - sine) / 2
        y -= front * min(1.0, drop / 0.3) * 0.012 * math.sin(math.atan2(x, drop + 0.02) * 9 + 0.6)
        if abs(x) < 0.012 and drop > 0.12:
            y += 0.004 * front
        return y

    def front_y(x, drop):
        """The front surface's y at x and this drop (for buttons and pockets)."""
        half_width, thickness = size_at(drop)
        sine = -math.sqrt(max(0.0, 1 - (x / half_width) ** 2))
        return body_y(x, sine, drop, thickness)

    around = 48
    rings = []
    for drop, half_width, thickness in shape:
        ring = []
        for k in range(around):
            t = 2 * math.pi * k / around
            x = half_width * math.cos(t)
            ring.append(Vector((x, body_y(x, math.sin(t), drop, thickness), nail_z - drop - 0.006)))
        rings.append(ring)
    body = loft('jacket-body', rings, wool)
    parts = [body]
    # sleeves: from the drooping shoulders down the body's sides, a little in front of it, bowed forward
    for side in (-1, 1):
        # it starts inside the shoulder, so its top doesn't stand up above the drooping shoulder line
        sleeve = [Vector((side * (0.15 + 0.06 * math.sin(math.pi * f / 2)), -0.055 - 0.035 * math.sin(math.pi * f), nail_z - 0.15 - 0.53 * f))
                  for f in (k / 10 for k in range(11))]
        parts.append(bent_bar('sleeve', sleeve, 0.052, wool, sides=16, radius_end=0.046, flatten=0.85, bend_plane=(1, 0, 0)))
    # three buttons on the button line and two pocket flaps
    horn = kit.plain_material('button-horn', (0.04, 0.032, 0.026), roughness=0.4)
    for drop in (0.24, 0.38, 0.52):
        parts.append(kit.cylinder('button', 0.011, 0.005, at=(0.016, front_y(0.016, drop) - 0.0015, nail_z - drop - 0.006), material=horn,
                                  sides=16, rotate=(math.pi / 2, 0, 0)))
    for side in (-1, 1):
        x = side * 0.125
        slope = (front_y(x + 0.01, 0.56) - front_y(x - 0.01, 0.56)) / 0.02
        parts.append(kit.box('pocket-flap', (0.15, 0.012, 0.055), (x, front_y(x, 0.56) - 0.004, nail_z - 0.566), wool, bevel=0.004,
                             rotate=(0, 0, math.atan(slope))))
    kit.join('jacket', parts)
    # the nail: a forged nail sticking 6 cm out of the wall, its head just in front of the cap
    iron = pit_village.iron()
    nail = [kit.box('nail-shank', (0.007, 0.075, 0.007), (0, -0.0375, nail_z), iron),
            kit.cylinder('nail-head', 0.01, 0.004, at=(0, -0.077, nail_z), material=iron, sides=8, rotate=(math.pi / 2, 0, 0))]
    kit.join('nail', nail)
    # the flat cap, built as worn (crown up, peak toward -y), then hung: crown out (-y), peak down
    cap_parts = []
    bm = bmesh.new()
    grid = {}
    steps = 14
    for i in range(steps + 1):
        for j in range(steps + 1):
            u, v = 2 * i / steps - 1, 2 * j / steps - 1                 # -1..1 across and front (-1) to back (+1)
            r = math.sqrt(u * u + v * v)
            scale = 1 if r == 0 else max(abs(u), abs(v)) / r          # the square grid drawn in onto a disc
            x, y = u * scale * 0.098, v * scale * 0.115 - 0.012
            back = (v + 1) / 2
            reach = max(abs(u), abs(v))                                # 0 at the middle, 1 at the rim
            z = 0.012 + 0.04 * math.sqrt(max(0.0, 1 - reach * reach)) * (0.55 + 0.45 * back)
            grid[i, j] = bm.verts.new((x, y, z))
    for i in range(steps):
        for j in range(steps):
            bm.faces.new([grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]])
    mesh = bpy.data.meshes.new('cap-crown'); bm.to_mesh(mesh); bm.free()
    crown = bpy.data.objects.new('cap-crown', mesh); bpy.context.scene.collection.objects.link(crown)
    crown.data.materials.append(tweed)
    thick = crown.modifiers.new('cloth', 'SOLIDIFY'); thick.thickness = 0.004
    kit.apply_all(crown)
    for polygon in crown.data.polygons: polygon.use_smooth = True
    kit.project_by_facing(crown)
    cap_parts.append(crown)
    band = kit.cylinder('cap-band', 0.09, 0.016, at=(0, 0.0, 0.008), material=tweed, sides=32, radius_top=0.092)
    band.scale = (1.0, 1.17, 1.0)
    cap_parts.append(band)
    peak = kit.cylinder('cap-peak', 0.088, 0.005, at=(0, -0.145, 0.006), material=tweed, sides=32, rotate=(-0.12, 0, 0))
    peak.scale = (1.0, 0.55, 1.0)       # it sticks out about 6 cm past the crown's front
    cap_parts.append(peak)
    cap = kit.join('cap', cap_parts)
    # hung by the back of its band, crown out, turned 35 degrees so the peak juts down to the left: seen
    # crown-on and upright, a cap is a plain oval over the collar that reads like a head
    tilt = math.radians(35)
    cap.rotation_euler = (math.pi / 2, tilt, 0)
    cap.location = (-0.105 * math.sin(tilt), -0.072, nail_z - 0.105 * math.cos(tilt) + 0.012)
    save('jacket-and-cap-on-nail', 'a dark wool work jacket hung by its collar on a forged nail (shoulders drooping from the nail, drape folds, '
         'sleeves hanging at the sides, three horn buttons, two pocket flaps) with a grey-brown tweed flat cap hung over the collar, crown out '
         'and peak down; about 0.6 m wide and 0.86 m from hem to nail; its back is flat against the plane of the wall or post (the prop\'s +y '
         'side), the nail sticking out toward -y; no lettering', {'nail_height_above_base_metres': round(NAIL_HEIGHT + 0.006, 3)})


BUILDERS = {
    'gate-board-no-1': gate_board_no_1, 'gate-board-no-2': gate_board_no_2,
    'bank-hanging-sign': bank_hanging_sign, 'bank-brass-plate': bank_brass_plate,
    'steel-drum-petrol': steel_drum_petrol, 'steel-drum-diesel': steel_drum_diesel,
    'crate-this-way-up': crate_this_way_up, 'chain-and-padlock': chain_and_padlock,
    'lunch-tin': lunch_tin, 'jacket-and-cap-on-nail': jacket_and_cap_on_nail,
    'tin-mug': tin_mug, 'wages-envelope': wages_envelope,
}

if __name__ == '__main__':
    library.use_library('inflation-chapter-2-newcomers')
    wanted = library.take_folder_settings(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    print('writing props to', library.PROPS_FOLDER, 'with pictures from', kit.pictures_folder())
    for name in wanted or list(BUILDERS):
        BUILDERS[name]()
