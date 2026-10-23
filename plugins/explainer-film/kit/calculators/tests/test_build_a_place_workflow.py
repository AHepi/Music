"""What this does: tests the workflow workflows/build-a-place.js and its five helpers' files (agents/place-*.md) WITHOUT any real
helper. It copies the workflow into a module and asks node to read it (node --check), then runs it in workflow_harness.mjs, a small
stand-in for the Workflow tool that answers every agent() call with a canned answer from fixtures/place-workflow/*.json chosen by the
call's label. Every canned answer is also checked against the schema the script asked for, so a script that asks for one shape and
a helper file that promises another are noticed.
The cases: the happy path (all ten phases in order, every key returned, one fix round, a re-check, a final gate); a missing argument
(a plain sentence); an audit that fails once (repaired by the owners the audit names, then goes on); an audit that always fails (two
repair rounds, no picture drawn); a part that comes back empty (reported as missing, not combined); more parts than the cap (queued,
none skipped, never more than the cap at one moment); nothing to fix (no fix round); a stalled card and a renderer that returns
nothing (no picture, no look checker, no fix round); a fix round whose audit fails or whose pictures cannot be drawn; a re-check that
still finds a fault (no second fix round, and the real judge place_audit_check.py fresh fails the final fresh check); a skeptic that
returns nothing; a blind reader whose prompt would share words with the feature list.
The rules checked on every prompt of every case: it starts "First read <plugin>/agents/place-<role>.md and follow it." (the blind
reader's prompt alone is self-contained, on purpose); the checkers' prompts hold no builder number (every number planted in the
builders' fixture reports starts PLANT-), only the claims as bare sentences; the blind reader's prompt holds neither the request
nor a word of the feature list; no prompt names a verb that explainer-film-place does not print, or an option its --help lacks;
no prompt holds a key, a long hex id, the folder where the rented-card account keeps its settings, an email-like string or the
plugin author's name (read from plugin.json while the test runs, never written here); two runs give the same prompts (resume-safe).
Card time and batches (plugin 1.4.0, batching step): the card-time allowances written in the script equal the house numbers; every builder, fixer, integrator and renderer prompt names the helper's own name, role and the ledger and carries the
batch rule (one sweep, about 10 measurably different versions in ONE batch, at most one more, small quick pictures, full-size once at the very end); the rounds draw small previews only and, when finals are asked for, ONE full-size drawing comes
last, after the re-check and before the gate; the report has a card-time section and flags a helper that reports more seconds than its allowance; the planner is asked to write the person's total for the run; "no rented card" reaches the helpers.
Lessons round (plugin 1.4.0): start small (by default the run draws only the first view's small picture and stops "for the person's reaction";
the other cases pass allViews: true); a place for the film (film: true) gets 1080 x 1920 views, tall previews, and a planner told to run plan_shot.py and to
write "for_film": true; every named view must see a finished horizon (the world round the place, the ground part's job); every Blender run gets a thread
limit (EXPLAINER_FILM_BLENDER_THREADS, blender -t; blenderThreads, default 2); nobody messages a helper that is spending money.
Also: no Date.now, Math.random, new Date() or agentType in the script; the meta block is a pure literal whose phases are the phase()
calls; the reading-test line equals the house number; the agent files have their front matter and name every field of the report they
must return. A part of the test is skipped (exit 77 for the whole test when node is missing) with a plain reason.
Run: python3 kit/calculators/tests/test_build_a_place_workflow.py
"""
import atexit
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, KIT, PLUGIN, TESTS, skip  # noqa: E402

TITLE = 'workflow build-a-place: run with canned helpers'
NODE = shutil.which('node')
if not NODE:
    skip(TITLE, 'node is not installed, so the workflow cannot be run here (the plain-Python parts of the plugin do not need it)')

WORKFLOW = os.path.join(PLUGIN, 'workflows', 'build-a-place.js')
HARNESS = os.path.join(TESTS, 'workflow_harness.mjs')
FIXTURE_FOLDER = os.path.join(FIXTURES, 'place-workflow')
WORK = tempfile.mkdtemp()
atexit.register(shutil.rmtree, WORK, True)      # the test's own scratch folder goes when it ends
check = Checker(TITLE)


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def fixture(name):
    return json.load(open(os.path.join(FIXTURE_FOLDER, name), encoding='utf-8'))


source = read(WORKFLOW)
REQUEST = "Build one side of a small canal lock: brick walls with stone coping, stone steps, a gravel towpath, a timber gate and a few props."
ENVIRONMENT = 'ENVNOTE: the disk is small; only the renderer may use the rented card; nothing else costs money.'
PLUGIN_PATH = '/path/to/explainer-film'
# every case but the start-small ones asks for all views (allViews: true), so the whole run is exercised; the default (start small) has its own cases below
BASE_ARGS = {'plugin': PLUGIN_PATH, 'kit': PLUGIN_PATH + '/kit', 'folder': '/path/to/run', 'request': REQUEST, 'today': '2026-10-22', 'environment': ENVIRONMENT, 'allViews': True}
DEFAULT_RESPONSES = {
    'plan': 'plan.json', 'ground:*': 'ground-report.json', 'build:*': 'part-report.json', 'combine': 'combine-report.json',
    '~^audit\\d*$': 'audit-pass.json', 'render': 'render-report.json', 'check:look': 'check-look.json', 'check:structure': 'check-structure.json',
    'check:process': 'check-process.json', 'blind:1': 'blind-1.json', 'skeptic': 'skeptic.json', 'fix:*': 'part-report-fixed.json',
    'combine:fix': 'combine-report-fixed.json', 'audit:fix': 'audit-pass.json', 'render:fix': 'render-fix.json', 'recheck': 'recheck.json',
    'blind:2': 'blind-2.json', 'gate': 'gate.json', 'render:final': 'render-final.json',
}
PHASES = ['Plan', 'Ground', 'Build parts', 'Combine', 'Audit', 'Render', 'Check', 'Fix', 'Re-check', 'Report']
RESULT_KEYS = ['plan', 'ground', 'parts', 'missing_parts', 'combine', 'audit', 'repairs', 'render', 'final_render', 'card_time', 'checks', 'confirmed', 'fixes', 'recheck',
               'reading_test', 'fresh_check', 'final_gate', 'stopped', 'report_markdown']
AGENT_OF = {'plan': 'planner', 'ground': 'builder', 'build': 'builder', 'repair': 'builder', 'fix': 'builder', 'combine': 'integrator', 'recombine': 'integrator',
            'audit': 'integrator', 'gate': 'integrator', 'render': 'renderer', 'check': 'checker', 'skeptic': 'checker', 'recheck': 'checker'}

ALL_PROMPTS = []     # (case, label, prompt) of every call in every case
CASES = {}


def run_case(name, args=None, responses=None, no_args=False, workflow=None):
    given = copy.deepcopy(BASE_ARGS)
    for key, value in (args or {}).items():
        if value is None:
            given.pop(key, None)
        else:
            given[key] = value
    answers = dict(DEFAULT_RESPONSES)
    answers.update(responses or {})
    path = os.path.join(WORK, f'{name}.json')
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump({'args': None if no_args else given, 'responses': answers}, handle)
    run = subprocess.run([NODE, HARNESS, workflow or WORKFLOW, path, FIXTURE_FOLDER], capture_output=True, text=True, timeout=180)
    try:
        data = json.loads(run.stdout)
    except ValueError:
        data = {'error': 'the harness printed no JSON: ' + (run.stderr or run.stdout)[-400:], 'calls': [], 'phases': [], 'logs': [], 'result': None, 'max_in_flight': {}}
    if workflow is None:
        for call in data['calls']:
            ALL_PROMPTS.append((name, call['label'], call['prompt']))
    CASES[name] = data
    return data


def labels(data):
    return [one_call['label'] for one_call in data['calls']]


def calls(data, pattern):
    return [one_call for one_call in data['calls'] if re.search(pattern, one_call['label'] or '')]


def prompt_of(data, label):
    found = [one_call['prompt'] for one_call in data['calls'] if one_call['label'] == label]
    return found[0] if found else ''


CHECKER_LABELS = r'(check|blind|skeptic|recheck)'


