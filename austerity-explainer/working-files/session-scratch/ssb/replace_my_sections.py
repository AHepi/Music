"""Scratch helper (not shipped): replaces ONLY this helper's three sections (script_gate, sound_gates, budget_planner) in
the plugin's film-settings.json, in one write, re-reading the file right before; every other section is checked unchanged."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
PATH = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
names = ('script_gate', 'sound_gates', 'budget_planner')
text = open(PATH, encoding='utf-8').read()
data = json.loads(text)
start = min(text.index(f'\n "{n}": {{') for n in names)
# the three sections are the last three, written by add_my_sections.py; check nothing follows them
tail = json.loads('{' + text[start:].rstrip().rstrip('}').rstrip() + '}')
assert list(tail) == list(names), list(tail)
blocks = [json.dumps({n: json.load(open(os.path.join(HERE, n + '.json')))}, indent=1, ensure_ascii=False)[2:-2] for n in names]
new_text = text[:start] + '\n' + ',\n'.join(blocks) + '\n}\n'
merged = json.loads(new_text)
assert all(merged[k] == v for k, v in data.items() if k not in names), 'another section changed'
open(PATH, 'w', encoding='utf-8').write(new_text)
print('replaced', ', '.join(names), 'in', PATH)
