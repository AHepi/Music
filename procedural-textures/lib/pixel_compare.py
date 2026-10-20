# What this does: measures PIXEL accuracy: how closely a generated texture set matches a reference set at every single dot, not just in
# overall look. (texture_compare.py asks "is it the same kind of surface?"; this asks "is it the same picture?") For colour it gives
# the average error in brightness steps (0-255), the peak signal-to-noise ratio, the structural similarity (SSIM, 1.0 = identical
# structure), the average colour difference (Delta E) and how many edges sit within 2 dots of a reference edge. For height it gives the error in 8-bit
# steps (and the error after the best possible brightness/contrast fix, to tell "wrong level" from "wrong shape"). For the normal map
# it gives the angle between the two normals, dot by dot. Because painted textures are full of edges, the edge score has the score of a wrongly placed copy taken off ('edge skill': 0 = no better than luck, 1 = every edge in place). It also draws a difference sheet: reference | generated | where they differ |
# edge overlay (red = edge only in the reference, green = edge only in the generated one, yellow = both).
# The tier names say how far a recipe has got: 'layout' (the features are in the right places), 'close' (a careful eye needs a side-by-side
# to see the difference), 'exact' (practically the same picture).
# Use:  python3 -I pixel_compare.py REFERENCE_NAME CANDIDATE_FOLDER [--json out.json] [--sheet diff.png]
#   CANDIDATE_FOLDER holds colour.png, normal.png (OpenGL), height.png as in texture_compare.py. REFERENCE_NAME: brick slate wood metal mud gravel.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import texture_compare as tc  # noqa: E402

REFERENCE_FOLDER = tc.REFERENCE_FOLDER

# (measure, 'min' or 'max', layout, close, exact): a tier is reached when ALL its measures pass
TIERS = [
    ('layout', {'edge_skill_2px': ('min', 0.30), 'colour_mean_delta_e': ('max', 20.0), 'height_mae_best_fit_levels': ('max', 40.0)}),
    ('close', {'edge_skill_2px': ('min', 0.55), 'colour_ssim': ('min', 0.60), 'colour_mean_delta_e': ('max', 10.0), 'height_mae_best_fit_levels': ('max', 20.0),
              'normal_mean_angle_degrees': ('max', 12.0)}),
    ('exact', {'edge_skill_2px': ('min', 0.85), 'colour_ssim': ('min', 0.92), 'colour_mean_delta_e': ('max', 3.0), 'height_mae_best_fit_levels': ('max', 6.0),
               'normal_mean_angle_degrees': ('max', 4.0)}),
]


