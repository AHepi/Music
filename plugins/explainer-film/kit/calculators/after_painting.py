"""What this does: the fixed chain every returned painting goes through, with pass marks, so nobody has to remember the
steps or judge them by eye each time. It spends nothing; a paid re-ask it suggests still needs the user's yes.

  1. Saving: the painter's file is kept as it came; everything this tool writes is PNG (lossless), and a JPEG used as a
     base is flagged (round 2: saving as JPEG moved every pixel 0.48 levels on average, up to 9).
  2. Size: resized to the plate (Lanczos, as the ledgers' paintings were), since Flux returns 1504 x 2672 for a 1536 x 2730 plate.
  3. Line-up: always run (align_painting.py, the kit's tool). It fails only if the result ends under 0.85 of the props'
     outlines on the painting's edges, if the best shift or stretch sits at the edge of the search (12 px, 0.985/1.015:
     the painter moved it further than the search covers), or if lining up gained nothing on a painting that was not
     already lined up (skeptic, log 35). Notice corner: 0.70 to 0.96 at 1.0065, +3, +3; people test 0.874 to 0.903.
  4. Figures (when the check file has people): each figure's plate outline against the painting's edges, passed when
     the share within 3 px is no more than 0.05 below that figure's own plate baseline (the plate against itself:
     the measure is noisy, the hand-on-bar man scores only 0.84 on his own plate); figure-sized dark blobs the plate
     does not have (an added person); each figure's brightness against its surround, plate against painting (people
     test: about 0.15 in the plate, about 0.50 painted: the men turned mid-grey); skin-coloured pixels added on each
     head (the hand-on-bar man: 0 to 183).
  5. Style against the standard painting (the notice corner the user kept): brightness 77.4, spread 26.1, colour 50,
     ink lines 6.7% of the picture about 2.9 px wide, warm light on 19.7% of the ground. Warnings only.
  6. The behind painting (with --behind): resized, lined up against the lined-up painting away from the removed things;
     for near props (a slide) the painted shadows are kept round them (keep_painted_shadows.py) and the ground just beside
     each must not change by more than 2 levels at the handover (log 32: the pavement by the pail rose from 70 to 89);
     for people who leave at a cut (with --helper-plate, the plate drawn without them) their cast shadows must be gone
     (lesson 135: the painter left them). Wet and dry paintings go in and out as a pair: over the ground round the area
     the near props hid, the behind picture must not be lighter than the painting (a "pale patch": the wet lockout's
     old dry behind painting brought the hidden road back pale and dry, 59 percent of those road dots lighter; FAIL
     above 0.10 of the compared dots, an invented limit).
  7. The look as filmed (warnings only): how bright the painted ground arrives through the stage's finish pass with the
     page's look (--toe 0 or 1, the page's look.toe; the line says "the road arrives at X of its painted brightness",
     LOOK under 0.9, invented: the wet lockout reached 0.935 and the dry one 0.96 with toe 1); a "bottom fifth" more
     than composing.bottom_fifth_darker_max_share darker than the middle (a built place painted over should not end
     in a bare dark floor); "clouds" the painter added in the plate's sky area (textures logs 19-25: it adds heavy pale
     clouds even when told not to; put a plain sky back with Blender's exact sky outline).
Cut-out (paper look) checks are not here (the skeptic moved them to a second priority).

Use:
  python3 after_painting.py check --painting RETURNED.png --plate PLATE.png --check CHECK.json --facts PLATE_FACTS \\
          --out-folder DIR [--behind RETURNED_BEHIND.png] [--near GROUP ... | --near-list near-list.json] \\
          [--helper-plate HELPER.png] [--standard STANDARD_PAINTING] [--toe 0|1]
  python3 after_painting.py style --painting P.png [--standard S.png]      the style match alone
  python3 after_painting.py sky --painting LINED_UP.png --plate PLATE.png --facts PLATE_FACTS --to NEW.png
        lays the plate's plain sky over the painting, exactly inside the plate's sky area (a "clouds" LOOK); never writes over a file
An output that is already there (from an earlier run) is kept as NAME-previous.png beside the new one, never written over.
  python3 after_painting.py figures --painting LINED_UP.png --plate PLATE.png --check C.json --facts F   the figure checks alone
PLATE_FACTS is shot_facts.py's folder for the PLATE's camera and lens. Every command prints a plain report (or --json) and
names the film-settings.json values it used. Exit 1 when a check fails.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402
import frame_geometry as geometry  # noqa: E402
import painting_measures as measures  # noqa: E402


def item(found, name, verdict, words, numbers=None, fix=''):
    found.append({'check': name, 'verdict': verdict, 'what': words, 'numbers': measures.round_all(numbers or {}), 'fix': fix})


def keep_previous(path, kept=None):
    """Never writes over what came before (a person may have looked at it or approved it): an existing output is kept beside the new
    one as NAME-previous.png (an older -previous is replaced). Returns the kept path or None; adds it to the kept list when given."""
    if not os.path.exists(path):
        return None
    stem, ending = os.path.splitext(path)
    previous = f'{stem}-previous{ending}'
    os.replace(path, previous)
    if kept is not None:
        kept.append(previous)
    return previous


def write_png(path, rgb):
    """Writes losslessly and reads back: the file must hold exactly what was meant (0 levels off)."""
    data = np.clip(np.round(rgb), 0, 255).astype(np.uint8)
    cv2.imwrite(path, data[:, :, ::-1], [cv2.IMWRITE_PNG_COMPRESSION, 6])
    back = cv2.imread(path)[:, :, ::-1]
    return int(np.abs(back.astype(np.int16) - data.astype(np.int16)).max())


def plate_size(settings):
    return settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels')


# ------------------------------------------------------------------------------------------------ 3. the line-up
def judge_alignment(numbers, settings):
    floor = settings.value('painting_tools.after_painting.align_floor')
    aim = settings.value('painting.align_outline_agreement_aim')
    gain_min = settings.value('painting_tools.after_painting.align_gain_min')
    search = settings.value('painting.align_search')
    gain = numbers['after'] - numbers['before']
    at_edge = (numbers['stretch'] <= search['stretch'][0] + search['stretch_step'] / 5 or numbers['stretch'] >= search['stretch'][1] - search['stretch_step'] / 5
               or max(abs(v) for v in numbers['shift']) >= search['shift_pixels'][1])
    if at_edge:
        return 'fail', (f'the best fit sits at the edge of the search (stretch {numbers["stretch"]:.4f}, shift {numbers["shift"][0]:+.1f}, '
                        f'{numbers["shift"][1]:+.1f}; {numbers["after"]:.3f} of the outlines on edges): the painter moved it further than the search '
                        f'covers; widen the search or re-ask')
    if numbers['after'] < floor:
        return 'fail', f'only {numbers["after"]:.3f} of the outlines lie on the painting\'s edges once lined up (needs {floor}): the painter changed the shapes; re-ask'
    if gain < gain_min and numbers['before'] < aim:
        return 'fail', (f'lining up gained nothing ({numbers["before"]:.3f} to {numbers["after"]:.3f}) on a painting that does not sit on its outlines: '
                        f'is it the right plate? re-ask')
    if gain < gain_min:
        return 'pass', f'already lined up ({numbers["before"]:.3f}, {numbers["after"]:.3f} after the best fit)'
    return 'pass', (f'lined up: {numbers["before"]:.3f} to {numbers["after"]:.3f} of the outlines on the painting\'s edges at stretch '
                    f'{numbers["stretch"]:.4f}, shift {numbers["shift"][0]:+.1f}, {numbers["shift"][1]:+.1f} px (of {numbers["shift_frame_width"]} wide)')


# ------------------------------------------------------------------------------------------------ 4. figures
def edges(grey, low_high, blur):
    return cv2.Canny(cv2.GaussianBlur(grey, (0, 0), blur), low_high[0], low_high[1]) > 0


def distance_to_edges(edge_map):
    return cv2.distanceTransform((~edge_map).astype(np.uint8), cv2.DIST_L2, 5)


def figure_masks(shot, figures, size):
    return {g: measures.mask_at(shot.visible[g], size, smooth=True) for g in figures if shot.visible[g].sum() >= 20}


def outline_points(mask):
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return np.concatenate([c.reshape(-1, 2) for c in contours]) if contours else np.zeros((0, 2), int)


def figure_outlines(painting, plate, masks, settings):
    """Per figure: the share of its plate outline within 3 px of an edge in the painting, and the same against the plate's
    own edges (its baseline), as the figures helper measured (check-figures/scripts/chamfer.py)."""
    s = settings.value('painting_tools.after_painting.figure_edges')
    to_paint = distance_to_edges(edges(cv2.cvtColor(painting.astype(np.uint8), cv2.COLOR_RGB2GRAY), s['painting_canny'], s['blur']))
    to_plate = distance_to_edges(edges(cv2.cvtColor(plate.astype(np.uint8), cv2.COLOR_RGB2GRAY), s['plate_canny'], s['blur']))
    found = {}
    for g, m in masks.items():
        pts = outline_points(m)
        if len(pts) < 10:
            continue
        found[g] = {'outline_points': int(len(pts)), 'within_painting': float((to_paint[pts[:, 1], pts[:, 0]] <= s['within_pixels']).mean()),
                    'within_plate_baseline': float((to_plate[pts[:, 1], pts[:, 0]] <= s['within_pixels']).mean()),
                    'height_pixels': int(m.any(1).sum())}
    return found


def standing_height_pixels(shot, feet_down, settings):
    """How tall a standing person whose feet land at feet_down (share of the frame) comes out, from the plate camera's eye
    height and where the street's lines meet (frame_geometry's reach sums); None above the horizon."""
    camera = shot.facts['camera']
    meet = (shot.meet or shot.facts['lines_meet'].get('level') or [0.5, 0.5])[1]
    depth = geometry.reach_distance(feet_down, camera['eye_height'], meet, camera['vertical_fov_degrees'], shot.height)
    if depth is None:
        return None
    return geometry.size_in_pixels({'focal': geometry.focal_length_pixels(camera['vertical_fov_degrees'], shot.height)},
                                   settings.value('people.figure_height_metres'), depth) / shot.height


def dark_blobs(lum, settings, shot, exclude):
    """Dark, upright blobs as tall as a person standing where their feet are (the plate camera's eye and horizon)."""
    s = settings.value('painting_tools.after_painting.added_figure_blob')
    width, height = lum.shape[1], lum.shape[0]
    surround = cv2.blur(lum, (measures.scaled(s['surround_pixels_at_1536'], width),) * 2)
    dark = (lum < s['darker_than_surround'] * surround) & ~exclude
    dark = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    found = []
    for i in range(1, count):
        w, h, area = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT], stats[i, cv2.CC_STAT_AREA]
        if h < 20 or not (s['aspect_range'][0] <= h / max(w, 1) <= s['aspect_range'][1]) or area < s['fill_min'] * w * h:
            continue
        expected = standing_height_pixels(shot, (stats[i, cv2.CC_STAT_TOP] + h) / height, settings)
        if expected and s['height_range_factor'][0] <= h / (expected * height) <= s['height_range_factor'][1]:
            found.append({'box': [int(stats[i, cv2.CC_STAT_LEFT]), int(stats[i, cv2.CC_STAT_TOP]), int(w), int(h)], 'label': i,
                          'height_for_a_person_there': round(expected * height, 1)})
    return found, labels


