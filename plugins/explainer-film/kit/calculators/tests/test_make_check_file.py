"""What this does: tests make_check_file.py (paper-film/blender/make_check_file.py), which writes a view's shot check file
from the Blender scene with only the story choices taken from a short shot list. The proof is that it rebuilds the
hand-made check files of the notice corner and the Works (W1, W3) except their story roles, and the checkout's interior
cases (counter props kept off the street's ground test, the ceiling as the dim top), group by group (by the objects
each group holds) and role by role.
Parts:
  A. always: the helpers (names, patterns, the shot_facts grouping rule) and the check files the generator wrote on
     2026-10-16 (fixtures/views-and-models/generated: only repeats that run)
  B. when Blender and the project are on this machine (fixtures/views-and-models/project.json, or BLENDER and
     FILM_PROJECT): the four scenes are built and the check files generated again and compared with the hand-made ones
     (about a minute and a half, one Blender at a time; VIEWS_AND_MODELS_NO_BLENDER=1 skips it)
Run: python3 kit/calculators/tests/test_make_check_file.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
BLENDER_FOLDER = os.path.join(KIT, 'paper-film', 'blender')
sys.path.insert(0, BLENDER_FOLDER)
import make_check_file as maker  # noqa: E402   (bpy is only needed inside Blender)

HERE = os.path.join(FIXTURES, 'views-and-models')
check = Checker('make_check_file: check files from the scene')


class Thing:
    """A stand-in for a Blender object: a name and what it hangs from."""
    def __init__(self, name, parent=None):
        self.name, self.parent = name, parent


# ---------------------------------------------------------------------------------------------------- A. helpers
check.equal('a copy number is taken off a root\'s name', maker.stem_of('brazier-drum.001'), 'brazier-drum')
scene_names = [f'brazier_coal_{i}' for i in range(22)] + ['brazier_soot', 'lantern_flame']
check.equal('a whole family of loose parts becomes one pattern', maker.compress_names([f'brazier_coal_{i}' for i in range(22)] + ['brazier_soot'], scene_names, {}),
            ['brazier_coal_*', 'brazier_soot'], recorded='examples/notice-corner/shot-check.json "drum" (brazier_coal_*, brazier_soot*)')
check.equal('a family split between groups keeps its names', maker.compress_names(['brazier_coal_0', 'brazier_coal_1'], scene_names, {}),
            ['brazier_coal_0', 'brazier_coal_1'])
groups = {'notice': ['notice', 'notice.0*'], 'board': ['notice-board*', 'tacks*'], 'drum': ['brazier-drum*']}
root = Thing('notice-on-board.001')
check.equal('shot_facts\' rule: an object\'s own name wins over what it hangs from', maker.group_of(Thing('tacks', root), groups), 'board',
            recorded='shot_facts.py group_of')
check.equal('a part with no group of its own takes its holder\'s', maker.group_of(Thing('brazier-drum', Thing('brazier-drum.001')), groups), 'drum')

generated = {}
for name in ('notice-corner-end', 'works-w1', 'works-w3', 'checkout-c1'):
    path = os.path.join(HERE, 'generated', f'{name}-check.json')
    generated[name] = json.load(open(path))
shot_lists = {name: json.load(open(os.path.join(HERE, 'shot-lists', f'{name}.json'))) for name in generated}
for name, made in generated.items():
    shot = shot_lists[name]
    check.true(f'{name} (2026-10-16 run): story roles exactly as the shot list', made.get('subject') == shot.get('subject') and made['story'] == shot['story']
               and made.get('support') == shot.get('support'), proves='only repeats that run')
check.true('every generated file asks rule 7 (story_reaches_down 0.70)', all(m['story_reaches_down'] == 0.7 for m in generated.values()),
           recorded='design (log 35): "story_reaches_down 0.70 appears in every file"; shot_kind_profiles rule7')
check.equal('W3 eye range from the overview profile', generated['works-w3']['eye_height'], [0.8, 7.0],
            recorded='works-w3-shot-check.json eye_height (the window: "the range is wide on purpose")')
check.true('W1 and W3 (crowd views) say "band": true', generated['works-w1'].get('band') and generated['works-w3'].get('band'),
           recorded='round 5 final checks: only 27-32% of the title band is sky (skeptic, log 35)')
check.true('checkout: the ceiling is the sky and no counter prop is on the street\'s ground test',
           generated['checkout-c1'].get('sky') == 'ceiling*' and not set(generated['checkout-c1']['on_ground']) & {'basket', 'divider', 'bill stand', 'bill', 'till', 'card terminal'},
           recorded='checkout-c1-shot-check.json ("sky": "ceiling*", on_ground []); round5-checkout/check1 (four counter props "landed on something high")')

# ---------------------------------------------------------------------------------------------------- B. Blender
note = json.load(open(os.path.join(HERE, 'project.json')))
project = os.environ.get('FILM_PROJECT', note['project'])
blender = os.environ.get('BLENDER', note['blender'])
kit_folder = os.path.join(project, 'film-kit')
if os.environ.get('VIEWS_AND_MODELS_NO_BLENDER') or not os.path.exists(blender) or not os.path.isdir(kit_folder):
    check.note('part B skipped: no Blender or no project (set BLENDER and FILM_PROJECT; VIEWS_AND_MODELS_NO_BLENDER=1 skips it)')
    check.finish()

environment = dict(os.environ, DISPLAY=os.environ.get('BLENDER_DISPLAY', note['display']))
script = os.path.join(BLENDER_FOLDER, 'make_check_file.py')
works_folder = os.path.join(kit_folder, 'assets', 'models', 'inflation-chapter-2-newcomers', 'works')
folder = tempfile.mkdtemp(prefix='check-file-test-')
assemble_real = os.path.join(kit_folder, 'paper-film', 'blender', 'inflation-chapter-2-newcomers', 'works', 'assemble_works.py')
assemble_copy = os.path.join(folder, 'assemble_works.py')
with open(assemble_copy, 'wb') as handle:
    subprocess.run(['git', '-C', project, 'show', f'{note["commits"]["round 5 Works assembly matching the final checks (redrawn plates)"]}:'
                    './film-kit/paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py'], stdout=handle, check=True)
runner = os.path.join(folder, 'run_as.py')
with open(runner, 'w') as handle:
    handle.write('import sys\nargv = sys.argv[sys.argv.index("--") + 1:]\nscript, real = argv[argv.index("--script") + 1], argv[argv.index("--as") + 1]\n'
                 'exec(compile(open(script).read(), real, "exec"), {"__name__": "__main__", "__file__": real})\n')
works_facts = os.path.join(FIXTURES, 'works', 'works-place-facts.json')
cases = {
    'notice-corner-end': ([os.path.join(kit_folder, 'assets', 'models', 'pit-village', 'notice-corner.blend'), '--disable-autoexec'], [],
                          os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json'), os.path.join(FIXTURES, 'notice-corner', 'notice-corner-shot-check.json')),
    'works-w1': ([os.path.join(works_folder, 'works-lane.blend')], ['--script', assemble_copy, '--as', assemble_real, '--view', 'w1'],
                 works_facts, os.path.join(FIXTURES, 'works', 'works-w1-shot-check.json')),
    'works-w3': ([os.path.join(works_folder, 'works-lane.blend')], ['--script', assemble_copy, '--as', assemble_real, '--view', 'w3'],
                 works_facts, os.path.join(FIXTURES, 'works', 'works-w3-shot-check.json')),
    'checkout-c1': ([], [], os.path.join(FIXTURES, 'checkout-c1', 'checkout-c1-place-facts.json'), os.path.join(FIXTURES, 'checkout-c1', 'checkout-c1-shot-check.json')),
}
results = {}
try:
    for name, (opening, assemble_options, facts, hand) in cases.items():
        out = os.path.join(folder, f'{name}-result.json')
        before = ['--python', runner] if assemble_options else []
        if name == 'checkout-c1':   # built from an empty scene by its own script (the checkout helper's current copy)
            before = ['--python', os.path.join(kit_folder, 'paper-film', 'blender', 'inflation-chapter-2-newcomers', 'checkout', 'assemble_checkout.py')]
        command = [blender, '-b'] + opening + before + ['--python', script, '--'] + assemble_options + \
            ['--shot-list', os.path.join(HERE, 'shot-lists', f'{name}.json'), '--check-file', os.path.join(folder, f'{name}-check.json'),
             '--place-facts', facts, '--compare', hand, '--out', out]
        run = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=900)
        if not os.path.exists(out):
            check.note(f'{name}: the scene could not be built or measured (exit {run.returncode}): {run.stdout[-400:]}')
            continue
        results[name] = json.load(open(out))
finally:
    for item in os.listdir(folder):
        os.remove(os.path.join(folder, item))
    os.rmdir(folder)


def groups_line(name, count):
    rows = results[name]['comparison']['groups']
    same = sum(1 for r in rows if r['same_objects_share'] == 1.0)
    check.equal(f'{name}: hand groups holding exactly the same drawn objects as a generated group', (same, len(rows)), (count, count),
                proves='the generated groups (one per prop root, loose parts joined, copies merged) cover the hand-made ones')


def role(name, key):
    return results[name]['comparison']['roles'][key]


if 'notice-corner-end' in results:
    name = 'notice-corner-end'
    groups_line(name, 15)
    for key in ('subject', 'support', 'story', 'work', 'must_read', 'lights_in_story', 'box_excludes'):
        check.true(f'{name}: {key} the same as the hand file', role(name, key)['same'], details=json.dumps(role(name, key)),
                   recorded='examples/notice-corner/shot-check.json (log 31)')
    check.true(f'{name}: the hand file\'s pairs_also are all there (more background pairs added)', not role(name, 'pairs_also')['only_hand'],
               details=f'added: {role(name, "pairs_also")["only_generated"]}', recorded='Lessons.md 121 (a check limited to story props missed background near-touches)')
    check.true(f'{name}: the hand file\'s on_ground are all there', not role(name, 'on_ground')['only_hand'], details=f'added: {role(name, "on_ground")["only_generated"]}')
    check.equal(f'{name}: stands_on', role(name, 'stands_on')['generated'], {'lantern': 'chair'}, recorded='the hand file\'s "stands_on"')
    shares = results[name]['facts']['surfaces']
    check.true(f'{name}: the lantern glows over more of itself than the brazier (only the lantern is a light prop)',
               shares['lantern']['glowing_share'] > 0.15 > shares['drum']['glowing_share'],
               details=f'lantern {shares["lantern"]["glowing_share"]:.2f}, drum {shares["drum"]["glowing_share"]:.2f}',
               recorded='skeptic (log 35): by distance the drum would be a light prop and its bright rim excused (log 31)')
if 'works-w1' in results:
    name = 'works-w1'
    groups_line(name, 17)
    for key in ('subject', 'story', 'must_read', 'lights_in_story'):
        check.true(f'{name}: {key} the same as the hand file', role(name, key)['same'], details=json.dumps(role(name, key)),
                   recorded='examples/inflation-chapter-2-newcomers/works-w1-shot-check.json (round 5)')
    for key in ('pairs_also', 'on_ground'):
        check.true(f'{name}: the hand file\'s {key} are all there', not role(name, key)['only_hand'], details=f'added: {role(name, key)["only_generated"]}')
    check.equal(f'{name}: stands_on (the hand file has none)', role(name, 'stands_on')['generated'], {'lantern': 'diesel drum', 'lunch tin': 'petrol drum'},
                recorded='assemble_works.py LANTERN "on DIESEL\'s lid", LUNCH_TIN "on PETROL\'s lid"', proves='found facts the hand file left out')
    made = results[name]['check']
    check.true(f'{name}: every waiting man is his own group and left out of the picture match, as is the gate', all(f'man {i}' in made['groups'] for i in range(1, 8))
               and all(f'man {i}' in made['match_excludes'] for i in range(1, 8)) and 'no-1 gate' in made['match_excludes'],
               recorded='round5-set/tools/check_dark_picture.py (men and gates left out of that test by hand)')
if 'works-w3' in results:
    name = 'works-w3'
    groups_line(name, 18)
    check.equal(f'{name}: eye range', results[name]['comparison']['keys']['eye_height']['generated'], [0.8, 7.0],
                recorded='works-w3-shot-check.json eye_height')
    added = role(name, 'must_read')['only_generated']
    check.true(f'{name}: must_read adds the drums the hand file missed', 'no-1 drums' in added and 'no-2 drums' in added and not role(name, 'must_read')['only_hand'],
               details=f'added {added}', recorded='round 3 ("SEL", "DIE") and round 4 ("DIESE" in W3) fragments')
if 'checkout-c1' in results:
    name = 'checkout-c1'
    groups_line(name, 14)
    made = results[name]['check']
    counter = {'basket', 'divider', 'bill stand', 'bill', 'till', 'card terminal'}
    check.true(f'{name}: no counter prop on the street\'s ground test', not counter & set(made['on_ground']),
               details=f'on_ground {made["on_ground"]} (floor-standing only)', recorded='round5-checkout/check1/report.md: four props "landed on something high"; the hand file has on_ground []',
               proves='the counter case: props on a declared counter are not ground props')
    check.equal(f'{name}: the ceiling is the dim top', made.get('sky'), 'ceiling*', recorded='checkout-c1-shot-check.json "sky"')
    check.equal(f'{name}: eye range indoors', made['eye_height'], [1.5, 1.7], recorded='checkout-c1-shot-check.json eye_height')
    for key in ('subject', 'support', 'story', 'work'):
        check.true(f'{name}: {key} the same as the hand file', role(name, key)['same'])
check.finish()
