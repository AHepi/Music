"""
What this file does: lays see-through stains where you say, the way the chapel builders dressed their walls and
ground: a thin plane a few millimetres in front of a wall (soot under a sill or cornice, damp at a wall's foot, a rust
run under a bracket or pipe joint, mud splashed low) or a soft ragged smear lying on the ground (mud by a doorstep,
coal dust under a scuttle, ash carried out on boots, damp along a kerb). The plane itself is plain; the stain's
strength is a number written on its points ('fade', 0 strongest, 1 gone) that the stain materials read and break up
with noise; soot, damp and rust are streaked downwards. Four heavy kinds (heavy soot, far soot, heavy damp, leak) are
pushed hard enough to show on fronts 15 to 35 m away: they hold nearly full strength and stop at a ragged edge. Nothing
here chooses where a stain goes.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import stain
    soot = stain.on_wall(wall, 'front', 1.2, 2.3, 1.0, 2.3, kind='soot', strong_at='top', seed=1)      # under a sill
    damp = stain.on_wall(wall, 'front', 0.0, 6.0, 0.0, 1.1, kind='damp', strong_at='bottom')             # at the foot
    rust = stain.on_wall(wall, 'front', 3.0, 3.4, 0.5, 2.6, kind='rust', strong_at='top', strength=0.8)  # under a bracket
    mud = stain.on_ground((1.0, -0.4, 0.0), size=(0.9, 0.5), kind='mud', turn=15, seed=2)              # by a doorstep
    dust = stain.on_ground((2.0, 1.0, 0.0), size=(0.5, 0.35), kind='coal dust', ground=my_ground, strength=0.4)

On a stone front from lay_stone (its blocks stand 0.20 to 0.24 m out), set the stains out in front of the blocks with
offset='front' (or the metres, offset=0.24), and use the heavy kinds for fronts seen from across a street. The third
street builder's wear, as calls (a window's opening from u0 to u1 along the front and from z to z + h up):

    stain.on_wall(wall, 'front', u0 - 0.12, u1 + 0.12, z - 0.27 - 1.4, z - 0.27, kind='heavy soot', strength=1.15,
                  offset='front', taper=0.5, seed=1)                              # a soot run under a sill
    stain.on_wall(wall, 'front', u0 - 0.16, u1 + 0.16, z + h + 0.2, z + h + 1.0, kind='heavy soot', strong_at='bottom',
                  strength=0.95, offset='front', taper=0.6)                       # soot over a window head
    stain.on_wall(wall, 'front', 0.0, width, top - 2.3, top, kind='heavy soot', strength=1.25, offset='front',
                  uneven=0.3)                                                     # a soot band under the eaves
    stain.on_wall(wall, 'front', 0.0, width, 0.0, 1.2, kind='heavy damp', strong_at='bottom', offset='front',
                  uneven=0.35)                                                    # rising damp, its salt line on top
    stain.on_wall(wall, 'front', 3.0, 3.5, top - 3.0, top - 0.2, kind='leak', strength=1.2, offset='front',
                  taper=0.4)                                                      # a gutter leak under a joint
    (kind='far soot' for fronts 25 m and more away: broader runs.)

on_wall(wall, side, x0, x1, z0, z1, ...): `wall` is a box-like object; `side` names its face in its own axes, as the
boards and stone tools name them: 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X). x0 and x1 are metres along
that side from its left end as you see it standing outside facing it; z0 and z1 are metres up from the wall's foot.
The plane stands `offset` (4 mm) in front of the face, with its own origin at its middle.
on_ground(location, size, ...): `location` is the smear's middle (z is the ground height when no `ground` is given);
`size` = (rx, ry), its half-lengths along and across before `turn`; with `ground` (a mesh object) the smear is draped
onto it by rays cast straight down.

From the command line:

    python3 stain.py --help
    python3 stain.py --blend IN.blend --wall Chapel --side front --from 1.2 2.3 --up 1.0 2.3 --kind soot --strong-at top --out OUT.blend
    python3 stain.py --blend IN.blend --ground-at 1.0 -0.4 0.0 --size 0.9 0.5 --kind mud --turn 15 --out OUT.blend

Options, with their defaults:
    kind          'soot' on a wall, 'mud' on the ground;  on a wall: 'soot', 'damp', 'rust', 'mud', and the heavy
                  'heavy soot', 'far soot', 'heavy damp' (with a salt line), 'leak'; on the ground: 'mud', 'coal dust',
                  'ash', 'damp'
    strong_at     'top'      which end of the wall plane the stain is strongest at: 'top' or 'bottom'
    strength      1.0        how strong at its strongest (a wall); 0.7 for a ground smear; it scales 'fade' (above 1
                             the strongest part grows)
    seed          0          the plane's edge softening and the smear's ragged outline (the material's noise is fixed)
    offset        0.004 m    how far the wall plane stands off the face, metres; or 'front': in front of lay_stone's
                             blocks (the relief it wrote on the wall, 'stone_front', plus 0.04 m: 0.24 m by default)
    taper         1.0        how wide the wall plane is at its weak end, as a share of its strong end (0.4: a run
                             gathering into streaks as it goes down); 1 leaves it square
    uneven        0.0        how far the wall plane's weak end wanders, as a share of its height (0.3: a tide line
                             or a soot band's lower edge that rises and falls along the wall); 0 leaves it straight
    lift          0.006 m    how far the ground smear sits above the ground
    turn          0          degrees about Z the ground smear's rx is turned
    ground        none       a mesh object to drape the ground smear onto
    raggedness    1.0        how broken the ground smear's outline is (0 an ellipse, 2 very ragged)
    collection    none       where the planes go (default: a new collection 'stain')
    material      none       a material of your own instead of the kind's 'MADE • stain <kind>'

Each call returns one object ('stain soot on wall front', 'smear mud'), casting no shadow, carrying 'fade' 0..1.

Trap (from the chapel dresser): a smear laid over glossy ground kills its shine where it lies, even faint; keep ground
smears thin (strength well under 0.5 on a wet or polished surface) and off puddles and polished paths altogether.
Trap (from the third street builder): lay_stone's blocks stand 0.20 to 0.24 m out, so a plane at the default 4 mm is
hidden behind them; use offset='front'. A stain on a front 15 to 35 m away shows only big and heavy: judge it in a drawn
picture at full size, never by its numbers; on side fronts seen edge-on only the broad ones read.
"""

