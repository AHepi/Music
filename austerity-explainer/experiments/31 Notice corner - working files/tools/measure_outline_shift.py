# Measures how well each prop's outline lines up with edges in a picture, unshifted and at its best small shift.
import sys, types, numpy as np, cv2
sys.path.insert(0, 'KIT/paper-film/tools')
import check_shot
facts, picture = sys.argv[1], sys.argv[2]
args = types.SimpleNamespace(check='KIT/examples/notice-corner/shot-check.json', facts=facts, picture=picture,
                             out='OUT_FOLDER', title='', render_log=None)
shot = check_shot.Shot(args)
edges = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(shot.picture, cv2.COLOR_BGR2GRAY), (0, 0), 1.5), 20, 60) > 0
near = cv2.dilate(edges.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
for g in dict.fromkeys(shot.core + shot.check.get('pairs_also', [])):
    if not shot.shows(g) or shot.visible[g].sum() < 400:
        continue
    mask = shot.visible[g].astype(np.uint8)
    outline = (mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0
    def agree(dx, dy):
        moved = np.roll(np.roll(outline, dy, 0), dx, 1)
        return (moved & near).sum() / max(1, moved.sum())
    zero = agree(0, 0)
    best = max(((agree(dx, dy), dx, dy) for dx in range(-24, 25, 3) for dy in range(-24, 25, 3)))
    print(f'{g:12s} unshifted {zero:.2f}  best {best[0]:.2f} at {best[1]},{best[2]}')
# draws one prop's outline: green where the picture has an edge next to it, red where it hasn't
if len(sys.argv) > 3:
    g = sys.argv[3]
    mask = shot.visible[g].astype(np.uint8)
    outline = (mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0
    drawn = shot.picture.copy()
    drawn[outline & near] = (0, 255, 0)
    drawn[outline & ~near] = (0, 0, 255)
    ys, xs = np.nonzero(mask)
    pad = 20
    cv2.imwrite(sys.argv[4], drawn[max(0, ys.min() - pad):ys.max() + pad, max(0, xs.min() - pad):xs.max() + pad])
