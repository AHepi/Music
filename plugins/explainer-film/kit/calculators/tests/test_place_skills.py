"""What this does: checks the words of the plugin against its code, so that a skill, an agent, a workflow or a guide can
never name something that does not exist. It checks: (1) the new skill surfaces-wear-and-construction has a front matter name
equal to its folder and a description with every routing word (normal map, displacement, dirt, grime, weeds, moss,
weathering, damage, wetness, rust, cracks, construction, village, Blender); (2) the descriptions of make-3d-models,
build-and-paint-a-place and make-explainer-film name the new skill; (3) the REQUIRED block is the same word for word in the
three skills that carry it; (4) every `explainer-film-place VERB` written in a skill, agent, workflow or guide is a verb that
`explainer-film-place --verbs` prints, and every --option written beside it is in that verb's --help; (5) every house number
written as place_section.key exists in film-settings.json; (6) every kit file named in backticks exists; (7) plugin.json says
1.4.0 and the README has a 1.4.0 entry and says nine stages (a marketplace file two folders up is only reported); (8) no new
text holds an email-like string, a provider settings folder, a long hex id or a key-looking value; (9) the agents the workflow
names exist; (10) explainer-film-setup treats a word that starts with - as an option, not a folder: --help prints the use line and
makes nothing, any other such word stops before a folder is made. Every check is also run on a deliberately wrong text (fixtures/place-skills/bad_skill.md, and texts made here) and
must fail there, so a check that can never fail cannot pass for nothing. Standard library only. The verb checks are skipped, said
plainly, when the launcher bin/explainer-film-place is not there or cannot print its verbs.
Run: python3 kit/calculators/tests/test_place_skills.py
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, KIT, PLUGIN  # noqa: E402

SKILL_NAME = 'surfaces-wear-and-construction'
SKILL_FOLDER = os.path.join(PLUGIN, 'skills', SKILL_NAME)
ROUTING_WORDS = ['normal map', 'displacement', 'dirt', 'grime', 'weeds', 'moss', 'weathering', 'damage', 'wetness', 'rust',
                 'cracks', 'construction', 'village', 'Blender']
CARRIERS = ['surfaces-wear-and-construction', 'make-3d-models', 'build-and-paint-a-place']   # skills that carry the REQUIRED block
ROUTERS = ['make-3d-models', 'build-and-paint-a-place', 'make-explainer-film']               # skills whose description names the new one
REQUIRED_START = 'REQUIRED for every place, set or prop you build in Blender'
FILE_EXTENSIONS = {'py', 'json', 'md', 'js', 'txt', 'blend', 'sh', 'png', 'jpg', 'env', 'mjs'}
KIT_PREFIXES = ('paper-film/', 'narration-tools/', 'examples/', 'docs/', 'place-kit/', 'calculators/')
PATTERN_CHARS = re.compile(r'[<>*{}$]|\bN\b|NAME|CHAPTER|\.\.\.|\bPLACE\b|\bOWNER\b|\bVERB\b')
BAD_FIXTURE = os.path.join(FIXTURES, 'place-skills', 'bad_skill.md')


def read(path):
    return open(path, encoding='utf-8').read()


def front_matter(text):
    """The key: value lines between the first two --- lines (single-line values only)."""
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


def check_front_matter(text, folder_name):
    problems = []
    meta = front_matter(text)
    if meta.get('name') != folder_name:
        problems.append(f"front matter name is {meta.get('name')!r}, the folder is {folder_name!r}")
    description = meta.get('description', '').lower()
    missing = [w for w in ROUTING_WORDS if w.lower() not in description]
    if missing:
        problems.append('the description lacks the routing words: ' + ', '.join(missing))
    return problems


def check_routing(descriptions):
    """descriptions: {skill name: description text}."""
    return [f'the description of {name} does not name {SKILL_NAME}' for name, text in descriptions.items() if SKILL_NAME not in text]


def required_block(text):
    """The run of '>' lines that starts with the REQUIRED line, or None."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if REQUIRED_START in line:
            block = []
            j = i
            while j < len(lines) and lines[j].startswith('>'):
                block.append(lines[j])
                j += 1
            return '\n'.join(block)
    return None


