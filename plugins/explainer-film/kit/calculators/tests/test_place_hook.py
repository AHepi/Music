"""What this does: tests the plugin's prompt-time reminder (hooks/hooks.json and hooks/place-reminder.py), which makes a model that was asked only for a place ("build a canal lock", "make a garden") read the
surface-and-wear skill first, even when other Blender skills compete for the request.
1. hooks.json is valid JSON, names one UserPromptSubmit hook that runs place-reminder.py from the plugin folder, and that script is there.
2. Requests that build a place, a set or props (a village, a lock, a garden, a prop, Blender itself) get the reminder, which names the skill and the three commands.
3. Requests that are not about building a place (weather, a typo, a poem, a shopping cart in a web page, a random forest, a stable build, film pages, a market analysis, the plugin
   marketplace file, a street address parser, a docking station) get nothing at all; railway, station, market, street and pier requests do get it.
4. A message the script cannot read (not JSON, no prompt, empty input) gets nothing and exit 0: a hook must never stop the person's work.
5. The reminder names only commands and skills that exist (the skill folder, the three commands) and holds no key, no address and no personal detail.
6. The film-frame routing (plugin 1.4.0, lessons round): the reminder's second line sends a place that will be shown in the film to the skill
   build-and-paint-a-place and sections 4 to 12 of the tips guide, and says a film view is 1080 x 1920; both skill folders and the guide exist.
7. The person's words win: a request about building a place that says not to use the plugin or its skills ("plain Blender", "without the plugin",
   "do not use the plugin", "don't use the plugin", "do not use the skill") gets nothing; the same request without those words still gets the reminder,
   so the check can fail. Read narrowly (fix round): "with and without the plugin" and "do not use skills from another set" still get the reminder.
8. (fix round) Plain place words a blind newcomer found silent now get the reminder (a monastery, a cloister, a lighthouse, a factory floor, a stone bridge, a fort, a classroom),
   while their software senses stay silent (a lighthouse score, a bridge pattern, a factory function, shedding light).
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
    'Perfect. Now build a canal lock beside a towpath. Needs weathered brick walls, a wooden gate, stone steps and a few props.',
    'Build a village with a few houses and some props.',
    'make a cabin',
    'create a harbour with boats',
    'put together a market square with props',
    'build a small farm with a barn and a yard',
    'Model a barrel in Blender',
    'write a python script for blender that makes a tavern interior',
    'I need a 3D diorama of a mill',
    'furnish the kitchen with props',
    # the second newcomer round: plain place requests that say neither Blender nor 3D
    'Build an old railway station for a film.',
    'Make a railway station with platforms and tracks for the film',
    'Make a fish market by the sea for the film',
    'Build a street with shops',
    'build a pier',
    'make a small chapel on a hill',
    # the fix round (the blind newcomer judge found these silent): plain place words that are not software words
    'Make an old mountain monastery for the film', 'Build an abbey cloister for a film', 'Make a lighthouse on a cliff', 'Build a factory floor for chapter 3',
    'Build a stone bridge over a river', 'Make a fort on a hill', 'Build a school classroom',
]
for prompt in positive:
    text = reminder_for(prompt)
    check.true(f'a reminder for: {prompt[:60]}', 'surfaces-wear-and-construction' in text and 'explainer-film-place finish' in text and 'explainer-film-place audit' in text and 'explainer-film-preflight place' in text, text[:80] or '(nothing printed)')

# 3. requests that are not
negative = [
    'what is the weather in Oslo', 'fix the typo in my README', 'write a poem about the sea', 'add a test for the road parser', 'make the music louder in the film',
    'build a random forest classifier', 'make the nightly build stable', 'add a cart to the shop page', 'make room for the new button', 'Build the film scene for page 4', 'record the narration for chapter 2',
    'explain what causes inflation', 'make a market analysis for the report', 'update the marketplace file', 'make a street address parser', 'create a docking station for the laptop',
    'build a work station list', 'make the lighthouse score better', 'build a bridge pattern class', 'make a factory function', 'make it shed light on the problem', '',
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
# 6. the film-frame routing in line 2
second = text.splitlines()[1] if len(text.splitlines()) > 1 else ''
check.true('line 2 sends a place for the film to build-and-paint-a-place and sections 4 to 12 of the tips guide before a camera is placed, and says 1080 x 1920',
           'build-and-paint-a-place' in second and 'sections 4 to 12' in second and 'LLM tips and tricks.md' in second and '1080 x 1920' in second and 'before you place a camera' in second,
           second[:120])
check.true('  (the skill folder build-and-paint-a-place and the tips guide it names exist)',
           os.path.isdir(os.path.join(PLUGIN, 'skills', 'build-and-paint-a-place')) and os.path.exists(os.path.join(PLUGIN, 'kit', 'docs', 'LLM tips and tricks.md')))

# 7. the person's "leave the plugin out" wins
leave_out = [
    'Build a canal lock in plain Blender.',
    'Build a village in Blender without the plugin.',
    'Make a barn with a few props in Blender. Do not use the plugin.',
    "Build a small farm with a barn, but don't use the plugin",
    'Build a garden in Blender and do not use the skill',
    'Build a cabin in 3D, don\u2019t use the plugin',
]
for prompt in leave_out:
    check.true(f'nothing when the person says to leave the plugin out: {prompt[:60]}', reminder_for(prompt) == '', reminder_for(prompt)[:80])
for prompt in ('Build a canal lock in Blender.', 'Build a village in Blender with the plugin.', 'Make a barn with a few props in Blender.'):
    check.true(f'  (the same kind of request without those words still gets the reminder: {prompt[:50]})', 'surfaces-wear-and-construction' in reminder_for(prompt))
# ...read narrowly (fix round): a comparison "with and without the plugin" and a "do not use" about some other skill are not a leave-out
for prompt in ('Build a farm. Compare with and without the plugin later', 'Build a farm with or without the plugin, your choice',
               'Build a garden in Blender and do not use skills from the Scenario set', 'Build a garden in Blender, do not use the skill scenario-blender-expert'):
    check.true(f'  (not a leave-out, so the reminder is still printed: {prompt[:60]})', 'surfaces-wear-and-construction' in reminder_for(prompt), reminder_for(prompt)[:60] or '(nothing printed)')
for prompt in ("Build a cabin, don't use the skills", 'Do not use the explainer-film skills about lighting; build a barn'):
    check.true(f'nothing when the person says to leave the plugin\'s skills out: {prompt[:60]}', reminder_for(prompt) == '', reminder_for(prompt)[:80])

source = open(SCRIPT, encoding='utf-8').read()
forbidden = re.search(r'\b(urllib|socket|requests|open\(|os\.environ|subprocess)\b', re.sub(r'\"\"\".*?\"\"\"', '', source, flags=re.S))      # the note at the top may say these words; the code may not use them
check.true('the script reads only standard input and prints (no network, no files, no settings)', forbidden is None, forbidden.group(0) if forbidden else 'none found')
check.finish()
