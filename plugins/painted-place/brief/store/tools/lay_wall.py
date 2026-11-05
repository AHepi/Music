"""
What this file does: covers one flat plane you name (a wall face, a gable, a panel, a floor) with real bricks or
dressed stone blocks, your choice, standing a little out over the plane, which becomes the mortar seen in the joints.
The courses run level (along the world's horizontal when the plane stands up, along the plane's own X when it lies
flat) and are fitted to the plane: whole courses from bottom to top (each course a little taller or shorter so they come
out whole), the bond kept to the edges with half bricks and closers, blocks cut at the edges, nothing outside the
plane's outline (a gable's slopes cut the units along them). Bricks are real size (215 x 102.5 x 65 mm, 10 mm joints)
in stretcher, English, Flemish or header bond; stone is coursed ashlar, its course heights and block lengths varied,
thin joints, arrises chipped. Every unit is a little off true (set in or out a few millimetres, tipped a hair), its
edges worn, and shows one whole photographed brick or block of its own: its front is mapped into one rectangle of the
set's atlas (UV map 'pp_atlas'), sometimes turned half round, its sides into thin strips at that rectangle's edges, and
it carries its own number 'pp_piece' (0 to 1), which the photographed materials read for its shade.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_wall
    bricks = lay_wall.lay(my_plane, kind='brick', bond='flemish', seed=2)
    stone = lay_wall.lay(other_plane, kind='stone', seed=5)

From the command line:

    python3 lay_wall.py --help
    python3 lay_wall.py --blend IN.blend --object Plane --kind brick --bond english --out OUT.blend

The plane is any mesh whose faces lie in one plane (a single face, or a subdivided one): its outline is the faces'
outer edge. A hole in it (faces left out for a window or a door) is left open: the courses stop a half joint from its
sides, its top and its bottom (the units there cut in height). Unapplied scale and rotation are fine. The units stand on the side its face looks towards (flip=True for the other side).
"""

import argparse
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import store  # noqa: E402

KINDS = ('brick', 'stone')
BONDS = ('stretcher', 'english', 'flemish', 'header')
STRETCHER, HEADER, HEIGHT = 0.215, 0.1025, 0.065          # a brick's face: length, end, height (metres)
BRICK_JOINT, STONE_JOINT = 0.010, 0.005
CLOSER = (HEADER - BRICK_JOINT) / 2                         # a queen closer's face: 46.25 mm
ATLAS_FOLDER = os.path.join(store.STORE, 'materials', 'atlas')
ATLAS_SETS = {'brick': ['brick_wall_02'], 'stone': ['sandstone_blocks_05']}         # the store's atlases (Photographed.md)
MORTAR_MATERIALS = ['SURFACE • rough_plasterbrick_05', 'MORTAR • dark eroded joints']

# Stand-in atlases, used only when the store's own atlas file for a set is missing: thirty whole bricks found in the
# shelf's brick_wall_02 colour picture (by its pale mortar), and the whole sandstone_cracks picture for stone blocks.
STAND_IN = {
    'brick_wall_02': {'set': 'brick_wall_02', 'material': None, 'picture_size_m': [2.0, 2.0], 'units': [
        [0.0176, 0.9502, 0.1387, 0.9814], [0.2979, 0.9541, 0.415, 0.9902], [0.3779, 0.9033, 0.4971, 0.9365],
        [0.7949, 0.9033, 0.9248, 0.9346], [0.0938, 0.8018, 0.2031, 0.834], [0.5088, 0.8037, 0.6348, 0.8379],
        [0.082, 0.7012, 0.1934, 0.7314], [0.8027, 0.7031, 0.9258, 0.7334], [0.3672, 0.6025, 0.4912, 0.6289],
        [0.2139, 0.499, 0.3379, 0.5352], [0.3564, 0.499, 0.4775, 0.5332], [0.4941, 0.499, 0.6104, 0.5293],
        [0.7891, 0.498, 0.9141, 0.5293], [0.1426, 0.4512, 0.2666, 0.4834], [0.21, 0.3994, 0.3203, 0.4326],
        [0.3564, 0.3984, 0.4746, 0.4326], [0.5068, 0.3984, 0.624, 0.4336], [0.6455, 0.4072, 0.7676, 0.4307],
        [0.79, 0.4023, 0.8994, 0.4297], [0.0166, 0.3545, 0.126, 0.3848], [0.291, 0.3516, 0.4014, 0.3809],
        [0.5635, 0.3496, 0.6885, 0.3838], [0.7178, 0.3545, 0.834, 0.3838], [0.3594, 0.2979, 0.4756, 0.3281],
        [0.6436, 0.3008, 0.7666, 0.333], [0.7871, 0.2998, 0.9072, 0.333], [0.1621, 0.252, 0.2812, 0.2812],
        [0.7266, 0.25, 0.8389, 0.2842], [0.79, 0.2031, 0.9131, 0.2305], [0.5732, 0.1514, 0.6982, 0.1816]]},
    'sandstone_cracks': {'set': 'sandstone_cracks', 'material': None, 'picture_size_m': [2.0, 2.0], 'units': [[0.0, 0.0, 1.0, 1.0]]},
}
STAND_IN_FOR = {'brick': 'brick_wall_02', 'stone': 'sandstone_cracks'}

