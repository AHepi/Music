"""
What this file does:
Gives the objects of a scene proven materials from the street bundle "Rain on the Old Curve", chosen by each
object's role. The builder builds plain shapes and names them with role words ("left terrace wall", "road",
"window lit", "lamp glass", "puddle"); this script does the dressing.

    blender -b --python apply_by_role.py -- --scene PLACE.blend --save-as DRESSED.blend [--roles roles.json] [--report report.json]
    python3 apply_by_role.py --scene ... --save-as ...        (with the bpy module installed)

Where a role comes from, in this order:
  1. the object property `place_role` (set it in your build script: obj['place_role'] = 'wall'),
  2. the roles file, if given: {"object name": "role", ...},
  3. role words in the object's name (see Roles.md for the words).
An object with no role keeps whatever material it has; the report lists it.

The materials are appended once from Materials.blend (next to this file, its pictures packed inside). The stone
materials project one unique sandstone picture in world space; this script stretches that projection over the
place's own size, because the bundle tuned it to one street. Everything else in them is procedural and carries
anywhere. Nothing in the scene's shapes is changed.
"""

import argparse
import json
import os
import random
import re
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lay_setts  # noqa: E402
import lay_facade  # noqa: E402
import lay_timber  # noqa: E402
import lay_details  # noqa: E402
import scans  # noqa: E402

MATERIALS_BLEND = os.path.join(HERE, 'Materials.blend')

WALL_SHADES = ['Hand-painted sandstone • shade %02d' % i for i in range(12)]

ROLE_MATERIALS = {
    'wall': WALL_SHADES,
    'plaster': 'PLASTER • mineral flakes and scars',
    'trim': 'STONE • worn honey-grey architectural dressings',
    'mortar': 'MORTAR • dark eroded joints',
    'road': 'COBBLES • wet basalt / broken amber-blue reflections',
    'pavement': 'PAVEMENT • damp sandstone slabs',
    'earth': 'ROAD BED • damp grit',
    'roof': 'SLATE • soot-dark irregular roofs',
    'wood': 'WOOD • peeling dark painted doors',
    'iron': 'IRON • soot-black lamp posts',
    'rust': 'RUST • rain-aged iron',
    'window lit': 'GLASS • warm occupied interiors',
    'window dim': 'GLASS • dim amber rooms',
    'window dark': 'GLASS • sleeping navy interiors',
    'lamp glass': 'Lantern • glowing imperfect amber glass',
    'flame': 'LAMP • honey flame glow',
    'water': 'PUDDLE • shallow transparent reflective film',
    'moss': 'MOSS • subdued olive crevices',
    'grime': 'GRIME • dark damp organic residue',
    'recess': 'RECESSES • near-black blue',
    'smoke': 'Chimney smoke • organic soft wisps',
    'weed': 'Weed • rain olive',
    'leaf': 'Fallen leaf • ochre',
    'paper': 'PAPER • aged torn fragments',
    'rock': 'STONE • unique sandstone / damp soot',
    'sand': 'ROLE • damp sand',
    'sea': 'ROLE • dark sea with small waves',
}

CODE_MATERIALS = {}  # made here, because Materials.blend has no such surface


