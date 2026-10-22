# Applies Builder 3's own kit edits (patch 5) to a fresh copy of ours/kit_patched in surfaces/kit and writes the diffs.
import json, shutil, os, re, subprocess
BASE = 'proc-work/garden'
SRC = BASE + '/ours/kit_patched'
DST = BASE + '/surfaces/kit'
# fresh copy of the two files we edit
for rel in ('sets/japanese_courtyard.json', 'apply/roles.py', 'presets/mossy_courtyard_kept.json', 'masks/reader.py'):
    shutil.copy(os.path.join(SRC, rel), os.path.join(DST, rel))

# ---- roles.py: custom_props may be a list of alternatives (any one matching is enough)
p = DST + '/apply/roles.py'
s = open(p).read()
old = """def _props_ok(rule, obj):
    wanted = rule.get('custom_props')
    if not wanted:
        return False
    return all(obj.props.get(key) == str(value) for key, value in wanted.items())
"""
new = """def _props_ok(rule, obj):
    wanted = rule.get('custom_props')
    if not wanted:
        return False
    # GARDEN PATCH 5: custom_props may also be a LIST of alternatives ([{"ct_material_role": "stone"}, {"garden_role": "stone.natural"}]): one matching dict is enough,
    # so objects other builders make (tagged with garden_role) get their role without the set file knowing their names.
    alternatives = wanted if isinstance(wanted, list) else [wanted]
    return any(all(obj.props.get(key) == str(value) for key, value in alt.items()) for alt in alternatives)
"""
assert old in s
open(p, 'w').write(s.replace(old, new))

# ---- reader.py: the set is read with strict=False (the builders' own dials, such as moss_vs_stone, are only known after the layers register, so a strict first read of a set that
# uses them fails; apply() checks the look again after registering, which is where mistakes are caught)
p = DST + '/masks/reader.py'
s = open(p).read()
old = "k = kit_module.Kit.load(set_ref, scene_id=scene_id, strict=True)"
assert old in s
open(p, 'w').write(s.replace(old, "k = kit_module.Kit.load(set_ref, scene_id=scene_id, strict=False)   # GARDEN PATCH 5: was strict=True"))

# ---- set file
p = DST + '/sets/japanese_courtyard.json'
d = json.load(open(p))
roles = d['roles']
roles.pop('roof.deck', None)                                                     # matched no object: the roof's timber material is credited to 'Hall roof' (roof.tile)
roles['roof.tile']['objects'] = ['^Hall roof$']
roles['roof.tile']['_note'] = roles['roof.tile'].get('_note', '') + ' GARDEN PATCH 5: roof.deck role removed (it matched no object; the deck and ridge materials are credited to Hall roof by the evaluated-materials rule).'
roles['bark']['type'] = 'ANY'                                                    # the maple and pine trunks, branches and limbs are CURVE objects
roles['bark']['custom_props'] = [{'garden_role': 'bark'}]
roles['bark']['_note'] = 'GARDEN PATCH 5: type ANY so the curve objects match; also any object tagged garden_role=bark.'
for role in ('ground.earth', 'ground.gravel', 'stone.dressed', 'timber.deck', 'timber.frame', 'roof.tile', 'wall.plaster', 'wall.cap'):
    existing = roles[role].get('custom_props')
    alts = ([existing] if isinstance(existing, dict) else list(existing or [])) + [{'garden_role': role}]
    roles[role]['custom_props'] = alts
ex = roles['stone.natural'].get('custom_props')
roles['stone.natural']['custom_props'] = ([ex] if isinstance(ex, dict) else list(ex or [])) + [{'garden_role': 'stone.natural'}]
# never: patterns that matched nothing
d['never']['objects'] = [x for x in d['never']['objects'] if x != '^CT / ']
d['never']['materials'] = ['.*haze$' if x == 'haze$' else x for x in d['never']['materials']]
d['never']['_note'] = d['never'].get('_note', '') + " GARDEN PATCH 5: '^CT / ' removed (matched nothing: the hidden tile prototype is not in the scene's object list) and 'haze$' became '.*haze$' (names are matched from the start)."
# plate size = the garden pictures
d['plate']['size'] = [2400, 1600]
d['plate']['_note'] = 'GARDEN PATCH 5: the garden pictures are 2400 x 1600 (landscape), not the film plate.'
# layers: bark joins the film, the damp foot and the growth layers; per-material first guesses (from plan section 10, tuned by eye later)
ap = d['apply']
for layer in ('soot', 'foot', 'wallgrowth'):
    if 'bark' not in ap[layer]['roles']:
        ap[layer]['roles'].append('bark')
