# What this does (plain words): bakes the WHOLE tile (colour only) with the layer on and off at a chosen size and writes a side-by-side picture
# with the reference, for the "does it read as the same kind of surface" look.
# Use: python3 -I full_tile.py NAME SIZE '{"outline_and_shadow.shadow_width": 0.03}'
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
name, size = sys.argv[1], int(sys.argv[2])
params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
folder = os.path.join(HERE, 'previews', 'tile_' + name)
jobs = {'on': {'params': params}, 'off': {'params': dict(params, **{'outline_and_shadow.amount': 0.0})}}
subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, folder, str(size), '0.5,0.5,1.0', json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
on, off = [cv2.imread(os.path.join(folder, f'{n}_colour.png')) for n in ('on', 'off')]
ref = cv2.resize(cv2.imread(os.path.join(HERE, '..', '..', '..', 'reference', 'slate', 'colour.png')), (size, size), interpolation=cv2.INTER_AREA)
cv2.imwrite(os.path.join(HERE, 'previews', f'tile_{name}_on.png'), on)
cv2.imwrite(os.path.join(HERE, 'previews', f'tile_{name}_vs_reference.png'), np.hstack([on, ref]))
cv2.imwrite(os.path.join(HERE, 'previews', f'tile_{name}_off_on.png'), np.hstack([off, on]))
print('wrote previews/tile_%s_*.png' % name)