import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

KINDS = ('soot', 'damp', 'rust', 'mud', 'coal dust', 'ash', 'heavy soot', 'far soot', 'heavy damp', 'leak')
HEAVY = ('heavy soot', 'far soot', 'heavy damp', 'leak')
SIDES = {'front': '-y', 'back': '+y', 'left': '-x', 'right': '+x', '-y': '-y', '+y': '+y', '-x': '-x', '+x': '+x'}
PAST_THE_RELIEF = 0.04     # lay_stone's block faces stand up to 0.037 m past the relief it writes ('stone_front')

TOOL = {
    'name': 'stain',
    'what': 'see-through stains where you say: a streaked plane in front of a wall face (soot under a sill, damp at the foot, a rust run under a bracket; heavy soot, rising damp with a salt line and leak runs that show on fronts 15 to 35 m away) or a soft ragged smear on the ground (mud, coal dust, ash, damp)',
    'call': "stain.on_wall(wall, 'front', 1.2, 2.3, 1.0, 2.3, kind='soot', strong_at='top', seed=1);  stain.on_wall(stone_wall, 'front', 0, 9, 0, 1.2, kind='heavy damp', strong_at='bottom', offset='front', uneven=0.35);  stain.on_ground((1.0, -0.4, 0.0), size=(0.9, 0.5), kind='mud', turn=15, ground=my_ground)",
    'options': {
        'wall, side, x0, x1, z0, z1': "the box-like object and its face ('front' -Y, 'back' +Y, 'left' -X, 'right' +X); metres along the side from its left end seen from outside, and up from its foot",
        'kind': "'soot', 'damp', 'rust', 'mud' on a wall (default 'soot'), or the heavy 'heavy soot', 'far soot' (fronts 25 m and more away), 'heavy damp' (a salt line on its edge), 'leak'; 'mud', 'coal dust', 'ash', 'damp' on the ground (default 'mud')",
        'strong_at': "'top' or 'bottom': where the wall stain is strongest ('top')",
        'strength': 'how strong at its strongest, scaling the fade (1.0 on a wall, 0.7 on the ground)',
        'taper': "the wall plane's width at its weak end as a share of its strong end: 0.4 a run gathering into streaks; 1 square (1.0)",
        'uneven': "how far the wall plane's weak end wanders, as a share of its height: 0.3 a tide line or soot band rising and falling; 0 straight (0.0)",
        'location, size, turn': "the ground smear's middle (x, y, z), half-lengths (rx, ry) and turn in degrees",
        'ground': 'a mesh object to drape the ground smear onto (none: flat at z)',
        'raggedness': "how broken the smear's outline is: 0 an ellipse, 1 normal, 2 very ragged (1)",
        'offset, lift': "the wall plane off its face in metres (0.004 m), or 'front': in front of lay_stone's blocks (0.24 m on its default relief); the ground smear above the ground (0.006 m)",
        'seed': "the plane's edge softening, the smear's outline (0)",
        'collection': "where the planes go (a new collection 'stain')",
        'material': "your own material instead of 'MADE • stain <kind>'",
    },
    'materials': ['MADE • stain %s' % kind for kind in KINDS],
    'source': "`stain` in the chapel builder's '51 chapel - render_final.py' (line 561) and `smear` in the dresser's 'dress_block.py' (line 277), made into a tool; the heavy kinds, offset 'front', taper and uneven from `wear_mat` and `wall_stain` in '/home/claude/build-55-street/fronts/render_final.py' (lines 1383 and 1464), with the salt line its notes ask for and its runs of rising damp made one uneven plane",
    'trap': "a smear over glossy ground kills its shine where it lies: keep ground smears thin (strength well under 0.5 on wet or polished ground) and off puddles and polished paths; on lay_stone's fronts a plane at the default 4 mm is hidden behind the blocks: use offset='front'",
}

