"""What this does: plans the pictures a held shot cuts or blends to when something in it changes on a spoken word (the
men gone on "go", the windows lit on "start"), so the helper plates, the cut-or-blend choice and the commands come out
the same way every time instead of being found round by round (logs 34, rounds 2 to 5).

From a page plan of state changes (which view, which word, which state it goes to, which of the state's fields that
word changes) and the place facts (views, slides, states, figures) it works out:
  - every plate the place needs: one per (view, state after each change) in order, and for every view with a slide a
    "behind" plate: the same state as the main plate with the near things left out (round 3: a behind picture made from
    another state lit No. 1's doorway the moment the slide began);
  - errors: a change inside a slide (a state changes only while the camera holds); two sub-changes on one plate timed
    on different words (round 4: the slowed plate held both the dark windows and the men, so a window blend on "slows"
    would have faded the men in as ghosts), with the extra plate that fixes it;
  - warnings: a time cut where only people change (lesson 136: they seem to blink out; change something else with
    them); a state described as busy with nobody seen at work, or a worker whose face could show (round 4); a cue (lit
    windows, smoke) that does not land in the frame below the words band (round 3: No. 2's windows were out of frame);
  - cut or blend from the share of the frame the change swaps (measured with make_state_picture.py on the plates, when
    given): a time cut on the word up to 0.12 of the frame, else the project's stepped blend (0.8 s in 3 steps,
    works-effects.js steppedBlend); things that come and go swapping over 3 times their own outline (long shadows,
    blocked light: the people test 5.6 times) are flagged, and any swap over 0.15 of the frame;
  - the thresholds from the plates' measured noise (max(6, 3 x noise), max(3, 3 x smooth noise): render noise has been
    0.0 to 0.9 levels, so they stay 6 and 3) and the exact make_state_picture.py and make_behind_picture.py commands.

The page plan (JSON; see tests/fixtures/painting/works-state-plan.json):
  {"place_facts": "works-place-facts.json", "plate_folder": "...", "facts_folders": {"w1": "..."},
   "plates": {"w1/quiet": "works-w1-plate.jpg", ...}, "field_groups": {"men_1": ["man 1", ...]},
   "pages": [{"page": 3, "view": "w1", "start_state": "quiet", "slides": [{"from": 57.9, "to": 61.0}],
              "changes": [{"word": "go", "time": 67.2, "to_state": "men gone", "changes": ["men_1", ...],
                           "cue_points": [[x, y, z], ...]}]}]}
Use:
  python3 plan_states.py plan --plan works-state-plan.json [--measure] [--out-folder DIR] [--plate-folder DIR] [--facts-folder VIEW=DIR ...]
--measure runs make_state_picture.py on each pair of plates the plan names (its pictures go to a scratch folder and are
deleted) to measure the swap and the noise. Without it the shares are "not measured". Prints a plain report (or --json)
naming the film-settings.json values it used; exit 1 when the plan has an error.
"""
import argparse
import json
import math
import os
import shutil
import sys
import tempfile

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402
import frame_geometry as geometry  # noqa: E402
import painting_measures as measures  # noqa: E402

TOOL = 'kit/paper-film/tools'


def note(found, kind, words, **numbers):
    found.append({'kind': kind, 'what': words, **measures.round_all(numbers)})


def people_field(name, settings):
    return any(w in name.lower() for w in settings.value('painting_tools.plan_states.people_field_words'))


def state_name(base, fields):
    return f'{base} (only {", ".join(fields)})'


