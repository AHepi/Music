"""
What this file does: puts a Japanese tiled roof on a building, a box you name, the way temples and inns are roofed: a
hip-and-gable roof (irimoya: four slopes below, a small upright gable high on each end) by default, or a plain hipped
roof (yosemune) or a plain gable roof (kirizuma). The eaves are deep and the slopes curve: steep near the ridge, flatter
towards the eaves, and the eaves lift towards turned-up corners. The slopes are laid in real tiles: rows of pan tiles,
each course stepping over the one below, with half-round cover tiles over their joints and a round end tile on every
row at the eave; a heavy ridge of stacked tiles with an ornamental end tile (onigawara) at each end; hips (or, on a
hip-and-gable roof, the gables' edges and the corner ridges) in smaller stacks. Under the eaves: rafters, the boarding
they carry, an eaves board along the edge and a heavy beam along the top of each wall; the gables are plaster in a
timber frame, with bargeboards and a hanging ornament. A small gable can stand on the front slope over an entrance
(`front_gable`). Each tile shows its own part of the photographed surface (the number `pp_piece`). Nothing is moved,
and nothing is placed anywhere you did not say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_tile_roof
    made = lay_tile_roof.lay(inn, kind='hip-and-gable', overhang=1.1, pitch=28, lift=0.35, front_gable=2.6, seed=2)
    made['tiles'], made['timber'], made['gables']            # the objects: tiles and ridges, timber, plaster gables

The box's own axes decide the sides: 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X). The ridge runs along the
box's longer side unless you say (`ridge`).

From the command line:

    python3 lay_tile_roof.py --help
    python3 lay_tile_roof.py --blend IN.blend --object Inn --kind hip-and-gable --overhang 1.1 --front-gable 2.6 --out OUT.blend

Options, with their defaults:
    kind          'hip-and-gable'  'hip-and-gable' (irimoya), 'hipped' (yosemune: four slopes up to a short ridge) or
                                   'gable' (kirizuma: two slopes, an upright gable at each end)
    overhang      1.0 m       how far the eaves reach past the walls (a gable roof's gable ends reach 0.6 of it)
    pitch         28          the slope's mean pitch in degrees (20 to 45): about 0.65 of it at the eave, 1.35 near the ridge
    lift          0.3 m       how much the eaves rise towards each corner (0 for a straight eave; 0.8 at most)
    ridge         'long'      'long' (along the box's longer side), 'front' (parallel to the front) or 'side'
    front_gable   None        the width in metres of a small gable standing on the front slope over an entrance
                              (1.2 to 0.7 of the front's length); None for none
    gable_at      None        metres along the front from its left end to the small gable's middle (None: the middle)
    tile          0.28 m      the spacing of the rows of cover tiles (0.2 to 0.4)
    rafters       0.42 m      the rafters' spacing under the eaves (0 for none)
    seed          0           each tile's part of the picture and shade, the cover tiles' small set
    collection    none        where the objects go (a new collection 'lay_tile_roof')
    tile_material    'SURFACE • dark_rock_02'      (the tiles and ridges; a darkened, wet, finer copy is made of it)
    timber_material  'SURFACE • old_planks_02'     (the rafters, boarding, eaves boards, beams, bargeboards, gable frame)
    plaster_material 'SURFACE • worn_plaster_wall' (the gables' plaster)

The result: {'tiles': object, 'timber': object, 'gables': object or None, 'eave_height': the world height of the
front eave's lowest edge at its middle}. The tool also writes on the box what lay_veranda needs to set its beam under
the eave: 'tile_roof_under' (the roof's underside height in the box's own z, every 0.1 m out from the wall face) and
'tile_roof_eaves' (the sides that have eaves).
"""

import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

import store  # noqa: E402

TILE_MATERIAL = 'SURFACE • dark_rock_02'
TIMBER_MATERIAL = 'SURFACE • old_planks_02'
PLASTER_MATERIAL = 'SURFACE • worn_plaster_wall'
KINDS = ('hip-and-gable', 'hipped', 'gable')
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x', '-y': '-y', '+y': '+y', '-x': '-x', '+x': '+x'}
CURVE = 0.38           # how concave the slope is: the eave slopes (1 - CURVE) of the mean pitch, the top (1 + CURVE)
THICK = 0.16           # the roof's thickness at the eave: tiles, their clay bed and the boarding
WALL_HEAD = 0.30       # the wall-top beam: the roof's underside meets the wall's face this far above the box's top
COURSE = 0.30          # a course of tiles up the slope
STEP = 0.022           # how far each course stands over the one below
DISH = 0.018           # how much a pan tile's middle lies below its edges
ROLL_R = 0.068         # the cover tiles' radius
GABLE_AT = 0.34        # a hip-and-gable roof's gable stands this share of the way up the end slope
RAFTER_W, RAFTER_H = 0.075, 0.095