def checkers_that_see_builder_numbers(data):
    """The checkers, skeptic and readers whose prompt holds a number planted in a builder report (every one starts PLANT-)."""
    return [one_call['label'] for one_call in data['calls'] if re.match(CHECKER_LABELS, one_call['label']) and ('PLANT-' in one_call['prompt'] or '48213' in one_call['prompt'] or '187.4' in one_call['prompt'])]


def drew_pictures(data):
    return any(one_label == 'render' or one_label.startswith('render:') for one_label in labels(data))


def blind_prompt_knows_the_request(data):
    return any(REQUEST in one_call['prompt'] or 'ENVNOTE' in one_call['prompt'] for one_call in data['calls'] if one_call['label'].startswith('blind'))


def builders_at_once(data):
    return data['max_in_flight'].get('build', 0)


# --------------------------------------------------------------------------------------------------------- the script itself
def wrapped(text):
    """The script as a module node can read: the body goes inside a function (a script uses await and return at its top level)."""
    return ('export default async function run(args, agent, parallel, pipeline, phase, log, budget, workflow) {\n'
            + text.replace('export const meta = ', 'const meta = ', 1) + '\n}\n')


def node_check(text, name):
    path = os.path.join(WORK, name)
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)
    run = subprocess.run([NODE, '--check', path], capture_output=True, text=True, timeout=60)
    return run.returncode, run.stderr


code, errors = node_check(wrapped(source), 'wrapped.mjs')
check.true('the workflow parses (node --check on a copy wrapped as a module)', code == 0, details=errors.strip()[:300] or 'it parses')
code_bad, _ = node_check(wrapped(source + '\nconst = ;\n'), 'wrapped_bad.mjs')
check.true('  (a copy with a deliberate syntax fault does not parse: the check can fail)', code_bad != 0)

forbidden = [word for word in ('Date.now', 'Math.random', 'agentType', 'process.env', 'require(', 'import(', 'fs.') if word in source]
check.true('the script uses no clock, no random numbers, no file access and no agentType (which was not verified)', not forbidden, details=', '.join(forbidden) or 'none used')
check.true('  (new Date() with no argument is not written)', not re.search(r'new Date\(\s*\)', source))
check.true('the script says in plain words what it does at the top (a "What this does" note)', 'What this does:' in source)

happy = run_case('happy')
check.true('the harness ran the happy path without an error', happy['error'] is None, details=str(happy['error']))
check.true('the meta block is a pure literal (no variables, calls or templates)', happy.get('meta_is_pure_literal') is True)
meta_titles = [phase['title'] for phase in happy.get('meta', {}).get('phases', [])]
called_titles = list(dict.fromkeys(re.findall(r"phase\('([^']+)'\)", source)))
check.equal('the meta phases are the phase() calls of the script, in order', meta_titles, called_titles)
check.equal('the ten phases are Plan, Ground, Build parts, Combine, Audit, Render, Check, Fix, Re-check, Report', meta_titles, PHASES)
check.equal('the phases began in that order on the happy path', happy['phases'], PHASES)
check.true('the meta has a name, a description and a whenToUse', all(happy.get('meta', {}).get(key) for key in ('name', 'description', 'whenToUse')) and happy['meta']['name'] == 'build-a-place')

settings = json.load(open(os.path.join(KIT, 'film-settings.json'), encoding='utf-8'))
line = re.search(r'READING_LINE = ([0-9.]+)', source)
check.close('the reading-test line in the script equals the house number place_measures.reading_test_share_min',
            float(line.group(1)) if line else None, settings['place_measures']['reading_test_share_min']['value'], 1e-9,
            recorded='kit/film-settings.json place_measures.reading_test_share_min', proves='the script and the house numbers cannot drift apart')
check.equal('the house number place_checks.fix_rounds is 1 (the script does exactly one fix round)', settings['place_checks']['fix_rounds']['value'], 1)

# --------------------------------------------------------------------------------------------------------------- happy path
check.equal('happy: every key of the result is there', sorted(happy['result'].keys()), sorted(RESULT_KEYS))
check.true('happy: no canned answer failed its schema and no schema was malformed',
           all(not one_call['schema_problems'] for one_call in happy['calls']), details='; '.join(f"{one_call['label']}: {one_call['schema_problems'][:2]}" for one_call in happy['calls'] if one_call['schema_problems']) or 'all fit')
labs = labels(happy)
check.equal('happy: the helpers ran in this order (plan, ground, builders, combine, audit, render, checkers, skeptic, one fix round, re-check, gate)',
            labs, ['plan', 'ground:ground_and_water', 'build:walls_and_steps', 'build:lock_gate', 'build:props', 'build:bank_planting', 'combine', 'audit', 'render',
                   'check:look', 'check:structure', 'check:process', 'blind:1', 'skeptic', 'fix:lock_gate', 'fix:walls_and_steps', 'combine:fix', 'audit:fix', 'render:fix',
                   'recheck', 'blind:2', 'gate'])
check.true('happy: the audit helper ran before the renderer (nothing is drawn before the audit)', labs.index('audit') < labs.index('render'))
check.equal('happy: exactly one fix round: one fixer per owner with a confirmed finding (lock_gate, walls_and_steps), and the settings finding goes to the integrator',
            [one_label for one_label in labs if one_label.startswith('fix:')], ['fix:lock_gate', 'fix:walls_and_steps'])
check.true('  (no second fix round: the re-check problems are reported, not fixed)', labs.count('combine:fix') == 1 and labs.count('render:fix') == 1 and not any(re.match(r'fix\d', one_label) for one_label in labs))
gate_prompt = prompt_of(happy, 'build:lock_gate')
check.true('the plugin\'s own steps are in every builder prompt whatever the brief says: the part pass (finish-part), the construction check and the stage-file safety run, each as a real command',
           all('explainer-film-place ' + step in gate_prompt for step in ('finish-part --scene /path/to/run/work/lock_gate/scene.blend', 'construction --scene /path/to/run/work/lock_gate/part.blend', 'combine --scene /path/to/run/scene/ground.blend --stages /path/to/run/stages/stage_lock_gate.py'))
           and 'THE STEPS THE PLUGIN ADDS' in gate_prompt and 'never has to ask' in gate_prompt)
check.true('  (the ground part and a fixer get them too; the ground part checks its stage on the starting scene, the others on the frozen ground)',
           all('THE STEPS THE PLUGIN ADDS' in prompt_of(happy, label) for label in ('ground:ground_and_water', 'fix:lock_gate'))
           and 'combine --scene /path/to/run/scene/start.blend' in prompt_of(happy, 'ground:ground_and_water'))
check.true('the ground builder is told the quick way to freeze the ground (combine on the starting scene, saved as the ground file)',
           'explainer-film-place combine --scene /path/to/run/scene/start.blend --stages /path/to/run/stages/stage_ground_and_water.py --order plain' in prompt_of(happy, 'ground:ground_and_water')
           and '--save-as /path/to/run/scene/ground.blend' in prompt_of(happy, 'ground:ground_and_water'))
check.true('happy: the squint miss is reported as not fixed on purpose (in the report) and no fixer is given its finding (the far hills)',
           'NOT FIXED ON PURPOSE' in happy['result']['report_markdown'] and 'far hills' in happy['result']['report_markdown']
           and not any('far hills' in prompt_of(happy, one_label) for one_label in ('fix:lock_gate', 'fix:walls_and_steps', 'combine:fix')))
check.true('happy: the fixers got only their own findings (lock_gate: the board, not the coping stones)',
           'gate board' in prompt_of(happy, 'fix:lock_gate') and 'coping stones' not in prompt_of(happy, 'fix:lock_gate')
           and 'coping stones' in prompt_of(happy, 'fix:walls_and_steps') and 'gate board' not in prompt_of(happy, 'fix:walls_and_steps'))
check.true('happy: the settings finding went to the recombine (the integrator), not to a builder',
           'preview cameras' in prompt_of(happy, 'combine:fix') and 'preview cameras' not in prompt_of(happy, 'fix:lock_gate'))
check.true('happy: the fix round redrew only the view the fixers named (towpath_close)', 'towpath_close: camera' in prompt_of(happy, 'render:fix') and 'wide: camera' not in prompt_of(happy, 'render:fix'))
check.true('happy: the redraw used the existing guard and gave the previous pictures for the squint test',
           'do not make a new one' in prompt_of(happy, 'render:fix') and 'wide_preview.jpg' in prompt_of(happy, 'render:fix'))
