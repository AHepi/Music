"""What this does: tests the place kit INSIDE Blender, on two small made-up places (a flat hut of plain boxes with a plank that floats, and a yard with sheds, a fence, a well, a barrel
with iron bands, an iron post and a stump on a big flat ground), by running the same commands a model runs: `explainer-film-place audit`, `finish`, `normals-test`, `undo`, `light`.
What it proves, and how (each measurement is read straight from Blender's own data by fixtures/place/probe_place.py, not from the kit's own audit):
  1. The flat hut FAILS the audit and the report names what it lacks and the floating plank; the finished hut passes; a quick trial finishes but is refused as a final.
  2. Every treatment is really there after `finish`: normal maps are OpenGL, Non-Color, wired to the shader and point the right way (and a copy with the green flipped reads wrong, so
     the check is not blind); displacement is set on the roles that need it, on a mesh that can show it; roughness varies and colour varies; edges get a bevel with hardened normals;
     each wear layer (layer dirt, layer grime, layer weathering, layer wetness, layer cracks_and_chips, layer edge_wear, layer moss_and_algae, layer rust, layer rubbish) is in a
     material and has a real amount on an object (an object with no amount reads 0 in every renderer); shape damage makes siblings differ; plants kept out of wheel ruts, the lane's
     centre strip and puddles (counted against the lane's own geometry), while weeds still grow beside the lane.
  3. The wear is controllable and honest: the master at 0 gives EXACTLY the picture with every layer removed (the largest pixel difference is reported); drawing twice gives the
     same picture; each layer on its own changes the picture; layer_off and layer_on put a layer out of and back into every chain.
  4. The pass can be repeated and undone: finishing twice gives the same scene; finishing the same flat scene twice gives the same scene and the same pictures; `undo` puts the
     original materials back and removes everything the kit added.
  5. The lane is real geometry: two ruts about a gauge apart, as deep as the settings say, measured from the ground by rays.
  6. The construction check on small scenes of boxes: seated, floating, a beam on posts, a beam 3 cm short, a rail joined into posts, a rail that barely overlaps, inside out, flicker,
     a door above a gap, a lamp in a solid, a plank that spans too far.
  7. One object with two materials gets two roles; a material that carries its own maps is kept; UVs are in metres; a scene with no light gets one.
  8. Design decision D7 (normal map and displacement together): the relief under a low sun, measured.
Part B (the rented-card and picture tests) is in test_place_render.py and test_picture_measures.py; combining builders is in test_place_combine.py.
Needs Blender (BLENDER, or machine-settings.env, or the PATH); without it the file says so and exits as skipped.
Run: BLENDER=/path/to/blender python3 kit/calculators/tests/test_place_blender.py   (about 4 minutes on a slow machine)
"""
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, FIXTURES, blender_program, skip  # noqa: E402

blender = blender_program()
if not blender:
    skip('place kit inside Blender', 'Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')

PLACE_KIT = os.path.join(KIT, 'place-kit')
LAUNCHER = os.path.join(PLACE_KIT, 'place_command.py')
HUT = os.path.join(FIXTURES, 'place', 'make_hut_scene.py')
YARD = os.path.join(FIXTURES, 'place', 'make_yard_scene.py')
PROBE = os.path.join(FIXTURES, 'place', 'probe_place.py')
check = Checker('place kit inside Blender: audit, finish, treatments, wear, roads, construction, undo')
folder = tempfile.mkdtemp(prefix='place-blender-test-')
environment = {name: value for name, value in os.environ.items() if name not in ('RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_SETTINGS_FILE')}
environment['BLENDER'] = blender
timings = {}


def path(*parts):
    """A file inside the test folder; its own folder is made (every scene gets a folder of its own, so the settings and audit files beside one scene never meet another)."""
    full = os.path.join(folder, *parts)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def blender_run(scene, *script_and_arguments, timeout=900):
    command = [blender, '-b', '--disable-autoexec'] + ([scene] if scene else []) + list(script_and_arguments)
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=environment)


def make_scene(script, name, *options):
    out = path(name, name + '.blend')
    done = blender_run(None, '--python', script, '--', out, *options)
    assert os.path.exists(out), done.stdout[-400:] + done.stderr[-400:]
    return out


def place(verb, scene, *arguments, timeout=900):
    """Runs `explainer-film-place VERB --scene SCENE ...`; returns (exit code, plain output, seconds)."""
    started = time.time()
    done = subprocess.run([sys.executable, '-I', '-B', LAUNCHER, verb, '--scene', scene] + list(arguments), capture_output=True, text=True, timeout=timeout, env=environment)
    return done.returncode, done.stdout + done.stderr, time.time() - started


def probe(scene, name, *extra):
    out = path(f'probe-{name}-{os.path.basename(scene) if scene else "none"}.json')
    done = blender_run(scene, '--python', PROBE, '--', name, out, *extra)
    if not os.path.exists(out):
        raise AssertionError(f'probe {name} wrote nothing: ' + done.stdout[-500:] + done.stderr[-300:])
    with open(out) as handle:
        return json.load(handle)


