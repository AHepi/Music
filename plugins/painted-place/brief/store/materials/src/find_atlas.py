"""
What this file does: finds every whole brick or stone block in a wall photograph on the shelf (brief/surfaces/), from the
thin lines of mortar between them (paler than the bricks in the colour picture, or lower and darker than the blocks in
the height and colour pictures), and writes the store's atlas file for it, materials/atlas/<set>.json:

    {"material": "BRICK • <set>", "set": "<set>", "picture_size_m": [w, h], "units": [[u0, v0, u1, v1], ...],
     "kinds": ["stretcher", "header", ...]}

u and v run from 0 to 1 over the picture, v up. A unit is a rectangle a little inside the brick's face, so no mortar
shows in it. The courses are found first (the bed joints, rows where mortar runs most of the way across), then the head
joints in each course (columns where mortar runs down most of the course and lies lower than the faces either side).
Left out: units cut by the picture's edge, units with mortar in them, units no higher than the joints round them in the
height picture, and, in a brick wall, units much longer than the rest (two bricks with a joint missed) and, in a wall
of stretchers only, the few short bits of brick split at a pale patch. With --check FOLDER it also draws the
rectangles over the colour and height pictures, to look at.

    python3 find_atlas.py                       every atlas set (ATLAS_SETS below)
    python3 find_atlas.py brick_wall_02 --check /tmp/check
Needs numpy, scipy and Pillow (no Blender).
"""
import argparse
import json
import os
import sys

import numpy
from PIL import Image, ImageDraw
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIALS = os.path.dirname(HERE)
BRIEF = os.path.dirname(os.path.dirname(MATERIALS))
SHELF = os.path.join(BRIEF, 'surfaces')
ATLAS = os.path.join(MATERIALS, 'atlas')

# set: (material name, kind of unit, what shows the mortar best, the face's width over its height a whole unit may have)
#   'pale': the mortar is paler and less red than the bricks (the colour picture's blue)
#   'low': the mortar lies low and dark (the height and colour pictures together)
ATLAS_SETS = {
    'brick_wall_02': ('BRICK • brick_wall_02', 'brick', 'pale', (1.1, 6.0)),
    'brick_wall_10': ('BRICK • brick_wall_10', 'brick', 'pale', (1.1, 6.0)),
    'sandstone_blocks_05': ('ASHLAR • sandstone_blocks_05', 'block', 'low', (0.45, 4.5)),
}
SIZE = 1024


def otsu(values):
    histogram, edges = numpy.histogram(values, bins=256, range=(0.0, 1.0))
    histogram = histogram.astype(float)
    centres = (edges[:-1] + edges[1:]) / 2
    weight_low = numpy.cumsum(histogram)
    weight_high = weight_low[-1] - weight_low
    mean_low = numpy.cumsum(histogram * centres) / numpy.maximum(weight_low, 1)
    mean_high = (numpy.sum(histogram * centres) - numpy.cumsum(histogram * centres)) / numpy.maximum(weight_high, 1)
    between = weight_low * weight_high * (mean_low - mean_high) ** 2
    return float(centres[int(numpy.argmax(between))])


def pictures(set_id):
    """The set's colour and height pictures at 1024 x 1024 (0..1), and its manifest entry."""
    entry = json.load(open(os.path.join(SHELF, 'manifest.json')))[set_id]
    colour = Image.open(os.path.join(SHELF, set_id, entry['maps']['diff'])).convert('RGB').resize((SIZE, SIZE), Image.BILINEAR)
    height = Image.open(os.path.join(SHELF, set_id, entry['maps']['disp'])).convert('F').resize((SIZE, SIZE), Image.BILINEAR)
    return numpy.asarray(colour, dtype=numpy.float64) / 255.0, numpy.asarray(height, dtype=numpy.float64) / 255.0, entry


def normalised(values):
    low, high = numpy.percentile(values, [2, 98])
    return numpy.clip((values - low) / max(high - low, 1e-6), 0.0, 1.0)


