"""What this does: tests, inside Blender, every fault that the 1.4.0 smoke check, the code review and the newcomer judge found in the place kit and that the 1.4.0 fix round repaired. Each fault gets a
small made-up scene (fixtures/place/make_fix_scenes.py) and is checked against Blender's own data (fixtures/place/probe_fixes.py), and where the fault was a gate that let something through,
the same gate must still fail the planted fault (the negative proof). The faults:
  1. objects with no material at all passed the audit (the blocking hole): the audit must fail them by name, and `finish` must repair them;
  2. a curved lane strip was reshaped into a rectangle and a lane with a trench cut in it had the trench filled in (and the steps in it moved 2 m): neither may happen;
  3. a plain request got no ruts: a dirt-road object with no road in the settings gets a road drafted from its own shape, and the settings file says so;
  4. curves, text and instanced collections escaped the whole pass: they are turned into meshes (and undo brings the originals back);
  5. a lettered sign (a material with its own picture) failed the audit for ever: it keeps its picture and gets roughness and a normal map, and undo takes those out;
  6. `undo` crashed on a scene where the kit itself added the sun; `finish` crashed on an empty scene; `finish` found out only at the end that it had nowhere to save;
  7. `finish-part` always failed; a world colour alone counted as light; the audit now says when only the world lights a scene;
  8. a wall turned 45 degrees was size-checked by its box along the world axes;
  9. water was a solid prop (it shaded the seabed) and wet nothing beside it; and the renderer rule now says Cycles where water is in view.
Needs Blender (BLENDER, or machine-settings.env, or the PATH); without it the file says so and exits as skipped.
Run: BLENDER=/path/to/blender python3 kit/calculators/tests/test_place_fixes.py   (about 3 minutes on a slow machine)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, FIXTURES, blender_program, skip  # noqa: E402

blender = blender_program()
if not blender:
    skip('place kit fixes inside Blender', 'Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')

PLACE_KIT = os.path.join(KIT, 'place-kit')
LAUNCHER = os.path.join(PLACE_KIT, 'place_command.py')
FIX_SCENES = os.path.join(FIXTURES, 'place', 'make_fix_scenes.py')
PROBE = os.path.join(FIXTURES, 'place', 'probe_fixes.py')
HUT = os.path.join(FIXTURES, 'place', 'make_hut_scene.py')
check = Checker('place kit fixes inside Blender: the faults of the smoke check, the review and the newcomer judge')
folder = tempfile.mkdtemp(prefix='place-fixes-test-')
environment = {name: value for name, value in os.environ.items() if name not in ('RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_SETTINGS_FILE')}
environment['BLENDER'] = blender


def path(*parts):
    full = os.path.join(folder, *parts)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def place(verb, scene, *arguments, timeout=900):
    """Runs `explainer-film-place VERB --scene SCENE ...`; returns (exit code, plain output, seconds)."""
    started = time.time()
    command = [sys.executable, '-I', '-B', LAUNCHER, verb] + (['--scene', scene] if scene else []) + list(arguments)
    done = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=environment)
    return done.returncode, done.stdout + done.stderr, time.time() - started


def probe(scene, name):
    out = path(f'probe-{name}-{os.path.basename(os.path.dirname(scene))}-{os.path.basename(scene)}.json')
    done = subprocess.run([blender, '-b', '--disable-autoexec', scene, '--python', PROBE, '--', name, out], capture_output=True, text=True, timeout=600, env=environment)
    if not os.path.exists(out):
        raise AssertionError(f'probe {name} wrote nothing: ' + done.stdout[-400:] + done.stderr[-300:])
    with open(out) as handle:
        return json.load(handle)


def lines(text, start):
    return [line for line in text.splitlines() if line.startswith(start)]


def own_copy(name, folder_name=None):
    """The scene as a file in a folder of its own (settings and audit files made beside it never meet another scene)."""
    target = path(folder_name or name, name + '.blend')
    shutil.copy(os.path.join(scenes, name + '.blend'), target)
    return target


scenes = path('scenes', 'x')
scenes = os.path.dirname(scenes)
made = subprocess.run([blender, '-b', '--disable-autoexec', '--python', FIX_SCENES, '--', scenes], capture_output=True, text=True, timeout=300, env=environment)
assert os.path.exists(os.path.join(scenes, 'lazy.blend')), made.stdout[-400:] + made.stderr[-400:]

# ---------------------------------------------------------------- 1. objects with no material at all
lazy = own_copy('lazy')
code, text, _ = place('audit', lazy)
failed = ' '.join(lines(text, 'FAIL'))
check.equal('objects with NO material at all (bevels and shape damage put on by hand) FAIL the audit (exit 1)', code, 1,
            recorded='the smoke check of the canal lock: a scene with no material passed with zero normal maps, zero wear and zero weeds',
            proves='the gate that used to let a materialless scene through now fails it')
check.true('...and the report names the objects and what they lack (normal_map, dirt, grime, weathering)', all(word in failed for word in ('Cottage wall 1', 'Prop barrel 1', 'normal_map', 'dirt', 'grime', 'weathering')), failed[:200])
check.true('...and says the ground gets no plants and no litter even though it has no material', 'no plants on the ground' in failed and 'no litter pieces on the ground' in failed)
code, text, _ = place('finish', lazy, '--save-as', path('lazy-done', 'done.blend'))
check.equal('`finish` repairs it: the same scene passes after the pass (exit 0)', code, 0, proves='the audit is not simply failing everything')

# ---------------------------------------------------------------- 2. a curved lane, and a lane with a trench cut in it (also: a plain request gets ruts)
lanes = own_copy('lanes')
code, text, seconds = place('finish', lanes, '--save-as', path('lanes-done', 'done.blend'))
check.equal('a curved lane strip with no settings file finishes and passes (exit 0)', code, 0, f'{seconds:.0f} s')
settings_written = json.load(open(path('lanes', 'place-settings.json')))
roads = settings_written.get('roads') or []
check.true('a plain request still gets ruts: a road was drafted from the lane object\'s own shape and written into the settings file', len(roads) == 1 and len(roads[0]['polyline']) >= 8 and roads[0].get('drafted') and "road(s) drafted from the lanes' shapes" in text, str(roads)[:200])
check.true('...its width is read from the lane (about 3.2 m, not the 4 m a slice across the curve would show) and it runs the length of the lane (50 m)', roads and 3.0 <= roads[0]['width'] <= 3.8
           and abs(roads[0]['polyline'][-1][0] - roads[0]['polyline'][0][0]) > 45, str(roads[0]['width']) if roads else '')
outline = probe(path('lanes-done', 'done.blend'), 'outline')['ground']
ribbon = outline['Dirt road ribbon']
check.true('the curved lane strip is still ONE curved strip: the kit split its faces in place (more than 5000 faces), its outline area is within 2 percent of what it was and it is not a rectangle', ribbon['faces'] > 5000 and ribbon['boundary_loops'] == 1 and not ribbon['plain_rectangle']
           and abs(ribbon['area'] / ribbon['area_before'] - 1.0) < 0.02, str(ribbon),
           recorded='the code review: a 160 square metre curved lane became a 39,198-square rectangle of 50 x 11 m', proves='the lane was not replaced by a grid over its box')
check.true('...and it has real ruts: relief at least 3 cm (the audit asks for it)', ribbon['relief'] >= 0.03, f'{ribbon["relief"]} m')
check.true('a plain rectangle ground still gets a graded grid (more than 4000 faces, still a rectangle)', outline['Ground']['faces'] > 4000 and outline['Ground']['plain_rectangle'], str(outline['Ground']))
code, text, _ = place('undo', path('lanes-done', 'done.blend'), '--save-as', path('lanes-undone', 'undone.blend'))
back = probe(path('lanes-undone', 'undone.blend'), 'outline')['ground'] if code == 0 else {}
check.true('undo swaps the original lane mesh back (20 faces)', code == 0 and back.get('Dirt road ribbon', {}).get('faces') == 20, str(back.get('Dirt road ribbon')))

lanes_two = own_copy('lanes', 'lanes-two')                                 # a settings file that exists but names no road: finish drafts one and writes it in
json.dump({'place': 'lanes', 'roads': []}, open(path('lanes-two', 'place-settings.json'), 'w'))
code, text, _ = place('finish', lanes_two, '--save-as', path('lanes-two-done', 'done.blend'))
check.true('a settings file with "roads": [] and a dirt-road object gets a road written into it (and the audit passes)', code == 0 and len(json.load(open(path('lanes-two', 'place-settings.json')))['roads']) == 1, text.strip().splitlines()[-1][:160])

trench = own_copy('trench')
json.dump({'place': 'trench', 'look': 'lived_in', 'state': 'damp', 'roads': [{'name': 'towpath', 'polyline': [[0, 0], [14, 0]], 'width': 2.4, 'gauge': 1.3, 'rut_depth': 0.08, 'hoof': True}]}, open(path('trench', 'place-settings.json'), 'w'))
before = probe(trench, 'positions')['objects']
code, text, _ = place('finish', trench, '--save-as', path('trench-done', 'done.blend'))
check.equal('a towpath with a trench cut in it, and steps in the trench, finishes and passes (exit 0)', code, 0)
after = probe(path('trench-done', 'done.blend'), 'positions')['objects']
moves = {name: abs(after[name]['low'] - before[name]['low']) for name in before if name.startswith('Stone step')}
check.true('the steps in the trench did not move (every step within 1 cm of where it was built; before the fix they went up 2 m)', len(moves) == 3 and max(moves.values()) < 0.01, str({n: round(v, 4) for n, v in moves.items()}),
           recorded='the smoke check: roads filled the trench and finish moved the stair stones up 2 m without saying how far')
trench_ground = probe(path('trench-done', 'done.blend'), 'outline')['ground']['Towpath']
check.true('the towpath still has its trench: 2 outlines (the strip and the hole) and the same number of faces (its 0.1 m squares were fine already)', trench_ground['boundary_loops'] == 2 and trench_ground['faces'] == 3240 and trench_ground['original_mesh'] is None, str(trench_ground))
check.true('nothing is said to have moved by more than 3 cm', not [line for line in lines(text, 'LOOK parts:') if 'moved' in line], ' | '.join(lines(text, 'LOOK parts:'))[:200])

# ---------------------------------------------------------------- 3. curves, text and instances
kinds = own_copy('kinds')
code, text, _ = place('audit', kinds)
failed = ' '.join(lines(text, 'FAIL'))
check.true('a bevelled curve, a text sign and an instanced collection FAIL the audit by name before the pass ("they are drawn but are not meshes")', code == 1 and all(word in failed for word in ('Rope 1', 'Sign text', 'Prop barrel instance')) and 'not meshes' in failed, failed[:240],
           recorded='the code review: a red bevelled curve floating 3 m up, a text sign and an instanced prop all got PASS')
code, text, _ = place('finish', kinds, '--save-as', path('kinds-done', 'done.blend'))
check.equal('...and `finish` turns them into meshes and passes (exit 0)', code, 0, ' | '.join(lines(text, 'FAIL'))[:200])
objects = probe(path('kinds-done', 'done.blend'), 'kinds')['objects']
new_names = ['Rope 1', 'Sign text', 'Prop barrel instance barrel source mesh']
check.true('the three became mesh objects with kit materials (a real surface), made by the kit', all(objects.get(n, {}).get('type') == 'MESH' and objects[n]['made'] and objects[n]['materials'] and objects[n]['materials'][0].startswith('PK ') for n in new_names), str({n: (objects.get(n, {}).get('type'), objects.get(n, {}).get('materials')) for n in new_names}))
check.true('the originals are kept, hidden, and say what they became', objects['Rope 1 (curve)']['hide_render'] and objects['Rope 1 (curve)']['converted_to'] == 'Rope 1' and objects['Prop barrel instance']['hide_render'] and objects['Prop barrel instance']['converted_to'])
check.true('a helper curve with a never role is left alone (still a visible curve, no mesh made from it)', objects['Helper line']['type'] == 'CURVE' and not objects['Helper line']['hide_render'])
code, text, _ = place('undo', path('kinds-done', 'done.blend'), '--save-as', path('kinds-undone', 'undone.blend'))
back = probe(path('kinds-undone', 'undone.blend'), 'kinds')['objects']
check.true('undo brings the curve, the text and the instance back as they were (same names, same types, visible) and removes the meshes made from them', code == 0 and back['Rope 1']['type'] == 'CURVE' and back['Sign text']['type'] == 'FONT' and back['Prop barrel instance']['type'] == 'EMPTY'
           and not back['Rope 1']['hide_render'] and not any(v['made'] for v in back.values()) and 'Prop barrel instance barrel source mesh' not in back, str({n: (v['type'], v['hide_render']) for n, v in back.items()}))

# ---------------------------------------------------------------- 4. a lettered sign keeps its picture
sign = own_copy('sign')
code, text, _ = place('finish', sign, '--save-as', path('sign-done', 'done.blend'))
check.equal('a sign whose material carries its own picture finishes and PASSES the audit (before the fix it failed for ever, and re-running changed nothing)', code, 0, ' | '.join(lines(text, 'FAIL'))[:200])
facts = probe(path('sign-done', 'done.blend'), 'sign')
check.true('its picture is still the colour (upstream of the colour plug), and it got roughness that varies and a normal map', facts['colour_still_the_picture'] and facts['roughness_varies'] and facts['normal_map'] and facts['augment_nodes'] > 0, str(facts))
check.true('the surfaces step says which materials it kept', any('kept (own picture): lettered sign' in line for line in lines(text, 'PASS surfaces')), ' | '.join(lines(text, 'PASS surfaces'))[:200])
code, text, _ = place('undo', path('sign-done', 'done.blend'), '--save-as', path('sign-undone', 'undone.blend'))
facts = probe(path('sign-undone', 'undone.blend'), 'sign')
check.true('undo takes what was added out again: the sign is exactly as it was (picture is the colour, roughness and normal not wired, no kit node left)', code == 0 and facts['colour_still_the_picture'] and not facts['roughness_linked'] and not facts['normal_linked'] and facts['augment_nodes'] == 0 and not facts['layer_groups'], str(facts))

# ---------------------------------------------------------------- 5. undo after the kit added the sun; finish with nowhere to save; an empty scene
nolight = path('no-light-hut', 'no-light-hut.blend')
made = subprocess.run([blender, '-b', '--disable-autoexec', '--python', HUT, '--', nolight, '--no-floating', '--no-light'], capture_output=True, text=True, timeout=300, env=environment)
assert os.path.exists(nolight), made.stdout[-300:] + made.stderr[-300:]
code, text, _ = place('light', nolight, '--save-as', path('lit-hut', 'lit.blend'))
lights = probe(path('lit-hut', 'lit.blend'), 'lights')
check.true('`light` on a scene with no lamp adds the kit\'s own sun', code == 0 and any(kind == 'SUN' and made_by_kit for _, kind, made_by_kit in lights['lights']), str(lights))
code, text, _ = place('undo', path('lit-hut', 'lit.blend'), '--save-as', path('lit-hut-undone', 'undone.blend'))
lights = probe(path('lit-hut-undone', 'undone.blend'), 'lights')
check.true('`undo` after the kit added the sun does not crash (it used to end with "StructRNA of type SunLight has been removed") and takes the sun out', code == 0 and 'ReferenceError' not in text and not lights['lights'], text.strip().splitlines()[-1][:160])
code, text, seconds = place('finish', nolight)
check.true('`finish` with no --save-as stops at once (exit 2, under 8 seconds), says where to save and that nothing was done, and runs no step', code == 2 and seconds < 8 and '--save-as' in text and 'Nothing was done' in text and not lines(text, 'PASS roles'), f'{seconds:.1f} s: {text.strip()[:120]}',
           recorded='the smoke check: finish did the whole 23 s of work and only then said it had nowhere to save')
empty = own_copy('empty')
code, text, _ = place('finish', empty, '--save-as', path('empty-done', 'done.blend'))
check.true('`finish` on an empty scene stops with a plain sentence (exit 2), writes no settings file and says nothing about infinity', code == 2 and 'no visible mesh objects' in text and 'infinity' not in text and not os.path.exists(path('empty', 'place-settings.json')), text.strip()[:160])
code, text, _ = place('audit', empty)
check.true('the audit of an empty scene FAILS (exit 1: nothing was audited), it no longer passes "every visible object has a role (0 objects)"', code == 1 and any('no visible mesh objects' in line for line in lines(text, 'FAIL')), ' | '.join(lines(text, 'FAIL'))[:200])

# ---------------------------------------------------------------- 6. finish-part, the NEXT line, --facts, a world colour alone
part = own_copy('part')
code, text, _ = place('finish-part', part, '--owner', 'cottages', '--save-as', path('part-done', 'done.blend'))
check.true('`finish-part` on a clean part exits 0 (it used to exit 1 with "place: quick output" on every run) and says in a LOOK that it was a quick trial', code == 0 and not lines(text, 'FAIL') and any('quick' in line for line in lines(text, 'LOOK')), ' | '.join(lines(text, 'LOOK'))[:200],
           recorded='the code review: finish-part always exits 1 and prints a FAIL no builder can clear', proves='a part builder can read its own result')
facts_file = path('facts', 'facts.json')
json.dump({'facts': [{'id': 'wall_thickness', 'what': 'a cottage wall', 'applies_to_role': '^wall\\.', 'dimension': 'thickness', 'min': 0.2, 'max': 0.5, 'unit': 'metres', 'kind': 'judged', 'source': 'this test', 'confidence': 'weak'}]}, open(facts_file, 'w'))
turned = own_copy('turned')
code, text, _ = place('finish', turned, '--facts', facts_file, '--save-as', path('turned-done', 'done.blend'))
next_line = lines(text, 'NEXT run:')
check.true('`finish --facts` is accepted, and the NEXT line carries --reports and --real-world-facts (so the preflight writes beside the audit, and judges with the place\'s own facts)', code == 0 and next_line and '--reports' in next_line[0] and '--real-world-facts' in next_line[0] and facts_file in next_line[0], next_line[0][-200:] if next_line else text[-200:])
check.true('the wall turned 45 degrees is size-checked by its own sides (4 x 0.3 m): the audit says 46 or more sizes fit, with no warning about its thickness', 'wall thickness' not in ' '.join(lines(text, 'LOOK')).lower() and not lines(text, 'FAIL'), ' | '.join(lines(text, 'LOOK'))[:200])
sizes = probe(turned, 'sizes')['objects']['Cottage wall 1']
check.true('the oriented size of the turned wall is 4.0 x 0.3 (its box along the world axes says 3.0 x 3.0: the trap)', sorted(sizes['oriented'][:2]) == [0.3, 4.0] and abs(sizes['world_box'][0] - 3.04) < 0.05, str(sizes))
world = own_copy('world')
code, text, _ = place('audit', world)
check.true('a scene lit only by its world colour passes the light check as "some light" but the audit LOOKs that it has no lamp (no raking shadows)', any('place: light' in line and 'no lamp' in line for line in lines(text, 'LOOK')), ' | '.join(lines(text, 'LOOK'))[:240])
code, text, _ = place('light', world, '--save-as', path('world-lit', 'lit.blend'))
lights = probe(path('world-lit', 'lit.blend'), 'lights')
check.true('`light` adds the kit\'s sun to a scene that has only a world colour (it used to say "the scene already has light")', code == 0 and any(kind == 'SUN' for _, kind, _ in lights['lights']) and lights['scene_world'] == 'Sky colour', str(lights))

# ---------------------------------------------------------------- 7. water: damp beside it, not a solid, Cycles when in view
quay = own_copy('quay')
samples = probe(quay, 'masks')['samples']
check.true('the plan masks wet the ground beside water: dampness 0.4 or more 10 cm from the quay edge, fading to 0 by 3 m from the water', samples['7.9']['dampness'] >= 0.4 and samples['5.0']['dampness'] == 0.0 and 0.0 < samples['7.0']['dampness'] < samples['7.9']['dampness'], str({k: samples[k]['dampness'] for k in ('2.0', '5.0', '7.0', '7.9')}),
           recorded='the newcomer judge: damp on the quay 0.1 m from the water was 0.00', proves='a tide line and a wet quay edge are in the wear, not only in the text')
check.true('the sea is not counted as a solid: it casts no shade on the seabed (shade 0), where it used to read 0.9', all(samples[k]['shade'] < 0.05 for k in ('9.5', '11.5', '14.0')), str({k: samples[k]['shade'] for k in ('9.5', '11.5', '14.0')}))
code, text, _ = place('renderer-for', quay)
check.true('the renderer rule says Cycles where water is in view (the owner\'s rule plus this plugin\'s one added reason, named in the text)', code == 0 and text.splitlines()[0].strip() == 'CYCLES' and 'water "Sea" is in view' in text, text.splitlines()[0] if text else '')

check.note('all scenes and files were made in a temporary folder')
shutil.rmtree(folder, ignore_errors=True)
check.finish()
