"""
What this file does: hangs a cast-iron downpipe on a wall face you name, the way the town street's builders did: a
round pipe standing a little off the wall from a top point you give straight down to the ground, made of lengths with
a socket (a collar) at the top of each and an iron holdfast under each socket fixing it to the wall, a hopper head at
the top (the open iron box the gutter's water falls into), a swan neck from the gutter's outlet to the hopper when you
give that outlet, and a shoe at the foot that throws the water out onto the ground. With `leaks` it lays the stains
water leaves on the wall: a wet stripe behind the pipe, a green-black run under each socket, a rust run under each
holdfast and under the hopper's lip; with `splash` a damp splash on the ground at the shoe. Nothing here chooses where
a pipe goes.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import downpipe
    made = downpipe.lay(wall, 'front', along=0.3, top=8.2, leaks=True, splash=True, seed=3)
    made['pipe'], made['stains']                         # the iron (one object) and the stain planes (a list)
    # under a gutter from lay_eaves: its outlet is a point the eaves give back; the pipe takes its place and height
    # from it (along: the outlet's place on the face; top: 0.4 m under the outlet)
    eaves = lay_eaves.lay(wall, ridge='front', outlets={'front': [0.3]})
    downpipe.lay(wall, 'front', outlet=eaves['outlets'][0], leaks=True)

`wall` is a box-like object; `side` names its face in its own axes as the stone and stain tools do: 'front' (-Y),
'back' (+Y), 'left' (-X), 'right' (+X). `along` is metres along that side from its left end as you see it standing
outside facing it; `top` is metres up from the wall's foot to the top of the hopper head (the pipe's top without one).
Given an `outlet`, either may be left out: `along` is then the outlet's place on the face and `top` 0.4 m under it.

From the command line:

    python3 downpipe.py --help
    python3 downpipe.py --blend IN.blend --wall House --side front --along 0.3 --top 8.2 --leaks --splash --out OUT.blend

Options, with their defaults:
    ground       none       where the pipe stops: none, the wall's foot; a number, the ground's height (world z); a mesh
                            object, its height straight under the shoe
    face         auto       metres the wall's face stands in front of the box: on a lay_stone wall its blocks (the relief
                            it wrote, 'stone_front', plus 0.04 m: 0.24 m), else 0; give it for other relief (lay_rubble's
                            stones: 0.085)
    out          auto       metres from the box's face to the pipe's middle: face + 0.085 (0.325 m on lay_stone's wall)
    radius       0.05 m     the pipe's radius (a 4 inch pipe; 0.038 is a 3 inch)
    hopper       True       a hopper head at the top
    outlet       none       a point (x, y, z): the gutter's outlet; a swan neck runs from it down into the hopper
    lengths      1.83 m     the pipe's lengths (6 ft): a socket and a holdfast at the top of each, counted up from the shoe
    leaks        False      the wet stripe, the leak runs under the sockets, the rust runs under the holdfasts and hopper
    splash       False      a damp splash on the ground in front of the shoe
    seed         0          the leak runs' lengths, the splash's outline, a little play in the sockets' heights
    collection   none       where the objects go (a new collection 'downpipe')
    iron_material           'IRON • soot-black lamp posts'

The pipe object carries its counts: obj['sockets'], obj['holdfasts'], and obj['top'] and obj['foot'] (world heights).
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import stain  # noqa: E402

IRON_MATERIAL = 'IRON • soot-black lamp posts'
UP = Vector((0.0, 0.0, 1.0))
GAP = 0.035          # between the pipe and the wall's face, where the holdfasts are

TOOL = {
    'name': 'downpipe',
    'what': 'a cast-iron downpipe down a wall face you name, from a top point to the ground: lengths with sockets and holdfasts, a hopper head at the top, a swan neck from a gutter outlet you give, a shoe at the foot; leak and rust stains behind it and a splash at the shoe if you ask',
    'call': "downpipe.lay(wall, 'front', along=0.3, top=8.2, leaks=True, splash=True, seed=3)",
    'options': {
        'wall, side, along, top': "the box-like object and its face ('front' -Y, 'back' +Y, 'left' -X, 'right' +X); metres along the side from its left end seen from outside; metres up from the wall's foot to the top of the hopper (with an outlet, either may be left out: the outlet's place, 0.4 m under it)",
        'ground': 'where the pipe stops: none the wall\'s foot, a number the ground\'s height (world z), a mesh object its height under the shoe',
        'face': "metres the wall's face stands in front of the box (default: lay_stone's blocks, 0.24 m, from the 'stone_front' it writes; else 0)",
        'out': "metres from the box's face to the pipe's middle (default face + 0.085)",
        'radius': "the pipe's radius (0.05 m, a 4 inch pipe)",
        'hopper': 'a hopper head at the top (True)',
        'outlet': "a point (x, y, z), the gutter's outlet (lay_eaves gives them back): a swan neck from it into the hopper (none)",
        'lengths': "metres between sockets, counted up from the shoe (1.83, 6 ft)",
        'leaks': 'a wet stripe behind the pipe, leak runs under the sockets, rust runs under the holdfasts and the hopper (False)',
        'splash': 'a damp splash on the ground in front of the shoe (False)',
        'seed': "the leak runs' lengths, the splash, a little play in the sockets (0)",
        'collection': "where the objects go (a new collection 'downpipe')",
        'iron_material': "default '%s'" % IRON_MATERIAL,
    },
    'materials': [IRON_MATERIAL, 'MADE • stain leak', 'MADE • stain rust', 'MADE • stain damp'],
    'source': "the downpipe in building() and the hopper heads in '/home/claude/build-55-street/fronts/render_final.py' (lines 432-442 and 1542-1551), the stains behind it from wall_stain() (lines 1530-1539), made into a tool: the hopper's back now meets the wall's face instead of sinking into the stone, the swan neck runs from a gutter outlet you give, and the leaks follow the sockets the pipe really has",
    'trap': "lay_stone's bands (plinth and cornice) stand 0.37 m out, past the pipe: the pipe runs through them; start the pipe below a cornice or give a larger `out`",
}


class Iron:
    """Cylinders and boxes gathered into one mesh, in the world."""

    def __init__(self):
        self.bm = bmesh.new()

    def tube(self, p0, p1, radius, segments=12, radius_end=None):
        p0, p1 = Vector(p0), Vector(p1)
        length = (p1 - p0).length
        if length < 1e-5:
            return
        turn = (p1 - p0).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segments, radius1=radius,
                              radius2=radius if radius_end is None else radius_end, depth=length,
                              matrix=Matrix.Translation((p0 + p1) / 2) @ turn)

    def box(self, centre, size, frame):
        """A box of `size` (along, out, up) centred at `centre`, turned to the wall's frame (a 3x3 matrix)."""
        matrix = Matrix.Translation(centre) @ frame.to_4x4() @ Matrix.Diagonal((*[max(s, 1e-4) for s in size], 1.0))
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=matrix)

    def hopper(self, centre, bottom, top, height, frame):
        """A box wider at its top than its foot: (along, out) at the bottom and the top, centred at `centre`."""
        made = bmesh.ops.create_cube(self.bm, size=1.0)['verts']
        for v in made:
            wide = top if v.co.z > 0 else bottom
            v.co = Vector((v.co.x * 2 * wide[0] / 2, v.co.y * 2 * wide[1] / 2, v.co.z * height))
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(centre) @ frame.to_4x4(), verts=made)

    def make(self, name, material, collection, ground):
        mesh = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(mesh)
        self.bm.free()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        store.use_material(obj, material, ground=ground)
        return obj


