"""What this does: for every view of a place, works out before anything is painted what this project found by looking,
round after round (logs 29-34):
  - how tall every sign's letters come out on the phone frame, from the camera and the sign's facing. Turning a board
    sideways narrows its letters; only tipping it toward or away from the camera (an envelope lying flat) shortens
    them, so height comes from the up-and-down part of the view and width from the across part (skeptic, log 35).
    Words the page needs fail under 20 px and warn under 25 px, with the letter height that would reach them;
  - the turn that faces a drum's curved stencil to every camera that reads it (the best compromise across views);
  - a readable sign the page never names that is louder than the words it does name (BANK in W3, rounds 3-4), with
    the dim that would quieten it; loudness is letter pixels times letter brightness;
  - the back of a sign showing in a view (round 4: No. 2's board was a blank plank from inside its yard);
  - tall landmarks (chimney tops) whose tops sit in or just under the band kept for typed words, and the height that
    would clear it;
  - each figure's head size and whether its face can show, how near it stands, and whether it is in the frame;
  - how many figures of each group every view shows in every state (continuity: 7, 7, 0, 0, 8, 8 at the Works);
  - with a still and a word's box: the contrast behind a typed title and the dark band it needs (title-contrast).
It reads a place facts file (kit/calculators/place_facts_schema.json) and the camera sums of frame_geometry.py.

Use:
  python3 view_audit.py audit --place-facts PLACE.json [--view w1 --view w3] [--named "no-1 board,no-2 board"]
        [--timeline timeline.json --page 3] [--levels levels.json] [--figure-states "men at No. 1=men_1,..."]
        [--count-groups "men at No. 1,men at No. 2"] [--expect-counts "w3/quiet=7,w1/quiet=7"]
  python3 view_audit.py title-contrast --still FRAME.png --box 0.06,0.05,0.90,0.22 --text-colour ffffff
--named     the signs the page says aloud (their words are needed); with --timeline and --page, signs whose words the
            page's narration says are added. Without either, every must-read sign counts as needed and the loud-sign
            check is skipped (it needs to know what the page names).
--levels    letter brightness (0-255) per view and sign as measured on a still: {"w3": {"bank sign": 118}}; a number
            is the lit level (the sign's dim_until_named is then applied), {"filmed": 52} is the level as filmed
--figure-states  which state flag shows a figure group ("men at No. 1=men_1"); without it every figure counts in
            every state, unless the figure lists "shown_in"
Every command takes --json, --out FILE, --report FILE and --settings FILE, and names the film-settings.json values it
used. Exit 1 when a needed word fails or a sign that must be read shows its back; 0 otherwise.
"""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import frame_geometry as geometry  # noqa: E402
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402

SECTION = 'views_and_models.view_audit'


# ------------------------------------------------------------------------------------------------ cameras of a view
def view_spots(view):
    """The spots a view is seen from: the plate spot (the slide's start) and the composed spot (its end); a view that
    holds still has one. The composed spot is where words must read (the end frame of the move)."""
    camera = view['camera']
    spots = []
    if camera.get('plate') is not None:
        spots.append('plate')
    if camera.get('composed') is not None and camera.get('composed') != camera.get('plate'):
        spots.append('composed')
    return spots or ['composed']


def reading_spot(view):
    return 'composed' if view['camera'].get('composed') is not None else 'plate'


def film_camera(facts, settings, view, spot):
    return geometry.camera_from_place_facts(facts, settings, view['name'], spot, 'film')


def in_frame(landed):
    return bool(landed['in_front'] and 0 <= landed['across'] <= 1 and 0 <= landed['down'] <= 1)


def pixel_distance(camera, a, b):
    pa, pb = geometry.project_point(camera, a), geometry.project_point(camera, b)
    if not (pa['in_front'] and pb['in_front']):
        return None
    return math.hypot(pa['x_pixels'] - pb['x_pixels'], pa['y_pixels'] - pb['y_pixels'])


# ------------------------------------------------------------------------------------------------ lettering
def letter_axes(sign, camera):
    """The letters' up and right directions on the sign. An upright sign's letters stand along z; a sign lying flat
    (its face up) is read with the letters' tops pointing away from the viewer, unless the sign gives "letters_up"."""
    n = geometry.normalise(sign['normal'])
    if sign.get('letters_up'):
        up = geometry.normalise(sign['letters_up'])
    elif abs(n[2]) < 0.95:
        z = [0.0, 0.0, 1.0]
        up = geometry.normalise(geometry.subtract(z, geometry.scale(n, geometry.dot(z, n))))
    else:
        away = geometry.subtract(sign['centre'], camera['position'])
        away = geometry.subtract(away, geometry.scale(n, geometry.dot(away, n)))
        up = geometry.normalise(away) if geometry.length(away) > 1e-9 else geometry.normalise(geometry.cross(n, [1.0, 0, 0]))
    right = geometry.normalise(geometry.cross(up, n))
    return n, up, right


