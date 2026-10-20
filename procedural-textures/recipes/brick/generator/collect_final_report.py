# What this does (plain words): gathers every measured number of the brick job into one file, recipes/brick/final_report.json (per class S / M / L: description size,
# pixel tier, SSIM, colour difference, edge skill, height and normal errors, the "same kind of surface" score, seam, bake seconds; then the variation, area, resolution,
# route comparison, transfer and rate-distortion results). It only reads result files that the other scripts wrote.
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(HERE, '..'))


def load(*parts, default=None):
    path = os.path.join(R, *parts)
    if not os.path.exists(path):
        return default
    return json.load(open(path))


report = {'surface': 'brick', 'classes': {}}
for cls, limit in (('S', 8), ('M', 64), ('L', 512)):
    px = load('scores', f'final_{cls}_pixel.json', default={})
    tx = load('scores', f'final_{cls}_texture.json', default={})
    bake = load('outputs', f'final_{cls}', 'bake.json', default={})
    desc_path = os.path.join(R, 'generator', 'descriptions', f'description_{cls}.json')
    report['classes'][cls] = {
        'size_limit_kilobytes': limit, 'description_bytes': os.path.getsize(desc_path), 'tier': px.get('tier_reached'),
        'colour_ssim': px.get('colour_ssim'), 'colour_mean_delta_e': px.get('colour_mean_delta_e'), 'edge_skill': px.get('edge_skill_2px'),
        'height_mae_best_fit_levels': px.get('height_mae_best_fit_levels'), 'normal_mean_angle_degrees': px.get('normal_mean_angle_degrees'),
        'texture_compare_overall': tx.get('overall'), 'texture_groups': tx.get('groups'),
        'seam_ratio_from_texture_compare': (tx.get('facts') or {}).get('seam_ratio_candidate'), 'reference_seam_ratio': (tx.get('facts') or {}).get('seam_ratio_reference'),
        'bake_seconds_1254px_16_samples': bake.get('seconds'), 'shapes': bake.get('shapes')}
report['half_tile_shift_test'] = {'S_class_description': load('scores', 'seam_S', 'seam_result.json'), 'M_class_description': load('scores', 'seam_M', 'seam_result.json'), 'sampled_blob_tile': load('scores', 'seam_sample11', 'seam_result.json'),
                                  'sampled_mosaic_tile': load('scores', 'seam_mosaic21d', 'seam_result.json'), 'cobblestone_tile': load('transfer', 'seam_cobble', 'seam_result.json')}
report['derivation_ceiling'] = load('analysis', 'derivation_ceiling.json')
report['rate_distortion'] = load('scores', 'rate_distortion.json')
report['variation'] = load('variations', 'variation_summary.json')
report['area'] = load('area', 'area_result.json')
report['resolution'] = load('resolution', 'resolution_result.json')
report['transfer'] = load('transfer', 'transfer_result.json')
routes = {}
for name in ('M_height_derived', 'M_height_hybrid', 'M_height_geometry', 'shader_route', 'gn_route'):
    px = load('scores', f'{name}_pixel.json')
    tx = load('scores', f'{name}_texture.json')
    if px or tx:
        routes[name] = {'pixel': {k: px.get(k) for k in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached')} if px else None,
                        'texture_overall': tx.get('overall') if tx else None, 'texture_groups': tx.get('groups') if tx else None}
report['route_comparison'] = routes
report['gn_route'] = load('outputs', 'gn_route', 'gn_route.json')
json.dump(report, open(os.path.join(R, 'final_report.json'), 'w'), indent=1)
print('wrote', os.path.join(R, 'final_report.json'))
