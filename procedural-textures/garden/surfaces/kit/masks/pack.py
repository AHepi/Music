# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE PACK: writes (and reads) a scene's mask pictures and manifest.json. A pack folder holds a handful of pictures, each carrying up to four masks (R, G, B, A):
#   gp_height.png (16 bit)   R ground height, G has-ground, B ground role number           gp_a .. gp_g (8 bit)   ground plan at 4 cm, four masks each
#   gp_fine.png (8 bit)      step_top, step_edge, edge_dist, piece_gap at 2 cm
#   wf_*.png                 wall sheets stacked in one atlas per kind (2 cm: wf_a, wf_b, wf_height 16 bit; 8 cm: wf_c, wf_d)
#   tx_<material>.png (set-wide, in ../textures/)   R tx_cavity, G tx_joint, B tx_cell
#   manifest.json            where every bus name lives (picture, channel, frame, scale), the frames' matrices and atlas rectangles, statistics, checks, timings
# All pictures are PNG, read as Non-Color data, never colour-managed; the first row of a file is the TOP (high y or high v) so Blender's picture coordinates match the world.
# Plain Python (numpy + OpenCV): also finalises the habitat fields after the geometry stage, so the rubbish picture (made by a render) can be added without redoing the geometry.
import json
import os
import time

import numpy as np

from . import habitat, names as names_module, texture_space
from .grid import Grid

PACK_ROOT_NAME = 'packs'
GP_LAYOUT = {
    'gp_a': ('wall_dist', 'prop_dist', 'inside_corner', 'step_foot'),
    'gp_b': ('vertical_foot', 'seam_dist', 'cover_dist', 'water_dist'),
    'gp_c': ('slope', 'lowness', 'crown', 'above_water'),
    'gp_d': ('shade', 'dampness', 'openness', 'sheltered'),
    'gp_e': ('footfall', 'keepclear', 'entry_rand', 'existing_growth'),
    'gp_f': ('moss_site', 'weed_site', 'algae_site', 'lichen_site'),
    'gp_g': ('rubbish_heap', 'drip', 'drip_dist', 'drip_kind'),
}
FINE_LAYOUT = ('step_top', 'step_edge', 'edge_dist', 'piece_gap')
WF_LAYOUT = {'wf_a': ('sheltered', 'drip', 'drip_dist', 'drip_kind'), 'wf_b': ('corner', 'reveal')}
WF_COARSE_LAYOUT = {'wf_c': ('shade', 'dampness', 'openness', 'moss_site'), 'wf_d': ('algae_site', 'lichen_site')}
HEIGHT_RANGE = (-1.5, 11.0)


def pack_dir(kit_root, set_id, scene_id):
    return os.path.join(kit_root, 'masks', PACK_ROOT_NAME, set_id, scene_id)


def texture_dir(kit_root, set_id):
    return os.path.join(kit_root, 'masks', PACK_ROOT_NAME, set_id, 'textures')


