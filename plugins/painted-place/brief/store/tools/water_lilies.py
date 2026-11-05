"""
What this file does: floats water lilies on a pond at the water level you give, within an area you give, in clumps as
they grow: round pads with a narrow notch cut to the middle, each its own size and green (some yellowing, a few with a
red rim), lying flat on the water with a faint wave at the edge, the older ones curling up at their rim to show the
red-purple underside; and a few flowers among them, pink or white, rings of pointed petals cupped round a yellow
middle. They keep clear of whatever you name (a bridge's posts, stepping stones, a rock) by a margin you give. Nothing
here chooses where lilies grow: the area, the level and how many are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import water_lilies
    made = water_lilies.lay([(1.0, 6.0), (4.0, 6.2), (4.4, 9.5), (1.2, 9.8)], level=-0.05, amount=1.0, seed=3)
    made = water_lilies.lay(pond_water, keep_clear=[bridge, (2.2, 5.3, 0.6)], flowers=1.5, colour='white', seed=4)
    made['pads'], made['flowers']          # obj['pads'], obj['flowers'] count them

The area is a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or a mesh object (your pond's water: lilies float
where a ray straight down meets it, at its height there, unless you give `level`). `keep_clear` is a list of things to
stay away from: objects (their outline from above, as a box), circles (x, y, radius) and polygons [(x, y), ...].

From the command line:

    python3 water_lilies.py --help
    python3 water_lilies.py --area 0 0 3 2 --level 0 --amount 1.5 --out lilies.blend

Options, with their defaults:
    area        the area they grow in (required)
    level       none      the water's height (needed unless the area is your water object)
    amount      1.0       how many: 1 a few clumps (about 3 pads a square metre of the area), 2 crowded, 0.3 a scattering
    flowers     1.0       about how many flowers for every ten pads (0 none)
    colour      'pink'    the flowers: 'pink', 'white' or 'mixed'
    size        1.0       the pads' size: 1 is 14 to 28 cm across
    keep_clear  none      things to keep clear of: objects, circles (x, y, radius), polygons
    margin      0.12 m    how far the pads keep from them
    seed        0         the same seed floats the same lilies
    collection  none      where the objects go (a new collection 'water_lilies')

What it makes: 'water-lily pads' (obj['pads']) and 'water-lily flowers' (obj['flowers'], none when there are none),
with their own materials made here, 'MADE • water-lily pads' and 'MADE • water-lily flowers'. Each pad's points carry
'lily_tone' (its green) and 'lily_r' (0 at its middle to 1 at its rim, for the veins).
"""

import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

PADS = 'MADE • water-lily pads'
FLOWERS = 'MADE • water-lily flowers'
COLOURS = ('pink', 'white', 'mixed')

TOOL = {
    'name': 'water_lilies',
    'what': 'water-lily pads (round, a notch to the middle, some curling at the edge) and a few pink or white flowers '
            'floating at a water level you give, in clumps within an area you give, keeping clear of what you name '
            "(a bridge's posts, stepping stones)",
    'call': "water_lilies.lay([(1.0, 6.0), (4.0, 6.2), (4.4, 9.5), (1.2, 9.8)], level=-0.05, keep_clear=[bridge], seed=3)",
    'options': {
        'area': 'a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or your water object (required)',
        'level': "the water's height (needed unless the area is your water object)",
        'amount': 'how many: 1 a few clumps, about 3 pads a square metre; 2 crowded; 0.3 a scattering (1.0)',
        'flowers': 'about how many flowers for every ten pads; 0 none (1.0)',
        'colour': "the flowers: 'pink', 'white' or 'mixed' ('pink')",
        'size': "the pads' size: 1 is 14 to 28 cm across (1.0)",
        'keep_clear, margin': 'things to keep clear of: objects (their box from above), circles (x, y, radius), polygons; '
                              'and by how much (none, 0.12 m)',
        'seed': 'the same seed floats the same lilies (0)',
        'collection': "where the objects go (a new collection 'water_lilies')",
    },
    'materials': [PADS + ' (made in code)', FLOWERS + ' (made in code)'],
    'source': "the water lilies in the garden builders' '57 garden' scripts ('/home/claude/build-57-garden/second pass/"
              "render_final.py', lines 1488-1522: flat notched discs and five-point flowers), made into a tool: pads in "
              'clumps that keep clear of what you name, a faint wave and curled rims showing the underside, veins, and '
              'cupped flowers of pointed petals round a yellow middle',
    'trap': 'the pads lie 4 mm over the level you give: give the water\'s own height, or they float in the air or drown; '
            'a pad is a hand across, so from 15 m it is a fleck: put clumps where the eye is near or the water mirrors '
            "a light; pink flowers go grey at dusk unless a light reaches them",
}


