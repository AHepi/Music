"""What this does: makes a state picture (plan 34, "How the men come and go"): the picture a held shot cuts to when
something in it changes on a spoken word (the waiting men gone, or come back). It is the view's main painting
everywhere except inside a mask, and the second painting of the same view (the one painted without the men) inside
it, joined with a soft edge. So at the time cut only the men, and the light and shadows they changed, change; every
other brushstroke stays exactly where it was. (Cutting to the whole second painting would change every brushstroke
in the frame at once.)

The mask is made of two parts, joined:
  (a) where the two plates really differ: the plate drawn with the men and the helper plate drawn without them.
      That is the men themselves and everything they change: the long shadows the fire and the lamps throw from
      them, the light they hold off the walls behind them, the glow on their coats.
  (b) the men's own outlines, widened a little, so the painter's dark edge round each man goes with him even where
      a man is close in colour to what is behind him. The outlines are the shot checker's per-prop pictures from
      shot_facts.py, measured for the PLATE's camera and lens (--outlines FACTS_FOLDER GROUP ...: the parts of each
      named group that show, from ids.png), and/or any mask picture (--mask FILE: white where things change).
Then the mask is cleared of specks and pinholes, widened (--widen) and softened (--soften). The widening comes
before the softening, so every pixel that really changed takes the second painting fully, and the soft join lies
outside it, on paint that is the same in both states.

How the mask's thresholds were chosen (in levels of 0 to 255). Both plates are blurred a little first (2 pixels), so
the render's grain and the JPEG's little blocks don't count, and the difference is the largest of the three colour
channels (the fire's light the men hold off the walls is mostly red). A pixel counts as changed if that difference
is over --threshold (default 6), or if the same difference blurred a lot (10 pixels) is over --faint (default 3).
Measured on the people test's plates (round 2, log 34):
  - Noise: two renders of the same set differ by under 1 level in their fine grain (99th percentile 0.2 to 0.6),
    and saving them as JPEGs moves them by up to 2 (99th percentile, after the blur), so 6 levels is clear of
    both; the few specks left on sharp edges are cleared by size. The tool measures
    this noise again for every view (in the quarter of the frame furthest from the change) and warns if a
    threshold is under three times it.
  - Ghosts: the men's long shadows, thrown toward the camera by the fire and the lamps, fade out slowly. With 6
    levels alone, their faint ends (3 to 8 levels) stayed with the main painting: in the state picture made from
    the plates, man-shaped shadow ends were left on the road and the pavement below the group over 6.8% of the
    frame (by more than 3 levels). With 10 levels, darker remnants (8 to 12 levels) stayed. A shadow left behind
    after the men have gone is exactly the ghost the cut must not leave, so the smooth difference is also taken,
    down to 3 levels: blurred over 10 pixels, a change that small is still a smooth shadow or wash of light (the
    cobbles' texture and the noise are blurred away), and the mask's edge comes out clean, not lacy. With both,
    what the state picture leaves behind is under 4 levels everywhere but 0.04% of the frame.
  - Cost: the lower the thresholds, the more of the frame comes from the second painting, where its brushwork
    changes at the cut. In the people test the mask covers 32% of the frame with 6 levels alone and 42% with the
    faint 3 as well (the men, their shadows over the road and pavement below them, and the house wall on the
    right, which the fire lights more brightly once the men no longer stand in its way). At a time cut, a change
    of brushwork where the light really changed is far less noticeable than a shadow left behind; under 3 levels
    (about 1% of the full range, spread softly) no change can be seen at a cut on a phone.
  - To make the mask smaller, the plates themselves must differ less: for example draw both with the men casting
    no shadows and not blocking the fire's light, and give each man a small soft shadow under his own feet.
The tool prints how much of the frame the mask covers at other settings, to make this choice again for another
view; look at the mask picture (--look) before trusting it.

Use: python3 -I make_state_picture.py MAIN_PAINTING SECOND_PAINTING PLATE HELPER_PLATE OUT_PICTURE OUT_MASK
         [--outlines FACTS_FOLDER GROUP ...] [--mask MASK.png] [--threshold 6] [--faint 3] [--widen 12] [--soften 5]
         [--outline-widen 6] [--look LOOK.jpg]
MAIN_PAINTING is the painting of the plate (the state before the cut); SECOND_PAINTING the painting of the helper plate
(the state after). For the free test, give the plate and the helper plate as the two paintings. All the pictures
must show the same view; the paintings and masks are resized to the plate's size, and the state picture is written at
that size, losslessly: OUT_PICTURE must end in .png (or .webp, written as lossless WebP). A JPEG is refused: saving
as a JPEG again changes every pixel a little (round 2's check: 0.48 levels on average and up to 9 outside the mask), so
the state picture would no longer be exactly the main painting where nothing changed. After writing, the tool reads
the picture back and prints the largest difference from the main painting where the mask is zero; it must be 0
(it stops with an error if it is not). OUT_MASK is the mask as a grey picture (white: the second painting). --look writes a
picture to judge the mask by: the main painting dimmed, the plates' difference (a) in orange, the outlines (b) in
blue, the soft edge as a thin line. Pixel sizes are for a 1536-pixel-wide plate and scale with the plate's width.
"""
import json
import os
import sys