# ------------------------------------------------------------------------------------------------ the plan
def walk_changes(plan, place, settings, found):
    """Walks each page's changes in time order: the plates needed, sub-changes bundled on one plate, changes in a slide,
    people-only cuts. Returns the plates [{view, state, fields, from_page, word}] and the changes."""
    states = place.get('states', {})
    plates, changes = [], []
    seen = set()

    def add_plate(view, state, fields, why):
        key = (view, state)
        if key not in seen:
            seen.add(key)
            plates.append({'view': view, 'state': state, 'fields': fields, 'why': why})

    for page in plan['pages']:
        view = page['view']
        current_name = page['start_state']
        if current_name not in states:
            note(found, 'error', f'page {page["page"]}: the start state "{current_name}" is not in the place facts\' states ({", ".join(states)})')
            continue
        current = dict(states[current_name])
        add_plate(view, current_name, current, f'page {page["page"]}: the view\'s main plate')
        events = sorted(page.get('changes', []), key=lambda e: e['time'])
        for k, event in enumerate(events):
            target = states.get(event['to_state'])
            if target is None:
                note(found, 'error', f'page {page["page"]} "{event["word"]}": no state "{event["to_state"]}" in the place facts')
                continue
            for slide in page.get('slides', []):
                if slide['from'] < event['time'] < slide['to']:
                    note(found, 'error', f'page {page["page"]} "{event["word"]}" at {event["time"]} s falls inside the slide '
                                         f'({slide["from"]} to {slide["to"]} s): a state changes only while the camera holds (plan T9)',
                         page=page['page'], word=event['word'])
            differ = [f for f in target if f != 'about' and target.get(f) != current.get(f)]
            declared = [f for f in event.get('changes', differ) if f in differ]
            bundled = [f for f in differ if f not in declared]
            later = {f: e['word'] for e in events[k + 1:] for f in e.get('changes', []) if f in bundled}
            reached = dict(current)
            for f in declared:
                reached[f] = target[f]
            if bundled and later:
                derived = state_name(event['to_state'], declared)
                note(found, 'error', f'page {page["page"]}: the plate for "{event["to_state"]}" holds two sub-changes timed on different words: '
                                     f'"{event["word"]}" changes {", ".join(declared)}, but {", ".join(f"{f} (on \"{w}\")" for f, w in later.items())} '
                                     f'change later. Draw a plate "{derived}" = "{current_name}" with only {", ".join(declared)} changed '
                                     f'(round 4: the slowed plate held both the windows and the men).',
                     page=page['page'], word=event['word'], fields_now=declared, fields_later=later, plate_needed=derived)
                add_plate(view, derived, reached, f'page {page["page"]} "{event["word"]}": {", ".join(declared)} only')
                name = derived
            else:
                if bundled:
                    note(found, 'warning', f'page {page["page"]} "{event["word"]}": "{event["to_state"]}" also changes {", ".join(bundled)}, '
                                           f'which no word announces (they change silently with "{event["word"]}")', page=page['page'], word=event['word'])
                    for f in bundled:
                        reached[f] = target[f]
                name = event['to_state']
                add_plate(view, name, reached, f'page {page["page"]} "{event["word"]}"')
            all_changed = declared + (bundled if not later else [])
            only_people = bool(all_changed) and all(people_field(f, settings) for f in all_changed)
            changes.append({'page': page['page'], 'view': view, 'word': event['word'], 'time': event['time'], 'from_state': current_name,
                            'to_state': name, 'fields': all_changed, 'only_people': only_people, 'cue_points': event.get('cue_points'),
                            'cue_radius_metres': event.get('cue_radius_metres', 0.0), 'outlines': event.get('outlines')})
            current, current_name = reached, name
    return plates, changes


def slide_near_things(place, view, settings):
    """The figures and props the view's slide moves past by more than the parallax limit (frame_geometry's sums, with the
    set assumed behind_gap_metres behind each)."""
    if not view.get('slide'):
        return {}
    camera = geometry.camera_from_place_facts(place, settings, view['name'], 'plate', 'film')
    start, end = view['slide']['start'], view['slide']['end']
    step = geometry.subtract(end, start)
    forward = geometry.dot(step, camera['forward'])
    sideways = math.hypot(geometry.dot(step, camera['right']), geometry.dot(step, camera['up']))
    gap = settings.value('painting_tools.plan_states.behind_gap_metres')
    fov, rows = settings.value('frame.film_vertical_fov_degrees'), settings.value('frame.height_pixels')
    found = {}
    things = [(f['name'], [f['feet'][0], f['feet'][1], f['feet'][2] + 0.5 * f['height_metres']], f.get('group')) for f in place.get('figures', [])]
    things += [(p['name'], p['at'], 'prop') for p in place.get('props', [])]
    for name, point, group in things:
        landed = geometry.project_point(camera, point)
        if not geometry.in_frame(landed) or landed['depth'] <= forward + 0.1:
            continue
        offset = math.hypot(landed['x_pixels'] - camera['frame'][0] / 2, landed['y_pixels'] - camera['frame'][1] / 2)
        pixels = geometry.parallax_forward_pixels(offset, forward, landed['depth'], landed['depth'] + gap) if forward > 0 else 0.0
        pixels += geometry.parallax_sideways_pixels(sideways, landed['depth'], landed['depth'] + gap, fov, rows) if sideways > 0 else 0.0
        found[name] = {'pixels': round(pixels, 2), 'group': group}
    return found


