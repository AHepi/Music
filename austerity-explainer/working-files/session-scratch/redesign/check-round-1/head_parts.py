# What this does: for each figure .glb in a folder, finds its head, nose and hair pieces and says which
# way the face points and whether the hair sits on the back of the head (opposite the nose) or not.
import json, struct, sys, os
import numpy as np
folder = sys.argv[1]
def load(path):
    data = open(path, 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    return data, gltf, 20 + length + 8
def accessor_array(data, gltf, binary_start, index):
    accessor = gltf['accessors'][index]
    view = gltf['bufferViews'][accessor['bufferView']]
    sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    start = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return np.frombuffer(data, dtype=np.float32, count=accessor['count'] * sizes, offset=start).reshape(-1, sizes)
def quaternion_matrix(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
for name in sorted(os.listdir(folder)):
    if not name.endswith('.glb'): continue
    data, gltf, binary_start = load(os.path.join(folder, name))
    world = {}
    def walk(index, parent):
        node = gltf['nodes'][index]
        m = np.eye(4)
        if 'matrix' in node: m = np.array(node['matrix']).reshape(4, 4).T
        else:
            r = quaternion_matrix(node.get('rotation', [0, 0, 0, 1])) * np.array(node.get('scale', [1, 1, 1]))
            m[:3, :3] = r; m[:3, 3] = node.get('translation', [0, 0, 0])
        m = parent @ m
        if 'mesh' in node:
            positions = np.concatenate([accessor_array(data, gltf, binary_start, p['attributes']['POSITION']) for p in gltf['meshes'][node['mesh']]['primitives']])
            world[node.get('name', '')] = (m[:3, :3] @ positions.T).T + m[:3, 3]
        for child in node.get('children', []): walk(child, m)
    for root in gltf['scenes'][0]['nodes']: walk(root, np.eye(4))
    pieces = {k: v.mean(0) for k, v in world.items()}
    head = [k for k in pieces if k.endswith('-head')]
    nose = [k for k in pieces if k.endswith('-nose')]
    hair = [k for k in pieces if k.endswith('-hair')]
    if not head: print(name, 'no head piece; names:', list(pieces)[:12]); continue
    h = pieces[head[0]]
    facing = (pieces[nose[0]] - h) if nose else None
    line = f'{name:34s} nose dir {np.round(facing / np.linalg.norm(facing), 2) if facing is not None else None}'
    if hair:
        hair_offset = pieces[hair[0]] - h
        line += f'  hair centre offset {np.round(hair_offset, 3)}  hair-vs-nose dot {np.dot(hair_offset, facing):.5f}'
        hp = world[hair[0]] - h
        along = hp @ (facing / np.linalg.norm(facing))
        line += f'  hair points: front {int((along > 0.03).sum())} back {int((along < -0.03).sum())}'
    print(line)
