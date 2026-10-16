"""What this does: tests what the shot planner helper taught the plugin kit's shot checker (paper-film/tools/check_shot.py):
the check file's "accepted" list (problems the project chose to keep, reported as known, not as new problems) and its
"kind_of_shot" (the shot-kind profiles of film-settings.json, which switch off or loosen a rule and add its replacement test).

Part 1 needs nothing outside the plugin: it builds a "box world" at test time (every measured group of the notice corner's
final frame drawn as a flat box in its own colour, from fixtures/notice-corner/notice-corner-final-frame-facts.json) and
runs the checker on it. It proves:
 - with neither key the report is word for word the one the original checker (version 3ad3cd77, the film kit's copy) wrote
   for the same box world (fixtures/shot-planner/box-world-original-report.md), apart from the line naming the version;
 - "kind_of_shot": ["still_life"] with an empty "accepted" list changes no problem;
 - an accepted entry turns its problem into a known one, a worse one stays a problem, an entry that matches nothing is
   noted, and the crowd's 2% bottom-left allowance applies to story things only.
Part 2 uses the project's own measurements when they are on this machine (each part is skipped, not failed, when they
are not): the notice corner (round 5's re-measurement with the log 32 still) and the Works' W1 (round 5's final check,
with the relaxed "picture matches" test round 5 used). The film kit and the experiments come from the project
(FILM_PROJECT, or austerity-explainer next to the plugins folder); the measurements from its working files
(FILM_WORKING_FILES: redesign/round5-set).
The plugin's example check files now carry "kind_of_shot", "figures" and "accepted"; where a run needs neither key, the
test writes a copy without them (the film kit's checker and the original report never had them). It proves the plugin's checker writes the same report and the same
marked picture as the film kit's, that the film kit's reproduces the recorded reports, and what the accepted list and the
crowd + dark subject kinds do to the real reports.
Run: python3 kit/calculators/tests/test_check_shot_kinds.py   (or tests/run_all.py; about two minutes: each check takes 15-20 s)
"""
import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, CALCULATORS, project_folder, film_kit_folder, working_files_folder  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
PLUGIN_CHECKER = os.path.join(KIT, 'paper-film', 'tools', 'check_shot.py')
NOTICE_CHECK = os.path.join(KIT, 'examples', 'notice-corner', 'shot-check.json')
W1_CHECK = os.path.join(KIT, 'examples', 'inflation-chapter-2-newcomers', 'works-w1-shot-check.json')
PROJECT = project_folder() or ''
FILM_KIT_CHECKER = os.path.join(film_kit_folder() or '', 'paper-film', 'tools', 'check_shot.py')
REDESIGN = os.path.join(working_files_folder() or '', 'redesign')
NOTICE_FACTS = os.path.join(REDESIGN, 'round5-set', 'notice', 'check-new', 'facts')
NOTICE_STILL = os.path.join(PROJECT, 'experiments', '32 Notice corner - relit and checked.jpg')
NOTICE_REPORT = os.path.join(PROJECT, 'experiments', '32 Notice corner - the shot checker\'s report.md')
W1_FOLDER = os.path.join(REDESIGN, 'round5-set', 'checks', 'final-w1-quiet')
NEW_KEYS = ('kind_of_shot', 'figures', 'accepted', 'fill', 'support_surfaces')

RELAXED = '''# runs a check_shot.py (by path) with round 5's relaxed "picture matches the scene" test (working files redesign/round5-set/tools/check_dark_picture.py)
import importlib.util, sys
spec = importlib.util.spec_from_file_location('check_shot_under_test', sys.argv[1])
check_shot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_shot)
original = check_shot.picture_mismatch
check_shot.picture_mismatch = lambda shot: [e for e in original(shot) if not (e.startswith('man ') or any(w in e.split(' (')[0] for w in ('gate', 'board', 'sign')))]
sys.argv = ['check_shot.py'] + sys.argv[2:]
check_shot.main()
'''

check = Checker('shot checker: kinds of shot and the accepted list')
work = tempfile.mkdtemp(prefix='check-shot-kinds-')   # this run's own folder (several runs may go at once), removed however the test ends
atexit.register(shutil.rmtree, work, True)


