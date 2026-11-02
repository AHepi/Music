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
}

# word pairs first (they beat single words), then single words in priority order
PAIR_WORDS = [
    (('window', 'lit'), 'window lit'), (('lit', 'window'), 'window lit'), (('window', 'warm'), 'window lit'),
    (('window', 'dim'), 'window dim'), (('dim', 'window'), 'window dim'),
    (('window', 'dark'), 'window dark'), (('dark', 'window'), 'window dark'),
    (('lamp', 'glass'), 'lamp glass'), (('lamp', 'head'), 'lamp glass'), (('lamp', 'pane'), 'lamp glass'),
    (('lamp', 'post'), 'iron'), (('lamp', 'cap'), 'iron'), (('down', 'pipe'), 'iron'), (('wall', 'foot'), 'grime'),
    (('window', 'surround'), 'trim'), (('door', 'surround'), 'trim'), (('door', 'step'), 'pavement'),
    (('cart', 'wheel'), 'iron'), (('chimney', 'pot'), 'trim'),
]
SINGLE_WORDS = [
    ('lantern', 'lamp glass'), ('mantle', 'flame'), ('flame', 'flame'), ('fire', 'flame'), ('glow', 'flame'),
    ('kerb', 'trim'), ('curb', 'trim'), ('sill', 'trim'), ('lintel', 'trim'), ('quoin', 'trim'), ('cornice', 'trim'),
    ('surround', 'trim'), ('dressing', 'trim'), ('trim', 'trim'), ('plinth', 'trim'),
    ('window', 'window dark'), ('pane', 'window dark'), ('glass', 'window dark'), ('fanlight', 'window dim'),
    ('puddle', 'water'), ('water', 'water'), ('gutter', 'water'),
    ('smoke', 'smoke'), ('haze', 'smoke'),
    ('roof', 'roof'), ('slate', 'roof'), ('tile', 'roof'), ('ridge', 'roof'),
    ('road', 'road'), ('cobble', 'road'), ('sett', 'road'), ('street', 'road'), ('lane', 'road'), ('carriageway', 'road'),
    ('pavement', 'pavement'), ('flag', 'pavement'), ('footpath', 'pavement'), ('slab', 'pavement'), ('step', 'pavement'),
    ('arch', 'trim'), ('cap', 'trim'),
    ('door', 'wood'), ('shutter', 'wood'), ('frame', 'wood'), ('sash', 'wood'), ('beam', 'wood'), ('plank', 'wood'),
    ('board', 'wood'), ('cart', 'wood'), ('crate', 'wood'), ('barrel', 'wood'), ('timber', 'wood'), ('wood', 'wood'), ('fence', 'wood'),
    ('rust', 'rust'), ('rusty', 'rust'),
    ('iron', 'iron'), ('post', 'iron'), ('rail', 'iron'), ('pipe', 'iron'), ('bracket', 'iron'), ('gate', 'iron'),
    ('drain', 'iron'), ('metal', 'iron'), ('steel', 'iron'), ('wheel', 'iron'), ('chain', 'iron'), ('wire', 'iron'),
    ('plaster', 'plaster'), ('render', 'plaster'), ('limewash', 'plaster'),
    ('mortar', 'mortar'), ('joint', 'mortar'),
    ('moss', 'moss'), ('algae', 'moss'), ('lichen', 'moss'),
    ('grime', 'grime'), ('soot', 'grime'), ('stain', 'grime'), ('dirt', 'grime'),
    ('weed', 'weed'), ('grass', 'weed'), ('ivy', 'weed'),
    ('leaf', 'leaf'), ('leaves', 'leaf'), ('litter', 'leaf'),
    ('paper', 'paper'), ('poster', 'paper'), ('notice', 'paper'),
    ('recess', 'recess'), ('void', 'recess'), ('inside', 'recess'), ('interior', 'recess'), ('dark', 'recess'), ('shadow', 'recess'),
    ('wall', 'wall'), ('brick', 'wall'), ('stone', 'wall'), ('masonry', 'wall'), ('facade', 'wall'), ('terrace', 'wall'),
    ('house', 'wall'), ('chimney', 'wall'), ('tenement', 'wall'), ('building', 'wall'), ('shop', 'wall'), ('tower', 'wall'),
    ('earth', 'earth'), ('ground', 'earth'), ('yard', 'earth'), ('mud', 'earth'), ('soil', 'earth'), ('grit', 'earth'), ('track', 'earth'),
]


def role_from_name(name):
    words = re.findall(r'[a-z]+', name.lower())
    word_set = set(words)
    for pair, role in PAIR_WORDS:
        if pair[0] in word_set and pair[1] in word_set:
            return role
    for word, role in SINGLE_WORDS:
        if word in word_set:
            return role
    return None


def role_for(obj, roles_file):
    if obj.get('place_role') in ROLE_MATERIALS:
        return obj['place_role']
    if roles_file and obj.name in roles_file and roles_file[obj.name] in ROLE_MATERIALS:
        return roles_file[obj.name]
    return role_from_name(obj.name)


def append_materials(names):
    """Bring the named materials in from Materials.blend (once); return them by name."""
    wanted = [n for n in names if n not in bpy.data.materials]
    if wanted:
        with bpy.data.libraries.load(MATERIALS_BLEND, link=False) as (data_from, data_to):
            missing = [n for n in wanted if n not in data_from.materials]
            if missing:
                raise SystemExit('not in Materials.blend: ' + ', '.join(missing))
            data_to.materials = wanted
    return {n: bpy.data.materials[n] for n in names}


def place_bounds(scene, backdrop_limit=400.0):
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in scene.objects:
        if obj.type != 'MESH' or max(obj.dimensions) > backdrop_limit:
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
    return 'LAID •' in obj.name or '• laid' in obj.name or any('LAID •' in c.name for c in obj.users_collection)


def apply(scene, roles_file=None, seed=7, setts=True):
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
    counts = {}
    for obj in scene.objects:
        if obj.name not in plan:
            continue
        role = plan[obj.name]
        choice = ROLE_MATERIALS[role]
        name = rng.choice(choice) if isinstance(choice, list) else choice
        obj.data.materials.clear()
        obj.data.materials.append(materials[name])
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
    return {'objects_dressed': len(plan), 'by_role': counts, 'unassigned': unassigned, 'laid_stones': laid,
            'projection_fitted_to': {'low': tuple(round(v, 1) for v in low), 'high': tuple(round(v, 1) for v in high), 'nodes': fitted}}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Dress a scene with the street materials by role.')
    parser.add_argument('--scene', required=True)
    parser.add_argument('--save-as', required=True)
    parser.add_argument('--roles', help='a JSON file: {"object name": "role"}')
    parser.add_argument('--report', help='write the report here as JSON')
    parser.add_argument('--no-setts', action='store_true', help='leave flat roads and pavements flat')
    args = parser.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.scene))
    roles_file = json.load(open(args.roles)) if args.roles else None
    report = apply(bpy.context.scene, roles_file, setts=not args.no_setts)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save_as))
    print(json.dumps(report, indent=2))
    if args.report:
        with open(args.report, 'w') as handle:
            json.dump(report, handle, indent=2)


if __name__ == '__main__':
    main()