# ------------------------------------------------------------------------------------------------ where

class _Area:
    def __init__(self, area, level):
        self.object = area if isinstance(area, bpy.types.Object) else None
        self.level = level
        if self.object is not None:
            if self.object.type != 'MESH':
                raise ValueError('the area object must be a mesh (your water)')
            bpy.context.view_layer.update()
            corners = [self.object.matrix_world @ Vector(c) for c in self.object.bound_box]
            self.box = (min(c.x for c in corners), min(c.y for c in corners), max(c.x for c in corners), max(c.y for c in corners))
            self.top = max(c.z for c in corners) + 1.0
            self.to_local = self.object.matrix_world.inverted()
            self.down = (self.to_local.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
            self.polygon = None
        else:
            if level is None:
                raise ValueError('give level= (the water\'s height), or give your water object as the area')
            if len(area) == 4 and not hasattr(area[0], '__len__'):
                x0, y0, x1, y1 = (float(v) for v in area)
                self.polygon = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            else:
                self.polygon = [(float(p[0]), float(p[1])) for p in area]
                if len(self.polygon) < 3:
                    raise ValueError('an area polygon needs at least three points')
            xs, ys = [p[0] for p in self.polygon], [p[1] for p in self.polygon]
            self.box = (min(xs), min(ys), max(xs), max(ys))

    def size(self):
        if self.polygon is None:
            return (self.box[2] - self.box[0]) * (self.box[3] - self.box[1]) * 0.7
        area = 0.0
        for (x0, y0), (x1, y1) in zip(self.polygon, self.polygon[1:] + self.polygon[:1]):
            area += x0 * y1 - x1 * y0
        return abs(area) / 2.0

    def height(self, x, y):
        """The water's height at (x, y), or None outside the area."""
        if self.polygon is not None:
            return self.level if _inside(self.polygon, x, y) else None
        hit, location, _, _ = self.object.ray_cast(self.to_local @ Vector((x, y, self.top)), self.down)
        if not hit:
            return None
        return self.level if self.level is not None else (self.object.matrix_world @ location).z


def _inside(polygon, x, y):
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def _keep_clear(items, margin):
    """A function (x, y, radius) -> True where a pad of that radius would touch one of the things named."""
    shapes = []
    for item in items or ():
        if isinstance(item, bpy.types.Object):
            corners = [item.matrix_world @ Vector(c) for c in item.bound_box]
            shapes.append(('box', (min(c.x for c in corners), min(c.y for c in corners), max(c.x for c in corners), max(c.y for c in corners))))
        elif len(item) == 3 and not hasattr(item[0], '__len__'):
            shapes.append(('circle', tuple(float(v) for v in item)))
        else:
            shapes.append(('polygon', [(float(p[0]), float(p[1])) for p in item]))

    def blocked(x, y, radius):
        reach = radius + margin
        for kind, shape in shapes:
            if kind == 'circle':
                if math.hypot(x - shape[0], y - shape[1]) < shape[2] + reach:
                    return True
            elif kind == 'box':
                dx = max(shape[0] - x, 0.0, x - shape[2])
                dy = max(shape[1] - y, 0.0, y - shape[3])
                if math.hypot(dx, dy) < reach:
                    return True
            else:
                if _inside(shape, x, y):
                    return True
                for (x0, y0), (x1, y1) in zip(shape, shape[1:] + shape[:1]):
                    ex, ey = x1 - x0, y1 - y0
                    t = max(0.0, min(1.0, ((x - x0) * ex + (y - y0) * ey) / ((ex * ex + ey * ey) or 1e-12)))
                    if math.hypot(x - x0 - ex * t, y - y0 - ey * t) < reach:
                        return True
        return False
    return blocked


# ------------------------------------------------------------------------------------------------ the pads and flowers

class _Mesh:
    def __init__(self):
        self.verts, self.faces, self.tone, self.radial = [], [], [], []

    def add(self, verts, faces, tone, radial):
        base = len(self.verts)
        self.verts.extend(tuple(v) for v in verts)
        self.faces.extend(tuple(base + i for i in face) for face in faces)
        self.tone.extend([tone] * len(verts))
        self.radial.extend(radial)

    def make(self, name, material, collection):
        if not self.faces:
            return None
        mesh = bpy.data.meshes.new(name)
        origin = Vector(self.verts[0])
        mesh.from_pydata([tuple(Vector(v) - origin) for v in self.verts], [], self.faces)
        for column, values in (('lily_tone', self.tone), ('lily_r', self.radial)):
            layer = mesh.attributes.new(column, 'FLOAT', 'POINT')
            layer.data.foreach_set('value', values)
        for polygon in mesh.polygons:                     # every pad and petal faces up (its underside is the back)
            if polygon.normal.z < 0:
                polygon.flip()
        mesh.update()
        mesh.shade_smooth()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = origin
        collection.objects.link(obj)
        obj.data.materials.append(material)
        store.mark(obj)
        return obj


def _pad(mesh, x, y, z, radius, rng):
    """A pad: round, a narrow notch to the middle, a faint wave at the rim; old ones curl up at the edge."""
    notch = rng.uniform(0.0, math.tau)
    half_gap = math.radians(rng.uniform(3.5, 8.0))
    curl = radius * rng.uniform(0.12, 0.3) if rng.random() < 0.22 else radius * rng.uniform(0.0, 0.03)
    tone = 0.8 * rng.random() ** 1.5 if rng.random() > 0.08 else rng.uniform(0.85, 1.0)   # a few yellowing
    rings = (0.0, 0.3, 0.6, 0.82, 0.94, 1.0)
    angles = 30
    offset = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), 0.0))
    verts, radial = [], []
    for f in rings:
        for k in range(angles + 1):
            a = notch + half_gap * (0.3 + 0.7 * f) + (math.tau - 2 * half_gap * (0.3 + 0.7 * f)) * k / angles
            wave = 0.04 * noise.noise(Vector((math.cos(a) * 2.0, math.sin(a) * 2.0, 0.0)) + offset)
            r = radius * f * (1.0 + wave)
            lift = curl * max(0.0, (f - 0.7) / 0.3) ** 2.2 + 0.002 * f * noise.noise(Vector((math.cos(a) * 4.0, math.sin(a) * 4.0, 1.0)) + offset)
            verts.append((x + r * math.cos(a), y + r * math.sin(a), z + 0.004 + lift))
            radial.append(f)
    faces = []
    row = angles + 1
    for i in range(len(rings) - 1):
        for k in range(angles):
            a0, b0 = i * row + k, (i + 1) * row + k
            faces.append((a0, a0 + 1, b0 + 1, b0))
    mesh.add(verts, faces, tone, radial)


