import json, struct, sys
def read(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    return json.loads(b[20:20+n])
for p in sys.argv[1:]:
    g = read(p)
    print('==', p.split('/')[-1])
    print(' nodes:', [n.get('name') for n in g.get('nodes', [])])
    for m in g.get('materials', []):
        pbr = m.get('pbrMetallicRoughness', {})
        print('  mat', m.get('name'), 'alpha', m.get('alphaMode'), 'base', pbr.get('baseColorFactor'), 'tex', 'baseColorTexture' in pbr, 'ext', list(m.get('extensions', {}).keys()), 'emis', m.get('emissiveFactor'))
