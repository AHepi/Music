# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P2 (the wet look is kept). From the 22 lighting pictures of a set (PNG), the class pictures (class_<camera>_<W>x<H>), the puddle pictures (puddle_<label>_<state>) and, for the
# kit's own elements, the layer pictures (layer_<key>_<label>_<state>) it works out, for every picture and surface class (walls, trims, road, pavement ...):
#   class_mean       mean brightness of the class (Rec.709 weights of the picture as shown)
#   wet_to_dry       for every wet or heavy picture with a dry twin (same label and light): the class's mean brightness wet / dry
#   puddle_cover     share of the road under a puddle (puddle picture red above 0.5)
#   road_p95         the 95th percentile of the road's brightness in the wet picture (frozen by the baseline); highlight_share = share of road dots above the BASELINE's p95
#   speckle_share    road dots at least 4 times the local median (15 x 15 window, median floored at 0.02) in lighting E wet pictures
#   element_wet_dry  for every kit layer: mean brightness under its mask in the wet picture over the dry one (dry mask used for both), pictures with layer_ files only
# judge(result, base) applies the plan's P2 lines: ratio within 0.05 of base on road, pavement and walls; puddle cover within 2 points; highlight share 85 to 115 % of base's;
# speckle share not above base's + 0.2 points; every element's wet/dry at most 1.0.
# Use:   python3 -I measure_wet.py SET_ID FOLDER [FOLDER ...] [--base base_wet.json] [--out result.json]
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402

CLASSES_OF_P2 = ('road', 'pavement', 'walls')


def _find(folders, name, ext='.png'):
    for f in folders:
        p = os.path.join(f, name + ext)
        if os.path.exists(p):
            return p
    return None


def run(settings, folders, base=None):
    folders = mc.folders_for(folders)
    classes = mc.classes(settings)
    out = {'pictures': {}, 'wet_to_dry': {}, 'puddle_cover': {}, 'speckle': {}, 'element_wet_dry': {}}
    cache = {}
    for label, light, state, scene_id in mc.t22_list(settings):
        name = f'{label}_{light}_{state}'
        picture = _find(folders, name)
        if picture is None:
            out['pictures'][name] = {'missing': True}
            continue
        w, h = mc.size_of(settings, label)
        camera = mc.camera_of(settings, label)
        class_path = _find(folders, f'class_{camera}_{w}x{h}')
        if class_path is None:
            out['pictures'][name] = {'missing': 'class picture'}
            continue
        if class_path not in cache:
            cache[class_path] = mc.read_class(class_path)
        cmap = cache[class_path]
        L = mc.read_lum(picture)
        entry = {'class_mean': {}, 'class_dots': {}}
        for cname, ids in classes.items():
            m = mc.class_mask(cmap, ids)
            if m.any():
                entry['class_mean'][cname] = round(float(L[m].mean()), 4)
                entry['class_dots'][cname] = int(m.sum())
        road = mc.class_mask(cmap, classes.get('road', []))
        if road.any() and state != 'dry':
            entry['road_p95'] = round(float(np.percentile(L[road], 95)), 4)
            if base and name in base.get('pictures', {}) and 'road_p95' in base['pictures'][name]:
                p95 = base['pictures'][name]['road_p95']
                entry['highlight_share'] = round(float((L[road] > p95).mean()), 4)
            pf = _find(folders, f'puddle_{label}_{state}')
            if pf:
                pud = mc.read_channel(pf, 0) > 0.5
                out['puddle_cover'][name] = round(float((pud & road).sum() / road.sum()), 4)
        if light == 'E' and state == 'wet' and road.any():
            med = cv2.medianBlur((np.clip(L, 0, 1) * 255).astype(np.uint8), 15).astype(np.float32) / 255.0
            out['speckle'][name] = round(float((L[road] >= 4.0 * np.maximum(med[road], 0.02)).mean()), 5)
        out['pictures'][name] = entry
    for label, light, state, scene_id in mc.t22_list(settings):
        if state == 'dry':
            continue
        wet, dry = out['pictures'].get(f'{label}_{light}_{state}'), out['pictures'].get(f'{label}_{light}_dry')
        if not wet or not dry or 'class_mean' not in wet or 'class_mean' not in dry:
            continue
        row = {c: round(wet['class_mean'][c] / dry['class_mean'][c], 4) for c in wet['class_mean'] if c in dry['class_mean'] and dry['class_mean'][c] > 0}
        out['wet_to_dry'][f'{label}_{light}_{state}'] = row
    # kit elements: layer_<key>_<label>_<state>.png
    keys = sorted({fn.split('_')[1] for f in folders for fn in os.listdir(f) if fn.startswith('layer_') and not fn.split('_')[1] == 'plate' and fn.endswith('.png')})
    for key in keys:
        for label, light, state, scene_id in mc.t22_list(settings):
            if state == 'dry':
                continue
            mask_p = _find(folders, f'layer_{key}_{label}_{state}')
            pic_wet, pic_dry = _find(folders, f'{label}_{light}_{state}'), _find(folders, f'{label}_{light}_dry')
            if not (mask_p and pic_wet and pic_dry):
                continue
            m = mc.read_channel(mask_p, 0) > 0.3
            if m.sum() < 200:
                continue
            out['element_wet_dry'][f'{key}:{label}_{light}_{state}'] = round(float(mc.read_lum(pic_wet)[m].mean() / max(1e-4, mc.read_lum(pic_dry)[m].mean())), 4)
    return out


def judge(result, base):
    """P2's lines against a frozen base result. Returns (ok, list of failures)."""
    fails = []
    for name, row in result['wet_to_dry'].items():
        b = base['wet_to_dry'].get(name, {})
        for c in CLASSES_OF_P2:
            if c in row and c in b and abs(row[c] - b[c]) > 0.05:
                fails.append(f'{name} {c} wet/dry {row[c]:.3f} vs base {b[c]:.3f} (more than 0.05)')
    for name, v in result['puddle_cover'].items():
        b = base['puddle_cover'].get(name)
        if b is not None and abs(v - b) > 0.02:
            fails.append(f'{name} puddle cover {v:.3f} vs base {b:.3f} (more than 2 points)')
    for name, e in result['pictures'].items():
        hs = e.get('highlight_share')
        if hs is not None and not (0.85 * 0.05 <= hs <= 1.15 * 0.05):
            fails.append(f'{name} highlight share {hs:.4f} outside 85 to 115 % of base (0.05)')
    for name, v in result['speckle'].items():
        b = base['speckle'].get(name)
        if b is not None and v > b + 0.002:
            fails.append(f'{name} speckle share {v:.4f} above base {b:.4f} + 0.2 points')
    for name, v in result['element_wet_dry'].items():
        if v > 1.0:
            fails.append(f'element {name} wet/dry {v:.3f} above 1.0')
    return not fails, fails


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    settings = mc.load_set(args[0])
    base = mc.json.load(open(opts['--base'])) if '--base' in opts else None
    result = run(settings, args[1:], base)
    if '--out' in opts:
        mc.jdump(result, opts['--out'])
    print(mc.json.dumps({k: v for k, v in result.items() if k != 'pictures'}, indent=1))
    if base:
        print(judge(result, base))
