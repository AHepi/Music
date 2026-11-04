"""
What this file does: a ribbon of smoke rising from a point you give (a chimney's top, a stove pipe, a fire), drifting
with the wind, widening as it rises, turned to face the point you say the viewer stands at. Smoke drawn as a flat
ribbon facing the viewer reads as soft wisps where a volume box often reads as balloons. It decides nothing about where
smoke goes: the start, the wind and the viewer are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import smoke_ribbon
    smoke = smoke_ribbon.make(start=(-24, 84, 24.6), facing=camera.location, drift=(1.0, 0.1), rise=34, seed=2)

Options, with their defaults:
    start         where the smoke leaves the chimney (x, y, z), metres (required)
    facing        where the viewer stands (x, y, z): the ribbon turns to face it (required; give your camera's place)
    drift         the wind's way along the ground (x, y); its length does not matter; (0, 0) means along +X (1, 0)
    rise          how high the ribbon climbs, metres (12)
    lean          how far it leans with the wind for each metre it rises (0.5)
    width_start   its width at the chimney, metres (0.8)
    width_end     its width at the top, metres (6)
    sway          how much it wanders from side to side, metres (1.5)
    seed          the same seed, the same wander (0)
    collection    where to put it (default: a new collection 'smoke')

It returns the object 'smoke ribbon', with the material 'MADE • smoke ribbon' (it reads the ribbon's UV map). It casts no
shadow. Smoke shows best where light passes through it towards the viewer: against a paler sky low down, or over a
lamp; against a dark sky it is faint.

From the command line:

    python3 smoke_ribbon.py --help
    python3 smoke_ribbon.py --start 0 30 8 --facing 0 -5 1.6 --rise 15 --out smoke.blend
"""

import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

TOOL = {
    'name': 'smoke_ribbon',
    'what': 'a ribbon of smoke rising from a point you give, drifting with the wind, widening, turned to face the viewer\'s place you give',
    'call': 'smoke_ribbon.make(start=(-24, 84, 24.6), facing=(0.9, -0.5, 1.7), drift=(1.0, 0.1), rise=34, seed=2)',
    'options': {
        'start': 'where the smoke leaves the chimney (x, y, z) (required)',
        'facing': 'where the viewer stands (x, y, z); the ribbon turns to face it (required)',
        'drift': 'the wind\'s way along the ground (x, y) (1, 0)',
        'rise': 'how high it climbs, metres (12)', 'lean': 'lean with the wind per metre of rise (0.5)',
        'width_start': 'width at the chimney, metres (0.8)', 'width_end': 'width at the top, metres (6)',
        'sway': 'side-to-side wander, metres (1.5)', 'seed': 'the same seed, the same wander (0)',
    },
    'materials': ['MADE • smoke ribbon'],
    'source': 'the desert mine builder (log 46) and the goods yard builder (log 51), made into a tool',
    'trap': 'against a dark upper sky smoke is faint at best; it shows against the paler sky low down or over a lamp',
}


def make(start, facing, drift=(1.0, 0.0), rise=12.0, lean=0.5, width_start=0.8, width_end=6.0, sway=1.5, seed=0,
         collection=None, steps=40, material='MADE • smoke ribbon'):
    """Make the ribbon; returns the object 'smoke ribbon'."""
    rng = random.Random(seed)
    start, facing = Vector(start), Vector(facing)
    wind = Vector((drift[0], drift[1], 0.0))
    wind = wind.normalized() if wind.length > 1e-6 else Vector((1.0, 0.0, 0.0))
    phase = rng.uniform(0.0, math.tau)
    spine = []
    for step in range(steps + 1):
        t = step / steps
        height = rise * t ** 0.85
        across = wind.cross(Vector((0.0, 0.0, 1.0)))
        wander = across * (sway * math.sin(t * 5.0 + phase) * t) + wind * (lean * height + 0.6 * sway * t * t)
        spine.append(start + Vector((0.0, 0.0, height)) + wander)
    vertices, uvs = [], []
    for step, point in enumerate(spine):
        t = step / steps
        ahead = (spine[min(step + 1, steps)] - spine[max(step - 1, 0)]).normalized()
        to_viewer = (facing - point).normalized()
        side = ahead.cross(to_viewer)
        side = side.normalized() if side.length > 1e-6 else Vector((1.0, 0.0, 0.0))
        half = (width_start + (width_end - width_start) * t ** 0.8) / 2
        vertices += [point - side * half, point + side * half]
        uvs += [(0.0, t), (1.0, t)]
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(steps)]
    mesh = bpy.data.meshes.new('smoke ribbon')
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    layer = mesh.uv_layers.new(name='UVMap')
    layer.data.foreach_set('uv', [c for face in faces for corner in face for c in uvs[corner]])
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new('smoke ribbon', mesh)
    obj.visible_shadow = False
    if collection is None:
        collection = bpy.data.collections.new('smoke')
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)
    store.use_material(obj, material)
    return obj


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='A ribbon of smoke facing the viewer (see the note at the top of smoke_ribbon.py).')
    parser.add_argument('--blend', help='open this .blend file first (otherwise a new empty one)')
    parser.add_argument('--out', help='save the result here')
    parser.add_argument('--start', type=float, nargs=3, required=True, help='where the smoke leaves the chimney: x y z')
    parser.add_argument('--facing', type=float, nargs=3, required=True, help='where the viewer stands: x y z')
    parser.add_argument('--drift', type=float, nargs=2, default=(1.0, 0.0), help='the wind\'s way along the ground: x y; default 1 0')
    parser.add_argument('--rise', type=float, default=12.0, help='how high it climbs, metres; default 12')
    parser.add_argument('--width-end', type=float, default=6.0, help='its width at the top, metres; default 6')
    parser.add_argument('--seed', type=int, default=0, help='the same seed, the same wander; default 0')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    make(args.start, args.facing, drift=args.drift, rise=args.rise, width_end=args.width_end, seed=args.seed)
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
