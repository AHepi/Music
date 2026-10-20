# What this does (plain words): scores one baked folder with BOTH comparison tools and writes one summary json. Because the reference "height.png" that
# texture_compare reads was smoothed by 0.8 dots and stretched to full range while the uploaded 8-bit height (read by pixel_compare) was not, the
# texture score is made twice: on the folder as baked, and on a "texture view" copy whose height got the same 0.8 dot smoothing and stretch.
# Use: python3 -I score_folder.py FOLDER NAME_FOR_SUMMARY [--out scores_folder]
import json, os, subprocess, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..')); PROC = os.path.abspath(os.path.join(SLATE, '..', '..'))
folder, name = sys.argv[1], sys.argv[2]
out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(SLATE, 'scores')
os.makedirs(out, exist_ok=True)

def run(tool, target, extra=()):
    path = os.path.join(out, f'{name}_{tool}.json')
    subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', tool + '.py'), 'slate', target, '--json', path, *extra], capture_output=True, text=True)
    return json.load(open(path))

pixel = run('pixel_compare', folder, ['--sheet', os.path.join(out, f'{name}_diff.png')])
texture = run('texture_compare', folder, ['--sheet', os.path.join(out, f'{name}_texture_sheet.png')])
view = os.path.join(folder, 'texture_view')
os.makedirs(view, exist_ok=True)
for file in ('colour.png', 'normal.png'):
    cv2.imwrite(os.path.join(view, file), cv2.imread(os.path.join(folder, file), cv2.IMREAD_UNCHANGED))
h = cv2.imread(os.path.join(folder, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
h = h[..., 0] if h.ndim == 3 else h
h = cv2.GaussianBlur(np.pad(h, 12, mode='wrap'), (0, 0), 0.8)[12:-12, 12:-12]
h = (h - h.min()) / (h.max() - h.min())
cv2.imwrite(os.path.join(view, 'height.png'), (h * 65535).astype(np.uint16))
texture_view = run('texture_compare', view)
bake = json.load(open(os.path.join(folder, 'bake.json'))) if os.path.exists(os.path.join(folder, 'bake.json')) else {}
keep = ['colour_ssim', 'colour_mean_delta_e', 'colour_p95_delta_e', 'colour_psnr_db', 'edge_skill_2px', 'edge_f1_2px', 'height_mae_levels', 'height_mae_best_fit_levels', 'height_ssim', 'height_correlation',
        'normal_mean_angle_degrees', 'normal_median_angle_degrees', 'tier_reached']
summary = {'name': name, 'pixel': {k: pixel[k] for k in keep if k in pixel}, 'texture_as_baked': {'overall': texture['overall'], **texture['groups']},
           'texture_view': {'overall': texture_view['overall'], **texture_view['groups']}, 'seam_ratio': texture['facts']['seam_ratio_candidate'], 'bake': bake}
json.dump(summary, open(os.path.join(out, f'{name}_summary.json'), 'w'), indent=1)
print(json.dumps(summary))
