# What this does: re-reads numbers that the guides quote, straight from the files the guides name (final_report.json, verifier_answer.json,
# scores/*.json and the cookbook's own check files), rounds them the way the guide wrote them, and says for each one whether the guide's number
# matches (a file number counts as matching when it rounds half up to the guide's number). Writes number_checks.json next to this script and prints one line per check.
# Usage (from anywhere): python3 -I number_checks.py
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', '..', '..'))      # proc-work
R = os.path.join(P, 'recipes')
C = os.path.join(P, 'cookbook', 'checks')


def load(*parts):
    with open(os.path.join(*parts)) as handle:
        return json.load(handle)


fr = {s: load(R, s, 'final_report.json') for s in ('brick', 'slate', 'wood', 'metal', 'mud', 'gravel')}
gravel_classes = {row['class_name']: row for row in fr['gravel']['classes']}
brick_rd = {row['tag']: row for row in fr['brick']['rate_distortion']}
metal_var = [fr['metal']['variation'][str(i)]['texture_overall'] for i in range(1, 9)]
gravel_var = [t['texture_overall'] for t in fr['gravel']['variation']['tiles'].values()]
gravel_view = [t['texture_view_overall'] for t in fr['gravel']['variation']['tiles'].values()]
mud_rows = fr['mud']['mud']
self_tests = load(C, 'baking_and_checking', 'self_tests.json')
flat = load(C, 'baking_and_checking', 'flat_baselines.json')
smooth = load(C, 'baking_and_checking', 'smoothed_height_check.json')

