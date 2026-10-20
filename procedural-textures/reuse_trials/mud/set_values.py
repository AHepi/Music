# What this does (plain words): changes some values in settings.json from the command line, keeping the file tidy (one value per name, sorted by
# layer). Use: python3 -I set_values.py 'JSON {setting: value}'   (a value of null removes a setting). Prints what it changed.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, 'settings.json')
settings = json.load(open(path))
changes = json.loads(sys.argv[1])
for key, value in changes.items():
    old = settings.get(key, '(not set)')
    if value is None:
        settings.pop(key, None)
    else:
        settings[key] = value
    print(f'{key}: {old} -> {value}')
order = ['mud_layout', 'colour_and_fade', 'ruts', 'moss', 'damage', 'outline_and_shadow', 'combine', 'mud_height_rule', 'recipe']
settings = dict(sorted(settings.items(), key=lambda kv: (order.index(kv[0].split('.')[0]) if kv[0].split('.')[0] in order else 99, kv[0])))
with open(path, 'w') as handle:
    handle.write('{\n' + ',\n'.join(f' {json.dumps(k)}: {json.dumps(v)}' for k, v in settings.items()) + '\n}\n')
