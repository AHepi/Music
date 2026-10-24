"""Writes the hand-made audit fixtures (flat hut and finished hut) into kit/calculators/tests/fixtures/place/."""
import json, os, sys
KIT = '/home/user/Music/plugins/explainer-film/kit'
sys.path.insert(0, os.path.join(KIT, 'place-kit'))
from place_kit import roles as R, settings_file as S, names
OUT = os.path.join(KIT, 'calculators', 'tests', 'fixtures', 'place')
os.makedirs(OUT, exist_ok=True)
table = S.roles_table()

def material(name, role, finished):
    req = R.requirements(role, table, {})
    treatments = {}
    for key in names.ALL_TREATMENTS:
        required = key in req['required']
        wanted = key in req['wanted']
        if not (required or wanted):
            continue
        has = finished
        entry = {'has': has, 'required': required, 'wanted': wanted, 'amount': (0.5 if has and key in names.LAYER_ORDER else None), 'detail': {}}
        if key == 'normal_map' and has:
            entry['detail'] = {'images': 2, 'space': 'TANGENT', 'colourspace': 'Non-Color', 'uv_map': 'UVMap', 'reaches_normal': True, 'strength': 0.9, 'bump_leftover': 0}
        if key == 'displacement' and has:
            entry['detail'] = {'method': 'BOTH', 'depth_metres': 0.06, 'mesh': 'dense'}
        treatments[key] = entry
    missing = [k for k, v in treatments.items() if not v['has'] and v['required']]
    return {'name': name, 'role': role, 'users': 1, 'objects': [], 'treatments': treatments, 'missing': missing, 'off_with_reason': {}}

def obj(name, role, mat, finished, size=None, bevel=True, uv=True, plain=True):
    req = R.requirements(role, table, {})
    layers = [k for k in names.LAYER_ORDER if k in req['required']]
    o = {'name': name, 'role': role, 'owner': 'hut', 'collection': 'Place: hut', 'materials': [mat], 'has_normal_map': finished,
         'uv': {'has': uv if finished else False, 'layer': 'UVMap', 'mirrored_share': 0.0}, 'look': 'lived_in',
         'layer_amounts': {k: 0.5 for k in layers} if finished else {}, 'layer_amounts_missing': [] if finished else layers, 'layers_off': [],
         'geometry': {'triangles': 12, 'plain_box': plain and not finished, 'bevel': finished and bevel, 'shape_damage': finished, 'relief_m': 0.0, 'mean_edge_m': 1.0},
         'construction': {'carried': True, 'via': 'ground', 'gap_mm': 0.0, 'hung': False, 'floating': False, 'short_by_mm': 0, 'span_max_m': 0.0, 'inside_out': False,
                          'coplanar_faces': 0, 'buried_light': False, 'opening_floor_gap_m': None, 'needs_ground': False},
         'scale': [], 'missing': [], 'visible': True, 'exempt': False}
    if 'bevelled_edges' in req['required'] and not (finished and bevel):
        o['missing'].append('bevelled_edges')
    if 'shape_damage' in req['required'] and not finished:
        o['missing'].append('shape_damage')
    return o

def hut(finished):
    spec = [('ground', 'ground.earth', 'ground_mat'), ('wall_north', 'wall.plaster', 'wall_mat'), ('wall_south', 'wall.plaster', 'wall_mat'), ('wall_east', 'wall.plaster', 'wall_mat'),
            ('wall_west', 'wall.plaster', 'wall_mat'), ('roof', 'roof.shingle', 'roof_mat'), ('door', 'timber.door', 'door_mat'), ('floor_plank_1', 'timber.floor', 'floor_mat'),
            ('floor_plank_2', 'timber.floor', 'floor_mat')]
    mats = {}
    objects = []
    for name, role, mat in spec:
        if mat not in mats:
            mats[mat] = material(mat if not finished else f'PK {role} / x', role, finished)
        mats[mat]['objects'].append(name)
        objects.append(obj(name, role, mats[mat]['name'], finished))
    audit = {'audit_version': 1, 'made': '2026-10-22T12:00:00', 'blender': '5.2.2', 'scene_file': 'hut.blend', 'scene_sha1': 'a' * 40, 'settings_file': 'place-settings.json', 'settings_sha1': 'b' * 40,
             'place': 'hut', 'place_type': 'generic', 'look': 'lived_in', 'state': 'dry', 'quick': False, 'map_size_pixels': 1024, 'mask': {'cell_metres': 0.1, 'seconds': 3.0, 'source': 'whole_scene'}, 'masks_from': 'whole_scene',
             'picture': {'camera': None, 'height_pixels': None, 'set': False},
             'counts': {'objects_visible': len(objects), 'materials': len(mats), 'triangles': 108, 'triangles_by_owner': {'hut': 108}, 'scatter_pieces': 0, 'ground_area_m2': 100},
             'roles': {'unknown': [], 'fallback': [], 'by_role': {}},
             'materials': list(mats.values()), 'objects': objects, 'siblings': {}, 'scatter': {'groups': []},
             'normal_maps': {'images': [], 'test_light': {'verdict': 'pass'}}, 'displacement': {'materials': [], 'objects': [], 'too_coarse': []}, 'roads': [],
             'renderer': {'decision': 'EEVEE', 'reasons': [], 'settings_choice': 'auto'}, 'light': {'any_light': True, 'clip_share': 0.0}, 'off': {'entries': [], 'allowed_ids': [], 'share': 0.0}, 'problems': []}
    for o in objects:
        audit['roles']['by_role'][o['role']] = audit['roles']['by_role'].get(o['role'], 0) + 1
    if finished:
        audit['normal_maps']['images'] = [{'name': 'pk_plaster_lime_nor', 'size': [1024, 1024], 'mean_rgb': [0.5, 0.5, 0.97], 'convention': 'opengl', 'made_by_kit': True, 'colourspace': 'Non-Color',
                                           'direction': {'x': 0.6, 'y': 0.6, 'method': 'height'}, 'verdict': 'pass'}]
        audit['scatter'] = {'groups': [{'name': 'tuft', 'count': 80, 'in_keepout': 0, 'in_puddle': 0, 'on_crown': 0, 'on_wheel_track': 0, 'within_5cm_of_litter': 0}]}
        for m in audit['materials']:
            for key in ('plants', 'litter_pieces'):
                if key in m['treatments']:
                    m['treatments'][key]['has'] = True
    else:
        audit['floating_note'] = 'one floor plank floats 6 cm'
        audit['objects'][-1]['construction'].update(carried=False, floating=True, gap_mm=60.0)
    return audit
json.dump(hut(False), open(os.path.join(OUT, 'flat_hut_audit.json'), 'w'), indent=1)
json.dump(hut(True), open(os.path.join(OUT, 'finished_hut_audit.json'), 'w'), indent=1)
print('written')
