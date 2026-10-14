# For each prop: outline agreement with colour+brightness edges unshifted, and the best agreement within a small slide.
import sys, types, numpy as np, cv2
sys.path.insert(0, 'KIT/paper-film/tools')
import check_shot
facts = sys.argv[1]
for picture in sys.argv[2:]:
    args = types.SimpleNamespace(check='KIT/examples/notice-corner/shot-check.json', facts=facts, picture=picture,
                                 out='OUT_FOLDER', title='', render_log=None)
    shot = check_shot.Shot(args)
    lab = cv2.cvtColor(cv2.GaussianBlur(shot.picture, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
    edges = cv2.Canny(lab[:, :, 0], 20, 60) > 0
    for c in (1, 2):
        edges |= cv2.Canny(lab[:, :, c], 10, 30) > 0
    near = cv2.dilate(edges.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    step = max(2, shot.width // 270)
    reach = shot.width // 30
    row = []
    for g in dict.fromkeys(shot.core + shot.check.get('pairs_also', [])):
        if not shot.shows(g) or shot.visible[g].sum() < 400:
            continue
        mask = shot.visible[g].astype(np.uint8)
        outline = (mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0
        ys, xs = np.nonzero(outline)
        def agree(dx, dy):
            y2, x2 = ys + dy, xs + dx
            ok = (y2 >= 0) & (y2 < shot.height) & (x2 >= 0) & (x2 < shot.width)
            return near[y2[ok], x2[ok]].sum() / max(1, ok.sum())
        zero = agree(0, 0)
        best = max((agree(dx, dy), dx, dy) for dx in range(-reach, reach + 1, step) for dy in range(-reach, reach + 1, step))
        row.append(f'{g.split()[0]} {zero:.2f}>{best[0]:.2f}@{best[1]},{best[2]}')
    print(picture.split('/')[-1], '|', '  '.join(row))
