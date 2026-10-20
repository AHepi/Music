# What this does (plain words): an early look-at-it script: paints the dots of the mud picture that belong to the 'stone' and 'water' palette colours in white and blue so I could judge whether a palette-colour sort finds stones (it was the first try; section 10 of the recipe says why it was replaced). Writes a picture into /tmp (the scratch folder is deleted at the end). Analysis only.
import cv2, numpy as np
labels = np.load('labels_k16.npy')
img = cv2.imread('proc-work/reference/mud/colour.png')
stone = np.isin(labels, [10, 12, 13, 15])
water = np.isin(labels, [5, 8])
grey_brown = np.isin(labels, [7])
vis = np.zeros_like(img)
vis[stone] = (255, 255, 255); vis[water] = (255, 120, 0); vis[grey_brown] = (0, 200, 0)
vis = cv2.resize(vis, (900, 900), interpolation=cv2.INTER_NEAREST)
cv2.imwrite('/tmp/mudscratch/masks.png', vis)