def box_world(facts_path, out):
    """Every measured group drawn as a flat box in its colour (far first), with its own solo picture: shot_facts.py's
    output for a world of boxes."""
    with open(facts_path) as handle:
        facts = json.load(handle)
    width, height = facts['size']
    os.makedirs(os.path.join(out, 'solo'), exist_ok=True)
    ids = np.zeros((height, width, 3), np.uint8)
    for name, group in sorted(facts['groups'].items(), key=lambda kv: -kv[1]['distance']):
        l, t, r, b = group['screen_box_unclipped']
        box = (int(round(l * width)), int(round(t * height)), int(round(r * width)) - 1, int(round(b * height)) - 1)
        red, green, blue = group['colour']
        cv2.rectangle(ids, box[:2], box[2:], (blue, green, red), -1)
        solo = np.zeros((height, width, 3), np.uint8)
        cv2.rectangle(solo, box[:2], box[2:], (255, 255, 255), -1)
        cv2.imwrite(os.path.join(out, 'solo', f'{name}.png'), solo)
    cv2.imwrite(os.path.join(out, 'ids.png'), ids)
    shutil.copy(facts_path, os.path.join(out, 'facts.json'))


def check_file(base, name, **changes):
    """A copy of a check file without the new keys (as the film kit's examples are), with these changes."""
    with open(base) as handle:
        data = {k: v for k, v in json.load(handle).items() if k not in NEW_KEYS}
    data.update(changes)
    path = os.path.join(work, name + '.json')
    with open(path, 'w') as handle:
        json.dump(data, handle, indent=1)
    return path


def start(name, checker, check_path, facts, picture=None, relaxed=False, extra=()):
    out = os.path.join(work, name)
    command = [sys.executable, '-B']
    if relaxed:
        command += [os.path.join(work, 'relaxed.py'), checker]
    else:
        command += [checker]
    command += ['--check', check_path, '--facts', facts, '--out', out, '--title', name] + (['--picture', picture] if picture else []) + list(extra)
    environment = dict(os.environ, PYTHONHASHSEED='1')
    return name, out, subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=environment)


def finish_all(runs, at_once=4):
    """Runs the checks four at a time; returns {name: output folder} for those that worked."""
    done, waiting, running = {}, list(runs), []
    while waiting or running:
        while waiting and len(running) < at_once:
            running.append(start(*waiting.pop(0)))
        name, out, process = running.pop(0)
        _, error = process.communicate()
        if process.returncode != 0:
            print(f'NOTE  check {name} stopped: {error.strip().splitlines()[-1] if error.strip() else process.returncode}')
        else:
            done[name] = out
    return done


def report(out):
    with open(os.path.join(out, 'report.md')) as handle:
        return handle.read()


def without_version(text):
    return re.sub(r'version [0-9a-f]{8}', 'version (any)', re.sub(r'^# Shot check: .*$', '# Shot check: (title)', text, flags=re.M))


def section(text, title):
    match = re.search(rf'^## {re.escape(title)}\n(.*?)(?=^## |\Z)', text, flags=re.M | re.S)
    return match.group(1).strip() if match else ''


def problems(text):
    return re.findall(r'^\d+\. \*\*(.+?)\.\*\* (.*)$', section(text, 'Problems'), flags=re.M)


def same_text(name, got, expected, recorded='', proves=''):
    """Two reports compared line by line (printing only how many lines differ and the first difference)."""
    a, b = got.splitlines(), expected.splitlines()
    differing = [k for k in range(max(len(a), len(b))) if (a[k] if k < len(a) else None) != (b[k] if k < len(b) else None)]
    details = (f'{len(a)} lines, all the same' if not differing else
               f'{len(differing)} of {max(len(a), len(b))} lines differ; first, line {differing[0] + 1}: '
               f'{(a[differing[0]] if differing[0] < len(a) else "(none)")[:120]!r}')
    return check.true(name, not differing, details=details, recorded=recorded, proves=proves)


def known(text):
    return re.findall(r'^- \*\*(.+?)\.\*\* (.*)$', section(text, 'Known and allowed'), flags=re.M)


