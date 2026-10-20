# What this does (plain words): turns the things found in the mud picture (puddles, stones; see element_tools.py / extract_elements.py) into a DESCRIPTION: the small
# dictionary the generator is driven by. Different "levels" keep more or fewer things and draw their outlines with more or fewer corners, so the size of the description
# (in bytes) can be traded against accuracy. It also measures the size and scores a description with a quick numpy picture (no Blender). Analysis only.
import json, os, pickle, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import mud_layers as ml

MAPS = {'height': {'grey_low': 20.0, 'grey_high': 128.0, 'blur': 0.5, 'mode': 'from_colour'}, 'normal': {'strength': 9}}


def simplify(points, epsilon):
    pts = np.asarray(points, np.int32)
    if epsilon <= 0 or len(pts) <= 4:
        return pts
    out = cv2.approxPolyDP(pts.reshape(-1, 1, 2), epsilon, True)[:, 0, :]
    return out if len(out) >= 3 else pts


def byte_size(description):
    return len(json.dumps(description, separators=(',', ':')).encode())


def load_elements(name='mud'):
    d = pickle.load(open(os.path.join(HERE, f'elements_{name}.pkl'), 'rb'))
    return d


def water_base(puddle, water_ids):
    totals = {}
    for t in puddle['tones']:
        totals[t['c']] = totals.get(t['c'], 0) + t['a']
    return max(totals, key=totals.get) if totals else water_ids[0]


def make_description(elements, level, name='mud'):
    """level: dict with keys puddle_eps, puddle_tones (bool), tone_eps, tone_min_area, stone_min_area, stone_eps, face_eps, max_faces, face_min_area, max_stones."""
    palette = [[int(c[2]), int(c[1]), int(c[0])] for c in elements['palette_bgr']]
    kinds = elements['kinds']
    water_ids = [i for i, k in enumerate(kinds) if k == 'water']
    counts = {}
    for p in elements['puddles']:
        pass
    # ground colour: the palette entry nearest to the picture's typical earth (the most common earth colour is index 0 or 9 in this palette; found by share in the analysis)
    ground = int(level.get('ground', 0))
    puddles = []
    for p in sorted(elements['puddles'], key=lambda p: -p['area']):
        item = {'b': int(water_base(p, water_ids)), 'p': ml.encode(simplify(p['p'], level['puddle_eps']))}
        if level.get('puddle_tones'):
            tones = [t for t in sorted(p['tones'], key=lambda t: -t['a']) if t['a'] >= level.get('tone_min_area', 30) and t['c'] != item['b']]
            item['t'] = [[int(t['c']), ml.encode(simplify(t['p'], level.get('tone_eps', 2.5)))] for t in tones]
        puddles.append(item)
    stones = []
    for s in sorted(elements['stones'], key=lambda s: -s['area']):
        if s['area'] < level['stone_min_area'] or len(stones) >= level.get('max_stones', 10 ** 9):
            continue
        faces = [(k, simplify(pp, level.get('face_eps', 2.0)), a) for k, pp, a in s['faces'] if a >= level.get('face_min_area', 12)][:level.get('max_faces', 0)]
        stones.append([int(s['base']), ml.encode(simplify(s['outline'], level['stone_eps'])), [[int(k), ml.encode(pp)] for k, pp, a in faces]])
    layers = [{'type': 'puddles', 'items': puddles}, {'type': 'stones', 'items': stones}]
    return {'name': name, 'tile': 1254, 'palette': palette, 'ground': {'colour': ground}, 'layers': layers, 'maps': MAPS}


def score_description(description, label, texture=True, scratch='/tmp/mudscratch'):
    import score_tools as st
    shapes = ml.make_shape_list(description)
    img = ml.draw_preview(description, shapes=shapes)
    folder = os.path.join(scratch, 'preview_' + label)
    st.write_folder(img, folder)
    r = st.score_folder(folder, texture=texture)
    keys = ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall')
    return {k: r.get(k) for k in keys}, img


def add_patches(description, patches_pickle, epsilon_keep=None, under=True):
    """Add the traced ground patches (analysis/ground_trace_*/patches_N.pkl) as the FIRST layer (they sit under the puddles and stones). The patch palette is appended to
    the description's palette; patch colour numbers are shifted. Returns a new description."""
    data = pickle.load(open(patches_pickle, 'rb'))
    d = json.loads(json.dumps(description))
    offset = len(d['palette'])
    d['palette'] += [[int(c[2]), int(c[1]), int(c[0])] for c in data['palette_bgr']]
    items = [[int(r['c']) + offset, ml.encode(simplify(r['p'], epsilon_keep) if epsilon_keep else np.asarray(r['p']))] for r in data['regions']]
    layer = {'type': 'patches', 'items': items}
    d['layers'] = [layer] + d['layers'] if under else d['layers'] + [layer]
    return d