TOOL = {
    'name': 'lay_wall',
    'what': 'covers one flat plane you name, of any size, standing or lying, with real bricks or dressed stone blocks in level courses fitted to it, each unit showing its own photographed brick or block, the plane becoming the mortar in the joints',
    'call': "lay_wall.lay(plane, kind='brick', bond='flemish', seed=2)  /  lay_wall.lay(plane, kind='stone', seed=5)",
    'options': {
        'plane': 'a mesh whose faces lie in one plane: its outline is covered, holes in it (a window, a door) left open; unapplied scale and rotation are fine (required)',
        'kind': "'brick' (215 x 102.5 x 65 mm bricks, 10 mm joints) or 'stone' (coursed ashlar blocks, 5 mm joints) (default 'brick')",
        'bond': "for bricks: 'stretcher', 'english', 'flemish' or 'header' (default 'stretcher')",
        'seed': 'the same seed lays the same wall: which photographed brick or block each unit shows, its wear, the stone lengths (default 0)',
        'course': 'for stone: about how tall a course is, metres; each course 0.75 to 1.3 of it, fitted to the plane (default 0.30)',
        'relief': 'how far the units\' faces stand out from the plane, metres (default 0.012 for brick, 0.02 for stone)',
        'wear': 'how far off true each unit is (set in or out, tipped) and how worn and chipped its edges: 0 laid true and sharp, 1 normal, up to 2 (default 1.0)',
        'atlas': "the photographed set whose atlas the units are mapped into: a set name with a file in store/materials/atlas/ ('brick_wall_02' old red brick, 'brick_wall_10', 'sandstone_blocks_05' sandstone blocks), a path to such a file, or its contents as a dict (default: %s for brick, %s for stone)" % (ATLAS_SETS['brick'][0], ATLAS_SETS['stone'][0]),
        'material': "the units' material (default None: the atlas file's own: 'BRICK • brick_wall_02' for brick, 'ASHLAR • sandstone_blocks_05' for stone; a material of your own must read the UV map 'pp_atlas')",
        'mortar_material': "the plane becomes this, seen in the joints (default 'SURFACE • rough_plasterbrick_05', the photographed lime mortar; None leaves the plane's own)",
        'flip': "lay the units on the other side of the plane, the side its face looks away from (default False)",
        'collection': "where the object 'wall units' goes (default a new collection 'lay_wall')",
    },
    'materials': ['BRICK • brick_wall_02', 'ASHLAR • sandstone_blocks_05', 'SURFACE • rough_plasterbrick_05', 'BRICK • brick_wall_10'],
    'source': 'made for the store (decision 80): the owner asked for a brick wall that "auto adjusts to size", "based on the 2d area of a single plane", bricks or stone blocks "as a choice"; brick sizes and bonds from British practice; the chipped arrises from lay_stone\'s blocks',
    'trap': 'the units stand on the side the plane\'s face looks towards: if they come out behind it, give flip=True (or turn the plane round); the units are photographed only through the atlas material, so a material of your own must read the UV map \'pp_atlas\' to show whole bricks',
}


# ----------------------------------------------------------------------------------------------- the plane

def _outline_loop(obj):
    """The plane's outline: the outer edge of its faces, as world points in order, and the edges of any holes in it.
    Refuses a mesh whose faces do not lie in one plane."""
    mesh = obj.data
    if len(mesh.polygons) == 0:
        raise ValueError('lay_wall needs a plane with at least one face: %r has none' % obj.name)
    matrix = obj.matrix_world
    normal_matrix = matrix.to_3x3().inverted_safe().transposed()
    biggest = max(mesh.polygons, key=lambda p: p.area)
    normal = (normal_matrix @ biggest.normal).normalized()
    if normal.length < 0.5:
        raise ValueError('the plane %r has no area' % obj.name)
    points = [matrix @ v.co for v in mesh.vertices]
    anchor = points[biggest.vertices[0]]
    size = max((p - anchor).length for p in points) or 1.0
    for polygon in mesh.polygons:
        for index in polygon.vertices:
            if abs((points[index] - anchor).dot(normal)) > max(0.002, size * 1e-4):
                raise ValueError('the faces of %r do not lie in one plane: lay_wall covers one flat plane' % obj.name)
    if len(mesh.polygons) == 1:
        return [points[i] for i in biggest.vertices], [], normal
    count = {}
    for polygon in mesh.polygons:
        for key in polygon.edge_keys:
            count[key] = count.get(key, 0) + 1
    boundary = [k for k, c in count.items() if c == 1]
    neighbours = {}
    for a, b in boundary:
        neighbours.setdefault(a, []).append(b)
        neighbours.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in neighbours:
        if start in seen:
            continue
        loop, previous, current = [start], None, start
        seen.add(start)
        while True:
            options = [n for n in neighbours[current] if n != previous and n not in seen]
            if not options:
                break
            previous, current = current, options[0]
            loop.append(current)
            seen.add(current)
        loops.append(loop)
    if not loops:
        raise ValueError('could not find the outline of %r' % obj.name)
    loops = [loop for loop in loops if len(loop) >= 3]
    if not loops:
        raise ValueError('could not find the outline of %r' % obj.name)
    loops.sort(key=lambda loop: -sum((points[loop[i]] - points[loop[i - 1]]).length for i in range(len(loop))))
    return [points[i] for i in loops[0]], [[points[i] for i in loop] for loop in loops[1:]], normal


