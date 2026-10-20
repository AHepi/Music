# Plain note: takes the raw files Material Maker wrote (albedo.png, normal.png, displace.exr, rough.exr, occlusion.exr; all 2048 x 2048)
# and makes the folder the comparison tools expect: colour.png, normal.png (OpenGL, green up), height.png (16-bit), plus roughness.png and
# ao.png, all shrunk to 1254 x 1254 (area averaging) so they can be compared dot for dot with the references.
# It also CHECKS which way the exported normal map's green channel points, by comparing it with the slope of the exported height.
# Run: python3 -I finish_maps.py RAW_FOLDER STEM OUT_FOLDER   (the EXR files must first have been converted with exr_to_png16.py inside Blender)
import sys, os, json
import numpy as np
import cv2

raw, stem, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
report = {}
SIZE = 1254


def load(path):
    return cv2.imread(path, cv2.IMREAD_UNCHANGED)


def shrink(img):
    if img.shape[0] == SIZE:
        return img
    return cv2.resize(img, (SIZE, SIZE), interpolation=cv2.INTER_AREA)


albedo = load(f'{raw}/{stem}_albedo.png')
albedo = albedo[..., :3]
cv2.imwrite(f'{out}/colour.png', shrink(albedo))

report = {}
# the "Blender" export writes displace.exr as 1 - height (found by testing: bricks come out dark), so turn it back into a true height
height = 1.0 - load(f'{raw}/{stem}_displace.png16.png').astype(np.float64) / 65535.0
report['note'] = 'height.png = 1 - displace.exr (the Blender export stores the height upside down)'
height_small = shrink(height)
cv2.imwrite(f'{out}/height.png', (np.clip(height_small, 0, 1) * 65535 + 0.5).astype(np.uint16))
for name, fn in (('roughness', 'rough'), ('ao', 'occlusion')):
    p = f'{raw}/{stem}_{fn}.png16.png'
    if os.path.exists(p):
        a = shrink(load(p).astype(np.float64) / 65535.0)
        cv2.imwrite(f'{out}/{name}.png', (np.clip(a, 0, 1) * 65535 + 0.5).astype(np.uint16))

normal = load(f'{raw}/{stem}_normal.png')[..., :3].astype(np.float64) / 255.0   # BGR order from cv2
rgb = normal[..., ::-1]
# convention check on the full-size data: correlate green with the slope of the height along image rows
hf = cv2.GaussianBlur(height.astype(np.float32), (0, 0), 1.5)
d_row = np.gradient(hf, axis=0)
d_col = np.gradient(hf, axis=1)
g = rgb[..., 1] - 0.5
r = rgb[..., 0] - 0.5
c_g = float(np.corrcoef(g.ravel(), d_row.ravel())[0, 1])
c_r = float(np.corrcoef(r.ravel(), d_col.ravel())[0, 1])
report['green_vs_row_slope_corr'] = round(c_g, 3)
report['red_vs_column_slope_corr'] = round(c_r, 3)
# OpenGL (Blender): green correlates POSITIVELY with the slope along rows (downwards); red correlates NEGATIVELY with slope along columns
report['green_convention'] = 'OpenGL (green up)' if c_g > 0 else 'DirectX (green down)'
report['red_sign'] = 'normal' if c_r < 0 else 'flipped'
flip_green = c_g < 0
fix = rgb.copy()
if flip_green:
    fix[..., 1] = 1.0 - fix[..., 1]
if c_r > 0:
    fix[..., 0] = 1.0 - fix[..., 0]
report['applied_fix_to_make_opengl'] = {'flip_green': bool(flip_green), 'flip_red': bool(c_r > 0)}
fix_small = shrink(fix)
cv2.imwrite(f'{out}/normal.png', (np.clip(fix_small[..., ::-1], 0, 1) * 255 + 0.5).astype(np.uint8))
cv2.imwrite(f'{out}/normal_as_exported.png', (np.clip(shrink(rgb)[..., ::-1], 0, 1) * 255 + 0.5).astype(np.uint8))
json.dump(report, open(f'{out}/finish_report.json', 'w'), indent=1)
print(json.dumps(report))