def present(group, state, plan):
    """Is a place-facts figure group in this state? (the plan's "people_fields" names the state field that holds it)"""
    field = plan.get('people_fields', {}).get(group)
    return True if field is None else bool(state.get(field))


def behind_plates(plan, place, plates, settings, found):
    """For each view with a slide: the behind plate is the view's main state with the near people left out (people the
    slide moves past by more than the figures' parallax limit); name the place's state that is exactly that, and flag a
    behind picture taken from another state. Near props over the props' limit are listed for the behind painting."""
    states = place.get('states', {})
    views = {v['name']: v for v in place['views']}
    prop_limit = settings.value('painting_tools.plan_states.near_parallax_pixels')
    figure_limit = settings.value('painting_tools.plan_states.near_parallax_pixels_figures')
    out = []
    for page in plan['pages']:
        view = views.get(page['view'])
        if not view or not view.get('slide') or not page.get('slides'):
            continue
        main = states[page['start_state']]
        near = slide_near_things(place, view, settings)
        people = {n: v for n, v in near.items() if v['group'] not in (None, 'prop') and present(v['group'], main, plan) and v['pixels'] > figure_limit}
        props = {n: v['pixels'] for n, v in near.items() if v['group'] == 'prop' and v['pixels'] > prop_limit}
        groups = sorted({v['group'] for v in people.values()})
        fields = [plan.get('people_fields', {}).get(g) for g in groups]
        chosen = None
        if groups and all(fields):
            for name, state in states.items():
                differ = [f for f in state if f != 'about' and state.get(f) != main.get(f)]
                if sorted(differ) == sorted(set(fields)) and all(not state[f] for f in differ):
                    chosen = (name, differ)
                    break
        entry = {'view': page['view'], 'page': page['page'], 'main_state': page['start_state'], 'near_people_groups': groups,
                 'near_people_pixels': {n: v['pixels'] for n, v in sorted(people.items(), key=lambda kv: -kv[1]['pixels'])},
                 'near_props_pixels': props, 'behind_state': chosen[0] if chosen else None, 'hides_fields': chosen[1] if chosen else None}
        out.append(entry)
        if chosen and (page['view'], chosen[0]) not in {(p['view'], p['state']) for p in plates}:
            plates.append({'view': page['view'], 'state': chosen[0], 'fields': states[chosen[0]], 'why': f'page {page["page"]}: the behind plate for the slide'})
        if groups and not chosen:
            note(found, 'error', f'page {page["page"]} ({page["view"]}): the slide moves past {", ".join(groups)}, but no state of the place is '
                                 f'"{page["start_state"]}" without them: add one for the behind plate', page=page['page'])
        given = page.get('behind_state')
        if given and chosen and given != chosen[0]:
            other = states.get(given, {})
            wrong = [f for f in other if f != 'about' and other.get(f) != states[chosen[0]].get(f)]
            note(found, 'error', f'page {page["page"]}: the behind picture comes from "{given}", which differs from the main state in '
                                 f'{", ".join(wrong)}: those would show round the near things as soon as the slide starts (round 3: No. 1\'s '
                                 f'doorway lit from "Workers"). Use "{chosen[0]}".', page=page['page'], fields=wrong)
    return out


