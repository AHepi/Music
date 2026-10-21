# makes the private tuned copies used for measuring (the kit's own sets/ and presets/ are never edited):
#   work/tuned/street_set.json, work/tuned/look_street.json     (python3 work/mk_tuned.py)
import json, copy, os
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'kits', 'weathering'))
OUT = os.path.join(HERE, 'tuned')
tuned = json.load(open(os.path.join(OUT, 'tuned_street.json')))
look = json.load(open(os.path.join(KIT, 'presets', 'sooty_1926.json')))
for layer, dials in tuned['layers'].items():
    look['layers'].setdefault(layer, {}).update(dials)
look['id'] = 'sooty_1926_walls_tuned'
json.dump(look, open(os.path.join(OUT, 'look_street.json'), 'w'), indent=1)
sset = json.load(open(os.path.join(KIT, 'sets', 'pit_village_street.json')))
sset['looks']['default'] = os.path.join(OUT, 'look_street.json')
for layer, rd in tuned.get('role_dials', {}).items():
    sset['apply'][layer]['role_dials'] = rd
json.dump(sset, open(os.path.join(OUT, 'street_set.json'), 'w'), indent=1)
print('made', OUT)
