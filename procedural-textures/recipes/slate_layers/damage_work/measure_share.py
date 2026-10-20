# What this does (plain words): bakes the whole recipe at a small size with several DAMAGE settings and, for each, measures how much of the picture is
# tan or pale (the same simple measure that was used once on the reference: warm and fairly light, or pale), how that share is spread over a row of
# slates (top to bottom, in tenths) and how big the biggest tan area is. It is only a GUIDE for hand-tuning the default settings: the reference has 2.8 percent
# tan/pale (mostly in the lowest 30 percent of a row; its biggest connected area is 587 dots at 1254 dots per tile).
# Use (plain python):  python3 -I measure_share.py PIXELS 'JSON {name: {settings}}'
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
pixels, variants = int(sys.argv[1]), json.loads(sys.argv[2])
folder = os.path.join(HERE, 'share_work')
# one Blender run per variant is simplest (the settings go in as the base parameters)
def measure(path):
    im = cv2.imread(path)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0] * 100 / 255; a = lab[..., 1] - 128; b = lab[..., 2] - 128
    tan = ((b > 5) & (a > 0) & (L > 30)) | ((L > 42) & (b > 0))
    h = im.shape[0]; y = np.arange(h)
    phase = ((y / (h / 8.0)) - 0.5) % 1.0
    hist = [round(float(tan[(phase >= k / 10) & (phase < (k + 1) / 10)].mean()), 3) for k in range(10)]
    n, _, stats, _ = cv2.connectedComponentsWithStats(tan.astype(np.uint8), 8)
    areas = stats[1:, cv2.CC_STAT_AREA] * (1254.0 / im.shape[0]) ** 2          # in dots at 1254
    areas = areas[areas >= 4]
    return round(100 * float(tan.mean()), 2), hist, (int(areas.max()) if len(areas) else 0)
for name, settings in variants.items():
    out = os.path.join(folder, name)
    subprocess.run(BLENDER + [os.path.join(HERE, '..', 'tests', 'bake_tools.py'), '--', os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'), out, str(pixels), '4',
                              json.dumps({'full': {}}), json.dumps(settings), 'Colour'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(name, settings, '-> tan share % / by tenth of a row / biggest area (dots at 1254):', measure(os.path.join(out, 'full_colour.png')), flush=True)