TOOL = {
    'name': 'lay_tile_roof',
    'what': "puts a Japanese tiled roof on a building (a box you name): hip-and-gable (irimoya), hipped or gable; deep eaves curving up to turned-up corners, courses of pan tiles with half-round cover tiles and round end tiles at the eave, a heavy stacked ridge with ornamental end tiles, hips or gable edges in smaller stacks; rafters, boarding, an eaves board and wall-top beams under the eaves; plaster gables in a timber frame with bargeboards; a small gable on the front slope if asked",
    'call': "lay_tile_roof.lay(inn, kind='hip-and-gable', overhang=1.1, pitch=28, lift=0.35, front_gable=2.6, seed=2)",
    'options': {
        'kind': "'hip-and-gable' (default; irimoya: four slopes, a small upright gable high on each end), 'hipped' (yosemune: four slopes to a short ridge) or 'gable' (kirizuma: two slopes, an upright gable at each end)",
        'overhang': "metres the eaves reach past the walls (default 1.0; a gable roof's gable ends reach 0.6 of it)",
        'pitch': "the slope's mean pitch in degrees, 20 to 45 (default 28); the slope curves: about 0.65 of it at the eave, 1.35 near the ridge",
        'lift': "metres the eaves rise towards each corner (default 0.3; 0 a straight eave, 0.8 at most)",
        'ridge': "'long' (along the box's longer side), 'front' (parallel to the front) or 'side' (default 'long'); a hipped or hip-and-gable roof's ridge must run along the longer side",
        'front_gable': "the width in metres of a small gable standing on the front slope over an entrance (default None: none)",
        'gable_at': "metres along the front from its left end to the small gable's middle (default None: the middle)",
        'tile': "the spacing of the rows of cover tiles, metres (default 0.28)",
        'rafters': "the rafters' spacing under the eaves, metres (default 0.42; 0 none)",
        'seed': "each tile's part of the picture and shade, the cover tiles' small set (default 0)",
        'collection': "where the objects go (default a new collection 'lay_tile_roof')",
        'tile_material': "the tiles and ridges (default '%s'; the tool lays a darker, wet copy with a finer grain, 'lay_tile_roof • <name>')" % TILE_MATERIAL,
        'timber_material': "rafters, boarding, eaves boards, beams, bargeboards, the gables' frame (default '%s'; the members lying along X or Y get its copies turned so the grain runs along them)" % TIMBER_MATERIAL,
        'plaster_material': "the gables' plaster (default '%s')" % PLASTER_MATERIAL,
    },
    'materials': [TILE_MATERIAL, TIMBER_MATERIAL, PLASTER_MATERIAL],
    'source': "roof() in '/home/claude/build-57-garden/first pass/render_final.py' (line 1218: one front slope, concave, its ends lifted, rolls of tiles as tubes, round ends as cylinders, rafters, a ridge with two horns) and its front gable (lines 1289-1312), rebuilt as a tool: every slope of a hipped, hip-and-gable or gable roof from one curved surface, corners lifted on both slopes so the hips stay true, pan tiles laid in stepped courses with a half-round cover tile per course, each tile its own part of the photographed surface; stacked ridges with onigawara; underside, rafters, wall-top beams, gables and bargeboards as the board's photographs 03, 05, 06 and 10 show them",
    'trap': "the roof starts 0.3 m above the box's top (the wall-top beam) and its eaves hang about 0.3 m lower than that 1 m out: a door or veranda under them must be lower; lay the roof before lay_veranda, which reads the eave's height from the box; the ridge of a hipped or hip-and-gable roof runs along the box's longer side",
}


# ----------------------------------------------------------------------------------------------- the mesh builder

class Build:
    """Vertices, faces, a material slot and a piece number (pp_piece) per face, in the roof's frame."""

    def __init__(self):
        self.verts, self.faces, self.slots, self.pieces = [], [], [], []

    def face(self, points, slot=0, piece=0.5):
        start = len(self.verts)
        self.verts.extend(tuple(p) for p in points)
        self.faces.append(tuple(range(start, start + len(points))))
        self.slots.append(slot)
        self.pieces.append(piece)

    def rings(self, rings, slot, piece, closed=False, caps=True):
        """Faces between successive rings of points (each ring the same length); caps close the ends."""
        n = len(rings[0])
        start = len(self.verts)
        for ring in rings:
            self.verts.extend(tuple(p) for p in ring)
        last = n if closed else n - 1
        for r in range(len(rings) - 1):
            for i in range(last):
                j = (i + 1) % n
                a, b = start + r * n + i, start + r * n + j
                self.faces.append((a, b, b + n, a + n))
                self.slots.append(slot)
                self.pieces.append(piece)
        if caps:
            self.faces.append(tuple(start + i for i in reversed(range(n))))
            self.faces.append(tuple(start + (len(rings) - 1) * n + i for i in range(n)))
            self.slots.extend([slot, slot])
            self.pieces.extend([piece, piece])

    def sweep(self, path, section, slot, piece, up=Vector((0.0, 0.0, 1.0)), caps=True):
        """A closed section of (side, up) offsets carried along a path of points."""
        path = [Vector(p) for p in path]
        rings = []
        for i, p in enumerate(path):
            a = path[max(i - 1, 0)]
            b = path[min(i + 1, len(path) - 1)]
            tangent = (b - a).normalized()
            side = tangent.cross(up)
            if side.length < 1e-6:
                side = tangent.cross(Vector((1.0, 0.0, 0.0)))
            side.normalize()
            upward = side.cross(tangent).normalized()
            rings.append([p + side * s + upward * h for s, h in section])
        self.rings(rings, slot, piece, closed=True, caps=caps)

    def beam(self, a, b, width, height, slot, piece, up=Vector((0.0, 0.0, 1.0))):
        """A rectangular member from a to b (the middle of its top face on the line), its top towards `up`."""
        self.sweep([a, b], [(-width / 2, 0.0), (width / 2, 0.0), (width / 2, -height), (-width / 2, -height)], slot, piece, up=up)

    def disc(self, centre, axis, radius, thick, slot, piece, segments=12):
        axis = Vector(axis).normalized()
        side = axis.cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 1e-6:
            side = axis.cross(Vector((1.0, 0.0, 0.0)))
        side.normalize()
        upward = side.cross(axis).normalized()
        ring = [side * (radius * math.cos(2 * math.pi * k / segments)) + upward * (radius * math.sin(2 * math.pi * k / segments)) for k in range(segments)]
        c = Vector(centre)
        self.rings([[c + q for q in ring], [c + axis * thick + q for q in ring]], slot, piece, closed=True)

    def make(self, name, materials, collection, frame, ground):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', self.slots)
        attribute = mesh.attributes.new('pp_piece', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.pieces)
        mesh.validate(clean_customdata=False)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.matrix_world = frame
        store.mark(obj, ground=ground)
        return obj


