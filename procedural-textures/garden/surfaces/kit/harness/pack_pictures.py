# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# PICTURES OF A PACK for the reports (plain Python: numpy and OpenCV; no Blender): the ground plan masks side by side over a stretch of the ground, one wall sheet's masks, the
# habitat fields with the traffic lanes drawn over them. Every picture is a JPG under 400 KB with the mask's name and its real range on it.
#     python3 -I harness/pack_pictures.py ground SET SCENE OUT.jpg y0 y1 name1,name2,...
#     python3 -I harness/pack_pictures.py wall SET SCENE OUT.jpg OBJECT_NAME [name1,name2,...]
#     python3 -I harness/pack_pictures.py habitat SET SCENE OUT.jpg y0 y1
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402
import sheets  # noqa: E402
from measure_zones import read_gp  # noqa: E402
from masks import pack as pack_module  # noqa: E402

MAPS = {'default': cv2.COLORMAP_VIRIDIS, 'height': cv2.COLORMAP_TURBO}


def colourise(a, lo=0.0, hi=1.0, cmap='default'):
    t = np.clip((a - lo) / max(1e-9, hi - lo), 0, 1)
    return cv2.applyColorMap((t * 255).astype(np.uint8), MAPS[cmap])


def tile(a, label, lo=0.0, hi=1.0, cmap='default', scale=1.0, note=''):
    """a: 2D array with row 0 = low y (flipped here so the top of the picture is the high end)."""
    img = colourise(np.flipud(a), lo, hi, cmap)
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    text = f'{label}  {note}' if note else label
    return sheets._label(img, text, scale=0.42)


def _ground_array(gp, manifest, name):
    a = gp[name]
    gh, gw = int(round((manifest['ground']['y'][1] - manifest['ground']['y'][0]) / manifest['ground']['dot_m'])), int(round((manifest['ground']['x'][1] - manifest['ground']['x'][0]) / manifest['ground']['dot_m']))
    if a.shape != (gh, gw):
        a = cv2.resize(a, (gw, gh), interpolation=cv2.INTER_AREA)
    return a


