# What this does: the geometry experiments only photographed colour and height. To score them with the project's scorer they need a normal map too, so this makes one
# from the height with a simple Sobel slope (strength 6, OpenGL: green up) into a copy of each folder under out/scored_geometry/, then runs lib/texture_compare.py.
# Use: python3 -I score_geometry_pictures.py   (prints one line per picture set)
import json, os, shutil, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
SETS = [('gravel', 'geo_gravel_poisson_plain'), ('gravel', 'geo_gravel_poisson_ghosts'), ('gravel', 'geo_gravel_random_plain'), ('gravel', 'geo_physics_gravel'), ('slate', 'geo_slate_rows')]
for surface, name in SETS:
    src = os.path.join(HERE, 'out', name.replace('geo_gravel_poisson_plain', 'geo_gravel_poisson_plain'))
    dst = os.path.join(HERE, 'out', 'scored_geometry', name)
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(src, 'colour.png'), dst)
    height = cv2.imread(os.path.join(src, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    height = height if height.ndim == 2 else height[..., 0]
    height /= height.max()
    cv2.imwrite(os.path.join(dst, 'height.png'), (height * 65535).astype(np.uint16))
    hx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / 2.0
    hy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / 2.0
    nx, ny, nz = -6.0 * hx * 10, 6.0 * hy * 10, np.ones_like(height)
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    normal = np.stack([nx / length, ny / length, nz / length], -1) * 0.5 + 0.5
    cv2.imwrite(os.path.join(dst, 'normal.png'), (normal[..., ::-1] * 255).astype(np.uint8))
    subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'texture_compare.py'), surface, dst, '--json', os.path.join(dst, 'score.json'), '--sheet', os.path.join(dst, 'sheet.png')], capture_output=True)
    d = json.load(open(os.path.join(dst, 'score.json')))
    print(f"{name:32s} vs {surface}: overall {d['overall']:.3f}  {d['groups']}")
