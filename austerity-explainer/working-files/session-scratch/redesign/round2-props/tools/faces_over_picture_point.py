# What this does: finds the triangles of a .glb whose texture coordinates cover a point of its picture
# (u across from the left, v down from the top, as glTF counts them), and says where they are on the model.
# Run: python3 -I faces_over_picture_point.py PROP.glb U V
import json
import struct
import sys

import numpy as np

path, u, v = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
data = open(path, 'rb').read()
length = struct.unpack('<I', data[12:16])[0]
gltf = json.loads(data[20:20 + length])
start = 20 + length + 8


def read(number):
    item = gltf['accessors'][number]
    view = gltf['bufferViews'][item['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[item['type']]
    kind = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[item['componentType']]
    offset = start + view.get('byteOffset', 0) + item.get('byteOffset', 0)
    return np.frombuffer(data, kind, item['count'] * width, offset).reshape(item['count'], width)


for mesh in gltf['meshes']:
    for primitive in mesh['primitives']:
        uv = read(primitive['attributes']['TEXCOORD_0']).astype(np.float64)
        uv = uv - np.floor(uv)          # wrapped coordinates
        points = read(primitive['attributes']['POSITION'])
        triangles = read(primitive['indices']).reshape(-1, 3)
        a, b, c = uv[triangles[:, 0]], uv[triangles[:, 1]], uv[triangles[:, 2]]
        def side(p, q, r):
            return (q[:, 0] - p[:, 0]) * (r[1] - p[:, 1]) - (q[:, 1] - p[:, 1]) * (r[0] - p[:, 0])
        target = np.array([u, v])
        s1, s2, s3 = side(a, b, target), side(b, c, target), side(c, a, target)
        inside = ((s1 >= 0) & (s2 >= 0) & (s3 >= 0)) | ((s1 <= 0) & (s2 <= 0) & (s3 <= 0))
        for index in np.nonzero(inside)[0]:
            corners = points[triangles[index]]
            print(mesh.get('name'), 'triangle', index, 'at (glTF x, up, z):', corners.mean(0).round(3), 'spanning', (corners.max(0) - corners.min(0)).round(3))
