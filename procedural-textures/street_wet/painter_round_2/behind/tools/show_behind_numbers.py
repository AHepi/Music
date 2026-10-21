"""What this file does (plain words): prints the key numbers of numbers/<TAG>_measurements.json in a short table, so two versions of the behind painting can be compared quickly.
Run: python3 -I tools/show_behind_numbers.py TAG [--full]"""
import json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(HERE, 'numbers', sys.argv[1] + '_measurements.json')))
print('picture:', d['picture_measured'])
for sec in ('1_match_on_the_parts_visible_in_both', '1b_match_in_the_ring_round_the_props'):
    print('\n' + sec)
    print(f"  {'surface':32s} {'dots':>8s} {'front':>6s} {'behind':>6s} {'diff':>6s} {'ratio':>5s} {'blurMAD':>7s} {'corr':>5s} {'b-r F':>6s} {'b-r B':>6s} {'glintF':>6s} {'glintB':>6s}")
    for cl, row in d[sec].items():
        if 'behind_vs_front' not in row:
            print('  ', cl, row); continue
        a = row['behind_vs_front']
        print(f"  {cl:32s} {row['dots']:8d} {a['mean_brightness_front_or_painting']:6.3f} {a['mean_brightness_behind']:6.3f} {a['difference_behind_minus_front']:+6.3f} {a['ratio_behind_over_front']:5.2f} {a['mean_absolute_difference_blurred_sigma4']:7.3f} {a['correlation_blurred_sigma4']:5.2f} {a['blue_minus_red_front']:+6.3f} {a['blue_minus_red_behind']:+6.3f} {a['glint_share_front']:6.3f} {a['glint_share_behind']:6.3f}")
k2 = [k for k in d if k.startswith('2_')][0]
print('\n2. where the props stood vs the common ground round it  (ratio ~1 = as bright as its surroundings)')
for pic, row in d[k2].items():
    if pic == 'note': continue
    for n, r in row.items():
        print(f"  {pic:3s} {n:18s} dots {r['dots']:7d}  where {r['mean_brightness_where_props_stood']:.3f}  round {r['mean_brightness_of_the_common_ground_round_it']:.3f}  ratio {r['ratio_brightness_where_stood_over_round_it']:.2f}  b-r {r['blue_minus_red_where_stood']:+.3f} (round {r['blue_minus_red_round_it']:+.3f})  glint {r['glint_share_where_stood']:.3f} (round {r['glint_share_on_the_common_ground_within_60_dots_of_it']:.3f})")
print('\n3. ghost props: (edge strength along the removed prop\'s outline / on the ground 12-28 dots away), divided by the same for the props-free plate. 1 = no outline left; F = the front picture that has the prop (must be well above 1)')
for g, row in d['3_ghost_props_edge_strength_along_the_removed_props_outlines'].items():
    print(f"  {g:12s} B {row['ghost_excess_B']:.2f}   old dry behind {row['ghost_excess_OB']:.2f}   front painting (prop there) {row['ghost_excess_F']:.2f}")
print('\n3b. ground where props stood darker/brighter than round it by 0.10 (blurred):')
for pic, r in d['3b_ground_where_props_stood_much_darker_or_brighter_than_the_ground_round_it_(blurred)'].items():
    print('  ', pic, {k: round(v, 3) for k, v in r.items()})
print('\n4. rubbish blobs')
for n, r in d['4_rubbish_blobs'].items():
    print(f"  {n:24s} dots {r['ground_dots']:8d} plate {r['plate_blobs_per_100k']:6.1f}/100k  painting {r['behind_painting_blobs_per_100k']:6.1f}/100k  kept {r['kept_share_of_plate_blobs_found_in_the_painting_within_7_dots']:.2f} (chance {r['chance_level_(painting_shifted_60_dots)']:.2f})  added {r['added_share_of_painting_blobs_with_no_plate_blob_within_7_dots']:.2f} (chance {r['chance_level_for_added_share']:.2f})")
print('  front painting blobs per 100k on C:', round(d['4b_front_painting_blobs_per_100k_on_C_(for_comparison)'], 1))
print('\n5. joints (line / texture)')
for pic, r in d[[k for k in d if k.startswith('5_')][0]].items():
    print('  ', pic, {k: {n: (x['line'], x['texture']) for n, x in v.items()} for k, v in r.items()})
print('\n6. sky', {k: round(v, 3) for k, v in d['6_sky_(B_against_F_inside_the_sky_mask)'].items()})
w = d['7_whole_picture']
print('7. mean brightness not sky', {k: round(v, 3) for k, v in w['not_sky_mean_brightness'].items()})
print('   glare/road', json.dumps(w['glare_pool_and_road_brightness']))
print('   lamp glass RGB', w['lamp_left_glass_RGB_(brightest_tenth_of_the_head)'])
