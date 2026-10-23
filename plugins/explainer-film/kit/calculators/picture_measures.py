"""What this does: MEASURES a picture of a place so "it looks right" is not only an opinion: how light and dark it is (the percentiles of luminance), how colourful, how much fine
detail each part has (the "detail energy": too much reads as busy and photographic, too little as flat), whether any window of the picture is dead flat, whether too many pixels are
strongly coloured or turquoise or blown out, and how much the big shapes and light changed since the last round (the squint test). It can make a STYLE GUARD from the first honest picture
of a place (marked provisional: it locks in whatever that picture looked like until a person accepts it) and check later pictures against it. A measure is not a look: the eye decides;
these only catch what a person's eye is bad at (a drift of 0.03 in the middle grey, detail energy twice the guard's) and say plainly which region loses the most.
Plain Python with numpy and Pillow; large pictures are shrunk with a float32 buffer (a float64 buffer once crashed the metric).

Verbs:
  measure PICTURE... [--regions FILE.json | --id-map PICTURE --id-colours FILE.json] [--previous PICTURE]
        the numbers for each picture; regions are {"name": [x0, y0, x1, y1]} in pixels, or a flat-colour picture of role classes with the colour of each class
  make-guard PICTURE --out GUARD.json [--regions ...]      the guard from the first honest picture (provisional)
  check PICTURE... --guard GUARD.json [--previous PICTURE] [--regions ...]
        findings named 'place pictures: value range', '... detail energy', '... flat windows', '... palette', '... squint' (squint is a look, never a fail, unless the guard says squint_gate true)
  squint A B                                              the structural similarity of two pictures' 12 px blurred luminance
  crops PICTURE --boxes x,y,w,h ... --out-folder DIR [--previous PICTURE]     100 percent crops, with before-and-after strips when a previous picture is given
Plain lines start with PASS, LOOK or FAIL. Exit: 0 pass, 1 fail, 2 an input is missing or unusable.
A concrete example: a flat grey picture has every 96 x 96 window flat (spread 0), so `check` fails its flat-windows check; a picture of fine noise has a known detail energy.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main, read_json, InputProblem  # noqa: E402

PERCENTILES = (1, 5, 25, 50, 75, 95, 99)
MAX_SIDE = 2400


def finding(verdict, check, where, text, fix=''):
    return {'verdict': verdict, 'check': check, 'where': where, 'text': text, 'fix': fix}


# ---------------------------------------------------------------- pictures
def load_picture(path):
    """A picture as float32 RGB 0..1 (rows from the top), shrunk when it is wider than MAX_SIDE."""
    try:
        from PIL import Image
    except ImportError:
        raise InputProblem('Pillow is needed to read pictures (pip install pillow)')
    try:
        with Image.open(path) as picture:
            picture = picture.convert('RGB')
            if max(picture.size) > MAX_SIDE:
                scale = MAX_SIDE / max(picture.size)
                picture = picture.resize((max(1, int(picture.width * scale)), max(1, int(picture.height * scale))), Image.BOX)
            return np.asarray(picture, dtype=np.float32) / 255.0
    except FileNotFoundError:
        raise InputProblem(f'{path} is not there (it should be a picture, PNG or JPG)')
    except OSError as problem:
        raise InputProblem(f'{path} cannot be read as a picture ({problem})')


def luminance(rgb):
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)


def saturation(rgb):
    high, low = rgb.max(axis=2), rgb.min(axis=2)
    return np.where(high > 1e-4, (high - low) / np.maximum(high, 1e-4), 0.0).astype(np.float32)


def hue_degrees(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    high, low = rgb.max(axis=2), rgb.min(axis=2)
    delta = np.maximum(high - low, 1e-6)
    hue = np.where(high == r, ((g - b) / delta) % 6, np.where(high == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60.0
    return hue.astype(np.float32)


def gaussian_blur(array, sigma):
    """A separable gaussian blur of a 2D array (edges repeat)."""
    radius = max(1, int(round(sigma * 3)))
    kernel = np.exp(-(np.arange(-radius, radius + 1) ** 2) / (2.0 * sigma * sigma)).astype(np.float32)
    kernel /= kernel.sum()
    padded = np.pad(array.astype(np.float32), radius, mode='edge')
    horizontal = sum(kernel[i] * padded[:, i:i + array.shape[1]] for i in range(len(kernel)))
    return sum(kernel[i] * horizontal[i:i + array.shape[0], :] for i in range(len(kernel))).astype(np.float32)


def box_mean(array, size):
    """The mean over size x size windows (valid positions only), by integral images."""
    integral = np.pad(array.astype(np.float64).cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))
    total = integral[size:, size:] - integral[:-size, size:] - integral[size:, :-size] + integral[:-size, :-size]
    return (total / (size * size)).astype(np.float32)


# ---------------------------------------------------------------- measures
def percentiles_of(lum):
    return {str(p): float(np.percentile(lum, p)) for p in PERCENTILES}


def detail_energy(lum, blur_pixels, mask=None):
    """The mean of the absolute difference between the 8-bit luminance and its blur (a measure of fine contrast)."""
    eight = lum * 255.0
    difference = np.abs(eight - gaussian_blur(eight, blur_pixels))
    return float(difference[mask].mean()) if mask is not None and mask.any() else float(difference.mean())


SKY_TOP_SHARE = 0.4                  # without an id map, flat windows joined to the top edge count as sky only inside the top 40 percent of the picture


def flat_windows(lum, window, step, std_max, sky_mask=None, auto_sky=True):
    """How many window x window windows (every `step` pixels) are dead flat (spread under std_max), and the share under 0.014. Sky windows are left out: from the id map's sky mask when one
    is given, else (auto_sky) every flat window that reaches the top edge of the picture through flat windows above it and starts in the top 40 percent of the picture (a plain sky; a picture
    that is flat all the way down is still flat). 'sky_windows' says how many were left out and 'sky_from' where the sky came from."""
    rows, cols = lum.shape
    ys = list(range(0, rows - window + 1, step))
    xs = list(range(0, cols - window + 1, step))
    spread = [[float(lum[y:y + window, x:x + window].std()) for x in xs] for y in ys]
    sky = [[False] * len(xs) for _ in ys]
    sky_from = 'none'
    if sky_mask is not None:
        sky_from = 'the id map'
        for yi, y in enumerate(ys):
            for xi, x in enumerate(xs):
                sky[yi][xi] = bool(sky_mask[y:y + window, x:x + window].mean() > 0.5)
    elif auto_sky:
        sky_from = 'the flat top of the picture'
        for yi, y in enumerate(ys):
            if y >= SKY_TOP_SHARE * rows:
                break
            for xi in range(len(xs)):
                if spread[yi][xi] < std_max and (yi == 0 or sky[yi - 1][xi]):
                    sky[yi][xi] = True
    flat, near_flat, total, sky_count = 0, 0, 0, 0
    for yi in range(len(ys)):
        for xi in range(len(xs)):
            if sky[yi][xi]:
                sky_count += 1
                continue
            total += 1
            flat += spread[yi][xi] < std_max
            near_flat += spread[yi][xi] < 0.014
    return {'windows': total, 'flat': int(flat), 'share_under_0_014': (near_flat / total) if total else 0.0, 'sky_windows': sky_count, 'sky_from': sky_from if sky_count else 'none'}


def squint_similarity(first, second, blur_pixels=12, window=6):
    """The structural similarity (1.0 = identical) of the two pictures' blurred luminance, and the SSIM map."""
    a = gaussian_blur(luminance(first), blur_pixels)
    b = luminance(second)
    if a.shape != b.shape:
        from PIL import Image
        picture = Image.fromarray(np.clip(b * 255, 0, 255).astype(np.uint8)).resize((a.shape[1], a.shape[0]), Image.BOX)
        b = np.asarray(picture, dtype=np.float32) / 255.0
    b = gaussian_blur(b, blur_pixels)
    # the pictures are already blurred, so their local spread is tiny; the usual constants (for sharp pictures) would swamp it and make everything look alike
    c1, c2 = (0.01) ** 2, (0.004) ** 2
    mean_a, mean_b = box_mean(a, window), box_mean(b, window)
    var_a = box_mean(a * a, window) - mean_a ** 2
    var_b = box_mean(b * b, window) - mean_b ** 2
    covariance = box_mean(a * b, window) - mean_a * mean_b
    ssim = ((2 * mean_a * mean_b + c1) * (2 * covariance + c2)) / ((mean_a ** 2 + mean_b ** 2 + c1) * (var_a + var_b + c2))
    return float(ssim.mean()), ssim


