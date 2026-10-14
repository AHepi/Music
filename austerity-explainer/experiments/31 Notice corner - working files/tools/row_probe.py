# Prints the picture's brightness, the drum mask and the edge map along one row across the drum's left edge.
import sys, types, numpy as np, cv2
sys.path.insert(0, 'KIT/paper-film/tools')
import check_shot
args = types.SimpleNamespace(check='KIT/examples/notice-corner/shot-check.json', facts=sys.argv[1], picture=sys.argv[2],
                             out='OUT_FOLDER', title='', render_log=None)
shot = check_shot.Shot(args)
grey = cv2.cvtColor(shot.picture, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(grey, (0, 0), 1.5)
edges = cv2.Canny(blur, 20, 60) > 0
mask = shot.visible['drum']
ys, xs = np.nonzero(mask)
print('picture', shot.picture.shape, 'mask rows', ys.min(), ys.max(), 'cols', xs.min(), xs.max())
for y in (int(ys.min() + 0.3 * (ys.max() - ys.min())), int(ys.min() + 0.6 * (ys.max() - ys.min()))):
    left = np.nonzero(mask[y])[0].min()
    cols = range(left - 8, left + 8)
    print('row', y, 'mask left edge at', left)
    print(' col   ', ' '.join(f'{c:4d}' for c in cols))
    print(' grey  ', ' '.join(f'{grey[y, c]:4d}' for c in cols))
    print(' blur  ', ' '.join(f'{blur[y, c]:4d}' for c in cols))
    print(' mask  ', ' '.join(f'{int(mask[y, c]):4d}' for c in cols))
    print(' edge  ', ' '.join(f'{int(edges[y, c]):4d}' for c in cols))
