"""What this does: the small picture measures the three painting tools share (paint_request.py before a painting is
asked for, after_painting.py when it comes back, plan_states.py for the pictures a held shot cuts to), so each is
written once. It does not run on its own; the three tools call it.

It holds:
  - loading a view the way the shot checker does (check_shot.Shot: the check file, shot_facts.py's facts folder with
    ids.png and solo/ pictures), and its masks at any picture size;
  - which groups are people (the check file's "figures", or the place facts' figures matched to the check file's groups);
  - brightness, a figure's brightness against what surrounds it, skin-coloured pixels on a head;
  - the stage's colour finish (exposure, ACES curve, contrast, film tint, lift) ported from cinema-stage.js, so a
    plate colour can be judged as it will look in the film (round 2: tan coats came out crimson);
  - running the kit's own tools (align_painting.py, keep_painted_shadows.py, make_state_picture.py) and reading the
    numbers they print, instead of copying their sums here.
Every number it uses comes from film-settings.json through the caller's Settings (the caller names them in its report).
"""
import json
import math
import os
import re
import subprocess
import sys
import types
from fnmatch import fnmatch

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
TOOLS = os.path.join(KIT, 'paper-film', 'tools')
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import check_shot  # noqa: E402  (the shot checker: its Shot loads a view's masks exactly as every check sees them)

LOSSLESS_ENDINGS = ('.png', '.webp')


# ------------------------------------------------------------------------------------------------ loading a view
def load_shot(check_path, facts_folder, picture=None):
    """The shot checker's view of a check file and a facts folder (shot_facts.py's output for the PLATE's camera and lens)."""
    for needed in ('facts.json', 'ids.png'):
        if not os.path.exists(os.path.join(facts_folder, needed)):
            raise SystemExit(f'painting tools: {facts_folder} has no {needed}: measure the plate with shot_facts.py '
                             f'(the plate\'s own camera and lens) first')
    return check_shot.Shot(types.SimpleNamespace(check=check_path, facts=facts_folder, picture=picture, out='/tmp', title='',
                                                 render_log=None))


def read_rgb(path, size=None):
    """A picture as float RGB 0-255; resized with the area filter when a (width, height) is given."""
    picture = cv2.imread(path, cv2.IMREAD_COLOR)
    if picture is None:
        raise SystemExit(f'painting tools: can\'t read the picture {path}')
    if size and (picture.shape[1], picture.shape[0]) != tuple(size):
        picture = cv2.resize(picture, tuple(size), interpolation=cv2.INTER_AREA)
    return picture[:, :, ::-1].astype(np.float32)


def mask_at(mask, size, smooth=False):
    """A facts-size mask (1080 x 1920) at a picture's (width, height): nearest neighbour, so it stays yes/no; smooth=True
    resizes it bilinearly and keeps what is over half (smoother outlines, as the figures helper's masks.py did)."""
    if (mask.shape[1], mask.shape[0]) == tuple(size):
        return mask.astype(bool)
    if smooth:
        return cv2.resize(mask.astype(np.float32), tuple(size), interpolation=cv2.INTER_LINEAR) > 0.5
    return cv2.resize(mask.astype(np.uint8), tuple(size), interpolation=cv2.INTER_NEAREST).astype(bool)


def read_painting_at_plate_size(path, size):
    """A returned painting resized to the plate the way the ledgers' paintings were (PIL's Lanczos filter): this reproduces
    the people test's painted-1-plate-size.png exactly (0 levels off), and so its line-up numbers."""
    from PIL import Image
    with Image.open(path) as picture:
        picture = picture.convert('RGB')
        if picture.size != tuple(size):
            picture = picture.resize(tuple(size), Image.LANCZOS)
        return np.asarray(picture).astype(np.float32)


def luminance(rgb):
    """Brightness 0-255 (Rec. 709 weights, as every project measure used)."""
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def hsv(rgb):
    """OpenCV HSV: hue 0-180 (half degrees), saturation and value 0-255."""
    return cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)


def box_of(mask):
    ys, xs = np.nonzero(mask)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None


# ------------------------------------------------------------------------------------------------ who is a figure
def figure_groups(shot, place_facts=None):
    """The check file's groups that are people: its "figures" list, else the groups whose object patterns match a figure
    of the place facts (people-test: "man stooped" holds "figure-stooped")."""
    listed = [g for g in shot.check.get('figures', []) if g in shot.facts['groups']]
    if listed:
        return listed
    names = [f['name'] for f in (place_facts or {}).get('figures', [])]
    found = []
    for group, patterns in shot.check.get('groups', {}).items():
        if group in shot.facts['groups'] and any(fnmatch(n, p) for n in names for p in patterns):
            found.append(group)
    return found


def figure_record(shot, group, place_facts):
    """The place facts' figure behind a check-file group (its feet, facing and height), or None."""
    patterns = shot.check.get('groups', {}).get(group, [group])
    for f in (place_facts or {}).get('figures', []):
        if any(fnmatch(f['name'], p) for p in patterns):
            return f
    return None


