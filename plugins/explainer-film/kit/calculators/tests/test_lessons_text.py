"""What this does: checks that the lessons round of plugin 1.4.0 (23 October 2026) stays in the words a model reads, so a later edit
cannot quietly bring back an old mistake. A concrete example: the painting prompts once said "the lower quarter of the picture is the
empty floor" with no word of where that applies, and a review traced the empty bottom third of a whole chapter to that sentence; this
test fails if such a line comes back without "paper route only" beside it.
It checks, and every check is also tried on a deliberately wrong text, where it must fail:
1. The three old contradictions are gone: (a) every instruction about the empty lower quarter (paint-and-cut and docs 01, 02, 04;
   the prompt table rows of doc 04 are left as they were) says it is for the paper route only and that a built place reaches about
   0.70 down; (b) the painter's blank placards are explained (only so it invents no writing) and both place skills that build props
   say every sign and book carries real lettering, with the audit's check "place: lettering"; (c) workflows/critique-film.js no longer
   gives the old phone-button numbers (bottom 380 px, right 140 px) but 0.90 across and 0.80 down.
2. workflows/critique-film.js has a critic keyed history and tells its critics to read section 19 of the tips guide; when node is
   installed the workflow is also run with stand-in helpers, and the result's critics include the area "history", whose prompt asks
   "was this in that place and that year?".
3. workflows/verify-facts.js takes args.pictures and args.propLettering, and (with node) both reach the helper that splits the claims.
4. The prompt-time hook names build-and-paint-a-place and the 1080 x 1920 film frame, and prints nothing for "plain Blender" (while the
   same request without those words still gets the reminder).
5. The house rules carry the privacy line (no name or email in a request to an outside website), the paid-helper line (never message
   a helper that is spending money), the dollar-sign line (bin/bash, a quoted here-document) and the start-small line; doc 06 keeps step.
6. The REQUIRED block is still word for word the same in the three skills that carry it, and holds the two new lines (the film frame
   and "for_film", the person's words winning).
Standard library only; node is optional (the parts that run a workflow are skipped, said plainly, without it).
Run: python3 kit/calculators/tests/test_lessons_text.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, PLUGIN  # noqa: E402

check = Checker('lessons round: the old contradictions stay gone and the new lessons stay where models read them')
NODE = shutil.which('node')
DOCS = os.path.join(KIT, 'docs')
SKILLS = os.path.join(PLUGIN, 'skills')
WORKFLOWS = os.path.join(PLUGIN, 'workflows')
HOOK = os.path.join(PLUGIN, 'hooks', 'place-reminder.py')


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


# ---------------------------------------------------------------------------------------- 1. the three contradictions
def lower_quarter_problems(text, where):
    """Every instruction about an empty lower quarter must say, close by, that it is for the paper route only and that a built place
    reaches about 0.70 down. Rows of a prompt table (lines that start with |) are the paper route's own record and are left alone."""
    problems = []
    for match in re.finditer(r'lower quarter', text, flags=re.I):
        line_start = text.rfind('\n', 0, match.start()) + 1
        if text[line_start:].lstrip().startswith('|'):
            continue
        window = text[max(0, match.start() - 400): match.end() + 1200]
        if 'paper route only' not in window or '0.70 down' not in window:
            problems.append(f'{where}: "lower quarter" at character {match.start()} has no "paper route only" and "0.70 down" beside it')
    return problems


LOWER_QUARTER_FILES = [os.path.join(SKILLS, 'paint-and-cut', 'SKILL.md'), os.path.join(DOCS, 'paper-look - 04 Painting prompts.md'),
                       os.path.join(DOCS, 'paper-look - 02 The look - style rules.md'), os.path.join(DOCS, 'paper-look - 01 How to make a film with this kit.md')]
problems, counted = [], 0
for path in LOWER_QUARTER_FILES:
    text = read(path)
    counted += len(re.findall(r'lower quarter', text, flags=re.I))
    problems += lower_quarter_problems(text, os.path.relpath(path, PLUGIN))
check.true(f'(1a) every instruction about the empty lower quarter says "paper route only" and that a built place reaches about 0.70 down ({counted} mentions in 4 files)',
           not problems and counted >= 4, details='; '.join(problems[:3]) or 'all qualified')
