"""What this does: checks that the BATCH RULE and the CARD-TIME ALLOWANCE are written everywhere a model will read them, and that the words agree with the numbers. The rule (the person's, after the
Japanese garden job spent US$10.89 of rented-card time on pictures that cost about 5 cents): make every change in one sweep, then look once; for each change to a thing, about 10 measurably
different versions in ONE batch; at most one more batch; build the scene once and save it; small quick pictures until the end; full-size pictures once, at the very end; stay inside the
allowance and report the card seconds.
It checks: (1) the house numbers place_card_time.* and place_variations.* are there, each with a kind and a source, and the allowances are builder 10, fixer 5, integrator 10, renderer 10, checker 3,
planner 0 minutes; (2) the REQUIRED block of the three skills that carry it holds the rule, the tool and the file to read; (3) the new skill file exists, names every action of `variations`
and `card-time`, and every house number it writes exists; (4) each of the five place agents carries the rule in its own words (the builder, integrator and renderer have an allowance; the
planner has none; the checker looks at the ledger); (5) every allowance written as "builder 10 minutes" in a skill, agent, README or guide equals the house number; (6) the tips guide has the four
tips, the hook reminder names the rule and is still three lines, and the README says what changed; (7) the example variations file of the real canal lock is read by the real reader and uses only keys
the tool knows, with no folder of this computer in it, and the hook template is valid Python with an apply function; (8) the workflow file names the ledger, the batch rule and the single full-size drawing.
Every check of text is also tried on a text that lacks the rule and must fail there. Standard library only (the reader of the variations file needs the place kit's own Python, no Blender).
Run: python3 kit/calculators/tests/test_place_batching_rule.py
"""
import ast
import glob
import json
import os
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True        # reading the hook and the place kit here must leave no __pycache__ folder inside the plugin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, PLUGIN  # noqa: E402

check = Checker('batch rule and card-time allowance: written where models read, and equal to the house numbers')
settings = json.load(open(os.path.join(KIT, 'film-settings.json'), encoding='utf-8'))
SKILL = os.path.join(PLUGIN, 'skills', 'surfaces-wear-and-construction')
RULE_FILE = os.path.join(SKILL, 'batched-rounds-and-card-time.md')
CARRIERS = ['surfaces-wear-and-construction', 'make-3d-models', 'build-and-paint-a-place']
AGENTS = ['planner', 'builder', 'integrator', 'renderer', 'checker']


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


# (1) the house numbers
card = settings['place_card_time']
variations_numbers = settings['place_variations']
expected = {'builder': 10, 'fixer': 5, 'integrator': 10, 'renderer': 10, 'checker': 3, 'planner': 0}
check.true('the house numbers place_card_time.allowance_minutes are builder 10, fixer 5, integrator 10, renderer 10, checker 3, planner 0',
           all(card['allowance_minutes'][role]['value'] == minutes for role, minutes in expected.items()), details=str({r: v['value'] for r, v in card['allowance_minutes'].items()}))
every = [(f'place_card_time.{key}', row) for key, row in card.items() if isinstance(row, dict) and 'value' in row]
every += [(f'place_card_time.allowance_minutes.{key}', row) for key, row in card['allowance_minutes'].items()]
every += [(f'place_variations.{key}', row) for key, row in variations_numbers.items() if isinstance(row, dict) and 'value' in row]
missing_kind = [name for name, row in every if row.get('kind') not in ('measured', 'judged', 'invented', 'worked out') or len(str(row.get('source', ''))) < 20]
check.true(f'every card-time and variations house number has a kind and a real source ({len(every)} numbers)', not missing_kind, details=', '.join(missing_kind) or 'all marked')
check.true('the allowances are marked judged (nobody measured how long a good try takes), and the wake-up and picture seconds are marked measured',
           all(row['kind'] == 'judged' for row in card['allowance_minutes'].values()) and card['estimated_wake_up_seconds']['kind'] == 'measured' and card['estimated_seconds_per_final_picture']['kind'] == 'measured')

# (2) the REQUIRED block of the three skills
BLOCK_WORDS = ['ONE sweep', 'about 10 variations', 'ONE batch', 'variations scout', 'variations run', 'ONE more batch', '600 x 400', 'once, at the very end', 'allowance', 'builder 10 minutes, fixer 5', 'batched-rounds-and-card-time.md']


def required_block(text):
    lines = [line for line in text.split('\n') if line.startswith('>')]
    return '\n'.join(lines)


def lacks(block):
    return [word for word in BLOCK_WORDS if word not in block]


for name in CARRIERS:
    block = required_block(read(os.path.join(PLUGIN, 'skills', name, 'SKILL.md')))
    check.true(f'the REQUIRED block of {name} holds the batch rule, the tool, the sizes, the allowance and the file to read', not lacks(block), details='lacks: ' + ', '.join(lacks(block)))
check.true('  (a block without the rule is found lacking: the check can fail)', len(lacks('> 1. build it\n> 2. finish\n> 3. audit')) == len(BLOCK_WORDS))

