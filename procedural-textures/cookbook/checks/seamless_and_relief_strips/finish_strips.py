# What this does: turns the squares made by make_coordinate_strips.py into the guide's strip pictures and measures the numbers the guide quotes.
#  * every square is first ROLLED by half a tile (moved half its width right and half its height down, wrapping round), so a seam shows
#    as a cross in the middle of the square;
#  * the rolled squares are joined into a labelled strip with lib/make_strip.py and saved as a small JPEG in cookbook/pictures/;
#  * numbers (written to numbers_coordinates.json): the jump across the wrap-round edge compared with an ordinary jump between neighbouring
#    dots in the SAME direction (1.0 = no seam), whether the "Mapping first" square repeats, how different the area quarters are, and how
#    different the Texture Coordinate outputs are from each other.
# It also makes the OpenGL / DirectX comparison picture for the relief guide from the reference brick maps (pictures used for explanation only).
# Run with plain Python:  python3 -I finish_strips.py
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WORK = os.path.join(HERE, 'work')
PICTURES = os.path.join(PROC, 'cookbook', 'pictures')
MAKE_STRIP = os.path.join(PROC, 'lib', 'make_strip.py')

STRIPS = {
    'voronoi_cells_across': ('seamless-strip-voronoi-cells-across.jpg', 'Seamless Voronoi (4D donut): cells across the tile, shown shifted by half', 256),
    'warp_keeps_tiling': ('seamless-strip-warp-keeps-tiling.jpg', 'Bands bent by seamless noise (first four) and by plain noise (last), shifted by half', 256),
    'stretch_trap': ('seamless-strip-stretch-trap.jpg', 'Stretching seamless noise: Mapping before the donut, or two counts (shifted by half)', 256),
    'area_or_repeat': ('seamless-area-or-repeat.jpg', 'Repeat the tile, or raise the tile count', 384),
    'texture_coordinate': ('coordinates-strip-texture-coordinate.jpg', 'Texture Coordinate outputs into plain 3D noise (shifted by half)', 256),
}


def grey_of(path):
    return cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float64)


def seam_same_direction(grey):
    """Jump across the wrap edge / ordinary jump, measured sideways for the left-right edge and up-down for the top-bottom edge."""
    sideways = np.abs(np.diff(grey, axis=1)).mean()
    updown = np.abs(np.diff(grey, axis=0)).mean()
    left_right = np.abs(grey[:, 0] - grey[:, -1]).mean() / max(sideways, 1e-9)
    top_bottom = np.abs(grey[0, :] - grey[-1, :]).mean() / max(updown, 1e-9)
    return round(float(left_right), 2), round(float(top_bottom), 2)


def wrap_line_against_ordinary_lines(grey):
    """A fairer seam number: the jump between the last and the first column (the wrap edge) next to the jumps between every other
    pair of neighbouring columns, and the same for rows. A seam is a wrap jump far ABOVE the biggest ordinary one; a seamless tile
    has its wrap jump somewhere inside the ordinary range."""
    result = {}
    for direction, axis in (('columns (left-right edge)', 1), ('rows (top-bottom edge)', 0)):
        jumps = np.abs(np.roll(grey, -1, axis=axis) - grey).mean(axis=0 if axis == 1 else 1)
        wrap, ordinary = jumps[-1], jumps[:-1]
        result[direction] = {'wrap_jump': round(float(wrap), 2), 'ordinary_mean': round(float(ordinary.mean()), 2),
                             'ordinary_biggest': round(float(ordinary.max()), 2),
                             'share_of_ordinary_lines_below_the_wrap_jump': round(float((ordinary < wrap).mean()), 2)}
    return result


