"""What this does: makes a "behind picture" for a held shot whose camera then slides past near things that stand in the
painting (the waiting men at the Works' No. 1 gate, page 3 of chapter 2 for newcomers). It is the view's main painting
everywhere except inside the near things' outlines (widened a little), where it is filled in from round about, so it
shows the background as if they were not there.

Why it is needed: once the camera moves, the stage (projected-set.js) gives a ring round each near thing to the behind
picture, because there the painting's own edges belong to the things (the painter's dark outlines, smears), and they
would be left on the wall behind as ghosts. Outside the outlines this picture is the main painting exactly, so that ring
changes nothing; inside them it holds a plain fill of what was round about. Any other picture of the same view (the
working painting, a helper plate's state picture) also changes everything else it shows differently there: at the
Works, the lit cart doorway behind the men (the "men gone" helper) and the lit windows and yard light (the working
painting) came on behind the waiting men the moment the slide began, long before "go" and "start" (round 3 of log 34).
The fill is only ever seen in thin slivers beside the near things: as the camera moves toward them they grow on the
frame faster than the background, and so cover their own outlines.

When there is a helper plate drawn without the near things and with everything else as in the main plate (the Works'
works-w1-behind-plate.jpg), the truer behind picture is a state picture made from it (make_state_picture.py MAIN
HELPER PLATE HELPER_PLATE OUT MASK --outlines ...), and that is what page 3 uses while the plates stand in for the
paintings. This tool is the free way once the paintings come: it needs no painting of that helper plate. Its fill is
plain and a little smeared (the colours round about run into it), so look at --look before using it.

How the fill is made: OpenCV's inpainting (Telea's method) from the edge inwards, each colour taken from the pixels just
outside the outline. The outlines are the shot checker's per-prop pictures from shot_facts.py, measured for the PLATE's
camera and lens (the same ones make_state_picture.py uses), and/or any mask picture (white where the near things are).

Use: python3 -I make_behind_picture.py MAIN_PAINTING OUT_PICTURE [--outlines FACTS_FOLDER GROUP ...] [--mask MASK.png]
         [--widen 10] [--radius 9] [--look LOOK.jpg]
OUT_PICTURE must end in .png (lossless: a JPEG would change every pixel a little, so outside the outlines it would no
longer be exactly the main painting). Pixel sizes are for a 1536-pixel-wide plate and scale with its width. After
writing, the tool reads the picture back and checks it equals the main painting outside the widened outlines (0 levels).
--look writes a picture to judge it by: the main painting with the filled area outlined in orange, beside the result.
"""
import json
import os
import sys

import cv2
import numpy as np


def option(name, default=None, many=False):
    """A setting after the two pictures: '--name value', or with many=True every word up to the next --setting."""
    rest = sys.argv[3:]
    if name not in rest:
        return [] if many else default
    start = rest.index(name) + 1
    if not many:
        return rest[start]
    words = []
    for word in rest[start:]:
        if word.startswith('--'):
            break
        words.append(word)
    return words


def outlines_from_facts(facts_folder, groups, size):
    """The parts of the named groups that show, from shot_facts.py's ids.png (each group in its own flat colour), at the
    painting's size (as in make_state_picture.py)."""
    facts = json.load(open(os.path.join(facts_folder, 'facts.json')))
    ids = cv2.cvtColor(cv2.imread(os.path.join(facts_folder, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
    shown = np.zeros(ids.shape[:2], np.uint8)
    for group in groups:
        if group not in facts['groups']:
            raise SystemExit(f'make_behind_picture: no group "{group}" in {facts_folder}/facts.json (it has: {", ".join(facts["groups"])})')
        shown |= (np.abs(ids - np.array(facts['groups'][group]['colour'])).sum(axis=2) < 24).astype(np.uint8)
    width, height = size
    if abs(ids.shape[1] / ids.shape[0] - width / height) > 0.01:
        raise SystemExit(f'make_behind_picture: the outlines ({ids.shape[1]} x {ids.shape[0]}) are a different shape from the painting '
                         f'({width} x {height}): measure them for the plate\'s camera (shot_facts.py --fov PLATE_LENS)')
    return cv2.resize(shown * 255, size, interpolation=cv2.INTER_NEAREST) > 127


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main_path, out_path = sys.argv[1:3]
    if os.path.splitext(out_path)[1].lower() != '.png':
        raise SystemExit('make_behind_picture: write the behind picture as .png (lossless)')
    painting = cv2.imread(main_path, cv2.IMREAD_COLOR)
    if painting is None:
        raise SystemExit(f'make_behind_picture: can\'t read {main_path}')
    height, width = painting.shape[:2]
    unit = width / 1536
    widen = float(option('--widen', 10)) * unit
    radius = float(option('--radius', 9)) * unit
    near = np.zeros((height, width), bool)
    facts_and_groups = option('--outlines', many=True)
    if facts_and_groups:
        near |= outlines_from_facts(facts_and_groups[0], facts_and_groups[1:], (width, height))
    if option('--mask'):
        mask = cv2.imread(option('--mask'), cv2.IMREAD_GRAYSCALE)
        near |= cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST) > 127
    if not near.any():
        raise SystemExit('make_behind_picture: no outlines given (--outlines FACTS_FOLDER GROUP ... and/or --mask MASK.png)')
    size = max(1, int(round(widen)))
    filled_area = cv2.dilate(near.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * size + 1, 2 * size + 1)))
    behind = cv2.inpaint(painting, filled_area, radius, cv2.INPAINT_TELEA)
    behind[filled_area == 0] = painting[filled_area == 0]
    cv2.imwrite(out_path, behind, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    check = cv2.imread(out_path, cv2.IMREAD_COLOR)
    largest = int(np.abs(check.astype(np.int16) - painting.astype(np.int16))[filled_area == 0].max())
    print(f'make_behind_picture: {width} x {height}; filled {100 * (filled_area > 0).mean():.1f}% of the frame (the outlines widened '
          f'by {widen:.0f} pixels); largest difference from the main painting elsewhere, read back: {largest} levels (must be 0)')
    if largest != 0:
        raise SystemExit('make_behind_picture: the written picture is not the main painting outside the outlines')
    print(f'  wrote {out_path}')
    if option('--look'):
        marked = painting.copy()
        edge = cv2.morphologyEx(filled_area, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
        marked[edge] = (40, 140, 255)
        look = np.concatenate([marked, behind], axis=1)
        look = cv2.resize(look, (look.shape[1] // 2, look.shape[0] // 2), interpolation=cv2.INTER_AREA)
        cv2.imwrite(option('--look'), look, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f'  wrote {option("--look")}')


if __name__ == '__main__':
    main()
