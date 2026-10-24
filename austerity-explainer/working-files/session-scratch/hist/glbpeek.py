import json, struct, sys
import numpy as np
def load(path):
    b = open(path,'rb').read()
    l = struct.unpack('<I', b[12:16])[0]
    js = json.loads(b[20:20+l])
    off = 20+l
    l2 = struct.unpack('<I', b[off:off+4])[0]
    binc = b[off+8:off+8+l2]
    return js, binc
def acc(js, binc, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    start = bv.get('byteOffset',0)+a.get('byteOffset',0)
    n = a['count']; comp = {'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
    dt = {5126:np.float32,5123:np.uint16,5125:np.uint32}[a['componentType']]
    stride = bv.get('byteStride', 0)
    if stride and stride != comp*np.dtype(dt).itemsize:
        raw = np.frombuffer(binc, dtype=np.uint8, count=stride*n, offset=start).reshape(n, stride)
        return raw[:, :comp*np.dtype(dt).itemsize].copy().view(dt).reshape(n, comp)
    return np.frombuffer(binc, dtype=dt, count=n*comp, offset=start).reshape(n, comp)

def quat_mat(q):
    x,y,z,w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],[2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],[2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def node_mat(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4,4).T
    M = np.eye(4)
    if 'scale' in n: M = np.diag(list(n['scale'])+[1]) @ M
    if 'rotation' in n: 
        r = np.eye(4); r[:3,:3] = quat_mat(n['rotation']); M = r @ M
    if 'translation' in n:
        t = np.eye(4); t[:3,3] = n['translation']; M = t @ M
    return M
js, binc = load(sys.argv[1])
pts = []
def walk(i, M):
    n = js['nodes'][i]; M2 = M @ node_mat(n)
    if 'mesh' in n:
        for p in js['meshes'][n['mesh']]['primitives']:
            v = acc(js, binc, p['attributes']['POSITION'])
            vv = (M2 @ np.c_[v, np.ones(len(v))].T).T[:, :3]
            pts.append((n.get('name'), vv))
    for c in n.get('children', []): walk(c, M2)
for r in js['scenes'][js.get('scene',0)]['nodes']: walk(r, np.eye(4))
allp = np.vstack([p for _, p in pts])
# glTF is y-up, -z forward; Blender import: x->x, y(gltf)->z, z(gltf)-> -y
bx = allp[:,0]; by = -allp[:,2]; bz = allp[:,1]
print('bounds x', bx.min(), bx.max(), ' y', by.min(), by.max(), ' z', bz.min(), bz.max())
hi = bz > bz.min() + 0.75*(bz.max()-bz.min())
print('top quarter (back) mean x,y:', bx[hi].mean(), by[hi].mean(), ' all mean', bx.mean(), by.mean())
for name, p in pts:
    print(name, len(p))
