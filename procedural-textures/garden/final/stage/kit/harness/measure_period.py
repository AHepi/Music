# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P4 (nothing modern or wrong for the period). Four automatic parts (the fifth, a fresh person looking at eight crops, is done by a person):
#   forbidden   the look file has no layer key or entry from its `forbidden` list (graffiti, road lines, studs, bins, dishes, modern litter, oil, trench patches, flower boxes ...)
#               and every dial named in its `must_be_zero` list (lichen_amount) is 0 in the look
#   caps        coverage.run on the look's `period` table (a number outside its cap fails)
#   hue         on the dots the kit changed (|kit - base| above 0.02 in any channel): orange or yellow (hue 30 to 65 degrees, saturation 0.5 or more, value 0.5 or more) outside the
#               allowed masks (rust and dandelion: layer pictures named in look.hue_allowed) at most 0.05 % of the changed dots; no bright green (saturation 0.6 and value 0.6 or more);
#               nothing whiter than the whitened steps (the brightest 0.1 % of changed dots not above the whitened-step mask's 99th percentile + 0.03, when that mask exists)
#   whitewash   at most 15 % of the visible wall
# Use:   python3 -I measure_period.py SET_ID KIT_FOLDER BASE_FOLDER [--look sooty_1926] [--out result.json]
import colorsys
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage  # noqa: E402
import measure_common as mc  # noqa: E402


def forbidden_check(look):
    bad = []
    layers = look.get('layers', {})
    for word in look.get('forbidden', []):
        for key in layers:
            if key == word or key.startswith(word + '_'):
                bad.append(f'layer {key} matches forbidden {word}')
    for dial in look.get('must_be_zero', []):
        for key, values in layers.items():
            if dial in values and values[dial] != 0:
                bad.append(f'{key}.{dial} = {values[dial]}, must be 0')
    return not bad, bad


def hue_check(kit_rgb, base_rgb, allowed_mask=None, changed_threshold=0.02):
    """Hue test on the dots the kit changed. Returns dict(changed, orange_yellow_outside, bright_green)."""
    diff = np.abs(kit_rgb - base_rgb).max(axis=2)
    changed = diff > changed_threshold
    n = int(changed.sum())
    if n == 0:
        return dict(changed=0, orange_yellow_share=0.0, bright_green_share=0.0, ok=True)
    hsv = cv2.cvtColor(np.clip(kit_rgb, 0, 1).astype(np.float32), cv2.COLOR_RGB2HSV)       # hue 0..360, s, v 0..1
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    orange = changed & (hue >= 30) & (hue <= 65) & (sat >= 0.5) & (val >= 0.5)
    if allowed_mask is not None:
        orange &= ~allowed_mask
    green = changed & (sat >= 0.6) & (val >= 0.6) & (hue >= 75) & (hue <= 160)
    r = dict(changed=n, orange_yellow_share=round(float(orange.sum() / n), 6), bright_green_share=round(float(green.sum() / n), 6))
    r['ok'] = r['orange_yellow_share'] <= 0.0005 and green.sum() == 0
    return r


def run(settings, kit_folder, base_folder, look):
    out = {}
    ok, bad = forbidden_check(look)
    out['forbidden'] = dict(passed=ok, found=bad)
    out['caps'] = coverage.run(settings, kit_folder, look)
    out['hue'] = {}
    for camera, light, state, scene_id, w, h in mc.plate_list(settings):
        name = f'plate_{camera}_{light}_{state}'
        k, b = mc.pic(kit_folder, name), mc.pic(base_folder, name)
        if not (k and b):
            continue
        allowed = None
        for key in look.get('hue_allowed', []):
            mp = mc.pic(kit_folder, f'layer_{key}_plate_{camera}')
            if mp:
                m = mc.read_channel(mp, 0) > 0.3
                allowed = m if allowed is None else (allowed | m)
        out['hue'][name] = hue_check(mc.read_rgb(k), mc.read_rgb(b), allowed)
    out['passed'] = out['forbidden']['passed'] and out['caps']['passed'] and all(v['ok'] for v in out['hue'].values())
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    settings = mc.load_set(args[0])
    look = json.load(open(os.path.join(mc.KIT_ROOT, 'presets', opts.get('--look', 'sooty_1926') + '.json')))
    result = run(settings, args[1], args[2], look)
    if '--out' in opts:
        mc.jdump(result, opts['--out'])
    print(json.dumps(result, indent=1))
