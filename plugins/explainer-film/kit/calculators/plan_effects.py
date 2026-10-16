"""What this does: plans the live effects of a built-and-painted place before anything is filmed, so nobody has to
find the wind, the plume's path, the smoke colour or the contact shadows by hand again (log 34 needed five rounds for the
Works' smoke). It works from the place facts file (calculators/place_facts.py) and the house numbers in
film-settings.json, using the core's camera sums (frame_geometry.py) for every point on the frame.

  wind             chooses the wind against every view (the direction most across all of them, both signs traced, the
                   sign that passes in every view kept) and traces each chimney's plume on each view's frame with the same
                   sums as ChimneySmoke (works-effects.js): how far the plume travels while it can be seen, where its puffs'
                   TOP EDGES reach (not only their middles), whether it runs under a word card, whether it fades before
                   another factory's chimney, whether its puffs cross a figure, and which emitters never enter the frame
                   (drop them). Give --wind to judge one wind instead of choosing.
  colour           the plume's colour against the sky behind it (measured on the plate or painting) and the mouth's
                   size against the chimney top's width
  contact-shadows  a soft contact shadow for every near prop the behind painting removes: its size from the prop's base
                   footprint, its height, strength and fade-in from the slide's start
  window-change    how much a teaching event ("busy") changes the lit windows between two stills (15 levels or more)
  fire             the glow's pulse and the flames' variety, from numbers or read from the page and effects files
  lint             paper-look pages: every dust and smoke made through kit.effect, so it is put away with its page

Use:
  python3 plan_effects.py wind --place-facts works-place-facts.json [--smoke works-effects.js | smoke.json]
        [--smoking no-1-chimney=working --smoking no-2-chimney-a=heavy ...] [--view w3 --view w1]
        [--card w3:lower=0.06,0.1635,0.90,0.2365 ...] [--wind -0.85,-0.12,-0.5] [--main-view w1]
  python3 plan_effects.py colour --place-facts F --view w3 --picture works-w3-plate.jpg [--smoke ...] [--smoking ...]
  python3 plan_effects.py contact-shadows --place-facts F [--props drum,chair,pail] [--footprints footprints.json]
        [--slide-start 2.0]
  python3 plan_effects.py window-change --box 320,480,620,700 STILL_AT_WORD.jpg STILL_0.6_S_LATER.jpg [MORE.jpg ...]
  python3 plan_effects.py fire [--glow 1.25,0.02 | --page-file notice-corner.js] [--effects-file pit-village-effects.js]
  python3 plan_effects.py lint PAGE.js [PAGE.js ...]
Every command takes --json (print JSON), --out FILE, --report FILE and --settings FILE, and ends by naming the
film-settings.json values it used. Axes: places in Blender metres (x across, y forward, z up); wind and smoke offsets in
three.js axes (x, y up, z toward the cameras), as works-effects.js writes them. On the frame, across runs 0 (left) to 1
(right) and down 0 (top) to 1 (bottom).
"""
import argparse
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings, MissingSetting  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402
import frame_geometry as geometry  # noqa: E402

# The plume model: the same sums as ChimneySmoke.place() in works-effects.js (a puff's middle along the plume's line;
# each real puff also wanders up to about 1.5 k m to either side and up or down, and is 0.8 to 1.25 times as wide).
# These mirror that code, they are not house numbers: tests/test_plan_effects.py fails if the page code changes them.
RISE_POWER = 0.75          # climb = rise * k ** 0.75
DRIFT_POWER = 1.25         # blown = drift * k ** 1.25
MOUTH_LIFT = 0.3           # puffs start 0.3 m above the chimney top
WIDEN_POWER = 0.8          # size grows from size[0] to size[1] by rest ** 0.8
FADE_IN_SECONDS = 0.2      # strength * min(1, age / 0.2)
DEFAULT_FADE = 1.3         # settings.fade ?? 1.3
SPREAD_PER_K = 1.5         # puff.lift * 3 * k with lift in [-0.5, 0.5]: up to 1.5 k metres higher
SIZE_SPREAD = 1.25         # puff.size 0.8 to 1.25
# effects.js Smoke (the brazier's live smoke): the same, from that class
FIRE_SMOKE_RISE = 1.7      # y = origin + scale * 1.7 k
FIRE_SMOKE_SWAY = 0.12     # x wanders scale * 0.12 sin(...)
FIRE_SMOKE_SIZE = (0.35, 1.1)   # size = scale * puff.size * (0.35 + 1.1 k), puff.size 0.8 to 1.3
FIRE_SMOKE_PUFF_SIZE_MAX = 1.3
FIRE_SMOKE_OPACITY = 0.5   # opacity = 0.5 * min(1, age / 0.25) * (1 - k)
FIRE_SMOKE_FADE_IN = 0.25


# ------------------------------------------------------------------------------------------------ reading settings
def normalise_kind(name, raw, mouth_seconds_default):
    """One smoke kind in one form, from film-settings.json (mouth_seconds, mouth_size), a smoke_trace JSON or a page's
    SMOKE (mouth: {seconds, size}). A kind with no mouth at all (round 4's) has none."""
    kind = {'name': name, 'life': float(raw['life']), 'rise': float(raw['rise']), 'drift': float(raw['drift']),
            'size': [float(raw['size'][0]), float(raw['size'][1])], 'opacity': float(raw['opacity']),
            'fade': float(raw.get('fade', DEFAULT_FADE)), 'colour': raw.get('colour'), 'count': raw.get('count')}
    mouth = raw.get('mouth')
    if isinstance(mouth, dict):
        kind['mouth_seconds'] = float(mouth.get('seconds', mouth_seconds_default))
        kind['mouth_size'] = float(mouth.get('size', kind['size'][0]))
    elif 'mouth_size' in raw or 'mouth_seconds' in raw:
        kind['mouth_seconds'] = float(raw.get('mouth_seconds', mouth_seconds_default))
        kind['mouth_size'] = float(raw.get('mouth_size', kind['size'][0]))
        kind['mouth_seconds_from'] = 'given' if 'mouth_seconds' in raw else 'effects_planner.mouth_seconds_default'
    else:
        kind['mouth_seconds'], kind['mouth_size'] = 0.0, kind['size'][0]
    return kind


def js_object_to_json(text):
    """A plain JavaScript object literal (numbers, arrays, nested objects, bare keys, // comments) as JSON text."""
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', text)
    text = re.sub(r"'([^']*)'\s*:", r'"\1":', text)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