def lines(text, start):
    return [line for line in text.splitlines() if line.startswith(start)]


# ---------------------------------------------------------------- the scenes
flat_hut = make_scene(HUT, 'flat-hut')
good_hut = make_scene(HUT, 'good-hut', '--no-floating')
yard = make_scene(YARD, 'yard')
with open(path('yard', 'place-settings.json'), 'w') as handle:           # the settings the yard test uses (a lane through the ground); the huts have none and get a draft
    json.dump({'place': 'yard', 'place_type': 'generic', 'look': 'neglected', 'state': 'damp', 'seed': 5,
               'roads': [{'name': 'main lane', 'polyline': [[0, 3], [14, 3], [30, 5]], 'width': 3.0, 'gauge': 1.3, 'rut_depth': 0.08, 'hoof': True}],
               'footfall': [{'shape': 'auto_door_strip', 'role': 'timber.door', 'depth': 1.0, 'width': 1.2}], 'picture': {'camera': 'Camera A', 'height_pixels': 1200}}, handle)
yard_settings = path('yard', 'place-settings.json')

# ---------------------------------------------------------------- 1. flat fails, finished passes, quick is refused
code, text, _ = place('audit', flat_hut)
check.true('the flat hut fails the audit (exit 1)', code == 1, f'exit {code}')
failed = ' '.join(lines(text, 'FAIL'))
for word in ('normal_map', 'displacement', 'dirt', 'grime', 'weathering', 'cracks_and_chips', 'bevelled_edges', 'shape_damage', 'plants', 'litter'):
    check.true(f'the flat hut report names {word}', word in failed.replace('litter pieces', 'litter'), recorded='a hut of plain boxes, made like a model made it from a one-line request')
check.true('the report names the plank that floats and says how to fix it', 'floor_plank_float' in failed and 'seat' in failed.lower(), proves='the construction check can fail (the negative proof)')
audit_file = path('flat-hut', 'place-audit.json')
with open(audit_file) as handle:
    audit = json.load(handle)
check.true('the audit file holds facts only: no overall verdict, no exit code, no list of checks (the plain-Python judge decides, with the house numbers)', not ({'verdict', 'exit', 'checks', 'findings'} & set(audit)))
check.true('the audit records the scene file hash, the settings hash, the Blender version and what was measured', all(k in audit for k in ('scene_sha1', 'settings_sha1', 'blender', 'materials', 'objects', 'normal_maps', 'scatter', 'roads', 'light', 'renderer')))

code, text, seconds = place('finish', good_hut, '--save-as', path('good-hut', 'finished.blend'))
timings['finish, hut, full size'] = seconds
check.equal('the good hut finishes and passes the audit at full size (exit 0)', code, 0)
check.true(f'finishing the hut takes {seconds:.1f} s (full size: 1024 px maps, 0.1 m masks)', seconds < 120, f'{seconds:.1f} s')
check.true('every step reports a plain PASS line (roles, roads, surfaces, damage, plan masks, wear, growth, light)', all(any(line.startswith(f'PASS {step}') for line in text.splitlines()) for step in ('roles', 'roads', 'surfaces', 'damage', 'plan masks', 'wear', 'growth', 'light')))
check.true('it ends by saying what to run next (the preflight place stage)', any(line.startswith('NEXT run: explainer-film-preflight place') for line in text.splitlines()))
finished_hut = path('good-hut', 'finished.blend')
code, text, seconds = place('finish', good_hut, '--quick', '--save-as', path('quick-hut', 'quick.blend'))
timings['finish, hut, quick'] = seconds
check.true('a quick trial finishes but is refused as a final by the audit (exit 1) and the line says "quick"', code == 1 and any('quick' in line for line in lines(text, 'FAIL')), f'exit {code}')
code, _, _ = place('audit', path('quick-hut', 'quick.blend'), '--allow-quick')
check.equal('the same quick scene is accepted as a trial with --allow-quick', code, 0)

# ---------------------------------------------------------------- 2. the treatments are really there
facts_hut = probe(finished_hut, 'facts')
code, text, seconds = place('finish', yard, '--settings', yard_settings, '--save-as', path('yard', 'finished.blend'))
timings['finish, yard (36 x 26 m ground, 41 objects, one lane), full size'] = seconds
check.true('the yard finishes and passes the audit (exit 0 or a LOOK-only warning)', code == 0, f'exit {code}: ' + ' '.join(lines(text, 'FAIL'))[:200])
yard_finished = path('yard', 'finished.blend')
facts = probe(yard_finished, 'facts')
kit_materials = [(o['name'], m) for o in facts['objects'] if not o['scatter'] for m in o['materials'] if m['name'].startswith('PK ')]
check.true('every visible object has a kit material (not a plain colour any more)', all(o['materials'] and o['materials'][0]['name'].startswith('PK ') for o in facts['objects'] if not o['scatter']), f'{len(kit_materials)} slots')

