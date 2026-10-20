# What this does (plain words): writes recipes/wood/final_report.json: one block per size class (bytes, tier, structure score, colour difference, edge skill, height and normal errors,
# same-kind score, seam number, bake seconds), plus the derivation ceiling, variation, area, resolution, half-tile and transfer results, read from the score files. Plain Python.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
load = lambda *p: json.load(open(os.path.join(WOOD, *p))) if os.path.exists(os.path.join(WOOD, *p)) else None
table = load('scores', 'rate_distortion_table_wrap_aware.json') or []
cut = load('scores', 'rate_distortion_table_cut_at_edge.json') or []
report = {'surface': 'wood', 'folder': WOOD,
          'classes': {r['class']: {k: r[k] for k in ('bytes', 'tier', 'colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'texture_compare_overall', 'seam_ratio', 'bake_seconds')} for r in table},
          'classes_cut_at_tile_edge': {r['class']: {k: r[k] for k in ('bytes', 'tier', 'colour_ssim', 'edge_skill_2px', 'texture_compare_overall', 'seam_ratio')} for r in cut if r['class'][0] in 'ML'},
          'derivation_ceiling': load('analysis', 'derivation_ceiling.json'), 'variation': {k: v for k, v in (load('variations', 'variation_scores.json') or {}).items() if k != 'pairs'},
          'area': load('area', 'area_scores.json'), 'resolution': load('resolution', 'resolution_table.json'), 'geometry_route': load('outputs', 'geometry_route', 'geometry_route_report.json'),
          'half_tile': {n: load('scores', 'half_tile', n + '.json') for n in ('S1_layout_paint_grain', 'L2', 'L2w', 'sample_101')},
          'extras': {k: (lambda r: r and {m: r[m] for m in ('colour_ssim', 'edge_skill_2px', 'normal_mean_angle_degrees', 'texture_compare_overall')})(load('scores', f'extra_{k}.json')) for k in ('X1_S1_without_grain', 'X2_S0_with_grain', 'X3_L2_with_grain', 'X4_M3_with_grain')},
          'transfer': load('transfer', 'deck_boards_score.json'), 'description_audits': load('scores', 'description_audits.json')}
json.dump(report, open(os.path.join(WOOD, 'final_report.json'), 'w'), indent=1)
print('wrote final_report.json', os.path.getsize(os.path.join(WOOD, 'final_report.json')), 'bytes')
