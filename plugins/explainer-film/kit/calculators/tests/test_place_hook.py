"""What this does: tests the plugin's prompt-time reminder (hooks/hooks.json and hooks/place-reminder.py), which makes a model that was asked only for "a village in the forest" read the
surface-and-wear skill first, even when other Blender skills compete for the request.
1. hooks.json is valid JSON, names one UserPromptSubmit hook that runs place-reminder.py from the plugin folder, and that script is there.
2. Requests that build a place, a set or props (the person's own village request among them) get the reminder, which names the skill and the three commands.
3. Requests that are not about building a place (weather, a typo, a poem, a shopping cart in a web page, a random forest, film pages) get nothing at all.
4. A message the script cannot read (not JSON, no prompt, empty input) gets nothing and exit 0: a hook must never stop the person's work.
5. The reminder names only commands and skills that exist (the skill folder, the three commands) and holds no key, no address and no personal detail.
Run: python3 kit/calculators/tests/test_place_hook.py
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, PLUGIN  # noqa: E402

check = Checker('place reminder hook: routing words at the start of a turn')
HOOKS = os.path.join(PLUGIN, 'hooks')
SCRIPT = os.path.join(HOOKS, 'place-reminder.py')


def run_hook(stdin_text):
    done = subprocess.run([sys.executable, '-I', '-B', SCRIPT], input=stdin_text, capture_output=True, text=True, timeout=30)
    return done.returncode, done.stdout


def reminder_for(prompt):
    return run_hook(json.dumps({'prompt': prompt}))[1].strip()


# 1. the hook file
try:
    with open(os.path.join(HOOKS, 'hooks.json'), encoding='utf-8') as handle:
        config = json.load(handle)
except (OSError, ValueError) as problem:
    config = {}
    check.true('hooks.json is valid JSON', False, str(problem))
entries = config.get('hooks', {}).get('UserPromptSubmit', [])
commands = [h.get('command', '') for entry in entries for h in entry.get('hooks', []) if h.get('type') == 'command']
check.true('hooks.json has exactly one UserPromptSubmit hook that is a command', len(entries) == 1 and len(commands) == 1, str(commands))
check.true('that command runs place-reminder.py from the plugin folder', bool(commands) and '${CLAUDE_PLUGIN_ROOT}/hooks/place-reminder.py' in commands[0], str(commands))
check.true('place-reminder.py is there', os.path.exists(SCRIPT))

# 2. requests that build a place
positive = [
    'Perfect. Now build a village in the forest. Needs unkept dirt roads like they\'ve been driven down by horse and carriage, an empty stable, a few cottages, some scattered mediaeval props.',
    'make a cottage',
    'create a harbour with boats',
    'put together a medieval market with props',
    'build a small farm with a barn and a yard',
    'Model a barrel in Blender',
    'write a python script for blender that makes a tavern interior',
    'I need a 3D diorama of a mill',
    'furnish the kitchen with props',
]
for prompt in positive:
    text = reminder_for(prompt)
    check.true(f'a reminder for: {prompt[:60]}', 'surfaces-wear-and-construction' in text and 'explainer-film-place finish' in text and 'explainer-film-place audit' in text and 'explainer-film-preflight place' in text, text[:80] or '(nothing printed)')

# 3. requests that are not
negative = [
    'what is the weather in Oslo', 'fix the typo in my README', 'write a poem about the sea', 'add a test for the road parser', 'make the music louder in the film',
    'build a random forest classifier', 'add a cart to the shop page', 'make room for the new button', 'Build the film scene for page 4', 'record the narration for chapter 2',
    'explain what causes inflation', '',
]
for prompt in negative:
    text = reminder_for(prompt)
    check.true(f'nothing for: {prompt[:60] or "(an empty message)"}', text == '', text[:80])

# 4. input it cannot read
for label, stdin_text in (('not JSON', '{bad'), ('no prompt', '{"session": 1}'), ('a number for the prompt', '{"prompt": 5}'), ('empty input', ''), ('a list', '[1, 2]')):
    code, out = run_hook(stdin_text)
    check.true(f'unreadable input ({label}): exit 0 and nothing printed', code == 0 and out.strip() == '', f'exit {code}, {out[:60]!r}')

# 5. what the reminder names
text = reminder_for('build a village')
check.true('the skill it names is a folder of the plugin', os.path.isdir(os.path.join(PLUGIN, 'skills', 'surfaces-wear-and-construction')))
check.true('it is three lines or fewer and says to ignore it when the work is not 3D', len(text.splitlines()) <= 3 and 'ignore it if this is not 3D work' in text, str(len(text.splitlines())))
check.true('it holds no key, address, e-mail or long id', not re.search(r'https?://|@[a-z0-9-]+\.[a-z]|rpa_|[0-9a-f]{24,}|api[_ ]?key', text, re.I), text[:80])
source = open(SCRIPT, encoding='utf-8').read()
forbidden = re.search(r'\b(urllib|socket|requests|open\(|os\.environ|subprocess)\b', re.sub(r'\"\"\".*?\"\"\"', '', source, flags=re.S))      # the note at the top may say these words; the code may not use them
check.true('the script reads only standard input and prints (no network, no files, no settings)', forbidden is None, forbidden.group(0) if forbidden else 'none found')
check.finish()
