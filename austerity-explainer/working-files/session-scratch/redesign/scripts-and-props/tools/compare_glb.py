# What this does: compares two .glb files part by part (the scene description, then each block of
# data: mesh points, texture pictures), and says which parts differ and by how much.
# Run: python3 -I compare_glb.py FIRST.glb SECOND.glb
import json
import struct
import sys

import numpy as np


def read_glb(path):
    data = open(path, 'rb').read()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    offset = 12
    chunks = {}
    while offset < length:
        chunk_length, chunk_type = struct.unpack_from('<I4s', data, offset)
        chunks[chunk_type] = data[offset + 8: offset + 8 + chunk_length]
        offset += 8 + chunk_length
    return json.loads(chunks[b'JSON'].rstrip(b' \0').decode()), chunks.get(b'BIN\0', b'')


first_description, first_binary = read_glb(sys.argv[1])
second_description, second_binary = read_glb(sys.argv[2])
for key in sorted(set(first_description) | set(second_description)):
    same = first_description.get(key) == second_description.get(key)
    count = len(first_description.get(key, [])) if isinstance(first_description.get(key), list) else ''
    print(f'{key:12s} {count!s:>6} {"same" if same else "DIFFERENT"}')
names_first = sorted(node['name'] for node in first_description['nodes'])
names_second = sorted(node['name'] for node in second_description['nodes'])
print('object names the same:', names_first == names_second, len(names_first), len(names_second))
# which buffer views differ, and what uses them
users = {}
for accessor_index, accessor in enumerate(first_description.get('accessors', [])):
    users.setdefault(accessor.get('bufferView'), []).append(('accessor', accessor_index, accessor['componentType'], accessor['type']))
for image_index, image in enumerate(first_description.get('images', [])):
    users.setdefault(image.get('bufferView'), []).append(('image', image.get('name')))
different = []
largest_difference = 0.0
for index, (view_first, view_second) in enumerate(zip(first_description['bufferViews'], second_description['bufferViews'])):
    a = first_binary[view_first.get('byteOffset', 0): view_first.get('byteOffset', 0) + view_first['byteLength']]
    b = second_binary[view_second.get('byteOffset', 0): view_second.get('byteOffset', 0) + view_second['byteLength']]
    if a != b:
        what = users.get(index, [])
        difference = None
        if len(a) == len(b) and what and what[0][0] == 'accessor' and what[0][2] == 5126:
            difference = float(np.max(np.abs(np.frombuffer(a, np.float32) - np.frombuffer(b, np.float32))))
            largest_difference = max(largest_difference, difference)
        different.append((index, len(a), len(b), what[:1], difference))
print('data blocks:', len(first_description['bufferViews']), 'different:', len(different))
for row in different[:20]:
    print('  ', row)
print('largest difference in any number:', largest_difference)