def _material(value):
    return store.material(value) if isinstance(value, str) else value


def tile_copy(material):
    """A darker, wet copy of a photographed material with a finer grain, for fired clay tiles (made once)."""
    name = 'lay_tile_roof • %s' % material.name.split(' • ')[-1]
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    copy = material.copy()
    copy.name = name
    nodes = copy.node_tree.nodes if copy.node_tree else None
    weather = nodes.get('Weather') if nodes else None
    if weather is not None:
        for dial, value in (('Wet', 0.55), ('Edge wear', 0.0), ('Grime', 0.25), ('Darken', 0.8)):
            if dial in weather.inputs:
                weather.inputs[dial].default_value = value
        # fired clay tiles are a cool silver-grey: take most of the rock's own colour out and cool what is left
        tree = copy.node_tree
        bsdf = next((n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
        link = next((l for l in tree.links if bsdf is not None and l.to_node == bsdf and l.to_socket.name == 'Base Color'), None)
        if link is not None:
            grey = nodes.new('ShaderNodeHueSaturation')
            grey.name = grey.label = 'Tile grey'
            grey.inputs['Saturation'].default_value = 0.08
            grey.inputs['Value'].default_value = 0.8
            cool = nodes.new('ShaderNodeMix')
            cool.name = cool.label = 'Tile cool'
            cool.data_type = 'RGBA'
            cool.blend_type = 'MULTIPLY'
            cool.inputs['Factor'].default_value = 1.0
            cool.inputs[7].default_value = (0.72, 0.84, 1.0, 1.0)
            source = link.from_socket
            tree.links.new(source, grey.inputs['Color'])
            tree.links.new(grey.outputs['Color'], cool.inputs[6])
            tree.links.new(cool.outputs[2], bsdf.inputs['Base Color'])
    size = nodes.get('Picture size') if nodes else None
    if size is not None and 'Scale' in size.inputs:
        size.inputs['Scale'].default_value = size.inputs['Scale'].default_value * 2.5
    return copy


def timber_copy(material):
    """A darker, grimier copy of a photographed timber for the roof's old, sooted wood (made once)."""
    name = 'lay_tile_roof • %s' % material.name.split(' • ')[-1]
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    copy = material.copy()
    copy.name = name
    weather = copy.node_tree.nodes.get('Weather') if copy.node_tree else None
    if weather is not None:
        for dial, value in (('Darken', 0.5), ('Grime', 0.6), ('Wet', 0.15)):
            if dial in weather.inputs:
                weather.inputs[dial].default_value = value
    return copy


def plaster_copy(material):
    """A paler, cleaner copy of a photographed plaster for the gables' lime plaster (made once)."""
    name = 'lay_tile_roof • %s' % material.name.split(' • ')[-1]
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    copy = material.copy()
    copy.name = name
    weather = copy.node_tree.nodes.get('Weather') if copy.node_tree else None
    if weather is not None:
        for dial, value in (('Darken', 1.35), ('Grime', 0.2)):
            if dial in weather.inputs:
                weather.inputs[dial].default_value = value
    return copy


def turned(material, axis):
    try:
        import lay_stone
        return lay_stone.turned_along(material, axis)
    except Exception:
        return material


# ----------------------------------------------------------------------------------------------- the roof

def lay(box, kind='hip-and-gable', overhang=1.0, pitch=28.0, lift=0.3, ridge='long', front_gable=None, gable_at=None,
        tile=0.28, rafters=0.42, seed=0, collection=None, tile_material=TILE_MATERIAL, timber_material=TIMBER_MATERIAL,
        plaster_material=PLASTER_MATERIAL):
    """Roof the box (see the note at the top). Returns {'tiles', 'timber', 'gables', 'eave_height'}."""
    if box is None or box.type != 'MESH':
        raise ValueError('lay_tile_roof needs a mesh object (the building)')
    if kind not in KINDS:
        raise ValueError("kind is 'hip-and-gable', 'hipped' or 'gable', not %r" % (kind,))
    if ridge not in ('long', 'front', 'side'):
        raise ValueError("ridge is 'long', 'front' or 'side', not %r" % (ridge,))
    overhang = float(overhang)
    if not 0.3 <= overhang <= 3.0:
        raise ValueError('overhang is 0.3 to 3 m, not %r' % (overhang,))
    pitch = float(pitch)
    if not 20.0 <= pitch <= 45.0:
        raise ValueError('pitch is 20 to 45 degrees, not %r' % (pitch,))
    lift = float(lift)
    if not 0.0 <= lift <= 0.8:
        raise ValueError('lift is 0 to 0.8 m, not %r' % (lift,))
    tile = float(tile)
    if not 0.2 <= tile <= 0.4:
        raise ValueError('tile is 0.2 to 0.4 m, not %r' % (tile,))
    rafters = float(rafters or 0.0)
    if rafters and not 0.25 <= rafters <= 1.2:
        raise ValueError('rafters is a spacing of 0.25 to 1.2 m (or 0 for none), not %r' % (rafters,))
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    location, rotation, _ = box.matrix_world.decompose()
    box_frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_box = box_frame.inverted()
    corners = [to_box @ (box.matrix_world @ Vector(c)) for c in box.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    size_x, size_y = high.x - low.x, high.y - low.y
    along_x = size_x >= size_y if ridge == 'long' else ridge == 'front'
    turn = Matrix.Identity(4) if along_x else Matrix.Rotation(-math.pi / 2, 4, 'Z')
    centre = (low + high) / 2
    frame = box_frame @ Matrix.Translation(Vector((centre.x, centre.y, 0.0))) @ turn
    ground = location.z + low.z
    hx, hy = (size_x / 2, size_y / 2) if along_x else (size_y / 2, size_x / 2)
    if kind != 'gable' and hx < hy - 1e-6:
        raise ValueError("a %s roof's ridge runs along the box's longer side: give ridge='long'" % kind)
    top = high.z
    ov = overhang
    X = hx + (0.6 * ov if kind == 'gable' else ov)
    Y = hy + ov
    tan_p = math.tan(math.radians(pitch))
    H = Y * tan_p

    def p(t):
        return (1 - CURVE) * t + CURVE * t * t

    z0 = top + WALL_HEAD + THICK - H * p(ov / Y)
    ramp = max(1.5, min(5.0, 0.38 * min(2 * X, 2 * Y) + 0.8))

    def Zp(d):
        return z0 + H * p(max(0.0, min(d, Y)) / Y)

    def lifted(u, v, d):
        if lift <= 0:
            return 0.0
        if kind == 'gable':
            w = max(0.0, 1.0 - v / ramp) ** 2
        else:
            w = max(0.0, 1.0 - (u + v) / ramp) ** 2
        return lift * w * max(0.0, 1.0 - d / Y) ** 1.2

    # --- the slopes: each a function (a along the eave, d up from the eave) -> point, with its limits
    slopes = []

    def front_slope(sign, a_lo, a_hi, d_lo, d_hi, eave):
        def pos(a, d):
            v = X - abs(a)
            return Vector((a, sign * (Y - d), Zp(d) + lifted(d, v, d)))
        slopes.append({'pos': pos, 'a': (a_lo, a_hi), 'dlo': d_lo, 'dhi': d_hi, 'eave': eave, 'flip': sign > 0, 'axis': 'y'})

    def end_slope(sign, top_d):
        def pos(a, d):
            u = Y - abs(a)
            return Vector((sign * (X - d), a, Zp(d) + lifted(u, d, d)))
        slopes.append({'pos': pos, 'a': (-Y, Y), 'dlo': lambda a: 0.0, 'dhi': lambda a, t=top_d: min(t, Y - abs(a)),
                       'eave': True, 'flip': sign < 0, 'axis': 'x'})

    dg = GABLE_AT * Y
    Xg = X - dg
    og = min(0.45, 0.8 * dg)
    for sign in (-1, 1):
        if kind == 'hipped':
            front_slope(sign, -X, X, lambda a: 0.0, lambda a: min(Y, X - abs(a)), True)
            end_slope(sign, Y)
        elif kind == 'hip-and-gable':
            front_slope(sign, -X, X, lambda a: 0.0, lambda a: min(dg, X - abs(a)), True)
            front_slope(sign, -(Xg + og), Xg + og, lambda a: dg, lambda a: Y, False)
            end_slope(sign, dg)
        else:
            front_slope(sign, -X, X, lambda a: 0.0, lambda a: Y, True)

    # --- a small gable on the front slope
    small = None
    if front_gable:
        if not along_x:
            raise ValueError("the small gable stands on the front slope: the ridge must run parallel to the front (ridge='front', or 'long' on a box wider than deep)")
        width = float(front_gable)
        if not 1.0 <= width <= 2 * hx:
            raise ValueError('front_gable is a width of 1 m up to the front\'s length (%.2f m), not %r' % (2 * hx, front_gable))
        gx = 0.0
        if gable_at is not None:
            gx = float(gable_at) - hx
        width = max(1.0, min(width, 0.7 * 2 * hx))
        gx = max(-hx + width / 2, min(hx - width / 2, gx))
        ug = ov + 0.35                       # its foot stands on the slope just inside the wall's line
        g_pitch = math.radians(42.0)
        z_base = Zp(ug)
        half = width / 2
        z_apex = z_base + half * math.tan(g_pitch)
        if z_apex > Zp(Y) - 0.15:
            half = (Zp(Y) - 0.15 - z_base) / math.tan(g_pitch)
            z_apex = Zp(Y) - 0.15
        # where its ridge meets the main slope
        u_end = ug
        while u_end < Y and Zp(u_end) < z_apex:
            u_end += 0.02
        small = {'x': gx, 'half': half, 'u0': ug, 'u1': u_end, 'z_base': z_base, 'z_apex': z_apex, 'tan': math.tan(g_pitch)}

    def under_small(x, u):
        """True where the small gable covers the main front slope."""
        if small is None:
            return False
        t = abs(x - small['x'])
        return u > small['u0'] - 0.05 and t < small['half'] + 0.05 and small['z_apex'] - t * small['tan'] > Zp(u) - 0.02

    tiles, timber, plaster = Build(), Build(), Build()
    # timber slots: 0 plain (posts, upright), 1 grain along x, 2 grain along y
    piece = rng.random

    def lay_tiles(slope, is_front_main):
        a_lo, a_hi = slope['a']
        pos, dlo, dhi = slope['pos'], slope['dlo'], slope['dhi']
        rolls = []
        k = math.ceil((a_lo + 0.06) / tile)
        while k * tile < a_hi - 0.06:
            rolls.append(k * tile)
            k += 1
        edges = [a_lo] + rolls + [a_hi]
        top_d = max(dhi(a) for a in (a_lo, (a_lo + a_hi) / 2, a_hi, 0.0) if a_lo <= a <= a_hi)
        courses = int(math.ceil(top_d / COURSE)) + 1

        def normal(a, d):
            e = 0.02
            ta = pos(a + e, d) - pos(a - e, d)
            td = pos(a, d + e) - pos(a, d - e)
            n = ta.cross(td).normalized()
            return n if n.z > 0 else -n

        # pan tiles, one quad per tile, each course stepping over the one below
        for c in range(len(edges) - 1):
            a0, a1 = edges[c], edges[c + 1]
            if a1 - a0 < 0.02:
                continue
            for j in range(courses):
                d0, d1 = j * COURSE, (j + 1) * COURSE
                l0, l1 = max(d0, dlo(a0)), max(d0, dlo(a1))
                u0, u1 = min(d1, dhi(a0)), min(d1, dhi(a1))
                if u0 <= l0 + 0.01 and u1 <= l1 + 0.01:
                    continue
                u0, u1 = max(u0, l0), max(u1, l1)
                mid = (a0 + a1) / 2
                if is_front_main and under_small(mid, (l0 + u0) / 2):
                    continue
                n0, n1 = normal(a0, l0), normal(a1, l1)
                lo0 = pos(a0, l0) + n0 * STEP
                lo1 = pos(a1, l1) + n1 * STEP
                hi0, hi1 = pos(a0, u0), pos(a1, u1)
                pc = piece()
                # a pan tile is dished: its middle lies a little lower than its edges under the cover tiles
                am = (a0 + a1) / 2
                lm, um = (l0 + l1) / 2, (u0 + u1) / 2
                nm = normal(am, lm)
                lom = pos(am, lm) + nm * (STEP - DISH)
                him = pos(am, um) - nm * DISH
                for quad in ([lo0, lom, him, hi0], [lom, lo1, hi1, him]):
                    tiles.face(quad if not slope['flip'] else list(reversed(quad)), 0, pc)
                drop = 0.06 if (slope['eave'] and l0 < 0.01 and l1 < 0.01) else STEP
                bottom_m = pos(am, lm) - nm * (drop - STEP + DISH)
                for lip in ([pos(a0, l0) - n0 * (drop - STEP), bottom_m, lom, lo0], [bottom_m, pos(a1, l1) - n1 * (drop - STEP), lo1, lom]):
                    tiles.face(lip if not slope['flip'] else list(reversed(lip)), 0, pc)
        # cover tiles, a half-round per course, and a round end tile at the eave
        seg = 6
        for a in rolls:
            lo, hi = dlo(a), dhi(a)
            if hi - lo < 0.06:
                continue
            j = int(lo // COURSE)
            while j * COURSE < hi - 0.02:
                d0, d1 = max(j * COURSE, lo), min((j + 1) * COURSE, hi)
                j += 1
                if d1 - d0 < 0.03:
                    continue
                if is_front_main and under_small(a, (d0 + d1) / 2):
                    continue
                wob = (rng.random() - 0.5) * 0.012
                rings = []
                for d, scale in ((d0, 1.10), (d0 + 0.03, 1.0), (d1, 1.0)):
                    if d > d1:
                        continue
                    cpos = pos(a + wob, d)
                    n = normal(a, d)
                    along = (pos(a, d + 0.01) - pos(a, d - 0.01)).normalized()
                    side = along.cross(n).normalized()
                    r = ROLL_R * scale
                    rings.append([cpos + n * (ROLL_R * 0.25) + side * (r * math.cos(math.pi * q / seg)) + n * (r * math.sin(math.pi * q / seg)) for q in range(seg + 1)])
                if len(rings) >= 2:
                    tiles.rings(rings, 0, piece(), closed=False, caps=False)
            if slope['eave'] and lo < 0.01:
                c0 = pos(a, 0.0)
                n = normal(a, 0.0)
                along = (pos(a, 0.02) - c0).normalized()
                tiles.disc(c0 + n * (ROLL_R * 0.3) - along * 0.04, along, ROLL_R * 1.22, 0.05, 0, piece())

    def lay_underside(slope):
        """The boarding under the overhang, the rafters, the eaves board."""
        a_lo, a_hi = slope['a']
        pos, dhi = slope['pos'], slope['dhi']
        reach = ov + 0.06
        steps = max(8, int((a_hi - a_lo) / 0.25))
        rings = []
        for i in range(steps + 1):
            a = a_lo + (a_hi - a_lo) * i / steps
            dd = min(reach, dhi(a))
            row = [pos(a, dd * q / 4) - Vector((0, 0, THICK)) for q in range(5)]
            rings.append(row)
        timber.rings(rings, 1 if slope['axis'] == 'y' else 2, piece(), closed=False, caps=False)
        # the eaves board along the edge, following the lift
        path = [pos(a_lo + (a_hi - a_lo) * i / steps, min(0.07, max(0.0, dhi(a_lo + (a_hi - a_lo) * i / steps)))) for i in range(steps + 1)]
        eave_dir = Vector((0, 0, -1))
        board = [p + eave_dir * 0.0 for p in path]
        rings = []
        for p in board:
            rings.append([p + Vector((0, 0, -0.015)), p + Vector((0, 0, -THICK - 0.06))])
        flat = [[r[0], r[1]] for r in rings]
        # give the board some thickness inward (towards the wall)
        inward = (pos(0.0 if a_lo < 0 < a_hi else a_lo, 0.1) - pos(0.0 if a_lo < 0 < a_hi else a_lo, 0.0))
        inward.z = 0
        inward = inward.normalized() * 0.05
        full = [[r[0], r[1], r[1] + inward, r[0] + inward] for r in flat]
        timber.rings(full, 1 if slope['axis'] == 'y' else 2, piece(), closed=True, caps=True)
        if rafters:
            a = a_lo + rafters / 2
            while a < a_hi - 0.05:
                dd = min(ov, dhi(a))
                if dd > 0.12:
                    pa, pb = pos(a, 0.02) - Vector((0, 0, THICK)), pos(a, dd + 0.05) - Vector((0, 0, THICK))
                    timber.beam(pa, pb, RAFTER_W, RAFTER_H, 2 if slope['axis'] == 'y' else 1, piece())
                a += rafters

    for slope in slopes:
        main_front = slope['axis'] == 'y' and not slope['flip'] and slope['dlo'](0.0) == 0.0
        lay_tiles(slope, main_front and small is not None)
        if slope['eave']:
            lay_underside(slope)

    # --- ridges: stacked plates with a round cap; ornamental end tiles
    def stack(path, wide=True):
        tiers = [(0.36, 0.08), (0.32, 0.08), (0.28, 0.08)] if wide else [(0.26, 0.07), (0.22, 0.07)]
        z = 0.0
        for w, h in tiers:
            sec = [(-w / 2, z), (w / 2, z), (w / 2, z + h), (-w / 2, z + h)]
            tiles.sweep(path, [(s, hh) for s, hh in sec], 0, piece())
            z += h
        r = 0.085 if wide else 0.07
        cap = [(r * math.cos(math.pi * q / 6), z - 0.02 + r * math.sin(math.pi * q / 6)) for q in range(7)]
        tiles.sweep(path, cap, 0, piece())
        return z + r

    def onigawara(at, facing, scale=1.0):
        """An ornamental end tile: a shield with two horns, standing at `at`, its face looking along `facing`."""
        outline = [(-0.25, 0.0), (0.25, 0.0), (0.27, 0.28), (0.34, 0.56), (0.17, 0.43), (0.0, 0.5), (-0.17, 0.43), (-0.34, 0.56), (-0.27, 0.28)]
        f = Vector(facing).normalized()
        side = f.cross(Vector((0, 0, 1))).normalized()
        at = Vector(at)
        centre2 = (0.0, 0.25)
        back = [at + side * (x * scale) + Vector((0, 0, y * scale)) - f * (0.07 * scale) for x, y in outline]
        front = [at + side * (x * scale) + Vector((0, 0, y * scale)) + f * (0.07 * scale) for x, y in outline]
        tiles.rings([back, front], 0, piece(), closed=True, caps=False)
        pc = piece()
        for ring, rev in ((front, False), (back, True)):
            mid = at + side * (centre2[0] * scale) + Vector((0, 0, centre2[1] * scale)) + (f if not rev else -f) * (0.07 * scale)
            for i in range(len(ring)):
                tri = [mid, ring[i], ring[(i + 1) % len(ring)]]
                tiles.face(tri if not rev else list(reversed(tri)), 0, pc)

    def surface_line(points_fn, n=14):
        return [points_fn(i / n) for i in range(n + 1)]

    ridge_z = Zp(Y)
    if kind == 'hipped':
        xr = max(0.0, X - Y)
        r_path = [Vector((-xr + 2 * xr * i / 10, 0.0, ridge_z)) for i in range(11)] if xr > 0.05 else []
        for sx in (-1, 1):
            for sy in (-1, 1):
                path = surface_line(lambda t, sx=sx, sy=sy: Vector((sx * (X - Y * (1 - t)), sy * (Y - Y * (1 - t)), Zp(Y * (1 - t)) + lifted(Y * (1 - t), Y * (1 - t), Y * (1 - t)))))
                path = [Vector((pp.x, pp.y, pp.z)) for pp in path]
                stack(path, wide=False)
                tip = path[-1]
                onigawara(tip + Vector((0, 0, 0.1)), Vector((sx, sy, 0)), 0.55)
        ends = [Vector((-xr, 0, ridge_z)), Vector((xr, 0, ridge_z))]
    elif kind == 'hip-and-gable':
        xr = Xg + og
        r_path = [Vector((-xr + 2 * xr * i / 12, 0.0, ridge_z)) for i in range(13)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                # down the gable's edge, from the ridge to the gable's foot
                xe = sx * (xr - 0.16)
                path = surface_line(lambda t, xe=xe, sy=sy: Vector((xe, sy * (Y - (Y - (Y - dg) * t)), Zp(Y - (Y - dg) * t) + 0.02)), 10)
                stack(path, wide=False)
                onigawara(path[-1] + Vector((0, 0, 0.12)), Vector((0, sy, 0)), 0.5)
                # the corner ridge, from the gable's foot down the hip to the corner
                path = surface_line(lambda t, sx=sx, sy=sy: Vector((sx * (X - dg * (1 - t)), sy * (Y - dg * (1 - t)), Zp(dg * (1 - t)) + lifted(dg * (1 - t), dg * (1 - t), dg * (1 - t)))), 10)
                stack(path, wide=False)
                onigawara(path[-1] + Vector((0, 0, 0.1)), Vector((sx, sy, 0)), 0.55)
            # a low ridge along the gable's foot
            foot = [Vector((sx * (Xg + 0.08), -(Y - dg) + 2 * (Y - dg) * i / 8, Zp(dg))) for i in range(9)]
            stack(foot, wide=False)
        ends = [Vector((-xr, 0, ridge_z)), Vector((xr, 0, ridge_z))]
    else:
        xr = X
        r_path = [Vector((-xr + 2 * xr * i / 12, 0.0, ridge_z)) for i in range(13)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                xe = sx * (X - 0.16)
                path = surface_line(lambda t, xe=xe, sy=sy: Vector((xe, sy * (Y * t), Zp(Y * (1 - t)) + lifted(Y * (1 - t), 0.16, Y * (1 - t)) + 0.02)), 12)
                stack(path, wide=False)
        ends = [Vector((-xr, 0, ridge_z)), Vector((xr, 0, ridge_z))]
    if r_path:
        height = stack(r_path, wide=True)
        big = max(1.0, min(1.6, 2 * X / 9.0))
        for e, sx in zip(ends, (-1, 1)):
            onigawara(e + Vector((sx * 0.05, 0, height - 0.08)), Vector((sx, 0, 0)), big)

    # --- the small gable on the front slope
    if small is not None:
        gx, half, u0, u1 = small['x'], small['half'], small['u0'], small['u1']
        za, tg = small['z_apex'], small['tan']
        y_front = -(Y - u0) - 0.25             # its roof reaches 0.25 m in front of its gable face

        def zs(t):
            return za - t * tg

        for sgn in (-1, 1):
            # its slope, bent onto the main slope where it would go under it
            rows = []
            ts = [i / 8 * (half + 0.2) for i in range(9)]
            us = [Y + y_front] + [u0 + (u1 - u0) * q / 8 for q in range(9)]
            for u in us:
                row = []
                for t in ts:
                    z = max(zs(t), Zp(max(u, 0)) + 0.01)
                    row.append(Vector((gx + sgn * t, -(Y - u), z)))
                rows.append(row)
            tiles.rings(rows, 0, piece(), closed=False, caps=False)
            # its cover tiles run down its slope, sideways
            u = u0 - 0.2
            while u < u1:
                pts = []
                t = 0.0
                while t <= half + 0.2:
                    if zs(t) > Zp(u) + 0.03:
                        pts.append(Vector((gx + sgn * t, -(Y - u), zs(t) + ROLL_R * 0.3)))
                    t += 0.1
                if len(pts) >= 2:
                    sec = [(ROLL_R * math.cos(math.pi * q / 6), ROLL_R * math.sin(math.pi * q / 6)) for q in range(7)]
                    tiles.sweep(pts, sec, 0, piece(), up=Vector((0, 0, 1)))
                u += tile
            # its bargeboard
            path = [Vector((gx + sgn * t, y_front - 0.02, zs(t) + 0.04)) for t in [i / 8 * (half + 0.2) for i in range(9)]]
            timber.sweep(path, [(-0.03, 0.0), (0.03, 0.0), (0.03, -0.26), (-0.03, -0.26)], 0, piece(), up=Vector((0, 1, 0)))
        # its ridge and end tile
        rp = [Vector((gx, y_front + (-(Y - u1) - y_front) * i / 8, za + 0.02)) for i in range(9)]
        h = stack(rp, wide=False)
        onigawara(rp[0] + Vector((0, -0.05, h - 0.1)), Vector((0, -1, 0)), 0.7)
        # its gable face: plaster in a timber frame
        yf = -(Y - u0)
        tri = [Vector((gx - half, yf, small['z_base'] + 0.02)), Vector((gx + half, yf, small['z_base'] + 0.02)), Vector((gx, yf, za - 0.08))]
        plaster.face(tri, 0, piece())
        timber.beam(Vector((gx - half, yf - 0.03, small['z_base'] + 0.16)), Vector((gx + half, yf - 0.03, small['z_base'] + 0.16)), 0.06, 0.14, 1, piece())
        for f in (-0.5, 0.0, 0.5):
            zt = za - abs(f) * half * tg - 0.12
            timber.beam(Vector((gx + f * half, yf - 0.03, zt)), Vector((gx + f * half, yf - 0.03, small['z_base'] + 0.05)), 0.07, 0.05, 0, piece(), up=Vector((0, -1, 0)))

    # --- the gables of a hip-and-gable or gable roof: plaster in a timber frame, bargeboards, a hanging ornament
    if kind in ('hip-and-gable', 'gable'):
        for sx in (-1, 1):
            if kind == 'hip-and-gable':
                xw, z_b, u_b = sx * Xg, Zp(dg) + 0.02, dg
                while Zp(u_b) - THICK < z_b and u_b < Y:
                    u_b += 0.02
                x_edge = sx * (Xg + og)
                u_edge0 = dg
            else:
                xw, z_b, u_b = sx * hx, top, ov
                x_edge = sx * (X + 0.02)
                u_edge0 = 0.0
            outline = []
            outline.append(Vector((xw, -(Y - u_b), z_b)))
            for i in range(13):
                u = u_b + (Y - u_b) * i / 12
                outline.append(Vector((xw, -(Y - u), Zp(u) - THICK)))
            for i in range(11, -1, -1):
                u = u_b + (Y - u_b) * i / 12
                outline.append(Vector((xw, (Y - u), Zp(u) - THICK)))
            outline.append(Vector((xw, (Y - u_b), z_b)))
            mid = Vector((xw, 0.0, (z_b + Zp(Y) - THICK) / 2))
            pc = piece()
            for i in range(len(outline)):
                a, b = outline[i], outline[(i + 1) % len(outline)]
                tri = [mid, a, b] if sx > 0 else [mid, b, a]
                plaster.face(tri, 0, pc)
            # the frame: a tie beam at the foot, upright battens, a beam half way
            off = Vector((sx * 0.03, 0, 0))
            span = Y - u_b
            timber.beam(Vector((xw, -span, z_b + 0.2)) + off, Vector((xw, span, z_b + 0.2)) + off, 0.08, 0.2, 2, piece())
            z_mid = z_b + 0.45 * (Zp(Y) - THICK - z_b)
            w_mid = span * (1 - 0.45) * 0.95
            timber.beam(Vector((xw, -w_mid, z_mid)) + off, Vector((xw, w_mid, z_mid)) + off, 0.07, 0.12, 2, piece())
            for f in (-0.66, -0.33, 0.0, 0.33, 0.66):
                yb = f * span
                zt = Zp(Y - abs(yb)) - THICK - 0.02
                timber.beam(Vector((xw, yb, zt)) + off, Vector((xw, yb, z_b)) + off, 0.07, 0.06, 0, piece(), up=Vector((sx, 0, 0)))
            # bargeboards along both slopes' edges, and the hanging ornament at the apex
            for sy in (-1, 1):
                path = [Vector((x_edge, sy * (Y - u), Zp(u) + 0.05 + (lifted(u, 0.0, u) if kind == 'gable' else 0.0))) for u in [u_edge0 + (Y - u_edge0) * i / 12 for i in range(13)]]
                timber.sweep(path, [(-0.035, 0.0), (0.035, 0.0), (0.035, -0.30), (-0.035, -0.30)], 0, piece(), up=Vector((sx, 0, 0)))
            apex = Vector((x_edge + sx * 0.04, 0.0, Zp(Y) - 0.2))
            orn = [apex + Vector((0, -0.22, 0.05)), apex + Vector((0, 0.22, 0.05)), apex + Vector((0, 0.16, -0.32)), apex + Vector((0, 0.0, -0.42)), apex + Vector((0, -0.16, -0.32))]
            timber.face(orn if sx > 0 else list(reversed(orn)), 0, piece())

    # --- the beam along the top of every wall, under the eaves; a heavy rafter at each hip corner
    for sy in (-1, 1):
        timber.beam(Vector((-hx - 0.12, sy * (hy + 0.06), top + WALL_HEAD)), Vector((hx + 0.12, sy * (hy + 0.06), top + WALL_HEAD)), 0.14, WALL_HEAD + 0.01, 1, piece())
    for sx in (-1, 1):
        timber.beam(Vector((sx * (hx + 0.06), -hy - 0.12, top + WALL_HEAD)), Vector((sx * (hx + 0.06), hy + 0.12, top + WALL_HEAD)), 0.14, WALL_HEAD + 0.01, 2, piece())
    if kind != 'gable':
        for sx in (-1, 1):
            for sy in (-1, 1):
                pa = Vector((sx * hx, sy * hy, Zp(ov) - THICK))
                tip = Vector((sx * X, sy * Y, Zp(0.0) + lifted(0.0, 0.0, 0.0) - THICK))
                timber.beam(pa + (tip - pa) * 0.0, tip + (tip - pa).normalized() * 0.08, 0.13, 0.17, 0, piece())

    if collection is None:
        collection = bpy.data.collections.new('lay_tile_roof')
        bpy.context.scene.collection.children.link(collection)
    tile_mat = tile_copy(_material(tile_material))
    wood = timber_copy(_material(timber_material))
    tiles_obj = tiles.make('roof tiles', [tile_mat], collection, frame, ground)
    timber_obj = timber.make('roof timber', [wood, turned(wood, 'x' if along_x else 'y'), turned(wood, 'y' if along_x else 'x')], collection, frame, ground)
    gables_obj = plaster.make('roof gables', [plaster_copy(_material(plaster_material))], collection, frame, ground) if plaster.faces else None
    for obj in (tiles_obj, timber_obj, gables_obj):
        if obj is not None:
            obj['kind'] = kind
            obj['pitch'] = pitch
            obj['overhang'] = ov
    tiles_obj['tiles'] = sum(1 for _ in tiles.faces)
    # what lay_veranda reads: the underside's height out from the wall face, and which sides have eaves
    box['tile_roof_under'] = [Zp(max(0.0, ov - e)) - THICK for e in [i * 0.1 for i in range(int(ov / 0.1) + 1)]]
    if kind == 'gable':
        eave_sides = ['front', 'back'] if along_x else ['left', 'right']
    else:
        eave_sides = ['front', 'back', 'left', 'right']
    box['tile_roof_eaves'] = ','.join(eave_sides)
    eave_world = (frame @ Vector((0.0, -Y, Zp(0.0) - THICK - 0.05))).z
    return {'tiles': tiles_obj, 'timber': timber_obj, 'gables': gables_obj, 'eave_height': eave_world}


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the building (a box)')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--kind', choices=KINDS, default='hip-and-gable', help='default hip-and-gable')
    parser.add_argument('--overhang', type=float, default=1.0, help='metres the eaves reach past the walls; default 1.0')
    parser.add_argument('--pitch', type=float, default=28.0, help='mean pitch in degrees; default 28')
    parser.add_argument('--lift', type=float, default=0.3, help="metres the corners lift; default 0.3")
    parser.add_argument('--ridge', choices=('long', 'front', 'side'), default='long', help='default long')
    parser.add_argument('--front-gable', type=float, default=None, help='width of a small gable on the front slope; default none')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    box = bpy.data.objects.get(args.object)
    if box is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    made = lay(box, kind=args.kind, overhang=args.overhang, pitch=args.pitch, lift=args.lift, ridge=args.ridge,
               front_gable=args.front_gable, seed=args.seed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s roof: %d tile faces; saved %s' % (args.kind, made['tiles']['tiles'], args.out))


if __name__ == '__main__':
    main()
