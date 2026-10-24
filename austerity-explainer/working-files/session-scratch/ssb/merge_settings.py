"""Scratch helper: writes dev-settings.json = the plugin's film-settings.json plus this helper's own sections (for testing
before the one real edit)."""
import json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
real = json.load(open('/home/user/Music/plugins/explainer-film/kit/film-settings.json'))
for name in ('budget_planner', 'script_gate', 'sound_gates'):
    path = os.path.join(HERE, name + '.json')
    if os.path.exists(path):
        real[name] = json.load(open(path))
json.dump(real, open(os.path.join(HERE, 'dev-settings.json'), 'w'), indent=1, ensure_ascii=False)
print('wrote dev-settings.json with', [k for k in ('budget_planner', 'script_gate', 'sound_gates') if k in real])
