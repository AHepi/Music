# Checker script: numeric difference between two 8-bit PNGs (run in Blender's Python: blender -b --python compare_png.py -- A.png B.png OUT.json)
import sys, json
import numpy as np
import OpenImageIO as oiio
a_path, b_path, out = sys.argv[sys.argv.index('--') + 1:][:3]
def load(p):
    i = oiio.ImageInput.open(p); spec = i.spec()
    px = np.asarray(i.read_image(0, 0, 0, 3, 'uint8')).reshape(spec.height, spec.width, 3).astype(np.float32); i.close(); return px
A, B = load(a_path), load(b_path)
d = np.abs(A - B)
R = {'size': list(A.shape), 'mean_abs_diff_of_255': float(d.mean()), 'p99': float(np.percentile(d, 99)), 'max': float(d.max()),
     'mean_signed_diff_A_minus_B': float((A - B).mean()), 'share_pixels_diff_gt_8': float((d.max(axis=-1) > 8).mean())}
json.dump(R, open(out, 'w'), indent=1); print('COMPARE_DONE', R)