directions = probe(yard_finished, 'directions')
partnered = [i for i in directions['images'] if i['partner']]
true_fine = all(any(isinstance(v, float) and v >= 0.25 for v in (i['true']['x'], i['true']['y'])) and not any(isinstance(v, float) and v < 0.25 for v in (i['true']['x'], i['true']['y'])) for i in partnered)
flipped_caught = all(any(isinstance(v, float) and v < -0.25 for v in (i['green_flipped']['x'], i['green_flipped']['y'])) for i in partnered if isinstance(i['true']['y'], float))
colourspaces = {i['colourspace'] for i in facts['normal_images']}
check.true('normal maps are OpenGL: every map the kit made agrees with its own height (correlation at least +0.25 on every axis that has a slope)', len(partnered) >= 8 and true_fine, f'{len(partnered)} maps checked against their height pictures',
           recorded='place_surfaces.normal_direction_correlation_min = 0.25', proves='the red and green channels point the way Blender\'s Normal Map node expects')
check.true('...and a copy of each with its green channel flipped reads wrong on y (the control is not blind)', flipped_caught)
check.equal('...and every normal map is a Non-Color picture', colourspaces, {'Non-Color'})
check.true('...and every kit material has a Normal Map node fed by the picture and wired to the shader\'s Normal', all(m['normal_map_wired'] and m['normal_picture_colourspace'] == 'Non-Color' for _, m in kit_materials), str([m['name'] for _, m in kit_materials if not m['normal_map_wired']]))
ground = [(o, m) for o in facts['objects'] for m in o['materials'] if (o['role'] or '').startswith('ground.')]
check.true('displacement is set on the ground (a Displacement node on the output, method Displacement and Bump)', ground and all(m['displacement_node'] and m['displacement_method'] == 'BOTH' for _, m in ground), str([(o['name'], m['displacement_method']) for o, m in ground]))
check.true('...on a ground mesh fine enough to show it (a graded or uniform grid of thousands of faces, not a flat plane)', all(o['faces'] > 5000 for o, _ in ground), str([o['faces'] for o, _ in ground]))
walls_and_roofs = [m for o in facts['objects'] for m in o['materials'] if (o['role'] or '').split('.')[0] in ('wall', 'roof', 'timber', 'iron', 'stone') and not o['scatter']]
check.true('roughness varies (the Roughness input is fed by a texture, not one number) on every wall, roof, timber, iron and stone material', all(m['roughness_varies'] for m in walls_and_roofs))
check.true('colour varies (the Base Color input is fed by noise or a colour ramp, not one colour) on every one of them', all(m['colour_varies'] for m in walls_and_roofs))
bevelled = [o for o in facts['objects'] if (o['role'] or '').split('.')[0] in ('wall',) or o['role'] in ('timber.door', 'timber.post')]
check.true('bevel: walls, doors and posts have a Bevel modifier and a Weighted Normal modifier (hardened edges, clean shading)', bevelled and all({'BEVEL', 'WEIGHTED_NORMAL'} <= {m[0] for m in o['modifiers']} for o in bevelled), str([o['name'] for o in bevelled if 'BEVEL' not in {m[0] for m in o['modifiers']}]))
by_layer = {}
for o in facts['objects']:
    if o['scatter']:
        continue
    for m in o['materials']:
        for group in m['wear_groups']:
            by_layer.setdefault(group, []).append(o)
LAYER_GROUPS = {'dirt': 'PK Dirt', 'grime': 'PK Grime', 'weathering': 'PK Weathering', 'wetness': 'PK Wetness', 'cracks_and_chips': 'PK Cracks And Chips', 'edge_wear': 'PK Edge Wear',
                'moss_and_algae': 'PK Moss And Algae', 'rust': 'PK Rust', 'rubbish': 'PK Rubbish'}
check.true('layer dirt is in a material and has an amount above 0 on the objects that use it', 'PK Dirt' in by_layer and all(o['amounts'].get('dirt', 0) > 0 for o in by_layer['PK Dirt']))
check.true('layer grime is in a material and has an amount above 0 on the objects that use it', 'PK Grime' in by_layer and all(o['amounts'].get('grime', 0) > 0 for o in by_layer['PK Grime']))
check.true('layer weathering is in a material and has an amount above 0 on the objects that use it', 'PK Weathering' in by_layer and all(o['amounts'].get('weathering', 0) > 0 for o in by_layer['PK Weathering']))
check.true('layer wetness is in a material and has an amount above 0 on the objects that use it (the yard is damp)', 'PK Wetness' in by_layer and all(o['amounts'].get('wetness', 0) > 0 for o in by_layer['PK Wetness']))
check.true('layer cracks_and_chips is in a material and has an amount above 0 on the objects that use it', 'PK Cracks And Chips' in by_layer and all(o['amounts'].get('cracks_and_chips', 0) > 0 for o in by_layer['PK Cracks And Chips']))
check.true('layer edge_wear is in a material and has an amount above 0 on the objects that use it', 'PK Edge Wear' in by_layer and all(o['amounts'].get('edge_wear', 0) > 0 for o in by_layer['PK Edge Wear']))
check.true('layer moss_and_algae is in a material and has an amount above 0 on the objects that use it', 'PK Moss And Algae' in by_layer and all(o['amounts'].get('moss_and_algae', 0) > 0 for o in by_layer['PK Moss And Algae']))
rust_objects = by_layer.get('PK Rust', [])
check.true('layer rust is in the iron materials (and only on iron) and has an amount above 0', rust_objects and all((o['role'] or '').startswith('iron.') and o['amounts'].get('rust', 0) > 0 for o in rust_objects), str([o['name'] for o in rust_objects]))
check.true('layer rubbish is in a material and has an amount above 0 on the objects that use it', 'PK Rubbish' in by_layer and all(o['amounts'].get('rubbish', 0) > 0 for o in by_layer['PK Rubbish']))
originals = set(facts['fake_users'])
check.true('the original plain materials are kept with a fake user (a material nothing uses is dropped when a file is saved)', {'wall_mat', 'roof_mat', 'ground_mat', 'door_mat', 'iron_mat', 'wood_mat', 'stone_mat', 'bark_mat'} <= originals, str(sorted(originals))[:160])

