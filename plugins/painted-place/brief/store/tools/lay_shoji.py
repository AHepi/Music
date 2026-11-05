"""
What this file does: fills openings in a wall you name with sliding paper screens (shoji), the way a Japanese inn's
rooms are closed off from the veranda: each opening gets a timber casing (a head beam, a grooved sill and side posts)
and two or more panels sliding in two tracks, each a little in front of the next where they pass; each panel is a thin
timber frame with a fine lattice of bars and paper behind it, a solid kick board at its foot where the opening comes
down to the floor. The paper is paper: pale, matte and a little translucent by day; `lit` makes chosen screens glow warm
from a room behind (the lattice dark against the light), `dim` a faint glow. A glowing screen lights nothing round it
by itself: give each lit opening a small warm light just outside it (the tool gives back where: made['light_points']).
Each panel's paper and each piece of timber is its own part of its picture (the number `pp_piece`). Nothing is placed
anywhere you did not say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_shoji
    made = lay_shoji.lay(inn, openings=[('front', 0.6, 0.0, 3.6, 1.9), ('front', 4.8, 0.9, 1.8, 1.0)], lit=[0], dim=[1], seed=2)
    for x, y, z in made['light_points']:                 # one small warm light (20 to 40 W) outside each lit opening
        ...

An opening is (side, metres from the side's left end, metres up from its foot, width, height), as lay_stone takes them
(a kind word after the side, 'door' or 'window', is allowed and ignored). Sides are named by the way they face in the
box's own axes: 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X); the left end is the left as you stand outside
facing the side.

From the command line:

    python3 lay_shoji.py --help
    python3 lay_shoji.py --blend IN.blend --object Inn --opening "front 0.6 0.0 3.6 1.9" --lit 0 --out OUT.blend

Options, with their defaults:
    openings      required    (side, from the left end, from the foot, width, height) in metres
    panels        0           panels in each opening; 0: about one for every 0.9 m of width, at least 2
    lattice       'tall'      'tall' (tall rectangles, as in an inn's rooms), 'square' (small squares) or 'rows'
                              (close rows of thin bars across)
    kick          None        the kick board's height at the foot of each panel, metres; None: 0.22 m where the opening
                              comes down to within 5 cm of the foot, else none; 0 for none
    lit           None        which openings glow warm: a list of their places in openings (0 is the first), True for
                              all, or a share from 0 to 1 picked by the seed
    dim           None        which openings glow faintly, in the same ways (an opening both lit and dim is lit)
    glow          1.0         how bright the lit paper glows (1.0 is about a room lit by a lamp; the look's lit glass)
    seed          0           each panel's paper and its timber's part of the picture, which openings `lit` picks
    collection    none        where the objects go (a new collection 'lay_shoji')
    timber_material 'SURFACE • old_planks_02'   (the casings, frames and lattice; the members lying across get a turned copy)

The result: {'frames': object (casings, frames, lattice, kick boards), 'paper': object (one face per panel; its slots
plain, lit and dim paper), 'light_points': [world (x, y, z) 0.45 m out in front of the middle of each lit opening],
'panels': how many panels}.
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

TIMBER_MATERIAL = 'SURFACE • old_planks_02'
LATTICES = ('tall', 'square', 'rows')
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x', '-y': '-y', '+y': '+y', '-x': '-x', '+x': '+x'}
CASING_W, CASING_D = 0.07, 0.11      # side posts' width, the casing's depth out from the wall's face
HEAD_H, SILL_H = 0.09, 0.045         # the head beam's and the sill's height
STILE, STILE_D = 0.03, 0.028         # a panel's stiles: width, depth
RAIL_TOP, RAIL_BOTTOM = 0.035, 0.05
BAR, BAR_D = 0.009, 0.014            # the lattice's bars
TRACKS = (0.075, 0.037)              # each track's middle, out from the wall's face

TOOL = {
    'name': 'lay_shoji',
    'what': "fills openings in a wall you name with sliding paper screens (shoji): a timber casing, two or more panels per opening in two tracks, each a thin frame with a fine lattice and paper behind it, a kick board at the foot; plain by day, lit warm or dim from a room behind",
    'call': "lay_shoji.lay(inn, openings=[('front', 0.6, 0.0, 3.6, 1.9), ('front', 4.8, 0.9, 1.8, 1.0)], lit=[0], dim=[1], seed=2)",
    'options': {
        'openings': "(side, metres from the side's left end, metres up from its foot, width, height), as lay_stone takes them; sides '-y'/'front', '+y'/'back', '+x'/'right', '-x'/'left' (required)",
        'panels': "panels in each opening (default 0: about one for every 0.9 m of width, at least 2)",
        'lattice': "'tall' (default: tall rectangles, as in an inn's rooms), 'square' (small squares) or 'rows' (close rows of thin bars across)",
        'kick': "the kick board's height at each panel's foot, metres (default None: 0.22 where the opening comes down to the floor, else none; 0 none)",
        'lit': "which openings glow warm: a list of their places in openings (0 is the first), True for all, or a share from 0 to 1 picked by the seed (default None: none); each still needs a small warm light outside it to light anything: made['light_points'] says where",
        'dim': "which openings glow faintly, in the same ways (default None)",
        'glow': "how bright the lit paper glows (default 1.0)",
        'seed': "each panel's part of the picture and shade, which openings a share picks (default 0)",
        'collection': "where the objects go (default a new collection 'lay_shoji')",
        'timber_material': "the casings, frames and lattice (default '%s'; the members lying across get a copy turned so the grain runs along them)" % TIMBER_MATERIAL,
    },
    'materials': [TIMBER_MATERIAL],
    'source': "the paper screens in '/home/claude/build-57-garden/first pass/render_final.py' (the inn's upper floor, lines 1253-1266: a glowing plane per bay with thin boxes over it, mat_glow at line 342) and the veranda's wall of screens (line 821), made into a tool: real sliding panels in two tracks inside a casing, a lattice of tall rectangles as in the board's photograph 12, kick boards, paper that is matte and a little translucent by day and glows warm or dim with the lattice dark against it, each panel its own shade",
    'trap': "a glowing screen lights nothing round it: put a small warm light (20 to 40 W) at each of made['light_points']; many lit screens side by side draw far too bright (lit paper is counted by its area): light one or two openings and dim the rest; the screens stand up to 0.11 m out from the wall's face, so a veranda's floor or a sill there must stop short of them or start under them",
}


class Build:
    def __init__(self):
        self.verts, self.faces, self.slots, self.pieces = [], [], [], []

    def face(self, points, slot=0, piece=0.5):
        start = len(self.verts)
        self.verts.extend(tuple(p) for p in points)
        self.faces.append(tuple(range(start, start + len(points))))
        self.slots.append(slot)
        self.pieces.append(piece)

    def block(self, centre, half, slot, piece):
        """A box from its centre and half sizes (in the frame's axes)."""
        cx, cy, cz = centre
        hx, hy, hz = half
        v = [(cx + sx * hx, cy + sy * hy, cz + sz * hz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        start = len(self.verts)
        self.verts.extend(v)
        for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
            self.faces.append(tuple(start + i for i in f))
            self.slots.append(slot)
            self.pieces.append(piece)

    def make(self, name, materials, collection, frame, ground):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', self.slots)
        attribute = mesh.attributes.new('pp_piece', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.pieces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.matrix_world = frame
        store.mark(obj, ground=ground)
        return obj


def _material(value):
    return store.material(value) if isinstance(value, str) else value


def paper_material(state, glow=1.0):
    """Shoji paper, made once per state: 'plain' (pale, matte, a little translucent), 'lit' (glowing warm) or 'dim'.
    Each panel's paper is a little lighter or darker by its number pp_piece; fibres and thicker patches show in it."""
    name = 'lay_shoji • paper %s' % state + ('' if state == 'plain' or abs(glow - 1.0) < 1e-6 else ' x%.2f' % glow)
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    nodes, links = tree.nodes, tree.links
    bsdf = nodes['Principled BSDF']
    out = nodes['Material Output']
    coords = nodes.new('ShaderNodeTexCoord')
    fibres = nodes.new('ShaderNodeTexNoise')               # long thin fibres and thicker patches in the paper
    fibres.inputs['Scale'].default_value = 38.0
    fibres.inputs['Detail'].default_value = 6.0
    fibres.inputs['Roughness'].default_value = 0.62
    links.new(coords.outputs['Object'], fibres.inputs['Vector'])
    patches = nodes.new('ShaderNodeTexNoise')
    patches.inputs['Scale'].default_value = 4.0
    patches.inputs['Detail'].default_value = 2.0
    links.new(coords.outputs['Object'], patches.inputs['Vector'])
    piece = nodes.new('ShaderNodeAttribute')
    piece.attribute_name = 'pp_piece'
    piece.attribute_type = 'GEOMETRY'
    shade = nodes.new('ShaderNodeMapRange')                # each panel 0.82 to 1.12 as bright
    shade.inputs['To Min'].default_value = 0.82
    shade.inputs['To Max'].default_value = 1.12
    links.new(piece.outputs['Fac'], shade.inputs['Value'])
    mix_f = nodes.new('ShaderNodeMath')
    mix_f.operation = 'MULTIPLY_ADD'
    mix_f.inputs[1].default_value = 0.35
    mix_f.inputs[2].default_value = 0.8                    # fibres: 0.8 to 1.15
    links.new(fibres.outputs['Fac'], mix_f.inputs[0])
    mix_p = nodes.new('ShaderNodeMath')
    mix_p.operation = 'MULTIPLY_ADD'
    mix_p.inputs[1].default_value = 0.3
    mix_p.inputs[2].default_value = 0.85                   # patches: 0.85 to 1.15
    links.new(patches.outputs['Fac'], mix_p.inputs[0])
    m1 = nodes.new('ShaderNodeMath')
    m1.operation = 'MULTIPLY'
    links.new(mix_f.outputs[0], m1.inputs[0])
    links.new(mix_p.outputs[0], m1.inputs[1])
    level = nodes.new('ShaderNodeMath')
    level.operation = 'MULTIPLY'
    links.new(m1.outputs[0], level.inputs[0])
    links.new(shade.outputs['Result'], level.inputs[1])
    paper = {'plain': (0.62, 0.58, 0.49, 1.0), 'dim': (0.40, 0.35, 0.28, 1.0)}.get(state, (0.26, 0.21, 0.15, 1.0))
    tint = nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    tint.inputs[6].default_value = paper
    links.new(level.outputs[0], tint.inputs[7])
    links.new(tint.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.92
    bsdf.inputs['Specular IOR Level'].default_value = 0.2
    # a little translucent: light from the other side comes through
    translucent = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(tint.outputs[2], translucent.inputs['Color'])
    both = nodes.new('ShaderNodeMixShader')
    both.inputs['Fac'].default_value = 0.3
    links.new(bsdf.outputs['BSDF'], both.inputs[1])
    links.new(translucent.outputs['BSDF'], both.inputs[2])
    links.new(both.outputs['Shader'], out.inputs['Surface'])
    if state in ('lit', 'dim'):
        colour = (1.0, 0.36, 0.09, 1.0) if state == 'lit' else (0.85, 0.42, 0.18, 1.0)
        strength = (1.5 if state == 'lit' else 0.1) * glow
        warm = nodes.new('ShaderNodeMix')
        warm.data_type = 'RGBA'
        warm.blend_type = 'MULTIPLY'
        warm.inputs['Factor'].default_value = 1.0
        warm.inputs[6].default_value = colour
        links.new(level.outputs[0], warm.inputs[7])
        links.new(warm.outputs[2], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = strength
    return mat


def _turned(material, axis):
    try:
        import lay_stone
        return lay_stone.turned_along(material, axis)
    except Exception:
        return material


def _pick(value, count, rng, what):
    """Which openings: a list of places, True for all, a share 0..1, or None."""
    if value is None or value is False:
        return set()
    if value is True:
        return set(range(count))
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0 and not isinstance(value, int):
        chosen = list(range(count))
        rng.shuffle(chosen)
        return set(chosen[:int(round(float(value) * count))])
    try:
        places = {int(v) for v in value}
    except TypeError:
        raise ValueError('%s is a list of places in openings, True, or a share from 0 to 1, not %r' % (what, value))
    for v in places:
        if not 0 <= v < count:
            raise ValueError('%s names opening %d, but there are %d openings' % (what, v, count))
    return places


def side_frame(low, high, side):
    """The side's own axes in the box's frame: its left end (seen from outside, at the foot), the way along, the way out."""
    name = SIDE_NAMES.get(side)
    if name is None:
        raise ValueError("a side is 'front', 'back', 'left' or 'right', not %r" % (side,))
    if name == '-y':
        return Vector((low.x, low.y, low.z)), Vector((1, 0, 0)), Vector((0, -1, 0)), high.x - low.x, 'x'
    if name == '+y':
        return Vector((high.x, high.y, low.z)), Vector((-1, 0, 0)), Vector((0, 1, 0)), high.x - low.x, 'x'
    if name == '-x':
        return Vector((low.x, high.y, low.z)), Vector((0, -1, 0)), Vector((-1, 0, 0)), high.y - low.y, 'y'
    return Vector((high.x, low.y, low.z)), Vector((0, 1, 0)), Vector((1, 0, 0)), high.y - low.y, 'y'


def lay(wall, openings, panels=0, lattice='tall', kick=None, lit=None, dim=None, glow=1.0, seed=0, collection=None,
        timber_material=TIMBER_MATERIAL):
    """Fill the openings with sliding paper screens (see the note at the top)."""
    if wall is None or wall.type != 'MESH':
        raise ValueError('lay_shoji needs a mesh object (the wall)')
    if lattice not in LATTICES:
        raise ValueError("lattice is 'tall', 'square' or 'rows', not %r" % (lattice,))
    panels = int(panels or 0)
    if panels < 0 or panels == 1 or panels > 12:
        raise ValueError('panels is 2 to 12 (or 0 to choose by the width), not %r' % (panels,))
    glow = float(glow)
    if not 0.0 < glow <= 5.0:
        raise ValueError('glow is above 0 and at most 5, not %r' % (glow,))
    openings = list(openings)
    if not openings:
        raise ValueError('lay_shoji needs at least one opening')
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    lit_set = _pick(lit, len(openings), rng, 'lit')
    dim_set = _pick(dim, len(openings), rng, 'dim') - lit_set
    location, rotation, _ = wall.matrix_world.decompose()
    frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_box = frame.inverted()
    corners = [to_box @ (wall.matrix_world @ Vector(c)) for c in wall.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    ground = location.z + low.z
    wood = Build()          # slots: 0 upright grain, 1 across along x, 2 across along y
    paper = Build()         # slots: 0 plain, 1 lit, 2 dim
    light_points = []
    count = 0
    for index, opening in enumerate(openings):
        opening = list(opening)
        if len(opening) == 6:
            opening = [opening[0]] + opening[2:]
        if len(opening) != 5:
            raise ValueError('an opening is (side, from the left end, from the foot, width, height), not %r' % (tuple(opening),))
        side, along0, up0, width, height = opening[0], float(opening[1]), float(opening[2]), float(opening[3]), float(opening[4])
        origin, along, out, length, axis = side_frame(low, high, side)
        if width < 0.5 or height < 0.5:
            raise ValueError('opening %d is %.2f x %.2f m: at least 0.5 x 0.5 m' % (index, width, height))
        if along0 < -1e-6 or along0 + width > length + 1e-6 or up0 < -1e-6 or up0 + height > high.z - low.z + 1e-6:
            raise ValueError('opening %d does not fit on the %s side (%.2f m long, %.2f m high)' % (index, side, length, high.z - low.z))
        across = 1 if axis == 'x' else 2
        up = Vector((0, 0, 1))

        def at(a, z, o):
            return origin + along * a + up * z + out * o

        def member(a0, a1, z0, z1, o0, o1, slot, piece):
            """A block between two places along, two heights and two depths out from the face."""
            c = at((a0 + a1) / 2, (z0 + z1) / 2, (o0 + o1) / 2)
            ha, hz, ho = abs(a1 - a0) / 2, abs(z1 - z0) / 2, abs(o1 - o0) / 2
            half = Vector((abs(along.x) * ha + abs(out.x) * ho, abs(along.y) * ha + abs(out.y) * ho, hz))
            wood.block(c, half, slot, piece)

        a0, a1 = along0, along0 + width
        z0, z1 = up0, up0 + height
        # the casing: side posts, head beam, grooved sill
        member(a0 - CASING_W, a0, z0, z1 + HEAD_H, 0.0, CASING_D, 0, rng.random())
        member(a1, a1 + CASING_W, z0, z1 + HEAD_H, 0.0, CASING_D, 0, rng.random())
        member(a0 - CASING_W - 0.02, a1 + CASING_W + 0.02, z1, z1 + HEAD_H, 0.0, CASING_D + 0.01, across, rng.random())
        member(a0 - CASING_W, a1 + CASING_W, z0, z0 + SILL_H, 0.0, CASING_D + 0.005, across, rng.random())
        # the panels, in two tracks, each passing over the next by a stile's width
        n = panels or max(2, int(round(width / 0.9)))
        pw = (width + (n - 1) * STILE) / n
        bottom = z0 + SILL_H
        top = z1 - 0.004
        kick_h = kick if kick is not None else (0.22 if up0 < 0.05 else 0.0)
        kick_h = max(0.0, min(float(kick_h), 0.4 * (top - bottom)))
        state = 1 if index in lit_set else (2 if index in dim_set else 0)
        for i in range(n):
            pa0 = a0 + i * (pw - STILE)
            pa1 = pa0 + pw
            track = TRACKS[i % 2]
            f0, f1 = track - STILE_D / 2, track + STILE_D / 2
            pc = rng.random()
            member(pa0, pa0 + STILE, bottom, top, f0, f1, 0, pc)
            member(pa1 - STILE, pa1, bottom, top, f0, f1, 0, rng.random())
            member(pa0 + STILE, pa1 - STILE, top - RAIL_TOP, top, f0, f1, across, rng.random())
            member(pa0 + STILE, pa1 - STILE, bottom, bottom + RAIL_BOTTOM, f0, f1, across, rng.random())
            low_z = bottom + RAIL_BOTTOM
            if kick_h > 0.0:
                member(pa0 + STILE, pa1 - STILE, low_z, bottom + kick_h, f0 + 0.006, f1 - 0.006, 0, rng.random())
                member(pa0 + STILE, pa1 - STILE, bottom + kick_h, bottom + kick_h + RAIL_BOTTOM * 0.7, f0, f1, across, rng.random())
                low_z = bottom + kick_h + RAIL_BOTTOM * 0.7
            high_z = top - RAIL_TOP
            # the lattice, on the outer side of the paper
            ia0, ia1 = pa0 + STILE, pa1 - STILE
            inner_w, inner_h = ia1 - ia0, high_z - low_z
            if lattice == 'rows':
                verticals = 2
                rows = max(3, int(round(inner_h / 0.09)))
            else:
                verticals = max(1, int(round(inner_w / 0.19)) - 1)
                cell_w = inner_w / (verticals + 1)
                rows = max(2, int(round(inner_h / (cell_w * (1.45 if lattice == 'tall' else 1.0)))))
            b0, b1 = f1 - BAR_D, f1
            for k in range(1, verticals + 1):
                a = ia0 + inner_w * k / (verticals + 1)
                member(a - BAR / 2, a + BAR / 2, low_z, high_z, b0, b1, 0, rng.random())
            for k in range(1, rows):
                z = low_z + inner_h * k / rows
                member(ia0, ia1, z - BAR / 2, z + BAR / 2, b0 - 0.001, b1 - 0.001, across, rng.random())
            # the paper, just behind the lattice
            po = b0 - 0.004
            quad = [at(ia0, low_z, po), at(ia1, low_z, po), at(ia1, high_z, po), at(ia0, high_z, po)]
            normal = (quad[1] - quad[0]).cross(quad[3] - quad[0])
            if normal.dot(out) < 0:
                quad.reverse()
            paper.face(quad, state, rng.random())
            count += 1
        if state == 1:
            light_points.append(tuple(frame @ at((a0 + a1) / 2, (z0 + z1) / 2, 0.45)))
    if collection is None:
        collection = bpy.data.collections.new('lay_shoji')
        bpy.context.scene.collection.children.link(collection)
    timber = _material(timber_material)
    frames_obj = wood.make('shoji frames', [timber, _turned(timber, 'x'), _turned(timber, 'y')], collection, frame, ground)
    paper_obj = paper.make('shoji paper', [paper_material('plain'), paper_material('lit', glow), paper_material('dim', glow)], collection, frame, ground)
    paper_obj.visible_shadow = False            # light from a lamp behind comes through
    frames_obj['panels'] = count
    paper_obj['lit'] = len(lit_set)
    paper_obj['dim'] = len(dim_set)
    return {'frames': frames_obj, 'paper': paper_obj, 'light_points': light_points, 'panels': count}


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the wall (a box)')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--opening', action='append', default=[], help='"side from foot width height", e.g. "front 0.6 0.0 3.6 1.9" (repeat for more)')
    parser.add_argument('--panels', type=int, default=0, help='panels per opening; default 0 (by the width)')
    parser.add_argument('--lattice', choices=LATTICES, default='tall', help='default tall')
    parser.add_argument('--lit', type=int, action='append', default=None, help='an opening that glows warm (its place, from 0; repeat for more)')
    parser.add_argument('--dim', type=int, action='append', default=None, help='an opening that glows faintly (repeat for more)')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out and args.opening):
        parser.error('--blend, --object, --out and at least one --opening are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    wall = bpy.data.objects.get(args.object)
    if wall is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    openings = []
    for text in args.opening:
        parts = text.split()
        if len(parts) != 5:
            parser.error('an opening is five words: side from foot width height (got %r)' % text)
        openings.append((parts[0],) + tuple(float(v) for v in parts[1:]))
    made = lay(wall, openings, panels=args.panels, lattice=args.lattice, lit=args.lit, dim=args.dim, seed=args.seed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%d panels in %d openings; saved %s' % (made['panels'], len(openings), args.out))


if __name__ == '__main__':
    main()