def plane_frame(obj, flip=False):
    """The plane's frame: origin, along (the courses' direction), up (across the courses), out (its face's normal, or
    the other way with flip), whether it lies flat, and its outline as (s, t) points counter-clockwise seen from the
    front."""
    loop, hole_loops, normal = _outline_loop(obj)
    if flip:
        normal = -normal
    lying = abs(normal.z) >= 0.7
    if lying:
        along = obj.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))
        along = along - normal * along.dot(normal)
        if along.length < 1e-6:
            along = obj.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
            along = along - normal * along.dot(normal)
    else:
        along = Vector((0.0, 0.0, 1.0)).cross(normal)
    along.normalize()
    up = normal.cross(along).normalized()
    origin = loop[0].copy()
    outline = [((p - origin).dot(along), (p - origin).dot(up)) for p in loop]
    cleaned = []
    for p in outline:
        if not cleaned or math.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) > 1e-6:
            cleaned.append(p)
    if len(cleaned) > 1 and math.hypot(cleaned[0][0] - cleaned[-1][0], cleaned[0][1] - cleaned[-1][1]) <= 1e-6:
        cleaned.pop()
    if _area(cleaned) < 0:
        cleaned.reverse()
    holes = [[((p - origin).dot(along), (p - origin).dot(up)) for p in hole] for hole in hole_loops]
    for hole in holes:
        middle = (sum(p[0] for p in hole) / len(hole), sum(p[1] for p in hole) / len(hole))
        if not _scanline([cleaned], middle[1]) or not any(a <= middle[0] <= b for a, b in _scanline([cleaned], middle[1])):
            raise ValueError('the faces of %r make separate pieces: lay_wall covers one plane (lay each piece on its own)' % obj.name)
    return {'origin': origin, 'along': along, 'up': up, 'out': normal, 'lying': lying, 'outline': cleaned, 'holes': holes}


def _area(polygon):
    return 0.5 * sum(polygon[i - 1][0] * polygon[i][1] - polygon[i][0] * polygon[i - 1][1] for i in range(len(polygon)))


def _convex(polygon):
    sign = 0
    for i in range(len(polygon)):
        a, b, c = polygon[i - 2], polygon[i - 1], polygon[i]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cross) < 1e-9:
            continue
        if sign == 0:
            sign = 1 if cross > 0 else -1
        elif (cross > 0) != (sign > 0):
            return False
    return True


def _scanline(loops, t):
    """Where the line at height t lies inside the outline (and outside its holes): sorted (from, to) pieces. loops is
    the outline and its holes."""
    xs = []
    for polygon in loops:
        for i in range(len(polygon)):
            (s0, t0), (s1, t1) = polygon[i - 1], polygon[i]
            if t0 == t1:
                continue
            if min(t0, t1) <= t < max(t0, t1):
                xs.append(s0 + (t - t0) * (s1 - s0) / (t1 - t0))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def _intersect(a, b):
    out = []
    for p, q in a:
        for r, s in b:
            lo, hi = max(p, r), min(q, s)
            if hi > lo:
                out.append((lo, hi))
    return sorted(out)


def _band(loops, t0, t1):
    """The pieces of the band from t0 to t1 that the outline (less its holes) covers over the band's whole height,
    and the pieces it covers anywhere in the band (the second exact for a convex outline without holes)."""
    heights = [t0 + 1e-6, t1 - 1e-6] + [p[1] for polygon in loops for p in polygon if t0 + 1e-6 < p[1] < t1 - 1e-6]
    inner = None
    low, high = None, None
    for h in heights:
        pieces = _scanline(loops, h)
        inner = pieces if inner is None else _intersect(inner, pieces)
        if pieces:
            low = pieces[0][0] if low is None else min(low, pieces[0][0])
            high = pieces[-1][1] if high is None else max(high, pieces[-1][1])
    outer = [(low, high)] if low is not None else []
    return inner or [], outer


def _subtract(pieces, minus):
    """The (from, to) pieces less every piece in minus."""
    out = []
    for p, q in pieces:
        current = [(p, q)]
        for r, t in minus:
            kept = []
            for a, b in current:
                if t <= a or r >= b:
                    kept.append((a, b))
                    continue
                if r > a:
                    kept.append((a, r))
                if t < b:
                    kept.append((t, b))
            current = kept
        out.extend(current)
    return [(a, b) for a, b in out if b - a > 1e-6]


def _clip(subject, clipper):
    """Sutherland-Hodgman: the subject polygon cut to a convex clipper (both counter-clockwise)."""
    output = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i - 1], clipper[i]
        source, output = output, []
        if not source:
            break

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12

        def crossing(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = dx * ey - dy * ex
            if abs(den) < 1e-15:
                return q
            k = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
            return (p[0] + k * dx, p[1] + k * dy)
        for j in range(len(source)):
            p, q = source[j - 1], source[j]
            if inside(q):
                if not inside(p):
                    output.append(crossing(p, q))
                output.append(q)
            elif inside(p):
                output.append(crossing(p, q))
    return output


def _inset(polygon, amount, limit=3.0):
    """A convex counter-clockwise polygon moved inwards by amount (mitred corners, each move at most limit x amount)."""
    n = len(polygon)
    result = []
    for i in range(n):
        p0, p1, p2 = polygon[i - 1], polygon[i], polygon[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1])
        e2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*e1) or 1.0, math.hypot(*e2) or 1.0
        n1 = (-e1[1] / l1, e1[0] / l1)
        n2 = (-e2[1] / l2, e2[0] / l2)
        bis = (n1[0] + n2[0], n1[1] + n2[1])
        dot = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        if dot < 1e-6:
            move = (n1[0] * amount, n1[1] * amount)
        else:
            move = (bis[0] * amount / dot, bis[1] * amount / dot)
        length = math.hypot(*move)
        if length > limit * amount:
            move = (move[0] * limit * amount / length, move[1] * limit * amount / length)
        result.append((p1[0] + move[0], p1[1] + move[1]))
    return result