def added_figures(painting_lum, plate_lum, shot, all_groups, settings):
    """Person-sized dark blobs in the painting that no group and no person-sized dark blob of the plate explains."""
    explained = np.zeros(painting_lum.shape, bool)
    for m in all_groups:
        explained |= m
    explained = cv2.dilate(explained.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    painted, labels = dark_blobs(painting_lum, settings, shot, explained)
    plate_blobs, plate_labels = dark_blobs(plate_lum, settings, shot, explained)
    plate_dark = np.isin(plate_labels, [b['label'] for b in plate_blobs])
    plate_dark = cv2.dilate(plate_dark.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    return [{k: v for k, v in b.items() if k != 'label'} for b in painted if not (plate_dark & (labels == b['label'])).any()]


def figure_checks(painting, plate, shot, figures, settings, found):
    size = (painting.shape[1], painting.shape[0])
    masks = figure_masks(shot, figures, size)
    if not masks:
        return {}
    # outlines against the plate's own baseline
    drop_max = settings.value('painting_tools.after_painting.figure_outline_drop_max')
    outlines = figure_outlines(painting, plate, masks, settings)
    moved = {g: v for g, v in outlines.items() if v['within_painting'] < v['within_plate_baseline'] - drop_max}
    item(found, 'figures kept their outlines', 'fail' if moved else 'pass',
         ((', '.join(f'{g} {v["within_painting"]:.2f} against its plate baseline {v["within_plate_baseline"]:.2f}' for g, v in moved.items()) +
           f': the painter moved, reshaped, lost or added to them (pass: within {drop_max} of the baseline).') if moved else
          f'All {len(outlines)} figures keep their plate outlines (within-3-px share no more than {drop_max} below each figure\'s own plate baseline).'),
         outlines, 'Look at the named figures at full size; a large drop is a lost or added part (people test: walker 4 painted whole, walker 5\'s bag lost).' if moved else '')
    # added people
    plate_lum, paint_lum = measures.luminance(plate), measures.luminance(painting)
    groups = [measures.mask_at(shot.alone[g], size) for g in shot.facts['groups']]
    extra = added_figures(paint_lum, plate_lum, shot, groups, settings)
    item(found, 'no added people', 'look' if extra else 'pass',
         (f'{len(extra)} figure-sized dark shape(s) in the painting that the plate does not have, at ' +
          ', '.join(f'x {b["box"][0]}-{b["box"][0] + b["box"][2]}, y {b["box"][1]}-{b["box"][1] + b["box"][3]}' for b in extra) +
          ': an added person? Look.') if extra else 'No figure-sized dark shape the plate does not have.', {'added': extra})
    # brightness against the surround
    all_figures = np.zeros(paint_lum.shape, bool)
    for m in masks.values():
        all_figures |= m
    ratio_max = settings.value('painting_tools.after_painting.figure_surround_ratio_max')
    lift_max = settings.value('painting_tools.after_painting.figure_surround_lift_max')
    tones = {}
    for g, m in masks.items():
        before = measures.figure_surround_ratio(plate_lum, m, all_figures, settings)
        after = measures.figure_surround_ratio(paint_lum, m, all_figures, settings)
        if before and after:
            tones[g] = {'plate': before, 'painting': after, 'lift': after / before}
    pale = {g: v for g, v in tones.items() if v['painting'] > ratio_max and v['lift'] > lift_max}
    item(found, 'figures as dark as in the plate', 'fail' if pale else 'pass',
         (f'{len(pale)} figure(s) painted much paler against their surround: ' +
          ', '.join(f'{g} {v["plate"]:.2f} to {v["painting"]:.2f}' for g, v in pale.items()) +
          f' (limit {ratio_max}, or {lift_max} times the plate). On a phone they turn mid-grey and blend into the road (people test).') if pale else
         f'Every figure keeps its darkness against its surround (under {ratio_max}, or under {lift_max} times the plate).', tones,
         'Darken the figures inside their outlines back toward the plate\'s ratio (free), or re-ask with "Keep the figures as dark as they are '
         'in image 1" (a paid re-ask needs the user\'s yes).' if pale else '')
    # skin on heads
    limit = settings.value('painting_tools.after_painting.new_skin_pixels_look')
    plate_skin, paint_skin = measures.skin_pixels(plate), measures.skin_pixels(painting)
    heads = {}
    for g, m in masks.items():
        head = measures.head_region(m, settings)
        heads[g] = {'plate': int((plate_skin & head).sum()), 'painting': int((paint_skin & head).sum())}
        heads[g]['added'] = heads[g]['painting'] - heads[g]['plate']
    scale = (painting.shape[1] / 1536) ** 2
    skin = {g: v for g, v in heads.items() if v['added'] >= limit * scale}
    item(found, 'no skin added on heads', 'look' if skin else 'pass',
         (f'skin-coloured pixels added on {len(skin)} head(s): ' + ', '.join(f'{g} {v["plate"]} to {v["painting"]}' for g, v in skin.items()) +
          ' (a face, an ear or a lit cheek the prompt asked against). Look at them at phone size.') if skin else
         f'No head gained {limit} skin-coloured pixels or more.', heads,
         'If it shows on a phone, paint the patch over with the cap\'s shadow colour (free).' if skin else '')
    return {'outlines': outlines, 'added': extra, 'tones': tones, 'heads': heads}


# ------------------------------------------------------------------------------------------------ 5. style
def style_measures(rgb, settings):
    """The looks helper's measures (check-looks/scripts measure1.py, lines.py, warm.py) on a whole painting at plate size."""
    ink = settings.value('painting_tools.after_painting.ink_line')
    warm = settings.value('painting_tools.after_painting.warm_ground')
    lum = measures.luminance(rgb)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ink['blackhat_pixels'],) * 2)
    blackhat = cv2.morphologyEx(lum, cv2.MORPH_BLACKHAT, kernel)
    lines = (blackhat > ink['blackhat_min']) & (lum < ink['dark_max'])
    lines = cv2.morphologyEx(lines.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
    distance = cv2.distanceTransform(lines.astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    ridge = (distance > 0) & (distance >= cv2.dilate(distance, np.ones((3, 3), np.uint8)))
    warm_lit = ((rgb[..., 0] - rgb[..., 2]) > warm['red_minus_blue_min']) & (lum > warm['brightness_min'])
    ground = np.zeros(lum.shape, bool)
    ground[int(warm['ground_from_down'] * lum.shape[0]):, :] = True
    return {'brightness': float(lum.mean()), 'spread': float(lum.std()), 'colour': float(measures.hsv(rgb)[..., 1].mean()),
            'ink_share': float(lines.mean()), 'line_width_pixels': float((2 * distance[ridge]).mean()) if ridge.any() else 0.0,
            'warm_ground_share': float(warm_lit[ground].mean())}


def style_check(rgb, settings, found, standard_path=None):
    standard = style_measures(measures.read_rgb(standard_path, (rgb.shape[1], rgb.shape[0])), settings) if standard_path else \
        settings.value('painting_tools.after_painting.style_standard')
    tolerance = settings.value('painting_tools.after_painting.style_tolerance')
    got = style_measures(rgb, settings)
    off = []
    for key in ('brightness', 'spread', 'colour'):
        if abs(got[key] - standard[key]) > tolerance[key]:
            off.append(f'{key} {got[key]:.1f} against {standard[key]:.1f}')
    if abs(got['ink_share'] - standard['ink_share']) > tolerance['ink_share']:
        off.append(f'ink lines {got["ink_share"]:.1%} against {standard["ink_share"]:.1%}')
    if got['line_width_pixels'] > tolerance['line_width_ratio'] * standard['line_width_pixels']:
        off.append(f'lines {got["line_width_pixels"]:.1f} px wide against {standard["line_width_pixels"]:.1f}')
    if got['warm_ground_share'] < tolerance['warm_ground_ratio_min'] * standard['warm_ground_share']:
        off.append(f'warm light on {got["warm_ground_share"]:.1%} of the ground against {standard["warm_ground_share"]:.1%}')
    item(found, 'style against the standard painting', 'look' if off else 'pass',
         ('Differs from the standard painting: ' + '; '.join(off) + '. A warning, not a failure: look at it beside the standard.') if off else
         'Matches the standard painting\'s brightness, spread, colour, ink lines and warm ground.', {'got': got, 'standard': standard})
    return got


# ------------------------------------------------------------------------------------------------ 6. the behind painting
def ring(mask, inner, outer):
    grow = lambda r: cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))).astype(bool)
    return grow(outer) & ~grow(inner)