def mortar_score(set_id):
    """0..1 for every pixel: how much it looks like a line of mortar. 'pale': thin lines paler and less red than what
    is round them (the colour picture's blue); 'low': thin lines lower and darker than what is round them (the height
    and colour pictures together)."""
    colour, height, entry = pictures(set_id)
    clue = ATLAS_SETS[set_id][2]
    if clue == 'pale':
        blue = ndimage.gaussian_filter(colour[:, :, 2], 1.0)
        lines = blue - ndimage.grey_opening(blue, size=(25, 25))
    else:
        dark = ndimage.gaussian_filter(height, 1.0) + 0.5 * ndimage.gaussian_filter(colour.mean(axis=2), 1.0)
        lines = ndimage.grey_closing(dark, size=(17, 17)) - dark
    return normalised(lines), colour, height, entry


def joints(profile, spacing, least):
    """Where a 1-D profile (the share of mortar across a row or down a column) has its joints: the peaks at least
    'least' high, and each one's half width."""
    peaks, _ = signal.find_peaks(profile, distance=max(3, int(spacing)), height=least, prominence=0.5 * least)
    if len(peaks) == 0:
        return peaks, numpy.zeros(0)
    widths = signal.peak_widths(profile, peaks, rel_height=0.5)[0]
    return peaks, widths / 2.0


def course_pitch(profile):
    centred = profile - profile.mean()
    correlation = numpy.correlate(centred, centred, mode='full')[len(centred) - 1:]
    correlation /= max(correlation[0], 1e-9)
    peaks, _ = signal.find_peaks(correlation[8:400], prominence=0.05)
    return float(peaks[0] + 8) if len(peaks) else 40.0


def stands_proud(height, r0, r1, c0, c1):
    """True when the face inside the rectangle lies higher, on average, than a ring 2 to 7 pixels outside it (the
    joints round a brick or block)."""
    inside = height[r0:r1, c0:c1].mean()
    big = height[max(r0 - 7, 0):r1 + 7, max(c0 - 7, 0):c1 + 7]
    middle = height[max(r0 - 2, 0):r1 + 2, max(c0 - 2, 0):c1 + 2]
    ring = (big.sum() - middle.sum()) / max(big.size - middle.size, 1)
    return inside > ring


def find_units(set_id):
    """The whole units in the set's pictures: a list of (u0, v0, u1, v1), their kinds, and what was measured. The bed
    joints are rows where mortar runs most of the way across; the head joints, columns where it runs down most of the
    course between two bed joints (a pale or dark spot on a brick's face does not)."""
    material, kind, clue, (low_ratio, high_ratio) = ATLAS_SETS[set_id]
    score, colour, height, entry = mortar_score(set_id)
    threshold = otsu(score.ravel())
    mortar = ndimage.binary_closing(score > threshold, iterations=1)
    smooth_height = ndimage.gaussian_filter(height, 1.0)
    rows = ndimage.gaussian_filter1d(mortar.mean(axis=1), 1.0)
    pitch = course_pitch(rows)
    beds, bed_half = joints(rows, 0.6 * pitch, 0.3)
    found = []
    for i in range(len(beds) - 1):
        top = int(numpy.ceil(beds[i] + bed_half[i]))
        bottom = int(numpy.floor(beds[i + 1] - bed_half[i + 1]))
        if bottom - top < 5:
            continue
        columns = ndimage.gaussian_filter1d(mortar[top:bottom].mean(axis=0), 1.0)
        heads, head_half = joints(columns, (0.7 if kind == 'brick' else 0.4) * (bottom - top), 0.55)
        # a real head joint also lies lower than the faces on either side of it (a pale patch on a brick does not)
        band = smooth_height[top:bottom]
        kept = []
        for c, half in zip(heads, head_half):
            w = int(max(1, round(half)))
            if c - w - 12 < 0 or c + w + 12 >= SIZE:
                kept.append((c, half))
                continue
            joint = band[:, c - w:c + w + 1].mean()
            faces = 0.5 * (band[:, c - w - 12:c - w - 3].mean() + band[:, c + w + 4:c + w + 13].mean())
            if joint < faces - 0.15 * band.std():
                kept.append((c, half))
        heads = numpy.array([k[0] for k in kept], dtype=int)
        head_half = numpy.array([k[1] for k in kept])
        for j in range(len(heads) - 1):
            left = int(numpy.ceil(heads[j] + head_half[j]))
            right = int(numpy.floor(heads[j + 1] - head_half[j + 1]))
            if right - left < 5:
                continue
            found.append([top, bottom, left, right])
    units, widths = [], []
    for top, bottom, left, right in found:
        inset_r = max(1, int(round((bottom - top) * 0.08)))
        inset_c = max(1, int(round((right - left) * 0.03)))
        r0, r1, c0, c1 = top + inset_r, bottom - inset_r, left + inset_c, right - inset_c
        if r1 - r0 < 4 or c1 - c0 < 4:
            continue
        ratio = (c1 - c0) / float(r1 - r0)
        if not (low_ratio <= ratio <= high_ratio):
            continue
        if mortar[r0:r1, c0:c1].mean() > 0.15:
            continue                                                       # sits on mortar
        if not stands_proud(height, r0, r1, c0, c1):
            continue                                                       # no higher than the joints round it
        units.append((r0, r1, c0, c1))
        widths.append(ratio)
    kinds = []
    if kind == 'brick' and units:
        # bricks are all one length: a unit much longer than the middle one is two bricks with a joint missed
        lengths = numpy.array([c1 - c0 for r0, r1, c0, c1 in units], dtype=float)
        keep = lengths <= 1.2 * numpy.median(lengths)
        units = [unit for unit, k in zip(units, keep) if k]
        widths = [w for w, k in zip(widths, keep) if k]
    if kind == 'brick' and widths:
        long_ratio = numpy.percentile(widths, 75)
        kinds = ['header' if w < 0.66 * long_ratio else 'stretcher' for w in widths]
        if kinds.count('header') < 0.15 * len(kinds):
            # a wall of stretchers (no header courses): its few short units are bits of bricks split at a pale patch
            units = [unit for unit, k in zip(units, kinds) if k == 'stretcher']
            kinds = ['stretcher'] * len(units)
    result = [[round(c0 / SIZE, 5), round(1 - r1 / SIZE, 5), round(c1 / SIZE, 5), round(1 - r0 / SIZE, 5)]
              for r0, r1, c0, c1 in units]
    return result, kinds, {'beds': len(beds), 'pitch': pitch, 'threshold': threshold, 'mortar': mortar, 'height': height}