def _tidy(polygon, nearest):
    out = []
    for p in polygon:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > nearest:
            out.append(p)
    while len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= nearest:
        out.pop()
    return out


# ----------------------------------------------------------------------------------------------- the atlas

def read_atlas(atlas, kind):
    """The atlas as a dict (set, material, picture_size_m, units, maybe kinds)."""
    if isinstance(atlas, dict):
        data = dict(atlas)
    else:
        names = [atlas] if atlas is not None else ATLAS_SETS[kind]
        data = None
        for name in names:
            path = name if str(name).endswith('.json') or os.sep in str(name) else os.path.join(ATLAS_FOLDER, '%s.json' % name)
            if os.path.exists(path):
                with open(path, encoding='utf-8') as handle:
                    data = json.load(handle)
                break
            if name in STAND_IN:
                data = dict(STAND_IN[name])
                break
        if data is None:
            if atlas is not None:
                found = sorted(f[:-5] for f in os.listdir(ATLAS_FOLDER) if f.endswith('.json')) if os.path.isdir(ATLAS_FOLDER) else []
                raise ValueError('no atlas %r (atlases in the store: %s)' % (atlas, ', '.join(found + sorted(STAND_IN)) or 'none'))
            data = dict(STAND_IN[STAND_IN_FOR[kind]])
    units = data.get('units') or []
    size = data.get('picture_size_m') or [1.0, 1.0]
    good = []
    for unit in units:
        if len(unit) == 4 and 0.0 <= unit[0] < unit[2] <= 1.0 and 0.0 <= unit[1] < unit[3] <= 1.0:
            good.append([float(x) for x in unit])
    if not good or len(size) != 2 or min(size) <= 0:
        raise ValueError('the atlas %r holds no usable rectangles' % data.get('set'))
    data['units'] = good
    if data.get('kinds') and len(data['kinds']) != len(units):
        data['kinds'] = None
    return data