def _flower(mesh, x, y, z, size, rng, white):
    """A flower: three rings of pointed petals, the outer lying open, the inner cupped up round a yellow middle."""
    tone = rng.uniform(0.6, 1.0) if white else rng.uniform(0.0, 0.4)
    turn = rng.uniform(0.0, math.tau)
    for ring, (count, length, rise) in enumerate(((10, 1.0, 0.25), (9, 0.85, 0.75), (8, 0.62, 1.25))):
        for k in range(count):
            a = turn + math.tau * (k + 0.5 * ring) / count + rng.gauss(0.0, 0.05)
            out = Vector((math.cos(a), math.sin(a), 0.0))
            side = Vector((-math.sin(a), math.cos(a), 0.0))
            tilt = rise + rng.gauss(0.0, 0.08)
            verts, radial = [], []
            for j in range(5):                                # base to tip
                t = j / 4.0
                width = size * 0.16 * math.sin(math.pi * min(t * 0.9 + 0.08, 1.0)) * (1.0 - 0.6 * t)
                along = size * 0.5 * length * t
                lift = along * math.sin(tilt) * (0.6 + 0.6 * t)
                centre = Vector((x, y, z + 0.006)) + out * (size * 0.06 + along * math.cos(tilt)) + Vector((0, 0, lift))
                for s in (-1.0, 0.0, 1.0):
                    cup = abs(s) * width * 0.35              # the petal cupped along its middle
                    verts.append(centre + side * s * width + Vector((0, 0, cup)))
                    radial.append(0.2 + 0.8 * t)
            faces = []
            for j in range(4):
                for s in range(2):
                    a0 = j * 3 + s
                    faces.append((a0, a0 + 1, a0 + 4, a0 + 3))
            mesh.add(verts, faces, tone, radial)
    # the yellow middle: a low cone of stamens (lily_r 0 draws it yellow)
    verts, radial, faces = [Vector((x, y, z + 0.006 + size * 0.13))], [0.0], []
    for k in range(12):
        a = math.tau * k / 12
        verts.append(Vector((x + math.cos(a) * size * 0.1, y + math.sin(a) * size * 0.1, z + 0.006 + size * 0.06)))
        radial.append(0.0)
    for k in range(12):
        faces.append((0, 1 + k, 1 + (k + 1) % 12))
    mesh.add(verts, faces, tone, radial)