def cue_check(change, place, settings):
    """How much of the changing cue lands in the frame below the words band, at the view's composed spot."""
    if not change.get('cue_points'):
        return None
    camera = geometry.camera_from_place_facts(place, settings, change['view'], 'composed', 'film')
    radius = change.get('cue_radius_metres') or 0.0
    points = []
    for p in change['cue_points']:
        for dx in (-radius, radius):
            for dz in (-radius, radius):
                points.append([p[0] + dx, p[1], p[2] + dz])
    landed = geometry.project_box(camera, points)
    if not landed['box']:
        return {'inside_share': 0.0, 'box': None}
    left, top, right, bottom = landed['box']
    band = settings.value('safe_area.title_band_down')[1]
    area = max(1e-9, (right - left) * (bottom - top))
    inside = max(0.0, min(right, 1) - max(left, 0)) * max(0.0, min(bottom, 1) - max(top, band))
    return {'inside_share': inside / area, 'box': [round(v, 3) for v in landed['box']]}


def busy_check(plates, place, settings, found):
    """A state described as busy needs someone seen at work, with a head small enough that no face shows."""
    states = place.get('states', {})
    words = settings.value('painting_tools.plan_states.busy_words')
    limit = settings.value('people.facing_head_max_pixels')
    head = settings.value('people.head_height_metres')
    views = {v['name']: v for v in place['views']}
    workers = [f for f in place.get('figures', []) if 'work' in (f.get('group') or '').lower()]
    out = []
    for p in plates:
        state = states.get(p['state'].split(' (only')[0], {})
        about = (state.get('about') or '').lower()
        if not any(w in about for w in words) or p['view'] not in views:
            continue
        at_work = sum(v for f, v in p['fields'].items() if 'worker' in f.lower() and isinstance(v, (int, float)))
        camera = geometry.camera_from_place_facts(place, settings, p['view'], 'composed', 'film')
        heads = {}
        for f in workers:
            top = [f['feet'][0], f['feet'][1], f['feet'][2] + f['height_metres'] - head / 2]
            landed = geometry.project_point(camera, top)
            if geometry.in_frame(landed):
                heads[f['name']] = round(geometry.size_in_pixels(camera, head, landed['depth']), 1)
        big = {n: v for n, v in heads.items() if v > limit}
        entry = {'view': p['view'], 'state': p['state'], 'people_at_work': at_work, 'worker_heads_pixels': heads}
        out.append(entry)
        if not at_work:
            note(found, 'warning', f'{p["view"]} "{p["state"]}" is described as busy, but nobody is seen at work (round 4: a flat-out factory with '
                                   f'nobody at work read as "open late or deserted")', view=p['view'], state=p['state'])
        if big:
            note(found, 'warning', f'{p["view"]}: workers {", ".join(big)} have heads over {limit} px ({", ".join(f"{v:.0f}" for v in big.values())}): '
                                   f'turn them away or move them back so no face shows', view=p['view'])
    return out


# ------------------------------------------------------------------------------------------------ measuring the plates
def smooth_noise(plate_path, helper_path):
    """The 99th percentile of the plates' heavily blurred difference (10 px, largest channel) in the quarter of the frame
    furthest from where they differ: the noise the faint threshold must stay clear of."""
    a, b = cv2.imread(plate_path).astype(np.float32), cv2.imread(helper_path).astype(np.float32)
    unit = a.shape[1] / 1536
    fine = np.abs(cv2.GaussianBlur(a, (0, 0), 2 * unit) - cv2.GaussianBlur(b, (0, 0), 2 * unit)).max(axis=2)
    smooth = np.abs(cv2.GaussianBlur(a, (0, 0), 10 * unit) - cv2.GaussianBlur(b, (0, 0), 10 * unit)).max(axis=2)
    changed = (fine > 6) | (smooth > 3)
    distance = cv2.distanceTransform((~changed).astype(np.uint8), cv2.DIST_L2, 5)
    far = distance >= np.percentile(distance, 75)
    return float(np.percentile(smooth[far], 99)) if far.any() else 0.0