def _window(atlas, width, height, kind, rng):
    """One rectangle of the atlas for a unit of this face size (metres) and kind: (u0, v0, u1, v1), a window inside one
    whole photographed brick or block, of the unit's own proportions where the rectangle's differ much."""
    units = atlas['units']
    kinds = atlas.get('kinds')
    pw, ph = atlas['picture_size_m']
    choices = list(range(len(units)))
    if kinds:
        wanted = [i for i in choices if kinds[i] == ('header' if kind == 'closer' else kind)]
        if wanted:
            choices = wanted
    aspect = width / max(height, 1e-6)

    def misfit(i):
        u0, v0, u1, v1 = units[i]
        return abs(math.log(((u1 - u0) * pw) / max((v1 - v0) * ph, 1e-6) / aspect))
    if len(choices) > 6:
        choices.sort(key=misfit)
        choices = choices[:max(6, len(choices) // 3)]
    u0, v0, u1, v1 = units[rng.choice(choices)]
    rw, rh = (u1 - u0) * pw, (v1 - v0) * ph
    if rw > 1.5 * width and rh > 1.5 * height:            # a whole surface, not one block: a window at real size
        fw, fh = width / rw, height / rh
    elif abs(math.log(rw / rh / aspect)) < 0.3:            # near enough the unit's proportions: the whole brick
        return (u0, v0, u1, v1)
    else:
        k = min(rw / width, rh / height)
        fw, fh = min(1.0, width * k / rw), min(1.0, height * k / rh)
    a = rng.choice((0.0, 1.0)) if fw < 0.999 and rng.random() < 0.7 else rng.random()
    b = rng.random()
    su, sv = u0 + (u1 - u0) * (1 - fw) * a, v0 + (v1 - v0) * (1 - fh) * b
    return (su, sv, su + (u1 - u0) * fw, sv + (v1 - v0) * fh)


# ----------------------------------------------------------------------------------------------- the stand-in material

def _picture(basename, colour):
    path = store._shelf_file(basename)
    if path is None:
        return None
    image = bpy.data.images.load(path, check_existing=True)
    if not colour:
        image.colorspace_settings.name = 'Non-Color'
    return image


def stand_in_material(set_name):
    """A material for a set with no store atlas material yet: its shelf pictures through 'pp_atlas', each unit a
    little lighter or darker by its 'pp_piece', darkened into the look's range."""
    name = 'MADE • %s, one by one (stand-in)' % set_name
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'pp_atlas'
    piece = nodes.new('ShaderNodeAttribute')
    piece.attribute_name = 'pp_piece'
    shade = nodes.new('ShaderNodeMath')
    shade.operation = 'MULTIPLY_ADD'
    shade.inputs[1].default_value = 0.30
    shade.inputs[2].default_value = 0.42
    links.new(piece.outputs['Fac'], shade.inputs[0])
    tone = nodes.new('ShaderNodeHueSaturation')
    links.new(shade.outputs[0], tone.inputs['Value'])
    links.new(tone.outputs['Color'], bsdf.inputs['Base Color'])
    diff = _picture('%s_diff_2k.jpg' % set_name, True)
    if diff is not None:
        texture = nodes.new('ShaderNodeTexImage')
        texture.image = diff
        links.new(uv.outputs['UV'], texture.inputs['Vector'])
        links.new(texture.outputs['Color'], tone.inputs['Color'])
    rough = _picture('%s_rough_2k.jpg' % set_name, False)
    if rough is not None:
        texture = nodes.new('ShaderNodeTexImage')
        texture.image = rough
        links.new(uv.outputs['UV'], texture.inputs['Vector'])
        links.new(texture.outputs['Color'], bsdf.inputs['Roughness'])
    normal = _picture('%s_nor_gl_2k.jpg' % set_name, False)
    if normal is not None:
        texture = nodes.new('ShaderNodeTexImage')
        texture.image = normal
        links.new(uv.outputs['UV'], texture.inputs['Vector'])
        bend = nodes.new('ShaderNodeNormalMap')
        bend.uv_map = 'pp_atlas'
        bend.inputs['Strength'].default_value = 0.8
        links.new(texture.outputs['Color'], bend.inputs['Color'])
        links.new(bend.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def _store_has(name):
    try:
        return name in store.names('materials')
    except Exception:
        return False


def _material(value):
    return store.material(value) if isinstance(value, str) else value


# ----------------------------------------------------------------------------------------------- the courses

def brick_course(bond, k):
    """The units of course k (0 at the bottom) from the plane's left edge: (width, kind) in order, repeating its last
    pair or one for ever. Kinds: 'stretcher', 'header', 'closer'."""
    S, H, Q = (STRETCHER, 'stretcher'), (HEADER, 'header'), (CLOSER, 'closer')
    if bond == 'stretcher':
        return ([S], [S]) if k % 2 == 0 else ([H], [S])
    if bond == 'header':
        return ([H], [H]) if k % 2 == 0 else ([Q], [H])
    if bond == 'english':
        return ([S], [S]) if k % 2 == 0 else ([H, Q], [H])
    if bond == 'flemish':
        return ([H, Q], [S, H]) if k % 2 == 0 else ([], [S, H])
    raise ValueError('bond is one of %s, not %r' % (', '.join(BONDS), bond))


def _units_along(start, end, joint, widths):
    """Unit slots from start to end: (from, to, kind) with the joints between them, the first slot starting half a
    joint in from start. widths is a function giving the next (width, kind)."""
    slots, x = [], start
    while x < end - 1e-9:
        width, kind = widths()
        slots.append((x + joint / 2, x + width + joint / 2, kind))
        x += width + joint
    return slots


def _broken_bond(left, right, s_low, s_high, joint, shortest, below=()):
    """One course's slots with the bond kept at both edges: from the left edge towards the middle as laid from the
    left, from the right edge as laid from the right (mirrored), and cut bricks where the two meet near the middle (a
    broken bond, as bricklayers put it). Where they meet is chosen, within 0.35 m of the middle, so the joints there
    stand well clear of the joints of the course below (below)."""
    middle = (s_low + s_high) / 2
    ends = [slot[1] for slot in left]
    candidates = [i for i, e in enumerate(ends) if abs(e - middle) <= 0.35]
    if not candidates:
        candidates = [max([i for i, e in enumerate(ends) if e <= middle] or [-1])]
    best = None
    for i in candidates:
        kept = list(left[:i + 1]) if i >= 0 else []
        edge = kept[-1][1] + joint / 2 if kept else s_low
        others = [slot for slot in right if slot[0] >= edge + joint / 2 - 1e-9]
        start = others[0][0] - joint / 2 if others else s_high
        room = start - edge - joint
        if room >= shortest or not kept:
            if room > 1e-6:
                kept.append((edge + joint / 2, start - joint / 2, 'stretcher' if room > 0.15 else 'header'))
        else:
            last = kept.pop()
            both = start - joint / 2 - last[0] - joint
            cut = last[0] + both / 2
            kind = 'stretcher' if both / 2 > 0.15 else 'header'
            kept.extend([(last[0], cut, kind), (cut + joint, start - joint / 2, kind)])
        result = kept + others
        joints = [(a[1] + b[0]) / 2 for a, b in zip(result[:-1], result[1:]) if abs((a[1] + b[0]) / 2 - middle) < 0.5]
        lap = min((abs(a - b) for a in joints for b in below), default=1.0)
        score = (min(lap, 0.056), -abs(edge - middle))     # a quarter brick's lap first, then nearest the middle
        if best is None or score > best[0]:
            best = (score, result)
    return best[1]


def _fit_pieces(slots, a, b, joint, shortest):
    """The slots cut to the piece of course from a to b (each end half a joint in), a sliver at either end shared with
    its neighbour. Returns (from, to, full_from, full_to, kind)."""
    lo, hi = a + joint / 2, b - joint / 2
    pieces = []
    for s0, s1, kind in slots:
        p, q = max(s0, lo), min(s1, hi)
        if q - p > 1e-6:
            pieces.append([p, q, s0, s1, kind])
    if pieces and pieces[-1][1] < hi - 1e-7:              # a joint fell across the end: the last unit reaches the end
        pieces[-1][1] = pieces[-1][3] = hi
    if pieces and pieces[0][0] > lo + 1e-7:
        pieces[0][0] = pieces[0][2] = lo
    if len(pieces) >= 2 and pieces[-1][1] - pieces[-1][0] < shortest:
        last, before = pieces[-1], pieces[-2]
        both = last[1] - before[0] - joint
        middle = before[0] + both / 2
        before[1], last[0] = middle, middle + joint
        before[3] = max(before[3], before[1])
        last[2] = min(last[2], last[0])
    if len(pieces) >= 2 and pieces[0][1] - pieces[0][0] < shortest:
        first, after = pieces[0], pieces[1]
        both = after[1] - first[0] - joint
        middle = first[0] + both / 2
        first[1], after[0] = middle, middle + joint
        first[3] = max(first[3], first[1])
        after[2] = min(after[2], after[0])
    return [tuple(p) for p in pieces if p[1] - p[0] > 1e-4]


# ----------------------------------------------------------------------------------------------- the mesh

class WallMesh:
    def __init__(self, frame):
        self.frame = frame
        self.verts, self.faces, self.uvs, self.pieces = [], [], [], []

    def point(self, s, t, d):
        f = self.frame
        p = f['origin'] + f['along'] * s + f['up'] * t + f['out'] * d
        return (p.x, p.y, p.z)

    def unit(self, outline, full, depth, bevel, window, turned, piece):
        """One unit: outline (s, t) counter-clockwise; full = (s0, t0, s1, t1) the uncut unit's face, which maps onto
        window; depth(s, t) gives the face's distance out from the plane."""
        s0, t0, s1, t1 = full
        u0, v0, u1, v1 = window

        def uv(s, t, strip=0.0):
            a = min(1.0, max(0.0, (s - s0) / max(s1 - s0, 1e-9)))
            b = min(1.0, max(0.0, (t - t0) / max(t1 - t0, 1e-9)))
            a, b = a + (0.5 - a) * 2 * strip, b + (0.5 - b) * 2 * strip
            if turned:
                a, b = 1.0 - a, 1.0 - b
            return (u0 + a * (u1 - u0), v0 + b * (v1 - v0))
        inner = _inset(outline, bevel)
        if _area(inner) <= 0:
            cs = sum(p[0] for p in outline) / len(outline)
            ct = sum(p[1] for p in outline) / len(outline)
            inner = [(cs + (p[0] - cs) * 0.9, ct + (p[1] - ct) * 0.9) for p in outline]
        n = len(outline)
        start = len(self.verts)
        back = -0.003
        for s, t in inner:                                    # 0 .. n-1: the face
            self.verts.append(self.point(s, t, depth(s, t)))
        for s, t in outline:                                  # n .. 2n-1: the worn edge's outer line
            self.verts.append(self.point(s, t, depth(s, t) - bevel * 0.75))
        for s, t in outline:                                  # 2n .. 3n-1: the sides' back, at the plane
            self.verts.append(self.point(s, t, back))
        self.faces.append(tuple(start + i for i in range(n)))
        self.uvs.append([uv(s, t) for s, t in inner])
        for i in range(n):
            j = (i + 1) % n
            self.faces.append((start + i, start + n + i, start + n + j, start + j))
            self.uvs.append([uv(*inner[i]), uv(*outline[i]), uv(*outline[j]), uv(*inner[j])])
            self.faces.append((start + n + i, start + 2 * n + i, start + 2 * n + j, start + n + j))
            self.uvs.append([uv(*outline[i]), uv(*outline[i], strip=0.05), uv(*outline[j], strip=0.05), uv(*outline[j])])
        self.pieces.extend([piece] * (1 + 2 * n))

    def make(self, name, material, collection, seed=0):
        # each unit its own number: spread evenly over 0 to 1 and shuffled, so no two units share one (a random number
        # each, stored as a 32-bit float, repeats now and then on a big wall)
        count = max(self.pieces) + 1 if self.pieces else 0
        chooser = random.Random(seed)
        numbers = [(i + chooser.random()) / count for i in range(count)]
        chooser.shuffle(numbers)
        self.pieces = [numbers[i] for i in self.pieces]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        if material is not None:
            mesh.materials.append(material)
        layer = mesh.uv_layers.new(name='pp_atlas')
        flat = [c for face in self.uvs for pair in face for c in pair]
        layer.data.foreach_set('uv', flat)
        attribute = mesh.attributes.new('pp_piece', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.pieces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        return obj


def _chipped(s0, t0, s1, t1, chips):
    """A unit's outline with its four corners knocked off (chips: four (along, up) sizes), counter-clockwise."""
    (a0, b0), (a1, b1), (a2, b2), (a3, b3) = chips
    return [(s0 + a0, t0), (s1 - a1, t0), (s1, t0 + b1), (s1, t1 - b2), (s1 - a2, t1), (s0 + a3, t1), (s0, t1 - b3), (s0, t0 + b0)]


# ----------------------------------------------------------------------------------------------- the wall

def lay(plane, kind='brick', bond='stretcher', seed=0, course=0.30, relief=None, wear=1.0, atlas=None, material=None,
        mortar_material='default', flip=False, collection=None):
    """Cover the plane with bricks or stone blocks. Returns the object 'wall units' (its counts in obj['units'],
    obj['courses'])."""
    if plane is None or getattr(plane, 'type', None) != 'MESH':
        raise ValueError('lay_wall needs a mesh object (the plane)')
    if kind not in KINDS:
        raise ValueError("kind is 'brick' or 'stone', not %r" % (kind,))
    if kind == 'brick' and bond not in BONDS:
        raise ValueError('bond is one of %s, not %r' % (', '.join(BONDS), bond))
    if not (0.12 <= float(course) <= 1.2):
        raise ValueError('course is a stone course height in metres, 0.12 to 1.2, not %r' % (course,))
    if not (0.0 <= float(wear) <= 2.0):
        raise ValueError('wear runs from 0 to 2, not %r' % (wear,))
    if relief is not None and not (0.002 <= float(relief) <= 0.2):
        raise ValueError('relief is metres out from the plane, 0.002 to 0.2, not %r' % (relief,))
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    frame = plane_frame(plane, flip=bool(flip))
    outline = frame['outline']
    if len(outline) < 3 or abs(_area(outline)) < 1e-4:
        raise ValueError('the plane %r is too small to lay a wall on' % plane.name)
    atlas_data = read_atlas(atlas, kind)
    joint = BRICK_JOINT if kind == 'brick' else STONE_JOINT
    relief = float(relief) if relief is not None else (0.012 if kind == 'brick' else 0.02)
    wear = float(wear)
    t_low = min(p[1] for p in outline)
    t_high = max(p[1] for p in outline)
    s_low = min(p[0] for p in outline)
    s_high = max(p[0] for p in outline)
    height = t_high - t_low
    holes = frame['holes']
    convex = _convex(outline) and not holes
    clipper = _inset(outline, joint / 2, limit=6.0) if convex else None
    # the courses: whole from bottom to top
    if kind == 'brick':
        count = max(1, int(round(height / (HEIGHT + BRICK_JOINT))))
        rises = [height / count] * count
    else:
        count = max(1, int(round(height / course)))
        weights = [rng.uniform(0.75, 1.3) for _ in range(count)]
        rises = [height * w / sum(weights) for w in weights]
    mesh = WallMesh(frame)
    units = 0
    below_joints = []
    t = t_low
    for k, rise in enumerate(rises):
        ta, tb = t, t + rise
        t = tb
        if kind == 'brick':
            face_h = min(HEIGHT, rise - 0.006) if rise - HEIGHT < 0.016 else rise - 0.016
            face_h = max(face_h, rise * 0.5)
        else:
            face_h = rise - joint
        fa = (ta + tb) / 2 - face_h / 2
        fb = fa + face_h
        inner, outer = _band([outline] + holes, ta, tb)
        cut_slopes = convex and outer and inner != outer and not (
            inner and abs(inner[0][0] - outer[0][0]) < 1e-4 and abs(inner[-1][1] - outer[0][1]) < 1e-4)
        runs = [(a, b, fa, fb) for a, b in (outer if cut_slopes else inner)]
        if not cut_slopes:
            # where a hole's top or bottom (or a step in the outline) falls inside the course: units cut in height
            loops = [outline] + holes
            levels = sorted(set(p[1] for polygon in loops for p in polygon if ta + 1e-6 < p[1] < tb - 1e-6))
            edges = [ta] + levels + [tb]
            for ya, yb in zip(edges[:-1], edges[1:]):
                part, _ = _band(loops, ya, yb)
                low_t = max(fa, ya + (joint / 2 if ya > ta else 0.0))
                high_t = min(fb, yb - (joint / 2 if yb < tb else 0.0))
                if high_t - low_t < (0.02 if kind == 'brick' else 0.04):
                    continue
                runs.extend((a, b, low_t, high_t) for a, b in _subtract(part, inner))
        if not runs:
            continue
        # the slots of this course, from the plane's left edge
        if kind == 'brick':
            first, repeat = brick_course(bond, k)
            sequence = list(first)
            state = {'i': 0}

            def widths():
                i = state['i']
                state['i'] += 1
                if i < len(sequence):
                    return sequence[i]
                return repeat[(i - len(sequence)) % len(repeat)]
            left = _units_along(s_low, s_high + 1.0, joint, widths)
            state['i'] = 0
            right = sorted((s_high + s_low - q, s_high + s_low - p, kind_) for p, q, kind_ in _units_along(s_low, s_high + 1.0, joint, widths))
            slots = _broken_bond(left, right, s_low, s_high, joint, 0.05, below_joints)
            below_joints = [(a[1] + b[0]) / 2 for a, b in zip(slots[:-1], slots[1:])]
        else:
            slots, x, joints_here = [], s_low - rng.uniform(0.0, 0.5) * rise, []
            while x < s_high + 1e-6:
                length = min(max(rng.uniform(1.3, 2.7) * rise, 0.3), 1.5)
                for _ in range(6):
                    end = x + length
                    if all(abs(end - j) > 0.12 for j in below_joints):
                        break
                    length += 0.07
                slots.append((x + joint / 2, x + length - joint / 2, 'block'))
                joints_here.append(x + length)
                x += length
            below_joints = joints_here
        shortest = 0.05 if kind == 'brick' else max(0.18, rise * 0.6)
        for a, b, ya, yb in runs:
            for p, q, full0, full1, unit_kind in _fit_pieces(slots, a, b, joint, shortest):
                w_face, h_face = q - p, yb - ya
                bevel = (rng.uniform(0.0015, 0.0035) if kind == 'brick' else rng.uniform(0.002, 0.005)) * min(wear, 1.5)
                bevel = max(bevel, 0.0005)
                if kind == 'brick':
                    chips = [(rng.uniform(1.5 * bevel, 1.5 * bevel + 0.005 * wear), rng.uniform(1.5 * bevel, 1.5 * bevel + 0.003 * wear)) for _ in range(4)]
                else:
                    chips = []
                    for _ in range(4):
                        big = rng.random() < 0.35            # now and then a corner knocked off, as lay_stone's blocks
                        along = rng.uniform(0.008, max(0.0081, min(0.090, w_face * 0.16))) if big else rng.uniform(0.002, 0.008)
                        up = rng.uniform(0.005, max(0.0051, min(0.060, h_face * 0.22))) if big else rng.uniform(0.002, 0.006)
                        chips.append((along * min(wear, 1.5) + 1.5 * bevel, up * min(wear, 1.5) + 1.5 * bevel))
                chips = [(min(c[0], w_face * 0.3), min(c[1], h_face * 0.3)) for c in chips]
                shape = _chipped(p, ya, q, yb, chips)
                if cut_slopes:
                    shape = _tidy(_clip(shape, clipper), 0.6 * bevel)
                    if len(shape) < 3 or _area(shape) < max(0.0004, 0.12 * w_face * h_face):
                        continue
                set_in = rng.uniform(-1.0, 1.0) * (0.0025 if kind == 'brick' else 0.004) * wear
                tip = 0.6 if kind == 'brick' else 0.3           # degrees: a hair either way
                tip_s = math.radians(rng.uniform(-tip, tip) * wear)
                tip_t = math.radians(rng.uniform(-tip, tip) * wear)
                cs, ct = (p + q) / 2, (ya + yb) / 2
                ripple = (0.0015 if kind == 'stone' else 0.0004) * wear
                phase = rng.uniform(0, 6.28)

                def depth(s, tt, cs=cs, ct=ct, set_in=set_in, tip_s=tip_s, tip_t=tip_t, ripple=ripple, phase=phase):
                    return relief + set_in + math.tan(tip_s) * (s - cs) + math.tan(tip_t) * (tt - ct) + ripple * math.sin(phase + 37 * s + 23 * tt)
                full = (full0, fa, full1, fb)
                window = _window(atlas_data, full1 - full0, fb - fa, unit_kind if unit_kind != 'block' else 'block', rng)
                turned = rng.random() < 0.5
                mesh.unit(shape, full, depth, bevel, window, turned, units)
                units += 1
    if collection is None:
        collection = bpy.data.collections.new('lay_wall')
        bpy.context.scene.collection.children.link(collection)
    if material is None:
        name = atlas_data.get('material')
        unit_material = _material(name) if name and _store_has(name) else stand_in_material(atlas_data.get('set') or STAND_IN_FOR[kind])
    else:
        unit_material = _material(material)
    made = mesh.make('wall units', unit_material, collection, seed=rng.random())
    ground = min((plane.matrix_world @ v.co).z for v in plane.data.vertices)
    store.mark(made, ground=ground)
    made['units'] = units
    made['courses'] = len(rises)
    made['kind'] = kind
    made['bond'] = bond if kind == 'brick' else 'coursed ashlar'
    made['atlas'] = str(atlas_data.get('set'))
    made['relief'] = relief
    if mortar_material == 'default':
        mortar_material = next((m for m in MORTAR_MATERIALS if _store_has(m)), None)
    if mortar_material is not None:
        store.use_material(plane, _material(mortar_material), ground=ground)
    plane['wall_front'] = relief
    return made


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the plane object')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--kind', default='brick', choices=KINDS, help="'brick' or 'stone'; default brick")
    parser.add_argument('--bond', default='stretcher', choices=BONDS, help='the brick bond; default stretcher')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same wall; default 0')
    parser.add_argument('--course', type=float, default=0.30, help='stone: about how tall a course is, metres; default 0.30')
    parser.add_argument('--relief', type=float, default=None, help="metres the units' faces stand out; default 0.012 brick, 0.02 stone")
    parser.add_argument('--wear', type=float, default=1.0, help='0 laid true and sharp, 1 normal, up to 2; default 1')
    parser.add_argument('--atlas', default=None, help='the photographed set (an atlas file in store/materials/atlas/); default the kind\'s own')
    parser.add_argument('--mortar-material', default='default', help="the plane's new material; 'none' leaves it")
    parser.add_argument('--flip', action='store_true', help='lay the units on the side the plane\'s face looks away from')
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to lay a wall')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    plane = bpy.data.objects.get(args.object)
    if plane is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    mortar = None if args.mortar_material.lower() == 'none' else args.mortar_material
    made = lay(plane, kind=args.kind, bond=args.bond, seed=args.seed, course=args.course, relief=args.relief, wear=args.wear,
               atlas=args.atlas, mortar_material=mortar, flip=args.flip)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s: %d units in %d courses, saved %s' % (made.name, made['units'], made['courses'], args.out))


if __name__ == '__main__':
    main()
