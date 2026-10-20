# What this does (plain words): the RESOLUTION and AREA tests, driving Blender (python3 -I).
#  RESOLUTION: one sampled description (seed 7) baked at 512, 1254 and 2508 dots: the bake time of each, and what changes (sharpness of edges, size of files).
#  AREA: the sampler asked for a 2508-dot design tile (about 4 times the content: 10 planks, 16 knots ...) baked at 2508 dots = a picture 2 x 2 tiles big with NEW content
#  everywhere (nothing repeats); then (a) the four 1254 quarters are compared with each other (they must be different pictures), (b) the half-tile shift test is made on the big
#  picture, (c) the seam measure is taken across the middle lines. Output: ../resolution/ and ../area/ plus JSON tables.
import json, os, subprocess, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(WOOD, 'generator'))
import sampler
import score_tools as st
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
def bake(desc_path, out, size, shift=None):
    cmd = [BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(WOOD, 'generator', 'wood_generator.py'), '--', desc_path, out, '--size', str(size)]
    if shift: cmd += ['--shift', str(shift[0]), str(shift[1])]
    t0 = time.time(); subprocess.run(cmd, capture_output=True); return round(time.time() - t0, 1)
which = sys.argv[1:] or ['resolution', 'area']
if 'resolution' in which:
    d = sampler.sample_description(7)
    p = os.path.join(WOOD, 'resolution', 'sample_7.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w'), separators=(',', ':'))
    rows = []
    for size in (512, 1254, 2508):
        out = os.path.join(WOOD, 'resolution', f'size_{size}')
        seconds = bake(p, out, size)
        bj = json.load(open(os.path.join(out, 'bake.json')))
        bytes_png = sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out) if f.endswith('.png'))
        rows.append({'size': size, 'wall_seconds': seconds, 'colour_render_s': bj.get('colour_render_s'), 'shapes': bj.get('shapes'), 'mesh_faces': bj.get('mesh_faces'), 'png_megabytes': round(bytes_png / 1e6, 1)})
        print(json.dumps(rows[-1]), flush=True)
    # sharpness: share of dots on strong edges (gradient over 40 levels) and the mean gradient, of each size seen at 1254 dots (the 2508 and 512 pictures resized to 1254)
    sharp = {}
    for size in (512, 1254, 2508):
        g = cv2.cvtColor(cv2.resize(cv2.imread(os.path.join(WOOD, 'resolution', f'size_{size}', 'colour.png')), (1254, 1254), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(float)
        gx, gy = np.abs(np.diff(g, axis=1)).mean(), np.abs(np.diff(g, axis=0)).mean()
        sharp[size] = {'mean_gradient': round(float((gx + gy) / 2), 3), 'texture_compare_overall': st.tc.score_set('wood', os.path.join(WOOD, 'resolution', f'size_{size}'))['overall']}
    json.dump({'rows': rows, 'sharpness_seen_at_1254': sharp}, open(os.path.join(WOOD, 'resolution', 'resolution_table.json'), 'w'), indent=1)
    print(json.dumps(sharp))
if 'area' in which:
    d = sampler.sample_description(11, tile=2508)
    p = os.path.join(WOOD, 'area', 'area_2508.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w'), separators=(',', ':'))
    out, out_s = os.path.join(WOOD, 'area', 'area_2508'), os.path.join(WOOD, 'area', 'area_2508_shifted')
    t_a = bake(p, out, 2508); t_b = bake(p, out_s, 2508, (0.5, 0.5))
    a = cv2.imread(os.path.join(out, 'colour.png')); b = cv2.imread(os.path.join(out_s, 'colour.png'))
    h, w = a.shape[:2]
    rolled = np.roll(a, (h // 2, w // 2), axis=(0, 1)).astype(float); diff = np.abs(rolled - b.astype(float)).mean(axis=-1)
    wrong = np.abs(np.roll(a, (h // 3, w // 3), axis=(0, 1)).astype(float) - b.astype(float)).mean(axis=-1)
    quarters = {'top_left': a[:1254, :1254], 'top_right': a[:1254, 1254:], 'bottom_left': a[1254:, :1254], 'bottom_right': a[1254:, 1254:]}
    grey = {k: cv2.cvtColor(v, cv2.COLOR_BGR2GRAY) for k, v in quarters.items()}
    names = list(grey); pair_rows = []
    for i in range(4):
        for j in range(i + 1, 4):
            pair_rows.append({'a': names[i], 'b': names[j], 'mean_abs_difference_levels': round(float(np.abs(grey[names[i]].astype(float) - grey[names[j]].astype(float)).mean()), 2), 'ssim': round(st.pc.ssim(grey[names[i]], grey[names[j]]), 3)})
    gg = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(float)
    inner = float(np.abs(np.diff(gg, axis=1)).mean()); inner_down = float(np.abs(np.diff(gg, axis=0)).mean())          # a normal one-dot jump ALONG the rows and DOWN the columns (the wood changes faster down than along)
    mid_v = float(np.abs(gg[:, 1253] - gg[:, 1254]).mean()); mid_h = float(np.abs(gg[1253] - gg[1254]).mean())
    wrap_v = float(np.abs(gg[:, 0] - gg[:, -1]).mean()); wrap_h = float(np.abs(gg[0] - gg[-1]).mean())
    # a repeated 2 x 2 tiling of ONE 1254 tile as the control: the quarter pairs would be identical
    res = {'bake_seconds': t_a, 'half_tile': {'mean_difference_levels': round(float(diff.mean()), 3), 'share_over_40': round(float((diff > 40).mean()), 5), 'wrong_roll_mean_difference': round(float(wrong.mean()), 3), 'wrong_roll_share_over_40': round(float((wrong > 40).mean()), 4)},
           'quarters_pairs': pair_rows, 'seam_across_middle_over_normal_jump': {'vertical_line': round(mid_v / inner, 2), 'horizontal_line': round(mid_h / inner_down, 2)},
           'wrap_edge_over_normal_jump': {'left_right': round(wrap_v / inner, 2), 'top_bottom': round(wrap_h / inner_down, 2)}}
    json.dump(res, open(os.path.join(WOOD, 'area', 'area_scores.json'), 'w'), indent=1)
    cv2.imwrite(os.path.join(WOOD, 'area', 'area_2508_preview.png'), cv2.resize(a, (1254, 1254), interpolation=cv2.INTER_AREA))
    tile2 = np.vstack([np.hstack([a, a]), np.hstack([a, a])])
    cv2.imwrite(os.path.join(WOOD, 'area', 'area_tiled_2x2_preview.png'), cv2.resize(tile2, (1254, 1254), interpolation=cv2.INTER_AREA))
    print(json.dumps(res))