def balanced_block(text, start):
    """The text from the first '{' at or after start to its matching '}'."""
    opening = text.index('{', start)
    depth = 0
    for i in range(opening, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[opening:i + 1]
    raise ValueError('no matching }')


def read_smoke_from_page_code(path):
    """SMOKE and WIND from a page's effects file (works-effects.js writes `export const SMOKE = {...}` and
    `export const WIND = new THREE.Vector3(x, y, z)`)."""
    with open(path) as handle:
        code = handle.read()
    found = re.search(r'export\s+const\s+SMOKE\s*=', code)
    wind = re.search(r'export\s+const\s+WIND\s*=\s*new\s+THREE\.Vector3\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', code)
    if not found or not wind:
        raise SystemExit(f'plan_effects: {path} has no "export const SMOKE = {{...}}" and "export const WIND = new THREE.Vector3(...)"')
    kinds = json.loads(js_object_to_json(balanced_block(code, found.end())))
    return {'wind': [float(v) for v in wind.groups()], 'kinds': kinds}


def read_smoke(settings, path=None):
    """The wind (three.js axes, normalised) and smoke kinds: from --smoke (a JSON like smoke-final.json, or a page's
    effects .js file), else from film-settings.json (effects.wind_three_axes and effects.smoke_kinds)."""
    mouth_default = settings.value('effects_planner.mouth_seconds_default')
    if path:
        if path.endswith('.js') or path.endswith('.mjs'):
            raw, source = read_smoke_from_page_code(path), f'{os.path.basename(path)} (SMOKE and WIND)'
        else:
            with open(path) as handle:
                raw = json.load(handle)
            source = os.path.basename(path)
    else:
        raw = {'wind': settings.value('effects.wind_three_axes'), 'kinds': settings.value('effects.smoke_kinds')}
        source = 'film-settings.json effects.wind_three_axes and effects.smoke_kinds'
    kinds = {name: normalise_kind(name, k, mouth_default) for name, k in raw['kinds'].items()}
    return {'wind': geometry.normalise([float(v) for v in raw['wind']]), 'kinds': kinds, 'source': source}


# ------------------------------------------------------------------------------------------------ the plume model
def puff_at(kind, age):
    """A puff's offset from the chimney top (three.js axes, before the wind's direction is applied: climb and blown
    distances), its width in metres and its strength (0 to 1) at this age (seconds since it left the mouth)."""
    life = kind['life']
    k = age / life
    climb = kind['rise'] * k ** RISE_POWER
    blown = kind['drift'] * k ** DRIFT_POWER
    seconds, mouth = kind['mouth_seconds'], kind['mouth_size']
    if seconds > 0 and age < seconds:
        size = mouth + (kind['size'][0] - mouth) * (age / seconds)
    else:
        rest = (age - seconds) / max(1e-6, life - seconds)
        size = kind['size'][0] + (kind['size'][1] - kind['size'][0]) * max(0.0, rest) ** WIDEN_POWER
    strength = kind['opacity'] * min(1.0, age / FADE_IN_SECONDS) * max(0.0, 1 - k) ** kind['fade']
    return {'k': k, 'climb': climb, 'blown': blown, 'size': size, 'strength': strength}


def puff_centre_blender(top_blender, wind_three, puff, lift=0.0):
    """Where a puff's middle is (Blender metres), from the chimney top, the wind and the puff's climb and drift."""
    top = geometry.to_three(top_blender)
    x = top[0] + wind_three[0] * puff['blown']
    y = top[1] + MOUTH_LIFT + puff['climb'] + wind_three[1] * puff['blown'] + lift
    z = top[2] + wind_three[2] * puff['blown']
    return geometry.from_three([x, y, z])


def ages_for(life, step):
    count = int(round(life / step))
    return [i * step for i in range(count) if i * step < life]


def trace_plume(camera, top_blender, kind, wind_three, step):
    """Each traced age of one chimney's plume on one camera's frame: the puff's middle (across, down), its width on the
    frame, its top and bottom edges (down), its left and right edges (across), its strength, and (as information) how
    high a puff could reach with the code's random wander and size."""
    width, height = camera['frame']
    samples = []
    for age in ages_for(kind['life'], step):
        puff = puff_at(kind, age)
        centre = puff_centre_blender(top_blender, wind_three, puff)
        landed = geometry.project_point(camera, centre)
        if not landed['in_front']:
            samples.append({'age': age, 'in_front': False, 'strength': puff['strength']})
            continue
        size_pixels = geometry.size_in_pixels(camera, puff['size'], landed['depth'])
        half_down, half_across = size_pixels / 2 / height, size_pixels / 2 / width
        wander = geometry.project_point(camera, puff_centre_blender(top_blender, wind_three, puff, SPREAD_PER_K * puff['k']))
        widest_half = geometry.size_in_pixels(camera, puff['size'] * SIZE_SPREAD, wander['depth']) / 2 / height
        samples.append({'age': age, 'in_front': True, 'across': landed['across'], 'down': landed['down'], 'depth': landed['depth'],
                        'size_metres': puff['size'], 'width_share_of_height': 2 * half_down, 'top': landed['down'] - half_down,
                        'bottom': landed['down'] + half_down, 'left': landed['across'] - half_across, 'right': landed['across'] + half_across,
                        'strength': puff['strength'], 'highest_top_with_wander': wander['down'] - widest_half})
    return samples


def trace_fire_smoke(camera, coals_blender, fire, step):
    """The brazier's live smoke (effects.js Smoke) on one camera's frame: it rises 1.7 x scale over its life and leans
    `wind` x scale along +x (Blender and three.js), puffs up to 1.3 x scale x (0.35 + 1.1 k) wide."""
    width, height = camera['frame']
    origin = [coals_blender[0], coals_blender[1], coals_blender[2] + fire['above_coals_metres']]
    samples = []
    for age in ages_for(fire['life'], step):
        k = age / fire['life']
        centre = [origin[0] + fire['scale'] * fire['wind'] * k, origin[1], origin[2] + fire['scale'] * FIRE_SMOKE_RISE * k]
        size = fire['scale'] * FIRE_SMOKE_PUFF_SIZE_MAX * (FIRE_SMOKE_SIZE[0] + FIRE_SMOKE_SIZE[1] * k)
        strength = FIRE_SMOKE_OPACITY * min(1.0, age / FIRE_SMOKE_FADE_IN) * (1 - k)
        landed = geometry.project_point(camera, centre)
        if not landed['in_front']:
            continue
        sway = geometry.size_in_pixels(camera, fire['scale'] * FIRE_SMOKE_SWAY, landed['depth']) / width
        half = geometry.size_in_pixels(camera, size, landed['depth']) / 2
        samples.append({'age': age, 'across': landed['across'], 'down': landed['down'], 'strength': strength,
                        'left': landed['across'] - half / width - sway, 'right': landed['across'] + half / width + sway,
                        'top': landed['down'] - half / height, 'bottom': landed['down'] + half / height})
    return samples


# ------------------------------------------------------------------------------------------------ judging a plume
def overlaps(a, b):
    """Whether two boxes [left, top, right, bottom] overlap, and by how much down (b's bottom minus a's top)."""
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def figure_boxes(facts, camera, settings):
    """Each figure of the place on this camera's frame: [left, top, right, bottom] from its feet to its head."""
    width = settings.value('effects_planner.figure_box_width_metres')
    boxes = []
    for figure in facts.get('figures', []):
        feet = figure['feet']
        low, high = geometry.box_from_centre([feet[0], feet[1], feet[2] + figure['height_metres'] / 2], [width, width, figure['height_metres']])
        landed = geometry.project_box(camera, geometry.box_corners(low, high))
        if landed['box'] and landed['all_in_front']:
            box = landed['box']
            if box[2] > 0 and box[0] < 1 and box[3] > 0 and box[1] < 1:
                boxes.append({'name': figure['name'], 'box': box})
    return boxes


def judge_plume(samples, settings, cards=(), others=(), figures=(), emitter_across=None):
    """The planner's verdicts on one traced plume. cards: [(name, box)]; others: [(name, across, down)] other
    factories' chimney tops on this frame; figures: [{'name', 'box'}]."""
    visible_min = settings.value('effects_planner.visible_strength_min')
    edge_min = settings.value('effects_planner.edge_strength_min')
    travel_min = settings.value('effects_planner.travel_min_share_of_width')
    clearance = settings.value('effects_planner.other_chimney_clearance_share')
    figure_max = settings.value('effects_planner.figure_smoke_strength_max')
    front = [s for s in samples if s.get('in_front')]
    visible = [s for s in front if s['strength'] >= visible_min]
    edged = [s for s in front if s['strength'] >= edge_min]
    result = {'problems': [], 'notes': []}
    in_frame = [s for s in front if s['right'] > 0 and s['left'] < 1 and s['bottom'] > 0 and s['top'] < 1]
    result['enters_frame'] = bool(in_frame)
    if not visible:
        result['problems'].append('never seen (no puff reaches the visible strength)')
        return result
    acrosses = [s['across'] for s in visible]
    result['travel'] = max(acrosses) - min(acrosses)
    result['first_visible'] = [visible[0]['across'], visible[0]['down']]
    result['last_visible'] = [visible[-1]['across'], visible[-1]['down']]
    result['centre_down_range'] = [min(s['down'] for s in visible), max(s['down'] for s in visible)]
    result['top_edge_min'] = min(s['top'] for s in edged) if edged else None
    result['highest_top_with_wander'] = min(s['highest_top_with_wander'] for s in edged) if edged and 'highest_top_with_wander' in edged[0] else None
    if result['travel'] < travel_min:
        result['problems'].append(f'travels only {result["travel"]:.3f} of the width while seen (needs {travel_min}): the puffs pile up '
                                  f'(round 4: rings and a hook); blow it more across the view')
    for name, box in cards:
        over_edges = [s for s in edged if overlaps([s['left'], s['top'], s['right'], s['bottom']], box)]
        over_centres = [s for s in visible if box[0] <= s['across'] <= box[2] and box[1] <= s['down'] <= box[3]]
        if over_centres:
            result['problems'].append(f'puffs\' middles are inside the {name} card ({len(over_centres)} of the traced ages): the words hide the plume')
        elif over_edges:
            deepest = max(box[3] - s['top'] for s in over_edges)
            result['problems'].append(f'puffs\' top edges reach {min(s["top"] for s in over_edges):.3f} down, {deepest:.3f} into the {name} card '
                                      f'(it ends {box[3]:.4f} down; strength {edge_min} or more): the card covers the plume\'s top. '
                                      f'Sink the plume about {deepest:.3f} of the height, or move the card, or judge it by eye')
    if emitter_across is not None and len(visible) > 1:
        direction = 1 if visible[-1]['across'] >= visible[0]['across'] else -1
        last = visible[-1]['across']
        for name, across, down in others:
            if (across - emitter_across) * direction <= 0:
                continue
            gap = (across - last) * direction
            entry = {'chimney': name, 'across': across, 'gap': gap}
            result.setdefault('other_chimneys', []).append(entry)
            if gap < clearance:
                result['problems'].append(f'still seen {"past" if gap < 0 else "only " + format(gap, ".3f") + " short of"} {name}\'s chimney '
                                          f'({across:.3f} across; needs to fade {clearance} short): it would read as that factory\'s smoke')
    for figure in figures:
        thick = [s for s in front if s['strength'] > figure_max and overlaps([s['left'], s['top'], s['right'], s['bottom']], figure['box'])]
        if thick:
            result['problems'].append(f'puffs stronger than {figure_max} cross {figure["name"]} (a man in smoke reads as a grey ghost)')
    return result


# ------------------------------------------------------------------------------------------------ choosing the wind
def horizontal(v):
    n = math.hypot(v[0], v[1])
    return [v[0] / n, v[1] / n] if n > 1e-9 else None


def most_across(forwards):
    """The level direction (Blender x, y) that is most across every view's level direction: it maximises the smallest
    |sin| of the angle to each view (searched in tenths of a degree). Returns it and that smallest |sin|."""
    best, best_score = None, -1.0
    for tenth in range(0, 1800):
        angle = math.radians(tenth / 10)
        u = [math.cos(angle), math.sin(angle)]
        score = min(abs(u[0] * f[1] - u[1] * f[0]) for f in forwards)
        if score > best_score + 1e-12:
            best, best_score = u, score
    return best, best_score


def candidate_winds(forwards, main_forward, mix):
    """Both signs of the across direction, each with a little 'away from the main camera' and a little 'down', as
    works-effects.js mixes them, normalised, in three.js axes."""
    u, score = most_across(forwards)
    winds = []
    for sign in (1, -1):
        across = [sign * u[0], sign * u[1], 0.0]
        away = [main_forward[0], main_forward[1], 0.0]
        blender = [mix['across'] * across[0] + mix['away'] * away[0], mix['across'] * across[1] + mix['away'] * away[1], -mix['down']]
        winds.append(geometry.normalise(geometry.to_three(blender)))
    return winds, score


# ------------------------------------------------------------------------------------------------ the wind command
def parse_box(text):
    values = [float(v) for v in text.split(',')]
    if len(values) != 4:
        raise SystemExit(f'plan_effects: "{text}" is not a box left,top,right,bottom')
    return values


def parse_cards(items):
    """VIEW:NAME=left,top,right,bottom (shares of the frame) -> {view: [(name, box)]}; VIEW '*' means every view."""
    cards = {}
    for item in items or []:
        where, _, box = item.partition('=')
        view, _, name = where.partition(':')
        cards.setdefault(view or '*', []).append((name or 'card', parse_box(box)))
    return cards


def identifying_name(facts, emitter):
    """What an emitter identifies (a landmark top at the same place, e.g. 'No. 1'), else its own name."""
    for top in facts.get('landmark_tops', []):
        if geometry.length(geometry.subtract(top['top'], emitter['at'])) < 0.5 and top.get('identifies'):
            return top['identifies']
    return emitter['name']


def view_cameras(facts, settings, view):
    """The film camera at each spot a view's shot uses: the slide's start (the plate spot) and end (the composed spot),
    or the one spot of a held shot."""
    camera = view['camera']
    spots = []
    if camera.get('plate') and view.get('slide'):
        spots.append(('slide start', geometry.camera_from_place_facts(facts, settings, view['name'], 'plate', 'film')))
    if camera.get('composed'):
        spots.append(('composed', geometry.camera_from_place_facts(facts, settings, view['name'], 'composed', 'film')))
    if not spots:
        spots.append(('held', geometry.camera_from_place_facts(facts, settings, view['name'], 'composed', 'film')))
    return spots


def smoking_plan(facts, smoke, items):
    """Which chimney mouths smoke with which kind: NAME=KIND items, else every chimney mouth with the heaviest kind."""
    chimneys = [e for e in facts.get('emitters', []) if e.get('kind') == 'chimney mouth']
    by_name = {e['name']: e for e in chimneys}
    plan = {}
    if items:
        for item in items:
            name, _, kind = item.partition('=')
            if name not in by_name:
                raise SystemExit(f'plan_effects: no chimney mouth "{name}" in the place facts (there are: {", ".join(by_name)})')
            if kind not in smoke['kinds']:
                raise SystemExit(f'plan_effects: no smoke kind "{kind}" (kinds: {", ".join(smoke["kinds"])})')
            plan[name] = kind
    else:
        heaviest = max(smoke['kinds'].values(), key=lambda k: k['opacity'] * k['size'][1])['name']
        plan = {e['name']: heaviest for e in chimneys}
    return [(by_name[name], smoke['kinds'][kind]) for name, kind in plan.items()]


def trace_wind(facts, settings, smoke, wind, smoking, views, cards, step):
    """Every smoking chimney traced in every view for one wind; returns per view and spot the plumes and verdicts."""
    out = []
    for view in views:
        for spot, camera in view_cameras(facts, settings, view):
            tops = {e['name']: geometry.project_point(camera, e['at']) for e, _ in smoking}
            figures = figure_boxes(facts, camera, settings)
            view_cards = cards.get(view['name'], []) + cards.get('*', [])
            for emitter, kind in smoking:
                samples = trace_plume(camera, emitter['at'], kind, wind, step)
                mine = identifying_name(facts, emitter)
                others = []
                for other in facts.get('emitters', []):
                    if other.get('kind') != 'chimney mouth' or identifying_name(facts, other) == mine:
                        continue
                    landed = geometry.project_point(camera, other['at'])
                    if landed['in_front']:
                        others.append((other['name'], landed['across'], landed['down']))
                top = tops[emitter['name']]
                verdict = judge_plume(samples, settings, view_cards, others, figures, top['across'] if top['in_front'] else None)
                out.append({'view': view['name'], 'spot': spot, 'chimney': emitter['name'], 'kind': kind['name'],
                            'chimney_top_on_frame': [top['across'], top['down']] if top['in_front'] else None,
                            'samples': samples, **verdict})
    return out


def drop_list(traced):
    """Emitters whose plume never enters the frame at any spot of a view: drop them from that view."""
    seen = {}
    for row in traced:
        key = (row['view'], row['chimney'])
        seen[key] = seen.get(key, False) or row['enters_frame']
    return sorted(key for key, entered in seen.items() if not entered)


def summarise(traced):
    """Problems for the plumes that enter the frame (a plume outside the frame is dropped, not judged)."""
    dropped = set(drop_list(traced))
    problems = []
    for row in traced:
        if (row['view'], row['chimney']) in dropped:
            continue
        for problem in row['problems']:
            problems.append(f'{row["view"]} ({row["spot"]}) {row["chimney"]} ({row["kind"]}): {problem}')
    return problems


def command_wind(args, settings):
    with open(args.place_facts) as handle:
        facts = json.load(handle)
    smoke = read_smoke(settings, args.smoke)
    step = settings.value('effects_planner.trace_step_seconds')
    views = [v for v in facts['views'] if not args.view or v['name'] in args.view]
    if args.view and len(views) != len(args.view):
        raise SystemExit(f'plan_effects: unknown view in {args.view} (views: {", ".join(v["name"] for v in facts["views"])})')
    smoking = smoking_plan(facts, smoke, args.smoking)
    if not smoking:
        raise SystemExit('plan_effects: the place facts list no chimney mouths (emitters of kind "chimney mouth")')
    cards = parse_cards(args.card)
    lines, result = [], {'smoke_source': smoke['source'], 'smoking': {e['name']: k['name'] for e, k in smoking}}
    # the views that see a chimney (only they choose the wind)
    seeing = []
    for view in views:
        cameras = view_cameras(facts, settings, view)
        if any(geometry.project_point(c, e['at'])['in_front'] for _, c in cameras for e, _ in smoking):
            seeing.append((view, cameras[-1][1]))
    if args.wind:
        winds = [('given', geometry.normalise([float(v) for v in args.wind.split(',')]))]
        lines.append(f'Judging the given wind {fmt_vector(winds[0][1])} (three.js axes, normalised).')
    else:
        if not seeing:
            raise SystemExit('plan_effects: no view sees a chimney, so there is no wind to choose')
        forwards = [horizontal(cam['forward']) for _, cam in seeing]
        main = next((cam for view, cam in seeing if view['name'] == args.main_view), seeing[0][1])
        mix = settings.value('effects_planner.wind_mix')
        found, score = candidate_winds(forwards, horizontal(main['forward']), mix)
        winds = [('plus', found[0]), ('minus', found[1])]
        lines.append(f'Views that see a chimney: {", ".join(v["name"] for v, _ in seeing)}. The level direction most across all of them '
                     f'is at least {math.degrees(math.asin(min(1, score))):.1f} degrees off every view. Tracing both signs '
                     f'(the across part {mix["across"]}, away from {args.main_view or seeing[0][0]["name"]} {mix["away"]}, down {mix["down"]}):')
    lines.append(f'Smoke kinds from {smoke["source"]}; traced every {step} s of a puff\'s life.')
    tried = []
    for label, wind in winds:
        traced = trace_wind(facts, settings, smoke, wind, smoking, views, cards, step)
        problems = summarise(traced)
        tried.append({'label': label, 'wind_three_axes': wind, 'problems': problems, 'dropped': drop_list(traced), 'plumes': traced})
    for t in tried:
        seen = [row['travel'] for row in t['plumes'] if 'travel' in row and (row['view'], row['chimney']) not in set(t['dropped'])]
        t['smallest_travel'] = min(seen) if seen else 0.0
    # the sign that passes in every view; else the fewest problems, then the longer smallest trail
    ranked = sorted(tried, key=lambda t: (len(t['problems']), -t['smallest_travel']))
    passing = [t for t in ranked if not t['problems']]
    chosen = ranked[0]
    result.update({'tried': [{k: v for k, v in t.items() if k != 'plumes'} for t in tried], 'chosen': chosen['label'],
                   'chosen_wind_three_axes': chosen['wind_three_axes'], 'passes': not chosen['problems']})
    for t in tried:
        lines.append('')
        lines.append(f'Wind {t["label"]} {fmt_vector(t["wind_three_axes"])}: '
                     + ('passes in every view.' if not t['problems'] else f'{len(t["problems"])} problem(s).'))
        for row in t['plumes']:
            if (row['view'], row['chimney']) in set(t['dropped']):
                continue
            if 'travel' not in row:
                lines.append(f'  {row["view"]} {row["spot"]:11s} {row["chimney"]} ({row["kind"]}): never seen')
                continue
            top = f'{row["top_edge_min"]:.3f}' if row['top_edge_min'] is not None else '-'
            lines.append(f'  {row["view"]} {row["spot"]:11s} {row["chimney"]} ({row["kind"]}): travels {row["travel"]:.3f} of the width while seen, '
                         f'from {row["first_visible"][0]:.3f} to {row["last_visible"][0]:.3f} across; middles {row["centre_down_range"][0]:.3f}-'
                         f'{row["centre_down_range"][1]:.3f} down, top edges from {top} down'
                         + ''.join(f'; fades {o["gap"]:.3f} short of {o["chimney"]}' for o in row.get('other_chimneys', [])))
        band = settings.value('safe_area.title_band_down')
        under_words = sorted({(row['view'], row['chimney']) for row in t['plumes'] if 'centre_down_range' in row
                              and (row['view'], row['chimney']) not in set(t['dropped'])
                              and row['centre_down_range'][0] < band[1] and row['centre_down_range'][1] > band[0]
                              and not cards.get(row['view']) and not cards.get('*')})
        for name, chimney in under_words:
            lines.append(f'  note: in {name} {chimney}\'s plume runs in the title band ({band[0]}-{band[1]} down) and no word boxes were given '
                         f'for {name}: give them with --card {name}:NAME=l,t,r,b, or draw a soft band behind the words')
        for name, chimney in t['dropped']:
            lines.append(f'  {name}: {chimney}\'s plume never enters the frame: drop it from this view')
        for problem in t['problems']:
            lines.append(f'  PROBLEM {problem}')
    lines.append('')
    if args.wind:
        lines.append('The given wind passes.' if result['passes'] else 'The given wind does not pass (see the problems above).')
    elif passing:
        lines.append(f'Use wind {fmt_vector(chosen["wind_three_axes"])} (the {chosen["label"]} sign): it passes in every view.'
                     + (' Both signs pass; this one is listed first.' if len(passing) > 1 else ''))
    else:
        lines.append(f'Neither sign passes in every view. The {chosen["label"]} sign {fmt_vector(chosen["wind_three_axes"])} has the fewest problems '
                     f'and the longest shortest trail ({chosen["smallest_travel"]:.3f} of the width). '
                     'A person must choose: change the drift or life, move a word card, or accept a problem (in the place facts\' accepted list).')
    longest = max(k['life'] for _, k in smoking)
    lines.append(f'Plumes that start on a word take their life ({longest:g} s) to reach full length; ChimneySmoke depends only on time, so '
                 f'filming needs no pre-roll for it ({settings.value("effects_planner.smoke_preroll_note")} s).')
    result['plumes'] = [strip_samples(row, args.full_trace) for row in chosen['plumes']]
    return result, lines


def strip_samples(row, keep):
    row = dict(row)
    if not keep:
        row['samples'] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k in ('age', 'across', 'down', 'top', 'strength')}
                          for s in row['samples'] if s.get('in_front')]
    return row