# ------------------------------------------------------------------------------------------------ figure measures
def scaled(pixels_at_1536, width):
    """A pixel size set on a 1,536-wide plate, at this picture's width (odd, at least 3)."""
    return max(3, int(round(pixels_at_1536 * width / 1536)) | 1)


def figure_surround_ratio(lum, mask, all_figures, settings):
    """A figure's mean brightness inside its outline (eroded) over the mean of a ring round it (people left out), as the
    people test's looks helper measured it (redesign people-paint/check-looks/scripts/measure1.py): erode 7 px, ring from
    13 to 61 px out, at 1,536 wide. Plate about 0.15, painting about 0.50 for the dark men."""
    ring_sizes = settings.value('painting_tools.after_painting.figure_ring_pixels_at_1536')
    width = mask.shape[1]
    m8 = mask.astype(np.uint8)
    inner = cv2.erode(m8, np.ones((scaled(ring_sizes['erode'], width),) * 2, np.uint8)).astype(bool)
    if inner.sum() < 20:
        inner = mask
    outer = cv2.dilate(m8, np.ones((scaled(ring_sizes['ring_outer'], width),) * 2, np.uint8)).astype(bool)
    gap = cv2.dilate(m8, np.ones((scaled(ring_sizes['ring_inner'], width),) * 2, np.uint8)).astype(bool)
    ring = outer & ~gap & ~all_figures
    if not inner.any() or not ring.any():
        return None
    return float(lum[inner].mean() / max(1e-6, lum[ring].mean()))


def skin_pixels(rgb):
    """Skin-coloured pixels (the usual rule for lit skin: R > 95, G > 40, B > 20, spread over 15, R above G by 15 and
    above B). On the people test it reads 0 in the plate and 184 in the painting inside the box round the hand-on-bar
    man's head that the figures helper measured (0 and 183)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    top, bottom = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    return (r > 95) & (g > 40) & (b > 20) & (top - bottom > 15) & (np.abs(r - g) > 15) & (r > g) & (r > b)


def head_region(mask, settings):
    """The head of a standing figure: the top share of its outline (a 0.23 m head on a 1.75 m figure), widened a little so
    an ear or cheek the painter put just outside the plate's outline is counted."""
    head_share = settings.value('people.head_height_metres') / settings.value('people.figure_height_metres')
    widen_share = settings.value('painting_tools.after_painting.head_widen_share_of_height')
    box = box_of(mask)
    if box is None:
        return mask
    top, height = box[1], box[3] - box[1] + 1
    head = mask & (np.arange(mask.shape[0])[:, None] < top + head_share * height)
    radius = max(1, int(round(widen_share * height)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))
    return cv2.dilate(head.astype(np.uint8), kernel).astype(bool)


def head_and_coat(lum, mask, settings):
    """Mean brightness of the band under the cap (the lower half of the head) and of the coat (the torso), for a figure
    seen from behind: a head paler than its coat reads as a bald dummy or a face to the painter (round 1: heads 80/54/35
    over coats 39/25/14; round 3 after the fix: head band 12 against coat 25)."""
    head_share = settings.value('people.head_height_metres') / settings.value('people.figure_height_metres')
    coat_band = settings.value('painting_tools.paint_request.coat_band_share_of_height')
    box = box_of(mask)
    if box is None:
        return None, None
    top, height = box[1], box[3] - box[1] + 1
    rows = np.arange(mask.shape[0])[:, None]
    band = mask & (rows >= top + 0.5 * head_share * height) & (rows < top + head_share * height)
    coat = mask & (rows >= top + coat_band[0] * height) & (rows < top + coat_band[1] * height)
    if band.sum() < 5 or coat.sum() < 5:
        return None, None
    return float(lum[band].mean()), float(lum[coat].mean())


# ------------------------------------------------------------------------------------------------ the stage's finish
def srgb_to_linear(values):
    v = np.asarray(values, np.float64) / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(values):
    c = np.asarray(values, np.float64)
    return np.where(c < 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 1e-12), 1 / 2.4) - 0.055) * 255.0


def stage_finish(rgb, look):
    """A plate colour (0-255 sRGB) as the film shows it, through cinema-stage.js's finish pass with a page's look (exposure,
    ACES filmic curve, saturation, contrast, film tint, lift). Glow, vignette, grain and the projector's softening are
    left out, so it is a sum for dark cloth, not for lamps. Round 3's slate-grey coats (plate about 46/39/32) come out
    about 30/18/4 here against 27/16/3 sampled from the film."""
    c = srgb_to_linear(rgb) * look['exposure']
    c = np.clip((c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14), 0, 1)
    luma = c @ np.array([0.2126, 0.7152, 0.0722])
    c = luma[..., None] + (c - luma[..., None]) * look['saturation']
    c = (c - 0.5) * look['contrast'] + 0.5
    t = np.clip((luma - 0.05) / 0.70, 0, 1)
    t = t * t * (3 - 2 * t)
    shadow, high = np.array(look['shadow_tint']), np.array(look['highlight_tint'])
    tint = shadow + (high - shadow) * t[..., None]
    c = c + (c * tint * 2.0 - c) * look['tint_amount']
    c = c + look['lift'] * (1 - c)
    return linear_to_srgb(np.clip(c, 0, 1))


