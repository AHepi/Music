# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# STAMPS two pictures that only a render can make onto a scene's finished PACK, in plain Python (numpy + OpenCV), without redoing the geometry (so it needs neither Blender nor the
# reader's raw arrays):
#     python3 -I masks/stamp_pack.py SET_ID SCENE_ID [--puddles PLAN_PICTURE.png [--puddle_margin_m 0.03] [--puddle_threshold 0.5]] [--litter PLAN_PICTURE.png [--litter_points POINTS.json] [--litter_max_m 0.25]]
#   --puddles  the runner's view `plan:puddles` (the earlier water layer's puddle mask seen straight down over the ground bounds, red = standing water, drawn in the wet state the plate
#              uses). It is widened by puddle_margin_m (a plant does not stand at the very edge of a puddle) and written into the `above_water` mask (alpha of gp_c.png) as
#              above_water = 0 inside a puddle and 1 outside (a pond's own value stays where it is lower). Everything that already reads `above_water` (the growth layer: nothing grows
#              under water) then keeps plants out of puddles too. Only sets that have a water layer with puddles need this.
#   --litter   the runner's view `plan:litter` (the 3D litter pieces of the objects the set names in growth.avoid_pieces_of seen straight down, white = a piece; the runner also writes
#              plan_litter_points.json, the centre of every piece: a piece thinner than a dot is lost in the picture but not there). It becomes the new
#              mask `litter_dist` (picture gp_h.png, 2 cm dots like gp_fine): the distance in metres to the nearest litter piece, 0 .. litter_max_m scaled to 0..1 (1 = far). The growth
#              layer reads this picture instead of asking every one of tens of thousands of pieces for its nearest point at drawing time (which cost +70 percent of a plate).
# Stamping puddles twice only widens them (the old value stays): to change margin or threshold, put the pack's gp_c.png and manifest.json back first (or rebuild the pack).
# Both are only valid for the state they were drawn in (the puddle amount of the plate, the litter amount and seed): draw them again when those change.
# The pack's manifest.json is updated (`stamped` records the source pictures and the numbers used) and the mask statistics of above_water are refreshed.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

import numpy as np  # noqa: E402

from masks import pack as pack_module  # noqa: E402


def read_plan_red(path):
    """The red channel of a plan picture as floats 0..1 with row 0 = the LOW end of y (the file's first row is the high end)."""
    import cv2
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    scale = 65535.0 if im.dtype == np.uint16 else 255.0
    red = im[..., 2] if im.ndim == 3 else im
    return np.flipud(red.astype(np.float32) / scale)