def fmt_vector(v):
    return '(' + ', '.join(f'{x:.3f}' for x in v) + ')'


# ------------------------------------------------------------------------------------------------ colour and mouth
def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def lab(rgb):
    """sRGB levels (0-255) to CIE Lab (D65), for the colour difference between the plume and the sky."""
    def linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(float(c)) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = [v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116 for v in (x, y, z)]
    return [116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])]


def colour_difference(a, b):
    la, lb = lab(a), lab(b)
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(la, lb)))


def sky_behind(picture_path, camera, samples, settings):
    """The sky's mean colour (0-255 levels) behind a traced plume, measured on a picture drawn from `camera` (the plate
    camera and lens for a plate or painting): a box half the puff's size round each seen puff's middle."""
    import numpy as np
    from PIL import Image
    picture = np.asarray(Image.open(picture_path).convert('RGB')).astype(float)
    rows, cols = picture.shape[:2]
    visible_min = settings.value('effects_planner.visible_strength_min')
    values = []
    for s in samples:
        if not s.get('in_front') or s['strength'] < visible_min:
            continue
        half = max(1, int(s['width_share_of_height'] * rows / 4))
        x, y = int(s['across'] * cols), int(s['down'] * rows)
        if 0 <= x < cols and 0 <= y < rows:
            values.append(picture[max(0, y - half):y + half + 1, max(0, x - half):x + half + 1].reshape(-1, 3).mean(axis=0))
    if not values:
        return None, 0
    return [float(v) for v in np.mean(values, axis=0)], len(values)


