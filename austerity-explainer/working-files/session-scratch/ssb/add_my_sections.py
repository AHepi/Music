"""Scratch helper (not shipped): adds the script-sound-budget helper's three sections (script_gate, sound_gates,
budget_planner) to the plugin's film-settings.json in ONE write, as text inserted before the file's last closing
brace, so every other byte of the file stays as it is. It re-reads the file right before writing and refuses if any of
the three sections is already there."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
names = ('script_gate', 'sound_gates', 'budget_planner')
text = open(PATH, encoding='utf-8').read()          # re-read right before the edit
data = json.loads(text)
for name in names:
    if name in data:
        sys.exit(f'{name} is already in {PATH}; nothing written')
blocks = []
for name in names:
    section = json.load(open(os.path.join(HERE, name + '.json')))
    body = json.dumps({name: section}, indent=1, ensure_ascii=False)
    blocks.append(body[2:-2])                      # ' "name": {...}' without the outer braces
end = text.rstrip().rfind('}')
new_text = text[:end].rstrip() + ',\n' + ',\n'.join(blocks) + '\n}\n'
merged = json.loads(new_text)
assert all(merged[k] == v for k, v in data.items()), 'an existing section changed'
assert all(n in merged for n in names)
open(PATH, 'w', encoding='utf-8').write(new_text)
print(f'added {", ".join(names)} to {PATH}: {len(text)} -> {len(new_text)} characters; every other section unchanged')