def check_blocks(blocks):
    """blocks: {skill name: block text or None}."""
    problems = [f'{name} has no REQUIRED block' for name, block in blocks.items() if not block]
    texts = {block for block in blocks.values() if block}
    if len(texts) > 1:
        problems.append('the REQUIRED block differs between skills: ' + ', '.join(sorted(blocks)))
    return problems


def code_spans(text, extension):
    """The pieces of text that may hold a command: backticked spans and fenced blocks (markdown), quoted strings (json, js)."""
    if extension in ('.json', '.js', '.mjs'):
        return re.findall(r'"((?:[^"\\\n]|\\.)*)"', text) + re.findall(r"'((?:[^'\\\n]|\\.)*)'", text)
    spans = []
    for block in re.findall(r'```.*?```', text, flags=re.S):
        spans.extend(line for line in block.split('\n') if line.strip() and not line.startswith('```'))
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    spans.extend(re.findall(r'`([^`]+)`', text))
    return spans


def commands_in(text, extension, verbs=None):
    """(verb, options, subcommand) for each `explainer-film-place VERB ...` (and, when verbs is given, each span that starts with a
    known verb) written in the text."""
    found = []
    for span in code_spans(text, extension):
        span = span.replace('\\|', '|')
        parts = [(m.start(), m.group(1)) for m in re.finditer(r'explainer-film-place\s+([a-z][a-z-]*)\b', span)]
        pieces = []
        for index, (start, verb) in enumerate(parts):
            end = parts[index + 1][0] if index + 1 < len(parts) else len(span)
            pieces.append((verb, span[start:end]))
        if not parts and verbs:
            first = span.strip().split(None, 1)
            if first and first[0] in verbs and extension == '.md':
                pieces.append((first[0], span.strip()))
        for verb, piece in pieces:
            after = piece.split(None, 2)
            sub = after[1] if len(after) > 1 and re.fullmatch(r'[a-z]+', after[1]) and not after[1].startswith('-') else None
            options = re.findall(r'(?<![\w-])(--[a-z][a-z0-9-]*)', piece)
            found.append((verb, options, sub))
    return found


class Launcher:
    """Asks bin/explainer-film-place for its verbs and each verb's --help (asked once)."""
    def __init__(self):
        wrapper = os.path.join(PLUGIN, 'bin', 'explainer-film-place')
        command = os.path.join(KIT, 'place-kit', 'place_command.py')
        if os.path.exists(wrapper):
            self.base = ['bash', wrapper]
        elif os.path.exists(command):
            self.base = [sys.executable, '-B', command]
        else:
            self.base = None
        self.cache = {}
        self.verbs = self._run(['--verbs'])
        self.verbs = None if self.verbs is None else [line.strip() for line in self.verbs[1].split('\n') if line.strip()]

    def _run(self, args):
        if not self.base:
            return None
        key = tuple(args)
        if key not in self.cache:
            try:
                run = subprocess.run(self.base + args, capture_output=True, text=True, timeout=90)
                self.cache[key] = (run.returncode, run.stdout + run.stderr)
            except (OSError, subprocess.TimeoutExpired):
                self.cache[key] = None
        found = self.cache[key]
        return found if found and found[0] == 0 else None

    def help_text(self, verb, sub=None):
        text = ''
        first = self._run([verb, '--help'])
        text += first[1] if first else ''
        if sub:
            second = self._run([verb, sub, '--help'])
            text += second[1] if second else ''
        return text if first else None


def check_commands(found, launcher, where):
    problems = []
    for verb, options, sub in found:
        if verb not in launcher.verbs:
            problems.append(f'{where}: `explainer-film-place {verb}` is not a verb ({len(launcher.verbs)} verbs are printed by --verbs)')
            continue
        help_text = launcher.help_text(verb, sub)
        if help_text is None:
            problems.append(f'{where}: `explainer-film-place {verb} --help` failed')
            continue
        for option in options:
            if option not in help_text:
                problems.append(f'{where}: {option} is written beside `{verb}` but is not in its --help')
    return problems


def house_number_keys(text):
    return sorted(set(re.findall(r'(?<![\w/.-])(place_[a-z]+)\.([a-z][a-z0-9_]*)\b', text)))


