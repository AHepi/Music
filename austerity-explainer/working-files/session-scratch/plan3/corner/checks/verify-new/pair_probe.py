# What this does: repeats check_shot's rule-4 measure for one pair of groups in a facts folder, printing the numbers.
import sys, json, cv2, numpy as np
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
from check_shot import without_wires, without_specks, distance_inside, distance_outside
folder, a, b = sys.argv[1:4]
facts = json.load(open(folder + '/facts.json'))
ids = cv2.cvtColor(cv2.imread(folder + '/ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
vis = {g: without_specks(np.abs(ids - np.array(facts['groups'][g]['colour'])).sum(2) < 24) for g in (a, b)}
alone = {g: cv2.imread(f'{folder}/solo/{g}.png').max(2) > 8 for g in (a, b)}
solid = {g: without_wires(alone[g], 1080) for g in (a, b)}
both = solid[a] & solid[b]
print('whole overlap', int((alone[a] & alone[b]).sum()), 'solid overlap', int(both.sum()))
if both.any():
    showing = both & (vis[a] | vis[b])
    depth = max(distance_inside(solid[a])[showing].max(), distance_inside(solid[b])[showing].max()) if showing.any() else None
    print('showing', int(showing.sum()), 'depth', depth)
va, vb = vis[a], vis[b]
if (alone[a] & alone[b]).any():
    va, vb = without_wires(va, 1080), without_wires(vb, 1080)
gaps = np.where(vb, distance_outside(va), np.inf)
print('visible gap', float(gaps.min()), 'at', np.unravel_index(np.argmin(gaps), gaps.shape))
