# What this does (scratch check): prints a fingerprint of the geometry in each .glb given (every vertex position,
# rounded to 0.1 mm, sorted), so two builds can be compared regardless of the order glTF writes parts in.
import hashlib
import json
import struct
import sys

import numpy

for path in sys.argv[1:]:
    data = open(path, 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    document = json.loads(data[20:20 + length])
    binary = data[20 + length + 8:]
    points = []
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            accessor = document['accessors'][primitive['attributes']['POSITION']]
            view = document['bufferViews'][accessor['bufferView']]
            start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
            array = numpy.frombuffer(binary, numpy.float32, accessor['count'] * 3, start).reshape(-1, 3)
            points.append(array)
    every = numpy.round(numpy.concatenate(points) * 10000).astype(numpy.int64)
    every = every[numpy.lexsort(every.T[::-1])]
    print(path.split('/')[-1], len(every), hashlib.sha1(every.tobytes()).hexdigest()[:16])