# (guide, what the guide says, the number as the guide writes it, the number from the file, the file)
checks = [
    ('start here 1', 'slate S0 bytes', 2762, fr['slate']['classes']['S0_layout_only']['bytes'], 'slate/final_report.json'),
    ('start here 1', 'slate S0 colour SSIM', 0.711, round(fr['slate']['classes']['S0_layout_only']['colour_ssim'], 3), 'slate/final_report.json'),
    ('start here 1', 'slate S2 same-kind', 0.725, fr['slate']['classes']['S2_stamps_grain']['texture_compare_overall_as_baked'], 'slate/final_report.json'),
    ('start here 1', 'slate L fine bytes', 453054, fr['slate']['classes']['L_trace_fine']['bytes'], 'slate/final_report.json'),
    ('start here 1', 'slate L fine SSIM', 0.836, round(fr['slate']['classes']['L_trace_fine']['colour_ssim'], 3), 'slate/final_report.json'),
    ('start here 1', 'slate new tiles lowest', 0.722, fr['slate']['variations']['texture_overall_range'][0], 'slate/final_report.json'),
    ('start here 1', 'slate new tiles highest', 0.753, fr['slate']['variations']['texture_overall_range'][1], 'slate/final_report.json'),
    ('start here 5', 'brick L bytes', 508878, fr['brick']['classes']['L']['description_bytes'], 'brick/final_report.json'),
    ('start here 5', 'brick L normal error', 13.93, fr['brick']['classes']['L']['normal_mean_angle_degrees'], 'brick/final_report.json'),
    ('start here 5', 'brick S same-kind', 0.365, fr['brick']['classes']['S']['texture_compare_overall'], 'brick/final_report.json'),
    ('start here 5', 'brick new tiles mean', 0.708, round(fr['brick']['variation']['texture_overall_mean'], 3), 'brick/final_report.json'),
    ('start here 5', 'wood L3 edge skill', 0.523, fr['wood']['classes']['L3_trace_480k']['edge_skill_2px'], 'wood/final_report.json'),
    ('start here 5', 'wood S1 SSIM', 0.220, round(fr['wood']['classes']['S1_layout_paint_grain']['colour_ssim'], 3), 'wood/final_report.json'),
    ('start here 5', 'wood new tiles mean', 0.626, fr['wood']['variation']['texture_compare_mean'], 'wood/final_report.json'),
    ('start here 5', 'metal L bytes', 413452, fr['metal']['classes']['L']['description_bytes'], 'metal/final_report.json'),
    ('start here 5', 'metal L colour difference', 4.90, fr['metal']['classes']['L']['colour_mean_delta_e'], 'metal/final_report.json'),
    ('start here 5', 'metal new tiles mean', 0.569, round(sum(metal_var) / 8, 3), 'metal/final_report.json'),
    ('start here 5', 'metal new tiles lowest', 0.525, min(metal_var), 'metal/final_report.json'),
    ('start here 5', 'mud L final bytes', 503014, mud_rows['L_final_traced_ground_plus_corrections']['description_bytes'], 'mud/final_report.json'),
    ('start here 5', 'mud L final normal error', 18.59, mud_rows['L_final_traced_ground_plus_corrections']['normal_mean_angle_degrees'], 'mud/final_report.json'),
    ('start here 5', 'mud new tiles mean', 0.383, fr['mud']['variation']['summary']['kind_score_mean'], 'mud/final_report.json'),
    ('start here 5', 'gravel L KB', 426.16, gravel_classes['L_a100_s8']['description_kb'], 'gravel/final_report.json'),
    ('start here 5', 'gravel L normal error', 22.33, gravel_classes['L_a100_s8']['normal_mean_angle'], 'gravel/final_report.json'),
    ('start here 5', 'gravel new tiles mean', 0.403, round(sum(gravel_var) / 8, 3), 'gravel/final_report.json'),
    ('descriptions 1', 'gravel new tiles mean, smoothed-height view', 0.457, round(sum(gravel_view) / 8, 3), 'gravel/final_report.json'),
    ('descriptions 3.2', 'brick R1 colour difference', 12.68, brick_rd['R1']['colour_mean_delta_e'], 'brick/final_report.json'),
    ('descriptions 3.2', 'brick L + grain 0.14 same-kind', 0.598, brick_rd['L + grain 0.14']['texture_overall'], 'brick/final_report.json'),
    ('descriptions 3.2', 'metal R256k bytes (first "close")', 261188, fr['metal']['rate_distortion']['R256k']['description_bytes'], 'metal/final_report.json'),
    ('descriptions 3.2 (fixed)', 'mud L -> L final SSIM gain', 0.009, round(mud_rows['L_final_traced_ground_plus_corrections']['colour_ssim'] - mud_rows['L_traced_ground_5000_patches']['colour_ssim'], 3), 'mud/final_report.json'),
    ('descriptions 3.2 (fixed)', 'mud L2 -> L SSIM gain', 0.056, round(mud_rows['L_traced_ground_5000_patches']['colour_ssim'] - mud_rows['L2_traced_ground_2000_patches']['colour_ssim'], 3), 'mud/final_report.json'),
    ('descriptions 4 (fixed)', 'metal M seam number', 1.33, load(R, 'metal', 'scores', 'M_texture.json')['facts']['seam_ratio_candidate'], 'metal/scores/M_texture.json'),
    ('descriptions 4 (fixed)', 'metal L seam number', 1.38, load(R, 'metal', 'scores', 'L_texture.json')['facts']['seam_ratio_candidate'], 'metal/scores/L_texture.json'),
    ('descriptions 4', 'brick L seam number', 2.11, load(R, 'brick', 'scores', 'final_L_texture.json')['facts']['seam_ratio_candidate'], 'brick/scores/final_L_texture.json'),
    ('descriptions 7', 'gravel area bake seconds (checker)', 252.6, load(R, 'gravel', 'area', 'out', 'area_2508', 'bake.json')['total_s'], 'gravel/area/out/area_2508/bake.json'),
    ('baking 5 (fixed)', 'normal-height agreement, 8-bit copy', 0.788, smooth['8-bit uploaded height (selftest_brick_rolled2)']['normal_scores']['normal_height_agreement'], 'checks/baking_and_checking/smoothed_height_check.json'),
    ('baking 7.4', 'slid brick copy same-kind', 0.992, self_tests['brick_row']['slid by (311, 517) dots with wrap-around']['same_kind_overall'], 'checks/baking_and_checking/self_tests.json'),
    ('baking 7.4', 'gravel reference against mud', 0.498, self_tests['mud_row']['the gravel reference']['same_kind_overall'], 'checks/baking_and_checking/self_tests.json'),
    ('baking 7.5', 'metal flat normal', 13.26, flat['metal']['flat_normal_error_degrees'], 'checks/baking_and_checking/flat_baselines.json'),
    ('baking 7.5 (fixed)', 'gravel height ceiling', 5.01, fr['gravel']['derivation_ceiling']['height_from_colour']['mae_levels'], 'gravel/final_report.json'),
    ('relief 3.1', 'wood plain-slope ceiling', 4.6, round(fr['wood']['derivation_ceiling']['chain_normal_straight_line_central']['mean_angle_degrees'], 1), 'wood/final_report.json'),
    ('relief 3.1', 'mud Sobel ceiling', 3.7, round(fr['mud']['derivation_ceiling']['chain_normal_straight_line_sobel']['mean_angle_degrees'], 1), 'mud/final_report.json'),
    ('relief 3.4', 'mud S normal error at strength 9 (central)', 29.07, fr['mud']['normal_strength_test']['S_layout_ruts_clods']['central_9'], 'mud/final_report.json'),
    ('relief 9', 'slate geometry route height error', 33.76, fr['slate']['geometry_route']['geometry_route_plain']['pixel']['height_mae_best_fit_levels'], 'slate/final_report.json'),
    ('seamless 8.1', 'brick S half-tile wrong-roll share', 0.359, round(fr['brick']['half_tile_shift_test']['S_class_description']['wrongly_rolled_control']['share_over_40_levels'], 3), 'brick/final_report.json'),
    ('seamless 8.1', 'gravel half-tile mean (512 dots)', 1.29,
     float(re.search(r"colour_mean_difference_levels': ([0-9.]+)", fr['gravel']['half_tile_test']).group(1)), 'gravel/final_report.json, half_tile_test'),
    ('seamless 10', 'slate bake at 2508 dots, seconds', 100.7, fr['slate']['resolution']['2508']['process_seconds'], 'slate/final_report.json'),
    ('pattern makers 7.1 (fixed)', 'brick L grain 0 SSIM in rate_distortion', 0.672, round(brick_rd['L']['colour_ssim'], 3), 'brick/final_report.json (= scores/rate_distortion.json)'),
    ('pattern makers 7.1 (fixed)', 'brick L grain 0 same-kind in rate_distortion', 0.434, brick_rd['L']['texture_overall'], 'brick/final_report.json'),
    ('geometry 11', 'metal 20 % geometry, height error before fit', 18.3, fr['metal']['height_routes_L']['rows'][2][1], 'metal/final_report.json'),
    ('geometry 11', 'gravel geometry alone same-kind', 0.173, fr['gravel']['geometry_route']['geometry_compare_geometry_alone']['texture_as_baked']['overall'], 'gravel/final_report.json'),
    ('painted look 4', 'gravel shadow etc. same-kind', 0.437, fr['gravel']['procedural_ladder'][-1]['texture_overall'], 'gravel/final_report.json'),
    ('checklist 0.1', 'gravel flat ground SSIM', 0.444, fr['gravel']['procedural_ladder'][0]['colour_ssim'], 'gravel/final_report.json'),
    ('checklist C1 (fixed)', 'metal S0 bytes', 4840, fr['metal']['classes']['S0']['description_bytes'], 'metal/final_report.json'),
    ('checklist E7', 'mud area description bytes', 471580, os.path.getsize(os.path.join(R, 'mud', 'area', 'description_area_2508.json')), 'mud/area/description_area_2508.json'),
    ('checklist G1', 'pebbles description bytes', 1992, fr['gravel']['transfer']['description_bytes'], 'gravel/final_report.json'),
]

rows, mismatches = [], 0
for guide, what, quoted, from_file, source in checks:
    text = repr(quoted)
    decimals = len(text.split('.')[1]) if '.' in text else 0
    same = abs(float(quoted) - float(from_file)) <= 0.5 * 10 ** -decimals + 1e-9      # the file's number, rounded half up the way the guide wrote it
    mismatches += 0 if same else 1
    rows.append({'guide': guide, 'what': what, 'guide_says': quoted, 'file_says': from_file, 'match': same, 'file': source})
    print('%-5s %-28s %-48s guide %-10s file %s' % ('ok' if same else 'DIFF', guide, what, quoted, from_file))
print('%d checks, %d differ' % (len(rows), mismatches))
with open(os.path.join(HERE, 'number_checks.json'), 'w') as handle:
    json.dump({'checks': rows, 'count': len(rows), 'differ': mismatches}, handle, indent=1)