check.true('  (the old sentence alone fails this check)', bool(lower_quarter_problems('- Rooms: seen at standing eye level, "the lower quarter of the picture is the empty floor".', 'made-up')))


def placard_problems(paint_and_cut, make_models, build_place):
    problems = []
    if 'Ask for blank placards and plain signs (models invent writing).' in paint_and_cut:
        problems.append('paint-and-cut still has the old unexplained line')
    if not re.search(r'blank placards and plain signs only so that it\s+does not invent writing', paint_and_cut) or 'real lettering' not in paint_and_cut:
        problems.append('paint-and-cut does not say why the painter gets blank placards, or that built signs carry real lettering')
    for name, text in (('make-3d-models', make_models), ('build-and-paint-a-place', build_place)):
        if 'real lettering' not in text or 'place: lettering' not in text:
            problems.append(f'{name} lacks the lettering rule or the audit check "place: lettering"')
    return problems


paint_text = read(os.path.join(SKILLS, 'paint-and-cut', 'SKILL.md'))
models_text = read(os.path.join(SKILLS, 'make-3d-models', 'SKILL.md'))
place_text = read(os.path.join(SKILLS, 'build-and-paint-a-place', 'SKILL.md'))
problems = placard_problems(paint_text, models_text, place_text)
check.true('(1b) blank placards are for the painter only (so it invents no writing); make-3d-models and build-and-paint-a-place both say every sign carries real lettering and name "place: lettering"',
           not problems, details='; '.join(problems) or 'all three agree')
check.true('  (the old paint-and-cut line and a props skill without the rule fail this check)',
           len(placard_problems('- Ask for blank placards and plain signs (models invent writing).', 'build a box', place_text)) >= 2)

critique = read(os.path.join(WORKFLOWS, 'critique-film.js'))


def phone_button_problems(text):
    problems = []
    if re.search(r'\b(380|140) px\b', text):
        problems.append('the old phone-button numbers (bottom 380 px, right 140 px) are still there')
    if '0.90 across' not in text or '0.80 down' not in text:
        problems.append('the rule "left of 0.90 across and above 0.80 down" is not there')
    return problems


problems = phone_button_problems(critique)
check.true('(1c) critique-film.js gives the phone-button rule as 0.90 across and 0.80 down, and no "140 px" or "380 px"', not problems, details='; '.join(problems) or 'yes')
check.true('  (the old prompt fails this check)', bool(phone_button_problems('out of the phone-button zones (bottom 380 px, right 140 px)?')))


# ------------------------------------------------------------------------------------------ 2 and 3. the two workflows
def history_problems(text):
    problems = []
    if not re.search(r"key:\s*'history'", text):
        problems.append("no critic keyed 'history'")
    if 'section 19' not in text or 'LLM tips and tricks.md' not in text:
        problems.append('section 19 of the tips guide is not named')
    if 'was this in that place and that year?' not in text:
        problems.append('the history question is not asked')
    return problems


problems = history_problems(critique)
check.true('(2) critique-film.js has a critic keyed history that asks "was this in that place and that year?", and names section 19 of the tips guide', not problems, details='; '.join(problems) or 'yes')
check.true('  (a copy without the history critic fails this check)', bool(history_problems(critique.replace("key: 'history'", "key: 'story'"))))

verify = read(os.path.join(WORKFLOWS, 'verify-facts.js'))


def verify_problems(text):
    return [name for name in ('A.pictures', 'A.propLettering', 'weekday') if name not in text]


check.true('(3) verify-facts.js takes args.pictures and args.propLettering and asks for dates with their weekdays', not verify_problems(verify), details=', '.join(verify_problems(verify)) or 'yes')
check.true('  (a copy without them fails this check)', len(verify_problems(verify.replace('A.pictures', 'A.pics').replace('A.propLettering', 'A.props'))) == 2)