# ------------------------------------------------------------------------------------------------ materials

def _nodes(material):
    nodes, links = material.node_tree.nodes, material.node_tree.links

    def attribute(name):
        node = nodes.new('ShaderNodeAttribute')
        node.attribute_name = name
        return node.outputs['Fac']

    def ramp(fac, stops):
        node = nodes.new('ShaderNodeValToRGB')
        elements = node.color_ramp.elements
        elements[0].position, elements[0].color = stops[0][0], (*stops[0][1], 1.0)
        elements[1].position, elements[1].color = stops[-1][0], (*stops[-1][1], 1.0)
        for position, colour in stops[1:-1]:
            elements.new(position).color = (*colour, 1.0)
        links.new(fac, node.inputs['Fac'])
        return node.outputs['Color']

    def mix(fac, a, b):
        node = nodes.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        for socket, value in ((node.inputs[0], fac), (node.inputs[6], a), (node.inputs[7], b)):
            if isinstance(value, (int, float)):
                socket.default_value = value
            elif isinstance(value, tuple):
                socket.default_value = (*value, 1.0)
            else:
                links.new(value, socket)
        return node.outputs[2]
    return nodes, links, attribute, ramp, mix


def pads_material():
    existing = bpy.data.materials.get(PADS)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(PADS)
    material.use_nodes = True
    nodes, links, attribute, ramp, mix = _nodes(material)
    principled = nodes['Principled BSDF']
    green = ramp(attribute('lily_tone'), [(0.0, (0.016, 0.045, 0.012)), (0.45, (0.03, 0.068, 0.016)), (0.75, (0.055, 0.075, 0.018)),
                                          (0.9, (0.11, 0.09, 0.02)), (1.0, (0.14, 0.07, 0.02))])
    radial = attribute('lily_r')
    geometry = nodes.new('ShaderNodeNewGeometry')
    position = nodes.new('ShaderNodeTexCoord')               # faint veins: a fine net over the pad
    veins = nodes.new('ShaderNodeTexVoronoi')
    veins.feature = 'DISTANCE_TO_EDGE'
    veins.inputs['Scale'].default_value = 26.0
    links.new(position.outputs['Object'], veins.inputs['Vector'])
    vein = nodes.new('ShaderNodeMapRange')
    vein.inputs['From Min'].default_value = 0.0
    vein.inputs['From Max'].default_value = 0.06
    vein.inputs['To Min'].default_value = 0.35
    vein.inputs['To Max'].default_value = 0.0
    links.new(veins.outputs['Distance'], vein.inputs['Value'])
    colour = mix(vein.outputs['Result'], green, (0.01, 0.025, 0.008))
    rim = nodes.new('ShaderNodeMapRange')                     # a red rim on some
    rim.inputs['From Min'].default_value = 0.88
    rim.inputs['From Max'].default_value = 1.0
    rim.inputs['To Max'].default_value = 0.55
    links.new(radial, rim.inputs['Value'])
    colour = mix(rim.outputs['Result'], colour, (0.09, 0.02, 0.012))
    colour = mix(geometry.outputs['Backfacing'], colour, (0.13, 0.025, 0.04))   # the curled rim's red-purple underside
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.45          # waxy, not a mirror: a shiny pad flares white like paper
    principled.inputs['Specular IOR Level'].default_value = 0.22
    return material