def check_house_numbers(text, settings, where):
    problems = []
    for section, key in house_number_keys(text):
        if key in FILE_EXTENSIONS:
            continue            # a file name such as place_audit_check.py, not a house number
        if section not in settings:
            problems.append(f'{where}: house number {section}.{key} names a section that is not in film-settings.json')
        elif key not in settings[section]:
            problems.append(f'{where}: house number {section}.{key} is not in film-settings.json')
    return problems


def named_files(text):
    """Kit files written in backticks (a word that starts with a kit folder name), without the patterns and folders."""
    names = set()
    for span in re.findall(r'`([^`\n]+)`', text):
        whole = re.sub(r'^(\$\{CLAUDE_PLUGIN_ROOT\}/)?(film-)?kit/', '', span.strip())
        # a whole name with spaces in it ("docs/LLM tips and tricks.md"), else each word of a command (as explainer-film-setup does)
        words = [whole] if ' ' in whole and os.path.exists(os.path.join(KIT, whole)) else span.split()
        for word in words:
            word = word.strip('"\'(),;:')
            word = re.sub(r'^(\$\{CLAUDE_PLUGIN_ROOT\}/)?(film-)?kit/', '', word)
            if not word.startswith(KIT_PREFIXES):
                continue
            if PATTERN_CHARS.search(word) or word.endswith('/') or word.startswith('paper-film/out/'):
                continue
            names.add(word)
    return sorted(names)


def check_files(text, where):
    return [f'{where}: `{name}` does not exist in the kit' for name in named_files(text) if not os.path.exists(os.path.join(KIT, name))]


def private_hits(text):
    """Email-like strings, a provider settings folder, a long hex id, a key-looking value."""
    hits = []
    if re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text):
        hits.append('an email-like string')
    if ('.run' + 'pod') in text:
        hits.append('a provider settings folder name')
    if re.search(r'\b[0-9a-f]{24,}\b', text):
        hits.append('a long hex id')
    if re.search(r'\brp' + r'a_[A-Za-z0-9]{16,}\b', text) or re.search(r'\bsk-[A-Za-z0-9]{20,}\b', text):
        hits.append('a key-looking value')
    return hits


def own_text_files():
    """The new text of this version: the new skill, the place agents and workflow, the templates, the launcher."""
    paths = sorted(glob.glob(os.path.join(SKILL_FOLDER, '*.md')))
    paths += sorted(glob.glob(os.path.join(PLUGIN, 'agents', 'place-*.md')))
    paths += [p for p in (os.path.join(PLUGIN, 'workflows', 'build-a-place.js'), os.path.join(PLUGIN, 'bin', 'explainer-film-place')) if os.path.exists(p)]
    paths += sorted(glob.glob(os.path.join(KIT, 'place-kit', 'data', 'templates', '*.md')))
    paths += sorted(glob.glob(os.path.join(KIT, 'place-kit', 'data', 'templates', '*.json')))
    paths += [os.path.join(PLUGIN, 'README.md'), os.path.join(PLUGIN, '.claude-plugin', 'plugin.json')]
    return [p for p in paths if os.path.exists(p)]


def scanned_text_files():
    """Every file whose commands, house numbers and file names are checked."""
    paths = sorted(glob.glob(os.path.join(PLUGIN, 'skills', '**', '*.md'), recursive=True))
    paths += sorted(glob.glob(os.path.join(PLUGIN, 'agents', '*.md')))
    paths += [p for p in (os.path.join(PLUGIN, 'workflows', 'build-a-place.js'),) if os.path.exists(p)]
    paths += [os.path.join(KIT, 'docs', 'LLM tips and tricks.md')]
    paths += sorted(glob.glob(os.path.join(KIT, 'place-kit', 'data', 'templates', '*.md')))
    paths += sorted(glob.glob(os.path.join(KIT, 'place-kit', 'data', 'templates', '*.json')))
    return [p for p in paths if os.path.exists(p)]


check = Checker('place skills: the words of the plugin against its code')
bad = read(BAD_FIXTURE)

# (1) the new skill's front matter and routing words
skill_path = os.path.join(SKILL_FOLDER, 'SKILL.md')
check.true('the new skill exists', os.path.exists(skill_path), details=skill_path)
skill_text = read(skill_path) if os.path.exists(skill_path) else ''
problems = check_front_matter(skill_text, SKILL_NAME)
check.true('the new skill: name equals its folder and the description holds every routing word', not problems, details='; '.join(problems) or 'yes')
check.true('  (on the wrong text this check fails)', bool(check_front_matter(bad, SKILL_NAME)))