def measure_pairs(plan, changes, behinds, settings, work, found):
    """make_state_picture.py on each change's two plates (the free test) and on each behind pair: swap share, noise."""
    folder = plan.get('plate_folder', '')
    plates = plan.get('plates', {})
    path = lambda view, state: os.path.join(folder, plates[f'{view}/{state}']) if f'{view}/{state}' in plates else None
    pairs = [(c['view'], c['from_state'], c['to_state'], c) for c in changes] + \
            [(b['view'], b['main_state'], b['behind_state'], b) for b in behinds if b.get('behind_state')]
    for view, before, after, target in pairs:
        a, b = path(view, before), path(view, after)
        if not (a and b and os.path.exists(a) and os.path.exists(b)):
            target['measured'] = None
            continue
        facts = plan.get('facts_folders', {}).get(view)
        groups = target.get('outlines') or []
        shares = measures.state_mask_shares(a, b, a, b, work, facts if groups else None, groups)
        shares['smooth_noise_levels'] = smooth_noise(a, b)
        target['measured'] = shares


def judge_changes(changes, settings, found):
    cut_max = settings.value('painting_tools.plan_states.cut_when_change_share_max')
    flag = settings.value('state_pictures.flag_mask_share')
    blend = settings.value('state_pictures.stepped_blend')
    ratio_max = settings.value('painting_tools.plan_states.come_and_go_mask_over_outline_max')
    for c in changes:
        m = c.get('measured')
        share = m['mask_share'] if m else None
        if share is None:
            c['how'] = 'not measured: give the plates and --measure'
        elif share <= cut_max:
            c['how'] = f'time cut on "{c["word"]}" ({c["time"]} s)'
        else:
            c['how'] = f'stepped blend from "{c["word"]}" ({c["time"]} s): {blend["seconds"]} s in {blend["steps"]} steps'
        c['share'] = share
        if c['only_people']:
            note(found, 'warning', f'page {c["page"]} "{c["word"]}": only people change ({", ".join(c["fields"])}); a time cut of people alone reads '
                                   f'as a glitch (lesson 136). Change something else in the same frame: the light, the fire, a door, the people '
                                   f'seen elsewhere.', page=c['page'], word=c['word'])
        if m and share > flag:
            note(found, 'warning' if not c['only_people'] else 'error',
                 f'page {c["page"]} "{c["word"]}" swaps {share:.1%} of the frame (over {flag:.0%}): every brushstroke there changes at once '
                 f'once the paintings come', page=c['page'], word=c['word'], share=share)
        if m and c['only_people'] and m['outline_share'] > 0 and share / m['outline_share'] > ratio_max:
            c['how'] = f'fix the long shadows first (below); people alone should then swap little more than their outlines: a time cut on "{c["word"]}"'
            note(found, 'error', f'page {c["page"]} "{c["word"]}": the swap is {share / m["outline_share"]:.1f} times the people\'s own outlines '
                                 f'(limit {ratio_max:g}): they cast long shadows or block light (people test: 42% of the frame for people covering '
                                 f'7.5%). Draw them with no long shadows, only a soft patch at their feet.', page=c['page'], word=c['word'])


def thresholds(changes, behinds, settings):
    low, faint_low = settings.value('state_pictures.threshold_levels'), settings.value('state_pictures.faint_levels')
    factor = settings.value('state_pictures.noise_factor_min')
    found = {}
    for target in changes + behinds:
        m = target.get('measured')
        if not m:
            continue
        key = f'{target["view"]}: {target.get("from_state", target.get("main_state"))} to {target.get("to_state", target.get("behind_state"))}'
        found[key] = {'threshold': max(low, factor * (m['noise_levels'] or 0)), 'faint': max(faint_low, factor * m['smooth_noise_levels']),
                      'noise_levels': m['noise_levels'], 'smooth_noise_levels': m['smooth_noise_levels']}
    return found