def write(set_id, check=None):
    material, kind, _, _ = ATLAS_SETS[set_id]
    units, kinds, measured = find_units(set_id)
    entry = json.load(open(os.path.join(SHELF, 'manifest.json')))[set_id]
    data = {'material': material, 'set': set_id, 'picture_size_m': entry['size_m'], 'units': units}
    if kind == 'brick' and kinds and 'header' in kinds:
        data['kinds'] = kinds
    os.makedirs(ATLAS, exist_ok=True)
    path = os.path.join(ATLAS, set_id + '.json')
    with open(path, 'w') as handle:
        json.dump(data, handle, indent=1)
    if check:
        os.makedirs(check, exist_ok=True)
        colour = Image.open(os.path.join(SHELF, set_id, entry['maps']['diff'])).convert('RGB').resize((1024, 1024))
        height = Image.open(os.path.join(SHELF, set_id, entry['maps']['disp'])).convert('RGB').resize((1024, 1024))
        sheet = Image.new('RGB', (2048, 1024))
        sheet.paste(colour, (0, 0))
        sheet.paste(height, (1024, 0))
        draw = ImageDraw.Draw(sheet)
        for number, (u0, v0, u1, v1) in enumerate(units):
            x0, x1, y0, y1 = u0 * 1024, u1 * 1024, (1 - v1) * 1024, (1 - v0) * 1024
            tint = (255, 60, 60) if data.get('kinds', ['stretcher'] * len(units))[number] == 'stretcher' else (60, 200, 255)
            for offset in (0, 1024):
                draw.rectangle([x0 + offset, y0, x1 + offset, y1], outline=tint, width=2)
        sheet.save(os.path.join(check, set_id + ' atlas check.png'))
    return path, len(units), measured


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('sets', nargs='*', help='shelf sets (default: every atlas set)')
    parser.add_argument('--check', help='a folder for pictures of the found units drawn over the photographs')
    args = parser.parse_args()
    for set_id in args.sets or sorted(ATLAS_SETS):
        path, count, measured = write(set_id, args.check)
        print(set_id, count, 'units ->', path, '(courses %d, pitch %.0f px)' % (measured['beds'], measured['pitch']))


if __name__ == '__main__':
    sys.exit(main())
