"""What this does: tests that the plugin's example check files show the shot checker's newer keys the way a new film
should use them: "kind_of_shot" (the view's kinds of shot, the same as its place facts say), "figures" (the groups that
are people, each a group of the file), and "accepted" (problems kept on purpose, each saying who accepted it and when).
The five examples are the notice corner, the people test and the Works' W1, W2 and W3. It also runs the preflight's
shots stage with the notice corner's example, so the check file's accepted list shows up as known in its report.
Run: python3 kit/calculators/tests/test_example_check_files.py   (a few seconds; needs only the plugin)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402

from settings import load_settings  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
EXAMPLES = os.path.join(KIT, 'examples')
check = Checker('example check files: kinds of shot, figures and accepted problems')
settings = load_settings()
kinds_known = {key.split('.')[1] for key in settings.section('shot_kind_profiles') if '.rules.' in key}   # still_life, crowd, ...
CASES = [   # example file, its place facts fixture, the view there
    ('notice-corner/shot-check.json', 'notice-corner/notice-corner-place-facts.json', 'end'),
    ('people-test/shot-check.json', 'people-test/people-test-place-facts.json', 'still'),
    ('inflation-chapter-2-newcomers/works-w1-shot-check.json', 'works/works-place-facts.json', 'w1'),
    ('inflation-chapter-2-newcomers/works-w2-shot-check.json', 'works/works-place-facts.json', 'w2'),
    ('inflation-chapter-2-newcomers/works-w3-shot-check.json', 'works/works-place-facts.json', 'w3'),
]
for example, facts_name, view in CASES:
    data = json.load(open(os.path.join(EXAMPLES, example)))
    facts = json.load(open(os.path.join(FIXTURES, facts_name)))
    place_kinds = next(v['kind_of_shot'] for v in facts['views'] if v['name'] == view)
    check.equal(f'{example}: its kinds of shot are the place facts\' for view {view}', data.get('kind_of_shot'), place_kinds,
                recorded=f'tests/fixtures/{facts_name} views[{view}].kind_of_shot')
    check.true(f'{example}: every kind is a profile in film-settings.json', set(data.get('kind_of_shot', [])) <= kinds_known,
               details=f'{data.get("kind_of_shot")} of {sorted(kinds_known)}')
    figures = data.get('figures')
    check.true(f'{example}: "figures" is there and names only groups of the file', isinstance(figures, list) and set(figures) <= set(data['groups'])
               and ('crowd' not in place_kinds or figures), details=f'{len(figures or [])} figure group(s)')
    accepted = data.get('accepted')
    check.true(f'{example}: "accepted" is there, and every entry says its rule, reason, who and when', isinstance(accepted, list)
               and all(e.get('rule') and e.get('reason') and e.get('who') and e.get('date') for e in accepted), details=f'{len(accepted or [])} entr(ies)')
notice = json.load(open(os.path.join(EXAMPLES, 'notice-corner', 'shot-check.json')))
place = json.load(open(os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')))
check.equal('the notice corner\'s accepted list is the place facts\' (the user kept the shot, decision 38)', sorted(e['rule'] for e in notice['accepted']),
            sorted(e['rule'] for e in place['accepted']), recorded='notice-corner-place-facts.json accepted')
w3 = json.load(open(os.path.join(EXAMPLES, 'inflation-chapter-2-newcomers', 'works-w3-shot-check.json')))
check.equal('W3 (an overview) names the handcart as a fill prop that may make the reach down the frame', w3.get('fill'), ['handcart'],
            recorded='test_plan_shot.py: "the handcart, a fill prop, makes the reach, which an overview allows"')

work = tempfile.mkdtemp(prefix='example-check-files-')
try:
    run = subprocess.run([sys.executable, '-B', os.path.join(CALCULATORS, 'preflight.py'), 'shots', '--project', work,
                          '--place-facts', os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json'),
                          '--check-files', f'end={os.path.join(EXAMPLES, "notice-corner", "shot-check.json")}', '--json'],
                         capture_output=True, text=True, timeout=300)
    report = json.loads(run.stdout)
    from_check_file = [k for k in report['known_lists'] if k['source'].startswith('shot-check.json')]
    check_file_check = next(c for c in report['checks'] if c['title'].startswith('each view'))
    check.true('preflight shots with the notice corner\'s example: its 4 accepted entries are shown as known, and the check file passes',
               len(from_check_file) == 4 and all(k['signed'] for k in from_check_file) and check_file_check['verdict'] == 'pass',
               details=f'{len(from_check_file)} known from the check file; check file check {check_file_check["verdict"]}')
finally:
    shutil.rmtree(work, ignore_errors=True)
check.finish()