def white_patch_size(rgb, lum):
    """The size in pixels of the biggest connected patch of near-white (blown-out) pixels."""
    white = (lum > 0.97) & (saturation(rgb) < 0.1)
    if not white.any():
        return 0
    rows, cols = white.shape
    seen = np.zeros_like(white)
    biggest = 0
    for start in zip(*np.nonzero(white)):
        if seen[start]:
            continue
        stack, size = [start], 0
        seen[start] = True
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols and white[rr, cc] and not seen[rr, cc]:
                    seen[rr, cc] = True
                    stack.append((rr, cc))
        biggest = max(biggest, size)
    return biggest


def region_masks(shape, regions_file=None, id_map=None, id_colours=None):
    """{name: boolean mask} from a regions JSON ({name: [x0, y0, x1, y1]} in pixels) or a flat-colour id picture plus {name: [r, g, b]}."""
    rows, cols = shape
    masks = {}
    if regions_file:
        for name, box in read_json(regions_file, 'a regions file', 'write {"name": [x0, y0, x1, y1]} in pixels').items():
            mask = np.zeros(shape, dtype=bool)
            x0, y0, x1, y1 = [int(v) for v in box]
            mask[max(y0, 0):y1, max(x0, 0):x1] = True
            masks[name] = mask
    if id_map and id_colours:
        ids = load_picture(id_map)
        if ids.shape[:2] != shape:
            from PIL import Image
            picture = Image.fromarray((ids * 255).astype(np.uint8)).resize((cols, rows), Image.NEAREST)
            ids = np.asarray(picture, dtype=np.float32) / 255.0
        for name, colour in read_json(id_colours, 'the id colours file', 'write {"class": [r, g, b]} with 0 to 255 values').items():
            target = np.array(colour, dtype=np.float32) / 255.0
            masks[name] = np.all(np.abs(ids - target) < 8.0 / 255.0, axis=2)
    return masks


