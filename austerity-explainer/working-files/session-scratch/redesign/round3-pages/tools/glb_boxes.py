"""What this does: reads a .glb's scene tree (no extra libraries) and prints, for every object whose name matches a
word, where its box is in the world (glTF space: y up; Blender (x, y, z) is glTF (x, z, -y)), so a spot on the film's
frame can be worked out from the real set. Use: python3 -I glb_boxes.py FILE.glb WORD [WORD ...]
"""
import json
import struct
import sys

import numpy as np

path, words = sys.argv[1], sys.argv[2:]
with open(path, 'rb') as handle:
    data = handle.read()
length = struct.unpack_from('<I', data, 12)[0]
gltf = json.loads(data[20:20 + length])


def matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix']).reshape(4, 4).T
    t = np.array(node.get('translation', [0, 0, 0]))
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    s = np.array(node.get('scale', [1, 1, 1]))
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    m = np.eye(4)
    m[:3, :3] = r * s
    m[:3, 3] = t
    return m


rows = []


def walk(index, parent, inherited_name):
    node = gltf['nodes'][index]
    world = parent @ matrix(node)
    name = node.get('name', '')
    label = name or inherited_name
    if 'mesh' in node:
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            accessor = gltf['accessors'][primitive['attributes']['POSITION']]
            lo, hi = np.array(accessor['min']), np.array(accessor['max'])
            corners = np.array([[a, b, c, 1] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
            moved = (world @ corners.T).T[:, :3]
            rows.append((label, inherited_name, moved.min(axis=0), moved.max(axis=0)))
    for child in node.get('children', []):
        walk(child, world, name if any(w in name for w in words) else inherited_name)


for scene in gltf['scenes']:
    for index in scene['nodes']:
        walk(index, np.eye(4), '')
for label, group, lo, hi in rows:
    if any(w in label for w in words) or any(w in group for w in words):
        blender_lo = (lo[0], -hi[2], lo[1]); blender_hi = (hi[0], -lo[2], hi[1])
        print(f'{group or "-"} | {label} | Blender from {tuple(round(v, 2) for v in blender_lo)} to {tuple(round(v, 2) for v in blender_hi)}')
