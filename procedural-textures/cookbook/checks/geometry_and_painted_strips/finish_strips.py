# What this does (plain Python, run outside Blender with python3 -I):
#   1. MEASURES the outline-band test of make_painted_strips.py: for every "share" setting it finds the patch edge (where the soft mask
#      crosses 0.5), the dark line dots, and how wide the line is at each point of the edge. Numbers go to numbers_painted.json.
#   2. Re-joins the strips made by lib/make_strip.py with a white gap between the squares (so a join is never mistaken for a crack)
#      and saves them as small JPG pictures in cookbook/pictures/ with plain names.
#   3. Makes small JPG copies (under about 300 KB) of large existing research pictures that the two new guides show, also in cookbook/pictures/.
# Nothing outside cookbook/ is changed; the large originals stay where they are.
# Use: python3 -I finish_strips.py
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WORK = os.path.join(HERE, 'work')
PICTURES = os.path.join(PROC, 'cookbook', 'pictures')
RESEARCH = os.path.join(PROC, 'research')
GEO = os.path.join(RESEARCH, 'experiments_geometry_nodes_curves_modifiers_physics', 'out')
HP = os.path.join(RESEARCH, 'experiments_hand_painted_look', 'pictures')
DARK = np.array([43, 32, 27])           # '#2b201b' as red, green, blue


def save_small_jpg(image, path, max_width=1300, max_bytes=300_000):
    if image.shape[1] > max_width:
        scale = max_width / image.shape[1]
        image = cv2.resize(image, (max_width, int(round(image.shape[0] * scale))), interpolation=cv2.INTER_AREA)
    for quality in (90, 85, 80, 75, 70, 62, 55):
        ok, data = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if len(data) <= max_bytes:
            break
    with open(path, 'wb') as handle:
        handle.write(data.tobytes())
    return {'file': os.path.relpath(path, PROC), 'bytes': int(len(data)), 'jpeg_quality': quality, 'width': int(image.shape[1]), 'height': int(image.shape[0])}


def with_gaps(strip_path, cell=256, header=40, gap=8):
    """lib/make_strip.py joins squares edge to edge; put a white gap between them (title row kept)."""
    image = cv2.imread(strip_path)
    title, body = image[:header], image[header:]
    count = body.shape[1] // cell
    pieces = []
    for index in range(count):
        pieces.append(body[:, index * cell:(index + 1) * cell])
        if index < count - 1:
            pieces.append(np.full((body.shape[0], gap, 3), 255, np.uint8))
    body = np.hstack(pieces)
    title = np.hstack([title, np.full((header, body.shape[1] - title.shape[1], 3), 255, np.uint8)])
    return np.vstack([title, body])


def measure_outline_band():
    folder = os.path.join(WORK, 'outline_band_measure')
    info = json.load(open(os.path.join(folder, 'renders.json')))
    size = info['size']
    to_1254 = 1254.0 / size
    results = {'how': ('512-dot renders, 1 sample. Patch edge = dots where the soft mask crosses 0.5 (compared with the right and the lower '
                       'neighbour, wrapping round). Line dot = a dot painted the dark colour #2b201b (within 6 steps). Local line width at an edge dot '
                       '= 2 x (distance from that dot to the nearest non-line dot) - 1, measured on a wrap-padded copy (exact for odd widths, '
                       'about 1 dot short for even ones). Island dots = line dots more than 8 dots (of 512) from any patch edge.'),
               'size': size, 'samples': info['samples'], 'softness': info['softness'], 'shares': {}}
    for share in info['shares']:
        colour = cv2.imread(os.path.join(folder, f'share_{share}_colour.png'))[..., ::-1].astype(int)
        mask = cv2.imread(os.path.join(folder, f'share_{share}_height.png'), cv2.IMREAD_UNCHANGED)[..., 0].astype(float) / 65535.0
        side = mask > 0.5
        edge = (side != np.roll(side, -1, axis=1)) | (side != np.roll(side, -1, axis=0))
        line = (np.abs(colour - DARK).max(axis=-1) <= 6)
        pad = 32
        line_padded = np.pad(line.astype(np.uint8), pad, mode='wrap')
        inside = cv2.distanceTransform(line_padded, cv2.DIST_L2, 5)[pad:-pad, pad:-pad]
        not_edge_padded = np.pad((~edge).astype(np.uint8), pad, mode='wrap')
        from_edge = cv2.distanceTransform(not_edge_padded, cv2.DIST_L2, 5)[pad:-pad, pad:-pad]
        covered = edge & line
        widths = 2.0 * inside[covered] - 1.0
        entry = {'share_of_picture_dark': round(float(line.mean()), 4), 'edge_dots': int(edge.sum()),
                 'share_of_edge_dots_with_a_line': round(float(covered.sum() / max(1, edge.sum())), 3),
                 'island_share_of_line_dots': round(float((line & (from_edge > 8)).sum() / max(1, line.sum())), 3)}
        if covered.sum():
            p10, p50, p90 = np.percentile(widths, [10, 50, 90])
            entry.update({'width_at_edge_dots_512': {'p10': round(float(p10), 1), 'median': round(float(p50), 1), 'p90': round(float(p90), 1),
                                                       'max': round(float(widths.max()), 1)},
                          'width_in_dots_of_a_1254_tile': {'p10': round(float(p10 * to_1254), 1), 'median': round(float(p50 * to_1254), 1),
                                                           'p90': round(float(p90 * to_1254), 1)},
                          'mean_width_estimate_512_line_dots_per_edge_dot': round(float(line.sum() / max(1, edge.sum())), 2)})
        results['shares'][str(share)] = entry
    return results