reading = happy['result']['reading_test']
check.true('happy: the reading test counted the blind reader\'s words against the planned features (13 of 16 on round 1, 4 of 16 after the fix)',
           happy['logs'] and any('13 of 16' in one_label for one_label in happy['logs']) and reading['round'] == 2 and reading['found'] == 4 and reading['passed'] is False,
           details=f"final round {reading['round']}: {reading['found']} of {reading['planned']}")
first_test = [result for result in [happy['result']['checks']['blind_reader']] if result]
check.true('happy: the first reading test passed (13 of 16 is over the 75 percent line) and was blind', any('Reading test: 13 of 16 planned features named (passed)' in one_label for one_label in happy['logs'])
           and 'blind: yes' in happy['result']['report_markdown'])
check.true('happy: the report is plain words with the request, the audit, the pictures, the checkers, the fix round, the final gate and what was not tested',
           all(heading in happy['result']['report_markdown'] for heading in ('## What I did', '## The audit', '## Pictures', '## What the fresh checkers found', '## The fix round',
                                                                  '## The final gate', '## What was not tested', '## Every failure', '## For you to decide', REQUEST)))
check.true('happy: the report says what is an ESTIMATE and what is PROVISIONAL, and measured versus judged',
           all(word in happy['result']['report_markdown'] for word in ('ESTIMATE', 'PROVISIONAL', 'MEASURED', 'JUDGED')))
check.true('happy: the final gate ran last, on the fixed scene (round 2)', labs[-1] == 'gate' and '/round2/finished.blend' in prompt_of(happy, 'gate'))
check.true('happy: a job file, pictures and half-size copies are named in the render prompt, with the renderer rule in the film owner\'s words',
           all(word in prompt_of(happy, 'render') for word in ('job-round1.json', 'half/round1', "film owner's rule", 'view-1.jpg')))
check.true('happy: the render command is the real verb with a valid shape', 'explainer-film-place render --scene /path/to/run/scene/round1/finished.blend --job /path/to/run/render/job-round1.json --where auto --engine auto' in prompt_of(happy, 'render'))

# ------------------------------------------------------------------------------------- the rules on every prompt of the happy path
for call in happy['calls']:
    label = call['label']
    group = re.sub(r'\d+$', '', label.split(':')[0])
    if group == 'blind':
        continue
    role = AGENT_OF.get(group)
    expected = f'First read {PLUGIN_PATH}/agents/place-{role}.md and follow it.'
    if not call['prompt'].startswith(expected):
        check.true(f'prompt of {label} starts "{expected}"', False, details=call['prompt'][:100])
        break
else:
    check.true('every prompt (except the blind reader\'s) starts "First read <plugin>/agents/place-<role>.md and follow it." with the right agent', True, details=f'{len(happy["calls"])} prompts')
check.true('every prompt (except the blind reader\'s) says what ${CLAUDE_PLUGIN_ROOT} means (a helper that reads an agent file with the Read tool does not get it expanded)',
           all(f'${{CLAUDE_PLUGIN_ROOT}} means the plugin folder: {PLUGIN_PATH}' in one_call['prompt'] for one_call in happy['calls'] if not one_call['label'].startswith('blind')))
check.true('every prompt carries the request exactly and the environment notes, except the blind reader\'s and the planner-independent ones that need neither',
           all(REQUEST in one_call['prompt'] and 'ENVNOTE' in one_call['prompt'] for one_call in happy['calls'] if not one_call['label'].startswith(('blind', 'audit', 'combine', 'recombine', 'gate', 'render:fix'))
               and 'THE RUN' in one_call['prompt']))
check.true('every prompt except the blind reader\'s holds the rules (no money, no commit, no keys, never lower a requirement)',
           all('Spend no money' in one_call['prompt'] and 'Never commit or push' in one_call['prompt'] and 'Never lower a requirement' in one_call['prompt'] for one_call in happy['calls'] if not one_call['label'].startswith('blind')))
check.true('the effort: builders and the others medium, checkers high', all(one_call['effort'] == 'high' for one_call in happy['calls'] if re.match(r'(check|blind|skeptic|recheck)', one_call['label']))
           and all(one_call['effort'] == 'medium' for one_call in happy['calls'] if not re.match(r'(check|blind|skeptic|recheck)', one_call['label'])))

part = fixture('part-report.json')
ground = fixture('ground-report.json')
planted = ['PLANT-']
check.true('the builders\' fixture reports really carry planted numbers (so the next checks can fail)', 'PLANT-' in json.dumps(part) and str(part['triangles']) in json.dumps(part))
checker_calls = [one_call for one_call in happy['calls'] if re.match(CHECKER_LABELS, one_call['label'])]
leaks = checkers_that_see_builder_numbers(happy)
check.true('no checker, skeptic or reader prompt holds a number from a builder report (they get bare claims only)', not leaks and len(checker_calls) == 7, details=', '.join(leaks) or f'{len(checker_calls)} prompts clean')
look = prompt_of(happy, 'check:look')
check.true('the look checker gets the claims as bare sentences with the owner (the measured result in brackets is cut off)',
           '[walls_and_steps] every post of the walls_and_steps part stands on the ground\n' in look and '6 posts' not in look and 'measured:' not in look)
check.true('  (a builder\'s own "measured_by" text is never given to a checker)', 'construction.json' not in look and 'minimum supports' not in look)
check.true('the structure checker gets the same claims; the process checker gets none of them', 'every post of the lock_gate part' in prompt_of(happy, 'check:structure') and 'every post of the lock_gate part' not in prompt_of(happy, 'check:process'))
check.true('the look checker is told it was NOT blind to the feature list; the process checker is told to keep out of the work folder',
           'you were NOT blind' in look and 'do not open the work folder' in prompt_of(happy, 'check:process'))
blind = prompt_of(happy, 'blind:1')
check.true('the blind reader\'s prompt is self-contained: it does not start "First read", names no agent file, holds neither the request nor the environment nor any feature',
           not blind.startswith('First read') and '/agents/' not in blind and REQUEST not in blind and 'ENVNOTE' not in blind and 'canal' not in blind.lower()
           and not re.search(r'\b(' + '|'.join(re.escape(word) for feature in fixture('plan.json')['readable_features'] for word in feature['keywords']) + ')', blind.lower()))
check.true('the blind reader is shown half-size pictures with number-only names, and nothing else',
           all(f'view-{number}.jpg' in blind for number in (1, 2, 3)) and '_preview' not in blind and 'style-note' not in blind and 'wide' not in blind)
check.true('the blind reading test is labelled blind, and says it is a crude keyword match', happy['result']['checks']['blind_reader'] is not None
           and 'keyword match' in json.dumps(happy['result']['reading_test']))

# a skeptic that fails: findings stay unverified
# ------------------------------------------------------------------------------------------------------------ determinism
again = run_case('happy_again')
check.true('two runs give the same prompts, in the same order (the script can be resumed)', [one_call['prompt'] for one_call in again['calls']] == [one_call['prompt'] for one_call in happy['calls']])

# ----------------------------------------------------------------------------------------------------------- missing argument
bad = run_case('no_request', args={'request': None})
check.true('a missing request stops the run at once with a plain sentence that names args.request',
           bad['error'] and 'build-a-place cannot start' in bad['error'] and 'args.request' in bad['error'] and 'args.plugin' not in bad['error'] and not bad['calls'], details=str(bad['error']))
bad = run_case('nothing', no_args=True)
check.true('no args at all lists every missing argument', bad['error'] and all(f'args.{key}' in bad['error'] for key in ('plugin', 'kit', 'folder', 'request')), details=str(bad['error']))

# ------------------------------------------------------------------------------------------- audit fails once, then is repaired
once = run_case('audit_once', responses={'~^audit\\d*$': ['audit-fail.json', 'audit-pass.json'], '~^repair\\d+:': 'part-report-fixed.json', '~^recombine\\d+$': 'combine-report-fixed.json'})
labs = labels(once)
check.true('audit fails once: the owners the audit names repair it (lock_gate, ground_and_water), the integrator combines again, the audit passes, the run goes on',
           'repair1:lock_gate' in labs and 'repair1:ground_and_water' in labs and 'recombine1' in labs and 'audit1' in labs and 'render' in labs and 'repair2:lock_gate' not in labs,
           details=', '.join(labs[:14]))
