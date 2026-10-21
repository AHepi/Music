# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE PLAN OF PIECE DENSITY (plain Python): the ground seen from above with the places plants must keep out of marked (the crown of the road, the trodden lanes, the keep-clear
# strips, the doorsteps, a fire), the earlier rubbish layer's mask as brown, and every plant of one picture as a dot (weeds green, moss cushions cyan, size by the plant's size).
#     python3 -I growth/plan_growth.py SET_ID SCENE_ID PIECES_JSON OUT.jpg [--y0 -4 --y1 26] [--scale 28]
# Also writes a small density number table next to the picture (OUT.json): plants per square metre in the near strip, in the zones (must be 0), counts per zone.
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.path.insert(0, os.path.join(KIT_ROOT, 'harness'))
sys.dont_write_bytecode = True

import cv2  # noqa: E402

import measure_common as mc  # noqa: E402
import measure_zones as mz  # noqa: E402


def draw(set_id, scene_id, pieces_json, out_path, y0=None, y1=None, scale=28, title=''):
    gp, manifest = mz.read_gp(set_id, scene_id)
    g = manifest['ground']
    data = json.load(open(pieces_json))
    rows = data['pieces']
    height = pack_has(manifest)
    x0, x1 = g['x']
    ys_all = g['y']
    cam = data.get('stats', {}).get('camera') or [0, 0, 0]
    y0 = ys_all[0] if y0 is None else y0
    y1 = ys_all[1] if y1 is None else y1
    dot = g['dot_m']
    ix0, ix1 = 0, gp['footfall'].shape[1]
    iy0, iy1 = int((y0 - ys_all[0]) / dot), int((y1 - ys_all[0]) / dot)
    sl = (slice(iy0, iy1), slice(ix0, ix1))
    h, w = iy1 - iy0, ix1 - ix0
    img = np.zeros((h, w, 3), np.float32)
    has = height[sl]
    img[has] = (0.30, 0.30, 0.30)                                           # ground (grey)
    rub = gp['rubbish_heap'][sl]
    img[..., 0] = np.where(has, img[..., 0] + 0.22 * rub, img[..., 0])      # rubbish (brown)
    img[..., 1] = np.where(has, img[..., 1] + 0.10 * rub, img[..., 1])
    zone = {'footfall': gp['footfall'][sl] >= 0.6, 'crown': gp['crown'][sl] >= 0.7, 'keepclear': gp['keepclear'][sl] >= 0.5}
    img = img[..., ::-1].copy()                                             # now BGR
    tint = lambda mask, bgr, a: np.where(mask[..., None], img * (1 - a) + np.array(bgr, np.float32) * a, img)   # noqa: E731
    img = tint(zone['keepclear'] & has, (0.10, 0.10, 0.85), 0.55)
    img = tint(zone['footfall'] & has, (0.10, 0.60, 0.95), 0.45)
    img = tint(zone['crown'] & has, (0.95, 0.35, 0.10), 0.60)
    img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    img = np.flipud(img)                                                     # y up on the picture
    img = cv2.resize(img, (int(w * dot * scale), int(h * dot * scale)), interpolation=cv2.INTER_NEAREST)

    def to_px(x, y):
        return int((x - x0) * scale), int((y1 - y) * scale)
    for r in rows:
        if not (y0 <= r['y'] <= y1):
            continue
        colour = (60, 200, 60) if r['kind'].startswith('weed') else (230, 200, 40)
        radius = max(3, int(r['size_m'] * 0.5 * scale))
        cv2.circle(img, to_px(r['x'], r['y']), radius, colour, -1, cv2.LINE_AA)
        cv2.circle(img, to_px(r['x'], r['y']), radius, (255, 255, 255), 1, cv2.LINE_AA)
    # the camera and the pieces distance
    cx, cy = to_px(cam[0], cam[1])
    cv2.drawMarker(img, (cx, cy), (255, 255, 255), cv2.MARKER_TRIANGLE_UP, 14, 2)
    dist = float(data.get('calibration', {}).get('distance', 18.0)) if False else 18.0
    cv2.circle(img, (cx, cy), int(dist * scale), (255, 255, 255), 1, cv2.LINE_AA)
    for fx, fy in data.get('fire_points', []):
        cv2.circle(img, to_px(fx, fy), int(1.0 * scale), (0, 0, 255), 2, cv2.LINE_AA)
    # ruler and legend
    for m in range(int(np.ceil(y0 / 5.0) * 5), int(y1) + 1, 5):
        p = to_px(x0, m)
        cv2.line(img, (0, p[1]), (14, p[1]), (255, 255, 255), 1)
        cv2.putText(img, f'{m} m', (18, p[1] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
    legend = [('weed', (60, 200, 60)), ('moss cushion', (230, 200, 40)), ('crown (blue)', (240, 90, 25)), ('trodden lane (orange)', (25, 150, 240)), ('keep clear (red)', (25, 25, 215)), ('rubbish (brown tint)', (70, 100, 150))]
    pad = 170
    canvas = np.zeros((img.shape[0], img.shape[1] + pad, 3), np.uint8)
    canvas[:, :img.shape[1]] = img
    for i, (label, colour) in enumerate(legend):
        cv2.rectangle(canvas, (img.shape[1] + 8, 14 + 24 * i), (img.shape[1] + 24, 28 + 24 * i), colour, -1)
        cv2.putText(canvas, label, (img.shape[1] + 30, 27 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(canvas, title or f'{len(rows)} plants', (img.shape[1] + 8, 14 + 24 * len(legend) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(out_path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 88])
    in_window = [r for r in rows if y0 <= r['y'] <= y1]
    area = float(has.sum() * dot * dot)
    zones = mz.pieces_test(gp, manifest, rows, [tuple(p) for p in data.get('fire_points', [])], [])
    json.dump(dict(plants_drawn=len(in_window), ground_area_m2=round(area, 1), plants_per_m2=round(len(in_window) / max(area, 1e-6), 3), zone_counts=zones['counts']), open(os.path.splitext(out_path)[0] + '.json', 'w'))
    return out_path


def pack_has(manifest):
    from masks import pack as pack_module
    height = pack_module.read_png(os.path.join(manifest['_dir'], 'gp_height.png'))
    return height[..., 1] > 0.5


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    draw(args[0], args[1], args[2], args[3], float(opts['--y0']) if '--y0' in opts else None, float(opts['--y1']) if '--y1' in opts else None, float(opts.get('--scale', 28)))
