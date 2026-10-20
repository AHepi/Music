# What this does (plain words): collects every number of the slate job into ../final_report.json (per class: bytes, tier, SSIM, Delta E, edge skill,
# height and normal errors, same-kind score, bake seconds; then the variation, area, resolution, seam and transfer results). Plain Python.
import json, os, glob
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..'))
def load(path):
    p = os.path.join(SLATE, path)
    return json.load(open(p)) if os.path.exists(p) else None
classes = {}
for name, cls in (('S0_layout_only', 'S0'), ('S1_layout_stamps', 'S (S1)'), ('S2_stamps_grain', 'S (S2, with grain)'), ('M_trace_tiny', 'M (tiny)'), ('M_trace_small', 'M (small)'), ('M_trace_coarse', 'M (coarse)'),
                  ('L_trace_small', 'L (small)'), ('L_trace_medium', 'L (medium)'), ('L_trace_fine', 'L (fine)')):
    s = load(f'scores/{name}_summary.json')
    if not s:
        continue
    p = s['pixel']
    classes[name] = {'class': cls, 'bytes': os.path.getsize(os.path.join(SLATE, 'description', name + '.json')), 'tier': p['tier_reached'], 'colour_ssim': p['colour_ssim'], 'colour_mean_delta_e': p['colour_mean_delta_e'],
                     'edge_skill_2px': p['edge_skill_2px'], 'height_mae_best_fit_levels': p['height_mae_best_fit_levels'], 'normal_mean_angle_degrees': p['normal_mean_angle_degrees'],
                     'texture_compare_overall_as_baked': s['texture_as_baked']['overall'], 'texture_compare_overall_smoothed_height_view': s['texture_view']['overall'], 'seam_ratio_texture_compare': s['seam_ratio'],
                     'bake_seconds': s['bake'].get('total_s')}
transfer = {'surfaces': ['weathered cedar roof shingles', 'clay fish-scale roof tiles'],
            'generator_code_changed': {'cedar_shingles': 'none', 'fish_scale_clay': 'one new setting (layout.bottom_round, about 12 lines) plus two sampler options (alternate row phase, a fitted= argument)'},
            'numbers_changed': 'palette, family lists, rows x pieces, piece width and row height, gaps, corner radius and raggedness, tone and tone gradient, patch size factors, moss and lichen shares, height stretch (1st and 99th percentile of the picture)',
            'time': 'one short script (about 90 lines), numpy preview 10 s, Blender bake 25 s per picture set',
            'half_tile_test': {k: v for k, v in (load('scores/half_tile_test.json') or {}).items() if k in ('cedar_shingles_1', 'fish_scale_clay_1')},
            'known_flaw': 'fish-scale rows do not overlap: the gap between two scales is black instead of the next row\'s tile'}
report = {'surface': 'slate', 'transfer': transfer, 'classes': classes, 'derivation_ceiling': load('scores/derivation_ceiling.json'), 'half_tile_test': load('scores/half_tile_test.json'),
          'variations': load('variations/summary.json'), 'area': load('area/area_report.json'), 'resolution': load('resolution/resolution_table.json'),
          'geometry_route': load('scores/geometry_route_summary.json'), 'filter_width_test': load('scores/filter_width_test.json')}
json.dump(report, open(os.path.join(SLATE, 'final_report.json'), 'w'), indent=1)
print('written', os.path.getsize(os.path.join(SLATE, 'final_report.json')))
