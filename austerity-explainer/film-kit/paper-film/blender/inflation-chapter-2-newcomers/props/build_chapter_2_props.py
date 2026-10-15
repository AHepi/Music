# What this does: builds chapter 2's props that no free model covers, in Blender by script, and writes
# each as its own .glb with its line in its own library's index.json
# (assets/models/inflation-chapter-2-newcomers/props). So far the Works' small props ("34 Plan - chapter 2
# full redesign", part 1 A and part 3):
#   gate-board-no-1, gate-board-no-2   the works' gate boards, "No. 1" and "No. 2" in cream sign-writer's
#                                      lettering on near-black paint over three planks (a narrow plank
#                                      above and below a wide one that carries all the lettering, so no
#                                      joint runs through a letter), with a painted moulding
#   bank-hanging-sign                  "BANK" in gilt on both faces of a board hung from a wrought-iron
#                                      wall bracket
#   bank-brass-plate                   "BANK" engraved on a brass door plate with four screws
#   steel-drum-petrol, steel-drum-diesel   dull grey-black steel drums with rolling hoops, stencilled
#                                      "PETROL" and "DIESEL" in off-white
#   crate-this-way-up                  a nailed packing crate of deal boards and battens, stencilled
#                                      "THIS WAY UP" under two arrows on both long sides
#   chain-and-padlock                  a loop of iron chain (to go round the two gates' meeting bars),
#                                      a short hanging end, and an old iron padlock
#   lunch-tin                          a dull, dented tinplate lunch tin with its lid on
#   jacket-and-cap-on-nail             a wool work jacket hung by its collar on a nail, and beside it, on
#                                      its own nail and lower down, a tweed cap: nothing round sits above
#                                      the collar (a cap hung over the collar read as a headless man)
#   tin-mug                            an enamelled tin mug, dark blue-black, chipped at the rim and foot
#   wages-envelope                     a thin brown paper pay envelope printed "WAGES", lying flat, with a
#                                      faint fold below the word
# The wooden-chest model in the pit village library was not reused for the crate: it is a lidded chest
# with iron handles, not a nailed packing crate.
#
# Every prop is built in real metres, stands on the ground (its lowest point at height 0, centred over
# the origin) and has one root empty named after the prop, like the pit village's; joined parts carry
# their own names ("<prop>-body", "wages-envelope-paper"), never the prop's own, and
# prop_library.stand_on_ground stops if one does. Lettering is on its own materials (listed in each index
# line as "lettering_materials"), so the film can keep it as its own surface: the painter garbles small
# print. Lettered faces face Blender -y (three.js +z), except the envelope's, which faces up. The only
# figures (digits) are the gate boards' "1" and "2".
#
# Every size, letter height and hanging point written into index.json is measured from the finished
# model just before it is saved (and the letter heights from where the painter put the ink, which it
# notes in the pictures folder's lettering-sizes.json), not typed in. Each prop's licence names only the
# fonts and surfaces it really uses.
#
# It reuses the pit village's prop kit (pit-village/props: prop_library.py, scripted_kit.py) and the
# colliery-board builder's materials (build_scripted_props.py).
#
# Run (after download_poly_haven.py --choices chapter_2_choices.py and paint_chapter_2_pictures.py, which
# write into the scratch folder's downloads/ and pictures/):
#   blender -b --python build_chapter_2_props.py -- --scratch SCRATCH                 (all)
#   blender -b --python build_chapter_2_props.py -- --scratch SCRATCH tin-mug lunch-tin  (some)
#   (--library NAME_OR_FOLDER writes somewhere else; the default is chapter 2's own library)

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'pit-village', 'props'))
import prop_library as library  # noqa: E402
import scripted_kit as kit  # noqa: E402
import build_scripted_props as pit_village  # noqa: E402   (its builders run only when it is run itself)

SCRIPTED = 'Built by script (paper-film/blender/inflation-chapter-2-newcomers/props/build_chapter_2_props.py)'
FONT_LICENCES = {
    'Ultra': 'Ultra (Apache 2.0)',
    'Abril Fatface': 'Abril Fatface (SIL Open Font Licence)',
    'Old Standard TT': 'Old Standard TT (SIL Open Font Licence)',
    'DejaVu Sans Bold': 'DejaVu Sans Bold (Bitstream Vera licence, free)',
    'Alfa Slab One': 'Alfa Slab One (SIL Open Font Licence)',
}


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


def dull_tinplate():
    """Tinplate gone dull and dark with years of handling (paint_chapter_2_pictures.py's tinplate-dull.jpg,
    one picture to 0.25 m): a clean, light, shiny grey read as a modern plastic box."""
    return kit.picture_material('lunch-tin-tinplate', 'tinplate-dull.jpg', roughness=0.58, metallic=0.55, tile_metres=0.25)


def dark_enamel():
    """Dark blue-black enamel with chips showing the black iron (enamel-mug.jpg, wrapped once round the
    mug): a plain light metal read as a modern stainless-steel camping mug."""
    return kit.picture_material('tin-mug-enamel', 'enamel-mug.jpg', roughness=0.32, metallic=0.0)


def jacket_wool():
    """Dark grey-brown wool cloth (the caban texture with its orange taken out)."""
    return kit.surface_material('jacket-wool', 'caban', 0.27, tint=(0.2, 0.18, 0.16), tint_strength=1.0, metallic=0.0, roughness=0.95)


def cap_tweed():
    return kit.surface_material('cap-tweed', 'poly_wool_herringbone', 0.27, tint=(0.27, 0.25, 0.22), tint_strength=0.9, metallic=0.0, roughness=0.95)


# ------------------------------------------------------------------------- measuring the finished model

def lettering_sizes():
    """What paint_chapter_2_pictures.py noted about each lettered picture (lettering-sizes.json in the
    pictures folder): where the capitals' ink starts and ends, the font, the gate boards' plank joints and
    the envelope's fold."""
    path = os.path.join(kit.pictures_folder(), 'lettering-sizes.json')
    if not os.path.exists(path):
        raise SystemExit(f'{path} is missing: run paint_chapter_2_pictures.py into the scratch folder\'s pictures/ first')
    with open(path) as handle:
        return json.load(handle)


def metres_text(value):
    """A length in metres for a description: rounded to the millimetre, no trailing zeros."""
    return f'{round(value, 3):g}'


def part_bounds(*names):
    """Lowest and highest corner (world space) of the named parts."""
    return library.bounds([bpy.data.objects[name] for name in names])


def part_points(name):
    """Every point of a part, in world space."""
    part = bpy.data.objects[name]
    return [part.matrix_world @ vertex.co for vertex in part.data.vertices]


