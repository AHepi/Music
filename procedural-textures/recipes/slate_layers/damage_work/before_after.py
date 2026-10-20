# What this does (plain words): makes the before/after pictures of the DAMAGE layer: the same recipe with the layer switched off (Amount 0) and
# on (default), (1) as the whole tile at SIZE dots and (2) as three zoomed windows. Run with plain Python (it starts Blender itself).
# Use:  python3 -I before_after.py [SIZE]       Output: ../tests/damage_before_after/
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1254
OUT = os.path.abspath(os.path.join(HERE, '..', 'tests', 'damage_before_after'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
os.makedirs(OUT, exist_ok=True)
jobs = {'before': {'params': {'damage.amount': 0.0}}, 'after': {}}
subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, OUT, str(SIZE), '0.5,0.5,1.0', json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
windows = {'window_a': '0.2,0.354,0.4', 'window_b': '0.7,0.75,0.4', 'window_c': '0.62,0.2,0.4'}
for name, window in windows.items():
    subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, os.path.join(OUT, name), '500', window, json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a, b = cv2.imread(os.path.join(OUT, name, 'before_colour.png')), cv2.imread(os.path.join(OUT, name, 'after_colour.png'))
    for image, text in ((a, 'DAMAGE off (Amount 0)'), (b, 'DAMAGE on (defaults)')):
        cv2.putText(image, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(image, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(OUT, name + '_before_after.png'), np.hstack([a, b]))
whole = [cv2.imread(os.path.join(OUT, f'{n}_colour.png')) for n in ('before', 'after')]
cv2.imwrite(os.path.join(OUT, 'whole_tile_before_after.png'), np.hstack(whole))
print('wrote', OUT)