def flowers_material():
    existing = bpy.data.materials.get(FLOWERS)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(FLOWERS)
    material.use_nodes = True
    nodes, links, attribute, ramp, mix = _nodes(material)
    principled = nodes['Principled BSDF']
    petal = ramp(attribute('lily_tone'), [(0.0, (0.55, 0.13, 0.22)), (0.4, (0.66, 0.3, 0.38)), (0.6, (0.72, 0.68, 0.62)), (1.0, (0.8, 0.78, 0.72))])
    radial = attribute('lily_r')
    base = nodes.new('ShaderNodeMapRange')                    # paler and warmer towards the petal's foot
    base.inputs['From Min'].default_value = 0.2
    base.inputs['From Max'].default_value = 0.6
    base.inputs['To Min'].default_value = 0.45
    base.inputs['To Max'].default_value = 0.0
    links.new(radial, base.inputs['Value'])
    colour = mix(base.outputs['Result'], petal, (0.8, 0.7, 0.55))
    middle = nodes.new('ShaderNodeMath')
    middle.operation = 'LESS_THAN'
    middle.inputs[1].default_value = 0.05
    links.new(radial, middle.inputs[0])
    colour = mix(middle.outputs[0], colour, (0.62, 0.42, 0.04))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.5
    translucent = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(colour, translucent.inputs['Color'])
    shader = nodes.new('ShaderNodeMixShader')
    shader.inputs[0].default_value = 0.3
    links.new(principled.outputs[0], shader.inputs[1])
    links.new(translucent.outputs[0], shader.inputs[2])
    links.new(shader.outputs[0], nodes['Material Output'].inputs['Surface'])
    return material


# ------------------------------------------------------------------------------------------------ laying

