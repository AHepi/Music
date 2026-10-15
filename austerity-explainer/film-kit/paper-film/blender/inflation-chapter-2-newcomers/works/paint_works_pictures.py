# What this does: paints the glass pictures that the Works' two factories wear, with numpy and Pillow (no
# Blender needed), for build_factories.py ("34 Plan - chapter 2 full redesign", part 1 A). Every picture
# comes twice, lit and dark, with the panes and glazing bars in exactly the same places, so a window can
# be switched from dark to lit by changing its material and nothing else moves:
#   mill-window-narrow-lit.jpg / -dark.jpg   No. 1's windows: cast-iron frames of 4 x 6 small panes
#   mill-window-wide-lit.jpg / -dark.jpg     No. 2's wider windows: 6 x 6 panes
#   north-light-lit.jpg / -dark.jpg          No. 1's sawtooth roof glazing, one panel 6 x 3 panes
#   lantern-light-lit.jpg / -dark.jpg        No. 2's roof lantern glazing, one panel 6 x 2 panes
#   doorway-inside-lit.jpg / -dark.jpg       the inside of a works seen through an open loading door:
#                                            warm haze, dark machines, belts and a line shaft (lit), or
#                                            the same nearly black (dark)
# Each glass picture holds four different windows side by side (an atlas): build_factories.py gives
# each window one of the four, so neighbouring windows differ (a dim pane here, a dirty one there).
#
# Lit glass: warm lamplight, brighter towards the top (lamps hang from the ceiling), a darker band where
# the line shafting crosses, faint belts, a few dim panes. Dark glass: the blue dusk sky reflected,
# lighter at the top, a soft reflection streak, some dirty or darker panes. No lettering anywhere.
#
# Run: python3 -I paint_works_pictures.py [FOLDER]
#      (default FOLDER: assets/models/inflation-chapter-2-newcomers/works/textures in the film kit)
# The same pictures come out every time (fixed seeds).

import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_FOLDER = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
DEFAULT_FOLDER = os.path.join(KIT_FOLDER, 'assets', 'models', 'inflation-chapter-2-newcomers', 'works', 'textures')

IRON = np.array([0.055, 0.058, 0.062])           # glazing bars and frames, nearly black
LAMPLIGHT = np.array([1.0, 0.68, 0.36])          # warm light inside a working mill
DUSK_LOW = np.array([0.09, 0.115, 0.15])         # dark glass reflecting the dusk sky, low panes
DUSK_HIGH = np.array([0.2, 0.25, 0.32])          # ... and high panes (more sky)
VARIANTS = 4                                     # windows side by side in each picture


def smooth_noise(height, width, random_numbers, cells=6):
    """Soft blotchy noise from 0 to 1: random values on a coarse grid, blown up smoothly."""
    coarse = random_numbers.random((cells + 1, cells + 1))
    picture = Image.fromarray((coarse * 255).astype(np.uint8)).resize((width, height), Image.BICUBIC)
    return np.asarray(picture).astype(float) / 255.0


def glazing(columns, rows, width, height, seed, frame=6, bar=3, shafting=0.3, belts=2):
    """One window of columns x rows panes, width x height pixels. Returns (lit, dark), each an array
    height x width x 3 of colours from 0 to 1, with the bars and frame in the same places."""
    random_numbers = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    inner_x = (xs - frame) / (width - 2 * frame) * columns
    inner_y = (ys - frame) / (height - 2 * frame) * rows
    in_x, in_y = inner_x % 1, inner_y % 1
    pane_w, pane_h = (width - 2 * frame) / columns, (height - 2 * frame) / rows
    is_bar = (np.minimum(in_x, 1 - in_x) * pane_w < bar / 2) | (np.minimum(in_y, 1 - in_y) * pane_h < bar / 2)
    is_frame = (xs < frame) | (xs >= width - frame) | (ys < frame) | (ys >= height - frame)
    iron = is_bar | is_frame
    pane = (np.clip(np.floor(inner_y), 0, rows - 1) * columns + np.clip(np.floor(inner_x), 0, columns - 1)).astype(int)
    tone = 0.82 + 0.3 * random_numbers.random(columns * rows)
    dim = random_numbers.random(columns * rows) < 0.08                 # a few panes painted over or very dirty
    up = 1 - ys / height                                    # 1 at the top, 0 at the bottom
    blotches = smooth_noise(height, width, random_numbers)

    # lit: lamplight, brighter near the top, a darker band where the shafting crosses, faint belts
    brightness = tone[pane] * (0.72 + 0.32 * up) * (0.9 + 0.2 * blotches)
    band = np.exp(-((ys / height - shafting) / 0.035) ** 2)
    brightness *= 1 - 0.35 * band
    for _ in range(belts):
        x0 = random_numbers.uniform(0.15, 0.85) * width
        lean = random_numbers.uniform(-0.04, 0.04)
        belt = np.exp(-((xs - x0 - lean * (ys - shafting * height)) / 1.6) ** 2) * (ys > shafting * height)
        brightness *= 1 - 0.4 * belt
    brightness = np.where(dim[pane], brightness * 0.4, brightness)
    lit = LAMPLIGHT[None, None, :] * brightness[..., None]
    lit = np.where(iron[..., None], IRON * 1.4, lit)

    # dark: the dusk sky reflected, lighter at the top, a soft diagonal streak, dirty panes
    sky = DUSK_LOW[None, None, :] + (DUSK_HIGH - DUSK_LOW)[None, None, :] * (up ** 1.4)[..., None]
    streak = np.exp(-(((xs / width) - 0.9 * (ys / height) - random_numbers.uniform(-0.2, 0.3)) / 0.09) ** 2)
    dark = sky * (tone[pane] * (0.85 + 0.25 * blotches))[..., None] + 0.05 * streak[..., None]
    dirty = random_numbers.random(columns * rows) < 0.12
    dark = np.where(dirty[pane][..., None], dark * np.array([0.8, 0.85, 0.75]), dark)
    grime = np.clip(1 - in_y, 0, 1) ** 8                    # grime gathers at each pane's lower edge
    dark *= (1 - 0.25 * grime)[..., None]
    dark = np.where(iron[..., None], IRON, dark)
    return lit, dark