def letter_measure(sign, camera):
    """The sign's letters as seen from one camera: height and width in pixels (exact projection of a letter-sized
    upright and across segment at the sign's middle), the face-on size at that depth, and the facing."""
    centre = sign['centre']
    landed = geometry.project_point(camera, centre)
    to_camera = geometry.normalise(geometry.subtract(camera['position'], centre))
    n, up, right = letter_axes(sign, camera)
    facing = geometry.dot(n, to_camera)
    flat_n = [n[0], n[1], 0.0]
    flat_to = [to_camera[0], to_camera[1], 0.0]
    across_facing = (geometry.dot(geometry.normalise(flat_n), geometry.normalise(flat_to))
                     if geometry.length(flat_n) > 1e-9 and geometry.length(flat_to) > 1e-9 else None)
    result = {'across': landed['across'], 'down': landed['down'], 'depth': landed['depth'], 'in_front': landed['in_front'],
              'in_frame': in_frame(landed), 'distance': geometry.length(geometry.subtract(centre, camera['position'])),
              'facing': facing, 'across_facing': across_facing, 'back_shows': facing < 0}
    height = sign.get('letter_height_metres')
    if height is None or not landed['in_front']:
        result.update({'letter_pixels': None, 'letter_width_pixels': None, 'face_on_pixels': None})
        return result
    half = height / 2
    tall = pixel_distance(camera, geometry.add(centre, geometry.scale(up, -half)), geometry.add(centre, geometry.scale(up, half)))
    wide = pixel_distance(camera, geometry.add(centre, geometry.scale(right, -half)), geometry.add(centre, geometry.scale(right, half)))
    face_on = geometry.size_in_pixels(camera, height, landed['depth'])
    result.update({'letter_pixels': tall, 'letter_width_pixels': wide, 'face_on_pixels': face_on,
                   'height_factor': tall / face_on if tall is not None else None,
                   'width_factor': wide / face_on if wide is not None else None})
    return result


def needed_height(sign, measure, pixels):
    """Letter height (metres) that comes out `pixels` tall from this camera, keeping the sign's facing."""
    if not measure.get('letter_pixels'):
        return None
    return sign['letter_height_metres'] * pixels / measure['letter_pixels']


def words_of(text):
    return [w for w in re.findall(r"[a-z0-9]+", (text or '').lower()) if w]


def said_in(sign, narration_words):
    """Whether the narration says the sign's words (plurals count: 'banks' names BANK)."""
    wanted = [w for w in words_of(sign.get('words')) if len(w) > 2 or w.isdigit()]
    if not wanted:
        return False
    said = set(narration_words) | {w[:-1] for w in narration_words if w.endswith('s')}
    return all(w in said for w in wanted)