# (2) the descriptions of the three routing skills name the new skill
descriptions = {}
for name in ROUTERS:
    path = os.path.join(PLUGIN, 'skills', name, 'SKILL.md')
    descriptions[name] = front_matter(read(path)).get('description', '') if os.path.exists(path) else ''
problems = check_routing(descriptions)
check.true('make-3d-models, build-and-paint-a-place and make-explainer-film name the new skill in their descriptions', not problems,
           details='; '.join(problems) or 'yes')
check.true('  (on the wrong text this check fails)', bool(check_routing({'bad': front_matter(bad).get('description', '')})))
# every skill's front matter must be plain YAML: a colon followed by a space inside a value breaks a strict parser
def yaml_problems(text, name):
    return [f'{name}: {key}' for key, value in front_matter(text).items() if key in ('description', 'when_to_use') and ': ' in value]


yaml_bad = []
for path in sorted(glob.glob(os.path.join(PLUGIN, 'skills', '*', 'SKILL.md'))):
    yaml_bad += yaml_problems(read(path), os.path.basename(os.path.dirname(path)))
check.true('no skill description or when_to_use holds a colon followed by a space (strict YAML)', not yaml_bad, details=', '.join(yaml_bad) or 'none does')
check.true('  (a description with such a colon fails this check)', bool(yaml_problems('---\nname: x\ndescription: it does this: and that\n---\n', 'made-up')))
master = read(os.path.join(PLUGIN, 'skills', 'make-explainer-film', 'SKILL.md'))
check.true('make-explainer-film sends place work to the new skill in "Before you start" and has the place stage row',
           'surfaces-wear-and-construction/SKILL.md' in master and '| `place` |' in master)

# (3) the REQUIRED block is the same in the three skills
blocks = {}
for name in CARRIERS:
    path = os.path.join(PLUGIN, 'skills', name, 'SKILL.md')
    blocks[name] = required_block(read(path)) if os.path.exists(path) else None
problems = check_blocks(blocks)
check.true('the REQUIRED block is identical in the three skills that carry it', not problems, details='; '.join(problems) or 'yes')
check.true('  (a changed block fails this check)', bool(check_blocks({'a': blocks[CARRIERS[0]], 'b': required_block(bad)})))
block_text = blocks[CARRIERS[0]] or ''
check.true('the REQUIRED block says to report plainly (never to hide the work) and names the audit and the place stage',
           'say plainly' in block_text and 'do not tell the user' not in block_text.lower()
           and 'explainer-film-preflight place' in block_text and 'explainer-film-place audit' in block_text)

# (4) the verbs and their options
launcher = Launcher()
files = scanned_text_files()
if launcher.verbs is None:
    check.note('skipped: the verb and option checks (bin/explainer-film-place is not there, or it cannot print its verbs yet)')
else:
    check.true('the launcher prints its verbs', len(launcher.verbs) >= 21, details=f'{len(launcher.verbs)} verbs')
    for path in files:
        where = os.path.relpath(path, PLUGIN)
        text = read(path)
        found = commands_in(text, os.path.splitext(path)[1], verbs=launcher.verbs if os.path.basename(path) == 'SKILL.md' else None)
        problems = check_commands(found, launcher, where)
        check.true(f'verbs and options in {where} ({len(found)} commands)', not problems, details='; '.join(problems[:4]) or 'all exist')
    bad_found = commands_in(bad, '.md')
    check.true('  (a made-up verb and a made-up option fail these checks)', len(check_commands(bad_found, launcher, 'bad')) >= 2)

