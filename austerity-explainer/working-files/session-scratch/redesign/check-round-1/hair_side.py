# What this does: for each figure .glb (one body mesh, a primitive per material), compares where the
# hair sits with where the head's skin sits, along the way the figure faces (-z in glTF: its face).
import json, struct, sys, os
import numpy as np
folder = sys.argv[1]
for name in sorted(os.listdir(folder)):
    if not name.endswith('.glb'): continue
    data = open(os.path.join(folder, name), 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length]); binary_start = 20 + length + 8
    def positions(index):
        accessor = gltf['accessors'][index]; view = gltf['bufferViews'][accessor['bufferView']]
        start = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return np.frombuffer(data, dtype=np.float32, count=accessor['count'] * 3, offset=start).reshape(-1, 3)
    by_material = {}
    for mesh in gltf['meshes']:
        for primitive in mesh['primitives']:
            material = gltf['materials'][primitive['material']]['name'] if 'material' in primitive else '?'
            by_material.setdefault(material, []).append(positions(primitive['attributes']['POSITION']))
    by_material = {k: np.concatenate(v) for k, v in by_material.items()}
    skin = by_material.get('weathered skin'); hair = by_material.get('dark hair')
    top = max(v[:, 1].max() for v in by_material.values())
    if skin is None: print(name, list(by_material)); continue
    head_skin = skin[skin[:, 1] > top - 0.32]
    line = f'{name:32s} materials {sorted(by_material)}'
    if hair is not None:
        line += f'\n    head skin centre z {head_skin[:, 2].mean():+.3f}  hair centre z {hair[:, 2].mean():+.3f}  (face is toward -z: hair should have the larger z)'
        line += f'  hair y range {hair[:, 1].min():.2f}-{hair[:, 1].max():.2f}, head skin y {head_skin[:, 1].min():.2f}-{head_skin[:, 1].max():.2f}'
    print(line)