def measure_picture(path, settings, masks_spec=None, previous=None):
    rgb = load_picture(path)
    lum = luminance(rgb)
    sat = saturation(rgb)
    hue = hue_degrees(rgb)
    blur = settings.value('place_measures.detail_energy_blur_pixels')
    masks = region_masks(lum.shape, *(masks_spec or (None, None, None)))
    energy = {'all': detail_energy(lum, blur)}
    for name, mask in masks.items():
        if name not in ('sky', 'accent') and mask.any():
            energy[name] = detail_energy(lum, blur, mask)
    accent = masks.get('accent')
    strong_level = settings.value('place_measures.strong_saturation_level')
    strong = (sat > strong_level) & (~accent if accent is not None else True)
    band = settings.value('place_measures.turquoise_hue_band')
    turquoise = (hue >= band[0]) & (hue <= band[1]) & (sat >= settings.value('place_measures.turquoise_saturation_min'))
    result = {'file': os.path.basename(path), 'size': [int(lum.shape[1]), int(lum.shape[0])], 'percentiles': percentiles_of(lum), 'mean_saturation': float(sat.mean()),
              'detail_energy': energy, 'flat_windows': flat_windows(lum, settings.value('place_measures.flat_window_pixels'), settings.value('place_measures.flat_window_step_pixels'),
                                                                   settings.value('place_measures.flat_window_std_max'), masks.get('sky')),
              'strong_saturation_share': float(strong.mean()), 'turquoise_share': float(turquoise.mean()), 'white_patch_pixels': int(white_patch_size(rgb, lum))}
    if previous is not None:
        score, ssim = squint_similarity(load_picture(previous), rgb, settings.value('place_measures.squint_blur_pixels'), settings.value('place_measures.squint_window_pixels'))
        result['squint'] = {'against': os.path.basename(previous), 'similarity': score, 'loses_most': sorted(((float(ssim[m[:ssim.shape[0], :ssim.shape[1]]].mean()) if m[:ssim.shape[0], :ssim.shape[1]].any() else 1.0, n)
                                                                                                               for n, m in masks.items() if n not in ('sky', 'accent')))[:3]}
    result['regions'] = sorted(energy)
    return result


