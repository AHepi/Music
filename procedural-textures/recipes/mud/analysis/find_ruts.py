# What this does (plain words): runs the rut finder on the ground of the mud picture (puddles and stones already painted over) and saves the curves plus a picture of
# them laid over the reference so I can judge. Analysis only. Use: python3 -I find_ruts.py [name] [sigma]
import os, pickle, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rut_tools as rt
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
name = sys.argv[1] if len(sys.argv) > 1 else 'mud'
sigma = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
ground = cv2.imread(os.path.join(HERE, 'ground_trace_' + name, 'ground_inpainted.png'))
grey = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
curves, strength = rt.trace_ruts(grey, sigma=sigma, high_percentile=94.0, low_fraction=0.4, min_length=100.0, simplify=4.0, max_turn_degrees=30.0) if sigma >= 7 else rt.trace_ruts(grey, sigma=sigma)
print('curves', len(curves), 'total length', int(sum(c['length'] for c in curves)))
pickle.dump(curves, open(os.path.join(HERE, f'ruts_{name}.pkl' if sigma < 7 else f'ruts_s{int(sigma)}_{name}.pkl'), 'wb'))
ref = cv2.imread(f'{PROC}/reference/{name}/colour.png')
vis = (ref * 0.6).astype(np.uint8)
h, w = grey.shape
for c in curves:
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            cv2.polylines(vis, [(c['pts'] + [ox, oy]).round().astype(np.int32)], False, (0, 255, 255), 2)
cv2.imwrite(f'/tmp/mudscratch/ruts_{name}.png', vis)
cv2.imwrite(f'/tmp/mudscratch/ridge_{name}.png', np.clip(strength / np.percentile(strength, 99.5) * 255, 0, 255).astype(np.uint8))