# ------------------------------------------------------------------------------------------------ the audit
def audit(facts, settings, views=None, named=None, narration_words=None, levels=None, figure_states=None, count_groups=None,
          expect_counts=None):
    floor_pixels = settings.value('lettering.must_read_min_pixels')
    comfortable = settings.value('lettering.must_read_comfortable_pixels')
    quiet_pixels = settings.value('lettering.not_meant_to_read_max_pixels')
    facing_min = settings.value(f'{SECTION}.must_read_facing_min_cos')
    result = {'place': facts.get('place'), 'views': {}, 'stencil_turns': [], 'loud_signs': [], 'landmarks': [], 'figures': [],
              'continuity': {}, 'problems': [], 'warnings': [], 'notes': []}
    chosen = [v for v in facts['views'] if not views or v['name'] in views]
    if views:
        missing = sorted(set(views) - {v['name'] for v in chosen})
        if missing:
            raise SystemExit(f'view_audit: no view {", ".join(missing)} in the place facts (views: {", ".join(v["name"] for v in facts["views"])})')
    page_known = named is not None or narration_words is not None
    named = set(named or [])
    if narration_words is not None:
        named |= {s['name'] for s in facts['signs'] if said_in(s, narration_words)}
    unknown = sorted(named - {s['name'] for s in facts['signs']})
    if unknown:
        raise SystemExit(f'view_audit: --named gives sign(s) not in the place facts: {", ".join(unknown)} '
                         f'(signs: {", ".join(s["name"] for s in facts["signs"])})')

    # 1. lettering, per view and spot
    for view in chosen:
        entry = {'kind_of_shot': view.get('kind_of_shot'), 'reading_spot': reading_spot(view), 'signs': {}}
        for spot in view_spots(view):
            camera = film_camera(facts, settings, view, spot)
            for sign in facts['signs']:
                measure = letter_measure(sign, camera)
                entry['signs'].setdefault(sign['name'], {})[spot] = measure
        result['views'][view['name']] = entry
        spot = entry['reading_spot']
        for sign in facts['signs']:
            measure = entry['signs'][sign['name']][spot]
            if not measure['in_frame']:
                continue
            needed = sign.get('must_read', False) and (sign['name'] in named if page_known else True)
            measure['needed_by_page'] = needed
            where = f'{view["name"]} ({spot} spot)'
            px = measure['letter_pixels']
            if measure['back_shows'] and sign.get('wraps_degrees') is not None:
                measure['verdict'] = 'seen from behind (a drum: nothing to read on its back)'
                continue
            if measure['back_shows'] and not sign.get('both_faces'):
                measure['verdict'] = 'back shows'
                if needed or (px is not None and px > quiet_pixels):
                    text = (f'{sign["name"]} ("{sign["words"]}") shows its back in {where}, as big as {px:.0f} px letters would be: '
                            f'a blank plank on screen (round 4, W4). Letter its back too, or turn it.')
                    (result['problems'] if needed else result['warnings']).append(text)
                continue
            if px is None:
                measure['verdict'] = 'letter height not known'
                result['notes'].append(f'{sign["name"]} in {where}: its letter height is not in the place facts; not judged.')
                continue
            if needed:
                if px < floor_pixels:
                    measure['verdict'] = 'too small'
                    result['problems'].append(
                        f'{sign["name"]} ("{sign["words"]}") in {where}: letters {px:.1f} px tall, under {floor_pixels} px. Make the '
                        f'letters {needed_height(sign, measure, floor_pixels):.3f} m tall for {floor_pixels} px '
                        f'({needed_height(sign, measure, comfortable):.3f} m for {comfortable} px), bring it nearer, or let a typed '
                        f'label carry the word.')
                elif px < comfortable:
                    measure['verdict'] = 'readable, small'
                    result['warnings'].append(
                        f'{sign["name"]} ("{sign["words"]}") in {where}: letters {px:.1f} px, between {floor_pixels} and {comfortable} px '
                        f'(PETROL and DIESEL read at 22 px in round 4). {needed_height(sign, measure, comfortable):.3f} m letters '
                        f'would give {comfortable} px.')
                else:
                    measure['verdict'] = 'readable'
                if measure['across_facing'] is not None and measure['across_facing'] < facing_min and sign.get('wraps_degrees') is None:
                    result['warnings'].append(
                        f'{sign["name"]} in {where}: turned {math.degrees(math.acos(max(-1, min(1, measure["across_facing"])))):.0f} degrees '
                        f'from the camera; its letters are {100 * measure["width_factor"]:.0f}% of their width. Turn it to face the camera.')
            else:
                measure['verdict'] = 'legible' if px > quiet_pixels else 'too small to read'

    # 2. curved stencils (drums): the turn facing every camera that reads them
    for sign in facts['signs']:
        wrap = sign.get('wraps_degrees')
        if wrap is None:
            continue
        n = sign['normal']
        current = math.degrees(math.atan2(n[0], -n[1]))
        ideal = []
        for view in chosen:
            for spot in view_spots(view):
                measure = result['views'][view['name']]['signs'][sign['name']][spot]
                if not measure['in_frame'] or measure['facing'] <= 0:
                    continue
                camera = film_camera(facts, settings, view, spot)
                cx, cy = camera['position'][0], camera['position'][1]
                x, y = sign['centre'][0], sign['centre'][1]
                ideal.append({'view': view['name'], 'spot': spot, 'turn_degrees': math.degrees(math.atan2(cx - x, -(cy - y)))})
        if not ideal:
            continue
        turns = [i['turn_degrees'] for i in ideal]
        best = (min(turns) + max(turns)) / 2
        worst_now = max(abs(t - current) for t in turns)
        worst_best = max(abs(t - best) for t in turns)
        record = {'sign': sign['name'], 'words': sign['words'], 'current_turn_degrees': current, 'best_turn_degrees': best,
                  'per_view': ideal, 'worst_offset_now_degrees': worst_now, 'worst_offset_best_degrees': worst_best,
                  'end_letter_angle_now_degrees': worst_now + wrap, 'end_letter_angle_best_degrees': worst_best + wrap}
        result['stencil_turns'].append(record)
        if worst_now + wrap >= 90:
            result['problems'].append(f'{sign["name"]} ("{sign["words"]}"): its end letters turn edge-on to a camera '
                                      f'({worst_now + wrap:.0f} degrees); turn it to {best:.1f} degrees.')

    # 3. loud signs the page does not name
    if not page_known:
        result['notes'].append('Loud unnamed signs: not checked (give --named or --timeline with --page: the check needs what the page says).')
    else:
        limit = settings.value(f'{SECTION}.unnamed_sign_legibility_share_max')
        exponent = settings.value(f'{SECTION}.dim_brightness_exponent')
        for view in chosen:
            entry = result['views'][view['name']]
            spot = entry['reading_spot']
            view_levels = (levels or {}).get(view['name'], levels or {})

            def loudness(sign, apply_dim):
                measure = entry['signs'][sign['name']][spot]
                level = view_levels.get(sign['name']) if isinstance(view_levels, dict) else None
                if isinstance(level, dict):
                    if 'filmed' in level:
                        return measure['letter_pixels'] * level['filmed'], level['filmed'], 'as filmed'
                    level = level.get('lit')
                if level is None:
                    return measure['letter_pixels'], None, 'pixels only'
                if apply_dim and sign.get('dim_until_named') is not None:
                    dimmed = level * sign['dim_until_named'] ** exponent
                    return measure['letter_pixels'] * dimmed, dimmed, f'dimmed to {sign["dim_until_named"]} (predicted {dimmed:.0f} levels)'
                return measure['letter_pixels'] * level, level, 'lit'
            shown = [s for s in facts['signs'] if entry['signs'][s['name']][spot]['in_frame']
                     and entry['signs'][s['name']][spot].get('letter_pixels') and not entry['signs'][s['name']][spot]['back_shows']]
            spoken = [s for s in shown if s['name'] in named and entry['signs'][s['name']][spot]['letter_pixels'] > quiet_pixels]
            if not spoken:
                if any(s['name'] not in named for s in shown):
                    result['notes'].append(f'{view["name"]}: no sign the page names is readable in the frame; loud signs not compared.')
                continue
            reference_sign = min(spoken, key=lambda s: loudness(s, False)[0])
            reference, reference_level, _ = loudness(reference_sign, False)
            for sign in shown:
                measure = entry['signs'][sign['name']][spot]
                if sign['name'] in named or measure['letter_pixels'] <= quiet_pixels:
                    continue
                lit_loud, lit_level, lit_how = loudness(sign, False)
                loud, level, how = loudness(sign, True)
                share = loud / reference
                record = {'view': view['name'], 'sign': sign['name'], 'words': sign['words'], 'letter_pixels': measure['letter_pixels'],
                          'levels': level, 'how': how, 'share_of_least_named': share, 'lit_share': lit_loud / reference,
                          'least_named': reference_sign['name'], 'limit': limit}
                if share > limit:
                    if lit_level is not None and lit_how != 'as filmed':
                        target_level = limit * reference / measure['letter_pixels']
                        dim = (target_level / lit_level) ** (1 / exponent)
                    elif lit_how == 'pixels only':
                        dim = (limit * reference / measure['letter_pixels']) ** (1 / exponent)
                    else:
                        dim = None
                    record['dim_needed'] = dim
                    record['verdict'] = 'too loud'
                    dim_text = f'dim it to {dim:.2f} of its lit brightness until the page names it' if dim is not None else 'dim it more'
                    result['problems'].append(
                        f'{sign["name"]} ("{sign["words"]}") in {view["name"]}: the page never says it, yet it reads at {share:.2f} of '
                        f'{reference_sign["name"]} (letters {measure["letter_pixels"]:.1f} px, {how}; the limit is {limit}). '
                        f'Viewers read the clearest word first (BANK, rounds 3-4): {dim_text}, or take it out of the frame.')
                else:
                    record['verdict'] = 'quiet enough'
                result['loud_signs'].append(record)

    # 4. landmark tops and the words band
    band = settings.value('safe_area.title_band_down')
    clear = settings.value('safe_area.landmark_top_min_down')
    text_left, text_right = settings.value('safe_area.text_left_pixels'), settings.value('safe_area.text_right_pixels')
    width = settings.value('frame.width_pixels')
    for view in chosen:
        title_rule = profile_rule(settings, view.get('kind_of_shot') or ['still_life'], 'rule12_title_zone_sky_share')
        dark_band = not title_rule.get('applies', True)
        for spot in view_spots(view):
            camera = film_camera(facts, settings, view, spot)
            for landmark in facts.get('landmark_tops', []):
                landed = geometry.project_point(camera, landmark['top'])
                if not landed['in_front'] or not 0 <= landed['across'] <= 1:
                    continue
                beside = not text_left / width <= landed['across'] <= text_right / width
                down = landed['down']
                height_clear = clearing_height(camera, landmark['top'], clear)
                record = {'view': view['name'], 'spot': spot, 'landmark': landmark['name'], 'across': landed['across'], 'down': down,
                          'depth': landed['depth'], 'top_height': landmark['top'][2], 'height_for_clear': height_clear}
                if down >= clear:
                    record['verdict'] = 'below the words band'
                elif beside:
                    record['verdict'] = 'beside the words'
                elif down < band[1]:
                    where_top = 'above the frame' if down < 0 else f'{down:.3f} down'
                    record['verdict'] = 'in the words band' + (' (dark band)' if dark_band else '')
                    text = (f'{landmark["name"]} in {view["name"]} ({spot}): its top lands {where_top}, so it rises through the band kept '
                            f'for typed words ({band[0]}-{band[1]} down; round 2). Lower it to {height_clear:.1f} m (now '
                            f'{landmark["top"][2]:.1f}), move it back, or put the words beside it')
                    if dark_band:
                        record['dark_band'] = True
                        settings.value('safe_area.top_shade')
                    else:
                        result['warnings'].append(text + '; the shot checker\'s rule 12 (the title zone at least '
                                                  f'{title_rule.get("value")} sky) judges it on the plate.')
                else:
                    record['verdict'] = 'just under the band'
                    result['warnings'].append(
                        f'{landmark["name"]} in {view["name"]} ({spot}): its top lands {down:.3f} down, within {clear - band[1]:.2f} of the '
                        f'words band; {height_clear:.1f} m tall (now {landmark["top"][2]:.1f}) clears {clear}. Look at the plate.')
                result['landmarks'].append(record)

    for view in chosen:
        for spot in view_spots(view):
            banded = [l for l in result['landmarks'] if l['view'] == view['name'] and l['spot'] == spot and l.get('dark_band')]
            if banded:
                result['warnings'].append(
                    f'{", ".join(l["landmark"] for l in banded)} rise through the words band in {view["name"]} ({spot}) (tops '
                    f'{", ".join(("above the frame" if l["down"] < 0 else format(l["down"], ".3f")) for l in banded)} down). This kind of '
                    f'shot ({", ".join(view.get("kind_of_shot") or [])}) puts the words over a soft dark band (safe_area.top_shade); '
                    f'otherwise lower them to about {min(l["height_for_clear"] for l in banded):.1f} m or put the words beside them.')

    # 5. figures: head size, face, distance, in frame
    head = settings.value('people.head_height_metres')
    face_pixels = settings.value('people.facing_head_max_pixels')
    nearest = settings.value('people.backs_to_camera_min_distance_metres')
    face_within = settings.value(f'{SECTION}.face_shows_within_degrees')
    half_width = settings.value(f'{SECTION}.figure_half_width_metres')
    for view in chosen:
        for spot in view_spots(view):
            camera = film_camera(facts, settings, view, spot)
            for figure in facts.get('figures', []):
                box = figure_box(camera, figure, half_width)
                if box is None:
                    continue
                feet = figure['feet']
                top = [feet[0], feet[1], feet[2] + figure['height_metres']]
                head_depth = geometry.project_point(camera, top)['depth']
                to_camera = geometry.subtract(camera['position'], feet)
                flat = geometry.normalise([to_camera[0], to_camera[1], 0.0])
                facing = figure['facing']
                angle = math.degrees(math.acos(max(-1.0, min(1.0, geometry.dot(geometry.normalise([facing[0], facing[1], 0.0]), flat)))))
                record = {'view': view['name'], 'spot': spot, 'figure': figure['name'], 'group': figure.get('group'),
                          'distance': geometry.length([to_camera[0], to_camera[1], 0.0]), 'head_pixels': geometry.size_in_pixels(camera, head, head_depth),
                          'figure_pixels': (box[3] - box[1]) * camera['frame'][1], 'box': box, 'face_angle_degrees': angle,
                          'face_can_show': angle <= face_within, 'whole_in_frame': 0 <= box[0] and box[2] <= 1 and 0 <= box[1] and box[3] <= 1}
                notes = []
                if record['face_can_show'] and record['head_pixels'] > face_pixels:
                    notes.append(f'its face can show ({angle:.0f} degrees from the camera) and its head is {record["head_pixels"]:.0f} px: look at '
                                 f'the painting\'s face (the people test\'s facing man got a blank face; silhouettes were rejected, lesson 137)')
                if record['distance'] < nearest:
                    notes.append(f'it stands {record["distance"]:.1f} m from the camera, nearer than {nearest} m')
                record['look'] = notes
                result['figures'].append(record)
            # one line per group: faces that can show, and figures standing too near
            for group in dict.fromkeys(f.get('group') for f in facts.get('figures', [])):
                mine = [r for r in result['figures'] if r['view'] == view['name'] and r['spot'] == spot and r['group'] == group]
                faces = [r for r in mine if r['face_can_show'] and r['head_pixels'] > face_pixels]
                near = [r for r in mine if r['distance'] < nearest]
                if faces:
                    heads = [r['head_pixels'] for r in faces]
                    result['warnings'].append(
                        f'{len(faces)} of {group} in {view["name"]} ({spot}) can show their faces, heads {min(heads):.0f}-{max(heads):.0f} px '
                        f'(over {face_pixels} px): look at the painted faces (the people test\'s facing man got a blank face, the far '
                        f'walkers face dots; silhouettes were rejected, lesson 137), or turn them away.')
                if near:
                    result['warnings'].append(f'{", ".join(r["figure"] for r in near)} ({group}) stand nearer than {nearest} m to '
                                              f'{view["name"]} ({spot}): {min(r["distance"] for r in near):.1f} m.')

    # 6. continuity: figures of each group in each view and state
    states = list((facts.get('states') or {}).keys()) or ['all']
    groups = count_groups or sorted({f.get('group') or 'figures' for f in facts.get('figures', [])})
    for view in chosen:
        spot = reading_spot(view)
        view_states = view.get('states') or states
        for state in view_states:
            counts = {}
            for figure in facts.get('figures', []):
                group = figure.get('group') or 'figures'
                if group not in groups or not shown_in_state(facts, figure, state, figure_states):
                    continue
                seen = next((r for r in result['figures'] if r['view'] == view['name'] and r['spot'] == spot and r['figure'] == figure['name']), None)
                if seen is not None:
                    counts[group] = counts.get(group, 0) + 1
            total = sum(counts.values())
            key = f'{view["name"]}/{state}'
            result['continuity'][key] = {'total': total, 'by_group': counts}
            if expect_counts and key in expect_counts and expect_counts[key] != total:
                result['problems'].append(f'Continuity: {key} shows {total} figure(s) of {", ".join(groups)} in the frame, the state table says '
                                          f'{expect_counts[key]}.')
    if expect_counts:
        for key in expect_counts:
            if key not in result['continuity']:
                result['notes'].append(f'Continuity: {key} is not a view and state of this place (known: {", ".join(result["continuity"])}).')
    return result