import cv2
import numpy as np

# how each lossless kind of picture is written (OpenCV: PNG at its usual compression; WebP quality over 100 is lossless)
LOSSLESS_SETTINGS = {'.png': [cv2.IMWRITE_PNG_COMPRESSION, 6], '.webp': [cv2.IMWRITE_WEBP_QUALITY, 101]}


def option(name, default=None, many=False):
    """A setting after the six pictures: '--name value', or with many=True every word up to the next --setting."""
    rest = sys.argv[7:]
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


def read(path, size=None, grey=False):
    picture = cv2.imread(path, cv2.IMREAD_GRAYSCALE if grey else cv2.IMREAD_COLOR)
    if picture is None:
        raise SystemExit(f'make_state_picture: can\'t read {path}')
    if size and (picture.shape[1], picture.shape[0]) != size:
        picture = cv2.resize(picture, size, interpolation=cv2.INTER_NEAREST if grey else cv2.INTER_AREA)
    return picture


def disc(radius):
    radius = max(1, int(round(radius)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))


def outlines_from_facts(facts_folder, groups, size):
    """The parts of the named groups that show, from shot_facts.py's ids.png (each group drawn in its own flat colour,
    as the camera sees it), at the plate's size."""
    facts = json.load(open(os.path.join(facts_folder, 'facts.json')))
    ids = cv2.cvtColor(cv2.imread(os.path.join(facts_folder, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
    shown = np.zeros(ids.shape[:2], np.uint8)
    for group in groups:
        if group not in facts['groups']:
            raise SystemExit(f'make_state_picture: no group "{group}" in {facts_folder}/facts.json '
                             f'(it has: {", ".join(facts["groups"])})')
        shown |= (np.abs(ids - np.array(facts['groups'][group]['colour'])).sum(axis=2) < 24).astype(np.uint8)
    width, height = size
    if abs(ids.shape[1] / ids.shape[0] - width / height) > 0.01:
        raise SystemExit(f'make_state_picture: the outlines ({ids.shape[1]} x {ids.shape[0]}) are a different shape from the plate '
                         f'({width} x {height}): measure them for the plate\'s camera (shot_facts.py --fov PLATE_LENS)')
    return cv2.resize(shown * 255, size, interpolation=cv2.INTER_NEAREST) > 127


def main():
    main_path, second_path, plate_path, helper_path, out_path, mask_path = sys.argv[1:7]
    ending = os.path.splitext(out_path)[1].lower()
    if ending not in LOSSLESS_SETTINGS:
        raise SystemExit(f'make_state_picture: write the state picture losslessly, as .png or .webp (not "{ending or out_path}"): '
                         f'a JPEG changes every pixel a little, so outside the mask it would no longer be the main painting')
    threshold = float(option('--threshold', 6))
    faint = float(option('--faint', 3))
    plate, helper = read(plate_path), read(helper_path)
    height, width = plate.shape[:2]
    size = (width, height)
    if helper.shape != plate.shape:
        raise SystemExit(f'make_state_picture: the plate and the helper plate differ in size ({plate.shape} against {helper.shape})')
    unit = width / 1536   # pixel sizes below are for a 1536-pixel-wide plate
    widen = float(option('--widen', 12)) * unit
    soften = float(option('--soften', 5)) * unit
    outline_widen = float(option('--outline-widen', 6)) * unit
    main_painting, second_painting = read(main_path, size), read(second_path, size)

    # (a) where the plates differ: blurred a little, the largest of the three channels, in levels of 0-255; and the
    # same blurred a lot (10 pixels), for the faint, smooth ends of long shadows and washes of light
    blur = lambda picture, sigma: cv2.GaussianBlur(picture.astype(np.float32), (0, 0), sigma * unit)
    difference = np.abs(blur(plate, 2) - blur(helper, 2)).max(axis=2)
    smooth_difference = np.abs(blur(plate, 10) - blur(helper, 10)).max(axis=2)

    # (b) the outlines of what changes
    outlines = np.zeros((height, width), bool)
    groups = option('--outlines', many=True)
    if groups:
        outlines |= outlines_from_facts(groups[0], groups[1:], size)
    if option('--mask'):
        outlines |= read(option('--mask'), size, grey=True) > 127
    outlines = cv2.dilate(outlines.astype(np.uint8), disc(outline_widen)) > 0

    def changed_at(level, faint_level):
        """The plates' difference over `level`, or their smooth difference over `faint_level`, cleared of specks
        (single noisy pixels, JPEG blocks) and with its pinholes and thin gaps closed, so a shadow comes out whole,
        not as lace."""
        found = ((difference > level) | (smooth_difference > faint_level)).astype(np.uint8)
        found = cv2.morphologyEx(found, cv2.MORPH_OPEN, disc(1.5 * unit))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(found, connectivity=8)
        smallest = 60 * unit * unit
        keep = np.zeros(count, np.uint8)
        keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= smallest
        found = keep[labels]
        return cv2.morphologyEx(found, cv2.MORPH_CLOSE, disc(6 * unit)) > 0

    changed = changed_at(threshold, faint)
    core = changed | outlines

    # the noise between the two renders: the fine grain of their difference (with the smooth changes of light taken
    # out, as the men's light and shadows are smooth), in the quarter of the frame furthest from the change
    distance = cv2.distanceTransform((~core).astype(np.uint8), cv2.DIST_L2, 5)
    far = distance >= np.percentile(distance, 75)
    grain = np.abs(difference - cv2.GaussianBlur(difference, (0, 0), 8 * unit))
    noise = float(np.percentile(grain[far], 99)) if far.any() else 0.0

    # widened, then softened: the soft join lies outside every changed pixel
    widened = cv2.dilate(core.astype(np.uint8), disc(widen)).astype(np.float32)
    weight = np.maximum(cv2.GaussianBlur(widened, (0, 0), soften), core.astype(np.float32))
    weight = np.clip(weight, 0, 1)
    # a weight that the mask picture would write as 0 (or 255) is made exactly 0 (or 1), so where the mask picture is
    # 0 the state picture is the main painting to the last level, and where it is 255, the second painting
    weight[weight < 0.5 / 255] = 0.0
    weight[weight > 1 - 0.5 / 255] = 1.0
    weight = weight[:, :, None]

    state = main_painting.astype(np.float32) * (1 - weight) + second_painting.astype(np.float32) * weight
    if not cv2.imwrite(out_path, np.clip(state + 0.5, 0, 255).astype(np.uint8), LOSSLESS_SETTINGS[ending]):
        raise SystemExit(f'make_state_picture: could not write {out_path}')
    cv2.imwrite(mask_path, np.clip(weight[:, :, 0] * 255 + 0.5, 0, 255).astype(np.uint8))

    # read back what was written: outside the mask it must be the main painting exactly
    written, written_mask = read(out_path), read(mask_path, grey=True)
    outside = written_mask == 0
    off_outside = np.abs(written.astype(np.int16) - main_painting.astype(np.int16)).max(axis=2)[outside]
    largest_outside = int(off_outside.max()) if off_outside.size else 0

    # what is left: how far the state picture is from the second painting where the plates differ by more than
    # 2 levels but the mask doesn't reach (the faint changes left behind with the main painting)
    left_behind = (difference > 2) & (weight[:, :, 0] < 0.5)
    print(f'make_state_picture: {width} x {height}; threshold {threshold:g} levels, faint {faint:g} levels (smooth changes); noise between '
          f'the plates (their fine grain, far from the change) {noise:.1f} levels (99th percentile)')
    if min(threshold, faint) < 3 * noise:
        print(f'  WARNING: a threshold is less than three times the noise ({3 * noise:.1f}): specks of noise will join the mask')
    print('  the mask at other settings (share of the frame, after widening):')
    for level, faint_level in ((4, 99), (6, 99), (8, 99), (10, 99), (14, 99), (threshold, 2), (threshold, 3), (threshold, 4), (threshold, 5)):
        wide = cv2.dilate((changed_at(level, faint_level) | outlines).astype(np.uint8), disc(widen)) > 0
        used = abs(level - threshold) < 1e-6 and abs(faint_level - faint) < 1e-6
        print(f'    threshold {level:3g}, faint {"none" if faint_level == 99 else f"{faint_level:g}":>4}: {wide.mean():6.1%}' + ('   <- used' if used else ''))
    print(f'  used: plates differ over {changed.mean():.1%} of the frame; outlines {outlines.mean():.1%}; '
          f'second painting fully over {(weight[:, :, 0] > 0.999).mean():.1%}, partly over {((weight[:, :, 0] > 0.001) & (weight[:, :, 0] <= 0.999)).mean():.1%}')
    print(f'  left with the main painting although the plates differ by more than 2 levels: {left_behind.mean():.1%} of the frame, '
          f'by {float(difference[left_behind].mean()) if left_behind.any() else 0:.1f} levels on average, '
          f'{float(difference[left_behind].max()) if left_behind.any() else 0:.1f} at most')
    edge = (weight[:, :, 0] > 0.02) & (weight[:, :, 0] < 0.98)
    seam = np.abs(main_painting.astype(np.float32) - second_painting.astype(np.float32)).max(axis=2)
    print(f'  the two paintings across the soft join differ by {float(seam[edge].mean()) if edge.any() else 0:.1f} levels on average '
          f'(a large number here shows as a seam)')
    print(f'  largest difference from the main painting where the mask is zero ({outside.mean():.1%} of the frame), read back '
          f'from the written picture: {largest_outside} levels (must be 0)')
    print(f'  wrote {out_path} (lossless) and {mask_path}')
    if largest_outside:
        raise SystemExit(f'make_state_picture: outside the mask the state picture is up to {largest_outside} levels off the main painting')

    look = option('--look')
    if look:
        picture = main_painting.astype(np.float32) * 0.45
        picture[changed] = picture[changed] * 0.5 + np.array([40, 140, 255], np.float32) * 0.5     # orange (BGR): the plates differ
        picture[outlines] = picture[outlines] * 0.4 + np.array([255, 160, 60], np.float32) * 0.6   # blue: the outlines
        rim = cv2.morphologyEx((weight[:, :, 0] > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, disc(1)) > 0
        picture[rim] = (255, 255, 255)
        cv2.imwrite(look, np.clip(picture, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(f'  wrote {look}')


if __name__ == '__main__':
    main()
