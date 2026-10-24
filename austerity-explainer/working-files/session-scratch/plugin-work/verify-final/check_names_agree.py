"""What this does: checks that the words of the explainer-film plugin (skills, place agents, hook, workflow, READMEs, tips guide, templates)
agree with its real commands. It reads every `explainer-film-place VERB ...` and `explainer-film-preflight STAGE ...` it can find in those texts,
and checks that the verb, the action (for variations, card-time, rent) and every --option really exist in the command's own help.
It also checks house-number keys (place_variations.x, place_render.x, ...) against kit/film-settings.json, file names the texts point to,
and the agent and skill names the workflow and hook use.
A concrete example: the text "explainer-film-place variations scout cracks.json --helper me" is checked for the verb `variations`, the action
`scout` and the option `--helper`.
Run: python3 check_names_agree.py PLUGIN_FOLDER
Writes nothing; prints one line per problem and a count at the end.
"""
import glob
import json
import os
import re
import subprocess
import sys

plugin_folder = os.path.abspath(sys.argv[1])
place_command = os.path.join(plugin_folder, 'bin', 'explainer-film-place')
preflight_command = os.path.join(plugin_folder, 'bin', 'explainer-film-preflight')
problems = []
counts = {'commands': 0, 'options': 0, 'house_keys': 0, 'file_links': 0}


def help_text(arguments):
    done = subprocess.run(arguments, capture_output=True, text=True, timeout=120)
    return done.stdout + done.stderr


verbs = help_text([place_command, '--verbs']).split()
verbs = [verb.strip(',') for verb in verbs if re.fullmatch(r'[a-z-]+,?', verb)]
options_of_verb = {}
actions_of_verb = {}
for verb in verbs:
    text = help_text([place_command, verb, '--help'])
    options_of_verb[verb] = set(re.findall(r'(--[a-z][a-z0-9-]*)', text))
    choice = re.search(r'\{([a-z,_-]+)\}\s*\n?\s*\[?spec|\n\s+\{([a-z,_-]+)\}', text)
    found = re.findall(r'\{([a-z][a-z0-9,_-]+)\}', text)
    actions_of_verb[verb] = set()
    for group in found:
        if ',' in group and verb in ('variations', 'card-time', 'rent', 'roles', 'measure'):
            actions_of_verb[verb] |= set(group.split(','))
preflight_help = help_text([preflight_command, '--help'])
preflight_options = set(re.findall(r'(--[a-z][a-z0-9-]*)', preflight_help))
stages = ['script', 'record', 'shots', 'place', 'plates', 'paint', 'pages', 'film', 'finish']

settings = json.load(open(os.path.join(plugin_folder, 'kit', 'film-settings.json'), encoding='utf-8'))

TEXTS = []
for pattern in ['skills/**/*.md', 'agents/place-*.md', 'hooks/*.py', 'workflows/build-a-place.js', 'README.md', 'kit/place-kit/README.md',
                'kit/place-kit/DEVIATIONS.md', 'kit/docs/LLM tips and tricks.md', 'kit/place-kit/data/templates/*', 'kit/calculators/README.md']:
    TEXTS += glob.glob(os.path.join(plugin_folder, pattern), recursive=True)
TEXTS = sorted(set(TEXTS))

command_pattern = re.compile(r'explainer-film-place\s+([a-z][a-z-]*)((?:[ \t]+(?:\\\n\s*)?[^\s`"\'|;)]+){0,40})')
preflight_pattern = re.compile(r'explainer-film-preflight\s+([a-z-]+)((?:[ \t]+[^\s`"\'|;)]+){0,20})')
house_key_pattern = re.compile(r'\b(place_[a-z_]+)\.([a-z][a-z0-9_]+)\b')

