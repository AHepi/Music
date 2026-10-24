"""What this does (scratch, round 5 W4 helper): lists the object (node) names and material names in each .glb of a
folder, read straight from the files' JSON part, so two exports can be compared by name.
Use: python3 glb_names.py FOLDER OUT.json"""
import json
import os
import struct
import sys

folder, out = sys.argv[1], sys.argv[2]
found = {}
for name in sorted(os.listdir(folder)):
    if not name.endswith('.glb'):
        continue
    with open(os.path.join(folder, name), 'rb') as handle:
        handle.read(12)
        length, kind = struct.unpack('<II', handle.read(8))
        data = json.loads(handle.read(length))
    found[name] = {'nodes': sorted(n.get('name', '') for n in data.get('nodes', [])),
                   'materials': sorted(m.get('name', '') for m in data.get('materials', []))}
json.dump(found, open(out, 'w'), indent=1)
print({k: len(v['nodes']) for k, v in found.items()})