def profile_rule(settings, kinds, rule):
    """One rule of a view's shot-kind profile; only that rule is recorded as used."""
    from settings import resolve_profile
    before = dict(settings.used)
    resolved = resolve_profile(settings, kinds).get(rule, {})
    settings.used = before
    for kind in resolved.get('from_kinds', []):
        settings.used[f'shot_kind_profiles.{kind}.rules.{rule}'] = settings.node(f'shot_kind_profiles.{kind}.rules.{rule}')
    return resolved


def figure_box(camera, figure, half_width):
    """The figure's frame box [left, top, right, bottom] (shares) from an upright box round it, or None if no part of
    it is in the frame."""
    feet, height = figure['feet'], figure['height_metres']
    corners = geometry.box_corners([feet[0] - half_width, feet[1] - half_width, feet[2]], [feet[0] + half_width, feet[1] + half_width, feet[2] + height])
    projected = geometry.project_box(camera, corners)
    box = projected['box']
    if box is None or not projected['all_in_front']:
        return None
    if box[2] < 0 or box[0] > 1 or box[3] < 0 or box[1] > 1:
        return None
    return box


def shown_in_state(facts, figure, state, figure_states):
    if figure.get('shown_in') is not None:
        return state in figure['shown_in']
    if figure_states and figure.get('group') in figure_states:
        flag = figure_states[figure['group']]
        return bool((facts.get('states') or {}).get(state, {}).get(flag))
    return True


