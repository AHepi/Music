# What this file does (plain words): bakes a few views (colour, mask, joints) of the moss layer for ONE set of settings and joins them into one picture
# so it can be looked at; prints the covered share. Use: python3 -I views.py NAME SIZE 'JSON settings' [base] (base = flat or paint; add "damage":true in the JSON)
import json, subprocess, sys, os
import cv2
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.abspath(os.path.join(here, '..'))
name, size, settings = sys.argv[1], int(sys.argv[2]), json.loads(sys.argv[3] if len(sys.argv) > 3 else '{}')
views = {f'{name}_colour': dict(view='colour'), f'{name}_mask': dict(view='mask'), f'{name}_joints': dict(view='joints')}
out = os.path.join(work, 'dev', name)
subprocess.run([os.path.join(work, '..', 'tests', 'blender.sh'), os.path.join(work, '..', 'tests', 'bake_tools.py'), '--',
                os.path.join(work, 'moss_only_recipe.py'), out, str(size), '4', json.dumps(views), json.dumps(settings), 'Colour'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
c = cv2.imread(f'{out}/{name}_colour_colour.png'); m = cv2.imread(f'{out}/{name}_mask_colour.png'); j = cv2.imread(f'{out}/{name}_joints_colour.png', 0)
slate = j > 127
share = (m[..., 0][slate] > 127).mean()
print(f'{name}: covered share of slate dots {share:.3f}')
cv2.imwrite(f'{out}/sheet.png', np.hstack([c, m]))
