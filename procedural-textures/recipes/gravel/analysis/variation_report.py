# What this does (plain words): after the 8 new gravel tiles are baked and scored, this (1) puts them in one contact sheet (with the reference first), (2) measures
# how different the tiles are from each other (average dot difference and picture-structure score SSIM for every pair; a copy would give SSIM 1.0 and difference 0),
# and (3) collects each tile's "same kind" score and its dot-for-dot score against the reference (which should be poor: they are NEW tiles) into variations/report.json.
import glob, itertools, json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
G = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(G, '..', '..', 'lib'))
import pixel_compare as pc
folders = sorted(glob.glob(os.path.join(G, 'variations', 'out', 'sample_*')))
grey = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float64)
images = [cv2.imread(os.path.join(f, 'colour.png')) for f in folders]
ref = cv2.imread(os.path.join(G, '..', '..', 'reference', 'gravel', 'colour.png'))
tiles = [cv2.resize(ref, (420, 420), interpolation=cv2.INTER_AREA)] + [cv2.resize(i, (420, 420), interpolation=cv2.INTER_AREA) for i in images]
labels = ['reference'] + [os.path.basename(f) for f in folders]
cells = []
for t, l in zip(tiles, labels):
    t = t.copy(); cv2.rectangle(t, (0, 0), (420, 26), (255, 255, 255), -1); cv2.putText(t, l, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA); cells.append(t)
while len(cells) % 3:
    cells.append(np.full_like(cells[0], 255))
sheet = np.vstack([np.hstack(cells[i:i + 3]) for i in range(0, len(cells), 3)])
cv2.imwrite(os.path.join(G, 'variations', 'contact_sheet.png'), sheet)
pairs = []
for (a, fa), (b, fb) in itertools.combinations(zip(images, labels[1:]), 2):
    pairs.append({'a': fa, 'b': fb, 'mean_dot_difference_levels': round(float(np.abs(a.astype(float) - b.astype(float)).mean()), 2), 'ssim': round(pc.ssim(grey(a), grey(b)), 3)})
report = {'pairs': pairs, 'pair_mean_difference': round(float(np.mean([p['mean_dot_difference_levels'] for p in pairs])), 2), 'pair_mean_ssim': round(float(np.mean([p['ssim'] for p in pairs])), 3), 'tiles': {}}
for f in folders:
    name = 'var_' + os.path.basename(f)
    s = os.path.join(G, 'scores', name + '_summary.json')
    if os.path.exists(s):
        d = json.load(open(s))
        report['tiles'][os.path.basename(f)] = {'against_reference_ssim': round(d['pixel']['colour_ssim'], 3), 'against_reference_edge_skill': round(d['pixel']['edge_skill_2px'], 3),
                                                  'against_reference_delta_e': round(d['pixel']['colour_mean_delta_e'], 2), 'tier': d['pixel'].get('tier_reached'),
                                                  'texture_overall': d['texture_as_baked']['overall'], 'texture_view_overall': d['texture_view']['overall'], 'seam_ratio': d['seam_ratio']}
json.dump(report, open(os.path.join(G, 'variations', 'report.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in report.items() if k != 'pairs'}, indent=1))
