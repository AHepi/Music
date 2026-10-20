# What this does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------
# It turns the pictures that the image generator painted (the "originals": sheets of separate moss clumps and chips) into
# clean MASKS and then cuts them into an ATLAS: one picture made of a grid of equal-sized cells, one separate stamp in each cell.
#   mask  = a grey picture: white where the shape is, black where it is not, soft over about a dot at the edge.
#   atlas = the grid of stamps (a "stamp" is one shape, cut out and centred in its own cell).
# The recipe (slate_copy/layers/stamps.py) reads the atlas as a picture: red = the mask, green = how deep inside the shape a dot is
# (0 at the rim, 1 about 20 atlas dots in), blue = the same mask again.
#
# Steps for every sheet:
#   1. find the background colour (plain black, or cream for one sheet) and turn "how different from the background" into a soft mask;
#   2. remove specks (tiny bits smaller than a few dots);
#   3. join pieces that belong together (drips and flecks close to a clump) by growing the mask a little, and label every clump/chip;
#   4. cut each one out; for the long ragged chip strips cut them into short pieces and fade the cut ends;
#   5. fit each into one cell (moss clumps: top edge of the clump on the top of the cell, so the recipe can hang them from an upper edge;
#      chips: bottom of the piece on the bottom of the cell, so the recipe can sit them on a lower edge);
#   6. write the atlas and a JSON file that says the cell size and how many stamps there are.
# Run:  python3 -I make_stamps.py          (reads ../stamps/originals, writes ../stamps/cleaned and ../stamps/atlas)
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', 'stamps'))
ORIGINALS = os.path.join(ROOT, 'originals')
CLEANED = os.path.join(ROOT, 'cleaned')
ATLAS = os.path.join(ROOT, 'atlas')


def smoothstep(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def background_colour(rgb):
    border = np.concatenate([rgb[:30].reshape(-1, 3), rgb[-30:].reshape(-1, 3), rgb[:, :30].reshape(-1, 3), rgb[:, -30:].reshape(-1, 3)])
    return np.median(border, axis=0)


def difference_mask(path, lo, hi, green_only=False):
    """Soft mask 0..1 from 'how different is this dot from the plain background' (largest colour step, 0..255).
    green_only: keep only dots whose green is at least as strong as their red and blue (drops a brown rod and a red scribble that came with the moss)."""
    rgb = cv2.imread(path)[..., ::-1].astype(np.float32)
    bg = background_colour(rgb)
    diff = np.abs(rgb - bg).max(axis=2)
    mask = smoothstep(diff, lo, hi)
    if green_only:
        greenish = (rgb[..., 1] >= rgb[..., 0] - 2) & (rgb[..., 1] >= rgb[..., 2] - 2)
        mask = mask * cv2.GaussianBlur(greenish.astype(np.float32), (0, 0), 0.7)
    return mask, rgb


def remove_specks(mask, min_area):
    binary = (mask > 0.5).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    keep = np.zeros(count, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    return mask * keep[labels]


def label_pieces(mask, join_radius, min_area):
    """Label the clumps: the mask is grown by join_radius dots so drips and flecks stay with their clump. Returns labels and stats."""
    grown = cv2.dilate((mask > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * join_radius + 1, 2 * join_radius + 1)))
    count, labels, stats, cents = cv2.connectedComponentsWithStats(grown, connectivity=8)
    pieces = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= min_area]
    # reading order: rows of the 4 x 4 loose grid first, then left to right
    pieces.sort(key=lambda i: (round(cents[i][1] / 330.0), cents[i][0]))
    return labels, stats, pieces