def clearing_height(camera, point, target_down):
    """The height (z) at which a point at this x, y lands at target_down (bisection: down falls as the point rises)."""
    low, high = point[2] - 500.0, point[2] + 500.0
    for _ in range(80):
        middle = (low + high) / 2
        landed = geometry.project_point(camera, [point[0], point[1], middle])
        if landed['down'] is None:
            return None
        if landed['down'] > target_down:
            low = middle
        else:
            high = middle
    return (low + high) / 2


# ------------------------------------------------------------------------------------------------ title contrast
def relative_luminance(rgb):
    """sRGB 0-255 to relative luminance (0-1)."""
    def linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(float(c)) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    light, dark = max(a, b), min(a, b)
    return (light + 0.05) / (dark + 0.05)


def band_opacity_needed(text_luminance, background_luminance, target):
    """The opacity of a black band that brings light words on this background to the target contrast:
    a = 1 - ((L_text + 0.05) / target - 0.05) / L_background (0 when already enough)."""
    if background_luminance <= 0:
        return 0.0
    allowed = (text_luminance + 0.05) / target - 0.05
    if allowed <= 0:
        return 1.0
    return max(0.0, min(1.0, 1 - allowed / background_luminance))


def title_contrast(still_path, box, text_colour, settings):
    import numpy as np
    from PIL import Image
    target = settings.value(f'{SECTION}.title_contrast_min')
    grow = settings.value(f'{SECTION}.title_background_grow_pixels')
    picture = np.asarray(Image.open(still_path).convert('RGB')).astype(np.float64)
    height, width = picture.shape[:2]
    if max(box) <= 1.0:
        box = [box[0] * width, box[1] * height, box[2] * width, box[3] * height]
    left, top = max(0, int(box[0] - grow)), max(0, int(box[1] - grow))
    right, bottom = min(width, int(math.ceil(box[2] + grow))), min(height, int(math.ceil(box[3] + grow)))
    area = picture[top:bottom, left:right] / 255.0
    linear = np.where(area <= 0.04045, area / 12.92, ((area + 0.055) / 1.055) ** 2.4)
    luminance = 0.2126 * linear[..., 0] + 0.7152 * linear[..., 1] + 0.0722 * linear[..., 2]
    text = relative_luminance(text_colour)
    light_text = text > float(np.median(luminance))
    worst = float(np.percentile(luminance, 95 if light_text else 5))
    mean = float(luminance.mean())
    result = {'still': still_path, 'box_pixels': [left, top, right, bottom], 'text_luminance': text, 'background_mean_luminance': mean,
              'background_worst_luminance': worst, 'contrast_mean': contrast_ratio(text, mean), 'contrast_worst': contrast_ratio(text, worst),
              'target': target, 'light_text': light_text}
    result['band_opacity_needed'] = band_opacity_needed(text, worst, target) if light_text else None
    lines = [f'Title contrast on {os.path.basename(still_path)}, box {result["box_pixels"]} (the word\'s box grown {grow} px):',
             f'  text luminance {text:.3f}; background mean {mean:.3f}, brightest 5% {worst:.3f}',
             f'  contrast {result["contrast_mean"]:.2f} on the mean, {result["contrast_worst"]:.2f} on the brightest 5% (needs {target})']
    if light_text:
        a = result['band_opacity_needed']
        lines.append(f'  {"PASS" if a == 0 else "BAND"}: ' + ('enough contrast without a band.' if a == 0 else
                     f'put a soft dark band of at least {a:.2f} opacity behind the words (safe_area.top_shade is the house band).'))
        if a:
            settings.value('safe_area.top_shade')
    else:
        lines.append('  Dark words: ' + ('PASS' if result['contrast_worst'] >= target else 'too little contrast: use light words or a light plate.'))
    return result, lines


