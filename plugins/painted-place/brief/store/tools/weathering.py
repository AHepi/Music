"""
What this file does: makes weathered copies of materials you give, the way the town street's third builder aged its
fronts: `stone` darkens a stone with rain streaks running down it and soot blotches, both broad enough (streaks about
25 cm across, blotches about 2 m) to show on a front seen edge-on from down the street, and can make its tops a little
glossy with rain; `peel` flakes a painted material's paint off in big patches down to grey timber, worst near the
ground (the bottom rails of doors and shop fronts), each flake's edge a little raised. The copy is returned and your
material is left as it was, so only the things you give the copy are weathered. Nothing here chooses what is weathered:
you choose the objects that get the copies.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import weathering, lay_stone
    shades = [weathering.stone(name, seed=k) for k, name in enumerate(lay_stone.SHADES)]
    dressings = weathering.stone(lay_stone.TRIM_MATERIAL, dark=0.45, overall=0.88, wet=0.8)    # lighter, glossy tops
    lay_stone.lay(front, openings=[...], shades=shades, trim_material=dressings,
                  wood_material=weathering.peel(lay_stone.WOOD_MATERIAL, amount=0.5))
    store.use_material(my_door, weathering.peel('WOOD • peeling dark painted doors'))

From the command line:

    python3 weathering.py --help
    python3 weathering.py --blend IN.blend --stone "Hand-painted sandstone • shade 00" --peel "WOOD • peeling dark painted doors" --out OUT.blend

stone(material, ...), with its defaults:
    dark            0.62      how much the streaks and blotches darken the stone: 0 none, 0.9 nearly black
    overall         1.0       the whole stone's brightness, as a share (0.88 keeps dressings a little darker overall)
    streak_width    0.25 m    how broad the rain streaks are
    streak_length   3.0 m     how long they run down
    blotch          1.8 m     how big the soot blotches are
    wet             0.0       how glossy the copy is from rain: 0 as it was, 1 its roughness halved
    seed            0         where the streaks and blotches fall
peel(material, ...), with its defaults:
    amount          0.5       how much paint has gone: 0 none, 0.5 big flakes over a good part, 1 most of it
    flake           0.33 m    how big the flakes are
    worst_below     1.2 m     the height above the ground under which the paint is worse, worst at the foot
    timber          (0.075, 0.066, 0.055)   the grey weathered timber under the paint (linear)
    seed            0         where the flakes fall

Both work on the world's coordinates, so a front's streaks run on across all its blocks. The height in `peel` is
measured from the ground under each object, the number 'pp_ground' that store.mark and store.prepare_for_render write
(objects without it are measured from z = 0). The copies are named '<material> • weathered' and '<material> • peeling'
and carry 'pp_weathered_of' or 'pp_peeling_of' (your material's name).
"""

import argparse
import os
import random
import sys

import bpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

TOOL = {
    'name': 'weathering',
    'what': 'weathered copies of materials you give: stone darkened by rain streaks and soot blotches broad enough to show on fronts seen edge-on (its tops glossy with rain if you ask), and paint peeling in big flakes to grey timber, worst near the ground; your material is left as it was',
    'call': "shades = [weathering.stone(n, seed=k) for k, n in enumerate(lay_stone.SHADES)];  lay_stone.lay(front, shades=shades, wood_material=weathering.peel(lay_stone.WOOD_MATERIAL))",
    'options': {
        'material': 'a store material by name, or one you hold (required)',
        'stone: dark': 'how much the streaks and blotches darken it: 0 none, 0.9 nearly black (0.62)',
        'stone: overall': "the whole stone's brightness, as a share (1.0)",
        'stone: streak_width, streak_length': 'the rain streaks: how broad and how long, metres (0.25, 3.0)',
        'stone: blotch': 'the soot blotches\' size, metres (1.8)',
        'stone: wet': 'how glossy from rain: 0 as it was, 1 its roughness halved (0.0)',
        'peel: amount': 'how much paint has gone: 0 none, 1 most of it (0.5)',
        'peel: flake': "the flakes' size, metres (0.33)",
        'peel: worst_below': 'the height above the ground under which the paint is worse, worst at the foot (1.2 m)',
        'peel: timber': 'the grey timber under the paint, linear ((0.075, 0.066, 0.055))',
        'seed': 'where the streaks, blotches or flakes fall (0)',
    },
    'materials': ['any material with a Principled BSDF (the sandstone shades, the dressings, the painted woods, the SURFACE photographs)'],
    'source': "`weather_stone` (line 1832) and `peel_paint` (line 1796) in '/home/claude/build-55-street/fronts/render_final.py', made into a tool: they now work on a copy (the builder changed the store's own materials, so every stone and door in the scene changed), take a seed, measure 'worst near the ground' from the ground under each object instead of the object's own origin, let the timber show whole where the paint has gone, and raise each flake's edge",
    'trap': 'a copy changes nothing until you give it to your objects (lay_stone takes shades=, trim_material= and wood_material=); streaks and blotches read only at full size in a drawn picture: on fronts 15 to 35 m away they are what keeps the stone from looking new, not a pattern you will see close',
}


