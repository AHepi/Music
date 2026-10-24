import json, struct, sys
def load(path):
    b = open(path,'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    return json.loads(b[20:20+n])
for p in sys.argv[1:]:
    g = load(p)
    print('==', p)
    for i, m in enumerate(g.get('materials', [])):
        print(' mat', i, m.get('name'), 'alpha', m.get('alphaMode'), 'tex' if 'baseColorTexture' in m.get('pbrMetallicRoughness', {}) else '', m.get('extensions', {}).keys(), m.get('emissiveFactor'))
    for i, n in enumerate(g.get('nodes', [])):
        print(' node', i, n.get('name'), n.get('mesh'), n.get('translation'), n.get('scale'), n.get('children'))
    for i, me in enumerate(g.get('meshes', [])):
        for pr in me['primitives']:
            acc = g['accessors'][pr['attributes']['POSITION']]
            print(' mesh', i, me.get('name'), 'mat', pr.get('material'), 'min', [round(v,3) for v in acc['min']], 'max', [round(v,3) for v in acc['max']])
