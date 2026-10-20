# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Makes the "what does this setting do?" strips for the COLOUR AND FADE layer. For every setting in SWEEPS below it bakes the same corner
# of the same tile (two rows of slates, 627 x 301 dots at the full 1254-dot density) once per value, with only that one setting changed,
# and joins the pictures into one labelled sheet in ../../controls_sweeps/colour_and_fade/<name>.png.
# Everything else stays at its default, so the only thing that changes between two pictures of a sheet is the setting named on the sheet.
# Use (plain python):  python3 -I run_sweeps.py [NAME ...]        (no names = every sweep; names = only those)
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'controls_sweeps', 'colour_and_fade'))
RAW = os.path.join(HERE, 'sweep_pictures')
RECIPE = os.path.join(HERE, 'layer_only_recipe.py')
P = 'colour_and_fade.'

# name: (title, [(label, {settings})...])
SWEEPS = {
    'fade_amount': ('Fade Amount: how much weathering runs down each slate (0 = clean slates)',
                    [(f'fade_amount {v}', {P + 'fade_amount': v}) for v in (0.0, 0.5, 1.0, 1.5, 2.0)]),
    'fade_length': ('Fade Length: how far the longest tongue runs (tile units; 0.07 = 88 dots)',
                    [(f'fade_length {v}', {P + 'fade_length': v}) for v in (0.02, 0.04, 0.07, 0.12, 0.25)]),
    'streak_width': ('Streak Width: width of one tongue / streak (tile units; 0.034 = 43 dots)',
                     [(f'streak_width {v}', {P + 'streak_width': v}) for v in (0.012, 0.02, 0.034, 0.055, 0.09)]),
    'patch_hardness': ('Patch Hardness: 1 = flat painted patches with hard edges, 0 = colours blend smoothly',
                       [(f'patch_hardness {v}', {P + 'patch_hardness': v}) for v in (1.0, 0.8, 0.5, 0.2, 0.0)]),
    'fade_direction': ('Fade Direction: 1 = dark above, bleached below (reference); -1 = the reverse',
                       [(f'fade_direction {v}', {P + 'fade_direction': v}) for v in (1.0, 0.5, 0.0, -0.5, -1.0)]),
    'streak_contrast': ('Streak Contrast: how strongly neighbouring patches differ (0 = only the fade)',
                        [(f'streak_contrast {v}', {P + 'streak_contrast': v}) for v in (0.0, 0.5, 1.0, 1.6, 2.5)]),
    'streak_bend': ('Streak Bend + Edge Ragged: wavy and ragged patch edges (0 = ruler-straight)',
                    [('bend 0, ragged 0', {P + 'streak_bend': 0.0, P + 'edge_ragged': 0.0}), ('bend 0.01, ragged 0.002', {P + 'streak_bend': 0.01, P + 'edge_ragged': 0.002}),
                     ('bend 0.024, ragged 0.0035 (default)', {}), ('bend 0.035, ragged 0.006', {P + 'streak_bend': 0.035, P + 'edge_ragged': 0.006}),
                     ('bend 0.05, ragged 0.012', {P + 'streak_bend': 0.05, P + 'edge_ragged': 0.012})]),
    'sun_bleach': ('Sun Bleach Amount: pale patches that cross slates (cover 0.35 so they are easy to see)',
                   [(f'sun_bleach_amount {v}', {P + 'bleach_amount': v, P + 'bleach_cover': 0.35, P + 'stain_amount': 0.0}) for v in (0.0, 0.3, 0.6, 1.0)]),
    'damp_stain': ('Damp Stain Amount: darker patches that cross slates (cover 0.35)',
                   [(f'stain_amount {v}', {P + 'stain_amount': v, P + 'stain_cover': 0.35, P + 'bleach_amount': 0.0}) for v in (0.0, 0.3, 0.6, 1.0)]),
    'tone_spread': ('Tone Spread: how different the slates are from each other (steps)',
                    [(f'tone_spread {v}', {P + 'tone_spread': v}) for v in (0.0, 0.5, 1.0, 1.6, 2.5)]),
    'tone_centre': ('Tone Centre: the average slate (0 = darkest palette colour, 8 = lightest; default 3.6)',
                    [(f'tone_centre {v}', {P + 'tone_centre': v}) for v in (1.5, 2.5, 3.6, 4.8, 6.0)]),
    'tint': ('Tint Amount + Patch Tint: green and warm leanings (0 = pure blue-grey)',
             [('tints off', {P + 'tint_amount': 0.0, P + 'patch_tint': 0.0}), ('tint 0.4, patch 0.3', {P + 'tint_amount': 0.4, P + 'patch_tint': 0.3}),
              ('tint 0.6, patch 0.5 (default)', {}), ('tint 1.0, patch 0.8', {P + 'tint_amount': 1.0, P + 'patch_tint': 0.8}),
              ('tint 1.0 warm, patch 0', {P + 'tint_amount': 1.0, P + 'patch_tint': 0.0, P + 'tint_green_share': 0.0})]),
    'seed': ('Seed: the same slates (same layout), a different roll of the paint',
             [(f'seed {v}', {P + 'seed': v}) for v in (11, 12, 13, 14)]),
    'amount': ('Amount: 0 = layer switched off (every slate the middle tone, flat), 1 = full',
               [(f'amount {v}', {P + 'amount': v}) for v in (0.0, 0.25, 0.5, 0.75, 1.0)]),
    'grain': ('Grain: a very faint fine grain inside the flat patches (this view is stretched 2x)',
              [(f'grain {v}', {P + 'grain_amount': v}) for v in (0.0, 0.08, 0.2, 0.5)]),
}


def sheet(title, files_labels, out_path, columns=2):
    tiles = []
    for path, label in files_labels:
        image = cv2.imread(path)
        banner = np.full((30, image.shape[1], 3), 245, np.uint8)
        cv2.putText(banner, label[:70], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
        tiles.append(np.vstack([banner, image, np.full((6, image.shape[1], 3), 255, np.uint8)]))
    while len(tiles) % columns:
        tiles.append(np.full_like(tiles[0], 255))
    rows = [np.hstack([np.hstack([t, np.full((t.shape[0], 6, 3), 255, np.uint8)]) for t in tiles[i:i + columns]]) for i in range(0, len(tiles), columns)]
    grid = np.vstack(rows)
    header = np.full((38, grid.shape[1], 3), 255, np.uint8)
    cv2.putText(header, title[:110], (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.imwrite(out_path, np.vstack([header, grid]))


def main():
    names = sys.argv[1:] or list(SWEEPS)
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        title, entries = SWEEPS[name]
        folder = os.path.join(RAW, name)
        views = {f'v{i}': settings for i, (label, settings) in enumerate(entries)}
        subprocess.run(BLENDER + [os.path.join(HERE, 'bake_region.py'), '--', RECIPE, folder, '1254', '0', '0.06', '0.5', '0.30', '4',
                                  json.dumps(views), '{}', 'Colour'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        files = [(os.path.join(folder, f'v{i}_colour.png'), label) for i, (label, _) in enumerate(entries)]
        if name == 'grain':                                  # make the faint thing visible: stretch contrast around the mean
            for path, _ in files:
                image = cv2.imread(path).astype(np.float32)
                cv2.imwrite(path, np.clip((image - image.mean()) * 2.0 + image.mean(), 0, 255).astype(np.uint8))
        sheet(title, files, os.path.join(OUT, name + '.png'), columns=2)
        print('wrote', os.path.join(OUT, name + '.png'), flush=True)


if __name__ == '__main__':
    main()