# ---------------------------------------------------------------- guard and check
def make_guard(measured, view=None, settings=None):
    """A style guard from one picture (provisional). When that picture is already over a house limit for turquoise or strong colour (a place whose water is teal, a red-painted barn), the
    guard records the allowance it needs (1.5 times what the picture has), so a guard never fails the very picture it was made from for a taste rule of another place."""
    guard = {'made_from': measured['file'], 'view': view, 'provisional': True, 'percentiles': measured['percentiles'], 'mean_saturation': measured['mean_saturation'],
             'detail_energy': measured['detail_energy'], 'regions': sorted(measured['detail_energy']), 'accent': {'name': None}, 'squint_gate': False,
             'note': 'made from the first honest picture: it is provisional until a person accepts it (remove "provisional" and write who and when)'}
    if settings is not None:
        for key, limit_key in (('turquoise_share', 'turquoise_share_max'), ('strong_saturation_share', 'strong_saturation_share_max')):
            limit = settings.value(f'place_measures.{limit_key}')
            if measured[key] > limit:
                guard[limit_key] = round(measured[key] * 1.5, 4)
                guard['note'] += f'; this place has {measured[key]:.2%} {key.replace("_", " ")} in its first picture (the house limit is {limit:.2%}), so the guard allows up to {guard[limit_key]:.2%}'
    return guard


def guard_for(guard_data, path):
    """The guard that applies to one picture. A guard file is one guard, or {"guards": {view: guard}, "default_view": view}: the guard whose view name is in the picture's file name (the
    longest such name), else the default view's. Views differ (a wide view and a close-up have different value ranges), so one guard need not serve them all."""
    if 'guards' not in guard_data:
        return guard_data
    base = os.path.basename(path).lower()
    matches = sorted((view for view in guard_data['guards'] if view and view.lower() in base), key=len, reverse=True)
    chosen = matches[0] if matches else guard_data.get('default_view') or next(iter(guard_data['guards']))
    return guard_data['guards'][chosen]


