# What this does (plain words): a tiny helper for hand-tuning. It changes named settings in settings.json in place (keeping the file's layout and its
# notes), and adds a setting after a named one if it is not there yet. Use: python3 -I set_settings.py '{"layer.setting": value, ...}' [after_key]
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, 'settings.json')
text = open(path).read()
changes = json.loads(sys.argv[1])
anchor = sys.argv[2] if len(sys.argv) > 2 else None
for key, value in changes.items():
    pattern = re.compile(r'("%s":\s*)("[^"]*"|[-0-9.eE]+)' % re.escape(key))
    if pattern.search(text):
        text = pattern.sub(lambda m: m.group(1) + json.dumps(value), text, count=1)
    else:
        if not anchor:
            raise KeyError(f'{key} is not in settings.json; give a setting to add it after')
        anchor_pattern = re.compile(r'("%s":\s*("[^"]*"|[-0-9.eE]+))' % re.escape(anchor))
        text = anchor_pattern.sub(lambda m: m.group(1) + ', ' + json.dumps(key) + ': ' + json.dumps(value), text, count=1)
        anchor = key
json.loads(text)
open(path, 'w').write(text)
print('changed', len(changes), 'settings')
