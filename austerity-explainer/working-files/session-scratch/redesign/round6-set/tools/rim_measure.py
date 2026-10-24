"""What this does (scratch, round 6 set): measures the waiting men's rim light on a film-size picture, from the shot
checker's measured outlines (ids.png in the facts folder): for each man, the levels (0-255, brightest channel) in the
band 1 to 3 pixels inside his outline where it shows, the share of that band over 60 levels, the band's width where lit
(pixels from the outline over 60 levels), and the levels of his inside (more than 6 pixels in).
Use: python3 rim_measure.py PICTURE FACTS_FOLDER GROUP [GROUP ...]"""
import json, os, sys
import cv2
import numpy as np

picture = cv2.imread(sys.argv[1]).astype(np.float32)
facts = json.load(open(os.path.join(sys.argv[2], 'facts.json')))
ids = cv2.cvtColor(cv2.imread(os.path.join(sys.argv[2], 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
if picture.shape[:2] != ids.shape[:2]:
    picture = cv2.resize(picture, (ids.shape[1], ids.shape[0]), interpolation=cv2.INTER_AREA)
level = picture.max(axis=2)
for group in sys.argv[3:]:
    colour = np.array(facts['groups'][group]['colour'])
    mask = (np.abs(ids - colour).sum(axis=2) < 24).astype(np.uint8)
    if mask.sum() < 50:
        print(f'{group}: hardly shows ({mask.sum()} px)'); continue
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 3)
    band = (dist >= 1) & (dist <= 3)
    inside = dist > 6
    lit = band & (level > 60)
    widths = dist[(dist > 0) & (dist <= 8) & (level > 60)]
    print(f'{group}: edge band 95th pct {np.percentile(level[band], 95):.0f}, max {level[band].max():.0f}, over 60 levels {lit.sum() / band.sum():.0%} of the band; '
          f'lit depth median {np.median(widths) if widths.size else 0:.1f} px; inside median {np.median(level[inside]) if inside.any() else -1:.0f}, 95th {np.percentile(level[inside], 95) if inside.any() else -1:.0f}')