damage = probe(yard_finished, 'damage')['roles']
siblings = {role: info for role, info in damage.items() if info['count'] >= 4}
check.true('shape damage: siblings of one role (posts, rails, walls) are no longer exact copies (at least 80 percent have a shape of their own)', siblings and all(info['distinct_shapes'] / info['count'] >= 0.8 for info in siblings.values()),
           ', '.join(f'{role} {info["distinct_shapes"]} of {info["count"]}' for role, info in siblings.items()))
check.true('...every wall, post and plank carries a damage modifier with a strength of a few millimetres to a few centimetres', all(info['with_damage'] == info['count'] and 0.001 <= min(info['strengths_m']) and max(info['strengths_m']) <= 0.12 for role, info in damage.items() if role.split('.')[0] in ('wall', 'timber')),
           str({r: i['strengths_m'] for r, i in damage.items() if r.split('.')[0] in ('wall', 'timber')})[:200])
check.true('...and damage does not lift anything off the ground (every lowest point is within 6 cm of where it was seated)', all(info['max_lowest_z_error_m'] < 0.06 for info in damage.values()), str({r: round(i['max_lowest_z_error_m'], 3) for r, i in damage.items() if i['max_lowest_z_error_m'] >= 0.03}))

# ---------------------------------------------------------------- 5. the lane and plants kept out
roads = probe(yard_finished, 'roads', '--settings', yard_settings)
lane = roads['roads'][0]
check.true('the lane is real geometry: ruts measured from the ground by rays are about as deep as the settings say (within 40 percent of 8 cm)', abs(lane['depth_median_m'] - lane['rut_depth_in_settings_m']) <= 0.4 * lane['rut_depth_in_settings_m'],
           f'median {lane["depth_median_m"] * 100:.1f} cm, settings {lane["rut_depth_in_settings_m"] * 100:.0f} cm (from {lane["depth_min_m"] * 100:.1f} to {lane["depth_max_m"] * 100:.1f})')
check.close('...and the two ruts are a gauge apart (1.3 m, within 15 cm)', lane['gauge_median_m'], 1.3, 0.15)
counts = lane['roots']
check.equal('plants kept out: no plant or litter piece stands in a wheel rut (counted from the lane\'s own geometry)', counts['in_rut_core'], 0, recorded='exact-zero gate on the wheel-track mask')
check.equal('plants kept out: ...none within 2 cm of a rut edge', counts['in_rut_band'], 0)
check.equal('plants kept out: ...none in the trodden centre strip of the lane', counts['in_centre_strip'], 0)
check.true('...but weeds do grow beside the lane and across the yard (the gates are not "no plants at all")', counts['near_lane_outside'] >= 15 and counts['elsewhere'] >= 100 and roads['groups'].get('plant', 0) >= 100 and roads['groups'].get('litter', 0) >= 100,
           f'near the lane {counts["near_lane_outside"]}, elsewhere {counts["elsewhere"]}, plants {roads["groups"].get("plant")}, litter {roads["groups"].get("litter")}')
with open(path('yard', 'place-audit.json')) as handle:
    yard_audit = json.load(handle)
check.true('the audit\'s own recount agrees (every scatter group has 0 on a track, a crown, a puddle, a keep-out and within 5 cm of litter)', all(g[k] == 0 for g in yard_audit['scatter']['groups'] for k in ('in_keepout', 'in_puddle', 'on_crown', 'on_wheel_track', 'within_5cm_of_litter')))
check.true('the audit measured the ruts itself (ruts found, depth and gauge recorded)', yard_audit['roads'] and yard_audit['roads'][0]['ruts_found'] is True and abs(yard_audit['roads'][0]['gauge_m'] - 1.3) < 0.2)

# ---------------------------------------------------------------- 3. dial zero, determinism, isolation, layers off and on
damp_hut = path('damp-hut', 'damp.blend')
code, _, seconds = place('finish', good_hut, '--look', 'neglected', '--state', 'damp', '--save-as', damp_hut)
renders = probe(damp_hut, 'renders', '--size', '192', '128', '--samples', '8')
timings['five tiny Cycles pictures of the hut (192 x 128, 8 samples)'] = None
check.equal('dial zero: with the master at 0 the picture is EXACTLY the picture with every layer removed (largest pixel difference)', renders['max_difference_master_zero_vs_removed'], 0.0,
            recorded=f'measured here: {renders["max_difference_master_zero_vs_removed"]}; the same picture drawn from the same scene')