if __name__ == '__main__':
    numbers = {'outline_band': measure_outline_band(), 'pictures_written': []}
    os.makedirs(PICTURES, exist_ok=True)
    strips = [
        ('relax_steps_strip.png', 'geometry-strip-relax-steps.jpg'),
        ('groove_width_strip.png', 'geometry-strip-groove-width.jpg'),
        ('ridge_radius_strip.png', 'geometry-strip-curve-ridge-radius.jpg'),
        ('set_material_strip.png', 'geometry-trap-set-material.jpg'),
        ('outline_band_share_strip.png', 'painted-strip-outline-band-share.jpg'),
        ('outline_band_softness_strip.png', 'painted-strip-outline-band-softness.jpg'),
    ]
    for source, target in strips:
        numbers['pictures_written'].append(save_small_jpg(with_gaps(os.path.join(WORK, source)), os.path.join(PICTURES, target), max_width=1400))
    copies = [
        (os.path.join(GEO, 'overview_all_recipes.png'), 'geometry-overview-all-recipes.jpg', 1100),
        (os.path.join(GEO, 't05_modifiers_sheet.png'), 'geometry-modifiers-from-above.jpg', 1024),
        (os.path.join(GEO, 't07_wrap_sheet.png'), 'geometry-wrap-test-sheet.jpg', 1024),
        (os.path.join(HP, 'c05_outline_methods_sheet.png'), 'painted-outline-methods-sheet.jpg', 1300),
        (os.path.join(HP, 'c06_kuwahara_aniso_size.png'), 'painted-kuwahara-anisotropic-size.jpg', 1300),
        (os.path.join(HP, 'c06_kuwahara_classic.png'), 'painted-kuwahara-classic-size.jpg', 1300),
        (os.path.join(HP, 'c08_seam_fix_sheet.png'), 'painted-filter-seam-and-wrap-padding.jpg', 1300),
        (os.path.join(HP, 'c12_slate_demo_stages.png'), 'painted-slate-demo-stages.jpg', 1300),
        (os.path.join(HP, 'c17_gravel_demo_stages.png'), 'painted-gravel-demo-stages.jpg', 1300),
        (os.path.join(HP, 'a02_posterise_reference_all.png'), 'painted-references-in-4-8-16-32-colours.jpg', 1300),
    ]
    for source, target, width in copies:
        image = cv2.imread(source)
        entry = save_small_jpg(image, os.path.join(PICTURES, target), max_width=width)
        entry['copied_from'] = os.path.relpath(source, PROC)
        numbers['pictures_written'].append(entry)
    with open(os.path.join(HERE, 'numbers_painted.json'), 'w') as handle:
        json.dump(numbers, handle, indent=1)
    print(json.dumps(numbers, indent=1))