# the workflows run with stand-in helpers (node only): the result's areas and the prompts the helpers would get
RUNNER = r"""
const fs = require('fs')
const [file, argsJson] = process.argv.slice(2)
const source = fs.readFileSync(file, 'utf8').replace('export const meta', 'const meta')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const run = new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', source)
const prompts = []
const agent = async (prompt, options) => {
  prompts.push({ label: options.label, prompt })
  if (options.label === 'split claims') return { groups: [{ key: 'a', title: 'A', claims: ['x'] }] }
  return { findings: [], overall: 'ok', confirmed: [], rejected: [], summary: '', group: 'A', claims: [], other_notes: '', must_fix: [], should_fix: [], gaps: [] }
}
const parallel = (thunks) => Promise.all(thunks.map((thunk) => thunk()))
const pipeline = (items, stage) => Promise.all(items.map(stage))
run(JSON.parse(argsJson), agent, parallel, pipeline, () => {}, () => {})
  .then((result) => process.stdout.write(JSON.stringify({ result, prompts })))
  .catch((problem) => process.stdout.write(JSON.stringify({ error: String(problem && problem.message || problem), prompts })))
"""


def run_workflow(path, args):
    folder = tempfile.mkdtemp(prefix='lessons-text-test-')
    try:
        runner = os.path.join(folder, 'runner.js')
        with open(runner, 'w', encoding='utf-8') as handle:
            handle.write(RUNNER)
        done = subprocess.run([NODE, runner, path, json.dumps(args)], capture_output=True, text=True, timeout=60)
        try:
            return json.loads(done.stdout)
        except ValueError:
            return {'error': (done.stderr or done.stdout)[-300:], 'prompts': []}
    finally:
        shutil.rmtree(folder, ignore_errors=True)


if NODE:
    critique_args = {'kit': '/path/to/kit', 'chapter': 'chapter', 'script': '/path/to/script.md', 'wordTimes': '/path/to/times.json', 'guide': '/path/to/guide.md',
                     'pictureGroups': [{'label': 'pages 1-3', 'stills': '/path/to/sheet-1.jpg'}, {'label': 'pages 4-6', 'stills': '/path/to/sheet-2.jpg'}],
                     'propLettering': '/path/to/prop-lettering.json'}
    ran = run_workflow(os.path.join(WORKFLOWS, 'critique-film.js'), critique_args)
    areas = [critic.get('area') for critic in ((ran.get('result') or {}).get('critics') or [])]
    by_label = {item['label']: item['prompt'] for item in ran.get('prompts', [])}
    history_prompt = by_label.get('critique:history', '')
    picture_prompts = [prompt for label, prompt in by_label.items() if label.startswith('critique:pictures')]
    check.true('(2, run) critique-film returns { critics, verdict }, one critic\'s area is "history", and every picture critic and the history critic are told to read section 19',
               ran.get('error') is None and 'verdict' in (ran.get('result') or {}) and 'history' in areas and len(picture_prompts) == 2
               and all('section 19 of /path/to/kit/docs/LLM tips and tricks.md' in prompt for prompt in picture_prompts + [history_prompt]),
               details=str(ran.get('error') or areas))
    check.true('  (the history critic looks at every still and the words on props, and asks the period question)',
               all(word in history_prompt for word in ('/path/to/sheet-1.jpg', '/path/to/sheet-2.jpg', '/path/to/prop-lettering.json', 'was this in that place and that year?')))
    ran = run_workflow(os.path.join(WORKFLOWS, 'verify-facts.js'), {'script': '/path/to/script.md', 'today': '1 May 2026',
                                                                    'pictures': '/path/to/paintings/*.png', 'propLettering': '/path/to/prop-lettering.json'})
    split = next((item['prompt'] for item in ran.get('prompts', []) if item['label'] == 'split claims'), '')
    check.true('(3, run) verify-facts hands the pictures and the prop lettering to the helper that splits the claims, and to the checkers',
               ran.get('error') is None and '/path/to/paintings/*.png' in split and '/path/to/prop-lettering.json' in split
               and all('/path/to/prop-lettering.json' in item['prompt'] for item in ran.get('prompts', [])), details=str(ran.get('error') or 'yes'))
    ran = run_workflow(os.path.join(WORKFLOWS, 'verify-facts.js'), {'script': '/path/to/script.md', 'today': '1 May 2026'})
    split = next((item['prompt'] for item in ran.get('prompts', []) if item['label'] == 'split claims'), '')
    check.true('  (without them the split helper is not sent looking for pictures: the check can fail)', ran.get('error') is None and 'prop-lettering' not in split and 'Read tool' not in split)
