# What this does (plain words): bakes the whole tile at 512 dots for several named sets of settings in one Blender run and reports, for each, how much of the
# picture's brightness variation is "the same along a whole row" (variance of the row averages divided by the total variance). The "same kind" score tool
# reads a picture whose rows dominate as having a huge horizontal correlation length (it only needs the share to pass 0.5). The reference has 0.46.
# Use: python3 -I row_share.py '{"name": {"outline_and_shadow.shadow_darkness": 0.6}, ...}'
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
sets = json.loads(sys.argv[1])
folder = os.path.join(HERE, 'previews', 'row_share')
jobs = {n.replace(' ', '_'): {'params': p} for n, p in sets.items()}
subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, folder, '512', '0.5,0.5,1.0', json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def share(path):
    g = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY).astype(np.float64)
    return g.var(), g.mean(axis=1).var() / g.var()
ref = share(os.path.join(HERE, '..', '..', '..', 'reference', 'slate', 'colour.png'))
print('%-28s total var %6.0f  row share %.3f' % ('reference', *ref))
for n in jobs:
    t, s = share(os.path.join(folder, n + '_colour.png'))
    print('%-28s total var %6.0f  row share %.3f' % (n, t, s))
