# What this does: how deeply two measured props overlap on screen (scratch, round 5): from the shot checker's solo
# pictures, the widest run of pixels where both props' outlines cover the same spot, across and down.
# Use: python3 overlap.py FACTS_FOLDER "GROUP A" "GROUP B"
import sys, os
import cv2, numpy as np
facts, a, b = sys.argv[1:4]
ma = cv2.imread(os.path.join(facts, 'solo', f'{a}.png')).max(axis=2) > 8
mb = cv2.imread(os.path.join(facts, 'solo', f'{b}.png')).max(axis=2) > 8
both = ma & mb
if not both.any():
    print(f'{a} and {b} do not overlap'); sys.exit()
rows = both.sum(axis=1); cols = both.sum(axis=0)
print(f'{a} and {b}: overlap {both.sum()} pixels, widest across {rows.max()} px, tallest {cols.max()} px')
