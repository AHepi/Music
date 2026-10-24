import sys, json, types, numpy as np, cv2
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
facts_dir = sys.argv[1]
args = types.SimpleNamespace(check='/home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json', facts=facts_dir, picture=None)
check, facts, visible, alone, _ = cs.load(args)
W, H = facts['size']
ids = cv2.imread(facts_dir + '/ids.png')
cols = np.unique(ids.reshape(-1,3), axis=0)
print('unique colours in ids.png:', len(cols))
for a, b in [('lantern','board'), ('lamp post','winding wheels'), ('chair','board'), ('drum','board'), ('chair','notice'), ('chair','drum')]:
    both = alone[a] & alone[b]
    if not both.any():
        print(a,b,'no overlap'); continue
    showing = both & (visible[a] | visible[b])
    t = 2*cv2.distanceTransform(showing.astype(np.uint8), cv2.DIST_L2, 5).max()
    tb = 2*cv2.distanceTransform(both.astype(np.uint8), cv2.DIST_L2, 5).max()
    print(f'{a}/{b}: both {both.sum()} px, box {cs.box_of(both)}, showing {showing.sum()} ({showing.sum()/both.sum():.0%}), thickness(showing) {t:.1f}, thickness(both) {tb:.1f}')
    # how far does the front one reach past the back one's edge? -> the deepest point of the overlap measured inside the back silhouette
    for front, back in ((a,b),(b,a)):
        inside_back = cv2.distanceTransform(alone[back].astype(np.uint8), cv2.DIST_L2, 5)
        print(f'    deepest point of {front} inside {back}: {inside_back[both].max():.1f} px')
for g in ['lamp post', 'board', 'notice', 'pail', 'chair', 'drum', 'lantern']:
    print(g, 'visible box', cs.box_of(visible[g]), 'alone box', cs.box_of(alone[g]), 'unclipped', facts['groups'][g]['screen_box_unclipped'])