check.true('  (only one repair round was recorded, and nothing was drawn before the second audit passed)', len(once['result']['repairs']) == 1 and labs.index('audit1') < labs.index('render'))
check.true('  (each repairer got only its own problem; the settings problem went to the recombine; the ground repair told the integrator to rebuild the ground)',
           'AUDITGATE' in prompt_of(once, 'repair1:lock_gate') and 'AUDITGROUND' not in prompt_of(once, 'repair1:lock_gate') and 'AUDITSETTINGS' not in prompt_of(once, 'repair1:lock_gate')
           and 'AUDITSETTINGS' in prompt_of(once, 'recombine1') and 'THE GROUND STAGE WAS CHANGED' in prompt_of(once, 'recombine1'))
check.true('  (the second audit was asked to prove the second round\'s file, and the renderer drew that file)',
           '/round2/finished.blend' in prompt_of(once, 'audit1') and '/round2/finished.blend' in prompt_of(once, 'render'))

# ------------------------------------------------------------------------------------------- audit always fails: two repairs, no picture
always = run_case('audit_always', responses={'~^audit\\d*$': 'audit-fail.json', '~^repair\\d+:': 'part-report-fixed.json', '~^recombine\\d+$': 'combine-report-fixed.json'})
labs = labels(always)
check.true('an audit that always fails stops after two repair rounds and before any picture', always['result']['stopped'] and 'still fails' in always['result']['stopped']
           and not drew_pictures(always) and not any(one_label.startswith(('check', 'blind', 'skeptic', 'fix:')) for one_label in labs) and labs.count('audit') + len([one_label for one_label in labs if re.match(r'audit\d', one_label)]) == 3
           and 'repair2:lock_gate' in labs and 'repair3:lock_gate' not in labs and always['phases'][-1] == 'Audit', details=', '.join(labs))
check.true('  (it returns every key, with null for what did not run, and the report names the failing problems and who must decide)',
           sorted(always['result'].keys()) == sorted(RESULT_KEYS) and always['result']['render'] is None and 'AUDITGATE' in always['result']['report_markdown']
           and 'Only you can accept a problem' in always['result']['report_markdown'])
more = run_case('audit_always_five', args={'maxRepairRounds': 5}, responses={'~^audit\\d*$': 'audit-fail.json', '~^repair\\d+:': 'part-report-fixed.json', '~^recombine\\d+$': 'combine-report-fixed.json'})
check.true('asking for five repair rounds still gives only two', 'repair3:lock_gate' not in labels(more) and len(more['result']['repairs']) == 2)
none = run_case('audit_no_repairs', args={'maxRepairRounds': 0}, responses={'~^audit\\d*$': 'audit-fail.json'})
check.true('asking for no repair rounds stops at the first failing audit', not [one_label for one_label in labels(none) if one_label.startswith('repair')] and none['result']['stopped'])

# ------------------------------------------------------------------ the audit helper's word against the preflight's exit code
liar = dict(fixture('audit-pass.json'), preflight_exit_code=1)
lied = run_case('audit_liar', responses={'~^audit\\d*$': [liar, 'audit-pass.json'], '~^recombine\\d+$': 'combine-report-fixed.json'})
check.true('an audit helper that says pass while the preflight exited 1 is not believed: the exit code is a fact, the word is a claim',
           'recombine1' in labels(lied) and "the helper said the audit passed, but the preflight's exit code was 1" in prompt_of(lied, 'recombine1'))

# --------------------------------------------------------------------------------------------------------- a part comes back empty
miss = run_case('missing_part', responses={'build:lock_gate': None})
check.true('a part that returns nothing is reported as missing, not dropped quietly',
           miss['result']['missing_parts'] == ['lock_gate'] and 'MISSING parts' in miss['result']['report_markdown'] and 'lock_gate' in miss['result']['report_markdown'])
check.true('  (it is not combined: the integrator is told, and its stage file is not in the list)',
           'did NOT report (do not combine them; list them as missing in your answer): lock_gate' in prompt_of(miss, 'combine') and 'stage_lock_gate.py' not in prompt_of(miss, 'combine')
           and 'stage_walls_and_steps.py' in prompt_of(miss, 'combine'))
check.true('  (the other parts and the run carry on to the end)', labels(miss)[-1] == 'gate' and [part['owner'] for part in miss['result']['parts']] == ['ground_and_water', 'walls_and_steps', 'props', 'bank_planting'])
absent = run_case('missing_then_audit', responses={'build:lock_gate': None, '~^audit\\d*$': ['audit-fail.json', 'audit-pass.json'], '~^repair\\d+:': 'part-report-fixed.json', '~^recombine\\d+$': 'combine-report-fixed.json'})
check.true('problems of a part that never reported are not sent to a builder that has nothing to fix; the report says so',
           'repair1:lock_gate' not in labels(absent) and 'never reported' in absent['result']['report_markdown'])
nobody = run_case('no_builder', responses={'build:*': None})
check.true('when no builder reports, the run stops and says so', nobody['result']['stopped'] and 'no builder came back' in nobody['result']['stopped'] and 'combine' not in labels(nobody))
noground = run_case('no_ground', responses={'ground:*': None})
check.true('when the ground comes back with nothing, nothing else is built', noground['result']['stopped'] and 'ground' in noground['result']['stopped'] and not [one_label for one_label in labels(noground) if one_label.startswith('build')])
noplan = run_case('no_plan', responses={'plan': None})
check.true('when the planner returns nothing, the run stops with a report', noplan['result']['stopped'] and labels(noplan) == ['plan'] and noplan['result']['report_markdown'])

# --------------------------------------------------------------------------------------------- more parts than the cap: queued
many = run_case('queue', args={'maxParallelBuilders': 3}, responses={'plan': 'plan-many.json'})
builds = [one_label for one_label in labels(many) if one_label.startswith('build:')]
check.true('with 10 parts to build and room for 3, every part is built exactly once (queued, none skipped)', len(builds) == 10 and len(set(builds)) == 10, details=f'{len(builds)} builds')
check.true('  (never more than 3 builders at one moment, and really 3 at a time)', builders_at_once(many) == 3, details=f"most at once: {builders_at_once(many)}")
check.true('  (the run says that the rest wait in a queue)', any('wait in a queue' in one_label for one_label in many['logs']))
default_cap = run_case('queue_default', responses={'plan': 'plan-many.json'})
check.true('the default cap is 4', builders_at_once(default_cap) == 4)

# --------------------------------------------------------------------------------------------------- nothing to fix, no skeptic
clean = run_case('clean', responses={'check:look': 'check-clean.json', 'check:structure': 'check-clean.json', 'check:process': 'check-process-clean.json'})
labs = labels(clean)
check.true('when the checkers find nothing there is no skeptic, no fix round and no re-check, but the phases are still entered and the gate runs',
           'skeptic' not in labs and not any(one_label.startswith(('fix', 'combine:fix', 'recheck', 'blind:2')) for one_label in labs) and clean['phases'] == PHASES and labs[-1] == 'gate')
check.true('  (the report says nothing was fixed)', 'Nothing was fixed' in clean['result']['report_markdown'])
sev = run_case('nothing_severe', responses={'skeptic': 'skeptic-nothing-severe.json'})
check.true('when only a minor finding is confirmed there is no fix round, and the minor finding is still in the report',
           not any(one_label.startswith('fix:') for one_label in labels(sev)) and 'MINOR' in sev['result']['report_markdown'])
silent = run_case('skeptic_null', responses={'skeptic': None})
check.true('a skeptic that returns nothing leaves the findings unconfirmed: reported, not acted on',
           not any(one_label.startswith('fix:') for one_label in labels(silent)) and 'NOT CONFIRMED' in silent['result']['report_markdown'])

squint_skeptic = fixture('skeptic.json')
squint_skeptic['confirmed'].append({'what': 'squint test miss: the far hills lose most', 'where': 'wide view', 'severity': 'should fix', 'cheapest_fix': 'remove detail from the far hills',
                                    'owner': 'bank_planting', 'evidence': 'the measure', 'from': 'look checker'})
squint = run_case('squint_confirmed', responses={'skeptic': squint_skeptic})
check.true('a squint-test miss whose cure is to remove character is never sent to a fixer, even when a skeptic confirmed it; it goes to the person',
           not any('far hills' in call['prompt'] for call in squint['calls'] if call['label'].startswith(('fix:', 'combine:fix')))
           and 'bank_planting' not in ' '.join(call['label'] for call in squint['calls'] if call['label'].startswith('fix:'))
           and 'NOT FIXED ON PURPOSE' in squint['result']['report_markdown'] and 'remove detail from the far hills' in squint['result']['report_markdown'])

