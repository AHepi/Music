"""What this does: lists the object (node) names and material names inside each .glb file given, so the names the
Works pages read can be checked against the export. Use: python3 -I glb_names.py FILE.glb ... (prints JSON)"""
import json
import struct
import sys

out = {}
for path in sys.argv[1:]:
    with open(path, 'rb') as f:
        magic, version, length = struct.unpack('<4sII', f.read(12))
        chunk_length, chunk_type = struct.unpack('<I4s', f.read(8))
        doc = json.loads(f.read(chunk_length))
    out[path.split('/')[-1]] = {'nodes': [n.get('name', '') for n in doc.get('nodes', [])],
                                'materials': [m.get('name', '') for m in doc.get('materials', [])]}
print(json.dumps(out))
