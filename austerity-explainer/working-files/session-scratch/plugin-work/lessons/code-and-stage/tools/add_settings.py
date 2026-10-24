"""What this does: adds or replaces entries in a JSON settings file, keeping its exact layout (indent 1).
Use: python3 add_settings.py FILE ENTRIES.json   where ENTRIES.json is [{"section": "a.b", "key": "k", "entry": {...}, "after": "other"}]"""
import json, sys
path, entries = sys.argv[1], json.load(open(sys.argv[2]))
data = json.load(open(path))
for e in entries:
    node = data
    for part in e['section'].split('.'):
        node = node[part]
    items = list(node.items())
    items = [(k, v) for k, v in items if k != e['key']]
    position = len(items)
    if e.get('after'):
        position = [k for k, _ in items].index(e['after']) + 1
    items.insert(position, (e['key'], e['entry']))
    node.clear()
    node.update(items)
with open(path, 'w') as handle:
    handle.write(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
print('added', len(entries))