else:
    check.note('skipped: running the two workflows with stand-in helpers (node is not installed); the text checks above still ran')


# ------------------------------------------------------------------------------------------------------- 4. the hook
def hook_says(prompt):
    done = subprocess.run([sys.executable, '-I', '-B', HOOK], input=json.dumps({'prompt': prompt}), capture_output=True, text=True, timeout=30)
    return done.stdout.strip()


def reminder_problems(text):
    lines = text.splitlines()
    second = lines[1] if len(lines) > 1 else ''
    return [word for word in ('build-and-paint-a-place', '1080 x 1920', 'before you place a camera') if word not in second] + ([] if len(lines) <= 3 else ['more than three lines'])


reminder = hook_says('Build a canal lock in Blender.')
check.true('(4) the hook\'s reminder (its second line) names build-and-paint-a-place and the 1080 x 1920 film frame, and is still three lines',
           bool(reminder) and not reminder_problems(reminder), details=', '.join(reminder_problems(reminder)) or reminder.splitlines()[1][:80] if reminder else '(nothing printed)')
check.true('  (the old second line, without the film routing, fails this check)',
           len(reminder_problems('line one\nRead the skill surfaces-wear-and-construction first, then run: explainer-film-place finish.\nline three')) == 3)
check.true('(4) the hook prints nothing for "plain Blender", while the same request without those words still gets the reminder',
           hook_says('Build a canal lock in plain Blender.') == '' and bool(reminder))


# ------------------------------------------------------------------------------------------------- 5. the house rules
HOUSE_LINES = {
    'privacy': ('outside website', 'email', 'User-Agent'),
    'paid helper': ('Never send a message to a helper that is spending money',),
    'dollar sign': ('bin/bash', "<<'EOF'"),
    'start small': ('Start small',),
}


def house_problems(text):
    return [name for name, words in HOUSE_LINES.items() if not all(word in text for word in words)]


house = read(os.path.join(SKILLS, 'make-explainer-film', 'house-rules.md'))
check.true('(5) the house rules carry the privacy, paid-helper, dollar-sign and start-small lines', not house_problems(house), details=', '.join(house_problems(house)) or 'all four')
check.true('  (a text without them fails this check, line by line)', len(house_problems('Be kind. Spend little.')) == 4)
doc06 = read(os.path.join(DOCS, 'paper-look - 06 House rules for the project.md'))
in_step = [word for word in ('Start small', 'outside website', 'bin/bash', 'spending money', 'one next step, not a menu, for routine technical steps') if word.lower() not in doc06.lower()]
check.true('(5) doc 06 keeps step with the house rules where it repeats them (start small, privacy, the dollar sign, paid helpers, a menu only for looks)', not in_step, details=', '.join(in_step) or 'yes')


# ---------------------------------------------------------------------------------------- 6. the REQUIRED blocks
def required_block(text):
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if 'REQUIRED for every place, set or prop you build in Blender' in line:
            block = []
            while index < len(lines) and lines[index].startswith('>'):
                block.append(lines[index])
                index += 1
            return '\n'.join(block)
    return ''


def block_problems(blocks):
    problems = []
    if len(set(blocks.values())) != 1:
        problems.append('the REQUIRED blocks differ: ' + ', '.join(sorted(blocks)))
    for name, block in blocks.items():
        for word in ('1080 x 1920', '"for_film": true', 'build-and-paint-a-place/SKILL.md', "The person's words win", 'plain Blender'):
            if word not in block:
                problems.append(f'{name}: the block lacks "{word}"')
    return problems


CARRIERS = ['surfaces-wear-and-construction', 'make-3d-models', 'build-and-paint-a-place']
blocks = {name: required_block(read(os.path.join(SKILLS, name, 'SKILL.md'))) for name in CARRIERS}
problems = block_problems(blocks)
check.true('(6) the REQUIRED block is word for word the same in the three skills and holds the film-frame line and the "person\'s words win" line', not problems, details='; '.join(problems[:3]) or 'yes')
changed = dict(blocks)
changed['make-3d-models'] = changed['make-3d-models'].replace("The person's words win", 'The plugin wins')
check.true('  (one changed block fails this check)', bool(block_problems(changed)))

check.finish()