def roll_and_strip(name):
    picture_name, title, cell = STRIPS[name]
    source = os.path.join(WORK, name)
    rolled_folder = os.path.join(WORK, name + '_rolled')
    os.makedirs(rolled_folder, exist_ok=True)
    info = json.load(open(os.path.join(source, 'sweep.json')))
    for file_name in info['files']:
        image = cv2.imread(os.path.join(source, file_name))
        half_rows, half_columns = image.shape[0] // 2, image.shape[1] // 2
        rolled = np.roll(image, (half_rows, half_columns), axis=(0, 1))
        # a thin white frame round every square, so the joins between squares in the strip are not mistaken for seams
        border = max(2, image.shape[0] // 64)
        framed = cv2.copyMakeBorder(rolled, border, border, border, border, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        cv2.imwrite(os.path.join(rolled_folder, file_name), framed)
    shutil.copy(os.path.join(source, 'sweep.json'), os.path.join(rolled_folder, 'sweep.json'))
    out = os.path.join(PICTURES, picture_name)
    subprocess.run([sys.executable, '-I', MAKE_STRIP, rolled_folder, out, '--title', title, '--cell', str(cell)], check=True)
    return out, info


def main():
    numbers = {}
    for name in STRIPS:
        out, info = roll_and_strip(name)
        greys = [grey_of(os.path.join(WORK, name, f)) for f in info['files']]
        numbers[name] = {'picture': os.path.relpath(out, PROC), 'picture_bytes': os.path.getsize(out),
                         'seam_left_right_and_top_bottom': {label: seam_same_direction(g) for label, g in zip(info['labels'], greys)},
                         'wrap_line_against_ordinary_lines': {label: wrap_line_against_ordinary_lines(g) for label, g in zip(info['labels'], greys)}}
        if name == 'stretch_trap':
            mapped = greys[1]
            quarter = mapped.shape[0] // 4
            numbers[name]['mapping_y_x4_first_rows_0_to_quarter_vs_next_quarter_mean_difference'] = round(
                float(np.abs(mapped[:quarter] - mapped[quarter:2 * quarter]).mean()), 2)
            plain = greys[0]
            numbers[name]['plain_4x4_same_comparison_for_contrast'] = round(float(np.abs(plain[:quarter] - plain[quarter:2 * quarter]).mean()), 2)
        if name == 'area_or_repeat':
            for label, g in zip(info['labels'], greys):
                h = g.shape[0] // 2
                quarters = [g[:h, :h], g[:h, h:], g[h:, :h], g[h:, h:]]
                differences = [float(np.abs(quarters[0] - q).mean()) for q in quarters[1:]]
                numbers[name][label + ' : top-left quarter against the other three, mean difference'] = [round(d, 2) for d in differences]
        if name == 'texture_coordinate':
            pairs = {}
            for i, a in enumerate(info['labels']):
                for j, b in enumerate(info['labels']):
                    if j > i:
                        pairs[f'{a} vs {b}'] = round(float(np.abs(greys[i] - greys[j]).mean()), 2)
            numbers[name]['mean_difference_between_outputs_0_to_255'] = pairs
    numbers['relief_opengl_directx'] = make_opengl_directx_picture()
    with open(os.path.join(HERE, 'numbers_coordinates.json'), 'w') as handle:
        json.dump(numbers, handle, indent=1)
    print(json.dumps(numbers, indent=1))


def make_opengl_directx_picture():
    """Crop of the brick reference: height, normal (OpenGL, green up) and the uploaded DirectX normal, with labels.
    Also the green-versus-height-slope correlation on the crop (OpenGL about +0.9, DirectX about -0.9)."""
    folder = os.path.join(PROC, 'reference', 'brick')
    top, left, size, shown = 300, 300, 200, 300
    height = cv2.imread(os.path.join(folder, 'height_as_uploaded.png'), cv2.IMREAD_GRAYSCALE)
    opengl = cv2.imread(os.path.join(folder, 'normal.png'))
    directx = cv2.imread(os.path.join(folder, 'normal_as_uploaded_directx.png'))
    result = {}
    whole_height = height.astype(np.float64) / 255.0
    slope_down = (np.roll(whole_height, -1, axis=0) - np.roll(whole_height, 1, axis=0)) / 2.0
    for label, picture in (('normal.png (OpenGL)', opengl), ('normal_as_uploaded_directx.png (DirectX)', directx)):
        green = picture[..., 1].astype(np.float64)
        result[label + ': correlation of green with the height slope DOWN the picture'] = round(float(np.corrcoef(green.ravel(), slope_down.ravel())[0, 1]), 3)
    panels = []
    for label, picture in (('height', cv2.cvtColor(height, cv2.COLOR_GRAY2BGR)), ('OpenGL (Blender): green up', opengl),
                           ('DirectX: green down', directx)):
        crop = cv2.resize(picture[top:top + size, left:left + size], (shown, shown), interpolation=cv2.INTER_NEAREST)
        banner = np.full((34, shown, 3), 245, np.uint8)
        cv2.putText(banner, label, (6, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
        panels.append(np.vstack([banner, crop]))
    sheet = np.hstack(panels)
    header = np.full((40, sheet.shape[1], 3), 255, np.uint8)
    cv2.putText(header, 'Brick reference, same 200-dot corner, three maps', (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    out = os.path.join(PICTURES, 'relief-opengl-or-directx-brick.jpg')
    cv2.imwrite(out, np.vstack([header, sheet]), [cv2.IMWRITE_JPEG_QUALITY, 88])
    result['picture'] = os.path.relpath(out, PROC)
    result['picture_bytes'] = os.path.getsize(out)
    return result


main()