# (4b) the preflight stages and their options, as written in the skills and guides
PREFLIGHT_STAGES = ['script', 'record', 'shots', 'place', 'plates', 'paint', 'pages', 'film', 'finish']
preflight = os.path.join(PLUGIN, 'bin', 'explainer-film-preflight')
if os.path.exists(preflight):
    try:
        run = subprocess.run(['bash', preflight, '--help'], capture_output=True, text=True, timeout=90)
        preflight_help = run.stdout + run.stderr
    except (OSError, subprocess.TimeoutExpired):
        preflight_help = ''
    problems, written = [], 0
    for path in files:
        where = os.path.relpath(path, PLUGIN)
        for span in code_spans(read(path), os.path.splitext(path)[1]):
            for match in re.finditer(r'explainer-film-preflight\s+([a-z]+)\b', span):
                if match.group(1) not in PREFLIGHT_STAGES:
                    continue
                written += 1
                rest = span[match.end():]
                nxt = re.search(r'explainer-film-', rest)
                rest = rest[:nxt.start()] if nxt else rest
                for option in re.findall(r'(?<![\w-])(--[a-z][a-z0-9-]*)', rest):
                    if option not in preflight_help:
                        problems.append(f'{where}: {option} is written beside the preflight stage {match.group(1)} but is not in its --help')
    check.true(f'every option written beside `explainer-film-preflight STAGE` is in the preflight\'s --help ({written} commands)',
               bool(preflight_help) and not problems, details='; '.join(problems[:4]) or 'all exist')
    check.true('the preflight has the stage place', 'place' in preflight_help)
else:
    check.note('skipped: bin/explainer-film-preflight is not there')

# (5) house numbers
settings = json.load(open(os.path.join(KIT, 'film-settings.json'), encoding='utf-8'))
all_problems, counted = [], 0
for path in files:
    text = read(path)
    counted += len(house_number_keys(text))
    all_problems += check_house_numbers(text, settings, os.path.relpath(path, PLUGIN))
check.true(f'every house number written as place_section.key exists in film-settings.json ({counted} written)', not all_problems,
           details='; '.join(all_problems[:4]) or 'all exist')
check.true('  (a made-up house number fails this check)', bool(check_house_numbers(bad, settings, 'bad')))

# (6) the kit files named in backticks
all_problems, counted = [], 0
for path in files:
    text = read(path)
    counted += len(named_files(text))
    all_problems += check_files(text, os.path.relpath(path, PLUGIN))
check.true(f'every kit file named in backticks exists ({counted} named)', not all_problems, details='; '.join(all_problems[:4]) or 'all exist')
check.true('  (a made-up file name fails this check)', bool(check_files(bad, 'bad')))
basenames = {os.path.basename(p) for p in glob.glob(os.path.join(PLUGIN, '**', '*'), recursive=True) if os.path.isfile(p)}
loose = []
for path in sorted(glob.glob(os.path.join(SKILL_FOLDER, '*.md'))):
    for name in re.findall(r'`([A-Za-z0-9_-]+\.md)`', read(path)):
        if name not in basenames:
            loose.append(f'{os.path.basename(path)}: `{name}`')
check.true('every plain file name ending in .md written in the new skill is a file of the plugin', not loose, details='; '.join(loose) or 'all are')
expected = ['SKILL.md', 'the-required-steps.md', 'surface-recipes.md', 'wear-recipes.md', 'construction-and-scale.md',
            'style-rule-and-measures.md', 'fresh-checkers.md', 'rendering-on-rented-cards.md', 'worked-examples-garden-and-canal-lock.md', 'blender-5-traps.md']
missing = [n for n in expected if not os.path.exists(os.path.join(SKILL_FOLDER, n))]
check.true('the new skill folder holds all ten files', not missing, details=', '.join(missing) or 'all ten')

# (7) versions, README
plugin_json = json.load(open(os.path.join(PLUGIN, '.claude-plugin', 'plugin.json'), encoding='utf-8'))
check.equal('plugin.json says 1.4.0', plugin_json.get('version'), '1.4.0')
readme = read(os.path.join(PLUGIN, 'README.md'))
check.true('the README has a 1.4.0 entry and says nine stages', '**1.4.0 (' in readme and 'nine stages' in readme)
check.true('the README names the reminder hook and says its format was not run inside Claude Code', 'hooks/hooks.json' in readme and 'place-reminder.py' in readme and 'run inside Claude Code' in ' '.join(readme.split()))
marketplace = os.path.normpath(os.path.join(PLUGIN, '..', '..', '.claude-plugin', 'marketplace.json'))
if os.path.exists(marketplace):
    try:
        entries = json.load(open(marketplace, encoding='utf-8')).get('plugins', [])
        version = next((e.get('version') for e in entries if e.get('name') == plugin_json.get('name')), None)
    except ValueError:
        version = None
    if version == plugin_json.get('version'):
        check.note(f'the marketplace file says {version} too')
    else:
        check.note(f'not checked as a failure: the marketplace file two folders up says {version}, plugin.json says {plugin_json.get("version")} '
                   '(it is outside the plugin folder; whoever publishes sets it)')
