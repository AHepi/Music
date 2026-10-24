# What this does: reads .glb files directly (no Blender) and prints, for each, its root nodes, any
# repeated or ".001" node names, any node named like the file but not the root, the overall size
# (from the mesh positions' min/max and the node transforms), the number of pictures, and the file size.
import json, struct, sys, os, re
import numpy

def read_glb(path):
    data = open(path, 'rb').read()
    magic, version, length = struct.unpack_from('<III', data, 0)
    offset = 12
    document, binary = None, None
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8: offset + 8 + chunk_length]
        if chunk_type == 0x4E4F534A:
            document = json.loads(chunk)
        else:
            binary = chunk
        offset += 8 + chunk_length
    return document, binary

def matrix_of(node):
    if 'matrix' in node:
        return numpy.array(node['matrix']).reshape(4, 4).T
    translation = numpy.array(node.get('translation', [0, 0, 0]))
    rotation = node.get('rotation', [0, 0, 0, 1])
    scale = numpy.array(node.get('scale', [1, 1, 1]))
    x, y, z, w = rotation
    turn = numpy.array([[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
                        [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
                        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]])
    result = numpy.eye(4)
    result[:3, :3] = turn * scale
    result[:3, 3] = translation
    return result

def positions(document, binary, accessor_index):
    accessor = document['accessors'][accessor_index]
    view = document['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    count = accessor['count']
    stride = view.get('byteStride', 12)
    raw = numpy.frombuffer(binary, dtype=numpy.uint8, count=stride * (count - 1) + 12, offset=start)
    out = numpy.lib.stride_tricks.as_strided(raw, shape=(count, 12), strides=(stride, 1)).copy()
    return out.view(numpy.float32).reshape(count, 3)

def facts(path):
    document, binary = read_glb(path)
    nodes = document.get('nodes', [])
    scene = document['scenes'][document.get('scene', 0)]
    roots = [nodes[i].get('name') for i in scene['nodes']]
    names = [n.get('name', '') for n in nodes]
    repeated = sorted({n for n in names if names.count(n) > 1})
    numbered = [n for n in names if re.search(r'\.\d{3}$', n)]
    stem = os.path.splitext(os.path.basename(path))[0]
    stem_not_root = [i for i, n in enumerate(names) if n == stem and i not in scene['nodes']]
    low = numpy.full(3, numpy.inf); high = numpy.full(3, -numpy.inf)
    def walk(index, parent):
        node = nodes[index]
        world = parent @ matrix_of(node)
        if 'mesh' in node:
            for primitive in document['meshes'][node['mesh']]['primitives']:
                points = positions(document, binary, primitive['attributes']['POSITION'])
                points = points @ world[:3, :3].T + world[:3, 3]
                low[:] = numpy.minimum(low, points.min(0)); high[:] = numpy.maximum(high, points.max(0))
        for child in node.get('children', []):
            walk(child, world)
    for root in scene['nodes']:
        walk(root, numpy.eye(4))
    size = high - low   # glTF is y-up: x width, y height, z depth
    return {'file': os.path.basename(path), 'megabytes': round(os.path.getsize(path) / 1e6, 2), 'roots': roots,
            'repeated_names': repeated[:10], 'numbered_names': numbered[:10], 'file_name_on_a_child': len(stem_not_root),
            'nodes': len(nodes), 'pictures': len(document.get('images', [])),
            'size_x_y_z': [round(float(v), 3) for v in size], 'low': [round(float(v), 3) for v in low],
            'high': [round(float(v), 3) for v in high],
            'node_names': names if '--names' in sys.argv else None,
            'extras': {n.get('name'): n.get('extras') for n in nodes if n.get('extras')} if '--extras' in sys.argv else None}

for path in sys.argv[1:]:
    if path.startswith('--'):
        continue
    print(json.dumps({k: v for k, v in facts(path).items() if v is not None}))
