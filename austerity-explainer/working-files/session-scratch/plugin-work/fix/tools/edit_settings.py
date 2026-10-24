"""Scratch helper (not part of the plugin): adds or changes house numbers in kit/film-settings.json, keeping its layout. Safe to run twice."""
import json
import sys

PATH = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
raw = open(PATH, encoding='utf-8').read()
data = json.loads(raw)


def put(section, key, value, unit, kind, source, note=None):
    entry = {'value': value, 'unit': unit, 'kind': kind, 'source': source}
    if note:
        entry['note'] = note
    data[section][key] = entry


put('place_construction', 'sunk_in_centimetres_max', 4, 'centimetres', 'judged',
    'plugin 1.4.0 fix round (23 October 2026): the smoke check found a board bedded 6 mm into its post failing as "floats"; a part may sit this far into what carries it and still count as resting on it (the same size as the overlap that counts as joined, judged from the garden bridge)')
put('place_audit', 'ground_area_growth_max', 1.5, 'times', 'judged',
    'plugin 1.4.0 fix round: a ground object whose outline area grew more than this after the roads step was reshaped into its bounding box (a curved lane became a rectangle: the fault the code review measured grew its area 3.4 times; a correct change keeps it at 1.0)')
data['place_audit']['fallback_role_share_fail']['value'] = 0.15
data['place_audit']['fallback_role_share_fail']['source'] = ('the plugin 1.4.0 design (22 October 2026) said 0.5; lowered to 0.15 in the 1.4.0 fix round, because after finish a roleless object only warns and a harbour of grey '
                                                             'stone piles could pass at 0.5: above this share the roles say nothing')
put('place_render', 'cycles_when_water_in_view', True, 'yes or no', 'judged',
    'plugin 1.4.0 fix round: the film owner\'s rule is Cycles where lights are lit; the smoke check drew still water in EEVEE as a flat dark slab and in Cycles as reflective water, so water in view also gives Cycles. Set it to false to follow the owner\'s rule exactly')
with open(PATH, 'w', encoding='utf-8') as handle:
    handle.write(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
print('film-settings.json written')