def check_picture(measured, guard, settings):
    findings = []
    where = measured['file']
    tolerance = settings.value('place_measures.percentile_tolerance')
    off = [f'p{p} {measured["percentiles"][p]:.3f} vs {guard["percentiles"][p]:.3f}' for p in measured['percentiles'] if abs(measured['percentiles'][p] - guard['percentiles'][p]) > tolerance]
    problems = []
    if off:
        problems.append('value range off by more than ' + f'{tolerance}: ' + ', '.join(off[:4]))
    if measured['percentiles']['99'] > settings.value('place_measures.percentile_99_max'):
        problems.append(f'the brightest 1 percent is {measured["percentiles"]["99"]:.2f} (at most {settings.value("place_measures.percentile_99_max")})')
    drift = abs(measured['mean_saturation'] - guard['mean_saturation'])
    if drift > settings.value('place_measures.mean_saturation_tolerance'):
        problems.append(f'mean saturation {measured["mean_saturation"]:.2f} vs the guard\'s {guard["mean_saturation"]:.2f}')
    findings.append(finding('fail' if problems else 'pass', 'place pictures: value range', where, '; '.join(problems) or 'the value range and mean colour match the guard'))
    low, high, cap = settings.value('place_measures.detail_energy_ratio_low'), settings.value('place_measures.detail_energy_ratio_high'), settings.value('place_measures.detail_energy_cap')
    bad = []
    for region, wanted in guard['detail_energy'].items():
        if region in measured['detail_energy']:
            got = measured['detail_energy'][region]
            upper = min(high * wanted, cap)
            if got < low * wanted:
                bad.append(f'{region} too flat ({got:.2f}, the guard has {wanted:.2f}: at least {low * wanted:.2f})')
            elif got > upper:
                bad.append(f'{region} too busy ({got:.2f}, at most {upper:.2f}): fewer, bigger, cleaner marks')
    findings.append(finding('fail' if bad else 'pass', 'place pictures: detail energy', where, '; '.join(bad) or 'fine detail is within the guard\'s band in every region',
                            'less noise and finer texture where it is too busy; bigger designed marks and shape where it is too flat' if bad else ''))
    windows = measured['flat_windows']
    if windows['flat'] > 0:
        sky_note = f' ({windows.get("sky_windows", 0)} sky windows were left out, found from {windows.get("sky_from", "none")})' if windows.get('sky_windows') else ' (no sky was found to leave out: give --id-map with a sky class if a plain sky is in the picture)'
        findings.append(finding('fail', 'place pictures: flat windows', where, f'{windows["flat"]} of {windows["windows"]} windows are dead flat (spread under {settings.value("place_measures.flat_window_std_max")}): plain colour with no surface{sky_note}',
                                'look at where they are: a plain slab needs a normal map and variation; a smooth surface that only LOOKS flat (still water, glass, a smooth wall) may need Cycles (reflections) or a designed mark, not more noise'))
    elif windows['share_under_0_014'] > settings.value('place_measures.flat_window_share_under_0_014_max'):
        findings.append(finding('warn', 'place pictures: flat windows', where, f'{windows["share_under_0_014"]:.1%} of windows are nearly flat (more than {settings.value("place_measures.flat_window_share_under_0_014_max"):.0%})'))
    else:
        findings.append(finding('pass', 'place pictures: flat windows', where, 'no flat windows'))
    palette = []
    strong_limit = max(settings.value('place_measures.strong_saturation_share_max'), guard.get('strong_saturation_share_max') or 0.0)
    if measured['strong_saturation_share'] > strong_limit:
        palette.append(f'{measured["strong_saturation_share"]:.1%} of pixels are strongly coloured (at most {strong_limit:.1%})')
    turquoise_limit = max(settings.value('place_measures.turquoise_share_max'), guard.get('turquoise_share_max') or 0.0)
    if measured['turquoise_share'] > turquoise_limit:
        palette.append(f'{measured["turquoise_share"]:.2%} of pixels are turquoise (at most {turquoise_limit:.2%}; a place with teal water writes its own allowance into its guard)')
    if measured['white_patch_pixels'] > settings.value('place_measures.white_patch_pixels_max'):
        palette.append(f'a blown-out white patch of {measured["white_patch_pixels"]} pixels (at most {settings.value("place_measures.white_patch_pixels_max")})')
    findings.append(finding('fail' if palette else 'pass', 'place pictures: palette', where, '; '.join(palette) or 'no strongly coloured, turquoise or blown-out areas'))
    if 'squint' in measured:
        score, target = measured['squint']['similarity'], settings.value('place_measures.squint_target')
        gate = bool(guard.get('squint_gate'))
        if score >= target:
            findings.append(finding('pass', 'place pictures: squint', where, f'the big shapes and light are as before (similarity {score:.3f}, target {target})'))
        else:
            where_lost = ', '.join(f'{n} ({v:.2f})' for v, n in measured['squint']['loses_most']) or 'no regions given'
            findings.append(finding('fail' if gate else 'warn', 'place pictures: squint', where,
                                    f'similarity {score:.3f} is under {target}: the big shapes or light changed; it loses most in {where_lost}. Report it plainly and never remove character to chase it; the person decides.'))
    return findings


def verdict_of(findings):
    verdicts = {f['verdict'] for f in findings}
    return 'fail' if 'fail' in verdicts else 'warn' if 'warn' in verdicts else 'pass'


