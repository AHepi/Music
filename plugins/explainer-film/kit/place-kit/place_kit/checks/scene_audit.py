"""What this does: gathers the FACTS about a finished (or unfinished) place into one place-audit.json: for every material which treatments it
has and which its role requires, for every object its role, UVs, wear-layer amounts, shape and construction, sizes against real-world facts,
the scattered plants and litter with the keep-out counts, the normal maps and their direction, displacement, roads, the renderer rule and the
light. It decides nothing: calculators/place_audit_check.py judges the audit with the house numbers (decision D2 of the 1.4.0 design), so thresholds
live in one table and the judge is tested without Blender.
The audit describes the scene file ON DISK: it hashes the saved file (scene_sha1) and never saves the scene itself, so a file that is changed
afterwards is recognised as a different file (the audit is then stale). An unsaved scene is refused (exit 2).
A concrete example: audit_place(settings, 'place-audit.json') on a flat hut returns an audit in which every material's treatments have has false,
and the judge then fails it naming normal_map, roughness_variation, colour_variation, dirt, grime, weathering and the rest per material.
Needs Blender (bpy) and numpy.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess

import numpy as np

import bpy

from .. import house_numbers, names, parts, roles as roles_module, run_record, scene_read, settings_file
from . import construction, material_inspect, normals_test, scale

AUDIT_VERSION = 1
LAYER_SET = set(names.LAYER_ORDER)


class AuditRefused(Exception):
    """The audit cannot be made (an unsaved scene); the launcher turns it into exit 2 with this sentence."""


def sha1_of_file(path):
    digest = hashlib.sha1()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def _ground_area(ground_objects):
    total = 0.0
    for obj in ground_objects:
        vertices, triangles = parts.world_triangles(obj)
        if len(triangles):
            a, b, c = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]
            total += float(np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])).sum() / 2.0)
    return total


def _sibling_facts(object_rows, minimum_count):
    """Per role: how many objects, what share are exact copies of another (same mesh data and size, and no shape damage), spread of sizes."""
    groups = {}
    for row in object_rows:
        if row.get('exempt') or not row.get('role') or roles_module.is_never(row['role']):
            continue
        groups.setdefault(row['role'], []).append(row)
    result = {}
    for role, rows in groups.items():
        if len(rows) < minimum_count:
            continue
        keys = {}
        for row in rows:
            key = (row.get('mesh_name'), tuple(round(v, 2) for v in row.get('size', [])), bool(row['geometry'].get('shape_damage')))
            keys.setdefault(key, []).append(row['name'])
        copies = sum(len(v) for k, v in keys.items() if len(v) > 1 and not k[2])
        sizes = np.array([r.get('size', [0, 0, 0]) for r in rows], dtype=float)
        spread = float((sizes.std(axis=0) / (sizes.mean(axis=0) + 1e-9)).mean()) if len(sizes) else 0.0
        result[role] = {'count': len(rows), 'copies_share': copies / len(rows), 'size_spread': round(spread, 3),
                        'all_damaged': all(r['geometry'].get('shape_damage') for r in rows)}
    return result


def _light_facts():
    scene = bpy.context.scene
    lamps = [o for o in scene.objects if o.type == 'LIGHT' and not o.hide_render and getattr(o.data, 'energy', 0) > 0]
    suns = [o for o in lamps if o.data.type == 'SUN']
    world_light = False
    if scene.world is not None:
        if scene.world.use_nodes and scene.world.node_tree is not None:
            for node in scene.world.node_tree.nodes:
                if node.type == 'BACKGROUND' and node.inputs['Strength'].default_value > 0 and max(node.inputs['Color'].default_value[:3]) > 0:
                    world_light = True
        elif max(scene.world.color[:3]) > 0:
            world_light = True
    emissive = any(m.node_tree is not None and material_inspect.inspect_material(m)['glows'] for m in bpy.data.materials if m.users > 0)
    return {'any_light': bool(lamps or world_light or emissive), 'lamps': len(lamps), 'suns': len(suns), 'world_light': world_light, 'emissive_materials': emissive, 'clip_share': None}


def audit_place(settings, out_path=None, judge=True, run_light_test=True, facts_path=None, construction_result=None, owner=None):
    """Gathers the audit (see the note at the top), writes it to out_path, and returns it. judge=True also runs the judge and puts its verdict
    in the returned dict under 'judged' (and the launcher prints the lines)."""
    if not bpy.data.filepath:
        raise AuditRefused('the scene has not been saved (no file name), so the audit cannot be tied to a file. Save it first (explainer-film-place finish --save-as OUT.blend), then audit that file.')
    path = bpy.data.filepath
    record = run_record.read()
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    objects = scene_read.mesh_objects(only_visible=True)
    if owner is not None:     # a part's own audit: its objects, plus the ground they stand on
        objects = [o for o in objects if o.get(names.OWNER) == owner or (o.get(names.ROLE) or '').startswith('ground.')]
    facts_list = [scene_read.object_facts(o) for o in objects]
    tagged = roles_module.tag_objects(facts_list, rules, table)
    by_object = tagged['by_object']
    problems = []
    quick = bool(record.get('quick'))

    # ---- fallbacks: objects the kit itself gave a fallback role (recorded on the object by tag_roles)
    fallback = [o.name for o in objects if o.get('pk_fallback_role')]
    unknown = [n for n in tagged['unknown'] if n not in fallback]

    # ---- construction and scale
    built = construction_result if construction_result is not None else construction.check_construction(settings, owner=owner)
    construction_by_object = built['objects']
    pairs = [(o, by_object[o.name]['role']) for o in objects if by_object[o.name]['role'] and not scene_read.is_scatter(o) and not roles_module.is_never(by_object[o.name]['role'])]
    scale_by_object = scale.scale_report(settings, pairs, facts_path)
    road_gauges = scale.gauge_entries(settings.roads, scale.load_facts(settings.data, facts_path))

    # ---- materials
    inspected = {}
    for material in bpy.data.materials:
        if material.users > 0 and material.node_tree is not None:
            inspected[material.name] = material_inspect.inspect_material(material)
    material_roles, material_objects = {}, {}
    for obj in objects:
        info = by_object[obj.name]
        if info['role'] is None:
            continue
        for slot_material, slot_role in zip([s.material for s in obj.material_slots if s.material is not None], info['slot_roles']):
            material_roles.setdefault(slot_material.name, set()).add(slot_role)
            material_objects.setdefault(slot_material.name, []).append(obj)

    # ---- scatter (plants and litter)
    from ..growth import keepout
    scatter = keepout.scatter_facts(settings)
    ground_objects = [o for o in objects if (by_object[o.name]['role'] or '').startswith('ground.') and not scene_read.is_scatter(o)]
    ground_area = _ground_area(ground_objects)
    per100 = (lambda count: (count / ground_area * 100.0) if ground_area > 0 else None)
    plants_count = sum(g['count'] for g in scatter['groups'] if g.get('group') == 'plant')
    litter_count = sum(g['count'] for g in scatter['groups'] if g.get('group') == 'litter')
    scatter['plants_per_100m2'] = per100(plants_count)
    scatter['litter_per_100m2'] = per100(litter_count)
    plants_floor = house_numbers.value('place_audit.plants_min_per_100_square_metres')
    litter_floor = house_numbers.value('place_audit.litter_min_per_100_square_metres')

    # ---- per object
    object_rows, triangles_by_owner, total_triangles = [], {}, 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    displacement_objects, too_coarse = [], []
    edge_limit = house_numbers.value('place_surfaces.displacement_mesh_edge_metres_max')
    off_cache = {}
    for obj in objects:
        info = by_object[obj.name]
        role = info['role']
        owner = settings.owner_of(scene_read.object_facts(obj)) or 'unowned'
        exempt = scene_read.is_scatter(obj) or (role is not None and roles_module.is_never(role))
        triangles = scene_read.triangle_count(obj, True, depsgraph)
        total_triangles += triangles
        triangles_by_owner[owner] = triangles_by_owner.get(owner, 0) + triangles
        material_list = [s.material for s in obj.material_slots if s.material is not None]
        layers_here = set()
        for material in material_list:
            layers_here |= set(inspected.get(material.name, {}).get('layers', {}))
        layer_amounts, layer_missing = {}, []
        layers_off = []
        if role:
            for layer in names.LAYER_ORDER:
                if roles_module.off_entries_for(role, layer, rules):
                    layers_off.append(layer)
        for layer in layers_here:
            key = names.layer_amount_name(layer)
            if key in obj.keys():
                layer_amounts[layer] = float(obj[key])
            else:
                layer_missing.append(layer)
        has_normal = any(inspected.get(m.name, {}).get('normal_map', {}).get('has') for m in material_list)
        geometry = {'triangles': triangles, 'plain_box': scene_read.is_plain_box(obj), 'bevel': scene_read.has_bevel(obj), 'shape_damage': scene_read.has_shape_damage(obj),
                    'mean_edge_m': scene_read.mean_edge_length(obj) if len(obj.data.edges) else 0.0, 'subdivided': scene_read.has_subdivision(obj)}
        if role and role.startswith('ground.'):
            geometry['relief_m'] = round(scene_read.relief_metres(obj), 4)
        wants_displacement = any(inspected.get(m.name, {}).get('displacement', {}).get('has') for m in material_list)
        if wants_displacement:
            displacement_objects.append(obj.name)
            if geometry['mean_edge_m'] > edge_limit and not geometry['subdivided']:
                too_coarse.append(obj.name)
        missing = []
        if role and not exempt:
            req = roles_module.requirements(role, table, rules)
            if 'bevelled_edges' in req['required'] and not geometry['bevel'] and not roles_module.off_entries_for(role, 'bevelled_edges', rules):
                missing.append('bevelled_edges')
            if 'shape_damage' in req['required'] and not geometry['shape_damage'] and not roles_module.off_entries_for(role, 'shape_damage', rules):
                missing.append('shape_damage')
        row = {'name': obj.name, 'role': role, 'owner': owner, 'collection': (obj.users_collection[0].name if obj.users_collection else None), 'materials': [m.name for m in material_list],
               'mesh_name': obj.data.name, 'size': [round(float(v), 4) for v in scene_read.object_size(obj)], 'has_normal_map': bool(has_normal), 'needs_uv': True,
               'uv': scene_read.uv_facts(obj), 'look': settings.look_for_role(role) if role else settings.look_id, 'layer_amounts': layer_amounts,
               'layer_amounts_missing': layer_missing, 'layers_off': layers_off, 'geometry': geometry, 'missing': missing, 'visible': True, 'exempt': exempt}
        if obj.name in construction_by_object and not exempt:
            row['construction'] = construction_by_object[obj.name]
        entries = list(scale_by_object.get(obj.name, []))
        if role == 'ground.dirt_road':
            entries += road_gauges
        if entries:
            row['scale'] = entries
        object_rows.append(row)
    for lamp_name, fact in construction_by_object.items():
        if fact.get('buried_light'):
            object_rows.append({'name': lamp_name, 'role': 'never.light', 'owner': 'unowned', 'collection': None, 'materials': [], 'size': [0, 0, 0], 'uv': {'has': True}, 'geometry': {},
                                'layer_amounts': {}, 'layer_amounts_missing': [], 'layers_off': [], 'missing': [], 'visible': True, 'exempt': False, 'construction': fact, 'mesh_name': None})

    # ---- material rows
    material_rows, off_pairs, required_pairs = [], 0, 0
    for material_name, role_set in sorted(material_roles.items()):
        info = inspected.get(material_name)
        if info is None:
            continue
        real_roles = [r for r in role_set if not roles_module.is_never(r)]
        if not real_roles:
            continue
        required, wanted, exempt_map, off_map = set(), set(), {}, {}
        for role in real_roles:
            req = roles_module.requirements(role, table, rules)
            for treatment in req['required']:
                off_entries = roles_module.off_entries_for(role, treatment, rules)
                required_pairs += 1
                if off_entries:
                    off_map[treatment] = off_entries[0].get('reason', '')
                    off_pairs += 1
                else:
                    required.add(treatment)
            wanted.update(req['wanted'])
        users = material_objects.get(material_name, [])
        treatments = {}
        for treatment in sorted(required | wanted | set(off_map), key=names.ALL_TREATMENTS.index):
            entry = {'required': treatment in required, 'wanted': treatment in wanted and treatment not in required, 'has': False, 'amount': None, 'detail': {}}
            if treatment == 'normal_map':
                entry.update(has=info['normal_map']['has'], detail=info['normal_map']['detail'])
            elif treatment == 'displacement':
                entry.update(has=info['displacement']['has'], detail=dict(info['displacement']['detail']))
                if info['displacement']['has']:
                    coarse = [o.name for o in users if o.name in too_coarse]
                    entry['detail']['mesh'] = 'coarse' if coarse else 'dense'
            elif treatment == 'roughness_variation':
                entry['has'] = bool(info['roughness_variation'])
            elif treatment == 'colour_variation':
                entry['has'] = bool(info['colour_variation'])
            elif treatment in LAYER_SET:
                entry['has'] = treatment in info['layers']
                amounts = [float(o[names.layer_amount_name(treatment)]) for o in users if names.layer_amount_name(treatment) in o.keys()]
                entry['amount'] = max(amounts) if amounts else None
            elif treatment == 'bevelled_edges':
                entry['has'] = all(scene_read.has_bevel(o) for o in users) if users else False
            elif treatment == 'shape_damage':
                entry['has'] = all(scene_read.has_shape_damage(o) for o in users) if users else False
            elif treatment == 'plants':
                entry['has'] = bool(plants_count) and (per100(plants_count) is None or per100(plants_count) >= plants_floor)
                entry['detail'] = {'count': plants_count, 'per_100_square_metres': per100(plants_count)}
            elif treatment == 'litter_pieces':
                entry['has'] = bool(litter_count) and (per100(litter_count) is None or per100(litter_count) >= litter_floor)
                entry['detail'] = {'count': litter_count, 'per_100_square_metres': per100(litter_count)}
            treatments[treatment] = entry
        material_rows.append({'name': material_name, 'role': sorted(real_roles)[0], 'roles': sorted(real_roles), 'users': len(users), 'objects': [o.name for o in users][:12],
                              'treatments': treatments, 'missing': [k for k, v in treatments.items() if v['required'] and not v['has']], 'off_with_reason': off_map,
                              'glows': info['glows']})

    # ---- normal maps, roads, renderer, off entries
    maps = normals_test.normal_map_facts(run_light=run_light_test and not quick)
    roads = []
    try:
        from ..surfaces import roads as roads_module
        roads = roads_module.audit_roads(settings, [o for o in ground_objects])
    except ImportError:
        problems.append('the roads step is not available (surfaces/roads.py)')
    renderer = {'decision': None, 'reasons': [], 'settings_choice': settings.get('renderer', 'auto')}
    try:
        from ..render import renderer_choice
        decision = renderer_choice.renderer_for_scene()
        renderer.update(decision=decision['engine'], reasons=decision['reasons'])
    except ImportError:
        renderer = None
    place_type = settings.place_type_id
    allowed_ids = []
    try:
        allowed_ids = [e['id'] for e in settings_file.place_type(place_type).get('allowed_off', [])]
    except ValueError:
        pass
    present_roles = list(tagged['by_role'])
    off_entries = []
    for e in settings.off_entries:
        patterns = e.get('roles') or ['*']
        applies = any(re.match('^' + re.escape(pattern).replace('\\*', '.*') + '$', role) for pattern in patterns for role in present_roles)
        if applies:
            off_entries.append({'layer': e.get('layer') or e.get('treatment'), 'roles': e.get('roles'), 'reason': e.get('reason'), 'reason_id': e.get('reason_id')})
    scene_sha1 = sha1_of_file(path)
    settings_sha1 = sha1_of_file(settings.path) if settings.path and os.path.exists(settings.path) else None
    audit = {'audit_version': AUDIT_VERSION, 'made': datetime.datetime.now().isoformat(timespec='seconds'), 'blender': bpy.app.version_string, 'scene_file': os.path.basename(path),
             'scene_sha1': scene_sha1, 'settings_file': os.path.basename(settings.path) if settings.path else None, 'settings_sha1': settings_sha1, 'place': settings.place,
             'place_type': place_type, 'look': record.get('look') or settings.look_id, 'state': record.get('state') or settings.state, 'quick': quick,
             'map_size_pixels': record.get('map_size_pixels'), 'mask': record.get('mask') or {}, 'masks_from': record.get('masks_from', 'whole_scene'),
             'picture': record.get('picture') or {'camera': None, 'height_pixels': None, 'set': False},
             'counts': {'objects_visible': len(objects), 'materials': len(material_rows), 'triangles': total_triangles, 'triangles_by_owner': triangles_by_owner,
                        'scatter_pieces': sum(g['count'] for g in scatter['groups']), 'ground_area_m2': round(ground_area, 2)},
             'roles': {'unknown': unknown, 'fallback': fallback, 'by_role': tagged['by_role']}, 'materials': material_rows, 'objects': object_rows,
             'siblings': _sibling_facts(object_rows, house_numbers.value('place_wear.shape_sibling_min_count')), 'scatter': scatter, 'normal_maps': maps,
             'displacement': {'materials': [m['name'] for m in material_rows if m['treatments'].get('displacement', {}).get('has')], 'objects': displacement_objects, 'too_coarse': too_coarse},
             'roads': roads, 'renderer': renderer, 'light': _light_facts(),
             'off': {'entries': off_entries, 'allowed_ids': allowed_ids, 'share': (off_pairs / required_pairs) if required_pairs else 0.0},
             'construction_summary': built['summary'], 'problems': problems}
    if renderer is None:
        del audit['renderer']
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, 'w') as handle:
            json.dump(audit, handle, indent=1, default=_json_default)
    return audit


def _json_default(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f'cannot write {type(value).__name__} as JSON')


def judge_audit(audit_path, blend=None, allow_quick=False, facts_path=None):
    """Runs calculators/place_audit_check.py check on the audit (a plain Python tool in its own process) and returns (exit code, its printed lines)."""
    import shutil
    tool = os.path.join(house_numbers.CALCULATORS, 'place_audit_check.py')
    python = os.environ.get('PYTHON') or shutil.which('python3') or 'python3'
    command = [python, '-I', '-B', tool, 'check', audit_path]
    if blend:
        command += ['--blend', blend]
    if allow_quick:
        command.append('--allow-quick')
    if facts_path:
        command += ['--facts', facts_path]
    run = subprocess.run(command, capture_output=True, text=True)
    return run.returncode, run.stdout + (run.stderr if run.returncode == 2 else '')