ap['soot']['role_dials'] = {
    'wall.plaster': {'film_mult': 0.9}, 'stone.dressed': {'film_mult': 0.9},
    'roof.tile': {'film_mult': 1.0, 'roof_mult': 1.0, 'grey_pull': 0.0, 'floor_mult': 0.9},        # dark surfaces: no darker film, pale marks only
    'timber.frame': {'film_mult': 1.0, 'grey_pull': 0.0, 'floor_mult': 0.9}, 'wall.cap': {'film_mult': 1.0, 'grey_pull': 0.0, 'floor_mult': 0.9},
    'bark': {'film_mult': 0.95, 'grey_pull': 0.0},
}
ap['foot']['role_dials'] = {
    'wall.plaster': {'splash_strength': 0.5, 'tide_green': 0.4}, 'stone.dressed': {'splash_strength': 0.6, 'tide_green': 0.4},
    'stone.natural': {'splash_strength': 1.4, 'tide_green': 0.5}, 'timber.frame': {'tide_green': 0.5, 'splash_strength': 0.3},
    'bark': {'splash_strength': 0.5, 'tide_green': 0.4},
}
ap['wallgrowth']['role_dials'] = {
    'wall.plaster': {'lichen_amount': 0.002, 'moss_amount': 0.25, 'algae_amount': 1.0},
    'stone.natural': {'lichen_amount': 0.4, 'moss_amount': 0.1, 'moss_vs_stone': 0.6},
    'stone.dressed': {'lichen_amount': 0.3, 'moss_amount': 0.1, 'moss_vs_stone': 0.6},
    'timber.frame': {'lichen_amount': 0.002, 'moss_amount': 0.15},
    'timber.deck': {'lichen_amount': 0.002, 'moss_amount': 0.1, 'algae_amount': 0.8},
    'roof.tile': {'moss_amount': 1.2, 'moss_vs_stone': 1.0, 'lichen_amount': 0.002},
    'wall.cap': {'moss_amount': 0.5, 'lichen_amount': 0.1, 'moss_vs_stone': 0.8},
    'bark': {'moss_amount': 0.6, 'lichen_amount': 0.3, 'moss_vs_stone': 0.8},
}
# ground moss (patch moss on earth, gravel and stones): the first pictures showed flat pale-mint blotches on the stones (dial sweep on 21 Oct: they come from patch_moss on stone.natural plus a
# little wall-growth moss; the kit draws moss in flat painted tones, built for the film's painter). On the garden: little patch moss on stones (the add-on's 3D moss and my lichen-rock mix carry
# the weathering), no liverwort, the earth scan already carries real moss so only a little is added.
d['ground']['role_dials']['groundmoss'] = {
    'ground.gravel': {'joint_share': 0.0, 'patch_moss': 0.1, 'algae_fan': 0.0, 'liverwort': 0.0, 'far_band': 0.5, 'moss_lift': 1.0},
    'ground.earth': {'joint_share': 0.0, 'patch_moss': 0.25, 'algae_fan': 0.0, 'liverwort': 0.0, 'far_band': 0.5, 'moss_lift': 1.0},
    'stone.natural': {'joint_share': 0.0, 'patch_moss': 0.12, 'algae_fan': 0.3, 'liverwort': 0.0, 'far_band': 0.0, 'moss_lift': 1.0},
}
# shade follows the lamp (the stage writes the lamp's real direction into toward_sun each run)
d['shade']['mode'] = 'declared_and_openness'
d['shade']['toward_sun'] = d['lighting']['sun_toward']['Golden hour sun']
d['shade']['_note'] = 'GARDEN PATCH 5: was year_sun_and_openness with an assumed north (+y) and latitude 35. Now the declared direction of the sun lamp (weights stay sun 0.6, openness 0.4); stage_surfaces writes the lamp\'s real direction here every run.'
d['looks']['default'] = 'garden_kept'
d['looks']['available'] = ['garden_kept'] + [x for x in d['looks']['available'] if x != 'garden_kept']
d['looks']['_why'] = d['looks'].get('_why', '') + ' GARDEN PATCH 5: default is the garden look.'
json.dump(d, open(p, 'w'), indent=1)

# ---- look: the garden look (3D growth off, nothing wet, weeds near zero)
look = json.load(open(DST + '/presets/mossy_courtyard_kept.json'))
look['id'] = 'garden_kept'
look['note'] = 'GARDEN: mossy_courtyard_kept with the 3D growth layer off (builder 2 owns plants), weeds none, no puddle or water-mark dials. First guesses, tune by eye.'
look['layers']['growth'].update({'amount': 0.0, 'weeds_amount': 0.0, 'cushions_amount': 0.0, 'weed_cover': 0.0, 'cushion_cover': 0.0, 'max_pieces': 0.0})
look['layers']['dirt'].update({'water_marks': 0.15, 'film': 0.35, 'film_max_share': 0.22})
look['layers']['soot'].update({'floor_mult': 0.7})
# moss: darker, greener and less saturated than the first guess (it came out pale lime on the grey stone); lichen discs smaller; less on caps and drips
look['layers']['groundmoss'].update({'moss_value': 0.12})
look['layers']['wallgrowth'].update({'moss_value': 0.11, 'hue': 98.0, 'saturation': 0.5, 'brightness_floor': 0.10, 'cap_moss': 0.3, 'drip_moss': 0.3, 'lichen_dots': 6.0, 'moss_height': 0.4})
json.dump(look, open(DST + '/presets/garden_kept.json', 'w'), indent=1)

# ---- diffs for the record
out = BASE + '/surfaces/out/kit_patch5_diffs.txt'
with open(out, 'w') as f:
    f.write('GARDEN PATCH 5 (builder 3): what differs between ours/kit_patched and surfaces/kit (regenerated by tests/make_kit_edits.py)\n\n')
    for rel in ('apply/roles.py', 'masks/reader.py', 'sets/japanese_courtyard.json'):
        r = subprocess.run(['diff', '-u', '--label', 'a/' + rel, '--label', 'b/' + rel, os.path.join(SRC, rel), os.path.join(DST, rel)], capture_output=True, text=True)
        f.write(r.stdout + '\n')
    f.write('NEW FILE presets/garden_kept.json (copy of mossy_courtyard_kept with growth off, see its note)\n')
print('written', out)