def plain_lines(findings, header):
    word = {'fail': 'FAIL', 'warn': 'LOOK', 'pass': 'PASS', 'known': 'KNOWN'}
    lines = [header]
    for f in findings:
        lines.append(f'{word[f["verdict"]]} {f["check"]} [{f["where"]}]: {f["text"]}' + (f'  Fix: {f["fix"]}' if f.get('fix') and f['verdict'] != 'pass' else ''))
    return lines


# ---------------------------------------------------------------- commands
def regions_of(args):
    return (args.regions, args.id_map, args.id_colours)


def command_measure(args, settings):
    results = [measure_picture(p, settings, regions_of(args), args.previous) for p in args.pictures]
    lines = []
    for r in results:
        lines.append(f'{r["file"]} ({r["size"][0]} x {r["size"][1]}): luminance percentiles ' + ', '.join(f'{k}: {v:.3f}' for k, v in r['percentiles'].items())
                     + f'; mean saturation {r["mean_saturation"]:.3f}; detail energy ' + ', '.join(f'{k} {v:.2f}' for k, v in r['detail_energy'].items())
                     + f'; flat windows {r["flat_windows"]["flat"]} of {r["flat_windows"]["windows"]}; strong colour {r["strong_saturation_share"]:.2%}; turquoise {r["turquoise_share"]:.2%}'
                     + (f'; squint {r["squint"]["similarity"]:.3f}' if 'squint' in r else ''))
    finish('picture_measures measure', {'about': 'The measures of the given pictures.', 'pictures': results, 'verdict': 'pass'}, ['PASS ' + l for l in lines], settings, args)
    return 0


def command_make_guard(args, settings):
    if not args.pictures:
        raise InputProblem('give the first honest picture of the place: picture_measures.py make-guard PICTURE --out GUARD.json [--view NAME]')
    measured = measure_picture(args.pictures[0], settings, regions_of(args))
    guard = make_guard(measured, view=args.view, settings=settings)
    # the guard file is read BEFORE the report is written: the report's --out is the same file, and writing it first would wipe the guards of the other views
    existing = {}
    if args.out and args.view and os.path.exists(args.out):
        try:
            with open(args.out) as handle:
                existing = json.load(handle)
        except ValueError:
            existing = {}
    result = {'about': 'A style guard made from one picture (provisional).', 'guard': guard, 'verdict': 'pass'}
    lines = [f'PASS guard made from {guard["made_from"]}: provisional until a person accepts it', f'LOOK {guard["note"]}']
    finish('picture_measures make-guard', result, lines, settings, args)
    if args.out:
        to_write = guard
        if args.view:
            # one guard file for several views: this view's guard is added to (or replaces its place in) the file; pictures are checked against the guard whose view name is in their file name
            guards = existing['guards'] if 'guards' in existing else ({(existing.get('view') or 'default'): existing} if existing.get('percentiles') else {})
            guards[args.view] = guard
            to_write = {'guards': guards, 'default_view': existing.get('default_view') or next(iter(guards)), 'provisional': any(g.get('provisional') for g in guards.values()),
                        'note': 'one guard per view; a picture is checked against the guard whose view name is in its file name, else the default view\'s'}
        with open(args.out, 'w') as handle:
            json.dump(to_write, handle, indent=1)
    return 0


def command_check(args, settings):
    guard = read_json(args.guard, 'the style guard', 'picture_measures.py make-guard PICTURE --out GUARD.json (from the first honest picture)')
    findings = []
    measured_all = []
    for path in args.pictures:
        measured = measure_picture(path, settings, regions_of(args), args.previous)
        measured_all.append(measured)
        findings += check_picture(measured, guard_for(guard, path), settings)
    verdict = verdict_of(findings)
    made_from = ', '.join(sorted({g.get('made_from', '?') for g in guard['guards'].values()})) if 'guards' in guard else guard.get('made_from')
    lines = plain_lines(findings, f'Picture measures of {len(args.pictures)} picture(s) against the guard made from {made_from}: {verdict.upper()}.')
    finish('picture_measures check', {'about': 'Pictures against a style guard.', 'verdict': verdict, 'checks': findings, 'measures': measured_all}, lines, settings, args)
    return 1 if verdict == 'fail' else 0