# ---------------------------------------------------------------------------------------- no pictures: stalled card, empty renderer
for name, answer in (('stalled', 'render-stalled.json'), ('render_null', None)):
    run = run_case(name, responses={'render': answer})
    labs = labels(run)
    check.true(f'{name}: no look checker, no blind reader, no fix round and no re-check; the structure and process checkers still run',
               'check:structure' in labs and 'check:process' in labs and 'check:look' not in labs and 'blind:1' not in labs and not any(one_label.startswith('fix:') for one_label in labs) and 'recheck' not in labs)
    check.true(f'  ({name}: the report says what happened and the queue was never touched)', ('five minutes' in run['result']['report_markdown'] or 'came back with nothing' in run['result']['report_markdown'])
               and 'purge' not in ' '.join(one_call['prompt'] for one_call in run['calls']).replace('never purge', '').replace('Never purge', ''))

# ------------------------------------------------------------------------------------------------- the fix round that goes wrong
fa = run_case('fix_audit_fails', responses={'audit:fix': 'audit-fail.json'})
labs = labels(fa)
check.true('when the audit after the fix round fails, nothing is drawn again, there is no re-check, and the first audited file stays final',
           'render:fix' not in labs and 'recheck' not in labs and '/round1/finished.blend' in prompt_of(fa, 'gate') and 'does not pass' in fa['result']['report_markdown'])
fr = run_case('fix_render_fails', responses={'render:fix': None})
check.true('when the pictures after the fix round cannot be drawn there is no re-check and the first audited file stays final',
           'recheck' not in labels(fr) and '/round1/finished.blend' in prompt_of(fr, 'gate') and 'nobody has looked at it' in fr['result']['report_markdown'])
rc = run_case('recheck_fails', responses={'recheck': 'recheck-still-failing.json'})
check.true('a re-check that still finds a fault does not start a second fix round, and the fault is in the report',
           [one_label for one_label in labels(rc) if one_label.startswith('fix')] == ['fix:lock_gate', 'fix:walls_and_steps'] and 'still floats 1 cm' in rc['result']['report_markdown'])

# ---------------------------------------------------------------------------------------- the fresh check closes the loop
judge = os.path.join(KIT, 'calculators', 'place_audit_check.py')


def judge_fresh(data, name):
    path = os.path.join(WORK, name)
    json.dump(data['result']['fresh_check'], open(path, 'w'))
    run = subprocess.run([sys.executable, '-I', '-B', judge, 'fresh', path, '--out', os.path.join(WORK, name + '.out.json')], capture_output=True, text=True, timeout=60)
    return run.returncode, run.stdout + run.stderr


if os.path.exists(judge):
    code, text = judge_fresh(clean, 'fresh_clean.json')
    check.true('the fresh-check object of a clean run is accepted by the real judge (place_audit_check.py fresh): no FAIL and no shape complaint', code == 0 and 'lacks' not in text, details=text.strip().splitlines()[0][:160] if text.strip() else f'exit {code}')
    code, text = judge_fresh(happy, 'fresh_happy.json')
    check.true('the fresh-check object after a fix round (the re-check\'s answer) is accepted by the real judge', code == 0 and 'lacks' not in text, details=text.strip().splitlines()[0][:160] if text.strip() else f'exit {code}')
    code, text = judge_fresh(rc, 'fresh_failing.json')
    check.true('a fresh check that still has a fault that does not hold FAILS in the real judge (an unfixed finding cannot slip through)', code == 1 and 'FAIL' in text, details=f'exit {code}')
    check.true('  (the object carries the SHA-1 the checker gave, for the judge to compare)', happy['result']['fresh_check'].get('audit_scene_sha1') == 'fixture-sha1-round-1')
else:
    check.note('skipped: the judge calculators/place_audit_check.py is not there yet, so the fresh-check shape was not tried on it')

# ------------------------------------------------------------------------------------------------ blind reader that is not blind
leaky_plan = fixture('plan.json')
leaky_plan['readable_features'][0]['keywords'].append('pictures')
leaky = run_case('leaky', responses={'plan': leaky_plan})
check.true('when the blind reader\'s prompt would share a word with the feature list, the reading test says it was not blind',
           leaky['result']['checks']['blind_reader'] is not None and any('shares words' in one_label and 'pictures' in one_label for one_label in leaky['logs'])
           and 'blind: no' in leaky['result']['report_markdown'])

# --------------------------------------------------------------------------------------------- the arguments change the prompts
cheap = run_case('options', args={'renderer': 'eevee', 'rented': False, 'finals': True, 'effort': 'low', 'checkEffort': 'max', 'blender': '/path/to/blender',
                                  'references': ['/path/to/reference.jpg'], 'accepted': '/path/to/accepted.json', 'ledger': '/path/to/ledger.json'})
check.true('renderer eevee and rented false change the render command; finals true does NOT make the rounds draw full size (they stay small and quick), the ONE full-size drawing comes last',
           '--where local --engine eevee --helper renderer' in prompt_of(cheap, 'render') and '--finals' not in prompt_of(cheap, 'render') and '--finals' not in prompt_of(cheap, 'render:fix')
           and '--where local --engine eevee --finals' in prompt_of(cheap, 'render:final'))
check.true('effort low for builders, max for checkers; the planner follows the effort', [one_call['effort'] for one_call in cheap['calls'] if one_call['label'] == 'plan'] == ['low']
           and all(one_call['effort'] == 'max' for one_call in cheap['calls'] if re.match(r'(check|skeptic|recheck|blind)', one_call['label'])))
check.true('the Blender path reaches the helpers; the reference pictures reach the planner and the renderer (the guard is not provisional); the accepted file reaches the audit; the ledger the process checker',
           '--blender /path/to/blender' in prompt_of(cheap, 'build:lock_gate') and '/path/to/reference.jpg' in prompt_of(cheap, 'plan') and 'the reference pictures: /path/to/reference.jpg' in prompt_of(cheap, 'render')
           and '--accepted /path/to/accepted.json' in prompt_of(cheap, 'audit') and '/path/to/ledger.json' in prompt_of(cheap, 'check:process'))
given_parts = run_case('given_parts', args={'parts': [{'name': 'pump_house', 'owner': 'pump_house', 'brief': 'a small pump house'}], 'views': [{'name': 'sunset', 'size': [600, 400]}]})
check.true('a part the person asked for that the planner left out is added with its brief and built; the person\'s views win over the planner\'s',
           'build:pump_house' in labels(given_parts) and any('pump_house' in one_label and 'added' in one_label for one_label in given_parts['logs']) and 'sunset: camera "View sunset", 600 x 400' in prompt_of(given_parts, 'render')
           and 'wide: camera' not in prompt_of(given_parts, 'render'))
check.true('every non-blind prompt names the folders of the run and the place and preflight commands by full path',
           all('/path/to/run' in one_call['prompt'] and f'{PLUGIN_PATH}/bin/explainer-film-place' in one_call['prompt'] for one_call in happy['calls'] if not one_call['label'].startswith('blind')))

# ------------------------------------------------------------------------ card time and batches (the batching step)
card_minutes_text = re.search(r'const CARD_MINUTES = \{([^}]*)\}', source)
written_minutes = {role: float(number) for role, number in re.findall(r'(\w+):\s*(\d+)', card_minutes_text.group(1))} if card_minutes_text else {}
house_minutes = {role: float(row['value']) for role, row in settings['place_card_time']['allowance_minutes'].items()}
check.true('the card-time allowances written in the script (builder, fixer, integrator, renderer, checker, planner) equal the house numbers place_card_time.allowance_minutes',
           written_minutes and all(house_minutes[role] == minutes for role, minutes in written_minutes.items()) and {'builder', 'fixer', 'integrator', 'renderer', 'checker', 'planner'} <= set(written_minutes),
           details=f'script {written_minutes}, house {house_minutes}')
