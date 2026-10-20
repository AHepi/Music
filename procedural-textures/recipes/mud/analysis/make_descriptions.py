# What this does (plain words): writes the rows of the "ladder" for the mud reference: descriptions that add one layer at a time (flat ground; + puddle outlines; + a few big
# stones; + wheel ruts; + crumbly ground clods; + puddle water tones, stone faces and all stones; and the big traced-patches class) and audits each one with the project
# audit tool (size, no picture data). The S class must be 8 KB or less, M 64 KB or less, L 512 KB or less. Files go to recipes/mud/description/. Analysis only: it
# reads the found elements (analysis/elements_mud.pkl), the fitted ground model and the traced patch lists, never the picture itself.
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import describe_tools as dt
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
NAME = sys.argv[1] if len(sys.argv) > 1 else 'mud'
SUFFIX = '' if NAME == 'mud' else '_' + NAME
OUT = os.path.join(HERE, '..', 'description' if NAME == 'mud' else 'description_' + NAME); os.makedirs(OUT, exist_ok=True)
el = dt.load_elements(NAME)
GM = os.path.join(HERE, f'ground_model_{NAME}.json'); RUTS = os.path.join(HERE, f'ruts_main_{NAME}.json')
_model = json.load(open(GM)); BASE = _model['earth_palette_ids'][max(range(len(_model['ground_share_by_tone'])), key=lambda i: _model['ground_share_by_tone'][i])]   # the most common earth colour
def level(**kw):
    base = dict(ground=BASE, puddle_eps=99, puddle_tones=False, stone_min_area=10**9, stone_eps=3, max_stones=0, max_faces=0)
    base.update(kw); return base
rows = {}
def put(name, d):
    path = os.path.join(OUT, name + '.json')
    json.dump(d, open(path, 'w'), separators=(',', ':'))
    rows[name] = dt.byte_size(d); print(f'{name:34s} {rows[name]:8d} bytes', flush=True)
    return d
# row 0: flat ground only (the palette is cut to what is used later; here the full 16)
d0 = dt.make_description(el, level(), name=NAME); d0['layers'] = []
put('R0_flat_ground', d0)
# row 1: + the six biggest puddles, coarse outlines, no tones
d1 = dt.make_description(el, level(puddle_eps=6)); d1['layers'][0]['items'] = d1['layers'][0]['items'][:8]; d1['layers'] = d1['layers'][:1]
put('R1_plus_puddle_outlines', d1)
# row 2: + 40 biggest stones (outline only)
d2 = dt.make_description(el, level(puddle_eps=6, stone_min_area=0, stone_eps=4, max_stones=40)); d2['layers'][0]['items'] = d2['layers'][0]['items'][:8]
put('R2_plus_40_big_stones', d2)
# row 3: + wheel ruts
d3 = dt.add_procedural_ground(d2, GM, RUTS, el_kinds=el['kinds'], clod_count=0, rut_eps=9); d3['layers'] = [l for l in d3['layers'] if l['type'] != 'clods']
put('R3_plus_ruts', d3)
# row 4: + crumbly ground clods  (this row is the S class if small enough)
for n_puddles, p_eps, n_stones, s_eps, n_ruts, r_eps in ((8, 6, 40, 4, 34, 9), (7, 8, 24, 5, 26, 14), (6, 9, 16, 6, 22, 16), (6, 10, 12, 7, 18, 18)):
    d2s = dt.make_description(el, level(puddle_eps=p_eps, stone_min_area=0, stone_eps=s_eps, max_stones=n_stones)); d2s['layers'][0]['items'] = d2s['layers'][0]['items'][:n_puddles]
    ruts_all = json.load(open(RUTS)); ruts_all = sorted(ruts_all, key=lambda r: -r['length'])[:n_ruts]
    json.dump(ruts_all, open('/tmp/mudscratch/ruts_s.json', 'w'))
    d4 = dt.add_procedural_ground(d2s, GM, '/tmp/mudscratch/ruts_s.json', el_kinds=el['kinds'], clod_count=14000, rut_eps=r_eps)
    for layer in d4['layers']:
        if layer['type'] == 'clods':
            layer['chances'] = [[[round(v, 2) for v in row] for row in side] for side in layer['chances']]
    print('  S try', n_puddles, n_stones, n_ruts, '->', dt.byte_size(d4))
    if dt.byte_size(d4) <= 8000:
        break
