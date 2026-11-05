"""
What this file does: raises wooded mountain ridges far behind a place, for a backdrop: several layers one behind the
other, each a long ridge with its own peaks and saddles and a skyline broken by the tops of trees, the nearer layers
dark and green, each farther one paler and bluer as the air between swallows it, with mist lying low in the valleys
at the foot of every ridge so the layers stand apart. The haze is in the hills' own material (they stand far outside
any haze box over the place). Nothing here chooses where the hills stand: the place's middle, the way they lie from it
and how far are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import far_hills
    made = far_hills.lay(centre=(0, 0), facing=0, distance=(120, 450), layers=4, height=(60, 220), seed=2)
    made['hills']                    # one object per layer: 'far hills 1' (nearest) ...
    camera.data.clip_end = 1000      # Blender's camera stops drawing at 100 m by default: the hills vanish

From the command line:

    python3 far_hills.py --help
    python3 far_hills.py --distance 120 450 --layers 4 --out hills.blend

Options, with their defaults:
    centre        (0, 0)          the place's middle (x, y): the hills are measured from it
    facing        0               the way from the place to the hills, degrees counter-clockwise from +Y (0: behind a
                                  place whose front faces -Y, as the store's parts do; 90 towards -X)
    distance      (120, 450)      metres from the place to the nearest ridge and to the farthest
    layers        4               how many ridges, one behind the other
    height        (60, 220)       the highest peaks of the nearest ridge and of the farthest, metres above `base`
    width         none            how far each ridge reaches across, metres (none: 1.8 times its distance)
    haze          400 m           how thick the air: the distance at which a hill has lost half its own colour
    haze_colour   (0.11, 0.14, 0.18)   the air's colour, linear RGB (a dusk grey-blue; warmer for a sunset behind)
    haze_strength 0.7             how bright the air glows (the sky's light it scatters)
    mist          0.6             the mist lying in the valleys at each ridge's foot, 0 none to 1 thick
    trees         1.0             how wooded: the skyline broken by tree tops and the slopes mottled with crowns, 0 bare
    base          0.0             the height of the place's ground; the ridges' feet go 15 m below it
    seed          0               the same seed raises the same hills
    collection    none            where the objects go (a new collection 'far_hills')

What it makes: 'far hills 1' to 'far hills N' (nearest first), each with obj['distance'] and its points' 'hill_haze'
(0 its own colour to 1 all air) and 'hill_height' (0 at its foot to 1 at its top), read by the material made here,
'MADE • far hills' (one copy for all).
"""

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

MATERIAL = 'MADE • far hills'

TOOL = {
    'name': 'far_hills',
    'what': 'wooded mountain ridges far behind a place, for a backdrop: layers one behind the other, each skyline broken by '
            'tree tops, fading paler and bluer into haze with distance, mist low in the valleys between them',
    'call': "far_hills.lay(centre=(0, 0), facing=0, distance=(120, 450), layers=4, height=(60, 220), seed=2)",
    'options': {
        'centre': "the place's middle (x, y) ((0, 0))",
        'facing': 'the way from the place to the hills, degrees counter-clockwise from +Y; 0 behind a place facing -Y (0)',
        'distance': 'metres to the nearest ridge and to the farthest ((120, 450))',
        'layers': 'how many ridges, one behind the other (4)',
        'height': 'the highest peaks of the nearest and of the farthest ridge, metres ((60, 220))',
        'width': 'how far each ridge reaches across, metres (none: 1.8 times its distance)',
        'haze, haze_colour, haze_strength': 'the distance at which a hill has lost half its colour (400 m); the air\'s '
                                            'colour ((0.11, 0.14, 0.18), a dusk grey-blue); how bright it glows (0.7)',
        'mist': "the mist in the valleys at each ridge's foot, 0 to 1 (0.6)",
        'trees': 'how wooded: tree tops on the skyline, crowns on the slopes; 0 bare (1.0)',
        'base': "the place's ground height; the ridges' feet go 15 m below it (0.0)",
        'seed': 'the same seed raises the same hills (0)',
        'collection': "where the objects go (a new collection 'far_hills')",
    },
    'materials': [MATERIAL + ' (made in code)'],
    'source': "the mountains in the garden builders' '57 garden' scripts ('/home/claude/build-57-garden/second pass/"
              "render_final.py', lines 1672-1686, with add_air() at line 298), made into a tool: ridges in layers that "
              'stand apart by valley mist, skylines broken by tree tops, and the haze in the hills\' own material by '
              'distance instead of read from the camera',
    'trap': "a camera draws nothing beyond its far limit, 100 m by Blender's default: set camera.data.clip_end to at "
            'least 1.5 times the farthest distance (1000 for the default hills) or the hills vanish; a haze box over the '
            'place does not reach them (their haze is their own): judge them against your sky in a drawn picture',
}


