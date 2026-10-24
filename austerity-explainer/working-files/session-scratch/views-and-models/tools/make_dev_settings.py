"""Scratch (views-and-models helper): merges my section file into a copy of the plugin's film-settings.json, so my tools
can be developed against it (FILM_SETTINGS=...dev-film-settings.json) before the one edit to the real file.
Use: python3 make_dev_settings.py"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
SECTION = os.path.join(HERE, 'views_and_models_section.json')
OUT = os.path.join(os.path.dirname(HERE), 'dev-film-settings.json')

with open(REAL) as handle:
    data = json.load(handle)
with open(SECTION) as handle:
    section = json.load(handle)
data['views_and_models'] = section
with open(OUT, 'w') as handle:
    json.dump(data, handle, indent=1)
print('wrote', OUT)
