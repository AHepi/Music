# What this does (plain words): two scale tests with the same generator.
#  AREA: one description of a bigger roof (2 x 2 tiles of NEW unique content, 2508 x 2508 dots, 16 rows of 12 slates) is invented by the sampler and
#        baked in one go. Measured: (a) the wrap-around seam of the big picture, (b) whether the four 1254 quarters repeat each other
#        (largest normalised cross-correlation between quarters, 1.0 would be a copy), (c) the "joint" lines where four quarters would meet, (d) time.
#  RESOLUTION: one sampled description baked at 512, 1254 and 2508 dots: time, and how sharp the edges are (mean gradient of the colour picture).
# Writes ../area/ and ../resolution/. Plain Python (python3 -I) + one Blender run per picture.
import json, os, subprocess, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..')); PROC = os.path.abspath(os.path.join(SLATE, '..', '..'))
sys.path.insert(0, os.path.join(SLATE, 'generator'))
import sampler
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
area_dir, res_dir = os.path.join(SLATE, 'area'), os.path.join(SLATE, 'resolution')
os.makedirs(area_dir, exist_ok=True); os.makedirs(res_dir, exist_ok=True)


def bake(description_path, out_folder, size):
    started = time.time()
    subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(SLATE, 'generator', 'slate_generator.py'), '--', description_path, out_folder, '--size', str(size)], capture_output=True, text=True)
    return round(time.time() - started, 1)


def seam_numbers(image):
    f = image.astype(np.float64)
    normal_x = np.abs(np.diff(f, axis=1)).mean(); normal_y = np.abs(np.diff(f, axis=0)).mean()
    wrap_x = np.abs(f[:, 0] - f[:, -1]).mean(); wrap_y = np.abs(f[0] - f[-1]).mean()
    mid = f.shape[0] // 2
    inner_x = np.abs(f[:, mid] - f[:, mid - 1]).mean(); inner_y = np.abs(f[mid] - f[mid - 1]).mean()
    return {'wrap_seam_ratio_x': round(float(wrap_x / normal_x), 2), 'wrap_seam_ratio_y': round(float(wrap_y / normal_y), 2),
            'middle_line_ratio_x': round(float(inner_x / normal_x), 2), 'middle_line_ratio_y': round(float(inner_y / normal_y), 2)}


def quarter_similarity(image):
    g = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    h = g.shape[0] // 2
    q = [g[:h, :h], g[:h, h:], g[h:, :h], g[h:, h:]]
    best = 0.0
    for i in range(4):
        for j in range(i + 1, 4):
            a = q[i] - q[i].mean(); b = q[j] - q[j].mean()
            corr = np.fft.ifft2(np.fft.fft2(a) * np.conj(np.fft.fft2(b))).real / (np.sqrt((a ** 2).sum() * (b ** 2).sum()))
            best = max(best, float(corr.max()))
    return round(best, 3)


# ---- AREA
d = sampler.sample_description(201, tile=2508)
path = os.path.join(area_dir, 'area_2508.json')
json.dump(d, open(path, 'w'), separators=(',', ':'))
seconds = bake(path, os.path.join(area_dir, 'area_2508'), 2508)
image = cv2.imread(os.path.join(area_dir, 'area_2508', 'colour.png'))
report = {'description_bytes': os.path.getsize(path), 'bake_seconds_total_process': seconds, 'bake_json': json.load(open(os.path.join(area_dir, 'area_2508', 'bake.json'))),
          'seam': seam_numbers(image), 'max_quarter_cross_correlation': quarter_similarity(image)}
# for comparison the reference tile repeated 2 x 2 has quarters that are exact copies
ref = cv2.imread(os.path.join(PROC, 'reference', 'slate', 'colour.png'))
report['reference_repeated_2x2_max_quarter_cross_correlation'] = quarter_similarity(np.tile(ref, (2, 2, 1)))
report['reference_repeated_2x2_seam'] = seam_numbers(np.tile(ref, (2, 2, 1)))
cv2.imwrite(os.path.join(area_dir, 'area_preview_1254.png'), cv2.resize(image, (1254, 1254), interpolation=cv2.INTER_AREA))
json.dump(report, open(os.path.join(area_dir, 'area_report.json'), 'w'), indent=1)
print('AREA', json.dumps(report))

# ---- RESOLUTION
d = sampler.sample_description(1)
path = os.path.join(res_dir, 'sample_1.json')
json.dump(d, open(path, 'w'), separators=(',', ':'))
table = {}
for size in (512, 1254, 2508):
    seconds = bake(path, os.path.join(res_dir, f'size_{size}'), size)
    im = cv2.imread(os.path.join(res_dir, f'size_{size}', 'colour.png'))
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float64)
    gx = np.abs(np.diff(g, axis=1)); 
    bj = json.load(open(os.path.join(res_dir, f'size_{size}', 'bake.json')))
    table[size] = {'process_seconds': seconds, 'bake': bj, 'mean_edge_step_per_dot': round(float(gx.mean()), 3), 'share_of_steps_over_20_levels': round(float((gx > 20).mean()), 4),
                   'colour_png_bytes': os.path.getsize(os.path.join(res_dir, f'size_{size}', 'colour.png'))}
    print('RES', size, table[size]['process_seconds'], table[size]['mean_edge_step_per_dot'], flush=True)
json.dump(table, open(os.path.join(res_dir, 'resolution_table.json'), 'w'), indent=1)
# crop sheet: the same 120 x 120 patch (of the 1254-dot tile) at the three sizes, each scaled up to 360 dots
crops = []
for size in (512, 1254, 2508):
    im = cv2.imread(os.path.join(res_dir, f'size_{size}', 'colour.png'))
    f = size / 1254.0
    x0, y0, w = int(300 * f), int(300 * f), int(120 * f)
    crop = cv2.resize(im[y0:y0 + w, x0:x0 + w], (360, 360), interpolation=cv2.INTER_NEAREST)
    cv2.putText(crop, f'{size} dots', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA); cv2.putText(crop, f'{size} dots', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    crops.append(crop)
cv2.imwrite(os.path.join(res_dir, 'crop_sheet.png'), np.hstack(crops))
