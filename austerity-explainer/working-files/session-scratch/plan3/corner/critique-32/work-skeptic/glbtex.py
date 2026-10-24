import json, struct, sys, io
from PIL import Image
import numpy as np
p = sys.argv[1]
b = open(p,'rb').read()
n = struct.unpack('<I', b[12:16])[0]
g = json.loads(b[20:20+n])
binstart = 20+n
# bin chunk header
bl = struct.unpack('<I', b[binstart:binstart+4])[0]
bin_ = b[binstart+8:binstart+8+bl]
for i,m in enumerate(g['materials']):
    pbr = m.get('pbrMetallicRoughness', {})
    print(m['name'], {k:v for k,v in pbr.items()}, m.get('alphaCutoff'))
    if 'baseColorTexture' in pbr:
        t = g['textures'][pbr['baseColorTexture']['index']]
        im = g['images'][t['source']]
        bv = g['bufferViews'][im['bufferView']]
        data = bin_[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
        img = Image.open(io.BytesIO(data))
        print('  image', img.mode, img.size)
        a = np.asarray(img.convert('RGBA')).astype(float)/255
        print('  alpha min/mean/max', a[...,3].min(), a[...,3].mean().round(3), a[...,3].max(), ' rgb mean', a[...,:3].mean(axis=(0,1)).round(3))