def command_squint(args, settings):
    score, _ = squint_similarity(load_picture(args.first), load_picture(args.second), settings.value('place_measures.squint_blur_pixels'), settings.value('place_measures.squint_window_pixels'))
    target = settings.value('place_measures.squint_target')
    word = 'PASS' if score >= target else 'LOOK'
    finish('picture_measures squint', {'about': 'Squint test.', 'similarity': score, 'target': target, 'verdict': 'pass' if score >= target else 'warn'},
           [f'{word} squint similarity {score:.3f} (target {target})'], settings, args)
    return 0


def command_crops(args, settings):
    from PIL import Image
    picture = Image.open(args.picture).convert('RGB')
    previous = Image.open(args.previous).convert('RGB') if args.previous else None
    os.makedirs(args.out_folder, exist_ok=True)
    written = []
    for index, box in enumerate(args.boxes or []):
        x, y, w, h = [int(v) for v in box.split(',')]
        crop = picture.crop((x, y, x + w, y + h))
        path = os.path.join(args.out_folder, f'crop_{index + 1}_{x}_{y}_{w}x{h}.png')
        crop.save(path)
        written.append(path)
        if previous is not None:
            before = previous.resize(picture.size).crop((x, y, x + w, y + h))
            strip = Image.new('RGB', (w * 2 + 8, h), (255, 255, 255))
            strip.paste(before, (0, 0))
            strip.paste(crop, (w + 8, 0))
            path = os.path.join(args.out_folder, f'strip_{index + 1}_before_after.png')
            strip.save(path)
            written.append(path)
    finish('picture_measures crops', {'about': 'Crops.', 'written': written, 'verdict': 'pass'}, [f'PASS {p}' for p in written] or ['LOOK no boxes were given (--boxes x,y,w,h)'], settings, args)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Measures pictures of a place (value range, detail energy, flat windows, palette, squint), makes a style guard from the first honest picture and checks later pictures against it. See the note at the top of this file.')
    commands = parser.add_subparsers(dest='command', required=True)

    def regions(p):
        p.add_argument('--regions', help='a regions JSON {"name": [x0, y0, x1, y1]} in pixels')
        p.add_argument('--id-map', dest='id_map', help='a flat-colour picture of role classes')
        p.add_argument('--id-colours', dest='id_colours', help='{"class": [r, g, b]} for the id map')

    p = add_output_options(commands.add_parser('measure', help='the numbers for each picture'))
    p.add_argument('pictures', nargs='+')
    p.add_argument('--previous', help='the previous round\'s picture (adds the squint test)')
    regions(p)
    p = add_output_options(commands.add_parser('make-guard', help='a guard from the first honest picture'))
    p.add_argument('pictures', nargs=1)
    p.add_argument('--view', help='the view this guard is for (a name inside its pictures\' file names); several views share one --out file')
    regions(p)
    p = add_output_options(commands.add_parser('check', help='pictures against a guard'))
    p.add_argument('pictures', nargs='+')
    p.add_argument('--guard', required=True)
    p.add_argument('--previous')
    regions(p)
    p = add_output_options(commands.add_parser('squint', help='the squint test of two pictures'))
    p.add_argument('first')
    p.add_argument('second')
    p = add_output_options(commands.add_parser('crops', help='100 percent crops'))
    p.add_argument('picture')
    p.add_argument('--boxes', nargs='+')
    p.add_argument('--previous')
    p.add_argument('--out-folder', dest='out_folder', required=True)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    return {'measure': command_measure, 'make-guard': command_make_guard, 'check': command_check, 'squint': command_squint, 'crops': command_crops}[args.command](args, settings)


if __name__ == '__main__':
    sys.exit(run_main(main, 'picture_measures'))