def atlas(name, columns, rows, width, height, folder, seed, **settings):
    """Four windows side by side, lit and dark, saved as NAME-lit.jpg and NAME-dark.jpg."""
    lits, darks = [], []
    for variant in range(VARIANTS):
        lit, dark = glazing(columns, rows, width, height, seed + variant * 17, **settings)
        lits.append(lit)
        darks.append(dark)
    for state, parts in (('lit', lits), ('dark', darks)):
        picture = np.concatenate(parts, axis=1)
        path = os.path.join(folder, f'{name}-{state}.jpg')
        Image.fromarray((np.clip(picture, 0, 1) * 255).round().astype(np.uint8)).save(path, quality=92)
        print('wrote', path, picture.shape[1], 'x', picture.shape[0])


def doorway_inside(folder, width=512, height=512, seed=41):
    """The inside of a works seen through an open loading door: a warm haze lit from lamps hanging
    from the ceiling, dark machines along the floor, belts rising to a line shaft, a far wall with
    lit windows. The dark copy is the same picture with the lamps out."""
    random_numbers = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:height, 0:width].astype(float) / np.array([height, width])[:, None, None]
    haze = LAMPLIGHT[None, None, :] * (0.38 + 0.3 * (1 - ys) + 0.12 * smooth_noise(height, width, random_numbers, 5))[..., None]
    shapes = np.zeros((height, width))
    for _ in range(10):                                      # machines: dark blocks on the floor
        x0, width_fraction = random_numbers.random(), 0.06 + 0.14 * random_numbers.random()
        top = 0.5 + 0.3 * random_numbers.random()
        shapes = np.maximum(shapes, ((xs > x0) & (xs < x0 + width_fraction) & (ys > top)).astype(float))
    shapes = np.maximum(shapes, (np.abs(ys - 0.2) < 0.012).astype(float))          # the line shaft
    for _ in range(7):                                       # belts from the shaft down to the machines
        x0 = random_numbers.random()
        shapes = np.maximum(shapes, ((np.abs(xs - x0 - 0.05 * (ys - 0.2)) < 0.005) & (ys > 0.2) & (ys < 0.75)).astype(float))
    lit = haze * (1 - 0.85 * shapes)[..., None]
    for _ in range(5):                                       # lamps under the ceiling
        cx, cy = random_numbers.random(), 0.06 + 0.1 * random_numbers.random()
        lit += np.array([1.0, 0.8, 0.5]) * 0.7 * np.exp(-(((xs - cx) * 26) ** 2 + ((ys - cy) * 26) ** 2))[..., None]
    dark = np.array([0.03, 0.028, 0.026]) * (1 - 0.6 * shapes)[..., None] + 0.01 * (1 - ys)[..., None]
    for state, picture in (('lit', lit), ('dark', dark)):
        path = os.path.join(folder, f'doorway-inside-{state}.jpg')
        Image.fromarray((np.clip(picture, 0, 1) * 255).round().astype(np.uint8)).save(path, quality=92)
        print('wrote', path)


def main():
    folder = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER
    os.makedirs(folder, exist_ok=True)
    # pixel sizes keep each pane about square on its window (sizes in build_factories.py)
    atlas('mill-window-narrow', 4, 6, 168, 288, folder, seed=11, shafting=0.32)
    atlas('mill-window-wide', 6, 6, 252, 288, folder, seed=23, shafting=0.3, belts=3)
    atlas('north-light', 6, 3, 384, 168, folder, seed=37, shafting=0.75, belts=0)
    atlas('lantern-light', 6, 2, 384, 128, folder, seed=53, shafting=0.8, belts=0)
    doorway_inside(folder)


if __name__ == '__main__':
    main()