LEDGER_PATH = '/path/to/run/card-time-ledger.jsonl'
builder_text = prompt_of(happy, 'build:lock_gate')
check.true('card time: a builder\'s prompt gives its own helper name, its role, the run\'s ledger and its allowance, and carries the batch rule (one sweep, about 10 variations in ONE batch, at most one more, small quick pictures, full-size once at the end)',
           f'--helper builder-lock_gate --role builder --ledger {LEDGER_PATH}' in builder_text and 'Your allowance is 10 minutes' in builder_text and 'THE BATCH RULE' in builder_text
           and 'batched-rounds-and-card-time.md' in builder_text and 'ONE sweep' in builder_text and 'about 10 variations' in builder_text and 'ONE batch' in builder_text and 'at most ONE more batch' in builder_text
           and 'full-size pictures are drawn once, at the very end' in builder_text and 'variations plan FILE.json' in builder_text)
check.true('  (the ground builder, a fixer and a repairer have their own names and the fixer\'s 5 minutes; the integrator and the renderer theirs)',
           '--helper builder-ground_and_water --role builder' in prompt_of(happy, 'ground:ground_and_water') and '--helper fixer-lock_gate --role fixer' in prompt_of(happy, 'fix:lock_gate')
           and 'Your allowance is 5 minutes' in prompt_of(happy, 'fix:lock_gate') and '--helper fixer-lock_gate --role fixer' in prompt_of(once, 'repair1:lock_gate')
           and '--helper integrator --role integrator' in prompt_of(happy, 'combine') and 'Your allowance is 10 minutes' in prompt_of(happy, 'combine')
           and f'--helper renderer --role renderer --ledger {LEDGER_PATH}' in prompt_of(happy, 'render'))
check.true('  (the planner is told it has no card time and which allowances the others have; the process checker gets the ledger and the allowances and is asked to compare)',
           'you have none' in prompt_of(happy, 'plan') and 'builder 10 minutes, fixer 5' in prompt_of(happy, 'plan') and LEDGER_PATH in prompt_of(happy, 'check:process')
           and 'THE CARD-TIME LEDGER' in prompt_of(happy, 'check:process') and 'match the ledger' in prompt_of(happy, 'check:process') and 'more than two batches' in prompt_of(happy, 'check:process'))
check.true('the rounds draw small quick pictures only: no render prompt of the happy path asks for --finals, and each says finals come once, at the very end',
           all('--finals' not in prompt_of(happy, one_label) for one_label in ('render', 'render:fix')) and 'ONCE, at the very end' in prompt_of(happy, 'render') and 'render:final' not in labels(happy))
check.true('the report has a Card time section: each helper\'s reported card seconds against its allowance, the total, and that seconds are not a bill',
           '## Card time' in happy['result']['report_markdown'] and 'renderer (renderer): 60 card seconds of 600 allowed' in happy['result']['report_markdown']
           and 'fixer-lock_gate (fixer): 61.5 card seconds of 300 allowed; 1 batch(es)' in happy['result']['report_markdown'] and 'never a bill' in happy['result']['report_markdown'],
           details=re.sub(r'\s+', ' ', happy['result']['report_markdown'].split('## Card time')[-1][:300]))
summary = happy['result']['card_time']
check.true('the result carries card_time: the ledger path, the allowances, what each helper reported (the largest ledger total of a helper that reported twice), and nobody over',
           summary['ledger'] == LEDGER_PATH and summary['over_allowance'] == [] and summary['allowance_minutes']['builder'] == 10
           and {row['name'] for row in summary['reported']} >= {'renderer', 'fixer-lock_gate', 'builder-lock_gate'} and next(row for row in summary['reported'] if row['name'] == 'renderer')['card_seconds'] == 60.0,
           details=str(summary['reported'][:3]))
over = run_case('over_allowance', responses={'build:lock_gate': dict(part, card_seconds=700, batches=3)})
check.true('a helper that reports more card seconds than its allowance (700 of 600) is named in the result and the report says OVER ITS ALLOWANCE; the process checker is told what was reported',
           'builder-lock_gate' in over['result']['card_time']['over_allowance'] and 'OVER ITS ALLOWANCE' in over['result']['report_markdown'] and '700' in prompt_of(over, 'check:process'))
finals = run_case('finals', args={'finals': True})
flabs = labels(finals)
check.true('finals asked for: the ONE full-size drawing is a single call after the re-check and just before the gate, from the last audited file (the fixed one), only final-size views, no extra preview',
           flabs.count('render:final') == 1 and flabs.index('recheck') < flabs.index('render:final') < flabs.index('gate') and flabs[-1] == 'gate' and '/round2/finished.blend' in prompt_of(finals, 'render:final')
           and 'ONE FULL-SIZE DRAWING OF THE RUN' in prompt_of(finals, 'render:final') and '"kinds": ["final"]' in prompt_of(finals, 'render:final') and ' --finals ' in prompt_of(finals, 'render:final') + ' ',
           details=', '.join(flabs[-6:]))
check.true('  (the earlier rounds still drew small previews only; the result holds the final render, and the report says full-size pictures were drawn once at the very end)',
           all('--finals' not in prompt_of(finals, one_label) for one_label in ('render', 'render:fix')) and finals['result']['final_render'] and 'drawn once at the very end' in finals['result']['report_markdown']
           and 'renderer (renderer): 152' in finals['result']['report_markdown'])
nopics = run_case('finals_no_pictures', args={'finals': True}, responses={'render': None})
check.true('finals asked for but there are no pictures to build on: no full-size drawing, and the report says so',
           'render:final' not in labels(nopics) and 'asked for, but there were no pictures' in nopics['result']['report_markdown'])
failed_finals = run_case('finals_fail', args={'finals': True}, responses={'render:final': None})
check.true('a full-size drawing that comes back empty is reported (not silently dropped) and does not stop the gate',
           failed_finals['result']['final_render'] is None and 'full-size pictures could not be drawn' in failed_finals['result']['report_markdown'] and labels(failed_finals)[-1] == 'gate')
team = run_case('card_team', args={'cardTeamMinutes': 30, 'cardLedger': '/path/to/shared/card-ledger.jsonl', 'cardClient': 'python3 -I /path/to/card_client.py'})
check.true('a total for the whole run and a ledger file given in the arguments reach the planner and every helper; the report names the total',
           'card-time start --team-minutes 30 --ledger /path/to/shared/card-ledger.jsonl' in prompt_of(team, 'plan') and '--ledger /path/to/shared/card-ledger.jsonl' in prompt_of(team, 'build:lock_gate')
           and 'the person\'s total for the run: 30 minutes' in team['result']['report_markdown'] and 'The person set no total' in prompt_of(happy, 'plan'))
check.true('a card client named in the arguments reaches the builders\' batch command as --card-client (and is not in the prompts when none was named)',
           'variations run FILE.json --where auto --card-client "python3 -I /path/to/card_client.py"' in prompt_of(team, 'build:lock_gate') and '--card-client' not in prompt_of(happy, 'build:lock_gate'))
check.true('"rented: false" reaches every helper that could use the card: no card in this run, a batch only locally on a tiny scene',
           'no rented card in this run' in prompt_of(cheap, 'build:lock_gate') and 'no rented card in this run' in prompt_of(cheap, 'render') and 'no rented card in this run' not in builder_text)

# ------------------------------------------------------------------------ the lessons round: start small, the film frame, threads, the world
small = run_case('first_view_only', args={'allViews': None}, responses={'render': 'render-first-view.json'})
slabs = labels(small)
check.true('start small (the default, no allViews): the run builds, audits, draws ONLY the first view and stops there for the person\'s reaction (no checker, no fixer, no other view)',
           slabs[-1] == 'render' and slabs.count('render') == 1 and not any(one_label.startswith(('check', 'blind', 'skeptic', 'fix', 'gate', 'render:')) for one_label in slabs)
           and small['phases'][-1] == 'Render' and small['result']['stopped'] and "stopped for the person's reaction" in small['result']['stopped'], details=', '.join(slabs[-4:]))
check.true('  (the render prompt names only the first view, says it is the one small test, and the report tells the person how to go on)',
           'wide: camera "View wide"' in prompt_of(small, 'render') and 'towpath_close: camera' not in prompt_of(small, 'render') and 'START SMALL' in prompt_of(small, 'render')
           and 'allViews: true' in small['result']['report_markdown'] and sorted(small['result'].keys()) == sorted(RESULT_KEYS))
