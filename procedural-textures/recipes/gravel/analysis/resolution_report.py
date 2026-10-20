# What this does (plain words): the RESOLUTION table. The same description (S_v4) was baked at 512, 1254 and 2508 dots across. This reports for each: the bake time
# (and which part grows), how sharp the colour picture is (average size of the change between neighbouring dots, per tile dot), how strong the normal map is
# (average slope), whether the shrunk big picture matches the small one (SSIM and average difference after shrinking everything to 512), and the "same kind" score.
import json, os, sys, subprocess
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(G, '..', '..', 'lib'))
import pixel_compare as pc
folders = {512: os.path.join(G, 'resolution', 'out', 'S_v4_512'), 1254: os.path.join(G, 'outputs', 'S_v4'), 2508: os.path.join(G, 'resolution', 'out', 'S_v4_2508')}
rows, small = [], {}
for size, f in folders.items():
    if not os.path.exists(os.path.join(f, 'colour.png')):
        continue
    c = cv2.imread(os.path.join(f, 'colour.png')).astype(np.float64)
    n = cv2.imread(os.path.join(f, 'normal.png')).astype(np.float64)[..., ::-1] / 255 * 2 - 1
    bake = json.load(open(os.path.join(f, 'bake.json')))
    dots_per_px = 1254.0 / size
    grad = (np.abs(np.diff(c, axis=1)).mean() + np.abs(np.diff(c, axis=0)).mean()) / 2          # change per picture dot
    row = {'size': size, 'bake_seconds_total': bake['total_s'], 'colour_render_s': bake['colour_render_s'], 'height_render_s': bake['height_render_s'], 'shapes_and_mesh_s': round(bake['shapes_s'] + bake['mesh_s'], 1),
           'change_between_neighbour_dots_per_tile_dot': round(float(grad / dots_per_px), 2), 'mean_normal_slope': round(float(np.hypot(n[..., 0], n[..., 1]).mean()), 4),
           'file_megabytes': round(sum(os.path.getsize(os.path.join(f, x)) for x in os.listdir(f)) / 1e6, 1)}
    g = cv2.cvtColor(cv2.resize(c.astype(np.uint8), (512, 512), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float64)
    small[size] = g
    rows.append(row)
for row in rows:
    if row['size'] != 512 and 512 in small:
        row['ssim_against_512_after_shrinking'] = round(pc.ssim(small[row['size']], small[512]), 3)
        row['mean_difference_against_512_after_shrinking_levels'] = round(float(np.abs(small[row['size']] - small[512]).mean()), 2)
json.dump(rows, open(os.path.join(G, 'resolution', 'resolution_report.json'), 'w'), indent=1)
for r in rows:
    print(r)