def shadow_band(main, behind, combined, shot, near, settings, others):
    """The ground 10-30 px beside each near prop: main painting against the raw behind painting and the combined picture."""
    band = settings.value('painting_tools.after_painting.shadow_band_pixels_at_1536')
    width = main.shape[1]
    inner, outer = [max(1, int(round(b * width / 1536))) for b in band]
    lum = {k: measures.luminance(v) for k, v in (('main', main), ('behind', behind), ('combined', combined))}
    found = {}
    size = (width, main.shape[0])
    for g in near:
        if g not in shot.visible or not shot.visible[g].any():
            continue
        m = measures.mask_at(shot.visible[g], size)
        r = ring(m, inner, outer) & ~others
        if r.sum() < 50:
            continue
        found[g] = {'main': float(lum['main'][r].mean()), 'behind': float(lum['behind'][r].mean()), 'combined': float(lum['combined'][r].mean())}
        found[g]['combined_change'] = abs(found[g]['combined'] - found[g]['main'])
        found[g]['behind_change'] = abs(found[g]['behind'] - found[g]['main'])
    return found


def leftover_shadows(painting, behind, plate, helper, masks, settings):
    """Where the leaving figures' shadows fell (the plate under 0.75 of the helper plate, outside the figures), how much the
    behind painting brightened against the painting, as a share of how much the helper plate is brighter than the plate."""
    s = settings.value('painting_tools.after_painting.leftover_shadow')
    plate_lum, helper_lum = measures.luminance(plate), measures.luminance(helper)
    figures = np.zeros(plate_lum.shape, bool)
    for m in masks.values():
        figures |= m
    figures = cv2.dilate(figures.astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
    blur = lambda x: cv2.GaussianBlur(x, (0, 0), 3)
    shadow = (blur(plate_lum) + 1) / (blur(helper_lum) + 1) < s['plate_over_helper_max']
    shadow &= ~figures
    shadow = cv2.morphologyEx(shadow.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
    if shadow.sum() < 100:
        return None
    expected = float((helper_lum - plate_lum)[shadow].mean())
    actual = float((measures.luminance(behind) - measures.luminance(painting))[shadow].mean())
    return {'shadow_share_of_frame': float(shadow.mean()), 'expected_brightening': expected, 'painted_brightening': actual,
            'share_of_expected': actual / expected if expected > 0 else None}


def behind_checks(args, settings, shot, aligned_path, painting, plate, found, out, kept=None):
    s = settings
    size = plate_size(s)
    stem = os.path.splitext(os.path.basename(args.behind))[0]
    resized = measures.read_painting_at_plate_size(args.behind, size)
    resized_path = os.path.join(out, f'{stem}-plate-size.png')
    keep_previous(resized_path, kept)
    write_png(resized_path, resized)
    near = list(args.near or [])
    if args.near_list:
        near += measures.load_json(args.near_list).get('near', [])
    figures = measures.figure_groups(shot)
    leaving_people = bool(args.helper_plate)
    if not near and leaving_people:
        near = [g for g in figures if shot.visible[g].any()]
    if not near:
        near = [g for g in shot.core if g in shot.visible]
    lined = os.path.join(out, f'{stem}-aligned.png')
    keep_previous(lined, kept)
    numbers = measures.align(args.check, args.facts, resized_path, lined, against=aligned_path, groups=near)
    verdict, words = judge_alignment(numbers, s)
    against_floor = s.value('painting.align_outline_agreement_aim')
    if numbers['after'] < against_floor:
        verdict = 'fail'
    item(found, 'behind painting lined up against the painting', verdict, words + f' (away from {", ".join(near)})', numbers)
    behind = measures.read_rgb(lined)
    result = {'near': near, 'aligned': lined}
    if leaving_people:
        masks = figure_masks(shot, figures, size)
        helper = measures.read_rgb(args.helper_plate, size)
        left = leftover_shadows(painting, behind, plate, helper, masks, s)
        limits = s.value('painting_tools.after_painting.leftover_shadow')
        if left is None:
            item(found, 'leaving people took their shadows', 'pass', 'The plates show no cast shadows from the people who leave.')
        else:
            bad = left['expected_brightening'] >= limits['expected_min_levels'] and (left['share_of_expected'] or 0) < limits['brightening_share_min']
            item(found, 'leaving people took their shadows', 'fail' if bad else 'pass',
                 (f'Where their shadows fell ({left["shadow_share_of_frame"]:.1%} of the frame) the helper plate is {left["expected_brightening"]:.1f} levels '
                  f'brighter than the plate, but the behind painting only {left["painted_brightening"]:.1f} brighter than the painting: the painter '
                  f'left their shadows (lesson 135); they stay on the road after the cut.') if bad else
                 f'The shadows where the people stood are gone ({left["painted_brightening"]:.1f} of {left["expected_brightening"]:.1f} levels brighter).',
                 left, 'Free fix: multiply the behind painting by helper/plate (clamped 1 to 3, blurred) in that area; better, draw plates '
                       'with no long shadows from people who come and go.' if bad else '')
        result['leftover'] = left
    else:
        shadows_kept = os.path.join(out, f'{stem}-shadows-kept.png')
        keep_previous(shadows_kept, kept)
        widen = s.value('painting.keep_painted_shadows_widen_pixels')
        measures.run_tool('keep_painted_shadows.py', [args.check, args.facts, aligned_path, lined, shadows_kept, widen] + near)
        combined = measures.read_rgb(shadows_kept)
        others = np.zeros(combined.shape[:2], bool)
        for g in shot.facts['groups']:
            others |= measures.mask_at(shot.alone[g], (combined.shape[1], combined.shape[0]))
        bands = shadow_band(painting, behind, combined, shot, near, s, others)
        limit = s.value('painting_tools.after_painting.shadow_band_change_max_levels')
        moved = {g: v for g, v in bands.items() if v['combined_change'] > limit}
        item(found, 'painted shadows kept round the near props', 'fail' if moved else 'pass',
             (', '.join(f'{g}: {v["main"]:.1f} to {v["combined"]:.1f}' for g, v in moved.items()) + f' levels on the ground beside it at the '
              f'handover (limit {limit}).') if moved else
             (f'The ground beside each near prop changes at most {max((v["combined_change"] for v in bands.values()), default=0):.1f} levels at the '
              f'handover (the raw behind painting would change it up to {max((v["behind_change"] for v in bands.values()), default=0):.1f}).'),
             bands)
        result['shadows_kept'] = shadows_kept
        result['bands'] = bands
        hid = np.zeros(combined.shape[:2], bool)
        for g in near:
            if g in shot.alone:
                hid |= measures.mask_at(shot.alone[g], (combined.shape[1], combined.shape[0]))
        visible = np.zeros(combined.shape[:2], bool)
        for g in shot.facts['groups']:
            visible |= measures.mask_at(shot.visible[g], (combined.shape[1], combined.shape[0]))
        result['pale_patch'] = pale_patch(painting, combined, hid, visible, s)
        judge_pale_patch(found, result['pale_patch'], s)
    return result


# ------------------------------------------------------------------------------------------------ 6b. pale patch
def pale_patch(main, behind, hid, groups, settings):
    """Wet and dry go in and out as a pair: over the ground round the area the near props hid (grown by the band, with
    every measured group and a blur's width round it left out, so only ground both pictures show is compared), the share
    of dots where the behind picture is lighter than the painting by more than lighter_by_levels, after a blur (two
    paintings never match dot for dot, so local brightness is compared). None when there is too little ground."""
    s = settings.value('painting_tools.after_painting.pale_patch')
    width = main.shape[1]
    band = max(1, int(round(s['band_pixels_at_1536'] * width / 1536)))
    blur = max(0.5, s['blur_pixels_at_1536'] * width / 1536)
    grown = cv2.dilate(hid.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * band + 1,) * 2)).astype(bool)
    margin = int(round(3 * blur)) + 2
    keep_out = cv2.dilate(groups.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * margin + 1,) * 2)).astype(bool)
    area = grown & ~keep_out
    if area.sum() < 100:
        return None
    painted = cv2.GaussianBlur(measures.luminance(main).astype(np.float32), (0, 0), blur)
    behind_lum = cv2.GaussianBlur(measures.luminance(behind).astype(np.float32), (0, 0), blur)
    change = (behind_lum - painted)[area]
    return {'compared_dots': int(area.sum()), 'lighter_share': float((change > s['lighter_by_levels']).mean()),
            'darker_share': float((change < -s['lighter_by_levels']).mean()), 'mean_change_levels': float(change.mean())}


