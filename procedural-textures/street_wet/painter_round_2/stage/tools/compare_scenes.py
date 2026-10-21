"""What this file does (plain words): proves that the brightness fix changes nothing where it is not asked for, and measures what it changes where it is asked for.
  1. NOT ASKED FOR: every picture in stills/after_default/ (the film's own dry lockout, the notice corner clip, two moments of chapter 2, one of chapter 1: drawn with the new stage file but WITHOUT asking for the fix) is compared dot by dot with the same picture in
     stills/before/ (the film's own stage file). Reported: the average and the largest difference (0 to 255), and how many dots differ at all. The aim is: none.
  2. ASKED FOR, DRY: the film's own dry lockout painting drawn with the fix switched on (stills/after/dry_*) against the film's own look (stills/before/dry_*): how much would the dry lockout change if the fix were used on it too
     (average difference in brightness 0 to 1 over the whole picture, the road, the walls, the pavement and the sky; and how much brighter or darker on average).
  3. ASKED FOR, WET: the new wet pictures with the fix (stills/after/wet_*) against without it (stills/before/wet_*), the same way.
Masks: Blender's, for the plate camera (plate view pictures) and the moved camera (moved view), the first painter test's, read only. Writes numbers/no_change_proof.json and numbers/change_where_asked.json. Run: python3 -I tools/compare_scenes.py
"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from stage_common import central_mask, masks, er, TEST1, P
def img(folder, name):
    p = None
    d = P('stills', folder, name)
    for f in os.listdir(d):
        if f.startswith('still-'): p = os.path.join(d, f)
    return cv2.imread(p)
def lum(im):
    b, g, r = [im[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
# 1. not asked for
res1 = {}
print('1. NOT ASKED FOR: new stage file, fix off by default, against the film\'s own stage file')
for name in sorted(os.listdir(P('stills', 'after_default'))):
    if not os.path.isdir(P('stills', 'before', name)): continue
    a, b = img('before', name).astype(int), img('after_default', name).astype(int)
    d = np.abs(a - b)
    res1[name] = {'mean_abs_difference_0_to_255': float(d.mean()), 'largest_difference': int(d.max()), 'share_of_dots_that_differ_at_all': float((d.max(axis=2) > 0).mean()), 'picture_mean_brightness_before': float(lum(a.astype(np.uint8)).mean())}
    print(f"   {name:14s} mean difference {d.mean():.5f}  largest {d.max()}  dots that differ {100 * (d.max(axis=2) > 0).mean():.4f} %   (picture mean brightness {lum(a.astype(np.uint8)).mean():.3f})")
json.dump(res1, open(P('numbers/no_change_proof.json'), 'w'), indent=1)
# 2 and 3. asked for
Mp = masks(TEST1 + 'alignment/facts_surfaces/'); Mm = masks(TEST1 + 'alignment/facts_surfaces_moved/')
ones = np.ones((1920, 1080), bool)
def zones(M, f):
    return {'whole picture': ones, 'road': er(f(M['road']), 4), 'pavement/kerb/gutter': er(f(M['pavement'] | M['kerb'] | M['gutter']), 3), 'walls': er(f(M['walls']), 3), 'roofs': er(f(M['roofs']), 3)}
# the plate-view masks are in the plate camera's frame (lens 44 deg); the stage's plate view (lens 40 deg) sees the middle part of it
Zp = zones(Mp, central_mask); Zm = zones(Mm, lambda m: m)
res23 = {}
print('\n2/3. ASKED FOR: with the fix switched on against the film\'s own look (average brightness change 0 to 1; + = brighter)')
for name in ('dry_projector', 'dry_moved', 'dry_move', 'wet_projector', 'wet_moved', 'wet_move', 'wetolddry_moved', 'wetown_moved'):
    if not os.path.isdir(P('stills', 'after', name)): continue
    a, b = lum(img('before', name)), lum(img('after', name))
    Z = Zp if 'projector' in name else Zm if 'moved' in name else None
    r = {'whole_picture_mean_abs_change': float(np.abs(b - a).mean()), 'whole_picture_mean_signed_change': float((b - a).mean())}
    if Z:
        for k, m in Z.items():
            if k == 'whole picture' or m.sum() < 100: continue
            r[k] = {'mean_abs_change': float(np.abs(b - a)[m].mean()), 'mean_signed_change': float((b - a)[m].mean()), 'brightness_before': float(a[m].mean()), 'brightness_after': float(b[m].mean())}
    res23[name] = r
    print(f"   {name:16s} whole picture: change {r['whole_picture_mean_abs_change']:.4f} (signed {r['whole_picture_mean_signed_change']:+.4f})" + ''.join(f"   {k}: {r[k]['mean_signed_change']:+.3f}" for k in r if isinstance(r[k], dict)))
json.dump(res23, open(P('numbers/change_where_asked.json'), 'w'), indent=1)