check.equal('determinism: drawing the same scene twice gives the same picture (largest pixel difference)', renders['max_difference_as_it_is_vs_again'], 0.0)
check.true('the wear changes the picture (mean pixel change at least 3 percent of the mean brightness)', renders['mean_difference_as_it_is_vs_removed'] >= 0.03 * renders['mean_brightness_removed'],
           f'{renders["mean_difference_as_it_is_vs_removed"] / renders["mean_brightness_removed"]:.1%} of the brightness')
alone = renders['mean_difference_only_one_layer_vs_removed']
check.true('isolation: each of dirt, grime, weathering, wetness and moss_and_algae on its own changes the picture', all(alone.get(layer, 0) > 1e-5 for layer in ('dirt', 'grime', 'weathering', 'wetness', 'moss_and_algae')), str({k: round(v, 6) for k, v in alone.items()}))
check.true('...and every layer that is in is a layer of the chain, never a stray', set(alone) <= set(LAYER_GROUPS))
layer_test = r'''
import bpy, sys, os
HERE = os.path.dirname(%r)
sys.path.insert(0, %r); sys.path.insert(0, %r)
from place_kit import commands
from place_kit.wear import door
settings = commands.read_settings(None)
commands.tag_roles(settings, write=False, fallback=True)
wear = door.age_place(settings, look='neglected', state='damp')
def count(group):
    return sum(1 for m in bpy.data.materials for n in m.node_tree.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith(group)) if True else 0
before = count('PK Dirt')
wear.layer_off('dirt')
off = count('PK Dirt')
wear.layer_on('dirt')
back = count('PK Dirt')
wear.set_state('dry')
dry_amount = max(o.get('pk_wetness_amount', 0) for o in bpy.data.objects)
wear.set_state('wet')
wet_amount = max(o.get('pk_wetness_amount', 0) for o in bpy.data.objects)
try:
    wear.set_dials('dirt', no_such_dial=1)
    message = ''
except KeyError as problem:
    message = str(problem)
print('LAYERTEST', before, off, back, dry_amount, wet_amount, message[:80])
''' % (PROBE, os.path.join(PLACE_KIT), os.path.join(KIT, 'calculators'))
script_path = path('scripts', 'layer-test.py')
open(script_path, 'w').write(layer_test)
done = blender_run(damp_hut, '--python', script_path)
row = [line for line in done.stdout.splitlines() if line.startswith('LAYERTEST')]
parts = row[0].split(' ', 6) if row else []
check.true('layer_off takes a layer out of every chain and layer_on puts it back', len(parts) >= 4 and int(parts[1]) > 0 and int(parts[2]) == 0 and int(parts[3]) == int(parts[1]), row[0] if row else done.stdout[-300:] + done.stderr[-300:])
check.true('set_state moves the wetness amount (dry gives 0, wet gives more than damp) and a dial name that does not exist is an error, not silent', len(parts) >= 6 and float(parts[4]) == 0.0 and float(parts[5]) > 0.6 and 'no dial' in row[0], row[0] if row else '')

# ---------------------------------------------------------------- 4. finishing twice, determinism, undo
again = path('twice', 'twice.blend')
place('finish', finished_hut, '--save-as', again)
first = path('fingerprints', 'first.json')
second = path('fingerprints', 'second.json')
place('fingerprint', finished_hut, '--out', first)
place('fingerprint', again, '--out', second)
with open(first) as handle:
    one = json.load(handle)
with open(second) as handle:
    two = json.load(handle)
same_objects = set(one['objects']) == set(two['objects']) and all(one['objects'][n].get(k) == two['objects'][n].get(k) for n in one['objects'] for k in ('mesh', 'matrix', 'slots', 'role', 'owner'))
check.true('finishing twice gives the same scene: the same objects, shapes, places, materials and roles', same_objects, str(sorted(set(one['objects']) ^ set(two['objects'])))[:200])
check.equal('...and the same materials and node groups (by name)', (sorted(one['materials']), sorted(one['node_groups'])), (sorted(two['materials']), sorted(two['node_groups'])))
other = path('again-b', 'again-b.blend')
place('finish', good_hut, '--save-as', other)
pictures_a = probe(finished_hut, 'images')['images']
pictures_b = probe(other, 'images')['images']
check.true('determinism: finishing the same flat scene twice gives the same pictures (every kit picture has the same pixels)', pictures_a == pictures_b and len(pictures_a) >= 8, f'{len(pictures_a)} pictures')
undone = path('undone', 'undone.blend')
code, text, _ = place('undo', finished_hut, '--save-as', undone)
facts_undone = probe(undone, 'facts')
check.equal('undo: the original plain materials are back in every slot', sorted({m['name'] for o in facts_undone['objects'] for m in o['materials']}), ['door_mat', 'floor_mat', 'ground_mat', 'roof_mat', 'wall_mat'])
names_before = sorted(o['name'] for o in probe(good_hut, 'facts')['objects'])
check.true('undo: every object the builder made is still there and nothing the kit made is left (no scatter pieces, no modifiers, no wear amounts)', not any(o['scatter'] for o in facts_undone['objects']) and all(not o['modifiers'] and not o['amounts'] for o in facts_undone['objects']) and sorted(o['name'] for o in facts_undone['objects']) == names_before, f'{len(names_before)} objects before, {len(facts_undone["objects"])} after')
check.true('undo: the kit\'s pictures are gone', not probe(undone, 'images')['images'])