with open(os.path.join(work, 'relaxed.py'), 'w') as handle:
    handle.write(RELAXED)

# ------------------------------------------------------------------------------------------------ part 1: the box world
facts = os.path.join(work, 'box-world')
box_world(os.path.join(FIXTURES, 'notice-corner', 'notice-corner-final-frame-facts.json'), facts)
accepted_handcart = {'rule': 'rule8_bottom_left_share', 'things': ['handcart'], 'reason': 'a test entry', 'who': 'the test', 'date': '2026-10-16'}
NOTICE_PLAIN = check_file(NOTICE_CHECK, 'notice-plain')   # the example as the film kit has it: neither new key
W1_PLAIN = check_file(W1_CHECK, 'w1-plain')
runs = [
    ('box default', PLUGIN_CHECKER, NOTICE_PLAIN, facts),
    ('box empty', PLUGIN_CHECKER, check_file(NOTICE_CHECK, 'empty', kind_of_shot=['still_life'], accepted=[]), facts),
    ('box accepted', PLUGIN_CHECKER, check_file(NOTICE_CHECK, 'accepted', accepted=[
        accepted_handcart,
        {'rule': 'rule6_lit_from_below', 'reason': 'not measured without a picture', 'who': 'the test', 'date': '2026-10-16'},
        {'rule': 'slide_magnification', 'reason': 'a planner rule', 'who': 'the test', 'date': '2026-10-16', 'measured': 1.45}]), facts),
    ('box worse', PLUGIN_CHECKER, check_file(NOTICE_CHECK, 'worse', accepted=[dict(accepted_handcart, measured=0.015)]), facts),
    ('box crowd', PLUGIN_CHECKER, check_file(NOTICE_CHECK, 'crowd', kind_of_shot=['crowd']), facts),
    ('box example', PLUGIN_CHECKER, NOTICE_CHECK, facts),   # the example as shipped, with its kinds and accepted list
]
done = finish_all(runs)
with open(os.path.join(FIXTURES, 'shot-planner', 'box-world-original-report.md')) as handle:
    original = handle.read()
default = report(done['box default'])
same_text('box world, no new keys: the report is the original checker\'s, word for word (version line aside)', without_version(default), without_version(original),
            recorded='fixtures/shot-planner/box-world-original-report.md (written by the film kit\'s check_shot.py 3ad3cd77 on the same box world)',
            proves='default behaviour unchanged when the check file has neither "kind_of_shot" nor "accepted"')
check.true('box world, no new keys: no known.json is written', not os.path.exists(os.path.join(done['box default'], 'known.json')))
empty = report(done['box empty'])
check.true('box world, still life and an empty accepted list: the same numbered problems', problems(empty) == problems(original),
           details=f'{len(problems(empty))} problems', proves='naming the base kind changes no problem (only the header names the kind)')
accepted = report(done['box accepted'])
open_rules = [p[1][:40] for p in problems(accepted)]
check.true('box world, accepted: the handcart\'s bottom-left problem is known, the drum\'s stays', len(problems(accepted)) == len(problems(original)) - 1
           and any('handcart fills' in k[1] for k in known(accepted)) and any('drum fills' in p[1] for p in problems(accepted)),
           details=f'{len(problems(accepted))} problems, known: {[k[1][:40] for k in known(accepted)]}',
           proves='an accepted entry with "things" matches only its own thing')
notes = section(accepted, 'Notes')
check.true('box world, accepted: an entry no problem matches is noted; one for a rule this tool never measures says so',
           'rule6_lit_from_below' in notes and 'no such problem was found' in notes and 'does not measure' in notes, details=notes[-200:])
worse = report(done['box worse'])
check.true('box world, accepted at 1.5% but now 2.2%: the handcart stays a problem and says it is worse than accepted',
           any('handcart fills' in p[1] and 'worse than that' in p[1] for p in problems(worse)),
           details=next((p[1][-160:] for p in problems(worse) if 'handcart fills' in p[1]), 'not found'),
           recorded='shot_planner.check_shot_accepted_worse_share 0.05 (invented)')
