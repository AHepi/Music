# Plain note: runs INSIDE Blender (blender -b --python exr_to_png16.py -- FILE.exr [FILE2.exr ...]). Reads each EXR picture that
# Material Maker wrote and saves a 16-bit grey PNG next to it (same name, .png16.png) plus prints min / max / mean of the values.
# 16-bit PNG keeps 65535 steps so nothing is lost for height/roughness maps whose values run 0..1.
import sys
import numpy as np
import OpenImageIO as oiio
files = sys.argv[sys.argv.index('--') + 1:]
for f in files:
    buf = oiio.ImageBuf(f)
    a = buf.get_pixels(oiio.FLOAT)
    ch = a.shape[2]
    g = a[..., 0]
    out = f[:-4] + '.png16.png'
    arr = (np.clip(g, 0, 1) * 65535.0 + 0.5).astype(np.uint16)
    ob = oiio.ImageBuf(oiio.ImageSpec(arr.shape[1], arr.shape[0], 1, oiio.UINT16))
    ob.set_pixels(oiio.ROI(0, arr.shape[1], 0, arr.shape[0], 0, 1, 0, 1), arr[..., None])
    ob.write(out)
    print('EXR', f, a.shape, 'channels', ch, 'min %.4f max %.4f mean %.4f' % (g.min(), g.max(), g.mean()), '->', out)
