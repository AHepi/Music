import sys, json, types, numpy as np, cv2
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
C='/home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json'
for d in ['facts-end', 'tests/a-old-camera', 'tests/c-chair-touching']:
    args = types.SimpleNamespace(check=C, facts=d, picture=None)
    check, facts, visible, alone, _ = cs.load(args)
    W, H = facts['size']
    for label, width in (('tool (20/25 px at 1080)', W), ('doc (20/25 px at 1536)', W*1080/1536)):
        r = cs.Report(W, H)
        cs.check_pairs(r, check, facts, visible, alone, width, facts['camera']['at'][2])
        print(d, label, '->', [i['what'][:70] for i in r.items])
# the lamp head over the spoked wheel (test a): overlap with the wheel's filled disc
args = types.SimpleNamespace(check=C, facts='tests/a-old-camera', picture=None)
check, facts, visible, alone, _ = cs.load(args)
w = alone['winding wheels'].astype(np.uint8)*255
filled = w.copy(); mask = np.zeros((w.shape[0]+2, w.shape[1]+2), np.uint8); cv2.floodFill(filled, mask, (0,0), 128)
disc = filled != 128
both = disc & alone['lamp post']
print('test a: lamp post over the wheel discs: overlap', both.sum(), 'px, thickness', 2*cv2.distanceTransform(both.astype(np.uint8), cv2.DIST_L2, 5).max(), 'px; over the spokes and rim only:', 2*cv2.distanceTransform((alone['winding wheels'] & alone['lamp post']).astype(np.uint8), cv2.DIST_L2, 5).max())
