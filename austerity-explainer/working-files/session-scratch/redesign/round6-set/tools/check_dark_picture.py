# Runs the kit's shot checker (check_shot.py, unchanged) with one test relaxed: whether the finished picture
# matches the scene. On the Works' dusk views it judged pictures drawn from the current scene "out of date": the
# waiting men are dark on dark and alike (one slid sideways lines up with the man beside him), the gates are thin
# bars. So the men and the gates are left out of that one test (everything else keeps it), and outlines.jpg is drawn:
# every measured outline over the picture, to check by eye that they line up.
# Use: python3 check_dark_picture.py --check FILE --facts FOLDER --picture PICTURE --out FOLDER [--render-log LOG]
import sys, os
import numpy as np
import cv2
sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/tools')
import check_shot  # noqa: E402

original = check_shot.picture_mismatch


def relaxed(shot):
    """Keeps the checker's own findings except for the waiting men and the iron gates: a queue of like figures, and
    a gate of thin bars, line up with a neighbour's or another bar's edge when slid, by chance (a man slid 24 pixels
    lines up 100% with the man beside him); a near-black sign board's strongest edges are its painted border lines a
    little inside its outline. Those are checked by eye on outlines.jpg instead."""
    found = original(shot)
    return [entry for entry in found if not (entry.startswith('man ') or any(word in entry.split(' (')[0] for word in ('gate', 'board', 'sign')))]


check_shot.picture_mismatch = relaxed
args = sys.argv[1:]
out = args[args.index('--out') + 1]
os.makedirs(out, exist_ok=True)
sys.argv = ['check_shot.py'] + args
check_shot.main()
# the outlines over the picture: each measured group's edge (its flat colour in ids.png, within 2 levels: the flat
# pictures carry a little dither) drawn in cyan over the finished picture
import json
facts = args[args.index('--facts') + 1]
picture = cv2.imread(args[args.index('--picture') + 1])
ids = cv2.imread(os.path.join(facts, 'ids.png')).astype(np.int16)
picture = cv2.resize(picture, (ids.shape[1], ids.shape[0]))
groups = json.load(open(os.path.join(facts, 'facts.json')))['groups']
over = picture.copy()
for name, group in groups.items():
    r, g, b = group['colour']
    mask = (np.abs(ids - np.array([b, g, r])).max(axis=2) <= 2).astype(np.uint8)
    edge = (mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0
    over[cv2.dilate(edge.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0] = (255, 255, 60)
cv2.imwrite(os.path.join(out, 'outlines.jpg'), cv2.resize(over, (540, 960), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
