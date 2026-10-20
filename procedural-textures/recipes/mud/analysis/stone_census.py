# What this does (plain words): counts the dark stones in the mud picture and measures how big they are (analysis only).
import cv2, numpy as np
labels = np.load('labels_k16.npy')
stone = np.isin(labels, [10, 12, 13, 15]).astype(np.uint8)
stone = cv2.morphologyEx(stone, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
n, comp, stats, cent = cv2.connectedComponentsWithStats(stone, connectivity=8)
areas = stats[1:, cv2.CC_STAT_AREA]
print('components', n - 1)
for lo, hi in ((1, 10), (10, 30), (30, 80), (80, 200), (200, 500), (500, 1500), (1500, 5000), (5000, 10**6)):
    m = (areas >= lo) & (areas < hi)
    print('area %6d..%-7d: %5d components, %5.1f%% of picture' % (lo, hi, m.sum(), 100 * areas[m].sum() / stone.size))
