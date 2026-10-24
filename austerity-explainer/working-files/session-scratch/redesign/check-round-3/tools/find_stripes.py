# What this does: reads a .glb and lists the parts whose faces have picture coordinates squashed to a line
# (a surface that shows as fine stripes instead of brick or stone), with how much area is affected.
import json, struct, sys
import numpy as np
TYPES = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
SIZES = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def load(path):
    data = open(path, 'rb').read()
    jlen = struct.unpack('<I', data[12:16])[0]
    js = json.loads(data[20:20 + jlen])
    binstart = 20 + jlen + 8
    return js, data[binstart:]
def acc(js, binb, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    n = SIZES[a['type']]; dt = TYPES[a['componentType']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride')
    itemsize = np.dtype(dt).itemsize * n
    if stride and stride != itemsize:
        raw = np.frombuffer(binb, dtype=np.uint8, count=stride * a['count'], offset=off).reshape(a['count'], stride)[:, :itemsize]
        return np.frombuffer(raw.tobytes(), dtype=dt).reshape(a['count'], n)
    return np.frombuffer(binb, dtype=dt, count=n * a['count'], offset=off).reshape(a['count'], n)
for path in sys.argv[1:]:
    js, binb = load(path)
    mats = js.get('materials', [])
    meshnames = {}
    for node in js.get('nodes', []):
        if 'mesh' in node: meshnames.setdefault(node['mesh'], node.get('name'))
    report = []
    for mi, mesh in enumerate(js.get('meshes', [])):
        for prim in mesh['primitives']:
            at = prim['attributes']
            if 'TEXCOORD_0' not in at: continue
            P = acc(js, binb, at['POSITION']).astype(np.float64); U = acc(js, binb, at['TEXCOORD_0']).astype(np.float64)
            I = acc(js, binb, prim['indices']).reshape(-1, 3).astype(np.int64) if 'indices' in prim else np.arange(len(P)).reshape(-1, 3)
            a, b, c = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
            area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
            ua, ub, uc = U[I[:, 0]], U[I[:, 1]], U[I[:, 2]]
            uarea = 0.5 * np.abs((ub[:, 0] - ua[:, 0]) * (uc[:, 1] - ua[:, 1]) - (uc[:, 0] - ua[:, 0]) * (ub[:, 1] - ua[:, 1]))
            ok = area > 1e-6
            if ok.sum() == 0: continue
            r = uarea[ok] / area[ok]
            med = np.median(r)
            bad = r < 0.02 * max(med, 1e-9)
            badarea = area[ok][bad].sum(); tot = area[ok].sum()
            mname = mats[prim['material']]['name'] if 'material' in prim and prim['material'] < len(mats) else '?'
            if badarea > 0.5:
                report.append((badarea, tot, meshnames.get(mi, mesh.get('name')), mname))
    report.sort(reverse=True)
    print('==', path.split('/')[-1], 'parts with squashed picture coordinates:', len(report))
    for badarea, tot, name, m in report[:25]:
        print('   %-40s %-32s %7.1f of %7.1f (model units squared)' % (name, m, badarea, tot))
