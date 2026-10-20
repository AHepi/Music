# What this does (plain words): gathers the scores of every baked description into one table (rate-distortion: how accurate the picture is for each description
# size) and writes scores/rate_distortion.json. Reads scores/*_pixel.json and scores/*_texture.json and the description file sizes.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.abspath(os.path.join(HERE, '..'))
rows = [
    ('R0', 'R0_layout_only', 'layout only: brick rectangles, one colour', 'layout'),
    ('R1', 'stage1_bricks_only', 'layout + one base colour per brick', 'layout'),
    ('S', 'S_blobs', 'S class: layout + 146 patches + outline (ellipses)', 'S'),
    ('M', 'M_blobs', 'M class: layout + 1818 patches + outline (ellipses)', 'M'),
    ('M+ (200 KB ellipses)', 'Mb200_blobs', 'ellipse patches, 5990 patches, 200 KB', 'in between'),
    ('L-ellipses (376 KB)', 'Lb_blobs', 'ellipse patches, 11406 patches, 376 KB', 'in between'),
    ('L-300', 'L_amin300_eps2.0', 'traced patches >= 300 dots (640 regions)', 'L steps'),
    ('L-80', 'L_amin80_eps2.0', 'traced patches >= 80 dots (2449 regions)', 'L steps'),
    ('L-20', 'L_amin20_eps2.0', 'traced patches >= 20 dots (8509 regions)', 'L steps'),
    ('L', 'L_amin12_eps2.2', 'L class: traced patches >= 12 dots (12553 regions)', 'L'),
    ('L + grain 0.10', 'L12_g0.10', 'L + per-dot grain 0.10', 'L'),
    ('L + grain 0.14', 'L12_g0.14', 'L + per-dot grain 0.14', 'L'),
]
out = []
for tag, desc, text, cls in rows:
    d = os.path.join(RECIPE, 'generator', 'descriptions', desc + '.json')
    name = {'R0_layout_only': 'R0', 'stage1_bricks_only': 'R1', 'S_blobs': 'S_blobs', 'M_blobs': 'M_blobs', 'L_amin300_eps2.0': 'L300', 'L_amin80_eps2.0': 'L80',
            'L_amin20_eps2.0': 'L20', 'L_amin12_eps2.2': 'L12', 'Mb200_blobs': 'Mb200_blobs', 'Lb_blobs': 'Lb_blobs'}.get(desc, desc)
    px = json.load(open(os.path.join(RECIPE, 'scores', name + '_pixel.json')))
    tx = json.load(open(os.path.join(RECIPE, 'scores', name + '_texture.json')))
    out.append({'tag': tag, 'what': text, 'class': cls, 'description_bytes': os.path.getsize(d), 'description_kilobytes': round(os.path.getsize(d) / 1024, 1),
                'colour_ssim': px['colour_ssim'], 'colour_mean_delta_e': px['colour_mean_delta_e'], 'edge_skill_2px': px['edge_skill_2px'],
                'height_mae_best_fit_levels': px['height_mae_best_fit_levels'], 'normal_mean_angle_degrees': px['normal_mean_angle_degrees'], 'tier': px['tier_reached'],
                'texture_overall': tx['overall'], 'texture_groups': tx['groups']})
json.dump(out, open(os.path.join(RECIPE, 'scores', 'rate_distortion.json'), 'w'), indent=1)
print('%-16s %9s %6s %6s %6s %6s %6s %-7s %6s' % ('step', 'KB', 'SSIM', 'dE', 'edge', 'height', 'normal', 'tier', 'texture'))
for r in out:
    print('%-16s %9.1f %6.3f %6.2f %6.3f %6.1f %6.1f %-7s %6.3f' % (r['tag'], r['description_kilobytes'], r['colour_ssim'], r['colour_mean_delta_e'], r['edge_skill_2px'], r['height_mae_best_fit_levels'], r['normal_mean_angle_degrees'], r['tier'], r['texture_overall']))