def judge_pale_patch(found, numbers, settings):
    s = settings.value('painting_tools.after_painting.pale_patch')
    if numbers is None:
        item(found, 'behind picture as wet or dry as the painting', 'pass', 'Too little ground round the near props to compare (no pale patch can show).')
        return
    bad = numbers['lighter_share'] > s['lighter_share_max']
    item(found, 'behind picture as wet or dry as the painting', 'fail' if bad else 'pass',
         (f'pale patch: {numbers["lighter_share"]:.2f} of the ground round the area the near props hid is lighter in the behind picture than '
          f'in the painting (by more than {s["lighter_by_levels"]} levels; limit {s["lighter_share_max"]}, invented; the wet lockout\'s old dry '
          f'behind painting: 0.59, measured). When the camera moves the hidden road comes back pale and dry.') if bad else
         (f'The behind picture matches the painting round the near props ({numbers["lighter_share"]:.2f} of the ground lighter, limit '
          f'{s["lighter_share_max"]}, invented): no pale patch.'), numbers,
         'Wet and dry paintings go in and out as a pair: ask for (or make) the behind painting in the same state as the front painting, '
         'and keep the other pair beside it under -dry or -wet names with a note on how to go back.' if bad else '')


# ------------------------------------------------------------------------------------------------ 7. the look as filmed
def ground_mask(shot, size):
    """The painted ground: below the height where the street's lines meet (the ground's horizon), not sky and not any
    measured group, at a picture's (width, height)."""
    width, height = size
    ground = np.zeros((height, width), bool)
    ground[int(round(shot.ground_horizon / shot.height * height)):, :] = True
    ground &= ~measures.mask_at(shot.sky, size)
    for g in shot.facts['groups']:
        ground &= ~measures.mask_at(shot.visible[g], size)
    return ground


