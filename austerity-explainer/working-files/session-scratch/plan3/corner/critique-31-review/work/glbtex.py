import json, struct, sys, io
import numpy as np, cv2
def chunks(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20+n])
    off = 20 + n
    m = struct.unpack('<I', b[off:off+4])[0]
    binc = b[off+8:off+8+m]
    return g, binc
path, matname = sys.argv[1], sys.argv[2]
g, binc = chunks(path)
for m in g['materials']:
    if m['name'] != matname: continue
    pbr = m.get('pbrMetallicRoughness', {})
    ti = pbr['baseColorTexture']['index']
    src = g['textures'][ti]['source']
    img = g['images'][src]
    bv = g['bufferViews'][img['bufferView']]
    data = binc[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
    a = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    print(matname, img.get('mimeType'), a.shape)
    if a.ndim == 3 and a.shape[2] == 4:
        al = a[..., 3] / 255.0
        print(' alpha mean %.3f min %.3f max %.3f p10 %.3f p90 %.3f' % (al.mean(), al.min(), al.max(), np.percentile(al, 10), np.percentile(al, 90)))
    rgb = a[..., :3][..., ::-1].reshape(-1, 3).mean(0)
    print(' rgb mean', rgb.round(1))