def command_colour(args, settings):
    with open(args.place_facts) as handle:
        facts = json.load(handle)
    smoke = read_smoke(settings, args.smoke)
    step = settings.value('effects_planner.trace_step_seconds')
    lighter_max = settings.value('effects_planner.plume_lighter_than_sky_max_levels')
    difference_min = settings.value('effects_planner.plume_colour_difference_min')
    ratio_min = settings.value('effects_planner.mouth_to_chimney_top_ratio_min')
    view = next((v for v in facts['views'] if v['name'] == args.view), None)
    if view is None:
        raise SystemExit(f'plan_effects: no view "{args.view}" (views: {", ".join(v["name"] for v in facts["views"])})')
    smoking = smoking_plan(facts, smoke, args.smoking)
    from PIL import Image
    with Image.open(args.picture) as picture:
        cols, rows = picture.size
    spot = args.spot
    camera = geometry.camera_from_place_facts(facts, settings, view['name'], spot, 'plate' if spot == 'plate' else 'film')
    camera = geometry.with_lens(camera, camera['vertical_fov_degrees'], cols, rows)
    wind = geometry.normalise([float(v) for v in args.wind.split(',')]) if args.wind else smoke['wind']
    lines = [f'Plume colour and mouth in {view["name"]}, the sky measured on {os.path.basename(args.picture)} ({cols} x {rows}) from the {spot} '
             f'camera with a {camera["vertical_fov_degrees"]:g} degree lens; wind {fmt_vector(wind)}.']
    rows_out = []
    for emitter, kind in smoking:
        samples = trace_plume(camera, emitter['at'], kind, wind, step)
        sky, count = sky_behind(args.picture, camera, samples, settings)
        row = {'chimney': emitter['name'], 'kind': kind['name'], 'colour': kind['colour'], 'sky_colour': sky, 'samples_measured': count,
               'problems': [], 'notes': []}
        if kind['colour'] and sky is not None:
            lighter = luminance(kind['colour']) - luminance(sky)
            difference = colour_difference(kind['colour'], sky)
            row.update({'lighter_than_sky_levels': lighter, 'colour_difference': difference})
            if lighter > lighter_max:
                scale = (luminance(sky) + lighter_max / 2) / luminance(kind['colour'])
                row['suggested_colour'] = [round(c * scale) for c in kind['colour']]
                row['problems'].append(f'{lighter:+.0f} levels lighter than the sky (at most {lighter_max}): pale smoke on a dusk sky reads as a glow '
                                       f'(round 4). Try {row["suggested_colour"]} (the same hue, {lighter_max / 2:.0f} levels over the sky)')
            if difference < difference_min:
                row['problems'].append(f'only {difference:.0f} colour-difference units from the sky (at least {difference_min}): the plume will hardly '
                                       f'show; make it browner or darker than the sky')
            lines.append(f'{emitter["name"]} ({kind["name"]}): smoke {kind["colour"]} against the sky\'s {[round(v) for v in sky]} ({count} places '
                         f'along the plume): {lighter:+.0f} levels lighter, colour difference {difference:.0f}')
        elif sky is None:
            row['problems'].append('the plume is not in this picture')
            lines.append(f'{emitter["name"]}: the plume is not in this picture')
        else:
            row['notes'].append('the kind has no colour')
            lines.append(f'{emitter["name"]} ({kind["name"]}): the kind has no colour; the sky behind it is {[round(v) for v in sky]}: choose a '
                         f'colour at most {lighter_max} levels lighter and at least {difference_min} colour-difference units away')
        if emitter.get('radius_metres'):
            width = 2 * emitter['radius_metres']
            ratio = kind['mouth_size'] / width
            row.update({'chimney_top_width': width, 'mouth_size': kind['mouth_size'], 'mouth_ratio': ratio})
            if ratio < ratio_min:
                row['problems'].append(f'the mouth ({kind["mouth_size"]} m) is narrower than the chimney top ({width:.2f} m): use at least '
                                       f'{width * ratio_min:.2f} m so the plume leaves the whole top')
            lines.append(f'  mouth {kind["mouth_size"]} m for a top {width:.2f} m wide: ratio {ratio:.2f}'
                         + (' (a square top\'s diagonal is 1.41 times its side)' if ratio > 1.3 else ''))
        for problem in row['problems']:
            lines.append(f'  PROBLEM {problem}')
        rows_out.append(row)
    return {'view': view['name'], 'picture': args.picture, 'plumes': rows_out,
            'problems': sum(len(r['problems']) for r in rows_out)}, lines


