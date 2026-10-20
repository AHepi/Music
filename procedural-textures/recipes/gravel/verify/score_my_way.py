# Verifier script: scores one baked folder the way the builder's score_folder.py does (as baked, plus smoothed-height view), written independently.
import json, os, subprocess, sys
import cv2
import numpy as np
PROC = 'proc-work'
folder, name = sys.argv[1], sys.argv[2]
out = os.path.join(PROC, 'recipes/gravel/verify')
def run(tool, target, extra=()):
    path = os.path.join(out, f'{name}_{tool}.json')
    r = subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', tool + '.py'), 'gravel', target, '--json', path, *extra], capture_output=True, text=True)
    return json.load(open(path))
pixel = run('pixel_compare', folder, ['--sheet', os.path.join(out, f'{name}_diff.png')])
texture = run('texture_compare', folder, ['--sheet', os.path.join(out, f'{name}_texture_sheet.png')])
view = os.path.join(folder, 'texture_view_verifier')
os.makedirs(view, exist_ok=True)
for file in ('colour.png', 'normal.png'):
    cv2.imwrite(os.path.join(view, file), cv2.imread(os.path.join(folder, file), cv2.IMREAD_UNCHANGED))
h = cv2.imread(os.path.join(folder, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
h = h[..., 0] if h.ndim == 3 else h
h = cv2.GaussianBlur(np.pad(h, 12, mode='wrap'), (0, 0), 0.8)[12:-12, 12:-12]
h = (h - h.min()) / (h.max() - h.min())
cv2.imwrite(os.path.join(view, 'height.png'), (h * 65535).astype(np.uint16))
tv = run('texture_compare', view)
res = {'name': name, 'colour_ssim': pixel['colour_ssim'], 'colour_mean_delta_e': pixel['colour_mean_delta_e'], 'edge_skill': pixel['edge_skill_2px'], 'height_mae_best_fit': pixel['height_mae_best_fit_levels'],
       'normal_mean_angle': pixel['normal_mean_angle_degrees'], 'tier': pixel['tier_reached'], 'texture_compare_overall': texture['overall'], 'texture_view_overall': tv['overall']}
json.dump(res, open(os.path.join(out, f'{name}_verifier_summary.json'), 'w'), indent=1)
print(json.dumps(res))