def crop_piece(mask, labels, stats, index, grown_margin=6):
    x, y, w, h = stats[index, :4]
    region = (labels[y:y + h, x:x + w] == index)
    region = cv2.dilate(region.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    return mask[y:y + h, x:x + w] * region


def fit_into_cell(piece, cell_w, cell_h, pad, align):
    """Scale the piece down (never up) so it fits the cell with `pad` dots round it; align 'top' or 'bottom'; centred sideways."""
    h, w = piece.shape
    scale = min((cell_w - 2 * pad) / w, (cell_h - 2 * pad) / h)
    new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    small = cv2.resize(piece, (new_w, new_h), interpolation=cv2.INTER_AREA)
    cell = np.zeros((cell_h, cell_w), np.float32)
    x0 = (cell_w - new_w) // 2
    y0 = pad if align == 'top' else cell_h - pad - new_h
    cell[y0:y0 + new_h, x0:x0 + new_w] = small
    return cell, scale


def soften_and_depth(cell, blur_sigma, depth_reach):
    """Soft edge: a small blur of the mask. Depth: how far inside the shape a dot is (0 at the rim, 1 at depth_reach dots in)."""
    soft = cv2.GaussianBlur(cell, (0, 0), blur_sigma) if blur_sigma > 0 else cell
    soft = np.clip((soft - 0.5) * 1.6 + 0.5, 0, 1) if blur_sigma > 0 else soft          # keep the edge from getting too wide
    inside = (cell > 0.5).astype(np.uint8)
    distance = cv2.distanceTransform(inside, cv2.DIST_L2, 5)
    depth = np.clip(distance / depth_reach, 0, 1).astype(np.float32)
    return soft, depth


def write_atlas(cells, columns, rows, cell_w, cell_h, name, info):
    atlas_r = np.zeros((rows * cell_h, columns * cell_w), np.float32)
    atlas_g = np.zeros_like(atlas_r)
    for k, (soft, depth) in enumerate(cells):
        row, col = divmod(k, columns)
        atlas_r[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w] = soft
        atlas_g[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w] = depth
    rgb = np.stack([atlas_r, atlas_g, atlas_r], axis=-1)
    cv2.imwrite(os.path.join(ATLAS, name + '_atlas.png'), (rgb[..., ::-1] * 255).round().astype(np.uint8))
    cv2.imwrite(os.path.join(ATLAS, name + '_atlas_mask_view.png'), (atlas_r * 255).round().astype(np.uint8))
    info = dict(info, _note='Written by tools/make_stamps.py. Says how the stamp atlas picture is cut: cell size, grid and count. The recipe (layers/stamps.py) reads it. Atlas picture: red = mask, green = depth inside the shape, blue = mask again.', atlas_file=name + '_atlas.png', columns=columns, rows=rows, cell_width=cell_w, cell_height=cell_h,
                cell_aspect_height_over_width=cell_h / cell_w, stamp_count=len(cells), atlas_size=[columns * cell_w, rows * cell_h])
    with open(os.path.join(ATLAS, name + '_atlas.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


def build_clump_atlas(source, name, lo, hi, columns, rows, cell, align, blur_sigma, depth_reach, join_radius=7, min_piece_area=9000, green_only=False, drop_thin_horizontal=0):
    mask, _ = difference_mask(os.path.join(ORIGINALS, source), lo, hi, green_only)
    mask = remove_specks(mask, 60)
    if drop_thin_horizontal:
        # thin level bars (the brown rod the generator hung the moss from) are removed: opening with an upright line as long as drop_thin_horizontal
        # dots deletes everything lower than that, and keeps the body of the moss and its long hanging strands
        opened = cv2.morphologyEx((mask > 0.3).astype(np.uint8), cv2.MORPH_OPEN, np.ones((drop_thin_horizontal, 1), np.uint8))
        allowed = cv2.dilate(opened, np.ones((3, 3), np.uint8), iterations=2).astype(np.float32)
        mask = mask * allowed
        mask = remove_specks(mask, 60)
    cv2.imwrite(os.path.join(CLEANED, name + '_sheet_mask.png'), (mask * 255).round().astype(np.uint8))
    labels, stats, pieces = label_pieces(mask, join_radius, min_piece_area)
    cells, scales, areas = [], [], []
    for index in pieces[:columns * rows]:
        piece = crop_piece(mask, labels, stats, index)
        fitted, scale = fit_into_cell(piece, cell, cell, 6, align)
        cells.append(soften_and_depth(fitted, blur_sigma, depth_reach))
        scales.append(round(float(scale), 3))
        areas.append(float((fitted > 0.5).mean()))
    info = dict(source=source, found_pieces=len(pieces), used=len(cells), shrink_factors=scales, fill_share=[round(a, 3) for a in areas],
                align=align, threshold_low=lo, threshold_high=hi, blur_sigma=blur_sigma, depth_reach=depth_reach)
    return write_atlas(cells, columns, rows, cell, cell, name, info)


def build_strip_atlas(source, name, lo, hi, columns, rows, cell_w, cell_h, blur_sigma, depth_reach, segment_width=330):
    """The chip strips: each long ragged strip is cut into short pieces; the cut ends fade out; each piece sits on the bottom of its cell."""
    mask, _ = difference_mask(os.path.join(ORIGINALS, source), lo, hi)
    mask = remove_specks(mask, 80)
    cv2.imwrite(os.path.join(CLEANED, name + '_sheet_mask.png'), (mask * 255).round().astype(np.uint8))
    labels, stats, pieces = label_pieces(mask, 14, 20000)
    pieces.sort(key=lambda i: stats[i, cv2.CC_STAT_TOP])                       # strips from the top of the sheet down
    cells, info_pieces = [], []
    for index in pieces:
        strip = crop_piece(mask, labels, stats, index)
        h, w = strip.shape
        count = max(1, int(round(w / segment_width)))
        edges = np.linspace(0, w, count + 1).astype(int)
        for a, b in zip(edges[:-1], edges[1:]):
            part = strip[:, a:b].copy()
            if part.sum() < 500:
                continue
            width = part.shape[1]
            ramp = max(8, int(width * 0.12))
            fade = np.ones(width, np.float32)
            fade[:ramp] = np.linspace(0.0, 1.0, ramp)
            fade[-ramp:] = np.linspace(1.0, 0.0, ramp)
            part = part * fade[None, :]
            rows_with_paint = np.where(part.max(axis=1) > 0.5)[0]
            if len(rows_with_paint) == 0:
                continue
            part = part[rows_with_paint[0]:rows_with_paint[-1] + 1]
            fitted, scale = fit_into_cell(part, cell_w, cell_h, 4, 'bottom')
            cells.append(soften_and_depth(fitted, blur_sigma, depth_reach))
            info_pieces.append({'strip': int(len(info_pieces)), 'source_width': int(width), 'source_height': int(part.shape[0]), 'shrink': round(float(scale), 3)})
    cells = cells[:columns * rows]
    info = dict(source=source, found_strips=len(pieces), used=len(cells), pieces=info_pieces[:len(cells)], align='bottom', segment_width=segment_width,
                threshold_low=lo, threshold_high=hi, blur_sigma=blur_sigma, depth_reach=depth_reach)
    return write_atlas(cells, columns, rows, cell_w, cell_h, name, info)


def join_atlases(first, second, name):
    """Put two atlases of the same cell size one above the other (the first one's cells come first)."""
    infos = [json.load(open(os.path.join(ATLAS, n + '_atlas.json'))) for n in (first, second)]
    pictures = [cv2.imread(os.path.join(ATLAS, n + '_atlas.png')) for n in (first, second)]
    joined = np.vstack(pictures)
    views = [cv2.imread(os.path.join(ATLAS, n + '_atlas_mask_view.png'), 0) for n in (first, second)]
    cv2.imwrite(os.path.join(ATLAS, name + '_atlas.png'), joined)
    cv2.imwrite(os.path.join(ATLAS, name + '_atlas_mask_view.png'), np.vstack(views))
    first_info = infos[0]
    info = dict(first_info, _note=first_info.get('_note', ''), source=infos[0]['source'] + ' + ' + infos[1]['source'], atlas_file=name + '_atlas.png', rows=infos[0]['rows'] + infos[1]['rows'],
                used=infos[0]['stamp_count'] + infos[1]['stamp_count'], shrink_factors=infos[0]['shrink_factors'] + infos[1]['shrink_factors'], fill_share=infos[0]['fill_share'] + infos[1]['fill_share'],
                stamp_count=infos[0]['stamp_count'] + infos[1]['stamp_count'], found_pieces=infos[0]['found_pieces'] + infos[1]['found_pieces'],
                atlas_size=[joined.shape[1], joined.shape[0]], joined_from=[first, second])
    with open(os.path.join(ATLAS, name + '_atlas.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


def main():
    os.makedirs(CLEANED, exist_ok=True)
    os.makedirs(ATLAS, exist_ok=True)
    results = {}
    # moss: sheet A (fluffy clumps on black), sheet B (splats on cream)
    results['moss_A'] = build_clump_atlas('moss_sheet_A_flux-dev_seed4101.png', 'moss_A', 22, 55, 4, 4, 256, 'top', 1.0, 28.0)
    results['moss_B'] = build_clump_atlas('moss_sheet_B_flux-dev_seed4103.png', 'moss_B', 30, 80, 4, 4, 256, 'top', 1.0, 28.0)
    results['moss_AB'] = join_atlases('moss_A', 'moss_B', 'moss_AB')
    results['moss_C'] = build_clump_atlas('moss_sheet_C_flux-dev_seed4106.png', 'moss_C', 22, 55, 4, 4, 256, 'top', 0.8, 28.0, join_radius=9, min_piece_area=12000, green_only=True, drop_thin_horizontal=15)
    # chips: sheet A (chunky flakes), sheet B (squarish pieces), sheet C (ragged strips cut into pieces)
    results['chips_A'] = build_clump_atlas('chips_sheet_A_flux-dev_seed4102.png', 'chips_A', 40, 90, 4, 4, 256, 'bottom', 0.8, 14.0)
    results['chips_B'] = build_clump_atlas('chips_sheet_B_flux-dev_seed4104.png', 'chips_B', 40, 90, 4, 4, 256, 'bottom', 0.8, 14.0)
    results['chips_C'] = build_strip_atlas('chips_sheet_C_flux-dev_seed4105.png', 'chips_C', 60, 110, 4, 6, 300, 120, 0.8, 8.0)
    for name, info in results.items():
        print(name, 'pieces found', info.get('found_pieces', info.get('found_strips')), 'stamps used', info['stamp_count'], 'atlas', info['atlas_size'])


if __name__ == '__main__':
    main()