def picture_on_model(material_name, axis='z'):
    """Where a picture material lies on the finished model, measured from it: the world-space bounds of
    every face wearing it, how many metres the whole picture spans from its bottom edge to its top along
    `axis` (the picture's upward direction on the model), and where along that axis its bottom edge
    falls. Returns (low, high, picture_metres, picture_bottom)."""
    low, high = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    pairs = []
    for part in library.mesh_objects():
        slots = [index for index, slot in enumerate(part.material_slots) if slot.material and slot.material.name == material_name]
        if not slots:
            continue
        texture = part.data.uv_layers.active
        for polygon in part.data.polygons:
            if polygon.material_index not in slots:
                continue
            for loop_index in polygon.loop_indices:
                point = part.matrix_world @ part.data.vertices[part.data.loops[loop_index].vertex_index].co
                low, high = Vector(map(min, low, point)), Vector(map(max, high, point))
                pairs.append((getattr(point, axis), texture.data[loop_index].uv[1]))
    if not pairs:
        raise SystemExit(f'no face wears the material "{material_name}"')
    lowest = min(pairs, key=lambda pair: pair[1])
    highest = max(pairs, key=lambda pair: pair[1])
    picture_metres = (highest[0] - lowest[0]) / (highest[1] - lowest[1])
    return low, high, picture_metres, lowest[0] - lowest[1] * picture_metres


def letter_height(sizes, picture_metres):
    """The capitals' height in metres: the share of the picture's height the ink takes, times the
    picture's height on the model."""
    return (sizes['letters_bottom'] - sizes['letters_top']) * picture_metres


def picture_size(picture_file):
    image = bpy.data.images.get(picture_file)
    return f'{image.size[0]}x{image.size[1]}' if image else 'unknown size'


def uses_poly_haven_surfaces():
    """Whether any material wears a Poly Haven surface (straight from the downloads or tinted)."""
    surfaces = os.path.abspath(kit.surfaces_folder())
    tinted = os.path.abspath(os.path.join(library.SCRATCH, 'tinted'))
    for image in bpy.data.images:
        path = os.path.abspath(bpy.path.abspath(image.filepath_raw or image.filepath)) if (image.filepath_raw or image.filepath) else ''
        if path.startswith(surfaces) or path.startswith(tinted) or image.name.startswith('tint-'):
            return True
    return False


def save(prop_name, description, extra=None, fonts=()):
    """Writes the prop (already stood on the ground by library.stand_on_ground) with a source and licence
    naming only what it uses: the Poly Haven surfaces if any material wears one, and the lettering's font."""
    surfaces = uses_poly_haven_surfaces()
    source = SCRIPTED + (' with Poly Haven CC0 surface textures' if surfaces else ', wearing only pictures painted by paint_chapter_2_pictures.py')
    licence = 'Own work' + ('; textures CC0 1.0 (Poly Haven)' if surfaces else '')
    if fonts:
        licence += '; lettering font: ' + ', '.join(FONT_LICENCES[name] for name in fonts)
    return library.save_prop(prop_name, description, source, licence, extra)


# ---------------------------------------------------------------------------------- shape helpers

def turned(name, profile, material, sides=40, at=(0, 0, 0), wrap_picture=False):
    """A turned shape (drum, mug): profile [(radius, height), ...] spun round the upright axis. A point
    with radius 0 becomes the centre of a flat end. wrap_picture: lay the material's picture once round
    the shape (left to right) and from the foot (bottom of the picture) to the top (its top), instead of
    projecting it at real size."""
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
    if wrap_picture:
        top = max(height for _, height in profile)
        texture = bm.loops.layers.uv.new('UVMap')
        for face in bm.faces:
            arounds = [None if loop.vert.co.xy.length < 1e-6 else (math.atan2(loop.vert.co.y, loop.vert.co.x) / (2 * math.pi)) % 1.0
                       for loop in face.loops]
            known = [around for around in arounds if around is not None]
            if max(known) - min(known) > 0.5:        # the face crosses the seam: carry its low side past 1
                arounds = [None if around is None else around + 1 if around < 0.5 else around for around in arounds]
                known = [around for around in arounds if around is not None]
            middle = sum(known) / len(known)
            for loop, around in zip(face.loops, arounds):
                loop[texture].uv = (middle if around is None else around, loop.vert.co.z / top)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    part = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(part)
    part.location = at
    part.data.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    bpy.context.view_layer.update()
    if not wrap_picture:
        kit.project_by_facing(part)
    return part


