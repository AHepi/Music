"""Scratch: builds dev-film-settings.json = the plugin kit's film-settings.json + this helper's sections (for testing
before the one real edit). Use: python3 make_dev_settings.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
real = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
data = json.load(open(real))
mine = json.load(open(os.path.join(HERE, 'my-sections.json')))
for k, v in mine.items():
    data[k] = v
open(os.path.join(HERE, 'dev-film-settings.json'), 'w').write(json.dumps(data, indent=1) + '\n')
print('wrote dev-film-settings.json with', ', '.join(mine))
