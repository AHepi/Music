# What this does: measures the six reference colour pictures (and the maps of the ones that have maps) with plain numbers, so the people
# building the recipes have a "look specification" to aim at: the palette (k-means in Lab colour space), how few colours are enough, how
# flat the paint patches are, how big the patches are, how dark and how wide the outlines are, how streaky the picture is, how hard the
# edges are, and how the colour, height and normal pictures relate. It only READS the reference pictures (analysis), it never feeds them
# into a texture recipe.
# Use (plain python, from anywhere):  python3 -I a01_measure_references.py   -> writes ../data/reference_measurements.json and pictures
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(PROC, 'reference')
DATA = os.path.join(HERE, '..', 'data')
PICS = os.path.join(HERE, '..', 'pictures')
SURFACES = ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel', 'mud_golden']
rng = np.random.default_rng(12345)


def load_rgb_u8(path):
    return cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1].copy()


def to_lab(rgb_u8):
    return cv2.cvtColor(rgb_u8.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)


def lab_to_hex(lab_rows):
    rgb = cv2.cvtColor(np.asarray(lab_rows, np.float32).reshape(-1, 1, 3), cv2.COLOR_Lab2RGB).reshape(-1, 3)
    rgb = np.clip(np.round(rgb * 255.0), 0, 255).astype(int)
    return ['#%02x%02x%02x' % tuple(c) for c in rgb]


def nearest_labels(lab, centres, chunk=200000):
    flat = lab.reshape(-1, 3)
    labels = np.empty(len(flat), np.int32)
    errors = np.empty(len(flat), np.float32)
    for start in range(0, len(flat), chunk):
        part = flat[start:start + chunk]
        distance = np.linalg.norm(part[:, None, :] - centres[None, :, :], axis=2)
        labels[start:start + chunk] = distance.argmin(axis=1)
        errors[start:start + chunk] = distance.min(axis=1)
    return labels.reshape(lab.shape[:2]), errors.reshape(lab.shape[:2])