# ------------------------------------------------------------------------------------------------ report
def report_lines(result, settings):
    lines = [f'View audit of {result["place"]}: {len(result["views"])} view(s).', '']
    for name, entry in result['views'].items():
        spot = entry['reading_spot']
        lines.append(f'View {name} ({", ".join(entry["kind_of_shot"] or [])}), words read at its {spot} spot:')
        rows = []
        for sign, by_spot in entry['signs'].items():
            m = by_spot.get(spot)
            if not m or not m['in_frame']:
                continue
            px = f'{m["letter_pixels"]:.1f} px' if m.get('letter_pixels') else 'size unknown'
            factors = (f', height x{m["height_factor"]:.2f}, width x{m["width_factor"]:.2f}' if m.get('height_factor') is not None
                       and m.get('width_factor') is not None else '')
            rows.append(f'    {sign}: {px} at {m["depth"]:.1f} m{factors}; {m.get("verdict", "")}')
        lines += rows or ['    no sign in the frame']
        out = [s for s, by_spot in entry['signs'].items() if not by_spot.get(spot, {}).get('in_frame')]
        behind = [s for s, by_spot in entry['signs'].items() if not by_spot.get(spot, {}).get('in_front', True)]
        if behind:
            lines.append(f'    behind the camera (never shows): {", ".join(behind)}')
        lines.append('')
    if result['stencil_turns']:
        lines.append('Curved stencils (the turn that faces every camera that reads them; the stencil faces -y at 0, + turns toward +x):')
        for t in result['stencil_turns']:
            per = ', '.join(f'{p["view"]} {p["spot"]} {p["turn_degrees"]:.1f}' for p in t['per_view'])
            lines.append(f'    {t["sign"]} ("{t["words"]}"): now {t["current_turn_degrees"]:.1f}, best {t["best_turn_degrees"]:.1f} '
                         f'(each camera: {per}); end letters {t["end_letter_angle_now_degrees"]:.1f} degrees from the worst camera now, '
                         f'{t["end_letter_angle_best_degrees"]:.1f} at the best')
        lines.append('')
    if result['loud_signs']:
        lines.append('Signs the page does not name:')
        for s in result['loud_signs']:
            lines.append(f'    {s["view"]} {s["sign"]}: {s["share_of_least_named"]:.2f} of {s["least_named"]} ({s["how"]}); limit {s["limit"]}; '
                         f'{s["verdict"]}' + (f'; dim needed {s["dim_needed"]:.2f}' if s.get('dim_needed') else ''))
        lines.append('')
    if result['landmarks']:
        lines.append('Landmark tops (down the frame; the words band is ' f'{settings.value("safe_area.title_band_down")}):')
        for l in result['landmarks']:
            lines.append(f'    {l["view"]} {l["spot"]} {l["landmark"]}: {l["down"]:.3f} down, {l["across"]:.3f} across; {l["verdict"]}')
        lines.append('')
    if result['figures']:
        lines.append('Figures in the frame at each view\'s reading spot (by group; every figure is in the JSON):')
        for name, entry in result['views'].items():
            rows = [f for f in result['figures'] if f['view'] == name and f['spot'] == entry['reading_spot']]
            for group in dict.fromkeys(f['group'] for f in rows):
                mine = [f for f in rows if f['group'] == group]
                heads = [f['head_pixels'] for f in mine]
                faces = sum(1 for f in mine if f['face_can_show'])
                cut = [f['figure'] for f in mine if not f['whole_in_frame']]
                lines.append(f'    {name} {group}: {len(mine)}, heads {min(heads):.1f}-{max(heads):.1f} px, nearest '
                             f'{min(f["distance"] for f in mine):.1f} m, faces that can show {faces}'
                             + (f', partly out of the frame: {", ".join(cut)}' if cut else ''))
        lines.append('')
    if result['continuity']:
        lines.append('Continuity (figures in the frame, by view and state):')
        lines.append('    ' + ', '.join(f'{k} {v["total"]}' for k, v in result['continuity'].items()))
        lines.append('')
    for title, items in (('Problems', result['problems']), ('Look at', result['warnings']), ('Notes', result['notes'])):
        if items:
            lines.append(f'{title}:')
            lines += [f'  - {i}' for i in items]
            lines.append('')
    lines.append(f'Verdict: {"FAIL" if result["problems"] else "PASS"} ({len(result["problems"])} problem(s), {len(result["warnings"])} to look at)')
    return lines