# ------------------------------------------------------------------------------------------------ contact shadows
def ground_height_under(facts, point):
    """The height of the ground (road, pavement, ground, floor) under a point, from the place facts' support surfaces
    (a sloped surface rises by its slope from its 'at' point); None if none is given."""
    best = None
    for surface in facts.get('support_surfaces', []):
        if surface.get('kind') not in ('ground', 'road', 'pavement', 'floor'):
            continue
        xr, yr = surface.get('x_range'), surface.get('y_range')
        if xr and not xr[0] <= point[0] <= xr[1]:
            continue
        if yr and not yr[0] <= point[1] <= yr[1]:
            continue
        height = surface['height']
        if surface.get('slope') and surface.get('at'):
            height += surface['slope'][0] * (point[0] - surface['at'][0]) + surface['slope'][1] * (point[1] - surface['at'][1])
        if best is None or abs(height - point[2]) < abs(best - point[2]):
            best = height
    return best


def command_contact_shadows(args, settings):
    with open(args.place_facts) as handle:
        facts = json.load(handle)
    footprints = {}
    if args.footprints:
        with open(args.footprints) as handle:
            footprints = json.load(handle).get('footprints', {})
    per = settings.value('effects_planner.contact_shadow_size_per_footprint_diagonal')
    on_ground = settings.value('effects_planner.contact_shadow_on_ground_within_metres')
    shadow = settings.value('effects.contact_shadow')
    props = {p['name']: p for p in facts.get('props', [])}
    names = [n.strip() for n in args.props.split(',')] if args.props else None
    if names:
        missing = [n for n in names if n not in props]
        if missing:
            raise SystemExit(f'plan_effects: no prop {", ".join(missing)} in the place facts (props: {", ".join(props)})')
    else:
        names = [n for n, p in props.items() if p.get('role') in ('subject', 'support', 'story') and p.get('size')]
    lines = [f'Contact shadows (the behind painting removes the painted ones): side = {per} x the base footprint\'s diagonal, '
             f'{shadow["height_above_ground_metres"]} m above the ground, strength {shadow["opacity"]}, faded in over '
             f'{shadow["fade_in_seconds"]} s from the slide\'s start' + (f' ({args.slide_start} s).' if args.slide_start is not None else '.')]
    out = []
    for name in names:
        prop = props[name]
        size = prop.get('size')
        bottom = prop['at'][2] - size[2] / 2 if size else prop['at'][2]
        ground = ground_height_under(facts, [prop['at'][0], prop['at'][1], bottom])
        row = {'prop': name, 'centre': [prop['at'][0], prop['at'][1]], 'bottom': bottom, 'ground': ground}
        if name in footprints:
            fp = footprints[name]
            width, depth = fp['width'], fp['depth']
            row['footprint_from'] = 'measured base (' + fp.get('how', 'footprints file') + ')'
            if fp.get('centre'):
                row['centre'] = fp['centre'][:2]
            if fp.get('bottom') is not None:
                bottom = fp['bottom']
                row['bottom'] = bottom
        elif size:
            width, depth = size[0], size[1]
            row['footprint_from'] = 'the whole box (larger than the base: measure the base with paper-film/blender/set_measurements.py footprints)'
        else:
            lines.append(f'{name}: no size or footprint: skipped')
            continue
        if ground is not None and bottom - ground > on_ground and not args.props:
            lines.append(f'{name}: stands {bottom - ground:.2f} m above the ground (on another prop): no ground shadow')
            continue
        diagonal = math.hypot(width, depth)
        side = per * diagonal
        row.update({'footprint': [width, depth], 'diagonal': diagonal, 'shadow_side': side,
                    'height': (ground if ground is not None else bottom) + shadow['height_above_ground_metres'],
                    'opacity': shadow['opacity'], 'fade_in_seconds': shadow['fade_in_seconds'], 'fade_from': args.slide_start})
        out.append(row)
        lines.append(f'{name}: base {width:.3f} x {depth:.3f} m (diagonal {diagonal:.3f}) -> shadow {side:.2f} x {side:.2f} m at '
                     f'({row["centre"][0]:.3f}, {row["centre"][1]:.3f}), {row["height"]:.3f} m high [{row["footprint_from"]}]')
    lines.append('In the page: contactShadow(side, side) from pit-village-effects.js, placed at the ground under the prop + the height above, '
                 'its opacity = strength x smooth((t - slide start) / fade-in) (as notice-corner.js does).')
    return {'shadows': out}, lines