check.true('  (the planner is told to name first the view that shows the most of the request)', 'START SMALL' in prompt_of(small, 'plan') and 'Name first the view' in prompt_of(small, 'plan'))
again_small = run_case('first_view_false', args={'allViews': None, 'firstViewOnly': False})
check.true('  (firstViewOnly: false goes on to the end like allViews: true)', labels(again_small)[-1] == 'gate' and 'START SMALL' not in prompt_of(again_small, 'render'))
nothing_drawn = run_case('first_view_null', args={'allViews': None}, responses={'render': None})
check.true('  (when the first view cannot be drawn, the run still stops there and says so)', labels(nothing_drawn)[-1] == 'render' and 'could not be drawn' in nothing_drawn['result']['stopped'])

film = run_case('film', args={'film': True})
check.true('a place for the film (film: true): every view is drawn at 1080 x 1920 (the planner\'s 1200 x 800 is changed, and the log says so), the previews in the same tall shape (540 x 960)',
           'wide: camera "View wide", 1080 x 1920' in prompt_of(film, 'render') and '1200 x 800' not in prompt_of(film, 'render') and '540 x 960' in prompt_of(film, 'render')
           and any('drawn at 1080 x 1920' in one_line for one_line in film['logs']))
check.true('  (the planner is told to read build-and-paint-a-place and the tips guide, run plan_shot.py for each view and write "for_film": true; without film it is told the wide default)',
           all(word in prompt_of(film, 'plan') for word in ('THE FILM FRAME', 'calculators/plan_shot.py --place-facts', '"for_film": true', 'build-and-paint-a-place/SKILL.md', 'sections 4 to 12', 'place: film frame', '0.90 across'))
           and 'plan_shot.py' not in prompt_of(happy, 'plan') and 'not marked for the film' in prompt_of(happy, 'plan') and 'wide: camera "View wide", 1200 x 800' in prompt_of(happy, 'render'))
film_given = run_case('film_person_views', args={'film': True, 'views': [{'name': 'street', 'size': [600, 400]}]})
check.true('  (a size the person gave is kept even for the film, and the log says the film-frame check will speak)',
           'street: camera "View street", 600 x 400' in prompt_of(film_given, 'render') and any('kept as the person gave it' in one_line for one_line in film_given['logs']))
check.true('every named view must see a finished horizon: the planner and the ground part are told the world round the place is the ground part\'s, with the role backdrop and the check "place: world"',
           all('finished horizon' in prompt_of(happy, label) and 'place: world' in prompt_of(happy, label) and 'backdrop' in prompt_of(happy, label) for label in ('plan', 'ground:ground_and_water'))
           and 'clip end at 1000 m' in prompt_of(happy, 'ground:ground_and_water'))
thread_labels = ('ground:ground_and_water', 'build:lock_gate', 'combine', 'audit', 'fix:lock_gate')
check.true('every builder and integrator prompt gives the thread limit (EXPLAINER_FILM_BLENDER_THREADS=2 for the plugin\'s commands, blender -t 2 for their own runs; default 2)',
           all('EXPLAINER_FILM_BLENDER_THREADS=2 explainer-film-place' in prompt_of(happy, label) and 'blender -t 2 -b --disable-autoexec' in prompt_of(happy, label) for label in thread_labels))
threads = run_case('threads', args={'blenderThreads': 3})
check.true('  (blenderThreads: 3 reaches them as 3)', 'EXPLAINER_FILM_BLENDER_THREADS=3' in prompt_of(threads, 'build:lock_gate') and 'blender -t 3' in prompt_of(threads, 'combine')
           and 'EXPLAINER_FILM_BLENDER_THREADS=2' not in prompt_of(threads, 'build:lock_gate'))
check.true('every prompt except the blind reader\'s says never to send a message to a helper that is spending money (it once woke a second copy: 8 extra paid calls)',
           all('Never send a message to a helper that is spending money' in one_call['prompt'] for one_call in happy['calls'] if not one_call['label'].startswith('blind')))

