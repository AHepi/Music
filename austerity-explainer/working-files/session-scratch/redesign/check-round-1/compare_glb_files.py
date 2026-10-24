# What this does: compares two .glb files: node names, mesh and picture counts, every accessor's numbers
# (largest difference per kind of data) and every picture's bytes.
import json, struct, sys
import numpy as np
def load(path):
    data = open(path, 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    return data, json.loads(data[20:20 + length]), 20 + length + 8
def accessor(data, gltf, start_of_binary, index):
    a = gltf['accessors'][index]; view = gltf['bufferViews'][a['bufferView']]
    sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    dtype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    start = start_of_binary + view.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(data, dtype=dtype, count=a['count'] * sizes, offset=start)
(da, ga, sa), (db, gb, sb) = load(sys.argv[1]), load(sys.argv[2])
print('nodes', len(ga['nodes']), len(gb['nodes']), 'same names in order:', [n.get('name') for n in ga['nodes']] == [n.get('name') for n in gb['nodes']])
for key in ('meshes', 'materials', 'images', 'accessors', 'textures'):
    print(key, len(ga.get(key, [])), len(gb.get(key, [])))
same_nodes = all(json.dumps({k: v for k, v in x.items()}, sort_keys=True) == json.dumps({k: v for k, v in y.items()}, sort_keys=True) for x, y in zip(ga['nodes'], gb['nodes']))
print('node transforms identical:', same_nodes)
largest = {}
for i in range(min(len(ga['accessors']), len(gb['accessors']))):
    x = accessor(da, ga, sa, i).astype(float); y = accessor(db, gb, sb, i).astype(float)
    kind = ga['accessors'][i]['type'] + str(ga['accessors'][i]['componentType'])
    d = np.abs(x - y).max() if x.shape == y.shape else float('inf')
    largest[kind] = max(largest.get(kind, 0), d)
print('largest difference by kind:', largest)
images_same = 0
for i, (x, y) in enumerate(zip(ga.get('images', []), gb.get('images', []))):
    vx, vy = ga['bufferViews'][x['bufferView']], gb['bufferViews'][y['bufferView']]
    bx = da[sa + vx.get('byteOffset', 0): sa + vx.get('byteOffset', 0) + vx['byteLength']]
    by = db[sb + vy.get('byteOffset', 0): sb + vy.get('byteOffset', 0) + vy['byteLength']]
    images_same += bx == by
print('pictures identical:', images_same, 'of', len(ga.get('images', [])))
