"""What this does: gets a plate ready to be painted and writes the request for the painter (Flux 3 edit on fal), so the
prompt, the pictures to send and the price are worked out the same way every time instead of by hand. It spends nothing:
it writes the request, and a person says yes before anything is sent.

Three jobs, each its own command:
  preflight  checks the plate before paying (a failure stops the request):
             - the render log has no render faults; the shot checker's light rules passed (give its report);
             - thin parts (wires, rungs, bars under about 6 px at 1080 wide) that the painter will smear;
             - lettering in the plate (the painter garbles it: keep it on its own surface);
             - even bright discs and near-black holes round the story (log 32: soup in the drum, an open-looking gate);
             - a glow inside a hollow prop's top (lesson 138: the painter lifts it into a bright band; darken it first);
             - figures: a head paler than its coat (reads as a bald dummy or a face), cloth the film's colour finish turns
               red (round 2's tan coats came out crimson), a figure barely darker than its surround (the painter lifts
               figures about 3 times toward their surround), figures casting long shadows (lesson 135: the painter
               leaves them when asked to remove the figures; needs --helper-plate, the plate drawn without them);
             - real people's names in the prompt or the group names (only typed name cards show real people).
  prompt     writes the main prompt (templates/paint-prompt.txt) and the behind prompt (templates/behind-prompt.txt):
             the Keep list of every group that shows (each with its "paint_as" words from the check file), where warm
             light stays, thin parts, edges that meet, the people (how many, near and far, which way they face, no
             faces, flat dark far walkers, a facing man's face lost in shadow with no lit cheek, kept as dark as in
             image 1), lettering as plain marks, and what never to add. Which things to name is measured from the plate
             and its facts; the descriptions are a person's words (check file "paint_as", and a short brief).
  price      the estimated price: the dated rate in film-settings.json times (the megapixels returned + every picture
             sent). fal shows no exact charge, so this stays an estimate until fit-price fits it to real charges.
  request    all three, plus the request file (model, settings, pictures and their sizes) and an optional planned entry
             in a paintings ledger. It refuses when the preflight fails (unless --ignore-preflight) or when the price
             would pass what is left of the allowance.
  fit-price  fits the rate to real charges you read from fal (a JSON list of {"request_id", "cents", "output", "inputs"}).

Inputs: --check (the view's shot-check file, with "paint_as" words and optional "hollow", "figures", "behind_as"),
--facts (shot_facts.py's folder for the PLATE's camera and lens), --plate (the plate picture), --brief (a short JSON of a
person's words for the place: its sentence, set things to keep, notes, colours, warm-light words, the people's dress and
poses, removed parts, library props, what lies behind; see tests/fixtures/painting/*-brief.json), --place-facts and
--view (figures' facing, the slide, the film camera). Optional: --helper-plate, --render-log, --shot-report,
--real-names FILE, --exposure (the page's), --hollow GROUP... (props with an open top), --behind-remove figures|GROUP...,
--keep-wetness (a place built wet: the prompt keeps its wet ground, puddles and reflections and forbids only new ones, where the default words
forbid every puddle and reflection)
The request is refused without a render log and a shot report (a paid repaint needs both, decision 37).

Use:
  python3 paint_request.py preflight --check C.json --facts PLATE_FACTS --plate plate.png [--helper-plate H.png] ...
  python3 paint_request.py prompt --check C.json --facts PLATE_FACTS --plate plate.png --brief B.json --place-facts P.json --view V
  python3 paint_request.py price [--returned 1504x2672] [--send 1536x2730 --send 768x1368] [--behind]
  python3 paint_request.py request ... --out-folder DIR [--ledger LEDGER.json]
  python3 paint_request.py fit-price --charges charges.json
Every command prints a plain report (or --json) naming the film-settings.json values it used.
"""
import argparse
import json
import math
import os
import re
import shutil
import sys
import tempfile

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings, resolve_profile  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402
import frame_geometry as geometry  # noqa: E402
import painting_measures as measures  # noqa: E402
from painting_measures import check_shot  # noqa: E402

TEMPLATES = os.path.join(HERE, 'templates')
NUMBER_WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']


def number_words(n):
    return NUMBER_WORDS[n] if 0 <= n < len(NUMBER_WORDS) else str(n)


def join_words(items, last='and'):
    items = [i for i in items if i]
    if len(items) <= 1:
        return ''.join(items)
    return ', '.join(items[:-1]) + f' {last} ' + items[-1]


# ------------------------------------------------------------------------------------------------ templates
def load_template(name):
    """A template file: the prompt's lines (with {slots}) and its [sentences] frames."""
    lines, sentences, in_sentences = [], {}, False
    for raw in open(os.path.join(TEMPLATES, name)):
        line = raw.rstrip('\n')
        if line.startswith('#') or not line.strip():
            continue
        if line.strip() == '[sentences]':
            in_sentences = True
            continue
        if in_sentences:
            key, _, text = line.partition('=')
            sentences[key.strip()] = text.strip()
        else:
            lines.append(line)
    return lines, sentences


def fill_lines(lines, slots):
    """Fills each line; a line whose only slot is empty is dropped; returns the parts in order (slot name, text)."""
    parts = []
    for line in lines:
        names = re.findall(r'\{(\w+)\}', line)
        values = {n: slots.get(n, '') for n in names}
        if names and all(not values[n] for n in names) and line.strip() == '{' + names[0] + '}':
            continue
        text = line.format(**values).strip()
        if text:
            parts.append((names[0] if len(names) == 1 and line.strip() == '{' + names[0] + '}' else 'fixed', text))
    return parts


