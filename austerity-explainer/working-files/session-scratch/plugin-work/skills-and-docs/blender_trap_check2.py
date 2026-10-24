import bpy, numpy as np
buf = np.full((4,4,4), 0.5, np.float32)
img2 = bpy.data.images.new('b', 4, 4)
img2.pixels.foreach_set(buf.ravel())
img2.colorspace_settings.name = 'Non-Color'
print('FIRST PIXEL after set-space-last:', [round(v,3) for v in img2.pixels[:4]])
# attribute node reads 0 without a property: quick check via material nodes is too long; skip
# exit code behaviour
import sys
raise SystemExit(0)