def pick_rut_colours(palette, kinds):
    """Which palette entries play which part in a rut, chosen by lightness: the groove = the darkest earth colour, the broad band = the next darker earth colour, the bank = a light earth
    colour, the wet shine = a grey-brown 'stone'-kind colour of middling lightness."""
    lab = cv2.cvtColor(np.asarray(palette, np.uint8)[:, ::-1].reshape(1, -1, 3).astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[0]
    earth = [i for i, k in enumerate(kinds) if k == 'earth']
    by_light = sorted(earth, key=lambda i: lab[i][0])
    stone_mid = [i for i, k in enumerate(kinds) if k == 'stone' and 28 <= lab[i][0] <= 45]
    return {'groove': by_light[0], 'band': by_light[1], 'bank': min(earth, key=lambda i: abs(lab[i][0] - 43)), 'wet': stone_mid[0] if stone_mid else by_light[2]}


def add_procedural_ground(description, ground_model_path, ruts_path, el_kinds=None, clod_count=14000, rut_eps=5, base=None, colours=None, coverage_tones=None, seed=1, zone_scale=30.0, zone_weight=0.6):
    """Put the 'procedural ground' under the puddles and stones: the wheel ruts (curves with a broad dark band, groove, bank and wet streaks) and the crumbly ground clods
    (chances of each earth colour by distance from the nearest rut and side, sizes and shapes measured on the reference). Returns a new description."""
    model = json.load(open(ground_model_path))
    ruts = json.load(open(ruts_path))
    d = json.loads(json.dumps(description))
    ids = model['earth_palette_ids']
    share = model['ground_share_by_tone']
    lightness = [float(np.dot([0.299, 0.587, 0.114], d['palette'][i])) for i in ids]
    order = list(np.argsort(lightness))                     # tones from dark to light (the chance table follows the same order)
    ids_sorted = [ids[i] for i in order]
    base = ids[int(np.argmax(share))] if base is None else base
    colours = colours or (pick_rut_colours(d['palette'], el_kinds) if el_kinds else {'band': 3, 'groove': 7, 'bank': 9, 'wet': 5})
    items = []
    for r in ruts:
        pts = simplify(r['pts'], rut_eps).tolist()
        if len(pts) >= 2:
            items.append({'p': pts, **{'w': 20, 'bw': 9, 'gw': 6}, **colours})
    chances = np.array(model['tone_chance_by_side_and_distance'])[:, :, order]
    layer_ruts = {'type': 'ruts', 'seed': seed, 'wobble': 2.0, 'items': items}
    layer_clods = {'type': 'clods', 'seed': seed, 'count': clod_count, 'tones': ids_sorted, 'zone': {'scale': zone_scale, 'weight': zone_weight}, 'bins': model['distance_bins'][:-1], 'chances': np.round(chances, 3).tolist(),
                   'area_log_mean': round(model['patch_area_log_mean'], 3), 'area_log_sd': round(model['patch_area_log_sd'], 3), 'aspect_median': round(model['patch_aspect_median'], 2),
                   'along': 0.8, 'flow_range': 60, 'skip': [base]}
    d['ground'] = {'colour': int(base)}
    d['seed'] = seed
    d['layers'] = [layer_ruts, layer_clods] + d['layers']
    return d


def add_residual_patches(description, reference_bgr, threshold=9.0, min_area=14, epsilon=1.8, max_patches=None, palette_ids=None):
    """A correction layer painted LAST: where the picture drawn from the description is still more than `threshold` colour steps (Delta E) away from the reference, trace the reference's
    flat colour there (nearest palette colour, connected areas of at least `min_area` dots) as patches. It is tracing, like the ground patches; it is spent where the other layers are
    wrong (stones cut up by the stone finder, puddle edges), which is where a patch is worth most. Returns (new description, number of patches)."""
    import score_tools as st
    img = ml.draw_preview(description)
    lab_a = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    lab_b = cv2.cvtColor(reference_bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    bad = (np.sqrt(((lab_a - lab_b) ** 2).sum(-1)) > threshold)
    palette = np.array(description['palette'], np.uint8)[:, ::-1].reshape(1, -1, 3)
    plab = cv2.cvtColor(palette.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[0]
    ids = list(range(len(plab))) if palette_ids is None else list(palette_ids)
    flat = lab_b.reshape(-1, 3)
    labels = np.zeros(len(flat), np.int32)
    for s in range(0, len(flat), 200000):
        dd = ((flat[s:s + 200000, None, :] - plab[None, ids, :]) ** 2).sum(-1)
        labels[s:s + 200000] = np.array(ids)[dd.argmin(1)]
    labels = cv2.medianBlur(labels.reshape(reference_bgr.shape[:2]).astype(np.uint8), 3)
    items = []
    for k in ids:
        m = (bad & (labels == k)).astype(np.uint8)
        n, comp, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
        for j in range(1, n):
            if stats[j, cv2.CC_STAT_AREA] < min_area:
                continue
            x, y, w, h = stats[j, :4]
            contours, _ = cv2.findContours(np.pad((comp[y:y + h, x:x + w] == j).astype(np.uint8), 1), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            c = max(contours, key=cv2.contourArea)
            poly = cv2.approxPolyDP(c, epsilon, True)[:, 0, :] + np.array([x - 1, y - 1])
            if len(poly) >= 3:
                items.append((int(stats[j, cv2.CC_STAT_AREA]), int(k), poly))
    items.sort(key=lambda t: -t[0])
    if max_patches:
        items = items[:max_patches]
    d = json.loads(json.dumps(description))
    d['layers'].append({'type': 'patches', 'items': [[k, ml.encode(p)] for a, k, p in items]})
    return d, len(items)
