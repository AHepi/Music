# What this does (plain words): makes N new brick tiles (different random seeds, each a NEW description drawn from the measured statistics), bakes each
# one in Blender with the same generator, scores each one two ways (is it the same KIND of surface? -> texture_compare; is it the same PICTURE as the
# reference? -> pixel_compare, which should be poor), measures how different the tiles are from each other (colour difference and structure
# similarity, pair by pair) and writes a contact sheet. Run with the system python:  python3 -I run_variations.py [first_seed] [count]
import json, os, subprocess, sys, itertools
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RECIPE = os.path.join(PROC, 'recipes', 'brick')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(PROC, 'lib'))
import sample_description as sd
import pixel_compare as pc
import texture_compare as tc
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
first, count = int(sys.argv[1]) if len(sys.argv) > 1 else 11, int(sys.argv[2]) if len(sys.argv) > 2 else 8
grain = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12
folder = os.path.join(RECIPE, 'variations')
os.makedirs(folder, exist_ok=True)
model = json.load(open(os.path.join(HERE, 'sampler_model_brick.json')))
results = []
for seed in range(first, first + count):
    desc = sd.sample_description(seed, model, grain=grain)
    path = os.path.join(folder, f'description_{seed}.json')
    json.dump(desc, open(path, 'w'), separators=(',', ':'))
    out = os.path.join(folder, f'tile_{seed}')
    log = subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(HERE, 'brick_generator.py'), '--', path, out, '--size', '1254', '--samples', '8'],
                         capture_output=True, text=True).stdout
    bake = json.loads(open(os.path.join(out, 'bake.json')).read())
    texture = tc.score_set('brick', out)
    px = pc.pixel_report('brick', out)
    results.append({'seed': seed, 'description_bytes': os.path.getsize(path), 'bake_seconds': bake['seconds'], 'shapes': bake['shapes'],
                    'texture_overall': texture['overall'], 'texture_groups': texture['groups'], 'seam_ratio': texture['facts']['seam_ratio_candidate'], 'pixel_ssim': px['colour_ssim'], 'pixel_delta_e': px['colour_mean_delta_e'], 'pixel_edge_skill': px['edge_skill_2px'], 'pixel_tier': px['tier_reached']})
    print(results[-1], flush=True)
json.dump(results, open(os.path.join(folder, 'variation_runs.json'), 'w'), indent=1)

# ---- how different are the tiles from each other (and from the reference)? colour difference per dot and structure similarity, pair by pair
def grey(path):
    im = cv2.imread(path)
    return im, cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
tiles = {r['seed']: grey(os.path.join(folder, f"tile_{r['seed']}", 'colour.png')) for r in results}
ref_im, ref_grey = grey(os.path.join(PROC, 'reference', 'brick', 'colour.png'))
pairs = []
for a, b in itertools.combinations(tiles, 2):
    pairs.append({'a': a, 'b': b, 'mean_abs_diff_levels': float(np.abs(tiles[a][0].astype(float) - tiles[b][0].astype(float)).mean()), 'ssim': pc.ssim(tiles[a][1], tiles[b][1])})
versus_ref = [{'seed': s, 'mean_abs_diff_levels': float(np.abs(tiles[s][0].astype(float) - ref_im.astype(float)).mean()), 'ssim': pc.ssim(tiles[s][1], ref_grey)} for s in tiles]
summary = {'tiles': results, 'pairs_mean_abs_diff': float(np.mean([p['mean_abs_diff_levels'] for p in pairs])), 'pairs_mean_ssim': float(np.mean([p['ssim'] for p in pairs])),
           'versus_reference_mean_abs_diff': float(np.mean([v['mean_abs_diff_levels'] for v in versus_ref])), 'versus_reference_mean_ssim': float(np.mean([v['ssim'] for v in versus_ref])),
           'texture_overall_mean': float(np.mean([r['texture_overall'] for r in results])), 'texture_overall_min': float(min(r['texture_overall'] for r in results)),
           'texture_overall_max': float(max(r['texture_overall'] for r in results))}
json.dump(summary, open(os.path.join(folder, 'variation_summary.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != 'tiles'}, indent=1))
# contact sheet: reference + the tiles, each 400 dots, 3 columns
size = 400
cells = [cv2.resize(ref_im, (size, size), interpolation=cv2.INTER_AREA)] + [cv2.resize(tiles[s][0], (size, size), interpolation=cv2.INTER_AREA) for s in tiles]
names = ['reference'] + [f'seed {s}' for s in tiles]
for cell, name in zip(cells, names):
    cv2.putText(cell, name, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
while len(cells) % 3:
    cells.append(np.zeros_like(cells[0]))
rows_img = [np.hstack(cells[i:i + 3]) for i in range(0, len(cells), 3)]
cv2.imwrite(os.path.join(folder, 'contact_sheet.png'), np.vstack(rows_img))