def road_arrival(painting, ground, look):
    """How bright the painted ground arrives in the film: its mean brightness after the stage's finish pass (with the
    page's look, toe included; glow, vignette and grain left out) over its painted mean brightness."""
    if ground.sum() < 100:
        return None
    colours = painting[ground]
    step = max(1, len(colours) // 200000)
    colours = colours[::step]
    painted = float(measures.luminance(colours).mean())
    filmed = float(measures.luminance(measures.stage_finish(colours, look)).mean())
    return {'ground_dots': int(ground.sum()), 'painted_brightness': painted, 'filmed_brightness': filmed,
            'arrives_share': filmed / painted if painted > 0 else None, 'toe': look.get('toe', 0)}


def bottom_fifth(painting, settings):
    """How much darker the bottom fifth of the picture is than its middle (1 - bottom / middle)."""
    bands = settings.value('painting_tools.after_painting.bottom_fifth_bands')
    lum = measures.luminance(painting)
    height = lum.shape[0]
    part = lambda band: float(lum[int(band[0] * height):max(int(band[0] * height) + 1, int(band[1] * height))].mean())
    bottom, middle = part(bands['bottom']), part(bands['middle'])
    return {'bottom_fifth_brightness': bottom, 'middle_brightness': middle, 'darker_share': 1 - bottom / middle if middle > 0 else 0.0}


def sky_clouds(painting, sky, settings):
    """The spread of brightness inside the plate's sky area once each row's own middle level is taken away: a plain or
    evenly graded sky spreads close to 0; painted clouds spread it. The sky area is shrunk first so rails, roof edges and
    wires at its border do not count."""
    s = settings.value('painting_tools.after_painting.sky_clouds')
    size = (painting.shape[1], painting.shape[0])
    mask = measures.mask_at(sky, size)
    result = {'sky_share': float(mask.mean())}
    if mask.mean() < s['sky_share_min']:
        return result
    erode = int(round(s['erode_pixels_at_1536'] * size[0] / 1536))
    inner = cv2.erode(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * erode + 1,) * 2)).astype(bool)
    if inner.sum() < 100:
        return result
    blur = max(0.5, s['blur_pixels_at_1536'] * size[0] / 1536)
    lum = cv2.GaussianBlur(measures.luminance(painting).astype(np.float32), (0, 0), blur)
    row_middle = np.ma.median(np.ma.masked_array(lum, ~inner), axis=1).filled(0)
    residual = (lum - row_middle[:, None])[inner]
    result.update({'sky_dots': int(inner.sum()), 'spread_levels': float(residual.std()),
                   'lighter_share': float((residual > 2 * s['spread_levels_max']).mean())})
    return result


