# What this does (plain words): bakes ONE description at three picture sizes (512, 1254, 2508 dots square) and tabulates the time each takes, what is
# the same (the shapes, the layout), and what changes (edge sharpness, fine detail, file size, how close the small picture is to the big one shrunk).
# The description is measured in "tile dots" (1254 per tile), not in picture dots, so one description draws at any size: this is the "vector" advantage.
# Use (system python):  python3 -I resolution_test.py DESCRIPTION.json OUT_FOLDER [samples]
import json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import pixel_compare as pc
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
description_path, out = sys.argv[1], sys.argv[2]
samples = sys.argv[3] if len(sys.argv) > 3 else '8'
rows, pics = [], {}
for size in (512, 1254, 2508):
    folder = os.path.join(out, f'size_{size}')
    subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(HERE, 'brick_generator.py'), '--', description_path, folder, '--size', str(size), '--samples', samples], capture_output=True, text=True)
    bake = json.load(open(os.path.join(folder, 'bake.json')))
    c = cv2.imread(os.path.join(folder, 'colour.png'))
    n = cv2.imread(os.path.join(folder, 'normal.png'))
    pics[size] = (c, n)
    grey = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY).astype(float)
    gx, gy = cv2.Sobel(grey, cv2.CV_64F, 1, 0, ksize=3) / 8, cv2.Sobel(grey, cv2.CV_64F, 0, 1, ksize=3) / 8
    sharp = np.hypot(gx, gy)
    strong = float((sharp > 20).mean())
    # steepest edge: the 99.9th percentile of the gradient (a sharper picture has steeper edges per dot, measured per tile dot)
    rows.append({'size': size, 'seconds_total': bake['seconds'], 'seconds_colour_render': bake['colour_render_seconds'], 'seconds_mesh': bake['mesh_seconds'],
                 'seconds_derive': bake['derive_seconds'], 'shapes': bake['shapes'], 'triangles': bake['triangles'],
                 'colour_png_kilobytes': round(os.path.getsize(os.path.join(folder, 'colour.png')) / 1024), 'share_of_dots_on_a_strong_edge': round(strong, 4),
                 'edge_steepness_p999_per_tile_dot': round(float(np.percentile(sharp, 99.9)) * size / 1254, 1)})
    print(rows[-1], flush=True)
big = cv2.resize(pics[2508][0], (1254, 1254), interpolation=cv2.INTER_AREA)
mid = pics[1254][0]
small_up = cv2.resize(pics[512][0], (1254, 1254), interpolation=cv2.INTER_CUBIC)
def ssim(a, b):
    return pc.ssim(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY))
result = {'rows': rows, 'ssim_1254_vs_2508_shrunk': round(ssim(mid, big), 4), 'ssim_512_enlarged_vs_2508_shrunk': round(ssim(small_up, big), 4),
          'mean_abs_diff_1254_vs_2508_shrunk': round(float(np.abs(mid.astype(float) - big.astype(float)).mean()), 3)}
json.dump(result, open(os.path.join(out, 'resolution_result.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
# side-by-side crop (same 160 x 160 dot patch of the tile at the three sizes, shown at the same screen size)
def crop(img, size):
    s = size / 1254.0
    patch = img[int(300 * s):int(460 * s), int(300 * s):int(460 * s)]
    return cv2.resize(patch, (480, 480), interpolation=cv2.INTER_NEAREST)
cv2.imwrite(os.path.join(out, 'crops_512_1254_2508.png'), np.hstack([crop(pics[s][0], s) for s in (512, 1254, 2508)]))
