# What this does (plain words): makes 8 NEW mud tiles with the sampler (seeds 101 to 108), bakes each with Blender (1254 dots, all maps), scores each against the reference with both
# comparison tools ("same kind of surface" must be good, "same picture" must be poor), measures how different the tiles are from each other (dot-for-dot structure score and mean colour
# difference over all 28 pairs) and writes a contact sheet. Use: python3 -I generator/run_variations.py   (about 6 minutes)
import itertools, json, os, subprocess, sys, time
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'analysis'))
import sampler, score_tools as st, pixel_compare as pc
OUT = os.path.join(ROOT, 'variations'); os.makedirs(OUT, exist_ok=True)
seeds = list(range(101, 109))
rows = {}
for seed in seeds:
    d = sampler.sample_description(seed)
    path = os.path.join(OUT, f'description_{seed}.json')
    json.dump(d, open(path, 'w'), separators=(',', ':'))
    folder = os.path.join(OUT, f'tile_{seed}')
    if not os.path.exists(os.path.join(folder, 'colour.png')):
        subprocess.run([os.path.join(HERE, 'bake_one.sh'), path, folder, '1254', '8'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = st.score_folder(folder, texture=True)
    bake = json.load(open(os.path.join(folder, 'bake.json')))
    rows[seed] = {'bytes': len(json.dumps(d, separators=(',', ':'))), 'bake_seconds': bake['total_s'], 'shapes': bake['shapes'], **{k: r.get(k) for k in ('texture_compare_overall', 'seam_ratio', 'colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached')}}
    print(seed, rows[seed], flush=True)
imgs = {s: cv2.imread(os.path.join(OUT, f'tile_{s}', 'colour.png')) for s in seeds}
pairs = {}
for a, b in itertools.combinations(seeds, 2):
    ga, gb = cv2.cvtColor(imgs[a], cv2.COLOR_BGR2GRAY), cv2.cvtColor(imgs[b], cv2.COLOR_BGR2GRAY)
    pairs[f'{a}-{b}'] = {'ssim': round(pc.ssim(ga, gb), 3), 'mean_abs_colour_difference': round(float(np.abs(imgs[a].astype(float) - imgs[b]).mean()), 2)}
ssims = [v['ssim'] for v in pairs.values()]
summary = {'tiles': rows, 'between_tiles_ssim_mean': round(float(np.mean(ssims)), 3), 'between_tiles_ssim_max': round(float(np.max(ssims)), 3),
           'between_tiles_mean_abs_difference': round(float(np.mean([v['mean_abs_colour_difference'] for v in pairs.values()])), 2),
           'kind_score_mean': round(float(np.mean([r['texture_compare_overall'] for r in rows.values()])), 3), 'kind_score_min': round(float(np.min([r['texture_compare_overall'] for r in rows.values()])), 3),
           'kind_score_max': round(float(np.max([r['texture_compare_overall'] for r in rows.values()])), 3),
           'against_reference_ssim_mean': round(float(np.mean([r['colour_ssim'] for r in rows.values()])), 3), 'against_reference_ssim_max': round(float(np.max([r['colour_ssim'] for r in rows.values()])), 3)}
json.dump({'summary': summary, 'pairs': pairs}, open(os.path.join(OUT, 'variation_scores.json'), 'w'), indent=1)
ref = cv2.imread(os.path.join(ROOT, '..', '..', 'reference', 'mud', 'colour.png'))
small = [cv2.resize(ref, (420, 420), interpolation=cv2.INTER_AREA)] + [cv2.resize(imgs[s], (420, 420), interpolation=cv2.INTER_AREA) for s in seeds]
rows_img = [np.hstack(small[i:i + 3]) for i in range(0, 9, 3)]
cv2.imwrite(os.path.join(OUT, 'contact_sheet.png'), np.vstack(rows_img))
print(json.dumps(summary, indent=1))