# ------------------------------------------------------------------------------------------------ window change
def window_change(box, first_path, other_paths, settings):
    """How much the lit windows inside `box` (pixels: left, top, right, bottom) change from the first still to each
    other: the lit windows are the first still's pixels brighter than the mask's brightness and redder than blue."""
    import numpy as np
    from PIL import Image
    mask_settings = settings.value('effects_planner.window_mask')
    left, top, right, bottom = [int(v) for v in box]
    first = np.asarray(Image.open(first_path).convert('RGB')).astype(float)[top:bottom, left:right]
    luma = first @ [0.2126, 0.7152, 0.0722]
    mask = (luma > mask_settings['brightness_min']) & (first[..., 0] > first[..., 2] + mask_settings['red_over_blue_min'])
    rows = []
    for path in other_paths:
        other = np.asarray(Image.open(path).convert('RGB')).astype(float)[top:bottom, left:right]
        other_luma = other @ [0.2126, 0.7152, 0.0722]
        change = (other_luma - luma)[mask]
        rows.append({'still': path, 'mean_level': float(other_luma[mask].mean()) if mask.any() else None,
                     'mean_change': float(change.mean()) if mask.any() else None,
                     'size_of_change': float(abs(change).mean()) if mask.any() else None})
    return {'window_pixels': int(mask.sum()), 'first_level': float(luma[mask].mean()) if mask.any() else None, 'others': rows}


