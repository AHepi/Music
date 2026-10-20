# What this does (plain words): turns the analysis results into DESCRIPTION files (the small json files the wood generator is driven by) and measures their size.
# It writes the traced layer ("patches": flat coloured outlines found by joining the least-different neighbours, see merge_trace.py) in the compact
# form the generator reads: each patch is [palette colour, [x0, y0, dx1, dy1, ...]] (the first corner, then small steps). Plain Python (python3 -I).
# It READS the reference picture (analysis); the generator does not.
import json
import os
import pickle
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import merge_trace as mt  # noqa: E402
import trace_tools as tt  # noqa: E402

DEFAULT_MAPS = {'height': {'grey_low': 12.0, 'grey_high': 128.0, 'blur': 0.5}, 'normal': {'strength': 8}}


def load_reference():
    return cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))


def load_merge_state(bgr, cache_folder=os.path.join(HERE, 'merge_ladder'), wrap=False):
    """wrap=True: neighbours across the tile edge may be joined (patches that cross the edge keep ONE colour: no colour seam). wrap=False: used for the statistics."""
    comp, lab = mt.initial_regions(bgr, colour_count=32)
    tree_path = os.path.join(cache_folder, 'tree.pkl' if wrap else 'tree_nowrap.pkl')
    if os.path.exists(tree_path):
        tree = pickle.load(open(tree_path, 'rb'))
    else:
        os.makedirs(cache_folder, exist_ok=True)
        tree = mt.build_merge_tree(comp, lab, wrap=wrap)
        pickle.dump(tree, open(tree_path, 'wb'))
    return comp, lab, tree


def traced_regions(bgr, state, patch_count, palette_size=96, epsilon=1.0):
    """Returns (regions, palette_rgb list) for about `patch_count` patches: regions = [{'c', 'p', 'a'}] big to small."""
    comp, lab, tree = state
    region_labels, count = mt.labels_at(comp, tree, patch_count)
    means, area = mt.region_colours(region_labels, lab, count)
    centres, index = mt.squeeze_palette(means, area, palette_size)
    regions = mt.trace_labelled_regions(region_labels, count, index, epsilon)
    palette_bgr = tt.palette_to_bgr(centres)
    return regions, [[int(c[2]), int(c[1]), int(c[0])] for c in palette_bgr]


def sort_palette_dark_to_light(palette_rgb, regions):
    """Renumber palette colours from dark to light (a tidier file) and rewrite the regions' colour numbers."""
    grey = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in palette_rgb]
    order = sorted(range(len(palette_rgb)), key=lambda i: grey[i])
    new_index = {old: new for new, old in enumerate(order)}
    for r in regions:
        r['c'] = new_index[r['c']]
    return [palette_rgb[i] for i in order]


def patches_layer(regions):
    return {'type': 'patches', 'list': [[r['c'], tt.delta_encode(r['p'])] for r in regions]}


def traced_description(regions, palette_rgb, note=''):
    """A complete wood description holding only traced patches (the "tracing" end of the ladder)."""
    palette_rgb = sort_palette_dark_to_light(palette_rgb, regions)
    return {'format': 'wood-v1', 'note': note, 'tile': 1254, 'palette': palette_rgb, 'ground': 0, 'grow': 0.5, 'maps': DEFAULT_MAPS,
            'layers': [patches_layer(regions)]}


def write_description(description, path):
    text = json.dumps(description, separators=(',', ':'))
    with open(path, 'w') as handle:
        handle.write(text)
    return len(text.encode())