crowd = report(done['box crowd'])
check.true('box world, crowd: the drum (a story thing, 1.5%) is allowed under the crowd\'s 2%; the handcart (a work prop, 2.2%) is not',
           any('drum fills' in k[1] for k in known(crowd)) and any('handcart fills' in p[1] for p in problems(crowd)),
           details=f'known: {[k[1][:30] for k in known(crowd)]}',
           recorded='shot_kind_profiles.crowd rule8_bottom_left_share 0.02, applies to story things (round 5 final checks)')
check.true('box world, crowd without "figures": the head-spacing test says it was not run', 'list the people\'s groups under "figures"' in section(crowd, 'Notes'))
with open(os.path.join(done['box crowd'], 'known.json')) as handle:
    written = json.load(handle)
check.true('box world, crowd: known.json lists the kinds, the settings used and each known problem', written['kinds'] == ['crowd'] and written['known']
           and any(k.startswith('shot_kind_profiles.crowd') for k in written['settings_used']), details=f'{len(written["known"])} known')

example = report(done['box example'])
with open(os.path.join(done['box example'], 'known.json')) as handle:
    example_known = json.load(handle)
check.true('the shipped notice corner example (still life, the user\'s four accepted problems) runs: a "Known and allowed" section, known.json, '
           'and a note that the slide entry is for other tools', example_known['kinds'] == ['still_life'] and 'Known and allowed' in example
           and 'slide_magnification' in section(example, 'Notes') and 'does not measure' in section(example, 'Notes'),
           details=f'{len(problems(example))} problems, {len(known(example))} known', proves='the example shows the new keys working')