def wall_face(wall, face):
    """How far the wall's face stands in front of the box: `face` if given, else lay_stone's blocks, else 0."""
    if face is not None:
        face = float(face)
        if not 0.0 <= face <= 1.5:
            raise ValueError('face is 0 to 1.5 m, not %r' % (face,))
        return face
    relief = wall.get('stone_front')
    return float(relief) + stain.PAST_THE_RELIEF if relief is not None else 0.0


def _ground_height(ground, point, fallback):
    if ground is None:
        return fallback
    if isinstance(ground, (int, float)):
        return float(ground)
    if getattr(ground, 'type', None) != 'MESH':
        raise ValueError('ground is none, a height (world z) or a mesh object, not %r' % (ground,))
    bpy.context.view_layer.update()
    corners = [ground.matrix_world @ Vector(c) for c in ground.bound_box]
    to_local = ground.matrix_world.inverted()
    start = to_local @ Vector((point.x, point.y, max(c.z for c in corners) + 1.0))
    down = (to_local.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    hit, location, _, _ = ground.ray_cast(start, down, distance=1.0e5)
    if not hit:
        raise ValueError('the ground %r is not under the shoe at (%.2f, %.2f)' % (ground.name, point.x, point.y))
    return (ground.matrix_world @ location).z


def lay(wall, side, along=None, top=None, ground=None, face=None, out=None, radius=0.05, hopper=True, outlet=None, lengths=1.83,
        leaks=False, splash=False, seed=0, collection=None, iron_material=IRON_MATERIAL):
    """Hang the downpipe on the wall's side (see the note at the top). Returns {'pipe': object, 'stains': [objects]}."""
    if wall is None or wall.type != 'MESH':
        raise ValueError('downpipe needs a mesh object (the wall)')
    bpy.context.view_layer.update()
    sides = stain.wall_side(wall, side)                     # refuses a side that is not front, back, left or right
    face = wall_face(wall, face)
    if (along is None or top is None) and outlet is None:
        raise ValueError('give along and top (or an outlet, which gives both)')
    if along is None:
        along = (Vector(outlet) - sides['origin']).dot(sides['along'])
    if top is None:
        top = Vector(outlet).z - sides['origin'].z - 0.40
    radius, lengths, along, top = float(radius), float(lengths), float(along), float(top)
    if not 0.015 <= radius <= 0.15:
        raise ValueError('radius is 0.015 to 0.15 m, not %r' % (radius,))
    if not 0.5 <= lengths <= 4.0:
        raise ValueError('lengths is 0.5 to 4 m, not %r' % (lengths,))
    if not 0.0 <= along <= sides['length']:
        raise ValueError('along is 0 to %.2f m (the side\'s length), not %r' % (sides['length'], along))
    out = face + radius + GAP if out is None else float(out)
    if out < face + radius:
        raise ValueError('out %.3f m puts the pipe into the wall (its face stands %.3f m out, the pipe is %.3f m thick)' % (out, face, radius * 2))
    rng = random.Random(seed)
    origin, run, normal = sides['origin'], sides['along'], sides['normal']
    frame = Matrix((run, normal, UP)).transposed()          # the wall's frame: along, out, up

    def at(d, z_world):
        p = origin + run * along + normal * d
        return Vector((p.x, p.y, z_world))

    foot_z = origin.z
    shoe_reach = 0.16 + radius
    mouth = at(out + shoe_reach, foot_z)
    ground_z = _ground_height(ground, mouth, foot_z)
    top_z = foot_z + top
    hopper_h = 0.30 if hopper else 0.0
    pipe_top = top_z - hopper_h + 0.02
    if pipe_top - ground_z < 1.0:
        raise ValueError('top is %.2f m above the ground: a downpipe needs at least 1 m below its hopper' % (top_z - ground_z))
    iron = Iron()
    shoe_top = ground_z + 0.32
    # the pipe, straight down the wall from under the hopper to the shoe
    iron.tube(at(out, shoe_top), at(out, pipe_top), radius)
    # the shoe: a short bend at the foot, kicking the water out from the wall, its mouth a little wider
    iron.tube(at(out, shoe_top + 0.01), at(out + shoe_reach * 0.55, ground_z + 0.15), radius * 1.02)
    iron.tube(at(out + shoe_reach * 0.5, ground_z + 0.16), at(out + shoe_reach, ground_z + 0.05), radius * 1.05, radius_end=radius * 1.25)
    # sockets at the top of each length, counted up from the shoe; a holdfast under each, fixing it to the wall
    sockets, z = 0, shoe_top + lengths + rng.uniform(-0.04, 0.04)
    socket_heights = []
    while z < pipe_top - 0.25:
        iron.tube(at(out, z), at(out, z + 0.075), radius + 0.016)
        iron.tube(at(out, z - 0.07), at(out, z - 0.035), radius + 0.006)                         # the holdfast's band
        iron.box(at(face + (out - face) / 2, z - 0.0525), (0.035, out - face, 0.03), frame)  # its arm to the wall
        iron.box(at(face + 0.006, z - 0.0525), (0.13, 0.012, 0.05), frame)                       # its plate on the wall
        socket_heights.append(z)
        sockets += 1
        z += lengths + rng.uniform(-0.02, 0.02)
    # a holdfast just under the hopper too (a short top length carries one)
    iron.tube(at(out, pipe_top - 0.20), at(out, pipe_top - 0.165), radius + 0.006)
    iron.box(at(face + (out - face) / 2, pipe_top - 0.1825), (0.035, out - face, 0.03), frame)
    holdfasts = sockets + 1
    hopper_centre = None
    if hopper:
        depth = 0.26
        hopper_centre = at(face + 0.01 + depth / 2, top_z - hopper_h / 2 - 0.03)
        iron.hopper(hopper_centre, (0.24, depth - 0.07), (0.34, depth), hopper_h - 0.05, frame)
        iron.box(at(face + 0.01 + (depth + 0.05) / 2, top_z - 0.025), (0.40, depth + 0.05, 0.05), frame)   # its lip, proud at the front
        iron.box(at(face + 0.006, top_z - hopper_h / 2), (0.44, 0.012, 0.06), frame)                     # its ears on the wall
    if outlet is not None:
        # the swan neck: down from the gutter's outlet, back towards the wall, down into the hopper (or the pipe)
        outlet = Vector(outlet)
        into = (hopper_centre if hopper else at(out, pipe_top))
        entry = Vector((into.x, into.y, top_z + 0.10))
        if outlet.z < entry.z + 0.1:
            raise ValueError('the outlet (z %.2f) must be above the top of the hopper (z %.2f)' % (outlet.z, top_z))
        bend = outlet - Vector((0.0, 0.0, 0.07))
        iron.tube(outlet + Vector((0.0, 0.0, 0.01)), bend, radius * 0.85)
        iron.tube(bend, entry, radius * 0.85)
        iron.tube(entry, Vector((entry.x, entry.y, top_z - (0.05 if hopper else 0.0))), radius * 0.85)
    if collection is None:
        collection = bpy.data.collections.new('downpipe')
        bpy.context.scene.collection.children.link(collection)
    pipe = iron.make('downpipe', store.material(iron_material) if isinstance(iron_material, str) else iron_material, collection, ground_z)
    pipe['sockets'] = sockets
    pipe['holdfasts'] = holdfasts
    pipe['top'] = top_z
    pipe['foot'] = ground_z
    made = {'pipe': pipe, 'stains': []}
    if leaks:
        set_out = face + 0.004
        wall_z0 = foot_z
        def up(z_world):
            return z_world - wall_z0
        stains = made['stains']
        stains.append(stain.on_wall(wall, side, max(0.0, along - 0.28), min(sides['length'], along + 0.30), max(0.0, up(ground_z)),
                                    up(pipe_top), kind='leak', strong_at='bottom', strength=0.75, seed=seed * 31 + 1,
                                    offset=set_out, collection=collection))
        for k, z in enumerate(socket_heights):
            reach = rng.uniform(0.9, 1.5)
            stains.append(stain.on_wall(wall, side, max(0.0, along - 0.2), min(sides['length'], along + 0.24), max(0.0, up(z) - reach), up(z),
                                        kind='leak', strength=1.25, seed=seed * 31 + 10 + k, offset=set_out + 0.002,
                                        collection=collection, taper=0.45))
            stains.append(stain.on_wall(wall, side, max(0.0, along - 0.06), min(sides['length'], along + 0.07), max(0.0, up(z) - 0.8),
                                        up(z) - 0.05, kind='rust', strength=1.0, seed=seed * 31 + 50 + k, offset=set_out + 0.004,
                                        collection=collection))
        if hopper:
            stains.append(stain.on_wall(wall, side, max(0.0, along - 0.18), min(sides['length'], along + 0.2), up(top_z) - 1.1,
                                        up(top_z) - 0.25, kind='rust', strength=1.0, seed=seed * 31 + 90,
                                        offset=set_out + 0.004, collection=collection))
    if splash:
        spot = at(out + shoe_reach + 0.22, ground_z)
        turn = math.degrees(math.atan2(normal.y, normal.x))
        made['stains'].append(stain.on_ground((spot.x, spot.y, ground_z), size=(0.38, 0.26), kind='damp', turn=turn,
                                              ground=ground if getattr(ground, 'type', None) == 'MESH' else None,
                                              strength=0.45, seed=seed * 31 + 99, collection=collection))
    return made


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of downpipe.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--wall', help='the box-like wall object')
    parser.add_argument('--side', default='front', help='its face: front, back, left or right; default front')
    parser.add_argument('--along', type=float, help="metres along the side from its left end")
    parser.add_argument('--top', type=float, help="metres up from the wall's foot to the top of the hopper")
    parser.add_argument('--ground', help='a ground mesh object the shoe stands on (default: the wall\'s foot)')
    parser.add_argument('--face', type=float, default=None, help="metres the wall's face stands in front of the box (default: from lay_stone, else 0)")
    parser.add_argument('--radius', type=float, default=0.05, help="the pipe's radius; default 0.05")
    parser.add_argument('--no-hopper', action='store_true', help='no hopper head')
    parser.add_argument('--leaks', action='store_true', help='leak and rust stains behind the pipe')
    parser.add_argument('--splash', action='store_true', help='a damp splash at the shoe')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not (args.blend and args.wall and args.along is not None and args.top is not None and args.out):
        parser.error('--blend, --wall, --along, --top and --out are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    wall = bpy.data.objects.get(args.wall)
    if wall is None:
        parser.error('no object %r in %s' % (args.wall, args.blend))
    ground = None
    if args.ground:
        ground = bpy.data.objects.get(args.ground)
        if ground is None:
            parser.error('no object %r in %s' % (args.ground, args.blend))
    made = lay(wall, args.side, args.along, args.top, ground=ground, face=args.face, radius=args.radius,
               hopper=not args.no_hopper, leaks=args.leaks, splash=args.splash, seed=args.seed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('downpipe: %d sockets, %d stains, saved %s' % (made['pipe']['sockets'], len(made['stains']), args.out))


if __name__ == '__main__':
    main()
