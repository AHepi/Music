# What this does: works out two "do nothing" yardsticks for each of the six references, measured exactly the way lib/pixel_compare.py measures:
#   * the normal error of a completely FLAT normal map (every dot facing straight out): the average angle between the reference's normal
#     (read from normal.png, made length 1) and straight out. A generated normal map with a bigger error than this is worse than no relief at all.
#   * the height error of a completely FLAT height picture after the tool's best brightness-and-contrast fit: the average distance of the
#     reference's 8-bit uploaded height from its own average. A generated height near this number has no relation to the reference's relief.
# Writes flat_baselines.json. Plain Python: python3 -I flat_baselines.py
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import pixel_compare  # noqa: E402

results = {}
for name in ('brick', 'slate', 'wood', 'metal', 'mud', 'gravel'):
    folder = os.path.join(PROC, 'reference', name)
    normal = pixel_compare.load_bgr8(os.path.join(folder, 'normal.png'))[..., ::-1] / 255.0 * 2 - 1
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-9)
    flat_angle = np.degrees(np.arccos(np.clip(normal[..., 2], -1, 1)))
    height = pixel_compare.load_bgr8(os.path.join(folder, 'height_as_uploaded.png'))[..., 0]
    results[name] = {'flat_normal_error_degrees': round(float(flat_angle.mean()), 2),
                     'flat_height_error_after_best_fit_steps': round(float(np.abs(height - height.mean()).mean()), 2)}
    print(name, results[name])
with open(os.path.join(HERE, 'flat_baselines.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