def commands(plan, changes, behinds, chosen):
    """The exact commands for each state picture and behind picture."""
    folder = plan.get('plate_folder', '.')
    plates = plan.get('plates', {})
    lines = []
    for c in changes:
        main = plates.get(f'{c["view"]}/{plan_main_state(plan, c["view"])}', f'{c["view"]}-plate.png')
        helper = plates.get(f'{c["view"]}/{c["to_state"]}', f'<plate of {c["view"]} "{c["to_state"]}">')
        out = f'{c["view"]}-{c["to_state"].replace(" ", "-").replace(",", "").replace("(", "").replace(")", "")}-state.png'
        t = chosen.get(f'{c["view"]}: {c["from_state"]} to {c["to_state"]}', {'threshold': 6, 'faint': 3})
        groups = ' '.join(f'"{g}"' for g in (c.get('outlines') or []))
        facts = plan.get('facts_folders', {}).get(c['view'], 'PLATE_FACTS')
        lines.append(f'python3 -I {TOOL}/make_state_picture.py MAIN_PAINTING SECOND_PAINTING {os.path.join(folder, main)} {os.path.join(folder, helper)} '
                     f'{out} {out.replace("-state.png", "-mask.png")}' + (f' --outlines {facts} {groups}' if groups else '') +
                     f' --threshold {t["threshold"]:g} --faint {t["faint"]:g} --look {out.replace(".png", "-look.jpg")}')
    for b in behinds:
        if b.get('behind_state'):
            main = plates.get(f'{b["view"]}/{b["main_state"]}', f'{b["view"]}-plate.png')
            helper = plates.get(f'{b["view"]}/{b["behind_state"]}')
            facts = plan.get('facts_folders', {}).get(b['view'], 'PLATE_FACTS')
            groups = ' '.join(f'"{g}"' for g in b.get('outline_groups', []))
            if helper:
                lines.append(f'python3 -I {TOOL}/make_state_picture.py MAIN_PAINTING MAIN_PAINTING {os.path.join(folder, main)} {os.path.join(folder, helper)} '
                             f'{b["view"]}-behind.png {b["view"]}-behind-mask.png' + (f' --outlines {facts} {groups}' if groups else '') + ' --threshold 6 --faint 3')
            lines.append(f'(free, once the painting comes) python3 -I {TOOL}/make_behind_picture.py MAIN_PAINTING {b["view"]}-behind.png '
                         f'--outlines {facts} {groups or "NEAR_GROUPS"} --widen 10 --radius 9')
    return lines


def plan_main_state(plan, view):
    for page in plan['pages']:
        if page['view'] == view:
            return page['start_state']
    return None


