import sys; sys.path.insert(0, ".")
# What this does (plain words): second fitting step, the "tracing" layer: cut the colour picture into flat patches of the palette colours
# (small ones are merged into their neighbours), trace each patch's outline as a short list of corner steps, and write it as a description
# (palette + derivation rule + patch list, no brick layout needed, the patches already contain the bricks). Several sizes are written to
# ../generator/descriptions/L_amin<A>_eps<E>.json so the size / accuracy trade-off can be measured.
import json
from region_tools import *
base = json.load(open('../generator/descriptions/stage1_bricks_only.json'))
labels = np.load('labels_k16.npy')
pal_rgb = np.load('palette_k16.npy')
pal_bgr = pal_rgb[:, ::-1]
K = 16
L1 = mode_filter(labels, K, 3)
variants = [(int(a), float(e)) for a, e in (arg.split(':') for arg in sys.argv[1:] if ':' in arg)] or [(20, 2.0)]
for amin, eps in variants:
    L2, _ = remove_small(L1, K, amin)
    regs = trace_regions(L2, K, epsilon=eps)
    enc = encode_regions(regs)
    back0 = int(np.bincount(L2.ravel()).argmax())
    enc.insert(0, [back0, 0, 0, 2508, 0, 0, 2508, -2508, 0])     # the plain tile-sized rectangle first: the backdrop (also keeps the audit's grid test honest, see notes)
    back = int(np.bincount(L2.ravel()).argmax())
    desc = {k: base[k] for k in ('format', 'surface', 'tile', 'seed', 'palette', 'maps')}
    desc['backdrop'] = back
    desc['palette'] = base['palette'] + [[60, 43, 34, 0.9]]                      # one extra colour: the dark outline
    desc['layers'] = [{'type': 'regions', 'unit': 0.5, 'wrap': False, 'items': enc}]
    if '--no-outline' not in sys.argv:
        desc['layers'].append({'type': 'outlines', 'colour': 16, 'corner_radius': 9.0, 'inside': [1.5, 1.5, 1.5, 2.5], 'outside': [1.5, 0.5, 2.5, 4.5],
                               'rows': base['layers'][0]['rows']})
    name = f'../generator/descriptions/L_amin{amin}_eps{eps}.json'
    json.dump(desc, open(name, 'w'), separators=(',', ':'))
    import os
    print(name, os.path.getsize(name), 'bytes', len(regs), 'regions', sum(len(r['points']) for r in regs), 'vertices')