def material(haze_colour=(0.11, 0.14, 0.18), haze_strength=0.7):
    """The hills' material: dark wooded green mottled with tree crowns, mixed into glowing air by each point's
    'hill_haze'. Made once for a colour and strength, then shared."""
    name = MATERIAL if (tuple(haze_colour), float(haze_strength)) == ((0.11, 0.14, 0.18), 0.7) else '%s • %.3f %.3f %.3f x%.2f' % (
        MATERIAL, haze_colour[0], haze_colour[1], haze_colour[2], haze_strength)
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    principled = nodes['Principled BSDF']
    output = nodes['Material Output']
    coords = nodes.new('ShaderNodeTexCoord')
    crowns = nodes.new('ShaderNodeTexVoronoi')              # tree crowns: soft cells a few metres across
    crowns.inputs['Scale'].default_value = 0.12
    links.new(coords.outputs['Object'], crowns.inputs['Vector'])
    patches = nodes.new('ShaderNodeTexNoise')               # stands of darker conifer and paler broadleaf
    patches.inputs['Scale'].default_value = 0.015
    patches.inputs['Detail'].default_value = 3.0
    links.new(coords.outputs['Object'], patches.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.3, (0.008, 0.016, 0.012, 1.0)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.7, (0.03, 0.045, 0.026, 1.0)
    links.new(patches.outputs['Fac'], ramp.inputs['Fac'])
    shade = nodes.new('ShaderNodeMapRange')
    shade.inputs['To Min'].default_value = 0.55
    shade.inputs['To Max'].default_value = 1.1
    links.new(crowns.outputs['Distance'], shade.inputs['Value'])
    mottled = nodes.new('ShaderNodeVectorMath')
    mottled.operation = 'SCALE'
    links.new(ramp.outputs['Color'], mottled.inputs[0])
    links.new(shade.outputs['Result'], mottled.inputs['Scale'])
    links.new(mottled.outputs['Vector'], principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.9
    principled.inputs['Specular IOR Level'].default_value = 0.1
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 1.5
    links.new(crowns.outputs['Distance'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    haze = nodes.new('ShaderNodeAttribute')
    haze.attribute_name = 'hill_haze'
    air = nodes.new('ShaderNodeEmission')
    air.inputs['Color'].default_value = (*haze_colour, 1.0)
    air.inputs['Strength'].default_value = float(haze_strength)
    mix = nodes.new('ShaderNodeMixShader')
    links.new(haze.outputs['Fac'], mix.inputs[0])
    links.new(principled.outputs[0], mix.inputs[1])
    links.new(air.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])
    return mat


def lay(centre=(0.0, 0.0), facing=0.0, distance=(120.0, 450.0), layers=4, height=(60.0, 220.0), width=None, haze=400.0,
        haze_colour=(0.11, 0.14, 0.18), haze_strength=0.7, mist=0.6, trees=1.0, base=0.0, seed=0, collection=None):
    """Raise the ridges (see the note at the top). Returns {'hills': [obj, ...]} (nearest first)."""
    near, far = (float(v) for v in distance)
    low, high = (float(v) for v in height)
    layers = int(layers)
    if not 0 < near <= far:
        raise ValueError('distance is (nearest, farthest) with 0 < nearest <= farthest, not %r' % (distance,))
    if not 1 <= layers <= 12:
        raise ValueError('layers is 1 to 12, not %r' % (layers,))
    if not 0.0 <= mist <= 1.0 or not 0.0 <= trees <= 2.0:
        raise ValueError('mist is 0 to 1 and trees 0 to 2, not %r and %r' % (mist, trees))
    if haze <= 0:
        raise ValueError('haze is a distance in metres above 0, not %r' % (haze,))
    a = math.radians(facing)
    away = Vector((-math.sin(a), math.cos(a), 0.0))          # from the place towards the hills
    across = Vector((away.y, -away.x, 0.0))                  # to the right, looking at them
    middle = Vector((centre[0], centre[1], float(base)))
    target = collection
    if target is None:
        target = bpy.data.collections.new('far_hills')
        bpy.context.scene.collection.children.link(target)
    mat = material(haze_colour, haze_strength)
    made = []
    for layer in range(layers):
        share = layer / max(layers - 1, 1)
        d = near + (far - near) * share ** 1.15
        peak = low + (high - low) * share
        reach = float(width) if width is not None else 1.8 * d
        depth = max(0.35 * d / max(layers, 1), peak * 2.2)    # each ridge's own breadth front to back
        columns = max(60, min(320, int(reach / max(d * 0.012, 1.0))))
        rows = 16
        own = 1.0 - math.exp(-d / haze * math.log(2.0))        # half its colour gone at `haze` metres
        offset = Vector((seed * 17.3 + layer * 41.7, seed * 3.1 - layer * 13.9, layer * 7.7))
        verts, haze_values, heights, faces = [], [], [], []
        for j in range(rows + 1):
            v = j / rows
            for i in range(columns + 1):
                u = i / columns
                x = (u - 0.5) * reach
                q = Vector((x / max(peak * 9.0, 1.0), 0.0, 0.0)) + offset
                ridge = 0.6 + 0.42 * noise.noise(q) + 0.22 * noise.noise(q * 2.7 + Vector((5.0, 0, 0))) + 0.08 * noise.noise(q * 7.0)
                ridge = max(ridge, 0.12)
                profile = math.sin(math.pi * min(max(v, 0.0), 1.0)) ** 0.85
                treetop = trees * peak * 0.035 * (0.5 + noise.noise(Vector((x * 0.11, v * 3.0, layer + 3.0)) + offset)) * profile
                z = peak * ridge * profile + treetop
                edge = min(u, 1.0 - u)                       # the ends fall away so no ridge stops in the air
                if edge < 0.08:
                    z *= (edge / 0.08) ** 0.6
                point = middle + away * (d + depth * (v - 0.35)) + across * x + Vector((0.0, 0.0, z - 15.0 * (1.0 - profile)))
                verts.append(tuple(point))
                foot = max(0.0, min(1.0, z / max(peak * ridge * 0.95, 1e-6)))     # 1 at this ridge's own crest
                low_mist = mist * (1.0 - foot) ** 1.3
                haze_values.append(1.0 - (1.0 - own) * (1.0 - 0.85 * low_mist))
                heights.append(foot)
        row = columns + 1
        for j in range(rows):
            for i in range(columns):
                a0, b0 = j * row + i, (j + 1) * row + i
                faces.append((a0, a0 + 1, b0 + 1, b0))
        mesh = bpy.data.meshes.new('far hills %d' % (layer + 1))
        origin = Vector(verts[0])
        mesh.from_pydata([tuple(Vector(p) - origin) for p in verts], [], faces)
        for column, values in (('hill_haze', haze_values), ('hill_height', heights)):
            attribute = mesh.attributes.new(column, 'FLOAT', 'POINT')
            attribute.data.foreach_set('value', values)
        for polygon in mesh.polygons:
            if polygon.normal.dot(-away) < 0 and polygon.normal.z < 0:
                polygon.flip()
        mesh.update()
        mesh.shade_smooth()
        obj = bpy.data.objects.new('far hills %d' % (layer + 1), mesh)
        obj.location = origin
        obj.visible_shadow = False
        target.objects.link(obj)
        obj.data.materials.append(mat)
        obj['distance'] = d
        store.mark(obj)
        made.append(obj)
    return {'hills': made}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of far_hills.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--centre', type=float, nargs=2, default=(0.0, 0.0), metavar=('X', 'Y'), help="the place's middle; default 0 0")
    parser.add_argument('--facing', type=float, default=0.0, help='degrees from +Y, counter-clockwise; default 0')
    parser.add_argument('--distance', type=float, nargs=2, default=(120.0, 450.0), metavar=('NEAR', 'FAR'), help='default 120 450')
    parser.add_argument('--layers', type=int, default=4, help='how many ridges; default 4')
    parser.add_argument('--height', type=float, nargs=2, default=(60.0, 220.0), metavar=('NEAR', 'FAR'), help='default 60 220')
    parser.add_argument('--haze', type=float, default=400.0, help='metres at which a hill has lost half its colour; default 400')
    parser.add_argument('--mist', type=float, default=0.6, help='valley mist, 0 to 1; default 0.6')
    parser.add_argument('--trees', type=float, default=1.0, help='how wooded, 0 bare; default 1')
    parser.add_argument('--base', type=float, default=0.0, help="the place's ground height; default 0")
    parser.add_argument('--seed', type=int, default=0, help='the same seed raises the same hills; default 0')
    parser.add_argument('--out', help='save the result here (.blend)')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    made = lay(centre=args.centre, facing=args.facing, distance=args.distance, layers=args.layers, height=args.height,
               haze=args.haze, mist=args.mist, trees=args.trees, base=args.base, seed=args.seed)
    print('raised %d ridges, %s' % (len(made['hills']), ', '.join('%.0f m' % o['distance'] for o in made['hills'])))
    print("remember: camera.data.clip_end = 1000 (Blender's default 100 m hides them)")
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
