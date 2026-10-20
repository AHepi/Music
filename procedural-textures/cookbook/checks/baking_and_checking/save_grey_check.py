# What this does: checks lib/bake_harness.save_array_png with a flat (2-D) grey array: does the saved PNG hold the grey in red, green AND blue?
# Writes save_grey_check.png (8-bit) and save_grey_check_16.png (16-bit), reads them back and prints the result. Run inside Blender:
#   blender -b --disable-autoexec -t 2 --python save_grey_check.py
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'lib'))
import bake_harness as harness
ramp = np.tile(np.linspace(0.0, 1.0, 64), (32, 1))          # 32 rows x 64 columns, a grey ramp
for name, sixteen in (('save_grey_check.png', False), ('save_grey_check_16.png', True)):
    path = os.path.join(HERE, name)
    harness.save_array_png(ramp, path, sixteen_bit=sixteen)
    back = harness.load_png_as_array(path)
    print('[save grey]', name, 'red=green=blue:', bool(np.allclose(back[..., 0], back[..., 1]) and np.allclose(back[..., 0], back[..., 2])),
          'largest error against the ramp:', round(float(np.abs(back[..., 0] - ramp).max()), 5))
