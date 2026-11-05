"""
What this file does: makes a mossy copy of a material you give, the way moss grows on old stone and wood: in patches,
not as a carpet, on the faces that look up (a wall's top stones, ledges, sills, the tops of copes and steps) and up
the damp foot of whatever stands on the ground, where it is thickest, in soft cushions a little rougher and more matte
than the stone round them. The copy is returned and your material is left as it was, so only the things you give the
copy get moss. Nothing here chooses where moss grows on a scene: you choose the objects that get the mossy copy.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import moss, dry_wall
    mossy = moss.add('SURFACE • old_stone_wall_02', amount=0.85)          # a store material by name, or one you hold
    dry_wall.lay(line, material=mossy, ground=yard)                         # the wall's stones get the moss
    store.use_material(my_trough, moss.add(my_stone, foot=0.2))

From the command line:

    python3 moss.py --help
    python3 moss.py --blend IN.blend --material "SURFACE • old_stone_wall_02" --amount 0.8 --out OUT.blend

Options, with their defaults:
    amount      0.8       how much: 0 none, 0.5 a little in the best places, 1 thick, up to 1.5
    foot        0.35 m    how far up from the ground moss climbs a thing's foot (0: none at the foot)
    facing      (0.45, 0.85)   how much a face must look up to carry moss: none below the first, full above the second
                          (the up part of the face's direction, 0 a wall face to 1 a flat top)
    scale       3.0       the patches' size: 3 is patches about 30 cm across, 6 about 15 cm
    colour      (0.035, 0.05, 0.014)    the moss's darkest green (linear); its cushions vary lighter and yellower

The foot is measured from the ground under each object, the number 'pp_ground' that store.mark and
store.prepare_for_render write (objects without it are measured from z = 0). The copy is named '<material> • moss'
and carries 'pp_moss' (the amount) and 'pp_moss_of' (your material's name).
"""

import argparse
import os
import sys

import bpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