# ---------------------------------------------------------------- 6. the construction check on small scenes
cases = probe(None, 'constructions')['cases']


def one_fact(case, name):
    return cases[case][name]


check.true('construction: a seated box is carried and does not float', one_fact('a seated box', 'wall A')['carried'] and not one_fact('a seated box', 'wall A')['floating'])
check.true('construction: a plank 6 cm above the ground floats, with a gap of about 60 mm', one_fact('a plank 6 cm above the ground', 'plank float')['floating'] and abs(one_fact('a plank 6 cm above the ground', 'plank float')['gap_mm'] - 60) < 5)
check.true('construction: a plank 3 mm above the ground is within the tolerance and does not float', not one_fact('a plank 3 mm above the ground', 'plank low')['floating'])
beam = one_fact('a beam resting on two posts', 'beam 1')
check.true('construction: a beam resting on two posts is carried, not hung, and its free span is inside the limit', beam['carried'] and not beam['hung'] and beam['span_max_m'] < beam['max_span_m'], f'span {beam["span_max_m"]} m of {beam["max_span_m"]}')
short = cases['a beam 3 cm above two posts']
check.true('construction: a beam 3 cm above two posts floats AND each post is called short by about 30 mm', short['beam 1']['floating'] and abs(short['post 1']['short_by_mm'] - 30) < 3 and abs(short['post 2']['short_by_mm'] - 30) < 3)
rail = one_fact('a fence rail joined 6 cm into two posts', 'rail 1')
check.true('construction: a fence rail joined into two posts is framed in: carried through them, not called hung', rail['carried'] and rail['framed'] and not rail['hung'])
joined = one_fact('a beam (which may not hang) joined into two posts', 'beam 1')
check.true('construction: a beam (a role that may not hang) joined 5 cm into the sides of two posts is framed in and carried, not "hangs from above" (correct joinery is not a failure)', joined['carried'] and joined['framed'] and not joined['hung'] and not joined['hang_allowed'],
           recorded='the smoke check of the canal lock gate: rails tenoned into both posts read as hung', proves='a tenoned frame needs no may-hang role')
one_post = one_fact('a beam joined into only one post', 'beam 1')
check.true('construction: a beam joined into only ONE post, its other end in the air, is still called hung and not allowed', one_post['hung'] and not one_post['hang_allowed'] and not one_post['framed'])
bedded = one_fact('a beam bedded 6 mm into two posts', 'beam 1')
check.true('construction: a beam bedded 6 mm into the tops of its posts rests on them (not "floats"), and the facts say how far it sits in', bedded['carried'] and not bedded['floating'] and 5.0 <= bedded['sunk_in_mm'] <= 7.0, f'sunk in {bedded["sunk_in_mm"]} mm',
           recorded='place_construction.sunk_in_centimetres_max = 4 (invented)', proves='a part set a little into its carrier is not failed with the distance to the next thing below')
check.true('construction: a stake driven 10 cm into the top of a post is carried by it', one_fact('a stake driven 10 cm into a post top', 'stake 1')['carried'])
mirrored = cases['a mirrored wall (scale -1) with a roof resting on it']
check.true('construction: a wall with a negative scale is not "inside out", its faces do not flicker, and the roof on it does not float', not mirrored['wall A']['inside_out'] and not mirrored['wall A']['coplanar_faces'] and mirrored['roof 1']['carried'] and not mirrored['roof 1']['floating'])
afloat = one_fact('a boat afloat through the water plane', 'hull 1')
check.true('construction: a hull that goes down through the water plane and out above it is carried by the water', afloat['carried'] and not afloat['floating'] and afloat['afloat_on'] == 'sea', str(afloat['afloat_on']))
check.true('construction: a hull hovering 3 cm above the water still floats (the water carries only what stands in it)', one_fact('a boat hovering 3 cm above the water', 'hull 1')['floating'])
flight = cases['a flight of solid step blocks of 17 cm rise']
check.true('construction: a flight of solid step blocks reads a rise of 17 cm for every step (top to top), not each block\'s height from the bed', all(abs(flight[n]['rise_m'] - 0.17) < 0.005 for n in ('step 1', 'step 2', 'step 3')), str({n: flight[n]['rise_m'] for n in flight}))
check.true('construction: a 17 cm slab on a stone core reads a rise of 17 cm', abs(one_fact('a 17 cm slab on a stone core', 'step 1')['rise_m'] - 0.17) < 0.005)
check.true('construction: one solid block 1.83 m high called a step reads a rise of 1.83 m (it is not a step)', abs(one_fact('one solid block 1.83 m high called a step', 'step 1')['rise_m'] - 1.83) < 0.01)
for case_name in ('a wall on the bed beside higher ground, its box edge 4 mm over it', 'a wall whose box reaches past the end of the ground'):
    wall = cases[case_name]['quay wall']
    check.true(f'construction: {case_name}: seated on the bed, no seat error, and the check names the ground it measured against', wall['carried'] and abs(wall['seat_error_m']) < 0.02 and wall['seat_ground_object'] == 'Ground' and abs(wall['seat_ground_m'] + 2.0) < 0.01,
               f'seat error {wall["seat_error_m"]}, ground {wall["seat_ground_object"]} at {wall["seat_ground_m"]}')
    check.true(f'   (control: the way it used to be read, from the raw box corners with 0.0 where there is no ground, says {cases[case_name]["_old_way"]["old_error_m"]} m)', abs(cases[case_name]['_old_way']['old_error_m'] + 2.0) < 0.05,
               proves='the scene really holds the trap, so the pass above is not blind')
