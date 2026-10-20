# What this does (plain words): collects every measured number of the gravel work (class rows, ladder, variations, area, resolution, transfer, geometry route,
# derivation ceiling) from the files in scores/, variations/, area/, resolution/, transfer/ into one final_report.json. Nothing is invented: a number that does not
# exist yet is left out. Run: python3 -I make_final_report.py
import glob, json, os
G = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
def load(path):
    p = os.path.join(G, path)
    return json.load(open(p)) if os.path.exists(p) else None
def size_kb(name):
    p = os.path.join(G, 'description', name + '.json')
    return round(len(json.dumps(json.load(open(p)), separators=(',', ':')).encode()) / 1024, 2) if os.path.exists(p) else None
rows = []
for name, klass in (('S_v4', 'S (procedural, <= 8 KB) FINAL'), ('S_v2', 'S (procedural) first round, stones too small'), ('TS_k24_a300', 'M-size hybrid (stone patches traced + procedural soil)'), ('M_a600_s120', 'M (traced, <= 64 KB)'), ('T_k24_a250', 'L-size, patches only'),
                    ('T_k24_a100', 'L-size, patches only'), ('T_k24_a50', 'L-size, patches only'), ('L_a250_s12', 'L (traced + stamps)'), ('L_a100_s8', 'L (traced + stamps, best)')):
    s = load(f'scores/{name}_summary.json')
    if not s:
        continue
    p = s['pixel']
    rows.append({'class_name': name, 'tier': p.get('tier_reached'), 'size_class': klass, 'description_kb': size_kb(name), 'colour_ssim': p['colour_ssim'], 'colour_mean_delta_e': p['colour_mean_delta_e'],
                 'edge_skill': p['edge_skill_2px'], 'height_mae_best_fit': p['height_mae_best_fit_levels'], 'normal_mean_angle': p['normal_mean_angle_degrees'],
                 'texture_compare_as_baked': s['texture_as_baked']['overall'], 'texture_compare_view': s['texture_view']['overall'], 'seam_ratio': s['seam_ratio'], 'bake_seconds': s['bake'].get('total_s')})
report = {'surface': 'gravel', 'classes': rows, 'derivation_ceiling': load('scores/derivation_ceiling.json'), 'derivation_parametric': load('scores/derivation_parametric.json'), 'palette_ceiling': load('scores/palette_ceiling.json'),
          'procedural_ladder': load('scores/ladder_procedural.json'), 'stamp_experiment': load('scores/stamp_experiment.json'), 'window_spread': load('scores/window_spread.json'),
          'half_tile_test': open(os.path.join(G, 'scores', 'flags', 'half_tile.txt')).read().strip() if os.path.exists(os.path.join(G, 'scores', 'flags', 'half_tile.txt')) else None,
          'variation': load('variations/report.json'), 'area': load('area/area_report.json'), 'resolution': load('resolution/resolution_report.json'), 'geometry_route': load('scores/geometry_route_summary.json'),
          'transfer': load('transfer/transfer_report.json')}
json.dump(report, open(os.path.join(G, 'final_report.json'), 'w'), indent=1)
print('final_report.json written;', len(rows), 'class rows')