def wrapped_strip(name, radius, half_angle_degrees, bottom, top, material, segments=32):
    """A picture laid round a cylinder (a drum's stencil): a curved strip facing -y, centred on the
    front, its picture running left to right as seen from the front."""
    bm = bmesh.new()
    texture = bm.loops.layers.uv.new('UVMap')
    columns = []
    for k in range(segments + 1):
        angle = math.radians(-half_angle_degrees + 2 * half_angle_degrees * k / segments)
        x, y = radius * math.sin(angle), -radius * math.cos(angle)
        columns.append((bm.verts.new((x, y, bottom)), bm.verts.new((x, y, top)), k / segments))
    for (low_a, high_a, u_a), (low_b, high_b, u_b) in zip(columns, columns[1:]):
        face = bm.faces.new([low_a, low_b, high_b, high_a])
        for loop, uv in zip(face.loops, [(u_a, 0), (u_b, 0), (u_b, 1), (u_a, 1)]):
            loop[texture].uv = uv
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
    texture = bm.loops.layers.uv.new('UVMap')
    corners = [bm.verts.new((left, y, z - height / 2)), bm.verts.new((right, y, z - height / 2)),
               bm.verts.new((right, y, z + height / 2)), bm.verts.new((left, y, z + height / 2))]
    face = bm.faces.new(corners)
    for loop, uv in zip(face.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop[texture].uv = uv
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
    texture = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for face in bm.faces:
        front, back = face.normal.y < -0.9, face.normal.y > 0.9 and both_sides
        if not (front or back):
            continue
        face.material_index = index
        for loop in face.loops:
            point = part.matrix_world @ loop.vert.co
            u = (point.x - centre[0]) / width + 0.5
            loop[texture].uv = (u if front else 1 - u, (point.z - centre[2]) / height + 0.5)
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
        ring_radius = radius + (radius_end - radius) * index / (len(points) - 1)
        rings.append([bm.verts.new(point + normal * math.cos(2 * math.pi * k / sides) * ring_radius * flatten
                                   + side * math.sin(2 * math.pi * k / sides) * ring_radius)
                      for k in range(sides)])
    for lower, upper in zip(rings, rings[1:]):
        for k in range(sides):
            bm.faces.new([lower[k], lower[(k + 1) % sides], upper[(k + 1) % sides], upper[k]])
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    part = kit._object(name, bm, material, (0, 0, 0), (0, 0, 0), 0, smooth=True)
    kit.project_by_facing(part)
    return part


def rounded_outline(length, width, corner, corner_steps=6, long_steps=12, short_steps=7):
    """The outline of a box with rounded upright corners (a tin, its lid), length along x and width along
    y, going round anticlockwise seen from above, with points along the straight sides too (so the sides
    can take a dent)."""
    corners = ((length / 2 - corner, width / 2 - corner, 0), (-length / 2 + corner, width / 2 - corner, 90),
               (-length / 2 + corner, -width / 2 + corner, 180), (length / 2 - corner, -width / 2 + corner, 270))
    outline = []
    for index, (centre_x, centre_y, start) in enumerate(corners):
        arc = [(centre_x + corner * math.cos(math.radians(start + 90 * step / corner_steps)),
                centre_y + corner * math.sin(math.radians(start + 90 * step / corner_steps))) for step in range(corner_steps + 1)]
        outline += arc
        next_x, next_y, next_start = corners[(index + 1) % 4]
        target = (next_x + corner * math.cos(math.radians(next_start)), next_y + corner * math.sin(math.radians(next_start)))
        steps = long_steps if index % 2 == 0 else short_steps      # after the first and third corners comes a long side
        outline += [(arc[-1][0] + (target[0] - arc[-1][0]) * step / steps, arc[-1][1] + (target[1] - arc[-1][1]) * step / steps)
                    for step in range(1, steps)]
    return outline


def dented_tin(name, length, width, height, corner, bottom, material, dents=(), rows=7, lip=0.0025):
    """A tinplate box with rounded upright corners and rolled, rounded top and bottom edges (a tin, its
    lid), closed top and bottom, finely enough divided to take soft dents. dents: (centre, radius, depth,
    push) each, push being the way the metal is pushed in."""
    outline = rounded_outline(length, width, corner)

    def drawn_in(scale_by):
        """The outline drawn in toward the middle by scale_by of the way."""
        return [(x * (1 - scale_by), y * (1 - scale_by)) for x, y in outline]

    lip_in = lip / (width / 2)
    side_heights = [bottom + lip + (height - 2 * lip) * k / rows for k in range(rows + 1)]
    rings = [(drawn_in(lip_in), bottom)] + [(outline, z) for z in side_heights] + [(drawn_in(lip_in), bottom + height)]
    rings += [(drawn_in(lip_in + (1 - lip_in) * fraction), bottom + height) for fraction in (0.12, 0.24, 0.36, 0.48, 0.60, 0.72, 0.84, 0.94)]
    bm = bmesh.new()
    vertex_rings = [[bm.verts.new((x, y, z)) for x, y in ring] for ring, z in rings]
    count = len(outline)
    for lower, upper in zip(vertex_rings, vertex_rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new([lower[i], lower[j], upper[j], upper[i]])
    top_middle = bm.verts.new((0, 0, bottom + height))
    bottom_middle = bm.verts.new((0, 0, bottom))
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new([vertex_rings[-1][i], vertex_rings[-1][j], top_middle])
        bm.faces.new([vertex_rings[0][j], vertex_rings[0][i], bottom_middle])
    for centre, radius, depth, push in dents:
        centre, push = Vector(centre), Vector(push).normalized()
        for vertex in bm.verts:
            distance = (vertex.co - centre).length
            if distance < radius:
                vertex.co += push * depth * 0.5 * (1 + math.cos(math.pi * distance / radius))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    part = kit._object(name, bm, material, (0, 0, 0), (0, 0, 0), 0, smooth=True)
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


def planks_cut_at_joints(name, width, height, joints_from_top, thickness, centre, face_material, back_material, gap=0.005):
    """A board of horizontal planks (like the pit village's plank_board) cut where the picture puts its
    joints (fractions of the board's height from its top): the planks' front faces together show the one
    painted picture. Sides and back wear plain timber."""
    bottom = centre[2] - height / 2
    edges = [bottom] + sorted(bottom + height * (1 - fraction) for fraction in joints_from_top) + [bottom + height]
    pieces = []
    for k, (low, high) in enumerate(zip(edges, edges[1:])):
        plank = kit.box(f'{name}{k}', (width, thickness, high - low - gap), (centre[0], centre[1], (low + high) / 2), back_material, bevel=0.003)
        plank.data.materials.append(face_material)
        bm = bmesh.new(); bm.from_mesh(plank.data)
        texture = bm.loops.layers.uv.get('UVMap')
        for face in bm.faces:
            if face.normal.y < -0.9:
                face.material_index = 1
                for loop in face.loops:
                    world = plank.matrix_world @ loop.vert.co
                    loop[texture].uv = ((world.x - centre[0]) / width + 0.5, (world.z - bottom) / height)
        bm.to_mesh(plank.data); bm.free()
        pieces.append(plank)
    return pieces


# ------------------------------------------------------------------------------- the gate boards

GATE_BOARD_WIDTH, GATE_BOARD_HEIGHT = 1.4, 0.6


def gate_board(words, prop_name, picture):
    """A works' gate board: three planks (cut where the picture puts the joints, above and below the
    letters) wearing the painted picture, a near-black moulding round the edge with coach bolts through
    its sides, two battens behind. Faces -y; hang it on the pier or wall."""
    kit.reset()
    sizes = lettering_sizes()[picture]
    lettering = kit.picture_material(f'{prop_name}-lettering', picture, roughness=0.7)
    wood, paint, iron = pit_village.grey_wood(), board_paint(), pit_village.black_iron()
    width, height = GATE_BOARD_WIDTH, GATE_BOARD_HEIGHT
    parts = planks_cut_at_joints(f'{prop_name}-plank', width, height, sizes['joints_from_top'], 0.035, (0, 0, height / 2), lettering, wood)
    for z in (-0.02, height + 0.02):
        parts.append(kit.box('moulding', (width + 0.08, 0.05, 0.04), (0, -0.004, z), paint, bevel=0.008))
    for x in (-width / 2 - 0.02, width / 2 + 0.02):
        parts.append(kit.box('moulding', (0.04, 0.05, height), (x, -0.004, height / 2), paint, bevel=0.008))
    for x in (-0.42, 0.42):
        parts.append(kit.box('batten', (0.08, 0.03, height - 0.02), (x, 0.033, height / 2), wood, bevel=0.004))
    bolts = [(side * (width / 2 + 0.02), -0.03, z) for side in (-1, 1) for z in (0.12, height - 0.12)]
    parts.append(kit.hex_bolts('coach-bolts', bolts, 0.011, iron))
    kit.join(f'{prop_name}-body', parts)
    library.stand_on_ground(prop_name)
    # measured from the finished model
    face_low, face_high, picture_metres, picture_bottom = picture_on_model(f'{prop_name}-lettering')
    letters = letter_height(sizes, picture_metres)
    joints = sorted(round(picture_bottom + (1 - fraction) * picture_metres, 3) for fraction in sizes['joints_from_top'])
    letters_low = picture_bottom + (1 - sizes['letters_bottom']) * picture_metres
    letters_high = picture_bottom + (1 - sizes['letters_top']) * picture_metres
    if any(letters_low - 0.01 < joint < letters_high + 0.01 for joint in joints):
        raise SystemExit(f'{prop_name}: a plank joint ({joints}) runs through the letters ({letters_low:.3f} to {letters_high:.3f} m)')
    save(prop_name, f'the works\' gate board "{words}" in cream sign-writer\'s lettering with a dark drop shade inside a cream lined border, '
         f'on near-black paint over three planks (a narrow plank above and below a wide one that carries all the lettering, so no joint '
         f'crosses a letter; lightly chipped, dark joints), a painted moulding with coach bolts, two battens behind; the lettered face is '
         f'{metres_text(face_high.x - face_low.x)} x {metres_text(face_high.z - face_low.z)} m, letters about {metres_text(letters)} m high; '
         f'faces -y (three.js +z); hang it on the gate pier or the wall over the gate',
         {'lettering': [words], 'lettering_materials': [f'{prop_name}-lettering'], 'texture': f'{picture} {picture_size(picture)}',
          'letter_height_metres': round(letters, 3), 'letters_from_base_metres': [round(letters_low, 3), round(letters_high, 3)],
          'plank_joints_from_base_metres': joints},
         fonts=[sizes['font']])


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
    sizes = lettering_sizes()['bank-sign.jpg']
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
    spiral = [centre + Vector((math.cos(angle), 0, math.sin(angle))) * (0.11 * (1 - 0.75 * share))
              for share, angle in ((k / 40, math.radians(170 - 600 * k / 40)) for k in range(41))]
    bracket.append(bent_bar('scroll', [Vector((wall_x + 0.005, 0, centre.z + 0.02))] + spiral, 0.0075, iron, flatten=0.6))
    # two eye rods from the bar to the board's top, with an eye at each end
    for x in (-0.42, 0.42):
        bracket.append(kit.rod('hanger', (x, 0, height + 0.02), (x, 0, bar_z - 0.03), 0.006, iron, sides=8))
        for z in (height + 0.02, bar_z - 0.03):
            bracket.append(kit.ring('eye', 0.012, 0.019, 0.008, at=(x, 0, z), material=iron, segments=20, rotate=(math.pi / 2, 0, 0)))
    kit.join('bank-sign-bracket', bracket)
    library.stand_on_ground('bank-hanging-sign')
    # measured from the finished model
    face_low, face_high, picture_metres, _ = picture_on_model('bank-sign-lettering')
    letters = letter_height(sizes, picture_metres)
    board_low, board_high = part_bounds('bank-sign-board')
    bracket_points = part_points('bank-sign-bracket')
    wall_end = min(point.x for point in bracket_points)
    wall_plate = [point.z for point in bracket_points if point.x < wall_end + 0.015]
    far_end = max(point.x for point in bracket_points)
    finial = [point.z for point in bracket_points if point.x > far_end - 0.03]
    bar_above_board = (min(finial) + max(finial)) / 2 - board_low.z
    save('bank-hanging-sign', f'the bank\'s hanging sign: "BANK" in gilt (dark-shaded, inside a gilt lined border with corner diamonds) on both faces '
         f'of a near-black framed board (lettered face {metres_text(face_high.x - face_low.x)} x {metres_text(face_high.z - face_low.z)} m), letters '
         f'about {metres_text(letters)} m high, hung on two eye rods from a wrought-iron bracket (wall plate, square top bar, stay, scroll and ball '
         f'finial). The bracket\'s wall plate is the prop\'s left end (lowest x, {metres_text(min(wall_plate))} to {metres_text(max(wall_plate))} m '
         f'above the prop\'s base): set it against the wall, so the board sticks out from the wall and faces along the lane (-y and +y); the bar is '
         f'{metres_text(bar_above_board)} m above the board\'s bottom',
         {'lettering': ['BANK', 'BANK (back face)'], 'lettering_materials': ['bank-sign-lettering'],
          'texture': f'bank-sign {picture_size("bank-sign.jpg")}', 'letter_height_metres': round(letters, 3),
          'board_bottom_above_base_metres': round(board_low.z, 3), 'wall_plate_from_base_metres': [round(min(wall_plate), 3), round(max(wall_plate), 3)]},
         fonts=[sizes['font']])


def bank_brass_plate():
    """A brass door plate 0.45 x 0.2 m with "BANK" engraved and blacked in, four round-headed brass
    screws. Faces -y; fix it beside the door."""
    kit.reset()
    sizes = lettering_sizes()['brass-plate.jpg']
    lettering = kit.picture_material('bank-brass-plate-lettering', 'brass-plate.jpg', roughness=0.3, metallic=0.85)
    brass = pit_village.brass()
    width, height = 0.45, 0.2
    plate = kit.box('plate', (width, 0.005, height), (0, 0, height / 2), brass, bevel=0.0015)
    picture_on_faces(plate, lettering, width, height, (0, 0, height / 2))
    screws = kit.studs('screws', [(side_x * (width / 2 - 0.014), -0.0026, height / 2 + side_z * (height / 2 - 0.014))
                                  for side_x in (-1, 1) for side_z in (-1, 1)], 0.0055, brass, height_ratio=0.45)
    kit.join('bank-brass-plate-body', [plate, screws])
    library.stand_on_ground('bank-brass-plate')
    face_low, face_high, picture_metres, _ = picture_on_model('bank-brass-plate-lettering')
    letters = letter_height(sizes, picture_metres)
    save('bank-brass-plate', f'the bank\'s brass door plate: "BANK" engraved in a serif and filled with black wax inside an engraved border, '
         f'brushed brass polished in the middle and tarnished toward the edges, four round-headed screws; '
         f'{metres_text(face_high.x - face_low.x)} x {metres_text(face_high.z - face_low.z)} m, letters about {metres_text(letters)} m high; '
         f'faces -y (three.js +z); fix it on the wall beside the bank\'s door',
         {'lettering': ['BANK'], 'lettering_materials': ['bank-brass-plate-lettering'], 'texture': f'brass-plate {picture_size("brass-plate.jpg")}',
          'letter_height_metres': round(letters, 3)},
         fonts=[sizes['font']])


# -------------------------------------------------------------------------------------- the drums

DRUM_RADIUS, DRUM_HEIGHT = 0.2925, 0.88    # a 45-gallon (205-litre) steel drum


def steel_drum(words, prop_name, picture):
    """A steel drum: rolled chimes top and bottom, two rolling hoops, a recessed lid with two bungs,
    dull grey-black paint; the stencilled word laid round the front between the hoops."""
    kit.reset()
    sizes = lettering_sizes()[picture]
    steel = drum_steel()
    radius, height = DRUM_RADIUS, DRUM_HEIGHT
    profile = [(0.0, 0.008), (radius - 0.012, 0.008), (radius - 0.012, 0.0), (radius + 0.004, 0.0), (radius + 0.004, 0.018), (radius, 0.026)]
    for hoop in (0.293, 0.587):
        profile += [(radius, hoop - 0.016), (radius + 0.006, hoop - 0.009), (radius + 0.011, hoop), (radius + 0.006, hoop + 0.009), (radius, hoop + 0.016)]
    profile += [(radius, height - 0.026), (radius + 0.004, height - 0.018), (radius + 0.004, height), (radius - 0.012, height),
                (radius - 0.012, height - 0.014), (0.0, height - 0.014)]
    body = turned('drum-body', profile, steel, sides=48)
    bungs = [kit.cylinder('bung-large', 0.032, 0.014, at=(-0.19, 0, height - 0.007), material=steel, sides=6, bevel=0.002),
             kit.cylinder('bung-small', 0.017, 0.012, at=(0.19, 0, height - 0.008), material=steel, sides=6, bevel=0.0015)]
    wrapped_strip('stencil', radius + 0.0012, 60, 0.336, 0.536,
                  kit.picture_material(f'{prop_name}-stencil', picture, see_through=True, roughness=0.8))
    kit.join(f'{prop_name}-body', [body] + bungs)
    library.stand_on_ground(prop_name)
    # measured from the finished model
    body_low, body_high = part_bounds(f'{prop_name}-body')
    _, _, picture_metres, _ = picture_on_model(f'{prop_name}-stencil')
    letters = letter_height(sizes, picture_metres)
    centre = (body_low + body_high) / 2
    strip_half_angle = max(abs(math.degrees(math.atan2(point.x - centre.x, centre.y - point.y))) for point in part_points('stencil'))
    words_half_angle = max(abs(sizes['letters_left'] - 0.5), abs(sizes['letters_right'] - 0.5)) * 2 * strip_half_angle
    across = body_high.y - body_low.y
    save(prop_name, f'steel drum ({metres_text(across)} m across the hoops, {metres_text(body_high.z - body_low.z)} m tall) in dull grey-black worn '
         f'paint, rolled chimes, two rolling hoops, a recessed lid with two bungs; "{words}" stencilled in off-white block capitals (stencil '
         f'bridges, sprayed edges) about {metres_text(letters)} m high round the front between the hoops (its own see-through object "stencil", '
         f'facing -y; the word reaches {round(words_half_angle)} degrees round to either side of the front, so turn the drum to face the camera)',
         {'lettering': [words], 'lettering_materials': [f'{prop_name}-stencil'], 'texture': f'{picture} {picture_size(picture)} with transparency',
          'letter_height_metres': round(letters, 3), 'word_reaches_degrees_either_side': round(words_half_angle, 1)},
         fonts=[sizes['font']])


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
    sizes = lettering_sizes()['crate-stencil.png']
    deal, battens, iron = deal_boards(), pit_village.rough_wood(), pit_village.iron()
    length, depth, height, board = CRATE_LENGTH, CRATE_DEPTH, CRATE_HEIGHT, BOARD
    parts, nails = [], []
    side_height = height - 2 * board
    board_height = (side_height - 2 * 0.008) / 3
    for k in range(3):
        z = board + board_height / 2 + k * (board_height + 0.008)
        for side in (-1, 1):
            parts.append(kit.box('side-board', (length, board, board_height), (0, side * (depth / 2 - board / 2), z), deal, bevel=0.002))
            parts.append(kit.box('end-board', (board, depth - 2 * board, board_height), (side * (length / 2 - board / 2), 0, z), deal, bevel=0.002))
    top_width = (depth - 3 * 0.006) / 4
    for k in range(4):
        y = -depth / 2 + top_width / 2 + k * (top_width + 0.006)
        for z in (board / 2, height - board / 2):
            parts.append(kit.box('top-board', (length, top_width, board), (0, y, z), deal, bevel=0.002))
    for side in (-1, 1):
        y = side * (depth / 2 + board / 2)
        for x in (-length / 2 + 0.045, length / 2 - 0.045):
            parts.append(kit.box('batten', (0.07, board, height - 0.01), (x, y, height / 2), battens, bevel=0.003))
            nails += [(x, y + side * (board / 2 + 0.0005), board + board_height / 2 + k * (board_height + 0.008)) for k in range(3)]
        x = side * (length / 2 + board / 2)
        for z in (0.045, height - 0.045):
            parts.append(kit.box('end-batten', (board, depth, 0.07), (x, 0, z), battens, bevel=0.003))
    front_nails = [n for n in nails if n[1] < 0]
    back_nails = [n for n in nails if n[1] > 0]
    parts.append(kit.studs('nails-front', front_nails, 0.005, iron, normal=(0, -1, 0), height_ratio=0.3))
    parts.append(kit.studs('nails-back', back_nails, 0.005, iron, normal=(0, 1, 0), height_ratio=0.3))
    kit.join('crate', parts)
    stencil = kit.picture_material('crate-stencil', 'crate-stencil.png', see_through=True, roughness=0.85)
    for side in (-1, 1):
        flat_picture(f'stencil-{"front" if side < 0 else "back"}', 0.62, 0.25, (0, side * (depth / 2 + 0.0008), height / 2), stencil, facing=side)
    library.stand_on_ground('crate-this-way-up')
    # measured from the finished model
    _, _, picture_metres, _ = picture_on_model('crate-stencil')
    letters = letter_height(sizes, picture_metres)
    low, high = part_bounds('crate')
    save('crate-this-way-up', f'nailed packing crate of sawn deal boards (three on each side, four on top and bottom) with battens and nail heads, '
         f'{metres_text(high.x - low.x)} x {metres_text(high.y - low.y)} x {metres_text(high.z - low.z)} m over its battens; "THIS WAY UP" under '
         f'two upward arrows stencilled in black on both long sides (objects "stencil-front" facing -y and "stencil-back" facing +y, letters '
         f'about {metres_text(letters)} m high); turned over, the words read upside down',
         {'lettering': ['THIS WAY UP', 'THIS WAY UP (back)'], 'lettering_materials': ['crate-stencil'],
          'texture': f'crate-stencil {picture_size("crate-stencil.png")} with transparency', 'letter_height_metres': round(letters, 3)},
         fonts=[sizes['font']])


# ---------------------------------------------------------------------------- chain and padlock

LOOP_STILE_GAP, LOOP_RADIUS, LOOP_HEIGHT = 0.03, 0.045, 0.30


def chain_and_padlock():
    """A loop of iron chain lying round two upright gate bars (centred 0.08 m apart, each up to about
    0.06 m thick), its two ends joined at the front by an old iron lever padlock that hangs below, and a
    short loose end hanging beside it."""
    kit.reset()
    iron, black = pit_village.iron(), pit_village.black_iron()
    links = []
    # the loop's path: a stadium shape round the two bars, starting at the front middle; half_straight is
    # half the length of its straight sides, which is where each bar's centre stands
    half_straight, loop_radius = LOOP_STILE_GAP + 0.01, LOOP_RADIUS
    path = []
    steps = 200
    perimeter = 4 * half_straight + 2 * math.pi * loop_radius
    for k in range(steps):
        along = perimeter * k / steps
        if along < half_straight:                                            # front, middle to right
            point, tangent = (along, -loop_radius), (1, 0)
        elif along < half_straight + math.pi * loop_radius:                  # round the right end
            angle = -math.pi / 2 + (along - half_straight) / loop_radius
            point, tangent = (half_straight + loop_radius * math.cos(angle), loop_radius * math.sin(angle)), (-math.sin(angle), math.cos(angle))
        elif along < 3 * half_straight + math.pi * loop_radius:              # along the back, right to left
            point, tangent = (half_straight - (along - half_straight - math.pi * loop_radius), loop_radius), (-1, 0)
        elif along < 3 * half_straight + 2 * math.pi * loop_radius:          # round the left end
            angle = math.pi / 2 + (along - 3 * half_straight - math.pi * loop_radius) / loop_radius
            point, tangent = (-half_straight + loop_radius * math.cos(angle), loop_radius * math.sin(angle)), (-math.sin(angle), math.cos(angle))
        else:                                                                # front, left back to the middle
            point, tangent = (-half_straight + (along - 3 * half_straight - 2 * math.pi * loop_radius), -loop_radius), (1, 0)
        path.append((along, point, tangent))
    link_length, link_width, wire = 0.05, 0.03, 0.0065
    pitch = link_length - 2 * wire - 0.004
    count = int(perimeter / pitch)
    for index in range(count):
        along = perimeter * (index + 0.5) / count
        _, (x, y), (tangent_x, tangent_y) = min(path, key=lambda item: abs(item[0] - along))
        front_sag = max(0.0, -y / loop_radius) ** 4 * 0.02 * (1 - min(1.0, abs(x) / half_straight))   # the front middle sags toward the lock
        turn = math.atan2(tangent_y, tangent_x)
        standing = index % 2 == 1
        links.append(kit.chain_link(f'link-{index}', (x, y, LOOP_HEIGHT - front_sag), (math.pi / 2 if standing else 0, 0, turn), iron,
                                    length=link_length, width=link_width, thickness=wire))
    # the loose end, hanging from the loop's front left
    for index in range(5):
        z = LOOP_HEIGHT - 0.03 - index * pitch
        links.append(kit.chain_link(f'loose-{index}', (-half_straight - 0.012, -loop_radius - 0.004, z), (0, math.pi / 2, math.pi / 2 if index % 2 else 0), iron,
                                    length=link_length, width=link_width, thickness=wire))
    kit.join('chain', links)
    # the padlock: a body with a rounded bottom, a shackle through the loop's front, a keyhole cover
    shackle_top = LOOP_HEIGHT - 0.012
    body_top = shackle_top - 0.055
    lock = [kit.box('padlock-body', (0.07, 0.026, 0.05), (0, -loop_radius, body_top - 0.025), black, bevel=0.006),
            kit.cylinder('padlock-bottom', 0.035, 0.026, at=(0, -loop_radius, body_top - 0.05), material=black, sides=28, rotate=(math.pi / 2, 0, 0), bevel=0.004)]
    shackle = [Vector((-0.022, -loop_radius, body_top - 0.002))] + [
        Vector((-0.022 * math.cos(math.radians(angle)), -loop_radius, shackle_top - 0.022 + 0.022 * math.sin(math.radians(angle))))
        for angle in range(0, 181, 15)] + [Vector((0.022, -loop_radius, body_top - 0.002))]
    shackle[1:-1] = [Vector((p.x, p.y, max(p.z, body_top + 0.008))) for p in shackle[1:-1]]
    lock.append(bent_bar('shackle', shackle, 0.0055, iron))
    lock.append(kit.cylinder('keyhole-cover', 0.009, 0.003, at=(0, -loop_radius - 0.0145, body_top - 0.04), material=pit_village.brass(), sides=16, rotate=(math.pi / 2, 0, 0)))
    lock.append(kit.box('keyhole', (0.003, 0.002, 0.008), (0, -loop_radius - 0.0165, body_top - 0.042), kit.plain_material('keyhole-dark', (0.01, 0.01, 0.01), roughness=0.9)))
    kit.join('padlock', lock)
    root = library.stand_on_ground('chain-and-padlock')
    # measured: where standing the prop on the ground moved the loop's middle (every part moved alike)
    moved = root.children[0].location
    loop_height = round(LOOP_HEIGHT + moved.z, 3)
    bars_x = [round(-half_straight + moved.x, 3), round(half_straight + moved.x, 3)]
    bars_y = round(moved.y, 3)
    save('chain-and-padlock', f'a loop of heavy iron chain (links 5 cm long) to lie round the two gate leaves\' meeting bars, its ends joined at the '
         f'front by an old black iron lever padlock hanging below (brass keyhole cover), and a short loose end hanging beside it; the bars pass '
         f'through the loop at x = {bars_x[0]} and {bars_x[1]} m, y = {bars_y} m (up to about 0.06 m thick each), the loop {loop_height} m above '
         f'the prop\'s base',
         {'loop_height_above_base_metres': loop_height, 'bars_through_loop_at_metres': {'x': bars_x, 'y': bars_y}})


# ------------------------------------------------------------------------ lunch tin, mug, envelope

def lunch_tin():
    """A tinplate lunch tin with rounded corners, its lid on (overlapping 2.5 cm), a hinge along the back
    and a small clasp at the front: dull, darkened tinplate, the lid dented twice on top and knocked at
    one corner, the box dented once at the front."""
    kit.reset()
    tin = dull_tinplate()
    parts = [dented_tin('tin', 0.19, 0.12, 0.058, 0.016, 0.0, tin,
                        dents=[((-0.045, -0.062, 0.026), 0.024, 0.003, (0, 1, 0))]),
             dented_tin('lid', 0.194, 0.124, 0.026, 0.017, 0.05, tin,
                        dents=[((0.042, -0.018, 0.076), 0.032, 0.0038, (0, 0, -1)),
                               ((-0.058, 0.028, 0.076), 0.02, 0.0022, (0, 0, -1)),
                               ((0.093, -0.058, 0.073), 0.016, 0.0025, (-0.5, 0.6, -0.6))]),
             kit.rod('hinge', (-0.075, 0.063, 0.062), (0.075, 0.063, 0.062), 0.0028, tin, sides=8),
             kit.box('clasp', (0.024, 0.004, 0.022), (0, -0.0635, 0.05), tin, bevel=0.001)]
    kit.join('lunch-tin-body', parts)
    library.stand_on_ground('lunch-tin')
    low, high = part_bounds('lunch-tin-body')
    save('lunch-tin', f'a lunch tin of dull, darkened tinplate (mottled, scratched, a few rust freckles) with rounded corners, its lid on, two soft '
         f'dents in the lid and a knock at its front corner, a dent in the box\'s front, a hinge along the back and a clasp at the front; '
         f'{metres_text(high.x - low.x)} x {metres_text(high.y - low.y)} x {metres_text(high.z - low.z)} m over its hinge and clasp; no lettering', {})


def tin_mug():
    """An enamelled tin mug (0.085 m across, 0.09 m tall) with a rolled rim, a strap handle and a dark tea
    stain inside: dark blue-black enamel, chipped to the black iron at the rim and the foot."""
    kit.reset()
    enamel = dark_enamel()
    profile = [(0.0, 0.004), (0.0395, 0.004), (0.0395, 0.087), (0.0405, 0.0905), (0.0428, 0.0912), (0.0438, 0.0885),
               (0.042, 0.0845), (0.042, 0.004), (0.0408, 0.0), (0.0, 0.0)]
    mug = turned('mug', profile, enamel, sides=36, wrap_picture=True)
    handle_points = [Vector((0.041 + 0.03 * math.cos(math.radians(angle)), 0, 0.05 + 0.03 * math.sin(math.radians(angle))))
                     for angle in range(-80, 81, 10)]
    handle = bent_bar('handle', [Vector((0.038, 0, handle_points[0].z))] + handle_points + [Vector((0.038, 0, handle_points[-1].z))], 0.006, enamel,
                      flatten=0.3)   # a flat strap of tin, 12 mm wide
    stain = kit.cylinder('tea-stain', 0.0392, 0.001, at=(0, 0, 0.0047), material=kit.plain_material('tea-stain', (0.13, 0.08, 0.045), roughness=0.4))
    kit.join('tin-mug-body', [mug, handle, stain])
    library.stand_on_ground('tin-mug')
    low, high = part_bounds('tin-mug-body')
    save('tin-mug', f'an enamelled tin mug in dark blue-black enamel, chipped to the black iron at the rolled rim and the foot, with a strap handle on '
         f'its +x side and a tea stain inside; {metres_text(high.y - low.y)} m across, {metres_text(high.z - low.z)} m tall, '
         f'{metres_text(high.x - low.x)} m with the handle; no lettering', {})


def wages_envelope():
    """A brown pay envelope (0.114 x 0.076 m) of thin paper, lying flat, a little filled out in the middle
    by what is inside: "WAGES" printed on top, the gummed flap underneath, and a faint fold across below
    the word where it was once folded and flattened again (the paper beyond the fold lifts a little)."""
    kit.reset()
    sizes = lettering_sizes()['wages-envelope-front.jpg']
    length, width = 0.114, 0.076
    edge, swell = 0.0006, 0.0012          # the paper's edge (two layers), and how much the notes inside fill it out
    fold = 1 - sizes['fold_from_top']      # the fold's place across the printed face, from its bottom edge (0) to its top (1)
    front = kit.picture_material('wages-envelope-printing', 'wages-envelope-front.jpg', roughness=0.85)
    back = kit.picture_material('wages-envelope-back', 'wages-envelope-back.jpg', roughness=0.85)
    acrosses = [i / 16 for i in range(17)]
    ups = sorted(set([round(j / 12, 4) for j in range(13)] + [round(fold - 0.03, 4), round(fold, 4), round(fold + 0.03, 4)]))

    def filled(share):
        """0 at an edge, 1 in the middle: how much the contents fill the paper out there."""
        return 1 - (2 * share - 1) ** 2

    def crease(up):
        """The fold's shallow crease along the top face."""
        return -0.00025 * math.exp(-((up - fold) / 0.012) ** 2)

    def raised(up):
        """The strip beyond the fold, lifted a little: folded paper never lies quite flat again."""
        return 0.0008 * ((fold - up) / fold) ** 1.5 if up < fold else 0.0

    bm = bmesh.new()
    texture = bm.loops.layers.uv.new('UVMap')
    top, under = {}, {}
    for i, across in enumerate(acrosses):
        for j, up in enumerate(ups):
            x, y = (across - 0.5) * length, (up - 0.5) * width
            bulge = filled(across) * filled(up)
            top[i, j] = bm.verts.new((x, y, edge / 2 + swell * bulge + raised(up) + crease(up)))
            under[i, j] = bm.verts.new((x, y, -edge / 2 - 0.3 * swell * bulge + raised(up)))
    columns, rows = len(acrosses), len(ups)

    def textured(face, corners, flip, material_index):
        face.material_index = material_index
        for loop, (ci, cj) in zip(face.loops, corners):
            loop[texture].uv = ((1 - acrosses[ci]) if flip else acrosses[ci], ups[cj])

    for i in range(columns - 1):
        for j in range(rows - 1):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            textured(bm.faces.new([top[c] for c in corners]), corners, False, 0)
            textured(bm.faces.new([under[c] for c in reversed(corners)]), list(reversed(corners)), True, 1)
    # the paper's thin edge all round, wearing the printed side's paper
    boundary = [(i, 0) for i in range(columns)] + [(columns - 1, j) for j in range(1, rows)] + \
               [(i, rows - 1) for i in range(columns - 2, -1, -1)] + [(0, j) for j in range(rows - 2, 0, -1)]
    for a, b in zip(boundary, boundary[1:] + boundary[:1]):
        textured(bm.faces.new([under[a], under[b], top[b], top[a]]), [a, b, b, a], False, 0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new('envelope'); bm.to_mesh(mesh); bm.free()
    envelope = bpy.data.objects.new('wages-envelope-paper', mesh); bpy.context.scene.collection.objects.link(envelope)
    envelope.data.materials.append(front); envelope.data.materials.append(back)
    for polygon in mesh.polygons: polygon.use_smooth = True
    library.stand_on_ground('wages-envelope')
    # measured from the finished model
    low, high = part_bounds('wages-envelope-paper')
    _, _, picture_metres, picture_bottom = picture_on_model('wages-envelope-printing', axis='y')
    letters = letter_height(sizes, picture_metres)
    fold_from_bottom_edge = picture_bottom + fold * picture_metres - low.y
    edge_points = [point.z for point in part_points('wages-envelope-paper')]
    save('wages-envelope', f'a brown manila pay envelope of thin paper lying flat, "WAGES" printed large in heavy black letters on its top face '
         f'(faces up, +z in Blender, +y in three.js; the word reads from the prop\'s -y side), the gummed flap underneath, a faint fold across '
         f'{metres_text(fold_from_bottom_edge)} m in from its -y edge, below the word; {metres_text(high.x - low.x)} x {metres_text(high.y - low.y)} m, '
         f'{metres_text(max(edge_points) - min(edge_points))} m thick where the contents fill it out; letters about {metres_text(letters)} m high, so '
         f'at real size the word can be read only within about 3 m of the camera',
         {'lettering': ['WAGES'], 'lettering_materials': ['wages-envelope-printing'],
          'texture': f'wages-envelope-front and -back {picture_size("wages-envelope-front.jpg")}', 'letter_height_metres': round(letters, 3),
          'fold_from_minus_y_edge_metres': round(fold_from_bottom_edge, 3)},
         fonts=[sizes['font']])


# --------------------------------------------------------------------------- jacket and cap on nails

NAIL_HEIGHT = 0.84      # the jacket's nail above its hem, before standing the prop on the ground
CAP_NAIL_ACROSS, CAP_NAIL_DROP = 0.40, 0.20     # the cap's own nail: right of the jacket's (+x) and below it
CAP_SWING_DEGREES = -35     # the hung cap swung round on its nail, its peak jutting down and away from the jacket
CAP_TURN_DEGREES = 20       # and turned on the nail so one side of it shows: seen straight on, crown out, a cap is a
                            # plain round disc; swung and turned, its sloping crown and its peak read as a cap


def jacket_and_cap_on_nail():
    """A wool work jacket hung by its collar on a nail (the wall or post is the plane y = 0 behind it),
    so its shoulders droop from the nail and drape folds fan out below; sleeves hanging at the sides,
    three buttons, two pocket flaps. Beside it, on its own short nail lower down, a tweed flat cap hangs
    against the wall by the back of its band, crown out, peak down. Nothing round sits above the collar:
    a cap hung over the collar read as a hunched man with a blank head."""
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
                fraction = (drop - drop_a) / (drop_b - drop_a)
                return width_a + (width_b - width_a) * fraction, thickness_a + (thickness_b - thickness_a) * fraction
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
            angle = 2 * math.pi * k / around
            x = half_width * math.cos(angle)
            ring.append(Vector((x, body_y(x, math.sin(angle), drop, thickness), nail_z - drop - 0.006)))
        rings.append(ring)
    body = loft('jacket-body', rings, wool)
    parts = [body]
    # sleeves: from the drooping shoulders down the body's sides, a little in front of it, bowed forward
    for side in (-1, 1):
        # it starts inside the shoulder, so its top doesn't stand up above the drooping shoulder line
        sleeve = [Vector((side * (0.15 + 0.06 * math.sin(math.pi * fraction / 2)), -0.055 - 0.035 * math.sin(math.pi * fraction), nail_z - 0.15 - 0.53 * fraction))
                  for fraction in (k / 10 for k in range(11))]
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
    # the jacket's nail: a forged nail sticking 7.5 cm out of the wall through the collar's loop
    iron = pit_village.iron()
    kit.join('jacket-nail', [kit.box('jacket-nail-shank', (0.007, 0.075, 0.007), (0, -0.0375, nail_z), iron),
                             kit.cylinder('jacket-nail-head', 0.01, 0.004, at=(0, -0.077, nail_z), material=iron, sides=8, rotate=(math.pi / 2, 0, 0))])
    # the flat cap, built as worn (crown up, peak toward -y)
    cap_parts = []
    bm = bmesh.new()
    grid = {}
    steps = 14
    for i in range(steps + 1):
        for j in range(steps + 1):
            u, v = 2 * i / steps - 1, 2 * j / steps - 1                 # -1..1 across and front (-1) to back (+1)
            distance = math.sqrt(u * u + v * v)
            scale = 1 if distance == 0 else max(abs(u), abs(v)) / distance   # the square grid drawn in onto a disc
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
    cloth = crown.modifiers.new('cloth', 'SOLIDIFY'); cloth.thickness = 0.004
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
    # hung on its nail: turned crown out (-y) and peak down, swung and turned on the nail, and moved so the
    # point inside the crown 3 cm in from the back of the band (where the nail holds it) sits on the nail's
    # head; then moved out from the wall just enough that no part of it goes behind the wall's plane
    cap.rotation_euler = (math.pi / 2, math.radians(CAP_SWING_DEGREES), math.radians(CAP_TURN_DEGREES))
    hook = Vector((0, 0.075, 0.030))
    nail_head = Vector((CAP_NAIL_ACROSS, -0.031, nail_z - CAP_NAIL_DROP))
    cap.location = nail_head - cap.rotation_euler.to_matrix() @ hook
    bpy.context.view_layer.update()
    behind_wall = max((cap.matrix_world @ vertex.co).y for vertex in cap.data.vertices) + 0.002
    cap.location.y -= max(0.0, behind_wall)
    nail_head.y -= max(0.0, behind_wall)
    # the cap's nail, out of the wall as far as the cap's inside, so the cap hides it
    kit.join('cap-nail', [kit.box('cap-nail-shank', (0.006, -nail_head.y, 0.006), (nail_head.x, nail_head.y / 2, nail_head.z), iron),
                          kit.cylinder('cap-nail-head', 0.008, 0.003, at=tuple(nail_head), material=iron, sides=8, rotate=(math.pi / 2, 0, 0))])
    library.stand_on_ground('jacket-and-cap-on-nail')
    # measured from the finished model
    jacket_low, jacket_high = part_bounds('jacket')
    jacket_nail_low, jacket_nail_high = part_bounds('jacket-nail')
    cap_nail_low, cap_nail_high = part_bounds('cap-nail')
    cap_low, cap_high = part_bounds('cap')
    jacket_nail_at = (jacket_nail_low + jacket_nail_high) / 2
    cap_nail_at = (cap_nail_low + cap_nail_high) / 2
    if cap_high.z > jacket_high.z - 0.08 or cap_low.x < jacket_high.x:
        raise SystemExit('jacket-and-cap-on-nail: the cap is above the collar or overlaps the jacket; it must hang beside it, lower down')
    save('jacket-and-cap-on-nail', f'a dark wool work jacket hung by its collar on a forged nail (shoulders drooping from the nail, drape folds, sleeves '
         f'hanging at the sides, three horn buttons, two pocket flaps), {metres_text(jacket_high.x - jacket_low.x)} m wide and '
         f'{metres_text(jacket_nail_at.z - jacket_low.z)} m from hem to nail; beside it on the +x side, on its own short nail '
         f'{metres_text(cap_nail_at.x - jacket_nail_at.x)} m across and {metres_text(jacket_nail_at.z - cap_nail_at.z)} m lower, a grey-brown tweed '
         f'flat cap hung by the back of its band, crown out, swung and turned a little on the nail so its peak juts down and away from the jacket, its top {metres_text(jacket_high.z - cap_high.z)} m below the collar, so '
         f'nothing round sits above the collar; the backs of both are flat against the plane of the wall or post (the prop\'s +y side), the nails '
         f'sticking out toward -y; no lettering',
         {'jacket_nail_metres': {'x': round(jacket_nail_at.x, 3), 'height_above_base': round(jacket_nail_at.z, 3)},
          'cap_nail_metres': {'x': round(cap_nail_at.x, 3), 'height_above_base': round(cap_nail_at.z, 3)},
          'wall_plane_y_metres': round(max(point.y for point in part_points('jacket-nail')), 3)})


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