def lay(area, level=None, amount=1.0, flowers=1.0, colour='pink', size=1.0, keep_clear=None, margin=0.12, seed=0, collection=None):
    """Float the lilies (see the note at the top). Returns {'pads': obj, 'flowers': obj or None}."""
    if colour not in COLOURS:
        raise ValueError("colour is 'pink', 'white' or 'mixed', not %r" % (colour,))
    amount, flowers, size, margin = float(amount), float(flowers), float(size), float(margin)
    if not 0.0 < amount <= 5.0:
        raise ValueError('amount is above 0 and up to 5, not %r' % (amount,))
    if not 0.2 <= size <= 3.0:
        raise ValueError('size is 0.2 to 3, not %r' % (size,))
    rng = random.Random(seed)
    where = _Area(area, level)
    blocked = _keep_clear(keep_clear, margin)
    target_count = max(1, min(800, int(round(3.0 * amount * where.size()))))
    clumps = max(1, int(round(target_count / 9.0)))
    x0, y0, x1, y1 = where.box
    centres = []
    for _ in range(clumps * 30):
        if len(centres) >= clumps:
            break
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if where.height(x, y) is None or blocked(x, y, 0.1 * size):
            continue
        if any(math.hypot(x - cx, y - cy) < 0.5 * size for cx, cy, _ in centres):
            continue
        centres.append((x, y, rng.uniform(0.25, 0.6) * size * math.sqrt(amount + 0.3)))
    pads, laid = _Mesh(), []
    per_clump = max(1, int(round(target_count / max(len(centres), 1))))
    for cx, cy, spread in centres:
        for _ in range(per_clump * 4):
            if sum(1 for p in laid if p[3] == (cx, cy)) >= per_clump:
                break
            x, y = cx + rng.gauss(0.0, spread * 0.55), cy + rng.gauss(0.0, spread * 0.55)
            radius = size * rng.uniform(0.07, 0.14)
            z = where.height(x, y)
            if z is None or blocked(x, y, radius):
                continue
            if any(math.hypot(x - px, y - py) < 0.72 * (radius + pr) for px, py, pr, _ in laid):
                continue
            _pad(pads, x, y, z, radius, rng)
            laid.append((x, y, radius, (cx, cy)))
    blooms = _Mesh()
    flower_count = int(round(len(laid) * flowers / 10.0 + rng.uniform(-0.3, 0.3)))
    placed = 0
    for x, y, radius, _ in rng.sample(laid, len(laid)):
        if placed >= flower_count:
            break
        a = rng.uniform(0.0, math.tau)                        # beside its pad, on the water
        fx, fy = x + math.cos(a) * radius * 1.05, y + math.sin(a) * radius * 1.05
        z = where.height(fx, fy)
        if z is None or blocked(fx, fy, 0.06 * size):
            continue
        white = colour == 'white' or (colour == 'mixed' and rng.random() < 0.5)
        _flower(blooms, fx, fy, z, size * rng.uniform(0.11, 0.15), rng, white)
        placed += 1
    target = collection
    if target is None:
        target = bpy.data.collections.new('water_lilies')
        bpy.context.scene.collection.children.link(target)
    made = {'pads': pads.make('water-lily pads', pads_material(), target), 'flowers': blooms.make('water-lily flowers', flowers_material(), target)}
    if made['pads'] is not None:
        made['pads']['pads'] = len(laid)
    if made['flowers'] is not None:
        made['flowers']['flowers'] = placed
    return made


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of water_lilies.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--water', help='the name of your water object in the --blend file (the area)')
    parser.add_argument('--area', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='a rectangle to float them in')
    parser.add_argument('--level', type=float, default=None, help="the water's height")
    parser.add_argument('--amount', type=float, default=1.0, help='1 a few clumps; default 1')
    parser.add_argument('--flowers', type=float, default=1.0, help='flowers for every ten pads; default 1')
    parser.add_argument('--colour', default='pink', choices=list(COLOURS), help="the flowers' colour; default pink")
    parser.add_argument('--seed', type=int, default=0, help='the same seed floats the same lilies; default 0')
    parser.add_argument('--out', help='save the result here (.blend)')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    area = bpy.data.objects.get(args.water) if args.water else (tuple(args.area) if args.area else None)
    if area is None:
        parser.error('give --area X0 Y0 X1 Y1 with --level, or --blend with --water')
    made = lay(area, level=args.level, amount=args.amount, flowers=args.flowers, colour=args.colour, seed=args.seed)
    print('floated %d pads and %d flowers' % (made['pads']['pads'] if made['pads'] else 0, made['flowers']['flowers'] if made['flowers'] else 0))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
