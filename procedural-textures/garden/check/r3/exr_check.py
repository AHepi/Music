# Checker script: do the light-group layers in a multilayer EXR add up to the Combined layer?
# Run (Blender's own Python has OpenImageIO and numpy):
#   blender -b --disable-autoexec --python exr_check.py -- OUT.json IN1.exr [IN2.exr ...]
# Reads channels directly with OpenImageIO. No drawing, no scene needed.
import sys, json, os
import numpy as np
import OpenImageIO as oiio

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
files = argv[1:]
R = {}
for path in files:
    info = {'bytes': os.path.getsize(path) if os.path.exists(path) else None}
    inp = oiio.ImageInput.open(path)
    if inp is None:
        info['error'] = oiio.geterror(); R[path] = info; continue
    parts = []
    sub = 0
    chans = {}
    while inp.seek_subimage(sub, 0):
        spec = inp.spec()
        names = list(spec.channelnames)
        parts.append({'subimage': sub, 'name': spec.get_string_attribute('name', ''), 'w': spec.width, 'h': spec.height, 'n_channels': len(names), 'sample': names[:6]})
        # keep all channels of every part keyed by full name, but only read the ones we need
        for ci, nm in enumerate(names):
            chans.setdefault(nm, (sub, ci))
        sub += 1
    info['parts'] = parts
    allnames = sorted(chans)
    info['channel_names_with_Combined'] = [n for n in allnames if 'Combined' in n][:40]

    def read(nm):
        sub, ci = chans[nm]
        inp.seek_subimage(sub, 0)
        spec = inp.spec()
        px = inp.read_image(sub, 0, ci, ci + 1, 'float')
        return np.asarray(px).reshape(spec.height, spec.width)

    def rgb(prefix):
        return np.stack([read(prefix + '.' + c) for c in 'RGB'], axis=-1)

    # find the layer holding the groups
    gp = sorted({n.rsplit('.', 1)[0] for n in allnames if '.Combined_' in n})
    info['group_passes'] = gp
    if not gp:
        R[path] = info; inp.close(); continue
    layer = gp[0].split('.Combined_')[0]
    comb = rgb(layer + '.Combined')
    groups = {p.split('.Combined_')[1]: rgb(p) for p in gp}
    s = sum(groups.values())
    lum = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    Lc, Ls = lum(comb), lum(s)
    info['layer'] = layer
    info['mean_combined_lum'] = float(Lc.mean())
    info['mean_sum_of_groups_lum'] = float(Ls.mean())
    info['total_rel_error'] = float((Ls.sum() - Lc.sum()) / Lc.sum())
    info['share_of_groups_percent'] = {g: round(100 * float(lum(v).sum() / Ls.sum()), 2) for g, v in groups.items()}
    # exact test: groups against the NOISY (un-denoised) combined image of the same samples
    if layer + '.Noisy Image.R' in chans:
        noisy = rgb(layer + '.Noisy Image')
        Ln = lum(noisy)
        info['noisy_image_total_rel_error_of_group_sum'] = float((Ls.sum() - Ln.sum()) / Ln.sum())
        d = np.abs(s - noisy[..., :3]).max(axis=-1)
        info['noisy_image_max_abs_pixel_diff'] = float(d.max())
        info['noisy_image_pixels_with_diff_gt_1e-3_relative'] = int((np.abs(Ls - Ln) > 1e-3 * np.maximum(Ln, 1e-3)).sum())
    # blockwise (16x16) relative error, so that pixel noise does not dominate
    H, W = Lc.shape
    b = 16
    Hc, Wc = H // b * b, W // b * b
    bc = Lc[:Hc, :Wc].reshape(Hc // b, b, Wc // b, b).mean(axis=(1, 3))
    bs = Ls[:Hc, :Wc].reshape(Hc // b, b, Wc // b, b).mean(axis=(1, 3))
    ok = bc > 0.02
    rel = np.abs(bs[ok] - bc[ok]) / bc[ok]
    info['block16_rel_error'] = {'median': float(np.median(rel)), 'p90': float(np.percentile(rel, 90)), 'p99': float(np.percentile(rel, 99)), 'max': float(rel.max()), 'blocks': int(ok.sum())}
    # pixel-wise on bright pixels (noise included)
    okp = Lc > 0.05
    relp = np.abs(Ls[okp] - Lc[okp]) / Lc[okp]
    info['pixel_rel_error'] = {'median': float(np.median(relp)), 'p90': float(np.percentile(relp, 90)), 'pixels': int(okp.sum())}
    # noisiness of the raw group layers: std of pixel vs 16x16 block mean, relative, for the sum and for combined
    def noise(L):
        blocks = L[:Hc, :Wc].reshape(Hc // b, b, Wc // b, b)
        m = blocks.mean(axis=(1, 3))
        sd = blocks.std(axis=(1, 3))
        k = m > 0.05
        return float(np.median(sd[k] / m[k]))
    info['noise_median_rel_sd_in_16px_blocks'] = {'combined': noise(Lc), 'sum_of_groups': noise(Ls)}
    # also: is the "Composite" part (final picture) present, and its size
    info['has_composite_part'] = any(p['name'].lower().startswith('composite') or any(n.startswith('Composite') for n in [p['sample'][0]]) for p in parts)
    inp.close()
    R[path] = info
json.dump(R, open(out, 'w'), indent=1)
print('EXR_CHECK_DONE')
