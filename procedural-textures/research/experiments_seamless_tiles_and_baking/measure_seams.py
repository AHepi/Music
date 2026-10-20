# What this does: measures whether each grey picture in a folder tiles without a visible seam, and draws a contact sheet.
# For every picture it prints:
#   seam_ratio   the project's own measure (lib/texture_compare.py): jump across the wrap-around edge divided by the usual jump between
#                neighbouring pixels. About 1.0 = seamless. 2 or more = a seam you can see.
#   seam_x/seam_y the same, only for the left-right edge and only for the top-bottom edge (tells you which direction is broken)
#   seam_peak    the same idea but using the 95th-percentile jump, so a seam that only touches some rows (like half bricks) still shows
#   spread       the standard deviation of the picture (shows contrast lost by blending)
#   mirror_tell  how alike the picture is to its own mirror image (1.0 = a perfect mirror: a giveaway of mirror tiling)
# The contact sheet shows each picture shifted by half a tile, so the wrap-around edge sits in the middle as a cross: if the pattern is
# seamless you see no cross.
# Run (plain Python):  python3 -I measure_seams.py PICTURE_FOLDER OUT_JSON OUT_SHEET_PNG [columns]
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import texture_compare as tc  # noqa: E402


def load_grey(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image.ndim == 3:
        image = image[..., :3].mean(axis=-1)
    image = image.astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def measure(grey):
    inner_x = np.abs(np.diff(grey, axis=1))
    inner_y = np.abs(np.diff(grey, axis=0))
    wrap_x = np.abs(grey[:, 0] - grey[:, -1])
    wrap_y = np.abs(grey[0, :] - grey[-1, :])
    eps = 1e-9
    flipped = grey[:, ::-1]
    mirror = float(np.corrcoef(grey.ravel(), flipped.ravel())[0, 1]) if grey.std() > 0 else 0.0
    return {
        'seam_ratio': round(tc.seam_ratio(grey), 2),
        'seam_x': round(float(wrap_x.mean() / max(inner_x.mean(), eps)), 2),
        'seam_y': round(float(wrap_y.mean() / max(inner_y.mean(), eps)), 2),
        'seam_peak': round(float(max(np.percentile(wrap_x, 95) / max(np.percentile(inner_x, 95), eps),
                                     np.percentile(wrap_y, 95) / max(np.percentile(inner_y, 95), eps))), 2),
        'spread': round(float(grey.std()), 3),
        'mirror_tell': round(mirror, 2),
    }


def sheet(names, greys, results, out_path, columns=6, cell=220):
    tiles = []
    for name in names:
        half = np.roll(greys[name], (greys[name].shape[0] // 2, greys[name].shape[1] // 2), axis=(0, 1))
        picture = cv2.resize((np.clip(half, 0, 1) * 255).astype(np.uint8), (cell, cell), interpolation=cv2.INTER_AREA)
        picture = cv2.cvtColor(picture, cv2.COLOR_GRAY2BGR)
        banner = np.full((44, cell, 3), 245, np.uint8)
        cv2.putText(banner, name[:30], (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (20, 20, 20), 1, cv2.LINE_AA)
        r = results[name]
        colour = (0, 120, 0) if r['seam_ratio'] < 1.5 else (0, 0, 200)
        cv2.putText(banner, f"seam {r['seam_ratio']}  peak {r['seam_peak']}", (4, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, colour, 1, cv2.LINE_AA)
        tiles.append(np.vstack([banner, picture]))
    while len(tiles) % columns:
        tiles.append(np.full_like(tiles[0], 255))
    rows = [np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)]
    cv2.imwrite(out_path, np.vstack(rows))


def main():
    folder, out_json, out_sheet = sys.argv[1], sys.argv[2], sys.argv[3]
    columns = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    names = sorted(f[:-4] for f in os.listdir(folder) if f.endswith('.png'))
    order = None
    if os.path.exists(os.path.join(folder, 'order.txt')):
        order = [l.strip() for l in open(os.path.join(folder, 'order.txt')) if l.strip()]
        names = [n for n in order if n in names] + [n for n in names if n not in order]
    greys = {n: load_grey(os.path.join(folder, n + '.png')) for n in names}
    results = {n: measure(greys[n]) for n in names}
    with open(out_json, 'w') as handle:
        json.dump(results, handle, indent=1)
    sheet(names, greys, results, out_sheet, columns)
    print(f"{'picture':42s} seam_ratio seam_x seam_y seam_peak spread mirror_tell")
    for n in names:
        r = results[n]
        print(f"{n:42s} {r['seam_ratio']:9} {r['seam_x']:6} {r['seam_y']:6} {r['seam_peak']:9} {r['spread']:6} {r['mirror_tell']:6}")


if __name__ == '__main__':
    main()
