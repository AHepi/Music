# What this does (plain words): collects every number of the mud work into recipes/mud/final_report.json: per class (the rows of the ladder and the S, M, L classes): description bytes,
# pixel tier, SSIM, colour difference, edge skill, height and normal errors, "same kind" score, seam, bake seconds; plus the variation, area, resolution, seam-test, golden and transfer
# numbers. Plain Python; it only reads the score files written by the other scripts.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
def load(p, default=None):
    p = os.path.join(ROOT, p)
    return json.load(open(p)) if os.path.exists(p) else default
sizes = load('analysis/description_sizes.json', {})
sizes_g = load('analysis/description_sizes_mud_golden.json', {})
CLASS_OF = {'R0_flat_ground': 'row', 'R1_plus_puddle_outlines': 'row', 'R2_plus_40_big_stones': 'row', 'R3_plus_ruts': 'row', 'S_layout_ruts_clods': 'S', 'M_puddle_tones_stone_faces': 'M',
            'L2_traced_ground_2000_patches': 'L (smaller)', 'L_traced_ground_5000_patches': 'L (first)', 'L_final_traced_ground_plus_corrections': 'L'}
def row(name, size_table, folder, score_name):
    s = load(f'{folder}/{name}/score.json')
    if not s:
        return None
    bake = load(f'{folder}/{name}/bake.json', {})
    keep = ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall', 'seam_ratio', 'colour_psnr_db', 'colour_mae_levels', 'height_correlation')
    return {'class': CLASS_OF.get(name, ''), 'description_bytes': size_table.get(name), 'bake_seconds': bake.get('total_s'), 'shapes': bake.get('shapes'), **{k: s.get(k) for k in keep if k in s}}
report = {'surface': 'mud', 'folder': ROOT, 'mud': {}, 'mud_golden': {}}
for name in CLASS_OF:
    r = row(name, sizes, 'outputs', name)
    if r: report['mud'][name] = r
    g = row(name, sizes_g, 'outputs_golden', name) if os.path.exists(os.path.join(ROOT, 'outputs_golden', name, 'score.json')) else None
    if g: report['mud_golden'][name] = g
report['derivation_ceiling'] = load('analysis/derivation_ceiling.json')
report['quantised_ceiling'] = load('analysis/ceiling_quantised.json')
report['variation'] = load('variations/variation_scores.json')
report['scale_tests'] = load('scores/scale_tests.json')
report['normal_strength_test'] = load('scores/normal_strength_test.json')
report['geometry_route'] = load('outputs/geometry_route/report.json')
report['half_tile_seam_tests_reference_fitted'] = load('scores/seam_tests_extra.json')
report['transfer_snow'] = {'description_bytes': os.path.getsize(os.path.join(ROOT, 'transfer', 'snow_description.json')) if os.path.exists(os.path.join(ROOT, 'transfer', 'snow_description.json')) else None, 'bake': load('transfer/snow/bake.json'), 'what_changed': 'palette (16 colours), which palette entries play band/groove/bank/wet/water, stone_scale 0.35, puddle_scale 0.7, clod_count 9000, zone_weight 0.85, height stretch 60..245; sampler got one new option (maps)', 'judged': 'by eye only (no reference)'}
report['sizes_bytes'] = {'mud': sizes, 'mud_golden': sizes_g}
json.dump(report, open(os.path.join(ROOT, 'final_report.json'), 'w'), indent=1)
print('final_report.json written;', len(report['mud']), 'mud rows,', len(report['mud_golden']), 'golden rows')