for path in TEXTS:
    text = open(path, encoding='utf-8', errors='replace').read()
    short = os.path.relpath(path, plugin_folder)
    for match in command_pattern.finditer(text):
        verb, rest = match.group(1), match.group(2)
        line = text.count('\n', 0, match.start()) + 1
        counts['commands'] += 1
        if verb in ('VERB', 'verb'):
            continue
        if verb not in verbs:
            if verb not in ('is', 'and', 'or', 'the', 'a', 'to', 'command', 'tool', 'verb', 'verbs', 'help', 'on', 'with', 'in', 'does', 'variations-worker'):
                problems.append(f'{short}:{line}: unknown verb "{verb}" in "explainer-film-place {verb}{rest[:60]}"')
            continue
        words = rest.replace('\\\n', ' ').split()
        if verb in actions_of_verb and actions_of_verb[verb] and words:
            first = words[0]
            if not first.startswith('-') and re.fullmatch(r'[a-z-]+', first) and first not in actions_of_verb[verb]:
                problems.append(f'{short}:{line}: "{verb}" has no action "{first}" (actions: {sorted(actions_of_verb[verb])})')
        for word in words:
            option = re.match(r'(--[a-z][a-z0-9-]*)', word)
            if option:
                counts['options'] += 1
                if option.group(1) not in options_of_verb[verb]:
                    problems.append(f'{short}:{line}: "{verb}" has no option {option.group(1)}')
    for match in preflight_pattern.finditer(text):
        stage, rest = match.group(1), match.group(2)
        line = text.count('\n', 0, match.start()) + 1
        counts['commands'] += 1
        if stage.startswith('-') or stage in ('STAGE', 'stage'):
            continue
        if stage not in stages and stage not in ('is', 'and', 'or', 'the', 'a', 'stage', 'runs', 'with', 'for', 'at', 'gate', 'reports'):
            problems.append(f'{short}:{line}: unknown preflight stage "{stage}"')
        for word in rest.split():
            option = re.match(r'(--[a-z][a-z0-9-]*)', word)
            if option and option.group(1) not in preflight_options:
                counts['options'] += 1
                problems.append(f'{short}:{line}: preflight has no option {option.group(1)}')
    for match in house_key_pattern.finditer(text):
        group, key = match.group(1), match.group(2)
        if group not in settings:
            continue
        counts['house_keys'] += 1
        if not isinstance(settings[group], dict) or key not in settings[group]:
            line = text.count('\n', 0, match.start()) + 1
            problems.append(f'{short}:{line}: house number {group}.{key} is not in kit/film-settings.json')
    for match in re.finditer(r'`([A-Za-z0-9_./${}-]+\.(?:md|json|py|js|blend|jsonl))`', text):
        name = match.group(1)
        if '${' in name and 'CLAUDE_PLUGIN_ROOT' not in name:
            continue
        name = name.replace('${CLAUDE_PLUGIN_ROOT}/', '')
        if any(token in name for token in ('YOUR', 'NAME', '<', 'FILE', 'SCENE', 'RUN-FOLDER')):
            continue
        counts['file_links'] += 1
        candidates = [os.path.join(plugin_folder, name), os.path.join(os.path.dirname(path), name), os.path.join(plugin_folder, 'kit', name),
                      os.path.join(plugin_folder, 'kit', 'place-kit', name), os.path.join(plugin_folder, 'kit', 'place-kit', 'data', name),
                      os.path.join(plugin_folder, 'kit', 'calculators', name), os.path.join(plugin_folder, 'skills', 'surfaces-wear-and-construction', name)]
        if '/' not in name:
            if glob.glob(os.path.join(plugin_folder, '**', name), recursive=True):
                continue
        if not any(os.path.exists(candidate) for candidate in candidates):
            line = text.count('\n', 0, match.start()) + 1
            problems.append(f'{short}:{line}: points to `{name}`, which is not in the plugin (may be a file the user makes)')

# agents and skills named by the workflow and the hook
workflow = open(os.path.join(plugin_folder, 'workflows', 'build-a-place.js'), encoding='utf-8').read()
agent_names = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(plugin_folder, 'agents', '*.md'))}
for name in sorted(set(re.findall(r'\b(place-[a-z]+)\b', workflow))):
    if name not in agent_names and name not in ('place-settings', 'place-audit', 'place-kit', 'place-reminder', 'place-type'):
        problems.append(f'workflows/build-a-place.js: names "{name}", which is not an agent file')
skill_names = {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(plugin_folder, 'skills', '*', 'SKILL.md'))}
for path in TEXTS:
    text = open(path, encoding='utf-8', errors='replace').read()
    for name in set(re.findall(r'skill[s]? `?([a-z]+(?:-[a-z0-9]+){1,6})`?', text)):
        if name not in skill_names and not name.startswith('scenario-') and name not in ('explainer-film',):
            problems.append(f'{os.path.relpath(path, plugin_folder)}: names skill "{name}", which is not a skill folder')

print(f'texts read: {len(TEXTS)}; verbs: {len(verbs)}; commands found: {counts["commands"]}; options checked: {counts["options"]}; '
      f'house numbers checked: {counts["house_keys"]}; file links checked: {counts["file_links"]}')
print(f'actions: { {verb: sorted(actions) for verb, actions in actions_of_verb.items() if actions} }')
for problem in problems:
    print('PROBLEM', problem)
print(f'{len(problems)} problem(s)')