# ----------------------------------------------------------------------------- the commands written in the prompts are real
def launcher(args):
    wrapper = os.path.join(PLUGIN, 'bin', 'explainer-film-place')
    if not os.path.exists(wrapper):
        return None
    try:
        run = subprocess.run(['bash', wrapper] + args, capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (run.returncode, run.stdout + run.stderr) if run.returncode == 0 else None


verbs_run = launcher(['--verbs'])
if verbs_run is None:
    check.note('skipped: the verb and option checks of the prompts (bin/explainer-film-place is not there or cannot print its verbs)')
else:
    verbs = [verb_line.strip() for verb_line in verbs_run[1].splitlines() if verb_line.strip()]
    helps, problems, seen_verbs = {}, [], set()
    for case, label, prompt in ALL_PROMPTS:
        for match in re.finditer(r'explainer-film-place\s+([A-Za-z][A-Za-z-]*)([^\n]*)', prompt):
            verb, rest = match.group(1), match.group(2)
            rest = rest.split('explainer-film-')[0]
            if verb not in verbs:
                problems.append(f'{case}/{label}: "{verb}" is not a verb')
                continue
            seen_verbs.add(verb)
            if verb not in helps:
                got = launcher([verb, '--help'])
                helps[verb] = got[1] if got else ''
            for option in re.findall(r'(?<![\w-])(--[a-z][a-z0-9-]*)', rest):
                if option not in helps[verb]:
                    problems.append(f'{case}/{label}: {option} is not an option of {verb}')
    check.true(f'no prompt names a verb that explainer-film-place does not print, or an option its --help lacks ({len(seen_verbs)} verbs used: {", ".join(sorted(seen_verbs))})', not problems and bool(seen_verbs), details='; '.join(sorted(set(problems))[:4]) or 'all exist')
    check.true('  (a made-up verb and a made-up option would be found by this check)',
               re.search(r'explainer-film-place\s+([A-Za-z][A-Za-z-]*)', 'explainer-film-place build-everything --now').group(1) not in verbs)
    preflight = os.path.join(PLUGIN, 'bin', 'explainer-film-preflight')
    if os.path.exists(preflight):
        run = subprocess.run(['bash', preflight, '--help'], capture_output=True, text=True, timeout=90)
        help_text = run.stdout + run.stderr
        wrong = []
        for case, label, prompt in ALL_PROMPTS:
            for match in re.finditer(r'explainer-film-preflight\s+([a-z]+)([^\n]*)', prompt):
                if match.group(1) not in ('script', 'record', 'shots', 'place', 'plates', 'paint', 'pages', 'film', 'finish'):
                    continue
                for option in re.findall(r'(?<![\w-])(--[a-z][a-z0-9-]*)', match.group(2)):
                    if option not in help_text:
                        wrong.append(f'{case}/{label}: {option}')
        check.true('every option written beside explainer-film-preflight place in a prompt is in the preflight\'s --help', not wrong, details='; '.join(sorted(set(wrong))[:4]) or 'all exist')

# ------------------------------------------------------------------------------------------------------- nothing private in a prompt
author = ''
try:
    author = json.load(open(os.path.join(PLUGIN, '.claude-plugin', 'plugin.json'), encoding='utf-8')).get('author', {}).get('name', '')
except (OSError, ValueError):
    pass
private = []
for case, label, prompt in ALL_PROMPTS:
    if re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', prompt):
        private.append(f'{case}/{label}: an email-like string')
    if re.search(r'\b[0-9a-f]{24,}\b', prompt):
        private.append(f'{case}/{label}: a long hex id')
    if re.search(r'\brp' + r'a_[A-Za-z0-9]{16,}\b', prompt) or re.search(r'\bsk-[A-Za-z0-9]{20,}\b', prompt):
        private.append(f'{case}/{label}: a key-looking value')
    if ('.run' + 'pod') in prompt:
        private.append(f'{case}/{label}: the rented-card settings folder')
    if len(author) >= 4 and re.search(r'\b' + re.escape(author) + r'\b', prompt, re.I):
        private.append(f'{case}/{label}: the plugin author\'s name')
check.true(f'no prompt of any case holds a key, a long hex id, a settings folder, an email-like string or the author\'s name ({len(ALL_PROMPTS)} prompts)', not private, details='; '.join(private[:3]) or 'none')
check.true('  (made-up private text would be found by these patterns)', len([1 for found in (re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', 'x someone' + '@' + 'example.org'),
                                                                                       re.search(r'\b[0-9a-f]{24,}\b', 'a1b2c3d4' * 4), re.search(r'\brp' + r'a_[A-Za-z0-9]{16,}\b', 'rp' + 'a_' + 'x' * 20)) if found]) == 3)
check.true('the script file itself has no email-like string, long hex id, key-looking value or settings folder name',
           not re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', source) and not re.search(r'\b[0-9a-f]{24,}\b', source) and ('.run' + 'pod') not in source and not re.search(r'\brp' + r'a_[A-Za-z0-9]{16,}', source))
check.true('the script and the agent files name no folder of this machine or of the person (no home folder, no scratch folder, no add-on name)',
           not any(word in text for text in [source] + [read(os.path.join(PLUGIN, 'agents', f'place-{role}.md')) for role in ('planner', 'builder', 'integrator', 'renderer', 'checker')]
                   for word in ('/ho' + 'me/', 'claude' + '-0', 'As' + 'tra', 'CT' + ' /')))

# ------------------------------------------------------------------------------------------------------------- the agent files
AGENT_FILES = {role: os.path.join(PLUGIN, 'agents', f'place-{role}.md') for role in ('planner', 'builder', 'integrator', 'renderer', 'checker')}
named = sorted(set(re.findall(r'place-[a-z]+\.md', source)))
check.equal('the script names exactly the five place agent files', named, sorted(f'place-{role}.md' for role in AGENT_FILES))
check.true('every agent file the script names exists', all(os.path.exists(path) for path in AGENT_FILES.values()), details=', '.join(path for path in AGENT_FILES.values() if not os.path.exists(path)) or 'all five')


def front_matter(text):
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        return {}
    out = {}
    for line in lines[1:]:
        if line.strip() == '---':
            break
        key, sep, value = line.partition(':')
        if sep:
            out[key.strip()] = value.strip()
    return out


bad_front = []
for role, path in AGENT_FILES.items():
    if not os.path.exists(path):
        continue
    meta = front_matter(read(path))
    if meta.get('name') != f'place-{role}':
        bad_front.append(f'{role}: name {meta.get("name")!r}')
    if len(meta.get('description', '')) < 80:
        bad_front.append(f'{role}: no real description')
    if meta.get('effort') != 'medium':
        bad_front.append(f'{role}: effort {meta.get("effort")!r}')
    if ': ' in meta.get('description', ''):
        bad_front.append(f'{role}: a colon and a space in the description (strict YAML)')
check.true('each agent file has front matter with its name, a real description and effort medium (and no colon-space in the description)', not bad_front, details='; '.join(bad_front) or 'all five')
check.true('the agents that must know the finishing pass name the skill', all('surfaces-wear-and-construction' in read(AGENT_FILES[role]) for role in ('planner', 'builder', 'integrator', 'renderer', 'checker') if os.path.exists(AGENT_FILES[role])))

# every field a helper must return is named in its own agent file (the schema is enforced, but a model that has not been told the names loses a round)
schema_of = {}
for call in happy['calls']:
    schema_of.setdefault(call['label'].split(':')[0].rstrip('0123456789'), call['schema'])
wanted = {'planner': [schema_of['plan']], 'builder': [schema_of['build'], schema_of['ground']], 'integrator': [schema_of['combine'], schema_of['audit'], schema_of['gate']],
          'renderer': [schema_of['render']], 'checker': [schema_of['check'], schema_of['blind'], schema_of['skeptic']]}
missing_fields = []
for role, schemas in wanted.items():
    text = read(AGENT_FILES[role]) if os.path.exists(AGENT_FILES[role]) else ''
    for schema in schemas:
        for name in schema['required'] if schema else []:
            if not re.search(r'\b' + re.escape(name) + r'\b', text) and name.replace('_', ' ') not in text:
                missing_fields.append(f'{role}: {name}')
check.true('every field the script asks for is named in the agent file of the helper that returns it', not missing_fields, details=', '.join(missing_fields[:8]) or 'all named')
shape = re.search(r'```\n(\{ "mode".*?)```', read(AGENT_FILES['checker']), re.S)
shape_keys = re.findall(r'"([a-z_]+)":', shape.group(1)) if shape else []
check.true('the result shape written in place-checker.md names exactly the fields of the CHECK schema (plus the ones inside its lists)',
           bool(shape_keys) and set(schema_of['check']['required']) <= set(shape_keys) and all(name in set(schema_of['check']['properties']) | {'element', 'verdict', 'why', 'claim', 'holds', 'evidence', 'what', 'where', 'severity', 'cheapest_fix', 'owner'} for name in shape_keys),
           details=f'{len(shape_keys)} names found')
check.true('the fresh-check judge reads the same field names the CHECK schema has', all(field in schema_of['check']['properties'] for field in ('mode', 'was_blind', 'art_style_kept', 'lived_in', 'construction_makes_sense', 'claims_checked', 'problems', 'not_tested')))

# ----------------------------------------------------------------------------------- a check that can never fail proves nothing
def mutant(name, old, new):
    """A copy of the script with one deliberate fault (the fault must be there to change)."""
    if old not in source:
        check.true(f'mutation {name}: the place to change is still in the script', False, details=old[:60])
        return None
    path = os.path.join(WORK, f'mutant_{name}.js')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(source.replace(old, new, 1))
    return path


changed_script = mutant('checkers_see_numbers', 'The finished scene file: ${STATE.finalFile}\nThe pictures', 'The finished scene file: ${STATE.finalFile} ${JSON.stringify(STATE.built.map((entry) => entry.report))}\nThe pictures')
if changed_script:
    check.true('mutation: a script that hands the builders\' reports to the checkers is caught by the planted-number check', bool(checkers_that_see_builder_numbers(run_case('m1', workflow=changed_script))))
changed_script = mutant('draws_anyway', 'if (!gateOk(STATE.combine, STATE.audit)) {\n  return done(', 'if (false) {\n  return done(')
if changed_script:
    check.true('mutation: a script that draws pictures after a failing audit is caught', drew_pictures(run_case('m2', workflow=changed_script, responses={'~^audit\\d*$': 'audit-fail.json', '~^repair\\d+:': 'part-report-fixed.json', '~^recombine\\d+$': 'combine-report-fixed.json'})))
changed_script = mutant('no_cap', 'Array.from({ length: Math.min(cap, items.length) }, slot)', 'Array.from({ length: items.length }, slot)')
if changed_script:
    check.true('mutation: a script that ignores the cap on builders is caught', builders_at_once(run_case('m3', workflow=changed_script, args={'maxParallelBuilders': 3}, responses={'plan': 'plan-many.json'})) > 3)
changed_script = mutant('blind_knows', 'You are a reader of pictures. Round ${round}.', 'You are a reader of pictures. Round ${round}. The request was: "${ARGS.request}".')
if changed_script:
    check.true('mutation: a script that tells the blind reader the request is caught', blind_prompt_knows_the_request(run_case('m4', workflow=changed_script)))
changed_script = mutant('drops_missing', 'STATE.missing = STATE.built.filter((entry) => !entry.report).map((entry) => entry.part.owner)', 'STATE.missing = []')
if changed_script:
    check.true('mutation: a script that drops a part that returned nothing without a word is caught', 'MISSING parts' not in run_case('m5', workflow=changed_script, responses={'build:lock_gate': None})['result']['report_markdown'])
changed_script = mutant('no_first_read', "const first = (role) => `First read ${ARGS.plugin}/agents/${AGENT[role]} and follow it. (In that file and in the skill files it names, \\${CLAUDE_PLUGIN_ROOT} means the plugin folder: ${ARGS.plugin}.)`", "const first = (role) => ''")
if changed_script:
    mutated = run_case('m6', workflow=changed_script)
    check.true('mutation: a script whose prompts do not start with "First read <agent file>" is caught', not mutated['calls'][0]['prompt'].startswith('First read'))
changed_script = mutant('extra_phase', "phase('Re-check')", "phase('Fix')\nS.version += 0\nphase('Re-check')")
if changed_script:
    check.true('mutation: a script whose phases are out of step with its meta block is caught', run_case('m7', workflow=changed_script)['phases'] != PHASES)

changed_script = mutant('no_first_view_stop', 'if (FIRST_VIEW_ONLY) {\n  STATE.firstViewStop', 'if (false) {\n  STATE.firstViewStop')
if changed_script:
    check.true('mutation: a script that does not stop after the first view by default is caught', labels(run_case('m8', workflow=changed_script, args={'allViews': None}))[-1] != 'render')

check.finish()
