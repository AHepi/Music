"""
mangold_heap: a cartload of mangolds (mangel-wurzels, the field roots fed to cattle in winter) tipped against the foot
of a wall: long tapering roots lying every way, each its own dull orange-yellow to red, darker on the shoulder that grew
above the soil, soil caked on their tails; the heap peaks against the wall at +Y and spreads to a foot of roots lying on
the ground; a few rolled loose in front. The gaps between the roots are dark earth. Foot at z = 0; the origin is the
middle of the heap's footprint; its back is flat, at y = +depth/2, for the wall.

Options:
    width    along the wall (X), metres (default 1.8)
    depth    out from the wall (Y), metres (default 0.9)
    height   at the wall, metres (default 0.65)
    loose    how many roots lie rolled loose in front of the heap (default 5; 0 for none)
    seed     every root's size, shape, colour and lie

Where it came from: '/home/claude/build-54-barn/dress/render_final.py', mangold_material() (line 964), mangold_mesh()
(line 1020), put_mangold() (line 1052) and the heap after heap_inside() (lines 1070-1094): about 330 separate root
objects made from five shared meshes, in three shells of a half dome. Rebuilt here as one mesh of roots in two layers
over a dark core, slimmer and longer (that builder's roots first read as peaches), every root its own shape and colour.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402

PART = 'mangold_heap'

CARD = {
    'name': PART,
    'what': 'a cartload of mangolds tipped against a wall at +Y: long tapering roots lying every way, each its own dull orange to red, '
            'soil caked on their tails, dark earth between them; a few rolled loose in front',
    'size_m': (1.94, 1.30, 0.70),
    'options': {
        'width': 'along the wall (X), metres (default 1.8)',
        'depth': 'out from the wall (Y), metres (default 0.9)',
        'height': 'at the wall, metres (default 0.65)',
        'loose': 'how many roots lie rolled loose in front of the heap (default 5; 0 for none)',
        'seed': "every root's size, shape, colour and lie (default 0)",
    },
    'materials': ['PART • mangold_heap: mangold, soiled', 'PART • mangold_heap: earth between the roots'],
    'source': "'/home/claude/build-54-barn/dress/render_final.py', mangold_material() (line 964), mangold_mesh() (line 1020), "
              "put_mangold() (line 1052) and the heap after heap_inside() (lines 1070-1094)",
    'views': 'reads from the front and both sides; its back is flat, for the wall at +Y',
    'trap': 'the origin is the middle of the footprint and the flat back is at y = +depth/2 (0.45 m behind the origin): stand that face '
            'on a wall, or the heap shows a cut-off back',
}

ROOT_LENGTH = (0.27, 0.40)
ROOT_RADIUS = (0.045, 0.063)


def earth_material():
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        n = shapes.noise_fac(nodes, links, vec, 9.0, detail=5.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, n, 0.35, 0.7), (0.012, 0.009, 0.006), (0.03, 0.021, 0.013))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.9
        links.new(shapes.bump(nodes, links, n, 0.6, 0.01), principled.inputs['Normal'])
        m.diffuse_color = (0.02, 0.015, 0.01, 1.0)
    return shapes.part_material(PART, 'earth between the roots', maker)


def build(collection, seed=0, width=1.8, depth=0.9, height=0.65, loose=5):
    width = barn.number('mangold_heap width', width, 0.4, 12.0)
    depth = barn.number('mangold_heap depth', depth, 0.3, 6.0)
    height = barn.number('mangold_heap height', height, 0.12, 3.0)
    loose = int(round(barn.number('mangold_heap loose', loose, 0, 400)))
    rng = shapes.rng_for(PART, seed)
    a, b, top = width / 2.0, depth, height
    wall = depth / 2.0

    def lift(x, y):
        """The heap's height over the ground at (x, y): a dome peaking against the wall, its foot flaring out."""
        d2 = (x / a) ** 2 + ((wall - y) / b) ** 2
        return top * (1.0 - d2) ** 1.25 if d2 < 1.0 else 0.0

    def normal(x, y):
        e = 0.01
        dx = (lift(x + e, y) - lift(x - e, y)) / (2 * e)
        dy = (lift(x, y + e) - lift(x, y - e)) / (2 * e)
        return Vector((-dx, -dy, 1.0)).normalized()

    def keep_clear(points):
        """Move a root off the wall (behind +Y) and out of the ground."""
        dy = max(p.y for p in points) - (wall - 0.004)
        dz = -min(p.z for p in points)
        return Vector((0.0, -max(0.0, dy), max(0.0, dz)))

    def resting(points):
        """A loose root lies on the ground: its lowest point at z = 0."""
        return Vector((0.0, 0.0, -min(p.z for p in points)))

    # the heap's surface, measured, so the number of roots follows its size
    area = 0.0
    steps = 30
    for i in range(steps):
        for j in range(steps):
            x = -a + 2 * a * (i + 0.5) / steps
            y = wall - b * (j + 0.5) / steps
            if lift(x, y) > 0.0:
                n = normal(x, y)
                area += (2 * a / steps) * (b / steps) / max(n.z, 0.2)

    roots = shapes.Shape()

    def one_root(point, n, depth_below, tilt):
        length = rng.uniform(*ROOT_LENGTH)
        radius = rng.uniform(*ROOT_RADIUS)
        t1 = n.cross(Vector((1.0, 0.0, 0.0)))
        if t1.length < 1e-3:
            t1 = n.cross(Vector((0.0, 1.0, 0.0)))
        t1.normalize()
        t2 = n.cross(t1).normalized()
        psi = rng.uniform(0, 2 * math.pi)
        along = t1 * math.cos(psi) + t2 * math.sin(psi)
        beta = rng.uniform(-tilt, tilt)
        axis = (along * math.cos(beta) + n * math.sin(beta)).normalized()
        centre = point - n * (depth_below + radius * 0.4)
        crown = centre - axis * (0.42 * length)
        matrix = shapes.to4(barn.root_frame(axis, rng.uniform(0, 2 * math.pi)), crown)
        barn.mangold(roots, matrix, length, radius, rng, adjust=keep_clear)

    def scatter(count, spacing, depth_below, reach, tilt):
        """Roots over the heap's surface, kept `spacing` apart (dart throwing on a grid)."""
        cells = {}
        placed = 0
        tries = 0
        while placed < count and tries < count * 40:
            tries += 1
            u = math.sqrt(rng.uniform(0.0, 1.0)) * reach
            phi = rng.uniform(0.0, math.pi)
            x, y = a * u * math.cos(phi), wall - b * u * math.sin(phi)
            p = Vector((x, y, lift(x, y)))
            key = (int(math.floor(p.x / spacing)), int(math.floor(p.y / spacing)), int(math.floor(p.z / spacing)))
            near = False
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for q in cells.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                            if (q - p).length < spacing:
                                near = True
                                break
                        if near:
                            break
                    if near:
                        break
                if near:
                    break
            if near:
                continue
            cells.setdefault(key, []).append(p)
            one_root(p, normal(x, y), depth_below, tilt)
            placed += 1

    scatter(int(area * 46) + 6, 0.12, 0.075, 0.97, 0.3)        # the layer under, half seen in the gaps
    scatter(int(area * 64) + 8, 0.10, 0.0, 1.0, 0.3)           # the outer layer
    # the heap's foot: roots lying on the ground round it, most along the foot, some pointing out
    rim = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b))) / 2.0
    for k in range(int(rim / 0.17)):
        phi = math.pi * (k + rng.uniform(0.2, 0.8)) / int(rim / 0.17)
        u = rng.uniform(0.9, 1.04)
        x, y = a * u * math.cos(phi), wall - b * u * math.sin(phi)
        out = Vector((math.cos(phi) / a, -math.sin(phi) / b, 0.0)).normalized()
        side = Vector((-out.y, out.x, 0.0))
        axis = (side if rng.random() < 0.6 else out) * rng.choice((-1, 1))
        axis = (axis + Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(-0.1, 0.15)))).normalized()
        length = rng.uniform(*ROOT_LENGTH)
        radius = rng.uniform(*ROOT_RADIUS)
        crown = Vector((x, y, radius)) - axis * (0.42 * length)
        matrix = shapes.to4(barn.root_frame(axis, rng.uniform(0, 2 * math.pi)), crown)
        barn.mangold(roots, matrix, length, radius, rng, adjust=lambda pts: keep_clear(pts) + resting(pts))
    # rolled loose in front
    for k in range(loose):
        phi = rng.uniform(0.12, 0.88) * math.pi
        u = rng.uniform(1.06, 1.36)
        x, y = a * u * math.cos(phi), wall - b * u * math.sin(phi)
        turn = rng.uniform(0, 2 * math.pi)
        axis = Vector((math.cos(turn), math.sin(turn), rng.uniform(-0.12, 0.12))).normalized()
        length = rng.uniform(*ROOT_LENGTH)
        radius = rng.uniform(*ROOT_RADIUS)
        crown = Vector((x, y, radius)) - axis * (0.42 * length)
        matrix = shapes.to4(barn.root_frame(axis, rng.uniform(0, 2 * math.pi)), crown)
        barn.mangold(roots, matrix, length, radius, rng, adjust=resting)
    objects = [roots.finish('mangold_heap roots', collection, barn.mangold_material(PART), smooth=True, sharp=None)]

    # the dark earth under and between the roots: the heap's own shape a little inside, closed at the wall
    core = shapes.Shape()
    nx, ny = max(8, int(width / 0.06)), max(6, int(depth / 0.06))
    sink = min(0.09, top * 0.18)
    grid = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -a + 2 * a * i / nx
            y = wall - b * j / ny
            z = max(0.002, lift(x, y) - sink)
            grid[i, j] = core.bm.verts.new((x, y, z))
    for i in range(nx):
        for j in range(ny):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all((((-a + 2 * a * ci / nx) / a) ** 2 + (((b * cj / ny)) / b) ** 2) < 1.02 for ci, cj in corners):
                core._face([grid[c] for c in corners])
    back = []
    for i in range(nx + 1):
        back.append(core.bm.verts.new((grid[i, 0].co.x, wall, 0.002)))
    for i in range(nx):
        if grid[i, 0].co.z > 0.004 or grid[i + 1, 0].co.z > 0.004:
            core._face([back[i], back[i + 1], grid[i + 1, 0], grid[i, 0]])
    core.bm.verts.ensure_lookup_table()
    loose_verts = [v for v in core.bm.verts if not v.link_faces]
    for v in loose_verts:
        core.bm.verts.remove(v)
    objects.append(core.finish('mangold_heap earth', collection, earth_material(), smooth=True, sharp=None))
    return objects