UP = Vector((0.0, 0.0, 1.0))


def _material(kind, material):
    if material is not None:
        return store.material(material) if isinstance(material, str) else material
    if kind not in KINDS:
        raise ValueError('kind is one of %s, not %r' % (', '.join(repr(k) for k in KINDS), kind))
    return store.material('MADE • stain %s' % kind)


def _collection(collection):
    if collection is None:
        collection = bpy.data.collections.new('stain')
        bpy.context.scene.collection.children.link(collection)
    return collection


def _object(name, verts, faces, fade, collection, material, origin, ground, smooth=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(Vector(v) - origin) for v in verts], [], faces)
    layer = mesh.attributes.new('fade', 'FLOAT', 'POINT')
    layer.data.foreach_set('value', [float(min(1.0, max(0.0, f))) for f in fade])
    mesh.update()
    if smooth:
        mesh.shade_smooth()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = origin
    obj.visible_shadow = False
    collection.objects.link(obj)
    store.use_material(obj, material, ground=ground)
    bpy.context.view_layer.update()                      # so its world matrix carries its place at once
    return obj


# ------------------------------------------------------------------------------------------------ on a wall

def wall_side(wall, side):
    """The named face of a box-like object, in the world: its origin (the left end at the foot, seen from outside),
    `along` (to the right), `normal` (out), its length and height."""
    if side not in SIDES:
        raise ValueError("side is 'front', 'back', 'left' or 'right' (or '-y', '+y', '-x', '+x'), not %r" % (side,))
    name = SIDES[side]
    axis = 0 if name[1] == 'x' else 1
    sign = 1.0 if name[0] == '+' else -1.0
    corners = [Vector(c) for c in wall.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    matrix = wall.matrix_world
    local_normal = Vector((0.0, 0.0, 0.0))
    local_normal[axis] = sign
    normal = (matrix.to_3x3() @ local_normal)
    normal.z = 0.0
    normal.normalize()
    along = Vector((-normal.y, normal.x, 0.0)).normalized()
    other = 1 - axis
    plane = high[axis] if sign > 0 else low[axis]
    points = []
    for o in (low[other], high[other]):
        p = Vector((0.0, 0.0, low.z))
        p[axis] = plane
        p[other] = o
        points.append(matrix @ p)
    top = matrix @ Vector((plane if axis == 0 else low.x, plane if axis == 1 else low.y, high.z))
    left = min(points, key=lambda p: p.dot(along))
    length = abs((points[1] - points[0]).dot(along))
    foot_z = min(p.z for p in points)
    return {'origin': Vector((left.x, left.y, foot_z)), 'along': along, 'normal': normal, 'length': length, 'height': top.z - foot_z}


def set_out(wall, offset):
    """The distance the wall plane stands off the face: `offset` in metres, or 'front': in front of lay_stone's blocks,
    the relief it wrote on the wall ('stone_front') plus PAST_THE_RELIEF."""
    if isinstance(offset, str):
        if offset != 'front':
            raise ValueError("offset is metres or 'front', not %r" % (offset,))
        relief = wall.get('stone_front')
        if relief is None:
            raise ValueError("offset='front' needs a wall built by lay_stone (it writes 'stone_front' on the wall); %r carries "
                             "none: give the metres instead (lay_rubble's stones stand about 0.085 m out)" % wall.name)
        return float(relief) + PAST_THE_RELIEF
    offset = float(offset)
    if not 0.0 <= offset <= 2.0:
        raise ValueError('offset is 0 to 2 m, not %r' % (offset,))
    return offset


def on_wall(wall, side, x0, x1, z0, z1, kind='soot', strong_at='top', strength=1.0, seed=0, offset=0.004, collection=None,
            material=None, across=8, down=14, taper=1.0, uneven=0.0):
    """A stain plane in front of the wall's face, from x0 to x1 along it and z0 to z1 up it; returns the object."""
    if strong_at not in ('top', 'bottom'):
        raise ValueError("strong_at is 'top' or 'bottom', not %r" % (strong_at,))
    if x1 <= x0 or z1 <= z0:
        raise ValueError('x0 < x1 and z0 < z1 are needed (got %s to %s along, %s to %s up)' % (x0, x1, z0, z1))
    if not 0.05 <= taper <= 1.0:
        raise ValueError('taper is 0.05 (a thin run at its weak end) to 1 (as wide as its strong end), not %r' % (taper,))
    if not 0.0 <= uneven <= 0.8:
        raise ValueError('uneven is 0 (a straight end) to 0.8 (its weak end wandering by 80%% of its height), not %r' % (uneven,))
    rng = random.Random(seed)
    face = wall_side(wall, side)
    base = face['origin'] + face['normal'] * set_out(wall, offset)
    along, normal = face['along'], face['normal']
    verts, fade, faces = [], [], []
    wobble = [Vector((rng.uniform(-40, 40), rng.uniform(-40, 40), 0.0)) for _ in range(2)]
    if uneven > 0:
        across = max(across, int(math.ceil((x1 - x0) / 0.2)))                 # fine enough for the wandering end to show
        wander = Vector((rng.uniform(-60, 60), rng.uniform(-60, 60), 0.0))
    middle = (x0 + x1) / 2
    for j in range(down + 1):
        v = j / down
        z = z0 + (z1 - z0) * v
        gradient = v if strong_at == 'top' else 1.0 - v                       # 1 at the strong end
        narrowing = taper + (1.0 - taper) * gradient                          # 1 at the strong end, taper at the weak end
        for i in range(across + 1):
            u = i / across
            x = x0 + (x1 - x0) * u
            if uneven > 0:
                # the weak end wanders: here the stain reaches only part of the way, a smooth noise along the wall
                reach = 1.0 - uneven * min(1.0, max(0.0, 0.5 + 0.9 * noise.noise(Vector((x * 0.7, 0.0, 0.0)) + wander)))
                gradient = max(0.0, 1.0 - (1.0 - (v if strong_at == 'top' else 1.0 - v)) / reach)
            if taper < 1.0:
                x = middle + (x - middle) * narrowing
            verts.append(base + along * x + UP * z)
            # softened at the two side edges and ragged there, so the plane never ends in a hard line
            edge = min(u, 1.0 - u) / 0.2
            edge += 0.35 * noise.noise(Vector((x * 2.0, z * 2.0, 0.0)) + wobble[0])
            soft = min(1.0, max(0.0, edge))
            held = gradient ** 0.8 * soft
            fade.append(1.0 - strength * held)
    for j in range(down):
        for i in range(across):
            a = j * (across + 1) + i
            faces.append((a, a + 1, a + across + 2, a + across + 1))          # faces out: along x up = the face's normal
    origin = base + along * ((x0 + x1) / 2) + UP * ((z0 + z1) / 2)
    name = 'stain %s on wall %s' % (kind, side)
    obj = _object(name, verts, faces, fade, _collection(collection), _material(kind, material), origin, face['origin'].z)
    obj['stain_kind'] = kind
    return obj


# ------------------------------------------------------------------------------------------------ on the ground

def _ground_height(ground, x, y, fallback, depsgraph=None):
    if ground is None:
        return fallback
    corners = [ground.matrix_world @ Vector(c) for c in ground.bound_box]
    above = max(c.z for c in corners) + 1.0
    to_local = ground.matrix_world.inverted()
    start = to_local @ Vector((x, y, above))
    down = (to_local.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    hit, location, _, _ = ground.ray_cast(start, down, distance=1.0e5, depsgraph=depsgraph)
    return (ground.matrix_world @ location).z if hit else fallback


def on_ground(location, size=(0.6, 0.4), kind='mud', turn=0.0, ground=None, strength=0.7, seed=0, lift=0.006,
              raggedness=1.0, collection=None, material=None, rings=5, segments=32):
    """A soft ragged smear lying on the ground with its middle at `location`; returns the object."""
    rng = random.Random(seed)
    location = Vector(location)
    rx, ry = float(size[0]), float(size[1])
    depsgraph = bpy.context.evaluated_depsgraph_get() if ground is not None else None
    if ground is not None:
        bpy.context.view_layer.update()
    turning = Matrix.Rotation(math.radians(turn), 3, 'Z')
    phases = [rng.uniform(0, math.tau) for _ in range(4)]
    amounts = [rng.uniform(0.04, 0.22) * raggedness for _ in range(4)]
    shift = Vector((rng.uniform(-30, 30), rng.uniform(-30, 30), 0.0))

    def wobble(angle):
        return 1.0 + sum(amounts[k] * math.sin((k + 2) * angle + phases[k]) for k in range(4))

    verts, fade, faces = [location.copy()], [1.0 - strength], []
    for r in range(1, rings + 1):
        t = r / rings
        for i in range(segments):
            angle = math.tau * i / segments
            w = wobble(angle) if r == rings else 1.0 + (wobble(angle) - 1.0) * t
            local = Vector((math.cos(angle) * rx * t * w, math.sin(angle) * ry * t * w, 0.0))
            spot = location + turning @ local
            z = _ground_height(ground, spot.x, spot.y, location.z, depsgraph) + lift
            verts.append(Vector((spot.x, spot.y, z)))
            patchy = 0.3 * raggedness * noise.noise(Vector((spot.x * 3.0, spot.y * 3.0, 0.0)) + shift) * (4 * t * (1 - t))
            fade.append(1.0 - strength * max(0.0, min(1.0, (1.0 - t ** 1.4) - patchy)))
    verts[0].z = _ground_height(ground, location.x, location.y, location.z, depsgraph) + lift
    for i in range(segments):
        faces.append((0, 1 + i, 1 + (i + 1) % segments))
    for r in range(rings - 1):
        inner, outer = 1 + r * segments, 1 + (r + 1) * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((inner + i, outer + i, outer + j, inner + j))
    for k in range(1 + (rings - 1) * segments, len(fade)):
        fade[k] = 1.0                                                           # the very rim is gone
    obj = _object('smear %s' % kind, verts, faces, fade, _collection(collection), _material(kind, material), Vector((location.x, location.y, verts[0].z - lift)),
                  verts[0].z - lift, smooth=True)
    obj['stain_kind'] = kind
    return obj


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of stain.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', required=False, help='the .blend file to open')
    parser.add_argument('--wall', help='the box-like object to stain (a wall stain)')
    parser.add_argument('--side', default='front', help="its face: front, back, left or right; default front")
    parser.add_argument('--from', dest='along', type=float, nargs=2, metavar=('X0', 'X1'), help='metres along the side from its left end')
    parser.add_argument('--up', type=float, nargs=2, metavar=('Z0', 'Z1'), help='metres up from the wall\'s foot')
    parser.add_argument('--strong-at', default='top', choices=('top', 'bottom'), help='default top')
    parser.add_argument('--ground-at', type=float, nargs=3, metavar=('X', 'Y', 'Z'), help="a ground smear's middle")
    parser.add_argument('--size', type=float, nargs=2, metavar=('RX', 'RY'), default=(0.6, 0.4), help='the smear\'s half-lengths; default 0.6 0.4')
    parser.add_argument('--turn', type=float, default=0.0, help='degrees about Z; default 0')
    parser.add_argument('--ground', help='a ground mesh object to drape the smear onto')
    parser.add_argument('--kind', default=None, help="soot, damp, rust, mud, 'coal dust', ash, 'heavy soot', 'far soot', 'heavy damp' or leak; default soot on a wall, mud on the ground")
    parser.add_argument('--strength', type=float, default=None, help='how strong at its strongest; default 1.0 on a wall, 0.7 on the ground')
    parser.add_argument('--offset', default='0.004', help="metres the wall plane stands off the face, or front (in front of lay_stone's blocks); default 0.004")
    parser.add_argument('--taper', type=float, default=1.0, help="the wall plane's width at its weak end, as a share; default 1")
    parser.add_argument('--uneven', type=float, default=0.0, help="how far the wall plane's weak end wanders, as a share of its height; default 0")
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not args.blend:
        parser.error('--blend is needed (the wall or ground is in it)')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    if args.wall:
        if args.wall not in bpy.data.objects:
            parser.error('no object %r in %s' % (args.wall, args.blend))
        if not (args.along and args.up):
            parser.error('--from X0 X1 and --up Z0 Z1 are needed for a wall stain')
        offset = args.offset if args.offset == 'front' else float(args.offset)
        made = on_wall(bpy.data.objects[args.wall], args.side, args.along[0], args.along[1], args.up[0], args.up[1],
                       kind=args.kind or 'soot', strong_at=args.strong_at, strength=1.0 if args.strength is None else args.strength, seed=args.seed,
                       offset=offset, taper=args.taper, uneven=args.uneven)
    elif args.ground_at:
        ground = None
        if args.ground:
            if args.ground not in bpy.data.objects:
                parser.error('no object %r in %s' % (args.ground, args.blend))
            ground = bpy.data.objects[args.ground]
        made = on_ground(args.ground_at, size=args.size, kind=args.kind or 'mud', turn=args.turn, ground=ground,
                         strength=0.7 if args.strength is None else args.strength, seed=args.seed)
    else:
        parser.error('give --wall NAME (with --from and --up) or --ground-at X Y Z')
    print('made', made.name)
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing saved; give --out FILE.blend to keep it')


if __name__ == '__main__':
    main()