def load_bgr8(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    image = image[..., :3] if image.ndim == 3 else np.stack([image] * 3, axis=-1)
    image = image.astype(np.float64)
    image = image / 257.0 if image.max() > 255 else image
    if image.shape[:2] != (tc.TILE, tc.TILE):
        image = cv2.resize(image, (tc.TILE, tc.TILE), interpolation=cv2.INTER_AREA)
    return image


def ssim(a, b):
    """Structural similarity of two grey pictures on a 0..255 scale (the usual 11 x 11 Gaussian window)."""
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    a, b = a.astype(np.float64), b.astype(np.float64)
    blur = lambda x: cv2.GaussianBlur(x, (11, 11), 1.5)
    mu_a, mu_b = blur(a), blur(b)
    var_a, var_b, covariance = blur(a * a) - mu_a ** 2, blur(b * b) - mu_b ** 2, blur(a * b) - mu_a * mu_b
    map_ = ((2 * mu_a * mu_b + c1) * (2 * covariance + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (var_a + var_b + c2))
    return float(map_[5:-5, 5:-5].mean())


def edge_map(grey8):
    return cv2.Canny(grey8, 50, 150) > 0


def edge_f1(edges_a, edges_b, tolerance=2):
    """Share of edge dots that have a matching edge dot within `tolerance` dots in the other picture (precision, recall, F1)."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tolerance + 1, 2 * tolerance + 1))
    near_a = cv2.dilate(edges_a.astype(np.uint8), kernel) > 0
    near_b = cv2.dilate(edges_b.astype(np.uint8), kernel) > 0
    recall = float((edges_a & near_b).sum() / max(edges_a.sum(), 1))
    precision = float((edges_b & near_a).sum() / max(edges_b.sum(), 1))
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def pixel_report(reference_name, candidate_folder):
    reference_folder = os.path.join(REFERENCE_FOLDER, reference_name)
    report = {'reference': reference_name, 'candidate': candidate_folder}
    ref_colour = load_bgr8(os.path.join(reference_folder, 'colour.png'))
    cand_colour = load_bgr8(os.path.join(candidate_folder, 'colour.png'))
    difference = ref_colour - cand_colour
    mse = float((difference ** 2).mean())
    ref_grey = cv2.cvtColor(np.clip(ref_colour, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    cand_grey = cv2.cvtColor(np.clip(cand_colour, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    lab_ref = tc.srgb_to_lab(ref_colour[..., ::-1] / 255.0)
    lab_cand = tc.srgb_to_lab(cand_colour[..., ::-1] / 255.0)
    delta_e = np.sqrt(((lab_ref - lab_cand) ** 2).sum(axis=-1))
    ref_edges_map, cand_edges_map = edge_map(ref_grey), edge_map(cand_grey)
    precision, recall, f1 = edge_f1(ref_edges_map, cand_edges_map)
    # painted textures are full of edges, so even a wrongly placed copy "matches" a lot by luck; measure the luck and take it off
    luck = float(np.mean([edge_f1(ref_edges_map, np.roll(cand_edges_map, shift, axis=(0, 1)))[2] for shift in ((397, 611), (-523, 289))]))
    skill = max(0.0, (f1 - luck) / max(1.0 - luck, 1e-6))
    report.update({
        'colour_mae_levels': round(float(np.abs(difference).mean()), 2),
        'colour_psnr_db': round(float(10 * np.log10(255.0 ** 2 / max(mse, 1e-9))), 2),
        'colour_ssim': round(ssim(ref_grey, cand_grey), 4),
        'colour_mean_delta_e': round(float(delta_e.mean()), 2),
        'colour_p95_delta_e': round(float(np.percentile(delta_e, 95)), 2),
        'edge_precision_2px': round(precision, 3), 'edge_recall_2px': round(recall, 3), 'edge_f1_2px': round(f1, 3),
        'edge_f1_by_luck': round(luck, 3), 'edge_skill_2px': round(skill, 3),
    })
    ref_height_path = os.path.join(reference_folder, 'height_as_uploaded.png')
    cand_height_path = os.path.join(candidate_folder, 'height.png')
    if os.path.exists(ref_height_path) and os.path.exists(cand_height_path):
        ref_height = load_bgr8(ref_height_path)[..., 0]
        cand_height = load_bgr8(cand_height_path)[..., 0]
        report['height_mae_levels'] = round(float(np.abs(ref_height - cand_height).mean()), 2)
        design = np.stack([cand_height.ravel(), np.ones(cand_height.size)], axis=1)
        gain, offset = np.linalg.lstsq(design, ref_height.ravel(), rcond=None)[0]
        fitted = cand_height * gain + offset
        report['height_mae_best_fit_levels'] = round(float(np.abs(ref_height - fitted).mean()), 2)
        report['height_best_fit_gain_offset'] = [round(float(gain), 3), round(float(offset), 1)]
        report['height_ssim'] = round(ssim(ref_height, cand_height), 4)
        report['height_correlation'] = round(float(np.corrcoef(ref_height.ravel(), cand_height.ravel())[0, 1]), 4)
    ref_normal_path = os.path.join(reference_folder, 'normal.png')
    cand_normal_path = os.path.join(candidate_folder, 'normal.png')
    if os.path.exists(ref_normal_path) and os.path.exists(cand_normal_path):
        a = load_bgr8(ref_normal_path)[..., ::-1] / 255.0 * 2 - 1
        b = load_bgr8(cand_normal_path)[..., ::-1] / 255.0 * 2 - 1
        a /= np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)
        b /= np.maximum(np.linalg.norm(b, axis=-1, keepdims=True), 1e-9)
        angle = np.degrees(np.arccos(np.clip((a * b).sum(axis=-1), -1, 1)))
        report['normal_mean_angle_degrees'] = round(float(angle.mean()), 2)
        report['normal_median_angle_degrees'] = round(float(np.median(angle)), 2)
        report['normal_p95_angle_degrees'] = round(float(np.percentile(angle, 95)), 2)
    reached = 'none'
    for tier_name, rules in TIERS:
        ok = True
        for measure, (direction, limit) in rules.items():
            if measure not in report:
                continue
            value = report[measure]
            ok = ok and (value >= limit if direction == 'min' else value <= limit)
        if ok:
            reached = tier_name
    report['tier_reached'] = reached
    report['tier_rules'] = {name: {m: f'{d} {l}' for m, (d, l) in rules.items()} for name, rules in TIERS}
    return report


def difference_sheet(reference_name, candidate_folder, out_path):
    reference_folder = os.path.join(REFERENCE_FOLDER, reference_name)
    ref = load_bgr8(os.path.join(reference_folder, 'colour.png')).astype(np.uint8)
    cand = load_bgr8(os.path.join(candidate_folder, 'colour.png')).astype(np.uint8)
    difference = np.abs(ref.astype(np.int16) - cand.astype(np.int16)).mean(axis=-1)
    heat = cv2.applyColorMap(np.clip(difference * 4, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    ref_edges = edge_map(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY))
    cand_edges = edge_map(cv2.cvtColor(cand, cv2.COLOR_BGR2GRAY))
    overlay = np.zeros_like(ref)
    overlay[ref_edges] = (0, 0, 255)
    overlay[cand_edges] = (0, 255, 0)
    overlay[ref_edges & cand_edges] = (0, 255, 255)
    overlay = cv2.dilate(overlay, np.ones((2, 2), np.uint8))
    half = tc.TILE // 2
    tiles = [tc.label(cv2.resize(x, (half, half), interpolation=cv2.INTER_AREA), text) for x, text in
             ((ref, 'reference colour'), (cand, 'generated colour'), (heat, 'difference (bright = differs)'), (overlay, 'edges: red ref only, green generated only, yellow both'))]
    cv2.imwrite(out_path, np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])]))
    return out_path


def main(arguments):
    reference_name, candidate_folder = arguments[0], arguments[1]
    report = pixel_report(reference_name, candidate_folder)
    if '--json' in arguments:
        with open(arguments[arguments.index('--json') + 1], 'w') as handle:
            json.dump(report, handle, indent=1)
    if '--sheet' in arguments:
        difference_sheet(reference_name, candidate_folder, arguments[arguments.index('--sheet') + 1])
    print(json.dumps({k: v for k, v in report.items() if k != 'tier_rules'}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
