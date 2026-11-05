"""
newspaper: a sheet of newspaper gone sodden in the rain, lying flat on wet ground: clinging to it, creased where it
was folded and where feet and wheels went over it, its edges torn, one corner turned back over itself; grey-buff
newsprint darkened and a little glossy where the water stands in it, no print showing.

Options:
    kind     'folded' (default): a broadsheet folded in half, two leaves, 0.44 x 0.30 m, its fold along one long edge;
             'sheet': one leaf opened out flat, 0.44 x 0.60 m, creased in quarters
    seed     the creases, the tears, which corner is turned back, the turn on the ground

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the sodden newspaper in the gutter (lines
1189-1208): a 0.36 x 0.28 m grid of 9 x 7 squares rippled by a sine, two corners left out as tears, in a plain made
'sodden newspaper' (line 790). Rebuilt here finer, with real creases (folds that stand as ridges and valleys), a
torn edge, two leaves for the folded paper, a corner turned back, and a made newsprint that is wet in patches.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_street_things as street  # noqa: E402

PART = 'newspaper'
KINDS = ('folded', 'sheet')

CARD = {
    'name': PART,
    'what': 'a sodden newspaper lying flat on wet ground: creased, torn at the edges, one corner turned back; grey-buff newsprint '
            'dark and glossy where wet, no print',
    'size_m': (0.46, 0.32, 0.012),
    'options': {
        'kind': "'folded' (default): a broadsheet folded in half, two leaves, 0.44 x 0.30 m; 'sheet': one leaf opened out flat, "
                "0.44 x 0.60 m, creased in quarters",
        'seed': 'the creases, the tears, which corner is turned back, the turn on the ground (default 0)',
    },
    'materials': ['PART • newspaper: sodden newsprint'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the sodden newspaper in the gutter (lines 1189-1208) and its "
              "material 'sodden newspaper' (line 790)",
    'views': 'made to be seen from above and at a low angle; from straight across it is a thin line',
    'trap': 'it lies 1 mm over z = 0 and is only 1 cm high at its creases: on uneven ground (setts, a rutted lane) the ground pokes '
            'through it; lay it on a flat patch (a flag, the gutter) or lift it to the ground\'s top',
}


def _height(x, y, creases, salt, w, l):
    """How high the sheet stands at (x, y): the creases as sharp ridges and valleys, soft lumps where it lies on grit."""
    z = 0.0
    for (p, d, depth, width) in creases:
        dist = abs((x - p.x) * d.y - (y - p.y) * d.x)
        z += depth * max(0.0, 1.0 - dist / width) ** 1.5
    z += 0.0018 * (mnoise.noise(Vector((x * 14.0, y * 14.0, 0.0)) + salt) + 0.6)
    # the edges lift a little where the paper has started to dry
    edge = min(x + w / 2, w / 2 - x, y + l / 2, l / 2 - y)
    z += 0.002 * max(0.0, 1.0 - edge / 0.03)
    return max(z, 0.0)


def _leaf(shape, w, l, nx, ny, base_z, creases, salt, rng, torn_edges, turn_back):
    """One leaf as a grid of faces: its outline torn along `torn_edges` ('left', 'right', 'front', 'back'), one
    corner folded back over it along a line (turn_back = (corner sign x, corner sign y, size)), all lifted
    by its height above the ground."""
    grid = []
    turned = set()
    sx, sy, size = turn_back
    fold_point = Vector((sx * (w / 2 - size), sy * l / 2, 0.0))
    fold_dir = Vector((sx * size, -sy * size * 0.9, 0.0)).normalized()
    fold_normal = Vector((-fold_dir.y, fold_dir.x, 0.0))
    corner = Vector((sx * w / 2, sy * l / 2, 0.0))
    if (corner - fold_point).dot(fold_normal) < 0:
        fold_normal = -fold_normal
    for i in range(nx + 1):
        col = []
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            x, y = (u - 0.5) * w, (v - 0.5) * l
            # tears: pull the torn edges in by a ragged amount
            if 'left' in torn_edges and i == 0:
                x += 0.004 + 0.012 * abs(mnoise.noise(Vector((0.0, y * 25.0, 1.0)) + salt))
            if 'right' in torn_edges and i == nx:
                x -= 0.004 + 0.012 * abs(mnoise.noise(Vector((1.0, y * 25.0, 2.0)) + salt))
            if 'front' in torn_edges and j == 0:
                y += 0.004 + 0.012 * abs(mnoise.noise(Vector((x * 25.0, 0.0, 3.0)) + salt))
            if 'back' in torn_edges and j == ny:
                y -= 0.004 + 0.012 * abs(mnoise.noise(Vector((x * 25.0, 1.0, 4.0)) + salt))
            p = Vector((x, y, 0.0))
            z = base_z + _height(x, y, creases, salt, w, l)
            side = (p - fold_point).dot(fold_normal)
            if side > 0:
                # the turned-back corner: mirrored over the fold line, lying on the leaf, a little higher at the fold
                p = p - fold_normal * (2 * side)
                z = base_z + _height(p.x, p.y, creases, salt, w, l) + 0.0016 + 0.003 * max(0.0, 1.0 - side / 0.02)
            vert = shape._verts([(p.x, p.y, z)])[0]
            if side > 0:
                turned.add(vert)
            col.append(vert)
        grid.append(col)
    for i in range(nx):
        for j in range(ny):
            quad = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            face = shape._face(quad)
            if face is not None and all(v in turned for v in quad):
                face.normal_flip()              # the turned-back corner was mirrored: its faces face up again


def build(collection, seed=0, kind='folded'):
    if kind not in KINDS:
        raise ValueError("newspaper kind is 'folded' or 'sheet', not %r" % (kind,))
    rng = shapes.rng_for(PART, seed)
    salt = Vector((rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100)))
    w, l = (0.44, 0.30) if kind == 'folded' else (0.44, 0.60)
    creases = []
    if kind == 'sheet':
        creases.append((Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), 0.006, 0.016))     # the fold across the middle
        creases.append((Vector((0.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), 0.003, 0.012))     # and the one down it
    for _ in range(5):
        a = rng.uniform(0, math.pi)
        creases.append((Vector((rng.uniform(-w / 3, w / 3), rng.uniform(-l / 3, l / 3), 0.0)), Vector((math.cos(a), math.sin(a), 0.0)),
                        rng.uniform(0.003, 0.0065), rng.uniform(0.008, 0.018)))
    corner = (rng.choice((-1, 1)), rng.choice((-1, 1)), rng.uniform(0.07, 0.11))
    sheet = shapes.Shape()
    nx, ny = (44, 30) if kind == 'folded' else (44, 60)
    if kind == 'folded':
        # the under leaf, then the upper; the fold runs along the back edge (+Y), the open edges torn a little
        _leaf(sheet, w, l, nx, ny, 0.0008, creases, salt, rng, ('front', 'right'), (corner[0], -1, 0.02))
        _leaf(sheet, w - 0.006, l - 0.004, nx, ny, 0.0022, creases, salt + Vector((0.3, 0.0, 0.0)), rng, ('front', 'left'), corner)
    else:
        _leaf(sheet, w, l, nx, ny, 0.0008, creases, salt, rng, ('left', 'front', 'back'), corner)
    sheet.transform(Matrix.Rotation(rng.uniform(-0.25, 0.25), 4, 'Z'))
    return [sheet.finish('newspaper', collection, street.newsprint_material(PART), smooth=True, sharp=70, normals=False)]
