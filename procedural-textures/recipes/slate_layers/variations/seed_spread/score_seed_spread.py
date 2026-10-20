# What this does (plain words): how much does the "same kind" colour score move when ONLY the seeds change? It scores the default tile, variation v1
# (five new seeds) and three more sets of seeds of the default settings (seeds_b, seeds_c, seeds_d; all at 1254 dots) against the slate reference,
# and writes the five colour groups with their mean, lowest and highest to seed_spread.json. Then it keeps small JPEG copies of the three new tiles
# for looking and deletes the big PNGs. Use (plain python): python3 -I score_seed_spread.py
import json, os, subprocess
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SL = os.path.abspath(os.path.join(HERE, '..', '..'))
pictures = {'default seeds (outputs/default)': os.path.join(SL, 'outputs', 'default', 'colour.png'),
            'v1 new seeds (layout 7, colour 17, damage 27, moss 37, outline 47)': os.path.join(SL, 'variations', 'v1_new_seeds_colour.png')}
views = json.load(open(os.path.join(HERE, 'views.json')))
for name, seeds in views.items():
    pictures[f'{name} (' + ', '.join(f'{k.split(".")[0]} {v}' for k, v in seeds.items()) + ')'] = os.path.join(HERE, f'{name}_colour.png')
result = {}
for label, path in pictures.items():
    line = subprocess.run(['bash', os.path.join(SL, 'integration', 'score_colour.sh'), path], capture_output=True, text=True).stdout
    result[label] = {'colour group': float(line.split()[2]), 'colour_scale': float(line.split("'colour_scale': ")[1].split(',')[0])}
    print(label, result[label], flush=True)
groups = [v['colour group'] for v in result.values()]
summary = {'tiles': result, 'mean colour group': round(float(np.mean(groups)), 3), 'lowest': min(groups), 'highest': max(groups),
           'spread (highest - lowest)': round(max(groups) - min(groups), 3)}
json.dump(summary, open(os.path.join(HERE, 'seed_spread.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != 'tiles'}))
for name in views:
    path = os.path.join(HERE, f'{name}_colour.png')
    cv2.imwrite(path[:-4] + '_small.jpg', cv2.resize(cv2.imread(path), (627, 627), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 90])
    os.remove(path)
