# What this does: gathers the numbers of every full-size bake (timings, vertex counts, scores against the references, hybrid-height scores) into results_summary.json
# and prints two markdown tables for the guide. Run (plain Python): python3 -I collect_results.py
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
full = os.path.join(HERE, 'out', 'full')
hyb = os.path.join(HERE, 'out', 'hybrid')
names = [('brick', 'brick'), ('slate', 'slate'), ('wood', 'wood'), ('metal', 'metal'), ('mud', 'mud'), ('gravel', 'gravel (rigid body)'), ('gravel_gn', 'gravel (nodes only)')]
summary = {}
rows1, rows2 = [], []
for key, title in names:
    folder = os.path.join(full, key)
    if not os.path.exists(os.path.join(folder, 'score.json')):
        continue
    score = json.load(open(os.path.join(folder, 'score.json')))
    photo = json.load(open(os.path.join(folder, 'photo.json')))
    p = photo.get('photo', photo)
    entry = {'overall': score['overall'], **score['groups'], 'vertices': p.get('vertices'), 'evaluate_geometry_s': p.get('evaluate_geometry_s'),
             'height_render_s': p.get('height_render_s'), 'colour_render_s': p.get('colour_render_s'), 'normal_render_s': p.get('normal_render_s'), 'total_seconds': photo.get('total_seconds')}
    h = os.path.join(hyb, key, 'hybrid_results.json')
    if os.path.exists(h):
        entry['hybrid'] = json.load(open(h))
    summary[key] = entry
    rows1.append(f"| {title} | {entry['total_seconds']} | {entry['vertices']:,} | {entry['evaluate_geometry_s']} | {entry['height_render_s']} | {entry['colour_render_s']} | {entry['normal_render_s']} | **{entry['overall']}** | {entry['colour']} | {entry['height']} | {entry['normal']} | {entry['tiling']} |")
    if 'hybrid' in entry:
        hy = entry['hybrid']
        rows2.append(f"| {title} | {hy['A_geometry']['overall']} (n {hy['A_geometry']['normal']}, h {hy['A_geometry']['height']}) | {hy['B_geo_normal']['overall']} (n {hy['B_geo_normal']['normal']}) | {hy['C_hybrid_half_geometry_half_colour']['overall']} (h {hy['C_hybrid_half_geometry_half_colour']['height']}) | {hy['D_colour_brightness_only']['overall']} (h {hy['D_colour_brightness_only']['height']}, n {hy['D_colour_brightness_only']['normal']}) | {hy['A_geometry']['height_colour_corr']} / {hy['C_hybrid_half_geometry_half_colour']['height_colour_corr']} / {hy['D_colour_brightness_only']['height_colour_corr']} |")
json.dump(summary, open(os.path.join(HERE, 'results_summary.json'), 'w'), indent=1)
print('| recipe | total s | vertices | geometry s | height render s | colour render s (AO) | normal render s | OVERALL | colour | height | normal | tiling |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|')
print('\n'.join(rows1))
print()
print('| recipe | A geometry only | B true-normal | C hybrid | D colour brightness only | height-colour correlation A / C / D |')
print('|---|---|---|---|---|---|')
print('\n'.join(rows2))