def kmeans_lab(lab, k, sample=160000):
    flat = lab.reshape(-1, 3)
    pick = flat[rng.integers(0, len(flat), sample)].astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.3)
    _, _, centres = cv2.kmeans(pick, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    return centres


def mode_filter(labels, k, size=5):
    best = np.zeros(labels.shape, np.float32) - 1
    result = np.zeros(labels.shape, np.int32)
    for index in range(k):
        score = cv2.boxFilter((labels == index).astype(np.float32), -1, (size, size), normalize=True, borderType=cv2.BORDER_WRAP)
        better = score > best
        result[better] = index
        best[better] = score[better]
    return result


def wrap_pad(image, pad):
    return np.pad(image, ((pad, pad), (pad, pad)) + ((0, 0),) * (image.ndim - 2), mode='wrap')


def wrap_unpad(image, pad):
    return image[pad:-pad, pad:-pad]


def patch_sizes(labels, k, min_area=12):
    """Connected patches of one palette label each (the picture is a seamless tile, so merge across the wrap edge by tiling 2 x 2)."""
    areas = []
    for index in range(k):
        mask = (labels == index).astype(np.uint8)
        count, comp, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for a in stats[1:, cv2.CC_STAT_AREA]:
            areas.append(int(a))
    areas = np.array(areas)
    big = areas[areas >= min_area]
    diameters = 2.0 * np.sqrt(big / np.pi)
    weights = big.astype(float)
    order = np.argsort(diameters)
    cumulative = np.cumsum(weights[order]) / weights.sum()
    area_weighted_median = float(diameters[order][np.searchsorted(cumulative, 0.5)])
    p25 = float(diameters[order][np.searchsorted(cumulative, 0.25)])
    p75 = float(diameters[order][np.searchsorted(cumulative, 0.75)])
    return {'patches_at_least_12px': int(len(big)), 'median_diameter_px_by_count': float(np.median(diameters)),
            'area_weighted_median_diameter_px': area_weighted_median, 'area_weighted_p25_diameter_px': p25,
            'area_weighted_p75_diameter_px': p75}


def thin_dark_lines(lightness, kernel_size):
    """Black top-hat: how much darker each pixel is than the closing of its surroundings; keeps only dark features narrower than the kernel."""
    pad = kernel_size
    padded = wrap_pad(lightness.astype(np.float32), pad)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    closing = cv2.morphologyEx(padded, cv2.MORPH_CLOSE, kernel)
    return wrap_unpad(closing - padded, pad)


def ridge_widths(mask):
    """Width of each thin line in a binary mask: twice the distance-transform value at the ridge (medial axis) pixels."""
    distance = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    local_max = cv2.dilate(distance, np.ones((3, 3), np.uint8))
    ridge = (distance >= local_max - 1e-6) & (distance >= 1.0)
    return 2.0 * distance[ridge] - 1.0, ridge


def row_profile_dips(lightness):
    """Horizontal outlines (courses of brick or slate, plank gaps) show up as dark dips in the row-by-row average lightness.
    Returns how many dips, their width at half depth (px), how deep (lightness units) and how dark the dip bottom is."""
    profile = lightness.mean(axis=1)
    smooth = np.convolve(np.r_[profile[-3:], profile, profile[:3]], np.ones(3) / 3, mode='valid')
    baseline = np.array([np.median(np.take(smooth, range(i - 30, i + 31), mode='wrap')) for i in range(len(smooth))])
    dip = baseline - smooth
    peaks = [i for i in range(len(dip)) if dip[i] > 5 and dip[i] == dip[max(0, i - 12):i + 13].max()]
    widths, depths = [], []
    for p in peaks:
        half = dip[p] / 2.0
        left = p
        while dip[(left - 1) % len(dip)] > half and p - left < 40:
            left -= 1
        right = p
        while dip[(right + 1) % len(dip)] > half and right - p < 40:
            right += 1
        widths.append(right - left + 1)
        depths.append(dip[p])
    if not peaks:
        return {'dips': 0}
    return {'dips': len(peaks), 'width_at_half_depth_px_median': float(np.median(widths)), 'widths': [int(w) for w in widths],
            'depth_lightness_median': float(np.median(depths)), 'bottom_lightness_median': float(np.median([smooth[p] for p in peaks]))}


def edge_profile_rise(lightness, samples=5000, half=4, minimum_step=10.0):
    """How abrupt the strong edges are: for each edge, 'equivalent width' = (jump over +-4 px) / (steepest slope along the way), in pixels.
    A perfect one-pixel step gives about 1; a smooth ramp 6 px long gives 6."""
    gx = cv2.Sobel(lightness, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lightness, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.hypot(gx, gy)
    edges = cv2.Canny(np.clip(lightness * 2.55, 0, 255).astype(np.uint8), 40, 100)
    ys, xs = np.nonzero(edges[half + 2:-half - 2, half + 2:-half - 2])
    ys += half + 2
    xs += half + 2
    pick = rng.choice(len(ys), min(samples, len(ys)), replace=False)
    ys, xs = ys[pick], xs[pick]
    ux, uy = gx[ys, xs] / (magnitude[ys, xs] + 1e-6), gy[ys, xs] / (magnitude[ys, xs] + 1e-6)
    offsets = np.linspace(-half, half, 8 * half + 1)
    map_x = (xs[:, None] + ux[:, None] * offsets[None, :]).astype(np.float32)
    map_y = (ys[:, None] + uy[:, None] * offsets[None, :]).astype(np.float32)
    profile = cv2.remap(lightness.astype(np.float32), map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    step = profile[:, -1] - profile[:, 0]
    slope = np.abs(np.diff(profile, axis=1)).max(axis=1) / (offsets[1] - offsets[0])
    keep = np.abs(step) >= minimum_step
    width = np.abs(step[keep]) / np.maximum(slope[keep], 1e-6)
    return {'median_equivalent_width_px': float(np.median(width)), 'p25': float(np.percentile(width, 25)), 'p75': float(np.percentile(width, 75)),
            'share_of_edges_within_2px': float((width <= 2.0).mean()), 'median_step_lightness': float(np.median(np.abs(step[keep]))),
            'edges_measured': int(keep.sum())}


def autocorrelation_length(grey, axis):
    """Distance where the (mean-removed) picture's self-similarity along one axis drops to 1/e, in pixels. Wrap-around is right for a seamless tile."""
    centred = grey - grey.mean()
    power = np.abs(np.fft.fft2(centred)) ** 2
    autocorrelation = np.fft.ifft2(power).real
    autocorrelation /= autocorrelation[0, 0]
    line = autocorrelation[0, :grey.shape[1] // 2] if axis == 'x' else autocorrelation[:grey.shape[0] // 2, 0]
    below = np.where(line < 1.0 / np.e)[0]
    return float(below[0]) if len(below) else float(len(line))


def structure_coherence(lightness, sigma_integrate=20):
    gx = cv2.Sobel(lightness, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lightness, cv2.CV_32F, 0, 1, ksize=3)
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), sigma_integrate)
    jyy = cv2.GaussianBlur(gy * gy, (0, 0), sigma_integrate)
    jxy = cv2.GaussianBlur(gx * gy, (0, 0), sigma_integrate)
    tr = jxx + jyy
    det_part = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)
    coherence = det_part / (tr + 1e-6)
    # energy of horizontal gradient (x-direction changes = vertical features) vs vertical gradient
    return {'mean_coherence': float(np.average(coherence, weights=tr)),
            'share_of_gradient_energy_across_x': float(jxx.sum() / (jxx.sum() + jyy.sum()))}


def analyse(name):
    folder = os.path.join(REF, name)
    rgb = load_rgb_u8(os.path.join(folder, 'colour.png'))
    lab = to_lab(rgb)
    lightness = lab[..., 0]
    result = {'size': list(rgb.shape[:2])}
    flat_rgb = rgb.reshape(-1, 3)
    result['unique_colours_8bit'] = int(len(np.unique(flat_rgb[:, 0].astype(np.int64) * 65536 + flat_rgb[:, 1].astype(np.int64) * 256 + flat_rgb[:, 2])))
    # contrast
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    result['contrast'] = {
        'lightness_p1_p5_p50_p95_p99': [float(np.percentile(lightness, p)) for p in (1, 5, 50, 95, 99)],
        'lightness_std': float(lightness.std()), 'chroma_mean': float(chroma.mean()), 'chroma_p95': float(np.percentile(chroma, 95)),
        'mean_srgb_hex': '#%02x%02x%02x' % tuple(int(round(v)) for v in rgb.reshape(-1, 3).mean(axis=0)),
    }
    # palette and how few colours are enough
    curve = {}
    centres_by_k = {}
    for k in (3, 4, 6, 8, 12, 16, 24, 32, 64):
        centres = kmeans_lab(lab, k)
        labels, errors = nearest_labels(lab, centres)
        curve[k] = {'mean_error_deltaE': float(errors.mean()), 'p95_error': float(np.percentile(errors, 95))}
        centres_by_k[k] = (centres, labels)
    result['palette_size_curve'] = curve
    for k in (6, 8):
        centres, labels = centres_by_k[k]
        shares = np.bincount(labels.ravel(), minlength=k) / labels.size
        order = np.argsort(centres[:, 0])
        result[f'palette_{k}'] = [{'hex': lab_to_hex(centres[i:i + 1])[0], 'share_percent': round(float(shares[i]) * 100, 1),
                                   'lab': [round(float(v), 1) for v in centres[i]]} for i in order]
    # flat patches
    k = 12
    centres, labels = centres_by_k[12]
    smooth_labels = mode_filter(labels, k, 5)
    result['patches_k12'] = patch_sizes(smooth_labels, k)
    flat_std = np.sqrt(np.maximum(cv2.boxFilter(lightness ** 2, -1, (5, 5)) - cv2.boxFilter(lightness, -1, (5, 5)) ** 2, 0))
    result['flatness'] = {'share_of_pixels_with_5x5_lightness_std_below_1': float((flat_std < 1.0).mean()),
                          'share_below_2': float((flat_std < 2.0).mean()), 'median_5x5_std': float(np.median(flat_std))}
    # within-patch spread versus between patches (patches from the smoothed labels of k=12)
    within = []
    for index in range(k):
        mask = (smooth_labels == index)
        if mask.sum() > 200:
            within.append(float(lightness[mask].std()))
    result['within_label_lightness_std_median'] = float(np.median(within))
    # outlines: thin dark lines (black top-hat: dark features narrower than the kernel and much darker than their surroundings)
    outlines = {}
    for kernel, drop in ((15, 22.0), (9, 12.0)):
        black_hat = thin_dark_lines(lightness, kernel)
        mask = (black_hat > drop).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        count, comp, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        keep_ids = np.where(stats[:, cv2.CC_STAT_AREA] >= 80)[0]
        keep_ids = keep_ids[keep_ids != 0]
        mask = np.isin(comp, keep_ids)
        widths, ridge = ridge_widths(mask)
        outlines[f'kernel_{kernel}_drop_{int(drop)}'] = {
            'share_of_pixels_in_thin_dark_lines': float(mask.mean()),
            'width_px_median': float(np.median(widths)) if len(widths) else 0.0,
            'width_px_p25': float(np.percentile(widths, 25)) if len(widths) else 0.0,
            'width_px_p75': float(np.percentile(widths, 75)) if len(widths) else 0.0,
            'darker_than_surroundings_lightness_median': float(np.median(black_hat[mask])) if mask.any() else 0.0,
            'darker_than_surroundings_lightness_p90': float(np.percentile(black_hat[mask], 90)) if mask.any() else 0.0,
            'lightness_of_the_line_pixels_median': float(np.median(lightness[mask])) if mask.any() else 0.0}
        if kernel == 15:
            overlay = (rgb[..., ::-1] * 0.45).astype(np.uint8)
            overlay[mask] = (0, 255, 255)
            cv2.imwrite(os.path.join(PICS, f'a01_outline_mask_{name}.png'), cv2.resize(overlay, (627, 627), interpolation=cv2.INTER_AREA))
    result['outlines'] = outlines
    result['horizontal_line_profile'] = row_profile_dips(lightness)
    # hardness of edges
    result['edge_hardness'] = edge_profile_rise(lightness)
    # streaks
    result['streaks'] = {'autocorr_1e_length_x_px': autocorrelation_length(lightness, 'x'), 'autocorr_1e_length_y_px': autocorrelation_length(lightness, 'y')}
    high = lightness - cv2.GaussianBlur(lightness, (0, 0), 25)
    result['streaks_detail_only'] = {'autocorr_1e_length_x_px': autocorrelation_length(high, 'x'), 'autocorr_1e_length_y_px': autocorrelation_length(high, 'y')}
    result['streaks']['structure'] = structure_coherence(lightness)
    # maps
    height_path = os.path.join(folder, 'height_as_uploaded.png')
    if os.path.exists(height_path):
        raw = cv2.imread(height_path, cv2.IMREAD_UNCHANGED)
        if raw.ndim == 3:
            raw = raw[..., 0]
        hist = np.bincount(raw.ravel(), minlength=256 if raw.dtype == np.uint8 else 65536)
        used = int((hist > raw.size * 0.0005).sum())
        height = raw.astype(np.float64) / (255.0 if raw.dtype == np.uint8 else 65535.0)
        smooth = cv2.imread(os.path.join(folder, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
        if smooth.ndim == 3:
            smooth = smooth[..., 0]
        smooth /= 65535.0 if smooth.max() > 255 else 255.0
        normal = cv2.imread(os.path.join(folder, 'normal.png'), cv2.IMREAD_COLOR)[..., ::-1].astype(np.float64) / 255.0 * 2 - 1
        tilt = np.degrees(np.arccos(np.clip(normal[..., 2] / np.maximum(np.linalg.norm(normal, axis=2), 1e-6), -1, 1)))
        ranks = lambda v: np.argsort(np.argsort(v.ravel())).astype(np.float64)
        sub = rng.integers(0, height.size, 120000)
        result['maps'] = {
            'height_8bit_levels_with_more_than_0.05_percent_of_pixels': used,
            'height_p1_p50_p99': [float(np.percentile(height, p)) for p in (1, 50, 99)],
            'height_vs_lightness_pearson': float(np.corrcoef(height.ravel(), lightness.ravel())[0, 1]),
            'height_vs_lightness_spearman': float(np.corrcoef(ranks(height.ravel()[sub]), ranks(lightness.ravel()[sub]))[0, 1]),
            'height_edge_rise': edge_profile_rise((height * 100).astype(np.float32)),
            'normal_tilt_degrees_p50_p90_p99': [float(np.percentile(tilt, p)) for p in (50, 90, 99)],
            'normal_flat_share_tilt_below_3deg': float((tilt < 3).mean()),
            'normal_flat_share_tilt_below_8deg': float((tilt < 8).mean()),
            'height_gradient_p50_p99_per_px': [float(np.percentile(np.hypot(*np.gradient(smooth)), p)) for p in (50, 99)],
        }
    return result, lab, centres_by_k


def save_palette_and_posterise_pictures(name, rgb, lab, centres_by_k):
    """One row: a 300 x 300 piece of the reference, then the same piece with every pixel snapped to the nearest of 4, 8, 16, 32 palette colours."""
    y, x, size = 300, 300, 300
    pieces = [rgb[y:y + size, x:x + size, ::-1].copy()]
    for k in (4, 8, 16, 32):
        centres, labels = centres_by_k[k]
        rgb_centres = np.clip(cv2.cvtColor(centres.reshape(-1, 1, 3).astype(np.float32), cv2.COLOR_Lab2RGB).reshape(-1, 3), 0, 1)
        out = (rgb_centres[labels] * 255).astype(np.uint8)[y:y + size, x:x + size, ::-1].copy()
        pieces.append(out)
    labels_text = ['reference', '4 colours', '8 colours', '16 colours', '32 colours']
    for piece, text in zip(pieces, labels_text):
        cv2.putText(piece, f'{name} {text}', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(piece, f'{name} {text}', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(PICS, f'a02_posterise_reference_{name}.png'), np.hstack(pieces))


def main():
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(PICS, exist_ok=True)
    only = sys.argv[1:] or SURFACES
    everything = {}
    for name in only:
        result, lab, centres_by_k = analyse(name)
        everything[name] = result
        save_palette_and_posterise_pictures(name, load_rgb_u8(os.path.join(REF, name, 'colour.png')), lab, centres_by_k)
        print(name, json.dumps({'patch': result['patches_k12'], 'outline15': result['outlines']['kernel_15_drop_22'], 'edge': result['edge_hardness']})[:600])
    with open(os.path.join(DATA, 'reference_measurements.json' if not sys.argv[1:] else 'reference_measurements_partial.json'), 'w') as handle:
        json.dump(everything, handle, indent=1)


if __name__ == '__main__':
    main()