def _node(nodes, kind, **inputs):
    node = nodes.new(kind)
    for key, value in inputs.items():
        node.inputs[key].default_value = value
    return node


def _math(nodes, links, operation, a, b=None, c=None, clamp=False):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    node.use_clamp = clamp
    for socket, value in zip(node.inputs, (a, b, c)):
        if value is None:
            continue
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value
    return node.outputs[0]


def _range(nodes, links, value, low, high, to_low=0.0, to_high=1.0):
    node = nodes.new('ShaderNodeMapRange')
    node.clamp = True
    node.inputs['From Min'].default_value = low
    node.inputs['From Max'].default_value = high
    node.inputs['To Min'].default_value = to_low
    node.inputs['To Max'].default_value = to_high
    if isinstance(value, bpy.types.NodeSocket):
        links.new(value, node.inputs['Value'])
    else:
        node.inputs['Value'].default_value = value
    return node.outputs['Result']


def _source(material, what):
    source = store.material(material) if isinstance(material, str) else material
    if not isinstance(source, bpy.types.Material):
        raise ValueError('%s needs a material (a store name or a material you hold), not %r' % (what, material))
    if not source.use_nodes or source.node_tree is None or not [n for n in source.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
        raise ValueError('the material %r has no Principled BSDF to %s' % (source.name, what))
    return source


def _shifted_position(nodes, links, seed):
    """The world position moved by a seeded amount, so another seed puts the pattern somewhere else."""
    rng = random.Random(seed)
    geometry = nodes.new('ShaderNodeNewGeometry')
    shift = nodes.new('ShaderNodeVectorMath')
    shift.operation = 'ADD'
    links.new(geometry.outputs['Position'], shift.inputs[0])
    shift.inputs[1].default_value = (rng.uniform(-500, 500), rng.uniform(-500, 500), rng.uniform(-500, 500)) if seed else (0.0, 0.0, 0.0)
    return shift.outputs['Vector'], geometry


def _before(links, socket):
    return socket.links[0].from_socket if socket.links else None


def stone(material, dark=0.62, overall=1.0, streak_width=0.25, streak_length=3.0, blotch=1.8, wet=0.0, seed=0):
    """A copy of the stone material darkened by rain streaks and soot blotches (see the note at the top). Returns the
    copy; the material you gave is not changed."""
    source = _source(material, 'weather')
    dark, overall, wet = float(dark), float(overall), float(wet)
    if not 0.0 <= dark <= 0.9:
        raise ValueError('dark is 0 (none) to 0.9 (nearly black), not %r' % (dark,))
    if not 0.2 <= overall <= 1.5:
        raise ValueError('overall is 0.2 to 1.5, not %r' % (overall,))
    if not 0.0 <= wet <= 1.0:
        raise ValueError('wet is 0 to 1, not %r' % (wet,))
    for name, value, low, high in (('streak_width', streak_width, 0.03, 3.0), ('streak_length', streak_length, 0.3, 30.0), ('blotch', blotch, 0.2, 20.0)):
        if not low <= float(value) <= high:
            raise ValueError('%s is %g to %g m, not %r' % (name, low, high, value))
    copy = source.copy()
    copy.name = '%s • weathered' % source.name
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    position, _ = _shifted_position(nodes, links, seed)
    stretch = nodes.new('ShaderNodeMapping')
    stretch.inputs['Scale'].default_value = (1.0 / streak_width, 1.0 / streak_width, 1.0 / streak_length)
    links.new(position, stretch.inputs['Vector'])
    streaks = _node(nodes, 'ShaderNodeTexNoise', Scale=1.0, Detail=4.0, Roughness=0.6)
    links.new(stretch.outputs['Vector'], streaks.inputs['Vector'])
    blotches = _node(nodes, 'ShaderNodeTexNoise', Scale=1.0 / blotch, Detail=3.0, Roughness=0.55)
    links.new(position, blotches.inputs['Vector'])
    worst = _math(nodes, links, 'MAXIMUM', _range(nodes, links, streaks.outputs['Fac'], 0.43, 0.60),
                  _range(nodes, links, blotches.outputs['Fac'], 0.42, 0.62))
    shade = _range(nodes, links, worst, 0.0, 1.0, overall, overall * (1.0 - dark))
    grey = nodes.new('ShaderNodeCombineXYZ')
    for axis in ('X', 'Y', 'Z'):
        links.new(shade, grey.inputs[axis])
    for principled in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        base = principled.inputs['Base Color']
        before = _before(links, base)
        darker = nodes.new('ShaderNodeMix')
        darker.data_type = 'RGBA'
        darker.blend_type = 'MULTIPLY'
        darker.inputs[0].default_value = 1.0
        if before is not None:
            links.new(before, darker.inputs[6])
        else:
            darker.inputs[6].default_value = base.default_value
        links.new(grey.outputs[0], darker.inputs[7])
        links.new(darker.outputs[2], base)
        if wet > 0:
            rough = principled.inputs['Roughness']
            rough_before = _before(links, rough)
            glossy = _math(nodes, links, 'MULTIPLY', rough_before if rough_before is not None else rough.default_value, 1.0 - 0.5 * wet)
            links.new(glossy, rough)
    copy['pp_weathered_of'] = source.name
    copy['pp_weathered'] = dark
    return copy


def peel(material, amount=0.5, flake=0.33, worst_below=1.2, timber=(0.075, 0.066, 0.055), seed=0):
    """A copy of the painted material with its paint flaking off in big patches to grey timber, worst near the ground
    (see the note at the top). Returns the copy; the material you gave is not changed."""
    source = _source(material, 'peel')
    amount, flake, worst_below = float(amount), float(flake), float(worst_below)
    if not 0.0 <= amount <= 1.0:
        raise ValueError('amount is 0 (no paint gone) to 1 (most of it), not %r' % (amount,))
    if not 0.03 <= flake <= 3.0:
        raise ValueError('flake is 0.03 to 3 m, not %r' % (flake,))
    if not 0.0 <= worst_below <= 5.0:
        raise ValueError('worst_below is 0 to 5 m, not %r' % (worst_below,))
    if len(timber) != 3:
        raise ValueError('timber is a colour of three numbers (linear), not %r' % (timber,))
    copy = source.copy()
    copy.name = '%s • peeling' % source.name
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    position, geometry = _shifted_position(nodes, links, seed)
    flakes = _node(nodes, 'ShaderNodeTexNoise', Scale=1.0 / flake, Detail=8.0, Roughness=0.7)
    links.new(position, flakes.inputs['Vector'])
    height = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geometry.outputs['Position'], height.inputs['Vector'])
    ground = nodes.new('ShaderNodeAttribute')
    ground.attribute_type = 'OBJECT'
    ground.attribute_name = 'pp_ground'
    above = _math(nodes, links, 'SUBTRACT', height.outputs['Z'], ground.outputs['Fac'])
    worse = _range(nodes, links, above, worst_below, 0.2, 0.0, 0.08) if worst_below > 0.2 else 0.0   # worse near the ground
    middle = 0.68 - 0.2 * amount
    gone = _range(nodes, links, _math(nodes, links, 'ADD', flakes.outputs['Fac'], worse), middle - 0.015, middle + 0.015)
    if amount <= 0.0:
        gone = 0.0
    for principled in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        base = principled.inputs['Base Color']
        before = _before(links, base)
        bare = nodes.new('ShaderNodeMix')
        bare.data_type = 'RGBA'
        if isinstance(gone, bpy.types.NodeSocket):
            links.new(gone, bare.inputs[0])
        else:
            bare.inputs[0].default_value = gone
        if before is not None:
            links.new(before, bare.inputs[6])
        else:
            bare.inputs[6].default_value = base.default_value
        bare.inputs[7].default_value = (*timber, 1.0)
        links.new(bare.outputs[2], base)
        rough = principled.inputs['Roughness']                                    # bare timber is matte
        rough_before = _before(links, rough)
        matte = nodes.new('ShaderNodeMix')
        matte.data_type = 'FLOAT'
        if isinstance(gone, bpy.types.NodeSocket):
            links.new(gone, matte.inputs[0])
        else:
            matte.inputs[0].default_value = gone
        if rough_before is not None:
            links.new(rough_before, matte.inputs[2])
        else:
            matte.inputs[2].default_value = rough.default_value
        matte.inputs[3].default_value = 0.88
        links.new(matte.outputs[0], rough)
        if isinstance(gone, bpy.types.NodeSocket):                                # the paint's edge stands a little proud
            normal = principled.inputs['Normal']
            normal_before = _before(links, normal)
            bump = _node(nodes, 'ShaderNodeBump', Strength=0.3, Distance=0.002)
            links.new(_math(nodes, links, 'SUBTRACT', 1.0, gone), bump.inputs['Height'])
            if normal_before is not None:
                links.new(normal_before, bump.inputs['Normal'])
            links.new(bump.outputs['Normal'], normal)
    copy['pp_peeling_of'] = source.name
    copy['pp_peeling'] = amount
    return copy


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--stone', action='append', default=[], help='a stone material to weather (repeat for more)')
    parser.add_argument('--peel', action='append', default=[], help='a painted material to peel (repeat for more)')
    parser.add_argument('--dark', type=float, default=0.62, help='how much the stone darkens, 0 to 0.9; default 0.62')
    parser.add_argument('--amount', type=float, default=0.5, help='how much paint has gone, 0 to 1; default 0.5')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not (args.blend and (args.stone or args.peel) and args.out):
        parser.error('--blend, --stone or --peel, and --out are needed to make weathered copies')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    for name in args.stone:
        print('%s: made %s' % (name, stone(name, dark=args.dark, seed=args.seed).name))
    for name in args.peel:
        print('%s: made %s' % (name, peel(name, amount=args.amount, seed=args.seed).name))
    for material in bpy.data.materials:
        if material.get('pp_weathered_of') or material.get('pp_peeling_of'):
            material.use_fake_user = True                                         # kept in the saved file though no object uses it yet
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))


if __name__ == '__main__':
    main()
