"""
What this file does:
Makes timber look old and used wherever a builder used it, the way the street bundle made its stone old.

  - Big timber (walls, decks, piles, posts, planks, fences, boats) gets weathered boards: grey wood, every board its
    own shade, rain streaks running down, the old paint left in peeling, cracked patches (one faded paint per
    building - white, duck-egg blue, faded blue, green, cream or turquoise - chosen by where it stands, so neighbours share it).
  - Tree trunks (anything named trunk, tree, palm, coconut, bark, branch or bough) get dark, wet, ringed bark.
  - Doors, shutters, frames, sashes and casings keep the street's peeling dark paint.
  - Timber the builder made out of many separate boards gets a shade per board.
  - A plain timber wall (one flat slab) is laid as overlapping boards: cut round its windows and doors, with casings,
    corner boards and nail lines that bleed rust.
  - Where timber meets the ground (seen by the camera survey), damp and rot creep up it, mould sits in the corner,
    and paint flakes and splinters lie at its foot.

    import lay_timber
    lay_timber.timber_kind(obj, role)            # 'painted', 'boards', 'bark' or None: which look a wood object gets
    lay_timber.timber_material(kind)             # the material for that look
    report = lay_timber.lay_boards(scene, roles, role_from_name, materials)          # plain slabs -> lapped boards
    report = lay_timber.lay_timber_feet(survey, materials, grime=1.0, growth=1.0, litter=1.0)

Laid boards are named "TIMBER • ..." (remove with remove_boards()); the small things are named "DETAIL • timber ..."
and go with lay_details.remove_details(). The builder's shapes are not moved.
"""

import math
import random
import re

import bpy
from mathutils import Vector

import survey as survey_module

PREFIX = 'TIMBER • '
DETAIL_PREFIX = 'DETAIL • timber '
BOARD_SHADES_MODIFIER = 'TIMBER • board shades'
PAINTED_WORDS = {'door', 'shutter', 'sash', 'frame', 'casing', 'window', 'surround', 'jamb', 'architrave'}
BARK_WORDS = {'trunk', 'bark', 'palm', 'tree', 'coconut', 'branch', 'bough'}
UP = Vector((0, 0, 1))


# ----------------------------------------------------------------------------------------------- which look

def timber_kind(obj, role):
    """Which look a wood-role object gets: 'painted' (doors, shutters, frames), 'bark' (trunks), else 'boards'."""
    if role != 'wood':
        return None
    words = set(re.findall(r'[a-z]+', obj.name.lower()))
    if words & BARK_WORDS:
        return 'bark'
    if words & PAINTED_WORDS:
        return 'painted'
    return 'boards'     # a mast, a flagpole or a column is timber, not a tree: only the words above make bark


# ----------------------------------------------------------------------------------------------- materials

def _ramp(nodes, stops, interpolation='LINEAR'):
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = interpolation
    elements = ramp.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, (position, colour) in zip(elements, stops):
        element.position = position
        element.color = (*colour, 1) if len(colour) == 3 else colour
    return ramp


def _mix(nodes, links, factor, a, b, blend='MIX'):
    """Colour mix; factor, a and b are sockets or plain values."""
    node = nodes.new('ShaderNodeMix')
    node.data_type = 'RGBA'
    node.blend_type = blend
    for socket, value in ((node.inputs[0], factor), (node.inputs[6], a), (node.inputs[7], b)):
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value if not isinstance(value, tuple) or len(value) != 3 else (*value, 1)
    return node.outputs[2]


def _math(nodes, links, operation, a, b=None, c=None):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for socket, value in zip(node.inputs, (a, b, c)):
        if value is None:
            continue
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value
    return node.outputs[0]


def _noise(nodes, links, vector, scale, detail=4.0, roughness=0.5, distortion=0.0):
    node = nodes.new('ShaderNodeTexNoise')
    node.inputs['Scale'].default_value = scale
    node.inputs['Detail'].default_value = detail
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Distortion'].default_value = distortion
    links.new(vector, node.inputs['Vector'])
    return node.outputs['Fac']