def _code_material(name):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    geometry = nodes.new('ShaderNodeNewGeometry')
    noise = nodes.new('ShaderNodeTexNoise')
    links.new(geometry.outputs['Position'], noise.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    if 'sand' in name:
        import scans
        if scans.available('damp_beach_sand'):
            bpy.data.materials.remove(material)
            return scans.sand(name)          # the photographed sand, when the scans are here
        noise.inputs['Scale'].default_value = 3.0
        noise.inputs['Detail'].default_value = 6
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (0.060, 0.056, 0.047, 1)   # sand in this look is a dark, damp grey-brown, never a pale floor:
        ramp.color_ramp.elements[1].color = (0.135, 0.122, 0.098, 1)   # a fire or a lamp nearby must not turn it to snow
        links.new(noise.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
        grain = nodes.new('ShaderNodeTexNoise')
        grain.inputs['Scale'].default_value = 900.0
        links.new(geometry.outputs['Position'], grain.inputs['Vector'])
        links.new(grain.outputs['Fac'], bump.inputs['Height'])
        bump.inputs['Strength'].default_value = 0.25
        principled.inputs['Roughness'].default_value = 0.95
    else:
        noise.inputs['Scale'].default_value = 1.6
        noise.inputs['Detail'].default_value = 4
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        bump.inputs['Strength'].default_value = 0.35
        principled.inputs['Base Color'].default_value = (0.006, 0.020, 0.028, 1)
        principled.inputs['Roughness'].default_value = 0.06
        principled.inputs['IOR'].default_value = 1.333
    return material

# word pairs first (they beat single words), then single words in priority order
PAIR_WORDS = [
    (('window', 'lit'), 'window lit'), (('lit', 'window'), 'window lit'), (('window', 'warm'), 'window lit'),
    (('window', 'dim'), 'window dim'), (('dim', 'window'), 'window dim'),
    (('window', 'dark'), 'window dark'), (('dark', 'window'), 'window dark'),
    (('lamp', 'glass'), 'lamp glass'), (('lamp', 'head'), 'lamp glass'), (('lamp', 'pane'), 'lamp glass'),
    (('lamp', 'post'), 'iron'), (('lamp', 'cap'), 'iron'), (('down', 'pipe'), 'iron'), (('wall', 'foot'), 'grime'),
    (('window', 'surround'), 'trim'), (('door', 'surround'), 'trim'), (('door', 'step'), 'pavement'),
    (('cart', 'wheel'), 'iron'), (('chimney', 'pot'), 'trim'),
    (('sea', 'water'), 'sea'), (('ocean', 'water'), 'sea'), (('lagoon', 'water'), 'sea'), (('harbour', 'water'), 'sea'),
    (('harbor', 'water'), 'sea'), (('salt', 'water'), 'sea'),
    # natural stone: "reef stone" is rock, though "stone" alone means a built wall
    (('reef', 'stone'), 'rock'), (('cliff', 'stone'), 'rock'), (('crag', 'stone'), 'rock'), (('outcrop', 'stone'), 'rock'),
    (('headland', 'stone'), 'rock'), (('shore', 'stone'), 'rock'), (('field', 'stone'), 'rock'),
]
# a container of water is not water: "water tank", "water butt", "water trough" take the role of what they are made of
WATER_CONTAINERS = {'tank', 'butt', 'trough', 'pump', 'tower', 'jug', 'bottle', 'bucket', 'barrel', 'can', 'pipe', 'tap', 'heater'}
SINGLE_WORDS = [
    ('boulder', 'rock'), ('rock', 'rock'),
    ('sand', 'sand'),
    ('lantern', 'lamp glass'), ('mantle', 'flame'), ('flame', 'flame'), ('fire', 'flame'), ('glow', 'flame'),
    ('kerb', 'trim'), ('curb', 'trim'), ('sill', 'trim'), ('lintel', 'trim'), ('quoin', 'trim'), ('cornice', 'trim'),
    ('surround', 'trim'), ('dressing', 'trim'), ('trim', 'trim'), ('plinth', 'trim'),
    ('window', 'window dark'), ('pane', 'window dark'), ('glass', 'window dark'), ('fanlight', 'window dim'),
    ('puddle', 'water'), ('water', 'water'), ('gutter', 'water'),
    ('smoke', 'smoke'), ('haze', 'smoke'),
    ('roof', 'roof'), ('slate', 'roof'), ('tile', 'roof'), ('ridge', 'roof'),
    ('road', 'road'), ('cobble', 'road'), ('sett', 'road'), ('street', 'road'), ('lane', 'road'), ('carriageway', 'road'),
    ('pavement', 'pavement'), ('flag', 'pavement'), ('flagstone', 'pavement'), ('footpath', 'pavement'), ('slab', 'pavement'),
    ('step', 'pavement'),
    ('arch', 'trim'), ('cap', 'trim'),
    ('door', 'wood'), ('shutter', 'wood'), ('frame', 'wood'), ('sash', 'wood'), ('beam', 'wood'), ('plank', 'wood'),
    ('board', 'wood'), ('cart', 'wood'), ('crate', 'wood'), ('barrel', 'wood'), ('timber', 'wood'), ('wood', 'wood'), ('wooden', 'wood'),
    ('fence', 'wood'),
    ('rust', 'rust'), ('rusty', 'rust'),
    ('iron', 'iron'), ('rail', 'iron'), ('pipe', 'iron'), ('bracket', 'iron'), ('gate', 'iron'),
    ('drain', 'iron'), ('metal', 'iron'), ('steel', 'iron'), ('wheel', 'iron'), ('chain', 'iron'), ('wire', 'iron'),
    ('plaster', 'plaster'), ('render', 'plaster'), ('limewash', 'plaster'),
    ('mortar', 'mortar'), ('joint', 'mortar'),
    ('moss', 'moss'), ('algae', 'moss'), ('lichen', 'moss'),
    ('grime', 'grime'), ('soot', 'grime'), ('stain', 'grime'), ('dirt', 'grime'),
    ('weed', 'weed'), ('grass', 'weed'), ('ivy', 'weed'),
    ('leaf', 'leaf'), ('leaves', 'leaf'), ('litter', 'leaf'),
    ('paper', 'paper'), ('poster', 'paper'), ('notice', 'paper'),
    ('recess', 'recess'), ('void', 'recess'), ('inside', 'recess'), ('interior', 'recess'), ('dark', 'recess'), ('shadow', 'recess'),
    ('wall', 'wall'), ('brick', 'wall'), ('stone', 'wall'), ('masonry', 'wall'), ('facade', 'wall'), ('chimney', 'wall'),
    ('earth', 'earth'), ('ground', 'earth'), ('yard', 'earth'), ('mud', 'earth'), ('soil', 'earth'), ('grit', 'earth'), ('track', 'earth'),
    # names of things rather than what they are made of come last, so the material word wins: "boat hull rust" stays rust,
    # "harbour wall stone" is a wall, "beach hut timber" is timber, "jetty deck" is timber
    ('trunk', 'wood'), ('bark', 'wood'), ('log', 'wood'), ('driftwood', 'wood'), ('deck', 'wood'), ('decking', 'wood'), ('jetty', 'wood'),
    ('pier', 'wood'), ('wharf', 'wood'), ('boardwalk', 'wood'), ('stilt', 'wood'), ('weatherboard', 'wood'), ('cladding', 'wood'),
    ('hull', 'wood'), ('canoe', 'wood'), ('boat', 'wood'), ('floorboard', 'wood'), ('table', 'wood'), ('chair', 'wood'), ('bench', 'wood'),
    ('stool', 'wood'), ('counter', 'wood'), ('shelf', 'wood'), ('cupboard', 'wood'), ('cabinet', 'wood'), ('dresser', 'wood'),
    ('butt', 'wood'),
    ('frond', 'weed'), ('foliage', 'weed'), ('canopy', 'weed'), ('bush', 'weed'), ('shrub', 'weed'), ('hedge', 'weed'), ('fern', 'weed'),
    ('reed', 'weed'),
    ('palm', 'wood'), ('tree', 'wood'), ('coconut', 'wood'),
    ('floor', 'pavement'), ('quay', 'pavement'), ('ceiling', 'plaster'), ('trough', 'trim'),
    ('post', 'iron'), ('tank', 'iron'),
    ('pond', 'water'), ('pool', 'water'), ('river', 'water'), ('canal', 'water'), ('lake', 'water'), ('stream', 'water'), ('creek', 'water'),
    ('sea', 'sea'), ('ocean', 'sea'), ('lagoon', 'sea'), ('harbour', 'sea'), ('harbor', 'sea'),
    ('beach', 'sand'), ('dune', 'sand'),
    ('reef', 'rock'), ('cliff', 'rock'), ('headland', 'rock'), ('crag', 'rock'), ('outcrop', 'rock'),
    ('terrace', 'wall'), ('house', 'wall'), ('tenement', 'wall'), ('building', 'wall'), ('shop', 'wall'), ('tower', 'wall'),
]


def name_words(name):
    """The words of a name, each also as its singular, so "flags", "steps" and "rocks" count as "flag", "step", "rock"."""
    words = set(re.findall(r'[a-z]+', name.lower()))
    for word in list(words):
        if len(word) > 3 and word.endswith('ies'):
            words.add(word[:-3] + 'y')
        if len(word) > 3 and word.endswith('es'):
            words.add(word[:-2])
        if len(word) > 3 and word.endswith('s'):
            words.add(word[:-1])
    if words & WATER_CONTAINERS:
        words.discard('water')
    return words


def role_from_name(name):
    word_set = name_words(name)
    for pair, role in PAIR_WORDS:
        if pair[0] in word_set and pair[1] in word_set:
            return role
    for word, role in SINGLE_WORDS:
        if word in word_set:
            return role
    return None


def role_for(obj, roles_file):
    """The builder's own `place_role` first; then the roles file; then the name. A role this script wrote at an earlier
    dressing (marked `place_role_from = 'dressing'`) is not the builder's: it is worked out again, so a renamed object
    takes its new role when the scene is dressed again."""
    if obj.get('place_role') in ROLE_MATERIALS and obj.get('place_role_from') != 'dressing':
        return obj['place_role']
    if roles_file and obj.name in roles_file and roles_file[obj.name] in ROLE_MATERIALS:
        return roles_file[obj.name]
    return role_from_name(obj.name)


def append_materials(names):
    """Bring the named materials in from Materials.blend (once), or make the few the file lacks; return them by name."""
    for name in names:
        if name.startswith('ROLE •'):
            _code_material(name)
    names = list(names)
    wanted = [n for n in names if n not in bpy.data.materials]
    if wanted:
        with bpy.data.libraries.load(MATERIALS_BLEND, link=False) as (data_from, data_to):
            missing = [n for n in wanted if n not in data_from.materials]
            if missing:
                raise SystemExit('not in Materials.blend: ' + ', '.join(missing))
            data_to.materials = wanted
    return {n: bpy.data.materials[n] for n in names}


def place_bounds(scene, backdrop_limit=400.0):
    """The place's own extent: backdrops, parked pattern pieces and everything the plugin added are left out, so a
    scene dressed twice measures the same as when it was dressed once."""
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in scene.objects:
        if obj.type != 'MESH' or max(obj.dimensions) > backdrop_limit or _is_laid_or_source(obj):
            continue
        if max((obj.matrix_world @ Vector(c)).z for c in obj.bound_box) < -20:
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            low = Vector((min(low.x, world.x), min(low.y, world.y), min(low.z, world.z)))
            high = Vector((max(high.x, world.x), max(high.y, world.y), max(high.z, world.z)))
    return low, high


def fit_projection(material, low, high):
    """
    Stretch the material's unique-picture projection over the place. The bundle wires Separate XYZ -> Multiply Add
    (one per picture axis) -> Combine XYZ -> the picture nodes; the multiply and add were tuned to the street.
    """
    if not material.use_nodes:
        return 0
    nodes = material.node_tree.nodes
    picture_nodes = [n for n in nodes if n.type == 'TEX_IMAGE' and n.name.startswith('Unique world-projected')]
    if not picture_nodes:
        return 0
    combine = None
    for link in material.node_tree.links:
        if link.to_node in picture_nodes and link.from_node.type == 'COMBXYZ':
            combine = link.from_node
            break
    if combine is None:
        return 0
    changed = 0
    for link in material.node_tree.links:
        if link.to_node == combine and link.from_node.type == 'MATH' and link.from_node.operation == 'MULTIPLY_ADD':
            math_node = link.from_node
            source_links = [l for l in material.node_tree.links if l.to_socket == math_node.inputs[0]]
            if not source_links or source_links[0].from_node.type != 'SEPXYZ':
                continue
            axis = 'xyz'.index(source_links[0].from_socket.name.lower())
            span = max(high[axis] - low[axis], 1.0)
            math_node.inputs[1].default_value = 1.0 / span
            math_node.inputs[2].default_value = -low[axis] / span
            changed += 1
    return changed


def _is_laid_or_source(obj):
    return (obj.name.startswith(('LAID •', 'DETAIL •', 'FACADE •', 'LOOK •', 'TIMBER •')) or '• laid' in obj.name or bool(obj.get('prototype'))
            or any(c.name.startswith(('LAID •', 'DETAIL •', 'FACADE •', 'TIMBER •')) for c in obj.users_collection))


FACADE_MATERIALS = {'trim': 'STONE • worn honey-grey architectural dressings', 'dark': 'RECESSES • near-black blue',
                    'wood': 'WOOD • peeling dark painted doors', 'mortar': 'MORTAR • dark eroded joints',
                    'slate': 'SLATE • soot-dark irregular roofs'}
DETAIL_MATERIALS = {'water': 'PUDDLE • shallow transparent reflective film', 'grime': 'GRIME • dark damp organic residue',
                    'soot': 'Damp • fine dark soot', 'rust': 'RUST • rain-aged iron', 'moss': 'MOSS • subdued olive crevices',
                    'stone': 'STONE • worn honey-grey architectural dressings', 'paper': 'PAPER • aged torn fragments'}
DETAIL_GREENS = ['Weed • rain olive', 'Weed • dark ivy', 'Weed • yellowed seed blades']
DETAIL_LEAVES = ['Fallen leaf • peat brown', 'Fallen leaf • ochre']


def facade_materials():
    by_name = append_materials(sorted(set(FACADE_MATERIALS.values()) | set(WALL_SHADES)))
    found = {key: by_name[name] for key, name in FACADE_MATERIALS.items()}
    found['shades'] = [by_name[name] for name in WALL_SHADES]
    return found


def detail_materials():
    by_name = append_materials(sorted(set(DETAIL_MATERIALS.values()) | set(DETAIL_GREENS) | set(DETAIL_LEAVES)))
    found = {key: by_name[name] for key, name in DETAIL_MATERIALS.items()}
    found['greens'] = [by_name[name] for name in DETAIL_GREENS]
    found['leaves'] = [by_name[name] for name in DETAIL_LEAVES]
    return found


def _grain_the_stone():
    """Real stone grain from the sandstone scan over every stone material of the street's that is in the scene
    (walls, dressings, flags, rocks): their colours and weathering stay; pits, cracks and relief come in."""
    count = 0
    for material in list(bpy.data.materials):
        # flags lie under the lamps' raking light: deeper relief there breaks their mirror-flat reflections, as worn stone does
        relief = 0.014 if material.name.startswith('PAVEMENT •') else 0.006
        if material.name.startswith(scans.STONE_FAMILY) and scans.add_stone_grain(material, relief=relief):
            count += 1
    return count


def timber_materials():
    by_name = append_materials([FACADE_MATERIALS['dark'], FACADE_MATERIALS['wood'], DETAIL_MATERIALS['rust'], ROLE_MATERIALS['iron']])
    return {'boards': scans.boards() or lay_timber.boards_material(), 'dark': by_name[FACADE_MATERIALS['dark']], 'painted': by_name[FACADE_MATERIALS['wood']],
            'rust': by_name[DETAIL_MATERIALS['rust']], 'iron': by_name[ROLE_MATERIALS['iron']]}


def apply(scene, roles_file=None, seed=7, setts=True, facade=True, boards=True, details=True, wet=1.0, grime=1.0, growth=1.0, litter=1.0,
          today=False):
    rng = random.Random(seed)
    plan = {}
    for obj in scene.objects:
        if obj.type != 'MESH' or _is_laid_or_source(obj) or len(obj.data.polygons) == 0:
            continue
        role = role_for(obj, roles_file)
        if role:
            plan[obj.name] = role
    needed = set()
    for role in plan.values():
        choice = ROLE_MATERIALS[role]
        needed.update(choice if isinstance(choice, list) else [choice])
    if setts:
        needed.update([ROLE_MATERIALS['earth'], ROLE_MATERIALS['road'], ROLE_MATERIALS['pavement']])
    materials = append_materials(sorted(needed))
    low, high = place_bounds(scene)
    fitted = sum(fit_projection(m, low, high) for m in materials.values())
    grained = _grain_the_stone()
    counts = {}
    timber_looks = {}
    for obj in scene.objects:
        if obj.name not in plan:
            continue
        role = plan[obj.name]
        choice = ROLE_MATERIALS[role]
        name = rng.choice(choice) if isinstance(choice, list) else choice
        material = materials[name]
        if role == 'wood':
            # big timber weathers to grey boards, trunks get bark; doors, shutters and frames keep the street's paint
            kind = lay_timber.timber_kind(obj, role)
            material = lay_timber.timber_material(kind, obj) or material
            timber_looks[kind] = timber_looks.get(kind, 0) + 1
            scans.mark_object(obj)          # its scale and grain, read by the photographed timber
        obj.data.materials.clear()
        obj.data.materials.append(material)
        counts[role] = counts.get(role, 0) + 1
    laid = {}
    if setts:
        # a flat road or pavement becomes laid stones; the flat object stays as the bed underneath
        for name, role in list(plan.items()):
            obj = scene.objects.get(name)
            if obj is None or not lay_setts.is_flat(obj):
                continue
            if role == 'road':
                _, count = lay_setts.lay_setts_on(obj, materials[ROLE_MATERIALS['road']], materials[ROLE_MATERIALS['earth']])
                laid[name] = {'setts': count}
            elif role == 'pavement' and max(obj.dimensions) > 3.0:
                _, count = lay_setts.lay_flags_on(obj, materials[ROLE_MATERIALS['pavement']])
                laid[name] = {'flags': count}
    unassigned = [o.name for o in scene.objects if o.type == 'MESH' and o.name not in plan and max(o.dimensions) <= 400
                  and not _is_laid_or_source(o) and len(o.data.polygons) > 0]
    for name, role in plan.items():
        obj = scene.objects.get(name)
        if obj is not None and (not obj.get('place_role') or obj.get('place_role_from') == 'dressing'):
            obj['place_role'] = role
            obj['place_role_from'] = 'dressing'     # written here, not by the builder: worked out again next time
    report = {'objects_dressed': len(plan), 'by_role': counts, 'timber_looks': timber_looks, 'unassigned': unassigned, 'laid_stones': laid,
              'projection_fitted_to': {'low': tuple(round(v, 1) for v in low), 'high': tuple(round(v, 1) for v in high), 'nodes': fitted},
              'stone_given_scanned_grain': grained, 'scans_on_the_shelf': scans.available()}
    if facade:
        report['facade'] = lay_facade.lay_facades(scene, facade_materials(), role_from_name)
        report['stone_given_scanned_grain'] += _grain_the_stone()     # the dressings and shades the facades brought in
    if boards:
        roles = {o.name: role_for(o, roles_file) for o in scene.objects if o.type == 'MESH' and not _is_laid_or_source(o)}
        report['boards'] = lay_timber.lay_boards(scene, roles, role_from_name, timber_materials())
    if details:
        report['details'] = lay_details.lay_details(scene, detail_materials(), role_from_name,
                                                    wet=wet, grime=grime, growth_amount=growth, litter_amount=litter, today=today)
    return report


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Dress a scene with the street materials by role.')
    parser.add_argument('--scene', required=True)
    parser.add_argument('--save-as', required=True)
    parser.add_argument('--roles', help='a JSON file: {"object name": "role"}')
    parser.add_argument('--report', help='write the report here as JSON')
    parser.add_argument('--no-setts', action='store_true', help='leave flat roads and pavements flat')
    parser.add_argument('--no-facade', action='store_true', help='leave flat stone walls flat (no ashlar, dressings, sashes)')
    parser.add_argument('--no-boards', action='store_true', help='leave plain timber walls plain (no lapped boards, no shade per board)')
    parser.add_argument('--no-details', action='store_true', help='no puddles, damp, stains, rust, moss, weeds or litter')
    parser.add_argument('--wet', type=float, default=1.0,
                        help='water: puddles, gutter water, the wet band by water, foam and swash, things wet to the tide line (0 none, 1 the street, 2 twice)')
    parser.add_argument('--grime', type=float, default=1.0,
                        help='damp wall feet, soot and run-off stains, rust under iron, damp and rot up timber feet')
    parser.add_argument('--growth', type=float, default=1.0, help='moss and weeds: at feet, along kerbs, in joints, mould on timber, moss along banks')
    parser.add_argument('--litter', type=float, default=1.0,
                        help='leaves, rubbish, fallen flakes, paint flakes, sand drifts, the wrack line, driftwood, what trees drop')
    parser.add_argument('--no-scans', action='store_true',
                        help='use the code-made timber, bark, sand and driftwood and no scanned stone grain (for a before-and-after)')
    parser.add_argument('--today', action='store_true',
                        help="the place is in the present day: today's scraps (plastic, rope ends, a sandal) join the tide line")
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.scene))
    if args.no_scans:
        scans.ENABLED = False
    roles_file = json.load(open(args.roles)) if args.roles else None
    report = apply(bpy.context.scene, roles_file, setts=not args.no_setts, facade=not args.no_facade, boards=not args.no_boards, details=not args.no_details,
                   wet=args.wet, grime=args.grime, growth=args.growth, litter=args.litter, today=args.today)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_as))
    print(json.dumps(report, indent=2))
    if args.report:
        with open(args.report, 'w') as handle:
            json.dump(report, handle, indent=2)


if __name__ == '__main__':
    main()