def look_checks(painting, shot, toe, settings, found):
    """Step 7, warnings only: the road's arrival through the finish with the page's toe, the bottom fifth, clouds."""
    result = {}
    size = (painting.shape[1], painting.shape[0])
    look = dict(settings.value('painting_tools.paint_request.film_look'), toe=toe)
    below = settings.value('painting_tools.after_painting.road_arrives_look_below')
    road = road_arrival(painting, ground_mask(shot, size), look)
    result['road'] = road
    if road is None or road['arrives_share'] is None:
        item(found, 'the road as filmed', 'pass', 'No painted ground below the horizon to measure.')
    else:
        dark = road['arrives_share'] < below
        item(found, 'the road as filmed', 'look' if dark else 'pass',
             f'With the page\'s look (toe {toe}) the road arrives at {road["arrives_share"]:.3f} of its painted brightness '
             f'({road["painted_brightness"]:.1f} painted, {road["filmed_brightness"]:.1f} filmed; the finish pass without glow, vignette and grain). '
             + (f'Under {below} (invented; the wet lockout reached 0.935 and the dry one 0.96 with toe 1): dark painted values are being '
                'crushed. Look at it in the film.' if dark else f'Not under {below} (invented).'),
             road, ('For a dark, dusk or wet page set toe: 1 and vignette: 0.25 in its look (cinema-stage.js look.toe; the lockout test '
                    'page does), then check again with --toe 1.' if dark and not toe else 'Look at the page in the film.' if dark else ''))
    fifth = bottom_fifth(painting, settings)
    result['bottom_fifth'] = fifth
    most = settings.value('composing.bottom_fifth_darker_max_share')
    dark_floor = fifth['darker_share'] > most
    item(found, 'the bottom of the frame', 'look' if dark_floor else 'pass',
         (f'The bottom fifth is {fifth["darker_share"]:.0%} darker than the middle (limit {most:.0%}, composing.bottom_fifth_darker_max_share; '
          'in the log 26 review about 70 percent of frames failed this because the prompts asked for an empty floor). On a built place painted '
          'over, the nearest story thing should reach about 0.70 down and the bottom third is not bare floor (only the paper route keeps the '
          'lower quarter for its pieces).') if dark_floor else
         f'The bottom fifth is {max(0.0, fifth["darker_share"]):.0%} darker than the middle (limit {most:.0%}).', fifth)
    clouds = sky_clouds(painting, shot.sky, settings)
    result['sky'] = clouds
    limit = settings.value('painting_tools.after_painting.sky_clouds')['spread_levels_max']
    if 'spread_levels' not in clouds:
        item(found, 'a plain sky', 'pass', f'Too little sky in this view to measure ({clouds["sky_share"]:.1%} of the frame).', clouds)
    else:
        cloudy = clouds['spread_levels'] > limit
        item(found, 'a plain sky', 'look' if cloudy else 'pass',
             (f'clouds: inside the plate\'s sky area the brightness spreads {clouds["spread_levels"]:.1f} levels once each row\'s own level is '
              f'taken away (limit {limit}, invented; a plain or evenly graded sky is close to 0). The painter adds heavy pale clouds even when '
              'told not to.') if cloudy else
             f'The sky is plain: it spreads {clouds["spread_levels"]:.1f} levels inside the plate\'s sky area (limit {limit}, invented; no clouds).',
             clouds, 'Put a plain sky back from the plate, using Blender\'s exact sky outline (the plate\'s sky area), keeping thin rails and '
                     'roof edges clean; look at it at full size.' if cloudy else '')
    return result


