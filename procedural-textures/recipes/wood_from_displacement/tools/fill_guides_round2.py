# What this does (plain words): writes the two guide files of the wood-from-maps job (round 2) from their templates (tools/guide_templates_round2/*.md) by putting the
# measured numbers into the places marked @@NAME@@. The numbers come from scores/*.json and from the job logs, so no number in the guides is typed by hand; the plain
# words around them (what the pictures look like, what I am unsure of) were written by me after looking at the pictures. It stops with an error if a mark is left unfilled.
# Use: python3 -I tools/fill_guides_round2.py
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
TEMPLATES = os.path.join(HERE, 'guide_templates_round2')
RECIPE_GUIDE = '08 Recipe - wood from your displacement and colour maps - how it is made.md'
LESSONS_GUIDE = '08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces.md'


def load(path, default=None):
    p = os.path.join(BASE, path)
    if not os.path.exists(p):
        return default if default is not None else {}
    with open(p) as handle:
        return json.load(handle)


def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return '\n'.join(out)


def f3(x):
    return 'n/a' if x is None else f'{x:.3f}'


def pct(x):
    return 'n/a' if x is None else f'{100.0 * x:.0f} %'


def get(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


def build():
    sc = load('scores/final_scores_round2.json')
    ck = load('scores/checks_round2.json')
    rp = load('scores/repeat_tests_round2.json')
    r1c = load('scores/checks_round1.json')
    r1r = load('scores/repeat_tests_round1.json')
    jn = load('scores/job_numbers_round2.json')
    jf = load('scores/joints_found_round2.json')
    V, T = {}, {}
    mains = [sc.get(f'main_seed{s}') for s in (1, 2, 3)]
    cmps = [sc.get(f'comparison_seed{s}') for s in (1, 2, 3)]
    earlier = sc.get('earlier_wood_best_new_tile_seed105')
    r1 = sc.get('round1_for_before_and_after', {})

    def mean(items, key):
        vals = [(i['overall'] if key == 'overall' else i['groups'][key]) for i in items if i]
        return sum(vals) / len(vals) if vals else None

    def r1mean(prefix, key):
        vals = [(r1[f'{prefix}_seed{s}']['overall'] if key == 'overall' else r1[f'{prefix}_seed{s}']['groups'][key]) for s in (1, 2, 3) if f'{prefix}_seed{s}' in r1]
        return sum(vals) / len(vals) if vals else None
    V['main_mean'] = f3(mean(mains, 'overall'))
    V['cmp_mean'] = f3(mean(cmps, 'overall'))
    V['earlier'] = f3(earlier['overall'] if earlier else None)
    V['r1_main_mean'] = f3(r1mean('main', 'overall'))
    V['r1_cmp_mean'] = f3(r1mean('comparison', 'overall'))
    V['nodes_tile'], V['nodes_area'], V['nodes_identity'] = jn.get('nodes_main', '?'), jn.get('nodes_area', '?'), jn.get('nodes_identity', '?')

    # ---- 7.1 score table
    rows = []
    for kind, items, title in (('main', mains, 'MAIN (colour map)'), ('comparison', cmps, 'COMPARISON (colour from height)')):
        for s, it in enumerate(items, 1):
            if it:
                g = it['groups']
                rows.append([f'{title}, seed {s}', f3(it['overall']), f3(g['colour']), f3(g['height']), f3(g['normal']), f3(g['tiling'])])
        rows.append([f'**{title}, mean of three seeds, round 2**', f'**{f3(mean(items, "overall"))}**', f3(mean(items, 'colour')), f3(mean(items, 'height')), f3(mean(items, 'normal')), f3(mean(items, 'tiling'))])
        rows.append([f'{title}, mean of three seeds, round 1 (for comparison)', f3(r1mean(kind, 'overall')), f3(r1mean(kind, 'colour')), f3(r1mean(kind, 'height')), f3(r1mean(kind, 'normal')), f3(r1mean(kind, 'tiling'))])
    if earlier:
        g = earlier['groups']
        rows.append(['earlier wood recipe, best new tile (its seed 105), baked again', f3(earlier['overall']), f3(g['colour']), f3(g['height']), f3(g['normal']), f3(g['tiling'])])
    T['SCORES_TABLE'] = md_table(['Picture (1254 dots)', 'Overall', 'Colour', 'Height', 'Normal', 'Tiling (seam)'], rows)

    # ---- 7.1 measures table (seed 1)
    if mains[0] and cmps[0] and earlier:
        names = list(mains[0]['scores'].keys())
        T['MEASURES_TABLE'] = md_table(['Measure', 'MAIN seed 1', 'COMPARISON seed 1', 'earlier recipe'], [[n, f3(mains[0]['scores'][n]), f3(cmps[0]['scores'][n]), f3(earlier['scores'][n])] for n in names])
        better = sum(1 for n in names if mains[0]['scores'][n] > earlier['scores'][n] + 0.005)
        worse = [n for n in names if mains[0]['scores'][n] < earlier['scores'][n] - 0.005]
        V['measures_better'], V['measures_total'] = better, len(names)
        V['measures_worse'] = ', '.join(f"{n} {f3(mains[0]['scores'][n])} against {f3(earlier['scores'][n])}" for n in worse) or 'none'
        V['seam_main1'] = f3(mains[0]['facts'].get('seam_ratio_candidate'))
        V['seam_ref'] = f3(mains[0]['facts'].get('seam_ratio_reference'))
    # ---- pixel table (both height numbers, labelled)
    prow = []
    for key, title in (('main_seed1', 'MAIN seed 1'), ('main_seed2', 'MAIN seed 2'), ('main_seed3', 'MAIN seed 3'), ('comparison_seed1', 'COMPARISON seed 1'), ('earlier_wood_best_new_tile_seed105', 'earlier recipe tile')):
        it = sc.get(key)
        if it and 'pixel' in it and 'colour_ssim' in it['pixel']:
            p = it['pixel']
            prow.append([title, p['colour_ssim'], p['colour_mean_delta_e'], p['edge_skill_2px'], p['height_mae_levels'], p['height_mae_best_fit_levels'], p['normal_mean_angle_degrees'], p['tier_reached']])
    T['PIXEL_TABLE'] = md_table(['Picture', 'colour SSIM (1 = same)', 'colour Delta E', 'edge skill (0 = luck)', 'height error, plain (steps of 255)', 'height error after best fit (a flat grey: the same for all, says nothing)', 'normal angle (degrees)', 'tier'], prow)

    # ---- 7.2 pipeline and tile checks
    su = ck.get('source_unchanged_check', {})
    hs = ck.get('half_tile_shift_test_1254', {})
    rows = [['source unchanged: height, mean absolute difference to the uploaded height (0 to 1)', su.get('height_mean_absolute_difference_to_uploaded_0_to_1')],
            ['source unchanged: share of dots differing by more than 2 of 255', su.get('height_share_of_dots_differing_by_more_than_2_of_255')],
            ['source unchanged: colour, mean absolute difference to the uploaded colour (0 to 1; 8-bit rounding and dither)', su.get('colour_mean_absolute_difference_to_uploaded_0_to_1')],
            ['source unchanged: normal made from the baked height (strength 8) against the uploaded normal, x / y / z', ' / '.join(str(v) for v in su.get('normal_from_baked_height_strength_8_mean_absolute_difference_x_y_z', []))],
            ['the same rule on the uploaded height itself, x / y / z (the best this rule can do)', ' / '.join(str(v) for v in su.get('for_comparison_the_normal_rule_on_the_uploaded_height_itself_x_y_z', []))]]
    for ch in ('colour', 'height'):
        h = hs.get(ch, {})
        rows += [[f'half-tile slide test, {ch}: bake slid versus picture slid, mean absolute difference (0 to 1)', h.get('slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1')],
                 [f'half-tile slide test, {ch}: share of dots differing by more than 0.1', h.get('share_of_dots_differing_by_more_than_0.1')],
                 [f'half-tile slide test, {ch}: control with a WRONG slide, mean / share over 0.1', f"{h.get('wrong_slide_control_mean')} / {h.get('wrong_slide_control_share_over_0.1')}"]]
    corr = ck.get('colour_brightness_versus_height_correlation', {})
    rows += [['colour brightness versus height, correlation: MAIN seeds 1 / 2 / 3', ' / '.join(str(corr.get(f'main_seed{s}')) for s in (1, 2, 3))],
             ['colour brightness versus height, correlation: uploaded maps', corr.get('uploaded_maps')],
             ['COMPARISON colour (made from height) versus height, correlation', corr.get('comparison_seed1_(colour_from_height)')]]
    sd = ck.get('seed_difference_height', {})
    rows += [['two seeds: correlation between their heights, seed 1 with 2 / 1 with 3 / 2 with 3', f"{sd.get('correlation_seed1_seed2')} / {sd.get('correlation_seed1_seed3')} / {sd.get('correlation_seed2_seed3')}"]]
    sq = ck.get('window_squeeze_check_seed1_tile', {})
    if sq:
        rows += [['how much of the source one picture dot covers across the grain: 1st / 5th / 25th / 50th / 75th / 95th percentile of 15-dot blocks (1 = as the source)', ' / '.join(str(v) for v in sq['source_dots_per_picture_dot_across_the_grain_percentiles_1_5_25_50_75_95'])],
                 ['share of 15-dot blocks where the source is magnified more than 1.7 times across the grain (blurred or smeared)', sq['share_of_blocks_across_under_0.6_(magnified_and_blurred)']]]
    T['PIPELINE_TABLE'] = md_table(['Check', 'Result'], [[a, b] for a, b in rows])
    wj = ck.get('tile_wrap_edge_jumps', {})
    erows = []
    for k, v in wj.items():
        erows.append([k.replace('_', ' '), v['left_right_wrap_jump_over_a_typical_jump'], v['top_bottom_wrap_jump_over_a_typical_jump']])
    T['EDGE_TABLE'] = md_table(['Default tile (the jump from its last dot line to its first, over a typical jump between neighbouring dot lines)', 'left-right', 'top-bottom'], erows)
    ev = ck.get('tile_edge_versus_ordinary_row_boundaries_colour', {})
    erows2 = []
    for k, v in ev.items():
        ords = v['jumps_across_the_four_strongest_ordinary_row_boundaries_inside_the_tile_(y_position, jump)']
        erows2.append([k.replace('seed', 'seed '), v['jump_across_the_tile_edge_over_a_typical_jump'], ' / '.join(str(j) for _, j in ords)])
    T['EDGE_VS_ROW_TABLE'] = md_table(['Colour of the default tile', 'jump across the tile edge (wrap-around)', 'jumps across the four strongest ordinary row boundaries inside the same tile'], erows2)
    st = rp.get('seam_test_default_tile_2x2', {})
    srows = [[ch, v.get('jump_across_the_vertical_tile_line_over_a_typical_jump'), v.get('jump_across_the_horizontal_tile_line_over_a_typical_jump'),
              v.get('largest_ordinary_row_boundary_jump_over_a_typical_jump_(for_comparison)'), v.get('mean_difference_between_the_four_tiles_0_to_1')] for ch, v in st.items()]
    T['SEAM2X2_TABLE'] = md_table(['Picture (default tile repeated 2 x 2)', 'jump across the vertical tile line / a typical jump', 'jump across the horizontal tile line / a typical jump', 'largest ordinary row boundary jump / a typical jump', 'mean difference between the four tiles (0 to 1)'], srows)

    # ---- 7.3 big area
    sh = rp.get('shift_test', {})
    rows = []
    for key, v in sh.items():
        s_ = v['special_shifts_correlation']
        rows.append([v['picture'], s_['one_tile_across'], s_['one_tile_down'], s_['one_tile_diagonal'], s_['half_tile_across'], v['background_random_shifts_highest'], v['background_sideways_only_highest']])
    T['SHIFT_TABLE'] = md_table(['Picture', 'shifted one tile across', 'one tile down', 'one tile diagonally', 'half a tile across', 'background: highest of 300 random shifts', 'background: highest of the sideways-only shifts'], rows)
    sr = rp.get('source_reuse_and_neighbours_4x4', {})
    tp = sr.get('touching_pairs', {})
    rr = r1r.get('source_reuse_4x4', {})
    T['REUSE_TABLE'] = md_table(['What', 'round 2', 'round 1'], [
        ['source dots used at least once (the map has 1,572,516 dots; row 1 is not used by design)', sr.get('source_dots_used_at_least_once'), rr.get('share_of_source_dots_used_at_least_once')],
        ['times a used source dot appears in the 4 x 4 area: mean / median / 90th percent', ' / '.join(str(v) for v in sr.get('times_a_used_source_dot_appears_mean_median_90th', [])), ' / '.join(str(v) for v in rr.get('times_a_used_source_dot_appears_in_the_area_(mean_median_90th_percent)', []))],
        ['boards counted in 16 tiles', sr.get('boards_counted'), get(rr, 'boards', 'number_of_boards_counted')],
        ['board length in tiles: median / 90th percent', ' / '.join(str(v) for v in sr.get('board_length_in_tiles_median_and_90th_percent', [])), 'about 0.33 (3 per row, half of the pairs joined)'],
        ['touching board pairs (side by side, above and below)', tp.get('all_touching_pairs'), ''],
        ['share of touching pairs that take the SAME source row', tp.get('share_of_all_touching_pairs_with_the_same_source_row'), '0.19 (the honesty checker measured it; the round 1 guide claimed 0)'],
        ['touching pairs with the same source row AND half or more of the same stretch of it', tp.get('touching_pairs_with_the_same_source_row_AND_half_or_more_of_the_same_source_stretch'), 'about 14 mirrored + 10 repeated of 387 (honesty checker)']])
    lc = rp.get('landmarks_shown_in_the_4x4_area') or {}
    rows = [[k, v['times_shown_in_16_tiles'], v['pairs_closer_than_one_tile']] for k, v in lc.items() if not k.startswith('_')]
    if rows:
        rows.append(['**all twelve landmarks together**', lc.get('_total_shown_in_16_tiles'), ''])
    T['LANDMARK_TABLE'] = md_table(['Landmark', 'times it is shown in the 4 x 4 area (16 tiles)', 'pairs of showings less than one tile apart'], rows)
    V['landmarks_total'] = lc.get('_total_shown_in_16_tiles', '?')
    knots = sum(lc.get(k, {}).get('times_shown_in_16_tiles', 0) for k in ('knot K2', 'knot K3', 'knot K4')) if lc else '?'
    V['knots_total'] = knots
    nc = rp.get('near_copies', {})
    rows = []
    for key, v in nc.items():
        if key.startswith('research_test'):
            rows.append([key.replace('research_test_', 'research test ').replace('_', ' '), v['median_best_match'], pct(v['share_with_a_near_copy_over_0.8'])])
    T['NEAR_RESEARCH_TABLE'] = md_table(['Picture (research test: pieces searched for in the other rows, also flipped)', 'median best match', 'share with a near copy (over 0.8)'], rows)
    rows = []
    for key, v in nc.items():
        if key.startswith('look_checker_test'):
            rows.append([key.replace('look_checker_test_200x380_dots_', '').replace('_', ' '), v['pieces'], v['median'], pct(v['share_over_0.6']), pct(v['share_over_0.7']), pct(v['share_over_0.8'])])
    T['NEAR_CHECKER_TABLE'] = md_table(['Picture (the look checker\'s test: pieces of 200 x 380 dots searched everywhere, all four ways round)', 'pieces', 'median best match', 'share over 0.6', 'share over 0.7', 'share over 0.8'], rows)
    sw = get(rp, 'near_copies_switching_parts_off', 'results') or {}
    titles = {'default': 'default settings', 'no_landmark_painting': 'landmarks all shown (nothing painted out)', 'no_bending_no_stretch': 'no bending, tilt or stretch of the windows',
              'windows_only': 'windows only (no bending, stretch, flips, stains, patches; landmarks shown)', 'three_boards_per_row': 'three boards per row'}
    rows = []
    for k in ('default', 'no_landmark_painting', 'no_bending_no_stretch', 'windows_only', 'three_boards_per_row'):
        if k in sw:
            v = sw[k]
            lcs = v.get('look_checker_test') or {}
            rows.append([titles[k], v['research_test_36x80']['median_best_match'], pct(v['research_test_36x80']['share_with_a_near_copy_over_0.8']), lcs.get('median', 'n/a'), pct(lcs.get('share_over_0.6')) if lcs else 'n/a', pct(lcs.get('share_over_0.7')) if lcs else 'n/a'])
    T['SWITCH_TABLE'] = md_table(['4 x 4 area of height (1024 dots)', 'research test: median', 'research test: share over 0.8', 'checker test: median', 'checker test: share over 0.6', 'checker test: share over 0.7'], rows)
    ft = rp.get('first_tile_of_the_area_versus_the_default_tile', {})
    V['first_tile_corr'] = ft.get('top_left_tile_of_the_area_versus_the_default_tile_of_the_same_seed_correlation', '?')
    V['other_tiles_corr'] = ft.get('other_tiles_of_the_area_versus_the_default_tile_correlation_highest', '?')

    # ---- 7.4 joints
    V['joint_parts'] = ' / '.join(str(get(jf, f'seed{s}', 'joint_parts_at_least_25_dots_tall', default='?')) for s in (1, 2, 3))
    V['joint_crops'] = ' / '.join(str(get(jf, f'seed{s}', 'crops_on_the_sheet', default='?')) for s in (1, 2, 3))
    # ---- 7.5 colour
    mc = ck.get('main_versus_comparison_colour', {})
    rows = []
    for s in (1, 2, 3):
        v = mc.get(f'seed{s}')
        if v:
            rows.append([f'seed {s}', v['mean_delta_e'], v['ninety_fifth_percent_delta_e'], ' / '.join(str(x) for x in v['mean_colour_main_0_255']), ' / '.join(str(x) for x in v['mean_colour_comparison_0_255']),
                         f"{v['share_of_dots_more_blue_than_red_main_versus_comparison'][0]} / {v['share_of_dots_more_blue_than_red_main_versus_comparison'][1]}"])
    up = mc.get('uploaded_colour_map_for_comparison_mean_colour_0_255_and_share_more_blue_than_red')
    if up:
        rows.append(['uploaded colour map', '', '', ' / '.join(str(x) for x in up[0]), '', up[1]])
    T['COLOUR_TABLE'] = md_table(['', 'mean Delta E MAIN vs COMPARISON', '95th percent Delta E', 'mean colour MAIN (red / green / blue, 0 to 255)', 'mean colour COMPARISON', 'share of dots more blue than red (MAIN / COMPARISON)'], rows)
    # ---- speed
    if jn.get('speed_rows'):
        T['SPEED_TABLE'] = md_table(['What', 'Seconds (machine shared with two other helpers, load 4 to 9 on 4 cores, 2 threads)'], jn['speed_rows'])
    else:
        T['SPEED_TABLE'] = '(speed numbers not collected)'
    V['blender_runs'] = jn.get('blender_runs', '?')

    # numbers for the near-copy narrative
    def share(key, field='share_over_0.7'):
        return get(nc, key, field)
    V['chk_new_07'] = pct(share('look_checker_test_200x380_dots_new_area_height_50_pieces'))
    V['chk_new_07b'] = pct(share('look_checker_test_200x380_dots_new_area_height_other_draw'))
    V['chk_old_07'] = pct(share('look_checker_test_200x380_dots_ROUND_1_area_height'))
    V['chk_old_07b'] = pct(share('look_checker_test_200x380_dots_ROUND_1_area_height_other_draw'))
    V['chk_new_06'] = pct(share('look_checker_test_200x380_dots_new_area_height_50_pieces', 'share_over_0.6'))
    V['chk_old_06'] = pct(share('look_checker_test_200x380_dots_ROUND_1_area_height', 'share_over_0.6'))
    V['res_new'] = pct(get(nc, 'research_test_36x80_new_area_height', 'share_with_a_near_copy_over_0.8'))
    V['res_old'] = pct(get(nc, 'research_test_36x80_ROUND_1_area_height', 'share_with_a_near_copy_over_0.8'))
    V['same_row_share'] = pct(tp.get('share_of_all_touching_pairs_with_the_same_source_row'))
    V['reuse_mean'] = get(sr, 'times_a_used_source_dot_appears_mean_median_90th', default=['?'])[0]
    one = get(sh, 'new_area_4x4_height', 'special_shifts_correlation', 'one_tile_across')
    V['shift_new'] = one
    V['shift_control'] = get(sh, 'control_plain_source_repeated_4x4_height_(exact_whole_dots)', 'special_shifts_correlation', 'one_tile_across')
    V['shift_bg'] = get(sh, 'new_area_4x4_height', 'background_sideways_only_highest')
    V['slide_colour'] = get(hs, 'colour', 'slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1')
    V['slide_height'] = get(hs, 'height', 'slid_bake_versus_slid_picture_mean_absolute_difference_0_to_1')
    V['src_h'] = su.get('height_mean_absolute_difference_to_uploaded_0_to_1')
    V['src_n'] = ' / '.join(str(v) for v in su.get('normal_from_baked_height_strength_8_mean_absolute_difference_x_y_z', []))
    V['corr_main'] = ' / '.join(str(corr.get(f'main_seed{s}')) for s in (1, 2, 3))
    V['corr_up'] = corr.get('uploaded_maps')
    V['wrap_tb'] = get(wj, 'seed1_colour', 'top_bottom_wrap_jump_over_a_typical_jump')
    V['wrap_lr'] = get(wj, 'seed1_colour', 'left_right_wrap_jump_over_a_typical_jump')
    V['wrap_tb_up'] = get(wj, 'uploaded_height_for_comparison', 'top_bottom_wrap_jump_over_a_typical_jump')
    V['wrap_lr_up'] = get(wj, 'uploaded_height_for_comparison', 'left_right_wrap_jump_over_a_typical_jump')
    V['squeeze_share'] = get(sq, 'share_of_blocks_across_under_0.6_(magnified_and_blurred)')
    for k, name in (('default', 'def'), ('no_landmark_painting', 'nolm'), ('no_bending_no_stretch', 'nobend'), ('windows_only', 'wo'), ('three_boards_per_row', 'three')):
        v = (sw.get(k) or {}).get('look_checker_test') or {}
        V[f'sw_{name}_06'], V[f'sw_{name}_07'] = pct(v.get('share_over_0.6')), pct(v.get('share_over_0.7'))
        V[f'sw_{name}_med'] = v.get('median', 'n/a')
    nb = load('scores/neighbour_count_default_tile_seed1.json')
    V['tile_same_pairs'], V['tile_pairs'] = nb.get('same_source_row', '?'), nb.get('touching_pairs', '?')
    V['tile_edge_same'], V['tile_edge_pairs'] = nb.get('of_which_same_source_row', '?'), nb.get('pairs_across_the_tile_edge_top_bottom', '?')
    V['board_length'] = get(sr, 'board_length_in_tiles_median_and_90th_percent', default=['?'])[0]
    V['cmp_colour_now'] = f3(mean(cmps, 'colour'))
    V['cmp_colour_before'] = f3(r1mean('comparison', 'colour'))
    V['touching_all'] = tp.get('all_touching_pairs', '?')
    V['twin_pairs'] = tp.get('touching_pairs_with_the_same_source_row_AND_half_or_more_of_the_same_source_stretch', '?')
    tl = [it['groups']['tiling'] for it in mains if it]
    V['tiling_range'] = f"{min(tl):.2f} to {max(tl):.2f}" if tl else '?'
    V['seeds_corr'] = f"{sd.get('correlation_seed1_seed2')} / {sd.get('correlation_seed1_seed3')} / {sd.get('correlation_seed2_seed3')}"
    V['cmp_de'] = get(mc, 'seed1', 'mean_delta_e')
    V['cmp_de95'] = get(mc, 'seed1', 'ninety_fifth_percent_delta_e')
    for s in (1, 2, 3):
        for kind in ('main', 'comparison'):
            it = sc.get(f'{kind}_seed{s}')
            if it:
                V[f'{kind}{s}'] = f3(it['overall'])
    return V, T


def fill(text, V, T, extra):
    def repl(m):
        name = m.group(1)
        for src in (extra, T, V):
            if name in src:
                return str(src[name])
            if name.lower() in src:                      # the templates may write a number's name in capitals
                return str(src[name.lower()])
        raise KeyError(f'unfilled mark @@{name}@@')
    out = re.sub(r'@@([A-Za-z0-9_]+)@@', repl, text)
    return out


def main():
    V, T = build()
    extra = {}

    def read(name):
        p = os.path.join(TEMPLATES, name)
        if os.path.exists(p):
            with open(p) as handle:
                return handle.read()
        return ''
    extra['SWITCH_READING'] = fill(read('switch_reading.md'), V, T, {})
    extra['LIT_READING'] = fill(read('lit_reading.md'), V, T, {})
    parts = [read(f'results_part{i}.md') for i in (1, 2, 3)]
    extra['RESULTS'] = fill('\n\n'.join(p for p in parts if p), V, T, extra)
    for name in ('RESULT_PAGE', 'ROUND2_DEAD_ENDS', 'NOT_TESTED', 'ROUND2'):
        extra[name] = fill(read(f'{name.lower()}.md'), V, T, {})
    with open(os.path.join(TEMPLATES, 'recipe_part_a.md')) as handle:
        recipe = fill(handle.read(), V, T, extra)
    with open(os.path.join(BASE, RECIPE_GUIDE), 'w') as handle:
        handle.write(recipe)
    with open(os.path.join(TEMPLATES, 'lessons_guide.md')) as handle:
        lessons = fill(handle.read(), V, T, {})
    with open(os.path.join(BASE, LESSONS_GUIDE), 'w') as handle:
        handle.write(lessons)
    print('wrote both guides;', len(recipe), 'and', len(lessons), 'characters')


if __name__ == '__main__':
    main()