def parse_pairs(text, convert=str):
    pairs = {}
    for item in [i for i in (text or '').split(',') if i.strip()]:
        key, _, value = item.rpartition('=')
        pairs[key.strip()] = convert(value.strip())
    return pairs


def narration_of_page(timeline_path, page):
    with open(timeline_path) as handle:
        timeline = json.load(handle)
    for entry in timeline.get('pages', []):
        if str(entry.get('page')) == str(page):
            return [w for word in entry.get('words', []) for w in words_of(word.get('text'))]
    raise SystemExit(f'view_audit: no page {page} in {timeline_path}')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lettering, figure and landmark audit for every view of a place, worked out from '
                                                 'its place facts before anything is painted (see the note at the top of this file).')
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('audit', help='letters, stencil turns, loud signs, backs, landmark tops, heads and continuity')
    run.add_argument('--place-facts', required=True, help='the place facts file (place_facts.py check FILE)')
    run.add_argument('--view', action='append', help='only this view (repeatable)')
    run.add_argument('--named', help='comma list of the signs the page says aloud')
    run.add_argument('--timeline', help='a timeline JSON with pages and words (estimate_timeline.py), to find named signs')
    run.add_argument('--page', help='the page of --timeline')
    run.add_argument('--levels', help='letter brightness per view and sign (JSON)')
    run.add_argument('--figure-states', help='which state flag shows a figure group: "men at No. 1=men_1,men at No. 2=men_2"')
    run.add_argument('--count-groups', help='comma list of figure groups to count for continuity (default: all groups)')
    run.add_argument('--expect-counts', help='the state table: "w3/quiet=7,w1/working=0"')
    add_output_options(run)
    contrast = commands.add_parser('title-contrast', help='contrast behind a typed title on a still, and the dark band it needs')
    contrast.add_argument('--still', required=True, help='a still of the shot without the words (a plate or a filmed frame)')
    contrast.add_argument('--box', required=True, help='the words\' box left,top,right,bottom (shares of the frame, or pixels)')
    contrast.add_argument('--text-colour', default='ffffff', help='the words\' colour as hex (default ffffff)')
    add_output_options(contrast)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    if args.command == 'title-contrast':
        colour = args.text_colour.lstrip('#')
        rgb = [int(colour[i:i + 2], 16) for i in (0, 2, 4)]
        box = [float(v) for v in args.box.split(',')]
        result, lines = title_contrast(args.still, box, rgb, settings)
        finish('view_audit title-contrast', result, lines, settings, args)
        return 0
    with open(args.place_facts) as handle:
        facts = json.load(handle)
    named = [n.strip() for n in args.named.split(',') if n.strip()] if args.named else None
    narration = None
    if args.timeline:
        if not args.page:
            parser.error('--timeline needs --page')
        narration = narration_of_page(args.timeline, args.page)
    levels = None
    if args.levels:
        with open(args.levels) as handle:
            levels = json.load(handle)
    result = audit(facts, settings, args.view, named, narration, levels, parse_pairs(args.figure_states) or None,
                   [g.strip() for g in args.count_groups.split(',')] if args.count_groups else None,
                   parse_pairs(args.expect_counts, int) or None)
    full = finish('view_audit audit', geometry.round_all(result, 4), report_lines(result, settings), settings, args)
    return 1 if full['problems'] else 0


if __name__ == '__main__':
    sys.exit(main())