TOOL = {
    'name': 'moss',
    'what': 'a mossy copy of a material you give: patchy moss on the faces that look up (tops, ledges) and up the damp foot, '
            'matte and a little raised; your material is left as it was',
    'call': "mossy = moss.add('SURFACE • old_stone_wall_02', amount=0.85);  dry_wall.lay(line, material=mossy)",
    'options': {
        'material': 'a store material by name, or one you hold (required)',
        'amount': 'how much: 0 none, 1 thick, up to 1.5 (0.8)',
        'foot': 'how far up from the ground moss climbs a thing\'s foot, metres; 0 none (0.35)',
        'facing': 'how much a face must look up to carry moss: none below the first, full above the second ((0.45, 0.85))',
        'scale': 'patch size: 3 is about 30 cm across (3.0)',
        'colour': "the moss's darkest green, linear ((0.035, 0.05, 0.014))",
    },
    'materials': ['any material with a Principled BSDF (stone, wood, the SURFACE photographs)'],
    'source': "`add_moss` in the barn dresser's '54 barn dress - render_final.py' (line 242), made into a tool: it now works on a "
              'copy, measures the foot from the ground under each object instead of z = 0, works on plain colours too, and '
              'makes the moss matte and cushioned',
    'trap': 'moss under the AgX view and at dusk shows far less than in the nodes: judge it in a drawn picture (the dresser '
            'used amount 0.85 on a dry-stone wall); a copy changes nothing until you give it to your objects',
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


def _range(nodes, links, value, low, high):
    node = nodes.new('ShaderNodeMapRange')
    node.clamp = True
    node.inputs['From Min'].default_value = low
    node.inputs['From Max'].default_value = high
    if isinstance(value, bpy.types.NodeSocket):
        links.new(value, node.inputs['Value'])
    else:
        node.inputs['Value'].default_value = value
    return node.outputs['Result']


def add(material, amount=0.8, foot=0.35, facing=(0.45, 0.85), scale=3.0, colour=(0.035, 0.05, 0.014)):
    """A copy of the material with patchy moss on its upward faces and up the foot (see the note at the top). Returns
    the copy; the material you gave is not changed."""
    source = store.material(material) if isinstance(material, str) else material
    if not isinstance(source, bpy.types.Material):
        raise ValueError('moss needs a material (a store name or a material you hold), not %r' % (material,))
    amount, foot, scale = float(amount), float(foot), float(scale)
    if not 0.0 <= amount <= 1.5:
        raise ValueError('amount is 0 (none) to 1.5 (very thick), not %r' % (amount,))
    if not 0.0 <= foot <= 3.0:
        raise ValueError('foot is 0 to 3 m, not %r' % (foot,))
    if not 0.2 <= scale <= 50.0:
        raise ValueError('scale is 0.2 to 50 (3 is patches about 30 cm across), not %r' % (scale,))
    low, high = float(facing[0]), float(facing[1])
    if not -1.0 <= low < high <= 1.0:
        raise ValueError('facing is two numbers from -1 to 1, the first smaller, not %r' % (facing,))
    if not source.use_nodes or source.node_tree is None or not [n for n in source.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
        raise ValueError('the material %r has no Principled BSDF to add moss to' % source.name)
    copy = source.copy()
    copy.name = '%s • moss' % source.name
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    geometry = nodes.new('ShaderNodeNewGeometry')
    facing_up = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geometry.outputs['Normal'], facing_up.inputs['Vector'])
    on_top = _range(nodes, links, facing_up.outputs['Z'], low, high)
    where = on_top
    if foot > 0:
        position = nodes.new('ShaderNodeSeparateXYZ')
        links.new(geometry.outputs['Position'], position.inputs['Vector'])
        ground = nodes.new('ShaderNodeAttribute')
        ground.attribute_type = 'OBJECT'
        ground.attribute_name = 'pp_ground'
        above = _math(nodes, links, 'SUBTRACT', position.outputs['Z'], ground.outputs['Fac'])
        at_foot = _range(nodes, links, above, foot, 0.0)
        at_foot = _math(nodes, links, 'POWER', at_foot, 0.7)
        where = _math(nodes, links, 'MAXIMUM', on_top, at_foot)
    patches = _node(nodes, 'ShaderNodeTexNoise', Scale=scale, Detail=8.0, Roughness=0.55)
    links.new(geometry.outputs['Position'], patches.inputs['Vector'])
    cushions = _node(nodes, 'ShaderNodeTexNoise', Scale=scale * 7.0, Detail=4.0, Roughness=0.6)
    links.new(geometry.outputs['Position'], cushions.inputs['Vector'])
    patchy = _range(nodes, links, patches.outputs['Fac'], 0.42, 0.58)               # patches, not a carpet
    lumpy = _math(nodes, links, 'MULTIPLY_ADD', _range(nodes, links, cushions.outputs['Fac'], 0.3, 0.7), 0.45, 0.55)
    factor = _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'MULTIPLY', where, patchy), lumpy)
    factor = _math(nodes, links, 'MULTIPLY', factor, amount, clamp=True)
    tint = nodes.new('ShaderNodeMix')                                              # darker green to a yellower, lighter cushion
    tint.data_type = 'RGBA'
    tint.inputs[6].default_value = (*colour, 1.0)
    tint.inputs[7].default_value = (colour[0] * 2.3 + 0.016, colour[1] * 2.2 + 0.014, colour[2] * 1.4, 1.0)
    links.new(cushions.outputs['Fac'], tint.inputs[0])
    for principled in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        base = principled.inputs['Base Color']
        before = base.links[0].from_socket if base.links else None
        blend = nodes.new('ShaderNodeMix')
        blend.data_type = 'RGBA'
        links.new(factor, blend.inputs[0])
        if before is not None:
            links.new(before, blend.inputs[6])
        else:
            blend.inputs[6].default_value = base.default_value
        links.new(tint.outputs[2], blend.inputs[7])
        links.new(blend.outputs[2], base)
        rough = principled.inputs['Roughness']
        rough_before = rough.links[0].from_socket if rough.links else None
        matte = nodes.new('ShaderNodeMix')                                         # moss is matte
        matte.data_type = 'FLOAT'
        links.new(factor, matte.inputs[0])
        if rough_before is not None:
            links.new(rough_before, matte.inputs[2])
        else:
            matte.inputs[2].default_value = rough.default_value
        matte.inputs[3].default_value = 0.92
        links.new(matte.outputs[0], rough)
        normal = principled.inputs['Normal']
        normal_before = normal.links[0].from_socket if normal.links else None
        bump = _node(nodes, 'ShaderNodeBump', Strength=0.35, Distance=0.004)
        links.new(_math(nodes, links, 'MULTIPLY', factor, cushions.outputs['Fac']), bump.inputs['Height'])
        if normal_before is not None:
            links.new(normal_before, bump.inputs['Normal'])
        links.new(bump.outputs['Normal'], normal)
    copy['pp_moss'] = amount
    copy['pp_moss_of'] = source.name
    return copy


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--material', action='append', default=[], help='a material in the file or the store (repeat for more)')
    parser.add_argument('--amount', type=float, default=0.8, help='how much moss, 0 to 1.5; default 0.8')
    parser.add_argument('--foot', type=float, default=0.35, help='how far up the foot moss climbs, metres; default 0.35')
    parser.add_argument('--scale', type=float, default=3.0, help='patch size (3: about 30 cm); default 3')
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not (args.blend and args.material and args.out):
        parser.error('--blend, --material and --out are needed to make mossy copies')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    for name in args.material:
        print('%s: made %s' % (name, add(name, amount=args.amount, foot=args.foot, scale=args.scale).name))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))


if __name__ == '__main__':
    main()