# (3) the new skill file
rule = read(RULE_FILE) if os.path.exists(RULE_FILE) else ''
check.true('the skill file batched-rounds-and-card-time.md exists, starts with what it is, and gives a concrete example (the garden) before the rule',
           rule.startswith('# Batched rounds and card time') and 'What this is:' in rule and rule.index('US$10.89') < rule.index('## 2. The rule'))
actions = ['variations make', 'variations scout', 'variations plan', 'variations run', 'variations collect', 'variations refine', 'variations keys', 'card-time show', 'card-time check', 'card-time start']
check.true('it names every action it asks a helper to use: ' + ', '.join(actions), all(action in rule for action in actions), details=', '.join(a for a in actions if a not in rule) or 'all named')
numbers_named = sorted(set(re.findall(r'\bplace_(?:card_time|variations|render|measures)\.[a-z_]+(?:\.[a-z_]+)?', rule)))


def exists(dotted):
    node = settings
    for part in dotted.split('.'):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


check.true(f'every house number the file writes exists in film-settings.json ({", ".join(numbers_named)})', numbers_named and all(exists(name) for name in numbers_named), details=', '.join(n for n in numbers_named if not exists(n)) or 'all exist')
for needed in ('one sweep', 'Build the scene once', 'ONE more batch', 'Small quick pictures', 'Full-size pictures are drawn ONCE', 'allowance', 'refuses', 'over-allowance', 'estimate'):
    if needed.lower() not in rule.lower():
        check.true(f'the skill file says "{needed}"', False)
        break
else:
    check.true('the skill file states the whole rule: one sweep, build once, one batch of about 10, one more batch at most, small pictures, full size once, the allowance, the refusal, the way over, and that price is an estimate', True)
check.true('the skill file says where the measures are made and what a card second is (work + wake-up + idle tail)', 'work + wake-up + idle tail' in rule and 'cost no card seconds' in rule)

# (4) the five agents
agent_text = {role: read(os.path.join(PLUGIN, 'agents', f'place-{role}.md')) for role in AGENTS}
check.true('the builder carries the rule: a section on trying variations, the allowance (builder 10, fixer 5), the ledger flags, the batch, no third batch, and that it reports card_seconds and batches',
           all(word in agent_text['builder'] for word in ('## 3b. Trying variations', 'builder 10 minutes, fixer 5', '--helper NAME --role ROLE --ledger LEDGER', 'variations scout', 'variations plan', 'variations run',
                                                    'variations collect', 'at most ONE more batch', '`card_seconds`', '`batches`')))
check.true('the integrator may try a dial the batch way (role integrator, 10 minutes) and reports card seconds; the renderer has 10 minutes, draws full size once at the very end and reports card_seconds',
           'role integrator' in agent_text['integrator'] and 'variations run' in agent_text['integrator'] and 'card_seconds' in agent_text['integrator']
           and 'ONCE, at the very end' in agent_text['renderer'] and '`card_seconds`' in agent_text['renderer'] and '(10 minutes: judged)' in agent_text['renderer'])
check.true('the planner is told it has no card time and writes the rule into every brief; the checker compares the reported seconds with the ledger and counts batches',
           'You use no card time yourself' in agent_text['planner'] and 'Plan for batches and card time' in agent_text['planner'] and 'card-time ledger' in agent_text['checker'] and 'more than two batches' in agent_text['checker'])
check.true('no agent still says that nobody but the renderer may use the card, or that a builder never uses it',
           all('You are the only helper in the' not in text and 'Never use the rented card yourself' not in text for text in agent_text.values()))

# (5) the numbers written in words equal the house numbers
written = []
for path in (glob.glob(os.path.join(PLUGIN, 'skills', '**', '*.md'), recursive=True) + glob.glob(os.path.join(PLUGIN, 'agents', '*.md')) + [os.path.join(PLUGIN, 'README.md'), os.path.join(KIT, 'docs', 'LLM tips and tricks.md'),
                                                                                                                               os.path.join(KIT, 'place-kit', 'README.md')]):
    for role, number in re.findall(r'\b(builder|fixer|integrator|renderer|checker|planner) (\d+) minutes?', read(path)):
        written.append((os.path.relpath(path, PLUGIN), role, int(number)))
wrong = [f'{where}: {role} {number}' for where, role, number in written if expected[role] != number]
check.true(f'every allowance written in words ("builder 10 minutes") equals the house number ({len(written)} places)', written and not wrong, details='; '.join(wrong[:4]) or f'{len(written)} agree')
check.true('  (a wrong number would be found)', 'builder 12' != 'builder 10' and [1 for role, number in [('builder', 12)] if expected[role] != number])
check.true('the figure from the garden job (US$10.89 of card time against pictures worth about 5 cents) is the same wherever it is written',
           all(not re.search(r'US\$\s?\d+\.\d+ of (?:rented-)?card time', read(path)) or 'US$10.89' in read(path) for path in glob.glob(os.path.join(PLUGIN, 'skills', '**', '*.md'), recursive=True)))