def command_window_change(args, settings):
    if len(args.stills) < 2:
        raise SystemExit('plan_effects window-change: give the still at the word and at least one later still')
    needed = settings.value('effects.busy_window_change_min_levels')
    after = settings.value('effects_planner.window_change_after_word_seconds')
    box = [float(v) for v in args.box.split(',')]
    found = window_change(box, args.stills[0], args.stills[1:], settings)
    lines = [f'Lit windows in {args.box} (pixels): {found["window_pixels"]} pixels, {found["first_level"]:.1f} levels in the first still '
             f'(compare the still at the word with one about {after} s later).' if found['first_level'] is not None else
             f'No lit window pixels in {args.box}: check the box.']
    best = 0.0
    for row in found['others']:
        if row['size_of_change'] is None:
            continue
        best = max(best, row['size_of_change'])
        lines.append(f'  {os.path.basename(row["still"])}: {row["mean_level"]:.1f} levels, change {row["mean_change"]:+.1f}, '
                     f'size of change {row["size_of_change"]:.1f}')
    passes = best >= needed
    boost = needed / best if best > 0 else None
    lines.append(f'Largest change {best:.1f} levels against the {needed} needed: ' + ('seen.' if passes else
                 f'too small to see. Raise the event\'s strength about {boost:.1f} times (or add a moving dark band, as round 5 did) and measure again.'))
    return {**found, 'largest_change': best, 'needed': needed, 'passes': passes, 'boost_factor': None if passes else boost}, lines


# ------------------------------------------------------------------------------------------------ fire: glow and flames
def read_glow_pulse(path):
    """glow.scale.setScalar(BASE + AMPLITUDE * Math.sin(...)) in a page file: every one found."""
    with open(path) as handle:
        code = handle.read()
    return [{'name': m.group(1), 'base': float(m.group(2)), 'amplitude': float(m.group(3))}
            for m in re.finditer(r'(\w+)\.scale\.setScalar\(\s*([\d.]+)\s*\+\s*([\d.]+)\s*\*\s*Math\.sin', code)]


def read_flames(path):
    """The Flames class's tongues, sizes and leans in an effects file (pit-village-effects.js)."""
    with open(path) as handle:
        code = handle.read()
    block = code[code.index('class Flames'):]
    tongues = re.search(r'this\.tongues\s*=\s*\[(.*?)\]\s*\n?\s*\.map', block, re.S)
    count = len(re.findall(r'\[[^\[\]]+\]', tongues.group(1))) if tongues else None
    size = re.search(r'const size = ([\d.]+) \+ random\(\) \* ([\d.]+)', block)
    lean = re.search(r'lean: \(random\(\) - 0\.5\) \* ([\d.]+)', block)
    found = {'tongues': count}
    if size:
        low, spread = float(size.group(1)), float(size.group(2))
        middle = low + spread / 2
        found['size_range'] = [low, low + spread]
        found['size_share_each_way'] = (spread / 2) / middle
    if lean:
        found['lean_degrees_each_way'] = math.degrees(float(lean.group(1)) / 2)
    return found


def command_fire(args, settings):
    limit = settings.value('effects_planner.glow_pulse_setting_max_share')
    variety = settings.value('effects_planner.flame_variety_min')
    filmed = settings.value('effects.glow_size_swing_share')
    lines, result = [], {'glows': [], 'flames': None, 'problems': []}
    glows = []
    if args.glow:
        base, amplitude = [float(v) for v in args.glow.split(',')]
        glows.append({'name': 'given', 'base': base, 'amplitude': amplitude})
    for path in args.page_file or []:
        glows += [dict(g, file=os.path.basename(path)) for g in read_glow_pulse(path)]
    for g in glows:
        swing = g['amplitude'] / g['base']
        g['swing_share'] = swing
        g['passes'] = swing <= limit + 1e-12
        where = f' in {g["file"]}' if g.get('file') else ''
        lines.append(f'Glow {g["name"]}{where}: size {g["base"]} +- {g["amplitude"]} = {swing * 100:.2f}% swing (setting limit {limit * 100:.1f}%; '
                     f'the kept notice corner filmed at {filmed * 100:.1f}% on screen)' + ('' if g['passes'] else ': PROBLEM its rim will slide on the ground'))
        if not g['passes']:
            result['problems'].append(f'glow {g["name"]}{where} swings {swing * 100:.1f}%: keep it to {limit * 100:.1f}% (log 32: 8% slid the rim 20 px)')
        result['glows'].append(g)
    if args.effects_file:
        flames = read_flames(args.effects_file)
        result['flames'] = flames
        lines.append(f'Flames in {os.path.basename(args.effects_file)}: {flames.get("tongues")} tongues, sizes '
                     f'{flames.get("size_range")} (+-{flames.get("size_share_each_way", 0) * 100:.0f}%), leans +-{flames.get("lean_degrees_each_way", 0):.1f} degrees.')
        if flames.get('size_share_each_way', 0) < variety['size_share']:
            result['problems'].append(f'flame sizes vary only +-{flames.get("size_share_each_way", 0) * 100:.0f}% (at least +-{variety["size_share"] * 100:.0f}%): they read as a neat row')
        if flames.get('lean_degrees_each_way', 0) < variety['lean_degrees']:
            result['problems'].append(f'flame leans vary only +-{flames.get("lean_degrees_each_way", 0):.1f} degrees (at least +-{variety["lean_degrees"]})')
    if not glows and not args.effects_file:
        raise SystemExit('plan_effects fire: give --glow BASE,AMPLITUDE, --page-file PAGE.js or --effects-file EFFECTS.js')
    for problem in result['problems']:
        lines.append(f'PROBLEM {problem}')
    lines.append('Flames, smoke and glows are drawn live in the film, never in the plate or the painting (lesson 89).')
    return result, lines


