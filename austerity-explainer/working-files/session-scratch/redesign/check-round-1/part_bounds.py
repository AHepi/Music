# What this does: prints each mesh node's placed bounds (glTF y up) for a .glb, from its accessors' min and max,
# to check heights such as where a nail sits on a hung jacket.
import json, struct, sys
import numpy as np
data = open(sys.argv[1], 'rb').read(); length = struct.unpack('<I', data[12:16])[0]; gltf = json.loads(data[20:20 + length])
def matrix(node):
    m = np.eye(4)
    if 'matrix' in node: return np.array(node['matrix']).reshape(4, 4).T
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    r = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    m[:3, :3] = r * np.array(node.get('scale', [1, 1, 1])); m[:3, 3] = node.get('translation', [0, 0, 0]); return m
def walk(index, parent):
    node = gltf['nodes'][index]; m = parent @ matrix(node)
    if 'mesh' in node:
        lows, highs = [], []
        for p in gltf['meshes'][node['mesh']]['primitives']:
            a = gltf['accessors'][p['attributes']['POSITION']]
            corners = np.array([[x, y, z, 1] for x in (a['min'][0], a['max'][0]) for y in (a['min'][1], a['max'][1]) for z in (a['min'][2], a['max'][2])])
            placed = (m @ corners.T).T[:, :3]; lows.append(placed.min(0)); highs.append(placed.max(0))
        print(f"{node.get('name'):12s} low {np.round(np.min(lows, 0), 3)} high {np.round(np.max(highs, 0), 3)}")
    for child in node.get('children', []): walk(child, m)
for root in gltf['scenes'][0]['nodes']: walk(root, np.eye(4))
