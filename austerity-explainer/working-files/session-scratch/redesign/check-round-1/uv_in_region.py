# What this does: counts the triangles of a .glb whose texture coordinates fall inside a box of its
# picture (to see whether a picture's corner, such as a maker's label, shows on the model).
import json, struct, sys
import numpy as np
path = sys.argv[1]
u0, v0, u1, v1 = map(float, sys.argv[2:6])
data = open(path, 'rb').read()
length = struct.unpack('<I', data[12:16])[0]
gltf = json.loads(data[20:20 + length])
binary_start = 20 + length + 8
def read_accessor(index):
    accessor = gltf['accessors'][index]
    view = gltf['bufferViews'][accessor['bufferView']]
    count = accessor['count']
    sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    dtype = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[accessor['componentType']]
    start = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride')
    item = np.dtype(dtype).itemsize * sizes
    if stride and stride != item:
        raw = np.frombuffer(data, dtype=np.uint8, count=stride * count, offset=start).reshape(count, stride)[:, :item]
        return np.frombuffer(raw.tobytes(), dtype=dtype).reshape(count, sizes)
    return np.frombuffer(data, dtype=dtype, count=count * sizes, offset=start).reshape(count, sizes)
for mesh in gltf['meshes']:
    for primitive in mesh['primitives']:
        if 'TEXCOORD_0' not in primitive['attributes']:
            continue
        uv = read_accessor(primitive['attributes']['TEXCOORD_0'])
        positions = read_accessor(primitive['attributes']['POSITION'])
        inside = (uv[:, 0] >= u0) & (uv[:, 0] <= u1) & (uv[:, 1] >= v0) & (uv[:, 1] <= v1)
        if inside.any():
            print(mesh.get('name'), 'vertices inside:', int(inside.sum()), 'of', len(uv), 'positions:', positions[inside].min(0), positions[inside].max(0))
