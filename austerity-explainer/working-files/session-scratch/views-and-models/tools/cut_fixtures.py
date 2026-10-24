"""Scratch (views-and-models helper): cuts small fixtures for the plugin's tests from the project's own model files:
  - one part (a node's mesh: positions, texture coordinates, triangles, material names) of a .glb into a small .glb
    (No. 2's chimney a from the round 3 and round 4 factory files: the striped and the mended geometry)
  - the node names and roots of several .glb files into JSON (round 1's props, eight with 'name.001' roots)
Use: python3 cut_fixtures.py part SOURCE.glb NODE_NAME OUT.glb
     python3 cut_fixtures.py names OUT.json FILE.glb ...
"""
import json
import os
import struct
import sys

sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/paper-film/blender')
import model_lint  # noqa: E402
import numpy as np  # noqa: E402


def write_glb(path, nodes, meshes, accessors_data, materials):
    """nodes: glTF node dicts; meshes: glTF mesh dicts whose accessor fields index into accessors_data (arrays)."""
    binary = b''
    views, accessors = [], []
    for array, kind in accessors_data:
        data = np.ascontiguousarray(array)
        while len(binary) % 4:
            binary += b'\0'
        offset = len(binary)
        binary += data.tobytes()
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': data.nbytes})
        component = {np.dtype(np.float32): 5126, np.dtype(np.uint32): 5125}[data.dtype]
        accessor = {'bufferView': len(views) - 1, 'componentType': component, 'count': int(data.shape[0]), 'type': kind}
        if kind == 'VEC3':
            accessor['min'] = data.min(axis=0).tolist()
            accessor['max'] = data.max(axis=0).tolist()
        accessors.append(accessor)
    while len(binary) % 4:
        binary += b'\0'
    gltf = {'asset': {'version': '2.0', 'generator': 'cut_fixtures.py (views-and-models helper)'}, 'scene': 0,
            'scenes': [{'nodes': [i for i, n in enumerate(nodes) if not any(i in m.get('children', []) for m in nodes)]}],
            'nodes': nodes, 'meshes': meshes, 'materials': materials, 'accessors': accessors, 'bufferViews': views,
            'buffers': [{'byteLength': len(binary)}]}
    text = json.dumps(gltf).encode()
    while len(text) % 4:
        text += b' '
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(text) + 8 + len(binary)))
        handle.write(struct.pack('<II', len(text), 0x4E4F534A) + text)
        handle.write(struct.pack('<II', len(binary), 0x004E4942) + binary)


def cut_part(source, node_name, out):
    gltf, binary = model_lint.read_glb(source)
    nodes = gltf['nodes']
    index = next(i for i, n in enumerate(nodes) if n.get('name') == node_name)
    # its world matrix (parents included), kept as the new node's matrix
    parent_of = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
    chain, i = [], index
    while i is not None:
        chain.append(i)
        i = parent_of.get(i)
    world = np.eye(4)
    for i in reversed(chain):
        world = world @ model_lint.node_matrix(nodes[i])
    mesh = gltf['meshes'][nodes[index]['mesh']]
    data, primitives, materials = [], [], []
    for primitive in mesh['primitives']:
        attributes = primitive['attributes']
        positions = model_lint.read_accessor(gltf, binary, attributes['POSITION']).astype(np.float32)
        uvs = model_lint.read_accessor(gltf, binary, attributes['TEXCOORD_0']).astype(np.float32)
        indices = model_lint.read_accessor(gltf, binary, primitive['indices']).astype(np.uint32).reshape(-1)
        data += [(positions, 'VEC3'), (uvs, 'VEC2'), (indices, 'SCALAR')]
        name = gltf['materials'][primitive['material']]['name']
        materials.append({'name': name})
        primitives.append({'attributes': {'POSITION': len(data) - 3, 'TEXCOORD_0': len(data) - 2}, 'indices': len(data) - 1,
                           'material': len(materials) - 1})
    node = {'name': node_name, 'mesh': 0, 'matrix': world.T.reshape(-1).tolist()}
    write_glb(out, [node], [{'name': mesh.get('name', node_name), 'primitives': primitives}], data, materials)
    print('cut', node_name, 'from', source, '->', out, os.path.getsize(out), 'bytes')


def names(out, files):
    found = {}
    for path in files:
        gltf, _ = model_lint.read_glb(path)
        nodes = gltf.get('nodes', [])
        scene = gltf['scenes'][gltf.get('scene', 0)]
        found[os.path.basename(path)] = {'roots': [nodes[i].get('name') for i in scene['nodes']],
                                         'nodes': [{'name': n.get('name'), 'children': n.get('children', [])} for n in nodes]}
    with open(out, 'w') as handle:
        json.dump(found, handle, indent=1)
    print('wrote', out)


if __name__ == '__main__':
    if sys.argv[1] == 'part':
        cut_part(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        names(sys.argv[2], sys.argv[3:])
