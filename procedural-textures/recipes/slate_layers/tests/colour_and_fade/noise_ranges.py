# What this file does (plain words): measures how widely Blender's noise values spread (2D, 3D, 4D, 1D, seamless), at detail 0, 1, 2, so the
# settings of COLOUR AND FADE can use the right stretch. Run with plain python; it starts Blender itself. Prints mean, std and percentiles.
import json, os, subprocess
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
views = {f'{d}_{k}': {'dims': d, 'detail': k} for d in ('1D', '2D', '3D', '4D', 'seamless') for k in (0, 1, 2)}
subprocess.run(BLENDER + [os.path.join(HERE, '..', 'bake_tools.py'), '--', os.path.join(HERE, 'noise_range_recipe.py'), os.path.join(HERE, 'dev', 'noise_ranges'), '512', '1',
                          json.dumps(views), '{}', 'Height'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for name in views:
    image = cv2.imread(os.path.join(HERE, 'dev', 'noise_ranges', name + '_height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
    values = image[..., 1] if image.ndim == 3 else image
    p = np.percentile(values, [1, 10, 50, 90, 99])
    print(f'{name:12s} mean {values.mean():.3f} std {values.std():.3f}  p1/10/50/90/99 {np.round(p, 2).tolist()}')
