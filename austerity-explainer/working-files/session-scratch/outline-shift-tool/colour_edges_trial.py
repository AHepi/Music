# Compares outline agreement using brightness edges only against brightness-plus-colour edges, for one facts folder and several pictures.
import sys, types, numpy as np, cv2
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot
def edge_map(picture, with_colour):
    lab = cv2.cvtColor(cv2.GaussianBlur(picture, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
    found = cv2.Canny(lab[:, :, 0], 20, 60) > 0
    if with_colour:
        for c in (1, 2):
            found |= cv2.Canny(lab[:, :, c], 10, 30) > 0
    return cv2.dilate(found.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
facts = sys.argv[1]
for picture in sys.argv[2:]:
    args = types.SimpleNamespace(check='/home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json', facts=facts, picture=picture,
                                 out='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/outline-shift', title='', render_log=None)
    shot = check_shot.Shot(args)
    grey_near, colour_near = edge_map(shot.picture, False), edge_map(shot.picture, True)
    row = []
    for g in dict.fromkeys(shot.core + shot.check.get('pairs_also', [])):
        if not shot.shows(g) or shot.visible[g].sum() < 400:
            continue
        mask = shot.visible[g].astype(np.uint8)
        outline = (mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0
        a = (outline & grey_near).sum() / max(1, outline.sum()); b = (outline & colour_near).sum() / max(1, outline.sum())
        row.append(f'{g.split()[0]} {a:.2f}/{b:.2f}')
    print(picture.split('/')[-1], '|', '  '.join(row), '| edge share', f'{grey_near.mean():.2f}/{colour_near.mean():.2f}')
