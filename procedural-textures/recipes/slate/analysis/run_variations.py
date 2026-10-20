# What this does (plain words): makes 8 NEW slate tiles. For each seed the sampler invents a new description (a few KB), one Blender run bakes them
# all with the same generator, then every tile is scored (a) against the reference with texture_compare ("is it the same kind of surface?")
# and pixel_compare ("is it the same picture?" - it should NOT be), (b) against every other new tile (how different are they from each other),
# and a contact sheet is drawn. Output: variations/ (descriptions, pictures, summary.json, contact_sheet.png). Plain Python (python3 -I).
import itertools, json, os, subprocess, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..')); PROC = os.path.abspath(os.path.join(SLATE, '..', '..'))
sys.path.insert(0, os.path.join(SLATE, 'generator')); sys.path.insert(0, os.path.join(PROC, 'lib'))
import sampler
import pixel_compare as pc
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
out = os.path.join(SLATE, 'variations'); os.makedirs(out, exist_ok=True)
seeds = [101, 102, 103, 104, 105, 106, 107, 108]
jobs = []
for seed in seeds:
    d = sampler.sample_description(seed)
    path = os.path.join(out, f'var_{seed}.json')
    json.dump(d, open(path, 'w'), separators=(',', ':'))
    jobs.append([path, os.path.join(out, f'var_{seed}'), 1254])
json.dump(jobs, open(os.path.join(out, 'jobs.json'), 'w'))
started = time.time()
subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(SLATE, 'generator', 'slate_generator.py'), '--', '--batch', os.path.join(out, 'jobs.json')], capture_output=True, text=True)
bake_seconds = time.time() - started
summary = {'seeds': seeds, 'bake_total_seconds': round(bake_seconds, 1), 'tiles': {}}
colours = {}
reference = cv2.imread(os.path.join(PROC, 'reference', 'slate', 'colour.png'))
for seed in seeds:
    folder = os.path.join(out, f'var_{seed}')
    result = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'score_folder.py'), folder, f'var_{seed}', '--out', os.path.join(out, 'scores')], capture_output=True, text=True)
    s = json.loads(result.stdout.strip().splitlines()[-1])
    colours[seed] = cv2.imread(os.path.join(folder, 'colour.png'))
    g = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    summary['tiles'][seed] = {'texture_overall': s['texture_as_baked']['overall'], 'texture_view_overall': s['texture_view']['overall'], 'groups': s['texture_as_baked'], 'seam_ratio': s['seam_ratio'],
                              'pixel_vs_reference': s['pixel'], 'description_bytes': os.path.getsize(os.path.join(out, f'var_{seed}.json')), 'bake_seconds': s['bake'].get('total_s')}
    print(seed, s['texture_as_baked'], s['pixel']['tier_reached'], flush=True)
# how different are the tiles from each other: mean colour difference, SSIM of grey, and Delta E
def pair_measures(a, b):
    ga, gb = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    return {'mean_abs_difference_levels': round(float(np.abs(a.astype(float) - b.astype(float)).mean()), 2), 'ssim': round(pc.ssim(ga, gb), 3)}
pairs = {}
for a, b in itertools.combinations(seeds, 2):
    pairs[f'{a}-{b}'] = pair_measures(colours[a], colours[b])
summary['pairs'] = pairs
summary['pairs_mean'] = {k: round(float(np.mean([v[k] for v in pairs.values()])), 3) for k in ('mean_abs_difference_levels', 'ssim')}
summary['vs_reference_mean'] = {'ssim': round(float(np.mean([summary['tiles'][s]['pixel_vs_reference']['colour_ssim'] for s in seeds])), 3),
                                'delta_e': round(float(np.mean([summary['tiles'][s]['pixel_vs_reference']['colour_mean_delta_e'] for s in seeds])), 2)}
summary['texture_overall_mean'] = round(float(np.mean([summary['tiles'][s]['texture_overall'] for s in seeds])), 3)
summary['texture_overall_range'] = [min(summary['tiles'][s]['texture_overall'] for s in seeds), max(summary['tiles'][s]['texture_overall'] for s in seeds)]
json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
# contact sheet: reference first, then the 8 tiles
cell = 400
tiles = [cv2.resize(reference, (cell, cell), interpolation=cv2.INTER_AREA)] + [cv2.resize(colours[s], (cell, cell), interpolation=cv2.INTER_AREA) for s in seeds]
labels = ['reference'] + [f'new tile {i + 1} (seed {s})' for i, s in enumerate(seeds)]
for t, l in zip(tiles, labels):
    cv2.putText(t, l, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(t, l, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
sheet = np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, 9, 3)])
cv2.imwrite(os.path.join(out, 'contact_sheet.png'), sheet)
print(json.dumps({k: summary[k] for k in ('pairs_mean', 'vs_reference_mean', 'texture_overall_mean', 'texture_overall_range', 'bake_total_seconds')}))