def hue_degrees_and_saturation(rgb):
    """Hue in degrees (0-360) and saturation (0-1) of one colour."""
    r, g, b = [float(x) / 255 for x in rgb]
    top, bottom = max(r, g, b), min(r, g, b)
    if top - bottom < 1e-9:
        return 0.0, 0.0
    if top == r:
        hue = ((g - b) / (top - bottom)) % 6
    elif top == g:
        hue = (b - r) / (top - bottom) + 2
    else:
        hue = (r - g) / (top - bottom) + 4
    return hue * 60.0, (top - bottom) / top


def in_hue_band(hue, band):
    low, high = band
    return (hue >= low or hue <= high) if low > high else (low <= hue <= high)


# ------------------------------------------------------------------------------------------------ the kit's own tools
def run_tool(script, arguments, timeout=900):
    """Runs one of the kit's tools (paper-film/tools) with this Python and returns its printed output; stops with the
    tool's own words if it fails."""
    path = os.path.join(TOOLS, script)
    run = subprocess.run([sys.executable, '-I', '-B', path] + [str(a) for a in arguments], capture_output=True, text=True, timeout=timeout)
    if run.returncode != 0:
        raise SystemExit(f'painting tools: {script} failed (exit {run.returncode}):\n{(run.stdout + run.stderr)[-1500:]}')
    return run.stdout + run.stderr


ALIGN_LINE = re.compile(r'unaligned agreement ([0-9.]+); best ([0-9.]+) at stretch ([0-9.]+), shift ([+-][0-9.]+), ([+-][0-9.]+) pixels \(of (\d+) wide\)')


def align(check_path, facts_folder, painting, out_path, against=None, groups=()):
    """align_painting.py on a painting (at the plate's size); returns its numbers: agreement before and after, stretch,
    shift (pixels of the facts' frame width) and that width."""
    arguments = [check_path, facts_folder, painting, out_path] + (['--against', against] if against else []) + list(groups)
    text = run_tool('align_painting.py', arguments)
    found = ALIGN_LINE.search(text)
    if not found:
        raise SystemExit(f'painting tools: could not read align_painting.py\'s result:\n{text[-800:]}')
    before, after, stretch, dx, dy, width = found.groups()
    return {'before': float(before), 'after': float(after), 'stretch': float(stretch), 'shift': [float(dx), float(dy)],
            'shift_frame_width': int(width), 'printed': found.group(0)}


STATE_LINES = {
    'noise': re.compile(r'noise between the plates .* ([0-9.]+) levels \(99th percentile\)'),
    'differ': re.compile(r'used: plates differ over ([0-9.]+)% of the frame; outlines ([0-9.]+)%; second painting fully over ([0-9.]+)%, partly over ([0-9.]+)%'),
    'used': re.compile(r'threshold\s+([0-9.]+), faint\s+([0-9.]+):\s+([0-9.]+)%\s+<- used'),
    'outside': re.compile(r'read back from the written picture: (\d+) levels'),
}


def state_mask_shares(main, second, plate, helper, out_folder, facts_folder=None, groups=(), threshold=6, faint=3, keep=False):
    """make_state_picture.py on a pair (the free test when main/second are the plates themselves); returns the mask's
    shares of the frame as it printed them. Its pictures go to out_folder and are deleted unless keep is true."""
    os.makedirs(out_folder, exist_ok=True)
    picture, mask = os.path.join(out_folder, 'state-trial.png'), os.path.join(out_folder, 'state-trial-mask.png')
    arguments = [main, second, plate, helper, picture, mask, '--threshold', threshold, '--faint', faint]
    if facts_folder and groups:
        arguments += ['--outlines', facts_folder] + list(groups)
    text = run_tool('make_state_picture.py', arguments)
    if not keep:
        for path in (picture, mask):
            if os.path.exists(path):
                os.remove(path)
    result = {'printed': text}
    for key, pattern in STATE_LINES.items():
        found = pattern.search(text)
        if found:
            result[key] = [float(x) for x in found.groups()]
    if 'used' not in result or 'differ' not in result:
        raise SystemExit(f'painting tools: could not read make_state_picture.py\'s numbers:\n{text[-800:]}')
    return {'mask_share': result['used'][2] / 100, 'plates_differ_share': result['differ'][0] / 100,
            'outline_share': result['differ'][1] / 100, 'full_share': result['differ'][2] / 100, 'part_share': result['differ'][3] / 100,
            'noise_levels': result['noise'][0] if 'noise' in result else None,
            'outside_levels': int(result['outside'][0]) if 'outside' in result else None}


def is_lossless(path):
    return os.path.splitext(path)[1].lower() in LOSSLESS_ENDINGS


def load_json(path):
    with open(path) as handle:
        return json.load(handle)


def round_all(value, digits=4):
    if isinstance(value, float):
        return round(value, digits) if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: round_all(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [round_all(v, digits) for v in value]
    if isinstance(value, (np.floating,)):
        return round(float(value), digits)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value