def ground_sheet(set_id, scene_id, out, y0, y1, names, scale=1.0):
    gp, manifest = read_gp(set_id, scene_id)
    g = manifest['ground']
    gp = dict(gp)
    # real heights for ground_height (stored over the z range)
    if 'ground_height' in gp:
        z0, z1 = g['z_range']
        gp['ground_height'] = gp['ground_height'] * (z1 - z0) + z0
    tiles = []
    for name in names:
        a = _ground_array(gp, manifest, name)
        r0, r1 = int((y0 - g['y'][0]) / g['dot_m']), int((y1 - g['y'][0]) / g['dot_m'])
        sub = a[max(0, r0):min(a.shape[0], r1)]
        if name == 'ground_height':
            valid = sub[sub > g['z_range'][0] + 0.01]
            lo, hi = (float(valid.min()), float(valid.max())) if valid.size else (0.0, 1.0)
            hi = max(hi, lo + 0.05)
            tiles.append(tile(sub, 'ground_height', lo, hi, 'height', scale, f'{lo:.2f} to {hi:.2f} m'))
        else:
            tiles.append(tile(sub, name, 0.0, 1.0, 'default', scale, f'{float(sub.min()):.2f} to {float(sub.max()):.2f}'))
    h = max(t.shape[0] for t in tiles)
    row = np.full((h, sum(t.shape[1] + 4 for t in tiles), 3), 24, np.uint8)
    x = 0
    for t in tiles:
        row[:t.shape[0], x:x + t.shape[1]] = t
        x += t.shape[1] + 4
    cap = np.full((24, row.shape[1], 3), 24, np.uint8)
    cv2.putText(cap, f'{set_id} / {scene_id}: ground plan, y {y0:g} to {y1:g} m (x across, 4 cm per dot; top of each picture = far end)', (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)
    return sheets.save_under_limit(np.concatenate([cap, row], axis=0), out)


def wall_sheet(set_id, scene_id, out, object_name, names=('height', 'sheltered', 'drip', 'corner'), scale=2.0):
    manifest = pack_module.load_manifest(mc.KIT_ROOT, set_id, scene_id)
    sheet = next(s for s in manifest['frames']['sheets'] if s['object'] == object_name or object_name in s.get('objects', []))
    tiles = []
    cache = {}
    for name in names:
        entry = manifest['masks']['WF'][name]
        atlas = manifest['frames']['atlases'][entry['picture']]
        if entry['picture'] not in cache:
            cache[entry['picture']] = pack_module.read_png(os.path.join(manifest['_dir'], atlas['file']))
        img = cache[entry['picture']]
        rect = atlas['rects'][str(sheet['id'])]
        ch = 'RGBA'.index(entry['channel']) if img.shape[2] > 1 else 0
        a = img[..., ch] if img.ndim == 3 else img
        # the atlas is a stack: row 0 = LOW end in pack.read_png; the rect's y counts from the first row written (the sheet's low end)
        sub = a[rect['y']:rect['y'] + rect['h'], :rect['w']]
        if name == 'height':
            lo, hi = entry.get('range', [-1.5, 11.0])
            sub = sub * (hi - lo) + lo
            tiles.append(tile(sub, 'height', 0.0, float(sheet.get('top_z', 6.0)), 'height', scale, 'metres above the ground'))
        else:
            tiles.append(tile(sub, name, 0.0, 1.0, 'default', scale, f'{float(sub.min()):.2f} to {float(sub.max()):.2f}'))
    h = max(t.shape[0] for t in tiles)
    row = np.full((h, sum(t.shape[1] + 4 for t in tiles), 3), 24, np.uint8)
    x = 0
    for t in tiles:
        row[:t.shape[0], x:x + t.shape[1]] = t
        x += t.shape[1] + 4
    cap = np.full((24, row.shape[1], 3), 24, np.uint8)
    cv2.putText(cap, f'{object_name}: wall sheet {sheet["size"][0]} x {sheet["size"][1]} dots (2 cm per dot; across the front, up from the floor), {len(sheet.get("sources", []))} run-off sources found', (6, 17),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)
    return sheets.save_under_limit(np.concatenate([cap, row], axis=0), out)


def habitat_sheet(set_id, scene_id, out, y0, y1, fields=('moss_site', 'weed_site', 'algae_site'), scale=1.4):
    gp, manifest = read_gp(set_id, scene_id)
    g = manifest['ground']
    r0, r1 = int((y0 - g['y'][0]) / g['dot_m']), int((y1 - g['y'][0]) / g['dot_m'])
    sl = slice(max(0, r0), r1)
    lanes = gp['footfall'][sl] >= 0.6
    crown = gp['crown'][sl] >= 0.7
    keep = gp['keepclear'][sl] >= 0.5
    tiles = []
    for name in fields:
        a = gp[name][sl]
        base = colourise(np.flipud(a), 0.0, max(0.05, float(a.max())), 'default')
        # the zones where the field must be exactly 0, drawn over it: footfall >= 0.6 red edge, crown >= 0.7 blue edge, keepclear >= 0.5 orange edge
        for zone, colour in ((lanes, (60, 60, 255)), (crown, (255, 160, 60)), (keep, (40, 170, 255))):
            z = np.flipud(zone).astype(np.uint8)
            edge = z - cv2.erode(z, np.ones((3, 3), np.uint8))
            base[edge > 0] = colour
        inside = max((float(a[z].max()) for z in (lanes, crown, keep) if z.any()), default=0.0)
        img = cv2.resize(base, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        tiles.append(sheets._label(img, f'{name}  max {float(a.max()):.2f}; inside the zones {inside:.1f}', scale=0.42))
    h = max(t.shape[0] for t in tiles)
    row = np.full((h, sum(t.shape[1] + 4 for t in tiles), 3), 24, np.uint8)
    x = 0
    for t in tiles:
        row[:t.shape[0], x:x + t.shape[1]] = t
        x += t.shape[1] + 4
    cap = np.full((24, row.shape[1], 3), 24, np.uint8)
    cv2.putText(cap, f'{set_id} / {scene_id}: where moss, weeds and algae may grow (bright = more). Edges: red = trodden lanes (footfall 0.6+), blue = crown (0.7+), orange = keep clear (0.5+). Must be exactly 0 inside.',
                (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (240, 240, 240), 1, cv2.LINE_AA)
    return sheets.save_under_limit(np.concatenate([cap, row], axis=0), out)


if __name__ == '__main__':
    kind, set_id, scene_id, out = sys.argv[1:5]
    if kind == 'ground':
        print(ground_sheet(set_id, scene_id, out, float(sys.argv[5]), float(sys.argv[6]), sys.argv[7].split(',')))
    elif kind == 'wall':
        print(wall_sheet(set_id, scene_id, out, sys.argv[5], tuple(sys.argv[6].split(',')) if len(sys.argv) > 6 else ('height', 'sheltered', 'drip', 'corner')))
    elif kind == 'habitat':
        print(habitat_sheet(set_id, scene_id, out, float(sys.argv[5]), float(sys.argv[6])))