def stamp_puddles(out_dir, manifest, picture, margin_m, threshold=0.5):
    import cv2
    grid = manifest['ground']
    dot = float(grid['dot_m'])
    w, h = grid['size']
    red = read_plan_red(picture)
    # the picture is drawn at some resolution over the same bounds; bring it to the pack's own dots with the largest value in each dot (a thin puddle edge is kept)
    big = cv2.resize(red, (w * 4, h * 4), interpolation=cv2.INTER_AREA)
    puddle = (big > threshold).astype(np.uint8)
    reach = max(int(round(margin_m / (dot / 4.0))), 0)
    if reach > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * reach + 1, 2 * reach + 1))
        puddle = cv2.dilate(puddle, kernel)
    cell = cv2.resize(puddle.astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
    wet = (cell > 0.2).astype(np.float32)
    path = os.path.join(out_dir, manifest['pictures']['gp_c']['file'])
    gp_c = pack_module.read_png(path)                                 # (h, w, 4): R slope, G lowness, B crown, A above_water
    before = gp_c[..., 3].copy()
    has = pack_module.read_png(os.path.join(out_dir, manifest['pictures']['gp_height']['file']))[..., 1] > 0.5
    gp_c[..., 3] = np.minimum(before, 1.0 - wet * has)
    pack_module.write_png(path, gp_c, 8)
    stats = dict(min=float(gp_c[..., 3].min()), max=float(gp_c[..., 3].max()), mean=float(gp_c[..., 3].mean()))
    manifest.setdefault('mask_stats', {})['above_water'] = stats
    return dict(source=os.path.abspath(picture), margin_m=margin_m, threshold=threshold, puddle_share_of_ground=round(float((wet * has).sum() / max(has.sum(), 1)), 4), above_water_mean=stats['mean'])


def stamp_litter(out_dir, manifest, picture, max_m, points=None, point_r=0.015):
    """litter_dist from the plan picture (white shapes) and, when given, the pieces' own centres ([[x, y], ...] drawn as discs of point_r metres: a piece thinner than a dot of the picture is
    lost there but its centre is known). The distance is made at the picture's own resolution and brought to the fine grid with the smallest value of each block."""
    import cv2
    fine = manifest['ground']['fine']
    dot = float(fine['dot_m'])
    w, h = fine['size']
    red = read_plan_red(picture)
    ph, pw = red.shape
    piece = (red > 0.05).astype(np.uint8)
    npoints = 0
    if points:
        gx, gy = manifest['ground']['x'], manifest['ground']['y']
        r_px = max(int(round(point_r / ((gx[1] - gx[0]) / pw))), 1)
        for x, y in points:
            ix, iy = int((x - gx[0]) / (gx[1] - gx[0]) * pw), int((y - gy[0]) / (gy[1] - gy[0]) * ph)
            if 0 <= ix < pw and 0 <= iy < ph:
                cv2.circle(piece, (ix, iy), r_px, 1, -1)
                npoints += 1
    src_dot = (manifest['ground']['x'][1] - manifest['ground']['x'][0]) / pw
    dist_m = cv2.distanceTransform((1 - piece).astype(np.uint8), cv2.DIST_L2, 5) * src_dot
    if (ph, pw) != (h, w):
        if ph % h == 0 and pw % w == 0:
            dist_m = dist_m.reshape(h, ph // h, w, pw // w).min(axis=(1, 3))
        else:
            dist_m = cv2.resize(dist_m, (w, h), interpolation=cv2.INTER_AREA)
    arr = np.clip(dist_m / max(max_m, 1e-3), 0.0, 1.0).astype(np.float32)
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., 0] = arr
    rgba[..., 3] = 1.0
    path = os.path.join(out_dir, 'gp_h.png')
    size = pack_module.write_png(path, rgba, 8)
    manifest['pictures']['gp_h'] = dict(file='gp_h.png', frame='GP', grid='fine', bits=8, channels=dict(R='litter_dist'), max_m=max_m)
    manifest['masks']['GP']['litter_dist'] = dict(picture='gp_h', channel='R', frame='GP', unit='metres / max_m')
    manifest.setdefault('mask_stats', {})['litter_dist'] = dict(min=float(arr.min()), max=float(arr.max()), mean=float(arr.mean()))
    return dict(source=os.path.abspath(picture), max_m=max_m, piece_share_of_picture=round(float(piece.mean()), 4), centres_drawn=npoints, centre_disc_m=point_r, bytes=size)


def main(argv):
    flags = {}
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            flags[a] = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else True
            i += 2 if flags[a] is not True else 1
        else:
            pos.append(a)
            i += 1
    set_id, scene_id = pos[0], pos[1]
    out_dir = pack_module.pack_dir(KIT_ROOT, set_id, scene_id)
    manifest_path = os.path.join(out_dir, 'manifest.json')
    manifest = json.load(open(manifest_path))
    record = manifest.setdefault('stamped', {})
    if '--puddles' in flags:
        record['puddles'] = stamp_puddles(out_dir, manifest, flags['--puddles'], float(flags.get("--puddle_margin_m", 0.03)), float(flags.get('--puddle_threshold', 0.5)))
        record['puddles']['at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        print('puddles stamped', record['puddles'])
    if '--litter' in flags:
        points = json.load(open(flags['--litter_points'])) if '--litter_points' in flags else None
        record['litter'] = stamp_litter(out_dir, manifest, flags['--litter'], float(flags.get('--litter_max_m', 0.25)), points)
        record['litter']['at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        print('litter stamped', record['litter'])
    json.dump(manifest, open(manifest_path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