# ------------------------------------------------------------------------------------------------ the command
def command_plan(args, settings):
    plan = measures.load_json(args.plan)
    if args.plate_folder:
        plan['plate_folder'] = args.plate_folder
    for given in args.facts_folder or []:
        view, _, folder = given.partition('=')
        plan.setdefault('facts_folders', {})[view] = folder
    base = os.path.dirname(os.path.abspath(args.plan))
    place_path = plan['place_facts'] if os.path.isabs(plan['place_facts']) else os.path.join(base, plan['place_facts'])
    place = measures.load_json(place_path)
    if plan.get('states'):   # a place whose facts have no states table: the plan gives them
        place.setdefault('states', {}).update(plan['states'])
    found = []
    plates, changes = walk_changes(plan, place, settings, found)
    behinds = behind_plates(plan, place, plates, settings, found)
    for b in behinds:
        groups = []
        for field in (b.get('hides_fields') or []):
            groups += plan.get('field_groups', {}).get(field, [])
        b['outline_groups'] = groups
    for c in changes:
        if not c.get('outlines'):
            groups = []
            for field in c['fields']:
                groups += plan.get('field_groups', {}).get(field, [])
            c['outlines'] = groups
    for c in changes:
        cue = cue_check(c, place, settings)
        c['cue'] = cue
        least = settings.value('painting_tools.plan_states.cue_inside_share_min')
        if cue is not None and cue['inside_share'] < least:
            note(found, 'warning', f'page {c["page"]} "{c["word"]}": only {cue["inside_share"]:.0%} of the changing cue lands in the frame below the '
                                   f'words band (needs {least:.0%}; round 3: No. 2\'s windows were out of W2\'s frame)', page=c['page'], word=c['word'], box=cue['box'])
    busy = busy_check(plates, place, settings, found)
    if args.measure:
        work = os.path.join(args.work_folder, 'plan-states-trial') if args.work_folder else tempfile.mkdtemp(prefix='plan-states-trial-')
        try:
            measure_pairs(plan, changes, behinds, settings, work, found)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    judge_changes(changes, settings, found)
    chosen = thresholds(changes, behinds, settings)
    lines_of_commands = commands(plan, changes, behinds, chosen)
    errors = [f for f in found if f['kind'] == 'error']
    lines = [f'State picture plan: {os.path.basename(args.plan)} ({len(errors)} error(s), {len(found) - len(errors)} warning(s))', '', 'Plates:']
    for p in plates:
        lines.append(f'  - {p["view"]} "{p["state"]}": {p["why"]}')
    lines += ['', 'Changes:']
    for c in changes:
        share = f'{c["share"]:.1%} of the frame' if c.get('share') is not None else 'share not measured'
        lines.append(f'  - page {c["page"]} {c["view"]} "{c["word"]}" ({c["time"]} s): {c["from_state"]} -> {c["to_state"]}; {share}; {c["how"]}'
                     + (f'; cue {c["cue"]["inside_share"]:.0%} in frame' if c.get('cue') else ''))
    for b in behinds:
        m = b.get('measured')
        if b['behind_state']:
            lines.append(f'  - page {b["page"]} {b["view"]} behind plate: "{b["behind_state"]}" (the main "{b["main_state"]}" without '
                         f'{", ".join(b["near_people_groups"])})' + (f'; swaps {m["mask_share"]:.1%}' if m else ''))
        else:
            lines.append(f'  - page {b["page"]} {b["view"]}: no people near the slide; no behind plate needed for people')
        if b['near_props_pixels']:
            lines.append(f'    near props for the behind painting (over the parallax limit): ' + ', '.join(f'{n} {v:.1f} px' for n, v in b['near_props_pixels'].items()))
    if busy:
        lines += ['', 'Busy states:'] + [f'  - {b["view"]} "{b["state"]}": {b["people_at_work"]} at work; worker heads '
                                         f'{", ".join(f"{v:.0f}" for v in b["worker_heads_pixels"].values()) or "none in frame"} px' for b in busy]
    if chosen:
        lines += ['', 'Thresholds from the measured noise:'] + [f'  - {k}: threshold {v["threshold"]:g}, faint {v["faint"]:g} (noise {v["noise_levels"]}, '
                                                                f'smooth noise {v["smooth_noise_levels"]:.2f})' for k, v in chosen.items()]
    lines += ['', 'Errors and warnings:'] + ([f'  - {f["kind"].upper()}: {f["what"]}' for f in found] or ['  - none'])
    lines += ['', 'Commands (PNG only; each checks the picture equals the main painting outside its mask):'] + [f'  {l}' for l in lines_of_commands]
    result = {'plates': [{k: v for k, v in p.items() if k != 'fields'} for p in plates], 'changes': changes, 'behind_plates': behinds,
              'busy_states': busy, 'thresholds': chosen, 'commands': lines_of_commands, 'problems': found, 'errors': len(errors)}
    if args.out_folder:
        os.makedirs(args.out_folder, exist_ok=True)
        with open(os.path.join(args.out_folder, 'state-plan.json'), 'w') as handle:
            json.dump(measures.round_all(result), handle, indent=1)
    return measures.round_all(result), lines, 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Plans the helper plates and state pictures of held shots (see the note at the top).')
    commands_parser = parser.add_subparsers(dest='command', required=True)
    p = commands_parser.add_parser('plan', help='plan the plates, cuts and blends of a page plan')
    p.add_argument('--plan', required=True, help='the page plan of state changes (JSON)')
    p.add_argument('--measure', action='store_true', help='measure the swap and noise on the plates the plan names (make_state_picture.py)')
    p.add_argument('--work-folder', help='where the measuring trial writes (and deletes) its pictures')
    p.add_argument('--out-folder', help='write state-plan.json here')
    p.add_argument('--plate-folder', help='the folder of the plates the plan names (instead of the plan\'s "plate_folder")')
    p.add_argument('--facts-folder', nargs='*', help='VIEW=FOLDER: shot_facts.py\'s folder for that view\'s PLATE camera (for the outlines)')
    add_output_options(p)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    result, lines, code = command_plan(args, settings)
    finish(f'plan_states {args.command}', result, lines, settings, args)
    return code


if __name__ == '__main__':
    sys.exit(run_main(main, 'plan_states'))