def plain_sky(painting, plate, sky):
    """The painting with the plate's own plain sky laid over it, exactly inside the plate's sky area (Blender's own outline: the dots
    where nothing is drawn), so thin rails, wires and roof edges stay as painted. Returns (picture, share of the frame replaced)."""
    out = painting.copy()
    out[sky] = plate[sky]
    return out, float(sky.mean())


def sky_mask_from_facts(facts_folder, size):
    """The plate's sky area at a picture's (width, height): the dots of the facts folder's ids.png where nothing is drawn (as the shot
    checker reads it), resized dot for dot (nearest), never blurred."""
    ids = cv2.imread(os.path.join(facts_folder, 'ids.png'))
    if ids is None:
        raise SystemExit(f'after_painting: {facts_folder} has no ids.png: measure the plate with shot_facts.py first')
    return measures.mask_at(ids.astype(np.int32).sum(axis=2) < 24, size)


def command_sky(args, settings):
    """Lays the plate's plain sky over a painting the painter gave clouds (it adds heavy pale clouds even when told not to)."""
    if os.path.abspath(args.to) in (os.path.abspath(args.painting), os.path.abspath(args.plate)):
        raise SystemExit('after_painting sky: --to must be a new file (the painting and the plate are never written over)')
    painting = measures.read_rgb(args.painting)
    size = (painting.shape[1], painting.shape[0])
    plate = measures.read_rgb(args.plate, size)
    sky = sky_mask_from_facts(args.facts, size)
    result_picture, share = plain_sky(painting, plate, sky)
    found = []
    kept = []
    keep_previous(args.to, kept)
    off = write_png(args.to, result_picture)
    spread_before = sky_spread(painting, sky, settings)
    spread_after = sky_spread(result_picture, sky, settings)
    item(found, 'a plain sky laid in', 'pass' if off == 0 else 'fail',
         f'the plate\'s plain sky laid over {share:.1%} of the frame (the plate\'s exact sky outline; thin rails and roof edges stay as painted); '
         f'the sky\'s spread {spread_before:.1f} levels before, {spread_after:.1f} after; written to {os.path.basename(args.to)}'
         + (f' (the earlier one kept as {os.path.basename(kept[0])})' if kept else '') + '. Look at the edges at full size.',
         {'sky_share': share, 'spread_before_levels': spread_before, 'spread_after_levels': spread_after, 'read_back_levels_off': off})
    return finish_lines(found, {'picture': args.to, 'sky_share': share}, 'A plain sky: ' + os.path.basename(args.painting))


def sky_spread(picture, sky, settings):
    """The clouds measure's spread (levels) inside a sky mask already at the picture's size."""
    s = settings.value('painting_tools.after_painting.sky_clouds')
    erode = int(round(s['erode_pixels_at_1536'] * picture.shape[1] / 1536))
    inner = cv2.erode(sky.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * erode + 1,) * 2)).astype(bool)
    if inner.sum() < 100:
        return 0.0
    blur = max(0.5, s['blur_pixels_at_1536'] * picture.shape[1] / 1536)
    lum = cv2.GaussianBlur(measures.luminance(picture).astype(np.float32), (0, 0), blur)
    row_middle = np.ma.median(np.ma.masked_array(lum, ~inner), axis=1).filled(0)
    return float((lum - row_middle[:, None])[inner].std())