def _stretched(nodes, links, vector, scale):
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = scale
    links.new(vector, mapping.inputs['Vector'])
    return mapping.outputs['Vector']


def _fresh_material(name):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material, False
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    return material, True


def boards_material():
    """Weathered boards: grey wood with a shade per board (attribute 'board_tone'), rain streaks running down, and
    the old paint left in peeling, cracked patches; one faded paint per building (neighbouring objects share it)."""
    material, new = _fresh_material(PREFIX + 'weathered boards, peeling paint')
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    tone = nodes.new('ShaderNodeAttribute')
    tone.attribute_type = 'GEOMETRY'
    tone.attribute_name = 'board_tone'
    info = nodes.new('ShaderNodeObjectInfo')
    fine = _noise(nodes, links, position, 16.0, detail=6.0, roughness=0.55)
    mixed_tone = _math(nodes, links, 'MULTIPLY_ADD', tone.outputs['Fac'], 0.65, _math(nodes, links, 'MULTIPLY', fine, 0.45))
    bare = _ramp(nodes, [(0.0, (0.045, 0.041, 0.036)), (0.45, (0.115, 0.105, 0.092)), (0.85, (0.215, 0.205, 0.185)), (1.0, (0.26, 0.25, 0.23))])
    links.new(mixed_tone, bare.inputs[0])
    # no reds or oranges: under amber light a red paint peeling off grey wood reads as rust
    paint = _ramp(nodes, [(0.0, (0.36, 0.36, 0.33)), (0.2, (0.18, 0.25, 0.25)), (0.4, (0.11, 0.155, 0.23)),
                          (0.6, (0.12, 0.18, 0.12)), (0.8, (0.30, 0.27, 0.18)), (0.9, (0.07, 0.18, 0.18))], interpolation='CONSTANT')
    # one paint per building, not per board: the colour follows where the object stands, so neighbours share it
    where = nodes.new('ShaderNodeTexNoise')
    where.inputs['Scale'].default_value = 0.045
    where.inputs['Detail'].default_value = 0.0
    links.new(info.outputs['Location'], where.inputs['Vector'])
    spread = nodes.new('ShaderNodeMapRange')
    spread.inputs['From Min'].default_value, spread.inputs['From Max'].default_value = 0.32, 0.68
    links.new(where.outputs['Fac'], spread.inputs['Value'])
    links.new(spread.outputs['Result'], paint.inputs[0])
    # where the paint has held on: lower down it has peeled more
    peel = _noise(nodes, links, position, 2.7, detail=9.0, roughness=0.62, distortion=0.35)
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position, separate.inputs['Vector'])
    low = nodes.new('ShaderNodeMapRange')
    low.inputs['From Min'].default_value, low.inputs['From Max'].default_value = 0.0, 1.2
    low.inputs['To Min'].default_value, low.inputs['To Max'].default_value = 0.10, 0.0
    links.new(separate.outputs['Z'], low.inputs['Value'])
    threshold = _math(nodes, links, 'ADD', _math(nodes, links, 'MULTIPLY_ADD', info.outputs['Random'], 0.16, 0.40), low.outputs['Result'])
    held = nodes.new('ShaderNodeMapRange')
    links.new(peel, held.inputs['Value'])
    links.new(_math(nodes, links, 'SUBTRACT', threshold, 0.015), held.inputs['From Min'])
    links.new(_math(nodes, links, 'ADD', threshold, 0.015), held.inputs['From Max'])
    # alligator cracks in the old paint
    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = 34.0
    links.new(position, voronoi.inputs['Vector'])
    crack = nodes.new('ShaderNodeMapRange')
    crack.inputs['From Min'].default_value, crack.inputs['From Max'].default_value = 0.0, 0.05
    crack.inputs['To Min'].default_value, crack.inputs['To Max'].default_value = 0.35, 1.0
    links.new(voronoi.outputs['Distance'], crack.inputs['Value'])
    cracked_paint = _mix(nodes, links, 1.0, paint.outputs['Color'], crack.outputs['Result'], 'MULTIPLY')
    colour = _mix(nodes, links, held.outputs['Result'], bare.outputs['Color'], cracked_paint)
    # rain streaks running down from every edge
    streak = _noise(nodes, links, _stretched(nodes, links, position, (1.7, 1.7, 0.085)), 1.0, detail=5.0, roughness=0.6)
    streak_ramp = _ramp(nodes, [(0.32, (0.52, 0.52, 0.52)), (0.62, (1.0, 1.0, 1.0))])
    links.new(streak, streak_ramp.inputs[0])
    colour = _mix(nodes, links, 1.0, colour, streak_ramp.outputs['Color'], 'MULTIPLY')
    links.new(colour, principled.inputs['Base Color'])
    rough = nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value, rough.inputs['To Max'].default_value = 0.48, 0.86
    links.new(fine, rough.inputs['Value'])
    links.new(rough.outputs['Result'], principled.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.22
    bump.inputs['Distance'].default_value = 0.002
    links.new(_math(nodes, links, 'MULTIPLY_ADD', held.outputs['Result'], 0.6, _math(nodes, links, 'MULTIPLY', fine, 0.4)), bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.13, 0.12, 0.11, 1)
    return material


def bark_material():
    """Dark, wet, ringed bark: furrows running up the trunk and rings round it (a palm's leaf scars)."""
    material, new = _fresh_material(PREFIX + 'wet ringed bark')
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    furrow = _noise(nodes, links, _stretched(nodes, links, position, (7.0, 7.0, 0.7)), 1.0, detail=8.0, roughness=0.6)
    base = _ramp(nodes, [(0.25, (0.028, 0.025, 0.021)), (0.7, (0.10, 0.088, 0.070)), (1.0, (0.15, 0.135, 0.11))])
    links.new(furrow, base.inputs[0])
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 3.6
    wave.inputs['Distortion'].default_value = 5.0
    wave.inputs['Detail'].default_value = 3.0
    links.new(position, wave.inputs['Vector'])
    rings = _ramp(nodes, [(0.0, (0.5, 0.5, 0.5)), (0.25, (1.0, 1.0, 1.0))])
    links.new(wave.outputs['Fac'], rings.inputs[0])
    colour = _mix(nodes, links, 1.0, base.outputs['Color'], rings.outputs['Color'], 'MULTIPLY')
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.62
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.55
    bump.inputs['Distance'].default_value = 0.01
    links.new(_math(nodes, links, 'ADD', furrow, _math(nodes, links, 'MULTIPLY', wave.outputs['Fac'], 0.4)), bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.07, 0.06, 0.05, 1)
    return material


def _plain_material(name, colour, roughness, high=None, scale=60.0):
    material, new = _fresh_material(name)
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    principled.inputs['Roughness'].default_value = roughness
    if high is None:
        principled.inputs['Base Color'].default_value = (*colour, 1)
    else:
        noise = _noise(nodes, links, nodes.new('ShaderNodeNewGeometry').outputs['Position'], scale, detail=3.0)
        ramp = _ramp(nodes, [(0.0, colour), (1.0, high)])
        links.new(noise, ramp.inputs[0])
        links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    material.diffuse_color = (*colour, 1)
    return material


def is_flat_slab(obj):
    """A deck or a floor laid as one flat slab (few faces, thin, wide): it gets planks rather than plain boards."""
    if obj is None or obj.type != 'MESH' or len(obj.data.polygons) > 12:
        return False
    size = obj.dimensions
    return size.z < 0.25 and min(size.x, size.y) > 0.8


def timber_material(kind, obj=None):
    """The material for a timber look: from the photographed scans when they are in materials/textures, else the
    code-made one. Palms get palm bark; a flat deck or floor gets planks."""
    import scans
    if kind == 'boards':
        if obj is not None and is_flat_slab(obj):
            return scans.planks() or boards_material()
        return scans.boards() or boards_material()
    if kind == 'bark':
        palm = obj is not None and bool(set(re.findall(r'[a-z]+', obj.name.lower())) & {'palm', 'coconut'})
        return scans.bark(palm=palm) or bark_material()
    return None


# ----------------------------------------------------------------------------------------------- a shade per board

def vary_boards(obj, seed):
    """Timber the builder made of many separate boards: each board (each separate piece of the mesh) its own shade,
    written as the attribute 'board_tone' that the weathered-boards material reads. Live, so it follows edits."""
    if obj.type != 'MESH' or obj.modifiers.get(BOARD_SHADES_MODIFIER) or 'board_tone' in obj.data.attributes:
        return False
    group = bpy.data.node_groups.new(BOARD_SHADES_MODIFIER + ' • ' + obj.name, 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in, group_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    island = nodes.new('GeometryNodeInputMeshIsland')
    random_value = nodes.new('FunctionNodeRandomValue')
    random_value.data_type = 'FLOAT'
    random_value.inputs['Seed'].default_value = seed
    store = nodes.new('GeometryNodeStoreNamedAttribute')
    store.data_type = 'FLOAT'
    store.domain = 'FACE'
    store.inputs['Name'].default_value = 'board_tone'
    links.new(island.outputs['Island Index'], random_value.inputs['ID'])
    links.new(group_in.outputs['Geometry'], store.inputs['Geometry'])
    links.new(random_value.outputs['Value'], store.inputs['Value'])
    links.new(store.outputs['Geometry'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new(BOARD_SHADES_MODIFIER, 'NODES')
    modifier.node_group = group
    return True


# ----------------------------------------------------------------------------------------------- lapped boards

class BoardMesh:
    """Vertices, faces, material slots and a shade per face, in a wall face's own frame (u along, d out, z up). The
    vertices are kept in that frame (x along the wall, -y out of it, z up) and the object is turned and placed to the
    wall, so a scanned picture's grain runs along the boards whichever way the wall faces."""

    def __init__(self, face):
        self.face = face
        self.verts, self.faces, self.slots, self.tones = [], [], [], []

    def point(self, u, d, z):
        return (u, -d, z)

    def frame(self):
        from mathutils import Matrix
        along, normal = self.face['along'], self.face['normal']
        matrix = Matrix.Identity(4)
        for row in range(3):
            matrix[row][0] = along[row]
            matrix[row][1] = -normal[row]
            matrix[row][2] = (0.0, 0.0, 1.0)[row]
            matrix[row][3] = self.face['origin'][row]
        return matrix

    def solid(self, coords, slot, tone):
        """Eight corners: back-bottom-left, back-bottom-right, front-bottom-right, front-bottom-left, then the tops."""
        start = len(self.verts)
        self.verts.extend(self.point(*c) for c in coords)
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.faces.append(tuple(start + i for i in f))
            self.slots.append(slot)
            self.tones.append(tone)

    def box(self, u, d, z, w, dep, h, slot, tone):
        x, y = w / 2, dep / 2
        self.solid([(u - x, d - y, z - h / 2), (u + x, d - y, z - h / 2), (u + x, d + y, z - h / 2), (u - x, d + y, z - h / 2),
                    (u - x, d - y, z + h / 2), (u + x, d - y, z + h / 2), (u + x, d + y, z + h / 2), (u - x, d + y, z + h / 2)], slot, tone)

    def flat(self, quad, slot):
        start = len(self.verts)
        self.verts.extend(self.point(*c) for c in quad)
        self.faces.append(tuple(range(start, start + 4)))
        self.slots.append(slot)
        self.tones.append(0.5)


def _board_tone(rng):
    roll = rng.random()
    if roll < 0.06:
        return rng.uniform(0.93, 1.0)       # a newer board put in
    if roll < 0.11:
        return rng.uniform(0.0, 0.08)       # a rotten, near-black one
    return rng.uniform(0.18, 0.8)


def lap_face(face, holes, windows, doors, rng, near_camera):
    """Overlapping boards up one wall face, stopping at its openings, with casings, corner boards and nails."""
    mesh = BoardMesh(face)
    BOARD, IRON, RUST, CASING = 0, 1, 2, 3
    u0, u1, z0, z1 = face['u0'], face['u1'], face['z0'], face['z1']
    exposure = rng.uniform(0.165, 0.215)
    boards = nails = streaks = 0
    z = z0 + 0.01
    while z < z1 - 0.04:
        h = min(exposure, z1 - z)
        top = min(z + h + 0.03, z1)
        in_course = [(a - 0.01, b + 0.01) for a, b, c, e in holes if z < e and z + h > c]
        u = u0 - rng.uniform(0.0, 2.4)
        while u < u1:
            length = rng.uniform(1.8, 4.2)
            lo, hi = max(u, u0), min(u + length, u1)
            for p, q in survey_free_segments(lo, hi, in_course, 0.08):
                p, q = p + 0.002, q - 0.002
                tone = _board_tone(rng)
                proud = rng.uniform(-0.003, 0.004)
                twist = rng.uniform(-0.003, 0.003)
                b0, b1 = 0.024 + proud, 0.024 + proud + twist      # bottom edge out from the wall, each end
                t0, t1 = 0.008 + proud * 0.5, 0.008 + proud * 0.5 + twist * 0.5
                mesh.solid([(p, 0.002, z), (q, 0.002, z), (q, b1, z), (p, b0, z),
                            (p, 0.002, top), (q, 0.002, top), (q, t1, top), (p, t0, top)], BOARD, tone)
                boards += 1
                if near_camera:
                    stud = math.ceil((p - u0) / 0.6) * 0.6 + u0
                    while stud < q - 0.03:
                        if stud > p + 0.03:
                            mesh.box(stud, b0 + 0.002, z + 0.028, 0.011, 0.006, 0.011, IRON, 0.5)
                            nails += 1
                            if rng.random() < 0.16:
                                long = rng.uniform(0.05, 0.28)
                                w = rng.uniform(0.008, 0.016)
                                d = b0 + 0.006
                                mesh.flat([(stud - w / 2, d, z + 0.02 - long), (stud + w / 2, d, z + 0.02 - long),
                                           (stud + w * 0.3, d, z + 0.024), (stud - w * 0.3, d, z + 0.024)], RUST)
                                streaks += 1
                        stud += 0.6
            u += length
        z += h
    # casings round windows and doors; a drip cap over each window; a sill board under it
    for wu0, wu1, wz0, wz1 in windows:
        for side_u in (wu0 - 0.045, wu1 + 0.045):
            mesh.box(side_u, 0.042, (wz0 + wz1) / 2, 0.09, 0.03, wz1 - wz0 + 0.18, CASING, 0.5)
        mesh.box((wu0 + wu1) / 2, 0.042, wz1 + 0.045, wu1 - wu0 + 0.18, 0.03, 0.09, CASING, 0.5)
        mesh.box((wu0 + wu1) / 2, 0.06, wz1 + 0.10, wu1 - wu0 + 0.24, 0.07, 0.025, CASING, 0.5)
        mesh.box((wu0 + wu1) / 2, 0.06, wz0 - 0.03, wu1 - wu0 + 0.26, 0.09, 0.035, CASING, 0.5)
    for du0, du1, dz0, dz1 in doors:
        for side_u in (du0 - 0.05, du1 + 0.05):
            mesh.box(side_u, 0.042, (dz0 + dz1) / 2, 0.10, 0.03, dz1 - dz0, CASING, 0.5)
        mesh.box((du0 + du1) / 2, 0.042, dz1 + 0.05, du1 - du0 + 0.20, 0.03, 0.10, CASING, 0.5)
    # corner boards where the wall ends free
    for edge_u in (u0 + 0.05, u1 - 0.05):
        if not any(a - 0.1 < edge_u < b + 0.1 for a, b, c, e in holes):
            mesh.box(edge_u, 0.04, (z0 + z1) / 2, 0.10, 0.032, z1 - z0, BOARD, _board_tone(rng))
    return mesh, boards, nails, streaks


def survey_free_segments(lo, hi, blocked, minimum):
    import lay_facade
    return lay_facade._free_segments(lo, hi, blocked, minimum=minimum)


def remove_boards(scene):
    for obj in list(scene.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        if 'timber_front' in obj:
            del obj['timber_front']
        modifier = obj.modifiers.get(BOARD_SHADES_MODIFIER)
        if modifier is not None:
            group = modifier.node_group
            obj.modifiers.remove(modifier)
            if group is not None and group.users == 0:
                bpy.data.node_groups.remove(group)
    collection = bpy.data.collections.get(PREFIX + 'laid boards')
    if collection is not None and not collection.objects:
        bpy.data.collections.remove(collection)


def _is_added(obj):
    return (obj.name.startswith(('FACADE •', 'DETAIL •', 'LAID •', 'LOOK •', 'TIMBER •')) or bool(obj.get('prototype'))
            or '• laid' in obj.name)


def _thinnest_side(obj):
    """(thickness, length) of a simple shape measured across and along its own walls, so a wall turned by its vertices
    (not by its object) still counts as thin."""
    matrix = obj.matrix_world
    verts = [matrix @ v.co for v in obj.data.vertices]
    normal_matrix = matrix.to_3x3().inverted_safe().transposed()
    best = None
    for polygon in obj.data.polygons:
        n = normal_matrix @ polygon.normal
        n.z = 0.0
        if n.length < 1e-6:
            continue
        n.normalize()
        across = [v.dot(n) for v in verts]
        along_axis = Vector((-n.y, n.x, 0.0))
        along = [v.dot(along_axis) for v in verts]
        width, length = max(across) - min(across), max(along) - min(along)
        if best is None or width < best[0]:
            best = (width, length)
    return best or (min(obj.dimensions.x, obj.dimensions.y), max(obj.dimensions.x, obj.dimensions.y))


def is_plain_timber_wall(obj, role):
    if obj.type != 'MESH' or role != 'wood' or timber_kind(obj, role) != 'boards' or len(obj.data.polygons) > 12:
        return False
    thickness, length = _thinnest_side(obj)
    return thickness < 0.45 and obj.dimensions.z > 1.0 and length > 1.2


def lay_boards(scene, roles, role_from_name, materials, seed=60411):
    """
    materials: boards, dark (behind the boards), iron (nail heads), rust (streaks), painted (casings).
    Every plain timber wall facing the camera gets lapped boards; every other boards-look timber object gets a shade
    per board. Returns a report.
    """
    import lay_facade
    remove_boards(scene)
    rng = random.Random(seed)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    camera_spot = scene.camera.matrix_world.translation if scene.camera else Vector((0, 0, 1.6))
    collection = bpy.data.collections.get(PREFIX + 'laid boards')
    if collection is None:
        collection = bpy.data.collections.new(PREFIX + 'laid boards')
        scene.collection.children.link(collection)
    report = {'timber_walls_boarded': 0, 'faces_boarded': 0, 'boards': 0, 'nails': 0, 'rust_streaks_under_nails': 0,
              'timber_objects_shaded_per_board': 0}
    for index, obj in enumerate(list(scene.objects)):
        if obj.type != 'MESH' or _is_added(obj):
            continue
        role = roles.get(obj.name)
        if timber_kind(obj, role) != 'boards':
            continue
        if not is_plain_timber_wall(obj, role):
            if vary_boards(obj, 300 + index):
                report['timber_objects_shaded_per_board'] += 1
            continue
        made_any = False
        for face_index, face in enumerate(lay_facade.oriented_faces(obj, minimum_area=1.0)):
            if not lay_facade._facing_camera(face, camera_spot) or lay_facade._buried(scene, depsgraph, face, roles):
                continue
            found = lay_facade.openings_on(face, scene, roles, role_from_name)
            windows = [(a, b, c, e) for a, b, c, e, r, name in found if r in lay_facade.WINDOW_ROLES and 0.25 < b - a < 4 and 0.25 < e - c < 4]
            doors = [(a, b, c, e) for a, b, c, e, r, name in found if r == 'wood' and e - c > 1.6 and c < face['z0'] + 0.8 and 0.55 < b - a < 2.5]
            holes = [(a, b, c, e) for a, b, c, e, r, name in found if r != 'trim']
            centre = face['origin'] + face['along'] * ((face['u0'] + face['u1']) / 2)
            near = (centre - Vector((camera_spot.x, camera_spot.y, 0))).length < 14.0
            mesh, boards, nails, streaks = lap_face(face, holes, windows, doors, rng, near)
            report['faces_boarded'] += 1
            report['boards'] += boards
            report['nails'] += nails
            report['rust_streaks_under_nails'] += streaks
            if not mesh.faces:
                continue
            name = PREFIX + obj.name + ' • lapped boards %d' % face_index
            data = bpy.data.meshes.new(name)
            data.from_pydata(mesh.verts, [], mesh.faces)
            for material in (materials['boards'], materials['iron'], materials['rust'], materials['painted']):
                data.materials.append(material)
            for polygon, slot in zip(data.polygons, mesh.slots):
                polygon.material_index = slot
            attribute = data.attributes.new('board_tone', 'FLOAT', 'FACE')
            attribute.data.foreach_set('value', mesh.tones)
            import bmesh
            tool = bmesh.new()
            tool.from_mesh(data)
            bmesh.ops.recalc_face_normals(tool, faces=tool.faces)
            tool.to_mesh(data)
            tool.free()
            data.update()
            boards_obj = bpy.data.objects.new(name, data)
            boards_obj.matrix_world = mesh.frame()
            boards_obj['place_role'] = 'wood'
            collection.objects.link(boards_obj)
            import scans
            scans.mark_object(boards_obj, grain_axis=0)      # along the wall: the boards' own length
            made_any = True
        if not made_any:
            continue
        obj.data.materials.clear()
        obj.data.materials.append(materials['dark'])
        obj['timber_front'] = 0.026
        report['timber_walls_boarded'] += 1
    return report


# ----------------------------------------------------------------------------------------------- where timber meets the ground

def _strip(seen, run, heights, out, rows, rng, drop_top, drop_rest, verts, faces):
    """A band up a standing surface from its foot: rows of points that follow the surface, its top edge ragged."""
    columns = []
    for foot, h in zip(run, heights):
        column = []
        for r in range(rows + 1):
            z = max(0.012, h * r / rows)
            p = seen.surface_point(foot, z, strict=r > 0)
            if p is None or (r and (p - (column[-1] - foot.normal * out)).length > 0.45):
                break
            column.append(p + foot.normal * out)
        columns.append(column)
    made = 0
    for a, b in zip(columns, columns[1:]):
        rows_here = min(len(a), len(b)) - 1
        if rows_here < 1:
            continue
        start_a = len(verts)
        verts.extend(tuple(p) for p in a[:rows_here + 1])
        start_b = len(verts)
        verts.extend(tuple(p) for p in b[:rows_here + 1])
        for r in range(rows_here):
            chance = drop_top if r == rows_here - 1 else drop_rest
            if rng.random() < chance:
                continue
            faces.append((start_a + r, start_b + r, start_b + r + 1, start_a + r + 1))
            made += 1
    return made


def _mesh(name, verts, faces, material, collection, role):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    if material is not None:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    obj['place_role'] = role
    collection.objects.link(obj)
    return obj


def lay_timber_feet(seen, roles, materials, collection, *, grime=1.0, growth=1.0, litter=1.0, seed=50873, indoors=None):
    """
    Damp and rot up the foot of every timber thing the camera sees meeting the ground, mould in the corner, and
    paint flakes and splinters on the ground in front; none of it indoors (a table on a tea-room floor stays clean
    at the foot). materials: grime, moss. Returns a report.
    """
    rng = random.Random(seed)
    report = {'timber_feet_seen': 0, 'rot_faces': 0, 'mould_faces': 0, 'flakes_and_splinters': 0}
    if seen is None or not seen.grid:
        return report
    rot_verts, rot_faces, mould_verts, mould_faces = [], [], [], []
    flake_verts, flake_faces, flake_slots = [], [], []
    scene = seen.scene
    for run in seen.foot_runs({'wood'}):
        obj = scene.objects.get(run[0].obj)
        if obj is None:
            continue
        kind = timber_kind(obj, 'wood') if not obj.name.startswith(PREFIX) else 'boards'
        report['timber_feet_seen'] += len(run)
        if indoors is not None and indoors(run[len(run) // 2].point):
            report['timber_feet_indoors_left_clean'] = report.get('timber_feet_indoors_left_clean', 0) + len(run)
            continue
        lengths = survey_module.run_length(run)
        object_seed = survey_module.steady_seed(obj.name) / 37.0
        base = rng.uniform(0.10, 0.30) if kind != 'bark' else rng.uniform(0.25, 0.7)
        if grime > 0 and len(run) > 1:
            heights = [base * grime * (0.62 + 0.38 * survey_module.smooth_wave(t * 2.4, object_seed)) for t in lengths]
            report['rot_faces'] += _strip(seen, run, heights, 0.006, 4, rng, 0.32, 0.06, rot_verts, rot_faces)
        if growth > 0 and len(run) > 1:
            heights = [base * (0.22 + 0.18 * survey_module.smooth_wave(t * 3.1, object_seed + 5)) for t in lengths]
            report['mould_faces'] += _strip(seen, run, heights, 0.009, 2, rng, 0.62, 0.45 / max(growth, 0.2), mould_verts, mould_faces)
        if litter > 0 and kind in ('boards', 'painted') and obj.dimensions.z > 0.45:
            along = Vector((-run[0].normal.y, run[0].normal.x, 0))
            for k, foot in enumerate(run):
                if rng.random() > 0.38 * litter:
                    continue
                for _ in range(rng.randint(1, 3)):
                    out = rng.expovariate(1 / 0.09) + 0.015
                    p = foot.point + foot.normal * min(out, 0.5) + along * rng.uniform(-0.08, 0.08)
                    ground = seen.ground_under(p, above=0.3)
                    if ground is None or abs(ground[0] - foot.point.z) > 0.12:
                        continue
                    size = rng.uniform(0.008, 0.035)
                    a = rng.uniform(0, math.tau)
                    start = len(flake_verts)
                    for c in range(4):
                        angle = a + c * math.pi / 2 + rng.uniform(-0.4, 0.4)
                        r = size * rng.uniform(0.6, 1.2) * (1.6 if c % 2 == 0 else 0.7)
                        corner = Vector((p.x + math.cos(angle) * r, p.y + math.sin(angle) * r, ground[0]))
                        under = seen.ground_under(corner, above=0.05)         # each corner rests on the ground below it
                        z = under[0] if under is not None and abs(under[0] - ground[0]) < 0.05 else ground[0]
                        flake_verts.append((corner.x, corner.y, z + 0.002 + rng.uniform(0, 0.003)))
                    flake_faces.append((start, start + 1, start + 2, start + 3))
                    flake_slots.append(0 if rng.random() < 0.55 else 1)
                    report['flakes_and_splinters'] += 1
    if rot_faces:
        obj = _mesh(DETAIL_PREFIX + 'damp and rot at the foot', rot_verts, rot_faces, materials['grime'], collection, 'grime')
        obj.visible_shadow = False
    if mould_faces:
        obj = _mesh(DETAIL_PREFIX + 'mould in the corner', mould_verts, mould_faces, materials['moss'], collection, 'moss')
        obj.visible_shadow = False
    if flake_faces:
        obj = _mesh(DETAIL_PREFIX + 'paint flakes and splinters', flake_verts, flake_faces, None, collection, 'leaf')
        obj.data.materials.append(_plain_material(PREFIX + 'paint flakes', (0.16, 0.165, 0.155), 0.7, (0.25, 0.25, 0.235)))
        obj.data.materials.append(_plain_material(PREFIX + 'splinters', (0.10, 0.09, 0.075), 0.8, (0.19, 0.175, 0.15)))
        for polygon, slot in zip(obj.data.polygons, flake_slots):
            polygon.material_index = slot
    return report