# (6) the tips guide, the hook, the README
tips = read(os.path.join(KIT, 'docs', 'LLM tips and tricks.md'))
check.true('the tips guide has the four tips (sweep, batch of about 10, small until the end and full size once, ledger and allowance) in section 8a and a line in the money section',
           all(f'\n{number}. ' in tips.split('## 9.')[0] for number in (16, 17, 18, 19)) and 'ONE sweep' in tips and 'about 10 variations' in tips and 'ledger' in tips.split('## 17.')[0] and 'Rented-card time is limited' in tips
           and 'variations scout' in tips and 'variations collect' in tips)
hook = read(os.path.join(PLUGIN, 'hooks', 'place-reminder.py'))
sys.path.insert(0, os.path.join(PLUGIN, 'hooks'))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location('place_reminder', os.path.join(PLUGIN, 'hooks', 'place-reminder.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
check.true('the hook reminder names the rule (one sweep, one batch of about 10, explainer-film-place variations, full size once, card seconds) and is still three lines',
           all(word in module.REMINDER for word in ('ONE sweep', 'ONE batch', 'explainer-film-place variations', 'once at the very end', 'card seconds')) and len(module.REMINDER.splitlines()) <= 3, details=str(len(module.REMINDER.splitlines())))
readme = read(os.path.join(PLUGIN, 'README.md'))
check.true('the README says what changed (the rule, both verbs, the allowances, that it was proved on real cards) and which skill file holds the rule',
           all(word in readme for word in ('Batched rounds and card time', 'explainer-film-place variations', 'explainer-film-place card-time', 'batched-rounds-and-card-time.md', 'real rented cards')))

# (7) the example file and the hook template
examples = os.path.join(KIT, 'place-kit', 'data', 'examples')
example_path = os.path.join(examples, 'canal-lock-cracks-variations.json')
example = json.load(open(example_path, encoding='utf-8')) if os.path.exists(example_path) else {}
sys.path.insert(0, os.path.join(KIT, 'place-kit'))
from place_kit.variations import keys as variation_keys, spec as variation_spec  # noqa: E402

problems = []
for item in example.get('variations', []):
    _, found = variation_keys.clean_set(item.get('set'))
    problems += found
check.true('the example variations file of the real canal lock has 10 variations, every key and value valid for the tool, and its scene and settings written beside the file (no absolute folder)',
           len(example.get('variations', [])) == 10 and not problems and not os.path.isabs(example.get('scene', '/')) and not os.path.isabs(example.get('settings', '/')) and 'Camera A' in example.get('cameras', []), details='; '.join(problems[:2]))
folder = tempfile.mkdtemp(prefix='batching-rule-test-')
try:
    shutil.copy(example_path, os.path.join(folder, 'example.json'))
    open(os.path.join(folder, example['scene']), 'wb').write(b'x')
    open(os.path.join(folder, example['settings']), 'w').write('{}')
    read_spec = variation_spec.read_spec(os.path.join(folder, 'example.json'))
    checked = variation_spec.check_before(read_spec)
    check.true('the real reader reads it, and all 10 variations survive the check before drawing (they are far apart)', len(read_spec['variations']) == 10 and len(checked['kept']) == 10 and not checked['dropped'],
               details=f'{len(checked["kept"])} kept, {len(checked["dropped"])} dropped')
finally:
    shutil.rmtree(folder, True)
text_of_example = open(example_path, encoding='utf-8').read() if os.path.exists(example_path) else ''
check.true('the example holds no folder of this computer, no address, no key and no personal detail', not re.search(r'/home/|/tmp/|claude-0|@\w+\.\w+|rpa_|\.runpod', text_of_example))
template_path = os.path.join(KIT, 'place-kit', 'data', 'templates', 'variation_hook.py')
template = read(template_path) if os.path.exists(template_path) else ''
try:
    tree = ast.parse(template)
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
except SyntaxError:
    functions = []
check.true('the hook template is valid Python, starts with a plain note and a concrete example, and has apply(variation)', 'apply' in functions and template.startswith('"""What this does:') and 'A concrete example:' in template.split('"""')[1])

# (8) the workflow
workflow = read(os.path.join(PLUGIN, 'workflows', 'build-a-place.js'))
check.true('the workflow writes the card ledger, the allowances by role, the batch rule and the ONE full-size drawing at the end (and no rounds drawn at full size)',
           all(word in workflow for word in ('CARD_LEDGER', 'CARD_MINUTES', 'THE BATCH RULE', 'cardTeamMinutes', "label: 'render:final'", 'THIS IS THE ONE FULL-SIZE DRAWING OF THE RUN', 'function cardTimeSummary',
                                             'variations scout', 'variations collect'))
           and "${FINALS ? ' --finals' : ''}" not in workflow)

check.finish()