check.true('construction: a rail with only 2 cm inside its post is NOT joined (it floats)', one_fact('a rail with only 2 cm inside its post', 'rail 1')['floating'])
check.true('construction: a closed box turned inside out is found', one_fact('a closed box turned inside out', 'box out')['inside_out'])
check.true('construction: two planks with the same top plane flicker (coplanar faces found)', one_fact('two planks with the same top plane', 'plank A')['coplanar_faces'] >= 2)
check.true('construction: a door whose sill is 60 cm above the ground has no floor close below it', abs(one_fact('a door whose sill is 60 cm above the ground', 'door 1')['opening_floor_gap_m'] - 0.6) < 0.03)
check.true('construction: a plank spanning 2.5 m between two blocks has a free span of about 2.5 m (over its 1.38 m limit)', abs(one_fact('a plank spanning 2.5 m between two blocks', 'plank long')['span_max_m'] - 2.5) < 0.15 and one_fact('a plank spanning 2.5 m between two blocks', 'plank long')['span_max_m'] > one_fact('a plank spanning 2.5 m between two blocks', 'plank long')['max_span_m'])
check.true('construction: a lamp inside a solid is found', one_fact('a lamp inside a solid', 'Lamp')['buried_light'])

# ---------------------------------------------------------------- 7. one object with two materials, own maps kept, UVs in metres, light, renderer
two_materials = r'''
import bpy, bmesh, sys
sys.path.insert(0, %r); sys.path.insert(0, %r)
from place_kit import commands, names
bpy.ops.wm.read_factory_settings(use_empty=True)
def material(name, colour):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = colour; return m
def box(name, size, location, materials):
    mesh = bpy.data.meshes.new(name); b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts: v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    for f in b.faces: f.material_index = 1 if f.normal.z > 0.5 else 0
    b.to_mesh(mesh); b.free()
    for m in materials: mesh.materials.append(m)
    o = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(o); o.location = location; return o
ground = bpy.data.meshes.new('Ground'); ground.from_pydata([(-6,-6,0),(6,-6,0),(6,6,0),(-6,6,0)], [], [(0,1,2,3)]); ground.materials.append(material('ground colour', (.3,.25,.15,1)))
bpy.context.scene.collection.objects.link(bpy.data.objects.new('Ground', ground))
box('Prop barrel 1', (0.7, 0.7, 0.9), (0, 0, 0.45), [material('oak staves', (.4,.3,.2,1)), material('iron band', (.2,.2,.22,1))])
painted = material('painted by hand', (.7,.2,.2,1))
tex = painted.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.new('hand_painted_map', 8, 8)
painted.node_tree.links.new(tex.outputs['Color'], painted.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
box('Prop crate 1', (0.6, 0.6, 0.6), (2, 0, 0.3), [painted])
bpy.ops.wm.save_as_mainfile(filepath=%r)
''' % (PLACE_KIT, os.path.join(KIT, 'calculators'), path('two-materials', 'two-materials.blend'))
script_path = path('scripts', 'two-materials.py')
open(script_path, 'w').write(two_materials)
blender_run(None, '--python', script_path)
with open(path('two-materials', 'place-settings.json'), 'w') as handle:
    json.dump({'roles': [{'role': 'iron.fitting', 'match': {'materials': ['^iron band']}}], 'look': 'lived_in'}, handle)