else:
    check.note('not checked: no marketplace file two folders up (the plugin stands alone)')

# (7b) the parts the README and the 1.4.0 entry say are inside the plugin really are there
claimed = ['bin/explainer-film-place', 'kit/calculators/place_audit_check.py', 'kit/calculators/picture_measures.py',
           'workflows/build-a-place.js', 'kit/place-kit/README.md', 'kit/place-kit/SOURCES-AND-LICENCES.md', 'kit/place-kit/DEVIATIONS.md',
           'hooks/hooks.json', 'hooks/place-reminder.py']
claimed += [f'agents/place-{role}.md' for role in ('planner', 'builder', 'integrator', 'renderer', 'checker')]
absent = [name for name in claimed if not os.path.exists(os.path.join(PLUGIN, name))]
check.true(f'every part the README says is inside the plugin is there ({len(claimed)} named)', not absent, details=', '.join(absent) or 'all are there')
model_lint = os.path.join(KIT, 'paper-film', 'blender', 'model_lint.py')
lint_help = ''
if os.path.exists(model_lint):
    try:
        run = subprocess.run([sys.executable, '-I', '-B', model_lint, '--help'], capture_output=True, text=True, timeout=90)
        lint_help = run.stdout + run.stderr
    except (OSError, subprocess.TimeoutExpired):
        lint_help = ''
check.true('model_lint.py has the --surfaces option the README, the skills and the tips guide mention', '--surfaces' in lint_help,
           details='yes' if '--surfaces' in lint_help else 'model_lint.py --help does not list --surfaces')

# (8) privacy
all_hits = []
for path in own_text_files():
    hits = private_hits(read(path))
    if hits:
        all_hits.append(f'{os.path.relpath(path, PLUGIN)}: {", ".join(hits)}')
check.true(f'no new text holds an email-like string, a provider settings folder, a long hex id or a key-looking value ({len(own_text_files())} files)',
           not all_hits, details='; '.join(all_hits) or 'none')
made_up = 'write to ' + 'someone' + '@' + 'example.org' + ' in ' + '.run' + 'pod' + ' with ' + 'a1b2c3d4' * 4 + ' and rp' + 'a_' + 'x' * 20
check.true('  (made-up private text fails this check, with all four kinds)', len(private_hits(made_up)) == 4)

# (9) the agents the workflow names
workflow = os.path.join(PLUGIN, 'workflows', 'build-a-place.js')
if os.path.exists(workflow):
    named = sorted(set(re.findall(r'place-[a-z]+\.md', read(workflow))))
    missing = [n for n in named if not os.path.exists(os.path.join(PLUGIN, 'agents', n))]
    check.true(f'the agent files the workflow names exist ({", ".join(named) or "none named"})', not missing and bool(named),
               details=', '.join(missing) or 'all exist')
else:
    check.note('skipped: workflows/build-a-place.js is not there yet')

# (10) the setup command and a word that starts with - (a newcomer once ran it with --help: it made a junk folder tree named after cd's help text)
import tempfile  # noqa: E402
setup = os.path.join(PLUGIN, 'bin', 'explainer-film-setup')
empty = tempfile.mkdtemp(prefix='setup-argument-test-')
try:
    asked_help = subprocess.run(['bash', setup, '--help'], cwd=empty, capture_output=True, text=True, timeout=60)
    asked_option = subprocess.run(['bash', setup, '-q'], cwd=empty, capture_output=True, text=True, timeout=60)
    left = os.listdir(empty)
    check.true('`explainer-film-setup --help` prints the use line, exits 0 and makes nothing; `explainer-film-setup -q` stops with exit 2 and makes nothing',
               asked_help.returncode == 0 and 'Use: explainer-film-setup' in asked_help.stdout and asked_option.returncode == 2 and 'is not a folder' in asked_option.stderr and not left,
               details=f'exits {asked_help.returncode} and {asked_option.returncode}; left in the folder: {left or "nothing"}')
finally:
    shutil_rmtree = __import__('shutil').rmtree
    shutil_rmtree(empty, ignore_errors=True)
check.finish()