# ------------------------------------------------------------------------------------------------ the view
class View:
    """One view's plate, its facts, check file, brief and place facts, and the measures the prompt and preflight share."""

    def __init__(self, args, settings):
        self.settings = settings
        self.shot = measures.load_shot(args.check, args.facts)
        self.width, self.height = self.shot.width, self.shot.height
        self.check = self.shot.check
        self.plate_path = args.plate
        self.plate = measures.read_rgb(args.plate, (self.width, self.height)) if args.plate else None
        self.brief = measures.load_json(args.brief) if getattr(args, 'brief', None) else {}
        self.keep_wetness = bool(getattr(args, 'keep_wetness', False) or self.brief.get('keep_wetness'))
        self.place_facts = measures.load_json(args.place_facts) if getattr(args, 'place_facts', None) else None
        self.view_name = getattr(args, 'view', None)
        self.view = None
        if self.place_facts:
            views = {v['name']: v for v in self.place_facts['views']}
            if self.view_name is None and len(views) == 1:
                self.view_name = next(iter(views))
            self.view = views.get(self.view_name)
        self.subject = self.shot.subject
        self.figures = measures.figure_groups(self.shot, self.place_facts)
        self.share = {g: float(m.mean()) for g, m in self.shot.visible.items()}

    # --- which groups, in which role
    def role(self, g):
        check = self.check
        if g == self.subject:
            return 'subject'
        if g == check.get('support'):
            return 'support'
        if g in self.figures:
            return 'figure'
        if g in check.get('story', []):
            return 'story'
        if g in check.get('work', []):
            return 'work'
        if g in check.get('pairs_also', []):
            return 'pairs_also'
        return 'other'

    def showing(self):
        least = self.settings.value('painting_tools.paint_request.keep_min_frame_share')
        return [g for g in self.shot.facts['groups'] if self.share[g] >= least]

    def distance(self, g):
        return float(self.shot.info(g).get('distance', 0.0))

    def across(self, g):
        box = measures.box_of(self.shot.visible[g])
        return (box[0] + box[2]) / 2 / self.width if box else 0.5

    def lum(self):
        return measures.luminance(self.plate)

    # --- thin parts: thin in the whole prop, counted where it shows
    def thin_shares(self):
        found = {}
        for g in self.shot.facts['groups']:
            seen, whole = self.shot.visible[g], self.shot.alone[g]
            if not seen.any() or g in self.figures:
                continue
            thin = seen & whole & ~check_shot.without_wires(whole, self.width)
            found[g] = float(thin.sum() / seen.sum())
        self.settings.value('painting.plate_thin_parts_pixels_at_1080')   # the opening the shot checker uses (named in the report)
        return found

    # --- edges that meet or nearly meet: signed distance (negative: overlap depth), as the shot checker measures rule 4
    def pair_distance(self, a, b):
        solid_a = check_shot.without_wires(self.shot.alone[a], self.width)
        solid_b = check_shot.without_wires(self.shot.alone[b], self.width)
        both = solid_a & solid_b
        if both.any():
            showing = both & (self.shot.visible[a] | self.shot.visible[b])
            if showing.any():
                return -float(max(check_shot.distance_inside(solid_a)[showing].max(), check_shot.distance_inside(solid_b)[showing].max()))
        seen_a, seen_b = self.shot.visible[a], self.shot.visible[b]
        if not (seen_a.any() and seen_b.any()):
            return None
        return float(np.where(seen_b, check_shot.distance_outside(seen_a), np.inf).min())

    def near_pairs(self):
        s = self.settings
        scale = self.width / 1536
        overlap = math.ceil(s.value('composing.clear_overlap_pixels_at_1536') * scale)
        gap = math.ceil(s.value('composing.clear_gap_pixels_at_1536') * scale)
        factor = s.value('painting_tools.paint_request.pair_band_factor')
        groups = [g for g in self.showing() if self.shot.alone[g].any()]
        rests = self.check.get('stands_on', {})
        found = []
        for i, a in enumerate(groups):
            for b in groups[i + 1:]:
                if {a, b} <= {self.subject, self.check.get('support')} or rests.get(a) == b or rests.get(b) == a:
                    continue   # one hangs or stands on the other: their shared edge is the point
                d = self.pair_distance(a, b)
                if d is None:
                    continue
                intended = d < 0 and self.subject in (a, b) and (self.role(a) in ('story', 'figure') or self.role(b) in ('story', 'figure'))
                if -factor * overlap < d < factor * gap or intended:
                    found.append({'a': a, 'b': b, 'signed_pixels': round(d, 1), 'intended_overlap': bool(intended and d <= -factor * overlap)})
        return found, {'overlap': overlap, 'gap': gap, 'band': [-factor * overlap, factor * gap]}

    # --- warm light and brightness
    def warm_mask(self):
        threshold = self.settings.value('composing.warm_pixel_threshold')
        warmth = np.clip((self.plate[..., 0] - self.plate[..., 2]) / 255, 0, 1)
        return warmth * (cv2.cvtColor(np.clip(self.plate, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY) / 255.0) > threshold

    def warm_owners(self):
        """Each warm pixel belongs to the nearest group within the checker's 'round the story' reach, or to the set."""
        warm = self.warm_mask()
        if not warm.any():
            return {}, 0.0, 0.0
        reach = self.settings.value('composing.warm_near_story_widen_share_of_width') * self.width
        groups = [g for g in self.showing()]
        far = np.full(warm.shape, np.inf, np.float32)
        owner = np.full(warm.shape, -1, np.int32)
        for i, g in enumerate(groups):
            d = check_shot.distance_outside(self.shot.visible[g])
            closer = d < far
            far[closer], owner[closer] = d[closer], i
        owner[far > reach] = -1
        total = warm.sum()
        shares = {g: float(((owner == i) & warm).sum() / total) for i, g in enumerate(groups)}
        return {g: v for g, v in shares.items() if v > 0}, float(((owner == -1) & warm).sum() / total), float(warm.mean())

    def mean_brightness(self, g):
        m = self.shot.visible[g]
        return float(self.lum()[m].mean()) if m.any() else None

    # --- the people
    def people(self):
        """Each figure that shows: near or far, which way it faces against the plate camera, its side, its head in film pixels."""
        s = self.settings
        near_limit = s.value('painting_tools.paint_request.near_figure_metres')
        head = s.value('people.head_height_metres')
        film_camera = plate_camera = None
        if self.place_facts and self.view:
            film_camera = geometry.camera_from_place_facts(self.place_facts, s, self.view_name, 'composed', 'film')
            plate_camera = geometry.camera_from_place_facts(self.place_facts, s, self.view_name, 'plate', 'plate')
        focal = geometry.focal_length_pixels(s.value('frame.film_vertical_fov_degrees'), s.value('frame.height_pixels'))
        found, hidden = [], []
        for g in self.figures:
            if self.shot.visible[g].sum() < 20:
                hidden.append(g)
                continue
            record = measures.figure_record(self.shot, g, self.place_facts)
            distance = self.distance(g)
            facing = 'unknown'
            if record and plate_camera:
                to_figure = [record['feet'][0] - plate_camera['position'][0], record['feet'][1] - plate_camera['position'][1]]
                length = math.hypot(*to_figure) or 1.0
                along = (record['facing'][0] * to_figure[0] + record['facing'][1] * to_figure[1]) / length
                facing = 'away' if along > 0.5 else 'toward' if along < -0.5 else 'side'
            if record and film_camera:
                top = [record['feet'][0], record['feet'][1], record['feet'][2] + record['height_metres'] - head / 2]
                depth = geometry.project_point(film_camera, top)['depth']
                head_pixels = geometry.size_in_pixels(film_camera, head, depth) if depth > 0 else None
            else:
                head_pixels = head * focal / distance if distance > 0 else None
            found.append({'group': g, 'distance_metres': round(distance, 2), 'near': distance < near_limit, 'facing': facing,
                          'side': 'left' if self.across(g) < 0.5 else 'right', 'head_film_pixels': round(head_pixels, 1) if head_pixels else None})
        return found, hidden

    # --- what the slide moves past (the behind painting's near list)
    def slide_parallax(self):
        """How far each showing group slides against what lies behind it over the view's slide (frame_geometry's parallax
        sums), with the set assumed behind_gap_metres behind it (Blender's rays would give the real depth)."""
        s = self.settings
        if not (self.view and self.view.get('slide')):
            return {}
        start, end = self.view['slide']['start'], self.view['slide']['end']
        camera = geometry.camera_from_place_facts(self.place_facts, s, self.view_name, 'plate', 'film')
        step = geometry.subtract(end, start)
        forward = geometry.dot(step, camera['forward'])
        sideways = math.hypot(geometry.dot(step, camera['right']), geometry.dot(step, camera['up']))
        gap = s.value('painting_tools.plan_states.behind_gap_metres')
        fov, rows = s.value('frame.film_vertical_fov_degrees'), s.value('frame.height_pixels')
        found = {}
        for g in self.showing():
            d = self.distance(g)
            if d <= forward + 0.1:
                continue
            box = measures.box_of(self.shot.visible[g])
            x, y = (box[0] + box[2]) / 2 / self.width, (box[1] + box[3]) / 2 / self.height
            plate_focal = geometry.focal_length_pixels(self.shot.camera['vertical_fov_degrees'], self.height)
            film_focal = geometry.focal_length_pixels(fov, rows)
            offset = math.hypot((x - 0.5) * self.width, (y - 0.5) * self.height) * film_focal / plate_focal * (rows / self.height)
            pixels = geometry.parallax_forward_pixels(offset, forward, d, d + gap) if forward > 0 else 0.0
            pixels += geometry.parallax_sideways_pixels(sideways, d, d + gap, fov, rows) if sideways > 0 else 0.0
            found[g] = round(pixels, 2)
        return found


# ------------------------------------------------------------------------------------------------ the preflight
def item(found, name, verdict, words, numbers=None, fix=''):
    found.append({'check': name, 'verdict': verdict, 'what': words, 'numbers': numbers or {}, 'fix': fix})


def hollow_glow(view, groups):
    """Light in the top of a hollow prop (lesson 138): the share of its top that is over N times the prop's own median."""
    s = view.settings.value('painting_tools.paint_request.hollow_glow')
    lum = view.lum()
    found = {}
    for g in groups:
        m = view.shot.visible[g]
        box = measures.box_of(m)
        if box is None:
            continue
        top = m & (np.arange(view.height)[:, None] < box[1] + s['top_share'] * (box[3] - box[1] + 1))
        body = m & ~top
        if top.sum() < 10 or body.sum() < 10:
            continue
        glow = top & (lum > s['brighter_than_body'] * np.median(lum[body]))
        found[g] = {'glow_share_of_top': float(glow.sum() / top.sum()), 'glow_pixels': int(glow.sum()),
                    'body_median': float(np.median(lum[body]))}
    return found


def discs_and_holes(view):
    """Even, strongly coloured bright patches round the story, and near-black holes anywhere (log 32: an even orange disc in
    the drum's mouth reads as soup or a lid; the pure-black doorway behind the colliery's gates made them read as open)."""
    s = view.settings.value('painting_tools.paint_request.even_disc')
    darkest = view.settings.value('painting_tools.paint_request.dark_hole_levels_max')
    hole_least = view.settings.value('painting_tools.paint_request.dark_hole_frame_share_min')
    lum = view.lum()
    window = max(3, int(round(s['window_pixels_at_1080'] * view.width / 1080)) | 1)
    mean = cv2.blur(lum, (window, window))
    spread = np.sqrt(np.maximum(cv2.blur(lum * lum, (window, window)) - mean * mean, 0))
    colours = measures.hsv(view.plate)
    even = (spread < s['spread_levels_max']) & (colours[..., 1] / 255 > s['saturation_min']) & (colours[..., 2] / 255 > s['value_min'])
    hole = lum < darkest
    for g in view.shot.facts['groups']:   # a dark prop or a dark coat is not an opening: only the set's own black holes count
        hole &= ~view.shot.visible[g]
    story = np.zeros_like(hole)
    for g in view.shot.core:
        story |= view.shot.visible[g]
    box = measures.box_of(story)
    inside = np.zeros_like(hole)
    if box:
        inside[box[1]:box[3] + 1, box[0]:box[2] + 1] = True
    found = []
    frame = view.width * view.height
    for kind, mask, least in (('even bright patch', even & inside, s['frame_share_min']), ('near-black hole', hole, hole_least)):
        mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, count):
            if stats[i, cv2.CC_STAT_AREA] >= least * frame:
                part = labels == i
                grown = cv2.dilate(part.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
                owners = {g: int((grown & view.shot.alone[g]).sum()) for g in view.shot.facts['groups']}
                owner = max(owners, key=owners.get) if owners and max(owners.values()) > 0 else 'the set'
                found.append({'kind': kind, 'share_of_frame': float(stats[i, cv2.CC_STAT_AREA] / frame), 'on': owner,
                              'at': [round(float(stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] / 2) / view.width, 3),
                                     round(float(stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] / 2) / view.height, 3)]})
    return found


