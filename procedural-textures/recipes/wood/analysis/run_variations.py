# What this does (plain words): the VARIATION test. The sampler invents 8 NEW wood descriptions (seeds 101 to 108); one Blender run bakes them all at 1254 dots; then each is
# scored with the "same kind of surface" tool (should be high) and the dot-for-dot tool against the reference (should be poor: they are NOT copies), and every pair of
# new tiles is compared with each other (how different are they?). Also makes a contact sheet of all 8 next to the reference. Plain Python driving Blender (python3 -I).
# Output: ../variations/sample_k/ (pictures), ../variations/variation_scores.json, ../variations/contact_sheet.png
import itertools, json, os, subprocess, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(WOOD, 'generator'))
import sampler
import score_tools as st
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
seeds = [int(a) for a in sys.argv[1:]] or list(range(101, 109))
out = os.path.join(WOOD, 'variations'); os.makedirs(out, exist_ok=True)
jobs = []
for s in seeds:
    d = sampler.sample_description(s)
    path = os.path.join(out, f'sample_{s}.json')
    json.dump(d, open(path, 'w'), separators=(',', ':'))
    jobs.append([path, os.path.join(out, f'sample_{s}'), 1254])
json.dump(jobs, open(os.path.join(out, 'jobs.json'), 'w'))
t0 = time.time()
subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(WOOD, 'generator', 'wood_generator.py'), '--', '--batch', os.path.join(out, 'jobs.json')], capture_output=True)
bake_seconds = round(time.time() - t0)
rows, greys = [], {}
for s in seeds:
    folder = os.path.join(out, f'sample_{s}')
    r = st.score_folder(folder, texture=True)
    rows.append({'seed': s, 'description_bytes': os.path.getsize(os.path.join(out, f'sample_{s}.json')), 'texture_compare_overall': r['texture_compare_overall'], 'texture_groups': r['texture_compare_groups'],
                 'pixel_ssim_vs_reference': r['colour_ssim'], 'pixel_edge_skill_vs_reference': r['edge_skill_2px'], 'pixel_delta_e_vs_reference': r['colour_mean_delta_e'], 'pixel_tier': r['tier_reached'], 'seam_ratio': r['seam_ratio']})
    greys[s] = cv2.cvtColor(cv2.imread(os.path.join(folder, 'colour.png')), cv2.COLOR_BGR2GRAY)
    print(json.dumps(rows[-1]), flush=True)
pairs = []
for a, b in itertools.combinations(seeds, 2):
    d = np.abs(greys[a].astype(float) - greys[b].astype(float)).mean()
    pairs.append({'a': a, 'b': b, 'mean_abs_difference_levels': round(float(d), 2), 'ssim': round(st.pc.ssim(greys[a], greys[b]), 3)})
summary = {'bake_seconds_for_all_8': bake_seconds, 'rows': rows, 'pairs': pairs,
           'texture_compare_mean': round(float(np.mean([r['texture_compare_overall'] for r in rows])), 3), 'texture_compare_min': min(r['texture_compare_overall'] for r in rows), 'texture_compare_max': max(r['texture_compare_overall'] for r in rows),
           'pixel_ssim_vs_reference_mean': round(float(np.mean([r['pixel_ssim_vs_reference'] for r in rows])), 3), 'pair_ssim_mean': round(float(np.mean([p['ssim'] for p in pairs])), 3),
           'pair_mean_abs_difference_mean': round(float(np.mean([p['mean_abs_difference_levels'] for p in pairs])), 2)}
json.dump(summary, open(os.path.join(out, 'variation_scores.json'), 'w'), indent=1)
# contact sheet: reference + the new tiles, 3 x 3, 420 dots each
ref = cv2.imread(os.path.join(WOOD, '..', '..', 'reference', 'wood', 'colour.png'))
tiles = [cv2.resize(ref, (420, 420), interpolation=cv2.INTER_AREA)] + [cv2.resize(cv2.imread(os.path.join(out, f'sample_{s}', 'colour.png')), (420, 420), interpolation=cv2.INTER_AREA) for s in seeds]
labels = ['reference (given)'] + [f'new tile, seed {s}' for s in seeds]
for t, l in zip(tiles, labels):
    cv2.rectangle(t, (0, 0), (420, 26), (245, 245, 245), -1); cv2.putText(t, l, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
while len(tiles) % 3: tiles.append(np.full_like(tiles[0], 255))
cv2.imwrite(os.path.join(out, 'contact_sheet.png'), np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]))
print(json.dumps({k: v for k, v in summary.items() if k not in ('rows', 'pairs')}))
