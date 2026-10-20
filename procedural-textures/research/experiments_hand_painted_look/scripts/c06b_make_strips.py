# What this does (plain python): joins the compositor sweep pictures from c06_compositor_sweeps.py into labelled strips (each tile is a 420 x 420 crop of the
# 1254 x 1254 result, shown at 300 x 300), with the untouched source crop first in every row.
import os, json, cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.abspath(os.path.join(HERE, '..'))
SWEEP = os.path.join(BASE, 'pictures', 'c06_compositor')
manifest = json.load(open(os.path.join(BASE, 'data', 'c06_compositor_sweeps.json')))['manifest']
timings = json.load(open(os.path.join(BASE, 'data', 'c06_compositor_sweeps.json')))['timings_seconds_at_1254']
Y0, X0, S, SHOW = 420, 420, 420, 300
def tile(path, label):
    im = cv2.imread(path)[Y0:Y0 + S, X0:X0 + S]
    im = cv2.resize(im, (SHOW, SHOW), interpolation=cv2.INTER_AREA)
    band = np.full((26, SHOW, 3), 245, np.uint8)
    cv2.putText(band, label[:38], (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([band, im])
source_tile = tile(os.path.join(SWEEP, 'source_grainy.png'), 'source (before)')
def row(folder, title):
    tiles = [source_tile] + [tile(os.path.join(SWEEP, folder, m['file']), m['label'] + (f"  ({timings.get(folder + '/' + m['label'], 0):.1f}s)" if timings.get(folder + '/' + m['label'], 0) > 1.0 else '')) for m in manifest[folder]]
    return title, tiles
def figure(rows, out, per_row=7):
    blocks = []
    for title, tiles in rows:
        for i in range(0, len(tiles), per_row):
            chunk = tiles[i:i + per_row]
            while len(chunk) < per_row: chunk.append(np.full_like(tiles[0], 255))
            line = np.hstack(chunk)
            if i == 0:
                head = np.full((34, line.shape[1], 3), 255, np.uint8); cv2.putText(head, title, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA); line = np.vstack([head, line])
            blocks.append(line)
    cv2.imwrite(os.path.join(BASE, 'pictures', out), np.vstack(blocks)); print(out)
figure([row('classic_size', 'Kuwahara Classic: Size (pixels at 1254)'), row('classic_precision', 'Kuwahara Classic: High Precision off / on (Size 8)'), row('classic_iterations', 'Kuwahara Classic: chained passes (Size 4)')], 'c06_kuwahara_classic.png')
figure([row('aniso_size', 'Kuwahara Anisotropic: Size (times in brackets)'), row('aniso_iterations', 'Anisotropic: chained passes (Size 6)')], 'c06_kuwahara_aniso_size.png')
figure([row('aniso_uniformity', 'Anisotropic (Size 8): Uniformity'), row('aniso_sharpness', 'Anisotropic (Size 8): Sharpness'), row('aniso_eccentricity', 'Anisotropic (Size 8): Eccentricity')], 'c06_kuwahara_aniso_settings.png')
figure([row('posterize', 'Posterize (per colour channel)'), row('pixelate', 'Pixelate Size'), row('bilateral', 'Bilateral Blur'), row('blur_types', 'Blur node Type (Size 6)'), row('filter_types', 'Filter node Type'), row('despeckle', 'Despeckle (Color Threshold)')], 'c06_other_nodes.png')