code, text, _ = place('surfaces', path('two-materials', 'two-materials.blend'), '--save-as', path('two-materials-done', 'done.blend'), '--quick')
facts_two = probe(path('two-materials-done', 'done.blend'), 'facts')
barrel = next(o for o in facts_two['objects'] if o['name'] == 'Prop barrel 1')
crate = next(o for o in facts_two['objects'] if o['name'] == 'Prop crate 1')
slot_names = [m['name'] for m in barrel['materials']]
check.true('one object with two materials gets two roles: the staves a barrel\'s wood, the band iron', len(slot_names) == 2 and slot_names[0].startswith('PK prop.barrel') and slot_names[1].startswith('PK iron.fitting'), str(slot_names))
check.true('a material that carries its own picture (hand painted) is kept, not replaced', [m['name'] for m in crate['materials']] == ['painted by hand'], str([m['name'] for m in crate['materials']]))
uvs = probe(yard_finished, 'uvs')['objects']
walls = [o for o in uvs if (o['role'] or '').startswith('wall.')]
ok_uv = all(max(o['uv_extent']) >= 0.9 * max(o['size_metres']) and max(o['uv_extent']) <= 1.6 * max(o['size_metres']) for o in walls)
check.true('UVs are in metres: the biggest side of every wall box has a UV extent about its real size (0.9 to 1.6 times)', walls and ok_uv, str([(o['name'], [round(v, 2) for v in o['uv_extent']], [round(v, 2) for v in o['size_metres']]) for o in walls[:3]]))
nolight = make_scene(HUT, 'no-light-hut', '--no-floating', '--no-light')
code, text, _ = place('light', nolight, '--save-as', path('lit-hut', 'lit.blend'))
lit = blender_run(path('lit-hut', 'lit.blend'), '--python-expr', 'import bpy; print("LIGHTS", sorted(o.data.type for o in bpy.data.objects if o.type == "LIGHT"), bpy.context.scene.world is not None)')
check.true('a scene with no light gets one: `light` adds a sun and more, and says so', code == 0 and 'LIGHTS' in lit.stdout and "'SUN'" in lit.stdout, lit.stdout.strip().splitlines()[-2] if lit.stdout.strip() else '')
code, text, _ = place('renderer-for', yard_finished)
check.true('renderer-for says EEVEE with its reason for a daylight yard, and the exit code is 0', code == 0 and 'EEVEE' in text.splitlines()[0], text.splitlines()[0] if text else '')
code, text, _ = place('finish-part', good_hut, '--owner', 'nobody', '--quick', '--save-as', path('owned', 'owned.blend'))
check.true('finish-part with an owner that owns nothing touches no object (the hut stays plain boxes)', not any(m['name'].startswith('PK ') for o in probe(path('owned', 'owned.blend'), 'facts')['objects'] if not o['scatter'] and not (o['role'] or '').startswith('ground.') for m in o['materials']))

# ---------------------------------------------------------------- the normals test with a deliberate fault
flip_script = r'''
import bpy, numpy as np
image = bpy.data.images['pk_plaster_lime_nor']
pixels = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
image.pixels.foreach_get(pixels)
pixels = pixels.reshape(-1, 4)
pixels[:, 1] = 1.0 - pixels[:, 1]
image.pixels.foreach_set(pixels.ravel())
image.update()
image.pack()
bpy.ops.wm.save_as_mainfile(filepath=%r)
''' % path('flipped', 'flipped.blend')
script_path = path('scripts', 'flip.py')
open(script_path, 'w').write(flip_script)
blender_run(finished_hut, '--python', script_path)
code_good, text_good, seconds_good = place('normals-test', finished_hut)
timings['normals-test (every map against its height, and the test light)'] = seconds_good
code_bad, text_bad, _ = place('normals-test', path('flipped', 'flipped.blend'))
check.equal('normals-test passes the kit\'s own maps (exit 0)', code_good, 0)
check.true('normals-test FAILS a normal map whose green channel was flipped by hand (exit 1) and names the picture', code_bad == 1 and 'pk_plaster_lime_nor' in text_bad, text_bad.strip().splitlines()[-1][:160] if text_bad.strip() else f'exit {code_bad}')

# ---------------------------------------------------------------- 8. D7: normal map and displacement together
low = {surface: probe(None, 'lowangle', '--size', '256', '256', '--samples', '16', '--surface', surface) for surface in ('packed_earth', 'dirt_road')}
for surface, result in low.items():
    check.true(f'D7 low-angle test ({surface}): displacement with the normal strength at 0.6 does not double the relief (at most 1.3 times the larger of the two alone)', result['ratio_both_to_larger_single'] <= 1.3,
               f'{result["ratio_both_to_larger_single"]:.2f}; normal alone {result["normal_map_alone"]["relief_contrast"]:.2f}, displacement alone {result["displacement_alone"]["relief_contrast"]:.2f}, both {result["both_normal_at_0_6"]["relief_contrast"]:.2f}, both with the normal at full strength {result["both_normal_at_full"]["relief_contrast"]:.2f}',
               recorded='measured here (a flat 120 x 120 plane, sun 10 degrees above it, Cycles on the processor, 16 samples)')
    check.true(f'D7 ({surface}): even at full normal strength the pair is under twice the normal map alone (so no doubling was found at either strength)', result['ratio_both_full_normal_to_normal_alone'] < 2.0, f'{result["ratio_both_full_normal_to_normal_alone"]:.2f}')

check.note('timings measured here (seconds on this computer, Blender ' + ', '.join(f'{name}: {value:.1f}' if value else name for name, value in timings.items()) + ')')
check.finish()