put('S_layout_ruts_clods', d4)
# row 5 = M class: finer puddles with water tones, stones with faces (as many as fit in 64 KB)
for min_area, eps, faces in ((40, 2.2, 3), (30, 2.4, 3), (24, 2.6, 2), (20, 2.8, 2), (40, 3.0, 2), (60, 3.2, 1), (90, 3.4, 1), (130, 3.6, 1)):
    lvl = level(puddle_eps=2.0, puddle_tones=True, tone_eps=4, tone_min_area=60, stone_min_area=min_area, stone_eps=eps, max_stones=10**9, max_faces=faces, face_eps=3, face_min_area=30)
    dm = dt.add_procedural_ground(dt.make_description(el, lvl, name=NAME), GM, RUTS, el_kinds=el['kinds'], clod_count=14000, rut_eps=6)
    size = dt.byte_size(dm)
    print('  M try: stones >=', min_area, 'eps', eps, 'faces', faces, '->', size)
    if size <= 64 * 1024:
        break
put('M_puddle_tones_stone_faces', dm)
# L class: traced ground (5000 patches, loose outlines) under fine puddles and stones, NO procedural ground (never mix the two)
fine = level(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
for target, eps in ((5000, 1.8), (5000, 2.0), (5000, 2.4)):
    dl = dt.add_patches(dt.make_description(el, fine), os.path.join(HERE, f'ground_trace_{NAME}', f'patches_{target}.pkl'), epsilon_keep=eps)
    size = dt.byte_size(dl)
    print('  L try', target, eps, size)
    if size <= 500 * 1024:
        break
put('L_traced_ground_5000_patches', dl)
# a middle rung: traced ground with only 2000 patches
dl2 = dt.add_patches(dt.make_description(el, fine), os.path.join(HERE, f'ground_trace_{NAME}', 'patches_2000.pkl'), epsilon_keep=2.4)
put('L2_traced_ground_2000_patches', dl2)
# the final L class: traced ground (5000 patches, loose outlines) under fine puddles and stones, plus a CORRECTION layer of traced patches painted last where the picture is still wrong
import cv2
ref_bgr = cv2.imread(os.path.join(PROC, 'reference', NAME, 'colour.png'))
base_l = dt.add_patches(dt.make_description(el, fine), os.path.join(HERE, f'ground_trace_{NAME}', 'patches_5000.pkl'), epsilon_keep=2.6)
for thr, min_area in ((6, 11), (6, 14), (7, 14), (8, 14)):
    dfinal, n_res = dt.add_residual_patches(base_l, ref_bgr, threshold=thr, min_area=min_area, epsilon=1.6)
    print('  L_final try', thr, min_area, n_res, dt.byte_size(dfinal))
    if dt.byte_size(dfinal) <= 505 * 1000:
        break
put('L_final_traced_ground_plus_corrections', dfinal)
json.dump(rows, open(os.path.join(HERE, f'description_sizes{SUFFIX}.json'), 'w'), indent=1)
for name in rows:
    limit = {'S': 8, 'M': 64, 'L': 512}.get(name[0], 512)
    r = subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'description_audit.py'), os.path.join(OUT, name + '.json'), '--limit-kilobytes', str(limit)], capture_output=True, text=True)
    print(name, '| audit', 'PASS' if r.returncode == 0 else 'FAIL', '|', r.stdout.strip().replace('\n', ' ')[:200], r.stderr.strip()[:200])
