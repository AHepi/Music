# What this does (plain words): a quick look at the OUTLINE AND SHADOW layer while it is being tuned. It bakes one zoomed WINDOW of the finished
# recipe (colour) with the layer on and with it off (Amount 0), plus the layer's own Mask and the exact height, and writes one sheet.
# Use (plain python, it starts Blender itself):
#   python3 -I preview.py NAME PIXELS '{"outline_and_shadow.shadow_width": 0.03}' cx,cy,width
#   cx, cy = window centre in tile units (cy counts from the BOTTOM), width = window size in tile units (0.3 = a bit under a third of the tile).
# Output: previews/NAME_sheet.png (left to right: layer OFF, layer ON, layer Mask alone, height) and previews/NAME_on.png
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
name, pixels = sys.argv[1], int(sys.argv[2])
params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
window = sys.argv[4] if len(sys.argv) > 4 else '0.5,0.5,1.0'
folder = os.path.join(HERE, 'previews', 'work_' + name)
os.makedirs(folder, exist_ok=True)
jobs = {'on': {'params': params},
        'off': {'params': dict(params, **{'outline_and_shadow.amount': 0.0})},
        'mask': {'params': dict(params, debug_view='outline_and_shadow.mask')},
        'height': {'params': params, 'channel': 'Height'}}
subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, folder, str(pixels), window, json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
read = lambda n, c: cv2.imread(os.path.join(folder, f'{n}_{c}.png'))
on, off, mask = read('on', 'colour'), read('off', 'colour'), read('mask', 'colour')
height = cv2.imread(os.path.join(folder, 'height_height.png'), cv2.IMREAD_UNCHANGED)
height = cv2.cvtColor((height.astype(np.float32) / 65535 * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR) if height.ndim == 2 else (height.astype(np.float32) / 65535 * 255).astype(np.uint8)
def label(im, text):
    im = im.copy()
    cv2.putText(im, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.putText(im, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 1, cv2.LINE_AA)
    return im
sheet = np.hstack([label(off, 'layer OFF'), label(on, 'layer ON'), label(mask, 'layer mask'), label(height, 'height')])
os.makedirs(os.path.join(HERE, 'previews'), exist_ok=True)
cv2.imwrite(os.path.join(HERE, 'previews', name + '_sheet.png'), sheet)
cv2.imwrite(os.path.join(HERE, 'previews', name + '_on.png'), on)
print('wrote', os.path.join(HERE, 'previews', name + '_sheet.png'))