# ------------------------------------------------------------------------------------------------ commands
def command_check(args, settings):
    out = args.out_folder
    os.makedirs(out, exist_ok=True)
    found = []
    size = plate_size(settings)
    shot = measures.load_shot(args.check, args.facts)
    # 1. saving
    lossless = measures.is_lossless(args.painting)
    item(found, 'kept lossless', 'pass' if lossless else 'look',
         'The painting is a lossless file; everything written here is PNG.' if lossless else
         f'{os.path.basename(args.painting)} is a JPEG: keep the PNG the painter returned for anything used as a base (a JPEG moves every '
         f'pixel; round 2: 0.48 levels on average, up to 9). Everything written here is PNG.')
    # 2. size
    stem = os.path.splitext(os.path.basename(args.painting))[0]
    resized = measures.read_painting_at_plate_size(args.painting, size)
    resized_path = os.path.join(out, f'{stem}-plate-size.png')
    kept = []
    keep_previous(resized_path, kept)
    off = write_png(resized_path, resized)
    returned = cv2.imread(args.painting).shape[:2][::-1]
    item(found, 'resized to the plate', 'pass' if off == 0 else 'fail', f'{returned[0]} x {returned[1]} resized to {size[0]} x {size[1]} '
         f'(Lanczos, as the ledgers\' paintings were) and read back {off} levels off.', {'returned_size': list(returned), 'read_back_levels_off': off})
    # 3. line-up
    aligned_path = os.path.join(out, f'{stem}-aligned.png')
    keep_previous(aligned_path, kept)
    numbers = measures.align(args.check, args.facts, resized_path, aligned_path)
    verdict, words = judge_alignment(numbers, settings)
    item(found, 'lined up with the plate', verdict, words[0].upper() + words[1:] + '.', numbers,
         'Re-ask the painter (a paid re-ask needs the user\'s yes).' if verdict == 'fail' else '')
    painting = measures.read_rgb(aligned_path)
    plate = measures.read_rgb(args.plate, size)
    result = {'resized': resized_path, 'aligned': aligned_path, 'alignment': numbers}
    # 4. figures
    figures = args.figures or measures.figure_groups(shot)
    if figures:
        result['figures'] = figure_checks(painting, plate, shot, figures, settings, found)
    # 5. style
    result['style'] = style_check(painting, settings, found, args.standard)
    # 7. the look as filmed (warnings only; before the behind painting so its lines stay together)
    result['look'] = look_checks(painting, shot, args.toe, settings, found)
    # 6. behind
    if args.behind:
        result['behind'] = behind_checks(args, settings, shot, aligned_path, painting, plate, found, out, kept)
    if kept:
        result['kept_previous'] = kept
        item(found, 'earlier outputs kept', 'pass', f'{len(kept)} earlier output(s) were kept beside the new ones as NAME-previous.png ('
             + ', '.join(os.path.basename(k) for k in kept[:4]) + '): to go back, copy a -previous file over its new one.')
    return finish_lines(found, result, 'Painting arrival checks: ' + os.path.basename(args.painting))


def finish_lines(found, result, title):
    failed = [f for f in found if f['verdict'] == 'fail']
    lines = [f'{title} ({len(failed)} failure(s); a paid re-ask needs the user\'s yes)', '']
    for f in found:
        lines.append(f'- {f["verdict"].upper():5s} {f["check"]}: {f["what"]}')
        if f['fix']:
            lines.append(f'        fix: {f["fix"]}')
    result['checks'] = found
    result['failed'] = len(failed)
    return measures.round_all(result), lines, 1 if failed else 0


def command_style(args, settings):
    found = []
    size = plate_size(settings)
    got = style_check(measures.read_rgb(args.painting, size), settings, found, args.standard)
    return finish_lines(found, {'style': got}, 'Style against the standard: ' + os.path.basename(args.painting))


def command_figures(args, settings):
    found = []
    size = plate_size(settings)
    shot = measures.load_shot(args.check, args.facts)
    figures = args.figures or measures.figure_groups(shot)
    if not figures:
        raise SystemExit('after_painting: the check file names no "figures" (or give --figures)')
    result = figure_checks(measures.read_rgb(args.painting, size), measures.read_rgb(args.plate, size), shot, figures, settings, found)
    return finish_lines(found, {'figures': result}, 'Figure checks: ' + os.path.basename(args.painting))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Checks a returned painting (see the note at the top).')
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('check', help='the whole chain on a returned painting')
    p.add_argument('--painting', required=True, help='the painting as returned')
    p.add_argument('--plate', required=True, help='the plate it was painted from')
    p.add_argument('--check', required=True, help='the view\'s shot-check file')
    p.add_argument('--facts', required=True, help='shot_facts.py\'s folder for the PLATE\'s camera and lens')
    p.add_argument('--out-folder', required=True, help='where the resized, lined-up and combined PNGs go')
    p.add_argument('--behind', help='the behind painting as returned')
    p.add_argument('--near', nargs='*', help='the groups the behind painting removed (default: the near list, the leaving people or the story)')
    p.add_argument('--near-list', help='paint_request.py\'s near-list.json')
    p.add_argument('--helper-plate', help='the plate drawn without the people who leave (for their shadows)')
    p.add_argument('--figures', nargs='*', help='the groups that are people (default: the check file\'s "figures")')
    p.add_argument('--standard', help='the standard painting to match (default: its numbers in film-settings.json)')
    p.add_argument('--toe', type=int, choices=(0, 1), default=0,
                   help='the page\'s look.toe (0, the default, the filmic curve as it always was; 1 for a dark, dusk or wet page)')
    add_output_options(p)
    p = commands.add_parser('style', help='the style match alone')
    p.add_argument('--painting', required=True)
    p.add_argument('--standard', help='the standard painting (default: its numbers in film-settings.json)')
    add_output_options(p)
    p = commands.add_parser('sky', help='lay the plate\'s plain sky over a painting (exactly inside the plate\'s sky area), into a new file')
    p.add_argument('--painting', required=True, help='the lined-up painting (the -aligned.png check wrote)')
    p.add_argument('--plate', required=True, help='the plate it was painted from')
    p.add_argument('--facts', required=True, help='shot_facts.py\'s folder for the PLATE (its ids.png gives the sky area)')
    p.add_argument('--to', required=True, help='the new picture file (PNG); an earlier one is kept as NAME-previous.png')
    add_output_options(p)
    p = commands.add_parser('figures', help='the figure checks alone, on a lined-up painting')
    p.add_argument('--painting', required=True)
    p.add_argument('--plate', required=True)
    p.add_argument('--check', required=True)
    p.add_argument('--facts', required=True)
    p.add_argument('--figures', nargs='*')
    add_output_options(p)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    job = {'check': command_check, 'style': command_style, 'figures': command_figures, 'sky': command_sky}[args.command]
    result, lines, code = job(args, settings)
    finish(f'after_painting {args.command}', result, lines, settings, args)
    return code


if __name__ == '__main__':
    sys.exit(run_main(main, 'after_painting'))
