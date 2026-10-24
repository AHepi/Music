"""What this file does (plain words): compares, dot for dot, each of the eight proof stills drawn with the OLD stage (stills/old/NAME) against the same still
drawn with the NEW stage (stills/new/NAME): average difference (0 to 255), largest difference, the share of dots that differ at all. Writes numbers/no_change_proof.json
and prints a table. Run: python3 -I compare_old_new.py
"""
import json, os, sys
import cv2, numpy as np
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def still(folder, name):
    d = os.path.join(W, 'stills', folder, name)
    for f in sorted(os.listdir(d)):
        if f.startswith('still-') and f.endswith('.jpg'): return cv2.imread(os.path.join(d, f)), os.path.join(d, f)
    return None, None
names = ['dry_projector', 'dry_moved', 'dry_move', 'notice_end', 'notice_move', 'chapter2_a', 'chapter2_b', 'chapter1_a']
res = {}
for n in names:
    a, pa = still('old', n); b, pb = still('new', n)
    if a is None or b is None: print(f'{n:15s} missing'); continue
    assert a.shape == b.shape, (n, a.shape, b.shape)
    d = np.abs(a.astype(int) - b.astype(int))
    res[n] = {'mean_abs_difference_0_to_255': float(d.mean()), 'largest_difference': int(d.max()), 'share_of_dots_that_differ_at_all': float((d.max(axis=2) > 0).mean()), 'size': list(a.shape[:2])}
    print(f"{n:15s} mean difference {d.mean():.5f}   largest {d.max():3d}   dots that differ {100 * (d.max(axis=2) > 0).mean():.4f} %")
os.makedirs(os.path.join(W, 'numbers'), exist_ok=True)
json.dump(res, open(os.path.join(W, 'numbers', 'no_change_proof.json'), 'w'), indent=1)
