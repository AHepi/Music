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

Real moss, with thickness (made after the owner's word of 6 November 2026, "Ok. I meant the rocks with moss. Not the
pavement lol. Those are still lacking a lot of detail"): the moss above is a colour on the stone only. grow() grows real
moss on a stone object you give: cushions with thickness, thick on the tops and in the hollows, thinning to nothing at
their edges and creeping over the rims (a little hanging down the sides), in the shelf's photographed moss
(forest_leaves_02: its lumps, roughness and light and dark) under greens from yellow-green young cushions to dark olive moss,
brownish dry tips in places, a soft sheen; and on them a pile of tiny tufts and fronds (about 1.5 cm, star-shaped like
the hair-cap moss of Japanese gardens, some with capsules on thin red-brown stalks) laid by Blender's particle system as
copies, so it stays light. The rocks tool grows the same cushions on its rocks when they have moss (moss_style='cushions',
its default), inside each rock's own shape so its particle copies carry them, and gives their bare stone pale lichen
crusts (add's lichen). feet() puts moss and small plants where rocks meet the soil: moss tufts straight on the soil,
spilling from each rock's foot in patches, the grass tool's turf round it, and ferns at the biggest.

    moss_obj = moss.grow(bpy.data.objects['stone basin'], amount=0.9, thickness=0.03)   # 'moss on stone basin'
    laid = rocks.scatter(yard, kind='boulder', count=20, moss=0.9, seed=2)                # cushions by default
    moss.feet(yard, laid, turf=0.5, ferns=2, seed=3)
    old_look = rocks.scatter(yard, kind='boulder', count=20, moss=0.9, moss_style='paint', seed=2)   # the colour only

Options of grow(), with their defaults:
    target      a mesh object of stone; it is not changed (the moss is a new object parented to it)
    amount      0.8   about half the places moss could grow at 1; 0.5 a quarter; 1.5 nearly all
    thickness   0.03 m   the cushions' depth in the middle (they thin to nothing at their edges)
    facing      (0.3, 0.85)   how much a face must look up to carry moss (as add's)
    hollows     0.6   how much moss the cracks and hollows carry, 0 to 1
    foot        0.15 m   how far up from the ground moss climbs the foot (the object's 'pp_ground', or its lowest point)
    pile_amount 1.0   the tufts: about 16,000 a square metre of cushion; 0 none
    pile_length 0.015 m   a tuft's height
    colour      (0.07, 0.105, 0.02)   the moss's middle green, linear; young cushions are yellower, old ones darker
    greens      'olive'   the cushions' greens: 'olive' dark olive with yellow-green where the light falls, deep darks
                          between the tufts (as the garden builder's moss at dusk); 'bright' the first, brighter greens
                          (they read as smooth lime-green felt at dusk)
    sheen       0.3   the cushions' soft sheen at a grazing look, 0 to 1 (the tufts get 0.7 of it); 0.8 lit every
                      mossy top lime under a dusk sky
    lumps       0.7   the photographed moss's own lumps on the cushions (its relief), 0 smooth to 2; 0.2 read as felt
                      (sheen=0.8, lumps=0.2, greens='bright': the cushions as they first were)
    wet         0.4   after rain: fewer dry tips, shinier tufts
    step        0.012 m   how finely the cushions follow the object
    droop       0.5   how far a cushion on a side hangs down
    seed        0
    An open shape (a basin carved open underneath, a lantern's hollow foot) is closed for the growing: its holes are
    filled as a solid stone's are; a thin sheet, or a shell with a wide opening on top (a trough, a pot), is thickened
    inwards instead, so no moss grows over the opening; your object stays as it is. The moss object's 'moss_closed'
    says what was done ('holes filled: 2', 'thickened').
Options of feet(), with their defaults: ground (required), spots (required: what rocks.scatter or at_spots gave back,
    rocks.place's objects, or (x, y, size) places), reach 0.22 m, amount 0.7, turf 0.5, ferns 0,
    pile_amount 1.0, colour (0.065, 0.1, 0.02), wet 0.4, seed 0, collection (the ground's),
    keep None (a test of one place, keep(x, y) giving True where moss, turf and ferns may go),
    keep_out None (an area they stay out of: a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or a list of them;
    a path, a step, the water), sheen None (the tufts' sheen; as the pile's). With keep or keep_out a fern goes to
    another side of its rock where its crown and its fronds keep out of those places, or a smaller one, or to the next
    biggest rock; 'ferns_left_out' in what feet gives back says how many found no room.
add() also takes lichen (pale lichen crusts on the bare stone, 0 to 1.5; 0.0) and hollows (moss in the cracks the
    cushions found, 0 to 1; 0.0); on a mesh with real cushions its flat moss follows them ('moss_film').
on_mesh(mesh, ...) and pile(obj, ...) are the two halves grow() and the rocks tool use: cushions into a mesh in its own
    coordinates (a second material, points weighted in deform group 0), and the tufts on an object's vertex group
    'moss pile'.

What it costs (measured on this machine, 6 November 2026, against the same rocks with moss_style='paint'): a 1.05 m
boulder set singly gets 0.42 square metres of cushions, 2,455 more faces (10,436 to 12,891, about a quarter more) and
6,779 tufts; a 0.8 m flat stone 1,254 more faces (5,314 to 6,568) and 4,007 tufts; 20 scattered rocks draw 80,390 faces
instead of 65,712, and with the moss at their feet about 30,000 tufts in all, as copies. A 540 x 960 picture of two big
mossy rocks with 22 small and far ones and the moss at their feet (Cycles, 40 samples) drew in 129 s instead of 109 s
seen close, 60 s instead of 56 s from 6 m; memory at its peak 1.92 GB instead of 1.50 GB; the saved file is 2.5 MB
bigger (7.8 against 5.3 MB, compressed: the particle system stores its tufts' places); building the rocks takes about
4 s longer.
"""

import argparse
import math
import os
import sys

import bpy
import bmesh
import numpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _noise  # noqa: E402

# the cushions' greens (linear): their darkest, old moss (the brighter green of the owner's garden picture, as the rocks
# tool's moss), bright young cushions and brownish dry tips; pale lichen crusts on the bare stone
CUSHION_COLOUR = (0.07, 0.105, 0.02)
DRY = (0.105, 0.072, 0.028)
LICHEN = (0.2, 0.215, 0.17)
LICHEN_YELLOW = (0.23, 0.205, 0.1)
MOSS_SET = 'forest_leaves_02'      # the shelf's photographed moss: the cushions' relief, roughness and light and dark

TOOL = {
    'name': 'moss',
    'what': 'moss on stone, two ways: real moss (cushions with thickness, thick on the tops and in the hollows, thinning '
            'at their edges and spilling over the rims; a pile of tiny tufts and fronds on them laid by Blender\'s particle '
            'system, some with capsules on red-brown stalks; greens from yellow-green young to dark olive old, brownish dry tips; '
            'photographed moss under them) grown on a stone object you give or on the rocks tool\'s rocks, with moss '
            'and small plants at the rocks\' feet; and a mossy copy of a material (patches of green on the faces that '
            'look up and up the damp foot, pale lichen crusts on the bare stone if asked); your things are left as they were',
    'call': "moss.grow(my_basin, amount=0.9);  moss.feet(yard, laid_rocks, turf=0.5, ferns=1);  "
            "mossy = moss.add('SURFACE • old_stone_wall_02', amount=0.85, lichen=0.6);  dry_wall.lay(line, material=mossy)",
    'options': {
        'material': 'add: a store material by name, or one you hold (required)',
        'amount': 'how much: 0 none, 1 thick (grow: about half the places moss could grow; add: thick), up to 1.5 (add 0.8, grow 0.8, feet 0.7)',
        'foot': 'how far up from the ground moss climbs a thing\'s foot, metres; 0 none (add 0.35, grow 0.15)',
        'facing': 'how much a face must look up to carry moss: none below the first, full above the second (add (0.45, 0.85), grow (0.3, 0.85))',
        'scale': 'add: patch size: 3 is about 30 cm across (3.0)',
        'colour': "the moss's green, linear (add (0.035, 0.05, 0.014), its darkest; grow and the cushions (0.07, 0.105, 0.02), "
                  "the middle of their greens; feet a little darker (0.065, 0.1, 0.02))",
        'greens': "grow: the cushions' greens: 'olive' dark olive with yellow-green where the light falls and deep darks "
                  "between the tufts, as the garden builder's moss at dusk; 'bright' the first, brighter greens, which "
                  "read as smooth lime-green felt at dusk ('olive'; the rocks tool's cushions get 'olive' too)",
        'sheen': "grow: the cushions' soft sheen at a grazing look, 0 to 1; the tufts get 0.7 of it (0.3; 0.8 lit every "
                 "mossy top lime under a dusk sky); feet: the tufts' sheen (None: 0.21)",
        'lumps': "grow: the photographed moss's own lumps on the cushions, its relief, 0 smooth to 2 (0.7; 0.2 read as "
                 "smooth felt). sheen=0.8, lumps=0.2, greens='bright' gives the cushions as they first were",
        'lichen': 'add: pale lichen crusts on the bare stone, 0 none to 1.5 (0.0; the rocks tool gives its cushioned rocks 0.6)',
        'hollows': 'add: moss in the cracks and hollows the cushions found (their \'moss_hollow\'), 0 none to 1 (0.0); grow: '
                   'how much moss the hollows carry, 0 to 1 (0.6)',
        'target': 'grow: a mesh object of stone (a basin, a lantern\'s foot, a wall top, a rock of your own) (required); not '
                  'changed; an open one (a basin carved open underneath) is closed for the growing, its holes filled; a thin '
                  'sheet, or a shell with a wide opening on top (a trough, a pot), is thickened inwards instead, so no moss '
                  'grows over the opening',
        'thickness': 'grow: the cushions\' depth in the middle, metres (0.03)',
        'pile_amount': 'grow and feet: the tufts: 1 about 16,000 a square metre of cushion, 0 none, up to 3 (1.0)',
        'pile_length': 'grow: a tuft\'s height, metres (0.015)',
        'wet': 'grow and feet: how wet the moss is after rain, 0 to 1: fewer dry tips, shinier tufts (0.4)',
        'step': 'grow: how finely the cushions follow your object, metres (0.012; smaller is finer and heavier)',
        'droop': 'grow: how far a cushion on a side hangs down, 0 none to 1 (0.5)',
        'spots': 'feet: the rocks: what rocks.scatter or rocks.at_spots gave back, the objects rocks.place gave back, or (x, y, size) places (required)',
        'ground': 'feet: the ground the rocks stand on, a mesh object; not changed (required)',
        'reach': 'feet: how far out from a rock\'s foot the moss on the soil reaches, metres (0.22)',
        'turf': 'feet: grass tufts round the feet (the grass tool\'s turf), 0 none, 1 full (0.5)',
        'ferns': 'feet: how many small ferns (the fern part) at the feet of the biggest rocks (0)',
        'keep': 'feet: a test of one place, keep(x, y) giving True where the moss, turf and ferns may go, False keeping '
                'them out (a path, a step, the water); a fern then goes to another side of its rock, or a smaller one, '
                'or to the next biggest rock (None)',
        'keep_out': 'feet: an area the moss, turf and ferns stay out of: a rectangle (x0, y0, x1, y1), a polygon '
                    "[(x, y), ...] or a list of them; a fern's crown and its fronds' reach keep out of it too (None)",
        'seed': 'grow and feet: the same seed, the same moss (0)',
        'collection': 'grow and feet: where the new objects go (grow: your object\'s collection; feet: the ground\'s)',
    },
    'materials': ['any material with a Principled BSDF (stone, wood, the SURFACE photographs)', 'SURFACE • forest_leaves_02 (under the cushions)',
                  'moss • cushions (made)', 'moss • pile (made)'],
    'source': "`add_moss` in the barn dresser's '54 barn dress - render_final.py' (line 242), made into a tool: it now works on a "
              'copy, measures the foot from the ground under each object instead of z = 0, works on plain colours too, and '
              'makes the moss matte and cushioned. The real moss (grow, feet, the rocks tool\'s cushions) made for the owner\'s '
              'word of 6 November 2026, seeing the garden\'s rocks pass ("Ok. I meant the rocks with moss. Not the pavement '
              'lol. Those are still lacking a lot of detail"): its moss was a colour only on the stone '
              "('/home/claude/build-57-garden/rocks/render_final.py', rocks pass, line 1940 on); after the mossy rocks of the "
              "owner's garden picture and the board brief/boards/japanese garden (01: pale lichen speckles on a boulder; moss "
              'on tops and in the joints); the photographed moss Poly Haven forest_leaves_02 (CC0). From the garden '
              "builder's moss pass ('/home/claude/build-57-garden/moss/render_final.py'): the cushions' look at dusk "
              '(lines 2371-2400: sheen 0.8 to 0.3, the tufts 0.7 of it, the darks between the tufts 0.38 to 0.24, the '
              "greens young 1.8, 1.6, 0.9, middle 0.95, 0.95, 0.85, old 0.42, 0.48, 0.55 times the colour, the photograph's "
              'lumps 0.2 to 0.7: the defaults now, the old look by greens=\'bright\', sheen=0.8, lumps=0.2); grow on an '
              'open shape (lines 2317-2334: the builder grew the basin\'s moss on a hidden copy with its holes filled; grow '
              'now fills them itself); keep and keep_out for feet (lines 2349-2368: the builder set its ferns by hand '
              'after the feet tool put one on the path twice)',
    'trap': 'moss under the AgX view and at dusk shows far less than in the nodes: judge it in a drawn picture (the dresser '
            'used amount 0.85 on a dry-stone wall); a copy changes nothing until you give it to your objects. The real moss: '
            'its tufts are particle copies drawn only when the picture is drawn; a 1 m boulder with real moss carries about '
            '7,000 tufts and its cushions add about a quarter to its faces (a picture drew 18% slower, with 28% more memory at its peak); the cushions stand up to their thickness off the '
            'stone, so a thing stood on a mossy top stands on the moss; grow() follows your object as it is drawn, with its '
            'modifiers, and does not follow later changes to it: grow again; inside a basin\'s bowl the moss grows under '
            'the water too (hidden by it); feet sets its ferns at a random side of the biggest rocks: near a path give '
            'keep_out (the path) or keep, or a fern lands on the path (it did twice in the garden); the defaults of the '
            'cushions changed on 6 November 2026 (darker, olive, less sheen, stronger lumps): an earlier script drawn '
            'with a fresh kit draws its moss darker; set greens, sheen and lumps to keep a look',
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


def add(material, amount=0.8, foot=0.35, facing=(0.45, 0.85), scale=3.0, colour=(0.035, 0.05, 0.014), lichen=0.0,
        hollows=0.0):
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
    # on a mesh the cushions tool grew real moss on ('moss_cushioned' 1), the flat moss follows the cushions' film
    # ('moss_film': under and just round the cushions, and down into the cracks) instead of its own patches; on any
    # other mesh both numbers read 0 and nothing changes
    film = nodes.new('ShaderNodeAttribute')
    film.attribute_name = 'moss_film'
    cushioned = nodes.new('ShaderNodeAttribute')
    cushioned.attribute_name = 'moss_cushioned'
    follow = nodes.new('ShaderNodeMix')
    follow.data_type = 'FLOAT'
    links.new(cushioned.outputs['Fac'], follow.inputs[0])
    links.new(factor, follow.inputs[2])
    links.new(_math(nodes, links, 'MULTIPLY', film.outputs['Fac'], lumpy), follow.inputs[3])
    factor = follow.outputs[0]
    if hollows > 0:                       # the cracks and hollows the cushions tool found ('moss_hollow')
        hollow = nodes.new('ShaderNodeAttribute')
        hollow.attribute_name = 'moss_hollow'
        factor = _math(nodes, links, 'MAXIMUM', factor,
                       _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'MULTIPLY', hollow.outputs['Fac'], patchy), float(hollows)))
    factor = _math(nodes, links, 'MULTIPLY', factor, amount, clamp=True)
    lichen_f = _lichen(nodes, links, geometry, factor, float(lichen)) if lichen > 0 else None
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
        coloured = blend.outputs[2]
        if lichen_f is not None:                                                    # pale lichen crusts on the bare stone
            crust = nodes.new('ShaderNodeMix')
            crust.data_type = 'RGBA'
            links.new(lichen_f[0], crust.inputs[0])
            links.new(coloured, crust.inputs[6])
            links.new(lichen_f[1], crust.inputs[7])
            coloured = crust.outputs[2]
        links.new(coloured, base)
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
        roughness = matte.outputs[0]
        if lichen_f is not None:
            dry_crust = nodes.new('ShaderNodeMix')
            dry_crust.data_type = 'FLOAT'
            links.new(lichen_f[0], dry_crust.inputs[0])
            links.new(roughness, dry_crust.inputs[2])
            dry_crust.inputs[3].default_value = 0.8
            roughness = dry_crust.outputs[0]
        links.new(roughness, rough)
        normal = principled.inputs['Normal']
        normal_before = normal.links[0].from_socket if normal.links else None
        bump = _node(nodes, 'ShaderNodeBump', Strength=0.35, Distance=0.004)
        height = _math(nodes, links, 'MULTIPLY', factor, cushions.outputs['Fac'])
        if lichen_f is not None:
            height = _math(nodes, links, 'ADD', height, _math(nodes, links, 'MULTIPLY', lichen_f[0], 0.35))
        links.new(height, bump.inputs['Height'])
        if normal_before is not None:
            links.new(normal_before, bump.inputs['Normal'])
        links.new(bump.outputs['Normal'], normal)
    copy['pp_moss'] = amount
    copy['pp_moss_of'] = source.name
    if lichen > 0:
        copy['pp_lichen'] = float(lichen)
    return copy


def _lichen(nodes, links, geometry, moss_factor, lichen):
    """Pale lichen crusts on the bare stone: round rosettes 2 to 6 cm across (a Voronoi's cells, their edges made to
    wander), gathered in some places and missing in others, grey-green and a few yellower, never on the moss. Returns
    (how much lichen, its colour) as sockets."""
    warp = _node(nodes, 'ShaderNodeTexNoise', Scale=9.0, Detail=3.0, Roughness=0.6)
    links.new(geometry.outputs['Position'], warp.inputs['Vector'])
    centred = nodes.new('ShaderNodeVectorMath')
    centred.operation = 'MULTIPLY_ADD'
    links.new(warp.outputs['Color'], centred.inputs[0])
    centred.inputs[1].default_value = (0.035, 0.035, 0.035)
    links.new(geometry.outputs['Position'], centred.inputs[2])
    cells = nodes.new('ShaderNodeTexVoronoi')
    cells.feature = 'F1'
    cells.inputs['Scale'].default_value = 24.0
    links.new(centred.outputs['Vector'], cells.inputs['Vector'])
    rosette = _range(nodes, links, cells.outputs['Distance'], 0.46, 0.2)            # a disc in each cell, soft at its rim
    where = _node(nodes, 'ShaderNodeTexNoise', Scale=1.7, Detail=3.0, Roughness=0.55)
    links.new(geometry.outputs['Position'], where.inputs['Vector'])
    gathered = _range(nodes, links, where.outputs['Fac'], 0.46, 0.6)
    bare = _range(nodes, links, moss_factor, 0.35, 0.05)                           # none on the moss
    amount = _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'MULTIPLY', rosette, gathered), bare)
    amount = _math(nodes, links, 'MINIMUM', _math(nodes, links, 'MULTIPLY', amount, lichen * 0.9), 1.0)
    yellower = nodes.new('ShaderNodeSeparateColor')
    links.new(cells.outputs['Color'], yellower.inputs['Color'])
    tone = nodes.new('ShaderNodeMix')
    tone.data_type = 'RGBA'
    links.new(_range(nodes, links, yellower.outputs['Red'], 0.78, 0.82), tone.inputs[0])
    tone.inputs[6].default_value = (*LICHEN, 1.0)
    tone.inputs[7].default_value = (*LICHEN_YELLOW, 1.0)
    speckle = _node(nodes, 'ShaderNodeTexNoise', Scale=160.0, Detail=2.0, Roughness=0.5)  # the crust's own grain
    links.new(geometry.outputs['Position'], speckle.inputs['Vector'])
    lighter = nodes.new('ShaderNodeMapRange')
    lighter.inputs['To Min'].default_value = 0.65
    links.new(_range(nodes, links, speckle.outputs['Fac'], 0.25, 0.75), lighter.inputs['Value'])
    shaded = nodes.new('ShaderNodeMix')
    shaded.data_type = 'RGBA'
    shaded.blend_type = 'MULTIPLY'
    shaded.inputs[0].default_value = 1.0
    links.new(tone.outputs[2], shaded.inputs[6])
    links.new(lighter.outputs['Result'], shaded.inputs[7])
    return amount, shaded.outputs[2]


# ----------------------------------------------------------------------------------------------- real moss: cushions
#
# The real moss: cushions with thickness grown on a mesh as a skin of their own (thick on the tops and in the hollows,
# thinning to nothing at their edges, creeping over the rims and hanging a little down the sides), covered with the
# shelf's photographed moss under the moss's own greens, and a pile of tiny tufts and fronds on them laid by Blender's
# particle system (copies, so it stays light). On a rock the cushions are part of the rock's own mesh (a second
# material), so the rocks tool's particle copies carry them; on an object you give, grow() makes them an object of
# their own, parented to yours.

def _attr(nodes, name):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_name = name
    return node


def _ramp(nodes, stops):
    node = nodes.new('ShaderNodeValToRGB')
    elements = node.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, (position, colour) in zip(elements, stops):
        element.position = position
        element.color = (*colour, 1.0)
    return node


def _greens(colour):
    """(young, middle, old): bright young cushions, the colour given, dark old moss."""
    young = (colour[0] * 2.3 + 0.016, colour[1] * 2.2 + 0.014, colour[2] * 1.4)
    old = (colour[0] * 0.5, colour[1] * 0.58, colour[2] * 0.7)
    return young, tuple(colour), old


# the cushions' greens at dusk (the garden builder's moss pass, 6 November 2026): the bright greens above drew the
# cushions as smooth lime-green felt at dusk; young, middle and old as these times the colour drew dark olive moss,
# yellow-green where the light falls on it
OLIVE = ((1.8, 1.6, 0.9), (0.95, 0.95, 0.85), (0.42, 0.48, 0.55))
GREENS = ('olive', 'bright')
SHEEN = 0.3          # the cushions' sheen (the pile's is 0.7 of it); 0.8 lit every mossy top lime under a dusk sky
LUMPS = 0.7          # the photographed moss's own relief on the cushions (its normal picture); 0.2 read as smooth felt


def _cushion_greens(colour, greens):
    """(young, middle, old) for the cushions: 'olive' (darker and more olive, as the garden builder's at dusk) or
    'bright' (the brighter, yellower greens the cushions had first)."""
    if greens == 'bright':
        return _greens(colour)
    return tuple(tuple(c * k for c, k in zip(colour, times)) for times in OLIVE)


def _check_look(sheen, lumps, greens):
    sheen, lumps = float(sheen), float(lumps)
    if not 0.0 <= sheen <= 1.0:
        raise ValueError('sheen is 0 (none) to 1 (a strong sheen; 0.8 drew lime felt at dusk), not %r' % (sheen,))
    if not 0.0 <= lumps <= 2.0:
        raise ValueError('lumps is 0 (smooth) to 2 (twice the photograph\'s relief), not %r' % (lumps,))
    if greens not in GREENS:
        raise ValueError('greens is %s, not %r' % (' or '.join(repr(g) for g in GREENS), greens))
    return sheen, lumps, greens


def cushion_material(colour=None, wet=0.4, dry=0.35, sheen=SHEEN, lumps=LUMPS, greens='olive'):
    """The cushions' material: the shelf's photographed moss (forest_leaves_02: its relief, roughness and light and
    dark) under the moss's own greens: young and dark old moss in patches (the cushion's 'moss_age'), brighter where it
    is thick ('moss_depth'), brownish dry tips in places (fewer when wet), a soft sheen that catches the light at a
    grazing angle (`sheen`), the photograph's lumps (`lumps`, its relief), and its thin edges breaking up into the
    stone. `greens` 'olive' (the default: darker, more olive, deeper darks between the tufts, as the garden builder's
    moss at dusk) or 'bright' (the first, brighter greens; with sheen=0.8 and lumps=0.2 the cushions as they first were).
    Made once for the same choices, then shared."""
    colour = tuple(float(c) for c in (CUSHION_COLOUR if colour is None else colour))
    sheen, lumps, greens = _check_look(sheen, lumps, greens)
    darks = 0.24 if greens == 'olive' else 0.38      # (the name greens is taken by the ramp further down)
    wet, dry = float(wet), float(dry)
    key = 'cushions|%.4f,%.4f,%.4f|%.3f|%.3f|%.3f|%.3f|%s' % (*colour, wet, dry, sheen, lumps, greens)
    for found in bpy.data.materials:
        if found.get('moss_key') == key:
            return found
    try:
        photo = store.material('SURFACE • ' + MOSS_SET)
    except KeyError:
        photo = None
    if photo is not None:
        mat = photo.copy()
    else:
        mat = bpy.data.materials.new('moss')
        mat.use_nodes = True
    mat.name = 'moss • cushions'
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    weather = nodes.get('Weather')
    if weather is not None:
        for name, value in (('Wet', wet * 0.6), ('Grime', 0.0), ('Mud height', 0.0), ('Edge wear', 0.0)):
            if name in weather.inputs:
                weather.inputs[name].default_value = value
    young, middle, old = _cushion_greens(colour, greens)
    first_young = _greens(colour)[0]          # the sheen's tint and the light through the moss, as they always were
    if nodes.get('Normal picture') is not None and 'Strength' in nodes['Normal picture'].inputs:
        nodes['Normal picture'].inputs['Strength'].default_value = lumps    # the photograph's lumps (0.2 read as felt)
    depth, age = _attr(nodes, 'moss_depth'), _attr(nodes, 'moss_age')
    coordinates = nodes.new('ShaderNodeTexCoord')
    # the greens: young where the cushion is thick and new, old and dark elsewhere
    younger = _math(nodes, links, 'SUBTRACT', age.outputs['Fac'], _math(nodes, links, 'MULTIPLY', depth.outputs['Fac'], 0.15))
    greens = _ramp(nodes, [(0.15, young), (0.4, middle), (0.7, old)])
    links.new(younger, greens.inputs['Fac'])
    # brownish dry tips: in patches, more at the thin edges, fewer after rain; and where the photograph shows litter
    patches = _node(nodes, 'ShaderNodeTexNoise', Scale=6.0, Detail=4.0, Roughness=0.6)
    links.new(coordinates.outputs['Object'], patches.inputs['Vector'])
    dry_here = _math(nodes, links, 'ADD', _range(nodes, links, patches.outputs['Fac'], 0.56, 0.72),
                     _math(nodes, links, 'MULTIPLY', _range(nodes, links, depth.outputs['Fac'], 0.35, 0.0), 0.4))
    picture = next((n for n in nodes if n.type == 'TEX_IMAGE' and n.image and '_diff' in n.image.name), None)
    if picture is not None:
        parts = nodes.new('ShaderNodeSeparateColor')
        links.new(picture.outputs['Color'], parts.inputs['Color'])
        litter = _range(nodes, links, _math(nodes, links, 'SUBTRACT', parts.outputs['Red'], parts.outputs['Green']), 0.03, 0.12)
        dry_here = _math(nodes, links, 'ADD', dry_here, _math(nodes, links, 'MULTIPLY', litter, 0.35))
    dry_amount = _math(nodes, links, 'MINIMUM', _math(nodes, links, 'MULTIPLY', dry_here, dry * (1.0 - 0.5 * wet)), 1.0)
    browned = nodes.new('ShaderNodeMix')
    browned.data_type = 'RGBA'
    links.new(dry_amount, browned.inputs[0])
    links.new(greens.outputs['Color'], browned.inputs[6])
    browned.inputs[7].default_value = (*DRY, 1.0)
    coloured = browned.outputs[2]
    if picture is not None:
        # the photograph's light and dark: every small cushion and hollow in it, lighter and darker over the greens
        light = nodes.new('ShaderNodeRGBToBW')
        links.new(picture.outputs['Color'], light.inputs['Color'])
        shade = nodes.new('ShaderNodeMapRange')
        shade.inputs['From Min'].default_value = 0.03
        shade.inputs['From Max'].default_value = 0.32
        shade.inputs['To Min'].default_value = darks          # darker down between the tufts, so their tips read (0.38 first)
        shade.inputs['To Max'].default_value = 1.0
        links.new(light.outputs['Val'], shade.inputs['Value'])
        shaded = nodes.new('ShaderNodeMix')
        shaded.data_type = 'RGBA'
        shaded.blend_type = 'MULTIPLY'
        shaded.inputs[0].default_value = 1.0
        links.new(coloured, shaded.inputs[6])
        links.new(shade.outputs['Result'], shaded.inputs[7])
        coloured = shaded.outputs[2]
    links.new(coloured, principled.inputs['Base Color'])
    if weather is not None and weather.outputs.get('Roughness') is not None:
        rough = nodes.new('ShaderNodeMapRange')
        rough.inputs['To Min'].default_value = 0.48
        rough.inputs['To Max'].default_value = 0.85
        links.new(weather.outputs['Roughness'], rough.inputs['Value'])
        links.new(rough.outputs['Result'], principled.inputs['Roughness'])
    else:
        principled.inputs['Roughness'].default_value = 0.7
    for name, value in (('Sheen Weight', sheen), ('Sheen Roughness', 0.45), ('Specular IOR Level', 0.35)):
        if name in principled.inputs:
            principled.inputs[name].default_value = value
    if 'Sheen Tint' in principled.inputs:
        principled.inputs['Sheen Tint'].default_value = (min(1.0, first_young[0] * 3.0), min(1.0, first_young[1] * 3.0), min(1.0, first_young[2] * 3.0), 1.0)
    # a little light through the thin moss, and the thinnest edges breaking up into the stone under them
    through = nodes.new('ShaderNodeBsdfTranslucent')
    through.inputs['Color'].default_value = (*first_young, 1.0)
    glow = nodes.new('ShaderNodeMixShader')
    glow.inputs[0].default_value = 0.12
    links.new(principled.outputs['BSDF'], glow.inputs[1])
    links.new(through.outputs['BSDF'], glow.inputs[2])
    ragged = _node(nodes, 'ShaderNodeTexNoise', Scale=75.0, Detail=6.0, Roughness=0.7)     # frayed, feathery edges
    links.new(coordinates.outputs['Object'], ragged.inputs['Vector'])
    edge = _math(nodes, links, 'ADD', depth.outputs['Fac'], _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'SUBTRACT', ragged.outputs['Fac'], 0.5), 0.5))
    solid = _range(nodes, links, edge, 0.06, 0.13)
    clear = nodes.new('ShaderNodeBsdfTransparent')
    edged = nodes.new('ShaderNodeMixShader')
    links.new(solid, edged.inputs[0])
    links.new(clear.outputs['BSDF'], edged.inputs[1])
    links.new(glow.outputs['Shader'], edged.inputs[2])
    links.new(edged.outputs['Shader'], output.inputs['Surface'])
    mat.diffuse_color = (*middle, 1.0)
    mat['moss_key'] = key
    mat['store_what'] = 'the moss tool\'s cushions: photographed moss (%s) under greens from young to old, dry brown tips, a sheen' % MOSS_SET
    return mat


def pile_material(colour=None, wet=0.4, sheen=None):
    """The tufts' material: each tuft its own green from bright young to dark old, some with brownish dry tips, the
    stalks of the moss's capsules red-brown and the capsules brown-green, a little shine from the rain on the tips, a
    sheen (`sheen`; None: 0.7 of the cushions' SHEEN) and some light through the fronds."""
    colour = tuple(float(c) for c in (CUSHION_COLOUR if colour is None else colour))
    wet = float(wet)
    sheen = 0.7 * SHEEN if sheen is None else float(sheen)
    key = 'pile|%.4f,%.4f,%.4f|%.3f|%.3f' % (*colour, wet, sheen)
    for found in bpy.data.materials:
        if found.get('moss_key') == key:
            return found
    mat = bpy.data.materials.new('moss • pile')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    young, middle, old = _greens(colour)
    info = nodes.new('ShaderNodeObjectInfo')
    tip, stalk = _attr(nodes, 'tip'), _attr(nodes, 'stalk')
    greens = _ramp(nodes, [(0.0, old), (0.4, middle), (1.0, young)])
    links.new(info.outputs['Random'], greens.inputs['Fac'])
    second = _math(nodes, links, 'FRACT', _math(nodes, links, 'MULTIPLY', info.outputs['Random'], 13.7))
    dry_tufts = _range(nodes, links, second, 0.62, 0.7)                     # about a third of the tufts dry at the tips
    dry_tips = _math(nodes, links, 'MULTIPLY', _range(nodes, links, tip.outputs['Fac'], 0.45, 0.95), dry_tufts)
    browned = nodes.new('ShaderNodeMix')
    browned.data_type = 'RGBA'
    links.new(_math(nodes, links, 'MULTIPLY', dry_tips, 1.0 - 0.4 * wet), browned.inputs[0])
    links.new(greens.outputs['Color'], browned.inputs[6])
    browned.inputs[7].default_value = (*DRY, 1.0)
    bright_tips = nodes.new('ShaderNodeMix')                                  # young tips catch the light
    bright_tips.data_type = 'RGBA'
    links.new(_math(nodes, links, 'MULTIPLY', _range(nodes, links, tip.outputs['Fac'], 0.55, 1.0),
                    _math(nodes, links, 'SUBTRACT', 1.0, dry_tufts)), bright_tips.inputs[0])
    links.new(browned.outputs[2], bright_tips.inputs[6])
    bright_tips.inputs[7].default_value = (min(1.0, young[0] * 1.35), min(1.0, young[1] * 1.35), min(1.0, young[2] * 1.2), 1.0)
    browned = bright_tips
    darker_root = nodes.new('ShaderNodeMix')                                  # dark down in the pile
    darker_root.data_type = 'RGBA'
    darker_root.blend_type = 'MULTIPLY'
    links.new(_range(nodes, links, tip.outputs['Fac'], 0.35, 0.0), darker_root.inputs[0])
    links.new(browned.outputs[2], darker_root.inputs[6])
    darker_root.inputs[7].default_value = (0.35, 0.35, 0.35, 1.0)
    stalks = nodes.new('ShaderNodeMix')
    stalks.data_type = 'RGBA'
    links.new(_range(nodes, links, stalk.outputs['Fac'], 0.2, 0.3), stalks.inputs[0])
    links.new(darker_root.outputs[2], stalks.inputs[6])
    capsule = nodes.new('ShaderNodeMix')
    capsule.data_type = 'RGBA'
    links.new(_range(nodes, links, stalk.outputs['Fac'], 0.8, 0.7), capsule.inputs[0])
    capsule.inputs[6].default_value = (0.13, 0.04, 0.014, 1.0)                # the stalk, red-brown
    capsule.inputs[7].default_value = (0.11, 0.085, 0.03, 1.0)                # the capsule, brown-green
    links.new(capsule.outputs[2], stalks.inputs[7])
    links.new(stalks.outputs[2], principled.inputs['Base Color'])
    shine = nodes.new('ShaderNodeMapRange')                                   # rain on the tips shines a little
    shine.inputs['To Min'].default_value = 0.62
    shine.inputs['To Max'].default_value = 0.62 - 0.3 * wet
    links.new(tip.outputs['Fac'], shine.inputs['Value'])
    links.new(shine.outputs['Result'], principled.inputs['Roughness'])
    for name, value in (('Sheen Weight', sheen), ('Sheen Roughness', 0.4), ('Specular IOR Level', 0.4)):
        if name in principled.inputs:
            principled.inputs[name].default_value = value
    through = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(stalks.outputs[2], through.inputs['Color'])
    glow = nodes.new('ShaderNodeMixShader')
    glow.inputs[0].default_value = 0.22
    links.new(principled.outputs['BSDF'], glow.inputs[1])
    links.new(through.outputs['BSDF'], glow.inputs[2])
    links.new(glow.outputs['Shader'], output.inputs['Surface'])
    mat.diffuse_color = (*middle, 1.0)
    mat['moss_key'] = key
    mat['store_what'] = "the moss tool's pile: tufts from young to old green, dry tips, red-brown capsule stalks"
    return mat


def _tuft_mesh(index):
    """One tuft about 1 cm high: leafy shoots rising and spreading from one root (a star of narrow leaves, as the hair
    cap moss of Japanese gardens), each shoot a cross of two narrow strips so it reads from every side; the last kind is
    a few short shoots with two capsules on long thin stalks. Points carry 'tip' (0 at the root, 1 at the tip) and
    'stalk' (1 on a stalk, 0.75 on a capsule)."""
    import random
    pick = random.Random(911 + 37 * index)
    verts, faces, tips, stalks = [], [], [], []

    def strip(points, widths, across, mark):
        base = len(verts)
        for (x, y, z), w, t in zip(points, widths, [k / (len(points) - 1) for k in range(len(points))]):
            verts.append((x + across[0] * w, y + across[1] * w, z + across[2] * w))
            verts.append((x - across[0] * w, y - across[1] * w, z - across[2] * w))
            tips.extend([t, t])
            stalks.extend([mark, mark])
        for k in range(len(points) - 1):
            a = base + 2 * k
            faces.append((a, a + 1, a + 3, a + 2))

    def shoot(turn, lean, length, width, curl, mark=0.0):
        points, widths = [], []
        for k in range(5):
            t = k / 4.0
            out = length * (math.sin(lean) * t + curl * t * t)
            up = length * math.cos(lean) * t * (1.0 - 0.35 * curl * t)
            points.append((out * math.cos(turn), out * math.sin(turn), up))
            widths.append(width * (0.35 + 2.2 * t) * (1.0 - t) + 0.00005)
        flat = (-math.sin(turn), math.cos(turn), 0.0)
        strip(points, widths, flat, mark)
        tilt = (math.cos(turn) * math.cos(lean), math.sin(turn) * math.cos(lean), -math.sin(lean))
        strip(points, widths, tilt, mark)

    kinds = [(7, 0.55, 0.010, 0.0011, 0.15), (10, 0.35, 0.007, 0.0009, 0.1), (5, 0.8, 0.012, 0.0012, 0.3),
             (12, 0.45, 0.005, 0.0008, 0.05), (6, 0.65, 0.009, 0.001, 0.2)]
    if index < len(kinds):
        count, lean, length, width, curl = kinds[index]
        for k in range(count):
            shoot(2.0 * math.pi * (k + pick.uniform(-0.3, 0.3)) / count, lean * pick.uniform(0.6, 1.3),
                  length * pick.uniform(0.7, 1.2), width, curl)
        if index != 3:
            shoot(pick.uniform(0, 6.28), 0.1, length * 1.1, width, 0.0)       # one upright in the middle
    else:
        for k in range(5):                                                    # a few short shoots
            shoot(2.0 * math.pi * k / 5 + pick.uniform(-0.3, 0.3), 0.6, 0.005, 0.0008, 0.1)
        for k in range(2):                                                    # the capsules on their stalks
            turn, height = pick.uniform(0, 6.28), pick.uniform(0.014, 0.02)
            lean = pick.uniform(0.05, 0.25)
            top = (height * math.sin(lean) * math.cos(turn), height * math.sin(lean) * math.sin(turn), height * math.cos(lean))
            points = [(top[0] * t, top[1] * t, top[2] * t) for t in (0.0, 0.35, 0.7, 1.0)]
            strip(points, [0.00022] * 4, (-math.sin(turn), math.cos(turn), 0.0), 1.0)
            strip(points, [0.00022] * 4, (math.cos(turn), math.sin(turn), 0.0), 1.0)
            base = len(verts)                                                 # a small nodding capsule: six sides
            drop = (math.cos(turn) * 0.6, math.sin(turn) * 0.6, -0.8)
            for k2 in range(6):
                a = 2.0 * math.pi * k2 / 6
                verts.append((top[0] + 0.0009 * math.cos(a) + drop[0] * 0.0012, top[1] + 0.0009 * math.sin(a) + drop[1] * 0.0012,
                              top[2] + drop[2] * 0.0012 + 0.0004 * math.sin(a)))
                tips.append(1.0)
                stalks.append(0.75)
            verts.append(top)
            verts.append((top[0] + drop[0] * 0.0032, top[1] + drop[1] * 0.0032, top[2] + drop[2] * 0.0032))
            tips.extend([1.0, 1.0])
            stalks.extend([0.75, 0.75])
            for k2 in range(6):
                faces.append((base + 6, base + k2, base + (k2 + 1) % 6))
                faces.append((base + 7, base + (k2 + 1) % 6, base + k2))
    mesh = bpy.data.meshes.new('moss tuft %d' % index)
    mesh.from_pydata(verts, [], faces)
    for name, values in (('tip', tips), ('stalk', stalks)):
        layer = mesh.attributes.new(name, 'FLOAT', 'POINT')
        layer.data.foreach_set('value', values)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.update()
    return mesh


def tufts(material=None):
    """The collection (not in the scene) of the pile's tuft shapes, made once and shared."""
    material = material or pile_material()
    name = 'moss • tufts • ' + material.name
    found = bpy.data.collections.get(name)
    if found is not None and len(found.objects) == 6:
        return found
    shapes = bpy.data.collections.new(name)
    for index in range(6):
        mesh = _tuft_mesh(index)
        mesh.materials.append(material)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.track_axis = 'POS_Z'                 # the particle system stands the tuft's up (Z) on the cushion's normal
        obj.up_axis = 'Y'
        shapes.objects.link(obj)
    return shapes


def _smoothstep(low, high, value):
    t = numpy.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _noise3(co, size, seed):
    """Smooth noise in space for many points (lumps about `size` metres), about -0.5 .. 0.5."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    return (_noise.wander(x, y, size, seed, layers=3) + _noise.wander(y + 3.1, z, size, seed + 1, layers=3)
            + _noise.wander(z - 1.7, x, size, seed + 2, layers=3)) / 3.0


def _smooth(values, edges, n, passes, keep=0.5):
    count = numpy.maximum(numpy.bincount(edges.ravel(), minlength=n), 1).astype(numpy.float64)
    for _ in range(passes):
        around = (numpy.bincount(edges[:, 0], weights=values[edges[:, 1]], minlength=n)
                  + numpy.bincount(edges[:, 1], weights=values[edges[:, 0]], minlength=n)) / count
        values = values * keep + around * (1.0 - keep)
    return values


def _hollows(co, normals, edges, ridges=False):
    """How deep in a crack or hollow each point lies, 0 to 1: its neighbours standing above its own surface. With
    ridges, also how sharp a ridge or edge it lies on (its neighbours falling away below it), 0 to 1."""
    n = len(co)
    count = numpy.maximum(numpy.bincount(edges.ravel(), minlength=n), 1).astype(numpy.float64)
    mean = numpy.stack([numpy.bincount(edges[:, 0], weights=co[edges[:, 1], k], minlength=n)
                        + numpy.bincount(edges[:, 1], weights=co[edges[:, 0], k], minlength=n) for k in range(3)], 1) / count[:, None]
    length = float(numpy.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1).mean()) + 1e-9
    deep = ((mean - co) * normals).sum(1) / length
    deep = _smooth(deep, edges, n, 4)
    spread = deep.std() + 1e-9
    hollow = _smoothstep(0.6, 2.2, deep / spread)
    if ridges:
        return hollow, _smoothstep(0.3, 1.8, -deep / spread)
    return hollow


def _field(co, normals, edges, up, amount, facing, hollows, foot, height, seed, patch):
    """Where the moss grows on a mesh, 0 to 1 at each point: on faces that look up, just over their rims, in its
    cracks and hollows and up its damp foot, in patches; spread a little over the mesh so the cushions creep over the
    rims and soften at their edges. Returns (where, hollow)."""
    n = len(co)
    facing_up = normals @ up
    hollow, ridge = _hollows(co, normals, edges, ridges=True)
    on_top = _smoothstep(facing[0], facing[1], facing_up)
    over_rim = _smoothstep(facing[0] - 0.3, facing[0], facing_up) * 0.3
    at_foot = _smoothstep(foot, 0.0, height) * 0.85 if foot > 0 else numpy.zeros(n)
    # patches by rank, so the amount says what share of the places moss could grow it covers, whatever the noise
    # gives: 1 a little over half, 0.5 about a quarter, 1.5 nearly all
    # the bare places: the sharp ridges and edges first (moss keeps off them, where it dries and is rubbed), then
    # big wandering gaps, few small round ones
    wander = _noise3(co, patch * 1.2, seed) + 0.3 * _noise3(co, patch * 0.45, seed + 7) - 0.3 * ridge + 0.15 * hollow
    could = numpy.maximum.reduce([on_top, over_rim, hollow * hollows, at_foot])
    rank = numpy.zeros(n)
    able = numpy.flatnonzero(could > 0.15)                 # ranked among the places moss could grow only
    if len(able):
        rank[able[numpy.argsort(wander[able])]] = numpy.arange(len(able)) / max(len(able) - 1, 1)
    edge = float(numpy.clip(1.0 - 0.55 * amount, 0.08, 0.97))
    patches = _smoothstep(edge - 0.07, edge + 0.07, rank)
    where = could * patches
    where = _smooth(where, edges, n, 3)
    return numpy.clip(where * 1.15, 0.0, 1.0), hollow


SHELL = 0.16          # the least 'where' a face needs to carry a cushion


def _shell(bm, where, hollow, up, thickness, base, seed, material_index, droop, group, into=None):
    """The cushions as faces over the bmesh's faces whose points all have moss: each point lifted along its normal by
    the cushion's depth (0 at the edge, thick in the middle and in the hollows, lumpy), and on the sides let down a
    little, so a cushion overhangs a rim. The faces go into `into` (a bmesh; None: the same bmesh) with the material
    `material_index`; their points carry 'moss_depth', 'moss_age' and the weight `group` (the pile's density).
    Returns (the cushions' area in square metres, their faces)."""
    target = bm if into is None else into
    bm.verts.ensure_lookup_table()
    co = numpy.array([v.co[:] for v in bm.verts])
    normals = numpy.array([v.normal[:] for v in bm.verts])
    depth = _smoothstep(SHELL, 0.8, where) ** 0.7
    depth = numpy.clip(depth + 0.35 * hollow * (where > SHELL), 0.0, 1.0)
    lump = 0.7 + 0.6 * numpy.clip(0.5 + 1.3 * _noise3(co, 0.05, seed + 11), 0.0, 1.0)
    age = numpy.clip(0.5 + 1.8 * _noise3(co, 0.09, seed + 23), 0.0, 1.0)
    side = 1.0 - numpy.clip(normals @ up, 0.0, 1.0)
    chosen = [f for f in bm.faces if all(where[v.index] > SHELL for v in f.verts)]
    # how far in from the cushion's edge each point lies, in rings of faces: a cushion is a soft rounded mound, nothing
    # at its edge, rising over about 14 cm to its full depth, and smoothed so it never steps
    edge_uses, around = {}, {}
    for face in chosen:
        ring = [v.index for v in face.verts]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            pair = (a, b) if a < b else (b, a)
            edge_uses[pair] = edge_uses.get(pair, 0) + 1
            around.setdefault(a, set()).add(b)
            around.setdefault(b, set()).add(a)
    length = float(numpy.mean([numpy.linalg.norm(co[a] - co[b]) for a, b in list(edge_uses)[:2000]])) if edge_uses else 0.01
    rings = int(min(24, max(3, round(0.14 / max(length, 1e-4)))))
    steps = {}
    frontier = sorted({a for pair, uses in edge_uses.items() if uses == 1 for a in pair})
    rim = set(frontier)
    for a in frontier:
        steps[a] = 0
    for step in range(1, rings + 1):
        following = []
        for a in frontier:
            for b in around.get(a, ()):
                if b not in steps:
                    steps[b] = step
                    following.append(b)
        frontier = following
    rise = numpy.ones(len(co))
    for a, step in steps.items():
        rise[a] = step / float(rings)
    rise = rise * (2.0 - rise)                                   # a mound: rising fast from its edge, rounded on top
    lump = 0.78 + 0.44 * numpy.clip(0.5 + 1.3 * _noise3(co, 0.03, seed + 11), 0.0, 1.0)   # small rounded mounds in it
    depth = depth * rise * lump
    inside = [a for a in around if a not in rim]
    for _ in range(4):                                           # smoothed over the cushion, its edge kept at nothing
        depth_before = depth.copy()
        for a in inside:
            near = around[a]
            depth[a] = 0.5 * depth_before[a] + 0.5 * sum(depth_before[b] for b in near) / len(near)
    for a in rim:
        depth[a] = 0.0
    depth = numpy.clip(depth, 0.0, 1.0)
    lump = numpy.ones(len(co))
    lift = base + thickness * depth
    places = co + normals * lift[:, None] - numpy.outer(droop * thickness * depth * side * lump, up)
    depth_layer = target.verts.layers.float.get('moss_depth') or target.verts.layers.float.new('moss_depth')
    age_layer = target.verts.layers.float.get('moss_age') or target.verts.layers.float.new('moss_age')
    weights = target.verts.layers.deform.verify()
    made, new_faces, area = {}, [], 0.0
    for face in chosen:
        corners = []
        for v in face.verts:
            new = made.get(v.index)
            if new is None:
                new = target.verts.new(places[v.index])
                new[depth_layer] = float(depth[v.index])
                new[age_layer] = float(age[v.index])
                new[weights][group] = float(max(0.03, depth[v.index] ** 0.6))
                made[v.index] = new
            corners.append(new)
        try:
            new_face = target.faces.new(corners)
        except ValueError:
            continue
        new_face.material_index = material_index
        new_face.smooth = True
        new_faces.append(new_face)
        area += face.calc_area()
    return area, new_faces


def _check(amount, thickness, pile, facing):
    amount, thickness, pile = float(amount), float(thickness), float(pile)
    if not 0.0 <= amount <= 1.5:
        raise ValueError('amount is 0 (none) to 1.5 (very thick), not %r' % (amount,))
    if not 0.002 <= thickness <= 0.15:
        raise ValueError('thickness is 0.002 to 0.15 m (a cushion 3 cm deep: 0.03), not %r' % (thickness,))
    if not 0.0 <= pile <= 3.0:
        raise ValueError('pile is 0 (no tufts) to 3 (three times as many), not %r' % (pile,))
    low, high = float(facing[0]), float(facing[1])
    if not -1.0 <= low < high <= 1.0:
        raise ValueError('facing is two numbers from -1 to 1, the first smaller, not %r' % (facing,))
    return amount, thickness, pile, (low, high)


PILE_DENSITY = 16000.0    # tufts per square metre of cushion at pile=1


def on_mesh(mesh, amount=0.8, thickness=0.03, facing=(0.3, 0.85), hollows=0.6, foot=0.0, colour=None, wet=0.4,
            seed=0, base=0.002, patch=0.22, droop=0.5, up=(0.0, 0.0, 1.0), sheen=SHEEN, lumps=LUMPS, greens='olive'):
    """Real moss cushions added to a mesh in its own coordinates (its up `up`, its soil line at height 0 for `foot`),
    as faces of its own with the cushions' material as a new material slot; the mesh's points also get 'moss_film'
    (where the stone under and round the cushions is green), 'moss_hollow' and 'moss_cushioned' for the stone material
    (moss.add follows them). Its points' weights for the pile go in deform group 0: give the object that uses the
    mesh a vertex group (pile() does). Returns the cushions' area in square metres."""
    amount, thickness, _, facing = _check(amount, thickness, 1.0, facing)
    sheen, lumps, greens = _check_look(sheen, lumps, greens)
    up = numpy.array(up, dtype=numpy.float64)
    up /= numpy.linalg.norm(up)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    co = numpy.array([v.co[:] for v in bm.verts])
    normals = numpy.array([v.normal[:] for v in bm.verts])
    edges = numpy.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges], dtype=numpy.int64).reshape(-1, 2)
    where, hollow = _field(co, normals, edges, up, amount, facing, float(hollows), float(foot), co @ up, int(seed), float(patch))
    film = bm.verts.layers.float.new('moss_film')
    deep = bm.verts.layers.float.new('moss_hollow')
    cushioned = bm.verts.layers.float.new('moss_cushioned')
    for v in bm.verts:
        v[film] = float(min(1.0, where[v.index] * 1.4))
        v[deep] = float(hollow[v.index])
        v[cushioned] = 1.0
    if not len(mesh.materials):
        mesh.materials.append(None)                  # the stone keeps the first slot (empty), the cushions get their own
    index = len(mesh.materials)
    area, faces = _shell(bm, where, hollow, up, thickness, float(base), int(seed), index, float(droop), 0)
    for face in faces:
        for v in face.verts:
            v[film] = 1.0
            v[cushioned] = 1.0
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(cushion_material(colour, wet, sheen=sheen, lumps=lumps, greens=greens))
    mesh['moss_area'] = area
    mesh['moss_faces'] = len(faces)
    return area


def pile(obj, area=None, amount=1.0, length=0.015, colour=None, wet=0.4, seed=0, sheen=None):
    """The pile on an object's cushions: tiny tufts and fronds, copies of six shapes, laid by Blender's particle system
    (hair, each copy standing on the cushion's surface) wherever its vertex group 'moss pile' weighs, thickest where the
    cushion is deep. `area`: the cushions' area (None: the mesh's 'moss_area'); amount: 1 about 16,000 tufts a square
    metre. Returns the particle system, or None when there is nothing to lay them on."""
    area = float(obj.data.get('moss_area', 0.0) if area is None else area)
    count = int(area * PILE_DENSITY * float(amount))
    if count < 1:
        return None
    if obj.vertex_groups.get('moss pile') is None:
        obj.vertex_groups.new(name='moss pile')
    modifier = obj.modifiers.new('moss pile', 'PARTICLE_SYSTEM')
    system = modifier.particle_system
    system.vertex_group_density = 'moss pile'
    system.seed = int(seed) + 3
    settings = system.settings
    settings.name = 'moss pile • %s' % obj.name
    settings.type = 'HAIR'
    settings.use_advanced_hair = True
    settings.count = count
    settings.hair_length = float(length)
    settings.emit_from = 'FACE'
    settings.distribution = 'RAND'
    settings.use_emit_random = True
    settings.use_even_distribution = True
    settings.render_type = 'COLLECTION'
    settings.instance_collection = tufts(pile_material(colour, wet, sheen))
    settings.use_collection_pick_random = True
    settings.particle_size = float(length) / 0.01
    settings.size_random = 0.55
    settings.use_rotations = True
    settings.rotation_mode = 'NOR'
    settings.rotation_factor_random = 0.2
    settings.phase_factor_random = 2.0
    settings.use_rotation_instance = False
    settings.use_scale_instance = True
    settings.display_method = 'RENDER'
    settings.display_percentage = 10
    return system


def _close(mesh, step, report=None, up=(0.0, 0.0, 1.0)):
    """Make an open shape closed for the voxel remesh, which needs one (on a carved basin open underneath it grew 121
    faces and no moss, the garden builder found): each hole in it (a loop of open edges) filled with a face, as a solid
    stone is; a shape that is only a thin sheet (filled, it holds no room inside), or one with a wide opening on top (a
    trough or a pot made as a thin shell: a lid there would carry moss over the opening), is given a thickness instead.
    Changes `mesh`; a closed shape is left as it is. Writes into `report` how many holes were filled or 'thickened'."""
    from mathutils import Vector
    bm = bmesh.new()
    bm.from_mesh(mesh)
    open_edges = [e for e in bm.edges if e.is_boundary]
    if not open_edges:
        bm.free()
        return None
    filled = bmesh.ops.holes_fill(bm, edges=open_edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    holes = len(filled['faces'])
    up = Vector(up).normalized()
    lids = [f for f in filled['faces'] if f.normal.dot(up) > 0.5 and f.calc_area() > (5.0 * step) ** 2]
    volume = abs(bm.calc_volume(signed=False)) if not [e for e in bm.edges if e.is_boundary] else 0.0
    if volume > 20.0 * step ** 3 and not lids:        # it holds room inside: a solid with its holes filled
        bm.to_mesh(mesh)
        bm.free()
        if report is not None:
            report['holes filled'] = holes
        return 'filled'
    bm.free()                                         # a thin sheet: give it a thickness instead
    if report is not None:
        report['thickened'] = True
    return 'sheet'


def _even_skin(obj, step, report=None, up=(0.0, 0.0, 1.0)):
    """The object's mesh as it is drawn (modifiers applied), in its own coordinates, remade as even small faces about
    `step` metres across (Blender's voxel remesh), as a bmesh. An open shape is closed first (_close; `up`, the
    object's up in its own coordinates, tells an opening on top from one underneath)."""
    layer = bpy.context.view_layer
    depsgraph = bpy.context.evaluated_depsgraph_get()
    drawn = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    closing = _close(drawn, step, report, up)
    holder = bpy.data.objects.new('moss • skin', drawn)
    workshop = bpy.data.scenes.new('moss • making')
    workshop.collection.objects.link(holder)
    if closing == 'sheet':                            # a thin sheet: thickened downwards, so its top stays where it is
        thick = holder.modifiers.new('thickness', 'SOLIDIFY')
        thick.thickness = 3.0 * step
        thick.offset = -1.0
        thick.use_even_offset = True
    remesh = holder.modifiers.new('even skin', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = step
    remesh.adaptivity = 0.0
    view = workshop.view_layers[0]
    view.update()
    with bpy.context.temp_override(scene=workshop, view_layer=view):
        evaluated = bpy.context.evaluated_depsgraph_get()
        remade = bpy.data.meshes.new_from_object(holder.evaluated_get(evaluated))
    bpy.data.objects.remove(holder)
    bpy.data.meshes.remove(drawn)
    bpy.data.scenes.remove(workshop)
    bm = bmesh.new()
    bm.from_mesh(remade)
    bpy.data.meshes.remove(remade)
    del layer
    return bm


def grow(target, amount=0.8, thickness=0.03, facing=(0.3, 0.85), hollows=0.6, foot=0.15, pile_amount=1.0,
         pile_length=0.015, colour=None, wet=0.4, seed=0, step=0.012, patch=0.22, droop=0.5, collection=None,
         sheen=SHEEN, lumps=LUMPS, greens='olive'):
    """Real moss on a stone object you give (a basin, a lantern's foot, a wall top, a rock of your own): cushions with
    thickness on its upward faces, in its hollows and up its foot (`foot` metres above the ground under it: the
    object's 'pp_ground', or its lowest point), with the pile of tufts on them, as a new object 'moss on <name>'
    parented to yours (move yours and the moss goes with it). Your object is not changed. Returns the moss object
    (its 'moss_area' says the cushions' area in square metres), or None if no moss grew on it. An open shape (a basin
    carved open underneath, a lantern's hollow foot) is closed for the growing, its holes filled as a solid stone's
    are (a thin sheet, or a shell with a wide opening on top, is thickened inwards); your object stays open. `sheen`,
    `lumps` and `greens` as cushion_material's."""
    if target is None or target.type != 'MESH':
        raise ValueError('grow needs a mesh object to grow moss on, not %r' % (target,))
    amount, thickness, pile_amount, facing = _check(amount, thickness, pile_amount, facing)
    sheen, lumps, greens = _check_look(sheen, lumps, greens)
    scale = sum(target.matrix_world.to_scale()) / 3.0
    closing = {}
    up_here = (target.matrix_world.to_3x3().inverted() @ __import__('mathutils').Vector((0.0, 0.0, 1.0))).normalized()
    bm = _even_skin(target, float(step) / max(scale, 1e-6), closing, tuple(up_here))
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    if not bm.verts:
        bm.free()
        return None
    rotation = target.matrix_world.to_3x3()
    up_local = rotation.inverted() @ __import__('mathutils').Vector((0.0, 0.0, 1.0))
    up = numpy.array(up_local.normalized()[:])
    co = numpy.array([v.co[:] for v in bm.verts])
    normals = numpy.array([v.normal[:] for v in bm.verts])
    edges = numpy.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges], dtype=numpy.int64).reshape(-1, 2)
    world = numpy.array([(target.matrix_world @ v.co)[:] for v in bm.verts])
    ground = float(target['pp_ground']) if 'pp_ground' in target.keys() else float(world[:, 2].min())
    where, hollow = _field(co * scale, normals, edges, up, amount, facing, float(hollows), float(foot), world[:, 2] - ground,
                           int(seed), float(patch))
    out = bmesh.new()
    area, faces = _shell(bm, where, hollow, up, thickness / scale, 0.002 / scale, int(seed), 0, float(droop), 0, into=out)
    bm.free()
    if not faces:
        out.free()
        return None
    mesh = bpy.data.meshes.new('moss on %s' % target.name)
    out.to_mesh(mesh)
    out.free()
    mesh.materials.append(cushion_material(colour, wet, sheen=sheen, lumps=lumps, greens=greens))
    mesh['moss_area'] = area * scale * scale
    mesh['moss_faces'] = len(faces)
    if closing:
        mesh['moss_closed'] = 'thickened' if closing.get('thickened') else 'holes filled: %d' % closing.get('holes filled', 0)
    obj = bpy.data.objects.new('moss on %s' % target.name, mesh)
    if collection is None:
        collection = target.users_collection[0] if target.users_collection else bpy.context.scene.collection
    collection.objects.link(obj)
    obj.parent = target
    obj.matrix_parent_inverse.identity()
    obj.vertex_groups.new(name='moss pile')
    obj['pp_ground'] = ground
    if pile_amount > 0:
        pile(obj, area * scale * scale, pile_amount, pile_length, colour, wet, seed, sheen=0.7 * sheen)
    return obj


def _spots_of(spots):
    """(x, y, foot radius) for each rock: from what rocks.scatter or rocks.at_spots gave back, a list of objects, or
    (x, y, size) / (x, y, z, size) tuples. A rock's foot reaches about 0.42 of its size from its middle."""
    from mathutils import Vector
    out = []
    if isinstance(spots, dict) and 'spots' in spots:
        at_spots = 'lowered' in spots                 # at_spots: (x, y, z, size, top); scatter: (x, y, z, from, to)
        for spot in spots['spots']:
            size = spot[3] if at_spots else (spot[3] + spot[4]) / 2.0
            out.append((float(spot[0]), float(spot[1]), 0.42 * float(size)))
        return out
    for spot in spots:
        if hasattr(spot, 'matrix_world'):
            box = [spot.matrix_world @ Vector(c) for c in spot.bound_box]
            size = max(max(c.x for c in box) - min(c.x for c in box), max(c.y for c in box) - min(c.y for c in box))
            out.append((float(spot.matrix_world.translation.x), float(spot.matrix_world.translation.y), 0.42 * size))
        else:
            spot = [float(c) for c in spot]
            out.append((spot[0], spot[1], 0.42 * (spot[3] if len(spot) >= 4 else spot[2])))
    return out


FEET_COLOUR = (0.065, 0.1, 0.02)        # the moss on the soil: a little darker and older than on the rocks' tops


def _areas(keep_out):
    """keep_out as a list of ('rect', (x0, y0, x1, y1)) and ('poly', points): a rectangle, a polygon [(x, y), ...] or a
    list of them."""
    if keep_out is None:
        return []
    items = list(keep_out)
    if not items:
        return []
    if len(items) == 4 and all(isinstance(v, (int, float)) for v in items):
        return [('rect', tuple(float(v) for v in items))]
    first = items[0]
    if hasattr(first, '__len__') and len(first) == 2 and all(isinstance(v, (int, float)) for v in first):
        if len(items) < 3:
            raise ValueError('a polygon to keep out of needs at least three corners, not %r' % (keep_out,))
        return [('poly', numpy.array([(float(x), float(y)) for x, y in items]))]
    out = []
    for item in items:
        if not hasattr(item, '__len__'):
            raise ValueError('keep_out is a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or a list of them, not %r' % (keep_out,))
        out.extend(_areas(item))
    return out


def _inside(polygon, xy):
    """Which of the points xy (n, 2) lie inside the polygon (even-odd rule)."""
    x, y = xy[:, 0], xy[:, 1]
    inside = numpy.zeros(len(xy), dtype=bool)
    px, py = polygon[:, 0], polygon[:, 1]
    qx, qy = numpy.roll(px, -1), numpy.roll(py, -1)
    for ax, ay, bx, by in zip(px, py, qx, qy):
        crosses = (ay > y) != (by > y)
        at = ax + (y - ay) * (bx - ax) / ((by - ay) if by != ay else 1e-12)
        inside ^= crosses & (x < at)
    return inside


def _allowed(keep, keep_out):
    """A test of many places at once, (n, 2) points -> True where the moss, turf and ferns may go: outside every area
    of keep_out, and where keep(x, y) says True. None when neither is given."""
    areas = _areas(keep_out)
    if keep is None and not areas:
        return None
    if keep is not None and not callable(keep):
        raise ValueError('keep is a test of one place, keep(x, y) giving True or False, not %r' % (keep,))

    def allowed(xy):
        xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
        ok = numpy.ones(len(xy), dtype=bool)
        for kind, area in areas:
            if kind == 'rect':
                x0, x1 = sorted((area[0], area[2]))
                y0, y1 = sorted((area[1], area[3]))
                ok &= ~((xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1))
            else:
                ok &= ~_inside(area, xy)
        if keep is not None:
            for i in numpy.flatnonzero(ok):
                ok[i] = bool(keep(float(xy[i, 0]), float(xy[i, 1])))
        return ok
    return allowed


def feet(ground, spots, reach=0.22, amount=0.7, turf=0.5, ferns=0, pile_amount=1.0, colour=None, wet=0.4, seed=0,
         collection=None, keep=None, keep_out=None, sheen=None):
    """Moss and small plants where rocks meet the soil of a ground you give: moss spilling from each rock's foot onto
    the soil as tufts straight on it (thickest against the rock, in patches, thinning out to nothing `reach` metres out;
    laid by the particle system on a hidden copy of the ground's faces there); grass
    tufts round the feet (the store's grass tool, its turf); and `ferns` small ferns (the store's fern part) at the
    feet of the biggest rocks. `spots`: what rocks.scatter or rocks.at_spots gave back, the objects rocks.place gave
    back, or (x, y, size) places. The ground is not changed. Returns {'moss': the carpet object or None, 'turf': what
    grass.grow gave back or None, 'ferns': the ferns' roots, 'ferns_left_out': how many asked for found no room}.
    `keep` (a test of one place, keep(x, y) giving True or False) and `keep_out` (an area to stay out of: a rectangle
    (x0, y0, x1, y1), a polygon [(x, y), ...] or a list of them) keep the moss, the turf and the ferns out of places
    (a path, a step, the water): a fern then goes to another side of its rock where its crown and its fronds' reach
    keep out, or a smaller one, or to the next biggest rock. Without them, everything is laid as before. `sheen`: the
    tufts' sheen (None: as the pile's)."""
    if ground is None or ground.type != 'MESH':
        raise ValueError('feet needs the ground: a mesh object with faces')
    places = _spots_of(spots)
    if not places:
        raise ValueError('feet needs the rocks: what rocks.scatter or at_spots gave back, objects, or (x, y, size) places')
    reach = float(reach)
    if not 0.02 <= reach <= 2.0:
        raise ValueError('reach is 0.02 to 2 m, not %r' % (reach,))
    allowed = _allowed(keep, keep_out)
    centres = numpy.array([(x, y) for x, y, _ in places])
    radii = numpy.array([r for _, _, r in places])

    def nearness(xy):
        d = numpy.linalg.norm(xy[:, None, :] - centres[None, :, :], axis=2) - radii[None, :]
        return numpy.clip(1.0 - _smoothstep(-0.05, reach, d), 0.0, 1.0).max(1)

    matrix = ground.matrix_world
    mesh = ground.data
    # the ground's faces near the rocks (found all at once), copied and made finer: the moss grows on them as tufts
    # straight on the soil, thick against each rock's foot, in patches, thinning out to nothing (no sheet of its own, so
    # no cut edge)
    centres_of = numpy.zeros(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get('center', centres_of)
    centres_of = centres_of.reshape(-1, 3) @ numpy.array(matrix.to_3x3()).T + numpy.array(matrix.translation)
    gap = numpy.linalg.norm(centres_of[:, None, :2] - centres[None, :, :], axis=2) - radii[None, :]
    keep = numpy.flatnonzero(gap.min(1) < reach + 0.15)
    bm = bmesh.new()
    picked = {}
    for k in keep:
        polygon = mesh.polygons[int(k)]
        verts = []
        for i in polygon.vertices:
            if i not in picked:
                picked[i] = bm.verts.new(matrix @ mesh.vertices[i].co)
            verts.append(picked[i])
        try:
            bm.faces.new(verts)
        except ValueError:
            pass
    result = {'moss': None, 'turf': None, 'ferns': []}
    if bm.faces:
        longest = max(e.calc_length() for e in bm.edges)
        cuts = int(min(6, max(0, math.ceil(longest / 0.03) - 1)))
        if cuts:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
        bm.verts.ensure_lookup_table()
        co = numpy.array([v.co[:] for v in bm.verts])
        near = nearness(co[:, :2])
        patches = _smoothstep(0.62 - 0.25 * min(float(amount), 1.5), 0.82 - 0.25 * min(float(amount), 1.5),
                              numpy.clip(0.5 + 1.6 * _noise3(co, 0.06, int(seed) + 41), 0.0, 1.0))
        where = numpy.clip(near * near * (0.25 + 0.75 * patches) * 1.2, 0.0, 1.0)
        if allowed is not None:
            where = where * allowed(co[:, :2])
        weights = bm.verts.layers.deform.verify()
        for v in bm.verts:
            v[weights][0] = float(where[v.index])
        area = sum(f.calc_area() * float(numpy.mean([where[v.index] for v in f.verts])) for f in bm.faces)
        for v in bm.verts:                                      # just over the soil, so every tuft's root is on it
            v.co.z += 0.002
        soil = bpy.data.meshes.new('moss at the feet')
        bm.to_mesh(soil)
        soil['moss_area'] = area
        obj = bpy.data.objects.new('moss at the feet', soil)
        (collection or (ground.users_collection[0] if ground.users_collection else bpy.context.scene.collection)).objects.link(obj)
        obj.vertex_groups.new(name='moss pile')
        obj.show_instancer_for_render = False                  # only its tufts are drawn
        obj.show_instancer_for_viewport = False
        if pile_amount > 0 and area > 0:
            pile(obj, area, pile_amount * 3.0, 0.016, colour or FEET_COLOUR, wet, seed, sheen=sheen)
        result['moss'] = obj
    bm.free()
    if turf > 0:
        import grass

        def ring(xy):
            xy = numpy.asarray(xy, dtype=numpy.float64)
            d = numpy.linalg.norm(xy[:, None, :] - centres[None, :, :], axis=2) - radii[None, :]
            weight = numpy.clip(_smoothstep(-0.02, 0.06, d) * (1.0 - _smoothstep(0.08, reach + 0.12, d)), 0.0, 1.0).max(1)
            if allowed is not None:
                weight = weight * allowed(xy)
            return weight
        result['turf'] = grass.grow(ground, area=ring, layers=('turf',), amount=float(turf), seed=int(seed) + 5,
                                    collection=collection)
    result['ferns_left_out'] = 0
    if int(ferns) > 0:
        import random
        pick = random.Random(int(seed) + 77)
        by_size = numpy.argsort(-radii)
        order = by_size[:int(ferns)] if allowed is None else by_size
        from mathutils.bvhtree import BVHTree
        tree = BVHTree.FromObject(ground, bpy.context.evaluated_depsgraph_get())
        inverse = matrix.inverted()
        around = [(math.cos(math.tau * j / 8.0), math.sin(math.tau * j / 8.0)) for j in range(8)]
        for k in order:
            if len(result['ferns']) >= int(ferns):
                break
            size = max(0.3, min(0.6, radii[k] * 1.4))
            angle = pick.uniform(0.0, 2.0 * math.pi)
            if allowed is not None:
                # another side of the rock, or a smaller fern, where its crown and its fronds' reach (about 0.75 of
                # its size round the crown) keep out of the places it must not cover; else the next biggest rock
                found = None
                for fern_size in ([size, 0.3] if size > 0.3 else [size]):
                    for turn in range(24):
                        a = angle + math.tau * turn / 24.0
                        cx = centres[k, 0] + (radii[k] + 0.04) * math.cos(a)
                        cy = centres[k, 1] + (radii[k] + 0.04) * math.sin(a)
                        test = [(cx, cy)] + [(cx + 0.75 * fern_size * u, cy + 0.75 * fern_size * v) for u, v in around]
                        if allowed(test).all():
                            found = (a, fern_size)
                            break
                    if found:
                        break
                if found is None:
                    continue
                angle, size = found
            x = centres[k, 0] + (radii[k] + 0.04) * math.cos(angle)
            y = centres[k, 1] + (radii[k] + 0.04) * math.sin(angle)
            start = inverse @ __import__('mathutils').Vector((x, y, 1000.0))
            hit = tree.ray_cast(start, (inverse.to_3x3() @ __import__('mathutils').Vector((0, 0, -1))).normalized())
            z = (matrix @ hit[0]).z if hit[0] is not None else 0.0
            result['ferns'].append(store.add_part('fern', location=(x, y, z), turn=math.degrees(angle) + 90.0,
                                                  seed=int(seed) + int(k), size=size,
                                                  collection=collection))
        result['ferns_left_out'] = int(ferns) - len(result['ferns'])
    return result


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--material', action='append', default=[], help='a material in the file or the store to make a mossy copy of (repeat for more)')
    parser.add_argument('--grow', action='append', default=[], help='an object in the file to grow real moss on (repeat for more)')
    parser.add_argument('--amount', type=float, default=0.8, help='how much moss, 0 to 1.5; default 0.8')
    parser.add_argument('--foot', type=float, help='how far up the foot moss climbs, metres; default 0.35 (add), 0.15 (grow)')
    parser.add_argument('--scale', type=float, default=3.0, help='add: patch size (3: about 30 cm); default 3')
    parser.add_argument('--lichen', type=float, default=0.0, help='add: pale lichen crusts on the bare stone, 0 to 1.5; default 0')
    parser.add_argument('--thickness', type=float, default=0.03, help='grow: the cushions\' depth, metres; default 0.03')
    parser.add_argument('--pile', type=float, default=1.0, help='grow: the tufts, 1 about 16,000 a square metre, 0 none; default 1')
    parser.add_argument('--seed', type=int, default=0, help='grow: the same seed, the same moss; default 0')
    parser.add_argument('--greens', default='olive', choices=list(GREENS), help="grow: the cushions' greens; default 'olive'")
    parser.add_argument('--sheen', type=float, default=SHEEN, help="grow: the cushions' sheen, 0 to 1; default %s" % SHEEN)
    parser.add_argument('--lumps', type=float, default=LUMPS, help="grow: the photographed moss's lumps, 0 to 2; default %s" % LUMPS)
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not (args.blend and (args.material or args.grow) and args.out):
        parser.error('--blend, --out and a --material (a mossy copy) or a --grow (real moss on an object) are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    for name in args.material:
        made = add(name, amount=args.amount, foot=0.35 if args.foot is None else args.foot, scale=args.scale, lichen=args.lichen)
        print('%s: made %s' % (name, made.name))
    for name in args.grow:
        grown = grow(bpy.data.objects[name], amount=args.amount, thickness=args.thickness,
                     foot=0.15 if args.foot is None else args.foot, pile_amount=args.pile, seed=args.seed,
                     sheen=args.sheen, lumps=args.lumps, greens=args.greens)
        print('%s: %s' % (name, ('grew %s, %.2f square metres of cushions' % (grown.name, grown.data['moss_area'])) if grown else 'no moss grew'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))

if __name__ == '__main__':
    main()
