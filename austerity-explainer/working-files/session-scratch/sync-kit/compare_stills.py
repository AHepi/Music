"""What this does: compares pairs of stills pixel by pixel and prints the largest difference (levels 0-255) and the
share of pixels that differ by more than 2 levels. Pass mark (the design's regression rule): largest <= 5 and under
0.1% of pixels over 2.
Use: python3 -I compare_stills.py A.jpg B.jpg [A2.jpg B2.jpg ...]   (exit 1 if any pair fails)
"""
import sys
import numpy as np
from PIL import Image
args, failed = sys.argv[1:], False
for a, b in zip(args[0::2], args[1::2]):
    x = np.asarray(Image.open(a).convert('RGB'), dtype=np.int16); y = np.asarray(Image.open(b).convert('RGB'), dtype=np.int16)
    if x.shape != y.shape:
        print(f'FAIL sizes differ {x.shape} {y.shape}: {a} {b}'); failed = True; continue
    d = np.abs(x - y).max(axis=2)
    share = (d > 2).mean()
    ok = d.max() <= 5 and share < 0.001
    failed |= not ok
    print(f'{"pass" if ok else "FAIL"}  largest difference {d.max()} levels, {share*100:.4f}% of pixels over 2  ({a.split("/")[-2]}/{a.split("/")[-1]} vs {b.split("/")[-2]}/{b.split("/")[-1]})')
sys.exit(1 if failed else 0)