# ------------------------------------------------------------------------------------------------ lint
EFFECT_CLASSES = ('Smoke', 'Dust', 'Snow', 'Sparks', 'Flames', 'ChimneySmoke', 'CoinRain')


def lint_page(path):
    """Paper-look pages (they import paper-kit.js and share one scene): every effect made through kit.effect(...), so it
    is hidden with its page (lesson 29). Cinema pages (cinema-kit.js) each have their own scene and are not linted."""
    with open(path) as handle:
        code = handle.read()
    if 'paper-kit' not in code:
        return {'file': path, 'kind': 'not a paper-look page (each cinema page has its own scene)', 'problems': []}
    problems = []
    for match in re.finditer(r'new\s+(' + '|'.join(EFFECT_CLASSES) + r')\s*\(', code):
        before = code[max(0, match.start() - 40):match.start()]
        line_start = code.rfind('\n', 0, match.start()) + 1
        line = code[line_start:code.find('\n', match.start())]
        if re.search(r'effect\(\s*$', before):
            continue
        assigned = re.match(r'\s*(?:const|let|var)?\s*([\w.]+)\s*=', line)
        if assigned and re.search(r'effect\(\s*' + re.escape(assigned.group(1)) + r'\s*[,)]', code):
            continue
        number = code.count('\n', 0, match.start()) + 1
        problems.append(f'{os.path.basename(path)} line {number}: new {match.group(1)}(...) not made through kit.effect: it will stay on other pages')
    return {'file': path, 'kind': 'paper-look page', 'problems': problems}


def command_lint(args, settings):
    files = []
    for item in args.pages:
        files += sorted(glob.glob(item)) or [item]
    found = [lint_page(f) for f in files]
    lines = []
    for row in found:
        lines.append(f'{os.path.basename(row["file"])}: {row["kind"]}: ' + (f'{len(row["problems"])} problem(s)' if row['problems'] else 'fine'))
        for problem in row['problems']:
            lines.append(f'  PROBLEM {problem}')
    return {'pages': found, 'problems': sum(len(r['problems']) for r in found)}, lines


# ------------------------------------------------------------------------------------------------ command line
def main(argv=None):
    parser = argparse.ArgumentParser(description='Plans live effects (wind and smoke, colour, contact shadows, window change, fire) '
                                                 'before filming. See the note at the top of this file.')
    commands = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(commands.add_parser('wind', help='choose the wind against every view and trace each chimney plume'))
    p.add_argument('--place-facts', required=True, help='the place facts file (views, chimney mouths, landmark tops, figures)')
    p.add_argument('--smoke', help='smoke kinds and wind: a JSON (smoke-final.json form) or a page effects file (works-effects.js); '
                                   'default film-settings.json effects')
    p.add_argument('--smoking', action='append', help='NAME=KIND: this chimney mouth smokes with this kind (repeat); default every '
                                                      'chimney with the heaviest kind')
    p.add_argument('--view', action='append', help='only these views (repeat)')
    p.add_argument('--main-view', help='the view the wind blows a little away from (default the first that sees a chimney)')
    p.add_argument('--card', action='append', help='VIEW:NAME=left,top,right,bottom (shares): a word card the plume must stay under; '
                                                   'VIEW * for every view (repeat)')
    p.add_argument('--wind', help='judge this wind (x,y,z three.js axes) instead of choosing one')
    p.add_argument('--full-trace', action='store_true', help='keep every traced number in the JSON')
    p = add_output_options(commands.add_parser('colour', help='the plume colour against the sky behind it, and the mouth size'))
    p.add_argument('--place-facts', required=True)
    p.add_argument('--view', required=True)
    p.add_argument('--picture', required=True, help='the plate or painting of that view')
    p.add_argument('--spot', default='plate', choices=['plate', 'composed'], help='where the picture was drawn from (default plate)')
    p.add_argument('--smoke')
    p.add_argument('--smoking', action='append')
    p.add_argument('--wind', help='x,y,z three.js axes (default: the smoke settings\' wind)')
    p = add_output_options(commands.add_parser('contact-shadows', help='soft shadows for the near props the behind painting removes'))
    p.add_argument('--place-facts', required=True)
    p.add_argument('--props', help='the props, separated by commas (default: subject, support and story props standing on the ground)')
    p.add_argument('--footprints', help='a JSON of measured base footprints (paper-film/blender/set_measurements.py footprints)')
    p.add_argument('--slide-start', type=float, help='the slide\'s start (seconds), when the shadows begin to fade in')
    p = add_output_options(commands.add_parser('window-change', help='how much a teaching event changes the lit windows'))
    p.add_argument('--box', required=True, help='left,top,right,bottom in pixels round the windows')
    p.add_argument('stills', nargs='+', help='the still at the word, then one or more later stills')
    p = add_output_options(commands.add_parser('fire', help='the glow\'s pulse and the flames\' variety'))
    p.add_argument('--glow', help='BASE,AMPLITUDE of the glow\'s size pulse')
    p.add_argument('--page-file', action='append', help='a page file to read glow pulses from (repeat)')
    p.add_argument('--effects-file', help='an effects file with the Flames class (pit-village-effects.js)')
    p = add_output_options(commands.add_parser('lint', help='paper-look pages: effects made through kit.effect'))
    p.add_argument('pages', nargs='+')
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    runner = {'wind': command_wind, 'colour': command_colour, 'contact-shadows': command_contact_shadows,
              'window-change': command_window_change, 'fire': command_fire, 'lint': command_lint}[args.command]
    try:
        result, lines = runner(args, settings)
    except MissingSetting as problem:
        raise SystemExit(f'plan_effects: {problem}')
    full = finish(f'plan_effects {args.command}', result, lines, settings, args)
    failed = (args.command == 'wind' and not full.get('passes')) or (args.command in ('colour', 'lint') and full.get('problems')) or \
        (args.command == 'window-change' and not full.get('passes')) or (args.command == 'fire' and full.get('problems'))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