# ------------------------------------------------------------------------------------------------ part 2: the project's own measurements
have_notice = all(os.path.exists(p) for p in (FILM_KIT_CHECKER, NOTICE_FACTS, NOTICE_STILL, NOTICE_REPORT))
have_w1 = all(os.path.exists(os.path.join(W1_FOLDER, p)) for p in ('facts', 'picture.png', 'blender.log', 'light/report.md')) and os.path.exists(FILM_KIT_CHECKER)
runs = []
if have_notice:
    with open(os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')) as handle:
        notice_accepted = json.load(handle)['accepted']
    runs += [('notice old', FILM_KIT_CHECKER, NOTICE_PLAIN, NOTICE_FACTS, NOTICE_STILL),
             ('notice new', PLUGIN_CHECKER, NOTICE_PLAIN, NOTICE_FACTS, NOTICE_STILL),
             ('notice accepted', PLUGIN_CHECKER, check_file(NOTICE_CHECK, 'notice-accepted', accepted=notice_accepted), NOTICE_FACTS, NOTICE_STILL)]
if have_w1:
    w1_args = (os.path.join(W1_FOLDER, 'facts'), os.path.join(W1_FOLDER, 'picture.png'), True, ['--render-log', os.path.join(W1_FOLDER, 'blender.log')])
    runs += [('w1 old', FILM_KIT_CHECKER, W1_PLAIN) + w1_args, ('w1 new', PLUGIN_CHECKER, W1_PLAIN) + w1_args,
             ('w1 kinds', PLUGIN_CHECKER, check_file(W1_CHECK, 'w1-kinds', kind_of_shot=['crowd', 'dark_subject'],
                                                     figures=[f'man {k}' for k in range(1, 8)])) + w1_args]
done = finish_all(runs)
if not have_notice:
    check.note('part 2, notice corner: skipped (it needs the project\'s film kit and experiments, and the working files\' '
               'redesign/round5-set/notice; set FILM_PROJECT and FILM_WORKING_FILES)')
elif {'notice old', 'notice new', 'notice accepted'} <= set(done):
    old, new = report(done['notice old']), report(done['notice new'])
    same_text('notice corner: the plugin\'s checker writes the film kit\'s report (version line aside)', without_version(new), without_version(old),
                recorded='film-kit/paper-film/tools/check_shot.py (3ad3cd77) on round 5\'s notice corner measurement and the log 32 still',
                proves='the notice corner\'s report is unchanged by the new keys\' code')
    with open(os.path.join(done['notice old'], 'marked.jpg'), 'rb') as a, open(os.path.join(done['notice new'], 'marked.jpg'), 'rb') as b:
        check.true('notice corner: and the same marked picture, byte for byte', a.read() == b.read())
    with open(NOTICE_REPORT) as handle:
        recorded_report = handle.read()
    check.true('notice corner: the film kit\'s checker gives the recorded log 32 problems (so these inputs are the kept shot)', problems(old) == problems(recorded_report),
               details=f'{len(problems(old))} problems, word for word', recorded='experiments/32 Notice corner - the shot checker\'s report.md',
               proves='only that the test runs on the right measurement and picture')
    with_accepted = report(done['notice accepted'])
    check.equal('notice corner with its accepted list: the light and quiet-side problems the user kept are known',
                sorted(k[0] for k in known(with_accepted)), ['rule 10: the quiet side keeps the frame from tipping', 'rule 6: lit from below'],
                recorded='notice-corner-place-facts.json accepted (decision 38: "Wow that\'s incredible. Yes keep it.")')
    check.true('notice corner with its accepted list: only the reference problems (matching the liked picture, not a house rule) stay',
               problems(with_accepted) and all(p[0].startswith('reference') for p in problems(with_accepted)),
               details=f'{len(problems(with_accepted))} problems: {sorted(set(p[0] for p in problems(with_accepted)))}')
else:
    check.true('notice corner: every check ran', False, details=f'ran: {sorted(done)}')
if not have_w1:
    check.note('part 2, Works W1: skipped (round 5\'s final check folder is in the working files, redesign/round5-set/checks/final-w1-quiet; '
               'set FILM_WORKING_FILES)')
elif {'w1 old', 'w1 new', 'w1 kinds'} <= set(done):
    old, new = report(done['w1 old']), report(done['w1 new'])
    same_text('W1: the plugin\'s checker writes the film kit\'s report (version line aside)', without_version(new), without_version(old),
                recorded='round 5 final check of W1 (quiet), with round 5\'s relaxed picture test')
    with open(os.path.join(W1_FOLDER, 'light', 'report.md')) as handle:
        recorded_report = handle.read()
    same_text('W1: and it is the recorded round 5 light report', without_version(old), without_version(recorded_report),
                recorded='working files redesign/round5-set/checks/final-w1-quiet/light/report.md (21 problems)')
    kinds = report(done['w1 kinds'])
    allowed, open_now = known(kinds), problems(kinds)
    check.equal('W1 as a crowd with a dark subject: problems allowed by the kinds of shot', len(allowed), 15,
                recorded='test_shot_kind_profiles.py (the core\'s reading of the same 21 problems: 15 covered for "w1-quiet-light")',
                proves='the checker applies the profiles as the core read them from the report\'s words')
    texts = ' | '.join(p[1] for p in open_now)
    check.true('W1 kinds: the petrol drum (not a story thing) and the lantern touching man 1 stay open',
               'petrol drum fills' in texts and 'lantern and man 1 almost touch' in texts,
               recorded='core: the profiles leave these open on purpose (fix them, or accept them by name)')
    check.true('W1 kinds: no near-touch between two men is left as a problem (a crowd replaces it by head spacing)',
               not re.search(r'man \d.{0,60}man \d', ' '.join(p[1] for p in open_now if p[0].startswith('rule 4'))),
               details=f'rule 4 problems left: {[p[1][:40] for p in open_now if p[0].startswith("rule 4")]}')
    added = {p[0]: p[1] for p in open_now if p[0].startswith(('crowd', 'dark subject'))}
    check.true('W1 kinds: the replacement tests run and fail where the render shows it: man 1 hidden behind man 6, the gate\'s outline faint',
               'crowd: heads apart' in added and 'crowd: every figure half seen' in added and 'dark subject: its outline against the light' in added,
               details='; '.join(f'{k}: {v[:90]}' for k, v in added.items()),
               recorded='works-shot.json men_seen (man 1\'s box 0.34-0.47 across behind man 6\'s 0.37-0.53); plan_shot.py predicts man 1 shows about 12% of his box')
    check.note('W1 kinds: the silhouette test uses 2.2, measured on painted figures, never on a gate, and a band width that is invented: calibrate on '
               'the W1 painting before trusting its fail')
else:
    check.true('W1: every check ran', False, details=f'ran: {sorted(done)}')
check.finish()
