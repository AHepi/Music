"""What this does: puts a painted fill into a painting only where objects were removed. Takes the
original painting, an edited copy with the objects painted out (any size; it is resized to match),
and the mask of the removed objects; blends the edit in inside the mask with a soft edge, so
everything outside stays exactly the original. Also checks how well the edit lines up with the
original just outside the mask (mean difference, 0-255).
Use: python3 -I composite_fill.py ORIGINAL.jpg EDITED.png MASK.png OUT.jpg"""
import sys
import numpy as np
from PIL import Image, ImageFilter
original_path, edited_path, mask_path, out_path = sys.argv[1:5]
original = Image.open(original_path).convert('RGB')
edited = Image.open(edited_path).convert('RGB').resize(original.size, Image.LANCZOS)
mask = Image.open(mask_path).convert('L')
soft = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10))
a, b, m = (np.asarray(x, dtype=float) for x in (original, edited, soft))
w = (m / 255.0)[..., None]
Image.fromarray((a * (1 - w) + b * w).astype(np.uint8)).save(out_path, quality=93)
ring = (np.asarray(mask.filter(ImageFilter.MaxFilter(61))) > 128) & ~(np.asarray(mask.filter(ImageFilter.MaxFilter(21))) > 128)
print('edit vs original just outside the mask: mean difference', round(float(np.abs(a[ring] - b[ring]).mean()), 1))
