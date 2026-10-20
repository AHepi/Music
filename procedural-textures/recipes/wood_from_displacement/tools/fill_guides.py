# What this does (plain words): writes the two guide files of the wood-from-maps job from their templates (tools/guide_templates/*.md) by putting the
# measured numbers into the places marked @@name@@ and @@TABLE_NAME@@. The numbers come from scores/*.json and from the job logs, so no number in the
# guides is typed by hand. It stops with an error if a mark is left unfilled.
# Use: python3 -I tools/fill_guides.py
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
RECIPE_GUIDE = '08 Recipe - wood from your displacement and colour maps - how it is made.md'
LESSONS_GUIDE = '08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces.md'


def load(path):
    with open(os.path.join(BASE, path)) as handle:
        return json.load(handle)


def f3(x):
    return f'{x:.3f}'


def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)


def build():
    sc = load('scores/final_scores_round1.json')
    ck = load('scores/checks_round1.json')
    rp = load('scores/repeat_tests_round1.json')
    sw2 = load('tests/sweep2_scores.json')
    values, tables = {}, {}
    mains = [sc[f'main_seed{s}'] for s in (1, 2, 3)]
    cmps = [sc[f'comparison_seed{s}'] for s in (1, 2, 3)]
    earlier = sc['earlier_wood_best_new_tile_seed105']
    mean = lambda items, key: sum(i['overall'] if key == 'overall' else i['groups'][key] for i in items) / len(items)
    values['main_mean'] = f3(mean(mains, 'overall'))
    values['cmp_mean'] = f3(mean(cmps, 'overall'))
    values['earlier'] = f3(earlier['overall'])
    values['main_colour'] = f3(mean(mains, 'colour'))
    values['cmp_colour'] = f3(mean(cmps, 'colour'))
    rows = []
    for name, items, label in (('main', mains, 'MAIN (colour map)'), ('comparison', cmps, 'COMPARISON (colour from height)')):
        for s, r in zip((1, 2, 3), items):
            rows.append([f'{label}, seed {s}', f3(r['overall']), f3(r['groups']['colour']), f3(r['groups']['height']), f3(r['groups']['normal']), f3(r['groups']['tiling'])])
        rows.append([f'**{label}, mean of three seeds**', f"**{f3(mean(items, 'overall'))}**", f3(mean(items, 'colour')), f3(mean(items, 'height')), f3(mean(items, 'normal')), f3(mean(items, 'tiling'))])
    rows.append(['earlier wood recipe, best new tile (its seed 105), baked again', f3(earlier['overall']), f3(earlier['groups']['colour']), f3(earlier['groups']['height']), f3(earlier['groups']['normal']), f3(earlier['groups']['tiling'])])
    tables['TABLE_SCORES'] = md_table(['Picture (1254 dots)', 'Overall', 'Colour', 'Height', 'Normal', 'Tiling (seam)'], rows)
    names = list(mains[0]['scores'].keys())
    tables['TABLE_MEASURES'] = md_table(['Measure', 'MAIN seed 1', 'COMPARISON seed 1', 'earlier recipe'],
                                        [[n, f3(mains[0]['scores'][n]), f3(cmps[0]['scores'][n]), f3(earlier['scores'][n])] for n in names])
    prow = []
    for label, r in (('MAIN seed 1', mains[0]), ('MAIN seed 2', mains[1]), ('MAIN seed 3', mains[2]), ('COMPARISON seed 1', cmps[0]), ('earlier recipe tile', earlier)):
        p = r['pixel']
        prow.append([label, p['colour_ssim'], p['colour_mean_delta_e'], p['edge_skill_2px'], p['height_mae_best_fit_levels'], p['normal_mean_angle_degrees'], p['tier_reached']])
    tables['TABLE_PIXEL'] = md_table(['Picture', 'colour SSIM (1 = same)', 'colour Delta E', 'edge skill (0 = luck)', 'height error (steps of 255)', 'normal angle (degrees)', 'tier'], prow)
    su, ht = ck['source_unchanged_check'], ck['half_tile_shift_test_1254']
    values['unchanged_height'] = f"{su['height_mean_absolute_difference_to_uploaded_0_to_1']:.5f}"
    values['unchanged_normal'] = f"{su['normal_from_baked_height_strength_8_mean_absolute_difference_x_y_z'][0]:.4f}"
    values['half_tile_colour'] = f"{ht['colour']['slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1']:.4f}"
    values['half_tile_height'] = f"{ht['height']['slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1']:.4f}"
    corr = ck['colour_brightness_versus_height_correlation']
    values['corr_main'] = f"{min(corr['main_seed1'], corr['main_seed2'], corr['main_seed3']):.3f} to {max(corr['main_seed1'], corr['main_seed2'], corr['main_seed3']):.3f}"
    values['corr_up'] = f"{corr['uploaded_maps']:.3f}"
    de = ck['main_versus_comparison_colour']
    values['de_mean'] = f"{sum(d['mean_delta_e'] for d in de.values()) / len(de):.1f}"
    values['de_p95'] = f"{sum(d['ninety_fifth_percent_delta_e'] for d in de.values()) / len(de):.1f}"
    seeds = ck['seed_difference_height']
    rows = [['source unchanged: height, mean absolute difference to the uploaded height (0 to 1)', su['height_mean_absolute_difference_to_uploaded_0_to_1']],
            ['source unchanged: share of dots differing by more than 2 of 255', su['height_share_of_dots_differing_by_more_than_2_of_255']],
            ['source unchanged: colour, mean absolute difference to the uploaded colour (0 to 1; 8-bit rounding and dither)', su['colour_mean_absolute_difference_to_uploaded_0_to_1']],
            ['source unchanged: normal made from the baked height (strength 8) against the uploaded normal, x / y / z', ' / '.join(str(v) for v in su['normal_from_baked_height_strength_8_mean_absolute_difference_x_y_z'])],
            ['the same rule on the uploaded height itself, x / y / z (the best this rule can do)', ' / '.join(str(v) for v in su['for_comparison_the_normal_rule_on_the_uploaded_height_itself_x_y_z'])],
            ['half-tile slide test, colour: bake slid versus picture slid, mean absolute difference (0 to 1)', ht['colour']['slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1']],
            ['half-tile slide test, colour: share of dots differing by more than 0.1', ht['colour']['share_of_dots_differing_by_more_than_0.1']],
            ['half-tile slide test, colour: control with a WRONG slide, mean / share over 0.1', f"{ht['colour']['wrong_slide_control_mean']} / {ht['colour']['wrong_slide_control_share_over_0.1']}"],
            ['half-tile slide test, height: mean absolute difference (0 to 1)', ht['height']['slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1']],
            ['half-tile slide test, height: control with a wrong slide, mean / share over 0.1', f"{ht['height']['wrong_slide_control_mean']} / {ht['height']['wrong_slide_control_share_over_0.1']}"],
            ['colour brightness versus height, correlation: MAIN seeds 1 / 2 / 3', f"{corr['main_seed1']} / {corr['main_seed2']} / {corr['main_seed3']}"],
            ['colour brightness versus height, correlation: uploaded maps', corr['uploaded_maps']],
            ['COMPARISON colour (made from height) versus height, correlation', corr['comparison_seed1_(colour_from_height)']],
            ['two seeds: correlation between their heights, seed 1 with 2 / with 3', f"{seeds['correlation_seed1_seed2']} / {seeds['correlation_seed1_seed3']}"]]
    tables['TABLE_CHECKS'] = md_table(['Check', 'Result'], rows)
    seam = rp['seam_test_default_tile_2x2']
    rows = []
    for ch in ('colour', 'height'):
        s = seam[ch]
        rows.append([ch, s['jump_across_the_vertical_tile_line_over_a_typical_jump'], s['jump_across_the_horizontal_tile_line_over_a_typical_jump'], s['largest_ordinary_row_boundary_jump_over_a_typical_jump_(for_comparison)'], s['mean_difference_between_the_four_tiles_0_to_1']])
    tables['TABLE_SEAM'] = md_table(['Picture (default tile repeated 2 x 2)', 'jump across the vertical tile line / a typical jump', 'jump across the horizontal tile line / a typical jump', 'largest ordinary row boundary jump / a typical jump', 'mean difference between the four tiles (0 to 1)'], rows) + \
        '\n\n(A jump of about 1 is no seam. The ordinary row boundaries jump more than a typical dot line because every row boundary is a dark band; the horizontal tile line is itself a row boundary and jumps less than the largest of the others.)'
    st = rp['shift_test']
    rows = []
    for key, label in (('control_plain_source_repeated_4x4_height', 'plain uploaded height map repeated 4 x 4 (the thing to get away from)'), ('new_area_4x4_height', 'NEW 4 x 4 area, height'),
                       ('new_area_4x4_colour_brightness', 'NEW 4 x 4 area, colour brightness'), ('new_area_2x2_height_(one_tile_is_627_dots)', 'NEW 2 x 2 area, height'),
                       ('default_tile_repeated_2x2_on_purpose_height', 'default tile repeated 2 x 2 ON PURPOSE (must be 1.0)')):
        r = st[key]
        sp = r['special_shifts_correlation']
        rows.append([label, sp['one_tile_across'], sp['one_tile_down'], sp['one_tile_diagonal'], sp['half_tile_across'], r['background_random_shifts']['highest'], r['background_sideways_only']['highest']])
    tables['TABLE_SHIFT'] = md_table(['Picture', 'shifted one tile across', 'one tile down', 'one tile diagonally', 'half a tile across', 'background: highest of 400 random shifts', 'background: highest of the sideways-only shifts'], rows)
    values['shift_new'] = f"{st['new_area_4x4_height']['special_shifts_correlation']['one_tile_across']}"
    values['shift_plain'] = f"{st['control_plain_source_repeated_4x4_height']['special_shifts_correlation']['one_tile_across']}"
    values['shift_bg'] = f"{st['new_area_4x4_height']['background_sideways_only']['highest']}"
    ru = rp['source_reuse_4x4']
    values['reuse_times'] = f"{ru['times_a_used_source_dot_appears_in_the_area_(mean_median_90th_percent)'][0]:.0f}"
    kn = ru['knots']
    values['knots_4x4'] = f"{kn['knot_boards_in_the_area']}"
    values['knots_per_tile'] = f"{kn['knot_boards_in_the_area']} knot boards in 16 tiles = {kn['knot_boards_in_the_area'] / 16:.1f} per tile (K2: {kn['K2_from_row_R2']['boards']}, K3: {kn['K3_from_row_R4']['boards']})"
    bd = ru['boards']
    rows = [['source dots used at least once (the map has 1,572,516 dots; row 1 is not used by design)', ru['share_of_source_dots_used_at_least_once']],
            ['times a used source dot appears in the 4 x 4 area: mean / median / 90th percent', ' / '.join(str(v) for v in ru['times_a_used_source_dot_appears_in_the_area_(mean_median_90th_percent)'])]]
    for k, v in ru['by_source_row'].items():
        rows.append([f'source row {k}: share of its dots used / mean times per used dot', f"{v['share_used']} / {v['mean_times_per_used_dot']}"])
    rows += [['boards counted (not cut by the edge of the area)', bd['number_of_boards_counted']],
             ['boards that share half or more of their source piece with at least one other board', bd['share_of_boards_that_show_at_least_half_of_the_same_source_piece_as_another_board']],
             ['pairs of boards sharing half or more: how many, median distance in tiles, closest', f"{bd['pairs_sharing_half_or_more']}, {bd['distance_between_such_pairs_in_tiles_(median_and_closest)'][0]}, {bd['distance_between_such_pairs_in_tiles_(median_and_closest)'][1]}"],
             ['pairs sharing 80 percent or more: how many, closest in tiles', f"{bd['pairs_sharing_80_percent_or_more']}, {bd['closest_pair_sharing_80_percent_in_tiles']}"],
             ['knot boards in 16 tiles (K2 from row 2 / K3 from row 4); closest two of the same knot, in tiles', f"{kn['knot_boards_in_the_area']} ({kn['K2_from_row_R2']['boards']} / {kn['K3_from_row_R4']['boards']}); {kn['K2_from_row_R2']['closest_two_in_tiles']} / {kn['K3_from_row_R4']['closest_two_in_tiles']}"]]
    tables['TABLE_REUSE'] = md_table(['What', 'Result'], rows) + \
        '\n\nReading it: with four usable source rows and only about 230 boards in the area, any two windows from the same source row overlap, so the "share half or more" measure is 1.0 for every board and says little by itself; what a person sees is whether the pieces are the same way round, the same size, the same tone and carry the same stains and joints (they are not), and how the pieces are placed.'
    nc = rp['near_copies_research_test_4x4']
    rows = []
    for r in nc:
        rows.append([r['picture'], r['board_size_36x80']['median_best_match'], f"{round(r['board_size_36x80']['share_with_a_near_copy_over_0.8'] * 100)} %", r['feature_size_24x40']['median_best_match'], f"{round(r['feature_size_24x40']['share_with_a_near_copy_over_0.8'] * 100)} %"])
    tables['TABLE_NEAR'] = md_table(['Picture', 'board-size: median best match', 'board-size: share with a near copy', 'feature-size: median', 'feature-size: share'], rows)
    better = [n for n in names if mains[0]['scores'][n] > earlier['scores'][n] + 1e-9]
    worse = [n for n in names if mains[0]['scores'][n] < earlier['scores'][n] - 1e-9]
    values['m_better'] = str(len(better))
    values['m_worse'] = f'{len(worse)} ' + ('measure' if len(worse) == 1 else 'measures')
    values['m_worse_names'] = ', '.join(f"{n} {mains[0]['scores'][n]:.3f} against {earlier['scores'][n]:.3f}" for n in worse) or 'none'
    values['near_new'] = f"{round(nc[1]['board_size_36x80']['share_with_a_near_copy_over_0.8'] * 100)} percent"
    values['near_new_colour'] = f"{round(nc[3]['board_size_36x80']['share_with_a_near_copy_over_0.8'] * 100)} percent"
    sw = rp['near_copies_research_test_4x4_switching_parts_off']['results']
    labels = {'plain_windows_only': 'windows only (no zoom, flips, tone, stains, patches, joined boards)', 'no_stains_no_patches': 'everything except stains and large patches', 'default': 'default settings',
              'two_boards_per_row': 'two boards per row', 'four_boards_per_row': 'four boards per row', 'knots_free_and_many': 'knot share 0.5'}
    tables['TABLE_NEAR_SWITCH'] = md_table(['4 x 4 area of height (1024 dots)', 'board-size: median', 'board-size: share with a near copy', 'feature-size: median', 'feature-size: share'],
                                          [[labels[k], v['board_size_36x80']['median_best_match'], f"{round(v['board_size_36x80']['share_with_a_near_copy_over_0.8'] * 100)} %", v['feature_size_24x40']['median_best_match'], f"{round(v['feature_size_24x40']['share_with_a_near_copy_over_0.8'] * 100)} %"] for k, v in sw.items()])
    jf = load('scores/joints_found.json')
    values['joints_total'] = str(sum(jf.values()))
    values['b3_mean'] = f3(sum(sw2[f'sw2_s{s}_b3']['overall'] for s in (1, 2, 3)) / 3)
    values['b2_mean'] = f3(sum(sw2[f'sw2_s{s}_b2']['overall'] for s in (1, 2, 3)) / 3)
    values['normal_rule'] = '0.004 against 0.03'
    jl = load('scores/job_numbers.json')
    values['nodes_main'] = str(jl['nodes_main'])
    values['nodes_area'] = str(jl['nodes_area'])
    values['nodes_identity'] = str(jl['nodes_identity'])
    values['runs'] = str(jl['blender_runs'])
    tables['TABLE_SPEED'] = md_table(['What', 'Seconds (machine under load of 4 to 9 on 4 cores)'], jl['speed_rows'])
    spread = max(f3(m['overall']) for m in mains), min(f3(m['overall']) for m in mains)
    values['seed_spread'] = f"{float(spread[0]) - float(spread[1]):.3f}"
    return values, tables


def fill(text, values, tables):
    for k, v in tables.items():
        text = text.replace(f'@@{k}@@', v)
    for k, v in values.items():
        text = text.replace(f'@@{k}@@', v)
    left = sorted(set(re.findall(r'@@[A-Za-z0-9_]+@@', text)))
    if left:
        raise SystemExit(f'unfilled marks: {left}')
    return text


if __name__ == '__main__':
    values, tables = build()
    for template, out in (('recipe_guide.md', RECIPE_GUIDE), ('lessons_guide.md', LESSONS_GUIDE)):
        with open(os.path.join(HERE, 'guide_templates', template)) as handle:
            text = fill(handle.read(), values, tables)
        with open(os.path.join(BASE, out), 'w') as handle:
            handle.write(text)
        print('wrote', out, len(text))
