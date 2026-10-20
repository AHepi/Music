# What this does (plain words): assembles the DESCRIPTION files for the wood reference from the analysis results (layout_fit.json, cracks_fitted.json, the paint
# model, the traced patches). Each description is a layered list; the generator draws the layers back to front. The ladder it builds:
#   S0  layout only        : 16 colours, 5 boards with their gaps, long cracks, 4 knots, splatter clouds, pebbles   (flat colour per board; no paint)
#   S1  + statistical paint: S0 + "stamps" (random horizontal ragged patches drawn from a fitted model) + fine speckle   (still procedural: invented paint)
#   M   + traced patches   : S0 layout, then the biggest traced patches on top (what the picture actually does at the large scale)
#   L   traced patches     : many traced patches (the whole picture traced; this is "tracing", not procedural generation)
# Plain Python (python3 -I). Reads analysis results (which were made by reading the reference); the generator never reads the reference.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import describe_tools as dt  # noqa: E402
import trace_tools as tt  # noqa: E402

MAPS = {'height': {'grey_low': 12.0, 'grey_high': 128.0, 'blur': 0.5}, 'normal': {'strength': 8}}


def lab_to_rgb(lab):
    bgr = cv2.cvtColor(np.array([[lab]], np.float32), cv2.COLOR_Lab2BGR)[0, 0]
    return [int(round(float(np.clip(c, 0, 1)) * 255)) for c in bgr[::-1]]


def make_s_palette(bgr=None, size=16):
    """The 16-colour palette of the paint model (written by fit_paint_model.py): rgb list and Lab array, dark to light."""
    data = json.load(open(os.path.join(HERE, 'palette16.json')))
    return data['palette_rgb'], np.array(data['palette_lab'])


def nearest(palette_lab, lab):
    d = ((palette_lab - np.asarray(lab)) ** 2).sum(axis=1)
    return int(np.argmin(d))


def layout_layers(fit, cracks, palette_lab, crack_count=25, with_blobs=True, with_pebbles=True, with_stamps=None, with_planks=True, cloud_count=40, waves=None):
    """The layout layers shared by every class, in painting order: plank_rows (boards from wave-form gap lines), [stamps], blobs, cracks, gap_ribbons, knots, pebbles.
    Compact on purpose (the gap lines are written as a few waves, splatter clouds as short rows) so that the layout alone fits in a few kilobytes."""
    layers = []
    waves = waves or json.load(open(os.path.join(HERE, 'gap_waves.json')))
    board_colours = [nearest(palette_lab, lab) for lab in fit['board_mean_lab']]
    if with_planks:
        layers.append({'type': 'plank_rows', 'gaps': waves, 'colours': board_colours})
    if with_stamps:
        layers.append(with_stamps)
    darkest = 0
    if with_blobs:
        rust = [nearest(palette_lab, l) for l in fit['blob_stats']['rust_palette_lab']]
        layers.append({'type': 'blobs', 'seed': 5, 'colours': rust, 'cloud_list': [[c['x'], c['y'], c['n'], c['spread_x'], c['spread_y'], max(c['r_min'], 1.5), max(c['r_max'], 2.5)] for c in fit['blob_clouds'][:cloud_count]]})
    layers.append({'type': 'cracks', 'list': [{'c': darkest, 'pts': l['pts']} for l in cracks[:crack_count]]})
    layers.append({'type': 'gap_ribbons', 'colour': darkest, 'width_scale': 1.15})
    knots = []
    for k in fit['knots']:
        rings = [nearest(palette_lab, [r[0], r[1], r[2]]) for r in reversed(k['ring_lab_outer_last'])]       # outer first
        knots.append({'x': k['x'], 'y': k['y'], 'rx': k['rx'], 'ry': k['ry'], 'rings': rings, 'ragged': 0.05, 'seed': 11 + k['x'] % 7, 'core': 3.5, 'core_colour': darkest})
    layers.append({'type': 'knots', 'list': knots})
    if with_pebbles:
        grey = nearest(palette_lab, [24, 3, 3])
        light = nearest(palette_lab, [38, 4, 6])
        layers.append({'type': 'pebbles', 'seed': 7, 'rows': [{'gap': p['gap'], 'x0': p['x_min'], 'x1': p['x_max'], 'r': [round(p['radius_median'] * 0.7, 1), round(p['radius_median'] * 1.4, 1)],
                                                              'colours': [grey, light]} for p in fit['pebbles'] if p['count'] > 0]})
    return layers


def base_description(palette, note):
    return {'format': 'wood-v1', 'note': note, 'tile': 1254, 'palette': palette, 'ground': 0, 'grow': 0.5, 'maps': MAPS, 'layers': []}


def write(description, path):
    return dt.write_description(description, path)