def graded_colour(view, g, look):
    """The figure's cloth as the film shows it: the lit half of its coat band (the dark half has no colour to show), through
    the stage's finish. Round 2's tan coats: plate about 40/27/14, here 21/0/0 (filmed 26/1/0); round 3's grey coats: plate
    about 45/38/31, here 28/17/3 (filmed 27/16/3)."""
    band = view.settings.value('painting_tools.paint_request.coat_band_share_of_height')
    m = view.shot.visible[g]
    box = measures.box_of(m)
    rows = np.arange(view.height)[:, None]
    height = box[3] - box[1] + 1
    coat = m & (rows >= box[1] + band[0] * height) & (rows < box[1] + band[1] * height)
    coat = cv2.erode(coat.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    if coat.sum() < 20:
        coat = m
    lum = view.lum()
    lit = coat & (lum >= np.percentile(lum[coat], 50))
    plate_colour = view.plate[lit].mean(axis=0)
    film = measures.stage_finish(plate_colour[None, :], look)[0]
    hue, saturation = measures.hue_degrees_and_saturation(film)
    return plate_colour, film, hue, saturation


def suggest_plate_colour(plate_colour, look, band, saturation_min):
    """The nearest plate colour (lighter and greyer) that the finish no longer turns red."""
    grey = plate_colour.mean()
    for lighter in np.arange(1.0, 2.01, 0.05):
        for greyer in np.arange(0.0, 0.81, 0.1):
            colour = np.clip((grey + (plate_colour - grey) * (1 - greyer)) * lighter, 0, 255)
            hue, saturation = measures.hue_degrees_and_saturation(measures.stage_finish(colour[None, :], look)[0])
            if not (measures.in_hue_band(hue, band) and saturation > saturation_min):
                return [round(float(c)) for c in colour], round(hue, 1)
    return None, None


def preflight(view, args):
    s = view.settings
    found = []
    # 1. render faults
    faults = s.value('light.render_faults')
    if args.render_log:
        text = open(args.render_log, errors='replace').read()
        hits = [f for f in faults if f in text]
        saved = [os.path.basename(m) for m in re.findall(r'^\s*[\d:.]+\s+render\s+\|\s+Saved:\s+\'([^\']+)\'', text, re.M)]
        plate_name = os.path.basename(args.plate)
        if not saved:
            item(found, 'render log', 'fail', f'{os.path.basename(args.render_log)} is not a Blender render log (no "render | Saved:" line'
                 + ('; the file is empty' if not text.strip() else '') + '): it proves nothing about the plate.', {'saved': []},
                 'Give the log Blender wrote while drawing this plate (blender -b ... > plate.log 2>&1).')
        elif plate_name not in saved:
            item(found, 'render log', 'fail', f'The render log saves {join_words(saved)}, not {plate_name}: it is the log of another render.',
                 {'saved': saved}, 'Give the log of this plate\'s own render.')
        else:
            item(found, 'render log', 'fail' if hits else 'pass',
                 f'The render log names {join_words(hits)}: the plate has shadow faults.' if hits else f'The render log of {plate_name} has no render faults.',
                 {'faults_found': hits}, 'Render the plate again with fewer shadow-casting lights or a larger shadow pool (lesson 110).' if hits else '')
    else:
        item(found, 'render log', 'not checked', 'No render log given (--render-log).')
    # 2. the shot checker's light rules
    if args.shot_report:
        text = open(args.shot_report, errors='replace').read()
        known = os.path.join(os.path.dirname(os.path.abspath(args.shot_report)), 'known.json')
        by_checker = (text.startswith('# Shot check: ') and re.search(r'^Made by check_shot\.py version \S+', text, re.M)) or os.path.exists(known)
        problems = text.split('## Problems', 1)[1].split('\n## ', 1)[0] if '## Problems' in text else ''
        light = [line.strip() for line in problems.splitlines() if re.match(r'\s*\d+\. \*\*rule [56]', line)]
        if not by_checker:
            item(found, 'light rules', 'fail', f'{os.path.basename(args.shot_report)} is not the shot checker\'s report (no "# Shot check:" title and '
                 '"Made by check_shot.py version" line, and no known.json beside it): the light rules were not judged.', {'problems': []},
                 'Run the shot checker on the plate (paper-film/tools/check-shot.sh) and give its report.md.')
        else:
            item(found, 'light rules', 'fail' if light else 'pass',
                 (f'{len(light)} light problem(s) in the shot check: fix light in 3D before paying for paint (decision 37).') if light else
                 'The shot check lists no light problem (rules 5 and 6).', {'problems': light})
    else:
        item(found, 'light rules', 'not checked', 'No shot-check report given (--shot-report): run check_shot.py on the plate first.')
    # 3. thin parts
    named = s.value('painting_tools.paint_request.thin_share_named')
    remove = s.value('painting_tools.paint_request.thin_share_remove_or_thicken')
    thin = view.thin_shares()
    listed = {g: round(v, 3) for g, v in thin.items() if v >= named and g in view.showing()}
    story_thin = [g for g, v in listed.items() if v >= remove and view.role(g) in ('subject', 'support', 'story')]
    item(found, 'thin parts', 'look' if story_thin else 'pass',
         (f'Thin parts the painter will smear are on {join_words(story_thin)}: remove them, thicken them, or keep the prompt\'s '
          f'thin-parts sentence (log 31 removed the pail\'s wire handle).') if story_thin else
         f'No story prop has much thin detail; the prompt names {join_words(list(listed)) or "nothing"} as thin.',
         {'thin_share_by_group': listed})
    # 4. lettering in the plate
    lettered = [g for g in view.check.get('must_read', []) if g in view.shot.visible and view.shot.visible[g].any()]
    item(found, 'lettering', 'look' if lettered else 'pass',
         (f'{join_words(lettered)} carry words the painter will garble (logs 29-30): keep them on their own surfaces in the film; '
          f'the prompt asks for plain marks.') if lettered else 'No lettered group shows in the plate.', {'lettered': lettered})
    # 5. even bright discs and near-black holes round the story
    patches = discs_and_holes(view)
    item(found, 'even discs and dark holes', 'fail' if patches else 'pass',
         ('; '.join(f'a {p["kind"]} on {p["on"]} ({p["share_of_frame"]:.2%} of the frame, at {p["at"][0]:.2f} across, {p["at"][1]:.2f} down)'
                    for p in patches) + ': the painter reads an even disc as soup or a lid and a black hole as an opening (log 32).') if patches else
         'No even bright disc or near-black hole round the story.', {'patches': patches},
         'Let the glow fade up from below; put a dim surface behind a black opening.' if patches else '')
    # 6. a glow inside a hollow
    hollow = [g for g in list(view.check.get('hollow', [])) + list(getattr(args, 'hollow', None) or []) if g in view.shot.visible]
    if hollow:
        limit = s.value('painting_tools.paint_request.hollow_glow')['share_max']
        glows = hollow_glow(view, hollow)
        bad = {g: v for g, v in glows.items() if v['glow_share_of_top'] > limit}
        item(found, 'glow inside a hollow', 'fail' if bad else 'pass',
             (f'{join_words(list(bad))}: ' + ', '.join(f'{v["glow_share_of_top"]:.1%}' for v in bad.values()) +
              f' of the top is lit (limit {limit:.0%}): the painter lifts a glowing hollow into a bright band (lesson 138). Darken the glow '
              f'inside it in the plate first.') if bad else
             f'The hollow props\' tops ({join_words(hollow)}) are dark enough.', {g: measures.round_all(v) for g, v in glows.items()},
             'Lower the coals\' glow or hide it behind the front rim, then draw the plate again.' if bad else '')
    else:
        item(found, 'glow inside a hollow', 'not checked', 'The check file names no "hollow" props.')
    # 7-10. figures
    if view.figures:
        figure_checks(view, args, found)
    # 11. real names
    names = load_real_names(args)
    if names:
        texts = ' '.join(list(view.shot.facts['groups']) + [json.dumps(view.brief), json.dumps(view.check.get('paint_as', {}))]).lower()
        hits = [n for n in names if n.lower() in texts]
        item(found, 'real people', 'fail' if hits else 'pass',
             f'The request names real people ({join_words(hits)}): only typed name cards show real people (decision 2026-10-11).' if hits else
             f'No name from the list of {len(names)} real people appears in the request.', {'found': hits})
    else:
        item(found, 'real people', 'not checked', 'No list of real people given (--real-names).')
    return found


def load_real_names(args):
    if not getattr(args, 'real_names', None):
        return []
    data = measures.load_json(args.real_names) if args.real_names.endswith('.json') else [l.strip() for l in open(args.real_names) if l.strip()]
    if isinstance(data, dict):
        data = data.get('names') or data.get('real_people') or []
    return [n for n in data if isinstance(n, str) and n.strip()]


def figure_checks(view, args, found):
    s = view.settings
    lum = view.lum()
    people, hidden = view.people()
    by_group = {p['group']: p for p in people}
    # head paler than coat, for figures with their backs to us
    limit = s.value('painting_tools.paint_request.head_band_over_coat_max')
    heads = {}
    for g, p in by_group.items():
        if p['facing'] in ('away', 'unknown') and p['near']:
            band, coat = measures.head_and_coat(lum, view.shot.visible[g], s)
            if band is not None:
                heads[g] = {'head_band': round(band, 1), 'coat': round(coat, 1), 'ratio': round(band / max(coat, 1e-6), 2)}
    pale_min = s.value('painting_tools.paint_request.head_band_pale_min_levels')
    pale = [g for g, v in heads.items() if v['ratio'] >= limit and v['head_band'] >= pale_min]
    item(found, 'heads from behind', 'fail' if pale else 'pass',
         (f'{join_words(pale)}: the back of the head is pale (over {pale_min} levels) and as bright as the coat or brighter; the painter '
          f'paints a face or a bald dummy (round 1: head 80/54/35 over coat 39/25/14). Use matt dark hair from cap to collar, collars up, '
          f'caps low.') if pale else
         f'No near figure seen from behind has a pale head brighter than its coat ({len(heads)} checked).', heads)
    # cloth through the film's finish
    look = dict(s.value('painting_tools.paint_request.film_look'))
    if getattr(args, 'exposure', None):
        look['exposure'] = args.exposure
    band = s.value('painting_tools.paint_request.red_hue_band_degrees')
    saturation_min = s.value('painting_tools.paint_request.red_saturation_min')
    graded, red = {}, []
    for g in by_group:
        plate_colour, film, hue, saturation = graded_colour(view, g, look)
        graded[g] = {'plate': [round(float(c)) for c in plate_colour], 'film': [round(float(c)) for c in film], 'hue_degrees': round(hue, 1),
                     'saturation': round(saturation, 2)}
        if measures.in_hue_band(hue, band) and saturation > saturation_min:
            suggestion, new_hue = suggest_plate_colour(plate_colour, look, band, saturation_min)
            graded[g]['suggested_plate'] = suggestion
            graded[g]['suggested_hue'] = new_hue
            red.append(g)
    item(found, 'cloth through the film\'s finish', 'fail' if red else 'pass',
         (f'{join_words(red)} come out red in the film (the finish turns dark warm cloth red, round 2): '
          + '; '.join(f'{g} {graded[g]["plate"]} becomes {graded[g]["film"]}, hue {graded[g]["hue_degrees"]:.0f} degrees' for g in red) + '.') if red else
         f'No figure\'s cloth turns red through the film\'s finish (exposure {look["exposure"]}).', graded,
         ('Use greyer, lighter cloth: ' + '; '.join(f'{g} about {graded[g].get("suggested_plate")}' for g in red) + '.') if red else '')
    # figure against its surround in the plate
    all_figures = np.zeros((view.height, view.width), bool)
    for g in view.figures:
        all_figures |= view.shot.visible[g]
    ratio_max = s.value('painting_tools.paint_request.figure_surround_ratio_max_plate')
    ratios = {g: measures.figure_surround_ratio(lum, view.shot.visible[g], all_figures, s) for g in by_group}
    ratios = {g: round(v, 3) for g, v in ratios.items() if v is not None}
    weak = [g for g, v in ratios.items() if v > ratio_max]
    item(found, 'figures against their surround', 'look' if weak else 'pass',
         (f'{join_words(weak)} are barely darker than what surrounds them in the plate (over {ratio_max} of its brightness); the painter '
          f'lifts figures about three times toward their surround (people test 0.15 to 0.50), so these will read pale.') if weak else
         f'Every figure is clearly darker than its surround in the plate (all under {ratio_max}).', ratios,
         'Darken their cloth or stand them against a lighter background.' if weak else '')
    # long shadows (needs the plate drawn without the figures)
    if getattr(args, 'helper_plate', None):
        work = os.path.join(args.work_folder, 'paint-request-trial') if args.work_folder else tempfile.mkdtemp(prefix='paint-request-trial-')
        try:
            shares = measures.state_mask_shares(args.plate, args.helper_plate, args.plate, args.helper_plate, work, args.facts, view.figures)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        limit = s.value('painting_tools.plan_states.come_and_go_mask_over_outline_max')
        ratio = shares['mask_share'] / max(shares['outline_share'], 1e-6)
        long_shadows = ratio > limit
        verdict = 'look' if (long_shadows and args.allow_long_shadows) else 'fail' if long_shadows else 'pass'
        item(found, 'figures casting long shadows', verdict,
             (f'Removing the figures changes {shares["mask_share"]:.1%} of the frame against {shares["outline_share"]:.1%} for the figures '
              f'themselves ({ratio:.1f} times; limit {limit:g}): they cast long shadows or block light. Asked to remove them, the painter '
              f'leaves the shadows (lesson 135).') if long_shadows else
             f'Removing the figures changes {shares["mask_share"]:.1%} of the frame, {ratio:.1f} times their own outlines: no long shadows.',
             {'mask_share': shares['mask_share'], 'outline_share': shares['outline_share'], 'ratio': round(ratio, 2)},
             'Draw the plates with the figures casting no long shadows (a small soft patch at their feet), as the Works do.' if long_shadows else '')
    else:
        item(found, 'figures casting long shadows', 'not checked', 'No helper plate (the plate drawn without the figures) given (--helper-plate).')
    if hidden:
        item(found, 'hidden figures', 'look', f'{join_words(hidden)} do not show in the plate at all; the prompt does not count them.', {'hidden': hidden})


# ------------------------------------------------------------------------------------------------ the prompts
def paint_as(view, g):
    words = view.check.get('paint_as', {})
    if g in words:
        return words[g]
    return f'the {g}'


def keep_list(view, sentences, warm_only=False):
    """The Keep list: story things first (the drum, the chair...), then the subject and its support, the things the checker
    pairs, then the far work props grouped by side, then the brief's set words."""
    s = view.settings
    far = s.value('painting_tools.paint_request.far_metres')
    darker = s.value('painting_tools.paint_request.darker_than_subject_share')
    lum = view.lum()
    subject_light = float(np.median(lum[view.shot.visible[view.subject]])) if view.shot.visible[view.subject].any() else 0.0
    bright_part = lambda g: float(np.percentile(lum[view.shot.visible[g]], 95)) if view.shot.visible[g].any() else 0.0
    order = {'story': 0, 'subject': 1, 'support': 1, 'pairs_also': 2, 'other': 3, 'work': 4}
    groups = [g for g in view.showing() if view.role(g) != 'figure']
    groups.sort(key=lambda g: (order.get(view.role(g), 3), -view.share[g]))
    items, far_items, chosen = [], {'left': [], 'right': []}, []
    lights = set(view.check.get('lights_in_story', []))
    for g in groups:
        words = paint_as(view, g)
        if not words:
            chosen.append(g)
            continue   # covered by another group's words (the notice in the board's)
        if view.role(g) == 'story' and g not in lights and subject_light and bright_part(g) >= darker * subject_light \
                and 'darker than' not in words:
            words += f', darker than the {view.subject}'
        if view.role(g) == 'work' and view.distance(g) > far:
            far_items['left' if view.across(g) < 0.5 else 'right'].append(words)
        else:
            items.append(words)
        chosen.append(g)
    items += view.brief.get('set_keep', [])
    for side in ('left', 'right'):
        if far_items[side]:
            items.append(sentences['far_group'].format(side=side, items=join_words(far_items[side])))
    return items, chosen


def people_part(view, sentences):
    people, hidden = view.people()
    if not people:
        return '', {}
    s = view.settings
    brief = view.brief.get('people', {})
    near = [p for p in people if p['near']]
    far = [p for p in people if not p['near']]
    lines = [sentences['people_intro'].format(dress=brief.get('dress', 'dark figures in dull browns, greys and near-black'))]
    if near:
        away = [p for p in near if p['facing'] in ('away', 'unknown')]
        toward = [p for p in near if p['facing'] == 'toward']
        side = [p for p in near if p['facing'] == 'side']
        bits = []
        if away:
            text = sentences['behind_words'].format(count=number_words(len(away)))
            if brief.get('behind_note'):
                text += f' ({brief["behind_note"]})'
            bits.append(text)
        if side:
            bits.append(sentences['side_words'].format(count=number_words(len(side))))
        for side_name in ('left', 'right'):
            facing = [p for p in toward if p['side'] == side_name]
            if facing:
                bits.append(sentences['facing_words'].format(count=number_words(len(facing)), side=side_name))
        lines.append(sentences['people_near'].format(subject=brief.get('near_what', view.subject), count=number_words(len(near)),
                                                     noun=brief.get('near_noun', 'figures'), breakdown=join_words(bits)))
    if far:
        lines.append(sentences['people_far'].format(count=number_words(len(far)), doing=brief.get('far_doing', 'walking away')))
    faces_limit = s.value('people.facing_head_max_pixels')
    biggest = max((p['head_film_pixels'] or 0) for p in people)
    if biggest > faces_limit:
        lines.append(sentences['no_faces'])
    lines.append(sentences['keep_dark'])
    lines.append(sentences['count_kept'])
    return ' '.join(lines), {'figures': people, 'hidden': hidden, 'near': len(near), 'far': len(far), 'largest_head_film_pixels': biggest,
                             'no_faces_sentence': biggest > faces_limit}


def emitter_groups(view):
    """The showing groups that hold one of the place's lights (place facts emitters: a fire, a lamp), by kind."""
    found = {}
    for e in (view.place_facts or {}).get('emitters', []):
        if e.get('kind') not in ('fire', 'lamp'):
            continue
        holders = []
        for g in view.showing():
            info = view.shot.info(g)
            if not all(k in info for k in ('centre', 'width', 'depth', 'bottom', 'top')):
                continue
            x, y, z = e['at']
            if abs(x - info['centre'][0]) <= info['width'] / 2 + 0.5 and abs(y - info['centre'][1]) <= info['depth'] / 2 + 0.5 \
                    and info['bottom'] - 0.5 <= z <= info['top'] + 0.5:
                holders.append((math.dist(e['at'], info['centre']), g))
        if holders:
            found.setdefault(min(holders)[1], e['kind'])
    return found


def warm_part(view, sentences):
    """Where warm light stays: round every group that holds a fire, every group owning a share of the plate's warm pixels,
    at the lamps, and on the set (lit windows) when the set holds a share too."""
    least = view.settings.value('painting_tools.paint_request.warm_owner_share_min')
    owners, set_share, warm_share = view.warm_owners()
    words = view.brief.get('warm_words', {})
    lights = emitter_groups(view)
    fires = [g for g, kind in lights.items() if kind == 'fire']
    lamps = [g for g, kind in lights.items() if kind == 'lamp']
    owning = [g for g, v in sorted(owners.items(), key=lambda kv: -kv[1]) if v >= least and g not in fires]
    chosen = fires + [g for g in owning if g not in lamps] + [g for g in lamps + owning if g in lamps]
    places = [words.get(g, f'round the {g}') for g in dict.fromkeys(chosen)]
    if set_share >= least and words.get('set'):
        places += words['set'] if isinstance(words['set'], list) else [words['set']]
    places = list(dict.fromkeys(places))
    text = sentences['warm'].format(places=join_words(places)) if places else ''
    return text, {'owners': {g: round(v, 3) for g, v in owners.items()}, 'set_share': round(set_share, 3), 'warm_share_of_frame': round(warm_share, 4),
                  'fires': fires, 'lamps': lamps, 'named': list(dict.fromkeys(chosen)) + (['set'] if set_share >= least and words.get('set') else [])}


def brightest_part(view, sentences):
    """"Nothing is brighter than the subject" when the subject is meant to be brightest (not a dark subject) and is, in the plate."""
    kinds = (view.view or {}).get('kind_of_shot') or view.check.get('kind_of_shot') or ['still_life']
    before = dict(view.settings.used)
    rule = resolve_profile(view.settings, kinds).get('rule5_subject_brightness_ratio', {})
    view.settings.used = before
    for kind in rule.get('from_kinds', []):
        view.settings.entry(f'shot_kind_profiles.{kind}.rules.rule5_subject_brightness_ratio')
    if not rule.get('applies', True) or not isinstance(rule.get('value'), (int, float)):
        return '', {'reason': 'a dark subject: the subject is not meant to be the brightest'}
    ratio = (view.mean_brightness(view.subject) or 0) / max(1e-6, float(view.lum().mean()))
    return (sentences['brightest'].format(subject=view.subject) if ratio >= rule['value'] else ''), {'subject_over_frame': round(ratio, 2), 'needs': rule['value']}


def thin_part(view, sentences):
    named = view.settings.value('painting_tools.paint_request.thin_share_named')
    thin = view.thin_shares()
    words = view.brief.get('thin_words', {})
    groups = [g for g in view.showing() if thin.get(g, 0) >= named]
    items = list(dict.fromkeys(words.get(g, f'the {g}\'s thin parts') for g in groups))
    items += view.brief.get('thin_also', [])
    return (sentences['thin'].format(items=join_words(items)) if items else ''), {'groups': groups, 'shares': {g: round(thin[g], 3) for g in groups}}


def edges_part(view, sentences):
    pairs, limits = view.near_pairs()
    words = view.brief.get('pair_words', {})
    people_words = view.brief.get('people', {})
    near_noun = people_words.get('near_noun', 'figures')
    people, _ = view.people()
    near_set = {p['group'] for p in people if p['near']}
    far_set = {p['group'] for p in people if not p['near']}
    items = []
    for p in pairs:
        a, b = p['a'], p['b']
        key = '|'.join(sorted((a, b)))
        if key in words:
            items.append(words[key])
            continue
        kinds = ['near' if g in near_set else 'far' if g in far_set else 'thing' for g in (a, b)]
        if kinds == ['near', 'near']:
            items.append(f'each of the {near_noun} and the next')
        elif 'near' in kinds:
            other = b if kinds[0] == 'near' else a
            items.append(f'each of the {near_noun} and the {other}' if other == view.subject else f'the {near_noun} and the {other}')
        elif kinds == ['far', 'far']:
            items.append('the far figures and each other')
        elif 'far' in kinds:
            other = b if kinds[0] == 'far' else a
            items.append(f'the far figures and the {other}')
        else:
            items.append(f'the {a} and the {b}')
    items = list(dict.fromkeys(items)) + view.brief.get('extra_pairs', [])
    return (sentences['edges'].format(pairs=join_words(items)) if items else ''), {'pairs': pairs, 'band_pixels': limits['band']}


def wetness_words(sentences, keep_wetness):
    """The "never add" words about puddles, and the Keep item for wet ground. By default a place has no puddles to paint, so none may be added (the
    notice corner's and the people test's words, word for word). A place built wet (--keep-wetness, or "keep_wetness": true in the brief) has wet
    ground the painter must KEEP, so only NEW puddles and reflections are forbidden. Returns (the never-add sentence, the Keep item or an empty text)."""
    if keep_wetness:
        return sentences['never_rest_wet'], sentences['keep_wet']
    return sentences['never_rest'], ''


def never_part(view, sentences, has_people):
    brief = view.brief
    notes = brief.get('never_add_notes', {})
    absent = [p for p in brief.get('library_props', []) if p not in view.shot.facts['groups'] or not view.shot.visible[p].any()]
    props_note = notes.get('props') or (f' (no {join_words(absent, "or")} in the road or on the pavement)' if absent else '')
    items = [sentences['never_flames'].format(note=notes.get('flames', '')),
             sentences['never_glows'].format(note=notes.get('glows', ''))]
    items += brief.get('removed_parts', [])
    items.append(sentences['never_animals'] if has_people else sentences['never_people'])
    items.append(sentences['never_props'].format(note=props_note))
    items.append(wetness_words(sentences, view.keep_wetness)[0])
    items += brief.get('never_add_also', [])
    return sentences['never_add'].format(items='; '.join(items)), {'absent_library_props': absent, 'removed_parts': brief.get('removed_parts', [])}


def lettering_items(view, sentences, kept_words):
    """Every lettered group that shows gets "with plain marks, no readable letters", unless the kept words already say so."""
    found = []
    for g in view.check.get('must_read', []):
        if g not in view.shot.visible or not view.shot.visible[g].any():
            continue
        if any('no readable letters' in w for w in kept_words):
            continue
        found.append(sentences['lettering'].format(item=paint_as(view, g) or f'the {g}'))
    return found


def main_prompt(view):
    lines, sentences = load_template('paint-prompt.txt')
    people_text, people_numbers = people_part(view, sentences)
    keep_items, kept = keep_list(view, sentences)
    keep_items += lettering_items(view, sentences, keep_items)
    wet_item = wetness_words(sentences, view.keep_wetness)[1]
    if wet_item:
        keep_items.append(wet_item)
    warm_text, warm_numbers = warm_part(view, sentences)
    bright_text, bright_numbers = brightest_part(view, sentences)
    thin_text, thin_numbers = thin_part(view, sentences)
    edge_text, edge_numbers = edges_part(view, sentences)
    never_text, never_numbers = never_part(view, sentences, bool(people_numbers.get('figures')))
    brief = view.brief
    slots = {'place_sentence': brief.get('place_sentence', ''), 'people': people_text,
             'keep': sentences['keep'].format(items='; '.join(keep_items)) if keep_items else '',
             'notes': ' '.join(brief.get('notes', [])), 'lamps': brief.get('lamps_sentence', '') if lamps_show(view) else '',
             'colour': brief.get('colour_sentence', ''), 'warm': warm_text, 'brightest': bright_text, 'thin': thin_text,
             'edges': edge_text, 'never_add': never_text}
    parts = fill_lines(lines, slots)
    return ' '.join(t for _, t in parts), {'parts': [n for n, _ in parts], 'kept_groups': kept, 'people': people_numbers, 'warm': warm_numbers,
                                          'brightest': bright_numbers, 'thin': thin_numbers, 'edges': edge_numbers, 'never_add': never_numbers}


def lamps_show(view):
    """A lamp sentence only when a lamp of the place lands inside the plate."""
    if not view.place_facts or not view.view:
        return bool(view.brief.get('lamps_sentence'))
    camera = geometry.camera_from_place_facts(view.place_facts, view.settings, view.view_name, 'plate', 'plate')
    for e in view.place_facts.get('emitters', []):
        if e.get('kind') == 'lamp':
            landed = geometry.project_point(camera, e['at'])
            if landed['in_front'] and 0 <= landed['across'] <= 1 and 0 <= landed['down'] <= 1:
                return True
    return False


def behind_list(view, args):
    """What the behind painting removes: things the slide moves past (parallax over the limit), or the people who leave at a
    cut (--behind-remove figures), or named groups."""
    s = view.settings
    remove = list(getattr(args, 'behind_remove', None) or view.brief.get('behind', {}).get('remove') or [])
    parallax = view.slide_parallax()
    limit = s.value('painting_tools.plan_states.near_parallax_pixels')
    chosen = []
    if 'figures' in remove:
        chosen += [g for g in view.figures if view.shot.visible[g].any()]
        remove = [r for r in remove if r != 'figures']
    chosen += [g for g in remove if g in view.shot.visible]
    if not remove and not chosen:
        chosen = [g for g, px in parallax.items() if px > limit]
    return list(dict.fromkeys(chosen)), parallax


def behind_prompt(view, near):
    lines, sentences = load_template('behind-prompt.txt')
    brief = view.brief.get('behind', {})
    people_words = view.brief.get('people', {})
    figures = [g for g in near if g in view.figures]
    things = [g for g in near if g not in view.figures]
    items = []
    behind_as = view.check.get('behind_as', {})
    for g in things:
        words = behind_as.get(g, paint_as(view, g))
        if words:
            items.append(words)
    if figures:
        people, _ = view.people()
        chosen = [p for p in people if p['group'] in figures]
        near_people = [p for p in chosen if p['near']]
        far_people = [p for p in chosen if not p['near']]
        if near_people:
            items.append(f'the {number_words(len(near_people))} {people_words.get("near_noun", "figures")} {people_words.get("near_where", "")}'.strip()
                         + (f' ({people_words["remove_note"]})' if people_words.get('remove_note') else ''))
        if far_people:
            items.append(f'the {number_words(len(far_people))} small dark figures {people_words.get("far_doing", "walking away")}')
    keep = [paint_as(view, g) for g in view.showing() if g not in near and view.role(g) != 'figure' and paint_as(view, g)]
    keep = brief.get('keep_words') or keep
    only_people = bool(figures) and not things
    slots = {'what': sentences['what_people'] if only_people else sentences['what_things'], 'items': join_words(items),
             'shadows': sentences['shadows_people'] if figures else '', 'one': 'person' if only_people else 'one',
             'it': 'them' if only_people else 'it', 'behind': brief.get('behind_words', 'what lies behind them'),
             'warm': (', and ' + brief['warm_words']) if brief.get('warm_words') else '',
             'keep': keep if isinstance(keep, str) else join_words(keep)}
    parts = fill_lines(lines, slots)
    return ' '.join(t for _, t in parts), {'parts': [n for n, _ in parts], 'removed_groups': near}


# ------------------------------------------------------------------------------------------------ the price
def parse_size(text):
    w, h = re.split(r'[x,]', str(text).lower())
    return int(w), int(h)


def megapixels(size, settings):
    return size[0] * size[1] / settings.value('painting_tools.paint_request.megapixel_pixels')


def price(settings, returned, sent, rate=None):
    """rate x (megapixels returned + megapixels of every picture sent), in US cents (an estimate)."""
    entry = settings.entry('money.fal_flux_3_edit_cents_per_megapixel')
    rate = entry['value'] if rate is None else rate
    out = megapixels(returned, settings)
    ins = [megapixels(s, settings) for s in sent]
    return {'rate_cents_per_megapixel': rate, 'rate_read_on': entry.get('date_read'), 'returned_megapixels': round(out, 4),
            'sent_megapixels': [round(m, 4) for m in ins], 'cents': round(rate * (out + sum(ins)), 2),
            'note': 'an estimate: fal shows no exact charge; fit the rate to real charges with fit-price before trusting it'}


def default_sizes(settings):
    plate = (settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels'))
    returned = tuple(settings.value('frame.painting_returned_size_pixels'))
    style = tuple(settings.value('painting.style_picture_size_pixels'))
    return plate, returned, style


# ------------------------------------------------------------------------------------------------ commands
def command_preflight(args, settings):
    view = View(args, settings)
    found = preflight(view, args)
    failed = [f for f in found if f['verdict'] == 'fail']
    lines = [f'Plate preflight: {os.path.basename(args.plate)} ({len(failed)} failure(s); a failure stops the paid request)', '']
    for f in found:
        lines.append(f'- {f["verdict"].upper():12s} {f["check"]}: {f["what"]}')
        if f['fix']:
            lines.append(f'               fix: {f["fix"]}')
    return {'preflight': measures.round_all(found), 'failed': len(failed)}, lines, 1 if failed else 0


def command_prompt(args, settings):
    view = View(args, settings)
    text, numbers = main_prompt(view)
    near, parallax = behind_list(view, args)
    behind_text, behind_numbers = behind_prompt(view, near) if near else ('', {'removed_groups': []})
    lines = ['Main prompt:', '', text, '', 'Behind prompt' + (f' (removes {join_words(near)}):' if near else ': none (nothing near, nobody leaves)'), '']
    lines += [behind_text, ''] if behind_text else []
    lines += [f'Measured from the plate: kept {join_words(numbers["kept_groups"])}; thin {join_words(numbers["thin"]["groups"]) or "nothing"}; '
              f'{len(numbers["edges"]["pairs"])} near pair(s); warm light named at {join_words(numbers["warm"]["named"]) or "nowhere"}.']
    if numbers['people']:
        p = numbers['people']
        lines.append(f'People: {p["near"]} near, {p["far"]} far; largest head {p["largest_head_film_pixels"]:.0f} px on the film frame'
                     + (f'; hidden (not counted): {join_words(p["hidden"])}' if p['hidden'] else '') + '.')
    if parallax:
        lines.append('Slide parallax (px against a surface 1 m behind): ' + ', '.join(f'{g} {v:.1f}' for g, v in sorted(parallax.items(), key=lambda kv: -kv[1])))
    return {'main_prompt': text, 'main': measures.round_all(numbers), 'behind_prompt': behind_text, 'behind': measures.round_all(behind_numbers),
            'near_list': near, 'slide_parallax_pixels': parallax}, lines, 0


def command_price(args, settings):
    plate, returned, style = default_sizes(settings)
    returned = parse_size(args.returned) if args.returned else returned
    sent = [parse_size(s) for s in args.send] if args.send else [plate, style]
    main = price(settings, returned, sent, args.rate_cents)
    result = {'main_painting': main}
    total = main['cents']
    lines = [f'Main painting: {main["rate_cents_per_megapixel"]} c/MP (read {main["rate_read_on"]}) x ({main["returned_megapixels"]:.2f} MP returned + '
             f'{" + ".join(f"{m:.2f}" for m in main["sent_megapixels"])} MP sent) = {main["cents"]:.1f} US cents']
    if args.behind:
        behind = price(settings, returned, [plate], args.rate_cents)
        result['behind_painting'] = behind
        total += behind['cents']
        lines.append(f'Behind painting: x ({behind["returned_megapixels"]:.2f} + {behind["sent_megapixels"][0]:.2f} MP) = {behind["cents"]:.1f} US cents')
    result['total_cents'] = round(total, 2)
    lines += [f'Total: {total:.1f} US cents. {main["note"]}.']
    if args.spent_dollars is not None:
        allowance = settings.value('money.user_allowance_dollars')
        left = allowance['spending_line'] - args.spent_dollars
        result['left_before_spending_line_dollars'] = round(left, 2)
        result['within_allowance'] = total / 100 <= left
        lines.append(f'Left before the spending line (US${allowance["spending_line"]}): US${left:.2f}: ' + ('within it.' if total / 100 <= left else 'THIS WOULD PASS IT.'))
    return result, lines, 0 if result.get('within_allowance', True) else 1


def command_request(args, settings):
    pre, pre_lines, pre_failed = command_preflight(args, settings)
    prompts, prompt_lines, _ = command_prompt(args, settings)
    args.behind = bool(prompts['behind_prompt'])
    args.returned = args.returned
    if not args.send:
        args.send = None
    cost, cost_lines, over = command_price(args, settings)
    plate, returned, style = default_sizes(settings)
    refused = []
    if pre_failed and not args.ignore_preflight:
        refused.append('the plate preflight failed')
    unchecked = [f['check'] for f in pre['preflight'] if f['check'] in ('render log', 'light rules') and f['verdict'] == 'not checked']
    if unchecked and not args.ignore_preflight:
        refused.append(f'the {" and the ".join(unchecked)} were not checked (give --render-log and --shot-report: a paid repaint needs a clean '
                       f'render and passed light rules, decision 37)')
    if over:
        refused.append('the price would pass the spending line')
    request = {'model': settings.value('painting.painter_model'), 'settings': settings.value('painting.painter_settings'),
               'images': [{'role': 'image 1, the plate', 'file': args.plate, 'size': list(plate)},
                          {'role': 'image 2, the style picture (the place\'s master painting)', 'file': args.style or 'the place\'s master painting',
                           'send_size': list(style)}],
               'prompt': prompts['main_prompt'], 'expected_return_size': list(returned),
               'behind': {'prompt': prompts['behind_prompt'], 'images': [{'role': 'image 1, the main painting once lined up', 'size': list(plate)}],
                          'removes': prompts['near_list']} if prompts['behind_prompt'] else None,
               'estimated_cents': cost['total_cents'], 'price_note': cost['main_painting']['note'],
               'needs_the_users_yes': True, 'refused': refused}
    if args.out_folder:
        os.makedirs(args.out_folder, exist_ok=True)
        with open(os.path.join(args.out_folder, 'paint-request.json'), 'w') as handle:
            json.dump(request, handle, indent=1)
        with open(os.path.join(args.out_folder, 'paint-prompt.txt'), 'w') as handle:
            handle.write(prompts['main_prompt'] + '\n')
        if prompts['behind_prompt']:
            with open(os.path.join(args.out_folder, 'behind-prompt.txt'), 'w') as handle:
                handle.write(prompts['behind_prompt'] + '\n')
        with open(os.path.join(args.out_folder, 'near-list.json'), 'w') as handle:
            json.dump({'near': prompts['near_list'], 'slide_parallax_pixels': prompts['slide_parallax_pixels']}, handle, indent=1)
    if args.ledger and not refused:
        ledger = measures.load_json(args.ledger) if os.path.exists(args.ledger) else {'note': 'paintings asked for and made', 'paintings': []}
        ledger.setdefault('planned', []).append({'prompt': request['prompt'], 'images_sent': request['images'], 'settings': request['settings'],
                                                 'estimated_cents': request['estimated_cents'], 'status': 'planned: not sent, needs the user\'s yes'})
        with open(args.ledger, 'w') as handle:
            json.dump(ledger, handle, indent=1)
    lines = pre_lines + [''] + prompt_lines + [''] + cost_lines + ['']
    lines.append(('REFUSED: ' + '; '.join(refused) + '.') if refused else
                 'Ready to ask the user: nothing has been sent or paid.' + (f' Request written to {args.out_folder}.' if args.out_folder else ''))
    return {'request': request, 'preflight': pre, 'prompts': prompts, 'price': cost}, lines, 1 if refused else 0


def command_fit_price(args, settings):
    """Fits cents = rate x (output MP + input MP) to real charges (least squares through zero)."""
    charges = measures.load_json(args.charges)
    xs, ys = [], []
    for c in charges:
        mp = megapixels(parse_size(c['output']), settings) + sum(megapixels(parse_size(i), settings) for i in c['inputs'])
        xs.append(mp)
        ys.append(float(c['cents']))
    xs, ys = np.array(xs), np.array(ys)
    rate = float((xs * ys).sum() / (xs * xs).sum())
    output_only = float((ys * np.array([megapixels(parse_size(c['output']), settings) for c in charges])).sum() /
                        (np.array([megapixels(parse_size(c['output']), settings) for c in charges]) ** 2).sum())
    worst = float(np.abs(rate * xs - ys).max())
    table = settings.value('money.fal_flux_3_edit_cents_per_megapixel')
    lines = [f'{len(charges)} real charge(s): best rate {rate:.3f} c/MP counting output + inputs (worst miss {worst:.2f} c); '
             f'{output_only:.3f} c/MP if only the output were charged. The table says {table} c/MP.',
             'If the fit is close, update money.fal_flux_3_edit_cents_per_megapixel (kind: measured) with today\'s date.']
    return {'fitted_rate_cents_per_megapixel': round(rate, 4), 'output_only_rate': round(output_only, 4), 'worst_miss_cents': round(worst, 3),
            'table_rate': table}, lines, 0


def view_options(parser, need_brief=False):
    parser.add_argument('--check', required=True, help='the view\'s shot-check file (with "paint_as" words)')
    parser.add_argument('--facts', required=True, help='shot_facts.py\'s folder for the PLATE\'s camera and lens')
    parser.add_argument('--plate', required=True, help='the plate picture')
    parser.add_argument('--keep-wetness', action='store_true', help='the place is built wet: the prompt keeps its wet ground, puddles and reflections and forbids only NEW ones (or "keep_wetness": true in the brief)')
    parser.add_argument('--brief', required=need_brief, help='the place\'s painting brief (a person\'s words; see tests/fixtures/painting)')
    parser.add_argument('--place-facts', help='the place facts file (figures, the slide, the film camera)')
    parser.add_argument('--view', help='the view in the place facts')
    parser.add_argument('--helper-plate', help='the plate drawn without the figures (for the long-shadow check)')
    parser.add_argument('--allow-long-shadows', action='store_true', help='make the long-shadow check a warning instead of a failure')
    parser.add_argument('--work-folder', help='where the long-shadow trial writes (and deletes) its pictures')
    parser.add_argument('--render-log', help='the plate\'s render log')
    parser.add_argument('--shot-report', help='check_shot.py\'s report.md for this view')
    parser.add_argument('--real-names', help='a list of real people\'s names (JSON list or one per line)')
    parser.add_argument('--exposure', type=float, help='the page\'s exposure for the film\'s finish (page 3\'s W1: 1.6)')
    parser.add_argument('--hollow', nargs='*', help='props with an open top (a drum, a brazier), as well as the check file\'s "hollow" list')
    parser.add_argument('--behind-remove', nargs='*', help='what the behind painting removes: "figures" and/or group names '
                                                           '(default: what the slide moves past by more than the parallax limit)')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Gets a plate ready to paint and writes the painter\'s request (see the note at the top).')
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('preflight', help='check the plate before paying')
    view_options(p)
    add_output_options(p)
    p = commands.add_parser('prompt', help='write the main and behind prompts')
    view_options(p, need_brief=True)
    add_output_options(p)
    p = commands.add_parser('price', help='the estimated price')
    p.add_argument('--returned', help='the size the painter returns, WxH (default film-settings.json frame.painting_returned_size_pixels)')
    p.add_argument('--send', nargs='*', help='sizes of the pictures sent, WxH (default the plate and the style picture)')
    p.add_argument('--behind', action='store_true', help='add the behind painting (the lined-up painting sent back)')
    p.add_argument('--rate-cents', type=float, help='a rate to use instead of the table\'s')
    p.add_argument('--spent-dollars', type=float, help='what has been spent of the allowance so far')
    add_output_options(p)
    p = commands.add_parser('request', help='preflight, prompts, price and the request file')
    view_options(p, need_brief=True)
    p.add_argument('--style', help='the style picture to send as image 2')
    p.add_argument('--returned', help='as price')
    p.add_argument('--send', nargs='*', help='as price')
    p.add_argument('--rate-cents', type=float, help='as price')
    p.add_argument('--spent-dollars', type=float, help='as price')
    p.add_argument('--out-folder', help='write paint-request.json, the prompts and the near list here')
    p.add_argument('--ledger', help='add a planned entry to this paintings ledger (never sent)')
    p.add_argument('--ignore-preflight', action='store_true', help='write the request even if the preflight failed (say why)')
    add_output_options(p)
    p = commands.add_parser('fit-price', help='fit the rate to real charges read from fal')
    p.add_argument('--charges', required=True, help='JSON list of {"request_id", "cents", "output": "WxH", "inputs": ["WxH", ...]}')
    add_output_options(p)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    job = {'preflight': command_preflight, 'prompt': command_prompt, 'price': command_price, 'request': command_request,
           'fit-price': command_fit_price}[args.command]
    result, lines, code = job(args, settings)
    finish(f'paint_request {args.command}', result, lines, settings, args)
    return code


if __name__ == '__main__':
    sys.exit(run_main(main, 'paint_request'))
