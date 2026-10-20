# What this does (plain words): a quick look at the DAMAGE layer while it is being tuned. It bakes the finished recipe (colour) and the
# damage Mask alone at a small size with the settings you give, then writes one picture with the damage layer on top of a zoomed crop.
# Use (plain python):  python3 -I preview.py NAME SIZE '{"damage.chip_amount": 0.7}' [CROP_X0 CROP_Y0 CROP_SIZE]
# Output: previews/NAME_full.png (colour), previews/NAME_mask.png, previews/NAME_zoom.png (crop of colour and mask side by side, 4x)
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
name, size, params = sys.argv[1], int(sys.argv[2]), json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
x0, y0, crop = (int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (0, 0, size // 2)
out = os.path.join(HERE, 'previews'); os.makedirs(out, exist_ok=True)
folder = os.path.join(out, 'work_' + name)
views = {'full': {}, 'mask': {'debug_view': 'damage.mask'}}
subprocess.run(BLENDER + [os.path.join(HERE, '..', 'tests', 'bake_tools.py'), '--', os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'), folder, str(size), '4',
                          json.dumps(views), json.dumps(params), 'Colour'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
full = cv2.imread(os.path.join(folder, 'full_colour.png')); mask = cv2.imread(os.path.join(folder, 'mask_colour.png'))
cv2.imwrite(os.path.join(out, name + '_full.png'), full); cv2.imwrite(os.path.join(out, name + '_mask.png'), mask)
z = lambda im: cv2.resize(im[y0:y0 + crop, x0:x0 + crop], None, fx=4 if crop <= 256 else 2, fy=4 if crop <= 256 else 2, interpolation=cv2.INTER_NEAREST)
cv2.imwrite(os.path.join(out, name + '_zoom.png'), np.hstack([z(full), z(mask)]))
share = float((mask[..., 0] > 128).mean())
print('mask share of all dots: %.2f%%' % (100 * share))