def write_png(path, array, bits=8):
    """array: (h, w) or (h, w, c) floats 0..1, row 0 = LOW end; written flipped (first file row = top). Channels are R, G, B, A."""
    import cv2
    a = np.asarray(array, np.float32)
    if a.ndim == 2:
        a = a[..., None]
    a = np.flipud(a)
    scale = 255.0 if bits == 8 else 65535.0
    q = np.clip(np.round(a * scale), 0, scale).astype(np.uint8 if bits == 8 else np.uint16)
    if q.shape[2] >= 3:
        q = q.copy()
        q[..., [0, 2]] = q[..., [2, 0]]            # OpenCV writes BGR(A)
    if q.shape[2] == 1:
        q = q[..., 0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, q, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    return os.path.getsize(path)


def read_png(path):
    """Returns (h, w, c) floats 0..1 with row 0 = LOW end (the inverse of write_png), channels R, G, B, A."""
    import cv2
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    a = im.astype(np.float32) / scale
    if a.ndim == 2:
        a = a[..., None]
    if a.shape[2] >= 3:
        a = a.copy()
        a[..., [0, 2]] = a[..., [2, 0]]
    return np.flipud(a)


def save_raw(raw_dir, grid, fine_grid, arrays, fine, sheets, frame_of, meta):
    os.makedirs(raw_dir, exist_ok=True)
    np.savez_compressed(os.path.join(raw_dir, 'ground.npz'), **{k: v for k, v in arrays.items() if not k.startswith('_role')})
    np.savez_compressed(os.path.join(raw_dir, 'fine.npz'), **fine)
    sheet_meta = []
    for sh in sheets:
        np.savez_compressed(os.path.join(raw_dir, f'sheet_{sh.id}.npz'), **{k: v for k, v in sh.arrays.items()}, **{'coarse_' + k: v for k, v in sh.coarse.items()})
        m = dict(sh.meta)
        m['id'] = sh.id
        m['name'] = sh.name
        sheet_meta.append(m)
    json.dump(dict(grid=grid.meta(), fine_grid=fine_grid.meta(), sheets=sheet_meta, frame_of_object=frame_of, **meta), open(os.path.join(raw_dir, 'raw.json'), 'w'), indent=1)


def load_raw(raw_dir):
    info = json.load(open(os.path.join(raw_dir, 'raw.json')))
    ground = dict(np.load(os.path.join(raw_dir, 'ground.npz')))
    fine = dict(np.load(os.path.join(raw_dir, 'fine.npz')))
    sheets = []
    for m in info['sheets']:
        z = dict(np.load(os.path.join(raw_dir, f'sheet_{m["id"]}.npz')))
        sheets.append((m, {k: v for k, v in z.items() if not k.startswith('coarse_')}, {k[7:]: v for k, v in z.items() if k.startswith('coarse_')}))
    return info, ground, fine, sheets


def finalise_ground(settings, grid, ground, extra=None):
    """Brings the coarse pictures to the normal grid, then makes dampness and the habitat fields. `ground` holds the geometry stage's arrays. Returns a dict of all GP masks."""
    import cv2
    out = {}
    g16 = None
    for key in ('shade', 'openness', 'sun_shade', 'sheltered'):
        a = ground[key]
        out[key] = cv2.resize(a, (grid.width, grid.height), interpolation=cv2.INTER_LINEAR) if a.shape != grid.shape() else a
    for key in ('slope', 'lowness', 'crown', 'wall_dist', 'prop_dist', 'inside_corner', 'step_foot', 'vertical_foot', 'cover_dist', 'seam_dist', 'water_dist', 'above_water',
                'footfall', 'keepclear', 'entry_rand', 'existing_growth', 'drip', 'drip_dist'):
        out[key] = ground[key]
    has = ground['has_ground']
    out['has_ground'] = has
    out['shade'][~has] = 0.5
    heap = np.zeros(grid.shape(), np.float32)
    if extra and extra.get('rubbish_heap') is not None:
        heap = np.asarray(extra['rubbish_heap'], np.float32)
    out['rubbish_heap'] = heap
    out['drip_kind'] = ground.get('drip_kind', np.zeros(grid.shape(), np.float32))
    out['dampness'] = habitat.dampness(settings, out)
    out.update(habitat.fields(settings, out))
    return out


def build(settings, kit_root, scene_id, raw_dir, out_dir, rubbish_heap=None, checks=None, timings=None, with_textures=True):
    """Writes the whole pack. Returns the manifest dict."""
    info, ground, fine, sheets = load_raw(raw_dir)
    grid = Grid(info['grid']['x'][0], info['grid']['x'][1], info['grid']['y'][0], info['grid']['y'][1], info['grid']['dot_m'])
    fine_grid = Grid(info['fine_grid']['x'][0], info['fine_grid']['x'][1], info['fine_grid']['y'][0], info['fine_grid']['y'][1], info['fine_grid']['dot_m'])
    gp = finalise_ground(settings, grid, ground, extra=dict(rubbish_heap=rubbish_heap))
    os.makedirs(out_dir, exist_ok=True)
    manifest = dict(schema='weathering-pack/1', set=settings.id, scene=scene_id, made=time.strftime('%Y-%m-%d %H:%M:%S'), ground=dict(info['grid'], fine=info['fine_grid']),
                    pictures={}, masks={'GP': {}, 'WF': {}, 'TX': {}}, frames=dict(sheets=[], atlases={}, frame_of_object=info['frame_of_object']), textures={}, stats=info.get('stats', {}), checks=checks or {},
                    timings=timings or {})
    z_lo, z_hi = settings.geometry.get('ground_height_picture', {}).get('z_range', [-2.0, 6.0])
    manifest['ground']['z_range'] = [z_lo, z_hi]
    total = 0

    def register(name, picture, channel, frame, **extra):
        manifest['masks'][frame][name] = dict(picture=picture, channel=channel, frame=frame, **extra)

    # ---- height (16 bit)
    h = (np.clip((ground['ground_height'] - z_lo) / (z_hi - z_lo), 0, 1))
    rgb = np.stack([h, ground['has_ground'].astype(np.float32), ground['ground_role'].astype(np.float32) / 65.0], axis=-1)
    total += write_png(os.path.join(out_dir, 'gp_height.png'), rgb, 16)
    manifest['pictures']['gp_height'] = dict(file='gp_height.png', frame='GP', grid='normal', bits=16, channels=dict(R='ground_height', G='has_ground', B='ground_role'))
    register('ground_height', 'gp_height', 'R', 'GP', unit='metres', z_range=[z_lo, z_hi])
    # ---- 8-bit ground pictures
    for picture, members in GP_LAYOUT.items():
        stack = np.stack([np.clip(gp[m], 0, 1) for m in members], axis=-1)
        stack = np.concatenate([stack, np.zeros(stack.shape[:2] + (4 - len(members),), np.float32)], axis=-1) if len(members) < 4 else stack
        total += write_png(os.path.join(out_dir, picture + '.png'), stack, 8)
        manifest['pictures'][picture] = dict(file=picture + '.png', frame='GP', grid='normal', bits=8, channels=dict(zip('RGBA', members)))
        for c, m in zip('RGBA', members):
            register(m, picture, c, 'GP')
    # ---- the fine picture
    stack = np.stack([np.clip(fine[m], 0, 1) for m in FINE_LAYOUT], axis=-1)
    total += write_png(os.path.join(out_dir, 'gp_fine.png'), stack, 8)
    manifest['pictures']['gp_fine'] = dict(file='gp_fine.png', frame='GP', grid='fine', bits=8, channels=dict(zip('RGBA', FINE_LAYOUT)))
    for c, m in zip('RGBA', FINE_LAYOUT):
        register(m, 'gp_fine', c, 'GP')
    # ---- wall sheets: one atlas per kind, sheets stacked
    if sheets:
        pad = 2
        for atlas, members in list(WF_LAYOUT.items()) + [('wf_height', ('height',))] + list(WF_COARSE_LAYOUT.items()):
            coarse = atlas in WF_COARSE_LAYOUT
            sizes = []
            for m, arr, car in sheets:
                src = car if coarse else arr
                sizes.append(src[members[0]].shape)
            width = max(s[1] for s in sizes)
            rows = sum(s[0] + 2 * pad for s in sizes)
            canvas = np.zeros((rows, width, 4), np.float32)
            rects = {}
            r0 = 0
            for (m, arr, car), s in zip(sheets, sizes):
                src = car if coarse else arr
                for k, name in enumerate(members):
                    a = src[name]
                    if name == 'height':
                        a = np.clip((a - HEIGHT_RANGE[0]) / (HEIGHT_RANGE[1] - HEIGHT_RANGE[0]), 0, 1)
                    a = np.pad(a, ((pad, pad), (0, width - s[1])), mode='edge')
                    a = np.pad(a, ((0, 0), (0, 0)), mode='edge')
                    canvas[r0:r0 + a.shape[0], :, k] = a
                rects[m['id']] = dict(x=0, y=r0 + pad, w=s[1], h=s[0])
                r0 += s[0] + 2 * pad
            bits = 16 if atlas == 'wf_height' else 8
            channels = 1 if atlas == 'wf_height' else 4
            total += write_png(os.path.join(out_dir, atlas + '.png'), canvas[..., :channels] if channels > 1 else canvas[..., 0], bits)
            manifest['frames']['atlases'][atlas] = dict(file=atlas + '.png', size=[width, rows], bits=bits, coarse=coarse, rects={str(k): v for k, v in rects.items()},
                                                        channels=dict(zip('RGBA', members)))
            manifest['pictures'][atlas] = dict(file=atlas + '.png', frame='WF', grid='coarse' if coarse else 'fine', bits=bits, channels=dict(zip('RGBA', members)))
            for c, name in zip('RGBA', members):
                register(name, atlas, c, 'WF', **({'unit': 'metres', 'range': list(HEIGHT_RANGE)} if name == 'height' else {}))
        for m, arr, car in sheets:
            manifest['frames']['sheets'].append({k: v for k, v in m.items()})
    # ---- texture space (shared by the set's scenes)
    if with_textures and settings.get('texture_maps'):
        tdir = texture_dir(kit_root, settings.id)
        root = settings.get('texture_maps', {}).get('root')
        for material, spec in settings.get('texture_maps').items():
            if material.startswith('_') or material == 'root' or not isinstance(spec, dict):
                continue
            rgb8, stats = texture_space.make_material(spec, root, kit_root)
            import cv2
            os.makedirs(tdir, exist_ok=True)
            path = os.path.join(tdir, f'tx_{material}.png')
            cv2.imwrite(path, np.flipud(rgb8)[..., ::-1].copy(), [cv2.IMWRITE_PNG_COMPRESSION, 9])
            total += os.path.getsize(path)
            manifest['textures'][material] = dict(file=os.path.join('..', 'textures', f'tx_{material}.png'), channels=dict(R='tx_cavity', G='tx_joint', B='tx_cell'), **stats)
            for c, nm in zip('RGB', ('tx_cavity', 'tx_joint', 'tx_cell')):
                register(nm, 'tx:' + material, c, 'TX')
    # ---- statistics of every mask (for the contract tests)
    stats = {}
    for name, entry in manifest['masks']['GP'].items():
        if entry['picture'] != 'gp_height' and name in gp and entry['picture'] != 'gp_fine':
            a = gp[name]
            stats[name] = dict(min=float(a.min()), max=float(a.max()), mean=float(a.mean()))
    manifest['mask_stats'] = stats
    from . import checks as checks_module
    manifest['checks'] = dict(manifest.get('checks') or {}, **checks_module.habitat_checks(gp))
    manifest['bytes'] = total
    json.dump(manifest, open(os.path.join(out_dir, 'manifest.json'), 'w'), indent=1)
    return manifest, gp


def load_manifest(kit_root, set_id, scene_id):
    path = os.path.join(pack_dir(kit_root, set_id, scene_id), 'manifest.json')
    manifest = json.load(open(path))
    manifest['_dir'] = os.path.dirname(path)
    return manifest
